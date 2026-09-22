"""Tests for ttywedge Order 01 (g40w37): a nested `aw` must never block on a prompt.

Incident: a driver-spawned `aw ipd finalize` wedged for 1h49m holding its run lock, leaving the plan
`approved` in pending/ while the run reported `complete`. `ipd_lifecycle.run_finalize` decided it could
prompt from `sys.stdin.isatty()` alone, and the driver spawned it with stdout/stderr piped but stdin
INHERITED, so the child saw the operator's terminal and called `input()` for an answer nobody could
type, because the prompt itself went into a pipe.

Two independent layers are asserted here, because each alone would have prevented the incident and
neither is redundant: the CALLEE must not treat an inherited TTY as consent, and the CALLER must not
hand a child a terminal at all.

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: vary one input and
assert one bool. The tables group BY LAYER, which is the boundary that matters here: the callee's
predicate, the callee's real source, the caller's launch sites, and the completeness of the owner set
the caller guard is scoped to.

THE INTERACTIVE ROWS AND THE NON-INTERACTIVE ROWS SHARE ONE TABLE, which is the load-bearing decision
in the predicate matrix. The two failure directions are opposite and both are real: a predicate that
returned False for everything satisfies every non-interactive row while silently removing every
legitimate prompt a human relies on, and one that returned True for everything satisfies the
human-terminal row while REPRODUCING THE ORIGINAL INCIDENT exactly. Neither can pass the table, and
the failure message says which direction collapsed.

HOST IS A COLUMN, NOT A CLASS, in the caller table, and the PARITY claim between the two drivers is
kept and stated explicitly on measured values. A fix landing in one host only must not pass, and that
is a property OF THE PAIR: no per-host test can express it, which is precisely why the old form
counted across both and why the count is asserted per module here with the equality checked after the
loop.

COUNTS ARE MINIMA, NOT EXACT, AND THAT IS DELIBERATE. The threshold history is recorded in the rows:
it has twice been RE-BASED (`818uru` moved `run_checked` into `runner_shared`, `ct4w0a` moved
`driver_begin`) and never LOWERED. A minimum fails when a launcher is deleted while tolerating one
being added, and the UNIVERSAL beside it (every non-exempt launcher denies stdin) is what makes the
count non-vacuous, since a count can be satisfied while one site is uncovered.

Tests that are NOT rows carry a one-line docstring saying why they stay separate.
"""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

REPO_ROOT = Path(__file__).resolve().parents[1]
DRIVERS = ("agent_workflows/oc_runipd.py", "agent_workflows/agy_runipd.py")

# rununify 05 (`ct4w0a`) E-03, per the maintainer's OQ-03 ruling: THE OWNER SET, not the driver files.
# A nested-`aw` launcher may now live in `runner_shared` (`run_checked` since `818uru`, `driver_begin`
# since `ct4w0a`), so a guard keyed to FILES has to be edited every time a symbol moves, and each such
# edit is an opportunity to weaken it by accident. Keyed to the owner set it states the property that
# actually matters -- every nested `aw` launch denies stdin, WHEREVER it lives -- and stops needing
# maintenance. The set must list every module that may hold one; a launcher added to a module NOT
# listed here would be invisible, which `OwnerSetCompletenessTests` below is what refuses.
OWNER_SET = DRIVERS + ("agent_workflows/runner_shared.py",)


class _FakeStream:
    def __init__(self, tty: bool, raises: type[BaseException] | None = None) -> None:
        self._tty = tty
        self._raises = raises

    def isatty(self) -> bool:
        if self._raises is not None:
            raise self._raises("detached")
        return self._tty


def _interactive(
    *,
    stdin_tty: bool,
    stdout_tty: bool,
    is_agent: bool = False,
    is_json: bool = False,
    env: dict[str, str] | None = None,
    stdin_raises: type[BaseException] | None = None,
) -> bool:
    """Re-evaluate run_finalize's predicate in isolation.

    Mirrors the implementation exactly; the AST test below pins that the real code still carries the
    same conditions, so this cannot silently drift into testing a copy.
    """
    import os

    environ = env if env is not None else {}

    def is_tty(stream: object) -> bool:
        try:
            return bool(getattr(stream, "isatty", None) and stream.isatty())  # type: ignore[union-attr]
        except (ValueError, OSError):
            return False

    forced = any(
        str(environ.get(var, "")).strip().lower() not in ("", "0", "false", "no")
        for var in ("AW_NONINTERACTIVE", "CI")
    )
    assert os is not None
    return (
        not (is_agent or is_json)
        and not forced
        and is_tty(_FakeStream(stdin_tty, stdin_raises))
        and is_tty(_FakeStream(stdout_tty))
    )


class PredicateMatrixTests(unittest.TestCase):
    """E-01: the full matrix of inputs that decide whether `run_finalize` may prompt.

    ONE table replaces eight tests. Every one called `_interactive` with a different keyword
    combination and asserted a bool; two of them already looped over a list of values inline, which is
    the table wanting to exist. Each varying input - the two stream states, the two output modes, the
    env override, and whether `isatty` RAISES - is a column.

    Why the table beats the eight: a single boolean expression decides every row, so the realistic
    regression is one conjunct being dropped or inverted, and that moves a legible GROUP of cells. All
    four falsey-env rows failing together means the value parsing went; both mode rows means the
    agent/json guard went; the incident row alone means the stdout requirement was removed, which is
    the exact conjunct the incident turned on. Eight tests report any of these as unrelated `False is
    not true` lines that name no input at all.

    THE ONE INTERACTIVE-EXPECTING ROW IS LOAD-BEARING FOR EVERY OTHER ROW. A predicate returning False
    unconditionally satisfies all nine non-interactive rows while removing every legitimate prompt in
    the tool, and that would be a silent, hard-to-notice regression precisely because nothing wedges.
    Conversely a predicate returning True satisfies the interactive rows while reproducing the 1h49m
    wedge. Keeping both senses here is what makes the table unsatisfiable by either degenerate
    implementation, and the failure message names the direction.
    """

    #: (case, stdin is a tty, stdout is a tty, is_agent, is_json, the env mapping (None for empty),
    #: the exception `stdin.isatty()` raises (None for none), whether the predicate must say
    #: INTERACTIVE, why this row exists)
    MATRIX = (
        (
            "stdin an inherited TTY, stdout piped",
            True,
            False,
            False,
            False,
            None,
            None,
            False,
            "THE INCIDENT, EXACTLY: this combination wedged a driver-spawned `aw ipd finalize` for "
            "1h49m holding its run lock. The child saw the operator's real terminal on stdin while its "
            "prompt went into a pipe, so it waited for an answer nobody could see it asking for. "
            "Requiring stdout too is what makes the prompt VISIBLE before it is asked",
        ),
        (
            "a genuine human terminal on both streams",
            True,
            True,
            False,
            False,
            None,
            None,
            True,
            "THE ONLY ROW THAT MUST BE INTERACTIVE, and it carries the whole table: while it is broken "
            "every other row here is VACUOUS, because a predicate returning False for everything "
            "satisfies all of them - and it would do so while silently deleting every legitimate "
            "prompt in the tool, a regression nothing wedges to reveal",
        ),
        (
            "AW_NONINTERACTIVE=1 on a real terminal",
            True,
            True,
            False,
            False,
            {"AW_NONINTERACTIVE": "1"},
            None,
            False,
            "THE EXPLICIT OVERRIDE must beat a real TTY, because it is how an operator says 'do not "
            "stop for me' when running a long unattended job from their own terminal. A predicate that "
            "checked the streams first and the env second would fail exactly here",
        ),
        (
            "CI=true on a real terminal",
            True,
            True,
            False,
            False,
            {"CI": "true"},
            None,
            False,
            "THE CONVENTIONAL CI SIGNAL, honored as an alias of the override above so no pipeline has "
            "to know this tool's own variable name. A prompt in CI is an infinite hang with a log that "
            "ends mid-sentence",
        ),
        (
            "CI set to the empty string",
            True,
            True,
            False,
            False,
            {"CI": ""},
            None,
            True,
            "A PRESENT-BUT-EMPTY VARIABLE IS NOT A SIGNAL. `CI` is exported empty by plenty of shells "
            "and wrappers, and a mere presence check would make every one of those developers' "
            "terminals silently non-interactive",
        ),
        (
            "CI=0",
            True,
            True,
            False,
            False,
            {"CI": "0"},
            None,
            True,
            "THE EXPLICIT OFF VALUE: `0` must mean off, not 'set'. This is the row a truthiness test on "
            "the raw string fails, since any non-empty string is truthy in Python",
        ),
        (
            "CI=false",
            True,
            True,
            False,
            False,
            {"CI": "false"},
            None,
            True,
            "the word-spelled off value, kept beside `0` so the rule reads as a small closed set of "
            "falsey spellings rather than one numeric special case",
        ),
        (
            "CI=no",
            True,
            True,
            False,
            False,
            {"CI": "no"},
            None,
            True,
            "the third falsey spelling. These four rows must be read TOGETHER: all of them failing at "
            "once means value parsing was replaced by a presence check, which would turn off prompting "
            "for every operator whose shell exports CI empty",
        ),
        (
            "CI set to whitespace only",
            True,
            True,
            False,
            False,
            {"CI": "  "},
            None,
            True,
            "the whitespace case, which pins that the value is STRIPPED before comparison. A "
            "`.strip()` dropped from the implementation fails only here",
        ),
        (
            "--agent mode on a real terminal",
            True,
            True,
            True,
            False,
            None,
            None,
            False,
            "AGENT MODE IS NON-INTERACTIVE BY DEFINITION: there is no human in the loop to answer, so a "
            "prompt is a hang. An agent may well be driving from a terminal it inherited, which is why "
            "this cannot be inferred from the streams",
        ),
        (
            "--json mode on a real terminal",
            True,
            True,
            False,
            True,
            None,
            None,
            False,
            "JSON MODE HAS NOWHERE TO PUT A PROMPT: the question would land in the middle of the "
            "document and corrupt it for the parser waiting on stdout. Kept as its own row beside "
            "`--agent` so a refactor cannot drop one of the two disjuncts unnoticed",
        ),
        (
            "neither stream a terminal",
            False,
            False,
            False,
            False,
            None,
            None,
            False,
            "THE ORDINARY PIPED CASE, e.g. output redirected to a file. It is the baseline the incident "
            "row differs from by a single input, which is what isolates the inherited-stdin conjunct",
        ),
        (
            "stdin.isatty() raises ValueError",
            True,
            True,
            False,
            False,
            None,
            ValueError,
            False,
            "A CLOSED STREAM RAISES ValueError, and that must read as 'no terminal' rather than "
            "crashing. A traceback here would abort a finalize mid-transition, which is a worse "
            "outcome than the wedge this file is about",
        ),
        (
            "stdin.isatty() raises OSError",
            True,
            True,
            False,
            False,
            None,
            OSError,
            False,
            "the other exception a detached or exotic stream raises. Both are caught, so the pair of "
            "rows states the rule is 'an unanswerable stream is not a terminal' rather than one "
            "hardcoded exception type",
        ),
    )

    def test_the_predicate_permits_a_prompt_only_for_a_real_answerable_human(self):
        wrong = []
        interactive_rows_broken = 0
        noninteractive_rows_broken = 0
        for (
            case,
            stdin_tty,
            stdout_tty,
            is_agent,
            is_json,
            env,
            stdin_raises,
            expected,
            why,
        ) in self.MATRIX:
            got = _interactive(
                stdin_tty=stdin_tty,
                stdout_tty=stdout_tty,
                is_agent=is_agent,
                is_json=is_json,
                env=env,
                stdin_raises=stdin_raises,
            )
            if got is not expected:
                if expected:
                    interactive_rows_broken += 1
                else:
                    noninteractive_rows_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    f"    - expected interactive={expected}, got {got!r}\n"
                    f"    - inputs: stdin_tty={stdin_tty}, stdout_tty={stdout_tty}, "
                    f"is_agent={is_agent}, is_json={is_json}, env={env!r}, "
                    f"stdin_raises={getattr(stdin_raises, '__name__', None)}\n"
                    f"    this row exists because: {why}"
                )
        direction = ""
        if noninteractive_rows_broken and not interactive_rows_broken:
            direction = (
                f" ALL {noninteractive_rows_broken} failing row(s) expect NON-interactive, so the "
                "predicate has widened and a nested `aw` can prompt again: that is the 1h49m wedge, "
                "reproduced."
            )
        elif interactive_rows_broken and not noninteractive_rows_broken:
            direction = (
                f" ALL {interactive_rows_broken} failing row(s) expect INTERACTIVE, so the predicate "
                "now refuses to prompt a real human. Every non-interactive row above proves nothing "
                "while that is true (a predicate returning False for everything satisfies them all), "
                "and the symptom is silent: prompts simply stop appearing, and nothing hangs to "
                "reveal it."
            )
        self.assertEqual(
            wrong,
            [],
            f"the interactivity predicate answered wrongly for {len(wrong)} of {len(self.MATRIX)} "
            f"input combinations.{direction} ONE boolean expression decides every row, so read the "
            "grouping: the four falsey-`CI` rows failing together means value parsing became a "
            "presence check (which silences prompts for every shell that exports CI empty); both mode "
            "rows means the agent/json guard went; the two raising rows means the exception handling "
            "went; the INCIDENT row alone means the stdout requirement was dropped, which is the exact "
            "conjunct the wedge turned on. FIX: this helper MIRRORS `ipd_lifecycle.run_finalize`, so a "
            "failure here means the mirror and the real predicate have diverged - check the source "
            "table below before editing either, and never fix a row by relaxing it.\n"
            + "\n".join(wrong),
        )


class CalleeSourceTests(unittest.TestCase):
    """E-01: pin that the real predicate still carries every condition the mirror above models.

    ONE table replaces four tests. Each read the same window of `ipd_lifecycle.py` and asserted one
    substring was present, so the needle is the only thing that varied.

    WHY THIS EXISTS AT ALL, since it is otherwise an odd thing to assert: the matrix above tests a
    MIRROR of the predicate, not the predicate itself, because the real one reads process-global
    `sys.stdin`/`sys.stdout` and the real environment. That mirror is worthless if the original drifts,
    so these needles are the seam. They are the cheapest possible check on the strongest possible
    claim: every condition the matrix models is still present in the shipped code.

    Why the table beats the four: all four needles are conditions of ONE expression, so a rewrite of
    that expression removes several at once - which is the shape of the actual risk - and one failure
    naming every missing condition says 'the predicate was rewritten' where four separate failures
    suggest four unrelated edits. THE WINDOW ANCHOR IS CHECKED FIRST and reported as its own problem,
    because if `forced_noninteractive` is gone every needle fails for a reason that has nothing to do
    with the needles.
    """

    #: (the substring the predicate's source must contain, why this row exists)
    NEEDLES = (
        (
            "_is_tty(_sys.stdout)",
            "THE CONJUNCT THE INCIDENT TURNED ON. Requiring stdout is what makes a prompt VISIBLE "
            "before it is asked; without it a child with stdin inherited and stdout piped asks a "
            "question into a pipe and waits forever",
        ),
        (
            "_is_tty(_sys.stdin)",
            "the other half of the stream requirement: an ANSWERABLE stream. Both must be named, "
            "because either one alone is satisfiable by a driver-spawned child",
        ),
        (
            "AW_NONINTERACTIVE",
            "THE EXPLICIT OVERRIDE must still be read from the environment. The drivers set it when "
            "spawning, so it is the belt to the stdin devnull's braces - and the only one that works "
            "for a nested `aw` a driver did not spawn itself",
        ),
        (
            "CI",
            "the conventional alias, so no pipeline has to know this tool's own variable name. A short "
            "needle deliberately: it only has to prove the variable is consulted, and the matrix above "
            "pins the value semantics",
        ),
        (
            "ctx.is_agent or ctx.is_json",
            "THE MODE GUARD, pinned as the whole disjunction rather than as two needles, because the "
            "risk is a refactor that keeps one branch and drops the other. Neither mode has a human to "
            "answer or anywhere to put the question",
        ),
    )

    def _predicate_src(self) -> str:
        src = (REPO_ROOT / "agent_workflows" / "ipd_lifecycle.py").read_text(
            encoding="utf-8"
        )
        i = src.find("forced_noninteractive")
        return "" if i < 0 else src[i - 400 : i + 700]

    def test_the_shipped_predicate_still_carries_every_modelled_condition(self):
        src = self._predicate_src()
        wrong = []
        if not src:
            wrong.append(
                "  the predicate itself:\n"
                "    - `forced_noninteractive` is not in `agent_workflows/ipd_lifecycle.py` at all, so "
                "the hardened predicate is GONE and every needle below fails for that one reason\n"
                "    this row exists because: this symbol is the window anchor every needle is "
                "measured against; reporting it separately stops five needle failures from being read "
                "as five independent edits"
            )
        else:
            for needle, why in self.NEEDLES:
                if needle not in src:
                    wrong.append(
                        f"  {needle!r}:\n"
                        "    - absent from the predicate's source window\n"
                        f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.NEEDLES)} conditions are missing from the shipped "
            "interactivity predicate. These needles are the SEAM between the real code and the mirror "
            "`_interactive` helper that `PredicateMatrixTests` exercises: the matrix is worthless if "
            "the original has drifted, which is the only thing this test can detect. All of them "
            "failing together means the expression was rewritten (check the window anchor line first); "
            "one failing means that condition was dropped. FIX: restore the condition in "
            "`ipd_lifecycle.py`, or - if the change is intended - update `_interactive` in this file in "
            "the SAME commit, because a mirror nobody updated is worse than no mirror.\n"
            + "\n".join(wrong),
        )


def _subprocess_calls(rel: str) -> list[tuple[int, set[str], str]]:
    """(lineno, kwargs, first-arg-source) for every subprocess.run/Popen in a module."""
    tree = ast.parse((REPO_ROOT / rel).read_text(encoding="utf-8"))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and ast.unparse(node.func) in (
            "subprocess.run",
            "subprocess.Popen",
        ):
            first = ast.unparse(node.args[0]) if node.args else ""
            out.append((node.lineno, {k.arg for k in node.keywords if k.arg}, first))
    return out


#: The `role` column of `CallerDevnullTests.MODULES`.
DRIVER = "driver (host-specific)"
SHARED = "shared by both drivers"


class CallerDevnullTests(unittest.TestCase):
    """E-02/E-03/E-04: every nested-`aw` launcher in the owner set denies stdin - an AST guard, not a grep.

    ONE table replaces three tests (`test_the_owner_set_has_nested_aw_call_sites`,
    `test_every_nested_aw_run_denies_stdin`, `test_symmetry_across_both_drivers`), which between them
    asserted the SAME universal twice and disagreed about how to count its population. The owning
    MODULE is now a row and its ROLE is a column, so the per-module population, the exemptions, and
    the universal are all stated once, per module, in one place.

    THE PARITY CLAIM IS KEPT AND IS ASSERTED ON MEASURED VALUES, after the loop. `oc_runipd` and
    `agy_runipd` must hold the same number of their OWN stdin-covered launchers, because a fix landing
    in one host only must not pass. That is a property of the PAIR and no per-host row can express it,
    which is exactly why the guard has always counted across both. It is checked on what was measured
    rather than on the expectations in the table, so a drift that moved both hosts equally still fails
    the per-module minimum while parity itself remains an independent, measured claim.

    COUNTS ARE MINIMA AND THE HISTORY MATTERS. The threshold has been RE-BASED TWICE AND NEVER
    LOWERED: the original form required at least 3 sites PER DRIVER FILE, which held only while every
    launcher lived in a driver; `818uru` moved `run_checked` into `runner_shared` and `ct4w0a` moved
    `driver_begin`, so per-file arithmetic broke while not one launcher lost its `stdin=`. A MINIMUM
    fails when a launcher is deleted and tolerates one being added. Beside it sits the UNIVERSAL -
    every non-exempt launcher denies stdin - which is strictly stronger than any count, since a count
    can be satisfied while one site is uncovered.

    THE agent `Popen` EXEMPTION IS COUNTED EXACTLY, not skipped silently. It is the host agent spawn
    (owned by backlog `qyaime`, not this plan), and an exact count is what stops a THIRD exemption
    appearing and quietly removing a site from the guard. That is the one number here that must not
    grow.

    MODULE EXISTENCE IS A COLUMN rather than a separate test: a renamed module would otherwise be
    silently skipped by every scan in this file, so the row fails loudly instead of passing vacuously.
    """

    # The nested-`aw` launchers: run_checked, driver_begin, driver_finalize in each driver. They pass
    # a prebuilt `argv`/`cmd` list, unlike the inline `['git', ...]` calls which cannot prompt.
    NESTED_AW_FIRST_ARGS = ("argv", "cmd")

    #: (module, role, MINIMUM nested-`aw` launch sites, EXACT count of exempt agent `Popen` spawns,
    #: MINIMUM non-exempt launchers that must all deny stdin, why this row exists)
    MODULES = (
        (
            "agent_workflows/oc_runipd.py",
            DRIVER,
            1,
            1,
            0,
            "THE OPENCODE DRIVER. Its counts were RE-BASED DOWN by hostdedup Order 01 (`li44r9`), "
            "which lifted its last two nested-`aw` launchers (`driver_finalize`, `set_plan_approved`) "
            "into the shared module after `818uru`/`ct4w0a` had already taken `run_checked` and "
            "`driver_begin`. THE COUNTS MOVED TO THE `runner_shared` ROW, WHICH ROSE BY THE SAME "
            "AMOUNT, which is the remedy this guard's own failure message prescribes for a launcher "
            "that MOVED, and not one launcher lost its `stdin=`. What remains here is the exempt agent "
            "`Popen`, still counted EXACTLY, so a second exemption cannot appear",
        ),
        (
            "agent_workflows/agy_runipd.py",
            DRIVER,
            1,
            1,
            0,
            "THE ANTIGRAVITY DRIVER, whose numbers must MATCH the row above. Both hosts run the same "
            "lifecycle, so a `stdin=` added to one and not the other is the drift the parity check "
            "exists to catch - and it is the realistic one, since a fix is written against whichever "
            "host reproduced the bug. Re-based with its twin by `li44r9`: PARITY IS PRESERVED AND IS "
            "NOW STRUCTURAL, because the launchers the two hosts used to keep in step by hand are one "
            "shared body they cannot diverge from",
        ),
        (
            "agent_workflows/runner_shared.py",
            SHARED,
            3,
            0,
            3,
            "THE SHARED MODULE, and the reason the guard was re-based off files onto an OWNER SET: it "
            "holds `run_checked` (`818uru`), `driver_begin` (`ct4w0a`), and now `driver_finalize` and "
            "`set_plan_approved` (`li44r9`), so a guard that inspected only the driver files would "
            "have STOPPED INSPECTING four launchers without any count going down. ITS MINIMUM ROSE AS "
            "THE DRIVERS' FELL, which is what makes the re-base a MOVE rather than a weakening: the "
            "owner-set total is asserted below and did not drop. It holds NO exempt `Popen`, because "
            "the host agent is spawned by the drivers and not from here",
        ),
    )

    #: The MINIMUM nested-`aw` launchers that must exist ACROSS the whole owner set, and must all deny
    #: stdin. Added by hostdedup Order 01 (`li44r9`) E-07 so the per-module re-base above cannot be
    #: performed as a net LOWERING: a launcher moved between two rows leaves this unchanged, while a
    #: launcher DELETED lowers it and fails. It is the number the per-module minima used to imply
    #: collectively, now stated explicitly because the modules' shares legitimately shift every time a
    #: symbol is lifted.
    MIN_OWNER_SET_LAUNCHERS = 3

    def _nested_aw_calls(self, rel: str):
        return [
            (lineno, kw, first)
            for lineno, kw, first in _subprocess_calls(rel)
            if first in self.NESTED_AW_FIRST_ARGS
        ]

    def test_every_nested_aw_launcher_in_the_owner_set_denies_stdin(self):
        wrong = []
        uncovered_total = 0
        total_launchers = 0
        own_covered: dict[str, int] = {}
        for rel, role, min_sites, exact_popen, min_launchers, why in self.MODULES:
            problems = []
            target = REPO_ROOT / rel
            if not target.is_file():
                problems.append(
                    "the module is named in OWNER_SET but DOES NOT EXIST, so every scan in this file "
                    "silently skips it; a renamed module must fail loudly rather than pass vacuously"
                )
                wrong.append(
                    f"  {rel} ({role}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
                continue
            src_lines = target.read_text(encoding="utf-8").splitlines()
            sites = self._nested_aw_calls(rel)
            popen = [(ln, kw, a) for ln, kw, a in sites if "Popen" in src_lines[ln - 1]]
            launchers = [s for s in sites if s not in popen]
            uncovered = [
                f"{rel}:{ln} (arg0={a})" for ln, kw, a in launchers if "stdin" not in kw
            ]
            uncovered_total += len(uncovered)
            total_launchers += len(launchers)
            own_covered[rel] = sum(1 for _ln, kw, _a in launchers if "stdin" in kw)
            # THE UNIVERSAL: no nested-`aw` launcher anywhere in the owner set may inherit a terminal.
            if uncovered:
                problems.append(
                    "these nested-`aw` launch sites do NOT deny stdin, so each can hand a child the "
                    f"operator's terminal: {uncovered!r}"
                )
            # NON-VACUITY: a universal over an empty set is trivially true, so the population is pinned.
            if len(sites) < min_sites:
                problems.append(
                    f"only {len(sites)} nested-`aw` launch site(s) found, expected at least "
                    f"{min_sites}; a launcher that VANISHED makes the universal above vacuous"
                )
            if len(launchers) < min_launchers:
                problems.append(
                    f"only {len(launchers)} non-exempt launcher(s) found, expected at least "
                    f"{min_launchers}"
                )
            if len(popen) != exact_popen:
                problems.append(
                    f"expected EXACTLY {exact_popen} exempt agent `Popen` spawn(s), found "
                    f"{len(popen)} at lines {[ln for ln, _kw, _a in popen]!r}; an extra exemption "
                    "means something else stopped being checked"
                )
            if problems:
                wrong.append(
                    f"  {rel} ({role}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        # THE OWNER-SET FLOOR (hostdedup Order 01, `li44r9`, E-07). The per-module minima above are
        # shares of one population, and a lift legitimately moves a launcher from one row to another. So
        # the population itself is asserted here, across every row, which is what makes such a re-base
        # provably a MOVE: shifting a launcher between rows leaves this untouched, while DELETING one
        # lowers it and fails no matter how the per-module numbers were edited.
        if total_launchers < self.MIN_OWNER_SET_LAUNCHERS:
            wrong.append(
                "  the owner set as a whole:\n"
                f"    - only {total_launchers} non-exempt nested-`aw` launcher(s) across every row, "
                f"expected at least {self.MIN_OWNER_SET_LAUNCHERS}\n"
                "    this row exists because: the per-module minima are SHARES of one population, so a "
                "lift that moves a launcher between modules is legitimate and must not fail, while a "
                "launcher DELETED must fail however the per-module numbers were re-based. Only this "
                "cross-row floor can tell those two apart"
            )
        # THE PARITY PROPERTY, on MEASURED values: a fix landing in one host only must not pass. It is
        # a property of the PAIR, so it cannot live in any single row above.
        if len(own_covered) == len(self.MODULES):
            a, b = DRIVERS
            if own_covered.get(a) != own_covered.get(b):
                wrong.append(
                    "  the two drivers' own stdin= coverage:\n"
                    f"    - {a} covers {own_covered.get(a)!r} of its own launchers while {b} covers "
                    f"{own_covered.get(b)!r}\n"
                    "    this row exists because: BOTH HOSTS RUN THE SAME LIFECYCLE, so a `stdin=` "
                    "added to one driver and not the other is the realistic drift (a fix gets written "
                    "against whichever host reproduced the bug). No per-host row can state this; it is "
                    "a property of the pair"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.MODULES)} owner-set modules (plus the cross-driver parity "
            f"check) are wrong; {uncovered_total} nested-`aw` launch site(s) can inherit a terminal. "
            "Read the grouping: an UNCOVERED site is the incident itself waiting to happen, so fix it "
            "by adding `stdin=subprocess.DEVNULL` at that call rather than by editing this table; a "
            "count BELOW its minimum means a launcher was deleted or renamed, which makes the "
            "universal vacuous - if a launcher legitimately MOVED, move its count to the receiving "
            "module's row (the threshold has been re-based twice and never lowered); an extra exempt "
            "`Popen` means a site stopped being checked and that number must not grow; a PARITY "
            "failure means one host was fixed and the other was not. FIX: if a launcher moved to a "
            "module not listed in OWNER_SET, add the module here - `OwnerSetCompletenessTests` below "
            "is what refuses to let it hide.\n" + "\n".join(wrong),
        )

    def test_guard_fails_on_an_injected_regression(self):
        """Kept separate: the subject is a SYNTHETIC snippet, not a module in the owner set.

        Every row above scans real shipped code, which can only ever prove the guard passes TODAY.
        This runs the same detection logic over a deliberately broken snippet to prove it would
        FAIL, which is a different claim and needs an input that must never exist in the tree.
        """
        snippet = (
            "import subprocess\n"
            "def f(cmd, repo):\n"
            "    return subprocess.run(cmd, cwd=repo, stdout=subprocess.PIPE)\n"
        )
        offenders = []
        for node in ast.walk(ast.parse(snippet)):
            if (
                isinstance(node, ast.Call)
                and ast.unparse(node.func) == "subprocess.run"
            ):
                kw = {k.arg for k in node.keywords if k.arg}
                first = ast.unparse(node.args[0]) if node.args else ""
                if first in self.NESTED_AW_FIRST_ARGS and "stdin" not in kw:
                    offenders.append(node.lineno)
        self.assertEqual(
            offenders, [3], "the AST guard must catch a nested-aw call missing stdin="
        )


class OwnerSetCompletenessTests(unittest.TestCase):
    """rununify 05 (`ct4w0a`) E-03: what an owner-set guard can miss, and what stops it.

    Re-basing from FILES onto an OWNER SET buys freedom from per-move edits, and it introduces exactly
    one new failure mode in exchange: a launcher added to a module that is not in `OWNER_SET` would
    never be inspected, so the guard above would keep passing while an unprotected nested `aw` shipped.
    That is a worse hole than the one the re-base closed, so the set's completeness is asserted rather
    than assumed. This class is the price of the ruling and it is deliberately paid here.

    ONE TABLE here replaces the two non-vacuity tests (`test_the_completeness_scan_would_catch_a_stray
    _launcher`, `test_the_semantic_detector_ignores_a_plain_git_invocation`). Both wrote a real
    temporary module under the package and asked `_semantic_nested_aw_sites` what it found, differing
    only in the SOURCE and therefore in whether anything should be found - which is the accept/reject
    sense, a column.

    BOTH SENSES MUST SHARE THAT TABLE, and here the reason is measured rather than theoretical. The
    driver guard identifies launchers by `arg0 in ('argv', 'cmd')`, which is precise inside the drivers
    and useless package-wide, because `cmd` is also what a plain `git` invocation is called: that
    filter yields 5 false positives across the package, all `git`/`--version` calls that cannot prompt
    for anything. So a detector that cried wolf would make the package-wide scan below unmaintainable
    and it would be TURNED OFF, while a detector that found nothing would let a stray launcher ship.
    One row proves recall, the other precision, and neither alone is worth anything.
    """

    # Nested-`aw` launches that live OUTSIDE the owner set, each with the reason it is not covered by
    # the stdin guard above. This is an ALLOWLIST and it is deliberately tiny: every entry is a hole,
    # and the scan below fails when a new one appears so the hole is a decision rather than a drift.
    EXEMPT_OUTSIDE_OWNER_SET: ClassVar[dict[str, int]] = {
        # PRE-EXISTING AND REPORTED, not introduced by `ct4w0a` (measured at its execution HEAD
        # 1171f7b2, before any change in this plan). These two are release GATES, not runner launchers:
        # they are invoked from a human-run `aw release-review`, they pass `--agent` (which makes the
        # child non-interactive on its own merits), and they build an INLINE literal argv rather than
        # naming it `argv`/`cmd`, which is why the original per-driver guard never saw them either.
        # They are NOT fixed here because `agent_workflows/release_readiness.py` is outside this plan's
        # declared `Scope-Paths`; the finding is filed instead, so the next reader inherits the fact
        # rather than re-discovering it.
        "agent_workflows/release_readiness.py": 2,
    }

    def _semantic_nested_aw_sites(self, rel: str) -> list[tuple[int, str, bool]]:
        """Nested-`aw` launches found by MEANING rather than by the first argument's NAME.

        WHY A SECOND DETECTOR. The guard above identifies launchers by `arg0 in ('argv', 'cmd')`,
        which is precise INSIDE the drivers and useless outside them: package-wide, `cmd` is what a
        plain `git` invocation is called too, so that filter yields false positives (measured: 5, all
        of them `git`/`--version` calls that cannot prompt for anything). This detector instead finds a
        function that BUILDS a nested-`aw` argv -- through the pin helpers or a literal
        `-m agent_workflows` -- and reports the subprocess launches inside it.
        """
        target = REPO_ROOT / rel
        if not target.is_file():
            return []
        try:
            src = target.read_text(encoding="utf-8")
        except OSError:
            return []
        if (
            "pinned_module_argv" not in src
            and "_AW_PIN_BOOTSTRAP" not in src
            and "_AW_PIN_PROBE" not in src
            and '"-m"' not in src
            and "'-m'" not in src
        ):
            return []
        tree = ast.parse(src)
        builders: dict[str, tuple[int, int]] = {}
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = ast.get_source_segment(src, fn) or ast.unparse(fn)
            if (
                "pinned_module_argv" in body
                or "_AW_PIN_BOOTSTRAP" in body
                or "_AW_PIN_PROBE" in body
                or '"-m", "agent_workflows"' in body
                or "'-m', 'agent_workflows'" in body
            ):
                builders[fn.name] = (fn.lineno, fn.end_lineno or fn.lineno)
        found: list[tuple[int, str, bool]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Attribute) and isinstance(
                    node.func.value, ast.Name
                ):
                    func_name = f"{node.func.value.id}.{node.func.attr}"
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id
                if func_name in ("subprocess.run", "subprocess.Popen"):
                    kw = {k.arg for k in node.keywords if k.arg}
                    for name, (start, end) in builders.items():
                        if start <= node.lineno <= end:
                            found.append((node.lineno, name, "stdin" in kw))
        return found

    #: (case, the module filename to write, its source, the EXACT `(function, stdin-covered)` pairs
    #: the detector must report, why this row exists)
    DETECTOR = (
        (
            "a stray nested-`aw` launcher in an unlisted module",
            "stray_launcher.py",
            "import subprocess\n"
            "def sneaky(repo):\n"
            "    argv = pinned_module_argv(['ipd', 'set', 'executed'])\n"
            "    return subprocess.run(argv, cwd=repo, stdout=subprocess.PIPE)\n",
            [("sneaky", False)],
            "RECALL: this is the hole the owner-set re-base created, so the scan below must SEE it. "
            "The expected pair also pins that it is reported as NOT stdin-covered, since a detector "
            "that found the site but misjudged its coverage would report a real hole as safe",
        ),
        (
            "a plain `git` invocation whose argv is called `cmd`",
            "benign_git.py",
            "import subprocess\n"
            "def commit(repo, paths):\n"
            "    cmd = ['git', 'commit', '-m', 'x', '--'] + paths\n"
            "    return subprocess.run(cmd, cwd=repo)\n",
            [],
            "PRECISION, and the reason this detector works by MEANING rather than by the `arg0` NAME "
            "the driver guard uses: measured, the name filter reports 5 false positives package-wide, "
            "all `git`/`--version` calls that cannot prompt. A scan that cried wolf on ordinary `git` "
            "calls would be turned off, taking the recall row's protection with it",
        ),
    )

    def test_the_semantic_detector_finds_stray_launchers_without_crying_wolf(self):
        wrong = []
        recall_rows_broken = 0
        precision_rows_broken = 0
        for case, filename, source, expected, why in self.DETECTOR:
            # A REAL file on disk under the package, and asserted through the SAME function the
            # package-wide scan uses, so a detector that stopped detecting fails here.
            with tempfile.TemporaryDirectory(dir=REPO_ROOT / "agent_workflows") as temp:
                module = Path(temp) / filename
                module.write_text(source, encoding="utf-8")
                rel = module.relative_to(REPO_ROOT).as_posix()
                got = [
                    (fn, covered)
                    for _ln, fn, covered in self._semantic_nested_aw_sites(rel)
                ]
            if got != expected:
                if expected:
                    recall_rows_broken += 1
                else:
                    precision_rows_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    f"    - expected the detector to report {expected!r}\n"
                    f"    - got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        direction = ""
        if recall_rows_broken and not precision_rows_broken:
            direction = (
                " The RECALL row failed, so the package-wide scan below is now blind: a nested-`aw` "
                "launcher added to an unlisted module would never be inspected by the stdin guard and "
                "would ship unprotected."
            )
        elif precision_rows_broken and not recall_rows_broken:
            direction = (
                " The PRECISION row failed, so the detector is now reporting ordinary `git` calls. "
                "That makes the scan below unmaintainable, and an unmaintainable scan gets turned off "
                "- taking the recall protection with it."
            )
        self.assertEqual(
            wrong,
            [],
            f"the semantic detector was wrong on {len(wrong)} of {len(self.DETECTOR)} synthetic "
            f"modules.{direction} Both senses share this table because neither is worth anything "
            "alone: a detector that finds nothing satisfies the precision row while letting a stray "
            "launcher ship, and one that flags everything satisfies the recall row while burying the "
            "package-wide scan in false positives. FIX: this detector is what makes the OWNER_SET "
            "re-base safe, so repair the detector rather than the expectation - and note the recall "
            "row asserts the COVERAGE flag too, since reporting a real hole as stdin-covered is as "
            "bad as not reporting it.\n" + "\n".join(wrong),
        )

    def test_no_unaccounted_nested_aw_launcher_lives_outside_the_owner_set(self):
        """Kept separate: the subject is the WHOLE SHIPPED PACKAGE, not a fixture.

        Every other assertion in this file is about a named module or a synthetic snippet. This walks
        all of `agent_workflows/` and is the only guard that a launcher added to a module NOBODY
        listed fails loudly - which is the single hole the owner-set re-base introduced.
        """
        package = REPO_ROOT / "agent_workflows"
        strays: dict[str, list[str]] = {}
        for path in sorted(package.rglob("*.py")):
            if any(part.startswith("tmp") for part in path.relative_to(package).parts):
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel in OWNER_SET:
                continue
            sites = self._semantic_nested_aw_sites(rel)
            if sites:
                strays[rel] = [f"{rel}:{ln} in {fn}" for ln, fn, _ in sites]
        counts = {rel: len(v) for rel, v in strays.items()}
        self.assertEqual(
            counts,
            self.EXEMPT_OUTSIDE_OWNER_SET,
            "the set of nested-`aw` launches OUTSIDE the owner set changed. Every such site is "
            "invisible to the stdin guard above, so a new one must be a decision: either add its "
            "module to OWNER_SET (preferred, it then gets the guard) or add it to "
            "EXEMPT_OUTSIDE_OWNER_SET with the reason. Found: " + repr(strays),
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
