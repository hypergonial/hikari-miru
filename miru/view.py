"""
MIT License

Copyright (c) 2022-present HyperGH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import asyncio
import itertools
import sys
import traceback
from functools import partial
from typing import Callable
from typing import ClassVar
from typing import List
from typing import Optional

import hikari

from .interaction import Interaction
from .item import Item


class _Weights:
    """
    Calculate the position of an item based on it's width, and keep track of item positions
    """

    def __init__(self, children: List[Item]):

        self._weights = [0, 0, 0, 0, 0]

        for item in children:
            self.add_item(item)

    def add_item(self, item: Item) -> None:
        if item.row is not None:
            if item.width + self._weights[item.row] > 5:
                raise ValueError(f"Item does not fit on row {item.row}!")

            self._weights[item.row] += item.width
            item._rendered_row = item.row
        else:
            for row, weight in enumerate(self._weights):
                if weight + item.width <= 5:
                    self._weights[row] += item.width
                    item._rendered_row = row + 1
                    break

    def remove_item(self, item: Item) -> None:
        if item._row:
            self._weights[item._row] -= item.width
            item._rendered_row = None

    def clear(self) -> None:
        self._weights = [0, 0, 0, 0, 0]


class View:
    """
    Represents a set of Discord UI components.
    """

    persistent_views: List["View"] = []  # List of all currently active persistent views
    _view_children: ClassVar[List["Callable"]] = []  # Decorated callbacks that need to be turned into items

    def __init_subclass__(cls) -> None:
        """
        Get decorated callbacks
        """
        children: List[Callable] = []
        for base_cls in reversed(cls.mro()):
            for func in base_cls.__dict__.values():
                if hasattr(func, "_view_item_type"):
                    children.append(func)

        if len(children) > 25:
            raise ValueError("View cannot have more than 25 components attached.")

        cls._view_children = children

    def __init__(
        self,
        app: hikari.GatewayBot,
        *,
        timeout: Optional[float] = 120.0,
        autodefer: Optional[bool] = True,
    ) -> None:
        self._timeout: Optional[float] = float(timeout) if timeout else None
        self._children: List[Item] = []
        self._app: hikari.GatewayBot = app
        self._autodefer: Optional[bool] = autodefer
        self._message: Optional[hikari.Message] = None

        self._weights = _Weights(self.children)
        self._stopped: asyncio.Event = asyncio.Event()
        self._listener_task: Optional[asyncio.Task[None]] = None

        for callable in self._view_children:  # Sort and instantiate decorated callbacks
            item = callable._view_item_type(**callable._view_item_data)
            item.callback = partial(callable, self, item)
            self.add_item(item)
            setattr(self, callable.__name__, item)

        if len(self.children) > 25:
            raise ValueError("View cannot have more than 25 components attached.")

        if not isinstance(self.app, hikari.GatewayBot):
            raise TypeError("Expected instance of hikari.GatewayBot.")

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
    def children(self) -> List[Item]:
        """
        A list of all items attached to the view.
        """
        return self._children

    @property
    def app(self) -> hikari.GatewayBot:
        """
        The application that instantiated the view.
        """
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

    def add_item(self, item: Item) -> None:
        """Adds a new item to the view."""

        if len(self.children) > 25:
            raise ValueError("View cannot have more than 25 components attached.")

        if not isinstance(item, Item):
            raise TypeError("Expected Item.")

        self._weights.add_item(item)

        item._view = self
        self.children.append(item)

    def remove_item(self, item: Item) -> None:
        """Removes the specified item from the view."""
        try:
            self.children.remove(item)
        except ValueError:
            pass
        else:
            self._weights.remove_item(item)

    def clear_items(self) -> None:
        """Removes all items from this view."""
        self.children.clear()
        self._weights.clear()

    def build(self) -> List[hikari.api.ActionRowBuilder]:
        """Converts the view into action rows, must be called before sending."""
        if len(self.children) == 0:
            raise ValueError("Empty views cannot be built.")

        self.children.sort(key=lambda i: i._rendered_row or sys.maxsize)

        action_rows = []

        for row, items in itertools.groupby(self.children, lambda i: i._rendered_row):
            action_row = self.app.rest.build_action_row()
            for item in items:
                item._build(action_row)
            action_rows.append(action_row)
        return action_rows

    async def on_timeout(self) -> None:
        """
        Called when the view times out.
        """
        pass

    async def view_check(self, interaction: Interaction) -> bool:
        """
        Called before any callback in the view is called. Must evaluate to a truthy value to pass.
        """
        return True

    async def on_error(
        self, error: Exception, item: Optional[Item] = None, interaction: Optional[Interaction] = None
    ) -> None:
        """
        Called when an error occurs in a callback function or the built-in timeout function.
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
        if self._listener_task is not None:
            self._listener_task.cancel()
        self._stopped.set()
        if self.is_persistent:
            View.persistent_views.remove(self)

    async def _handle_callback(self, item: Item, interaction: Interaction) -> None:
        """
        Handle the callback of a view item. Seperate task in case the view is stopped in the callback.
        """
        try:
            await item._refresh(interaction)
            await item.callback(interaction)

            if not interaction._issued_response and self.autodefer:
                await interaction.defer()

        except Exception as error:
            await self.on_error(error, item, interaction)

    async def _process_interactions(self, event: hikari.InteractionCreateEvent) -> None:
        """
        Process incoming interactions and convert interaction to miru.Interaction
        """

        if isinstance(event.interaction, hikari.ComponentInteraction):

            interaction: Interaction = Interaction.from_hikari(event.interaction)

            items = [item for item in self.children if item.custom_id == interaction.custom_id]
            if len(items) > 0:

                passed = await self.view_check(interaction)
                if not passed:
                    return

                for item in items:
                    # Create task here to ensure autodefer works even if callback stops view
                    asyncio.create_task(self._handle_callback(item, interaction))

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
                event = await self.app.wait_for(
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

        if self._listener_task is not None:
            self._listener_task.cancel()

        self._listener_task = None
        self._stopped.set()

        try:
            await self.on_timeout()
        except Exception as error:
            await self.on_error(error)

    async def wait(self) -> None:
        """
        Wait until the view times out or gets stopped manually.
        """
        await asyncio.wait_for(self._stopped.wait(), timeout=None)

    def start_listener(self, message_id: Optional[int] = None) -> None:
        """
        Re-registers a persistent view for listening after an application restart. Specify message_id for improved listener accuracy.
        """
        if not self.is_persistent:
            raise ValueError("This can only be used on persistent views.")

        self._listener_task = asyncio.create_task(self._listen_for_events(message_id))
        View.persistent_views.append(self)

    def start(self, message: hikari.Message) -> None:
        """
        Start up the view and begin listening for interactions.
        """
        if not isinstance(message, hikari.Message):
            raise TypeError("Expected instance of hikari.Message.")

        self._message = message
        self._listener_task = asyncio.create_task(self._listen_for_events(message.id))

        if self.is_persistent:
            View.persistent_views.append(self)
