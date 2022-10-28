from __future__ import annotations

import typing as t

import hikari

from .raw import RawModalContext

if t.TYPE_CHECKING:
    from ..abc.item import ModalItem
    from ..modal import Modal

__all__ = ("ModalContext",)


class ModalContext(RawModalContext):
    """A context object proxying a ModalInteraction received by a miru modal."""

    __slots__ = ("_modal", "_values")

    def __init__(self, modal: Modal, interaction: hikari.ModalInteraction, values: t.Mapping[ModalItem, str]) -> None:
        super().__init__(interaction)
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

    def get_value_by_id(self, custom_id: str, default: hikari.UndefinedOr[t.Any] = hikari.UNDEFINED) -> t.Any:
        """Get the value for a modal item with the given custom ID.

        Parameters
        ----------
        custom_id : str
            The custom_id of the component.
        default : hikari.UndefinedOr[t.Any], optional
            A default value to return if the item was not found, by default hikari.UNDEFINED

        Returns
        -------
        Any
            The value of the item with the given custom ID or the default value.

        Raises
        ------
        KeyError
            The item was not found and no default was provided.
        """
        for item, value in self.values.items():
            if item.custom_id == custom_id:
                return value

        if default is hikari.UNDEFINED:
            raise KeyError(f"No modal item with ID {custom_id}.")
        return default

    def get_value_by_predicate(
        self,
        predicate: t.Callable[[ModalItem], bool],
        default: hikari.UndefinedOr[t.Any] = hikari.UNDEFINED,
    ) -> t.Any:
        """Get the value for the first modal item that matches the given predicate.

        Parameters
        ----------
        predicate : Callable[[ModalItem], bool]
            A predicate to match the item.
        default : hikari.UndefinedOr[t.Any], optional
            A default value to return if no item was matched, by default hikari.UNDEFINED

        Returns
        -------
        Any
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
