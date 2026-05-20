#!/usr/bin/env python3
"""Write coverage/REPORT.md from coverage/coverage.json (pytest-cov output)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _count_tests(root: Path) -> int | None:
    try:
        out = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
            env={**__import__("os").environ, "PYTHONPATH": str(root / "src")},
        )
    except subprocess.CalledProcessError:
        return None
    total = 0
    for line in out.stdout.splitlines():
        head, _, tail = line.rpartition(": ")
        if head.endswith(".py") and tail.strip().isdigit():
            total += int(tail.strip())
    return total if total else None


def _module_rows(files: dict) -> list[tuple[str, float, int, int, str]]:
    rows: list[tuple[str, float, int, int, str]] = []
    prefix = "src/event_ledger_api/"
    for path in sorted(files):
        if prefix not in path:
            continue
        entry = files[path]
        summary = entry["summary"]
        name = path.split(prefix, 1)[-1]
        missing_line_nums = entry.get("missing_lines") or []
        missing_note = ", ".join(str(n) for n in missing_line_nums[:12])
        if len(missing_line_nums) > 12:
            missing_note += f", … (+{len(missing_line_nums) - 12} more)"
        rows.append(
            (
                name,
                summary["percent_covered"],
                summary["covered_lines"],
                summary["num_statements"],
                missing_note or "—",
            )
        )
    return rows


def _suite_breakdown(root: Path) -> list[tuple[str, int]]:
    tests_dir = root / "tests"
    if not tests_dir.is_dir():
        return []
    rows: list[tuple[str, int]] = []
    for path in sorted(tests_dir.rglob("test_*.py")):
        rel = path.relative_to(tests_dir)
        count = path.read_text(encoding="utf-8").count("def test_")
        rows.append((str(rel.parent or "."), count))
    by_dir: dict[str, int] = {}
    for folder, count in rows:
        by_dir[folder] = by_dir.get(folder, 0) + count
    return sorted(by_dir.items())


def main() -> int:
    root = _repo_root()
    json_path = root / "coverage" / "coverage.json"
    if not json_path.is_file():
        print(f"error: missing {json_path} — run ./scripts/coverage.sh first", file=sys.stderr)
        return 1

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    totals = payload["totals"]
    percent = totals["percent_covered"]
    stmts = totals["num_statements"]
    covered = totals["covered_lines"]
    missed = totals["missing_lines"]
    branches = int(totals.get("num_branches") or 0)
    branches_covered = int(totals.get("covered_branches") or 0)
    branch_pct = float(totals.get("percent_branches_covered") or 0.0)

    test_count = _count_tests(root)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    module_rows = _module_rows(payload["files"])
    suite_rows = _suite_breakdown(root)

    lines = [
        "# Test coverage report",
        "",
        f"Generated: **{generated_at}**",
        "",
        "Regenerate after code or test changes:",
        "",
        "```bash",
        "./scripts/coverage.sh",
        "```",
        "",
        "Interactive HTML (local only, not committed): `coverage/html/index.html`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|------:|",
        f"| Tests collected | {test_count if test_count is not None else '—'} |",
        f"| Statements | {stmts} |",
        f"| Lines covered | {covered} |",
        f"| Lines missed | {missed} |",
        f"| **Line coverage** | **{percent:.1f}%** |",
    ]
    if branches:
        lines.append(f"| Branch coverage | {branch_pct:.1f}% ({branches_covered}/{branches}) |")

    lines.extend(
        [
            "",
            "## Coverage by module (`event_ledger_api`)",
            "",
            "| Module | Line % | Covered / Stmts | Uncovered lines |",
            "|--------|-------:|----------------:|-----------------|",
        ]
    )
    for name, pct, cov, total, missing in module_rows:
        lines.append(f"| `{name}` | {pct:.1f}% | {cov}/{total} | {missing} |")

    if suite_rows:
        lines.extend(
            [
                "",
                "## Test suite layout",
                "",
                "| Directory | Tests (`def test_`) |",
                "|-----------|--------------------:|",
            ]
        )
        for folder, count in suite_rows:
            lines.append(f"| `tests/{folder}` | {count} |")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Coverage measures `src/event_ledger_api` only (application code under test).",
            "- Regenerate with `./scripts/coverage.sh` after changes; `fail_under = 100` in `pyproject.toml`.",
            "- Machine-readable detail: `coverage/coverage.json`.",
            "",
        ]
    )

    report_path = root / "coverage" / "REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
