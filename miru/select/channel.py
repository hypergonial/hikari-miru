from __future__ import annotations

import inspect
import typing as t

import hikari

from ..abc.item import DecoratedItem
from .base import SelectBase

if t.TYPE_CHECKING:
    from ..context.base import Context
    from ..context.view import ViewContext
    from ..view import View

    ViewT = t.TypeVar("ViewT", bound="View")
    ViewContextT = t.TypeVar("ViewContextT", bound=ViewContext)

__all__ = ("ChannelSelect", "channel_select")


class ChannelSelect(SelectBase):
    """A view component representing a select menu of channels.

    Parameters
    ----------
    channel_types : Sequence[Union[int, hikari.ChannelType]], optional
        A sequence of channel types to filter the select menu by, by default (hikari.ChannelType.GUILD_TEXT,)
    custom_id : Optional[str], optional
        The custom identifier of the select menu, by default None
    placeholder : Optional[str], optional
        Placeholder text displayed on the select menu, by default None
    min_values : int, optional
        The minimum values a user has to select before it can be sent, by default 1
    max_values : int, optional
        The maximum values a user can select, by default 1
    disabled : bool, optional
        A boolean determining if the select menu should be disabled or not, by default False
    row : Optional[int], optional
        The row the select menu should be in, leave as None for auto-placement.
    """

    def __init__(
        self,
        *,
        channel_types: t.Sequence[hikari.ChannelType] = (hikari.ChannelType.GUILD_TEXT,),
        custom_id: t.Optional[str] = None,
        placeholder: t.Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: t.Optional[int] = None,
    ) -> None:
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        self.channel_types = channel_types
        self._values: t.Sequence[hikari.InteractionChannel] = []

    @property
    def channel_types(self) -> t.Sequence[hikari.ChannelType]:
        """The valid channel types that can be selected from the select menu."""
        return self._channel_types

    @channel_types.setter
    def channel_types(self, value: t.Sequence[hikari.ChannelType]) -> None:
        self._channel_types = tuple(value)

    @property
    def type(self) -> hikari.ComponentType:
        return hikari.ComponentType.CHANNEL_SELECT_MENU

    @property
    def values(self) -> t.Sequence[hikari.InteractionChannel]:
        """The currently selected channels."""
        return self._values

    @classmethod
    def _from_component(cls, component: hikari.PartialComponent, row: t.Optional[int] = None) -> ChannelSelect:
        assert isinstance(component, hikari.ChannelSelectMenuComponent)

        # Filter out unrecognized channel types
        channel_types = [item for item in component.channel_types if isinstance(item, hikari.ChannelType)]

        return cls(
            channel_types=channel_types,
            custom_id=component.custom_id,
            placeholder=component.placeholder,
            min_values=component.min_values,
            max_values=component.max_values,
            disabled=component.is_disabled,
            row=row,
        )

    def _build(self, action_row: hikari.api.MessageActionRowBuilder) -> None:
        action_row.add_channel_menu(
            self.custom_id,
            placeholder=self.placeholder or hikari.UNDEFINED,
            min_values=self.min_values,
            max_values=self.max_values,
            is_disabled=self.disabled,
            channel_types=self.channel_types,
        )

    async def _refresh_state(self, context: Context[t.Any]) -> None:
        hikari.ComponentInteraction
        if context.interaction.resolved is None:
            self._values = ()
            return
        self._values = tuple(context.interaction.resolved.channels.values())


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
    [t.Callable[[ViewT, ChannelSelect, ViewContextT], t.Awaitable[None]]],
    DecoratedItem[ViewT, ChannelSelect, ViewContextT],
]:
    """A decorator to transform a function into a Discord UI ChannelSelectMenu's callback.
    This must be inside a subclass of View.

    Parameters
    ----------
    channel_types : Sequence[Union[int, hikari.ChannelType]], optional
        A sequence of channel types to filter the select menu by. Defaults to (hikari.ChannelType.GUILD_TEXT,).
    custom_id : Optional[str], optional
        The custom ID of the select menu. Defaults to None.
    placeholder: Optional[str], optional
        The placeholder to display when nothing is selected. Defaults to None.
    min_values : int, optional
        The minimum number of values that can be selected. Defaults to 1.
    max_values : int, optional
        The maximum number of values that can be selected. Defaults to 1.
    disabled : bool, optional
        Whether the select menu is disabled. Defaults to False.
    row : Optional[int], optional
        The row the select should be in, leave as None for auto-placement.

    Returns
    -------
    Callable[[Callable[[ViewT, ChannelSelect, ViewContextT], Awaitable[None]]], DecoratedItem[ViewT, ChannelSelect, ViewContextT]]
        The decorated function.

    Raises
    ------
    TypeError
        If the decorated function is not a coroutine function.

    """

    def decorator(
        func: t.Callable[[ViewT, ChannelSelect, ViewContextT], t.Awaitable[None]],
    ) -> DecoratedItem[ViewT, ChannelSelect, ViewContextT]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("channel_select must decorate coroutine function.")

        item = ChannelSelect(
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
