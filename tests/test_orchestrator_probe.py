"""orchprobe Order 03 (`m7gvuz`): the pre-run orchestrator coverage probe and its gate.

WHAT THIS PINS, and why each half exists rather than merely that it does.

E-01/E-02, THE PROMPT AND A PARSER THAT FAILS CLOSED. The probe answers with one of exactly two
sentinel strings, held as named constants so the prompt and the parser cannot drift; a prompt asking
for one spelling while the parser accepts another would turn every answer into `unknown` and block
every run. The parser accepts ONLY those two exact strings: a chatty reply, a refusal, and a reply
carrying both sentinels are each `unknown`, which BLOCKS, because a permissive parser here would
convert a confused model into a silent pass, which is the one outcome this gate exists to prevent.

THE FOUR-STATE ANSWER IS THE MAINTAINER'S OQ-02 RULING, not defensive elaboration, and the split is
the load-bearing part. A COULD-NOT-ASK (unreachable host, missing binary, timeout, empty reply) is
NOT evidence about the orchestrator, so it is retried to the run's `--retry-budget` and then WARNED
PAST; an `unknown` is an answer the host DELIVERED and cannot be used, so it blocks. A tri-state
cannot express that, which is why `TheCouldNotAskPathDoesNotBlock` and `TheParserFailsClosed` are
separate classes: collapsing the two states is the specific regression they exist to catch.

E-03, A BOUNDED PAYLOAD THAT IS THE CACHE KEY'S OWN INPUTS. The excerpt is rendered FROM
`probe_cache_payload`, so payload and key are the same two things BY CONSTRUCTION. That identity is a
requirement and not a tidiness: if the probe reasoned over something the digest did not cover, editing
that thing would serve a STALE verdict under apparent authority. `TheExcerptIsTheCacheKeysOwnInputs`
asserts the identity, and `TheExcerptHasAKnownLIMIT` states the price that identity has, so the limit
is visible in the suite rather than discovered later by someone debugging a missed instance.

E-04, QUEUE-SCOPED AND CACHE-FIRST. `aw oc run all` must not sweep the corpus, and an unmodified
orchestrator must cost nothing. `TheProbeIsQueueScoped` and `TheCacheIsConsultedFirst` pin both,
counting ACTUAL calls through an injected double rather than trusting that a cache was used.

E-05/E-06, THE GATE AND ITS VOICE. Three paths: prompt on a TTY, FAIL without one, and an override
that RECORDS ITS JUSTIFICATION. The refusal must be DURABLE (readable from run state after the process
exits, which is what child 01's record buys) and must name the CONSTRUCTIVE action, because `AGENTS.md`
records that a prohibition-only message gets complied with by DELETION of the very checklist that makes
`execute <setid>` complete. `TheRefusalNamesAddAChild` asserts the wording, not merely that a string
exists.

E-09, BOTH HOSTS ACTUALLY GATE. `pgq326`'s lesson was an agy runner that DECIDED an orchestrator
action while having no dispatch branch that read it, so `BothHostsShareOneDefinition` asserts object
IDENTITY per symbol and `BothHostsActuallyRefuse` drives the REAL `initialize_run` on both hosts over
the same fixture. The host-parameterized remedy is the measured carve-out: the composing FUNCTION is
one object, while the rendered strings differ because each names its own host's command.

NO TEST SPENDS A TOKEN, AND THAT IS ASSERTED BY CONSTRUCTION RATHER THAN HOPED FOR.
`runner_shared._assert_probe_spawn_is_permitted` RAISES whenever a real spawn is attempted under
pytest, so a future test that forgets its double fails loudly instead of quietly billing a model;
`TheSuiteCannotSpendTokens` pins that guard itself.

FIXTURES ARE FROZEN, DELIBERATELY. Every orchestrator text below is built in this module. The live
corpus WAS re-classified at execution to derive these shapes (recorded as pasted evidence in the IPD),
but pinning to live plan files is what broke `test_orchestrator_retirement.py::RealRepositorySets`, and
this Set's own orchestrator forbids repeating it.

MOST OF THIS FILE IS NOW TABLE-DRIVEN, because most of it was one shape repeated: hand the subject one
input, assert one field of one answer. The tables group by SUBJECT (the prompt, the answer vocabulary,
the payload/digest pair, the queue scope, the cache, the gate's decision, the refusal's wording, both
hosts) rather than by which E-item of the plan asked for the case, which is provenance and not a
property of the subject.

EVERY DISTINCT VERDICT KEEPS ITS OWN ROW, AND THAT IS THE ONE RULE THIS FILE'S TABLES MAY NOT BEND.
This is a fail-closed gate, so "it refused" is not an assertion worth making: a gate that refused for
the WRONG reason, or that recorded the wrong refusal CODE, is broken in the way that matters, since an
operator acts on the code and the remedy rather than on the exit status. So the four answers
(`no-executions`, `executions`, `unknown`, `could-not-ask`), the two refusal codes
(`orchestrator-uncovered-work`, `orchestrator-probe-unavailable`), and the three admission paths
(unattended refusal, interactive phrase, justified override) each occupy their own row asserting the
SPECIFIC outcome reported: which code was recorded, whether the run proceeded, whether it was warned
past, how many model calls it cost, and what the recorded justification says. Never a bare "it
blocked".

MODES ARE COLUMNS, NOT CLASSES. The HOST (`oc` versus `agy`), the cache's prior STATE, the retry
BUDGET, the interactive/unattended distinction, and the answer the double returns are all columns. In
every case the property worth stating is that the SAME subject gets a different answer in a different
mode, which no single-mode test can express.

Tests that are NOT rows carry a one-line docstring saying why they stay separate. The recurring
reasons: the claim is `assertRaises` over a typed exception rather than a returned value; the subject
is the module's own STRUCTURE (an AST walk over a host driver, a symbol-identity sweep) rather than any
fixture; the setup is materially different (a real `git init` repository driven through the REAL
`initialize_run` on both hosts); or the assertion is a before/after PAIR whose content is that the
answer does NOT change.
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from agent_workflows import agy_runipd, oc_runipd
from agent_workflows import render_stream
from agent_workflows import runner_shared as rs

BOTH_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))


# ==================================================================================================
# FROZEN FIXTURES, derived by re-classifying the live corpus at execution and then copied here.
# ==================================================================================================
#
# THE TWO SHAPES THAT MATTER ARE BOTH REPRESENTED, and the second one is why this child exists.
#
#   ORCHESTRATION ONLY (must NOT be flagged): sequencing the children, reading each child's status on
#   disk, stopping on the first that is not `executed`, refusing to do a child's work. Measured over
#   the live corpus, EVERY orchestrator carries items and most carry only this, so a probe that flagged
#   it would fire on all of them and the operator would learn to reach for the override.
#
#   PARENT-ONLY WORK (must BE flagged): a deliverable, a baseline established before any child runs, a
#   whole-Set verification or record reconciliation afterwards. It is stated in ORDINARY PROSE inside
#   an item's action text, which is exactly why no pattern match can separate it from the shape above:
#   both are "an E-item on an orchestrator".

_HEAD = """\
# IPD: {title}

- Date: 2026-09-19
- Kind: orchestrator
- Concern: frozen fixture for the coverage probe.
- Scope: synthetic.
- Scope-Paths: none
- Status: approved
- Set: {setid}
- Order: 0
- Highest E allocated: 0{n}
- Id: {id6}

## Workflow history

- 2026-09-19 draft (fixture): created.

## Goal

{goal}

## Detailed Implementation Checklist (TODO)

{items}
## Child IPDs, sequence, and dependencies

| Order | Id | Child plan | Depends on |
| --- | --- | --- | --- |
| 01 | {child} | the child that does the work | none |

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: paste the children's statuses.
  - Observed evidence:
  - Result: pending
"""

#: ORCHESTRATION ONLY. Copied in shape from the live `d0cbt3`/`y9s4vm`/`lyo1tz` orchestrators, whose
#: items sequence children and read their statuses on disk and nothing else.
ORCHESTRATION_ONLY = _HEAD.format(
    title="orchestration only",
    setid="orchonly",
    n=1,
    id6="orc001",
    child="aaa111",
    goal="Sequence the Set. This parent holds coordination and nothing beyond it.",
    items=(
        # TYPED ROW, prose on the continuation lines (updated 2026-09-24, same reason as
        # PARENT_ONLY_WORK below): `68uhp0` sited `enforce_orchestrator_shape_gate` AHEAD of the
        # probe, so a prose action text is refused by IPD-S407 before the probe is reached. This
        # fixture is the CLEAN control - it must let the run actually START - so its row has to
        # satisfy the shape gate or the control becomes vacuous and every refusal row beside it is
        # satisfied by a host that simply refuses everything.
        # THE LINE WRAP HERE IS LOAD-BEARING, do not reflow it casually: the cache-cost table below
        # mutates the exact substring "does not. DO NOT PERFORM ANY CHILD'S WORK FROM HERE" to prove
        # that editing a CONTINUATION line changes the digest and costs exactly one model call. If
        # that phrase is split across two of these string literals the replace silently matches
        # nothing, the mutated fixture is byte-identical to the original, and the test fails claiming
        # the gate spent 0 calls.
        "- [ ] E-01 CONFIRM aaa111 REACHED executed\n"
        "  Hold each child until its predecessor reads `- Status: executed` ON DISK rather than\n"
        "  trusting this table, and STOP on the first that\n"
        "  does not. DO NOT PERFORM ANY CHILD'S WORK FROM HERE: if a child appears to need a change\n"
        "  this parent could make, the child table is wrong, so fix the child.\n"
        "  - Depends on: none\n"
        "  - Expected outcome: every child executed, in order.\n"
        "  - Execution state: pending\n"
    ),
)

#: PARENT-ONLY WORK, stated in prose inside the item's action text. Copied in shape from the live
#: `5e4sb6` E-01/E-02 (a research deliverable, and a baseline established BEFORE any child runs) and
#: `wfjsp4` E-02/`a5wdne` E-01 (a whole-Set verification afterwards), which are the corpus's clearest
#: instances of the hazard.
PARENT_ONLY_WORK = _HEAD.format(
    title="parent-only work",
    setid="parentwork",
    n=2,
    id6="orc002",
    child="bbb222",
    goal="Unify the thing, having first measured it.",
    items=(
        # E-01 IS A TYPED CHILD-TRACKING ROW ON PURPOSE (updated 2026-09-24). `orchtyped` Order 04
        # (`68uhp0`, commit `70678847`) landed the IPD-S407 grammar, which refuses a prose
        # orchestrator row BEFORE `initialize_run` ever reaches the probe. This fixture's SUBJECT is
        # E-02 (parent-only work stated in prose), so E-01 must be a CONFORMING row or the shape
        # check short-circuits the very scenario this fixture exists to exercise, and the probe is
        # never asked at all. Keeping the prose spelling here would test S407, not the probe.
        "- [ ] E-01 CONFIRM bbb222 REACHED executed\n"
        "  Hold each child until its predecessor reads `- Status: executed` ON DISK.\n"
        "  - Depends on: none\n"
        "  - Expected outcome: every child executed, in order.\n"
        "  - Execution state: pending\n"
        "\n"
        # E-02 CARRIES THE PARENT-ONLY WORK IN ITS CONTINUATION PROSE WHILE ITS ROW IS TYPED, and
        # that combination is the whole point of this fixture (updated 2026-09-24).
        #
        # WHY IT CHANGED. `68uhp0` sited `enforce_orchestrator_shape_gate` DELIBERATELY AHEAD of the
        # probe ("ordered AHEAD of the semantic probe ... Refusing here spends zero model calls
        # because the probe is never reached"). So a row whose ACTION TEXT is prose is refused by
        # S407 and never reaches the probe at all. The previous spelling therefore made this fixture
        # exercise the shape gate instead of the probe, which is a different check with its own
        # suites (`test_orchestrator_shape_gate.py`, `test_orchestrator_shape_composed.py`).
        #
        # WHY THIS STILL TESTS WHAT IT CLAIMS. S407 constrains the ROW GRAMMAR only; it is measured
        # conforming with this text. The uncovered work - establishing a baseline before any child
        # runs, producing a research artifact - now lives in the continuation lines, where only a
        # SEMANTIC reader can find it. That is exactly the hazard the probe exists to catch and the
        # shape gate cannot: a parent that looks structurally correct and still carries work no child
        # covers. The fixture is consequently STRONGER than before, because it can no longer pass by
        # tripping a deterministic grammar check.
        "- [ ] E-02 CONFIRM bbb222 REACHED executed\n"
        "  Establish the CHARACTERIZATION BASELINE that makes this Set's behavior-preservation claim\n"
        "  falsifiable, BEFORE any child reconciles anything. Write the missing characterization\n"
        "  tests against the current behavior and record the measured coverage, then produce the\n"
        "  inventory as a durable research artifact. Afterwards, once the children have executed,\n"
        "  run the repo-wide suite and the leak sanitization and reconcile the records this Set\n"
        "  closes.\n"
        "  - Depends on: E-01\n"
        "  - Expected outcome: a baseline nobody else establishes.\n"
        "  - Execution state: pending\n"
    ),
)


def _reply(text: str):
    """A `runner` double returning `text` as one opencode-shaped text event, exit 0."""

    payload = json.dumps({"type": "text", "part": {"text": text}})

    def runner(argv, cwd, timeout):
        return 0, payload + "\n", ""

    return runner


def _transport_failure(exit_code: int = 127, stderr: str = "opencode: not found"):
    """A `runner` double that never delivers an answer (the COULD-NOT-ASK shape)."""

    def runner(argv, cwd, timeout):
        return exit_code, "", stderr

    return runner


def _raises(exc: BaseException):
    """A `runner` double that RAISES rather than returning, so the ask's except path is driven."""

    def runner(argv, cwd, timeout):
        raise exc

    return runner


def _counting_asker(answer: str):
    """An `asker` double returning `answer`, recording one entry per call in `.calls`."""

    calls: list = []

    def asker(state, excerpt, *, host, repo, runner=None):
        calls.append(excerpt)
        return answer, "double"

    asker.calls = calls  # type: ignore[attr-defined]
    return asker


class ProbeCase(unittest.TestCase):
    """A temp repo, a run directory, and a frozen state shaped exactly as the runners write one."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.repo = self.root / "repo"
        (self.repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        (self.repo / ".git").mkdir()
        self.run_dir = self.root / "run"
        self.run_dir.mkdir()

    def write_plan(self, name: str, text: str) -> str:
        rel = f".aw/records/plans/pending/{name}"
        (self.repo / rel).write_text(text, encoding="utf-8")
        return rel

    def state(self, items: list[dict]) -> dict:
        return {
            "run_id": "run-fixture",
            "repo": str(self.repo),
            "queue": items,
            "options": {"opencode": "opencode", "model": "test/model"},
        }

    def item(
        self, id6: str, rel: str, *, kind: str = "orchestrator", position: int = 1
    ) -> dict:
        return {
            "position": position,
            "id6": id6,
            "setid": "fixture",
            "configured_file": rel,
            "kind": kind,
            "status": "queued",
            "attempts": [],
        }

    def gate(self, state: dict, **kwargs):
        """Run the real gate with output captured, never a real spawn."""
        kwargs.setdefault("repo", self.repo)
        kwargs.setdefault("host", "oc")
        kwargs.setdefault("interactive", False)
        kwargs.setdefault("write_report_fn", lambda rd, st: None)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            decision = rs.enforce_orchestrator_probe_gate(self.run_dir, state, **kwargs)
        return decision, err.getvalue()

    def events(self) -> list[dict]:
        path = self.run_dir / "events.jsonl"
        if not path.is_file():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


# ==================================================================================================
# E-01 / V-01: the prompt
# ==================================================================================================


class ThePromptIsBiasedTowardSuspicion(unittest.TestCase):
    """E-01. Every instruction the rendered prompt must actually carry.

    ONE table replaces four tests (`says_a_child_checklist_is_EXPECTED`,
    `instructs_that_DOUBT_resolves`, `names_prose_as_counting`, and the containment half of
    `the_prompt_and_the_parser_share_the_sentinel_objects`). Each rendered the prompt for a throwaway
    excerpt and asserted one substring, so they differed only in WHICH instruction they looked for.

    Why the table beats the four: this prompt is ONE composed string from ONE template, so the
    realistic regression is a rewrite that drops or rephrases SEVERAL instructions at once while the
    prompt still looks reasonable to a human reading it. Four tests report that as four unrelated
    `'x' not found in '...'` lines, each dumping the whole multi-paragraph prompt into the failure
    output with no hint they share a cause; the table reports one failure listing exactly which
    instructions went missing. It also makes the prompt's CONTRACT browsable as a list, so the next
    person rewording it can see what may not be lost.

    EACH ROW SAYS WHAT BREAKS IF ITS NEEDLE IS GONE, and the two directions are not symmetric. Losing
    the "a child checklist is EXPECTED" half makes the probe fire on EVERY orchestrator in the corpus
    (measured: every one carries items), which teaches the operator to reach for the override; losing
    the "doubt resolves to CONTAINS EXECUTIONS" half makes it fire on NONE, which is the silent
    failure this whole gate exists to prevent. The failure message says so rather than leaving a
    reader to work out which side they are on.

    THE TWO SENTINELS ARE ROWS TOO, but their identity claim is not a substring check and stays in
    `test_the_prompt_and_the_parser_agree_on_the_same_sentinel_OBJECTS` below.
    """

    #: (case, the substring the rendered prompt MUST contain, whether to fold case before looking,
    #: why this row exists)
    #:
    #: THE NEEDLES ARE LITERAL STRINGS AND THE SENTINEL ROWS REFERENCE THE CONSTANTS, deliberately
    #: and for opposite reasons. An INSTRUCTION is prose whose exact words are the contract with the
    #: model, so a literal is right. A SENTINEL must be the same OBJECT the parser compares against,
    #: so a literal would let the two drift apart while this table stayed green.
    INSTRUCTIONS = (
        (
            "the CONTAINS EXECUTIONS sentinel",
            rs.PROBE_SENTINEL_EXECUTIONS,
            False,
            "the prompt must name the exact string it wants back. A prompt asking for a spelling the "
            "parser does not accept turns every answer into `unknown`, which BLOCKS EVERY RUN rather "
            "than failing visibly",
        ),
        (
            "the CONTAINS NO EXECUTIONS sentinel",
            rs.PROBE_SENTINEL_NO_EXECUTIONS,
            False,
            "the clean answer's spelling, for the same reason. Both sentinels reach the prompt from "
            "the same constants the parser compares against, which is what makes drift impossible "
            "rather than merely unlikely",
        ),
        (
            "a child checklist is EXPECTED",
            "EXPECTED",
            False,
            "THE FALSE-POSITIVE SIDE, and it is the half that keeps the probe usable at all. Measured "
            "over the live corpus EVERY orchestrator carries items and most carry only sequencing, so "
            "a prompt that misread sequencing as work would fire on all of them and the operator "
            "would learn to reach for the override reflexively",
        ),
        (
            "the word `orchestration` names the legitimate shape",
            "orchestration",
            True,
            "naming the legitimate activity is what lets the model separate it from work; case is "
            "folded because this is prose about a concept rather than a token anything consumes "
            "verbatim",
        ),
        (
            "sequencing is NOT an execution",
            "NOT an execution",
            False,
            "the EXPLICIT negative. Saying a checklist is expected leaves open whether it still "
            "counts; this sentence closes that, and it is the sentence a reworded prompt is most "
            "likely to drop as redundant",
        ),
        (
            "doubt resolves to CONTAINS EXECUTIONS",
            "doubt resolves to CONTAINS EXECUTIONS",
            False,
            "THE FAIL-CLOSED SIDE, and the opposite failure from the EXPECTED row above: without it "
            "a hard case resolves to a silent CLEAR, and a false clear launders a bad state with "
            "apparent authority, which is worse than having no probe at all",
        ),
        (
            "PROSE counts as work",
            "PROSE",
            False,
            "the dangerous case is work stated in ordinary prose inside an item's action text, which "
            "is the entire reason this is a model and not a regex. A prompt that only described "
            "checklist-shaped work would be answerable by pattern matching and would miss the "
            "measured corpus shape",
        ),
    )

    def test_the_rendered_prompt_carries_every_instruction_it_depends_on(self):
        prompt = rs.render_probe_prompt("excerpt here")
        wrong = []
        for case, needle, fold, why in self.INSTRUCTIONS:
            haystack = prompt.lower() if fold else prompt
            probe = needle.lower() if fold else needle
            if probe not in haystack:
                wrong.append(
                    f"  {case}:\n"
                    f"    - the rendered prompt is missing {needle!r}"
                    f"{' (case-insensitively)' if fold else ''}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the probe prompt lost {len(wrong)} of {len(self.INSTRUCTIONS)} instructions it depends "
            "on. ONE template composes all of them, so SEVERAL rows failing together means the "
            "prompt was rewritten wholesale rather than any single instruction being wrong. READ "
            "WHICH SIDE FAILED, because the two failure directions are opposite and not equally "
            "recoverable: losing the EXPECTED / orchestration / NOT-an-execution rows makes the probe "
            "fire on every orchestrator in the corpus, which is LOUD and trains operators to override "
            "it; losing the doubt-resolves row makes a hard case resolve to a silent CLEAR, which is "
            "the failure this gate exists to prevent and which nothing else in the suite would "
            "notice. FIX: restore the instruction, do not relax this table; if a rewording is "
            "deliberate, change the needle in the same commit that changes the template.\n"
            + "\n".join(wrong),
        )

    def test_the_prompt_and_the_parser_agree_on_the_same_sentinel_OBJECTS(self):
        """Kept separate: an IDENTITY claim, not a containment one.

        The table above proves the sentinel STRINGS reach the prompt. This proves the parser ANSWERS
        to those same two objects, which is a different subject (`classify_probe_reply`) and cannot be
        expressed as a substring row.
        """
        self.assertEqual(
            rs.classify_probe_reply(rs.PROBE_SENTINEL_EXECUTIONS),
            rs.PROBE_ANSWER_EXECUTIONS,
        )
        self.assertEqual(
            rs.classify_probe_reply(rs.PROBE_SENTINEL_NO_EXECUTIONS),
            rs.PROBE_ANSWER_NO_EXECUTIONS,
        )

    def test_the_prompt_is_held_as_data_not_inlined_at_a_call_site(self):
        """Kept separate: a claim about the MODULE ATTRIBUTE's existence and shape, not about output.

        `PROBE_PROMPT_TEMPLATE` being a formattable string is what makes the sentinels reach the
        prompt from the parser's own constants. A rendered-prompt row cannot state it: a prompt
        inlined at the call site would satisfy every row above.
        """
        self.assertIsInstance(rs.PROBE_PROMPT_TEMPLATE, str)
        self.assertIn("{excerpt}", rs.PROBE_PROMPT_TEMPLATE)


# ==================================================================================================
# E-02 / V-02: the parser, and the state split the ruling requires
# ==================================================================================================


class TheParserFailsClosed(unittest.TestCase):
    """E-02/E-10. Which reply reaches WHICH of the four answers, and whether that answer BLOCKS.

    ONE table replaces ELEVEN tests spread over two classes (`TheParserFailsClosed` and
    `TheCouldNotAskPathIsDistinctFromUnknown`). Every one handed `classify_probe_reply` one reply and
    asserted the answer plus its blocking membership, differing only in the reply text and the
    `transport_ok` flag. The class boundary tracked which E-item asked for the case, which is
    provenance rather than a property of the subject.

    EVERY ANSWER KEEPS ITS OWN ROW AND EVERY ROW ASSERTS THE ANSWER BY NAME, never merely "it
    blocked". That is the rule this file's tables may not bend: `unknown` and `could-not-ask` BOTH
    describe a probe that produced no usable verdict, and they have OPPOSITE consequences, so a table
    asserting only `answer in PROBE_BLOCKING_ANSWERS` would pass with the two collapsed into one
    state, which is exactly the regression these rows exist to catch. The blocking membership is
    asserted TOO, as a second column, because the answer name and its consequence are two facts and a
    reclassification could move either.

    WHY THE SPLIT IS THE POINT, restated because merging the two old classes makes it easier to lose:
    a COULD-NOT-ASK is evidence about the HOST (unreachable binary, timeout, empty stream) and is
    therefore evidence of NOTHING about the orchestrator, so the gate retries it to the run's budget
    and then warns past. An `unknown` is an answer the host DELIVERED and that cannot be used, so it
    evidences a confused model and BLOCKS. Keeping both in one table with an explicit `blocks` column
    is what makes the asymmetry readable as a property rather than as two unrelated files' worth of
    labels.

    THE TWO CLEAN ROWS ARE IN THE SAME TABLE and they carry real weight: a parser that answered
    `unknown` to everything would satisfy every blocking row on its own. Their failure message says so.
    """

    #: (case, the reply to classify, the `transport_ok` flag, the EXACT answer expected, whether that
    #: answer must be in `PROBE_BLOCKING_ANSWERS`, why this row exists)
    REPLIES = (
        (
            "the bare CONTAINS NO EXECUTIONS sentinel",
            rs.PROBE_SENTINEL_NO_EXECUTIONS,
            True,
            rs.PROBE_ANSWER_NO_EXECUTIONS,
            False,
            "A CLEAN ROW, and not decoration: this is the ONLY input that may clear a run, so every "
            "blocking row below is vacuous while this one is broken, because a parser that answered "
            "`unknown` to everything satisfies all of them",
        ),
        (
            "the bare CONTAINS EXECUTIONS sentinel",
            rs.PROBE_SENTINEL_EXECUTIONS,
            True,
            rs.PROBE_ANSWER_EXECUTIONS,
            True,
            "THE SECOND CLEAN ROW in the sense that the parser understood it, and simultaneously the "
            "gate's primary refusal. It must be distinguishable from `unknown`: both block, but only "
            "this one means the model actually found uncovered work, and the refusal an operator "
            "reads says so",
        ),
        (
            "a chatty reply that CONTAINS the clean sentinel",
            "Sure! Having read it carefully, " + rs.PROBE_SENTINEL_NO_EXECUTIONS,
            True,
            rs.PROBE_ANSWER_UNKNOWN,
            True,
            "THE MOST IMPORTANT ROW IN THE TABLE: the parser matches the reply EXACTLY and never by "
            "containment. A containment parser would read this as a CLEAR, which converts a model "
            "that did not follow instructions into a silent pass, and a false clear is the one "
            "outcome this whole gate exists to prevent",
        ),
        (
            "a refusal reply",
            "I cannot help with that request.",
            True,
            rs.PROBE_ANSWER_UNKNOWN,
            True,
            "a host that declined to answer DELIVERED something, so this is not `could-not-ask`: the "
            "transport worked and the reply is unusable, which is the definition of `unknown`",
        ),
        (
            "a reply carrying BOTH sentinels",
            rs.PROBE_SENTINEL_EXECUTIONS + "\n" + rs.PROBE_SENTINEL_NO_EXECUTIONS,
            True,
            rs.PROBE_ANSWER_UNKNOWN,
            True,
            "the model did not CHOOSE. Reading the first, the last, or either one would be inventing "
            "a verdict nobody gave, and the coin-flip lands on `clear` half the time",
        ),
        (
            "a reply reporting a problem with the excerpt",
            "The excerpt appears truncated; I could not determine coverage.",
            True,
            rs.PROBE_ANSWER_UNKNOWN,
            True,
            "A DELIVERED complaint is still an answer that cannot be used, and it reads like a "
            "transport failure in prose. Classifying it as `could-not-ask` would make it retried and "
            "then WARNED PAST, which is precisely the wrong treatment for a model saying it does not "
            "know",
        ),
        (
            "any reply at all when the transport FAILED",
            "anything at all",
            False,
            rs.PROBE_ANSWER_COULD_NOT_ASK,
            False,
            "THE SPLIT THE MAINTAINER'S OQ-02 RULING REQUIRES: `transport_ok=False` overrides the "
            "text entirely, because bytes that arrived from a failed spawn are not evidence about the "
            "orchestrator. This is the one row where a reply that WOULD classify as `unknown` must "
            "not, and it is what stops an outage being reported as a confused model",
        ),
        (
            "an EMPTY reply",
            "",
            True,
            rs.PROBE_ANSWER_COULD_NOT_ASK,
            False,
            "there is nothing to be CONFUSED BY. An empty stream on a nominally successful exit is a "
            "host that produced no answer, so it belongs on the availability path and not the "
            "fail-closed one",
        ),
        (
            "a None reply",
            None,
            True,
            rs.PROBE_ANSWER_COULD_NOT_ASK,
            False,
            "the same fact arriving as the absence of a value rather than as an empty string. Kept as "
            'its own row because `None` and `""` reach different branches of any real parser and a '
            "`None` that crashed would take the gate down rather than warn past",
        ),
    )

    def test_every_reply_reaches_its_own_answer_and_its_own_blocking_verdict(self):
        wrong = []
        for case, reply, transport_ok, expected, blocks, why in self.REPLIES:
            answer = rs.classify_probe_reply(reply, transport_ok=transport_ok)
            problems = []
            if answer != expected:
                problems.append(f"expected answer {expected!r}, got {answer!r}")
            actually_blocks = answer in rs.PROBE_BLOCKING_ANSWERS
            if actually_blocks != blocks:
                problems.append(
                    f"expected this answer to {'BLOCK' if blocks else 'NOT block'} "
                    f"(membership in PROBE_BLOCKING_ANSWERS), but {answer!r} "
                    f"{'blocks' if actually_blocks else 'does not block'}"
                )
            if problems:
                wrong.append(
                    f"  {case} (transport_ok={transport_ok}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`classify_probe_reply` was wrong for {len(wrong)} of {len(self.REPLIES)} replies. READ "
            "THE GROUPING, because each pattern names a different defect. Both SENTINEL rows going "
            "`unknown` means the accepted spellings moved and no run can ever be cleared. The CHATTY "
            "row alone turning into a clean answer means the parser started matching by CONTAINMENT, "
            "which converts a model that ignored its instructions into a silent pass. All three "
            "COULD-NOT-ASK rows turning into `unknown` means the four-state vocabulary was collapsed "
            "into a tri-state, so a model outage now halts runs instead of warning past them; the "
            "reverse (an `unknown` row turning into `could-not-ask`) is far worse, because a confused "
            "model would then be RETRIED and WARNED PAST. FIX: the two unusable states are not "
            "interchangeable labels; `unknown` means the host answered and the answer is useless, "
            "`could-not-ask` means the host never answered.\n" + "\n".join(wrong),
        )

    def test_the_answer_vocabulary_is_FOUR_states_not_three(self):
        """Kept separate: a claim about the closed SET, with no reply involved.

        The table above proves each reply reaches its answer; this proves the vocabulary itself has
        not been narrowed. A tri-state cannot express the OQ-02 ruling at all, and a table row cannot
        state that because every row already presumes the four names exist.
        """
        self.assertEqual(
            {
                rs.PROBE_ANSWER_NO_EXECUTIONS,
                rs.PROBE_ANSWER_EXECUTIONS,
                rs.PROBE_ANSWER_UNKNOWN,
                rs.PROBE_ANSWER_COULD_NOT_ASK,
            },
            {"no-executions", "executions", "unknown", "could-not-ask"},
        )
        self.assertNotIn(rs.PROBE_ANSWER_COULD_NOT_ASK, rs.PROBE_BLOCKING_ANSWERS)


class TheReplyIsReadFromEitherHostsSchema(unittest.TestCase):
    """E-02/E-09. ONE extractor taking the HOST as an argument, never a parser forked per host.

    ONE table replaces four tests. Each handed `probe_reply_text` one host's stdout shape and asserted
    the text it recovered, so the HOST and the SCHEMA are columns rather than reasons for four tests.

    THE HOST IS A COLUMN AND THAT IS THE WHOLE POINT OF ONE TABLE: the claim worth stating is that the
    SAME function answers for both hosts, which is `pgq326`'s lesson applied to the parser. Four
    separate tests would each pass with a per-host fork in place, since none of them compares the two.

    THE END-TO-END ANSWER IS ASSERTED, NOT JUST THE EXTRACTED TEXT, and that is what the unrecognized
    -schema row needs: the property there is not "it returned something odd" but that the odd thing
    classifies to `could-not-ask`, so a host that changes its event shape FAILS THE PARSE rather than
    accidentally clearing a run. Asserting the intermediate string alone would let a schema change
    land on `no-executions` and still look tested.
    """

    #: (case, host, the stdout bytes to read, the text `probe_reply_text` must recover, the answer
    #: that text must then classify to, why this row exists)
    SCHEMAS = (
        (
            "the opencode `text` event shape",
            "oc",
            json.dumps(
                {"type": "text", "part": {"text": rs.PROBE_SENTINEL_EXECUTIONS}}
            ),
            rs.PROBE_SENTINEL_EXECUTIONS,
            rs.PROBE_ANSWER_EXECUTIONS,
            "opencode's shipped `--format json` stream shape. A CLEAN ROW: the extractor must "
            "actually recover a real answer, or every refusal row below is satisfied by a function "
            "that returns nothing at all",
        ),
        (
            "the antigravity `step_update` shape",
            "agy",
            json.dumps(
                {
                    "event": "step_update",
                    "step_update": {
                        "state": "DONE",
                        "step_type": "agent_response",
                        "text": rs.PROBE_SENTINEL_NO_EXECUTIONS,
                    },
                }
            ),
            rs.PROBE_SENTINEL_NO_EXECUTIONS,
            rs.PROBE_ANSWER_NO_EXECUTIONS,
            "THE SECOND CLEAN ROW, and the one that makes this table a host COLUMN rather than two "
            "tests: a different wire schema must reach the same answer vocabulary through the same "
            "function. It carries the CLEAN sentinel deliberately, so a host whose replies were "
            "silently dropped could not pass by defaulting to a block",
        ),
        (
            "plain text on stdout, no JSON envelope at all",
            "oc",
            rs.PROBE_SENTINEL_EXECUTIONS,
            rs.PROBE_SENTINEL_EXECUTIONS,
            rs.PROBE_ANSWER_EXECUTIONS,
            "a host that emitted no envelope must still be READ, not discarded: a correct answer in "
            "the simplest possible form is the case a JSON-only extractor would turn into a "
            "permanent `could-not-ask`, which blocks nothing but costs every run its probe",
        ),
        (
            "an UNRECOGNIZED event schema",
            "agy",
            json.dumps({"event": "something-new", "payload": {"deep": "value"}}),
            None,  # the recovered text is not pinned; only what it classifies to
            rs.PROBE_ANSWER_COULD_NOT_ASK,
            "THE FAIL-CLOSED ROW: a host that changes its event shape must fail the PARSE. The "
            "recovered text is deliberately unpinned (any of empty, the raw line, or a partial "
            "extraction is acceptable) because the property that matters is only that it can never "
            "classify as an answer, and `could-not-ask` is right rather than `unknown` since nothing "
            "was delivered in a shape the reader understood",
        ),
    )

    def test_one_extractor_reads_both_hosts_and_fails_closed_on_a_third_shape(self):
        wrong = []
        for case, host, stdout, expected_text, expected_answer, why in self.SCHEMAS:
            reply = rs.probe_reply_text(stdout, host=host)
            problems = []
            if expected_text is not None and reply != expected_text:
                problems.append(f"expected the text {expected_text!r}, got {reply!r}")
            answer = rs.classify_probe_reply(reply)
            if answer != expected_answer:
                problems.append(
                    f"the recovered text classified as {answer!r}, expected {expected_answer!r} "
                    f"(text was {reply!r})"
                )
            if problems:
                wrong.append(
                    f"  {case} (host={host!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`probe_reply_text` was wrong for {len(wrong)} of {len(self.SCHEMAS)} host schemas. ONE "
            "function takes the host as an ARGUMENT, so BOTH host rows failing together means that "
            "function changed rather than either schema being misread; ONE host row failing alone is "
            "the dangerous case, because it means the reader was forked per host and the two halves "
            "have started to disagree, which is `pgq326`'s exact lesson. FIX: a host whose replies "
            "stop being read does not merely lose its probe, it loses it SILENTLY as a permanent "
            "`could-not-ask` that every run warns past.\n" + "\n".join(wrong),
        )


class TheAskerReportsWhatWentWrong(unittest.TestCase):
    """E-02/E-10. `ask_orchestrator_probe` over a real spawn's failure modes, with its DETAIL.

    ONE table replaces three tests (`a_missing_binary_is_could_not_ask_and_not_unknown`,
    `a_timeout_exit_is_could_not_ask_even_if_the_stream_carried_words`,
    `a_FileNotFoundError_from_the_spawn_is_could_not_ask`). All three injected a `runner` double that
    fails in one way and asserted `could-not-ask` plus, sometimes, a substring of the detail.

    THE DETAIL IS A COLUMN AND EVERY ROW CARRIES ONE, which is stricter than what it replaces: the
    timeout test asserted only the answer, so a timeout reported as "not found" would have passed. All
    three failures reach the SAME answer, so the detail is the ONLY thing that tells an operator which
    of them happened, and this gate's whole output to a human is a reason plus a remedy.

    THE DELIVERING ROWS ARE IN THE SAME TABLE. Three failure rows are all satisfied by an asker that
    returns `could-not-ask` unconditionally, so a successful ask through the same seam is a row too,
    on both hosts.
    """

    #: (case, the `runner` double, the host, the answer expected, a substring the DETAIL must carry
    #: or None, why this row exists)
    ASKS = (
        (
            "a runner delivering the clean sentinel",
            _reply(rs.PROBE_SENTINEL_NO_EXECUTIONS),
            "oc",
            rs.PROBE_ANSWER_NO_EXECUTIONS,
            None,
            "THE CLEAN ROW: the ask seam must be able to succeed. Every failure row below is "
            "satisfied by an asker that returns `could-not-ask` unconditionally, so without this one "
            "the table would pass against a probe that never works at all",
        ),
        (
            "a runner delivering the blocking sentinel",
            _reply(rs.PROBE_SENTINEL_EXECUTIONS),
            "oc",
            rs.PROBE_ANSWER_EXECUTIONS,
            None,
            "THE SECOND CLEAN ROW, kept distinct because the two verdicts must be individually "
            "reachable THROUGH THE SEAM and not merely through the classifier: an asker that mapped "
            "every delivered reply onto one verdict would still satisfy the row above",
        ),
        (
            "an exit-127 spawn failure with a message on stderr",
            _transport_failure(),
            "oc",
            rs.PROBE_ANSWER_COULD_NOT_ASK,
            "not found",
            "THE MISSING-BINARY CASE, which is the most common real failure (a host not installed on "
            "the machine the run launched from). The detail must carry the host's own words, because "
            "`could-not-ask` alone tells an operator nothing about what to fix",
        ),
        (
            "a timeout exit whose stream DID carry words",
            lambda argv, cwd, timeout: (
                124,
                json.dumps({"type": "text", "part": {"text": "partial"}}),
                "timed out",
            ),
            "oc",
            rs.PROBE_ANSWER_COULD_NOT_ASK,
            "timed out",
            "A PARTIAL STREAM MUST NOT BE JUDGED. The bytes look parseable, so a reader keying on "
            "content rather than on the exit code would classify the fragment and could land on a "
            "CLEAR. The detail row is stricter than the test it replaces, which asserted only the "
            "answer and so accepted a timeout reported as any other failure",
        ),
        (
            "a FileNotFoundError raised by the spawn itself",
            _raises(FileNotFoundError("opencode")),
            "oc",
            rs.PROBE_ANSWER_COULD_NOT_ASK,
            "PATH",
            "THE EXCEPTION PATH, distinct from the exit-127 row above: an OSError escaping here would "
            "take the whole run down instead of warning past a missing host. The detail must name "
            "PATH, because that is the actionable fix and it is what distinguishes this from a host "
            "that ran and failed",
        ),
    )

    def test_every_ask_outcome_reports_its_own_answer_and_its_own_reason(self):
        state = {"options": {"opencode": "opencode"}}
        wrong = []
        for case, runner, host, expected, needle, why in self.ASKS:
            problems = []
            try:
                answer, detail = rs.ask_orchestrator_probe(
                    state, "x", host=host, repo=Path("."), runner=runner
                )
            except Exception as exc:  # noqa: BLE001 - an escaping error IS the defect here
                answer, detail = None, ""
                problems.append(
                    f"the ask RAISED {type(exc).__name__}: {exc}. Every failure mode must be "
                    "REPORTED as an answer; an escaping exception takes the run down"
                )
            if answer is not None:
                if answer != expected:
                    problems.append(f"expected answer {expected!r}, got {answer!r}")
                if needle is not None and needle not in detail:
                    problems.append(
                        f"the detail must carry {needle!r} so an operator knows WHICH failure "
                        f"happened; it said {detail!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case} (host={host!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`ask_orchestrator_probe` was wrong for {len(wrong)} of {len(self.ASKS)} outcomes. All "
            "THREE failure rows failing together means the transport-failure detection changed "
            "wholesale; a single one failing means that specific mode is now misreported, and the "
            "detail is the ONLY thing distinguishing them once the answer is `could-not-ask` for all "
            "three. The dangerous direction is a failure row reaching `unknown` or an ANSWER: "
            "`unknown` blocks a run over an outage, and a judged partial stream can CLEAR one. FIX: "
            "if a clean row is among the failures the seam cannot succeed at all, which makes every "
            f"failure row here vacuous.\n" + "\n".join(wrong),
        )


# ==================================================================================================
# E-03 / V-03: the bounded payload, and the price of bounding it
# ==================================================================================================


class TheExcerptIsTheCacheKeysOwnInputs(unittest.TestCase):
    """E-03. Payload and key are the same two things BY CONSTRUCTION, not by agreement.

    ONE table replaces four tests (`the_excerpt_is_rendered_from_the_cache_payload`,
    `is_a_SMALL_FRACTION_of_the_file`, `the_child_table_arrives_as_ROW_CELL_TEXT`,
    `an_empty_orchestrator_still_produces_a_usable_excerpt`). Each took one orchestrator text, built
    its excerpt, and asserted one property of it, so the FIXTURE is a column and the properties are
    checked on every fixture instead of one each.

    Why the table beats the four: every property here is a property of ONE renderer reading ONE
    payload function, so a change to the payload shape breaks several at once. Checking each property
    on each fixture is also strictly stronger than the tests it replaces: the old containment test ran
    only on the parent-only fixture, and the bounded-size test ran on two while asserting nothing about
    content.

    THE BOUNDEDNESS COLUMN IS THREE-VALUED, NOT A BOOLEAN, AND THAT IS A MEASURED CORRECTION. The
    empty-orchestrator fixture's excerpt is LONGER than its source (34 characters in, 178 out: the two
    "(this orchestrator declares no ...)" placeholders exceed the file), so a table demanding
    `len(excerpt) < len(text)` on every row would be asserting something false. Boundedness is
    therefore asserted where it is meaningful and explicitly WAIVED on the degenerate row, which is
    better than dropping the claim or narrowing the table to the fixtures that happen to satisfy it.
    """

    #: (case, the orchestrator text, whether the excerpt must be SHORTER than the source, substrings
    #: the excerpt must contain, substrings it must NOT contain, why this row exists)
    #:
    #: The containment check that the excerpt is rendered FROM `probe_cache_payload` runs on every row
    #: automatically (see the loop), since that identity is the point of the whole class and not a
    #: property of any one fixture.
    EXCERPTS = (
        (
            "the orchestration-only parent",
            ORCHESTRATION_ONLY,
            True,
            (
                # The sequencing instruction moved to the row's CONTINUATION lines when the row was
                # made IPD-S407 conforming (2026-09-24), so the substring asserted here moved with
                # it. The PROPERTY is unchanged and is what this row is for: the item's own text
                # must reach the model, not only the child table.
                "Hold each child until its predecessor reads",
                "CONFIRM aaa111 REACHED executed",
                "aaa111",
                "the child that does the work",
            ),
            (),
            "THE SHAPE THE CORPUS ACTUALLY CONTAINS, measured: every live orchestrator carries items "
            "and most carry only sequencing. Its item text and its child-table cells must both reach "
            "the model, or the probe is deciding on less than the question depends on",
        ),
        (
            "the parent-only-work parent",
            PARENT_ONLY_WORK,
            True,
            (
                "CHARACTERIZATION BASELINE",
                "BEFORE any child reconciles anything",
                "run the repo-wide suite",
                "bbb222",
            ),
            (),
            "THE HAZARD ITSELF, and the needles are chosen to prove the payload is not truncated at "
            "an item's first line: two of them live on CONTINUATION lines, which is where the live "
            "corpus actually states parent-only work and which a measured defect once dropped "
            "entirely (58 percent of action prose lost; see the class below)",
        ),
        (
            "a bare parent with neither items nor a child table",
            "# IPD: bare\n\n- Kind: orchestrator\n",
            False,  # MEASURED: 34 chars in, 178 out. The placeholders exceed the source.
            ("no checklist items", "no child table"),
            (),
            "THE DEGENERATE ROW: an empty prompt body would ask the model to judge nothing, and a "
            "model given nothing tends to agree with whatever it was asked. The placeholders must SAY "
            "the sections are empty. Boundedness is WAIVED here rather than quietly excluded, because "
            "this excerpt is legitimately LONGER than its source file",
        ),
    )

    def test_every_excerpt_is_bounded_complete_and_rendered_from_the_cache_payload(
        self,
    ):
        wrong = []
        for case, text, bounded, required, forbidden, why in self.EXCERPTS:
            excerpt = rs.orchestrator_probe_excerpt(text)
            payload = rs.probe_cache_payload(text)
            problems = []
            # THE IDENTITY, checked on every row: everything the digest keys on must be IN the
            # excerpt, or the probe reasons over something the cache does not cover and a later edit
            # to that thing serves a STALE verdict under apparent authority.
            for item in payload["e_items"]:
                if item.splitlines()[0] not in excerpt:
                    problems.append(
                        f"the cache payload's E-item {item.splitlines()[0][:60]!r} is NOT in the "
                        "excerpt, so the digest keys on text the model never sees"
                    )
            for row in payload["child_table_rows"]:
                for cell in row:
                    if cell and cell not in excerpt:
                        problems.append(
                            f"the cache payload's child-table cell {cell!r} is NOT in the excerpt, "
                            "so the digest keys on a table cell the model never sees"
                        )
            if bounded and len(excerpt) >= len(text):
                problems.append(
                    f"the excerpt is {len(excerpt)} characters for a {len(text)}-character source, "
                    "so it is not bounded: an unbounded probe sends a five-figure token file to "
                    "answer a yes/no question"
                )
            for needle in required:
                if needle not in excerpt:
                    problems.append(
                        f"the excerpt is missing {needle!r}, which the coverage question depends on"
                    )
            for needle in forbidden:
                if needle in excerpt:
                    problems.append(f"the excerpt must NOT contain {needle!r}")
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the excerpt was wrong for {len(wrong)} of {len(self.EXCERPTS)} fixtures. ONE renderer "
            "reading ONE payload function answers every row, so SEVERAL rows failing together means "
            "the payload's SHAPE changed rather than any fixture being mishandled. FIX: the two "
            "failure directions have different costs. A MISSING needle narrows what the model sees, "
            "so the probe decides on less than the question depends on and misses an instance. A "
            "payload entry absent from the excerpt is worse and is the reason this identity is "
            "asserted at all: the digest would then key on text the probe never reasoned over, so "
            "editing that text serves a STALE verdict with apparent authority, which is the one way "
            f"this cache can be actively WRONG rather than merely useless.\n"
            + "\n".join(wrong),
        )

    def test_the_child_table_arrives_as_ROW_CELL_TEXT_not_a_parsed_order_graph(self):
        """Kept separate: a before/after PAIR asserting the excerpt CHANGES, not a per-fixture claim.

        `ipd_set_plan.parse_child_table` returns `{order: (dep_orders,)}`, so an Id swap and a
        description rewrite leave it byte-identical. The claim is that two DIFFERENT documents produce
        two different excerpts, which needs both of them and cannot be a row about one.
        """
        excerpt = rs.orchestrator_probe_excerpt(PARENT_ONLY_WORK)
        swapped = PARENT_ONLY_WORK.replace("bbb222", "zzz999")
        self.assertNotEqual(excerpt, rs.orchestrator_probe_excerpt(swapped))
        reworded = PARENT_ONLY_WORK.replace(
            "the child that does the work", "a totally different child"
        )
        self.assertNotEqual(excerpt, rs.orchestrator_probe_excerpt(reworded))

    def test_a_NO_OP_executor_mutation_does_not_change_the_excerpt(self):
        """Kept separate: a before/after IDENTITY pair, whose content is that nothing moved.

        The `xmqv5l` trap: a conforming executor ticks boxes and fills evidence, and neither may
        re-probe. A row asserting one excerpt's content cannot state that two excerpts are EQUAL.
        """
        ticked = PARENT_ONLY_WORK.replace(
            "- [ ] E-02 Establish", "- [x] E-02 Establish"
        )
        self.assertEqual(
            rs.orchestrator_probe_excerpt(PARENT_ONLY_WORK),
            rs.orchestrator_probe_excerpt(ticked),
        )


class TheActionTextIsTheWholeBlockNotItsFirstLine(unittest.TestCase):
    """E-03. A DEFECT FOUND AND FIXED WHILE EXECUTING THIS CHILD, pinned so it cannot return.

    WHAT WAS WRONG. `probe_cache_payload` took each item's action from `ipd_lint.Leaf.text`, which is
    the remainder of the leaf's OPENING LINE only, so every CONTINUATION line was dropped. Measured
    over the ten live pending orchestrators at 2026-09-19 that lost 58 percent of the action prose
    (11,758 of 27,949 characters) and on `wfjsp4` it kept 10 percent.

    WHY IT MATTERED TWICE OVER, which is why this class exists rather than a one-line assertion. As a
    PROBE PAYLOAD it hid the very evidence the coverage question turns on, because parent-only work is
    stated in exactly those continuation lines. As a CACHE KEY it was UNDER-SENSITIVE: rewriting an
    item's continuation lines is how an author actually changes what an item asks for, and the digest
    did not move, so a stale verdict was served for a materially different plan. The second is the
    dangerous half, since it is the cache being actively WRONG rather than merely narrow.

    ONE TABLE REPLACES FOUR OF THIS CLASS'S TESTS (`editing_a_CONTINUATION_line_moves_the_digest`,
    `ticking_the_checkbox_still_moves_NOTHING`, `writing_an_execution_note_still_moves_NOTHING`, and
    the digest half of the excerpt claim). Each edited the same fixture in one way and asserted the
    digest either MOVED or did not, so the direction is a COLUMN.

    BOTH DIRECTIONS MUST BE IN ONE TABLE, which is the strongest argument for tabulating here at all.
    Over-sensitivity and under-sensitivity are opposite defects with one shared cause (what the digest
    keys on), and a digest that moved on EVERYTHING would satisfy every `moves` row while destroying
    the cache, while one that moved on NOTHING satisfies every `stays` row while serving stale verdicts
    forever. Only adjacent rows state the real property: the digest moves for exactly the edits that
    change what an item ASKS FOR.

    THE EXCERPT IS CHECKED IN THE SAME LOOP, because the excerpt and the digest read the same payload
    function and the whole point of E-03 is that they cannot disagree. A row whose digest moves while
    its excerpt does not (or the reverse) is the divergence this Set spent a child preventing, and the
    failure message says so explicitly.
    """

    MULTILINE = (
        "## Detailed Implementation Checklist (TODO)\n"
        "\n"
        "- [ ] E-01 Sequence the children.\n"
        "  AND ALSO establish the baseline before any child runs, which no child covers.\n"
        "  - Depends on: none\n"
        "  - Expected outcome: a baseline nobody else establishes.\n"
        "  - Execution state: pending\n"
    )

    #: (case, the edit as (find, replace), whether the digest MUST move, why this row exists)
    #:
    #: Every row additionally asserts that the EXCERPT moved iff the digest did, which is the payload
    #: identity E-03 requires. Measured 2026-09-19: all eight edits agree in both directions today.
    EDITS = (
        (
            "rewriting a CONTINUATION line's meaning",
            (
                "AND ALSO establish the baseline before any child runs, which no child covers.",
                "AND ALSO merely read each child's status on disk, which is pure sequencing.",
            ),
            True,
            "THE UNDER-SENSITIVITY HALF, AND THIS ASSERTION FAILED BEFORE THE FIX. Rewriting an "
            "item's continuation lines is how an author actually changes what the item asks for, and "
            "this exact edit turns parent-only work into pure sequencing, i.e. it flips the correct "
            "verdict. A digest that does not move here serves the OLD verdict for a materially "
            "different plan, which is the cache being actively wrong rather than merely narrow",
        ),
        (
            "changing the item's action FIRST line",
            ("E-01 Sequence the children.", "E-01 Produce the inventory deliverable."),
            True,
            "the first line was the ONLY thing the digest used to read, so this row is the control "
            "for the one above: if it moves and the continuation row does not, the pre-fix "
            "first-line-only behavior has returned",
        ),
        (
            "ticking the checkbox",
            ("- [ ] E-01", "- [x] E-01"),
            False,
            "THE `xmqv5l` TRAP, and the fix above must not be bought by re-introducing it: a "
            "conforming executor ticks boxes, so a digest that moved here would re-probe (and spend a "
            "model call) on every run that touched the plan without changing what it asks for",
        ),
        (
            "writing an execution note and marking the state performed",
            (
                "  - Execution state: pending\n",
                "  - Execution state: performed\n  - Execution note: did the thing.\n",
            ),
            False,
            "the other half of the same no-op: the sub-fields are PROGRESS, not intent. A digest "
            "keying on them would invalidate itself exactly when a run is making progress, which is "
            "the worst possible time to spend a call",
        ),
    )

    def test_the_digest_moves_for_exactly_the_edits_that_change_what_an_item_ASKS_FOR(
        self,
    ):
        wrong = []
        for case, (find, replace), must_move, why in self.EDITS:
            edited = self.MULTILINE.replace(find, replace)
            problems = []
            if edited == self.MULTILINE:
                problems.append(
                    f"the row's edit did not apply: {find!r} is not in the fixture, so this row "
                    "asserts nothing"
                )
            digest_moved = rs.probe_cache_digest(
                self.MULTILINE
            ) != rs.probe_cache_digest(edited)
            excerpt_moved = rs.orchestrator_probe_excerpt(
                self.MULTILINE
            ) != rs.orchestrator_probe_excerpt(edited)
            if digest_moved != must_move:
                problems.append(
                    f"the digest {'did NOT move' if must_move else 'MOVED'} but it must "
                    f"{'move' if must_move else 'stay identical'}"
                )
            if digest_moved != excerpt_moved:
                problems.append(
                    f"THE PAYLOAD IDENTITY IS BROKEN: the digest "
                    f"{'moved' if digest_moved else 'did not move'} while the excerpt "
                    f"{'moved' if excerpt_moved else 'did not move'}. They read the same payload "
                    "function, so they cannot legitimately disagree"
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
            f"`probe_cache_digest` was wrong for {len(wrong)} of {len(self.EDITS)} edits. READ WHICH "
            "DIRECTION FAILED, because the two are opposite defects with one cause. ALL THE `stays` "
            "ROWS MOVING means the digest is over-sensitive, which merely wastes model calls and is "
            "loud. ALL THE `moves` ROWS STAYING is the dangerous direction: a stale verdict is then "
            "served for a plan whose items now ask for something else, under the apparent authority "
            "of a recorded answer, and the continuation-line row is the one that was measurably "
            "broken in production (58 percent of action prose dropped across ten live orchestrators). "
            "A PAYLOAD-IDENTITY complaint outranks both: it means the excerpt and the digest have "
            "diverged, so widening one without the other is already underway. FIX: widen the payload "
            f"and the digest in the SAME change, never one alone.\n" + "\n".join(wrong),
        )

    def test_the_action_block_is_the_whole_block_and_nothing_structural(self):
        """Kept separate: a claim about `e_item_action_blocks`'s STRUCTURE, not about a digest.

        ONE test rather than rows because all three claims are about the SAME single parse of the same
        fixture: the block count, what the block includes (the continuation line), and what it
        excludes (the sub-fields the `xmqv5l` no-op invariants depend on). Splitting them would
        re-parse the same input three times to assert three facets of one return value.
        """
        blocks = rs.e_item_action_blocks(self.MULTILINE)
        self.assertEqual(len(blocks), 1)
        self.assertIn("Sequence the children.", blocks[0])
        self.assertIn("establish the baseline before any child runs", blocks[0])
        for field in ("Depends on:", "Expected outcome:", "Execution state:"):
            self.assertNotIn(field, blocks[0])
        # And the probe SEES that continuation prose, which is the payload half of the same fix.
        self.assertIn(
            "establish the baseline before any child runs",
            rs.orchestrator_probe_excerpt(self.MULTILINE),
        )

    def test_a_multi_item_document_keeps_the_items_SEPARATE(self):
        """Kept separate: materially different setup (a two-item document) and a boundary claim.

        The property is that the parser does not RUN two items together, which needs a second item and
        asserts something about the relationship between blocks rather than about any one of them.
        """
        text = self.MULTILINE + (
            "\n- [ ] E-02 A second item entirely.\n"
            "  with its own continuation.\n"
            "  - Execution state: pending\n"
        )
        blocks = rs.e_item_action_blocks(text)
        self.assertEqual(len(blocks), 2)
        joined = " ".join(blocks)
        self.assertIn("A second item entirely.", joined)
        self.assertNotIn("A second item entirely.", blocks[0])


class TheExcerptHasAKnownLIMIT(unittest.TestCase):
    """E-03's PRICE, asserted so it is visible in the suite rather than found while debugging.

    THE TENSION IS REAL AND IS RESOLVED DELIBERATELY. This child's stated reason for using a model is
    that the dangerous case is PROSE, and its E-03 simultaneously requires the payload be EXACTLY the
    cache key's inputs (E-item action text plus child-table rows), because a payload the key does not
    cover would serve a STALE verdict - the one way that cache can be actively wrong rather than merely
    useless. Those two requirements do not fully agree: prose inside an ITEM'S ACTION TEXT is sent (and
    that is the case the corpus actually contains, measured), while prose in a section OUTSIDE the
    checklist is not.

    E-03 WINS, because a stale verdict served under apparent authority is worse than a narrower probe,
    and widening the payload without widening `8tgg6g`'s digest is precisely the divergence this Set
    spent a child preventing. The residual gap is REPORTED as a defect rather than hidden here; closing
    it means widening BOTH the digest and the payload together, which is a change to a shipped cache
    and belongs to its own plan.
    """

    def test_prose_inside_an_ITEM_is_sent_because_that_is_the_measured_corpus_shape(
        self,
    ):
        excerpt = rs.orchestrator_probe_excerpt(PARENT_ONLY_WORK)
        self.assertIn("CHARACTERIZATION BASELINE", excerpt)
        # A CONTINUATION line of the same item, which is where the hazard is actually stated in the
        # live corpus and which was dropped until this child widened the payload.
        self.assertIn("BEFORE any child reconciles anything", excerpt)
        self.assertIn("run the repo-wide suite", excerpt)

    def test_prose_OUTSIDE_the_checklist_is_NOT_sent_and_that_limit_is_pinned_here(
        self,
    ):
        plan = ORCHESTRATION_ONLY.replace(
            "Sequence the Set. This parent holds coordination and nothing beyond it.",
            "Before any child runs, SOMEONE MUST MIGRATE THE PRODUCTION DATABASE by hand.",
        )
        excerpt = rs.orchestrator_probe_excerpt(plan)
        self.assertNotIn(
            "MIGRATE THE PRODUCTION DATABASE",
            excerpt,
            "if this now PASSES, the payload was widened; widen `probe_cache_digest` in the SAME "
            "change or the cache will serve stale verdicts, and then delete this test",
        )

    def test_the_limit_is_a_consequence_of_the_payload_identity_and_not_a_bug_in_the_excerpt(
        self,
    ):
        """Stated as an assertion so the two cannot drift apart silently."""
        payload = rs.probe_cache_payload(ORCHESTRATION_ONLY)
        self.assertEqual(set(payload), {"e_items", "child_table_rows"})


# ==================================================================================================
# E-04 / V-04: queue-scoped, cache-first
# ==================================================================================================


class TheCacheIsConsultedFirst(ProbeCase):
    """E-04. What the cache's prior STATE costs, and what each answer writes back into it.

    ONE table replaces three of this class's tests (`every_orchestrator_cached_means_ZERO_model_calls`,
    `editing_an_E_item_action_costs_exactly_ONE_call`,
    `a_probed_verdict_is_RECORDED_so_the_next_run_is_free`). Each seeded the store in one state, ran
    the real gate once, and asserted the call count plus either the decision or what the store held
    afterwards. The PRIOR STATE is therefore a column, not a reason for three tests.

    EVERY VERDICT KEEPS ITS OWN ROW, including the two that must NOT be written back. That is the
    rule this file holds to: a cached `fail` must refuse just as a probed `executions` does, and a
    `could-not-ask` or an `unknown` must leave the store EMPTY, because recording either would turn
    "nobody established this" into a stored fact that a later run reads as authority. Those two rows
    are the reason the store's contents are a column rather than an afterthought.

    THE ROWS ASSERT COST AND OUTCOME TOGETHER, which is stronger than the tests they replace. A hit
    row that checked only `calls == 0` would pass against a gate that consulted the cache and then
    ignored its verdict, so each row pins the verdict SERVED (via `outcomes[0].cached`), whether the
    run proceeded, AND what the store holds when the gate returns.
    """

    #: (case, the plan text to write, the text whose digest is SEEDED (None = seed nothing), the
    #: verdict to seed, the answer the double returns, expected model calls, expected `cached` flag,
    #: expected `proceed`, the verdict the store must hold afterwards (None = it must hold NOTHING),
    #: why this row exists)
    CACHE_STATES = (
        (
            "an unmodified orchestrator whose PASS is cached",
            ORCHESTRATION_ONLY,
            ORCHESTRATION_ONLY,
            rs.PROBE_VERDICT_PASS,
            rs.PROBE_ANSWER_EXECUTIONS,  # the double would BLOCK if it were ever consulted
            0,
            True,
            True,
            rs.PROBE_VERDICT_PASS,
            "THE WHOLE POINT OF THE CACHE: an unmodified orchestrator must cost NOTHING. The double is "
            "rigged to answer `executions`, so a gate that asked anyway would refuse the run, which "
            "is what makes `calls == 0` a real assertion rather than a count nobody checks",
        ),
        (
            "an unmodified orchestrator whose FAIL is cached",
            PARENT_ONLY_WORK,
            PARENT_ONLY_WORK,
            rs.PROBE_VERDICT_FAIL,
            rs.PROBE_ANSWER_NO_EXECUTIONS,  # the double would CLEAR if it were ever consulted
            0,
            True,
            False,
            rs.PROBE_VERDICT_FAIL,
            "A CACHED REFUSAL MUST STILL REFUSE, and the double is rigged the opposite way so a gate "
            "that re-asked would CLEAR the run. This is the row that makes the cache a decision "
            "surface and not merely a cost optimization: a `fail` served from disk carries the same "
            "authority as one just probed",
        ),
        (
            "a CONTINUATION line edited under a cached PASS",
            ORCHESTRATION_ONLY.replace(
                "does not. DO NOT PERFORM ANY CHILD'S WORK FROM HERE",
                "does not. ALSO produce the inventory artifact nobody else produces",
            ),
            ORCHESTRATION_ONLY,
            rs.PROBE_VERDICT_PASS,
            rs.PROBE_ANSWER_NO_EXECUTIONS,
            1,
            False,
            True,
            rs.PROBE_VERDICT_PASS,
            "A CONTENT CHANGE COSTS EXACTLY ONE CALL, and the edit is a CONTINUATION line "
            "deliberately: that is where an author actually changes what an item asks for, and it was "
            "invisible to the digest until this child fixed the payload. A stale hit here would serve "
            "the old verdict for a plan that now asks for something else",
        ),
        (
            "an unseeded orchestrator answered `no-executions`",
            ORCHESTRATION_ONLY,
            None,
            None,
            rs.PROBE_ANSWER_NO_EXECUTIONS,
            1,
            False,
            True,
            rs.PROBE_VERDICT_PASS,
            "THE VERDICT IS RECORDED SO THE NEXT RUN IS FREE. Without the write-back the cache never "
            "populates and every run pays for every orchestrator, which is how a probe gets disabled "
            "by an operator rather than by a decision",
        ),
        (
            "an unseeded orchestrator answered `executions`",
            PARENT_ONLY_WORK,
            None,
            None,
            rs.PROBE_ANSWER_EXECUTIONS,
            1,
            False,
            False,
            rs.PROBE_VERDICT_FAIL,
            "A REFUSAL IS RECORDED TOO, as `fail` rather than as nothing. Recording only passes would "
            "make every refused run re-probe, and the re-probe is exactly where a flaky model gets a "
            "second chance to clear work it already flagged",
        ),
        (
            "an unseeded orchestrator the host COULD NOT BE ASKED about",
            ORCHESTRATION_ONLY,
            None,
            None,
            rs.PROBE_ANSWER_COULD_NOT_ASK,
            1,
            False,
            True,
            None,
            "IT MUST WRITE NOTHING. Recording a `could-not-ask` would convert `not probed` into a "
            "stored fact, so a later run would read an outage as an answer. The run still PROCEEDS "
            "(E-10 warns past it), which is why the store being empty is the only thing that keeps "
            "the hole visible. Budget is 0 here so the row asserts one call, not the retry count",
        ),
        (
            "an unseeded orchestrator that answered UNUSABLY",
            ORCHESTRATION_ONLY,
            None,
            None,
            rs.PROBE_ANSWER_UNKNOWN,
            1,
            False,
            False,
            None,
            "AN `unknown` WRITES NOTHING EITHER, and unlike the row above it BLOCKS. The pair is the "
            "clearest statement of the split: both leave the store empty because neither is a "
            "verdict, and they differ entirely in what the run does next",
        ),
    )

    def test_each_cache_state_costs_what_it_should_and_records_only_a_real_verdict(
        self,
    ):
        wrong = []
        for (
            case,
            plan_text,
            seed_text,
            seed_verdict,
            answer,
            expected_calls,
            expected_cached,
            expected_proceed,
            expected_stored,
            why,
        ) in self.CACHE_STATES:
            # A FRESH fixture per row: each needs its own temp repo, run dir and verdict store.
            row = ProbeCase("run")
            row.setUp()
            try:
                rel = row.write_plan("orc001.ipd.md", plan_text)
                state = row.state([row.item("orc001", rel)])
                if seed_text is not None:
                    rs.record_probe_verdict(
                        row.repo,
                        rs.probe_cache_digest(seed_text),
                        seed_verdict,
                        model="test/model",
                    )
                asker = _counting_asker(answer)
                decision, _err = row.gate(state, asker=asker, retry_budget=0)
                served = rs.read_probe_verdict(
                    row.repo, rs.probe_cache_digest(plan_text), model="test/model"
                )
            finally:
                row.doCleanups()
            problems = []
            if decision.calls != expected_calls:
                problems.append(
                    f"expected {expected_calls} model call(s), the gate spent {decision.calls}"
                )
            if len(asker.calls) != expected_calls:
                problems.append(
                    f"the double was called {len(asker.calls)} time(s), expected "
                    f"{expected_calls} (the gate's own count and the double's must agree)"
                )
            if not decision.outcomes:
                problems.append("the gate decided about NO orchestrator at all")
            elif decision.outcomes[0].cached is not expected_cached:
                problems.append(
                    f"expected the outcome's `cached` flag to be {expected_cached}, it was "
                    f"{decision.outcomes[0].cached}"
                )
            if decision.proceed is not expected_proceed:
                problems.append(
                    f"expected proceed={expected_proceed}, got {decision.proceed}"
                )
            if expected_stored is None:
                if served.is_hit:
                    problems.append(
                        f"the store MUST hold nothing for this digest, but it holds "
                        f"{served.verdict!r}: `not probed` has been turned into a stored fact"
                    )
            elif not served.is_hit:
                problems.append(
                    f"the store must hold {expected_stored!r} for this digest, but it holds nothing "
                    f"(stale_reason={served.stale_reason!r}), so the next run re-probes"
                )
            elif served.verdict != expected_stored:
                problems.append(
                    f"the store holds {served.verdict!r}, expected {expected_stored!r}"
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
            f"the verdict cache behaved wrongly for {len(wrong)} of {len(self.CACHE_STATES)} prior "
            "states. READ THE GROUPING. Both CACHED rows spending a call means the cache is not "
            "consulted first, which is loud (every run pays) but safe. Both UNSEEDED verdict rows "
            "storing nothing means the write-back broke, so the cache never populates. The dangerous "
            "failures are the other two: a cached `fail` that PROCEEDS means a recorded refusal is "
            "being ignored, and a `could-not-ask` or `unknown` that gets STORED means an outage or a "
            "confused model has been laundered into a verdict a later run will read as authority. "
            "FIX: `pass` and `fail` are answers and belong in the store; `unknown` and "
            f"`could-not-ask` are the ABSENCE of an answer and must never be written.\n"
            + "\n".join(wrong),
        )

    def test_a_MISS_is_never_read_as_a_pass(self):
        """Kept separate: a claim about the READER alone, with no gate and no plan on disk.

        "Not probed" and "probed and cleared" are different facts, and this asserts the reader's
        default for a digest nobody ever recorded. Every row above presumes it.
        """
        served = rs.read_probe_verdict(self.repo, "no-such-digest")
        self.assertEqual(served.verdict, rs.PROBE_VERDICT_UNKNOWN)
        self.assertFalse(served.is_hit)

    def test_a_could_not_ask_verdict_cannot_even_be_RECORDED(self):
        """Kept separate: an `assertRaises` over the writer's own refusal.

        The table above proves the gate does not write a `could-not-ask`; this proves the store would
        REFUSE it even if a caller tried, which is the durable half. A row cannot carry both a
        returned outcome and an exception type without a column meaningless to every other row.
        """
        for verdict in (
            rs.PROBE_ANSWER_COULD_NOT_ASK,
            rs.PROBE_VERDICT_UNKNOWN,
        ):
            with self.subTest(verdict=verdict), self.assertRaises(ValueError):
                rs.record_probe_verdict(self.repo, "d", verdict, model=None)


class TheProbeIsQueueScoped(ProbeCase):
    """E-04. `aw oc run all` must not sweep the repository's whole orchestrator corpus.

    ONE table replaces four tests. Each built a queue, called `queued_orchestrator_targets`, and
    asserted which id6s came back, differing only in what was in the queue versus on disk.

    Why the table beats the four: one filter answers every row (kind is `orchestrator`, the file
    resolves and reads, queue order preserved), so the realistic regression moves several rows at
    once. The rows are also ORDERED as a list rather than compared as a set, which is what makes the
    queue-order claim part of the same assertion instead of a fourth test.

    THE POPULATED ROWS AND THE EMPTY ROWS ARE IN ONE TABLE deliberately: a filter that returned
    NOTHING would satisfy every exclusion row on its own, and one that returned everything would
    satisfy the inclusion rows. Their failure message says which side is broken.
    """

    #: (case, the plans to write as [(filename, text)], the queue as [(id6, filename, kind,
    #: position)], the id6 list expected back IN ORDER, why this row exists)
    #:
    #: A filename of None in the queue means "point at a path no file was written to".
    SCOPES = (
        (
            "one queued orchestrator beside one that is only ON DISK",
            (
                ("orc001.ipd.md", ORCHESTRATION_ONLY),
                ("orc002.ipd.md", PARENT_ONLY_WORK),
            ),
            (("orc001", "orc001.ipd.md", "orchestrator", 1),),
            ["orc001"],
            "THE SCOPE CLAIM ITSELF: `aw oc run all` would otherwise make the probe's cost a function "
            "of the TREE rather than of the run. The unqueued plan is the parent-only fixture "
            "deliberately, so a sweep would not merely cost more, it would REFUSE a run over a plan "
            "nobody asked to execute",
        ),
        (
            "two queued orchestrators, in queue order",
            (
                ("orc001.ipd.md", ORCHESTRATION_ONLY),
                ("orc002.ipd.md", PARENT_ONLY_WORK),
            ),
            (
                ("orc001", "orc001.ipd.md", "orchestrator", 1),
                ("orc002", "orc002.ipd.md", "orchestrator", 2),
            ),
            ["orc001", "orc002"],
            "ORDER IS PART OF THE CONTRACT, not incidental: the gate reports the FIRST blocker, and "
            "the remedy it renders names that one orchestrator, so a reordered result would name the "
            "wrong plan in the message an operator acts on",
        ),
        (
            "a CHILD in the queue",
            (("child.ipd.md", ORCHESTRATION_ONLY),),
            (("chi001", "child.ipd.md", "child", 1),),
            [],
            "the question is about ORCHESTRATORS, since only they get retired without a pre-transition "
            "checkpoint. The fixture is a valid orchestrator BODY under a `child` kind, so this row "
            "proves the filter reads the queue item's kind and not the file's shape",
        ),
        (
            "a queued orchestrator whose file is ABSENT",
            (),
            (("gone01", None, "orchestrator", 1),),
            [],
            "SKIPPED RATHER THAN REFUSED: this function answers `what is in the queue`, and a plan the "
            "runner cannot even read is a different refusal the existing preflight already owns. A "
            "crash here would take down runs the preflight is meant to reject with a clear message",
        ),
    )

    def test_exactly_the_queued_readable_orchestrators_are_targeted_in_order(self):
        wrong = []
        for case, plans, queue, expected, why in self.SCOPES:
            row = ProbeCase("run")
            row.setUp()
            try:
                for name, text in plans:
                    row.write_plan(name, text)
                items = [
                    row.item(
                        id6,
                        f".aw/records/plans/pending/{name}"
                        if name is not None
                        else ".aw/records/plans/pending/absent.ipd.md",
                        kind=kind,
                        position=position,
                    )
                    for id6, name, kind, position in queue
                ]
                got = [
                    t.id6
                    for t in rs.queued_orchestrator_targets(
                        row.state(items), repo=row.repo
                    )
                ]
            finally:
                row.doCleanups()
            if got != expected:
                wrong.append(
                    f"  {case}:\n"
                    f"    - expected the targets {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`queued_orchestrator_targets` was wrong for {len(wrong)} of {len(self.SCOPES)} queues. "
            "ONE filter answers every row, so read which SIDE moved. The two EMPTY-expectation rows "
            "returning something means the filter widened: either a child is now probed (spending a "
            "call per child, on every run) or an unreadable plan crashes the gate instead of being "
            "left to the preflight. The two POPULATED rows going empty is the dangerous direction, "
            "because the gate then decides about NO orchestrator and every run proceeds having "
            "established nothing, which looks exactly like a clean run. FIX: an order-only failure on "
            "the two-orchestrator row is not cosmetic; the rendered remedy names the FIRST blocker, so "
            f"a reordering makes the message name the wrong plan.\n" + "\n".join(wrong),
        )


# ==================================================================================================
# E-05 / V-05: the gate's three paths
# ==================================================================================================


class TheGateHasThreePaths(ProbeCase):
    """E-05/E-06/E-10. Every way the gate can decide, and the SPECIFIC outcome each one reports.

    ONE table replaces NINE tests spread over three classes (`TheGateHasThreePaths`,
    `TheRefusalIsDURABLE`, and the availability half of `TheCouldNotAskPathDoesNotBlock`). Every one
    drove the REAL `enforce_orchestrator_probe_gate` over one fixture with one answer and asserted some
    subset of: did it proceed, how many calls, was it warned past, what refusal code landed on the
    item, what the event says, what the recorded justification says. Those are FACETS OF ONE DECISION,
    and splitting them let each test assert the two or three facets its author happened to care about.

    EVERY VERDICT AND EVERY ADMISSION PATH KEEPS ITS OWN ROW, ASSERTING THE SPECIFIC OUTCOME REPORTED.
    This is the rule that governs this file: a fail-closed gate is not tested by "it refused". So the
    rows separate (a) a clean CLEAR, (b) a refusal because the model found work, (c) a refusal because
    the model answered UNUSABLY, (d) a proceed-with-a-KNOWN-HOLE because the host could not be asked,
    (e) an override by FLAG carrying its justification, (f) an override by the exact INTERACTIVE
    phrase, (g) a refusal because the interactive answer was NOT the phrase, (h) a refusal because the
    flag carried no real justification, and (i) a run with no queued orchestrator at all. Each pins the
    REFUSAL CODE, because `orchestrator-uncovered-work` and `orchestrator-probe-unavailable` are
    different facts an operator acts on differently, and a gate that recorded the wrong one is broken
    in the way that matters even though `proceed` is right.

    THE CLEAN ROWS ARE IN THE SAME TABLE and they carry real weight here: a gate that refused
    everything would satisfy rows (b), (c), (g) and (h) on its own. Their failure message says the
    refusal rows are vacuous while a clear is broken.

    WHAT THIS TABLE DOES NOT COVER, each kept as its own test below with a reason: the retry COUNT (it
    needs a call-counting double and asserts a number, not a decision), the no-TTY-no-prompt claim (it
    asserts a collaborator was NOT invoked), the absence of sessions and worktrees (a claim about the
    filesystem), and both hosts driven through the real `initialize_run` (a materially different
    setup).
    """

    #: (case, the plan text, the answer the double returns, the retry budget, the `interactive` flag,
    #: the canned `response` or None when none is supplied, the override justification or None,
    #: expected `proceed`, expected `warned_past`, the refusal code expected ON DISK or None for no
    #: refusal at all, a substring the recorded justification must carry or None, a substring stderr
    #: must carry or None, why this row exists)
    #:
    #: THE REFUSAL CODES ARE LITERAL STRINGS, NOT `rs.PROBE_*_CODE`, AND THAT IS DELIBERATE. Measured
    #: while mutation-verifying this table: SWAPPING the two codes at their definitions (setting
    #: `PROBE_UNAVAILABLE_CODE` to `"orchestrator-uncovered-work"`) left a constant-referencing version
    #: of this table GREEN on all 40 tests, because the constant and the reported value move together.
    #: These codes are a published interface: `aw runs` renders them, the end-of-run summary keys on
    #: them, and an operator's next action depends on WHICH one they see, so a renumbering or a
    #: collapse is a breaking change that must fail here. Do not "tidy" these into constants.
    DECISIONS = (
        (
            "an orchestration-only parent the model CLEARS",
            ORCHESTRATION_ONLY,
            rs.PROBE_ANSWER_NO_EXECUTIONS,
            0,
            False,
            None,
            None,
            True,
            False,
            None,
            None,
            None,
            "THE FALSE-POSITIVE SIDE, and the corpus is overwhelmingly this shape: every live "
            "orchestrator carries items and most carry only sequencing. Every refusal row below is "
            "vacuous while this one is broken, because a gate that refuses everything satisfies all "
            "of them and would simply be switched off by the operator",
        ),
        (
            "a parent-only-work parent the model FLAGS",
            PARENT_ONLY_WORK,
            rs.PROBE_ANSWER_EXECUTIONS,
            0,
            False,
            None,
            None,
            False,
            False,
            "orchestrator-uncovered-work",
            None,
            None,
            "THE GATE'S PRIMARY REFUSAL: unattended, it FAILS. The code must be "
            "`orchestrator-uncovered-work` specifically, because that is what says the parent carries "
            "work no child covers, and the remedy keyed to it tells the operator to ADD A CHILD",
        ),
        (
            "a parent the model answered UNUSABLY about",
            ORCHESTRATION_ONLY,
            rs.PROBE_ANSWER_UNKNOWN,
            0,
            False,
            None,
            None,
            False,
            False,
            "orchestrator-uncovered-work",
            None,
            None,
            "AN `unknown` BLOCKS, and it lands on the SAME code as a real finding, which is a "
            "deliberate design choice worth pinning: the run is treated as though the work were "
            "uncovered because a confused model is not evidence of safety. The fixture is the "
            "ORCHESTRATION-ONLY one, so this row cannot pass by the plan genuinely carrying work",
        ),
        (
            "a host that COULD NOT BE ASKED",
            ORCHESTRATION_ONLY,
            rs.PROBE_ANSWER_COULD_NOT_ASK,
            0,
            False,
            None,
            None,
            True,
            True,
            "orchestrator-probe-unavailable",
            None,
            "KNOWN HOLE",
            "THE OPPOSITE DECISION FROM THE ROW ABOVE ON A DIFFERENT CODE, which is the whole of the "
            "maintainer's OQ-02 ruling in one row: a model outage must not halt a run that is "
            "otherwise fine, so it PROCEEDS, it is marked `warned_past`, and it records "
            "`orchestrator-probe-unavailable` rather than the refusal code. The two codes are "
            "different facts: one says this parent carries uncovered work, the other says nobody "
            "established whether it does",
        ),
        (
            "an override by FLAG with a real justification",
            PARENT_ONLY_WORK,
            rs.PROBE_ANSWER_EXECUTIONS,
            0,
            False,
            None,
            "accepted: E-02 is covered by a child landing tomorrow",
            True,
            False,
            "orchestrator-uncovered-work",
            "covered by a child landing tomorrow",
            "OVERRIDDEN",
            "THE OVERRIDE CARRIES ITS REASON, NOT A BOOLEAN. The run proceeds AND the refusal is still "
            "recorded, which is the point: a bare boolean would record that somebody clicked past the "
            "gate and nothing about whether they should have. The justification must be readable "
            "verbatim afterwards",
        ),
        (
            "an override by the EXACT interactive phrase",
            PARENT_ONLY_WORK,
            rs.PROBE_ANSWER_EXECUTIONS,
            0,
            True,
            rs.PROBE_CONFIRM_PHRASE,
            None,
            True,
            False,
            "orchestrator-uncovered-work",
            "interactive",
            "OVERRIDDEN",
            "AN INTERACTIVE CONSENT IS STILL AN OVERRIDE AND IS RECORDED AS ONE, labelled "
            "`interactive` so an operator who typed the phrase at 03:00 is distinguishable in the "
            "record from a run nobody gated at all",
        ),
        (
            "an interactive answer that is NOT the phrase",
            PARENT_ONLY_WORK,
            rs.PROBE_ANSWER_EXECUTIONS,
            0,
            True,
            "y",
            None,
            False,
            False,
            "orchestrator-uncovered-work",
            None,
            None,
            "`y` IS NOT CONSENT. The phrase is exact and compared in one place (the shipped "
            "`run drafts` / `RUN-MIXED-TYPES` precedent), because a reflexive `y` is what an operator "
            "types to a gate they have stopped reading",
        ),
        (
            "an EMPTY interactive answer",
            PARENT_ONLY_WORK,
            rs.PROBE_ANSWER_EXECUTIONS,
            0,
            True,
            "",
            None,
            False,
            False,
            "orchestrator-uncovered-work",
            None,
            None,
            "a bare RETURN is the most likely accidental input of all, and it must refuse. Kept "
            "distinct from `y` because an empty string reaches different branches of any real "
            "comparison and a falsy-check bug would treat it as no answer at all",
        ),
        (
            "a flag carrying only WHITESPACE",
            PARENT_ONLY_WORK,
            rs.PROBE_ANSWER_EXECUTIONS,
            0,
            False,
            None,
            "   ",
            False,
            False,
            "orchestrator-uncovered-work",
            None,
            None,
            "A BARE FLAG MUST NOT CLEAR THE GATE. argparse already requires a value, so whitespace is "
            "how the requirement gets defeated in practice; the gate strips and refuses, which is what "
            "makes the recorded justification worth reading",
        ),
        (
            "a run with NO queued orchestrator at all",
            ORCHESTRATION_ONLY,
            rs.PROBE_ANSWER_EXECUTIONS,
            0,
            False,
            None,
            None,
            True,
            False,
            None,
            None,
            None,
            "THE ZERO-COST ROW: a queue of children must spend nothing and proceed. The double is "
            "rigged to BLOCK, so a gate that probed anyway would refuse a run containing no "
            "orchestrator, and the `calls == 0` check below is what proves nothing was asked. The "
            "plan is enqueued as a `child`",
        ),
    )

    def test_every_decision_path_reports_its_own_specific_outcome(self):
        wrong = []
        for (
            case,
            plan_text,
            answer,
            budget,
            interactive,
            response,
            justification,
            expected_proceed,
            expected_warned,
            expected_code,
            justification_needle,
            stderr_needle,
            why,
        ) in self.DECISIONS:
            kind = "child" if "NO queued orchestrator" in case else "orchestrator"
            row = ProbeCase("run")
            row.setUp()
            try:
                rel = row.write_plan("orc002.ipd.md", plan_text)
                state = row.state([row.item("orc002", rel, kind=kind)])
                asker = _counting_asker(answer)
                kwargs: dict = {
                    "asker": asker,
                    "retry_budget": budget,
                    "interactive": interactive,
                    "override_justification": justification,
                }
                if response is not None:
                    kwargs["response"] = response
                decision, err = row.gate(state, **kwargs)
                on_disk = (
                    json.loads((row.run_dir / "state.json").read_text(encoding="utf-8"))
                    if (row.run_dir / "state.json").is_file()
                    else None
                )
                events = [
                    e
                    for e in row.events()
                    if e.get("event") == "orchestrator-probe-gate"
                ]
            finally:
                row.doCleanups()
            problems = []
            if decision.proceed is not expected_proceed:
                problems.append(
                    f"expected proceed={expected_proceed}, got {decision.proceed} "
                    f"(message was {decision.message[:160]!r})"
                )
            if decision.warned_past is not expected_warned:
                problems.append(
                    f"expected warned_past={expected_warned}, got {decision.warned_past}"
                )
            # THE REFUSAL CODE, read back THE WAY A READER DOES rather than by dict key: through the
            # shared `render_stream` reader that `aw runs` itself uses, so a refusal recorded in a
            # shape no reader understands fails here.
            recorded = (
                render_stream.refusal_of_item(on_disk["queue"][0])
                if on_disk is not None
                else None
            )
            if expected_code is None:
                if recorded is not None:
                    problems.append(
                        f"no refusal may be recorded, but the item carries {recorded.code!r}: "
                        f"{recorded.reason[:120]!r}"
                    )
            elif recorded is None:
                problems.append(
                    f"expected the refusal code {expected_code!r} to be DURABLE on the queue item "
                    "(readable through `render_stream.refusal_of_item` after the process exits), but "
                    "nothing was recorded"
                )
            elif recorded.code != expected_code:
                problems.append(
                    f"expected the refusal code {expected_code!r}, got {recorded.code!r}. The two "
                    "codes are different FACTS and an operator acts on them differently"
                )
            elif "orc002" not in recorded.reason:
                problems.append(
                    f"the recorded reason must NAME the orchestrator (`orc002`); it said "
                    f"{recorded.reason[:160]!r}"
                )
            stored = (on_disk or {}).get("options", {}).get(
                "allow_uncovered_orchestrator_work"
            ) or ""
            if justification_needle is not None:
                if justification_needle not in stored:
                    problems.append(
                        f"the recorded justification must carry {justification_needle!r}; run state "
                        f"holds {stored!r}"
                    )
                if justification_needle not in (decision.override_justification or ""):
                    problems.append(
                        f"the returned decision must carry the justification "
                        f"{justification_needle!r}; it said "
                        f"{decision.override_justification!r}"
                    )
            else:
                # NO NON-OVERRIDE ROW MAY RECORD ONE. A justification written for a decision nobody
                # overrode would read, later, as a human having accepted a risk they never saw.
                if stored:
                    problems.append(
                        "run state records an override justification for a decision that is NOT an "
                        f"override: {stored!r}"
                    )
                if decision.override_justification:
                    problems.append(
                        "the returned decision carries an override justification for a decision "
                        f"that is not an override: {decision.override_justification!r}"
                    )
            if stderr_needle is not None and stderr_needle not in err:
                problems.append(
                    f"stderr must carry {stderr_needle!r} so the operator sees it live; it said "
                    f"{err[:200]!r}"
                )
            # THE EVENT, which is what `aw runs` and any later audit read.
            if len(events) != 1:
                problems.append(
                    f"the gate must record EXACTLY ONE `orchestrator-probe-gate` event; it recorded "
                    f"{len(events)}"
                )
            elif events[0].get("proceed") is not expected_proceed:
                problems.append(
                    f"the recorded event says proceed={events[0].get('proceed')!r}, but the decision "
                    f"was {expected_proceed}: the durable record and the return value DISAGREE"
                )
            if kind == "child" and (decision.calls != 0 or asker.calls):
                problems.append(
                    f"a queue with no orchestrator must spend NOTHING; the gate spent "
                    f"{decision.calls} and the double saw {len(asker.calls)} call(s)"
                )
            if problems:
                wrong.append(
                    f"  {case} (answer={answer!r}, interactive={interactive}, "
                    f"response={response!r}, justification={justification!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the gate decided wrongly in {len(wrong)} of {len(self.DECISIONS)} paths. READ THE "
            "GROUPING, because each pattern is a different defect. If a CLEAR row is among the "
            "failures, every refusal row is vacuous and the gate is refusing runs it must admit, "
            "which gets it overridden reflexively. If the two CODES were swapped, `proceed` may still "
            "be right while the operator is told the wrong thing: `orchestrator-uncovered-work` means "
            "this parent carries work no child covers and the fix is to ADD A CHILD, while "
            "`orchestrator-probe-unavailable` means nobody established whether it does and the fix is "
            "to re-run once the host is reachable. If every OVERRIDE row now refuses, an operator has "
            "no way past a false positive; if the WHITESPACE or `y` rows now proceed, the gate can be "
            "cleared by an accident. The most dangerous single failure is a refusal row that PROCEEDS "
            "with no recorded refusal, because the parent's own items are then reported complete "
            "having never been performed or verified, which is the exact outcome this gate exists to "
            f"prevent.\n" + "\n".join(wrong),
        )

    def test_the_prompt_is_only_asked_when_a_TTY_was_established_by_the_caller(self):
        """Kept separate: asserts a collaborator was NOT invoked, which no outcome row can state.

        No TTY means no prompt and no waiting, EVER (the shipped `_lane_reclaim_prompt` rule). The
        table's unattended rows prove the gate REFUSES; this proves it did not first block on a human
        who is not there.
        """
        asked: list = []

        def prompt(question):
            asked.append(question)
            return None

        rel = self.write_plan("orc002.ipd.md", PARENT_ONLY_WORK)
        self.gate(
            self.state([self.item("orc002", rel)]),
            interactive=False,
            prompt=prompt,
            asker=_counting_asker(rs.PROBE_ANSWER_EXECUTIONS),
        )
        self.assertEqual(asked, [])

    def test_on_a_TTY_the_question_itself_carries_the_reason_and_the_remedy(self):
        """Kept separate: asserts what was ASKED, not what was decided.

        When no `response` is canned the gate must compose the prompt from the same reason and remedy
        it would refuse with, so a human is deciding from the prompt alone. The table's interactive
        rows supply a canned answer and therefore never exercise the composer.
        """
        asked: list = []

        def prompt(question):
            asked.append(question)
            return rs.PROBE_CONFIRM_PHRASE

        rel = self.write_plan("orc002.ipd.md", PARENT_ONLY_WORK)
        decision, _err = self.gate(
            self.state([self.item("orc002", rel)]),
            interactive=True,
            prompt=prompt,
            asker=_counting_asker(rs.PROBE_ANSWER_EXECUTIONS),
        )
        self.assertTrue(decision.proceed)
        self.assertEqual(len(asked), 1)
        self.assertIn("orc002", asked[0])
        self.assertIn("ADD A CHILD", asked[0])
        self.assertIn(rs.PROBE_CONFIRM_PHRASE, asked[0])


class TheRefusalIsDURABLE(ProbeCase):
    """E-05/E-06. Criterion 3: the reason survives the process, not only the scrollback.

    THE CODE-AND-REASON HALF OF THIS CLASS IS NOW A COLUMN in `TheGateHasThreePaths.DECISIONS`, where
    every row reads its refusal back through `render_stream.refusal_of_item` (the same reader `aw runs`
    uses) and pins the code, and every row checks the event's `proceed` against the returned decision.
    What remains here is what a decision row cannot state.

    THE EVENT'S PAYLOAD IS A TABLE, because the event is the machine-readable record: a later audit
    keys on `blocking`, `probed`, `calls`, `override` and `justification`, and the realistic failure is
    a field being dropped or renamed while `proceed` stays correct. The decision table already pins
    `proceed` per row, so this one pins the FIELDS.
    """

    #: (case, the override justification or None, the event fields that must match EXACTLY as
    #: (key, value) pairs, the keys that must be ABSENT, why this row exists)
    EVENT_SHAPES = (
        (
            "an unattended refusal",
            None,
            (
                ("proceed", False),
                ("blocking", ["orc002"]),
                ("probed", ["orc002"]),
                ("calls", 1),
            ),
            ("override", "justification"),
            "THE AUDIT RECORD OF A REFUSAL. `blocking` must name WHICH orchestrator, since a refusal "
            "naming none is unactionable, and `probed` must show the gate actually asked. The override "
            "keys must be ABSENT rather than false, so a reader cannot mistake a refusal for a "
            "consented launch",
        ),
        (
            "a flag override",
            "maintainer accepted 2026-09-19",
            (
                ("proceed", True),
                ("override", "flag"),
                ("justification", "maintainer accepted 2026-09-19"),
                ("blocking", ["orc002"]),
            ),
            (),
            "THE OVERRIDE'S RECORD IS THE WHOLE VALUE OF REQUIRING A REASON: it must carry the "
            "justification VERBATIM and still name what was blocking, so a later reader can tell an "
            "accepted risk from an unnoticed one AND see what was accepted. `override: flag` "
            "distinguishes it from the interactive path",
        ),
        (
            "an interactive consent",
            None,
            (("proceed", True), ("override", "interactive"), ("blocking", ["orc002"])),
            (),
            "THE THIRD PATH, tagged distinctly: an operator who typed the phrase at 03:00 must be "
            "distinguishable in the record from a flag passed deliberately in a script, because the "
            "two carry different amounts of thought",
        ),
    )

    def test_the_recorded_event_carries_every_field_an_audit_reads(self):
        wrong = []
        for case, justification, expected_fields, absent_keys, why in self.EVENT_SHAPES:
            row = ProbeCase("run")
            row.setUp()
            try:
                rel = row.write_plan("orc002.ipd.md", PARENT_ONLY_WORK)
                kwargs: dict = {
                    "asker": _counting_asker(rs.PROBE_ANSWER_EXECUTIONS),
                    "override_justification": justification,
                }
                if case == "an interactive consent":
                    kwargs["interactive"] = True
                    kwargs["response"] = rs.PROBE_CONFIRM_PHRASE
                row.gate(row.state([row.item("orc002", rel)]), **kwargs)
                events = [
                    e
                    for e in row.events()
                    if e.get("event") == "orchestrator-probe-gate"
                ]
            finally:
                row.doCleanups()
            problems = []
            if len(events) != 1:
                problems.append(
                    f"expected exactly one `orchestrator-probe-gate` event, got {len(events)}"
                )
            else:
                event = events[0]
                for key, value in expected_fields:
                    if key not in event:
                        problems.append(
                            f"the event has no {key!r} key; its keys are {sorted(event)}"
                        )
                    elif event[key] != value:
                        problems.append(
                            f"the event's {key!r} is {event[key]!r}, expected {value!r}"
                        )
                for key in absent_keys:
                    if key in event:
                        problems.append(
                            f"the event must NOT carry {key!r} for this path; it holds "
                            f"{event[key]!r}"
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
            f"the gate's recorded event was wrong for {len(wrong)} of {len(self.EVENT_SHAPES)} paths. "
            "ONE emitter writes all three, so several rows losing the same KEY means a field was "
            "renamed or dropped and every consumer of this event breaks at once, silently, since the "
            "run itself still decides correctly. FIX: the event is the only record that survives once "
            "the scrollback is gone, so a missing `blocking` makes a refusal unactionable and a "
            "missing `justification` erases the reason a human accepted the risk. A path that gained "
            "an `override` key it should not have is the worst case: a refused run would then read, "
            f"afterwards, as one somebody consented to.\n" + "\n".join(wrong),
        )

    def test_a_refusal_rewrites_the_report_so_aw_runs_renders_it(self):
        """Kept separate: asserts a COLLABORATOR was invoked, not a value the gate returned.

        `write_report_fn` is what makes the refusal visible in `aw runs` rather than only in
        `state.json`. No outcome row can state that a callback ran.
        """
        rel = self.write_plan("orc002.ipd.md", PARENT_ONLY_WORK)
        saved: list = []
        self.gate(
            self.state([self.item("orc002", rel)]),
            asker=_counting_asker(rs.PROBE_ANSWER_EXECUTIONS),
            write_report_fn=lambda rd, st: saved.append(rd),
        )
        self.assertTrue(
            saved, "the report must be rewritten so `aw runs` renders the refusal"
        )

    def test_a_refusal_leaves_NO_session_and_NO_worktree_behind(self):
        """Kept separate: a claim about the FILESYSTEM and about absent state keys.

        "Costs nothing" means no agent turn, no lane, no session - not "no run directory". The
        assertions are over what does NOT exist, which is a different shape from every decision row.
        """
        rel = self.write_plan("orc002.ipd.md", PARENT_ONLY_WORK)
        state = self.state([self.item("orc002", rel)])
        self.gate(state, asker=_counting_asker(rs.PROBE_ANSWER_EXECUTIONS))
        sessions = self.run_dir / "sessions"
        self.assertFalse(sessions.exists() and any(sessions.iterdir()))
        on_disk = json.loads((self.run_dir / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["queue"][0]["attempts"], [])
        self.assertNotIn("worktree", on_disk["queue"][0])


class TheRefusalNamesAddAChild(ProbeCase):
    """E-06. THE WORDING IS THE DELIVERABLE: a prohibition gets complied with by DELETION.

    ONE table replaces four tests (`names_the_CONSTRUCTIVE_action_first`,
    `explicitly_tells_the_reader_NOT_to_delete_the_parents_items`,
    `does_NOT_read_as_a_bare_prohibition`, `names_the_override`). Each asked for the same rendered
    remedy and asserted one substring's presence, absence, or position.

    Why the table beats the four: this is ONE composed string, so a rewording that loses several of
    these properties at once is the realistic failure, and four tests report it as four unrelated
    `assertIn` failures each dumping the whole paragraph. The table reports one failure naming exactly
    which properties the new wording lost, which is what a person rewording it needs.

    THE REASON THIS WORDING IS TESTED AT ALL, restated because it is the only thing that justifies
    pinning prose: `AGENTS.md` records the MEASURED failure mode that a message saying only "an
    orchestrator must not contain executions" gets complied with by DELETION of the parent's checklist,
    and that checklist is what makes `execute <setid>` complete when no runner is involved. So the
    remedy's job is to redirect an agent toward adding a child, and the forbidden-phrase rows are as
    load-bearing as the required ones.

    BOTH HOSTS ARE A COLUMN, so every property is asserted for both renderings. That is stricter than
    the tests it replaces, which only ever rendered the `oc` variant while a separate identity test
    compared the two.
    """

    #: (case, the substring, the check mode, why this row exists)
    #:
    #: Check modes: `in` (must be present), `not-in` (must be absent), `leads` (present AND in the
    #: first half, so it cannot be a trailing afterthought).
    WORDING = (
        (
            "the constructive action, LEADING",
            "ADD A CHILD",
            "leads",
            "THE ENTIRE DELIVERABLE. It must LEAD rather than trail a prohibition, because an agent "
            "acting on a message it skimmed acts on the first instruction it found. This is the row "
            "that encodes the measured failure: a prohibition-first message gets complied with by "
            "deleting the very checklist that makes a Set execute completely",
        ),
        (
            "the explicit instruction not to delete",
            "Do NOT delete",
            "in",
            "NAMING THE CONSTRUCTIVE ACTION IS NOT ENOUGH, because deleting the items also makes the "
            "complaint go away and is a smaller edit. The prohibition has to be present too; it just "
            "must not be the whole message",
        ),
        (
            "what must not be deleted, by name",
            "checklist",
            "in",
            "`Do NOT delete` alone leaves ambiguous WHAT: the parent's checklist is the thing, and "
            "saying so is what connects the instruction to the consequence",
        ),
        (
            "the override flag",
            "--allow-uncovered-orchestrator-work",
            "in",
            "an operator who has decided to accept the risk must not be left guessing the spelling. A "
            "gate with no visible way past it gets worked around by editing the plan, which is the "
            "deletion this whole message exists to prevent",
        ),
        (
            "the bare-prohibition phrasing `must not contain executions`",
            "must not contain executions",
            "not-in",
            "THE EXACT SENTENCE THAT WAS MEASURED TO CAUSE DELETION. It is forbidden outright rather "
            "than merely deprecated, because the wording is the deliverable and this is the wording "
            "that failed",
        ),
        (
            "the bare-prohibition phrasing `cannot have executions`",
            "cannot have executions",
            "not-in",
            "the same message in the other voice. Kept as its own row so a reworded prohibition cannot "
            "slip in by avoiding one literal spelling",
        ),
        (
            "the bare-prohibition phrasing `is not allowed`",
            "is not allowed",
            "not-in",
            "the generic form, which is the most likely thing a well-meaning rewrite reaches for and "
            "which carries no instruction at all",
        ),
    )

    def test_the_remedy_redirects_toward_adding_a_child_on_both_hosts(self):
        wrong = []
        for host, labels in (("oc", rs.OC_HOST_LABELS), ("agy", rs.AGY_HOST_LABELS)):
            remedy = rs.probe_refusal_remedy(labels, "orc002")
            for case, needle, mode, why in self.WORDING:
                problems = []
                if mode == "not-in":
                    if needle in remedy:
                        problems.append(
                            f"the remedy contains the bare-prohibition phrasing {needle!r}"
                        )
                else:
                    if needle not in remedy:
                        problems.append(f"the remedy is missing {needle!r}")
                    elif mode == "leads" and remedy.index(needle) >= len(remedy) // 2:
                        problems.append(
                            f"{needle!r} appears at offset {remedy.index(needle)} of "
                            f"{len(remedy)}, i.e. in the SECOND half: the constructive action must "
                            "lead, not trail a prohibition"
                        )
                if problems:
                    wrong.append(
                        f"  {case} (host={host!r}):\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"the refusal remedy lost {len(wrong)} of {2 * len(self.WORDING)} wording properties "
            "(each checked on BOTH hosts). ONE composing function renders both, so a property failing "
            "on both hosts means the wording was rewritten, while failing on ONE means the renderings "
            "have been forked and only one was updated. FIX: this prose is pinned for a measured "
            "reason recorded in `AGENTS.md`. A message that says only what an orchestrator must NOT "
            "contain gets complied with by DELETING the parent's checklist, and that checklist is what "
            "makes `execute <setid>` complete when no runner is involved, so the prohibition-only "
            "wording causes exactly the lost work this gate exists to prevent. Reword freely, but keep "
            f"the constructive action first and keep the flag visible.\n"
            + "\n".join(wrong),
        )

    def test_the_remedy_reaches_the_run_SUMMARY_through_child_01s_renderer(self):
        """Kept separate: drives the real gate and a DIFFERENT subject (the summary renderer).

        The table above is about the composed string; this is about the string reaching the surface a
        human actually reads at the end of a run, which requires a gate decision and a rendered table.
        """
        rel = self.write_plan("orc002.ipd.md", PARENT_ONLY_WORK)
        state = self.state([self.item("orc002", rel)])
        self.gate(state, asker=_counting_asker(rs.PROBE_ANSWER_EXECUTIONS))
        rendered = render_stream.render_run_summary_table(
            state, self.run_dir, pal=render_stream.Palette(False)
        )
        self.assertIn("ADD A CHILD", rendered)
        self.assertIn("remedy", rendered)

    def test_the_unavailable_remedy_says_what_is_UNVERIFIED_rather_than_what_to_fix(
        self,
    ):
        """Kept separate: a DIFFERENT function with a different job, on both hosts.

        `probe_unavailable_remedy` answers a question nobody can fix by editing a plan, so it must not
        say ADD A CHILD; it must name the KNOWN HOLE and tell the reader to re-run once the host is
        reachable. Keeping it here rather than as a row in the table above is deliberate: every row
        there would be wrong for this string.
        """
        for labels, command in (
            (rs.OC_HOST_LABELS, "aw oc run"),
            (rs.AGY_HOST_LABELS, "aw agy run"),
        ):
            with self.subTest(command=command):
                remedy = rs.probe_unavailable_remedy(labels)
                self.assertIn("KNOWN HOLE", remedy)
                self.assertIn("UNVERIFIED", remedy)
                self.assertIn(command, remedy)
                self.assertNotIn("ADD A CHILD", remedy)


# ==================================================================================================
# E-10 / V-10: availability
# ==================================================================================================


class TheCouldNotAskPathDoesNotBlock(ProbeCase):
    """E-10. HOW MANY TIMES an unusable outcome is asked, per answer and per budget.

    ONE table replaces three tests (`it_is_retried_to_the_budget_and_then_PROCEEDS`,
    `a_budget_of_zero_asks_exactly_once`, `an_unknown_still_BLOCKS_and_is_NOT_retried_past`). Each ran
    the gate with one budget against one answer and asserted the resulting call COUNT, so the BUDGET
    and the ANSWER are columns.

    THE TWO UNUSABLE ANSWERS MUST BE IN ONE TABLE, which is the argument for tabulating exactly here.
    The property worth stating is not "a retry budget is honored" but that the budget applies to a
    `could-not-ask` and NOT to an `unknown`, and only adjacent rows differing solely in the answer can
    say that. Split apart, a gate that retried everything would leave the `could-not-ask` tests green
    while the `unknown` one failed as an unrelated count, which reads like an off-by-one rather than
    like a fail-closed gate being talked into passing.

    THE DECISION IS ASSERTED ALONGSIDE THE COUNT on every row, because a count alone cannot
    distinguish "retried and then warned past" from "retried and then refused anyway". The verdict-
    and-code half of these paths is covered per-row in `TheGateHasThreePaths.DECISIONS`; this table
    owns the COST.
    """

    def unreachable_asker(self):
        calls: list = []

        def asker(state, excerpt, *, host, repo, runner=None):
            calls.append(excerpt)
            return rs.PROBE_ANSWER_COULD_NOT_ASK, "the host binary is not on PATH"

        asker.calls = calls  # type: ignore[attr-defined]
        return asker

    #: (case, the answer the double returns, the retry budget passed, expected total asks, expected
    #: `proceed`, expected `warned_past`, substrings stderr must carry, why this row exists)
    BUDGETS = (
        (
            "could-not-ask with a budget of 2",
            rs.PROBE_ANSWER_COULD_NOT_ASK,
            2,
            3,
            True,
            True,
            ("WARNING", "KNOWN HOLE"),
            "THE INITIAL ATTEMPT PLUS THE BUDGET, which is what `a budget of retries` means and is the "
            "off-by-one worth pinning. A transient outage is the case retrying actually helps, and the "
            "run must then PROCEED loudly rather than halt",
        ),
        (
            "could-not-ask with a budget of 0",
            rs.PROBE_ANSWER_COULD_NOT_ASK,
            0,
            1,
            True,
            True,
            ("WARNING", "KNOWN HOLE"),
            "A BUDGET OF ZERO STILL ASKS ONCE: zero RETRIES is not zero attempts. A gate that asked "
            "nothing here would warn past every run having never contacted the host, which looks "
            "identical in the logs to an outage",
        ),
        (
            "could-not-ask with a budget of 1",
            rs.PROBE_ANSWER_COULD_NOT_ASK,
            1,
            2,
            True,
            True,
            ("WARNING", "KNOWN HOLE"),
            "the third point is what makes this a LINE rather than two special cases: with 0, 1 and 2 "
            "all pinned, a gate that ignored the budget or doubled it cannot satisfy the table",
        ),
        (
            "unknown with a budget of 5",
            rs.PROBE_ANSWER_UNKNOWN,
            5,
            1,
            False,
            False,
            (),
            "THE ROW THE WHOLE TABLE EXISTS FOR: an `unknown` is asked ONCE even with a generous "
            "budget, and it BLOCKS. Retrying a confused model is precisely how a fail-closed gate is "
            "talked into passing, since each retry is another chance to roll the clean answer. Note "
            "the fixture is the orchestration-only one, so the refusal cannot come from the plan",
        ),
        (
            "a real verdict with a budget of 5",
            rs.PROBE_ANSWER_NO_EXECUTIONS,
            5,
            1,
            True,
            False,
            (),
            "THE CLEAN ROW: a usable answer is asked once and never retried, and the run proceeds "
            "WITHOUT being marked warned-past. Without it, every row above is satisfied by a gate that "
            "retries on success too, and a `warned_past` flag set on a clean run would make the "
            "end-of-run report claim a hole that does not exist",
        ),
    )

    def test_only_a_could_not_ask_is_retried_and_only_to_the_budget(self):
        wrong = []
        for (
            case,
            answer,
            budget,
            expected_asks,
            expected_proceed,
            expected_warned,
            stderr_needles,
            why,
        ) in self.BUDGETS:
            row = ProbeCase("run")
            row.setUp()
            try:
                rel = row.write_plan("orc001.ipd.md", ORCHESTRATION_ONLY)
                asker = (
                    self.unreachable_asker()
                    if answer == rs.PROBE_ANSWER_COULD_NOT_ASK
                    else _counting_asker(answer)
                )
                decision, err = row.gate(
                    row.state([row.item("orc001", rel)]),
                    asker=asker,
                    retry_budget=budget,
                )
            finally:
                row.doCleanups()
            problems = []
            if len(asker.calls) != expected_asks:
                problems.append(
                    f"expected {expected_asks} ask(s) for a budget of {budget}, the gate made "
                    f"{len(asker.calls)}"
                )
            if decision.calls != expected_asks:
                problems.append(
                    f"the decision reports {decision.calls} call(s) but the double saw "
                    f"{len(asker.calls)}: the gate's own accounting disagrees with reality"
                )
            if decision.proceed is not expected_proceed:
                problems.append(
                    f"expected proceed={expected_proceed}, got {decision.proceed}"
                )
            if decision.warned_past is not expected_warned:
                problems.append(
                    f"expected warned_past={expected_warned}, got {decision.warned_past}"
                )
            for needle in stderr_needles:
                if needle not in err:
                    problems.append(
                        f"stderr must carry {needle!r} so the hole is visible live; it said "
                        f"{err[:200]!r}"
                    )
            if not stderr_needles and ("WARNING" in err or "KNOWN HOLE" in err):
                problems.append(
                    f"stderr must NOT warn about a hole on this path; it said {err[:200]!r}"
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
            f"the retry behavior was wrong for {len(wrong)} of {len(self.BUDGETS)} (answer, budget) "
            "pairs. READ WHICH ROWS MOVED TOGETHER. All three COULD-NOT-ASK rows being off by the same "
            "amount means the loop's bound changed (a budget of N must mean N retries AFTER the first "
            "attempt); one of them alone means that specific bound is special-cased. THE DANGEROUS "
            "FAILURE IS THE `unknown` ROW GAINING RETRIES, because retrying a confused model is how a "
            "fail-closed gate is talked into passing: each extra ask is another chance to roll the "
            "answer that clears the run. A clean row that gains retries merely spends money, and a "
            "clean row marked `warned_past` makes the end-of-run report claim a hole that does not "
            f"exist.\n" + "\n".join(wrong),
        )

    def test_the_KNOWN_HOLE_is_durable_and_readable_after_the_process_exits(self):
        """Kept separate: asserts the REASON and REMEDY text of the recorded refusal, not a count.

        `TheGateHasThreePaths.DECISIONS` pins the CODE for this path; this pins the words a human
        reads, which is what makes the hole actionable rather than merely flagged.
        """
        rel = self.write_plan("orc001.ipd.md", ORCHESTRATION_ONLY)
        state = self.state([self.item("orc001", rel)])
        self.gate(state, asker=self.unreachable_asker(), retry_budget=1)
        on_disk = json.loads((self.run_dir / "state.json").read_text(encoding="utf-8"))
        refusal = render_stream.refusal_of_item(on_disk["queue"][0])
        self.assertIsNotNone(refusal)
        assert refusal is not None
        self.assertEqual(refusal.code, "orchestrator-probe-unavailable")
        self.assertIn("COULD NOT BE ASKED", refusal.reason)
        self.assertIn("KNOWN HOLE", refusal.remedy)

    def test_the_budget_is_the_EXISTING_flag_and_its_bound_is_not_re_implemented(self):
        """Kept separate: a claim about the FLAG REGISTRY, with no gate and no repository.

        No second retry knob: `--retry-budget` already exists on both hosts (the E-09 rule), and the
        absence of any probe-specific flag is the assertion. Also an `assertRaises` over the bound.
        """
        from agent_workflows import run_recovery

        self.assertEqual(
            rs.resolve_retry_budget(None), run_recovery.DEFAULT_RETRY_LIMIT
        )
        self.assertEqual(run_recovery.DEFAULT_RETRY_LIMIT, 2)
        self.assertIn("--retry-budget", rs.RUN_POLICY_FLAGS_BY_FLAG)
        with self.assertRaises(rs.RunFlagRefusal):
            rs.resolve_retry_budget(11)
        probe_flags = [
            row
            for row in rs.RUN_POLICY_FLAGS
            if "probe" in row.dest or "probe" in row.flag
        ]
        self.assertEqual(probe_flags, [], "a SECOND retry knob was introduced")


# ==================================================================================================
# E-09 / V-09: both hosts, and the suite's own safety
# ==================================================================================================


class BothHostsShareOneDefinition(unittest.TestCase):
    """E-09. Object IDENTITY per symbol, never grep (the `2r306y`/`818uru` discipline)."""

    SYMBOLS = (
        "PROBE_SENTINEL_EXECUTIONS",
        "PROBE_SENTINEL_NO_EXECUTIONS",
        "PROBE_PROMPT_TEMPLATE",
        "render_probe_prompt",
        "orchestrator_probe_excerpt",
        "classify_probe_reply",
        "probe_reply_text",
        "probe_argv",
        "ask_orchestrator_probe",
        "probe_orchestrator",
        "probe_refusal_remedy",
        "probe_unavailable_remedy",
        "enforce_orchestrator_probe_gate",
        "queued_orchestrator_targets",
    )

    def test_each_host_resolves_every_new_symbol_to_the_SAME_object(self):
        """Not merged: already a loop over (symbol x host), which is the table this class needs."""
        for name in self.SYMBOLS:
            shared = getattr(rs, name)
            for label, module in BOTH_HOSTS:
                with self.subTest(symbol=name, host=label):
                    reached = getattr(module, name, getattr(module.runner_shared, name))
                    self.assertIs(reached, shared)

    def test_the_remedy_is_HOST_PARAMETERIZED_and_that_is_the_measured_carve_out(self):
        """Kept separate: a claim about the RELATIONSHIP between the two renderings.

        One composing FUNCTION; the rendered strings must DIFFER, and each must name its own host and
        NOT the other's. `TheRefusalNamesAddAChild` asserts each rendering's content per host, which is
        a different claim: every property there could hold with both hosts rendering identically.
        """
        oc = rs.probe_refusal_remedy(rs.OC_HOST_LABELS, "orc002")
        agy = rs.probe_refusal_remedy(rs.AGY_HOST_LABELS, "orc002")
        self.assertNotEqual(oc, agy)
        self.assertIn("aw oc run", oc)
        self.assertIn("aw agy run", agy)
        self.assertNotIn("aw agy run", oc)
        self.assertNotIn("aw oc run", agy)

    #: (host, the argv prefix ONE builder must produce for it, why this row exists)
    ARGV_PREFIXES = (
        (
            "oc",
            ["opencode", "run"],
            "opencode takes the prompt as a trailing argument after `--`, so its prefix is the "
            "subcommand form. A wrong prefix here does not fail loudly; it spawns something that is "
            "not a probe and the gate reads the result as `could-not-ask` forever",
        ),
        (
            "agy",
            ["agy", "-p"],
            "antigravity takes the prompt via `-p`, which is a DIFFERENT shape for the same job, and "
            "that difference is exactly why one builder taking the host as an argument is the rule "
            "rather than two builders that happen to agree",
        ),
    )

    def test_the_probe_argv_is_built_per_host_by_ONE_builder(self):
        state = {
            "options": {
                "opencode": "opencode",
                "agy_executable": "agy",
                "model": "m",
                "dangerously_skip_permissions": True,
            }
        }
        wrong = []
        for host, prefix, why in self.ARGV_PREFIXES:
            argv = rs.probe_argv(state, host=host, prompt="P", repo="/r")
            problems = []
            if list(argv[: len(prefix)]) != prefix:
                problems.append(
                    f"expected the prefix {prefix!r}, got {list(argv[: len(prefix)])!r} "
                    f"(full argv {list(argv)!r})"
                )
            # A ONE-SHOT on EVERY host: a probe that joined a session would pollute the Set's own
            # conversation with an audit question, and on some hosts would inherit its context.
            for flag in ("--session", "--conversation", "--continue"):
                if flag in argv:
                    problems.append(
                        f"the probe argv carries {flag!r}, so it is not a one-shot: it would attach "
                        "to a session and pollute the Set's own conversation"
                    )
            if "P" not in argv:
                problems.append(f"the prompt never reached the argv: {list(argv)!r}")
            if problems:
                wrong.append(
                    f"  host={host!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`probe_argv` was wrong for {len(wrong)} of {len(self.ARGV_PREFIXES)} hosts. ONE builder "
            "takes the host as an argument, so BOTH rows failing together means that builder changed, "
            "while ONE failing means the hosts' argv construction has been forked. FIX: a wrong prefix "
            "fails SILENTLY in production, because a spawn that is not a probe returns no sentinel and "
            "the gate classifies it as `could-not-ask`, which every run then warns past. A leaked "
            f"session flag is worse: the audit question lands in the Set's own conversation.\n"
            + "\n".join(wrong),
        )


class BothHostsActuallyRefuse(unittest.TestCase):
    """E-09. `pgq326`'s lesson: DECIDING is not ACTING. Drive the REAL `initialize_run` on both.

    ONE table replaces four tests, each of which already looped over BOTH_HOSTS and differed only in
    the fixture, the answer the patched asker returns, and whether `--prepare-only` was passed. Those
    three are now columns, so every scenario runs on both hosts and the failure names the (scenario,
    host) cells that moved rather than reporting N subTest failures with no shared context.

    THE HOST IS THE LOAD-BEARING COLUMN AND THE REASON THIS CLASS EXISTS AT ALL. `pgq326`'s measured
    lesson was an `agy` runner that DECIDED an orchestrator action while having no dispatch branch that
    read it, so an identity check over shared symbols passes while one host does not act. Only driving
    the REAL `initialize_run` on both hosts over the same fixture can catch that, which is why these
    rows are not merged into the `enforce_orchestrator_probe_gate` tables above: those call the gate
    directly and would pass on a host that never calls it.

    EVERY OUTCOME KEEPS ITS OWN ROW AND ITS OWN SPECIFIC ASSERTION: a refusal must RAISE with a message
    naming the orchestrator, the constructive action, and THIS host's own command while NOT naming the
    other's; a clear must return a run directory with `state.json` written; and `--prepare-only` must
    reach neither outcome, writing state while announcing that nothing was cleared. A row asserting
    only "it raised" would accept a refusal that named the wrong host, which is the exact defect the
    host column exists to catch.

    THE `--prepare-only` ROW'S DOUBLE RAISES RATHER THAN ANSWERING, which is how "did not probe" is
    asserted as a property rather than as a call count: the promise is that no host turn is launched at
    all, so any call is a failure no matter what it would have returned.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self._seq = 0

    def make_repo(self, text: str) -> Path:
        self._seq += 1
        repo = self.root / f"repo-{self._seq}"
        plans = repo / ".aw" / "records" / "plans" / "pending"
        plans.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (plans / "20260919-fixture-00-orc002-parent-only.ipd.md").write_text(
            text, encoding="utf-8"
        )
        return repo

    def run_initialize(self, module, repo: Path, extra: list[str] | None = None):
        args = module.build_parser().parse_args(
            ["start", "orc002", "--repo", str(repo), *(extra or [])]
        )
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            run_dir = module.initialize_run(args)
        return run_dir, out.getvalue(), err.getvalue()

    #: The host's own command, which the refusal must name and the OTHER host's must not appear.
    HOST_COMMANDS = (("oc", "aw oc run"), ("agy", "aw agy run"))

    #: (case, the plan text, the answer the patched asker returns (`None` means the double RAISES),
    #: extra argv, whether `initialize_run` must raise `DriverError`, needles required in the raised
    #: message or in stderr, whether the host-command check applies, why this row exists)
    SCENARIOS = (
        (
            "a parent carrying uncovered work",
            PARENT_ONLY_WORK,
            rs.PROBE_ANSWER_EXECUTIONS,
            (),
            True,
            ("orc002", "ADD A CHILD"),
            True,
            "THE WHOLE CLAIM: both hosts must actually REFUSE, not merely decide to. It must name the "
            "orchestrator (an unnamed refusal is unactionable), the constructive action, and THIS "
            "host's command while never the other's, because a remedy naming the wrong host fails "
            "E-09 even though the symbol-identity check passes",
        ),
        (
            "an orchestration-only parent",
            ORCHESTRATION_ONLY.replace("- Id: orc001", "- Id: orc002"),
            rs.PROBE_ANSWER_NO_EXECUTIONS,
            (),
            False,
            (),
            False,
            "THE CLEAN ROW, and it is what stops the refusal row being satisfied by a host that "
            "refuses every run. It must return a run directory with `state.json` written, i.e. the "
            "run really started rather than merely not raising",
        ),
        (
            "`--prepare-only`, which promises no host turn",
            PARENT_ONLY_WORK,
            None,  # the double RAISES: any probe at all is the failure
            ("--prepare-only",),
            False,
            ("SKIPPED under --prepare-only", "NOT yet cleared"),
            False,
            "A THIRD OUTCOME, neither refusal nor clear: `--prepare-only` promises to launch no host "
            "turn, so spending one would break it, and the fixture is the BLOCKING one so a probe "
            "would also refuse the run. It must SAY the gate was skipped and that the orchestrator is "
            "NOT yet cleared, because silence here would read as a clean preparation",
        ),
    )

    def test_every_scenario_reaches_its_own_outcome_on_BOTH_hosts(self):
        wrong = []
        for (
            case,
            plan_text,
            answer,
            extra,
            expect_raise,
            needles,
            check_host_command,
            why,
        ) in self.SCENARIOS:
            for label, module in BOTH_HOSTS:
                repo = self.make_repo(plan_text)
                if answer is None:

                    def double(*a, **k):
                        raise AssertionError(
                            "--prepare-only must not ask the model: this call IS the defect"
                        )
                else:

                    def double(*a, _answer=answer, **k):
                        return _answer, "double"

                problems = []
                raised = None
                run_dir = None
                err = ""
                with unittest.mock.patch.object(rs, "ask_orchestrator_probe", double):
                    try:
                        run_dir, _out, err = self.run_initialize(
                            module, repo, list(extra)
                        )
                    except rs.DriverError as exc:
                        raised = exc
                if expect_raise and raised is None:
                    problems.append(
                        "`initialize_run` did NOT raise: the host DECIDED nothing or decided and then "
                        "failed to act, which is `pgq326`'s exact defect"
                    )
                if not expect_raise and raised is not None:
                    problems.append(f"`initialize_run` RAISED unexpectedly: {raised}")
                haystack = str(raised) if raised is not None else err
                for needle in needles:
                    if needle not in haystack:
                        problems.append(
                            f"the {'refusal message' if raised is not None else 'stderr'} must carry "
                            f"{needle!r}; it said {haystack[:220]!r}"
                        )
                if check_host_command and raised is not None:
                    commands = dict(self.HOST_COMMANDS)
                    mine = commands[label]
                    theirs = commands["agy" if label == "oc" else "oc"]
                    if mine not in haystack:
                        problems.append(
                            f"the refusal must name THIS host's command {mine!r}; it said "
                            f"{haystack[:220]!r}"
                        )
                    if theirs in haystack:
                        problems.append(
                            f"the refusal names the OTHER host's command {theirs!r}, so it would send "
                            "the operator to the wrong runner"
                        )
                if not expect_raise and (
                    run_dir is None or not (run_dir / "state.json").is_file()
                ):
                    problems.append(
                        "no `state.json` was written, so the run did not actually start; a host "
                        "that merely declines to raise has not cleared anything"
                    )
                if problems:
                    wrong.append(
                        f"  {case} (host={label!r}):\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.SCENARIOS) * len(BOTH_HOSTS)} (scenario, host) cells behaved "
            "wrongly. READ WHETHER A WHOLE ROW OR A WHOLE HOST FAILED, because they mean different "
            "things. A whole ROW failing on both hosts means the shared gate changed behavior, which "
            "the direct-gate tables above would also report. A single HOST failing across rows is the "
            "failure this class exists for and nothing else in the suite catches it: `pgq326` was an "
            "`agy` runner that DECIDED an orchestrator action while having no dispatch branch that "
            "read it, so every symbol-identity assertion passed while one host did not act. FIX: if "
            "the CLEAR row fails, the refusal rows are vacuous because the host refuses everything; if "
            "a refusal names the wrong host's command, the operator is sent to the wrong runner and "
            f"the remedy they follow will not re-probe the plan they were told about.\n"
            + "\n".join(wrong),
        )


class TheSuiteCannotSpendTokens(unittest.TestCase):
    """The validation requirement asserted BY CONSTRUCTION, not by hoping.

    NOT TABULATED, and each test says why: all three are `assertRaises` over a guard or a claim about
    the process environment, which the house rule keeps out of tables. Merging them would also be
    self-defeating, since the point of the class is that EACH of the three independent conditions holds
    (the guard raises, the guard is on the real path, and it keys on pytest's own variable), and a
    single accumulating loop would report them as one failure when they have three different fixes.
    """

    def test_a_real_spawn_from_inside_pytest_RAISES(self):
        """Kept separate: `assertRaises` over the guard called DIRECTLY."""
        with self.assertRaises(rs.DriverError) as caught:
            rs._assert_probe_spawn_is_permitted(["opencode", "run"])
        self.assertIn("test that spends tokens is not a test", str(caught.exception))

    def test_the_guard_is_reached_from_the_real_ask_when_no_double_is_injected(self):
        """The guard must be ON the real path, not merely defined beside it.

        Asserted by CALLING `ask_orchestrator_probe` with no `runner`, which is exactly what a future
        test that forgets its double would do. A `DriverError` here is the PASS: it proves the real
        spawn refused. Anything else (a returned answer, an OSError from a real exec) would mean the
        guard was bypassed and the suite could bill a model.
        """
        with self.assertRaises(rs.DriverError) as caught:
            rs.ask_orchestrator_probe(
                {"options": {"opencode": "opencode"}},
                "x",
                host="oc",
                repo=Path("."),
            )
        self.assertIn("REAL model spawn", str(caught.exception))

    def test_the_guard_keys_on_pytests_OWN_variable_so_production_never_sees_it(self):
        """Kept separate: a claim about the PROCESS ENVIRONMENT, with no subject called at all.

        `PYTEST_CURRENT_TEST` is set by pytest and by nothing else, so a real run is unaffected. It is
        what makes the guard above safe to ship rather than a production hazard.
        """
        import os

        self.assertTrue(os.environ.get(rs._PYTEST_ACTIVE_ENV))
        self.assertEqual(rs._PYTEST_ACTIVE_ENV, "PYTEST_CURRENT_TEST")


if __name__ == "__main__":
    unittest.main()
