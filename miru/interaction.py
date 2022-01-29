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

import functools
import typing

import hikari

if typing.TYPE_CHECKING:
    from hikari import messages


__all__ = ["Interaction"]


class Interaction(hikari.ComponentInteraction):
    """
    Represents a component interaction on Discord. Has additional short-hand methods for ease-of-use.
    """

    _issued_response: bool = False

    @classmethod
    def from_hikari(cls, interaction: hikari.ComponentInteraction) -> Interaction:
        """Create a new Interaction object from a hikari.ComponentInteraction. This should be rarely used.

        Parameters
        ----------
        interaction : hikari.ComponentInteraction
            The ComponentInteraction this object should be created from.

        Returns
        -------
        Interaction
            The created interaction object.
        """
        return cls(
            channel_id=interaction.channel_id,
            component_type=interaction.component_type,
            custom_id=interaction.custom_id,
            values=interaction.values,
            guild_id=interaction.guild_id,
            message=interaction.message,
            member=interaction.member,
            user=interaction.user,
            app=interaction.app,
            id=interaction.id,
            application_id=interaction.application_id,
            type=interaction.type,
            token=interaction.token,
            version=interaction.version,
        )

    @functools.wraps(hikari.ComponentInteraction.create_initial_response)
    async def create_initial_response(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        await super().create_initial_response(*args, **kwargs)
        self._issued_response = True

    @functools.wraps(hikari.ComponentInteraction.execute)
    async def send_message(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        """Short-hand method to send a message response to the interaction

        Parameters
        ----------
        content : undefined.UndefinedOr[typing.Any], optional
            The content of the message. Anything passed here will be cast to str.
        tts : undefined.UndefinedOr[bool], optional
            If the message should be tts or not.
        attachment : undefined.UndefinedOr[files_.Resourceish], optional
            An attachment to add to this message.
        attachments : undefined.UndefinedOr[typing.Sequence[files_.Resourceish]], optional
            A sequence of attachments to add to this message.
        component : undefined.UndefinedOr[special_endpoints.ComponentBuilder], optional
            A component to add to this message.
        components : undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]], optional
            A sequence of components to add to this message.
        embed : undefined.UndefinedOr[embeds_.Embed], optional
            An embed to add to this message.
        embeds : undefined.UndefinedOr[typing.Sequence[embeds_.Embed]], optional
            A sequence of embeds to add to this message.
        mentions_everyone : undefined.UndefinedOr[bool], optional
            If True, mentioning @everyone will be allowed.
        user_mentions : undefined.UndefinedOr[typing.Union[snowflakes.SnowflakeishSequence[users_.PartialUser], bool]], optional
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : undefined.UndefinedOr[typing.Union[snowflakes.SnowflakeishSequence[guilds_.PartialRole], bool]], optional
            The set of allowed role mentions in this message. Set to True to allow all.
        flags : typing.Union[undefined.UndefinedType, int, messages_.MessageFlag], optional
            Message flags that should be included with this message.
        """
        if self._issued_response:
            await self.execute(*args, **kwargs)
        else:
            await self.create_initial_response(hikari.ResponseType.MESSAGE_CREATE, *args, **kwargs)

    @functools.wraps(hikari.ComponentInteraction.execute)
    async def edit_message(self, *args: typing.Any, **kwargs: typing.Any) -> None:  # type: ignore
        """A short-hand method to edit the message belonging to this interaction.

        Parameters
        ----------
        content : undefined.UndefinedOr[typing.Any], optional
            The content of the message. Anything passed here will be cast to str.
        tts : undefined.UndefinedOr[bool], optional
            If the message should be tts or not.
        attachment : undefined.UndefinedOr[files_.Resourceish], optional
            An attachment to add to this message.
        attachments : undefined.UndefinedOr[typing.Sequence[files_.Resourceish]], optional
            A sequence of attachments to add to this message.
        component : undefined.UndefinedOr[special_endpoints.ComponentBuilder], optional
            A component to add to this message.
        components : undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]], optional
            A sequence of components to add to this message.
        embed : undefined.UndefinedOr[embeds_.Embed], optional
            An embed to add to this message.
        embeds : undefined.UndefinedOr[typing.Sequence[embeds_.Embed]], optional
            A sequence of embeds to add to this message.
        mentions_everyone : undefined.UndefinedOr[bool], optional
            If True, mentioning @everyone will be allowed.
        user_mentions : undefined.UndefinedOr[typing.Union[snowflakes.SnowflakeishSequence[users_.PartialUser], bool]], optional
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : undefined.UndefinedOr[typing.Union[snowflakes.SnowflakeishSequence[guilds_.PartialRole], bool]], optional
            The set of allowed role mentions in this message. Set to True to allow all.
        flags : typing.Union[undefined.UndefinedType, int, messages_.MessageFlag], optional
            Message flags that should be included with this edit.
        
        Raises
        ------
        RuntimeError
            The interaction was already responded to.
        """
        if self._issued_response:
            raise RuntimeError("Interaction was already responded to.")

        await self.create_initial_response(hikari.ResponseType.MESSAGE_UPDATE, *args, **kwargs)

    async def defer(self, flags: typing.Union[int, messages.MessageFlag, None] = None) -> None:
        """Short-hand method to defer an interaction response. Raises RuntimeError if the interaction was already responded to.

        Parameters
        ----------
        flags : typing.Union[int, messages.MessageFlag, None], optional
            Message flags that should be included with this defer request, by default None

        Raises
        ------
        RuntimeError
            The interaction was already responded to.
        """

        if self._issued_response:
            raise RuntimeError("Interaction was already responded to.")

        await self.create_initial_response(hikari.ResponseType.DEFERRED_MESSAGE_UPDATE, flags=flags)
