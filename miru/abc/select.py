from __future__ import annotations

import abc
import typing as t

import hikari

from miru.abc.item import InteractiveViewItem

if t.TYPE_CHECKING:
    import typing_extensions as te

    from miru.context.view import AutodeferOptions
    from miru.view import View

    ViewT = t.TypeVar("ViewT", bound="View")

__all__ = ("SelectBase",)


class SelectBase(InteractiveViewItem, abc.ABC):
    """A view component representing some type of select menu. All types of selects derive from this class.

    Parameters
    ----------
    custom_id : str | None
        The custom identifier of the select menu
    placeholder : str | None
        Placeholder text displayed on the select menu
    disabled : bool
        A boolean determining if the select menu should be disabled or not
    row : int | None
        The row the select menu should be in, leave as None for auto-placement.
    autodefer : bool | AutodeferOptions | hikari.UndefinedType
        The autodefer options for the select menu. If left `UNDEFINED`, the view's autodefer options will be used.

    Raises
    ------
    ValueError
        Exceeded the maximum of 25 select menu options possible.
    """

    def __init__(
        self,
        *,
        custom_id: str | None = None,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: int | None = None,
        autodefer: bool | AutodeferOptions | hikari.UndefinedType = hikari.UNDEFINED,
    ) -> None:
        super().__init__(custom_id=custom_id, row=row, position=0, width=5, disabled=disabled, autodefer=autodefer)
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values

    @property
    def placeholder(self) -> str | None:
        """The placeholder text that appears before the select menu is clicked."""
        return self._placeholder

    @placeholder.setter
    def placeholder(self, value: str | None) -> None:
        if value is not None and len(value) > 150:
            raise ValueError(f"Parameter 'placeholder' must be 150 or fewer in length. (Found length {len(value)})")
        self._placeholder = str(value) if value else None

    @property
    def min_values(self) -> int:
        """The minimum amount of options a user has to select."""
        return self._min_values

    @min_values.setter
    def min_values(self, value: int) -> None:
        self._min_values = value

    @property
    def max_values(self) -> int:
        """The maximum amount of options a user is allowed to select."""
        return self._max_values

    @max_values.setter
    def max_values(self, value: int) -> None:
        self._max_values = value

    @classmethod
    @abc.abstractmethod
    def _from_component(cls, component: hikari.PartialComponent, row: int | None = None) -> te.Self:
        """Called internally to convert a component to a select menu."""

    @abc.abstractmethod
    def _build(self, action_row: hikari.api.MessageActionRowBuilder) -> None:
        """Called internally to build and append to an action row."""


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
