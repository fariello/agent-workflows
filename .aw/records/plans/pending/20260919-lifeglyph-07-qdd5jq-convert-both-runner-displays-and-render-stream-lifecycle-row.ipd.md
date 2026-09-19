# IPD: Convert both runner displays and render_stream lifecycle rows then delete every duplicate table

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` Section 12 step 5 converts the runner displays and `render_stream.py` last, and step 6 deletes the duplicate tables only after every consumer is off them. This child is where the spec's Section 1 complaint is most concretely true: `render_stream.py:51 _STATUS_COLOR` maps `approved`, `reviewed`, `executed`, and `substantially-complete` ALL to green (verified 2026-09-19), which collapses exactly the readiness-versus-completion distinction Section 5 exists to prevent ("Green is reserved for successful completion. Ready work is cyan, not green"). That table is re-exported into both drivers (`oc_runipd.py:104` and its `__all__` at 447, `agy_runipd.py:104`, `runner_shared.py:168`, consumed at `runner_shared.py:12789`), so one wrong palette currently reaches every runner view.
- Scope: IN: convert lifecycle item and statusline rendering in `oc_runipd.py`, `agy_runipd.py`, `runner_shared.py`, and `render_stream.py` to the shared resolver; dismantle the `_STATUS_COLOR` re-export chain; delete the now-unused duplicate tables including `term.py`'s `STATUS_COLOR_256`; and assert criterion A17 that no second lifecycle table remains. OUT: `render_stream.py`'s EVENT glyphs and severity colors, which R10.3 explicitly permits it to retain because they are not lifecycle semantics; and any change to run outcome vocabulary, exit codes, or report sections, which the spec's Section 0.5 override explicitly does not touch.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, agent_workflows/render_stream.py, agent_workflows/term.py, tests/test_render_stream.py, tests/test_runner_shared.py
- Item-Dependencies: executed:9zvl2w
- Status: to-review
- Set: lifeglyph
- Order: 7
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: qdd5jq
- From-Spec: uonrjg
- Blocks-Release: next

## Workflow history

- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from spec uonrjg Section 12 steps 5-6, R10.3, and criteria A17/A18. Carries the spec's `Blocks-Release: next` gate.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Move the runner and stream lifecycle rows onto the shared resolver and then remove every duplicate lifecycle table, so criterion A17 holds and the readiness-versus-completion collapse in the current runner palette is gone.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The stream renderer

- [ ] E-01 Convert `render_stream.py` lifecycle rendering to the shared resolver, and SEPARATE it from the event glyphs and severity colors that module legitimately keeps. Remove `_STATUS_COLOR` (render_stream.py:51) once nothing reads it.
  - Depends on: none
  - Expected outcome: Lifecycle rows render through the shared resolver; event glyphs and severity colors are untouched and still pass their own tests (criterion A18). `approved` no longer shares a color with `executed`.
  - Execution state: pending

### Task group 2: The runner displays

- [ ] E-02 Dismantle the `_STATUS_COLOR` re-export chain: remove the import at `oc_runipd.py:104` and its `__all__` entry at 447, the aliased import at `agy_runipd.py:104`, and the import at `runner_shared.py:168`, converting the consumption site at `runner_shared.py:12789` to the shared resolver.
  - Depends on: E-01
  - Expected outcome: No module re-exports a lifecycle palette. The disposition styling at runner_shared.py:12789 resolves through the shared module, including the Section 7.2 rows for `ran`, `unknown_outcome`, `needs_input`, and `awaiting-human`.
  - Execution state: pending

- [ ] E-03 Convert the remaining lifecycle item and statusline rendering in both drivers to the shared resolver, applying the Section 7.1 action-aware activity rule so a live turn shows `reviewing`, `executing`, `verifying`, `integrating`, or `recovering` rather than a generic `running`.
  - Depends on: E-02
  - Expected outcome: A live runner view names the specific activity when it knows it, and falls back to generic `active` only when the subtype is genuinely unavailable. Criterion A3 holds. A plan being executed still displays its STORED status unchanged (criterion A7), because the runner must not mutate an artifact to produce a display.
  - Execution state: pending

### Task group 3: Delete the duplicates and prove it

- [ ] E-04 Delete `term.py`'s `STATUS_COLOR_256` and any remaining lifecycle table now that every consumer routes through the shared module, per Section 12 step 6.
  - Depends on: E-03
  - Expected outcome: One lifecycle table exists in the package, in `lifecycle_style.py`. Nothing else defines a lifecycle color or glyph.
  - Execution state: pending

- [ ] E-05 Add the criterion A17 and A18 guard tests: assert no second lifecycle color or glyph table exists anywhere in the package, and assert the generic event, finding-severity, priority, and gate visuals still resolve independently and were not remapped as lifecycle state.
  - Depends on: E-04
  - Expected outcome: A test that FAILS if a future change reintroduces a local lifecycle palette. Severity and event visuals proven independent rather than assumed so.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Verified 2026-09-19: `render_stream.py:51 _STATUS_COLOR` maps `executed`, `reviewed`, `approved`, and `substantially-complete` all to `green`, which is the readiness/completion collapse the spec's Section 5 forbids.
- Verified 2026-09-19: the re-export chain is `render_stream._STATUS_COLOR` -> `oc_runipd.py:104` (+ `__all__` at 447), `agy_runipd.py:104` (aliased), `runner_shared.py:168` -> consumed at `runner_shared.py:12789`.
- File sizes make this the largest child: `runner_shared.py` 12822 lines, `oc_runipd.py` 7872, `agy_runipd.py` 4327, `render_stream.py` 2553. The E-items are split by module and by concern so each is executable in one focused pass.
- Four plans touch `render_stream.py` or the runners (`r2i1b1` and `st5klo` already executed; `ys1dor` and `zzcrlo` still pending as of 2026-09-19). Spec Section 12a classifies this as MERGE FRICTION ONLY, not an ordering hazard, because each execute item gets an isolated worktree and returns through the merge-and-revalidate gate.
- `render_stream.py` already carries a measured `use_unicode` ASCII-substitution pattern, which spec Section 9.4 names as the route to reuse.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md.
- `- Readiness:` is deliberately absent (it is `/plan-review`'s output; IPD-M107 refuses an unattested value).

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | The live runner palette collapses `approved` (ready) and `executed` (complete) into one green, which is the precise distinction spec Section 5 was written to protect, and it currently reaches every runner view through the re-export chain. | `render_stream.py:51-55`; re-exported at `oc_runipd.py:104`, `agy_runipd.py:104`, `runner_shared.py:168`. |
| F-02 | High | `term.py`'s `STATUS_COLOR_256` cannot be deleted before this child, because the unconverted runners still reach lifecycle styling through `term.py`. Section 12 step 6 sequences the deletion last for this reason, and doing it earlier would break live views. | Section 12 step 6; the `status_256`/`status_label` caller set measured in child `9zvl2w`. |
| F-03 | Medium | `render_stream.py` legitimately owns non-lifecycle visuals (event glyphs, severity colors) that R10.3 permits it to keep, so a blunt "remove the palette" edit here would delete working, in-spec behavior. E-01 separates the two deliberately. | R10.3: "`render_stream.py` MAY retain event glyphs and severity colors that are not lifecycle semantics"; criterion A18. |

## Proposed changes (ordered, validatable)

1. Convert `render_stream.py` lifecycle rows, keeping event and severity visuals (E-01).
2. Dismantle the `_STATUS_COLOR` re-export chain and convert its consumption site (E-02).
3. Convert both drivers' lifecycle rendering with action-aware activity (E-03).
4. Delete `term.py`'s `STATUS_COLOR_256` and any remaining lifecycle table (E-04).
5. Add A17/A18 guard tests that fail if a palette returns (E-05).

## Deferred / out of scope (with reason)

- Run outcome vocabulary, exit codes, and report sections: spec Section 0.5 states its override "covers DISPLAY only" and changes none of these. Touching them here would exceed the spec's own authority.
  - Carrier-Declined: Excluded by the granting authority itself: spec Section 0.5 bounds its override to DISPLAY only and changes no state, transition, exit code, or report section. Touching them would exceed the maintainer's ruling, so there is no obligation to carry.
- `render_stream.py`'s event glyphs and severity colors: R10.3 keeps them, and criterion A18 requires proving they were NOT remapped.
  - Carrier-Declined: R10.3 explicitly PERMITS this module to retain non-lifecycle event glyphs and severity colors, and criterion A18 requires proving they were not remapped. Retaining them is compliance, not deferred work.
- Generic `Term` OK/WARN/FAIL: R10.3 keeps them valid and explicitly warns against mechanically replacing every checkmark in the repository.
  - Carrier-Declined: EXPLICITLY OUT OF SCOPE by R10.3, which keeps these valid and warns against mechanically replacing every checkmark. No obligation to carry.
- A shared display-width helper: child `bn026f` records why the `render_stream` ASCII-table pattern satisfies Section 9.4 without one. If this child finds a case that genuinely needs true width, Section 9.4 requires it be shared, which is a separate change rather than a local guess.
  - Carrier-Declined: A conforming alternative is CHOSEN (the ASCII route Section 9.4 calls cheaper and proven), and Section 9.4 already binds any future true-width helper to be shared. Nothing outstanding.

## Scope check

- Over-scope: none. Every E-item maps to Section 12 step 5 or 6, R10.3, or criterion A17/A18.
- Under-scope: none. This child completes the conversion, which is why the deletion and the A17 guard both live here: deleting earlier breaks views, and asserting A17 before the deletion would assert something false.

## Required tests / validation

Run the suite BARE: `python3 -m pytest`. Paste the actual summary line. This is the largest-surface child and touches both drivers, so also paste evidence that runner behavior is unchanged beyond presentation: criterion A7 (a live executing plan keeps its stored `approved` status) and criterion A14 (no ANSI or schema change in `--agent`/`--json`).

## Spec / documentation sync

No `.spec.md` edit in this child, so none is declared in `- Scope-Paths:`. The `25kzda` Section 5.6 amendment that spec Section 0.5 REQUIRES is carried by child `7p3tt8`, which declares that spec file. Note the sequencing this creates: the superseded five-color table remains in the tree until `7p3tt8` lands, so a reader between these two children will find `25kzda` still describing the old scheme. That is a known, bounded documentation lag, and it is why `7p3tt8` is the final child rather than an optional follow-up.

## Open questions

### OQ-01: Does any runner statusline need a lifecycle glyph in a width-constrained cell that the ASCII pattern cannot satisfy?

- Blocking: no
- Status: open
- Owner: none
- Carrier-Declined: A CONFORMING FALLBACK ALWAYS EXISTS, so no obligation can outlive this plan. Section 9.3 guarantees single-byte alignment in ASCII mode, so a width-constrained statusline uses the ASCII form rather than requiring new machinery. This child's own E-03 covers the statusline and V-03 requires its rendered evidence; the question is recorded only to direct attention at the one repainting surface where `▶`'s measured ambiguous width could show.
- Resolution or deferral rationale: NOT BLOCKING because a conforming fallback always exists: Section 9.3 guarantees ASCII mode gives single-byte alignment, so a width-constrained statusline can use the ASCII form rather than requiring a new width helper. Recorded because the runners are the one surface with a live, repainting statusline where an ambiguous-width glyph could visibly misalign, and `▶` (this spec's `executing`) is one of the two glyphs `render_stream` already measured as ambiguous. The executing agent should check the statusline specifically rather than assuming the row-based evidence covers it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste `grep -n "_STATUS_COLOR" agent_workflows/render_stream.py` returning no table definition. Paste rendered lifecycle rows showing `approved` and `executed` in DIFFERENT colors, and paste the event-glyph and severity tests still passing (A18).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste `grep -rn "_STATUS_COLOR" agent_workflows/` showing no import, alias, or `__all__` entry remains. Paste the converted `runner_shared.py:12789` site and its resolved output for `ran`, `unknown_outcome`, `needs_input`, and `awaiting-human`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste runner view output for each of the five action-aware activities showing the correct glyph and the exact activity word (A3). Paste evidence for A7: a plan displayed as `executing` whose on-disk `- Status:` is still `approved`, with the file content shown.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste `grep -rn "STATUS_COLOR_256" agent_workflows/` returning NO matches.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the BARE `python3 -m pytest` summary line. Paste the A17 guard test FAILING against a deliberately reintroduced local palette, then passing after removal: a guard that cannot fail is not evidence. Paste the A18 assertions showing severity, event, priority, and gate visuals resolve independently.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved qdd5jq --by-human`). Its `- Item-Dependencies: executed:9zvl2w` edge is re-checked at dispatch, sequencing it after the non-runner consumers per Section 12 steps 4 and 5, so the table deletion in E-04 happens only when nothing else reads them.

On completion: append the workflow-history line, set the terminal `Status: executed`, and `git mv` this plan to `.aw/records/plans/executed/` as a post-gate lifecycle step via `aw ipd finalize`, never as a checklist item. Commit path-scoped; never push.
