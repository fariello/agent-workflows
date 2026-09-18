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

import re
import unittest
from pathlib import Path

from agent_workflows import docs_check as dc
from agent_workflows import docs_render as dr
from agent_workflows import host_adapters as ha
from agent_workflows import host_capability_registry as hcr

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"


class DocsExistTests(unittest.TestCase):
    """Every doc the tree PROMISES must be present, reported in one list.

    Three tests (dir exists / 13 docs / 5 walkthroughs) became one: they fail for the same reason
    (something referenced was moved or deleted) and the fix is the same, so a reader benefits from
    seeing the whole missing set at once rather than rediscovering it one red test per file.
    """

    REQUIRED = tuple(
        f"{d}/{n}" if d else n
        for d, names in (
            (
                "",
                (
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
                ),
            ),
            (
                "walkthroughs",
                (
                    "incomplete-run.md",
                    "evidence-inspection.md",
                    "host-probe.md",
                    "recovery.md",
                    "rollback.md",
                ),
            ),
        )
        for n in names
    )

    def test_every_required_doc_is_present(self):
        if not DOCS_DIR.is_dir():
            self.fail(f"the docs directory itself is missing: {DOCS_DIR}")
        missing = [rel for rel in self.REQUIRED if not (DOCS_DIR / rel).is_file()]
        self.assertEqual(
            missing,
            [],
            "docs promised by the tree are absent, so any link or index entry pointing at them is "
            "dead:\n  "
            + "\n  ".join(f"docs/{rel}" for rel in missing)
            + "\n  FIX: restore the file, or if it was deliberately retired, remove it from this "
            "list AND from whatever links to it (run `aw check` to find those links).",
        )


class DocCheckTests(unittest.TestCase):
    def test_no_findings_across_docs(self):
        # FALSIFIABLE: any broken link, unknown `aw` subcommand, or em/en dash is a finding.
        findings = dc.check_docs_dir(DOCS_DIR)
        self.assertEqual(findings, [], "\n".join(str(f) for f in findings))

    # NOTE: a separate `test_no_unicode_dashes_anywhere` was removed as strictly redundant.
    # `check_docs_dir` walks the same `rglob("*.md")` and calls `check_doc`, whose FIRST check is
    # `check_no_unicode_dashes`, so the assertion above already covers every dash the removed test
    # looked for. `DocCheckFalsifiabilityTests` below proves that check really fires.


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


def _bare_run_scratch_refs(text: str) -> list[str]:
    """Return every BARE `workflow-artifacts/` PATH reference in ``text``.

    THE UNIT IS OCCURRENCES, NOT LINES (wfartifacts Order 03, finding F-8): some lines carry
    two references, so a line-based sweep under-reports and reports itself complete while
    references remain.

    THREE SPELLINGS ARE DELIBERATELY NOT MATCHED, because none of them is a stale path:

    1. `.aw/workflow-artifacts/` - the live, correct path (the negative lookbehind).
    2. `/workflow-artifacts/` as the ANCHORED GITIGNORE PATTERN. Patterns in the
       framework-owned `.aw/.gitignore` are `.aw/`-relative, so the pattern that ignores run
       scratch is written `/workflow-artifacts/` and a body naming it is CORRECT. Any
       slash-preceded form is therefore allowed, which subsumes case 1.
    3. `workflow-artifacts-README.md`, the installer TEMPLATE FILENAME under
       `.aw/system/workflows/templates/` (a hyphen, not a slash, follows), plus the bare
       segment name in `assess/tools/scan_secrets.py`'s `SKIP_DIR_NAMES` (no trailing slash),
       which must stay bare because that set is matched per path SEGMENT.
    """

    return re.findall(r"(?<![/\w-])workflow-artifacts/", text)


class ShippedRunScratchPathTests(unittest.TestCase):
    """wfartifacts Order 03: no shipped workflow body may name the RETIRED run-scratch path.

    Order 07 (spec `20260817-2124-01`) moved run scratch from a repo-root `workflow-artifacts/`
    to `.aw/workflow-artifacts/`, but the shipped bodies were never updated: 86 stale references
    across 25 files, and two of them (`assess/assess.md`) actively asserted the retired path was
    gitignored when nothing ignored it in a target repo. An agent that trusts such a sentence
    writes local context (absolute home paths, session detail) into TRACKED working material,
    which is the D92 leak this guard exists to prevent recurring.

    This test is the regression pin: without it, the rewrite decays exactly as Order 07's did.
    """

    WORKFLOWS_DIR = REPO_ROOT / ".aw" / "system" / "workflows"

    def _shipped_bodies(self):
        for suffix in ("*.md", "*.py"):
            for path in sorted(self.WORKFLOWS_DIR.rglob(suffix)):
                # `__pycache__` holds compiled build output, not editable shipped bodies;
                # counting it once inflated this surface from 25 files to 28 (finding F-7).
                if "__pycache__" in path.parts:
                    continue
                yield path

    def test_shipped_dir_exists(self):
        self.assertTrue(self.WORKFLOWS_DIR.is_dir(), self.WORKFLOWS_DIR)

    def test_no_bare_run_scratch_path_in_shipped_bodies(self):
        offenders: list[str] = []
        scanned = 0
        for path in self._shipped_bodies():
            scanned += 1
            hits = _bare_run_scratch_refs(path.read_text(encoding="utf-8"))
            if hits:
                rel = path.relative_to(REPO_ROOT).as_posix()
                offenders.append(f"{rel}: {len(hits)} bare reference(s)")
        self.assertTrue(scanned, "no shipped bodies were scanned")
        self.assertEqual(
            offenders,
            [],
            "shipped workflow bodies name the RETIRED repo-root run-scratch path; "
            "write `.aw/workflow-artifacts/` instead:\n" + "\n".join(offenders),
        )

    def test_no_doubled_aw_prefix_in_shipped_bodies(self):
        # The mechanical hazard of the sweep itself (finding F-5): re-running a substitution
        # over an already-rewritten file yields `.aw/.aw/workflow-artifacts/`.
        for path in self._shipped_bodies():
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(".aw/.aw/", text, path.relative_to(REPO_ROOT).as_posix())


class ShippedRunScratchGuardFalsifiabilityTests(unittest.TestCase):
    """The guard must FAIL on a reintroduced reference; one that cannot fail proves nothing."""

    def test_detects_reintroduced_bare_reference(self):
        self.assertEqual(
            _bare_run_scratch_refs(
                "Write the run record to `workflow-artifacts/assess-security/<RUN_ID>/`."
            ),
            ["workflow-artifacts/"],
        )

    def test_detects_two_references_on_one_line(self):
        # The F-8 unit error: a line-based check would count this once and miss a rewrite.
        self.assertEqual(
            len(
                _bare_run_scratch_refs(
                    "Do NOT commit workflow-artifacts/ and never force-add workflow-artifacts/ either."
                )
            ),
            2,
        )

    def test_allows_the_live_prefixed_path(self):
        self.assertEqual(
            _bare_run_scratch_refs("Run records live under `.aw/workflow-artifacts/`."),
            [],
        )

    def test_allows_the_anchored_gitignore_pattern(self):
        self.assertEqual(
            _bare_run_scratch_refs(
                "`.aw/.gitignore` carries the anchored pattern `/workflow-artifacts/`."
            ),
            [],
        )

    def test_allows_the_installer_template_filename(self):
        self.assertEqual(
            _bare_run_scratch_refs("`workflow-artifacts-README.md` is a template."), []
        )

    def test_allows_the_bare_segment_name_used_as_code(self):
        # scan_secrets.py's SKIP_DIR_NAMES holds path SEGMENTS, which carry no slash.
        self.assertEqual(_bare_run_scratch_refs('    "workflow-artifacts",'), [])


class BenchmarkThresholdTableTests(unittest.TestCase):
    def test_renders_invariants_from_policy(self):
        table = dr.render_benchmark_thresholds_table()
        self.assertIn("Source: benchmark threshold policy", table)
        # Every risk class must show 0 critical escapes and 1.0 evidence validity.
        self.assertIn("destructive_gated", table)
        self.assertIn("| 0 | 1.0 |", table)


if __name__ == "__main__":
    unittest.main()
