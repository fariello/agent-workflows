# IPD: Land the typed child-tracking row grammar and its one shared validation function

- Date: 2026-09-19
- Kind: child
- Concern: Spec `r07vma` R1a requires an orchestrator's checklist item to be a TYPED CHILD-TRACKING ROW with three validated fields, and R3 requires ONE function to decide conformance for every consumer. Neither exists. Measured at HEAD `21eff5d8`: `ipd_lint` carries 30 `C_*` stable rule codes and none concerns orchestrator checklist shape; `grep` for a row grammar in `agent_workflows/` returns nothing. Until this lands, the other three consumers have nothing to call and would each invent their own rule, which is the drift R3 exists to prevent.
  THE TWO RESOLVERS THIS MUST CONSUME RATHER THAN REIMPLEMENT ALREADY EXIST, and using them is what makes the three fields VALIDATED rather than merely parsed. `ipd_set_plan.parse_child_table` parses the orchestrator's own `## Child IPDs, sequence, and dependencies` table, resolving the Order and Depends-on columns BY HEADER NAME so a table with extra columns still parses, and returns a `ChildTableResult` whose `reason` explains any refusal. `ipd_schema.RECOGNIZED_STATUS` holds the nine-value plan status vocabulary (`approved`, `auto-approved`, `draft`, `executed`, `not-executed`, `reusable`, `reviewed`, `superseded`, `to-review`). A second definition of either is a defect.
- Scope: The row grammar, the one shared validation function, and its stable rule code. IN: the grammar for `- [ ] E-NN CONFIRM <child-id6> REACHED <status>`; a function that returns the three parsed fields or a typed refusal; validation that `<child-id6>` resolves to a row of THAT orchestrator's own child table, that `<status>` is in `RECOGNIZED_STATUS`, and that the `Depends on:` edge is present; the refusal message satisfying R7; and a stable `C_*` code in `ipd_lint`'s existing block. OUT: calling the function from `/plan-review` (child 02), from either runner (child 03), migrating any existing orchestrator (child 04), and the merged-result proof (child 05). Also OUT: parsing continuation lines or the orchestrator's prose sections, which R1a deliberately leaves to the semantic probe.
- Scope-Paths: agent_workflows/ipd_lint.py, agent_workflows/ipd_schema.py, tests/test_orchestrator_row_grammar.py
- Item-Dependencies: none
- Status: to-review
- Set: orchtyped
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: dpdyed
- From-Spec: r07vma
- Blocks-Release: next
- Work-Kind: bug
- Priority: high

## Workflow history

- 2026-09-19 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from approved spec `r07vma` as Order 01 of Set `orchtyped`. Every anchor measured at HEAD `21eff5d8`: the 30 existing `C_*` codes, `parse_child_table`'s header-name resolution, and `RECOGNIZED_STATUS`'s nine values. The parent orchestrator `d1u4sy` is written IN this grammar on purpose, so it is a live conforming fixture this child must accept.

## Goal

Give the Set one function that answers "is this orchestrator checklist row a well-formed typed child-tracking row?", validating all three fields against the resolvers that already exist, and refusing with a message that states the invariant and names both remedies without prescribing one.

READ THE SCOPE PRECISELY: this child WIRES NOTHING. It lands the rule and its tests. A reviewer who finds a consumer call site in this child's diff should treat that as over-scope, because the three consumers are separately reviewable children.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the grammar and its resolvers

- [ ] E-01 DEFINE THE ROW GRAMMAR as spec `r07vma` R1a states it, matching `- [ ] E-NN CONFIRM <child-id6> REACHED <status>` on the item's FIRST line only, and treating every subsequent indented line as unparsed context. Site the pattern where `ipd_lint`'s other structural patterns live, as a module-level constant beside the `C_*` block, so one grep finds the rule. The grammar must be anchored (a row that merely CONTAINS the phrase is not conforming) and must tolerate a ticked box (`- [x]`), since a mid-execution orchestrator has ticked rows.
  DO NOT WIDEN THE GRAMMAR TO ACCOMMODATE AN EXISTING PLAN. Measured at HEAD `21eff5d8`, ZERO of 32 live orchestrator rows conform, and that is expected: the grammar is new, so nothing authored before it can satisfy it by accident. Spec Section 5 cost 3 states that a non-zero pre-migration count would mean the grammar had been quietly widened. The one exception is the parent `d1u4sy`, authored in this grammar deliberately.
  - Depends on: none
  - Expected outcome: a module-level anchored pattern; the parent `d1u4sy`'s five rows all match; a sample of pre-existing rows all fail.
  - Execution state: pending

- [ ] E-02 RESOLVE `<child-id6>` AGAINST THE ORCHESTRATOR'S OWN CHILD TABLE, using `ipd_set_plan.parse_child_table` rather than a fresh scan, so a row naming a plan that is not a child of THIS Set is refused. Handle the case `parse_child_table` itself refuses (its `ChildTableResult.reason` explains why): a table that does not parse means conformance is UNKNOWN, not satisfied, so refuse and surface the reason rather than passing by default.
  - Depends on: E-01
  - Expected outcome: a row naming a child of the Set passes; a row naming a real plan that is not a child of the Set is refused; an unparseable child table refuses with `parse_child_table`'s own reason quoted.
  - Execution state: pending

- [ ] E-03 VALIDATE `<status>` AGAINST `ipd_schema.RECOGNIZED_STATUS` rather than a local list. Accept the full vocabulary for now, per the parent's OQ-01: narrowing to the subset a parent can meaningfully wait on is a one-line change once child 04's migration reveals which values are actually used, and accepting too much fails safe (a parent declaring a wait that never completes is reported `dependency-blocked`, not silently passed).
  - Depends on: E-01
  - Expected outcome: each of the nine recognized statuses parses; an unrecognized token is refused naming the vocabulary.
  - Execution state: pending

### Task group 2: the one function, and the message

- [ ] E-04 EXPOSE ONE FUNCTION THAT IS THE WHOLE RULE (R3), returning either the three parsed fields or a typed refusal carrying the rule code and the message. It takes the orchestrator's text and returns a result per ROW plus an overall verdict, because R8 requires a consumer to report EVERY finding rather than the first. Do not return a bare bool: children 02 and 03 both need the per-row detail to render their own output, and a bool would force them to re-derive it, which is the R3 violation this item exists to prevent.
  ALSO ADD THE STABLE RULE CODE to `ipd_lint`'s existing `C_*` block, in the structural family. Codes are stable and are not recycled; confirm by grep that the chosen code is unused anywhere in `agent_workflows/` or `tests/` before taking it.
  - Depends on: E-02, E-03
  - Expected outcome: one public function; its result exposes per-row fields and refusals; a fresh unused `C_*` code exists and is asserted unused-before by the test.
  - Execution state: pending

- [ ] E-05 WRITE THE REFUSAL MESSAGE TO SATISFY R7, which is a content requirement and not a wording preference. It must state WHAT is wrong and WHY (a parent is retired programmatically with the E/V checkpoint skipped, so work parked here is marked complete having never run), must EXPLICITLY forbid satisfying it by deleting the item, and must name BOTH remedies without prescribing either: move the step to a child whose `- Item-Dependencies:` put it in the right order, OR remove it because a child already covers it.
  THE REASON BOTH REMEDIES MUST APPEAR, measured rather than asserted: `rh5tt6` E-02 welds a redundant half (re-run the suite and leak sanitization, which every child already does and which the pre-commit hook enforces on every commit) to a genuinely uncovered half (an end-to-end install proof the plan itself calls "the part no child owns"). The correct repair is DELETE for the first and a CHILD for the second, so a message prescribing one remedy produces a pointless child plan for work already done.
  - Depends on: E-04
  - Expected outcome: the rendered message contains the invariant, the anti-deletion clause, and both remedies; a test asserts all three are present rather than asserting an exact string.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `ipd_lint` DECLARES STABLE RULE CODES AS `C_*` MODULE CONSTANTS, grouped by area (`IPD-P001` parse, `IPD-M1xx` metadata, `IPD-H2xx` headings, `IPD-I3xx` ids, `IPD-S4xx` states, `IPD-Q501` open questions, `IPD-Z6xx` size, `IPD-N001` name). Thirty exist at HEAD `21eff5d8`. A new rule adds a constant to that block; codes are not recycled.
- `ipd_lint._structural_lines` RETURNS ONLY THE LINES OUTSIDE fenced code, indented code, YAML front matter, and block quotes, as `(1-based line number, line)` pairs, and its docstring names that as what structural checks see. Reuse it rather than re-implementing fence detection, which is how a rule starts flagging pasted examples.
- `ipd_set_plan.parse_child_table` RESOLVES COLUMNS BY HEADER NAME, not by fixed index, so a table carrying extra columns parses; and its `ChildTableResult.reason` explains any refusal so a caller's fallback is never silent. E-02 consumes it.
- `ipd_schema.RECOGNIZED_STATUS` IS THE STATUS VOCABULARY and holds nine values. A second list is a defect.
- THE SEMANTIC PROBE IS NOT THIS CHILD'S BUSINESS but must not be disturbed: seven functions in `runner_shared` totalling 476 lines plus `tests/test_orchestrator_probe.py` at 1265 lines. This child declares neither path.
- SUITE BARE: `python3 -m pytest`. `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0`, a second `-q`, or `-p no:randomly`. Measure the baseline in the executing worktree and compare failing NODE IDS.

## Findings

| Id | Severity | Location (symbol / content anchor) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `agent_workflows/` | No row grammar and no shared conformance function exist, so R1a and R3 are unimplemented and the other three children have nothing to call. | `grep` for a row grammar returns nothing; `ipd_lint`'s 30 `C_*` codes include none for checklist shape |
| F-2 | HIGH | live orchestrator corpus | ZERO of 32 rows conform to the R1a grammar, which is the EXPECTED pre-migration state and the reason E-01 forbids widening the grammar to fit an existing plan. | measured against the grammar as written in the spec |
| F-3 | MEDIUM | `ipd_set_plan.parse_child_table` | The child-table resolver already exists and resolves by header name, so E-02 must consume it; a fresh scan would be a second definition of "who are this Set's children". | source read; docstring quoted |
| F-4 | MEDIUM | `ipd_schema.RECOGNIZED_STATUS` | The status vocabulary already exists with nine values, so E-03 must not carry a local list. | value read at HEAD `21eff5d8` |
| F-5 | MEDIUM | `d1u4sy` (this Set's parent) | The parent is authored IN the grammar, so it is a live conforming fixture. If this child's implementation rejects it, either the grammar or the parent is wrong and that disagreement must be REPORTED rather than patched on one side. | the parent's five rows |
| F-6 | LOW | spec `r07vma` R1a | Continuation lines are explicitly NOT parsed, so an implementer who extends the check into them has changed the contract and broken the division of labour with the probe. | R1a's text |

## Proposed changes (ordered, validatable)

1. E-01 defines the anchored row grammar and sites it beside the existing structural patterns.
2. E-02 resolves the child id6 through `parse_child_table`, refusing when that resolver itself refuses.
3. E-03 validates the status against `RECOGNIZED_STATUS`.
4. E-04 exposes the one public function with per-row detail, and allocates the stable rule code.
5. E-05 writes the refusal message to R7's content requirements.

## Deferred / out of scope (with reason)

- CALLING THE FUNCTION FROM ANY CONSUMER: children 02 (`r3xk1f`), 03 (`0xmk4e`) and 04 (`68uhp0`) own the three call sites. Landing the rule and a call site together would make the two separately-reviewable halves one unreviewable change.
  - Carrier-Declined: Owned in full by named sibling children in this same Set; nothing to hand off.
- PARSING CONTINUATION LINES OR THE ORCHESTRATOR'S PROSE SECTIONS: R1a deliberately excludes them and the semantic probe remains their control. Spec Section 3a limit 1 records this as an honest limit.
  - Carrier: d1u4sy
- NARROWING `<status>` TO THE TERMINAL SUBSET: the parent's OQ-01, open and non-blocking. E-03 accepts the full vocabulary so child 04's migration can reveal which values are used.
  - Carrier: d1u4sy
- ANY CHANGE TO THE SEMANTIC PROBE: forbidden by `25kzda` 2.5b and pinned by the Set's criterion 9. This child declares neither the probe's module path nor its test file.
  - Carrier-Declined: An explicit non-goal the governing spec forbids.

## Scope check

- Over-scope: none. `ipd_lint.py` is touched by E-01/E-04, `ipd_schema.py` by E-03 only if the vocabulary needs exporting (if it does not, that path is reconciled with a `--scope-ack` at finalize), and the new test file by every item.
- Under-scope: if the one function turns out to belong in a module this plan does not declare (for example a new `orchestrator_shape.py` rather than inside `ipd_lint`), that path must be DECLARED before the edit rather than reconciled afterwards. Siting is an implementation choice this plan deliberately leaves open, so the executor must expect to amend `- Scope-Paths:` and say so.

## Required tests / validation

`python3 -m pytest` BARE, in an isolated worktree, baseline measured there and compared by failing NODE ID rather than by total, since concurrent work moves the total.

Beyond the suite: the grammar exercised against the parent `d1u4sy`'s five rows (expect all five to conform) and against a sample of pre-existing rows (expect all to fail, which is the correct pre-migration result); one fixture per refusal mode; and the rendered message checked for R7's three required contents.

## Spec / documentation sync

N/A with reason: spec `r07vma` is `approved` and this child implements R1a and R3 as written, so there is no amendment to make. No `.spec.md` path is declared. If an executor finds R1a under-specified in a way that forces a judgement call, that is a finding to report against the spec rather than a licence to decide it here.

## Open questions

### OQ-01: Should the one function live inside `ipd_lint`, or in its own module that both `ipd_lint` and `runner_shared` import?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: NOT blocking: R3 requires ONE implementation and is satisfied either way, so this is a siting choice the executor can make from what it finds. It is recorded because it changes `- Scope-Paths:` (see the Scope check's under-scope note) and because there is a real constraint either way: `runner_shared` already imports `render_stream` at module level while `render_stream` imports zero first-party modules, so a shared symbol that the renderer must read cannot live in `runner_shared` without risking a cycle. PROPOSED DIRECTION: put it where `ipd_lint` can call it without importing a runner, since the review-side consumer is the one that must work with no run in progress.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the grammar as written and show it is ANCHORED (a row containing the phrase mid-line does not match). Paste it applied to all five of `d1u4sy`'s rows, each conforming, and to at least five pre-existing rows drawn from different orchestrators, each failing. Paste a ticked-box row conforming. State the re-derived pre-migration conforming count over the live corpus and confirm it is ZERO apart from `d1u4sy`; a higher number means the grammar was widened and this item FAILS.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste three cases with their rendered results: a row naming a genuine child of the Set (passes); a row naming a real plan that is NOT a child of that Set (refused); and an orchestrator whose child table does not parse (refused, with `parse_child_table`'s own `reason` quoted rather than a generic message). Paste the call showing `parse_child_table` is consumed rather than a fresh scan.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste all nine `RECOGNIZED_STATUS` values parsing, and an unrecognized token refused with the vocabulary named. Paste the reference to `ipd_schema.RECOGNIZED_STATUS` proving no local list was introduced.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the public function's signature and its result type, showing per-row detail is exposed rather than a bare bool, and explain in one sentence why children 02 and 03 can render their own output from it without re-deriving the rule. Paste the new `C_*` code and a grep proving it was unused before this change. Plus a MUTATION check: break one field's validation, show a pin FAILS, restore, show it passes.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the rendered refusal message in full. Confirm it contains (a) the invariant and why it exists, (b) an explicit statement that deleting the item is NOT an acceptable fix, and (c) BOTH remedies with neither prescribed. Paste the test asserting all three contents are present, and confirm it does not assert an exact string (which would make every wording improvement a test failure).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Size note: 5 E-leaves in 2 groups, all on one rule and its tests. Deliberately excludes all three call sites, which are separate children.
- Cohesion rationale: E-01 through E-03 are the three fields of one grammar and cannot be validated apart from each other. E-04 is the single entry point they compose into, which is R3's requirement. E-05 is the refusal that entry point returns, and it is inseparable from E-04 because a refusal with no message is not usable by a consumer.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since a rejected hook can leave paths in the index. When reporting tests passed, paste the ACTUAL runner output. This is a SHARED CHECKOUT: other agents are editing this tree concurrently, so never revert or commit a file you did not change.

Post-gate lifecycle: requires `/plan-review` then explicit human approval (`aw ipd set approved dpdyed --by-human --message ...`). Do NOT hand-write a `- Readiness:` field. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
