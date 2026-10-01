"""Behavioral tests pinning that write_report tolerates malformed queue entries.

Pins:
  (1) oc_runipd.write_report survives a non-mapping queue entry and writes execution-report.md;
  (2) agy_runipd.write_report survives a non-mapping queue entry and writes execution-report.md;
  (3) - Counts: line accounts for the malformed entry under its own bucket and total equals len(queue);
  (4) Table contains exactly one row for it carrying the malformed-entry status token;
  (5) runner_shared.save_state survives mid-run and writes execution-report.md alongside state.json;
  (6) Well-formed reports remain byte-identical to the pre-fix format fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from agent_workflows import lane_containment


def _make_malformed_state() -> dict[str, Any]:
    return {
        "repo": "/repo",
        "run_id": "run-20260930T000000Z-123456",
        "created_at": "2026-09-30T00:00:00Z",
        "updated_at": "2026-09-30T00:05:00Z",
        "selectors": ["sel1"],
        "set_sessions": {},
        "queue": ["not-a-mapping"],
    }


def _make_well_formed_state() -> dict[str, Any]:
    return {
        "repo": "/repo",
        "run_id": "run-20260930T000000Z-123456",
        "created_at": "2026-09-30T00:00:00Z",
        "updated_at": "2026-09-30T00:05:00Z",
        "selectors": ["sel1"],
        "set_sessions": {"s1": "sess-1"},
        "queue": [
            {
                "position": 1,
                "id6": "abc123",
                "setid": "s1",
                "action": "execute",
                "status": "executed",
                "verification_status": "verified",
                "attempts": [{"session_id": "sess-1"}],
            }
        ],
    }


EXPECTED_WELL_FORMED_OC_REPORT = (
    "# Execution Report: run-20260930T000000Z-123456\n"
    "\n"
    "- Repository: `/repo`\n"
    "- Created: 2026-09-30T00:00:00Z\n"
    "- Updated: 2026-09-30T00:05:00Z\n"
    "- Selectors: `sel1`\n"
    '- Set sessions: `{"s1": "sess-1"}`\n'
    '- Counts: `{"executed": 1}`\n'
    "- Pushed: no (required; verify independently in outcomes)\n"
    "- Launch: model=(host default); profile=(none recorded)\n"
    "\n"
    "| # | id6 | Set | Action | Status | Verify | Attempts | Last session |\n"
    "|---:|---|---|---|---|---|---:|---|\n"
    "| 1 | `abc123` | `s1` | `execute` | executed | verified | 1 | `sess-1` |\n"
    "\n"
    "## Review\n"
    "\n"
    "Review `decisions-and-questions.md` first, then `outcomes/` and `sessions/`.\n"
)

EXPECTED_WELL_FORMED_AGY_REPORT = (
    "# Antigravity IPD Driver Execution Report: run-20260930T000000Z-123456\n"
    "\n"
    "- Repository: `/repo`\n"
    "- Created: 2026-09-30T00:00:00Z\n"
    "- Updated: 2026-09-30T00:05:00Z\n"
    "- Selectors: `sel1`\n"
    '- Set sessions: `{"s1": "sess-1"}`\n'
    '- Counts: `{"executed": 1}`\n'
    "- Pushed: no (required; verify independently in outcomes)\n"
    "\n"
    "| # | id6 | Set | Action | Status | Verify | Attempts | Last session |\n"
    "|---:|---|---|---|---|---|---:|---|\n"
    "| 1 | `abc123` | `s1` | `execute` | executed | verified | 1 | `sess-1` |\n"
    "\n"
    "## Review\n"
    "\n"
    "Review `decisions-and-questions.md` first, then `outcomes/` and `sessions/`.\n"
)


def _extract_counts(report_text: str) -> dict[str, int]:
    for line in report_text.splitlines():
        if line.startswith("- Counts: `") and line.endswith("`"):
            raw = line[len("- Counts: `") : -1]
            return json.loads(raw)
    raise AssertionError(f"Could not find - Counts: line in report:\n{report_text}")


def _extract_table_rows(report_text: str) -> list[str]:
    lines = report_text.splitlines()
    rows = []
    in_table = False
    for line in lines:
        if line.startswith("| # |"):
            in_table = True
            continue
        if in_table:
            if line.startswith("|---"):
                continue
            if line.startswith("|"):
                rows.append(line)
            else:
                break
    return rows


def test_oc_write_report_malformed_entry(tmp_path: Path) -> None:
    state = _make_malformed_state()
    oc_runipd.write_report(tmp_path, state)
    report_file = tmp_path / "execution-report.md"
    assert report_file.is_file(), "execution-report.md must exist after write_report"
    report_text = report_file.read_text(encoding="utf-8")

    counts = _extract_counts(report_text)
    assert counts.get("malformed-entry") == 1
    assert sum(counts.values()) == len(state["queue"])

    rows = _extract_table_rows(report_text)
    assert len(rows) == 1
    assert (
        rows[0]
        == "| 1 | `(unreadable)` | `(unreadable)` | `(unreadable)` | malformed-entry |  | 0 | `` |"
    )


def test_agy_write_report_malformed_entry(tmp_path: Path) -> None:
    state = _make_malformed_state()
    agy_runipd.write_report(tmp_path, state)
    report_file = tmp_path / "execution-report.md"
    assert report_file.is_file(), "execution-report.md must exist after write_report"
    report_text = report_file.read_text(encoding="utf-8")

    counts = _extract_counts(report_text)
    assert counts.get("malformed-entry") == 1
    assert sum(counts.values()) == len(state["queue"])

    rows = _extract_table_rows(report_text)
    assert len(rows) == 1
    assert (
        rows[0]
        == "| 1 | `(unreadable)` | `(unreadable)` | `(unreadable)` | malformed-entry |  | 0 | `` |"
    )


def test_save_state_with_malformed_entry_writes_report_and_state(
    tmp_path: Path,
) -> None:
    state = _make_malformed_state()
    runner_shared.save_state(tmp_path, state, write_report=oc_runipd.write_report)
    assert (tmp_path / "state.json").is_file()
    report_file = tmp_path / "execution-report.md"
    assert report_file.is_file(), "execution-report.md must exist after save_state"
    report_text = report_file.read_text(encoding="utf-8")
    counts = _extract_counts(report_text)
    assert counts.get("malformed-entry") == 1


def test_well_formed_report_byte_identical_to_fixture(tmp_path: Path) -> None:
    state = _make_well_formed_state()

    oc_dir = tmp_path / "oc"
    oc_dir.mkdir()
    oc_runipd.write_report(oc_dir, state)
    oc_report = (oc_dir / "execution-report.md").read_text(encoding="utf-8")
    assert oc_report == EXPECTED_WELL_FORMED_OC_REPORT

    agy_dir = tmp_path / "agy"
    agy_dir.mkdir()
    agy_runipd.write_report(agy_dir, state)
    agy_report = (agy_dir / "execution-report.md").read_text(encoding="utf-8")
    assert agy_report == EXPECTED_WELL_FORMED_AGY_REPORT


def test_section_helpers_tolerate_malformed_entry(tmp_path: Path) -> None:
    state = _make_malformed_state()
    assert runner_shared.render_transient_dependency_waits(state) == []
    assert runner_shared.render_zero_work_notes(state) == []
    assert runner_shared.format_verifier_evidence_section(state, tmp_path) == []
    assert runner_shared.format_generated_next_actions_section(state) == []
    assert lane_containment.format_preserved_lanes(state) == []
