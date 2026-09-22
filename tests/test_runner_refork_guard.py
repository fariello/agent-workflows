#!/usr/bin/env python3
"""SYMMETRIC anti-re-fork guard for both host runners (rununify child 01, `2r306y`).

WHY THIS FILE EXISTS. `render_stream` was extracted a Set ago and the guard that kept the
runners from re-defining its symbols was written for ONE runner only
(`test_oc_runipd_source_has_no_inline_definitions` asserted over `oc_runipd`; the agy side
checked two names). So `agy_runipd` re-forked `Palette`, `_strip_ansi`, `_one_line` and the
four ANSI constants they close over with nothing noticing, and `Heartbeat` actually DRIFTED
(`stallfp-01`/`kaga7s`): a display fix in the owning module silently did not reach
`aw agy run`. A one-sided guard cannot detect that, in either direction.

THE CONTRACT. For every `(symbol, owning module)` pair in `REFORK_TABLE` below, each runner
listed must:
  1. NOT contain a TOP-LEVEL DEFINITION of that symbol (checked by AST, see below), and
  2. expose the OWNER'S OBJECT at that attribute name (`assertIs`).

Both halves are load-bearing and neither implies the other. (1) alone passes while a runner
rebinds the name to something else at runtime; (2) alone passes while a stale duplicate
definition sits in the file being shadowed by a later import, which is a trap rather than a
fix. Together they say: exactly one definition, and the runner sees it.

WHY AST AND NOT SUBSTRING MATCHING. The retired guard used
`assertNotIn("class Palette:", src)`. That form is satisfied by a comment or a docstring that
merely mentions the string, and it is EVADED by `class Palette (object):`, by
`class Palette(Base):`, and by any decorated or reformatted definition. This module parses the
module source and inspects `ast.Module.body`, so it sees definitions and only definitions.

WHY A DATA TABLE AND NOT REPEATED ASSERTIONS. The retired oc-side guard was ten hand-written
`assertNotIn` lines, and that shape is precisely why the guarantee never extended to agy:
adding a symbol meant remembering to hand-write it twice. Add a row here and BOTH runners are
covered in both directions automatically.
"""

from __future__ import annotations

import ast
import pathlib
import unittest
from typing import NamedTuple

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    render_stream,
    run_selection_policy,
    runner_shared,
    selectors,
)

BOTH = ("oc_runipd", "agy_runipd")


class Owned(NamedTuple):
    """One already-extracted symbol and the runners forbidden to re-define it.

    ``runner_name`` exists because a runner does not always bind the owner's symbol under
    the owner's name: both runners call the front-matter readers as ``_read_id``, while
    ``selectors`` exposes them publicly. The AST half must forbid a definition of EITHER
    spelling (a re-fork under the local name is the actual historical shape), and the
    identity half must check the name the runner's call sites really use, since that is the
    binding a stale copy would shadow.
    """

    symbol: str
    owner: str
    runners: tuple[str, ...]
    runner_name: str | None = None

    @property
    def local(self) -> str:
        return self.runner_name or self.symbol

    @property
    def forbidden(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((self.symbol, self.local)))


# Every name the retired one-sided guards asserted is present here, so the guarantee STRICTLY
# GROWS: the oc-side names are now also enforced against agy, and the identity half is new for
# most of them. Rows are grouped by owning module.
REFORK_TABLE: tuple[Owned, ...] = (
    # --- render_stream: the display layer, extracted by `runnernorm` ---------------------
    # ANSI constants. The `Palette`/`_strip_ansi` bodies CLOSE OVER these, so leaving a
    # duplicate constant behind reproduces the same defect one layer down: a fix to the
    # color map would still not reach the runner that carries its own copy.
    Owned("_ANSI_RESET", "render_stream", BOTH),
    Owned("_ANSI_CODES", "render_stream", BOTH),
    Owned("_ANSI_STRIP_RE", "render_stream", BOTH),
    Owned("_STATUS_COLOR", "render_stream", BOTH),
    # Render classes and helpers.
    Owned("Palette", "render_stream", BOTH),
    Owned("StreamTracker", "render_stream", ("oc_runipd",)),
    Owned("Statusline", "render_stream", BOTH),
    Owned("Heartbeat", "render_stream", BOTH),
    Owned("format_tokens", "render_stream", ("oc_runipd",)),
    Owned("format_statusline", "render_stream", ("oc_runipd",)),
    Owned("render_event", "render_stream", ("oc_runipd",)),
    Owned("statusline_action_for_item", "render_stream", BOTH),
    Owned("execution_index", "render_stream", BOTH),
    Owned("_one_line", "render_stream", BOTH),
    Owned("_strip_ansi", "render_stream", BOTH),
    # --- selectors: the record front-matter readers --------------------------------------
    # Both runners carried private-name copies of these, AST-identical to `selectors`' own
    # readers but closing over LOOSER regexes. The public aliases are the documented
    # cross-module API (plan `2r306y` OQ-01, resolved by the maintainer) and deliberately
    # keep the runners' permissive matching; see `selectors.read_front_matter_id`.
    Owned("read_front_matter_id", "selectors", BOTH, runner_name="_read_id"),
    Owned("read_front_matter_status", "selectors", BOTH, runner_name="_read_status"),
    # --- runner_shared: the class (a) commons, extracted by `rununify` Order 02 ----------
    # EXTENDED BY `818uru` E-08, which is why this table exists as data rather than as
    # hand-written assertions: adding these 26 rows covers BOTH runners in BOTH directions
    # automatically, and a future re-fork of ANY of them now fails a test.
    #
    # These 26 are the moved symbols that are CLEAN re-exports, so both halves of the
    # contract apply unchanged: no runner-local definition, and the runner attribute IS the
    # owner's object.
    #
    # DELIBERATELY ABSENT, and each absence is a decision rather than an oversight:
    #   * The 8 WRAPPED symbols (`run_checked`, `save_state`, `discover_plans`,
    #     `validate_manifest`, `print_status`, `git_head`, `git_status`, `git_common_dir`).
    #     Each keeps a one-line runner-local `def` at its original name that binds a
    #     host-specific or DIVERGED dependency, so it fails BOTH halves by construction: it
    #     has a local definition, and the attribute is the wrapper rather than the shared
    #     object. Their equivalent guarantee is enforced by
    #     `tests/test_runner_shared.py::SingleDefinitionTests`, which proves each wrapper is a
    #     single delegating statement and therefore a binding rather than a second body.
    #   * `disable_lane_prompt`, which CANNOT move at all: it mutates a module-level
    #     `_LANE_PROMPT_DISABLED` through `global`, and a shared `global` would write the
    #     shared module's flag while each runner's DIVERGED `_lane_reclaim_prompt` kept
    #     reading its own. Pinned in `UnmovableSymbolTests`.
    #   * `reconcile_interrupted`, SHARED 2026-09-22 by runrecon-02 (`fduoj4`) E-01 and absent here
    #     for the SAME structural reason as the eight wrapped symbols above, not by oversight. Each
    #     host keeps a one-line `def` at the original name injecting its own `save_state` (which needs
    #     the class (c) DIVERGED `write_report`, so a shared body cannot choose one host's report
    #     renderer), so it fails BOTH halves of this table's contract by construction: it HAS a
    #     runner-local definition, and each runner's attribute is that wrapper rather than the shared
    #     object. Its equivalent guarantee, plus the third caller (`run_viewer.repair_run`) that no
    #     assertion about the two runners could cover, is enforced by
    #     `tests/test_runner_shared.py::ReconcileInterruptedExtractionTests`. Do NOT "complete" this
    #     table by adding a row for it: the row would fail rather than guard.
    Owned("DriverError", "runner_shared", BOTH),
    Owned("SCHEMA_VERSION", "runner_shared", BOTH),
    Owned("ID6_RE", "runner_shared", BOTH),
    Owned("_SET_RE", "runner_shared", BOTH),
    Owned("_ORDER_RE", "runner_shared", BOTH),
    Owned("utc_now", "runner_shared", BOTH),
    Owned("should_color", "runner_shared", BOTH),
    Owned("new_run_id", "runner_shared", BOTH),
    Owned("state_root", "runner_shared", BOTH),
    Owned("resolve_run_dir", "runner_shared", BOTH),
    Owned("_run_git", "runner_shared", BOTH),
    Owned("git_branch", "runner_shared", BOTH),
    Owned("load_json", "runner_shared", BOTH),
    Owned("atomic_write_json", "runner_shared", BOTH),
    Owned("append_jsonl", "runner_shared", BOTH),
    Owned("sha256_file", "runner_shared", BOTH),
    Owned("load_state", "runner_shared", BOTH),
    Owned("_lane_records_from_state", "runner_shared", BOTH),
    Owned("describe_lane", "runner_shared", BOTH),
    Owned("format_lane_report", "runner_shared", BOTH),
    Owned("print_lane_interrupt_report", "runner_shared", BOTH),
    Owned("build_recovery_lane_notice", "runner_shared", BOTH),
    Owned("allocate_isolation_worktree", "runner_shared", BOTH),
    Owned("teardown_isolation_worktree", "runner_shared", BOTH),
    Owned("_read_set", "runner_shared", BOTH),
    Owned("_read_order", "runner_shared", BOTH),
    Owned("resolve_plan_path", "runner_shared", BOTH),
    Owned("plan_bucket", "runner_shared", BOTH),
    Owned("describe_unresolved_plan_selector", "runner_shared", BOTH),
    Owned("enforce_no_active_runner_conflict", "runner_shared", BOTH),
    Owned("format_slated_artifacts_table", "runner_shared", BOTH),
    # --- runner_shared: the ACTION-AWARE SUCCESS BAR, added by `runnoop` Order 01 (`zz5yxq`) ------
    #
    # WHY THIS TABLE AND NOT `tests/test_runner_item_dependencies.py::_SHARED_NAMES`, stated because
    # the two are the only legal homes and the choice follows the OWNER. `_SHARED_NAMES` exists for
    # `oc_runipd`-OWNED names that agy must bind (its own comment records that this table structurally
    # cannot host one, since naming a runner as `owner` would make the AST half forbid that runner's
    # own definition). These four are owned by `runner_shared`, so BOTH halves of this table's
    # contract apply unchanged and they belong here: no runner-local definition, and each runner
    # attribute IS `runner_shared`'s object.
    #
    # WHAT A ROW HERE ACTUALLY BUYS, since grep would not buy it. The bar the exit code, the finish
    # glyph and `render_continuation_hint`'s `all_success` consult must be ONE object: a textually
    # identical copy in one host would let a later fix reach only one driver, which is exactly how
    # `render_stream`'s ANSI constants came to be re-forked and how agy carried a broken
    # `dependency_status_detailed` for months. `assertIs` distinguishes a shared object from a copy;
    # reading the source cannot.
    Owned("success_states_for_action", "runner_shared", BOTH),
    Owned("item_reached_success", "runner_shared", BOTH),
    Owned("item_needs_approval", "runner_shared", BOTH),
    Owned("exit_code_statuses", "runner_shared", BOTH),
    # --- runner_shared: the TURN-FAILURE CORRECTION layer, added by `retrywire` (`xipfy1`) E-07 ----
    #
    # THIS TABLE AND NOT `_SHARED_NAMES`, by the same owner-follows-the-home rule stated above: every
    # symbol below is DEFINED in `runner_shared`, so both halves of this table's contract apply. (The
    # plan that authorized this work named `AntiDivergenceGuardTests` as the guard to extend; that
    # class polices dependency REGEXES and makes no cross-host identity assertion, so the row went
    # here instead. Recorded so the next reader does not re-derive it.)
    #
    # WHY THE CLASSIFICATION TABLE IS REGISTERED AND NOT ONLY THE FUNCTIONS. A host carrying its own
    # copy of `TURN_RETRY_CLASSIFICATION` would agree about the MECHANISM and disagree about WHICH
    # failures are retryable, and that is the more expensive divergence: this layer decides what a run
    # spends paid model turns on, so a drifted allowlist could retry a class spec `25kzda` 5.5 forbids
    # retrying (an operator's deliberate stop being the one that costs real money to get wrong).
    Owned("TURN_RETRYABLE_DISPOSITIONS", "runner_shared", BOTH),
    Owned("TURN_RETRY_CLASSIFICATION", "runner_shared", BOTH),
    Owned("turn_failure_is_retryable", "runner_shared", BOTH),
    Owned("turn_retry_decision", "runner_shared", BOTH),
    Owned("turn_retry_budget_remaining", "runner_shared", BOTH),
    Owned("handle_turn_failure_retry", "runner_shared", BOTH),
    # --- run_selection_policy: the PER-ARTIFACT DISPOSITION LINE, added by `runnoop` Order 02 (`m85gxh`) ---
    #
    # THE FIRST ROW THIS TABLE CARRIES FOR `run_selection_policy` (measured before adding it: zero
    # rows named that owner). The module is the established pure-renderer home for run-selection
    # output, and the renderer below is called by BOTH hosts at their end-of-run site, so both halves
    # of this table's contract apply unchanged: no runner-local definition, and each runner attribute
    # IS the owner's object.
    #
    # WHY A ROW IS REQUIRED HERE RATHER THAN IMPLIED BY THE TABLE'S OTHER TESTS, stated because the
    # opposite was once believed and is FALSE (m85gxh F-9, re-measured at execution): a SYMMETRIC row
    # is a requirement of this plan, not something `test_the_table_covers_both_runners` enforces. That
    # test asserts only that the table's AGGREGATE `runners` set equals `BOTH` and that more than one
    # row names agy; four of the shipped rows legitimately name a single runner and pass. What makes
    # THIS row bite is the per-row identity assertion
    # (`test_every_runner_attribute_is_the_owning_modules_object`) plus the AST half
    # (`test_no_runner_redefines_an_already_extracted_symbol`), both proven against this symbol by the
    # mutation check recorded in the plan's V-04.
    #
    # WHAT IT BUYS: the operator-facing REASON text (why a matched artifact was not acted on) must be
    # ONE object. A textually identical copy in one driver is exactly how `render_stream`'s ANSI
    # constants came to be re-forked and how `aw agy run` silently missed a display fix; a reader
    # cannot tell a shared object from a copy, and `assertIs` can.
    Owned("render_queue_dispositions", "run_selection_policy", BOTH),
    # --- run_selection_policy: the END-OF-RUN DISPOSITION SUMMARY, added by `runnoop` Order 03 (`bsc457`) ---
    #
    # SYMMETRIC (`BOTH`) BECAUSE THE SUMMARY IS PRINTED BY BOTH HOSTS at their end-of-run site, from the
    # owning pure module, never one host importing it from the other.
    #
    # WHAT THIS ROW BUYS, since grep would not buy it: the operator-facing REMEDY text must be ONE
    # object. A remedy is the line that tells a human how to unblock a run at 3am, and `AGENTS.md`
    # records the measured failure mode when a message names only the prohibition (it gets complied with
    # by DELETION). A textually identical copy in one driver would let a remedy correction reach only
    # one host, which is exactly how `render_stream`'s ANSI constants came to be re-forked and how
    # `aw agy run` silently carried a broken `dependency_status_detailed` for months. `assertIs`
    # distinguishes a shared object from a copy; reading the source cannot.
    #
    # AND NOTE WHAT ENFORCES THE SYMMETRY, because the obvious answer is WRONG and was corrected at this
    # plan's review (F-9, re-measured at execution): `test_the_table_covers_both_runners` asserts only
    # that the table's AGGREGATE `runners` set equals `BOTH` and that more than one row names agy. It
    # does NOT fail a one-sided ROW; measured, four shipped rows legitimately name a single runner and
    # the suite passes. What makes THIS row bite is the per-row identity assertion
    # (`test_every_runner_attribute_is_the_owning_modules_object`) plus the AST half
    # (`test_no_runner_redefines_an_already_extracted_symbol`), both proven against this symbol by the
    # mutation check recorded in the plan's V-05.
    Owned("render_disposition_summary", "run_selection_policy", BOTH),
    # --- runner_shared: the VERIFIER VERDICT MAPPING, added by `runverdict` Order 05 (`1bfppy`) ----
    #
    # SYMMETRIC (`BOTH`) BECAUSE THE DEFECT WAS SYMMETRIC. The verdict gate this mapping replaces
    # existed as TWO BYTE-IDENTICAL COPIES, one per host (`oc_runipd` and `agy_runipd`), and both
    # carried the same fail-open `else` that recorded `CORRECTION_REQUIRED` - a verdict the prompt
    # explicitly asks the model for - as `verified`. A one-sided row would guard the less exposed
    # host: agy runs its verifier on its SHIPPED DEFAULT (`not no_verify`) and feeds the verdict
    # into `integration_is_earned`, while oc requires an explicit `--validate`.
    #
    # WHAT THIS ROW BUYS THAT GREP CANNOT. The table that decides whether a verifier's REJECTION is
    # honored must be ONE object. A textually identical copy in one driver is exactly how
    # `render_stream`'s ANSI constants came to be re-forked and how `aw agy run` silently carried a
    # broken `dependency_status_detailed` for months; `assertIs` distinguishes a shared object from
    # a copy and reading the source cannot. `VerdictMappingGuardTests` below adds the half no table
    # row can express: that neither driver carries a private substring test on a verdict, which is
    # the SHAPE of the original defect rather than the name of it.
    #
    # AND NOTE WHAT DOES *NOT* ENFORCE THE SYMMETRY, because the obvious answer is wrong:
    # `test_the_table_covers_both_runners` asserts only that the table's AGGREGATE `runners` set
    # equals `BOTH`, which it already did before these rows. What makes THESE rows bite is the
    # per-row identity assertion plus the AST half, both mutation-checked in this plan's V-06.
    Owned("map_verdict", "runner_shared", BOTH),
    Owned("normalize_verdict", "runner_shared", BOTH),
    Owned("verdict_refusal_text", "runner_shared", BOTH),
    Owned("VerdictMapping", "runner_shared", BOTH),
)

_MODULES = {
    "oc_runipd": oc_runipd,
    "agy_runipd": agy_runipd,
    "render_stream": render_stream,
    "runner_shared": runner_shared,
    "run_selection_policy": run_selection_policy,
    "selectors": selectors,
}


def module_source(module) -> str:
    """Read a module's own source text from disk."""
    return pathlib.Path(str(module.__file__)).read_text(encoding="utf-8")


def top_level_definitions(module) -> dict[str, int]:
    """Map every TOP-LEVEL definition/binding in ``module`` to its line number.

    AST-based on purpose (see the module docstring): a substring search cannot tell a
    definition from a mention of one in a comment, and misses spelling variants.

    Counts as a definition: `def`/`async def`/`class` (however spelled or decorated) and a
    module-level assignment binding the bare name, since a re-forked CONSTANT is the same
    defect as a re-forked function. An `import X` / `from m import X` is deliberately NOT a
    definition: importing the owner's object is the fix, not the violation.
    """
    source = module_source(module)
    found: dict[str, int] = {}
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found.setdefault(node.name, node.lineno)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found.setdefault(target.id, node.lineno)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            found.setdefault(node.target.id, node.lineno)
    return found


class FrontMatterReaderBehaviorTests(unittest.TestCase):
    """PIN the tolerated-input decision E-03 took, so it cannot be silently reversed.

    The runners' deleted `_read_id`/`_read_status` copies were AST-IDENTICAL in body to
    `selectors._read_id`/`_read_status` but closed over LOOSER regexes. So the AST/identity
    guard above, which is what proves the de-duplication, is BLIND to this difference: a
    swap to the strict readers would have passed every assertion in this file while changing
    which front-matter spellings both drivers accept.

    The chosen resolution was the PERMISSIVE PUBLIC ALIAS: the runners keep their historical
    tolerance, and `selectors`' own strict readers (a documented `aw find` matching contract)
    are untouched. These tests encode both halves of that decision.
    """

    ONE_SPACE = "- Id: abc123\n- Status: approved\n"
    TWO_SPACES = "-  Id: abc123\n-  Status: approved\n"
    TAB = "-\tId: abc123\n-\tStatus: approved\n"

    def test_public_readers_tolerate_loose_leading_whitespace(self):
        for label, text in (
            ("one space", self.ONE_SPACE),
            ("two spaces", self.TWO_SPACES),
            ("tab", self.TAB),
        ):
            with self.subTest(spelling=label):
                self.assertEqual(selectors.read_front_matter_id(text), "abc123")
                self.assertEqual(selectors.read_front_matter_status(text), "approved")

    def test_both_runners_still_accept_every_spelling_they_did_before(self):
        """The behavior-preservation claim for E-03, asserted rather than asserted-about."""
        for runner in BOTH:
            module = _MODULES[runner]
            for label, text in (
                ("one space", self.ONE_SPACE),
                ("two spaces", self.TWO_SPACES),
                ("tab", self.TAB),
            ):
                with self.subTest(runner=runner, spelling=label):
                    self.assertEqual(module._read_id(text), "abc123")
                    self.assertEqual(module._read_status(text), "approved")

    def test_selector_internal_readers_stay_strict(self):
        """The other half: `aw find` matching must NOT have been widened.

        `selectors._STATUS_RE`'s strictness is a deliberate matching contract (it disagrees
        with `plans_index._META_RE` on real records). If a later change "harmonizes" the
        public alias by widening the internal reader, this fails.
        """
        self.assertEqual(selectors._read_id(self.TWO_SPACES), None)
        self.assertEqual(selectors._read_status(self.TWO_SPACES), None)
        self.assertEqual(selectors._read_id(self.TAB), None)
        self.assertEqual(selectors._read_status(self.TAB), None)
        self.assertEqual(selectors._ID_RE.pattern, r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")
        self.assertEqual(selectors._STATUS_RE.pattern, r"(?m)^- Status:\s*(\S+)\s*$")

    def test_public_status_reader_keeps_the_single_token_contract(self):
        """Only the leading whitespace tolerance differs; `(\\S+)` is preserved."""
        multi = "- Status: EXECUTED (approved by maintainer)\n"
        self.assertIsNone(selectors.read_front_matter_status(multi))
        self.assertIsNone(selectors._read_status(multi))


class SymmetricReForkGuardTests(unittest.TestCase):
    """No runner may re-DEFINE a symbol another module already owns."""

    def test_no_runner_redefines_an_already_extracted_symbol(self):
        definitions = {
            name: top_level_definitions(mod) for name, mod in _MODULES.items()
        }
        violations = []
        for row in REFORK_TABLE:
            for runner in row.runners:
                for spelling in row.forbidden:
                    line = definitions[runner].get(spelling)
                    if line is not None:
                        violations.append(
                            f"{runner}.py:{line} re-defines `{spelling}`, which "
                            f"`{row.owner}.py` already owns as `{row.symbol}`"
                        )
        self.assertEqual(
            violations,
            [],
            "RE-FORK(S) FOUND. Import the symbol from its owning module instead of "
            "defining a second copy; a fix to the owner does not reach a copy.\n  "
            + "\n  ".join(violations),
        )

    def test_every_runner_attribute_is_the_owning_modules_object(self):
        """The identity half. A textually-different stale copy passes the AST half."""
        violations = []
        for row in REFORK_TABLE:
            expected = getattr(_MODULES[row.owner], row.symbol, None)
            if expected is None:
                violations.append(
                    f"{row.owner}.{row.symbol} does not exist, so the table's owner is wrong"
                )
                continue
            for runner in row.runners:
                actual = getattr(_MODULES[runner], row.local, None)
                if actual is None:
                    violations.append(
                        f"{runner}.{row.local} is MISSING; it must stay reachable "
                        f"(re-export `{row.owner}.{row.symbol}`)"
                    )
                elif actual is not expected:
                    violations.append(
                        f"{runner}.{row.local} is NOT `{row.owner}.{row.symbol}` "
                        f"(got {actual!r} from {getattr(actual, '__module__', '?')})"
                    )
        self.assertEqual(
            violations,
            [],
            "IDENTITY MISMATCH. The runner does not see the owner's definition:\n  "
            + "\n  ".join(violations),
        )

    def test_the_owning_module_really_defines_every_tabled_symbol(self):
        """Guard the guard: a typo'd owner would make both tests vacuous."""
        for row in REFORK_TABLE:
            with self.subTest(symbol=row.symbol, owner=row.owner):
                self.assertIn(
                    row.symbol,
                    top_level_definitions(_MODULES[row.owner]),
                    f"`{row.owner}.py` does not DEFINE `{row.symbol}`, so the table's "
                    "owner is wrong and the re-fork assertions would be meaningless",
                )

    def test_both_runners_import_from_the_shared_render_module(self):
        """Retained from the retired one-sided guards, now applied to BOTH runners."""
        for runner in BOTH:
            with self.subTest(runner=runner):
                self.assertIn(
                    "from agent_workflows.render_stream import",
                    module_source(_MODULES[runner]),
                )

    def test_the_table_covers_both_runners(self):
        """A table that drifted back to one-sided would silently stop guarding agy."""
        covered = {runner for row in REFORK_TABLE for runner in row.runners}
        self.assertEqual(covered, set(BOTH))
        agy_rows = [row.symbol for row in REFORK_TABLE if "agy_runipd" in row.runners]
        self.assertGreater(
            len(agy_rows), 1, "the agy side must not collapse to one symbol"
        )


#: The verdict tokens whose appearance inside an `in` comparison means a SUBSTRING test on a verifier
#: verdict. Chosen from the two the original defective gate actually tested plus their alias, since
#: those are the strings a re-fork would reach for.
_VERDICT_TOKENS = ("BLOCKED", "NOT CONFORMING", "CONFORMING", "VERIFIED")


class VerdictMappingGuardTests(unittest.TestCase):
    """The verdict mapping must stay ONE fail-closed table, and no driver may test a verdict itself.

    WHY THIS EXISTS BEYOND THE TABLE ROWS ABOVE (runverdict `1bfppy` E-06). The identity rows prove
    both hosts see the same `map_verdict` object. They CANNOT prove a driver did not ALSO grow a
    second, private verdict test beside it - a fresh `if "BLOCKED" in verdict:` under a new local
    name would satisfy every row in the table while re-creating the exact defect. So this class
    asserts on the SHAPE of the defect rather than on a symbol name.

    THE DEFECT BEING GUARDED, precisely. Both drivers once carried this, byte-identically:

        verify_verdict = str(v_data.get("verdict", "")).upper()
        if "BLOCKED" in verify_verdict or "NOT CONFORMING" in verify_verdict: ...
        else: verify_disp = "verified"

    Two things are wrong and only one of them was the leak. The LEAK was the permissive `else`
    (fixed in `61137509`). The SHAPE is the substring test, which survives a fixed `else`: measured
    before this change, the repaired branch still mapped `NOT BLOCKED` to `blocked`, because
    `"BLOCKED" in "NOT BLOCKED"`. The same trap runs the other way and is worse -
    `"CONFORMING" in "NOT CONFORMING"` is True - so under substring semantics the table's behavior
    depends on the ORDER of its arms and a reordering silently maps a rejection to a pass. Exact
    matching on a normalized token is what removes the hazard, and this test is what keeps it removed.
    """

    def test_neither_driver_tests_a_verdict_by_substring(self):
        """No `<token> in <expr>` comparison naming a verdict token, in either driver."""
        violations = []
        for runner in BOTH:
            module = _MODULES[runner]
            tree = ast.parse(module_source(module))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Compare):
                    continue
                if not any(isinstance(op, ast.In) for op in node.ops):
                    continue
                left = node.left
                if isinstance(left, ast.Constant) and isinstance(left.value, str):
                    if left.value.upper() in _VERDICT_TOKENS:
                        violations.append(
                            f"{runner}.py:{node.lineno} tests a verdict by SUBSTRING "
                            f"({left.value!r} in ...). Call "
                            f"`runner_shared.map_verdict` instead: substring semantics make "
                            f"the result depend on arm order "
                            f"(`'CONFORMING' in 'NOT CONFORMING'` is True)"
                        )
        self.assertEqual(
            violations,
            [],
            "A PRIVATE VERDICT SUBSTRING TEST HAS RETURNED:\n  "
            + "\n  ".join(violations),
        )

    def test_the_mapping_is_exact_and_not_a_substring_match(self):
        """The property the guard above protects, asserted on BEHAVIOR rather than on source.

        `NOT BLOCKED` and `NOT CONFORMING` are the pair that proves exactness: under substring
        semantics the first wrongly reads as `blocked`, and mis-ordered arms make the second wrongly
        read as a pass. Both are asserted, in both directions.
        """
        self.assertEqual(
            runner_shared.map_verdict("NOT CONFORMING").verify_disp, "blocked"
        )
        self.assertFalse(
            runner_shared.map_verdict("NOT CONFORMING").verify_disp == "verified"
        )
        # Substring semantics would make this `blocked`; exact matching makes it unrecognized.
        not_blocked = runner_shared.map_verdict("NOT BLOCKED")
        self.assertEqual(not_blocked.verify_disp, "unverified")
        self.assertFalse(not_blocked.recognized)

    def test_the_mapping_is_reached_from_the_shared_execute_path(self):
        """The wiring half: the one call site both hosts run through actually calls it.

        An identity row proves the object is SHARED; it does not prove anything CALLS it. This
        asserts `execute_item_core`'s verifier block invokes the mapping, so the table cannot be
        shared, correct, and bypassed all at once.
        """
        source = module_source(runner_shared)
        self.assertIn("v_map = map_verdict(", source)


if __name__ == "__main__":
    unittest.main()
