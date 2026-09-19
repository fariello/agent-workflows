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
        "- [ ] E-01 SEQUENCE THE CHILDREN IN ORDER, holding each until its predecessor reads\n"
        "  `- Status: executed` ON DISK rather than trusting this table, and STOP on the first that\n"
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
        "- [ ] E-01 SEQUENCE THE CHILDREN IN ORDER, holding each until its predecessor reads\n"
        "  `- Status: executed` ON DISK.\n"
        "  - Depends on: none\n"
        "  - Expected outcome: every child executed, in order.\n"
        "  - Execution state: pending\n"
        "\n"
        "- [ ] E-02 Establish the CHARACTERIZATION BASELINE that makes this Set's\n"
        "  behavior-preservation claim falsifiable, BEFORE any child reconciles anything. Write the\n"
        "  missing characterization tests against the current behavior and record the measured\n"
        "  coverage, then produce the inventory as a durable research artifact. Afterwards, once the\n"
        "  children have executed, run the repo-wide suite and the leak sanitization and reconcile\n"
        "  the records this Set closes.\n"
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
    """E-01. The prompt is DATA, names both sentinels, and resolves doubt the safe way."""

    def test_the_prompt_and_the_parser_share_the_sentinel_objects(self):
        """A prompt asking for one spelling while the parser accepts another blocks every run."""
        prompt = rs.render_probe_prompt("excerpt here")
        self.assertIn(rs.PROBE_SENTINEL_EXECUTIONS, prompt)
        self.assertIn(rs.PROBE_SENTINEL_NO_EXECUTIONS, prompt)
        # The SAME objects the parser compares against, not two literals that agree today.
        self.assertEqual(
            rs.classify_probe_reply(rs.PROBE_SENTINEL_EXECUTIONS),
            rs.PROBE_ANSWER_EXECUTIONS,
        )
        self.assertEqual(
            rs.classify_probe_reply(rs.PROBE_SENTINEL_NO_EXECUTIONS),
            rs.PROBE_ANSWER_NO_EXECUTIONS,
        )

    def test_it_says_a_child_checklist_is_EXPECTED_and_is_not_an_execution(self):
        """Without this, the probe fires on every orchestrator in the corpus."""
        prompt = rs.render_probe_prompt("x")
        self.assertIn("EXPECTED", prompt)
        self.assertIn("orchestration", prompt.lower())
        self.assertIn("NOT an execution", prompt)

    def test_it_instructs_that_DOUBT_resolves_to_contains_executions(self):
        prompt = rs.render_probe_prompt("x")
        self.assertIn("doubt resolves to CONTAINS EXECUTIONS", prompt)

    def test_it_names_prose_as_counting(self):
        """The dangerous case is prose, which is the whole reason this is a model and not a regex."""
        prompt = rs.render_probe_prompt("x")
        self.assertIn("PROSE", prompt)

    def test_the_prompt_is_held_as_data_not_inlined_at_a_call_site(self):
        self.assertIsInstance(rs.PROBE_PROMPT_TEMPLATE, str)
        self.assertIn("{excerpt}", rs.PROBE_PROMPT_TEMPLATE)


# ==================================================================================================
# E-02 / V-02: the parser, and the state split the ruling requires
# ==================================================================================================


class TheParserFailsClosed(unittest.TestCase):
    """E-02. Only the two exact sentinels pass; everything DELIVERED and unusable blocks."""

    def test_the_two_exact_sentinels_are_the_only_accepted_answers(self):
        self.assertEqual(
            rs.classify_probe_reply(rs.PROBE_SENTINEL_NO_EXECUTIONS),
            rs.PROBE_ANSWER_NO_EXECUTIONS,
        )
        self.assertEqual(
            rs.classify_probe_reply(rs.PROBE_SENTINEL_EXECUTIONS),
            rs.PROBE_ANSWER_EXECUTIONS,
        )

    def test_a_chatty_reply_is_unknown_and_BLOCKS(self):
        answer = rs.classify_probe_reply(
            "Sure! Having read it carefully, " + rs.PROBE_SENTINEL_NO_EXECUTIONS
        )
        self.assertEqual(answer, rs.PROBE_ANSWER_UNKNOWN)
        self.assertIn(answer, rs.PROBE_BLOCKING_ANSWERS)

    def test_a_refusal_reply_is_unknown_and_BLOCKS(self):
        answer = rs.classify_probe_reply("I cannot help with that request.")
        self.assertEqual(answer, rs.PROBE_ANSWER_UNKNOWN)
        self.assertIn(answer, rs.PROBE_BLOCKING_ANSWERS)

    def test_a_reply_carrying_BOTH_sentinels_is_unknown_and_BLOCKS(self):
        answer = rs.classify_probe_reply(
            rs.PROBE_SENTINEL_EXECUTIONS + "\n" + rs.PROBE_SENTINEL_NO_EXECUTIONS
        )
        self.assertEqual(answer, rs.PROBE_ANSWER_UNKNOWN)
        self.assertIn(answer, rs.PROBE_BLOCKING_ANSWERS)

    def test_a_reply_reporting_a_problem_is_unknown_and_BLOCKS(self):
        answer = rs.classify_probe_reply(
            "The excerpt appears truncated; I could not determine coverage."
        )
        self.assertEqual(answer, rs.PROBE_ANSWER_UNKNOWN)
        self.assertIn(answer, rs.PROBE_BLOCKING_ANSWERS)

    def test_the_answer_vocabulary_is_FOUR_states_not_three(self):
        """A tri-state cannot express the maintainer's OQ-02 ruling; see the class below."""
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


class TheCouldNotAskPathIsDistinctFromUnknown(unittest.TestCase):
    """E-02/E-10. The split the ruling requires, asserted as a SPLIT and not as two labels."""

    def test_a_transport_failure_is_could_not_ask_and_does_NOT_block(self):
        answer = rs.classify_probe_reply("anything at all", transport_ok=False)
        self.assertEqual(answer, rs.PROBE_ANSWER_COULD_NOT_ASK)
        self.assertNotIn(answer, rs.PROBE_BLOCKING_ANSWERS)

    def test_an_empty_reply_is_could_not_ask_because_there_is_nothing_to_be_confused_BY(
        self,
    ):
        self.assertEqual(rs.classify_probe_reply(""), rs.PROBE_ANSWER_COULD_NOT_ASK)
        self.assertEqual(rs.classify_probe_reply(None), rs.PROBE_ANSWER_COULD_NOT_ASK)

    def test_a_missing_binary_is_could_not_ask_and_not_unknown(self):
        state = {"options": {"opencode": "opencode"}}
        answer, detail = rs.ask_orchestrator_probe(
            state, "x", host="oc", repo=Path("."), runner=_transport_failure()
        )
        self.assertEqual(answer, rs.PROBE_ANSWER_COULD_NOT_ASK)
        self.assertIn("not found", detail)

    def test_a_timeout_exit_is_could_not_ask_even_if_the_stream_carried_words(self):
        def runner(argv, cwd, timeout):
            return (
                124,
                json.dumps({"type": "text", "part": {"text": "partial"}}),
                "timed out",
            )

        answer, _detail = rs.ask_orchestrator_probe(
            {"options": {}}, "x", host="oc", repo=Path("."), runner=runner
        )
        self.assertEqual(answer, rs.PROBE_ANSWER_COULD_NOT_ASK)

    def test_a_FileNotFoundError_from_the_spawn_is_could_not_ask(self):
        def runner(argv, cwd, timeout):
            raise FileNotFoundError("opencode")

        answer, detail = rs.ask_orchestrator_probe(
            {"options": {}}, "x", host="oc", repo=Path("."), runner=runner
        )
        self.assertEqual(answer, rs.PROBE_ANSWER_COULD_NOT_ASK)
        self.assertIn("PATH", detail)


class TheReplyIsReadFromEitherHostsSchema(unittest.TestCase):
    """E-02/E-09. ONE extractor taking the host as an argument, never a parser forked per host."""

    def test_the_opencode_text_event_shape_is_read(self):
        stdout = json.dumps(
            {"type": "text", "part": {"text": rs.PROBE_SENTINEL_EXECUTIONS}}
        )
        self.assertEqual(
            rs.probe_reply_text(stdout, host="oc"), rs.PROBE_SENTINEL_EXECUTIONS
        )

    def test_the_antigravity_step_update_shape_is_read(self):
        stdout = json.dumps(
            {
                "event": "step_update",
                "step_update": {
                    "state": "DONE",
                    "step_type": "agent_response",
                    "text": rs.PROBE_SENTINEL_NO_EXECUTIONS,
                },
            }
        )
        self.assertEqual(
            rs.probe_reply_text(stdout, host="agy"), rs.PROBE_SENTINEL_NO_EXECUTIONS
        )

    def test_an_unrecognized_schema_degrades_into_a_STRICTER_parse_not_a_silent_pass(
        self,
    ):
        """A host that changes its event shape must fail the parse, never accidentally clear a run."""
        stdout = json.dumps({"event": "something-new", "payload": {"deep": "value"}})
        reply = rs.probe_reply_text(stdout, host="agy")
        self.assertEqual(rs.classify_probe_reply(reply), rs.PROBE_ANSWER_COULD_NOT_ASK)

    def test_plain_text_output_is_passed_through_so_a_correct_answer_still_parses(self):
        self.assertEqual(
            rs.probe_reply_text(rs.PROBE_SENTINEL_EXECUTIONS, host="oc"),
            rs.PROBE_SENTINEL_EXECUTIONS,
        )


# ==================================================================================================
# E-03 / V-03: the bounded payload, and the price of bounding it
# ==================================================================================================


class TheExcerptIsTheCacheKeysOwnInputs(unittest.TestCase):
    """E-03. Payload and key are the same two things BY CONSTRUCTION, not by agreement."""

    def test_the_excerpt_is_rendered_from_the_cache_payload(self):
        payload = rs.probe_cache_payload(PARENT_ONLY_WORK)
        excerpt = rs.orchestrator_probe_excerpt(PARENT_ONLY_WORK)
        for text in payload["e_items"]:
            self.assertIn(text.splitlines()[0], excerpt)
        for row in payload["child_table_rows"]:
            for cell in row:
                if cell:
                    self.assertIn(cell, excerpt)

    def test_the_excerpt_is_a_SMALL_FRACTION_of_the_file(self):
        """An unbounded probe would send a five-figure token file to answer a yes/no question."""
        for name, text in (
            ("orchestration-only", ORCHESTRATION_ONLY),
            ("parent-only-work", PARENT_ONLY_WORK),
        ):
            with self.subTest(fixture=name):
                self.assertLess(len(rs.orchestrator_probe_excerpt(text)), len(text))

    def test_the_child_table_arrives_as_ROW_CELL_TEXT_not_a_parsed_order_graph(self):
        """`parse_child_table` returns `{order: (deps,)}`, so an Id swap leaves it byte-identical."""
        excerpt = rs.orchestrator_probe_excerpt(PARENT_ONLY_WORK)
        self.assertIn("bbb222", excerpt)
        self.assertIn("the child that does the work", excerpt)
        swapped = PARENT_ONLY_WORK.replace("bbb222", "zzz999")
        self.assertNotEqual(excerpt, rs.orchestrator_probe_excerpt(swapped))

    def test_a_NO_OP_executor_mutation_does_not_change_the_excerpt(self):
        """The `xmqv5l` trap: a conforming executor ticks boxes and fills evidence."""
        ticked = PARENT_ONLY_WORK.replace(
            "- [ ] E-02 Establish", "- [x] E-02 Establish"
        )
        self.assertEqual(
            rs.orchestrator_probe_excerpt(PARENT_ONLY_WORK),
            rs.orchestrator_probe_excerpt(ticked),
        )

    def test_an_empty_orchestrator_still_produces_a_usable_excerpt(self):
        """A parent with neither items nor a table must not send an empty prompt body."""
        excerpt = rs.orchestrator_probe_excerpt("# IPD: bare\n\n- Kind: orchestrator\n")
        self.assertIn("no checklist items", excerpt)
        self.assertIn("no child table", excerpt)


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

    def test_a_continuation_line_is_INCLUDED_in_the_action_text(self):
        blocks = rs.e_item_action_blocks(self.MULTILINE)
        self.assertEqual(len(blocks), 1)
        self.assertIn("Sequence the children.", blocks[0])
        self.assertIn("establish the baseline before any child runs", blocks[0])

    def test_the_SUB_FIELDS_are_still_excluded(self):
        """The structural exclusion the `xmqv5l` no-op invariants depend on must be intact."""
        blocks = rs.e_item_action_blocks(self.MULTILINE)
        for field in ("Depends on:", "Expected outcome:", "Execution state:"):
            self.assertNotIn(field, blocks[0])

    def test_editing_a_CONTINUATION_line_moves_the_digest(self):
        """The under-sensitivity half: this assertion FAILED before the fix."""
        edited = self.MULTILINE.replace(
            "AND ALSO establish the baseline before any child runs, which no child covers.",
            "AND ALSO merely read each child's status on disk, which is pure sequencing.",
        )
        self.assertNotEqual(
            rs.probe_cache_digest(self.MULTILINE), rs.probe_cache_digest(edited)
        )

    def test_ticking_the_checkbox_still_moves_NOTHING(self):
        """The fix must not be bought by re-introducing the `xmqv5l` trap."""
        ticked = self.MULTILINE.replace("- [ ] E-01", "- [x] E-01")
        self.assertEqual(
            rs.probe_cache_digest(self.MULTILINE), rs.probe_cache_digest(ticked)
        )

    def test_writing_an_execution_note_still_moves_NOTHING(self):
        noted = self.MULTILINE.replace(
            "  - Execution state: pending\n",
            "  - Execution state: performed\n  - Execution note: did the thing.\n",
        )
        self.assertEqual(
            rs.probe_cache_digest(self.MULTILINE), rs.probe_cache_digest(noted)
        )

    def test_the_probe_SEES_the_continuation_prose(self):
        excerpt = rs.orchestrator_probe_excerpt(self.MULTILINE)
        self.assertIn("establish the baseline before any child runs", excerpt)

    def test_a_multi_item_document_keeps_the_items_SEPARATE(self):
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
    """E-04. A cache HIT spends nothing; a content change spends exactly one call."""

    def test_every_orchestrator_cached_means_ZERO_model_calls(self):
        rel = self.write_plan("orc001.ipd.md", ORCHESTRATION_ONLY)
        state = self.state([self.item("orc001", rel)])
        rs.record_probe_verdict(
            self.repo,
            rs.probe_cache_digest(ORCHESTRATION_ONLY),
            rs.PROBE_VERDICT_PASS,
            model="test/model",
        )
        asker = _counting_asker(rs.PROBE_ANSWER_EXECUTIONS)
        decision, _err = self.gate(state, asker=asker)
        self.assertTrue(decision.proceed)
        self.assertEqual(decision.calls, 0)
        self.assertEqual(asker.calls, [])
        self.assertTrue(decision.outcomes[0].cached)

    def test_editing_an_E_item_action_costs_exactly_ONE_call(self):
        # A CONTINUATION line, deliberately: that is where an author actually changes what an item
        # asks for, and it was invisible to the digest until this child fixed the payload. See
        # `TheActionTextIsTheWholeBlockNotItsFirstLine`.
        edited = ORCHESTRATION_ONLY.replace(
            "does not. DO NOT PERFORM ANY CHILD'S WORK FROM HERE",
            "does not. ALSO produce the inventory artifact nobody else produces",
        )
        rel = self.write_plan("orc001.ipd.md", edited)
        state = self.state([self.item("orc001", rel)])
        rs.record_probe_verdict(
            self.repo,
            rs.probe_cache_digest(ORCHESTRATION_ONLY),
            rs.PROBE_VERDICT_PASS,
            model="test/model",
        )
        asker = _counting_asker(rs.PROBE_ANSWER_NO_EXECUTIONS)
        decision, _err = self.gate(state, asker=asker)
        self.assertTrue(decision.proceed)
        self.assertEqual(decision.calls, 1)
        self.assertEqual(len(asker.calls), 1)

    def test_a_probed_verdict_is_RECORDED_so_the_next_run_is_free(self):
        rel = self.write_plan("orc001.ipd.md", ORCHESTRATION_ONLY)
        state = self.state([self.item("orc001", rel)])
        asker = _counting_asker(rs.PROBE_ANSWER_NO_EXECUTIONS)
        self.gate(state, asker=asker)
        served = rs.read_probe_verdict(
            self.repo, rs.probe_cache_digest(ORCHESTRATION_ONLY), model="test/model"
        )
        self.assertTrue(served.is_hit)
        self.assertEqual(served.verdict, rs.PROBE_VERDICT_PASS)

    def test_a_MISS_is_never_read_as_a_pass(self):
        """ "Not probed" and "probed and cleared" are different facts."""
        served = rs.read_probe_verdict(self.repo, "no-such-digest")
        self.assertEqual(served.verdict, rs.PROBE_VERDICT_UNKNOWN)
        self.assertFalse(served.is_hit)


class TheProbeIsQueueScoped(ProbeCase):
    """E-04. `aw oc run all` must not sweep the repository's whole orchestrator corpus."""

    def test_an_orchestrator_on_disk_but_NOT_in_the_queue_is_never_probed(self):
        in_queue = self.write_plan("orc001.ipd.md", ORCHESTRATION_ONLY)
        self.write_plan("orc002.ipd.md", PARENT_ONLY_WORK)  # on disk, not queued
        state = self.state([self.item("orc001", in_queue)])
        targets = rs.queued_orchestrator_targets(state, repo=self.repo)
        self.assertEqual([t.id6 for t in targets], ["orc001"])

    def test_a_CHILD_in_the_queue_is_not_probed(self):
        rel = self.write_plan("child.ipd.md", ORCHESTRATION_ONLY)
        state = self.state([self.item("chi001", rel, kind="child")])
        self.assertEqual(rs.queued_orchestrator_targets(state, repo=self.repo), ())

    def test_an_unreadable_plan_is_skipped_rather_than_crashing_the_gate(self):
        state = self.state(
            [self.item("gone01", ".aw/records/plans/pending/absent.ipd.md")]
        )
        self.assertEqual(rs.queued_orchestrator_targets(state, repo=self.repo), ())

    def test_queue_order_is_preserved_so_the_first_blocker_is_the_first_in_the_queue(
        self,
    ):
        a = self.write_plan("orc001.ipd.md", ORCHESTRATION_ONLY)
        b = self.write_plan("orc002.ipd.md", PARENT_ONLY_WORK)
        state = self.state(
            [self.item("orc001", a, position=1), self.item("orc002", b, position=2)]
        )
        targets = rs.queued_orchestrator_targets(state, repo=self.repo)
        self.assertEqual([t.id6 for t in targets], ["orc001", "orc002"])


# ==================================================================================================
# E-05 / V-05: the gate's three paths
# ==================================================================================================


class TheGateHasThreePaths(ProbeCase):
    """E-05. FAIL unattended, PROMPT on a TTY, and honor a JUSTIFIED override."""

    def blocking_state(self) -> dict:
        rel = self.write_plan("orc002.ipd.md", PARENT_ONLY_WORK)
        return self.state([self.item("orc002", rel)])

    def test_unattended_it_REFUSES(self):
        decision, _err = self.gate(
            self.blocking_state(),
            interactive=False,
            asker=_counting_asker(rs.PROBE_ANSWER_EXECUTIONS),
        )
        self.assertFalse(decision.proceed)
        self.assertIn("orc002", decision.message)

    def test_interactively_the_EXACT_phrase_admits_and_anything_else_refuses(self):
        for answer, expect in (
            (rs.PROBE_CONFIRM_PHRASE, True),
            ("y", False),
            ("", False),
        ):
            with self.subTest(answer=answer):
                case = ProbeCase("run")
                case.setUp()
                rel = case.write_plan("orc002.ipd.md", PARENT_ONLY_WORK)
                decision, _err = case.gate(
                    case.state([case.item("orc002", rel)]),
                    interactive=True,
                    response=answer,
                    asker=_counting_asker(rs.PROBE_ANSWER_EXECUTIONS),
                )
                self.assertIs(decision.proceed, expect)

    def test_the_prompt_is_only_asked_when_a_TTY_was_established_by_the_caller(self):
        """No TTY means no prompt and no waiting, EVER (the shipped `_lane_reclaim_prompt` rule)."""
        asked: list = []

        def prompt(question):
            asked.append(question)
            return None

        self.gate(
            self.blocking_state(),
            interactive=False,
            prompt=prompt,
            asker=_counting_asker(rs.PROBE_ANSWER_EXECUTIONS),
        )
        self.assertEqual(asked, [])

    def test_the_override_REQUIRES_and_RECORDS_a_justification(self):
        state = self.blocking_state()
        decision, err = self.gate(
            state,
            interactive=False,
            override_justification="accepted: E-02 is covered by a child landing tomorrow",
            asker=_counting_asker(rs.PROBE_ANSWER_EXECUTIONS),
        )
        self.assertTrue(decision.proceed)
        self.assertIn(
            "covered by a child landing tomorrow", decision.override_justification
        )
        self.assertIn(
            "covered by a child landing tomorrow",
            state["options"]["allow_uncovered_orchestrator_work"],
        )
        self.assertIn("OVERRIDDEN", err)

    def test_an_EMPTY_justification_is_not_an_override(self):
        """A bare flag must not clear the gate; argparse requires a value and so does this."""
        decision, _err = self.gate(
            self.blocking_state(),
            interactive=False,
            override_justification="   ",
            asker=_counting_asker(rs.PROBE_ANSWER_EXECUTIONS),
        )
        self.assertFalse(decision.proceed)

    def test_an_interactive_consent_is_recorded_as_an_override_too(self):
        state = self.blocking_state()
        decision, _err = self.gate(
            state,
            interactive=True,
            response=rs.PROBE_CONFIRM_PHRASE,
            asker=_counting_asker(rs.PROBE_ANSWER_EXECUTIONS),
        )
        self.assertTrue(decision.proceed)
        self.assertIn(
            "interactive", state["options"]["allow_uncovered_orchestrator_work"]
        )

    def test_an_orchestration_only_parent_is_CLEARED(self):
        """The false-positive side: the corpus is overwhelmingly this shape."""
        rel = self.write_plan("orc001.ipd.md", ORCHESTRATION_ONLY)
        decision, _err = self.gate(
            self.state([self.item("orc001", rel)]),
            asker=_counting_asker(rs.PROBE_ANSWER_NO_EXECUTIONS),
        )
        self.assertTrue(decision.proceed)
        self.assertFalse(decision.warned_past)
        self.assertEqual(decision.refusal, None)

    def test_a_run_with_NO_queued_orchestrator_spends_nothing_and_proceeds(self):
        rel = self.write_plan("child.ipd.md", ORCHESTRATION_ONLY)
        asker = _counting_asker(rs.PROBE_ANSWER_EXECUTIONS)
        decision, _err = self.gate(
            self.state([self.item("chi001", rel, kind="child")]), asker=asker
        )
        self.assertTrue(decision.proceed)
        self.assertEqual(decision.calls, 0)
        self.assertEqual(asker.calls, [])


class TheRefusalIsDURABLE(ProbeCase):
    """E-05/E-06. Criterion 3: the reason survives the process, not only the scrollback."""

    def test_the_refusal_is_written_into_run_STATE_where_aw_runs_reads_it(self):
        rel = self.write_plan("orc002.ipd.md", PARENT_ONLY_WORK)
        state = self.state([self.item("orc002", rel)])
        saved: list = []
        self.gate(
            state,
            asker=_counting_asker(rs.PROBE_ANSWER_EXECUTIONS),
            write_report_fn=lambda rd, st: saved.append(rd),
        )
        # Read it back the way a READER does, through the shared reader rather than by key.
        on_disk = json.loads((self.run_dir / "state.json").read_text(encoding="utf-8"))
        refusal = render_stream.refusal_of_item(on_disk["queue"][0])
        self.assertIsNotNone(refusal)
        assert refusal is not None
        self.assertEqual(refusal.code, rs.PROBE_REFUSAL_CODE)
        self.assertIn("orc002", refusal.reason)
        self.assertTrue(
            saved, "the report must be rewritten so `aw runs` renders the refusal"
        )

    def test_the_gate_records_its_decision_as_an_EVENT(self):
        rel = self.write_plan("orc002.ipd.md", PARENT_ONLY_WORK)
        self.gate(
            self.state([self.item("orc002", rel)]),
            asker=_counting_asker(rs.PROBE_ANSWER_EXECUTIONS),
        )
        events = [
            e for e in self.events() if e.get("event") == "orchestrator-probe-gate"
        ]
        self.assertEqual(len(events), 1)
        self.assertFalse(events[0]["proceed"])
        self.assertEqual(events[0]["blocking"], ["orc002"])

    def test_the_override_event_carries_the_justification(self):
        rel = self.write_plan("orc002.ipd.md", PARENT_ONLY_WORK)
        self.gate(
            self.state([self.item("orc002", rel)]),
            override_justification="maintainer accepted 2026-09-19",
            asker=_counting_asker(rs.PROBE_ANSWER_EXECUTIONS),
        )
        events = [
            e for e in self.events() if e.get("event") == "orchestrator-probe-gate"
        ]
        self.assertEqual(events[0]["justification"], "maintainer accepted 2026-09-19")

    def test_a_refusal_leaves_NO_session_and_NO_worktree_behind(self):
        """ "Costs nothing" means no agent turn, no lane, no session - not "no run directory"."""
        rel = self.write_plan("orc002.ipd.md", PARENT_ONLY_WORK)
        state = self.state([self.item("orc002", rel)])
        self.gate(state, asker=_counting_asker(rs.PROBE_ANSWER_EXECUTIONS))
        sessions = self.run_dir / "sessions"
        self.assertFalse(sessions.exists() and any(sessions.iterdir()))
        on_disk = json.loads((self.run_dir / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["queue"][0]["attempts"], [])
        self.assertNotIn("worktree", on_disk["queue"][0])


class TheRefusalNamesAddAChild(ProbeCase):
    """E-06. THE WORDING IS THE DELIVERABLE: a prohibition gets complied with by DELETION."""

    def remedy(self, host: str = "oc") -> str:
        labels = rs.AGY_HOST_LABELS if host == "agy" else rs.OC_HOST_LABELS
        return rs.probe_refusal_remedy(labels, "orc002")

    def test_it_names_the_CONSTRUCTIVE_action_first(self):
        remedy = self.remedy()
        self.assertIn("ADD A CHILD", remedy)
        self.assertLess(
            remedy.index("ADD A CHILD"),
            len(remedy) // 2,
            "the constructive action must lead, not trail a prohibition",
        )

    def test_it_explicitly_tells_the_reader_NOT_to_delete_the_parents_items(self):
        remedy = self.remedy()
        self.assertIn("Do NOT delete", remedy)
        self.assertIn("checklist", remedy)

    def test_it_does_NOT_read_as_a_bare_prohibition(self):
        remedy = self.remedy()
        for forbidden in (
            "must not contain executions",
            "cannot have executions",
            "is not allowed",
        ):
            self.assertNotIn(forbidden, remedy)

    def test_it_names_the_override_so_the_operator_is_not_left_guessing(self):
        self.assertIn("--allow-uncovered-orchestrator-work", self.remedy())

    def test_the_remedy_reaches_the_run_SUMMARY_through_child_01s_renderer(self):
        rel = self.write_plan("orc002.ipd.md", PARENT_ONLY_WORK)
        state = self.state([self.item("orc002", rel)])
        self.gate(state, asker=_counting_asker(rs.PROBE_ANSWER_EXECUTIONS))
        rendered = render_stream.render_run_summary_table(
            state, self.run_dir, pal=render_stream.Palette(False)
        )
        self.assertIn("ADD A CHILD", rendered)
        self.assertIn("remedy", rendered)


# ==================================================================================================
# E-10 / V-10: availability
# ==================================================================================================


class TheCouldNotAskPathDoesNotBlock(ProbeCase):
    """E-10. A model outage must not halt a run that is otherwise fine (maintainer's OQ-02)."""

    def unreachable_asker(self):
        calls: list = []

        def asker(state, excerpt, *, host, repo, runner=None):
            calls.append(excerpt)
            return rs.PROBE_ANSWER_COULD_NOT_ASK, "the host binary is not on PATH"

        asker.calls = calls  # type: ignore[attr-defined]
        return asker

    def test_it_is_retried_to_the_budget_and_then_PROCEEDS(self):
        rel = self.write_plan("orc001.ipd.md", ORCHESTRATION_ONLY)
        asker = self.unreachable_asker()
        decision, err = self.gate(
            self.state([self.item("orc001", rel)]), asker=asker, retry_budget=2
        )
        self.assertTrue(decision.proceed)
        self.assertTrue(decision.warned_past)
        # The initial attempt PLUS the budget, which is what "a budget of retries" means.
        self.assertEqual(len(asker.calls), 3)
        self.assertIn("WARNING", err)
        self.assertIn("KNOWN HOLE", err)

    def test_a_budget_of_zero_asks_exactly_once(self):
        rel = self.write_plan("orc001.ipd.md", ORCHESTRATION_ONLY)
        asker = self.unreachable_asker()
        self.gate(self.state([self.item("orc001", rel)]), asker=asker, retry_budget=0)
        self.assertEqual(len(asker.calls), 1)

    def test_an_unknown_still_BLOCKS_and_is_NOT_retried_past(self):
        """Retrying a confused model is how a fail-closed gate is talked into passing."""
        rel = self.write_plan("orc001.ipd.md", ORCHESTRATION_ONLY)
        asker = _counting_asker(rs.PROBE_ANSWER_UNKNOWN)
        decision, _err = self.gate(
            self.state([self.item("orc001", rel)]), asker=asker, retry_budget=5
        )
        self.assertFalse(decision.proceed)
        self.assertEqual(len(asker.calls), 1)

    def test_the_KNOWN_HOLE_is_durable_and_readable_after_the_process_exits(self):
        rel = self.write_plan("orc001.ipd.md", ORCHESTRATION_ONLY)
        state = self.state([self.item("orc001", rel)])
        self.gate(state, asker=self.unreachable_asker(), retry_budget=1)
        on_disk = json.loads((self.run_dir / "state.json").read_text(encoding="utf-8"))
        refusal = render_stream.refusal_of_item(on_disk["queue"][0])
        self.assertIsNotNone(refusal)
        assert refusal is not None
        self.assertEqual(refusal.code, rs.PROBE_UNAVAILABLE_CODE)
        self.assertIn("COULD NOT BE ASKED", refusal.reason)
        self.assertIn("KNOWN HOLE", refusal.remedy)

    def test_a_could_not_ask_verdict_is_NEVER_written_to_the_cache(self):
        """Recording it would turn "not probed" into a stored fact."""
        rel = self.write_plan("orc001.ipd.md", ORCHESTRATION_ONLY)
        self.gate(
            self.state([self.item("orc001", rel)]), asker=self.unreachable_asker()
        )
        served = rs.read_probe_verdict(
            self.repo, rs.probe_cache_digest(ORCHESTRATION_ONLY), model="test/model"
        )
        self.assertFalse(served.is_hit)
        with self.assertRaises(ValueError):
            rs.record_probe_verdict(
                self.repo, "d", rs.PROBE_ANSWER_COULD_NOT_ASK, model=None
            )

    def test_the_budget_is_the_EXISTING_flag_and_its_bound_is_not_re_implemented(self):
        """No second retry knob: `--retry-budget` already exists on both hosts (the E-09 rule)."""
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
        for name in self.SYMBOLS:
            shared = getattr(rs, name)
            for label, module in BOTH_HOSTS:
                with self.subTest(symbol=name, host=label):
                    reached = getattr(module, name, getattr(module.runner_shared, name))
                    self.assertIs(reached, shared)

    def test_the_remedy_is_HOST_PARAMETERIZED_and_that_is_the_measured_carve_out(self):
        """One composing FUNCTION; the rendered strings differ because each names its own host."""
        oc = rs.probe_refusal_remedy(rs.OC_HOST_LABELS, "orc002")
        agy = rs.probe_refusal_remedy(rs.AGY_HOST_LABELS, "orc002")
        self.assertNotEqual(oc, agy)
        self.assertIn("aw oc run", oc)
        self.assertIn("aw agy run", agy)
        self.assertNotIn("aw agy run", oc)
        self.assertNotIn("aw oc run", agy)

    def test_agy_did_not_gain_a_new_import_from_oc(self):
        """Measured in THIS worktree rather than trusting a number written in a plan."""
        import ast

        source = Path(agy_runipd.__file__).read_text(encoding="utf-8")
        names: set = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ImportFrom) and (node.module or "").endswith(
                "oc_runipd"
            ):
                names.update(a.name for a in node.names)
        for symbol in BothHostsShareOneDefinition.SYMBOLS:
            self.assertNotIn(
                symbol, names, "reached agy through the OTHER HOST'S driver"
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
        oc_argv = rs.probe_argv(state, host="oc", prompt="P", repo="/r")
        agy_argv = rs.probe_argv(state, host="agy", prompt="P", repo="/r")
        self.assertEqual(oc_argv[:2], ["opencode", "run"])
        self.assertEqual(agy_argv[:2], ["agy", "-p"])
        # A ONE-SHOT: no session on either host, so it cannot pollute a Set's session.
        for argv in (oc_argv, agy_argv):
            with self.subTest(argv=argv[0]):
                self.assertNotIn("--session", argv)
                self.assertNotIn("--conversation", argv)
                self.assertNotIn("--continue", argv)


class BothHostsActuallyRefuse(unittest.TestCase):
    """E-09. `pgq326`'s lesson: DECIDING is not ACTING. Drive the REAL `initialize_run` on both."""

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

    def test_BOTH_hosts_refuse_on_the_same_fixture(self):
        for label, module in BOTH_HOSTS:
            with self.subTest(host=label):
                repo = self.make_repo(PARENT_ONLY_WORK)
                with unittest.mock.patch.object(
                    rs,
                    "ask_orchestrator_probe",
                    lambda *a, **k: (rs.PROBE_ANSWER_EXECUTIONS, "double"),
                ):
                    with self.assertRaises(rs.DriverError) as caught:
                        self.run_initialize(module, repo)
                message = str(caught.exception)
                self.assertIn("orc002", message)
                self.assertIn("ADD A CHILD", message)

    def test_BOTH_hosts_CLEAR_an_orchestration_only_parent(self):
        for label, module in BOTH_HOSTS:
            with self.subTest(host=label):
                repo = self.make_repo(
                    ORCHESTRATION_ONLY.replace("- Id: orc001", "- Id: orc002")
                )
                with unittest.mock.patch.object(
                    rs,
                    "ask_orchestrator_probe",
                    lambda *a, **k: (rs.PROBE_ANSWER_NO_EXECUTIONS, "double"),
                ):
                    run_dir, _out, _err = self.run_initialize(module, repo)
                self.assertTrue((run_dir / "state.json").is_file())

    def test_the_refusal_names_the_HOST_THAT_REFUSED(self):
        """A remedy naming the wrong host fails E-09 even though the identity check passes."""
        expected = {"oc": "aw oc run", "agy": "aw agy run"}
        for label, module in BOTH_HOSTS:
            with self.subTest(host=label):
                repo = self.make_repo(PARENT_ONLY_WORK)
                with unittest.mock.patch.object(
                    rs,
                    "ask_orchestrator_probe",
                    lambda *a, **k: (rs.PROBE_ANSWER_EXECUTIONS, "double"),
                ):
                    with self.assertRaises(rs.DriverError) as caught:
                        self.run_initialize(module, repo)
                message = str(caught.exception)
                self.assertIn(expected[label], message)
                other = expected["agy" if label == "oc" else "oc"]
                self.assertNotIn(other, message)

    def test_prepare_only_does_NOT_probe_and_says_so(self):
        """`--prepare-only` promises to launch no host turn; spending one would break it."""
        for label, module in BOTH_HOSTS:
            with self.subTest(host=label):
                repo = self.make_repo(PARENT_ONLY_WORK)

                def explode(*a, **k):
                    raise AssertionError("--prepare-only must not ask the model")

                with unittest.mock.patch.object(rs, "ask_orchestrator_probe", explode):
                    run_dir, _out, err = self.run_initialize(
                        module, repo, ["--prepare-only"]
                    )
                self.assertIn("SKIPPED under --prepare-only", err)
                self.assertIn("NOT yet cleared", err)
                self.assertTrue((run_dir / "state.json").is_file())


class TheSuiteCannotSpendTokens(unittest.TestCase):
    """The validation requirement asserted BY CONSTRUCTION, not by hoping."""

    def test_a_real_spawn_from_inside_pytest_RAISES(self):
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
        """`PYTEST_CURRENT_TEST` is set by pytest and by nothing else, so a real run is unaffected."""
        import os

        self.assertTrue(os.environ.get(rs._PYTEST_ACTIVE_ENV))
        self.assertEqual(rs._PYTEST_ACTIVE_ENV, "PYTEST_CURRENT_TEST")


if __name__ == "__main__":
    unittest.main()
