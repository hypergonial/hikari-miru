from __future__ import annotations

import logging
import typing as t

import hikari

import miru

from .screen import Screen

logger = logging.getLogger(__name__)

__all__ = ("Menu",)

ViewContextT = t.TypeVar("ViewContextT", bound="miru.ViewContext")


class Menu(miru.View):
    """A menu that can be used to display multiple nested screens of components."""

    def __init__(self, *, timeout: float = 300.0, autodefer: bool = True):
        super().__init__(timeout=timeout, autodefer=autodefer)
        self._stack: t.List[Screen] = []
        # The interaction that was used to send the menu, if any.
        self._inter: t.Optional[hikari.MessageResponseMixin[t.Any]] = None
        self._ephemeral: bool = False
        self._payload: t.Dict[str, t.Any] = {}

    @property
    def is_persistent(self) -> bool:
        return False

    @property
    def ephemeral(self) -> bool:
        return self._ephemeral

    @property
    def current_screen(self) -> Screen:
        return self._stack[-1]

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

        await self.update_message()

    async def _load_screen(self, screen: Screen) -> None:
        """Load a screen into the menu, updating it's state."""

        self.clear_items()

        self._payload = (await screen.build_content())._build_payload()

        if self.ephemeral:
            self._payload["flags"] = hikari.MessageFlag.EPHEMERAL

        for item in screen.children:
            self.add_item(item)

    async def update_message(self) -> None:
        """Update the message with the current state of the menu."""

        if self.message is None:
            return

        if self.last_context is not None and self.last_context.is_valid:
            await self.last_context.edit_response(components=self, **self._payload)
        elif self.last_context is None and self._inter is not None:
            await self._inter.edit_message(self.message, components=self, **self._payload)
        else:
            await self.message.edit(components=self, **self._payload)

    async def push(self, screen: Screen) -> None:
        """Push a screen onto the menu stack and display it."""

        self._stack.append(screen)

        await self._load_screen(screen)
        await self.update_message()

    async def pop(self, count: int = 1) -> None:
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

        if count > len(self._stack) + 1:
            raise ValueError("Cannot pop the last screen.")

        self._stack = self._stack[:-count]
        await self._load_screen(self.current_screen)
        await self.update_message()

    async def pop_until_root(self) -> None:
        """Pop all screens off the menu stack until the root screen is reached."""
        if not self._stack:
            raise ValueError("The menu contains no screens. Did you send the Menu?")

        if len(self._stack) == 1:
            return

        self._stack = [self._stack[0]]

        await self._load_screen(self.current_screen)
        await self.update_message()

    async def send(
        self,
        starting_screen: Screen,
        to: t.Union[
            hikari.SnowflakeishOr[hikari.TextableChannel], hikari.MessageResponseMixin[t.Any], miru.Context[t.Any]
        ],
        ephemeral: bool = False,
        responded: bool = False,
    ) -> None:
        """Start up the menu, send the starting screen, and start listening for interactions.

        Parameters
        ----------
        starting_screen : Screen
            The screen to start the menu with.
        to : Union[hikari.SnowflakeishOr[hikari.PartialChannel], hikari.MessageResponseMixin[Any], miru.Context]
            The channel, interaction, or miru context to send the menu to.
        ephemeral : bool
            If an interaction or context was provided, determines if the navigator will be sent ephemerally or not.
            This is ignored if a channel was provided, as regular messages cannot be ephemeral.
        responded : bool
            If an interaction was provided, determines if the interaction was previously acknowledged or not.
            This is ignored if a channel or context was provided.
        """

        self._ephemeral = ephemeral if isinstance(to, (hikari.MessageResponseMixin, miru.Context)) else False
        self._stack.append(starting_screen)

        if self.ephemeral and self.timeout and self.timeout > 900:
            logger.warning(
                f"Using a timeout value longer than 900 seconds (Used {self.timeout}) in ephemeral menu {type(self).__name__} may cause on_timeout to fail."
            )

        await self._load_screen(starting_screen)

        if isinstance(to, (int, hikari.TextableChannel)):
            channel = hikari.Snowflake(to)
            message = await self.app.rest.create_message(channel, components=self, **self._payload)
        elif isinstance(to, miru.Context):
            self._inter = to.interaction
            resp = await to.respond(**self._payload)
            message = await resp.retrieve_message()
        else:
            self._inter = to
            if not responded:
                await to.create_initial_response(hikari.ResponseType.MESSAGE_CREATE, components=self, **self._payload)
                message = await to.fetch_initial_response()
            else:
                message = await to.execute(components=self, **self._payload)

        await self.start(message)
