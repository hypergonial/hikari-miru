from __future__ import annotations

import typing as t

import attr
import hikari

from .abc.item_handler import ItemHandler
from .context.raw import RawComponentContext
from .context.raw import RawModalContext
from .modal import Modal
from .view import View

if t.TYPE_CHECKING:
    from .traits import MiruAware

__all__ = (
    "Event",
    "ComponentInteractionCreateEvent",
    "ModalInteractionCreateEvent",
)


@attr.define()
class Event(hikari.Event):
    """A base class for every miru event."""

    app: MiruAware = attr.field()


@attr.define()
class InteractionCreateEvent(Event):
    """Event fired when a miru interaction is received. This may either be a modal or a component interaction."""

    interaction: t.Union[hikari.ModalInteraction, hikari.ComponentInteraction] = attr.field()

    @property
    def guild_id(self) -> t.Optional[hikari.Snowflake]:
        """The ID of the guild this event was received from."""
        return self.interaction.guild_id

    @property
    def channel_id(self) -> hikari.Snowflake:
        """The ID of the channel this event was received from."""
        return self.interaction.channel_id

    @property
    def user(self) -> hikari.User:
        """The user that triggered this interaction."""
        return self.interaction.user

    @property
    def author(self) -> hikari.User:
        """An alias for 'user'."""
        return self.user

    @property
    def member(self) -> t.Optional[hikari.Member]:
        """The member that triggered this interaction, `None` if not in a guild."""
        return self.interaction.member

    @property
    def message(self) -> t.Optional[hikari.Message]:
        """The message that the interaction belongs to."""
        return self.interaction.message

    @property
    def custom_id(self) -> str:
        """The developer-provided custom ID of the interaction."""
        return self.interaction.custom_id

    def get_channel(self) -> t.Optional[hikari.TextableGuildChannel]:
        """Gets the channel object from the interaction, returns `None` if cache is not enabled."""
        return self.interaction.get_channel()

    def get_guild(self) -> t.Optional[hikari.GatewayGuild]:
        """Gets the guild object from the interaction, returns `None` if cache is not enabled."""
        return self.interaction.get_guild()


@attr.define()
class ComponentInteractionCreateEvent(InteractionCreateEvent):
    """
    An event that is dispatched when a new component interaction is received.
    This event is only dispatched if the interaction was not handled by a miru view.
    """

    interaction: hikari.ComponentInteraction = attr.field()
    context: RawComponentContext = attr.field()


@attr.define()
class ModalInteractionCreateEvent(InteractionCreateEvent):
    """
    An event that is dispatched when a new modal interaction is received.
    This event is only dispatched if the interaction was not handled by a miru modal.
    """

    interaction: hikari.ModalInteraction = attr.field()
    context: RawModalContext = attr.field()


class EventHandler:
    """Singleton class for handling events."""

    _app: t.Optional[MiruAware] = None
    """The currently running app instance that will be subscribed to the listener."""

    _bound_handlers: t.MutableMapping[hikari.Snowflakeish, ItemHandler[t.Any]] = {}
    """A mapping of message_id to ItemHandler. This contains handlers that are bound to a message or custom_id."""

    _handlers: t.MutableMapping[str, ItemHandler[t.Any]] = {}
    """A mapping of custom_id to ItemHandler. This only contains handlers that are not bound to a message."""

    def __new__(cls: type[EventHandler]) -> EventHandler:
        if not hasattr(cls, "instance"):  # Ensure that class remains singleton
            cls.instance = super(EventHandler, cls).__new__(cls)
        return cls.instance

    def start(self, app: MiruAware) -> None:
        """Start all custom event listeners, this is called during miru.install()"""
        if self._app is not None:
            self.close()
        self._app = app
        self._app.event_manager.subscribe(hikari.InteractionCreateEvent, self._handle_events)

    def close(self) -> None:
        """Stop all custom event listeners for events, this is called during miru.uninstall()"""
        if self._app is None:
            raise RuntimeError(f"miru was never installed, cannot close listener.")
        self._app.event_manager.unsubscribe(hikari.InteractionCreateEvent, self._handle_events)
        self._bound_handlers.clear()
        self._handlers.clear()
        self._app = None

    def add_handler(self, handler: ItemHandler[t.Any]) -> None:
        """Add a handler to the event handler."""
        if isinstance(handler, View):
            if handler.is_bound and handler._message_id is not None:
                self._bound_handlers[handler._message_id] = handler
            else:
                for custom_id in (item.custom_id for item in handler.children):
                    self._handlers[custom_id] = handler
        elif isinstance(handler, Modal):
            self._handlers[handler.custom_id] = handler

    def remove_handler(self, handler: ItemHandler[t.Any]) -> None:
        """Remove a handler from the event handler."""
        if isinstance(handler, View):
            if handler.is_bound and handler._message_id is not None:
                self._bound_handlers.pop(handler._message_id, None)
            else:
                for custom_id in (item.custom_id for item in handler.children):
                    self._handlers.pop(custom_id, None)
        elif isinstance(handler, Modal):
            self._handlers.pop(handler.custom_id, None)

    async def _handle_events(self, event: hikari.InteractionCreateEvent) -> None:
        """Sort interaction create events and dispatch miru custom events."""

        assert self._app is not None

        if not isinstance(event.interaction, (hikari.ComponentInteraction, hikari.ModalInteraction)):
            return

        if isinstance(event.interaction, hikari.ModalInteraction) and (
            handler := self._handlers.get(event.interaction.custom_id)
        ):
            await handler._process_interactions(event)
            return

        if event.interaction.message and (handler := self._bound_handlers.get(event.interaction.message.id)):
            await handler._process_interactions(event)
            return

        if handler := self._handlers.get(event.interaction.custom_id):
            await handler._process_interactions(event)
            return

        # God why does mypy hate me so much for naming two variables the same in two if statement arms >_<
        if isinstance(event.interaction, hikari.ComponentInteraction):
            comp_ctx = RawComponentContext(event.interaction)
            self._app.event_manager.dispatch(ComponentInteractionCreateEvent(self._app, event.interaction, comp_ctx))

        elif isinstance(event.interaction, hikari.ModalInteraction):
            modal_ctx = RawModalContext(event.interaction)
            self._app.event_manager.dispatch(ModalInteractionCreateEvent(self._app, event.interaction, modal_ctx))


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
