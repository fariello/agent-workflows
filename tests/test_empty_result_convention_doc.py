"""Behavioral tests guarding Section 11.1 Empty Result Convention.

Verifies the three zero-match classes published in docs/cli-output-contract.md:
1. Standing questions about repository state (vocabulary token matching zero records).
2. Assertions that a named artifact exists (bogus token matching zero records).
3. Resolving selectors in excluded trees (artifact resides under an excluded TreePolicy).

Follows GUIDING_PRINCIPLES P16: tests observable outcomes via public functions,
not code structure or source text. Uses tmp_path and derives excluded trees
from attention_contract.TREE_POLICY at test time.
"""

from __future__ import annotations

import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import agent_schema
from agent_workflows import attention as att
from agent_workflows import attention_contract as A


def _build_fixture_repo(root: Path) -> tuple[Path, A.TreePolicy, str]:
    """Construct an isolated minimal repository in tmp_path with one tracked and one excluded artifact.

    Builds an isolated repo with no dependencies on the live repository's artifact count.
    Derives the excluded tree from attention_contract.TREE_POLICY at test time.
    """
    config = root / ".aw" / "config"
    plans = root / ".aw" / "records" / "plans" / "pending"
    for d in (config, plans):
        d.mkdir(parents=True, exist_ok=True)

    (config / "project.json").write_text("{}", encoding="utf-8")

    # One tracked artifact: a pending IPD with id6 'pln001'
    (plans / "20260901-test-01-pln001-sample.ipd.md").write_text(
        "# IPD: sample plan\n\n- Status: draft\n- Id: pln001\n\n## Workflow history\n- 2026-09-01 draft (t): created.\n",
        encoding="utf-8",
    )

    # Derive excluded policy dynamically from TREE_POLICY at test time:
    excluded_policy = next(
        p
        for p in A.TREE_POLICY
        if not p.tracked and p.name in ("walkthroughs", "roadmaps")
    )
    excluded_dir = root / ".aw" / "records" / excluded_policy.name
    excluded_dir.mkdir(parents=True, exist_ok=True)
    ext = "walkthrough" if excluded_policy.name == "walkthroughs" else "roadmap"
    artifact_id6 = "ex0001"
    artifact_file = excluded_dir / f"20260901-test-01-{artifact_id6}-sample.{ext}.md"
    artifact_file.write_text(
        f"# {excluded_policy.name.capitalize()}: sample\n\n- Id: {artifact_id6}\n\nNarrative content.\n",
        encoding="utf-8",
    )

    # Fixture assertion: verify attention._classify_tree maps the artifact to the tracked=False policy
    rel_path = f".aw/records/{excluded_policy.name}/{artifact_file.name}"
    classified = att._classify_tree(rel_path)
    assert classified is not None, f"Failed to classify fixture artifact: {rel_path}"
    assert (
        not classified.tracked
    ), f"Classified policy for {rel_path} must be tracked=False"
    assert (
        classified.name == excluded_policy.name
    ), f"Expected {excluded_policy.name}, got {classified.name}"

    return root, excluded_policy, artifact_id6


def _run_attention_in_process(root: Path, **kw) -> tuple[int, str, str]:
    """Drive attention.run in-process, capturing stdout and stderr."""
    base = dict(
        dir=str(root),
        format=None,
        check=False,
        selectors=[],
        no_color=True,
        all=False,
        long=False,
        types=[],
        status=[],
        priority=[],
        blocking=[],
        readiness=[],
        open_questions=False,
        agent=False,
        json=False,
        id6_only=False,
        paths=False,
        filenames=False,
        details=False,
        order_by=None,
        runs=False,
        active=False,
        not_active=False,
        run_status=[],
        arcive_state=[],
        active_state=[],
    )
    base.update(kw)
    args = argparse.Namespace(**base)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = att.run(args)
    return rc, out.getvalue(), err.getvalue()


class EmptyResultConventionDocSection111Tests(unittest.TestCase):
    """Behavioral guard over docs/cli-output-contract.md Section 11.1."""

    def test_class1_standing_question_is_not_refused(self):
        """A vocabulary token matching nothing is not refused."""
        with tempfile.TemporaryDirectory() as td:
            root, _, _ = _build_fixture_repo(Path(td))
            voc = att.selector_vocabulary()
            standing_token = "specs"
            self.assertIn(standing_token, voc)

            rc, out, err = _run_attention_in_process(root, selectors=[standing_token])
            # Section 11.1: standing question is NOT REFUSED (do not assert flat exit 0)
            self.assertNotEqual(rc, att.EXIT_UNRESOLVED_SELECTOR)
            self.assertNotIn("no artifact matched selector", err)
            self.assertNotIn("cannot-run", err)

    def test_class2_named_artifact_assertion_is_refused(self):
        """A bogus selector asserting a named artifact is refused at EXIT_UNRESOLVED_SELECTOR."""
        with tempfile.TemporaryDirectory() as td:
            root, _, _ = _build_fixture_repo(Path(td))
            bogus_token = "definitelybogustoken123"

            rc, out, err = _run_attention_in_process(root, selectors=[bogus_token])
            # Section 11.1 / Spec 25kzda 2.4a: unresolvable named artifact is refused with exit 2
            self.assertEqual(rc, att.EXIT_UNRESOLVED_SELECTOR)
            self.assertIn(bogus_token, err)
            self.assertIn("no artifact matched selector", err)

    def test_class3_excluded_tree_human_board_is_not_refused_and_names_tree(self):
        """An excluded-tree selector is not refused and names the tree (silence guard)."""
        with tempfile.TemporaryDirectory() as td:
            root, policy, token = _build_fixture_repo(Path(td))

            rc, out, err = _run_attention_in_process(root, selectors=[token])
            # Section 11.1: NOT REFUSED
            self.assertNotEqual(rc, att.EXIT_UNRESOLVED_SELECTOR)
            combined = out + err
            # Silence guard: output must not be empty and must name the excluded tree and quote reason
            self.assertTrue(
                len(combined.strip()) > 0, "Silence guard failed: output is empty"
            )
            self.assertIn(policy.name, combined)
            self.assertIn(policy.reason, combined)
            self.assertIn(f"aw find {token}", combined)

    def test_class3_excluded_tree_agent_surface_is_not_refused_with_clean_record(self):
        """An excluded-tree selector on --agent emits a clean result record."""
        with tempfile.TemporaryDirectory() as td:
            root, policy, token = _build_fixture_repo(Path(td))

            rc, out, err = _run_attention_in_process(
                root, selectors=[token], agent=True
            )
            # Section 11.1: NOT REFUSED
            self.assertNotEqual(rc, att.EXIT_UNRESOLVED_SELECTOR)
            self.assertEqual(err, "")
            record = json.loads(out)
            agent_schema.assert_valid_agent_record(record)
            self.assertEqual(record["outcome"], "clean")
            self.assertEqual(record["kind"], "result")
            self.assertIn(token, record["excluded_tree_selectors"])
            self.assertEqual(record["next"], f"aw find {token}")
            self.assertTrue(
                any(a["tree"] == policy.name for a in record["excluded_artifacts"])
            )

    def test_class3_excluded_tree_list_mode_paths_channel_split(self):
        """On list-mode --paths, stdout contains no explanation text (pipe safety)."""
        with tempfile.TemporaryDirectory() as td:
            root, policy, token = _build_fixture_repo(Path(td))

            rc, out, err = _run_attention_in_process(
                root, selectors=[token], paths=True
            )
            # Section 11.1: NOT REFUSED
            self.assertNotEqual(rc, att.EXIT_UNRESOLVED_SELECTOR)
            # Per-surface channel rule: stdout stays clean (0 bytes) for piping
            self.assertEqual(out, "")
            # Explanation is written to stderr
            self.assertIn(policy.name, err)
            self.assertIn(policy.reason, err)
