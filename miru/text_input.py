from __future__ import annotations

import typing as t

import hikari

from miru.abc.item import ModalItem
from miru.context.modal import ModalContext

if t.TYPE_CHECKING:
    from miru.modal import Modal

ModalT = t.TypeVar("ModalT", bound="Modal")

__all__ = ("TextInput",)


class TextInput(ModalItem):
    """A text input field that can be used in modals.

    Parameters
    ----------
    label : str
        The label above the text input field.
    style : hikari.TextInputStyle
        The style of the text input
    placeholder : Optional[str]
        Placeholder content in the text input
    value : Optional[str]
        Pre-filled content of the input field
    required : bool
        If the text input is required for modal submission
    min_length : Optional[int]
        The minimum required input length of the text input
    max_length : Optional[int]
        The maximum allowed input length of the text input
    custom_id : Optional[str]
        The custom identifier of the text input
    row : Optional[int]
        The row of the text input
    """

    def __init__(
        self,
        *,
        label: str,
        style: hikari.TextInputStyle = hikari.TextInputStyle.SHORT,
        placeholder: str | None = None,
        value: str | None = None,
        required: bool = False,
        min_length: int | None = None,
        max_length: int | None = None,
        custom_id: str | None = None,
        row: int | None = None,
    ) -> None:
        super().__init__(custom_id=custom_id, row=row, position=0, width=5, required=required)
        self._value: str | None = str(value) if value else None
        self.style = style
        self.placeholder = placeholder
        self.label = label
        self.max_length = max_length
        self.min_length = min_length

    @property
    def type(self) -> hikari.ComponentType:
        return hikari.ComponentType.TEXT_INPUT

    @property
    def style(self) -> hikari.TextInputStyle:
        """The text input's style."""
        return self._style

    @style.setter
    def style(self, value: hikari.TextInputStyle) -> None:
        self._style = value

    @property
    def label(self) -> str:
        """The text input's label. This is the text visible above the text input."""
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        if len(value) > 45:
            raise ValueError(f"Parameter 'label' must be 45 or fewer in length. (Found length {len(value)})")
        self._label = str(value)

    @property
    def placeholder(self) -> str | None:
        """Placeholder content for this text input field."""
        return self._placeholder

    @placeholder.setter
    def placeholder(self, value: str | None) -> None:
        if value is not None and len(value) > 100:
            raise ValueError(f"Parameter 'placeholder' must be 100 or fewer in length. (Found length {len(value)})")
        self._placeholder = str(value) if value else None

    @property
    def value(self) -> str | None:
        """Pre-filled content that should be included in the text input.
        After sending the modal, this field will be updated to the user's input.
        """
        return self._value

    @value.setter
    def value(self, value: str | None) -> None:
        if value:
            if self.min_length is not None and self.min_length > len(value):
                raise ValueError("Parameter 'value' does not meet minimum length requirement.")

            if self.max_length is not None and self.max_length < len(value):
                raise ValueError("Parameter 'value' does not meet maximum length requirement.")

        self._value = str(value) if value else None

    @property
    def min_length(self) -> int | None:
        """What the required minimum length of the input text should be."""
        return self._min_length

    @min_length.setter
    def min_length(self, value: int | None) -> None:
        if self.value and value is not None and value > len(self.value):
            raise ValueError("New minimum length constraint does not satisfy pre-filled value.")
        self._min_length = value

    @property
    def max_length(self) -> int | None:
        """What the maximum allowed length of the input text should be."""
        return self._max_length

    @max_length.setter
    def max_length(self, value: int | None) -> None:
        if self.value and value is not None and value < len(self.value):
            raise ValueError("New maximum length constraint does not satisfy pre-filled value.")
        self._max_length = value

    def _build(self, action_row: hikari.api.ModalActionRowBuilder) -> None:
        action_row.add_text_input(
            self.custom_id,
            self.label,
            style=self.style,
            placeholder=self.placeholder or hikari.UNDEFINED,
            value=self.value or hikari.UNDEFINED,
            required=self.required,
            min_length=self.min_length or 0,
            max_length=self.max_length or 4000,
        )

    async def _refresh_state(self, context: ModalContext) -> None:
        assert isinstance(context, ModalContext)
        self._value = context.values.get(self)


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
