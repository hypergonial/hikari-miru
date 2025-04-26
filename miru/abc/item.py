from __future__ import annotations

import abc
import os
import typing as t
from abc import abstractmethod

import hikari

from miru.context.view import AutodeferOptions
from miru.exceptions import ItemAlreadyAttachedError
from miru.internal.types import BuilderT, ContextT, HandlerT, ViewItemT, ViewT

if t.TYPE_CHECKING:
    import typing_extensions as te

    from miru.context import ModalContext, ViewContext  # noqa: F401
    from miru.modal import Modal
    from miru.view import View


__all__ = ("DecoratedItem", "InteractiveViewItem", "Item", "ModalItem", "ViewItem")


class Item(abc.ABC, t.Generic[BuilderT, ContextT, HandlerT]):
    """An abstract base class for all components. Cannot be directly instantiated."""

    def __init__(
        self, *, custom_id: str | None = None, row: int | None = None, position: int | None = None, width: int = 1
    ) -> None:
        self._rendered_row: int | None = None
        """The row the item was placed at when rendered. None if this item was not sent to a message yet."""

        self.row = row
        """The row the item should occupy. Leave as None for automatic placement."""

        self._width: int = width
        """The relative width of the item. 5 takes up a whole row."""

        self.position = position
        """The position of the item within the row it occupies. Leave as None for automatic placement."""

        self.custom_id = custom_id
        """The Discord custom_id of the item."""

        self._is_persistent: bool = bool(custom_id)
        """If True, the custom_id was provided by the user, and not randomly generated."""

        self._handler: HandlerT | None = None
        """The handler the item was added to, if any."""

    @property
    def position(self) -> int | None:
        """The position of the item within the row it occupies."""
        return self._position

    @position.setter
    def position(self, value: int | None) -> None:
        if value is None or 4 >= value >= 0:
            self._position = value
        else:
            raise ValueError(f"Position of item {type(self).__name__} must be between 0 and 4.")

    @property
    def row(self) -> int | None:
        """The row the item should occupy. Leave as None for automatic placement."""
        return self._row

    @row.setter
    def row(self, value: int | None) -> None:
        if self._rendered_row is not None:
            raise ItemAlreadyAttachedError("Item is already attached to an item handler, row cannot be changed.")

        if value is None or 5 > value >= 0:
            self._row = value
        else:
            raise ValueError("Row must be between 0 and 4.")

    @property
    def width(self) -> int:
        """The item's width taken up in a Discord UI action row."""
        return self._width

    @property
    def custom_id(self) -> str:
        """The item's custom identifier. This will be used to track the item through interactions and
        is required for persistent views.
        """
        return self._custom_id

    @custom_id.setter
    def custom_id(self, value: str | None) -> None:
        if value and len(value) > 100:
            raise ValueError("custom_id has a max length of 100.")

        self._is_persistent = bool(value)
        self._custom_id = value or os.urandom(16).hex()

    @abc.abstractmethod
    def _build(self, action_row: t.Any) -> None: ...

    @property
    @abstractmethod
    def type(self) -> hikari.ComponentType:
        """The component's underlying component type."""
        ...

    async def _refresh_state(self, context: ContextT) -> None:
        """Called on an item to refresh it's internal state."""
        pass


class ViewItem(Item["hikari.impl.MessageActionRowBuilder", "ViewContext", "View"], abc.ABC):
    """An abstract base class for view components. Cannot be directly instantiated."""

    def __init__(
        self,
        *,
        custom_id: str | None = None,
        row: int | None = None,
        position: int | None = None,
        width: int = 1,
        disabled: bool = False,
    ) -> None:
        super().__init__(custom_id=custom_id, row=row, position=position, width=width)
        self._handler: View | None = None
        self._disabled: bool = disabled

    @property
    def view(self) -> View:
        """The view this item is attached to."""
        if not self._handler:
            raise AttributeError(f"{type(self).__name__} hasn't been attached to a view yet.")

        return self._handler

    @property
    def disabled(self) -> bool:
        """Indicates whether the item is disabled or not."""
        return self._disabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        self._disabled = value

    @abstractmethod
    def _build(self, action_row: hikari.api.MessageActionRowBuilder) -> None:
        """Called internally to build and append the item to an action row."""
        ...

    @classmethod
    @abstractmethod
    def _from_component(cls, component: hikari.PartialComponent, row: int | None = None) -> te.Self:
        """Converts the passed hikari component into a miru ViewItem."""
        ...


class InteractiveViewItem(ViewItem, abc.ABC):
    """An abstract base class for view components that have callbacks.
    Cannot be directly instantiated.
    """

    def __init__(
        self,
        *,
        custom_id: str | None = None,
        row: int | None = None,
        position: int | None = None,
        width: int = 1,
        disabled: bool = False,
        autodefer: bool | AutodeferOptions | hikari.UndefinedType = hikari.UNDEFINED,
    ) -> None:
        super().__init__(custom_id=custom_id, row=row, position=position, width=width, disabled=disabled)
        self._autodefer = AutodeferOptions.parse(autodefer) if autodefer is not hikari.UNDEFINED else autodefer

    @property
    def autodefer(self) -> AutodeferOptions | hikari.UndefinedType:
        """Indicates whether the item should be deferred automatically.
        If left as `UNDEFINED`, the view's autodefer option will be used.
        """
        return self._autodefer

    @classmethod
    @abstractmethod
    def _from_component(cls, component: hikari.PartialComponent, row: int | None = None) -> te.Self:
        """Converts the passed hikari component into a miru ViewItem."""
        ...

    async def callback(self, context: ViewContext, /) -> None:
        """The component's callback, gets called when the component receives an interaction.

        Parameters
        ----------
        context : ViewContextT
            The context, proxying the incoming interaction.
        """
        pass


class ModalItem(Item["hikari.impl.ModalActionRowBuilder", "ModalContext", "Modal"], abc.ABC):
    """An abstract base class for modal components. Cannot be directly instantiated."""

    def __init__(
        self,
        *,
        custom_id: str | None = None,
        row: int | None = None,
        position: int | None = None,
        width: int = 1,
        required: bool = False,
    ) -> None:
        super().__init__(custom_id=custom_id, row=row, position=position, width=width)
        self._handler: Modal | None = None
        self._required: bool = required

    @property
    def modal(self) -> Modal | None:
        """The modal this item is attached to."""
        if not self._handler:
            raise AttributeError(f"{type(self).__name__} hasn't been attached to a modal yet.")

        return self._handler

    @property
    def required(self) -> bool:
        """Indicates whether the item is required or not."""
        return self._required

    @required.setter
    def required(self, value: bool) -> None:
        self._required = value

    @abstractmethod
    def _build(self, action_row: hikari.api.ModalActionRowBuilder) -> None:
        """Called internally to build and append the item to an action row."""
        ...


class DecoratedItem(t.Generic[ViewT, ViewItemT]):
    """A partial item made using a decorator."""

    __slots__ = ("callback", "item_type", "kwargs")

    def __init__(
        self,
        item_type: type[ViewItemT],
        callback: t.Callable[[ViewT, ViewContext, ViewItemT], t.Coroutine[t.Any, t.Any, None]],
        **kwargs: t.Any,
    ) -> None:
        self.item_type = item_type
        self.callback = callback
        self.kwargs = kwargs

    def build(self, view: ViewT) -> ViewItemT:
        """Convert a DecoratedItem into a ViewItem.

        Parameters
        ----------
        view : ViewT
            The view this decorated item is attached to.

        Returns
        -------
        ViewItem[ViewT]
            The converted item.
        """
        item = self.item_type(**self.kwargs)

        async def wrapped_callback(ctx: ViewContext) -> None:
            await self.callback(view, ctx, item)

        item.callback = wrapped_callback

        return item

    @property
    def name(self) -> str:
        """The name of the callback this item decorates.

        Returns
        -------
        str
            The name of the callback.
        """
        return self.callback.__name__

    def __call__(self, view: ViewT, context: ViewContext, item: ViewItemT, /) -> t.Awaitable[None]:
        """Call the callback this DecoratedItem wraps."""
        return self.callback(view, context, item)


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
