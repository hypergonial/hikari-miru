from __future__ import annotations

import abc
import inspect
import typing as t
from functools import partial

import hikari

import miru
from miru.abc import ViewItem

if t.TYPE_CHECKING:
    from miru.ext.menu.menu import Menu
    from miru.ext.menu.screen import Screen

__all__ = (
    "ScreenItem",
    "ScreenButton",
    "ScreenTextSelect",
    "ScreenUserSelect",
    "ScreenRoleSelect",
    "ScreenChannelSelect",
    "ScreenMentionableSelect",
    "button",
    "text_select",
    "user_select",
    "role_select",
    "channel_select",
    "mentionable_select",
)

ScreenT = t.TypeVar("ScreenT", bound="Screen")
ScreenItemT = t.TypeVar("ScreenItemT", bound="ScreenItem")


class ScreenItem(ViewItem, abc.ABC):
    """A base class for all screen items. Screen requires instances of this class as it's items."""

    def __init__(
        self,
        *,
        custom_id: str | None = None,
        row: int | None = None,
        position: int | None = None,
        disabled: bool = False,
        width: int = 1,
    ) -> None:
        super().__init__(custom_id=custom_id, row=row, width=width, position=position, disabled=disabled)
        self._handler: Menu | None = None  # type: ignore
        self._screen: Screen | None = None

    @property
    def view(self) -> Menu:
        """The view this item is attached to."""
        if not self._handler:
            raise AttributeError(f"{type(self).__name__} hasn't been attached to a view yet")
        return self._handler

    @property
    def menu(self) -> Menu:
        """The menu this item is attached to. Alias for `view`."""
        return self.view

    @property
    def screen(self) -> Screen:
        """The screen this item is attached to."""
        if not self._screen:
            raise AttributeError(f"{type(self).__name__} hasn't been attached to a screen yet")
        return self._screen


class ScreenButton(miru.Button, ScreenItem):
    """A base class for all screen buttons."""


class ScreenTextSelect(miru.TextSelect, ScreenItem):
    """A base class for all screen text selects."""


class ScreenUserSelect(miru.UserSelect, ScreenItem):
    """A base class for all screen user selects."""


class ScreenRoleSelect(miru.RoleSelect, ScreenItem):
    """A base class for all screen role selects."""


class ScreenChannelSelect(miru.ChannelSelect, ScreenItem):
    """A base class for all screen channel selects."""


class ScreenMentionableSelect(miru.MentionableSelect, ScreenItem):
    """A base class for all screen mentionable selects."""


class DecoratedScreenItem(t.Generic[ScreenT, ScreenItemT]):
    """A partial item made using a decorator."""

    __slots__ = ("item", "callback")

    def __init__(
        self, item: ScreenItemT, callback: t.Callable[[ScreenT, ScreenItemT, miru.ViewContext], t.Awaitable[None]]
    ) -> None:
        self.item = item
        self.callback = callback

    def build(self, screen: Screen) -> ScreenItemT:
        """Convert a DecoratedScreenItem into a ViewItem.

        Parameters
        ----------
        screen : ScreenT
            The screen this decorated item is attached to.

        Returns
        -------
        ScreenItemT
            The converted item.
        """
        self.item.callback = partial(self.callback, screen, self.item)  # type: ignore[assignment]

        return self.item

    @property
    def name(self) -> str:
        """The name of the callback this item decorates.

        Returns
        -------
        str
            The name of the callback.
        """
        return self.callback.__name__

    def __call__(self, screen: ScreenT, item: ScreenItemT, context: miru.ViewContext) -> t.Any:
        return self.callback(screen, item, context)


def button(
    *,
    label: str | None = None,
    custom_id: str | None = None,
    style: hikari.ButtonStyle = hikari.ButtonStyle.PRIMARY,
    emoji: str | hikari.Emoji | None = None,
    row: int | None = None,
    disabled: bool = False,
) -> t.Callable[
    [t.Callable[[ScreenT, ScreenButton, miru.ViewContext], t.Awaitable[None]]],
    DecoratedScreenItem[ScreenT, ScreenButton],
]:
    """A decorator to transform a coroutine function into a Discord UI Button's callback.
    This must be inside a subclass of Screen.

    Parameters
    ----------
    label : Optional[str]
        The button's label
    custom_id : Optional[str]
        The button's custom ID
    style : hikari.ButtonStyle
        The style of the button
    emoji : Optional[Union[str, hikari.Emoji]]
        The emoji shown on the button
    row : Optional[int]
        The row the button should be in, leave as None for auto-placement.
    disabled : bool
        A boolean determining if the button should be disabled or not

    Returns
    -------
    Callable[[Callable[[ScreenT, ScreenButton, ViewContextT], Awaitable[None]]], DecoratedScreenItem[ScreenT, ScreenButton, ViewContextT]]
        The decorated callback coroutine function.

    Raises
    ------
    TypeError
        If the decorated function is not a coroutine function.
    """

    def decorator(
        func: t.Callable[[ScreenT, ScreenButton, miru.ViewContext], t.Awaitable[None]],
    ) -> DecoratedScreenItem[ScreenT, ScreenButton]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("button must decorate coroutine function.")
        item: ScreenButton = ScreenButton(
            label=label, custom_id=custom_id, style=style, emoji=emoji, row=row, disabled=disabled, url=None
        )

        return DecoratedScreenItem(item, func)

    return decorator


def channel_select(
    *,
    channel_types: t.Sequence[hikari.ChannelType] = (hikari.ChannelType.GUILD_TEXT,),
    custom_id: str | None = None,
    placeholder: str | None = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: int | None = None,
) -> t.Callable[
    [t.Callable[[ScreenT, ScreenChannelSelect, miru.ViewContext], t.Awaitable[None]]],
    DecoratedScreenItem[ScreenT, ScreenChannelSelect],
]:
    """A decorator to transform a function into a Discord UI ChannelSelectMenu's callback.
    This must be inside a subclass of Screen.

    Parameters
    ----------
    channel_types : Sequence[hikari.ChannelType]
        A sequence of channel types to filter the select menu by. Defaults to (hikari.ChannelType.GUILD_TEXT,).
    custom_id : Optional[str]
        The custom ID for the select menu. Defaults to None.
    placeholder : Optional[str]
        The placeholder text for the channel select menu. Defaults to None.
    min_values : int
        The minimum number of values that can be selected. Defaults to 1.
    max_values : int
        The maximum number of values that can be selected. Defaults to 1.
    disabled : bool
        Whether the channel select menu is disabled or not. Defaults to False.
    row : Optional[int]
        The row the select should be in, leave as None for auto-placement.

    Returns
    -------
    Callable[[Callable[[ScreenT, ScreenChannelSelect, ViewContextT], Awaitable[None]]], DecoratedScreenItem[ScreenT, ScreenChannelSelect, ViewContextT]]
        The decorated function.

    Raises
    ------
    TypeError
        If the decorated function is not a coroutine function.
    """

    def decorator(
        func: t.Callable[[ScreenT, ScreenChannelSelect, miru.ViewContext], t.Awaitable[None]],
    ) -> DecoratedScreenItem[ScreenT, ScreenChannelSelect]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("channel_select must decorate coroutine function.")

        item: ScreenChannelSelect = ScreenChannelSelect(
            channel_types=channel_types,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        return DecoratedScreenItem(item, func)

    return decorator


def mentionable_select(
    *,
    custom_id: str | None = None,
    placeholder: str | None = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: int | None = None,
) -> t.Callable[
    [t.Callable[[ScreenT, ScreenMentionableSelect, miru.ViewContext], t.Awaitable[None]]],
    DecoratedScreenItem[ScreenT, ScreenMentionableSelect],
]:
    """A decorator to transform a function into a Discord UI MentionableSelectMenu's callback.
    This must be inside a subclass of Screen.

    Parameters
    ----------
    custom_id : Optional[str]
        The custom ID for the select menu
    placeholder : Optional[str]
        The placeholder text to display when no option is selected
    min_values : int
        The minimum number of values that can be selected
    max_values : int
        The maximum number of values that can be selected
    disabled : bool
        Whether the mentionable select menu is disabled
    row : Optional[int]
        The row the select should be in, leave as None for auto-placement.

    Returns
    -------
    Callable[[Callable[[ScreenT, ScreenMentionableSelect, ViewContextT], Awaitable[None]]], DecoratedScreenItem[ScreenT, ScreenMentionableSelect, ViewContextT]]
        The decorated function.

    Raises
    ------
    TypeError
        If the decorated function is not a coroutine function.
    """

    def decorator(
        func: t.Callable[[ScreenT, ScreenMentionableSelect, miru.ViewContext], t.Awaitable[None]],
    ) -> DecoratedScreenItem[ScreenT, ScreenMentionableSelect]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("mentionable_select must decorate coroutine function.")

        item: ScreenMentionableSelect = ScreenMentionableSelect(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        return DecoratedScreenItem(item, func)

    return decorator


def role_select(
    *,
    custom_id: str | None = None,
    placeholder: str | None = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: int | None = None,
) -> t.Callable[
    [t.Callable[[ScreenT, ScreenRoleSelect, miru.ViewContext], t.Awaitable[None]]],
    DecoratedScreenItem[ScreenT, ScreenRoleSelect],
]:
    """A decorator to transform a function into a Discord UI RoleSelectMenu's callback.
    This must be inside a subclass of Screen.

    Parameters
    ----------
    custom_id : Optional[str]
        The custom ID for the select menu
    placeholder : Optional[str]
        The placeholder text to display when no roles are selected
    min_values : int
        The minimum number of roles that can be selected
    max_values : int
        The maximum number of roles that can be selected
    disabled : bool
        Whether the select menu is disabled or not
    row : Optional[int]
        The row number to place the select menu in

    Returns
    -------
    Callable[[Callable[[ScreenT, ScreenRoleSelect, ViewContextT], Awaitable[None]]], DecoratedScreenItem[ScreenT, ScreenRoleSelect, ViewContextT]]
        The decorated function that serves as the callback for the select menu.

    Raises
    ------
    TypeError
        If the decorated function is not a coroutine function.
    """

    def decorator(
        func: t.Callable[[ScreenT, ScreenRoleSelect, miru.ViewContext], t.Awaitable[None]],
    ) -> DecoratedScreenItem[ScreenT, ScreenRoleSelect]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("role_select must decorate coroutine function.")

        item: ScreenRoleSelect = ScreenRoleSelect(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        return DecoratedScreenItem(item, func)

    return decorator


def text_select(
    *,
    options: t.Sequence[hikari.SelectMenuOption | miru.SelectOption],
    custom_id: str | None = None,
    placeholder: str | None = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: int | None = None,
) -> t.Callable[
    [t.Callable[[ScreenT, ScreenTextSelect, miru.ViewContext], t.Awaitable[None]]],
    DecoratedScreenItem[ScreenT, ScreenTextSelect],
]:
    """A decorator to transform a function into a Discord UI TextSelectMenu's callback.
    This must be inside a subclass of Screen.

    Parameters
    ----------
    options : Sequence[Union[hikari.SelectMenuOption, miru.SelectOption]]
        The options to add to the select menu.
    custom_id : Optional[str]
        The custom ID for the select menu
    placeholder : Optional[str]
        The placeholder text to display when no options are selected
    min_values : int
        The minimum number of options that can be selected
    max_values : int
        The maximum number of options that can be selected
    disabled : bool
        Whether the select menu is disabled or not
    row : Optional[int]
        The row number to place the select menu in

    Returns
    -------
    Callable[[Callable[[ScreenT, ScreenTextSelect, ViewContextT], Awaitable[None]]], DecoratedScreenItem[ScreenT, ScreenTextSelect, ViewContextT]]
        The decorated function that serves as the callback for the select menu.
    """

    def decorator(
        func: t.Callable[[ScreenT, ScreenTextSelect, miru.ViewContext], t.Awaitable[None]],
    ) -> DecoratedScreenItem[ScreenT, ScreenTextSelect]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("text_select must decorate coroutine function.")

        item: ScreenTextSelect = ScreenTextSelect(
            options=options,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        return DecoratedScreenItem(item, func)

    return decorator


def user_select(
    *,
    custom_id: str | None = None,
    placeholder: str | None = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: int | None = None,
) -> t.Callable[
    [t.Callable[[ScreenT, ScreenUserSelect, miru.ViewContext], t.Awaitable[None]]],
    DecoratedScreenItem[ScreenT, ScreenUserSelect],
]:
    """A decorator to transform a function into a Discord UI UserSelectMenu's callback.
    This must be inside a subclass of Screen.

    Parameters
    ----------
    custom_id : Optional[str]
        The custom ID for the select menu
    placeholder : Optional[str]
        The placeholder text to display when no users are selected
    min_values : int
        The minimum number of users that can be selected
    max_values : int
        The maximum number of users that can be selected
    disabled : bool
        Whether the select menu is disabled or not
    row : Optional[int]
        The row number to place the select menu in

    Returns
    -------
    Callable[[Callable[[ScreenT, ScreenUserSelect, ViewContextT], Awaitable[None]]], DecoratedScreenItem[ScreenT, ScreenUserSelect, ViewContextT]]
        The decorated function that serves as the callback for the select menu.
    """

    def decorator(
        func: t.Callable[[ScreenT, ScreenUserSelect, miru.ViewContext], t.Awaitable[None]],
    ) -> DecoratedScreenItem[ScreenT, ScreenUserSelect]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("user_select must decorate coroutine function.")

        item: ScreenUserSelect = ScreenUserSelect(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        return DecoratedScreenItem(item, func)

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
