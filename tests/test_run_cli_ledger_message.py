"""The absent-ledger refusal must say WHY it cannot answer, at every leaf that prints it (`i1hlgx`).

THE DEFECT THESE TESTS PIN. `aw runs verify-ledger <any-real-run>` cannot verify any driver run,
because no driver run writes a `ledger.jsonl` at all, and the refusal used to say only
`ledger file not found for target '<id>'`. That is an accurate statement about a FILE and a
misleading one about the WORLD: an operator asking "is this run's record intact" was answered with
something that reads like one unusual missing artifact rather than "this command cannot answer that
question for any driver run". Graduated from backlog `zrzfkw`, whose fix #1 this is.

WHY THE MESSAGE ASSERTION IS PARAMETERIZED ACROSS LEAVES RATHER THAN TESTED ONCE. TEN
operator-facing leaves print this refusal: three construct it inline (`runs show`, `runs evidence`,
`runs verify-ledger`) and seven reach it through the shared `_resolve_or_error` (`run start`,
`runs next`, `run record`, `runs resume`, `run cancel`, `runs status`, `run finalize`). A test that
covered `verify-ledger` alone would PASS against the exact defect this module exists to correct, in
which one surface explains the unwired ledger while nine keep implying a missing file. So the table
covers all three classes: an inline emitter, a second inline emitter, and helper-routed leaves
including an ACTION verb, which is the case that proves the shared text is not reader-specific.

WHAT IS PINNED AND WHAT IS DELIBERATELY NOT. Pinned: the three CLAUSES the message must carry (the
file it reads, that no driver writes one, and that `events.jsonl` is different), the EXIT CODE, the
machine payload's KEYS, and that a PRESENT ledger is unaffected. Not pinned: the sentence's exact
wording, because rewording a message is not a regression; each clause is checked as the one phrase
a reader greps for, following the convention in `tests/test_run_recovery_cli.py`.

THE EXIT CODE IS MEASURED WITHOUT A PIPELINE, AND THAT IS THE POINT OF `_exit_code_unpiped`. The
backlog item this graduates from originally claimed the command exited 0 on an absent ledger and
told a reader to hunt for lost plumbing. It does not, and never did: the original measurement piped
the command through `head`, so the `$?` read was `head`'s status rather than the command's. Reading
a return code through a pipe in a TEST would enshrine that very error in the place most likely to be
trusted, so these tests take the return value of the call directly and capture output by patching
`sys.stdout` rather than through any pipeline.

No live model, no network, no repository writes: the happy-path ledger is a FIXTURE, built here,
because none exists anywhere in the repository (that absence is the defect's premise).
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Tuple
from unittest.mock import patch

from agent_workflows import cli, run_cli
from agent_workflows import run_ledger_schema as schema
from agent_workflows import run_ledger_store as ledger_store

RUN_ID = "run-abcdef1234"
HEAD = "1" * 40

#: The three clauses the refusal MUST carry, each as the one phrase a reader greps for rather than a
#: whole sentence. Keyed by what the clause is FOR, so a failure names the missing idea and not a
#: string index.
#:
#:   "file"     WHICH file this family reads, so the operator knows what was looked for
#:   "unwired"  that NO driver run writes one today, which is what turns a puzzling absence into a
#:              known limitation and stops the operator hunting a fault in their own run
#:   "events"   that the drivers' own `events.jsonl` is a DIFFERENT file, which is the naming trap:
#:              "ledger" names two unrelated substrates and only one of them exists
REQUIRED_CLAUSES: Dict[str, str] = {
    "file": "ledger.jsonl",
    "unwired": "no driver run writes one",
    "events": "events.jsonl",
}


def _run_record() -> Dict[str, Any]:
    return {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "run",
        "run_id": RUN_ID,
        "actor": "runtime",
        "workflow_digest": "a" * 64,
        "requirement_digest": "b" * 64,
        "repo": "agent-workflows",
        "head": HEAD,
        "parent": "",
    }


def _requirement_set(reqs: List[str]) -> Dict[str, Any]:
    return {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "requirement_set",
        "run_id": RUN_ID,
        "actor": "runtime",
        "requirement_digest": "b" * 64,
        "requirements": [{"id": r} for r in reqs],
        "scope_fence": {},
        "parent": "",
    }


def _complete_run_records() -> List[Dict[str, Any]]:
    """Records for a clean, complete run, so the happy path has something real to verify."""
    return [
        _run_record(),
        _requirement_set(["R-01"]),
        {
            "schema_version": schema.LEDGER_SCHEMA_VERSION,
            "kind": "step_attempt",
            "run_id": RUN_ID,
            "actor": "executor",
            "step": "S-01",
            "state": "performed",
            "attempt": 1,
            "parent": "",
        },
        {
            "schema_version": schema.LEDGER_SCHEMA_VERSION,
            "kind": "verifier_decision",
            "run_id": RUN_ID,
            "actor": "verifier",
            "requirement": "R-01",
            "result": "satisfied",
            "parent": "",
        },
    ]


def _parse_machine(out: str) -> Any:
    """Parse machine output, tolerating both the pretty `--json` block and one-line `--agent`."""
    text = out.strip()
    try:
        return json.loads(text)
    except ValueError:
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            raise
        return json.loads(lines[-1])


class _CliCase(unittest.TestCase):
    """Shared invocation helper: call the CLI in-process and read its return value DIRECTLY.

    NO PIPELINE ANYWHERE. `cli.main` returns the exit code, and stdout is captured by patching the
    stream, so the code under assertion is the COMMAND's and never a downstream stage's. This is the
    deliberate defense against the measurement error that produced backlog `zrzfkw`'s false second
    defect, where `aw runs verify-ledger <id> | head` reported `head`'s zero.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _exit_code_unpiped(self, *argv: str) -> Tuple[int, str]:
        """Return (exit code, stdout). The code is `cli.main`'s own return, not a pipeline's."""
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            rc = cli.main(list(argv))
        return rc, out.getvalue()


class TestAbsentLedgerRefusalIsTruthful(_CliCase):
    """The absent-ledger refusal names the real situation, identically at every leaf that prints it."""

    #: (case, argv for a BARE RUN ID target, why this row exists)
    #:
    #: Each row is a leaf that emits the refusal, chosen to cover all three emit paths. Every row's
    #: target is a bare run id with no ledger anywhere, which is precisely the situation an operator
    #: diagnosing a real driver run is in.
    LEAVES: Tuple[Tuple[str, Tuple[str, ...], str], ...] = (
        (
            "runs verify-ledger (inline emitter, and the leaf the item was filed against)",
            ("runs", "verify-ledger", RUN_ID),
            "THE ORIGINAL SUBJECT: the operator asks whether the record is intact and must be told "
            "the question cannot be answered for any driver run, not that one file is absent",
        ),
        (
            "runs show (a SECOND inline emitter)",
            ("runs", "show", RUN_ID),
            "THE LEAF AN OPERATOR TRIES NEXT after a vague refusal, to see what IS there. Before "
            "this fix it printed the byte-identical misleading line, so a single-leaf fix would "
            "have walked the operator straight back into the same dead end",
        ),
        (
            "runs status (helper-routed, read-only)",
            ("runs", "status", RUN_ID),
            "THE CHEAPEST PROOF THAT THE SHARED PLACEMENT HOLDS: this leaf has no refusal text of "
            "its own and inherits the wording from `_resolve_or_error`. If a later refactor returns "
            "the honest message to one leaf, this row is what fails",
        ),
        (
            "run cancel (helper-routed, and an ACTION VERB)",
            ("run", "cancel", RUN_ID),
            "THE LOAD-BEARING ROW FOR THE WORDING ITSELF: six of the helper's callers are actions "
            "rather than readers, so a message hardcoding 'cannot verify' would be FALSE here. "
            "Covering an action verb is what pins the text as verb-neutral",
        ),
    )

    def test_every_leaf_states_all_three_clauses_and_exits_two(self) -> None:
        """One table over every emit path: the three clauses are present and the code is 2.

        Accumulates problems rather than asserting per row, because the realistic failure is not one
        leaf breaking alone: it is the shared wording moving, or one class of emitter (inline versus
        helper-routed) drifting from the other. A single failure listing every affected leaf shows
        that shape; four independent red lines would not.
        """
        problems: List[str] = []
        for case, argv, _why in self.LEAVES:
            rc, out = self._exit_code_unpiped(*argv, "--dir", str(self.tmp))
            if rc != run_cli.EXIT_INVALID_INVOCATION:
                problems.append(
                    f"{case}: exit {rc}, expected {run_cli.EXIT_INVALID_INVOCATION} "
                    f"(measured with NO pipeline)"
                )
            for clause, needle in REQUIRED_CLAUSES.items():
                if needle not in out:
                    problems.append(
                        f"{case}: refusal is missing the {clause!r} clause ({needle!r}); "
                        f"got {out[:400]!r}"
                    )
        self.assertEqual([], problems, "\n".join(problems))

    def test_refusal_asserts_nothing_about_the_run_health(self) -> None:
        """The message may say a ledger is unwired; it may NOT judge the run or promise a future one.

        Kept apart from the table because its claim is a PROHIBITION rather than a per-leaf
        expectation: the danger is a well-meaning rewrite that reassures the operator ("the run is
        fine") or invites a bug report for a gap that is already tracked. Either would be a new,
        worse defect than the vague message being replaced.
        """
        _rc, out = self._exit_code_unpiped(
            "runs", "verify-ledger", RUN_ID, "--dir", str(self.tmp)
        )
        lowered = out.lower()
        for forbidden in (
            "is fine",
            "is healthy",
            "is corrupt",
            "file a bug",
            "report this",
            "will be written",
        ):
            self.assertNotIn(
                forbidden,
                lowered,
                f"refusal must not claim {forbidden!r}: it knows only that no ledger is there",
            )

    def test_machine_payload_carries_the_same_text_with_unchanged_keys(self) -> None:
        """An agent consumer gets the same honest text, and the record's KEYS do not move.

        Separate from the human table because the claim is about a STRUCTURED contract: a machine
        consumer is exactly who cannot infer missing context from a terse string, and is also who
        breaks if a key is renamed while the text improves. So the text is checked for all three
        clauses AND the payload is checked for `ok`/`error`/`exit_code` exactly.
        """
        rc, out = self._exit_code_unpiped(
            "runs", "verify-ledger", RUN_ID, "--dir", str(self.tmp), "--agent"
        )
        payload = _parse_machine(out)
        self.assertEqual(run_cli.EXIT_INVALID_INVOCATION, rc)
        self.assertEqual(
            {"ok", "error", "exit_code"},
            set(payload),
            "the absent-ledger machine record's keys are a consumed contract; only the text changed",
        )
        self.assertIs(False, payload["ok"])
        self.assertEqual(run_cli.EXIT_INVALID_INVOCATION, payload["exit_code"])
        for clause, needle in REQUIRED_CLAUSES.items():
            self.assertIn(
                needle,
                payload["error"],
                f"machine record is missing the {clause!r} clause",
            )

    def test_an_explicit_path_that_is_absent_keeps_the_bare_sentence(self) -> None:
        """For a path named VERBATIM, "file not found" is the whole truth and the rest is noise.

        Apart from the table because the expectation INVERTS: `resolve_ledger_path` honours an
        explicit path whatever it is named, so an operator who pointed at a file asked about THAT
        file. Telling them no driver writes a ledger would answer a question they did not ask. The
        exit code is unchanged, which is what keeps this from being a second refusal class.
        """
        missing = self.tmp / "nowhere" / "ledger.jsonl"
        rc, out = self._exit_code_unpiped("runs", "verify-ledger", str(missing))
        self.assertEqual(run_cli.EXIT_INVALID_INVOCATION, rc)
        self.assertIn("not found", out)
        self.assertNotIn(
            REQUIRED_CLAUSES["unwired"],
            out,
            "the unwired-driver clause is irrelevant when the operator named a path themselves",
        )


class TestPresentLedgerIsUnaffected(_CliCase):
    """A real ledger still verifies exactly as before, proving only the absent branch moved.

    THE FIXTURE IS BUILT HERE ON PURPOSE. No `ledger.jsonl` exists anywhere in the repository, which
    is the very fact the refusal now states, so there is no real one to borrow. Without this class
    the change could have silently broken verification and every other test here would still pass,
    since they all exercise the absent path.
    """

    def _seed_complete(self) -> Path:
        path = self.tmp / "run.jsonl"
        store = ledger_store.RunLedgerStore(path)
        for rec in _complete_run_records():
            store.append(rec)
        return path

    def test_verify_ledger_on_a_present_valid_ledger_still_exits_clean(self) -> None:
        """The happy path keeps its exit code and does not acquire the refusal's prose."""
        path = self._seed_complete()
        rc, out = self._exit_code_unpiped("runs", "verify-ledger", str(path))
        self.assertEqual(
            run_cli.EXIT_OK, rc, f"expected a clean verify; output: {out[:400]!r}"
        )
        self.assertNotIn(
            REQUIRED_CLAUSES["unwired"],
            out,
            "a ledger that IS present must not be told that no driver writes one",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
