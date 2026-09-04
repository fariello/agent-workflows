"""Characterization + regression tests for the `aw run` / `aw runs` noun split (IPD `0soncw`).

WHY THIS FILE EXISTS, and why it is NOT in `tests/test_run_viewer.py`: that file is documented as
reading the LIVE repository (see its module docstring; 15 of its tests fail in a fresh clone because
`.aw/records/runs/` is gitignored, tracked as backlog `agrlvw`). Every test here builds its own
temp-dir fixture, so its verdict is a property of the CODE, not of the machine.

The split under test (maintainer ruling 2026-08-31, recorded in `0soncw` OQ-03):

  * `aw run`  WRITES: `start`, `record`, `cancel`, `finalize` stay put.
  * `aw runs` READS:  `show`, `status`, `list`, `next`, `resume`, `decisions`, `questions`,
                      `evidence`, `verify-ledger` move here (`next`/`resume` only reconstruct state
                      and report, so they are viewers despite sounding like actions).

Three falsifiable groups:

1. `LeafSurfaceCharacterizationTests` (E-01/V-01) pins the EXIT CLASS of all twelve leaves at their
   post-split spelling, plus the bare viewer's argv shapes and flag binding. It is the safety net
   proving the move preserved behaviour: it was written against the pre-change `aw run <leaf>`
   spelling, observed passing, and then flipped to the new spelling.
2. `DuplicateRenderingGuardTests` (E-02/V-02) asserts no two distinct invocations render the same
   viewer output. Seeded with the historical `aw run list` vs `aw runs` pair. It compares NORMALIZED
   output over a FIXTURE ledger, never raw bytes of live output: a raw comparison was measured to
   differ on `runtime:` lines alone for live pids, which would make the guard flake for a reason
   unrelated to the duplication it exists to catch.
3. `MovedLeafRemovalTests` (E-05/V-05) asserts each moved leaf is REJECTED under `aw run` by normal
   argument parsing with a nonzero exit and no ledger write - not silently forwarded, because silent
   aliasing is exactly how the `run list` duplicate survived unnoticed.
"""

from __future__ import annotations

import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Dict, List, Tuple

from agent_workflows import cli
from agent_workflows import run_ledger_schema as schema
from agent_workflows import run_ledger_store as ledger_store

# The split, as ruled. Kept as module constants so a future reader can see the whole contract in one
# place, and so a leaf silently appearing/disappearing changes a test outcome rather than a comment.
VIEWER_LEAVES: Tuple[str, ...] = (
    "show",
    "status",
    "list",
    "next",
    "resume",
    "decisions",
    "questions",
    "evidence",
    "verify-ledger",
)
WRITER_LEAVES: Tuple[str, ...] = ("start", "record", "cancel", "finalize")

RUN_ID = "run-abcdef1234"
HEAD = "1" * 40


def _run_record() -> Dict[str, Any]:
    return {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "run",
        "run_id": RUN_ID,
        "actor": "runtime",
        "workflow_digest": "a" * 64,
        "requirement_digest": "b" * 64,
        "repo": "agent-workflows",
        "head": HEAD,
        "parent": "",
    }


def _requirement_set(reqs: List[str]) -> Dict[str, Any]:
    return {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "requirement_set",
        "run_id": RUN_ID,
        "actor": "runtime",
        "requirement_digest": "b" * 64,
        "requirements": [{"id": r} for r in reqs],
        "scope_fence": {},
        "parent": "",
    }


def _cli(*argv: str) -> Tuple[int, str]:
    """Invoke the real CLI in-process, capturing stdout+stderr. Returns (rc, combined output)."""
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            rc = cli.main(list(argv))
    except SystemExit as exc:  # argparse usage errors exit rather than return
        rc = int(exc.code or 0)
    return rc, out.getvalue() + err.getvalue()


class _LedgerFixture(unittest.TestCase):
    """A temp repo holding one real (incomplete) ledger plus one driver run dir for the viewer."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

        run_dir = self.root / ".aw" / "records" / "runs" / RUN_ID
        run_dir.mkdir(parents=True)
        self.ledger = run_dir / ledger_store.LEDGER_FILENAME
        store = ledger_store.RunLedgerStore(self.ledger)
        store.append(_run_record())
        store.append(_requirement_set(["R-01"]))

        # A driver run dir the VIEWER can summarize (state.json, not a ledger).
        self.viewer_run = "run-20260829T000000Z-111111"
        vdir = self.root / ".aw" / "records" / "runs" / self.viewer_run
        vdir.mkdir(parents=True)
        (vdir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": self.viewer_run,
                    "setid": "charz",
                    "queue": [
                        {
                            "position": 1,
                            "id6": "item01",
                            "setid": "charz",
                            "action": "execute",
                            "status": "complete",
                            "configured_file": "",
                            "stem": "20260829-charz-01-item01",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )


class LeafSurfaceCharacterizationTests(_LedgerFixture):
    """E-01/V-01: pin the parse + exit CLASS of all twelve leaves and the bare viewer shapes."""

    # Exit CLASS per leaf on this fixture (an incomplete but well-formed ledger). Pinning the class
    # rather than a message keeps the test about the surface, not about wording.
    #   show/status      -> 1 incomplete
    #   next             -> 3 nothing runnable
    #   resume/evidence
    #   verify-ledger    -> 0 clean-but-incomplete is still a valid read
    #   decisions/quest. -> 2 no projection for this run
    #   start/record     -> 2 missing --step/--state
    #   cancel           -> 0 records a terminal cancellation
    #   finalize         -> 1 incomplete, refuses
    EXPECTED_EXIT: Dict[str, int] = {
        "show": 1,
        "status": 1,
        "next": 3,
        "resume": 0,
        "evidence": 0,
        "verify-ledger": 1,
        "decisions": 2,
        "questions": 2,
        "start": 2,
        "record": 2,
        "cancel": 0,
        "finalize": 1,
    }

    def test_all_twelve_leaves_are_covered_by_this_characterization(self) -> None:
        """Guard the guard: a leaf added to either noun without a pinned exit class fails here.

        `list` is excluded from the exit-class table because it is the VIEWER under its own name: it
        takes `targets nargs="*"`, not the single required `target` every other leaf takes, so its
        exit class is the viewer's, asserted separately.
        """
        self.assertEqual(
            (set(VIEWER_LEAVES) | set(WRITER_LEAVES)) - {"list"},
            set(self.EXPECTED_EXIT),
            "the twelve-leaf surface changed; pin the new leaf's exit class",
        )
        self.assertEqual(len(VIEWER_LEAVES), 9)
        self.assertEqual(len(WRITER_LEAVES), 4)
        # THIRTEEN parser leaves across the two nouns: the TWELVE that carry a declaration in
        # `command_surface.COMMAND_INVENTORY` (each with a pinned exit class above), plus `list`,
        # which was a registered parser leaf without its own declaration before this split.
        self.assertEqual(len(set(VIEWER_LEAVES) | set(WRITER_LEAVES)), 13)
        self.assertEqual(len(self.EXPECTED_EXIT), 12)

    def test_viewer_leaves_parse_and_keep_their_exit_class_under_runs(self) -> None:
        for leaf in VIEWER_LEAVES:
            with self.subTest(leaf=leaf):
                target = self.viewer_run if leaf == "list" else str(self.ledger)
                rc, out = _cli("runs", leaf, target, "--dir", str(self.root))
                if leaf == "list":
                    # `list` is the viewer leaf: it renders the table, exit 0.
                    self.assertEqual(rc, 0, out)
                else:
                    self.assertEqual(rc, self.EXPECTED_EXIT[leaf], f"{leaf}: {out}")
                self.assertNotIn("invalid choice", out)

    def test_writer_leaves_parse_and_keep_their_exit_class_under_run(self) -> None:
        for leaf in WRITER_LEAVES:
            with self.subTest(leaf=leaf):
                rc, out = _cli("run", leaf, str(self.ledger), "--dir", str(self.root))
                self.assertEqual(rc, self.EXPECTED_EXIT[leaf], f"{leaf}: {out}")
                self.assertNotIn("invalid choice", out)

    def test_leaf_specific_flags_still_bind(self) -> None:
        """The moved/retained leaves keep their own flags; a flag that stopped binding fails here."""
        rc, out = _cli(
            "runs",
            "decisions",
            RUN_ID,
            "--dir",
            str(self.root),
            "--workflow",
            "exec-set",
        )
        self.assertEqual(rc, 2, out)  # no projection dir in the fixture
        rc, out = _cli(
            "run",
            "record",
            str(self.ledger),
            "--dir",
            str(self.root),
            "--step",
            "S-01",
            "--state",
            "bogus",
        )
        self.assertEqual(rc, 2, out)
        self.assertIn("invalid --state", out)

    def test_bare_viewer_argv_shapes_all_render(self) -> None:
        """The four viewer shapes the ruling promises to preserve: bare, run-id, set-id, multi."""
        for argv in (
            (),
            (self.viewer_run,),
            ("charz",),
            (self.viewer_run, "charz"),
        ):
            with self.subTest(argv=argv):
                rc, out = _cli("runs", *argv, "--dir", str(self.root))
                self.assertEqual(rc, 0, out)
                self.assertIn(self.viewer_run[:18], out)

    def test_viewer_flags_bind_after_a_positional_target(self) -> None:
        """REGRESSION GUARD for the routing mechanism.

        A naive custom-action implementation swallows every remaining token as a target, so
        `aw runs <id> --dir X -i` silently loses `--dir`/`-i`. This asserts they still bind, which is
        the specific defect the chosen mechanism had to avoid.
        """
        rc, out = _cli("runs", self.viewer_run, "--dir", str(self.root), "--issues")
        self.assertEqual(rc, 0, out)
        self.assertNotIn("no matching runs found", out)
        # `-l/--last` takes an optional value; it must still parse after a target.
        rc, out = _cli("runs", "--dir", str(self.root), "--last", "1")
        self.assertEqual(rc, 0, out)

    def test_leaf_name_as_viewer_target_is_reachable_via_the_escape_hatch(self) -> None:
        """E-03's documented ambiguity rule + its escape hatch.

        A first positional that exactly equals a leaf name routes to the LEAF (documented rule), so a
        Set literally named `status` needs `--` to be reachable as a viewer target. No such collision
        exists in the repo today, but the rule must be exercised, not merely asserted in prose.
        """
        # Bare `runs status` routes to the LEAF, which then demands its own required target.
        rc, out = _cli("runs", "status", "--dir", str(self.root))
        self.assertNotEqual(rc, 0)
        self.assertIn("target", out)
        self.assertIn("runs status", out)  # the LEAF's usage, not the viewer's
        # `--` forces VIEWER interpretation: the token becomes a target selector. Asserted by the
        # viewer table being rendered at all, which the leaf path can never do.
        rc, out = _cli("runs", "--dir", str(self.root), "--", "status")
        self.assertEqual(rc, 0, out)
        self.assertNotIn("the following arguments are required", out)
        # A token that matches nothing renders the viewer's own empty-state, still not a leaf error.
        rc, out = _cli("runs", "--dir", str(self.root), "--", "no-such-target-xyz")
        self.assertEqual(rc, 0, out)
        self.assertIn("no matching runs found", out)

    def test_runs_repair_verb_still_routes(self) -> None:
        """The pre-existing positionally-routed MUTATING verb must survive the split (ssk6nf E-04)."""
        # NOTE the argv ORDER: all positionals first, then flags. Interleaving a flag BETWEEN two
        # positionals (`runs repair --dir X <id>`) is rejected by argparse's `nargs="*"` handling,
        # which is PRE-EXISTING behaviour of the bare viewer and not part of this split.
        rc, out = _cli("runs", "repair", self.viewer_run, "--dir", str(self.root))
        self.assertEqual(rc, 0, out)
        self.assertIn("nothing to repair", out)


def _normalize(text: str) -> str:
    """Mask volatile fields so two renderings of the SAME data compare equal deterministically.

    Measured need (`0soncw` PR-003/F-1): `aw run list` and `aw runs` differed on 2 of 1031 lines
    purely because the viewer prints elapsed wall-clock for live pids (`runtime: 31m 19s` vs
    `31m 21s`). A raw byte comparison would therefore flake for a reason unrelated to duplication.
    Masked here: runtime/elapsed durations, absolute timestamps, and pids.
    """
    text = re.sub(r"(runtime|elapsed):\s*\S+(\s+\S+)?", r"\1: <MASKED>", text)
    text = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?Z?", "<TS>", text)
    text = re.sub(r"pid:\s*\d+", "pid: <PID>", text)
    text = re.sub(r"\b\d+[hms]\s*\d*[ms]?\b", "<DUR>", text)
    return text


class DuplicateRenderingGuardTests(_LedgerFixture):
    """E-02/V-02: no two DISTINCT invocations may render the same viewer output.

    Seeded with the historical `aw run list` / `aw runs` pair, which is why this test FAILED at
    pre-change HEAD (both spellings reached one renderer) and passes now that only one spelling
    exists. A guard never observed failing is not evidence, so its failure was captured before the
    change and pasted into the plan's V-02.
    """

    #: Invocations that must each be either UNIQUE in what they render, or rejected outright.
    #: `("runs", "list")` is deliberately ABSENT: it is an INTENTIONAL, documented alias of the bare
    #: viewer registered from the same shared flag parent, which is a different thing from the defect
    #: this guard exists to catch. The defect was a duplicate ACROSS NOUNS (`aw run list` vs
    #: `aw runs`) that made the retired noun look like a live inspection surface. The alias is pinned
    #: by `test_runs_list_is_a_declared_alias_of_the_bare_viewer` instead, so it cannot silently
    #: diverge either.
    CANDIDATE_SPELLINGS: Tuple[Tuple[str, ...], ...] = (
        ("runs",),
        ("run", "list"),
        ("run", "runs"),
        ("run", "summary"),
        ("run", "viewer"),
    )

    def _render(self, argv: Tuple[str, ...]) -> Tuple[int, str]:
        rc, out = _cli(*argv, "--dir", str(self.root))
        return rc, _normalize(out)

    def test_no_two_spellings_render_identical_viewer_output(self) -> None:
        rendered: Dict[str, Tuple[str, ...]] = {}
        for argv in self.CANDIDATE_SPELLINGS:
            rc, out = self._render(argv)
            if rc != 0:
                # A rejected spelling renders nothing; rejection is the desired end state for the
                # retired duplicates, so it is not a collision candidate.
                continue
            if out in rendered:
                self.fail(
                    "duplicate rendering: `aw {0}` and `aw {1}` produce identical output; "
                    "one job must have one name".format(
                        " ".join(rendered[out]), " ".join(argv)
                    )
                )
            rendered[out] = argv
        self.assertTrue(rendered, "no spelling rendered the viewer at all")

    def test_exactly_one_spelling_renders_the_viewer_table(self) -> None:
        succeeded = [
            argv for argv in self.CANDIDATE_SPELLINGS if self._render(argv)[0] == 0
        ]
        self.assertEqual(
            succeeded,
            [("runs",)],
            f"expected only bare `aw runs` to render the viewer, got {succeeded}",
        )

    def test_runs_list_is_a_declared_alias_of_the_bare_viewer(self) -> None:
        """`aw runs list` is INTENDED to equal bare `aw runs`, and must keep equalling it.

        This is the counterpart to the guard above: the alias is legitimate (one renderer, one
        registration, one shared flag parent), so it is asserted EQUAL here rather than flagged as a
        duplicate. If someone gives `list` its own divergent behaviour, this fails.
        """
        bare_rc, bare_out = self._render(("runs",))
        list_rc, list_out = self._render(("runs", "list"))
        self.assertEqual(bare_rc, list_rc)
        self.assertEqual(bare_out, list_out)

    def test_guard_is_stable_across_repeated_runs(self) -> None:
        """Stability proof: the normalized rendering is identical on two consecutive calls."""
        first = self._render(("runs",))
        second = self._render(("runs",))
        self.assertEqual(first, second)


class MovedLeafRemovalTests(_LedgerFixture):
    """E-05/V-05: the nine moved leaves are GONE from `aw run`, loudly, with no ledger write."""

    def test_every_moved_leaf_is_rejected_under_the_old_noun(self) -> None:
        for leaf in VIEWER_LEAVES:
            with self.subTest(leaf=leaf):
                rc, out = _cli("run", leaf, str(self.ledger), "--dir", str(self.root))
                self.assertNotEqual(rc, 0, f"`aw run {leaf}` must not succeed: {out}")
                self.assertIn("invalid choice", out)

    def test_rejection_performs_no_ledger_write(self) -> None:
        before = self.ledger.read_bytes()
        listing_before = sorted(p.name for p in self.ledger.parent.iterdir())
        _cli("run", "show", str(self.ledger), "--dir", str(self.root))
        self.assertEqual(self.ledger.read_bytes(), before)
        self.assertEqual(
            sorted(p.name for p in self.ledger.parent.iterdir()), listing_before
        )

    def test_the_writing_noun_still_works(self) -> None:
        """`aw run` is NOT retired: retiring it would break the `runprofile` Set's `aw run as`."""
        rc, out = _cli("run", "cancel", str(self.ledger), "--dir", str(self.root))
        self.assertEqual(rc, 0, out)
        self.assertIn("Cancelled run", out)

    def test_bare_run_help_advertises_only_the_writing_leaves(self) -> None:
        """`aw run`'s own help must not still sell the leaves it no longer has (E-07)."""
        rc, out = _cli("run")
        for writer in WRITER_LEAVES:
            self.assertIn(writer, out, f"`aw run` help omits its own leaf {writer!r}")
        # The choice list argparse prints is the authoritative surface; it must hold only writers.
        self.assertIn("{start,record,cancel,finalize}", out)
        # And the prose must not describe a moved leaf as if `aw run` still provided it.
        for moved in ("verify-ledger", "evidence"):
            self.assertNotIn(
                f"aw run {moved}", out, f"`aw run` help still advertises {moved!r}"
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
