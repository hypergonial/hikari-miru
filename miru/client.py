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
    """The base class for a miru client.

    It is responsible for handling component and modal interactions and dispatching them to the correct item handler.

    Parameters
    ----------
    app : AppT
        The currently running app instance that will be used to receive interactions.
    """

    def __init__(self, app: AppT) -> None:
        self._app = app

        self._handlers: dict[str, ItemHandler[te.Self, t.Any, t.Any, t.Any, t.Any, t.Any]] = {}
        """A mapping of custom_id to ItemHandler. This only contains handlers that are not bound to a message."""

        self._bound_handlers: dict[hikari.Snowflakeish, ItemHandler[te.Self, t.Any, t.Any, t.Any, t.Any, t.Any]] = {}
        """A mapping of message_id to ItemHandler. This contains handlers that are bound to a message."""

    @property
    def app(self) -> AppT:
        """The currently running app instance that will be subscribed to the listener."""
        return self._app

    @property
    def bot(self) -> AppT:
        """Alias for 'Client.app'. The currently running app instance that will be subscribed to the listener."""
        return self.app

    @property
    def rest(self) -> hikari.api.RESTClient:
        """The rest client instance of the underlying app."""
        return self._app.rest

    @property
    @abc.abstractmethod
    def is_rest(self) -> bool:
        """Whether the app is a rest client or a gateway client.

        This controls the client response flow, if True, `Client.handle_component_interaction` and `Client.handle_modal_interaction`
        will return interaction response builders to be sent back to Discord, otherwise they will return None.
        """

    def _associate_message(self, message: hikari.Message, view: View[te.Self]) -> None:
        """Associate a message with a bound view."""
        view._message = message
        view._message_id = message.id
        self._bound_handlers[message.id] = view

        for item in view.children:
            self._handlers.pop(item.custom_id, None)

    async def handle_component_interaction(
        self, interaction: hikari.ComponentInteraction
    ) -> ViewResponseBuildersT | None:
        """Handle a component interaction.

        Parameters
        ----------
        interaction : hikari.ComponentInteraction
            The interaction to handle.

        Returns
        -------
        ViewResponseBuildersT | None
            If using a REST client, the response builders to send back to discord.
        """
        # Check bound views first
        if handler := self._bound_handlers.get(interaction.message.id):
            fut = await handler._invoke(interaction)
            return await fut if fut is not None else None

        # Check unbound or pending bound views
        elif handler := self._handlers.get(interaction.custom_id):
            # Bind pending bound views
            if isinstance(handler, View) and handler.is_bound and handler._message_id is None:
                self._associate_message(interaction.message, handler)

            fut = await handler._invoke(interaction)
            return await fut if fut is not None else None

    async def handle_modal_interaction(self, interaction: hikari.ModalInteraction) -> ModalResponseBuildersT | None:
        """Handle a modal interaction.

        Parameters
        ----------
        interaction : hikari.ModalInteraction
            The interaction to handle.

        Returns
        -------
        ModalResponseBuildersT | None
            If using a REST client, the response builders to send back to discord.
        """
        if handler := self._handlers.get(interaction.custom_id):
            fut = await handler._invoke(interaction)
            return await fut if fut is not None else None

    def clear(self) -> None:
        """Stop all currently running views and modals."""
        self._bound_handlers.clear()
        self._handlers.clear()

    def _add_handler(self, handler: ItemHandler[te.Self, t.Any, t.Any, t.Any, t.Any, t.Any]) -> None:
        """Add a handler to this client handler."""
        if isinstance(handler, View):
            if handler.is_bound and handler._message_id is not None:
                self._bound_handlers[handler._message_id] = handler
            else:
                for custom_id in (item.custom_id for item in handler.children):
                    self._handlers[custom_id] = handler
        elif isinstance(handler, Modal):
            self._handlers[handler.custom_id] = handler

    def _remove_handler(self, handler: ItemHandler[te.Self, t.Any, t.Any, t.Any, t.Any, t.Any]) -> None:
        """Remove a handler from this client."""
        if isinstance(handler, View):
            if handler.is_bound and handler._message_id is not None:
                self._bound_handlers.pop(handler._message_id, None)
            else:
                for custom_id in (item.custom_id for item in handler.children):
                    self._handlers.pop(custom_id, None)
        elif isinstance(handler, Modal):
            self._handlers.pop(handler.custom_id, None)

    def get_bound_view(self, message: hikari.SnowflakeishOr[hikari.PartialMessage]) -> View[te.Self] | None:
        """Get a bound view that is currently managed by this client.

        Parameters
        ----------
        message : hikari.SnowflakeishOr[hikari.PartialMessage]
            The message object or ID of the message that the view is bound to.

        Returns
        -------
        View[te.Self] | None
            The view if found, otherwise None.
        """
        message_id = hikari.Snowflake(message)
        handler = self._bound_handlers.get(message_id)
        if handler is None or not isinstance(handler, View):
            return None

        return handler

    def get_unbound_view(self, custom_id: str) -> View[te.Self] | None:
        """Get a currently running view that is managed by this client.

        This will not return bound views.

        Parameters
        ----------
        custom_id : str
            The custom_id of one of the view's children.

        Returns
        -------
        View[te.Self] | None
            The view if found, otherwise None.
        """
        handler = self._handlers.get(custom_id)
        if handler is None or not isinstance(handler, View):
            return None

        return handler

    def get_modal(self, custom_id: str) -> Modal[te.Self] | None:
        """Get a currently running modal that is managed by this client.

        Parameters
        ----------
        custom_id : str
            The custom_id of the modal.

        Returns
        -------
        Modal[te.Self] | None
            The modal if found, otherwise None.
        """
        handler = self._handlers.get(custom_id)
        if handler is None or not isinstance(handler, Modal):
            return None

        return handler

    def start_view(
        self,
        view: View[te.Self],
        *,
        bind_to: hikari.UndefinedNoneOr[hikari.SnowflakeishOr[hikari.PartialMessage]] = hikari.UNDEFINED,
    ) -> None:
        """Add a view to this client and start it.

        Parameters
        ----------
        view : View[te.Self]
            The view to start.
        bind_to : hikari.UndefinedNoneOr[hikari.SnowflakeishOr[hikari.PartialMessage]]
            The message to bind the view to. If set to `None`, the view will be unbound.
            If left as `UNDEFINED` (the default), the view will automatically be bound
            to the first message it receives an interaction from.

        Raises
        ------
        ValueError
            If the view is not persistent and `bind_to` is set to None.

        !!! note
            A view can only be unbound if it is persistent, meaning that it has a timeout of None and all it's items have
            explicitly defined custom_ids. If a view is not persistent, it must be bound to a message.
        """
        if bind_to is None and not view.is_persistent:
            raise ValueError("Cannot make a view unbound that is not persistent.")
        view._is_bound = bind_to is not None

        if isinstance(bind_to, hikari.Snowflakeish):
            view._message_id = hikari.Snowflake(bind_to)

        view._client_start_hook(self)

    def start_modal(self, modal: Modal[te.Self]) -> None:
        """Add a modal to this client and start it.

        Parameters
        ----------
        modal : Modal[te.Self]
            The modal to start.
        """
        modal._client_start_hook(self)


class RESTClient(Client[hikari.RESTBotAware]):
    """The default REST client implementation for miru.

    Parameters
    ----------
    app : hikari.RESTBotAware
        The currently running app instance that will be used to receive interactions.
    """

    def __init__(self, app: hikari.RESTBotAware) -> None:
        super().__init__(app)
        self.app.interaction_server.set_listener(hikari.ModalInteraction, self._rest_handle_modal_inter)
        self.app.interaction_server.set_listener(hikari.ComponentInteraction, self._rest_handle_component_inter)

    @property
    def is_rest(self) -> bool:
        return True

    async def _rest_handle_modal_inter(self, interaction: hikari.ModalInteraction) -> ModalResponseBuildersT:
        builder = await self.handle_modal_interaction(interaction)
        assert builder is not None
        return builder

    async def _rest_handle_component_inter(self, interaction: hikari.ComponentInteraction) -> ViewResponseBuildersT:
        builder = await self.handle_component_interaction(interaction)
        assert builder is not None
        return builder


class GatewayClient(Client[hikari.GatewayBotAware]):
    """The default gateway client implementation for miru.

    Parameters
    ----------
    app : hikari.GatewayBotAware
        The currently running app instance that will be used to receive interactions.
    stop_bound_on_delete : bool
        Whether to automatically stop bound views when the message it is bound to is deleted.
    """

    def __init__(self, app: hikari.GatewayBotAware, *, stop_bound_on_delete: bool = True) -> None:
        super().__init__(app)
        self._app.event_manager.subscribe(hikari.InteractionCreateEvent, self._handle_events)
        if stop_bound_on_delete:
            self._app.event_manager.subscribe(hikari.MessageDeleteEvent, self._remove_bound_view)

    @property
    def is_rest(self) -> bool:
        return False

    @property
    def cache(self) -> hikari.api.Cache:
        """The cache instance of the underlying app."""
        return self._app.cache

    async def _handle_events(self, event: hikari.InteractionCreateEvent) -> None:
        """Sort interaction create events and dispatch miru custom events."""
        assert self._app is not None

        if not isinstance(event.interaction, (hikari.ComponentInteraction, hikari.ModalInteraction)):
            return

        if isinstance(event.interaction, hikari.ModalInteraction):
            await self.handle_modal_interaction(event.interaction)
        else:
            await self.handle_component_interaction(event.interaction)

    async def _remove_bound_view(self, event: hikari.MessageDeleteEvent) -> None:
        """Remove a bound view if the message it is bound to is deleted."""
        if handler := self._bound_handlers.pop(event.message_id, None):
            handler.stop()


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
