"""Install-time emission of the machine-readable layout artifacts (`wslayout` Order 04 `hauwqh`;
spec `kw5y2s` Section 6.1).

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
"""

from __future__ import annotations

import argparse
import json
import stat
import tempfile
import unittest
from pathlib import Path

from tests.support import SOURCE_WORKFLOWS, git, init_repo

from agent_workflows import cli as CLI
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
    """E-01/V-01: a fresh install writes both artifacts, at mode 0o644, with the right version."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_fresh_install_emits_both_layout_artifacts(self) -> None:
        repo = _seed_committed_repo(self.base, "fresh")
        result = _install(repo)

        self.assertEqual(result["target_layout"], "aw")
        self.assertTrue(
            (repo / LAYOUT_JSON).is_file(), f"{LAYOUT_JSON} was not emitted by install"
        )
        self.assertTrue(
            (repo / LAYOUT_SCHEMA).is_file(),
            f"{LAYOUT_SCHEMA} was not emitted by install",
        )
        self.assertEqual(
            sorted(result["layout_artifacts"]), sorted([LAYOUT_JSON, LAYOUT_SCHEMA])
        )

    def test_emitted_files_are_mode_0644(self) -> None:
        # Spec kw5y2s 6.1 clause 2: mode 0o644 (world-readable, not executable), since a non-Python
        # consumer may run as a different user than the one that installed.
        repo = _seed_committed_repo(self.base, "modes")
        _install(repo)
        for rel in (LAYOUT_JSON, LAYOUT_SCHEMA):
            mode = stat.S_IMODE((repo / rel).stat().st_mode)
            self.assertEqual(mode, 0o644, f"{rel} has mode {oct(mode)}, want 0o644")

    def test_framework_version_matches_the_installed_version_file(self) -> None:
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
        # Structural conformance with the STDLIB (no `jsonschema` dependency), the same approach
        # tests/test_layout.py takes: every required top-level key present, no undeclared key, and
        # each declared type honored. The point is that the two EMITTED files agree with each other,
        # so a consumer validating on disk succeeds.
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

    def test_emitted_content_is_exactly_the_canonical_model_serialization(self) -> None:
        # No forked serializer: the installer must emit `layout.build_default_layout()`'s own output,
        # so `aw layout` (Order 05) and a file-reading consumer can never disagree.
        repo = _seed_committed_repo(self.base, "canonical")
        _install(repo)
        model = LAYOUT.build_default_layout()
        version = (repo / ".aw/system/VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(
            (repo / LAYOUT_JSON).read_text(encoding="utf-8"), model.to_json(version)
        )
        self.assertEqual(
            (repo / LAYOUT_SCHEMA).read_text(encoding="utf-8"), model.to_schema_json()
        )

    def test_reinstall_at_same_version_rewrites_nothing(self) -> None:
        # V-01 determinism: byte-identical AND not rewritten. The mtime assertion is the one that
        # actually pins "no-op rather than a rewrite" - a nondeterministic serializer that happened to
        # produce equal bytes would still fail an mtime check, and a needless rewrite churns the file
        # for every watcher in the target repo.
        repo = _seed_committed_repo(self.base, "idem")
        _install(repo)
        before = {
            rel: (
                (repo / rel).read_bytes(),
                (repo / rel).stat().st_mtime_ns,
            )
            for rel in (LAYOUT_JSON, LAYOUT_SCHEMA)
        }

        result = _install(repo)
        self.assertEqual(
            result["layout_artifacts"],
            [],
            "a re-install at the same version must report no layout writes",
        )
        for rel, (content, mtime) in before.items():
            self.assertEqual(
                (repo / rel).read_bytes(), content, f"{rel} content churned"
            )
            self.assertEqual(
                (repo / rel).stat().st_mtime_ns,
                mtime,
                f"{rel} was needlessly rewritten",
            )

    def test_stale_content_is_refreshed(self) -> None:
        # The skip-unchanged optimization must not become a skip-always: a corrupted or
        # previous-version file has to be brought back into line by the next install.
        repo = _seed_committed_repo(self.base, "stale")
        _install(repo)
        (repo / LAYOUT_JSON).write_text("{}\n", encoding="utf-8")
        result = _install(repo)
        self.assertIn(LAYOUT_JSON, result["layout_artifacts"])
        doc = json.loads((repo / LAYOUT_JSON).read_text(encoding="utf-8"))
        self.assertIn("record_classes", doc, "stale layout.json was not regenerated")


class LayoutEmissionSiteTests(unittest.TestCase):
    """E-01/V-01: emission lives in the SHARED core, so every install path inherits it."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_emission_is_reached_through_the_cli_install_one_path(self) -> None:
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

    def test_no_emission_code_in_the_setup_repo_workflow_body(self) -> None:
        # PR-003: `/aw setup-repo` is an agent slash-command backed by a workflow BODY, not a CLI verb
        # and not a Python entry point, so it inherits emission transitively and must contain no
        # emission code of its own.
        body = (
            Path(INS.__file__).resolve().parent.parent
            / ".aw/system/workflows/setup-repo/setup-repo.md"
        )
        if not body.is_file():
            self.skipTest("setup-repo workflow body not present in this checkout")
        text = body.read_text(encoding="utf-8")
        self.assertNotIn("emit_layout_artifacts", text)
        self.assertNotIn("build_default_layout", text)

    def test_dry_run_emits_nothing(self) -> None:
        # A dry run must report without writing; otherwise `--dry-run` mutates the repo it is
        # previewing.
        repo = _seed_committed_repo(self.base, "dry")
        INS.install_into_repo(
            repo, SOURCE_WORKFLOWS, dry_run=True, yes=True, no_color=True
        )
        self.assertFalse((repo / LAYOUT_JSON).exists())
        self.assertFalse((repo / LAYOUT_SCHEMA).exists())

    def test_legacy_layout_target_gets_no_aw_system_artifacts(self) -> None:
        # The emitted paths are `.aw/system/` paths by definition. A repo deliberately left on the
        # legacy `.agents/workflows` layout must not be half-migrated by having `.aw/system/` created
        # under it just to hold generated output.
        repo = init_repo(self.base / "legacy")
        (repo / ".agents/workflows").mkdir(parents=True)
        (repo / ".agents/workflows/index.md").write_text("# index\n", encoding="utf-8")
        self.assertEqual(INS.resolve_target_layout(repo), "legacy")
        self.assertEqual(INS.emit_layout_artifacts(repo), [])
        self.assertFalse((repo / LAYOUT_JSON).exists())


class LayoutArtifactsGitignoreTests(unittest.TestCase):
    """E-02/V-02: both artifacts are ignored via the GENERATED `.aw/.gitignore`, on both paths."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _ignore_source(self, repo: Path, rel: str) -> str:
        """The gitignore FILE git attributes the rule to, per `git check-ignore -v`."""

        res = git(repo, "check-ignore", "-v", rel)
        self.assertEqual(
            res.returncode, 0, f"{rel} is not gitignored at all (stderr: {res.stderr})"
        )
        return res.stdout.split(":", 1)[0]

    def test_template_carries_both_patterns(self) -> None:
        # A FRESH install writes the template verbatim, so the patterns must be in the template
        # itself, not only in the back-fill list.
        for pattern in IGNORE_PATTERNS:
            self.assertIn(f"\n{pattern}\n", INS._AW_GITIGNORE_TEMPLATE)

    def test_fresh_install_ignores_both_emitted_files(self) -> None:
        repo = _seed_committed_repo(self.base, "ignored")
        _install(repo)

        aw_gitignore = (repo / ".aw/.gitignore").read_text(encoding="utf-8")
        for pattern in IGNORE_PATTERNS:
            self.assertIn(f"\n{pattern}\n", aw_gitignore)

        porcelain = git(repo, "status", "--porcelain").stdout
        self.assertNotIn(
            "layout.json",
            porcelain,
            f"an emitted layout artifact is visible to git:\n{porcelain}",
        )

        for rel in (LAYOUT_JSON, LAYOUT_SCHEMA):
            self.assertEqual(
                self._ignore_source(repo, rel),
                ".aw/.gitignore",
                f"{rel} must be ignored by the framework-owned .aw/.gitignore",
            )

    def test_root_gitignore_carries_no_layout_entry(self) -> None:
        # PR-027 precision. The installer DOES legitimately write to the target's ROOT `.gitignore`
        # (`ensure_untracked_gitignore` adds a managed `aw:block`; `ensure_backups_gitignored` adds the
        # backups line), so "root file unchanged" is the wrong assertion and would fail for a
        # legitimate reason. What THIS plan must never do is put a LAYOUT entry there.
        repo = _seed_committed_repo(self.base, "rootfile")
        _install(repo)
        root_text = (repo / ".gitignore").read_text(encoding="utf-8")
        self.assertNotIn(
            "layout", root_text, "a layout entry leaked into the ROOT .gitignore"
        )
        self.assertIn(
            "*.user-tmp",
            root_text,
            "the installer clobbered the user's own .gitignore line",
        )

    def test_backfill_adds_the_patterns_to_a_pre_existing_gitignore(self) -> None:
        # The path a template-only edit silently fails: a repo installed BEFORE emission existed
        # already HAS a `.aw/.gitignore`, so `_ensure_aw_gitignore` takes the append branch and never
        # re-reads the template.
        repo = _seed_committed_repo(self.base, "backfill")
        _install(repo)
        gi = repo / ".aw/.gitignore"
        stripped = "\n".join(
            line
            for line in gi.read_text(encoding="utf-8").splitlines()
            if line.strip() not in IGNORE_PATTERNS
        )
        gi.write_text(stripped + "\n", encoding="utf-8")
        for pattern in IGNORE_PATTERNS:
            self.assertNotIn(f"\n{pattern}\n", gi.read_text(encoding="utf-8"))

        INS._ensure_aw_gitignore(repo)

        text = gi.read_text(encoding="utf-8")
        for pattern in IGNORE_PATTERNS:
            lines = [ln for ln in text.splitlines() if ln.strip() == pattern]
            self.assertEqual(
                len(lines),
                1,
                f"back-fill wrote {len(lines)} copies of {pattern}, want 1",
            )
        for rel in (LAYOUT_JSON, LAYOUT_SCHEMA):
            self.assertEqual(self._ignore_source(repo, rel), ".aw/.gitignore")

    def test_backfill_is_idempotent(self) -> None:
        # `_ensure_aw_gitignore` is called on several install steps and by `write_setup_marker`, so a
        # non-idempotent addition would accrue duplicate lines on every run.
        repo = _seed_committed_repo(self.base, "backfill-idem")
        _install(repo)
        for _ in range(3):
            INS._ensure_aw_gitignore(repo)
        text = (repo / ".aw/.gitignore").read_text(encoding="utf-8")
        for pattern in IGNORE_PATTERNS:
            self.assertEqual(
                len([ln for ln in text.splitlines() if ln.strip() == pattern]),
                1,
                f"duplicate {pattern} line after repeated _ensure_aw_gitignore calls",
            )

    def test_reinstall_does_not_duplicate_the_patterns(self) -> None:
        repo = _seed_committed_repo(self.base, "reinstall-idem")
        _install(repo)
        _install(repo)
        text = (repo / ".aw/.gitignore").read_text(encoding="utf-8")
        for pattern in IGNORE_PATTERNS:
            self.assertEqual(
                len([ln for ln in text.splitlines() if ln.strip() == pattern]), 1
            )

    def test_tracked_comms_inbox_lane_is_still_not_ignored(self) -> None:
        # Regression fence on the neighbouring rule the template documents at length: adding patterns
        # must not disturb the anchored `/inbox/` rule that keeps the TRACKED comms lane visible.
        repo = _seed_committed_repo(self.base, "inbox")
        _install(repo)
        lane = repo / ".aw/records/comms/shared/inbox/.gitkeep"
        lane.parent.mkdir(parents=True, exist_ok=True)
        lane.write_text("", encoding="utf-8")
        self.assertNotEqual(
            git(
                repo, "check-ignore", "-q", ".aw/records/comms/shared/inbox/.gitkeep"
            ).returncode,
            0,
            "the TRACKED comms inbox lane must NOT be gitignored",
        )


class ManifestIndexGitignoreTests(unittest.TestCase):
    """idxuntrack Order 02 (yvvf98 E-05/E-06): the four generated manifest indexes are gitignored.

    Deliberately mirrors `LayoutArtifactsGitignoreTests` above rather than introducing a new harness,
    per E-05: that class already solved this exact problem shape (a generated, gitignored artifact
    proven ignored IN EFFECT with real `git check-ignore`, on BOTH the fresh-template and the
    back-fill code paths, attributed to `.aw/.gitignore` and not the user's root file).

    WHY A GUARD TEST AT ALL, since the gitignore lines are right there in the source: the failure this
    fences is a SILENT RE-TRACKING. The manifests are regenerated on nearly every `aw` status write,
    so if a future change drops a pattern, the files reappear as tracked content and the churn plus
    the lane-conflict failure class both return with nothing failing to say so.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _ignore_source(self, repo: Path, rel: str) -> str:
        """The gitignore FILE git attributes the rule to, per `git check-ignore -v`."""

        res = git(repo, "check-ignore", "-v", rel)
        self.assertEqual(
            res.returncode, 0, f"{rel} is not gitignored at all (stderr: {res.stderr})"
        )
        return res.stdout.split(":", 1)[0]

    def _materialize(self, repo: Path) -> None:
        """Create the four manifests on disk, as `aw index` would."""

        for rel in MANIFEST_PATHS:
            p = repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("{}\n", encoding="utf-8")

    def test_template_carries_all_four_patterns(self) -> None:
        # A FRESH install writes the template verbatim, so the patterns must be in the template
        # itself, not only in the back-fill list.
        for pattern in MANIFEST_IGNORE_PATTERNS:
            self.assertIn(f"\n{pattern}\n", INS._AW_GITIGNORE_TEMPLATE)

    def test_patterns_are_anchored_specific_paths_not_bare_index_names(self) -> None:
        # The `/inbox/` trap the template documents at length: a bare `INDEX.json` is unanchored and
        # would match an INDEX.json at ANY depth in ANY tree, silently swallowing unrelated files.
        lines = [
            ln.strip()
            for ln in INS._AW_GITIGNORE_TEMPLATE.splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
        for bare in ("INDEX.json", "INDEX.md"):
            self.assertNotIn(
                bare,
                lines,
                f"a BARE {bare} pattern matches at any depth; write the specific paths",
            )

    def test_fresh_install_ignores_all_four_manifests(self) -> None:
        repo = _seed_committed_repo(self.base, "manifests-fresh")
        _install(repo)
        self._materialize(repo)

        aw_gitignore = (repo / ".aw/.gitignore").read_text(encoding="utf-8")
        for pattern in MANIFEST_IGNORE_PATTERNS:
            self.assertIn(f"\n{pattern}\n", aw_gitignore)

        porcelain = git(repo, "status", "--porcelain").stdout
        self.assertNotIn(
            "INDEX.",
            porcelain,
            f"a generated manifest index is visible to git:\n{porcelain}",
        )

        for rel in MANIFEST_PATHS:
            self.assertEqual(
                self._ignore_source(repo, rel),
                ".aw/.gitignore",
                f"{rel} must be ignored by the framework-owned .aw/.gitignore",
            )

    def test_manifests_are_untracked_after_install(self) -> None:
        # The outcome the item exists for, asserted on the INDEX rather than on the ignore file: a
        # pattern can be present while the path is still TRACKED (gitignore does not untrack), which
        # is precisely the state this plan's `git rm --cached` had to fix.
        repo = _seed_committed_repo(self.base, "manifests-untracked")
        _install(repo)
        self._materialize(repo)
        git(repo, "add", "-A")
        tracked = git(repo, "ls-files").stdout.splitlines()
        offenders = [p for p in tracked if p.endswith(("INDEX.json", "INDEX.md"))]
        self.assertEqual(
            offenders, [], f"generated manifest indexes got tracked: {offenders}"
        )

    def test_root_gitignore_carries_no_manifest_entry(self) -> None:
        # Same precision as the layout twin: `.aw/` is framework-owned and is the correct home; the
        # user's ROOT `.gitignore` must never gain one of these rules.
        repo = _seed_committed_repo(self.base, "manifests-rootfile")
        _install(repo)
        root_text = (repo / ".gitignore").read_text(encoding="utf-8")
        self.assertNotIn(
            "INDEX.", root_text, "a manifest entry leaked into the ROOT .gitignore"
        )
        self.assertIn(
            "*.user-tmp",
            root_text,
            "the installer clobbered the user's own .gitignore line",
        )

    def test_backfill_adds_the_patterns_to_a_pre_existing_gitignore(self) -> None:
        # The ONLY path that reaches an ALREADY-INSTALLED repo, and the one a template-only edit
        # silently fails: such a repo already HAS a `.aw/.gitignore`, so `_ensure_aw_gitignore` takes
        # the append branch and never re-reads the template.
        repo = _seed_committed_repo(self.base, "manifests-backfill")
        _install(repo)
        gi = repo / ".aw/.gitignore"
        stripped = "\n".join(
            line
            for line in gi.read_text(encoding="utf-8").splitlines()
            if line.strip() not in MANIFEST_IGNORE_PATTERNS
        )
        gi.write_text(stripped + "\n", encoding="utf-8")
        for pattern in MANIFEST_IGNORE_PATTERNS:
            self.assertNotIn(f"\n{pattern}\n", gi.read_text(encoding="utf-8"))
        # The pre-existing content must survive the back-fill (no clobber).
        self.assertIn("records/*/untracked/", gi.read_text(encoding="utf-8"))

        INS._ensure_aw_gitignore(repo)

        text = gi.read_text(encoding="utf-8")
        self.assertIn(
            "records/*/untracked/", text, "back-fill clobbered pre-existing content"
        )
        for pattern in MANIFEST_IGNORE_PATTERNS:
            lines = [ln for ln in text.splitlines() if ln.strip() == pattern]
            self.assertEqual(
                len(lines),
                1,
                f"back-fill wrote {len(lines)} copies of {pattern}, want 1",
            )
        self._materialize(repo)
        for rel in MANIFEST_PATHS:
            self.assertEqual(self._ignore_source(repo, rel), ".aw/.gitignore")

    def test_backfill_is_idempotent(self) -> None:
        repo = _seed_committed_repo(self.base, "manifests-backfill-idem")
        _install(repo)
        for _ in range(3):
            INS._ensure_aw_gitignore(repo)
        text = (repo / ".aw/.gitignore").read_text(encoding="utf-8")
        for pattern in MANIFEST_IGNORE_PATTERNS:
            self.assertEqual(
                len([ln for ln in text.splitlines() if ln.strip() == pattern]),
                1,
                f"duplicate {pattern} line after repeated _ensure_aw_gitignore calls",
            )

    def test_reinstall_does_not_duplicate_the_patterns(self) -> None:
        repo = _seed_committed_repo(self.base, "manifests-reinstall-idem")
        _install(repo)
        _install(repo)
        text = (repo / ".aw/.gitignore").read_text(encoding="utf-8")
        for pattern in MANIFEST_IGNORE_PATTERNS:
            self.assertEqual(
                len([ln for ln in text.splitlines() if ln.strip() == pattern]), 1
            )

    def test_template_and_this_repos_own_gitignore_agree(self) -> None:
        # F-7: this repo's `.aw/.gitignore` is byte-identical to the template, and the next install
        # would re-diff the repo against its own template if E-01 and E-06 ever diverged.
        own = Path(__file__).resolve().parents[1] / ".aw/.gitignore"
        if not own.is_file():  # pragma: no cover - not a managed checkout
            self.skipTest("no .aw/.gitignore in this checkout")
        self.assertEqual(
            own.read_text(encoding="utf-8"),
            INS._AW_GITIGNORE_TEMPLATE,
            "this repo's .aw/.gitignore and _AW_GITIGNORE_TEMPLATE have diverged",
        )

    def test_unrelated_index_json_at_another_depth_is_not_ignored(self) -> None:
        # The anchoring proven IN EFFECT, not just by reading the pattern: a file that happens to be
        # named INDEX.json somewhere else must stay visible to git.
        repo = _seed_committed_repo(self.base, "manifests-anchor")
        _install(repo)
        other = repo / "docs/INDEX.json"
        other.parent.mkdir(parents=True, exist_ok=True)
        other.write_text("{}\n", encoding="utf-8")
        self.assertNotEqual(
            git(repo, "check-ignore", "-q", "docs/INDEX.json").returncode,
            0,
            "an unrelated INDEX.json outside .aw/records was swallowed by an unanchored pattern",
        )


if __name__ == "__main__":
    unittest.main()
