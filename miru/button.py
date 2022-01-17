"""
MIT License

Copyright (c) 2022-present HyperGH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import inspect
import os
from typing import Callable
from typing import Optional
from typing import Union

import hikari

from .item import Item


class Button(Item):
    """
    A view component representing a button.
    """

    def __init__(
        self,
        *,
        style: hikari.ButtonStyle = hikari.ButtonStyle.PRIMARY,
        label: Optional[str] = None,
        disabled: bool = False,
        custom_id: Optional[str] = None,
        url: Optional[str] = None,
        emoji: Union[hikari.Emoji, str, None] = None,
        row: Optional[int] = None,
    ) -> None:
        super().__init__()

        if emoji is None and label is None:
            raise TypeError("Must provide at least one of emoji or label")

        if custom_id and url:
            raise TypeError("Cannot provide both url and custom_id")

        self._style: hikari.ButtonStyle = style
        self._label: Optional[str] = label
        self._disabled: bool = disabled
        self._emoji: Union[str, hikari.Emoji, None] = emoji
        self._custom_id: Optional[str] = custom_id
        self._row: Optional[int] = int(row) if row else None
        self._url: Optional[str] = url

        self._persistent: bool = True if custom_id else False

        if self.url is None and self.custom_id is None:
            self.custom_id = os.urandom(16).hex()

        if self.url is not None:
            self.style = hikari.ButtonStyle.LINK

    @property
    def type(self) -> hikari.ComponentType:
        return hikari.ComponentType.BUTTON

    @property
    def style(self) -> hikari.ButtonStyle:
        """
        The button's style.
        """
        return self._style

    @style.setter
    def style(self, value: hikari.ButtonStyle) -> None:
        if not isinstance(value, hikari.ButtonStyle):
            raise TypeError("Expected type hikari.ButtonStyle for property style.")
        self._style = value

    @property
    def disabled(self) -> bool:
        """
        Boolean indicating if the button should be disabled or not.
        """
        return self._disabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("Expected type bool for property disabled.")
        self._disabled = value

    @property
    def label(self) -> Optional[str]:
        """
        The button's label. This is the text visible on the button.
        """
        return self._label

    @label.setter
    def label(self, value: Optional[str]) -> None:
        self._label = str(value) if value else None

    @property
    def emoji(self) -> Union[str, hikari.Emoji, None]:
        """
        The emoji that should be visible on the button, if any.
        """
        return self._emoji

    @emoji.setter
    def emoji(self, value: Union[str, hikari.Emoji, None]) -> None:
        if value and isinstance(value, str):
            value = hikari.Emoji.parse(value)

        if value and not isinstance(value, hikari.Emoji):
            raise TypeError("Expected types str or hikari.Emoji for property emoji.")
        self._emoji = value

    @property
    def url(self) -> Optional[str]:
        """
        The button's URL. If specified, the button will turn into a link button, and the style kwarg will be ignored.
        """
        return self._url

    @url.setter
    def url(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Expected type str for property url.")
        self._url = value

    def _build(self, action_row: hikari.api.ActionRowBuilder) -> None:
        """
        Called internally to build and append the button to an action row
        """
        button: Union[
            hikari.api.InteractiveButtonBuilder[hikari.api.ActionRowBuilder],
            hikari.api.LinkButtonBuilder[hikari.api.ActionRowBuilder],
        ]
        if self.style is hikari.ButtonStyle.LINK:
            assert self.url is not None
            button = action_row.add_button(hikari.ButtonStyle.LINK, self.url)
        else:
            assert self.custom_id is not None
            button = action_row.add_button(self.style, self.custom_id)

        if self.label:
            button.set_label(self.label)
        if self.emoji:
            button.set_emoji(self.emoji)
        button.set_is_disabled(self.disabled)
        button.add_to_container()


def button(
    *,
    label: Optional[str] = None,
    custom_id: Optional[str] = None,
    style: hikari.ButtonStyle = hikari.ButtonStyle.PRIMARY,
    emoji: Optional[Union[str, hikari.Emoji]] = None,
    row: Optional[int] = None,
    disabled: Optional[bool] = False,
) -> Callable[[Callable], Callable]:
    """
    A decorator to transform a function into a Discord UI Button's callback. This must be inside a subclass of View.
    """

    def decorator(func: Callable) -> Callable:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("button must decorate coroutine function.")

        func._view_item_type = Button
        func._view_item_data = {
            "label": label,
            "custom_id": custom_id,
            "style": style,
            "emoji": emoji,
            "row": row,
            "disabled": disabled,
            "url": None,
        }
        return func

    return decorator
