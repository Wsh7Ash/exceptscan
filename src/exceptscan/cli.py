"""Command line interface for exceptscan."""

from __future__ import annotations

import argparse
import sys

from . import (
    RULES,
    at_or_above,
    render_json,
    render_text,
    scan_path,
    summarize,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="exceptscan",
        description="Review Python exception handlers for swallowed or silent failures.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="scan a file or directory")
    scan.add_argument("path")
    scan.add_argument("--json", action="store_true")
    scan.add_argument("--out", help="also write the report to this path")
    scan.add_argument("--fail-on", choices=["none", "low", "medium", "high"], default="medium")

    explain = sub.add_parser("explain", help="explain one rule")
    explain.add_argument("rule", choices=sorted(RULES))
    sub.add_parser("rules", help="list rules")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "rules":
        for rule in sorted(RULES):
            print(f"{rule:20} {RULES[rule]}")
        return 0
    if args.command == "explain":
        print(f"{args.rule}: {RULES[args.rule]}")
        return 0

    try:
        findings = scan_path(args.path)
    except FileNotFoundError:
        print(f"exceptscan: path not found: {args.path}", file=sys.stderr)
        return 2

    report = render_json(findings, args.path) if args.json else render_text(findings, args.path)
    print(report)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(report + "\n")

    summary = summarize(findings)
    if args.fail_on != "none" and at_or_above(findings, args.fail_on):
        print(
            f"exceptscan: {summary['counts']['high']} high / {summary['counts']['medium']} "
            f"medium finding(s) at or above '{args.fail_on}'",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
