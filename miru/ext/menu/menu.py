from __future__ import annotations

import logging
import typing as t

import hikari

import miru

if t.TYPE_CHECKING:
    import datetime

    from miru.ext.menu.screen import Screen, ScreenContent

logger = logging.getLogger(__name__)

__all__ = ("Menu",)


class Menu(miru.View):
    """A menu that can be used to display multiple nested screens of components.

    Parameters
    ----------
    timeout : Optional[Union[float, int, datetime.timedelta]]
        The duration after which the menu times out, in seconds
    autodefer : bool
        If enabled, interactions will be automatically deferred if not responded to within 2 seconds
    """

    def __init__(
        self,
        *,
        timeout: float | int | datetime.timedelta | None = 300.0,
        autodefer: bool | miru.AutodeferOptions = True,
    ):
        super().__init__(timeout=timeout, autodefer=autodefer)
        self._stack: list[Screen] = []
        # The interaction that was used to send the menu, if any.
        self._inter: hikari.MessageResponseMixin[t.Any] | None = None
        self._ephemeral: bool = False
        self._payload: dict[str, t.Any] = {}

    @property
    def is_persistent(self) -> bool:
        return False

    @property
    def ephemeral(self) -> bool:
        """If true, the menu will be sent ephemerally."""
        return self._ephemeral

    @property
    def current_screen(self) -> Screen:
        """The current screen being displayed."""
        return self._stack[-1]

    @property
    def _flags(self) -> hikari.MessageFlag:
        """Flags to use when sending an interaction response."""
        return hikari.MessageFlag.EPHEMERAL if self.ephemeral else hikari.MessageFlag.NONE

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

        await self.update_message()

    async def _load_screen(self, screen: Screen) -> None:
        """Load a screen into the menu, updating it's state."""
        self.clear_items()

        try:
            self._payload = (await screen.build_content())._build_payload()
        except Exception as e:
            await screen.on_error(e)

        for item in screen.children:
            self.add_item(item)

    async def update_message(self, new_content: ScreenContent | None = None) -> None:
        """Update the message with the current state of the menu.

        Parameters
        ----------
        new_content : Optional[ScreenContent]
            The new content to use, if left as None, only the components will be updated
        """
        if self.message is None:
            return

        if new_content is not None:
            self._payload = new_content._build_payload()

        if self.last_context is not None and self.last_context.is_valid:
            await self.last_context.edit_response(components=self, **self._payload, flags=self._flags)
        elif self.last_context is None and self._inter is not None:
            await self._inter.edit_message(self.message, components=self, **self._payload)
        elif not self._ephemeral:
            await self.message.edit(components=self, **self._payload)

    async def push(self, screen: Screen) -> None:
        """Push a screen onto the menu stack and display it.

        Parameters
        ----------
        screen : Screen
            The screen to push onto the stack and display.
        """
        await self.current_screen.on_dispose()
        self._stack.append(screen)

        await self._load_screen(screen)
        await self.update_message()

    async def pop(self, *, count: int = 1) -> None:
        """Pop 'count' screen off the menu stack and display the screen on top of the stack.
        This can be used to go back to the previous screen(s).

        Parameters
        ----------
        count : int
            The number of screens to pop off the stack. Defaults to 1

        Raises
        ------
        ValueError
            Cannot pop less than 1 screen.
        ValueError
            Cannot pop the last screen.
        """
        if not self._stack:
            raise ValueError("The menu contains no screens. Did you send the Menu?")

        if count < 1:
            raise ValueError("Cannot pop less than 1 screen.")

        if count >= len(self._stack):
            raise ValueError("Cannot pop the last screen.")

        for i in range(len(self._stack) - 1, len(self._stack) - count - 1, -1):
            try:
                await self._stack[i].on_dispose()
            except Exception as e:
                await self._stack[i].on_error(e)

        self._stack = self._stack[:-count]
        await self._load_screen(self.current_screen)
        await self.update_message()

    async def pop_until_root(self) -> None:
        """Pop all screens off the menu stack until the root screen is reached."""
        if not self._stack:
            raise ValueError("The menu contains no screens. Did you send the Menu?")

        if len(self._stack) == 1:
            return

        for i in range(len(self._stack) - 1, 0, -1):
            try:
                await self._stack[i].on_dispose()
            except Exception as e:
                await self._stack[i].on_error(e)

        self._stack = [self._stack[0]]

        await self._load_screen(self.current_screen)
        await self.update_message()

    async def build_response_async(
        self, client: miru.Client, starting_screen: Screen, *, ephemeral: bool = False
    ) -> miru.MessageBuilder:
        """Create a REST response builder out of this Menu.

        !!! tip
            If it takes too long to build the starting screen, you may want to
            defer the interaction before calling this method.

        Parameters
        ----------
        client : Client
            The client instance to use to build the response
        starting_screen : Screen
            The screen to start the menu with.
        ephemeral : bool
            Determines if the navigator will be sent ephemerally or not.
        """
        if self._client is not None:
            raise RuntimeError("Navigator is already bound to a client.")

        self._stack.append(starting_screen)
        await self._load_screen(starting_screen)
        self._ephemeral = ephemeral

        builder = miru.MessageBuilder(hikari.ResponseType.MESSAGE_CREATE, components=self, **self._payload)
        builder._client = client
        return builder


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
