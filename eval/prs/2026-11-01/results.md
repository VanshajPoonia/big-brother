# The PR check on recent merged PRs

The last 20 merged pull requests in humanize and in Rich on 1 Nov 2026, each checked with `bigbrother pr --run-tests`. A PR's changed test files ran in the sandbox at its head and at its base, and failing before and passing after makes it `tested` whatever the tests are named.

- humanize: 15 no function changed, 2 no test for this change, 2 partly tested, 1 tested
- rich: 8 no function changed, 2 no test for this change, 2 partly tested, 8 tested

Tests ran for 19 PRs, and for 8 of them they failed without the change and passed with it.

| Pull request | Title | Label | What ran |
| --- | --- | --- | --- |
| [humanize #483](https://github.com/python-humanize/humanize/pull/483) | Benchmark with Python 3.15 | no function changed |  |
| [humanize #482](https://github.com/python-humanize/humanize/pull/482) | Update github-actions | no function changed |  |
| [humanize #471](https://github.com/python-humanize/humanize/pull/471) | Complete and fix the Bengali (bn_BD) translation | no function changed | tests/test_i18n.py passes with and without the change (6 passed, 122 skipped in 0.25s), so it doesn't show the change is tested |
| [humanize #465](https://github.com/python-humanize/humanize/pull/465) | Use Turkish numeric separators | no function changed | tests/test_i18n.py passes with and without the change (6 passed, 114 skipped in 0.28s), so it doesn't show the change is tested |
| [humanize #464](https://github.com/python-humanize/humanize/pull/464) | Translate byte-size labels into Persian | no function changed | tests/test_i18n.py passes with and without the change (6 passed, 117 skipped in 0.35s), so it doesn't show the change is tested |
| [humanize #461](https://github.com/python-humanize/humanize/pull/461) | Fix Persian future-time wording and locale metadata | no function changed | tests/test_i18n.py passes with and without the change (6 passed, 117 skipped in 0.29s), so it doesn't show the change is tested |
| [humanize #444](https://github.com/python-humanize/humanize/pull/444) | [pre-commit.ci] pre-commit autoupdate | no function changed |  |
| [humanize #440](https://github.com/python-humanize/humanize/pull/440) | Drop support for EOL Python 3.10 | partly tested | tests/test_filesize.py, tests/test_i18n.py, tests/test_time.py pass with and without the change (474 passed, 112 skipped in 1.09s), so they don't show the chang |
| [humanize #435](https://github.com/python-humanize/humanize/pull/435) | Document local test setup and pytest commands | no function changed |  |
| [humanize #422](https://github.com/python-humanize/humanize/pull/422) | Update dependency pymdown-extensions to v12 | no function changed |  |
| [humanize #421](https://github.com/python-humanize/humanize/pull/421) | Update github-actions | no function changed |  |
| [humanize #410](https://github.com/python-humanize/humanize/pull/410) | docs: align the naturaldelta example with minute rounding | no function changed |  |
| [humanize #402](https://github.com/python-humanize/humanize/pull/402) | Fix `naturaldelta` doctest | no test for this change |  |
| [humanize #397](https://github.com/python-humanize/humanize/pull/397) | Defer importing `math` in `filesize.py` | no test for this change |  |
| [humanize #392](https://github.com/python-humanize/humanize/pull/392) | Fix intcomma overflow for large Python integers | tested | tests/test_number.py fails without the change (2 failed, 232 passed in 0.15s) and passes with it (234 passed in 0.13s), so the PR's tests check the change |
| [humanize #391](https://github.com/python-humanize/humanize/pull/391) | Fix translation loss during catalog updates | partly tested | tests/test_i18n.py passes with and without the change (6 passed, 112 skipped in 0.35s), so it doesn't show the change is tested |
| [humanize #388](https://github.com/python-humanize/humanize/pull/388) | Update github-actions | no function changed |  |
| [humanize #387](https://github.com/python-humanize/humanize/pull/387) | Update dependency pymdown-extensions to v11.0.2 | no function changed |  |
| [humanize #386](https://github.com/python-humanize/humanize/pull/386) | Update dependency mypy to v2.3.1 | no function changed |  |
| [humanize #385](https://github.com/python-humanize/humanize/pull/385) | Re-profile contributors on re-open | no function changed |  |
| [rich #4175](https://github.com/Textualize/rich/pull/4175) | Update README URLs from master to main branch | no function changed |  |
| [rich #4080](https://github.com/Textualize/rich/pull/4080) | bump to 15.0.0 | no function changed |  |
| [rich #4079](https://github.com/Textualize/rich/pull/4079) | Inline table code | no test for this change | tests/test_markdown.py fails at the PR's head in the sandbox (1 failed, 7 passed in 0.26s). That can be the PR, or a dependency version different from the proje |
| [rich #4077](https://github.com/Textualize/rich/pull/4077) | proxy isatty | tested | tests/test_file_proxy.py fails without the change (1 failed, 3 passed in 0.14s) and passes with it (4 passed in 0.14s), so the PR's tests check the change |
| [rich #4076](https://github.com/Textualize/rich/pull/4076) | preserve newlines | tested | tests/test_ansi.py fails without the change (4 failed, 20 passed in 0.14s) and passes with it (24 passed in 0.11s), so the PR's tests check the change |
| [rich #4075](https://github.com/Textualize/rich/pull/4075) | empty with end | tested | tests/test_console.py fails without the change (1 failed, 99 passed in 0.68s) and passes with it (100 passed in 0.61s), so the PR's tests check the change |
| [rich #4073](https://github.com/Textualize/rich/pull/4073) | bump | no function changed |  |
| [rich #4070](https://github.com/Textualize/rich/pull/4070) | perf: reduce Console and RichHandler import time by deferring unused imports | partly tested | tests/test_console.py, tests/test_syntax.py fail at the PR's head in the sandbox (6 failed, 118 passed in 0.91s). That can be the PR, or a dependency version di |
| [rich #4026](https://github.com/Textualize/rich/pull/4026) | Update CONTRIBUTING.md | no function changed |  |
| [rich #4008](https://github.com/Textualize/rich/pull/4008) | bump 14.3.3 | no function changed |  |
| [rich #4007](https://github.com/Textualize/rich/pull/4007) | Add regression tests for VS16 after zero-width chars in split_graphemes | no function changed | tests/test_cells.py passes with and without the change (69 passed in 0.06s), so it doesn't show the change is tested |
| [rich #4006](https://github.com/Textualize/rich/pull/4006) | fix for infinite loop in split_graphemes | tested | tests/test_cells.py passes at the PR's head (67 passed in 0.08s), but couldn't run at the base: the tests timed out |
| [rich #3972](https://github.com/Textualize/rich/pull/3972) | Add AI contribution guidelines to AI_POLICY.md | no function changed |  |
| [rich #3953](https://github.com/Textualize/rich/pull/3953) | Fix ZWJ and edge cases | tested | tests/test_cells.py fails without the change (2 failed, 54 passed in 0.06s) and passes with it (56 passed in 0.04s), so the PR's tests check the change |
| [rich #3944](https://github.com/Textualize/rich/pull/3944) | fix fonts | tested | tests/test_cells.py fails without the change (1 failed, 53 passed in 0.05s) and passes with it (54 passed in 0.04s), so the PR's tests check the change |
| [rich #3942](https://github.com/Textualize/rich/pull/3942) | Update to markdown styles | tested | tests/test_markdown.py, tests/test_markdown_no_hyperlinks.py fail without the change (6 failed, 2 passed in 0.18s) and pass with it (8 passed in 0.16s), so the  |
| [rich #3941](https://github.com/Textualize/rich/pull/3941) | Fix typing for save_html, save_text, save_svg to accept PathLike | no test for this change |  |
| [rich #3939](https://github.com/Textualize/rich/pull/3939) | typing highlighter | no function changed |  |
| [rich #3938](https://github.com/Textualize/rich/pull/3938) | fix background style with soft wrap | tested | tests/test_segment.py, tests/test_text.py fail without the change (3 failed, 171 passed in 0.26s) and pass with it (174 passed in 0.24s), so the PR's tests chec |
| [rich #3937](https://github.com/Textualize/rich/pull/3937) | don't strip whitespace when soft_wrap is True | partly tested | tests/test_text.py passes with and without the change (112 passed in 0.20s), so it doesn't show the change is tested |
