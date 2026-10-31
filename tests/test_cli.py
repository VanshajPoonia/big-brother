import pytest

from bigbrother import __version__
from bigbrother.cli import main


def test_version_prints_package_version(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])

    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"bigbrother {__version__}"


def test_no_arguments_exits_cleanly():
    assert main([]) == 0
