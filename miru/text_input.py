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

import os
from typing import TYPE_CHECKING
from typing import Optional
from typing import TypeVar
from typing import Union

import hikari

from .abc.item import ModalItem

if TYPE_CHECKING:
    from .modal import Modal

ModalT = TypeVar("ModalT", bound="Modal")

__all__ = ["TextInput"]


class TextInput(ModalItem[ModalT]):
    """A text input field that can be used in modals.

    Parameters
    ----------
    label : str
        The label above the text input field.
    style : Union[hikari.TextInputStyle, int], optional
        The style of the text input, by default hikari.TextInputStyle.SHORT
    placeholder : Optional[str], optional
        Placeholder content in the text input, by default None
    value : Optional[str], optional
        Pre-filled content of the input field, by default None
    required : bool, optional
        If the text input is required for modal submission, by default False
    min_length : Optional[int], optional
        The minimum required input length of the text input, by default None
    max_length : Optional[int], optional
        The maximum allowed input length of the text input, by default None
    custom_id : Optional[str], optional
        The custom identifier of the text input, by default None
    row : Optional[int], optional
        The row of the text input, by default None
    """

    def __init__(
        self,
        *,
        label: str,
        style: Union[hikari.TextInputStyle, int] = hikari.TextInputStyle.SHORT,
        placeholder: Optional[str] = None,
        value: Optional[str] = None,
        required: bool = False,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        custom_id: Optional[str] = None,
        row: Optional[int] = None,
    ) -> None:
        super().__init__()
        self._width: int = 5
        self._style: Union[hikari.TextInputStyle, int] = style
        self._placeholder: Optional[str] = placeholder
        self._value: Optional[str] = value
        self._label: str = label
        self._required: bool = required
        self._custom_id: Optional[str] = custom_id
        self._max_length: Optional[int] = max_length
        self._min_length: Optional[int] = min_length
        self._row: Optional[int] = int(row) if row is not None else None

        if self.custom_id is None:
            self.custom_id = os.urandom(16).hex()

    @property
    def type(self) -> hikari.ComponentType:
        return hikari.ComponentType.TEXT_INPUT

    @property
    def style(self) -> Union[hikari.TextInputStyle, int]:
        """
        The text input's style.
        """
        return self._style

    @style.setter
    def style(self, value: Union[hikari.TextInputStyle, int]) -> None:
        if not isinstance(value, (hikari.TextInputStyle, int)):
            raise TypeError("Expected type hikari.ButtonStyle or int for property style.")

        self._style = value

    @property
    def label(self) -> str:
        """
        The text input's label. This is the text visible above the text input.
        """
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        self._label = str(value)

    @property
    def placeholder(self) -> Optional[str]:
        """
        Placeholder content for this text input field.
        """
        return self._placeholder

    @placeholder.setter
    def placeholder(self, value: Optional[str]) -> None:
        self._placeholder = str(value) if value else None

    @property
    def value(self) -> Optional[str]:
        """
        Pre-filled content that should be included in the text input.
        """
        return self._value

    @value.setter
    def value(self, value: Optional[str]) -> None:
        self._value = str(value) if value else None

    @property
    def min_length(self) -> Optional[int]:
        return self._min_length

    @min_length.setter
    def min_length(self, value: Optional[int]) -> None:
        if not isinstance(value, int):
            raise TypeError("Expected type int for property min_length.")
        self._min_length = value

    @property
    def max_length(self) -> Optional[int]:
        return self._min_length

    @max_length.setter
    def max_length(self, value: Optional[int]) -> None:
        if not isinstance(value, int):
            raise TypeError("Expected type int for property max_length.")
        self._min_length = value

    def _build(self, action_row: hikari.api.ActionRowBuilder) -> None:

        assert self.custom_id is not None
        text_input = action_row.add_text_input(style=self.style, custom_id=self.custom_id, label=self.label)

        if self.max_length:
            text_input.set_max_length(self.max_length)
        if self.min_length:
            text_input.set_min_length(self.min_length)
        if self.placeholder:
            text_input.set_placeholder(self.placeholder)
        if self.value:
            text_input.set_value(self.value)

        text_input.add_to_container()