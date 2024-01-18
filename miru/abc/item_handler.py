from __future__ import annotations

import abc
import asyncio
import datetime
import itertools
import sys
import typing as t
from collections.abc import Sequence

from miru.abc.item import Item
from miru.exceptions import HandlerFullError, ItemAlreadyAttachedError, RowFullError
from miru.internal.types import BuilderT, ContextT, InteractionT, ItemT, RespBuilderT

if t.TYPE_CHECKING:
    import typing_extensions as te

    from miru import Client

__all__ = ("ItemHandler",)


class _ItemArranger(t.Generic[ItemT]):
    """Calculate the position of an item based on it's width, and automatically arrange items if no explicit row is specified.

    Used internally by ItemHandler.
    """

    __slots__ = ("_weights",)

    def __init__(self) -> None:
        self._weights = [0, 0, 0, 0, 0]

    def add_item(self, item: ItemT) -> None:
        """Add an item to the weights.

        Parameters
        ----------
        item : ItemT
            The item to add.

        Raises
        ------
        RowFullError
            The item does not fit on the row specified.
            This error is only raised if a row is specified explicitly.
        HandlerFullError
            The item does not fit on any row.
        """
        if item.row is not None:
            if item.width + self._weights[item.row] > 5:
                raise RowFullError(f"Item does not fit on row {item.row}!")

            self._weights[item.row] += item.width
            item._rendered_row = item.row
        else:
            for row, weight in enumerate(self._weights):
                if weight + item.width <= 5:
                    self._weights[row] += item.width
                    item._rendered_row = row
                    return
            raise HandlerFullError("Item does not fit on this item handler.")

    def remove_item(self, item: ItemT) -> None:
        """Remove an item from the weights.

        Parameters
        ----------
        item : ItemT
            The item to remove.
        """
        if item._rendered_row is not None:
            self._weights[item._rendered_row] -= item.width
            item._rendered_row = None

    def clear(self) -> None:
        """Clear the weights, remove all items."""
        self._weights = [0, 0, 0, 0, 0]


class ItemHandler(Sequence[BuilderT], abc.ABC, t.Generic[BuilderT, RespBuilderT, ContextT, InteractionT, ItemT]):
    """Abstract base class all item-handlers (e.g. views, modals) inherit from.

    Parameters
    ----------
    timeout : Optional[Union[float, int, datetime.timedelta]]
        The duration after which the item handler times out, in seconds

    Raises
    ------
    HandlerFullError
        Raised if the item handler has more than 25 components attached.
    """

    def __init__(self, *, timeout: float | int | datetime.timedelta | None = 120.0) -> None:
        if isinstance(timeout, datetime.timedelta):
            timeout = timeout.total_seconds()

        self._client: Client | None = None
        self._timeout: float | None = float(timeout) if timeout else None
        self._children: list[ItemT] = []

        self._arranger: _ItemArranger[ItemT] = _ItemArranger()
        self._stopped: asyncio.Event = asyncio.Event()
        self._timeout_task: asyncio.Task[None] | None = None
        self._running_tasks: t.MutableSequence[asyncio.Task[t.Any]] = []
        self._last_context: ContextT | None = None

        if len(self.children) > 25:
            raise HandlerFullError(f"{type(self).__name__} cannot have more than 25 components attached.")

    @t.overload
    def __getitem__(self, value: int) -> BuilderT:
        ...

    @t.overload
    def __getitem__(self, value: slice) -> list[BuilderT]:
        ...

    def __getitem__(self, value: slice | int) -> BuilderT | t.Sequence[BuilderT]:
        return self.build()[value]

    def __iter__(self) -> t.Iterator[BuilderT]:
        for action_row in self.build():
            yield action_row

    def __contains__(self, value: object) -> bool:
        return value in self.build()

    def __len__(self) -> int:
        return len(self.build())

    def __reversed__(self) -> t.Iterator[BuilderT]:
        return self.build().__reversed__()

    @property
    def children(self) -> t.Sequence[ItemT]:
        """A list of all items attached to the item handler."""
        return self._children

    @property
    def timeout(self) -> float | None:
        """The amount of time the item handler is allowed to idle for, in seconds. Must be None for persistent views."""
        return self._timeout

    @property
    def client(self) -> Client:
        """The client that started this handler."""
        if not self._client:
            raise RuntimeError(
                f"'{type(self).__name__}' was not started, '{type(self).__name__}.client' is unavailable."
            )

        return self._client

    @property
    def last_context(self) -> ContextT | None:
        """The last context that was received by the item handler."""
        return self._last_context

    @property
    @abc.abstractmethod
    def _builder(self) -> type[BuilderT]:
        ...

    def add_item(self, item: ItemT) -> te.Self:
        """Adds a new item to the item handler.

        Parameters
        ----------
        item : Item[Any]
            The item to be added.

        Raises
        ------
        ValueError
            ItemHandler already has 25 components attached.
        TypeError
            Parameter item is not an instance of Item.
        ItemAlreadyAttachedError
            The item is already attached to this item handler.
        ItemAlreadyAttachedError
            The item is already attached to another item handler.

        Returns
        -------
        ItemHandler
            The item handler the item was added to.
        """
        if len(self.children) > 25:
            raise HandlerFullError("Item Handler cannot have more than 25 components attached.")

        if not isinstance(item, Item):
            raise TypeError(f"Expected Item not {type(item).__name__} for parameter item.")

        if item in self.children:
            raise ItemAlreadyAttachedError(f"Item {type(item).__name__} is already attached to this item handler.")

        if item._handler is not None:
            raise ItemAlreadyAttachedError(
                f"Item {type(item).__name__} is already attached to another item handler: {type(item._handler).__name__}."
            )

        self._arranger.add_item(item)

        item._handler = self
        self._children.append(item)

        return self

    def remove_item(self, item: ItemT) -> te.Self:
        """Removes the specified item from the item handler.

        Parameters
        ----------
        item : Item[Any]
            The item to be removed.

        Returns
        -------
        ItemHandler
            The item handler the item was removed from.
        """
        try:
            self._children.remove(item)
        except ValueError:
            pass
        else:
            self._arranger.remove_item(item)
            item._handler = None

        return self

    def clear_items(self) -> te.Self:
        """Removes all items from this item handler.

        Returns
        -------
        ItemHandler
            The item handler items were cleared from.
        """
        for item in self.children:
            item._handler = None
            item._rendered_row = None

        self._children.clear()
        self._arranger.clear()

        return self

    def get_item_by(self, predicate: t.Callable[[ItemT], bool]) -> ItemT | None:
        """Get the first item that matches the given predicate.

        Parameters
        ----------
        predicate : Callable[[Item[Any]], bool]
            A predicate to match the item.

        Returns
        -------
        Optional[Item[Any]]
            The item that matched the predicate or None.
        """
        for item in self.children:
            if predicate(item):
                return item
        return None

    def get_item_by_id(self, custom_id: str) -> ItemT | None:
        """Get the first item that matches the given custom ID.

        Parameters
        ----------
        custom_id : str
            The custom_id of the component.

        Returns
        -------
        Optional[Item[Any]]
            The item that matched the custom ID or None.
        """
        return self.get_item_by(lambda item: item.custom_id == custom_id)

    def build(self) -> t.Sequence[BuilderT]:
        """Creates the action rows the item handler represents.

        Returns
        -------
        List[hikari.impl.MessageActionRowBuilder]
            A list of action rows containing all items attached to this item handler,
            converted to hikari component objects. If the item handler has no items attached,
            this returns an empty list.
        """
        if not self.children:
            return []

        self._children.sort(key=lambda i: i._rendered_row if i._rendered_row is not None else sys.maxsize)

        action_rows: list[BuilderT] = []

        for _, items in itertools.groupby(self.children, lambda i: i._rendered_row):
            s_items = sorted(items, key=lambda i: i.position if i.position is not None else sys.maxsize)
            action_row = self._builder()
            for item in s_items:
                item._build(action_row)
            action_rows.append(action_row)
        return action_rows

    async def on_timeout(self) -> None:
        """Called when the item handler times out. Override for custom timeout logic."""
        pass

    def stop(self) -> None:
        """Stop listening for interactions."""
        if not self._client:
            return

        self._stopped.set()

        if self._timeout_task:
            self._timeout_task.cancel()

        self._client._remove_handler(self)

    @abc.abstractmethod
    async def _invoke(self, interaction: InteractionT) -> asyncio.Future[RespBuilderT] | None:
        """Process incoming interactions."""

    def _reset_timeout(self) -> None:
        """Reset the timeout counter."""
        if self.timeout is not None and self._timeout_task:
            self._timeout_task.cancel()
            self._timeout_task = self._create_task(self._handle_timeout())

    async def _handle_timeout(self) -> None:
        """Handle the timing out of the item handler."""
        if not self.timeout:
            return

        await asyncio.sleep(self.timeout)
        try:
            await self.on_timeout()
        except Exception as error:
            if on_error := getattr(self, "on_error", None):
                await on_error(error)

        self.stop()

    def _create_task(self, coro: t.Awaitable[t.Any], *, name: str | None = None) -> asyncio.Task[t.Any]:
        """Run tasks inside the item handler internally while keeping a reference to the provided task."""
        task: asyncio.Task[t.Any] = asyncio.create_task(coro, name=name)  # type: ignore
        self._running_tasks.append(task)
        task.add_done_callback(lambda t: self._running_tasks.remove(t))
        return task

    async def wait(self, timeout: float | None = None) -> None:
        """Wait until the item handler has stopped receiving interactions.

        Parameters
        ----------
        timeout : Optional[float]
            The amount of time to wait, in seconds
        """
        await asyncio.wait_for(self._stopped.wait(), timeout=timeout)


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
