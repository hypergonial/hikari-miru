from __future__ import annotations

import typing as t

__all__ = ("Paginator",)


class Paginator:
    """A paginator that can be used to paginate long strings to ensure a consistent character count per page.

    Parameters
    ----------
    max_len : int, optional
        The maximum length per page, by default 1000
    prefix : str, optional
        A prefix to insert every page, by default ""
    suffix : str, optional
        A suffix to insert every page, by default ""
    line_separator : str, optional
        The character used to divide lines, by default "\\n"
    """

    __slots__ = ("_max_len", "_prefix", "_suffix", "_line_separator", "_pages")

    def __init__(self, max_len: int = 1000, prefix: str = "", suffix: str = "", line_separator: str = "\n") -> None:
        self._max_len = max_len
        self._prefix = prefix
        self._suffix = suffix
        self._line_separator = line_separator
        self._pages: t.List[str] = []

    def _add_line(self, line: str) -> None:
        """Add a line to the paginator."""

        if len(self._prefix + line + self._line_separator + self._suffix) > self._max_len:
            raise ValueError(
                f"A single line cannot be longer than the maximum length of a page ({self._max_len} characters)."
            )

        if not self._pages:
            self._pages[0] = self._prefix

        # If content fits on page
        if not len(self._pages[-1]) + len(f"{line}{self._line_separator}{self._suffix}") >= self._max_len:
            self._pages[-1] += f"{line}{self._line_separator}"
        # If not, finish this page, start a new one, repeat
        else:
            self._pages[-1] += self._suffix
            self._pages.append(self._prefix)
            self._add_line(line)

    def add_line(self, line: str) -> None:
        """Add a line or multiple lines to the paginator.

        Parameters
        ----------
        line : str
            The string to add to the paginator. If it contains the line seperator, the text will be split into multiple lines.
        Raises
        ------
        ValueError
            If a single line is longer than the maximum length of a page. (Includes the prefix and suffix)
        """
        for bean in line.split(self._line_separator):
            self._add_line(bean)

    @property
    def pages(self) -> t.Sequence[str]:
        """The paginated pages."""
        return self._pages


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
