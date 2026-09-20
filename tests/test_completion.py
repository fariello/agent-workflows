"""Tests for tabcomp Orders 01 (bja8og) and 02 (4f1j25): shell completion.

Order 01 covers E-01 (introspect_cli_tree surfaces user commands, excludes the internal `*-gate`
family and the hidden aliases), E-02 (the three generators emit valid, alias-binding, shell-escaped
scripts; each parses under its own shell's syntax checker where installed), E-03 (`aw completion
<shell>` streams the script to stdout with exit 0; bare invocation detects $SHELL with a bash
fallback; the parser shape leaves room for tabcomp-03 install/uninstall), and E-04.

Order 02 (4f1j25) covers dynamic completion: E-01 (`complete_query` returns bare-token candidates -
subcommands/flags, Set ids, run ids, plan/spec/backlog id6 handles extracted from path stems, and
per-type status enums from the real vocab modules - within the <50ms latency budget under active-
disposition scan-scoping), E-02 (the `aw __complete --cword N -- <tokens>` wire protocol matches
`complete_query` and always exits 0), and E-03 (the `# PYTHON_ARGCOMPLETE_OK` marker is a real
comment inside the first 1024 bytes and the soft `argcomplete` import leaves the CLI working when
argcomplete is absent).
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import pytest

from agent_workflows import cli, completion
from agent_workflows.term import Term


def _run(argv):
    out = io.StringIO()
    with redirect_stdout(out):
        rc = cli.main(argv)
    return rc, out.getvalue()


class IntrospectTreeTests(unittest.TestCase):
    """The command-visibility policy (E-01), asserted as ONE table of named in/out decisions.

    Three tests became this one because they were three spellings of a single question: is this
    name in the completable top-level set? The table is better than the three for the reason the
    subject makes unavoidable: visibility is decided by ONE policy in
    ``completion._visible_subcommands``, so the realistic regression is that policy changing and
    taking a whole CLASS of names with it (every ``*-gate``, every argparse alias). Three tests
    report that as three unrelated red lines that each name only their first offender; the table
    reports one failure listing every name whose visibility moved, which is the shape of the
    actual defect.

    The POSITIVE rows (real user commands that must be PRESENT) are deliberately in the same
    table as the exclusions. A policy that hides everything satisfies every exclusion row on its
    own, so the negative rows are vacuous without them.
    """

    #: (command name, must it be completable?, why this row exists)
    VISIBILITY = (
        (
            "install",
            True,
            "the headline user command; if this is hidden, completion is useless",
        ),
        ("check", True, "a primary user verb"),
        ("doctor", True, "a primary user verb"),
        (
            "runs",
            True,
            "the READING noun for runs (a user-facing verb after the run/runs split)",
        ),
        (
            "ipd",
            True,
            "the plan noun, and the parent whose nested leaves are asserted below",
        ),
        ("specs", True, "the spec noun"),
        (
            "completion",
            True,
            "the command that generates this very feature must complete itself",
        ),
        (
            "ipd-executed-gate",
            False,
            "the *-gate family is INTERNAL pre-commit plumbing, never typed by a human",
        ),
        ("ipd-status-untooled-gate", False, "internal gate"),
        ("backlog-blocking-close-gate", False, "internal gate"),
        ("ipd-dependency-statement-gate", False, "internal gate"),
        ("precommit-scope-gate", False, "internal gate"),
        ("prepush-authorization-gate", False, "internal gate"),
        (
            "att",
            False,
            "an argparse ALIAS shares its parent's parser and carries no help entry, so offering "
            "it would double every completion list",
        ),
        ("spec", False, "hidden alias of `specs`"),
        ("sanitize", False, "hidden alias of `check-local-leaks`"),
        ("antigravity", False, "hidden alias of `agy`"),
        ("opencode", False, "hidden alias of `oc`"),
    )

    def setUp(self) -> None:
        self.tree = completion.introspect_cli_tree(cli._build_parser())
        self.top = set(self.tree["subcommands"])

    def test_every_named_command_has_its_declared_visibility(self) -> None:
        wrong = []
        for name, should_be_present, why in self.VISIBILITY:
            present = name in self.top
            if present != should_be_present:
                wrong.append(
                    f"  {name!r}: expected {'COMPLETABLE' if should_be_present else 'EXCLUDED'}, "
                    f"got {'COMPLETABLE' if present else 'EXCLUDED'}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"completion.introspect_cli_tree got the visibility wrong for {len(wrong)} of "
            f"{len(self.VISIBILITY)} names. Visibility is decided by ONE policy in "
            "`completion._visible_subcommands`, so several rows moving together usually means that "
            "policy changed (or argparse changed how aliases carry help entries) rather than "
            "several independent mistakes. If the POSITIVE rows are the ones failing, every "
            "exclusion row above is vacuous, because a policy that hides everything satisfies "
            "all of them. FIX: adjust `_visible_subcommands`, not this table, unless a command was "
            f"deliberately renamed or retired.\n" + "\n".join(wrong),
        )

    def test_no_gate_suffixed_command_at_all_is_completable(self) -> None:
        """Kept separate: a UNIVERSAL claim over the whole command set, not a per-name row.

        The table above names the six gates that exist today; this catches a SEVENTH added later
        that nobody thought to tabulate.
        """
        self.assertFalse(
            any(name.endswith("-gate") for name in self.top),
            "no *-gate command may be completable; found "
            f"{sorted(n for n in self.top if n.endswith('-gate'))}",
        )

    def test_nested_subcommands_captured(self) -> None:
        """Kept separate: asserts RECURSION (a nested dict is non-empty), a structurally different
        claim from the flat in/out membership every visibility row makes."""
        # `ipd` has real nested subcommands (e.g. set/begin/finalize/lint) - the tree must recurse.
        self.assertIn("ipd", self.tree["subcommands"])
        ipd_subs = self.tree["subcommands"]["ipd"]["subcommands"]
        self.assertTrue(ipd_subs, "ipd should expose nested subcommands")

    def test_does_not_mutate_parser(self) -> None:
        """Kept separate: a BEFORE/AFTER comparison of the parser against itself, not a data row."""
        p = cli._build_parser()
        before = [a.dest for a in p._actions]
        completion.introspect_cli_tree(p)
        after = [a.dest for a in p._actions]
        self.assertEqual(before, after)


class GeneratorSyntaxTests(unittest.TestCase):
    """Each generator emits a NON-EMPTY script carrying its shell's required binding constructs.

    ONE table replaces three tests that were the same test three times over: call a generator,
    assert the script is non-empty, assert the shell-specific lines that bind the three console
    aliases. The table wins for a reason specific to this subject: all three generators consume the
    SAME introspected tree and share the escaping helpers, so the realistic breakage (a tree shape
    change, or an ENTRYPOINTS edit) takes several shells down at once. Three tests report that as
    three red lines, and each `assertIn` short-circuits so each names only its FIRST missing
    needle; the table reports one failure naming every missing construct in every shell, which is
    what tells you the cause is shared rather than per-shell.

    Alias binding is per-shell by NECESSITY, not by taste, which is why the needles differ per row:
    bash binds via one `complete -F` line naming all three commands, zsh binds from the
    first-line `#compdef`, and fish needs a separate `complete -c` per command name. Those three
    mechanisms are asserted as three rows of one table rather than three tests so that a change to
    `ENTRYPOINTS` shows up as "all three shells lost agent-workflows" in a single message.
    """

    #: (shell, generator, required substrings, why this row exists)
    GENERATORS = (
        (
            "bash",
            "generate_bash_completion",
            (
                "_aw_completion()",
                "complete -F _aw_completion aw agentwf agent-workflows",
            ),
            "bash binds with ONE `complete -F` naming all three aliases, so the function must be "
            "defined and bound in the same script",
        ),
        (
            "zsh",
            "generate_zsh_completion",
            ("#compdef aw agentwf agent-workflows",),
            "zsh binds every alias from the `#compdef` line, which compinit honors on LINE 1 only",
        ),
        (
            "fish",
            "generate_fish_completion",
            ("complete -c aw", "complete -c agentwf", "complete -c agent-workflows"),
            "fish has no multi-command bind, so each alias needs its own `complete -c` line",
        ),
    )

    def setUp(self) -> None:
        self.tree = completion.introspect_cli_tree(cli._build_parser())

    def test_every_generator_emits_its_required_binding_constructs(self) -> None:
        wrong = []
        for shell, generator_name, needles, why in self.GENERATORS:
            script = getattr(completion, generator_name)(self.tree)
            if not script.strip():
                wrong.append(
                    f"  {shell}: completion.{generator_name} returned an EMPTY script, so its "
                    f"{len(needles)} required construct(s) cannot be checked at all\n"
                    f"    this row exists because: {why}"
                )
                continue
            missing = [n for n in needles if n not in script]
            if missing:
                wrong.append(
                    f"  {shell}: completion.{generator_name} omitted {missing!r}\n"
                    f"    expected all of {list(needles)!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the completion generators are missing required constructs in {len(wrong)} of "
            f"{len(self.GENERATORS)} shells. All three consume the same introspected tree and the "
            "same ENTRYPOINTS tuple, so several shells failing together usually means the shared "
            "input changed (an alias added/removed, or the tree shape) rather than three "
            "independent generator bugs. FIX: check `completion.ENTRYPOINTS` and "
            "`introspect_cli_tree` first; only edit a single generator when exactly one row "
            f"fails.\n" + "\n".join(wrong),
        )

    # The three shell-syntax checks below are deliberately NOT rows in a table. Each carries its
    # OWN `skipUnless` on a different external binary, and merging them would couple the three
    # skips into one: a machine with zsh but no fish would either skip both (losing real zsh
    # coverage) or report a missing interpreter as a failure. Per-test skips are the point.

    @unittest.skipUnless(shutil.which("bash"), "bash not installed")
    def test_bash_parses_under_bash_n(self) -> None:
        """Kept separate: gated on its own interpreter being installed (`skipUnless`)."""
        self._check_shell("bash", ["bash", "-n"], completion.generate_bash_completion)

    @unittest.skipUnless(shutil.which("zsh"), "zsh not installed")
    def test_zsh_parses_under_zsh_n(self) -> None:
        """Kept separate: gated on its own interpreter being installed (`skipUnless`)."""
        self._check_shell("zsh", ["zsh", "-n"], completion.generate_zsh_completion)

    @unittest.skipUnless(shutil.which("fish"), "fish not installed")
    def test_fish_parses_under_fish_no_execute(self) -> None:
        """Kept separate: gated on its own interpreter being installed (`skipUnless`)."""
        self._check_shell(
            "fish", ["fish", "--no-execute"], completion.generate_fish_completion
        )

    def _check_shell(self, shell, cmd, gen):
        script = gen(self.tree)
        with tempfile.NamedTemporaryFile("w", suffix=f".{shell}", delete=False) as fh:
            fh.write(script)
            path = fh.name
        try:
            proc = subprocess.run(cmd + [path], capture_output=True, text=True)
            self.assertEqual(
                proc.returncode, 0, f"{shell} -n failed: {proc.stderr}\n{script}"
            )
        finally:
            os.unlink(path)

    def test_escaping_guarantee_backtick_and_dollar(self) -> None:
        """Kept separate: builds a SYNTHETIC hostile tree and shells out, unlike every table row,
        which consumes the real CLI tree."""
        # A generated script whose embedded help text contains a backtick / $ must remain valid.
        # Build a tiny synthetic tree carrying hostile help text and assert bash -n still passes
        # (bash is the always-available baseline; the zsh/fish escapers are unit-covered by the
        # syntax tests above where those shells exist).
        hostile = {
            "flags": [
                {
                    "flag": "--danger",
                    "help": "uses `rm -rf $HOME` and 'quotes' and \\ backslash",
                }
            ],
            "subcommands": {
                "cmd`x": {"flags": [], "subcommands": {}},
                "cmd$y": {"flags": [], "subcommands": {}},
            },
        }
        bash_script = completion.generate_bash_completion(hostile)
        if shutil.which("bash"):
            with tempfile.NamedTemporaryFile("w", suffix=".bash", delete=False) as fh:
                fh.write(bash_script)
                path = fh.name
            try:
                proc = subprocess.run(
                    ["bash", "-n", path], capture_output=True, text=True
                )
                self.assertEqual(
                    proc.returncode, 0, f"escaping failed: {proc.stderr}\n{bash_script}"
                )
            finally:
                os.unlink(path)
        # The zsh/fish escapers must not leave a raw unescaped backtick/$ in a description context.
        zsh_desc = completion._zsh_desc("uses `x` and $y")
        self.assertNotIn("`", zsh_desc.replace("\\`", ""))
        self.assertNotIn("$", zsh_desc.replace("\\$", ""))


_UNSET = object()  #: sentinel meaning "$SHELL must be absent for this row"


class CompletionCliTests(unittest.TestCase):
    """`aw completion [shell]` streams the right script to stdout and exits 0.

    Four tests became ONE table with a MODE COLUMN, because the distinction between them was never
    pure data: two passed the shell EXPLICITLY as an argument and two left it off so the shell is
    DETECTED from `$SHELL`. Splitting those into two tables would hide the property that actually
    matters, namely that both routes land on the same generator, so the mode is a column
    (`shell_arg=None` means bare invocation) and the `$SHELL` value is another.

    Why the table beats the four tests: explicit selection and `$SHELL` detection funnel into ONE
    dispatch in the `completion` handler, so the realistic failure is that dispatch changing and
    sending several shells to the wrong generator at once. Four tests report that as four red
    lines, and the old `test_cli_zsh_and_fish_exit0` looped internally so it stopped at the FIRST
    broken shell and never told you about the second. The table reports every wrong row, with the
    script head it actually got.

    The rows keep BOTH assertions the old tests made, which were not the same assertion: bash's
    header had to be at position 0 (`startswith`, which is what proves nothing is printed before
    the script), while zsh/fish only had to CONTAIN their binding line. `at_start` is that column.
    """

    #: (case, shell_arg or None for bare, $SHELL value or _UNSET, needle, must the needle be at
    #: position 0?, why this row exists)
    INVOCATIONS = (
        (
            "explicit bash",
            "bash",
            _UNSET,
            "# bash completion for aw",
            True,
            "the header must be the FIRST byte on stdout: anything printed before it would be "
            "sourced by the shell as part of the script",
        ),
        (
            "explicit zsh",
            "zsh",
            _UNSET,
            "#compdef aw agentwf agent-workflows",
            True,
            "zsh's compinit honors `#compdef` on LINE 1 only, so for zsh the at-start claim is a "
            "functional requirement rather than a cosmetic one",
        ),
        (
            "explicit fish",
            "fish",
            _UNSET,
            "complete -c aw",
            False,
            "fish has no first-line marker, so the binding line need only be present",
        ),
        (
            "bare, $SHELL unset",
            None,
            _UNSET,
            "# bash completion for aw",
            True,
            "with no $SHELL to read, detection must FALL BACK to bash rather than failing",
        ),
        (
            "bare, $SHELL=/usr/bin/zsh",
            None,
            "/usr/bin/zsh",
            "#compdef aw agentwf agent-workflows",
            True,
            "bare invocation must DETECT the shell from $SHELL, not always emit bash",
        ),
        (
            "bare, $SHELL=/usr/bin/fish",
            None,
            "/usr/bin/fish",
            "complete -c aw",
            False,
            "detection covers all three supported shells, not just zsh",
        ),
        (
            "bare, $SHELL=/usr/bin/tcsh",
            None,
            "/usr/bin/tcsh",
            "# bash completion for aw",
            True,
            "an UNSUPPORTED shell degrades to bash instead of erroring out",
        ),
    )

    def test_every_invocation_streams_its_shell_script_and_exits_zero(self) -> None:
        wrong = []
        for case, shell_arg, shell_env, needle, at_start, why in self.INVOCATIONS:
            argv = ["completion"] + ([shell_arg] if shell_arg else [])
            with mock.patch.dict(os.environ, {}, clear=False):
                if shell_env is _UNSET:
                    os.environ.pop("SHELL", None)
                else:
                    os.environ["SHELL"] = shell_env
                rc, out = _run(argv)
            problems = []
            if rc != 0:
                problems.append(f"exit code expected 0, got {rc}")
            if at_start:
                if not out.startswith(needle):
                    problems.append(
                        f"expected stdout to START with {needle!r}, got {out[:80]!r}"
                    )
            elif needle not in out:
                problems.append(
                    f"expected stdout to CONTAIN {needle!r}, got {out[:80]!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (argv={argv!r}): "
                    + "; ".join(problems)
                    + f"\n    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`aw completion` mishandled {len(wrong)} of {len(self.INVOCATIONS)} invocations. "
            "Explicit selection and $SHELL detection share ONE dispatch, so several rows failing "
            "together usually means that dispatch (or `cli._detect_shell`) changed rather than one "
            "generator breaking. FIX: if only the bare rows fail, look at `cli._detect_shell`; if "
            "explicit and bare rows for the SAME shell both fail, the generator for that shell is "
            f"the suspect.\n" + "\n".join(wrong),
        )

    #: (`$SHELL` value, detected shell, why this row exists)
    DETECTED_SHELLS = (
        ("/bin/bash", "bash", "the ordinary bash path"),
        ("/usr/bin/zsh", "zsh", "a supported shell is detected by its basename"),
        ("/usr/bin/fish", "fish", "the third supported shell"),
        (
            "/usr/bin/tcsh",
            "bash",
            "an UNSUPPORTED shell degrades to bash, because emitting nothing would look like a "
            "broken install",
        ),
        (
            "/usr/bin/zsh-5.9",
            "bash",
            "matching is on the EXACT basename, so a versioned binary name is not zsh: a "
            "zsh-shaped script under a name we did not verify is worse than the bash fallback",
        ),
        ("", "bash", "an empty $SHELL is no information, so fall back"),
    )

    def test_detect_shell_maps_every_shell_env_value_to_its_generator(self) -> None:
        wrong = []
        for value, expected, why in self.DETECTED_SHELLS:
            with mock.patch.dict(os.environ, {"SHELL": value}):
                got = cli._detect_shell()
            if got != expected:
                wrong.append(
                    f"  $SHELL={value!r} expected {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"cli._detect_shell misread {len(wrong)} of {len(self.DETECTED_SHELLS)} $SHELL values. "
            "One basename lookup against one supported set decides all of these, so several rows "
            "moving together usually means the supported set or the basename handling changed. "
            "FIX: a row expecting 'bash' that now returns a real shell name means the fallback was "
            "widened (a versioned or unsupported binary is being trusted); the reverse means a "
            f"supported shell was dropped from the set.\n" + "\n".join(wrong),
        )

    def test_parser_shape_allows_child03_extension(self) -> None:
        """Kept separate: asserts the ABSENCE of an argparse `choices=` constraint (forward-compat),
        not a value mapping."""
        # Forward-compat: `target` is a free-form optional positional (no fixed choices), so a future
        # `aw completion install`/`uninstall` token parses without a redesign. Confirm the parser
        # accepts a non-shell target token (it reaches the handler, which validates), i.e. the parse
        # itself does not reject it via `choices`.
        parser = cli._build_parser()
        args = parser.parse_args(["completion", "install"])
        self.assertEqual(args.command, "completion")
        self.assertEqual(args.target, "install")  # not constrained by choices=


# --------------------------------------------------------------------------------------
# tabcomp Order 02 (4f1j25): dynamic contextual completion.
# --------------------------------------------------------------------------------------


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class _DynamicRepoFixture(unittest.TestCase):
    """A controlled temp repo with plans/specs/backlog/runs of KNOWN id6/status, so expected
    completions are stable (never the live repo). Mirrors the tests/test_selectors.py convention."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        rec = self.root / ".aw" / "records"

        # Two ACTIVE plans (pending) in Set `tabcomp`, one TERMINAL plan (executed) that MUST be
        # excluded by the active-disposition scan-scoping (latency budget).
        _write(
            rec / "plans" / "pending" / "20260828-tabcomp-02-4f1j25-child-two.ipd.md",
            "# IPD: two\n\n- Id: 4f1j25\n- Status: approved\n- Set: tabcomp (tabs)\n\n## Goal\n\nx\n",
        )
        _write(
            rec / "plans" / "pending" / "20260828-tabcomp-01-bja8og-child-one.ipd.md",
            "# IPD: one\n\n- Id: bja8og\n- Status: to-review\n- Set: tabcomp (tabs)\n\n## Goal\n\nx\n",
        )
        _write(
            rec / "plans" / "executed" / "20260101-oldset-01-ffffff-terminal.ipd.md",
            "# IPD: old\n\n- Id: ffffff\n- Status: executed\n- Set: oldset\n\n## Goal\n\nx\n",
        )
        # A spec and a backlog item, each with a KNOWN id6.
        _write(
            rec / "specs" / "20260828-abc123-01-abc123-a-spec.spec.md",
            "# Spec\n\n- Id: abc123\n- Status: draft\n",
        )
        _write(
            rec / "backlog" / "open" / "20260828-def456-01-def456-a-task.md",
            "# Task\n\n- Id: def456\n- Status: open\n- Summary: x\n",
        )
        # A single PLANNED release record with a KNOWN id6 + version, so `aw releases show`
        # completion (IPD w0ln4q E-04) resolves stably and `next` is offered.
        _write(
            rec / "releases" / "20260828-rel111-01-rel111-7-0-0.release.md",
            "# Release: 7.0.0\n\n- Id: rel111\n- Status: planned\n- Version: 7.0.0\n"
            "- Summary: the completable one\n",
        )
        # A run directory.
        (rec / "runs" / "run-20260829T000000Z-1").mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()


class CompleteQueryTests(_DynamicRepoFixture):
    """Every completion POSITION answers with the right candidate vocabulary.

    Thirteen tests across three classes became ONE table, because each was the same three lines:
    call `complete_query(tokens, cword, root)` against the SAME fixture repo and make one claim
    about the returned list. Only the position and the expected candidates differed, which is the
    definition of a data row.

    Why the table beats the thirteen: a single dispatch in `complete_query` decides which
    vocabulary a position gets (subcommand names, then flags, then artifact id6 handles, Set ids,
    run ids, the per-type status enums). The realistic failure is that dispatch mis-routing, which
    moves SEVERAL positions at once: a change to the run/runs noun split, or a `records_backend`
    regression, breaks every artifact row together while leaving the flag rows fine. Thirteen tests
    report that as thirteen unrelated red lines; the table reports one failure listing every
    position that moved with the candidates it actually produced, and that pattern is what
    identifies the cause.

    The MODE column is load-bearing and is why this is one table rather than several. The old tests
    did not all assert the same KIND of thing about their list: some pinned it EXACTLY (`equals`,
    the strongest claim, and the only one that catches an over-broad answer), some only required a
    candidate to be PRESENT because the real vocabulary is larger than the fixture (`contains`),
    some required a candidate to be ABSENT (`excludes`, which is how active-disposition scoping and
    the retired viewer leaves are proven), and one required every candidate to share the typed
    prefix (`all_start_with`). Collapsing those into one mode would either weaken the exact rows or
    make the superset rows fail, so a row carries a TUPLE of checks and keeps every distinct
    assertion the old tests made.
    """

    #: Each row: (case, tokens, cword, checks, why this row exists).
    #: `checks` is a tuple of (mode, value) pairs, all of which must hold:
    #:   "equals"         -> the returned list is EXACTLY this (order included)
    #:   "contains"       -> every named candidate is present (the real vocabulary is larger)
    #:   "excludes"       -> no named candidate is present
    #:   "all_start_with" -> every returned candidate starts with this prefix
    QUERIES = (
        (
            "a subcommand prefix in command position",
            ["aw", "r"],
            1,
            (("contains", ("run", "runs", "research", "rename")),),
            "command position offers subcommand names; asserted as a SUPERSET because the real "
            "command set is larger than any list pinned here would stay",
        ),
        (
            "a flag prefix after a noun",
            ["aw", "ipd", "--js"],
            2,
            (("contains", ("--json",)), ("all_start_with", "--js")),
            "a token starting with `-` switches the vocabulary to that noun's FLAGS, and every "
            "candidate must honor the typed prefix or the shell will insert a wrong completion",
        ),
        (
            "a plan id6 in a plan target slot",
            ["aw", "ipd", "lint", "b"],
            3,
            (("equals", ["bja8og"]),),
            "pinned EXACTLY because the value must be a BARE id6, not the filename or path that "
            "`selectors.resolve_selectors` actually returns",
        ),
        (
            "a plan id6 whose only match is TERMINAL",
            ["aw", "ipd", "lint", "f"],
            3,
            (("excludes", ("ffffff",)), ("equals", [])),
            "`ffffff` is an EXECUTED plan, and scans are scoped to active dispositions for the "
            "<50ms budget (the unscoped full-history sweep measured ~500ms)",
        ),
        (
            "a spec id6 in a spec target slot",
            ["aw", "specs", "set", "abc"],
            3,
            (("contains", ("abc123",)),),
            "the spec record type resolves through the same extraction as plans",
        ),
        (
            "a backlog id6 in a backlog target slot",
            ["aw", "backlog", "set", "def"],
            3,
            (("contains", ("def456",)),),
            "the backlog record type resolves too, proving the branch is per-type not plan-only",
        ),
        (
            "a Set id under the READING noun",
            ["aw", "runs", "t"],
            2,
            (("equals", ["tabcomp"]),),
            "the Set id comes from the plans' `- Set:` FRONT MATTER, not from the resolver; target "
            "completion lives on the reading noun after the runnamecollapse (0soncw E-08) split",
        ),
        (
            "a run id under the READING noun",
            ["aw", "runs", "run-"],
            2,
            (("contains", ("run-20260829T000000Z-1",)),),
            "run ids come from the runs directory listing",
        ),
        (
            "the WRITING noun's own first slot",
            ["aw", "run", ""],
            2,
            (
                ("equals", ["as", "cancel", "finalize", "ipd", "record", "start"]),
                ("excludes", ("show", "status", "evidence", "verify-ledger", "list")),
                ("excludes", ("tabcomp", "run-20260829T000000Z-1")),
            ),
            "E-08: `aw run` takes only its writer leaves here (plus the `as`/`ipd` dispatch routes "
            "runprofile ygzq71 added), so offering a TARGET or a retired VIEWER leaf would "
            "advertise a shape the parser rejects. Pinned exactly for that reason",
        ),
        (
            "a writer leaf's target slot",
            ["aw", "run", "start", "t"],
            3,
            (("equals", ["tabcomp"]),),
            "`aw run start <TAB>` IS a target position, so the dynamic answer must still fire "
            "under the writing noun one token deeper",
        ),
        (
            "a viewer leaf's target slot",
            ["aw", "runs", "show", "run-"],
            3,
            (("contains", ("run-20260829T000000Z-1",)),),
            "the moved viewer leaves keep their target completion under the new noun",
        ),
        (
            "a viewer leaf name under the reading noun",
            ["aw", "runs", "st"],
            2,
            (("contains", ("status",)),),
            "the nine moved leaves must be REACHABLE by completion under their new noun at all",
        ),
        (
            "a release selector slot",
            ["aw", "releases", "show", ""],
            3,
            (("contains", ("rel111", "7.0.0", "next")),),
            "w0ln4q E-04: releases complete from the records on disk by BOTH id6 and Version, plus "
            "the `next` sentinel. Asserted here so a refactor of this engine cannot silently drop "
            "the release branch",
        ),
        (
            "a release selector prefix",
            ["aw", "releases", "show", "rel"],
            3,
            (("equals", ["rel111"]),),
            "the prefix filter narrows to the id6 and drops the Version spelling",
        ),
        (
            "plan statuses in a status slot",
            ["aw", "ipd", "set", "a"],
            3,
            (("equals", ["approved", "auto-approved"]),),
            "plan statuses come from `ipd_schema`; pinned exactly because the CLI status arguments "
            "are free-form `nargs='+'` with no argparse `choices` to fall back on",
        ),
        (
            "spec statuses in a status slot",
            ["aw", "specs", "set", "abc123", "--status", "i"],
            5,
            (("contains", ("implementing", "implemented")),),
            "the spec vocabulary is its OWN enum; these two i-statuses exist for specs only",
        ),
        (
            "plan statuses at the same prefix specs answer to",
            ["aw", "ipd", "set", "i"],
            3,
            (("excludes", ("implementing", "implemented")),),
            "the negative half of the row above: the per-type vocabularies must actually DIFFER, "
            "not merely both contain the right answers",
        ),
        (
            "backlog statuses in a status slot",
            ["aw", "backlog", "set", "def456", "--status", ""],
            5,
            (("contains", ("graduated",)),),
            "v58bvy E-01: `graduated` joined the vocabulary and a hardcoded list went stale; the "
            "full set is asserted against `backlog.STATUSES` itself in its own test below",
        ),
        (
            "a prefix matching nothing",
            ["aw", "ipd", "lint", "zzzzzz"],
            3,
            (("equals", []),),
            "no candidates is a normal answer, not an error: the shell must get an empty list",
        ),
    )

    def _check(self, got, mode, value):
        """Return a failure description for one check, or None when it holds."""
        if mode == "equals":
            return None if got == value else f"expected EXACTLY {value!r}, got {got!r}"
        if mode == "contains":
            missing = [v for v in value if v not in got]
            return None if not missing else f"missing {missing!r} from {got!r}"
        if mode == "excludes":
            present = [v for v in value if v in got]
            return None if not present else f"must NOT offer {present!r}, got {got!r}"
        if mode == "all_start_with":
            bad = [c for c in got if not c.startswith(value)]
            return (
                None
                if not bad
                else f"every candidate must start with {value!r}; these do not: {bad!r}"
            )
        raise AssertionError(f"unknown check mode {mode!r} in the table")

    def test_every_position_offers_its_candidate_vocabulary(self) -> None:
        wrong = []
        for case, tokens, cword, checks, why in self.QUERIES:
            got = completion.complete_query(tokens, cword, self.root)
            problems = [
                msg
                for mode, value in checks
                if (msg := self._check(got, mode, value)) is not None
            ]
            if problems:
                wrong.append(
                    f"  {case} (tokens={tokens!r}, cword={cword}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"completion.complete_query answered {len(wrong)} of {len(self.QUERIES)} positions "
            "wrongly. ONE dispatch in `complete_query` routes a position to its vocabulary, so "
            "several rows failing together usually means that routing changed rather than several "
            "vocabularies breaking independently. FIX: group the failures before editing anything. "
            "All ARTIFACT rows failing points at the scan scoping or the records backend; all "
            "STATUS rows failing points at the vocabulary modules (`ipd_schema`, "
            "`attention_contract`, `backlog`); a mix of `run`/`runs` rows points at the noun split; "
            "a lone row is a genuine single-branch bug. Note an `excludes` row can only fail by "
            "offering something the parser REJECTS, which is worse than offering too little.\n"
            + "\n".join(wrong),
        )

    def test_the_release_argparse_alias_resolves_identically(self) -> None:
        """Kept separate: compares TWO queries to each other, so it has no single expected list.

        A row could pin both spellings to the same literal, but that would pass if both drifted the
        same way; asserting EQUALITY of the two answers is the actual claim.
        """
        canonical = completion.complete_query(
            ["aw", "releases", "show", ""], 3, self.root
        )
        alias = completion.complete_query(["aw", "release", "show", ""], 3, self.root)
        self.assertEqual(
            sorted(alias),
            sorted(canonical),
            "the `release` argparse alias must complete identically to `releases`; "
            f"alias gave {sorted(alias)!r} and canonical gave {sorted(canonical)!r}",
        )

    def test_the_spec_and_plan_status_vocabularies_are_not_the_same_set(self) -> None:
        """Kept separate: a set-INEQUALITY between two queries, not a claim about one list.

        The table above carries the positive and negative halves (specs offer the i-statuses, plans
        do not). This adds the claim neither row can make alone: the two vocabularies are genuinely
        different sets, so a future refactor cannot satisfy both rows by merging them.
        """
        spec_got = completion.complete_query(
            ["aw", "specs", "set", "abc123", "--status", "i"], 5, self.root
        )
        plan_got = completion.complete_query(["aw", "ipd", "set", "i"], 3, self.root)
        self.assertNotEqual(
            set(spec_got),
            set(plan_got),
            "the per-type status vocabularies must DIFFER; both returned "
            f"{sorted(spec_got)!r}",
        )

    def test_backlog_statuses_come_from_the_source_of_truth(self) -> None:
        """Kept separate: asserts against a live module constant, not a literal row.

        bklgrad Order 01 (v58bvy) E-01: a hardcoded list here went stale the moment `graduated`
        joined the vocabulary. Completion derives from `backlog.STATUSES` (completion.py:509), so
        the assertion has to name that constant rather than any list a table row could hold.
        """
        from agent_workflows import backlog as _backlog

        got = completion.complete_query(
            ["aw", "backlog", "set", "def456", "--status", ""], 5, self.root
        )
        self.assertEqual(
            sorted(got),
            sorted(_backlog.STATUSES),
            "backlog status completion must offer exactly `backlog.STATUSES`; got "
            f"{sorted(got)!r} against {sorted(_backlog.STATUSES)!r}",
        )


class RunIdCandidateTests(_DynamicRepoFixture):
    """`run_id_candidates` directly, NOT through `complete_query`.

    These two are deliberately not rows in the position table above. Each needs materially
    different SETUP (one creates extra sibling directories mid-test; the other builds a whole
    second repo with a companion `records_backend` config), and each calls a different function
    than the table's subject. Folding them in would make every other row carry that machinery.
    """

    def test_run_id_candidates_excludes_analytics_and_non_run_dirs(self) -> None:
        """Kept separate: creates extra sibling directories the other rows must not see."""
        rec = self.root / ".aw" / "records"
        (rec / "runs" / "analytics" / "snapshots" / "run-snapshot").mkdir(parents=True)
        (rec / "runs" / "analytics").mkdir(parents=True, exist_ok=True)
        (rec / "runs" / "not-a-run").mkdir(parents=True, exist_ok=True)
        got = completion.run_id_candidates(self.root)
        self.assertIn("run-20260829T000000Z-1", got)
        self.assertNotIn("analytics", got)
        self.assertNotIn("not-a-run", got)
        self.assertNotIn("run-snapshot", got)

    def test_run_id_candidates_relocated_records_backend(self) -> None:
        """Kept separate: builds a SECOND repo with a companion `records_backend` config."""
        with tempfile.TemporaryDirectory() as alt_tmp:
            alt_root = Path(alt_tmp)
            (alt_root / ".aw" / "config").mkdir(parents=True)
            companion_dir = alt_root / "custom_companion"
            custom_runs = companion_dir / "records" / "runs"
            (custom_runs / "run-20260901T120000Z-9").mkdir(parents=True)
            (custom_runs / "analytics").mkdir(parents=True)
            (alt_root / ".aw" / "config" / "project.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "project_id": "testproj",
                        "records_backend": "companion",
                    }
                ),
                encoding="utf-8",
            )
            (alt_root / ".aw" / "config" / "local.json").write_text(
                json.dumps(
                    {
                        "companion_dir": str(companion_dir),
                    }
                ),
                encoding="utf-8",
            )
            got = completion.run_id_candidates(alt_root)
            self.assertIn("run-20260901T120000Z-9", got)
            self.assertNotIn("analytics", got)


class CompleteQueryLatencyTests(_DynamicRepoFixture):
    def test_representative_query_within_budget(self) -> None:
        """Kept separate: a TIMING assertion, not a value mapping; it needs the best-of-N loop."""
        # Latency assertion. The <50ms interactive budget is the design target; the parser-build cost
        # dominates the subcommand path, so we assert a generous CI-safe upper bound (250ms) to avoid
        # a flaky test on a slow/loaded runner while still catching a pathological regression (the
        # unscoped full-history resolver sweep measured ~500ms). Artifact queries are far faster.
        best = min(
            (
                _timed(
                    lambda: completion.complete_query(
                        ["aw", "ipd", "lint", "b"], 3, self.root
                    )
                )
                for _ in range(3)
            )
        )
        self.assertLess(best, 0.25, f"complete_query too slow: {best * 1000:.1f}ms")


def _timed(fn) -> float:
    t = time.perf_counter()
    fn()
    return time.perf_counter() - t


class DunderCompleteProtocolTests(_DynamicRepoFixture):
    """E-02: `aw __complete --cword N -- <tokens>` is the WIRE PROTOCOL over `complete_query`.

    Four tests became one table. All four did the same thing: run the hidden subcommand, assert
    exit 0, and compare the printed lines to a small expectation. The distinction between them was
    which token stream they passed.

    Why the table beats the four: every row funnels through ONE handler
    (`cli._run_dunder_complete`), whose whole job is to marshal argv into a `complete_query` call
    and print the result one candidate per line. The realistic failure is in that marshalling (the
    `--cword` offset, the `--` separator handling, or the printing), and it breaks EVERY row at once
    while leaving `complete_query` itself perfectly healthy. Four tests report that as four red
    lines; the table reports one failure showing every token stream and what came back, which is
    what distinguishes a marshalling bug from a vocabulary bug.

    Each row asserts BOTH things the old tests asserted, because they are not the same claim and
    the difference is the whole point of this class: the exit code must be 0 (a non-zero exit makes
    a shell BEEP at the user even when candidates were printed), AND the printed lines must equal
    what `complete_query` returns for the identical input, which is the protocol's only real
    contract. `expected_exact` additionally pins the literal for rows where the value itself
    matters, so a bug that made BOTH sides return the same wrong answer still fails here.
    """

    #: (case, cword, tokens, expected exact lines or None to only cross-check, why)
    WIRE_CASES = (
        (
            "a subcommand prefix",
            1,
            ["aw", "ru"],
            None,
            "the base case: command position over the wire. Not pinned exactly because the real "
            "command set grows; the cross-check against complete_query is the assertion",
        ),
        (
            "an artifact position",
            3,
            ["aw", "ipd", "lint", "b"],
            ["bja8og"],
            "pinned exactly: the wire must carry a BARE id6, since a path would be inserted "
            "verbatim into the user's command line",
        ),
        (
            "a leading-dash token",
            2,
            ["aw", "ipd", "--js"],
            ["--json"],
            "the `--` separator means an option-like token in the COMPLETED LINE is DATA; without "
            "it argparse would eat `--js` as a flag of `__complete` itself",
        ),
        (
            "a prefix matching nothing",
            3,
            ["aw", "ipd", "lint", "zzzzzz"],
            [],
            "no candidates must still exit 0: a non-zero exit makes the shell beep and look broken",
        ),
    )

    def _complete(self, cword, tokens):
        out = io.StringIO()
        cwd = os.getcwd()
        os.chdir(self.root)
        try:
            with redirect_stdout(out):
                rc = cli.main(["__complete", "--cword", str(cword), "--", *tokens])
        finally:
            os.chdir(cwd)
        lines = [line for line in out.getvalue().splitlines() if line]
        return rc, lines

    def test_the_wire_protocol_matches_complete_query_and_always_exits_zero(
        self,
    ) -> None:
        wrong = []
        for case, cword, tokens, expected_exact, why in self.WIRE_CASES:
            rc, lines = self._complete(cword, tokens)
            expected = completion.complete_query(tokens, cword, self.root)
            problems = []
            if rc != 0:
                problems.append(f"exit code expected 0, got {rc}")
            if lines != expected:
                problems.append(
                    f"printed {lines!r} but complete_query returned {expected!r}"
                )
            if expected_exact is not None and lines != expected_exact:
                problems.append(f"expected exactly {expected_exact!r}, got {lines!r}")
            if problems:
                wrong.append(
                    f"  {case} (cword={cword}, tokens={tokens!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`aw __complete` broke the wire protocol on {len(wrong)} of {len(self.WIRE_CASES)} "
            "token streams. One handler (`cli._run_dunder_complete`) marshals argv into "
            "`complete_query` and prints its result, so ALL rows failing together means the "
            "marshalling broke (a `--cword` off-by-one, the `--` separator, or the printing) "
            "rather than any vocabulary changing. FIX: when a row's printed lines DISAGREE with "
            "complete_query, the bug is in the handler; when they AGREE but the exact expectation "
            "fails, the bug is in `complete_query` and the position table above should be failing "
            f"too.\n" + "\n".join(wrong),
        )


class ArgcompleteSoftImportTests(unittest.TestCase):
    """E-03: the argcomplete marker + soft import."""

    def test_marker_is_real_comment_within_1024_bytes(self) -> None:
        src = Path(cli.__file__).read_text(encoding="utf-8")
        idx = src.find("# PYTHON_ARGCOMPLETE_OK")
        self.assertNotEqual(idx, -1, "marker missing")
        self.assertLess(idx, 1024, "marker must be within the first 1024 bytes")
        # It must be a real `#` comment, NOT inside the module docstring (which closes earlier).
        docstring_end = src.find('"""', 3) + 3
        self.assertGreater(
            idx,
            docstring_end,
            "marker must be a comment AFTER the docstring, not inside it",
        )

    def test_cli_imports_and_runs_without_argcomplete(self) -> None:
        # argcomplete is optional; simulate its absence and prove main() still runs cleanly.
        import builtins

        real_import = builtins.__import__

        def _no_argcomplete(name, *a, **k):
            if name == "argcomplete" or name.startswith("argcomplete."):
                raise ImportError("simulated: argcomplete not installed")
            return real_import(name, *a, **k)

        # Use a command that RETURNS (not one like `--version` that argparse turns into sys.exit).
        with mock.patch.object(builtins, "__import__", _no_argcomplete):
            rc, out = _run(["completion", "bash"])
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("# bash completion for aw"))

    def test_maybe_argcomplete_is_noop_when_absent(self) -> None:
        # Directly exercise the hook: with argcomplete unimportable it must return without error.
        import builtins

        real_import = builtins.__import__

        def _no_argcomplete(name, *a, **k):
            if name == "argcomplete" or name.startswith("argcomplete."):
                raise ImportError("simulated")
            return real_import(name, *a, **k)

        parser = cli._build_parser()
        with mock.patch.object(builtins, "__import__", _no_argcomplete):
            cli._maybe_argcomplete(parser)  # must not raise


# --------------------------------------------------------------------------------------
# tabcomp Order 03 (jolfpj): drop-in auto-discovery installation.
# --------------------------------------------------------------------------------------


class _DropInFixture(unittest.TestCase):
    """A REAL temp HOME + XDG bases (not a mock), so `mkdir(parents=True)`, symlink creation, and
    the dotfile-untouched assertion exercise actual filesystem behavior."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.xdg_data = self.root / "xdg-data"
        self.xdg_config = self.root / "xdg-config"
        self._env = mock.patch.dict(
            os.environ,
            {
                "HOME": str(self.home),
                "XDG_DATA_HOME": str(self.xdg_data),
                "XDG_CONFIG_HOME": str(self.xdg_config),
            },
        )
        self._env.start()
        self.addCleanup(self._env.stop)
        self.addCleanup(self._tmp.cleanup)

    def dotfile_paths(self):
        return [
            self.home / ".bashrc",
            self.home / ".bash_profile",
            self.home / ".zshrc",
            self.home / ".profile",
            self.xdg_config / "fish" / "config.fish",
        ]

    def assert_no_dotfile_touched(self) -> None:
        """The CORE PROMISE: no user rc/dotfile is ever created or modified."""
        for path in self.dotfile_paths():
            self.assertFalse(
                path.exists(),
                f"{path} must never be created or modified by completion install/uninstall",
            )


class ResolveCompletionDirTests(_DropInFixture):
    """E-01: which directory each shell's drop-in goes in, XDG-first with HOME fallbacks.

    Three tests became ONE table with a MODE COLUMN. The three were not pure data variants of each
    other, which is exactly why the mode is a column rather than the basis for three tables: one
    ran with the XDG env vars SET, one with them UNSET, and one passed an explicit `custom_dir`.
    Same function, same single assertion, three environment modes, so each row declares its mode
    and the six shell/mode combinations sit in one place.

    Why the table beats the three: `resolve_completion_dir` is a pure function from (shell, env) to
    a path, and its six answers come from ONE precedence rule (explicit dir, else the XDG var, else
    the HOME default) crossed with a per-shell subdirectory. The realistic failure is the precedence
    changing, and it moves every row of a mode together: an XDG var that stops being consulted makes
    all three `xdg` rows point into `$HOME` at once. Three tests report that as one red line naming
    only the FIRST shell (each old test had three sequential `assertEqual`s, so the second and third
    never ran), and the table reports all six rows with the paths they actually resolved to.

    `fish` sits under `XDG_CONFIG_HOME` while `bash` and `zsh` sit under `XDG_DATA_HOME`, which
    looks inconsistent and is not: those are the directories each shell actually auto-discovers.
    Keeping all three in one table is what makes that visible as a deliberate per-shell fact.
    """

    #: (shell, mode, why this row exists). Mode is "xdg" (env vars set), "home" (env vars unset),
    #: or "custom" (an explicit custom_dir, which must win over both).
    DIRECTORIES = (
        (
            "bash",
            "xdg",
            "bash-completion's own XDG-aware search path lives under XDG_DATA_HOME",
        ),
        ("zsh", "xdg", "zsh site-functions is a DATA dir, not a config dir"),
        (
            "fish",
            "xdg",
            "fish is the odd one out on purpose: it discovers completions under "
            "XDG_CONFIG_HOME, so following the same var as the others would put the file "
            "somewhere fish never looks",
        ),
        (
            "bash",
            "home",
            "with no XDG var, fall back to the ~/.local/share default that var stands in for",
        ),
        ("zsh", "home", "same fallback base for the other data-dir shell"),
        (
            "fish",
            "home",
            "fish's fallback is ~/.config, matching its config-dir home rather than sharing "
            "the data-dir fallback",
        ),
        (
            "bash",
            "custom",
            "an explicit --dir overrides EVERYTHING, including a set XDG var, and is used "
            "verbatim without a per-shell subdirectory appended",
        ),
    )

    def _expected(self, shell, mode, custom):
        if mode == "custom":
            return custom
        if mode == "xdg":
            return {
                "bash": self.xdg_data / "bash-completion/completions",
                "zsh": self.xdg_data / "zsh/site-functions",
                "fish": self.xdg_config / "fish/completions",
            }[shell]
        return {
            "bash": self.home / ".local/share/bash-completion/completions",
            "zsh": self.home / ".local/share/zsh/site-functions",
            "fish": self.home / ".config/fish/completions",
        }[shell]

    def test_every_shell_resolves_to_its_directory_in_every_mode(self) -> None:
        custom = self.root / "elsewhere"
        wrong = []
        for shell, mode, why in self.DIRECTORIES:
            expected = self._expected(shell, mode, custom)
            with mock.patch.dict(os.environ, {}, clear=False):
                if mode == "home":
                    os.environ.pop("XDG_DATA_HOME", None)
                    os.environ.pop("XDG_CONFIG_HOME", None)
                got = completion.resolve_completion_dir(
                    shell, **({"custom_dir": custom} if mode == "custom" else {})
                )
            if got != expected:
                wrong.append(
                    f"  {shell} in {mode!r} mode:\n    expected {expected}\n    got      {got}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"completion.resolve_completion_dir returned the wrong directory for {len(wrong)} of "
            f"{len(self.DIRECTORIES)} shell/mode combinations. One precedence rule (explicit dir, "
            "else the XDG var, else the HOME default) crossed with a per-shell subdirectory "
            "produces all of these, so failures cluster by MODE when the precedence changed and by "
            "SHELL when a subdirectory changed. FIX: every `xdg` row landing under $HOME means the "
            "env vars stopped being consulted; every `home` row landing under the XDG base means "
            "the fallback is reading a var that should be unset; the `custom` row failing means "
            "--dir is no longer absolute and a user's explicit path is being rewritten. A wrong "
            "directory installs a file the shell never discovers, which looks to the user exactly "
            f"like completion being broken.\n" + "\n".join(wrong),
        )

    def test_unsupported_shell_raises(self) -> None:
        """Kept separate: asserts a RAISE, which is structurally not a returned-path row."""
        with self.assertRaises(completion.CompletionInstallError):
            completion.resolve_completion_dir("tcsh")

    def test_xdg_precedence_matches_config_module(self) -> None:
        """Kept separate: cross-checks against ANOTHER module (`config.config_dir`), so its
        expectation is a live value rather than a literal a row could hold."""
        # The convention must be the SAME one config.config_dir uses (XDG env var, else ~/.config),
        # not a second invented one.
        from agent_workflows import config as _config

        self.assertEqual(_config.config_dir().parent, self.xdg_config)
        self.assertEqual(
            completion.resolve_completion_dir("fish").parent.parent, self.xdg_config
        )


class InstallShellCompletionTests(_DropInFixture):
    """E-01: drop-in writes, per-shell alias binding, sentinel, idempotency, no-clobber, uninstall."""

    #: What a clean install of each shell must leave on disk.
    #: (shell, dir attribute + relative dir, the COMPLETE set of entry names, expected symlinks as
    #:  {name: target}, substrings required in the primary file, why this row exists)
    INSTALL_LAYOUTS = (
        (
            "bash",
            ("xdg_data", "bash-completion/completions"),
            {"aw", "agentwf", "agent-workflows"},
            {"agentwf": "aw", "agent-workflows": "aw"},
            (),
            "BASH dispatches completion BY COMMAND NAME, so each alias needs its own entry; they "
            "are RELATIVE symlinks to `aw` so the set survives the directory being moved",
        ),
        (
            "zsh",
            ("xdg_data", "zsh/site-functions"),
            {"_aw"},
            {},
            ("#compdef aw agentwf agent-workflows",),
            "ZSH binds all three aliases from the ONE file's `#compdef` line, so per-alias files "
            "must NOT exist. That is WRONG rather than merely redundant: a second file in "
            "site-functions is a second completion definition zsh may load instead",
        ),
        (
            "fish",
            ("xdg_config", "fish/completions"),
            {"aw.fish"},
            {},
            (
                "complete -c aw ",
                "complete -c agentwf ",
                "complete -c agent-workflows ",
            ),
            "FISH binds each alias from its own `complete -c` line INSIDE the single file, so the "
            "alias coverage is a content claim here where for bash it is a filesystem claim",
        ),
    )

    def test_every_shell_install_leaves_its_exact_drop_in_layout(self) -> None:
        """One table over the three per-shell layouts, the sentinel, and the no-dotfile promise.

        Four tests became this one. Each installed ONE shell and then asserted that shell's layout;
        the fourth looped the three shells asserting only the sentinel. They are one subject: what
        `install_shell_completion` leaves on disk.

        The table is better than the four for a reason this subject makes sharp. The three layouts
        are DELIBERATELY DIFFERENT (bash needs a file per command name, zsh needs exactly one
        `#compdef`-bound file, fish needs one file containing a `complete -c` per name), and the
        thing most likely to break them is shared: the alias list, the sentinel writer, or the
        directory resolver. A regression there breaks all three at once but in three different
        shapes, and four tests report that as four red lines with no hint they share a cause. This
        reports one failure listing every shell whose layout moved, with the entries it actually
        found. Asserting the COMPLETE entry set rather than per-file existence is also strictly
        stronger than the old tests were for bash: an extra stray file now fails.
        """
        wrong = []
        for shell, (
            base_attr,
            rel,
        ), entries, symlinks, needles, why in self.INSTALL_LAYOUTS:
            directory = getattr(self, base_attr) / rel
            result = completion.install_shell_completion(shell)
            problems = []
            if result["dir"] != directory:
                problems.append(
                    f"reported dir {result['dir']} but expected {directory}"
                )
            if not directory.is_dir():
                problems.append(f"{directory} was not created at all")
                wrong.append(
                    f"  {shell}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
                continue
            found = {p.name for p in directory.iterdir()}
            if found != entries:
                problems.append(
                    f"expected exactly the entries {sorted(entries)}, found {sorted(found)}"
                )
            primary = result["paths"][0]
            if not primary.is_file():
                problems.append(
                    f"the primary file {primary.name} is not a regular file"
                )
            else:
                head = primary.read_text(encoding="utf-8").split("\n")[:3]
                if completion.INSTALL_SENTINEL not in head:
                    problems.append(
                        f"INSTALL_SENTINEL is not in the first 3 lines of {primary.name}; "
                        f"got {head!r}. Uninstall identifies OUR files by that sentinel, so "
                        "without it this install can never be cleanly removed"
                    )
                body = primary.read_text(encoding="utf-8")
                missing = [n for n in needles if n not in body]
                if missing:
                    problems.append(f"{primary.name} is missing {missing!r}")
            for name, target in symlinks.items():
                link = directory / name
                if not link.exists():
                    problems.append(f"the alias entry {name!r} was not created")
                elif not link.is_symlink():
                    problems.append(f"{name!r} exists but is not a symlink")
                elif os.readlink(link) != target:
                    problems.append(
                        f"{name!r} points at {os.readlink(link)!r}, expected {target!r}"
                    )
            touched = [p for p in self.dotfile_paths() if p.exists()]
            if touched:
                problems.append(
                    f"THE CORE PROMISE IS BROKEN: installing {shell} created or modified "
                    f"{touched!r}"
                )
            if problems:
                wrong.append(
                    f"  {shell} (into {directory}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"completion.install_shell_completion wrote the wrong layout for {len(wrong)} of "
            f"{len(self.INSTALL_LAYOUTS)} shells. The three layouts differ on purpose, but they "
            "share the alias list (`completion.ENTRYPOINTS`), the sentinel writer, and the "
            "directory resolver, so all three failing together points at one of those rather than "
            "at three per-shell bugs. FIX: an alias missing from bash's entry set AND from fish's "
            "file content is an ENTRYPOINTS change; a missing sentinel across shells is the header "
            "writer, and it makes uninstall unable to recognize its own files; an unexpected EXTRA "
            "entry under zsh means per-alias files are being created for a shell that binds them "
            f"from one file.\n" + "\n".join(wrong),
        )

    def test_zsh_sentinel_does_not_displace_compdef_first_line(self) -> None:
        """Kept separate: an ORDERING claim between two lines, which no layout row expresses.

        The table above asserts the sentinel is within the first three lines and that `#compdef` is
        present. Neither implies the sentinel sits BELOW `#compdef`, and for zsh that ordering is
        functional: compinit honors `#compdef` on line 1 only, so a sentinel written above it
        silently disables completion while every other assertion still passes.
        """
        # zsh's compinit only honors `#compdef` on line 1, so the sentinel must go BELOW it.
        result = completion.install_shell_completion("zsh")
        lines = result["paths"][0].read_text(encoding="utf-8").split("\n")
        self.assertTrue(lines[0].startswith("#compdef"))
        self.assertEqual(lines[1], completion.INSTALL_SENTINEL)

    def test_creates_missing_parent_directories(self) -> None:
        """Kept separate: asserts the directory did NOT exist before the call, so the claim is about a
        state transition rather than the post-install layout the table pins."""
        # OQ-01: mkdir(parents=True) so a fresh machine with no completion dir works.
        directory = self.xdg_data / "bash-completion/completions"
        self.assertFalse(directory.exists())
        completion.install_shell_completion("bash")
        self.assertTrue(directory.is_dir())

    def test_install_is_idempotent(self) -> None:
        """Kept separate: a BEFORE/AFTER comparison of two installs, not a single-input row.

        The claim is that the SECOND install produces byte-identical results to the first, which
        needs two observations with the first one's output as the expectation. A table row holds one
        expected value and cannot express "the same as whatever the previous call produced".
        """
        first = completion.install_shell_completion("bash")
        body = first["paths"][0].read_text(encoding="utf-8")
        second = completion.install_shell_completion("bash")
        self.assertEqual(second["paths"], first["paths"])
        self.assertEqual(second["paths"][0].read_text(encoding="utf-8"), body)
        self.assertTrue(completion.is_completion_installed("bash"))

    # The three refusal tests below stay as their own tests: each asserts a RAISE
    # (`assertRaises(CompletionInstallError)`) rather than a returned value, and each needs its own
    # hostile pre-existing directory state (a foreign primary, a foreign ALIAS entry, a symlink
    # pointing outside). Their real content is also not the exception but the "and nothing was
    # written" claim that follows it, which differs per row: one checks the foreign bytes survived,
    # one checks the primary was never created, one checks we did not write THROUGH a link. The
    # CLI-level exit-code-1 translation of this same refusal IS tabulated, in
    # `CompletionInstallCliTests.CLI_CASES`.

    def test_refuses_to_clobber_foreign_completion(self) -> None:
        """Kept separate: asserts a RAISE plus that the foreign file's bytes are unchanged."""
        directory = self.xdg_data / "bash-completion/completions"
        directory.mkdir(parents=True)
        foreign = directory / "aw"
        foreign.write_text("# someone else's aw completion\n", encoding="utf-8")
        with self.assertRaises(completion.CompletionInstallError):
            completion.install_shell_completion("bash")
        # The foreign file is left EXACTLY as it was, and no alias links were created.
        self.assertEqual(
            foreign.read_text(encoding="utf-8"), "# someone else's aw completion\n"
        )
        self.assertFalse((directory / "agentwf").exists())

    def test_refuses_when_a_foreign_alias_file_exists(self) -> None:
        """Kept separate: asserts a RAISE, and that it FAILS CLOSED before any write.

        A foreign ALIAS entry (not the primary) must abort the whole install, so the distinctive
        claim is that the primary `aw` was never created at all.
        """
        directory = self.xdg_data / "bash-completion/completions"
        directory.mkdir(parents=True)
        (directory / "agentwf").write_text("# foreign alias\n", encoding="utf-8")
        with self.assertRaises(completion.CompletionInstallError):
            completion.install_shell_completion("bash")
        self.assertFalse((directory / "aw").exists())

    def test_dry_run_writes_nothing(self) -> None:
        """Kept separate: asserts over the RETURNED result dict (`dry_run`, `paths`), not a layout.

        The layout table above asserts what a real install leaves on disk. This asserts the
        preview's own contract: the flag is echoed back, a non-empty path list is still reported,
        and none of those paths exist. That is a claim about the return value, not the filesystem
        state a row expresses.
        """
        result = completion.install_shell_completion("bash", dry_run=True)
        self.assertTrue(result["dry_run"])
        self.assertTrue(result["paths"])
        for path in result["paths"]:
            self.assertFalse(path.exists())
        self.assertFalse((self.xdg_data / "bash-completion").exists())

    def test_symlink_to_unexpected_target_is_treated_as_foreign(self) -> None:
        """Kept separate: asserts a RAISE, and that we did not write THROUGH the symlink.

        Needs its own setup (a symlink whose target lives OUTSIDE the completion directory), and the
        assertion that matters is about the target file's bytes, which no other row touches.
        """
        directory = self.xdg_data / "bash-completion/completions"
        directory.mkdir(parents=True)
        outside = self.root / "outside.bash"
        outside.write_text("# not ours\n", encoding="utf-8")
        (directory / "aw").symlink_to(outside)
        with self.assertRaises(completion.CompletionInstallError):
            completion.install_shell_completion("bash")
        # We must NOT have written THROUGH the link into the unexpected target.
        self.assertEqual(outside.read_text(encoding="utf-8"), "# not ours\n")


class UninstallShellCompletionTests(_DropInFixture):
    """E-01: uninstall removes ONLY tool-created files, and reports what it refused to touch.

    Four tests became ONE table, because each set up a directory state, called
    `uninstall_shell_completion`, and asserted the returned `removed`/`skipped` lists plus what
    survived on disk. Only the starting state differed, and `dry_run` is a MODE COLUMN rather than
    a separate table: a dry run must report the SAME `removed` list as a real run while changing
    nothing, so the two modes belong side by side where that correspondence is visible.

    Why the table beats the four: every row exercises ONE decision made per file, namely "does this
    carry `INSTALL_SENTINEL`?", which sorts it into `removed` or `skipped`. The realistic failure is
    that check breaking, and it is DANGEROUS in one direction: a sentinel check that starts matching
    everything turns uninstall into a deleter of other tools' completion files. That regression
    flips the foreign rows and the ours rows together, which is one failure with a shared cause, and
    the table says so in one message instead of two unrelated red lines.

    Each row asserts THREE things the old tests kept separate, because they are genuinely different
    claims: the `removed` list (what it says it deleted), the `skipped` list (what it says it
    REFUSED, which is the part that makes a refusal visible to the user rather than silent), and
    `surviving`, the complete set of names left in the directory, which is the only one that
    actually proves nothing extra was destroyed.
    """

    #: (case, install these shells first, extra files to plant as {name: text}, shell to uninstall,
    #:  dry_run, expected removed names, expected skipped names, expected surviving names, why)
    UNINSTALL_CASES = (
        (
            "our install beside a foreign sibling",
            ("bash",),
            {"other-tool": "# foreign\n"},
            "bash",
            False,
            ["agent-workflows", "agentwf", "aw"],
            [],
            {"other-tool"},
            "the primary AND both alias links go, while another tool's unrelated completion file "
            "in the same shared directory must survive untouched",
        ),
        (
            "a foreign file under OUR name",
            (),
            {"aw": "# foreign aw completion\n"},
            "bash",
            False,
            [],
            ["aw"],
            {"aw"},
            "a file at our path without our sentinel is somebody else's; it must be REPORTED as "
            "skipped rather than silently deleted or silently ignored",
        ),
        (
            "nothing installed at all",
            (),
            {},
            "fish",
            False,
            [],
            [],
            set(),
            "uninstalling what was never installed is a NO-OP, not an error: `aw completion "
            "uninstall` must be safe to run twice",
        ),
        (
            "a dry run over our own install",
            ("zsh",),
            {},
            "zsh",
            True,
            ["_aw"],
            [],
            {"_aw"},
            "a dry run must report exactly what a real run WOULD remove while leaving the file in "
            "place; reporting nothing would make the preview useless",
        ),
    )

    def test_every_directory_state_removes_only_our_files(self) -> None:
        wrong = []
        for (
            case,
            preinstall,
            planted,
            shell,
            dry_run,
            expected_removed,
            expected_skipped,
            surviving,
            why,
        ) in self.UNINSTALL_CASES:
            # Each row needs its own clean HOME/XDG bases.
            row_root = Path(tempfile.mkdtemp(dir=self.root))
            self.xdg_data = row_root / "xdg-data"
            self.xdg_config = row_root / "xdg-config"
            self.home = row_root / "home"
            self.home.mkdir()
            with mock.patch.dict(
                os.environ,
                {
                    "HOME": str(self.home),
                    "XDG_DATA_HOME": str(self.xdg_data),
                    "XDG_CONFIG_HOME": str(self.xdg_config),
                },
            ):
                for other in preinstall:
                    completion.install_shell_completion(other)
                directory = completion.resolve_completion_dir(shell)
                directory.mkdir(parents=True, exist_ok=True)
                for name, text in planted.items():
                    (directory / name).write_text(text, encoding="utf-8")
                result = completion.uninstall_shell_completion(shell, dry_run=dry_run)
                got_removed = sorted(p.name for p in result["removed"])
                got_skipped = sorted(p.name for p in result["skipped"])
                found = {p.name for p in directory.iterdir()}
                still_installed = completion.is_completion_installed(shell)
                touched = [p for p in self.dotfile_paths() if p.exists()]

            problems = []
            if got_removed != sorted(expected_removed):
                problems.append(
                    f"reported removed {got_removed} but expected {sorted(expected_removed)}"
                )
            if got_skipped != sorted(expected_skipped):
                problems.append(
                    f"reported skipped {got_skipped} but expected {sorted(expected_skipped)}"
                )
            if found != surviving:
                problems.append(
                    f"the directory holds {sorted(found)} but should hold {sorted(surviving)}"
                )
            # A real uninstall of our own files must clear the installed flag; a dry run must not.
            expected_installed = dry_run and bool(preinstall)
            if still_installed != expected_installed:
                problems.append(
                    f"is_completion_installed({shell!r}) returned {still_installed}, expected "
                    f"{expected_installed}"
                )
            if touched:
                problems.append(
                    f"THE CORE PROMISE IS BROKEN: it created or modified {touched!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (uninstall {shell}, dry_run={dry_run}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"completion.uninstall_shell_completion mishandled {len(wrong)} of "
            f"{len(self.UNINSTALL_CASES)} directory states. One per-file decision (does it carry "
            "INSTALL_SENTINEL?) sorts every file into removed or skipped, so several rows moving "
            "together means that check changed. FIX: read the direction of the failure, because "
            "the two directions are not equally bad. A FOREIGN file appearing in `removed`, or "
            "vanishing from `surviving`, means uninstall is now deleting other tools' files, which "
            "is data loss on a user's machine and the worst outcome this table guards. Our own "
            "files appearing in `skipped` is merely an uninstall that leaves litter behind. A dry "
            f"run whose `surviving` set shrank is a preview that actually deleted.\n"
            + "\n".join(wrong),
        )

    def test_roundtrip_touches_no_dotfile(self) -> None:
        for shell in ("bash", "zsh", "fish"):
            completion.install_shell_completion(shell)
            completion.uninstall_shell_completion(shell)
        self.assert_no_dotfile_touched()


class CompletionInstallCliTests(_DropInFixture):
    """E-02: `aw completion install|uninstall` as the USER sees it: exit code, stdout, files.

    Five tests became ONE table. Each ran one `cli.main(["completion", ...])` invocation and
    asserted an exit code, sometimes a stdout substring, and what appeared on disk. The flags
    (`--shell`, `--dir`, `--dry-run`, or none at all) are the data.

    Why the table beats the five: this is the CLI SURFACE over the library functions tabulated
    above, and its own job is only argument marshalling plus reporting. The realistic failure is
    therefore shared across rows (the `--shell` default, the exit-code mapping, or the path
    reporting), and it moves several rows together while the library tables stay green. That
    combination is the diagnostic signal, and five tests destroy it by reporting five unrelated red
    lines.

    The REFUSAL row (a foreign file, which must exit 1) is deliberately in the same table as the
    success rows rather than kept apart, and it is not an `assertRaises` case: the CLI's contract is
    to translate the library's exception into a nonzero EXIT CODE and a message, which is a data row
    like any other. Keeping it here is what makes the exit-code column meaningful, since a table
    where every row expects 0 would pass against a CLI that can only ever return 0.

    `stdout_needles` preserves a claim the exit code cannot make: the command must PRINT the paths
    it wrote (or would write), because that output is how a user finds the file and how `--dry-run`
    is useful at all. `expected_files` is asserted as the COMPLETE set of files created anywhere
    under the row's HOME, which is stronger than the old per-path checks: a dry run that secretly
    wrote a different file now fails.
    """

    #: (case, argv, $SHELL, plant a foreign `aw` file first, expected exit code, stdout substrings,
    #:  the complete set of created file names, why this row exists)
    CLI_CASES = (
        (
            "install an explicit shell",
            ["completion", "install", "--shell", "bash"],
            "/usr/bin/bash",
            False,
            0,
            ("bash-completion/completions/aw",),
            {"aw", "agentwf", "agent-workflows"},
            "the base case, and it must PRINT the installed path: a file written somewhere the "
            "user cannot see is not a usable install",
        ),
        (
            "uninstall when nothing is installed",
            ["completion", "uninstall", "--shell", "bash"],
            "/usr/bin/bash",
            False,
            0,
            ("nothing to remove",),
            set(),
            "a no-op uninstall EXITS 0 and says so; exiting nonzero would make the idempotent "
            "`aw completion uninstall` look like a failure in any script that runs it",
        ),
        (
            "install with --dry-run",
            ["completion", "install", "--shell", "fish", "--dry-run"],
            "/usr/bin/bash",
            False,
            0,
            ("[dry-run]", "aw.fish"),
            set(),
            "a preview must NAME the file and create nothing; the `[dry-run]` marker is what tells "
            "the user this did not happen yet",
        ),
        (
            "install with --dir",
            ["completion", "install", "--shell", "zsh", "--dir", "<CUSTOM>"],
            "/usr/bin/bash",
            False,
            0,
            ("_aw",),
            {"_aw"},
            "--dir overrides the resolved directory even though $SHELL says bash and XDG is set",
        ),
        (
            "install with no --shell",
            ["completion", "install"],
            "/usr/bin/fish",
            False,
            0,
            ("aw.fish",),
            {"aw.fish"},
            "the shell DEFAULTS to `cli._detect_shell()`, so the install surface and the "
            "script-output surface agree about what shell the user is in",
        ),
        (
            "install over a foreign file",
            ["completion", "install", "--shell", "bash"],
            "/usr/bin/bash",
            True,
            1,
            ("refusing to overwrite",),
            {"aw"},
            "a refusal must EXIT 1 and explain itself, never overwrite silently. The one surviving "
            "file is the foreign one, unchanged, and no alias links were created alongside it",
        ),
    )

    def test_every_cli_invocation_reports_and_writes_what_it_should(self) -> None:
        wrong = []
        for (
            case,
            argv,
            shell_env,
            plant_foreign,
            expected_rc,
            needles,
            expected_files,
            why,
        ) in self.CLI_CASES:
            row_root = Path(tempfile.mkdtemp(dir=self.root))
            self.xdg_data = row_root / "xdg-data"
            self.xdg_config = row_root / "xdg-config"
            self.home = row_root / "home"
            self.home.mkdir()
            custom = row_root / "custom-dir"
            argv = [str(custom) if a == "<CUSTOM>" else a for a in argv]
            with mock.patch.dict(
                os.environ,
                {
                    "HOME": str(self.home),
                    "XDG_DATA_HOME": str(self.xdg_data),
                    "XDG_CONFIG_HOME": str(self.xdg_config),
                    "SHELL": shell_env,
                },
            ):
                if plant_foreign:
                    directory = self.xdg_data / "bash-completion/completions"
                    directory.mkdir(parents=True)
                    (directory / "aw").write_text("# foreign\n", encoding="utf-8")
                rc, out = _run(argv)
                created = {
                    p.name
                    for base in (self.xdg_data, self.xdg_config, custom)
                    if base.exists()
                    for p in base.rglob("*")
                    if p.is_file() or p.is_symlink()
                }
                foreign_body = (
                    (self.xdg_data / "bash-completion/completions/aw").read_text(
                        encoding="utf-8"
                    )
                    if plant_foreign
                    else None
                )
                touched = [p for p in self.dotfile_paths() if p.exists()]

            problems = []
            if rc != expected_rc:
                problems.append(f"exit code expected {expected_rc}, got {rc}")
            missing = [n for n in needles if n not in out]
            if missing:
                problems.append(
                    f"stdout is missing {missing!r}; it printed {out.strip()[:200]!r}"
                )
            if created != expected_files:
                problems.append(
                    f"expected the created files {sorted(expected_files) or 'none'}, "
                    f"got {sorted(created) or 'none'}"
                )
            if plant_foreign and foreign_body != "# foreign\n":
                problems.append(
                    f"the foreign file was MODIFIED; it now reads {foreign_body!r}"
                )
            if touched:
                problems.append(
                    f"THE CORE PROMISE IS BROKEN: it created or modified {touched!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (argv={argv!r}, $SHELL={shell_env!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`aw completion install|uninstall` mishandled {len(wrong)} of {len(self.CLI_CASES)} "
            "invocations. This layer only marshals flags and reports results, so several rows "
            "failing together usually means the marshalling or the reporting changed rather than "
            "the installer itself. FIX: check whether the library tables above are also failing. "
            "If they are GREEN and these are red, the bug is in `cli._run_completion_install`; if "
            "both are red, fix the library first. A stdout needle missing while the files are "
            "correct is a reporting regression, which is minor for install and total for "
            f"`--dry-run`, whose entire output IS the feature.\n" + "\n".join(wrong),
        )

    def test_child01_script_output_still_works(self) -> None:
        # REGRESSION GUARD: adding the install/uninstall verbs must EXTEND child 01's parser, not
        # redesign it - `aw completion <shell>` must still stream the raw script to stdout.
        for shell, needle in (
            ("bash", "# bash completion for aw"),
            ("zsh", "#compdef aw agentwf agent-workflows"),
            ("fish", "complete -c aw "),
        ):
            rc, out = _run(["completion", shell])
            self.assertEqual(rc, 0, shell)
            self.assertIn(needle, out)
        # And bare `aw completion` still detects the shell rather than being read as a verb.
        with mock.patch.dict(os.environ, {"SHELL": "/usr/bin/bash"}):
            rc, out = _run(["completion"])
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("# bash completion for aw"))


class SetupCompletionPromptTests(_DropInFixture):
    """E-03/E-04: when `_configure_completion` PROMPTS, and what it installs (host-level, not
    install_wizard.py).

    Nine tests across two classes became this one table. Each was the same six lines: patch
    `isatty`, patch `input`, set `$SHELL`, call `cli._configure_completion(Namespace(...), term)`,
    then make ONE claim, either "a prompt was/was not shown" or "this file exists/does not".

    Why the table beats the nine: `_configure_completion` implements a SINGLE decision procedure
    over a handful of inputs (the `--completion` value, `--yes`, whether stdin is a tty, whether
    completion is already installed, and `$SHELL`), and it has exactly three outcomes: prompt,
    install silently, or do nothing. That makes the real subject a TRUTH TABLE, and the realistic
    failure is a reordered or inverted condition, which flips several rows at once. Nine tests
    report an inverted `--yes` check as two or three unrelated red lines and never show you that
    every non-prompting row moved together. The table reports one failure naming each row with the
    outcome it expected against the outcome it got.

    Three columns are load-bearing and are why this is one table rather than several:
      * `prompted` keeps the `m_input.assert_not_called()` claim, which is about the USER
        EXPERIENCE (a non-interactive install must never block waiting on stdin) and is NOT implied
        by the file outcome. The accept and reject rows install different things while both
        prompting; the `--yes`+flag and already-installed rows prompt for neither.
      * `installed` keeps the filesystem claim, and it is asserted as the COMPLETE set of the three
        supported shells' drop-in files, not just the one shell a row cares about. That is strictly
        stronger than the old per-test assertion: a row that should install zsh now also proves it
        did not additionally install bash or fish.
      * `preinstall` covers the one row whose premise is that completion is ALREADY present. It is
        a column rather than a separate test because the outcome it asserts (no prompt) is the same
        kind of claim every other row makes.

    Every row also re-asserts the CORE PROMISE (`assert_no_dotfile_touched`), which the old tests
    only checked in some of them: no rc/dotfile is ever created or modified, whichever branch runs.
    """

    #: (case, `--completion` value, `--yes`, stdin is a tty, $SHELL, input reply, preinstall shell,
    #:  must it prompt?, the drop-in files that must exist afterwards, why this row exists)
    PROMPT_CASES = (
        (
            "no flag, interactive, user accepts",
            None,
            False,
            True,
            "/usr/bin/bash",
            "y",
            None,
            True,
            {"bash"},
            "the headline path: with no flag and a real terminal, ASK, and install on yes",
        ),
        (
            "no flag, interactive, user declines",
            None,
            False,
            True,
            "/usr/bin/bash",
            "n",
            None,
            True,
            set(),
            "declining must leave the filesystem untouched; a prompt whose 'no' still installs is "
            "worse than no prompt at all",
        ),
        (
            "no flag, NOT a tty",
            None,
            False,
            False,
            "/usr/bin/bash",
            None,
            None,
            False,
            set(),
            "a pipe or CI has nobody to answer, so prompting there would HANG the install",
        ),
        (
            "no flag, under --yes",
            None,
            True,
            True,
            "/usr/bin/bash",
            None,
            None,
            False,
            set(),
            "--yes suppresses the QUESTION but must not be read as consent: installing shell "
            "files nobody asked for is a side effect outside the scope --yes was given for",
        ),
        (
            "--completion none",
            "none",
            False,
            True,
            "/usr/bin/bash",
            None,
            None,
            False,
            set(),
            "an explicit opt-out is final and must not be re-litigated by a prompt",
        ),
        (
            "already installed",
            None,
            False,
            True,
            "/usr/bin/bash",
            None,
            "bash",
            False,
            {"bash"},
            "nothing to offer, so asking again would be noise on every subsequent `aw setup`. The "
            "bash file in the expectation is the PREINSTALLED one, not a fresh install",
        ),
        (
            "--completion bash with --yes",
            "bash",
            True,
            True,
            "/usr/bin/bash",
            None,
            None,
            False,
            {"bash"},
            "an EXPLICIT shell is consent already given, so install without asking",
        ),
        (
            "--completion auto with --yes, $SHELL=zsh",
            "auto",
            True,
            True,
            "/usr/bin/zsh",
            None,
            None,
            False,
            {"zsh"},
            "`auto` resolves through $SHELL, and installs THAT shell only",
        ),
        (
            "--completion fish, not a tty",
            "fish",
            False,
            False,
            "/usr/bin/bash",
            None,
            None,
            False,
            {"fish"},
            "an explicit shell needs no terminal: it must install non-interactively, and must "
            "honor the FLAG over $SHELL (which says bash here)",
        ),
    )

    #: The drop-in file each supported shell installs, so `installed` can be asserted as a whole set.
    def _installed_shells(self) -> set:
        candidates = {
            "bash": self.xdg_data / "bash-completion/completions/aw",
            "zsh": self.xdg_data / "zsh/site-functions/_aw",
            "fish": self.xdg_config / "fish/completions/aw.fish",
        }
        return {shell for shell, path in candidates.items() if path.is_file()}

    def _args(self, **kw):
        base = dict(completion=None, yes=False)
        base.update(kw)
        return argparse.Namespace(**base)

    def test_every_input_combination_reaches_its_declared_outcome(self) -> None:
        wrong = []
        for (
            case,
            comp,
            yes,
            isatty,
            shell_env,
            reply,
            preinstall,
            should_prompt,
            expected_installed,
            why,
        ) in self.PROMPT_CASES:
            # Each row needs a CLEAN home, so the fixture's XDG bases are re-pointed per row.
            row_root = Path(tempfile.mkdtemp(dir=self.root))
            self.xdg_data = row_root / "xdg-data"
            self.xdg_config = row_root / "xdg-config"
            self.home = row_root / "home"
            self.home.mkdir()
            env = {
                "HOME": str(self.home),
                "XDG_DATA_HOME": str(self.xdg_data),
                "XDG_CONFIG_HOME": str(self.xdg_config),
                "SHELL": shell_env,
            }
            with mock.patch.dict(os.environ, env):
                if preinstall:
                    completion.install_shell_completion(preinstall)
                input_patch = (
                    mock.patch.object(cli, "input", create=True, return_value=reply)
                    if reply is not None
                    else mock.patch.object(cli, "input", create=True)
                )
                with (
                    mock.patch.object(cli.sys.stdin, "isatty", return_value=isatty),
                    input_patch as m_input,
                ):
                    cli._configure_completion(
                        self._args(completion=comp, yes=yes), Term(color=False)
                    )
                prompted = m_input.called
                installed = self._installed_shells()
                dotfiles = [p for p in self.dotfile_paths() if p.exists()]

            problems = []
            if prompted != should_prompt:
                problems.append(
                    f"expected it to {'PROMPT' if should_prompt else 'NOT prompt'}, "
                    f"but input() was {'called' if prompted else 'not called'}"
                )
            if installed != expected_installed:
                problems.append(
                    f"expected the installed set {expected_installed or 'nothing'}, "
                    f"got {installed or 'nothing'}"
                )
            if dotfiles:
                problems.append(
                    f"THE CORE PROMISE IS BROKEN: it created or modified {dotfiles!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (completion={comp!r}, yes={yes}, isatty={isatty}, "
                    f"$SHELL={shell_env!r}, reply={reply!r}, preinstalled={preinstall!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"cli._configure_completion reached the wrong outcome for {len(wrong)} of "
            f"{len(self.PROMPT_CASES)} input combinations. This is ONE decision procedure over "
            "five inputs, so several rows moving together usually means a condition was reordered "
            "or inverted rather than several independent bugs. FIX: read the failing rows as a "
            "truth table. Every NON-prompting row suddenly prompting means the guard chain "
            "(`--completion` set / `--yes` / not a tty / already installed) stopped short-"
            "circuiting; the accept row not installing while reject still declines means the reply "
            "parsing flipped; a wrong SHELL installed means `_resolve_completion_choice` is "
            "preferring $SHELL over the explicit flag. Any dotfile appearing is not a regression "
            f"to triage but the one thing this feature promises never to do.\n"
            + "\n".join(wrong),
        )

    def test_prompt_lives_in_cli_not_install_wizard(self) -> None:
        # The reviewed integration point: the per-user completion prompt belongs to the host-level
        # setup flow, NOT the per-target-repo project-policy wizard.
        from agent_workflows import install_wizard

        wizard_src = Path(install_wizard.__file__).read_text(encoding="utf-8")
        for needle in (
            "install_shell_completion",
            "resolve_completion_dir",
            "completion install",
        ):
            self.assertNotIn(
                needle,
                wizard_src,
                "install_wizard.py (per-repo policy wizard) must not carry the "
                "per-user completion prompt",
            )
        cli_src = Path(cli.__file__).read_text(encoding="utf-8")
        self.assertIn("_configure_completion(args, term)", cli_src)

    def test_install_failure_does_not_break_setup(self) -> None:
        """Kept separate: patches the installer to RAISE and asserts the caller swallows it, which is
        an exception-path claim no outcome row expresses."""
        # An optional convenience must never fail the host setup flow.
        term = Term(color=False)
        with mock.patch.object(
            completion,
            "install_shell_completion",
            side_effect=completion.CompletionInstallError("boom"),
        ):
            cli._configure_completion(self._args(completion="bash"), term)  # no raise


class InstallCompletionFlagTests(_DropInFixture):
    """E-04: `--completion [auto|bash|zsh|fish|none]` parsing and resolution.

    The `--completion` value has TWO layers, and they are tabulated separately below because they
    are two different subjects, not two spellings of one: argparse must ACCEPT the value on the
    verbs that offer the flag (`PARSED_FLAGS`), and `cli._resolve_completion_choice` must MAP an
    accepted value to the shell that gets installed, or to `None` for "install nothing"
    (`RESOLUTIONS`). A value can parse fine and resolve wrongly, so collapsing them would hide
    which layer broke.

    `_resolve_completion_choice` is a pure function from (flag value, `$SHELL`) to a shell name or
    `None`, which is exactly a mapping, and the old test asserted four rows of it inside one method
    where the first failure hid the rest. That matters here because `auto` and `none` are the two
    rows that carry real logic (one reads `$SHELL`, one must return `None` rather than the literal
    string `"none"`), and a regression in the branch order breaks both at once.

    The three `_configure_completion` end-to-end tests that used to live in this class
    (`test_explicit_shell_installs_without_prompting`, `test_yes_without_flag_installs_nothing`,
    `test_auto_detects_shell`) are NOT lost: they are rows in
    `SetupCompletionPromptTests.PROMPT_CASES`, which asserts the same prompt-and-install outcomes
    for those exact input combinations, and asserts them more strictly (against the complete set of
    installed shells, plus the no-dotfile promise).
    """

    #: (verb, `--completion` value, why this row exists)
    PARSED_FLAGS = (
        ("install", "zsh", "the flag is registered on `install`"),
        ("setup", "zsh", "and on `setup`, the OTHER host-level verb that offers it"),
        ("install", "auto", "`auto` is an accepted choice"),
        ("install", "bash", "each supported shell is an accepted choice"),
        ("install", "fish", "each supported shell is an accepted choice"),
        (
            "install",
            "none",
            "`none` is an accepted choice: opting out must not be an argparse ERROR",
        ),
    )

    def test_the_completion_flag_parses_on_every_verb_and_choice(self) -> None:
        parser = cli._build_parser()
        wrong = []
        for verb, value, why in self.PARSED_FLAGS:
            try:
                args = parser.parse_args([verb, "--completion", value])
            except (
                SystemExit
            ) as exc:  # argparse rejects with SystemExit, not an exception we want
                wrong.append(
                    f"  `aw {verb} --completion {value}`: argparse REJECTED it "
                    f"(SystemExit {exc.code})\n    this row exists because: {why}"
                )
                continue
            got = getattr(args, "completion", "<no `completion` attribute at all>")
            if got != value:
                wrong.append(
                    f"  `aw {verb} --completion {value}`: parsed as {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the `--completion` flag failed to parse for {len(wrong)} of "
            f"{len(self.PARSED_FLAGS)} verb/choice pairs. One `add_argument` call per verb with one "
            "shared `choices` list decides all of these, so every row for a given VERB failing "
            "means the flag is not registered on that verb, while the same CHOICE failing across "
            "verbs means it was dropped from `choices`. FIX: if `none` is the only failure, "
            "someone likely removed it thinking it redundant; it is the documented opt-out and a "
            f"SystemExit here is a user-facing error.\n" + "\n".join(wrong),
        )

    #: (flag value, $SHELL, expected resolution, why this row exists)
    RESOLUTIONS = (
        (
            None,
            None,
            None,
            "no flag means make no decision here (the prompt layer decides)",
        ),
        (
            "none",
            None,
            None,
            "`none` must resolve to None, NOT to the literal string 'none', which would be handed "
            "on as a shell name and fail deep inside the installer",
        ),
        ("zsh", None, "zsh", "an explicit shell passes straight through"),
        ("bash", None, "bash", "and is not special-cased per shell"),
        (
            "auto",
            "/usr/bin/fish",
            "fish",
            "`auto` is the only value that CONSULTS $SHELL",
        ),
        (
            "auto",
            "/usr/bin/tcsh",
            "bash",
            "`auto` inherits `_detect_shell`'s bash fallback for an unsupported shell, rather than "
            "resolving to None and silently installing nothing",
        ),
        (
            "fish",
            "/usr/bin/bash",
            "fish",
            "an explicit shell WINS over $SHELL; the reverse would make the flag a suggestion",
        ),
    )

    def test_every_flag_value_resolves_to_its_shell(self) -> None:
        wrong = []
        for value, shell_env, expected, why in self.RESOLUTIONS:
            with mock.patch.dict(os.environ, {}, clear=False):
                if shell_env is None:
                    os.environ.pop("SHELL", None)
                else:
                    os.environ["SHELL"] = shell_env
                got = cli._resolve_completion_choice(
                    argparse.Namespace(completion=value)
                )
            if got != expected:
                wrong.append(
                    f"  --completion {value!r} with $SHELL={shell_env!r}: expected {expected!r}, "
                    f"got {got!r}\n    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"cli._resolve_completion_choice resolved {len(wrong)} of {len(self.RESOLUTIONS)} "
            "values wrongly. One branch chain over the flag value decides all of these, so several "
            "rows moving together usually means that chain was reordered. FIX: a row expecting "
            "None that returned a shell name means an opt-out is about to install files (the worst "
            "failure here); a row expecting a shell that returned None means the feature silently "
            "does nothing; and `auto` returning the wrong shell points at `cli._detect_shell`, "
            f"whose own table is above.\n" + "\n".join(wrong),
        )

    def test_tip_shown_when_unconfigured_and_hidden_once_installed(self) -> None:
        """Kept separate: a BEFORE/AFTER pair over one mutating action, not a data row.

        The claim is that installing FLIPS the tip off, so the test needs two observations of the
        same function with a state change between them. A table row holds one input and one
        expected output, which cannot express "and then this changed".
        """
        buf = io.StringIO()
        term = Term(stream=buf, color=False)
        with mock.patch.dict(os.environ, {"SHELL": "/usr/bin/bash"}):
            cli._completion_tip(term)
            self.assertIn("aw completion install", buf.getvalue())

            completion.install_shell_completion("bash")
            buf2 = io.StringIO()
            cli._completion_tip(Term(stream=buf2, color=False))
            self.assertEqual(buf2.getvalue(), "")


# The only test here that SPAWNS the CLI, so it carries the `slow` marker (pyproject.toml:108-109);
# the rest of this module is fast in-process and stays in the default suite.
@pytest.mark.slow
class CompletionInstallSubprocessTests(_DropInFixture):
    """E-04/E-02 end-to-end through a real subprocess (marked slow per pyproject.toml)."""

    def test_module_cli_install_then_uninstall(self) -> None:
        env = dict(os.environ)
        env["XDG_DATA_HOME"] = str(self.xdg_data)
        env["XDG_CONFIG_HOME"] = str(self.xdg_config)
        env["HOME"] = str(self.home)
        primary = self.xdg_data / "bash-completion/completions/aw"

        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "completion",
                "install",
                "--shell",
                "bash",
            ],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(self.root),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(primary.is_file())

        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "completion",
                "uninstall",
                "--shell",
                "bash",
            ],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(self.root),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(primary.exists())
        self.assert_no_dotfile_touched()


class ReadmeCompletionDocsTests(unittest.TestCase):
    """E-05: what the README tells a user to TYPE, and where it says the file lands, must be true.

    WHAT THIS REPLACED, and why. `test_readme_has_shell_tab_completion_section` asserted three
    literal strings appeared in `README.md` ("Shell Tab Completion", "aw completion install",
    "source <(aw completion bash)"). That is a change-detector over prose: git already records a
    README edit, retitling the section is a normal and desirable change, and the pin could not fail
    for any defect in the feature. It also could not catch the failure that actually matters, namely
    the README documenting a command or a path that no longer works.

    The two tests below are that check instead. Both are falsifiable against the CODE, not against
    wording: the README's commands are parsed by the REAL argparse parser, and its per-shell
    drop-in table is compared to what `resolve_completion_dir` + `completion_filename` actually
    produce. Rewriting every sentence around them is free.

    NON-VACUITY is asserted deliberately: each test requires that the README documents SOMETHING
    (at least one `aw completion` invocation; all three shells' paths), because a check over an
    empty extraction would pass on a README with the section deleted.
    """

    README = Path(__file__).resolve().parents[1] / "README.md"

    #: A fenced-or-inline `aw ...` invocation, up to a trailing comment or a closing paren.
    _CMD_RE = re.compile(
        r"(?m)(?:^|source <\()(aw completion[^#\n)]*|aw install[^#\n)]*)"
    )
    #: A row of the per-shell drop-in path table: `| Bash | `<path>` |`.
    _ROW_RE = re.compile(r"(?m)^\|\s*(Bash|Zsh|Fish)\s*\|\s*`([^`]+)`\s*\|")

    def test_every_command_the_readme_tells_a_user_to_run_parses(self) -> None:
        """A documented command that argparse rejects is a defect the user hits immediately."""

        from agent_workflows import cli

        body = self.README.read_text(encoding="utf-8")
        commands = sorted({m.group(1).strip() for m in self._CMD_RE.finditer(body)})
        self.assertTrue(
            commands,
            "the README documents no `aw completion` invocation at all, so this check would be "
            "vacuous. The feature must be documented somewhere in README.md; the wording and the "
            "section title are NOT pinned.",
        )
        parser = cli._build_parser()
        broken = []
        for cmd in commands:
            argv = shlex.split(cmd)[1:]
            err = io.StringIO()
            try:
                with redirect_stderr(err):
                    parser.parse_args(argv)
            except SystemExit:
                broken.append(
                    f"  {cmd!r}: argparse REJECTED it -> {err.getvalue().strip().splitlines()[-1:]}"
                )
        self.assertEqual(
            broken,
            [],
            f"the README documents {len(broken)} of {len(commands)} completion/install commands "
            "that the real CLI no longer accepts. A user copies these literally, so each one is a "
            "command that fails on first use:\n"
            + "\n".join(broken)
            + "\n  FIX: update README.md to the current flag spelling, or restore the flag. Only "
            "the COMMANDS are checked here; the surrounding prose may be rewritten freely.",
        )

    def test_the_documented_drop_in_paths_are_the_paths_the_installer_uses(
        self,
    ) -> None:
        """The path table is a PROMISE about where a file lands; derive it, do not pin it.

        The README writes the paths in shell-expansion form
        (`${XDG_DATA_HOME:-~/.local/share}/...`), which is how a user reads them; this resolves
        that form with the env var SET and again with it UNSET, and compares both against
        `resolve_completion_dir(shell) / completion_filename(shell)`. So a relocated drop-in
        directory fails here, while retitling or reformatting the table does not.
        """

        body = self.README.read_text(encoding="utf-8")
        documented = {shell.lower(): path for shell, path in self._ROW_RE.findall(body)}
        self.assertEqual(
            sorted(documented),
            sorted(completion.SUPPORTED_SHELLS),
            f"the README's drop-in path table documents {sorted(documented)}, but the installer "
            f"supports {sorted(completion.SUPPORTED_SHELLS)}. A supported shell with no documented "
            "path leaves a user guessing; a documented shell the installer refuses is a promise it "
            "cannot keep.",
        )

        wrong = []
        for shell, template in sorted(documented.items()):
            # `${VAR:-default}/rest` -> (VAR, default, rest)
            m = re.match(r"^\$\{([A-Z_]+):-([^}]+)\}(/.*)$", template)
            if m is None:
                wrong.append(
                    f"  {shell}: documented path {template!r} is not in the "
                    "`${VAR:-default}/rest` form this test can resolve; if the documentation "
                    "style changed deliberately, update this parser"
                )
                continue
            var, default, rest = m.groups()
            for mode, env in (
                ("env set", {var: str(self.SET_BASE)}),
                ("env unset", {}),
            ):
                with mock.patch.dict(os.environ, env, clear=True):
                    os.environ["HOME"] = str(self.HOME)
                    actual = completion.resolve_completion_dir(
                        shell
                    ) / completion.completion_filename(shell)
                    base = (
                        Path(self.SET_BASE)
                        if mode == "env set"
                        else Path(default.replace("~", str(self.HOME)))
                    )
                    expected = Path(str(base) + rest)
                if actual != expected:
                    wrong.append(
                        f"  {shell} ({mode}): README promises {expected}\n"
                        f"    installer writes    {actual}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} documented drop-in path(s) disagree with where the installer actually "
            "writes. A wrong path in the README sends a user to inspect a file that is not there, "
            "and looks exactly like completion being broken:\n"
            + "\n".join(wrong)
            + "\n  FIX: change `completion._DROPIN_LAYOUT` and the README table together. The env "
            "var each shell uses is deliberately NOT uniform (fish discovers completions under "
            "XDG_CONFIG_HOME), so check the per-shell row rather than assuming one base.",
        )

    #: Fixed bases so the comparison is about the LAYOUT, not about this machine's real HOME/XDG.
    HOME = Path("/tmp/aw-readme-home")
    SET_BASE = Path("/tmp/aw-readme-xdg")


if __name__ == "__main__":
    unittest.main()
