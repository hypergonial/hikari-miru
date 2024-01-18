from __future__ import annotations

import abc
import copy
import typing as t

import attr
import hikari

from miru.exceptions import HandlerFullError, ItemAlreadyAttachedError
from miru.ext.menu.items import DecoratedScreenItem, InteractiveScreenItem, ScreenItem

if t.TYPE_CHECKING:
    import typing_extensions as te

    from miru.ext.menu.menu import Menu

__all__ = ("ScreenContent", "Screen")


@attr.define(slots=True)
class ScreenContent:
    """The content payload of an individual menu screen."""

    content: hikari.UndefinedOr[t.Any] = hikari.UNDEFINED
    """The content of the message. Anything passed here will be cast to str."""
    attachment: hikari.UndefinedOr[hikari.Resourceish] = hikari.UNDEFINED
    """An attachment to add to this page."""
    attachments: hikari.UndefinedOr[t.Sequence[hikari.Resourceish]] = hikari.UNDEFINED
    """A sequence of attachments to add to this page."""
    embed: hikari.UndefinedOr[hikari.Embed] = hikari.UNDEFINED
    """An embed to add to this page."""
    embeds: hikari.UndefinedOr[t.Sequence[hikari.Embed]] = hikari.UNDEFINED
    """A sequence of embeds to add to this page."""
    mentions_everyone: hikari.UndefinedOr[bool] = hikari.UNDEFINED
    """If True, mentioning @everyone will be allowed in this page's message."""
    user_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialUser] | bool] = hikari.UNDEFINED
    """The set of allowed user mentions in this page's message. Set to True to allow all."""
    role_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialRole] | bool] = hikari.UNDEFINED
    """The set of allowed role mentions in this page's message. Set to True to allow all."""

    def _build_payload(self) -> dict[str, t.Any]:
        d: dict[str, t.Any] = {
            "content": self.content or None,
            "attachments": self.attachments or None,
            "embeds": self.embeds or None,
            "mentions_everyone": self.mentions_everyone or False,
            "user_mentions": self.user_mentions or False,
            "role_mentions": self.role_mentions or False,
        }
        if not d["attachments"] and self.attachment:
            d["attachments"] = [self.attachment]

        if not d["embeds"] and self.embed:
            d["embeds"] = [self.embed]

        return d


class Screen(abc.ABC):
    """A screen in a menu. Acts similarly to a View, although it is not a subclass of it.

    Parameters
    ----------
    menu : Menu
        The menu that this screen belongs to.
    """

    _screen_children: t.Sequence[
        DecoratedScreenItem[te.Self, InteractiveScreenItem]
    ] = []  # Decorated callbacks that need to be turned into items

    def __init_subclass__(cls) -> None:
        """Get decorated callbacks."""
        children: t.MutableSequence[DecoratedScreenItem[te.Self, InteractiveScreenItem]] = []
        for base_cls in reversed(cls.mro()):
            for value in base_cls.__dict__.values():
                if isinstance(value, DecoratedScreenItem):
                    children.append(value)  # type: ignore

        if len(children) > 25:
            raise HandlerFullError("View cannot have more than 25 components attached.")

        cls._screen_children = children

    def __init__(self, menu: Menu) -> None:
        self._menu = menu
        self._children: t.MutableSequence[ScreenItem] = []

        for decorated_item in self._screen_children:
            # Must deepcopy, otherwise multiple views will have the same item reference
            decorated_item = copy.deepcopy(decorated_item)
            item = decorated_item.build(self)
            self.add_item(item)
            setattr(self, decorated_item.name, item)

    @property
    def menu(self) -> Menu:
        """The menu that this screen belongs to."""
        return self._menu

    @property
    def children(self) -> t.Sequence[ScreenItem]:
        """The items contained in this screen."""
        return self._children

    @abc.abstractmethod
    async def build_content(self) -> ScreenContent:
        """Build the content payload for this screen.
        This function is called whenever the screen comes into view.

        Returns
        -------
        ScreenContent
            The content payload for this screen.
        """

    async def on_dispose(self) -> None:
        """Called when this screen is disposed.
        This happens when the menu navigates away from this screen.

        Note that this is not the same as the screen being
        removed from the menu, although it can be.
        """

    async def on_error(self, error: Exception) -> None:
        """Called when an exception is raised in build_content or on_dispose.

        Parameters
        ----------
        error : Exception
            The exception that was raised.
        """
        raise error

    def add_item(self, item: ScreenItem) -> te.Self:
        """Adds a new item to the screen.

        Parameters
        ----------
        item : ViewItem
            The item to be added.

        Raises
        ------
        ValueError
            ItemHandler already has 25 components attached.
        TypeError
            Parameter item is not an instance of ViewItem.
        ItemAlreadyAttachedError
            The item is already attached to this item handler.

        Returns
        -------
        Screen
            The item handler the item was added to.
        """
        if len(self.children) > 25:
            raise HandlerFullError("Screen cannot have more than 25 components attached.")

        if item in self.children:
            raise ItemAlreadyAttachedError(f"Item {type(item).__name__} is already attached to this screen.")

        self._children.append(item)
        item._screen = self

        return self

    def remove_item(self, item: ScreenItem) -> te.Self:
        """Removes the specified item from the screen.

        Parameters
        ----------
        item : ViewItem
            The item to be removed.

        Returns
        -------
        Screen
            The item handler the item was removed from.
        """
        try:
            self._children.remove(item)
            item._screen = None
        except ValueError:
            pass

        return self

    def clear_items(self) -> te.Self:
        """Removes all items from this item handler.

        Returns
        -------
        Screen
            The item handler items were cleared from.
        """
        for item in self.children:
            item._screen = None

        self._children.clear()
        return self

    def get_item_by(self, predicate: t.Callable[[ScreenItem], bool]) -> ScreenItem | None:
        """Get the first item that matches the given predicate.

        Parameters
        ----------
        predicate : Callable[[ScreenItem], bool]
            A predicate to match the item.

        Returns
        -------
        Optional[ScreenItem]
            The item that matched the predicate or None.
        """
        for item in self.children:
            if predicate(item):
                return item

        return None

    def get_item_by_id(self, custom_id: str) -> ScreenItem | None:
        """Get the first item with the given custom ID.

        Parameters
        ----------
        custom_id : str
            The custom_id of the component.

        Returns
        -------
        Optional[ScreenItem]
            The item with the given custom ID or None.
        """
        return self.get_item_by(lambda item: item.custom_id == custom_id)


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
