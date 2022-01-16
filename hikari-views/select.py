import os
from typing import List, Optional, Union

import hikari

from .item import Item


class SelectOption:
    '''
    A more lenient way to instantiate select options.
    '''
    def __init__(self, label:str, value:Optional[str]=None, description:Optional[str]=None, emoji:Optional[Union[str, hikari.Emoji]]=None, is_default:bool=False) -> None:
        self.label = label
        self.value = value if value else label
        self.description = description
        self.emoji = emoji
        self.is_default = is_default
    
    def _convert(self) -> hikari.SelectMenuOption:
        return hikari.SelectMenuOption(label=self.label, value=self.value, description=self.description, emoji=self.emoji, is_default=self.is_default)


class Select(Item):
    '''
    A view component representing a select menu.
    '''
    def __init__(self, *, options: Union[List[SelectOption], List[hikari.SelectMenuOption]], custom_id: str = None, placeholder:str = None, min_values: int = 1, max_values: int = 1, disabled:bool = False, row: Optional[int] = None) -> None:
        super().__init__()
        self._values: List[str] = []
        self._persistent: bool = True if custom_id else False
        self.custom_id: str = os.urandom(16).hex() if not custom_id else custom_id
        self.disabled:bool = disabled
        self.options: List[hikari.SelectMenuOption] = options
        self.min_values: int = min_values
        self.max_values: int = max_values
        self.placeholder: str = placeholder
        self.row: Optional[int] = row if row else None
    
    @property
    def type(self) -> hikari.ComponentType:
        return hikari.ComponentType.SELECT_MENU

    def _build(self, action_row: hikari.api.ActionRowBuilder) -> None:
        '''
        Called internally to build and append to an action row
        '''
        select = action_row.add_select_menu(self.custom_id)
        select.set_placeholder(self.placeholder)
        select.set_min_values(self.min_values)
        select.set_max_values(self.max_values)
        select.set_is_disabled(self.disabled)

        for option in self.options:
            if isinstance(option, SelectOption):
                option = option._convert()
            _option = select.add_option(option.label, option.value)
            _option.set_description(option.description)
            if option.emoji:
                _option.set_emoji(option.emoji)
            _option.add_to_menu()
        
        select.add_to_container()
    
    @property
    def values(self) -> List[str]:
        return self._values

    @property
    def width(self) -> int:
        return 5

    def _refresh(self, interaction: hikari.ComponentInteraction) -> None:
        self._values = interaction.values
