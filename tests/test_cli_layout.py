"""The read-only `aw layout` verb and the workspace layout health rules (`wslayout` Order 05
`30jug9`; spec `kw5y2s` Section 6.2).

WHAT THIS FILE EXISTS TO PIN, since for each of these a naive assertion passes while the feature is
broken in the way that actually matters:

1. THE FRESH-CLONE CASE IS THE DEFAULT, not an edge case. Spec Section 2.3 rules the emitted
   `.aw/system/layout.json` GITIGNORED, so EVERY fresh clone has none until an install runs. A test
   that only ever ran `aw layout` in a fully installed workspace would pass while the command
   crashed for every new contributor, so the no-emitted-file path is asserted explicitly, and so is
   the reverse (an installed repo must actually READ the emitted file rather than silently ignoring
   it, which is the only way a stale document is observable through the CLI at all).

2. THE CHECK RULE'S SILENCE IS AS LOAD-BEARING AS ITS NOISE. `check.system-layout-missing` must fire
   for an INSTALLED workspace whose document vanished, and must NOT fire for a repo that was never
   installed. Only the second half keeps `aw check` from failing on every fresh clone by design, and
   only a test can hold that line: the gate is one `if` in `check_system_layout`, and deleting it
   leaves every positive assertion here still passing. Both severities are pinned too, because an
   unregistered rule silently defaults to `error` (`check_engine._DEFAULT_RULESPEC`).

3. READ-ONLY MEANS PROVEN READ-ONLY. `aw layout` sits one keystroke from the TRANSACTIONAL
   `aw migrate-layout` in tab completion, so "it is read-only" is asserted against the filesystem
   (a byte-level before/after snapshot of the whole workspace), not merely against the help text.

4. THE UNION VOCABULARY DID NOT NARROW. `aw check reviews` and `aw check roadmaps` must BOTH be
   accepted type nouns. HONEST PROVENANCE (DECISION 05-30jug9-D4): `reviews` was made an accepted
   noun by Order 02 (`zvk796`, this plan's declared dependency), so this is a REGRESSION FENCE
   inherited from that Order rather than behavior introduced here. The falsifiable content is
   unchanged either way - an edit that drops either type fails here.

NO THIRD-PARTY IMPORTS. Schema conformance is checked structurally with the stdlib, matching
`tests/test_layout.py` and `tests/test_engine_install.py`: `jsonschema` is in neither the runtime
deps nor the `[test]` extra, so importing it would make this file skip or fail depending on the
environment rather than on the code.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.support import SOURCE_WORKFLOWS, init_repo

from agent_workflows import check_engine as CE
from agent_workflows import cli as CLI
from agent_workflows import engine as INS
from agent_workflows import layout as LAYOUT

LAYOUT_JSON = ".aw/system/layout.json"
LAYOUT_SCHEMA = ".aw/system/layout.schema.json"
VERSION_MARKER = ".aw/system/VERSION"

REPO_ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------------------


def _run_cli(*argv: str) -> subprocess.CompletedProcess:
    """Run `python -m agent_workflows <argv>` as a subprocess from the source checkout.

    A SUBPROCESS rather than an in-process call for the output-contract assertions, because the
    audience decision (`select_output`) keys off whether stdout is a TTY: captured pipes are the
    non-TTY path, which is exactly the path a script or CI job takes. stdin is DEVNULL so no prompt
    can ever block.
    """

    return subprocess.run(
        [sys.executable, "-m", "agent_workflows", *argv],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )


def _install(repo: Path) -> dict:
    """Install through the shared core every entry point funnels into."""

    return INS.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)


def _snapshot(root: Path) -> dict:
    """Map every file under `root` to its bytes, for a read-only proof.

    Content, not just names and mtimes: a rewrite with identical size and a preserved mtime would
    slip past a name-and-stat comparison, and "writes nothing" is the claim under test.
    """

    out: dict = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            try:
                out[str(path.relative_to(root))] = path.read_bytes()
            except OSError:
                out[str(path.relative_to(root))] = b"<unreadable>"
    return out


class _LayoutRepoCase(unittest.TestCase):
    """Base case providing an INSTALLED temporary workspace with the emitted layout artifacts."""

    @classmethod
    def setUpClass(cls) -> None:
        # ONE install shared across the class, then copied per test. A full install is the
        # expensive part; copying the result keeps each test independent without paying for it
        # repeatedly. Every test that MUTATES its workspace works on its own copy.
        cls._base_dir = tempfile.TemporaryDirectory()
        cls.installed = init_repo(Path(cls._base_dir.name) / "installed")
        (cls.installed / "README.md").write_text("seed\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "README.md"],
            cwd=str(cls.installed),
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["git", "commit", "-qm", "seed"],
            cwd=str(cls.installed),
            capture_output=True,
            check=False,
        )
        _install(cls.installed)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._base_dir.cleanup()

    def _copy_installed(self, name: str) -> Path:
        dest = Path(tempfile.mkdtemp(dir=self._base_dir.name)) / name
        shutil.copytree(self.installed, dest)
        return dest


# --------------------------------------------------------------------------------------------------
# E-01 / V-01: the `aw layout` verb
# --------------------------------------------------------------------------------------------------


class LayoutCommandExistsTests(unittest.TestCase):
    """`aw layout` is a real, declared, read-only parser leaf."""

    def test_layout_is_a_parser_leaf(self):
        parser = CLI._build_parser()
        args = parser.parse_args(["layout"])
        self.assertEqual(args.command, "layout")

    def test_layout_declares_the_read_only_output_contract(self):
        from agent_workflows.command_surface import get_declaration

        decl = get_declaration("layout")
        self.assertIsNotNone(decl, "aw layout must carry a CommandDeclaration")
        assert decl is not None  # narrow for type-checkers
        # `read` + `mutation_gate="none"` is the MACHINE-READABLE statement that this verb is
        # read-only. It is what keeps `layout` classified apart from the transactional
        # `migrate-layout`, so it is asserted rather than left to the help prose.
        self.assertEqual(decl.command_class, "read")
        self.assertEqual(decl.mutation_gate, "none")
        self.assertIn("--json", decl.legacy_flags)
        self.assertIn("--schema", decl.legacy_flags)
        self.assertIn("--agent", decl.legacy_flags)

    def test_layout_is_covered_by_the_live_conformance_matrix(self):
        """Every new read-only leaf must be live-exercised, not declaration-covered only."""
        from tests.conformance_matrix import LIVE_SAFE_LEAVES, build_matrix

        self.assertIn("layout", LIVE_SAFE_LEAVES)
        report = build_matrix(CLI._build_parser())
        self.assertTrue(
            report.rows_for("layout"), "aw layout produced no conformance matrix rows"
        )
        # Scoped to THIS leaf deliberately. The repo-wide "zero undeclared leaves" gate belongs to
        # `tests/test_cli_conformance_matrix.py`, which owns it; asserting it here too would make
        # this file fail for an UNRELATED leaf another Set is adding concurrently (measured at this
        # HEAD: the five `oc profile *` leaves are undeclared and are not this plan's work).
        self.assertNotIn(
            "layout",
            report.undeclared,
            "aw layout is a parser leaf with no declaration",
        )
        # Every scenario its class requires must be covered, which is the real contract for a new
        # read-only leaf: a leaf can be declared and still be under-covered.
        from tests.conformance_matrix import required_scenarios
        from agent_workflows.command_surface import get_declaration

        decl = get_declaration("layout")
        assert decl is not None  # narrow for type-checkers
        self.assertEqual(
            set(required_scenarios(decl)) - report.scenarios_for("layout"),
            set(),
            "aw layout is missing a required conformance scenario",
        )

    def test_layout_is_distinct_from_migrate_layout(self):
        """The adjacent transactional verb still exists and is a DIFFERENT leaf (F-2 / OQ-01)."""
        parser = CLI._build_parser()
        self.assertEqual(
            parser.parse_args(["migrate-layout"]).command, "migrate-layout"
        )
        self.assertEqual(parser.parse_args(["layout"]).command, "layout")

    def test_help_text_states_the_read_only_nature(self):
        """OQ-01's resolution REQUIRES the human surface to make read-only obvious."""
        res = _run_cli("layout", "--help")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("READ-ONLY", res.stdout)
        # And it must point at the transactional neighbor, so a user cannot confuse the two.
        self.assertIn("migrate-layout", res.stdout)


class LayoutJsonAndSchemaTests(unittest.TestCase):
    """V-01: `--json` and `--schema` emit the expected documents, and one validates the other."""

    def test_json_emits_the_layout_document(self):
        res = _run_cli("layout", "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        payload = json.loads(res.stdout)
        self.assertEqual(payload["command"], "layout")
        self.assertEqual(payload["exit_code"], 0)
        doc = payload["data"]["layout"]
        model = LAYOUT.build_default_layout()
        for key in model.to_schema()["required"]:
            self.assertIn(key, doc, f"emitted document missing required key {key!r}")
        self.assertEqual(doc["schema_version"], model.schema_version)
        # The union vocabulary reaches the CLI surface: eleven record classes, `roadmaps` retained
        # and `reviews` present (spec Section 3.2), with the `records` ROOT ALIAS excluded because
        # emitting it would assert a nonsensical `records/records/` path (layout.to_dict).
        self.assertEqual(len(doc["record_classes"]), 11)
        self.assertIn("roadmaps", doc["record_classes"])
        self.assertIn("reviews", doc["record_classes"])
        self.assertNotIn("records", doc["record_classes"])

    def test_schema_emits_the_json_schema(self):
        res = _run_cli("layout", "--schema")
        self.assertEqual(res.returncode, 0, res.stderr)
        schema = json.loads(res.stdout)
        self.assertEqual(schema["title"], "AgentWorkflowsLayout")
        self.assertIn("$schema", schema)
        self.assertEqual(schema["additionalProperties"], False)

    def test_the_json_document_validates_against_the_emitted_schema(self):
        """The two documents must AGREE; a schema nobody's document satisfies is worthless.

        Structural validation with the stdlib (no `jsonschema` dependency): required keys present,
        the pinned `schema_version` enum honored, per-class required properties present, and the
        `additionalProperties: false` contract respected.
        """
        doc = json.loads(_run_cli("layout", "--json").stdout)["data"]["layout"]
        schema = json.loads(_run_cli("layout", "--schema").stdout)

        for key in schema["required"]:
            self.assertIn(key, doc)
        self.assertIn(
            doc["schema_version"], schema["properties"]["schema_version"]["enum"]
        )
        self.assertEqual(
            set(doc) - set(schema["properties"]),
            set(),
            "document carries a key the schema forbids (additionalProperties: false)",
        )
        for root in schema["properties"]["logical_roots"]["required"]:
            self.assertIn(root, doc["logical_roots"])
        class_required = schema["properties"]["record_classes"]["additionalProperties"][
            "required"
        ]
        for name, entry in doc["record_classes"].items():
            for key in class_required:
                self.assertIn(key, entry, f"record class {name!r} missing {key!r}")
        for tier in ("durable", "runtime"):
            self.assertIn(tier, doc["state_classes"])
        self.assertIsInstance(doc["traversal_exclusions"], list)

    def test_schema_and_json_together_are_a_usage_error(self):
        """They name two DIFFERENT documents, so combining them is exit 2, not a silent winner."""
        res = _run_cli("layout", "--schema", "--json")
        self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
        payload = json.loads(res.stdout)
        self.assertEqual(payload["exit_code"], 2)
        self.assertEqual(payload["status"], "error")

    def test_agent_output_is_ansi_free_and_exit_consistent(self):
        res = _run_cli("layout", "--agent")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertNotIn("\x1b[", res.stdout + res.stderr)
        record = json.loads(res.stdout.strip().splitlines()[-1])
        self.assertEqual(record["cmd"], "layout")
        self.assertEqual(record["exit"], res.returncode)

    def test_bad_flag_is_a_usage_error(self):
        res = _run_cli("layout", "--this-flag-does-not-exist")
        self.assertEqual(res.returncode, 2)
        self.assertIn("usage", (res.stdout + res.stderr).lower())

    def test_human_output_is_plain_when_piped_and_states_read_only(self):
        res = _run_cli("layout")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertNotIn("\x1b[", res.stdout)
        self.assertIn("Read-only", res.stdout)
        self.assertIn("Record Classes", res.stdout)


class LayoutSourceResolutionTests(_LayoutRepoCase):
    """V-01: the emitted file is READ when present, and its absence is tolerated (D3)."""

    def test_reads_the_emitted_document_when_present(self):
        repo = self.installed
        self.assertTrue(
            (repo / LAYOUT_JSON).is_file(), "install did not emit the layout document"
        )
        res = _run_cli("layout", "--repo", str(repo), "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)["data"]
        self.assertEqual(data["source"], "emitted")
        self.assertEqual(data["source_path"], str(repo / LAYOUT_JSON))
        # It must be the FILE's content, not a coincidentally-equal in-process render.
        on_disk = json.loads((repo / LAYOUT_JSON).read_text(encoding="utf-8"))
        self.assertEqual(data["layout"], on_disk)

    def test_succeeds_from_the_in_process_model_when_the_emitted_file_is_absent(self):
        """The FRESH-CLONE case: the emitted file is gitignored, so absence is normal, not an error."""
        repo = self._copy_installed("no-emitted")
        (repo / LAYOUT_JSON).unlink()
        self.assertFalse((repo / LAYOUT_JSON).exists())

        res = _run_cli("layout", "--repo", str(repo), "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)["data"]
        self.assertEqual(data["source"], "in-process")
        self.assertNotIn("source_path", data)
        # A plain absence is NOT surfaced as an error: it is the expected state.
        self.assertNotIn("emitted_error", data)
        self.assertEqual(data["layout"]["schema_version"], LAYOUT.SCHEMA_VERSION)

    def test_succeeds_in_a_repo_with_no_aw_workspace_at_all(self):
        """Not merely a missing FILE: a directory that was never installed must still work."""
        with tempfile.TemporaryDirectory() as tmp:
            bare = Path(tmp) / "bare"
            bare.mkdir()
            res = _run_cli("layout", "--repo", str(bare), "--json")
            self.assertEqual(res.returncode, 0, res.stderr)
            data = json.loads(res.stdout)["data"]
            self.assertEqual(data["source"], "in-process")
            # No install marker, so there is no framework version to report; the field is present
            # and EMPTY rather than absent, so a consumer never has to special-case its shape.
            self.assertEqual(data["layout"]["framework_version"], "")

    def test_an_unparseable_emitted_file_falls_back_and_reports_why(self):
        repo = self._copy_installed("corrupt-emitted")
        (repo / LAYOUT_JSON).write_text("{not json", encoding="utf-8")
        res = _run_cli("layout", "--repo", str(repo), "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)["data"]
        self.assertEqual(data["source"], "in-process")
        # A file that EXISTS but could not be used IS reported, unlike a plain absence.
        self.assertIn("emitted_error", data)
        self.assertIn("invalid JSON", data["emitted_error"])

    def test_schema_is_always_generated_in_process(self):
        """`--schema` must describe the RUNNING code, so a stale on-disk schema is never served."""
        repo = self._copy_installed("stale-schema")
        (repo / LAYOUT_SCHEMA).write_text('{"title": "STALE"}\n', encoding="utf-8")
        res = _run_cli("layout", "--repo", str(repo), "--schema")
        self.assertEqual(res.returncode, 0, res.stderr)
        schema = json.loads(res.stdout)
        self.assertEqual(schema["title"], "AgentWorkflowsLayout")


class LayoutIsReadOnlyTests(_LayoutRepoCase):
    """E-01: read-only is proven against the filesystem, not asserted in prose."""

    def test_no_workspace_file_changes_in_any_mode(self):
        repo = self._copy_installed("readonly")
        before = _snapshot(repo)
        for argv in (
            ["layout", "--repo", str(repo)],
            ["layout", "--repo", str(repo), "--json"],
            ["layout", "--repo", str(repo), "--agent"],
            ["layout", "--repo", str(repo), "--schema"],
        ):
            res = _run_cli(*argv)
            self.assertEqual(res.returncode, 0, f"{argv}: {res.stderr}")
        self.assertEqual(
            _snapshot(repo),
            before,
            "aw layout modified the workspace; it must be read-only",
        )

    def test_does_not_create_the_emitted_file_it_could_not_find(self):
        """A tempting 'helpful' behavior that would make the read verb an installer."""
        repo = self._copy_installed("no-write-back")
        (repo / LAYOUT_JSON).unlink()
        res = _run_cli("layout", "--repo", str(repo), "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertFalse(
            (repo / LAYOUT_JSON).exists(),
            "aw layout wrote the emitted document; emission belongs to 'aw install' only",
        )


# --------------------------------------------------------------------------------------------------
# E-02 / V-02: the workspace health rules
# --------------------------------------------------------------------------------------------------


class SystemLayoutRuleRegistrationTests(unittest.TestCase):
    """Both rules are REGISTERED, so their severity is a decision rather than a default."""

    def test_both_rules_are_registered_as_warnings(self):
        for rule in ("check.system-layout-missing", "check.system-layout-drift"):
            spec = CE.RULE_REGISTRY.get(rule)
            self.assertIsNotNone(spec, f"{rule} is not in RULE_REGISTRY")
            assert spec is not None  # narrow for type-checkers
            # `warning` is DELIBERATE (DECISION 05-30jug9-D1): the remedy is mechanical
            # ("run an install") rather than a malformed human-authored record. It is still LOUD,
            # which the next test proves against `drift_exit_code` rather than by assumption.
            self.assertEqual(spec.severity, "warning", f"{rule} severity changed")
            self.assertEqual(spec.assurance, CE.ASSURANCE_REPOSITORY)
            self.assertEqual(spec.determinism, CE.DET_DETERMINISTIC)

    def test_warning_severity_still_fails_the_gate(self):
        """`warning` is not advisory: only `info` is. This is what makes the rule a real backstop."""
        from agent_workflows import artifact_core as core

        for rule in ("check.system-layout-missing", "check.system-layout-drift"):
            drift = CE.enrich_drift(core.Drift(LAYOUT_JSON, rule, "x"))
            self.assertEqual(
                core.drift_exit_code([drift]), 1, f"{rule} did not fail the gate"
            )


class SystemLayoutRuleStateTests(_LayoutRepoCase):
    """V-02: the four workspace states, each asserted separately."""

    def test_a_clean_installed_workspace_reports_nothing(self):
        self.assertEqual(CE.check_system_layout(self.installed), [])

    def test_a_repo_with_no_aw_workspace_reports_nothing(self):
        """THE FRESH-CLONE GUARANTEE. Removing the install-marker gate breaks only this test."""
        with tempfile.TemporaryDirectory() as tmp:
            bare = Path(tmp) / "bare"
            bare.mkdir()
            self.assertFalse((bare / VERSION_MARKER).exists())
            self.assertEqual(
                CE.check_system_layout(bare),
                [],
                "the layout rule fired on a repo that was never installed; every fresh clone "
                "would fail 'aw check' by design",
            )

    def test_an_installed_workspace_missing_the_document_reports_missing(self):
        repo = self._copy_installed("missing-doc")
        (repo / LAYOUT_JSON).unlink()
        drift = CE.check_system_layout(repo)
        self.assertEqual(len(drift), 1, drift)
        self.assertEqual(drift[0].rule, "check.system-layout-missing")
        self.assertEqual(drift[0].severity, "warning")
        self.assertEqual(drift[0].location, LAYOUT_JSON)
        # The finding must TEACH the fix, since the file is gitignored and has no diff to read.
        self.assertIn("aw install", drift[0].recovery)

    def test_a_version_mismatched_document_reports_drift(self):
        """The ONLY way a stale emitted file is detectable: it is gitignored, so there is no diff."""
        repo = self._copy_installed("stale-version")
        doc = json.loads((repo / LAYOUT_JSON).read_text(encoding="utf-8"))
        doc["framework_version"] = "0.0.1-definitely-stale"
        (repo / LAYOUT_JSON).write_text(json.dumps(doc, indent=2), encoding="utf-8")
        drift = CE.check_system_layout(repo)
        self.assertEqual(len(drift), 1, drift)
        self.assertEqual(drift[0].rule, "check.system-layout-drift")
        self.assertEqual(drift[0].severity, "warning")
        self.assertIn("0.0.1-definitely-stale", drift[0].detail)
        self.assertEqual(drift[0].observed, "0.0.1-definitely-stale")
        self.assertEqual(
            drift[0].required,
            (repo / VERSION_MARKER).read_text(encoding="utf-8").strip(),
        )

    def test_a_schema_invalid_document_reports_drift(self):
        repo = self._copy_installed("schema-invalid")
        (repo / LAYOUT_JSON).write_text('{"schema_version": 1}\n', encoding="utf-8")
        drift = CE.check_system_layout(repo)
        self.assertEqual(len(drift), 1, drift)
        self.assertEqual(drift[0].rule, "check.system-layout-drift")
        self.assertIn("missing required key", drift[0].detail)

    def test_an_unparseable_document_reports_drift(self):
        repo = self._copy_installed("unparseable")
        (repo / LAYOUT_JSON).write_text("{not json", encoding="utf-8")
        drift = CE.check_system_layout(repo)
        self.assertEqual(len(drift), 1, drift)
        self.assertEqual(drift[0].rule, "check.system-layout-drift")
        self.assertIn("unusable", drift[0].detail)

    def test_a_wrong_schema_version_reports_drift(self):
        repo = self._copy_installed("wrong-schema-version")
        doc = json.loads((repo / LAYOUT_JSON).read_text(encoding="utf-8"))
        doc["schema_version"] = LAYOUT.SCHEMA_VERSION + 99
        (repo / LAYOUT_JSON).write_text(json.dumps(doc, indent=2), encoding="utf-8")
        drift = CE.check_system_layout(repo)
        self.assertEqual(len(drift), 1, drift)
        self.assertEqual(drift[0].rule, "check.system-layout-drift")
        self.assertIn("schema_version", drift[0].detail)

    def test_a_missing_schema_sibling_reports_missing(self):
        repo = self._copy_installed("missing-schema")
        (repo / LAYOUT_SCHEMA).unlink()
        drift = CE.check_system_layout(repo)
        self.assertEqual(len(drift), 1, drift)
        self.assertEqual(drift[0].rule, "check.system-layout-missing")
        self.assertEqual(drift[0].location, LAYOUT_SCHEMA)

    def test_the_rule_is_read_only(self):
        """A CHECK that repairs what it inspects would make its own next run pass vacuously."""
        repo = self._copy_installed("rule-readonly")
        (repo / LAYOUT_JSON).unlink()
        before = _snapshot(repo)
        CE.check_system_layout(repo)
        self.assertEqual(
            _snapshot(repo), before, "check_system_layout wrote to the workspace"
        )


class LoadEmittedLayoutTests(_LayoutRepoCase):
    """The loader shared by the inspector and the checker, so the two cannot disagree."""

    def test_absent_is_reported_as_absent_not_as_an_error(self):
        repo = self._copy_installed("loader-absent")
        (repo / LAYOUT_JSON).unlink()
        doc, err = CE.load_emitted_layout(repo)
        self.assertIsNone(doc)
        # The EXACT token matters: `aw layout` distinguishes a normal absence from a real problem
        # by comparing against it, so a reworded string silently turns a fresh clone into a warning.
        self.assertEqual(err, "absent")

    def test_a_valid_document_loads(self):
        doc, err = CE.load_emitted_layout(self.installed)
        self.assertEqual(err, "")
        self.assertIsInstance(doc, dict)
        assert doc is not None  # narrow for type-checkers
        self.assertEqual(doc["schema_version"], LAYOUT.SCHEMA_VERSION)

    def test_a_non_object_document_is_rejected(self):
        repo = self._copy_installed("loader-array")
        (repo / LAYOUT_JSON).write_text("[1, 2, 3]\n", encoding="utf-8")
        doc, err = CE.load_emitted_layout(repo)
        self.assertIsNone(doc)
        self.assertIn("not a JSON object", err)


class SystemLayoutSurfaceWiringTests(_LayoutRepoCase):
    """V-02: the rule actually reaches `aw check` and `aw doctor`, not just its own function."""

    def test_the_rule_rides_the_full_check_sweep(self):
        repo = self._copy_installed("check-sweep")
        (repo / LAYOUT_JSON).unlink()
        rules = {d.rule for d in CE.check_types(repo, ["all"])}
        self.assertIn("check.system-layout-missing", rules)

    def test_the_rule_does_not_fire_per_record_type(self):
        """A workspace-level finding emitted once per type would be eleven duplicates."""
        repo = self._copy_installed("check-per-type")
        (repo / LAYOUT_JSON).unlink()
        found = [
            d
            for d in CE.check_types(repo, ["all"])
            if d.rule.startswith("check.system-layout-")
        ]
        self.assertEqual(len(found), 1, found)
        # And a single-type check must not carry it at all: the state of a generated system file
        # is irrelevant to `aw check plans`.
        plan_rules = {d.rule for d in CE.check_types(repo, ["plans"])}
        self.assertNotIn("check.system-layout-missing", plan_rules)

    def test_doctor_reports_the_same_finding(self):
        from agent_workflows import doctor as DOC

        repo = self._copy_installed("doctor-sweep")
        (repo / LAYOUT_JSON).unlink()
        rules = {d.rule for d in DOC.probe_environment(repo).drift}
        self.assertIn("check.system-layout-missing", rules)

    def test_doctor_is_silent_on_a_clean_workspace(self):
        from agent_workflows import doctor as DOC

        rules = {d.rule for d in DOC.probe_environment(self.installed).drift}
        self.assertNotIn("check.system-layout-missing", rules)
        self.assertNotIn("check.system-layout-drift", rules)


# --------------------------------------------------------------------------------------------------
# E-03 / V-03: the union-vocabulary CLI fence
# --------------------------------------------------------------------------------------------------


class UnionVocabularyCliFenceTests(unittest.TestCase):
    """The Set added a type noun without removing one (plan PR-001; DECISION 05-30jug9-D4).

    PROVENANCE, stated plainly: `reviews` became an accepted noun in Order 02 (`zvk796`), this
    plan's declared dependency, so these are REGRESSION FENCES inherited from that Order rather
    than behavior this plan introduced. The falsifiable content is identical either way: an edit
    that drops either type fails here as well as in `wpu5zu`'s model test.
    """

    def test_check_reviews_is_an_accepted_type_noun(self):
        res = _run_cli("check", "reviews", "--agent")
        record = json.loads(res.stdout.strip().splitlines()[-1])
        self.assertEqual(record["target"], "reviews")
        self.assertNotEqual(
            record["outcome"],
            "error",
            "aw check reviews was rejected; the union vocabulary lost the 'reviews' type",
        )
        self.assertNotIn("unknown artifact type", res.stdout + res.stderr)

    def test_check_roadmaps_is_still_an_accepted_type_noun(self):
        """`roadmaps` is live and backs shipped verbs; dropping it would break a public surface."""
        res = _run_cli("check", "roadmaps", "--agent")
        record = json.loads(res.stdout.strip().splitlines()[-1])
        self.assertEqual(record["target"], "roadmaps")
        self.assertNotEqual(record["outcome"], "error")
        self.assertNotIn("unknown artifact type", res.stdout + res.stderr)

    def test_both_types_are_in_the_cli_vocabulary(self):
        from agent_workflows import artifact_types as AT

        self.assertIn("reviews", AT.ARTIFACT_TYPES)
        self.assertIn("roadmaps", AT.ARTIFACT_TYPES)
        # The model and the CLI vocabulary must be the SAME vocabulary, not two lists that agree
        # today: this is what makes `aw layout`'s output a description of real CLI behavior.
        self.assertEqual(
            tuple(AT.ARTIFACT_TYPES), LAYOUT.build_default_layout().artifact_types()
        )

    def test_an_unknown_type_is_still_rejected(self):
        """The vocabulary is CLOSED; a union is not an open set.

        The MESSAGE is asserted on the human path, not the agent one: the compact `aw.agent/v1`
        envelope deliberately carries `outcome`/`exit`/`target` and no prose summary, so grepping
        the agent stream for the message would assert something the output contract never promises.
        """
        agent = _run_cli("check", "definitely-not-a-type", "--agent")
        self.assertEqual(agent.returncode, 2)
        record = json.loads(agent.stdout.strip().splitlines()[-1])
        self.assertEqual(record["outcome"], "error")
        self.assertEqual(record["exit"], 2)

        human = _run_cli("check", "definitely-not-a-type")
        self.assertEqual(human.returncode, 2)
        self.assertIn("unknown artifact type", human.stdout + human.stderr)


if __name__ == "__main__":
    unittest.main()
