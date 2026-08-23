"""Documentation checks + registry-rendered tables for awoptimize Order 18 E-01 / E-02.

E-01: the documentation link/command/option checks pass over the whole `docs/` set, and the
user-facing prose contains NO em/en dashes (ASCII only).

E-02: the support and model-profile tables render FROM the registries (a support cell is
'supported' only where the registry promoted it, else 'unverified'; the model-profile table
keeps the model ID distinct from the profile and records benchmark date, corpus, host/version,
uncertainty, and pending combinations). No table asserts an unproven generalization.

Stdlib ``unittest`` (repository convention).
"""

from __future__ import annotations

import unittest
from pathlib import Path

from agent_workflows import docs_check as dc
from agent_workflows import docs_render as dr
from agent_workflows import host_adapters as ha
from agent_workflows import host_capability_registry as hcr

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"


class DocsExistTests(unittest.TestCase):
    def test_docs_dir_exists(self):
        self.assertTrue(DOCS_DIR.is_dir())

    def test_required_docs_present(self):
        for name in (
            "README.md",
            "architecture.md",
            "authoring.md",
            "skill-selection.md",
            "orchestration.md",
            "evidence.md",
            "verification.md",
            "benchmark.md",
            "host-adapters.md",
            "model-profiles.md",
            "security.md",
            "troubleshooting.md",
            "recovery.md",
        ):
            self.assertTrue((DOCS_DIR / name).is_file(), name)

    def test_walkthroughs_present(self):
        wdir = DOCS_DIR / "walkthroughs"
        for name in (
            "incomplete-run.md",
            "evidence-inspection.md",
            "host-probe.md",
            "recovery.md",
            "rollback.md",
        ):
            self.assertTrue((wdir / name).is_file(), name)


class DocCheckTests(unittest.TestCase):
    def test_no_findings_across_docs(self):
        # FALSIFIABLE: any broken link, unknown `aw` subcommand, or em/en dash is a finding.
        findings = dc.check_docs_dir(DOCS_DIR)
        self.assertEqual(findings, [], "\n".join(str(f) for f in findings))

    def test_no_unicode_dashes_anywhere(self):
        for md in DOCS_DIR.rglob("*.md"):
            text = md.read_text(encoding="utf-8")
            self.assertNotIn(dc.EM_DASH, text, f"em dash in {md.name}")
            self.assertNotIn(dc.EN_DASH, text, f"en dash in {md.name}")


class DocCheckFalsifiabilityTests(unittest.TestCase):
    def test_detects_em_dash(self):
        findings = dc.check_no_unicode_dashes("a \u2014 b", "x.md")
        self.assertTrue(findings)

    def test_detects_unknown_command(self):
        findings = dc.check_aw_commands("run `aw florb` please", ["run", "ipd"], "x.md")
        self.assertTrue(findings)

    def test_detects_broken_link(self):
        import tempfile

        base = Path(tempfile.mkdtemp(prefix="aw-doccheck-"))
        try:
            doc = base / "a.md"
            doc.write_text("see [missing](./nope.md)\n", encoding="utf-8")
            findings = dc.check_internal_links(doc.read_text(encoding="utf-8"), doc)
            self.assertTrue(findings)
        finally:
            import shutil

            shutil.rmtree(base, ignore_errors=True)


class SupportTableRendersFromRegistryTests(unittest.TestCase):
    def test_unpromoted_capability_renders_unverified(self):
        # Build adapters against an EMPTY registry: everything must render 'unverified'.
        registry = hcr.HostCapabilityRegistry()
        adapters = {
            h: ha.build_host_adapter(h, registry, "1.0.0") for h in ha.ALL_ADAPTER_HOSTS
        }
        table = dr.render_support_table(adapters)
        self.assertIn("Source: host capability-evidence registry", table)
        # No feature was promoted, so no row may claim 'supported'.
        for line in table.splitlines():
            if line.startswith("| ") and " supported " in f" {line} ":
                self.fail(f"unpromoted capability claimed supported: {line}")

    def test_provenance_line_present(self):
        registry = hcr.HostCapabilityRegistry()
        adapters = {
            h: ha.build_host_adapter(h, registry, "1.0.0") for h in ha.ALL_ADAPTER_HOSTS
        }
        table = dr.render_support_table(adapters)
        self.assertIn(
            "A feature is 'supported' only where a live probe promoted it", table
        )


class ModelProfileTableTests(unittest.TestCase):
    def test_model_id_distinct_from_profile(self):
        table = dr.render_model_profile_table(
            [
                {
                    "model_id": "(operator-selected)",
                    "profile": {"name": "default", "reasoning_level": "medium"},
                    "notes": "baseline",
                }
            ],
            benchmark_date="2026-08-21",
            host="opencode",
            host_version="1.0.0",
            uncertainty="+/- 0.03 (n=30)",
            pending_combinations=["claude_code x max reasoning"],
        )
        # Header records provenance, and the model ID + reasoning are SEPARATE columns.
        self.assertIn("Benchmark date: 2026-08-21", table)
        self.assertIn("Task corpus:", table)
        self.assertIn("Host / version: opencode 1.0.0", table)
        self.assertIn("Measurement uncertainty:", table)
        self.assertIn("| Model ID | Profile | Reasoning config |", table)
        self.assertIn("(operator-selected)", table)
        self.assertIn("Pending", table)
        self.assertIn("claude_code x max reasoning", table)

    def test_no_universal_quality_claim(self):
        table = dr.render_model_profile_table(
            [{"model_id": "m", "profile": {"name": "p"}}],
            benchmark_date="2026-08-21",
        )
        self.assertIn("not a universal quality claim", table)

    def test_disallowed_profile_key_rejected(self):
        # FALSIFIABLE: smuggling a semantic override under an unknown profile key is rejected.
        from agent_workflows import workflow_profile as wp

        with self.assertRaises(wp.ProfileError):
            dr.render_model_profile_table(
                [
                    {
                        "model_id": "m",
                        "profile": {"name": "p", "smuggled_semantics": "x"},
                    }
                ],
                benchmark_date="2026-08-21",
            )


class BenchmarkThresholdTableTests(unittest.TestCase):
    def test_renders_invariants_from_policy(self):
        table = dr.render_benchmark_thresholds_table()
        self.assertIn("Source: benchmark threshold policy", table)
        # Every risk class must show 0 critical escapes and 1.0 evidence validity.
        self.assertIn("destructive_gated", table)
        self.assertIn("| 0 | 1.0 |", table)


if __name__ == "__main__":
    unittest.main()
