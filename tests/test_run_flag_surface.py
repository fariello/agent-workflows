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
SPEC_PATH = next(
    (REPO_ROOT / ".aw" / "records" / "specs").rglob(
        "20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md"
    )
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
#:
#: `--type` WAS excluded here and no longer is: `specsweep-01` (`ui8b9b`) registered it in
#: `RUN_POLICY_FLAGS` and threaded it to the already-shipped type-scoped sweep, so this surface now
#: OWNS it. The row was MOVED rather than deleted-and-re-added, which is the distinction
#: `test_every_flag_the_spec_declares_is_accounted_for` measures: `declared - owned - excluded` must
#: stay empty, so an exclusion whose owner has landed has to become an owned row in the same change.
#: Its former reason read "needs the whole per-type dispatch table, not a flag", and that reading was
#: HALF right, which is why the flag could land without the table: SELECTION needed only the flag,
#: while EXECUTION does need the table and is deliberately still absent (spec `z7nbn1` owns it, and
#: `--type spec` is refused at queue build rather than pretending to run).
DECLARED_BUT_NOT_OWNED_HERE = {
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


def _record(order: list, label: str, real):
    """`real`, but appending `label` to `order` FIRST, for call-ORDER assertions.

    The same shape `tests/test_dirty_base_gate.py::_OrderRecorder` uses, and for the same reason:
    a claim about where a gate sits in a sequence is only testable by recording the sequence. Both
    `order` and `label` are PARAMETERS rather than closed-over loop variables, which is the
    late-binding trap that silently makes one host's run assert about another's.
    """

    def _wrapped(*args, **kwargs):
        order.append(label)
        return real(*args, **kwargs)

    return _wrapped


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
            "run.retry_budget",
            "spec 2.1/5.5 declares THREE precedence tiers (CLI > repository policy > default) and "
            "ALL THREE now ship (`y4adch`), so the help must NAME the config key the middle tier "
            "reads. This REPLACES the former `NOT IMPLEMENTED`/`dh3us4` gap-disclosure rows: while "
            "the tier was missing an operator needed the backlog id to find who owned it, and now "
            "that it exists they need the key itself, because `--help` is the ONLY surface telling "
            "a repository owner what to write and where. A row asserting the old disclosure would "
            "now demand the shipped behavior be reported as absent",
        ),
        (
            "--retry-budget",
            "does NOT refuse",
            "the two failure postures DIFFER on purpose (maintainer decision, 2026-09-10): a bad "
            "value passed on the CLI refuses that invocation, while a bad value in the SHARED "
            "tracked `project.json` warns and falls back. An operator who assumes symmetry either "
            "expects a typo in a committed file to break every run in the checkout, or expects a "
            "bad CLI value to be quietly ignored; both readings are wrong and only the help "
            "corrects them",
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

    THE LIMIT IS GONE, AND ITS REMOVAL IS ASSERTED (specsweep-01 `ui8b9b`). This paragraph used to
    record that no live `aw <host> run` invocation could produce a mixed selection, because discovery
    was IPD-only and neither host registered `--type`. `--type` is now registered on both hosts and
    threaded to the type-scoped sweep, so `--type ipd --type spec` reaches this gate from a real
    command line. See :meth:`test_a_live_invocation_CAN_now_produce_a_mixed_selection`, which is the
    former limit test inverted rather than deleted.

    THE REMAINING LIMIT, stated because it is a different one and is still real: a selection CAN now
    be mixed and a non-IPD selection still cannot be EXECUTED. `--type spec` selects specs and is then
    refused at queue build by `runner_shared.refuse_unrunnable_selected_types`, because a queue entry
    is plan-shaped. So this gate is reachable and consequential, while per-type dispatch (spec
    `z7nbn1`) remains unbuilt.
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

    def test_a_live_invocation_CAN_now_produce_a_mixed_selection(self):
        """THE LIMIT, INVERTED (specsweep-01 `ui8b9b` E-04). Formerly
        `test_no_live_invocation_can_yet_produce_a_mixed_selection`.

        WHY THIS TEST CHANGED SIDES RATHER THAN BEING DELETED. `uyeko5` pinned the unreachability
        deliberately, recording that it did so "so registering `--type` later fails here rather than
        silently outgrowing it". `ui8b9b` registered `--type`, so this pin FAILED BY DESIGN and the
        failure was the handoff signal working. Deleting it would have discarded the invariant it was
        defending; inverting it keeps that invariant and flips only the claim that went stale.

        THE INVARIANT IT DEFENDED, AND STILL DEFENDS, is that the mixed-type gate's reachability is a
        FACT ABOUT THE SHIPPED SURFACE rather than a claim in a comment. It asserted that fact in the
        negative when the surface could not reach the gate; it asserts the same fact in the positive
        now that it can. Both directions fail if the flag and the gate ever come apart.

        WHAT IS DELIBERATELY *NOT* INVERTED: the discovery half. `discover_plans` must STILL return
        IPDs only, because `--type spec` reaches the specs tree through `discover_specs`, not by
        widening plan discovery. A `discover_plans` that started returning specs would mean the
        IPD-only default had been widened by the back door, which spec 2.4a property 1 forbids, so that
        assertion is kept exactly as it was.
        """
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            for sub in ("start", "resume"):
                with self.subTest(runner=runner, subcommand=sub):
                    self.assertIn(
                        "--type",
                        _option_strings(runner, sub),
                        f"{runner}/{sub}: `--type` must be REGISTERED. This assertion was inverted by "
                        "`ui8b9b`: while it read `assertNotIn`, the mixed-type gate was unreachable "
                        "from any command line and the shipped `[RUN-MIXED-TYPES]` refusal was dead "
                        "code. If this now fails, the flag was removed and the gate is dead again",
                    )

        # THE GATE ACTUALLY FIRES on a selection the flag can now produce. Registration alone does not
        # prove reachability: the gate is reached with the resolved path set, so a runner that filtered
        # non-plan paths out BEFORE the gate would leave it permanently single-type while every
        # registration assertion above still passed. That filtering is the realistic regression here,
        # which is why this half drives the real gate rather than inspecting the parser.
        from agent_workflows import run_selection_policy

        with tempfile.TemporaryDirectory() as td:
            root = _P(td)
            paths = self.multi_type_paths(root)
            classification = run_selection_policy.classify_paths(root, paths)
            self.assertTrue(
                classification.is_mixed,
                "the two-type path set must classify as MIXED; if it does not, the gate cannot "
                "fire and the reachability claimed above is not real",
            )
            with self.assertRaises(runner_shared.DriverError) as ctx:
                runner_shared.enforce_mixed_type_gate(
                    root,
                    paths,
                    allow_mixed=False,
                    interactive=False,
                    host="oc",
                    selector="reviews",
                )
            self.assertIn("[RUN-MIXED-TYPES]", str(ctx.exception))

        with tempfile.TemporaryDirectory() as td:
            root = _P(td)
            ipd, spec = self.multi_type_paths(root)
            for runner in BOTH:
                with self.subTest(runner=runner):
                    found = _MODULES[runner].discover_plans(root)
                    self.assertEqual(
                        sorted(found),
                        ["aaa111"],
                        f"{runner}: PLAN discovery must STILL return the IPD ONLY, and this half is "
                        f"NOT inverted. The temp repo holds a real spec at {spec.name} beside the "
                        f"IPD at {ipd.name}. `--type spec` reaches specs through `discover_specs`, "
                        "so a spec appearing HERE would mean the normative IPD-only default (spec "
                        "2.4a property 1) had been widened through plan discovery instead",
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


class RepositoryPolicyRetryTierTests(unittest.TestCase):
    """`y4adch` E-05: spec 2.1/5.5's MIDDLE precedence tier, CLI over repository policy over 2.

    WHY THIS IS A SEPARATE CLASS FROM `RetryBudgetTests` RATHER THAN A COLUMN IN ITS TABLE. That
    table's rows are PURE: each feeds one integer to the resolver with no repository in sight, and
    that purity is the point (the resolver must stay callable at parse time, where no repo may be
    resolved). Every row here needs a REPOSITORY ON DISK, because the value under test is read from
    `.aw/config/project.json`. Adding a fixture repo to those rows would make ten pure assertions pay
    for a filesystem they do not use, and would blur which tier a failure came from.

    THE FIXTURES ARE THROWAWAY REPOS, NEVER THIS ONE. `.aw/config/project.json` is TRACKED and other
    agents work in this checkout, so a test that wrote to the real file would change every other run's
    behavior in the tree. `tests.support.REPO_ROOT` is imported by this module for READING the spec
    and is deliberately not used here.
    """

    #: Only the key path spec 5.5 names, plus the flat convenience form both precedents in
    #: `config.py` also tolerate. Written as DATA so a case states its document rather than
    #: constructing one inline.
    def write_policy(self, root, document) -> "object":
        """A repo directory holding `document` as `.aw/config/project.json` (or none if None)."""
        repo = root / "repo"
        (repo / ".aw" / "config").mkdir(parents=True, exist_ok=True)
        if document is not None:
            import json as _json

            (repo / ".aw" / "config" / "project.json").write_text(
                _json.dumps(document), encoding="utf-8"
            )
        return repo

    #: (case, config document or None for "no file at all", CLI value, expected effective budget,
    #: whether a WARNING must be emitted, why this row exists)
    #:
    #: THE EXPECTED VALUES ARE LITERAL where they are policy values and DERIVED where they are the
    #: default, which is the opposite of `RetryBudgetTests`' choice and deliberately so: there the
    #: literals pin an operator-facing RANGE that must fail on a widening, whereas here `2` is the
    #: DEFAULT tier and its single definition is `run_recovery.DEFAULT_RETRY_LIMIT`. Writing `2` in
    #: these rows would put a second copy of the default in the test file, which is exactly what
    #: `sq61qd` collapsed.
    CASES = (
        (
            "CLI value alongside a set policy",
            {"run": {"retry_budget": 9}},
            4,
            4,
            False,
            "CASE (a), THE PRECEDENCE GUARD. The CLI is the HIGHEST tier, so a policy must not win "
            "when a flag was passed. A resolver that consults config first, or that treats the "
            "policy as an override, inverts spec 2.1's chain and makes an explicit operator "
            "instruction lose to a committed file",
        ),
        (
            "set policy with no CLI value",
            {"run": {"retry_budget": 9}},
            None,
            9,
            False,
            "CASE (b), the tier this plan EXISTS to add. Before it, this row returned the default "
            "and the code said so in its own docstring",
        ),
        (
            "a policy of zero with no CLI value",
            {"run": {"retry_budget": 0}},
            None,
            0,
            False,
            "`0` IS A LEGAL POLICY meaning no retries (spec 5.5), so the middle tier's guard must be "
            "`is None`-shaped like the CLI tier's. A truthiness test silently converts a "
            "repository's deliberate no-retry policy into two retries, which is the same defect "
            "`RetryBudgetTests`' zero rows guard on the CLI side",
        ),
        (
            "a file with no run key",
            {"schema_version": 2},
            None,
            None,
            False,
            "CASE (c). A project config that simply does not set the key is the COMMON case, and "
            "must reach the default silently - no warning, because nothing is wrong",
        ),
        (
            "no config file at all",
            None,
            None,
            None,
            False,
            "CASE (d). A fresh repository has no `.aw/config/project.json`, so an absent file must "
            "never be an error and must never warn",
        ),
        (
            "an explicit null policy",
            {"run": {"retry_budget": None}},
            None,
            None,
            False,
            "an explicit null is how a key is CLEARED, which is a normal edit and not a malformed "
            "value, so it must fall through silently rather than warning",
        ),
        (
            "a policy out of the 0..10 range",
            {"run": {"retry_budget": 11}},
            None,
            None,
            True,
            "CASE (e). The bound is `sq61qd`'s single definition and the POLICY value must be "
            "routed through it too, so a flag and a config key cannot disagree about what is legal. "
            "It FALLS BACK AND WARNS rather than refusing (maintainer decision, 2026-09-10): the "
            "identical value on the CLI refuses, and the asymmetry is deliberate because this file "
            "is shared and tracked",
        ),
        (
            "a malformed policy (string)",
            {"run": {"retry_budget": "lots"}},
            None,
            None,
            True,
            "CASE (f). A wrong TYPE is the likeliest hand-edit mistake, and the one that would be "
            "most damaging to swallow: a repository that believes it set a policy would be silently "
            "overridden, which is precisely why the maintainer chose a warning over silence",
        ),
        (
            "a malformed policy (bool)",
            {"run": {"retry_budget": True}},
            None,
            None,
            True,
            "`bool` is an `int` subclass in Python, so `True` would smuggle in `1` if the type check "
            "were a bare `isinstance(int)`. `run_recovery.validate_retry_budget` excludes bools for "
            "the same reason; this row keeps the config path from being the loophole",
        ),
        (
            "the flat convenience form",
            {"retry_budget": 6},
            None,
            6,
            False,
            "spec 5.5 names `run.retry_budget`, which is what the nested rows above assert. A "
            "repository owner writing the obvious FLAT key is making an understandable mistake, and "
            "both precedents in `config.py` tolerate a convenience shape, so honoring it costs "
            "nothing and silently ignoring it would be the worst outcome",
        ),
    )

    def test_every_policy_document_resolves_to_the_right_tier(self):
        """Cases (a) to (f) in one table, with the WARNING as a column.

        The warning is a column and not a separate test because the maintainer's OQ-01 answer makes
        the fallback and the warning ONE behavior: "fall back to the default AND emit a visible
        warning". A table that asserted only the returned integer would pass against a silent
        fallback, which is the option the maintainer explicitly declined.
        """
        import tempfile
        from pathlib import Path as _P

        from agent_workflows import run_recovery

        wrong = []
        for case, document, cli, expected, warns, why in self.CASES:
            want = run_recovery.DEFAULT_RETRY_LIMIT if expected is None else expected
            problems = []
            with tempfile.TemporaryDirectory() as td:
                repo = self.write_policy(_P(td), document)
                warnings: list = []
                got = runner_shared.resolve_retry_budget(
                    cli, repo=repo, warn=warnings.append
                )
            if got != want:
                problems.append(
                    f"resolved to {got!r}, expected {want!r}"
                    + ("" if expected is not None else " (the DEFAULT tier)")
                )
            if warns and not warnings:
                problems.append(
                    "no WARNING was emitted. A silent fallback overrides a repository that believes "
                    "it set a policy with no signal anywhere, which is the option the maintainer "
                    "DECLINED on 2026-09-10"
                )
            if not warns and warnings:
                problems.append(
                    f"an unexpected warning was emitted: {warnings!r}. Warning on a NORMAL absence "
                    "trains operators to ignore the warning that matters"
                )
            for emitted in warnings:
                if "retry_budget" not in emitted:
                    problems.append(
                        f"the warning does not name the KEY: {emitted!r}. A warning that says only "
                        "'invalid config' reproduces the silent-override problem one step removed"
                    )
                if "project.json" not in emitted:
                    problems.append(
                        f"the warning does not name the FILE: {emitted!r}. In a shared checkout the "
                        "operator needs to know WHICH file to fix"
                    )
            if problems:
                wrong.append(
                    f"  {case} (config={document!r}, cli={cli!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the repository-policy tier is wrong for {len(wrong)} of {len(self.CASES)} documents. "
            "READ THEM TOGETHER: if the CLI row fails ALONE, precedence is inverted and an explicit "
            "flag loses to a committed file. If every ABSENT row fails, the accessor is treating a "
            "missing file or key as an error instead of as 'no policy set', which breaks every fresh "
            "repository. If the out-of-range row RESOLVES to 11 instead of falling back, the policy "
            "value is bypassing `run_recovery.validate_retry_budget` and the bound now has two "
            "definitions. If only the WARNING halves fail, the fallback is silent, which is the "
            "posture the maintainer declined.\n" + "\n".join(wrong),
        )

    def test_the_policy_value_is_validated_by_sq61qds_single_definition(self):
        """The bound is CALLED for the POLICY value too, proven with a sentinel rather than a grep.

        The same technique `test_the_bound_is_sq61qds_and_is_not_re_checked_here` uses for the CLI
        tier, applied to the tier this plan added: patch the shared validator and require THIS
        layer's answer to change. A private range check in the config path keeps returning the real
        value, so the sentinel never appears - and a config path that validated the value itself
        would be a SECOND copy of a bound whose whole design (`sq61qd`) is that it has one.
        """
        import tempfile
        from pathlib import Path as _P

        from agent_workflows import run_recovery

        with tempfile.TemporaryDirectory() as td:
            repo = self.write_policy(_P(td), {"run": {"retry_budget": 5}})
            with mock.patch.object(
                run_recovery, "validate_retry_budget", lambda value: 99
            ):
                self.assertEqual(
                    runner_shared.resolve_retry_budget(None, repo=repo),
                    99,
                    "patching `run_recovery.validate_retry_budget` must change the POLICY tier's "
                    "answer too. Getting 5 back means the config path accepted the value without "
                    "reaching the shared bound, so a repository could set a budget the CLI would "
                    "refuse",
                )

    def test_an_absent_repo_argument_means_no_policy_tier_and_never_reads_a_file(self):
        """OQ-04's optional parameter, asserted as a PROPERTY rather than as a signature.

        `repo=None` must mean "no repository known, therefore no policy tier", not "look somewhere
        sensible". This is what keeps the resolver callable at parse time and what makes the pure
        rows in `RetryBudgetTests` a real code path rather than an accident. Asserted by patching
        the accessor and requiring it NOT to be called: a signature check would pass against an
        implementation that defaulted the root to the current working directory, which would make a
        run's budget depend on where it was invoked from.
        """
        from agent_workflows import config as _config
        from agent_workflows import run_recovery

        calls: list = []

        def _spy(repo_root, **kwargs):
            calls.append(repo_root)
            return 9

        with mock.patch.object(_config, "policy_retry_budget", _spy):
            self.assertEqual(
                runner_shared.resolve_retry_budget(None),
                run_recovery.DEFAULT_RETRY_LIMIT,
                "with no `repo`, the resolver must fall straight through to the DEFAULT tier",
            )
        self.assertEqual(
            calls,
            [],
            "the policy accessor was consulted with NO repository argument, so the resolver invented "
            f"a root ({calls!r}). A budget that depends on the invocation's working directory is "
            "worse than a missing tier, because it is unpredictable rather than merely absent",
        )

    def test_a_changed_policy_cannot_move_the_frozen_value_on_resume(self):
        """CASE (g), THE FREEZE GUARD, asserted as an existing structural property.

        Stated honestly: this asserts a property the resume path ALREADY had, and says why it is
        still worth a test. `--retry-budget` carries `resume_rule=RESUME_REFUSE`, and
        `apply_run_policy_flags_on_resume` SKIPS every such row and never re-resolves, so a resume
        reads the frozen integer and has no code path that can consult config. The risk this plan
        introduced is that ADDING a config read could tempt a later change to re-resolve on resume,
        which spec `:162` forbids ("The frozen value cannot change on resume").

        Driven rather than reasoned: the frozen state says 3, the repository's policy then changes to
        9, and the resume must still report 3.
        """
        import tempfile
        from pathlib import Path as _P

        with tempfile.TemporaryDirectory() as td:
            repo = self.write_policy(_P(td), {"run": {"retry_budget": 3}})
            args = argparse.Namespace(
                **{row.dest: None for row in runner_shared.RUN_POLICY_FLAGS}
            )
            frozen = runner_shared.freeze_run_policy_flags(args, repo=repo)
            self.assertEqual(
                frozen["retry_budget"],
                3,
                "precondition: the run froze the repository's policy value",
            )
            state = {"options": dict(frozen)}
            self.write_policy(_P(td), {"run": {"retry_budget": 9}})
            resume_args = argparse.Namespace(
                **{row.dest: None for row in runner_shared.RUN_POLICY_FLAGS}
            )
            runner_shared.apply_run_policy_flags_on_resume(state, resume_args)
            self.assertEqual(
                state["options"]["retry_budget"],
                3,
                "the FROZEN budget must stand even though the repository's policy changed to 9 "
                "since the run started (spec `:162`). A 9 here means a resume re-resolved from "
                "config, so a run's retry budget could change under it between its first turn and "
                "its last",
            )
            self.assertEqual(
                runner_shared.frozen_retry_budget(state),
                3,
                "and the reader every consumer uses must agree, since that is the value a retry is "
                "actually spent against",
            )

    def test_the_frozen_value_that_reaches_run_state_is_the_policy_value(self):
        """CASE (h): the tier reaches DURABLE STATE, not merely the resolver's return.

        THE ONE CASE WITHOUT WHICH THIS WHOLE CLASS PROVES NOTHING OBSERVABLE. Cases (a) to (g) can
        all pass against a resolver whose answer never reaches the freeze path, because the two early
        `resolve_retry_budget` calls in `initialize_run_core` DISCARD their result and exist only for
        the early refusal. `freeze_run_policy_flags` is the only call whose value is kept, so a change
        that resolves correctly and freezes the default is indistinguishable from doing nothing.
        """
        import tempfile
        from pathlib import Path as _P

        from agent_workflows import run_recovery

        with tempfile.TemporaryDirectory() as td:
            repo = self.write_policy(_P(td), {"run": {"retry_budget": 7}})
            args = argparse.Namespace(
                **{row.dest: None for row in runner_shared.RUN_POLICY_FLAGS}
            )
            frozen = runner_shared.freeze_run_policy_flags(args, repo=repo)
        self.assertEqual(
            frozen["retry_budget"],
            7,
            "the FROZEN budget must be the repository's policy value. Getting "
            f"{run_recovery.DEFAULT_RETRY_LIMIT} means `freeze_run_policy_flags` was not given the "
            "repo root, so the middle tier resolves correctly somewhere and never reaches the run "
            "state anything spends the budget from",
        )
        self.assertNotEqual(
            frozen["retry_budget"],
            run_recovery.DEFAULT_RETRY_LIMIT,
            "the fixture's policy is deliberately NOT the default, so this row cannot pass by "
            "coincidence",
        )

    def test_the_frozen_options_shape_is_unchanged(self):
        """The consumption premise `xipfy1` (`retrywire-01`) depends on: one integer, same key.

        That plan reads the FROZEN budget from `state["options"]` and explicitly does not re-resolve
        ("Do NOT call `resolve_retry_budget` again in the loop"). It was `Status: to-review` when this
        plan was reviewed, so this asserts the property in a form that holds whether or not it has
        landed: adding a tier must not change the KEY or the TYPE, only which number appears.
        """
        import tempfile
        from pathlib import Path as _P

        with tempfile.TemporaryDirectory() as td:
            args = argparse.Namespace(
                **{row.dest: None for row in runner_shared.RUN_POLICY_FLAGS}
            )
            without = runner_shared.freeze_run_policy_flags(args)
            repo = self.write_policy(_P(td), {"run": {"retry_budget": 7}})
            with_policy = runner_shared.freeze_run_policy_flags(args, repo=repo)
        self.assertEqual(
            set(without),
            set(with_policy),
            "the frozen options' KEY SET must not change when a repository policy is in force. A new "
            "key here would mean a consumer reading `retry_budget` is no longer reading the whole "
            "policy, and an absent one would break every reader",
        )
        self.assertIsInstance(
            with_policy["retry_budget"],
            int,
            "`retry_budget` must remain a bare integer. A dict or a string recording WHICH tier won "
            "would be a more informative value and would break every existing consumer, including "
            "`frozen_retry_budget`",
        )
        self.assertNotIsInstance(
            with_policy["retry_budget"],
            bool,
            "and not a bool, which `int` would otherwise admit",
        )


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

    def test_the_gate_runs_after_resolution_but_before_any_durable_run_state(self):
        """Spec 2.5a's seam, OBSERVED at the moment the gate runs rather than inferred from text.

        REPLACES A BYTE-OFFSET SOURCE PIN, which is the single most fragile shape in this file. The old
        test read `inspect.getsource(initialize_run)`, split the text on the literal
        `"run_dir = state_root"`, asserted `"enforce_draft_admission_gate"` appeared in the PREFIX, and
        then compared `.index("expand_selectors")` against `.index("enforce_draft_admission_gate")` -
        a claim about which substring appears EARLIER IN THE FILE. That breaks when unrelated lines move
        or when `ruff format` rewraps a call, it is satisfied by a comment mentioning either name in
        the right order, and it says nothing about what the gate actually SEES.

        Now the seam is observed on a REAL run, following the approach
        `tests/test_dirty_base_gate.py::test_the_report_is_ordered_between_the_preflight_refusals_and_queue_resolution`
        established for the analogous ordering claim rather than re-inventing one. THREE points, three
        measurements:

        * THE RECORDED CALL ORDER. All THREE collaborators are spied and the ORDER LOG is asserted to be
          exactly `["expand", "gate", "preflight"]`. This is the half a "what did the gate receive"
          assertion alone CANNOT make, MEASURED while writing this: a mutation that inserted an EXTRA
          gate call BEFORE `expand_selectors` (on the raw selector) and left the real call in place was
          NOT CAUGHT by the received-ids check, because the later real call still reported resolved ids.
          The order log catches it, because a second entry appears before `expand`.
        * AFTER RESOLUTION, in what it SEES: the ids handed to the gate are the RESOLVED selection
          (`drf001` and `rev003` from the `reviews` selector), not the raw selector string. Kept
          alongside the order log because the two fail for different reasons: a gate called in the right
          POSITION but handed `args.selectors` would satisfy the order and still be deciding about a
          string.
        * BEFORE DURABLE STATE: no `run-*` directory exists AT THE MOMENT the gate is called, so an
          exclusion leaves nothing for an operator to reconcile - the same guarantee the dependency
          preflight beside it provides, and it is asserted by LOOKING at the filesystem from inside the
          gate call, which a byte-offset scan cannot do at all.
        """
        import contextlib
        import io
        import tempfile
        from pathlib import Path as _P

        wrong = []
        real = runner_shared.enforce_draft_admission_gate

        def make_spy(repo, observed, order):
            # Every captured value is a PARAMETER, not a loop variable, so each host observes its own
            # repository and its own order log; a closure over the loop is the late-binding trap that
            # silently makes one host assert about another's run.
            def spy(manifest, ids, **kwargs):
                order.append("gate")
                runs = repo / ".aw" / "records" / "runs"
                # RECORDED PER CALL, in a list, so an EXTRA gate call is visible rather than being
                # overwritten by the last one's (correct) values.
                observed.setdefault("ids", []).append(sorted(ids))
                observed.setdefault("runs", []).append(
                    sorted(p.name for p in runs.glob("run-*")) if runs.exists() else []
                )
                return real(manifest, ids, **kwargs)

            return spy

        for runner in BOTH:
            observed: dict = {}
            order: list = []
            module = _MODULES[runner]

            with tempfile.TemporaryDirectory() as td:
                repo = self.make_repo(_P(td))
                args = _parse(runner, ["start", "reviews", "--repo", str(repo)])
                args.prepare_only = True
                with (
                    mock.patch.object(
                        runner_shared,
                        "enforce_draft_admission_gate",
                        make_spy(repo, observed, order),
                    ),
                    mock.patch.object(
                        module,
                        "expand_selectors",
                        _record(order, "expand", module.expand_selectors),
                    ),
                    mock.patch.object(
                        module,
                        "enforce_dependency_preflight",
                        _record(
                            order, "preflight", module.enforce_dependency_preflight
                        ),
                    ),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    module.initialize_run(args)

            if "ids" not in observed:
                wrong.append(
                    f"  {runner}: the gate was never called on a real `reviews` run, so no half "
                    "of the seam can be observed"
                )
                continue
            if order != ["expand", "gate", "preflight"]:
                wrong.append(
                    f"  {runner}: the recorded call order was {order!r}, expected "
                    "['expand', 'gate', 'preflight']. `gate` appearing BEFORE `expand` means the "
                    "gate decides about an unresolved selector; appearing AFTER `preflight` means "
                    "the dependency preflight already refused (or passed) on items the gate may yet "
                    "exclude; and appearing TWICE means one decision is taken twice, which for this "
                    "gate writes two ledger records and, interactively, prompts twice"
                )
            if observed["ids"] != [["drf001", "rev003"]]:
                wrong.append(
                    f"  {runner}: the gate received {observed['ids']} but the RESOLVED `reviews` "
                    "selection is ['drf001', 'rev003'], exactly once. It must run AFTER resolution, "
                    "because its whole job is to decide about the concrete items the selector "
                    "produced"
                )
            if any(observed["runs"]):
                wrong.append(
                    f"  {runner}: run director(ies) {observed['runs']} already existed when the gate "
                    "ran. Spec 2.5a puts the gate BEFORE any lease or session precisely so an "
                    "exclusion leaves no durable state to reconcile"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(BOTH)} host(s) place the draft gate at the wrong seam. The three "
            "halves fail for different reasons and need different fixes: a wrong ORDER LOG means the "
            "call site itself moved (or was duplicated); receiving a raw selector instead of resolved "
            "ids means the gate is in the right place but deciding about a string rather than about "
            "items; and an existing run directory means it moved too LATE and an exclusion now leaves "
            "a run directory, a report, and a ledger behind for work that never started. FIX: exactly "
            "ONE call, between `expand_selectors` and the dependency preflight, and before the "
            f"run-directory allocation.\n" + "\n".join(wrong),
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
        seam. What has changed (specsweep-01 `ui8b9b`) is WHY it does not fire on the run below.

        THIS TEST'S FIRST ASSERTION WAS INVERTED, ITS SECOND WAS NOT, and the split is the whole point
        of keeping it. It used to argue unreachability from TWO premises: that neither host registers
        `--type`, and that no non-mixed run reaches the combined entry point. `ui8b9b` falsified the
        first, so that assertion now requires the flag to BE registered. The second premise is
        untouched and is the invariant this test actually defends: a `--allow-drafts` run that is NOT
        mixed must not reach the combined gate. Deleting the test because one of its two assertions
        went stale would have discarded a live invariant, which is why it was inverted in place (the
        same treatment `test_a_live_invocation_CAN_now_produce_a_mixed_selection` received).

        SO THE CLAIM IS NARROWER THAN IT WAS AND STILL HONEST: the combined path is reachable in
        principle now that a selection can be mixed, and it is NOT reached by the single-type run this
        test performs.
        """
        from agent_workflows import run_selection_policy

        self.assertTrue(hasattr(run_selection_policy, "decide_selection_gates"))
        for runner in BOTH:
            for sub in ("start", "resume"):
                with self.subTest(runner=runner, subcommand=sub):
                    self.assertIn(
                        "--type",
                        _option_strings(runner, sub),
                        f"{runner}/{sub}: INVERTED by `ui8b9b`. While this read `assertNotIn`, it was "
                        "one of two premises for declaring spec 2.5a bullet 5 unreachable; the flag "
                        "now exists, so a mixed selection is possible and only the second premise "
                        "(this run is single-type) keeps the combined gate unfired below",
                    )

        # And nothing in either runner reaches the combined entry point ON A SINGLE-TYPE RUN, which is
        # the assertion this test keeps. NOTE WHAT THIS NO LONGER CLAIMS: it is not evidence that the
        # combined path is unreachable in general (it no longer is), only that a non-mixed run does not
        # take it. That narrowing is deliberate; asserting the broader claim would now be false.
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
                "the combined mixed-plus-draft gate FIRED on a SINGLE-TYPE run. Note what this no "
                "longer means: `--type` is registered (`ui8b9b`), so a mixed selection is reachable "
                "and the gate firing on a genuinely MIXED run would be correct. The run below passes "
                "only `--allow-drafts` with no `--type`, so its selection is IPD-only by the "
                "normative default and the combined path must not be taken. Firing here means the "
                "default widened, or a single-type selection is being classified as mixed"
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


class TypeScopedReviewSweepTests(unittest.TestCase):
    """specsweep-01 (`ui8b9b`): `--type` is OPERATOR-REACHABLE, and its default did not widen.

    WHAT THIS CLASS EXISTS FOR, since "a flag parses" is the least valuable thing in it. Spec `6m4kow`
    R-15 was satisfied at the FUNCTION boundary and by nothing an operator could type:
    `runner_shared.sweep_review_candidates_for_type(repo, "spec")` answered correctly while
    `grep '"--type"'` returned ZERO in both hosts, so the capability was complete and unreachable. That
    gap was documented at the function's own definition and excluded by name from executed plan
    `uyeko5`. These tests are the reachability, plus the three properties that make adding the flag
    SAFE rather than merely possible.

    THE LOAD-BEARING TEST IS THE ONE ABOUT THE DEFAULT, not the one about the flag.
    :meth:`test_a_bare_reviews_selection_is_byte_identical_to_the_ipd_only_sweep` is what proves spec
    2.4a property 1 ("with no `--type`, `reviews` selects IPDs only") did not move, and property 1 is
    NORMATIVE: a type added later must never join the sweep implicitly. A flag that works is worth
    nothing if registering it silently widened what every existing invocation selects.

    EVERY POSITIVE CASE USES A TEST-AUTHORED FIXTURE, NEVER THE LIVE TREE, and that is a measured
    decision rather than a convention. The live population of `to-review` specs changed THREE times in
    ten days: four specs when this plan was authored, ZERO at its review (the same review round
    advanced all four to `approved`), and one (`z7nbn1`) at execution. A test asserting any of those
    would have been wrong within hours, and the middle state would have made it pass VACUOUSLY against
    unchanged code. A fixture is also the only honest option: manufacturing a population by advancing a
    real spec's status would be a tooled lifecycle change made to satisfy a test.

    TABLE-DRIVEN OVER (case x HOST) for this file's standing reason: the property is that the TWO hosts
    agree, and `--full-auto` already shipped meaning opt-in on one host and opt-out on the other.
    """

    #: A spec at a given status, in the id6-carrying canonical name `discover_specs` requires.
    SPEC = """# Spec: probe {id6}

- Date: 2026-09-05
- Id: {id6}
- Status: {status}

## Summary

probe
"""

    PLAN = """# IPD: probe {id6}

- Date: 2026-09-05
- Kind: child
- Concern: probe.
- Scope: probe.
- Scope-Paths: src/
- Item-Dependencies: none
- Status: {status}
- Set: probe
- Order: {order}
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history
- 2026-09-05 {status} (test): probe.
"""

    def make_repo(self, root, *, plans=(), specs=()):
        """A committed repo holding `plans` and `specs` as ``[(id6, status)]`` pairs.

        SPECS ARE WRITTEN AS REAL FILES under `.aw/records/specs/` with canonical id6-carrying names,
        because `discover_specs` resolves identity through `check_engine._iter_spec_records` and
        `_ITEM_ID_RE` and deliberately SKIPS a spec with no `- Id:`. A fixture that faked the tree
        would not be swept at all and the test would pass for the wrong reason.
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
        for order, (id6, status) in enumerate(plans, start=1):
            (pending / f"20260905-probe-{order:02d}-{id6}-probe.ipd.md").write_text(
                self.PLAN.format(id6=id6, status=status, order=order), encoding="utf-8"
            )
        if specs:
            spec_dir = repo / ".aw" / "records" / "specs"
            spec_dir.mkdir(parents=True, exist_ok=True)
            for id6, status in specs:
                (spec_dir / f"20260905-{id6}-01-{id6}-probe.spec.md").write_text(
                    self.SPEC.format(id6=id6, status=status), encoding="utf-8"
                )
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
        return repo

    def sweep(self, runner, repo, argv):
        """`expand_selectors` through the HOST, with the type set resolved as `initialize_run` does.

        Driven through each host's own `expand_selectors` rather than the shared sweep directly,
        because the defect this plan closed was in the THREADING: the shared function already worked,
        and nothing passed it a type. A test calling the shared function would have passed before the
        change and proves nothing about reachability.
        """
        args = _parse(runner, ["start", *argv, "--repo", str(repo)])
        types = runner_shared.resolve_run_types(getattr(args, "types", None))
        manifest = runner_shared.build_dynamic_manifest(
            repo, _MODULES[runner].discover_plans(repo)
        )
        return _MODULES[runner].expand_selectors(
            manifest, args.selectors, repo=repo, types=types
        )

    def test_the_type_vocabulary_is_the_policy_modules_own(self):
        """`RUN_TYPE_CHOICES` must EQUAL spec 2.2's canonical order, tuple for tuple.

        THIS TEST IS WHY THE TUPLE MAY BE SPELLED OUT in `runner_shared`. That module's module-level
        first-party imports are pinned to exactly two (`test_no_new_module_level_first_party_import_in_
        runner_shared`), so it cannot read `run_selection_policy.SPEC_TYPE_ORDER` at module scope and
        the values are written literally. A literal copy is a second definition free to drift, so the
        tie is enforced HERE instead: the flag's vocabulary and the type system's vocabulary are the
        same list or this fails.

        ORDER IS ASSERTED, not just membership, because `resolve_run_types` sorts its output by this
        tuple to make two equivalent invocations freeze byte-identical run state, and
        `SPEC_TYPE_ORDER`'s own docstring records that its order is load-bearing for the preview.
        """
        from agent_workflows import run_selection_policy

        self.assertEqual(
            runner_shared.RUN_TYPE_CHOICES,
            run_selection_policy.SPEC_TYPE_ORDER,
            "`--type`'s accepted vocabulary must be spec 2.2's canonical type list, in its order. "
            "It is spelled literally in `runner_shared` only because that module's module-level "
            "first-party imports are pinned, so THIS assertion is the thing keeping the copy honest",
        )

    def test_the_sweepable_set_is_exactly_what_the_sweep_can_enumerate(self):
        """`RUN_TYPE_SWEEPABLE` must match the singular sweep's REAL behavior, both directions.

        The constant decides which types are REFUSED, so a drift either refuses a capability the
        package has (a type the sweep serves, absent here) or accepts one it lacks (a type here the
        sweep answers `[]` for, which is the silent-empty-success failure the refusal exists to
        prevent). Both directions are checked by DRIVING the sweep against a fixture that holds a
        review-eligible artifact of each type, rather than by trusting the constant.
        """
        import tempfile
        from pathlib import Path as _P

        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(
                _P(td), plans=[("pln001", "to-review")], specs=[("spc001", "to-review")]
            )
            manifest = runner_shared.build_dynamic_manifest(
                repo, oc_runipd.discover_plans(repo)
            )
            wrong = []
            for spec_type in runner_shared.RUN_TYPE_CHOICES:
                got = runner_shared.sweep_review_candidates_for_type(
                    repo, spec_type, manifest=manifest
                )
                declared = spec_type in runner_shared.RUN_TYPE_SWEEPABLE
                if declared and not got:
                    wrong.append(
                        f"  {spec_type}: declared SWEEPABLE but the sweep returned nothing for a "
                        "fixture holding a review-eligible artifact of this type\n"
                        "    this direction matters because: the flag would REFUSE a type the "
                        "package can actually serve, hiding a shipped capability behind a refusal"
                    )
                if not declared and got:
                    wrong.append(
                        f"  {spec_type}: NOT declared sweepable but the sweep returned {got}\n"
                        "    this direction matters because: the flag refuses this type, so a "
                        "capability that exists is unreachable - and if the refusal were removed "
                        "instead, the type would need a runnable queue entry it does not have"
                    )
            self.assertEqual(
                wrong,
                [],
                "`RUN_TYPE_SWEEPABLE` disagrees with `sweep_review_candidates_for_type`'s actual "
                "behavior. It must be derived from that function's real branches (`ipd` walks the "
                "manifest, `spec` walks the specs tree, everything else hits the fail-safe "
                "`return []`).\n" + "\n".join(wrong),
            )

    def test_a_bare_reviews_selection_is_byte_identical_to_the_ipd_only_sweep(self):
        """THE NORMATIVE DEFAULT DID NOT WIDEN (spec 2.4a property 1). The load-bearing test here.

        Asserted THREE ways over one fixture that deliberately holds a `to-review` SPEC alongside two
        `to-review` plans, because that fixture is the only one where widening is observable at all:

        1. a bare `reviews` equals `--type ipd` exactly, so the default IS the ipd sweep;
        2. both equal `sweep_review_candidates` - the pre-change function, unchanged and still shipped
           - so the delegation really is verbatim rather than merely similar; and
        3. the spec's id6 is ABSENT, which is what "IPDs only" means when a spec is present to be
           wrongly included.

        Without (3) this test would pass against a widened default whenever the fixture had no specs,
        which is exactly how a normative default rots unnoticed.
        """
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo = self.make_repo(
                    _P(td),
                    plans=[("pln001", "to-review"), ("pln002", "approved")],
                    specs=[("spc001", "to-review")],
                )
                manifest = runner_shared.build_dynamic_manifest(
                    repo, _MODULES[runner].discover_plans(repo)
                )
                bare = self.sweep(runner, repo, ["reviews"])
                explicit = self.sweep(runner, repo, ["reviews", "--type", "ipd"])
                legacy = runner_shared.sweep_review_candidates(manifest, repo=repo)
                self.assertEqual(
                    bare,
                    ["pln001"],
                    f"{runner}: a bare `reviews` must select the to-review PLAN only",
                )
                self.assertEqual(
                    bare,
                    explicit,
                    f"{runner}: a bare `reviews` and `--type ipd` must be the SAME selection; a "
                    "difference means the default is no longer the ipd sweep",
                )
                self.assertEqual(
                    bare,
                    legacy,
                    f"{runner}: the default must still be `sweep_review_candidates`'s own answer "
                    "VERBATIM. That function is unchanged and still shipped, so a difference here "
                    "means the type-scoped path reimplemented the IPD walk instead of delegating",
                )
                self.assertNotIn(
                    "spc001",
                    bare,
                    f"{runner}: the fixture holds a `to-review` SPEC and the default must NOT select "
                    "it. Spec 2.4a property 1 is normative: 'with no --type, reviews selects IPDs "
                    "only', and a type never joins the sweep implicitly",
                )

    def test_type_spec_selects_a_FIXTURE_spec_awaiting_review_on_both_hosts(self):
        """REACHABILITY: the capability spec `6m4kow` R-15 shipped, now reachable from a command line.

        THE FIXTURE IS THE POINT (see the class docstring): the live `to-review` spec population moved
        three times in ten days, so this asserts against a spec this test wrote. It also asserts the
        PLAN is absent, because `--type spec` selecting specs AND plans would be a union the operator
        did not ask for - and would silently make every spec sweep a mixed selection.
        """
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo = self.make_repo(
                    _P(td),
                    plans=[("pln001", "to-review")],
                    specs=[("spc001", "to-review"), ("spc002", "approved")],
                )
                got = self.sweep(runner, repo, ["reviews", "--type", "spec"])
                self.assertEqual(
                    got,
                    ["spc001"],
                    f"{runner}: `--type spec` must select the spec at `to-review` and nothing else. "
                    "`spc002` is `approved`, which the dispatch table routes to `plan` rather than "
                    "`review`, so including it would mean membership stopped being the table's",
                )
                self.assertNotIn(
                    "pln001",
                    got,
                    f"{runner}: `--type spec` must NOT also select the to-review PLAN. A union "
                    "nobody asked for would make every spec sweep a MIXED selection",
                )

    def test_repeating_the_flag_selects_the_union_in_canonical_type_order(self):
        """Spec 2.3 step 2: repetition is the UNION, deduplicated, in spec 2.2's type order."""
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo = self.make_repo(
                    _P(td),
                    plans=[("pln001", "to-review")],
                    specs=[("spc001", "to-review")],
                )
                self.assertEqual(
                    self.sweep(
                        runner,
                        repo,
                        ["reviews", "--type", "spec", "--type", "ipd"],
                    ),
                    ["pln001", "spc001"],
                    f"{runner}: the union must be ordered by spec 2.2's type order (ipd before "
                    "spec), NOT by the order the operator typed the flags. Run state freezes this "
                    "list, so two equivalent invocations must produce identical state",
                )
                self.assertEqual(
                    self.sweep(
                        runner,
                        repo,
                        ["reviews", "--type", "spec", "--type", "spec"],
                    ),
                    ["spc001"],
                    f"{runner}: a repeated SAME type must deduplicate. Without this, `--type spec "
                    "--type spec` would look like a two-type selection and trip the mixed-type gate",
                )

    def test_an_empty_type_scoped_sweep_is_a_SUCCESS_that_exits_zero(self):
        """Spec 2.4a property 3 holds for `--type spec` too: nothing awaiting review is HEALTHY.

        `EmptyStatusSelection` is the type that makes `main` exit 0 for a status selector while a
        misspelled id6 still exits 2, so this asserts BOTH the exception type at the seam and the
        real process exit code. A repository with no spec awaiting review is the normal state - it is
        the state the live tree was in at this plan's review - so getting an error for it would make
        the flag unusable in the common case.
        """
        import contextlib
        import io
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo = self.make_repo(
                    _P(td),
                    plans=[("pln001", "to-review")],
                    specs=[("spc001", "approved")],
                )
                with self.assertRaises(_MODULES[runner].EmptyStatusSelection):
                    self.sweep(runner, repo, ["reviews", "--type", "spec"])
                out, err = io.StringIO(), io.StringIO()
                with (
                    contextlib.redirect_stdout(out),
                    contextlib.redirect_stderr(err),
                ):
                    rc = _MODULES[runner].main(
                        [
                            "start",
                            "reviews",
                            "--type",
                            "spec",
                            "--repo",
                            str(repo),
                            "--prepare-only",
                        ]
                    )
                self.assertEqual(
                    rc,
                    0,
                    f"{runner}: an empty `--type spec` sweep must EXIT 0 (spec 2.4a property 3). "
                    f"Got {rc}. stderr: {err.getvalue()[-400:]}",
                )
                self.assertFalse(
                    (repo / ".aw" / "records" / "runs").exists(),
                    f"{runner}: an empty selection must create nothing durable",
                )

    def test_membership_is_not_reimplemented_for_either_type(self):
        """Both hosts reach the SAME shared sweep, and the sweep asks the SAME predicate.

        Asserted by DELEGATION rather than by grepping for a function name, following this file's own
        rule: `needs_review` is replaced with a sentinel that answers True for everything, and a
        `--type spec` sweep must then return the `approved` spec it otherwise skips. A second
        membership test inside the sweep would keep skipping it, because its own copy is untouched by
        the patch - so the sentinel's effect IS the proof there is one predicate.

        This is the property spec `6m4kow` R-16 requires and that `6ypimw` was written to restore: two
        verbatim `_needs_review` closures had drifted, one testing `status == "to-review"` while the
        dispatch table routed `draft` to review as well.
        """
        import tempfile
        from pathlib import Path as _P

        from agent_workflows import run_selection_policy

        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(_P(td), specs=[("spc001", "approved")])
            self.assertEqual(
                runner_shared.sweep_review_candidates_for_type(repo, "spec"),
                [],
                "an `approved` spec must not be swept; the dispatch table routes it to `plan`",
            )
            with mock.patch.object(
                run_selection_policy, "needs_review", lambda *a, **k: True
            ):
                for runner in BOTH:
                    with self.subTest(runner=runner):
                        self.assertEqual(
                            self.sweep(runner, repo, ["reviews", "--type", "spec"]),
                            ["spc001"],
                            f"{runner}: patching `run_selection_policy.needs_review` must change "
                            "this host's selection. An unchanged answer means the sweep carries its "
                            "own membership test, which is the fork `6ypimw` deleted",
                        )

    def test_both_hosts_reach_the_SAME_shared_sweep_function(self):
        """One function object, two hosts: the `rununify` property for this seam."""
        self.assertIs(
            oc_runipd.runner_shared.sweep_review_candidates_for_types,
            agy_runipd.runner_shared.sweep_review_candidates_for_types,
        )

    #: (case, argv tail, the substring the refusal must contain, why an operator needs that substring)
    REFUSALS = (
        (
            "a type the sweep cannot enumerate",
            ["reviews", "--type", "research"],
            "can enumerate only",
            "spec 2.1 DECLARES seven types and two are served, so the grammar is deliberately wider "
            "than the implementation (the `--action` precedent). Accepting `research` would report a "
            "successful EMPTY selection, which tells the operator their sweep found nothing when it "
            "never looked - the exact falsehood `refuse_unimplemented_run_flags` exists to prevent",
        ),
        (
            "a type on the `all` selector",
            ["all", "--type", "spec"],
            "not honored by this selector",
            "THE ASYMMETRY IS THE HAZARD. `--type spec` genuinely works on `reviews`, so an operator "
            "has every reason to believe it worked on `all` too; `all` resolves against the "
            "plans-only manifest, so ignoring it silently would hand them an IPD-only run they "
            "believe was type-scoped",
        ),
        (
            "a type on a NAMED selector",
            ["pln001", "--type", "spec"],
            "not honored by this selector",
            "the same asymmetry reached the other way. A named selector resolves through the "
            "manifest too, and this row exists because a refusal scoped only to `all` would leave "
            "the commonest spelling (naming an item) silently ignoring the flag",
        ),
        (
            "a spec that was SELECTED but cannot be RUN",
            ["reviews", "--type", "spec"],
            "cannot be RUN",
            "THE HONEST LIMIT, enforced rather than documented. A queue entry is plan-shaped, so "
            "queueing a spec would hand it to code that assumes a plan - and because "
            "`resolve_plan_path` fails OPEN, that failure would be SILENT. The refusal is what stops "
            "an operator reading type-scoped SELECTION as shipped per-type EXECUTION",
        ),
    )

    def test_every_illegal_or_unrunnable_type_use_is_REFUSED_and_says_why(self):
        """Every refusal, on both hosts, each asserting it left NOTHING DURABLE behind.

        THE `nothing durable` HALF IS NOT DECORATION. Every one of these refusals is sited ahead of
        the run directory precisely so a refused invocation costs an operator no reconciliation, which
        is the same property the mixed-type refusal's "No work started." sentence promises. A refusal
        that fired after the run directory existed would leave a run, a report and a ledger for zero
        work, and no assertion about the message would notice.
        """
        import contextlib
        import io
        import tempfile
        from pathlib import Path as _P

        wrong = []
        for case, tail, needle, why in self.REFUSALS:
            for runner in BOTH:
                with tempfile.TemporaryDirectory() as td:
                    repo = self.make_repo(
                        _P(td),
                        plans=[("pln001", "to-review")],
                        specs=[("spc001", "to-review")],
                    )
                    problems = []
                    err = io.StringIO()
                    try:
                        with contextlib.redirect_stderr(err):
                            args = _parse(runner, ["start", *tail, "--repo", str(repo)])
                            args.prepare_only = True
                            _MODULES[runner].initialize_run(args)
                    except runner_shared.RunFlagRefusal as exc:
                        if needle not in str(exc):
                            problems.append(
                                f"the refusal does not contain {needle!r}: {str(exc)[:300]!r}"
                            )
                    except Exception as exc:  # noqa: BLE001 - any other error is itself the finding
                        problems.append(
                            f"expected a RunFlagRefusal, got {type(exc).__name__}: "
                            f"{str(exc)[:200]}"
                        )
                    else:
                        problems.append(
                            "the invocation was ACCEPTED; no refusal was raised"
                        )
                    if (repo / ".aw" / "records" / "runs").exists():
                        problems.append(
                            "a run directory was created, so the refusal fired AFTER durable state "
                            "existed and an operator is left with a run to reconcile"
                        )
                    if problems:
                        wrong.append(
                            f"  {case} on {runner} ({' '.join(tail)}):\n"
                            + "".join(f"    - {p}\n" for p in problems)
                            + f"    this row exists because: {why}"
                        )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.REFUSALS) * len(BOTH)} (refusal, host) cells are wrong. READ "
            "THE SHAPE: a row failing on BOTH hosts is a missing or mis-sited refusal in the shared "
            "core; a row failing on ONE host means a host bypassed the shared seam, which is the "
            "asymmetry this file exists to catch. A `nothing durable` failure alongside a correct "
            "message means the refusal is real but sited too late.\n"
            + "\n".join(wrong),
        )

    def test_the_unrunnable_refusal_names_what_it_selected(self):
        """The refusal must report the SELECTION, not merely decline.

        This is the whole operator value of a flag that selects but cannot run: the sweep's answer is
        the thing they wanted, so a refusal that withholds it converts a working capability into a
        dead end. Asserted separately from the message-substring table above because it is a claim
        about CONTENT (the resolved artifact) rather than about wording.
        """
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo = self.make_repo(_P(td), specs=[("spc001", "to-review")])
                args = _parse(
                    runner, ["start", "reviews", "--type", "spec", "--repo", str(repo)]
                )
                args.prepare_only = True
                with self.assertRaises(runner_shared.RunFlagRefusal) as ctx:
                    _MODULES[runner].initialize_run(args)
                self.assertIn(
                    "spc001",
                    str(ctx.exception),
                    f"{runner}: the refusal must NAME the spec it selected. The selection is the "
                    "capability this flag delivers, so withholding it makes the refusal a dead end "
                    "instead of a usable answer an operator can act on",
                )

    def test_the_mixed_type_gate_REFUSES_a_real_invocation_and_proceeds_with_allow_mixed(
        self,
    ):
        """E-04: the gate fires on a REAL command line, which nobody could produce before.

        `uyeko5` proved this gate WIRED and CORRECT on a constructed classification while stating
        plainly that no live invocation could trigger it. This test is the evidence that was
        unobtainable then: `--type ipd --type spec` against a fixture holding a review-eligible item
        of each type.

        `gate_applied` IS NOT ASSERTED HERE and that is deliberate, not an omission: the unattended
        refusal path raises, so there is no verdict object to read. The `gate_applied=True` assertion
        lives on the `--allow-mixed` half below, which returns a verdict, and
        `MixedTypeGateWiringTests` asserts it at the seam. What THIS test adds is that a REAL argv
        reaches the gate at all.

        THE `--allow-mixed` HALF THEN HITS THE UNRUNNABLE-TYPE REFUSAL, and that ordering is the
        design (DECISION D4): the mixed gate asks about the operator's INTENT and this refusal states
        the runner's CAPABILITY, so the intent question must come first. Reaching the SECOND refusal
        is therefore the proof the FIRST one was satisfied rather than skipped.
        """
        import contextlib
        import io
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo = self.make_repo(
                    _P(td),
                    plans=[("pln001", "to-review")],
                    specs=[("spc001", "to-review")],
                )
                argv = [
                    "start",
                    "reviews",
                    "--type",
                    "ipd",
                    "--type",
                    "spec",
                    "--repo",
                    str(repo),
                    "--unattended",
                ]
                args = _parse(runner, argv)
                args.prepare_only = True
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    with self.assertRaises(runner_shared.DriverError) as ctx:
                        _MODULES[runner].initialize_run(args)
                self.assertIn(
                    "[RUN-MIXED-TYPES]",
                    str(ctx.exception),
                    f"{runner}: a real multi-type invocation must hit the spec's mixed-type refusal. "
                    "Before `--type` existed no argv could produce a mixed selection, so this "
                    "refusal was unreachable shipped code",
                )
                self.assertIn("No work started.", str(ctx.exception))
                self.assertFalse(
                    (repo / ".aw" / "records" / "runs").exists(),
                    f"{runner}: the mixed-type refusal must leave nothing durable",
                )

                args = _parse(runner, [*argv, "--allow-mixed"])
                args.prepare_only = True
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    with self.assertRaises(runner_shared.RunFlagRefusal) as ctx2:
                        _MODULES[runner].initialize_run(args)
                message = str(ctx2.exception)
                self.assertNotIn(
                    "[RUN-MIXED-TYPES]",
                    message,
                    f"{runner}: `--allow-mixed` must SATISFY the mixed-type gate. Still seeing its "
                    "refusal means the flag did not reach the gate",
                )
                self.assertIn(
                    "cannot be RUN",
                    message,
                    f"{runner}: past the mixed gate, the selection must meet the unrunnable-type "
                    "refusal. Reaching THIS refusal is the proof the mixed gate was satisfied "
                    "rather than skipped, and it is where the honest limit is stated",
                )

    def test_the_gate_reports_gate_applied_TRUE_on_the_real_multi_type_path_set(self):
        """`gate_applied=True` on the path set a REAL invocation produces, not a constructed one.

        `gate_applied=False` is the SINGLE-TYPE short circuit and is what a still-unreachable gate
        would also return, so it cannot satisfy this. The path set here is built by the same
        `resolve_selected_artifact_paths` the runner uses, which is the seam that would break the gate
        most plausibly: a resolver that filtered non-plan paths out would hand the gate one type and
        the verdict would read `gate_applied=False` while every other test in this class still passed.
        """
        import tempfile
        from pathlib import Path as _P

        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(
                _P(td),
                plans=[("pln001", "to-review")],
                specs=[("spc001", "to-review")],
            )
            manifest = runner_shared.build_dynamic_manifest(
                repo, oc_runipd.discover_plans(repo)
            )
            types = ("ipd", "spec")
            queue = runner_shared.sweep_review_candidates_for_types(
                repo, types, manifest=manifest
            )
            selection = runner_shared.resolve_selected_artifact_paths(
                repo, manifest, queue, types
            )
            self.assertEqual(
                len(selection.all_paths),
                2,
                f"the resolver must place BOTH artifacts; got {selection.all_paths} with "
                f"unresolved={selection.unresolved}",
            )
            self.assertEqual(
                len(selection.plan_paths),
                1,
                "the PLAN subset must hold the plan only: the dependency preflight hands each path's "
                "text to the IPD dependency evaluator, which can say nothing true about a spec",
            )
            verdict = runner_shared.enforce_mixed_type_gate(
                repo,
                list(selection.all_paths),
                allow_mixed=True,
                interactive=False,
                host="oc",
                selector="reviews",
            )
            self.assertTrue(verdict.proceed)
            self.assertTrue(
                verdict.gate_applied,
                "gate_applied=False is the single-type short circuit and would also be returned by "
                "a still-dead gate; on a genuinely mixed selection it must be True",
            )
            self.assertEqual(verdict.record.response_or_flag, "--allow-mixed")

    def test_the_effective_type_set_is_FROZEN_into_run_state(self):
        """E-03: run state records the EFFECTIVE type set, so a resume cannot re-derive it differently.

        The default freezes as `["ipd"]` rather than `null`, for the reason `--retry-budget` freezes
        its resolved integer: a bare `None` in durable state forces every later reader to re-resolve
        it, and to re-resolve it differently. It also makes the run's own record able to say what it
        selected, which a `null` cannot.
        """
        import contextlib
        import io
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo = self.make_repo(_P(td), plans=[("pln001", "to-review")])
                args = _parse(runner, ["start", "reviews", "--repo", str(repo)])
                args.prepare_only = True
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    run_dir = _MODULES[runner].initialize_run(args)
                state = runner_shared.load_state(run_dir)
                self.assertEqual(
                    state["options"]["types"],
                    ["ipd"],
                    f"{runner}: a bare invocation must freeze the EFFECTIVE default type set, not "
                    "null. A null would leave the run unable to report what it selected and would "
                    "force every reader to re-resolve the default for itself",
                )

    def test_resume_REFUSES_a_different_type_rather_than_re_scoping_the_queue(self):
        """E-03's pinned rule: `--type` is REFUSED on resume (spec `:129`/`:131`), never overwritten.

        WHY REFUSE RATHER THAN COPY `--full-auto`, which OVERWRITES its frozen value: `--type` is not
        a policy a resume could re-apply, it IS THE SELECTION, and the queue is already frozen. An
        accepted `--type` could therefore not re-scope the queue; it could only write a frozen option
        CONTRADICTING the queue the run holds, leaving run state asserting a selection that never
        happened. Spec `:129` names exactly this case ("flags that would change the frozen queue"), so
        unlike `--full-auto` there is no `:129`-versus-`:131` tension to inherit. `uyeko5` recorded
        that divergence and warned against copying a neighbour blindly; this is the explicit decision.

        BOTH HALVES ARE ASSERTED, because the refusal alone is satisfiable by a flag nobody can use:
        an OMITTED `--type` must leave the frozen value untouched.
        """
        import contextlib
        import io
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo = self.make_repo(_P(td), plans=[("pln001", "to-review")])
                args = _parse(runner, ["start", "reviews", "--repo", str(repo)])
                args.prepare_only = True
                with contextlib.redirect_stderr(io.StringIO()):
                    run_dir = _MODULES[runner].initialize_run(args)

                passed = _parse(
                    runner,
                    ["resume", run_dir.name, "--repo", str(repo), "--type", "spec"],
                )
                with self.assertRaises(runner_shared.RunFlagRefusal) as ctx:
                    runner_shared.refuse_frozen_flags_on_resume(passed)
                self.assertIn("--type", str(ctx.exception))
                self.assertIn("cannot be changed on --resume", str(ctx.exception))

                out, err = io.StringIO(), io.StringIO()
                with (
                    contextlib.redirect_stdout(out),
                    contextlib.redirect_stderr(err),
                ):
                    rc = _MODULES[runner].main(
                        ["resume", run_dir.name, "--repo", str(repo), "--type", "spec"]
                    )
                self.assertEqual(
                    rc,
                    2,
                    f"{runner}: a resume passing `--type` must FAIL rather than re-scope the queue",
                )

                omitted = _parse(runner, ["resume", run_dir.name, "--repo", str(repo)])
                state = {"options": {"types": ["ipd"]}}
                self.assertFalse(
                    runner_shared.apply_run_policy_flags_on_resume(state, omitted),
                    f"{runner}: an OMITTED `--type` must change nothing",
                )
                self.assertEqual(
                    state["options"]["types"],
                    ["ipd"],
                    f"{runner}: the frozen type set must survive a resume that does not name it. "
                    "Without `default=None` on the resume parser, silence and an explicit value are "
                    "indistinguishable and every resume clobbers frozen policy",
                )
