__all__ = ("MiruException", "BootstrapFailureError", "RowFullError", "HandlerFullError", "ItemAlreadyAttachedError")


class MiruException(Exception):
    """Base class for all miru exceptions."""


class BootstrapFailureError(MiruException):
    """Raised when the requested operation requires calling miru.install() beforehand, but was ommitted."""


class RowFullError(MiruException):
    """Raised when a row of components is full and cannot be added to."""


class HandlerFullError(MiruException):
    """Raised when an ItemHandler instance is full and cannot fit more components."""


class ItemAlreadyAttachedError(MiruException):
    """Raised when an item is already attached to a handler and the requested operation is not possible because of it."""


# MIT License
#
# Copyright (c) 2022-present HyperGH
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
