"""Tests for the data-driven research model vocabulary (IPD t38a4o, Set modelvocab).

All tests test observable behavior and outcomes:
- E-01 seed equivalence
- Three-layer additive merge (add-only, no deletion)
- E-10 two-repo root scoping + no-root package-default case
- E-03 single-read cache and explicit invalidation
- Unknown-token warning containing `aw research add-model`
- Hyphen admitted verbatim and malformed tokens refused
- F-5 artifact_adopt facet detector regression guard
- End-to-end aw research index manifest generation without F-2 outage
- Advisory info-severity drift in --check exiting 0 vs real drift exiting 1
- Zero undeclared parser leaves after E-08 add-model
- aw research add-model round trip including --normalize-from and dry-run preview
"""

from __future__ import annotations

import argparse
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import artifact_adopt as _adopt
from agent_workflows import artifact_core as _core
from agent_workflows import cli
from agent_workflows import command_surface as _cs
from agent_workflows import model_vocab as _mv
from agent_workflows import research_cmd as _rc
from agent_workflows import research_contract as _contract
from agent_workflows import research_index as _ri

EXPECTED_HEAD_MODELS = frozenset(
    {
        "gemini31pro",
        "gemini31prodeepthink",
        "gemini31prohigh",
        "gemini36flash",
        "gemini38flash",
        "gemini38flashhigh",
        "gpt56",
        "gpt56high",
        "gpt56medium",
        "gpt56solhigh",
        "reconciliation",
        "sonnet5",
        "sonnet5high",
    }
)

EXPECTED_HEAD_NORMALIZATIONS = {
    "chatgpt": "gpt56",
    "gemini-31-pro": "gemini31pro",
    "gemini-31-pro-deep-think": "gemini31prodeepthink",
    "gemini-31-pro-high": "gemini31prohigh",
    "gemini-36-flash": "gemini36flash",
    "gemini-38-flash": "gemini38flash",
    "gemini-38-flash-high": "gemini38flashhigh",
    "gemini31pro-deep-think": "gemini31prodeepthink",
    "gemini31pro-high": "gemini31prohigh",
    "gemini31prodeepthink-high": "gemini31prodeepthink",
    "gemini38flash-high": "gemini38flashhigh",
    "gpt-56": "gpt56",
    "gpt-56-high": "gpt56high",
    "gpt-56-medium": "gpt56medium",
    "gpt-56-sol-high": "gpt56solhigh",
    "gpt56-high": "gpt56high",
    "gpt56-medium": "gpt56medium",
    "gpt56-sol-high": "gpt56solhigh",
    "gpt56sol-high": "gpt56solhigh",
    "sonnet-5": "sonnet5",
    "sonnet-5-high": "sonnet5high",
    "sonnet5-high": "sonnet5high",
}


def _create_research_doc(
    repo_root: Path,
    *,
    set_id: str,
    order: int,
    id6: str,
    slug: str,
    model: str | None,
    kind: str = "research-report",
    status: str = "todo",
    date_str: str = "20260901",
    corrupt_frontmatter: bool = False,
) -> Path:
    findings_dir = repo_root / ".aw" / "records" / "research" / "findings"
    findings_dir.mkdir(parents=True, exist_ok=True)
    name = _contract.ResearchName(
        date=date_str,
        set_id=set_id,
        order=f"{order:02d}",
        id6=id6,
        slug=slug,
        model=model,
        kind=kind,
    )
    filename = _contract.format_name(name)
    if corrupt_frontmatter:
        content = "---\ninvalid_yaml: [unclosed\n---\nBody\n"
    else:
        content = (
            _rc.build_frontmatter(
                id6=id6,
                created=date_str,
                set_id=set_id,
                order=f"{order:02d}",
                topic=["test"],
                model=model,
                kind=kind,
                status=status,
                outcome="none-yet",
                summary=f"summary for {id6}",
            )
            + f"# Title\n\nContent for {id6}\n"
        )
    doc_path = findings_dir / filename
    _core.atomic_write(doc_path, content)
    return doc_path


class TestModelVocab(unittest.TestCase):
    def setUp(self):
        _mv.invalidate_cache()

    def tearDown(self):
        _mv.invalidate_cache()

    def test_01_seed_equivalence(self):
        """E-01 / V-01: seed package data file matches expected HEAD vocabulary."""
        models, norms = _mv.load(None)
        self.assertEqual(models, EXPECTED_HEAD_MODELS)
        self.assertEqual(norms, EXPECTED_HEAD_NORMALIZATIONS)
        self.assertEqual(len(models), 13)
        self.assertEqual(len(norms), 22)

    def test_02_three_layer_additive_merge(self):
        """E-02 / V-02: three layers merge additively; package tokens cannot be deleted."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            user_dir = Path(td) / "user_cfg"
            root.mkdir()
            user_dir.mkdir()

            # Repo layer
            repo_cfg = root / ".aw" / "config" / "research-models.toml"
            repo_cfg.parent.mkdir(parents=True, exist_ok=True)
            repo_cfg.write_text(
                'models = ["deepseek4"]\n\n[normalizations]\n"deep-seek-4" = "deepseek4"\n',
                encoding="utf-8",
            )

            # User layer
            user_cfg = user_dir / "research-models.toml"
            user_cfg.write_text(
                'models = ["llama99"]\n\n[normalizations]\n"llama-99" = "llama99"\n',
                encoding="utf-8",
            )

            models, norms = _mv.load(root, user_config_dir=user_dir)
            self.assertIn("deepseek4", models)
            self.assertIn("llama99", models)
            self.assertIn("sonnet5", models)  # Package default preserved
            self.assertEqual(norms.get("deep-seek-4"), "deepseek4")
            self.assertEqual(norms.get("llama-99"), "llama99")
            self.assertEqual(norms.get("gpt-56"), "gpt56")  # Package norm preserved

            # Confirm no package tokens were lost (set difference is empty)
            missing_pkg = EXPECTED_HEAD_MODELS - models
            self.assertEqual(missing_pkg, frozenset())

    def test_03_two_repo_root_scoping_and_no_root(self):
        """E-10 / V-10: repo root is explicitly scoped, never inferred from cwd."""
        with tempfile.TemporaryDirectory() as td:
            repo_a = Path(td) / "repo_a"
            repo_b = Path(td) / "repo_b"
            repo_a.mkdir()
            repo_b.mkdir()

            cfg_a = repo_a / ".aw" / "config" / "research-models.toml"
            cfg_a.parent.mkdir(parents=True, exist_ok=True)
            cfg_a.write_text('models = ["deepseek4"]\n', encoding="utf-8")

            orig_cwd = os.getcwd()
            try:
                os.chdir(repo_a)
                # Scoped to repo_a -> recognized
                res_a = _contract.normalize_model("deepseek4", repo_root=repo_a)
                self.assertTrue(res_a.ok)
                self.assertTrue(res_a.recognized)

                # Scoped to repo_b (with cwd in repo_a) -> NOT recognized
                res_b = _contract.normalize_model("deepseek4", repo_root=repo_b)
                self.assertTrue(res_b.ok)
                self.assertFalse(res_b.recognized)

                # No root supplied -> package default only, not recognized
                res_none = _contract.normalize_model("deepseek4", repo_root=None)
                self.assertTrue(res_none.ok)
                self.assertFalse(res_none.recognized)
            finally:
                os.chdir(orig_cwd)

    def test_04_single_read_cache_and_invalidation(self):
        """E-03 / V-03: reads cached per repo root; cache invalidated on demand."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            repo.mkdir()
            cfg = repo / ".aw" / "config" / "research-models.toml"
            cfg.parent.mkdir(parents=True, exist_ok=True)
            cfg.write_text('models = ["custommodel"]\n', encoding="utf-8")

            read_counts = {"count": 0}
            real_read = _mv._read_layer_file

            def counting_read(p: Path):
                read_counts["count"] += 1
                return real_read(p)

            with patch(
                "agent_workflows.model_vocab._read_layer_file",
                side_effect=counting_read,
            ):
                for _ in range(500):
                    res = _contract.normalize_model("custommodel", repo_root=repo)
                    self.assertTrue(res.recognized)

                # Exactly 2 reads: 1 for package default, 1 for repo layer
                self.assertEqual(read_counts["count"], 2)

                # Invalidate cache for repo
                _mv.invalidate_cache(repo)
                _contract.normalize_model("custommodel", repo_root=repo)
                # Only 1 additional read for the invalidated repo
                self.assertEqual(read_counts["count"], 3)

    def test_05_unknown_token_warning_teaches_add_model(self):
        """E-05 / V-05: warning contains aw research add-model and proximity hint is subordinate."""
        res = _contract.normalize_model("deepseek4")
        self.assertTrue(res.ok)
        self.assertFalse(res.recognized)
        self.assertEqual(res.value, "deepseek4")
        self.assertIn("aw research add-model deepseek4", res.message)

        # Typo shows add-model AND spelling check hint
        res_typo = _contract.normalize_model("sonnet5hgih")
        self.assertTrue(res_typo.ok)
        self.assertFalse(res_typo.recognized)
        self.assertIn("aw research add-model sonnet5hgih", res_typo.message)
        self.assertIn("spelling check: did you mean 'sonnet5'?", res_typo.message)

    def test_06_hyphen_admitted_verbatim_and_malformed_refused(self):
        """E-05 / V-05: hyphenated token is accepted verbatim; malformed tokens are refused."""
        # Hyphen admitted verbatim
        res_hyphen = _contract.normalize_model("gemini-4-pro")
        self.assertTrue(res_hyphen.ok)
        self.assertFalse(res_hyphen.recognized)
        self.assertEqual(res_hyphen.value, "gemini-4-pro")

        # Malformed tokens refused with malformed error message
        for bad in ["gemini 4", "a.b", "gemini_4", ""]:
            res_bad = _contract.normalize_model(bad)
            self.assertFalse(res_bad.ok)
            self.assertIn("malformed", res_bad.message)

    def test_07_artifact_adopt_detector_regression(self):
        """E-04 / V-04: suggest_metadata uses recognized flag, preserving facet detection."""
        # Known model is picked over trailing agy facet
        meta1 = _adopt.suggest_metadata("some-report.gemini31prohigh.agy.md", "")
        self.assertEqual(meta1.model, "gemini31prohigh")

        # Non-model facet is NOT picked as model
        meta2 = _adopt.suggest_metadata("some-report.agy.md", "")
        self.assertIsNone(meta2.model)

        # Kind facet is NOT picked as model
        meta3 = _adopt.suggest_metadata("some-report.research-report.md", "")
        self.assertIsNone(meta3.model)

        # Unknown model (gemini4pro) is not yet in recognized set, so agy is not mistakenly chosen
        meta4 = _adopt.suggest_metadata("some-report.gemini4pro.agy.md", "")
        self.assertIsNone(meta4.model)

    def test_08_research_index_eliminates_f2_manifest_outage(self):
        """E-06 / V-06 / F-20: INDEX.json is written with known, unknown, and hyphenated models."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            repo.mkdir()

            # 1. Control (known model)
            _create_research_doc(
                repo, set_id="s1", order=0, id6="aaaaaa", slug="ctrl", model="sonnet5"
            )
            # 2. Unknown model
            _create_research_doc(
                repo, set_id="s1", order=1, id6="bbbbbb", slug="unkn", model="deepseek4"
            )
            # 3. Hyphenated unknown model (F-20 guard)
            _create_research_doc(
                repo,
                set_id="s1",
                order=2,
                id6="cccccc",
                slug="hyph",
                model="gemini-4-pro",
            )

            args = argparse.Namespace(
                dir=str(repo),
                check=False,
                limit=None,
                agent=False,
                json=False,
            )
            rc = _ri.run_index(args)
            self.assertEqual(rc, 0)

            index_json = repo / ".aw" / "records" / "research" / "INDEX.json"
            self.assertTrue(index_json.is_file())
            import json

            data = json.loads(index_json.read_text(encoding="utf-8"))
            indexed_models = {doc["id6"]: doc.get("model") for doc in data}
            self.assertEqual(indexed_models["aaaaaa"], "sonnet5")
            self.assertEqual(indexed_models["bbbbbb"], "deepseek4")
            self.assertEqual(indexed_models["cccccc"], "gemini-4-pro")

    def test_09_check_drift_info_severity_exit_behavior(self):
        """E-07 / V-07 / F-21: unrecognized-model drift is info severity and exits 0; real drift exits 1."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            repo.mkdir()

            _create_research_doc(
                repo, set_id="s1", order=0, id6="aaaaaa", slug="ctrl", model="sonnet5"
            )
            _create_research_doc(
                repo, set_id="s1", order=1, id6="bbbbbb", slug="unkn", model="deepseek4"
            )

            # Regenerate index first
            rc_regen = _ri.run_index(
                argparse.Namespace(
                    dir=str(repo), check=False, limit=None, agent=False, json=False
                )
            )
            self.assertEqual(rc_regen, 0)

            # Check index: should report unrecognized-model at info severity and exit 0
            drift = _ri.check_drift(repo, repo / ".aw" / "records" / "research")
            unrecognized_findings = [d for d in drift if d.rule == "unrecognized-model"]
            self.assertTrue(len(unrecognized_findings) > 0)
            for f in unrecognized_findings:
                self.assertEqual(f.severity, "info")

            rc_check = _ri.run_index(
                argparse.Namespace(
                    dir=str(repo), check=True, limit=None, agent=False, json=False
                )
            )
            self.assertEqual(rc_check, 0)

            # Corrupt a doc with real broken frontmatter -> exits 1
            _create_research_doc(
                repo,
                set_id="s1",
                order=2,
                id6="cccccc",
                slug="bad",
                model="sonnet5",
                corrupt_frontmatter=True,
            )
            rc_broken = _ri.run_index(
                argparse.Namespace(
                    dir=str(repo), check=True, limit=None, agent=False, json=False
                )
            )
            self.assertEqual(rc_broken, 1)

    def test_10_zero_undeclared_leaves(self):
        """E-08 / V-08: parser leaf research add-model is declared in command inventory."""
        parser = cli._build_parser()
        undeclared = _cs.find_undeclared_leaves(parser)
        self.assertEqual(undeclared, set())

    def test_11_add_model_round_trip(self):
        """E-08 / V-08: aw research add-model previews on dry run and blesses on --apply."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            repo.mkdir()
            cfg_path = repo / ".aw" / "config" / "research-models.toml"

            # Dry run: previews change, does not create file
            args_preview = argparse.Namespace(
                token="deepseek4",
                normalize_from=None,
                dir=str(repo),
                apply=False,
            )
            rc_prev = _mv.run_add_model(args_preview)
            self.assertEqual(rc_prev, 0)
            self.assertFalse(cfg_path.is_file())

            # Apply: creates file and blesses model
            args_apply = argparse.Namespace(
                token="deepseek4",
                normalize_from=None,
                dir=str(repo),
                apply=True,
            )
            rc_app = _mv.run_add_model(args_apply)
            self.assertEqual(rc_app, 0)
            self.assertTrue(cfg_path.is_file())

            # Model is now recognized in repo
            res = _contract.normalize_model("deepseek4", repo_root=repo)
            self.assertTrue(res.ok)
            self.assertTrue(res.recognized)

            # Add normalization alias with --normalize-from
            args_norm = argparse.Namespace(
                token="deepseek4",
                normalize_from="deep-seek-4",
                dir=str(repo),
                apply=True,
            )
            rc_norm = _mv.run_add_model(args_norm)
            self.assertEqual(rc_norm, 0)

            res_alias = _contract.normalize_model("deep-seek-4", repo_root=repo)
            self.assertTrue(res_alias.ok)
            self.assertTrue(res_alias.recognized)
            self.assertEqual(res_alias.value, "deepseek4")


if __name__ == "__main__":
    unittest.main()
