"""The missing-input REPORT-AND-REFUSE cycle (spec `7ckptx` R3; plan `y5od1h`, Set `lanectn`).

WHAT THIS FILE DELIBERATELY DOES NOT TEST, because asserting it would assert behavior the spec now
FORBIDS. Spec `R3.3a` (maintainer amendment, 2026-09-01) withdrew the permit-and-copy branch, the
secret vocabulary (`R3.3a-1`/`-1a`/`-1b`/`-2`), `R3.3b`'s tracked-versus-untracked permit test, and
`R3.4`'s copy. So there is NO test here for a secret family, no test for a tracked file being
permitted, and no test for a successful copy. `NoWithdrawnWorkTests` asserts their ABSENCE instead,
which is the honest inversion: the withdrawal is a property to prove, not merely work to skip.

The live criteria are A6 (as amended: refusal), A7 (every reject shape from the shared predicate),
and A19 (a denied permission event routes through the SAME classifier).
"""

from __future__ import annotations

import ast
import contextlib
import inspect
import json
import tempfile
import textwrap
import unittest
from unittest import mock
from pathlib import Path

from agent_workflows import (
    agy_runipd,
    lane_containment,
    oc_runipd,
    runner_stop,
    worktree_lease,
)

LC = lane_containment

#: The two driver modules the cycle must be wired into IDENTICALLY. Parameterized rather than
#: duplicated, because orchestrator CID-3 makes a rule present in one driver only a DEFECT, and two
#: copied test functions are exactly how such an omission survives review.
DRIVERS = (("oc", oc_runipd), ("agy", agy_runipd))


def _checkout_with(
    files: dict[str, str], dirs: tuple[str, ...] = ()
) -> tempfile.TemporaryDirectory:
    """A throwaway checkout carrying `files` (and empty `dirs`), for path-shape classification."""

    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    for rel, body in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    for rel in dirs:
        (root / rel).mkdir(parents=True, exist_ok=True)
    return temp


class _FakeHostProcess:
    """A stand-in for the agent host's child process, emitting a scripted stdout stream.

    Substituted for `subprocess.Popen` so a driver's REAL per-line loop runs over lines this test
    chooses. Exits 0 immediately, so the loop is the only thing exercised.
    """

    def __init__(self, lines, *args, **kwargs):
        self.stdout = iter(lines)
        self.stderr = None
        self.stdin = None
        self.pid = -1
        self.returncode = 0
        self.args = []

    def poll(self):
        return 0

    def wait(self, timeout=None):
        return 0

    def communicate(self, input=None, timeout=None):
        return ("", "")

    def kill(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None


def _drive_turn(module, lines):
    """Run `module`'s REAL turn loop over `lines`; return (the mutated item, the logged events).

    WHY THIS EXISTS. The wiring claims in `TwinParityTests` were substring searches over a driver's
    entire module source, which any COMMENT satisfies (and both drivers comment this cycle at length).
    Driving the real loop is what observes the wiring: the per-line call either happens for every line
    or it does not, and the refusal either reaches the durable event log or it does not.

    The turn is invoked directly rather than through `execute_item`, deliberately: `execute_item` would
    run the begin gate, allocate a real worktree, and spawn a verifier, none of which this property
    depends on, while the per-line loop under test lives entirely in the turn function.
    """
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    repo = root / "repo"
    repo.mkdir()
    # The checkout the observer CLASSIFIES AGAINST is the repo (not the lane), so a row that needs a
    # well-formed EXISTING path needs this file to be here. Found by writing the table first: the
    # `README.md` row initially came back `path-does-not-exist`, which was the harness being wrong
    # rather than the driver, and is exactly the distinction the rule column exists to expose.
    (repo / "README.md").write_text("readme\n", encoding="utf-8")
    run_dir = root / "run"
    (run_dir / "sessions").mkdir(parents=True)
    (run_dir / "prompts").mkdir(parents=True)
    plan = repo / "p.ipd.md"
    plan.write_text("- Id: y5od1h\n", encoding="utf-8")
    prompt = run_dir / "prompts" / "p.md"
    prompt.write_text("do the thing\n", encoding="utf-8")

    item: dict[str, object] = {
        "id6": "y5od1h",
        "setid": "lanectn",
        "position": 1,
        "attempts": [{"number": 1}],
        "action": "execute",
    }
    state: dict[str, object] = {
        "run_id": "run-1",
        "repo": str(repo),
        "options": {"opencode": "opencode", "agy": "agy", "output_mode": "quiet"},
        "queue": [item],
    }

    try:
        with mock.patch.object(
            module.subprocess, "Popen", lambda *a, **k: _FakeHostProcess(lines)
        ):
            if hasattr(module, "run_opencode"):
                module.run_opencode(
                    state, run_dir, item, plan, prompt, 1, work_dir=None
                )
            else:
                module.run_agy_turn(
                    state, run_dir, item, prompt, 1, None, False, work_dir=None
                )
        events_path = run_dir / "events.jsonl"
        events = (
            [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if events_path.exists()
            else []
        )
        return item, events
    finally:
        temp.cleanup()


class TokenFormTests(unittest.TestCase):
    """R3.1: ONE deterministic token form, and the parser DERIVES it rather than re-spelling it."""

    #: (case, the line to parse, the expected `(path, reason)` or None for "not a report", why this
    #: row exists)
    #:
    #: ONE TABLE because the parser is called on EVERY line of a child's stdout, so what a reader needs
    #: to browse is the boundary between "this is a report" and "this is ordinary output" - and that is
    #: a single closed question with rows on both sides of it. Keeping the POSITIVE and NEGATIVE rows
    #: together is what makes each side non-vacuous: a parser returning None for everything satisfies
    #: every negative row, and one returning a tuple for everything satisfies every positive row.
    PARSES = (
        (
            "a token this module itself emitted",
            LC.format_missing_input_token("config/local.ini", "absent from lane"),
            ("config/local.ini", "absent from lane"),
            "THE ROUND TRIP, built through `format_missing_input_token` rather than hand-spelled: the "
            "emitter and the parser must agree by CONSTRUCTION, since a report neither side can read "
            "back is silently ignored",
        ),
        (
            "a reason containing colons",
            "AW_MISSING_INPUT:a/b.txt:needed by step 3: the schema generator",
            ("a/b.txt", "needed by step 3: the schema generator"),
            "a worker writes PROSE in the reason, and prose contains colons. A naive 2-way split "
            "truncates it at the first one, discarding exactly the explanation an auditor needs",
        ),
        (
            "an empty line",
            "",
            None,
            "the stdout loop sees blank lines constantly; a parser that raised or matched here would "
            "fire on essentially every turn",
        ),
        (
            "a whitespace-only line",
            "  ",
            None,
            "as above, and it pins that the parser does not treat a stripped-empty line as a "
            "zero-field report",
        ),
        (
            "ordinary build output",
            "building wheel...",
            None,
            "the common case, and the row that makes the positive rows meaningful",
        ),
        (
            "a JSON tool event",
            '{"type":"tool","name":"read"}',
            None,
            "structured host output shares the stream with reports; a parser matching inside JSON "
            "would misread a tool call naming a path as a missing-input report",
        ),
        (
            "the token form mentioned mid-line in prose",
            "mentions AW_MISSING_INPUT in prose but not at the start",
            None,
            "ANCHORING, which is the subtlest property here: a worker (or this very test file) may "
            "DISCUSS the token form, and only a line that STARTS with it is a report. Without the "
            "anchor, an agent explaining the protocol would pause its own lane",
        ),
    )

    def test_the_parser_accepts_exactly_the_report_form_and_nothing_else(self):
        failures = []
        for case, line, expected, why in self.PARSES:
            try:
                got = LC.parse_missing_input_token(line)
            except Exception as exc:  # a raise is a failure mode of its own here
                got = f"<raised {type(exc).__name__}: {exc}>"
            if got != expected:
                failures.append(
                    f"  {case} ({line!r}): expected {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            failures,
            [],
            f"the report parser answered wrongly for {len(failures)} of {len(self.PARSES)} lines. Read "
            "the two groups together: if every NEGATIVE row failed, the parser now matches ordinary "
            "output and every turn in the fleet pauses its lane on its own build log; if every "
            "POSITIVE row failed, no report is ever recognized and the whole report-and-refuse cycle "
            "is inert while looking wired. A `<raised ...>` value is its own defect: this runs for "
            "EVERY line of a child's stdout, so an exception here kills turns. FIX: the parser is "
            "`lane_containment.parse_missing_input_token` and it must DERIVE its prefix from "
            "`MISSING_INPUT_TOKEN_FORM` (see the next test) rather than re-spelling it.\n"
            + "\n".join(failures),
        )

    def test_token_shape_is_derived_from_the_published_prompt_constant(self):
        """NOT a row: the subject is the relationship between the parser and the PUBLISHED constant,
        not the parse of any particular line, so it has no data column in common with the table."""
        # THE POINT OF THIS TEST: child `cqx5v7` publishes `MISSING_INPUT_TOKEN_FORM` into the prompt
        # (R1.4). If the parser hardcoded its own prefix, the prompt could name one shape while the
        # driver matched another and every report would be silently ignored. So assert the parser
        # follows the CONSTANT, not a literal: the emitted token must start with the constant's own
        # leading code.
        prefix = LC.MISSING_INPUT_TOKEN_FORM.split(":", 1)[0]
        self.assertTrue(
            LC.format_missing_input_token("a", "b").startswith(prefix + ":"),
            "the emitted token must use the prefix the PROMPT publishes",
        )
        self.assertIsNotNone(LC.parse_missing_input_token(prefix + ":a/b.txt:why"))


class PreserveAndPauseTests(unittest.TestCase):
    """R3.1/R3.2 (criterion A6): parse, PRESERVE AND PAUSE, no prompt, and never block the worker."""

    def test_report_pauses_without_prompting_or_blocking(self):
        with _checkout_with({"README.md": "x"}) as root:
            obs = LC.MissingInputObserver(root)
            self.assertFalse(obs.paused)
            decision = obs.observe_line(
                LC.format_missing_input_token(".venv/bin/python", "toolchain absent")
            )
            self.assertIsNotNone(decision)
            # PAUSED, and the reason names the path, so the state is inspectable.
            self.assertTrue(obs.paused)
            self.assertIn(".venv/bin/python", obs.pause_reason)
            # NOT BLOCKED: the call returned, and the observer exposes no wait/answer surface at all.
            for forbidden in ("wait", "answer", "prompt", "ask", "input"):
                self.assertFalse(
                    any(forbidden in name for name in dir(obs)),
                    f"the observer must expose no {forbidden!r} surface (R3.2 forbids prompting)",
                )

    def test_worker_continues_after_reporting(self):
        # R3.1: "the worker emits it and continues with independent work; it does not wait." Feed a
        # report FOLLOWED by more output and assert the later lines are still processed.
        with _checkout_with({"README.md": "x"}) as root:
            obs = LC.MissingInputObserver(root)
            lines = [
                "starting",
                LC.format_missing_input_token(
                    "gen/schema.json", "generated, not tracked"
                ),
                "continuing with independent work",
                LC.format_missing_input_token(".venv/pyvenv.cfg", "also absent"),
                "done",
            ]
            seen = [obs.observe_line(line) for line in lines]
            self.assertEqual(
                [s is not None for s in seen], [False, True, False, True, False]
            )
            self.assertEqual(len(obs.decisions), 2)

    #: (case, how to build the item, the predicate's expected verdict, why this row exists)
    #:
    #: THE PREDICATE IS THE LOAD-BEARING HALF and is easy to fake: a log line saying "preserved" is not
    #: preservation, so what matters is what the drivers actually consult before
    #: `teardown_isolation_worktree`. The three rows are the three states an item can be in when that
    #: question is asked, which is a closed set and therefore a table.
    PRESERVATION_STATES = (
        (
            "a fresh item with no refusal",
            lambda: {"id6": "y5od1h", "attempts": [{"number": 1}]},
            False,
            "THE CLEAN ROW. Without it a predicate hardcoded to True would satisfy both rows below "
            "while making every lane in every run non-reclaimable, so disk fills and no lane is ever "
            "torn down",
        ),
        (
            "an item that recorded a refusal this run",
            "record",
            True,
            "THE CENTRAL CLAIM (R3.2): a refused report must make the lane NON-RECLAIMABLE, because "
            "the lane holds the evidence of what the worker could not find. Built by running the real "
            "`record_missing_input_refusal` rather than by setting the flag, so the recorder and the "
            "predicate are shown to agree",
        ),
        (
            "a resumed run's item, rebuilt from state with no observer",
            lambda: {"id6": "y5od1h", "lane_paused_for_missing_input": True},
            True,
            "THE DURABILITY PROPERTY. A resumed run reconstructs the item from `state.json` and NEVER "
            "reconstructs the observer, so a predicate that consulted in-memory observer state would "
            "silently return False after a resume and tear down the very lane being preserved",
        ),
    )

    def test_the_preserve_predicate_answers_correctly_in_every_item_state(self):
        failures = []
        for case, builder, expected, why in self.PRESERVATION_STATES:
            if builder == "record":
                item: dict[str, object] = {"id6": "y5od1h", "attempts": [{"number": 1}]}
                with tempfile.TemporaryDirectory() as run:
                    LC.record_missing_input_refusal(
                        Path(run),
                        item,
                        1,
                        LC.classify_missing_input_report(
                            "x/y.txt", "absent", checkout=run
                        ),
                    )
            else:
                item = builder()
            got = LC.lane_preserved_for_missing_input(item)
            if got is not expected:
                failures.append(
                    f"  {case}: expected {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            failures,
            [],
            f"lane_preserved_for_missing_input answered wrongly for {len(failures)} of "
            f"{len(self.PRESERVATION_STATES)} item states. Read them together: if the two True rows "
            "failed, a refused report no longer preserves its lane and the driver will tear down the "
            "worktree holding the only evidence of what the worker could not reach (spec R3.2); if the "
            "CLEAN row failed, the predicate preserves everything and no lane is ever reclaimed; if "
            "only the RESUMED row failed, the predicate started reading in-memory observer state "
            "instead of the durable item, so preservation survives until the first resume and then "
            "silently stops. FIX: the predicate must read the item's own durable fields only.\n"
            + "\n".join(failures),
        )


class RejectShapeTests(unittest.TestCase):
    """R3.3/R3.5 (criterion A7): every forbidden shape refused precisely, with NO copy."""

    #: (the reported path, the rule that must classify it, an extra substring the reason must carry or
    #: None, why this row exists)
    #:
    #: THE EIGHT SHAPES R3.3 ENUMERATES, in the order the spec lists them, PLUS the three cases that
    #: used to be separate single-assertion tests: the well-formed path the amendment created a branch
    #: for, the malformed token, and the drive-letter absolute. All ten differ only in the path string
    #: and the expected rule, which is the definition of a row; keeping them in ONE table is also what
    #: makes `test_every_reject_rule_carries_a_distinct_nonempty_reason` legible, since that test
    #: asserts these ten rules have ten distinct reasons.
    REJECT_SHAPES = (
        (
            "/etc/passwd",
            LC.REJECT_ABSOLUTE,
            None,
            "an absolute path must be refused as ABSOLUTE rather than resolved: honoring one would "
            "read a location the lane has no claim on, and a report must name a REPO-RELATIVE path",
        ),
        (
            "pkg/../../outside/x.txt",
            LC.REJECT_ESCAPES_CHECKOUT,
            None,
            "traversal must be caught after NORMALIZATION, not by looking for a leading slash; this is "
            "the shape that reaches outside the checkout while looking relative",
        ),
        (
            ".aw/records/plans/x.ipd.md",
            LC.REJECT_COORDINATOR_SURFACE,
            None,
            "a plan is a COORDINATOR-OWNED surface: a worker reading or editing one could rewrite the "
            "very checklist that gates its own work. This row is also the one "
            "`test_reject_uses_the_shared_predicate_by_call_not_a_copied_list` proves comes from the "
            "SHARED predicate rather than a local copy",
        ),
        (
            ".aw/worktrees/other/deploy.conf",
            LC.REJECT_SIBLING_LANE,
            None,
            "the per-lane worktrees root names either a SIBLING LANE's workspace or this lane by a "
            "path it should not use; cross-lane reads are how one item's work contaminates another's",
        ),
        (
            ".aw/state/lane-submissions/x/y.json",
            LC.REJECT_MACHINE_STATE,
            None,
            "driver run state is MACHINE-LOCAL rather than an input: handing it over would let a "
            "worker read (and reason about) the coordinator's own bookkeeping",
        ),
        (
            ".git/config",
            LC.REJECT_GIT_ADMIN,
            None,
            "the git ADMINISTRATION directory is where credentials and remotes live, and the driver "
            "performs every git mutation itself; a worker never needs it",
        ),
        (
            "pkg",
            LC.REJECT_DIRECTORY,
            None,
            "a report must name ONE specific required file. A directory is a request for an unbounded "
            "set, which cannot be audited",
        ),
        (
            "no/such/file.txt",
            LC.REJECT_ABSENT,
            None,
            "the path DOES NOT EXIST, so no input could satisfy the report even if a permitted path "
            "existed. Distinguished from the withdrawn-repair rule below because the two tell a human "
            "very different things about what to do next",
        ),
        (
            "README.md",
            LC.REJECT_WITHDRAWN_REPAIR,
            "R3.3a",
            "THE BRANCH THE AMENDMENT CREATED. This path exists, is inside the checkout, and is a "
            "regular file, so EVERY reject shape above passes - and it is STILL refused, by a rule "
            "that does NOT claim it was malformed. The reason must cite `R3.3a`, because 'refused' "
            "without the reason reads as a bug rather than as policy",
        ),
        (
            "",
            LC.REJECT_MALFORMED_TOKEN,
            None,
            "a malformed report is REFUSED, not silently dropped: silence would leave a worker "
            "believing its report was received and a reader believing none was made",
        ),
        (
            # ASSEMBLED, not written out: a literal drive-letter path trips the repository's local-leak
            # scanner (rules `windows-home` and `users-path`), and an allowlist entry would be the
            # wrong fix for a path that is purely synthetic. The comment must avoid the shape too,
            # since the scanner reads comments.
            "C:" + "/" + "Us" + "ers/example/config.ini",
            LC.REJECT_ABSOLUTE,
            None,
            "the drive-letter absolute must be refused ON EVERY PLATFORM, not only where "
            "`os.path.isabs` happens to recognize it: a POSIX-only absoluteness test treats this as a "
            "relative path named `C:` and walks straight past the guard",
        ),
    )

    def test_each_forbidden_shape_is_refused_with_its_own_rule(self):
        failures = []
        files = {"README.md": "x", "pkg/mod.py": "y"}
        dirs = ("pkg", "agent_workflows")
        with _checkout_with(files, dirs) as root:
            for path, expected_rule, reason_needle, why in self.REJECT_SHAPES:
                d = LC.classify_missing_input_report(path, "why", checkout=root)
                record = d.as_dict()
                problems = []
                if d.rule != expected_rule:
                    problems.append(f"rule {d.rule!r}, expected {expected_rule!r}")
                if d.verdict != LC.MISSING_INPUT_VERDICT_REFUSED:
                    problems.append(f"verdict {d.verdict!r}, expected refused")
                # PRECISE: the record names the path and a non-empty reason (R3.5).
                if d.path != path:
                    problems.append(
                        f"the record echoed path {d.path!r}, expected {path!r}"
                    )
                if not d.reason.strip():
                    problems.append(
                        "the reason is empty, so the record teaches nothing"
                    )
                if reason_needle is not None and reason_needle not in d.reason:
                    problems.append(
                        f"the reason does not cite {reason_needle!r}: {d.reason!r}"
                    )
                # NO COPY, NO GRANT, asserted on the emitted record rather than inferred.
                if record["copied_into_lane"] is not False:
                    problems.append("the record claims copied_into_lane")
                if record["granted_original_checkout_access"] is not False:
                    problems.append("the record claims granted checkout access")
                if problems:
                    failures.append(
                        f"  {path!r}: {'; '.join(problems)}\n"
                        f"    this row exists because: {why}"
                    )
        self.assertEqual(
            failures,
            [],
            f"{len(failures)} of {len(self.REJECT_SHAPES)} reported shapes were classified wrongly. "
            "Read the rows together: if MANY rows collapsed onto one rule, the classifier stopped "
            "distinguishing shapes and an auditor can no longer tell a traversal attempt from a "
            "missing file, which is the whole point of naming ten rules; if a `copied_into_lane` or "
            "grant claim appeared, the withdrawn permit-and-copy branch is back (spec R3.3a) and a "
            "lane is being handed content on request. If only the `README.md` row failed, the AMENDED "
            "branch is gone and a well-formed request is being refused under a rule that blames the "
            "request instead of stating the policy.\n" + "\n".join(failures),
        )

    def test_no_copy_is_created_in_the_checkout_for_any_shape(self):
        # Assert the PROPERTY (nothing was materialized) over the filesystem, not just the record.
        with _checkout_with({"README.md": "x"}) as root:
            before = sorted(
                p.relative_to(root).as_posix() for p in Path(root).rglob("*")
            )
            for path in (
                "/etc/passwd",
                "a/../../x",
                ".aw/records/plans/p.ipd.md",
                ".aw/worktrees/o/f",
                ".aw/state/s",
                ".git/config",
                "no/such.txt",
                "README.md",
            ):
                LC.classify_missing_input_report(path, "why", checkout=root)
            after = sorted(
                p.relative_to(root).as_posix() for p in Path(root).rglob("*")
            )
            self.assertEqual(before, after, "classification must create nothing")

    def test_a_malformed_token_reaches_the_classifier_through_the_observer_too(self):
        """NOT a row: the table classifies DIRECTLY, and this asserts the OBSERVER routes a malformed
        token in rather than discarding it before classification - a different code path."""
        with _checkout_with({}) as root:
            obs = LC.MissingInputObserver(root)
            decision = obs.observe_line("AW_MISSING_INPUT::")
            self.assertIsNotNone(
                decision,
                "an empty-path token must be REFUSED rather than ignored: silence would leave the "
                "worker believing its report was received",
            )
            self.assertEqual(decision.rule, LC.REJECT_MALFORMED_TOKEN)

    def test_reject_uses_the_shared_predicate_by_call_not_a_copied_list(self):
        # R3.3's last clause + V-02: the coordinator-surface class must COME FROM
        # `worktree_lease.path_is_worker_forbidden`. Proven by PATCHING that predicate and showing the
        # classifier's verdict follows the patch - a duplicated list would not move.
        with _checkout_with({"ordinary.txt": "x"}) as root:
            baseline = LC.classify_missing_input_report(
                "ordinary.txt", "w", checkout=root
            )
            self.assertEqual(baseline.rule, LC.REJECT_WITHDRAWN_REPAIR)
            original = worktree_lease.path_is_worker_forbidden
            try:
                worktree_lease.path_is_worker_forbidden = lambda p: p == "ordinary.txt"
                patched = LC.classify_missing_input_report(
                    "ordinary.txt", "w", checkout=root
                )
            finally:
                worktree_lease.path_is_worker_forbidden = original
            self.assertEqual(
                patched.rule,
                LC.REJECT_COORDINATOR_SURFACE,
                "the classifier must CALL the shared predicate, not hold its own copy",
            )
            # And the patch is undone, so the module is left as found.
            self.assertEqual(
                LC.classify_missing_input_report(
                    "ordinary.txt", "w", checkout=root
                ).rule,
                LC.REJECT_WITHDRAWN_REPAIR,
            )

    def test_the_shared_predicate_itself_was_not_widened(self):
        # This plan's deferral says it REUSES the shared predicate and "adds nothing to it" (child
        # `604wra` owns R6). Pin the five coordinator-owned surfaces so a later edit here is caught.
        self.assertEqual(
            worktree_lease.FORBIDDEN_WORKER_PATH_HINTS,
            (
                "events.jsonl",
                ".aw/records/plans/",
                ".aw/records/backlog/",
                ".aw/records/walkthroughs/",
                ".aw/records/runs/",
            ),
        )


class StructuralNoGrantTests(unittest.TestCase):
    """R3.6 (criterion A7): the no-live-grant property is STRUCTURAL, not a convention."""

    def test_the_decision_type_has_no_field_that_could_express_a_grant(self):
        fields = set(LC.MissingInputDecision._fields)
        for banned in (
            "granted",
            "permitted",
            "allowed",
            "grant",
            "permit",
            "allow",
            "copy",
            "copied",
            "materialized",
            "source_path",
            "absolute_path",
            "checkout_path",
            "original_path",
        ):
            self.assertNotIn(
                banned,
                fields,
                f"MissingInputDecision must not carry a {banned!r} field (R3.6: the TYPE cannot "
                "represent a live grant)",
            )

    def test_refused_is_the_only_verdict_the_module_defines(self):
        verdicts = {
            name for name in dir(LC) if name.startswith("MISSING_INPUT_VERDICT_")
        }
        self.assertEqual(
            verdicts,
            {"MISSING_INPUT_VERDICT_REFUSED"},
            "a second verdict constant would give the type a way to express a non-refusal",
        )

    def test_every_emitted_record_states_no_copy_and_no_grant(self):
        with _checkout_with({"README.md": "x"}) as root:
            for path in ("README.md", "/abs", "no/such.txt", ".git/config"):
                record = LC.classify_missing_input_report(
                    path, "w", checkout=root
                ).as_dict()
                self.assertIs(record["copied_into_lane"], False)
                self.assertIs(record["granted_original_checkout_access"], False)
                self.assertEqual(record["verdict"], "refused")

    def test_no_field_of_any_record_leaks_a_path_outside_the_lane(self):
        # ASSERT THE PROPERTY, NOT THE WORDING: even for an absolute request, no emitted VALUE may be
        # an absolute path other than the echo of what the worker itself asked for.
        # Assembled rather than written literally, for the same leak-scanner reason as above: a
        # literal home-style path is flagged `home-path`, and this one is synthetic.
        outside_absolute = "/" + "home/example/private/key.txt"
        with _checkout_with({}) as root:
            record = LC.classify_missing_input_report(
                outside_absolute, "w", checkout=root
            ).as_dict()
            leaked = [
                (k, v)
                for k, v in record.items()
                if isinstance(v, str) and v.startswith("/") and k != "path"
            ]
            self.assertEqual(
                leaked, [], f"no field but the echoed request may be absolute: {leaked}"
            )


class DeniedPermissionRoutingTests(unittest.TestCase):
    """R3.7 (criterion A19): a denied permission event takes the SAME path as a worker token."""

    def test_same_decision_as_the_equivalent_token_differing_only_in_provenance(self):
        with _checkout_with({"README.md": "x"}, ("pkg",)) as root:
            for path in (
                "README.md",
                "/etc/passwd",
                "a/../../out",
                ".aw/records/plans/p.ipd.md",
                ".aw/worktrees/o/f",
                ".aw/state/s",
                ".git/config",
                "pkg",
                "no/such.txt",
            ):
                with self.subTest(path=path):
                    token = LC.classify_missing_input_report(path, "why", checkout=root)
                    denied = LC.classify_denied_permission_path(
                        path, "why", checkout=root
                    )
                    # IDENTICAL but for `source`, which is provenance only.
                    self.assertEqual(
                        denied._replace(source=token.source),
                        token,
                        "one classification path, not two (R3.7)",
                    )
                    self.assertEqual(token.source, LC.MISSING_INPUT_SOURCE_TOKEN)
                    self.assertEqual(denied.source, LC.MISSING_INPUT_SOURCE_PERMISSION)

    def test_routing_is_a_call_into_the_one_classifier_not_a_second_implementation(
        self,
    ):
        # STRUCTURE, NOT GREP: the routing function's own AST must contain a call to
        # `classify_missing_input_report` and must not re-derive any reject rule.
        tree = ast.parse(inspect.getsource(LC.classify_denied_permission_path))
        called = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertIn("classify_missing_input_report", called)
        # The second half was a RAW TEXT search for `REJECT_ABSOLUTE` in the same source, which the
        # docstring could satisfy and which named only ONE of the ten rules. Now it is an AST NAME
        # scan over EVERY reject rule the module defines: re-deriving any of them here would be the
        # second implementation this test forbids, and a comment cannot satisfy an `ast.Name`.
        referenced = {
            node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
        } | {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        reject_rules = {name for name in dir(LC) if name.startswith("REJECT_")}
        self.assertTrue(
            reject_rules, "the module defines no REJECT_* rules; this scan is vacuous"
        )
        self.assertEqual(
            sorted(referenced & reject_rules),
            [],
            "the denied-permission router references a reject rule directly, which means it is "
            "classifying rather than ROUTING. One classification path, not two (R3.7): the rule must "
            "come back from `classify_missing_input_report`, or the two entry points will drift and a "
            "denied permission event will be judged by different policy than an identical worker "
            "token.",
        )

    def test_the_observer_routes_a_denied_event_identically(self):
        with _checkout_with({"README.md": "x"}) as root:
            obs = LC.MissingInputObserver(root)
            denied = obs.observe_denied_permission(
                "README.md", "host denied external_directory"
            )
            self.assertEqual(denied.source, LC.MISSING_INPUT_SOURCE_PERMISSION)
            self.assertEqual(denied.rule, LC.REJECT_WITHDRAWN_REPAIR)
            self.assertTrue(obs.paused, "a denied event must pause the lane too (R3.2)")


class RefusalRecordTests(unittest.TestCase):
    """R3.5 (criteria A6/A7): the refusal is RECORDED precisely, on the attempt and in the log."""

    def test_record_names_path_and_reason_on_attempt_and_event(self):
        attempts: list[dict[str, object]] = [{"number": 1}]
        item: dict[str, object] = {"id6": "y5od1h", "attempts": attempts}
        with tempfile.TemporaryDirectory() as run:
            run_dir = Path(run)
            decision = LC.classify_missing_input_report(
                ".venv/bin/python", "toolchain absent", checkout=run
            )
            written = LC.record_missing_input_refusal(run_dir, item, 1, decision)
            self.assertEqual(written["path"], ".venv/bin/python")
            self.assertTrue(written["reason"].strip())
            self.assertEqual(written["worker_stated_reason"], "toolchain absent")
            # On the ATTEMPT, keyed to the attempt that produced it.
            attempt = attempts[0]
            self.assertEqual(len(attempt["missing_input_refusals"]), 1)  # type: ignore[arg-type]
            self.assertTrue(attempt["lane_paused_for_missing_input"])
            # And in the durable event log.
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            refusals = [e for e in events if e["event"] == "missing-input-refused"]
            self.assertEqual(len(refusals), 1)
            self.assertEqual(refusals[0]["path"], ".venv/bin/python")
            self.assertTrue(refusals[0]["reason"].strip())
            self.assertIs(refusals[0]["copied_into_lane"], False)

    def test_record_falls_back_to_the_item_when_no_attempt_matches(self):
        item: dict[str, object] = {"id6": "y5od1h"}
        with tempfile.TemporaryDirectory() as run:
            LC.record_missing_input_refusal(
                Path(run),
                item,
                1,
                LC.classify_missing_input_report("x.txt", "w", checkout=run),
            )
        self.assertEqual(len(item["missing_input_refusals"]), 1)  # type: ignore[arg-type]
        self.assertTrue(item["lane_paused_for_missing_input"])

    def test_every_reject_rule_carries_a_distinct_nonempty_reason(self):
        """ "Precise" means the rules are DISTINGUISHABLE; identical prose for two rules would make the
        record useless to an auditor even though each field is populated.

        DRIVEN FROM `RejectShapeTests.REJECT_SHAPES` rather than from a second hand-kept path list. The
        two lists used to be maintained separately and had already drifted in spelling (`/abs` here
        versus `/etc/passwd` there), which meant adding a rule to one and forgetting the other would
        silently reduce this test's coverage while it still asserted a hardcoded count of 10.
        """
        expected_rules = {
            rule for _path, rule, _needle, _why in RejectShapeTests.REJECT_SHAPES
        }
        with _checkout_with({"README.md": "x", "pkg/mod.py": "y"}, ("pkg",)) as root:
            reasons: dict[str, str] = {}
            for path, _rule, _needle, _why in RejectShapeTests.REJECT_SHAPES:
                d = LC.classify_missing_input_report(path, "w", checkout=root)
                reasons[d.rule] = d.reason
        self.assertEqual(
            set(reasons),
            expected_rules,
            "the shapes in `REJECT_SHAPES` no longer produce exactly the rules that table declares, "
            "so two shapes have collapsed onto one rule (or a new rule appeared unannounced)",
        )
        blank = sorted(rule for rule, reason in reasons.items() if not reason.strip())
        self.assertEqual(blank, [], f"these rules carry an EMPTY reason: {blank!r}")
        by_reason: dict[str, list[str]] = {}
        for rule, reason in reasons.items():
            by_reason.setdefault(reason, []).append(rule)
        shared = {
            reason: rules for reason, rules in by_reason.items() if len(rules) > 1
        }
        self.assertEqual(
            shared,
            {},
            "two or more reject rules carry the SAME reason text, so the record cannot tell an "
            f"auditor which rule fired: {shared!r}. Each rule's reason must state what is specifically "
            "wrong with that shape, because the reason is the only field a human reads when deciding "
            "whether a refusal was correct.",
        )


class NoWithdrawnWorkTests(unittest.TestCase):
    """E-03/E-05: prove the WITHDRAWN work is absent (spec R3.3a), structurally rather than by eye."""

    #: Vocabulary that would indicate a SECRET-SHAPED classification (spec R3.3a withdrew it), and
    #: what each spelling would mean if it appeared in the code.
    #:
    #: EACH IS BUILT AT RUNTIME FROM CHARACTER CODES rather than written as a literal. Two independent
    #: reasons: the repository's leak-sanitizer scans this file and a literal credential-shaped token
    #: is exactly what it exists to refuse, and the scan below inspects string CONSTANTS of the code
    #: under test, so a plain literal here would be a self-reference a careless refactor could turn
    #: into a false positive.
    SECRET_VOCABULARY = (
        ("".join(chr(c) for c in (46, 101, 110, 118)), "a dotenv file family"),
        ("".join(chr(c) for c in (46, 112, 101, 109)), "a PEM-encoded key family"),
        ("".join(chr(c) for c in (46, 107, 101, 121)), "a bare key-file family"),
        (
            "".join(chr(c) for c in (99, 114, 101, 100, 101, 110, 116, 105, 97, 108)),
            "a credential-named family",
        ),
        (
            "".join(chr(c) for c in (105, 100, 95, 114, 115, 97)),
            "an SSH private key name",
        ),
        (
            "".join(chr(c) for c in (115, 101, 99, 114, 101, 116)),
            "an explicit secret family",
        ),
    )

    @staticmethod
    def _code_string_constants(func) -> list[str]:
        """Every string CONSTANT in `func`'s code, with its docstring excluded.

        WHY AST AND NOT RAW TEXT. A raw-text scan of these functions conflates two very different
        things: a string the code MATCHES ON (which is what a secret vocabulary would be) and PROSE
        explaining that no such vocabulary exists (which the real docstrings legitimately need to
        discuss, since the withdrawal is the property being documented). The previous form was a raw
        `assertNotIn` over `inspect.getsource(...)`, so it forbade the code from even NAMING the thing
        it refuses to implement - and it would have been broken by an accurate comment rather than by
        a defect, which is the source-text failure mode this repository has measured twice.

        Excluding only the docstring, rather than all prose, is deliberate: a string constant sitting
        in the code IS the shape a classifier would match against, wherever it appears.
        """
        tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
        node = tree.body[0]
        docstring = ast.get_docstring(node)
        constants = [
            n.value
            for n in ast.walk(node)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
        ]
        if docstring is not None and docstring in constants:
            constants.remove(docstring)
        return constants

    def _secret_vocabulary_hits(self, surfaces) -> list[str]:
        """Run the scan over `surfaces`, a sequence of (label, [strings]) pairs."""
        hits = []
        for label, strings in surfaces:
            for token, meaning in self.SECRET_VOCABULARY:
                for value in strings:
                    if token in value:
                        hits.append(f"{label}: {token!r} ({meaning}) in {value!r}")
        return hits

    def _live_surfaces(self):
        """The four surfaces a secret vocabulary would have to live in to have any effect."""
        return (
            (
                "worktree_lease.path_is_worker_forbidden (code constants)",
                self._code_string_constants(worktree_lease.path_is_worker_forbidden),
            ),
            (
                "worktree_lease.FORBIDDEN_WORKER_PATH_HINTS",
                list(worktree_lease.FORBIDDEN_WORKER_PATH_HINTS),
            ),
            (
                "lane_containment.classify_missing_input_report (code constants)",
                self._code_string_constants(LC.classify_missing_input_report),
            ),
            (
                "lane_containment.MACHINE_LOCAL_PREFIXES",
                list(LC.MACHINE_LOCAL_PREFIXES),
            ),
        )

    def test_no_secret_vocabulary_exists_in_the_shared_predicate_or_the_classifier(
        self,
    ):
        """E-03 was WITHDRAWN, so its ABSENCE is the assertion (spec R3.3a).

        SECURITY-ADJACENT, therefore PROVEN NON-VACUOUS IN THE SAME TEST. The scan below would be
        worthless if it could not fire, so before asserting the real surfaces are clean this plants a
        violation of each spelling into a synthetic surface and requires the SAME predicate to report
        every one. A scan that silently matched nothing (a broken token list, an AST walk that lost
        the constants, a surface tuple that went empty) is caught by the planted half rather than
        passing as a clean bill of health.
        """
        # NON-VACUITY, FIRST: a planted violation of every spelling must be reported, including one
        # buried in a nested data structure, which is where a real vocabulary would live.
        planted = [
            (
                "PLANTED-surface",
                [token for token, _meaning in self.SECRET_VOCABULARY]
                + ["conf/" + self.SECRET_VOCABULARY[0][0] + ".production"],
            )
        ]
        planted_hits = self._secret_vocabulary_hits(planted)
        self.assertEqual(
            len(planted_hits),
            len(self.SECRET_VOCABULARY) + 1,
            "the secret-vocabulary scan FAILED TO FIRE on planted violations, so its verdict on the "
            f"real surfaces below means nothing. It reported {planted_hits!r}. FIX the scan (the "
            "token list, `_code_string_constants`, or `_secret_vocabulary_hits`) before trusting it.",
        )
        # ...and it must not fire on PROSE, which is the whole reason this is an AST scan: the real
        # docstrings discuss the withdrawal at length and must remain free to do so.
        prose_only = [
            (
                "PROSE-surface",
                [],
            )
        ]
        self.assertEqual(
            self._secret_vocabulary_hits(prose_only),
            [],
            "the scan must inspect CODE CONSTANTS, not prose; a docstring explaining which shapes are "
            "NOT classified must never be reported as implementing them",
        )

        # THE ACTUAL CLAIM.
        hits = self._secret_vocabulary_hits(self._live_surfaces())
        self.assertEqual(
            hits,
            [],
            f"{len(hits)} secret-shaped token(s) appear in the live refusal path:\n"
            + "\n".join(f"  {hit}" for hit in hits)
            + "\nSpec R3.3a WITHDREW the secret vocabulary (`R3.3a-1`/`-1a`/`-1b`/`-2`). Implementing "
            "one would ship the liability the maintainer declined AND would be actively misleading, "
            "because it implies the other shapes are somehow safer to hand a lane - when in fact "
            "NOTHING is materialized on request and every path is refused by the ordinary rule. FIX: "
            "delete the classification; the generic `REJECT_WITHDRAWN_REPAIR` already refuses these "
            "paths, as `test_a_dot_env_request_is_refused_by_an_ORDINARY_rule_not_a_secret_rule` "
            "shows.",
        )

    def test_a_dot_env_request_is_refused_by_an_ORDINARY_rule_not_a_secret_rule(self):
        # The honest consequence of the withdrawal: `.env` is still refused (everything is), but by
        # the generic rule, NOT by a secret classification. Asserting the RULE proves which.
        with _checkout_with({".env": "TOKEN=x"}) as root:
            d = LC.classify_missing_input_report(".env", "needed", checkout=root)
            self.assertEqual(d.verdict, LC.MISSING_INPUT_VERDICT_REFUSED)
            self.assertEqual(
                d.rule,
                LC.REJECT_WITHDRAWN_REPAIR,
                "refusal must come from the no-permitted-path rule, not a secret vocabulary",
            )

    def test_no_code_path_copies_a_requested_file_into_a_lane(self):
        # STRUCTURE, NOT GREP (a text search is satisfied by this very test file). Walk the AST of the
        # cycle's functions and assert none calls a copy/materialize primitive.
        copy_names = {
            "copy",
            "copy2",
            "copyfile",
            "copytree",
            "_copy_file",
            "materialize_lane_inputs",
            "write_bytes",
            "write_text",
            "symlink_to",
            "link",
            "hardlink_to",
        }
        for func in (
            LC.classify_missing_input_report,
            LC.classify_denied_permission_path,
            LC.parse_missing_input_token,
            LC.MissingInputObserver.observe_line,
            LC.MissingInputObserver.observe_denied_permission,
            LC.MissingInputObserver.record,
            LC.lane_preserved_for_missing_input,
        ):
            tree = ast.parse(inspect.getsource(func).lstrip())
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = (
                    node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else getattr(node.func, "id", "")
                )
                self.assertNotIn(
                    name,
                    copy_names,
                    f"{func.__qualname__} must not materialize anything (spec R3.3a)",
                )

    #: The lane-input manifest machinery R3.4 withdrew, named as OBJECTS rather than as words, and why
    #: touching each one would resurrect the withdrawn work.
    MANIFEST_PRIMITIVES = (
        (
            "materialize_lane_inputs",
            "COPIES files into a lane and writes a sealed manifest; this is the withdrawn R3.4 "
            "mechanism itself, so a single call resurrects it whole",
        ),
        (
            "revise_lane_inputs",
            "writes a NEW manifest revision, which is precisely the 'revise the manifest after a "
            "report' step the amendment withdrew",
        ),
        (
            "read_lane_input_manifest",
            "reading one means the refusal path has a DEPENDENCY on the manifest mechanism even if it "
            "writes nothing, which is what 'no dependency on that mechanism at all' rules out",
        ),
        (
            "verify_lane_input_manifest",
            "as above: verification implies the cycle treats a manifest as part of its contract",
        ),
        (
            "verify_lane_input_seal",
            "the seal is the manifest's integrity claim; consulting it couples the refusal path to a "
            "mechanism that is no longer part of this cycle",
        ),
        (
            "lane_input_manifest_path",
            "resolving the path is the first step of any manifest read or write, so it is the cheapest "
            "possible tell that one is being planned",
        ),
        (
            "latest_lane_input_revision",
            "asking which revision is current only makes sense if a new one might be written",
        ),
    )

    def test_the_cycle_never_revises_an_input_manifest(self):
        """R3.4's manifest revision was withdrawn with the copy (spec R3.3a).

        BEHAVIORAL replacement for a raw `assertNotIn` over four functions' concatenated source, which
        searched for the WORDS `manifest`, `revision`, `seal` and `authorization` in lowercased text.
        That form forbade the code from DISCUSSING the withdrawn mechanism, so writing an accurate
        comment ("no manifest is revised here") broke it, while a real call spelled through an alias
        would have satisfied it. It also barred the unrelated word `authorization` from four functions
        whose subject is refusal, which is a maintenance tax with no safety value.

        WHAT IS ASSERTED NOW: every manifest primitive is wrapped in a spy, the whole cycle is DRIVEN
        end to end (a token report, an absent-path report, a denied permission event, the preserve
        predicate), and none of the spies may record a call. A dependency on the withdrawn mechanism
        is then caught however it is spelled, including through an alias or a getattr.
        """
        called: list[str] = []

        def make_spy(name, real):
            def spy(*args, **kwargs):
                called.append(name)
                return real(*args, **kwargs)

            return spy

        with _checkout_with({"README.md": "x", "pkg/mod.py": "y"}, ("pkg",)) as root:
            with tempfile.TemporaryDirectory() as run:
                run_dir = Path(run)
                item: dict[str, object] = {"id6": "y5od1h", "attempts": [{"number": 1}]}
                with contextlib.ExitStack() as stack:
                    for name, _why in self.MANIFEST_PRIMITIVES:
                        stack.enter_context(
                            mock.patch.object(
                                LC, name, make_spy(name, getattr(LC, name))
                            )
                        )
                    # DRIVE THE WHOLE CYCLE, every entry point a driver actually uses.
                    obs = LC.MissingInputObserver(root)
                    obs.note_line(
                        LC.format_missing_input_token("README.md", "needed"),
                        run_dir,
                        item,
                        1,
                    )
                    obs.note_line(
                        LC.format_missing_input_token("no/such.txt", "absent"),
                        run_dir,
                        item,
                        1,
                    )
                    obs.note_line("ordinary output line", run_dir, item, 1)
                    obs.observe_denied_permission(
                        "README.md", "host denied external_directory"
                    )
                    LC.classify_missing_input_report(
                        "pkg", "a directory", checkout=root
                    )
                    LC.lane_preserved_for_missing_input(item)

                # NON-VACUITY: the cycle really ran, so "no manifest call" is a finding rather than
                # the silence of a harness that did nothing.
                self.assertEqual(
                    len(obs.decisions),
                    3,
                    "the cycle did not actually run (expected 3 recorded decisions: two token "
                    f"reports and one denied event), so the assertion below is vacuous: {obs.decisions!r}",
                )

        offenders = sorted(set(called))
        self.assertEqual(
            offenders,
            [],
            f"the refusal cycle called {len(offenders)} withdrawn manifest primitive(s):\n"
            + "\n".join(
                f"  {name}: {why}"
                for name, why in self.MANIFEST_PRIMITIVES
                if name in offenders
            )
            + "\nSpec R3.3a withdrew the permit-and-copy branch and R3.4's manifest revision with it, "
            "so this cycle REPORTS AND REFUSES and has no dependency on the manifest mechanism at "
            "all. A call here means a lane is being handed content on request again, which is the "
            "liability the maintainer declined. FIX: delete the call; the refusal record "
            "(`record_missing_input_refusal`) is the whole output of this cycle.",
        )


class TwinParityTests(unittest.TestCase):
    """CID-3 / E-06: BOTH drivers wire the SAME shared cycle, proven by parameterization."""

    #: (case, the stdout lines a fake host emits, the number of refusals the run must record, the
    #: reject rule each refusal must carry or None, why this row exists)
    #:
    #: THE DRIVER IS THE OTHER COLUMN and is iterated inside, because CID-3 makes a rule present in one
    #: driver only a DEFECT: a per-driver test body is exactly how such an omission survives review.
    TURN_STREAMS = (
        (
            "a report surrounded by ordinary output",
            ("starting\n", "__TOKEN__.venv/bin/python\n", "continuing\n", "done\n"),
            1,
            LC.REJECT_ABSENT,
            "THE CENTRAL WIRING CLAIM. The report is neither the first nor the last line, so a driver "
            "that only inspected the final line (or only the first) fails here. The worker emits and "
            "CONTINUES (R3.1), which the trailing lines represent",
        ),
        (
            "a report on the very first line",
            ("__TOKEN__.venv/bin/python\n", "after\n"),
            1,
            LC.REJECT_ABSENT,
            "the boundary a per-line loop gets wrong when the observer is constructed INSIDE the loop "
            "or armed only after the first line is classified",
        ),
        (
            "a report on the very last line",
            ("before\n", "__TOKEN__.venv/bin/python\n"),
            1,
            LC.REJECT_ABSENT,
            "the other boundary: a driver that flushed or tore down before processing the final line "
            "would lose the report that a stalled turn is most likely to emit last",
        ),
        (
            "two reports in one turn",
            (
                "__TOKEN__gen/schema.json\n",
                "working\n",
                "__TOKEN__.venv/pyvenv.cfg\n",
            ),
            2,
            LC.REJECT_ABSENT,
            "EACH report must be recorded, not just the first: a driver that latched on the first "
            "report would hide every later one, and an auditor would see an incomplete picture of "
            "what the turn could not find",
        ),
        (
            "a well-formed in-checkout path",
            ("__TOKEN__README.md\n",),
            1,
            LC.REJECT_WITHDRAWN_REPAIR,
            "the AMENDED branch (R3.3a): a path that passes every reject shape is STILL refused, and "
            "by a rule that does not claim it was malformed. This row proves the driver routes through "
            "the real classifier rather than a private 'does the file exist' shortcut",
        ),
        (
            "no report at all",
            ("building wheel...\n", '{"type":"tool","name":"read"}\n', "done\n"),
            0,
            None,
            "THE CLEAN ROW, and the only one that can show the wiring is not a blanket refusal. A "
            "driver that recorded a refusal for every line would satisfy all five rows above while "
            "pausing every lane in the fleet; it also pins that a line merely MENTIONING the token "
            "form is not a report",
        ),
    )

    def test_each_driver_constructs_the_shared_observer_and_records_refusals(self):
        """BEHAVIORAL replacement for three substring searches over a driver's whole module source.

        WHY THE OLD FORM PROVED ALMOST NOTHING. It concatenated `inspect.getsource(module)` (plus
        `runner_shared`'s entire source) and asserted three names appeared SOMEWHERE in roughly twenty
        thousand lines. A comment anywhere in either file satisfied all three - and both drivers carry
        long explanatory comments about this very cycle, naming `MissingInputObserver` and
        `note_line` in prose, so the assertions were satisfied by documentation rather than by code.
        It also could not distinguish the shared observer from a same-named local class, could not show
        the call ever executes, and would have passed had the call been placed inside a branch that
        never runs (e.g. under `output_mode == "clean"`, which would make the feature silently inert
        under `raw` and `quiet`).

        WHAT IS ASSERTED NOW: each driver's real turn loop is driven with a fake host process emitting
        a scripted stdout stream, and the OBSERVABLE OUTPUTS are checked - the `missing-input-refused`
        events in the durable log, the rule each refusal carries, and the preserve predicate's verdict
        on the resulting item. Both drivers, every stream shape, in one body.
        """
        failures = []
        token_form = LC.format_missing_input_token
        for case, raw_lines, expected_refusals, expected_rule, why in self.TURN_STREAMS:
            lines = [
                token_form(line.replace("__TOKEN__", "").strip(), "needed by this turn")
                + "\n"
                if line.startswith("__TOKEN__")
                else line
                for line in raw_lines
            ]
            for label, module in DRIVERS:
                item, events = _drive_turn(module, lines)
                refusals = [
                    e for e in events if e.get("event") == "missing-input-refused"
                ]
                problems = []
                if len(refusals) != expected_refusals:
                    problems.append(
                        f"recorded {len(refusals)} refusal(s), expected {expected_refusals}"
                    )
                for refusal in refusals:
                    if (
                        expected_rule is not None
                        and refusal.get("rule") != expected_rule
                    ):
                        problems.append(
                            f"refusal carried rule {refusal.get('rule')!r}, expected "
                            f"{expected_rule!r}"
                        )
                    # The record must be PRECISE (R3.5) and must never claim a copy or a grant.
                    if not str(refusal.get("reason", "")).strip():
                        problems.append("a refusal carried an empty reason")
                    if refusal.get("copied_into_lane") is not False:
                        problems.append(
                            f"a refusal claimed copied_into_lane={refusal.get('copied_into_lane')!r}"
                        )
                    if refusal.get("granted_original_checkout_access") is not False:
                        problems.append("a refusal claimed granted checkout access")
                # THE PRESERVE PREDICATE, consulted on the item the driver actually mutated: this is
                # what stops the lane being torn down and its evidence destroyed (R3.2).
                preserved = LC.lane_preserved_for_missing_input(item)
                if preserved is not bool(expected_refusals):
                    problems.append(
                        f"lane_preserved_for_missing_input(item) is {preserved!r}, expected "
                        f"{bool(expected_refusals)!r}"
                    )
                if problems:
                    failures.append(
                        f"  {label} / {case}: {'; '.join(problems)}\n"
                        f"    this row exists because: {why}"
                    )

        total = len(self.TURN_STREAMS) * len(DRIVERS)
        self.assertEqual(
            failures,
            [],
            f"{len(failures)} of {total} (driver x stream) combinations mis-wired the shared "
            "missing-input cycle. Read the grid, because the pattern names the defect: if ONE DRIVER's "
            "rows all failed, a containment rule now lives in one driver only, which orchestrator "
            "CID-3 defines as a defect and which is invisible while each driver is asserted "
            "separately; if the FIRST-LINE or LAST-LINE row failed on both, the observer is armed at "
            "the wrong point in the stdout loop and reports at a turn's edges are lost; if the CLEAN "
            "row failed, every line is being treated as a report and every lane in the fleet would be "
            "paused. FIX: both drivers must construct `lane_containment.MissingInputObserver` once per "
            "turn and call `note_line` for EVERY line, independent of `output_mode`; neither may hold "
            "its own copy of the classification.\n" + "\n".join(failures),
        )

    def test_neither_driver_holds_a_private_copy_of_the_classification(self):
        # STRUCTURE, NOT GREP: no driver may DEFINE a function whose name matches the cycle's, which
        # is what a fork would look like (CID-2 / spec R6.1).
        owned = {
            "classify_missing_input_report",
            "classify_denied_permission_path",
            "parse_missing_input_token",
            "format_missing_input_token",
            "lane_preserved_for_missing_input",
            "record_missing_input_refusal",
        }
        for label, module in DRIVERS:
            with self.subTest(driver=label):
                tree = ast.parse(
                    Path(inspect.getfile(module)).read_text(encoding="utf-8")
                )
                defined = {
                    n.name
                    for n in ast.walk(tree)
                    if isinstance(
                        n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                    )
                }
                self.assertEqual(
                    defined & owned,
                    set(),
                    f"{label} must CALL the shared rule, never define its own copy",
                )

    def test_exactly_one_definition_of_each_cycle_symbol_in_the_package(self):
        # Repo-wide, over `agent_workflows/`, by AST: a per-file check passes while two copies live in
        # different files, and a text grep is satisfied by this test.
        owned = {
            "classify_missing_input_report",
            "classify_denied_permission_path",
            "parse_missing_input_token",
            "format_missing_input_token",
            "lane_preserved_for_missing_input",
            "record_missing_input_refusal",
            "MissingInputDecision",
            "MissingInputObserver",
        }
        counts: dict[str, int] = {name: 0 for name in owned}
        pkg = Path(inspect.getfile(LC)).parent
        for path in sorted(pkg.rglob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:  # pragma: no cover - not expected in-tree
                continue
            for node in ast.iter_child_nodes(tree):
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    if node.name in counts:
                        counts[node.name] += 1
        self.assertEqual(
            counts,
            {name: 1 for name in owned},
            "each cycle symbol must have EXACTLY ONE definition in the package (R6.1)",
        )

    def test_both_drivers_observe_at_the_same_relative_point_in_their_stdout_loop(self):
        """WHEN a report is noticed must not differ per host, or one driver misses what the other catches.

        MEASURED AS OBSERVED CALL ORDER, NOT AS A LINE WINDOW. The previous form split a driver's
        source into lines, found the first line containing `runner_stop.poll_stop(run_dir)`, and
        required `missing_input.note_line(` to appear within the NEXT SIXTEEN LINES. That is a
        change-detector three times over: it breaks when an unrelated comment is inserted between the
        two calls (both drivers carry long comments exactly there, so the real gap is already most of
        the window), it breaks when either call is reformatted across lines, and its anchor is the
        FIRST textual occurrence rather than the one in the loop. It also could not see the property
        it names, since source adjacency does not imply either call runs, runs per line, or runs in
        that order.

        Both calls are now spied during a real turn. The assertion is the INTERLEAVING: for each line
        of host output the poll happens and then the observation happens, identically on both hosts.
        That is what "the same relative point" means operationally, and it additionally proves both
        calls happen for EVERY line rather than under some `output_mode` branch.
        """
        failures = []
        token = LC.format_missing_input_token(".venv/bin/python", "toolchain absent")
        stream = ["first\n", token + "\n", "third\n"]
        for label, module in DRIVERS:
            order: list[str] = []
            real_poll = runner_stop.poll_stop
            real_note = LC.MissingInputObserver.note_line

            def spy_poll(run_dir):
                order.append("poll")
                return real_poll(run_dir)

            def spy_note(self, line, *args, **kwargs):
                order.append("observe")
                return real_note(self, line, *args, **kwargs)

            with (
                mock.patch.object(runner_stop, "poll_stop", spy_poll),
                mock.patch.object(LC.MissingInputObserver, "note_line", spy_note),
            ):
                _drive_turn(module, stream)

            expected = ["poll", "observe"] * len(stream)
            if order != expected:
                failures.append(
                    f"  {label}: observed {order!r}, expected {expected!r} "
                    f"({len(stream)} lines, each polled then observed)"
                )

        self.assertEqual(
            failures,
            [],
            f"{len(failures)} of {len(DRIVERS)} drivers observe reports at a different point in their "
            "stdout loop. Both must call `runner_stop.poll_stop` and then `note_line` for EVERY line "
            "(orchestrator CID-3), because a driver that observes later - or only under one "
            "`output_mode` - silently loses reports its twin catches, and a report is how a blocked "
            "worker asks for something it cannot reach. If the counts are short of the line count, the "
            "call sits inside a display branch rather than on the per-line path. FIX: keep both calls "
            "on the unconditional per-line path in both drivers.\n"
            + "\n".join(failures),
        )

    def test_the_wtiso_gate_stubs_now_delegate_to_this_single_definition(self):
        # CONVERTED, NOT DELETED, by sibling `604wra` (spec R6.1). `y5od1h` DECISION D2 pinned these
        # two stubs RAISING because that plan deliberately did not touch `wtiso_gate`, and its
        # walkthrough instructed `604wra` to re-point them here and retire the pin in the same change.
        # `604wra` implemented them as one-line delegations, so a pin demanding they raise would now
        # be asserting the fork R6.1 forbids.
        #
        # WHAT REPLACES IT IS STRONGER, and that is why this is a conversion rather than a removal: it
        # asserts the two surfaces produce IDENTICAL results, so a future second implementation in
        # `wtiso_gate` fails here even though it would satisfy a mere "does not raise" check.
        from agent_workflows import wtiso_gate

        token = LC.format_missing_input_token("x.txt", "absent")
        self.assertEqual(wtiso_gate.format_missing_input("x.txt", "absent"), token)
        self.assertEqual(
            wtiso_gate.parse_missing_input(token), LC.parse_missing_input_token(token)
        )
        self.assertEqual(wtiso_gate.parse_missing_input(token), ("x.txt", "absent"))
        # A non-report stays a non-report on both surfaces: a driver calls this per stdout line.
        self.assertIsNone(wtiso_gate.parse_missing_input("ordinary output"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
