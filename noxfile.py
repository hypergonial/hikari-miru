import os

import nox
from nox import options

PATH_TO_PROJECT = os.path.join(".", "miru")
SCRIPT_PATHS = [
    PATH_TO_PROJECT,
    "noxfile.py",
    "docs/source/conf.py",
]

options.sessions = ["format_fix", "mypy", "pytest", "sphinx"]


@nox.session()
def format_fix(session: nox.Session) -> None:
    session.install("black")
    session.install("isort")
    session.run("python", "-m", "black", *SCRIPT_PATHS)
    session.run("python", "-m", "isort", *SCRIPT_PATHS)


# noinspection PyShadowingBuiltins
@nox.session()
def format(session: nox.Session) -> None:
    session.install("-U", "black")
    session.run("python", "-m", "black", *SCRIPT_PATHS, "--check")


@nox.session()
def mypy(session: nox.Session) -> None:
    session.install("-Ur", "requirements.txt")
    session.install("-U", "mypy")
    session.run(
        "python", "-m", "mypy", "--install-types", "--non-interactive", "--cache-dir=.mypy_cache/", PATH_TO_PROJECT
    )


@nox.session()
def pytest(session: nox.Session) -> None:
    session.install(".")
    session.install("-U", "pytest")
    session.run("pytest", "tests")


@nox.session(reuse_venv=True)
def sphinx(session: nox.Session) -> None:
    session.install("-Ur", "doc_requirements.txt")
    session.install("-Ur", "requirements.txt")
    session.run("python", "-m", "sphinx.cmd.build", "docs/source", "docs/build", "-b", "html")


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
