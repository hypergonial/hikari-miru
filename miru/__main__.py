"""
MIT License

Copyright (c) 2022-present HyperGH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import platform
import sys

import hikari
from colorama import Fore  # type: ignore[import]
from colorama import init

import miru

# Support color on Windows
init()
system_details = (
    f"{platform.uname().system} {platform.uname().machine} ({platform.uname().node}) - {platform.uname().release}"
)
python_details = f"{platform.python_implementation()} {platform.python_version()} ({platform.python_compiler()})"

sys.stderr.write(
    f"""{Fore.LIGHTCYAN_EX}hikari-miru - package information
{Fore.WHITE}----------------------------------
{Fore.CYAN}Miru version: {Fore.WHITE}{miru.__version__}
{Fore.CYAN}Install path: {Fore.WHITE}{os.path.abspath(os.path.dirname(__file__))}
{Fore.CYAN}Hikari version: {Fore.WHITE}{hikari.__version__}
{Fore.CYAN}Install path: {Fore.WHITE}{os.path.abspath(os.path.dirname(hikari._about.__file__))}
{Fore.CYAN}Python: {Fore.WHITE}{python_details}
{Fore.CYAN}System: {Fore.WHITE}{system_details}\n\n"""
)
