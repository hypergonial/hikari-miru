import os

import nox
from nox import options

PATH_TO_PROJECT = os.path.join(".", "hikari_views")
SCRIPT_PATHS = [
    PATH_TO_PROJECT,
    "noxfile.py",
]

options.sessions = ["format_fix", "mypy"]


@nox.session()
def format_fix(session):
    session.install("black")
    session.install("isort")
    session.run("python", "-m", "black", *SCRIPT_PATHS)
    session.run("python", "-m", "isort", *SCRIPT_PATHS)


# noinspection PyShadowingBuiltins
@nox.session()
def format(session):
    session.install("-U", "black")
    session.run("python", "-m", "black", *SCRIPT_PATHS, "--check")


@nox.session()
def mypy(session):
    session.install("-Ur", "requirements.txt")
    session.install("-U", "mypy")
    session.run("python", "-m", "mypy", PATH_TO_PROJECT)
