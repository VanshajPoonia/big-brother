import subprocess

import pytest

from bigbrother.pullrequest import (
    Coverage,
    PullRequest,
    changed_lines,
    check_pr,
    is_code,
    is_test,
    parse_pr_url,
    summary,
)

TESTS_V1 = '''from tinylib import parse_query


def test_parse_query():
    assert parse_query("a=1") == {"a": "1"}
'''


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=T", "-c", "user.email=t@example.com", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def commit(repo, files, message):
    for path, text in files.items():
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tinylib_repo):
    base = commit(tinylib_repo.path, {"tests/test_urls.py": TESTS_V1}, "Add tests")
    return tinylib_repo.path, base


def pr_for(base, head):
    return PullRequest(url="https://github.com/daggers/tinylib/pull/7", repo="daggers/tinylib", number=7,
                       title="Strip spaces", base_sha=base, head_sha=head)


def change_parse_url(repo):
    urls = (repo / "tinylib/urls.py").read_text().replace("def parse_url(url):\n", "def parse_url(url):\n    url = url.strip()\n")
    return {"tinylib/urls.py": urls}


def test_a_changed_function_no_test_uses_has_no_test(repo):
    path, base = repo
    head = commit(path, change_parse_url(path), "Strip spaces")
    report = check_pr(pr_for(base, head), path)

    assert report.label == Coverage.NO_TEST
    assert [(f.name, f.path, f.line, f.mentions) for f in report.functions] == [("parse_url", "tinylib/urls.py", 4, [])]
    assert "no test uses it at all" in report.reasons[0]
    assert report.reasons[-1] == "the PR changes 0 test files"


def test_a_test_added_in_the_pr_tests_it(repo):
    path, base = repo
    test = TESTS_V1 + '\n\ndef test_parse_url_strips():\n    assert parse_url(" http://a/b ")["host"] == "a"\n'
    head = commit(path, {**change_parse_url(path), "tests/test_urls.py": test.replace("import parse_query", "import parse_query, parse_url")}, "Strip spaces")
    report = check_pr(pr_for(base, head), path)

    assert report.label == Coverage.TESTED
    [m] = report.functions[0].mentions  # the import line doesn't count
    assert (m.path, m.line, m.in_pr) == ("tests/test_urls.py", 9, True)
    assert report.tests_changed == ["tests/test_urls.py"]
    assert "[tinylib/urls.py:4](https://github.com/daggers/tinylib/blob/" in summary(report)


def test_older_tests_alone_dont_count(repo):
    path, base = repo
    urls = (path / "tinylib/urls.py").read_text().replace('    return dict(pair', '    query = query.strip()\n    return dict(pair')
    head = commit(path, {"tinylib/urls.py": urls}, "Strip spaces in queries")
    report = check_pr(pr_for(base, head), path)

    assert report.label == Coverage.NO_TEST
    m = report.functions[0].mentions[0]
    assert (m.path, m.in_pr) == ("tests/test_urls.py", False)
    assert "Older tests do, like tests/test_urls.py:5" in report.reasons[0]


def test_a_new_parametrize_case_counts_for_the_test_it_decorates(repo):
    path, base = repo
    old = commit(path, {"tests/test_urls.py": 'import pytest\nfrom tinylib import parse_query\n\n\n'
                        '@pytest.mark.parametrize("q", ["a=1"])\ndef test_parse_query(q):\n    assert parse_query(q)\n'}, "Parametrize")
    urls = (path / "tinylib/urls.py").read_text().replace('    return dict(pair', '    query = query.strip()\n    return dict(pair')
    test = (path / "tests/test_urls.py").read_text().replace('["a=1"]', '["a=1", " a=1 "]')
    head = commit(path, {"tinylib/urls.py": urls, "tests/test_urls.py": test}, "Strip spaces in queries")
    report = check_pr(pr_for(old, head), path)

    assert report.label == Coverage.TESTED
    assert report.functions[0].mentions[0].in_pr


def test_two_functions_one_tested_is_partly_tested(repo):
    path, base = repo
    urls = change_parse_url(path)["tinylib/urls.py"].replace('    return dict(pair', '    query = query.strip()\n    return dict(pair')
    test = TESTS_V1.replace('"a=1"', '" a=1 "')
    head = commit(path, {"tinylib/urls.py": urls, "tests/test_urls.py": test}, "Strip spaces everywhere")
    report = check_pr(pr_for(base, head), path)

    assert report.label == Coverage.PARTLY
    assert {f.name: bool(f.mentions and f.mentions[0].in_pr) for f in report.functions} == {"parse_url": False, "parse_query": True}


def test_a_method_needs_its_class_named_too(repo):
    path, base = repo
    head = commit(path, {"tinylib/cls.py": "class Parser:\n    def parse(self, url):\n        return url\n",
                         "tests/test_other.py": "def test_x():\n    parse('x')\n"}, "Add Parser")
    report = check_pr(pr_for(base, head), path)
    assert [(f.name, f.mentions) for f in report.functions] == [("Parser.parse", [])]


def test_docs_and_constants_are_no_function_changed(repo):
    path, base = repo
    urls = (path / "tinylib/urls.py").read_text().replace("MAX_LENGTH = 255", "MAX_LENGTH = 2048")
    head = commit(path, {"tinylib/urls.py": urls, "docs/conf.py": "def setup(app):\n    pass\n"}, "Longer URLs")
    report = check_pr(pr_for(base, head), path)

    assert report.label == Coverage.NO_CODE
    assert report.outside_functions == ["tinylib/urls.py: 1 changed line outside any function"]


def test_changed_lines_reads_a_zero_context_diff():
    diff = ("+++ b/pkg/a.py\n@@ -3,0 +4,2 @@\n+x\n+y\n@@ -10 +11 @@\n-a\n+b\n"
            "+++ b/pkg/b.py\n@@ -5,2 +4,0 @@\n-gone\n-gone\n+++ /dev/null\n@@ -1,3 +0,0 @@\n")
    assert changed_lines(diff) == {"pkg/a.py": {4, 5, 11}, "pkg/b.py": {4}}


@pytest.mark.parametrize("path, test, code", [
    ("tests/test_urls.py", True, False),
    ("src/pkg/tests/helpers.py", True, False),
    ("pkg/urls_test.py", True, False),
    ("pkg/urls.py", False, True),
    ("docs/conf.py", False, False),
    ("setup.py", False, False),
    ("README.md", False, False),
])
def test_what_counts_as_a_test_or_code(path, test, code):
    assert (is_test(path), is_code(path)) == (test, code)


def test_pr_urls():
    assert parse_pr_url("https://github.com/a/b/pull/12") == ("a/b", 12)
    with pytest.raises(ValueError):
        parse_pr_url("https://github.com/a/b/issues/12")


def test_a_constructor_is_found_by_its_class_and_nested_code_belongs_outside(repo):
    path, base = repo
    code = "class Parser:\n    def __init__(self, url):\n        def clean(u):\n            return u\n        self.url = clean(url)\n"
    base = commit(path, {"tinylib/cls.py": code}, "Add Parser")
    head = commit(path, {"tinylib/cls.py": code.replace("return u", "return u.strip()"),
                         "tests/test_cls.py": "from tinylib.cls import Parser\n\n\ndef test_parser():\n    assert Parser(' a ').url == 'a'\n"},
                  "Strip in Parser")
    report = check_pr(pr_for(base, head), path)

    assert [f.name for f in report.functions] == ["Parser.__init__"]
    assert report.label == Coverage.TESTED and report.functions[0].mentions[0].line == 5


def test_a_name_two_modules_define_needs_the_module_named(repo):
    path, base = repo
    base = commit(path, {"tinylib/a.py": "def install():\n    return 1\n", "tinylib/b.py": "def install():\n    return 2\n",
                         "tests/test_a.py": "from tinylib import a\n\n\ndef test_a():\n    assert a.install() == 1\n"}, "Two installs")
    head = commit(path, {"tinylib/b.py": "def install():\n    return 3\n"}, "Change b")
    report = check_pr(pr_for(base, head), path)
    assert report.functions[0].mentions == []  # test_a.py tests a.install, not b.install
