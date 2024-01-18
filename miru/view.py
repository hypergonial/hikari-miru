from __future__ import annotations

import asyncio
import copy
import logging
import sys
import traceback
import typing as t

import hikari

from miru.abc.item import DecoratedItem, InteractiveViewItem, ViewItem
from miru.abc.item_handler import ItemHandler
from miru.button import Button, LinkButton
from miru.context.view import AutodeferOptions, ViewContext
from miru.exceptions import HandlerFullError
from miru.internal.types import ResponseBuildersT
from miru.select import ChannelSelect, MentionableSelect, RoleSelect, TextSelect, UserSelect

if t.TYPE_CHECKING:
    import datetime

    import typing_extensions as te

    from miru.abc.select import SelectBase
    from miru.client import Client

__all__ = ("View",)

logger = logging.getLogger(__name__)

ViewT = t.TypeVar("ViewT", bound="View")


_SELECT_VIEW_ITEM_MAPPING: t.Mapping[hikari.ComponentType, type[SelectBase]] = {
    hikari.ComponentType.TEXT_SELECT_MENU: TextSelect,
    hikari.ComponentType.CHANNEL_SELECT_MENU: ChannelSelect,
    hikari.ComponentType.ROLE_SELECT_MENU: RoleSelect,
    hikari.ComponentType.USER_SELECT_MENU: UserSelect,
    hikari.ComponentType.MENTIONABLE_SELECT_MENU: MentionableSelect,
}
"""A mapping of all select types to their respective item classes."""


class View(
    ItemHandler[
        hikari.impl.MessageActionRowBuilder, ResponseBuildersT, ViewContext, hikari.ComponentInteraction, ViewItem
    ]
):
    """Represents a set of Discord UI components attached to a message.

    Parameters
    ----------
    timeout : Optional[Union[float, int, datetime.timedelta]]
        The duration after which the view times out, in seconds
    autodefer : bool | AutodeferOptions
        If enabled, interactions will be automatically deferred if not responded to within 2 seconds
        You may also pass an instance of [miru.AutodeferOptions][miru.context.view.AutodeferOptions] to customize the autodefer behaviour.

    Raises
    ------
    ValueError
        Raised if a view has more than 25 components attached.
    RuntimeError
        Raised if miru.install() was never called before instantiation.
    """

    _view_children: t.ClassVar[
        t.MutableSequence[DecoratedItem[te.Self, InteractiveViewItem]]
    ] = []  # Decorated callbacks that need to be turned into items

    def __init_subclass__(cls) -> None:
        """Get decorated callbacks."""
        children: t.MutableSequence[DecoratedItem[te.Self, InteractiveViewItem]] = []
        for base_cls in reversed(cls.mro()):
            for value in base_cls.__dict__.values():
                if isinstance(value, DecoratedItem):
                    children.append(value)  # type: ignore

        if len(children) > 25:
            raise HandlerFullError("View cannot have more than 25 components attached.")

        cls._view_children = children

    def __init__(
        self, *, timeout: float | int | datetime.timedelta | None = 120.0, autodefer: bool | AutodeferOptions = True
    ) -> None:
        super().__init__(timeout=timeout)
        self._autodefer: AutodeferOptions = AutodeferOptions.parse(autodefer)
        self._message: hikari.Message | None = None
        self._message_id: hikari.Snowflake | None = None
        self._is_bound = True
        self._input_event: asyncio.Event = asyncio.Event()

        for decorated_item in self._view_children:
            # Must deepcopy, otherwise multiple views will have the same item reference
            decorated_item = copy.deepcopy(decorated_item)
            item = decorated_item.build(self)
            self.add_item(item)
            setattr(self, decorated_item.name, item)

    @property
    def is_persistent(self) -> bool:
        """Determines if this view is persistent or not.
        A view is persistent only if it has no timeout and all of it's items have explicitly set custom_ids.
        """
        return self.timeout is None and all(item._is_persistent for item in self.children)

    @property
    def message(self) -> hikari.Message | None:
        """The message this view is bound to. Will be None if the view is not bound."""
        return self._message

    @property
    def is_bound(self) -> bool:
        """Determines if the view should be bound to a message or not."""
        return self._is_bound

    @property
    def autodefer(self) -> AutodeferOptions:
        """The autodefer configuration of this view."""
        return self._autodefer

    @property
    def _builder(self) -> type[hikari.impl.MessageActionRowBuilder]:
        return hikari.impl.MessageActionRowBuilder

    @classmethod
    def from_message(
        cls,
        message: hikari.Message,
        *,
        timeout: float | int | datetime.timedelta | None = 120.0,
        autodefer: bool = True,
    ) -> te.Self:
        """Create a new view from the components included in the passed message.
        Returns an empty view if the message has no components attached.

        Parameters
        ----------
        message : hikari.Message
            The message to read components from
        timeout : Optional[float]
            The timeout of the created view
        autodefer : bool
            If enabled, interactions will be automatically deferred if not responded to within 2 seconds

        Returns
        -------
        View
            The view that represents the components attached to this message.

        !!! warning
            This function constructs a completely new view based on the information available in the message object.
            Any custom behaviour (such as callbacks) will not be re-created,
            if you want to access an already running view that is bound to a message, use [`Client.get_bound_view()`][miru.client.Client.get_bound_view] instead.
        """
        view = cls(timeout=timeout, autodefer=autodefer)

        if not message.components:
            return view

        for row, action_row in enumerate(message.components):
            assert isinstance(action_row, hikari.ActionRowComponent)

            for component in action_row.components:
                if not isinstance(component.type, hikari.ComponentType):
                    continue  # Unrecognized component types are ignored

                if component.type is hikari.ComponentType.BUTTON:
                    comp_cls = LinkButton if getattr(component, "url", None) else Button
                else:
                    comp_cls = _SELECT_VIEW_ITEM_MAPPING[component.type]
                view.add_item(comp_cls._from_component(component, row))

        return view

    def _refresh_client_customid_list(self) -> None:
        """Refresh the client's registered custom_ids.

        This is to handle an edge-case where the view was started,
        did not yet receive it's first interaction, but the components were edited.
        """
        if self._client is None:  # Did not start yet
            return

        if self._message_id is not None:  # If bound, the view is tracked by message_id instead
            return

        self.client._remove_handler(self)
        self.client._add_handler(self)

    def add_item(self, item: ViewItem) -> te.Self:
        """Adds a new item to the view.

        Parameters
        ----------
        item : ViewItem
            The item to be added.

        Raises
        ------
        ValueError
            A view already has 25 components attached.
        TypeError
            Parameter item is not an instance of ViewItem.
        RuntimeError
            The item is already attached to this view.
        RuntimeError
            The item is already attached to another view.

        Returns
        -------
        View
            The view the item was added to.
        """
        super().add_item(item)
        self._refresh_client_customid_list()
        return self

    def remove_item(self, item: ViewItem) -> te.Self:
        """Removes an item from the view.

        Parameters
        ----------
        item : ViewItem
            The item to be removed.

        Raises
        ------
        ValueError
            The item is not attached to this view.

        Returns
        -------
        View
            The view the item was removed from.
        """
        super().remove_item(item)
        self._refresh_client_customid_list()
        return self

    def clear_items(self) -> te.Self:
        """Removes all items from the view.

        Returns
        -------
        View
            The view the items were removed from.
        """
        super().clear_items()
        self._refresh_client_customid_list()
        return self

    async def view_check(self, context: ViewContext, /) -> bool:
        """Called before any callback in the view is called. Must evaluate to a truthy value to pass.
        Override for custom check logic.

        Parameters
        ----------
        context : ViewContextT
            The context for this check.

        Returns
        -------
        bool
            A boolean indicating if the check passed or not.
        """
        return True

    async def on_error(
        self, error: Exception, item: InteractiveViewItem | None = None, context: ViewContext | None = None, /
    ) -> None:
        """Called when an error occurs in a callback function or the built-in timeout function.
        Override for custom error-handling logic.

        Parameters
        ----------
        error : Exception
            The exception encountered.
        item : Optional[MessageItem[ViewT]]
            The item this exception originates from, if any.
        context : Optional[Context]
            The context associated with this exception, if any.
        """
        if item:
            print(f"Ignoring exception in view {self} for item {item}:", file=sys.stderr)
        else:
            print(f"Ignoring exception in view {self}:", file=sys.stderr)

        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    async def _handle_callback(self, item: InteractiveViewItem, context: ViewContext) -> None:
        """Handle the callback of a view item. Separate task in case the view is stopped in the callback."""
        try:
            if not self._message or (self._message.id == context.message.id):
                self._message = context.message

            self._input_event.set()
            self._input_event.clear()

            await item._refresh_state(context)

            autodefer = item.autodefer if item.autodefer is not hikari.UNDEFINED else self.autodefer

            if autodefer.mode.should_autodefer:
                context._start_autodefer(self.autodefer)

            await item.callback(context)

        except Exception as error:
            await self.on_error(error, item, context)

    async def _invoke(self, interaction: hikari.ComponentInteraction) -> asyncio.Future[ResponseBuildersT] | None:
        """Process incoming interactions."""
        item = next((item for item in self.children if item.custom_id == interaction.custom_id), None)

        if not item:
            logger.debug(f"View received interaction for unknown custom_id '{interaction.custom_id}', ignoring.")
            return

        assert isinstance(item, InteractiveViewItem)

        self._reset_timeout()

        context = ViewContext(self, self.client, interaction)
        self._last_context = context

        passed = await self.view_check(context)
        if not passed:
            if self.client.is_rest:
                return context._resp_builder
            return

        # Create task here to ensure autodefer works even if callback stops view
        self._create_task(self._handle_callback(item, context))

        if self.client.is_rest:
            return context._resp_builder

    def stop(self) -> None:
        self._input_event.set()
        return super().stop()

    async def wait_for_input(self, timeout: float | None = None) -> None:
        """Wait for any input to be received. This will also unblock if the view was stopped, thus
        it is recommended to check for the presence of a value after this function returns.

        Parameters
        ----------
        timeout : Optional[float]
            The amount of time to wait for input, in seconds
        """
        await asyncio.wait_for(self._input_event.wait(), timeout=timeout)

    def _client_start_hook(self, client: Client) -> None:
        """Called when a client wants to add the view itself."""
        self._client = client

        if not self.children:
            logger.warning(
                f"View '{type(self).__name__}' has no items attached. Ignoring '{type(client).__name__}.start_view()' call."
            )
            return

        # Optimize URL-button-only views by not adding to listener
        if all(isinstance(item, LinkButton) for item in self.children):
            logger.warning(
                f"View '{type(self).__name__}' only contains link buttons. Ignoring '{type(client).__name__}.start_view()' call."
            )
            return

        self._client._add_handler(self)
        self._timeout_task = self._create_task(self._handle_timeout())


# MIT License
#
# Copyright (c) 2022-present hypergonial
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
