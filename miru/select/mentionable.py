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

__all__ = ("MentionableSelect", "mentionable_select")


class MentionableSelect(SelectBase):
    """A view component representing a select menu of mentionables.

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
        self._values = hikari.ResolvedOptionData(
            attachments={}, channels={}, messages={}, members={}, roles={}, users={}
        )

    @property
    def type(self) -> hikari.ComponentType:
        return hikari.ComponentType.MENTIONABLE_SELECT_MENU

    @property
    def values(self) -> t.Optional[hikari.ResolvedOptionData]:
        """The currently selected mentionable objects.

        This is returned as a `hikari.ResolvedOptionData` object. You can access each type of mentionable object by using the following attributes:

        - `values.users` - All user objects selected
        - `values.roles` - All role objects selected
        - `values.channels` - All channel objects selected
        - `values.members` - All member objects selected
        """
        return self._values

    @classmethod
    def _from_component(cls, component: hikari.PartialComponent, row: t.Optional[int] = None) -> MentionableSelect:
        assert (
            isinstance(component, hikari.components.ChannelSelectMenuComponent)
            and component.type == hikari.ComponentType.MENTIONABLE_SELECT_MENU
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
        select = action_row.add_select_menu(hikari.ComponentType.MENTIONABLE_SELECT_MENU, self.custom_id)
        if self.placeholder:
            select.set_placeholder(self.placeholder)
        select.set_min_values(self.min_values)
        select.set_max_values(self.max_values)
        select.set_is_disabled(self.disabled)

        select.add_to_container()

    async def _refresh_state(self, context: Context[t.Any]) -> None:
        self._values = context.interaction.resolved


def mentionable_select(
    *,
    custom_id: t.Optional[str] = None,
    placeholder: t.Optional[str] = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: t.Optional[int] = None,
) -> t.Callable[[t.Callable[[ViewT, MentionableSelect, ViewContext], t.Any]], MentionableSelect]:
    """
    A decorator to transform a function into a Discord UI MentionableSelectMenu's callback. This must be inside a subclass of View.
    """

    def decorator(func: t.Callable[..., t.Any]) -> t.Any:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("mentionable_select must decorate coroutine function.")

        item = MentionableSelect(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        return DecoratedItem(item, func)

    return decorator
