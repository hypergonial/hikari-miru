__all__ = ("MiruError", "RowFullError", "HandlerFullError", "ItemAlreadyAttachedError")


class MiruError(Exception):
    """Base class for all miru exceptions."""


class RowFullError(MiruError):
    """Raised when a row of components is full and cannot be added to."""


class HandlerFullError(MiruError):
    """Raised when an ItemHandler instance is full and cannot fit more components."""


class ItemAlreadyAttachedError(MiruError):
    """Raised when an item is already attached to a handler and the requested operation is not possible because of it."""


class NoResponseIssuedError(MiruError):
    """Raised when no response was issued by a handler.
    Interactions must be responded to or deferred within 3 seconds to avoid this error.

    `miru` tries to automatically defer responses when possible, so this error should rarely occur, unless autodefer is disabled.
    """


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
