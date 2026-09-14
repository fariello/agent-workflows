"""orchprobe Order 02 (`8tgg6g`): the orchestrator probe verdict cache, keyed on content.

WHAT THIS PINS, and why each half exists rather than merely that it does.

E-01/V-01, ONE ROW-WALK SHARED WITH THE RETIREMENT GATE. `runner_shared` already owned a child-table
row scanner (`parse_declared_child_orders`) that found the section by schema heading, matched rows,
skipped the alignment row, and then discarded every cell but the first. The cache needs the SAME rows
with ALL their cells, so the walk is factored into `child_table_rows` and both callers use it; a
second scanner would give the gate and the cache two definitions of "a child row". The splitter is a
PARAMETER because the two consumers legitimately need different ones: an all-cells digest must be
backtick-aware (a backticked pipe fragments later columns), while the gate reads only cell 0, which
is measured identical under both splitters, so its behavior is left bit-for-bit unchanged.

E-02/E-03/V-02/V-03, THE DIGEST AND THE `xmqv5l` TRAP. The naive key is a whole-file hash and this
repository already MEASURED that as a dead end: `ipd_lifecycle.frozen_region_digest` exists because
hashing exact bytes made a begin receipt go stale on every CORRECT execution, since a conforming
executor MUST tick checkboxes, fill `Observed evidence` and append history. So the no-op mutations
below are the load-bearing half: five edits a correct executor makes, each asserted NOT to move the
digest.

THE CONTRAST TESTS ARE THE POINT, not decoration. Four of the five properties this digest needs
ALREADY hold for `frozen_region_digest`; the ONLY thing it adds is CHILD-TABLE SENSITIVITY. So
`TheDigestDiffersFromFrozenRegionDigest` asserts the existing function does NOT move on the same
child-table edits (which is why a second function exists at all), and `TheKeyIsRowTextNotTheOrderGraph`
asserts `ipd_set_plan.parse_child_table(...).rows` is BYTE-IDENTICAL for an Id swap and a description
rewrite (which is why the key must be row TEXT). A proof that omitted those two cases could not tell
a correct implementation from the broken one, because the obvious fixture ADDS a row and a row add is
the one child-table edit BOTH keys detect.

E-04/E-05/E-06/V-04/V-05/V-06, THE STORE AND ITS TWO GUARDS. A MISS is `unknown`, never `pass`: "not
probed" and "probed and cleared" are different facts and the whole gate rests on silence no longer
meaning safe. Both polarities are cached per the maintainer's OQ-01 ruling, and
`AStaleFailCannotBeServed` is the fixture that ruling specified: apply the real remedy (move the work
into a new child, editing BOTH the checklist and the child table) and the digest MOVES, so the fail
entry is discarded rather than re-served.

FIXTURES ARE FROZEN, DELIBERATELY. Every orchestrator text below is built in this module. Pinning to
live plan files is what broke `tests/test_orchestrator_retirement.py::RealRepositorySets` (a test
asserting a plan's mutable `- Status:`), and this Set's own orchestrator forbids repeating it. The
real-corpus measurements this child owes are recorded as pasted evidence in the IPD, not as asserts
against files that change under the suite.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_lifecycle, ipd_set_plan
from agent_workflows import runner_shared as rs
from tests.support import REPO_ROOT

# ==================================================================================================
# The frozen orchestrator fixture
# ==================================================================================================
#
# Shaped after a REAL orchestrator (`yeh7gc`): a metadata block, a `## Workflow history`, an E-item
# with the sub-fields a conforming executor mutates, a prose section, and a `## Child IPDs...`
# section carrying BOTH a table and explanatory paragraphs beside it. Each of those is a mutation
# target below, so the fixture has to contain all of them.

FIXTURE = """\
# IPD: frozen orchestrator fixture

- Date: 2026-09-14
- Kind: orchestrator
- Concern: synthetic fixture for the probe cache digest.
- Scope: synthetic.
- Scope-Paths: agent_workflows/runner_shared.py
- Status: approved
- Set: fixture
- Order: 0
- Highest E allocated: 02
- Id: fix000

## Workflow history

- 2026-09-14 draft (fixture): created.

## Goal

Give the digest tests something with every mutable region a real orchestrator has.

## Detailed Implementation Checklist (TODO)

### Task group 1: sequence the Set

- [ ] E-01 SEQUENCE THE THREE CHILDREN IN ORDER, confirming each is executed before the next.
  - Depends on: none
  - Expected outcome: all children executed in order.
  - Execution state: pending

- [ ] E-02 CONFIRM the Set's records are reconciled once every child has landed.
  - Depends on: E-01
  - Expected outcome: records reconciled.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

All children are AUTHORED and lint conforming. There are NO placeholder rows.

| Order | Id | Child plan | Depends on |
| --- | --- | --- | --- |
| 01 | aaa111 | Surface the refusal reason and its remedy | none |
| 02 | bbb222 | Cache the verdict against a content digest | none |
| 03 | ccc333 | Probe every queued orchestrator | executed:aaa111, executed:bbb222 |

Order 01 is first and independent because it is a DEFECT TODAY, with or without this Set.

Order 02 is independent of 01 and could run in parallel.

## Findings

| Id | Severity | Finding |
| --- | --- | --- |
| F-1 | HIGH | A whole-file digest punishes correct execution. |

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: paste the children's statuses.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the reconciled records.
  - Observed evidence:
  - Result: pending
"""


# ---- the five NO-OP mutations (what a conforming executor does) -----------------------------------


def tick_a_checkbox(text: str) -> str:
    """Mark E-01 performed, which every conforming executor must do."""
    return text.replace("- [ ] E-01 SEQUENCE", "- [x] E-01 SEQUENCE")


def fill_observed_evidence(text: str) -> str:
    """Fill V-01's `Observed evidence`, which every conforming executor must do."""
    return text.replace(
        "  - Required evidence: paste the children's statuses.\n  - Observed evidence:\n",
        "  - Required evidence: paste the children's statuses.\n"
        "  - Observed evidence: all three read `- Status: executed` (pasted output here).\n",
    )


def append_a_history_line(text: str) -> str:
    """Append a `## Workflow history` line, which every conforming executor must do."""
    return text.replace(
        "- 2026-09-14 draft (fixture): created.",
        "- 2026-09-14 draft (fixture): created.\n"
        "- 2026-09-14 executed (fixture): performed E-01 and E-02.",
    )


def edit_prose_outside_the_child_section(text: str) -> str:
    """Rewrite a prose section (`## Findings`), which is not part of the reviewed contract."""
    return text.replace(
        "| F-1 | HIGH | A whole-file digest punishes correct execution. |",
        "| F-1 | HIGH | COMPLETELY REWRITTEN FINDING TEXT WITH DIFFERENT WORDS. |",
    )


def edit_prose_inside_the_child_section(text: str) -> str:
    """Rewrite the explanatory paragraphs that sit INSIDE `## Child IPDs...`, beside its table.

    Pins rows-not-section: including that prose would reintroduce exactly the prose sensitivity
    `frozen_region_digest` deliberately excludes.
    """
    return text.replace(
        "Order 01 is first and independent because it is a DEFECT TODAY, with or without this Set.",
        "TOTALLY DIFFERENT EXPLANATORY PARAGRAPH SAYING SOMETHING ELSE ENTIRELY ABOUT ORDERING.",
    )


NO_OP_MUTATIONS = {
    "tick-a-checkbox": tick_a_checkbox,
    "fill-observed-evidence": fill_observed_evidence,
    "append-a-history-line": append_a_history_line,
    "edit-prose-outside-the-child-section": edit_prose_outside_the_child_section,
    "edit-prose-inside-the-child-section": edit_prose_inside_the_child_section,
}


# ---- the four REAL edits (a different plan than the one that was probed) --------------------------


def edit_an_e_item_action(text: str) -> str:
    """Change what E-02 ASKS FOR, which is a different question for the probe."""
    return text.replace(
        "- [ ] E-02 CONFIRM the Set's records are reconciled once every child has landed.",
        "- [ ] E-02 PRODUCE the migration research artifact before any child runs.",
    )


def add_a_child_row(text: str) -> str:
    """Add a fourth child row (the edit a parsed-order-graph key ALSO catches)."""
    return text.replace(
        "| 03 | ccc333 | Probe every queued orchestrator | executed:aaa111, executed:bbb222 |",
        "| 03 | ccc333 | Probe every queued orchestrator | executed:aaa111, executed:bbb222 |\n"
        "| 04 | ddd444 | Reconcile the Set's records | executed:ccc333 |",
    )


def swap_a_child_id(text: str) -> str:
    """Swap a child's Id (INVISIBLE to a parsed-order-graph key; measured on `yeh7gc`)."""
    return text.replace("| 02 | bbb222 |", "| 02 | qqqqqq |")


def rewrite_a_child_description(text: str) -> str:
    """Rewrite a child's description (INVISIBLE to a parsed-order-graph key; measured)."""
    return text.replace(
        "| 02 | bbb222 | Cache the verdict against a content digest | none |",
        "| 02 | bbb222 | TOTALLY REWRITTEN: do something completely different | none |",
    )


REAL_EDITS = {
    "edit-an-e-item-action": edit_an_e_item_action,
    "add-a-child-row": add_a_child_row,
    "swap-a-child-id": swap_a_child_id,
    "rewrite-a-child-description": rewrite_a_child_description,
}

#: The two child-table edits a parsed-order-graph key CANNOT see. Named because three tests depend on
#: exactly this pair and a hand-repeated list would drift.
ROW_CONTENT_EDITS = ("swap-a-child-id", "rewrite-a-child-description")


class _Repo:
    """A throwaway directory used as a repo root (no git init: `checkout_control_root` falls back)."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def close(self) -> None:
        self._tmp.cleanup()


class RepoCase(unittest.TestCase):
    def setUp(self) -> None:
        self._repo = _Repo()
        self.addCleanup(self._repo.close)

    @property
    def root(self) -> Path:
        return self._repo.root


# ==================================================================================================
# E-01: ONE shared row-walk, returning full cell tuples
# ==================================================================================================


class ChildTableRowsTests(unittest.TestCase):
    """`child_table_rows` returns FULL cells, in document order, header included."""

    def test_every_row_comes_back_with_all_its_cells(self):
        rows = rs.child_table_rows(FIXTURE)
        self.assertEqual(
            rows,
            (
                ("Order", "Id", "Child plan", "Depends on"),
                ("01", "aaa111", "Surface the refusal reason and its remedy", "none"),
                ("02", "bbb222", "Cache the verdict against a content digest", "none"),
                (
                    "03",
                    "ccc333",
                    "Probe every queued orchestrator",
                    "executed:aaa111, executed:bbb222",
                ),
            ),
        )

    def test_the_alignment_row_is_dropped_and_the_header_is_kept(self):
        rows = rs.child_table_rows(FIXTURE)
        self.assertEqual(rows[0][0], "Order", "the header row must be included")
        for row in rows:
            self.assertNotIn(
                "---", "".join(row), "an alignment row leaked into the rows"
            )

    def test_a_table_in_another_section_is_not_read(self):
        """The `## Findings` table above must not contribute rows."""
        rows = rs.child_table_rows(FIXTURE)
        flat = "\n".join("|".join(r) for r in rows)
        self.assertNotIn("F-1", flat)
        self.assertNotIn("Severity", flat)

    def test_an_absent_section_yields_no_rows_rather_than_raising(self):
        self.assertEqual(rs.child_table_rows("# IPD: no table here\n"), ())
        self.assertEqual(rs.child_table_rows(""), ())

    def test_a_backticked_pipe_does_NOT_fragment_the_row(self):
        """The measured live defect: three real orchestrators carry a backticked pipe.

        `94dhrt`, `mvz3d2` and `rreixg` each contain such a row, one splitting 12 cells instead of 4
        under the naive splitter. Harmless when only cell 0 is read; NOT harmless for an all-cells
        digest, where a backticked plan filename would fragment into bogus columns.
        """

        text = (
            f"## {rs._CHILD_IPDS_HEADING}\n\n"
            "| Order | Id | Child plan | Depends on |\n"
            "| --- | --- | --- | --- |\n"
            "| 01 | aaa111 | see `aw oc run | agy run` for the host split | none |\n"
        )
        aware = rs.child_table_rows(text)
        naive = rs.child_table_rows(text, backtick_aware=False)
        self.assertEqual(
            len(aware[-1]), 4, f"backtick-aware split fragmented: {aware[-1]}"
        )
        self.assertEqual(len(naive[-1]), 5, "the naive split is expected to fragment")
        self.assertEqual(
            aware[-1][0], naive[-1][0], "cell 0 must agree under both splitters"
        )


class TheRowWalkIsSharedWithTheRetirementGate(unittest.TestCase):
    """E-01: ONE definition of "a child row", consumed by the gate AND the digest.

    Asserted structurally (the gate's body CALLS the shared helper) rather than by output agreement,
    because two independent scanners can agree today and drift tomorrow, which is the entire failure
    class `2r306y`/`818uru` made this module's admission rule about.
    """

    def test_parse_declared_child_orders_calls_the_shared_row_walk(self):
        import inspect

        src = inspect.getsource(rs.parse_declared_child_orders)
        self.assertIn("child_table_rows(", src)
        self.assertNotIn(
            "_TABLE_ROW_RE.match",
            src,
            "the gate must not keep its own row matcher beside the shared walk",
        )

    def test_the_digest_payload_also_calls_the_shared_row_walk(self):
        import inspect

        self.assertIn("child_table_rows(", inspect.getsource(rs.probe_cache_payload))

    def test_the_gate_keeps_the_naive_split_so_its_behavior_is_unchanged(self):
        """The gate reads only cell 0, where both splitters are measured identical.

        Pinned so a later reader does not "tidy" the gate onto the backtick-aware splitter as part of
        a cache change: that would be a behavior change to a retirement gate made by a plan about a
        cache.
        """
        import inspect

        src = inspect.getsource(rs.parse_declared_child_orders)
        self.assertIn("backtick_aware=False", src)

    def test_the_gate_still_reads_the_five_real_column_shapes(self):
        """Regression fence for the refactor: the Order tokens must be unchanged.

        The five layouts share ONLY the first column and `rununify` has no `Id` column at all, so a
        row-walk change is exactly the kind of edit that would break one shape silently.
        """

        shapes = {
            "orchretire": ["Order", "Id", "Child", "Depends on"],
            "wslayout": ["Order", "Id", "What it does", "Set dependencies"],
            "runprofile": ["Order", "Id", "Child", "Responsibility", "Depends on"],
            "lanectn": [
                "Order",
                "Id",
                "Depth",
                "Requirements owned",
                "Prerequisite",
                "What it delivers",
            ],
            "rununify": ["Order", "What it does", "Depends on"],
        }
        for name, header in shapes.items():
            with self.subTest(shape=name):
                rows = ["| " + " | ".join(["01"] + ["x"] * (len(header) - 1)) + " |"]
                rows.append(
                    "| " + " | ".join(["02"] + ["y"] * (len(header) - 1)) + " |"
                )
                text = (
                    f"## {rs._CHILD_IPDS_HEADING}\n\n"
                    + "| "
                    + " | ".join(header)
                    + " |\n"
                    + "|"
                    + "|".join(["---"] * len(header))
                    + "|\n"
                    + "\n".join(rows)
                    + "\n"
                )
                tokens, parsed = rs.parse_declared_child_orders(text)
                self.assertTrue(parsed)
                self.assertEqual(tokens, ("01", "02"))

    def test_no_new_module_level_first_party_import_in_runner_shared(self):
        """`runner_shared` must keep exactly ONE module-level first-party import.

        It has always had exactly one (`render_stream`) plus the designated peer `runner_profiles`,
        and reaches `ipd_lint`/`ipd_schema`/`ipd_lifecycle` through function-local imports. A
        module-level import added here would change the import graph for BOTH host drivers.
        """

        import ast

        tree = ast.parse(Path(rs.__file__).read_text(encoding="utf-8"))
        module_level = []
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
                "agent_workflows"
            ):
                module_level.append(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("agent_workflows"):
                        module_level.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module == "agent_workflows":
                module_level.extend(a.name for a in node.names)
        # `from agent_workflows import runner_profiles` reports module `agent_workflows`.
        flat = []
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module == "agent_workflows":
                flat.extend(f"agent_workflows.{a.name}" for a in node.names)
        allowed = {"agent_workflows.render_stream", "agent_workflows.runner_profiles"}
        found = {m for m in module_level if m != "agent_workflows"} | set(flat)
        self.assertEqual(
            found,
            allowed,
            "runner_shared gained a module-level first-party import: "
            f"{sorted(found - allowed)}",
        )


# ==================================================================================================
# E-02 / E-03: the digest, and the `xmqv5l` trap it must avoid
# ==================================================================================================


class TheDigestIgnoresWhatCorrectExecutionChanges(unittest.TestCase):
    """E-03: the five NO-OP mutations. This is the `xmqv5l` proof."""

    def test_each_executor_mutation_leaves_the_digest_IDENTICAL(self):
        base = rs.probe_cache_digest(FIXTURE)
        for name, mutate in NO_OP_MUTATIONS.items():
            with self.subTest(mutation=name):
                mutated = mutate(FIXTURE)
                self.assertNotEqual(
                    mutated, FIXTURE, f"{name} did not actually change the text"
                )
                self.assertEqual(
                    rs.probe_cache_digest(mutated),
                    base,
                    f"{name} moved the digest; a conforming executor would re-probe on every tick",
                )

    def test_the_payload_carries_no_prose_from_inside_the_child_section(self):
        payload = rs.probe_cache_payload(FIXTURE)
        blob = json.dumps(payload)
        self.assertNotIn("DEFECT TODAY", blob)
        self.assertNotIn("could run in parallel", blob)

    def test_the_payload_carries_the_row_cell_TEXT(self):
        payload = rs.probe_cache_payload(FIXTURE)
        blob = json.dumps(payload)
        self.assertIn("bbb222", blob)
        self.assertIn("Cache the verdict against a content digest", blob)

    def test_the_payload_carries_no_scope_paths_and_no_V_item_text(self):
        """The deliberate divergence from `frozen_region_digest`, asserted rather than described."""
        blob = json.dumps(rs.probe_cache_payload(FIXTURE))
        self.assertNotIn("agent_workflows/runner_shared.py", blob)
        self.assertNotIn("paste the children's statuses", blob)


class TheDigestChangesForARealEdit(unittest.TestCase):
    """E-03: the four REAL edits. Each is a different question for the probe."""

    def test_each_real_edit_MOVES_the_digest(self):
        base = rs.probe_cache_digest(FIXTURE)
        for name, mutate in REAL_EDITS.items():
            with self.subTest(mutation=name):
                mutated = mutate(FIXTURE)
                self.assertNotEqual(
                    mutated, FIXTURE, f"{name} did not actually change the text"
                )
                self.assertNotEqual(
                    rs.probe_cache_digest(mutated),
                    base,
                    f"{name} left the digest unchanged; the probe would serve a stale verdict",
                )


class TheDigestIsDeterministic(unittest.TestCase):
    """E-02: stable across PROCESSES, not merely repeatable within one."""

    def test_two_separate_interpreters_agree(self):
        script = (
            "import sys;"
            f"sys.path.insert(0, {str(REPO_ROOT)!r});"
            "from agent_workflows import runner_shared as rs;"
            "import tests.test_orchestrator_probe_cache as m;"
            "print(rs.probe_cache_digest(m.FIXTURE))"
        )
        outs = []
        for _ in range(2):
            proc = subprocess.run(
                [sys.executable, "-c", script],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            outs.append(proc.stdout.strip())
        self.assertEqual(outs[0], outs[1])
        self.assertEqual(outs[0], rs.probe_cache_digest(FIXTURE))

    def test_the_docstring_states_the_divergence_from_frozen_region_digest(self):
        doc = rs.probe_cache_digest.__doc__ or ""
        self.assertIn("frozen_region_digest", doc)
        self.assertIn("CHILD-TABLE ROWS ARE IN", doc)
        self.assertIn("V-ITEM TEXT ARE OUT", doc)


class TheDigestDiffersFromFrozenRegionDigest(unittest.TestCase):
    """E-02's ONLY genuinely new behavior, asserted as a CONTRAST.

    Four of the five properties above already hold for `frozen_region_digest`. If this class ever
    passed vacuously (both functions moving on a child-table edit), this whole child would be cost
    with no benefit, so the contrast is a test rather than a claim in a docstring.
    """

    def test_frozen_region_digest_does_NOT_move_on_a_child_table_edit(self):
        base = ipd_lifecycle.frozen_region_digest(FIXTURE)
        for name in ("add-a-child-row",) + ROW_CONTENT_EDITS:
            with self.subTest(mutation=name):
                mutated = REAL_EDITS[name](FIXTURE)
                self.assertEqual(
                    ipd_lifecycle.frozen_region_digest(mutated),
                    base,
                    "frozen_region_digest moved on a child-table edit, so this "
                    "child's digest has no reason to exist; re-derive the design",
                )

    def test_the_probe_digest_DOES_move_on_those_same_edits(self):
        base = rs.probe_cache_digest(FIXTURE)
        for name in ("add-a-child-row",) + ROW_CONTENT_EDITS:
            with self.subTest(mutation=name):
                self.assertNotEqual(
                    rs.probe_cache_digest(REAL_EDITS[name](FIXTURE)), base
                )

    def test_both_digests_agree_on_the_executor_mutations(self):
        """The four properties that ALREADY held: neither function may move on them."""
        for name in (
            "tick-a-checkbox",
            "fill-observed-evidence",
            "append-a-history-line",
            "edit-prose-outside-the-child-section",
        ):
            with self.subTest(mutation=name):
                mutated = NO_OP_MUTATIONS[name](FIXTURE)
                self.assertEqual(
                    ipd_lifecycle.frozen_region_digest(mutated),
                    ipd_lifecycle.frozen_region_digest(FIXTURE),
                )
                self.assertEqual(
                    rs.probe_cache_digest(mutated), rs.probe_cache_digest(FIXTURE)
                )

    def test_neither_existing_digest_function_was_modified(self):
        """This child's fence: `plan_content_digest`/`frozen_region_digest` are gate inputs."""
        for fn in (
            ipd_lifecycle.plan_content_digest,
            ipd_lifecycle.frozen_region_digest,
        ):
            self.assertTrue(callable(fn))
        # A `Scope-Paths` fence cannot be asserted at runtime, so assert the OBSERVABLE property
        # those two functions are relied on for instead: the frozen digest still ignores execution
        # state (the `xmqv5l` fix) and still moves on an E-item edit (the receipt guard).
        base = ipd_lifecycle.frozen_region_digest(FIXTURE)
        self.assertEqual(
            ipd_lifecycle.frozen_region_digest(tick_a_checkbox(FIXTURE)), base
        )
        self.assertNotEqual(
            ipd_lifecycle.frozen_region_digest(edit_an_e_item_action(FIXTURE)), base
        )


class TheKeyIsRowTextNotTheOrderGraph(unittest.TestCase):
    """F-10: the correction the whole justification rests on.

    `ipd_set_plan.parse_child_table` returns `{order: (dep_orders,)}`. A key built on it would be
    sensitive to row COUNT and BLIND to row CONTENT, and since child 03 sends the child table AS the
    probe payload, a row edit the key ignored would serve a stale verdict under apparent authority.
    """

    def test_parse_child_table_rows_are_BYTE_IDENTICAL_for_a_row_content_edit(self):
        base = ipd_set_plan.parse_child_table(FIXTURE).rows
        for name in ROW_CONTENT_EDITS:
            with self.subTest(mutation=name):
                self.assertEqual(
                    ipd_set_plan.parse_child_table(REAL_EDITS[name](FIXTURE)).rows,
                    base,
                    "parse_child_table became content-sensitive; re-check whether "
                    "row-cell extraction is still required",
                )

    def test_the_row_cells_DO_distinguish_those_same_edits(self):
        base = rs.child_table_rows(FIXTURE)
        for name in ROW_CONTENT_EDITS:
            with self.subTest(mutation=name):
                self.assertNotEqual(
                    rs.child_table_rows(REAL_EDITS[name](FIXTURE)), base
                )

    def test_a_row_ADD_is_the_one_edit_BOTH_keys_catch(self):
        """Why the OQ-01 fixture alone cannot prove a correct implementation."""
        base = ipd_set_plan.parse_child_table(FIXTURE).rows
        self.assertNotEqual(
            ipd_set_plan.parse_child_table(add_a_child_row(FIXTURE)).rows, base
        )
        self.assertNotEqual(
            rs.child_table_rows(add_a_child_row(FIXTURE)), rs.child_table_rows(FIXTURE)
        )


# ==================================================================================================
# E-04: the verdict store
# ==================================================================================================


class VerdictStoreTests(RepoCase):
    """E-04: write-then-read round trips, the recorded model, and a corrupt entry."""

    def test_write_then_read_round_trips_with_the_model(self):
        digest = rs.probe_cache_digest(FIXTURE)
        rs.record_probe_verdict(
            self.root, digest, rs.PROBE_VERDICT_PASS, model="vendor/model-x"
        )
        got = rs.read_probe_verdict(self.root, digest, model="vendor/model-x")
        self.assertEqual(got.verdict, rs.PROBE_VERDICT_PASS)
        self.assertEqual(got.model, "vendor/model-x")
        self.assertTrue(got.recorded_at)
        self.assertTrue(got.is_hit)

    def test_the_store_path_derives_from_checkout_control_root(self):
        path = rs.probe_verdict_store_path(self.root)
        expected = (
            ipd_lifecycle.checkout_control_root(self.root)
            / "state"
            / "runtime"
            / "orchestrator-probe-verdicts.json"
        )
        self.assertEqual(path, expected)

    def test_a_linked_worktree_resolves_to_the_SAME_store(self):
        """The `dh0uno` property: an in-lane `repo_root` is the LANE, so hand-composition forks."""

        import os

        repo = self.root / "main"
        repo.mkdir()
        env = {
            **os.environ,
            "GIT_CONFIG_GLOBAL": str(self.root / "gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
        }

        def git(*args: str, cwd: Path = repo) -> None:
            subprocess.run(
                ["git", *args], cwd=str(cwd), check=True, env=env, capture_output=True
            )

        git("init", "-q", ".")
        git("config", "user.email", "fixture@example.invalid")
        git("config", "user.name", "fixture")
        (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
        git("add", "seed.txt")
        git("commit", "-qm", "seed")
        lane = self.root / "lane"
        git("worktree", "add", "-q", "-b", "lane", str(lane))

        self.assertEqual(
            rs.probe_verdict_store_path(repo),
            rs.probe_verdict_store_path(lane),
            "the lane resolved to a SECOND store the driver cannot see (dh0uno)",
        )

    def test_recording_one_verdict_does_not_discard_another(self):
        a = rs.probe_cache_digest(FIXTURE)
        b = rs.probe_cache_digest(add_a_child_row(FIXTURE))
        rs.record_probe_verdict(self.root, a, rs.PROBE_VERDICT_PASS, model="m")
        rs.record_probe_verdict(self.root, b, rs.PROBE_VERDICT_FAIL, model="m")
        self.assertEqual(
            rs.read_probe_verdict(self.root, a, model="m").verdict,
            rs.PROBE_VERDICT_PASS,
        )
        self.assertEqual(
            rs.read_probe_verdict(self.root, b, model="m").verdict,
            rs.PROBE_VERDICT_FAIL,
        )

    def test_a_corrupt_store_reads_as_ABSENT_rather_than_raising(self):
        digest = rs.probe_cache_digest(FIXTURE)
        rs.record_probe_verdict(self.root, digest, rs.PROBE_VERDICT_PASS, model="m")
        path = rs.probe_verdict_store_path(self.root)
        path.write_text('{"entries": {"trunc', encoding="utf-8")
        got = rs.read_probe_verdict(self.root, digest, model="m")
        self.assertEqual(got.verdict, rs.PROBE_VERDICT_UNKNOWN)
        self.assertEqual(got.stale_reason, rs.PROBE_STALE_MISS)

    def test_a_corrupt_ENTRY_reads_as_absent_rather_than_raising(self):
        digest = rs.probe_cache_digest(FIXTURE)
        rs.record_probe_verdict(self.root, digest, rs.PROBE_VERDICT_PASS, model="m")
        path = rs.probe_verdict_store_path(self.root)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["entries"][digest] = "not-an-object"
        path.write_text(json.dumps(payload), encoding="utf-8")
        got = rs.read_probe_verdict(self.root, digest, model="m")
        self.assertEqual(got.verdict, rs.PROBE_VERDICT_UNKNOWN)
        self.assertEqual(got.stale_reason, rs.PROBE_STALE_CORRUPT)

    def test_an_unrecognized_verdict_value_reads_as_unknown(self):
        digest = rs.probe_cache_digest(FIXTURE)
        rs.record_probe_verdict(self.root, digest, rs.PROBE_VERDICT_PASS, model="m")
        path = rs.probe_verdict_store_path(self.root)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["entries"][digest]["verdict"] = "probably-fine"
        path.write_text(json.dumps(payload), encoding="utf-8")
        got = rs.read_probe_verdict(self.root, digest, model="m")
        self.assertEqual(got.verdict, rs.PROBE_VERDICT_UNKNOWN)
        self.assertEqual(got.stale_reason, rs.PROBE_STALE_CORRUPT)

    def test_recording_unknown_is_REFUSED(self):
        """`unknown` is the ABSENCE of an answer; storing it would make 'not probed' a fact."""
        with self.assertRaises(ValueError):
            rs.record_probe_verdict(
                self.root, "d" * 64, rs.PROBE_VERDICT_UNKNOWN, model="m"
            )


class TheStoreIsGitignoredInAnAdopter(unittest.TestCase):
    """E-04's prerequisite, verified in a FRESH repo carrying ONLY installer output.

    THIS REPOSITORY PROVES NOTHING HERE. `.aw/state/` is ignored here by the ROOT `.gitignore`, which
    the installer explicitly never writes, so a `git check-ignore` run in this tree would pass and
    say nothing about an adopter. The framework-owned `.aw/.gitignore` gained an anchored `/state/`
    entry in BOTH `_AW_GITIGNORE_TEMPLATE` (fresh installs) and the `_ensure_aw_gitignore` back-fill
    (already-installed adopters) on 2026-09-12, commit `ee38864c`, which is the prerequisite this
    child's E-04 waited on.
    """

    def _fresh_repo(self, base: Path) -> Path:
        import os

        repo = base / "adopter"
        repo.mkdir()
        env = {
            **os.environ,
            "GIT_CONFIG_GLOBAL": str(base / "gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
        }
        subprocess.run(
            ["git", "init", "-q", "."],
            cwd=str(repo),
            check=True,
            env=env,
            capture_output=True,
        )
        self._env = env
        return repo

    def test_check_ignore_matches_the_framework_owned_gitignore(self):
        from agent_workflows import engine

        with tempfile.TemporaryDirectory() as td:
            repo = self._fresh_repo(Path(td))
            engine._ensure_aw_gitignore(repo)
            rel = ".aw/state/runtime/orchestrator-probe-verdicts.json"
            proc = subprocess.run(
                ["git", "check-ignore", "-v", rel],
                cwd=str(repo),
                capture_output=True,
                text=True,
                env=self._env,
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"the verdict store is NOT ignored in an adopter: {proc.stderr}",
            )
            self.assertIn(".aw/.gitignore", proc.stdout)

    def test_the_template_and_the_backfill_BOTH_carry_the_rule(self):
        """A template-only entry reaches FRESH installs only; the back-fill is a literal list."""
        from agent_workflows import engine

        self.assertIn("/state/", engine._AW_GITIGNORE_TEMPLATE)
        with tempfile.TemporaryDirectory() as td:
            repo = self._fresh_repo(Path(td))
            gi = repo / ".aw" / ".gitignore"
            gi.parent.mkdir(parents=True, exist_ok=True)
            gi.write_text(
                "records/*/untracked/\n", encoding="utf-8"
            )  # pre-`state/` adopter
            engine._ensure_aw_gitignore(repo)
            self.assertIn("/state/", gi.read_text(encoding="utf-8"))


# ==================================================================================================
# E-05: a MISS fails closed, and both polarities are cached
# ==================================================================================================


class AMissFailsClosed(RepoCase):
    """E-05: `unknown`, NEVER `pass`. The gate's whole premise."""

    def test_an_empty_store_returns_unknown(self):
        got = rs.read_probe_verdict(
            self.root, rs.probe_cache_digest(FIXTURE), model="m"
        )
        self.assertEqual(got.verdict, rs.PROBE_VERDICT_UNKNOWN)
        self.assertNotEqual(got.verdict, rs.PROBE_VERDICT_PASS)
        self.assertEqual(got.stale_reason, rs.PROBE_STALE_MISS)
        self.assertFalse(got.is_hit)

    def test_a_digest_that_moved_is_a_MISS_not_the_old_verdict(self):
        rs.record_probe_verdict(
            self.root, rs.probe_cache_digest(FIXTURE), rs.PROBE_VERDICT_PASS, model="m"
        )
        moved = rs.probe_cache_digest(edit_an_e_item_action(FIXTURE))
        self.assertEqual(
            rs.read_probe_verdict(self.root, moved, model="m").verdict,
            rs.PROBE_VERDICT_UNKNOWN,
        )

    def test_the_three_states_are_distinct_values(self):
        self.assertEqual(
            len(
                {rs.PROBE_VERDICT_PASS, rs.PROBE_VERDICT_FAIL, rs.PROBE_VERDICT_UNKNOWN}
            ),
            3,
        )


class AStaleFailCannotBeServed(RepoCase):
    """OQ-01's ruling, as the fixture the maintainer specified.

    BOTH polarities are cached, and re-evaluate-on-change is what makes a cached FAIL safe: the
    remedy for a fail is to move the work into a NEW CHILD, which edits BOTH the parent's checklist
    text and its child table, and the digest covers both. So the remedy is APPLIED here rather than
    argued about.
    """

    #: The remedy, applied to the fixture: E-02's parent-only work moves OUT of the checklist and INTO
    #: a new child row. Exactly the two edits the ruling names.
    @staticmethod
    def apply_the_remedy(text: str) -> str:
        without_the_item = text.replace(
            "- [ ] E-02 CONFIRM the Set's records are reconciled once every child has landed.\n"
            "  - Depends on: E-01\n"
            "  - Expected outcome: records reconciled.\n"
            "  - Execution state: pending\n\n",
            "",
        )
        assert without_the_item != text, "the checklist item was not removed"
        with_the_child = add_a_child_row(without_the_item)
        assert with_the_child != without_the_item, "the child row was not added"
        return with_the_child

    def test_the_remedy_MOVES_the_digest_so_the_fail_entry_is_discarded(self):
        before = rs.probe_cache_digest(FIXTURE)
        rs.record_probe_verdict(self.root, before, rs.PROBE_VERDICT_FAIL, model="m")
        self.assertEqual(
            rs.read_probe_verdict(self.root, before, model="m").verdict,
            rs.PROBE_VERDICT_FAIL,
            "the fail must be served BEFORE the remedy, or this test proves nothing",
        )

        fixed = self.apply_the_remedy(FIXTURE)
        after = rs.probe_cache_digest(fixed)
        self.assertNotEqual(after, before, "the remedy did not move the digest")
        got = rs.read_probe_verdict(self.root, after, model="m")
        self.assertEqual(got.verdict, rs.PROBE_VERDICT_UNKNOWN)
        self.assertEqual(got.stale_reason, rs.PROBE_STALE_MISS)

    def test_a_ROW_ONLY_remedy_also_discards_the_stale_fail(self):
        """The half of the remedy that ONLY child-table sensitivity can see.

        Adding a child that covers the parent's work while LEAVING the parent's item as sequencing
        prose is a real authoring outcome, and it is the case a parsed-order-graph key would get
        wrong in the dangerous direction: the fail entry would still be served after the work was
        genuinely moved. So this is asserted separately from the two-edit remedy above, whose
        checklist half moves the key on its own and therefore cannot prove this property.
        """
        before = rs.probe_cache_digest(FIXTURE)
        rs.record_probe_verdict(self.root, before, rs.PROBE_VERDICT_FAIL, model="m")
        self.assertEqual(
            rs.read_probe_verdict(self.root, before, model="m").verdict,
            rs.PROBE_VERDICT_FAIL,
        )

        after = rs.probe_cache_digest(add_a_child_row(FIXTURE))
        self.assertNotEqual(
            after,
            before,
            "a child-table-only remedy left the key unchanged, so a fixed "
            "orchestrator would keep being served its old FAIL",
        )
        self.assertEqual(
            rs.read_probe_verdict(self.root, after, model="m").verdict,
            rs.PROBE_VERDICT_UNKNOWN,
        )

    def test_the_remedy_is_detected_by_the_checklist_edit_ALONE_too(self):
        """Belt and braces: either half of the remedy moves the key on its own.

        Pinned because a remedy that only added a child row (without removing the parent item) is a
        real authoring outcome too, and a key that needed BOTH edits would serve a stale fail for it.
        """
        base = rs.probe_cache_digest(FIXTURE)
        checklist_only = FIXTURE.replace(
            "- [ ] E-02 CONFIRM the Set's records are reconciled once every child has landed.",
            "- [ ] E-02 SEQUENCE the fourth child once the third is executed.",
        )
        self.assertNotEqual(rs.probe_cache_digest(checklist_only), base)
        self.assertNotEqual(rs.probe_cache_digest(add_a_child_row(FIXTURE)), base)


# ==================================================================================================
# E-06: the staleness guard
# ==================================================================================================


class StalenessRuleTests(RepoCase):
    """E-06: a digest match proves the plan did not change, NOT that the answer is still good."""

    def _record(self, *, model: str | None, days_ago: int, digest: str = "") -> str:
        digest = digest or rs.probe_cache_digest(FIXTURE)
        when = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days_ago)
        rs.record_probe_verdict(
            self.root,
            digest,
            rs.PROBE_VERDICT_PASS,
            model=model,
            recorded_at=when.replace(microsecond=0).isoformat(),
        )
        return digest

    def test_a_fresh_verdict_is_SERVED(self):
        digest = self._record(model="vendor/model-x", days_ago=1)
        got = rs.read_probe_verdict(self.root, digest, model="vendor/model-x")
        self.assertEqual(got.verdict, rs.PROBE_VERDICT_PASS)
        self.assertTrue(got.is_hit)

    def test_a_verdict_past_the_bound_reads_as_unknown(self):
        digest = self._record(model="vendor/model-x", days_ago=400)
        got = rs.read_probe_verdict(self.root, digest, model="vendor/model-x")
        self.assertEqual(got.verdict, rs.PROBE_VERDICT_UNKNOWN)
        self.assertEqual(got.stale_reason, rs.PROBE_STALE_TOO_OLD)
        self.assertEqual(
            got.recorded_verdict,
            rs.PROBE_VERDICT_PASS,
            "the reader must still REPORT what was stored, so a human can see what expired",
        )

    def test_a_DIFFERENT_model_reads_as_unknown(self):
        digest = self._record(model="vendor/model-x", days_ago=1)
        got = rs.read_probe_verdict(self.root, digest, model="vendor/model-y")
        self.assertEqual(got.verdict, rs.PROBE_VERDICT_UNKNOWN)
        self.assertEqual(got.stale_reason, rs.PROBE_STALE_MODEL_CHANGED)

    def test_the_bound_is_configurable_per_read(self):
        digest = self._record(model="vendor/model-x", days_ago=10)
        self.assertEqual(
            rs.read_probe_verdict(
                self.root, digest, model="vendor/model-x", max_age_days=30
            ).verdict,
            rs.PROBE_VERDICT_PASS,
        )
        self.assertEqual(
            rs.read_probe_verdict(
                self.root, digest, model="vendor/model-x", max_age_days=5
            ).verdict,
            rs.PROBE_VERDICT_UNKNOWN,
        )

    def test_the_default_bound_is_a_named_constant_carrying_its_rationale(self):
        """The bound must be a constant with a recorded WHY, not a literal at a call site."""
        import inspect

        self.assertEqual(rs.DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS, 30)
        src = inspect.getsource(rs)
        marker = "DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS = 30"
        self.assertIn(marker, src)
        preamble = src[max(0, src.index(marker) - 1600) : src.index(marker)]
        self.assertIn("WHY 30 DAYS", preamble)
        self.assertIn("WHY A BOUND AT ALL", preamble)
        self.assertIn(
            "max_age_days: int = DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS",
            src,
            "the reader must default to the named constant, not to a literal",
        )

    def test_an_unparseable_timestamp_is_treated_as_infinitely_old(self):
        digest = self._record(model="vendor/model-x", days_ago=1)
        path = rs.probe_verdict_store_path(self.root)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["entries"][digest]["recorded_at"] = "not-a-timestamp"
        path.write_text(json.dumps(payload), encoding="utf-8")
        got = rs.read_probe_verdict(self.root, digest, model="vendor/model-x")
        self.assertEqual(got.verdict, rs.PROBE_VERDICT_UNKNOWN)
        self.assertEqual(got.stale_reason, rs.PROBE_STALE_TOO_OLD)


class TheHostDefaultModelCaseIsDecided(RepoCase):
    """F-12: `runner_profiles.resolve` returns `model=None` with provenance `host-default`.

    DECISION: when EITHER side cannot name a model, the model comparison is SKIPPED and the TIME
    BOUND alone decides. The rejected alternative (an unknown model never matches) would make the
    cache miss in the COMMON case, i.e. a cache that does not exist. The honest cost is stated in
    `read_probe_verdict`'s docstring and pinned by the last test here.
    """

    def _record(self, *, model: str | None, days_ago: int) -> str:
        digest = rs.probe_cache_digest(FIXTURE)
        when = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days_ago)
        rs.record_probe_verdict(
            self.root,
            digest,
            rs.PROBE_VERDICT_PASS,
            model=model,
            recorded_at=when.replace(microsecond=0).isoformat(),
        )
        return digest

    def test_the_premise_is_real_a_resolve_can_return_model_None(self):
        """Asserted rather than trusted, so the rule's rationale cannot quietly become false."""
        from agent_workflows import runner_profiles

        cfg = runner_profiles.ProfileConfig()
        resolved = runner_profiles.resolve(cfg, runner="opencode")
        self.assertIsNone(resolved.model)
        self.assertEqual(
            resolved.provenance.get("model"), runner_profiles.PROVENANCE_HOST_DEFAULT
        )

    def test_no_model_either_side_within_the_bound_is_SERVED(self):
        digest = self._record(model=None, days_ago=1)
        got = rs.read_probe_verdict(self.root, digest, model=None)
        self.assertEqual(got.verdict, rs.PROBE_VERDICT_PASS)
        self.assertEqual(got.model, "")

    def test_no_model_either_side_PAST_the_bound_is_unknown(self):
        """The time bound is the guard that ALWAYS applies; that is why it carries this case."""
        digest = self._record(model=None, days_ago=400)
        got = rs.read_probe_verdict(self.root, digest, model=None)
        self.assertEqual(got.verdict, rs.PROBE_VERDICT_UNKNOWN)
        self.assertEqual(got.stale_reason, rs.PROBE_STALE_TOO_OLD)

    def test_a_named_current_model_against_an_UNRECORDED_one_is_served(self):
        digest = self._record(model=None, days_ago=1)
        self.assertEqual(
            rs.read_probe_verdict(self.root, digest, model="vendor/model-x").verdict,
            rs.PROBE_VERDICT_PASS,
        )

    def test_an_UNNAMED_current_model_against_a_recorded_one_is_served(self):
        digest = self._record(model="vendor/model-x", days_ago=1)
        self.assertEqual(
            rs.read_probe_verdict(self.root, digest, model=None).verdict,
            rs.PROBE_VERDICT_PASS,
        )

    def test_the_docstring_states_the_decision_and_its_cost(self):
        doc = rs.read_probe_verdict.__doc__ or ""
        self.assertIn("model=None", doc)
        self.assertIn("TIME BOUND alone decides", doc)
        self.assertIn("honest limit", doc)


# ==================================================================================================
# E-07: one shared definition, no deeper oc->agy coupling
# ==================================================================================================


class BothHostsShareEverySymbol(unittest.TestCase):
    """E-07: object identity, not grep (`2r306y`/`818uru`)."""

    NEW_SYMBOLS = (
        "child_table_rows",
        "probe_cache_payload",
        "probe_cache_digest",
        "probe_verdict_store_path",
        "record_probe_verdict",
        "read_probe_verdict",
        "ProbeVerdict",
        "PROBE_VERDICT_PASS",
        "PROBE_VERDICT_FAIL",
        "PROBE_VERDICT_UNKNOWN",
        "PROBE_VERDICT_STORE_SCHEMA_VERSION",
        "DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS",
        "PROBE_STALE_MISS",
        "PROBE_STALE_CORRUPT",
        "PROBE_STALE_MODEL_CHANGED",
        "PROBE_STALE_TOO_OLD",
    )

    def test_every_new_symbol_is_defined_in_runner_shared(self):
        for name in self.NEW_SYMBOLS:
            with self.subTest(symbol=name):
                self.assertTrue(hasattr(rs, name), f"{name} is not in runner_shared")

    def test_exactly_one_definition_package_wide(self):
        import ast

        pkg = Path(rs.__file__).parent
        for name in self.NEW_SYMBOLS:
            with self.subTest(symbol=name):
                definers = []
                for path in sorted(pkg.glob("*.py")):
                    tree = ast.parse(path.read_text(encoding="utf-8"))
                    for node in tree.body:
                        if (
                            isinstance(node, (ast.FunctionDef, ast.ClassDef))
                            and node.name == name
                        ):
                            definers.append(path.name)
                        elif isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name) and target.id == name:
                                    definers.append(path.name)
                self.assertEqual(
                    definers,
                    ["runner_shared.py"],
                    f"{name} is defined in {definers}; a re-fork",
                )

    def test_both_hosts_reach_the_SAME_object(self):
        from agent_workflows import agy_runipd, oc_runipd

        for name in self.NEW_SYMBOLS:
            with self.subTest(symbol=name):
                shared = getattr(rs, name)
                for host in (oc_runipd, agy_runipd):
                    reached = getattr(host.runner_shared, name)
                    self.assertIs(
                        reached,
                        shared,
                        f"{host.__name__} reaches a DIFFERENT {name} object",
                    )

    def test_the_oc_to_agy_import_count_did_not_increase(self):
        """Measured 47 at both review rounds, 48 at execution, 57 after the 2026-09-14 recovery.

        The absolute number is deliberately NOT the point: backlog `cnwy8g` recorded 40, the reviews
        measured 47, execution measured 48, and this worktree measures 57, so the literal is a
        BASELINE and not a target. What is asserted is that THIS child added none, which is checked
        directly by the `NEW_SYMBOLS` loop below and is the property the test is named for.

        RE-MEASURED 2026-09-14 from 48 to 57, per the instruction in this assertion's own message
        ("if the change is unrelated work, re-measure and update the baseline with the new count and
        a note"). The nine added names are all UNRELATED to this child and all arrived with lane
        `st5klo` (specvis-01), integrated in the same recovery pass that integrated this lane:

            SPEC_NOT_FINALIZED, SPEC_RECONCILED, SPEC_RECONCILE_REFUSED, queue_plan_path,
            queue_with_plan_paths, record_item_spec_edits, report_run_spec_edits, spec_edit_record,
            spec_edit_summary

        Measured by diffing the import list at `fea2c9f8` (48) against HEAD (57), so the attribution
        is computed and not assumed. NOT loosened to an inequality: an exact baseline is what makes
        the NEXT unrelated increase visible at all, and `cnwy8g`'s standing complaint is that this
        coupling keeps growing quietly. Note the growth is itself the defect `cnwy8g` tracks: these
        nine SHOULD reach both hosts through `runner_shared`, and `st5klo` routed them through
        `oc_runipd` instead.
        """

        import ast

        agy_path = Path(rs.__file__).parent / "agy_runipd.py"
        self.assertTrue(agy_path.is_file())
        tree = ast.parse(agy_path.read_text(encoding="utf-8"))
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and "oc_runipd" in (node.module or ""):
                imported.extend(a.name for a in node.names)
        for name in BothHostsShareEverySymbol.NEW_SYMBOLS:
            self.assertNotIn(
                name,
                imported,
                f"{name} is imported from oc_runipd; both hosts must reach it "
                "through runner_shared",
            )
        self.assertEqual(
            len(imported),
            57,
            "the oc->agy import count moved. This test's job is to fail when THIS "
            "child's symbols deepen the coupling; if the change is unrelated work, "
            "re-measure and update the baseline with the new count and a note.",
        )
