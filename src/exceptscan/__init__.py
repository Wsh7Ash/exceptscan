"""exceptscan - find the exception handlers that hide failures.

Python makes it easy to catch everything and do nothing. This module walks the
AST (not text) and reports four review smells: bare ``except``, handlers whose
whole body is ``pass``, overly broad ``Exception``/``BaseException`` catches,
and handlers that neither log nor re-raise.
"""

from __future__ import annotations

import ast
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3}

RULES = {
    "bare-except": "A bare 'except:' also catches KeyboardInterrupt and SystemExit.",
    "swallowed-exception": "The handler body is only 'pass', so the failure disappears.",
    "broad-except": "Catches Exception/BaseException instead of the expected error types.",
    "silent-handler": "The handler neither logs nor re-raises, so failures leave no trace.",
    "parse-error": "The file could not be parsed, so it was not reviewed.",
}

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "env", "build", "dist", ".pytest_cache", "node_modules"}
LOG_HINTS = ("log", "warn", "error", "exception", "critical", "print", "notify", "report", "emit", "audit")


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    file: str
    line: int
    column: int
    message: str
    snippet: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _handler_snippet(source_lines: Sequence[str], node: ast.ExceptHandler) -> str:
    if 1 <= node.lineno <= len(source_lines):
        return source_lines[node.lineno - 1].strip()
    return ""


def _call_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr.lower()
    if isinstance(func, ast.Name):
        return func.id.lower()
    return ""


def _handler_responds(body: Sequence[ast.stmt]) -> bool:
    for statement in body:
        if isinstance(statement, ast.Raise):
            return True
        for node in ast.walk(statement):
            if isinstance(node, ast.Call) and any(hint in _call_name(node) for hint in LOG_HINTS):
                return True
    return False


def _is_pure_pass(body: Sequence[ast.stmt]) -> bool:
    return bool(body) and all(isinstance(statement, ast.Pass) for statement in body)


def scan_source(source: str, filename: str = "<string>") -> list[Finding]:
    """Parse ``source`` and return findings. Raises SyntaxError on bad input."""
    tree = ast.parse(source, filename)
    lines = source.splitlines()
    findings: list[Finding] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        snippet = _handler_snippet(lines, node)
        base = dict(file=filename, line=node.lineno, column=node.col_offset + 1, snippet=snippet)

        if node.type is None:
            findings.append(Finding("bare-except", "high", message=RULES["bare-except"], **base))
        elif _is_pure_pass(node.body):
            findings.append(
                Finding("swallowed-exception", "high", message=RULES["swallowed-exception"], **base)
            )
        elif isinstance(node.type, ast.Name) and node.type.id in {"Exception", "BaseException"}:
            findings.append(Finding("broad-except", "medium", message=RULES["broad-except"], **base))
        elif not _handler_responds(node.body):
            findings.append(Finding("silent-handler", "medium", message=RULES["silent-handler"], **base))

    return findings


def scan_file(path: str | os.PathLike[str]) -> list[Finding]:
    text_path = Path(path)
    try:
        source = text_path.read_text(encoding="utf-8")
    except OSError:
        return []
    try:
        return scan_source(source, str(text_path))
    except SyntaxError as exc:
        return [
            Finding(
                "parse-error", "low", str(text_path), exc.lineno or 0, exc.offset or 0,
                f"{RULES['parse-error']} ({exc.msg})",
            )
        ]


def iter_python_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for directory, subdirs, files in os.walk(root):
        subdirs[:] = [name for name in subdirs if name not in SKIP_DIRS]
        for name in sorted(files):
            if name.endswith(".py"):
                yield Path(directory) / name


def scan_path(path: str | os.PathLike[str]) -> list[Finding]:
    root = Path(path)
    if not root.exists():
        raise FileNotFoundError(str(path))
    findings: list[Finding] = []
    for file_path in iter_python_files(root):
        findings.extend(scan_file(file_path))
    return findings


def summarize(findings: Sequence[Finding]) -> dict:
    counts = {"high": 0, "medium": 0, "low": 0}
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    worst = "none"
    for severity in ("high", "medium", "low"):
        if counts.get(severity):
            worst = severity
            break
    return {"total": len(findings), "counts": counts, "worst": worst}


def at_or_above(findings: Sequence[Finding], threshold: str) -> list[Finding]:
    if threshold == "none":
        return []
    limit = SEVERITY_ORDER[threshold]
    return [f for f in findings if SEVERITY_ORDER[f.severity] >= limit]


def render_text(findings: Sequence[Finding], target: str = "") -> str:
    summary = summarize(findings)
    lines = [f"exceptscan report{f' - {target}' if target else ''}", "=" * 52]
    if not findings:
        lines.append("No exception-handling smells found.")
        return "\n".join(lines)
    ordered = sorted(findings, key=lambda f: (-SEVERITY_ORDER[f.severity], f.file, f.line))
    for finding in ordered:
        lines.append(f"[{finding.severity.upper():6}] {finding.rule:20} {finding.file}:{finding.line}")
        lines.append(f"         {finding.message}")
        if finding.snippet:
            lines.append(f"         > {finding.snippet}")
    lines.append("-" * 52)
    lines.append(
        f"{summary['total']} finding(s): {summary['counts']['high']} high, "
        f"{summary['counts']['medium']} medium, {summary['counts']['low']} low"
    )
    return "\n".join(lines)


def render_json(findings: Sequence[Finding], target: str = "") -> str:
    payload = {"target": target, "summary": summarize(findings), "findings": [f.to_dict() for f in findings]}
    return json.dumps(payload, indent=2)
