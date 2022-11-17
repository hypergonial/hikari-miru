from __future__ import annotations

import typing as t

import hikari

from .base import Context

if t.TYPE_CHECKING:
    from ..modal import Modal

__all__ = ("RawComponentContext", "RawModalContext")


class RawComponentContext(Context[hikari.ComponentInteraction]):
    """Raw context proxying component interactions received directly over the gateway."""

    __slots__ = ()

    @property
    def message(self) -> hikari.Message:
        """The message object for the view this context is proxying."""
        return self._interaction.message

    async def respond_with_modal(self, modal: Modal) -> None:
        """Respond to this interaction with a modal."""

        if self._issued_response:
            raise RuntimeError("Interaction was already responded to.")

        await modal.send(self.interaction)
        self._issued_response = True


class RawModalContext(Context[hikari.ModalInteraction]):
    """Raw context object proxying a ModalInteraction received directly over the gateway."""

    __slots__ = ()

    ...


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
