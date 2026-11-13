# Usage

## Reviewing a pull request locally

```shell
exceptscan scan $(git diff --name-only origin/main -- '*.py')
```

Passing explicit files keeps the report focused on what changed.

## Adopting the gate gradually

Start with high severity only:

```shell
exceptscan scan src/ --fail-on high
```

Then tighten to `--fail-on medium` once the bare and swallowed handlers are
fixed.

## Reading a finding

- `bare-except`: replace with the expected exception types, or add
  `except Exception` plus logging if the boundary really is a catch-all.
- `swallowed-exception`: delete the `try`, or log with context.
- `broad-except`: catch the specific error; keep `Exception` only at process
  boundaries.
- `silent-handler`: log, re-raise, or convert to a typed error — never return a
  bare `None` and hope.

## JSON for a review bot

```shell
exceptscan scan pkg/ --json
```

Each finding has `rule`, `severity`, `file`, `line`, `column`, `message` and
`snippet`, which maps cleanly onto review comments.

## Library use

```python
from exceptscan import scan_source

for finding in scan_source(open("module.py", encoding="utf-8").read(), "module.py"):
    print(finding.line, finding.rule)
```
