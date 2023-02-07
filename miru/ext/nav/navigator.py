from __future__ import annotations

import datetime
import logging
import typing as t

import hikari

from miru.abc import Item
from miru.context import Context
from miru.view import View

from .items import FirstButton
from .items import IndicatorButton
from .items import LastButton
from .items import NavButton
from .items import NavItem
from .items import NextButton
from .items import PrevButton

logger = logging.getLogger(__name__)

__all__ = ("NavigatorView",)


class NavigatorView(View):
    """A specialized view built for paginated button-menus, navigators.

    Parameters
    ----------
    pages : List[Union[str, hikari.Embed]]
        A list of strings or embeds that this navigator should paginate.
    buttons : Optional[List[NavButton[NavigatorViewT]]], optional
        A list of navigation buttons to override the default ones with, by default None
    timeout : Optional[float], optional
        The duration after which the view times out, in seconds, by default 120.0
    autodefer : bool, optional
        If unhandled interactions should be automatically deferred or not, by default True

    Raises
    ------
    TypeError
        One or more pages are not an instance of str or hikari.Embed
    """

    def __init__(
        self,
        *,
        pages: t.Sequence[t.Union[str, hikari.Embed]],
        buttons: t.Optional[t.Sequence[NavButton]] = None,
        timeout: t.Optional[t.Union[float, int, datetime.timedelta]] = 120.0,
        autodefer: bool = True,
    ) -> None:
        self._pages: t.Sequence[t.Union[str, hikari.Embed]] = pages
        self._current_page: int = 0
        self._ephemeral: bool = False
        # If the nav is using interaction-based handling or not
        self._using_inter: bool = False
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
    def pages(self) -> t.Sequence[t.Union[str, hikari.Embed]]:
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
        self._current_page = max(0, min(value, len(self.pages) - 1))

    @property
    def ephemeral(self) -> bool:
        """
        Value determining if the navigator is sent ephemerally or not.
        This value will be ignored if the navigator is not sent on an interaction.
        """
        return self._ephemeral

    @property
    def children(self) -> t.Sequence[NavItem]:
        return t.cast(t.Sequence[NavItem], super().children)

    async def on_timeout(self) -> None:
        if (self.message is None) or (self._using_inter and self._inter is None):
            return

        for button in self.children:
            assert isinstance(button, NavItem)
            button.disabled = True

        if self._using_inter and self._inter:
            await self._inter.edit_initial_response(components=self)
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

    def add_item(self, item: Item[hikari.impl.MessageActionRowBuilder]) -> NavigatorView:
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
            raise TypeError(f"Expected type 'NavItem' for parameter item, not '{item.__class__.__name__}'.")

        return t.cast(NavigatorView, super().add_item(item))

    def remove_item(self, item: Item[hikari.impl.MessageActionRowBuilder]) -> NavigatorView:
        return t.cast(NavigatorView, super().remove_item(item))

    def clear_items(self) -> NavigatorView:
        return t.cast(NavigatorView, super().clear_items())

    def _get_page_payload(self, page: t.Union[str, hikari.Embed]) -> t.MutableMapping[str, t.Any]:
        """Get the page content that is to be sent."""

        content = page if isinstance(page, str) else ""
        embeds = [page] if isinstance(page, hikari.Embed) else []

        if not content and not embeds:
            raise TypeError(f"Expected type 'str' or 'hikari.Embed' to send as page, not '{page.__class__.__name__}'.")

        if self.ephemeral:
            return dict(
                content=content,
                embeds=embeds,
                components=self,
                flags=hikari.MessageFlag.EPHEMERAL,
            )
        else:
            return dict(content=content, embeds=embeds, components=self)

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
            The index of the page to send, if not specifed, sends the current page, by default None
        """
        if page_index is not None:
            self.current_page = page_index

        page = self.pages[self.current_page]

        for button in self.children:
            if isinstance(button, NavItem):
                await button.before_page_change()

        payload = self._get_page_payload(page)

        self._inter = context.interaction  # Update latest inter

        await context.edit_response(**payload, attachment=None)

    async def swap_pages(
        self, context: Context[t.Any], new_pages: t.Sequence[t.Union[str, hikari.Embed]], start_at: int = 0
    ) -> None:
        """Swap out the pages of the navigator to the newly provided pages.
        By default, the navigator will reset to the first page.

        Parameters
        ----------
        context : Context
            The context object that should be used to send the updated pages
        new_pages : Sequence[Union[str, Embed]]
            The new pages to swap to
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
        to: t.Union[hikari.SnowflakeishOr[hikari.TextableChannel], hikari.MessageResponseMixin[t.Any]],
        *,
        start_at: int = 0,
        ephemeral: bool = False,
        responded: bool = False,
    ) -> None:
        """Start up the navigator, send the first page, and start listening for interactions.

        Parameters
        ----------
        to : Union[hikari.SnowflakeishOr[hikari.PartialChannel], hikari.MessageResponseMixin[Any]]
            The channel or interaction to send the navigator to.
        start_at : int
            If provided, the page number to start the pagination at.
        ephemeral : bool
            If an interaction was provided, determines if the navigator will be sent ephemerally or not.
        responded : bool
            If an interaction was provided, determines if the interaction was previously acknowledged or not.
        """
        self._ephemeral = ephemeral if isinstance(to, hikari.MessageResponseMixin) else False
        self._using_inter = isinstance(to, hikari.MessageResponseMixin)

        for button in self.children:
            if isinstance(button, NavItem):
                await button.before_page_change()

        if self.ephemeral and self.timeout and self.timeout > 900:
            logger.warning(
                f"Using a timeout value longer than 900 seconds (Used {self.timeout}) in ephemeral navigator {type(self).__name__} may cause on_timeout to fail."
            )

        payload = self._get_page_payload(self.pages[start_at])

        if isinstance(to, (int, hikari.TextableChannel)):
            channel = hikari.Snowflake(to)
            message = await self.app.rest.create_message(channel, **payload)

        else:
            self._inter = to
            if not responded:
                await to.create_initial_response(
                    hikari.ResponseType.MESSAGE_CREATE,
                    **payload,
                )
                message = await to.fetch_initial_response()
            else:
                message = await to.execute(**payload)

        if self.is_persistent and not self.is_bound:
            return  # Do not start the view if unbound persistent

        await self.start(message, start_at=start_at)


# MIT License
#
# Copyright (c) 2022-present HyperGH
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
