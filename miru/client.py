from __future__ import annotations

import abc
import typing as t

import hikari

from .internal.types import AppT, ModalResponseBuildersT, ViewResponseBuildersT
from .modal import Modal
from .view import View

if t.TYPE_CHECKING:
    import typing_extensions as te

    from .abc.item_handler import ItemHandler

__all__ = ("Client", "RESTClient", "GatewayClient", "GW", "REST")

GW: t.TypeAlias = "GatewayClient"
REST: t.TypeAlias = "RESTClient"


class Client(t.Generic[AppT]):
    """Singleton class for handling events."""

    def __init__(self, app: AppT) -> None:
        self._app = app

        self._handlers: dict[str, ItemHandler[te.Self, t.Any, t.Any, t.Any, t.Any, t.Any]] = {}
        """A mapping of custom_id to ItemHandler. This only contains handlers that are not bound to a message."""

        self._bound_handlers: dict[hikari.Snowflakeish, ItemHandler[te.Self, t.Any, t.Any, t.Any, t.Any, t.Any]] = {}
        """A mapping of message_id to ItemHandler. This contains handlers that are bound to a message or custom_id."""

    @property
    def app(self) -> AppT:
        """The currently running app instance that will be subscribed to the listener."""
        return self._app

    @property
    def rest(self) -> hikari.api.RESTClient:
        """The rest client instance."""
        return self._app.rest

    @property
    @abc.abstractmethod
    def is_rest(self) -> bool:
        """Whether the app is a rest client or a gateway client."""

    def _associate_message(self, message: hikari.Message, view: View[te.Self]) -> None:
        """Associate a message with a bound view."""
        view._message = message
        self._bound_handlers[message.id] = view

        for item in view.children:
            self._handlers.pop(item.custom_id, None)

    async def _handle_component_inter(self, interaction: hikari.ComponentInteraction) -> ViewResponseBuildersT | None:
        # Check bound views first
        if handler := self._bound_handlers.get(interaction.message.id):
            fut = await handler._invoke(interaction)
            return await fut if fut is not None else None

        # Check unbound or pending bound views
        elif handler := self._handlers.get(interaction.custom_id):
            # Bind pending bound views
            if isinstance(handler, View) and not handler.is_persistent:
                self._associate_message(interaction.message, handler)

            fut = await handler._invoke(interaction)
            return await fut if fut is not None else None

    async def _handle_modal_inter(self, interaction: hikari.ModalInteraction) -> ModalResponseBuildersT | None:
        if handler := self._handlers.get(interaction.custom_id):
            fut = await handler._invoke(interaction)
            return await fut if fut is not None else None

    def clear(self) -> None:
        """Stop all custom event listeners for events, this is called during miru.uninstall()."""
        self._bound_handlers.clear()
        self._handlers.clear()

    def add_handler(self, handler: ItemHandler[te.Self, t.Any, t.Any, t.Any, t.Any, t.Any]) -> None:
        """Add a handler to the event handler."""
        if isinstance(handler, View):
            if handler.is_bound and handler._message is not None:
                self._bound_handlers[handler._message.id] = handler
            else:
                for custom_id in (item.custom_id for item in handler.children):
                    self._handlers[custom_id] = handler
        elif isinstance(handler, Modal):
            self._handlers[handler.custom_id] = handler

    def remove_handler(self, handler: ItemHandler[te.Self, t.Any, t.Any, t.Any, t.Any, t.Any]) -> None:
        """Remove a handler from the event handler."""
        if isinstance(handler, View):
            if handler.is_bound and handler._message is not None:
                self._bound_handlers.pop(handler._message.id, None)
            else:
                for custom_id in (item.custom_id for item in handler.children):
                    self._handlers.pop(custom_id, None)
        elif isinstance(handler, Modal):
            self._handlers.pop(handler.custom_id, None)

    def get_view(self, message_id: hikari.Snowflake) -> View[te.Self] | None:
        """Get a bound view that is currently managed by this client."""
        handler = self._bound_handlers.get(message_id)
        if handler is None or not isinstance(handler, View):
            return None

        return handler

    def start_view(self, view: View[te.Self]) -> None:
        view._client_start_hook(self)

    def start_modal(self, modal: Modal[te.Self]) -> None:
        modal._client_start_hook(self)


class RESTClient(Client[hikari.RESTBot]):
    def __init__(self, app: hikari.RESTBot) -> None:
        super().__init__(app)
        self.app.set_listener(hikari.ModalInteraction, self._rest_handle_modal_inter)
        self.app.set_listener(hikari.ComponentInteraction, self._rest_handle_component_inter)

    async def _rest_handle_modal_inter(self, interaction: hikari.ModalInteraction) -> ModalResponseBuildersT:
        builder = await super()._handle_modal_inter(interaction)
        assert builder is not None
        return builder

    async def _rest_handle_component_inter(self, interaction: hikari.ComponentInteraction) -> ViewResponseBuildersT:
        builder = await super()._handle_component_inter(interaction)
        assert builder is not None
        return builder

    @property
    def is_rest(self) -> bool:
        return True


class GatewayClient(Client[hikari.GatewayBot]):
    def __init__(self, app: hikari.GatewayBot) -> None:
        super().__init__(app)
        self._app.subscribe(hikari.InteractionCreateEvent, self._handle_events)

    @property
    def is_rest(self) -> bool:
        return False

    async def _handle_events(self, event: hikari.InteractionCreateEvent) -> None:
        """Sort interaction create events and dispatch miru custom events."""
        assert self._app is not None

        if not isinstance(event.interaction, (hikari.ComponentInteraction, hikari.ModalInteraction)):
            return

        if isinstance(event.interaction, hikari.ModalInteraction):
            await self._handle_modal_inter(event.interaction)
        else:
            await self._handle_component_inter(event.interaction)


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
