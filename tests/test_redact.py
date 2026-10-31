import tempfile
from pathlib import Path

from bigbrother.redact import redact


def test_home_and_a_per_user_temp_folder_read_like_a_shell_would():
    clone = Path.home() / ".cache" / "bigbrother" / "repos" / "a__b"
    tmp = tempfile.gettempdir()
    temp = "/tmp" if tmp.rstrip("/") == "/tmp" else "$TMPDIR"
    command = f"git -C {clone} archive && docker run --mount type=bind,source={tmp}/bigbrother-x/src,target=/src"
    assert redact(command) == f"git -C ~/.cache/bigbrother/repos/a__b archive && docker run --mount type=bind,source={temp}/bigbrother-x/src,target=/src"


def test_paths_inside_the_container_and_the_reporters_own_stay():
    text = 'File "/src/tinylib/urls.py", line 6\nFile "/Users/universe/scripts/select.py", line 1'
    assert redact(text) == text
