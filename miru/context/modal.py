from __future__ import annotations

import typing as t

import hikari

from ..internal.types import ClientT, ModalResponseBuildersT
from .base import Context

if t.TYPE_CHECKING:
    from ..abc.item import ModalItem
    from ..modal import Modal

__all__ = ("ModalContext",)

T = t.TypeVar("T")


class ModalContext(Context[ClientT, hikari.ModalInteraction]):
    """A context object proxying a ModalInteraction received by a miru modal."""

    __slots__ = ("_modal", "_values")

    def __init__(
        self,
        modal: Modal[ClientT],
        client: ClientT,
        interaction: hikari.ModalInteraction,
        values: t.Mapping[ModalItem[ClientT], str],
    ) -> None:
        super().__init__(client, interaction)
        self._modal = modal
        self._values = values

    @property
    def modal(self) -> Modal[ClientT]:
        """The modal this context originates from."""
        return self._modal

    @property
    def values(self) -> t.Mapping[ModalItem[ClientT], str]:
        """The values received as input for this modal."""
        return self._values

    async def respond_with_builder(self, builder: ModalResponseBuildersT) -> None:
        """Respond to this interaction with a response builder.

        Parameters
        ----------
        builder : ModalResponseBuildersT
            The builder to respond with.

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
                else:
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
            self._issued_response = True

    def get_value_by(
        self, predicate: t.Callable[[ModalItem[ClientT]], bool], default: hikari.UndefinedOr[T] = hikari.UNDEFINED
    ) -> T | str:
        """Get the value for the first modal item that matches the given predicate.

        Parameters
        ----------
        predicate : Callable[[ModalItem], bool]
            A predicate to match the item.
        default : hikari.UndefinedOr[T], optional
            A default value to return if no item was matched, by default hikari.UNDEFINED

        Returns
        -------
        T | str
            The value of the item that matched the predicate or the default value.

        Raises
        ------
        KeyError
            The item was not found and no default was provided.
        """
        for item, value in self.values.items():
            if predicate(item):
                return value

        if default is hikari.UNDEFINED:
            raise KeyError("No modal item matched the given predicate.")
        return default

    def get_value_by_id(self, custom_id: str, default: hikari.UndefinedOr[T] = hikari.UNDEFINED) -> T | str:
        """Get the value for a modal item with the given custom ID.

        Parameters
        ----------
        custom_id : str
            The custom_id of the component.
        default : hikari.UndefinedOr[T], optional
            A default value to return if the item was not found, by default hikari.UNDEFINED

        Returns
        -------
        T | str
            The value of the item with the given custom ID or the default value.

        Raises
        ------
        KeyError
            The item was not found and no default was provided.
        """
        return self.get_value_by(lambda item: item.custom_id == custom_id, default=default)


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
