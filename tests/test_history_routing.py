"""Tests for the history WRITE routing: status writers append to the global sidecar AND keep the full
inline `## Workflow history`, newest-first, with attention `last_history_at` resolving from the newest
(first) inline record.

REWRITTEN BY PLAN `vhbvwz` E-08, AND THE REVERSAL IS THE POINT. awhistory Order 02 (spec
`20260818-1525-02` OQ-2) SLIMMED the inline history of specs and backlog items to the latest one
record, deferring the full log to `.aw/records/history.jsonl`. That sidecar is GITIGNORED
(`.aw/.gitignore`), so the slimmed records never survived a clone and a deliberately recorded reason
was destroyed for every reader but the machine that wrote it. The maintainer ruled on 2026-09-10 that
inline history is the DURABLE home for both types, matching plans. These tests therefore assert
PRESERVATION where they used to assert slimming; the sidecar assertions are unchanged, because the
sidecar is still written and is still a useful machine-local activity log."""

from __future__ import annotations

import contextlib
import io
import tempfile
import types
import unittest
from pathlib import Path

from agent_workflows import backlog, record_history, specs
from agent_workflows import attention_contract as A


class HistoryRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_backlog_set_appends_sidecar_and_preserves_inline(self) -> None:
        """RENAMED FROM `..._and_slims_inline`, which asserted the defect (E-08).

        The sidecar half is unchanged and still asserted. What changed is the inline half: the two
        PRIOR records must still be there afterwards, because they are the item's only
        clone-surviving provenance.
        """
        d = self.root / ".aw" / "records" / "backlog" / "open"
        d.mkdir(parents=True)
        item = d / "20260101-demo-01-aaa111-x.backlog.md"
        item.write_text(
            "- Id: aaa111\n- Status: open\n- Priority: medium\n- Kind: chore\n- Set: demo\n- Summary: x\n\n"
            "## Workflow history\n- 2026-01-02 set (aw backlog): newer\n- 2026-01-01 created (aw backlog): x\n",
            encoding="utf-8",
        )
        args = types.SimpleNamespace(
            path=str(item),
            dir=str(self.root),
            status="done",
            message="finished",
            apply=True,
        )
        rc = backlog.run_set(args)
        self.assertEqual(rc, 0)
        moved = self.root / ".aw" / "records" / "backlog" / "done" / item.name
        text = moved.read_text(encoding="utf-8")
        after = text.split("## Workflow history", 1)[1]
        inline = [ln for ln in after.split("\n") if ln.startswith("- ")]
        # THREE records now: the new one FIRST (newest-first), then both prior ones, in order.
        self.assertEqual(len(inline), 3, inline)
        self.assertIn("finished", inline[0])
        self.assertIn("newer", inline[1])
        self.assertIn("created", inline[2])
        # and the derivation still reports the NEWEST record, which is the new one.
        self.assertEqual(
            A.last_history_at([ln for ln in after.split("\n")]),
            inline[0].split(" ")[1],
        )
        # sidecar STILL has a record for aaa111 (it remains a machine-local activity log).
        recs = record_history.read_for(self.root, "aaa111")
        self.assertTrue(any("finished" in r["message"] for r in recs))

    def test_attention_last_history_at_preserved(self) -> None:
        # a single-record file still yields a last_history_at from that record.
        lines = "## Workflow history\n- 2026-05-05 set (aw backlog): only\n".split("\n")
        self.assertEqual(A.last_history_at(lines), "2026-05-05")

    def test_specs_preserves_inline(self) -> None:
        """RENAMED FROM `test_specs_slims_inline`, which asserted the defect (E-08).

        NOT DELETED, because the case it covers is still the one that matters: what
        `specs._append_history` does to a section that already holds records. The expectation is
        inverted, from "the prior records are gone" to "the prior records are kept and the new one
        leads".
        """
        out = specs._append_history(
            "# S\n\n- Status: draft\n\n## Workflow history\n- 2026-01-02 to-review (t): b\n- 2026-01-01 draft (t): a\n".split(
                "\n"
            ),
            "- 2026-01-03 reviewed (t): c",
        )
        text = "\n".join(out)
        after = text.split("## Workflow history", 1)[1]
        inline = [ln for ln in after.split("\n") if ln.startswith("- ")]
        self.assertEqual(
            inline,
            [
                "- 2026-01-03 reviewed (t): c",
                "- 2026-01-02 to-review (t): b",
                "- 2026-01-01 draft (t): a",
            ],
        )
        # the newest-first ordering is what makes the derivation report the new record's date.
        self.assertEqual(A.last_history_at(after.split("\n")), "2026-01-03")

    def test_specs_note_history_survives_a_fresh_clone(self) -> None:
        """THE DURABILITY PROPERTY ITSELF (E-08/V-08), asserted through a REAL second clone.

        Reading the same working tree cannot distinguish a tracked file from a gitignored one, which
        is exactly how the original defect went unnoticed: the sidecar was readable on the machine
        that wrote it and absent everywhere else. So this commits the spec, clones the repository into
        a separate directory, and reads the note back from the CLONE.
        """
        import subprocess

        def git(*a: str, cwd: Path) -> None:
            subprocess.run(
                ["git", *a],
                cwd=str(cwd),
                check=True,
                capture_output=True,
                env={
                    "GIT_AUTHOR_NAME": "t",
                    "GIT_AUTHOR_EMAIL": "t@example.invalid",
                    "GIT_COMMITTER_NAME": "t",
                    "GIT_COMMITTER_EMAIL": "t@example.invalid",
                    "HOME": str(self.root),
                    "PATH": "/usr/bin:/bin",
                },
            )

        origin = self.root / "origin"
        specs_dir = origin / ".aw" / "records" / "specs"
        specs_dir.mkdir(parents=True)
        # The sidecar is gitignored here exactly as it is in the real repository, so a test that
        # passed by reading the sidecar would fail in the clone.
        (origin / ".aw").joinpath(".gitignore").write_text(
            "records/history.jsonl\n", encoding="utf-8"
        )
        spec = specs_dir / "20260101-0000-01-demo.spec.md"
        spec.write_text(
            "# Spec: demo\n\n- Date: 2026-01-01\n- Status: draft\n\n"
            "## Workflow history\n- 2026-01-01 draft (aw specs): created.\n",
            encoding="utf-8",
        )
        git("init", "-q", cwd=origin)
        git("add", ".aw", cwd=origin)
        git("commit", "-q", "-m", "seed", cwd=origin)

        rc = specs.run_note(
            types.SimpleNamespace(
                path=str(spec),
                message="the reason this decision was made",
                date="2026-02-02",
            )
        )
        self.assertEqual(rc, 0)
        git("add", str(spec.relative_to(origin)), cwd=origin)
        git("commit", "-q", "-m", "note", cwd=origin)

        clone = self.root / "clone"
        subprocess.run(
            ["git", "clone", "-q", str(origin), str(clone)],
            check=True,
            capture_output=True,
            env={"HOME": str(self.root), "PATH": "/usr/bin:/bin"},
        )
        cloned = (clone / ".aw" / "records" / "specs" / spec.name).read_text(
            encoding="utf-8"
        )
        self.assertIn("the reason this decision was made", cloned)
        # and the ORIGINAL record is there too, which is the half the slimming destroyed.
        self.assertIn("- 2026-01-01 draft (aw specs): created.", cloned)
        # while the sidecar is genuinely NOT in the clone, proving the assertion above is about
        # tracked content and not about a file that merely happened to come along.
        self.assertFalse((clone / ".aw" / "records" / "history.jsonl").exists())


class LegacyMultiRecordItemsSurviveATransitionTests(unittest.TestCase):
    """The legacy multi-record corpus is safe BY CONSTRUCTION once nothing slims (plan `vhbvwz` E-03).

    221 tracked backlog items and specs carry more than one inline record (measured at execution with
    the production parser), all of it legacy and committed-only, and under the old behavior ONE
    `aw backlog set` call truncated any of them to a single line. E-08 removes the truncation, so this
    is a VERIFICATION rather than a migration: no tracked file is rewritten to achieve it.

    THE SECOND TEST HERE PINS A REAL DEFECT FOUND DURING THAT VERIFICATION, not a hypothetical. A
    backlog item is free-form prose below its history block, and a bug report about history ordering
    legitimately QUOTES history lines in that prose. An early E-08 implementation scanned the whole
    post-heading region and matched `line.strip()`, so five indented quoted examples in the real item
    `tk1gqo` were promoted into its history: 11 records became 17. The boundary and the column-zero
    rule in `backlog._prior_history_records` exist for that measured reason.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.dir = self.root / ".aw" / "records" / "backlog" / "open"
        self.dir.mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _records(self, path: Path):
        """The records EXACTLY AS THE PRODUCTION READERS SEE THEM: unstripped, so column zero matters.

        Deliberately NOT `.strip()`-ing each line before matching. `HISTORY_RECORD_RE` is anchored at
        `- `, so stripping first makes an INDENTED prose quotation match, which is precisely the
        confusion that produced the defect the second test pins. A test helper that is more permissive
        than the code under test measures the helper, not the code.
        """
        from agent_workflows import attention as att

        text = path.read_text(encoding="utf-8")
        return [
            ln
            for ln in att._history_section_lines(text)
            if A.HISTORY_RECORD_RE.match(ln)
        ]

    def test_a_legacy_item_keeps_every_prior_record_through_a_transition(self) -> None:
        item = self.dir / "20260101-demo-01-lg0001-x.backlog.md"
        item.write_text(
            "- Id: lg0001\n- Status: open\n- Priority: medium\n- Work-Kind: chore\n"
            "- Set: demo\n- Summary: x\n\n"
            "## Workflow history\n"
            "- 2026-03-03 set (aw backlog): third\n"
            "- 2026-02-02 set (aw backlog): second\n"
            "- 2026-01-01 created (aw backlog): first\n",
            encoding="utf-8",
        )
        before = self._records(item)
        self.assertEqual(len(before), 3)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            rc = backlog.run_set(
                types.SimpleNamespace(
                    dir=str(self.root),
                    path=str(item),
                    status="done",
                    message="a real transition",
                    apply=True,
                )
            )
        self.assertEqual(rc, 0)
        moved = self.root / ".aw" / "records" / "backlog" / "done" / item.name
        after = self._records(moved)
        self.assertEqual(len(after), 4, after)
        self.assertIn("a real transition", after[0])
        self.assertEqual(
            after[1:], before, "every prior record must survive verbatim, in order"
        )

    def test_prose_quoted_record_lines_are_not_promoted_into_history(self) -> None:
        """THE MEASURED DEFECT from the E-03 verification, pinned so it cannot return."""
        item = self.dir / "20260101-demo-01-lg0002-x.backlog.md"
        item.write_text(
            "- Id: lg0002\n- Status: open\n- Priority: medium\n- Work-Kind: chore\n"
            "- Set: demo\n- Summary: x\n\n"
            "## Workflow history\n"
            "- 2026-01-01 created (aw backlog): first\n"
            "\n"
            "THE SYMPTOM. This report quotes history lines verbatim:\n"
            "\n"
            "    - 2026-09-02 approved (aw set): a QUOTED example, NOT a record\n"
            "    - 2026-09-01 draft (author): also merely quoted\n"
            "\n"
            "and continues in prose.\n",
            encoding="utf-8",
        )
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            rc = backlog.run_set(
                types.SimpleNamespace(
                    dir=str(self.root),
                    path=str(item),
                    status="done",
                    message="a real transition",
                    apply=True,
                )
            )
        self.assertEqual(rc, 0)
        moved = self.root / ".aw" / "records" / "backlog" / "done" / item.name
        text = moved.read_text(encoding="utf-8")
        after = self._records(moved)
        self.assertEqual(len(after), 2, after)
        self.assertIn("a real transition", after[0])
        self.assertIn("created", after[1])
        # the quoted example appears EXACTLY ONCE: still in the prose, never copied into history.
        self.assertEqual(text.count("a QUOTED example, NOT a record"), 1)


class SidecarFailureIsReportedTests(unittest.TestCase):
    """A failed sidecar write is REPORTED and never costs the inline record (plan `vhbvwz` E-04).

    THE DEFECT: all three call sites wrapped `record_history.append` in a bare
    `except Exception: pass`, so a sidecar failure produced no message, no exit code and no record.
    Paired with the inline slimming that shipped alongside it, a swallowed sidecar write plus a
    successful slim lost the record outright at exit 0.

    THE REMEDY IS DELIBERATELY NARROW, and the shape matters as much as the fix. The inline write is
    NOT made conditional on the sidecar: the maintainer ruled (OQ-01) that inline history is the
    durable home and the sidecar is a machine-local activity log, so gating a durable write on an
    advisory one would invert that model. Each test below therefore asserts BOTH halves - the warning
    appears AND the inline record is present anyway.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._orig_append = record_history.append

    def tearDown(self) -> None:
        record_history.append = self._orig_append
        self._tmp.cleanup()

    def _break_the_sidecar(self) -> None:
        def boom(*_a, **_k):
            raise OSError(28, "No space left on device")

        record_history.append = boom

    def test_backlog_new_reports_and_still_writes_the_inline_record(self) -> None:
        (self.root / ".aw" / "records" / "backlog" / "open").mkdir(parents=True)
        self._break_the_sidecar()
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            rc = backlog.run_new(
                types.SimpleNamespace(
                    dir=str(self.root),
                    summary="a summary",
                    set="demo",
                    priority="medium",
                    work_kind="chore",
                    status="open",
                    message="the recorded reason",
                    body=None,
                    apply=True,
                    blocks_release=None,
                    agent=False,
                    json=False,
                    no_color=True,
                )
            )
        self.assertEqual(rc, 0)
        self.assertIn("could not append to the history sidecar", err.getvalue())
        item = next((self.root / ".aw" / "records" / "backlog" / "open").glob("*.md"))
        self.assertIn("the recorded reason", item.read_text(encoding="utf-8"))

    def test_backlog_set_reports_and_still_writes_the_inline_record(self) -> None:
        d = self.root / ".aw" / "records" / "backlog" / "open"
        d.mkdir(parents=True)
        item = d / "20260101-demo-01-aaa222-x.backlog.md"
        item.write_text(
            "- Id: aaa222\n- Status: open\n- Priority: medium\n- Work-Kind: chore\n"
            "- Set: demo\n- Summary: x\n\n"
            "## Workflow history\n- 2026-01-01 created (aw backlog): x\n",
            encoding="utf-8",
        )
        self._break_the_sidecar()
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            rc = backlog.run_set(
                types.SimpleNamespace(
                    dir=str(self.root),
                    path=str(item),
                    status="done",
                    message="why it is done",
                    apply=True,
                )
            )
        self.assertEqual(rc, 0)
        self.assertIn("could not append to the history sidecar", err.getvalue())
        moved = (
            self.root / ".aw" / "records" / "backlog" / "done" / item.name
        ).read_text(encoding="utf-8")
        self.assertIn("why it is done", moved)
        self.assertIn("- 2026-01-01 created", moved)

    def test_specs_note_reports_and_still_writes_the_inline_record(self) -> None:
        d = self.root / ".aw" / "records" / "specs"
        d.mkdir(parents=True)
        spec = d / "20260101-aaa333-01-aaa333-demo.spec.md"
        spec.write_text(
            "# Spec: demo\n\n- Date: 2026-01-01\n- Status: draft\n- Id: aaa333\n\n"
            "## Workflow history\n- 2026-01-01 draft (aw specs): created.\n",
            encoding="utf-8",
        )
        self._break_the_sidecar()
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            rc = specs.run_note(
                types.SimpleNamespace(
                    path=str(spec), message="the note that matters", date="2026-02-02"
                )
            )
        self.assertEqual(rc, 0)
        self.assertIn("could not append to the history sidecar", err.getvalue())
        self.assertIn("the note that matters", spec.read_text(encoding="utf-8"))

    def test_the_advisory_helper_returns_false_rather_than_raising(self) -> None:
        self._break_the_sidecar()
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            ok = record_history.append_advisory(
                self.root,
                id6="aaa555",
                tree="backlog",
                workflow="aw backlog set",
                actor="aw backlog",
                message="m",
            )
        self.assertFalse(ok)
        self.assertIn("could not append to the history sidecar", err.getvalue())
        # and it returns True on the happy path, so the boolean is meaningful.
        record_history.append = self._orig_append
        self.assertTrue(
            record_history.append_advisory(
                self.root,
                id6="aaa555",
                tree="backlog",
                workflow="aw backlog set",
                actor="aw backlog",
                message="m",
            )
        )


if __name__ == "__main__":
    unittest.main()
