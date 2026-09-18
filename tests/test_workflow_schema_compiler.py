"""Tests for the canonical workflow schema + compiler (awoptimize Order 01, nmwy3m).

Covers the E-07 acceptance: schema validation (positive + every named invalid invariant), package
layout + semantic digest, strict loader (closure, traversal/symlink refusal, fail-closed, source
locations), deterministic compilation (byte-identical across two clean runs; every schema field
present across the projections), profile semantic-parity (transport-only preserves the digest;
dropping a MUST/validation/stop-condition/scope-fence is rejected), and the CLI drift check (deleting
a required resource and hand-editing a generated file each make a named assertion fail). Stdlib
unittest, matching the repository convention.
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agent_workflows import workflow_cli as CLI
from agent_workflows import workflow_compiler as COMPILER
from agent_workflows import workflow_loader as LOADER
from agent_workflows import workflow_profile as PROFILE
from agent_workflows import workflow_schema as SCHEMA
from agent_workflows import workflow_source as SOURCE
from tests.support import REPO_ROOT

FIXTURE_PKG = REPO_ROOT / "tests" / "fixtures" / "workflow-src" / "plan-review"


def _valid_workflow():
    return {
        "schema_version": SCHEMA.SCHEMA_VERSION,
        "id": "plan-review",
        "aliases": ["plan-review-long"],
        "intent": "review",
        "risk": "low",
        "interaction": "interactive",
        "mutation_boundary": "planning-only",
        "summary": "Review a plan before execution.",
        "requirements": [{"id": "R-01", "text": "verify", "evidence": ["diff"]}],
        "steps": [
            {
                "id": "S-01",
                "action": "read",
                "satisfies": ["R-01"],
                "depends_on": [],
                "evidence": ["inspection"],
            }
        ],
        "validations": [{"verifies": "R-01", "evidence": ["diff"]}],
    }


class SchemaTests(unittest.TestCase):
    """Each named schema invariant rejects its own violation, with its own finding code.

    ONE table replaces twelve tests of identical shape (take a valid workflow, break exactly one
    thing, assert one WF-E* code). The table is better than the twelve for a specific reason: these
    codes are a CLOSED SET that the loader and the CLI both surface to users, and the common failure
    mode is a renumbering or a refactor that makes the validator return a DIFFERENT code than it
    used to. Twelve separate tests report that as twelve unrelated red lines; the table reports it as
    one failure listing every code that moved, which is the shape of the actual problem.

    The positive row (an unmodified valid workflow must PASS) is deliberately in the same test. A
    validator that rejects everything would satisfy every negative row on its own.
    """

    #: (case, mutate(wf) -> None, expected WF-E code; None means "must validate CLEAN")
    CASES = (
        ("an unmodified conforming workflow", lambda wf: None, None),
        ("a non-kebab id", lambda wf: wf.update(id="Bad_ID"), "WF-E020"),
        ("an unknown intent", lambda wf: wf.update(intent="bogus"), "WF-E021"),
        ("an unknown top-level field", lambda wf: wf.update(surprise=1), "WF-E013"),
        (
            "a duplicate requirement id",
            lambda wf: wf["requirements"].append(
                {"id": "R-01", "text": "dup", "evidence": ["diff"]}
            ),
            "WF-E042",
        ),
        (
            "a step satisfying a requirement that does not exist",
            lambda wf: wf["steps"][0].update(satisfies=["R-99"]),
            "WF-E055",
        ),
        (
            "a step depending on itself",
            lambda wf: wf["steps"][0].update(depends_on=["S-01"]),
            "WF-E057",
        ),
        (
            "a forbidden terminal action (push)",
            lambda wf: wf["steps"][0].update(terminal_action="push"),
            "WF-E05B",
        ),
        (
            "a read-only workflow that also declares writable paths",
            lambda wf: wf.update(
                risk="read-only",
                mutation_boundary="none",
                permissions={"allowed_paths": ["src/**"]},
            ),
            "WF-E033",
        ),
        (
            "a requirement with no validation verifying it",
            lambda wf: wf.update(validations=[]),
            "WF-E064",
        ),
        (
            "an unknown evidence kind",
            lambda wf: wf["requirements"][0].update(evidence=["telepathy"]),
            "WF-E045",
        ),
    )

    def test_every_named_invariant_rejects_its_own_violation(self):
        wrong = []
        for case, mutate, expected in self.CASES:
            wf = _valid_workflow()
            mutate(wf)
            result = SCHEMA.validate_workflow(wf)
            codes = {f.code for f in result.findings}
            if expected is None:
                if not result.ok:
                    wrong.append(
                        f"  {case}: must VALIDATE CLEAN but was rejected with {sorted(codes)}. "
                        "Every negative row is vacuous while this row is broken, because a "
                        "validator that rejects everything satisfies all of them"
                    )
            elif expected not in codes:
                wrong.append(
                    f"  {case}: expected code {expected!r}, got "
                    f"{sorted(codes) or 'no findings at all (it validated clean)'}"
                )
        self.assertEqual(
            wrong,
            [],
            f"workflow_schema.validate_workflow mishandled {len(wrong)} of {len(self.CASES)} "
            "invariants. The WF-E* codes are a closed set surfaced to users by the loader and the "
            "CLI, so several rows moving together usually means a renumbering rather than several "
            f"independent breakages:\n" + "\n".join(wrong),
        )

    def test_a_dependency_cycle_between_two_steps_is_rejected(self):
        """Kept out of the table: it needs a whole replacement step list, not a one-field edit."""
        wf = _valid_workflow()
        wf["steps"] = [
            {
                "id": "S-01",
                "action": "a",
                "satisfies": ["R-01"],
                "depends_on": ["S-02"],
                "evidence": ["inspection"],
            },
            {
                "id": "S-02",
                "action": "b",
                "satisfies": ["R-01"],
                "depends_on": ["S-01"],
                "evidence": ["inspection"],
            },
        ]
        codes = {f.code for f in SCHEMA.validate_workflow(wf).findings}
        self.assertIn(
            "WF-E05C",
            codes,
            f"a two-step dependency cycle must be rejected with WF-E05C; got {sorted(codes)}",
        )


class SourceLayoutTests(unittest.TestCase):
    def test_fixture_entry_parses_and_validates(self):
        data = SOURCE.parse_entry(FIXTURE_PKG)
        self.assertTrue(SCHEMA.validate_workflow(data).ok)

    def test_digest_is_stable(self):
        self.assertEqual(
            SOURCE.semantic_digest(FIXTURE_PKG), SOURCE.semantic_digest(FIXTURE_PKG)
        )

    def test_digest_ignores_generated_and_cruft(self):
        with _clone(FIXTURE_PKG) as pkg:
            base = SOURCE.semantic_digest(pkg)
            (pkg / SOURCE.GENERATED_DIRNAME).mkdir()
            (pkg / SOURCE.GENERATED_DIRNAME / "x.json").write_text("{}")
            (pkg / "steps" / "__pycache__").mkdir()
            (pkg / "steps" / "__pycache__" / "x.pyc").write_bytes(b"\x00")
            self.assertEqual(SOURCE.semantic_digest(pkg), base)

    def test_digest_changes_on_authoritative_edit(self):
        with _clone(FIXTURE_PKG) as pkg:
            base = SOURCE.semantic_digest(pkg)
            p = pkg / "protocol.md"
            p.write_text(p.read_text() + "\nmore\n")
            self.assertNotEqual(SOURCE.semantic_digest(pkg), base)

    def test_symlink_is_refused(self):
        with _clone(FIXTURE_PKG) as pkg:
            link = pkg / "evil"
            try:
                link.symlink_to("/etc/hostname")
            except OSError:
                self.skipTest("symlinks not supported on this platform")
            with self.assertRaises(SOURCE.SourceError):
                SOURCE.semantic_digest(pkg)


class LoaderTests(unittest.TestCase):
    def test_fixture_loads_to_full_ir(self):
        r = LOADER.load_package(FIXTURE_PKG)
        self.assertTrue(r.ok, r.findings)
        self.assertIsNotNone(r.ir)
        self.assertEqual(
            sorted(r.ir["resources"].keys()),
            ["protocol.md", "steps/01-scope.md", "steps/02-review.md"],
        )
        self.assertEqual(r.ir["digest"], SOURCE.semantic_digest(FIXTURE_PKG))

    def test_deleting_required_resource_fails_closed(self):
        # E-07 acceptance: deleting a referenced resource makes the load fail with NO ir.
        with _clone(FIXTURE_PKG) as pkg:
            (pkg / "steps" / "02-review.md").unlink()
            r = LOADER.load_package(pkg)
            self.assertFalse(r.ok)
            self.assertIsNone(r.ir)
            self.assertIn("WF-L013", {f.code for f in r.findings})

    def test_traversal_resource_rejected(self):
        with _clone(FIXTURE_PKG) as pkg:
            y = (
                (pkg / "workflow.yaml")
                .read_text()
                .replace("  - protocol.md", "  - ../../etc/hostname")
            )
            (pkg / "workflow.yaml").write_text(y)
            r = LOADER.load_package(pkg)
            self.assertFalse(r.ok)
            self.assertIn("WF-L010", {f.code for f in r.findings})

    def test_schema_finding_carries_provenance(self):
        with _clone(FIXTURE_PKG) as pkg:
            y = (
                (pkg / "workflow.yaml")
                .read_text()
                .replace("intent: review", "intent: bogus")
            )
            (pkg / "workflow.yaml").write_text(y)
            r = LOADER.load_package(pkg)
            self.assertFalse(r.ok)
            self.assertIsNone(r.ir)
            wheres = " ".join(f.where for f in r.findings)
            self.assertIn("plan-review:workflow.yaml", wheres)

    def test_missing_entry_is_invocation_finding(self):
        with tempfile.TemporaryDirectory() as d:
            r = LOADER.load_package(Path(d))
            self.assertFalse(r.ok)
            self.assertIn("WF-L001", {f.code for f in r.findings})


class CompilerTests(unittest.TestCase):
    def _compiled(self):
        ir = LOADER.load_package(FIXTURE_PKG).ir
        return ir, COMPILER.compile_workflow(ir)

    def test_all_six_projections_present(self):
        _ir, comp = self._compiled()
        self.assertEqual(sorted(comp.keys()), sorted(COMPILER.PROJECTION_KEYS))

    def test_manifest_binds_source_digest(self):
        ir, comp = self._compiled()
        self.assertEqual(comp["manifest"]["source_digest"], ir["digest"])

    def test_every_schema_field_reachable_in_projections(self):
        _ir, comp = self._compiled()
        # id, intent, risk, interaction, mutation_boundary appear in the manifest;
        # requirements + validations + evidence in the evidence projection; steps in packets.
        m = comp["manifest"]
        for f in (
            "id",
            "intent",
            "risk",
            "interaction",
            "mutation_boundary",
            "requirement_ids",
            "step_ids",
        ):
            self.assertIn(f, m)
        self.assertTrue(comp["evidence"]["requirements"])
        self.assertTrue(comp["evidence"]["validations"])
        self.assertEqual([p["step"] for p in comp["step_packets"]], ["S-01", "S-02"])

    def test_byte_identical_across_two_clean_runs(self):
        # E-04/E-07 acceptance: determinism.
        ir1 = LOADER.load_package(FIXTURE_PKG).ir
        ir2 = LOADER.load_package(FIXTURE_PKG).ir
        files1 = COMPILER.render_generated_files(COMPILER.compile_workflow(ir1))
        files2 = COMPILER.render_generated_files(COMPILER.compile_workflow(ir2))
        self.assertEqual(files1, files2)

    def test_generated_json_is_sorted_and_compact(self):
        _ir, comp = self._compiled()
        files = COMPILER.render_generated_files(comp)
        manifest_text = files["_generated/manifest.json"]
        # sorted keys => 'aliases' precedes 'id'; compact => no ", " separators
        self.assertLess(manifest_text.index('"aliases"'), manifest_text.index('"id"'))
        self.assertNotIn(", ", manifest_text)


class ProfileParityTests(unittest.TestCase):
    def _base(self):
        ir = LOADER.load_package(FIXTURE_PKG).ir
        return COMPILER.compile_workflow(ir)

    def test_transport_only_variant_preserves_semantics(self):
        base = self._base()
        variant = copy.deepcopy(base)
        variant["prompt_bundle"] += "\n<!-- profile note -->\n"
        for pkt in variant["step_packets"]:
            pkt["body"] = pkt["body"][:10]
        self.assertTrue(PROFILE.check_parity(base, variant).ok)

    def test_dropping_a_validation_is_rejected(self):
        base = self._base()
        drift = copy.deepcopy(base)
        drift["evidence"]["validations"] = drift["evidence"]["validations"][:1]
        self.assertFalse(PROFILE.check_parity(base, drift).ok)

    def test_widening_scope_fence_is_rejected(self):
        base = self._base()
        drift = copy.deepcopy(base)
        drift["command_descriptor"]["mutation_boundary"] = "product"
        r = PROFILE.check_parity(base, drift)
        self.assertFalse(r.ok)
        self.assertIn("scope_fence", r.reason)

    def test_changing_step_shape_is_rejected(self):
        base = self._base()
        drift = copy.deepcopy(base)
        for pkt in drift["step_packets"]:
            if pkt["step"] == "S-02":
                pkt["depends_on"] = []
        self.assertFalse(PROFILE.check_parity(base, drift).ok)

    def test_invalid_profile_key_rejected(self):
        with self.assertRaises(PROFILE.ProfileError):
            PROFILE.validate_profile({"requirements": []})

    def test_valid_transport_profile_accepted(self):
        PROFILE.validate_profile(
            {"name": "codex", "max_packet_chars": 4000, "output_format": "json"}
        )


class CliDriftTests(unittest.TestCase):
    def _run(self, argv_ns):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLI.run_workflow(argv_ns)
        return code, buf.getvalue()

    def _ns(self, sub, pkg, **kw):
        return argparse.Namespace(
            workflow_command=sub,
            path=[str(pkg)],
            agent=kw.get("agent", False),
            json=kw.get("json", False),
            apply=kw.get("apply", False),
        )

    def test_validate_clean_exit_zero(self):
        code, _out = self._run(self._ns("validate", FIXTURE_PKG))
        self.assertEqual(code, 0)

    def test_validate_bad_path_exit_two(self):
        code, _out = self._run(self._ns("validate", "/nonexistent/pkg"))
        self.assertEqual(code, 2)

    def test_compile_dry_run_writes_nothing(self):
        with _clone(FIXTURE_PKG) as pkg:
            code, _out = self._run(self._ns("compile", pkg))
            self.assertEqual(code, 0)
            self.assertFalse((pkg / SOURCE.GENERATED_DIRNAME).exists())

    def test_compile_apply_then_check_generated_clean(self):
        with _clone(FIXTURE_PKG) as pkg:
            self._run(self._ns("compile", pkg, apply=True))
            self.assertTrue(
                (pkg / SOURCE.GENERATED_DIRNAME / "manifest.json").is_file()
            )
            code, _out = self._run(self._ns("check-generated", pkg))
            self.assertEqual(code, 0)

    def test_check_generated_detects_hand_edit(self):
        # E-07 acceptance: hand-editing a generated adapter makes this named test fail (exit 1).
        with _clone(FIXTURE_PKG) as pkg:
            self._run(self._ns("compile", pkg, apply=True))
            (pkg / SOURCE.GENERATED_DIRNAME / "manifest.json").write_text(
                '{"tampered":1}\n'
            )
            code, out = self._run(self._ns("check-generated", pkg))
            self.assertEqual(code, 1)
            self.assertIn("changed", out)

    def test_check_generated_detects_unexpected_file(self):
        with _clone(FIXTURE_PKG) as pkg:
            self._run(self._ns("compile", pkg, apply=True))
            (pkg / SOURCE.GENERATED_DIRNAME / "rogue.txt").write_text("x")
            code, out = self._run(self._ns("check-generated", pkg))
            self.assertEqual(code, 1)
            self.assertIn("unexpected", out)

    def test_agent_output_is_valid_jsonl_no_ansi(self):
        code, out = self._run(self._ns("validate", FIXTURE_PKG, agent=True))
        self.assertEqual(code, 0)
        line = out.strip().splitlines()[0]
        rec = json.loads(line)  # must parse
        self.assertEqual(rec.get("schema"), "aw.agent/v1")
        self.assertEqual(rec.get("outcome"), "clean")
        self.assertNotIn("\x1b", out)  # no ANSI escapes


class _clone:
    """Context manager: copy the fixture package into a temp dir and clean up."""

    def __init__(self, src: Path):
        self.src = src
        self.tmp = None

    def __enter__(self) -> Path:
        self.tmp = Path(tempfile.mkdtemp())
        dst = self.tmp / self.src.name
        shutil.copytree(self.src, dst)
        return dst

    def __exit__(self, *exc):
        if self.tmp and self.tmp.exists():
            shutil.rmtree(self.tmp)
        return False


if __name__ == "__main__":
    unittest.main()
