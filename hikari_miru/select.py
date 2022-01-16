import inspect
import os
from typing import Callable
from typing import Coroutine
from typing import Optional
from typing import Sequence
from typing import Union

import hikari

from .item import Item


class SelectOption:
    """
    A more lenient way to instantiate select options.
    """

    def __init__(
        self,
        label: str,
        value: Optional[str] = None,
        description: Optional[str] = None,
        emoji: Optional[Union[str, hikari.Emoji]] = None,
        is_default: bool = False,
    ) -> None:
        self.label: str = label
        self.value: str = value if value else label
        self.description: Optional[str] = description
        if isinstance(emoji, str):
            emoji = hikari.Emoji.parse(emoji)
        self.emoji: Optional[hikari.Emoji] = emoji
        self.is_default: bool = is_default

    def _convert(self) -> hikari.SelectMenuOption:
        return hikari.SelectMenuOption(
            label=self.label,
            value=self.value,
            description=self.description,
            emoji=self.emoji,
            is_default=self.is_default,
        )


class Select(Item):
    """
    A view component representing a select menu.
    """

    def __init__(
        self,
        *,
        options: Sequence[Union[hikari.SelectMenuOption, SelectOption]],
        custom_id: Optional[str] = None,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: Optional[int] = None,
    ) -> None:
        super().__init__()
        self._values: Sequence[str] = []
        self._persistent: bool = True if custom_id else False
        self.custom_id: str = os.urandom(16).hex() if not custom_id else custom_id
        self.disabled: bool = disabled
        self.options: Sequence[Union[hikari.SelectMenuOption, SelectOption]] = options
        self.min_values: int = min_values
        self.max_values: int = max_values
        self.placeholder: Optional[str] = placeholder
        self.row: Optional[int] = row if row else None

    @property
    def type(self) -> hikari.ComponentType:
        return hikari.ComponentType.SELECT_MENU

    def _build(self, action_row: hikari.api.ActionRowBuilder) -> None:
        """
        Called internally to build and append to an action row
        """
        select = action_row.add_select_menu(self.custom_id)
        if self.placeholder:
            select.set_placeholder(self.placeholder)
        select.set_min_values(self.min_values)
        select.set_max_values(self.max_values)
        select.set_is_disabled(self.disabled)

        for option in self.options:
            if isinstance(option, SelectOption):
                option = option._convert()
            _option = select.add_option(option.label, option.value)
            if option.description:
                _option.set_description(option.description)
            if option.emoji:
                _option.set_emoji(option.emoji)
            _option.add_to_menu()

        select.add_to_container()

    @property
    def values(self) -> Sequence[str]:
        return self._values

    @property
    def width(self) -> int:
        return 5

    async def _refresh(self, interaction: hikari.ComponentInteraction) -> None:
        self._values = interaction.values


def select(
    *,
    options: Sequence[Union[hikari.SelectMenuOption, SelectOption]],
    custom_id: Optional[str] = None,
    placeholder: Optional[str] = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: Optional[int] = None,
) -> Callable[[Callable], Callable]:
    """
    A decorator to transform a function into a Discord UI SelectMenu's callback. This must be inside a subclass of View.
    """

    def decorator(func: Callable) -> Callable:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("select must decorate coroutine function.")

        func._view_item_type = Select
        func._view_item_data = {
            "options": options,
            "custom_id": custom_id,
            "placeholder": placeholder,
            "min_values": min_values,
            "max_values": max_values,
            "disabled": disabled,
            "row": row,
        }
        return func

    return decorator
