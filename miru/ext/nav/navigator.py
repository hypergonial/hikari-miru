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

from typing import Any
from typing import List
from typing import Literal
from typing import Mapping
from typing import Optional
from typing import Union

import hikari

from miru.interaction import Interaction
from miru.item import Item
from miru.view import View

from .buttons import FirstButton
from .buttons import IndicatorButton
from .buttons import LastButton
from .buttons import NavButton
from .buttons import NavigatorViewT
from .buttons import NextButton
from .buttons import PrevButton

__all__ = ["NavigatorView"]


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
            default_buttons = self.get_default_buttons()
            for default_button in default_buttons:
                self.add_item(default_button)

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
        if not isinstance(value, int):
            raise TypeError("Expected type int for property current_page.")

        # Ensure this value is always correct
        self._current_page = max(0, min(value, len(self.pages)))

    async def on_timeout(self) -> None:
        if self.message is None:
            return

        for button in self.children:
            button.disabled = True

        await self.message.edit(components=self.build())

    def get_default_buttons(self: NavigatorViewT) -> List[NavButton[NavigatorViewT]]:
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

    def _get_page_payload(self, page: Union[str, hikari.Embed]) -> Mapping[str, Any]:
        if isinstance(page, str):
            return dict(content=page, embeds=[], components=self.build())
        elif isinstance(page, hikari.Embed):
            return dict(content="", embed=page, components=self.build())
        else:
            raise TypeError("Expected type str or hikari.Embed to send as page.")

    async def send_page(self, interaction: Interaction, page_index: Optional[int] = None) -> None:
        """
        Send a page, editing the original message.
        """
        if page_index:
            self.current_page = page_index

        page = self.pages[self.current_page]

        for button in self.children:
            if isinstance(button, NavButton):
                await button.before_page_change()

        payload = self._get_page_payload(page)
        await interaction.edit_message(**payload)

    def start(self, message: hikari.Message) -> None:
        """
        Start up the navigator listener. This should not be called directly, use send() instead.
        """
        super().start(message)

    async def send(
        self,
        channel_or_interaction: Union[hikari.SnowflakeishOr[hikari.PartialChannel], hikari.MessageResponseMixin[Any]],
    ) -> None:
        """
        Start up the navigator, send the first page, and start listening for interactions.
        """
        self.current_page = 0

        for button in self.children:
            if isinstance(button, NavButton):
                await button.before_page_change()

        payload = self._get_page_payload(self.pages[0])

        if isinstance(channel_or_interaction, (int, hikari.PartialChannel)):
            channel = hikari.Snowflake(channel_or_interaction)
            message = await self.app.rest.create_message(channel, **payload)
        else:
            await channel_or_interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_CREATE,
                **payload,
            )
            message = await channel_or_interaction.fetch_initial_response()

        self.start(message)
