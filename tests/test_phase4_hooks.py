"""agentadhere Phase 4 (IPD diundn): local pre-commit/pre-push hooks + contract matrix.

Covers:
  E-01/V-01 - pre-commit scope/invariant gate: refuses an out-of-scope staged tree with a teaching
              message (invariant + recovery), passes clean, delegates to the shared aggregator (no
              fork), idempotent no-clobber install.
  E-02/V-02 - pre-push authorization gate: prevents an unacknowledged push with an HONEST local-only
              message, passes with the ack, delegates to the shared engine.
  E-03/V-03 - contract matrix (coverage, malformed input, disablement, fail-open/closed) + a
              NO-DIVERGENCE proof (hook and aw check produce the same rule for the same tree).

THE TWO "DELEGATES TO SHARED X, NO FORK" TESTS ARE BEHAVIORAL, and were not always. Each used to
read `inspect.getsource(<hook>.check)` and `assertIn` the shared helper's NAME. That proved neither
of the two things the claim needs: not that the hook reaches the SAME object (a hook holding its own
`def check_commit_invariants` satisfies the search perfectly), and not that it is CALLED AT ALL (a
mention in a comment satisfies it too, which this repository has measured twice). Both now PATCH the
shared surface with a spy returning a SENTINEL finding and assert the sentinel's own text arrives in
the hook's messages, which can only happen if the hook resolved and invoked that object at runtime.
The aggregator's half is proven the same way, one row per composed rule, by spying each shared rule
and requiring it to have RUN during a real gate invocation.

WHY A SENTINEL RATHER THAN A CALL COUNT ALONE: the load-bearing property is that the hook's OUTPUT
is the shared engine's finding, verbatim, including the `recovery` field it teaches. A call count
proves the call happened; the sentinel proves nothing was re-derived, re-worded, or dropped between
the rule and the operator.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import artifact_core as core
from agent_workflows import check_engine as ce
from agent_workflows import engine
from agent_workflows.hooks import precommit_scope_gate as pcgate
from agent_workflows.hooks import prepush_authorization_gate as ppgate


#: A finding no rule in the engine can produce, used to prove a hook's message really is the SHARED
#: surface's output rather than something the hook re-derived. Every field is distinctive so a
#: partial copy (rule kept, recovery dropped) still fails.
_SENTINEL = core.Drift(
    "SENTINEL-LOCATION",
    "check.sentinel-not-a-real-rule",
    "SENTINEL-DETAIL that no shared rule emits",
    recovery="aw sentinel-recovery-command",
)


def _mk_repo(tmp: Path):
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp, check=True)
    (tmp / ".gitignore").write_text(".aw/state/\n.aw/worktrees/\n", encoding="utf-8")
    plans = tmp / ".aw" / "records" / "plans" / "pending"
    plans.mkdir(parents=True)
    (tmp / "src").mkdir()
    (tmp / "other").mkdir()
    (plans / "20260828-t-01-aaa111-x.ipd.md").write_text(
        "# IPD: x\n\n- Id: aaa111\n- Kind: child\n- Status: approved\n- Set: t\n- Order: 1\n"
        "- Scope-Paths: src/\n\n## Workflow history\n- 2026-08-25 approved (aw set): x\n\n## Goal\n\ng\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp, check=True)
    base = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp, capture_output=True, text=True
    ).stdout.strip()
    rp = tmp / ".aw" / "state" / "ipd-lifecycle"
    rp.mkdir(parents=True, exist_ok=True)
    (rp / "aaa111.receipt.json").write_text(
        json.dumps({"plan_id": "aaa111", "base_head": base, "scope_paths": ["src/"]}),
        encoding="utf-8",
    )
    return tmp


@contextlib.contextmanager
def _push_ack(value):
    """Set (or clear, with `None`) the push-ack env var for the duration of the block."""
    previous = os.environ.get(ce.PUSH_ACK_ENV)
    if value is None:
        os.environ.pop(ce.PUSH_ACK_ENV, None)
    else:
        os.environ[ce.PUSH_ACK_ENV] = value
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(ce.PUSH_ACK_ENV, None)
        else:
            os.environ[ce.PUSH_ACK_ENV] = previous


class TestPreCommitGate(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = _mk_repo(Path(self._tmp.name))

    #: (case, repo-relative path to create, expected exit code, substrings every message set must
    #: carry, why this row exists)
    #:
    #: The CLEAN row lives in this table on purpose: a gate that refused everything would satisfy the
    #: refusal row alone, and a gate that refused nothing would satisfy no row but would look like a
    #: single broken assertion rather than the systematic failure it is.
    SCOPE_CASES = (
        (
            "an in-scope change only",
            "src/f.py",
            0,
            (),
            "THE CLEAN ROW, and the only one that can state the gate is not a blanket refusal. "
            "`src/` is the plan's declared Scope-Paths, so the ordinary commit must pass with NO "
            "messages at all; a gate that warns here trains an operator to `--no-verify` habitually, "
            "which disables it for the case below too",
        ),
        (
            "a change outside the declared Scope-Paths",
            "other/g.py",
            1,
            ("check.scope-drift", "fix:", "Scope-Paths"),
            "THE REFUSAL, with its TEACHING content (findings 4.4). Three substrings, because each "
            "is a separate promise: the RULE name makes the refusal auditable against `aw check`, "
            "`fix:` carries the recovery command the operator runs next, and `Scope-Paths` names the "
            "declaration that was violated. A refusal missing any one of them leaves a human knowing "
            "only that something was blocked",
        ),
    )

    def test_the_gate_passes_a_clean_tree_and_teaches_on_an_out_of_scope_one(self):
        failures = []
        for case, rel, expected_rc, required, why in self.SCOPE_CASES:
            with tempfile.TemporaryDirectory() as temp:
                root = _mk_repo(Path(temp))
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("x\n", encoding="utf-8")
                rc, msgs = pcgate.check(root)
            joined = "\n".join(msgs)
            problems = []
            if rc != expected_rc:
                problems.append(f"exit {rc}, expected {expected_rc}")
            if expected_rc == 0 and msgs:
                problems.append(f"expected NO messages, got {msgs!r}")
            missing = [token for token in required if token not in joined]
            if missing:
                problems.append(f"message lacks {missing!r}; message was {joined!r}")
            if problems:
                failures.append(
                    f"  {case}: {'; '.join(problems)}\n    this row exists because: {why}"
                )
        self.assertEqual(
            failures,
            [],
            f"precommit_scope_gate.check misbehaved for {len(failures)} of "
            f"{len(self.SCOPE_CASES)} trees. Read the rows TOGETHER: if only the out-of-scope row "
            "failed while the clean row passed, the scope rule stopped firing and every lane can now "
            "commit outside its declared territory; if only the CLEAN row failed, the gate became a "
            "blanket refusal and the negative row is passing VACUOUSLY. FIX: this hook must hold no "
            "policy of its own - it delegates to `check_engine.check_commit_invariants`, so repair "
            "the shared rule (and its `recovery` text) rather than adding a branch here.\n"
            + "\n".join(failures),
        )

    def test_the_gate_reaches_the_shared_aggregator_and_emits_its_finding_verbatim(
        self,
    ):
        """BEHAVIORAL replacement for a source-text pin that searched `check` for the helper's NAME.

        The spy is installed on `check_engine`, which is where the hook resolves the symbol (it
        imports the module inside the function), so a hook holding its OWN aggregator sees the real
        rules and never emits the sentinel.
        """
        calls = []

        def spy(repo_root):
            calls.append(Path(repo_root))
            return [_SENTINEL]

        with mock.patch.object(ce, "check_commit_invariants", spy):
            rc, msgs = pcgate.check(self.root)
        self.assertEqual(
            len(calls),
            1,
            "the gate must call the shared aggregator exactly once per invocation; it called it "
            f"{len(calls)} time(s), so it either forked the policy or re-runs it per rule",
        )
        self.assertEqual(
            calls[0], self.root, "the gate must pass the repo root through unchanged"
        )
        self.assertEqual(
            rc, 1, "a finding from the shared aggregator must fail the gate closed"
        )
        joined = "\n".join(msgs)
        for field in (
            _SENTINEL.location,
            _SENTINEL.rule,
            _SENTINEL.detail,
            _SENTINEL.recovery,
        ):
            self.assertIn(
                field,
                joined,
                f"the shared finding's {field!r} did not reach the operator. The hook's output must "
                f"be the engine's finding verbatim (including `recovery`, which is what it TEACHES); "
                f"messages were {msgs!r}",
            )

    #: (the shared rule the aggregator must re-invoke, why this row exists)
    #:
    #: DECISION 17-diundn-D1: the aggregator introduces NO policy, it COMPOSES existing rules. That
    #: is the whole no-divergence argument, so each composed rule is a row and each must be shown to
    #: RUN during a real gate invocation.
    COMPOSED_RULES = (
        (
            "check_status_untooled",
            "a staged HAND-EDITED plan status is the bypass every tooled transition exists to "
            "prevent; dropping it from the composition silently re-opens it",
        ),
        (
            "check_release_gate_consistency",
            "a staged release-blocking backlog item closed without a preserved gate is how a known "
            "bug ships; this is the rule that makes the pre-commit gate see it",
        ),
        (
            "check_scope_drift",
            "the receipt-scoped scope invariant (findings 5.3) is the gate's NAMESAKE rule; if it "
            "stopped being composed the hook would pass every out-of-scope tree while still looking "
            "like a scope gate",
        ),
    )

    def test_the_aggregator_reinvokes_every_shared_rule_rather_than_forking_policy(
        self,
    ):
        ran = []
        failures = []
        (self.root / "other" / "g.py").write_text("y\n", encoding="utf-8")

        def make_spy(name, real):
            def spy(repo_root):
                ran.append(name)
                return real(repo_root)

            return spy

        with contextlib.ExitStack() as stack:
            for name, _why in self.COMPOSED_RULES:
                stack.enter_context(
                    mock.patch.object(ce, name, make_spy(name, getattr(ce, name)))
                )
            rc, msgs = pcgate.check(self.root)

        for name, why in self.COMPOSED_RULES:
            if name not in ran:
                failures.append(
                    f"  {name}: never called during a real gate invocation\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            failures,
            [],
            f"check_commit_invariants failed to re-invoke {len(failures)} of "
            f"{len(self.COMPOSED_RULES)} shared rules (it ran {ran!r}; the gate returned rc={rc} "
            f"with {len(msgs)} message(s)). The aggregator's ONLY justification is that it composes "
            "the rules `aw check` runs, so a rule it stops calling is a rule the hook and `aw check` "
            "now DISAGREE about. FIX: add the rule back to the composition tuple in "
            "`check_engine.check_commit_invariants`; do NOT reimplement its logic inside the "
            "aggregator or the hook.\n" + "\n".join(failures),
        )

    def test_no_divergence_hook_matches_aw_check(self):
        # the hook and the engine's scope-drift rule produce the SAME rule for the same tree
        (self.root / "other" / "g.py").write_text("y\n", encoding="utf-8")
        _rc, msgs = pcgate.check(self.root)
        engine_rules = {d.rule for d in ce.check_scope_drift(self.root)}
        self.assertIn("check.scope-drift", engine_rules)
        self.assertTrue(any("check.scope-drift" in m for m in msgs))

    def test_malformed_input_fails_isolated(self):
        """NOT a row: the claim is that a rule's internal error is ISOLATED, which is a structurally
        different assertion (it constrains what did NOT happen - a raise - rather than a verdict)."""
        # a corrupt receipt must not crash the gate (aggregator isolates a rule error)
        rp = self.root / ".aw" / "state" / "ipd-lifecycle" / "aaa111.receipt.json"
        rp.write_text("{not json", encoding="utf-8")
        rc, _msgs = pcgate.check(self.root)
        self.assertIn(rc, (0, 1))  # did not raise


class TestPrePushGate(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = _mk_repo(Path(self._tmp.name))

    #: (case, the `AW_PUSH_AUTHORIZED` value or None for unset, expected exit code, why this row
    #: exists)
    #:
    #: THE ACK IS PARSED, NOT MERELY TESTED FOR PRESENCE, so the parse is what this table pins. Note
    #: the `"NO"` and `"False"` rows: the comparison is CASE-SENSITIVE against a lowercase set, so
    #: the uppercase spellings ACKNOWLEDGE. That is recorded as observed behavior rather than
    #: asserted as desirable; see the failure message.
    ACK_CASES = (
        (
            "unset",
            None,
            1,
            "THE DEFAULT, and the only row that matters for an accidental push: an operator who has "
            "done nothing must be stopped. If this row alone regressed, the guard is inert while "
            "every other row still passes",
        ),
        (
            "empty string",
            "",
            1,
            "an exported-but-empty variable is how a shell rc file leaves a name defined; it must "
            "count as NO acknowledgement, or `export AW_PUSH_AUTHORIZED=` would permanently disable "
            "the guard",
        ),
        (
            "whitespace only",
            "   ",
            1,
            "the value is `.strip()`ped before comparison, so whitespace is equivalent to empty; "
            "without the strip a stray space would read as an ack",
        ),
        (
            "the literal 0",
            "0",
            1,
            "`0` is the conventional OFF value and is in the falsey set explicitly; a hook that read "
            "any non-empty string as consent would treat a deliberate opt-OUT as consent",
        ),
        (
            "lowercase false",
            "false",
            1,
            "the falsey set is spelled in lowercase, which this row pins together with the case "
            "rows below",
        ),
        (
            "lowercase no",
            "no",
            1,
            "as above, and the pair (`false`, `no`) is what makes the case-sensitivity rows "
            "interpretable rather than looking like isolated flukes",
        ),
        (
            "uppercase NO",
            "NO",
            0,
            "OBSERVED, NOT ENDORSED: the comparison is case-sensitive, so `NO` is NOT in the falsey "
            "set and therefore ACKNOWLEDGES the push. Recorded so the sharp edge is visible in the "
            "suite; an operator typing `NO` gets the opposite of what they meant",
        ),
        (
            "capitalized False",
            "False",
            0,
            "the same sharp edge in the spelling Python itself uses, which is the one a developer is "
            "most likely to type by reflex",
        ),
        (
            "the literal 1",
            "1",
            0,
            "the documented acknowledgement. A gate that refused here would make an intended push "
            "impossible without `--no-verify`, i.e. it would train the bypass",
        ),
        (
            "an arbitrary non-falsey string",
            "acknowledged-by-operator",
            0,
            "the ack is a PRESENCE signal rather than an enumerated token, so any non-falsey value "
            "consents. Kept as a row because it is the behavior a reader would otherwise have to "
            "infer from the absence of a token list",
        ),
    )

    def test_the_ack_is_parsed_exactly_as_the_shared_engine_specifies(self):
        failures = []
        for case, value, expected_rc, why in self.ACK_CASES:
            with _push_ack(value):
                rc, msgs = ppgate.check(self.root)
            problems = []
            if rc != expected_rc:
                problems.append(f"exit {rc}, expected {expected_rc}")
            if expected_rc == 0 and msgs:
                problems.append(f"expected no messages, got {msgs!r}")
            if expected_rc == 1 and not any(
                "check.push-unauthorized" in m for m in msgs
            ):
                problems.append(
                    f"a prevention must name `check.push-unauthorized`; got {msgs!r}"
                )
            if problems:
                failures.append(
                    f"  {case} ({value!r}): {'; '.join(problems)}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            failures,
            [],
            f"the pre-push ack parse is wrong for {len(failures)} of {len(self.ACK_CASES)} values. "
            "Read them as two groups: the falsey group (unset/empty/whitespace/0/false/no) must "
            "PREVENT, and everything else must ALLOW. If the whole falsey group now allows, the "
            "guard is inert and no accidental push is caught; if the whole allow group now prevents, "
            "no authorized push can proceed without `--no-verify`, which trains the bypass and is "
            "worse than no hook. If ONLY the `NO`/`False` rows moved, somebody made the comparison "
            "case-insensitive: that is arguably an IMPROVEMENT, so change those rows to expect 1 and "
            "say so, rather than reverting the code. FIX: the parse lives in "
            "`prepush_authorization_gate.check` against `check_engine.PUSH_ACK_ENV`; keep this table "
            "and the shared rule in step.\n" + "\n".join(failures),
        )

    def test_honest_local_only_message(self):
        """NOT a row: this drives `main()` and inspects STDERR prose rather than the (rc, messages)
        pair every row asserts, and its subject is the honesty of the wording, not the verdict."""
        out = io.StringIO()
        with _push_ack(None):
            with redirect_stderr(out), redirect_stdout(io.StringIO()):
                rc = ppgate.main([])
        self.assertEqual(rc, 1)
        text = out.getvalue()
        # honestly states local-only, bypassable, NOT an authority boundary
        self.assertIn("NOT an authority boundary", text)
        self.assertIn("--no-verify", text)

    def test_the_gate_reaches_the_shared_engine_and_forwards_the_ack_it_computed(self):
        """BEHAVIORAL replacement for a pin that searched `check`'s source for the helper's NAME.

        Two claims, and the old pin proved neither: the hook CALLS the shared rule (shown by the
        sentinel finding arriving in its output), and it hands that rule the ack it parsed rather
        than deciding the question itself (shown by the recorded `ack` argument tracking the env).
        """
        recorded = []

        def spy(repo_root, ack=False):
            recorded.append((Path(repo_root), ack))
            return [_SENTINEL]

        with mock.patch.object(ce, "check_push_authorization", spy):
            with _push_ack(None):
                rc_unset, msgs = ppgate.check(self.root)
            with _push_ack("1"):
                ppgate.check(self.root)

        self.assertEqual(
            [ack for _root, ack in recorded],
            [False, True],
            "the hook must PARSE the env and forward the result as `ack`, letting the shared rule "
            f"decide; recorded calls were {recorded!r}",
        )
        self.assertEqual(recorded[0][0], self.root)
        self.assertEqual(
            rc_unset, 1, "a finding from the shared rule must prevent the push"
        )
        joined = "\n".join(msgs)
        for field in (
            _SENTINEL.location,
            _SENTINEL.rule,
            _SENTINEL.detail,
            _SENTINEL.recovery,
        ):
            self.assertIn(
                field,
                joined,
                f"the shared finding's {field!r} did not reach the operator, so this hook is not "
                f"simply rendering the engine's verdict; messages were {msgs!r}",
            )

    def test_push_rule_is_authority_class(self):
        """NOT a row: the subject is the rule REGISTRY's metadata, not the gate's runtime verdict."""
        # honest labeling: the push invariant is Authority-class (a local hook can only give feedback)
        spec = ce.rule_spec("check.push-unauthorized")
        self.assertEqual(spec.assurance, ce.ASSURANCE_AUTHORITY)
        self.assertEqual(spec.invariant, "I-02")


class TestHookInstall(unittest.TestCase):
    """Installation is one contract with the HOOK KIND as its only varying dimension, so the two
    per-class copies became one table: `create_*_hook(repo, False, install=...)`."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = _mk_repo(Path(self._tmp.name))

    #: (hook kind, the `engine` factory, why this row exists)
    INSTALLERS = (
        (
            "pre-commit scope gate",
            "create_precommit_scope_gate_hook",
            "E-01's installer. It writes the SAME `.pre-commit-config.yaml` the pre-push installer "
            "does, which is exactly why no-clobber matters: the second installer must MERGE into a "
            "file the first one created rather than replace it",
        ),
        (
            "pre-push authorization gate",
            "create_prepush_authorization_gate_hook",
            "E-02's installer, tabulated beside its twin because a divergence between the two "
            "install paths is invisible while each is asserted in its own class",
        ),
    )

    def test_every_hook_installer_is_idempotent_and_never_clobbers(self):
        failures = []
        for kind, factory_name, why in self.INSTALLERS:
            with tempfile.TemporaryDirectory() as temp:
                root = _mk_repo(Path(temp))
                factory = getattr(engine, factory_name)
                problems = []
                first = factory(root, False, install=True)
                if first["created"] != [".pre-commit-config.yaml"]:
                    problems.append(
                        f"first install created {first['created']!r}, expected "
                        "['.pre-commit-config.yaml']"
                    )
                second = factory(root, False, install=True)
                if not second["skipped"]:
                    problems.append(
                        f"second install reported nothing skipped ({second!r}), so it is not "
                        "idempotent"
                    )
                if second["created"] != []:
                    problems.append(
                        f"second install created {second['created']!r}, expected nothing"
                    )
                noop = factory(root, False, install=False)
                if noop != {"created": [], "skipped": [], "notes": []}:
                    problems.append(f"install=False was not a no-op: {noop!r}")
                if problems:
                    failures.append(
                        f"  {kind}: {'; '.join(problems)}\n"
                        f"    this row exists because: {why}"
                    )
        self.assertEqual(
            failures,
            [],
            f"{len(failures)} of {len(self.INSTALLERS)} hook installers broke the install contract. "
            "The contract has three parts and the failure text says which broke: CREATE on a fresh "
            "repo, SKIP (no duplicate entry) on a re-run, and NO-OP when `install=False`. A broken "
            "SKIP is the dangerous one: re-running `aw setup-repo` would then append a duplicate "
            "hook, or overwrite a `.pre-commit-config.yaml` carrying the OTHER gate plus whatever "
            "the operator added by hand. FIX: keep both installers on the shared merge-not-replace "
            "helper in `engine.py`; a second bespoke writer is how these two diverge.\n"
            + "\n".join(failures),
        )


if __name__ == "__main__":
    unittest.main()
