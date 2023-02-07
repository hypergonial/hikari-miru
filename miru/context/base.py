from __future__ import annotations

import abc
import asyncio
import datetime
import logging
import typing as t

import hikari
from hikari.snowflakes import Snowflake

from miru.exceptions import BootstrapFailureError

from ..abc.item_handler import ItemHandler
from ..traits import MiruAware

InteractionT = t.TypeVar("InteractionT", "hikari.ComponentInteraction", "hikari.ModalInteraction")

__all__ = ("Context", "InteractionResponse")

logger = logging.getLogger("__name__")


class InteractionResponse:
    """
    Represents a response to an interaction, allows for standardized handling of responses.
    This class is not meant to be directly instantiated, and is instead returned by :obj:`miru.context.Context`.
    """

    __slots__ = ("_context", "_message", "_delete_after_task")

    def __init__(self, context: Context[InteractionT], message: t.Optional[hikari.Message] = None) -> None:
        self._context: Context[t.Any] = context  # Before you ask why it is Any, because mypy is dumb
        self._message: t.Optional[hikari.Message] = message
        self._delete_after_task: t.Optional[asyncio.Task[None]] = None

    def __await__(self) -> t.Generator[t.Any, None, hikari.Message]:
        return self.retrieve_message().__await__()

    async def _do_delete_after(self, delay: float) -> None:
        """Delete the response after the specified delay.

        This should not be called manually,
        and instead should be triggered by the ``delete_after`` method of this class.
        """
        await asyncio.sleep(delay)
        await self.delete()

    def delete_after(self, delay: t.Union[int, float, datetime.timedelta]) -> None:
        """Delete the response after the specified delay.

        Parameters
        ----------
        delay : Union[int, float, datetime.timedelta]
            The delay after which the response should be deleted.
        """
        if self._delete_after_task is not None:
            raise RuntimeError("A delete_after task is already running.")

        if isinstance(delay, datetime.timedelta):
            delay = delay.total_seconds()
        self._delete_after_task = asyncio.create_task(self._do_delete_after(delay))

    async def retrieve_message(self) -> hikari.Message:
        """Get or fetch the message created by this response.
        Initial responses need to be fetched, while followups will be provided directly.

        .. note::
            The object itself can also be awaited directly, which in turn calls this method,
            producing the same results.

        Returns
        -------
        hikari.Message
            The message created by this response.
        """
        if self._message:
            return self._message

        assert isinstance(self._context.interaction, (hikari.ComponentInteraction, hikari.ModalInteraction))
        return await self._context.interaction.fetch_initial_response()

    async def delete(self) -> None:
        """Delete the response issued to the interaction this object represents."""

        if self._message:
            await self._context.interaction.delete_message(self._message)

        await self._context.interaction.delete_initial_response()

    async def edit(
        self,
        content: hikari.UndefinedOr[t.Any] = hikari.UNDEFINED,
        *,
        component: hikari.UndefinedOr[hikari.api.ComponentBuilder] = hikari.UNDEFINED,
        components: hikari.UndefinedOr[t.Sequence[hikari.api.ComponentBuilder]] = hikari.UNDEFINED,
        attachment: hikari.UndefinedOr[hikari.Resourceish] = hikari.UNDEFINED,
        attachments: hikari.UndefinedOr[t.Sequence[hikari.Resourceish]] = hikari.UNDEFINED,
        embed: hikari.UndefinedOr[hikari.Embed] = hikari.UNDEFINED,
        embeds: hikari.UndefinedOr[t.Sequence[hikari.Embed]] = hikari.UNDEFINED,
        mentions_everyone: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        user_mentions: hikari.UndefinedOr[
            t.Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]
        ] = hikari.UNDEFINED,
        role_mentions: hikari.UndefinedOr[
            t.Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]
        ] = hikari.UNDEFINED,
    ) -> InteractionResponse:
        """A short-hand method to edit the message belonging to this response.

        Parameters
        ----------
        content : undefined.UndefinedOr[t.Any], optional
            The content of the message. Anything passed here will be cast to str.
        attachment : undefined.UndefinedOr[hikari.Resourceish], optional
            An attachment to add to this message.
        attachments : undefined.UndefinedOr[t.Sequence[hikari.Resourceish]], optional
            A sequence of attachments to add to this message.
        component : undefined.UndefinedOr[hikari.api.special_endpoints.ComponentBuilder], optional
            A component to add to this message.
        components : undefined.UndefinedOr[t.Sequence[hikari.api.special_endpoints.ComponentBuilder]], optional
            A sequence of components to add to this message.
        embed : undefined.UndefinedOr[hikari.Embed], optional
            An embed to add to this message.
        embeds : undefined.UndefinedOr[t.Sequence[hikari.Embed]], optional
            A sequence of embeds to add to this message.
        mentions_everyone : undefined.UndefinedOr[bool], optional
            If True, mentioning @everyone will be allowed.
        user_mentions : undefined.UndefinedOr[t.Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]], optional
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : undefined.UndefinedOr[t.Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]], optional
            The set of allowed role mentions in this message. Set to True to allow all.

        Returns
        -------
        InteractionResponse
            A proxy object representing the response to the interaction.
        """
        if self._message:
            message = await self._context.interaction.edit_message(
                self._message,
                content,
                component=component,
                components=components,
                attachment=attachment,
                attachments=attachments,
                embed=embed,
                embeds=embeds,
                mentions_everyone=mentions_everyone,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
            )
            return self._context._create_response(message)

        message = await self._context.interaction.edit_initial_response(
            content,
            component=component,
            components=components,
            attachment=attachment,
            attachments=attachments,
            embed=embed,
            embeds=embeds,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )
        return self._context._create_response()


class Context(abc.ABC, t.Generic[InteractionT]):
    """An abstract base class for context
    objects that proxying a Discord interaction."""

    __slots__ = ("_interaction", "_responses", "_issued_response")

    def __init__(self, interaction: InteractionT) -> None:
        self._interaction: InteractionT = interaction
        self._responses: t.MutableSequence[InteractionResponse] = []
        self._issued_response: bool = False

    @property
    def interaction(self) -> InteractionT:
        """The underlying interaction object."""
        return self._interaction

    @property
    def custom_id(self) -> str:
        """The developer provided unique identifier for the interaction this context is proxying."""
        return self._interaction.custom_id

    @property
    def responses(self) -> t.Sequence[InteractionResponse]:
        """A list of all responses issued to the interaction this context is proxying."""
        return self._responses

    @property
    def app(self) -> MiruAware:
        """The application that loaded miru."""
        if not ItemHandler._app:
            raise BootstrapFailureError(f"miru was not loaded, {type(self).__name__} has no property app.")

        return ItemHandler._app

    @property
    def bot(self) -> MiruAware:
        """The application that loaded miru."""
        return self.app

    @property
    def user(self) -> hikari.User:
        """The user who triggered this interaction."""
        return self._interaction.user

    @property
    def author(self) -> hikari.User:
        """Alias for Context.user"""
        return self.user

    @property
    def member(self) -> t.Optional[hikari.InteractionMember]:
        """The member who triggered this interaction. Will be None in DMs."""
        return self._interaction.member

    @property
    def locale(self) -> t.Union[str, hikari.Locale]:
        """The locale of this context."""
        return self._interaction.locale

    @property
    def guild_locale(self) -> t.Optional[t.Union[str, hikari.Locale]]:
        """
        The guild locale of this context, if in a guild.
        This will default to `en-US` if not a community guild.
        """
        return self._interaction.guild_locale

    @property
    def app_permissions(self) -> t.Optional[hikari.Permissions]:
        """The permissions of the user who triggered the interaction. Will be None in DMs."""
        return self._interaction.app_permissions

    @property
    def channel_id(self) -> Snowflake:
        """The ID of the channel the context represents."""
        return self._interaction.channel_id

    @property
    def guild_id(self) -> t.Optional[Snowflake]:
        """The ID of the guild the context represents. Will be None in DMs."""
        return self._interaction.guild_id

    def _create_response(self, message: t.Optional[hikari.Message] = None) -> InteractionResponse:
        """Create a new response and add it to the list of tracked responses."""
        response = InteractionResponse(self, message)
        self._responses.append(response)
        return response

    def get_guild(self) -> t.Optional[hikari.GatewayGuild]:
        """Gets the guild this context represents, if any. Requires application cache."""
        return self._interaction.get_guild()

    def get_channel(self) -> t.Optional[hikari.TextableGuildChannel]:
        """Gets the channel this context represents, None if in a DM. Requires application cache."""
        return self._interaction.get_channel()

    async def get_last_response(self) -> InteractionResponse:
        """Get the last response issued to the interaction this context is proxying.

        Returns
        -------
        InteractionResponse
            The response object.

        Raises
        ------
        RuntimeError
            The interaction was not yet responded to.
        """
        if self._responses:
            return self._responses[-1]
        raise RuntimeError("This interaction was not yet issued a response.")

    async def respond(
        self,
        content: hikari.UndefinedOr[t.Any] = hikari.UNDEFINED,
        *,
        flags: t.Union[int, hikari.MessageFlag, hikari.UndefinedType] = hikari.UNDEFINED,
        tts: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        component: hikari.UndefinedOr[hikari.api.ComponentBuilder] = hikari.UNDEFINED,
        components: hikari.UndefinedOr[t.Sequence[hikari.api.ComponentBuilder]] = hikari.UNDEFINED,
        attachment: hikari.UndefinedOr[hikari.Resourceish] = hikari.UNDEFINED,
        attachments: hikari.UndefinedOr[t.Sequence[hikari.Resourceish]] = hikari.UNDEFINED,
        embed: hikari.UndefinedOr[hikari.Embed] = hikari.UNDEFINED,
        embeds: hikari.UndefinedOr[t.Sequence[hikari.Embed]] = hikari.UNDEFINED,
        mentions_everyone: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        user_mentions: hikari.UndefinedOr[
            t.Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]
        ] = hikari.UNDEFINED,
        role_mentions: hikari.UndefinedOr[
            t.Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]
        ] = hikari.UNDEFINED,
        delete_after: hikari.UndefinedOr[t.Union[float, int, datetime.timedelta]] = hikari.UNDEFINED,
    ) -> InteractionResponse:
        """Short-hand method to create a new message response via the interaction this context represents.

        Parameters
        ----------
        content : undefined.UndefinedOr[t.Any], optional
            The content of the message. Anything passed here will be cast to str.
        tts : undefined.UndefinedOr[bool], optional
            If the message should be tts or not.
        attachment : undefined.UndefinedOr[hikari.Resourceish], optional
            An attachment to add to this message.
        attachments : undefined.UndefinedOr[t.Sequence[hikari.Resourceish]], optional
            A sequence of attachments to add to this message.
        component : undefined.UndefinedOr[hikari.api.special_endpoints.ComponentBuilder], optional
            A component to add to this message.
        components : undefined.UndefinedOr[t.Sequence[hikari.api.special_endpoints.ComponentBuilder]], optional
            A sequence of components to add to this message.
        embed : undefined.UndefinedOr[hikari.Embed], optional
            An embed to add to this message.
        embeds : undefined.UndefinedOr[t.Sequence[hikari.Embed]], optional
            A sequence of embeds to add to this message.
        mentions_everyone : undefined.UndefinedOr[bool], optional
            If True, mentioning @everyone will be allowed.
        user_mentions : undefined.UndefinedOr[t.Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]], optional
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : undefined.UndefinedOr[t.Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]], optional
            The set of allowed role mentions in this message. Set to True to allow all.
        flags : t.Union[undefined.UndefinedType, int, hikari.MessageFlag], optional
            Message flags that should be included with this message.

        Returns
        -------
        InteractionResponse
            A proxy object representing the response to the interaction.
        """
        if self._issued_response:
            message = await self.interaction.execute(
                content,
                tts=tts,
                component=component,
                components=components,
                attachment=attachment,
                attachments=attachments,
                embed=embed,
                embeds=embeds,
                mentions_everyone=mentions_everyone,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
                flags=flags,
            )
            response = self._create_response(message)
        else:
            await self.interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_CREATE,
                content,
                tts=tts,
                component=component,
                components=components,
                attachment=attachment,
                attachments=attachments,
                embed=embed,
                embeds=embeds,
                mentions_everyone=mentions_everyone,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
                flags=flags,
            )
            self._issued_response = True
            response = self._create_response()
        if delete_after:
            response.delete_after(delete_after)
        return response

    async def edit_response(
        self,
        content: hikari.UndefinedNoneOr[t.Any] = hikari.UNDEFINED,
        *,
        flags: t.Union[int, hikari.MessageFlag, hikari.UndefinedType] = hikari.UNDEFINED,
        tts: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        component: hikari.UndefinedNoneOr[hikari.api.ComponentBuilder] = hikari.UNDEFINED,
        components: hikari.UndefinedNoneOr[t.Sequence[hikari.api.ComponentBuilder]] = hikari.UNDEFINED,
        attachment: hikari.UndefinedNoneOr[hikari.Resourceish] = hikari.UNDEFINED,
        attachments: hikari.UndefinedNoneOr[t.Sequence[hikari.Resourceish]] = hikari.UNDEFINED,
        embed: hikari.UndefinedNoneOr[hikari.Embed] = hikari.UNDEFINED,
        embeds: hikari.UndefinedNoneOr[t.Sequence[hikari.Embed]] = hikari.UNDEFINED,
        mentions_everyone: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        user_mentions: hikari.UndefinedOr[
            t.Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]
        ] = hikari.UNDEFINED,
        role_mentions: hikari.UndefinedOr[
            t.Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]
        ] = hikari.UNDEFINED,
    ) -> InteractionResponse:
        """A short-hand method to edit the last message belonging to this interaction.
        In the case of modals, this will be the component's message that triggered the modal.

        Parameters
        ----------
        content : undefined.UndefinedOr[t.Any], optional
            The content of the message. Anything passed here will be cast to str.
        tts : undefined.UndefinedOr[bool], optional
            If the message should be tts or not.
        attachment : undefined.UndefinedNoneOr[hikari.Resourceish], optional
            An attachment to add to this message.
        attachments : undefined.UndefinedNoneOr[t.Sequence[hikari.Resourceish]], optional
            A sequence of attachments to add to this message.
        component : undefined.UndefinedNoneOr[hikari.api.special_endpoints.ComponentBuilder], optional
            A component to add to this message.
        components : undefined.UndefinedNoneOr[t.Sequence[hikari.api.special_endpoints.ComponentBuilder]], optional
            A sequence of components to add to this message.
        embed : undefined.UndefinedNoneOr[hikari.Embed], optional
            An embed to add to this message.
        embeds : undefined.UndefinedNoneOr[t.Sequence[hikari.Embed]], optional
            A sequence of embeds to add to this message.
        mentions_everyone : undefined.UndefinedOr[bool], optional
            If True, mentioning @everyone will be allowed.
        user_mentions : undefined.UndefinedOr[t.Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]], optional
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : undefined.UndefinedOr[t.Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]], optional
            The set of allowed role mentions in this message. Set to True to allow all.
        flags : t.Union[undefined.UndefinedType, int, hikari.MessageFlag], optional
            Message flags that should be included with this message.

        Returns
        -------
        InteractionResponse
            A proxy object representing the response to the interaction.
        """
        if self._issued_response:
            message = await self.interaction.edit_initial_response(
                content,
                component=component,
                components=components,
                attachment=attachment,
                attachments=attachments,
                embed=embed,
                embeds=embeds,
                mentions_everyone=mentions_everyone,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
            )
            return self._create_response(message)

        else:
            await self.interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_UPDATE,
                content,
                component=component,
                components=components,
                attachment=attachment,
                attachments=attachments,
                tts=tts,
                embed=embed,
                embeds=embeds,
                mentions_everyone=mentions_everyone,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
                flags=flags,
            )
            self._issued_response = True
            return self._create_response()

    @t.overload
    async def defer(
        self,
        response_type: hikari.ResponseType,
        *,
        flags: hikari.UndefinedOr[t.Union[int, hikari.MessageFlag]] = hikari.UNDEFINED,
    ) -> None:
        ...

    @t.overload
    async def defer(self, *, flags: hikari.UndefinedOr[t.Union[int, hikari.MessageFlag]] = hikari.UNDEFINED) -> None:
        ...

    async def defer(
        self,
        *args: t.Any,
        flags: hikari.UndefinedOr[t.Union[int, hikari.MessageFlag]] = hikari.UNDEFINED,
        **kwargs: t.Any,
    ) -> None:
        """Short-hand method to defer an interaction response. Raises RuntimeError if the interaction was already responded to.

        Parameters
        ----------
        response_type : hikari.ResponseType, optional
            The response-type of this defer action. Defaults to DEFERRED_MESSAGE_UPDATE.
        flags : t.Union[int, hikari.MessageFlag, None], optional
            Message flags that should be included with this defer request, by default None

        Raises
        ------
        RuntimeError
            The interaction was already responded to.
        ValueError
            response_type was not a deffered response type.
        """
        response_type = args[0] if args else hikari.ResponseType.DEFERRED_MESSAGE_UPDATE

        if response_type not in [
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE,
            hikari.ResponseType.DEFERRED_MESSAGE_UPDATE,
        ]:
            raise ValueError(
                "Parameter response_type must be ResponseType.DEFERRED_MESSAGE_CREATE or ResponseType.DEFERRED_MESSAGE_UPDATE."
            )

        if self._issued_response:
            raise RuntimeError("Interaction was already responded to.")

        await self.interaction.create_initial_response(response_type, flags=flags)
        self._issued_response = True


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
