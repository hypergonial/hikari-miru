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

import abc
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Optional
from typing import TypeVar

import hikari

if TYPE_CHECKING:
    from .view import View

V = TypeVar("V", bound="View")


class Item(abc.ABC):
    """
    A base class for view components.
    """

    def __init__(self) -> None:
        self._view: Optional[V] = None
        self._row: Optional[int] = None
        self._width: int = 1
        self._rendered_row: Optional[int] = None  # Where it actually ends up when rendered by Discord
        self.custom_id: Optional[str] = None
        self._persistent: bool = False

    @property
    def row(self) -> Optional[int]:
        return self._row

    @row.setter
    def row(self, value: Optional[int]) -> None:
        if value is None:
            self._row = None
        elif 5 > value >= 0:
            self._row = value
        else:
            raise ValueError("Row must be between 0 and 5.")

    @property
    def width(self) -> int:
        return self._width

    @property
    def view(self) -> Optional[V]:
        return self._view

    @property
    @abstractmethod
    def type(self) -> hikari.ComponentType:
        """
        Return the component's underlying component type.
        """
        ...

    @abstractmethod
    def _build(self, action_row: hikari.api.ActionRowBuilder) -> None:
        """
        Called internally to build and append the item to an action row
        """
        ...

    async def callback(self, interaction: hikari.ComponentInteraction) -> None:
        """
        The component's callback, gets called when the component receives an interaction.
        """
        pass

    async def _refresh(self, interaction: hikari.ComponentInteraction) -> None:
        """
        Called on an item to refresh its internal data.
        """
        pass
