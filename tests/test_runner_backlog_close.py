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

import ast
import inspect
import json
import re
import signal
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from agent_workflows import agy_runipd, check_engine, ipd_schema, oc_runipd
from tests.support import REPO_ROOT

_DRIVERS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))
_DRIVER_SOURCES = (
    ("oc_runipd", REPO_ROOT / "agent_workflows" / "oc_runipd.py"),
    ("agy_runipd", REPO_ROOT / "agent_workflows" / "agy_runipd.py"),
)


def _code_only(text: str) -> str:
    """``text`` with `#` comments and docstrings/string literals removed, via the real tokenizer.

    The source guards below assert things about CODE, not about prose. A docstring that NAMES a
    banned construct in order to explain why it is absent must not be indistinguishable from the
    construct itself. Mirrors the same helper in `tests/test_runner_item_dependencies.py`.
    """
    import io
    import token as _token
    import tokenize as _tokenize

    kept: list[str] = []
    try:
        for tok in _tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type in (_token.COMMENT, _token.STRING):
                continue
            kept.append(tok.string)
    except (_tokenize.TokenError, IndentationError):  # pragma: no cover - defensive
        return "\n".join(
            ln for ln in text.splitlines() if not ln.lstrip().startswith("#")
        )
    return "\n".join(kept)


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
        """The manifest and the frozen queue entry both carry it, in both drivers."""
        self.repo.add_plan("aaaaaa", from_backlog="bbbbbb")
        self.repo.add_plan("cccccc", order=2)
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                manifest = mod.build_dynamic_manifest(
                    self.repo.root, mod.discover_plans(self.repo.root)
                )
                self.assertEqual(manifest["plans"]["aaaaaa"]["from_backlog"], "bbbbbb")
                self.assertIsNone(manifest["plans"]["cccccc"]["from_backlog"])

                src = inspect.getsource(mod.initialize_run)
                self.assertIn(
                    '"from_backlog"',
                    src,
                    f"{name}.initialize_run must freeze from_backlog on the queue entry",
                )

    def test_absent_and_placeholder_values_mean_no_linked_item(self):
        for raw in ("-", "none", "unresolved", ""):
            with self.subTest(value=raw):
                text = _plan_text("aaaaaa").replace(
                    "- Id: aaaaaa", f"- Id: aaaaaa\n- From-Backlog: {raw}"
                )
                self.assertIsNone(oc_runipd._read_from_backlog(text))

    def test_no_new_regex_the_field_name_comes_from_the_schema(self):
        """The field NAME must be the schema's constant, not a private pattern (E-01)."""
        self.assertEqual(ipd_schema.META_FROM_BACKLOG, "From-Backlog")
        src = inspect.getsource(oc_runipd._read_from_backlog)
        self.assertIn(
            "META_FROM_BACKLOG",
            src,
            "the reader must resolve the field name through ipd_schema.META_FROM_BACKLOG",
        )
        for name, path in _DRIVER_SOURCES:
            text = path.read_text(encoding="utf-8")
            offenders = [
                line
                for line in text.splitlines()
                if re.search(r"re\.compile\([^)]*From-Backlog", line)
            ]
            self.assertEqual(
                offenders,
                [],
                f"{name} must not define a private From-Backlog regex: {offenders}",
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
        """A `draft` and a `to-review` spec must produce the SAME verdict: existence is the test."""
        for status in ("draft", "to-review", "approved"):
            with self.subTest(spec_status=status):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = _Repo(Path(tmp))
                    repo.add_item("bbbbbb")
                    spec = repo.add_spec("dddddd", from_backlog="bbbbbb", status=status)
                    verdict = oc_runipd.evaluate_backlog_close(
                        repo.root, "bbbbbb", [repo.rel(spec)]
                    )
                    self.assertTrue(verdict.close, f"{status}: {verdict.reason}")
        src = _code_only(inspect.getsource(oc_runipd.evaluate_backlog_close))
        self.assertNotIn(
            "spec_status",
            src,
            "the non-IPD rule must not consult spec status; existence is the whole test",
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
        """E-02: `check_engine.find_from_backlog_artifacts` is THE lookup; no second scan."""
        src = inspect.getsource(oc_runipd.evaluate_backlog_close)
        self.assertIn("find_from_backlog_artifacts", src)
        self.assertTrue(callable(check_engine.find_from_backlog_artifacts))
        for name, path in _DRIVER_SOURCES:
            text = path.read_text(encoding="utf-8")
            self.assertEqual(
                text.count("def find_from_backlog"),
                0,
                f"{name} must not define its own carrier lookup",
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
        original = oc_runipd.plan_bucket

        def boom(*_a, **_k):
            raise RuntimeError("induced bucket read failure")

        oc_runipd.plan_bucket = boom  # type: ignore[assignment]
        try:
            verdict = oc_runipd.evaluate_backlog_close(
                self.repo.root, "bbbbbb", [self.repo.rel(plan)]
            )
        finally:
            oc_runipd.plan_bucket = original  # type: ignore[assignment]
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
        """E-02: close via the lifecycle-owned setter, never by writing the item file."""
        src = _code_only(
            inspect.getsource(oc_runipd.process_backlog_close)
            + inspect.getsource(oc_runipd.close_backlog_item)
        )
        for banned in ("write_text", "atomic_write", "unlink", "replace("):
            self.assertNotIn(
                banned,
                src,
                f"the close path must not {banned}; the setter owns the item file",
            )

    def test_the_commit_is_path_scoped_to_this_item_only(self):
        """A co-worker's edit to a DIFFERENT backlog item must never be swept in."""
        raw = inspect.getsource(oc_runipd.commit_backlog_close)
        code = _code_only(raw)
        self.assertIn("offer_commit", code, "must use the shared tooled commit path")
        # STRUCTURAL, not textual: assert an id6 membership test really gates the path set, so
        # reformatting cannot break the guard and prose cannot satisfy it.
        tree = ast.parse(textwrap.dedent(raw))
        gated = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Compare)
            and any(isinstance(op, ast.In) for op in node.ops)
            and "item_id6" in ast.unparse(node.left)
            and "name" in ast.unparse(node)
        ]
        self.assertTrue(
            gated,
            "the path set must be filtered by `item_id6 in <path>.name` so a co-worker's "
            "edit to a DIFFERENT backlog item can never be swept in",
        )
        for banned in ("-A", "add_all"):
            self.assertNotIn(
                banned,
                raw.replace("no push", ""),
                f"the commit must never use {banned}",
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
        state = _state_with_open_item()
        state["queue"][0].pop("from_backlog")
        self.assertEqual(oc_runipd.unclosed_backlog_items(state), [])

    def test_the_ledger_record_is_written_before_the_print(self):
        """Ordering is the whole point: a truncated print still leaves the answer on disk."""
        src = inspect.getsource(oc_runipd.emit_shutdown_report)
        tree = ast.parse(textwrap.dedent(src))
        order: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                rendered = ast.unparse(node)
                if (
                    "record_unclosed_backlog_items" in rendered
                    and "ledger" not in order
                ):
                    order.append("ledger")
                if rendered.startswith("print(") and "print" not in order:
                    order.append("print")
        self.assertEqual(
            order[:2],
            ["ledger", "print"],
            f"the ledger append must precede the print; saw {order}",
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

    def test_the_string_aw_oc_runs_appears_nowhere_in_either_driver(self):
        """`aw oc runs` is not a command and must never be emitted."""
        for name, path in _DRIVER_SOURCES:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(
                "aw oc runs ",
                text,
                f"{name} must not emit the nonexistent `aw oc runs` verb",
            )

    def test_json_output_suppresses_the_pointer(self):
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                src = inspect.getsource(mod.main)
                tree = ast.parse(textwrap.dedent(src))
                for node in ast.walk(tree):
                    if not isinstance(node, ast.If):
                        continue
                    if '"json"' not in ast.unparse(
                        node.test
                    ) and "json" not in ast.unparse(node.test):
                        continue
                    body = "\n".join(ast.unparse(stmt) for stmt in node.body)
                    if "json.dumps" not in body:
                        continue
                    self.assertNotIn(
                        "render_runs_pointer",
                        body,
                        f"{name}: the --json branch must not print the pointer",
                    )


# ======================================================================================
# E-05: the runner's own signal handlers (real subprocesses)
# ======================================================================================


_SIGNAL_SCRIPT = """
import json, os, signal, sys, time
from pathlib import Path
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
        """`main` must actually INSTALL the handler, or the SIGTERM half silently regresses."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                src = inspect.getsource(mod.main)
                self.assertIn(
                    "install_exit_signal_handler()",
                    src,
                    f"{name}.main must install the SIGTERM->KeyboardInterrupt handler",
                )
                self.assertIn(
                    "143",
                    src,
                    f"{name}.main must preserve the conventional SIGTERM exit status",
                )

    def test_both_drivers_report_from_their_keyboardinterrupt_funnel(self):
        """The SIGINT half must be wired in BOTH drivers; a one-runner fix fails here."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                src = inspect.getsource(mod.main)
                tree = ast.parse(textwrap.dedent(src))
                handlers = [
                    h
                    for h in ast.walk(tree)
                    if isinstance(h, ast.ExceptHandler)
                    and h.type is not None
                    and "KeyboardInterrupt" in ast.unparse(h.type)
                ]
                self.assertTrue(
                    handlers, f"{name}.main must keep its KeyboardInterrupt funnel"
                )
                body = "\n".join(ast.unparse(stmt) for h in handlers for stmt in h.body)
                self.assertIn(
                    "emit_shutdown_report",
                    body,
                    f"{name} must emit the shutdown report on interrupt",
                )

    def test_the_callable_is_handler_safe(self):
        """`71vjbn` will call this FROM a real handler, so it must not lock, save, or block."""
        report = oc_runipd.signal_report_callback()
        self.assertTrue(callable(report))
        # CODE only: a docstring that NAMES the banned call in order to explain why it is absent must
        # not trip the guard, or honest documentation would read as the defect.
        src = _code_only(
            inspect.getsource(oc_runipd.emit_shutdown_report)
            + inspect.getsource(oc_runipd.signal_report_callback)
        )
        for banned in ("run_lock", "locked_run", "save_state", "flock"):
            self.assertNotIn(
                banned, src, f"the handler-safe report path must not call {banned}"
            )

    def test_the_registration_is_left_to_its_owner(self):
        """Four executed plans reserve `signal.signal` IN THESE TWO FILES for `71vjbn`.

        This is not an oversight and it is not a gap in E-05. It is a boundary about WHERE the
        registration may live, and it survives E-05 being complete: the SIGTERM handler is registered
        in `render_stream` (by executed plan `bds6nd`) and both signals reach the report through the
        shared `except KeyboardInterrupt` funnel, so nothing here needs to call `signal.signal`. If a
        later change adds that call to either runner module, it must be coordinated with `71vjbn`'s
        escalation ladder rather than landing by accident.
        """
        for name, path in _DRIVER_SOURCES:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(
                "signal.signal(",
                text,
                f"{name}: SIGINT/SIGTERM registration belongs to runstop Phase 5 (71vjbn)",
            )

    def test_the_child_kill_escalation_path_is_unchanged(self):
        """The separate CHILD-process reaper must not be disturbed."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                src = inspect.getsource(mod.terminate_process)
                self.assertIn("_SIGINT_GRACE_SECONDS", src)
                self.assertIn("_SIGTERM_GRACE_SECONDS", src)
                for banned in ("emit_shutdown_report", "register_signal_report"):
                    self.assertNotIn(
                        banned,
                        src,
                        f"{name}.terminate_process is the CHILD reaper and must stay separate",
                    )


# ======================================================================================
# Anti-divergence: ONE implementation, both drivers
# ======================================================================================


class SharedNotCopied(unittest.TestCase):
    _SHARED = (
        "evaluate_backlog_close",
        "process_backlog_close",
        "close_backlog_item",
        "commit_backlog_close",
        "collect_earned_paths",
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
        for name, mod in _DRIVERS:
            for attr in self._SHARED:
                with self.subTest(driver=name, attr=attr):
                    self.assertTrue(hasattr(mod, attr), f"{name} must expose {attr}")

    def test_the_implementation_is_shared_not_copied(self):
        """OBJECT IDENTITY: a one-runner-only fix, or a second copy, fails here."""
        for attr in self._SHARED:
            with self.subTest(attr=attr):
                self.assertIs(
                    getattr(agy_runipd, attr),
                    getattr(oc_runipd, attr),
                    f"{attr} must be the SAME object in both drivers, not a copy",
                )

    def test_agy_does_not_redefine_any_of_the_shared_functions(self):
        text = (REPO_ROOT / "agent_workflows" / "agy_runipd.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(text)
        defined = {
            n.name
            for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        for attr in self._SHARED:
            with self.subTest(attr=attr):
                self.assertNotIn(
                    attr,
                    defined,
                    f"agy_runipd must IMPORT {attr}, not re-declare it",
                )

    def test_both_drivers_call_the_close_from_their_finalize_success_branch(self):
        """The symmetry that matters behaviorally: both must actually INVOKE the close."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                src = inspect.getsource(mod.execute_item)
                self.assertIn(
                    "process_backlog_close(run_dir, state, item)",
                    src,
                    f"{name}.execute_item must attempt the backlog close after finalize",
                )

    def test_both_drivers_emit_the_shutdown_report_on_normal_exit(self):
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                src = inspect.getsource(mod.run_queue)
                self.assertIn("emit_shutdown_report()", src, f"{name}.run_queue")
                self.assertIn("register_signal_report(", src, f"{name}.run_queue")


if __name__ == "__main__":
    unittest.main()
