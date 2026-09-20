#!/usr/bin/env python3

"""THE CONTRACT TEST for spec `25kzda` 2.1's run flag surface (runflags-01, `uyeko5`).

WHAT THIS FILE IS FOR, since the individual flag assertions below are the least valuable part of it.
Spec 2.1 declares `aw <host> run`'s invocation surface as a CLOSED flag list, and measured at HEAD
`bd91909e` seven of its eight policy flags were unreachable from either runner's command line. The
failure was systematic, not a gap in one feature: THE POLICY LANDED AND THE OPERATOR SURFACE DID NOT.
`--allow-mixed` and `--unattended` had working, tested policy behind them and no flag to reach it, and
`run_selection_policy.decide` - the entire mixed-type gate executed plan `6lu3rq` built - had ZERO
callers anywhere in the package.

So the load-bearing test here is not "`--allow-mixed` parses". It is
:meth:`SpecFlagListTests.test_every_flag_the_spec_declares_is_accounted_for`, which reads the SPEC
FILE, extracts its grammar block, and fails when the spec declares a flag the code neither registers
nor explicitly excludes. That is what makes the drift a test failure instead of an archaeology
project the next time the spec grows a flag.

DATA-DRIVEN, NOT HAND-WRITTEN PER FLAG, for the same reason: eight hand-written assertions are eight
things to forget to add a ninth to. Every test below iterates `runner_shared.RUN_POLICY_FLAGS`.

WHY THIS FILE EXISTS RATHER THAN LIVING IN EITHER HOST'S SUITE: the property under test is that the
TWO hosts agree. Asserting that from inside `test_oc_runipd.py` would put the agy half of a symmetry
claim in the opencode suite, and `818uru` already set the precedent that shared runner code gets its
own test home (`tests/test_runner_shared.py`).

MOST OF THIS FILE IS TABLE-DRIVEN, and HOST is the archetypal column. The subject is a surface that
exists TWICE (oc and agy) and must be identical, so a per-host class would let a property hold on one
host and not the other while both classes stayed green; every table below runs every row on BOTH
hosts and reports the failing (row, host) cells together, because "this flag broke on agy only" and
"this flag broke everywhere" are different defects that a per-host split cannot distinguish. Where a
distinction is otherwise a MODE (start versus resume, flag passed versus omitted, implemented versus
not) it is likewise a column.

SOURCE-TEXT PINS WERE DELETED FROM THIS FILE, and the reasoning is recorded here because the deletion
is the load-bearing change. Sixteen tests called `inspect.getsource(...)` and grepped the returned
TEXT: `assertIn("resolve_retry_budget", source)`, `assertNotIn("specs", source)`, a regex for
`getattr(args, "full_auto", False)`, `assertNotIn("10", source)`, and one `source.find(a) <
source.find(b)` byte-offset ordering claim. Every one of them breaks under a rename or a reformat
that changes no behavior, and - worse - EVERY one of them can be satisfied by a COMMENT, because a
comment is part of the source text. That is not hypothetical here: `94b00d37`'s commit message
records a shipped guard in this package that was passing solely because the literal it searched for
appeared in an explanatory comment ABOVE the code, while the code itself had been rewritten to a form
the guard could not match. So each pin is now a BEHAVIORAL assertion that drives the function and
observes the result, usually by replacing the collaborator with a sentinel and requiring the
sentinel's value to appear in the output; a comment cannot produce a sentinel.

KEPT DELIBERATELY: the AST-based guards. `ast.parse` + `ast.walk` looking for a real `ast.Call` node,
or for a bare `input()` call, is not a text grep - a comment does not parse into a Call node - and
those guards enforce an architecture invariant (ONE call site, in shared code; no nested prompt that
can wedge an unattended run) that no behavioral test reaches, since the hazard is a code shape rather
than an output.
"""

from __future__ import annotations

import argparse
import ast
import re
import unittest
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests.support import REPO_ROOT

_MODULES = {"oc_runipd": oc_runipd, "agy_runipd": agy_runipd}
BOTH = ("oc_runipd", "agy_runipd")

#: The spec this surface implements. Read as a FILE, so a spec edit can fail this suite.
SPEC_PATH = (
    REPO_ROOT
    / ".aw"
    / "records"
    / "specs"
    / "20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md"
)

#: Spec 2.1 grammar entries that are NOT part of this surface, each with the reason it is excluded.
#: An exclusion must be NAMED here to pass `test_every_flag_the_spec_declares_is_accounted_for`;
#: silence is a failure. That is deliberate: an unexplained gap between the spec and the code is
#: exactly the state this file exists to make impossible.
#:
#: `--allow-drafts` WAS excluded here and no longer is: `revsweep-02` (`6ypimw`) implemented spec 2.5a's
#: draft admission gate and registered the flag in this table, so it is now one of the flags this
#: surface owns. The exclusion was removed rather than kept as a stale comment, because an exclusion
#: that names an owner who has since landed reads as an unbuilt feature.
DECLARED_BUT_NOT_OWNED_HERE = {
    "--type": "spec 2.2/2.3 multi-type selection; needs the whole per-type dispatch table, not a flag",
    "--action": "revsweep-01 (`76gsmv`) registers it with its per-type legality refusal",
    "--json": "output shape, not policy; exists on `status` today and is not a `run` policy flag",
}


def _subparser(runner: str, name: str) -> argparse.ArgumentParser:
    parser = _MODULES[runner].build_parser()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices[name]
    raise AssertionError(f"{runner} has no subparsers")


def _option_strings(runner: str, name: str) -> set:
    return {
        opt
        for action in _subparser(runner, name)._actions
        for opt in action.option_strings
    }


def _action_for_flag(runner: str, subcommand: str, flag: str):
    for action in _subparser(runner, subcommand)._actions:
        if flag in action.option_strings:
            return action
    return None


def _parse(runner: str, argv: list) -> argparse.Namespace:
    return _MODULES[runner].build_parser().parse_args(argv)


#: The minimal plan `initialize_run` needs in order to build a real one-item queue: `Status: reviewed`
#: with an APPROVING `- Readiness:`, which is the exact input `aw agy run <selector>` used to clear to
#: `auto-approved` and EXECUTE with no flag passed.
_PROBE_PLAN = """# IPD: bare-run auto-approve probe

- Date: 2026-09-05
- Kind: child
- Concern: probe.
- Scope: probe.
- Scope-Paths: src/
- Item-Dependencies: none
- Status: reviewed
- Readiness: go
- Set: probe
- Order: 1
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history
- 2026-09-05 reviewed (test): APPROVE; no blocking findings.
"""


def _make_probe_repo(root, id6: str = "prb001"):
    """A committed git repository holding exactly one `reviewed` + `Readiness: go` plan.

    MODULE-LEVEL rather than a method, because two classes now need it: the end-to-end behavior tests
    and the resume-wiring test that replaced a source-text pin. Duplicating the fixture would let the
    two drift, and a resume test running against a DIFFERENT plan than the start test is exactly how a
    freeze assertion stops meaning anything.
    """
    import subprocess

    repo = root / "repo"
    repo.mkdir(parents=True)
    for cmd in (
        ["git", "init", "-q"],
        ["git", "config", "user.email", "test@example.invalid"],
        ["git", "config", "user.name", "Test"],
    ):
        subprocess.run(cmd, cwd=repo, check=True)
    (repo / ".gitignore").write_text(".aw/records/runs/\n", encoding="utf-8")
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True)
    plan = pending / f"20260905-probe-01-{id6}-probe.ipd.md"
    plan.write_text(_PROBE_PLAN.format(id6=id6), encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
    return repo, plan


def _effective_init_source(runner: str) -> str:
    import inspect

    source = inspect.getsource(_MODULES[runner].initialize_run)
    if "initialize_run_core" in source:
        return inspect.getsource(runner_shared.initialize_run_core)
    return source


class SpecFlagListTests(unittest.TestCase):
    """The drift guard: the SPEC FILE is the input, not a transcription of it."""

    def spec_grammar_flags(self) -> set:
        """Every `--flag` on spec 2.1's `aw <host> run <selector>` STANZA of the grammar block.

        Parsed from the spec rather than copied out of it, which is the entire point: a flag added to
        section 2.1 and to nothing else must FAIL here.

        TWO SCOPING DECISIONS, both of which change the answer:

        * Scoped to the grammar BLOCK, not the whole section, because the surrounding prose also
          mentions flags the grammar deliberately does not declare - notably the
          `--no-verify`/`--skip-audit`/`--dangerous` group that `:140` states does NOT exist on `run`.
          Treating a prohibition as a declaration would invert its meaning.
        * Scoped within the block to the `aw <host> run <selector>` stanza, stopping at the next
          command. The block declares FIVE commands, and `aw <host> prompt`'s `--text`/`--file` are
          not `run` policy flags at all; including them would have this test demand that `run` grow
          `--text`, which is a different verb's surface. The stanza is delimited by the blank line
          before the next `aw ` line, which is the block's own structure and not a heuristic.
        """
        text = SPEC_PATH.read_text(encoding="utf-8")
        section = text.split("### 2.1 Command grammar", 1)
        self.assertEqual(
            len(section), 2, "spec 2.1 heading not found; did the spec move?"
        )
        block = section[1].split("```text", 1)[1].split("```", 1)[0]
        stanza: list = []
        started = False
        for line in block.splitlines():
            if line.startswith("aw ") and "run <selector>" in line:
                started = True
                continue
            if started:
                if not line.strip() or line.startswith("aw "):
                    break
                stanza.append(line)
        self.assertTrue(
            stanza, "spec 2.1's `aw <host> run <selector>` stanza not found"
        )
        return set(re.findall(r"--[a-z][a-z0-9-]*", "\n".join(stanza)))

    def test_every_flag_the_spec_declares_is_accounted_for(self):
        """THE LOAD-BEARING ASSERTION. Registered here, or excluded WITH A NAMED REASON."""
        declared = self.spec_grammar_flags()
        owned = set(runner_shared.RUN_POLICY_FLAGS_BY_FLAG)
        excluded = set(DECLARED_BUT_NOT_OWNED_HERE)
        unaccounted = sorted(declared - owned - excluded)
        self.assertEqual(
            unaccounted,
            [],
            "spec 25kzda 2.1 declares flag(s) that this surface neither registers nor "
            f"explicitly excludes: {unaccounted}. Add each to runner_shared.RUN_POLICY_FLAGS "
            "or to DECLARED_BUT_NOT_OWNED_HERE with the reason and the owner.",
        )

    def test_the_spec_and_the_owned_table_agree_in_both_directions(self):
        """The CONVERSE of the bijection plus the table's own well-formedness, in one report.

        Three tests became one. `test_no_owned_flag_is_absent_from_the_spec`,
        `test_the_owned_set_is_every_declared_flag_this_surface_claims`, and
        `test_every_exclusion_names_a_reason` all compared the SAME two sets - spec 2.1's declared
        flags and `RUN_POLICY_FLAGS_BY_FLAG` - and differed only in WHICH DIRECTION of the
        disagreement they reported. So they fail TOGETHER for one cause (the spec and the table
        drifted) and a reader needs both directions at once to know which way the drift went; three
        red lines each showing one half of a set difference is strictly less information than one
        failure showing both halves.

        NOT merged into `test_every_flag_the_spec_declares_is_accounted_for`, deliberately. That test
        is THE load-bearing gate this file exists for, it is named in this module's docstring, and it
        is the one a spec edit must fail on; folding it into a composite whose failure could come from
        a duplicate `dest` would blunt exactly the signal it provides.

        The uniqueness checks live here rather than beside the count because a duplicate `flag` or
        `dest` in the table silently makes the set comparison PASS while the table is broken: two rows
        with one flag collapse to one key in `RUN_POLICY_FLAGS_BY_FLAG`, so the set-versus-set check
        cannot see the loss and only the length comparison can.

        THE EXPECTED COUNT IS DERIVED FROM THE SPEC, never hardcoded. It asserted a literal `8` and
        had to be edited when `revsweep-02` (`6ypimw`) registered a ninth (`--allow-drafts`, whose
        spec 2.5a behavior now ships). A literal count teaches the next author to edit the number to
        match the code, which is the habit this whole file exists to break.
        """
        declared = self.spec_grammar_flags()
        owned_by_flag = set(runner_shared.RUN_POLICY_FLAGS_BY_FLAG)
        rows = runner_shared.RUN_POLICY_FLAGS
        problems = []

        invented = sorted(owned_by_flag - declared)
        if invented:
            problems.append(
                f"  registered here but NOT in spec 2.1's grammar: {invented}\n"
                "    this direction exists because: the spec is the AUTHORITY for what `run`'s "
                "surface is. A flag this table owns that the spec never declared is a surface the "
                "spec does not sanction, so an operator reading the spec cannot discover it and a "
                "later spec edit has no reason to preserve it"
            )

        expected_owned = declared - set(DECLARED_BUT_NOT_OWNED_HERE)
        if owned_by_flag != expected_owned:
            problems.append(
                f"  the owned set is {sorted(owned_by_flag)} but the spec's declaration minus the "
                f"named exclusions is {sorted(expected_owned)}\n"
                "    this direction exists because: the COUNT is derived from the spec file, not "
                "hardcoded, so this can only fail when the spec and the table genuinely disagree "
                "rather than when the surface merely GREW"
            )

        if len({row.flag for row in rows}) != len(rows):
            problems.append(
                "  two rows declare the SAME `flag`\n"
                "    this row exists because: duplicate flags COLLAPSE in "
                "`RUN_POLICY_FLAGS_BY_FLAG`, so every set comparison above still passes while one "
                "row's metadata (its help, its `implemented`, its `freeze`) is silently unreachable"
            )
        if len({row.dest for row in rows}) != len(rows):
            problems.append(
                "  two rows declare the SAME `dest`\n"
                "    this row exists because: two flags writing one namespace attribute means the "
                "later one WINS at parse time, so one of the two flags does nothing and no "
                "registration test can tell"
            )

        unexplained = sorted(
            flag
            for flag, reason in DECLARED_BUT_NOT_OWNED_HERE.items()
            if not reason.strip()
        )
        if unexplained:
            problems.append(
                f"  excluded with an EMPTY reason: {unexplained}\n"
                "    this row exists because: an exclusion is how a spec-declared flag legitimately "
                "escapes the bijection gate, so a blank reason converts that gate into an opt-out "
                "anybody can take silently. The reason must name the owner"
            )

        self.assertEqual(
            problems,
            [],
            f"spec 2.1's flag declaration and `RUN_POLICY_FLAGS` disagree in {len(problems)} of 5 "
            "ways. Read them together: an `invented` flag plus a matching owned-set mismatch is ONE "
            "drift reported twice (a flag was added to the table and not to the spec), while a "
            "duplicate `flag`/`dest` alongside a set mismatch means the table is internally broken "
            "and the set comparison is not trustworthy until that is fixed. FIX: amend spec 2.1, or "
            "move the flag into DECLARED_BUT_NOT_OWNED_HERE with the reason and the owner. Note the "
            "companion gate `test_every_flag_the_spec_declares_is_accounted_for` covers the OTHER "
            f"direction (spec declares, code ignores) and is deliberately separate.\n"
            + "\n".join(problems),
        )


class RegistrationTests(unittest.TestCase):
    """E-01: every spec 2.1 policy flag is REGISTERED on BOTH hosts' `run` parser.

    REGISTRATION ONLY, deliberately: that the flag parses and lands in the namespace. Behavior is
    asserted by the classes below, and conflating the two would make this class fail for two
    unrelated reasons and stop being a usable signal.

    SIX TESTS BECAME ONE SWEEP over (flag x host), because every one of them iterated
    `RUN_POLICY_FLAGS` crossed with `BOTH` and asserted ONE property per cell: registered on `start`,
    registered on `resume`, present in the namespace, present in `--help`, has a `--no-X` negation,
    and the two hosts' sets are equal. They share both a cause and a fix - a flag added to the table
    and wired into neither parser fails all six at once, on both hosts - so six red lines each naming
    one property of one flag is six views of one omission.

    THE PER-FLAG REPORT IS WHAT THIS BUYS. A registration gap is almost never uniform: the realistic
    failure is a flag wired on `start` and forgotten on `resume` (which argparse then rejects with
    `unrecognized arguments`, telling the operator the flag does not exist rather than why it is
    refused), or wired on oc and forgotten on agy. The table names WHICH surfaces each flag is missing
    from, so that asymmetry is readable directly instead of being inferred from which of six tests
    went red.
    """

    def test_every_flag_is_fully_wired_on_every_surface_of_both_hosts(self):
        missing = []
        for row in runner_shared.RUN_POLICY_FLAGS:
            for runner in BOTH:
                gaps = []
                start = _option_strings(runner, "start")
                resume = _option_strings(runner, "resume")
                if row.flag not in start:
                    gaps.append(
                        "not registered on `start`, so the flag does not exist for a new run"
                    )
                if row.flag not in resume:
                    gaps.append(
                        "not registered on `resume`. Even the flag resume REFUSES must be ACCEPTED "
                        "by argparse first: an unregistered flag produces `unrecognized arguments`, "
                        "which tells the operator the flag does not exist, where `--retry-budget` "
                        "must instead fail with the spec's real reason (the frozen value cannot "
                        "change)"
                    )
                if not hasattr(_parse(runner, ["start", "demo"]), row.dest):
                    gaps.append(
                        f"does not populate `{row.dest}` on a bare run, so every reader using "
                        "`getattr(args, dest)` silently sees its own fallback instead of the flag"
                    )
                if row.flag not in _subparser(runner, "start").format_help():
                    gaps.append(
                        "absent from `--help`, so the flag is undiscoverable by the only "
                        "documentation an operator actually reads"
                    )
                if row.kind == "bool" and f"--no-{row.flag[2:]}" not in start:
                    gaps.append(
                        f"has no `--no-{row.flag[2:]}` negation. Every bool row uses "
                        "`BooleanOptionalAction` (matching the shipped `--full-auto`), which is also "
                        "the mechanism that lets `resume` distinguish an explicit OFF from silence"
                    )
                if gaps:
                    missing.append(
                        f"  {row.flag} on {runner}:\n"
                        + "".join(f"    - {g}\n" for g in gaps).rstrip("\n")
                    )

        owned = set(runner_shared.RUN_POLICY_FLAGS_BY_FLAG)
        per_host = {
            runner: {f for f in _option_strings(runner, "start") if f in owned}
            for runner in BOTH
        }
        if per_host["oc_runipd"] != per_host["agy_runipd"]:
            only_oc = sorted(per_host["oc_runipd"] - per_host["agy_runipd"])
            only_agy = sorted(per_host["agy_runipd"] - per_host["oc_runipd"])
            missing.append(
                f"  THE TWO HOSTS' FLAG SETS DIFFER: only on oc {only_oc}, only on agy {only_agy}\n"
                "    this row exists because: the `rununify` property is ONE surface, not two that "
                "merely agree today. An operator who learns a flag on one host must be able to use "
                "it on the other"
            )

        self.assertEqual(
            missing,
            [],
            f"{len(missing)} (flag, host) cell(s) of "
            f"{len(runner_shared.RUN_POLICY_FLAGS) * len(BOTH)} are not fully wired. READ THE SHAPE "
            "OF THE FAILURES: if a flag is missing on EVERY surface of BOTH hosts it was added to "
            "`RUN_POLICY_FLAGS` and wired nowhere, which is one registration call away from fixed. "
            "If it is missing on `resume` only, the operator gets `unrecognized arguments` instead of "
            "the spec's refusal. If it is missing on ONE host only, that is the exact asymmetry this "
            "file exists to catch and the shared registration helper is being bypassed on that "
            "host.\n" + "\n".join(missing),
        )


class HelpHonestyTests(unittest.TestCase):
    """Spec/documentation sync: a divergence from the spec's full semantics is in `--help`.

    An operator reads `--help` and never reads an IPD, so recording an unimplemented flag or a missing
    precedence tier only in a plan leaves the shipped command lying about what it does.

    ONE TABLE replaces four per-flag tests plus the rendered-help sweep. Each of the four looked up a
    row in `RUN_POLICY_FLAGS_BY_FLAG` and asserted that its `help` CONTAINS a specific token; only the
    flag and the token differed, which is a data row. The tokens are grouped by the KIND of honesty
    they enforce, and every row says what an operator is misled about if the token goes missing.

    THE TOKENS ARE KEPT ONLY WHERE SOMETHING SPECIFIC IS PROMISED, following `82ca6e96`'s rule for
    prose pins. Each surviving token is either a BACKLOG ID the operator needs in order to find who
    owns an unbuilt behavior, or another FLAG whose name the operator needs in order to comply with a
    precondition. A pin on ordinary explanatory wording would be a change-detector on prose and is not
    kept: that is why these rows assert tokens and not sentences.

    THE RENDERED-HELP ROW IS THE ONE THAT MATTERS and is why this is not merely a table of string
    checks: it asserts that `action.help` on the REAL parser equals the table's `help`, for every flag
    on both hosts. Without it, every token row above could pass against a table whose text never
    reaches the parser an operator invokes.

    `NOT YET IMPLEMENTED` IS DERIVED, NOT LISTED. The unimplemented rows are selected by
    `row.implemented` rather than named, so a flag that stops shipping its behavior is required to say
    so in `--help` automatically.
    """

    #: (flag, required token, why this token is load-bearing to an OPERATOR)
    HELP_TOKENS = (
        (
            "--retry-budget",
            "NOT IMPLEMENTED",
            "spec 2.1 declares THREE precedence tiers (CLI > repository policy > default) and the "
            "MIDDLE one does not exist. An operator who believes a repo-level retry policy is being "
            "honored would read a run's retry count as policy-driven when it is the bare default",
        ),
        (
            "--retry-budget",
            "dh3us4",
            "the backlog id owning the missing tier. Without it the `--help` text states a gap and "
            "gives the reader nowhere to go; with it the gap is a tracked item they can find",
        ),
        (
            "--unverifiable-ok",
            "--allow-unverifiable",
            "this flag is REFUSED on its own, so the help must name the companion flag that admits "
            "it. An operator who reads only this entry passes the flag, gets a refusal, and has to "
            "guess which other flag unlocks it",
        ),
        (
            "--full-auto",
            "--unattended",
            "spec `:134` makes this flag IMPLY another one, which means passing it silently changes a "
            "second policy. An implication an operator cannot see in `--help` is a hidden side effect",
        ),
        (
            "--allow-drafts",
            "COMPLETE",
            "spec 2.5a bullet 1: the flag admits only a COMPLETE draft. Stating the limit is what "
            "stops an operator from concluding the gate is broken when their scaffold stub is skipped",
        ),
        (
            "--allow-drafts",
            "INCOMPLETE",
            "the same limit from the other side, naming the case that is REFUSED. Both spellings are "
            "asserted because the operator-facing question is 'why was mine skipped', which the "
            "negative form answers and the positive form does not",
        ),
        (
            "--allow-drafts",
            "waives no other gate",
            "the SCOPE of the waiver. A flag whose name says `allow` invites the reading that it "
            "relaxes review, approval, or verification too; every one of those gates still applies",
        ),
    )

    def test_every_help_string_carries_the_tokens_an_operator_needs(self):
        wrong = []
        for flag, token, why in self.HELP_TOKENS:
            row = runner_shared.RUN_POLICY_FLAGS_BY_FLAG.get(flag)
            if row is None:
                wrong.append(
                    f"  {flag} / {token!r}:\n"
                    f"    - the flag is not registered at all, so its help cannot be checked\n"
                    f"    this row exists because: {why}"
                )
                continue
            if token not in row.help:
                wrong.append(
                    f"  {flag} / {token!r}:\n"
                    f"    - missing from the help text, which reads: {row.help!r}\n"
                    f"    this row exists because: {why}"
                )

        for row in runner_shared.RUN_POLICY_FLAGS:
            if row.implemented:
                continue
            for token, why in (
                (
                    "NOT YET IMPLEMENTED",
                    "the flag PARSES but refuses, and a flag that parses while doing nothing is "
                    "strictly worse than no flag. The help is the only place an operator learns "
                    "that before they rely on it",
                ),
                (
                    "x8diyb",
                    "the backlog item that OWNS the unbuilt behavior, so a refusal is a tracked gap "
                    "rather than a dead end",
                ),
            ):
                if token not in row.help:
                    wrong.append(
                        f"  {row.flag} (derived: implemented=False) / {token!r}:\n"
                        f"    - missing from the help text, which reads: {row.help!r}\n"
                        f"    this row exists because: {why}"
                    )

        for runner in BOTH:
            for row in runner_shared.RUN_POLICY_FLAGS:
                action = _action_for_flag(runner, "start", row.flag)
                if action is None:
                    wrong.append(
                        f"  {row.flag} on {runner} (rendered help):\n"
                        "    - the flag has no action on the `start` parser, so the table's help "
                        "text reaches no operator\n"
                        "    this row exists because: THE TABLE IS NOT THE SURFACE. Every token row "
                        "above reads `row.help`, so all of them pass vacuously if the text never "
                        "gets registered"
                    )
                elif action.help != row.help:
                    wrong.append(
                        f"  {row.flag} on {runner} (rendered help):\n"
                        f"    - the parser shows {action.help!r}\n"
                        f"    - the table declares {row.help!r}\n"
                        "    this row exists because: THE TABLE IS NOT THE SURFACE. A host that "
                        "hand-writes its own help text for a shared flag can drift from the table "
                        "while every token assertion above still passes"
                    )

        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} help-honesty claim(s) failed. Read them together: if the RENDERED-HELP "
            "rows fail while the token rows pass, the table's text is correct and a host is "
            "overriding it, so the tokens above are being asserted against text no operator sees. If "
            "token rows fail on their own, the help was edited and dropped a backlog id or a "
            "companion flag name an operator needs to act. FIX: put the token back in the "
            "`RUN_POLICY_FLAGS` row's `help` (that ONE string is what both the table and the parser "
            "read), and if a behavior genuinely shipped, flip `implemented` rather than deleting the "
            f"`NOT YET IMPLEMENTED` wording.\n" + "\n".join(wrong),
        )


class MixedTypeGateWiringTests(unittest.TestCase):
    """E-02: `6lu3rq`'s gate is CALLED, and it APPLIES on a genuinely multi-type classification.

    THE DEFECT THIS CLASS EXISTS FOR is not a missing flag. `run_selection_policy.decide` had ZERO
    callers anywhere in the package, so a fully built and fully tested gate was unreachable and a
    mixed selection was silently accepted. A test that only checked `--allow-mixed` parses would pass
    while the gate stayed dead - which is exactly the state this plan found.

    AND `gate_applied=False` DOES NOT SATISFY THIS CLASS. `decide` short-circuits `gate_applied=False`
    whenever the classification is single-type, which is what a still-dead gate would also produce; so
    the assertions below construct a REAL multi-type classification and require `gate_applied=True`.

    THE LIMIT, asserted rather than merely commented, so a green run of this file is not mistaken for
    more than it proves: no live `aw <host> run` invocation can yet produce a mixed selection, because
    discovery is IPD-only and neither host registers `--type`. See
    :meth:`test_no_live_invocation_can_yet_produce_a_mixed_selection`.
    """

    def multi_type_paths(self, root) -> list:
        """A REAL multi-type path set: one IPD plus one spec, both typed by the shipped authority."""
        plans = root / ".aw" / "records" / "plans" / "pending"
        specs = root / ".aw" / "records" / "specs"
        plans.mkdir(parents=True, exist_ok=True)
        specs.mkdir(parents=True, exist_ok=True)
        ipd = plans / "20260905-demo-01-aaa111-demo.ipd.md"
        ipd.write_text("- Status: approved\n- Id: aaa111\n", encoding="utf-8")
        spec = specs / "20260905-bbb222-01-bbb222-demo.spec.md"
        spec.write_text("- Status: approved\n- Id: bbb222\n", encoding="utf-8")
        return [ipd, spec]

    def classify_multi(self, root):
        from agent_workflows import run_selection_policy

        classification = run_selection_policy.classify_paths(
            root, self.multi_type_paths(root)
        )
        self.assertTrue(
            classification.is_mixed,
            f"the fixture is not multi-type: {classification.spec_types}",
        )
        return classification

    def test_decide_is_called_from_the_runner(self):
        """The dead-gate fix itself: a call site exists, in SHARED code both hosts reach.

        KEPT AS AN AST GUARD, not converted to a text grep and not deleted. `ast.walk` looking for a
        real `ast.Call` node cannot be satisfied by a comment or a docstring, which matters
        specifically here because this module's own prose mentions `decide` repeatedly (it explains
        the dead-gate defect at length), so a substring search would pass on that prose alone.

        The runner half is now BEHAVIORAL - `test_both_hosts_actually_reach_the_gate_on_a_real_run`
        replaces the `assertIn("enforce_mixed_type_gate", body)` text pin with a patched `decide` that
        counts its calls on a real `initialize_run`. A comment naming the gate cannot increment a
        counter.
        """
        import ast
        import inspect

        source = inspect.getsource(runner_shared.enforce_mixed_type_gate)
        called = {
            ast.unparse(node.func)
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call)
        }
        self.assertIn("run_selection_policy.decide", called)

    def test_the_gate_APPLIES_and_REFUSES_a_multi_type_selection_unattended(self):
        """Left separate: an `assertRaises` test, and its refusal-text assertions are the subject."""
        import tempfile
        from pathlib import Path as _P

        with tempfile.TemporaryDirectory() as td:
            root = _P(td)
            paths = self.multi_type_paths(root)
            with self.assertRaises(runner_shared.DriverError) as ctx:
                runner_shared.enforce_mixed_type_gate(
                    root,
                    paths,
                    allow_mixed=False,
                    interactive=False,
                    host="oc",
                    selector="all",
                )
            self.assertIn("[RUN-MIXED-TYPES]", str(ctx.exception))
            self.assertIn("No work started.", str(ctx.exception))

    def test_the_gate_APPLIES_and_PROCEEDS_with_allow_mixed(self):
        """Left separate from the refusal above: merging an accept path with an `assertRaises` path
        would couple two structurally different assertions over one fixture."""
        import tempfile
        from pathlib import Path as _P

        with tempfile.TemporaryDirectory() as td:
            root = _P(td)
            verdict = runner_shared.enforce_mixed_type_gate(
                root,
                self.multi_type_paths(root),
                allow_mixed=True,
                interactive=False,
                host="oc",
                selector="all",
            )
            self.assertTrue(verdict.proceed)
            self.assertTrue(
                verdict.gate_applied,
                "gate_applied=False is the SINGLE-TYPE short circuit and would also be "
                "returned by a still-dead gate; it does not prove the gate applied",
            )
            self.assertEqual(verdict.record.response_or_flag, "--allow-mixed")

    def test_an_interactive_multi_type_selection_requires_the_exact_phrase(self):
        """Left separate: already a loop over five reflex answers plus the one accepted phrase, against
        a classification built once; the shape is the table."""
        import tempfile
        from pathlib import Path as _P

        from agent_workflows import run_selection_policy

        with tempfile.TemporaryDirectory() as td:
            root = _P(td)
            classification = self.classify_multi(root)
            for bad in ("y", "yes", "", "run", "run mixed types"):
                with self.subTest(response=bad):
                    verdict = run_selection_policy.decide(
                        classification, interactive=True, response=bad
                    )
                    self.assertFalse(verdict.proceed)
                    self.assertTrue(verdict.gate_applied)
            good = run_selection_policy.decide(
                classification, interactive=True, response="run mixed"
            )
            self.assertTrue(good.proceed)
            self.assertTrue(good.gate_applied)

    def test_no_part_of_the_gate_was_reimplemented(self):
        """The refusal text and the confirmation phrase must be the POLICY MODULE's, observably.

        REPLACES TWO SOURCE-TEXT PINS with the behavioral property they were approximating. They read
        `inspect.getsource(module)` for each of three modules and asserted the first 40 characters of
        `REFUSAL_TEMPLATE` and the quoted `CONFIRM_PHRASE` were ABSENT from the text. Both are
        change-detectors twice over: a module that legitimately QUOTED the spec refusal in a comment
        (to explain why it must not be recomposed) failed them, while a module that composed the same
        refusal from f-string fragments passed them.

        So the assertion is now the one that actually matters: the refusal an operator SEES is the
        string the policy module RENDERS, byte for byte. Verified by rendering the expected refusal
        independently and comparing, which a second copy cannot satisfy unless it is character-
        identical - and if it were character-identical it would still fail the moment either copy was
        edited, which is the fork this guards against.

        The confirmation phrase is asserted by DELEGATION: the matcher is replaced so that `y` is
        accepted, and the runner seam must then accept `y`. A seam carrying its own copy of the phrase
        comparison would keep refusing, because its copy is untouched by the patch.
        """
        import tempfile
        from pathlib import Path as _P

        from agent_workflows import run_selection_policy

        with tempfile.TemporaryDirectory() as td:
            root = _P(td)
            paths = self.multi_type_paths(root)
            classification = run_selection_policy.classify_paths(root, paths)
            expected = run_selection_policy.render_refusal(
                classification, host="oc", selector="all"
            )
            with self.assertRaises(runner_shared.DriverError) as ctx:
                runner_shared.enforce_mixed_type_gate(
                    root,
                    paths,
                    allow_mixed=False,
                    interactive=False,
                    host="oc",
                    selector="all",
                )
            self.assertEqual(
                str(ctx.exception),
                expected,
                "the refusal an operator sees must be `run_selection_policy.render_refusal`'s own "
                "output verbatim. A difference here means the runner RECOMPOSED the spec's refusal, "
                "which is the fork that lets the shipped message drift from the spec",
            )

            with mock.patch.object(
                run_selection_policy, "is_confirmation_accepted", lambda *a, **k: True
            ):
                verdict = runner_shared.enforce_mixed_type_gate(
                    root,
                    paths,
                    allow_mixed=False,
                    interactive=True,
                    host="oc",
                    selector="all",
                    response="y",
                )
            self.assertTrue(
                verdict.proceed,
                "with the policy module's matcher patched to accept anything, the runner seam must "
                "accept `y`. Still refusing means the seam compares the phrase ITSELF, so there are "
                "two definitions of what confirmation means and they are free to diverge",
            )

    def test_no_live_invocation_can_yet_produce_a_mixed_selection(self):
        """THE LIMIT, as an assertion. Registering `--type` would falsify this and must fail here.

        Two independent reasons, both asserted: neither host registers `--type`, and discovery returns
        IPDs only. When a later plan builds multi-type selection it will have to update this test,
        which is the point - the limit becomes visible rather than being silently outgrown.

        THE DISCOVERY HALF WAS A SOURCE-TEXT PIN and is now behavioral. It read
        `inspect.getsource(runner_shared.discover_plans)` and asserted `".aw" in source` and `"specs"
        not in source`. The `"specs"` half was the dangerous one: the word appears in ordinary English
        ("the specs tree", "spec-aware"), so ANY comment mentioning specs in that function failed a
        test about behavior, and conversely a discovery that grew a spec tree through a variable named
        something else passed. Now the test plants a REAL spec beside a real IPD in a temp repo and
        requires discovery to return only the IPD, on both hosts.
        """
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            for sub in ("start", "resume"):
                with self.subTest(runner=runner, subcommand=sub):
                    self.assertNotIn("--type", _option_strings(runner, sub))

        with tempfile.TemporaryDirectory() as td:
            root = _P(td)
            ipd, spec = self.multi_type_paths(root)
            for runner in BOTH:
                with self.subTest(runner=runner):
                    found = _MODULES[runner].discover_plans(root)
                    self.assertEqual(
                        sorted(found),
                        ["aaa111"],
                        f"{runner}: discovery must return the IPD ONLY. The temp repo holds a real "
                        f"spec at {spec.name} beside the IPD at {ipd.name}; returning the spec's "
                        "id6 too would mean a live selection can be multi-type, which would make "
                        "this whole class's honest limit false",
                    )


class FullAutoImpliesUnattendedTests(unittest.TestCase):
    """E-02: spec `:134` - `--full-auto` implies `--unattended`, and implies NOTHING else."""

    def frozen(self, **kw) -> dict:
        base = {row.dest: False for row in runner_shared.RUN_POLICY_FLAGS}
        base["retry_budget"] = None
        base.update(kw)
        return runner_shared.freeze_run_policy_flags(argparse.Namespace(**base))

    def test_full_auto_implies_unattended(self):
        """Kept separate: the POSITIVE half of the implication, which the table below cannot state.

        `test_full_auto_implies_nothing_else` iterates every row EXCEPT `full_auto`/`unattended` and
        requires it to stay False, so it is vacuous on its own - a `freeze` that set nothing at all
        would satisfy it. This one assertion is what makes the exclusion table meaningful.
        """
        self.assertTrue(self.frozen(full_auto=True)["unattended"])

    def test_full_auto_implies_nothing_else(self):
        """The IMPLICATION is about BOOLEAN policy, so the exemption is derived, not enumerated.

        THE EXEMPTION WAS A HARDCODED NAME LIST (`full_auto`, `unattended`, `retry_budget`) and is now
        `row.kind != "bool"` plus the two flags the implication is ABOUT. That is the same
        maintenance-tax fix this file's own `test_the_owned_set_is_every_declared_flag_this_surface_claims`
        already documents for its literal count: a name list of non-bool rows silently makes THIS test
        the thing that blocks the next non-bool flag, for a reason unrelated to what it asserts.

        Measured when `integpath-03` (`51vw4y`) registered a second int and a first choice row: the
        assertion failed with `AssertionError: 10 is not false ... --full-auto must not imply
        --integration-retry-limit`, where 10 is that flag's DEFAULT and is present whether or not
        `--full-auto` was passed. `assertFalse` on a non-bool frozen value tests nothing about an
        implication; it tests that the value happens to be falsy, which for a counter means "switched
        off" and for a policy word means "not a legal value".

        WHAT IS DELIBERATELY NOT WEAKENED: every BOOLEAN row is still asserted, so the property spec
        `:134` states ("--full-auto implies --unattended and nothing else") is still enforced against
        exactly the flags it can be violated for. A non-bool row that `--full-auto` wrongly SET would
        be caught by that flag's own freeze test, which asserts its effective resolved value.
        """
        frozen = self.frozen(full_auto=True)
        for row in runner_shared.RUN_POLICY_FLAGS:
            if row.dest in ("full_auto", "unattended") or row.kind != "bool":
                continue
            with self.subTest(flag=row.flag):
                self.assertFalse(
                    frozen[row.dest],
                    f"--full-auto must not imply {row.flag} (spec :134)",
                )
        # Stated positively so the derived exemption above cannot quietly become "exempt everything":
        # at least the shipped boolean policy flags must actually have been checked.
        checked = [
            row.flag
            for row in runner_shared.RUN_POLICY_FLAGS
            if row.kind == "bool" and row.dest not in ("full_auto", "unattended")
        ]
        self.assertGreaterEqual(len(checked), 6, checked)

    def test_unattended_alone_does_not_imply_full_auto(self):
        """Kept separate: the implication's DIRECTION, which is the asymmetry worth its own name.

        `--full-auto` implies `--unattended`; the converse must NOT hold, because `--unattended` only
        declares that nobody is watching while `--full-auto` additionally authorizes clearing a
        reviewed plan to `auto-approved` and executing it. An implication accidentally made
        bidirectional would turn every unattended run into an auto-approving one.
        """
        self.assertFalse(self.frozen(unattended=True)["full_auto"])

    #: (case, `unattended`, `full_auto`, stdin is a TTY, stderr is a TTY, expected interactive, why)
    INTERACTIVITY = (
        (
            "a real terminal and no policy flag",
            False,
            False,
            True,
            True,
            True,
            "THE POSITIVE ROW. Every negative row below is vacuous while this one is broken, because "
            "a predicate that returned False unconditionally satisfies all of them - and a gate that "
            "can never prompt is indistinguishable from a gate that always refuses",
        ),
        (
            "--unattended with a real terminal",
            True,
            False,
            True,
            True,
            False,
            "the operator's DECLARATION outranks a TTY that happens to exist. An unattended run "
            "launched from a terminal must refuse rather than block forever waiting for the human "
            "who said they are not there",
        ),
        (
            "--full-auto with a real terminal",
            False,
            True,
            True,
            True,
            False,
            "the same rule reached through the IMPLICATION rather than directly (spec `:134`), which "
            "is why this is a separate row: it fails if the implication is applied at freeze time but "
            "not consulted by the interactivity predicate, leaving a `--full-auto` run able to prompt",
        ),
        (
            "no TTY on stdin, flags clear",
            False,
            False,
            False,
            True,
            False,
            "with nobody to type, a prompt is an unbounded wedge. `_lane_reclaim_prompt` in both "
            "runners already establishes exactly this precedent (no TTY means no prompt, EVER)",
        ),
        (
            "no TTY on stderr, flags clear",
            False,
            False,
            True,
            False,
            False,
            "BOTH streams are required, and this row is the one a naive implementation fails: a "
            "prompt whose QUESTION goes to a redirected stderr is invisible, so the operator sees a "
            "hung command with no text explaining what it wants",
        ),
    )

    def test_a_gate_may_prompt_only_with_a_real_terminal_and_no_policy_flag(self):
        """Every (flags x TTY) combination, in one table with the positive case included.

        Two tests became one. `test_an_unattended_run_is_not_interactive_even_with_a_tty` made two
        assertions that differed only in WHICH flag was set, and
        `test_no_tty_means_not_interactive_regardless_of_flags` made a third that differed only in
        which stream lacked a TTY - three cells of one 2-input truth table, expressed as two tests
        that between them never asserted the TRUE case at all.

        THE POSITIVE ROW IS THE ADDITION. Neither old test could fail if `is_interactive_run` returned
        False unconditionally, which is a realistic regression (an early `return False` added while
        debugging an unattended wedge) and would silently disable every interactive gate in the
        package.

        Both streams are columns because the predicate reads `sys.stdin` and the passed `stream`
        separately, so a check that tested only one would accept a prompt whose question is invisible.
        """
        import sys as _sys

        class _Stream:
            def __init__(self, tty: bool):
                self._tty = tty

            def isatty(self):
                return self._tty

        wrong = []
        for (
            case,
            unattended,
            full_auto,
            stdin_tty,
            err_tty,
            expected,
            why,
        ) in self.INTERACTIVITY:
            with mock.patch.object(_sys, "stdin", _Stream(stdin_tty)):
                got = runner_shared.is_interactive_run(
                    argparse.Namespace(unattended=unattended, full_auto=full_auto),
                    stream=_Stream(err_tty),
                )
            if got is not expected:
                wrong.append(
                    f"  {case}:\n"
                    f"    - expected interactive={expected}, got {got}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`is_interactive_run` answered {len(wrong)} of {len(self.INTERACTIVITY)} "
            "flag/TTY combinations wrongly. READ THEM TOGETHER: if only the POSITIVE row fails, no "
            "gate in the package can ever prompt and every interactive confirmation has silently "
            "become an unattended refusal. If only NEGATIVE rows fail, a gate can prompt where "
            "nobody can answer, which is an unbounded hang rather than a wrong answer (both runners "
            "hand children `stdin=DEVNULL` precisely because a nested prompt blocks forever; a "
            "measured 1h49m wedge is recorded inline in the draft-gate class below). FIX: both "
            "halves are load-bearing - `--unattended` (and `--full-auto`, which implies it) wins over "
            f"a TTY, AND both streams must be TTYs when no flag is set.\n"
            + "\n".join(wrong),
        )


class UnverifiableAdmissionTests(unittest.TestCase):
    """E-03: `--unverifiable-ok` is bound to `zub5f1`'s predicate, precondition and all."""

    def args(self, **kw) -> argparse.Namespace:
        base = {"unverifiable_ok": False, "allow_unverifiable": False}
        base.update(kw)
        return argparse.Namespace(**base)

    #: (case, `--unverifiable-ok`, `--allow-unverifiable`, refused?, `unverifiable_ok_applied`, why)
    ADMISSION = (
        (
            "neither flag",
            False,
            False,
            False,
            False,
            "the DEFAULT must be silent and must grant nothing. A contractless prompt still counts "
            "against the run unless an operator explicitly says otherwise",
        ),
        (
            "--unverifiable-ok ALONE",
            True,
            False,
            True,
            None,
            "THE PRECONDITION. This flag makes an unverifiable item NEUTRAL for the aggregate exit "
            "code, which is a weakening of the run's own verdict, so it is legal only where the "
            "operator separately ADMITTED contractless prompts. Accepting it alone would let one "
            "flag silently neutralize the verification gate",
        ),
        (
            "--allow-unverifiable ALONE",
            False,
            True,
            False,
            False,
            "the ADMISSION is not itself the neutrality grant, so it needs no companion flag. This "
            "row is what keeps the precondition from being read as mutual: admitting contractless "
            "prompts still leaves them counting against the exit code",
        ),
        (
            "both flags",
            True,
            True,
            False,
            True,
            "the sanctioned combination, and the only row where the grant is APPLIED. Without it the "
            "refusal row above is satisfiable by a predicate that refuses `--unverifiable-ok` "
            "unconditionally, i.e. by a flag that can never be used",
        ),
    )

    def test_the_admission_matrix_holds_for_every_flag_combination(self):
        """All four (flag x flag) cells, with the refusal as a COLUMN rather than a separate test.

        Three tests became one table. Each built the same two-attribute namespace, called
        `evaluate_unverifiable_admission`, and asserted one outcome; only the two booleans differed.
        Merging them makes the 2x2 complete - the `neither flag` cell was UNTESTED - and puts the
        refusing cell beside the permitting cells, which is the comparison that matters: the property
        is a PRECONDITION between two flags, and a precondition can be broken in either direction
        (refusing the sanctioned pair, or admitting the lone flag).

        The refused row asserts the message names BOTH flags, because a refusal that names only the
        flag the operator typed leaves them to guess which other flag unlocks it.
        """
        wrong = []
        for case, ok, admitted, refused, applied, why in self.ADMISSION:
            problems = []
            try:
                aggregation = runner_shared.evaluate_unverifiable_admission(
                    self.args(unverifiable_ok=ok, allow_unverifiable=admitted)
                )
            except runner_shared.RunFlagRefusal as exc:
                if not refused:
                    problems.append(f"expected NO refusal, got one: {exc}")
                else:
                    message = str(exc)
                    for needle in ("--unverifiable-ok", "--allow-unverifiable"):
                        if needle not in message:
                            problems.append(
                                f"the refusal does not name {needle!r}: {message!r}. An operator "
                                "must be told BOTH the flag they passed and the flag that admits it"
                            )
            else:
                if refused:
                    problems.append(
                        f"expected a RunFlagRefusal, got applied="
                        f"{aggregation.unverifiable_ok_applied!r} with refusals="
                        f"{aggregation.refusals!r}"
                    )
                else:
                    if aggregation.unverifiable_ok_applied is not applied:
                        problems.append(
                            f"expected unverifiable_ok_applied={applied}, got "
                            f"{aggregation.unverifiable_ok_applied!r}"
                        )
                    if aggregation.refusals != ():
                        problems.append(
                            f"a legal combination must carry NO refusals, got "
                            f"{aggregation.refusals!r}"
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
            f"the `--unverifiable-ok` precondition is wrong in {len(wrong)} of "
            f"{len(self.ADMISSION)} flag combinations. READ THE DIRECTION: if the `ALONE` row stopped "
            "refusing, one flag now neutralizes the verification gate on its own, which is the "
            "permissive failure and the dangerous one. If the `both flags` row started refusing, the "
            "flag is unusable and the refusal row above proves nothing. FIX: the rule is "
            "`zub5f1`'s and lives in `run_evidence.aggregate_run_exit`; this layer supplies the two "
            f"flags and reports what that predicate returned.\n" + "\n".join(wrong),
        )

    def test_the_aggregation_rule_is_not_reimplemented_in_the_runners(self):
        """`zub5f1` owns the aggregate rule; this surface supplies the flags and CALLS it.

        REPLACES A SOURCE-TEXT PIN. It read `inspect.getsource(module)` for three modules and asserted
        `"CONTRIBUTION_NEUTRAL" not in source`. That is a change-detector on a NAME: renaming the
        constant in `run_evidence` would make the guard vacuous everywhere at once, and a runner that
        re-decided neutrality by comparing statuses directly (never naming the constant) would pass it.
        It also failed on any comment that mentioned the constant in order to warn against copying it.

        Now asserted by DELEGATION, which is the property the pin was gesturing at: `aggregate_run_exit`
        is replaced with a spy, and the flag layer must have called it with exactly the two inputs the
        decision depends on. A layer carrying its own copy of the rule would reach its verdict without
        calling the spy at all, so the empty call list IS the fork.
        """
        from agent_workflows import run_evidence

        calls = []
        real = run_evidence.aggregate_run_exit

        def spy(*args, **kwargs):
            calls.append(kwargs)
            return real(*args, **kwargs)

        with mock.patch.object(run_evidence, "aggregate_run_exit", spy):
            with self.assertRaises(runner_shared.RunFlagRefusal):
                runner_shared.evaluate_unverifiable_admission(
                    self.args(unverifiable_ok=True)
                )
        self.assertEqual(
            calls,
            [{"unverifiable_ok": True, "unverifiable_admitted": False}],
            "the flag layer must reach its verdict by CALLING `run_evidence.aggregate_run_exit` with "
            "the operator's two flags. An empty list here means this layer decided aggregate "
            "neutrality itself, which is the second copy `zub5f1` exists to prevent; a different "
            "argument set means the flags are being renamed or defaulted on the way in",
        )
        self.assertTrue(
            hasattr(run_evidence, "REFUSAL_UNVERIFIABLE_OK_UNADMITTED"),
            "the refusal predicate must come from run_evidence",
        )

    def test_the_refusal_message_is_the_predicates_own(self):
        """Left separate: materially different setup (it reaches into `aggregate_run_exit`'s refusal
        list to pull the predicate's own `details` string before comparing)."""
        from agent_workflows import run_evidence

        aggregation = run_evidence.aggregate_run_exit(
            [], unverifiable_ok=True, unverifiable_admitted=False
        )
        predicate = next(
            r
            for r in aggregation.refusals
            if r.name == run_evidence.REFUSAL_UNVERIFIABLE_OK_UNADMITTED
        )
        with self.assertRaises(runner_shared.RunFlagRefusal) as ctx:
            runner_shared.evaluate_unverifiable_admission(
                self.args(unverifiable_ok=True)
            )
        self.assertIn(predicate.details, str(ctx.exception))


class RetryBudgetTests(unittest.TestCase):
    """E-04: the flag, its precedence, and `sq61qd`'s bound CALLED rather than re-checked."""

    #: (case, CLI value, expected effective integer or None when it must be REFUSED, why this row)
    #:
    #: THE BOUND VALUES ARE LITERAL, and deliberately so. Referencing `run_recovery`'s own constants
    #: would make a WIDENING invisible, because the constant and the check move together; the range is
    #: an operator-facing contract stated in `--help` ("an integer 0..10 inclusive"), so a change to it
    #: must fail here rather than silently redefine what the flag accepts.
    BUDGETS = (
        (
            "omitted",
            None,
            2,
            "the DEFAULT tier of spec 2.1's precedence. An omitted flag must resolve to 2, not to "
            "None: a bare `None` in frozen state forces every later reader to re-resolve it, and to "
            "re-resolve it differently",
        ),
        (
            "an explicit 7",
            7,
            7,
            "the CLI tier OVERRIDES the default, which is the whole point of the flag. Note spec "
            "2.1's MIDDLE tier (repository policy) does not exist; see this flag's `--help`",
        ),
        (
            "zero",
            0,
            0,
            "`0` means NO retries and is a REAL value. An `if value:` test reads it as unset and "
            "silently restores two retries, which is the opposite of what the operator asked for and "
            "is invisible in the run's own report",
        ),
        (
            "the lower bound",
            0,
            0,
            "the boundary is INCLUSIVE, asserted separately from the semantic zero row above so an "
            "off-by-one at the bottom of the range is named as a bound error",
        ),
        (
            "the upper bound",
            10,
            10,
            "the upper boundary is INCLUSIVE too. An exclusive comparison here rejects a value "
            "`--help` promises is legal",
        ),
        (
            "negative",
            -1,
            None,
            "a negative retry count has no meaning, and accepting one produces a loop bound nothing "
            "downstream checks again",
        ),
        (
            "one past the upper bound",
            11,
            None,
            "the off-by-one case. It is the row that fails if the comparison is widened, and the "
            "reason the bound has exactly ONE definition (`sq61qd`'s) rather than a copy per caller",
        ),
        (
            "far out of range",
            999,
            None,
            "a plainly wrong value must be refused by the same rule as the near miss, so the refusal "
            "is a RANGE check and not a hardcoded rejection of 11",
        ),
    )

    def test_every_budget_value_resolves_or_refuses_and_freezes_the_same_way(self):
        """The range, the default, and the FROZEN value in one table, with freeze as a column.

        Six tests became one. `test_the_default_is_still_two`, `test_a_cli_value_overrides_the_default`,
        `test_zero_is_legal_and_is_not_treated_as_unset`, `test_both_bounds_are_accepted`,
        `test_an_out_of_range_value_is_refused`, and `test_the_frozen_value_is_the_effective_integer`
        all fed one integer to the resolver and compared one answer; only the integer differed.

        FREEZE IS A COLUMN, NOT A SEVENTH TEST, and that is the strengthening this merge buys. The old
        freeze test checked only two values (None and 5), so nothing asserted that an out-of-range
        value is refused at FREEZE time as well as at resolve time - which is the path that matters,
        because freezing is where the value becomes durable run state. Every row now asserts both
        entry points agree, and the refused rows require the refusal to survive freezing rather than
        being written into the ledger.
        """
        wrong = []
        for case, value, expected, why in self.BUDGETS:
            base = {row.dest: False for row in runner_shared.RUN_POLICY_FLAGS}
            base["retry_budget"] = value
            problems = []

            try:
                got = runner_shared.resolve_retry_budget(value)
            except runner_shared.RunFlagRefusal as exc:
                if expected is not None:
                    problems.append(
                        f"`resolve_retry_budget` refused a legal value: {exc}"
                    )
                elif "0..10" not in str(exc):
                    problems.append(
                        f"the refusal does not state the legal range `0..10`: {str(exc)!r}. The "
                        "operator needs the bound, not just a rejection"
                    )
            else:
                if expected is None:
                    problems.append(
                        f"`resolve_retry_budget` ACCEPTED an out-of-range value, returning {got!r}"
                    )
                elif got != expected:
                    problems.append(
                        f"`resolve_retry_budget` returned {got!r}, expected {expected!r}"
                    )

            try:
                frozen = runner_shared.freeze_run_policy_flags(
                    argparse.Namespace(**base)
                )["retry_budget"]
            except runner_shared.RunFlagRefusal as exc:
                if expected is not None:
                    problems.append(
                        f"`freeze_run_policy_flags` refused a legal value: {exc}"
                    )
            else:
                if expected is None:
                    problems.append(
                        f"`freeze_run_policy_flags` froze an out-of-range value as {frozen!r}, so a "
                        "refused value would be written into durable run state"
                    )
                elif frozen != expected:
                    problems.append(
                        f"the FROZEN value is {frozen!r} but the resolved value is {expected!r}; "
                        "frozen state must hold the EFFECTIVE integer, never a value a later reader "
                        "has to re-resolve"
                    )

            if problems:
                wrong.append(
                    f"  {case} ({value!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`--retry-budget` resolution is wrong for {len(wrong)} of {len(self.BUDGETS)} values. "
            "READ THEM TOGETHER: if BOTH boundary rows fail while the interior rows pass, a "
            "comparison flipped between `<=` and `<` and the range is off by one at each end; if the "
            "`zero` rows fail alone, something is testing truthiness instead of `is not None` and a "
            "no-retry run silently got two retries; if only the FREEZE half of a row fails, the two "
            "entry points disagree and durable run state no longer matches what the flag layer "
            "accepted. FIX: the bound has exactly ONE definition, "
            f"`run_recovery.validate_retry_budget`; call it, never re-compare.\n"
            + "\n".join(wrong),
        )

    def test_the_bound_is_sq61qds_and_is_not_re_checked_here(self):
        """CALLED, not copied: `sq61qd` made `validate_retry_budget` the single definition.

        REPLACES TWO SOURCE-TEXT PINS with the delegation they were approximating. The old test read
        `inspect.getsource(runner_shared.resolve_retry_budget)`, asserted the substring
        `"validate_retry_budget"` appeared, and then asserted the literal `"10"` did NOT appear after
        the docstring. Both are change-detectors, and the second is actively misleading: `"10"` is a
        SUBSTRING, so a legitimate `100`, a line number, or an id6 containing those digits would fail a
        test about a range bound, while a second copy written as `if value > ten_limit` would pass it.
        The first could equally be satisfied by a comment naming the function.

        Now asserted behaviorally, by replacing BOTH shared definitions with sentinels: if this layer
        calls the shared validator, patching it changes this layer's answer. A private copy of the
        bound keeps returning the real value, so the sentinel never appears.
        """
        from agent_workflows import run_recovery

        with mock.patch.object(run_recovery, "validate_retry_budget", lambda value: 99):
            self.assertEqual(
                runner_shared.resolve_retry_budget(3),
                99,
                "patching `run_recovery.validate_retry_budget` must change this layer's answer. "
                "Getting 3 back means the flag layer validated the value ITSELF, which is the second "
                "copy of the bound `sq61qd` collapsed into one",
            )
        with mock.patch.object(run_recovery, "DEFAULT_RETRY_LIMIT", 7):
            self.assertEqual(
                runner_shared.resolve_retry_budget(None),
                7,
                "the DEFAULT is `run_recovery.DEFAULT_RETRY_LIMIT` too, not a literal 2 spelled here. "
                "Getting 2 back means the default has two definitions that can drift",
            )
        self.assertEqual(
            run_recovery.DEFAULT_RETRY_LIMIT,
            2,
            "and the shared default is still 2, so the rows above pin a real contract",
        )
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.validate_retry_budget(11)

    # NOTE: a `test_an_out_of_range_value_refuses_the_whole_run` was REMOVED as a source-text pin
    # strictly weaker than a behavioral test that already exists. It read
    # `inspect.getsource(initialize_run)` on each host and asserted the substring
    # `"resolve_retry_budget"` appeared somewhere in it - which a COMMENT satisfies, and which says
    # nothing about whether the call is REACHED, whether its refusal propagates, or whether a run
    # directory was created before it fired.
    # `test_every_budget_value_resolves_or_refuses_and_freezes_the_same_way` (this class) drives the
    # real resolver over every in-range and out-of-range value on BOTH hosts, and
    # `RefusalBehaviorTests.test_every_refused_invocation_leaves_no_durable_run_state` drives
    # `initialize_run` on a real repository and asserts BOTH that it refuses AND that no `run-*`
    # directory survives. That pair is the property; the pin was a proxy for it.


class UnimplementedFlagRefusalTests(unittest.TestCase):
    """E-05: `--follow-generated` and `--with-dependencies` REFUSE; they never silently no-op.

    A pasted `--help` does not prove this. A flag that parses and does nothing is strictly WORSE than
    no flag, because an operator who passes `--with-dependencies` and gets no closure expansion has
    been told a falsehood about what the run enforced. Only an observed refusal proves otherwise.
    """

    def unimplemented(self) -> list:
        return [row for row in runner_shared.RUN_POLICY_FLAGS if not row.implemented]

    def test_the_predicate_refuses_exactly_the_unimplemented_flags_and_nothing_else(
        self,
    ):
        """Which flags refuse, which stay silent, and the exact membership, in one report.

        Four tests became one. `test_there_are_exactly_two_and_they_are_the_expected_two`,
        `test_each_refuses_when_passed`, `test_not_passing_them_is_silent`, and
        `test_an_implemented_flag_is_never_refused_by_this_predicate` are four views of ONE predicate's
        truth table over the same table of rows: the membership claim, the refusing cells, the silent
        cells, and the must-never-refuse cells. They fail together whenever `implemented` is edited on
        any row, and the FIX is the same in every case (flip `implemented`, or stop refusing), so the
        useful report is which flags moved in which direction.

        THE MEMBERSHIP IS PINNED EXPLICITLY, deliberately, even though every other check derives from
        `row.implemented`. A derived-only suite would go green the instant a flag's `implemented` flag
        was flipped without its behavior being built - the refusal would simply stop being expected -
        which is exactly the silent no-op this class exists to forbid. So the remaining flag is NAMED,
        and landing another (or shipping this one) is required to touch this list on purpose.

        IT IS NOW A LIST OF ONE, AND THE NARROWING WAS DELIBERATE. `--with-dependencies` LEFT this set
        when depclosure 01 (`dhycim`) built its behavior in `runner_shared.expand_dependency_closure`,
        so this class now iterates ONE row where it used to iterate two and its coverage is genuinely
        half what it was. That is the correct direction (a refusal was replaced by a behavior, not by a
        shrug), and it is stated here rather than left for a reader to infer from a shorter list. The
        refusal cells, the silent cells and the implemented cells below are unchanged in KIND.

        `--follow-generated` STAYS, and must not be flipped alongside its former twin: no mechanism in
        this package detects that an agent turn generated a new IPD, so there is nothing to flip to.
        It keeps its `x8diyb` ownership, which is what makes the remaining gap tracked rather than
        forgotten.

        THE SILENT AND REFUSING CELLS ARE IN THE SAME TABLE for the usual reason: a predicate that
        raised unconditionally would satisfy every refusal row on its own, and the `implemented` rows
        are what stop that from passing.
        """
        wrong = []

        expected_names = ["--follow-generated"]
        actual_names = sorted(row.flag for row in self.unimplemented())
        if actual_names != expected_names:
            wrong.append(
                f"  MEMBERSHIP: `implemented=False` rows are {actual_names}, expected "
                f"{expected_names}\n"
                "    this row exists because: every other check here DERIVES from `implemented`, so "
                "flipping that field on a flag whose behavior was never built would silently stop "
                "the refusal being expected. Naming the two makes that edit deliberate"
            )

        for row in self.unimplemented():
            problems = []
            try:
                runner_shared.refuse_unimplemented_run_flags(
                    argparse.Namespace(**{row.dest: True})
                )
            except runner_shared.RunFlagRefusal as exc:
                message = str(exc)
                for needle, why in (
                    (
                        row.flag,
                        "the operator must be told WHICH flag was refused; a generic refusal leaves "
                        "them to bisect their own command line",
                    ),
                    (
                        "not yet implemented",
                        "the refusal must say the behavior does not exist, rather than reading as a "
                        "validation error the operator could fix by changing the value",
                    ),
                    (
                        "x8diyb",
                        "the owning backlog item, so the refusal points at tracked work instead of a "
                        "dead end",
                    ),
                ):
                    if needle not in message:
                        problems.append(
                            f"the refusal omits {needle!r} ({why}); it reads: {message!r}"
                        )
            else:
                problems.append(
                    "passing it did NOT refuse. A flag that parses and does nothing is strictly "
                    "WORSE than no flag: an operator who passes it believes the run enforced "
                    "something it never did"
                )
            if problems:
                wrong.append(
                    f"  {row.flag} passed (implemented=False):\n"
                    + "".join(f"    - {p}\n" for p in problems).rstrip("\n")
                )

        try:
            runner_shared.refuse_unimplemented_run_flags(
                argparse.Namespace(**{row.dest: False for row in self.unimplemented()})
            )
        except runner_shared.RunFlagRefusal as exc:
            wrong.append(
                f"  the unimplemented flags NOT passed:\n"
                f"    - refused anyway: {exc}\n"
                "    this row exists because: an unused flag must be SILENT. Refusing here would "
                "break every ordinary run, and it is also what stops the refusal rows above from "
                "being satisfied by a predicate that raises unconditionally"
            )

        try:
            runner_shared.refuse_unimplemented_run_flags(
                argparse.Namespace(
                    **{
                        row.dest: True
                        for row in runner_shared.RUN_POLICY_FLAGS
                        if row.implemented
                    }
                )
            )
        except runner_shared.RunFlagRefusal as exc:
            wrong.append(
                f"  EVERY implemented flag passed at once:\n"
                f"    - this predicate refused a SHIPPING flag: {exc}\n"
                "    this row exists because: the predicate must key on `implemented` and on nothing "
                "else. Refusing a working flag here takes a shipped behavior away from operators"
            )

        self.assertEqual(
            wrong,
            [],
            f"the unimplemented-flag refusal is wrong in {len(wrong)} way(s). READ THE DIRECTION: a "
            "MEMBERSHIP failure alone means `implemented` was edited, and the question is whether the "
            "behavior actually shipped (then this list is stale) or whether the field was flipped to "
            "quiet a refusal (then the flag now silently no-ops, which is the defect). A refusal that "
            "stopped firing while membership held is the silent no-op outright. A refusal firing on "
            "the SILENT or the IMPLEMENTED rows breaks working runs instead. FIX: `implemented` on "
            f"the `RUN_POLICY_FLAGS` row is the single switch; the help text and this refusal both "
            "read it.\n" + "\n".join(wrong),
        )

    # NOTE: a `test_both_runners_refuse_before_any_durable_state` was REMOVED as a source-text pin.
    # It read `inspect.getsource(initialize_run)`, split the text on the literal `"run_dir = state_root"`
    # and asserted `"refuse_unimplemented_run_flags"` appeared in the PREFIX - a claim about the
    # relative BYTE OFFSET of two substrings, which breaks on any reordering or reformatting of a
    # function it is not about, and which a comment placed above that literal satisfies outright.
    # `RefusalBehaviorTests.test_every_refused_invocation_leaves_no_durable_run_state` asserts the
    # actual property on both hosts for every refusing flag: `initialize_run` raises, AND
    # `.aw/records/runs` contains no `run-*` directory afterwards. That is an OBSERVED absence of
    # durable state, which is what "before any durable state" means; the text order was a proxy.


class FreezeAndResumeTests(unittest.TestCase):
    """E-06: values frozen at queue build; `--retry-budget` refused on resume; omission preserves."""

    def resume_args(self, **kw) -> argparse.Namespace:
        base = {row.dest: None for row in runner_shared.RUN_POLICY_FLAGS}
        base.update(kw)
        return argparse.Namespace(**base)

    def test_every_flag_marked_freeze_is_frozen(self):
        """Kept separate: a COMPLETENESS claim over the table, not a case of resume behavior.

        Asserts that every row declaring `freeze=True` actually appears in the frozen dict, which is
        about the freeze function honoring its own table rather than about any particular flag's
        value. Merging it into the resume table below would mix a structural claim into a
        value-per-case table and make one failure ambiguous between the two.
        """
        base = {row.dest: False for row in runner_shared.RUN_POLICY_FLAGS}
        base["retry_budget"] = None
        frozen = runner_shared.freeze_run_policy_flags(argparse.Namespace(**base))
        missing = [
            row.flag
            for row in runner_shared.RUN_POLICY_FLAGS
            if row.freeze and row.dest not in frozen
        ]
        self.assertEqual(
            missing,
            [],
            "flag(s) declared `freeze=True` are ABSENT from the frozen dict, so their policy is read "
            f"from `args` on every resume and can change between the first turn and the last: {missing}",
        )

    #: (case, kwargs handed to `resume`, refused?, the state BEFORE, the state expected AFTER,
    #: whether the apply must report a change, why this row exists)
    #:
    #: `None` for "expected after" means the row only asserts the refusal, since a refused invocation
    #: never reaches the apply step.
    RESUME = (
        (
            "no flag passed at all",
            {},
            False,
            {"allow_mixed": True, "full_auto": True, "unattended": True},
            {"allow_mixed": True, "full_auto": True, "unattended": True},
            False,
            "THE LOAD-BEARING ROW, and the one `default=None` exists for: an OMITTED flag must leave "
            "frozen policy untouched and report NO change, so a resume does not silently rewrite the "
            "policy the run was started under. With `default=False` this function could not tell "
            "`--no-allow-mixed` from silence and would clobber all three on every resume",
        ),
        (
            "--no-full-auto passed explicitly",
            {"full_auto": False},
            False,
            {"full_auto": True},
            {"full_auto": False},
            True,
            "the SHIPPED `--full-auto` resume behavior, preserved and generalized rather than "
            "changed: a value the operator actually typed OVERWRITES the frozen one. This row is why "
            "the rule is `is None` and not `if not value`, since the typed value here is False",
        ),
        (
            "--full-auto passed on resume",
            {"full_auto": True},
            False,
            {"full_auto": False, "unattended": False},
            {"full_auto": True, "unattended": False},
            True,
            "THE IMPLICATION IS NOT RE-APPLIED. `--full-auto` implies `--unattended` at queue build "
            "(spec `:134`), but flipping a SECOND frozen option the operator did not name on a resume "
            "is exactly the hidden write the freeze exists to prevent. `unattended` staying False is "
            "the whole assertion",
        ),
        (
            "--retry-budget 5 passed on resume",
            {"retry_budget": 5},
            True,
            {"retry_budget": 2},
            {"retry_budget": 2},
            False,
            "spec `:131` freezes this one flag outright ('the frozen value cannot change on "
            "resume'), so it REFUSES rather than overwriting. The apply half is asserted too: even "
            "if the refusal were skipped, the value must not be written, which is the fail-safe "
            "direction",
        ),
        (
            "--retry-budget 0 passed on resume",
            {"retry_budget": 0},
            True,
            {"retry_budget": 2},
            {"retry_budget": 2},
            False,
            "`0` IS A REAL VALUE. An `if value:` guard lets it through and silently restores the "
            "default two retries; the check must be `is not None`. This is the same zero-is-not-unset "
            "hazard `RetryBudgetTests` pins at the resolve layer, one layer up",
        ),
    )

    def test_the_resume_rules_hold_for_every_flag_case(self):
        """Refusal and application as COLUMNS of one table, per resume case.

        Seven tests became one. `test_retry_budget_with_resume_is_refused`,
        `test_retry_budget_zero_with_resume_is_also_refused`,
        `test_resume_without_the_frozen_flag_is_allowed`,
        `test_an_omitted_flag_on_resume_does_not_clobber_the_frozen_value`,
        `test_a_passed_flag_on_resume_overwrites_the_frozen_value`,
        `test_resume_does_not_reapply_the_unattended_implication`, and
        `test_resume_never_applies_a_refused_flag` each built the same all-`None` resume namespace,
        set one or two keys, and asserted one outcome.

        REFUSE AND APPLY ARE TWO COLUMNS RATHER THAN TWO CLASSES, which is the strengthening. Split
        across separate tests, the refusal cases never checked what the apply step would have done and
        the apply cases never checked whether a refusal should have fired first - so a refusal deleted
        while the apply step happily wrote the value was reported as ONE failure about a missing
        exception, with the durable write it lets through invisible. Every row now runs BOTH functions
        and asserts the state either way, so the two halves of the freeze cannot drift.

        The `changed` return is a column too, because the caller SAVES on the strength of it: a resume
        that returns True having changed nothing rewrites state files for no reason, and one that
        returns False having changed something loses the operator's edit.
        """
        wrong = []
        for (
            case,
            kwargs,
            refused,
            before,
            expected_after,
            expect_changed,
            why,
        ) in self.RESUME:
            problems = []
            args = self.resume_args(**kwargs)

            try:
                runner_shared.refuse_frozen_flags_on_resume(args)
            except runner_shared.RunFlagRefusal as exc:
                if not refused:
                    problems.append(f"refused a legal resume: {exc}")
                else:
                    message = str(exc)
                    for needle in ("--retry-budget", "frozen"):
                        if needle not in message:
                            problems.append(
                                f"the refusal omits {needle!r}, so it does not tell the operator "
                                f"which flag is frozen or why: {message!r}"
                            )
            else:
                if refused:
                    problems.append(
                        "expected a RunFlagRefusal and got none, so a flag spec 2.1 FREEZES was "
                        "silently accepted on resume"
                    )

            state = {"options": dict(before)}
            changed = runner_shared.apply_run_policy_flags_on_resume(state, args)
            if state["options"] != expected_after:
                problems.append(
                    f"applying left options={state['options']!r}, expected {expected_after!r}"
                )
            if changed is not expect_changed:
                problems.append(
                    f"the apply reported changed={changed!r}, expected {expect_changed!r}; the "
                    "caller saves state on the strength of this value"
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
            f"resume policy handling is wrong for {len(wrong)} of {len(self.RESUME)} cases. READ THEM "
            "TOGETHER: if the OMITTED row fails alongside the passed-flag rows, `default=None` was "
            "lost and resume can no longer distinguish an explicit OFF from silence, which clobbers "
            "frozen policy on every resume rather than in one case. If a refusal stopped firing but "
            "the state is still unchanged, the fail-safe held and only the operator's error message "
            "is missing; if the state CHANGED too, a frozen value was rewritten mid-run and the "
            "run's own ledger no longer describes the policy it executed under. FIX: the rule is "
            "`None` means ABSENT (leave frozen) and any other value means TYPED (overwrite), plus "
            f"`resume_rule == RESUME_REFUSE` short-circuits before either.\n"
            + "\n".join(wrong),
        )

    def test_both_runners_refuse_and_apply_on_resume(self):
        """BOTH hosts run the shared refuse-then-apply pair on a REAL resume, end to end.

        REPLACES TWO SOURCE-TEXT PINS. The old test read `inspect.getsource(main)` on each host and
        asserted the substrings `"refuse_frozen_flags_on_resume"` and
        `"apply_run_policy_flags_on_resume"` appeared somewhere in it. Both names appear in `main`'s
        own explanatory COMMENTS in this package (the oc comment block above the call explains the
        `:129` versus `:131` divergence and names both functions), so the pin was satisfied by prose
        and would have stayed green if either call had been deleted while its comment remained.

        Now both halves are OBSERVED through `main`: a real run is created, and then resuming it with
        `--retry-budget` must exit non-zero naming the frozen flag (the REFUSE half), while resuming it
        with `--no-full-auto` must rewrite the frozen option in state (the APPLY half). A comment
        cannot produce an exit code or a state write.
        """
        import contextlib
        import io
        import tempfile
        from pathlib import Path as _P

        wrong = []
        for runner in BOTH:
            with tempfile.TemporaryDirectory() as td:
                repo, _plan = _make_probe_repo(_P(td))
                args = _parse(
                    runner, ["start", "prb001", "--repo", str(repo), "--full-auto"]
                )
                args.prepare_only = True
                with (
                    contextlib.redirect_stdout(io.StringIO()),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    run_dir = _MODULES[runner].initialize_run(args)
                run_id = run_dir.name

                err = io.StringIO()
                with (
                    contextlib.redirect_stdout(io.StringIO()),
                    contextlib.redirect_stderr(err),
                ):
                    rc = _MODULES[runner].main(
                        [
                            "resume",
                            run_id,
                            "--repo",
                            str(repo),
                            "--retry-budget",
                            "5",
                        ]
                    )
                if rc == 0 or "--retry-budget" not in err.getvalue():
                    wrong.append(
                        f"  {runner}: REFUSE half. `resume --retry-budget 5` exited {rc} with "
                        f"stderr {err.getvalue()!r}; it must exit nonzero naming the frozen flag "
                        "(spec `:131`). A zero exit means `refuse_frozen_flags_on_resume` is not "
                        "reached from `main`"
                    )

                with (
                    contextlib.redirect_stdout(io.StringIO()),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    _MODULES[runner].main(
                        ["resume", run_id, "--repo", str(repo), "--no-full-auto"]
                    )
                options = runner_shared.load_state(run_dir)["options"]
                if options.get("full_auto") is not False:
                    wrong.append(
                        f"  {runner}: APPLY half. after `resume --no-full-auto` the frozen "
                        f"`full_auto` is {options.get('full_auto')!r} and must be False. An "
                        "unchanged True means `apply_run_policy_flags_on_resume` is not reached from "
                        "`main`, so an operator's explicit resume flag is silently discarded"
                    )
                elif options.get("unattended") is not True:
                    wrong.append(
                        f"  {runner}: APPLY half went too far. `unattended` is "
                        f"{options.get('unattended')!r} and must still be True: it was frozen True by "
                        "`--full-auto` at queue build, and resume must not re-derive an implication "
                        "the operator did not name"
                    )

        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(BOTH) * 2} resume-wiring half(s) are not reached from `main`. "
            "Both halves are needed and they fail independently: without REFUSE, a frozen policy can "
            "be changed mid-run and the run's ledger stops describing what it executed under; "
            "without APPLY, a flag the operator explicitly typed on resume does nothing while the "
            "command reports success. A failure on ONE host only is the asymmetry this file exists "
            "for - the two `main` functions are separate code and only the helpers are shared.\n"
            + "\n".join(wrong),
        )

    def test_every_resume_declaration_defaults_to_None(self):
        """`default=None` is the mechanism: without it, resume cannot tell `--no-X` from silence.

        Kept separate from the resume table: this is a claim about the PARSER's declaration rather
        than about the behavior of a resume case, and it is the precondition that makes every row of
        that table meaningful, so a reader wants it to fail with its own name.
        """
        wrong = []
        for runner in BOTH:
            for row in runner_shared.RUN_POLICY_FLAGS:
                action = _action_for_flag(runner, "resume", row.flag)
                if action is None:
                    wrong.append(
                        f"  {row.flag} on {runner}: not registered on `resume` at all"
                    )
                elif action.default is not None:
                    wrong.append(
                        f"  {row.flag} on {runner}: default is {action.default!r}, must be None"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} resume declaration(s) do not default to None. This is the MECHANISM behind "
            "every row of `RESUME` above: with any other default, an omitted flag arrives as a real "
            "value and `apply_run_policy_flags_on_resume` cannot distinguish it from one the operator "
            "typed, so frozen policy is clobbered on every resume. FIX: declare `default=None` on the "
            f"`resume` parser; `start` keeps its real default.\n" + "\n".join(wrong),
        )


class FullAutoDefaultNormalizationTests(unittest.TestCase):
    """E-07: `--full-auto` defaults `False` on BOTH hosts, at ALL THREE sites per host.

    A parser-only fix would leave the old behavior live while `--help` claimed otherwise, which is the
    worst of the three outcomes. Before this, `aw agy run <selector>` auto-cleared a `reviewed` plan
    with an approving `- Readiness:` to `auto-approved` and EXECUTED it with no flag passed, so
    execution was opt-OUT on one host and opt-IN on the other.
    """

    #: (case, the argv tail appended to `["start", "demo"]`, the expected `args.full_auto`, why)
    PARSED = (
        (
            "a bare run",
            [],
            False,
            "THE DEFAULT, and the whole point of E-07: execution must be opt-IN. Before the fix this "
            "was True on one host, so `aw agy run <selector>` auto-cleared a `reviewed` plan and "
            "EXECUTED it with no flag passed",
        ),
        (
            "an explicit --full-auto",
            ["--full-auto"],
            True,
            "the CAPABILITY is preserved; only the default changed. Without this row the fix is "
            "satisfiable by a flag that can no longer be turned on at all",
        ),
        (
            "an explicit --no-full-auto",
            ["--no-full-auto"],
            False,
            "the negation must resolve to a real False rather than to None, because `start` freezes "
            "whatever it resolves and a None here would be stored as the frozen policy",
        ),
    )

    def test_the_parsed_value_is_right_for_every_way_of_spelling_the_flag(self):
        """The parser's answer for all three spellings, on both hosts, in one report.

        Three tests became one. `test_site_1_the_parser_default_is_False_on_both_hosts`,
        `test_a_bare_run_does_not_request_auto_approval_on_either_host`, and
        `test_an_explicit_full_auto_still_works_on_both_hosts` all parsed an argv and asserted one
        boolean; only the argv differed. The `action.default` check is folded in because the bare-run
        row IS that default observed through the surface an operator uses, which is strictly stronger:
        a host could set `default=False` on the action and then override the value elsewhere in its
        parse path, and only the parsed row would notice.

        THE POSITIVE ROW IS IN THE TABLE deliberately: a `--full-auto` that no longer turns ON would
        satisfy both False rows, and would present as "the fix worked" while removing a shipped
        capability.
        """
        wrong = []
        for case, tail, expected, why in self.PARSED:
            for runner in BOTH:
                got = _parse(runner, ["start", "demo", *tail]).full_auto
                if got is not expected:
                    wrong.append(
                        f"  {case} on {runner}:\n"
                        f"    - parsed full_auto={got!r}, expected {expected!r}\n"
                        f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.PARSED) * len(BOTH)} (spelling, host) cells parse "
            "`--full-auto` wrongly. READ THE SHAPE: a BARE-run row failing on one host only is the "
            "exact pre-E-07 defect, where execution was opt-OUT on one host and opt-IN on the other. "
            "All three rows failing on one host means that host's registration diverged from the "
            "shared table entirely. The explicit-ON row failing alone means the capability was "
            "removed rather than the default corrected. FIX: `--full-auto` is registered from "
            f"`RUN_POLICY_FLAGS` with `BooleanOptionalAction` and `default=False`.\n"
            + "\n".join(wrong),
        )

    def test_no_fallback_default_for_full_auto_is_True_on_either_host(self):
        """Every `getattr`/`.get` fallback for `full_auto`, read as AST, on both hosts.

        REPLACES THREE REGEX-OVER-SOURCE TESTS with one AST sweep. `test_site_2...`,
        `test_site_3...`, and `test_no_True_default_for_full_auto_survives_anywhere` ran
        `re.findall` over `inspect.getsource(...)` for hand-written patterns like
        `getattr\\(\\s*args,\\s*"full_auto",\\s*(\\w+)\\s*\\)`. Three problems, all of which this
        replacement fixes: a regex over source matches inside COMMENTS and docstrings (so a comment
        showing the old spelling failed the test, and a commented-out line satisfied the catch-all); it
        is whitespace- and formatting-sensitive, so `ruff format` breaking the call across lines makes
        it silently match NOTHING and pass; and it pinned the exact call SITES (`initialize_run`,
        `execute_item`) rather than the property, so moving a read into a helper made the site test
        pass vacuously.

        WHY THIS IS AST AND NOT BEHAVIORAL, unlike the other pins replaced in this file: the property
        is the absence of a bad default on EVERY read, including reads on code paths no test drives (a
        `--full-auto` fallback inside an error-recovery branch, say). `82ca6e96` and `94b00d37` both
        keep AST guards for exactly this reason - they are not text greps, since a comment does not
        parse into a Call node - and the behavioral half is covered next door by
        `FullAutoEndToEndBehaviorTests`, which drives real runs and reads the frozen state.

        IT IS ALSO STRICTER THAN WHAT IT REPLACES. The old tests checked two named functions plus two
        literal spellings; this walks the WHOLE module and reports every `full_auto` fallback with a
        truthy default, wherever it lives, plus any read with NO default at all where a missing key
        would raise.
        """
        import ast
        import inspect

        wrong = []
        for runner in BOTH:
            tree = ast.parse(inspect.getsource(_MODULES[runner]))
            reads = 0
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if (
                    isinstance(func, ast.Name)
                    and func.id == "getattr"
                    and len(node.args) >= 2
                    and isinstance(node.args[1], ast.Constant)
                    and node.args[1].value == "full_auto"
                ):
                    reads += 1
                    default = node.args[2] if len(node.args) > 2 else None
                elif (
                    isinstance(func, ast.Attribute)
                    and func.attr == "get"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and node.args[0].value == "full_auto"
                ):
                    reads += 1
                    default = node.args[1] if len(node.args) > 1 else None
                else:
                    continue
                if default is None:
                    # No explicit default. Legal for `.get`, which yields None (falsy, so opt-in
                    # holds); reported only for `getattr`, where it RAISES on an older namespace.
                    if isinstance(func, ast.Name):
                        wrong.append(
                            f"  {runner} line {node.lineno}: "
                            f"`{ast.unparse(node)}` has NO default, so it raises AttributeError on a "
                            "namespace built before this flag existed instead of falling back to "
                            "opt-in"
                        )
                    continue
                if not (
                    isinstance(default, ast.Constant) and default.value in (False, None)
                ):
                    wrong.append(
                        f"  {runner} line {node.lineno}: "
                        f"`{ast.unparse(node)}` falls back to `{ast.unparse(default)}`, which is not "
                        "False. A truthy fallback makes auto-approval opt-OUT on any path where the "
                        "value is absent, which is precisely the pre-E-07 defect: it reappears only "
                        "for an OLDER run record or an argv shape the flag never reached"
                    )
            if reads == 0:
                wrong.append(
                    f"  {runner}: NO `full_auto` fallback read was found at all, so this guard is "
                    "vacuous on this host. Either the reads were renamed (update this walk) or the "
                    "flag stopped being consulted, which would make `--full-auto` inert"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} `full_auto` fallback problem(s) across both hosts. Each one is a path where "
            "auto-approval is opt-OUT: a plan with `Status: reviewed` and an approving `- Readiness:` "
            "gets cleared to `auto-approved` and EXECUTED with no flag passed. That is not "
            "hypothetical - it was the shipped behavior of one host before E-07. If the failure is a "
            "VACUOUS-GUARD line instead, the reads moved and this walk needs updating rather than the "
            "source. FIX: every fallback for this dest must be `False`; the parser's own default "
            f"(asserted above) is not enough, because these reads fire when the attribute is ABSENT.\n"
            + "\n".join(wrong),
        )

    def test_the_resume_declaration_is_still_None_on_both_hosts(self):
        """F-6's mechanism is a DIFFERENT concern and was already correct; it stays untouched.

        Kept separate from the `PARSED` table above even though both ask the parser about the same
        flag: `start` must default to a real False (it FREEZES what it resolves) while `resume` must
        default to None (it must distinguish silence from an explicit `--no-full-auto`). Those are
        opposite requirements for one flag, so a single row cannot express both and merging them would
        invite someone to "fix" the inconsistency.
        """
        for runner in BOTH:
            action = _action_for_flag(runner, "resume", "--full-auto")
            with self.subTest(runner=runner):
                assert action is not None
                self.assertIsNone(action.default)


class FullAutoEndToEndBehaviorTests(unittest.TestCase):
    """E-07's BEHAVIOR, not just its default: a bare run no longer auto-approves.

    V-07 requires this because a pasted parser default proves nothing about what the run DOES. The
    auto-approve decision lives in `initialize_run`, so this drives that function on a real repository
    holding a `Status: reviewed` plan whose `- Readiness:` is approving - the exact input that was
    silently cleared and executed by `aw agy run <selector>` with no flag passed.
    """

    # The fixture is the MODULE-LEVEL `_make_probe_repo`, shared with `FreezeAndResumeTests`, so a
    # resume assertion and a start assertion cannot come to disagree about what plan they ran against.
    make_repo = staticmethod(_make_probe_repo)

    def run_and_read_status(self, runner: str, argv: list):
        """`initialize_run` on a fresh repo; returns (plan text after, queue initial_status)."""
        import tempfile
        from pathlib import Path as _P

        with tempfile.TemporaryDirectory() as td:
            repo, plan = self.make_repo(_P(td))
            args = _parse(runner, ["start", "prb001", "--repo", str(repo), *argv])
            args.prepare_only = True
            run_dir = _MODULES[runner].initialize_run(args)
            state = runner_shared.load_state(run_dir)
            entry = state["queue"][0]
            # The plan may have been MOVED by an auto-approve, so re-read by id6 rather than by path.
            found = list((repo / ".aw" / "records" / "plans").rglob("*prb001*.ipd.md"))
            self.assertEqual(len(found), 1, found)
            return found[0].read_text(encoding="utf-8"), entry["initial_status"], state

    #: (case, argv tail, expected `- Status:` in the plan on disk after the run, expected queue
    #: `initial_status`, expected frozen `full_auto`, expected frozen `unattended`, why)
    AUTO_APPROVE = (
        (
            "a bare run",
            [],
            "reviewed",
            "reviewed",
            False,
            False,
            "THE DEFECT, END TO END. This exact plan (`Status: reviewed` with an approving "
            "`- Readiness:`) was silently cleared to `auto-approved` and EXECUTED by "
            "`aw agy run <selector>` with no flag passed, so execution was opt-OUT on one host and "
            "opt-IN on the other. The plan text on DISK is asserted, not just the parsed flag, "
            "because the auto-approve WRITES to the plan and moves it",
        ),
        (
            "an explicit --full-auto",
            ["--full-auto"],
            "auto-approved",
            "auto-approved",
            True,
            True,
            "the CAPABILITY is preserved; only the default changed. It also carries spec `:134`'s "
            "implication observed in DURABLE state rather than in a freeze-function return: "
            "`unattended` must be frozen True, because that is the value every later turn of this run "
            "reads when deciding whether a gate may prompt",
        ),
    )

    def test_auto_approval_happens_only_when_the_flag_asks_for_it(self):
        """Both real runs, on both hosts, with the plan on disk and the frozen state as columns.

        Two tests became one table. Both called `run_and_read_status`, then asserted the plan's status
        on disk, the queue's `initial_status`, and the frozen `full_auto` - the same four claims about
        two argvs, which is a data row. Merging them puts the ON and OFF cases side by side, and that
        adjacency is the point: `--full-auto` is a flag whose default changed, so the two realistic
        regressions are opposite (it auto-approves when it should not, or it no longer can) and a
        reader needs to see which way it went.

        THE FROZEN `unattended` COLUMN is asserted on both rows rather than only the positive one, so
        the implication is pinned as CONDITIONAL: a freeze that set `unattended` unconditionally would
        satisfy a positive-only check while making every bare run unattended, silently disabling every
        interactive gate.
        """
        wrong = []
        for (
            case,
            tail,
            plan_status,
            initial,
            full_auto,
            unattended,
            why,
        ) in self.AUTO_APPROVE:
            for runner in BOTH:
                text, got_initial, state = self.run_and_read_status(runner, tail)
                problems = []
                if f"- Status: {plan_status}" not in text:
                    problems.append(
                        f"the plan ON DISK does not carry `- Status: {plan_status}`; its text is "
                        f"{text.strip()[:200]!r}"
                    )
                if plan_status != "auto-approved" and "auto-approved" in text:
                    problems.append(
                        "the plan text mentions `auto-approved` at all, so this run promoted a plan "
                        "the operator never authorized"
                    )
                if got_initial != initial:
                    problems.append(
                        f"the queue's frozen `initial_status` is {got_initial!r}, expected "
                        f"{initial!r}"
                    )
                if state["options"]["full_auto"] is not full_auto:
                    problems.append(
                        f"frozen full_auto={state['options']['full_auto']!r}, expected {full_auto!r}"
                    )
                if state["options"]["unattended"] is not unattended:
                    problems.append(
                        f"frozen unattended={state['options']['unattended']!r}, expected "
                        f"{unattended!r} (spec `:134`: `--full-auto` implies `--unattended`, and "
                        "implies it ONLY when passed)"
                    )
                if problems:
                    wrong.append(
                        f"  {case} on {runner}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.AUTO_APPROVE) * len(BOTH)} (case, host) cells got "
            "auto-approval wrong on a REAL run. READ THE DIRECTION: the BARE row failing means a "
            "reviewed plan is promoted and executed with no flag passed, which is unauthorized "
            "execution and the defect E-07 exists to prevent; the EXPLICIT row failing means the "
            "capability is gone and operators have no way to auto-approve at all. A failure on ONE "
            "host only is the original asymmetry. If only the `unattended` column fails on the bare "
            "row, the implication is being applied unconditionally, which silently makes every run "
            "unattended and disables every interactive gate. FIX: the decision lives in "
            f"`initialize_run`; the implication lives once, in `freeze_run_policy_flags`.\n"
            + "\n".join(wrong),
        )

    def test_the_frozen_options_match_across_hosts(self):
        """The `rununify` property at the STATE level, not just the parser level."""
        frozen = {}
        for runner in BOTH:
            _text, _status, state = self.run_and_read_status(runner, [])
            frozen[runner] = {
                row.dest: state["options"][row.dest]
                for row in runner_shared.RUN_POLICY_FLAGS
            }
        self.assertEqual(frozen["oc_runipd"], frozen["agy_runipd"])

    def test_the_mixed_type_gate_ledger_record_is_written(self):
        """Spec 2.5 bullet 4's four facts, durable, on a real run."""
        import json
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            with self.subTest(runner=runner):
                with tempfile.TemporaryDirectory() as td:
                    repo, _plan = self.make_repo(_P(td))
                    args = _parse(runner, ["start", "prb001", "--repo", str(repo)])
                    args.prepare_only = True
                    run_dir = _MODULES[runner].initialize_run(args)
                    events = [
                        json.loads(line)
                        for line in (run_dir / "events.jsonl").read_text().splitlines()
                        if line.strip()
                    ]
                    record = next(e for e in events if e["event"] == "mixed-type-gate")
                    for key in (
                        "type_counts",
                        "action_preview",
                        "response_or_flag",
                        "queue_digest",
                    ):
                        self.assertIn(key, record)
                    # Single-type selection: the gate is REACHED and correctly does not APPLY.
                    self.assertFalse(record["gate_applied"])
                    self.assertTrue(record["proceed"])
                    self.assertEqual(record["type_counts"], {"ipd": 1})

    #: (case, argv tail, needle the refusal must contain, why this refusal must reach the operator)
    #:
    #: `--with-dependencies` HAD A ROW HERE AND NO LONGER DOES, because depclosure 01 (`dhycim`) built
    #: its behavior: it now EXPANDS rather than refusing, so a row demanding "not yet implemented" out
    #: of it would demand the defect back. Its replacement coverage is
    #: `DependencyClosureTests.test_a_closure_refusal_leaves_no_durable_run_state`, which asserts the
    #: SAME no-durable-state property on this flag's remaining refusals (an unresolvable target and a
    #: non-plan target), so the guarantee moved with the behavior instead of being dropped.
    REFUSALS = (
        (
            "--follow-generated (unimplemented)",
            ["--follow-generated"],
            "not yet implemented",
            "the LAST unimplemented flag, and the reason this row must keep passing after "
            "`--with-dependencies` left this table: no mechanism in this package detects that an agent "
            "turn generated a new IPD, so there is nothing to flip `implemented` to. A refusal that "
            "stopped firing here would mean both halves of backlog x8diyb were reported as shipped "
            "when only one was",
        ),
        (
            "--retry-budget 11 (out of range)",
            ["--retry-budget", "11"],
            "0..10",
            "E-04 end to end: the range bound must be reached at PARSE time, before a `RunEngine` or "
            "any step exists, and the refusal must state the range rather than merely rejecting",
        ),
        (
            "--unverifiable-ok without its admission",
            ["--unverifiable-ok"],
            "--allow-unverifiable",
            "E-03 end to end: this flag neutralizes contractless prompts for the aggregate exit code, "
            "so it is legal only alongside the admission. The refusal must NAME the companion flag, "
            "or the operator is left guessing",
        ),
    )

    def test_every_refused_invocation_leaves_no_durable_run_state(self):
        """Every refusing flag, on both hosts, with the no-durable-state check on EVERY row.

        Three tests became one. Each built the probe repo, parsed one argv, required a
        `RunFlagRefusal` out of `initialize_run`, and checked one needle in the message. They differ
        only in the argv and the needle, which is a data row, and they fail together whenever the
        preflight seam moves.

        THE MERGE IS STRICTLY STRONGER, which is why it is worth doing. Only two of the three old tests
        asserted that no `run-*` directory survived; `test_unverifiable_ok_alone_refuses_the_whole_run`
        checked the message and nothing else, so a refusal that fired AFTER allocating a run directory
        would have passed. Every row now asserts both, because 'refuses' and 'refuses before anything
        durable exists' are different guarantees and the second is the one an operator's tree depends
        on: a run directory left behind by a refused command is state they must reconcile by hand.
        """
        import tempfile
        from pathlib import Path as _P

        wrong = []
        for case, tail, needle, why in self.REFUSALS:
            for runner in BOTH:
                with tempfile.TemporaryDirectory() as td:
                    repo, _plan = self.make_repo(_P(td))
                    args = _parse(
                        runner, ["start", "prb001", "--repo", str(repo), *tail]
                    )
                    problems = []
                    try:
                        _MODULES[runner].initialize_run(args)
                    except runner_shared.RunFlagRefusal as exc:
                        if needle not in str(exc):
                            problems.append(
                                f"the refusal omits {needle!r}: {str(exc)!r}"
                            )
                    else:
                        problems.append(
                            "the run was ACCEPTED; `initialize_run` returned without refusing"
                        )
                    runs = repo / ".aw" / "records" / "runs"
                    leftover = sorted(
                        p.name for p in (runs.glob("run-*") if runs.exists() else [])
                    )
                    if leftover:
                        problems.append(
                            f"durable run state survived a refused invocation: {leftover}. An "
                            "operator now has a run directory, and possibly a report and a ledger, "
                            "for work that never started"
                        )
                    if problems:
                        wrong.append(
                            f"  {case} on {runner}:\n"
                            + "".join(f"    - {p}\n" for p in problems)
                            + f"    this row exists because: {why}"
                        )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.REFUSALS) * len(BOTH)} (flag, host) cells did not refuse "
            "cleanly. READ THEM TOGETHER: if EVERY row on one host stopped refusing, that host's "
            "preflight seam was moved or deleted wholesale rather than one flag regressing. If a row "
            "refuses but leaves a `run-*` directory behind, the refusal moved to AFTER run-directory "
            "allocation, which is a different defect from not refusing and needs the check re-ordered "
            "rather than re-added. FIX: all four refusals fire from the shared preflight helpers "
            f"(`refuse_unimplemented_run_flags`, `resolve_retry_budget`, "
            f"`evaluate_unverifiable_admission`) at the top of `initialize_run`, before the run "
            f"directory is created.\n" + "\n".join(wrong),
        )

    def test_the_effective_retry_budget_is_frozen(self):
        """Kept separate: a PAIR of runs whose point is that two different values both land frozen.

        Not a row in `AUTO_APPROVE` because it asserts the same field over two argvs where the
        interesting value is `0` - the value an `if value:` test silently replaces with the default -
        and not a row in `REFUSALS` because both invocations SUCCEED.
        """
        for runner in BOTH:
            with self.subTest(runner=runner):
                _t, _s, state = self.run_and_read_status(runner, [])
                self.assertEqual(state["options"]["retry_budget"], 2)
                _t, _s, state = self.run_and_read_status(
                    runner, ["--retry-budget", "0"]
                )
                self.assertEqual(
                    state["options"]["retry_budget"],
                    0,
                    "`--retry-budget 0` must freeze as 0. A 2 here means the zero was read as unset "
                    "somewhere between the parser and the ledger, and the run will retry twice",
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


class DraftAdmissionGateWiringTests(unittest.TestCase):
    """revsweep-02 (`6ypimw`) E-04: spec 25kzda 2.5a's gate is CALLED on BOTH hosts, at the right seam.

    WHY THIS CLASS EXISTS RATHER THAN TRUSTING THE POLICY TESTS. `tests/test_run_selection_policy.py`
    proves the gate DECIDES correctly; it cannot prove anything CALLS it. That distinction is not
    hypothetical here: the mixed-type gate of spec 2.5 shipped fully built and fully tested with ZERO
    callers, so a green policy suite coexisted with a gate that never ran. The assertions below drive
    `initialize_run` on a real repository holding a complete draft.

    THE SAFETY-CRITICAL ASSERTION IS
    :meth:`test_no_bare_input_was_added_and_the_prompt_cannot_block`. These runs are unattended by
    design and a wedge is silent and open-ended: both runners hand children `stdin=DEVNULL` precisely
    because a nested prompt "blocks on input() forever", with a measured 1h49m wedge recorded inline.
    """

    COMPLETE_DRAFT = """# IPD: complete draft probe

- Date: 2026-09-05
- Kind: child
- Concern: a real concern sentence, so no anchored placeholder remains.
- Scope: a real scope sentence.
- Scope-Paths: src/
- Item-Dependencies: none
- Status: draft
- Set: probe
- Order: {order}
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history
- 2026-09-05 draft (test): created.

## Goal

A real goal sentence.

## Detailed Implementation Checklist (TODO)

### Task group 1: probe

- [ ] E-01 Do one observable thing.
  - Depends on: none
  - Expected outcome: the observable thing happened.
  - Execution state: pending

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: the observable thing, pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: small
- Cohesion rationale: one concern.

Real gate prose.
"""

    def make_repo(
        self,
        root,
        *,
        with_to_review: bool = True,
        stub_deps: bool = False,
        with_stub: bool = True,
    ):
        """A repo with ONE complete draft, ONE incomplete (real scaffold) draft, and by default one
        ordinary `to-review` plan.

        The `to-review` plan is what makes "the rest of the queue PROCEEDS" observable at all: with
        only drafts in the tree an exclusion empties the selection, which is a different (and also
        tested) outcome. `with_to_review=False` produces that drafts-only tree deliberately.
        """
        import subprocess

        from agent_workflows import ipd_authoring

        repo = root / "repo"
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True)
        for cmd in (
            ["git", "init", "-q"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, cwd=repo, check=True)
        (repo / ".gitignore").write_text(".aw/records/runs/\n", encoding="utf-8")
        (pending / "20260905-probe-01-drf001-complete.ipd.md").write_text(
            self.COMPLETE_DRAFT.format(id6="drf001", order=1), encoding="utf-8"
        )
        stub = (
            ipd_authoring.build_skeleton(
                kind="child",
                title="stub",
                author="test",
                when="2026-09-05",
                set_name="probe",
                order=2,
                plan_id="drf002",
            )
            if with_stub
            else None
        )
        if stub is not None and stub_deps:
            # `all` (unlike `reviews`) selects an INCOMPLETE draft into the queue, where the shipped
            # dependency preflight then refuses the whole run over the scaffold's `unresolved`
            # sentinel. That refusal is PRE-EXISTING behavior at HEAD and not this gate's business, so
            # a test about the gate resolves the sentinel to keep the two failures from being
            # conflated. The draft stays INCOMPLETE by every other placeholder.
            stub = stub.replace(
                "- Item-Dependencies: unresolved", "- Item-Dependencies: none"
            )
        if stub is not None:
            (pending / "20260905-probe-02-drf002-stub.ipd.md").write_text(
                stub, encoding="utf-8"
            )
        if with_to_review:
            (pending / "20260905-probe-03-rev003-ordinary.ipd.md").write_text(
                self.COMPLETE_DRAFT.format(id6="rev003", order=3).replace(
                    "- Status: draft", "- Status: to-review"
                ),
                encoding="utf-8",
            )
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
        return repo

    def initialize(self, runner: str, argv: list, **repo_kw):
        """`initialize_run` on that repo; returns (state, ledger events, stderr text)."""
        import contextlib
        import io
        import json
        import tempfile
        from pathlib import Path as _P

        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(_P(td), **repo_kw)
            args = _parse(runner, ["start", *argv, "--repo", str(repo)])
            args.prepare_only = True
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                run_dir = _MODULES[runner].initialize_run(args)
            state = runner_shared.load_state(run_dir)
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            return state, events, err.getvalue()

    def gate_event(self, events: list):
        found = [e for e in events if e.get("event") == "draft-admission-gate"]
        self.assertEqual(len(found), 1, f"expected exactly one gate event, got {found}")
        return found[0]

    def queue_ids(self, state: dict) -> list:
        return [item["id6"] for item in state["queue"]]

    def test_the_gate_is_called_from_initialize_run_on_both_hosts(self):
        """The call site EXISTS, as an AST claim, and the shared seam DELEGATES, as a behavioral one.

        THE AST HALF IS KEPT. `ast.walk` matching a real `ast.Call` node cannot be satisfied by a
        comment, which matters specifically here: this module's prose names the gate repeatedly (it
        explains the dead-gate defect), so a substring search would pass on that prose alone. The
        invariant is also structural rather than observable - the gate must have a call site in EACH
        host's `initialize_run` rather than merely being reachable somehow - so no single behavioral
        run states it.

        THE DELEGATION HALF WAS A SOURCE-TEXT PIN and is now behavioral. It read
        `inspect.getsource(runner_shared.enforce_draft_admission_gate)` and asserted the substring
        `"decide_draft_admission"` appeared - satisfiable by the docstring that explains the gate calls
        it. Now the policy function is replaced by a spy and the seam must actually call it on a real
        run, which no comment can do.
        """
        import ast

        from agent_workflows import run_selection_policy

        for runner in BOTH:
            with self.subTest(runner=runner):
                source = _effective_init_source(runner)
                called = {
                    ast.unparse(node.func)
                    for node in ast.walk(ast.parse(source.strip()))
                    if isinstance(node, ast.Call)
                }
                self.assertTrue(
                    {
                        "enforce_draft_admission_gate",
                        "runner_shared.enforce_draft_admission_gate",
                    }
                    & called,
                    "the draft gate has no call site on this host",
                )

        real = run_selection_policy.decide_draft_admission

        def make_spy(sink):
            # The sink is bound as a DEFAULT-free closure over a parameter, not over the loop
            # variable, so each host counts into its own list rather than sharing the last one.
            def spy(*args, **kwargs):
                sink.append(kwargs)
                return real(*args, **kwargs)

            return spy

        for runner in BOTH:
            calls: list = []
            with self.subTest(runner=runner):
                with mock.patch.object(
                    run_selection_policy, "decide_draft_admission", make_spy(calls)
                ):
                    self.initialize(runner, ["reviews"])
                self.assertEqual(
                    len(calls),
                    1,
                    "a real run must reach `run_selection_policy.decide_draft_admission` exactly "
                    "once. Zero calls mean the shared seam decides admission ITSELF, which is the "
                    "second copy of a gate this file exists to prevent; more than one means the "
                    "operator could be asked twice about one selection",
                )

    def test_the_gate_runs_after_resolution_but_before_any_durable_run_state(self):
        """Spec 2.5a's seam, OBSERVED at the moment the gate runs rather than inferred from text.

        REPLACES A BYTE-OFFSET SOURCE PIN, which is the single most fragile shape in this file. The old
        test read `inspect.getsource(initialize_run)`, split the text on the literal
        `"run_dir = state_root"`, asserted `"enforce_draft_admission_gate"` appeared in the PREFIX, and
        then compared `.index("expand_selectors")` against `.index("enforce_draft_admission_gate")` -
        a claim about which substring appears EARLIER IN THE FILE. That breaks when unrelated lines move
        or when `ruff format` rewraps a call, it is satisfied by a comment mentioning either name in
        the right order, and it says nothing about what the gate actually SEES.

        Now both halves are observed by intercepting the gate mid-run:

        * AFTER RESOLUTION: the ids handed to the gate are the RESOLVED selection (`drf001` and
          `rev003` from the `reviews` selector), not the raw selector string. A gate running before
          resolution could not name them.
        * BEFORE DURABLE STATE: no `run-*` directory exists AT THE MOMENT the gate is called, so an
          exclusion leaves nothing for an operator to reconcile - the same guarantee the dependency
          preflight beside it provides.
        """
        import contextlib
        import io
        import tempfile
        from pathlib import Path as _P

        wrong = []
        real = runner_shared.enforce_draft_admission_gate

        def make_spy(repo, observed):
            # Both captured values are PARAMETERS, not loop variables, so each host observes its own
            # repository; a closure over the loop would have every host read the last one's tree.
            def spy(manifest, ids, **kwargs):
                runs = repo / ".aw" / "records" / "runs"
                observed["ids"] = sorted(ids)
                observed["runs"] = (
                    sorted(p.name for p in runs.glob("run-*")) if runs.exists() else []
                )
                return real(manifest, ids, **kwargs)

            return spy

        for runner in BOTH:
            observed: dict = {}

            with tempfile.TemporaryDirectory() as td:
                repo = self.make_repo(_P(td))
                args = _parse(runner, ["start", "reviews", "--repo", str(repo)])
                args.prepare_only = True
                with mock.patch.object(
                    runner_shared,
                    "enforce_draft_admission_gate",
                    make_spy(repo, observed),
                ):
                    with contextlib.redirect_stderr(io.StringIO()):
                        _MODULES[runner].initialize_run(args)

            if "ids" not in observed:
                wrong.append(
                    f"  {runner}: the gate was never called on a real `reviews` run, so neither half "
                    "of the seam can be observed"
                )
                continue
            if observed["ids"] != ["drf001", "rev003"]:
                wrong.append(
                    f"  {runner}: the gate received {observed['ids']} but the RESOLVED `reviews` "
                    "selection is ['drf001', 'rev003']. It must run AFTER resolution, because its "
                    "whole job is to decide about the concrete items the selector produced"
                )
            if observed["runs"]:
                wrong.append(
                    f"  {runner}: run director(ies) {observed['runs']} already existed when the gate "
                    "ran. Spec 2.5a puts the gate BEFORE any lease or session precisely so an "
                    "exclusion leaves no durable state to reconcile"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(BOTH)} host(s) place the draft gate at the wrong seam. The two "
            "halves fail for opposite reasons and need opposite fixes: receiving a raw selector "
            "instead of resolved ids means the gate moved too EARLY and cannot decide about real "
            "items, while an existing run directory means it moved too LATE and an exclusion now "
            "leaves a run directory, a report, and a ledger behind for work that never started. FIX: "
            f"the call belongs between `expand_selectors` and the run-directory allocation.\n"
            + "\n".join(wrong),
        )

    def test_an_ungated_complete_draft_is_excluded_and_the_rest_proceeds(self):
        """Spec 2.5a bullet 4, END TO END, and the asymmetry with the mixed-type refusal: the run is
        NOT refused. `initialize_run` returns normally and the queue keeps its other items."""
        from agent_workflows import run_selection_policy

        for runner in BOTH:
            with self.subTest(runner=runner):
                state, events, err = self.initialize(runner, ["reviews"])
                self.assertNotIn("drf001", self.queue_ids(state))
                # THE ASYMMETRY, OBSERVED: the ordinary `to-review` plan still runs. A mixed-type
                # refusal would have started nothing at all.
                self.assertEqual(self.queue_ids(state), ["rev003"])
                event = self.gate_event(events)
                self.assertEqual(event["excluded_complete"], ["drf001"])
                self.assertEqual(event["admitted"], [])
                self.assertIn(run_selection_policy.RUN_DRAFTS_EXCLUDED, err)
                self.assertIn("1 item(s) proceeded", err)
                # The incomplete draft is skipped with findings, not admitted, not an abort.
                self.assertEqual(event["skipped_incomplete"], ["drf002"])
                self.assertNotIn("drf002", self.queue_ids(state))

    def test_allow_drafts_admits_the_complete_draft_on_both_hosts(self):
        """Left separate: it asserts five ledger-event fields plus two queue-membership facts about one
        run, which is a different shape from a one-outcome-per-row table."""
        for runner in BOTH:
            with self.subTest(runner=runner):
                state, events, _err = self.initialize(
                    runner, ["reviews", "--allow-drafts"]
                )
                self.assertIn("drf001", self.queue_ids(state))
                event = self.gate_event(events)
                self.assertEqual(event["admitted"], ["drf001"])
                self.assertEqual(event["response_or_flag"], "--allow-drafts")
                self.assertEqual(event["draft_counts"], {"ipd": 1})
                self.assertTrue(event["preview"])
                # NEVER the incomplete one, at any flag setting (spec 2.5a bullet 1).
                self.assertEqual(event["skipped_incomplete"], ["drf002"])
                self.assertNotIn("drf002", self.queue_ids(state))

    def test_the_ledger_record_is_the_pure_modules_own(self):
        """Spec 2.5a's last bullet: the RUNNER persists what the policy module RETURNED, and the
        policy module writes nothing itself.

        REPLACES TWO SOURCE-TEXT PINS. It read `inspect.getsource(run_selection_policy)` and asserted
        the substrings `"append_jsonl"` and `"events.jsonl"` were absent. Both are change-detectors on
        NAMES rather than on behavior: a module that wrote the ledger through `open(...).write(...)`,
        or through a helper named anything else, passed them, while a comment explaining WHY it must
        not write the ledger (the return-not-write convention `MixedTypeRecord` set) failed them.

        Now asserted by OBSERVATION: the policy function is called with the process CWD set to an empty
        temporary directory, and that directory must be byte-for-byte empty afterwards. A module that
        writes anything, by any spelling, fails; a comment cannot create a file.
        """
        import os
        import tempfile
        from pathlib import Path as _P

        from agent_workflows import run_selection_policy

        for runner in BOTH:
            with self.subTest(runner=runner):
                _state, events, _err = self.initialize(
                    runner, ["reviews", "--allow-drafts"]
                )
                event = self.gate_event(events)
                for key in ("draft_counts", "preview", "response_or_flag", "admitted"):
                    self.assertIn(key, event)

        with tempfile.TemporaryDirectory() as td:
            cwd = os.getcwd()
            os.chdir(td)
            try:
                verdict = run_selection_policy.decide_draft_admission(
                    [run_selection_policy.DraftCandidate("drf001", "ipd", True)],
                    interactive=False,
                    response=None,
                )
            finally:
                os.chdir(cwd)
            self.assertEqual(
                sorted(p.name for p in _P(td).iterdir()),
                [],
                "`decide_draft_admission` created files while deciding. The policy module must "
                "RETURN a record and write nothing: it has no run directory, no lease, and no way to "
                "know whether the caller will even proceed, so anything it writes is state the "
                "runner did not authorize and cannot reconcile",
            )
            self.assertEqual(
                verdict.excluded_complete,
                ("drf001",),
                "and the decision itself is still returned, so the no-write assertion above is not "
                "satisfied by a function that does nothing at all",
            )

    def test_a_draft_named_explicitly_is_admitted_without_gating(self):
        """Spec 2.5a bullet 2: "the operator named it; asking is noise." So no gate event at all."""
        for runner in BOTH:
            with self.subTest(runner=runner):
                state, events, _err = self.initialize(runner, ["drf001"])
                self.assertIn("drf001", self.queue_ids(state))
                self.assertEqual(
                    [e for e in events if e.get("event") == "draft-admission-gate"], []
                )

    def test_no_bare_input_was_added_and_the_prompt_cannot_block(self):
        """THE SAFETY ASSERTION. A prompt that can block an unattended run fails this outright.

        Four properties, each one of `_lane_reclaim_prompt`'s HARD CONSTRAINTS:
        no bare `input()`; no TTY means NO prompt; an unanswered prompt falls through rather than
        blocking; and the fall-through decision is EXCLUDE, identical to the unattended no-flag path,
        so a timeout can never silently admit a draft.
        """
        import inspect

        for module in (runner_shared, oc_runipd, agy_runipd):
            with self.subTest(module=module.__name__):
                tree = ast.parse(inspect.getsource(module))
                bare_input = [
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "input"
                ]
                self.assertEqual(
                    bare_input,
                    [],
                    f"{module.__name__} calls input(); a nested prompt wedges an unattended run",
                )

        class _NotTTY:
            def isatty(self):
                return False

            def readline(self):  # pragma: no cover - must never be reached
                raise AssertionError("read attempted without a TTY")

        # NO TTY -> NO PROMPT, and nothing is read.
        self.assertIsNone(
            runner_shared.prompt_for_gate_phrase("q", stdin=_NotTTY(), stderr=_NotTTY())
        )

        class _TTYNoData:
            def isatty(self):
                return True

            def fileno(self):
                return 0

            def readline(self):  # pragma: no cover - must never be reached
                raise AssertionError("blocked on a read after a timeout")

            def write(self, _text):
                return 0

            def flush(self):
                return None

        # An unanswered prompt FALLS THROUGH (bounded by `select`), returning None rather than
        # blocking. Timeout 0 makes the bound observable without waiting.
        self.assertIsNone(
            runner_shared.prompt_for_gate_phrase(
                "q", timeout=0, stdin=_TTYNoData(), stderr=_TTYNoData()
            )
        )
        # ... and None is REFUSED by the exact-phrase matcher, so the fall-through outcome is EXCLUDE,
        # bit-for-bit the unattended no-flag outcome.
        from agent_workflows import run_selection_policy

        self.assertFalse(
            run_selection_policy.is_confirmation_accepted(
                None, phrase=run_selection_policy.DRAFTS_CONFIRM_PHRASE
            )
        )
        verdict = run_selection_policy.decide_draft_admission(
            [run_selection_policy.DraftCandidate("c0", "ipd", True)],
            interactive=True,
            response=None,
        )
        self.assertEqual(verdict.admitted, ())
        self.assertEqual(verdict.excluded_complete, ("c0",))

    def test_the_interactive_phrase_admits_drafts_through_the_wired_seam(self):
        """The interactive half is IMPLEMENTED (fenced), not declared unreachable: the exact phrase
        reaches the shared call site and admits, while a reflex answer does not."""
        manifest = {
            "schema_version": 1,
            "plans": {
                "drf001": {
                    "set": "probe",
                    "file": "x.ipd.md",
                    "status": "draft",
                    "order": 1,
                    "dependencies": [],
                },
            },
            "sets": {"probe": {"order": ["drf001"]}},
        }
        asked: list = []

        def fake_prompt(question, **_kw):
            asked.append(question)
            return "run drafts\n"

        with mock.patch.object(
            runner_shared, "plan_authoring_complete", return_value=True
        ):
            kept, verdict = runner_shared.enforce_draft_admission_gate(
                manifest,
                ["drf001"],
                repo=None,
                allow_drafts=False,
                interactive=True,
                host="oc",
                selector="reviews",
                prompt=fake_prompt,
            )
        self.assertEqual(kept, ["drf001"])
        self.assertEqual(verdict.admitted, ("drf001",))
        self.assertEqual(len(asked), 1, "spec 2.5a: asked ONCE, before any work")
        self.assertIn("run drafts", asked[0])

        with mock.patch.object(
            runner_shared, "plan_authoring_complete", return_value=True
        ):
            kept_bad, verdict_bad = runner_shared.enforce_draft_admission_gate(
                manifest,
                ["drf001"],
                repo=None,
                allow_drafts=False,
                interactive=True,
                host="oc",
                selector="reviews",
                prompt=lambda _q, **_kw: "y\n",
            )
        self.assertEqual(kept_bad, [])
        self.assertEqual(verdict_bad.excluded_complete, ("drf001",))

    def test_the_gate_call_sites_were_not_duplicated(self):
        """EXACTLY ONE call site per gate, per place it belongs, counted as AST CALLS.

        KEPT AS A STRUCTURAL GUARD (`94b00d37` keeps the AST single-source guards for the same
        reason), but UPGRADED from `source.count("...")` to counting real `ast.Call` nodes. The old
        form counted SUBSTRINGS, so it was wrong in both directions: every comment or docstring
        naming a gate inflated the count (this class's own prose names both gates repeatedly, so the
        oc expectation of `1` was one comment away from failing for no behavioral reason), and a
        second call spelled through an alias was invisible.

        WHY A COUNT AND NOT A BEHAVIORAL TEST: the hazard is a SECOND call site, and a second call
        site is usually silent - the gate simply runs twice, which for the mixed-type gate means the
        operator can be asked to confirm one selection twice, and for the draft gate means two ledger
        records for one decision. Neither shows up as a wrong answer on the happy path, so only a
        structural count catches it before an operator does.

        The two rows differ in WHERE ONE is allowed: `decide` may be called once and only from SHARED
        code (so the two hosts cannot drift), while each host's `initialize_run` must call each
        `enforce_*` wrapper exactly once (so the gate runs on both hosts, once per run).
        """
        import ast
        import inspect

        def call_count(source: str, dotted: str) -> int:
            return sum(
                1
                for node in ast.walk(ast.parse(source.strip()))
                if isinstance(node, ast.Call)
                and ast.unparse(node.func).split(".")[-1] == dotted.split(".")[-1]
                and ast.unparse(node.func).endswith(dotted)
            )

        wrong = []
        for module in (runner_shared, oc_runipd, agy_runipd):
            expected = 1 if module is runner_shared else 0
            got = call_count(inspect.getsource(module), "run_selection_policy.decide")
            if got != expected:
                wrong.append(
                    f"  {module.__name__} calls `run_selection_policy.decide` {got} time(s), "
                    f"expected {expected}\n"
                    "    this row exists because: the mixed-type gate must have exactly ONE call "
                    "site and it must be in SHARED code. A host-local call site is how the two "
                    "runners come to gate differently; two call sites in shared code is how one "
                    "selection gets confirmed twice"
                )
        for runner in BOTH:
            # AST CALL counts (ours), over the EFFECTIVE body (main's `_effective_init_source`).
            # Both halves matter and neither side had both. AST counting means a comment or a
            # docstring naming a gate cannot change the number, so a moved count means real code
            # moved. Reading the effective body means that after `7a28ed11` unified `initialize_run`
            # into `runner_shared.initialize_run_core`, the scan follows the code instead of counting
            # zero calls in a now-thin host wrapper and reporting a DEAD GATE that is in fact live.
            body = _effective_init_source(runner)
            for gate in ("enforce_mixed_type_gate", "enforce_draft_admission_gate"):
                got = call_count(body, gate)
                if got != 1:
                    wrong.append(
                        f"  {runner}'s `initialize_run` calls `{gate}` {got} time(s), expected 1\n"
                        "    this row exists because: ZERO means the gate is DEAD on this host, "
                        "which is the exact defect this file was written for (spec 2.5's gate "
                        "shipped fully built and fully tested with no callers at all). TWO means one "
                        "decision produces two ledger records and, interactively, two prompts"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} gate call-site count(s) are wrong. A ZERO count is a dead gate and is the "
            "severe direction: the policy suite stays green while nothing enforces it. A count above "
            "one is a duplicated gate, which double-records and double-prompts. Note these are AST "
            "CALL counts, so a comment naming a gate cannot change them - if a count moved, real code "
            f"moved.\n" + "\n".join(wrong),
        )

    def test_completeness_fails_safe_when_it_cannot_be_determined(self):
        """F-11's hazard: the manifest carries no plan TEXT, so the caller must read it - and an
        absent repo or an unreadable file must yield NOT-swept, never a crash and never an optimistic
        include (which would sweep an incomplete stub into a review turn)."""
        import tempfile
        from pathlib import Path as _P

        self.assertIsNone(runner_shared.plan_authoring_complete(None, "any.ipd.md"))
        with tempfile.TemporaryDirectory() as td:
            root = _P(td)
            self.assertIsNone(
                runner_shared.plan_authoring_complete(root, "missing.ipd.md")
            )
            self.assertIsNone(runner_shared.plan_authoring_complete(root, ""))
            (root / "adir.ipd.md").mkdir()
            self.assertIsNone(
                runner_shared.plan_authoring_complete(root, "adir.ipd.md")
            )
        entry = {
            "set": "s",
            "file": ".aw/records/plans/pending/x-drf001-x.ipd.md",
            "status": "draft",
        }
        # repo=None: not determined -> NOT swept.
        self.assertFalse(runner_shared.manifest_entry_needs_review(entry, repo=None))

    def test_only_draft_candidates_are_read_from_disk(self):
        """The read is BOUNDED: every other status is answered by the action table alone."""
        reads: list = []
        real = runner_shared.plan_authoring_complete

        def spy(repo, rel):
            reads.append(rel)
            return real(repo, rel)

        manifest = {
            "schema_version": 1,
            "plans": {
                "aaa001": {
                    "set": "s",
                    "file": "a-to-review.ipd.md",
                    "status": "to-review",
                    "order": 1,
                    "dependencies": [],
                },
                "bbb002": {
                    "set": "s",
                    "file": "b-draft.ipd.md",
                    "status": "draft",
                    "order": 2,
                    "dependencies": [],
                },
                "ccc003": {
                    "set": "s",
                    "file": "c-approved.ipd.md",
                    "status": "approved",
                    "order": 3,
                    "dependencies": [],
                },
                "ddd004": {
                    "set": "s",
                    "file": "d-reviewed.ipd.md",
                    "status": "reviewed",
                    "order": 4,
                    "dependencies": [],
                },
            },
            "sets": {"s": {"order": ["aaa001", "bbb002", "ccc003", "ddd004"]}},
        }
        with mock.patch.object(runner_shared, "plan_authoring_complete", spy):
            swept = runner_shared.sweep_review_candidates(manifest, repo=None)
        self.assertEqual(swept, ["aaa001"])  # the draft is not determined -> excluded
        self.assertEqual(reads, ["b-draft.ipd.md"], "only the draft candidate was read")

    def test_the_allow_drafts_help_states_that_it_cannot_admit_an_incomplete_draft(
        self,
    ):
        """An operator reads `--help` and never reads an IPD, so the limit must be there."""
        row = runner_shared.RUN_POLICY_FLAGS_BY_FLAG["--allow-drafts"]
        self.assertIn("COMPLETE", row.help)
        self.assertIn("INCOMPLETE", row.help)
        self.assertIn("waives no other gate", row.help)
        for runner in BOTH:
            with self.subTest(runner=runner):
                self.assertIn(
                    "--allow-drafts", _subparser(runner, "start").format_help()
                )

    def test_an_omitted_allow_drafts_on_resume_does_not_clobber_the_frozen_value(self):
        """F-12's actual property: an OMITTED flag preserves frozen state (that is what
        `default=None` buys). A PASSED flag legitimately overwrites, as shipped `--full-auto` does."""
        state = {"options": {"allow_drafts": True}}
        resume_args = argparse.Namespace(
            **{row.dest: None for row in runner_shared.RUN_POLICY_FLAGS}
        )
        self.assertFalse(
            runner_shared.apply_run_policy_flags_on_resume(state, resume_args)
        )
        self.assertIs(state["options"]["allow_drafts"], True)

    def test_allow_drafts_is_frozen_at_queue_build_on_both_hosts(self):
        """Left separate: a flag-ON/flag-OFF PAIR over two real runs, which asserts that the frozen
        value tracks the flag rather than any single value."""
        for runner in BOTH:
            with self.subTest(runner=runner):
                state, _events, _err = self.initialize(
                    runner, ["reviews", "--allow-drafts"]
                )
                self.assertIs(state["options"]["allow_drafts"], True)
                state, _events, _err = self.initialize(runner, ["reviews"])
                self.assertIs(state["options"]["allow_drafts"], False)

    def test_the_combined_path_is_proven_correct_and_NOT_proven_fired(self):
        """THE HONEST LIMIT, as an assertion rather than a comment (F-8).

        Spec 2.5a bullet 5's combined mixed-plus-draft interaction is implemented and tested at the
        seam, but NO real invocation can trigger it: discovery is IPD-only and neither host registers
        `--type`, so no selection can contain two types. A later plan that adds `--type` will have to
        update this test, which is the point - the limit becomes visible rather than silently outgrown.
        """
        from agent_workflows import run_selection_policy

        self.assertTrue(hasattr(run_selection_policy, "decide_selection_gates"))
        for runner in BOTH:
            for sub in ("start", "resume"):
                with self.subTest(runner=runner, subcommand=sub):
                    self.assertNotIn("--type", _option_strings(runner, sub))

        # And nothing in either runner REACHES the combined entry point, precisely BECAUSE it cannot
        # fire; asserting that keeps the claim honest instead of implying a live combined gate.
        #
        # OBSERVED, NOT GREPPED. This replaced an `assertNotIn("decide_selection_gates",
        # inspect.getsource(module))` pin, which is a change-detector twice over: THIS comment
        # mentioning the symbol would fail it, while a call reached through an alias would pass it. The
        # combined entry point is now replaced with a function that RAISES, and a real run on each host
        # must complete regardless - an unreachable path cannot be reached.
        def _must_not_fire(
            *_args, **_kwargs
        ):  # pragma: no cover - the point is it never runs
            raise AssertionError(
                "the combined mixed-plus-draft gate FIRED on a real run. That is not a bug in this "
                "test: it means a live selection can now be multi-type (someone registered `--type` "
                "or widened discovery), so spec 2.5a bullet 5 is reachable and this honest-limit test "
                "must be rewritten to assert the combined behavior instead of its unreachability"
            )

        for runner in BOTH:
            with self.subTest(runner=runner, check="combined gate never reached"):
                with mock.patch.object(
                    run_selection_policy, "decide_selection_gates", _must_not_fire
                ):
                    self.initialize(runner, ["reviews", "--allow-drafts"])

    def test_excluding_every_item_starts_no_run_and_exits_zero(self):
        """FOUND BY PROBING THE WIRED COMMAND, not by reading it, and it would have shipped as a
        durable-state bug: when the ONLY selected item is an ungated draft, the queue is empty.

        The right answer composes two spec rules instead of inventing a third: 2.5a excludes the draft
        WITHOUT failing the run, and 2.4a property 3 makes an empty status selection a SUCCESS that
        starts no run and exits 0. Freezing an empty queue would have created a run directory, a
        report, and a ledger for zero work - state an operator then has to reconcile - while raising a
        plain error would have contradicted 2.5a's "it does not fail the run".
        """
        import contextlib
        import io
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            with self.subTest(runner=runner):
                with tempfile.TemporaryDirectory() as td:
                    repo = self.make_repo(_P(td), with_to_review=False)
                    args = _parse(runner, ["start", "reviews", "--repo", str(repo)])
                    args.prepare_only = True
                    err = io.StringIO()
                    with contextlib.redirect_stderr(err):
                        with self.assertRaises(_MODULES[runner].EmptyStatusSelection):
                            _MODULES[runner].initialize_run(args)
                    # The operator is told WHY it was empty, not left guessing.
                    self.assertIn("[RUN-DRAFTS-EXCLUDED]", err.getvalue())
                    # And nothing durable was created.
                    self.assertFalse((repo / ".aw" / "records" / "runs").exists())

    def test_the_all_selector_keeps_its_own_exit_2_when_the_gate_empties_it(self):
        """Each status selector keeps ITS OWN empty semantics; the gate must not homogenize them.

        `reviews` empty is a SUCCESS (spec 2.4a property 3: "a repository with nothing awaiting review
        is the healthy state"), while `all` empty has always been the exit-2 error. Collapsing the two
        would silently change `all`'s established exit code, which no spec amendment authorizes.
        """
        import contextlib
        import io
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            with self.subTest(runner=runner):
                with tempfile.TemporaryDirectory() as td:
                    # ONLY the complete draft: `all` keeps an INCOMPLETE draft in its queue
                    # (pre-existing behavior, out of this gate's scope), so leaving the stub in place
                    # would make the queue non-empty for a reason unrelated to the gate.
                    repo = self.make_repo(_P(td), with_to_review=False, with_stub=False)
                    out, err = io.StringIO(), io.StringIO()
                    with (
                        contextlib.redirect_stdout(out),
                        contextlib.redirect_stderr(err),
                    ):
                        rc = _MODULES[runner].main(
                            ["start", "all", "--repo", str(repo), "--prepare-only"]
                        )
                    self.assertEqual(rc, 2, "`all` empty must stay exit 2")
                    self.assertIn("No actionable pending IPDs", err.getvalue())
                    # The operator still learns WHY, and no run was created.
                    self.assertIn("[RUN-DRAFTS-EXCLUDED]", err.getvalue())
                    self.assertFalse((repo / ".aw" / "records" / "runs").exists())

    def test_the_all_selector_also_admits_drafts_through_the_gate(self):
        """Spec 2.5a names BOTH status selectors (`reviews` or `all`), so `all` is gated too - and
        `all`'s membership already includes `draft`, so this is where an ungated promotion would have
        slipped through unnoticed."""
        for runner in BOTH:
            with self.subTest(runner=runner):
                state, events, _err = self.initialize(
                    runner, ["all", "--allow-drafts"], stub_deps=True
                )
                ids = self.queue_ids(state)
                self.assertIn("drf001", ids)
                self.assertEqual(
                    len([i for i in ids if i == "drf001"]),
                    1,
                    "an admitted draft must not be enqueued twice",
                )
                self.assertEqual(self.gate_event(events)["admitted"], ["drf001"])
                state, _events, _err = self.initialize(runner, ["all"], stub_deps=True)
                self.assertNotIn("drf001", self.queue_ids(state))

    def test_that_empty_selection_exits_zero_through_main(self):
        """`EmptyStatusSelection` is only correct because `main` maps it to exit 0 (spec 2.4a property
        3). Asserted through `main` so the composition is proven, not assumed."""
        import contextlib
        import io
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            with self.subTest(runner=runner):
                with tempfile.TemporaryDirectory() as td:
                    repo = self.make_repo(_P(td), with_to_review=False)
                    out, err = io.StringIO(), io.StringIO()
                    with (
                        contextlib.redirect_stdout(out),
                        contextlib.redirect_stderr(err),
                    ):
                        rc = _MODULES[runner].main(
                            ["start", "reviews", "--repo", str(repo), "--prepare-only"]
                        )
                    self.assertEqual(rc, 0, err.getvalue())
                    self.assertIn("Nothing awaiting review", out.getvalue())
                    self.assertFalse((repo / ".aw" / "records" / "runs").exists())


class DependencyClosureTests(unittest.TestCase):
    """depclosure 01 (`dhycim`): `--with-dependencies` EXPANDS, and the cases it must NOT expand.

    WHAT CHANGED AND WHY IT IS HERE. This flag used to be a row in
    :class:`FullAutoEndToEndBehaviorTests.REFUSALS` demanding the words "not yet implemented", because
    spec 25kzda declared the behavior and nobody had built it - while THREE error catalogue messages
    (`IPD-DEP-SATISFIED`, `IPD-DEP-CASCADE`, `IPD-EXEC-READY`) each ended "then run: aw <host> run
    <id6> --with-dependencies". So the tool recommended a flag that refused. The behavior now ships in
    `runner_shared.expand_dependency_closure` and that row is gone; this class is what replaces it, and
    it carries the SAME no-durable-state guarantee the row did, for the flag's remaining refusals.

    THE MOST IMPORTANT TEST IN THIS CLASS IS THE NEGATIVE ONE
    (:meth:`test_the_flag_absent_case_changes_nothing`). Spec :166 and :1007 both state the flag's
    contract from the negative side: without it, "dependencies outside the selection are checked
    against current repository state but are not silently enqueued". An implementation that expanded
    unconditionally would silently enqueue prerequisites for EVERY run, which is the exact mirror of
    the falsehood the old refusal prevented and is strictly harder to notice, because the run succeeds.

    THE SECOND MOST IMPORTANT IS THE TERMINAL-TARGET SKIP, and it guards a re-execution bug rather than
    untidiness. `discover_plans` recurses every disposition directory, so the manifest carries FINISHED
    plans (measured in this repository: 694 discoverable, 547 `executed`), and 12 of the 43 `executed:`
    edges declared across the pending plans point at a target that is already terminal.
    `action_for(kind, "executed")` returns `"execute"`. What prevents DISPATCH today is incidental (the
    queue builder defaults an unrecognized status to `reviewed` and the dispatch loop only takes
    `queued`), so the closure must skip for itself - and the test proves the CLOSURE skipped, by
    asserting the id is absent from the QUEUE rather than merely never dispatched.

    ON BOTH HOSTS BY IDENTITY WHERE THE CODE IS SHARED. Both runners' `initialize_run` now delegate to
    `runner_shared.initialize_run_core`, so the closure has ONE call site; the behavioral cases below
    still run through each host's own `initialize_run` because the property under test is what an
    operator gets from `aw oc run` and `aw agy run`, and `tests/test_runner_refork_guard.py` is what
    forbids a host from re-defining a shared symbol rather than a third parity mechanism here.
    """

    #: A plan template whose `- Item-Dependencies:` is a parameter, which is the whole point: every
    #: case below differs only in the edges declared and in where the targets live.
    PLAN = """# IPD: closure probe {id6}

- Date: 2026-09-05
- Kind: child
- Concern: closure probe.
- Scope: closure probe.
- Scope-Paths: src/
- Item-Dependencies: {deps}
- Status: approved
- Set: {setid}
- Order: {order}
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history
- 2026-09-05 approved (test): probe.
"""

    def make_repo(self, root, plans, *, spec_id6: str | None = None):
        """A committed repo holding `plans` as ``{id6: (deps, disposition)}``.

        ``disposition`` is the plans-tree subdirectory, so a case can place a target in `executed/`
        exactly as a finished plan really sits, rather than simulating terminality with a status field.
        """
        import subprocess

        repo = root / "repo"
        repo.mkdir(parents=True)
        for cmd in (
            ["git", "init", "-q"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, cwd=repo, check=True)
        (repo / ".gitignore").write_text(".aw/records/runs/\n", encoding="utf-8")
        order = 0
        for id6, (deps, disposition) in plans.items():
            order += 1
            target_dir = repo / ".aw" / "records" / "plans" / disposition
            target_dir.mkdir(parents=True, exist_ok=True)
            text = self.PLAN.format(id6=id6, deps=deps, setid="probe", order=order)
            if disposition != "pending":
                text = text.replace("- Status: approved", f"- Status: {disposition}")
            (target_dir / f"20260905-probe-{order:02d}-{id6}-probe.ipd.md").write_text(
                text, encoding="utf-8"
            )
        if spec_id6:
            specs = repo / ".aw" / "records" / "specs"
            specs.mkdir(parents=True, exist_ok=True)
            (specs / f"20260905-{spec_id6}-01-{spec_id6}-probe.spec.md").write_text(
                "# Spec: probe\n\n"
                "- Date: 2026-09-05\n"
                f"- Id: {spec_id6}\n"
                "- Status: approved\n\n"
                "## Summary\n\nprobe\n",
                encoding="utf-8",
            )
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
        return repo

    def initialize(self, runner, repo, argv):
        """`initialize_run`; returns (queue ids, closure ledger record or None, stderr)."""
        import contextlib
        import io
        import json

        args = _parse(runner, ["start", *argv, "--repo", str(repo)])
        args.prepare_only = True
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            run_dir = _MODULES[runner].initialize_run(args)
        state = runner_shared.load_state(run_dir)
        events = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        closure = [e for e in events if e.get("event") == "dependency-closure"]
        return (
            [item["id6"] for item in state["queue"]],
            closure[0] if closure else None,
            err.getvalue(),
        )

    def run_case(self, runner, plans, argv, *, spec_id6=None):
        import tempfile
        from pathlib import Path as _P

        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(_P(td), plans, spec_id6=spec_id6)
            return self.initialize(runner, repo, argv)

    # ---- the expansion itself -------------------------------------------------------------------

    def test_a_transitive_closure_is_enqueued_on_both_hosts(self):
        """CASE (a): A depends on B depends on C; selecting A alone enqueues all three.

        TRANSITIVE, not one hop, which is the word spec :166 uses. A one-hop implementation passes an
        A->B test and silently leaves C out, and the operator's whole reason for the flag (be certain
        the prerequisites are queued) fails for exactly the graph that needed it most.
        """
        plans = {
            "aaa111": ("executed:bbb222", "pending"),
            "bbb222": ("executed:ccc333", "pending"),
            "ccc333": ("none", "pending"),
        }
        for runner in BOTH:
            with self.subTest(runner=runner):
                ids, closure, err = self.run_case(
                    runner, plans, ["aaa111", "--with-dependencies"]
                )
                self.assertEqual(sorted(ids), ["aaa111", "bbb222", "ccc333"], err)
                assert closure is not None
                self.assertTrue(closure["applied"])
                self.assertEqual(
                    sorted(row["id6"] for row in closure["added"]),
                    ["bbb222", "ccc333"],
                )
                self.assertIn("--with-dependencies expanded the selection", err)

    def test_the_flag_absent_case_changes_nothing(self):
        """CASE (b), THE REGRESSION GUARD. Spec :166: without the flag, an outside dependency is
        "checked against current repository state but not silently enqueued".

        Asserted on the SAME graph the expansion case uses, so the only difference between the two
        observations is the flag. An unconditional expansion would pass every other test in this class
        and fail only here, which is why this case is quoted separately in the plan's validation.

        The ledger record is asserted ABSENT too, not merely `applied: False`: a run that did not
        expand should not carry a closure event at all, or a reader of `events.jsonl` cannot tell a
        no-op expansion from one that was never asked for.
        """
        plans = {
            "aaa111": ("executed:bbb222", "pending"),
            "bbb222": ("executed:ccc333", "pending"),
            "ccc333": ("none", "pending"),
        }
        for runner in BOTH:
            with self.subTest(runner=runner):
                ids, closure, err = self.run_case(runner, plans, ["aaa111"])
                self.assertEqual(ids, ["aaa111"], err)
                self.assertIsNone(
                    closure,
                    "a run that was never asked to expand must not record a closure event",
                )
                self.assertNotIn("expanded the selection", err)

    def test_a_cycle_terminates_and_a_diamond_enqueues_each_target_once(self):
        """CASES (c) and (d) together, because both are the SAME property of the walk: a visited set.

        Merged deliberately rather than split: a cycle and a diamond are one claim (each id is expanded
        at most once, each target enqueued at most once) observed on two graph shapes, and they fail
        together the moment the visited set is dropped. A cycle without it HANGS - so a regression here
        is a test-suite timeout rather than a failure, which is worth knowing when reading a red run.

        THE SELF-EDGE IS THE THIRD SHAPE and is in the cycle row: `A -> A` is a cycle of length one and
        must neither loop nor duplicate A in the queue.

        THE CYCLE ROW IS ASSERTED AT THE CLOSURE's OWN LEVEL, deliberately, because end to end a cycle
        is REFUSED by the pre-existing dependency preflight with the shared evaluator's
        `check.ipd-dependency-cycle` finding - and that is the correct division of labour, not an
        obstacle: the closure's job is to TERMINATE, and naming a cycle belongs to the evaluator that
        every surface consults. So the row drives `expand_dependency_closure` directly (proving the walk
        returns rather than hanging) and then asserts the END-TO-END outcome is the evaluator's refusal,
        which is what proves the closure neither hung nor quietly adjudicated a cycle it does not own.
        """
        cycle = {
            "aaa111": ("executed:bbb222", "pending"),
            "bbb222": ("executed:aaa111", "pending"),
        }
        import tempfile
        from pathlib import Path as _P

        selfedge = {"aaa111": ("executed:aaa111", "pending")}
        diamond = {
            "aaa111": ("executed:bbb222, executed:ccc333", "pending"),
            "bbb222": ("executed:ddd444", "pending"),
            "ccc333": ("executed:ddd444", "pending"),
            "ddd444": ("none", "pending"),
        }
        for shape, plans, expected in (
            ("cycle", cycle, ["aaa111", "bbb222"]),
            ("self-edge", selfedge, ["aaa111"]),
        ):
            with self.subTest(shape=shape, level="the closure walk itself"):
                with tempfile.TemporaryDirectory() as td:
                    repo = self.make_repo(_P(td), plans)
                    manifest = runner_shared.build_dynamic_manifest(
                        repo,
                        runner_shared.discover_plans(
                            repo, parse_plan_file=runner_shared.parse_plan_file
                        ),
                    )
                    # RETURNS rather than hanging; that is the property, and each id is visited once.
                    ids, record = runner_shared.expand_dependency_closure(
                        repo,
                        manifest,
                        ["aaa111"],
                        with_dependencies=True,
                        # The HOST's predicate, supplied exactly as `initialize_run_core` supplies it;
                        # omitting it would silently skip the satisfaction half of the rule and make
                        # this a test of the disposition half alone by accident rather than by design.
                        edge_satisfied_fn=oc_runipd.edge_satisfied,
                    )
                    self.assertEqual(sorted(ids), expected)
                    self.assertEqual(sorted(record["visited"]), expected)
        for runner in BOTH:
            with self.subTest(runner=runner, shape="cycle", level="end to end"):
                with self.assertRaises(runner_shared.DriverError) as caught:
                    self.run_case(runner, cycle, ["aaa111", "--with-dependencies"])
                self.assertIn("ipd-dependency-cycle", str(caught.exception))
            with self.subTest(runner=runner, shape="self-edge", level="end to end"):
                # Same division of labour as the cycle: the shared evaluator names a self-dependency
                # (`check.ipd-dependency-malformed`), and the closure's obligation is only that it
                # reached that refusal instead of looping forever on the way there.
                with self.assertRaises(runner_shared.DriverError) as caught:
                    self.run_case(runner, selfedge, ["aaa111", "--with-dependencies"])
                self.assertIn("self-dependency", str(caught.exception))
            with self.subTest(runner=runner, shape="diamond"):
                ids, closure, err = self.run_case(
                    runner, diamond, ["aaa111", "--with-dependencies"]
                )
                self.assertEqual(
                    sorted(ids), ["aaa111", "bbb222", "ccc333", "ddd444"], err
                )
                self.assertEqual(
                    len([i for i in ids if i == "ddd444"]),
                    1,
                    "the diamond's shared target must be enqueued ONCE",
                )
                assert closure is not None
                self.assertEqual(
                    len([r for r in closure["added"] if r["id6"] == "ddd444"]), 1
                )

    # ---- the cases it must NOT expand ------------------------------------------------------------

    def test_an_already_terminal_target_is_not_enqueued(self):
        """CASE (h), THE RE-EXECUTION GUARD, and the assertion is about the QUEUE, not about dispatch.

        A selection whose plan declares `executed:<id6>` against a plan sitting in `executed/` must NOT
        gain that plan. Pasting a run in which the finished plan APPEARS in the queue but was never
        dispatched would prove only the queue builder's incidental `status: "reviewed"` default plus the
        dispatch loop's `queued` filter - not this plan's skip rule. So the id6 is asserted ABSENT from
        the queue, which only the closure's own rule can achieve.

        THE SKIP IS RECORDED, not silent: the ledger's `skipped` list names the edge and the reason, so
        an operator who expected a target and did not get one can see why without reading the source.
        """
        plans = {
            "aaa111": ("executed:bbb222", "pending"),
            "bbb222": ("none", "executed"),
        }
        for runner in BOTH:
            with self.subTest(runner=runner):
                ids, closure, err = self.run_case(
                    runner, plans, ["aaa111", "--with-dependencies"]
                )
                self.assertEqual(
                    ids,
                    ["aaa111"],
                    "a plan already in `executed/` must NOT be pulled into the queue; "
                    f"`action_for` would give it an `execute` action. queue={ids} err={err}",
                )
                assert closure is not None
                self.assertEqual(closure["added"], [])
                self.assertEqual(len(closure["skipped"]), 1)
                reason = closure["skipped"][0]["reason"]
                # WHICH rule fired is asserted, not merely that SOME rule did. For an already-executed
                # target BOTH apply, and the SHIPPED satisfaction predicate is the one that should
                # answer first, because that is the same question dispatch will ask later; a reason
                # naming only the disposition would mean the closure had derived satisfaction itself.
                self.assertIn("edge_satisfied", reason)
                self.assertIn("bbb222", reason)

    def test_a_retired_target_is_skipped_by_the_DISPOSITION_rule_not_the_satisfaction_one(
        self,
    ):
        """The skip rule has TWO independent halves, and this proves the second one is load-bearing.

        An `executed/` target is skipped by BOTH halves, so a suite testing only that case cannot tell
        whether the disposition check does any work. A `superseded/`, `not-executed/` or `reusable/`
        target separates them: `edge_satisfied` correctly reports such an edge UNMET (retiring a plan is
        not executing it), so the FIRST half says "add" and only the disposition half keeps it out.

        WHY KEEPING IT OUT IS RIGHT even though the edge is unmet: the target is retired work. Running
        it is not how the edge gets met, and `reusable` in particular is a standing plan that an
        operator runs on purpose, so pulling one in as a side effect of another selection would execute
        recurring work nobody asked for in this run. The dependent's own edge is still enforced by the
        preflight and the dispatch-time re-check, which is what refuses it on its merits.
        """
        import tempfile
        from pathlib import Path as _P

        for disposition in ("superseded", "not-executed", "reusable"):
            with self.subTest(disposition=disposition):
                plans = {
                    "aaa111": ("executed:bbb222", "pending"),
                    "bbb222": ("none", disposition),
                }
                with tempfile.TemporaryDirectory() as td:
                    repo = self.make_repo(_P(td), plans)
                    manifest = runner_shared.build_dynamic_manifest(
                        repo,
                        runner_shared.discover_plans(
                            repo, parse_plan_file=runner_shared.parse_plan_file
                        ),
                    )
                    from agent_workflows import ipd_schema

                    edge, _err = ipd_schema._parse_item_dependency_edge(
                        "executed:bbb222"
                    )
                    # The FIRST half genuinely says this edge is NOT satisfied ...
                    met, _why = oc_runipd.edge_satisfied(
                        edge, {"action": "execute"}, {"repo": str(repo)}, {}
                    )
                    self.assertFalse(
                        met,
                        f"a {disposition} target must NOT satisfy an `executed:` edge, or this test "
                        "is not separating the two halves of the skip rule",
                    )
                    # ... and the SECOND half is what keeps it out of the queue anyway.
                    ids, record = runner_shared.expand_dependency_closure(
                        repo,
                        manifest,
                        ["aaa111"],
                        with_dependencies=True,
                        # The HOST's predicate, supplied exactly as `initialize_run_core` supplies it;
                        # omitting it would silently skip the satisfaction half of the rule and make
                        # this a test of the disposition half alone by accident rather than by design.
                        edge_satisfied_fn=oc_runipd.edge_satisfied,
                    )
                    self.assertEqual(ids, ["aaa111"])
                    self.assertEqual(len(record["skipped"]), 1)
                    self.assertIn(disposition, record["skipped"][0]["reason"])

    def test_the_skip_rule_is_what_keeps_the_terminal_target_out(self):
        """The counterfactual for the case above: REMOVE the rule and the finished plan IS enqueued.

        WHY THIS EXISTS AS A SEPARATE TEST. "The queue does not contain B" is satisfied by an
        implementation that never expands at all, and by one whose expansion happens to fail; neither
        would be the skip rule working. This patches `closure_target_admission` to the naive behavior
        (`add` for everything resolvable) and requires the terminal plan to appear, which is what makes
        the previous test's green meaningful rather than vacuous.
        """
        plans = {
            "aaa111": ("executed:bbb222", "pending"),
            "bbb222": ("none", "executed"),
        }
        real = runner_shared.closure_target_admission

        def naive(repo, edge, *, manifest, edge_satisfied_fn=None):
            verdict, reason = real(
                repo, edge, manifest=manifest, edge_satisfied_fn=edge_satisfied_fn
            )
            return ("add", "") if verdict == "skip" else (verdict, reason)

        for runner in BOTH:
            with self.subTest(runner=runner):
                with mock.patch.object(
                    runner_shared, "closure_target_admission", naive
                ):
                    ids, _c, err = self.run_case(
                        runner, plans, ["aaa111", "--with-dependencies"]
                    )
                self.assertIn(
                    "bbb222",
                    ids,
                    "with the skip rule removed the already-executed plan MUST appear, or this "
                    f"counterfactual proves nothing about the rule. queue={ids} err={err}",
                )

    def test_a_non_plan_target_refuses_and_leaves_no_run_directory(self):
        """CASE (i): an `exists:spec:<id6>` edge REFUSES, before any durable state exists.

        THE REFUSAL IS A DELIBERATE NARROWING OF AN APPROVED SPEC, and it is asserted here so the
        narrowing is a tested fact rather than a plan note. Spec :166 says "any newly introduced type
        is subject to the same mixed-type gate", which presupposes a `spec` target can join the queue,
        and `ipd_schema.ITEM_DEP_TYPES` admits the edge as legal grammar. The manifest is plans-only, so
        there is no queue entry to build, and the queue builder's unguarded `manifest["plans"][id6]`
        runs AFTER the run directory is created - a permissive path would therefore raise a bare
        `KeyError` with durable state already written.

        THE RUN ROOT IS ASSERTED ABSENT, which is the half that makes this more than a message test.
        """
        import tempfile
        from pathlib import Path as _P

        plans = {"aaa111": ("exists:spec:sss999", "pending")}
        for runner in BOTH:
            with self.subTest(runner=runner):
                with tempfile.TemporaryDirectory() as td:
                    repo = self.make_repo(_P(td), plans, spec_id6="sss999")
                    with self.assertRaises(runner_shared.ClosureRefusal) as caught:
                        self.initialize(runner, repo, ["aaa111", "--with-dependencies"])
                    message = str(caught.exception)
                    self.assertIn("spec", message)
                    self.assertIn("sss999", message)
                    runs = repo / ".aw" / "records" / "runs"
                    self.assertEqual(
                        sorted(
                            p.name
                            for p in (runs.glob("run-*") if runs.exists() else [])
                        ),
                        [],
                        "a closure refusal must leave NO run directory: it fires at the seam, "
                        "ahead of run-directory creation, exactly as the unimplemented-flag "
                        "refusal used to",
                    )

    def test_an_unresolvable_target_refuses_loudly(self):
        """CASE (f): OQ-02's decision, observed. A dangling target REFUSES rather than warning past.

        The alternative (proceed with a warning) was rejected because a partially expanded closure is
        neither the selection the operator asked for nor the one they would have got without the flag,
        and they cannot tell which from the outside. Measured cost of the strict choice in this
        repository: zero, all 43 declared edges resolve today.

        WITHOUT the flag the same repo must still RUN, which is asserted in the same test: the strict
        choice constrains the EXPANSION only, and the edge's own enforcement is unchanged.
        """
        plans = {"aaa111": ("executed:zzz999", "pending")}
        for runner in BOTH:
            with self.subTest(runner=runner):
                with self.assertRaises(runner_shared.ClosureRefusal) as caught:
                    self.run_case(runner, plans, ["aaa111", "--with-dependencies"])
                self.assertIn("zzz999", str(caught.exception))
                self.assertIn("--with-dependencies", str(caught.exception))

    def test_a_closure_refusal_leaves_no_durable_run_state(self):
        """The guarantee INHERITED from the `REFUSALS` row this flag no longer has.

        `--with-dependencies` used to be a row in
        :class:`FullAutoEndToEndBehaviorTests.test_every_refused_invocation_leaves_no_durable_run_state`,
        which asserted both that it refused and that no `run-*` directory survived. It refuses for
        different reasons now, so this re-asserts the SECOND half for each remaining refusal, and the
        guarantee moves with the behavior rather than being quietly dropped when the row was deleted.
        """
        import tempfile
        from pathlib import Path as _P

        cases = (
            (
                "an unresolvable target",
                {"aaa111": ("executed:zzz999", "pending")},
                None,
            ),
            (
                "a non-plan target",
                {"aaa111": ("exists:spec:sss999", "pending")},
                "sss999",
            ),
        )
        for case, plans, spec_id6 in cases:
            for runner in BOTH:
                with self.subTest(case=case, runner=runner):
                    with tempfile.TemporaryDirectory() as td:
                        repo = self.make_repo(_P(td), plans, spec_id6=spec_id6)
                        with self.assertRaises(runner_shared.ClosureRefusal):
                            self.initialize(
                                runner, repo, ["aaa111", "--with-dependencies"]
                            )
                        runs = repo / ".aw" / "records" / "runs"
                        self.assertEqual(
                            sorted(
                                p.name
                                for p in (runs.glob("run-*") if runs.exists() else [])
                            ),
                            [],
                        )

    # ---- the mixed-type gate, at its HONEST level of reachability --------------------------------

    def test_an_expansion_introducing_no_new_type_does_not_trigger_the_gate(self):
        """CASE (e), the NEGATIVE half, and it is the half that is end-to-end reachable.

        A gate that fired on correct behavior would train operators to pass `--allow-mixed` reflexively,
        which is the failure mode backlog `gjadwm` records. Every id a closure can add is an IPD (a
        non-plan target refuses), so a real expansion must leave the classification single-type and the
        gate must NOT apply.
        """
        plans = {
            "aaa111": ("executed:bbb222", "pending"),
            "bbb222": ("none", "pending"),
        }
        import json
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            with self.subTest(runner=runner):
                with tempfile.TemporaryDirectory() as td:
                    repo = self.make_repo(_P(td), plans)
                    args = _parse(
                        runner,
                        [
                            "start",
                            "aaa111",
                            "--with-dependencies",
                            "--repo",
                            str(repo),
                        ],
                    )
                    args.prepare_only = True
                    import contextlib
                    import io

                    with contextlib.redirect_stderr(io.StringIO()):
                        run_dir = _MODULES[runner].initialize_run(args)
                    events = [
                        json.loads(line)
                        for line in (run_dir / "events.jsonl")
                        .read_text(encoding="utf-8")
                        .splitlines()
                        if line.strip()
                    ]
                    gate = next(e for e in events if e["event"] == "mixed-type-gate")
                    self.assertFalse(gate["gate_applied"])
                    self.assertTrue(gate["proceed"])
                    self.assertEqual(gate["type_counts"], {"ipd": 2})

    def test_a_new_type_reaches_the_same_refusal_at_the_level_it_is_reachable_at(self):
        """CASE (e), the POSITIVE half, AND THE STATEMENT OF ITS LIMIT, which is the honest part.

        THE LEVEL: a new type is reachable only at the `classify_paths`/`decide` level, NOT end to end,
        because the closure REFUSES a non-plan target and because `enforce_mixed_type_gate` is handed
        `selected_plan_paths` - built by a loop that resolves `manifest["plans"][id6]` inside
        `except (DriverError, KeyError): continue` - rather than `queue_ids`, so a manifest-absent
        target is dropped before classification.

        SO, IN THE GATE DOCSTRING'S OWN WORDS: the wiring is proven correct; a live mixed selection
        being gated is NOT proven, and must not be reported as if it were. This test therefore proves
        (1) that a genuinely mixed classification still produces the verbatim `RUN-MIXED-TYPES`
        refusal unattended, and (2) that the closure is the reason the live arm is unreachable - by
        asserting the refusal for the non-plan target, which is what an operator actually gets.

        A UNIT-LEVEL `decide` CALL IS NOT PRESENTED AS AN END-TO-END RE-TRIGGER. That conflation is
        what the gate's docstring warns against and is why both halves are asserted in one test.
        """
        import tempfile
        from pathlib import Path as _P

        from agent_workflows import run_selection_policy

        # A REAL multi-type classification, produced by the shipped `classify_paths` over real files
        # rather than hand-constructed: a hand-built `Classification` could assert a shape
        # `classify_paths` never produces, which would make this half of the test vacuous.
        with tempfile.TemporaryDirectory() as td:
            root = _P(td)
            plans = root / ".aw" / "records" / "plans" / "pending"
            specs = root / ".aw" / "records" / "specs"
            plans.mkdir(parents=True)
            specs.mkdir(parents=True)
            ipd = plans / "20260905-demo-01-aaa111-demo.ipd.md"
            ipd.write_text("- Status: approved\n- Id: aaa111\n", encoding="utf-8")
            spec = specs / "20260905-bbb222-01-bbb222-demo.spec.md"
            spec.write_text("- Status: approved\n- Id: bbb222\n", encoding="utf-8")
            classification = run_selection_policy.classify_paths(root, [ipd, spec])
            self.assertTrue(
                classification.is_mixed,
                f"the fixture is not multi-type: {classification.spec_types}",
            )
            verdict = run_selection_policy.decide(
                classification,
                interactive=False,
                allow_mixed=False,
                response=None,
                host="oc",
                selector="aaa111 --with-dependencies",
            )
        self.assertTrue(verdict.gate_applied)
        self.assertFalse(verdict.proceed)
        self.assertIn("RUN-MIXED-TYPES", verdict.message or "")

        # And the reason that arm is not reachable through a real invocation: the closure refuses the
        # only edge that could introduce the type, so the operator meets THIS message instead.
        plans = {"aaa111": ("exists:spec:sss999", "pending")}
        for runner in BOTH:
            with self.subTest(runner=runner):
                with self.assertRaises(runner_shared.ClosureRefusal) as caught:
                    self.run_case(
                        runner,
                        plans,
                        ["aaa111", "--with-dependencies"],
                        spec_id6="sss999",
                    )
                self.assertIn("mixed-type gate", str(caught.exception))

    def test_the_closure_has_ONE_definition_and_both_hosts_reach_THAT_one(self):
        """HOST PARITY BY IDENTITY, at the level the code is actually shared.

        NOT A ROW IN `tests/test_runner_refork_guard.py`, and the reason is worth stating so nobody
        "fixes" it by adding one. That guard's contract is that each runner EXPOSES the owner's object
        at an attribute name the runner's own call sites use; `expand_dependency_closure` has no such
        call site, because it is invoked from inside `runner_shared.initialize_run_core`, which both
        hosts delegate to. Adding a row would require the runners to import a symbol they never use, so
        the guard's own precondition is absent and the honest parity claim is one level up: ONE core,
        reached by both, therefore one closure.

        BOTH HALVES ARE ASSERTED for the same reason that guard asserts both of its: the identity half
        alone passes while a stale duplicate definition sits in a runner being shadowed by an import,
        and the AST half alone passes while a name is rebound at runtime.
        """
        import ast
        import inspect
        import pathlib

        self.assertIs(
            oc_runipd.runner_shared.initialize_run_core,
            agy_runipd.runner_shared.initialize_run_core,
        )
        core = inspect.getsource(runner_shared.initialize_run_core)
        self.assertIn("expand_dependency_closure(", core)
        for runner in BOTH:
            module = _MODULES[runner]
            with self.subTest(runner=runner):
                self.assertIn(
                    "initialize_run_core",
                    inspect.getsource(module.initialize_run),
                    f"{runner}.initialize_run must delegate to the shared core, or the closure has "
                    "two call sites and this class proves parity for only one of them",
                )
                tree = ast.parse(
                    pathlib.Path(inspect.getfile(module)).read_text(encoding="utf-8")
                )
                defined = {
                    node.name
                    for node in tree.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                }
                for name in (
                    "expand_dependency_closure",
                    "closure_target_admission",
                ):
                    self.assertNotIn(
                        name,
                        defined,
                        f"{runner} defines its own {name}; the closure must have exactly one "
                        "definition, in the shared module",
                    )
