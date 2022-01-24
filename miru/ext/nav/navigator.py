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

from typing import List
from typing import Optional
from typing import TypeVar
from typing import Union

import hikari
from hikari.undefined import UNDEFINED

from ... import Interaction
from ... import Item
from ... import View
from .buttons import FirstButton
from .buttons import IndicatorButton
from .buttons import LastButton
from .buttons import NavButton
from .buttons import NavigatorViewT
from .buttons import NextButton
from .buttons import PrevButton


class NavigatorView(View):
    def __init__(
        self,
        app: hikari.GatewayBot,
        *,
        pages: List[Union[str, hikari.Embed]],
        buttons: Optional[List[NavButton[NavigatorViewT]]] = None,
        timeout: Optional[float] = 120.0,
        autodefer: bool = True,
    ) -> None:
        self._pages: List[Union[str, hikari.Embed]] = pages
        self._current_page: int = 0
        super().__init__(app, timeout=timeout, autodefer=autodefer)

        if buttons is not None:
            for button in buttons:
                self.add_item(button)
        else:
            default_buttons: List[NavButton[NavigatorViewT]] = self.get_default_buttons()
            for button in default_buttons:
                self.add_item(button)

        for page in pages:
            if not isinstance(page, (str, hikari.Embed)):
                raise TypeError("Expected type List[str, hikari.Embed] for parameter pages.")

    @property
    def pages(self) -> List[Union[str, hikari.Embed]]:
        """
        The pages the navigator is iterating through.
        """
        return self._pages

    @property
    def current_page(self) -> int:
        """
        The current page of the navigator, zero-indexed integer.
        """
        return self._current_page

    @current_page.setter
    def current_page(self, value: int) -> None:
        if isinstance(value, int):
            # Ensure this value is always correct
            if value >= 0 and value <= len(self.pages) - 1:
                self._current_page = value
            elif value > len(self.pages) - 1:
                self._current_page = len(self.pages) - 1
            else:
                self._current_page = 0
        else:
            raise TypeError("Expected type int for property current_page.")


    async def on_timeout(self) -> None:
        if self.message is not None:
            for button in self.children:
                button.disabled = True
            await self.message.edit(components=self.build())


    def get_default_buttons(self) -> List[NavButton[NavigatorViewT]]:
        """
        Returns the default set of buttons.
        """
        return [FirstButton(), PrevButton(), IndicatorButton(), NextButton(), LastButton()]


    def add_item(self, item: Item[NavigatorViewT]) -> None:
        """
        Adds a new item to the view. Item must be of type NavButton.
        """
        if not isinstance(item, NavButton):
            raise TypeError("Expected type NavButton for parameter item.")

        return super().add_item(item)


    async def send_page(self, page_index: int, interaction: Interaction) -> None:
        """
        Send a page, editing the original message.
        """
        page = self.pages[self.current_page]

        for button in self.children:
            if isinstance(button, NavButton):
                await button.before_page_change()

        if isinstance(page, str):
            await interaction.edit_message(page, embeds=[], components=self.build())
        elif isinstance(page, hikari.Embed):
            await interaction.edit_message(content="", embed=page, components=self.build())
        else:
            raise TypeError("Expected type str or hikari.Embed to send as page.")


    def start(self, message: hikari.Message) -> None:
        """
        Start up the navigator listener. This should not be called directly, use send() instead.
        """

        super().start(message)


    async def send(
        self,
        *,
        channel_id: Optional[int] = None,
        interaction: Optional[Union[hikari.ComponentInteraction, hikari.CommandInteraction]] = None,
    ) -> None:
        """
        Start up the navigator, send the first page, and start listening for interactions.
        """
        if channel_id and interaction:
            raise ValueError("Cannot provide both channel_id and interaction.")
        elif channel_id is None and interaction is None:
            raise ValueError("Must provide either channel_id or interaction.")

        if channel_id and not isinstance(channel_id, int):
            raise TypeError("Expected type int for parameter channel_id.")
        if interaction and not isinstance(interaction, (hikari.CommandInteraction, hikari.ComponentInteraction)):
            raise TypeError(
                "Expected types hikari.CommandInteraction or hikari.ComponentInteraction for parameter interaction."
            )

        content: hikari.UndefinedOr[str] = self.pages[0] if isinstance(self.pages[0], str) else hikari.UNDEFINED
        embed: hikari.UndefinedOr[hikari.Embed] = (
            self.pages[0] if isinstance(self.pages[0], hikari.Embed) else hikari.UNDEFINED
        )

        for button in self.children:
            if isinstance(button, NavButton):
                await button.before_page_change()

        if channel_id:
            message: hikari.Message = await self.app.rest.create_message(
                channel_id, content, embed=embed, components=self.build()
            )
        elif interaction:
            await interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_CREATE, content, embed=embed, components=self.build()
            )
            message = await interaction.fetch_initial_response()

        self.start(message)
