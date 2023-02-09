from __future__ import annotations

import inspect
import typing as t

import hikari

from ..abc.item import DecoratedItem
from ..context.view import ViewContext
from .base import SelectBase

if t.TYPE_CHECKING:
    from ..context.base import Context
    from ..view import View

    ViewT = t.TypeVar("ViewT", bound="View")

__all__ = ("UserSelect", "user_select")


class UserSelect(SelectBase):
    """A view component representing a select menu of users.

    Parameters
    ----------
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
        self._values: t.Sequence[hikari.User] = []

    @property
    def type(self) -> hikari.ComponentType:
        return hikari.ComponentType.USER_SELECT_MENU

    @property
    def values(self) -> t.Sequence[hikari.User]:
        """The currently selected user objects.
        Some users may also be instances of ``hikari.InteractionMember``, depending on how they were resolved."""
        return self._values

    @classmethod
    def _from_component(cls, component: hikari.PartialComponent, row: t.Optional[int] = None) -> UserSelect:
        assert (
            isinstance(component, hikari.components.SelectMenuComponent)
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
        """
        Called internally to build and append to an action row
        """
        select = action_row.add_select_menu(hikari.ComponentType.USER_SELECT_MENU, self.custom_id)
        if self.placeholder:
            select.set_placeholder(self.placeholder)
        select.set_min_values(self.min_values)
        select.set_max_values(self.max_values)
        select.set_is_disabled(self.disabled)

        select.add_to_container()

    async def _refresh_state(self, context: Context[t.Any]) -> None:
        if context.interaction.resolved is None:
            self._values = ()
            return

        values = []
        for user in context.interaction.resolved.users.values():
            if member := context.interaction.resolved.members.get(user.id):
                values.append(member)
            else:
                values.append(user)
        self._values = tuple(values)


def user_select(
    *,
    custom_id: t.Optional[str] = None,
    placeholder: t.Optional[str] = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: t.Optional[int] = None,
) -> t.Callable[[t.Callable[[ViewT, UserSelect, ViewContext], t.Any]], UserSelect]:
    """
    A decorator to transform a function into a Discord UI UserSelectMenu's callback. This must be inside a subclass of View.
    """

    def decorator(func: t.Callable[..., t.Any]) -> t.Any:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("user_select must decorate coroutine function.")

        item = UserSelect(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        return DecoratedItem(item, func)

    return decorator
