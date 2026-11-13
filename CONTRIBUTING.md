# Contributing

## Setup

```shell
python -m pip install -e . pytest
python -m pytest tests -q
```

## Rules

- Parse source with `ast`; never grep text.
- One finding per handler, chosen by the documented priority.
- New rules need a triggering test and a clean case that must not trigger.
- Keep the scanner read-only: never import or execute the target module.

## Adding a rule

1. Add the id and wording to `RULES`.
2. Extend the `ExceptHandler` classification in `scan_source`.
3. Document it in `README.md` and `docs/ARCHITECTURE.md`.
4. Add the rule to the CLI `choices` automatically via `sorted(RULES)` (no edit
   needed if the parser uses that pattern).
