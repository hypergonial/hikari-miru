import os
import typing as t

import nox
from nox import options

PATH_TO_PROJECT = os.path.join(".", "miru")
EXAMPLES_PATH = os.path.join(".", "examples")
SCRIPT_PATHS = [PATH_TO_PROJECT, EXAMPLES_PATH, "noxfile.py", os.path.join(".", "tests")]

options.default_venv_backend = "uv"
options.sessions = ["format_fix", "pyright", "pytest", "docs"]


# uv_sync taken from: https://github.com/hikari-py/hikari/blob/master/pipelines/nox.py#L48
#
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
def uv_sync(
    session: nox.Session, /, *, include_self: bool = False, extras: t.Sequence[str] = (), groups: t.Sequence[str] = ()
) -> None:
    if extras and not include_self:
        raise RuntimeError("When specifying extras, set `include_self=True`.")

    args: list[str] = []
    for extra in extras:
        args.extend(("--extra", extra))

    group_flag = "--group" if include_self else "--only-group"
    for group in groups:
        args.extend((group_flag, group))

    session.run_install(
        "uv", "sync", "--frozen", *args, silent=True, env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    )


@nox.session()
def format_fix(session: nox.Session) -> None:
    uv_sync(session, groups=["dev"])
    session.run("python", "-m", "ruff", "format", *SCRIPT_PATHS)
    session.run("python", "-m", "ruff", "check", *SCRIPT_PATHS, "--fix")


@nox.session()
def format(session: nox.Session) -> None:
    uv_sync(session, groups=["dev"])
    session.run("python", "-m", "ruff", "format", *SCRIPT_PATHS, "--check")
    session.run("python", "-m", "ruff", "check", *SCRIPT_PATHS)


@nox.session()
def pyright(session: nox.Session) -> None:
    uv_sync(session, include_self=True, groups=["dev"])
    session.run("pyright", *SCRIPT_PATHS)


@nox.session()
def pytest(session: nox.Session) -> None:
    uv_sync(session, include_self=True, groups=["dev"])
    session.run("pytest", "tests")


@nox.session()
def docs(session: nox.Session) -> None:
    uv_sync(session, include_self=True, groups=["docs"])
    session.run("python", "-m", "mkdocs", "-q", "build")


@nox.session()
def servedocs(session: nox.Session) -> None:
    uv_sync(session, include_self=True, groups=["docs"])
    session.run("python", "-m", "mkdocs", "serve")


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
