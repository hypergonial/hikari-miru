from __future__ import annotations

import logging
import typing as t

import attr
import hikari
import typing_extensions as te

from miru.ext.nav.items import FirstButton, IndicatorButton, LastButton, NavButton, NavItem, NextButton, PrevButton
from miru.internal.deprecation import warn_deprecate
from miru.internal.version import Version
from miru.response import MessageBuilder
from miru.view import View

if t.TYPE_CHECKING:
    import datetime

    from miru.abc.context import Context
    from miru.client import Client
    from miru.context.view import AutodeferOptions

logger = logging.getLogger(__name__)

__all__ = ("NavigatorView", "Page")


class NavigatorView(View):
    """A specialized view built for paginated button-menus, navigators.

    Parameters
    ----------
    pages : list[str | hikari.Embed | t.Sequence[hikari.Embed] | Page]
        A list of strings, embeds or page objects that this navigator should paginate.
    buttons : list[NavButton] | None
        A list of navigation buttons to override the default ones with
    timeout : float | int | datetime.timedelta | None
        The duration after which the view times out, in seconds
    autodefer : bool | AutodeferOptions
        If enabled, interactions will be automatically deferred if not responded to within 2 seconds

    Raises
    ------
    TypeError
        One or more pages are not an instance of str or hikari.Embed
    """

    @t.overload
    def __init__(
        self,
        *,
        pages: t.Sequence[str | hikari.Embed | t.Sequence[hikari.Embed] | Page],
        items: t.Sequence[NavItem] | None = None,
        timeout: float | int | datetime.timedelta | None = 120.0,
        autodefer: bool | AutodeferOptions = True,
    ) -> None:
        ...

    @te.deprecated("Use 'items=' instead of 'buttons='. 'buttons=' will be removed in version v4.2.0.")
    @t.overload
    def __init__(
        self,
        *,
        pages: t.Sequence[str | hikari.Embed | t.Sequence[hikari.Embed] | Page],
        buttons: t.Sequence[NavButton] | None = None,
        timeout: float | int | datetime.timedelta | None = 120.0,
        autodefer: bool | AutodeferOptions = True,
    ) -> None:
        ...

    def __init__(
        self,
        *,
        pages: t.Sequence[str | hikari.Embed | t.Sequence[hikari.Embed] | Page],
        buttons: t.Sequence[NavButton] | None = None,
        items: t.Sequence[NavItem] | None = None,
        timeout: float | int | datetime.timedelta | None = 120.0,
        autodefer: bool | AutodeferOptions = True,
    ) -> None:
        self._pages: t.Sequence[str | hikari.Embed | t.Sequence[hikari.Embed] | Page] = pages
        self._current_page: int = 0
        self._ephemeral: bool = False
        # The last interaction received, used for inter-based handling
        self._inter: hikari.MessageResponseMixin[t.Any] | None = None
        super().__init__(timeout=timeout, autodefer=autodefer)

        if items is not None:
            for item in items:
                self.add_item(item)

        if buttons is not None:
            warn_deprecate(what="passing 'buttons=' to NavigatorView", when=Version(4, 2, 0), use_instead="items=")

            for button in buttons:
                self.add_item(button)
        else:
            default_buttons = self.get_default_buttons()
            for default_button in default_buttons:
                self.add_item(default_button)

        if not pages:
            raise ValueError(f"Expected at least one page to be passed to {type(self).__name__}.")

    @property
    def pages(self) -> t.Sequence[str | hikari.Embed | t.Sequence[hikari.Embed] | Page]:
        """The pages the navigator is iterating through."""
        return self._pages

    @property
    def current_page(self) -> int:
        """The current page of the navigator, zero-indexed integer."""
        return self._current_page

    @current_page.setter
    def current_page(self, value: int) -> None:
        # Ensure this value is always correct
        self._current_page = max(0, min(value, len(self.pages) - 1))

    @property
    def ephemeral(self) -> bool:
        """Value determining if the navigator is sent ephemerally or not.
        This value will be ignored if the navigator is not sent on an interaction.
        """
        return self._ephemeral

    @property
    def children(self) -> t.Sequence[NavItem]:
        return t.cast(t.Sequence[NavItem], super().children)

    async def on_timeout(self) -> None:
        if self.message is None:
            return

        for item in self.children:
            item.disabled = True

        if self._inter is not None:
            await self._inter.edit_message(self.message, components=self)
        elif not self._ephemeral:
            await self.message.edit(components=self)

    def get_default_buttons(self) -> t.Sequence[NavButton]:
        """Returns the default set of buttons.

        Returns
        -------
        List[NavButton]
            A list of the default navigation buttons.
        """
        return [FirstButton(), PrevButton(), IndicatorButton(), NextButton(), LastButton()]

    def add_item(self, item: NavItem) -> te.Self:  # pyright: ignore reportIncompatibleMethodOverride
        """Adds a new item to the navigator. Item must be of type NavItem.

        Parameters
        ----------
        item : ViewItem
            An instance of NavItem

        Raises
        ------
        TypeError
            Parameter item was not an instance of NavItem

        Returns
        -------
        ItemHandler
            The item handler the item was added to.
        """
        return super().add_item(item)

    def remove_item(self, item: NavItem) -> te.Self:  # pyright: ignore reportIncompatibleMethodOverride
        return super().remove_item(item)

    def _get_page_payload(
        self, page: str | hikari.Embed | t.Sequence[hikari.Embed] | Page
    ) -> t.MutableMapping[str, t.Any]:
        """Get the page content that is to be sent."""
        if isinstance(page, Page):
            d: dict[str, t.Any] = page._build_payload()
            d["components"] = self
            if self.ephemeral:
                d["flags"] = hikari.MessageFlag.EPHEMERAL
            return d

        content = page if isinstance(page, str) else ""
        if page and isinstance(page, t.Sequence) and isinstance(page[0], hikari.Embed):
            embeds = page
        else:
            embeds = [page] if isinstance(page, hikari.Embed) else []

        if not content and not embeds:
            raise TypeError(
                "Expected type 'str', 'hikari.Embed', 'Sequence[hikari.Embed]' or 'ext.nav.Page' "
                f"to send as page, not '{type(page).__name__}'."
            )
        d = {
            "content": content,
            "embeds": embeds,
            "attachments": None,
            "mentions_everyone": False,
            "user_mentions": False,
            "role_mentions": False,
            "components": self,
        }
        if self.ephemeral:
            d["flags"] = hikari.MessageFlag.EPHEMERAL

        return d

    @property
    def is_persistent(self) -> bool:
        return super().is_persistent and not self.ephemeral

    async def send_page(self, context: Context[t.Any], page_index: int | None = None) -> None:
        """Send a page, editing the original message.

        Parameters
        ----------
        context : Context
            The context object that should be used to send this page
        page_index : Optional[int]
            The index of the page to send, if not specified, sends the current page
        """
        if page_index is not None:
            self.current_page = page_index

        page = self.pages[self.current_page]

        for item in self.children:
            await item.before_page_change()

        payload = self._get_page_payload(page)

        self._inter = context.interaction  # Update latest inter

        await context.edit_response(**payload)

    async def swap_pages(
        self,
        context: Context[t.Any],
        new_pages: t.Sequence[str | hikari.Embed | t.Sequence[hikari.Embed] | Page],
        start_at: int = 0,
    ) -> None:
        """Swap out the pages of the navigator to the newly provided pages.
        By default, the navigator will reset to the first page.

        Parameters
        ----------
        context : Context
            The context object that should be used to send the updated pages
        new_pages : Sequence[Union[str, Embed, Sequence[Embed] | Page]]
            The new sequence of pages to swap to
        start_at : int
            The page to start at
        """
        if not new_pages:
            raise ValueError(f"Expected at least one page to be passed to {type(self).__name__}.")

        self._pages = new_pages
        await self.send_page(context, page_index=start_at)

    async def build_response_async(
        self, client: Client, *, start_at: int = 0, ephemeral: bool = False
    ) -> MessageBuilder:
        """Create a response builder out of this Navigator.
        This also invokes all [`before_page_change()`][miru.ext.nav.items.NavItem.before_page_change] methods.

        !!! tip
            If it takes too long to invoke all `before_page_change()` methods, you may want to
            defer the interaction before calling this method.

        Parameters
        ----------
        client : Client
            The client instance to use to build the response
        ephemeral : bool
            Determines if the navigator will be sent ephemerally or not.
        start_at : int
            The page index to start at
        """
        if self._client is not None:
            raise RuntimeError("Navigator is already bound to a client.")

        if ephemeral and self.timeout is not None and self.timeout > 900:
            logger.warning(
                "Ephemeral navigators with a timeout greater than 15 minutes will fail. "
                "Consider lowering the timeout."
            )

        self.current_page = start_at
        self._ephemeral = ephemeral

        for item in self.children:
            await item.before_page_change()

        builder = MessageBuilder(hikari.ResponseType.MESSAGE_CREATE, **self._get_page_payload(self.pages[start_at]))
        builder._client = client
        return builder


@attr.define(slots=True, kw_only=True)
class Page:
    """Allows for the building of more complex pages for use with NavigatorView."""

    content: hikari.UndefinedOr[t.Any] = hikari.UNDEFINED
    """The content of the message. Anything passed here will be cast to str."""
    attachment: hikari.UndefinedOr[hikari.Resourceish] = hikari.UNDEFINED
    """An attachment to add to this page."""
    attachments: hikari.UndefinedOr[t.Sequence[hikari.Resourceish]] = hikari.UNDEFINED
    """A sequence of attachments to add to this page."""
    embed: hikari.UndefinedOr[hikari.Embed] = hikari.UNDEFINED
    """An embed to add to this page."""
    embeds: hikari.UndefinedOr[t.Sequence[hikari.Embed]] = hikari.UNDEFINED
    """A sequence of embeds to add to this page."""
    mentions_everyone: hikari.UndefinedOr[bool] = hikari.UNDEFINED
    """If True, mentioning @everyone will be allowed in this page's message."""
    user_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialUser] | bool] = hikari.UNDEFINED
    """The set of allowed user mentions in this page's message. Set to True to allow all."""
    role_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialRole] | bool] = hikari.UNDEFINED
    """The set of allowed role mentions in this page's message. Set to True to allow all."""

    def _build_payload(self) -> dict[str, t.Any]:
        d: dict[str, t.Any] = {
            "content": self.content or None,
            "attachments": self.attachments or None,
            "embeds": self.embeds or None,
            "mentions_everyone": self.mentions_everyone or False,
            "user_mentions": self.user_mentions or False,
            "role_mentions": self.role_mentions or False,
        }
        if not d["attachments"] and self.attachment:
            d["attachments"] = [self.attachment]

        if not d["embeds"] and self.embed:
            d["embeds"] = [self.embed]

        return d


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
