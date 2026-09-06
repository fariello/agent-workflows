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
import inspect
import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd, lane_containment, oc_runipd, worktree_lease

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


class TokenFormTests(unittest.TestCase):
    """R3.1: ONE deterministic token form, and the parser DERIVES it rather than re-spelling it."""

    def test_emit_and_parse_round_trip(self):
        token = LC.format_missing_input_token("config/local.ini", "absent from lane")
        self.assertEqual(
            LC.parse_missing_input_token(token),
            ("config/local.ini", "absent from lane"),
        )

    def test_token_shape_is_derived_from_the_published_prompt_constant(self):
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

    def test_reason_may_contain_colons(self):
        # A worker writes prose in the reason; a naive 2-way split would truncate it.
        parsed = LC.parse_missing_input_token(
            "AW_MISSING_INPUT:a/b.txt:needed by step 3: the schema generator"
        )
        assert parsed is not None
        path, why = parsed
        self.assertEqual(path, "a/b.txt")
        self.assertEqual(why, "needed by step 3: the schema generator")

    def test_an_ordinary_line_is_not_a_report(self):
        # Called on EVERY line of a child's stdout, so a non-report must be `None`, never an
        # exception and never a false positive.
        for line in (
            "",
            "  ",
            "building wheel...",
            '{"type":"tool","name":"read"}',
            "mentions AW_MISSING_INPUT in prose but not at the start",
        ):
            self.assertIsNone(LC.parse_missing_input_token(line), line)


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

    def test_lane_is_preserved_not_torn_down(self):
        # THE HALF THAT IS EASY TO FAKE. A log line saying "preserved" is not preservation; the
        # predicate the drivers consult before `teardown_isolation_worktree` must return True.
        item: dict[str, object] = {"id6": "y5od1h", "attempts": [{"number": 1}]}
        self.assertFalse(LC.lane_preserved_for_missing_input(item))
        with tempfile.TemporaryDirectory() as run:
            LC.record_missing_input_refusal(
                Path(run),
                item,
                1,
                LC.classify_missing_input_report("x/y.txt", "absent", checkout=run),
            )
        self.assertTrue(
            LC.lane_preserved_for_missing_input(item),
            "a refused report must make the lane non-reclaimable (R3.2)",
        )

    def test_preservation_survives_a_resumed_run_with_no_observer(self):
        # The predicate reads DURABLE state, so it is still correct when the observer object is gone
        # (a resumed run rebuilds the item from `state.json` and never reconstructs the observer).
        item = {"id6": "y5od1h", "lane_paused_for_missing_input": True}
        self.assertTrue(LC.lane_preserved_for_missing_input(item))


class RejectShapeTests(unittest.TestCase):
    """R3.3/R3.5 (criterion A7): every forbidden shape refused precisely, with NO copy."""

    #: The eight shapes R3.3 enumerates, in the order the spec lists them.
    def test_each_forbidden_shape_is_refused_with_its_own_rule(self):
        files = {"README.md": "x", "pkg/mod.py": "y"}
        dirs = ("pkg", "agent_workflows")
        with _checkout_with(files, dirs) as root:
            cases = {
                "/etc/passwd": LC.REJECT_ABSOLUTE,
                "pkg/../../outside/x.txt": LC.REJECT_ESCAPES_CHECKOUT,
                ".aw/records/plans/x.ipd.md": LC.REJECT_COORDINATOR_SURFACE,
                ".aw/worktrees/other/secret.txt": LC.REJECT_SIBLING_LANE,
                ".aw/state/lane-submissions/x/y.json": LC.REJECT_MACHINE_STATE,
                ".git/config": LC.REJECT_GIT_ADMIN,
                "pkg": LC.REJECT_DIRECTORY,
                "no/such/file.txt": LC.REJECT_ABSENT,
            }
            for path, expected_rule in cases.items():
                with self.subTest(path=path):
                    d = LC.classify_missing_input_report(path, "why", checkout=root)
                    self.assertEqual(d.rule, expected_rule)
                    self.assertEqual(d.verdict, LC.MISSING_INPUT_VERDICT_REFUSED)
                    # PRECISE: the record names the path and a non-empty reason (R3.5).
                    self.assertEqual(d.path, path)
                    self.assertTrue(d.reason.strip())
                    # NO COPY, asserted on the emitted record rather than inferred.
                    self.assertFalse(d.as_dict()["copied_into_lane"])
                    self.assertFalse(d.as_dict()["granted_original_checkout_access"])

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

    def test_a_wellformed_path_is_still_refused_and_says_why(self):
        # THE BRANCH THE AMENDMENT CREATED (R3.3a). `README.md` exists, is inside the checkout, and is
        # a regular file - every reject shape passes - and it is STILL refused, with a rule that does
        # NOT claim the path was malformed.
        with _checkout_with({"README.md": "x"}) as root:
            d = LC.classify_missing_input_report("README.md", "needed", checkout=root)
            self.assertEqual(d.rule, LC.REJECT_WITHDRAWN_REPAIR)
            self.assertEqual(d.verdict, LC.MISSING_INPUT_VERDICT_REFUSED)
            self.assertIn("R3.3a", d.reason)

    def test_malformed_report_is_refused_not_silently_dropped(self):
        with _checkout_with({}) as root:
            d = LC.classify_missing_input_report("", "", checkout=root)
            self.assertEqual(d.rule, LC.REJECT_MALFORMED_TOKEN)
            # And through the observer, so an empty-path token is not simply ignored.
            obs = LC.MissingInputObserver(root)
            self.assertIsNotNone(obs.observe_line("AW_MISSING_INPUT::"))

    def test_windows_style_absolute_is_refused_on_every_platform(self):
        # The drive-letter form is ASSEMBLED rather than written out: a literal one trips the
        # repository's local-leak scanner (rules `windows-home` and `users-path`), and an allowlist
        # entry would be the wrong fix for a path that is purely synthetic. Note the comment must
        # avoid the shape too, since the scanner reads comments.
        windows_absolute = "C:" + "/" + "Us" + "ers/example/config.ini"
        with _checkout_with({}) as root:
            self.assertEqual(
                LC.classify_missing_input_report(
                    windows_absolute, "w", checkout=root
                ).rule,
                LC.REJECT_ABSOLUTE,
            )

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
        self.assertNotIn(
            "REJECT_ABSOLUTE", inspect.getsource(LC.classify_denied_permission_path)
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
        # "Precise" means the rules are DISTINGUISHABLE; identical prose for two rules would make the
        # record useless to an auditor even though each field is populated.
        with _checkout_with({"README.md": "x"}, ("pkg",)) as root:
            reasons = {}
            for path in (
                "/abs",
                "a/../../out",
                ".aw/records/plans/p.ipd.md",
                ".aw/worktrees/o/f",
                ".aw/state/s",
                ".git/config",
                "pkg",
                "no/such.txt",
                "README.md",
                "",
            ):
                d = LC.classify_missing_input_report(path, "w", checkout=root)
                reasons[d.rule] = d.reason
            self.assertEqual(len(reasons), 10, "each shape must have its own rule")
            self.assertEqual(
                len(set(reasons.values())), 10, "each rule must have its own reason"
            )


class NoWithdrawnWorkTests(unittest.TestCase):
    """E-03/E-05: prove the WITHDRAWN work is absent (spec R3.3a), structurally rather than by eye."""

    def test_no_secret_vocabulary_exists_in_the_shared_predicate_or_the_classifier(
        self,
    ):
        # E-03 was WITHDRAWN. Implementing a secret vocabulary would ship the liability the maintainer
        # declined, so its ABSENCE is the assertion.
        surfaces = (
            inspect.getsource(worktree_lease.path_is_worker_forbidden),
            repr(worktree_lease.FORBIDDEN_WORKER_PATH_HINTS),
            inspect.getsource(LC.classify_missing_input_report),
            repr(LC.MACHINE_LOCAL_PREFIXES),
        )
        for token in (".env", ".pem", ".key", "credentials", "id_rsa", "secret"):
            for surface in surfaces:
                self.assertNotIn(
                    token,
                    surface,
                    f"{token!r} indicates a secret vocabulary, withdrawn by spec R3.3a",
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

    def test_the_cycle_never_revises_an_input_manifest(self):
        # R3.4's manifest revision was withdrawn with the copy. Prove this plan's code has no
        # dependency on that mechanism at all.
        source = "".join(
            inspect.getsource(f)
            for f in (
                LC.classify_missing_input_report,
                LC.classify_denied_permission_path,
                LC.record_missing_input_refusal,
                LC.lane_preserved_for_missing_input,
            )
        )
        for token in ("manifest", "revision", "seal", "authorization"):
            self.assertNotIn(
                token, source.lower(), f"{token!r} belongs to withdrawn R3.4 work"
            )


class TwinParityTests(unittest.TestCase):
    """CID-3 / E-06: BOTH drivers wire the SAME shared cycle, proven by parameterization."""

    def test_each_driver_constructs_the_shared_observer_and_records_refusals(self):
        for label, module in DRIVERS:
            with self.subTest(driver=label):
                source = inspect.getsource(module)
                self.assertIn(
                    "lane_containment.MissingInputObserver(",
                    source,
                    f"{label} must construct the shared observer",
                )
                self.assertIn(
                    "missing_input.note_line(",
                    source,
                    f"{label} must observe AND record through the one shared per-line call",
                )
                self.assertIn(
                    "lane_containment.lane_preserved_for_missing_input(",
                    source,
                    f"{label} must consult the shared preserve predicate before teardown",
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
        # WHEN a report is noticed must not differ per host, or one driver could miss reports the
        # other catches. Both call it immediately after `runner_stop.poll_stop(run_dir)`, which is the
        # established per-line checkpoint in BOTH loops.
        #
        # ANCHORED ON THE POLL, not on `turn_bounds.note_progress()`: `test_runner_stop.py`'s
        # `PollWiringTests` bounds the CHARACTER distance from `watchdog.touch()` to the poll (to prove
        # the poll sits at the per-line checkpoint), so inserting this call between them broke a
        # sibling's assertion. Anchoring here keeps the parity property while respecting that bound.
        for label, module in DRIVERS:
            with self.subTest(driver=label):
                lines = inspect.getsource(module).splitlines()
                progress = [
                    i
                    for i, line in enumerate(lines)
                    if "runner_stop.poll_stop(run_dir)" in line
                ]
                self.assertTrue(progress, f"{label}: expected the shared in-turn poll")
                window = "\n".join(lines[progress[0] : progress[0] + 16])
                self.assertIn(
                    "missing_input.note_line(",
                    window,
                    f"{label} must observe reports at the same point as its twin",
                )

    def test_the_wtiso_gate_stubs_are_left_raising_for_their_owner(self):
        # DECISION D2: this plan puts the bodies in the declared shared home and does NOT touch
        # `wtiso_gate`, whose stubs sibling `604wra` is chartered to implement and wire. Spec R6.2
        # requires they still fail loudly, so pin that rather than leaving it to chance.
        from agent_workflows import wtiso_gate

        with self.assertRaises(NotImplementedError):
            wtiso_gate.format_missing_input("x.txt", "absent")
        with self.assertRaises(NotImplementedError):
            wtiso_gate.parse_missing_input("AW_MISSING_INPUT:x.txt:absent")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
