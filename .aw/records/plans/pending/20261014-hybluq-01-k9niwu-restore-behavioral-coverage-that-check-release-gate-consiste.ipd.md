# IPD: Restore behavioral coverage that check_release_gate_consistency reports zero findings for a gated carrier under an ungated item

- Date: 2026-10-14
- Kind: child
- Concern: `check_engine.check_release_gate_consistency` Rule 2 (`check.from-backlog-gate-mismatch`) is deliberately ONE-WAY: a LIVE gated carrier (plan or spec) whose `From-Backlog` item carries NO `- Blocks-Release:` must produce ZERO findings (maintainer ruling on `qmgn12` OQ-03, 2026-09-12). The only test asserting that direction, the "a GATED carrier under an UNGATED item" row of `test_the_mismatch_rule_fires_only_for_a_live_carrier`, was deleted with `tests/test_bug_gate_check.py` in `19313eed` (`ev7t1w` site S-07, RETIRE-UNGUARDED), so a refactor making the rule symmetric would now go undetected.
- Scope: Add one new behavioral test module that builds isolated tmp repos and calls `check_engine.check_release_gate_consistency` directly, asserting zero `check.from-backlog-gate-mismatch` findings for a live gated plan carrier and a live gated spec carrier under an ungated item, plus anti-vacuity rows proving the rule still fires for a gated item with a live ungated or differently-gated carrier on the same fixture shape; then update the stale "no live guard currently asserts this directly" remark in the `check_release_gate_consistency` docstring to name the new module.
- Scope-Paths: tests/test_release_gate_one_way_mismatch.py, agent_workflows/check_engine.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: hybluq
- Set: hybluq
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: k9niwu

## Workflow history
- 2026-10-15 reviewed (aw set): plan-review applied revisions

- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003
- 2026-10-14 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored from backlog hybluq; review-ready.

## Goal

Restore, as behavioral tests only (P16), the guarantee that `check_engine.check_release_gate_consistency` never reports `check.from-backlog-gate-mismatch` for a live gated carrier whose originating backlog item is ungated, while still reporting it for the forward direction. This was lost when `tests/test_bug_gate_check.py` was deleted in `19313eed`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: one-way mismatch tests

- [ ] E-01 Create `tests/test_release_gate_one_way_mismatch.py` with a `unittest.TestCase` whose `setUp` calls `support.declare_execution_role(self)` (`from tests import support`). Add local fixture helpers (re-implemented, shaped as `19313eed^:tests/test_bug_gate_check.py` `_item`/`_plan`/`_spec` and its `ITEM`/`PLAN`/`SPEC` templates) that write, under a `tempfile.TemporaryDirectory` root: a backlog item in `.aw/records/backlog/<status>/` with `- Work-Kind: bug`, `- Status: graduated` and an optional `- Blocks-Release:`; a plan in `.aw/records/plans/<disposition>/` with `- From-Backlog:` and an optional gate; a spec in `.aw/records/specs/` with `- From-Backlog:` and an optional gate; plus one `planned` release record under `.aw/records/releases/` (shape as `tests/test_check_engine_release_gate.py` `_create_minimal_repo`) so `next` resolves. Add `test_gated_carrier_under_ungated_item_is_not_a_mismatch`, driven as `subTest` rows for (a) a live `pending/` plan carrying `- Blocks-Release: next` and (b) a spec carrying `- Blocks-Release: next`, each pointing at an UNGATED item; assert `[d.rule for d in check_engine.check_release_gate_consistency(root)]` contains no `"check.from-backlog-gate-mismatch"` (the rule id written as a literal string).
  - Depends on: none
  - Expected outcome: the module exists and the zero-finding test passes against current code.
  - Execution state: pending
- [ ] E-02 In the same module add `test_forward_direction_still_fires`, the anti-vacuity half, using the same helpers: (a) gated item (`next`) with a live `pending/` plan carrying NO gate, and (b) gated item (`next`) with a live plan gated to a DIFFERENT, unresolvable release string (for example `v9z9z9`); assert each yields exactly one `"check.from-backlog-gate-mismatch"` finding whose `location` is the carrier path and whose `detail` names the item id6. Add (c) gated item with a matching-gated live plan and assert zero findings, so a rule flagging every carrier cannot pass both tests. Add (d) gated item (`next`) with a SPEC carrier gated to `v9z9z9`, built with the SAME spec helper E-01(b) uses, and assert exactly one `"check.from-backlog-gate-mismatch"` finding at the spec path whose `detail` contains `spec`: this is the spec-side anti-vacuity row, without which a spec helper writing to a path `_iter_spec_records` never scans would let E-01(b) pass vacuously (PR-001).
  - Depends on: E-01
  - Expected outcome: the anti-vacuity test passes against current code, proving BOTH the plan and the spec fixtures of E-01 are capable of producing the finding.
  - Execution state: pending

### Task group 2: stale remark

- [ ] E-03 In `agent_workflows/check_engine.py`, edit the `check_release_gate_consistency` docstring sentence "why `tests/test_bug_gate_check.py` (deleted in `19313eed`; no live guard currently asserts this directly) pinned the zero-finding direction explicitly" so it states that `tests/test_release_gate_one_way_mismatch.py` now pins the zero-finding direction (keeping the historical note that the original guard was deleted in `19313eed`). Docstring-only change; no behavior change.
  - Depends on: E-02
  - Expected outcome: the docstring names the new live test module and no longer claims the guard is absent.
  - Execution state: pending

## Project conventions discovered (Step 0)

- P16 (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): drive `check_release_gate_consistency` on real tmp-repo fixtures and assert on its returned drift; never read source via `inspect`/`ast`/regex.
- Rule ids are a published interface (`aw check` prints them, CI greps them), so tests write them as literal strings (deleted module docstring, `19313eed^:tests/test_bug_gate_check.py`).
- Suite runs bare as `python3 -m pytest` (`-n auto`); tests must be xdist-safe with their own tmp repo and `support.declare_execution_role(self)` (`tests/support.py` `declare_execution_role`).
- Fixtures must not read the live checkout ("Every test builds its OWN temp repo; none reads the live checkout", same deleted module docstring).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- Executed plan `ev7t1w` (`.aw/records/plans/executed/20261011-iosmvn-03-ev7t1w-retire-or-repoint-the-dangling-test-citations-in-the-non-run.ipd.md`) row S-07: `check_engine.py` / `check_release_gate_consistency` / `tests/test_bug_gate_check.py` / `19313eed` / RETIRE-UNGUARDED, "no live test asserts zero-finding direction on `check_release_gate_consistency` directly (though `tests/test_check_engine_release_gate.py` exercises aggregate handoff path)".
- `check_engine.check_release_gate_consistency` Rule 2 builds `item_gate` only "if item_id and gate", then skips any carrier whose target is not in `item_gate`; that `continue` is what makes the ungated-item direction zero-finding today, and it is the line a symmetric refactor would change.
- `19313eed^:tests/test_bug_gate_check.py` `MISMATCHES` table row "a GATED carrier under an UNGATED item" (item gate `None`, carrier `("plan", "next", "pending", "to-review")`, expected `()`) plus its anti-vacuity row "matching gates on both sides" are the model for E-01/E-02.
- `tests/test_check_engine_release_gate.py` `test_rule_from_backlog_gate_mismatch_reachable` covers only the forward (gated item) direction through `check_release_gates`; no live test covers the ungated-item direction.

## Proposed changes (ordered, validatable)

1. E-01: new module with the zero-finding test for plan and spec carriers.
2. E-02: anti-vacuity forward-direction rows on the same fixtures.
3. E-03: docstring-only update in `check_engine.check_release_gate_consistency`.

## Deferred / out of scope (with reason)

- Restoring the rest of the deleted `tests/test_bug_gate_check.py` (the `check.live-bug-ungated` grid, terminal-carrier skip rows, seam and registration tests): not part of backlog `hybluq`, which names only the zero-finding direction.
  - Carrier-Declined: outside this backlog item's single named property; no defect is known in those areas.
- Any behavior change to `check_release_gate_consistency`: this is coverage restoration.
  - Carrier-Declined: deliberate non-goal, not an outstanding obligation.

## Scope check

- Over-scope: none. The only production edit is a docstring sentence that would otherwise become false.
- Under-scope: none. Both carrier types (plan, spec) and the anti-vacuity forward direction are covered.

## Required tests / validation

- `python3 -m pytest tests/test_release_gate_one_way_mismatch.py` passes (V-01, V-02).
- Mutation check (demonstrated at review 2026-10-15 in a scratch copy of the package: with `if item_id:` storing `(gate or "", str(f))`, both a pending plan and a spec carrying `- Blocks-Release: next` under an ungated item yield `check.from-backlog-gate-mismatch`; unmutated code yields none): temporarily change Rule 2's `item_gate` population in `check_release_gate_consistency` so ungated items are included (e.g. `if item_id:` storing `(gate or "", str(f))`), confirm `test_gated_carrier_under_ungated_item_is_not_a_mismatch` FAILS, then revert (V-01).
- Full bare suite `python3 -m pytest` with no new failures (V-03).

## Spec / documentation sync

N/A: no spec or user-facing documentation describes these tests; the only text change is the docstring in E-03.

## Open questions

### OQ-01: New module or append to `tests/test_check_engine_release_gate.py`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: a new purpose-named module `tests/test_release_gate_one_way_mismatch.py`. `tests/test_check_engine_release_gate.py` is scoped by its docstring to rule-family reachability through `check_release_gates` and the CLI, whereas this property is about `check_release_gate_consistency` directly; a dedicated name is what the E-03 docstring cites, matching sibling restoration plans `55kl2u` and `yfo6z6`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -v tests/test_release_gate_one_way_mismatch.py` showing `test_gated_carrier_under_ungated_item_is_not_a_mismatch` PASSED; pasted output of the temporary mutation run (Rule 2 `item_gate` populated for ungated items) showing that test FAILED, followed by `git diff --stat agent_workflows/check_engine.py` proving the mutation was reverted; plus `grep -nE "inspect|import ast|read_text\(.*check_engine" tests/test_release_gate_one_way_mismatch.py` returning no match.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest -o addopts="" -v tests/test_release_gate_one_way_mismatch.py` output showing the forward-direction test PASSED, with its rows visibly covering (a) ungated plan, (b) differently-gated plan, (c) matching plan with zero findings, and (d) differently-gated SPEC with the finding at the spec path; test names are non-binding pointers, the evidence is the behaviors pinned.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff agent_workflows/check_engine.py` showing only docstring lines changed and naming `tests/test_release_gate_one_way_mismatch.py`; AND the pasted summary line of a bare `python3 -m pytest` run with no new failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Open questions: OQ-01 is resolved; none remain. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; a claimed pass with no pasted output does not satisfy it. Execute only after explicit human approval (`aw ipd set approved k9niwu`); start with `aw ipd begin k9niwu`. Commit ONLY the two Scope-Paths files through `aw commit k9niwu -- <paths>`; never `git add -A`, never `-a`, never push, never `--no-verify`; verify the staged set with `git diff --cached --name-only` first. The V-01 mutation is temporary and MUST NOT be committed: revert it before any commit and show `git diff --stat agent_workflows/check_engine.py` touching only the E-03 docstring.

SCOPE FENCE. The declared `- Scope-Paths:` are the expected edit set; an out-of-scope edit that proves necessary is made and justified with `aw ipd finalize --scope-reason`. No behavior change to `check_engine.check_release_gate_consistency`.

POST-GATE LIFECYCLE. On completion every `V-*` carries pasted evidence with `Result: pass` and `aw ipd lint --phase pre-transition` must conform before the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that finalize, so the executor must NOT run it; executed by hand, run `aw ipd finalize k9niwu`. Never hand-roll the move or `git mv` the plan.
