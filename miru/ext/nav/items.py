from __future__ import annotations

import abc
import typing as t

import hikari

from miru.abc.item import InteractiveViewItem, ViewItem
from miru.button import Button, LinkButton
from miru.modal import Modal
from miru.select import ChannelSelect, MentionableSelect, RoleSelect, TextSelect, UserSelect
from miru.text_input import TextInput

if t.TYPE_CHECKING:
    from miru.context.view import ViewContext
    from miru.ext.nav.navigator import NavigatorView
    from miru.internal.types import InteractiveButtonStylesT

__all__ = (
    "NavItem",
    "NavButton",
    "NavTextSelect",
    "NavUserSelect",
    "NavRoleSelect",
    "NavChannelSelect",
    "NavMentionableSelect",
    "NextButton",
    "PrevButton",
    "FirstButton",
    "LastButton",
    "IndicatorButton",
    "StopButton",
)


class NavItem(ViewItem, abc.ABC):
    """An abstract base for all navigation items. NavigatorView requires instances of this class as it's items."""

    def __init__(
        self,
        *,
        custom_id: str | None = None,
        row: int | None = None,
        position: int | None = None,
        disabled: bool = False,
        width: int = 1,
    ) -> None:
        super().__init__(custom_id=custom_id, row=row, width=width, position=position, disabled=disabled)
        self._handler: NavigatorView | None = None  # type: ignore

    async def before_page_change(self) -> None:
        """Called when the navigator is about to transition to the next page.
        Also called when a builder is created out of the navigator this item is attached to.
        """
        pass

    @property
    def view(self) -> NavigatorView:
        """The view this item is attached to."""
        if not self._handler:
            raise AttributeError(f"{type(self).__name__} hasn't been attached to a view yet")
        return self._handler


class InteractiveNavItem(InteractiveViewItem, NavItem):
    """An abstract base for all interactive navigation items."""


class NavLinkButton(LinkButton, NavItem):
    """A base class for all navigation link buttons."""


class NavButton(Button, InteractiveNavItem):
    """A base class for all navigation buttons."""


class NavTextSelect(TextSelect, InteractiveNavItem):
    """A base class for all navigation text selects."""


class NavUserSelect(UserSelect, InteractiveNavItem):
    """A base class for all navigation user selects."""


class NavRoleSelect(RoleSelect, InteractiveNavItem):
    """A base class for all navigation role selects."""


class NavChannelSelect(ChannelSelect, InteractiveNavItem):
    """A base class for all navigation channel selects."""


class NavMentionableSelect(MentionableSelect, InteractiveNavItem):
    """A base class for all navigation mentionable selects."""


class NextButton(NavButton):
    """A built-in NavButton to jump to the next page."""

    def __init__(
        self,
        *,
        style: InteractiveButtonStylesT = hikari.ButtonStyle.PRIMARY,
        label: str | None = None,
        custom_id: str | None = None,
        emoji: hikari.Emoji | str | None = chr(9654),
        row: int | None = None,
        position: int | None = None,
    ):
        super().__init__(style=style, label=label, custom_id=custom_id, emoji=emoji, row=row, position=position)

    async def callback(self, context: ViewContext) -> None:
        self.view.current_page += 1
        await self.view.send_page(context)

    async def before_page_change(self) -> None:
        if self.view.current_page == len(self.view.pages) - 1:
            self.disabled = True
        else:
            self.disabled = False


class PrevButton(NavButton):
    """A built-in NavButton to jump to previous page."""

    def __init__(
        self,
        *,
        style: InteractiveButtonStylesT = hikari.ButtonStyle.PRIMARY,
        label: str | None = None,
        custom_id: str | None = None,
        emoji: hikari.Emoji | str | None = chr(9664),
        row: int | None = None,
        position: int | None = None,
    ):
        super().__init__(style=style, label=label, custom_id=custom_id, emoji=emoji, row=row, position=position)

    async def callback(self, context: ViewContext) -> None:
        self.view.current_page -= 1
        await self.view.send_page(context)

    async def before_page_change(self) -> None:
        if self.view.current_page == 0:
            self.disabled = True
        else:
            self.disabled = False


class FirstButton(NavButton):
    """A built-in NavButton to jump to first page."""

    def __init__(
        self,
        *,
        style: InteractiveButtonStylesT = hikari.ButtonStyle.PRIMARY,
        label: str | None = None,
        custom_id: str | None = None,
        emoji: hikari.Emoji | str | None = chr(9194),
        row: int | None = None,
        position: int | None = None,
    ):
        super().__init__(style=style, label=label, custom_id=custom_id, emoji=emoji, row=row, position=position)

    async def callback(self, context: ViewContext) -> None:
        self.view.current_page = 0
        await self.view.send_page(context)

    async def before_page_change(self) -> None:
        if self.view.current_page == 0:
            self.disabled = True
        else:
            self.disabled = False


class LastButton(NavButton):
    """A built-in NavButton to jump to the last page."""

    def __init__(
        self,
        *,
        style: InteractiveButtonStylesT = hikari.ButtonStyle.PRIMARY,
        label: str | None = None,
        custom_id: str | None = None,
        emoji: hikari.Emoji | str | None = chr(9193),
        row: int | None = None,
        position: int | None = None,
    ):
        super().__init__(style=style, label=label, custom_id=custom_id, emoji=emoji, row=row, position=position)

    async def callback(self, context: ViewContext) -> None:
        self.view.current_page = len(self.view.pages) - 1
        await self.view.send_page(context)

    async def before_page_change(self) -> None:
        if self.view.current_page == len(self.view.pages) - 1:
            self.disabled = True
        else:
            self.disabled = False


class IndicatorButton(NavButton):
    """A built-in NavButton to show the current page's number."""

    def __init__(
        self,
        *,
        style: InteractiveButtonStylesT = hikari.ButtonStyle.SECONDARY,
        custom_id: str | None = None,
        emoji: hikari.Emoji | str | None = None,
        disabled: bool = False,
        row: int | None = None,
        position: int | None = None,
    ):
        # Either label or emoji is required, so we pass a placeholder
        super().__init__(
            style=style, label="0/0", custom_id=custom_id, emoji=emoji, disabled=disabled, row=row, position=position
        )

    async def before_page_change(self) -> None:
        self.label = f"{self.view.current_page+1}/{len(self.view.pages)}"
        self.disabled = self.disabled if len(self.view.pages) != 1 else True

    async def callback(self, context: ViewContext) -> None:
        modal = Modal(title="Jump to page")
        modal.add_item(
            TextInput(label="Page Number", placeholder="Enter a page number to jump to it...", custom_id="pgnum")
        )
        await context.respond_with_modal(modal)
        await modal.wait()

        if not modal.last_context:
            return

        try:
            page_number = int(modal.last_context.get_value_by_id("pgnum")) - 1
        except (ValueError, TypeError):
            self.view._inter = modal.last_context.interaction
            await modal.last_context.defer()
            return

        self.view.current_page = page_number
        await self.view.send_page(modal.last_context)


class StopButton(NavButton):
    """A built-in NavButton to stop the navigator and disable all buttons."""

    def __init__(
        self,
        *,
        style: InteractiveButtonStylesT = hikari.ButtonStyle.DANGER,
        label: str | None = None,
        custom_id: str | None = None,
        emoji: hikari.Emoji | str | None = chr(9209),
        row: int | None = None,
        position: int | None = None,
    ):
        super().__init__(style=style, label=label, custom_id=custom_id, emoji=emoji, row=row, position=position)

    async def callback(self, context: ViewContext) -> None:
        if not self.view.message and not self.view._inter:
            return

        for item in self.view.children:
            item.disabled = True

        if self.view._inter:
            await self.view._inter.edit_initial_response(components=self.view)
        elif self.view.message:
            await self.view.message.edit(components=self.view)
        self.view.stop()


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
