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

import inspect
import os
from optparse import Option
from typing import Any
from typing import Callable
from typing import Coroutine
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
            raise TypeError("Must provide at least one of emoji and label")

        if custom_id and url:
            raise TypeError("Cannot provide both url and custom_id")

        if url is None and custom_id is None:
            custom_id = os.urandom(16).hex()

        if url is not None:
            style = hikari.ButtonStyle.LINK

        self.style: hikari.ButtonStyle = style
        self.label: Optional[str] = label
        self.disabled: bool = disabled
        self.emoji: Union[str, hikari.Emoji, None] = emoji
        self._persistent: bool = True if custom_id else False
        self.custom_id: Optional[str] = custom_id
        self._row: Optional[int] = int(row) if row else None
        self.url: Optional[str] = url

    @property
    def type(self) -> hikari.ComponentType:
        return hikari.ComponentType.BUTTON

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
