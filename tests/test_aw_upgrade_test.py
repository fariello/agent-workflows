"""Tests for the upgrade-rehearsal harness ``tools/aw_upgrade_test.py``.

WHAT THESE TESTS ARE FOR. The harness copies REAL repositories and runs a MUTATING installer
against the copy, so its own bugs could damage real work. These tests therefore target the
four safety invariants the harness documents, plus the inspection logic a rehearsal's
conclusions rest on. They deliberately do NOT test whether an upgrade produces a correct
result: judging that is the human's job, and encoding an opinion here would turn an
evidence-gathering rig into an unreviewed spec.

Every test builds its own throwaway git repo, so nothing here touches a real repository or
the operator's real config.

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: build a throwaway
repo in a named on-disk state, call one inspection function, assert one value. The tables group by
SUBJECT (the version probe, the layout classifier, the observation deriver, the sandbox-creation
contract, the argument parser) rather than by which safety invariant motivated the check, because
the closed sets this harness is built on (the four layout classifications, the observation kinds,
the two copy strategies, the three ``clean`` actions) are what a reader needs to browse as sets and
what a refactor moves SEVERAL of at once.

WHERE A DISTINCTION IS A MODE IT IS A COLUMN. The COPY STRATEGY (``full`` versus ``clone``) is the
load-bearing one: invariant 1 must hold for BOTH, and the old file asserted it for ``full`` only,
so a hardlinking ``clone`` would have shipped green. The ``force`` flag on ``clean`` is a column for
the same reason: the contract is that it changes NOTHING, which no single-value test can state.

Tests that are NOT rows carry a one-line docstring saying why they stay separate. The recurring
reasons: the claim is an assertRaises refusal; the setup is materially different (a real
subprocess, a git worktree, an environment-variable swap); the assertion is over a source file's
text rather than over behavior; or the test is a before/after pair whose whole content is the
comparison.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import REPO_ROOT, git, init_repo, load_module  # noqa: E402

TOOL = REPO_ROOT / "tools" / "aw_upgrade_test.py"
uat = load_module("aw_upgrade_test", TOOL)


def make_source_repo(
    path: Path, version: str = "1.2.1", layout: str = "legacy"
) -> Path:
    """Build a fake installed repo at ``path`` resembling a real managed target."""

    init_repo(path)
    if layout == "legacy":
        wf = path / ".agents" / "workflows"
        wf.mkdir(parents=True)
        (wf / "VERSION").write_text(f"{version}\n", encoding="utf-8")
        (wf / "index.md").write_text("# workflows\n", encoding="utf-8")
    elif layout == "aw":
        sysd = path / ".aw" / "system"
        sysd.mkdir(parents=True)
        (sysd / "VERSION").write_text(f"{version}\n", encoding="utf-8")
        (sysd / "managed-sections.json").write_text(
            json.dumps(
                {"schema_version": 2, "installed_version": version, "files": {}}
            ),
            encoding="utf-8",
        )
    elif layout == "dual":
        make_source_repo(path, version, "legacy")
        sysd = path / ".aw" / "system"
        sysd.mkdir(parents=True, exist_ok=True)
        (sysd / "VERSION").write_text(f"{version}\n", encoding="utf-8")
        return path
    (path / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (path / "README.md").write_text("# project\n", encoding="utf-8")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "seed")
    return path


class TempCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()


class InspectionTests(TempCase):
    """Version/layout detection: the basis of every claim a rehearsal report makes.

    THREE TABLES replace twelve tests here, one per inspection function, because the twelve had one
    shape: build a repo in a named on-disk state, call one probe, assert one value. What the class
    boundaries used to track was which SAFETY INVARIANT motivated the check, which is a property of
    the plan rather than of the subject; the subject is "what does this function report about a tree
    in state X", and that is a row.
    """

    #: (case, the layout `make_source_repo` builds or None for a bare git repo, an extra
    #: `.aw/system/VERSION` to plant or None, the expected (version, relative path), why this row
    #: exists)
    VERSION_PROBES = (
        (
            "both locations populated",
            "legacy",
            "9.9.9",
            ("9.9.9", ".aw/system/VERSION"),
            "THE PRECEDENCE RULE, and the only row that can state it: `VERSION_LOCATIONS` is "
            "ordered newest-layout-first and the probe returns the FIRST hit, so a repo mid-"
            "migration must report the canonical number. A probe that read the legacy file here "
            "would make every rehearsal of a dual-layout repo report the version it upgraded FROM",
        ),
        (
            "the legacy location only",
            "legacy",
            None,
            ("1.2.1", ".agents/workflows/VERSION"),
            "the fallback must still work, or the harness cannot rehearse the pre-migration repos "
            "that are its main input. This row is what stops the precedence rule above from being "
            "implemented as `only ever read .aw/system`",
        ),
        (
            "the canonical location only",
            "aw",
            None,
            ("1.2.1", ".aw/system/VERSION"),
            "the ordinary post-migration repo. Kept beside the legacy row so the PATH half of the "
            "return value is pinned for both layouts: the path is what the report shows a human, so "
            "a correct number attributed to the wrong file is still a wrong claim",
        ),
        (
            "no framework installed at all",
            None,
            None,
            (None, None),
            "ABSENCE IS (None, None), NOT AN EXCEPTION and not an empty string. `list` calls this "
            "over every discovered repo, most of which are unmanaged, so a raise here would make "
            "the harness unable to enumerate candidates at all",
        ),
    )

    def test_the_version_probe_reports_the_right_file_in_every_layout(self) -> None:
        wrong = []
        for index, (case, layout, planted, expected, why) in enumerate(
            self.VERSION_PROBES
        ):
            repo = self.tmp / f"v{index}"
            if layout is None:
                init_repo(repo)
            else:
                make_source_repo(repo, "1.2.1", layout)
            if planted is not None:
                sysd = repo / ".aw" / "system"
                sysd.mkdir(parents=True, exist_ok=True)
                (sysd / "VERSION").write_text(f"{planted}\n", encoding="utf-8")
            got = uat.installed_version(repo)
            if got != expected:
                wrong.append(
                    f"  {case}: expected {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"uat.installed_version reported the wrong (version, path) for {len(wrong)} of "
            f"{len(self.VERSION_PROBES)} layouts. One ORDERED tuple, `VERSION_LOCATIONS`, decides "
            "every row, so read them together: if the two single-location rows are right and only "
            "the both-populated row is wrong, the tuple was REORDERED and every dual-layout "
            "rehearsal now reports the version it upgraded from. If several rows return the same "
            "path, the loop stopped iterating. FIX: this probe must stay a mirror of "
            "`engine.read_installed_version`; if the installer's own precedence changed, change "
            "this table to match it and say so, because a harness that reports a different number "
            "than the installer invalidates every rehearsal conclusion.\n"
            + "\n".join(wrong),
        )

    #: (case, plan(repo) -> None building the on-disk state, expected `detect_layout` result,
    #: expected `count_empty_dirs(repo/'.agents')` or None to skip, why this row exists)
    LAYOUTS = (
        (
            "the canonical layout only",
            lambda repo: make_source_repo(repo, "1.2.1", "aw"),
            "aw",
            0,
            "the finished-migration baseline. It is in the table as the CLEAN row: a classifier "
            "that answered `dual` for everything would satisfy the split-brain row below on its own",
        ),
        (
            "the legacy layout only",
            lambda repo: make_source_repo(repo, "1.2.1", "legacy"),
            "legacy",
            0,
            "the pre-migration baseline, which is the harness's primary rehearsal INPUT, so "
            "misclassifying it would misdirect every observation derived downstream",
        ),
        (
            "real files on BOTH sides",
            lambda repo: (
                make_source_repo(repo, "1.2.1", "dual"),
                (repo / ".agents" / "workflows" / "VERSION").write_text(
                    "1.0.0\n", encoding="utf-8"
                ),
            ),
            "dual",
            0,
            "GENUINE SPLIT-BRAIN, the state the installer's own guard refuses and a legitimate "
            "rehearsal input. It requires LIVE FILES on both sides, which is the whole distinction "
            "from the litter row below",
        ),
        (
            "migrated, with EMPTY legacy directories left behind",
            lambda repo: (
                make_source_repo(repo, "1.2.1", "aw"),
                [
                    (repo / ".agents" / "workflows" / sub).mkdir(parents=True)
                    for sub in ("assess/tools", "verify/tools", "benchmark")
                ],
            ),
            "aw+litter",
            # 7, EXACTLY: the three created leaves, their two intermediate parents (`assess`,
            # `verify`), plus `.agents/workflows` and `.agents` themselves, every one of which holds
            # no file at any depth. Pinned as a number rather than `> 0` (what the test this replaces
            # asserted) because the count is what a human reads to judge how much litter there is, so
            # a walk that stopped recursing or stopped counting the intermediates would still satisfy
            # `> 0` while under-reporting the mess.
            7,
            "THE MEASURED DEFECT: a real finished migration left 9 EMPTY legacy directories, and a "
            "classifier keying on directory EXISTENCE called that `dual`, conflating harmless litter "
            "with the state the installer refuses. Classification is therefore by live file "
            "CONTENT, and this row sits directly beside the `dual` row because the pair is what "
            "states the difference. The empty-dir count is asserted here too: litter is only "
            "actionable if the count reaches the report",
        ),
        (
            "no framework at all",
            lambda repo: init_repo(repo),
            "none",
            0,
            "an unmanaged repo must classify as `none` rather than defaulting to a layout, because "
            "`list` runs this over every discovered directory and a default would report unmanaged "
            "repos as installed ones",
        ),
    )

    def test_the_layout_classifier_keys_on_live_content_in_every_state(self) -> None:
        wrong = []
        for index, (case, plan, expected, empty_dirs, why) in enumerate(self.LAYOUTS):
            repo = self.tmp / f"L{index}"
            plan(repo)
            problems = []
            got = uat.detect_layout(repo)
            if got != expected:
                problems.append(f"detect_layout expected {expected!r}, got {got!r}")
            if empty_dirs is not None:
                counted = uat.count_empty_dirs(repo / ".agents")
                if counted != empty_dirs:
                    problems.append(
                        f"count_empty_dirs expected {empty_dirs}, got {counted}"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"detect_layout classified {len(wrong)} of {len(self.LAYOUTS)} on-disk states wrongly. "
            "Every row is decided by two `has_files` calls plus a directory-existence fallback, so "
            "read them together: if `dual` and `aw+litter` swapped, classification reverted to "
            "keying on directory EXISTENCE and harmless migration litter is again being reported as "
            "the split-brain state the installer refuses (the measured 2026 defect). If the two "
            "single-layout rows also moved, `has_files` itself broke. FIX: every observation in a "
            "rehearsal report is derived from this one string, so a misclassification here does not "
            "merely mislabel a state, it silently changes which findings `derive_observations` "
            "emits.\n" + "\n".join(wrong),
        )

    #: (case, plan(root) -> None, expected `has_files`, why this row exists)
    HAS_FILES = (
        (
            "a directory tree containing no file at any depth",
            lambda root: (root / "deep" / "nested").mkdir(parents=True),
            False,
            "the primitive the layout classifier rests on. Empty nested directories must NOT count "
            "as live framework material, which is what makes litter distinguishable from a real tree",
        ),
        (
            "the same tree with one file at the bottom",
            lambda root: (
                (root / "deep" / "nested").mkdir(parents=True),
                (root / "deep" / "nested" / "f.txt").write_text("x", encoding="utf-8"),
            ),
            True,
            "one file ANY DEPTH DOWN is enough, so the walk must be recursive. A top-level-only "
            "check would report a populated `.agents/workflows/assess/` tree as empty and classify "
            "a genuine split-brain repo as migrated",
        ),
        (
            "a path that does not exist",
            lambda root: None,
            False,
            "a missing directory answers False rather than raising, because the classifier calls "
            "this on both candidate trees and one is normally absent",
        ),
    )

    def test_has_files_distinguishes_empty_from_populated(self) -> None:
        wrong = []
        for index, (case, plan, expected, why) in enumerate(self.HAS_FILES):
            root = self.tmp / f"hf{index}"
            plan(root)
            got = uat.has_files(root)
            if got is not expected:
                wrong.append(
                    f"  {case}: expected {expected}, got {got}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"uat.has_files was wrong for {len(wrong)} of {len(self.HAS_FILES)} trees. It is ONE "
            "recursive walk that returns on the first non-empty `filenames` list, so if the two "
            "populated/empty rows both fail the walk is inverted, while only the deep row failing "
            "means the walk stopped being recursive. FIX: this predicate is what `detect_layout` "
            "uses to tell migration litter from a live tree, so a wrong answer here propagates "
            "into the layout string and from there into every derived observation.\n"
            + "\n".join(wrong),
        )

    def test_legacy_breakdown_attributes_leftovers_to_subtrees(self) -> None:
        """Kept separate: asserts a MAPPING built by attributing each file to a subtree.

        Every row in the tables above asserts one scalar about one tree. This builds a repo with
        files at two different DEPTHS and asserts how each is keyed (a nested file under its
        top-level subtree, a top-level file under `(root)`), which is a claim about the keying rule
        rather than about a state.
        """

        repo = make_source_repo(self.tmp / "r", "1.2.1", "aw")
        skills = repo / ".agents" / "skills" / "assess-ui-ux"
        skills.mkdir(parents=True)
        (skills / "SKILL.md").write_text("x", encoding="utf-8")
        (repo / ".agents" / "README.md").write_text("x", encoding="utf-8")
        breakdown = uat.legacy_breakdown(repo)
        self.assertEqual(breakdown.get("skills"), 1)
        self.assertEqual(breakdown.get("(root)"), 1)

    #: (case, the layout to build or None for a bare git repo, the expected summary dict, why this
    #: row exists)
    MANIFEST_SUMMARIES = (
        (
            "a canonical-layout repo carrying a manifest",
            "aw",
            {
                "path": ".aw/system/managed-sections.json",
                "schema_version": 2,
                "installed_version": "1.2.1",
                "installer": None,
                "rows": 0,
            },
            "THE WHOLE DICT is pinned, not just one key, because the report prints the row count "
            "BESIDE the file count to surface a known upgrade defect (manifest.py has no row-"
            "deletion API; measured at 135 rows against 90 files). A summary that dropped `rows` "
            "would silently remove that signal while every single-key assertion stayed green",
        ),
        (
            "a legacy-layout repo with no manifest file",
            "legacy",
            {"path": None},
            "ABSENCE IS `{'path': None}`, NOT AN ERROR AND NOT AN EMPTY DICT. A pre-migration repo "
            "legitimately has no manifest, and the shape must stay a dict with a `path` key so the "
            "reporting layer can render it without branching on type",
        ),
        (
            "a bare git repo",
            None,
            {"path": None},
            "the same answer for a repo with no framework at all, which is what makes the absent "
            "case a property of the manifest rather than of the layout",
        ),
    )

    def test_the_manifest_summary_reports_its_whole_shape_or_a_clean_absence(
        self,
    ) -> None:
        wrong = []
        for index, (case, layout, expected, why) in enumerate(self.MANIFEST_SUMMARIES):
            repo = self.tmp / f"m{index}"
            if layout is None:
                init_repo(repo)
            else:
                make_source_repo(repo, "1.2.1", layout)
            got = uat.manifest_summary(repo)
            if got != expected:
                wrong.append(
                    f"  {case}: expected {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"uat.manifest_summary returned the wrong shape for {len(wrong)} of "
            f"{len(self.MANIFEST_SUMMARIES)} repos. One function with one early return per "
            "candidate path decides all three, so if BOTH absent rows fail the fallback return "
            "changed shape and the reporting layer will raise on a repo with no manifest, while the "
            "populated row failing alone means a key was renamed or dropped. FIX: `rows` existing "
            "is load-bearing, because the row-count-versus-disk drift it exposes is a KNOWN "
            "unfixed defect and this summary is the only place a rehearsal surfaces it.\n"
            + "\n".join(wrong),
        )

    def test_snapshot_tree_excludes_git_and_harness_scaffolding(self) -> None:
        """Kept separate: asserts over a LISTING, with three exclusions and one inclusion at once.

        Rows elsewhere in this class assert one value about one tree. This asserts the SHAPE of a file
        list: that `.git`, the marker, and the harness's own scratch directory are all absent while
        real content is present. Splitting it into rows would make each exclusion a separate tree
        build for no gain, since one snapshot call already exercises all of them, and the property
        that matters (`before` and `after` snapshots differ only by installer changes) depends on the
        exclusions holding TOGETHER.
        """

        repo = make_source_repo(self.tmp / "r", layout="aw")
        (repo / uat.MARKER_NAME).write_text("{}", encoding="utf-8")
        (repo / ".aw-upgrade-test").mkdir()
        (repo / ".aw-upgrade-test" / "junk").write_text("x", encoding="utf-8")
        files = uat.snapshot_tree(repo)
        self.assertIn("README.md", files)
        self.assertFalse([f for f in files if f.startswith(".git")])
        self.assertNotIn(uat.MARKER_NAME, files)
        self.assertFalse([f for f in files if f.startswith(".aw-upgrade-test")])


class SafetyInvariantOneSourceUntouched(TempCase):
    """Invariant 1: the source repo is never mutated, and copies are never hardlinked.

    ONE TABLE replaces two tests, AND THE STRATEGY IS THE COLUMN THAT MATTERS MOST IN THIS FILE.
    Both old tests called `copy_full` only, so invariant 1 was asserted for ONE of the two copy
    strategies the tool offers and a hardlinking `clone` path would have shipped green. `copy_clone`
    runs `git clone --local`, whose DEFAULT is to hardlink the object store, so the safe behavior
    there depends on a `--no-hardlinks` flag that a well-meant "make the clone cheaper" edit would
    remove; nothing was watching that flag. Running both strategies through the same rows is the
    whole reason this is a table.

    THE CHECK MODE IS ALSO A COLUMN, because the two old tests made DIFFERENT KINDS of claim about
    the same act: one compared the source tree byte-for-byte (and by mtime) before and after, the
    other asserted distinct inodes and then WROTE THROUGH the copy. Neither implies the other. A
    copy could leave the source bytes intact while sharing inodes (the hazard fires later, on the
    first sandbox write), and distinct inodes on one probed file say nothing about the other files.
    So every row runs all three probes and reports each independently.
    """

    #: (case, the copy strategy, whether `create_sandbox` is used rather than the raw copy helper,
    #: why this row exists)
    COPY_STRATEGIES = (
        (
            "the full copy (`cp -a`, the default)",
            "full",
            False,
            "THE DELIBERATE ABSENCE OF `-l` IS THE WHOLE SAFETY PROPERTY. `cp -al` would be faster "
            "and would let an in-place truncation inside the sandbox empty the SOURCE's file, which "
            "is the one way this harness could destroy real work",
        ),
        (
            "the clone copy (`git clone --local --no-hardlinks`)",
            "clone",
            True,
            "THE ROW THE OLD TESTS DID NOT HAVE, and the reason this is a table: invariant 1 must "
            "hold for BOTH strategies, and both old tests exercised only `copy_full`. The clone path "
            "shares NO implementation with it (a git clone, then an explicit `copytree`/`copy2` of "
            "the framework paths), so nothing here was covered by inference. What it can share with "
            "the source is MEASURED rather than assumed: see the object-store probe in the loop",
        ),
    )

    def test_neither_copy_strategy_can_write_back_to_the_source(self) -> None:
        """WHAT EACH PROBE BELOW CAN AND CANNOT SEE, recorded because getting it wrong is easy.

        A WRONG EXPECTATION WAS FOUND HERE BY MUTATION. The first version of this table probed only
        `.agents/workflows/VERSION` and claimed the clone row was what watched `--no-hardlinks`.
        Deleting that flag left the table GREEN, because a clone's WORKING-TREE files cannot be
        hardlinked to the source's however it is invoked: git writes them as a fresh checkout, and the
        framework paths arrive afterwards through `copytree`/`copy2`. Measured with the flag removed:
        8 of 8 loose OBJECT files became hardlinked while every working-tree file stayed distinct. So
        the working-tree probe is a real check for `cp -a` and a vacuous one for the clone, and the
        object store needs its own probe.

        HONEST SCOPE OF THE OBJECT-STORE CHECK. A shared object file is NOT the same hazard as a
        shared working-tree file, and `copy_clone`'s own docstring says as much: git treats objects as
        immutable and never rewrites one in place, so hardlinked objects are safe by design. That
        assertion therefore pins a DELIBERATE belt-and-braces choice rather than the barrier invariant
        1 rests on, and its failure message says so instead of crying data loss. It is kept because
        the choice is cheap, real, and otherwise entirely unwatched.
        """

        wrong = []
        for case, strategy, via_sandbox, why in self.COPY_STRATEGIES:
            source = make_source_repo(self.tmp / f"src-{strategy}", "1.2.1", "legacy")

            def snapshot() -> dict:
                return {
                    p.relative_to(source).as_posix(): (
                        p.stat().st_mtime_ns,
                        p.read_bytes(),
                    )
                    for p in sorted(source.rglob("*"))
                    if p.is_file() and ".git" not in p.parts
                }

            before = snapshot()
            if via_sandbox:
                sandbox = uat.create_sandbox(
                    uat.SourceRepo.inspect(source),
                    self.tmp / f"boxes-{strategy}",
                    strategy=strategy,
                )
            else:
                sandbox = self.tmp / f"dst-{strategy}"
                uat.copy_full(source, sandbox)

            problems = []
            after = snapshot()
            if after != before:
                changed = sorted(
                    set(before) ^ set(after)
                    | {k for k in set(before) & set(after) if before[k] != after[k]}
                )
                problems.append(
                    f"the SOURCE tree changed after the copy; differing paths: {changed}"
                )

            # THE OBJECT STORE, probed separately because it is the ONLY thing `git clone --local`
            # shares by default, and because a working-tree probe cannot see it. Measured: dropping
            # `--no-hardlinks` hardlinks 8 of 8 object files while every working-tree file stays
            # distinct, so without this check that edit is invisible.
            def object_inodes(root: Path) -> dict:
                objects = root / ".git" / "objects"
                return {
                    path.relative_to(objects).as_posix(): path.stat().st_ino
                    for path in sorted(objects.rglob("*"))
                    if path.is_file()
                }

            src_objects = object_inodes(source)
            dst_objects = object_inodes(sandbox)
            shared = sorted(
                name
                for name, ino in src_objects.items()
                if dst_objects.get(name) == ino
            )
            if not src_objects:
                problems.append(
                    "the source has no loose git objects at all, so the object-store probe below is "
                    "vacuous and this row cannot detect a hardlinking clone"
                )
            elif shared:
                problems.append(
                    f"{len(shared)} of {len(src_objects)} git OBJECT files are hardlinked to the "
                    f"source's (e.g. {shared[0]}). Git never rewrites an object in place, so this is "
                    "not immediately destructive, but it is the belt to the working-tree braces and "
                    "`git clone --local` shares them BY DEFAULT: the only thing preventing it is "
                    "`--no-hardlinks`"
                )

            src_file = source / ".agents" / "workflows" / "VERSION"
            dst_file = sandbox / ".agents" / "workflows" / "VERSION"
            if not dst_file.is_file():
                problems.append(
                    f"the copy did not reproduce {dst_file.name} at all, so neither the inode nor "
                    "the write-through probe below can run and this row proves nothing"
                )
            else:
                if src_file.stat().st_ino == dst_file.stat().st_ino:
                    problems.append(
                        "source and copy share an INODE, so the content is hardlinked: an in-place "
                        "truncation inside the sandbox would empty the source's file"
                    )
                # WRITE THROUGH, because distinct inodes alone are an inference. This is the actual
                # hazard being performed: if it reaches the source, the harness can destroy real work.
                with open(dst_file, "w", encoding="utf-8") as handle:
                    handle.write("CLOBBERED\n")
                surviving = src_file.read_text(encoding="utf-8").strip()
                if surviving != "1.2.1":
                    problems.append(
                        f"writing to the COPY changed the SOURCE: it now reads {surviving!r} "
                        "instead of '1.2.1'"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"invariant 1 (the source is never mutated) failed for {len(wrong)} of "
            f"{len(self.COPY_STRATEGIES)} copy strategies. The two strategies share no "
            "implementation, so BOTH rows failing together points at something common downstream "
            "(`create_sandbox`, or the framework-state copy both paths perform) rather than at "
            "either copy. A SINGLE row failing is the likelier and more dangerous case: it means "
            "one strategy is safe and the other is not, which is invisible to any test that "
            "exercises only the default. FIX: an inode-sharing failure is the urgent one, because "
            "it means this harness can destroy the real repository it was pointed at. Look for a "
            "`-l` added to `cp -a`, or `--no-hardlinks` dropped from `git clone --local`.\n"
            + "\n".join(wrong),
        )

    def test_no_hardlink_strategy_is_offered(self) -> None:
        """A cheap-but-unsafe strategy must not be reachable, even opt-in."""

        parser = uat.build_parser()
        args = parser.parse_args(["new", "x", "--strategy", "clone"])
        self.assertEqual(args.strategy, "clone")
        with self.assertRaises(SystemExit):
            parser.parse_args(["new", "x", "--strategy", "hardlink"])
        with self.assertRaises(uat.HarnessError):
            uat.create_sandbox(
                uat.SourceRepo.inspect(make_source_repo(self.tmp / "s")),
                self.tmp / "boxes",
                strategy="hardlink",
            )


class SafetyInvariantTwoNeverPush(TempCase):
    """Invariant 2: a sandbox cannot reach the source's real upstream."""

    def _sandbox_with_remote(self) -> Path:
        source = make_source_repo(self.tmp / "src", "1.2.1", "legacy")
        git(
            source, "remote", "add", "origin", "git@example.invalid:someone/private.git"
        )
        git(source, "remote", "add", "backup", "https://example.invalid/backup.git")
        sandbox = self.tmp / "box"
        uat.copy_full(source, sandbox)
        return sandbox

    def test_the_unneutralized_copy_DOES_inherit_the_real_remotes(self) -> None:
        """Kept separate: this is the CONTROL, and it asserts the hazard EXISTS.

        Every row in the table below asserts that neutralizing removed something. If a copy never
        carried a remote in the first place, all of them would pass while proving nothing, exactly as
        a leak scan with no control proves nothing. So this runs BEFORE neutralizing and states the
        opposite claim, which is why it cannot be a row in a table whose subject is post-neutralize
        state.
        """

        sandbox = self._sandbox_with_remote()
        remotes = uat.git_out(sandbox, "remote").split()
        self.assertIn("origin", remotes)
        self.assertIn("backup", remotes)

    #: (case, extra remotes to add beyond `origin`, whether the sandbox is built by `create_sandbox`
    #: (so neutralizing is the TOOL's job) rather than by a bare copy plus an explicit
    #: `neutralize_git` call, the remotes `neutralize_git` must report removing or None when the
    #: route does not return a result, why this row exists)
    NEUTRALIZE_ROUTES = (
        (
            "an explicit neutralize_git on a copied repo with two remotes",
            ("backup",),
            False,
            ["backup", "origin"],
            "EVERY remote goes, not just `origin`. A loop that handled only the conventional name "
            "would leave a `backup` remote (measured: real repos carry them) reachable, and the "
            "returned list is what the marker records as evidence, so it is asserted rather than "
            "inferred from the surviving set",
        ),
        (
            "create_sandbox, which must neutralize BEFORE it returns",
            (),
            True,
            None,
            "THE ROUTE CALLERS ACTUALLY USE, and the reason this is a column rather than a second "
            "test: `rehearse` never calls `neutralize_git` itself, so if `create_sandbox` stopped "
            "calling it every direct-call assertion would stay green while every real sandbox shipped "
            "with a live upstream. The window matters too: a sandbox that is neutralized LATER is "
            "pushable in between",
        ),
    )

    def test_every_route_to_a_sandbox_leaves_it_unable_to_reach_a_real_upstream(
        self,
    ) -> None:
        wrong = []
        for index, (case, extra, via_create, removed, why) in enumerate(
            self.NEUTRALIZE_ROUTES
        ):
            source = make_source_repo(self.tmp / f"src{index}", "1.2.1", "legacy")
            git(
                source,
                "remote",
                "add",
                "origin",
                "git@example.invalid:someone/private.git",
            )
            for name in extra:
                git(source, "remote", "add", name, "https://example.invalid/x.git")

            problems = []
            if via_create:
                sandbox = uat.create_sandbox(
                    uat.SourceRepo.inspect(source),
                    self.tmp / f"boxes{index}",
                    strategy="full",
                )
            else:
                sandbox = self.tmp / f"box{index}"
                uat.copy_full(source, sandbox)
                result = uat.neutralize_git(sandbox)
                if removed is not None and sorted(result["remotes_removed"]) != removed:
                    problems.append(
                        f"neutralize_git reported removing {sorted(result['remotes_removed'])!r}, "
                        f"expected {removed!r}; that list is the marker's evidence of what it did"
                    )

            # 1. REMOVAL. No real remote survives.
            surviving = [
                r
                for r in uat.git_out(sandbox, "remote").split()
                if r != "aw-upgrade-test-blackhole"
            ]
            if surviving:
                problems.append(
                    f"real remotes survive in the sandbox: {surviving!r}, so a push could reach the "
                    "operator's actual upstream"
                )
            # 2. THE BLACKHOLE, which is what makes a RE-ADDED remote still harmless. Removal alone
            # is a single point of failure: the installer, a hook, or a human may add one back.
            push_default = uat.git_out(
                sandbox, "config", "--local", "remote.pushDefault"
            )
            if push_default != "aw-upgrade-test-blackhole":
                problems.append(
                    f"remote.pushDefault is {push_default!r}, not the blackhole, so a re-added "
                    "remote would become the push target again"
                )
            url = uat.git_out(
                sandbox, "config", "--local", "remote.aw-upgrade-test-blackhole.pushurl"
            )
            if url != uat.BLACKHOLE_PUSH_URL:
                problems.append(
                    f"the blackhole pushurl is {url!r}, not {uat.BLACKHOLE_PUSH_URL!r}"
                )
            # 3. IDENTITY. A sandbox commit must not be attributable to the operator, in the repo
            # config AND in the environment the installer is actually run under.
            email = uat.git_out(sandbox, "config", "--local", "user.email")
            if email != "aw-upgrade-test@invalid.localhost":
                problems.append(
                    f"local user.email is {email!r}, so a sandbox commit would be attributed to the "
                    "operator"
                )
            env = uat.sandbox_env(sandbox)
            for key in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
                if env.get(key) != "aw-upgrade-test":
                    problems.append(
                        f"sandbox_env[{key!r}] is {env.get(key)!r}, so the environment would "
                        "override the local config and re-attribute the commit"
                    )
            # 4. AN ACTUAL PUSH, because every check above is an inference from configuration.
            proc = subprocess.run(
                ["git", "push", "origin", "HEAD"],
                cwd=str(sandbox),
                capture_output=True,
                text=True,
                check=False,
                env=dict(os.environ, GIT_TERMINAL_PROMPT="0"),
            )
            if proc.returncode == 0:
                problems.append(
                    "`git push origin HEAD` SUCCEEDED from inside the sandbox, which is invariant 2 "
                    f"broken outright: {proc.stdout.strip()!r} {proc.stderr.strip()!r}"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"invariant 2 (a sandbox cannot reach the real upstream) failed on {len(wrong)} of "
            f"{len(self.NEUTRALIZE_ROUTES)} routes. `neutralize_git` applies three independent "
            "barriers plus an identity rewrite, so the pattern names the cause: ALL rows failing the "
            "same barrier means that barrier was removed from `neutralize_git`, while only the "
            "`create_sandbox` row failing means the function is intact and its CALLER stopped "
            "invoking it, which is worse in practice because every sandbox real callers build would "
            "be live while direct-call tests stayed green. FIX: treat a SUCCEEDING push as the "
            "emergency; the config checks are early warnings, that one is the harm. Note the "
            "separate control test above, which proves an unneutralized copy really does inherit "
            "remotes, without which every row here could pass vacuously.\n"
            + "\n".join(wrong),
        )


class SafetyInvariantThreeNoInventoryPollution(TempCase):
    """Invariant 3: the operator's real config and repo inventory are never written."""

    def test_sandbox_env_redirects_config_and_home_into_the_sandbox(self) -> None:
        """Kept separate: the cheap half of a pair whose expensive half runs a real subprocess.

        This asserts the env vars are SET; the test below asserts `aw` HONORS them. Merging the two
        would run a subprocess to re-check a dict lookup, and keeping them adjacent is what documents
        that the first alone would not be evidence.
        """

        sandbox = self.tmp / "box"
        sandbox.mkdir()
        env = uat.sandbox_env(sandbox)
        self.assertTrue(env["XDG_CONFIG_HOME"].startswith(str(sandbox)))
        self.assertTrue(env["AW_HOME"].startswith(str(sandbox)))

    def test_redirected_config_path_resolves_inside_the_sandbox(self) -> None:
        """Proves the redirect actually moves the file the installer WRITES.

        Asserting the env var alone would not show that ``aw`` honors it, so this runs the
        real resolver in a subprocess under the sandbox environment.
        """

        sandbox = self.tmp / "box"
        sandbox.mkdir()
        env = uat.sandbox_env(sandbox)
        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                "from agent_workflows import config; print(config.config_path())",
            ],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(
            proc.stdout.strip().startswith(str(sandbox)),
            f"config path {proc.stdout.strip()!r} escaped the sandbox",
        )

    #: (case, plan(self, root) -> Path returning the directory that must NOT be offered as a
    #: rehearsal source, whether `discovery.discover` must ALSO not see it, why this row exists)
    #:
    #: ONE TABLE replaces two tests plus part of a third. All of them built a search root holding a
    #: real repo alongside something that merely LOOKS like one, called `discover_sources`, and
    #: asserted the real repo is offered while the impostor is not. The KIND of impostor is the data.
    #:
    #: THE SECOND COLUMN IS A DIFFERENT KIND OF CLAIM about one of the rows, kept as a column rather
    #: than weakened away: for the default sandbox root it is not enough that OUR OWN discovery skips
    #: it, because the hazard invariant 3 names is that `aw install all` sweeps the sandbox up as a
    #: managed repo. That requires the FRAMEWORK's `discovery.discover` not to see it either, which is
    #: a claim about a different module and holds for a different reason (the default root nests under
    #: a `tmp/` subdirectory the non-recursive immediate-children scan cannot reach).
    NON_SOURCES = (
        (
            "a sandbox at the DEFAULT nested root, beside a real repo",
            lambda self, root: uat.create_sandbox(
                uat.SourceRepo.inspect(make_source_repo(self.tmp / "src-nested")),
                (root / "tmp" / "aw-upgrade-tests"),
            ),
            True,
            "INVARIANT 3's ACTUAL HAZARD: a sandbox the framework's own discovery can see would be "
            "swept into a later `aw install all` and upgraded as if it were a managed repo. The "
            "default root therefore nests one level deeper than the non-recursive scan reaches, and "
            "this row asserts BOTH scanners miss it",
        ),
        (
            "a sandbox sitting DIRECTLY under the search root",
            lambda self, root: uat.create_sandbox(
                uat.SourceRepo.inspect(make_source_repo(self.tmp / "src-direct")), root
            ),
            # Deliberately NOT asserted: placed directly under a scanned root (via an explicit
            # --dest, which the default avoids) the framework's discovery DOES see it. Probed and
            # confirmed. That is precisely why the default root nests, and asserting the opposite
            # here would pin a guarantee the tool does not make.
            False,
            "A REHEARSAL MUST NEVER RUN ON A REHEARSAL, and this row covers the case the nesting "
            "does not: an operator who passes `--dest` can put a sandbox anywhere, so "
            "`discover_sources` needs its OWN exclusion (the name infix and the marker file) rather "
            "than relying on where the default put things",
        ),
    )

    def test_no_sandbox_is_ever_offered_as_a_rehearsal_source(self) -> None:
        from agent_workflows import discovery

        wrong = []
        for index, (case, plan, framework_blind, why) in enumerate(self.NON_SOURCES):
            root = self.tmp / f"VC{index}"
            root.mkdir(parents=True, exist_ok=True)
            make_source_repo(root / "realrepo")
            impostor = plan(self, root)

            problems = []
            names = [s.path.name for s in uat.discover_sources([root])]
            if impostor.name in names:
                problems.append(
                    f"discover_sources offered {impostor.name!r} as a rehearsal source, so a "
                    "rehearsal could be run against a previous rehearsal"
                )
            # THE POSITIVE HALF, in the same table: an exclusion that dropped EVERYTHING would
            # satisfy the check above while making the tool unable to find any repo at all.
            if "realrepo" not in names:
                problems.append(
                    "the real repo beside it was ALSO dropped, so the exclusion is over-broad and "
                    f"the tool can offer nothing; discover_sources returned {names!r}"
                )
            if framework_blind:
                found = discovery.discover([root], recursive=False)
                if impostor.resolve() in [t.resolve() for t in found.targets]:
                    problems.append(
                        "the FRAMEWORK's discovery sees this sandbox, so `aw install all` would "
                        "upgrade it as though it were one of the operator's managed repos"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.NON_SOURCES)} sandbox placements were treated as rehearsal "
            "sources. `discover_sources` excludes on two independent signals (the name infix and the "
            "marker file), so BOTH rows failing means both signals went, while one row failing means "
            "a placement slipped past one of them. FIX: if the `realrepo` half is what failed, the "
            "exclusion is over-broad and the symptom a human sees is the opposite one, an empty "
            "candidate list rather than a dangerous entry. Note the second column is asserted for "
            "the DEFAULT root only: a sandbox placed directly under a scanned root via --dest IS "
            "visible to the framework's discovery (probed), which is the whole reason the default "
            "nests under a `tmp/` subdirectory.\n" + "\n".join(wrong),
        )

    def test_discover_sources_skips_a_git_worktree(self) -> None:
        """A worktree shares its parent's object store, so it is not a valid source.

        Regression: the harness listed its OWN worktree as a rehearsal candidate.

        Kept separate from the sandbox-exclusion table above: this needs `git worktree add` to have
        WORKED, and it self-skips when it did not. As a row, that skip would silence the sandbox rows
        beside it on any machine where worktrees are unavailable, which is the one thing a shared
        skipUnless-style guard must never do.
        """

        root = self.tmp / "VC"
        root.mkdir()
        parent = make_source_repo(root / "parent", "1.2.1", "aw")
        wt = root / "wtree"
        subprocess.run(
            ["git", "worktree", "add", "-q", "-b", "lane", str(wt)],
            cwd=str(parent),
            capture_output=True,
            text=True,
            check=False,
        )
        if not wt.exists():
            self.skipTest("git worktree unavailable")
        self.assertTrue(uat.is_worktree(wt))
        names = [s.path.name for s in uat.discover_sources([root])]
        self.assertIn("parent", names)
        self.assertNotIn("wtree", names)

    def test_default_sandbox_root_is_computed_not_hardcoded(self) -> None:
        """A literal default path would bake one machine's layout into a tracked file.

        It is also what the leak-sanitizer rejects (rule ``vc-home``), so the default is
        derived from the configured search root and overridable by environment.
        """

        source = (REPO_ROOT / "agent_workflows" / "upgrade_rehearsal.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("DEFAULT_SANDBOX_ROOT = Path(", source)
        computed = uat.default_sandbox_root()
        self.assertEqual(computed.name, uat.SANDBOX_ROOT_NAME)
        self.assertEqual(computed.parent.name, "tmp")

    def test_sandbox_root_env_override_is_honored(self) -> None:
        """Kept separate: mutates and restores a process-wide environment variable.

        Materially different setup from every row and test around it. Folding it into a table would
        put a global mutation inside a loop, where a row failing mid-iteration could leave
        `AW_UPGRADE_TEST_ROOT` set for every test that runs after it under pytest-randomly's ordering.
        """

        prior = os.environ.get("AW_UPGRADE_TEST_ROOT")
        os.environ["AW_UPGRADE_TEST_ROOT"] = str(self.tmp / "custom")
        try:
            self.assertEqual(uat.default_sandbox_root(), self.tmp / "custom")
        finally:
            if prior is None:
                del os.environ["AW_UPGRADE_TEST_ROOT"]
            else:
                os.environ["AW_UPGRADE_TEST_ROOT"] = prior

    def test_relative_search_root_is_not_treated_as_a_source(self) -> None:
        """A "." search root resolves to the CHECKOUT, which must never be a source."""

        roots = uat.search_roots()
        self.assertNotIn(Path.cwd().resolve(), roots)


class SafetyInvariantFourMarkerGatedDeletion(TempCase):
    """Invariant 4: ``clean`` can only ever delete our own sandboxes.

    ONE TABLE replaces four tests, and `force` IS A COLUMN rather than a fourth test, because the
    contract is that the flag changes NOTHING. Stating that requires the same input twice with the
    flag flipped; a single-value test can only ever say what happened once. The three `action` values
    are a closed set and `clean` is the only destructive verb in this tool, so the rows are also
    where a reader sees the whole set at a glance.

    EVERY ROW RE-CHECKS THE FILESYSTEM, not just the returned action. A refusal that has already
    deleted the tree is not a refusal, and the action string is the one part of the outcome that can
    be right while the behavior is catastrophically wrong.
    """

    #: (case, plan() -> Path building the subject, `force`, the expected action, whether the
    #: directory must SURVIVE, why this row exists)
    CLEAN_CASES = (
        (
            "a real repository with no marker",
            lambda self: make_source_repo(self.tmp / "precious", "1.2.1", "legacy"),
            False,
            "refuse",
            True,
            "THE INVARIANT. A mistyped or stale path must be REFUSED rather than deleted, because "
            "this is the only verb in the tool that can destroy a human's real work",
        ),
        (
            "the same unmarked repository, with force=True",
            lambda self: make_source_repo(self.tmp / "precious-f", "1.2.1", "legacy"),
            True,
            "refuse",
            True,
            "FORCE IS NOT AN OVERRIDE, and this row is why `force` is a column: the flag exists only "
            "for CLI symmetry and `clean` discards it (`del force`). Paired with the row above, "
            "identical but for the flag, the two together state that the gate is unbypassable, which "
            "neither could say alone. A future 'but the operator asked for it' escape hatch fails "
            "here",
        ),
        (
            "a genuine sandbox carrying our marker",
            lambda self: uat.create_sandbox(
                uat.SourceRepo.inspect(make_source_repo(self.tmp / "src")),
                self.tmp / "boxes",
            ),
            False,
            "removed",
            False,
            "THE POSITIVE ROW, and it is load-bearing: a `clean` that refused EVERYTHING would "
            "satisfy both refusal rows on its own while making the verb useless, so sandboxes would "
            "accumulate until someone deleted one by hand, which is the dangerous act this gate "
            "exists to replace",
        ),
        (
            "a path that does not exist",
            lambda self: self.tmp / "nope",
            False,
            "skip",
            False,
            "A MISSING PATH IS `skip`, DISTINCT FROM `refuse`. The distinction is what lets a human "
            "tell 'already gone' from 'I pointed at the wrong thing', and collapsing them would make "
            "a dangerous typo read as a harmless no-op",
        ),
    )

    def test_clean_acts_only_on_its_own_marked_sandboxes(self) -> None:
        wrong = []
        for case, plan, force, expected, survives, why in self.CLEAN_CASES:
            subject = plan(self)
            existed = subject.is_dir()
            results = uat.clean([subject], force=force)
            problems = []
            if not results:
                problems.append("clean returned no result at all for this path")
            else:
                action = results[0].get("action")
                if action != expected:
                    problems.append(f"action expected {expected!r}, got {action!r}")
            # THE FILESYSTEM IS THE REAL ASSERTION: a refusal that already deleted the tree would
            # satisfy the action check above and still have destroyed the repository.
            if survives:
                if not subject.is_dir():
                    problems.append(
                        "THE DIRECTORY IS GONE despite the refusal, so invariant 4 is broken "
                        "outright and the action string was merely cosmetic"
                    )
                elif not (subject / "README.md").is_file():
                    problems.append(
                        "the directory survives but its contents were removed, so the refusal only "
                        "spared the top-level directory entry"
                    )
            elif existed and subject.exists():
                problems.append(
                    "the sandbox still exists after a 'removed' action, so nothing was cleaned and "
                    "sandboxes will accumulate silently"
                )
            if problems:
                wrong.append(
                    f"  {case} (force={force}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"clean behaved wrongly on {len(wrong)} of {len(self.CLEAN_CASES)} paths. One marker "
            "check decides all four, so read the grouping: if BOTH refusal rows fail together the "
            "gate is gone and this verb can now delete any directory it is pointed at, which is the "
            "one outcome this whole class exists to prevent. If only the force row fails, someone "
            "added an override and `force` is no longer inert. If only the positive row fails, the "
            "gate is over-tight and humans will start deleting sandboxes by hand instead. FIX: a "
            "wrong `action` STRING is a reporting bug; a missing directory on a refusal row is data "
            "loss, so triage the filesystem failures first.\n" + "\n".join(wrong),
        )

    def test_probe_refuses_a_non_sandbox(self) -> None:
        """Kept separate: an assertRaises refusal, and it goes through the CLI command rather than `probe`."""

        repo = make_source_repo(self.tmp / "real", "1.2.1", "legacy")
        parser = uat.build_parser()
        args = parser.parse_args(["probe", str(repo)])
        with self.assertRaises(uat.HarnessError):
            uat.cmd_probe(args)


class SandboxCreationTests(TempCase):
    """What each copy STRATEGY reproduces, and what the marker records about it.

    ONE TABLE replaces three tests. Each built a source repo carrying gitignored and untracked
    material, created a sandbox with one strategy, and asserted which files arrived; the third
    additionally read the marker back. The STRATEGY is therefore a column, and the table is where the
    two strategies' fidelity contracts become comparable instead of living in separate tests that
    never state how they differ.

    THE DIFFERENCE IS THE POINT, AND IT IS ASSERTED IN BOTH DIRECTIONS. `full` reproduces everything,
    including arbitrary untracked scratch files and arbitrary gitignored trees. `clone` reproduces
    committed state plus an ENUMERATED set of framework paths (`.aw`, `.agents`, `AGENTS.md`,
    `.opencode`, `.claude`, `.gitignore`) and NOTHING ELSE, so gitignored `.aw/state/` arrives while
    an unrelated gitignored tree does not. That asymmetry is a deliberate cost/fidelity tradeoff, and
    the rows below pin it as a POSITIVE and a NEGATIVE expectation per path rather than asserting only
    what should be present: a `clone` that silently became a full copy would satisfy every
    presence-only assertion while making the cheap strategy no longer cheap, and a `full` that
    silently became a clone would drop exactly the untracked state an upgrade reads.
    """

    #: (case, the strategy, {relative path: must it exist}, why this row exists)
    STRATEGY_FIDELITY = (
        (
            "the full copy",
            "full",
            {
                ".aw/system/VERSION": True,
                ".aw/state/live.json": True,
                "ignored/state.json": True,
                "untracked.txt": True,
                ".gitignore": True,
                "README.md": True,
            },
            "FIDELITY IS THE WHOLE POINT OF THIS STRATEGY: an upgrade READS untracked and gitignored "
            "material (state, backups, manifests), so a rehearsal that lost it would rehearse an "
            "upgrade of a repository that does not exist",
        ),
        (
            "the clone copy",
            "clone",
            {
                ".aw/system/VERSION": True,
                # Gitignored, yet present: the clone path copies the framework trees explicitly
                # AFTERWARDS, precisely because a clone reproduces only COMMITTED state.
                ".aw/state/live.json": True,
                # Gitignored and NOT a framework path, so it legitimately does not travel. Asserted
                # as an absence so a clone that quietly became a full copy is caught.
                "ignored/state.json": False,
                # Untracked and not a framework path: same reasoning.
                "untracked.txt": False,
                ".gitignore": True,
                "README.md": True,
            },
            "THE CHEAP STRATEGY'S CONTRACT, which is NOT 'everything': committed state plus an "
            "enumerated framework set. Both halves matter, and only a table states them together. "
            "The gitignored `.aw/state/live.json` arriving is what proves the explicit framework copy "
            "still runs; the gitignored `ignored/state.json` NOT arriving is what proves this is "
            "still a clone",
        ),
    )

    def test_each_strategy_reproduces_exactly_what_it_promises(self) -> None:
        wrong = []
        for case, strategy, paths, why in self.STRATEGY_FIDELITY:
            source = make_source_repo(self.tmp / f"src-{strategy}", "1.2.1", "aw")
            (source / ".gitignore").write_text(
                "ignored/\n.aw/state/\n", encoding="utf-8"
            )
            (source / "ignored").mkdir()
            (source / "ignored" / "state.json").write_text("{}", encoding="utf-8")
            (source / "untracked.txt").write_text("scratch\n", encoding="utf-8")
            state = source / ".aw" / "state"
            state.mkdir(parents=True)
            (state / "live.json").write_text("{}", encoding="utf-8")

            sandbox = uat.create_sandbox(
                uat.SourceRepo.inspect(source),
                self.tmp / f"boxes-{strategy}",
                strategy=strategy,
            )
            problems = []
            for rel, expected in paths.items():
                present = (sandbox / rel).is_file()
                if present != expected:
                    problems.append(
                        f"{rel}: expected {'present' if expected else 'ABSENT'}, "
                        f"found {'present' if present else 'absent'}"
                    )
            # THE MARKER IS PART OF CREATION, not a separate subject: it is the only record of what
            # the sandbox was made FROM, and every later comparison (`probe`'s baseline fields, the
            # rehearsal report) reads it. A sandbox with no marker is also unreachable by `clean`.
            marker = uat.read_marker(sandbox)
            if marker is None:
                problems.append(
                    "no marker was written, so this sandbox has no recorded baseline, `probe` can "
                    "report no version change, and `clean` cannot delete it"
                )
            else:
                recorded = (
                    marker.get("strategy"),
                    marker.get("source", {}).get("version"),
                    marker.get("source", {}).get("layout"),
                )
                if recorded != (strategy, "1.2.1", "aw"):
                    problems.append(
                        f"marker (strategy, source version, source layout) is {recorded!r}, "
                        f"expected {(strategy, '1.2.1', 'aw')!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.STRATEGY_FIDELITY)} copy strategies reproduced the wrong "
            "tree. Read the DIRECTION of each failure: an unexpectedly PRESENT file in the clone row "
            "means the clone became a full copy (correct results, silently none of the speed it "
            "exists for), while an unexpectedly ABSENT one in either row means a rehearsal now runs "
            "against a repository the source never was, which invalidates its conclusions rather "
            "than merely slowing it. If both rows lose `.aw/state/live.json`, the explicit framework "
            "copy stopped running. FIX: a missing MARKER is separately urgent, because it orphans "
            "the sandbox: nothing records what it was made from and `clean` will refuse to delete "
            "it.\n" + "\n".join(wrong),
        )

    def test_sandbox_name_carries_repo_and_timestamp(self) -> None:
        """Kept separate: a pure string-formatting claim, with no repository and no filesystem.

        Every row above builds a real tree and inspects the result. This asserts the NAME grammar
        (`<repo>.aw-upgrade-test.<stamp>`) from two strings, and that grammar is what `discover_sources`
        pattern-matches on to avoid offering a sandbox as a rehearsal source, so it is a claim about a
        convention rather than about a copy.
        """

        name = uat.sandbox_name("myrepo", "20260912-151437")
        self.assertEqual(name, "myrepo.aw-upgrade-test.20260912-151437")

    def test_create_sandbox_refuses_to_overwrite_an_existing_sandbox(self) -> None:
        """Kept separate: an assertRaises refusal, and it needs a PRIOR sandbox at the same stamp."""

        source = uat.SourceRepo.inspect(make_source_repo(self.tmp / "src"))
        boxes = self.tmp / "boxes"
        stamp = "20260101-000000"
        uat.create_sandbox(source, boxes, stamp=stamp)
        with self.assertRaises(uat.HarnessError):
            uat.create_sandbox(source, boxes, stamp=stamp)

    def test_find_sandboxes_locates_by_marker_not_by_name(self) -> None:
        """Kept separate: materially different setup, since the sandbox is RENAMED after creation.

        That rename is the whole assertion (discovery keys on the marker file, not the name), and it
        would be a destructive step to interleave with the fidelity rows above, which need the name
        the tool chose.
        """

        boxes = self.tmp / "boxes"
        sandbox = uat.create_sandbox(
            uat.SourceRepo.inspect(make_source_repo(self.tmp / "src")), boxes
        )
        renamed = boxes / "renamed-by-hand"
        sandbox.rename(renamed)
        found = uat.find_sandboxes([boxes])
        self.assertEqual([p.resolve() for p in found], [renamed.resolve()])


class ProbeAndObservationTests(TempCase):
    """What `probe` reports about a sandbox, and what `derive_observations` makes of it.

    ONE TABLE replaces seven observation tests spread over this class and `InspectionTests`. All
    seven had the identical shape: hand a state dict to `derive_observations`, assert one `kind`
    string is in (or not in) the result. The class boundary tracked which safety invariant motivated
    the case, which is not a property of the subject.

    Why the table beats the seven, specifically HERE: the observation kinds are a CLOSED SET a human
    reads to decide whether an upgrade behaved, and the realistic regression is a predicate widening
    so something fires on a state it should not. Seven tests report that as one red line saying
    `'x' unexpectedly found in [...]`; the table reports which rows fired, which is what distinguishes
    "this one predicate widened" from "the migration detection flipped and half the table moved".
    It also makes the set browsable, which matters because two of these predicates (`legacy-leftovers`
    and `legacy-kept`) are deliberate MIRRORS of each other and only make sense read together.

    EVERY ROW ASSERTS THE WHOLE KIND LIST, not a membership. That is stricter than all seven tests it
    replaces, and it is what catches a NEW observation appearing on a state that should be quiet: a
    membership check cannot see an extra finding, and an observation list a reader learns to ignore is
    the exact failure mode `derive_observations`'s own docstring warns about.
    """

    #: (case, the state dict handed to `derive_observations`, the EXACT expected kinds in order, why
    #: this row exists)
    OBSERVATIONS = (
        (
            "a clean canonical-layout run that bumped the version",
            {
                "layout": "aw",
                "baseline_layout": "aw",
                "baseline_version": "1.2.1",
                "installed_version": "1.3.0",
                "legacy_files_remaining": 0,
                "manifest": {"installed_version": "1.3.0"},
                "git": {"git": True, "remotes": []},
            },
            [],
            "THE CLEAN ROW, and it carries real weight because every other row asserts that "
            "something FIRES: a deriver that emitted a finding for every state would satisfy all of "
            "them on its own. This one says a good upgrade produces SILENCE, which is what makes a "
            "non-empty list meaningful to a human",
        ),
        (
            "a genuine split-brain layout",
            {"layout": "dual"},
            ["dual-layout"],
            "the state the installer's own guard refuses. It is reported even with no other "
            "information in the state dict, because a partial probe must not silence a safety finding",
        ),
        (
            "migrated, with empty legacy directories left behind",
            {"layout": "aw+litter", "empty_dirs": 9},
            ["empty-legacy-dirs"],
            "LITTER IS NOT SPLIT-BRAIN, and this row states the discrimination the old test made "
            "with an assertNotIn: `dual-layout` must NOT also fire. Since every row here pins the "
            "WHOLE list, that exclusion is now asserted for free on all of them",
        ),
        (
            "a MIGRATING run that left files under .agents/",
            {
                "baseline_layout": "legacy",
                "layout": "aw",
                "legacy_files_remaining": 5,
            },
            ["legacy-leftovers"],
            "leftovers are a finding only when the run actually moved layout, which is what the "
            "`migrated` predicate computes from the baseline/current pair",
        ),
        (
            "an ALREADY-canonical run with the same leftover count",
            {"baseline_layout": "aw", "layout": "aw", "legacy_files_remaining": 5},
            [],
            "THE NEGATIVE HALF OF THE SAME PREDICATE, with an identical `legacy_files_remaining`, "
            "so the pair proves the deriver keys on the layout TRANSITION and not on the count. The "
            "old file made this point as a before/after pair inside one test; as two rows it also "
            "gets the whole-list check",
        ),
        (
            "a run that deliberately KEPT the legacy layout",
            {
                "baseline_layout": "legacy",
                "layout": "legacy",
                "legacy_files_remaining": 331,
                "legacy_breakdown": {"skills": 92, "workflows": 158},
            },
            ["legacy-kept"],
            "WITHOUT --to-aw THE INSTALLER KEEPS THE LEGACY TREE, so reporting 331 intact files as "
            "leftovers would flag CORRECT behavior as a defect and teach the reader to ignore the "
            "list. Note the 92 skills present here fire nothing, which is the discrimination against "
            "the row below",
        ),
        (
            "a migrating run that left the skills tree behind",
            {
                "baseline_layout": "legacy",
                "layout": "aw+litter",
                "legacy_files_remaining": 92,
                "legacy_breakdown": {"skills": 92},
            },
            ["empty-legacy-dirs", "legacy-leftovers", "orphaned-skills"],
            "THREE FINDINGS FROM ONE STATE, which no single-membership test could state: the same "
            "state is simultaneously littered, holding leftovers, and holding ORPHANED SKILLS a host "
            "may still discover. The ORDER is pinned too, because the report prints them in "
            "sequence and reordering changes what a human reads first",
        ),
        (
            "an unbumped version",
            {"baseline_version": "1.2.1", "installed_version": "1.2.1"},
            ["version-unchanged"],
            "the stamped VERSION comes from the source tree's baked file rather than the running "
            "package, so an unbumped source silently stamps the old number; a rehearsal that did not "
            "say so would read as a successful upgrade",
        ),
        (
            "a manifest still recording the baseline version",
            {"baseline_version": "1.2.1", "manifest": {"installed_version": "1.2.1"}},
            ["manifest-version-unchanged"],
            "a SEPARATE kind from `version-unchanged` on purpose: the VERSION file and the manifest "
            "are written by different code, so the two can disagree and collapsing them would hide "
            "which one stalled. This row has no `installed_version`, so it also proves the manifest "
            "predicate does not depend on the version one",
        ),
        (
            "a sandbox that still has a real remote",
            {"git": {"git": True, "remotes": ["origin"]}},
            ["remote-present"],
            "the SAFETY observation: it is how a neutralize failure becomes visible in a report even "
            "if nothing else caught it",
        ),
        (
            "a sandbox carrying ONLY the blackhole remote",
            {"git": {"git": True, "remotes": ["aw-upgrade-test-blackhole"]}},
            [],
            "the blackhole is OUR remote and must not be reported as a leak, or every correctly "
            "neutralized sandbox would raise a false safety finding and the one real case would be "
            "lost in the noise",
        ),
    )

    def test_every_observation_fires_on_exactly_its_own_state(self) -> None:
        wrong = []
        for case, state, expected, why in self.OBSERVATIONS:
            kinds = [o["kind"] for o in uat.derive_observations(dict(state))]
            if kinds != expected:
                missing = [k for k in expected if k not in kinds]
                extra = [k for k in kinds if k not in expected]
                detail = []
                if missing:
                    detail.append(f"did not fire: {missing!r}")
                if extra:
                    detail.append(f"fired but must not: {extra!r}")
                if not detail:
                    detail.append("the kinds are right but the ORDER changed")
                wrong.append(
                    f"  {case}:\n"
                    f"    - expected {expected!r}, got {kinds!r} ({'; '.join(detail)})\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"derive_observations was wrong for {len(wrong)} of {len(self.OBSERVATIONS)} states. "
            "One function of independent predicates over a shared `migrated` computation decides "
            "every row, so read the grouping: if the leftovers/kept pair BOTH moved, the `migrated` "
            "predicate flipped and the tool is now flagging correct non-migrating behavior as a "
            "defect (or silently excusing a real migration's leftovers). If a single kind appears "
            "everywhere, its guard was dropped. If only the CLEAN row fails, something now fires on "
            "a good upgrade and every other row in this table is vacuous. FIX: this function is "
            "DESCRIPTIVE by design and must never become a pass/fail verdict, so the fix for a "
            "spurious finding is to narrow the predicate, never to delete the observation; a list a "
            "human learns to ignore is the failure its own docstring warns about.\n"
            + "\n".join(wrong),
        )

    #: (case, the source layout to rehearse, the expected (baseline_version, installed_version,
    #: layout) triple, whether `legacy_files_remaining` must be positive, why this row exists)
    PROBES = (
        (
            "a legacy-layout sandbox, freshly created and not installed into",
            "legacy",
            ("1.2.1", "1.2.1", "legacy"),
            True,
            "THE BASELINE-EQUALS-CURRENT CASE. A fresh sandbox has not been upgraded, so the probe "
            "must report the marker's recorded baseline and the on-disk version as the SAME number; "
            "a probe that read one of them from the wrong place would make every rehearsal report a "
            "version change that never happened. The leftover count is positive because a legacy "
            "tree is really there, which is what the migrating rows downstream contrast against",
        ),
        (
            "a canonical-layout sandbox",
            "aw",
            ("1.2.1", "1.2.1", "aw"),
            False,
            "the same triple with a DIFFERENT layout string and ZERO leftovers, which is what proves "
            "`layout` and `legacy_files_remaining` are read from the tree rather than copied from "
            "the marker. Without this row a probe that hardcoded `legacy` would pass",
        ),
    )

    def test_the_probe_reports_the_marker_baseline_beside_the_live_tree(self) -> None:
        wrong = []
        for index, (case, layout, expected, has_leftovers, why) in enumerate(
            self.PROBES
        ):
            source = make_source_repo(self.tmp / f"src{index}", "1.2.1", layout)
            sandbox = uat.create_sandbox(
                uat.SourceRepo.inspect(source), self.tmp / f"boxes{index}"
            )
            state = uat.probe(sandbox)
            got = (
                state["baseline_version"],
                state["installed_version"],
                state["layout"],
            )
            problems = []
            if got != expected:
                problems.append(
                    f"(baseline_version, installed_version, layout) expected {expected!r}, "
                    f"got {got!r}"
                )
            leftovers = state["legacy_files_remaining"]
            if has_leftovers and not leftovers > 0:
                problems.append(
                    f"legacy_files_remaining is {leftovers}, but a legacy tree is present so the "
                    "count must be positive or leftovers are invisible to the report"
                )
            if not has_leftovers and leftovers:
                problems.append(
                    f"legacy_files_remaining is {leftovers} for a repo with no .agents/ tree at all"
                )
            if not state["git"]["git"]:
                problems.append(
                    "the probe reports the sandbox is not a git repo, so every git-derived "
                    "observation (including the remote-present safety finding) is silently skipped"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"uat.probe misreported {len(wrong)} of {len(self.PROBES)} freshly created sandboxes. "
            "The baseline fields come from the MARKER and the rest from the live tree, so the split "
            "tells you where to look: both rows losing `baseline_version` means the marker is not "
            "being read (or `create_sandbox` stopped writing it), while a wrong `layout` or leftover "
            "count is a tree-inspection bug. FIX: a probe whose baseline and current values come "
            "from the same source would report every rehearsal as 'no change' and could never "
            "surface an upgrade at all.\n" + "\n".join(wrong),
        )

    def test_probe_is_idempotent(self) -> None:
        """Kept separate: a BEFORE/AFTER pair whose entire content is that two calls agree.

        No row can state this. The table above asserts what ONE probe reports; this asserts that a
        SECOND probe of the same tree reports the same thing, which is a claim about the function
        having no side effects. Folding it in would mean re-probing every row to check a property
        that is not per-row.
        """

        sandbox = uat.create_sandbox(
            uat.SourceRepo.inspect(make_source_repo(self.tmp / "src")),
            self.tmp / "boxes",
        )
        first = uat.probe(sandbox)
        second = uat.probe(sandbox)
        for key in ("installed_version", "layout", "legacy_files_remaining"):
            self.assertEqual(first[key], second[key])


class CliTests(TempCase):
    def test_default_aw_cmd_prefers_the_checkout_under_test(self) -> None:
        """A rehearsal must exercise THIS code, not whatever ``aw`` is on PATH.

        Kept separate: the subject is the resolved COMMAND LIST, not the argument parser every other
        test in this class exercises, and there is exactly one case to state.
        """

        cmd = uat.default_aw_cmd()
        self.assertEqual(cmd[0], sys.executable)
        self.assertEqual(cmd[1:], ["-m", "agent_workflows"])

    #: (case, argv, the expected `args.json`, why this row exists)
    #:
    #: THE FLAG'S POSITION IS THE COLUMN. This is a real regression, not a hypothetical: a subparser
    #: APPLIES ITS OWN DEFAULTS over the namespace the top-level parse already populated, so a
    #: concrete default on the subparser's `--json` made `--json list` parse to False and silently
    #: emit human output to a caller that asked for machine output. Only a table that varies the
    #: SIDE the flag appears on can state the fix, and only one that varies the SUBCOMMAND can show
    #: the fix is not per-parser: each subparser inherits `--json` from a shared parent, so the bug
    #: was reintroducible one subcommand at a time.
    JSON_FLAG = (
        (
            "--json BEFORE the subcommand",
            ["--json", "list"],
            True,
            "THE MEASURED REGRESSION. The subparser's default ran last and clobbered the value the "
            "top-level flag had already set, so the caller's request was discarded silently",
        ),
        (
            "--json AFTER the subcommand",
            ["list", "--json"],
            True,
            "the natural way to type it, and the case that kept working while the row above was "
            "broken, which is exactly why the bug survived: any test covering only this side passes",
        ),
        (
            "--json before a subcommand that takes a positional",
            ["--json", "probe", "x"],
            True,
            "`--json` is inherited from a SHARED parent parser by every subcommand, so the fix must "
            "hold for all of them. A subcommand with its own positional is where a hand-written "
            "per-subparser default is most likely to be reintroduced",
        ),
        (
            "--json after that subcommand",
            ["probe", "x", "--json"],
            True,
            "the same subcommand from the other side, which is what makes the pair evidence about "
            "the shared parent rather than about `list`",
        ),
        (
            "no --json at all",
            ["list"],
            None,
            "THE NEGATIVE ROW. Absence must be falsy, or every command would emit machine output and "
            "the human-readable report would be unreachable. It is `None` rather than `False` "
            "because the flag is `store_const` with `default=None`: that is what lets either side "
            "win without the other clobbering it, so pinning the value pins the MECHANISM, and a "
            "well-meant change to `default=False` would reintroduce the clobber",
        ),
    )

    def test_the_json_flag_is_honored_on_either_side_of_the_subcommand(self) -> None:
        parser = uat.build_parser()
        wrong = []
        for case, argv, expected, why in self.JSON_FLAG:
            got = parser.parse_args(argv).json
            if got != expected:
                wrong.append(
                    f"  {case} ({argv!r}): expected {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the --json flag parsed wrongly in {len(wrong)} of {len(self.JSON_FLAG)} positions. "
            "One `store_const` pair (top-level `default=None`, subparser `default=SUPPRESS`) decides "
            "every row, so read the pattern: if every BEFORE row is wrong while the AFTER rows pass, "
            "the subparser default stopped being SUPPRESS and is clobbering the global value again, "
            "which is the measured regression. If the no-flag row now reports True, the const leaked "
            "into the default and every invocation emits machine output. FIX: the failure is SILENT "
            "in production, because a caller that asked for JSON gets a human report and parses it "
            "as garbage rather than seeing an error.\n" + "\n".join(wrong),
        )

    def test_bare_separator_is_stripped_from_passthrough_args(self) -> None:
        """Kept separate: the subject is the `--` passthrough grammar, not the `--json` flag.

        It also cannot be folded into the table above: `--to-aw` is not a flag this parser knows, so
        the only way it parses at all is AFTER a `--`, which makes the separator the whole point
        rather than a column value. Verified: without the separator, argparse exits 2 on
        `unrecognized arguments: --to-aw`.
        """

        parser = uat.build_parser()
        args = parser.parse_args(["new", "repo", "--", "--to-aw", "--no-backup"])
        cleaned = [a for a in args.install_args if a != "--"]
        self.assertEqual(cleaned, ["--to-aw", "--no-backup"])

    def test_resolve_source_rejects_a_non_git_directory(self) -> None:
        """Kept separate: an assertRaises refusal."""

        plain = self.tmp / "plain"
        plain.mkdir()
        with self.assertRaises(uat.HarnessError):
            uat.resolve_source(str(plain))

    def test_resolve_source_accepts_an_explicit_path(self) -> None:
        """Kept separate: the POSITIVE counterpart of the assertRaises above, kept beside it.

        Merging the two would need an expected-exception column on a table of one pair, which is more
        machinery than the pair is worth; adjacency already states that the refusal is not total.
        """

        repo = make_source_repo(self.tmp / "src", "1.2.1", "legacy")
        resolved = uat.resolve_source(str(repo))
        self.assertEqual(resolved.path, repo.resolve())
        self.assertEqual(resolved.version, "1.2.1")

    def test_unknown_name_is_a_clean_error_not_a_traceback(self) -> None:
        """Kept separate: asserts a process EXIT CODE from `main`, not a parse result or a return value."""

        code = uat.main(["probe", str(self.tmp / "definitely-not-a-sandbox")])
        self.assertEqual(code, 2)

    def test_env_command_emits_isolating_exports(self) -> None:
        """Kept separate: runs the tool as a real SUBPROCESS and asserts over its stdout."""

        sandbox = uat.create_sandbox(
            uat.SourceRepo.inspect(make_source_repo(self.tmp / "src")),
            self.tmp / "boxes",
        )
        proc = subprocess.run(
            [sys.executable, str(TOOL), "env", str(sandbox)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("export XDG_CONFIG_HOME=", proc.stdout)
        self.assertIn("export AW_HOME=", proc.stdout)

    def test_clean_without_yes_is_a_dry_run(self) -> None:
        """Kept separate: a real SUBPROCESS, and the subject is the CLI's confirmation gate.

        The `clean` TABLE in SafetyInvariantFour covers the library function, which has no dry-run
        concept at all: `-y` is a CLI-layer gate, so this cannot be a row there without conflating the
        two layers.
        """

        sandbox = uat.create_sandbox(
            uat.SourceRepo.inspect(make_source_repo(self.tmp / "src")),
            self.tmp / "boxes",
        )
        proc = subprocess.run(
            [sys.executable, str(TOOL), "clean", str(sandbox)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Would remove", proc.stdout)
        self.assertTrue(sandbox.is_dir(), "dry run must not delete")

    def test_help_runs(self) -> None:
        """Kept separate: a smoke test over a real subprocess; there is no second case to pair it with."""

        proc = subprocess.run(
            [sys.executable, str(TOOL), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Rehearse", proc.stdout)


class NoRunRehearsalTests(TempCase):
    """The copy-only path, which needs no installer and so is fast and hermetic."""

    def test_rehearse_no_run_copies_and_probes_without_installing(self) -> None:
        """Kept separate: the subject is the whole `rehearse` orchestration, not one inspection.

        It asserts the copy-only path performs NO run and reports no tree delta, which is a claim about
        several return keys agreeing at once rather than a value that varies by row.
        """

        source = make_source_repo(self.tmp / "src", "1.2.1", "legacy")
        result = uat.rehearse(str(source), dest_root=self.tmp / "boxes", run_it=False)
        self.assertEqual(result["runs"], [])
        self.assertEqual(result["added"], [])
        self.assertEqual(result["removed"], [])
        self.assertEqual(result["state"]["installed_version"], "1.2.1")
        self.assertTrue(Path(result["sandbox"]).is_dir())

    def test_rehearse_persists_its_findings_into_the_marker(self) -> None:
        """Kept separate: asserts the marker is UPDATED after the rehearsal, a second write.

        `SandboxCreationTests` pins what `create_sandbox` writes; this pins what `rehearse` adds on top
        of it, so the two are claims about different writes to the same file at different times.
        """

        source = make_source_repo(self.tmp / "src", "1.2.1", "legacy")
        result = uat.rehearse(str(source), dest_root=self.tmp / "boxes", run_it=False)
        marker = uat.read_marker(Path(result["sandbox"]))
        assert marker is not None
        self.assertIn("rehearsal", marker)
        self.assertIn("last_probe", marker)
        self.assertEqual(marker["last_probe"]["baseline_version"], "1.2.1")


if __name__ == "__main__":
    unittest.main()
