from __future__ import annotations

import inspect
import typing as t

import hikari

from miru.abc.item import DecoratedItem
from miru.abc.select import SelectBase

if t.TYPE_CHECKING:
    import typing_extensions as te

    from miru.context.view import AutodeferOptions, ViewContext
    from miru.view import View

    ViewT = t.TypeVar("ViewT", bound="View")

__all__ = ("UserSelect", "user_select")


class UserSelect(SelectBase):
    """A view component representing a select menu of users.

    Parameters
    ----------
    custom_id : str | None
        The custom identifier of the select menu
    placeholder : str | None
        Placeholder text displayed on the select menu
    min_values : int
        The minimum values a user has to select before it can be sent
    max_values : int
        The maximum values a user can select
    disabled : bool
        A boolean determining if the select menu should be disabled or not
    row : int | None
        The row the select menu should be in, leave as None for auto-placement.
    autodefer : bool | AutodeferOptions | hikari.UndefinedType
        The autodefer options for the select menu. If left `UNDEFINED`, the view's autodefer options will be used.
    """

    def __init__(
        self,
        *,
        custom_id: str | None = None,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: int | None = None,
        autodefer: bool | AutodeferOptions | hikari.UndefinedType = hikari.UNDEFINED,
    ) -> None:
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
            autodefer=autodefer,
        )
        self._values: t.Sequence[hikari.User] = []

    @property
    def type(self) -> hikari.ComponentType:
        return hikari.ComponentType.USER_SELECT_MENU

    @property
    def values(self) -> t.Sequence[hikari.User]:
        """The currently selected user objects.
        Some users may also be instances of ``hikari.InteractionMember``, depending on how they were resolved.
        """
        return self._values

    @classmethod
    def _from_component(cls, component: hikari.PartialComponent, row: int | None = None) -> te.Self:
        assert (
            isinstance(component, hikari.SelectMenuComponent)
            and component.type == hikari.ComponentType.USER_SELECT_MENU
        )

        return cls(
            custom_id=component.custom_id,
            placeholder=component.placeholder,
            min_values=component.min_values,
            max_values=component.max_values,
            disabled=component.is_disabled,
            row=row,
        )

    def _build(self, action_row: hikari.api.MessageActionRowBuilder) -> None:
        action_row.add_select_menu(
            hikari.ComponentType.USER_SELECT_MENU,
            self.custom_id,
            placeholder=self.placeholder or hikari.UNDEFINED,
            min_values=self.min_values,
            max_values=self.max_values,
            is_disabled=self.disabled,
        )

    async def _refresh_state(self, context: ViewContext) -> None:
        if context.interaction.resolved is None:
            self._values = ()
            return

        values: list[hikari.User] = []
        for user in context.interaction.resolved.users.values():
            if member := context.interaction.resolved.members.get(user.id):
                values.append(member)
            else:
                values.append(user)
        self._values = tuple(values)


def user_select(
    *,
    custom_id: str | None = None,
    placeholder: str | None = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: int | None = None,
    autodefer: bool | AutodeferOptions | hikari.UndefinedType = hikari.UNDEFINED,
) -> t.Callable[[t.Callable[[ViewT, ViewContext, UserSelect], t.Awaitable[None]]], DecoratedItem[ViewT, UserSelect]]:
    """A decorator to transform a function into a Discord UI UserSelectMenu's callback.
    This must be inside a subclass of View.

    Parameters
    ----------
    custom_id : str | None
        The custom ID of the select menu
    placeholder : str | None
        Placeholder text displayed on the select menu
    min_values : int
        The minimum number of values that can be selected.
    max_values : int
        The maximum number of values that can be selected.
    disabled : bool
        Whether the select menu is disabled.
    row : int | None
        The row the select should be in, leave as None for auto-placement.
    autodefer : bool | AutodeferOptions | hikari.UndefinedType
        The autodefer options for the select menu. If left `UNDEFINED`, the view's autodefer options will be used.

    Returns
    -------
    Callable[[Callable[[ViewT, ViewContext, UserSelect], Awaitable[None]]], DecoratedItem[ViewT, UserSelect]]
        The decorated function.

    Raises
    ------
    TypeError
        If the decorated function is not a coroutine function.
    """

    def decorator(
        func: t.Callable[[ViewT, ViewContext, UserSelect], t.Awaitable[None]],
    ) -> DecoratedItem[ViewT, UserSelect]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("user_select must decorate coroutine function.")

        item: UserSelect = UserSelect(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
            autodefer=autodefer,
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
