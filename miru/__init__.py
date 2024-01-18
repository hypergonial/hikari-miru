"""A component handler for hikari, with support for modals and views.

GitHub:
https://github.com/hypergonial/hikari-miru

Documentation:
https://miru.hypergonial.com
"""

from alluka import Client as Injector
from alluka import inject

from miru import abc, ext, select
from miru.abc.context import InteractionResponse
from miru.button import Button, LinkButton, button
from miru.client import Client
from miru.context import AutodeferMode, AutodeferOptions, ModalContext, ViewContext
from miru.exceptions import HandlerFullError, ItemAlreadyAttachedError, MiruError, RowFullError
from miru.internal.about import __author__, __author_email__, __license__, __maintainer__, __url__, __version__
from miru.modal import Modal
from miru.response import DeferredResponseBuilder, MessageBuilder, ModalBuilder
from miru.select import (
    ChannelSelect,
    MentionableSelect,
    RoleSelect,
    SelectOption,
    TextSelect,
    UserSelect,
    channel_select,
    mentionable_select,
    role_select,
    text_select,
    user_select,
)
from miru.text_input import TextInput
from miru.view import View

__all__ = (
    "Injector",
    "inject",
    "abc",
    "ext",
    "select",
    "Client",
    "InteractionResponse",
    "ModalContext",
    "View",
    "ViewContext",
    "ModalContext",
    "Button",
    "LinkButton",
    "button",
    "MiruError",
    "RowFullError",
    "HandlerFullError",
    "ItemAlreadyAttachedError",
    "Modal",
    "SelectOption",
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
    "MessageBuilder",
    "ModalBuilder",
    "DeferredResponseBuilder",
    "AutodeferMode",
    "AutodeferOptions",
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
