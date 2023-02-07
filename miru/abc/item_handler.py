from __future__ import annotations

import abc
import asyncio
import datetime
import itertools
import sys
import typing as t
from collections.abc import Sequence

import hikari

from ..exceptions import BootstrapFailureError
from ..exceptions import HandlerFullError
from ..exceptions import ItemAlreadyAttachedError
from ..exceptions import RowFullError
from ..traits import MiruAware
from .item import Item

if t.TYPE_CHECKING:
    from ..context import Context
    from ..events import EventHandler

__all__ = ("ItemHandler",)


BuilderT = t.TypeVar("BuilderT", bound=hikari.api.ComponentBuilder)


class _Weights:
    """
    Calculate the position of an item based on it's width, and keep track of item positions
    """

    __slots__ = ("_weights",)

    def __init__(self) -> None:
        self._weights = [0, 0, 0, 0, 0]

    def add_item(self, item: Item[BuilderT]) -> None:
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

    def remove_item(self, item: Item[BuilderT]) -> None:
        if item._rendered_row is not None:
            self._weights[item._rendered_row] -= item.width
            item._rendered_row = None

    def clear(self) -> None:
        self._weights = [0, 0, 0, 0, 0]


# Add Sequence[hikari.api.MessageActionRowBuilder] here when dropping 3.8 support
class ItemHandler(Sequence, abc.ABC, t.Generic[BuilderT]):  # type: ignore[type-arg]
    """Abstract base class all item-handlers (e.g. views, modals) inherit from.

    Parameters
    ----------
    timeout : Optional[float], optional
        The duration after which the item handler times out, in seconds, by default 120.0
    autodefer : bool
        If unhandled interactions should be automatically deferred or not, by default True

    Raises
    ------
    HandlerFullError
        Raised if the item handler has more than 25 components attached.
    BootstrapFailureError
        Raised if miru.install() was never called before instantiation.
    """

    _app: t.ClassVar[t.Optional[MiruAware]] = None
    _events: t.ClassVar[t.Optional[EventHandler]] = None

    def __init__(self, *, timeout: t.Optional[t.Union[float, int, datetime.timedelta]] = 120.0) -> None:
        if isinstance(timeout, datetime.timedelta):
            timeout = timeout.total_seconds()

        self._timeout: t.Optional[float] = float(timeout) if timeout else None
        self._children: t.List[Item[BuilderT]] = []

        self._weights: _Weights = _Weights()
        self._stopped: asyncio.Event = asyncio.Event()
        self._timeout_task: t.Optional[asyncio.Task[None]] = None
        self._running_tasks: t.MutableSequence[asyncio.Task[t.Any]] = []
        self._last_context: t.Optional[Context[t.Any]] = None

        if len(self.children) > 25:
            raise HandlerFullError(f"{type(self).__name__} cannot have more than 25 components attached.")

        if self.app is None or self._events is None:
            raise BootstrapFailureError(f"miru.install() was not called before instantiation of {type(self).__name__}.")

    @t.overload
    def __getitem__(self, value: int) -> BuilderT:
        ...

    @t.overload
    def __getitem__(self, value: slice) -> t.Sequence[BuilderT]:
        ...

    def __getitem__(self, value: t.Union[slice, int]) -> t.Union[BuilderT, t.Sequence[BuilderT]]:
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
    def children(self) -> t.Sequence[Item[BuilderT]]:
        """
        A list of all items attached to the item handler.
        """
        return self._children

    @property
    def timeout(self) -> t.Optional[float]:
        """
        The amount of time the item handler is allowed to idle for, in seconds. Must be None for persistent views.
        """
        return self._timeout

    @property
    def app(self) -> MiruAware:
        """
        The application that loaded the miru extension.
        """
        if not self._app:
            raise AttributeError(f"miru was not loaded, {type(self).__name__} has no attribute app.")

        return self._app

    @property
    def bot(self) -> MiruAware:
        """
        The application that loaded the miru extension.
        """
        return self.app

    @property
    def last_context(self) -> t.Optional[Context[t.Any]]:
        """
        The last context that was received by the item handler.
        """
        return self._last_context

    @property
    @abc.abstractmethod
    def _builder(self) -> type[BuilderT]:
        ...

    def add_item(self, item: Item[BuilderT]) -> ItemHandler[BuilderT]:
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
        RuntimeError
            The item is already attached to this item handler.
        RuntimeError
            The item is already attached to another item handler.

        Returns
        -------
        ItemHandler
            The item handler the item was added to.
        """

        if len(self.children) > 25:
            raise HandlerFullError("Item Handler cannot have more than 25 components attached.")

        if not isinstance(item, Item):
            raise TypeError(f"Expected Item not {item.__class__.__name__} for parameter item.")

        if item in self.children:
            raise ItemAlreadyAttachedError(f"Item {item.__class__.__name__} is already attached to this item handler.")

        if item._handler is not None:
            raise ItemAlreadyAttachedError(
                f"Item {item.__class__.__name__} is already attached to another item handler: {item._handler.__class__.__name__}."
            )

        self._weights.add_item(item)

        item._handler = self
        self._children.append(item)

        return self

    def remove_item(self, item: Item[BuilderT]) -> ItemHandler[BuilderT]:
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
            self._weights.remove_item(item)
            item._handler = None

        return self

    def clear_items(self) -> ItemHandler[BuilderT]:
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
        self._weights.clear()

        return self

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

        action_rows = []

        for _, items in itertools.groupby(self.children, lambda i: i._rendered_row):
            action_row = self._builder()
            for item in items:
                item._build(action_row)
            action_rows.append(action_row)
        return action_rows

    async def on_timeout(self) -> None:
        """
        Called when the item handler times out. Override for custom timeout logic.
        """
        pass

    def stop(self) -> None:
        """
        Stop listening for interactions.
        """
        self._stopped.set()

        if self._timeout_task:
            self._timeout_task.cancel()

        if not self._events:
            return

        self._events.remove_handler(self)

    @abc.abstractmethod
    async def _process_interactions(self, event: hikari.InteractionCreateEvent) -> None:
        """
        Process incoming interactions.
        """

    def _reset_timeout(self) -> None:
        """
        Reset the timeout counter.
        """
        if self.timeout is not None and self._timeout_task:
            self._timeout_task.cancel()
            self._timeout_task = self._create_task(self._handle_timeout())

    async def _handle_timeout(self) -> None:
        """
        Handle the timing out of the item handler.
        """
        if not self.timeout:
            return

        await asyncio.sleep(self.timeout)
        try:
            await self.on_timeout()
        except Exception as error:
            if on_error := getattr(self, "on_error", None):
                await on_error(error)

        self.stop()

    def _create_task(self, coro: t.Awaitable[t.Any], *, name: t.Optional[str] = None) -> asyncio.Task[t.Any]:
        """
        Run tasks inside the itemhandler internally while keeping a reference to the provided task.
        """
        task = asyncio.create_task(coro, name=name)  # type: ignore
        self._running_tasks.append(task)
        task.add_done_callback(lambda t: self._running_tasks.remove(t))
        return task

    async def wait(self, timeout: t.Optional[float] = None) -> None:
        """Wait until the item handler has stopped receiveing interactions.

        Parameters
        ----------
        timeout : Optional[float], optional
            The amount of time to wait, in seconds, by default None
        """
        await asyncio.wait_for(self._stopped.wait(), timeout=timeout)


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
