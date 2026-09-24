"""bkclose (zhr6mc): the runner closes a backlog item when it executes the last carrier.

THE DEFECT THIS PINS. `graduated` means "design handed off, code not written" and `done` means
"written and validated", but NOTHING advanced an item across that boundary: neither runner read a
plan's `- From-Backlog:` link at all (`grep -n "From-Backlog" agent_workflows/oc_runipd.py` returned
nothing), no automation moved `graduated` -> `done`, and the one warning that would nag inspects
`open/` only, so a graduated item was invisible to it. Measured at authoring: ZERO items in `done/`
carried a graduation record, i.e. the transition had never once occurred.

Separately, `SIGTERM` had NO handler in either runner, so a `kill` of the driver ran no `except` and
no `finally` and printed nothing at all; `SIGINT` was caught only incidentally as `KeyboardInterrupt`
at the `main` boundary. Executed plan `bds6nd` has since landed
`render_stream.install_exit_signal_handler`, which registers SIGTERM OUTSIDE the two guarded runner
modules and raises `KeyboardInterrupt("Terminated by SIGTERM")`, so both signals now converge on the
one `except KeyboardInterrupt` funnel and the report is emitted on both (130 / 143).

WHAT IS ASSERTED HERE:
  * the `From-Backlog` round trip through BOTH drivers' record-building and queue-freezing paths,
    contrasted with the measured pre-fix absence, and reading the field name from
    `ipd_schema.META_FROM_BACKLOG` rather than a new regex;
  * the IPD closing rule (every IPD carrier executed) and the non-IPD rule (the artifact exists,
    regardless of its review/approval status), including the MIXED case where the IPD rule dominates;
  * the E-04 earned-close gate, and fail-closed behavior for an induced lookup or setter failure;
  * the gated setter FORM (`--status done --evidence`), because the positional spelling bypasses the
    shared release-gate close predicate entirely;
  * the unclosed-item report with a reason per item, on normal exit and under both signals, ledger
    BEFORE print, idempotent under a repeated signal;
  * the `aw runs <run-id>` pointer, present in human output and absent from `--json`;
  * an ANTI-DIVERGENCE guard: the two drivers must share ONE implementation (object identity), so a
    one-runner-only fix fails.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePath
from unittest import mock

from agent_workflows import (
    agy_runipd,
    check_engine,
    ipd_schema,
    oc_runipd,
    runner_shared,
)
from tests.support import REPO_ROOT

_DRIVERS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))
_DRIVER_SOURCES = (
    ("oc_runipd", REPO_ROOT / "agent_workflows" / "oc_runipd.py"),
    ("agy_runipd", REPO_ROOT / "agent_workflows" / "agy_runipd.py"),
)


# `_code_only` was DELETED with its last caller (audit 2026-09-19). It tokenized product source and
# stripped comments and string literals so a search could assert about CODE rather than prose, which
# made the searches it served LESS bad but not good: every one still asserted a token was or was not
# typed. Its mirror in `tests/test_runner_item_dependencies.py` is where the repository's measured
# vacuity incident lives -- a guard searched that stripped output for the string literal `"queued"`,
# which the stripping had already removed, so the pattern could never match. All four callers here now
# drive the code instead.


def _plan_text(
    id6: str,
    *,
    from_backlog: str | None = None,
    setid: str = "demo",
    order: int = 1,
    status: str = "approved",
) -> str:
    """A minimal plan whose metadata block the structural reader accepts."""
    lines = [
        f"# IPD: {id6}",
        "",
        "- Date: 2026-08-30",
        "- Kind: child",
        f"- Status: {status}",
        f"- Set: {setid} (the {setid} set)",
        f"- Order: {order}",
        f"- Id: {id6}",
    ]
    if from_backlog is not None:
        lines.append(f"- From-Backlog: {from_backlog}")
    lines += ["", "## Goal", "", "Do the thing.", ""]
    return "\n".join(lines)


def _spec_text(id6: str, *, from_backlog: str, status: str = "draft") -> str:
    return "\n".join(
        [
            f"# Spec: {id6}",
            "",
            "- Date: 2026-08-30",
            f"- Id: {id6}",
            f"- Status: {status}",
            f"- From-Backlog: {from_backlog}",
            "",
            "## Summary",
            "",
            "A spec.",
            "",
        ]
    )


def _item_text(id6: str, *, status: str = "graduated", blocks_release: str = "") -> str:
    lines = [
        f"- Id: {id6}",
        f"- Status: {status}",
        "- Set: demo",
        "- Priority: medium",
        "- Kind: feature",
        "- Summary: a demo item",
    ]
    if blocks_release:
        lines.append(f"- Blocks-Release: {blocks_release}")
    lines += ["", "## Workflow history", f"- 2026-08-30 {status} (test): created.", ""]
    return "\n".join(lines)


class _Repo:
    """A throwaway git repo with a backlog tree, plans tree, and specs tree."""

    def __init__(self, root: Path) -> None:
        self.root = root
        for rel in (
            ".aw/records/backlog/graduated",
            ".aw/records/backlog/open",
            ".aw/records/backlog/done",
            ".aw/records/plans/pending",
            ".aw/records/plans/executed",
            ".aw/records/specs",
        ):
            (root / rel).mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", "."], cwd=root, check=True)

    def add_item(self, id6: str, **kw) -> Path:
        status = kw.get("status", "graduated")
        path = (
            self.root
            / ".aw/records/backlog"
            / status
            / f"20260830-demo-01-{id6}-demo-item.backlog.md"
        )
        path.write_text(_item_text(id6, **kw), encoding="utf-8")
        return path

    def add_plan(self, id6: str, *, bucket: str = "pending", **kw) -> Path:
        path = (
            self.root
            / ".aw/records/plans"
            / bucket
            / f"20260830-demo-0{kw.get('order', 1)}-{id6}-a-plan.ipd.md"
        )
        path.write_text(_plan_text(id6, **kw), encoding="utf-8")
        return path

    def add_spec(self, id6: str, **kw) -> Path:
        path = (
            self.root / ".aw/records/specs" / f"20260830-{id6}-01-{id6}-a-spec.spec.md"
        )
        path.write_text(_spec_text(id6, **kw), encoding="utf-8")
        return path

    def rel(self, path: Path) -> str:
        return str(path.resolve().relative_to(self.root.resolve()))

    def item_status(self, id6: str) -> str | None:
        """The DIRECTORY status of the item (the authoritative disposition), or None."""
        for status in ("open", "graduated", "blocked", "parked", "done"):
            d = self.root / ".aw/records/backlog" / status
            if d.is_dir():
                for f in d.glob("*.md"):
                    if f"-{id6}-" in f.name:
                        return status
        return None

    def commit_all(self) -> None:
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.email=t@t",
                "-c",
                "user.name=t",
                "commit",
                "-qm",
                "fixture",
            ],
            cwd=self.root,
            check=True,
        )


class _RepoCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = _Repo(Path(self._tmp.name))


# ======================================================================================
# E-01: the runner can SEE the link
# ======================================================================================


class ReadsTheFromBacklogLink(_RepoCase):
    def test_both_drivers_read_the_link_into_the_plan_record(self):
        """A plan carrying `- From-Backlog: <id6>` records that id6; one without records nothing."""
        linked = self.repo.add_plan("aaaaaa", from_backlog="bbbbbb")
        bare = self.repo.add_plan("cccccc", order=2)
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                self.assertEqual(
                    mod.parse_plan_file(linked, self.repo.root).from_backlog,
                    "bbbbbb",
                    f"{name} must read the From-Backlog link",
                )
                self.assertIsNone(
                    mod.parse_plan_file(bare, self.repo.root).from_backlog,
                    f"{name} must record nothing when the field is absent",
                )

    def test_the_link_is_frozen_on_the_queue_entry(self):
        """The manifest and the frozen queue entry both carry it, in both drivers.

        THE SOURCE HALF IS REPLACED BY A REAL RUN (audit 2026-09-19). This searched
        `inspect.getsource(initialize_run)` for the literal `"from_backlog"`, and that search was
        MEASURABLY VACUOUS at the time of the audit: both hosts' `initialize_run` bodies delegate to
        `runner_shared.initialize_run_core` and mention `from_backlog` ONLY in their DOCSTRINGS
        ("Freezes queue items with 'from_backlog' ..."), so the assertion was satisfied by prose while
        the freezing happens in another module entirely. Verified by tokenizing the function and
        stripping strings and comments: the literal does not appear in the CODE of either host.

        WHAT REPLACES IT: `initialize_run` is actually RUN on a fixture repo with `--prepare-only`, and
        the frozen `state.json` must carry the id6 on the queue entry. That is the property the search
        was standing in for, and the only form that could have caught the vacuity.
        """
        self.repo.add_plan("aaaaaa", from_backlog="bbbbbb")
        self.repo.add_plan("cccccc", order=2)
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                manifest = mod.build_dynamic_manifest(
                    self.repo.root, mod.discover_plans(self.repo.root)
                )
                self.assertEqual(manifest["plans"]["aaaaaa"]["from_backlog"], "bbbbbb")
                self.assertIsNone(manifest["plans"]["cccccc"]["from_backlog"])

    def test_the_link_is_frozen_into_run_state_by_a_REAL_run(self):
        """The freeze, observed in `state.json` after driving the real `initialize_run`.

        BOTH DIRECTIONS IN ONE MEASUREMENT: the linked plan's queue entry carries the id6 and the
        unlinked one carries None. Only the pair is meaningful -- a host that froze a constant would
        satisfy either half alone.
        """
        self.repo.add_plan("aaaaaa", from_backlog="bbbbbb")
        self.repo.add_plan("cccccc", order=2)
        self.repo.commit_all()
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                args = mod.build_parser().parse_args(
                    ["start", "all", "--repo", str(self.repo.root)]
                )
                args.prepare_only = True
                # MEASURED (audit 2026-09-19): `new_run_id()` is derived from the clock to
                # whole-second resolution, so driving BOTH hosts against one fixture repo inside the
                # same second made the second call raise `DriverError: Run already exists`. Naming the
                # run per host is the fixture's job, not a product defect.
                args.run_id = f"run-frozen-link-{name}"
                sink = io.StringIO()
                with (
                    contextlib.redirect_stdout(sink),
                    contextlib.redirect_stderr(sink),
                ):
                    run_dir = mod.initialize_run(args)
                frozen = {
                    entry["id6"]: entry.get("from_backlog", "<MISSING KEY>")
                    for entry in json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )["queue"]
                }
                self.assertEqual(
                    frozen.get("aaaaaa"),
                    "bbbbbb",
                    f"{name} must FREEZE the From-Backlog link onto the queue entry; without it the "
                    "close can never fire, because `process_backlog_close` reads the id6 from the "
                    f"item and returns immediately when it is absent. Frozen queue: {frozen}",
                )
                self.assertIsNone(
                    frozen.get("cccccc"),
                    f"{name} must freeze None for an UNLINKED plan, not a stale or shared value; "
                    f"frozen queue: {frozen}",
                )

    def test_absent_and_placeholder_values_mean_no_linked_item(self):
        for raw in ("-", "none", "unresolved", ""):
            with self.subTest(value=raw):
                text = _plan_text("aaaaaa").replace(
                    "- Id: aaaaaa", f"- Id: aaaaaa\n- From-Backlog: {raw}"
                )
                self.assertIsNone(oc_runipd._read_from_backlog(text))

    def test_no_new_regex_the_field_name_comes_from_the_schema(self):
        """The field NAME must be the schema's constant, not a private pattern (E-01).

        REPLACES `assertIn("META_FROM_BACKLOG", src)` and a regex-over-source scan (audit 2026-09-19)
        with the constant SUBSTITUTION the brief prescribes for this shape: the schema constant is
        patched to a sentinel field name, and the reader must then read THAT field and stop reading the
        real one. A reader carrying its own private `From-Backlog` pattern would keep finding the real
        field and ignore the sentinel, so both halves of the old pin are covered by one measurement --
        and unlike the regex scan this one catches a private pattern however it is spelled (an f-string,
        a `str.startswith`, a split on the literal), not only as `re.compile(...)`.
        """
        self.assertEqual(
            ipd_schema.META_FROM_BACKLOG,
            "From-Backlog",
            "the shipped field name is part of the artifact contract; changing it is a migration, "
            "not a rename",
        )
        sentinel_field = "Sentinel-Backlog-Link"
        text = _plan_text("aaaaaa", from_backlog="bbbbbb")
        renamed = text.replace("- From-Backlog:", f"- {sentinel_field}:")
        self.assertIn(f"- {sentinel_field}: bbbbbb", renamed, "fixture sanity")
        with mock.patch.object(ipd_schema, "META_FROM_BACKLOG", sentinel_field):
            self.assertEqual(
                oc_runipd._read_from_backlog(renamed),
                "bbbbbb",
                "the reader must resolve the field NAME through `ipd_schema.META_FROM_BACKLOG`. With "
                f"the constant repointed at {sentinel_field!r} it must read that field; failing here "
                "means the reader carries its own hardcoded field name and cannot be kept in step "
                "with `aw check`",
            )
            self.assertIsNone(
                oc_runipd._read_from_backlog(text),
                "and with the constant repointed the reader must STOP recognizing the real field. "
                "Still reading it means a SECOND, private definition of the field name exists beside "
                "the schema's -- the divergence E-01 forbids",
            )


# ======================================================================================
# E-02 / E-03: the closing rules
# ======================================================================================


class ClosingRules(_RepoCase):
    def test_single_ipd_carrier_closes_when_its_plan_executes(self):
        self.repo.add_item("bbbbbb")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        verdict = oc_runipd.evaluate_backlog_close(
            self.repo.root, "bbbbbb", [self.repo.rel(plan)]
        )
        self.assertTrue(verdict.close, verdict.reason)
        self.assertEqual(verdict.rule, oc_runipd.CARRIER_KIND_IPD)
        self.assertEqual(verdict.evidence, self.repo.rel(plan))

    def test_two_carrier_item_does_not_close_when_only_one_executed(self):
        """The measured normal case: `dh0uno` had TWO carriers, so 'my plan executed' is wrong."""
        self.repo.add_item("bbbbbb")
        done = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        pending = self.repo.add_plan(
            "cccccc", bucket="pending", order=2, from_backlog="bbbbbb"
        )
        verdict = oc_runipd.evaluate_backlog_close(
            self.repo.root, "bbbbbb", [self.repo.rel(done)]
        )
        self.assertFalse(verdict.close)
        self.assertIn("not executed", verdict.reason)
        self.assertIn(self.repo.rel(pending), verdict.reason)

    def test_two_carrier_item_closes_when_both_executed(self):
        """Left alone: it is the POSITIVE twin of the two-carrier refusal above and its setup differs
        (two executed plans, both earned), so merging the pair would lose the contrast that makes
        either meaningful."""
        self.repo.add_item("bbbbbb")
        one = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        two = self.repo.add_plan(
            "cccccc", bucket="executed", order=2, from_backlog="bbbbbb"
        )
        verdict = oc_runipd.evaluate_backlog_close(
            self.repo.root, "bbbbbb", [self.repo.rel(one), self.repo.rel(two)]
        )
        self.assertTrue(verdict.close, verdict.reason)

    def test_spec_only_item_closes_on_existence_even_while_unapproved(self):
        """E-03 / OQ-01: no IPD carrier means the ARTIFACT is the deliverable. Status is not read."""
        self.repo.add_item("bbbbbb")
        spec = self.repo.add_spec("dddddd", from_backlog="bbbbbb", status="draft")
        verdict = oc_runipd.evaluate_backlog_close(
            self.repo.root, "bbbbbb", [self.repo.rel(spec)]
        )
        self.assertTrue(verdict.close, verdict.reason)
        self.assertEqual(verdict.rule, oc_runipd.CARRIER_KIND_OTHER)
        self.assertEqual(verdict.evidence, self.repo.rel(spec))
        self.assertIn("approval is not required", verdict.reason)

    def test_spec_status_is_never_consulted(self):
        """Every spec status must produce the SAME verdict: EXISTENCE is the whole test.

        THE SOURCE SEARCH BESIDE THIS IS DELETED (audit 2026-09-19). It ran `_code_only(...)` over
        `evaluate_backlog_close` and asserted the token `spec_status` was absent -- a variable name the
        function has no reason to use even if it DID consult status (it would read the parsed field, or
        call into `specs`), so the search could pass over exactly the code it was meant to forbid.

        WHAT MAKES THE LOOP SUFFICIENT WITHOUT IT, and it is stronger than the old `assertTrue` per
        row: the verdicts are collected and required to be IDENTICAL as whole tuples, not merely all
        truthy. A rule that consulted status would have to differ somewhere in `close`, `rule`,
        `evidence` or `reason`, and comparing the full tuple is what catches a difference that is not a
        flipped boolean (a status-dependent reason string, say). Every status in the spec vocabulary's
        review arc is covered, including the terminal-ish ones, because "unapproved still satisfies
        'create a spec'" is the maintainer's OQ-01 ruling and the permissive direction is the one worth
        pinning.
        """
        verdicts: dict[str, tuple] = {}
        for status in ("draft", "to-review", "reviewed", "approved", "implemented"):
            with self.subTest(spec_status=status), tempfile.TemporaryDirectory() as tmp:
                repo = _Repo(Path(tmp))
                repo.add_item("bbbbbb")
                spec = repo.add_spec("dddddd", from_backlog="bbbbbb", status=status)
                verdict = oc_runipd.evaluate_backlog_close(
                    repo.root, "bbbbbb", [repo.rel(spec)]
                )
                self.assertTrue(verdict.close, f"{status}: {verdict.reason}")
                verdicts[status] = (verdict.close, verdict.rule, verdict.evidence)
        self.assertEqual(
            len(set(verdicts.values())),
            1,
            "EVERY spec status must reach a BYTE-IDENTICAL verdict, because existence is the whole "
            "test (OQ-01). Comparing full verdict tuples rather than only `close` is what catches a "
            "rule that consults status in some subtler way than flipping the boolean -- a "
            f"status-dependent reason or evidence, say. Observed: {verdicts}",
        )

    def test_mixed_spec_plus_ipd_does_not_close_until_the_ipd_executes(self):
        """The IPD rule DOMINATES: an item whose output includes an IPD promised code."""
        self.repo.add_item("bbbbbb")
        spec = self.repo.add_spec("dddddd", from_backlog="bbbbbb")
        plan = self.repo.add_plan("aaaaaa", bucket="pending", from_backlog="bbbbbb")
        verdict = oc_runipd.evaluate_backlog_close(
            self.repo.root, "bbbbbb", [self.repo.rel(spec), self.repo.rel(plan)]
        )
        self.assertFalse(
            verdict.close,
            "a mixed spec+IPD item must NOT close while the IPD is unexecuted",
        )
        self.assertIn("not executed", verdict.reason)

    def test_item_with_no_carriers_is_not_closed(self):
        self.repo.add_item("bbbbbb")
        verdict = oc_runipd.evaluate_backlog_close(self.repo.root, "bbbbbb", [])
        self.assertFalse(verdict.close)
        self.assertIn("no plan or spec carries", verdict.reason)

    def test_an_already_done_item_is_left_alone(self):
        self.repo.add_item("bbbbbb", status="done")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        verdict = oc_runipd.evaluate_backlog_close(
            self.repo.root, "bbbbbb", [self.repo.rel(plan)]
        )
        self.assertFalse(verdict.close)
        self.assertIn("already done", verdict.reason)

    def test_the_shared_lookup_is_reused_not_reimplemented(self):
        """E-02: `check_engine.find_from_backlog_artifacts` is THE lookup; no second scan.

        REPLACES a source search plus a `def find_from_backlog` count (audit 2026-09-19) with a SPY that
        must actually be CALLED. That distinction is the whole point of this pin: the defect it guards
        against is a SECOND carrier scan, and a second scan would sit BESIDE the shared call, so the
        text would still contain the name and the count would still be zero. Here the shared lookup is
        patched to a spy returning NO carriers over a tree that really holds an executed carrier; the
        verdict must be the no-carrier refusal, which is only possible if the shared lookup is the sole
        source of the carrier set.
        """
        self.repo.add_item("bbbbbb")
        self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        # The control: with the REAL lookup this item closes, so the row below is not vacuous.
        real_verdict = oc_runipd.evaluate_backlog_close(
            self.repo.root, "bbbbbb", [self.repo.rel(self.repo.root / "x")]
        )
        del real_verdict  # the earning gate is exercised by its own tests; only the lookup matters here
        calls: list[tuple[str, str]] = []

        def spy(repo_root, item_id6):
            calls.append((str(repo_root), item_id6))
            return []

        with mock.patch.object(check_engine, "find_from_backlog_artifacts", spy):
            verdict = oc_runipd.evaluate_backlog_close(
                self.repo.root, "bbbbbb", ["some/earned/path.ipd.md"]
            )
        self.assertEqual(
            len(calls),
            1,
            "the carrier set must come from EXACTLY ONE call to the shared lookup; "
            f"{len(calls)} calls means a second scan was added beside it. Calls: {calls}",
        )
        self.assertEqual(
            calls[0][1],
            "bbbbbb",
            f"the shared lookup must be asked about THIS item; saw {calls[0]!r}",
        )
        self.assertFalse(
            verdict.close,
            "with the shared lookup returning no carriers the verdict must be the no-carrier "
            "refusal. Closing anyway means the runner found carriers by its OWN scan, which is the "
            f"divergence E-02 forbids. Reason given: {verdict.reason!r}",
        )
        self.assertIn(
            "no plan or spec carries",
            verdict.reason,
            "and the reason must be the no-carrier one specifically, so a refusal for some other "
            f"cause cannot pass for this claim; saw {verdict.reason!r}",
        )


# ======================================================================================
# E-04: the earned-close gate, and fail-closed
# ======================================================================================


class EarnedCloseGate(_RepoCase):
    def test_a_run_that_executed_no_carrier_closes_nothing(self):
        """Closing is a state change; a run that merely OBSERVED the carriers did not earn it."""
        self.repo.add_item("bbbbbb")
        self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        verdict = oc_runipd.evaluate_backlog_close(self.repo.root, "bbbbbb", [])
        self.assertFalse(verdict.close)
        self.assertIn("not earned", verdict.reason)

    def test_the_gate_applies_to_the_non_ipd_rule_too(self):
        self.repo.add_item("bbbbbb")
        self.repo.add_spec("dddddd", from_backlog="bbbbbb")
        verdict = oc_runipd.evaluate_backlog_close(self.repo.root, "bbbbbb", [])
        self.assertFalse(verdict.close, "a spec-only close must ALSO be earned")
        self.assertIn("not earned", verdict.reason)

    def test_an_induced_lookup_failure_leaves_the_item_untouched(self):
        self.repo.add_item("bbbbbb")
        self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        original = check_engine.find_from_backlog_artifacts

        def boom(*_a, **_k):
            raise RuntimeError("induced carrier lookup failure")

        check_engine.find_from_backlog_artifacts = boom  # type: ignore[assignment]
        try:
            verdict = oc_runipd.evaluate_backlog_close(
                self.repo.root, "bbbbbb", ["whatever"]
            )
        finally:
            check_engine.find_from_backlog_artifacts = original  # type: ignore[assignment]
        self.assertFalse(verdict.close, "a lookup failure must never close an item")
        self.assertIn("carrier lookup failed", verdict.reason)
        self.assertIn("induced carrier lookup failure", verdict.reason)
        self.assertEqual(self.repo.item_status("bbbbbb"), "graduated")

    def test_an_induced_terminal_state_read_failure_fails_closed(self):
        self.repo.add_item("bbbbbb")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        # PATCH WHERE `evaluate_backlog_close` RESOLVES `plan_bucket`, which is `runner_shared` since
        # runnerlayer Order 02 (`1f7xno`) re-homed that evaluator. Patching the `oc_runipd` attribute
        # would no longer intercept, so the induced failure would never fire and this FAIL-CLOSED test
        # would pass vacuously on a verdict that closed. The host attribute re-exports this same
        # object, so what is asserted is unchanged.
        original = runner_shared.plan_bucket

        def boom(*_a, **_k):
            raise RuntimeError("induced bucket read failure")

        runner_shared.plan_bucket = boom  # type: ignore[assignment]
        try:
            verdict = oc_runipd.evaluate_backlog_close(
                self.repo.root, "bbbbbb", [self.repo.rel(plan)]
            )
        finally:
            runner_shared.plan_bucket = original  # type: ignore[assignment]
        self.assertFalse(verdict.close)
        self.assertIn("terminal-state read failed", verdict.reason)

    def test_an_induced_setter_failure_leaves_the_item_untouched_with_a_reason(self):
        """A refused setter must be RECORDED as the reason, never swallowed and never forced."""
        self.repo.add_item("bbbbbb")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        state = {
            "repo": str(self.repo.root),
            "run_id": "run-test",
            "queue": [
                {
                    "id6": "aaaaaa",
                    "position": 1,
                    "setid": "demo",
                    "from_backlog": "bbbbbb",
                    "status": "executed",
                    "attempts": [],
                    # The real earning route: the finalized plan path, which
                    # `collect_earned_paths` reads (it RECOMPUTES `earned_paths`, so
                    # pre-seeding that key would be a fixture that cannot happen).
                    "last_plan_path": str(plan),
                }
            ],
        }
        item = state["queue"][0]
        original = oc_runipd.close_backlog_item
        oc_runipd.close_backlog_item = lambda *_a, **_k: (  # type: ignore[assignment]
            1,
            "aw backlog set: refused: induced setter failure",
        )
        try:
            oc_runipd.process_backlog_close(Path(self._tmp.name) / "run", state, item)
        finally:
            oc_runipd.close_backlog_item = original  # type: ignore[assignment]
        record = item["backlog_close"]
        self.assertFalse(record["closed"])
        self.assertIn("setter refused the close", record["reason"])
        self.assertIn("induced setter failure", record["reason"])
        self.assertEqual(self.repo.item_status("bbbbbb"), "graduated")


# ======================================================================================
# The setter FORM: gated, not the ungated positional spelling
# ======================================================================================


class UsesTheGatedSetter(_RepoCase):
    def test_the_close_uses_the_status_form_which_runs_the_release_gate_predicate(self):
        """`backlog set <status> <sel>` bypasses `evaluate_blocking_close`; `--status` does not.

        Verified live in a scratch repo: a `graduated` item carrying `Blocks-Release: next` closed
        with NO evidence via the positional form (exit 0) and was REFUSED via this one. The runner
        must be gated, so the argv must carry `--status` and `--evidence`.
        """
        captured: dict = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = list(cmd)

            class _R:
                returncode = 0
                stdout = "ok"
                stderr = ""

            return _R()

        original = subprocess.run
        subprocess.run = fake_run  # type: ignore[assignment]
        try:
            oc_runipd.close_backlog_item(
                self.repo.root,
                self.repo.root / "item.md",
                "bbbbbb",
                "path/to/carrier.ipd.md",
                "a message",
            )
        finally:
            subprocess.run = original  # type: ignore[assignment]
        cmd = captured["cmd"]
        self.assertIn("backlog", cmd)
        self.assertIn("set", cmd)
        self.assertIn("--status", cmd, f"the GATED form is required; argv was {cmd!r}")
        self.assertEqual(cmd[cmd.index("--status") + 1], "done")
        self.assertIn("--evidence", cmd)
        self.assertEqual(
            cmd[cmd.index("--evidence") + 1],
            "path/to/carrier.ipd.md",
            "the evidence argument must name the real carrier path",
        )
        # The positional spelling `set done <selector>` must NOT appear: it is the ungated path.
        self.assertNotEqual(
            cmd[cmd.index("set") + 1],
            "done",
            f"`set done <selector>` is the UNGATED positional form; argv was {cmd!r}",
        )

    def test_the_item_file_is_never_edited_directly(self):
        """E-02: close via the lifecycle-owned setter, never by writing the item file.

        REPLACES four `assertNotIn` searches over `_code_only()` output (audit 2026-09-19), which said
        only that the tokens `write_text`, `atomic_write`, `unlink` and `replace(` were not typed -- a
        list that cannot be complete (`os.rename`, `shutil.move`, `Path.open("w")` all pass it) and that
        fails on an innocent `str.replace`.

        WHAT REPLACES IT: the setter subprocess is STUBBED OUT so it performs no move at all, and the
        item file's bytes are compared before and after. If the close path wrote the file itself, the
        bytes would change even though the setter did nothing. That covers every write mechanism rather
        than four spellings of one.
        """
        self.repo.add_item("bbbbbb")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        item_path = next(
            (self.repo.root / ".aw/records/backlog/graduated").glob("*bbbbbb*.md")
        )
        before = item_path.read_bytes()
        state = {
            "repo": str(self.repo.root),
            "run_id": "run-test",
            "queue": [
                {
                    "id6": "aaaaaa",
                    "position": 1,
                    "setid": "demo",
                    "from_backlog": "bbbbbb",
                    "status": "executed",
                    "attempts": [],
                    "last_plan_path": str(plan),
                }
            ],
        }
        # The setter reports SUCCESS while doing nothing. Any change to the file therefore came from
        # the close path itself, which is exactly what must never happen.
        with mock.patch.object(
            oc_runipd, "close_backlog_item", lambda *_a, **_k: (0, "ok")
        ):
            oc_runipd.process_backlog_close(
                Path(self._tmp.name) / "run", state, state["queue"][0]
            )
        self.assertTrue(
            item_path.is_file(),
            "the close path must not MOVE or DELETE the item file; the lifecycle setter owns it, and "
            "a runner-side move bypasses the release-gate close predicate entirely",
        )
        self.assertEqual(
            item_path.read_bytes(),
            before,
            "the item file must be BYTE-IDENTICAL after a close whose setter did nothing. A change "
            "here means the runner edited the item itself, which skips `evaluate_blocking_close` and "
            "can silently drop a release gate",
        )

    def test_the_commit_is_path_scoped_to_this_item_only(self):
        """A co-worker's edit to a DIFFERENT backlog item must never be swept in.

        REPLACES `assertIn("offer_commit", code)` and two banned-substring searches (audit 2026-09-19)
        with a spy on the shared commit helper: it must be CALLED, and the path list it receives must
        contain ONLY paths whose basename carries this item's id6. The `assertNotIn("-A", raw)` it
        replaces was the weakest assertion in the file -- `-A` is two characters and matches inside
        ordinary words, which is why it needed a `.replace("no push", "")` kludge to avoid a false
        positive on its own docstring.

        THE AST id6-GATE CHECK IS ALSO GONE, because this subsumes it: the AST check proved a comparison
        of that SHAPE existed, while this proves the resulting path set is actually filtered.
        """
        self.repo.add_item("bbbbbb")
        coworker = self.repo.add_item("cccccc", status="open")
        self.repo.commit_all()
        # Simulate what the setter does (MOVE the item) plus a co-worker editing a DIFFERENT item.
        done = self.repo.root / ".aw/records/backlog/done"
        mine = next(
            (self.repo.root / ".aw/records/backlog/graduated").glob("*bbbbbb*.md")
        )
        (done / mine.name).write_text(
            mine.read_text(encoding="utf-8"), encoding="utf-8"
        )
        mine.unlink()
        coworker.write_text(
            coworker.read_text(encoding="utf-8") + "\nsomeone else's edit\n",
            encoding="utf-8",
        )

        from agent_workflows import git_commit_helper

        captured: list[tuple[list[str], dict]] = []
        real = git_commit_helper.offer_commit

        def spy(repo, paths, **kwargs):
            captured.append((list(paths), kwargs))
            return real(repo, paths, **kwargs)

        with mock.patch.object(git_commit_helper, "offer_commit", spy):
            sha = oc_runipd.commit_backlog_close(self.repo.root, "bbbbbb", "msg")
        self.assertEqual(
            len(captured),
            1,
            "the commit must go through the SHARED tooled path (`git_commit_helper.offer_commit`), "
            "which snapshots the index before staging and commits only the intersection of its own "
            f"paths. It was called {len(captured)} time(s)",
        )
        paths, kwargs = captured[0]
        unrelated = [p for p in paths if "bbbbbb" not in Path(p).name]
        self.assertEqual(
            unrelated,
            [],
            "every staged path's BASENAME must carry this item's id6, so a co-worker's concurrent "
            f"edit to a different backlog item can never be swept in. Unrelated paths: {unrelated}",
        )
        self.assertEqual(
            sorted(Path(p).parent.name for p in paths),
            ["done", "graduated"],
            "BOTH SIDES of the move must be staged (the deletion and the addition). Committing half "
            f"a move leaves the tree worse than not committing at all. Paths: {paths}",
        )
        self.assertFalse(
            kwargs.get("interactive", True),
            "the runner is unattended, so the commit helper must not be asked to prompt",
        )
        self.assertIsNotNone(sha, "the move must actually be committed")
        self.assertIn(
            "someone else's edit",
            coworker.read_text(encoding="utf-8"),
            "and the co-worker's uncommitted edit must be left exactly as found",
        )


class ClosesEndToEnd(_RepoCase):
    def test_a_real_close_moves_the_item_to_done_with_evidence(self):
        """The full path through the real setter: graduated -> done, evidence cited."""
        self.repo.add_item("bbbbbb", blocks_release="next")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        self.repo.commit_all()
        run_dir = self.repo.root / "run"
        run_dir.mkdir()
        state = {
            "repo": str(self.repo.root),
            "run_id": "run-test",
            "queue": [
                {
                    "id6": "aaaaaa",
                    "position": 1,
                    "setid": "demo",
                    "from_backlog": "bbbbbb",
                    "status": "executed",
                    "attempts": [],
                    "last_plan_path": str(plan),
                }
            ],
        }
        item = state["queue"][0]
        oc_runipd.process_backlog_close(run_dir, state, item)
        record = item["backlog_close"]
        self.assertTrue(record["closed"], record["reason"])
        self.assertEqual(
            self.repo.item_status("bbbbbb"),
            "done",
            "the item must have MOVED to the done/ directory",
        )
        moved = next((self.repo.root / ".aw/records/backlog/done").glob("*bbbbbb*.md"))
        text = moved.read_text(encoding="utf-8")
        self.assertIn("- Status: done", text)
        self.assertIn(
            "- Blocks-Release: next",
            text,
            "the gate field must be preserved, not silently dropped",
        )
        self.assertEqual(record["evidence"], self.repo.rel(plan))

    def test_the_move_is_committed_path_scoped_and_leaves_the_tree_clean(self):
        """The setter MOVES the file and does not commit; an uncommitted move contaminates the
        next turn's begin-dirty (z2isfg) and dirty-overlap (driverfin-03) gates.

        This pins THREE real bugs found by running it, each of which silently produced no commit:
          1. naming a nonexistent backlog root made `git status` exit nonzero (pathspec did not
             match), which `run_checked` raises on and this path suppresses;
          2. default `--porcelain` collapsed the untracked side to the DIRECTORY (`?? .../done/`),
             whose basename carries no id6, so the new file never matched the filter;
          3. `run_checked` strips its output, so `" D <path>"` arrived as `"D <path>"` and a fixed
             `line[3:]` slice ate the path's leading `.`, yielding a bad `git add` pathspec.
        """
        self.repo.add_item("bbbbbb")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        self.repo.commit_all()
        run_dir = self.repo.root / "run"
        run_dir.mkdir()
        state = {
            "repo": str(self.repo.root),
            "run_id": "run-test",
            "queue": [
                {
                    "id6": "aaaaaa",
                    "position": 1,
                    "setid": "demo",
                    "from_backlog": "bbbbbb",
                    "status": "executed",
                    "attempts": [],
                    "last_plan_path": str(plan),
                }
            ],
        }
        item = state["queue"][0]
        oc_runipd.process_backlog_close(run_dir, state, item)
        record = item["backlog_close"]
        self.assertTrue(record["closed"], record["reason"])
        self.assertIsNotNone(
            record["commit"],
            "the move must be committed, else the next turn inherits a dirty tree",
        )
        porcelain = subprocess.run(
            ["git", "status", "--porcelain", "-uall", "--", ".aw/records/backlog"],
            cwd=self.repo.root,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(
            porcelain, "", f"the backlog tree must be left clean; saw:\n{porcelain}"
        )
        # The commit must contain BOTH sides of the move and NOTHING else.
        files = subprocess.run(
            ["git", "show", "--name-only", "--format=", "HEAD"],
            cwd=self.repo.root,
            capture_output=True,
            text=True,
        ).stdout.split()
        self.assertEqual(len(files), 2, files)
        for path in files:
            self.assertIn(
                "bbbbbb", Path(path).name, f"unrelated path committed: {path}"
            )

    def test_a_coworkers_other_backlog_item_is_never_swept_in(self):
        """The id6 filter is the blast-radius control; prove it with a real concurrent edit."""
        self.repo.add_item("bbbbbb")
        coworker = self.repo.add_item("cccccc", status="open")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        self.repo.commit_all()
        # A co-worker's uncommitted edit to a DIFFERENT backlog item, present during our close.
        coworker.write_text(
            coworker.read_text(encoding="utf-8") + "\nsomeone else's edit\n",
            encoding="utf-8",
        )
        run_dir = self.repo.root / "run"
        run_dir.mkdir()
        state = {
            "repo": str(self.repo.root),
            "run_id": "run-test",
            "queue": [
                {
                    "id6": "aaaaaa",
                    "position": 1,
                    "setid": "demo",
                    "from_backlog": "bbbbbb",
                    "status": "executed",
                    "attempts": [],
                    "last_plan_path": str(plan),
                }
            ],
        }
        oc_runipd.process_backlog_close(run_dir, state, state["queue"][0])
        files = subprocess.run(
            ["git", "show", "--name-only", "--format=", "HEAD"],
            cwd=self.repo.root,
            capture_output=True,
            text=True,
        ).stdout.split()
        for path in files:
            self.assertNotIn(
                "cccccc",
                path,
                "a co-worker's edit to another backlog item must never be committed",
            )
        self.assertIn(
            "someone else's edit",
            coworker.read_text(encoding="utf-8"),
            "the co-worker's edit must be left exactly as found",
        )

    def test_the_close_is_recorded_in_the_run_ledger(self):
        self.repo.add_item("bbbbbb")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        self.repo.commit_all()
        run_dir = self.repo.root / "run"
        run_dir.mkdir()
        state = {
            "repo": str(self.repo.root),
            "run_id": "run-test",
            "queue": [
                {
                    "id6": "aaaaaa",
                    "position": 1,
                    "setid": "demo",
                    "from_backlog": "bbbbbb",
                    "status": "executed",
                    "attempts": [],
                    "last_plan_path": str(plan),
                }
            ],
        }
        oc_runipd.process_backlog_close(run_dir, state, state["queue"][0])
        events = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        closed = [e for e in events if e.get("event") == "backlog-item-closed"]
        self.assertEqual(len(closed), 1, events)
        self.assertEqual(closed[0]["backlog_item"], "bbbbbb")


# ======================================================================================
# E-06 / E-07: the report and the pointer
# ======================================================================================


def _state_with_open_item(
    reason: str = "IPD carrier(s) not executed: x.ipd.md",
) -> dict:
    return {
        "repo": "/tmp/nowhere",
        "run_id": "run-20260830T000000Z-1234",
        "queue": [
            {
                "id6": "aaaaaa",
                "position": 1,
                "setid": "demo",
                "status": "executed",
                "from_backlog": "bbbbbb",
                "backlog_close": {
                    "item": "bbbbbb",
                    "closed": False,
                    "reason": reason,
                },
            }
        ],
    }


class UnclosedReport(unittest.TestCase):
    def setUp(self) -> None:
        oc_runipd._SIGNAL_REPORT_DONE.clear()
        oc_runipd._SIGNAL_REPORT_STATE.clear()
        self.addCleanup(oc_runipd._SIGNAL_REPORT_DONE.clear)
        self.addCleanup(oc_runipd._SIGNAL_REPORT_STATE.clear)

    def test_each_open_item_is_listed_with_its_reason(self):
        state = _state_with_open_item()
        pairs = oc_runipd.unclosed_backlog_items(state)
        self.assertEqual(pairs, [("bbbbbb", "IPD carrier(s) not executed: x.ipd.md")])
        report = oc_runipd.render_unclosed_report(state)
        self.assertIn("bbbbbb", report)
        self.assertIn("not executed", report)

    def test_a_run_with_nothing_outstanding_prints_no_section(self):
        state = _state_with_open_item()
        state["queue"][0]["backlog_close"]["closed"] = True
        self.assertEqual(oc_runipd.unclosed_backlog_items(state), [])
        self.assertEqual(oc_runipd.render_unclosed_report(state), "")

    def test_an_item_whose_plan_never_reached_the_close_is_still_reported(self):
        """A linked item must never be silently absent; the reason says the plan's fate."""
        state = _state_with_open_item()
        del state["queue"][0]["backlog_close"]
        state["queue"][0]["status"] = "partial"
        pairs = oc_runipd.unclosed_backlog_items(state)
        self.assertEqual(len(pairs), 1)
        self.assertIn("partial", pairs[0][1])

    def test_a_plan_with_no_linked_item_contributes_nothing(self):
        """Left alone: it MUTATES the shared fixture state (removing the link) rather than varying an
        input, which is structurally different from its siblings."""
        state = _state_with_open_item()
        state["queue"][0].pop("from_backlog")
        self.assertEqual(oc_runipd.unclosed_backlog_items(state), [])

    def test_the_ledger_record_is_written_before_the_print(self):
        """Ordering is the whole point: a truncated print still leaves the answer on disk.

        REPLACES an `ast.walk` over `emit_shutdown_report` (audit 2026-09-19). That walk was NOT a text
        grep, so it was not the worst shape in this file, but it was unsound for an ORDERING claim in a
        way worth recording: `ast.walk` yields nodes in breadth-first tree order, which is NOT execution
        order, so a `record_...` call nested inside a later branch would still be reported "first". It
        also could not see whether either call HAPPENS.

        WHAT REPLACES IT: the run is driven for real and the FILESYSTEM is observed from inside the
        print. At print time `events.jsonl` must already exist; at ledger time it must not. That is the
        property the ordering exists for -- a print that is truncated, redirected, or lost to an
        uncatchable kill still leaves the answer on disk -- and it is observed rather than inferred.
        """
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            ledger = run_dir / "events.jsonl"
            observed: list[tuple[str, bool]] = []
            oc_runipd.register_signal_report(run_dir, _state_with_open_item())
            real_record = runner_shared.record_unclosed_backlog_items

            def watched_record(*args, **kwargs):
                observed.append(("ledger", ledger.exists()))
                return real_record(*args, **kwargs)

            def watched_print(*args, **kwargs):
                observed.append(("print", ledger.exists()))

            # PATCHED ON `runner_shared`, WHERE `emit_shutdown_report` RESOLVES BOTH NAMES since
            # runnerlayer Order 02 (`1f7xno`) re-homed that reporter out of the host driver. Patching
            # the `oc_runipd` attribute would intercept NOTHING now, and this test would report an
            # EMPTY observation list rather than a wrong order, which is how it failed when the move
            # landed. The host attribute is a re-export of this same object, so the assertion below is
            # unchanged in meaning.
            with (
                mock.patch.object(
                    runner_shared, "record_unclosed_backlog_items", watched_record
                ),
                mock.patch.object(runner_shared, "print", watched_print, create=True),
            ):
                oc_runipd.emit_shutdown_report()
        self.assertEqual(
            [label for label, _existed in observed][:2],
            ["ledger", "print"],
            "the ledger append must be ATTEMPTED before anything is printed; a print that is "
            f"truncated or lost must still leave the answer on disk. Observed: {observed}",
        )
        self.assertEqual(
            observed[0],
            ("ledger", False),
            "at ledger time the file must NOT yet exist, which is what shows this observation is "
            f"really ordered rather than reading a file an earlier test left behind. Saw {observed}",
        )
        self.assertTrue(
            observed[1][1],
            "at PRINT time the ledger must already be on disk. This is the assertion the AST walk "
            f"could not make, and it is the whole point of the ordering. Saw {observed}",
        )

    def test_the_ledger_record_survives_when_the_print_is_discarded(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            state = _state_with_open_item()
            oc_runipd.record_unclosed_backlog_items(run_dir, state)
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            left = [e for e in events if e.get("event") == "backlog-items-left-open"]
            self.assertEqual(len(left), 1, events)
            self.assertEqual(left[0]["items"][0]["item"], "bbbbbb")
            self.assertIn("not executed", left[0]["items"][0]["reason"])

    def test_the_report_is_idempotent_under_a_repeated_signal(self):
        """Left alone: a BEFORE/AFTER idempotence pair, which the house pattern excludes from
        tabulation because the property IS the repetition rather than any row's data."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            state = _state_with_open_item()
            oc_runipd.register_signal_report(run_dir, state)
            oc_runipd.emit_shutdown_report()
            first = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            oc_runipd.emit_shutdown_report()
            oc_runipd.emit_shutdown_report()
            self.assertEqual(
                (run_dir / "events.jsonl").read_text(encoding="utf-8"),
                first,
                "a repeated signal must not double-report",
            )

    def test_the_pointer_names_the_real_run_id_and_the_real_verb(self):
        state = _state_with_open_item()
        line = oc_runipd.render_runs_pointer(state)
        self.assertEqual(line, "Run `aw runs run-20260830T000000Z-1234` for more info.")
        self.assertNotIn("aw oc runs", line)

    def test_the_pointer_names_a_verb_the_CLI_really_has(self):
        """`aw oc runs` is not a command; `aw runs` is.

        REPLACES `assertNotIn("aw oc runs ", <whole driver source>)` (audit 2026-09-19), which scanned
        two 7000-line files for a string and so was satisfied by the absence of a phrase rather than by
        the presence of a working verb. Note it could not even fail for its stated reason: a driver that
        emitted `aw oc runs` with different spacing, or built it from parts, passed.

        WHAT REPLACES IT: the rendered pointer is PARSED, and the verb it names is required to be one
        the packaged CLI actually dispatches. That is the property -- an operator who types what the
        pointer says must get a working command -- and it fails if either the pointer or the CLI moves.
        """
        line = oc_runipd.render_runs_pointer(_state_with_open_item())
        match = re.search(r"`aw ([a-z-]+) ", line)
        self.assertIsNotNone(
            match,
            f"the pointer must name a backticked `aw <verb> ...` command; got {line!r}",
        )
        assert match is not None
        verb = match.group(1)
        from agent_workflows import cli as _cli

        # `_build_parser`, not `build_parser`: the packaged CLI exposes only the underscored name
        # (measured 2026-09-19). Reaching for a private helper is the honest cost of asserting against
        # the REAL dispatch table rather than a list of verbs restated here, which would rot silently.
        parser = _cli._build_parser()
        verbs: set[str] = set()
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                verbs.update(action.choices)
        self.assertIn(
            verb,
            verbs,
            f"the pointer tells the operator to run `aw {verb} <run-id>`, but the packaged CLI has no "
            f"such verb. An operator following it would get an error. Known verbs: {sorted(verbs)}",
        )
        self.assertNotIn(
            "oc",
            verb,
            f"`aw oc runs` is not a command and must never be emitted; the pointer named {verb!r}",
        )

    def test_json_output_suppresses_the_pointer_and_stays_PARSEABLE(self):
        """E-07, DRIVEN through `main` on a real prepared run (audit 2026-09-19).

        REPLACES an `ast.walk` looking for an `If` whose test mentions json and whose body contains
        `json.dumps`, then asserting `render_runs_pointer` was absent from that body. That search was
        CONDITIONALLY VACUOUS by construction: every one of its three `continue`s silently skips the
        check, so a refactor that moved the json branch, renamed the flag, or dropped the literal
        `json.dumps` would make the test assert NOTHING while still passing green.

        WHAT REPLACES IT: `main` is invoked for real with and without `--json`, and the output is
        required to be JSON-PARSEABLE in the `--json` case. That is the property the pin protects (a
        trailing human sentence makes machine output unparseable), and it cannot pass vacuously: a
        pointer leaking into the json branch makes `json.loads` raise. The non-json case is asserted in
        the SAME table so the suppression cannot be satisfied by never printing the pointer at all.
        """
        wrong: list[str] = []
        # (case, extra argv, must the pointer appear, must the output parse as JSON, why this row exists)
        modes = (
            (
                "human `status`",
                [],
                True,
                False,
                (
                    "THE POSITIVE ROW, without which suppression is satisfiable by deleting the "
                    "pointer entirely. A human operator reading a run summary needs the "
                    "`aw runs <id>` hint, which is the whole reason E-07 added it"
                ),
            ),
            (
                "`status --json`",
                ["--json"],
                False,
                True,
                (
                    "THE MACHINE ROW: a trailing human sentence after a JSON document makes the "
                    "output unparseable for every consumer. Asserting it PARSES rather than that a "
                    "symbol is absent is what makes this row impossible to satisfy vacuously"
                ),
            ),
        )
        for name, mod in _DRIVERS:
            with tempfile.TemporaryDirectory() as tmp:
                repo = _Repo(Path(tmp))
                repo.add_plan("aaa111", from_backlog="bbbbbb")
                repo.add_item("bbbbbb")
                repo.commit_all()
                sink = io.StringIO()
                with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                    mod.main(
                        [
                            "start",
                            "all",
                            "--repo",
                            str(repo.root),
                            "--prepare-only",
                            "--run-id",
                            f"run-pointer-{name}",
                        ]
                    )
                for case, extra, wants_pointer, must_parse, why in modes:
                    buffer = io.StringIO()
                    with (
                        contextlib.redirect_stdout(buffer),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        mod.main(
                            [
                                "status",
                                "--repo",
                                str(repo.root),
                                f"run-pointer-{name}",
                                *extra,
                            ]
                        )
                    output = buffer.getvalue()
                    problems: list[str] = []
                    has_pointer = "aw runs" in output
                    if has_pointer is not wants_pointer:
                        problems.append(
                            f"expected the `aw runs` pointer present={wants_pointer}, got "
                            f"{has_pointer}"
                        )
                    if must_parse:
                        try:
                            json.loads(output)
                        except json.JSONDecodeError as exc:
                            problems.append(
                                f"the output must be valid JSON and is not: {exc}. Tail of output: "
                                f"{output[-160:]!r}"
                            )
                    if problems:
                        wrong.append(
                            f"  {name} {case}:\n"
                            + "".join(f"    - {p}\n" for p in problems)
                            + f"    this row exists because: {why}"
                        )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(_DRIVERS) * len(modes)} host/output-mode combinations render the "
            "run pointer wrongly. BOTH ROWS SHARE THIS TABLE because the two failure directions are "
            "opposite: suppressing the pointer everywhere satisfies the machine row while removing the "
            "operator's hint, and emitting it everywhere satisfies the human row while breaking every "
            "JSON consumer. FIX: print the pointer only on the human path.\n"
            + "\n".join(wrong),
        )


# ======================================================================================
# E-05: the runner's own signal handlers (real subprocesses)
# ======================================================================================


_SIGNAL_SCRIPT = """
import json, os, signal, sys, time
from pathlib import Path, PurePath
sys.path.insert(0, {repo!r})
from agent_workflows import {driver} as d
from agent_workflows.render_stream import install_exit_signal_handler

run_dir = Path({run_dir!r})
state = {{
    "repo": {run_dir!r},
    "run_id": "run-signal-test",
    "queue": [
        {{
            "id6": "aaaaaa", "position": 1, "setid": "demo", "status": "executed",
            "from_backlog": "bbbbbb",
            "backlog_close": {{"item": "bbbbbb", "closed": False,
                              "reason": "IPD carrier(s) not executed: x.ipd.md"}},
        }}
    ],
}}
d.register_signal_report(run_dir, state)
# EXACTLY the two lines the real `main` uses, in the real order, so this exercises the shipped funnel
# rather than a mock of it:
#   1. `install_exit_signal_handler()` -- executed plan `bds6nd`'s SIGTERM handler, which lives in
#      `render_stream` (a module the `signal.signal` guards do NOT cover) and raises
#      `KeyboardInterrupt("Terminated by SIGTERM")`.
#   2. the `except KeyboardInterrupt` funnel, which CPython already routes SIGINT into.
# Both signals therefore converge on ONE report path, with the conventional 130/143 exit preserved.
#
# READY is announced INSIDE the try, so a signal that arrives the instant the parent sees it is still
# caught by the funnel under test. Announcing it first left a window in which the interrupt landed on
# the `print` itself and died as a bare KeyboardInterrupt (observed as a real flake at -2 under the
# loaded parallel suite), which tested the harness rather than the code.
install_exit_signal_handler()
try:
    print("READY", flush=True)
    while True:
        time.sleep(0.05)
except KeyboardInterrupt as exc:
    is_sigterm = "SIGTERM" in str(exc)
    d.emit_shutdown_report(to_stderr=True)
    print(
        ("Terminated by SIGTERM" if is_sigterm else "Interrupted")
        + "; durable run state was preserved.",
        file=sys.stderr,
    )
    sys.exit(143 if is_sigterm else 130)
"""


class ShutdownReportOnInterrupt(unittest.TestCase):
    """E-05/E-06: a real SIGINT and a real SIGTERM each produce the report, at 130 and 143.

    SCOPE NOTE (zhr6mc, and the reason the original DEFERRED Q1 is now CLOSED). E-05 as authored asked
    this plan to call `signal.signal` for SIGINT and SIGTERM inside the two runner modules. It still
    may not: four executed plans guard that call in those files, reserving it for `runstop` Phase 5
    (`71vjbn`), whose semantics (SIGINT escalates 1->3->4, SIGTERM requests level 3) would collide.

    What changed is the FACTS, not the ownership. Executed plan `bds6nd` landed
    `render_stream.install_exit_signal_handler`, which registers the SIGTERM handler OUTSIDE the two
    guarded modules and raises `KeyboardInterrupt("Terminated by SIGTERM")`. `main` already calls it.
    So SIGTERM now reaches the same `except KeyboardInterrupt` funnel SIGINT always did, and E-05's
    REQUIRED OUTCOME (report on both signals, conventional exit status) is reachable without this plan
    registering anything. `test_the_registration_is_left_to_its_owner` still holds the line on WHERE
    the registration may live.
    """

    def _run_and_signal(self, driver: str, sig: int) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "child.py"
            run_dir = Path(tmp) / "run"
            run_dir.mkdir()
            script.write_text(
                _SIGNAL_SCRIPT.format(
                    repo=str(REPO_ROOT), driver=driver, run_dir=str(run_dir)
                ),
                encoding="utf-8",
            )
            proc = subprocess.Popen(
                [sys.executable, str(script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            assert proc.stdout is not None
            self.assertEqual(proc.stdout.readline().strip(), "READY")
            proc.send_signal(sig)
            out, err = proc.communicate(timeout=30)
            events_path = run_dir / "events.jsonl"
            ledger = (
                events_path.read_text(encoding="utf-8") if events_path.exists() else ""
            )
            return proc.returncode, out + err + "\n--LEDGER--\n" + ledger

    def _assert_reported(self, rc: int, expect: int, output: str) -> None:
        self.assertEqual(rc, expect, output)
        self.assertIn("bbbbbb", output)
        self.assertIn("not executed", output)
        self.assertIn("Run `aw runs run-signal-test` for more info.", output)
        self.assertIn(
            "backlog-items-left-open",
            output,
            "the ledger record must exist even when only the print is observed",
        )

    def test_sigint_produces_the_report_and_exits_130(self):
        for driver in ("oc_runipd", "agy_runipd"):
            with self.subTest(driver=driver):
                rc, output = self._run_and_signal(driver, signal.SIGINT)
                self._assert_reported(rc, 130, output)

    def test_sigterm_produces_the_report_and_exits_143(self):
        """E-05's SIGTERM half, reachable now that `bds6nd`'s handler funnels it here.

        Pre-`bds6nd` this was impossible: SIGTERM had NO handler, so Python's default terminated the
        process immediately, no `except` ran, and nothing was printed.
        """
        for driver in ("oc_runipd", "agy_runipd"):
            with self.subTest(driver=driver):
                rc, output = self._run_and_signal(driver, signal.SIGTERM)
                self._assert_reported(rc, 143, output)

    def test_the_sigterm_funnel_is_wired_in_both_drivers_main(self):
        """`main` must actually INSTALL the handler, or the SIGTERM half silently regresses.

        REPLACES `assertIn("install_exit_signal_handler()", src)` plus `assertIn("143", src)` (audit
        2026-09-19). The second was the weakest assertion in this file: `"143"` is three digits and
        matches any line number, byte count, or id that happens to contain them, so it could not fail
        for its stated reason. Both are also satisfied by a comment.

        WHAT REPLACES THEM: `main` is CALLED (on a short out-of-band command that needs no run) and the
        process's real SIGTERM DISPOSITION is read back from the `signal` module. A `main` that stopped
        installing the handler leaves the disposition untouched, whatever its source says. The exit
        STATUS half is already proved end-to-end by `test_sigterm_produces_the_report_and_exits_143`
        above, which sends a real SIGTERM to a real subprocess and asserts 143, so the `"143"` search
        was redundant as well as vacuous.
        """
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
                self.addCleanup(signal.signal, signal.SIGTERM, signal.SIG_DFL)
                before = signal.getsignal(signal.SIGTERM)
                sink = io.StringIO()
                with (
                    tempfile.TemporaryDirectory() as tmp,
                    contextlib.redirect_stdout(sink),
                    contextlib.redirect_stderr(sink),
                ):
                    # An out-of-band `status` for a run that does not exist: it installs the handler
                    # and then exits, so nothing durable is created.
                    mod.main(["status", "--repo", tmp, "run-nope"])
                after = signal.getsignal(signal.SIGTERM)
                self.assertIsNot(
                    after,
                    before,
                    f"{name}.main must INSTALL the SIGTERM handler; the disposition is unchanged from "
                    f"{before!r}, so a SIGTERM would kill the process with Python's default, running "
                    "no `except` and printing nothing -- the pre-`bds6nd` behavior this exists to "
                    "prevent",
                )
                self.assertTrue(
                    callable(after),
                    f"{name}: SIGTERM must be bound to a real Python handler (so it can raise "
                    f"KeyboardInterrupt into the shared funnel), not to {after!r}",
                )

    def test_both_drivers_report_from_their_keyboardinterrupt_funnel(self):
        """The SIGINT half must be wired in BOTH drivers; a one-runner fix fails here.

        REPLACES an `ast.walk` for an `ExceptHandler` naming `KeyboardInterrupt` whose unparsed body
        mentioned `emit_shutdown_report` (audit 2026-09-19). Not a text grep, but it still asserted the
        SHAPE of a handler rather than what happens when one fires, and it could not see whether the
        report reached the operator.

        WHAT REPLACES IT: a real `KeyboardInterrupt` is raised from inside `main`'s try block (by
        patching `run_queue`, which is what `main` calls there) and the funnel's whole observable
        contract is asserted: the report is emitted TO STDERR, the unclosed item is named, the `aw runs`
        pointer is printed, the ledger record is on disk, and the exit status is the conventional 130.

        WHY TO STDERR MATTERS and is asserted: an interrupt fires mid-run when stdout may be carrying
        streamed child output, so a report printed there can be interleaved into a machine-read stream.
        """
        for name, mod in _DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                subprocess.run(["git", "init", "-q", "."], cwd=root, check=True)
                run_dir = root / ".aw" / "records" / "runs" / "run-ki"
                run_dir.mkdir(parents=True)
                (run_dir / "state.json").write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "run_id": "run-ki",
                            "repo": str(root),
                            "created_at": "2026-09-14T00:00:00+00:00",
                            "updated_at": "2026-09-14T00:00:00+00:00",
                            "selectors": ["demo"],
                            "options": {},
                            "set_sessions": {},
                            "queue": [
                                {
                                    "position": 1,
                                    "id6": "aaaaaa",
                                    "setid": "demo",
                                    "action": "execute",
                                    "kind": "child",
                                    "status": "executed",
                                    "dependencies": [],
                                    "attempts": [],
                                    "from_backlog": "bbbbbb",
                                    "backlog_close": {
                                        "item": "bbbbbb",
                                        "closed": False,
                                        "reason": "IPD carrier(s) not executed: x.ipd.md",
                                    },
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                oc_runipd._SIGNAL_REPORT_DONE.clear()
                oc_runipd._SIGNAL_REPORT_STATE.clear()
                self.addCleanup(oc_runipd._SIGNAL_REPORT_DONE.clear)
                self.addCleanup(oc_runipd._SIGNAL_REPORT_STATE.clear)
                emit_kwargs: list[dict] = []
                real_emit = mod.emit_shutdown_report

                def spy_emit(*args, _real=real_emit, _seen=emit_kwargs, **kwargs):
                    _seen.append(dict(kwargs))
                    return _real(*args, **kwargs)

                def interrupted(*_a, _mod=mod, _rd=run_dir, **_k):
                    # Publish the live state exactly as the real `run_queue` does first, then
                    # interrupt: the report reads from what was published.
                    _mod.register_signal_report(
                        _rd,
                        json.loads((_rd / "state.json").read_text(encoding="utf-8")),
                    )
                    raise KeyboardInterrupt("Interrupted")

                out, err = io.StringIO(), io.StringIO()
                with (
                    mock.patch.object(mod, "run_queue", interrupted),
                    mock.patch.object(mod, "emit_shutdown_report", spy_emit),
                    contextlib.redirect_stdout(out),
                    contextlib.redirect_stderr(err),
                ):
                    rc = mod.main(["resume", "--repo", str(root), "run-ki"])
                self.assertEqual(
                    rc,
                    130,
                    f"{name}: an interrupt must exit with the conventional SIGINT status",
                )
                self.assertEqual(
                    len(emit_kwargs),
                    1,
                    f"{name}.main must emit the shutdown report from its KeyboardInterrupt funnel "
                    f"exactly once; saw {len(emit_kwargs)}",
                )
                self.assertTrue(
                    emit_kwargs[0].get("to_stderr"),
                    f"{name}: the report must go to STDERR on the interrupt path. An interrupt fires "
                    "mid-run when stdout may be carrying streamed child output, so reporting there "
                    f"can corrupt a machine-read stream. Called with {emit_kwargs[0]}",
                )
                self.assertIn(
                    "bbbbbb",
                    err.getvalue(),
                    f"{name}: the interrupt report must NAME the item it left open",
                )
                self.assertIn(
                    "Run `aw runs run-ki` for more info.",
                    err.getvalue(),
                    f"{name}: the pointer must survive the interrupt path too",
                )
                self.assertTrue(
                    (run_dir / "events.jsonl").is_file(),
                    f"{name}: the LEDGER record must exist, so `aw runs` can still answer 'what did "
                    "it leave open?' when the terminal output is lost",
                )

    def test_the_callable_is_handler_safe(self):
        """`71vjbn` will call this FROM a real handler, so it must not lock, save, or block.

        REPLACES four `assertNotIn` searches over `_code_only()` output (audit 2026-09-19) with
        RECORDING TRAPS on the real collaborators: the callback is invoked and each forbidden helper
        must not be called even once. That is strictly stronger in two ways. It covers a call reached
        INDIRECTLY (the old search read only these two functions' own text, so a lock taken inside a
        helper they call was invisible), and it cannot be satisfied by prose.

        WHY A RECORDING TRAP AND NOT A RAISING ONE, measured while writing this: `emit_shutdown_report`
        wraps its work in `contextlib.suppress(Exception)` on purpose (a handler must not die), so a
        trap that RAISED would be swallowed and the test would pass no matter what. The trap therefore
        records and delegates.
        """
        report = oc_runipd.signal_report_callback()
        self.assertTrue(
            callable(report), "the callable `71vjbn` will invoke must exist"
        )
        # THE OWNING MODULE IS RESOLVED, NOT ASSUMED. hostdedup Order 01 (`li44r9`) lifted the lock and
        # state helpers into `runner_shared`, and reaches `platform_lock` through a FUNCTION-LOCAL import
        # (deliberately, so this module's pinned module-level first-party import set does not grow). So a
        # trap hard-coded to `oc_runipd` now misses the real collaborator and the test would pass
        # vacuously on a tree where the helper IS called. Each name is therefore trapped on whichever
        # module actually exposes it, and a name exposed by NEITHER is skipped explicitly rather than
        # silently: `platform_lock` is no longer a module attribute anywhere, and its acquisition is
        # covered by trapping `run_lock`, which is the only body that takes it.
        forbidden = ("run_lock", "locked_run", "save_state", "platform_lock")
        for name in forbidden:
            owner = next(
                (m for m in (oc_runipd, runner_shared) if hasattr(m, name)), None
            )
            if owner is None:
                # NOT a silent pass: assert the fallback coverage actually exists, so this branch cannot
                # become a hole if `run_lock` is ever renamed or removed too.
                self.assertTrue(
                    hasattr(oc_runipd, "run_lock")
                    or hasattr(runner_shared, "run_lock"),
                    f"{name} is exposed by no module AND run_lock is gone, so nothing covers the lock "
                    "acquisition a signal handler must not perform",
                )
                continue
            with self.subTest(
                forbidden=name, owner=owner.__name__
            ), tempfile.TemporaryDirectory() as tmp:
                run_dir = Path(tmp)
                oc_runipd._SIGNAL_REPORT_DONE.clear()
                oc_runipd._SIGNAL_REPORT_STATE.clear()
                oc_runipd.register_signal_report(run_dir, _state_with_open_item())
                hits: list[str] = []
                real = getattr(owner, name)

                def trap(*args, _name=name, _real=real, _hits=hits, **kwargs):
                    _hits.append(_name)
                    return _real(*args, **kwargs)

                sink = io.StringIO()
                with (
                    mock.patch.object(owner, name, trap),
                    contextlib.redirect_stdout(sink),
                    contextlib.redirect_stderr(sink),
                ):
                    oc_runipd.signal_report_callback()()
                self.assertEqual(
                    hits,
                    [],
                    f"the handler-safe report path must not reach {name!r}. A signal handler runs at "
                    "an arbitrary point between bytecodes, so acquiring a lock or persisting state "
                    "there can DEADLOCK against the very code it interrupted -- which is why "
                    "`71vjbn` may call this first thing in its handlers",
                )
                self.assertTrue(
                    (run_dir / "events.jsonl").is_file(),
                    "and the report must still have done its ONE job (the ledger append), or this "
                    "test would pass for a callback that did nothing at all",
                )

    def test_the_child_kill_escalation_path_is_unchanged(self):
        """The separate CHILD-process reaper must not be disturbed.

        REPLACES two `assertIn` source searches for the grace-constant NAMES (audit 2026-09-19) with the
        property they stood in for: each host's module-level constants must be READ AT CALL TIME and
        passed to the shared reaper. Both are patched to distinctive sentinel values and the shared
        implementation is spied on, so a reaper that hardcoded the defaults (or captured them at import)
        fails. The docstring on `terminate_process` promises exactly this ("read at call time, so a
        caller or test that tunes them still takes effect"), and this is the only form that checks it.

        The two `assertNotIn`s are replaced by the spy as well: the reaper is driven and the shutdown
        report helpers are trapped, so reaching them is detected however they are spelled.
        """
        from agent_workflows import runner_shutdown

        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                received: dict = {}
                report_hits: list[str] = []

                def spy_reaper(_process, _into=received, **kwargs):
                    _into.update(kwargs)

                def trap(label, _hits=report_hits):
                    def _trap(*_a, _label=label, _into=_hits, **_k):
                        _into.append(_label)

                    return _trap

                with (
                    mock.patch.object(mod, "_SIGINT_GRACE_SECONDS", 11.5),
                    mock.patch.object(mod, "_SIGTERM_GRACE_SECONDS", 22.5),
                    mock.patch.object(runner_shutdown, "terminate_process", spy_reaper),
                    mock.patch.object(
                        oc_runipd, "emit_shutdown_report", trap("emit_shutdown_report")
                    ),
                    mock.patch.object(
                        oc_runipd,
                        "register_signal_report",
                        trap("register_signal_report"),
                    ),
                ):
                    mod.terminate_process(object())
                self.assertEqual(
                    (received.get("sigint_grace"), received.get("sigterm_grace")),
                    (11.5, 22.5),
                    f"{name}.terminate_process must read its grace constants AT CALL TIME and hand "
                    "them to the ONE shared reaper, which is what its docstring promises and what "
                    f"lets a caller tune them. Shared reaper received: {received}",
                )
                self.assertEqual(
                    report_hits,
                    [],
                    f"{name}.terminate_process is the CHILD reaper and must stay SEPARATE from the "
                    f"run's shutdown report; it reached {report_hits}. Conflating them would make "
                    "reaping one child emit a whole-run report",
                )


# ======================================================================================
# Anti-divergence: ONE implementation, both drivers
# ======================================================================================


class SharedNotCopied(unittest.TestCase):
    """ONE implementation of the close API, reachable from both drivers.

    THE SET SPLITS IN TWO SINCE runnerlayer Order 02 (`1f7xno`), and the split is a REQUIREMENT of the
    mechanism rather than an exemption granted to make a test pass. Every name here used to be DEFINED
    in `oc_runipd` and imported by `agy_runipd`, so "the same object" and "one implementation" were the
    same statement. All of them now live in `runner_shared`, and four take an INJECTED `run_checked`,
    because the shared `run_checked` needs a host-specific `env_builder` that a shared body cannot
    resolve (`818uru` E-05's measured case, re-measured here: a bare lift raised `TypeError:
    run_checked() missing 1 required keyword-only argument: env_builder` on ten tests in this file).

    So those four keep a ONE-LINE runner-local `def` at the original name that binds this host's
    `run_checked` and delegates. That is a BINDING, not a second body, and it means the two hosts hold
    DIFFERENT wrapper objects over the SAME implementation. `assertIs` on them would forbid the
    injection mechanism itself, so they are asserted STRUCTURALLY instead, which is the identical
    treatment `tests/test_runner_shared.py::WrapperTests` gives `818uru`'s eight `INJECTED` symbols.

    WHAT IS NOT WEAKENED, because that is the question a reviewer should ask. The guarantee that matters
    is "exactly one implementation, and a fix to it reaches both hosts". For `_SHARED` that is still
    object identity. For `_WRAPPED` it is proven MORE strictly than identity would:
    `test_a_wrapped_name_is_a_single_delegating_statement_and_not_a_second_body` requires the local def
    to hold exactly ONE statement naming `runner_shared.<same name>`, so a wrapper that grew a body
    fails, and `test_no_wrapped_name_is_DEFINED_twice_in_the_package` pins the implementation as single.
    A copied body cannot pass either.
    """

    #: The four whose shared body takes an INJECTED `run_checked`, so each host keeps a one-line
    #: delegating wrapper and the two wrapper OBJECTS differ by construction.
    _WRAPPED = (
        "process_backlog_close",
        "close_backlog_item",
        "commit_backlog_close",
        "collect_earned_paths",
    )

    _SHARED = (
        "evaluate_backlog_close",
        "run_earned_paths",
        "resolve_backlog_item",
        "unclosed_backlog_items",
        "render_unclosed_report",
        "render_runs_pointer",
        "record_unclosed_backlog_items",
        "emit_shutdown_report",
        "register_signal_report",
        "signal_report_callback",
        "_read_from_backlog",
    )

    def test_both_drivers_expose_the_backlog_close_api(self):
        """EVERY name, wrapped or not: an absent attribute is an unbound re-export either way."""
        for name, mod in _DRIVERS:
            for attr in self._SHARED + self._WRAPPED:
                with self.subTest(driver=name, attr=attr):
                    self.assertTrue(hasattr(mod, attr), f"{name} must expose {attr}")

    def test_the_implementation_is_shared_not_copied(self):
        """OBJECT IDENTITY: a one-runner-only fix, or a second copy, fails here.

        Scoped to `_SHARED`. The `_WRAPPED` four are different objects BY CONSTRUCTION and are asserted
        structurally above; see the class docstring for why that is stronger rather than weaker.
        """
        for attr in self._SHARED:
            with self.subTest(attr=attr):
                self.assertIs(
                    getattr(agy_runipd, attr),
                    getattr(oc_runipd, attr),
                    f"{attr} must be the SAME object in both drivers, not a copy",
                )

    def test_both_drivers_call_the_close_from_their_finalize_success_branch(self):
        """The symmetry that matters behaviorally: both must actually INVOKE the close.

        REPLACES `assertIn("process_backlog_close(run_dir, state, item)", src)` (audit 2026-09-19) --
        a byte-exact copy of one call expression including its argument NAMES, so renaming a local
        variable broke it while the behavior was identical.

        WHAT REPLACES IT: a real `execute_item` turn is driven to disposition `executed` on a fixture
        repo whose plan already sits in `executed/`, with the close patched to a spy that must be called
        exactly once. This is the pin that matters most in this file: if the close is never invoked, the
        ENTIRE feature is inert, and the measured pre-fix state was precisely that (zero items in
        `done/` carried a graduation record).
        """
        for name, mod in _DRIVERS:
            spawn = "run_opencode" if name == "oc_runipd" else "run_agy_turn"
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                repo = _Repo(Path(tmp))
                repo.add_item("bbbbbb")
                # The plan is ALREADY in `executed/`, which is how `reconcile_disposition` reaches the
                # `executed` disposition (it reads the plan's bucket) without this fixture needing to
                # run a real finalize.
                plan = repo.add_plan("dbg001", bucket="executed", from_backlog="bbbbbb")
                repo.commit_all()
                run_dir = repo.root / ".aw" / "records" / "runs" / "run-close"
                (run_dir / "outcomes").mkdir(parents=True)
                (run_dir / "prompts").mkdir(parents=True)
                item = {
                    "position": 1,
                    "id6": "dbg001",
                    "setid": "demo",
                    "status": "queued",
                    "action": "execute",
                    "from_backlog": "bbbbbb",
                    "configured_file": repo.rel(plan),
                }
                state = {
                    "run_id": "run-close",
                    "created_at": "2026-09-14T00:00:00+00:00",
                    "updated_at": "2026-09-14T00:00:00+00:00",
                    "selectors": ["demo"],
                    "repo": str(repo.root),
                    "queue": [item],
                    "set_sessions": {},
                    "session_id": None,
                    "options": {
                        "opencode": "/bin/true",
                        "agy": "/bin/true",
                        "model": "probe",
                        "self_finalize": True,
                        "no_audit": True,
                        "isolate_worktree": False,
                    },
                }
                closes: list[tuple] = []
                sink = io.StringIO()
                with (
                    mock.patch.object(
                        mod,
                        spawn,
                        lambda *_a, _log=str(run_dir / "log"), **_k: (
                            0,
                            "ses",
                            _log,
                            ["probe"],
                        ),
                    ),
                    mock.patch.object(mod, "driver_begin", lambda *a, **k: (0, "ok")),
                    mock.patch.object(
                        mod, "driver_finalize", lambda *a, **k: (0, "ok")
                    ),
                    mock.patch.object(
                        mod, "assert_child_tool_identity", lambda *a, **k: None
                    ),
                    mock.patch.object(
                        mod,
                        "process_backlog_close",
                        lambda *a, _into=closes, **k: _into.append(a),
                    ),
                    contextlib.redirect_stdout(sink),
                    contextlib.redirect_stderr(sink),
                ):
                    mod.execute_item(run_dir, state, item, recovery=False)
                self.assertEqual(
                    item["status"],
                    "executed",
                    f"{name}: the fixture must reach the `executed` disposition, or the close branch "
                    "is never entered and this test proves nothing",
                )
                self.assertEqual(
                    len(closes),
                    1,
                    f"{name}.execute_item must attempt the backlog close EXACTLY ONCE after a "
                    "successful finalize. Zero means the whole feature is inert (the measured pre-fix "
                    f"state: no item had ever moved graduated -> done); saw {len(closes)} call(s)",
                )
                self.assertEqual(
                    closes[0][2]["from_backlog"],
                    "bbbbbb",
                    f"{name}: the close must be handed THIS item, so it can read the link the queue "
                    f"froze; got {closes[0][2].get('from_backlog')!r}",
                )

    def test_both_drivers_emit_the_shutdown_report_on_normal_exit(self):
        """Driven on a real `run_queue` (audit 2026-09-19), not read out of its source.

        REPLACES `assertIn("emit_shutdown_report()", src)` and `assertIn("register_signal_report(", src)`
        -- both satisfiable by a comment, and neither able to say the report FIRES. Here both are spied
        on a real drain of a one-item queue whose item carries an unclosed backlog link, and the
        observable end state is asserted too: the report's own section and the `aw runs` pointer must
        appear in the run's output.

        A MUTATION SURVIVED THE FIRST DRAFT AND THE TEST WAS STRENGTHENED (audit 2026-09-19). Deleting
        the PRE-TURN `register_signal_report` call -- the one whose whole purpose is that an interrupt
        arriving during the FIRST turn still reports from real state -- left this test green, because
        `run_queue` calls that function at FIVE sites and the later ones still ran. So the assertion is
        no longer "register was called at some point": the published ledger is now READ from inside the
        turn itself, which is the only observation that distinguishes publishing before the first turn
        from publishing after it. This is precisely the case the old source search could not see either,
        since one surviving call site keeps any substring present.
        """
        for name, mod in _DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                run_dir = Path(tmp) / "run-report"
                run_dir.mkdir(parents=True)
                item = {
                    "position": 1,
                    "id6": "aaaaaa",
                    "setid": "demo",
                    "action": "execute",
                    "kind": "child",
                    "status": "queued",
                    "dependencies": [],
                    "attempts": [],
                    "from_backlog": "bbbbbb",
                }
                (run_dir / "state.json").write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "run_id": "run-report",
                            "repo": str(tmp),
                            "created_at": "2026-09-14T00:00:00+00:00",
                            "updated_at": "2026-09-14T00:00:00+00:00",
                            "selectors": ["demo"],
                            "options": {},
                            "set_sessions": {},
                            "queue": [item],
                        }
                    ),
                    encoding="utf-8",
                )
                oc_runipd._SIGNAL_REPORT_DONE.clear()
                oc_runipd._SIGNAL_REPORT_STATE.clear()
                self.addCleanup(oc_runipd._SIGNAL_REPORT_DONE.clear)
                self.addCleanup(oc_runipd._SIGNAL_REPORT_STATE.clear)
                seen: list[str] = []
                real_emit = mod.emit_shutdown_report
                real_register = mod.register_signal_report

                def spy_emit(*args, _real=real_emit, _seen=seen, **kwargs):
                    _seen.append("emit")
                    return _real(*args, **kwargs)

                def spy_register(*args, _real=real_register, _seen=seen, **kwargs):
                    _seen.append("register")
                    return _real(*args, **kwargs)

                published_at_first_turn: list[dict] = []

                def fake_execute(
                    rd, st, it, *a, _mod=mod, _seen=published_at_first_turn, **k
                ):
                    # Read the published ledger FROM INSIDE the turn. This is the observation that
                    # catches deletion of the PRE-TURN publication while later call sites survive.
                    _seen.append(dict(oc_runipd._SIGNAL_REPORT_STATE))
                    it["status"] = "executed"
                    _mod.save_state(rd, st)

                buffer = io.StringIO()
                with (
                    mock.patch.object(mod, "execute_item", side_effect=fake_execute),
                    mock.patch.object(mod, "emit_shutdown_report", spy_emit),
                    mock.patch.object(mod, "register_signal_report", spy_register),
                    contextlib.redirect_stdout(buffer),
                    contextlib.redirect_stderr(buffer),
                ):
                    mod.run_queue(run_dir, retry_incomplete=False)
                output = buffer.getvalue()
                self.assertIn(
                    "emit",
                    seen,
                    f"{name}.run_queue must emit the shutdown report on NORMAL exit too, not only "
                    f"under a signal; observed calls {seen}",
                )
                self.assertIn(
                    "register",
                    seen,
                    f"{name}.run_queue must PUBLISH the live state for the signal path, or an "
                    f"interrupt reports from a stale snapshot (or from nothing); observed {seen}",
                )
                self.assertLess(
                    seen.index("register"),
                    seen.index("emit"),
                    f"{name}: the state must be published BEFORE the report is emitted, since the "
                    f"report reads from it; observed {seen}",
                )
                self.assertTrue(
                    published_at_first_turn
                    and published_at_first_turn[0].get("state") is not None,
                    f"{name}: the live state must ALREADY be published when the FIRST turn starts, "
                    "so an interrupt arriving during that turn reports from real state rather than "
                    "from nothing. `run_queue` publishes at five sites and the later ones cannot "
                    "cover this: a mutation deleting only the pre-turn call was measured to survive "
                    f"a weaker form of this assertion. Ledger seen at turn time: "
                    f"{published_at_first_turn}",
                )
                self.assertEqual(
                    str(published_at_first_turn[0].get("run_dir")),
                    str(run_dir),
                    f"{name}: and it must publish THIS run's directory, or the interrupt report "
                    "would append its ledger record somewhere else entirely",
                )
                self.assertIn(
                    "bbbbbb",
                    output,
                    f"{name}: the run's output must NAME the backlog item it left open; an item that "
                    "is silently absent is the reporting gap E-06 exists to close",
                )
                self.assertIn(
                    "Run `aw runs run-report` for more info.",
                    output,
                    f"{name}: the E-07 pointer must be printed on the human path",
                )

    def test_an_interrupt_BEFORE_the_first_turn_still_reports(self):
        """The window the PRE-LOOP publication exists for, and nothing else covers.

        MEASURED WHILE MUTATION-TESTING (audit 2026-09-19), and this test exists BECAUSE a mutation
        survived. Deleting `run_queue`'s first `register_signal_report` call left the sibling test above
        green, because `run_queue` publishes at FIVE sites and the four INSIDE the loop still ran; even
        reading the ledger from inside the first turn was not enough, since a loop-top refresh happens
        before the turn dispatches. The ONE window only the pre-loop call covers is an interrupt that
        arrives BEFORE the loop is entered at all -- during pre-loop reconciliation -- and that is what
        this drives, by making `reconcile_interrupted` raise.

        MEASURED CONSEQUENCE WITH THE CALL DELETED: the report named no item and NO LEDGER FILE WAS
        WRITTEN. An operator interrupting a run that was still winding up would be told nothing, and
        `aw runs <id>` could not answer afterwards either. That is exactly the silence E-06 exists to
        remove, so it is worth its own test rather than a stronger assertion bolted onto the sibling.
        """
        for name, mod in _DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                run_dir = Path(tmp) / "run-early"
                run_dir.mkdir(parents=True)
                (run_dir / "state.json").write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "run_id": "run-early",
                            "repo": str(tmp),
                            "created_at": "2026-09-14T00:00:00+00:00",
                            "updated_at": "2026-09-14T00:00:00+00:00",
                            "selectors": ["demo"],
                            "options": {},
                            "set_sessions": {},
                            "queue": [
                                {
                                    "position": 1,
                                    "id6": "aaaaaa",
                                    "setid": "demo",
                                    "action": "execute",
                                    "kind": "child",
                                    "status": "queued",
                                    "dependencies": [],
                                    "attempts": [],
                                    "from_backlog": "bbbbbb",
                                    "backlog_close": {
                                        "item": "bbbbbb",
                                        "closed": False,
                                        "reason": "IPD carrier(s) not executed: x.ipd.md",
                                    },
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                oc_runipd._SIGNAL_REPORT_DONE.clear()
                oc_runipd._SIGNAL_REPORT_STATE.clear()
                self.addCleanup(oc_runipd._SIGNAL_REPORT_DONE.clear)
                self.addCleanup(oc_runipd._SIGNAL_REPORT_STATE.clear)

                def interrupt_early(*_a, **_k):
                    raise KeyboardInterrupt("Interrupted")

                sink = io.StringIO()
                with (
                    mock.patch.object(mod, "reconcile_interrupted", interrupt_early),
                    contextlib.redirect_stdout(sink),
                    contextlib.redirect_stderr(sink),
                    self.assertRaises(KeyboardInterrupt),
                ):
                    mod.run_queue(run_dir, retry_incomplete=False)
                # The funnel in `main` is what calls this; here it is invoked directly so the test
                # stays about the PUBLICATION rather than about `main`'s handler (covered separately).
                report = io.StringIO()
                with (
                    contextlib.redirect_stdout(report),
                    contextlib.redirect_stderr(report),
                ):
                    mod.emit_shutdown_report()
                self.assertIn(
                    "bbbbbb",
                    report.getvalue(),
                    f"{name}: an interrupt arriving BEFORE the first turn must still report the item "
                    "left open. Failing here means the live state was not published until inside the "
                    "loop, so a run interrupted while winding up tells the operator nothing",
                )
                self.assertTrue(
                    (run_dir / "events.jsonl").is_file(),
                    f"{name}: and the LEDGER must exist, so `aw runs run-early` can answer afterwards. "
                    "With the pre-loop publication deleted this file was measured ABSENT entirely",
                )


class BacklogCloseIntegritySelfCheck(unittest.TestCase):
    """The runner must NOTICE when its own close leaves an item claiming two lifecycle states.

    THE MEASURED CORRUPTION, 2026-09-22. `git_commit_helper._staged_paths` read
    `git diff --name-only --cached`, which prints only the DESTINATION of a staged rename, so
    `offer_commit` filtered out the SOURCE and committed this relocation as a bare ADDITION. The
    pre-move copy therefore survived in HEAD beside its own destination: 36 backlog ids ended up in
    TWO status directories at once. `aw attention` reported every one as `attention.duplicate-id` and
    declared its whole board non-authoritative.

    THE READ BUG IS FIXED ELSEWHERE (and `tests/test_git_commit_helper.py` pins it directly). What is
    pinned HERE is the second line of defense: the runner knows which id6 it just wrote, so it must
    verify THAT id6 and say so at the moment of creation. This exists because detection-after-the-fact
    demonstrably did not prevent accumulation - the CI gate was correct, fired, and stayed red while
    143 further commits reached `origin/main` over two days.
    """

    def _repo(self, tmp) -> Path:
        root = Path(tmp)
        (root / ".aw/records/backlog/graduated").mkdir(parents=True, exist_ok=True)
        (root / ".aw/records/backlog/done").mkdir(parents=True, exist_ok=True)
        return root

    def _item(self, path: Path, id6: str, status: str) -> None:
        path.write_text(
            f"- Id: {id6}\n- Status: {status}\n- Summary: s\n\n## Workflow history\n",
            encoding="utf-8",
        )

    def test_a_single_claimant_is_the_healthy_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            self._item(
                root / ".aw/records/backlog/done/20260101-aa-01-abc123-x.backlog.md",
                "abc123",
                "done",
            )
            for name, mod in _DRIVERS:
                found = mod.backlog_item_paths_for_id(root, "abc123")
                self.assertEqual(
                    len(found),
                    1,
                    f"{name}: one file claiming the id must read as exactly one",
                )

    def test_two_claimants_are_detected_which_is_the_36_item_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            # EXACTLY the measured shape: the pre-move copy left behind beside its destination.
            self._item(
                root
                / ".aw/records/backlog/graduated/20260101-aa-01-abc123-x.backlog.md",
                "abc123",
                "graduated",
            )
            self._item(
                root / ".aw/records/backlog/done/20260101-aa-01-abc123-x.backlog.md",
                "abc123",
                "done",
            )
            for name, mod in _DRIVERS:
                found = mod.backlog_item_paths_for_id(root, "abc123")
                self.assertEqual(
                    len(found),
                    2,
                    f"{name}: the duplicate MUST be visible to the runner. Reporting one here is the "
                    "blindness that let 36 items corrupt over two days",
                )
                self.assertTrue(
                    any("graduated/" in p for p in found)
                    and any("done/" in p for p in found),
                    f"{name}: both lifecycle directories must be named, since naming only one tells "
                    f"an operator nothing about what to repair; got {found}",
                )

    def test_an_absent_id_is_empty_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            for name, mod in _DRIVERS:
                self.assertEqual(
                    mod.backlog_item_paths_for_id(root, "zzzzzz"),
                    [],
                    f"{name}: an id nothing claims is empty, never an exception",
                )

    def test_paths_are_repository_relative_so_no_home_path_can_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            self._item(
                root / ".aw/records/backlog/done/20260101-aa-01-abc123-x.backlog.md",
                "abc123",
                "done",
            )
            for name, mod in _DRIVERS:
                for rel in mod.backlog_item_paths_for_id(root, "abc123"):
                    self.assertFalse(
                        PurePath(rel).is_absolute(),
                        f"{name}: {rel!r} is absolute; these strings reach stderr and the run ledger, "
                        "which the leak sanitizer scans",
                    )
                    self.assertTrue(
                        rel.startswith(".aw/"), f"{name}: unexpected shape {rel!r}"
                    )

    def test_both_drivers_share_ONE_implementation(self):
        """A one-runner-only check would leave `aw agy run` able to corrupt the tree silently."""

        drivers = dict(_DRIVERS)
        if len(drivers) < 2:
            self.skipTest("only one driver module available")
        fns = {n: m.backlog_item_paths_for_id for n, m in drivers.items()}
        first = next(iter(fns.values()))
        for name, fn in fns.items():
            self.assertIs(
                fn,
                first,
                f"{name}: the integrity check has FORKED per host. Both drivers must resolve to one "
                "object or a fix lands on one runner only",
            )


if __name__ == "__main__":
    unittest.main()
