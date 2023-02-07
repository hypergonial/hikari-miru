from __future__ import annotations

import asyncio
import copy
import datetime
import inspect
import logging
import sys
import traceback
import typing as t

import hikari

from miru.exceptions import BootstrapFailureError
from miru.exceptions import HandlerFullError

from .abc.item import DecoratedItem
from .abc.item import Item
from .abc.item import ViewItem
from .abc.item_handler import ItemHandler
from .button import Button
from .context.view import ViewContext
from .select import ChannelSelect
from .select import MentionableSelect
from .select import RoleSelect
from .select import TextSelect
from .select import UserSelect

logger = logging.getLogger(__name__)

__all__ = (
    "View",
    "get_view",
)

COMPONENT_VIEW_ITEM_MAPPING: t.Mapping[hikari.ComponentType, t.Type[ViewItem]] = {
    hikari.ComponentType.BUTTON: Button,
    hikari.ComponentType.TEXT_SELECT_MENU: TextSelect,
    hikari.ComponentType.CHANNEL_SELECT_MENU: ChannelSelect,
    hikari.ComponentType.ROLE_SELECT_MENU: RoleSelect,
    hikari.ComponentType.USER_SELECT_MENU: UserSelect,
    hikari.ComponentType.MENTIONABLE_SELECT_MENU: MentionableSelect,
}
"""A mapping of all message component types to their respective item classes."""


class View(ItemHandler[hikari.impl.MessageActionRowBuilder]):
    """Represents a set of Discord UI components attached to a message.

    Parameters
    ----------
    timeout : Optional[float], optional
        The duration after which the view times out, in seconds, by default 120.0
    autodefer : bool, optional
        If unhandled interactions should be automatically deferred or not, by default True

    Raises
    ------
    ValueError
        Raised if a view has more than 25 components attached.
    RuntimeError
        Raised if miru.install() was never called before instantiation.
    """

    _view_children: t.Sequence[DecoratedItem] = []  # Decorated callbacks that need to be turned into items

    def __init_subclass__(cls) -> None:
        """
        Get decorated callbacks
        """
        children: t.MutableSequence[DecoratedItem] = []
        for base_cls in reversed(cls.mro()):
            for value in base_cls.__dict__.values():
                if isinstance(value, DecoratedItem):
                    children.append(value)

        if len(children) > 25:
            raise HandlerFullError("View cannot have more than 25 components attached.")

        cls._view_children = children

    def __init__(
        self,
        *,
        timeout: t.Optional[t.Union[float, int, datetime.timedelta]] = 120.0,
        autodefer: bool = True,
    ) -> None:
        super().__init__(timeout=timeout)
        self._autodefer: bool = autodefer
        self._message: t.Optional[hikari.Message] = None
        self._message_id: t.Optional[hikari.Snowflake] = None
        self._input_event: asyncio.Event = asyncio.Event()

        for decorated_item in self._view_children:  # Sort and instantiate decorated callbacks
            # Must deepcopy, otherwise multiple views will have the same item reference
            decorated_item = copy.deepcopy(decorated_item)
            item = decorated_item.build(self)
            self.add_item(item)
            setattr(self, decorated_item.name, item)

    @property
    def is_persistent(self) -> bool:
        """
        Determines if this view is persistent or not.
        """

        return self.timeout is None and all(
            isinstance(item, ViewItem) and item._is_persistent for item in self.children
        )

    @property
    def message(self) -> t.Optional[hikari.Message]:
        """
        The message this view is bound to. Will be None if the view is not bound, or if a message_id was passed to view.start().
        """
        return self._message

    @property
    def message_id(self) -> t.Optional[hikari.Snowflake]:
        """
        The message ID this view is bound to. Will be None if the view is an unbound persistent view.
        """
        return self._message_id

    @property
    def is_bound(self) -> bool:
        """
        Determines if the view is bound to a message or not. If this is False, message edits will not be supported.
        """
        return self._message_id is not None

    @property
    def autodefer(self) -> bool:
        """
        A boolean indicating if the received interaction should automatically be deferred if not responded to or not.
        """
        return self._autodefer

    @property
    def last_context(self) -> t.Optional[ViewContext]:
        """
        The last context that was received by the view.
        """
        return t.cast(ViewContext, self._last_context)

    @property
    def _builder(self) -> type[hikari.impl.MessageActionRowBuilder]:
        return hikari.impl.MessageActionRowBuilder

    @property
    def children(self) -> t.Sequence[ViewItem]:
        return t.cast(t.Sequence[ViewItem], super().children)

    @classmethod
    def from_message(cls, message: hikari.Message, *, timeout: t.Optional[float] = 120, autodefer: bool = True) -> View:
        """Create a new view from the components included in the passed message. Returns an empty view if the message has no components attached.

        Parameters
        ----------
        message : hikari.Message
            The message to read components from
        timeout : Optional[float], optional
            The timeout of the created view, by default 120
        autodefer : bool, optional
            If unhandled interactions should be automatically deferred or not, by default True

        Returns
        -------
        View
            The view that represents the components attached to this message.

        .. warning::
            This function constructs a completely new view based on the information available in the message object.
            Any custom behaviour (such as callbacks) will not be re-created, if you want to access an already running view that is bound to a message, use :obj:`miru.view.get_view` instead.
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

    def add_item(self: View, item: Item[hikari.impl.MessageActionRowBuilder]) -> View:
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

        if not isinstance(item, ViewItem):
            raise TypeError(f"Expected type ViewItem for parameter item, not {item.__class__.__name__}.")

        return t.cast(View, super().add_item(item))

    def remove_item(self, item: Item[hikari.impl.MessageActionRowBuilder]) -> View:
        return t.cast(View, super().remove_item(item))

    def clear_items(self) -> View:
        return t.cast(View, super().clear_items())

    async def view_check(self, context: ViewContext) -> bool:
        """Called before any callback in the view is called. Must evaluate to a truthy value to pass.
        Override for custom check logic.

        Parameters
        ----------
        context : Context
            The context for this check.

        Returns
        -------
        bool
            A boolean indicating if the check passed or not.
        """
        return True

    async def on_error(
        self,
        error: Exception,
        item: t.Optional[ViewItem] = None,
        context: t.Optional[ViewContext] = None,
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

        traceback.print_exception(error.__class__, error, error.__traceback__, file=sys.stderr)

    def get_context(
        self, interaction: hikari.ComponentInteraction, *, cls: t.Type[ViewContext] = ViewContext
    ) -> ViewContext:
        """
        Get the context for this view. Override this function to provide a custom context object.

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
        return cls(self, interaction)

    async def _handle_callback(self, item: ViewItem, context: ViewContext) -> None:
        """
        Handle the callback of a view item. Seperate task in case the view is stopped in the callback.
        """
        try:
            now = datetime.datetime.now()
            self._input_event.set()
            self._input_event.clear()

            await item._refresh_state(context)
            await item.callback(context)

            if not context._issued_response and self.autodefer:
                if (datetime.datetime.now() - now).total_seconds() <= 3:  # Avoid deferring if inter already timed out
                    await context.defer()

        except Exception as error:
            await self.on_error(error, item, context)

    async def _process_interactions(self, event: hikari.InteractionCreateEvent) -> None:
        """
        Process incoming interactions.
        """

        if not isinstance(event.interaction, hikari.ComponentInteraction):
            return

        items = [item for item in self.children if item.custom_id == event.interaction.custom_id]
        if items:
            self._reset_timeout()

            context = self.get_context(event.interaction)
            self._last_context = context

            passed = await self.view_check(context)
            if not passed:
                return

            for item in items:
                assert isinstance(item, ViewItem)
                # Create task here to ensure autodefer works even if callback stops view
                self._create_task(self._handle_callback(item, context))

    def stop(self) -> None:
        self._input_event.set()
        return super().stop()

    async def wait_for_input(self, timeout: t.Optional[float] = None) -> None:
        """Wait for any input to be received. This will also unblock if the view was stopped, thus
        it is recommended to check for the presence of a value after this function returns.

        Parameters
        ----------
        timeout : Optional[float], optional
            The amount of time to wait for input, in seconds, by default None
        """
        await asyncio.wait_for(self._input_event.wait(), timeout=timeout)

    async def start(
        self,
        message: t.Optional[
            t.Union[
                hikari.SnowflakeishOr[hikari.PartialMessage], t.Awaitable[hikari.SnowflakeishOr[hikari.PartialMessage]]
            ]
        ] = None,
    ) -> None:
        """Start up the view and begin listening for interactions.

        Parameters
        ----------
        message : Union[hikari.Message, Awaitable[hikari.Message]]
            If provided, the view will be bound to this message, and if the
            message is edited with a new view, this view will be stopped.
            Unbound views do not support message editing with additional views.

        Raises
        ------
        TypeError
            Parameter 'message' cannot be resolved to an instance of 'hikari.Message'.
        BootstrapFailureError
            miru.install() was not called before starting a view.
        """
        if self._events is None:
            raise BootstrapFailureError(f"Cannot start View {type(self).__name__} before calling miru.install() first.")

        # Optimize URL-button-only views by not adding to listener
        if all((isinstance(item, Button) and item.url is not None) for item in self.children):
            logger.warning(f"View {type(self).__name__} only contains link buttons. Ignoring 'View.start()' call.")
            return

        if message is None and not self.is_persistent:
            raise ValueError(f"View '{type(self).__name__}' is not persistent, parameter 'message' must be provided.")

        if message is None:
            self._events.add_handler(self)
            return

        result = (await message) if inspect.isawaitable(message) else message
        if not isinstance(result, (hikari.PartialMessage, hikari.Snowflake, int)):
            raise TypeError("Parameter 'message' cannot be resolved to an instance of 'hikari.Message'.")

        self._message_id = hikari.Snowflake(result)

        if isinstance(result, hikari.Message):
            self._message = result

        self._events.add_handler(self)
        self._timeout_task = self._create_task(self._handle_timeout())


def get_view(message: hikari.SnowflakeishOr[hikari.PartialMessage]) -> t.Optional[View]:
    """Get a currently running view that is attached to the provided message.

    Parameters
    ----------
    message : hikari.SnowflakeishOr[hikari.PartialMessage]
        The message the view is attached to.

    Returns
    -------
    Optional[View]
        The view bound to this message, if any.

    Raises
    ------
    BootstrapFailureError
        miru.install() was not called before this operation.
    """

    if View._events is None:
        raise BootstrapFailureError("miru is not yet initialized! Please call miru.install() first.")

    message_id = hikari.Snowflake(message)

    if view := View._events._bound_handlers.get(message_id):
        if isinstance(view, View):
            return view

    return None


# MIT License
#
# Copyright (c) 2022-present HyperGH
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
