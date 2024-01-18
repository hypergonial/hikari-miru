from __future__ import annotations

import copy
import os
import sys
import traceback
import typing as t

import hikari

from miru.abc.item import ModalItem
from miru.abc.item_handler import ItemHandler
from miru.context.modal import ModalContext
from miru.exceptions import HandlerFullError
from miru.internal.types import ModalResponseBuildersT
from miru.response import ModalBuilder

if t.TYPE_CHECKING:
    import asyncio
    import datetime

    import typing_extensions as te

    from miru.client import Client

__all__ = ("Modal",)


class Modal(
    ItemHandler[
        hikari.impl.ModalActionRowBuilder, ModalResponseBuildersT, ModalContext, hikari.ModalInteraction, ModalItem
    ]
):
    """Represents a Discord Modal.

    Parameters
    ----------
    title : str
        The title of the modal, appears on the top of the modal dialog box.
    custom_id : str
        The custom identifier of the modal, identifies the modal through interactions.
    timeout : Optional[Union[float, int, datetime.timedelta]]
        The duration after which the modal times out, in seconds

    Raises
    ------
    HandlerFullError
        Raised if the modal has more than 25 components attached.
    """

    _modal_children: t.Mapping[str, ModalItem] = {}

    def __init_subclass__(cls) -> None:
        """Get ModalItem classvars."""
        children: t.MutableMapping[str, ModalItem] = {}
        for base_cls in reversed(cls.mro()):
            for name, value in base_cls.__dict__.items():
                if isinstance(value, ModalItem):
                    children[name] = value

        if len(children) > 25:
            raise HandlerFullError("Modal cannot have more than 25 components attached.")
        cls._modal_children = children

    def __init__(
        self, title: str, *, custom_id: str | None = None, timeout: float | int | datetime.timedelta | None = 300.0
    ) -> None:
        super().__init__(timeout=timeout)

        self._title: str = title
        self._custom_id: str = custom_id or os.urandom(16).hex()
        self._values: t.Mapping[ModalItem, str] | None = None

        if len(self._title) > 100:
            raise ValueError("Modal title is too long. Maximum 100 characters.")

        if len(self._custom_id) > 100:
            raise ValueError("Modal custom_id is too long. Maximum 100 characters.")

        for name, item in self._modal_children.items():
            copied = copy.deepcopy(item)
            self.add_item(copied)
            setattr(self, name, copied)

    @property
    def title(self) -> str:
        """The title of this modal. Will be displayed on the top of the modal prompt."""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        if len(value) > 100:
            raise ValueError("Modal title is too long. Maximum 100 characters.")

        self._title = value

    @property
    def custom_id(self) -> str:
        """The custom identifier of this modal. Interactions belonging to it are tracked by this ID."""
        return self._custom_id

    @custom_id.setter
    def custom_id(self, value: str) -> None:
        if len(value) > 100:
            raise ValueError("Modal custom_id is too long. Maximum 100 characters.")

        self._custom_id = value

    @property
    def values(self) -> t.Mapping[ModalItem, str] | None:
        """The input values received by this modal."""
        return self._values

    @property
    def _builder(self) -> type[hikari.impl.ModalActionRowBuilder]:
        return hikari.impl.ModalActionRowBuilder

    def add_item(self, item: ModalItem) -> te.Self:
        """Adds a new item to the modal.

        Parameters
        ----------
        item : ModalItem
            An instance of ModalItem to be added.

        Raises
        ------
        TypeError
            item is not of type ModalItem.
        ValueError
            The modal already has 25 components attached.
        TypeError
            Parameter item is not an instance of ModalItem.
        RuntimeError
            The item is already attached to this view.
        RuntimeError
            The item is already attached to another view.

        Returns
        -------
        ItemHandler
            The item handler the item was added to.
        """
        return super().add_item(item)

    async def modal_check(self, context: ModalContext, /) -> bool:
        """Called before any callback in the modal is called. Must evaluate to a truthy value to pass.
        Override for custom check logic.

        Parameters
        ----------
        context : Context
            The context for this check.

        Returns
        -------
        bool
            A boolean indicating if the check passed or not.
        """
        return True

    async def on_error(self, error: Exception, context: ModalContext | None = None, /) -> None:
        """Called when an error occurs in a callback function.
        Override for custom error-handling logic.

        Parameters
        ----------
        error : Exception
            The exception encountered.
        context : Optional[Context]
            The context associated with this exception, if any.
        """
        print(f"Ignoring exception in modal {self}:", file=sys.stderr)

        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    async def callback(self, context: ModalContext, /) -> None:
        """Called when the modal is submitted.

        Parameters
        ----------
        context : ModalContext
            The context that belongs to this interaction callback.
        """
        pass

    async def _handle_callback(self, context: ModalContext) -> None:
        """Handle the callback of the modal. Separate task in case the modal is stopped in the callback."""
        try:
            await self.callback(context)
        except Exception as error:
            await self.on_error(error, context)

        self.stop()  # Modals can only receive one response

    async def _invoke(self, interaction: hikari.ModalInteraction) -> asyncio.Future[ModalResponseBuildersT] | None:
        children = {item.custom_id: item for item in self.children}

        values = {  # Check if any components match the provided custom_ids
            children[component.custom_id]: component.value
            for action_row in interaction.components
            for component in action_row.components
            if children.get(component.custom_id) is not None
        }
        if not values:
            return

        self._values = values

        context = ModalContext(self, self.client, interaction, values)
        self._last_context = context

        passed = await self.modal_check(context)
        if not passed:
            return

        for item in self.children:
            await item._refresh_state(context)

        self._create_task(self._handle_callback(context))

        if self.client.is_rest:
            # The alternative would be making Context generic over ResponseBuildersT
            # I can't take it anymore
            return context._resp_builder  # type: ignore

    def _client_start_hook(self, client: Client) -> None:
        """Called when the client adds the modal to itself."""
        self._client = client
        self._client._add_handler(self)
        self._timeout_task = self._create_task(self._handle_timeout())

    def build_response(self, client: Client) -> ModalBuilder:
        """Build the modal response for this modal."""
        builder = ModalBuilder(self.title, self.custom_id, list(self.build()))
        builder._client = client
        return builder


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
