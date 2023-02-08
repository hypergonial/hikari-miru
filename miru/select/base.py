from __future__ import annotations

import abc
import typing as t

import hikari

from ..abc.item import ViewItem

if t.TYPE_CHECKING:
    from ..view import View

    ViewT = t.TypeVar("ViewT", bound="View")

__all__ = ("SelectBase",)


class SelectBase(ViewItem, abc.ABC):
    """A view component representing some type of select menu. All types of selects derive from this class.

    Parameters
    ----------
    custom_id : Optional[str], optional
        The custom identifier of the select menu, by default None
    placeholder : Optional[str], optional
        Placeholder text displayed on the select menu, by default None
    disabled : bool, optional
        A boolean determining if the select menu should be disabled or not, by default False
    row : Optional[int], optional
        The row the select menu should be in, leave as None for auto-placement.

    Raises
    ------
    ValueError
        Exceeded the maximum of 25 select menu options possible.
    """

    def __init__(
        self,
        *,
        custom_id: t.Optional[str] = None,
        placeholder: t.Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: t.Optional[int] = None,
    ) -> None:
        super().__init__(custom_id=custom_id, row=row, disabled=disabled)
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values

    @property
    def placeholder(self) -> t.Optional[str]:
        """
        The placeholder text that appears before the select menu is clicked.
        """
        return self._placeholder

    @placeholder.setter
    def placeholder(self, value: t.Optional[str]) -> None:
        if value and not isinstance(value, str):
            raise TypeError("Expected type str for property placeholder.")
        if value is not None and len(value) > 150:
            raise ValueError(f"Parameter 'placeholder' must be 150 or fewer in length. (Found length {len(value)})")
        self._placeholder = str(value) if value else None

    @property
    def min_values(self) -> int:
        """
        The minimum amount of options a user has to select.
        """
        return self._min_values

    @min_values.setter
    def min_values(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("Expected type 'int' for property 'min_values'.")
        self._min_values = value

    @property
    def max_values(self) -> int:
        """
        The maximum amount of options a user is allowed to select.
        """
        return self._max_values

    @max_values.setter
    def max_values(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("Expected type 'int' for property 'max_values'.")
        self._max_values = value

    @classmethod
    @abc.abstractmethod
    def _from_component(cls, component: hikari.PartialComponent, row: t.Optional[int] = None) -> SelectBase:
        """
        Called internally to convert a component to a select menu.
        """

    @abc.abstractmethod
    def _build(self, action_row: hikari.api.MessageActionRowBuilder) -> None:
        """
        Called internally to build and append to an action row
        """

    @property
    def width(self) -> int:
        return 5
