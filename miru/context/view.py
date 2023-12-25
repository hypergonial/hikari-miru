from __future__ import annotations

import asyncio
import typing as t
from contextlib import suppress

import hikari

from ..internal.types import ClientT
from .base import Context

if t.TYPE_CHECKING:
    from miru.context.base import InteractionResponse

    from ..modal import Modal
    from ..view import View

__all__ = ("ViewContext",)


class ViewContext(Context[ClientT, hikari.ComponentInteraction]):
    """A context object proxying a ComponentInteraction for a view item."""

    __slots__ = "_view"

    def __init__(self, view: View[ClientT], client: ClientT, interaction: hikari.ComponentInteraction) -> None:
        super().__init__(client, interaction)
        self._view = view
        self._autodefer_task: t.Optional[asyncio.Task[None]] = None

    def _start_autodefer(self) -> None:
        if self._autodefer_task is not None:
            raise RuntimeError("ViewContext autodefer task already started")

        self._autodefer_task = asyncio.create_task(self._autodefer())

    async def _create_response(self, message: hikari.Message | None = None) -> InteractionResponse:
        if self._autodefer_task is not None:
            self._autodefer_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._autodefer_task
            self._autodefer_task = None

        return await super()._create_response(message)

    async def _autodefer(self) -> None:
        await asyncio.sleep(2)

        async with self._response_lock:
            if self._issued_response:
                return
            # ctx.defer() also acquires _response_lock so we need to use self._interaction directly
            await self._interaction.create_initial_response(hikari.ResponseType.DEFERRED_MESSAGE_UPDATE)
            self._issued_response = True
            await super()._create_response()

    @property
    def view(self) -> View[ClientT]:
        """The view this context originates from."""
        return self._view

    @property
    def message(self) -> hikari.Message:
        """The message object for the view this context is proxying."""
        return self._interaction.message

    async def respond_with_modal(self, modal: Modal[ClientT]) -> None:
        """Respond to this interaction with a modal."""
        if self._issued_response:
            raise RuntimeError("Interaction was already responded to.")

        await modal._send(self.client, self.interaction)
        self._issued_response = True


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
