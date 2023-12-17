from __future__ import annotations

import typing as t
from functools import total_ordering

from .about import __version__

if t.TYPE_CHECKING:
    import typing_extensions as te


__all__ = ("Version", "CURRENT_VERSION")


@total_ordering
class Version:
    """A version object representing a semantic version."""

    __all__ = ("major", "minor", "patch")

    def __init__(self, major: int, minor: int, patch: int) -> None:
        self.major = major
        self.minor = minor
        self.patch = patch

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: te.Self) -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    @classmethod
    def from_str(cls, version: str) -> te.Self:
        if version[0].casefold() == "v":
            version = version[1:]

        major, minor, patch = version.split(".", maxsplit=2)
        return cls(int(major), int(minor), int(patch))


CURRENT_VERSION: Version = Version.from_str(__version__)

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
