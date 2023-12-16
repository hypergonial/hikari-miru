from __future__ import annotations

import typing as t
from warnings import warn

from .version import CURRENT_VERSION, Version

__all__ = ("warn_deprecate",)


def warn_deprecate(*, what: str, when: Version, use_instead: t.Optional[str] = None) -> None:
    """Warn about a deprecation.

    Parameters
    ----------
    what : str
        The name of the object that is being deprecated.
    when : Version
        The version in which the object will be removed.
    use_instead : Optional[str], optional
        The object's name that should be used instead, by default None
    """
    if when < CURRENT_VERSION:
        raise DeprecationWarning(
            f"{what!r} is past its deprecation date and should not be used. {f'Use {use_instead!r} instead.' if use_instead else ''}"
        )

    if use_instead:
        warn(
            f"{what!r} is deprecated and will be removed in version {when}. Use {use_instead!r} instead.",
            DeprecationWarning,
            stacklevel=3,
        )
    else:
        warn(f"{what!r} is deprecated and will be removed in version {when}.", DeprecationWarning, stacklevel=3)


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
