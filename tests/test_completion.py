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

compinert Order 01 (92u0v9) covers the precondition the install never checked: E-01
(`completion_framework_status` reports PRESENT / REACHABLE / RC-SOURCES-IT as separate facts, with
UNKNOWN for a failed probe or an unmodelled shell), E-02 (the four message variants, and above all
that the non-reachable case is NOT labelled `ok` and does NOT tell the user to start a new shell),
E-03 (the guarded snippet, and the fenced `~/.bashrc` write that happens ONLY on explicit TTY
consent, never under `--yes`, never non-interactively, never twice, and never by creating an absent
file), and E-04 (all of it driven by INJECTION, never by the developer's own shell).
"""

from __future__ import annotations

import argparse
import io
import json
import os
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

    def test_introspect_cli_tree_visibility_and_immutability(self) -> None:
        p = cli._build_parser()
        before = [a.dest for a in p._actions]
        tree = completion.introspect_cli_tree(p)
        after = [a.dest for a in p._actions]
        self.assertEqual(before, after)

        top = set(tree["subcommands"])
        wrong = []
        for name, should_be_present, why in self.VISIBILITY:
            present = name in top
            if present != should_be_present:
                wrong.append(
                    f"  {name!r}: expected {'COMPLETABLE' if should_be_present else 'EXCLUDED'}, "
                    f"got {'COMPLETABLE' if present else 'EXCLUDED'}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(wrong, [])

        self.assertFalse(
            any(name.endswith("-gate") for name in top),
            "no *-gate command may be completable",
        )
        self.assertIn("ipd", tree["subcommands"])
        self.assertTrue(tree["subcommands"]["ipd"]["subcommands"])


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
                    f"  {shell}: completion.{generator_name} returned an EMPTY script\n"
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
        self.assertEqual(wrong, [])

        # Escaping checks
        zsh_desc = completion._zsh_desc("uses `x` and $y")
        self.assertNotIn("`", zsh_desc.replace("\\`", ""))
        self.assertNotIn("$", zsh_desc.replace("\\$", ""))

    def test_shells_parse_under_syntax_checks(self) -> None:
        checks = [
            ("bash", ["bash", "-n"], completion.generate_bash_completion),
            ("zsh", ["zsh", "-n"], completion.generate_zsh_completion),
            ("fish", ["fish", "--no-execute"], completion.generate_fish_completion),
        ]
        for shell, cmd, gen in checks:
            if shutil.which(shell):
                self._check_shell(shell, cmd, gen)

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


def _drive_bash_completion(script: str, words, cword=None):
    """EXECUTE a generated bash completion script and return the resulting `COMPREPLY` list.

    compargs 4y95tp E-04. This is the technique that found the fall-through defect, and the reason it
    is a helper rather than a one-off: every text-level assertion in this module passed throughout the
    bug's life, because the generated script was always internally CONSISTENT. It said "if no arm
    matched, offer the top-level commands", and it did exactly that - which was the defect. Only
    sourcing the script, setting `COMP_WORDS`/`COMP_CWORD` as bash does, calling `_aw_completion`, and
    reading `COMPREPLY` reveals that `aw find <TAB>` proposed `commit`, `archive` and `uninstall` as
    things to find. Assert on what the function RETURNS, never on what the script SAYS.

    Returns the candidate list; an EMPTY list is a meaningful answer (bash then falls back to its own
    default completion, e.g. filenames), not a failure to measure.
    """
    if cword is None:
        cword = len(words) - 1
    with tempfile.TemporaryDirectory() as tmp:
        script_path = Path(tmp) / "aw.bash"
        script_path.write_text(script, encoding="utf-8")
        # `printf '%s\n'` with an empty COMPREPLY would emit one blank line, so the count is printed
        # first and used to decide whether any candidate lines follow.
        driver = (
            f"source {shlex.quote(str(script_path))}\n"
            f"COMP_WORDS=({' '.join(shlex.quote(w) for w in words)})\n"
            f"COMP_CWORD={cword}\n"
            "_aw_completion\n"
            'echo "COUNT:${#COMPREPLY[@]}"\n'
            'if [[ ${#COMPREPLY[@]} -gt 0 ]]; then printf "%s\\n" "${COMPREPLY[@]}"; fi\n'
        )
        proc = subprocess.run(
            ["bash", "-c", driver], capture_output=True, text=True, check=False
        )
    if proc.returncode != 0:
        raise AssertionError(
            f"driving the generated bash completion failed (rc={proc.returncode}): {proc.stderr}"
        )
    lines = proc.stdout.strip().split("\n")
    count = int(lines[0].split(":", 1)[1])
    return sorted(lines[1 : 1 + count])


@unittest.skipUnless(shutil.which("bash"), "bash not installed")
class BashCompletionDrivenTests(unittest.TestCase):
    """The generated bash function is EXECUTED, and a command completes its OWN arguments.

    compargs 4y95tp E-04. This class exists because the whole module could not see the defect it
    covers. `aw completion <TAB><TAB>` listed all 47 top-level commands, `aw completion in<TAB>`
    narrowed to `include index install`, and taking `index` produced
    `error: unknown completion target 'index'` - the completion actively led the maintainer into an
    error. The cause was an unconditional `COMPREPLY=( ... top_names ... )` after the `case`, which
    made every command WITHOUT a `case` arm (30 of 47, measured) suggest the entire command list.

    WHY A TABLE HERE. The four rows are not four independent behaviors: one generator, one `case`
    construction and one `_node_candidates` helper decide all of them, so the realistic failure moves
    several rows at once. A reintroduced fall-through turns BOTH empty rows non-empty together, which
    a table reports as one message naming both plus the tokens they wrongly offered; four separate
    tests would report it as two red lines and each `assertEqual` would name only its own row.

    WHY EMPTY IS THE CORRECT ANSWER for two of them, since "completes nothing" reads like a
    regression: bash falls back to its OWN default (filenames) when `COMPREPLY` is empty, which for
    `aw find <PATTERN>` is frequently what the user wants and is never actively misleading. Offering
    `archive` as a thing to `find` is. Do not "fix" an empty row by restoring a fallback.
    """

    def setUp(self) -> None:
        self.script = completion.generate_bash_completion()

    #: (case, words, expected COMPREPLY (sorted) or None for "compute from the parser", why)
    DRIVEN = (
        (
            "aw find <TAB>",
            ["aw", "find", ""],
            [],
            "`find` has neither subcommands nor a choices-bearing positional, so the parser "
            "declares NO vocabulary for this slot and the honest answer is none. Before the fix it "
            "returned all 47 command names, proposing `commit` and `archive` as things to find",
        ),
        (
            "aw install <TAB>",
            ["aw", "install", ""],
            [],
            "a SECOND command from the 30 that had no `case` arm, so the fix is proven general "
            "rather than special-cased to one name",
        ),
        (
            "aw completion <TAB>",
            ["aw", "completion", ""],
            ["bash", "fish", "install", "uninstall", "zsh"],
            "the MAINTAINER'S REPORTED COMMAND. It works only because E-08 gave the positional real "
            "argparse `choices`: the vocabulary previously existed solely as a `metavar` display "
            "string, so no amount of generator work could have surfaced it",
        ),
        (
            "aw migrate-layout <TAB>",
            ["aw", "migrate-layout", ""],
            [
                "apply",
                "cleanup",
                "inventory",
                "plan",
                "resume",
                "rollback",
                "status",
                "wizard",
            ],
            "one of the two commands whose arguments are a positional with `choices`; it completed "
            "nothing true before, because the tree walker descended only `_SubParsersAction`",
        ),
        (
            "aw path <TAB>",
            ["aw", "path", ""],
            ["config", "records", "state", "system"],
            "the other choices-bearing command, so the capture is not tuned to one parser shape",
        ),
        (
            "aw ipd <TAB>",
            ["aw", "ipd", ""],
            None,
            "THE WORKING HALF MUST STAY WORKING: `ipd` has real subparsers and always completed "
            "correctly, so this row is what proves removing the fall-through did not break the 17 "
            "commands that had a `case` arm. Expected is computed from the parser so adding an ipd "
            "leaf does not make this a maintenance burden",
        ),
        (
            "aw completion in<TAB>",
            ["aw", "completion", "in"],
            ["install"],
            "THE EXACT REPORTED SEQUENCE, and the load-bearing assertion is what is ABSENT: this "
            "returned `include index install` before, and a test merely checking that `install` is "
            "present would have PASSED against the broken build. `index` must not appear",
        ),
    )

    def test_bash_completion_driven_and_script_invariants(self) -> None:
        tree = completion.introspect_cli_tree(cli._build_parser())
        wrong = []
        for case, words, expected, why in self.DRIVEN:
            if expected is None:
                expected = sorted(tree["subcommands"]["ipd"]["subcommands"])
            got = _drive_bash_completion(self.script, words)
            if got != sorted(expected):
                extra = [t for t in got if t not in expected]
                missing = [t for t in expected if t not in got]
                detail = []
                if extra:
                    detail.append(f"WRONGLY OFFERED {extra[:8]!r} ({len(extra)} extra)")
                if missing:
                    detail.append(f"MISSING {missing!r}")
                wrong.append(
                    f"  {case}: "
                    + "; ".join(detail)
                    + f"\n    this row exists because: {why}"
                )
        self.assertEqual(wrong, [])

        # Script structure invariants
        lines = self.script.split("\n")
        esac_index = next(i for i, line in enumerate(lines) if line.strip() == "esac")
        after = [
            line.strip()
            for line in lines[esac_index + 1 :]
            if line.strip() and not line.strip().startswith("#")
        ]
        offending = [line for line in after if line.startswith("COMPREPLY=")]
        self.assertEqual(offending, [])

        body = "\n".join(
            line
            for line in self.script.split("\n")
            if not line.lstrip().startswith("#")
        )
        for needle in ("__complete", "$(aw ", "$(agentwf ", "`aw "):
            self.assertNotIn(needle, body)


class PositionalChoicesIntrospectionTests(unittest.TestCase):
    """`introspect_cli_tree` captures positional `choices` under their OWN key (4y95tp E-02).

    The walker used to descend only `_SubParsersAction`, so a command expressing its arguments as a
    positional with a fixed `choices` vocabulary contributed NOTHING and the generators had nothing
    true to offer for it.

    THE KEY IS SEPARATE ON PURPOSE. Choice tokens are not subcommands: they do not nest and carry no
    flags of their own, so merging them into `subcommands` would invite a generator to emit a third
    level for something that cannot have one, and would make `_all_command_paths` report
    `migrate-layout apply` as a command path. These tests pin the separation, not just the capture.
    """

    def setUp(self) -> None:
        self.tree = completion.introspect_cli_tree(cli._build_parser())

    def test_positional_choices_introspection(self) -> None:
        node = self.tree["subcommands"]["migrate-layout"]
        self.assertEqual(
            sorted(node["choices"]),
            [
                "apply",
                "cleanup",
                "inventory",
                "plan",
                "resume",
                "rollback",
                "status",
                "wizard",
            ],
        )
        self.assertEqual(node["subcommands"], {})

        for name in ("find", "install", "show"):
            if name not in self.tree["subcommands"]:
                continue
            self.assertEqual(self.tree["subcommands"][name]["choices"], [])

        with_choices = sorted(
            name for name, n in self.tree["subcommands"].items() if n.get("choices")
        )
        self.assertEqual(with_choices, ["completion", "migrate-layout", "path"])


class CompletionSurfaceParityTests(unittest.TestCase):
    """The static scripts and the dynamic `complete_query` agree on the static layer (4y95tp E-05).

    THE CONTRACT IS DOCUMENTED, NOT INFERRED: `_subcommand_candidates`'s docstring says it "mirrors
    the generated static scripts so `__complete` and the offline scripts agree on the static layer".
    Nothing asserted it, which is why teaching only the static generators about positional `choices`
    would have falsified that sentence silently, in the very file that states it. Maintainer ruling
    2026-09-12 (OQ-03): fix BOTH surfaces; the amend-the-docstring branch is closed.

    This is the durable half of E-05. The implementation makes drift structurally hard (both surfaces
    read the same tree key through the same `_node_candidates` helper), and this test is what notices
    if a later change routes one of them around it.
    """

    #: (words, cword, why this case is in the parity set)
    PARITY_CASES = (
        (
            ["aw", "completion", ""],
            2,
            "the maintainer's reported keystroke, and the case the plan's "
            "review named explicitly: a `choices` vocabulary both surfaces must now see",
        ),
        (
            ["aw", "migrate-layout", ""],
            2,
            "a choices-bearing command the static side gained in this "
            "change; the dynamic side offered nothing here before E-05",
        ),
        (["aw", "path", ""], 2, "the second choices-bearing command"),
        (
            ["aw", "ipd", ""],
            2,
            "a SUBCOMMAND-bearing command, so parity is shown for the half that "
            "already worked and not only for the new half",
        ),
        (
            ["aw", "find", ""],
            2,
            "a command with NO vocabulary: both surfaces must agree on offering "
            "nothing, which is where they already agreed before this change",
        ),
    )

    @unittest.skipUnless(shutil.which("bash"), "bash not installed")
    def test_both_surfaces_return_the_same_static_candidates(self) -> None:
        script = completion.generate_bash_completion()
        wrong = []
        for words, cword, why in self.PARITY_CASES:
            static = _drive_bash_completion(script, words, cword)
            dynamic = sorted(completion.complete_query(words, cword))
            if static != dynamic:
                wrong.append(
                    f"  {' '.join(words[:-1])} <TAB>: static script returned {static!r} but "
                    f"complete_query returned {dynamic!r}\n"
                    f"    this case exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the two completion surfaces disagreed on {len(wrong)} of {len(self.PARITY_CASES)} "
            "static-layer positions. `_subcommand_candidates`'s own docstring promises they agree, "
            "and a user reaches one or the other depending on whether argcomplete is active, so a "
            "disagreement produces 'it works in my other shell' reports. FIX: both sides are meant "
            "to read `introspect_cli_tree`'s `subcommands` + `choices` through "
            "`completion._node_candidates`; a divergence means one side grew its own candidate "
            "logic. Do NOT resolve this by amending the parity docstring: the maintainer closed "
            f"that option on 2026-09-12 (OQ-03).\n" + "\n".join(wrong),
        )


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

    def test_completion_cli_invocations_and_detect_shell(self) -> None:
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
        self.assertEqual(wrong, [])

        wrong_detect = []
        for value, expected, why in self.DETECTED_SHELLS:
            with mock.patch.dict(os.environ, {"SHELL": value}):
                got = cli._detect_shell()
            if got != expected:
                wrong_detect.append(
                    f"  $SHELL={value!r} expected {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(wrong_detect, [])

        # Parser shape allows extension
        parser = cli._build_parser()
        args = parser.parse_args(["completion", "install"])
        self.assertEqual(args.command, "completion")
        self.assertEqual(args.target, "install")
        target_action = next(
            a
            for a in parser._subparsers._group_actions[0]  # type: ignore[union-attr]
            .choices["completion"]
            ._actions
            if a.dest == "target"
        )
        self.assertEqual(
            sorted(target_action.choices or []),
            sorted([*completion.SUPPORTED_SHELLS, "install", "uninstall"]),
        )
        for shell in completion.SUPPORTED_SHELLS:
            self.assertIn(shell, target_action.choices or [])
        with self.assertRaises(SystemExit):
            with redirect_stderr(io.StringIO()):
                parser.parse_args(["completion", "index"])


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

    def test_complete_query_positions_and_vocabularies(self) -> None:
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
            "vocabularies breaking independently.\n" + "\n".join(wrong),
        )

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
    """`run_id_candidates` directly, NOT through `complete_query`."""

    def test_run_id_candidates_filtering_and_backends(self) -> None:
        rec = self.root / ".aw" / "records"
        (rec / "runs" / "analytics" / "snapshots" / "run-snapshot").mkdir(parents=True)
        (rec / "runs" / "analytics").mkdir(parents=True, exist_ok=True)
        (rec / "runs" / "not-a-run").mkdir(parents=True, exist_ok=True)
        got = completion.run_id_candidates(self.root)
        self.assertIn("run-20260829T000000Z-1", got)
        self.assertNotIn("analytics", got)
        self.assertNotIn("not-a-run", got)
        self.assertNotIn("run-snapshot", got)

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
            got_alt = completion.run_id_candidates(alt_root)
            self.assertIn("run-20260901T120000Z-9", got_alt)
            self.assertNotIn("analytics", got_alt)


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

    def test_cli_imports_and_runs_without_argcomplete(self) -> None:
        # argcomplete is optional; simulate its absence and prove main() still runs cleanly.
        import builtins

        real_import = builtins.__import__

        def _no_argcomplete(name, *a, **k):
            if name == "argcomplete" or name.startswith("argcomplete."):
                raise ImportError("simulated: argcomplete not installed")
            return real_import(name, *a, **k)

        with mock.patch.object(builtins, "__import__", _no_argcomplete):
            rc, out = _run(["completion", "bash"])
            self.assertEqual(rc, 0)
            self.assertTrue(out.startswith("# bash completion for aw"))

            parser = cli._build_parser()
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
            f"{len(self.DIRECTORIES)} shell/mode combinations.\n" + "\n".join(wrong),
        )

        with self.assertRaises(completion.CompletionInstallError):
            completion.resolve_completion_dir("tcsh")

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

    def test_shell_install_layout_and_behavior(self) -> None:
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
                        f"got {head!r}."
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
                    f"THE CORE PROMISE IS BROKEN: installing {shell} created or modified {touched!r}"
                )
            if problems:
                wrong.append(
                    f"  {shell} (into {directory}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(wrong, [])

        # zsh compinit line order
        result = completion.install_shell_completion("zsh")
        lines = result["paths"][0].read_text(encoding="utf-8").split("\n")
        self.assertTrue(lines[0].startswith("#compdef"))
        self.assertEqual(lines[1], completion.INSTALL_SENTINEL)

        # Creates missing parent directories
        directory = self.xdg_data / "bash-completion/completions_fresh"
        with mock.patch.dict(os.environ, {"XDG_DATA_HOME": str(directory.parent)}):
            pass

        # Idempotency
        first = completion.install_shell_completion("bash")
        body = first["paths"][0].read_text(encoding="utf-8")
        second = completion.install_shell_completion("bash")
        self.assertEqual(second["paths"], first["paths"])
        self.assertEqual(second["paths"][0].read_text(encoding="utf-8"), body)
        self.assertTrue(completion.is_completion_installed("bash"))

        # Dry run
        dry_result = completion.install_shell_completion("bash", dry_run=True)
        self.assertTrue(dry_result["dry_run"])
        self.assertTrue(dry_result["paths"])

    def test_refuses_foreign_completion_states(self) -> None:
        directory = self.xdg_data / "bash-completion/completions"
        directory.mkdir(parents=True, exist_ok=True)
        foreign = directory / "aw"
        foreign.write_text("# someone else's aw completion\n", encoding="utf-8")
        with self.assertRaises(completion.CompletionInstallError):
            completion.install_shell_completion("bash")
        self.assertEqual(
            foreign.read_text(encoding="utf-8"), "# someone else's aw completion\n"
        )

        # Foreign alias file
        foreign.unlink()
        (directory / "agentwf").write_text("# foreign alias\n", encoding="utf-8")
        with self.assertRaises(completion.CompletionInstallError):
            completion.install_shell_completion("bash")
        self.assertFalse((directory / "aw").exists())
        (directory / "agentwf").unlink()

        # Symlink to unexpected target
        outside = self.root / "outside.bash"
        outside.write_text("# not ours\n", encoding="utf-8")
        (directory / "aw").symlink_to(outside)
        with self.assertRaises(completion.CompletionInstallError):
            completion.install_shell_completion("bash")
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
            f"{len(self.UNINSTALL_CASES)} directory states.\n" + "\n".join(wrong),
        )

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

    def test_completion_flag_parsing_resolution_and_tip(self) -> None:
        parser = cli._build_parser()
        wrong = []
        for verb, value, why in self.PARSED_FLAGS:
            try:
                args = parser.parse_args([verb, "--completion", value])
            except SystemExit as exc:
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
        self.assertEqual(wrong, [])

        wrong_res = []
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
                wrong_res.append(
                    f"  --completion {value!r} with $SHELL={shell_env!r}: expected {expected!r}, "
                    f"got {got!r}\n    this row exists because: {why}"
                )
        self.assertEqual(wrong_res, [])

        # Tip shown when unconfigured and hidden once installed
        buf = io.StringIO()
        term = Term(stream=buf, color=False)
        with mock.patch.dict(os.environ, {"SHELL": "/usr/bin/bash"}):
            cli._completion_tip(term)
            self.assertIn("aw completion install", buf.getvalue())

            completion.install_shell_completion("bash")
            buf2 = io.StringIO()
            cli._completion_tip(Term(stream=buf2, color=False))
            self.assertEqual(buf2.getvalue(), "")


class StaleCompletionWarningTests(_DropInFixture):
    """An installed-but-OUTDATED completion script is reported, and never rewritten (4y95tp E-06).

    THE GAP THIS CLOSES. The generated file is written once by `aw completion install`, and NOTHING in
    the install/upgrade path regenerates it, so a framework upgrade that adds or renames a command
    leaves the user completing a vocabulary that no longer exists. Worse, it was UNREPORTABLE:
    `_completion_configured` composes `is_completion_installed`, a PRESENCE check, so a stale file took
    the same silent branch as a current one and the user had no way to find out. This defect's own fix
    would not have reached an already-installed user for exactly that reason.

    WARN, NEVER REWRITE (maintainer ruling 2026-09-12, OQ-01). The user's completion file is theirs
    once written and a user-scoped write requires consent, so the file-untouched assertion below is
    not a detail: a run that warns correctly AND rewrites the file has failed this class.

    WHY A TABLE FOR THE THREE STATES. `_completion_tip` is one predicate over one classification, so
    the realistic failure (the classification collapsing back to a two-state presence check) moves the
    rows together: `stale` silently becomes `current`, or `current` starts warning on every command.
    Three separate tests report only the first; the table reports which states produced which output.
    """

    def _tip_output(self) -> str:
        buf = io.StringIO()
        cli._completion_tip(Term(stream=buf, color=False))
        return buf.getvalue()

    def _make_stale(self) -> Path:
        """Install, then edit the installed file so it no longer matches a fresh generation.

        Simulates the REAL cause (an upgrade whose generator output changed) without needing a second
        version of the package installed, and keeps our sentinel intact so the file is still
        recognizably ours - a file without the sentinel is FOREIGN, which is a different state.
        """
        completion.install_shell_completion("bash")
        primary = self.xdg_data / "bash-completion/completions/aw"
        body = primary.read_text(encoding="utf-8")
        primary.write_text(
            body.replace(
                "_aw_completion() {",
                "_aw_completion() {\n    # a command this version no longer has",
            ),
            encoding="utf-8",
        )
        return primary

    #: (state, setup name, expected substring or None for "no output at all", why this row exists)
    STATES = (
        (
            "absent",
            "none",
            "Tip: Enable tab-completion",
            "the original behavior must be untouched: with no file installed the user needs the "
            "enable-tip, not a staleness warning about a file that does not exist",
        ),
        (
            "current",
            "install",
            None,
            "SILENCE is the whole point of the current state. A warning on every `aw install` for a "
            "perfectly good file would train the user to ignore the message",
        ),
        (
            "stale",
            "stale",
            "aw completion install",
            "the new state, and the message must NAME THE COMMAND to run; a warning that says only "
            "'your completion is outdated' leaves the user to guess",
        ),
    )

    def test_stale_completion_warning_and_file_safety(self) -> None:
        wrong = []
        for state, setup, expected, why in self.STATES:
            with tempfile.TemporaryDirectory() as tmp:
                self.xdg_data = Path(tmp) / "xdg-data"
                with mock.patch.dict(
                    os.environ,
                    {
                        "SHELL": "/bin/bash",
                        "HOME": str(self.home),
                        "XDG_DATA_HOME": str(self.xdg_data),
                        "XDG_CONFIG_HOME": str(self.xdg_config),
                    },
                ):
                    if setup == "install":
                        completion.install_shell_completion("bash")
                    elif setup == "stale":
                        self._make_stale()
                    observed_state = completion.installed_completion_state("bash")
                    out = self._tip_output()
                problems = []
                if observed_state != state:
                    problems.append(
                        f"classified as {observed_state!r}, expected {state!r}"
                    )
                if expected is None:
                    if out != "":
                        problems.append(f"expected NO output, got {out!r}")
                elif expected not in out:
                    problems.append(
                        f"expected output containing {expected!r}, got {out!r}"
                    )
                if problems:
                    wrong.append(
                        f"  state {state}: "
                        + "; ".join(problems)
                        + f"\n    this row exists because: {why}"
                    )
        self.assertEqual(wrong, [])

        # Stale warning does not touch user file
        with tempfile.TemporaryDirectory() as tmp:
            self.xdg_data = Path(tmp) / "xdg-data"
            self.xdg_config = Path(tmp) / "xdg-config"
            with mock.patch.dict(
                os.environ,
                {
                    "SHELL": "/bin/bash",
                    "HOME": str(self.home),
                    "XDG_DATA_HOME": str(self.xdg_data),
                    "XDG_CONFIG_HOME": str(self.xdg_config),
                },
            ):
                primary = self._make_stale()
                before_stat = primary.stat()
                before_bytes = primary.read_bytes()

                out = self._tip_output()
                self.assertIn("aw completion install", out)

                after_stat = primary.stat()
                self.assertEqual(before_bytes, primary.read_bytes())
                self.assertEqual(
                    (before_stat.st_mtime_ns, before_stat.st_size),
                    (after_stat.st_mtime_ns, after_stat.st_size),
                )

        # Foreign file is absent not stale
        with tempfile.TemporaryDirectory() as tmp:
            self.xdg_data = Path(tmp) / "xdg-data"
            self.xdg_config = Path(tmp) / "xdg-config"
            directory = self.xdg_data / "bash-completion/completions"
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "aw").write_text(
                "# someone else's completion for a different aw\n", encoding="utf-8"
            )
            with mock.patch.dict(
                os.environ,
                {
                    "SHELL": "/bin/bash",
                    "HOME": str(self.home),
                    "XDG_DATA_HOME": str(self.xdg_data),
                    "XDG_CONFIG_HOME": str(self.xdg_config),
                },
            ):
                self.assertEqual(
                    completion.installed_completion_state("bash"), "absent"
                )
                out = self._tip_output()
            self.assertIn("Tip: Enable tab-completion", out)
            self.assertNotIn("OUTDATED", out)

        # Warning is scoped to detected shell
        with tempfile.TemporaryDirectory() as tmp:
            self.xdg_data = Path(tmp) / "xdg-data"
            self.xdg_config = Path(tmp) / "xdg-config"
            with mock.patch.dict(
                os.environ,
                {
                    "SHELL": "/bin/bash",
                    "HOME": str(self.home),
                    "XDG_DATA_HOME": str(self.xdg_data),
                    "XDG_CONFIG_HOME": str(self.xdg_config),
                },
            ):
                completion.install_shell_completion("zsh")
                zsh_primary = self.xdg_data / "zsh/site-functions/_aw"
                zsh_primary.write_text(
                    zsh_primary.read_text(encoding="utf-8") + "\n# drift\n",
                    encoding="utf-8",
                )
                completion.install_shell_completion("bash")
                self.assertEqual(completion.installed_completion_state("zsh"), "stale")
                self.assertEqual(
                    completion.installed_completion_state("bash"), "current"
                )
                self.assertEqual(self._tip_output(), "")


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


# ======================================================================================
# compinert Order 01 (92u0v9): the install reports whether it can ACTUALLY take effect.
# ======================================================================================


class FrameworkStatusTests(unittest.TestCase):
    """E-01/E-04: the three precondition facts, driven ENTIRELY by injection.

    WHY INJECTION IS MANDATORY HERE AND NOT MERELY TIDY, and this is measured rather than argued.
    The machine this feature was reported on answered `bash -ic 'echo ${BASH_COMPLETION_VERSINFO-}'`
    with EMPTY at authoring time and with `2` two days later, because a human added the remediation
    stanza to their `~/.bashrc` in between. No code changed. A test reading the ambient environment
    would have reversed its verdict on its own, which is the worst possible behavior for a
    regression test: it would have gone green on a broken predicate, or red on a correct one,
    depending on whose machine ran it. So every row below injects the entry-script list, the probe,
    and the rc path, and `test_no_test_here_reads_the_ambient_shell` asserts that property of the
    file itself.

    The four states are ONE table because they are four outcomes of ONE decision procedure, and the
    realistic regression (a reordered check, or collapsing the facts into a boolean) moves several
    rows at once. `rc_sources_it` and `rc_has_stanza` are columns rather than separate tests for the
    same reason: they are additional FACTS of the same measurement, and the whole design claim of
    E-01 is that these facts do not collapse into one another.
    """

    #: (case, entry-script candidates, probe verdict, rc text or None, expected present/reachable/
    #:  rc_sources_it/rc_has_stanza, why this row exists)
    STATES = (
        (
            "reachable: framework present and loaded interactively",
            ["<PRESENT>"],
            (completion.REACHABLE_YES, "BASH_COMPLETION_VERSINFO=2"),
            "export FOO=1\n",
            (True, completion.REACHABLE_YES, False, False),
            "the working case, which must stay reported as working: this is the state the original "
            "unconditional `ok` message was correct for",
        ),
        (
            "present but NOT reachable: the reported defect",
            ["<PRESENT>"],
            (completion.REACHABLE_NO, "BASH_COMPLETION_VERSINFO is unset"),
            "export FOO=1\n",
            (True, completion.REACHABLE_NO, False, False),
            "the whole reason this plan exists: the drop-in is installed and inert, and a one-line "
            "rc fix repairs it. `present=True` with `reachable='no'` is the state that must be "
            "distinguishable from the absent case, which a boolean cannot do",
        ),
        (
            "absent: no entry script anywhere on this system",
            ["/nonexistent/bash_completion"],
            ("probe must not be consulted", ""),
            "export FOO=1\n",
            (False, completion.REACHABLE_NO, False, False),
            "no rc line can help when there is nothing to source, so this needs DIFFERENT advice "
            "(install a package). The probe result is deliberately garbage to prove it is not "
            "consulted in this state",
        ),
        (
            "unknown: the probe could not answer",
            ["<PRESENT>"],
            (completion.REACHABLE_UNKNOWN, "the `bash -ic` probe timed out after 5s"),
            "export FOO=1\n",
            (True, completion.REACHABLE_UNKNOWN, False, False),
            "a failed probe must NOT become a confident negative; telling a user their working "
            "setup is broken on the strength of a timeout is worse than saying we could not tell",
        ),
        (
            "rc already sources the framework",
            ["<PRESENT>"],
            (completion.REACHABLE_YES, "BASH_COMPLETION_VERSINFO=2"),
            "[ -r /usr/share/bash-completion/bash_completion ] && . /usr/share/bash-completion/bash_completion\n",
            (True, completion.REACHABLE_YES, True, False),
            "fact (c) is INDEPENDENT of fact (b): an rc that mentions the framework does not prove "
            "it loads, and this row is what keeps the two from being merged",
        ),
        (
            "rc already carries OUR fenced stanza, hand-added",
            ["<PRESENT>"],
            (completion.REACHABLE_YES, "BASH_COMPLETION_VERSINFO=2"),
            "before\n" + completion.remediation_snippet(fenced=True) + "\nafter\n",
            (True, completion.REACHABLE_YES, True, True),
            "the reporting machine's live `~/.bashrc` is exactly this: the stanza was added BY HAND "
            "before this code existed. It must read as already-satisfied (so the offer is a no-op) "
            "rather than being duplicated, which is the opposite of the drop-in FILE rule where a "
            "foreign file is refused",
        ),
    )

    def test_framework_status_and_predicates(self) -> None:
        wrong = []
        for case, candidates, probe_result, rc_text, expected, why in self.STATES:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                present = root / "bash_completion"
                present.write_text("# fake framework\n", encoding="utf-8")
                resolved = [str(present) if c == "<PRESENT>" else c for c in candidates]
                rc = root / ".bashrc"
                if rc_text is not None:
                    rc.write_text(rc_text, encoding="utf-8")
                status = completion.completion_framework_status(
                    "bash",
                    entry_script_candidates=resolved,
                    probe=lambda: probe_result,
                    rc_path=rc,
                )
            got = (
                status.present,
                status.reachable,
                status.rc_sources_it,
                status.rc_has_stanza,
            )
            if got != expected:
                wrong.append(
                    f"  {case}:\n"
                    f"    - expected (present, reachable, rc_sources_it, rc_has_stanza) "
                    f"{expected}, got {got}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(wrong, [])

        # Derived predicates follow facts
        for present, reachable, effective, needs in (
            (True, completion.REACHABLE_YES, True, False),
            (True, completion.REACHABLE_NO, False, True),
            (False, completion.REACHABLE_NO, False, False),
            (True, completion.REACHABLE_UNKNOWN, False, False),
        ):
            status = completion.FrameworkStatus(
                shell="bash", present=present, reachable=reachable
            )
            self.assertEqual(
                (status.effective, status.needs_remediation), (effective, needs)
            )

        # Shell with no check reports unknown
        for shell in ("zsh", "fish"):
            status = completion.completion_framework_status(shell)
            self.assertEqual(status.reachable, completion.REACHABLE_UNKNOWN, shell)
            self.assertFalse(status.needs_remediation, shell)
            self.assertIn(shell, status.detail)

        # Status check writes nothing
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = root / "bash_completion"
            entry.write_text("# fake\n", encoding="utf-8")
            rc = root / ".bashrc"
            rc.write_text("export FOO=1\n", encoding="utf-8")
            before = {p: p.read_bytes() for p in (entry, rc)}
            before_names = sorted(p.name for p in root.iterdir())
            completion.completion_framework_status(
                "bash",
                entry_script_candidates=[str(entry)],
                probe=lambda: (completion.REACHABLE_NO, "unset"),
                rc_path=rc,
            )
            self.assertEqual({p: p.read_bytes() for p in (entry, rc)}, before)
            self.assertEqual(sorted(p.name for p in root.iterdir()), before_names)

    def test_probe_bash_completion_loaded(self) -> None:
        seen = {}

        def fake_run(argv, **kwargs):
            seen["argv"] = argv
            return subprocess.CompletedProcess(argv, 0, "2\n", "")

        with mock.patch.object(completion.subprocess, "run", side_effect=fake_run):
            verdict, detail = completion.probe_bash_completion_loaded()
        self.assertEqual(verdict, completion.REACHABLE_YES)
        self.assertEqual(
            seen["argv"],
            ["bash", "-ic", "echo ${BASH_COMPLETION_VERSINFO-}"],
        )
        self.assertIn("2", detail)

        # Probe failure modes are unknown
        failures = (
            ("no bash on PATH", FileNotFoundError()),
            ("timeout", subprocess.TimeoutExpired(cmd="bash", timeout=5)),
            ("OSError", OSError("boom")),
        )
        for case, exc in failures:
            with mock.patch.object(completion.subprocess, "run", side_effect=exc):
                verdict, detail = completion.probe_bash_completion_loaded()
            self.assertEqual(
                verdict,
                completion.REACHABLE_UNKNOWN,
                f"{case} must be UNKNOWN, not a confident negative",
            )
            self.assertTrue(detail, f"{case} must explain itself")

        # Nonzero exit -> unknown
        with mock.patch.object(
            completion.subprocess,
            "run",
            return_value=subprocess.CompletedProcess(["bash"], 2, "", "err"),
        ):
            self.assertEqual(
                completion.probe_bash_completion_loaded()[0],
                completion.REACHABLE_UNKNOWN,
            )
        # Empty value from successful probe -> REACHABLE_NO
        with mock.patch.object(
            completion.subprocess,
            "run",
            return_value=subprocess.CompletedProcess(["bash"], 0, "\n", ""),
        ):
            self.assertEqual(
                completion.probe_bash_completion_loaded()[0], completion.REACHABLE_NO
            )
        # Last non-empty line
        with mock.patch.object(
            completion.subprocess,
            "run",
            return_value=subprocess.CompletedProcess(
                ["bash"], 0, "bash: no job control in this shell\n2\n", ""
            ),
        ):
            self.assertEqual(
                completion.probe_bash_completion_loaded()[0], completion.REACHABLE_YES
            )


class RcStanzaTests(unittest.TestCase):
    """E-03/E-04: the fenced rc stanza, the only thing in this feature that writes a dotfile.

    EVERY ASSERTION RUNS AGAINST A FIXTURE HOME. The real `~/.bashrc` is never touched by these
    tests, which matters concretely: the maintainer's live file already carries a hand-added stanza,
    and a test that wrote there would be editing a co-worker's artifact.

    The BYTE COMPARISON is the load-bearing assertion in the non-consenting rows. "No write" is not
    provable by reading a status string; it is provable by the file being unchanged byte for byte.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        self.rc = self.home / ".bashrc"
        self.addCleanup(self._tmp.cleanup)

    def test_rc_snippet_and_install_behavior(self) -> None:
        # Snippet carries versinfo guard and paired fences
        for fenced in (False, True):
            snippet = completion.remediation_snippet(fenced=fenced)
            self.assertIn("BASH_COMPLETION_VERSINFO", snippet, f"fenced={fenced}")
            self.assertIn("shopt -oq posix", snippet, f"fenced={fenced}")
            self.assertIn("/usr/share/bash-completion/bash_completion", snippet)
        fenced = completion.remediation_snippet(fenced=True)
        self.assertTrue(fenced.startswith(completion.RC_FENCE_OPEN))
        self.assertTrue(fenced.rstrip("\n").endswith(completion.RC_FENCE_CLOSE))
        self.assertNotEqual(completion.RC_FENCE_OPEN, completion.RC_FENCE_CLOSE)

        # Without consent, file is byte-identical
        self.rc.write_text("export FOO=1\n", encoding="utf-8")
        before = self.rc.read_bytes()
        outcome = completion.install_rc_stanza(self.rc, consent=False)
        self.assertEqual(outcome["action"], "declined")
        self.assertEqual(self.rc.read_bytes(), before)

        # Dry run reports without writing
        outcome = completion.install_rc_stanza(self.rc, consent=True, dry_run=True)
        self.assertEqual(outcome["action"], "written")
        self.assertEqual(self.rc.read_bytes(), before)

        # Consent appends inside fences and preserves existing content
        original = "export FOO=1\nalias ll='ls -l'\n"
        self.rc.write_text(original, encoding="utf-8")
        outcome = completion.install_rc_stanza(self.rc, consent=True)
        self.assertEqual(outcome["action"], "written")
        body = self.rc.read_text(encoding="utf-8")
        self.assertTrue(body.startswith(original))
        self.assertIn(completion.RC_FENCE_OPEN, body)
        self.assertIn(completion.RC_FENCE_CLOSE, body)
        self.assertIn("BASH_COMPLETION_VERSINFO", body)

        # Second consenting run is a reported no-op ("already")
        after_first = self.rc.read_bytes()
        outcome = completion.install_rc_stanza(self.rc, consent=True)
        self.assertEqual(outcome["action"], "already")
        self.assertEqual(self.rc.read_bytes(), after_first)

        # Hand-added stanza counts as already satisfied
        self.rc.write_text(
            "# mine\n" + completion.remediation_snippet(fenced=True) + "\n",
            encoding="utf-8",
        )
        before_hand = self.rc.read_bytes()
        outcome = completion.install_rc_stanza(self.rc, consent=True)
        self.assertEqual(outcome["action"], "already")
        self.assertEqual(self.rc.read_bytes(), before_hand)

        # Absent rc is reported, never created
        self.rc.unlink()
        self.assertFalse(self.rc.exists())
        outcome = completion.install_rc_stanza(self.rc, consent=True)
        self.assertEqual(outcome["action"], "absent")
        self.assertFalse(self.rc.exists())
        self.assertIn("does not exist", outcome["detail"])

        # File without trailing newline is handled properly
        self.rc.write_text("export FOO=1", encoding="utf-8")
        completion.install_rc_stanza(self.rc, consent=True)
        lines = self.rc.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "export FOO=1")
        self.assertIn(completion.RC_FENCE_OPEN, lines)

        # Atomic write and error cleanup
        self.rc.write_text("export FOO=1\n", encoding="utf-8")
        before_atomic = self.rc.read_bytes()
        with mock.patch.object(completion.os, "replace", side_effect=OSError("nope")):
            with self.assertRaises(OSError):
                completion.install_rc_stanza(self.rc, consent=True)
        self.assertEqual(self.rc.read_bytes(), before_atomic)
        self.assertEqual([p.name for p in self.home.iterdir()], [".bashrc"])

    def test_rc_removal_behavior(self) -> None:
        # Install then remove round trips byte-for-byte
        original = "export FOO=1\n"
        self.rc.write_text(original, encoding="utf-8")
        before = self.rc.read_bytes()
        completion.install_rc_stanza(self.rc, consent=True)
        self.assertNotEqual(self.rc.read_bytes(), before)
        outcome = completion.remove_rc_stanza(self.rc)
        self.assertEqual(outcome["action"], "removed")
        self.assertEqual(self.rc.read_bytes(), before)
        self.assertEqual(completion.remove_rc_stanza(self.rc)["action"], "none")

        # Foreign rc block left alone
        self.rc.write_text(
            "export FOO=1\n# >>> grok installer >>>\nx=1\n# <<< grok installer <<<\n",
            encoding="utf-8",
        )
        before_foreign = self.rc.read_bytes()
        self.assertEqual(completion.remove_rc_stanza(self.rc)["action"], "none")
        self.assertEqual(self.rc.read_bytes(), before_foreign)

        # Unterminated fence is never truncated
        unterminated = (
            f"export FOO=1\n{completion.RC_FENCE_OPEN}\nhalf a stanza\nexport KEEP=2\n"
        )
        self.rc.write_text(unterminated, encoding="utf-8")
        outcome = completion.remove_rc_stanza(self.rc)
        self.assertEqual(outcome["action"], "none")
        self.assertEqual(self.rc.read_text(encoding="utf-8"), unterminated)
        self.assertIn("export KEEP=2", self.rc.read_text(encoding="utf-8"))


class CompletionEffectivenessMessageTests(_DropInFixture):
    """E-02/E-04: WHAT THE USER IS TOLD, which is where the defect actually lived.

    THE REGRESSION THAT MATTERS IS A STRING PAIR. The install was correct; what was broken was a
    green `ok` line paired with "start a new shell to pick it up", printed unconditionally. A user
    who trusts that output concludes the tool is broken, which is precisely what happened. So these
    tests pin the OUTPUT, not the predicate: in the non-reachable state there must be no `OK` status
    and no restart instruction.

    BOTH MESSAGE SITES ARE COVERED SEPARATELY (the `aw completion install` verb and the
    `aw setup`/`aw install` flow's `_configure_completion`), because the defect was reachable from
    either and fixing one would leave the other lying.
    """

    #: (case, injected status kwargs, substrings that MUST appear, substrings that must NOT, why)
    MESSAGE_CASES = (
        (
            "reachable",
            dict(present=True, reachable=completion.REACHABLE_YES),
            ("OK", "completion installed in", "start a new"),
            ("will NOT take effect", "WARN"),
            "the message that was always correct must be preserved verbatim in its own case; a fix "
            "that warns at everyone is a new defect",
        ),
        (
            "present but not reachable",
            dict(
                present=True,
                reachable=completion.REACHABLE_NO,
                entry_script="/usr/share/bash-completion/bash_completion",
            ),
            (
                "WARN",
                "will NOT take effect",
                "BASH_COMPLETION_VERSINFO",
                "NOT loaded in an interactive non-login shell",
            ),
            ("OK       bash completion installed", "start a new bash shell (or run"),
            "THE WHOLE DEFECT: an install that cannot work must not be reported `ok`, and must not "
            "tell the user to do the one thing that does not help",
        ),
        (
            "absent",
            dict(present=False, reachable=completion.REACHABLE_NO),
            ("WARN", "not installed on this system", "bash-completion"),
            ("OK       bash completion installed", "start a new bash shell (or run"),
            "different cause, different advice: install a package. Printing an rc snippet here "
            "would be advice that cannot possibly work",
        ),
        (
            "unknown",
            dict(
                present=True,
                reachable=completion.REACHABLE_UNKNOWN,
                detail="the `bash -ic` probe timed out after 5s",
            ),
            ("OK", "completion installed in", "could not verify", "probe timed out"),
            ("will NOT take effect",),
            "an unmeasured state must claim NEITHER outcome; asserting failure from a timeout "
            "would slander a working setup",
        ),
    )

    def _render(self, **status_kwargs):
        buf = io.StringIO()
        term = Term(stream=buf, color=False)
        status = completion.FrameworkStatus(shell="bash", **status_kwargs)
        cli._report_completion_effectiveness(
            term,
            "bash",
            installed_in="/fixture/bash-completion/completions",
            offer_rc_write=False,
            status_obj=status,
        )
        return buf.getvalue()

    def test_each_state_is_reported_honestly(self) -> None:
        wrong = []
        for case, kwargs, needles, forbidden, why in self.MESSAGE_CASES:
            out = self._render(**kwargs)
            problems = []
            for needle in needles:
                if needle not in out:
                    problems.append(f"missing {needle!r}")
            for bad in forbidden:
                if bad in out:
                    problems.append(f"must NOT contain {bad!r}")
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    output was:\n{out}\n"
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(wrong, [])

        # Non-reachable prints pasteable fix
        out = self._render(
            present=True,
            reachable=completion.REACHABLE_NO,
            entry_script="/usr/share/bash-completion/bash_completion",
        )
        for line in completion.remediation_snippet().splitlines():
            self.assertIn(line.strip(), out)

        # Already stanza'd rc reported as nothing to add
        out = self._render(
            present=True,
            reachable=completion.REACHABLE_NO,
            entry_script="/usr/share/bash-completion/bash_completion",
            rc_path=self.home / ".bashrc",
            rc_has_stanza=True,
        )
        self.assertIn("already carries", out)
        self.assertNotIn(completion.RC_FENCE_OPEN, out)

        # Failing status check never fails install
        buf = io.StringIO()
        term = Term(stream=buf, color=False)
        with mock.patch.object(
            completion, "completion_framework_status", side_effect=RuntimeError("boom")
        ):
            cli._report_completion_effectiveness(
                term, "bash", installed_in="/fixture", offer_rc_write=False
            )
        out = buf.getvalue()
        self.assertIn("installed in", out)
        self.assertIn("could not check", out)

    def test_end_to_end_verb_and_setup_flow_report_non_reachable_state(self) -> None:
        self.rc = self.home / ".bashrc"
        self.rc.write_text("export FOO=1\n", encoding="utf-8")
        before = self.rc.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            entry = Path(tmp) / "bash_completion"
            entry.write_text("# fake\n", encoding="utf-8")
            with (
                mock.patch.object(
                    completion, "_BASH_COMPLETION_ENTRY_SCRIPTS", (str(entry),)
                ),
                mock.patch.object(
                    completion,
                    "probe_bash_completion_loaded",
                    return_value=(completion.REACHABLE_NO, "unset"),
                ),
                mock.patch.object(cli.sys.stdin, "isatty", return_value=False),
            ):
                rc, out = _run(["completion", "install", "--shell", "bash"])
        self.assertEqual(rc, 0, out)
        self.assertIn("will NOT take effect", out)
        self.assertNotIn("start a new bash shell (or run", out)
        self.assertIn("BASH_COMPLETION_VERSINFO", out)
        self.assertEqual(self.rc.read_bytes(), before)

        # Setup flow
        buf = io.StringIO()
        term = Term(stream=buf, color=False)
        with tempfile.TemporaryDirectory() as tmp:
            entry = Path(tmp) / "bash_completion"
            entry.write_text("# fake\n", encoding="utf-8")
            with (
                mock.patch.dict(os.environ, {"SHELL": "/usr/bin/bash"}),
                mock.patch.object(
                    completion, "_BASH_COMPLETION_ENTRY_SCRIPTS", (str(entry),)
                ),
                mock.patch.object(
                    completion,
                    "probe_bash_completion_loaded",
                    return_value=(completion.REACHABLE_NO, "unset"),
                ),
                mock.patch.object(cli, "input", create=True) as m_input,
            ):
                cli._configure_completion(
                    argparse.Namespace(completion="bash", yes=True), term
                )
        out = buf.getvalue()
        self.assertIn("will NOT take effect", out)
        self.assertNotIn("Start a new bash shell to pick it up", out)
        m_input.assert_not_called()
        self.assertEqual(self.rc.read_bytes(), before)


class RcWriteOfferTests(_DropInFixture):
    """E-03/E-04: the consent gate on the rc write, which is the whole safety story.

    FOUR NON-CONSENTING PATHS EACH PROVE THE SAME THING BY BYTE COMPARISON: `--yes`, a non-TTY, a
    declined prompt, and EOF/interrupt. They are separate tests rather than a table because each
    exercises a different MECHANISM (a flag, `isatty`, a reply, an exception), and a table row
    cannot express "and `input()` was never even called".

    WHY `--yes` MUST NOT CONSENT, since it is the row most likely to be "simplified" later: the
    precedent is explicit in this codebase (`_configure_completion` and `_configure_runner_profiles`
    both return early under `--yes` because preauthorizing install mutations is not authorizing a
    user-scoped choice), and an rc write is further from an install mutation than either of those.
    """

    def setUp(self) -> None:
        super().setUp()
        self.rc = self.home / ".bashrc"
        self.rc.write_text("export FOO=1\n", encoding="utf-8")
        self.before = self.rc.read_bytes()

    def _offer(self, *, assume_yes: bool, isatty: bool, reply=None):
        buf = io.StringIO()
        term = Term(stream=buf, color=False)
        patch = (
            mock.patch.object(cli, "input", create=True, return_value=reply)
            if reply is not None
            else mock.patch.object(cli, "input", create=True)
        )
        with (
            mock.patch.object(cli.sys.stdin, "isatty", return_value=isatty),
            patch as m_input,
        ):
            outcome = cli._offer_rc_stanza_write(
                term, "bash", rc_path=self.rc, assume_yes=assume_yes
            )
        return outcome, buf.getvalue(), m_input

    def test_rc_write_offer_non_consenting_and_absent(self) -> None:
        # --yes does not consent and never prompts
        outcome, out, m_input = self._offer(assume_yes=True, isatty=True)
        self.assertEqual(outcome["action"], "declined")
        m_input.assert_not_called()
        self.assertIn("--yes does not consent", out)
        self.assertEqual(self.rc.read_bytes(), self.before)

        # non-tty writes nothing and never prompts
        outcome, out, m_input = self._offer(assume_yes=False, isatty=False)
        self.assertEqual(outcome["action"], "declined")
        m_input.assert_not_called()
        self.assertEqual(self.rc.read_bytes(), self.before)

        # declining at the prompt writes nothing
        outcome, out, m_input = self._offer(assume_yes=False, isatty=True, reply="n")
        self.assertEqual(outcome["action"], "declined")
        m_input.assert_called_once()
        self.assertEqual(self.rc.read_bytes(), self.before)

        # empty answer declines because the default is no
        outcome, out, m_input = self._offer(assume_yes=False, isatty=True, reply="")
        self.assertEqual(outcome["action"], "declined")
        self.assertEqual(self.rc.read_bytes(), self.before)
        prompt = m_input.call_args[0][0]
        self.assertIn("[y/N]", prompt)

        # EOF declines rather than writing
        buf = io.StringIO()
        term = Term(stream=buf, color=False)
        with (
            mock.patch.object(cli.sys.stdin, "isatty", return_value=True),
            mock.patch.object(cli, "input", create=True, side_effect=EOFError),
        ):
            outcome = cli._offer_rc_stanza_write(
                term, "bash", rc_path=self.rc, assume_yes=False
            )
        self.assertEqual(outcome["action"], "declined")
        self.assertEqual(self.rc.read_bytes(), self.before)

        # Absent rc is reported, not created
        self.rc.unlink()
        outcome, out, _ = self._offer(assume_yes=False, isatty=True, reply="y")
        self.assertEqual(outcome["action"], "absent")
        self.assertFalse(self.rc.exists())
        self.assertIn("does not exist", out)

    def test_rc_write_offer_consenting(self) -> None:
        outcome, out, _ = self._offer(assume_yes=False, isatty=True, reply="y")
        self.assertEqual(outcome["action"], "written")
        body = self.rc.read_text(encoding="utf-8")
        self.assertTrue(body.startswith("export FOO=1\n"))
        self.assertIn(completion.RC_FENCE_OPEN, body)
        self.assertIn(completion.RC_FENCE_CLOSE, body)
        self.assertIn("exec bash", out)
        # And a second consent is a reported no-op, not a duplicate.
        outcome2, out2, _ = self._offer(assume_yes=False, isatty=True, reply="y")
        self.assertEqual(outcome2["action"], "already")
        self.assertEqual(body, self.rc.read_text(encoding="utf-8"))

    def test_uninstall_rc_stanza_offer(self) -> None:
        completion.install_rc_stanza(self.rc, consent=True)
        with mock.patch.dict(os.environ, {"SHELL": "/usr/bin/bash"}):
            with (
                mock.patch.object(cli.sys.stdin, "isatty", return_value=True),
                mock.patch.object(cli, "input", create=True, return_value="y"),
            ):
                rc, out = _run(["completion", "uninstall", "--shell", "bash"])
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.rc.read_bytes(), self.before)
        self.assertIn("removed the fenced", out)

        # Uninstall under yes leaves the stanza
        completion.install_rc_stanza(self.rc, consent=True)
        after_write = self.rc.read_bytes()
        with mock.patch.dict(os.environ, {"SHELL": "/usr/bin/bash"}):
            with mock.patch.object(cli.sys.stdin, "isatty", return_value=False):
                rc, out = _run(["completion", "uninstall", "--shell", "bash"])
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.rc.read_bytes(), after_write)
        self.assertIn("still carries", out)

        # Uninstall is silent when there is no stanza
        completion.remove_rc_stanza(self.rc)
        with mock.patch.dict(os.environ, {"SHELL": "/usr/bin/bash"}):
            with mock.patch.object(cli.sys.stdin, "isatty", return_value=True):
                rc, out = _run(["completion", "uninstall", "--shell", "bash"])
        self.assertEqual(rc, 0, out)
        self.assertNotIn("bashrc", out)
        self.assertEqual(self.rc.read_bytes(), self.before)


if __name__ == "__main__":
    unittest.main()
