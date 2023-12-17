"""A component handler for hikari, with support for modals and views.

To get started, you will want to call `miru.install` with an instance of your bot.

GitHub:
https://github.com/hypergonial/hikari-miru

Documentation:
https://hikari-miru.readthedocs.io/
"""

from .bootstrap import install, uninstall
from .button import Button, button
from .context import Context, InteractionResponse, ModalContext, RawComponentContext, RawModalContext, ViewContext
from .events import ComponentInteractionCreateEvent, Event, ModalInteractionCreateEvent
from .exceptions import BootstrapFailureError, HandlerFullError, ItemAlreadyAttachedError, MiruException, RowFullError
from .internal.about import __author__, __author_email__, __license__, __maintainer__, __url__, __version__
from .modal import Modal
from .select import (
    ChannelSelect,
    MentionableSelect,
    RoleSelect,
    SelectBase,
    SelectOption,
    TextSelect,
    UserSelect,
    channel_select,
    mentionable_select,
    role_select,
    text_select,
    user_select,
)
from .text_input import TextInput
from .traits import MiruAware
from .view import View, get_view

__all__ = (
    "Context",
    "InteractionResponse",
    "ModalContext",
    "RawComponentContext",
    "ViewContext",
    "ModalContext",
    "RawModalContext",
    "install",
    "uninstall",
    "Button",
    "button",
    "Event",
    "ComponentInteractionCreateEvent",
    "ModalInteractionCreateEvent",
    "MiruException",
    "BootstrapFailureError",
    "RowFullError",
    "HandlerFullError",
    "ItemAlreadyAttachedError",
    "Modal",
    "SelectOption",
    "SelectBase",
    "TextSelect",
    "text_select",
    "ChannelSelect",
    "channel_select",
    "RoleSelect",
    "role_select",
    "UserSelect",
    "user_select",
    "MentionableSelect",
    "mentionable_select",
    "TextInput",
    "MiruAware",
    "View",
    "get_view",
    "__version__",
    "__author__",
    "__author_email__",
    "__license__",
    "__url__",
    "__maintainer__",
)

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
