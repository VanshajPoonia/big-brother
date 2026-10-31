# Eval results

- Accuracy, all cases: **6/11 (55%)**
- Accuracy where the label came from evidence: 5/9 (56%)
- Fell back because nothing could run: 2. Crashed: 0
- Said invalid when it wasn't: 0
- Seconds per issue: 56 on average

| Expected \ Said | confirmed | cannot reproduce | invalid | crashed |
| --- | --- | --- | --- | --- |
| confirmed | 3 | 1 | 0 | 0 |
| cannot reproduce | 0 | 3 | 0 | 0 |
| invalid | 0 | 4 | 0 | 0 |

| Label | Precision | Recall |
| --- | --- | --- |
| confirmed | 100% | 75% |
| cannot reproduce | 38% | 100% |
| invalid | n/a | 0% |

| Case | Expected | Said | Rule | Why |
| --- | --- | --- | --- | --- |
| [humanize-57](https://github.com/python-humanize/humanize/issues/57) | confirmed | confirmed | 1 | the repro hit the reported symptom (ValueError: math domain error) inside the package |
| [humanize-122](https://github.com/python-humanize/humanize/issues/122) | confirmed | confirmed | 1 | the repro hit the reported symptom (TypeError: can't subtract offset-naive and offset-aware datetimes) inside the package |
| [humanize-400](https://github.com/python-humanize/humanize/issues/400) | confirmed | confirmed | 1 | the reporter's own code printed the reported output (1000.0 sextillion) |
| [toolz-99](https://github.com/pytoolz/toolz/issues/99) | confirmed | cannot reproduce ✗ | 4 | the repro failed with ImportError outside the package, which isn't the reported symptom |
| [arrow-1154](https://github.com/arrow-py/arrow/issues/1154) | cannot reproduce | cannot reproduce | 3 | the reporter's own code ran cleanly, the reported symptom didn't appear |
| [arrow-896](https://github.com/arrow-py/arrow/issues/896) | cannot reproduce | cannot reproduce | 5 | the report has no steps to run, so the label is the blocked policy (cannot reproduce), not evidence |
| [rich-2988](https://github.com/Textualize/rich/issues/2988) | cannot reproduce | cannot reproduce | 4 | the repro failed with AttributeError outside the package, which isn't the reported symptom |
| [rich-3352](https://github.com/Textualize/rich/issues/3352) | invalid | cannot reproduce ✗ | 3 | the reporter's own code ran cleanly, the reported symptom didn't appear |
| [rich-2465](https://github.com/Textualize/rich/issues/2465) | invalid | cannot reproduce ✗ | 5 | the report has no steps to run, so the label is the blocked policy (cannot reproduce), not evidence |
| [tqdm-1477](https://github.com/tqdm/tqdm/issues/1477) | invalid | cannot reproduce ✗ | 4 | the repro failed with ModuleNotFoundError outside the package, which isn't the reported symptom |
| [humanize-136](https://github.com/python-humanize/humanize/issues/136) | invalid | cannot reproduce ✗ | 4 | the reported symptom showed up, but not from inside the package, so it doesn't count |
