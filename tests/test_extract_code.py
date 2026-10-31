from bigbrother.extract.code import code_blocks, reporter_script


def test_finds_fenced_blocks_with_their_language():
    body = "text\n```python\nprint(1)\n```\nmore\n~~~\nraw\n~~~\n"
    assert code_blocks(body) == [("python", "print(1)\n"), ("", "raw\n")]


def test_real_bug_fixture_gives_the_reporters_code(load_issue):
    script = reporter_script(load_issue("real_bug").body)
    assert script.origin == "reporter"
    assert 'parse_url("https://example.com/" + "a" * 300)' in script.code
    assert "ValueError" not in script.code  # the error block isn't Python, so it's left out


def test_no_code_means_no_script(load_issue):
    assert reporter_script(load_issue("no_steps").body) is None
    assert reporter_script(load_issue("missing_function").body) is None


def test_a_block_that_only_imports_isnt_runnable():
    assert reporter_script("```python\nimport tinylib\n```") is None


def test_blocks_are_joined_in_order():
    body = "```python\nfrom tinylib import parse_url\n```\nthen\n```py\nparse_url('x')\n```"
    assert reporter_script(body).code == "from tinylib import parse_url\n\nparse_url('x')\n"


def test_shell_and_traceback_blocks_are_skipped():
    body = "```bash\npip install tinylib\n```\n```pytb\nTraceback (most recent call last):\n```\n```python\nf()\n```"
    assert reporter_script(body).code == "f()\n"


def test_console_sessions_lose_prompts_and_output():
    body = "```pycon\n>>> from tinylib import parse_url\n>>> parse_url('x' * 300)\nTraceback (most recent call last):\nValueError: URL too long\n```"
    assert reporter_script(body).code == "from tinylib import parse_url\nparse_url('x' * 300)\n"


def test_windows_line_endings_work():
    assert reporter_script("```python\r\nf()\r\n```\r\n").code == "f()\n"


def test_huge_scripts_are_refused():
    assert reporter_script("```python\n" + "f()\n" * 2000 + "```") is None
