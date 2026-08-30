"""lanetruth Order 03 (8guhs0): the runners must consume the SHARED `Item-Dependencies` predicate.

THE DEFECT THIS PINS. Both drivers carried a private `_DEPS_RE` matching a LEGACY
`Dependencies:`/`Depends-on:` field that no plan in the tree uses, so the canonical
`- Item-Dependencies:` statement was invisible: `_read_deps` returned `[]` for a valid three-edge
statement while `ipd_schema.parse_item_dependencies` returned three typed records, every frozen queue
item carried `dependencies: []`, and ordering fell back to Set/Order, which spec 25kzda calls only a
tiebreaker.

WHAT IS ASSERTED HERE, and the division of labor that must not be "consolidated" later:
  * the typed-edge round trip through BOTH drivers' record-building path (contrasted with the
    measured pre-fix `[]`), with QUALIFIERS PRESERVED rather than flattened to bare id6 strings;
  * each edge kind's runtime satisfaction rule (spec 2.9), including wait-not-start;
  * fail-closed preflight for malformed / dangling / ambiguous / cyclic / self-edge / `unresolved`
    statements, delegated ENTIRELY to `check_engine.evaluate_ipd_dependencies`;
  * NO runner-local missing-statement rule (8guhs0 OQ-02: that decision belongs to the shared
    evaluator plus the cutover marker);
  * declared edges authoritative for ordering, with Set/Order demoted to a tiebreaker, and the
    `dependency-blocked` cascade;
  * an ANTI-DIVERGENCE guard: neither driver may define a dependency regex or a private dependency
    parser, and the two must share ONE implementation.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd, check_engine, ipd_schema, oc_runipd
from tests.support import REPO_ROOT

_DRIVERS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))
_DRIVER_SOURCES = (
    ("oc_runipd", REPO_ROOT / "agent_workflows" / "oc_runipd.py"),
    ("agy_runipd", REPO_ROOT / "agent_workflows" / "agy_runipd.py"),
)

# One valid statement exercising ALL THREE edge kinds at once.
_THREE_EDGE_VALUE = "executed:a1b2c3, exists:spec:d4e5f6, state:backlog:done:g7h8j9"


def _code_only(text: str) -> str:
    """``text`` with `#` comments and docstrings/string literals removed, via the real tokenizer.

    The anti-divergence guards assert things about CODE, not about prose. A comment or docstring that
    NAMES the deleted construct in order to warn against it must not trip the guard, or the honest
    documentation of a fix would be indistinguishable from the defect.
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
    deps: str | None = _THREE_EDGE_VALUE,
    setid: str = "demo",
    order: int = 1,
    status: str = "approved",
    date: str = "2026-08-29",
) -> str:
    """A minimal plan whose metadata block the structural reader will accept."""
    lines = [
        f"# IPD: {id6}",
        "",
        f"- Date: {date}",
        "- Kind: child",
        f"- Status: {status}",
        f"- Set: {setid} (the {setid} set)",
        f"- Order: {order}",
        f"- Id: {id6}",
    ]
    if deps is not None:
        lines.append(f"- Item-Dependencies: {deps}")
    lines += ["", "## Goal", "", "Demo.", ""]
    return "\n".join(lines)


def _write_plan(pending: Path, id6: str, order: int = 1, **kw) -> Path:
    path = pending / f"20260829-{kw.get('setid', 'demo')}-{order:02d}-{id6}-demo.ipd.md"
    path.write_text(_plan_text(id6, order=order, **kw), encoding="utf-8")
    return path


class TypedEdgeRoundTripTests(unittest.TestCase):
    """E-01: the canonical field is READ, and its qualifiers survive."""

    def test_both_drivers_yield_three_typed_edges(self):
        text = _plan_text("aaaaaa")
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                edges, err = mod._read_item_dependencies(text)
                self.assertIsNone(err)
                self.assertEqual(
                    edges,
                    [
                        "executed:a1b2c3",
                        "exists:spec:d4e5f6",
                        "state:backlog:done:g7h8j9",
                    ],
                    "the runner must see the SAME edges the shared parser sees, "
                    "where pre-fix it saw []",
                )

    def test_shared_parser_agreement_is_exact(self):
        """The runner's view must equal `ipd_schema.parse_item_dependencies`, not merely be nonempty."""
        shared, _ready, err = ipd_schema.parse_item_dependencies(_THREE_EDGE_VALUE)
        self.assertIsNone(err)
        expected = [e.canonical() for e in shared]
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                edges, _e = mod._read_item_dependencies(_plan_text("aaaaaa"))
                self.assertEqual(edges, expected)

    def test_qualifiers_are_not_flattened_to_bare_id6(self):
        """Plan finding F4: keeping only bare id6 tokens would silently change an edge's meaning."""
        edges, _err = oc_runipd._read_item_dependencies(_plan_text("aaaaaa"))
        for tok in edges:
            self.assertIn(
                ":", tok, f"edge {tok!r} lost its qualifier (degraded to a bare id6)"
            )
        self.assertIn("exists:spec:d4e5f6", edges)
        self.assertIn("state:backlog:done:g7h8j9", edges)

    def test_legacy_field_no_longer_yields_dependencies(self):
        """OQ-01 (resolved): the legacy field is REMOVED, not accepted alongside the canonical one."""
        legacy = "# IPD: aaaaaa\n\n- Id: aaaaaa\n- Dependencies: [5ahblp, pr2nd0]\n\n## Goal\n"
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                self.assertEqual(mod._read_item_dependencies(legacy), ([], None))

    def test_none_and_unresolved_and_absent_all_yield_no_edges(self):
        for value in ("none", "unresolved", ""):
            with self.subTest(value=value):
                edges, err = oc_runipd._read_item_dependencies(
                    _plan_text("aaaaaa", deps=value)
                )
                self.assertEqual(edges, [])
                self.assertIsNone(err)
        edges, err = oc_runipd._read_item_dependencies(_plan_text("aaaaaa", deps=None))
        self.assertEqual(edges, [])
        self.assertIsNone(err)

    def test_malformed_statement_surfaces_the_shared_parser_error(self):
        edges, err = oc_runipd._read_item_dependencies(
            _plan_text("aaaaaa", deps="executed:TOOLONGID")
        )
        self.assertEqual(edges, [])
        self.assertIsNotNone(err)

    def test_plan_record_carries_typed_edges(self):
        with tempfile.TemporaryDirectory() as t:
            repo = Path(t)
            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            path = _write_plan(pending, "aaaaaa")
            for name, mod in _DRIVERS:
                with self.subTest(driver=name):
                    rec = mod.parse_plan_file(path, repo)
                    self.assertEqual(
                        rec.dependencies,
                        [
                            "executed:a1b2c3",
                            "exists:spec:d4e5f6",
                            "state:backlog:done:g7h8j9",
                        ],
                    )
                    self.assertIsNone(rec.dependency_error)

    def test_frozen_queue_entry_carries_typed_edges(self):
        """The FROZEN queue is where the pre-fix `[]` was observed in real run records."""
        with tempfile.TemporaryDirectory() as t:
            repo = Path(t)
            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            _write_plan(pending, "aaaaaa")
            for name, mod in _DRIVERS:
                with self.subTest(driver=name):
                    manifest = mod.build_dynamic_manifest(
                        repo, mod.discover_plans(repo)
                    )
                    self.assertEqual(
                        manifest["plans"]["aaaaaa"]["dependencies"],
                        [
                            "executed:a1b2c3",
                            "exists:spec:d4e5f6",
                            "state:backlog:done:g7h8j9",
                        ],
                    )


class DependencyTokenGrammarTests(unittest.TestCase):
    def test_typed_tokens_resolve_through_the_shared_grammar(self):
        for tok, kind, ttype, status, id6 in (
            ("executed:a1b2c3", "executed", "ipd", None, "a1b2c3"),
            ("exists:spec:d4e5f6", "exists", "spec", None, "d4e5f6"),
            ("state:backlog:done:g7h8j9", "state", "backlog", "done", "g7h8j9"),
        ):
            with self.subTest(tok=tok):
                edge = oc_runipd.parse_dependency_token(tok)
                self.assertEqual(
                    (edge.kind, edge.target_type, edge.status, edge.id6),
                    (kind, ttype, status, id6),
                )

    def test_bare_id6_normalizes_to_an_executed_edge(self):
        """A legacy hand-written manifest JSON may still carry bare id6s; `executed:` is what they meant."""
        edge = oc_runipd.parse_dependency_token("a1b2c3")
        self.assertEqual((edge.kind, edge.id6), ("executed", "a1b2c3"))

    def test_illegal_tokens_are_rejected(self):
        for tok in ("", "garbage", "executed:", "state:ipd:executed:a1b2c3", "E-01"):
            with self.subTest(tok=tok):
                self.assertIsNone(oc_runipd.parse_dependency_token(tok))


class EdgeSatisfactionTests(unittest.TestCase):
    """E-03: spec 25kzda 2.9 runtime satisfaction, one demonstration per kind."""

    def _repo(self, temp: Path) -> Path:
        repo = temp / "repo"
        (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        return repo

    def _state(self, repo: Path, queue: list[dict]) -> dict:
        return {"repo": str(repo), "queue": queue}

    def test_executed_edge_in_queue_unsatisfied_causes_wait_not_start(self):
        with tempfile.TemporaryDirectory() as t:
            repo = self._repo(Path(t))
            state = self._state(
                repo,
                [
                    {
                        "id6": "depaaa",
                        "status": "queued",
                        "action": "execute",
                        "dependencies": [],
                        "position": 1,
                    },
                    {
                        "id6": "itemaa",
                        "status": "queued",
                        "action": "execute",
                        "dependencies": ["executed:depaaa"],
                        "position": 2,
                    },
                ],
            )
            dependent = state["queue"][1]
            satisfied, missing = oc_runipd.dependency_status(dependent, state)
            self.assertFalse(satisfied, "the dependent must WAIT, not start")
            self.assertEqual(missing, ["executed:depaaa"])

    def test_executed_edge_released_by_a_verified_in_run_target(self):
        with tempfile.TemporaryDirectory() as t:
            repo = self._repo(Path(t))
            for target_status in ("executed", "substantially-complete"):
                with self.subTest(target_status=target_status):
                    state = self._state(
                        repo,
                        [
                            {
                                "id6": "depaaa",
                                "status": target_status,
                                "action": "execute",
                                "dependencies": [],
                                "position": 1,
                            },
                            {
                                "id6": "itemaa",
                                "status": "queued",
                                "action": "execute",
                                "dependencies": ["executed:depaaa"],
                                "position": 2,
                            },
                        ],
                    )
                    satisfied, missing = oc_runipd.dependency_status(
                        state["queue"][1], state
                    )
                    self.assertTrue(satisfied)
                    self.assertEqual(missing, [])

    def test_executed_edge_external_target_must_be_in_executed_bucket(self):
        for bucket, expect_ok in (("executed", True), ("pending", False)):
            with self.subTest(bucket=bucket):
                with tempfile.TemporaryDirectory() as t:
                    repo = self._repo(Path(t))
                    d = repo / ".aw" / "records" / "plans" / bucket
                    d.mkdir(parents=True, exist_ok=True)
                    (d / "20260829-demo-01-depaaa-x.ipd.md").write_text(
                        _plan_text("depaaa", deps="none"), encoding="utf-8"
                    )
                    state = self._state(
                        repo,
                        [
                            {
                                "id6": "itemaa",
                                "status": "queued",
                                "action": "execute",
                                "dependencies": ["executed:depaaa"],
                                "position": 1,
                            }
                        ],
                    )
                    satisfied, _missing = oc_runipd.dependency_status(
                        state["queue"][0], state
                    )
                    self.assertEqual(satisfied, expect_ok)

    def test_exists_edge_releases_immediately_without_waiting(self):
        """spec 2.9: an `exists:` edge is evaluated from current state and does NOT wait."""
        with tempfile.TemporaryDirectory() as t:
            repo = self._repo(Path(t))
            specs = repo / ".aw" / "records" / "specs"
            specs.mkdir(parents=True)
            (specs / "20260829-d4e5f6-01-d4e5f6-demo.spec.md").write_text(
                "# Spec\n\n- Id: d4e5f6\n- Status: draft\n", encoding="utf-8"
            )
            state = self._state(
                repo,
                [
                    {
                        "id6": "itemaa",
                        "status": "queued",
                        "action": "execute",
                        "dependencies": ["exists:spec:d4e5f6"],
                        "position": 1,
                    }
                ],
            )
            satisfied, missing = oc_runipd.dependency_status(state["queue"][0], state)
            self.assertTrue(
                satisfied,
                "an existing target satisfies `exists:` whatever its status (here: draft)",
            )
            self.assertEqual(missing, [])

    def test_exists_edge_unsatisfied_when_the_target_does_not_exist(self):
        with tempfile.TemporaryDirectory() as t:
            repo = self._repo(Path(t))
            state = self._state(
                repo,
                [
                    {
                        "id6": "itemaa",
                        "status": "queued",
                        "action": "execute",
                        "dependencies": ["exists:spec:d4e5f6"],
                        "position": 1,
                    }
                ],
            )
            satisfied, missing = oc_runipd.dependency_status(state["queue"][0], state)
            self.assertFalse(satisfied)
            self.assertEqual(missing, ["exists:spec:d4e5f6"])

    def test_state_edge_requires_the_exact_status(self):
        with tempfile.TemporaryDirectory() as t:
            repo = self._repo(Path(t))
            specs = repo / ".aw" / "records" / "specs"
            specs.mkdir(parents=True)
            spec_file = specs / "20260829-d4e5f6-01-d4e5f6-demo.spec.md"
            state = self._state(
                repo,
                [
                    {
                        "id6": "itemaa",
                        "status": "queued",
                        "action": "execute",
                        "dependencies": ["state:spec:approved:d4e5f6"],
                        "position": 1,
                    }
                ],
            )
            spec_file.write_text(
                "# Spec\n\n- Id: d4e5f6\n- Status: draft\n", encoding="utf-8"
            )
            satisfied, missing = oc_runipd.dependency_status(state["queue"][0], state)
            self.assertFalse(satisfied, "a NEAR-miss status must not satisfy `state:`")
            self.assertEqual(missing, ["state:spec:approved:d4e5f6"])

            spec_file.write_text(
                "# Spec\n\n- Id: d4e5f6\n- Status: approved\n", encoding="utf-8"
            )
            satisfied, missing = oc_runipd.dependency_status(state["queue"][0], state)
            self.assertTrue(satisfied, "the EXACT status releases immediately")
            self.assertEqual(missing, [])

    def test_unconverted_typed_token_blocks_rather_than_admits(self):
        """Plan finding F8: pin the failure DIRECTION.

        A raw `"executed:depaaa"` string used BOTH as a queue dict key and as an id6 misses the queue
        lookup AND fails id6 resolution, so the WRONG implementation over-blocks a satisfied
        dependent; it never wrongly admits an unsatisfied one. A test written for the other direction
        would pass while the bug was live.
        """
        with tempfile.TemporaryDirectory() as t:
            repo = self._repo(Path(t))
            state = self._state(
                repo,
                [
                    {
                        "id6": "depaaa",
                        "status": "executed",
                        "action": "execute",
                        "dependencies": [],
                        "position": 1,
                    },
                    {
                        "id6": "itemaa",
                        "status": "queued",
                        "action": "execute",
                        "dependencies": ["executed:depaaa"],
                        "position": 2,
                    },
                ],
            )
            # The naive lookup the fix must NOT do:
            by_id = {e["id6"]: e for e in state["queue"]}
            self.assertNotIn(
                "executed:depaaa",
                by_id,
                "the raw token is not a queue key; treating it as one is the F8 hazard",
            )
            # The real implementation converts first, so the satisfied dependent is RELEASED.
            satisfied, missing = oc_runipd.dependency_status(state["queue"][1], state)
            self.assertTrue(
                satisfied,
                "an unconverted token would BLOCK this satisfied dependent (F8 direction)",
            )
            self.assertEqual(missing, [])

    def test_unparseable_token_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            repo = self._repo(Path(t))
            state = self._state(
                repo,
                [
                    {
                        "id6": "itemaa",
                        "status": "queued",
                        "action": "execute",
                        "dependencies": ["not-an-edge"],
                        "position": 1,
                    }
                ],
            )
            satisfied, missing = oc_runipd.dependency_status(state["queue"][0], state)
            self.assertFalse(
                satisfied, "an unparseable token is never treated as 'no dependency'"
            )
            self.assertEqual(missing, ["not-an-edge"])

    def test_no_declared_edges_is_satisfied(self):
        with tempfile.TemporaryDirectory() as t:
            repo = self._repo(Path(t))
            state = self._state(
                repo,
                [
                    {
                        "id6": "itemaa",
                        "status": "queued",
                        "action": "execute",
                        "dependencies": [],
                        "position": 1,
                    }
                ],
            )
            self.assertEqual(
                oc_runipd.dependency_status(state["queue"][0], state), (True, [])
            )


class PreflightFailClosedTests(unittest.TestCase):
    """E-02: refuse BEFORE any host session, naming the shared rule; no runner-local policy."""

    def _repo(self, temp: Path) -> tuple[Path, Path]:
        repo = temp / "repo"
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True)
        return repo, pending

    def test_each_fail_closed_class_refuses_and_names_the_shared_rule(self):
        cases = {
            "malformed": ("executed:NOTANID6", ipd_schema.RULE_IPD_DEP_MALFORMED),
            "dangling": ("executed:zzzzzz", ipd_schema.RULE_IPD_DEP_DANGLING),
            "self-edge": ("executed:aaaaaa", ipd_schema.RULE_IPD_DEP_MALFORMED),
            "unresolved": ("unresolved", ipd_schema.RULE_IPD_DEP_UNRESOLVED),
        }
        for label, (value, rule) in cases.items():
            with self.subTest(case=label):
                with tempfile.TemporaryDirectory() as t:
                    repo, pending = self._repo(Path(t))
                    path = _write_plan(pending, "aaaaaa", deps=value)
                    findings = oc_runipd.preflight_dependency_findings(repo, [path])
                    self.assertTrue(findings, f"{label} must produce a finding")
                    self.assertIn(rule, [f[1] for f in findings])
                    with self.assertRaises(oc_runipd.DriverError) as ctx:
                        oc_runipd.enforce_dependency_preflight(repo, [path])
                    self.assertIn(rule, str(ctx.exception))

    def test_cycle_is_refused(self):
        with tempfile.TemporaryDirectory() as t:
            repo, pending = self._repo(Path(t))
            a = _write_plan(pending, "aaaaaa", order=1, deps="executed:bbbbbb")
            b = _write_plan(pending, "bbbbbb", order=2, deps="executed:aaaaaa")
            findings = oc_runipd.preflight_dependency_findings(repo, [a, b])
            self.assertIn(ipd_schema.RULE_IPD_DEP_CYCLE, [f[1] for f in findings])
            with self.assertRaises(oc_runipd.DriverError) as ctx:
                oc_runipd.enforce_dependency_preflight(repo, [a, b])
            self.assertIn(ipd_schema.RULE_IPD_DEP_CYCLE, str(ctx.exception))

    def test_ambiguous_id6_is_reported_as_fatal(self):
        """spec 2.10 maps ambiguity to the run-wide `fatal` identity class."""
        with tempfile.TemporaryDirectory() as t:
            repo, pending = self._repo(Path(t))
            dup = repo / ".aw" / "records" / "plans" / "executed"
            dup.mkdir(parents=True)
            for n, sub in enumerate(("one", "two"), start=1):
                (dup / f"20260829-dupe-0{n}-d4e5f6-{sub}.ipd.md").write_text(
                    _plan_text("d4e5f6", deps="none", setid="dupe", order=n),
                    encoding="utf-8",
                )
            path = _write_plan(pending, "aaaaaa", deps="executed:d4e5f6")
            findings = oc_runipd.preflight_dependency_findings(repo, [path])
            rules = [f[1] for f in findings]
            self.assertIn(ipd_schema.RULE_IPD_DEP_AMBIGUOUS, rules)
            self.assertIn(
                ipd_schema.RULE_IPD_DEP_AMBIGUOUS, oc_runipd.DEPENDENCY_FATAL_RULES
            )
            with self.assertRaises(oc_runipd.DriverError) as ctx:
                oc_runipd.enforce_dependency_preflight(repo, [path])
            self.assertIn("ABORTED", str(ctx.exception))

    def test_a_valid_graph_is_admitted(self):
        with tempfile.TemporaryDirectory() as t:
            repo, pending = self._repo(Path(t))
            a = _write_plan(pending, "aaaaaa", order=1, deps="none")
            b = _write_plan(pending, "bbbbbb", order=2, deps="executed:aaaaaa")
            self.assertEqual(oc_runipd.preflight_dependency_findings(repo, [a, b]), [])
            self.assertEqual(oc_runipd.enforce_dependency_preflight(repo, [a, b]), [])

    def test_missing_statement_is_delegated_not_decided_locally(self):
        """8guhs0 OQ-02: the runner adds NO rule for the missing case; the evaluator decides."""
        with tempfile.TemporaryDirectory() as t:
            repo, pending = self._repo(Path(t))
            path = _write_plan(pending, "aaaaaa", deps=None)
            runner = oc_runipd.preflight_dependency_findings(repo, [path])
            shared = check_engine.evaluate_ipd_dependencies(
                repo,
                phase="pre-execution",
                plans=[(path, path.read_text(encoding="utf-8"))],
            )
            self.assertEqual(
                [(f[1], f[2]) for f in runner],
                [(d.rule, d.detail) for d in shared],
                "the runner must report EXACTLY what the shared evaluator returns",
            )

    def test_missing_statement_severity_follows_the_cutover_marker(self):
        """With no marker set, everything is grandfathered; setting it makes the field mandatory.

        This is the OQ-02 consequence, demonstrated rather than asserted: the behavior changes with
        the MARKER, with no change in the runner.
        """
        from agent_workflows import config as _config

        with tempfile.TemporaryDirectory() as t:
            repo, pending = self._repo(Path(t))
            path = _write_plan(pending, "aaaaaa", deps=None, date="2026-08-29")
            self.assertIsNone(
                _config.dependency_cutover_date(repo), "no marker in a fresh repo"
            )
            self.assertEqual(
                oc_runipd.preflight_dependency_findings(repo, [path]),
                [],
                "grandfathered: an absent marker must never mass-fail the corpus",
            )
            marker = repo / ".aw" / "config" / "project.json"
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(
                json.dumps({_config.DEPENDENCY_SCHEMA_CUTOVER_KEY: "2026-01-01"}),
                encoding="utf-8",
            )
            self.assertEqual(_config.dependency_cutover_date(repo), "2026-01-01")
            self.assertIn(
                ipd_schema.RULE_IPD_DEP_MISSING,
                [f[1] for f in oc_runipd.preflight_dependency_findings(repo, [path])],
                "a POST-cutover fieldless plan starts failing automatically",
            )

    def test_no_runner_local_missing_statement_branch_exists(self):
        """The diff must contain no runner-local rule for the missing case (OQ-02)."""
        for name, path in _DRIVER_SOURCES:
            with self.subTest(driver=name):
                code = _code_only(path.read_text(encoding="utf-8"))
                self.assertNotIn(
                    ipd_schema.RULE_IPD_DEP_MISSING,
                    code,
                    "the runner must not name the missing-statement rule in CODE; "
                    "it delegates to the shared evaluator",
                )
                self.assertNotIn(
                    "dependency_cutover_date",
                    code,
                    "the runner must not consult the cutover marker itself; that is the "
                    "shared evaluator's input (OQ-02)",
                )

    def test_preflight_refuses_before_any_session_starts(self):
        """The refusal must precede the run directory, hence any session log or launch event."""
        with tempfile.TemporaryDirectory() as t:
            repo, pending = self._repo(Path(t))
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            _write_plan(pending, "aaaaaa", deps="executed:zzzzzz")
            runs_root = oc_runipd.state_root(repo)
            args = _StartArgs(repo=str(repo), selectors=["aaaaaa"])
            with self.assertRaises(oc_runipd.DriverError) as ctx:
                oc_runipd.initialize_run(args)
            self.assertIn(ipd_schema.RULE_IPD_DEP_DANGLING, str(ctx.exception))
            self.assertFalse(
                runs_root.exists() and any(runs_root.iterdir()),
                "no run directory (hence no session log/prompt) may exist after a refusal",
            )

    def test_agy_preflight_raises_its_own_driver_error_type(self):
        """agy's `main` catches `agy_runipd.DriverError`; a leaked oc error would traceback."""
        with tempfile.TemporaryDirectory() as t:
            repo, pending = self._repo(Path(t))
            path = _write_plan(pending, "aaaaaa", deps="executed:zzzzzz")
            self.assertIsNot(agy_runipd.DriverError, oc_runipd.DriverError)
            with self.assertRaises(agy_runipd.DriverError):
                agy_runipd.enforce_dependency_preflight(repo, [path])


def _StartArgs(repo: str, selectors: list[str]) -> argparse.Namespace:
    """The `initialize_run` argument surface (`initialize_run` reads it with `getattr`)."""
    return argparse.Namespace(
        repo=repo,
        selectors=selectors,
        manifest=None,
        runbook=None,
        session=None,
        run_id=None,
        full_auto=False,
        opencode="opencode",
        model=None,
        agent=None,
        auto=True,
        output_mode="clean",
        stall_timeout=600.0,
        validate=False,
        self_finalize=True,
        isolate_worktree=False,
        max_items_per_session=4,
    )


class OrderingAndCascadeTests(unittest.TestCase):
    """E-04: declared edges authoritative; Set/Order a tiebreaker; `dependency-blocked` cascade."""

    def _item(
        self, id6, *, deps=None, setid="demo", order=1, position=1, status="queued"
    ):
        return {
            "id6": id6,
            "setid": setid,
            "order": order,
            "position": position,
            "status": status,
            "action": "execute",
            "dependencies": list(deps or []),
        }

    def test_dependency_depth_counts_only_in_queue_ipd_edges(self):
        queue = [
            self._item("aaaaaa", position=1),
            self._item("bbbbbb", deps=["executed:aaaaaa"], position=2),
            self._item("cccccc", deps=["executed:bbbbbb"], position=3),
            self._item("dddddd", deps=["exists:spec:d4e5f6"], position=4),
            self._item("eeeeee", deps=["executed:zzzzzz"], position=5),
        ]
        by_id = {i["id6"]: i for i in queue}
        self.assertEqual(oc_runipd.dependency_depth("aaaaaa", by_id), 0)
        self.assertEqual(oc_runipd.dependency_depth("bbbbbb", by_id), 1)
        self.assertEqual(oc_runipd.dependency_depth("cccccc", by_id), 2)
        self.assertEqual(
            oc_runipd.dependency_depth("dddddd", by_id),
            0,
            "a spec/backlog leaf is not a queue node",
        )
        self.assertEqual(
            oc_runipd.dependency_depth("eeeeee", by_id),
            0,
            "an external target is not a queue node",
        )

    def test_dependency_depth_is_cycle_safe(self):
        queue = [
            self._item("aaaaaa", deps=["executed:bbbbbb"], position=1),
            self._item("bbbbbb", deps=["executed:aaaaaa"], position=2),
        ]
        by_id = {i["id6"]: i for i in queue}
        self.assertIsInstance(oc_runipd.dependency_depth("aaaaaa", by_id), int)

    def test_declared_edges_beat_set_order_when_the_two_disagree(self):
        """The prerequisite has the HIGHER Order and the LATER position; the edge must still win."""
        queue = [
            self._item(
                "depend", deps=["executed:prereq"], setid="demo", order=1, position=1
            ),
            self._item("prereq", setid="demo", order=9, position=2),
        ]
        by_id = {i["id6"]: i for i in queue}
        ordered = [
            i["id6"]
            for i in sorted(queue, key=lambda it: oc_runipd.queue_sort_key(it, by_id))
        ]
        self.assertEqual(
            ordered,
            ["prereq", "depend"],
            "Set/Order said depend-first; the declared edge must reorder it",
        )

    def test_set_order_still_breaks_ties_among_equally_ready_nodes(self):
        queue = [
            self._item("bbbbbb", setid="demo", order=2, position=1),
            self._item("aaaaaa", setid="demo", order=1, position=2),
        ]
        by_id = {i["id6"]: i for i in queue}
        ordered = [
            i["id6"]
            for i in sorted(queue, key=lambda it: oc_runipd.queue_sort_key(it, by_id))
        ]
        self.assertEqual(
            ordered, ["aaaaaa", "bbbbbb"], "Order 1 precedes Order 2 on a tie"
        )

    def test_position_is_never_renumbered_by_ordering(self):
        """`position` is a stable identity (outcome/prompt/session filenames key on it)."""
        queue = [
            self._item("depend", deps=["executed:prereq"], order=1, position=1),
            self._item("prereq", order=9, position=2),
        ]
        by_id = {i["id6"]: i for i in queue}
        sorted(queue, key=lambda it: oc_runipd.queue_sort_key(it, by_id))
        self.assertEqual([i["position"] for i in queue], [1, 2])

    def test_missing_order_key_still_sorts(self):
        """An older run directory frozen before E-04 has no `order` key; resume must not crash."""
        legacy = {
            "id6": "aaaaaa",
            "setid": "demo",
            "position": 1,
            "status": "queued",
            "action": "execute",
            "dependencies": [],
        }
        by_id = {"aaaaaa": legacy}
        self.assertIsInstance(oc_runipd.queue_sort_key(legacy, by_id), tuple)

    def test_cascade_marks_only_dependents_of_a_failed_item(self):
        state = {
            "repo": "/nonexistent",
            "queue": [
                self._item("failed", position=1, status="failed-safely"),
                self._item("child1", deps=["executed:failed"], position=2),
                self._item("child2", deps=["executed:child1"], position=3),
                self._item("indep", position=4),
            ],
        }
        blocked = oc_runipd.cascade_dependency_blocked(state)
        by_id = {i["id6"]: i for i in state["queue"]}
        self.assertEqual({i["id6"] for i in blocked}, {"child1", "child2"})
        self.assertEqual(by_id["child1"]["status"], "dependency-blocked")
        self.assertEqual(
            by_id["child2"]["status"],
            "dependency-blocked",
            "the cascade must reach a fixed point over reverse edges",
        )
        self.assertEqual(
            by_id["indep"]["status"], "queued", "independent work must keep running"
        )
        self.assertTrue(by_id["child1"]["unsatisfied_dependencies"])

    def test_cascade_uses_the_existing_disposition_not_a_new_state(self):
        """Plan finding F9: `dependency-not-met` does not exist in this runner; do not invent it."""
        state = {
            "repo": "/nonexistent",
            "queue": [
                self._item("failed", position=1, status="failed-safely"),
                self._item("child1", deps=["executed:failed"], position=2),
            ],
        }
        oc_runipd.cascade_dependency_blocked(state)
        self.assertEqual(state["queue"][1]["status"], "dependency-blocked")
        self.assertIn("dependency-blocked", oc_runipd.TERMINAL_STATES)
        for name, path in _DRIVER_SOURCES:
            with self.subTest(driver=name):
                self.assertNotIn(
                    "dependency-not-met",
                    _code_only(path.read_text(encoding="utf-8")),
                    "the spec's `dependency_not_met` vocabulary must not become a second "
                    "runner state; run records already on disk use `dependency-blocked`",
                )
                self.assertNotIn(
                    "dependency_not_met", _code_only(path.read_text(encoding="utf-8"))
                )

    def test_cascade_does_not_block_on_a_successful_prerequisite(self):
        for good in ("executed", "substantially-complete"):
            with self.subTest(status=good):
                state = {
                    "repo": "/nonexistent",
                    "queue": [
                        self._item("prereq", position=1, status=good),
                        self._item("child1", deps=["executed:prereq"], position=2),
                    ],
                }
                self.assertEqual(oc_runipd.cascade_dependency_blocked(state), [])
                self.assertEqual(state["queue"][1]["status"], "queued")

    def test_no_declared_edges_set_is_untouched_by_the_cascade(self):
        """NO-REGRESSION: the behavior every current run depends on must be identical."""
        state = {
            "repo": "/nonexistent",
            "queue": [
                self._item("failed", position=1, status="failed-safely"),
                self._item("other1", position=2),
                self._item("other2", position=3),
            ],
        }
        self.assertEqual(oc_runipd.cascade_dependency_blocked(state), [])
        self.assertEqual(
            [i["status"] for i in state["queue"]],
            ["failed-safely", "queued", "queued"],
        )


class NoRegressionForUndeclaredEdgesTests(unittest.TestCase):
    """A Set with NO declared edges must gate exactly as it did pre-fix."""

    def test_existing_bare_id6_gating_semantics_are_preserved(self):
        """The pre-8guhs0 tests' semantics (bare id6 == `executed:`) still hold."""
        state = {
            "repo": "/nonexistent",
            "queue": [
                {"id6": "dep001", "status": "reviewed", "action": "review"},
                {"id6": "dep002", "status": "approved", "action": "execute"},
                {"id6": "dep003", "status": "executed", "action": "execute"},
            ],
        }
        for dep, action, expected in (
            ("dep001", "execute", False),
            ("dep002", "execute", False),
            ("dep003", "execute", True),
            ("dep001", "review", True),
        ):
            with self.subTest(dep=dep, action=action):
                item = {"id6": "tgt", "action": action, "dependencies": [dep]}
                sat, _missing = oc_runipd.dependency_status(item, state)
                self.assertEqual(sat, expected)

    def test_orchestrator_deferral_path_is_unchanged(self):
        """The orchestrator `dependency-blocked` call sites gate on children, not on edges."""
        state = {
            "repo": "/nonexistent",
            "queue": [
                {
                    "id6": "orch00",
                    "setid": "demo",
                    "status": "queued",
                    "action": "orchestrate",
                    "dependencies": [],
                    "position": 1,
                },
                {
                    "id6": "child1",
                    "setid": "demo",
                    "status": "queued",
                    "action": "execute",
                    "dependencies": [],
                    "position": 2,
                },
            ],
        }
        all_done, unfinished = oc_runipd._set_children_all_executed(
            state, "demo", "orch00"
        )
        self.assertFalse(all_done)
        self.assertEqual(unfinished, ["child1"])
        self.assertEqual(oc_runipd.cascade_dependency_blocked(state), [])


class AntiDivergenceGuardTests(unittest.TestCase):
    """E-05: the two parsers must not be able to diverge again."""

    # A `re.compile(...)` call whose pattern text mentions a dependency field name. Deliberately
    # NOT `[^)]*`: a real pattern contains `)` (e.g. the `(?m)` flag group), so a `[^)]*` bound
    # cannot reach the field name and the guard would be VACUOUS - measured: it passed against the
    # pre-fix `_DEPS_RE` it was written to catch. Bounded by a newline instead, since these are
    # single-line declarations.
    _DEP_REGEX_HINT = re.compile(
        r"re\.compile\([^\n]*(?:Item-Dependencies|Dependencies|Depends-on)"
    )

    def test_no_driver_defines_a_dependency_regex(self):
        for name, path in _DRIVER_SOURCES:
            with self.subTest(driver=name):
                text = path.read_text(encoding="utf-8")
                # NOTE: this guard reads the RAW source on purpose. A dependency regex is written as
                # a string literal, which `_code_only` would strip, so stripping here would make the
                # guard unfalsifiable. Comments are dropped (they are prose), string literals are not.
                code = "\n".join(
                    ln for ln in text.splitlines() if not ln.lstrip().startswith("#")
                )
                self.assertIsNone(
                    self._DEP_REGEX_HINT.search(code),
                    f"{name} re-introduced a private dependency regex; the field NAME must come "
                    "from ipd_schema and the GRAMMAR from parse_item_dependencies",
                )

    def test_no_driver_defines_the_deleted_private_parser(self):
        for name, path in _DRIVER_SOURCES:
            with self.subTest(driver=name):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("_DEPS_RE = ", text)
                self.assertNotIn("def _read_deps(", text)

    def test_no_driver_exposes_the_deleted_names(self):
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                self.assertFalse(hasattr(mod, "_DEPS_RE"))
                self.assertFalse(hasattr(mod, "_read_deps"))

    def test_drivers_reference_the_shared_dependency_api(self):
        """Pre-fix BOTH drivers referenced the shared dependency API zero times."""
        oc_text = (REPO_ROOT / "agent_workflows" / "oc_runipd.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("parse_item_dependencies", oc_text)
        self.assertIn("META_ITEM_DEPENDENCIES", oc_text)
        self.assertIn("evaluate_ipd_dependencies", oc_text)

    def test_shared_rule_modules_are_not_modified_by_the_runner(self):
        """The runner became a CONSUMER; the shared rules stay in the shared modules."""
        for mod_name in ("check_engine", "ipd_lint"):
            text = (REPO_ROOT / "agent_workflows" / f"{mod_name}.py").read_text(
                encoding="utf-8"
            )
            with self.subTest(module=mod_name):
                for runner_only in ("oc_runipd", "agy_runipd", "dependency_status"):
                    self.assertNotIn(
                        runner_only,
                        text,
                        f"{mod_name} must not learn about the runner or its run state",
                    )


class CrossDriverSymmetryTests(unittest.TestCase):
    """Both drivers are declared in this plan's Scope-Paths, so REAL symmetry is required."""

    _SHARED_NAMES = (
        "_read_item_dependencies",
        "parse_dependency_token",
        "dependency_target_id6",
        "edge_satisfied",
        "dependency_status",
        "dependency_reasons",
        "dependency_depth",
        "queue_sort_key",
        "cascade_dependency_blocked",
        "preflight_dependency_findings",
        "DEPENDENCY_FATAL_RULES",
    )

    def test_both_drivers_expose_the_dependency_api(self):
        for name in self._SHARED_NAMES:
            for dname, mod in _DRIVERS:
                with self.subTest(name=name, driver=dname):
                    self.assertTrue(hasattr(mod, name), f"{dname} is missing {name}")

    def test_the_implementation_is_shared_not_copied(self):
        """ONE definition: agy binds the SAME objects, so a fix cannot land in only one driver."""
        for name in self._SHARED_NAMES:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(agy_runipd, name),
                    getattr(oc_runipd, name),
                    f"{name} is a COPY in agy_runipd; it must be the shared object",
                )

    def test_both_drivers_agree_on_a_typed_statement(self):
        text = _plan_text("aaaaaa")
        self.assertEqual(
            oc_runipd._read_item_dependencies(text),
            agy_runipd._read_item_dependencies(text),
        )

    def test_both_drivers_freeze_the_same_queue_dependencies(self):
        with tempfile.TemporaryDirectory() as t:
            repo = Path(t)
            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            _write_plan(pending, "aaaaaa", order=1, deps="none")
            _write_plan(pending, "bbbbbb", order=2, deps="executed:aaaaaa")
            oc_manifest = oc_runipd.build_dynamic_manifest(
                repo, oc_runipd.discover_plans(repo)
            )
            agy_manifest = agy_runipd.build_dynamic_manifest(
                repo, agy_runipd.discover_plans(repo)
            )
            self.assertEqual(
                {k: v["dependencies"] for k, v in oc_manifest["plans"].items()},
                {k: v["dependencies"] for k, v in agy_manifest["plans"].items()},
            )
            self.assertEqual(
                oc_manifest["plans"]["bbbbbb"]["dependencies"], ["executed:aaaaaa"]
            )

    def test_both_drivers_validate_a_typed_manifest_identically(self):
        manifest = {
            "schema_version": oc_runipd.SCHEMA_VERSION,
            "plans": {
                "aaaaaa": {
                    "file": ".aw/records/plans/pending/a.ipd.md",
                    "set": "demo",
                    "dependencies": [],
                },
                "bbbbbb": {
                    "file": ".aw/records/plans/pending/b.ipd.md",
                    "set": "demo",
                    "dependencies": ["executed:aaaaaa", "exists:spec:d4e5f6"],
                },
            },
            "sets": {"demo": {"order": ["aaaaaa", "bbbbbb"]}},
        }
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                mod.validate_manifest(json.loads(json.dumps(manifest)))

    def test_both_drivers_reject_an_unknown_ipd_target_and_accept_a_leaf(self):
        base = {
            "schema_version": oc_runipd.SCHEMA_VERSION,
            "plans": {
                "aaaaaa": {
                    "file": ".aw/records/plans/pending/a.ipd.md",
                    "set": "demo",
                    "dependencies": ["executed:zzzzzz"],
                }
            },
            "sets": {"demo": {"order": ["aaaaaa"]}},
        }
        for name, mod in _DRIVERS:
            with self.subTest(driver=name, case="unknown ipd target"):
                with self.assertRaises(mod.DriverError):
                    mod.validate_manifest(json.loads(json.dumps(base)))
        leaf = json.loads(json.dumps(base))
        leaf["plans"]["aaaaaa"]["dependencies"] = ["exists:spec:zzzzzz"]
        for name, mod in _DRIVERS:
            with self.subTest(driver=name, case="spec leaf"):
                mod.validate_manifest(json.loads(json.dumps(leaf)))

    def test_both_drivers_reject_a_malformed_manifest_edge(self):
        bad = {
            "schema_version": oc_runipd.SCHEMA_VERSION,
            "plans": {
                "aaaaaa": {
                    "file": ".aw/records/plans/pending/a.ipd.md",
                    "set": "demo",
                    "dependencies": ["not-an-edge"],
                }
            },
            "sets": {"demo": {"order": ["aaaaaa"]}},
        }
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with self.assertRaises(mod.DriverError):
                    mod.validate_manifest(json.loads(json.dumps(bad)))


class LiveCorpusAgreementTests(unittest.TestCase):
    """The runner must now see what the authority surface sees on the REAL tree."""

    def test_runner_extraction_matches_the_authority_surface(self):
        plans_root = REPO_ROOT / ".aw" / "records" / "plans"
        if not plans_root.is_dir():
            self.skipTest("no plans tree in this checkout")
        files = sorted(plans_root.rglob("*.ipd.md"))
        if not files:
            self.skipTest("no IPDs in this checkout")
        compared = 0
        for path in files:
            text = path.read_text(encoding="utf-8")
            m = check_engine._ITEM_DEPENDENCIES_RE.search(text)
            if m is None:
                continue
            expected_edges, err = (
                (
                    [
                        e.canonical()
                        for e in ipd_schema.parse_item_dependencies(m.group(1).strip())[
                            0
                        ]
                    ],
                    None,
                )
                if ipd_schema.parse_item_dependencies(m.group(1).strip())[2] is None
                else ([], ipd_schema.parse_item_dependencies(m.group(1).strip())[2])
            )
            got_edges, got_err = oc_runipd._read_item_dependencies(text)
            self.assertEqual(
                (got_edges, got_err is None),
                (expected_edges, err is None),
                f"runner disagrees with the authority extraction for {path.name}",
            )
            compared += 1
        self.assertGreater(compared, 0)

    def test_a_declaring_plan_yields_nonempty_dependencies(self):
        """Contrast with the measured pre-fix state: real run records froze `dependencies: []`."""
        plans_root = REPO_ROOT / ".aw" / "records" / "plans"
        if not plans_root.is_dir():
            self.skipTest("no plans tree in this checkout")
        found = []
        for path in sorted(plans_root.rglob("*.ipd.md")):
            rec = oc_runipd.parse_plan_file(path, REPO_ROOT)
            if rec and rec.dependencies:
                found.append((rec.id6, rec.dependencies))
        if not found:
            self.skipTest("no plan in this checkout declares a dependency edge")
        for _id6, deps in found:
            for tok in deps:
                self.assertIsNotNone(
                    oc_runipd.parse_dependency_token(tok),
                    f"live corpus token {tok!r} must parse through the shared grammar",
                )


if __name__ == "__main__":
    unittest.main()
