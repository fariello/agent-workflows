"""Install `--diff` preview / apply GENERATED-MEMBER parity (plan at61gc, backlog bplplj).

WHY THIS MODULE EXISTS AT ALL, rather than these tests living beside the other skill-emission
tests: `tests/test_installer_skill_emission.py` sets a MODULE-level `pytestmark =
pytest.mark.slow`, and pytest offers NO per-test or per-class escape from a module-level mark
(measured: an extra per-test marker and a class-level `pytestmark = []` both leave the test
DESELECTED under `-m "not slow"`). This repository's configured `addopts` excludes `slow`, so a
parity test added there would not run in the bare `python3 -m pytest` that gates a change. This
module is therefore deliberately NOT slow-marked, and it needs no git repo to stay that way.

THE DEFECT BEING PINNED. The `--diff` branch in `engine.run` composed only `body_members` and
`shim_members` and never called `_build_skill_members`, while the apply path
(`engine.install_into_repo`) composed `{**shim_members, **skill_members}`. It is a CROSS-FUNCTION
divergence, which is why reading either function alone never reveals it. Measured before the fix:
`install-workflows.py --diff` printed 213 proposed-file headers with ZERO under `.agents/skills/`
while an apply wrote 92 files there.

WHY THESE TESTS DRIVE `engine.run` INSTEAD OF RE-COMPOSING THE MAPS. A test that builds both
sides itself is an identity assertion: `{**shims, **skills} == {**shims, **skills}` is True
against UNMODIFIED code, so it would pass with the defect fully present and could never fail if
the fix were reverted. So we monkeypatch `engine.show_install_diffs` with a recorder and assert on
the map the REAL branch actually hands it. Measured against the unfixed branch, the recorder
captured a 54-entry map with zero skill members, so these tests genuinely bite.

NO COUNT IS HARDCODED. The 54/92/213/92 figures above are historical measurements and move
whenever the workflow manifest gains or loses a row; the assertions below express the PROPERTY
(the captured map contains the non-empty skill set) so they stay true as the corpus grows.

An adjacent guard, `tests/test_installer.py::SingleSourceOrchestratorTests::
test_run_and_install_into_repo_produce_same_fileset`, compares the two APPLY paths' on-disk file
sets; the `if plan.diff:` branch `continue`s before writing anything, so that guard structurally
cannot reach this defect. These tests are not redundant with it.

Stdlib unittest only; no git repo, no network, no writes outside a temp dir.
"""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path

from agent_workflows import engine as INS


@dataclass
class CapturedDiffCall:
    """Exactly what the real `--diff` branch handed `show_install_diffs`."""

    plan: INS.InstallPlan
    body_members: list[str] = field(default_factory=list)
    generated_members: dict[str, str] = field(default_factory=dict)


class DiffPreviewGeneratedMemberParityTests(unittest.TestCase):
    """E-02/V-02: what the real `--diff` branch passes to the renderer."""

    def _capture_diff_call(self, repo_root: Path) -> CapturedDiffCall:
        """Drive the REAL `--diff` branch and return the `(plan, body, generated)` it passed.

        Deliberately exercises `engine.run(engine.parse_args([...]))`, i.e. the standalone
        installer's own entry point (`python3 install-workflows.py --diff`; the `--diff` flag
        belongs to THAT surface, not to `aw install`, which has `--dry-run` and rejects
        `--diff`). The branch returns before `ensure_repo_root` and the git diagnostics, so a
        bare directory suffices and no `git init` is needed - which is what keeps this fast
        enough to be non-slow.
        """

        calls: list[CapturedDiffCall] = []
        original = INS.show_install_diffs

        def recorder(plan, body_members, shim_members):  # mirrors the real signature
            calls.append(
                CapturedDiffCall(
                    plan=plan,
                    body_members=list(body_members),
                    generated_members=dict(shim_members),
                )
            )

        INS.show_install_diffs = recorder
        try:
            args = INS.parse_args(["--repo", str(repo_root), "--diff", "--no-color"])
            rc = INS.run(args)
        finally:
            INS.show_install_diffs = original

        self.assertEqual(rc, 0, "the --diff branch must succeed")
        self.assertEqual(
            len(calls), 1, "show_install_diffs was not called exactly once"
        )
        return calls[0]

    def _expected_skill_members(self, plan) -> dict[str, str]:
        """The skill map composed from the SAME inputs the observed branch used."""

        target_layout = INS.resolve_target_layout(plan.repo_root)
        workflows = INS.parse_manifest(plan.source_root)
        return INS._build_skill_members(workflows, plan.source_root, target_layout)

    def test_diff_preview_generated_map_contains_every_generated_skill_member(self):
        # THE REGRESSION GATE. With the `_build_skill_members` call removed from the `--diff`
        # branch this fails, because the captured map then carries shims only.
        with tempfile.TemporaryDirectory() as tmp:
            captured = self._capture_diff_call(Path(tmp))
            generated = captured.generated_members
            expected_skills = self._expected_skill_members(captured.plan)

            # NON-EMPTINESS FIRST: a containment assertion against an empty expectation passes
            # vacuously, i.e. by measuring nothing.
            self.assertTrue(
                expected_skills,
                "expected at least one generated skill member to check against",
            )

            missing = sorted(set(expected_skills) - set(generated))
            self.assertEqual(
                missing,
                [],
                "the --diff preview omits generated skill members an apply would write",
            )

    def test_diff_preview_generated_map_matches_the_apply_composition(self):
        # PARITY, not merely containment: the preview's generated map must be exactly the
        # shim-plus-skill map `install_into_repo` composes, so neither path can carry a member
        # the other lacks.
        with tempfile.TemporaryDirectory() as tmp:
            captured = self._capture_diff_call(Path(tmp))
            plan = captured.plan
            target_layout = INS.resolve_target_layout(plan.repo_root)
            workflows = INS.parse_manifest(plan.source_root)
            apply_shims = INS.generate_shim_members(
                workflows, plan.source_root, target_layout=target_layout
            )
            apply_skills = INS._build_skill_members(
                workflows, plan.source_root, target_layout
            )
            self.assertTrue(apply_shims, "expected a non-empty shim map")
            self.assertTrue(apply_skills, "expected a non-empty skill map")

            self.assertEqual(
                sorted(captured.generated_members),
                sorted({**apply_shims, **apply_skills}),
                "preview and apply generated-member key sets diverged",
            )

    def test_every_previewed_skill_member_value_is_renderable_text(self):
        # `show_install_diffs` does `content.encode("utf-8")` on every generated value, so a
        # non-str value would raise inside the renderer rather than being reported. Pin the
        # type contract at the boundary the new call introduced.
        with tempfile.TemporaryDirectory() as tmp:
            captured = self._capture_diff_call(Path(tmp))
            generated = captured.generated_members
            expected_skills = self._expected_skill_members(captured.plan)
            self.assertTrue(expected_skills, "expected a non-empty skill map")
            for rel in expected_skills:
                self.assertIsInstance(
                    generated[rel], str, f"previewed member {rel} is not text"
                )


if __name__ == "__main__":
    unittest.main()
