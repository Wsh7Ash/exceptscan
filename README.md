# exceptscan

**Find the Python `except` blocks that make failures disappear.**

## Why

Code review skims past exception handlers. A bare `except:` also catches Ctrl-C,
`except Exception: pass` hides a real bug, and a handler that neither logs nor
re-raises turns a crash into silence. `exceptscan` parses Python with `ast`
(so strings and comments never create false matches) and reports those four
patterns with file, line and the handler's own source line.

## Features

- Rules: `bare-except`, `swallowed-exception`, `broad-except`, `silent-handler`
- Understands "responds" (raise, or a call whose name looks like logging)
- Single file or recursive directory scan with sensible skips
- Syntax errors become a `parse-error` finding instead of a crash
- Text or JSON output, `--fail-on` gate, `rules` / `explain` subcommands

## Example

```text
exceptscan report - examples/bad_handler.py
====================================================
[HIGH  ] bare-except          examples/bad_handler.py:7
         A bare 'except:' also catches KeyboardInterrupt and SystemExit.
         > except:
[MEDIUM] silent-handler       examples/bad_handler.py:14
         The handler neither logs nor re-raises, so failures leave no trace.
         > except ValueError:
[MEDIUM] broad-except         examples/bad_handler.py:21
         Catches Exception/BaseException instead of the expected error types.
         > except Exception:
----------------------------------------------------
3 finding(s): 1 high, 2 medium, 0 low
```

## Architecture

```text
src/exceptscan/__init__.py  AST walking, handler classification, renderers
src/exceptscan/cli.py       scan / rules / explain and exit codes
tests/test_exceptscan.py    rule, directory, parse-error and CLI tests
```

One finding per handler, chosen by priority: bare → swallowed → broad → silent.
That keeps a single bad handler from producing three overlapping reports.

## Requirements

- Python 3.10+
- pytest for tests

## Installation

```shell
git clone https://github.com/Wsh7Ash/exceptscan.git
cd exceptscan
python -m pip install -e .
```

## Quick start

```shell
exceptscan scan src/
```

## Usage

```shell
# Gate CI on high findings only
exceptscan scan src/ --fail-on high

# Report for a review comment
exceptscan scan pkg/ --json --out results/exceptscan.json

exceptscan rules
exceptscan explain swallowed-exception
```

Exit codes: `0` clean or below threshold, `1` findings at/above `--fail-on`,
`2` path not found.

## Configuration

Flags only: `--json`, `--out`, `--fail-on none|low|medium|high`.

## Testing

```shell
python -m pip install -e . pytest
python -m pytest tests -q
```

## Project structure

```text
exceptscan/
├─ src/exceptscan/      analyser + CLI
├─ tests/               pytest suite
├─ examples/            sample handlers
├─ docs/                architecture, usage, spec
├─ results/             generated reports
└─ .github/workflows/   CI
```

## Limitations

- "Logging" is detected by callee name (`log`, `warn`, `print`, …), not data
  flow; `some_helper(exc)` counts as silent.
- One finding per handler; it will not also mention a specific exception class
  problem inside the body.
- No project configuration, baseline file or inline suppressions yet.
- Only Python; other languages need their own AST.

## Roadmap

- Baseline file for adopting the gate gradually
- Inline `# exceptscan: ignore` comments with justification
- Optional check for `except …: return None` in functions that return values

## License

MIT — see `LICENSE`.
