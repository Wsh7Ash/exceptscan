import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from exceptscan import (
    at_or_above,
    render_json,
    render_text,
    scan_path,
    scan_source,
    summarize,
)
from exceptscan.cli import main

BAD = '''
import logging

def swallowed():
    try:
        work()
    except:
        pass

def silent():
    try:
        work()
    except ValueError:
        return None

def broad():
    try:
        work()
    except Exception as exc:
        logging.error("failed: %s", exc)
'''

GOOD = '''
def handled():
    try:
        work()
    except ValueError as exc:
        print("bad value", exc)
        raise

def logged():
    try:
        work()
    except OSError:
        logger.warning("disk issue")
'''


def test_bare_except_flagged_high():
    findings = scan_source(BAD, "bad.py")
    bare = [f for f in findings if f.rule == "bare-except"]
    assert len(bare) == 1 and bare[0].severity == "high"
    assert bare[0].line > 0 and bare[0].file == "bad.py"


def test_silent_handler_and_broad_except():
    rules = {f.rule for f in scan_source(BAD)}
    assert "silent-handler" in rules
    assert "broad-except" in rules


def test_pure_pass_is_swallowed_even_when_narrow():
    findings = scan_source("try:\n    x()\nexcept KeyError:\n    pass\n")
    assert [f.rule for f in findings] == ["swallowed-exception"]


def test_good_handlers_are_clean():
    assert scan_source(GOOD) == []


def test_syntax_error_becomes_parse_error(tmp_path):
    path = tmp_path / "broken.py"
    path.write_text("def oops(:\n    pass\n", encoding="utf-8")
    findings = scan_path(path)
    assert [f.rule for f in findings] == ["parse-error"]


def test_directory_scan_skips_virtualenvs(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "mod.py").write_text(BAD, encoding="utf-8")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "vendor.py").write_text(BAD, encoding="utf-8")
    findings = scan_path(tmp_path)
    assert {f.file for f in findings} == {str(tmp_path / "pkg" / "mod.py")}


def test_summaries_and_rendering():
    findings = scan_source(BAD)
    summary = summarize(findings)
    assert summary["total"] == 3 and summary["worst"] == "high"
    assert len(at_or_above(findings, "high")) == 1
    assert at_or_above(findings, "none") == []
    text = render_text(findings, "bad.py")
    assert "exceptscan report - bad.py" in text and "finding(s)" in text
    payload = json.loads(render_json(findings, "bad.py"))
    assert payload["summary"]["total"] == 3


def test_cli_scan_rules_and_exit_codes(tmp_path, capsys):
    target = tmp_path / "mod.py"
    target.write_text(BAD, encoding="utf-8")
    assert main(["scan", str(target)]) == 1
    assert main(["scan", str(target), "--fail-on", "none"]) == 0
    capsys.readouterr()
    assert main(["scan", str(target), "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["total"] == 3

    clean = tmp_path / "clean.py"
    clean.write_text(GOOD, encoding="utf-8")
    assert main(["scan", str(clean)]) == 0
    assert main(["scan", str(tmp_path / "missing.py")]) == 2
    assert main(["rules"]) == 0
    assert main(["explain", "bare-except"]) == 0
