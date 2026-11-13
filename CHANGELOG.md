# Changelog

## [1.0.0] - 2026-11-14

### Added

- AST scanner for four exception-handling smells with severity and file:line.
- Recursive directory scan with virtualenv/build skips.
- `parse-error` findings for unreadable syntax instead of a crash.
- Text/JSON reports, `--out`, `--fail-on`, `rules` and `explain`.
- pytest suite covering every rule, directory behaviour and CLI exit codes.
