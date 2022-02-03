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

from __future__ import annotations

import functools
import typing

import hikari

__all__ = ["Interaction"]


class Interaction(hikari.ComponentInteraction):
    """
    Represents a component interaction on Discord. This object is practically identical to hikari.ComponentInteraction,
    with the only exception being that response status is tracked for automatic deferring and short-hand methods.
    """

    _issued_response: bool = False

    @classmethod
    def from_hikari(cls, interaction: hikari.ComponentInteraction) -> Interaction:
        """Create a new Interaction object from a hikari.ComponentInteraction. This should be rarely used.

        Parameters
        ----------
        interaction : hikari.ComponentInteraction
            The ComponentInteraction this object should be created from.

        Returns
        -------
        Interaction
            The created interaction object.
        """
        return cls(
            channel_id=interaction.channel_id,
            component_type=interaction.component_type,
            custom_id=interaction.custom_id,
            values=interaction.values,
            guild_id=interaction.guild_id,
            message=interaction.message,
            member=interaction.member,
            user=interaction.user,
            locale=interaction.locale,
            guild_locale=interaction.guild_locale,
            app=interaction.app,
            id=interaction.id,
            application_id=interaction.application_id,
            type=interaction.type,
            token=interaction.token,
            version=interaction.version,
        )

    @functools.wraps(hikari.ComponentInteraction.create_initial_response)
    async def create_initial_response(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        await super().create_initial_response(*args, **kwargs)
        self._issued_response = True
