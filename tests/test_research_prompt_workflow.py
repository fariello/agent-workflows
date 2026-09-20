"""Unit tests for the research-prompt producer workflow (`/aw research`).

WHAT IS ASSERTED, and why each is not a prose pin.

* The manifest ROW: `research` is registered, and its body path RESOLVES on disk. Both are
  machine-consumed: the dispatcher shim tells an agent to read the manifest and follow the body
  path, so a missing row means the verb does not exist and a dangling path means the verb is dead.
* The SHIM SET: no standalone `research-prompt` host shim is generated or present. Asserted by
  driving `generate_shim_members`, not by reading text.
* The COMMANDS the body instructs an agent to type: every `aw <sub>` token names a real subcommand
  and every flag of the `aw prompts new` invocation exists in the real parser. A stale instruction
  here is a genuine defect (the agent types a command that fails), and it is exactly what a prose
  pin could never catch, because a pin asserts the sentence is PRESENT, never that it still WORKS.
* The PATHS the body and README reference: every `.aw/...` path they name exists, and the staging
  lane they name is the lane `prompts.py` actually writes to (derived from `prompts_root` +
  `PENDING_BUCKET`, not hardcoded).
* The METADATA LINE the exit gate quotes: compared against `prompts.render_metadata_comment`'s own
  output rather than pinned as a string, so the doc and the renderer cannot drift.

WHAT WAS DELETED, and where the property lives now.

* `test_workflow_files_exist` (body/README exist and exceed a length threshold). Folded into the
  manifest test, which now requires the body path from the ROW to resolve; that is strictly
  stronger, because a body that exists under a name the manifest does not point at is still a dead
  verb. The README's existence is already asserted for EVERY top-level capability by
  `tests/test_dir_readmes.py::test_source_has_readme_for_every_top_level_capability`. The
  `len(text) > 100` byte-count thresholds are gone: they encode no rule and a 101-byte stub passes.
* `test_workflow_body_encodes_prompt_purity_and_contracts`, items 1-3 and 5 (the body must contain
  "only the prompt"/"no user-facing instructions", "self-contained", "downloadable" + ".md", and a
  sentence distinguishing `aw research`). These are change-detectors over English: the case-folded
  substring soup also made them near-vacuous (".md" appears in every path in the file, so the
  "downloadable .md" conjunct was satisfied by an unrelated filename). NOTHING ELSE COVERS the
  purity prose, and that is the honest status: `aw prompts check`, the prompt-purity LINT that
  would enforce it mechanically, is owned by a separate approved spec and is not implemented
  (`agent_workflows/prompts.py` module docstring, "Deliberately NOT here"). A needle search for
  three phrases was never that enforcement; it only proved someone typed the words once.
* `test_readme_content` (four literal needles in the README). Replaced by the path-resolution and
  command-validity checks below, which assert the things in it that can actually be wrong.
* `test_prompt_purity_negative_detection`. DELETED with no replacement and no loss: it defined a
  `check_purity` helper INSIDE the test body and then asserted that local helper against four
  literals. It imported nothing, drove no production code, and could not fail for any change to
  this repository; it was a test of itself.
"""

from __future__ import annotations

import re
import unittest

from agent_workflows import engine as INS
from agent_workflows import prompts as PROMPTS
from tests.support import REPO_ROOT, SOURCE_WORKFLOWS

WORKFLOW_DIR = REPO_ROOT / ".aw" / "system" / "workflows" / "research-prompt"
BODY_PATH = WORKFLOW_DIR / "research-prompt.md"
README_PATH = WORKFLOW_DIR / "README.md"

#: Every `.aw/...`-shaped path either document names inside backticks.
_AW_PATH_RE = re.compile(r"`(\.aw/[A-Za-z0-9_./-]+)`")
#: An `aw <subcommand>` reference, matching `docs_check`'s own notion of one.
_AW_CMD_RE = re.compile(r"\baw ([a-z][a-z0-9-]*)\b")


class ManifestRegistrationTests(unittest.TestCase):
    """The verb must EXIST and RESOLVE: both are read by the dispatcher, not by a human."""

    def setUp(self) -> None:
        self.workflows = INS.parse_manifest(SOURCE_WORKFLOWS)

    def test_the_research_row_is_registered_and_its_body_resolves(self) -> None:
        wf_map = {w.command: w for w in self.workflows}
        self.assertIn(
            "research",
            wf_map,
            "the manifest has no `research` row, so `/aw research` resolves to nothing. FIX: "
            "restore the row in `.aw/system/workflows/index.md`.",
        )
        wf = wf_map["research"]
        body = REPO_ROOT / wf.body
        self.assertTrue(
            body.is_file(),
            f"the manifest points `research` at {wf.body!r}, which does not exist. The dispatcher "
            "shim tells an agent to read the manifest and open that path, so a dangling body makes "
            "the verb dead even though the row is present. FIX: repair the path in index.md, or "
            "restore the body file.",
        )
        self.assertEqual(
            body.resolve(),
            BODY_PATH.resolve(),
            "the `research` row no longer points at this workflow's body; if the body legitimately "
            "moved, update this test's BODY_PATH too so the rest of the file keeps asserting the "
            "file the manifest actually ships.",
        )
        self.assertFalse(
            wf.lens, "`research` is a producer workflow, not a lens/persona catalog row"
        )
        self.assertTrue(
            wf.description, "a row with no description gets no shim help text"
        )

    def test_no_standalone_research_prompt_shim_is_generated_or_present(self) -> None:
        """The verb is reached through the `/aw` dispatcher; a second entry point would diverge."""

        shims = INS.generate_shim_members(
            self.workflows, SOURCE_WORKFLOWS, target_layout="aw"
        )
        generated = [k for k in shims if k.endswith("/research-prompt.md")]
        on_disk = [
            p
            for p in (
                REPO_ROOT / ".opencode" / "commands" / "research-prompt.md",
                REPO_ROOT / ".claude" / "commands" / "research-prompt.md",
            )
            if p.exists()
        ]
        self.assertEqual(
            (generated, [p.name for p in on_disk]),
            ([], []),
            f"a standalone research-prompt shim appeared (generated: {generated}, on disk: "
            f"{[str(p) for p in on_disk]}). The workflow is invoked as `/aw research`; a second "
            "host-level entry point is a second copy of the invocation contract that will drift.",
        )


class InstructedCommandsAreRealTests(unittest.TestCase):
    """Every command the body tells an agent to TYPE must still work.

    This is what replaced the purity/README prose pins, and it is the only kind of assertion about
    a workflow body that can catch a real defect: the body is executed BY AN AGENT, so a flag that
    no longer exists makes the workflow fail at step 4 while every needle test stays green.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.body = BODY_PATH.read_text(encoding="utf-8")
        cls.readme = README_PATH.read_text(encoding="utf-8")

    @staticmethod
    def _parser_tree():
        from agent_workflows import cli

        parser = cli._build_parser()
        subs = {}
        for action in parser._actions:  # noqa: SLF001 (argparse introspection, as docs_check does)
            choices = getattr(action, "choices", None)
            if choices and hasattr(choices, "items"):
                subs.update(choices)
        return subs

    def test_every_aw_subcommand_the_workflow_names_exists(self) -> None:
        known = set(self._parser_tree())
        unknown = []
        for label, text in (("body", self.body), ("README", self.readme)):
            for sub in sorted(set(_AW_CMD_RE.findall(text))):
                if sub not in known:
                    unknown.append(
                        f"  {label}: `aw {sub}` is not a subcommand of the real CLI"
                    )
        self.assertEqual(
            unknown,
            [],
            "the research-prompt workflow instructs an agent to run commands that do not exist:\n"
            + "\n".join(unknown)
            + "\n  FIX: update the workflow text to the current verb, or restore the verb. An "
            "agent follows these literally, so a stale one fails the workflow at that step.",
        )

    #: (flag the body's `aw prompts new` invocation passes, why the workflow depends on it)
    REQUIRED_PROMPTS_NEW_FLAGS = (
        ("--kind", "selects the prompt kind; without it the minted file has no kind"),
        ("--slug", "the only REQUIRED input; `prompts.run_new` exits 2 without it"),
        ("--apply", "dry-run is the DEFAULT, so without this nothing is ever written"),
        (
            "--author",
            "recorded in the metadata comment the workflow's exit gate checks",
        ),
        ("--targets", "records which AI the prompt was written for"),
        ("--concerns", "the one-line summary carried in the metadata comment"),
    )

    def test_the_minting_invocation_passes_only_flags_that_exist(self) -> None:
        subs = self._parser_tree()
        self.assertIn("prompts", subs, "the workflow's minting step needs `aw prompts`")
        inner = {}
        for action in subs["prompts"]._actions:  # noqa: SLF001
            choices = getattr(action, "choices", None)
            if choices and hasattr(choices, "items"):
                inner.update(choices)
        self.assertIn("new", inner, "the workflow mints with `aw prompts new`")
        real_flags = {
            opt for act in inner["new"]._actions for opt in act.option_strings
        }  # noqa: SLF001

        problems = []
        for flag, why in self.REQUIRED_PROMPTS_NEW_FLAGS:
            in_body = flag in self.body
            in_cli = flag in real_flags
            if in_body and not in_cli:
                problems.append(
                    f"  {flag}: the workflow tells the agent to pass it, but `aw prompts new` no "
                    f"longer accepts it (argparse would exit 2). Needed because: {why}"
                )
            if in_cli and not in_body:
                problems.append(
                    f"  {flag}: accepted by `aw prompts new` but no longer used by the workflow, "
                    f"so the minted prompt loses it. Needed because: {why}"
                )
        self.assertEqual(
            problems,
            [],
            f"{len(problems)} of {len(self.REQUIRED_PROMPTS_NEW_FLAGS)} flags in the workflow's "
            "minting step disagree with the real `aw prompts new` parser:\n"
            + "\n".join(problems)
            + "\n  FIX: change the workflow body and the CLI together. The failure mode this "
            "catches is silent: the workflow reads fine and fails only when an agent runs it.",
        )

    def test_the_kind_the_workflow_mints_is_in_the_closed_vocabulary(self) -> None:
        """`--kind research` must be a MEMBER of `prompts.PROMPT_KINDS`, which refuses unknowns."""

        self.assertIn(
            "research",
            PROMPTS.PROMPT_KINDS,
            "the workflow mints with `--kind research`, but `prompts.PROMPT_KINDS` "
            f"({PROMPTS.PROMPT_KINDS}) no longer contains it. That set is CLOSED and an unknown "
            "kind is refused, so the workflow's own minting step would fail. FIX: add the kind "
            "back, or change the workflow to a kind the module accepts.",
        )


class ReferencedPathsResolveTests(unittest.TestCase):
    """A workflow that points an agent at a path that does not exist is broken, not merely stale."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.body = BODY_PATH.read_text(encoding="utf-8")
        cls.readme = README_PATH.read_text(encoding="utf-8")

    def test_every_aw_path_either_document_names_exists(self) -> None:
        dangling = []
        for label, text in (("body", self.body), ("README", self.readme)):
            for rel in sorted(set(_AW_PATH_RE.findall(text))):
                if not (REPO_ROOT / rel.rstrip("/")).exists():
                    dangling.append(f"  {label}: `{rel}` does not exist in the tree")
        self.assertEqual(
            dangling,
            [],
            "the research-prompt workflow points at paths that are not there:\n"
            + "\n".join(dangling)
            + "\n  FIX: an agent following this workflow will look for each of these; repair the "
            "reference or restore the path.",
        )

    def test_the_staging_lane_named_matches_the_lane_the_tool_writes_to(self) -> None:
        """DERIVED, not pinned: the lane comes from `prompts.py`, so a relocation fails here.

        The old assertion hardcoded `.aw/records/prompts/pending/`. That passes even after the
        module starts writing somewhere else, which is the drift that actually matters, and fails
        on a pure rewording, which is the drift that does not.
        """

        lane = (
            (PROMPTS.prompts_root(REPO_ROOT) / PROMPTS.PENDING_BUCKET)
            .relative_to(REPO_ROOT)
            .as_posix()
        )
        self.assertIn(
            lane,
            self.body,
            f"`prompts.py` mints into {lane!r}, but the workflow body does not name that lane, so "
            "it directs the agent (and its exit-gate check) at the wrong directory. FIX: update "
            "the body to the lane the module actually uses.",
        )

    def test_the_readme_fallback_names_the_real_body_path(self) -> None:
        """The 'read and execute <path>' fallback is a literal instruction for a non-slash agent."""

        rel = BODY_PATH.relative_to(REPO_ROOT).as_posix()
        self.assertIn(
            rel,
            self.readme,
            f"the README's agent-agnostic fallback must name the real body path ({rel}); an agent "
            "with no /commands support has nothing else to open. FIX: update the README path.",
        )


class MetadataContractTests(unittest.TestCase):
    """The body QUOTES the metadata line the verb emits; compare against the renderer, not a pin."""

    def test_the_quoted_metadata_prefix_is_what_the_renderer_emits(self) -> None:
        rendered = PROMPTS.render_metadata_comment(
            kind="research", status=PROMPTS.DEFAULT_STATUS, created="2026-01-01"
        )
        # The prefix an agent (and a reviewer) compares a minted file against, byte for byte, up to
        # the point where the per-file fields start.
        prefix = rendered.split(" | Created:")[0]
        body = BODY_PATH.read_text(encoding="utf-8")
        self.assertIn(
            prefix,
            body,
            "the workflow's exit gate quotes the leading metadata comment a minted prompt must "
            f"begin with, but `prompts.render_metadata_comment` now emits {prefix!r}. The two have "
            "drifted, so an agent checking its own output against the workflow text would reject a "
            "correctly minted file (or accept a wrong one). FIX: requote the renderer's output in "
            "the body, or change the renderer.",
        )


if __name__ == "__main__":
    unittest.main()
