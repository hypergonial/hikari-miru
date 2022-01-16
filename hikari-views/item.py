from abc import abstractmethod
from typing import Optional

import hikari

from .view import View


class Item:
    """
    A base class for view components.
    """

    def __init__(self):
        self._view: Optional[View] = None
        self._row: Optional[int] = None
        self._width: int = 1
        self._rendered_row: Optional[int] = None  # Where it actually ends up when rendered by Discord
        self.custom_id: Optional[str] = None

    @property
    def row(self) -> int:
        return self._row

    @row.setter
    def row(self, value: int):
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
    def view(self) -> View:
        return self._view

    @property
    @abstractmethod
    def type(self) -> hikari.ComponentType:
        """
        Return the component's underlying component type.
        """
        ...

    @abstractmethod
    async def _build(self, action_row: hikari.api.ActionRowBuilder) -> None:
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
        Called on an item to refresh it's internal data.
        """
        pass
