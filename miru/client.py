from __future__ import annotations

import asyncio
import functools
import inspect
import logging
import typing as t

import alluka
import hikari

from miru.exceptions import NoResponseIssuedError
from miru.modal import Modal
from miru.view import View

if t.TYPE_CHECKING:
    import arc
    import tanjun
    import typing_extensions as te

    from miru.abc.item_handler import ItemHandler
    from miru.internal.types import (
        ModalResponseBuildersT,
        ResponseBuildersT,
        UnhandledCompInterHookT,
        UnhandledModalInterHookT,
    )

__all__ = ("Client",)


logger = logging.getLogger(__name__)

T = t.TypeVar("T")
P = t.ParamSpec("P")


@t.runtime_checkable
class GatewayBotLike(hikari.RESTAware, hikari.EventManagerAware, t.Protocol):
    """A type that implements both `RESTAware` and `EventManagerAware`."""


class Client:
    """The miru client.

    It is responsible for handling component and modal interactions and dispatching them to the correct item handler.

    Parameters
    ----------
    app : GatewayBotLike | hikari.InteractionServerAware
        The currently running app instance that will be used to receive interactions.
    ignore_unknown_interactions : bool
        Whether to ignore unknown interactions.
        If True, unknown interactions will be ignored and no warnings will be logged.
    stop_bound_on_delete : bool
        Whether to automatically stop bound views when the message it is bound to is deleted. This only applies to
        Gateway bots. When an app without EventManagerAware is used, this will be ignored.
    injector : alluka.Client | None
        The injector to use for dependency injection. If None, a new injector will be created.
    """

    __slots__: t.Sequence[str] = (
        "_app",
        "_ignore_unknown_interactions",
        "_stop_bound_on_delete",
        "_interaction_server",
        "_event_manager",
        "_cache",
        "_injector",
        "_unbound_views",
        "_bound_views",
        "_modals",
        "_is_rest",
        "_unhandled_comp_hook",
        "_unhandled_modal_hook",
    )

    def __init__(
        self,
        app: GatewayBotLike | hikari.InteractionServerAware,
        *,
        ignore_unknown_interactions: bool = False,
        stop_bound_on_delete: bool = True,
        injector: alluka.abc.Client | None = None,
    ) -> None:
        self._app = app
        self._ignore_unknown_interactions = ignore_unknown_interactions
        self._stop_bound_on_delete = stop_bound_on_delete
        self._interaction_server: hikari.api.InteractionServer | None = None
        self._event_manager: hikari.api.EventManager | None = None
        self._cache: hikari.api.Cache | None = None
        self._injector: alluka.abc.Client = injector or alluka.Client()
        self._unhandled_comp_hook: UnhandledCompInterHookT | None = None
        self._unhandled_modal_hook: UnhandledModalInterHookT | None = None

        if isinstance(app, hikari.InteractionServerAware):
            self._is_rest = True
            self._interaction_server = app.interaction_server
            self._interaction_server.set_listener(hikari.ModalInteraction, self._rest_handle_modal_inter)
            self._interaction_server.set_listener(hikari.ComponentInteraction, self._rest_handle_component_inter)
        elif isinstance(app, GatewayBotLike):  # pyright: ignore reportUnnecessaryIsInstance
            self._is_rest = False
            self._event_manager = app.event_manager
            self._event_manager.subscribe(hikari.InteractionCreateEvent, self._handle_events)
            if stop_bound_on_delete:
                self._event_manager.subscribe(hikari.MessageDeleteEvent, self._remove_bound_view)
        else:
            raise TypeError("App must be either InteractionServerAware or GatewayBotLike.")

        if isinstance(app, hikari.CacheAware):
            self._cache = app.cache

        self._injector.set_type_dependency(Client, self)

        if type(self) is not Client:
            self._injector.set_type_dependency(type(self), self)

        self._unbound_views: dict[str, View] = {}
        """A mapping of custom_id to View. This only contains views that are not bound to a message."""

        self._bound_views: dict[hikari.Snowflakeish, View] = {}
        """A mapping of message_id to View. This contains views that are bound to a message."""

        self._modals: dict[str, Modal] = {}
        """A mapping of custom_id to Modal."""

    @classmethod
    def from_arc(
        cls,
        client: arc.abc.Client[t.Any],
        *,
        ignore_unknown_interactions: bool = False,
        stop_bound_on_delete: bool = True,
    ) -> te.Self:
        """Create a new client from an arc client, using it's dependency injector.
        This can be used to share dependencies between the arc client and the miru client.

        Parameters
        ----------
        client : arc.abc.Client[t.Any]
            The arc client to create the miru client from.
        ignore_unknown_interactions : bool
            Whether to ignore unknown interactions.
            If True, unknown interactions will be ignored and no warnings will be logged.
        stop_bound_on_delete : bool
            Whether to automatically stop bound views when the message it is bound to is deleted. This only applies to
            Gateway bots. When an app without EventManagerAware is used, this will be ignored.

        Returns
        -------
        Client
            The created client.
        """
        return cls(
            client.app,
            ignore_unknown_interactions=ignore_unknown_interactions,
            stop_bound_on_delete=stop_bound_on_delete,
            injector=client.injector,
        )

    @classmethod
    def from_tanjun(
        cls, client: tanjun.abc.Client, *, ignore_unknown_interactions: bool = False, stop_bound_on_delete: bool = True
    ) -> te.Self:
        """Create a new client from a Tanjun client, using it's dependency injector.
        This can be used to share dependencies between the Tanjun client and the miru client.

        !!! note
            This convenience method only works if the Tanjun client was created with a bot object, not constructed manually.

        Parameters
        ----------
        client : tanjun.Client
            The Tanjun client to create the miru client from.
        ignore_unknown_interactions : bool
            Whether to ignore unknown interactions.
            If True, unknown interactions will be ignored and no warnings will be logged.
        stop_bound_on_delete : bool
            Whether to automatically stop bound views when the message it is bound to is deleted. This only applies to
            Gateway bots. When an app without EventManagerAware is used, this will be ignored.

        Returns
        -------
        Client
            The created client.

        Raises
        ------
        RuntimeError
            If no `RESTAware` dependency was declared in the Tanjun client injector.
            Tanjun automatically sets this if the client was created with a bot object.
        RuntimeError
            If the located `RESTAware` dependency is not a valid application for miru.
            A valid application is either a `GatewayBotLike` or `InteractionServerAware`.
        """
        app = client.get_type_dependency(hikari.RESTAware)

        if isinstance(app, alluka.abc.Undefined):
            raise RuntimeError("Could not resolve a RESTAware dependency from Tanjun client injector.")

        if not isinstance(app, (GatewayBotLike, hikari.InteractionServerAware)):
            raise RuntimeError("Could not resolve a valid application dependency from Tanjun client injector.")

        return cls(
            app,
            ignore_unknown_interactions=ignore_unknown_interactions,
            stop_bound_on_delete=stop_bound_on_delete,
            injector=client.injector,
        )

    @property
    def app(self) -> hikari.RESTAware:
        """The currently running app instance."""
        return self._app

    @property
    def bot(self) -> hikari.RESTAware:
        """Alias for 'Client.app'. The currently running app instance."""
        return self.app

    @property
    def rest(self) -> hikari.api.RESTClient:
        """The rest client instance of the underlying app."""
        return self._app.rest

    @property
    def event_manager(self) -> hikari.api.EventManager:
        """The event manager instance of the underlying app.

        !!! warning
            Accessing this property will raise a `RuntimeError` if the underlying app is not `EventManagerAware`.

        """
        if self._event_manager is None:
            raise RuntimeError("Cannot access event manager when using a REST app.")

        return self._event_manager

    @property
    def cache(self) -> hikari.api.Cache:
        """The cache instance of the underlying app.

        !!! warning
            Accessing this property will raise a `RuntimeError` if the underlying app is not `CacheAware`.
        """
        if self._cache is None:
            raise RuntimeError("Cannot access cache when using app is not CacheAware.")

        return self._cache

    @property
    def interaction_server(self) -> hikari.api.InteractionServer:
        """The interaction server instance of the underlying app.

        !!! warning
            Accessing this property will raise a `RuntimeError` if the underlying app is not `InteractionServerAware`.
        """
        if self._interaction_server is None:
            raise RuntimeError("Cannot access interaction server when using a Gateway app.")

        return self._interaction_server

    @property
    def is_rest(self) -> bool:
        """Whether the app is a rest client or a gateway client.

        This controls the client response flow, if True, `Client.handle_component_interaction` and `Client.handle_modal_interaction`
        will return interaction response builders to be sent back to Discord, otherwise they will return None.
        """
        return self._is_rest

    @property
    def ignore_unknown_interactions(self) -> bool:
        """Whether to ignore unknown interactions.

        If True, unknown interactions will be ignored and no warnings will be logged.
        """
        return self._ignore_unknown_interactions

    @property
    def injector(self) -> alluka.abc.Client:
        """The injector used for dependency injection."""
        return self._injector

    def _associate_message(self, message: hikari.Message, view: View) -> None:
        """Associate a message with a bound view."""
        view._message = message
        view._message_id = message.id
        self._bound_views[message.id] = view

        for item in view.children:
            self._unbound_views.pop(item.custom_id, None)

    async def _rest_handle_modal_inter(self, interaction: hikari.ModalInteraction) -> ModalResponseBuildersT:
        """Handle a modal interaction.

        Used only under REST flow.
        """
        try:
            builder = await asyncio.wait_for(self.handle_modal_interaction(interaction), timeout=3.0)
        except asyncio.TimeoutError:
            raise NoResponseIssuedError(f"Timed out waiting for response from modal {interaction.custom_id}.")
        if builder is None:
            raise NoResponseIssuedError(f"No response was issued to modal {interaction.custom_id}.")

        return builder

    async def _rest_handle_component_inter(self, interaction: hikari.ComponentInteraction) -> ResponseBuildersT:
        """Handle a component interaction.

        Used only under REST flow.
        """
        try:
            builder = await asyncio.wait_for(self.handle_component_interaction(interaction), timeout=3.0)
        except asyncio.TimeoutError:
            raise NoResponseIssuedError(f"Timed out waiting for response from component {interaction.custom_id}.")
        if builder is None:
            raise NoResponseIssuedError(f"No response was issued to component {interaction.custom_id}.")

        return builder

    async def _handle_events(self, event: hikari.InteractionCreateEvent) -> None:
        """Sort interaction create events and dispatch miru custom events.

        Used only under Gateway flow.
        """
        assert self._app is not None

        if not isinstance(event.interaction, (hikari.ComponentInteraction, hikari.ModalInteraction)):
            return

        if isinstance(event.interaction, hikari.ModalInteraction):
            await self.handle_modal_interaction(event.interaction)
        else:
            await self.handle_component_interaction(event.interaction)

    async def _remove_bound_view(self, event: hikari.MessageDeleteEvent) -> None:
        """Remove a bound view if the message it is bound to is deleted and stop_bound_on_delete is True.

        Used only under Gateway flow.
        """
        if handler := self._bound_views.pop(event.message_id, None):
            handler.stop()

    def _add_handler(self, handler: ItemHandler[t.Any, t.Any, t.Any, t.Any, t.Any]) -> None:
        """Add a handler to this client handler."""
        if isinstance(handler, View):
            if handler.is_bound and handler._message_id is not None:
                self._bound_views[handler._message_id] = handler
            else:
                for custom_id in (item.custom_id for item in handler.children):
                    self._unbound_views[custom_id] = handler
        elif isinstance(handler, Modal):
            self._modals[handler.custom_id] = handler

    def _remove_handler(self, handler: ItemHandler[t.Any, t.Any, t.Any, t.Any, t.Any]) -> None:
        """Remove a handler from this client."""
        if isinstance(handler, View):
            if handler.is_bound and handler._message_id is not None:
                self._bound_views.pop(handler._message_id, None)
            else:
                for custom_id in (item.custom_id for item in handler.children):
                    self._unbound_views.pop(custom_id, None)
        elif isinstance(handler, Modal):
            self._unbound_views.pop(handler.custom_id, None)

    async def handle_component_interaction(self, interaction: hikari.ComponentInteraction) -> ResponseBuildersT | None:
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
        if view := self._bound_views.get(interaction.message.id):
            fut = await view._invoke(interaction)

        # Check unbound or pending bound views
        elif view := self._unbound_views.get(interaction.custom_id):
            # Bind pending bound views
            if view.is_bound and view._message_id is None:
                self._associate_message(interaction.message, view)

            fut = await view._invoke(interaction)

        else:
            if self._unhandled_comp_hook is not None:
                return await self._unhandled_comp_hook(interaction)

            elif not self._ignore_unknown_interactions:
                logger.warning(
                    f"Unknown component interaction received for component: '{interaction.custom_id}'. Did you forget to start a view?"
                    "\nYou can disable this warning by setting 'ignore_unknown_interactions' to True in the client constructor, or"
                    " by setting a unhandled component interaction hook."
                )
            return

        if fut is None:
            return

        try:
            return await asyncio.wait_for(fut, timeout=3.0)
        except asyncio.TimeoutError:
            logger.warning(
                f"Timed out waiting for response from component interaction: '{interaction.custom_id}'"
                f" on message: '{interaction.message.id}'. Did you forget to respond?"
            )

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
        if modal := self._modals.get(interaction.custom_id):
            fut = await modal._invoke(interaction)
        else:
            if self._unhandled_modal_hook is not None:
                return await self._unhandled_modal_hook(interaction)

            elif not self._ignore_unknown_interactions:
                logger.warning(
                    f"Unknown modal interaction received for modal: '{interaction.custom_id}'. Did you forget to start a modal?"
                    "\nYou can disable this warning by setting 'ignore_unknown_interactions' to True in the client constructor, or"
                    " by setting a unhandled modal interaction hook."
                )
            return

        if fut is None:
            return

        try:
            return await asyncio.wait_for(fut, timeout=3.0)
        except asyncio.TimeoutError:
            logger.warning(
                f"Timed out waiting for response from modal interaction: '{interaction.custom_id}'. Did you forget to respond?"
            )

    def clear(self) -> None:
        """Stop all currently running views and modals."""
        self._bound_views.clear()
        self._unbound_views.clear()

    def get_bound_view(self, message: hikari.SnowflakeishOr[hikari.PartialMessage]) -> View | None:
        """Get a bound view that is currently managed by this client.

        Parameters
        ----------
        message : hikari.SnowflakeishOr[hikari.PartialMessage]
            The message object or ID of the message that the view is bound to.

        Returns
        -------
        View | None
            The view if found, otherwise None.
        """
        message_id = hikari.Snowflake(message)
        view = self._bound_views.get(message_id)
        if view is None:
            return None

        return view

    def get_unbound_view(self, custom_id: str) -> View | None:
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
        view = self._unbound_views.get(custom_id)
        if view is None:
            return None

        return view

    def get_modal(self, custom_id: str) -> Modal | None:
        """Get a currently running modal that is managed by this client.

        Parameters
        ----------
        custom_id : str
            The custom_id of the modal.

        Returns
        -------
        Modal | None
            The modal if found, otherwise None.
        """
        handler = self._unbound_views.get(custom_id)
        if handler is None or not isinstance(handler, Modal):
            return None

        return handler

    @t.overload
    def set_unhandled_component_interaction_hook(self, hook: UnhandledCompInterHookT) -> te.Self:
        ...

    @t.overload
    def set_unhandled_component_interaction_hook(self) -> t.Callable[[UnhandledCompInterHookT], te.Self]:
        ...

    def set_unhandled_component_interaction_hook(
        self, hook: UnhandledCompInterHookT | None = None
    ) -> te.Self | t.Callable[[UnhandledCompInterHookT], te.Self]:
        """Decorator to set the callback to be called for unhandled component interactions.

        This will be called when a component interaction is received that is not
        handled by any of the currently running views.

        Parameters
        ----------
        hook : UnhandledCompInterHookT
            The function to set as the hook.

        Returns
        -------
        te.Self
            The client for chaining calls.

        Examples
        --------
        ```py
        @client.set_unhandled_component_interaction_hook
        async def unhandled_comp_hook(inter: hikari.ComponentInteraction) -> None:
            await inter.create_initial_response("❌ Something went wrong!")
        ```

        Or, as a function:

        ```py
        client.set_unhandled_component_interaction_hook(unhandled_comp_hook)
        ```
        """

        def decorator(hook: UnhandledCompInterHookT) -> te.Self:
            self._unhandled_comp_hook = hook
            return self

        if hook is not None:
            return decorator(hook)

        return decorator

    @t.overload
    def set_unhandled_modal_interaction_hook(self, hook: UnhandledModalInterHookT) -> te.Self:
        ...

    @t.overload
    def set_unhandled_modal_interaction_hook(self) -> t.Callable[[UnhandledModalInterHookT], te.Self]:
        ...

    def set_unhandled_modal_interaction_hook(
        self, hook: UnhandledModalInterHookT | None = None
    ) -> te.Self | t.Callable[[UnhandledModalInterHookT], te.Self]:
        """Decorator to set the callback to be called for unhandled modal interactions.

        This will be called when a modal interaction is received that is not
        handled by any of the currently running modals.

        Parameters
        ----------
        hook : UnhandledModalInterHookT
            The function to set as the hook.

        Returns
        -------
        te.Self
            The client for chaining calls.

        Examples
        --------
        ```py
        @client.set_unhandled_modal_interaction_hook
        async def unhandled_modal_hook(inter: hikari.ModalInteraction) -> None:
            await inter.create_initial_response("❌ Something went wrong!")
        ```

        Or, as a function:

        ```py
        client.set_unhandled_modal_interaction_hook(unhandled_modal_hook)
        ```
        """

        def decorator(hook: UnhandledModalInterHookT) -> te.Self:
            self._unhandled_modal_hook = hook
            return self

        if hook is not None:
            return decorator(hook)

        return decorator

    def start_view(
        self,
        view: View,
        *,
        bind_to: hikari.UndefinedNoneOr[hikari.SnowflakeishOr[hikari.PartialMessage]] = hikari.UNDEFINED,
    ) -> None:
        """Add a view to this client and start it.

        Parameters
        ----------
        view : View
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

    def start_modal(self, modal: Modal) -> None:
        """Add a modal to this client and start it.

        Parameters
        ----------
        modal : Modal
            The modal to start.
        """
        modal._client_start_hook(self)

    @t.overload
    def get_type_dependency(self, type_: type[T]) -> T:
        ...

    @t.overload
    def get_type_dependency(self, type_: type[T], *, default: T) -> T:
        ...

    def get_type_dependency(self, type_: type[T], *, default: T | None = None) -> T:
        """Get a type dependency for this client.

        Parameters
        ----------
        type_ : type[T]
            The type of the dependency.
        default : T | None
            The default value to return if the dependency does not exist.
            If not specified, a `KeyError` will be raised.

        Returns
        -------
        T
            The instance of the dependency, or the default value if it does not exist.

        Raises
        ------
        KeyError
            If the dependency does not exist and no default was specified.
        """
        if default is None:
            value = self._injector.get_type_dependency(type_)
            if isinstance(value, alluka.abc.Undefined):
                raise KeyError(f"Could not resolve dependency of type {type_}.")
            return value
        else:
            return self._injector.get_type_dependency(type_, default=default)

    def set_type_dependency(self, type_: type[T], instance: T) -> te.Self:
        """Set a type dependency for this client. This can then be injected into miru callbacks.

        Parameters
        ----------
        type_ : type[T]
            The type of the dependency.
        instance : T
            The instance of the dependency.

        Returns
        -------
        te.Self
            The client for chaining calls.

        Examples
        --------
        ```py
        class Counter:
            def __init__(self, value: int = 0) -> None:
                self.value = value

        client.set_type_dependency(Counter, Counter(0))


        class SomeView(miru.View):
            @miru.button(label="Counter!", style=hikari.ButtonStyle.PRIMARY)
            @client.inject_dependencies
            async def counter_button(
                self,
                ctx: miru.ViewContext,
                button: miru.Button,
                counter: Counter = miru.inject(),
            ) -> None:
                counter.value += 1
                await ctx.respond(f"Counter is {counter.value}")
        ```

        See Also
        --------
        - [`Client.get_type_dependency`][miru.client.Client.get_type_dependency]
            A method to get dependencies for the client.

        - [`Client.inject_dependencies`][miru.client.Client.inject_dependencies]
            A decorator to inject dependencies into arbitrary functions.
        """
        self._injector.set_type_dependency(type_, instance)
        return self

    @t.overload
    def inject_dependencies(self, func: t.Callable[P, T]) -> t.Callable[P, T]:
        ...

    @t.overload
    def inject_dependencies(self) -> t.Callable[[t.Callable[P, T]], t.Callable[P, T]]:
        ...

    def inject_dependencies(
        self, func: t.Callable[P, T] | None = None
    ) -> t.Callable[P, T] | t.Callable[[t.Callable[P, T]], t.Callable[P, T]]:
        """Decorator to inject dependencies into the decorated function.

        This should be the first (the one at the bottom) decorator of the given function.

        Examples
        --------
        ```py
        class Counter:
            def __init__(self, value: int = 0) -> None:
                self.value = value

        client.set_type_dependency(Counter, Counter(0))


        class SomeView(miru.View):
            @miru.button(label="Counter!", style=hikari.ButtonStyle.PRIMARY)
            @client.inject_dependencies
            async def counter_button(
                self,
                ctx: miru.ViewContext,
                button: miru.Button,
                counter: Counter = miru.inject(),
            ) -> None:
                counter.value += 1
                await ctx.respond(f"Counter is {counter.value}")
        ```

        See Also
        --------
        - [`Client.set_type_dependency`][miru.client.Client.set_type_dependency]
            A method to set dependencies for the client.
        """

        def decorator(func: t.Callable[P, T]) -> t.Callable[P, T]:
            if inspect.iscoroutinefunction(func):

                @functools.wraps(func)
                async def decorator_async(*args: P.args, **kwargs: P.kwargs) -> T:
                    return await self.injector.call_with_async_di(func, *args, **kwargs)

                return decorator_async  # pyright: ignore reportGeneralTypeIssues
            else:

                @functools.wraps(func)
                def decorator_inner(*args: P.args, **kwargs: P.kwargs) -> T:
                    return self.injector.call_with_di(func, *args, **kwargs)

                return decorator_inner

        if func is not None:
            return decorator(func)

        return decorator


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
