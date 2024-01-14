from __future__ import annotations

import typing as t
from collections.abc import Mapping
from typing import Any, Iterator

import hikari

if t.TYPE_CHECKING:
    from miru.client import Client


class InteractionMessageBuilder(hikari.impl.InteractionMessageBuilder, Mapping[str, t.Any]):
    def __init__(
        self,
        type: t.Literal[hikari.ResponseType.MESSAGE_CREATE, 4, hikari.ResponseType.MESSAGE_UPDATE, 7],
        content: hikari.UndefinedOr[str],
        *,
        flags: hikari.UndefinedOr[hikari.MessageFlag],
        embeds: hikari.UndefinedOr[list[hikari.Embed]],
        components: hikari.UndefinedNoneOr[list[hikari.api.ComponentBuilder]],
        attachments: hikari.UndefinedNoneOr[list[hikari.Resourceish]],
        is_tts: hikari.UndefinedOr[bool],
        mentions_everyone: hikari.UndefinedOr[bool],
        user_mentions: hikari.UndefinedOr[t.Sequence[hikari.SnowflakeishOr[hikari.PartialUser]] | bool],
        role_mentions: hikari.UndefinedOr[t.Sequence[hikari.SnowflakeishOr[hikari.PartialRole]] | bool],
    ) -> None:
        super().__init__(
            type=type,
            flags=flags,
            content=content,
            embeds=embeds,
            components=components,
            attachments=attachments,
            is_tts=is_tts,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )
        self._client: Client | None = None

    def to_hikari_kwargs(self) -> dict[str, t.Any]:
        """Convert this builder to kwargs that can be passed to a hikari interaction's 'create_initial_response'."""
        return {
            "response_type": self.type,
            "flags": self.flags,
            "content": self.content,
            "embeds": self.embeds,
            "components": self.components,
            "attachments": self.attachments,
            "tts": self.is_tts,
            "mentions_everyone": self.mentions_everyone,
            "user_mentions": self.user_mentions,
            "role_mentions": self.role_mentions,
        }

    def to_tanjun_kwargs(self) -> t.Mapping[str, t.Any]:
        """Convert this builder to kwargs that can be passed to a tanjun context's 'respond'."""
        kwargs = self.to_hikari_kwargs()
        kwargs.pop("response_type")
        kwargs.pop("flags")
        return kwargs

    def __getitem__(self, __key: str) -> Any:
        return self.to_hikari_kwargs()[__key]

    def __iter__(self) -> Iterator[str]:
        return self.to_hikari_kwargs().__iter__()

    def __len__(self) -> int:
        return len(self.to_hikari_kwargs())

    async def send_to_channel(self, channel: hikari.SnowflakeishOr[hikari.TextableChannel]) -> hikari.Message:
        """Send this builder to a channel. This only works with a GatewayClient.

        Parameters
        ----------
        channel : hikari.TextableChannel
            The channel to send this message to.

        Returns
        -------
        hikari.Message
            The message that was sent.

        Raises
        ------
        RuntimeError
            This method was invoked on a builder that was created by a RESTClient.
        """
        if self._client is None or self._client.is_rest:
            raise RuntimeError("This method can only be called in a Gateway context.")

        return await self._client.rest.create_message(
            channel=channel,
            content=self.content,
            embeds=self.embeds or hikari.UNDEFINED,
            components=self.components or hikari.UNDEFINED,
            attachments=self.attachments or hikari.UNDEFINED,
            tts=self.is_tts,
            mentions_everyone=self.mentions_everyone,
            user_mentions=self.user_mentions,
            role_mentions=self.role_mentions,
        )

    async def create_initial_response(self, interaction: hikari.MessageResponseMixin[t.Any]) -> None:
        """Create an initial response from this builder. This only works with a GatewayClient.

        Parameters
        ----------
        interaction : hikari.MessageResponseMixin
            The interaction to respond to.

        Returns
        -------
        hikari.Message
            The message that was sent.

        Raises
        ------
        RuntimeError
            This method was invoked on a builder that was created by a RESTClient.
        """
        if self._client is None or self._client.is_rest:
            raise RuntimeError("This method can only be called in a Gateway context.")

        return await interaction.create_initial_response(
            response_type=self.type,
            content=self.content,
            embeds=self.embeds or hikari.UNDEFINED,
            components=self.components or hikari.UNDEFINED,
            attachments=self.attachments or hikari.UNDEFINED,
            tts=self.is_tts,
            mentions_everyone=self.mentions_everyone,
            user_mentions=self.user_mentions,
            role_mentions=self.role_mentions,
        )

    async def create_followup(self, interaction: hikari.MessageResponseMixin[t.Any]) -> hikari.Message:
        """Create a followup message from this builder. This works in both Gateway and REST contexts.

        Parameters
        ----------
        interaction : hikari.MessageResponseMixin
            The interaction to respond to.

        Returns
        -------
        hikari.Message
            The message that was sent or edited.
        """
        return await interaction.execute(
            content=self.content,
            embeds=self.embeds or hikari.UNDEFINED,
            components=self.components or hikari.UNDEFINED,
            attachments=self.attachments or hikari.UNDEFINED,
            tts=self.is_tts,
            mentions_everyone=self.mentions_everyone,
            user_mentions=self.user_mentions,
            role_mentions=self.role_mentions,
        )


class InteractionDeferredBuilder(hikari.impl.InteractionDeferredBuilder, t.Mapping[str, t.Any]):
    def __init__(
        self,
        type: t.Literal[hikari.ResponseType.DEFERRED_MESSAGE_CREATE, 5, hikari.ResponseType.DEFERRED_MESSAGE_UPDATE, 6],
        *,
        flags: hikari.UndefinedOr[hikari.MessageFlag],
    ) -> None:
        super().__init__(type=type, flags=flags)
        self._client: Client | None = None

    def to_hikari_kwargs(self) -> dict[str, t.Any]:
        """Convert this builder to kwargs that can be passed to a hikari interaction's create_initial_response."""
        return {"response_type": self.type, "flags": self.flags}

    async def create_initial_response(self, interaction: hikari.MessageResponseMixin[t.Any]) -> None:
        """Create an initial response from this builder. This only works with a GatewayClient.

        Parameters
        ----------
        interaction : hikari.MessageResponseMixin
            The interaction to respond to.

        Raises
        ------
        RuntimeError
            This method was invoked on a builder that was created by a RESTClient.
        """
        if self._client is None or self._client.is_rest:
            raise RuntimeError("This method can only be called in a Gateway context.")

        await interaction.create_initial_response(response_type=self.type, flags=self.flags)

    def __getitem__(self, __key: str) -> Any:
        return self.to_hikari_kwargs()[__key]

    def __iter__(self) -> Iterator[str]:
        return self.to_hikari_kwargs().__iter__()

    def __len__(self) -> int:
        return len(self.to_hikari_kwargs())


class InteractionModalBuilder(hikari.impl.InteractionModalBuilder, t.Mapping[str, t.Any]):
    def __init__(self, title: str, custom_id: str, components: list[hikari.api.ComponentBuilder]) -> None:
        super().__init__(title=title, custom_id=custom_id, components=components)
        self._client: Client | None = None

    def to_hikari_kwargs(self) -> t.Mapping[str, t.Any]:
        """Convert this builder to kwargs that can be passed to a hikari interaction's create_modal_response."""
        return {"title": self.title, "custom_id": self.custom_id, "components": self.components}

    def to_tanjun_args(self) -> t.Sequence[str]:
        """Convert this builder to args that can be passed to a tanjun context's create_modal_response."""
        return (self.title, self.custom_id)

    def to_tanjun_kwargs(self) -> t.Mapping[str, t.Any]:
        """Convert this builder to kwargs that can be passed to a tanjun context's create_modal_response."""
        return {"components": self.components}

    def __getitem__(self, __key: str) -> Any:
        return self.to_hikari_kwargs()[__key]

    def __iter__(self) -> Iterator[str]:
        return self.to_hikari_kwargs().__iter__()

    def __len__(self) -> int:
        return len(self.to_hikari_kwargs())

    async def create_modal_response(self, interaction: hikari.ModalResponseMixin) -> None:
        """Create a modal response from this builder. This only works with a GatewayClient.

        Parameters
        ----------
        interaction : hikari.ModalInteraction
            The interaction to respond to.

        Raises
        ------
        RuntimeError
            This method was invoked on a builder that was created by a RESTClient.
        """
        if self._client is None or self._client.is_rest:
            raise RuntimeError("This method can only be called in a Gateway context.")

        await interaction.create_modal_response(title=self.title, custom_id=self.custom_id, components=self.components)


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
