"""Install-time emission of the machine-readable layout artifacts (`wslayout` Order 04 `hauwqh`;
spec `kw5y2s` Section 6.1), the framework-owned `.aw/.gitignore` lanes, and the retired-run-scratch
relocation.

WHAT THIS FILE EXISTS TO PIN, since a naive version of each assertion passes while the feature is
broken:

1. THE CHOKEPOINT, not one entry point. `engine.install_into_repo` has three callers, and the second
   CLI one (`aw setup` -> `cli._run_setup` -> `cli._install_one`) is easy to miss. Emission wired into
   `engine.run()` instead would leave `aw setup` silently emitting nothing, so the emission is asserted
   through BOTH the shared core and `cli._install_one`.

2. THE GENERATOR, not this repo's checked-in file. A target repo's `.aw/.gitignore` is GENERATED from
   `engine._AW_GITIGNORE_TEMPLATE` (fresh install) or back-filled by `engine._ensure_aw_gitignore`
   (already-installed repo), never copied from here. A test that only greps the framework's own
   `.aw/.gitignore` would pass while every target repo showed the generated files as untracked, so BOTH
   generation paths are exercised in a temporary repo.

3. IGNORED IN EFFECT, not merely mentioned. The rule is proven with real `git status --porcelain` and
   `git check-ignore -v`, and the attribution is asserted to be `.aw/.gitignore` rather than the user's
   ROOT `.gitignore`. Note the root file legitimately DOES change on a first install
   (`ensure_untracked_gitignore` writes a managed `aw:block`; `ensure_backups_gitignored` adds the
   backups line), so the correct assertion is "carries no layout entry", NOT "has no diff".

NO THIRD-PARTY IMPORTS. Schema conformance is checked structurally with the stdlib, matching
`tests/test_layout.py`: `jsonschema` is in neither the runtime deps nor the `[test]` extra.

HOW THIS FILE IS ORGANIZED, and why it is mostly TABLE-DRIVEN. Four classes used to assert the SAME
property about four different generated trees (layout artifacts, manifest indexes, machine-local
state, run scratch): the pattern is in the template, the back-fill reaches an already-installed repo,
the back-fill is idempotent, the path is ignored IN EFFECT and attributed to `.aw/.gitignore`, and
the anchoring does not swallow a same-named neighbour. Those are now ONE table over
`(.aw/`-relative pattern, repo-relative path, must-ignore-or-not)` and one test per PROPERTY, because
the lanes share a single generator and a single back-fill function: a regression in either moves many
lanes at once, which four near-identical classes reported as four unrelated red blocks and this file
reports as one failure naming every lane that moved.

MUST-NOT-IGNORE ROWS LIVE IN THE SAME TABLE as the must-ignore ones, and they carry real weight: an
over-broad pattern (a bare `state/`, a bare `INDEX.json`, a bare `workflow-artifacts/`) satisfies
every must-ignore row on its own while silently unshipping `config/project.json` or swallowing a
tracked lane. That failure mode is not hypothetical here; the unanchored `inbox/` form really did
swallow the tracked `records/comms/shared/inbox/` lane, which is why every anchored pattern in the
template carries a comment about it.

Tests that are NOT rows carry a one-line docstring saying why. The recurring reasons: the claim is
about a REAL file or this repository's own tree rather than a fixture; the setup is materially
different (a patched `subprocess.run`, a legacy-layout repo, a dry run); the assertion is over
`git log --follow` or a returned action list rather than a path's ignore status; or the property is a
before/after idempotence pair, whose two halves cannot become one row.
"""

from __future__ import annotations

import argparse
import json
import stat
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from tests.support import SOURCE_WORKFLOWS, git, init_repo

from agent_workflows import cli as CLI
from json import dumps as _json_dumps

from agent_workflows import engine as INS
from agent_workflows import layout as LAYOUT
from agent_workflows.term import Term

LAYOUT_JSON = ".aw/system/layout.json"
LAYOUT_SCHEMA = ".aw/system/layout.schema.json"
# The `.aw/`-relative patterns as they must appear in the framework-owned `.aw/.gitignore`.
IGNORE_PATTERNS = ("system/layout.json", "system/layout.schema.json")

# idxuntrack Order 02 (yvvf98 E-05/E-06), backlog ila6vl: the four GENERATED manifest indexes, which
# are gitignored for the same reason the layout artifacts above are (byte-deterministically
# regenerated from the artifact files, so every tracked diff is derived) plus one the layout
# artifacts do not have: a tracked auto-regenerated file CONFLICTS on any concurrent lane by
# construction, which stranded lane `ueg5cf`'s 2477 tested lines on 2026-09-06.
MANIFEST_IGNORE_PATTERNS = (
    "records/plans/INDEX.json",
    "records/plans/INDEX.md",
    "records/research/INDEX.json",
    "records/research/INDEX.md",
)
MANIFEST_PATHS = tuple(f".aw/{p}" for p in MANIFEST_IGNORE_PATTERNS)


def _install(repo: Path) -> dict:
    """Run the shared install core the way every entry point does."""

    return INS.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)


def _seed_committed_repo(base: Path, name: str) -> Path:
    """A temporary git repo with one commit and a pre-existing user line in the root `.gitignore`.

    The user line exists so a test can prove the installer PRESERVED it while adding its own managed
    block, and the commit exists so `git status --porcelain` is meaningful (an unborn HEAD reports
    everything as untracked regardless of the ignore rules).
    """

    repo = init_repo(base / name)
    (repo / ".gitignore").write_text(
        "# user's own line\n*.user-tmp\n", encoding="utf-8"
    )
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-qm", "seed")
    return repo


class LayoutEmissionFreshInstallTests(unittest.TestCase):
    """What a fresh install writes, and what a SECOND install must not rewrite.

    ONE table replaces six tests, and the column that bought the reduction is the INSTALL MODE. Every
    one of the six installed into a temporary repo and then asserted one property of the two emitted
    files; the interesting distinctions between them were not the property but the STATE the repo was
    in (never installed, installed and current, installed and stale) and which of them the install was
    supposed to report as written. Expressing that state as a `prior` column puts the fresh, the
    no-op and the refresh cases side by side, which is the only arrangement in which the skip-unchanged
    optimization and its failure mode (a skip-ALWAYS that never repairs a corrupted file) are visible
    together.

    EVERY ROW ASSERTS THE FULL PROPERTY, deliberately, because this is an INSTALLER and a weakened row
    is worse than no row. For each mode a row pins: the exact `layout_artifacts` list the install
    REPORTED, the on-disk bytes (compared against `layout.build_default_layout()`'s own serialization,
    so a forked serializer cannot pass), the file MODE (0o644, spec kw5y2s 6.1 clause 2), and whether
    the file was REWRITTEN at all (mtime). The mtime column is the one that actually distinguishes
    "no-op" from "rewrote identical bytes": a nondeterministic serializer that happened to produce
    equal bytes still churns the file for every watcher in the target repo, and only an mtime check
    catches it.

    THE `reported` COLUMN IS THE ONE THAT MUST NOT BE DROPPED to a bool. `install_into_repo`'s return
    value is what the CLI summary prints to a human and what a library caller consumes, so a row says
    which paths it names, not merely that it named some. A fresh install reports BOTH, a re-install at
    the same version reports NEITHER, and a stale-file install reports EXACTLY the stale one: an
    implementation that reported everything every time would satisfy a bool-valued version of all
    three.
    """

    #: (case, prior on-disk state as {rel: text} written between the first and second install or None
    #: for a single fresh install, the EXACT `layout_artifacts` list the install must report, whether
    #: each file's bytes must equal the canonical serialization afterwards, whether an already-present
    #: file must be byte-and-mtime UNCHANGED by the second install, why this row exists)
    MODES = (
        (
            "a fresh install into a repo that has never been installed",
            None,
            [LAYOUT_JSON, LAYOUT_SCHEMA],
            True,
            (),
            "THE BASE CASE: both artifacts appear, at 0o644, carrying exactly "
            "`layout.build_default_layout()`'s own serialization. The canonical-bytes half is what "
            "forbids a FORKED serializer in the installer, so `aw layout` (Order 05) and a "
            "file-reading consumer can never disagree; asserting only that the files exist would "
            "accept any JSON at all",
        ),
        (
            "a re-install at the SAME version, nothing touched in between",
            {},
            [],
            True,
            (LAYOUT_JSON, LAYOUT_SCHEMA),
            "V-01 determinism, and the row the mtime column exists for: a second install must report "
            "NO layout writes and must not rewrite either file. Byte equality alone is too weak, "
            "because a rewrite of identical bytes still churns the file for every watcher in the "
            "target repo; and a skip that reported the paths anyway would put spurious entries in the "
            "CLI summary a human reads to see what changed",
        ),
        (
            "a CORRUPTED layout.json, as a previous version or a bad edit leaves it",
            {LAYOUT_JSON: "{}\n"},
            [LAYOUT_JSON],
            True,
            (LAYOUT_SCHEMA,),
            "the skip-unchanged optimization must not become a skip-ALWAYS. This row is the inverse of "
            "the one above and they must be read together: the refresh is reported and the bytes are "
            "restored to canonical, while the UNTOUCHED schema file is still left alone, which is what "
            "proves the installer repaired the stale file specifically rather than rewriting the pair",
        ),
    )

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_every_install_mode_emits_reports_and_preserves_the_right_files(
        self,
    ) -> None:
        model = LAYOUT.build_default_layout()
        wrong = []
        base_row_broken = 0
        for index, (case, prior, reported, canonical, unchanged, why) in enumerate(
            self.MODES
        ):
            repo = _seed_committed_repo(self.base, f"mode-{index}")
            result = _install(repo)
            problems = []

            if prior is not None:
                # The second install is the one under test; seed the prior state between them and
                # snapshot bytes+mtime so "was it rewritten at all" is answerable.
                for rel, text in prior.items():
                    (repo / rel).write_text(text, encoding="utf-8")
                before = {
                    rel: ((repo / rel).read_bytes(), (repo / rel).stat().st_mtime_ns)
                    for rel in (LAYOUT_JSON, LAYOUT_SCHEMA)
                }
                result = _install(repo)
                for rel in unchanged:
                    content, mtime = before[rel]
                    if (repo / rel).read_bytes() != content:
                        problems.append(
                            f"{rel} content churned across the second install"
                        )
                    if (repo / rel).stat().st_mtime_ns != mtime:
                        problems.append(
                            f"{rel} was needlessly REWRITTEN (bytes may be equal, but the mtime "
                            "moved, so every watcher in the target repo sees a change)"
                        )

            if sorted(result["layout_artifacts"]) != sorted(reported):
                problems.append(
                    f"install reported layout_artifacts {sorted(result['layout_artifacts'])!r}, "
                    f"expected exactly {sorted(reported)!r}"
                )

            for rel in (LAYOUT_JSON, LAYOUT_SCHEMA):
                path = repo / rel
                if not path.is_file():
                    problems.append(f"{rel} is not on disk at all")
                    continue
                mode = stat.S_IMODE(path.stat().st_mode)
                if mode != 0o644:
                    problems.append(
                        f"{rel} has mode {oct(mode)}, want 0o644 (spec kw5y2s 6.1 clause 2: a "
                        "non-Python consumer may run as a different user than the installer)"
                    )
                if canonical:
                    version = (
                        (repo / ".aw/system/VERSION")
                        .read_text(encoding="utf-8")
                        .strip()
                    )
                    expected = (
                        model.to_json(version)
                        if rel == LAYOUT_JSON
                        else model.to_schema_json()
                    )
                    got = path.read_text(encoding="utf-8")
                    if got != expected:
                        problems.append(
                            f"{rel} is not the canonical serialization; the installer has a FORKED "
                            f"serializer (got {len(got)} bytes, canonical is {len(expected)})"
                        )

            if problems:
                if index == 0:
                    base_row_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if base_row_broken:
            vacuity = (
                " THE BASE CASE (fresh install) is among the failures, and while it is broken the "
                "other rows prove nothing: they all install first, so an installer that emits "
                "nothing satisfies every no-write expectation trivially."
            )
        self.assertEqual(
            wrong,
            [],
            f"install_into_repo mishandled {len(wrong)} of {len(self.MODES)} install modes."
            f"{vacuity} All three modes run the SAME emission code with different prior on-disk "
            "state, so read the failures together: if every row fails on the BYTES, "
            "`layout.build_default_layout()` or its serializer changed and the installer is fine; "
            "if only the re-install row fails on the mtime, the skip-unchanged check regressed to an "
            "unconditional write; if only the corrupted row fails, skip-unchanged became "
            "skip-ALWAYS and a stale or corrupted artifact will never be repaired. FIX: a wrong "
            "`layout_artifacts` list is not cosmetic, because that list is what the CLI summary "
            f"prints and what a library caller acts on.\n" + "\n".join(wrong),
        )

    def test_framework_version_matches_the_installed_version_file(self) -> None:
        """Kept separate: relates the emitted document to ANOTHER installed file, not to a mode."""
        repo = _seed_committed_repo(self.base, "version")
        _install(repo)
        doc = json.loads((repo / LAYOUT_JSON).read_text(encoding="utf-8"))
        installed = (repo / ".aw/system/VERSION").read_text(encoding="utf-8").strip()
        self.assertTrue(installed, "no .aw/system/VERSION written by install")
        self.assertEqual(
            doc["framework_version"],
            installed,
            "emitted framework_version must match .aw/system/VERSION (version alignment)",
        )

    def test_emitted_document_conforms_to_the_emitted_schema(self) -> None:
        """Kept separate: a structural sweep over the schema's own key set, not a per-mode claim.

        Structural conformance with the STDLIB (no `jsonschema` dependency), the same approach
        tests/test_layout.py takes: every required top-level key present, no undeclared key, and each
        declared type honored. The point is that the two EMITTED files agree with EACH OTHER, so a
        consumer validating on disk succeeds.
        """
        repo = _seed_committed_repo(self.base, "conform")
        _install(repo)
        doc = json.loads((repo / LAYOUT_JSON).read_text(encoding="utf-8"))
        schema = json.loads((repo / LAYOUT_SCHEMA).read_text(encoding="utf-8"))

        for key in schema["required"]:
            self.assertIn(
                key, doc, f"emitted layout.json is missing required key {key}"
            )
        self.assertEqual(
            set(doc),
            set(schema["properties"]),
            "emitted document keys must match the emitted schema's declared properties",
        )
        self.assertIn(
            doc["schema_version"], schema["properties"]["schema_version"]["enum"]
        )
        types = {"string": str, "array": list, "object": dict, "integer": int}
        for key, value in doc.items():
            declared = schema["properties"][key]["type"]
            self.assertIsInstance(value, types[declared], f"{key} is not {declared}")


class LayoutEmissionSiteTests(unittest.TestCase):
    """E-01/V-01: emission lives in the SHARED core, so every install path inherits it.

    These stay as separate tests rather than becoming rows: each drives a DIFFERENT entry point or
    reads a source file, so they share no table shape with one another.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_emission_is_reached_through_the_cli_install_one_path(self) -> None:
        """Kept separate: drives `cli._install_one`, a different entry point with its own argv shape."""
        # PR-026: `aw setup` reaches the core via `cli._run_setup` -> `cli._install_one`, NOT via
        # `engine.run()`. Driving `_install_one` directly proves the second CLI install path emits;
        # a call placed in `engine.run()` would fail this test while `aw install` still looked fine.
        repo = _seed_committed_repo(self.base, "cli-path")
        args = argparse.Namespace(
            yes=True,
            no_color=True,
            dry_run=False,
            no_backup=False,
            no_prune=False,
            source_root=None,
            repo_root=repo,
            version=False,
            diff=False,
            undo=False,
        )
        outcome = CLI._install_one(repo, SOURCE_WORKFLOWS, args, Term(color=False))
        self.assertEqual(
            outcome, "ok", "cli._install_one did not complete successfully"
        )
        self.assertTrue(
            (repo / LAYOUT_JSON).is_file(),
            "the aw setup path (cli._install_one) emitted no layout.json; emission is not in "
            "the shared install_into_repo chokepoint",
        )
        self.assertTrue((repo / LAYOUT_SCHEMA).is_file())

    def test_dry_run_emits_nothing(self) -> None:
        """Kept separate: the only call with `dry_run=True`, and the claim is a pure ABSENCE."""
        # A dry run must report without writing; otherwise `--dry-run` mutates the repo it is
        # previewing.
        repo = _seed_committed_repo(self.base, "dry")
        INS.install_into_repo(
            repo, SOURCE_WORKFLOWS, dry_run=True, yes=True, no_color=True
        )
        self.assertFalse((repo / LAYOUT_JSON).exists())
        self.assertFalse((repo / LAYOUT_SCHEMA).exists())

    def test_legacy_layout_target_gets_no_aw_system_artifacts(self) -> None:
        """Kept separate: materially different setup (a repo deliberately left on the legacy layout)."""
        # The emitted paths are `.aw/system/` paths by definition. A repo deliberately left on the
        # legacy `.agents/workflows` layout must not be half-migrated by having `.aw/system/` created
        # under it just to hold generated output.
        repo = init_repo(self.base / "legacy")
        (repo / ".agents/workflows").mkdir(parents=True)
        (repo / ".agents/workflows/index.md").write_text("# index\n", encoding="utf-8")
        self.assertEqual(INS.resolve_target_layout(repo), "legacy")
        self.assertEqual(INS.emit_layout_artifacts(repo), [])
        self.assertFalse((repo / LAYOUT_JSON).exists())


class AwGitignoreLaneTests(unittest.TestCase):
    """Every framework-owned `.aw/.gitignore` lane, on both generation paths, ignored IN EFFECT.

    ONE table replaces FOUR NEAR-IDENTICAL CLASSES (`LayoutArtifactsGitignoreTests`,
    `ManifestIndexGitignoreTests`, `MachineLocalStateGitignoreTests`, `RunScratchGitignoreTests`),
    which is 25 tests over four different generated trees. Each class asserted the same five things
    about its own lane: the pattern is in `_AW_GITIGNORE_TEMPLATE`, a fresh install ignores the path,
    the rule is attributed to `.aw/.gitignore` and not the user's root file, `_ensure_aw_gitignore`
    back-fills the pattern into an already-installed repo exactly once, and repeated calls do not
    duplicate it. The three later classes say so in their own docstrings: each "mirrors the sibling
    classes rather than adding a harness", which is the tell that the lane is DATA.

    Why the table beats the 25, concretely. ONE template and ONE `_ensure_aw_gitignore` implement
    every lane, so the realistic regressions are shared: a pattern dropped from the template, a
    back-fill list that drifts from the template, a rewrite of the append branch that stops anchoring.
    Each of those moves SEVERAL lanes at once, and four classes reported it as four unrelated red
    blocks in which a reader had to notice the lanes were all the same shape. The table reports one
    failure naming every lane that moved, which is the shape of the real problem, and it makes the
    set of framework-ignored lanes browsable as a set, so the next person adding one can see what
    exists and copy the anchored form.

    THE MUST-NOT-IGNORE ROWS ARE IN THE SAME TABLE and they are the point, not decoration. Every
    anchored pattern here exists because an unanchored one silently swallowed something: the bare
    `inbox/` really did ignore the TRACKED `records/comms/shared/inbox/` lane and broke `aw install`
    on a fresh repo, and an over-broad `/config/` would stop shipping `config/project.json`, which
    spec `kw5y2s` Section 4.2/10 calls PORTABLE policy. A too-greedy pattern satisfies every
    must-ignore row on its own, so these rows are what stop the fix being a catastrophe; their
    failure message says so.

    EACH ROW IS CHECKED ON BOTH GENERATION PATHS, which is a COLUMN of the test rather than a second
    table: a repo installed before a lane existed already HAS a `.aw/.gitignore`, so
    `_ensure_aw_gitignore` takes the append branch and NEVER re-reads the template. A template-only
    edit therefore passes every fresh-install assertion while reaching no existing repo, which is the
    exact failure each of the four old classes wrote a separate comment about.
    """

    #: (lane, the `.aw/`-relative pattern the framework file must carry or None for a path that must
    #: NOT be ignored, a repo-relative path to materialize and check, whether it must be IGNORED,
    #: why this row exists)
    #:
    #: THE PATTERNS ARE LITERAL STRINGS, NOT slices of `_AW_GITIGNORE_TEMPLATE`. Deriving them from
    #: the template would make a DROPPED or LOOSENED pattern invisible, because both sides would move
    #: together; the whole point is that these are a published contract a target repo depends on.
    LANES = (
        (
            "the emitted layout document",
            "system/layout.json",
            LAYOUT_JSON,
            True,
            "GENERATED from the installed framework version by `engine.emit_layout_artifacts` and "
            "regenerated by every install, so tracking it is exactly the git drift install-time "
            "emission exists to avoid (wslayout Order 04, spec kw5y2s 6.1)",
        ),
        (
            "the emitted layout JSON Schema",
            "system/layout.schema.json",
            LAYOUT_SCHEMA,
            True,
            "the schema is emitted beside the document and regenerated with it; a repo that ignored "
            "one and tracked the other would show a derived diff on every install",
        ),
        (
            "the generated plans manifest index (JSON)",
            "records/plans/INDEX.json",
            ".aw/records/plans/INDEX.json",
            True,
            "byte-deterministically regenerated from the artifact files by `aw index plans`, so "
            "every tracked diff is derived; and worse than the layout pair, an auto-regenerated "
            "tracked file CONFLICTS on any concurrent lane BY CONSTRUCTION. On 2026-09-06 a conflict "
            "in exactly this file was the SOLE cause of lane `ueg5cf`'s aborted merge-back, "
            "stranding 2477 lines of correct tested code",
        ),
        (
            "the generated plans manifest index (Markdown)",
            "records/plans/INDEX.md",
            ".aw/records/plans/INDEX.md",
            True,
            "the human-readable half of the same generated pair; dropping only this one leaves a "
            "derived file tracked while the JSON looks correctly handled",
        ),
        (
            "the generated research manifest index (JSON)",
            "records/research/INDEX.json",
            ".aw/records/research/INDEX.json",
            True,
            "the research tree has the same generated manifest as plans, and the four patterns are "
            "written out individually rather than globbed, so a new record type does NOT silently "
            "inherit the rule",
        ),
        (
            "the generated research manifest index (Markdown)",
            "records/research/INDEX.md",
            ".aw/records/research/INDEX.md",
            True,
            "completes the four-way set the two `aw index` verbs produce; the set is asserted "
            "member by member so a partial regression names which member vanished",
        ),
        (
            "the machine-local config binding",
            "/config/local.json",
            ".aw/config/local.json",
            True,
            "spec kw5y2s Section 4.2/10 splits config into PORTABLE `project.json` and machine-local "
            "`local.json`. The rule is written as the specific FILE, not as `/config/`, because the "
            "directory form would unship portable policy (see the project.json row)",
        ),
        (
            "the per-machine state tree (durable snapshot)",
            "/state/",
            ".aw/state/durable/install.json",
            True,
            "LEAK CONTAINMENT, not tidiness (D92): `install_wizard._persist_policy` writes the "
            "resolved policy here INCLUDING `aw_home`, an ABSOLUTE HOME PATH, so tracking it "
            "publishes the operator's home directory and username into permanent git history. "
            "Measured 2026-09-12: the shipped sanitizer flags a real `install.json` as `home-path` + "
            "`handle`, exit 1",
        ),
        (
            "the per-machine state tree (appended install history)",
            None,  # covered by the anchored `/state/` pattern above, not a pattern of its own
            ".aw/state/durable/history/installs.jsonl",
            True,
            "one leaky snapshot is APPENDED per install, so the history file accumulates them. "
            "Asserted as its own row with no pattern of its own, which is what proves `/state/` "
            "covers the tree RECURSIVELY rather than only its top level",
        ),
        (
            "the state tree at its pre-`durable/` spelling",
            None,
            ".aw/state/install.json",
            True,
            "`/state/` must cover `durable/` and `runtime/` BOTH, and the flat spelling too: repos "
            "written by older versions carry `state/install.json` directly, and a rule that only "
            "matched the nested form would leave those leaking",
        ),
        (
            "the run-scratch home for workflow runs",
            "/workflow-artifacts/",
            ".aw/workflow-artifacts/release-review/20260918T045900Z/report.md",
            True,
            "same D92 rationale as `/state/`: a run record carries local context, absolute home "
            "paths and session detail. THE MEASURED DEFECT this fences (2026-09-12) is that the "
            "framework file had NO entry at all, so the first workflow run in a target repo offered "
            "its scratch to `git add -A`. This repo's ROOT .gitignore does ignore the path, but that "
            "file is not shipped, so it proves nothing about a target",
        ),
        (
            "the raw-drop inbox",
            "/inbox/",
            ".aw/inbox/raw-external-report.md",
            True,
            "unvetted third-party text that has not passed the leak sanitizer, and git history is "
            "permanent. It sits OUTSIDE records/ deliberately so the record sweep cannot enumerate "
            "it, since a stray `- Id: <id6>` QUOTED in a dropped report would otherwise be harvested "
            "as an identity claim colliding with a real artifact",
        ),
        (
            "the append-only workflow-history sidecar",
            "records/history.jsonl",
            ".aw/records/history.jsonl",
            True,
            "appended on every `aw` status write, so a tracked copy would produce a diff on nearly "
            "every command and conflict on every concurrent lane",
        ),
        (
            "the IPD-driver per-run durable state",
            "records/runs/",
            ".aw/records/runs/qv1/state.json",
            True,
            "queue state, session JSONL logs, prompts and the driver lock: box-local ephemeral "
            "working material, and the lock in particular is meaningless outside the machine holding it",
        ),
        (
            "the per-machine post-install setup reminder",
            "setup-repo-needed.md",
            ".aw/setup-repo-needed.md",
            True,
            "a per-MACHINE reminder, so committing it would tell every other clone to run a setup "
            "that has already happened for them",
        ),
        (
            "the box-local records quarantine lanes",
            "records/*/untracked/",
            ".aw/records/prompts/untracked/draft.md",
            True,
            "the safety valve the whole untracked convention rests on: a human drops raw or WIP "
            "content here and promotes a reviewed copy with `git mv`. The glob is per-record-type on "
            "purpose, so every typed tree gets a lane without naming them one by one",
        ),
        (
            "PORTABLE project policy",
            None,
            ".aw/config/project.json",
            False,
            "THE MUST-NOT-IGNORE ROW THAT GUARDS THE `/config/local.json` PATTERN ABOVE: spec kw5y2s "
            "4.2/10 calls this PORTABLE policy that SHOULD be committed, so an over-broad `/config/` "
            "would silently stop shipping it while satisfying every must-ignore row in this table",
        ),
        (
            "the TRACKED comms inbox lane",
            None,
            ".aw/records/comms/shared/inbox/.gitkeep",
            False,
            "THE ROW WITH THE MEASURED HISTORY: a bare `inbox/` is unanchored and matches an `inbox` "
            "directory at ANY depth, which ignored this tracked lane and its `.gitkeep` and BROKE "
            "`aw install` on a fresh repo. It is why the template's `/inbox/` carries a leading slash "
            "and a long comment, and why every later lane copied the anchored form",
        ),
        (
            "an unrelated INDEX.json at another depth",
            None,
            "docs/INDEX.json",
            False,
            "proves the four manifest patterns are ANCHORED SPECIFIC PATHS rather than bare "
            "filenames: a bare `INDEX.json` would match at any depth and swallow an unrelated file "
            "in the user's own tree",
        ),
        (
            "a records subdirectory that merely SHARES the state name",
            None,
            ".aw/records/state/keep.json",
            False,
            "the anchoring guard for `/state/`: the bare form would match a `state/` directory at "
            "any depth, including inside the user's records tree",
        ),
        (
            "a records subdirectory that merely SHARES the run-scratch name",
            None,
            ".aw/records/workflow-artifacts/keep.md",
            False,
            "the anchoring guard for `/workflow-artifacts/`, and the one a naive fix gets wrong: the "
            "patterns are `.aw/`-relative, so the anchored form resolves to `.aw/workflow-artifacts/` "
            "EXACTLY and must leave `records/workflow-artifacts/` visible",
        ),
    )

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    @staticmethod
    def _materialize(repo: Path, rel: str) -> None:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("{}\n", encoding="utf-8")

    def _ignore_source(self, repo: Path, rel: str):
        """The gitignore FILE git attributes the rule to, or None when nothing ignores `rel`."""

        res = git(repo, "check-ignore", "-v", rel)
        if res.returncode != 0:
            return None
        return res.stdout.split(":", 1)[0]

    def _report(self, wrong, total, headline, extra=""):
        vacuous = [w for w in wrong if "MUST NOT be ignored" in w]
        note = ""
        if vacuous and len(vacuous) < len(wrong):
            note = (
                f" {len(vacuous)} of the failures are MUST-NOT-IGNORE rows, which means a pattern is "
                "TOO GREEDY. Fix those first: while one of them is broken the must-ignore rows are "
                "nearly vacuous, because a pattern that ignores everything satisfies all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"{headline} ({len(wrong)} of {total} lanes).{note} ONE template and ONE "
            "`_ensure_aw_gitignore` implement every lane, so SEVERAL LANES FAILING TOGETHER means "
            "the generator or the back-fill changed, not that several lanes are independently "
            f"wrong.{extra}\n" + "\n".join(wrong),
        )

    def _describe(self, lane, pattern, rel, must_ignore, why, problems):
        return (
            f"  {lane} (pattern {pattern!r}, path {rel}):\n"
            + "".join(f"    - {p}\n" for p in problems)
            + f"    this row exists because: {why}"
        )

    def test_the_template_carries_every_pattern_anchored(self) -> None:
        wrong = []
        lines = [
            ln.strip()
            for ln in INS._AW_GITIGNORE_TEMPLATE.splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
        for lane, pattern, rel, must_ignore, why in self.LANES:
            if pattern is None:
                continue
            problems = []
            occurrences = [ln for ln in lines if ln == pattern]
            if len(occurrences) != 1:
                problems.append(
                    f"the template carries {len(occurrences)} bare pattern line(s) equal to "
                    f"{pattern!r}, want exactly 1. A FRESH install writes the template verbatim, so "
                    "a pattern missing here reaches no new repo at all"
                )
            if pattern.startswith("/"):
                bare = pattern.lstrip("/")
                if bare in lines:
                    problems.append(
                        f"the template also carries the UNANCHORED form {bare!r}, which matches a "
                        "directory of that name at ANY depth"
                    )
            if problems:
                wrong.append(
                    self._describe(lane, pattern, rel, must_ignore, why, problems)
                )
        self._report(
            wrong,
            len([r for r in self.LANES if r[1] is not None]),
            "the generated `.aw/.gitignore` template is missing or has loosened patterns",
            extra=" FIX: edit `engine._AW_GITIGNORE_TEMPLATE`, and remember the back-fill list must "
            "agree with it (test_backfill_reaches_an_already_installed_repo asserts that).",
        )

    def test_a_fresh_install_ignores_exactly_the_right_lanes(self) -> None:
        repo = _seed_committed_repo(self.base, "fresh-lanes")
        _install(repo)
        for _lane, _pattern, rel, _must, _why in self.LANES:
            self._materialize(repo, rel)
        wrong = []
        for lane, pattern, rel, must_ignore, why in self.LANES:
            problems = []
            source = self._ignore_source(repo, rel)
            if must_ignore:
                if source is None:
                    problems.append(
                        "MUST be ignored but git ignores it via nothing at all, so it is offered to "
                        "`git add -A` in every target repo"
                    )
                elif source != ".aw/.gitignore":
                    problems.append(
                        f"is ignored, but git attributes the rule to {source!r} rather than the "
                        "framework-owned `.aw/.gitignore`, which is the only file a target repo "
                        "receives (this repo's ROOT .gitignore is not shipped)"
                    )
            elif source is not None:
                problems.append(
                    f"MUST NOT be ignored, but {source!r} ignores it: a pattern is too greedy and is "
                    "swallowing a path the repo depends on being visible"
                )
            if problems:
                wrong.append(
                    self._describe(lane, pattern, rel, must_ignore, why, problems)
                )
        # TWO PRECISION RULES, both learned by getting this wrong while writing the table.
        # FIRST, match the full repo-relative PATH and never the basename: the shipped bundle
        # contains `.../release-review/templates/per-phase-report.md`, whose name ENDS WITH
        # `report.md`, so `"report.md" in porcelain` flags the correctly-ignored run-scratch lane.
        # SECOND, pass `-uall`. The default untracked mode COLLAPSES an untracked directory to a
        # single entry (`?? .aw/config/`), so the legitimately-visible `config/project.json` makes the
        # whole directory appear and any prefix test then reports the correctly-ignored
        # `config/local.json` beside it. With `-uall` git names each file, which is the granularity
        # this assertion is actually about.
        porcelain = git(repo, "status", "--porcelain", "-uall").stdout
        listed = {
            line[3:].strip() for line in porcelain.splitlines() if line[3:].strip()
        }
        leaked = sorted(
            rel for _l, _p, rel, must, _w in self.LANES if must and rel in listed
        )
        if leaked:
            wrong.append(
                "  git status --porcelain still SHOWS generated content:\n"
                + f"    - {leaked}\n"
                + "    this row exists because: `check-ignore` agreeing is not the outcome the user "
                "sees; what they see is `git status`, and that is the surface every one of these "
                f"lanes exists to keep clean. Full porcelain:\n{porcelain}"
            )
        self._report(
            wrong,
            len(self.LANES),
            "a FRESH install did not ignore the framework-owned lanes correctly",
        )

    def test_backfill_reaches_an_already_installed_repo(self) -> None:
        # THE PATH A TEMPLATE-ONLY EDIT SILENTLY FAILS, and the only path that reaches an existing
        # repo: such a repo already HAS a `.aw/.gitignore`, so `_ensure_aw_gitignore` takes the
        # append branch and never re-reads the template.
        repo = _seed_committed_repo(self.base, "backfill-lanes")
        _install(repo)
        gi = repo / ".aw/.gitignore"
        patterns = [p for _l, p, _r, _m, _w in self.LANES if p is not None]
        gi.write_text(
            "\n".join(
                line
                for line in gi.read_text(encoding="utf-8").splitlines()
                if line.strip() not in patterns
            )
            + "\n",
            encoding="utf-8",
        )
        pre = gi.read_text(encoding="utf-8")
        for _lane, _pattern, rel, _must, _why in self.LANES:
            self._materialize(repo, rel)

        INS._ensure_aw_gitignore(repo)

        text = gi.read_text(encoding="utf-8")
        wrong = []
        for lane, pattern, rel, must_ignore, why in self.LANES:
            problems = []
            if pattern is not None:
                count = len([ln for ln in text.splitlines() if ln.strip() == pattern])
                if count == 0:
                    problems.append(
                        f"the back-fill did NOT restore {pattern!r}: the pattern is in the template "
                        "but not in the back-fill list, so every repo installed before this lane "
                        "existed stays broken forever"
                    )
                elif count != 1:
                    problems.append(
                        f"the back-fill wrote {count} copies of {pattern!r}, want 1"
                    )
            if must_ignore:
                source = self._ignore_source(repo, rel)
                if source != ".aw/.gitignore":
                    problems.append(
                        f"after the back-fill the path is attributed to {source!r}, not "
                        "`.aw/.gitignore`"
                    )
            if problems:
                wrong.append(
                    self._describe(lane, pattern, rel, must_ignore, why, problems)
                )
        for survivor in ("records/*/untracked/", "setup-repo-needed.md"):
            if survivor in pre and survivor not in text:
                wrong.append(
                    f"  pre-existing content was CLOBBERED: {survivor!r} was present before the "
                    "back-fill and is gone after it\n"
                    "    this row exists because: the back-fill APPENDS to a user's already-installed "
                    "file; rewriting it wholesale would discard whatever a later version added"
                )
        self._report(
            wrong,
            len(self.LANES),
            "`_ensure_aw_gitignore` did not back-fill an ALREADY-INSTALLED repo correctly",
            extra=" FIX: the template and the back-fill list are two places one contract is written; "
            "a lane present in the first and absent from the second passes every fresh-install test "
            "while reaching no existing repo.",
        )

    def test_repeated_calls_and_reinstalls_never_duplicate_a_pattern(self) -> None:
        # `_ensure_aw_gitignore` runs on several install steps and from `write_setup_marker`, so a
        # non-idempotent addition would accrue duplicate lines on every run. Both repetition shapes
        # are checked because they enter through different code: one calls the helper directly, the
        # other goes around through the whole install.
        repo = _seed_committed_repo(self.base, "idem-lanes")
        _install(repo)
        for _ in range(3):
            INS._ensure_aw_gitignore(repo)
        _install(repo)
        text = (repo / ".aw/.gitignore").read_text(encoding="utf-8")
        wrong = []
        for lane, pattern, rel, must_ignore, why in self.LANES:
            if pattern is None:
                continue
            count = len([ln for ln in text.splitlines() if ln.strip() == pattern])
            if count != 1:
                wrong.append(
                    self._describe(
                        lane,
                        pattern,
                        rel,
                        must_ignore,
                        why,
                        [
                            f"{count} copies after three `_ensure_aw_gitignore` calls plus a second "
                            "full install, want exactly 1"
                        ],
                    )
                )
        self._report(
            wrong,
            len([r for r in self.LANES if r[1] is not None]),
            "repeated installs DUPLICATED gitignore patterns",
            extra=" FIX: the append branch must test for the pattern before adding it. Duplicates are "
            "harmless to git but they grow without bound and they are a diff on a tracked file, which "
            "is what the installer's own commit-set logic then has to reason about.",
        )

    def test_generated_lane_content_stays_untracked_after_git_add_dash_A(self) -> None:
        """Kept separate: the outcome asserted on the INDEX, not on any path's ignore status.

        A pattern can be present while the path is still TRACKED, because gitignore does not untrack
        anything; that is precisely the state a `git rm --cached` had to fix for the manifest indexes.
        So this drives the blunt instrument a user actually reaches for and then asks git what it
        took.
        """
        repo = _seed_committed_repo(self.base, "addall")
        _install(repo)
        for _lane, _pattern, rel, must, _why in self.LANES:
            if must:
                self._materialize(repo, rel)
        git(repo, "add", "-A")
        tracked = set(git(repo, "ls-files").stdout.split())
        offenders = sorted(
            rel for _l, _p, rel, must, _w in self.LANES if must and rel in tracked
        )
        self.assertEqual(
            offenders,
            [],
            "`git add -A` TRACKED generated or machine-local content:\n  "
            + "\n  ".join(offenders)
            + "\n  FIX: this is the failure mode the whole class exists for. For the state and "
            "run-scratch lanes it is a D92 LEAK (absolute home paths and session detail enter "
            "permanent history, which is unrecoverable); for the index lanes it is the conflict "
            "class that stranded lane `ueg5cf`.",
        )

    def test_this_repos_own_aw_gitignore_matches_the_template(self) -> None:
        """Kept separate: the subject is THIS checkout's real file, not a fixture, and it may be absent."""
        # F-7: this repo's `.aw/.gitignore` is byte-identical to the template, so the next install
        # would not re-diff the repo against its own template.
        own = Path(__file__).resolve().parents[1] / ".aw/.gitignore"
        if not own.is_file():  # pragma: no cover - not a managed checkout
            self.skipTest("no .aw/.gitignore in this checkout")
        self.assertEqual(
            own.read_text(encoding="utf-8"),
            INS._AW_GITIGNORE_TEMPLATE,
            "this repo's .aw/.gitignore and _AW_GITIGNORE_TEMPLATE have diverged",
        )

    def test_the_root_gitignore_gains_no_framework_lane_and_keeps_the_users_line(
        self,
    ) -> None:
        """Kept separate: one claim about a DIFFERENT file, as a pair of absence/presence sweeps.

        PR-027 precision. The installer DOES legitimately write to the target's ROOT `.gitignore`
        (`ensure_untracked_gitignore` adds a managed `aw:block`; `ensure_backups_gitignored` adds the
        backups line), so "root file unchanged" is the WRONG assertion and would fail for a legitimate
        reason. What must never happen is a framework lane landing there, or the user's own line being
        clobbered.
        """
        repo = _seed_committed_repo(self.base, "rootfile")
        _install(repo)
        root_text = (repo / ".gitignore").read_text(encoding="utf-8")
        leaked = [
            needle
            for needle in ("layout", "INDEX.", "/state/", "workflow-artifacts")
            if needle in root_text
        ]
        self.assertEqual(
            leaked,
            [],
            f"framework lane entries leaked into the user's ROOT .gitignore: {leaked}\n"
            f"{root_text}",
        )
        self.assertIn(
            "*.user-tmp",
            root_text,
            "the installer clobbered the user's own .gitignore line",
        )


class MachineLocalStatePremiseTests(unittest.TestCase):
    """The PREMISE behind the `/state/` lane, asserted rather than assumed.

    Kept out of the lane table because it asserts nothing about gitignore at all: it drives
    `install_wizard.persist_project_policy` and inspects the snapshot's CONTENT. If a future change
    stops embedding absolute paths, this should fail so someone re-decides whether the ignore rule is
    still warranted, instead of the rationale quietly becoming false while the rule stays.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_the_install_snapshot_really_does_carry_an_absolute_home_path(self) -> None:
        from agent_workflows import install_wizard as IW

        repo = _seed_committed_repo(self.base, "state-premise")
        policy = IW.ProjectPolicy(aw_home=str(self.base / "fake-home" / ".aw"))
        IW.persist_project_policy(str(repo), policy)
        snap = json.loads(
            (repo / ".aw/state/durable/install.json").read_text(encoding="utf-8")
        )
        self.assertIn(
            "aw_home",
            snap.get("policy", {}),
            "the install snapshot no longer records aw_home; re-check the /state/ lane's rationale",
        )
        self.assertTrue(
            Path(snap["policy"]["aw_home"]).is_absolute(),
            f"aw_home is not absolute: {snap['policy']['aw_home']!r}",
        )

    def test_a_realistic_leaky_payload_is_ignored_in_effect(self) -> None:
        """The lane proven against a REAL leaky payload rather than a `{}` placeholder."""
        repo = _seed_committed_repo(self.base, "state-payload")
        _install(repo)
        # The payload is BUILT rather than written as a literal: a literal absolute home path in a
        # tracked test file is itself a `home-path` finding to the shipped leak sanitizer, which
        # `test_local_leaks.ThisRepoTests` runs over this very tree. Caught exactly that way
        # 2026-09-12. Composing it keeps the fixture realistic without tripping the check the
        # fixture exists to justify.
        fake_home = "/" + "home" + "/anon/.aw"
        snapshot = repo / ".aw/state/durable/install.json"
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_text(
            _json_dumps({"policy": {"aw_home": fake_home}}) + "\n", encoding="utf-8"
        )
        git(repo, "add", "-A")
        self.assertNotIn(
            ".aw/state/durable/install.json",
            git(repo, "ls-files").stdout.split(),
            "a snapshot carrying an absolute home path was TRACKED by `git add -A` (D92)",
        )


class InstallerCommitSetTests(unittest.TestCase):
    """The installer's path-scoped commit must not be handed paths git sees no change in.

    REGRESSION for a real failure a maintainer hit 2026-09-12 running `aw install` in a target repo:
    the run ended `Error: git commit failed.` with `no changes added to commit`, leaving a modified
    `.aw/.gitignore` uncommitted. TWO defects composed.

    FIRST, `.aw/.gitignore` was missing from the commit set. It is TRACKED, and `_ensure_aw_gitignore`
    appends to it, but it reaches the set through neither `installed` (the manifest install reports it
    `[already current]`, because the manifest hash matches BEFORE the append) nor `agents_status`.

    SECOND, and this is what actually produced the error, the install manifest is appended as
    `[overwrite]` on EVERY run even when its bytes are unchanged. `git commit -- <paths>` fails when
    NONE of the given paths has a stageable change, so a repo whose framework was fully current
    offered exactly one path, that path had no diff, and the commit died.

    The two tests stay separate: they assert OPPOSITE things about the captured commit set (that no
    commit was attempted at all, versus that a specific path was offered), and the second has to dirty
    the file first, which is materially different setup.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _commit_set(self, repo: Path) -> dict:
        """Capture what `prompt_and_run_commit` would offer, without committing."""

        captured: dict = {}
        real = INS.subprocess.run

        def fake_run(cmd, *a, **k):
            if isinstance(cmd, list) and cmd[:2] == ["git", "commit"]:
                captured["paths"] = cmd[cmd.index("--") + 1 :]

                class _R:
                    returncode = 0

                return _R()
            return real(cmd, *a, **k)

        plan = INS.InstallPlan(
            source_root=SOURCE_WORKFLOWS,
            repo_root=repo,
            dry_run=False,
            backup=False,
            prune=False,
            no_color=True,
            yes=True,
        )
        with mock.patch.object(INS.subprocess, "run", fake_run):
            INS.prompt_and_run_commit(
                plan=plan,
                installed=[".aw/system/managed-sections.json [overwrite]"],
                pruned=[],
                agents_status={},
                backups_ignore_status="",
                use_git=True,
                artifacts=[],
                untracked_ignore_status="",
            )
        return captured

    def test_an_unchanged_path_is_not_offered_for_commit(self) -> None:
        """The direct cause of the reported failure."""

        repo = _seed_committed_repo(self.base, "commit-unchanged")
        _install(repo)
        git(repo, "add", "-A")
        git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base")
        # Tree is clean, so the manifest that `installed` claims was overwritten has NO diff.
        self.assertEqual(git(repo, "status", "--porcelain").stdout.strip(), "")

        captured = self._commit_set(repo)
        self.assertNotIn(
            "paths",
            captured,
            "a commit was attempted with no changed path, which is the failure under test",
        )

    def test_a_backfilled_aw_gitignore_IS_offered_for_commit(self) -> None:
        repo = _seed_committed_repo(self.base, "commit-gitignore")
        _install(repo)
        git(repo, "add", "-A")
        git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base")
        gi = repo / ".aw/.gitignore"
        gi.write_text(
            gi.read_text(encoding="utf-8") + "# a back-filled line\n", encoding="utf-8"
        )

        captured = self._commit_set(repo)
        self.assertIn(
            ".aw/.gitignore",
            captured.get("paths", []),
            "a modified tracked .aw/.gitignore must be committed, not left dirty",
        )


class RootRunScratchMigrationTests(unittest.TestCase):
    """wfartifacts Order 05 (y4pptx): an EXISTING install's run records move to `.aw/workflow-artifacts/`.

    WHAT THIS FILE'S SIBLING CLASSES CANNOT COVER, and why this class exists: Orders 01-04 fixed what
    a FRESH install produces, so every one of their tests starts from a repo with no run scratch at
    all. Measured 2026-09-12, 29 repos on one machine already carry the RETIRED repo-root
    `workflow-artifacts/`, and two of them TRACK real run records in it (11 files and 3 files). This
    is the only child that touches a user's committed history.

    THE PROOF OBLIGATION IS UNUSUALLY HIGH, so each assertion below is chosen against a specific way
    a naive implementation passes while the feature is broken:

    1. HISTORY, not merely location. Asserting the file exists at the new path passes for a
       copy-and-delete that lost the history. So the tracked case asserts the ACTUAL
       `git log --follow` output reaches the pre-migration commit.
    2. NOTHING LOST, not one file checked. A test that checks a single file cannot catch a partial
       move, so the before/after run-record path SETS are compared for equality modulo the prefix.
    3. MERGE, not move (F-7). The destination is usually already populated, which is the common case
       rather than an edge, so a pre-existing destination run must SURVIVE alongside the relocated
       one.
    4. REFUSAL, not overwrite. A same-path/different-bytes conflict must leave BOTH files in place.
    5. IGNORED IN EFFECT, via real `git check-ignore` attributed to `.aw/.gitignore`.

    WHAT IS TABULATED HERE AND WHAT IS NOT. The DISPOSITION table below merges the three tests that
    differed only in what the destination already held (nothing, the same bytes, different bytes),
    because those three are one decision function over one input and the property each asserts is the
    same triple: the destination's final bytes, whether the source survived, and whether a REFUSED
    action was reported. Keeping them apart hid the most important thing about them, which is that
    they are the THREE branches of one comparison and the middle branch (identical bytes) exists
    precisely so a re-run is safe. Every OTHER migration test stays separate, because each asserts a
    structurally different claim: git history via `--follow`, a whole path SET, a dry run touching
    nothing, commit scoping against a co-worker's staged file, a report-only lane, or a no-op.
    """

    RETIRED = "workflow-artifacts"
    NEW = ".aw/workflow-artifacts"
    RUN = "assess-bugs/20260726-115243"

    #: (case, the destination's pre-existing content or None for an absent destination, the bytes the
    #: destination must hold AFTER the migration, whether the SOURCE file must still exist, whether a
    #: `REFUSED` action must be reported, whether the retired DIRECTORY must survive, why this row
    #: exists)
    #:
    #: The source always holds "source version\n", so the three rows differ ONLY in the destination,
    #: which is what makes them one decision function's three branches.
    DISPOSITIONS = (
        (
            "no destination file: an ordinary relocation",
            None,
            "source version\n",
            False,
            False,
            False,
            "THE POSITIVE ROW, and the one that makes the other two non-vacuous: a migration that "
            "refused everything would satisfy both conflict rows on its own. The source is consumed "
            "and the retired directory goes away once empty, which is the whole point of the "
            "relocation",
        ),
        (
            "a destination holding DIFFERENT bytes at the same path",
            "destination version\n",
            "destination version\n",
            True,
            True,
            True,
            "REFUSAL, NOT OVERWRITE, and the single most important row here: overwriting a run record "
            "is UNRECOVERABLE, so the destination keeps its own bytes, the source is left where it "
            "is, the conflict is REPORTED to the user, and the retired directory survives because it "
            "still holds content nobody has adjudicated. A row that checked only the destination "
            "would accept an implementation that refused the write but deleted the source anyway",
        ),
        (
            "a destination holding the SAME bytes at the same path",
            "source version\n",
            "source version\n",
            True,
            False,
            True,
            "IDENTICAL BYTES ARE NOT A CONFLICT: a re-run must be safe, so this is redundancy and "
            "must not be REPORTED as a refusal. But the redundant source is still NOT deleted, "
            "because the invariant is that user content is never deleted outside the README-only "
            "case, and that is exactly the distinction a naive 'same bytes, so clean up the copy' "
            "implementation gets wrong",
        ),
    )

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write(self, repo: Path, rel: str, text: str = "record\n") -> Path:
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def _run_record_paths(self, root: Path) -> list[str]:
        """Every file under `root`, relative and sorted (the unit the path-set equality uses)."""

        if not root.is_dir():
            return []
        return sorted(
            p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
        )

    def _commit(self, repo: Path, *paths: str, message: str = "seed") -> None:
        git(repo, "add", "--", *paths)
        git(repo, "commit", "-qm", message)

    def test_every_destination_state_gets_the_right_disposition(self) -> None:
        rel = f"{self.RUN}/report.md"
        wrong = []
        positive_broken = 0
        for index, (
            case,
            pre_existing,
            expected_dst,
            src_survives,
            refused,
            retired_survives,
            why,
        ) in enumerate(self.DISPOSITIONS):
            repo = _seed_committed_repo(self.base, f"disp-{index}")
            _install(repo)  # gives the repo a real .aw/ tree and the ignore rule
            if pre_existing is not None:
                self._write(repo, f"{self.NEW}/{rel}", pre_existing)
            self._write(repo, f"{self.RETIRED}/{rel}", "source version\n")
            self._commit(repo, self.RETIRED, message="seed a legacy run record")

            actions = INS.migrate_root_workflow_artifacts(repo, use_git=True)

            problems = []
            dst = repo / self.NEW / rel
            got = dst.read_text(encoding="utf-8") if dst.is_file() else None
            if got != expected_dst:
                problems.append(
                    f"the destination holds {got!r}, expected {expected_dst!r}"
                    + (
                        " - AN EXISTING RUN RECORD WAS OVERWRITTEN, which is unrecoverable"
                        if pre_existing is not None and got != pre_existing
                        else ""
                    )
                )
            src_exists = (repo / self.RETIRED / rel).is_file()
            if src_exists != src_survives:
                problems.append(
                    f"the source file {'survived' if src_exists else 'was removed'}; this row "
                    f"requires it to {'survive' if src_survives else 'be consumed'}"
                    + (
                        " - refusing the move but deleting the source loses the content either way"
                        if src_survives
                        else ""
                    )
                )
            got_refused = any("REFUSED" in a for a in actions)
            if got_refused != refused:
                problems.append(
                    f"REFUSED was {'reported' if got_refused else 'NOT reported'}; this row requires "
                    f"it {'reported' if refused else 'absent'}. Actions were {actions!r}"
                )
            retired_exists = (repo / self.RETIRED).is_dir()
            if retired_exists != retired_survives:
                problems.append(
                    f"the retired directory {'survived' if retired_exists else 'was removed'}; this "
                    f"row requires it to {'survive' if retired_survives else 'be pruned'}"
                )
            if problems:
                if index == 0:
                    positive_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if positive_broken:
            vacuity = (
                " THE POSITIVE ROW (no destination file) is among the failures, and while it is "
                "broken the two conflict rows are vacuous: a migration that refuses every move "
                "satisfies both of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"the relocation mishandled {len(wrong)} of {len(self.DISPOSITIONS)} destination "
            f"states.{vacuity} All three rows feed ONE comparison with the same source bytes and "
            "differ only in what the destination already held, so read them together: if the two "
            "conflict rows fail on the DESTINATION bytes, the comparison is not happening at all and "
            "the migration is a blind overwrite, which is the unrecoverable case. If they fail only "
            "on the SOURCE, the move is adjudicated correctly but the cleanup is unconditional. If "
            "the identical-bytes row is the only failure, a re-run is being reported to the user as a "
            f"conflict it must not be.\n" + "\n".join(wrong),
        )

    def test_tracked_run_records_are_relocated_with_history_preserved(self) -> None:
        """Kept separate: the claim is `git log --follow` output, which no bytes/exists column expresses.

        THE CASE THAT MATTERS MOST: committed content moves and the history survives. Asserting the
        file exists at the new path passes for a copy-and-delete that threw the history away, so this
        reads the ACTUAL `--follow` log and looks for the pre-migration commit in it.
        """

        repo = _seed_committed_repo(self.base, "mig-tracked")
        src_rel = f"{self.RETIRED}/{self.RUN}/report.md"
        self._write(repo, src_rel, "the report\n")
        self._commit(repo, self.RETIRED, message="seed a committed run record")
        pre_commit = git(repo, "rev-parse", "HEAD").stdout.strip()
        before = self._run_record_paths(repo / self.RETIRED)
        self.assertEqual(before, [f"{self.RUN}/report.md"], "precondition")

        _install(repo)

        dst_rel = f"{self.NEW}/{self.RUN}/report.md"
        self.assertTrue((repo / dst_rel).is_file(), f"{dst_rel} was not created")
        self.assertFalse(
            (repo / src_rel).exists(), f"{src_rel} was left behind at the retired path"
        )
        self.assertEqual(
            (repo / dst_rel).read_text(encoding="utf-8"),
            "the report\n",
            "content changed during the migration",
        )

        # (1) HISTORY: the ACTUAL --follow output must reach the pre-migration commit.
        follow = git(repo, "log", "--follow", "--format=%H", "--", dst_rel)
        self.assertEqual(follow.returncode, 0, follow.stderr)
        self.assertIn(
            pre_commit,
            follow.stdout.split(),
            "git log --follow on the relocated file does not reach the pre-migration commit, so "
            f"the committed history was lost:\n{follow.stdout}",
        )

        # (5) IGNORED IN EFFECT, attributed to the framework-owned file.
        ci = git(repo, "check-ignore", "-v", dst_rel)
        self.assertEqual(
            ci.returncode,
            0,
            f"the relocated run record is NOT ignored, so the migration re-tracked it: {ci.stderr}",
        )
        self.assertEqual(
            ci.stdout.split(":", 1)[0],
            ".aw/.gitignore",
            "the relocated file must be ignored by the framework-owned .aw/.gitignore",
        )
        self.assertFalse(
            INS.git_is_tracked(repo, dst_rel),
            "the relocated run record is still TRACKED, so run scratch is still committed (D92)",
        )

    def test_nothing_is_lost_the_path_sets_are_equal_modulo_the_prefix(self) -> None:
        """Kept separate: the unit is a whole path SET over six seeded files, not one path."""

        repo = _seed_committed_repo(self.base, "mig-pathsets")
        rels = [
            f"{self.RETIRED}/assess-bugs/20260726-115243/{name}"
            for name in ("decisions.md", "evidence.md", "findings.csv", "report.md")
        ] + [
            f"{self.RETIRED}/assess-testing/20260726-131500/{name}"
            for name in ("ipd-link.md", "report.md")
        ]
        for rel in rels:
            self._write(repo, rel, f"{rel}\n")
        self._commit(repo, self.RETIRED, message="seed two committed assess runs")
        before = self._run_record_paths(repo / self.RETIRED)
        self.assertEqual(len(before), 6, "precondition: six seeded run-record files")

        _install(repo)

        after = self._run_record_paths(repo / self.NEW)
        after_records = [p for p in after if p != "README.md"]
        self.assertEqual(
            before,
            after_records,
            "the before/after run-record path sets differ, so the migration lost or renamed "
            f"content:\nbefore={before}\nafter={after_records}",
        )
        for rel in before:
            self.assertEqual(
                (repo / self.NEW / rel).read_text(encoding="utf-8"),
                f"{self.RETIRED}/{rel}\n",
                f"content of {rel} changed during the migration",
            )

    def test_an_already_populated_destination_is_MERGED_not_replaced(self) -> None:
        """Kept separate: the claim is the UNION of two run ids under one workflow directory.

        (3) F-7: the destination usually already holds other runs of the SAME workflow, so this is a
        MERGE and not a move. The disposition table above varies one file at one path; this varies the
        directory's membership, which is a different assertion shape (a set equality over run ids).
        """

        repo = _seed_committed_repo(self.base, "mig-merge")
        _install(repo)  # gives the repo a real .aw/ tree and the ignore rule
        # A run already at the NEW home, under the same workflow name, with a different RUN_ID.
        kept_rel = f"{self.NEW}/assess-bugs/20260901-101010/report.md"
        self._write(repo, kept_rel, "already here\n")
        # And a legacy run at the retired path under that same workflow name.
        moved_src = f"{self.RETIRED}/assess-bugs/20260726-115243/report.md"
        self._write(repo, moved_src, "the legacy one\n")
        self._commit(
            repo, self.RETIRED, message="seed a legacy run beside an existing new one"
        )

        INS.migrate_root_workflow_artifacts(repo, use_git=True)

        self.assertTrue(
            (repo / kept_rel).is_file(),
            "the pre-existing destination run was destroyed by the migration (this is a MERGE)",
        )
        self.assertEqual(
            (repo / kept_rel).read_text(encoding="utf-8"),
            "already here\n",
            "the pre-existing destination run was overwritten",
        )
        moved_dst = f"{self.NEW}/assess-bugs/20260726-115243/report.md"
        self.assertTrue(
            (repo / moved_dst).is_file(), "the legacy run was not relocated"
        )
        self.assertEqual(
            (repo / moved_dst).read_text(encoding="utf-8"), "the legacy one\n"
        )
        # Both RUN_IDs now live under the one workflow directory: the union survived.
        self.assertEqual(
            sorted(p.name for p in (repo / self.NEW / "assess-bugs").iterdir()),
            ["20260726-115243", "20260901-101010"],
        )

    def test_untracked_content_is_moved_without_git(self) -> None:
        """Kept separate: the precondition (and half the claim) is git TRACKEDNESS, not content."""

        repo = _seed_committed_repo(self.base, "mig-untracked")
        _install(repo)
        src_rel = f"{self.RETIRED}/{self.RUN}/report.md"
        self._write(repo, src_rel, "never committed\n")
        self.assertFalse(INS.git_is_tracked(repo, src_rel), "precondition: untracked")

        INS.migrate_root_workflow_artifacts(repo, use_git=True)

        dst_rel = f"{self.NEW}/{self.RUN}/report.md"
        self.assertTrue((repo / dst_rel).is_file())
        self.assertEqual(
            (repo / dst_rel).read_text(encoding="utf-8"), "never committed\n"
        )
        self.assertFalse((repo / src_rel).exists())
        self.assertFalse(
            INS.git_is_tracked(repo, dst_rel),
            "an untracked run record must not become tracked by being relocated",
        )

    def test_the_readme_only_case_is_removed_not_relocated(self) -> None:
        """Kept separate: the ONLY case where user content is deliberately DELETED, not moved.

        Case (c), the COMMON case: the stray README's content was the opposite of the rule, so it is
        superseded rather than relocated. It is the documented exception to the never-delete invariant
        the disposition table's identical-bytes row relies on, which is why it cannot be a row there.
        """

        repo = _seed_committed_repo(self.base, "mig-readme")
        retired_readme = f"{self.RETIRED}/README.md"
        self._write(
            repo,
            retired_readme,
            "# Workflow Run Artifacts\n\n* **DO NOT gitignore this folder.**\n",
        )
        self._commit(repo, self.RETIRED, message="seed the stray README")

        _install(repo)

        self.assertFalse(
            (repo / retired_readme).exists(),
            "the superseded stray README was left at the retired path",
        )
        self.assertFalse(
            (repo / self.RETIRED).exists(),
            "the retired directory should be gone once its only file was the stray README",
        )
        new_readme = repo / self.NEW / "README.md"
        self.assertTrue(
            new_readme.is_file(),
            "the new tree did not get its own README from the install",
        )
        self.assertNotIn(
            "DO NOT gitignore",
            new_readme.read_text(encoding="utf-8"),
            "the retired do-not-ignore prose was carried to the new home",
        )

    def test_a_repo_with_no_retired_directory_is_a_silent_no_op(self) -> None:
        """Kept separate: asserts an EMPTY action list, which no disposition row can state."""
        # OQ-01: report only when there is something to report.
        repo = _seed_committed_repo(self.base, "mig-noop")
        _install(repo)
        self.assertEqual(INS.migrate_root_workflow_artifacts(repo, use_git=True), [])

    def test_dry_run_reports_and_touches_nothing(self) -> None:
        """Kept separate: the only call with `dry_run=True`, and it pins git STATUS and HEAD."""
        repo = _seed_committed_repo(self.base, "mig-dryrun")
        _install(repo)
        src_rel = f"{self.RETIRED}/{self.RUN}/report.md"
        self._write(repo, src_rel, "untouched\n")
        self._commit(repo, self.RETIRED, message="seed for dry-run")
        before_status = git(repo, "status", "--porcelain").stdout
        before_head = git(repo, "rev-parse", "HEAD").stdout.strip()

        actions = INS.migrate_root_workflow_artifacts(repo, use_git=True, dry_run=True)

        self.assertTrue(any("dry-run" in a for a in actions), actions)
        self.assertTrue((repo / src_rel).is_file(), "dry-run MOVED a file")
        self.assertFalse(
            (repo / self.NEW / self.RUN / "report.md").exists(),
            "dry-run created the destination",
        )
        self.assertEqual(
            git(repo, "status", "--porcelain").stdout,
            before_status,
            "dry-run changed the git status",
        )
        self.assertEqual(
            git(repo, "rev-parse", "HEAD").stdout.strip(),
            before_head,
            "dry-run created a commit",
        )

    def test_the_migration_commit_does_not_sweep_in_unrelated_staged_work(self) -> None:
        """Kept separate: the subject is a CO-WORKER's staged file, a setup no other test has.

        This is a SHARED CHECKOUT: the relocation's commits are path-scoped, so a co-worker's staged
        file must not be swept into them (repository execution contract).
        """

        repo = _seed_committed_repo(self.base, "mig-scoped")
        _install(repo)
        src_rel = f"{self.RETIRED}/{self.RUN}/report.md"
        self._write(repo, src_rel, "mine\n")
        self._commit(repo, self.RETIRED, message="seed for scoping")
        coworker = repo / "coworker.txt"
        coworker.write_text("someone else's staged work\n", encoding="utf-8")
        git(repo, "add", "--", "coworker.txt")

        INS.migrate_root_workflow_artifacts(repo, use_git=True)

        staged = git(repo, "diff", "--cached", "--name-only").stdout.split()
        self.assertIn(
            "coworker.txt",
            staged,
            "the migration committed (or unstaged) a co-worker's staged file",
        )
        log = git(repo, "log", "--name-only", "--format=%H").stdout
        self.assertNotIn(
            "coworker.txt", log, "a co-worker's file was swept into a migration commit"
        )

    def test_run_records_in_a_records_quarantine_lane_are_REPORTED_not_moved(
        self,
    ) -> None:
        """Kept separate: a REPORT-ONLY disposition over a different tree, asserting a move did NOT happen.

        E-04 / decision D-02: the observed mis-relocation is reported, never swept up.
        `records/*/untracked/` is a legitimate box-local quarantine lane for MANY record types, so the
        installer cannot tell a mis-placed run record there from a human's in-progress typed record.
        It therefore reports and moves nothing.
        """

        repo = _seed_committed_repo(self.base, "mig-misplaced")
        _install(repo)
        stray = ".aw/records/reviews/untracked/20260726-115243/report.md"
        self._write(repo, stray, "mis-relocated run record\n")

        actions = INS.migrate_root_workflow_artifacts(repo, use_git=True)

        self.assertTrue(
            any("REPORT ONLY" in a for a in actions),
            f"the mis-placed run records were not reported: {actions}",
        )
        self.assertTrue(
            (repo / stray).is_file(),
            "the installer MOVED content out of a records quarantine lane; it must only report",
        )
        self.assertFalse(
            (repo / self.NEW / "20260726-115243").exists(),
            "content was swept from a records lane into the run-scratch tree",
        )

    def test_an_ordinary_wip_file_in_a_quarantine_lane_is_silent(self) -> None:
        """Kept separate: the NEGATIVE half of the report-only rule, and it asserts an empty list.

        The detection is narrow on purpose: only `<RUN_ID>`-shaped directories are reported, so the
        legitimate use of these lanes never nags the user.
        """

        repo = _seed_committed_repo(self.base, "mig-lane-quiet")
        _install(repo)
        self._write(repo, ".aw/records/prompts/untracked/draft.md", "wip\n")

        self.assertEqual(INS.migrate_root_workflow_artifacts(repo, use_git=True), [])

    def test_the_migration_runs_from_the_shared_install_chokepoint(self) -> None:
        """Kept separate: the claim is about install_into_repo's RETURN value, not the filesystem.

        E-02: wired into `install_into_repo`, so `aw install`, `aw setup` and library callers all get
        it. A `run()`-only wiring would leave `aw setup` silently doing nothing.
        """

        repo = _seed_committed_repo(self.base, "mig-chokepoint")
        src_rel = f"{self.RETIRED}/{self.RUN}/report.md"
        self._write(repo, src_rel, "via the chokepoint\n")
        self._commit(repo, self.RETIRED, message="seed for chokepoint")

        result = _install(repo)

        self.assertTrue(
            any("workflow-artifacts" in line for line in result["migrated"]),
            f"the migration did not report through install_into_repo: {result['migrated']}",
        )
        self.assertTrue((repo / self.NEW / self.RUN / "report.md").is_file())

    def test_reinstall_is_idempotent(self) -> None:
        """Kept separate: a before/after idempotence PAIR, whose two halves are one claim."""
        repo = _seed_committed_repo(self.base, "mig-idempotent")
        src_rel = f"{self.RETIRED}/{self.RUN}/report.md"
        self._write(repo, src_rel, "once\n")
        self._commit(repo, self.RETIRED, message="seed for idempotence")

        _install(repo)
        first = self._run_record_paths(repo / self.NEW)
        _install(repo)
        second = self._run_record_paths(repo / self.NEW)

        self.assertEqual(first, second, "a second install changed the relocated tree")
        self.assertFalse((repo / self.RETIRED).exists())


if __name__ == "__main__":
    unittest.main()
