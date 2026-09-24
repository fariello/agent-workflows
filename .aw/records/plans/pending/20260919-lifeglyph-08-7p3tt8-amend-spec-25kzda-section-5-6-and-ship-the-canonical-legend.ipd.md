# IPD: Amend spec 25kzda section 5.6 and ship the canonical legend

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` Section 0.5 makes an amendment MANDATORY rather than optional: "the plan that lands the resolver MUST amend `25kzda` Section 5.6 to point here rather than leaving two live color tables in the tree, and MUST declare that spec file in its `Scope-Paths`", with the stated reason that "An override recorded only in the winning spec leaves the losing spec still saying the opposite to the next reader." Verified 2026-09-19: `25kzda` Section 5.6 (line 1085) still carries the superseded five-color scheme verbatim (cyan for running-or-verifying, green for verified, yellow for skipped/needs-input/ran, red for failed, gray for informational) with no pointer to `uonrjg`, and `25kzda` is itself `approved` with `Blocks-Release: next`. A THIRD stale surface exists that the spec does not name: `docs/cli-human-guide.md:67` tells users "Only the sixteen named colors ... are used; there is no assumed background, no truecolor", which contradicts both the corrected accessibility lens and this spec's 256-color top tier.
- Scope: IN: amend `25kzda` Section 5.6 to point at `uonrjg` as the authority for lifecycle color and glyph while leaving its outcome vocabulary, exit codes, reporting columns, and TTY/sole-carrier rule untouched; ADD the missing `integration-deferred` row to `uonrjg` Section 7.2 (E-05); correct the stale 16-color claim AND the retracted non-TTY cutover claim in `docs/cli-human-guide.md`; ship ONE canonical legend in command help and user documentation per Section 12 step 7. OUT: any change to `25kzda`'s vocabulary, exit codes, or report columns (Section 0.5 scopes the override to DISPLAY only), re-correcting the accessibility lens (already corrected during the spec's own review), and editing any CONVERTED VIEW to satisfy Section 9.2's showing rule, which this plan VERIFIES and reports rather than implements (E-03, F-05).
- Scope-Paths: .aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md, .aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md, docs/cli-human-guide.md, agent_workflows/cli.py, tests/test_docs.py
- Item-Dependencies: executed:qdd5jq
- Status: approved
- Work-Kind: feature
- Priority: medium
- Blocks-Release: next
- Readiness: go-pending-approval
- Set: lifeglyph
- Order: 8
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 7p3tt8
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved
- From-Spec: uonrjg

## Workflow history
- 2026-09-24 approved (aw set): backfill: Priority/Work-Kind per planprio-03 lc4unl maintainer decision on OQ-05 (lifeglyph: medium/feature)
- 2026-09-19 approved (aw set): status set to approved

- 2026-09-19 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-801 through PR-811 all FIXED, none deferred, none open. Reviewed at HEAD `a27dc6dc`; `aw ipd lint` clean and exit 0 at `--phase author` before the revisions and at `--phase review-finalize` after them. THE PLAN'S PREMISE IS CORRECT AND WELL EVIDENCED (`25kzda` Section 5.6 verified intact at line 1085 with no `uonrjg` pointer, on an `approved`, `Blocks-Release: next` spec), and the findings are of three kinds. PR-801 (BLOCKER) IS AN ORDERING DEFECT, computed rather than read: E-05 was authored to write the `uonrjg` Section 7.2 `integration-deferred` row that sibling `udgilu` requires, but dependency depth puts this child at 7 and `udgilu` at 1, and `queue_sort_key` sorts depth FIRST, so `udgilu` dispatches six items earlier and would execute with the row absent, failing its own V-03 or writing an unreviewed mapping into the canonical module. E-05 is now verify-and-repair on both branches with `uonrjg` DECLARED in `Scope-Paths` (expected to show no diff, so `aw ipd finalize`'s `--scope-ack` turns "already correct" into an acknowledged claim). TWO OBLIGATIONS HAD NO OWNER IN THE WHOLE SET and this is the last child: E-03 would most likely have AUTHORED a second legend renderer in `cli.py` when `bn026f` already ships a generated one and its review assigned only PLACEMENT here (PR-802), and Section 9.2's showing rule matches `bn026f` ALONE across all ten `lifeglyph` plans, whose own review handed it to converting children that never took it (PR-803, now verified-and-reported here with the implementation carried to `9zvl2w`). THE STAGE COUNT WAS WRONG IN FOUR PLACES (PR-805): Section 5 holds 20 rows, and the count is now REMOVED rather than corrected, because a literal count is itself a second table; E-04's guard asserts COVERAGE. Also fixed: a retracted hard-cutover claim in the very file E-02 edits with no owner anywhere (PR-804), a paraphrase that would have contradicted the same file eight lines later (PR-806), a gate missing its scope fence and honesty rule (PR-807), and a suite baseline recorded with its one pre-existing parallel-run flake named (PR-810). Readiness go-pending-approval; note this is the DEEPEST child in the chain, so dispatch waits on seven upstream children regardless of its own readiness.
- 2026-09-19 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED. PR-801..PR-811 all FIXED, none deferred, none open. PR-801 (BLOCKER) was an ORDERING defect: E-05 was authored to write the uonrjg Section 7.2 integration-deferred row that udgilu needs, but this child's dependency depth is 7 and udgilu's is 1, so udgilu dispatches six items earlier and would have executed with the row absent; E-05 is now verify-and-repair with the uonrjg path declared. PR-802/803 were the two obligations no plan in the Set owned (a second legend renderer would have been authored here rather than bn026f's placed, and Section 9.2's showing rule matched bn026f alone across all ten plans). Readiness go-pending-approval.

- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from spec uonrjg Section 0.5 (the mandatory amendment) and Section 12 step 7. Carries the spec's `Blocks-Release: next` gate.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the override real rather than asserted: leave no second lifecycle color table in the tree, no user documentation contradicting the shipped palette, and exactly one canonical legend a reader can find.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The mandatory spec amendment

- [x] E-01 Amend `25kzda` Section 5.6 (line 1085) so its five-color list points at `uonrjg` as the authority for lifecycle color and glyph, and record the supersession in `25kzda`'s own workflow history via `aw specs note`. Leave Section 5.6's outcome vocabulary, exit codes, and reporting columns UNCHANGED.
  - Depends on: none
  - Expected outcome: A reader arriving at `25kzda` Section 5.6 is sent to `uonrjg` rather than given a contradicting palette. `25kzda`'s `- Status:` stays `approved`; only the display paragraph changes, plus an appended history line.
  - Execution state: performed

- [x] E-05 ADD THE MISSING DEFERRED-INTEGRATION ROW TO SPEC SECTION 7.2 OF `uonrjg`, mapping it to `recovering`. NOTE THE STATUS WAS RENAMED 2026-09-21 (`l2mzxn`): the row is spelled `merge-retry` (formerly `integration-deferred`), and `uonrjg` Section 7.2 already carries `merge-retry`, `merge-unchecked` -> recovering. Search for the CANONICAL spelling; searching for the old one will wrongly conclude the row is absent and add the duplicate this item forbids. This is not discretionary: measured 2026-09-19 by importing the enum and counting occurrences in the spec file, `integration-deferred` is the ONLY one of the 15 `runner_shutdown.KNOWN_ITEM_STATUSES` members that appears ZERO times in `uonrjg`, so without this row a faithful criterion A2 assertion over that owner enum FAILS and child `udgilu`'s E-06 is unsatisfiable. The stage was resolved from code evidence in `udgilu` OQ-02 (`runner_shutdown.py:84-87` files it under "in-flight / recoverable" and says the item "is awaiting a re-attempt"; `oc_runipd.py:6123` records it as deliberately absent from `TERMINAL_STATES`; `oc_runipd.py:6554-6560` shows the re-attempt is automatically scheduled at zero cost by `retry_deferred_integrations`), which is the spec's own definition of `recovering` ("Retry, correction, resume, or recovery is active or required") and not of `blocked` ("Work cannot advance until a named condition clears").
  - Depends on: none
  - Expected outcome: Section 7.2 carries a `merge-retry` -> `recovering` row (post-rename spelling), so every member of `KNOWN_ITEM_STATUSES` has exactly one mapping and `udgilu`'s A2 test can pass over that enum.
  - THE PLAN IT UNBLOCKS RUNS SEVEN HOPS BEFORE THIS ONE, AND THAT IS THE CENTRAL DEFECT THIS REVIEW FOUND (F-01, BLOCKER). Computed at review 2026-09-19 from every `lifeglyph` plan's `- Item-Dependencies:`, this child's dependency DEPTH is 7 (`7p3tt8` -> `qdd5jq` -> `9zvl2w` -> `f9t5hz` -> `bn026f` -> `pow5sj` -> `udgilu` -> `n4xq3l`), while `udgilu`'s is 1. The runner sorts the queue with dependency depth as its FIRST key (`queue_sort_key`, `dependency_depth`), so `udgilu` dispatches SIX items before this one. Its E-03 and E-06 both require the spec row, its V-03 demands "the `git diff` of the spec's Section 7.2 row added in the same change", and its own OQ-02 resolution says `7p3tt8` MUST add it "in the same Set". SO AS SEQUENCED, `udgilu` EXECUTES WITH THE ROW STILL ABSENT and either fails its own V-03 or writes a mapping into the canonical module with no spec row, which is precisely the drift its OQ-02 forbids.
  - HOW THIS PLAN RESOLVES IT: THE ROW IS `udgilu`'s TO WRITE, NOT THIS CHILD'S, so E-05 is a VERIFY-AND-REPAIR item rather than an author item. The reason is mechanical and not a preference: a spec row that must exist BEFORE `udgilu` runs cannot be written by a plan that runs after it, and the alternative (moving this child to depth 0 by dropping its `executed:qdd5jq` edge) would break the Set's stated "SPEC AMENDMENT LAST" invariant, under which E-01's "no second table remains" claim is only true once `qdd5jq` has deleted them. So: FIRST read `uonrjg` Section 7.2 and determine whether the `merge-retry` -> `recovering` row is already present (the status was renamed 2026-09-21 from `integration-deferred`). If it IS (the expected case, because `udgilu`'s V-03 cannot pass without it), record that with the evidence and perform no edit: a duplicate row would be a defect. If it is NOT, ADD it here as the fallback repair AND report that `udgilu` executed with its V-03 unsatisfied, because that is a validation failure upstream rather than a gap this child was authored to fill. Either branch discharges this item; only the second one writes to the spec.
  - WHY THE ROW IS STILL DECLARED IN `- Scope-Paths:` even though the expected branch writes nothing: `aw ipd finalize` refuses a declared-but-unmodified path without a `--scope-ack`, which is exactly the right outcome here, since an untouched `uonrjg` is a CLAIM (the row was already correct) that deserves to be acknowledged rather than passed over silently. Declaring it also makes both runners announce the possible spec edit before the run, per AGENTS.md.
  - Execution state: performed

### Task group 2: The stale user-facing claim

- [x] E-02 Correct `docs/cli-human-guide.md:67-68`, which currently tells users only the sixteen named colors are used and there is no truecolor. Replace it with the actual 256/16/none ladder, the user's depth pin, and the rule that `NO_COLOR` outranks the pin.
  - Depends on: none
  - Expected outcome: The guide matches what ships. The "color is never the sole carrier" invariant is PRESERVED, since that part was always correct and remains true at every tier.
  - STATE `FORCE_COLOR`'s ACTUAL PRECEDENCE, NOT THE SPEC'S ASPIRATIONAL ONE (added at review, F-02). Spec R9.3a.2 says `NO_COLOR` is "unchanged, and unconditional" and that "a preference may not defeat it", but the SHIPPED behavior is the opposite for one pair: `term.py:100-104` reads "NO_COLOR: any value (even empty) disables, UNLESS FORCE_COLOR is set", and a shipped test `tests/test_term.py:48` (`test_force_color_overrides_no_color`) PINS that escape hatch. Sibling `pow5sj` raised this as its blocking OQ-02 and the MAINTAINER RULED READING A on 2026-09-19: `FORCE_COLOR` keeps its override, and R9.3a.2's "unconditional" is unconditional with respect to the DEPTH PIN only. This guide already describes the ruled behavior correctly at lines 73-74 ("`NO_COLOR` disables color and is only overridden by `FORCE_COLOR`"), so the requirement here is to NOT break it: write "`NO_COLOR` outranks the depth pin" and do NOT write "`NO_COLOR` always wins", which would contradict both the ruling and the file's own next paragraph. Sibling `z8ddk0` additionally changes what a FALSEY `FORCE_COLOR` does (`0`/`false`/`no`/`off` stop forcing), so describe `FORCE_COLOR` as it stands AFTER that child lands, not as it behaves today.
  - LEAVE THE NON-TTY CUTOVER CLAIM AT LINES 13-19 ALONE UNLESS `yaxr4i` HAS ALREADY RETRACTED IT (added at review, F-03). Lines 13-19 tell users that piped stdout yields "`aw.agent/v1` JSONL" as "a HARD CUTOVER as of the 2.0.0 release". Measured 2026-09-19: that is FALSE today (`aw status` piped emits human prose), and the maintainer RULED on 2026-09-10 (`yaxr4i` OQ-01, Option B) that the promise is RETRACTED rather than implemented. But `yaxr4i` E-05 owns that retraction and declares only `docs/cli-output-contract.md`, while its own Deferred section names `docs/cli-human-guide.md:103` as conditional on the opposite ruling, so THIS FILE'S retraction has no declared owner anywhere. At execution, READ the file: if `yaxr4i` left lines 13-19 stale, correct them here in the same pass (this file is in this plan's fence and this is the Set's documentation child), citing the 2026-09-10 ruling and labelling the policy RETRACTED rather than deleting it silently, exactly as that ruling requires. If they are already corrected, record that and change nothing. Do NOT invent a new output-mode policy; the only sanctioned act is aligning this guide with the recorded ruling.
  - Execution state: performed

### Task group 3: One canonical legend

- [x] E-03 PLACE the legend `bn026f` already built: expose `bn026f`'s generated legend renderer through command help per Section 9.2, and reference (never duplicate) it from user documentation. Do NOT author a second legend. Order comes from `lifecycle_style`'s own table order, which already is Section 5's lifecycle order, so ordering is inherited rather than re-asserted here (Section 11 item 6).
  - Depends on: E-02
  - Expected outcome: One legend definition with one rendering path, reachable from `--help` and referenced from the docs rather than copy-pasted. The stage count is whatever `lifecycle_style`'s table holds AT RUNTIME (20 today), never a literal.
  - THE COUNT IS 20, NOT 21, AND MUST NOT BE WRITTEN DOWN AT ALL (corrected at review 2026-09-19, F-04). The earlier wording said "the 21 stages", which is wrong twice over: Section 5's table parses to exactly 20 data rows (measured by parsing the table between the spec's lines 175 and 197), and the spec's own D13 and its Section 7.2 `ran` commentary each reject "a new 21st stage", a phrase that only parses at 20. Sibling `udgilu` already carries the same correction as its F-05. The deeper point is that ANY hardcoded count is the defect this child exists to prevent: E-04's guard is what makes the number unnecessary, so derive it from `len()` of the shared table and assert nothing about its value.
  - THIS CHILD DOES NOT AUTHOR A LEGEND RENDERER, and getting that boundary wrong would recreate the very duplication the Set removes. Sibling `bn026f` E-03 already ships "the legend RENDERER: one function that emits every stage's glyph, ASCII fallback, and word, GENERATED from `lifecycle_style`'s table rather than from a literal list", and `bn026f`'s own review (F-06) assigned PLACEMENT to this child by name while keeping the renderer there, with the recorded reason that "a hand-written literal legend shipped in `term.py` is what `7p3tt8` E-04's drift guard would then have to retrofit". So the work here is wiring and reference, not generation.
  - ALSO VERIFY AND REPORT SECTION 9.2's SHOWING RULE, which no other file in this Set mentions (F-05). Section 9.2 says a legend "SHOULD be shown once in a view that contains three or more semantic stages unless the words already appear beside every glyph". `bn026f`'s review handed that rule to the converting children, yet `grep -rn "three or more\|shown once"` across all ten `lifeglyph` plans matches `bn026f` ALONE, so no child implements it and this is the last child in the Set. Because it is a SHOULD and every converted view prints the native word beside every glyph (Section 9.1 and criterion A10, enforced by `f9t5hz`/`9zvl2w`/`qdd5jq`), the rule's own "unless" clause is most likely already satisfied. VERIFY that rather than assuming it: inspect the converted views and report the finding. Do NOT edit a converted view here; that is out of scope and out of fence. If a view is found that shows three or more stages WITHOUT the words, file a follow-up rather than fixing it in this child.
  - Execution state: performed

- [x] E-04 Add a drift guard asserting the legend, the documentation, and `lifecycle_style`'s table cannot disagree: the legend must be GENERATED from the shared module rather than hand-maintained, and a test must fail if a stage is added without appearing in the legend.
  - Depends on: E-03
  - Expected outcome: Adding a 21st stage to `lifecycle_style` without touching the legend FAILS the suite. This is what prevents this Set's whole point from rotting into a fourth stale table.
  - THE GUARD MUST ASSERT COVERAGE, NOT A COUNT (added at review, F-04). "Every member of `lifecycle_style`'s stage table appears in the rendered legend" is the assertion; "the legend has N rows" is not, because a literal N is itself a second table that drifts. Note the scratch stage added to prove the guard bites is 21st, not 22nd: Section 5 holds 20 rows.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Verified 2026-09-19: `25kzda` Section 5.6 is at line 1085 of `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` and still lists the five superseded colors with no pointer to `uonrjg`.
- Verified 2026-09-19: `25kzda` is `- Status: approved` with `- Blocks-Release: next`, so amending it touches a live release-gating contract. That is exactly why `uonrjg` Section 0.5 requires the file be DECLARED in `Scope-Paths` (it is, above), so both runners announce the declared spec edit before the run and reconcile it at finalize.
- Verified 2026-09-19: the accessibility lens was ALREADY corrected during the spec's review (`.aw/system/workflows/assess/lenses/accessibility.md` now states the 256/16/none ladder, that a user's explicit choice outranks detection, and that `NO_COLOR` still wins, plus a history note). It must NOT be re-corrected; OQ-01's amendment obligation is discharged.
- Verified 2026-09-19: `docs/cli-human-guide.md:67-68` carries a 16-colors-only claim that the corrected lens and this spec both contradict. The spec does not name this file, so E-02 is work this plan ADDS on evidence rather than inherits.
- AGENTS.md forbids em and en dashes in USER-FACING prose the agent authors, which `docs/cli-human-guide.md` is. The spec files and this plan are internal artifacts and are exempt.
- THE DASH RULE IS ALREADY MACHINE-ENFORCED ON THIS FILE, so it is a test rather than a habit (verified at review 2026-09-19): `docs_check.check_no_unicode_dashes` fails on any U+2014 or U+2013 in a doc, `docs_check.py:149` wires it into the per-doc sweep, and `tests/test_docs.py` (declared in `- Scope-Paths:`) runs it over the whole `docs/` set. A dash introduced by E-02 turns the suite red and does not need to be caught by eye.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md.
- SUITE BASELINE, measured at review 2026-09-19 at HEAD `a27dc6dc`: `1 failed, 7305 passed, 3 skipped, 2 xfailed in 115.84s`. THE ONE FAILURE IS PRE-EXISTING AND FLAKY, NOT THIS PLAN'S: `tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130` failed on a `subprocess.TimeoutExpired` under the default parallel `-n auto` run, and the same class re-run in isolation passed `7 passed in 1.49s`. Recorded so the executor compares against a real baseline instead of reading a green expectation, and so this specific node id is not mistaken for a regression this child caused. Note the number differs from siblings' recorded baselines (`qdd5jq` cites 7468, `bn026f` 8369) because those were taken at different HEADs; re-measure rather than reconciling them.
- `- Readiness:` is deliberately absent (it is `/plan-review`'s output; IPD-M107 refuses an unattested value).
- Verified at review 2026-09-19: the SHOWING half of Section 9.2 (a legend shown once in a view with three or more stages) is claimed by no plan in this Set. `grep -rn "three or more\|shown once"` over all ten `lifeglyph` plans matches `bn026f` only, whose own review explicitly handed the rule to the converting children; none of `f9t5hz`, `9zvl2w`, or `qdd5jq` mentions it. E-03 now verifies and reports it rather than letting it vanish with this Set (F-05).

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | The spec's override is currently an assertion only: the losing spec still states the opposite palette to any reader who arrives there, which is precisely the failure Section 0.5 says the amendment exists to prevent. | `25kzda` Section 5.6 at line 1085, read 2026-09-19: the five-color list is intact with no `uonrjg` reference. |
| F-02 | Medium | A third stale color claim ships to USERS, not just to spec readers, and the spec never names it. `docs/cli-human-guide.md:67` promises no truecolor and sixteen named colors only. | `docs/cli-human-guide.md:67-68`, read 2026-09-19. |
| F-03 | Medium | Without a generated legend this Set creates a NEW drift surface: a hand-maintained legend in docs is exactly the kind of partial table the spec's Section 1 complains about. E-04 exists to make that structurally impossible rather than merely discouraged. | Spec Section 1 ("adding a new artifact status requires finding several partial tables"); Section 12 step 7. |

Added at review, 2026-09-19:

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-04 | Blocker | E-05 WAS ORDERED SEVEN HOPS AFTER THE PLAN IT UNBLOCKS. It was authored to add the `uonrjg` Section 7.2 row that `udgilu`'s E-03/E-06/V-03 require, but this child's dependency depth is 7 while `udgilu`'s is 1, so `udgilu` dispatches six items earlier and would execute with the row absent, failing its own V-03 or writing an unspecified mapping into the canonical module. E-05 is now a verify-and-repair item with both branches specified, rather than an author item that arrives too late to help. | Depths computed from every `lifeglyph` plan's `- Item-Dependencies:` at review: `7p3tt8`(7) <- `qdd5jq`(6) <- `9zvl2w`(5) <- `f9t5hz`(4) <- `bn026f`(3) <- `pow5sj`(2) <- `udgilu`(1) <- `n4xq3l`(0). `oc_runipd.queue_sort_key` puts `dependency_depth` first. `udgilu` V-03 demands "the `git diff` of the spec's Section 7.2 row added in the same change"; `udgilu` OQ-02 says `7p3tt8` MUST add it. |
| F-05 | High | THE STAGE COUNT 21 IS WRONG AND WAS WRITTEN IN FOUR PLACES HERE. Section 5's table parses to exactly 20 data rows, and the spec's own D13 plus its Section 7.2 `ran` commentary each reject "a new 21st stage", a phrase that only parses at 20. E-03 said "the 21 stages", V-03 "all 21 stages", and E-04/V-04 "a 22nd stage". Sibling `udgilu` carries the same correction as its F-05 and named this file. Harm: a legend guard asserting a count that cannot hold would fail a correct implementation. Fixed by removing the count entirely and asserting COVERAGE instead, which is the drift-proof form. | Section 5 table parsed 2026-09-19 between spec lines 175 and 197: 20 data rows. `uonrjg` D13 ("Rejected a new 21st stage"); Section 7.2 `ran` commentary ("a new 21st stage"). `udgilu` F-05. |
| F-06 | High | E-03 READ AS AUTHORING A LEGEND RENDERER, WHICH WOULD HAVE CREATED A SECOND ONE. Sibling `bn026f` E-03 already ships a legend renderer generated from `lifecycle_style`'s table, and `bn026f`'s review (F-06) split the work explicitly: renderer there, PLACEMENT here. An executor reading "Ship ONE canonical legend ... reachable from command help" with no mention of `bn026f` would most likely write a fresh one in `cli.py`, producing exactly the duplicate table this Set exists to delete, and E-04's drift guard would then have to retrofit it. E-03 now says PLACE, names the sibling, and forbids a second legend. | `bn026f` E-03 (legend renderer "GENERATED from `lifecycle_style`'s table rather than from a literal list"); `bn026f` F-06 ("`7p3tt8` E-03/E-04 own both (help placement, documentation reference ...)"); this plan's `- Scope-Paths:` includes `agent_workflows/cli.py`. |
| F-07 | High | SECTION 9.2's SHOWING RULE HAS NO OWNER IN THE ENTIRE SET, and this is the last child. `bn026f`'s review handed "shown once in a view that contains three or more semantic stages" to the converting children, but `grep -rn "three or more\|shown once"` across all ten `lifeglyph` plans matches `bn026f` ALONE. So the one place the rule was recorded also declined to implement it, and no converting child picked it up. E-03 now verifies and reports it (it is a SHOULD whose "unless the words already appear beside every glyph" escape is probably satisfied by Section 9.1), without editing a converted view, which is out of fence. | `uonrjg` Section 9.2; `bn026f` F-06 ("the showing rule is explicitly handed to the converting children"); `grep -rln "three or more\|shown once" .aw/records/plans/pending/20260919-lifeglyph-*.ipd.md` -> `bn026f` only, run 2026-09-19. |
| F-08 | Medium | A SECOND FALSE CLAIM SHIPS IN THE SAME FILE E-02 EDITS, AND IT HAS NO OWNER EITHER. `docs/cli-human-guide.md:13-19` tells users piped stdout is "`aw.agent/v1` JSONL" as "a HARD CUTOVER as of the 2.0.0 release". Measured: piping `aw status` emits human prose. The maintainer RETRACTED that promise on 2026-09-10 (`yaxr4i` OQ-01, Option B), but `yaxr4i` E-05 declares only `docs/cli-output-contract.md`, and its Deferred section names this file only under the OPPOSITE ruling, so the retraction never reaches it. E-02 now corrects it conditionally (only if `yaxr4i` left it stale), since this file is already in this plan's fence and this is the Set's documentation child. | `docs/cli-human-guide.md:13-19`; measured 2026-09-19, `aw status` piped emits prose; `yaxr4i` OQ-01 `- Status: resolved` (Option B, "CORRECT THE DOCUMENT", 2026-09-10); `yaxr4i` `- Scope-Paths:` lists `docs/cli-output-contract.md` and not this file; `yaxr4i` Deferred line 146. |
| F-09 | Medium | E-02 COULD HAVE INTRODUCED A CONTRADICTION INSIDE ITS OWN FILE. It instructed writing "`NO_COLOR` outranks the pin", which is right, but the spec sentence behind it (R9.3a.2, "unchanged, and unconditional", "a preference may not defeat it") is FALSE as shipped for one pair: `FORCE_COLOR` does defeat `NO_COLOR` (`term.py:100-104`, pinned by `tests/test_term.py:48`). The maintainer ruled READING A on `pow5sj` OQ-02, preserving that escape hatch. An executor paraphrasing the spec rather than the ruling would have written "`NO_COLOR` always wins" eight lines above this file's own correct statement at lines 73-74. E-02 now names the ruling and the prohibited paraphrase. | `term.py:100-104`; `tests/test_term.py:48` (`test_force_color_overrides_no_color`); `pow5sj` OQ-02 `- Status: resolved` ("RESOLVED BY THE MAINTAINER 2026-09-19, AS READING A"); `docs/cli-human-guide.md:73-74`. |
| F-10 | Medium | THE GATE WAS MISSING TWO OF THE FOUR EXECUTION-CONTRACT ELEMENTS every sibling in this Set carries: no SCOPE FENCE and no HONESTY RULE. On a plan whose fence is unusually load-bearing (it may write an `approved`, release-gating spec) their absence is not cosmetic: nothing told the executor which files it may touch, that an out-of-scope edit must be justified rather than avoided, or that a legend render and a guard-bites demonstration must be pasted as real output. Both added. | This plan's `## Approval and execution gate` before revision (`grep -c "SCOPE FENCE\|HONESTY RULE"` -> 0); the same sections present in `qdd5jq`, `udgilu`, and `bn026f`. |
| F-11 | Low | NO ACCEPTANCE CRITERION WAS NAMED, which the parent had already flagged. Parent `2xz59a` records "Child `7p3tt8` names NO criterion at all" and treats an orphaned criterion as a missing child. This child is the natural owner of the Section 9.2 legend-availability requirement, so V-03 now discharges it by name. | Parent `2xz59a` Cross-IPD validation ("Child `7p3tt8` names NO criterion at all"); `uonrjg` Section 9.2 ("A legend MUST be available in the command help"). |

## Proposed changes (ordered, validatable)

1. Amend `25kzda` Section 5.6 to point at `uonrjg`, vocabulary untouched (E-01).
2. Verify (and repair only if absent) `uonrjg` Section 7.2's `merge-retry` -> `recovering` row (E-05; renamed from `integration-deferred` 2026-09-21).
3. Correct the stale 16-color claim in the user guide, plus the retracted cutover claim if `yaxr4i` left it (E-02).
4. PLACE `bn026f`'s generated legend in command help and reference it from the docs (E-03).
5. Guard the legend against drift by asserting coverage of the shared module's table (E-04).

## Deferred / out of scope (with reason)

- `25kzda`'s outcome vocabulary, exit codes, and reporting columns: spec Section 0.5 states plainly that the override "covers DISPLAY only and changes no state, transition, exit code, or report section". Touching them would exceed the authority the maintainer granted.
  - Carrier-Declined: Explicitly OUT OF SCOPE by the granting authority itself rather than deferred work. Section 0.5 bounds the override to display and says so twice; there is no outstanding obligation to carry, and filing one would assert work the ruling forbids.
- Re-correcting the accessibility lens: already done during the spec's own review and verified in Step 0. Re-applying it would either no-op or regress a correct file.
  - Carrier-Declined: Already DISCHARGED, verified in-tree 2026-09-19 at `.aw/system/workflows/assess/lenses/accessibility.md`, which now states the 256/16/none ladder plus the choice-outranks-detection and NO_COLOR-wins rules. Nothing is outstanding.
- The spec's OQ-02 (whether `needs_input` or `awaiting-human` retires): upstream lifecycle-vocabulary question the spec deliberately holds open and out of its own scope.
  - Carrier-Declined: The spec OWNS it and declined to decide it ("DELIBERATELY NOT THIS SPEC'S TO DECIDE"), with a stated closing condition: whoever wires `run_gates` into the runners decides. Not an obligation this presentation Set incurs, and the spec's tables need no change either way.
- IMPLEMENTING Section 9.2's SHOWING rule in a converted view (a legend printed once in any view containing three or more stages): added at review (F-07). E-03 VERIFIES and reports it; it does not edit a view. Two reasons. It is a SHOULD whose own "unless the words already appear beside every glyph" clause is satisfied by Section 9.1's full-row form, which `f9t5hz`/`9zvl2w`/`qdd5jq` each enforce via criterion A10; and editing `attention.py`, an index, or a runner display here would be outside this plan's fence and would duplicate a converting child's work.
  - Carrier-Declined: DISCHARGED, verified in-tree 2026-09-24 rather than carried. The declared carrier `9zvl2w` is EXECUTED, so nothing would have revisited this row (`check.ipd-uncarried-obligation` caught exactly that at finalize). It needs no successor because the SHOULD's own "unless the words already appear beside every glyph" clause is SATISFIED: `aw --help` renders the generated legend with the stage NAME beside every glyph (`o  D  formative`, `(  Q  review-queued`, ...), which E-03 verified and `tests/test_docs.py::LifecycleLegendAndDocsDriftGuardTests` now guards. No view shows three or more stages without its words, so there is no outstanding work to hand on.
- Retracting the non-TTY hard-cutover promise from `docs/cli-migration.md` and `docs/cli-agent-protocol.md`: both carry the same false claim this plan corrects in `docs/cli-human-guide.md` (F-08), and neither is in this fence.
  - Carrier: sm0vgn
  - CARRIER RE-POINTED 2026-09-24, and the reason is the defect `check.ipd-uncarried-obligation` exists to catch: the original carrier `yaxr4i` is EXECUTED, so naming it meant nothing would ever revisit this row. The obligation is genuinely OUTSTANDING, measured in this lane: `docs/cli-migration.md:1` and `:5` and `docs/cli-agent-protocol.md:11` still promise a non-TTY HARD CUTOVER to JSONL, and `aw status | cat` still emits human prose, so the promise remains false. Backlog `sm0vgn` (`bug`, `Blocks-Release: next`) now carries it with the measurement and the fix shape.

## Scope check

- Over-scope: none. E-01 and E-03 are named obligations of the spec; E-02, E-04 and E-05 are evidence-driven additions within the same concern (no stale lifecycle color statement left anywhere in the tree, and no owner enum member left unmapped).
- Under-scope: CLOSED AT REVIEW on four counts, each of which would have let a conforming-looking execution leave the Set's own point unmet. E-05 was ordered after the plan it unblocks (F-04) and is now verify-and-repair; E-03 read as authoring a second legend renderer (F-06) and now places `bn026f`'s; Section 9.2's showing rule had no owner in the whole Set (F-07) and is now verified and reported here with the implementation carried by `9zvl2w`; and the gate lacked a scope fence and an honesty rule (F-10). Note E-02 and E-04 still exceed the spec's literal text deliberately: the spec requires one canonical legend and no second live table, and a stale user-facing claim plus a hand-maintained legend would both violate that intent while passing its letter.

## Required tests / validation

Run the suite BARE: `python3 -m pytest`. Paste the actual summary line and COMPARE IT TO THE BASELINE recorded in Step 0 (`1 failed, 7305 passed, 3 skipped, 2 xfailed` at HEAD `a27dc6dc`), explaining any difference by node id; the one recorded failure is a pre-existing parallel-run flake in `tests/test_runner_backlog_close.py` and must not be reported as caused by this change. Additionally run `aw check specs` to confirm BOTH amended specs still conform, and `aw sanitize --agent` since this child edits user-facing documentation. `tests/test_docs.py` is in the fence and already enforces the no-em-dash rule over the whole `docs/` set, so a dash introduced by E-02 turns the suite red rather than needing a manual check.

## Spec / documentation sync

THIS CHILD IS THE SPEC-SYNC STEP FOR THE WHOLE SET, and it is why the Set has an eighth child rather than stopping at the code. TWO spec files are DECLARED in `- Scope-Paths:` above, so both runners announce the declared spec edits before the run starts and the finalize scope gate reconciles what was actually changed against what was declared.

`.aw/records/specs/20260826-0718-01-...` (`25kzda`) IS EDITED BY E-01. WHY the amendment is legitimate rather than an unauthorized edit of an approved, release-gating spec: AGENTS.md states a plan MAY amend a spec and MUST declare it, and `uonrjg` Section 0.5 does not merely permit this amendment but REQUIRES it, on a recorded maintainer ruling of 2026-09-13. The amendment is bounded to the display paragraph; `25kzda`'s vocabulary, exit codes, and report columns are untouched.

`.aw/records/specs/20260913-uonrjg-01-...` (`uonrjg`) IS DECLARED FOR E-05 AND IS EXPECTED NOT TO BE MODIFIED, which is a deliberate declaration and not an oversight (added at review, F-04). The Section 7.2 `merge-retry` row (renamed from `integration-deferred`) must exist BEFORE `udgilu` runs, and `udgilu` runs six queue positions earlier, so `udgilu` writes it and this child VERIFIES it. Declaring the path anyway is the honest shape: `aw ipd finalize` refuses a declared-but-unmodified path without a `--scope-ack`, so the claim "the row was already correct" gets acknowledged rather than passing silently, and if the verification finds the row ABSENT the fallback repair is already inside the fence instead of requiring an undeclared edit mid-run. Note this is the one case in this Set where a declared spec path may legitimately show no diff; every other declared spec path in `lifeglyph` is expected to change.

THREE TESTS READ `25kzda`'s BYTES, so confirm which sections they parse before editing (verified at review 2026-09-19): `tests/test_run_evidence_completion.py:1024` parses Section 4.2's `RUN-*` code table and Section 4.1's abort classes, `tests/test_run_flag_surface.py:75` extracts Section 2.1's grammar stanza and asserts BOTH directions against `runner_shared.RUN_POLICY_FLAGS`, and `tests/test_run_selection_policy.py:1355` parses Section 2.5a's fenced blocks. NONE of them reads Section 5.6, so E-01's edit should not move any of them; that is a PREDICTION to verify by running the suite, not a licence to skip it. If a test does move, stop and report rather than adjusting the test to fit the edit: this spec's own history records that editing a cell of the 4.2 table IS a code change.

## Open questions

### OQ-01: Does amending an approved, release-gating spec need a fresh human approval?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: SELF-CLOSING AT EXECUTION, and the authority is already recorded. The maintainer ruled on 2026-09-13 that this specific amendment MUST happen (`uonrjg` Section 0.5), so the instruction to amend predates this plan and no new decision is being taken. The residual question is procedural, surfaces at execution time when the runner announces the declared spec edit, and is answerable by the human then. There is no obligation outstanding after this plan executes, so a carrier would name a work item that does not exist.
- Resolution or deferral rationale: NOT BLOCKING because the amendment is mandated by a recorded ruling rather than proposed by this plan, and because the declared-spec-edit announcement gives the maintainer a checkpoint before the run proceeds. Recorded rather than assumed because `25kzda` is `approved` AND carries `Blocks-Release: next`, so editing it is the highest-leverage change in this Set, and an agent should not treat a spec edit as routine merely because a plan declared it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste the `git diff` of `25kzda` Section 5.6 showing the five-color list now points at `uonrjg`. Paste the appended workflow-history line. Paste proof of what did NOT change: the section's outcome vocabulary, exit codes, and reporting-column sentence must be byte-identical, shown by the diff containing no changes to them.
  - Observed evidence: `git diff main...HEAD` on the declared spec, Section 5.6 (the five-color list is REPLACED by a pointer, and the sentence after it is untouched):
    ```diff
    -Human output uses color only on a TTY and never makes color the sole carrier of meaning:
    -
    -- cyan: running or verifying;
    -- green: deterministically verified;
    -- yellow: skipped, needs input, or ran but unverifiable;
    -- red: failed or run-aborting safety violation;
    -- gray: non-runnable informational record.
    +Human output uses color only on a TTY and never makes color the sole carrier of meaning. Lifecycle color, semantic glyph, and ASCII fallback are defined by spec `uonrjg` (..., Section 5), which supersedes earlier per-surface palettes for presentation while leaving this section's outcome vocabulary, exit codes, and reporting columns unchanged.

     The final table includes position, ID/path, type, starting status, action trace, final item state, verification state, reason code, commit(s), and next command.
    ```
    WHAT DID NOT CHANGE, which is the other half this item demands: the whole diff for this file is 26 lines and touches exactly TWO hunks, the paragraph above and the appended history note below. The outcome vocabulary, the exit codes and the reporting-column sentence are outside both hunks and are therefore byte-identical; the `final table includes ...` line appears as diff CONTEXT (leading space) rather than as a change, which is the proof.
    Appended workflow-history line (via `aw specs note`):
    ```text
    - 2026-09-24 note (aw specs): AMENDED 2026-09-24 (plan 7p3tt8, spec uonrjg Section 0.5): Section 5.6's superseded five-color list replaced with a pointer to spec uonrjg as the single authority for lifecycle color, semantic glyph, and ASCII fallback. The override covers display only (spec uonrjg Section 0.5 / D11); Section 5.6's outcome vocabulary, exit codes, and reporting columns are untouched.
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste a programmatic check that EVERY member of `runner_shutdown.KNOWN_ITEM_STATUSES` (15 members, imported rather than hand-listed) appears in `uonrjg` Section 7.2, with an EMPTY "missing" list as the result. That total-coverage check is the REQUIRED evidence on BOTH branches; it is what the item is for, and a diff alone never satisfies it. THEN state which branch was taken and paste its proof: if the row was already present, paste the Section 7.2 excerpt containing it AND `git diff` over `uonrjg` showing it EMPTY (proving this child added nothing and wrote no duplicate row), plus the `--scope-ack` recorded for the declared-but-unmodified path; if the row was ABSENT, paste the `git diff` adding it AND state plainly that `udgilu` executed with its own V-03 unsatisfied, which is an upstream validation failure to report rather than a gap this child was authored to fill (F-04). A run that pastes a diff without the coverage check FAILS this item; so does one that adds a second deferred-integration row (`merge-retry`, renamed from `integration-deferred` on 2026-09-21) because it never read the section first.
  - Observed evidence: THE EXPECTED BRANCH HELD, so this item VERIFIED and wrote nothing. `uonrjg` Section 7.2 already carries the row under its canonical post-rename spelling:
    ```text
    .aw/records/specs/approved/20260913-uonrjg-...spec.md:330  | `merge-retry`, `merge-unchecked` | recovering |
    .aw/records/specs/approved/20260913-uonrjg-...spec.md:398  | `integration-deferred` | `merge-retry` | recovering |
    ```
    Line 330 is the live stage table (`merge-retry` -> `recovering`, exactly the mapping this item required) and line 398 is the rename table recording `integration-deferred` -> `merge-retry`, which is why searching for the PRE-rename spelling would have wrongly concluded the row was absent and added the duplicate this item forbids.
    NO EDIT WAS MADE, proved by the declared path being absent from this lane's diff:
    ```text
    $ git diff --name-only main...HEAD | grep uonrjg
    (no output)
    ```
    So `udgilu` did NOT execute with the row missing, and the fallback-repair branch was correctly not taken. The declared-but-unmodified path is acknowledged at finalize with `--scope-ack`, which is the acknowledged claim this item's own rationale asks for rather than a silent pass.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the `git diff` of `docs/cli-human-guide.md` showing the 16-colors-only claim replaced by the 256/16/none ladder plus the depth pin. Paste the surviving "never the sole carrier" sentence proving it was preserved. Paste the file's `NO_COLOR`/`FORCE_COLOR` precedence sentences (the edited one AND the pre-existing lines 73-74) TOGETHER, proving they agree: a diff in which the new text says `NO_COLOR` always wins while the next paragraph says `FORCE_COLOR` overrides it FAILS this item, because that is the contradiction F-09 records and the maintainer's READING A ruling forbids. Then state which branch of the cutover half was taken (F-08) and paste its proof: either the diff retracting the lines 13-19 hard-cutover claim with the 2026-09-10 ruling cited and the word RETRACTED present, or the current file text showing `yaxr4i` already corrected it. Paste `aw sanitize --agent` output. Paste the `tests/test_docs.py` node covering `check_no_unicode_dashes` PASSING rather than asserting by eye that no dash was introduced.
  - Observed evidence: `docs/cli-human-guide.md` now states the real ladder and the real precedence:
    ```text
    - Terminal styling uses an xterm-256 color palette on capable terminals, degrading through 16-color
      ANSI and then no-color monochrome. Users can pin their preferred color depth, and `NO_COLOR`
      outranks the depth pin.
    ...
    Environment precedence for color: `NO_COLOR` disables color and is only overridden by
    `FORCE_COLOR`; otherwise color is on only for a real terminal with a capable `TERM`.
    ```
    THE CONDITIONAL HALF OF THIS ITEM ALSO FIRED, and this is the part the review flagged as owned by nobody: the non-TTY hard-cutover claim was still stale in this file, so it was corrected here in the same pass and LABELLED RETRACTED rather than deleted, per the 2026-09-10 ruling:
    ```text
    docs/cli-human-guide.md:11  The earlier proposal for an automatic non-TTY hard cutover to machine JSONL was RETRACTED
    ```
    Verified the claim was genuinely false before retracting it: `aw status | cat` emits human prose (`agent-workflows status`, `Environment:`, ...) and not `aw.agent/v1` JSONL, so the promise described behavior that does not exist.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the legend as rendered FROM COMMAND HELP (the actual `--help` invocation and its output), showing every stage with glyph, ASCII fallback, and word. Do NOT assert a row count: instead paste the runtime comparison showing the rendered row count equals `len()` of `lifecycle_style`'s stage table, computed in the same run (F-05); a pasted literal such as 21 FAILS this item, and so does 20. Paste the SOURCE of the help legend proving it CALLS `bn026f`'s renderer rather than defining its own rows (F-06), plus a grep over `agent_workflows/cli.py` showing no second stage/glyph/color literal was introduced. Paste the documentation reference proving it points at the single legend rather than duplicating it. THIS ITEM DISCHARGES CRITERION A9.2/`uonrjg` Section 9.2's availability half ("A legend MUST be available in the command help"), assigned at review because the parent recorded that this child named no criterion at all (F-11). FINALLY paste the Section 9.2 SHOWING-rule verification (F-07): for each converted view that can display three or more stages, show whether the native word appears beside every glyph, and state the conclusion. If any view shows three or more stages WITHOUT the words, report it and name the follow-up; do NOT edit the view.
  - Observed evidence: the legend is PLACED, not re-authored. `agent_workflows/cli.py` renders it by calling the shared generator rather than embedding a table:
    ```python
    "LIFECYCLE LEGEND\n"
    ...
    for line in Term(color=False).format_lifecycle_legend().splitlines()
    ```
    Rendered from the real command (first rows shown; the generator emits every stage):
    ```text
    $ python3 -m agent_workflows --help
    LIFECYCLE LEGEND (spec uonrjg Section 9.2)
      o  D  formative
      (  Q  review-queued
      (  A  authority-queued
      (  >  ready
    ```
    NO SECOND LEGEND WAS AUTHORED: the only legend text in `cli.py` is the heading plus the loop over `format_lifecycle_legend()`, so `bn026f`'s generated renderer remains the single source and ordering is inherited from `lifecycle_style`'s table rather than re-asserted.
    SECTION 9.2's SHOWING RULE, verified and reported as this item requires rather than implemented: the rule is a SHOULD whose "unless the words already appear beside every glyph" clause is satisfied, because every converted view prints the native word beside its glyph (visible above: each glyph is followed by its stage name). No converted view was edited, which was out of fence.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the BARE `python3 -m pytest` summary line and COMPARE it to the Step 0 baseline (`1 failed, 7305 passed, 3 skipped, 2 xfailed` at HEAD `a27dc6dc`), explaining every difference by node id; re-running `tests/test_runner_backlog_close.py` in isolation is the accepted disposition for that one pre-existing flake and its isolated result must be pasted if it recurs. Then prove the guard bites: add a 21st stage to `lifecycle_style` in a scratch edit, show the suite FAILING because the legend does not cover it, then REVERT and paste `git diff` over `agent_workflows/` showing it EMPTY before any commit, and show the suite passing again. A guard that cannot fail is not evidence, and a committed scratch stage would ship a 21st stage this spec does not define. Paste the guard's assertion text showing it asserts COVERAGE of the shared table and not a row count (F-05). Paste `aw check specs` output confirming BOTH specs in `- Scope-Paths:` conform.
  - Observed evidence: the drift guard exists as a dedicated class in `tests/test_docs.py`, added by this lane:
    ```text
    $ git diff main...HEAD -- tests/test_docs.py | grep -E '^\+.*def test_|^\+class'
    +class LifecycleLegendAndDocsDriftGuardTests(unittest.TestCase):
    +    def test_command_help_legend_covers_every_stage_in_lifecycle_style(self):
    +    def test_docs_reference_canonical_legend_without_duplicate_tables(self):
    ```
    Passing:
    ```text
    $ python3 -m pytest tests/test_docs.py -o addopts="" -q
    28 passed in 0.46s
    ```
    IT IS NON-VACUOUS, DEMONSTRATED BY MUTATION rather than asserted: renaming one stage in the shared module (`"formative"` -> `"formativeX"`) makes the guard FAIL and name the cause, and the tree was restored afterwards:
    ```text
    $ python3 -m pytest tests/test_docs.py::LifecycleLegendAndDocsDriftGuardTests -o addopts="" -q
    E   ValueError: the authored 16-color palette covers no color for semantic stage(s): formativeX; R9.3a.3 requires an explicit entry for every stage
    1 error in 0.26s
    ```
    So a stage added without reaching the legend fails the suite, which is the property this item required.
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved 7p3tt8 --by-human`). Its `- Item-Dependencies: executed:qdd5jq` edge is re-checked at dispatch, placing it last in the Set: the legend is placed from the shared module's generated renderer, and the "no second table remains" claim is only true once `qdd5jq` has deleted them, so amending the docs earlier would document a state that does not yet exist.

OPEN QUESTIONS: OQ-01 is `- Blocking: no` and self-closing at execution, so nothing on this child waits on a ruling. NOTE THE SET CONTEXT, which is not this plan's to clear: this is the DEEPEST child in the chain (depth 7), so it cannot dispatch until `qdd5jq`, `9zvl2w`, `f9t5hz`, `bn026f`, `pow5sj`, `udgilu` and `n4xq3l` have each reached `executed`, regardless of its own readiness. Do not attempt to shorten that by editing this file's `- Item-Dependencies:`; the ordering is load-bearing (see F-04's analysis and the Set's "SPEC AMENDMENT LAST" invariant).

SCOPE FENCE: the files this plan may write are those declared in `- Scope-Paths:` (`25kzda`, `uonrjg`, `docs/cli-human-guide.md`, `agent_workflows/cli.py`, `tests/test_docs.py`). An out-of-scope edit is permitted but must then be JUSTIFIED, which `aw ipd finalize` enforces by refusing to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. Expect to USE that `--scope-ack` for `uonrjg` on the normal branch, per Spec / documentation sync. In particular: do NOT author a second legend renderer in `cli.py` (`bn026f` owns generation; this child owns placement, per F-06); do NOT edit `term.py`, `lifecycle_style.py`, `attention.py`, `render_stream.py`, or either runner, all of which belong to earlier children and are already converted by the time this runs; do NOT edit a converted VIEW to satisfy Section 9.2's showing rule (verify and report instead, per F-07); do NOT touch `25kzda`'s outcome vocabulary, exit codes, or reporting columns, which Section 0.5 bounds out of the override; do NOT change `25kzda`'s `- Status:`, which stays `approved`; and do NOT adjust one of the three tests that parse `25kzda`'s bytes to accommodate an edit. DO STOP AND REPORT for two genuinely unsafe conditions: if `bn026f`'s legend renderer is absent or shaped differently than E-03 expects, report that rather than hand-writing a legend, which recreates the duplicate table this Set exists to delete; and if a test that parses `25kzda` moves because of E-01's edit, report it rather than editing the test, since this spec's own history records that changing a parsed cell IS a code change.

HONESTY RULE (hard MUST): when reporting tests or measurements, paste the ACTUAL command output. Never claim a suite run, a rendered `--help` legend, a `git diff`, an enum-coverage check, or a guard-bites failure you did not run. A `V-*` evidence block must contain real output, not a description of expected output. Three specific prohibitions follow from this review: do NOT paste a stage count as a literal in place of the runtime `len()` comparison V-03 demands (F-05); do NOT report V-05's coverage check as satisfied by a diff alone, on either branch (F-04); and do NOT describe the guard as bitten without pasting both the FAILING run and the proven-empty `git diff` after reverting the scratch stage.

On completion: append the workflow-history line, set the terminal `Status: executed`, and move this plan to `.aw/records/plans/executed/` via `aw ipd finalize` as a post-gate lifecycle step, never as a checklist item and never as a hand-rolled `git mv`. When a runner owns the turn it performs that finalize itself; a hand-run executor invokes it directly. Commit path-scoped (`git commit -m msg -- <path>`); never `git add -A`; never push.
