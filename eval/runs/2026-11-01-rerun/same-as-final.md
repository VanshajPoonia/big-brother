# Same labels twice?

The eval run again on the same code, compared with `2026-11-01-final`. The model runs at temperature 0 with a fixed seed.

**11 of 11** got the same label, confidence and rule.

| Case | Final run | Rerun | |
| --- | --- | --- | --- |
| arrow-1154 | cannot reproduce, high, rule 3 | cannot reproduce, high, rule 3 | same |
| arrow-896 | cannot reproduce, low, rule 3 | cannot reproduce, low, rule 3 | same |
| humanize-122 | confirmed, high, rule 1 | confirmed, high, rule 1 | same |
| humanize-136 | cannot reproduce, low, rule 4 | cannot reproduce, low, rule 4 | same |
| humanize-400 | confirmed, medium, rule 1 | confirmed, medium, rule 1 | same |
| humanize-57 | confirmed, high, rule 1 | confirmed, high, rule 1 | same |
| rich-2465 | invalid, medium, rule 2 | invalid, medium, rule 2 | same |
| rich-2988 | cannot reproduce, low, rule 4 | cannot reproduce, low, rule 4 | same |
| rich-3352 | cannot reproduce, high, rule 3 | cannot reproduce, high, rule 3 | same |
| toolz-99 | confirmed, high, rule 1 | confirmed, high, rule 1 | same |
| tqdm-1477 | invalid, medium, rule 2 | invalid, medium, rule 2 | same |
