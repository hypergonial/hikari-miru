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

from __future__ import annotations

import asyncio
import copy
import itertools
import sys
import traceback
from typing import Any
from typing import ClassVar
from typing import ContextManager
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import TypeVar

import hikari

from .context import Context
from .interaction import Interaction
from .item import DecoratedItem
from .item import Item
from .traits import ViewsAware

ViewT = TypeVar("ViewT", bound="View")

__all__ = ["View", "load", "unload", "get_view"]


class _Weights(Generic[ViewT]):
    """
    Calculate the position of an item based on it's width, and keep track of item positions
    """

    def __init__(self) -> None:

        self._weights = [0, 0, 0, 0, 0]

    def add_item(self, item: Item[ViewT]) -> None:
        if item.row is not None:
            if item.width + self._weights[item.row] > 5:
                raise ValueError(f"Item does not fit on row {item.row}!")

            self._weights[item.row] += item.width
            item._rendered_row = item.row
        else:
            for row, weight in enumerate(self._weights):
                if weight + item.width <= 5:
                    self._weights[row] += item.width
                    item._rendered_row = row
                    break

    def remove_item(self, item: Item[ViewT]) -> None:
        if item._rendered_row is not None:
            self._weights[item._rendered_row] -= item.width
            item._rendered_row = None

    def clear(self) -> None:
        self._weights = [0, 0, 0, 0, 0]


class View:
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
        Raised if miru.load() was never called before instantiation.
    """

    _app: ClassVar[Optional[ViewsAware]] = None
    _view_children: ClassVar[List[DecoratedItem]] = []  # Decorated callbacks that need to be turned into items
    # Mapping of message_id: View
    _views: Dict[int, View] = {}  # List of all currently active BOUND views, unbound persistent are not listed here

    def __init_subclass__(cls) -> None:
        """
        Get decorated callbacks
        """
        children: List[DecoratedItem] = []
        for base_cls in reversed(cls.mro()):
            for value in base_cls.__dict__.values():
                if isinstance(value, DecoratedItem):
                    children.append(value)

        if len(children) > 25:
            raise ValueError("View cannot have more than 25 components attached.")

        cls._view_children = children

    def __init__(
        self,
        *,
        timeout: Optional[float] = 120.0,
        autodefer: bool = True,
    ) -> None:
        self._timeout: Optional[float] = float(timeout) if timeout else None
        self._children: List[Item[Any]] = []
        self._autodefer: bool = autodefer
        self._message: Optional[hikari.Message] = None
        self._message_id: Optional[int] = None  # Only for bound persistent views

        self._weights: _Weights[View] = _Weights()
        self._stopped: asyncio.Event = asyncio.Event()
        self._listener_task: Optional[asyncio.Task[None]] = None

        for decorated_item in self._view_children:  # Sort and instantiate decorated callbacks
            # Must deepcopy, otherwise multiple views will have the same item reference
            decorated_item = copy.deepcopy(decorated_item)
            item = decorated_item.build(self)
            self.add_item(item)
            setattr(self, decorated_item.name, item)

        if len(self.children) > 25:
            raise ValueError("View cannot have more than 25 components attached.")

        if self.app is None:
            raise RuntimeError("miru.load() was never called before instantiation of View.")

    @property
    def is_persistent(self) -> bool:
        """
        Determines if this view is persistent or not.
        """

        return self.timeout is None and all(item._persistent for item in self.children)

    @property
    def timeout(self) -> Optional[float]:
        """
        The amount of time the view is allowed to idle for, in seconds. Must be None for persistent views.
        """
        return self._timeout

    @property
    def children(self: ViewT) -> List[Item[ViewT]]:
        """
        A list of all items attached to the view.
        """
        return self._children

    @property
    def app(self) -> ViewsAware:
        """
        The application that loaded the miru extension.
        """
        if not self._app:
            raise AttributeError("miru was not loaded, View has no attribute app.")

        return self._app

    @property
    def autodefer(self) -> Optional[bool]:
        """
        A boolean indicating if received interactions should automatically be deferred if not responded to or not.
        """
        return self._autodefer

    @property
    def message(self) -> Optional[hikari.Message]:
        """
        The message this view is attached to. This is None if the view was started with start_listener().
        """
        return self._message

    @property
    def is_bound(self) -> bool:
        """
        Determines if the view is bound to a message or not. If this is False, message edits will not be supported.
        """
        return True if self._message_id is not None else False

    def add_item(self, item: Item[Any]) -> None:
        """Adds a new item to the view.

        Parameters
        ----------
        item : Item[Any]
            The item to be added.

        Raises
        ------
        ValueError
            A view already has 25 components attached.
        TypeError
            Parameter item is not an instance of Item.
        RuntimeError
            The item is already attached to this view.
        RuntimeError
            The item is already attached to another view.
        """

        if len(self.children) > 25:
            raise ValueError("View cannot have more than 25 components attached.")

        if not isinstance(item, Item):
            raise TypeError(f"Expected Item not {type(item)} for parameter item.")

        if item in self.children:
            raise RuntimeError("Item is already attached to this view.")

        if hasattr(item, "_view") and item._view is not None:
            raise RuntimeError("Item is already attached to a view.")

        self._weights.add_item(item)

        item._view = self
        self.children.append(item)

    def remove_item(self, item: Item[Any]) -> None:
        """Removes the specified item from the view.

        Parameters
        ----------
        item : Item[Any]
            The item to be removed.
        """
        try:
            self.children.remove(item)
        except ValueError:
            pass
        else:
            self._weights.remove_item(item)
            item._view = None

    def clear_items(self) -> None:
        """Removes all items from this view."""
        for item in self.children:
            item._view = None
            item._rendered_row = None

        self.children.clear()
        self._weights.clear()

    def build(self) -> List[hikari.impl.ActionRowBuilder]:
        """Converts the view into action rows, must be called before sending.

        Returns
        -------
        List[hikari.impl.ActionRowBuilder]
            A list of action rows containing all items attached to this view,
            converted to hikari component objects.

        Raises
        ------
        ValueError
            The view has no items attached to it.
        """
        if len(self.children) == 0:
            raise ValueError("Empty views cannot be built.")

        self.children.sort(key=lambda i: i._rendered_row if i._rendered_row is not None else sys.maxsize)

        action_rows = []

        for row, items in itertools.groupby(self.children, lambda i: i._rendered_row):
            action_row = hikari.impl.ActionRowBuilder()
            for item in items:
                item._build(action_row)
            action_rows.append(action_row)
        return action_rows

    async def on_timeout(self) -> None:
        """
        Called when the view times out. Override for custom timeout logic.
        """
        pass

    async def view_check(self, context: Context) -> bool:
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
        self: ViewT,
        error: Exception,
        item: Optional[Item[ViewT]] = None,
        context: Optional[Context] = None,
    ) -> None:
        """Called when an error occurs in a callback function or the built-in timeout function.
        Override for custom error-handling logic.

        Parameters
        ----------
        error : Exception
            The exception encountered.
        item : Optional[Item[ViewT]], optional
            The item this exception originates from, if any.
        context : Optional[Context], optional
            The context associated with this exception, if any.
        """
        if item:
            print(f"Ignoring exception in view {self} for item {item}:", file=sys.stderr)
        else:
            print(f"Ignoring exception in view {self}:", file=sys.stderr)

        traceback.print_exception(error.__class__, error, error.__traceback__, file=sys.stderr)

    def stop(self) -> None:
        """
        Stop listening for interactions.
        """
        if self._message_id:
            View._views.pop(self._message_id)

        if self._listener_task is not None:
            self._listener_task.cancel()

        self._stopped.set()

        self._listener_task = None

    async def _handle_callback(self: ViewT, item: Item[ViewT], context: Context) -> None:
        """
        Handle the callback of a view item. Seperate task in case the view is stopped in the callback.
        """

        try:
            await item._refresh(context.interaction)
            await item.callback(context)

            if not context.interaction._issued_response and self.autodefer:
                await context.defer()

        except Exception as error:
            await self.on_error(error, item, context)

    async def _process_interactions(self, event: hikari.InteractionCreateEvent) -> None:
        """
        Process incoming interactions and convert interaction to miru.Interaction
        """

        if isinstance(event.interaction, hikari.ComponentInteraction):

            interaction: Interaction = Interaction.from_hikari(event.interaction)

            items = [item for item in self.children if item.custom_id == interaction.custom_id]
            if len(items) > 0:

                context = Context(self, interaction)

                passed = await self.view_check(context)
                if not passed:
                    return

                for item in items:
                    # Create task here to ensure autodefer works even if callback stops view
                    asyncio.create_task(self._handle_callback(item, context))

    async def _listen_for_events(self, message_id: Optional[int] = None) -> None:
        """
        Listen for incoming interaction events through the gateway.
        """

        if message_id:
            predicate = (
                lambda e: isinstance(e.interaction, hikari.ComponentInteraction)
                and e.interaction.message.id == message_id
            )
        else:
            predicate = lambda e: isinstance(e.interaction, hikari.ComponentInteraction)

        while True:
            try:
                event = await self.app.event_manager.wait_for(
                    hikari.InteractionCreateEvent,
                    timeout=self.timeout,
                    predicate=predicate,
                )
            except asyncio.TimeoutError:
                # Handle timeouts, stop listening
                await self._handle_timeout()

            else:
                await self._process_interactions(event)

    async def _handle_timeout(self) -> None:
        """
        Handle the timing out of the view.
        """
        if self._message_id:
            View._views.pop(self._message_id)
        try:
            await self.on_timeout()
        except Exception as error:
            await self.on_error(error)

        self._stopped.set()

        if self._listener_task is not None:
            self._listener_task.cancel()

        self._listener_task = None

    async def wait(self) -> None:
        """
        Wait until the view times out or gets stopped manually.
        """
        await asyncio.wait_for(self._stopped.wait(), timeout=None)

    def start_listener(self, message: Optional[hikari.SnowflakeishOr[hikari.PartialMessage]] = None) -> None:
        """Re-registers a persistent view for listening after an application restart.
        Specify message_id to create a bound persistent view that can be edited afterwards.

        Parameters
        ----------
        message: Optional[hikari.SnowflakeishOr[hikari.PartialMessage]], optional
            If provided, the persistent view will be bound to this message, and if the
            message is edited with a new view, that will be taken into account.
            Unbound views do not support message editing with additional views.

        Raises
        ------
        ValueError
            The view is not persistent.
        """
        if not self.is_persistent:
            raise ValueError("This can only be used on persistent views.")

        message_id = hikari.Snowflake(message) if message else None

        if message_id:
            self._message_id = message_id

            # Handle replacement of bound views on message edit
            if message_id in View._views.keys():
                View._views[message_id].stop()

            View._views[message_id] = self

        self._listener_task = asyncio.create_task(self._listen_for_events(message_id))

    def start(self, message: hikari.Message) -> None:
        """Start up the view and begin listening for interactions.

        Parameters
        ----------
        message : hikari.Message
            The message the view was built for.

        Raises
        ------
        TypeError
            Parameter message is not an instance of hikari.Message
        """
        if not isinstance(message, hikari.Message):
            raise TypeError("Expected instance of hikari.Message.")

        self._message = message
        self._message_id = message.id
        self._listener_task = asyncio.create_task(self._listen_for_events(message.id))

        # Handle replacement of view on message edit
        if message.id in View._views.keys():
            View._views[message.id].stop()

        View._views[message.id] = self


def load(bot: ViewsAware) -> None:
    """Load miru and pass the current running application to it.

    Parameters
    ----------
    bot : ViewsAware
        The currently running application. Must implement traits
        RESTAware and EventManagerAware.

    Raises
    ------
    RuntimeError
        miru is already loaded
    TypeError
        Parameter bot does not have traits specified in ViewsAware
    """
    if View._app is not None:
        raise RuntimeError("miru is already loaded!")
    if not isinstance(bot, ViewsAware):
        raise TypeError(f"Expected type with trait ViewsAware for parameter bot, not {type(bot)}")

    View._app = bot


def unload() -> None:
    """Unload miru and remove the current running application from it.

    .. warning::
        Unbound persistent views should be stopped manually.
    """
    for message, view in View._views.items():
        view.stop()

    View._app = None


def get_view(message: hikari.SnowflakeishOr[hikari.PartialMessage]) -> Optional[View]:
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
    RuntimeError
        miru was not loaded before this call.
    """

    if View._app is None:
        raise RuntimeError("miru is not yet loaded! Please call miru.load() first.")

    message_id = hikari.Snowflake(message)

    if int(message_id) in View._views.keys():
        return View._views[message_id]

    return None
