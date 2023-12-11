import abc
import inspect
import typing as t

import hikari

import miru
from miru.abc import DecoratedItem, ViewItem

if t.TYPE_CHECKING:
    from .menu import Menu
    from .screen import Screen

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

ViewContextT = t.TypeVar("ViewContextT", bound=miru.ViewContext)
ScreenT = t.TypeVar("ScreenT", bound="Screen")


class ScreenItem(ViewItem, abc.ABC):
    """A baseclass for all navigation items. NavigatorView requires instances of this class as it's items."""

    def __init__(
        self,
        *,
        custom_id: t.Optional[str] = None,
        row: t.Optional[int] = None,
        position: t.Optional[int] = None,
        disabled: bool = False,
        width: int = 1,
    ) -> None:
        super().__init__(custom_id=custom_id, row=row, width=width, position=position, disabled=disabled)
        self._handler: t.Optional[Menu] = None
        self._screen: t.Optional[Screen] = None

    async def before_page_change(self) -> None:
        """
        Called when the navigator is about to transition to the next page. Also called before the first page is sent.
        """
        pass

    @property
    def view(self) -> Menu:
        """
        The view this item is attached to.
        """
        if not self._handler:
            raise AttributeError(f"{type(self).__name__} hasn't been attached to a view yet")
        return self._handler

    @property
    def screen(self) -> Screen:
        """
        The screen this item is attached to.
        """
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


def button(
    *,
    label: t.Optional[str] = None,
    custom_id: t.Optional[str] = None,
    style: hikari.ButtonStyle = hikari.ButtonStyle.PRIMARY,
    emoji: t.Optional[t.Union[str, hikari.Emoji]] = None,
    row: t.Optional[int] = None,
    disabled: bool = False,
) -> t.Callable[[t.Callable[[ScreenT, ScreenButton, ViewContextT], t.Awaitable[None]]], DecoratedItem[ScreenButton]]:
    """A decorator to transform a coroutine function into a Discord UI Button's callback.
    This must be inside a subclass of Screen.

    Parameters
    ----------
    label : Optional[str], optional
        The button's label, by default None
    custom_id : Optional[str], optional
        The button's custom ID, by default None
    style : hikari.ButtonStyle, optional
        The style of the button, by default hikari.ButtonStyle.PRIMARY
    emoji : Optional[Union[str, hikari.Emoji]], optional
        The emoji shown on the button, by default None
    row : Optional[int], optional
        The row the button should be in, leave as None for auto-placement.
    disabled : bool, optional
        A boolean determining if the button should be disabled or not, by default False

    Returns
    -------
    Callable[[Callable[[ScreenT, ScreenButton, ViewContextT], Awaitable[None]]], DecoratedItem[ScreenButton]]
        The decorated callback coroutine function.

    Raises
    ------
    TypeError
        If the decorated function is not a coroutine function.
    """

    def decorator(
        func: t.Callable[[ScreenT, ScreenButton, ViewContextT], t.Awaitable[None]],
    ) -> DecoratedItem[ScreenButton]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("button must decorate coroutine function.")
        item = ScreenButton(
            label=label, custom_id=custom_id, style=style, emoji=emoji, row=row, disabled=disabled, url=None
        )

        return DecoratedItem(item, func)

    return decorator


def channel_select(
    *,
    channel_types: t.Sequence[hikari.ChannelType] = (hikari.ChannelType.GUILD_TEXT,),
    custom_id: t.Optional[str] = None,
    placeholder: t.Optional[str] = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: t.Optional[int] = None,
) -> t.Callable[
    [t.Callable[[ScreenT, ScreenChannelSelect, ViewContextT], t.Awaitable[None]]], DecoratedItem[ScreenChannelSelect]
]:
    """
    A decorator to transform a function into a Discord UI ChannelSelectMenu's callback.
    This must be inside a subclass of Screen.

    Parameters
    ----------
    channel_types : Sequence[hikari.ChannelType], optional
        A sequence of channel types to filter the select menu by. Defaults to (hikari.ChannelType.GUILD_TEXT,).
    custom_id : Optional[str], optional
        The custom ID for the select menu. Defaults to None.
    placeholder : Optional[str], optional
        The placeholder text for the channel select menu. Defaults to None.
    min_values : int, optional
        The minimum number of values that can be selected. Defaults to 1.
    max_values : int, optional
        The maximum number of values that can be selected. Defaults to 1.
    disabled : bool, optional
        Whether the channel select menu is disabled or not. Defaults to False.
    row : Optional[int], optional
        The row the select should be in, leave as None for auto-placement.

    Returns
    -------
    Callable[[Callable[[ScreenT, ScreenChannelSelect, ViewContextT], Awaitable[None]]], DecoratedItem[ScreenChannelSelect]]
        The decorated function.

    Raises
    ------
    TypeError
        If the decorated function is not a coroutine function.
    """

    def decorator(
        func: t.Callable[[ScreenT, ScreenChannelSelect, ViewContextT], t.Awaitable[None]],
    ) -> DecoratedItem[ScreenChannelSelect]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("channel_select must decorate coroutine function.")

        item = ScreenChannelSelect(
            channel_types=channel_types,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        return DecoratedItem(item, func)

    return decorator


def mentionable_select(
    *,
    custom_id: t.Optional[str] = None,
    placeholder: t.Optional[str] = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: t.Optional[int] = None,
) -> t.Callable[
    [t.Callable[[ScreenT, ScreenMentionableSelect, ViewContextT], t.Awaitable[None]]],
    DecoratedItem[ScreenMentionableSelect],
]:
    """
    A decorator to transform a function into a Discord UI MentionableSelectMenu's callback.
    This must be inside a subclass of Screen.

    Parameters
    ----------
    custom_id : Optional[str], optional
        The custom ID for the select menu, by default None
    placeholder : Optional[str], optional
        The placeholder text to display when no option is selected, by default None
    min_values : int, optional
        The minimum number of values that can be selected, by default 1
    max_values : int, optional
        The maximum number of values that can be selected, by default 1
    disabled : bool, optional
        Whether the mentionable select menu is disabled, by default False
    row : Optional[int], optional
        The row the select should be in, leave as None for auto-placement.

    Returns
    -------
    Callable[[Callable[[ScreenT, ScreenMentionableSelect, ViewContextT], Awaitable[None]]], DecoratedItem[ScreenMentionableSelect]]
        The decorated function.

    Raises
    ------
    TypeError
        If the decorated function is not a coroutine function.
    """

    def decorator(
        func: t.Callable[[ScreenT, ScreenMentionableSelect, ViewContextT], t.Awaitable[None]],
    ) -> DecoratedItem[ScreenMentionableSelect]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("mentionable_select must decorate coroutine function.")

        item = ScreenMentionableSelect(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        return DecoratedItem(item, func)

    return decorator


def role_select(
    *,
    custom_id: t.Optional[str] = None,
    placeholder: t.Optional[str] = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: t.Optional[int] = None,
) -> t.Callable[
    [t.Callable[[ScreenT, ScreenRoleSelect, ViewContextT], t.Awaitable[None]]], DecoratedItem[ScreenRoleSelect]
]:
    """
    A decorator to transform a function into a Discord UI RoleSelectMenu's callback.
    This must be inside a subclass of Screen.

    Parameters
    ----------
    custom_id : Optional[str], optional
        The custom ID for the RoleSelectMenu, by default None
    placeholder : Optional[str], optional
        The placeholder text to display when no roles are selected, by default None
    min_values : int, optional
        The minimum number of roles that can be selected, by default 1
    max_values : int, optional
        The maximum number of roles that can be selected, by default 1
    disabled : bool, optional
        Whether the RoleSelectMenu is disabled or not, by default False
    row : Optional[int], optional
        The row number to place the RoleSelectMenu in, by default None

    Returns
    -------
    Callable[[Callable[[ScreenT, ScreenRoleSelect, ViewContextT], Awaitable[None]]], DecoratedItem[ScreenRoleSelect]]
        The decorated function that serves as the callback for the RoleSelectMenu.

    Raises
    ------
    TypeError
        If the decorated function is not a coroutine function.
    """

    def decorator(
        func: t.Callable[[ScreenT, ScreenRoleSelect, ViewContextT], t.Awaitable[None]],
    ) -> DecoratedItem[ScreenRoleSelect]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("role_select must decorate coroutine function.")

        item = ScreenRoleSelect(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        return DecoratedItem(item, func)

    return decorator


def text_select(
    *,
    options: t.Sequence[t.Union[hikari.SelectMenuOption, miru.SelectOption]],
    custom_id: t.Optional[str] = None,
    placeholder: t.Optional[str] = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: t.Optional[int] = None,
) -> t.Callable[
    [t.Callable[[ScreenT, ScreenTextSelect, ViewContextT], t.Awaitable[None]]], DecoratedItem[ScreenTextSelect]
]:
    """
    A decorator to transform a function into a Discord UI TextSelectMenu's callback.
    This must be inside a subclass of View.
    """

    def decorator(
        func: t.Callable[[ScreenT, ScreenTextSelect, ViewContextT], t.Awaitable[None]],
    ) -> DecoratedItem[ScreenTextSelect]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("text_select must decorate coroutine function.")

        item = ScreenTextSelect(
            options=options,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        return DecoratedItem(item, func)

    return decorator


def user_select(
    *,
    custom_id: t.Optional[str] = None,
    placeholder: t.Optional[str] = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: t.Optional[int] = None,
) -> t.Callable[
    [t.Callable[[ScreenT, ScreenUserSelect, ViewContextT], t.Awaitable[None]]], DecoratedItem[ScreenUserSelect]
]:
    """
    A decorator to transform a function into a Discord UI UserSelectMenu's callback.
    This must be inside a subclass of View.
    """

    def decorator(
        func: t.Callable[[ScreenT, ScreenUserSelect, ViewContextT], t.Awaitable[None]],
    ) -> DecoratedItem[ScreenUserSelect]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("user_select must decorate coroutine function.")

        item = ScreenUserSelect(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        return DecoratedItem(item, func)

    return decorator
