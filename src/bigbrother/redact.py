"""Take this machine's folders out of what a report shows.

Reports become public comments. The commands that ran are evidence, but the folders they ran in
name the person running the tool. The home folder becomes `~` and a per-user temp folder becomes
`$TMPDIR`, the way a shell would write them, so the commands still read and paste the same.
Paths inside the container and the reporter's own paths, quoted from the issue, are left alone.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def _pairs() -> list[tuple[str, str]]:
    pairs = []
    tmp = tempfile.gettempdir()
    if tmp.rstrip("/") != "/tmp":  # /tmp names nobody, macOS's /var/folders/xx/... is per user
        pairs += [(tmp, "$TMPDIR"), (os.path.realpath(tmp), "$TMPDIR")]
    home = str(Path.home())
    pairs += [(home, "~"), (os.path.realpath(home), "~")]
    # Longest first, so /private/var/folders wins over /var/folders.
    return sorted({p for p in pairs if len(p[0]) > 1}, key=lambda p: -len(p[0]))


def redact(text: str) -> str:
    for path, label in _pairs():
        text = text.replace(path, label)
    return text
