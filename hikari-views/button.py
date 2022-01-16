from ui.item import Item
import hikari
import os
from typing import Union, Optional

class Button(Item):
    '''
    A view component representing a button.
    '''
    def __init__(self, *, style:hikari.ButtonStyle = hikari.ButtonStyle.PRIMARY, label:str=None, disabled:bool=False, custom_id:str=None, url:str=None, emoji:Union[hikari.Emoji, str], row:Optional[int]=None):
        super().__init__()

        if custom_id and url:
            raise TypeError("Cannot provide both url and custom_id")
        
        if url is None and custom_id is None:
            custom_id = os.urandom(16).hex()
        
        if url is not None:
            style = hikari.ButtonStyle.LINK

        self.style: hikari.ButtonStyle = style
        self.label: str = label
        self.disabled: bool = disabled
        self.emoji: Union[str, hikari.Emoji] = emoji
        self._persistent: bool = True if custom_id else False
        self.custom_id: str = custom_id
        self.row = int(row) if row else None
    
    @property
    def type(self) -> hikari.ComponentType:
        return hikari.ComponentType.BUTTON

    
    def _build(self, action_row: hikari.api.ActionRowBuilder) -> None:
        '''
        Called internally to build and append the button to an action row
        '''

        button = action_row.add_button(self.style, self.custom_id)
        button.set_label(self.label)
        if self.emoji:
            button.set_emoji(self.emoji)
        button.set_is_disabled(self.disabled)
        button.add_to_container()

        