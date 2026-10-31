"""Find the reporter's own Python code in an issue body, without the model."""

from __future__ import annotations

import ast
import re

from bigbrother.schema import ReproScript

FENCE = re.compile(r"^(?P<fence>`{3,}|~{3,})[ \t]*(?P<lang>[\w+-]*)[^\n]*\n(?P<code>.*?)^(?P=fence)[ \t]*$", re.M | re.S)
PYTHON = {"python", "py", "python3", "pycon", "ipython", ""}
MAX_SCRIPT = 4000


def code_blocks(body: str) -> list[tuple[str, str]]:
    """Every fenced block as (language, code). The language is lowercase, "" if none was given."""
    return [(m["lang"].lower(), m["code"]) for m in FENCE.finditer(body.replace("\r\n", "\n"))]


def _strip_prompts(code: str) -> str:
    """Turn a `>>>` console session into a script, dropping the printed output."""
    if ">>> " not in code:
        return code
    lines = []
    for line in code.splitlines():
        if line.startswith((">>> ", "... ")) or line in (">>>", "..."):
            lines.append(line[4:])
    return "\n".join(lines)


def _runnable(code: str) -> bool:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    return any(isinstance(node, ast.Call) for node in ast.walk(tree))


def reporter_script(body: str) -> ReproScript | None:
    """The reporter's Python blocks joined in order, if they parse and call something.

    Tracebacks, shell commands and output blocks don't parse as Python, so they drop out.
    """
    parts = []
    for lang, code in code_blocks(body):
        if lang not in PYTHON:
            continue
        code = _strip_prompts(code).strip()
        try:
            ast.parse(code)
        except SyntaxError:
            continue
        if code:
            parts.append(code)
    script = "\n\n".join(parts)
    if not script or not _runnable(script) or len(script) > MAX_SCRIPT:
        return None
    return ReproScript(code=script + "\n", origin="reporter")
