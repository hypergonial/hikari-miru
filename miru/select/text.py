from __future__ import annotations

import inspect
import typing as t

import hikari

from ..abc.item import DecoratedItem
from ..abc.item import ViewItem
from ..context.view import ViewContext
from .base import SelectBase

if t.TYPE_CHECKING:
    from ..context.base import Context
    from ..view import View

    ViewT = t.TypeVar("ViewT", bound="View")

__all__ = ("SelectOption", "TextSelect", "text_select")


class SelectOption:
    """
    A more lenient way to instantiate select options.
    """

    __slots__ = ("label", "value", "description", "emoji", "is_default")

    def __init__(
        self,
        label: str,
        value: t.Optional[str] = None,
        description: t.Optional[str] = None,
        emoji: t.Optional[t.Union[str, hikari.Emoji]] = None,
        is_default: bool = False,
    ) -> None:
        """A more lenient way to instantiate select options.

        Parameters
        ----------
        label : str
            The option's label.
        value : Optional[str], optional
            The internal value of the option, if None, uses label.
        description : Optional[str], optional
            The description of the option, by default None
        emoji : Optional[Union[str, hikari.Emoji]], optional
            The emoji of the option, by default None
        is_default : bool, optional
            A boolean determining of the option is default or not, by default False
        """
        self.label: str = label
        self.value: str = value or label
        self.description: t.Optional[str] = description
        if isinstance(emoji, str):
            emoji = hikari.Emoji.parse(emoji)
        self.emoji: t.Optional[hikari.Emoji] = emoji
        self.is_default: bool = is_default

    def _convert(self) -> hikari.SelectMenuOption:
        return hikari.SelectMenuOption(
            label=self.label,
            value=self.value,
            description=self.description,
            emoji=self.emoji,
            is_default=self.is_default,
        )


class TextSelect(SelectBase):
    """A view component representing a text select menu.

    Parameters
    ----------
    options : Sequence[Union[hikari.SelectMenuOption, SelectOption]]
        A sequence of select menu options that this select menu should use.
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

    Raises
    ------
    ValueError
        Exceeded the maximum of 25 select menu options possible.
    """

    def __init__(
        self,
        *,
        options: t.Sequence[t.Union[hikari.SelectMenuOption, SelectOption]],
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
        self._values: t.Sequence[str] = []
        self.options = options

    @property
    def type(self) -> hikari.ComponentType:
        return hikari.ComponentType.TEXT_SELECT_MENU

    @property
    def placeholder(self) -> t.Optional[str]:
        """
        The placeholder text that appears before the select menu is clicked.
        """
        return self._placeholder

    @placeholder.setter
    def placeholder(self, value: t.Optional[str]) -> None:
        if value and not isinstance(value, str):
            raise TypeError("Expected type str for property placeholder.")
        if value is not None and len(value) > 150:
            raise ValueError(f"Parameter 'placeholder' must be 150 or fewer in length. (Found length {len(value)})")
        self._placeholder = str(value) if value else None

    @property
    def options(self) -> t.Sequence[t.Union[hikari.SelectMenuOption, SelectOption]]:
        """
        The select menu's options.
        """
        return self._options

    @options.setter
    def options(self, value: t.Sequence[t.Union[hikari.SelectMenuOption, SelectOption]]) -> None:
        if not isinstance(value, t.Sequence) or not isinstance(value[0], (hikari.SelectMenuOption, SelectOption)):
            raise TypeError(
                "Expected type 'Sequence[Union[hikari.SelectMenuOption, SelectOption]]' for property 'options'."
            )

        if len(value) > 25:
            raise ValueError("A select can have a maximum of 25 options.")

        self._options = value

    @classmethod
    def _from_component(cls, component: hikari.PartialComponent, row: t.Optional[int] = None) -> TextSelect:
        assert isinstance(component, hikari.components.TextSelectMenuComponent)

        return cls(
            options=component.options,
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
        select = action_row.add_select_menu(hikari.ComponentType.TEXT_SELECT_MENU, self.custom_id)
        if self.placeholder:
            select.set_placeholder(self.placeholder)
        select.set_min_values(self.min_values)
        select.set_max_values(self.max_values)
        select.set_is_disabled(self.disabled)

        for option in self.options:
            if isinstance(option, SelectOption):
                option = option._convert()

            option_builder = select.add_option(option.label, option.value)
            option_builder.set_is_default(option.is_default)
            if option.description:
                option_builder.set_description(option.description)
            if option.emoji:
                option_builder.set_emoji(option.emoji)

            option_builder.add_to_menu()

        select.add_to_container()

    @property
    def values(self) -> t.Sequence[str]:
        return self._values

    @property
    def width(self) -> int:
        return 5

    async def _refresh_state(self, context: Context[hikari.ComponentInteraction]) -> None:
        assert isinstance(context, ViewContext)
        self._values = context.interaction.values


def text_select(
    *,
    options: t.Sequence[t.Union[hikari.SelectMenuOption, SelectOption]],
    custom_id: t.Optional[str] = None,
    placeholder: t.Optional[str] = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: t.Optional[int] = None,
) -> t.Callable[[t.Callable[[ViewT, TextSelect, ViewContext], t.Any]], TextSelect]:
    """
    A decorator to transform a function into a Discord UI TextSelectMenu's callback. This must be inside a subclass of View.
    """

    def decorator(func: t.Callable[..., t.Any]) -> t.Any:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("text_select must decorate coroutine function.")

        item = TextSelect(
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
