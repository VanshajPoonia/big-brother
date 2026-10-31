"""Spot a reporter's own file standing in for a real module, like a script named select.py.

Python puts a script's folder first on the import path, so a file called select.py hides the
standard select module. The error then looks like a bug in whatever imported it. This only
reads the report: it needs the reporter's own traceback to show both their file and the error.
"""

from __future__ import annotations

import re
import sys

from bigbrother.schema import Shadowing

FRAME = re.compile(r'File "(?P<path>[^"<>]+\.py)", line \d+')
# Errors that name the module Python actually loaded.
MODULE_ERROR = re.compile(
    r"^.*(?:"
    r"module '(?P<a>[\w.]+)' has no attribute '\w+'"
    r"|partially initialized module '(?P<b>[\w.]+)'"
    r"|cannot import name '\w+' from '(?P<c>[\w.]+)'"
    r"|No module named '(?P<d>[\w.]+)\.[\w.]+'; '[\w.]+' is not a package"
    r").*$",
    re.MULTILINE,
)
INSTALLED = re.compile(r"[\\/](?:site-packages|dist-packages)[\\/]|[\\/]lib[\\/]python\d[\d.]*[\\/]|[\\/]Lib[\\/]", re.IGNORECASE)


def _parts(path: str) -> list[str]:
    return [part for part in re.split(r"[\\/]", path) if part]


def find_shadowing(text: str, package: str | None = None) -> Shadowing | None:
    """The reporter's file that Python loaded in place of a real module, if their report shows one."""
    real = set(sys.stdlib_module_names)
    if package:
        real.add(package.split(".")[0])
    own_files = {}
    for frame in FRAME.finditer(text):
        path = frame["path"]
        parts = _parts(path)
        if INSTALLED.search(path) or len(parts) < 2:
            continue
        name = parts[-1][:-3]
        # select.py inside a folder called select is that package's own module, not a stand-in.
        if name in real and parts[-2] != name:
            own_files.setdefault(name, path)
    for error in MODULE_ERROR.finditer(text):
        module = next(group for group in error.group("a", "b", "c", "d") if group).split(".")[0]
        if module in own_files:
            return Shadowing(module=module, path=own_files[module], quote=error.group(0).strip()[:300])
    return None
