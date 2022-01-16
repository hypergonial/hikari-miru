import hikari


class Item:
    """
    A base class for view components.
    """

    def __init__(self):
        self._view = None
        self._row = None
        self._width = 1
        self._rendered_row = None  # Where it actually ends up when rendered by Discord
        self.custom_id = None

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
    def view(self) -> int:
        return self._view

    @property
    def type(self) -> hikari.ComponentType:
        raise NotImplementedError

    async def callback(self, interaction: hikari.ComponentInteraction) -> None:
        pass

    async def _build(self, action_row: hikari.api.ActionRowBuilder) -> None:
        """
        Called internally to build and append the item to an action row
        """
        raise NotImplementedError

    async def _refresh(self, interaction: hikari.ComponentInteraction) -> None:
        """
        Called on an item to refresh it's internal data.
        """
        pass
