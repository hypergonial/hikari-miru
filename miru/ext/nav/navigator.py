from __future__ import annotations

import logging
import typing as t

import attr
import hikari

from miru.context import Context
from miru.view import View

from .items import FirstButton, IndicatorButton, LastButton, NavButton, NavItem, NextButton, PrevButton

if t.TYPE_CHECKING:
    import datetime

    import typing_extensions as te

    from miru.abc import Item

logger = logging.getLogger(__name__)

__all__ = ("NavigatorView", "Page")


class NavigatorView(View):
    """A specialized view built for paginated button-menus, navigators.

    Parameters
    ----------
    pages : List[Union[str, hikari.Embed, Sequence[hikari.Embed], Page]]
        A list of strings, embeds or page objects that this navigator should paginate.
    buttons : Optional[List[NavButton[NavigatorViewT]]], optional
        A list of navigation buttons to override the default ones with, by default None
    timeout : Optional[Union[float, int, datetime.timedelta]], optional
        The duration after which the view times out, in seconds, by default 120.0
    autodefer : bool, optional
        If enabled, interactions will be automatically deferred if not responded to within 2 seconds, by default True

    Raises
    ------
    TypeError
        One or more pages are not an instance of str or hikari.Embed
    """

    def __init__(
        self,
        *,
        pages: t.Sequence[t.Union[str, hikari.Embed, t.Sequence[hikari.Embed], Page]],
        buttons: t.Optional[t.Sequence[NavButton]] = None,
        timeout: t.Optional[t.Union[float, int, datetime.timedelta]] = 120.0,
        autodefer: bool = True,
    ) -> None:
        self._pages: t.Sequence[t.Union[str, hikari.Embed, t.Sequence[hikari.Embed], Page]] = pages
        self._current_page: int = 0
        self._ephemeral: bool = False
        # The last interaction received, used for inter-based handling
        self._inter: t.Optional[hikari.MessageResponseMixin[t.Any]] = None
        super().__init__(timeout=timeout, autodefer=autodefer)

        if buttons is not None:
            for button in buttons:
                self.add_item(button)
        else:
            default_buttons = self.get_default_buttons()
            for default_button in default_buttons:
                self.add_item(default_button)

        if not pages:
            raise ValueError(f"Expected at least one page to be passed to {type(self).__name__}.")

    @property
    def pages(self) -> t.Sequence[t.Union[str, hikari.Embed, t.Sequence[hikari.Embed], Page]]:
        """The pages the navigator is iterating through."""
        return self._pages

    @property
    def current_page(self) -> int:
        """The current page of the navigator, zero-indexed integer."""
        return self._current_page

    @current_page.setter
    def current_page(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("Expected type int for property current_page.")

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
        else:
            await self.message.edit(components=self)

    def get_default_buttons(self) -> t.Sequence[NavButton]:
        """Returns the default set of buttons.

        Returns
        -------
        List[NavButton[NavigatorViewT]]
            A list of the default navigation buttons.
        """
        return [FirstButton(), PrevButton(), IndicatorButton(), NextButton(), LastButton()]

    def add_item(self, item: Item[hikari.impl.MessageActionRowBuilder]) -> te.Self:
        """Adds a new item to the navigator. Item must be of type NavItem.

        Parameters
        ----------
        item : Item[MessageActionRowBuilder]
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
        if not isinstance(item, NavItem):
            raise TypeError(f"Expected type 'NavItem' for parameter item, not '{type(item).__name__}'.")

        return super().add_item(item)

    def _get_page_payload(
        self, page: t.Union[str, hikari.Embed, t.Sequence[hikari.Embed], Page]
    ) -> t.MutableMapping[str, t.Any]:
        """Get the page content that is to be sent."""
        if isinstance(page, Page):
            d: t.Dict[str, t.Any] = page._build_payload()
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

    async def send_page(self, context: Context[t.Any], page_index: t.Optional[int] = None) -> None:
        """Send a page, editing the original message.

        Parameters
        ----------
        context : Context
            The context object that should be used to send this page
        page_index : Optional[int], optional
            The index of the page to send, if not specified, sends the current page, by default None
        """
        if page_index is not None:
            self.current_page = page_index

        page = self.pages[self.current_page]

        for item in self.children:
            if isinstance(item, NavItem):
                await item.before_page_change()

        payload = self._get_page_payload(page)

        self._inter = context.interaction  # Update latest inter

        await context.edit_response(**payload)

    async def swap_pages(
        self,
        context: Context[t.Any],
        new_pages: t.Sequence[t.Union[str, hikari.Embed, t.Sequence[hikari.Embed], Page]],
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
        start_at : int, optional
            The page to start at, by default 0
        """
        if not new_pages:
            raise ValueError(f"Expected at least one page to be passed to {type(self).__name__}.")

        self._pages = new_pages
        await self.send_page(context, page_index=start_at)

    async def start(
        self,
        message: t.Optional[
            t.Union[
                hikari.SnowflakeishOr[hikari.PartialMessage], t.Awaitable[hikari.SnowflakeishOr[hikari.PartialMessage]]
            ]
        ] = None,
        *,
        start_at: int = 0,
    ) -> None:
        """Start up the navigator listener. This should not be called directly, use send() instead.

        Parameters
        ----------
        message : Union[hikari.Message, Awaitable[hikari.Message]]
            If provided, the view will be bound to this message, and if the
            message is edited with a new view, this view will be stopped.
            Unbound views do not support message editing with additional views.
        start_at : int, optional
            The page index to start at, by default 0
        """
        await super().start(message)
        self.current_page = start_at

    async def send(
        self,
        to: t.Union[hikari.SnowflakeishOr[hikari.TextableChannel], hikari.MessageResponseMixin[t.Any], Context[t.Any]],
        *,
        start_at: int = 0,
        ephemeral: bool = False,
        responded: bool = False,
    ) -> None:
        """Start up the navigator, send the first page, and start listening for interactions.

        Parameters
        ----------
        to : Union[hikari.SnowflakeishOr[hikari.PartialChannel], hikari.MessageResponseMixin[Any], miru.Context]
            The channel, interaction, or miru context to send the navigator to.
        start_at : int
            If provided, the page number to start the pagination at.
        ephemeral : bool
            If an interaction or context was provided, determines if the navigator will be sent ephemerally or not.
            This is ignored if a channel was provided, as regular messages cannot be ephemeral.
        responded : bool
            If an interaction was provided, determines if the interaction was previously acknowledged or not.
            This is ignored if a channel or context was provided.
        """
        self._ephemeral = ephemeral if isinstance(to, (hikari.MessageResponseMixin, Context)) else False

        for item in self.children:
            if isinstance(item, NavItem):
                await item.before_page_change()

        if self.ephemeral and self.timeout and self.timeout > 900:
            logger.warning(
                f"Using a timeout value longer than 900 seconds (Used {self.timeout}) in ephemeral navigator {type(self).__name__} may cause on_timeout to fail."
            )

        payload = self._get_page_payload(self.pages[start_at])

        if isinstance(to, (int, hikari.TextableChannel)):
            channel = hikari.Snowflake(to)
            message = await self.app.rest.create_message(channel, **payload)
        elif isinstance(to, Context):
            self._inter = to.interaction
            resp = await to.respond(**payload)
            message = await resp.retrieve_message()
        else:
            self._inter = to
            if not responded:
                await to.create_initial_response(hikari.ResponseType.MESSAGE_CREATE, **payload)
                message = await to.fetch_initial_response()
            else:
                message = await to.execute(**payload)

        if self.is_persistent and not self.is_bound:
            return  # Do not start the view if unbound persistent

        await self.start(message, start_at=start_at)


@attr.define(slots=True)
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
    user_mentions: hikari.UndefinedOr[t.Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]] = hikari.UNDEFINED
    """The set of allowed user mentions in this page's message. Set to True to allow all."""
    role_mentions: hikari.UndefinedOr[t.Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]] = hikari.UNDEFINED
    """The set of allowed role mentions in this page's message. Set to True to allow all."""

    def _build_payload(self) -> t.Dict[str, t.Any]:
        d: t.Dict[str, t.Any] = {
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
