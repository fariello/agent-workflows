"""The CONTENT-LEVEL privacy boundary proof for every analytics artifact class.

runanalytics Order 10 (`9xycbh`) E-04. Stdlib unittest only.

WHY THIS FILE EXISTS INSTEAD OF AN `aw sanitize` INVOCATION, WHICH IS THE ROOT FINDING OF THIS PLAN.
The Set orchestrator requires this child's privacy scan to CONSUME the repository's own detector
rather than reimplement one, and that intent is right: a second private-data detector in
`run_analytics_*` would be exactly the drift the single-source rule forbids. But the MECHANISM the
orchestrator names cannot work here, and that was probe-verified twice, at review and again at
execution:

    `leak_sanitizer.scan_working_tree` enumerates `git ls-files` (via `_tracked_files`), and
    `.aw/records/runs/` is GITIGNORED (`.aw/.gitignore`, the `records/runs/` entry). Every cache
    entry, report, agent record, export and receipt this Set produces therefore lives in a tree
    that walk cannot see.

RE-MEASURED AT EXECUTION in a throwaway git repo: a repo whose `.aw/records/runs/analytics/facts.json`
held a fail-severity home path plus prompt text reported `tracked files: ['.aw/.gitignore']` and
`scan_working_tree findings: 0`, while `scan_text` over the identical bytes returned `handle` and
`home-path` at FAIL. Pointing the CLI at the analytics directory as its own root reports clean for
the same reason (`git ls-files` is empty there), and `--staged` cannot help because these artifacts
are never staged.

SO THIS FILE CONSUMES THE ENGINE, NOT THE WALK: `build_ruleset(repo_root)` plus
`scan_text(content, location, ruleset)` over each produced artifact's actual bytes. That honors the
single-source rule exactly (one engine, no reimplemented patterns, no second regex set) while
reading the files the walk skips by construction.

EVERY SCAN HERE IS PAIRED WITH A CONTROL, AND THAT IS NOT CEREMONY. A detector-based check with no
control cannot distinguish "clean" from "never looked", which is precisely the failure the
measurement above describes. So each artifact class is scanned twice: once as produced (expect zero
findings) and once with a canary PLANTED in the same bytes at the same location (expect findings). A
scan lacking its control is a FAILED validation, not a passing one.

AND THE DETECTOR IS CORROBORATION, NEVER THE GUARANTEE. Re-measured at execution against
`build_ruleset` + `scan_text`, of the thirteen canary classes `run_analytics_export.CANARY_CLASSES`
enumerates, exactly TWO are caught at fail severity (`filesystem-path` -> `home-path` + `handle`,
`username` -> `handle`) and ELEVEN return ZERO findings: hostname, prompt-text, response-text,
shell-command, git-remote, branch-name, commit-message, environment-secret, high-entropy-token,
spreadsheet-formula, archive-traversal. Three of the fail rules are compiled from this repository
maintainer's own tokens, so on an adopter's machine coverage is LOWER still. The guarantee for those
eleven classes is STRUCTURAL: an allowlist that refuses (cache/facts) or a construction that only
ever writes named fields (export events). Both are asserted below as structure, not as detection.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

from agent_workflows import leak_sanitizer
from agent_workflows import run_analytics
from agent_workflows import run_analytics_cache as cache_mod
from agent_workflows import run_analytics_export as export_mod
from agent_workflows import run_analytics_privacy as privacy
from agent_workflows import run_analytics_report as report_mod
from agent_workflows import run_analytics_submit as submit_mod

from tests.fixtures import run_analytics as corpus
from tests.support import REPO_ROOT


def _fail_rules(findings: list[Any]) -> list[str]:
    return sorted({f.rule for f in findings if f.severity == "fail"})


class _ArtifactFixture(unittest.TestCase):
    """A repo with a cache, a published report, an export bundle and a receipt on disk."""

    def setUp(self) -> None:
        self.maxDiff = None
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.repo = self.base / "repo"
        self.runs_root = self.repo / ".aw" / "records" / "runs"
        self.runs_root.mkdir(parents=True, exist_ok=True)
        # The RULESET comes from the real repository root, so the rules in force here are the same
        # ones CI compiles, including the maintainer-specific ones this proof must not depend on.
        self.ruleset = leak_sanitizer.build_ruleset(REPO_ROOT)

        self.run_dir = corpus.write_run(
            self.runs_root, "run-20260301T000000Z-9000001", mtime=corpus.BASE_MTIME
        )
        self.salt = privacy.load_or_create_salt(cache_mod.cache_root(self.repo))
        self.root_id = cache_mod.source_root_id(self.runs_root, salt=self.salt)
        self.report = cache_mod.update_cache(
            [self.run_dir],
            build_facts=run_analytics.build_cache_facts,
            repo=self.repo,
            root_id=self.root_id,
        )

    # --- the two halves of every check ------------------------------------------------------
    def assert_content_scans_clean(self, content: str, location: str) -> None:
        findings = leak_sanitizer.scan_text(content, location, self.ruleset)
        self.assertEqual(
            [(f.location, f.rule) for f in findings],
            [],
            f"{location} carries detector-visible sensitive content",
        )

    def assert_control_flags_a_planted_positive(
        self, content: str, location: str
    ) -> None:
        """THE CONTROL: the same invocation, over the same bytes, with a canary planted.

        Planted by APPENDING a line rather than by substitution, so the control cannot accidentally
        destroy the content under test and pass for the wrong reason.
        """

        planted = content + f'\n{{"repo": "{corpus.canary("filesystem-path")}"}}\n'
        findings = leak_sanitizer.scan_text(planted, location, self.ruleset)
        rules = _fail_rules(findings)
        self.assertIn(
            "home-path",
            rules,
            f"the control did not fire for {location}: this scan cannot distinguish a clean "
            f"artifact from one it never read, so the clean result above proves nothing",
        )

    def check_artifact(self, content: str, location: str) -> dict[str, Any]:
        """Scan an artifact AND its control, returning a pasteable record of both."""

        self.assert_content_scans_clean(content, location)
        self.assert_control_flags_a_planted_positive(content, location)
        return {
            "artifact": location,
            "bytes": len(content.encode("utf-8")),
            "findings": 0,
            "control_fired": True,
        }


class ArtifactContentScanTests(_ArtifactFixture):
    """E-04 / V-04: every safe artifact class scanned BY CONTENT, each with its control."""

    def test_cache_entry_content_scans_clean_with_a_control(self):
        path = cache_mod.entry_path(self.root_id, self.run_dir.name, self.repo)
        self.assertTrue(path.is_file(), "the cache entry was never published")
        record = self.check_artifact(
            path.read_text(encoding="utf-8"), "analytics/cache/entry.json"
        )
        self.assertGreater(record["bytes"], 0)

    def test_published_report_html_and_analysis_json_scan_clean_with_controls(self):
        published = report_mod.publish_bundle(
            report_mod.resolve_report_dir(self.repo),
            {
                report_mod.INDEX_FILENAME: "<!doctype html><html><body>ok</body></html>\n",
                "analysis.json": json.dumps(
                    self.report.to_dict(), indent=2, sort_keys=True
                )
                + "\n",
            },
            generated_label="privacy-proof",
            repo=self.repo,
        )
        self.assertTrue(published.files)
        for name in published.files:
            target = Path(published.directory) / name
            if not target.is_file():
                continue
            with self.subTest(artifact=name):
                self.check_artifact(
                    target.read_text(encoding="utf-8", errors="replace"),
                    f"analytics/report/{name}",
                )

    def test_agent_json_record_scans_clean_with_a_control(self):
        """The `aw.agent/v1` record an agent consumer reads."""

        record = {
            "schema": "aw.agent/v1",
            "command": "runs analyze",
            "status": "clean",
            "exit": 0,
            "data": self.report.to_dict(),
        }
        self.check_artifact(
            json.dumps(record, indent=2, sort_keys=True), "analytics/agent/record.json"
        )

    def test_agent_jsonl_stream_scans_clean_with_a_control(self):
        lines = "".join(
            json.dumps(
                {"schema": "aw.agent/v1", "decision": d.to_dict()}, sort_keys=True
            )
            + "\n"
            for d in self.report.decisions
        )
        self.assertTrue(lines, "the sweep produced no decisions to stream")
        self.check_artifact(lines, "analytics/agent/stream.jsonl")

    def test_metrics_export_payload_scans_clean_with_a_control(self):
        envelope = cache_mod.load_entry(
            cache_mod.entry_path(self.root_id, self.run_dir.name, self.repo)
        )
        payload = export_mod.build_metrics_payload([envelope])
        self.check_artifact(
            json.dumps(payload, indent=2, sort_keys=True),
            "analytics/export/metrics.json",
        )

    def test_redacted_events_export_scans_clean_with_a_control(self):
        envelope = cache_mod.load_entry(
            cache_mod.entry_path(self.root_id, self.run_dir.name, self.repo)
        )
        payload = export_mod.build_redacted_events([envelope])
        self.check_artifact(
            json.dumps(payload, indent=2, sort_keys=True),
            "analytics/export/events-redacted.json",
        )

    def test_written_export_bundle_every_file_scans_clean_with_controls(self):
        envelope = cache_mod.load_entry(
            cache_mod.entry_path(self.root_id, self.run_dir.name, self.repo)
        )
        bundle = export_mod.write_bundle(
            self.base / "bundle",
            tier="metrics",
            payload=export_mod.build_metrics_payload([envelope]),
            sanitizer_report=export_mod.sanitizer_blind_spot_report(
                [json.dumps(export_mod.build_metrics_payload([envelope]))],
                repo_root=REPO_ROOT,
            ),
        )
        scanned = 0
        for entry in bundle.entries:
            target = Path(bundle.root) / entry.path
            if not target.is_file():
                continue
            with self.subTest(artifact=entry.path):
                self.check_artifact(
                    target.read_text(encoding="utf-8", errors="replace"),
                    f"analytics/export/bundle/{entry.path}",
                )
                scanned += 1
        self.assertGreater(scanned, 0, "the bundle contained no scannable file")

    def test_diagnostics_text_scans_clean_with_a_control(self):
        """A diagnostic is the SECOND most likely leak, because interpolating the offending path is
        the natural way to report a failure. `redact_text` is the path that makes one safe."""

        hostile = f"could not read {corpus.canary('filesystem-path')}/state.json"
        before = _fail_rules(leak_sanitizer.scan_text(hostile, "diag", self.ruleset))
        self.assertIn(
            "home-path", before, "the control input was not itself detectable"
        )
        redacted = privacy.redact_text(hostile, salt=self.salt)
        self.assert_content_scans_clean(redacted, "analytics/diagnostics/message.txt")

    def test_submission_receipt_scans_clean_with_a_control(self):
        receipt = submit_mod.build_receipt(
            tier="metrics",
            destination="https://example.invalid/ingest/path?token=shouldnotappear",
            status="refused",
            total_bytes=1234,
            auth_env_var="AW_ANALYTICS_TOKEN",
            detail="no consent recorded",
        )
        text = json.dumps(receipt, indent=2, sort_keys=True)
        self.check_artifact(text, "analytics/submit/receipt.json")
        # The receipt records a credential by NAME and never a value, asserted explicitly because a
        # receipt is a file that outlives the command and gets pasted into bug reports.
        self.assertFalse(receipt["auth_value_recorded"])
        self.assertNotIn(
            "shouldnotappear", text, "the receipt kept the destination's query string"
        )


class StructuralExclusionTests(_ArtifactFixture):
    """E-04 / V-04: the ELEVEN detector-blind classes are excluded STRUCTURALLY, not by detection."""

    def test_the_detector_covers_two_of_thirteen_classes_re_measured_here(self):
        """RE-MEASURED rather than cited, because the plan requires every number re-derived.

        This test is the measurement. If a future ruleset catches more, it FAILS and the
        documentation's blind-spot list must be updated with it, which is the intended coupling.
        """

        caught: list[str] = []
        blind: list[str] = []
        for kind, value in corpus.canary_values().items():
            findings = leak_sanitizer.scan_text(value, f"canary/{kind}", self.ruleset)
            (caught if _fail_rules(findings) else blind).append(kind)
        self.assertEqual(
            sorted(caught),
            sorted(export_mod.DETECTOR_COVERED_CLASSES),
            f"measured detector coverage changed: caught={sorted(caught)}, "
            f"declared={sorted(export_mod.DETECTOR_COVERED_CLASSES)}",
        )
        self.assertEqual(
            sorted(blind),
            sorted(export_mod.DETECTOR_BLIND_SPOTS),
            f"measured blind spots changed: blind={sorted(blind)}, "
            f"declared={sorted(export_mod.DETECTOR_BLIND_SPOTS)}",
        )
        self.assertEqual(len(caught), 2)
        self.assertEqual(len(blind), 11)

    def test_every_blind_class_is_refused_by_the_write_side_allowlist(self):
        """THE GUARANTEE for the eleven. An unnamed key RAISES rather than being dropped.

        So a canary under any name the allowlist does not carry cannot reach a cache envelope at
        all, which holds identically for a class no pattern would have matched.
        """

        for kind in export_mod.DETECTOR_BLIND_SPOTS:
            with self.subTest(canary=kind):
                key = f"leaked_{kind.replace('-', '_')}"
                self.assertNotIn(key, privacy.ALLOWED_METRIC_KEYS)
                with self.assertRaises(privacy.PrivacyRefusal):
                    privacy.project_metric_facts({key: corpus.canary(kind)})

    def test_every_blind_class_is_dropped_by_the_export_field_construction(self):
        """The export tier's guarantee is a CONSTRUCTION: it iterates the allowlist and copies only
        named fields, so there is no path by which an unnamed key is written."""

        class _Env:
            run_id = "run-x"
            source_root_id = "root-x"
            event_facts: list[dict[str, Any]] = []

        env = _Env()
        env.event_facts = [
            {
                "event_type": "turn",
                **{
                    f"leaked_{kind.replace('-', '_')}": corpus.canary(kind)
                    for kind in export_mod.DETECTOR_BLIND_SPOTS
                },
            }
        ]
        payload = export_mod.build_redacted_events([env])
        text = json.dumps(payload, sort_keys=True)
        for kind in export_mod.DETECTOR_BLIND_SPOTS:
            with self.subTest(canary=kind):
                self.assertNotIn(
                    corpus.canary(kind), text, f"{kind} survived the field allowlist"
                )
        self.assertEqual(payload["redaction_method"], "structural-field-allowlist")
        self.assertEqual(len(payload["dropped_field_names"]), 11)

    def test_the_structural_exclusion_holds_for_a_class_the_detector_cannot_see(self):
        """A worked negative: prompt text is invisible to the detector AND structurally excluded.

        Asserted TOGETHER, because the pair is the whole argument: detection alone would report this
        canary as clean while it sat in the output.
        """

        prompt = corpus.canary("prompt-text")
        self.assertEqual(
            _fail_rules(
                leak_sanitizer.scan_text(prompt, "canary/prompt", self.ruleset)
            ),
            [],
            "the detector now sees prompt text; update the blind-spot documentation",
        )
        with self.assertRaises(privacy.PrivacyRefusal):
            privacy.project_metric_facts({"prompt_text": prompt})


class WhyTheCliWalkCannotSubstituteTests(unittest.TestCase):
    """E-04 / V-04: the measurement that forced the engine-level scan, reproduced not cited."""

    def test_scan_working_tree_reports_clean_over_a_gitignored_analytics_artifact(self):
        """THE PROBE. A fail-severity home path in an analytics artifact is invisible to the walk.

        Built as a throwaway git repo so the finding rests on reproduced behavior rather than on a
        review note. If this ever FAILS, the walk became able to see the tree and this plan's whole
        mechanism argument should be revisited.
        """

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".aw" / "records" / "runs" / "analytics").mkdir(parents=True)
            (root / ".aw" / ".gitignore").write_text(
                "records/runs/\n", encoding="utf-8"
            )
            artifact = root / ".aw" / "records" / "runs" / "analytics" / "facts.json"
            artifact.write_text(
                json.dumps(
                    {
                        "repo": corpus.canary("filesystem-path"),
                        "prompt": corpus.canary("prompt-text"),
                    }
                ),
                encoding="utf-8",
            )
            for cmd in (
                ["git", "init", "-q", "."],
                ["git", "add", ".aw/.gitignore"],
                [
                    "git",
                    "-c",
                    "user.email=a@b",
                    "-c",
                    "user.name=a",
                    "commit",
                    "-qm",
                    "init",
                ],
            ):
                subprocess.run(cmd, cwd=root, check=True, capture_output=True)

            tracked = leak_sanitizer._tracked_files(root)
            self.assertNotIn(
                ".aw/records/runs/analytics/facts.json",
                tracked,
                "the analytics artifact is tracked in this probe, so the probe is misconstructed",
            )
            walk_findings = leak_sanitizer.scan_working_tree(root)
            self.assertEqual(
                [(f.location, f.rule) for f in walk_findings],
                [],
                "the walk now sees gitignored files; re-evaluate this plan's mechanism",
            )

            # The SAME bytes, through the SAME engine, at the content level: FAIL.
            ruleset = leak_sanitizer.build_ruleset(root)
            content_findings = leak_sanitizer.scan_text(
                artifact.read_text(encoding="utf-8"), "analytics/facts.json", ruleset
            )
            self.assertIn("home-path", _fail_rules(content_findings))

    def test_the_analytics_tree_as_its_own_root_also_reports_clean(self):
        """The obvious workaround does not work either: `git ls-files` is empty there."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            root.mkdir(exist_ok=True)
            (root / "facts.json").write_text(
                json.dumps({"repo": corpus.canary("filesystem-path")}), encoding="utf-8"
            )
            subprocess.run(
                ["git", "init", "-q", "."], cwd=root, check=True, capture_output=True
            )
            self.assertEqual(leak_sanitizer._tracked_files(root), [])
            self.assertEqual(leak_sanitizer.scan_working_tree(root), [])


if __name__ == "__main__":
    unittest.main()
