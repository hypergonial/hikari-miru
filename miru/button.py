from __future__ import annotations

import inspect
import typing as t

import hikari

from miru.abc.item import DecoratedItem, InteractiveViewItem, ViewItem

if t.TYPE_CHECKING:
    import typing_extensions as te

    from miru.context import ViewContext
    from miru.context.view import AutodeferOptions
    from miru.internal.types import InteractiveButtonStylesT
    from miru.view import View

    ViewT = t.TypeVar("ViewT", bound="View")

__all__ = ("Button", "LinkButton", "button")


class Button(InteractiveViewItem):
    """A view component representing an interactive button.

    Parameters
    ----------
    label : str | None
        The button's label
    emoji : hikari.Emoji | str | None
        The emoji present on the button
    style : hikari.ButtonStyle
        The button's style
    disabled : bool
        A boolean determining if the button should be disabled or not
    custom_id : str | None
        The custom identifier of the button
    row : int | None
        The row the button should be in, leave as None for auto-placement.
    position : int | None
        The position the button should be in within a row, leave as None for auto-placement.
    autodefer : bool | AutodeferOptions | hikari.UndefinedType
        The autodefer options for the button. If left `UNDEFINED`, the view's autodefer options will be used.

    Raises
    ------
    TypeError
        If both label and emoji are left empty.
    TypeError
        if both custom_id and url are provided.
    """

    def __init__(
        self,
        label: str | None = None,
        *,
        emoji: hikari.Emoji | str | None = None,
        style: InteractiveButtonStylesT = hikari.ButtonStyle.PRIMARY,
        disabled: bool = False,
        custom_id: str | None = None,
        row: int | None = None,
        position: int | None = None,
        autodefer: bool | AutodeferOptions | hikari.UndefinedType = hikari.UNDEFINED,
    ) -> None:
        super().__init__(custom_id=custom_id, row=row, position=position, disabled=disabled, autodefer=autodefer)
        self._emoji: hikari.Emoji | None = hikari.Emoji.parse(emoji) if isinstance(emoji, str) else emoji
        self.label = label
        self.style = style

    @property
    def type(self) -> hikari.ComponentType:
        return hikari.ComponentType.BUTTON

    @property
    def style(self) -> hikari.ButtonStyle:
        """The button's style."""
        return self._style

    @style.setter
    def style(self, value: InteractiveButtonStylesT) -> None:
        self._style = value

    @property
    def label(self) -> str | None:
        """The button's label. This is the text visible on the button."""
        return self._label

    @label.setter
    def label(self, value: str | None) -> None:
        if value is not None and len(value) > 80:
            raise ValueError(f"Parameter 'label' must be 80 or fewer in length. (Found {len(value)})")
        self._label = str(value) if value else None

    @property
    def emoji(self) -> hikari.Emoji | None:
        """The emoji that should be visible on the button."""
        return self._emoji

    @emoji.setter
    def emoji(self, value: str | hikari.Emoji | None) -> None:
        if isinstance(value, str):
            value = hikari.Emoji.parse(value)

        self._emoji = value

    @classmethod
    def _from_component(cls, component: hikari.PartialComponent, row: int | None = None) -> te.Self:
        assert isinstance(component, hikari.ButtonComponent)

        style = hikari.ButtonStyle(component.style)

        if style is hikari.ButtonStyle.LINK:
            raise ValueError(f"Cannot create '{cls.__name__}' from link button.")

        return cls(
            style=hikari.ButtonStyle(component.style),  # type: ignore
            label=component.label,
            disabled=component.is_disabled,
            custom_id=component.custom_id,
            emoji=component.emoji,
            row=row,
        )

    def _build(self, action_row: hikari.api.MessageActionRowBuilder) -> None:
        if self.emoji is None and self.label is None:
            raise TypeError("Must provide at least one of 'emoji' or 'label' when building Button.")

        action_row.add_interactive_button(
            self.style if self.style is not hikari.ButtonStyle.LINK else hikari.ButtonStyle.PRIMARY,
            self.custom_id,
            emoji=self.emoji or hikari.UNDEFINED,
            label=self.label or hikari.UNDEFINED,
            is_disabled=self.disabled,
        )


class LinkButton(ViewItem):
    """A view component representing a link button.

    Parameters
    ----------
    url : str | None
        The URL of the button
    label : str | None
        The button's label
    emoji : hikari.Emoji | str | None
        The emoji present on the button
    disabled : bool
        A boolean determining if the button should be disabled or not
    row : int | None
        The row the button should be in, leave as None for auto-placement.
    position : int | None
        The position the button should be in within a row, leave as None for auto-placement.

    Raises
    ------
    TypeError
        If both label and emoji are left empty.
    TypeError
        if both custom_id and url are provided.
    """

    def __init__(
        self,
        url: str,
        label: str | None = None,
        *,
        emoji: hikari.Emoji | str | None = None,
        disabled: bool = False,
        row: int | None = None,
        position: int | None = None,
    ) -> None:
        super().__init__(row=row, position=position, disabled=disabled)
        self._emoji: hikari.Emoji | None = hikari.Emoji.parse(emoji) if isinstance(emoji, str) else emoji
        self.label = label
        self._url = url

    @property
    def type(self) -> hikari.ComponentType:
        return hikari.ComponentType.BUTTON

    @property
    def style(self) -> t.Literal[hikari.ButtonStyle.LINK]:
        """The button's style."""
        return hikari.ButtonStyle.LINK

    @property
    def label(self) -> str | None:
        """The button's label. This is the text visible on the button."""
        return self._label

    @label.setter
    def label(self, value: str | None) -> None:
        if value is not None and len(value) > 80:
            raise ValueError(f"Parameter 'label' must be 80 or fewer in length. (Found {len(value)})")
        self._label = str(value) if value else None

    @property
    def emoji(self) -> hikari.Emoji | None:
        """The emoji that should be visible on the button."""
        return self._emoji

    @emoji.setter
    def emoji(self, value: str | hikari.Emoji | None) -> None:
        if isinstance(value, str):
            value = hikari.Emoji.parse(value)

        self._emoji = value

    @property
    def url(self) -> str:
        """The URL of the button."""
        return self._url

    @url.setter
    def url(self, value: str) -> None:
        self._url = str(value)

    @classmethod
    def _from_component(cls, component: hikari.PartialComponent, row: int | None = None) -> te.Self:
        assert isinstance(component, hikari.ButtonComponent)

        style = hikari.ButtonStyle(component.style)

        if style is not hikari.ButtonStyle.LINK or component.url is None:
            raise ValueError(f"Cannot create '{cls.__name__}' from interactive button.")

        return cls(
            label=component.label, disabled=component.is_disabled, url=component.url, emoji=component.emoji, row=row
        )

    def _build(self, action_row: hikari.api.MessageActionRowBuilder) -> None:
        if self.emoji is None and self.label is None:
            raise TypeError("Must provide at least one of 'emoji' or 'label' when building LinkButton.")

        action_row.add_link_button(
            self.url,
            emoji=self.emoji or hikari.UNDEFINED,
            label=self.label or hikari.UNDEFINED,
            is_disabled=self.disabled,
        )


def button(
    label: str | None = None,
    *,
    emoji: str | hikari.Emoji | None = None,
    custom_id: str | None = None,
    style: InteractiveButtonStylesT = hikari.ButtonStyle.PRIMARY,
    row: int | None = None,
    disabled: bool = False,
    autodefer: bool | AutodeferOptions | hikari.UndefinedType = hikari.UNDEFINED,
) -> t.Callable[[t.Callable[[ViewT, ViewContext, Button], t.Awaitable[None]]], DecoratedItem[ViewT, Button]]:
    """A decorator to transform a coroutine function into a Discord UI Button's callback.
    This must be inside a subclass of View.

    Parameters
    ----------
    label : str | None
        The button's label
    emoji : str | hikari.Emoji | None
        The emoji shown on the button
    custom_id : str | None
        The button's custom identifier
    style : InteractiveButtonStylesT
        The style of the button
    row : int | None
        The row the button should be in, leave as None for auto-placement.
    disabled : bool
        A boolean determining if the button should be disabled or not
    autodefer : bool | AutodeferOptions | hikari.UndefinedType
        The autodefer options for the button. If left `UNDEFINED`, the view's autodefer options will be used.

    Returns
    -------
    Callable[[Callable[[ViewT, ViewContext, Button], Awaitable[None]]], DecoratedItem[ViewT, Button]]
        The decorated callback function.
    """

    def decorator(func: t.Callable[[ViewT, ViewContext, Button], t.Awaitable[None]]) -> DecoratedItem[ViewT, Button]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("'@button' must decorate coroutine function.")
        item: Button = Button(
            label=label, custom_id=custom_id, style=style, emoji=emoji, row=row, disabled=disabled, autodefer=autodefer
        )

        return DecoratedItem(item, func)

    return decorator


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
