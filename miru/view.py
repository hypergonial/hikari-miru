from __future__ import annotations

import asyncio
import copy
import logging
import sys
import traceback
import typing as t

import hikari

from miru.exceptions import HandlerFullError

from .abc.item import DecoratedItem, ViewItem
from .abc.item_handler import ItemHandler
from .button import Button
from .context.view import AutodeferOptions, ViewContext
from .internal.types import ClientT, ViewResponseBuildersT
from .select import ChannelSelect, MentionableSelect, RoleSelect, TextSelect, UserSelect

if t.TYPE_CHECKING:
    import datetime

    import typing_extensions as te


logger = logging.getLogger(__name__)

ViewContextT = t.TypeVar("ViewContextT", bound=ViewContext[t.Any])
ViewT = t.TypeVar("ViewT", bound="View[t.Any]")

__all__ = ("View",)

COMPONENT_VIEW_ITEM_MAPPING: t.Mapping[hikari.ComponentType, t.Type[ViewItem[t.Any]]] = {
    hikari.ComponentType.BUTTON: Button,
    hikari.ComponentType.TEXT_SELECT_MENU: TextSelect,
    hikari.ComponentType.CHANNEL_SELECT_MENU: ChannelSelect,
    hikari.ComponentType.ROLE_SELECT_MENU: RoleSelect,
    hikari.ComponentType.USER_SELECT_MENU: UserSelect,
    hikari.ComponentType.MENTIONABLE_SELECT_MENU: MentionableSelect,
}
"""A mapping of all message component types to their respective item classes."""


class View(
    ItemHandler[
        ClientT,
        hikari.impl.MessageActionRowBuilder,
        ViewResponseBuildersT,
        ViewContext[ClientT],
        hikari.ComponentInteraction,
        ViewItem[ClientT],
    ]
):
    """Represents a set of Discord UI components attached to a message.

    Parameters
    ----------
    timeout : Optional[Union[float, int, datetime.timedelta]], optional
        The duration after which the view times out, in seconds, by default 120.0
    autodefer : bool | AutodeferOptions, optional
        If enabled, interactions will be automatically deferred if not responded to within 2 seconds, by default True
        You may also pass an instance of [miru.AutodeferOptions][miru.context.view.AutodeferOptions] to customize the autodefer behaviour.

    Raises
    ------
    ValueError
        Raised if a view has more than 25 components attached.
    RuntimeError
        Raised if miru.install() was never called before instantiation.
    """

    _view_children: t.ClassVar[
        t.MutableSequence[DecoratedItem[t.Any, te.Self, ViewItem[t.Any]]]
    ] = []  # Decorated callbacks that need to be turned into items

    def __init_subclass__(cls) -> None:
        """Get decorated callbacks."""
        children: t.MutableSequence[DecoratedItem[ClientT, te.Self, ViewItem[ClientT]]] = []
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
    def _builder(self) -> t.Type[hikari.impl.MessageActionRowBuilder]:
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
        timeout : Optional[float], optional
            The timeout of the created view, by default 120
        autodefer : bool, optional
            If enabled, interactions will be automatically deferred if not responded to within 2 seconds, by default True

        Returns
        -------
        View
            The view that represents the components attached to this message.

        !!! warning
            This function constructs a completely new view based on the information available in the message object.
            Any custom behaviour (such as callbacks) will not be re-created,
            if you want to access an already running view that is bound to a message, use :obj:`miru.view.get_view` instead.
        """
        view = cls(timeout=timeout, autodefer=autodefer)

        if not message.components:
            return view

        for row, action_row in enumerate(message.components):
            assert isinstance(action_row, hikari.ActionRowComponent)

            for component in action_row.components:
                if not isinstance(component.type, hikari.ComponentType):
                    continue  # Unrecognized component types are ignored
                comp_cls = COMPONENT_VIEW_ITEM_MAPPING[component.type]
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

    def add_item(self, item: ViewItem[ClientT]) -> te.Self:
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

    def remove_item(self, item: ViewItem[ClientT]) -> te.Self:
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

    async def view_check(self, context: ViewContext[ClientT]) -> bool:
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
        self, error: Exception, item: ViewItem[ClientT] | None = None, context: ViewContext[ClientT] | None = None
    ) -> None:
        """Called when an error occurs in a callback function or the built-in timeout function.
        Override for custom error-handling logic.

        Parameters
        ----------
        error : Exception
            The exception encountered.
        item : Optional[MessageItem[ViewT]], optional
            The item this exception originates from, if any.
        context : Optional[Context], optional
            The context associated with this exception, if any.
        """
        if item:
            print(f"Ignoring exception in view {self} for item {item}:", file=sys.stderr)
        else:
            print(f"Ignoring exception in view {self}:", file=sys.stderr)

        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def get_context(
        self, interaction: hikari.ComponentInteraction, *, cls: t.Type[ViewContext[ClientT]] = ViewContext
    ) -> ViewContext[ClientT]:
        """Get the context for this view. Override this function to provide a custom context object.

        Parameters
        ----------
        interaction : hikari.ComponentInteraction
            The interaction to construct the context from.
        cls : Type[ViewContext], optional
            The class to use for the context, by default ViewContext.

        Returns
        -------
        ViewContext
            The context for this interaction.
        """
        return cls(self, self.client, interaction)

    async def _handle_callback(self, item: ViewItem[ClientT], context: ViewContext[ClientT]) -> None:
        """Handle the callback of a view item. Separate task in case the view is stopped in the callback."""
        try:
            if not self._message or (self._message.id == context.message.id):
                self._message = context.message

            self._input_event.set()
            self._input_event.clear()

            await item._refresh_state(context)

            if self.autodefer.mode.should_autodefer:
                context._start_autodefer(self.autodefer)

            await item.callback(context)

        except Exception as error:
            await self.on_error(error, item, context)

    async def _invoke(self, interaction: hikari.ComponentInteraction) -> asyncio.Future[ViewResponseBuildersT] | None:
        """Process incoming interactions."""
        item = next((item for item in self.children if item.custom_id == interaction.custom_id), None)

        if not item:
            return

        self._reset_timeout()

        context = self.get_context(interaction)
        self._last_context = context

        passed = await self.view_check(context)
        if not passed:
            return

        assert isinstance(item, ViewItem)
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
        timeout : Optional[float], optional
            The amount of time to wait for input, in seconds, by default None
        """
        await asyncio.wait_for(self._input_event.wait(), timeout=timeout)

    def _client_start_hook(self, client: ClientT) -> None:
        """Called when a client wants to add the view itself."""
        self._client = client

        # Optimize URL-button-only views by not adding to listener
        if all((isinstance(item, Button) and item.url is not None) for item in self.children):
            logger.warning(
                f"View {type(self).__name__} only contains link buttons. Ignoring '{type(client).__name__}.start_view()' call."
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
