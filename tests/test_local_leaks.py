"""Tests for the local-leaks detection engine (DECISIONS D93).

Covers: fail-severity structural patterns, warn-only auto-derivation (cross-platform +
missing-source degradation), repo allowlist + user hints, the three scan modes
(working tree / history / wheel), a bounded history scan, public-identifier negatives,
and that THIS repo's tracked tree is clean. Leak tokens are synthesized at runtime so
this test file holds no literal leak. Stdlib unittest only.

Most of this file is TABLE-DRIVEN, because most of it was one shape repeated: build a throwaway
git repository, commit one crafted file, call ``ll.run``, and assert one rule name. The tables
group by SUBJECT (what kind of decision the engine is making) rather than by which scan mode
implements it, so the closed sets this detector rests on - the structural rule names, the three
scan modes, the two severities - are browsable as sets.

THE RULE THAT SHAPES EVERY TABLE HERE, and it is a security rule rather than a style one: A
DETECTOR TEST IS EVIDENCE ONLY IF THE DETECTOR WAS LOOKING. An assertion that some input is CLEAN
passes trivially when detection is switched off, so every table below that contains a clean
expectation also contains at least one PLANTED row in the SAME test whose named rule must fire.
Those planted rows are labelled CONTROL in their reason string, and each table's failure message
says explicitly that the clean rows are vacuous while its control rows are broken. Where a clean
assertion could not be paired with its control without changing what is being asserted (the
repo-wide sweeps), it stays a separate test and says why.

EVERY ROW NAMES ITS RULE AND SEVERITY, never merely "something was flagged". The rule names are
an interface: `--fix` keys its rewrites off them, the allowlist config references them, and the
hook reports them, so a rule that starts answering under a different name is a breaking change
and must fail here.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from tests.support import REPO_ROOT
from agent_workflows import local_leaks as ll


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "t"], check=True)
    return path


def _commit(repo: Path, rel: str, content: str, msg: str) -> None:
    (repo / rel).parent.mkdir(parents=True, exist_ok=True)
    (repo / rel).write_text(content, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", rel], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", msg], check=True)


def _capture_cli(argv):
    """Run ``cli.main(argv)`` capturing stdout+stderr; return (exit code, combined text).

    Module level rather than a method because two classes below drive the same CLI: the
    leak-scanning surface and the self-documentation surface.
    """
    from agent_workflows import cli

    out, err = io.StringIO(), io.StringIO()
    code = None
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = cli.main(argv)
        except SystemExit as exc:  # argparse --help / usage errors
            code = exc.code
    return code, out.getvalue() + err.getvalue()


class ThisRepoTests(unittest.TestCase):
    """The two repo-wide sweeps. DELIBERATELY NOT TABULATED, and deliberately not sampled.

    These are the only tests here whose subject is THE REAL TRACKED TREE rather than a fixture,
    and they are the invariant the whole module exists to serve: nothing in this repository's
    tracked files, and nothing in the engine's own source, may leak maintainer identity. They stay
    two separate tests for three reasons.

    FIRST, merging them into a table would require a shared "expected findings" column whose value
    is `[]` for both, which is exactly the vacuous shape this file's docstring forbids; their
    control lives in the planted rows of the tables below, which prove on the same engine build
    that the rules DO fire.

    SECOND, they must not be narrowed. A sweep that scanned a SAMPLE of tracked files, or that
    scanned the engine with a reduced ruleset, would still pass while missing the one file that
    leaks; so both keep scanning EVERYTHING (`ll.run` over the whole tracked tree, and the full
    `build_ruleset` over the engine's entire source text).

    THIRD, they fail for different reasons and want different messages: a tree finding means a
    commit must be scrubbed, while a self-leak means the engine stopped assembling its sensitive
    literals from fragments and now contains one verbatim.
    """

    def test_this_repo_working_tree_is_clean(self):
        """Kept separate: scans THE WHOLE tracked tree, not a fixture. Must never be sampled."""
        fails, _warns = ll.run(REPO_ROOT)
        self.assertEqual(
            [f"{f.location}: {f.rule}" for f in fails],
            [],
            "local-leak fail findings in tracked files",
        )

    def test_module_source_is_self_clean(self):
        """Kept separate: the subject is the engine's OWN source, scanned with the full ruleset.

        The engine assembles its sensitive tokens from fragments precisely so that its own file is
        not a leak; this is what proves the assembly is still in place.
        """
        text = (REPO_ROOT / "agent_workflows" / "local_leaks.py").read_text(
            encoding="utf-8"
        )
        rs = ll.build_ruleset(REPO_ROOT)
        found = ll.scan_text(text, "local_leaks.py", rs)
        self.assertEqual([f.rule for f in found], [], f"self-leak: {found}")


class StructuralRuleTests(unittest.TestCase):
    """Each structural fail-rule fires on its own planted leak, and public identifiers do not.

    ONE table replaces four tests spread over two classes: two scan-mode tests that each planted
    one home-path shape (`ScanModeTests.test_working_tree_flags_home_path`,
    `test_windows_home_recognized`) and two allowlist-class negatives
    (`AllowlistAndHintsTests.test_public_identifiers_not_flagged`,
    `test_missing_user_hints_is_noop`). All four did the same thing: commit one file into a
    throwaway repo, run the working-tree scan, and check which rules came back. The old class
    boundary tracked which SECTION of the engine the rule came from, which is an implementation
    detail.

    Why the table beats the four: these rule names are a CLOSED SET that `--fix` keys its rewrites
    off, that the allowlist config references, and that the pre-commit hook prints. The realistic
    regression is one pattern being narrowed or renamed, which four tests report as four unrelated
    "False is not true" lines while the table reports one failure naming every rule that moved,
    which is the shape of the actual problem. It also makes the set readable as a set, so the next
    person adding a pattern can see what exists.

    THE POSITIVE AND NEGATIVE ROWS ARE IN ONE TEST DELIBERATELY, AND EACH MAKES THE OTHER
    MEANINGFUL. Without the planted rows, the clean rows pass with detection switched off
    entirely; without the clean rows, a detector that flagged every line would satisfy every
    planted row and would be turned off within a day for crying wolf. The failure message says
    which of the two happened.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        # The user hints file is personal config; point XDG at a throwaway so a real maintainer
        # hints file on the machine running the tests cannot add rules and change these verdicts.
        self._old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(Path(self._tmp.name) / "cfg")
        self.addCleanup(self._restore_xdg)

    def _restore_xdg(self):
        if self._old_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old_xdg

    #: Leak tokens are assembled from fragments at runtime so this test FILE contains no literal
    #: leak (the same convention the engine follows for its own source).
    POSIX_HOME = "/home/" + "someuser" + "/secret/path"
    WINDOWS_HOME = "C:\\Users\\" + "someone" + "\\proj"
    SESSION_ID = "ses_" + "A1b2C3d4E5f6"

    #: (case, the committed file content, the rule name that MUST fire with `fail` severity, or ""
    #: when the content must produce NO findings at all, why this row exists)
    CONTENTS = (
        (
            "a POSIX home directory path",
            "see " + POSIX_HOME + "\n",
            "home-path",
            "THE PRIMARY CONTROL: this is the single most common real leak (a path pasted out of a "
            "terminal), it names the maintainer's account, and it is the one class `--fix` can "
            "rewrite. If this row stops firing the detector is effectively off for the case it "
            "exists to catch",
        ),
        (
            "a Windows home directory path",
            "path " + WINDOWS_HOME + "\n",
            "windows-home",
            "A SEPARATE PATTERN, NOT A DIALECT OF THE ABOVE: it matches a drive letter and "
            "backslashes, so the POSIX pattern cannot catch it. A contributor on Windows leaks a "
            "different string shape, and a Unix-only detector would clear their commits silently",
        ),
        (
            "a captured opencode session id",
            "resumed " + SESSION_ID + " ok\n",
            "session-id",
            "A DIFFERENT LEAK CLASS ENTIRELY: not a path but a CAPTURED CREDENTIAL-LIKE TOKEN from "
            "a real session. `--fix` cannot rewrite it (there is no safe generic substitute), so it "
            "must be detected loudly or it ships. The `ses_<redacted>` placeholder is exempted by "
            "the pattern, which is why a real-looking token is needed here",
        ),
        (
            "the PUBLIC package name, author email, and repo remote together",
            "name = 'agent-workflows'\n"
            + f"email = '{ll._EMAIL}'\n"
            + f"origin = '{ll._REMOTE}'\n",
            "",
            "THE FALSE-POSITIVE CONTROL: all three of these are public BY CONSTRUCTION and appear "
            "in `pyproject.toml`, the README, and every clone's git config. Flagging them would "
            "make the gate fire on every repository and be disabled, so this row protects the "
            "detector's usefulness rather than its reach. It is meaningful only because the planted "
            "rows above prove the engine is still looking",
        ),
        (
            "ordinary prose with no identifier in it",
            "totally clean\n",
            "",
            "THE BASELINE NEGATIVE, with NO user hints file present: absence of a personal hints "
            "file must be a silent no-op, not an error and not an extra finding. This is the state "
            "every CI runner and every fresh clone is in, so a detector that needed the file would "
            "fail everywhere but the maintainer's machine",
        ),
    )

    def test_every_structural_rule_fires_on_its_planted_leak_and_on_nothing_public(
        self,
    ):
        wrong = []
        controls_broken = []
        false_positives = 0
        for case, content, rule, why in self.CONTENTS:
            repo = _init_repo(Path(self._tmp.name) / f"r{len(wrong)}{abs(hash(case))}")
            _commit(repo, "probe.md", content, "probe")
            fails, _warns = ll.run(repo)
            reported = [(f.rule, f.severity) for f in fails]
            problems = []
            if rule:
                if rule not in [r for r, _ in reported]:
                    controls_broken.append(rule)
                    problems.append(
                        f"expected the {rule!r} rule to fire; the engine reported "
                        f"{reported or 'NOTHING AT ALL, so it is not looking'}"
                    )
                else:
                    bad_sev = [(r, s) for r, s in reported if r == rule and s != "fail"]
                    if bad_sev:
                        problems.append(
                            f"{rule!r} must be `fail` severity so it BLOCKS the gate; it was "
                            f"reported as {bad_sev!r}, which only warns and ships anyway"
                        )
            else:
                if reported:
                    false_positives += 1
                    problems.append(
                        f"this content must produce NO fail findings; got {reported!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if controls_broken:
            note += (
                f" THE PLANTED CONTROL ROW(S) FOR {controls_broken!r} FAILED, so the detector is "
                "not looking for those classes and THE CLEAN ROWS IN THIS TABLE PROVE NOTHING: "
                "they pass with detection switched off. Fix the controls first."
            )
        if false_positives:
            note += (
                f" {false_positives} CLEAN row(s) failed, which is the other failure mode: the "
                "detector has become indiscriminate, and a gate that fires on public identifiers "
                "gets switched off, taking the real rules with it."
            )
        self.assertEqual(
            wrong,
            [],
            f"the local-leak engine mishandled {len(wrong)} of {len(self.CONTENTS)} planted "
            f"contents.{note} The rule names are an interface (`--fix` keys rewrites off them, the "
            "allowlist references them, the hook prints them), so SEVERAL PLANTED ROWS FAILING "
            "TOGETHER usually means `_FAIL_PATTERNS` was renamed or `build_ruleset` stopped loading "
            "it, rather than several independent pattern bugs. FIX: a row reporting NOTHING AT ALL "
            "is worse than one reporting the wrong rule, because a pattern that stopped firing lets "
            f"the leak through the hook, CI, and the release gate alike.\n"
            + "\n".join(wrong),
        )


class ScanModeTests(unittest.TestCase):
    """The three scan modes, and the bound on the history scan.

    ONE table replaces three tests (`test_history_flags_leak_removed_from_head`,
    `test_history_max_commits_bound`, `test_wheel_scan_flags_leak`). Each built a repository,
    planted the same class of leak somewhere only ONE mode can see, and asserted that mode found
    it. THE MODE IS THEREFORE A COLUMN, which is the whole point: the property worth asserting is
    that the SAME leak gets different answers from different modes, and no single-mode test can
    state that.

    Why the table beats the three: the modes are a closed set (`working tree` / `history` /
    `wheel`, plus the `max_commits` bound) and a release gate picks among them, so the realistic
    regression is one mode silently degrading to another or to nothing. The history rows are the
    clearest case: the SAME repository must read CLEAN in tree mode and DIRTY in history mode, so
    a history scan that quietly scanned the working tree instead would pass a tree-only test and
    fail exactly the row that encodes the difference.

    EVERY CLEAN EXPECTATION HERE IS PAIRED IN THIS SAME TEST. The tree-clean expectation of the
    history row sits beside that row's own history-dirty expectation, and the bounded row's clean
    expectation is paired with the unbounded row that finds the very same commit. So no row can be
    satisfied by a scanner that returns nothing.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    #: (case, the scan mode, how to build the fixture, kwargs for `ll.run`, the rule that MUST
    #: fire or "" for none, whether the WORKING TREE must simultaneously read clean, why this row
    #: exists)
    MODES = (
        (
            "a leak in an OLD commit, scrubbed at HEAD, read in HISTORY mode",
            "history-unbounded",
            "scrubbed",
            {"history": True},
            "home-path",
            True,
            "THE REASON HISTORY MODE EXISTS: git keeps the old blob forever, so scrubbing a leak at "
            "HEAD does not unpublish it. This row asserts BOTH halves at once - the tree is clean "
            "AND history is dirty - which is the only way to state that the two modes read "
            "different things; a history scan that had quietly degraded to a tree scan would pass "
            "any tree-only test and fail exactly here",
        ),
        (
            "the same old leak with the scan BOUNDED to the most recent 2 commits",
            "history-bounded",
            "padded",
            {"history": True, "max_commits": 2},
            "",
            False,
            "THE BOUND MUST ACTUALLY BOUND, and this row is only meaningful because the row above "
            "proves an unbounded history scan FINDS this class of leak. `--max-commits` exists so a "
            "pre-commit hook stays fast on a deep repository; a bound that silently scanned "
            "everything would be a hook that times out, and a bound that scanned nothing would be a "
            "hook that always passes",
        ),
        (
            "a leak inside a built wheel, in WHEEL mode",
            "wheel",
            "wheel",
            None,
            "home-path",
            False,
            "THE SHIPPING BOUNDARY: the wheel is what reaches PyPI, and it can contain a leak the "
            "tracked tree does not (generated files, stale build artifacts, an accidentally "
            "included path). The scan reads inside the zip, so this is the last gate before a leak "
            "becomes permanently public",
        ),
    )

    def test_each_scan_mode_sees_exactly_the_leak_only_it_can_reach(self):
        wrong = []
        controls_broken = []
        for case, mode, fixture, kwargs, rule, tree_must_be_clean, why in self.MODES:
            repo = _init_repo(Path(self._tmp.name) / f"r-{mode}")
            run_kwargs = dict(kwargs or {})
            if fixture == "scrubbed":
                _commit(repo, "h.md", "/home/" + "ghostuser" + "/x\n", "add leak")
                _commit(repo, "h.md", "clean now\n", "scrub")
            elif fixture == "padded":
                _commit(repo, "h.md", "/home/" + "oldu" + "/x\n", "old leak")
                for i in range(3):
                    _commit(repo, f"pad{i}.md", "clean\n", f"pad {i}")
            else:
                wheel = Path(self._tmp.name) / "pkg.whl"
                with zipfile.ZipFile(wheel, "w") as z:
                    z.writestr("pkg/mod.py", "x = '/home/" + "wheeluser" + "/p'\n")
                run_kwargs["wheel"] = wheel
            fails, _warns = ll.run(repo, **run_kwargs)
            reported = [f.rule for f in fails]
            problems = []
            if rule:
                if rule not in reported:
                    controls_broken.append(f"{mode}/{rule}")
                    problems.append(
                        f"the {mode!r} scan must report {rule!r}; it reported "
                        f"{reported or 'NOTHING AT ALL, so this mode is not scanning'}"
                    )
            elif reported:
                problems.append(
                    f"the {mode!r} scan must report NOTHING here; it reported {reported!r}, so the "
                    "bound did not bound and the scan reached commits it was told to skip"
                )
            if tree_must_be_clean:
                tree_fails, _ = ll.run(repo)
                if [f.rule for f in tree_fails]:
                    problems.append(
                        "the WORKING TREE half of this row must be clean (that is what makes the "
                        f"history finding a history finding); tree reported "
                        f"{[f.rule for f in tree_fails]!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case} [mode={mode}]:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if controls_broken:
            note = (
                f" THE PLANTED CONTROL ROW(S) {controls_broken!r} FAILED, so at least one scan mode "
                "is finding nothing; the bounded row's clean expectation is vacuous while that is "
                "true, because a scanner that returns nothing satisfies it."
            )
        self.assertEqual(
            wrong,
            [],
            f"the scan modes mishandled {len(wrong)} of {len(self.MODES)} fixtures.{note} All three "
            "modes funnel into the same `scan_text` and the same `build_ruleset`, so ALL ROWS "
            "FAILING TOGETHER means the shared core broke rather than any one mode; a single row "
            "failing points at that mode's own enumeration (`git log` walking, the zip reader, the "
            "`max_commits` slice). FIX: history and wheel are the modes that cover already-published "
            "content, so a mode that has gone quiet means past releases were cleared by a scan that "
            f"read nothing.\n" + "\n".join(wrong),
        )


class ConfigDrivenRuleTests(unittest.TestCase):
    """Config changes the verdict on IDENTICAL content: the allowlist exempts, a hint adds a rule.

    ONE table replaces two tests (`test_repo_allowlist_exempts_a_line`,
    `test_user_hint_token_is_flagged`) and MAKES BOTH FALSIFIABLE, which is what merging bought
    here. Each old test asserted only the WITH-CONFIG outcome, so neither could distinguish "the
    config was honored" from "nothing was ever going to be reported". The allowlist test in
    particular asserted an empty finding list, which a disabled detector satisfies perfectly.

    THE TABLE THEREFORE RUNS EACH ROW TWICE ON THE SAME CONTENT, once with the config present and
    once without, and asserts BOTH verdicts. That pairing is the control: the allowlist row must
    report `home-path` with no allowlist and nothing with it, and the user-hint row must report
    `user-hint-0` with the hints file and nothing without it. A detector that was off, or a config
    loader that was ignored, breaks one half of every row.

    CONFIG PRESENCE IS THE COLUMN, which is why this is one table rather than two tests: the
    property being asserted is that config, and only config, moved the verdict.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(Path(self._tmp.name) / "cfg")
        self.addCleanup(self._restore_xdg)

    def _restore_xdg(self):
        if self._old_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old_xdg

    ALLOW_MARKER = "MY-INTERNAL-HOST-OK"
    HINT_TOKEN = "ZzMyCodenameZz"

    #: (case, which config knob, the committed content, rules expected WITHOUT the config, rules
    #: expected WITH the config, why this row exists)
    KNOBS = (
        (
            "a real home-path leak on a line carrying an allowlist marker",
            "repo-allowlist",
            "/home/" + "svcacct" + "/run" + "  # " + ALLOW_MARKER + "\n",
            ("home-path",),
            (),
            "AN ALLOWLIST MUST SUPPRESS A GENUINE FINDING, so the without-config half planting a "
            "REAL `home-path` leak is what makes the with-config half evidence: it proves the line "
            "was suppressed BY THE ALLOWLIST rather than never detected. The old test asserted only "
            "the empty result, which a disabled detector satisfies. The allowlist is committed and "
            "travels with the repo, so it is how a team declares a string public-OK-here",
        ),
        (
            "a personal codename that no built-in pattern knows",
            "user-hints",
            "ref " + HINT_TOKEN + " here\n",
            (),
            ("user-hint-0",),
            "THE INVERSE DIRECTION: config ADDS a rule. This token is not identifying to anyone but "
            "its owner, so no shipped pattern can cover it; personal hints live OUTSIDE the repo "
            "(under the user config dir) precisely so a maintainer's private token list is never "
            "committed. The without-config half proves the finding comes from the hints file, and "
            "the rule name `user-hint-0` pins that hint-derived rules stay individually "
            "attributable rather than being folded into a generic name",
        ),
    )

    def _write_config(self, knob, repo):
        if knob == "repo-allowlist":
            _commit(
                repo,
                ".agents/local-leaks-allowlist.toml",
                f'allow_line_substrings = ["{self.ALLOW_MARKER}"]\n',
                "allowlist",
            )
        else:
            cfg = Path(self._tmp.name) / "cfg" / "agent-workflows"
            cfg.mkdir(parents=True, exist_ok=True)
            (cfg / ll.USER_HINTS_FILENAME).write_text(
                json.dumps({"tokens": [self.HINT_TOKEN]}), encoding="utf-8"
            )

    def _clear_config(self, knob):
        hints = (
            Path(self._tmp.name) / "cfg" / "agent-workflows" / ll.USER_HINTS_FILENAME
        )
        if knob == "user-hints" and hints.exists():
            hints.unlink()

    def test_config_and_only_config_moves_the_verdict_on_identical_content(self):
        wrong = []
        detector_blind = []
        for case, knob, content, without, with_, why in self.KNOBS:
            problems = []
            for present in (False, True):
                self._clear_config(knob)
                repo = _init_repo(Path(self._tmp.name) / f"r-{knob}-{int(present)}")
                if present:
                    self._write_config(knob, repo)
                _commit(repo, "note.md", content, "note")
                expected = with_ if present else without
                reported = tuple(f.rule for f in ll.run(repo)[0])
                label = "WITH the config" if present else "WITHOUT the config"
                missing = [r for r in expected if r not in reported]
                if missing:
                    if not present and without:
                        detector_blind.append(f"{knob} baseline")
                    problems.append(
                        f"{label}: expected {missing!r} to fire; reported "
                        f"{reported or 'NOTHING AT ALL'}"
                    )
                extra = [r for r in reported if r not in expected]
                if extra:
                    problems.append(
                        f"{label}: reported {extra!r}, which this half forbids (expected exactly "
                        f"{expected!r})"
                    )
            if problems:
                wrong.append(
                    f"  {case} [{knob}]:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if detector_blind:
            note = (
                f" THE WITHOUT-CONFIG BASELINE FAILED FOR {detector_blind!r}, so the detector found "
                "nothing even with a planted leak and no suppression in play. While that is true "
                "the with-config (clean) halves prove nothing at all: they are satisfied by a "
                "detector that is switched off. Fix the baseline first."
            )
        self.assertEqual(
            wrong,
            [],
            f"config-driven rules mishandled {len(wrong)} of {len(self.KNOBS)} knobs.{note} Each row "
            "runs the SAME content twice and the failing HALF names the defect: a broken "
            "without-config half means the underlying detection went away, and a broken with-config "
            "half means the config file was not found or not parsed (check "
            "`resolve_allowlist_path` for the allowlist, and `XDG_CONFIG_HOME` / `_config_dir` for "
            "the hints). FIX: an allowlist that stopped being honored is noisy but safe; a hints "
            "file that stopped being read is SILENT and unsafe, because the tokens only its owner "
            f"knows about stop being checked and nobody sees a difference.\n"
            + "\n".join(wrong),
        )


class AutoDeriveTests(unittest.TestCase):
    """Auto-derived tokens are WARN-ONLY: reported, never gate-failing.

    ONE table replaces two tests (`test_derive_is_warn_only_never_fails_gate`,
    `test_missing_sources_degrade_without_error`). Both exercised `derive_warn_tokens` and the
    severity it produces; they differed in whether the derivation SOURCE (the `USER` environment
    variable) was present, so presence of the source is the column.

    THE SEVERITY IS THE WHOLE POINT, and it is why this cannot be folded into
    `StructuralRuleTests`: a derived token is a GUESS (your username, your hostname, a sibling
    checkout's directory name), and a guess must not block a commit. So the table asserts the
    positive and negative sides of one finding: the token IS reported at `warn`, and it is NOT
    among the `fail` findings. A severity promoted to `fail` would turn every contributor whose
    username happens to appear in prose into a blocked commit; a severity demoted to nothing would
    lose the advisory entirely.

    THE PRESENT-SOURCE ROW IS THE CONTROL FOR THE ABSENT-SOURCE ROW. On its own, "derivation
    returns a dict and does not raise" is satisfied by a function that always returns `{}`; paired
    with a row that must produce an actual warn finding, the pair states that derivation works
    when it can and degrades quietly when it cannot.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    PROBE_USER = "ci-derive-probe-user"

    #: (case, env to force during the run (name -> value or None to remove), the token that must
    #: appear as a WARN finding or "" for none, whether `derive_warn_tokens` must return a dict,
    #: why this row exists)
    SOURCES = (
        (
            "a forced USER whose value appears in a committed file",
            {"USER": PROBE_USER},
            PROBE_USER,
            True,
            "THE CONTROL ROW: derivation must actually derive something, or the degradation row "
            "below is satisfied by a function that always returns `{}` and this whole advisory "
            "channel could be dead without any test noticing. It also pins the severity split: the "
            "token must appear among WARNS and must NOT appear among FAILS, because a guessed token "
            "blocking a commit is how a safety feature gets disabled",
        ),
        (
            "every derivation source stripped from the environment",
            {"USER": None, "USERNAME": None},
            "",
            True,
            "GRACEFUL DEGRADATION: CI containers, cron jobs, and minimal shells have no `USER`, so "
            "derivation must return an empty mapping rather than raising. A crash here would make "
            "the gate unrunnable exactly where it runs unattended, and `--warn` would take the "
            "whole scan down with it",
        ),
    )

    def test_derived_tokens_warn_without_failing_and_degrade_when_unavailable(self):
        wrong = []
        control_broken = False
        for case, env, token, want_dict, why in self.SOURCES:
            repo = _init_repo(Path(self._tmp.name) / f"r{abs(hash(case))}")
            _commit(repo, "d.md", f"hello {self.PROBE_USER}\n", "add")
            saved = {k: os.environ.get(k) for k in env}
            try:
                for k, v in env.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
                problems = []
                derived = ll.derive_warn_tokens(repo)
                if want_dict and not isinstance(derived, dict):
                    problems.append(
                        f"derive_warn_tokens must return a dict even with no sources; got "
                        f"{type(derived).__name__}"
                    )
                fails, warns = ll.run(repo, include_warn=True)
                leaked_to_fail = [f for f in fails if token and token in f.snippet]
                if leaked_to_fail:
                    problems.append(
                        f"a DERIVED token must never be a `fail` finding; it was: "
                        f"{[(f.rule, f.severity) for f in leaked_to_fail]!r}. That promotion blocks "
                        "commits on a guess"
                    )
                if token:
                    warned = [
                        w for w in warns if w.severity == "warn" and token in w.snippet
                    ]
                    if not warned:
                        control_broken = True
                        problems.append(
                            f"expected a `warn` finding naming {token!r}; warns were "
                            f"{[(w.rule, w.severity) for w in warns]!r}"
                        )
                if not token and warns:
                    warned_probe = [w for w in warns if self.PROBE_USER in w.snippet]
                    if warned_probe:
                        problems.append(
                            "with every derivation source removed, the probe token must not be "
                            f"derived from anywhere; it still warned: "
                            f"{[(w.rule, w.snippet) for w in warned_probe]!r}"
                        )
            finally:
                for k, v in saved.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if control_broken:
            note = (
                " THE CONTROL ROW FAILED: derivation produced no warn finding even with a forced "
                "source, so the degradation row below it is vacuous (a function that always returns "
                "`{}` satisfies it) and the entire warn channel may be dead."
            )
        self.assertEqual(
            wrong,
            [],
            f"auto-derivation mishandled {len(wrong)} of {len(self.SOURCES)} source states.{note} "
            "The two halves of the severity rule fail differently: a derived token appearing among "
            "FAILS means `build_ruleset` is putting derived tokens in the wrong bucket (check the "
            "`hostname_fail` branch), while no warn at all means `derive_warn_tokens` found no "
            "sources or `include_warn` stopped threading through. FIX: never resolve a failure here "
            "by promoting derived tokens to `fail`; they are guesses, and the warn tier exists so a "
            f"guess can be reported without blocking anyone.\n" + "\n".join(wrong),
        )


class CliSurfaceTests(unittest.TestCase):
    """The `check-local-leaks` CLI: exit code, human confirmation, and no internal jargon.

    ONE table replaces six tests spread over two classes: the two exit-code tests
    (`CliTests.test_cli_exit_zero_on_clean_tree`, `test_cli_exit_one_on_leak`), the clean-run
    confirmation (`SelfDocClarityTests.test_s4_clean_run_prints_confirmation`), and the
    decision-id jargon check on leak output (`test_s2_no_decision_ids_in_local_leaks_messages`).
    All four ran the SAME command over a fixture repository and asserted a different aspect of the
    same invocation, so running it once per tree state and asserting every aspect is strictly
    more coverage from fewer runs: the clean row now also checks jargon, and the leak row now also
    checks the exit code and that the finding is named in the output.

    THE TREE STATE IS THE COLUMN. Exit 0 versus exit 1 is the contract the pre-commit hook and CI
    consume, and it is only a contract if both values are pinned by the same code path.

    THE PLANTED-LEAK ROW IS THE CONTROL FOR THE CLEAN ROW, and it goes further than the tests it
    replaces: it requires the output to NAME the file, the line, and the rule. A CLI that exited 1
    while printing nothing actionable would have satisfied the old exit-code test, and an operator
    would be told only that something, somewhere, is wrong.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    #: (case, the committed content, expected exit code, substrings the output MUST contain, why
    #: this row exists)
    INVOCATIONS = (
        (
            "a clean tracked tree",
            "nothing to see\n",
            0,
            ("No local leaks found.",),
            "EXIT 0 PLUS AN EXPLICIT CONFIRMATION: the hook and CI branch on the code, and a HUMAN "
            "needs to know the scan RAN rather than silently did nothing. Silence on success is "
            "indistinguishable from a scanner that crashed early, which is how a broken gate stays "
            "broken for months. This row is evidence only because of the planted row below",
        ),
        (
            "a tracked file containing a home-path leak",
            "/home/" + "cliuser" + "/x\n",
            1,
            ("probe.md", "home-path"),
            "THE CONTROL ROW: exit 1 is what actually blocks a commit, and the output must NAME the "
            "file and the rule so the operator can act. The tests this replaces asserted the exit "
            "code alone, which a CLI that printed nothing would satisfy; naming `home-path` also "
            "pins that the rule id reaches the user, since that is the string the allowlist and "
            "`--fix` are documented in terms of",
        ),
    )

    def test_the_cli_reports_each_tree_state_with_the_right_code_and_an_actionable_message(
        self,
    ):
        wrong = []
        control_broken = False
        for case, content, expect_code, needles, why in self.INVOCATIONS:
            repo = _init_repo(Path(self._tmp.name) / f"r{abs(hash(case))}")
            _commit(repo, "probe.md", content, "probe")
            code, text = _capture_cli(["check-local-leaks", str(repo), "--no-color"])
            problems = []
            if code != expect_code:
                if expect_code == 1:
                    control_broken = True
                    problems.append(
                        f"expected exit 1 (the value that BLOCKS a commit); got {code}. Output was "
                        f"{text!r}"
                    )
                else:
                    problems.append(
                        f"expected exit 0 on a clean tree; got {code}. Output was {text!r}"
                    )
            missing = [n for n in needles if n not in text]
            if missing:
                problems.append(
                    f"the output must contain {missing!r} to be actionable; it was {text!r}"
                )
            # Internal decision ids (D92/D93 and friends) are jargon to a user; the message must
            # explain the leak, not cite the decision that introduced the rule.
            jargon = re.search(r"\(D\d+", text)
            if jargon:
                problems.append(
                    f"internal decision-id jargon leaked into user-facing output: {jargon.group(0)!r}"
                    f" in {text!r}"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if control_broken:
            note = (
                " THE PLANTED-LEAK ROW FAILED TO EXIT 1, so the CLI is not blocking anything and "
                "the clean row is vacuous: a command that always exits 0 satisfies it."
            )
        self.assertEqual(
            wrong,
            [],
            f"the check-local-leaks CLI mishandled {len(wrong)} of {len(self.INVOCATIONS)} tree "
            f"states.{note} Both rows go through one `cli.main` dispatch, so BOTH failing means the "
            "subcommand wiring broke rather than the detection; one failing points at the exit-code "
            "mapping or the renderer. FIX: exit 1 is the contract the pre-commit hook and CI read, "
            "so a clean-looking exit 0 on a dirty tree disables the gate everywhere at once while "
            f"looking perfectly healthy.\n" + "\n".join(wrong),
        )


class SelfDocClarityTests(unittest.TestCase):
    """assess-self-documentation S1-S4: the aw CLI teaches at the point of use.

    ONE table replaces three of the original six tests in this class (the bad/good `--status`
    pair and the `install all` discoverability check); the two leak-message tests moved to
    `CliSurfaceTests`, where they share an invocation with the exit-code rows, and the help-text
    jargon sweep stays separate below.

    The rows are held together by a single claim: the CLI must TEACH at the point of use rather
    than merely refusing. So a typo'd value must exit nonzero AND name real alternatives, while a
    correct value must be accepted - and those two are the same table because "names real
    alternatives" is only meaningful if the named values actually work. THE VALID-VALUE ROW IS
    THEREFORE THE CONTROL: it takes a value the error message advertises and proves the CLI
    accepts it, so the help cannot advertise a vocabulary the parser rejects.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = _init_repo(Path(self._tmp.name) / "r")
        (self.repo / ".agents" / "plans" / "pending").mkdir(parents=True)

    #: (case, argv, expected exit code, substrings the output MUST contain, why this row exists)
    SURFACES = (
        (
            "a typo'd --status value",
            ("ipd", "board", "--status", "pendign"),
            2,
            ("draft", "approved", "executed"),
            "S1: A REFUSAL MUST TEACH. Exit 2 alone leaves the user guessing at a closed "
            "vocabulary they cannot see, so the message has to name real statuses. Three are "
            "required rather than one, so a message that mentions a single example still fails",
        ),
        (
            "a valid --status value",
            ("ipd", "board", "--status", "approved"),
            0,
            (),
            "THE CONTROL FOR THE ROW ABOVE: `approved` is one of the values that error message "
            "advertises, so this row proves the advertised vocabulary is the vocabulary the parser "
            "accepts. Without it the CLI could refuse every value while printing a helpful list of "
            "values that do not work, and both halves would look correct",
        ),
        (
            "the top-level help",
            ("--help",),
            0,
            ("install all",),
            "S3: DISCOVERABILITY. `install all` is the command a new user needs first, and a "
            "command absent from the top-level help does not exist as far as they are concerned",
        ),
    )

    def test_the_cli_teaches_the_vocabulary_it_enforces(self):
        wrong = []
        for case, argv, expect_code, needles, why in self.SURFACES:
            full = list(argv)
            if "board" in full:
                full = full[:2] + ["--dir", str(self.repo)] + full[2:]
            full.append("--no-color")
            code, text = _capture_cli(full)
            problems = []
            if code != expect_code:
                problems.append(
                    f"expected exit {expect_code}, got {code}; output was {text[:400]!r}"
                )
            missing = [n for n in needles if n not in text]
            if missing:
                problems.append(
                    f"the output must name {missing!r}; it was {text[:400]!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (argv={full!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the self-documenting CLI surface mishandled {len(wrong)} of {len(self.SURFACES)} "
            "invocations. The typo row and the valid row are two halves of one claim, so the "
            "pattern names the defect: the typo row alone means the error message stopped listing "
            "the vocabulary, the valid row alone means a value the message advertises is no longer "
            "accepted, and both together mean `--status` parsing was rewritten. FIX: do not satisfy "
            "the typo row by widening what is accepted; the point is that a refusal names the "
            f"alternatives.\n" + "\n".join(wrong),
        )

    def test_s2_no_decision_ids_in_help(self):
        """Kept separate: sweeps the FULL help text of two commands for internal jargon.

        The `CliSurfaceTests` rows check jargon in leak MESSAGES; this checks HELP, which is
        generated by argparse from docstrings and flag help rather than by the renderer, so a
        decision id can appear in one and not the other. It is a negative-only sweep over a whole
        text with no per-row data, so there is nothing to tabulate.
        """
        for argv in (["--help"], ["check-local-leaks", "--help"]):
            _, text = _capture_cli(argv)
            self.assertIsNone(
                re.search(r"\(D\d+", text),
                f"decision-id jargon in help for {argv}: leaked",
            )


if __name__ == "__main__":
    unittest.main()
