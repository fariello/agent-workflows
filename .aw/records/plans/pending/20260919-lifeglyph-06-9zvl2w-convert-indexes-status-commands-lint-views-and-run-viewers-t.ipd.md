# IPD: Convert indexes status commands lint views and run viewers to the shared resolver

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` R10.3 requires human lifecycle output in "plan/spec/research/backlog indexes, status setters, lint output, run viewers" to consume the shared resolver, and Section 12 step 4 sequences them after `attention.py`. The consumer set is measurable rather than guessed: `status_256`/`status_label` in `term.py` are called from `plans_index.py`, `research_index.py`, `status_set.py`, `ipd_lint.py`, `run_viewer.py`, and `cli.py` (verified 2026-09-19). Each therefore renders lifecycle state through the OLD fused path, and each will keep doing so after `attention.py` converts unless changed, leaving the repository with two live presentations of the same state.
- Scope: IN: route lifecycle rendering in `plans_index.py`, `research_index.py`, `status_set.py`, `ipd_lint.py`, `run_viewer.py`, and the lifecycle call sites in `cli.py` through the shared helpers; apply Section 9.1 styling and criterion A20 unknown handling in each; handle the `quarantined` condition input that `ipd_lint` emits; and update each view's snapshots. OUT: both runners and `render_stream.py` (child `qdd5jq`), deleting the shared `term.py` table (also `qdd5jq`, after every consumer is off it), and generic `Term` OK/WARN/FAIL outcomes which R10.3 keeps explicitly out of scope.
- Scope-Paths: agent_workflows/plans_index.py, agent_workflows/research_index.py, agent_workflows/status_set.py, agent_workflows/ipd_lint.py, agent_workflows/run_viewer.py, agent_workflows/cli.py, tests/test_plans_index.py, tests/test_ipd_lint.py, tests/test_run_viewer.py
- Item-Dependencies: executed:f9t5hz
- Status: to-review
- Set: lifeglyph
- Order: 6
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 9zvl2w
- From-Spec: uonrjg
- Blocks-Release: next

## Workflow history

- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from spec uonrjg R10.3 and Section 12 step 4, against the measured `status_256`/`status_label` caller set. Carries the spec's `Blocks-Release: next` gate.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Move every remaining non-runner human lifecycle view onto the shared resolver, so the indexes, the status setters, the lint output, and the run viewers all render one vocabulary.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The record indexes

- [ ] E-01 Convert `plans_index.py` and `research_index.py` lifecycle rendering to the shared helpers, applying Section 9.1 (glyph, id6, status share one treatment; titles and paths neutral) and the spec's native mappings for plans (6.1) and research (6.4).
  - Depends on: none
  - Expected outcome: Both indexes render the shared marker. Research outcome values (`adopted`, `rejected`, `informational`, `none-yet`) do NOT replace the lifecycle glyph, per Section 6.4's explicit warning.
  - Execution state: pending

### Task group 2: The status setters and lint views

- [ ] E-02 Convert `status_set.py` lifecycle rendering to the shared helpers so a transition's echoed status matches the indexes.
  - Depends on: none
  - Expected outcome: A status transition prints the same glyph and color for a given status as every index does.
  - Execution state: pending

- [ ] E-03 Convert `ipd_lint.py` lifecycle rendering, and handle `quarantined` as the Section 8 CONDITION input it is rather than as a native status, mapping to `parked` per D15. The lint view must show a quarantined plan without calling it a pass.
  - Depends on: none
  - Expected outcome: A quarantined plan renders `parked` (`◇`) with its own word, and is not styled as conforming. Per D15 the value is read from the `- Quarantine:` FIELD, not from `- Status:`.
  - Execution state: pending

### Task group 3: The run viewers

- [ ] E-04 Convert `run_viewer.py` and the lifecycle call sites in `cli.py` to the shared helpers, applying the Section 7.2 and 7.3 runner and ledger mappings including the five review-added rows.
  - Depends on: none
  - Expected outcome: Run views render ledger and item states through the shared vocabulary. `ran` shows `recovering`, `unknown_outcome` shows `failed`, and neither is styled as success.
  - Execution state: pending

### Task group 4: Snapshots and machine-output safety

- [ ] E-05 Update each converted view's snapshots and assert criterion A14 for every one of them: no ANSI and no schema-breaking decorated status value in `--agent` or `--json` output.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: Human snapshots updated; machine output for every converted command proven byte-identical.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Verified 2026-09-19: `status_256`/`status_label` are called from exactly `plans_index.py`, `research_index.py`, `status_set.py`, `ipd_lint.py`, `run_viewer.py`, `cli.py`, and `term.py` itself. That measured set, not a guess, defines this child's scope.
- Verified 2026-09-19: no `STATUS_COLOR_256` literal exists outside `term.py` and `attention.py`, so these consumers style through `term.py`'s API rather than holding their own tables. The conversion is therefore call-site routing, not table deletion.
- `quarantined` is carried by a `- Quarantine:` field rather than a `- Status:` value (spec D15), so it is a condition input under Section 8 precedence.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md.
- `- Readiness:` is deliberately absent (it is `/plan-review`'s output; IPD-M107 refuses an unattested value).

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | Six modules render lifecycle state through `term.py`'s fused path, so converting `attention.py` alone would leave the repository with two live presentations, which is the exact Section 1 problem restated. | `grep -rln "status_256\|status_label"` -> plans_index, research_index, status_set, ipd_lint, run_viewer, cli, term (verified 2026-09-19). |
| F-02 | Medium | These consumers hold NO local color tables (no `STATUS_COLOR_256` outside `term.py`/`attention.py`), so the work is routing call sites rather than deleting duplicates. That makes this child smaller than R10.3's prose implies and is worth stating so a reviewer does not expect table removals here. | `grep -rn "STATUS_COLOR_256"` excluding term.py/attention.py returns nothing. |
| F-03 | Medium | `ipd_lint`'s `quarantined` is the one value in this child's surface that is NOT a `- Status:` value, so an implementer routing it as a native status would violate Section 8's precedence model. | Spec D15 and Section 7.2's `quarantined` commentary. |

## Proposed changes (ordered, validatable)

1. Convert the two record indexes with their native mappings (E-01).
2. Convert the status setters (E-02).
3. Convert the lint view and handle `quarantined` as a condition input (E-03).
4. Convert the run viewers with the runner and ledger mappings (E-04).
5. Update snapshots and prove machine output unchanged for each (E-05).

## Deferred / out of scope (with reason)

- Both runners and `render_stream.py`: child `qdd5jq`, because they are the largest surface (`oc_runipd.py` 7872 lines, `runner_shared.py` 12822, `render_stream.py` 2553) and carry the re-export chain that must be dismantled last.
  - Carrier: qdd5jq
- Deleting `term.py`'s `STATUS_COLOR_256`: also `qdd5jq`, per Section 12 step 6, which removes duplicate tables only after ALL consumers use the shared source. Deleting it here would break the unconverted runners.
  - Carrier: qdd5jq
- Generic `Term` OK/WARN/FAIL: R10.3 keeps them valid and outside this spec.
  - Carrier-Declined: EXPLICITLY OUT OF SCOPE by R10.3, which keeps these generic outcomes valid and outside this spec. No obligation to carry.
- Backlog index: no separate backlog index module surfaced in the measured caller set; backlog lifecycle reaches the human through `attention.py` (child `f9t5hz`) and `plans_index`-style listings. If execution finds a distinct backlog view, add it here rather than inventing a new child.
  - Carrier-Declined: NOT DEFERRED BUT CONDITIONAL AND SELF-CLOSING INSIDE THIS CHILD. OQ-01 resolves it at execution by reading the code: if a distinct backlog view exists it is converted under this child's own E-items, and if backlog lifecycle reaches the human only through `attention.py` (already converted by `f9t5hz`) there is nothing to convert. Either way no work outlives this plan. The Set-level A17 assertion in child `qdd5jq` independently catches a missed view, so a wrong guess here cannot pass silently.

## Scope check

- Over-scope: none. Every E-item maps to a module R10.3 names and that the measurement confirms renders lifecycle.
- Under-scope: the backlog index is named by R10.3 but did not appear in the measured caller set; the Deferred note above records how to handle it if execution finds one, rather than silently omitting it.

## Required tests / validation

Run the suite BARE: `python3 -m pytest`. Paste the actual summary line. For EACH converted command, diff `--agent` and `--json` output before and after to prove criterion A14, and update the human snapshot showing only the expected marker change.

## Spec / documentation sync

No `.spec.md` edit in this child, so none is declared in `- Scope-Paths:`.

## Open questions

### OQ-01: Does a distinct backlog index view exist that R10.3 names but the measurement did not find?

- Blocking: no
- Status: open
- Owner: none
- Carrier-Declined: RESOLVED INSIDE THIS PLAN'S OWN EXECUTION, and independently backstopped. If a distinct backlog view exists it is converted under this child's E-items; if backlog lifecycle reaches the human only via `attention.py` (converted by `f9t5hz`) there is nothing to convert. Child `qdd5jq`'s A17 assertion catches a missed view regardless, so a wrong guess cannot pass silently and no work outlives this plan.
- Resolution or deferral rationale: NOT BLOCKING because it is resolvable by reading the code during execution, and because the consequence either way is small and bounded. R10.3 lists "plan/spec/research/backlog indexes", but the `status_256`/`status_label` caller measurement found plan and research index modules only, with backlog lifecycle reaching the human through `attention.py` (converted in `f9t5hz`). Recorded rather than assumed because omitting a real view would leave criterion A17 ("No second lifecycle color or glyph table remains") unsatisfiable while every item here passes. If execution finds a distinct backlog view, convert it under this child.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste rendered output from `aw index plans` and `aw index research` (or their print paths) showing the shared marker, with escapes visible proving Section 9.1 treatment. Paste one research row carrying an outcome value proving the outcome did NOT replace the lifecycle glyph.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste a status transition's echoed output and the same status as rendered by an index, showing IDENTICAL glyph and color code.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste `aw ipd lint` output for a quarantined plan showing `◇`/`parked` plus its own word, and showing the lint result does NOT report it as conforming. Paste proof the value was read from the `- Quarantine:` field rather than from `- Status:`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste run-view output covering the Section 7.2 and 7.3 states available in a real or fixture ledger. Explicitly show `ran` rendering `recovering` and `unknown_outcome` rendering `failed`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the BARE `python3 -m pytest` summary line. For each converted command, paste an EMPTY diff of its `--agent` output before and after, and the same for `--json`. Paste each updated human snapshot diff.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved 9zvl2w --by-human`). Its `- Item-Dependencies: executed:f9t5hz` edge is re-checked at dispatch, sequencing it after the attention conversion per Section 12 steps 3 and 4.

On completion: append the workflow-history line, set the terminal `Status: executed`, and `git mv` this plan to `.aw/records/plans/executed/` as a post-gate lifecycle step via `aw ipd finalize`, never as a checklist item. Commit path-scoped; never push.
