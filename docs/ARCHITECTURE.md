# Architecture

## Flow

```text
path ──► iter_python_files (skips .git, .venv, build, node_modules…)
            │
            ▼
        read_text ──► ast.parse ──SyntaxError──► parse-error finding
            │
            ▼
        ast.walk for ExceptHandler
            │
            ├─ type is None            → bare-except (high)
            ├─ body is only `pass`     → swallowed-exception (high)
            ├─ type is Exception/Base  → broad-except (medium)
            ├─ no raise/log-like call  → silent-handler (medium)
            └─ otherwise               → clean
            ▼
        render_text / render_json / exit code
```

## Why AST instead of regex

Text matching reports `except:` inside docstrings and comments, and misses
multi-line handler bodies. The AST gives exact line numbers, handler bodies and
call names, so the rules stay short and the findings stay trustworthy.

## One finding per handler

Priority is deliberate: a bare `except:` with a `pass` body is a bare except,
and reporting both would inflate counts. `swallowed-exception` covers the
narrow-exception case; `broad-except` covers `Exception` handlers that do
respond.

## "Responds" heuristic

A handler responds if its body (or anything nested) contains a `Raise`, or a
`Call` whose function name contains a logging hint (`log`, `warn`, `error`,
`exception`, `critical`, `print`, `notify`, `report`, `emit`, `audit`). This is
intentionally simple and documented as a limitation.

## Error handling

Unreadable files are skipped. A `SyntaxError` is recorded as a low-severity
`parse-error` finding so a broken file cannot silently vanish from a review.
