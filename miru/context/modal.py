from __future__ import annotations

import typing as t

import hikari

from miru.abc.context import Context, InteractionResponse

if t.TYPE_CHECKING:
    from miru.abc.item import ModalItem
    from miru.client import Client
    from miru.internal.types import ModalResponseBuildersT
    from miru.modal import Modal

__all__ = ("ModalContext",)

T = t.TypeVar("T")


class ModalContext(Context[hikari.ModalInteraction]):
    """A context object proxying a ModalInteraction received by a miru modal."""

    __slots__ = ("_modal", "_values")

    def __init__(
        self, modal: Modal, client: Client, interaction: hikari.ModalInteraction, values: t.Mapping[ModalItem, str]
    ) -> None:
        super().__init__(client, interaction)
        self._modal = modal
        self._values = values

    @property
    def modal(self) -> Modal:
        """The modal this context originates from."""
        return self._modal

    @property
    def values(self) -> t.Mapping[ModalItem, str]:
        """The values received as input for this modal."""
        return self._values

    async def respond_with_builder(self, builder: ModalResponseBuildersT) -> InteractionResponse:  # pyright: ignore reportIncompatibleMethodOverride
        """Respond to the interaction with a builder. This method will try to turn the builder into a valid
        response or followup, depending on the builder type and interaction state.

        Parameters
        ----------
        builder : ModalResponseBuildersT
            The builder to respond with.

        Returns
        -------
        InteractionResponse
            The response that was sent.

        Raises
        ------
        RuntimeError
            The interaction was already responded to.
        """
        return await super().respond_with_builder(builder)

    def get_value_by(
        self, predicate: t.Callable[[ModalItem], bool], default: hikari.UndefinedOr[T] = hikari.UNDEFINED
    ) -> T | str:
        """Get the value for the first modal item that matches the given predicate.

        Parameters
        ----------
        predicate : Callable[[ModalItem], bool]
            A predicate to match the item.
        default : hikari.UndefinedOr[T]
            A default value to return if no item was matched

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
        default : hikari.UndefinedOr[T]
            A default value to return if the item was not found

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
