import asyncio
import inspect
import itertools
import sys
import traceback
from typing import List
from typing import Optional

import hikari

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

    views: List["View"] = []

    def __init__(self, app: hikari.GatewayBot, *, timeout: Optional[float] = 120.0):
        self.timeout: Optional[float] = float(timeout) if timeout else None
        self.children: List[Item] = []
        self.app: hikari.GatewayBot = app
        self.message: Optional[hikari.Message] = None

        self._weights = _Weights(self.children)
        self._stopped: asyncio.Event = asyncio.Event()
        self._listener_task: Optional[asyncio.Task[None]] = None
        self._timeout_task: Optional[asyncio.Task[None]] = None

        if not isinstance(self.app, hikari.GatewayBot):
            raise TypeError("Expected instance of hikari.GatewayBot.")

    @property
    def is_persistent(self) -> bool:
        """
        Determines if this view is persistent or not.
        """

        return self.timeout is None and all(item._persistent for item in self.children)

    def add_item(self, item: Item) -> None:
        """Add a new item to the view."""

        if len(self.children) > 25:
            raise ValueError("Maximum number of items exceeded.")

        if not isinstance(item, Item):
            raise TypeError("Expected Item.")

        self._weights.add_item(item)

        item._view = self
        self.children.append(item)

    def remove_item(self, item: Item) -> None:
        """Remove the specified item from the view."""
        try:
            self.children.remove(item)
        except ValueError:
            pass
        else:
            self._weights.clear()

    def clear_items(self) -> None:
        """Removes all items from this view."""
        self.children.clear()
        self._weights.clear()

    def build(self) -> List[hikari.api.ActionRowBuilder]:
        """Converts the view into action rows, must be called before sending."""
        if len(self.children) == 0:
            raise ValueError("Empty views cannot be built.")

        self.children.sort(key=lambda i: i._rendered_row or float("inf"))

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

    async def view_check(self, interaction: hikari.ComponentInteraction) -> bool:
        """
        Called before any callback in the view is called. Must evaluate to a truthy value to pass.
        """
        return True

    async def on_error(
        self, error: Exception, item: Optional[Item] = None, interaction: Optional[hikari.ComponentInteraction] = None
    ) -> None:
        """
        Called when an error occurs in a callback function or the built-in timeout function.
        """
        if item:
            print(f"Ignoring exception in view {self} for item {item}:", file=sys.stderr)
        else:
            print(f"Ignoring exception in view {self}:", file=sys.stderr)

        traceback.print_exception(error.__class__, error, error.__traceback__, file=sys.stderr)

    async def stop(self) -> None:
        """
        Stop listening for interactions.
        """
        if self._listener_task is not None:
            self._listener_task.cancel()
        if self._timeout_task is not None:
            self._timeout_task.cancel()
        self._stopped.set()
        View.views.remove(self)

    async def _process_interactions(self, event: hikari.InteractionCreateEvent) -> None:

        if isinstance(event.interaction, hikari.ComponentInteraction):

            interaction = event.interaction

            passed = await self.view_check(interaction)
            if not passed:
                return

            items = [item for item in self.children if item.custom_id == interaction.custom_id]
            if len(items) > 0:

                for item in items:
                    try:
                        await item._refresh(interaction)

                        if len(inspect.signature(item.callback).parameters) > 1:
                            await item.callback(interaction)

                        else:
                            await item.callback(interaction)

                    except Exception as error:
                        await self.on_error(error, item, interaction)

    async def _listen_for_events(self, message_id: int) -> None:
        while True:
            event = await self.app.wait_for(
                hikari.InteractionCreateEvent,
                timeout=None,
                predicate=lambda e: isinstance(e.interaction, hikari.ComponentInteraction)
                and e.interaction.message.id == message_id,
            )

            await self._process_interactions(event)

    async def _calculate_timeout(self) -> None:
        await asyncio.sleep(self.timeout or 0)

        if self._listener_task is not None:
            self._listener_task.cancel()
        self._listener_task = None
        self._stopped.set()

        try:
            await self.on_timeout()
        except Exception as error:
            await self.on_error(error)

        self._timeout_task = None
        View.views.remove(self)

    async def wait(self) -> None:
        """
        Wait until the view times out or stopped manually.
        """
        await asyncio.wait_for(self._stopped.wait(), timeout=None)

    async def start_listener(self, message_id: int) -> None:
        """
        Re-registers a persistent view for listening after an application restart.
        """
        if not self.is_persistent:
            raise ValueError("This can only be used on persistent views.")

        self._listener_task = asyncio.create_task(self._listen_for_events(message_id))
        View.views.append(self)

    async def start(self, message: hikari.Message) -> None:
        """
        Start up the view and begin listening for interactions.
        """
        if not isinstance(message, hikari.Message):
            raise TypeError("Expected instance of hikari.Message.")

        self.message = message
        self._listener_task = asyncio.create_task(self._listen_for_events(message.id))

        if self.timeout:
            self._timeout_task = asyncio.create_task(self._calculate_timeout())
        View.views.append(self)
