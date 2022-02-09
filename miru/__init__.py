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


from .abc import *
from .button import *
from .context import *
from .interaction import *
from .modal import *
from .select import *
from .text_input import *
from .traits import *
from .view import *

__version__ = "1.2.0"


def load(bot: MiruAware) -> None:
    """Load miru and pass the current running application to it.

    Parameters
    ----------
    bot : ViewsAware
        The currently running application. Must implement traits
        RESTAware and EventManagerAware.

    Raises
    ------
    RuntimeError
        miru is already loaded
    TypeError
        Parameter bot does not have traits specified in ViewsAware
    """
    if ItemHandler._app is not None:
        raise RuntimeError("miru is already loaded!")
    if not isinstance(bot, MiruAware):
        raise TypeError(f"Expected type with trait ViewsAware for parameter bot, not {type(bot)}")

    ItemHandler._app = bot


def unload() -> None:
    """Unload miru and remove the current running application from it.

    .. warning::
        Unbound persistent views should be stopped manually.
    """
    for message, view in View._views.items():
        view.stop()

    ItemHandler._app = None
