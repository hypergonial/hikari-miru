import logging
import typing as t

from .abc.item_handler import ItemHandler
from .events import _EventListener
from .traits import MiruAware
from .view import View

__all__ = ["install", "uninstall", "load", "unload"]

_event_listener: t.Optional[_EventListener] = None

logger = logging.getLogger(__name__)


def install(bot: MiruAware) -> None:
    """Install miru and pass the current running application to it.
    Starts listeners for custom miru events.

    Parameters
    ----------
    bot : MiruAware
        The currently running application. Must implement traits
        RESTAware and EventManagerAware.

    Raises
    ------
    RuntimeError
        miru is already loaded
    TypeError
        Parameter bot does not have traits specified in MiruAware
    """
    if ItemHandler._app is not None:
        raise RuntimeError("miru is already loaded!")

    if not isinstance(bot, MiruAware):
        raise TypeError(f"Expected type with trait ViewsAware for parameter bot, not {type(bot)}")

    ItemHandler._app = bot
    _event_listener = _EventListener()
    _event_listener.start_listeners(bot)


def uninstall() -> None:
    """Uninstall miru and remove the current running application from it.
    Stops listeners for custom miru events.

    .. warning::
        Unbound persistent views should be stopped manually.
    """
    for view in View._views.values():
        view.stop()

    ItemHandler._app = None
    if _event_listener:
        _event_listener.stop_listeners()


def load(bot: MiruAware) -> None:
    """DEPRECATED: Use miru.install instead."""
    logger.warning("miru.load is deprecated, use miru.install instead.")
    install(bot)


def unload() -> None:
    """DEPRECATED: Use miru.uninstall instead."""
    logger.warning("miru.unload is deprecated, use miru.uninstall instead.")
    uninstall()


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
