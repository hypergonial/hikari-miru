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

from __future__ import annotations

import typing

import hikari
from hikari.snowflakes import Snowflake

from .interaction import Interaction
from .traits import ViewsAware

if typing.TYPE_CHECKING:
    from .view import View

__all__ = ["Context"]


class Context:
    """
    A context object proxying a component interaction.
    """

    def __init__(self, view: View, interaction: Interaction) -> None:
        self._view: View = view
        self._interaction: Interaction = interaction

    @property
    def interaction(self) -> Interaction:
        """The underlying interaction object."""
        return self._interaction

    @property
    def view(self) -> View:
        """The view this context originates from."""
        return self._view

    @property
    def app(self) -> ViewsAware:
        """The application that loaded miru."""
        return self._view.app

    @property
    def message(self) -> hikari.Message:
        """The message object this context is proxying."""
        return self._interaction.message

    @property
    def user(self) -> hikari.User:
        """The user who triggered this interaction."""
        return self._interaction.user

    @property
    def member(self) -> typing.Optional[hikari.InteractionMember]:
        """The member who triggered this interaction. Will be None in DMs."""
        return self._interaction.member

    @property
    def locale(self) -> str:
        """The locale of this context."""
        return self._interaction.locale

    @property
    def guild_locale(self) -> typing.Optional[str]:
        """
        The guild locale of this context, if in a guild.
        This will default to `en-US` if not a community guild.
        """
        return self._interaction.guild_locale

    @property
    def channel_id(self) -> Snowflake:
        """The ID of the channel the context represents."""
        return self._interaction.channel_id

    @property
    def guild_id(self) -> typing.Optional[Snowflake]:
        """The ID of the guild the context represents. Will be None in DMs."""
        return self._interaction.guild_id

    def get_guild(self) -> typing.Optional[hikari.GatewayGuild]:
        """Gets the guild this context represents, if any. Requires application cache."""
        return self.interaction.get_guild()

    def get_channel(self) -> typing.Union[hikari.GuildTextChannel, hikari.GuildNewsChannel, None]:
        """Gets the channel this context represents, None if in a DM. Requires application cache."""
        return self.interaction.get_channel()

    async def respond(
        self,
        content: hikari.UndefinedOr[typing.Any] = hikari.UNDEFINED,
        *,
        flags: typing.Union[int, hikari.MessageFlag, hikari.UndefinedType] = hikari.UNDEFINED,
        tts: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        component: hikari.UndefinedOr[hikari.api.ComponentBuilder] = hikari.UNDEFINED,
        components: hikari.UndefinedOr[typing.Sequence[hikari.api.ComponentBuilder]] = hikari.UNDEFINED,
        embed: hikari.UndefinedOr[hikari.Embed] = hikari.UNDEFINED,
        embeds: hikari.UndefinedOr[typing.Sequence[hikari.Embed]] = hikari.UNDEFINED,
        mentions_everyone: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        user_mentions: hikari.UndefinedOr[
            typing.Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]
        ] = hikari.UNDEFINED,
        role_mentions: hikari.UndefinedOr[
            typing.Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]
        ] = hikari.UNDEFINED,
    ) -> None:
        """Short-hand method to respond to the interaction this context represents.

        Parameters
        ----------
        content : undefined.UndefinedOr[typing.Any], optional
            The content of the message. Anything passed here will be cast to str.
        tts : undefined.UndefinedOr[bool], optional
            If the message should be tts or not.
        attachment : undefined.UndefinedOr[hikari.Resourceish], optional
            An attachment to add to this message.
        attachments : undefined.UndefinedOr[typing.Sequence[hikari.Resourceish]], optional
            A sequence of attachments to add to this message.
        component : undefined.UndefinedOr[hikari.api.special_endpoints.ComponentBuilder], optional
            A component to add to this message.
        components : undefined.UndefinedOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]], optional
            A sequence of components to add to this message.
        embed : undefined.UndefinedOr[hikari.Embed], optional
            An embed to add to this message.
        embeds : undefined.UndefinedOr[typing.Sequence[hikari.Embed]], optional
            A sequence of embeds to add to this message.
        mentions_everyone : undefined.UndefinedOr[bool], optional
            If True, mentioning @everyone will be allowed.
        user_mentions : undefined.UndefinedOr[typing.Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]], optional
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : undefined.UndefinedOr[typing.Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]], optional
            The set of allowed role mentions in this message. Set to True to allow all.
        flags : typing.Union[undefined.UndefinedType, int, hikari.MessageFlag], optional
            Message flags that should be included with this message.
        """
        if self.interaction._issued_response:
            await self.interaction.execute(
                content,
                tts=tts,
                component=component,
                components=components,
                embed=embed,
                embeds=embeds,
                mentions_everyone=mentions_everyone,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
                flags=flags,
            )
        else:
            await self.interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_CREATE,
                content,
                tts=tts,
                component=component,
                components=components,
                embed=embed,
                embeds=embeds,
                mentions_everyone=mentions_everyone,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
                flags=flags,
            )

    async def edit_response(
        self,
        content: hikari.UndefinedOr[typing.Any] = hikari.UNDEFINED,
        *,
        flags: typing.Union[int, hikari.MessageFlag, hikari.UndefinedType] = hikari.UNDEFINED,
        tts: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        component: hikari.UndefinedOr[hikari.api.ComponentBuilder] = hikari.UNDEFINED,
        components: hikari.UndefinedOr[typing.Sequence[hikari.api.ComponentBuilder]] = hikari.UNDEFINED,
        embed: hikari.UndefinedOr[hikari.Embed] = hikari.UNDEFINED,
        embeds: hikari.UndefinedOr[typing.Sequence[hikari.Embed]] = hikari.UNDEFINED,
        mentions_everyone: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        user_mentions: hikari.UndefinedOr[
            typing.Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]
        ] = hikari.UNDEFINED,
        role_mentions: hikari.UndefinedOr[
            typing.Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]
        ] = hikari.UNDEFINED,
    ) -> None:
        """A short-hand method to edit the message belonging to this interaction.

        Parameters
        ----------
        content : undefined.UndefinedOr[typing.Any], optional
            The content of the message. Anything passed here will be cast to str.
        tts : undefined.UndefinedOr[bool], optional
            If the message should be tts or not.
        attachment : undefined.UndefinedOr[hikari.Resourceish], optional
            An attachment to add to this message.
        attachments : undefined.UndefinedOr[typing.Sequence[hikari.Resourceish]], optional
            A sequence of attachments to add to this message.
        component : undefined.UndefinedOr[hikari.api.special_endpoints.ComponentBuilder], optional
            A component to add to this message.
        components : undefined.UndefinedOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]], optional
            A sequence of components to add to this message.
        embed : undefined.UndefinedOr[hikari.Embed], optional
            An embed to add to this message.
        embeds : undefined.UndefinedOr[typing.Sequence[hikari.Embed]], optional
            A sequence of embeds to add to this message.
        mentions_everyone : undefined.UndefinedOr[bool], optional
            If True, mentioning @everyone will be allowed.
        user_mentions : undefined.UndefinedOr[typing.Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]], optional
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : undefined.UndefinedOr[typing.Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]], optional
            The set of allowed role mentions in this message. Set to True to allow all.
        flags : typing.Union[undefined.UndefinedType, int, hikari.MessageFlag], optional
            Message flags that should be included with this message.

        Raises
        ------
        RuntimeError
            The interaction was already responded to.
        """
        if self.interaction._issued_response:
            await self.interaction.edit_initial_response(
                content,
                component=component,
                components=components,
                embed=embed,
                embeds=embeds,
                mentions_everyone=mentions_everyone,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
            )
        else:
            await self.interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_UPDATE,
                content,
                component=component,
                components=components,
                tts=tts,
                embed=embed,
                embeds=embeds,
                mentions_everyone=mentions_everyone,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
                flags=flags,
            )

    async def defer(self, flags: typing.Union[int, hikari.MessageFlag, None] = None) -> None:
        """Short-hand method to defer an interaction response. Raises RuntimeError if the interaction was already responded to.

        Parameters
        ----------
        flags : typing.Union[int, hikari.MessageFlag, None], optional
            Message flags that should be included with this defer request, by default None

        Raises
        ------
        RuntimeError
            The interaction was already responded to.
        """

        if self.interaction._issued_response:
            raise RuntimeError("Interaction was already responded to.")

        await self.interaction.create_initial_response(hikari.ResponseType.DEFERRED_MESSAGE_UPDATE, flags=flags)
