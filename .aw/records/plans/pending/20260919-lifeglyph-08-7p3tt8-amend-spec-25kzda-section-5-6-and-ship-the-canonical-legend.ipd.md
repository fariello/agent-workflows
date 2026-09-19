# IPD: Amend spec 25kzda section 5.6 and ship the canonical legend

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` Section 0.5 makes an amendment MANDATORY rather than optional: "the plan that lands the resolver MUST amend `25kzda` Section 5.6 to point here rather than leaving two live color tables in the tree, and MUST declare that spec file in its `Scope-Paths`", with the stated reason that "An override recorded only in the winning spec leaves the losing spec still saying the opposite to the next reader." Verified 2026-09-19: `25kzda` Section 5.6 (line 1085) still carries the superseded five-color scheme verbatim (cyan for running-or-verifying, green for verified, yellow for skipped/needs-input/ran, red for failed, gray for informational) with no pointer to `uonrjg`, and `25kzda` is itself `approved` with `Blocks-Release: next`. A THIRD stale surface exists that the spec does not name: `docs/cli-human-guide.md:67` tells users "Only the sixteen named colors ... are used; there is no assumed background, no truecolor", which contradicts both the corrected accessibility lens and this spec's 256-color top tier.
- Scope: IN: amend `25kzda` Section 5.6 to point at `uonrjg` as the authority for lifecycle color and glyph while leaving its outcome vocabulary, exit codes, and reporting columns untouched; correct the stale 16-color claim in `docs/cli-human-guide.md`; ship ONE canonical legend in command help and user documentation per Section 12 step 7. OUT: any change to `25kzda`'s vocabulary, exit codes, or report columns (Section 0.5 scopes the override to DISPLAY only), and re-correcting the accessibility lens, which was already corrected during the spec's own review.
- Scope-Paths: .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md, docs/cli-human-guide.md, agent_workflows/cli.py, tests/test_docs.py
- Item-Dependencies: executed:qdd5jq
- Status: to-review
- Set: lifeglyph
- Order: 8
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 7p3tt8
- From-Spec: uonrjg
- Blocks-Release: next

## Workflow history

- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from spec uonrjg Section 0.5 (the mandatory amendment) and Section 12 step 7. Carries the spec's `Blocks-Release: next` gate.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the override real rather than asserted: leave no second lifecycle color table in the tree, no user documentation contradicting the shipped palette, and exactly one canonical legend a reader can find.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The mandatory spec amendment

- [ ] E-01 Amend `25kzda` Section 5.6 (line 1085) so its five-color list points at `uonrjg` as the authority for lifecycle color and glyph, and record the supersession in `25kzda`'s own workflow history via `aw specs note`. Leave Section 5.6's outcome vocabulary, exit codes, and reporting columns UNCHANGED.
  - Depends on: none
  - Expected outcome: A reader arriving at `25kzda` Section 5.6 is sent to `uonrjg` rather than given a contradicting palette. `25kzda`'s `- Status:` stays `approved`; only the display paragraph changes, plus an appended history line.
  - Execution state: pending

- [ ] E-05 ADD THE MISSING `integration-deferred` ROW TO SPEC SECTION 7.2, mapping it to `recovering`. This is not discretionary: measured 2026-09-19, `integration-deferred` is the ONLY one of the 15 `runner_shutdown.KNOWN_ITEM_STATUSES` members that appears ZERO times in `uonrjg`, so without this row a faithful criterion A2 assertion over that owner enum FAILS and child `udgilu`'s E-05 is unsatisfiable. The stage was resolved from code evidence in `udgilu` OQ-02 (`runner_shutdown.py:84-87` files it as in-flight and "awaiting a re-attempt"; `oc_runipd.py:6123` records it as deliberately non-terminal; `oc_runipd.py:6554-6560` shows the re-attempt is automatically scheduled at zero cost), which is the spec's own definition of `recovering` and not of `blocked`.
  - Depends on: none
  - Expected outcome: Section 7.2 carries an `integration-deferred` -> `recovering` row, so every member of `KNOWN_ITEM_STATUSES` has exactly one mapping and `udgilu`'s A2 test can pass over that enum.
  - Execution state: pending

### Task group 2: The stale user-facing claim

- [ ] E-02 Correct `docs/cli-human-guide.md:67-68`, which currently tells users only the sixteen named colors are used and there is no truecolor. Replace it with the actual 256/16/none ladder, the user's depth pin, and the rule that `NO_COLOR` outranks the pin.
  - Depends on: none
  - Expected outcome: The guide matches what ships. The "color is never the sole carrier" invariant is PRESERVED, since that part was always correct and remains true at every tier.
  - Execution state: pending

### Task group 3: One canonical legend

- [ ] E-03 Ship ONE canonical legend covering the 21 stages with their glyph, ASCII fallback, and word, reachable from command help per Section 9.2, and referenced (not duplicated) from user documentation. Order it by lifecycle word order, not by color name, per Section 11 item 6.
  - Depends on: E-02
  - Expected outcome: A single legend definition with one rendering path. The legend is available in command help and referenced from the docs rather than copy-pasted, so it cannot drift.
  - Execution state: pending

- [ ] E-04 Add a drift guard asserting the legend, the documentation, and `lifecycle_style`'s table cannot disagree: the legend must be GENERATED from the shared module rather than hand-maintained, and a test must fail if a stage is added without appearing in the legend.
  - Depends on: E-03
  - Expected outcome: Adding a 22nd stage to `lifecycle_style` without touching the legend FAILS the suite. This is what prevents this Set's whole point from rotting into a fourth stale table.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Verified 2026-09-19: `25kzda` Section 5.6 is at line 1085 of `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` and still lists the five superseded colors with no pointer to `uonrjg`.
- Verified 2026-09-19: `25kzda` is `- Status: approved` with `- Blocks-Release: next`, so amending it touches a live release-gating contract. That is exactly why `uonrjg` Section 0.5 requires the file be DECLARED in `Scope-Paths` (it is, above), so both runners announce the declared spec edit before the run and reconcile it at finalize.
- Verified 2026-09-19: the accessibility lens was ALREADY corrected during the spec's review (`.aw/system/workflows/assess/lenses/accessibility.md` now states the 256/16/none ladder, that a user's explicit choice outranks detection, and that `NO_COLOR` still wins, plus a history note). It must NOT be re-corrected; OQ-01's amendment obligation is discharged.
- Verified 2026-09-19: `docs/cli-human-guide.md:67-68` carries a 16-colors-only claim that the corrected lens and this spec both contradict. The spec does not name this file, so E-02 is work this plan ADDS on evidence rather than inherits.
- AGENTS.md forbids em and en dashes in USER-FACING prose the agent authors, which `docs/cli-human-guide.md` is. The spec files and this plan are internal artifacts and are exempt.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md.
- `- Readiness:` is deliberately absent (it is `/plan-review`'s output; IPD-M107 refuses an unattested value).

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | The spec's override is currently an assertion only: the losing spec still states the opposite palette to any reader who arrives there, which is precisely the failure Section 0.5 says the amendment exists to prevent. | `25kzda` Section 5.6 at line 1085, read 2026-09-19: the five-color list is intact with no `uonrjg` reference. |
| F-02 | Medium | A third stale color claim ships to USERS, not just to spec readers, and the spec never names it. `docs/cli-human-guide.md:67` promises no truecolor and sixteen named colors only. | `docs/cli-human-guide.md:67-68`, read 2026-09-19. |
| F-03 | Medium | Without a generated legend this Set creates a NEW drift surface: a hand-maintained 21-row legend in docs is exactly the kind of partial table the spec's Section 1 complains about. E-04 exists to make that structurally impossible rather than merely discouraged. | Spec Section 1 ("adding a new artifact status requires finding several partial tables"); Section 12 step 7. |

## Proposed changes (ordered, validatable)

1. Amend `25kzda` Section 5.6 to point at `uonrjg`, vocabulary untouched (E-01).
2. Correct the stale 16-color claim in the user guide (E-02).
3. Ship one canonical legend in help, referenced from docs (E-03).
4. Guard the legend against drift by generating it from the shared module (E-04).

## Deferred / out of scope (with reason)

- `25kzda`'s outcome vocabulary, exit codes, and reporting columns: spec Section 0.5 states plainly that the override "covers DISPLAY only and changes no state, transition, exit code, or report section". Touching them would exceed the authority the maintainer granted.
  - Carrier-Declined: Explicitly OUT OF SCOPE by the granting authority itself rather than deferred work. Section 0.5 bounds the override to display and says so twice; there is no outstanding obligation to carry, and filing one would assert work the ruling forbids.
- Re-correcting the accessibility lens: already done during the spec's own review and verified in Step 0. Re-applying it would either no-op or regress a correct file.
  - Carrier-Declined: Already DISCHARGED, verified in-tree 2026-09-19 at `.aw/system/workflows/assess/lenses/accessibility.md`, which now states the 256/16/none ladder plus the choice-outranks-detection and NO_COLOR-wins rules. Nothing is outstanding.
- The spec's OQ-02 (whether `needs_input` or `awaiting-human` retires): upstream lifecycle-vocabulary question the spec deliberately holds open and out of its own scope.
  - Carrier-Declined: The spec OWNS it and declined to decide it ("DELIBERATELY NOT THIS SPEC'S TO DECIDE"), with a stated closing condition: whoever wires `run_gates` into the runners decides. Not an obligation this presentation Set incurs, and the spec's tables need no change either way.

## Scope check

- Over-scope: none. E-01 and E-03 are named obligations of the spec; E-02 and E-04 are evidence-driven additions within the same concern (no stale lifecycle color statement left in the tree).
- Under-scope: none. Note E-02 and E-04 exceed the spec's literal text, deliberately: the spec requires one canonical legend and no second live table, and a stale user-facing claim plus a hand-maintained legend would both violate that intent while passing its letter.

## Required tests / validation

Run the suite BARE: `python3 -m pytest`. Paste the actual summary line. Additionally run `aw check specs` to confirm the amended `25kzda` still conforms, and `aw sanitize --agent` since this child edits user-facing documentation.

## Spec / documentation sync

THIS CHILD IS THE SPEC-SYNC STEP FOR THE WHOLE SET, and it is why the Set has an eighth child rather than stopping at the code. `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` is DECLARED in `- Scope-Paths:` above, so both runners announce the declared spec edit before the run starts and the finalize scope gate reconciles what was actually changed against what was declared. WHY the amendment is legitimate rather than an unauthorized edit of an approved, release-gating spec: AGENTS.md states a plan MAY amend a spec and MUST declare it, and `uonrjg` Section 0.5 does not merely permit this amendment but REQUIRES it, on a recorded maintainer ruling of 2026-09-13. The amendment is bounded to the display paragraph; `25kzda`'s vocabulary, exit codes, and report columns are untouched.

## Open questions

### OQ-01: Does amending an approved, release-gating spec need a fresh human approval?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: SELF-CLOSING AT EXECUTION, and the authority is already recorded. The maintainer ruled on 2026-09-13 that this specific amendment MUST happen (`uonrjg` Section 0.5), so the instruction to amend predates this plan and no new decision is being taken. The residual question is procedural, surfaces at execution time when the runner announces the declared spec edit, and is answerable by the human then. There is no obligation outstanding after this plan executes, so a carrier would name a work item that does not exist.
- Resolution or deferral rationale: NOT BLOCKING because the amendment is mandated by a recorded ruling rather than proposed by this plan, and because the declared-spec-edit announcement gives the maintainer a checkpoint before the run proceeds. Recorded rather than assumed because `25kzda` is `approved` AND carries `Blocks-Release: next`, so editing it is the highest-leverage change in this Set, and an agent should not treat a spec edit as routine merely because a plan declared it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the `git diff` of `25kzda` Section 5.6 showing the five-color list now points at `uonrjg`. Paste the appended workflow-history line. Paste proof of what did NOT change: the section's outcome vocabulary, exit codes, and reporting-column sentence must be byte-identical, shown by the diff containing no changes to them.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the `git diff` of `uonrjg` Section 7.2 showing the added `integration-deferred` -> `recovering` row. Then paste a programmatic check that EVERY member of `runner_shutdown.KNOWN_ITEM_STATUSES` (15 members) now appears in the spec, with an empty "missing" list as the result. A diff alone FAILS this item, because the point is total coverage of the owner enum rather than one row being present.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the `git diff` of `docs/cli-human-guide.md` showing the 16-colors-only claim replaced by the 256/16/none ladder plus the depth pin and the `NO_COLOR`-wins rule. Paste the surviving "never the sole carrier" sentence proving it was preserved. Paste `aw sanitize --agent` output, and confirm no em or en dash was introduced into this user-facing file.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the legend as rendered from command help, showing all 21 stages with glyph, ASCII fallback, and word in lifecycle order rather than color-name order. Paste the documentation reference proving it points at the single legend rather than duplicating it.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the BARE `python3 -m pytest` summary line. Then prove the guard bites: add a 22nd stage to `lifecycle_style` in a scratch edit, show the suite FAILING because the legend does not cover it, revert, and show it passing. A guard that cannot fail is not evidence. Paste `aw check specs` output confirming the amended spec conforms.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved 7p3tt8 --by-human`). Its `- Item-Dependencies: executed:qdd5jq` edge is re-checked at dispatch, placing it last in the Set: the legend is generated from the shared module and the "no second table remains" claim is only true once `qdd5jq` has deleted them, so amending the docs earlier would document a state that does not yet exist.

On completion: append the workflow-history line, set the terminal `Status: executed`, and `git mv` this plan to `.aw/records/plans/executed/` as a post-gate lifecycle step via `aw ipd finalize`, never as a checklist item. Commit path-scoped; never push.
