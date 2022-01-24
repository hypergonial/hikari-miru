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

from typing import TYPE_CHECKING
from typing import Optional
from typing import TypeVar
from typing import Union

import hikari

from ... import Button
from ... import Interaction

if TYPE_CHECKING:
    from .navigator import NavigatorView

NavigatorViewT = TypeVar("NavigatorViewT", bound="NavigatorView")


class NavButton(Button[NavigatorViewT]):
    """
    A baseclass for all navigation buttons. NavigatorViewT requires instances of this class as it's items.
    """

    def __init__(
        self,
        *,
        style: Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.PRIMARY,
        label: Optional[str] = None,
        disabled: bool = False,
        custom_id: Optional[str] = None,
        emoji: Union[hikari.Emoji, str, None] = None,
        row: Optional[int] = None,
    ):
        super().__init__(
            style=style, label=label, disabled=disabled, custom_id=custom_id, url=None, emoji=emoji, row=row
        )

    @property
    def url(self) -> None:
        return None

    @url.setter
    def url(self, value: str) -> None:
        raise AttributeError("NavButton cannot have attribute url.")

    async def before_page_change(self) -> None:
        """
        Called when the navigator is about to transition to the next page. Also called before the first page is sent.
        """
        pass


class NextButton(NavButton[NavigatorViewT]):
    """
    A built-in NavButton to jump to the next page.
    """

    def __init__(
        self,
        *,
        style: Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.PRIMARY,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        emoji: Union[hikari.Emoji, str, None] = chr(9654),
        row: Optional[int] = None,
    ):
        super().__init__(style=style, label=label, custom_id=custom_id, emoji=emoji, row=row)

    async def callback(self, interaction: Interaction) -> None:
        self.view.current_page += 1
        await self.view.send_page(self.view.current_page, interaction)

    async def before_page_change(self) -> None:
        if self.view.current_page == len(self.view.pages) - 1:
            self.disabled = True
        else:
            self.disabled = False


class PrevButton(NavButton[NavigatorViewT]):
    """
    A built-in NavButton to jump to previous page.
    """

    def __init__(
        self,
        *,
        style: Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.PRIMARY,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        emoji: Union[hikari.Emoji, str, None] = chr(9664),
        row: Optional[int] = None,
    ):
        super().__init__(style=style, label=label, custom_id=custom_id, emoji=emoji, row=row)

    async def callback(self, interaction: Interaction) -> None:
        self.view.current_page -= 1
        await self.view.send_page(self.view.current_page, interaction)

    async def before_page_change(self) -> None:
        if self.view.current_page == 0:
            self.disabled = True
        else:
            self.disabled = False


class FirstButton(NavButton[NavigatorViewT]):
    """
    A built-in NavButton to jump to first page.
    """

    def __init__(
        self,
        *,
        style: Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.PRIMARY,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        emoji: Union[hikari.Emoji, str, None] = chr(9194),
        row: Optional[int] = None,
    ):
        super().__init__(style=style, label=label, custom_id=custom_id, emoji=emoji, row=row)

    async def callback(self, interaction: Interaction) -> None:
        self.view.current_page = 0
        await self.view.send_page(self.view.current_page, interaction)

    async def before_page_change(self) -> None:
        if self.view.current_page == 0:
            self.disabled = True
        else:
            self.disabled = False


class LastButton(NavButton[NavigatorViewT]):
    """
    A built-in NavButton to jump to the last page.
    """

    def __init__(
        self,
        *,
        style: Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.PRIMARY,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        emoji: Union[hikari.Emoji, str, None] = chr(9193),
        row: Optional[int] = None,
    ):
        super().__init__(style=style, label=label, custom_id=custom_id, emoji=emoji, row=row)

    async def callback(self, interaction: Interaction) -> None:
        self.view.current_page = len(self.view.pages) - 1
        await self.view.send_page(self.view.current_page, interaction)

    async def before_page_change(self) -> None:
        if self.view.current_page == len(self.view.pages) - 1:
            self.disabled = True
        else:
            self.disabled = False


class IndicatorButton(NavButton[NavigatorViewT]):
    """
    A built-in NavButton to show the current page's number.
    """

    def __init__(
        self,
        *,
        style: Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.SECONDARY,
        custom_id: Optional[str] = None,
        emoji: Union[hikari.Emoji, str, None] = None,
        row: Optional[int] = None,
    ):
        # Either label or emoji is required, so we pass a placeholder
        super().__init__(style=style, label="0/0", custom_id=custom_id, emoji=emoji, row=row, disabled=True)

    async def before_page_change(self) -> None:
        self.label = f"{self.view.current_page+1}/{len(self.view.pages)}"


class StopButton(NavButton[NavigatorViewT]):
    """
    A built-in NavButton to stop the navigator and disable all buttons.
    """

    def __init__(
        self,
        *,
        style: Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.DANGER,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        emoji: Union[hikari.Emoji, str, None] = chr(9209),
        row: Optional[int] = None,
    ):
        super().__init__(style=style, label=label, custom_id=custom_id, emoji=emoji, row=row)

    async def callback(self, interaction: Interaction) -> None:
        if self.view.message:
            for button in self.view.children:
                button.disabled = True

            await self.view.message.edit(components=self.view.build())
            self.view.stop()
