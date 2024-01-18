from __future__ import annotations

import abc
import asyncio
import datetime
import logging
import typing as t

import attr
import hikari

if t.TYPE_CHECKING:
    from miru import Client
    from miru.internal.types import ResponseBuildersT

InteractionT = t.TypeVar("InteractionT", "hikari.ComponentInteraction", "hikari.ModalInteraction")

__all__ = ("Context", "InteractionResponse")

logger = logging.getLogger("__name__")


@attr.define(slots=True, kw_only=True, frozen=True)
class _ResponseGlue:
    """A glue object to allow for easy creation of responses in both REST and Gateway contexts."""

    response_type: t.Literal[hikari.ResponseType.MESSAGE_CREATE] | t.Literal[
        hikari.ResponseType.MESSAGE_UPDATE
    ] = hikari.ResponseType.MESSAGE_CREATE
    content: hikari.UndefinedOr[t.Any] = hikari.UNDEFINED
    flags: int | hikari.MessageFlag | hikari.UndefinedType = hikari.UNDEFINED
    tts: hikari.UndefinedOr[bool] = hikari.UNDEFINED
    component: hikari.UndefinedNoneOr[hikari.api.ComponentBuilder] = hikari.UNDEFINED
    components: hikari.UndefinedNoneOr[t.Sequence[hikari.api.ComponentBuilder]] = hikari.UNDEFINED
    attachment: hikari.UndefinedNoneOr[hikari.Resourceish] = hikari.UNDEFINED
    attachments: hikari.UndefinedNoneOr[t.Sequence[hikari.Resourceish]] = hikari.UNDEFINED
    embed: hikari.UndefinedNoneOr[hikari.Embed] = hikari.UNDEFINED
    embeds: hikari.UndefinedNoneOr[t.Sequence[hikari.Embed]] = hikari.UNDEFINED
    mentions_everyone: hikari.UndefinedOr[bool] = hikari.UNDEFINED
    user_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialUser] | bool] = hikari.UNDEFINED
    role_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialRole] | bool] = hikari.UNDEFINED

    def _to_dict(self) -> dict[str, t.Any]:
        return {
            "response_type": self.response_type,
            "content": self.content,
            "flags": self.flags,
            "tts": self.tts,
            "component": self.component,
            "components": self.components,
            "attachment": self.attachment,
            "attachments": self.attachments,
            "embed": self.embed,
            "embeds": self.embeds,
            "mentions_everyone": self.mentions_everyone,
            "user_mentions": self.user_mentions,
            "role_mentions": self.role_mentions,
        }

    def _to_builder(self) -> hikari.api.InteractionMessageBuilder:
        components: list[hikari.api.ComponentBuilder] = list(self.components) if self.components else []
        attachments: list[hikari.Resourceish] = list(self.attachments) if self.attachments else []
        embeds: list[hikari.Embed] = list(self.embeds) if self.embeds else []

        return hikari.impl.InteractionMessageBuilder(
            type=self.response_type,
            content=self.content,
            flags=self.flags,
            components=components or ([self.component] if self.component else hikari.UNDEFINED),
            attachments=attachments or ([self.attachment] if self.attachment else hikari.UNDEFINED),
            embeds=embeds or ([self.embed] if self.embed else hikari.UNDEFINED),
            mentions_everyone=self.mentions_everyone,
            user_mentions=self.user_mentions,
            role_mentions=self.role_mentions,
        )


class InteractionResponse:
    """Represents a message response to an interaction, allows for standardized handling of responses.
    This class is not meant to be directly instantiated, and is instead returned by [`Context`][miru.abc.context.Context].
    """

    __slots__ = ("_context", "_message", "_delete_after_task")

    def __init__(self, context: Context[InteractionT], message: hikari.Message | None = None) -> None:
        self._context: Context[InteractionT] = context
        self._message: hikari.Message | None = message
        self._delete_after_task: asyncio.Task[None] | None = None

    def __await__(self) -> t.Generator[t.Any, None, hikari.Message]:
        return self.retrieve_message().__await__()

    async def _do_delete_after(self, delay: float) -> None:
        """Delete the response after the specified delay.

        This should not be called manually,
        and instead should be triggered by the ``delete_after`` method of this class.
        """
        await asyncio.sleep(delay)
        await self.delete()

    def delete_after(self, delay: int | float | datetime.timedelta) -> None:
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

        !!! note
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
        else:
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
        user_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialUser] | bool] = hikari.UNDEFINED,
        role_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialRole] | bool] = hikari.UNDEFINED,
    ) -> InteractionResponse:
        """A short-hand method to edit the message belonging to this response.

        Parameters
        ----------
        content : undefined.UndefinedOr[t.Any]
            The content of the message. Anything passed here will be cast to str.
        attachment : undefined.UndefinedOr[hikari.Resourceish]
            An attachment to add to this message.
        attachments : undefined.UndefinedOr[t.Sequence[hikari.Resourceish]]
            A sequence of attachments to add to this message.
        component : undefined.UndefinedOr[hikari.api.special_endpoints.ComponentBuilder]
            A component to add to this message.
        components : undefined.UndefinedOr[t.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            A sequence of components to add to this message.
        embed : undefined.UndefinedOr[hikari.Embed]
            An embed to add to this message.
        embeds : undefined.UndefinedOr[t.Sequence[hikari.Embed]]
            A sequence of embeds to add to this message.
        mentions_everyone : undefined.UndefinedOr[bool]
            If True, mentioning @everyone will be allowed.
        user_mentions : undefined.UndefinedOr[[hikari.SnowflakeishSequence[hikari.PartialUser] | bool]
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : undefined.UndefinedOr[[hikari.SnowflakeishSequence[hikari.PartialRole] | bool]
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
        else:
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
        return await self._context._create_response(message)


class Context(abc.ABC, t.Generic[InteractionT]):
    """An abstract base class for context objects that proxying a Discord interaction."""

    __slots__ = (
        "_interaction",
        "_client",
        "_responses",
        "_issued_response",
        "_resp_builder",
        "_response_lock",
        "_autodefer_task",
        "_created_at",
    )

    def __init__(self, client: Client, interaction: InteractionT) -> None:
        self._interaction: InteractionT = interaction
        self._client = client
        self._responses: t.MutableSequence[InteractionResponse] = []
        self._issued_response: bool = False
        self._resp_builder: asyncio.Future[
            hikari.api.InteractionMessageBuilder
            | hikari.api.InteractionModalBuilder
            | hikari.api.InteractionDeferredBuilder
        ] = asyncio.Future()
        self._response_lock: asyncio.Lock = asyncio.Lock()
        self._created_at = datetime.datetime.now()

    @property
    def interaction(self) -> InteractionT:
        """The underlying interaction object.

        !!! warning
            This should not be used directly in most cases, and is only exposed for advanced use cases.

            If you use the interaction to create a response in a view,
            you should disable the autodefer feature in your View.
        """
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
    def client(self) -> Client:
        """The client that loaded miru."""
        return self._client

    @property
    def user(self) -> hikari.User:
        """The user who triggered this interaction."""
        return self._interaction.user

    @property
    def author(self) -> hikari.User:
        """Alias for Context.user."""
        return self.user

    @property
    def member(self) -> hikari.InteractionMember | None:
        """The member who triggered this interaction. Will be None in DMs."""
        return self._interaction.member

    @property
    def locale(self) -> str | hikari.Locale:
        """The locale of this context."""
        return self._interaction.locale

    @property
    def guild_locale(self) -> str | hikari.Locale | None:
        """The guild locale of this context, if in a guild.
        This will default to `en-US` if not a community guild.
        """
        return self._interaction.guild_locale

    @property
    def app_permissions(self) -> hikari.Permissions | None:
        """The permissions of the bot. Will be None in DMs."""
        return self._interaction.app_permissions

    @property
    def channel_id(self) -> hikari.Snowflake:
        """The ID of the channel the context represents."""
        return self._interaction.channel_id

    @property
    def guild_id(self) -> hikari.Snowflake | None:
        """The ID of the guild the context represents. Will be None in DMs."""
        return self._interaction.guild_id

    @property
    def is_valid(self) -> bool:
        """Returns if the underlying interaction expired or not.
        This is not 100% accurate due to API latency, but should be good enough for most use cases.
        """
        if self._issued_response:
            return datetime.datetime.now() - self._created_at <= datetime.timedelta(minutes=15)
        else:
            return datetime.datetime.now() - self._created_at <= datetime.timedelta(seconds=3)

    @property
    def issued_response(self) -> bool:
        """Whether this interaction was already issued an initial response."""
        return self._issued_response

    async def _create_response(self, message: hikari.Message | None = None) -> InteractionResponse:
        """Create a new response and add it to the list of tracked responses."""
        response = InteractionResponse(self, message)
        self._responses.append(response)
        return response

    def get_guild(self) -> hikari.GatewayGuild | None:
        """Gets the guild this context represents, if any. Requires application cache."""
        return self._interaction.get_guild()

    def get_channel(self) -> hikari.TextableGuildChannel | None:
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
        flags: int | hikari.MessageFlag | hikari.UndefinedType = hikari.UNDEFINED,
        tts: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        component: hikari.UndefinedOr[hikari.api.ComponentBuilder] = hikari.UNDEFINED,
        components: hikari.UndefinedOr[t.Sequence[hikari.api.ComponentBuilder]] = hikari.UNDEFINED,
        attachment: hikari.UndefinedOr[hikari.Resourceish] = hikari.UNDEFINED,
        attachments: hikari.UndefinedOr[t.Sequence[hikari.Resourceish]] = hikari.UNDEFINED,
        embed: hikari.UndefinedOr[hikari.Embed] = hikari.UNDEFINED,
        embeds: hikari.UndefinedOr[t.Sequence[hikari.Embed]] = hikari.UNDEFINED,
        mentions_everyone: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        user_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialUser] | bool] = hikari.UNDEFINED,
        role_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialRole] | bool] = hikari.UNDEFINED,
        delete_after: hikari.UndefinedOr[float | int | datetime.timedelta] = hikari.UNDEFINED,
    ) -> InteractionResponse:
        """Short-hand method to create a new message response via the interaction this context represents.

        Parameters
        ----------
        content : hikari.UndefinedOr[Any]
            The content of the message. Anything passed here will be cast to str.
        tts : hikari.UndefinedOr[bool]
            If the message should be tts or not.
        attachment : hikari.UndefinedOr[hikari.Resourceish]
            An attachment to add to this message.
        attachments : hikari.UndefinedOr[t.Sequence[hikari.Resourceish]]
            A sequence of attachments to add to this message.
        component : hikari.UndefinedOr[hikari.api.special_endpoints.ComponentBuilder]
            A component to add to this message.
        components : hikari.UndefinedOr[t.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            A sequence of components to add to this message.
        embed : hikari.UndefinedOr[hikari.Embed]
            An embed to add to this message.
        embeds : hikari.UndefinedOr[Sequence[hikari.Embed]]
            A sequence of embeds to add to this message.
        mentions_everyone : hikari.UndefinedOr[bool]
            If True, mentioning @everyone will be allowed.
        user_mentions : hikari.UndefinedOr[Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]]
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : hikari.UndefinedOr[Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]]
            The set of allowed role mentions in this message. Set to True to allow all.
        flags : Union[hikari.UndefinedType, int, hikari.MessageFlag]
            Message flags that should be included with this message.
        delete_after: hikari.undefinedOr[Union[float, int, datetime.timedelta]]
            Delete the response after the specified delay.

        Returns
        -------
        InteractionResponse
            A proxy object representing the response to the interaction.
        """
        async with self._response_lock:
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
                response = await self._create_response(message)
            else:
                glue = _ResponseGlue(
                    response_type=hikari.ResponseType.MESSAGE_CREATE,
                    content=content,
                    flags=flags,
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
                )
                if not self.client.is_rest:
                    await self.interaction.create_initial_response(**glue._to_dict())
                else:
                    self._resp_builder.set_result(glue._to_builder())
                self._issued_response = True
                response = await self._create_response()
            if delete_after:
                response.delete_after(delete_after)
            return response

    @t.overload
    async def respond_with_builder(self, builder: hikari.api.InteractionModalBuilder) -> None:
        ...

    @t.overload
    async def respond_with_builder(
        self, builder: hikari.api.InteractionMessageBuilder | hikari.api.InteractionDeferredBuilder
    ) -> InteractionResponse:
        ...

    async def respond_with_builder(self, builder: ResponseBuildersT) -> InteractionResponse | None:
        """Respond to the interaction with a builder. This method will try to turn the builder into a valid
        response or followup, depending on the builder type and interaction state.

        Parameters
        ----------
        builder : ResponseBuilderT
            The builder to respond with.

        Returns
        -------
        InteractionResponse | None
            A proxy object representing the response to the interaction. Will be None if the builder is a modal builder.

        Raises
        ------
        RuntimeError
            The interaction was already issued an initial response and the builder can only be used for initial responses.
        """
        async with self._response_lock:
            if self._issued_response and not isinstance(builder, hikari.api.InteractionMessageBuilder):
                raise RuntimeError("This interaction was already issued an initial response.")

            if self.client.is_rest and not self._issued_response:
                self._resp_builder.set_result(builder)
                self._issued_response = True
                if not isinstance(builder, hikari.api.InteractionModalBuilder):
                    return await self._create_response()
                return

            if isinstance(builder, hikari.api.InteractionMessageBuilder):
                if not self._issued_response:
                    await self.interaction.create_initial_response(
                        response_type=hikari.ResponseType.MESSAGE_CREATE,
                        content=builder.content,
                        tts=builder.is_tts,
                        components=builder.components,
                        attachments=builder.attachments,
                        embeds=builder.embeds,
                        mentions_everyone=builder.mentions_everyone,
                        user_mentions=builder.user_mentions,
                        role_mentions=builder.role_mentions,
                        flags=builder.flags,
                    )
                else:
                    await self.interaction.execute(
                        content=builder.content,
                        tts=builder.is_tts,
                        components=builder.components or hikari.UNDEFINED,
                        attachments=builder.attachments or hikari.UNDEFINED,
                        embeds=builder.embeds or hikari.UNDEFINED,
                        mentions_everyone=builder.mentions_everyone,
                        user_mentions=builder.user_mentions,
                        role_mentions=builder.role_mentions,
                        flags=builder.flags,
                    )
            elif isinstance(builder, hikari.api.InteractionDeferredBuilder):
                await self.interaction.create_initial_response(
                    response_type=hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=builder.flags
                )
            else:
                if isinstance(self.interaction, hikari.ModalInteraction):
                    raise RuntimeError("Cannot create a new modal response to a modal interaction.")

                await self.interaction.create_modal_response(
                    title=builder.title, custom_id=builder.custom_id, components=builder.components or hikari.UNDEFINED
                )

            self._issued_response = True
            if not isinstance(builder, hikari.api.InteractionModalBuilder):
                return await self._create_response()

    async def edit_response(
        self,
        content: hikari.UndefinedNoneOr[t.Any] = hikari.UNDEFINED,
        *,
        flags: int | hikari.MessageFlag | hikari.UndefinedType = hikari.UNDEFINED,
        tts: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        component: hikari.UndefinedNoneOr[hikari.api.ComponentBuilder] = hikari.UNDEFINED,
        components: hikari.UndefinedNoneOr[t.Sequence[hikari.api.ComponentBuilder]] = hikari.UNDEFINED,
        attachment: hikari.UndefinedNoneOr[hikari.Resourceish] = hikari.UNDEFINED,
        attachments: hikari.UndefinedNoneOr[t.Sequence[hikari.Resourceish]] = hikari.UNDEFINED,
        embed: hikari.UndefinedNoneOr[hikari.Embed] = hikari.UNDEFINED,
        embeds: hikari.UndefinedNoneOr[t.Sequence[hikari.Embed]] = hikari.UNDEFINED,
        mentions_everyone: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        user_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialUser] | bool] = hikari.UNDEFINED,
        role_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialRole] | bool] = hikari.UNDEFINED,
    ) -> InteractionResponse:
        """A short-hand method to edit the initial response belonging to this interaction.
        If no initial response was issued yet, this will create one of type ``MESSAGE_UPDATE``.
        In the case of modals, this will be the component's message that triggered the modal.

        Parameters
        ----------
        content : hikari.UndefinedOr[Any]
            The content of the message. Anything passed here will be cast to str.
        tts : hikari.UndefinedOr[bool]
            If the message should be tts or not.
        attachment : hikari.UndefinedOr[hikari.Resourceish]
            An attachment to add to this message.
        attachments : hikari.UndefinedOr[t.Sequence[hikari.Resourceish]]
            A sequence of attachments to add to this message.
        component : hikari.UndefinedOr[hikari.api.special_endpoints.ComponentBuilder]
            A component to add to this message.
        components : hikari.UndefinedOr[t.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            A sequence of components to add to this message.
        embed : hikari.UndefinedOr[hikari.Embed]
            An embed to add to this message.
        embeds : hikari.UndefinedOr[Sequence[hikari.Embed]]
            A sequence of embeds to add to this message.
        mentions_everyone : hikari.UndefinedOr[bool]
            If True, mentioning @everyone will be allowed.
        user_mentions : hikari.UndefinedOr[Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]]
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : hikari.UndefinedOr[Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]]
            The set of allowed role mentions in this message. Set to True to allow all.
        flags : Union[hikari.UndefinedType, int, hikari.MessageFlag]
            Message flags that should be included with this message.

        Returns
        -------
        InteractionResponse
            A proxy object representing the response to the interaction.
        """
        async with self._response_lock:
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
                return await self._create_response(message)

            else:
                glue = _ResponseGlue(
                    response_type=hikari.ResponseType.MESSAGE_UPDATE,
                    content=content,
                    flags=flags,
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
                )

                if not self.client.is_rest:
                    await self.interaction.create_initial_response(**glue._to_dict())
                else:
                    self._resp_builder.set_result(glue._to_builder())

                self._issued_response = True
                return await self._create_response()

    @t.overload
    async def defer(
        self,
        response_type: t.Literal[hikari.ResponseType.DEFERRED_MESSAGE_CREATE]
        | t.Literal[hikari.ResponseType.DEFERRED_MESSAGE_UPDATE],
        *,
        flags: hikari.UndefinedOr[int | hikari.MessageFlag] = hikari.UNDEFINED,
    ) -> None:
        ...

    @t.overload
    async def defer(self, *, flags: hikari.UndefinedOr[int | hikari.MessageFlag] = hikari.UNDEFINED) -> None:
        ...

    async def defer(  # noqa: D417
        self, *args: t.Any, flags: hikari.UndefinedOr[int | hikari.MessageFlag] = hikari.UNDEFINED, **kwargs: t.Any
    ) -> None:
        """Short-hand method to defer an interaction response. Raises RuntimeError if the interaction was already responded to.

        Parameters
        ----------
        response_type : hikari.ResponseType
            The response-type of this defer action. Defaults to DEFERRED_MESSAGE_UPDATE.
        flags : Union[int, hikari.MessageFlag, None]
            Message flags that should be included with this defer request

        Raises
        ------
        RuntimeError
            The interaction was already responded to.
        ValueError
            response_type was not a deferred response type.
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

        async with self._response_lock:
            if not self.client.is_rest:
                await self.interaction.create_initial_response(response_type, flags=flags)
            else:
                self._resp_builder.set_result(hikari.impl.InteractionDeferredBuilder(response_type, flags=flags))
            self._issued_response = True
            await self._create_response()


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
