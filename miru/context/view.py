from __future__ import annotations

import asyncio
import enum
import typing as t
from contextlib import suppress

import hikari

from miru.abc.context import Context

if t.TYPE_CHECKING:
    from miru.abc.context import InteractionResponse
    from miru.client import Client
    from miru.internal.types import ViewResponseBuildersT
    from miru.modal import Modal
    from miru.view import View

__all__ = ("ViewContext", "AutodeferOptions", "AutodeferMode")


class AutodeferOptions:
    def __init__(
        self,
        mode: AutodeferMode,
        response_type: t.Literal[hikari.ResponseType.DEFERRED_MESSAGE_CREATE]
        | t.Literal[hikari.ResponseType.DEFERRED_MESSAGE_UPDATE],
    ) -> None:
        self._mode = mode
        self._response_type = response_type

    @property
    def mode(self) -> AutodeferMode:
        """The autodefer mode."""
        return self._mode

    @property
    def response_type(self) -> hikari.ResponseType:
        """The response type to use when autodefering."""
        return self._response_type

    @classmethod
    def parse(cls, autodefer: bool | AutodeferOptions) -> AutodeferOptions:
        if isinstance(autodefer, bool):
            return cls(AutodeferMode(autodefer), hikari.ResponseType.DEFERRED_MESSAGE_UPDATE)
        return autodefer


class AutodeferMode(enum.IntEnum):
    OFF = 0
    """Do not autodefer."""

    ON = 1
    """Autodefer if the item takes longer than 2 seconds to respond."""

    EPHEMERAL = 2
    """Autodefer and make the response ephemeral if the item takes longer than 2 seconds to respond."""

    @property
    def should_autodefer(self) -> bool:
        """Whether this mode should autodefer."""
        return self is not self.OFF


class ViewContext(Context[hikari.ComponentInteraction]):
    """A context object proxying a ComponentInteraction for a view item."""

    __slots__ = "_view"

    def __init__(self, view: View, client: Client, interaction: hikari.ComponentInteraction) -> None:
        super().__init__(client, interaction)
        self._view = view
        self._autodefer_task: asyncio.Task[None] | None = None

    def _start_autodefer(self, options: AutodeferOptions) -> None:
        if self._autodefer_task is not None:
            raise RuntimeError("ViewContext autodefer task already started")

        self._autodefer_task = asyncio.create_task(self._autodefer(options))

    async def _create_response(self, message: hikari.Message | None = None) -> InteractionResponse:
        if self._autodefer_task is not None:
            self._autodefer_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._autodefer_task
            self._autodefer_task = None

        return await super()._create_response(message)

    async def _autodefer(self, options: AutodeferOptions) -> None:
        await asyncio.sleep(2)

        async with self._response_lock:
            if self._issued_response:
                return
            flags = hikari.MessageFlag.EPHEMERAL if options.mode is AutodeferMode.EPHEMERAL else hikari.UNDEFINED
            # ctx.defer() also acquires _response_lock so we need to use self._interaction directly
            if not self.client.is_rest:
                await self._interaction.create_initial_response(options.response_type, flags=flags)  # type: ignore
            else:
                self._resp_builder.set_result(
                    hikari.impl.InteractionDeferredBuilder(options.response_type, flags=flags)  # type: ignore
                )
            self._issued_response = True
            await super()._create_response()

    @property
    def view(self) -> View:
        """The view this context originates from."""
        return self._view

    @property
    def message(self) -> hikari.Message:
        """The message object for the view this context is proxying."""
        return self._interaction.message

    async def respond_with_modal(self, modal: Modal) -> None:
        """Respond to this interaction with a modal."""
        if self._issued_response:
            raise RuntimeError("Interaction was already responded to.")

        async with self._response_lock:
            builder = modal.build_response(self.client)

            if self.client.is_rest:
                self._resp_builder.set_result(builder)
            else:
                await self._interaction.create_modal_response(
                    title=builder.title, custom_id=builder.custom_id, components=builder.components
                )
            self.client.start_modal(modal)
            self._issued_response = True

    async def respond_with_builder(self, builder: ViewResponseBuildersT) -> InteractionResponse | None:
        """Respond to this interaction with a response builder.

        Parameters
        ----------
        builder : ViewResponseBuildersT
            The builder to respond with.

        Returns
        -------
        InteractionResponse | None
            The response that was sent. This is None if the builder created a modal.

        Raises
        ------
        RuntimeError
            The interaction was already responded to.
        """
        if self._issued_response:
            raise RuntimeError("Interaction was already responded to.")

        async with self._response_lock:
            if self.client.is_rest:
                self._resp_builder.set_result(builder)
            else:
                if isinstance(builder, hikari.api.InteractionDeferredBuilder):
                    await self._interaction.create_initial_response(response_type=builder.type, flags=builder.flags)
                elif isinstance(builder, hikari.api.InteractionMessageBuilder):
                    await self._interaction.create_initial_response(
                        response_type=builder.type,
                        flags=builder.flags,
                        content=builder.content,
                        embeds=builder.embeds,
                        components=builder.components,
                        attachments=builder.attachments,
                        tts=builder.is_tts,
                        mentions_everyone=builder.mentions_everyone,
                        user_mentions=builder.user_mentions,
                        role_mentions=builder.role_mentions,
                    )
                else:
                    await self._interaction.create_modal_response(
                        title=builder.title, custom_id=builder.custom_id, components=builder.components
                    )

            resp = (
                await self._create_response() if not isinstance(builder, hikari.api.InteractionModalBuilder) else None
            )

            self._issued_response = True
            return resp


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
