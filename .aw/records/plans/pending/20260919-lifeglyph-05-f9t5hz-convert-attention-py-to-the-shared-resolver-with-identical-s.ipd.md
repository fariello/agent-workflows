# IPD: Convert attention.py to the shared resolver with identical status and id6 treatment

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` Section 12 step 3 converts `attention.py` first among the consumers, and Section 1 names it as a specific duplication: it "duplicates native status colors and colors both status words and id6s". Verified 2026-09-19: `attention.py:1403` defines `_STATUS_COLOR_256`, consumed at three sites (1852, 1997, 2160), each falling back to `_CLASS_COLOR_256` and then to gray 244. That gray fallthrough is exactly what the spec's Section 6 preamble calls a defect ("Falling through silently to gray for a known status is a defect") and what criterion A20 requires be replaced by `?` plus the native word plus a validation diagnostic.
- Scope: IN: replace `attention.py`'s local `_STATUS_COLOR_256` lifecycle lookups with the shared `term.py` helpers, apply the Section 9.1 rule that status word and id6 receive the SAME treatment, replace the silent gray fallthrough with criterion A20 behavior, and update the command's snapshots. OUT: deleting the local table's non-lifecycle companions if any are used for something other than lifecycle (`_CLASS_COLOR_256` covers attention CLASSES, which is a separate vocabulary), the other consumers (children `9zvl2w`, `qdd5jq`), and any change to attention's class computation, which spec Section 3 excludes as a non-goal.
- Scope-Paths: agent_workflows/attention.py, tests/test_attention.py
- Item-Dependencies: executed:bn026f
- Status: to-review
- Set: lifeglyph
- Order: 5
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: f9t5hz
- From-Spec: uonrjg
- Blocks-Release: next

## Workflow history

- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from spec uonrjg Section 12 step 3, R10.3, and criteria A10/A17/A20. Carries the spec's `Blocks-Release: next` gate.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `aw attention` the first view rendered entirely through the shared resolver, with the status word and the id6 carrying identical lifecycle treatment and no known status silently rendering as gray.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Convert the lookups

- [ ] E-01 Replace the three `_STATUS_COLOR_256` lifecycle lookup sites in `attention.py` (1852, 1997, 2160) with calls to the shared `term.py` lifecycle helpers, and remove the local `_STATUS_COLOR_256` table (attention.py:1403) once no site reads it.
  - Depends on: none
  - Expected outcome: No lifecycle color literal remains in `attention.py`. Every lifecycle color comes from the shared resolver. `_CLASS_COLOR_256` is evaluated separately (see E-02) rather than deleted reflexively.
  - Execution state: pending

- [ ] E-02 Decide and record whether `_CLASS_COLOR_256` is lifecycle styling (and so must go) or the attention CLASS vocabulary (and so is a different dimension the spec does not claim). Act on the finding rather than assuming either way.
  - Depends on: E-01
  - Expected outcome: A recorded determination with evidence. If it is lifecycle, it is removed; if it is the class vocabulary, it stays and the plan says why, since R10.3 removes lifecycle tables and spec Section 3 excludes non-lifecycle visuals.
  - Execution state: pending

### Task group 2: The presentation rules

- [ ] E-03 Apply Section 9.1 in the attention board: glyph, id6, and status word take the same resolved color and bold flag; artifact type, title, and path take none. Replace the silent gray fallthrough with criterion A20 behavior, emitting `?` plus the native word plus a validation diagnostic for a known family with an unrecognized status.
  - Depends on: E-01
  - Expected outcome: Criterion A10 holds on the attention board, and a bogus status produces `?` plus the word plus a diagnostic rather than an indistinguishable gray row.
  - Execution state: pending

- [ ] E-04 Update the attention command's snapshots and assertions for the new marker column, preserving the existing column ORDER and every machine field, per Section 12's compatibility rule and criterion A14.
  - Depends on: E-03
  - Expected outcome: Human snapshots updated (expected, per Section 12). `--agent` and `--json` output byte-identical to before, proving no ANSI or schema change leaked into machine output.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Verified 2026-09-19: `attention.py:1403` defines `_STATUS_COLOR_256`; it is read at 1852, 1997, and 2160, each with a `_CLASS_COLOR_256` then gray-244 fallback chain.
- `attention.py` is 3320 lines and is a high-traffic file. Two pending plans (`9iiqmm`, `quqyc4`) declare it and one executed plan (`pr5b0t`) did; per AGENTS.md the runner isolates each execute item in its own worktree and re-validates on merge, so overlap is rebase friction rather than a hazard.
- `aw attention` is the command AGENTS.md directs agents to consume for cross-tree status, so a regression here is user-visible immediately.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md.
- `- Readiness:` is deliberately absent (it is `/plan-review`'s output; IPD-M107 refuses an unattested value).

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | The silent gray fallthrough the spec calls a defect is live at all three attention lookup sites, so any status absent from the local table currently renders indistinguishably from `parked`. | `attention.py:1852,1997,2160` each end `..., 244)`; spec Section 6 preamble and criterion A20. |
| F-02 | Medium | `_CLASS_COLOR_256` sits in the same fallback chain as the lifecycle table but plausibly encodes the attention CLASS vocabulary (`ready`/`active`/`blocked`/`done`/`parked`), which is a DIFFERENT dimension from native lifecycle status. Deleting it reflexively as "a duplicate lifecycle table" would remove a vocabulary the spec never claimed. E-02 exists to settle this with evidence. | `attention.py:1852` chain; spec Section 3 non-goal on encoding non-lifecycle dimensions; R10.3 scopes removal to LIFECYCLE tables. |
| F-03 | Medium | `aw attention` has machine output (`--agent`, `--json`) that AGENTS.md tells agents to consume, so criterion A14's no-ANSI-no-schema-break requirement is load-bearing here rather than theoretical. | AGENTS.md attention paragraph (`--format json` for machine use); criterion A14. |

## Proposed changes (ordered, validatable)

1. Convert the three lookup sites and remove the local lifecycle table (E-01).
2. Determine `_CLASS_COLOR_256`'s dimension and act on the finding (E-02).
3. Apply Section 9.1 styling and criterion A20 unknown handling (E-03).
4. Update human snapshots while proving machine output unchanged (E-04).

## Deferred / out of scope (with reason)

- Attention's class computation and the class vocabulary itself: spec Section 3 excludes "changing lifecycle states, transition rules, attention classes". This child restyles rows; it does not reclassify them.
  - Carrier-Declined: Spec Section 3 excludes changing lifecycle states, transition rules, and attention classes as a stated NON-GOAL. This child restyles rows without reclassifying them, so nothing is outstanding.
- The other consumers: children `9zvl2w` (indexes, status commands, lint views, run viewers) and `qdd5jq` (runners and `render_stream`), because each has an independent snapshot surface.
  - Carrier: 9zvl2w
- Column reordering: Section 12 requires existing column order be preserved unless a separately reviewed interface change alters it. Section 9.1 permits following an existing stable contract, so attention's order stays.
  - Carrier-Declined: Section 12 REQUIRES existing column order be preserved absent a separately reviewed interface change, and Section 9.1 permits following an existing stable contract. Preserving the order is compliance, not deferral.

## Scope check

- Over-scope: none. Every E-item maps to Section 12 step 3, R10.3, or criterion A10/A14/A20.
- Under-scope: none. E-02 deliberately adds a determination step rather than assuming, because F-02 identifies a real risk of deleting a non-lifecycle vocabulary.

## Required tests / validation

Run the suite BARE: `python3 -m pytest`. Paste the actual summary line. Validation must additionally show criterion A14 holding by diffing `aw attention --agent` and `aw attention --json` output before and after the change.

## Spec / documentation sync

No `.spec.md` edit in this child, so none is declared in `- Scope-Paths:`.

## Open questions

### OQ-01: Is `_CLASS_COLOR_256` in scope for removal?

- Blocking: no
- Status: open
- Owner: none
- Carrier-Declined: RESOLVED INSIDE THIS PLAN'S OWN EXECUTION. E-02 exists precisely to read `_CLASS_COLOR_256` and record which vocabulary it encodes, and V-02 demands that determination plus its code evidence. Both outcomes are handled by this child's own items (remove it if lifecycle, retain it with a Section 3 reason if it is the attention class vocabulary), so nothing outlives the plan.
- Resolution or deferral rationale: NOT BLOCKING because it is answerable from the code at execution time, which is what E-02 does. Recorded as a question rather than decided here because the two answers lead to opposite actions and the wrong one is a silent regression: R10.3 requires removing duplicate LIFECYCLE tables, while Section 3 forbids folding a non-lifecycle dimension into lifecycle styling. If `_CLASS_COLOR_256` maps attention's cross-tree CLASSES (`ready`/`active`/`blocked`/`done`/`parked`) rather than native statuses, it is a legitimate separate vocabulary and stays. The executing agent must read it and record which it is.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste `grep -n "_STATUS_COLOR_256" agent_workflows/attention.py` returning NO matches, and paste the new call sites showing they route through the shared helpers.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the recorded determination with the code evidence behind it (what `_CLASS_COLOR_256`'s keys actually are). If it was removed, paste the grep proving absence; if retained, paste the reason tied to spec Section 3.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste a rendered attention board with escapes visible showing the same color on glyph, id6, and status word and none on title or path (A10). Paste a row for a deliberately bogus status showing `?` plus the native word plus the diagnostic (A20). A gray row with no diagnostic FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the BARE `python3 -m pytest` summary line. Paste a diff of `aw attention --agent` output before and after showing it EMPTY, and the same for `--json`, proving A14. Paste the updated human snapshot diff showing only the expected marker change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved f9t5hz --by-human`). Its `- Item-Dependencies: executed:bn026f` edge is re-checked at dispatch, because this child consumes the rendering helpers that plan provides. Note the edge names only the nearest dependency: `bn026f` itself depends on `udgilu` and `pow5sj`, and the runner sorts by dependency depth, so the transitive chain is honored without restating it.

On completion: append the workflow-history line, set the terminal `Status: executed`, and `git mv` this plan to `.aw/records/plans/executed/` as a post-gate lifecycle step via `aw ipd finalize`, never as a checklist item. Commit path-scoped; never push.
