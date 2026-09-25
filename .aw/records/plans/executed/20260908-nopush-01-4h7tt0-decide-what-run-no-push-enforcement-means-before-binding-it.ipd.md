# IPD: Decide what RUN-NO-PUSH enforcement means before binding it, or keep it honestly unbound

- Date: 2026-09-08
- Kind: child
- Concern: `RUN-NO-PUSH` is the last remaining UNBOUND-UNBUILT finding code in spec `25kzda` 4.2: a name with no predicate behind it. It requires host push-denial ENFORCEMENT, and nothing in this repository implements one. The capability it would read, `supports_deny_push`, defaults `False` (`host_sandbox_profile.py:204`) and is "DECLARED AND NEVER PROBED, with the reason recorded in `probe_notes`" (`:88-95`), because it names host enforcement that "does not exist in this repository, so there is nothing to attempt". It therefore fails closed today, which is CORRECT and is not the defect. The defect is that the guarantee is owed and nothing records the design decision needed to either honor it or retire it.
  THE OBVIOUS IMPLEMENTATION IS EXPLICITLY FORBIDDEN, and that prohibition is the reason this is a spec-first plan rather than a coding plan. The same paragraph states: "Inferring support from the presence of the driver-side `git_commit_helper.offer_commit` helper is FORBIDDEN: a helper the driver chooses to call is not a boundary an agent cannot evade, and reporting it as one is the same fail-OPEN inference the sandbox probes above exist to refuse." So a plan may not bind `RUN-NO-PUSH` by detecting a helper, a hook, a config flag, or any other in-repo artifact's presence. Either a real boundary exists that an agent cannot evade, or the code must stay honestly unbound.
  THE BACKLOG ITEM ALSO SAYS SO, and its warning is inherited here verbatim in substance: `RUN-NO-PUSH` "is a security-boundary design of `1o4eif` magnitude and should not be picked up casually; treat it as needing a spec-level decision first, and do NOT let a future plan bind either code to a presence-based inference, which is the fail-open pattern already rejected once for the host capabilities."
  ITS SIBLING HALF IS ALREADY DEAD, which is why this plan covers one code and not two. The item was filed for `RUN-BASELINE-OWNERSHIP` and `RUN-NO-PUSH` together; the former is now BOUND, and the code says so: "`RUN-BASELINE-OWNERSHIP` is now BOUND, not UNBOUND-UNBUILT: the per-path lease overlap check F3 said nobody had built ships as `worktree_lease.LeaseTable.claim` (`m2wwns`), and `dirty_within` decides the pre-existing-dirty-path half" (`run_evidence.py:1221-1223`). Verified at HEAD: `LeaseTable.claim` exists (`worktree_lease.py:836`) and `run_evidence.dirty_within` exists (consumed at `ipd_lifecycle.py:892-895`). Do not build a second lease-overlap check.
- Scope: Implement the SPEC-LEVEL DECISION `RUN-NO-PUSH` needed, which the maintainer has now MADE: outcome (c), RETIRE the code from 4.2 with the reason recorded (OQ-01, commit `b23d447d`). Three outcomes were legitimate when this was authored (build a real boundary; narrow the guarantee; retire the code); two are now closed, so this plan executes retirement rather than deciding. RETIREMENT IS NARROWER THAN IT SOUNDS AND WIDER THAN ONE ROW: it withdraws the 4.2 reporting CODE and the promise of proved push denial, it necessarily amends the enforced code-count invariant and its tests (F-8), and it must reconcile the five other spec sites that still promise no-push (F-10) - while deliberately PRESERVING spec 5.2's `supports_deny_push` capability, whose action-class requirements keep failing closed (F-9). This plan writes NO fail-open binding.
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, agent_workflows/run_evidence.py, agent_workflows/host_sandbox_profile.py, tests/test_run_evidence_completion.py, tests/test_run_no_push_boundary.py
- Item-Dependencies: none
- Status: executed
- Set: nopush
- Order: 1
- Highest E allocated: 05
- Readiness: go-pending-approval
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 4h7tt0
- From-Backlog: d07nz2
- Blocks-Release: next

## Workflow history
- 2026-09-22 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: 4h7tt0 verified (set nopush, attempt 1). [Scope reconciliation - in-scope-unmodified agent_workflows/host_sandbox_profile.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-10 readiness re-check (opencode its_direct/pt3-claude-opus-5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: `plan_readiness.has_unresolved_blocking_question` -> False; `review_findings.subject_gating_blocks` -> empty; `plan_readiness.newest_verdict` polarity -> neutral (not negative). Specifically, its blocking OQ-02 was answered on 2026-09-10 and the finding it escalated (PR-002) is now closed in review round 2, with the removal carried by backlog `aagh7v`. Performed at HEAD `84111de2` at the maintainer's explicit instruction of 2026-09-10, who was shown that 10 of 15 `no-go` plans were held by stale bookkeeping and chose to have them hand-fixed with evidence recorded rather than re-reviewed. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-09-09 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review complete: REVIEWED - OPEN QUESTIONS; PR-001..PR-008; PR-002 escalated as blocking OQ-02 (irreversible decision, maintainer's to make); Readiness no-go pending that answer

- 2026-09-09 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008. Reviewed at HEAD `c0a9de73`; `aw ipd lint` conforming at `--phase author` before and `--phase review-finalize` after. SELF-REVIEW (same agent/model authored the plan), so the method was to EXECUTE the retirement in a scratch copy rather than re-read the plan, which is what produced the blocker. (1) BLOCKER PR-001: THE PLAN'S CENTRAL INSTRUCTION, "amend nothing else", WOULD HAVE FAILED THE SUITE AND SHIPPED A SELF-INVALIDATING TABLE. Simulated outcome (c) end to end (row removed from spec AND code) and measured `5 failed, 5915 passed` against a `1 failed, 5919 passed` baseline: FOUR new failures, all hardcoded-13 (`test_spec_defines_exactly_thirteen_run_codes`, `test_table_enumerates_exactly_the_specs_thirteen_codes`, `test_table_self_validation_passes`, `test_measured_binding_partition_is_recorded`). Worse than the tests, `validate_finding_table` hard-fails `len(...) != 13` with `RC-COUNT`, so a retirement done as written makes the SHIPPED table report itself INVALID at runtime. E-03/E-04 rewritten to own the count in all four enforcing places plus the spec's own "all 13" sentence; `tests/test_run_evidence_completion.py` added to `Scope-Paths` because the original fence made this impossible to do legally. (2) HIGH PR-002: THE 4.2 CODE AND THE 5.2 CAPABILITY ARE DIFFERENT ARTIFACTS AND THE PLAN NEVER SAID SO, so an executor "finishing the retirement" could delete a LIVE refusal: `CAP_DENY_PUSH` is required by the `review`, `mutate` and `contractless-prompt` action classes, which still fail closed after the code is gone. E-04 now forbids touching it and V-04 requires the five pinning assertions to pass with those test files UNEDITED. (3) HIGH PR-003: retiring one row leaves FIVE other spec sites still promising no-push (`:848`, `:864`, `:1115`, `:1129`, `:1154`), so the spec would contradict itself; added E-05/V-05 to give each a verdict, and noted `:1154`'s claim that the `oc` descriptor "positively proves ... no-push enforcement" is wrong INDEPENDENTLY of this plan given `supports_deny_push` is hardcoded `False`. (4) HIGH PR-004: the GATE said OQ-01 was `Blocking: yes` and unanswered while the question itself reads `Blocking: no`/`resolved` forty lines above, so the plan told the executor to await a decision it had already recorded. (5) MEDIUM PR-005: the plan cites `mjx7ne` OQ-03 as precedent for retirement, but that maintainer decision was "KEEP ALL THREE capabilities, honestly labelled" - it authorizes the declared-`False` shape E-04 now preserves, and is not a precedent for deleting a spec row; the authority is OQ-01's own decision. Also corrected: there is no "byte-equality test" (the pinning is four per-field comparisons, F-6), and V-04's instruction to disregard "~14 `test_run_viewer.py` failures" is stale and dangerous now that the file is `75 passed` (F-14). I VERIFIED THE ATTESTATION rather than trusting it, since a plan asserting its own maintainer approval is the forgery shape this repo guards: commit `b23d447d` is maintainer-authored and states the decision and reasoning independently of the plan body, so OQ-01 is genuine and outcome (c) stands. CONFIRMED SOUND: F-1 (`RUN-BASELINE-OWNERSHIP` bound; `LeaseTable.claim` and `dirty_within` both located), F-2 and the anti-inference prohibition (verbatim at `host_sandbox_profile.py:88-95`), F-4 (`supports_deny_push` `False`, declared-not-probed, fails closed), F-7 (sole UNBOUND-UNBUILT), the spec's `approved` status, and the retirement's core argument that this removes a promise rather than a protection. Added F-8..F-15 and four Step 0 conventions, including that the orphaned "Push attempt" abort class must be LEFT alone. `Highest E allocated` 04 -> 05. READINESS `no-go`, AND THE REASON IS PR-002 RATHER THAN ANY UNFIXED FINDING: every finding is FIXED, but PR-002's resolution is an IRREVERSIBLE decision (review record D-2, `Reversible: no`), which this repository's rules say a reviewer may not make on its own authority. It is therefore ESCALATED as new OQ-02 (`Blocking: yes`, owner maintainer), asking whether retiring the 4.2 code also authorizes removing spec 5.2's `supports_deny_push` capability. `aw ipd lint` now refuses the plan with `IPD-Q501` at every checkpoint, which is the intended fail-closed stop; the recommendation is PRESERVE and E-04/V-04 are already written that way, so a PRESERVE answer unblocks with no further edits. Verdict `REVIEWED - OPEN QUESTIONS`.
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `d07nz2`, HALVED. The item covers two finding codes; `RUN-BASELINE-OWNERSHIP` was BUILT after the item was written and is now BOUND (verified at HEAD by symbol: `worktree_lease.LeaseTable.claim`, `run_evidence.dirty_within`), so graduating the item as written would have commissioned a second lease-overlap check. Only `RUN-NO-PUSH` survives. Authored as a SPEC-FIRST plan because the item itself demands a spec-level decision first and forbids presence-based inference, and because the maintainer already ruled on the parallel case (`mjx7ne` OQ-03) that the capability may be declared `False` with a `probe_notes` entry rather than probed.

## Goal

Replace an owed-but-undesigned guarantee with a recorded withdrawal: spec `25kzda` stops promising proved push denial in its 4.2 reporting vocabulary, states plainly why, and points at where a real boundary would belong, WITHOUT weakening anything that currently refuses. The capability-level refusal (`supports_deny_push` `False`, gating three action classes) is preserved deliberately, so this removes a promise and not a protection.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish what is actually true, and what a boundary would have to be

- [x] E-01 RECORD THE CURRENT STATE BY SYMBOL, and confirm the sibling half is dead before touching anything. Establish and write down: that `RUN-NO-PUSH` is the only remaining UNBOUND-UNBUILT code in 4.2 (the code's own tally is "10 BOUND, 2 UNBOUND-BY-DEPENDENCY, 1 UNBOUND-UNBUILT", `run_evidence.py:1231`); that `supports_deny_push` defaults `False` and is never probed with its reason in `probe_notes`; and that `RUN-BASELINE-OWNERSHIP` is BOUND.
  IF THE TALLY HAS MOVED, SAY SO AND RE-SCOPE. Codes have been re-bound twice already as their dependencies executed, which is exactly why this item's own sibling half died. Trust the tree, not this plan's Concern.
  - Depends on: none
  - Expected outcome: a written, symbol-cited statement of which codes are bound, that `RUN-NO-PUSH` alone is unbound-unbuilt, and that no second lease-overlap check is needed.
  - Execution state: performed
  - Execution note: Measured at HEAD `2815aa56` BEFORE any edit. The tally HAD NOT MOVED since authoring: 13 codes, `{'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2, 'UNBOUND-UNBUILT': 1}`, with `unbuilt == ['RUN-NO-PUSH']` and `by-dependency == ['RUN-COMMIT-CONTENTS', 'RUN-COMMIT-GATEWAY']`, matching `run_evidence.py`'s own comment. So no re-scope was needed. `supports_deny_push` default `False` confirmed from `HostSandboxCapabilities()` with its `probe_notes` reason in `_DECLARED_UNENFORCED[CAP_DENY_PUSH]`. `RUN-BASELINE-OWNERSHIP` confirmed BOUND by locating both symbols: `worktree_lease.LeaseTable.claim` (`worktree_lease.py:921`) and `run_evidence.dirty_within` (`run_evidence.py:223`). NO SECOND LEASE-OVERLAP CHECK WAS BUILT.

- [x] E-02 RECORD THE CANDIDATE ENFORCEMENT MECHANISMS AND EACH ONE'S CONCRETE EVASION, as the DURABLE JUSTIFICATION for the retirement rather than as an open analysis. OQ-01 is already answered, so this item's purpose has shifted and the plan must not pretend otherwise: it no longer informs a pending choice, it preserves WHY building was declined so a future reader can reopen the question with the analysis in hand instead of redoing it. The spec amendment (E-03) cites this, which is what makes the withdrawal auditable rather than a bare assertion.
  AT MINIMUM COVER: an OS/sandbox-level network or exec restriction; a git-level mechanism (a `pre-push` hook, a remote-less clone, a push-denying credential); a host-runtime restriction the adapter can attest; and the null option.
  FOR EACH, STATE THE EVASION. The prohibition this plan inherits is not "do not use a helper", it is "a boundary an agent cannot evade". A `pre-push` hook can be bypassed with `--no-verify`; a helper the driver chooses to call can be sidestepped by calling git directly; a config flag can be rewritten by the agent it constrains. Name the evasion for each candidate or the analysis is worthless. The maintainer's own rationale in `b23d447d` names three of these evasions, so the table must at least reproduce and cite them, not contradict them.
  STILL DO NOT SELECT A MECHANISM. Not because the choice is pending, but because the choice was made: outcome (c). An item that ended by recommending a mechanism would be re-litigating a settled maintainer decision.
  - Depends on: E-01
  - Expected outcome: a candidate table with, per mechanism, what it proves, what it cannot prove, and its concrete evasion, consistent with `b23d447d`'s recorded reasoning; no mechanism selected; the table is durable justification for retirement.
  - Execution state: performed
  - Execution note: The candidate table is recorded below under "Candidate enforcement mechanisms (E-02)", covering all four required families (OS/sandbox, git-level in three variants, host-runtime attestation, and the null option) with a named concrete evasion for every row. NO MECHANISM WAS SELECTED. Cross-checked against `b23d447d`, whose message names three evasions (`pre-push` hook falls to `--no-verify`; driver-side helper falls to invoking git directly; config value falls to the agent rewriting it); the table reproduces all three and contradicts none. The summary of the table is carried into the spec amendment (E-03), which is what makes the withdrawal auditable.

### Task group 2: implement only what the decision authorizes

- [x] E-03 AMEND SPEC `25kzda` 4.2 TO REMOVE THE `RUN-NO-PUSH` ROW (OQ-01 outcome (c), maintainer-decided), and amend nothing else in 4.2. The row is RETIRED with the reason recorded: the spec stops promising something this repository cannot deliver.
  THE SPEC FILE IS DECLARED IN `- Scope-Paths:` DELIBERATELY, so the amendment is announced before the run starts and reconciled by the finalize scope gate (`AGENTS.md:82`). Say WHY in the spec-sync section, since a 4.2 edit changes what every run is checked against.
  RETIREMENT IS NOT A ONE-ROW EDIT, AND THE PLAN'S ORIGINAL "AMEND NOTHING ELSE" WOULD HAVE FAILED THE SUITE. MEASURED, not inferred: I removed the row from the spec table AND the matching `RunFindingCode` from `run_evidence.py` in a scratch copy and ran the suite. Result `5 failed, 5915 passed` against a baseline of `1 failed, 5919 passed`, i.e. FOUR new failures, every one of them a HARDCODED THIRTEEN that retirement necessarily falsifies:
    * `tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_spec_defines_exactly_thirteen_run_codes` (asserts the SPEC parses 13 rows, `:1082-1088`)
    * `::test_table_enumerates_exactly_the_specs_thirteen_codes` (asserts `len(RUN_FINDING_CODES) == 13`, `:1090-1095`)
    * `::test_table_self_validation_passes` (fails because `validate_finding_table` itself hard-fails `len(...) != 13` with `RC-COUNT`, `run_evidence.py:1649-1656`)
    * `::test_measured_binding_partition_is_recorded` (asserts `unbuilt == ["RUN-NO-PUSH"]`, `:1293-1301`)
  SO THE COUNT IS PART OF THE CONTRACT AND MUST BE AMENDED DELIBERATELY, in all four places plus the prose that states it: `run_evidence.validate_finding_table`'s `!= 13` invariant, the three tests above, and the spec's own sentence "`run_evidence.RUN_FINDING_CODES` carries all 13" (spec `:36`). Nine further code comments say "13 codes" (`run_evidence.py:1108`, `:1116`, `:1175`, `:1212`, `:1580`, `:1604`, `:1635`); update them or the code documents a table it no longer has. UPDATING THESE IS NOT SCOPE CREEP: a retirement that leaves a `13` invariant behind does not merely fail a test, it makes `validate_finding_table` report the shipped table as INVALID at runtime.
  - Depends on: E-02
  - Expected outcome: the `RUN-NO-PUSH` row removed from 4.2 with the reason stated; the spec's own "all 13" sentence corrected; no OTHER 4.2 row's text altered.
  - Execution state: performed
  - Execution note: The 4.2 row is removed (one deleted table line; the table now has 12 rows). The REASON is recorded in two new 4.2 prose paragraphs above the table: the withdrawal with its date and commit `b23d447d`, the promise-not-protection distinction, the preserved 5.2 capability, the per-mechanism evasions from E-02, the pointer to where a real boundary would belong (`x03wgn` OS-level enforcement), and the surviving anti-inference rule. The preamble's "carries all 13" sentence is corrected to 12 with the new partition. NO OTHER 4.2 ROW'S TEXT WAS ALTERED, proven by the four field-comparison tests passing over the remaining 12 codes (V-03). Also added, because retirement made the count contractual: a note that `validate_finding_table` hard-fails `!= 12`.

- [x] E-04 MAKE THE CODE AND THE TESTS MATCH THE AMENDED SPEC, AND PROVE NO FAIL-OPEN BINDING WAS INTRODUCED. Remove the `RUN-NO-PUSH` `RunFindingCode` from `RUN_FINDING_CODES`, drop the `13` invariant to `12` in `validate_finding_table`, and update the four measured test assertions E-03 enumerates (the two thirteen-counts, the self-validation case, and the `unbuilt == ["RUN-NO-PUSH"]` partition, which becomes an EMPTY unbuilt list). Also update the module's bound/unbound tally comment (`run_evidence.py:1231`, currently "10 BOUND, 2 UNBOUND-BY-DEPENDENCY, 1 UNBOUND-UNBUILT") to the post-retirement partition, since that comment is the tally E-01 reads.
  LEAVE `supports_deny_push` EXACTLY AS IT IS: `False`, DECLARED-NOT-PROBED, with its existing `probe_notes` reason (`host_sandbox_profile.py:204`, note text at `:549-554`). DO NOT DELETE THE CAPABILITY, and this is the single most important boundary in this item. The 4.2 FINDING CODE and the 5.2 CAPABILITY are different artifacts with different consumers: `CAP_DENY_PUSH` is a spec 5.2 requirement listed in the action-requirement map for `review`, `mutate` and `contractless-prompt` (`host_sandbox_profile.py:1324`, `:1345`, `:1366`), so it still makes those action classes fail closed at preflight AFTER the finding code is gone. Retiring the reporting code must not silently remove the refusal. `tests/test_host_capability_extension.py` pins that behavior in five places (`:78`, `:190`, `:255-257`, `:333`, `:473`, the last asserting `missing == {CAP_COMMIT_GATEWAY, CAP_DENY_PUSH}`) and `tests/test_host_sandbox_profile.py:54` pins the field's conservative default; ALL of those must still pass unchanged. If any of them needs editing, STOP: that means the change reached past the finding code into the capability gate, which OQ-01 did not authorize.
  THE ANTI-FAIL-OPEN TEST IS STILL REQUIRED, and retirement makes it more important rather than less: assert that `supports_deny_push` is NOT set True by the mere presence of `git_commit_helper.offer_commit`, a hook file, or a config value. That inference is forbidden by `host_sandbox_profile.py:88-95` and was already rejected once for the host capabilities; a test pinning the refusal is what stops it being reintroduced by a future well-meaning change. NOTE a sibling already exists and should be reused rather than duplicated: `tests/test_host_capability_extension.py:255-257` proves a FORCED `True` verdict does not stick for `CAP_DENY_PUSH`.
  - Depends on: E-03
  - Expected outcome: `RUN_FINDING_CODES` holds 12 codes and `validate_finding_table` reports the table VALID; the four measured test assertions updated; `supports_deny_push` and every capability-gate test unchanged and passing; a test pins the refusal of presence-based inference.
  - Execution state: performed
  - Execution note: The `RunFindingCode` is removed and replaced IN PLACE by a comment recording the retirement, its authority, and the do-not-reintroduce-by-presence rule, so the removal cannot read as an accident. `validate_finding_table`'s invariant is `!= 12` with its message text updated; the bound/unbound tally comment now records the re-measured 10/2/0 alongside the prior 10/2/1 rather than overwriting it; six further "13" prose counts corrected (module header x2, section banner, `run_finding_codes` docstring, `may_abort_run` docstring, `validate_finding_table` docstring). The four measured test assertions are updated (two renamed to `..._twelve_...`, the self-validation case now passes because the invariant moved, and `unbuilt == []`). NEW `tests/test_run_no_push_boundary.py` pins both halves of the outcome in 12 cases. `supports_deny_push` UNTOUCHED (decision D3): `host_sandbox_profile.py` is not in this change's diff at all, and neither capability test file was edited.
    ONE ADJACENT COMMENT WAS ALSO CORRECTED AND THE CORRECTION IS DECLARED (decision D1): the abort tally comment read "Two of the 13 ... eight ... three" while the table ALREADY held 6 conditional / 5 never BEFORE this change, so it was wrong on arrival. It now reads the measured 2/5/5 and records both moves.

- [x] E-05 RECONCILE THE FIVE OTHER PLACES THE SPEC STILL PROMISES NO-PUSH, or state per site why each legitimately stands. Retiring only the 4.2 row would leave the spec promising the same withdrawn guarantee elsewhere, which is the exact drift this plan exists to remove and would leave a reader unable to tell which sentence is current. MEASURED at review time, `RUN-NO-PUSH` is one of SIX no-push sites in `25kzda`:
    * `:652` the 4.2 finding-code row (E-03 removes this one)
    * `:848` the host-guarantee list, "deny push-capable network routes and withhold remote credentials"
    * `:864` the capability table row for plan/spec review, listing "no-push enforcement"
    * `:1115` design principle 4, "No-push and hook guarantees require control of execution ... If a host cannot provide those controls, unattended mutation must fail closed"
    * `:1129` the descriptor field list, "the exact set of host sandbox capabilities used to deny push/network access"
    * `:1154` the worked example asserting the `oc` descriptor "positively proves ... no-push enforcement"
  DECIDE EACH ON ITS MERITS AND SAY SO; do NOT bulk-delete. Two of these are probably CORRECT AS-IS and should be defended rather than edited, because they describe the 5.2 CAPABILITY that E-04 deliberately preserves (`:848`, `:864`, `:1129`) or state a design principle that retirement does not falsify (`:1115`, whose "must fail closed" is precisely what still happens). At least one is probably WRONG INDEPENDENTLY of this plan: `:1154` claims the `oc` descriptor "positively proves ... no-push enforcement", which contradicts `supports_deny_push` being hardcoded `False` and declared-not-probed. Report that as a finding whichever way it is resolved.
  IF A SITE NEEDS A SECOND SPEC EDIT, MAKE IT AND JUSTIFY IT rather than stopping, but keep every edit inside `25kzda` and keep 4.2's OTHER rows untouched. If a site turns out to require changing a DIFFERENT spec, STOP and report: that is a scope decision this plan did not declare.
  - Depends on: E-03
  - Expected outcome: a per-site verdict for all five remaining no-push sites, with edits applied only where the site actually asserted the retired guarantee, and the `:1154` contradiction reported explicitly.
  - Execution state: performed
  - Execution note: All five sites given a verdict; see V-05 for the table. THREE DEFENDED AS-IS (`:848`/`:864`/`:1129`, now `:1030`/`:1046`/`:1347`), because each describes the 5.2 CAPABILITY that E-04 deliberately preserves rather than the retired 4.2 code. ONE DEFENDED AS-IS (`:1115`, now `:1333`), because design principle 4's "must fail closed" is exactly what still happens. ONE EDITED (`:1154`, now `:1372`), which was FALSE INDEPENDENTLY of this plan, and MORE BROADLY THAN THE PLAN PREDICTED: it claimed the `oc` descriptor "positively proves ... commit-gateway ... and no-push enforcement" while BOTH `supports_commit_gateway` and `supports_deny_push` are hardcoded `False` and declared-not-probed, so TWO clauses were false, not one (decision D2). Reframed as an explicit worked-example ASSUMPTION with the measurement stated, which keeps the example's capability-gating lesson intact. One clarifying paragraph was added at the 5.2 list to name the 4.2-code versus 5.2-capability distinction, so a reader can tell a live rule from a withdrawn one; that is the second spec edit E-05 authorizes, and it stays inside `25kzda`.

## Candidate enforcement mechanisms (E-02)

RECORDED AS DURABLE JUSTIFICATION FOR THE RETIREMENT, NOT AS AN OPEN ANALYSIS. OQ-01 is answered
(outcome (c)), so the purpose of this table is to preserve WHY building was declined, so a future
reader can reopen the question with the analysis in hand rather than redo it. NO MECHANISM IS
SELECTED, and selecting one here would re-litigate a settled maintainer decision.

The test every row is held to is the one this plan inherits: not "is there a mechanism?" but "is there
a boundary AN AGENT CANNOT EVADE?". A row without a named concrete evasion would be an incomplete
analysis, so each names one.

| Mechanism | What it would prove | What it cannot prove | CONCRETE evasion |
|---|---|---|---|
| OS/sandbox network or exec restriction (Landlock/bwrap/userns, the `x03wgn` ladder) | That the agent's processes could not reach a remote at all, enforced by the KERNEL rather than by cooperation. This is the ONLY candidate that is a real boundary. | Nothing material for this guarantee; it is the honest answer. Its cost is the problem, not its strength: it needs a per-host proven sandbox rung plus a network partition the ladder does not currently implement. | No agent-level evasion. It is declined for SCOPE, not weakness: `host_sandbox_profile` already proves a sandbox rung must be PROBED BY ATTEMPT (the module records a host where every signal said "available" and the jail still failed), so this is a project of `1o4eif` magnitude, not a check. NOTE the partial-evasion caveat: a sandbox that confines only the AGENT while the DRIVER retains network could still push on the agent's behalf, so the boundary must cover the whole turn or it proves less than it claims. |
| Git `pre-push` hook | That a push invoked through ordinary `git push` in this repository ran our script first. | That a push did not happen. A hook is a local, opt-in convenience, not an authorization layer. | `git push --no-verify` skips it outright. Also `git -c core.hooksPath=/dev/null push`, or invoking a second clone. THE MAINTAINER'S OWN RATIONALE NAMES THIS EVASION (`b23d447d`). |
| Remote-less clone (delete or never configure `origin`) | That no named remote existed at some observed moment. | That none can be added. Remote configuration is ordinary repository state an agent can write. | `git push https://<url> HEAD`, or `git remote add` then push. A URL argument needs no configured remote at all. |
| Push-denying credential (no token, read-only token, credential helper refusing) | That the credential the DRIVER supplied cannot push. | That no OTHER credential is reachable. Credentials live in the ambient environment the agent shares. | The agent reads another credential from `~/.git-credentials`, an `SSH_AUTH_SOCK` agent, a `GITHUB_TOKEN` in the environment, or `gh auth`. Unless the sandbox above removes them, they are simply available. |
| Driver-side commit/push helper (`git_commit_helper.offer_commit`, `aw commit`) | That pushes routed THROUGH THE HELPER did not occur. | Anything about pushes not routed through it. This is a helper the driver CHOOSES to call. | Invoke `git push` directly, bypassing the helper entirely. THE MAINTAINER'S RATIONALE NAMES THIS (`b23d447d`), and `host_sandbox_profile.py:88-95` forbids in writing inferring support from this helper's PRESENCE. |
| Config flag / policy value the agent is told to honor (`no_push: true`) | An intent, recorded. | Any enforcement whatsoever. It constrains only an agent that chooses to read and obey it. | The agent rewrites the value, or ignores it. NAMED IN `b23d447d` as the third evasion. |
| Host-runtime restriction the adapter ATTESTS (e.g. the host declares "network denied" in its descriptor) | That the host SAID so, with the attestation's provenance recorded. | That the host DID so. An attestation is a claim transported into our evidence, which is exactly the fail-open shape `mjx7ne` refused when it required capabilities be probed BY ATTEMPT rather than inspected. | No evasion by the agent is needed: the claim can be false with nobody lying deliberately (a host whose sandbox silently failed still reports its configured intent). Trusting it converts our fail-closed refusal into a pass. |
| The null option: declare it unsupported, fail closed, and RETIRE the 4.2 promise | That we do not know, said plainly, with an action class refused rather than allowed. | It proves nothing about pushes, and does not pretend to. | Not applicable: there is nothing to evade, because nothing is claimed. THIS IS THE STATE THAT ALREADY SHIPPED (`supports_deny_push` False, declared-not-probed) and outcome (c) aligns the SPEC with it. |

CONCLUSION THE TABLE SUPPORTS, and the reason retirement beats the alternatives: every mechanism cheap
enough to build now has a named evasion, so binding `RUN-NO-PUSH` to any of them would report a
guarantee that does not hold, which is a fail-OPEN checker and strictly worse than the honest refusal
already in place. The only row without an agent-level evasion is OS-level enforcement, which is a
separate project. That is precisely the maintainer's recorded reasoning, reached independently here.

## Project conventions discovered (Step 0)

- Spec 4.2's finding-code table is transcribed into `run_evidence.RUN_FINDING_CODES` and PINNED FIELD-BY-FIELD (not by whole-file byte equality, as the plan first said): `tests/test_run_evidence_completion.py` parses the spec table and compares `message`, `action`, `inspects` and `pass_criterion` per code (`:1097-1136`), so a reworded cell fails. Practical effect is the same, the mechanism is not; there is no single "byte-equality test" to cite.
- THE COUNT THIRTEEN IS ITSELF PART OF THE CONTRACT, in four enforcing places and ten prose ones. `run_evidence.validate_finding_table` hard-fails `len(RUN_FINDING_CODES) != 13` with `RC-COUNT` (`:1649-1656`), and three tests assert 13 or name `RUN-NO-PUSH` explicitly (`:1082`, `:1090`, `:1293-1301`). MEASURED: retiring the code breaks exactly those four. So a retirement necessarily touches the test file, which is why it is now declared in `- Scope-Paths:`.
- THE 4.2 FINDING CODE AND THE 5.2 CAPABILITY ARE DIFFERENT ARTIFACTS, and only the former is being retired. `CAP_DENY_PUSH` remains a required capability for the `review`, `mutate` and `contractless-prompt` action classes (`host_sandbox_profile.py:1324`, `:1345`, `:1366`), so those classes still fail closed at preflight after the code is gone. Five assertions in `tests/test_host_capability_extension.py` pin that and must pass UNCHANGED.
- `RUN-NO-PUSH` IS THE ONLY CODE NAMING THE "Push attempt" ABORT CLASS (`run_evidence.py:1508`; class list at `:1184-1191`). After retirement that spec-4.1 class has no code, which is TOLERATED (`Unknown or non-idempotent external outcome` is already unused, verified) and the class list is byte-pinned to spec 4.1 (`tests/test_run_evidence_completion.py:1165-1166`), so do NOT remove the class to tidy up: that would be an unauthorized 4.1 edit and would fail its own test.
- `mjx7ne` OQ-03 established the governing precedent: a capability naming enforcement that does not exist may be DECLARED `False` with a `probe_notes` reason rather than probed. Honest-unbound is a legitimate, already-sanctioned outcome, not a failure.
- Presence-based inference is FORBIDDEN for these capabilities, in writing, at `host_sandbox_profile.py:88-95`. Both `supports_commit_gateway` and `supports_deny_push` default `False` and fail closed.
- `wlxkoz`'s design rule, inherited: a code honestly reporting itself unbound is SAFE, while a code silently wired to a predicate that does not answer its question is a fail-OPEN checker. Retiring or narrowing beats binding-something-adjacent.
- Shared checkout; the suite runs BARE. Re-locate symbols before editing.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | half the item is dead | `RUN-BASELINE-OWNERSHIP` is BOUND, so the item's "nothing implements one" is false at HEAD and no second lease check may be built. | `run_evidence.py:1221-1223`; `worktree_lease.LeaseTable.claim` at `:836`; `run_evidence.dirty_within` consumed at `ipd_lifecycle.py:892-895` |
| F-2 | HIGH | the obvious fix is forbidden | Binding the code by detecting `git_commit_helper.offer_commit` (or any in-repo artifact's presence) is explicitly prohibited as fail-open. | `host_sandbox_profile.py:88-95` |
| F-3 | HIGH | it is a spec decision | Two of the three legitimate outcomes AMEND an approved spec, so an agent may not choose among them; the item itself says "needs a spec-level decision first". | item text; spec `25kzda` is `- Status: approved` |
| F-4 | MEDIUM | current state is safe | `supports_deny_push` defaults `False` and is never probed, so today's behavior fails closed. The defect is an undesigned obligation, not a live hole. | `host_sandbox_profile.py:204`, `:88-95` |
| F-5 | MEDIUM | precedent for honest-unbound | `mjx7ne` OQ-03 already ruled a non-existent enforcement may be declared `False` with a `probe_notes` reason rather than probed, so outcome (c) is sanctioned rather than a cop-out. | `mjx7ne` in `.aw/records/plans/executed/`; `probe_notes` at `host_sandbox_profile.py:212` |
| F-6 | MEDIUM | table is field-pinned, not byte-pinned | 4.2's table is compared to `RUN_FINDING_CODES` FIELD BY FIELD (message/action/inspects/pass_criterion per code), not by whole-file byte equality. Same practical effect, different mechanism; there is no single "byte-equality test" to cite or paste. | `tests/test_run_evidence_completion.py:1097-1136` |
| F-7 | LOW | last one standing | `RUN-NO-PUSH` is the sole UNBOUND-UNBUILT code; the other unbound pair waits on `runtrail-01`'s trailers being READ, not written. | `run_evidence.py:1224-1231` |
| F-8 | BLOCKER | retirement is not a one-row edit | THE PLAN'S "AMEND NOTHING ELSE" WOULD HAVE FAILED THE SUITE. Simulated outcome (c) in a scratch copy (row removed from spec AND code) and ran the suite: `5 failed, 5915 passed` against a `1 failed, 5919 passed` baseline, i.e. FOUR new failures, all hardcoded-13: `test_spec_defines_exactly_thirteen_run_codes`, `test_table_enumerates_exactly_the_specs_thirteen_codes`, `test_table_self_validation_passes`, `test_measured_binding_partition_is_recorded`. Worse than a test break: `validate_finding_table` would report the SHIPPED table INVALID at runtime via `RC-COUNT`. | measured in `/tmp` scratch copy at HEAD `c0a9de73`; `run_evidence.py:1649-1656`; `tests/test_run_evidence_completion.py:1082`, `:1090`, `:1293-1301` |
| F-9 | HIGH | the capability must survive the code | RETIRING THE 4.2 CODE MUST NOT REMOVE THE 5.2 REFUSAL. `CAP_DENY_PUSH` is a required capability for the `review`, `mutate` and `contractless-prompt` action classes, so preflight still fails closed for them after the finding code is gone. The plan never distinguished the two artifacts, so an executor "cleaning up deny_push" could delete a live gate while believing it was completing the retirement. Five assertions pin the gate and must pass unchanged. | `host_sandbox_profile.py:1324`, `:1345`, `:1366`; `tests/test_host_capability_extension.py:78`, `:190`, `:255-257`, `:333`, `:473` |
| F-10 | HIGH | the spec promises no-push in six places | RETIRING ONE ROW LEAVES FIVE OTHER NO-PUSH PROMISES STANDING, so the spec would still promise the withdrawn guarantee and a reader could not tell which sentence is current: `:848` (host guarantees), `:864` (capability table), `:1115` (design principle 4), `:1129` (descriptor fields), `:1154` (worked example). Most legitimately describe the PRESERVED 5.2 capability, but `:1154` asserts the `oc` descriptor "positively proves ... no-push enforcement", which contradicts `supports_deny_push` being hardcoded `False` and declared-not-probed, and is wrong INDEPENDENTLY of this plan. Addressed by new E-05. | grepped `25kzda` at review time; `host_sandbox_profile.py:204`, `:549-554` |
| F-11 | HIGH | the gate contradicted the resolved OQ | THE GATE SAID OQ-01 WAS `Blocking: yes` AND UNANSWERED while the question itself reads `Blocking: no` / `Status: resolved` forty lines above, so the plan told an executor to wait for a decision it already recorded, and claimed `aw ipd set approved` would refuse. Only human approval is outstanding. | the plan's own `Blocking: no` at the OQ versus the gate paragraph |
| F-12 | MEDIUM | the cited precedent says the opposite | `mjx7ne` OQ-03 DID NOT SANCTION RETIREMENT; the maintainer chose "option (a), KEEP ALL THREE capabilities, honestly labelled". It sanctions declaring a capability `False` with a `probe_notes` reason, which is precisely what E-04 now PRESERVES, so citing it for retiring the 4.2 CODE overstates it. The distinction matters because the two artifacts are different (F-9): the precedent supports keeping the capability, and OQ-01's own maintainer decision (`b23d447d`) is the authority for retiring the code. | `mjx7ne` E-02's recorded answer, 2026-09-01 |
| F-13 | MEDIUM | OQ-01's attestation is genuine | VERIFIED rather than trusted, because a plan asserting its own maintainer approval is exactly the forgery shape this repository guards: commit `b23d447d` is authored by the maintainer and its message states the decision, the declined options and the evasion reasoning independently of the plan body. The resolution is real. | `git show b23d447d` |
| F-14 | MEDIUM | a stale validation instruction | V-04 told the executor to disregard "~14 `test_run_viewer.py` failures" as belonging to defect `agrlvw`. Measured at HEAD: `tests/test_run_viewer.py` is `75 passed`, zero failures. An instruction to ignore a named failure set is dangerous once that set is empty, because it licenses ignoring real failures in that file. | ran the file at HEAD `c0a9de73` |
| F-15 | LOW | the "Push attempt" class is orphaned but that is fine | After retirement no code names spec 4.1's "Push attempt" abort class. That is TOLERATED (`Unknown or non-idempotent external outcome` is already unused today, verified) and the class list is pinned to 4.1, so removing the class would be an unauthorized 4.1 edit that fails its own test. Recorded so nobody tidies it. | computed class usage at HEAD; `run_evidence.py:1184-1191`, `:1508`; `tests/test_run_evidence_completion.py:1165-1166` |

## Proposed changes (ordered, validatable)

1. Record the current bound/unbound tally by symbol and confirm the sibling half is dead (E-01).
2. Record the candidate mechanisms and each one's concrete evasion, as durable justification for the retirement (E-02).
3. Remove the `RUN-NO-PUSH` row from 4.2 with the reason recorded, and correct the spec's own "all 13" sentence (E-03).
4. Make code and the four measured test assertions match, keep `supports_deny_push` and every capability gate untouched, and pin the refusal of presence-based inference (E-04).
5. Reconcile or defend the five other spec sites that still promise no-push, and report the `:1154` contradiction (E-05).

## Deferred / out of scope (with reason)

Each row below carries a TYPED disposition, because an obligation recorded only in prose vanishes the moment this plan reaches `executed` and classes `done` in `aw attention` (`check.ipd-uncarried-obligation`). Three of these are NOT outstanding work at all - they name work already done or deliberately not wanted - so they are DECLINED with the reason. The fourth is real future work and names its carrier.

- `RUN-BASELINE-OWNERSHIP`: now BOUND (F-1). Removed from this plan's scope entirely; building a second lease-overlap check would duplicate `worktree_lease.LeaseTable.claim`.
  - Carrier-Declined: NOT AN OUTSTANDING OBLIGATION. This is a record that work is ALREADY DONE, not deferred: `worktree_lease.LeaseTable.claim` and `run_evidence.dirty_within` both ship and were located by symbol in V-01. A carrier here would commission a duplicate of shipped machinery, which is the exact error that killed this plan's sibling half.
- `RUN-COMMIT-CONTENTS` / `RUN-COMMIT-GATEWAY`: unbound but WAITING on something else. `runtrail-01` (`m73aet`) shipped the `AW-Run:`/`AW-Item:` trailers as WRITERS only; nothing reads a trailer back, and writing one is not proving a commit's tree diff equals the item-owned delta. Binding them now would be the same fail-open error. Not this plan.
  - Carrier-Declined: ALREADY CARRIED ELSEWHERE, by the machinery these codes wait on rather than by a new item. Their `waiting_on` text in `run_evidence.RUN_FINDING_CODES` names what is missing (a captured commit-gateway RECEIPT, and a trailer READER), and the spec preamble names `wao266` from backlog `a8eufb` as the owner of the trailer wiring. These two codes are UNBOUND-BY-DEPENDENCY, which is a self-reporting state a reader and `unbound_run_finding_codes()` can both see, so nothing vanishes when this plan closes.
- `RUN-HOST-CAPABILITY`: BOUND by `mjx7ne`. Not this plan.
  - Carrier-Declined: NOT AN OUTSTANDING OBLIGATION. Work already completed by an executed plan; recorded here only to stop a reader thinking this plan should touch it.
- BUILDING A SANDBOX or network-restriction layer: if outcome (a) selects one, it is its own plan of `1o4eif` magnitude. This plan produces the decision and the spec row, not a sandbox.
  - Carrier-Declined: DELIBERATELY NOT WANTED, which is a decision and not a deferral. OQ-01 chose outcome (c) and declined outcome (a), so no sandbox is owed; filing a carrier would re-open a settled maintainer decision as if it were pending work. Where a real boundary WOULD belong is recorded durably in the spec amendment itself (`x03wgn`, the OS-sandbox line of work), which is the honest record: findable by a future reader without asserting that anyone intends to build it.

## Scope check

- Over-scope: none, but note this plan DECLARES a spec file and amends it, which is deliberate and announced.
- `tests/test_run_evidence_completion.py` ADDED to `- Scope-Paths:` in review, and it is not optional: retirement breaks four assertions in that file, measured, so an executor working the original fence would have had to either edit an undeclared path or leave the suite red (F-8).
- Under-scope: this plan does NOT build a sandbox, does NOT touch the other unbound codes, does NOT bind `RUN-NO-PUSH` to anything, and deliberately does NOT touch spec 5.2's `supports_deny_push` capability or its action-requirement map, which stay as they are so the preflight refusal survives the reporting code's retirement (F-9).
- SPEC 4.1's "Push attempt" abort class is deliberately left ORPHANED rather than removed (F-15): an unused class is already tolerated today, and the class list is pinned to 4.1, so tidying it would be an unauthorized edit that fails its own test.

## Required tests / validation

`python3 -m pytest tests/test_run_evidence_completion.py -o addopts=""` must be green after the row removal AND the four count/partition assertions are updated; MEASURED, retirement breaks exactly four tests there if they are not (F-8). `python3 -m pytest tests/test_host_capability_extension.py tests/test_host_sandbox_profile.py -o addopts=""` must be green WITH THOSE FILES UNEDITED, which is what proves the 5.2 capability gate survived the 4.2 retirement (F-9). New `tests/test_run_no_push_boundary.py` pins that `supports_deny_push` is not inferred from any artifact's presence. `validate_finding_table()` must report VALID, since a forgotten `!= 13` invariant marks the shipped table invalid at runtime rather than merely failing a test.

Plus the bare suite on a self-measured delta. The review-measured baseline at HEAD `c0a9de73` is `1 failed, 5919 passed, 3 skipped, 2 xfailed`, with the single failure the ENVIRONMENTAL `test_reporting_contract.py` gitignored-dump case. Note there is NO single "byte-equality test" to cite (F-6); the spec-to-code pinning is four per-field comparisons.

## Spec / documentation sync

THIS PLAN AMENDS SPEC `25kzda` 4.2's `RUN-NO-PUSH` ROW, and the spec file is declared in `- Scope-Paths:` so the edit is announced before the run and reconciled afterwards. WHY: 4.2 currently promises a guarantee no code delivers and no host can prove, which is the fail-open shape `wlxkoz` was built to avoid; the amendment makes the spec say what is true, whichever of the three outcomes the maintainer chooses.

DO NOT EDIT ANY OTHER 4.2 ROW: each remaining code's `message`, `action`, `inspects` and `pass_criterion` is pinned field-by-field against the code table (F-6), so a neighbouring edit is a code change. If the work turns out to require touching a second 4.2 ROW, STOP and report rather than widening silently.

THE AMENDMENT IS BROADER THAN ONE ROW IN TWO WAYS THE PLAN ORIGINALLY MISSED, both measured and both now owned by items. FIRST, the spec states its own code COUNT in prose ("carries all 13", `:36`) and the count is an enforced invariant in code plus three tests, so retirement necessarily edits `run_evidence.py` and `tests/test_run_evidence_completion.py` (now declared) or leaves `validate_finding_table` reporting the shipped table INVALID (F-8). SECOND, `25kzda` promises no-push in FIVE further places (`:848`, `:864`, `:1115`, `:1129`, `:1154`); E-05 gives each a verdict, because retiring one row while five other sentences still promise the guarantee would leave the spec self-contradictory, which is the precise drift this plan exists to end (F-10).

WHAT MUST NOT CHANGE: spec 5.2's `supports_deny_push` CAPABILITY and its action-class requirements. The 4.2 finding code is being retired; the capability that makes `review`/`mutate`/`contractless-prompt` fail closed is not (F-9). `mjx7ne` OQ-03 is often cited loosely here, so state it precisely: that decision was "KEEP ALL THREE capabilities, honestly labelled", i.e. it AUTHORIZES keeping the capability declared-`False`, and it is NOT a precedent for deleting a spec row (F-12). The authority for the retirement is OQ-01's own maintainer decision in commit `b23d447d`, and nothing else.

## Open questions

### OQ-01: Which of the three outcomes should `RUN-NO-PUSH` take: specify a real boundary, narrow the guarantee, or retire the code?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-08: OPTION (c), RETIRE THE CODE FROM SPEC `25kzda` 4.2 WITH THE REASON RECORDED. The guarantee is withdrawn rather than narrowed or built.
  WHY THIS IS THE HONEST OUTCOME RATHER THAN THE LAZY ONE, which is the distinction a reviewer should check. Today `supports_deny_push` is hardcoded `False` (`host_sandbox_profile.py:204`) and DECLARED-NOT-PROBED with the reason in `probe_notes` (`:200-202`), so the check FAILS CLOSED: a run refuses rather than proceeding unprotected. Nothing is unsafe today. What is wrong is that spec 4.2 (`:652`) promises "Capability preflight proved push denial" and an ABORT RUN on an attempted push, and no such proof or enforcement exists. Retiring aligns the written promise with reality; it removes a promise, not a protection.
  AND IT MATCHES TWO ESTABLISHED RULES IN THIS REPOSITORY rather than inventing a posture: `wlxkoz`'s rule that an honestly-unbound finding code is safe while a silently-mis-bound one is fail-open, and `mjx7ne` OQ-03's sanctioned shape of declaring `False` with a `probe_notes` reason instead of probing. So the end state is one this repository already treats as correct.
  OPTION (a) WAS DECLINED FOR A MEASURED REASON, not for cost alone: every cheap mechanism has a known evasion, and the plan enumerates them (a `pre-push` hook falls to `--no-verify`, a driver-side helper falls to invoking git directly, a config value falls to the agent rewriting it). A genuine boundary therefore means OS-level enforcement, which is a separate project of `1o4eif` magnitude, as the source backlog item states. OPTION (b) was declined because an ATTESTATION IS NOT A BOUNDARY: narrowing to "no push was attempted on the driver's own path" would keep the word "guarantee" attached to something an agent can simply step around, which is closer to the fail-open framing this whole area exists to refuse than the current honest refusal is.
  WHAT MUST STILL NOT HAPPEN, and retirement makes this MORE important rather than less: do NOT bind the code to a presence-based inference on the way out. Forbidden in writing at `host_sandbox_profile.py:88-95` and already rejected once for the host capabilities. Retiring the code and simultaneously "helpfully" reporting that a helper's existence constitutes push prevention would convert a safe fail-closed state into a fail-OPEN checker, which is strictly worse than either the current state or clean retirement.
  WHAT THE SPEC AMENDMENT MUST CARRY, since this plan now performs a documented reduction of a shipped promise: the code's removal from 4.2, the REASON (no host enforcement exists and every cheap mechanism is evadable), the statement that the prior behavior was fail-closed so nothing became less safe, and a pointer to where a real boundary would belong if it is ever built (the OS-sandbox line of work). A reader must be able to tell this was a deliberate withdrawal rather than an oversight, and must be able to find the road not taken. Note the plan already declares the spec in `Scope-Paths`, which is what makes this amendment legitimate rather than a silent weakening.
### OQ-02: Does retiring the 4.2 `RUN-NO-PUSH` code also authorize removing spec 5.2's `supports_deny_push` CAPABILITY, or must that gate be preserved?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-002
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`): REMOVE `supports_deny_push`, AND REMOVE THE THREE UNENFORCED `REFUSED` VERDICTS WITH IT, IN A SEPARATE PLAN. This OVERTURNS the review's provisional PRESERVE and the recommendation I put in the prompt, so E-04/V-04 (written as preserve) must be re-pointed or retired by whoever executes this plan. THIS PLAN STILL ONLY RETIRES THE 4.2 SPEC SENTENCE; the capability removal is NOT absorbed here, per the plan's own rule that a loosening of a live gate needs its own scope and review. The follow-up must carry: deletion of the flag, deletion of the `review`/`mutate`/`contractless_prompt` requirement entries that reference it, and removal of the six test references (`tests/test_host_sandbox_profile.py:54`, `tests/test_host_capability_extension.py:39`, `:78`, `:190`, `:255-257`, `:333`, `:473`).
  THE PREMISE OF THE REVIEW'S RECOMMENDATION WAS FALSE, AND MEASURING IT IS WHAT CHANGED THE ANSWER. The review argued PRESERVE because the capability "makes those three action classes REFUSE at preflight today" and removing it "would convert a fail-closed refusal into no check at all". MEASURED AT HEAD `8dffd7a0`: NOTHING CONSUMES THE VERDICT. `ACTION_REQUIREMENTS` is referenced only inside `host_sandbox_profile.py` (`grep -rn ACTION_REQUIREMENTS --include=*.py .` returns no consumer outside that module, and no test), and `oc_runipd.py`/`agy_runipd.py` import only `SandboxProfileError`, `build_sandbox_plan`, `detect_host_capabilities`, `enter_sandbox`, `select_execution_profile` (`oc_runipd.py:58-65`). The `ALLOWED`/`REFUSED` lines are rendered by the reporting command alone (`host_cmd.py:104-107`). So there is no preflight refusal to preserve: the flag's only effect is to PRINT a protection that does not exist, which is worse than noise because a reader may act on it.
  THE MAINTAINER CAUGHT THIS BEFORE I DID, twice over. First they rejected the prompt outright, asking what the "second thing" and the "three classes" were and stating "I see `aw oc run` reviewing and editing lots of stuff, so I don't know what you're talking about". That observation IS the disproof: the runs are not blocked because nothing reads the verdict. Then, given the corrected picture, they challenged my revised recommendation to keep the flag: "I worry that keeping a dead flag is more noise than utility and the flag was never (yet) shipped in a release."
  BOTH GROUNDS THEY GAVE VERIFIED. NEVER SHIPPED: introduced 2026-09-04 in `30108f78`, while the newest tag `v1.3.0-rc.1` dates from 2026-07-24, so no released artifact contains it and removal has no external consumer. NOT THE ONLY HONEST RECORD: the finding survives independently in the run-findings table (`run_evidence.py:1505-1517`), which records `binding=UNBOUND_UNBUILT` and states that no host enforcement exists, that `check_engine.check_push_authorization` is "LOCAL, bypassable pre-push FEEDBACK that explicitly disclaims being an authority boundary", and that binding to it "would be a fail-open inference". So the flag duplicates a record rather than constituting one.
  A CITATION I USED WAS UNVERIFIED AND IS WITHDRAWN. I told the maintainer they had already ruled "KEEP ALL THREE capabilities, honestly labelled" (attributed to `mjx7ne` OQ-03). They replied "I don't remember this. Did you call it something chock full of jargon and I accidentally agreed to something I did not understand?" I could not show they were ever asked that in plain language, so it was retracted in the next prompt and must NOT be cited as authority by any successor. Treat `mjx7ne` OQ-03 as an unverified attribution until someone re-establishes it.
  WHAT REMAINS FORBIDDEN, unchanged by this answer: do not bind the retired code to a presence-based inference on the way out (`host_sandbox_profile.py:88-95`). Removing the flag is not permission to infer push prevention from the existence of any helper.
  ORIGINAL REVIEW REASONING RETAINED BELOW, including its now-disproved preflight premise, so the correction is visible rather than silent. RAISED IN REVIEW AS AN IRREVERSIBLE DECISION THE REVIEWER MAY NOT MAKE ALONE (review record `4h7tt0` D-2, `Reversible: no`). The review resolved it PROVISIONALLY as PRESERVE, and E-04/V-04 are written that way, but the decision removes or keeps a live security refusal and so needs the maintainer's word rather than a reviewer's judgement.
  WHY IT IS A REAL QUESTION AND NOT A FORMALITY. OQ-01 authorized retiring the 4.2 FINDING CODE. It said nothing about spec 5.2's CAPABILITY of the same name, and the two are different artifacts with different consumers. MEASURED: `CAP_DENY_PUSH` is a REQUIRED capability in the action-requirement map for `review`, `mutate` and `contractless-prompt` (`host_sandbox_profile.py:1324`, `:1345`, `:1366`), and since it is permanently `False` it makes those three action classes REFUSE at preflight today. Retiring the reporting code does not change that. So an executor could reasonably read "retire RUN-NO-PUSH" as also meaning "remove the now-unused deny_push machinery", and doing so would convert a fail-closed refusal into no check at all, which is a security regression delivered under cover of an honesty change.
  WHY THE REVIEWER CANNOT SETTLE IT. Removing a capability that currently refuses is not undoable by editing a plan: it changes what unattended runs are permitted to do, and anything that starts relying on the loosened gate compounds it. The repository's own rule is that a `Reversible: no` decision must be escalated rather than recorded, so it is escalated here and the plan is BLOCKED until answered, which is the correct fail-closed state.
  THE RECOMMENDATION IS PRESERVE, on three grounds. `mjx7ne` OQ-03's maintainer answer was expressly "KEEP ALL THREE capabilities, honestly labelled", which is authority for keeping this one declared-`False`. The capability's refusal is the only thing still making three action classes fail closed on this guarantee, so keeping it means retirement genuinely removes a promise rather than a protection, which is the plan's own stated justification. And five assertions already pin the behavior (`tests/test_host_capability_extension.py:78`, `:190`, `:255-257`, `:333`, `:473`), so preserving costs nothing while removing means editing tests that exist to prevent exactly this.
  IF THE ANSWER IS REMOVE, this plan must NOT absorb it: that is a separate security-boundary change needing its own plan, its own scope declaration, and its own review, because it loosens a live gate rather than correcting a document.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the current bound/unbound tally with its source line, and paste `supports_deny_push`'s default plus its `probe_notes` reason. Paste the symbol-level proof that `RUN-BASELINE-OWNERSHIP` is BOUND (`worktree_lease.LeaseTable.claim` and `run_evidence.dirty_within` both located), and state explicitly that no second lease-overlap check will be built. If the tally has moved since authoring, paste the new one and state how this plan's scope changed.
  - Observed evidence: THE TALLY AT HEAD `2815aa56`, MEASURED BEFORE ANY EDIT (not read from the plan):
    ```
    $ python3 -c "...Counter(x.binding for x in RUN_FINDING_CODES)..."
    total codes: 13
    tally: {'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2, 'UNBOUND-UNBUILT': 1}
    unbuilt: ['RUN-NO-PUSH']
    by-dep: ['RUN-COMMIT-CONTENTS', 'RUN-COMMIT-GATEWAY']
    validate: EvidenceValidationResult(ok=True, findings=())
    ```
    ITS SOURCE LINE, which agrees: `run_evidence.py` "# Net: 10 BOUND, 2 UNBOUND-BY-DEPENDENCY, 1 UNBOUND-UNBUILT (F3 recorded 9 / 2 / 2)." THE TALLY HAD NOT MOVED since the plan was authored, so THIS PLAN'S SCOPE DID NOT CHANGE. `RUN-NO-PUSH` was still the sole UNBOUND-UNBUILT code.
    `supports_deny_push` DEFAULT AND REASON:
    ```
    $ python3 -c "print(HostSandboxCapabilities().supports_deny_push, CAP_DENY_PUSH)"
    supports_deny_push default: False
    CAP_DENY_PUSH = supports_deny_push
    ```
    Its declared-not-probed reason, verbatim from `_DECLARED_UNENFORCED[CAP_DENY_PUSH]` (`host_sandbox_profile.py:572-577`): "DECLARED, NOT PROBED: no push-denial enforcement (tool/network/credential denial) exists in this package to attempt, so this capability is permanently not-supported (fail-closed). The driver not pushing is a driver behavior, not a host-enforced denial (spec 25kzda 5.2 guarantee 1, classified Host-dependent)."
    `RUN-BASELINE-OWNERSHIP` IS BOUND, both symbols located at HEAD:
    ```
    $ grep -n "def claim" agent_workflows/worktree_lease.py
    921:    def claim(self, lane_id: str, paths: Sequence[str]) -> None:
    922-        """Atomically claim ``paths`` for ``lane_id``. Fails closed (no partial claim) if ANY path is
    923-        already owned by a different lane."""
    $ grep -n "def dirty_within" agent_workflows/run_evidence.py
    223:def dirty_within(
    ```
    NO SECOND LEASE-OVERLAP CHECK WAS BUILT, and none will be: the per-path overlap check `wlxkoz` F3 said nobody had built ships as `LeaseTable.claim`, and `dirty_within` decides the pre-existing-dirty-path half. `RUN-BASELINE-OWNERSHIP` is untouched by this change (it is one of the 12 surviving rows).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the candidate table. For EACH mechanism it must state what it proves, what it cannot prove, and a CONCRETE evasion; a row without a named evasion is an incomplete analysis and fails this item. Confirm in prose that no mechanism was selected, and that the table does not contradict the three evasions the maintainer's own rationale records in `b23d447d`.
  - Observed evidence: THE TABLE IS IN THIS PLAN under "Candidate enforcement mechanisms (E-02)" and is not repeated here, because duplicating it would create two copies that can drift. It carries EIGHT rows covering every family E-02 requires: OS/sandbox restriction; git-level in THREE variants (`pre-push` hook, remote-less clone, push-denying credential); the driver-side helper; a config/policy flag; a host-runtime ATTESTATION; and the null option. EVERY ROW NAMES A CONCRETE EVASION - verified row by row: `--no-verify` / `core.hooksPath=/dev/null`; `git push <url> HEAD` with no configured remote; another credential from `~/.git-credentials`, `SSH_AUTH_SOCK`, `GITHUB_TOKEN`, or `gh auth`; invoking `git push` directly around the helper; the agent rewriting the config value; and for the attestation row, that no evasion is even needed because a false claim requires nobody to lie. The two rows with no agent-level evasion say so explicitly and explain why (OS-level enforcement is a real boundary declined for SCOPE; the null option claims nothing to evade), which is a stated verdict and not a missing cell.
    NO MECHANISM WAS SELECTED. The table's conclusion is that every mechanism cheap enough to build now has a named evasion, so any binding would be fail-open; it recommends nothing, because OQ-01 is already decided and recommending one would re-litigate it.
    CONSISTENT WITH `b23d447d`, checked against the maintainer's own words rather than assumed. That commit message states: "every cheap mechanism has a known evasion (a pre-push hook falls to --no-verify, a driver-side helper to invoking git directly, a config value to the agent rewriting it), so a real boundary means OS-level enforcement, a separate project of 1o4eif magnitude. Narrowing was declined because an attestation is not a boundary." All three evasions appear in the table, attributed to that commit; the table CONTRADICTS none of them and adds five more rows in the same direction.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste OQ-01's recorded answer with its provenance (the maintainer's decision, its date, and commit `b23d447d`), then paste the spec diff. It must show the `RUN-NO-PUSH` row REMOVED and the "all 13" sentence at `:36` corrected, and NO other 4.2 row's text altered; paste `git diff` for the spec file rather than only `--stat`, so a reviewer can see which lines moved. Quote the recorded reason from the spec-sync section. Do NOT claim to have run a "byte-equality test": no such single test exists (F-6); paste instead the four FIELD-comparison tests (`test_every_message_is_verbatim_from_the_spec`, `test_every_failure_action_is_verbatim_from_the_spec`, `test_inspects_and_pass_criterion_are_verbatim_from_the_spec`, `test_every_message_carries_the_specs_recovery_command`) passing over the remaining 12 codes.
  - Observed evidence: OQ-01'S PROVENANCE, VERIFIED FROM GIT RATHER THAN FROM THE PLAN BODY (an agent-asserted approval is exactly what must not be trusted):
    ```
    $ git log -1 --format='%an <%ae>%n%ad' b23d447d
    Gabriele Fariello <gabriele.fariello@gmail.com>
    Tue Sep 8 22:54:37 2026 -0400
    ```
    Its message states the decision independently of the plan: "plan(nopush): resolve 4h7tt0 OQ-01, retire RUN-NO-PUSH from spec 4.2 / RESOLVED by the maintainer 2026-09-08: option (c), retire the code with the reason recorded. The guarantee is withdrawn rather than narrowed or built." It is authored by the MAINTAINER, not by an agent, so the attestation is genuine.
    THE SPEC DIFF (full `git diff`, not `--stat`), abbreviated only by omitting the 11 UNCHANGED table rows that appear as context:
    ```diff
    @@ -754,7 +783,6 @@
     | `RUN-COMMIT-GATEWAY` | Captured commit-gateway event and argv | ... | FAIL ITEM after containment; ABORT RUN for a hook-bypass attempt |
    -| `RUN-NO-PUSH` | Enforced tool policy, network policy receipt, all captured process events, starting/ending remote config and remote-tracking refs | Capability preflight proved push denial; no push event or unexplained remote-state change exists | `[RUN-NO-PUSH] Host <host> could not prove push prevention for <item>. No work may start without that capability. Choose a capable host and run: aw <host> run <selector>` | FAIL ITEM if refused at preflight; ABORT RUN if a push was attempted |
     | `RUN-CHECK-FRESHNESS` | Check command end times, ... | RETRY, then FAIL ITEM |
    ```
    EXACTLY ONE TABLE LINE IS DELETED AND NO TABLE LINE IS MODIFIED: in the whole spec diff the only `-` lines inside the 4.2 table are that single row, and the only other changed hunks are the preamble sentence, two ADDED prose paragraphs above the table, one ADDED paragraph at 5.2, and the Section 7 example sentence (E-05). The preamble correction:
    ```diff
    -`run_evidence.RUN_FINDING_CODES` carries all 13, of which 10 are BOUND to predicates, one
    -(`RUN-NO-PUSH`) is a name over deliberately unbuilt enforcement ...
    +`run_evidence.RUN_FINDING_CODES` carries all 12, of which 10 are BOUND to predicates and the remaining
    +two (`RUN-COMMIT-CONTENTS`, `RUN-COMMIT-GATEWAY`) are unbound-by-dependency, so NO code is now
    +UNBOUND-UNBUILT.
    ```
    THE RECORDED REASON, quoted from the new 4.2 prose: "`RUN-NO-PUSH` WAS RETIRED FROM THIS TABLE ON 2026-09-08 (maintainer decision, commit `b23d447d`, executed by plan `4h7tt0`) ... THE PROMISE IS WITHDRAWN, NOT THE PROTECTION ... Nothing in this repository ever enforced push denial: `host_sandbox_profile` declares `supports_deny_push` False and NEVER probes it, so the capability FAILED CLOSED and a run requiring it was REFUSED rather than proceeding unprotected. Removing the row therefore removes a guarantee the table could not deliver; it does not remove a check that was passing."
    THE FOUR FIELD-COMPARISON TESTS, PASSING OVER THE REMAINING 12 CODES (no "byte-equality test" is claimed; none exists):
    ```
    $ python3 -m pytest tests/test_run_evidence_completion.py -o addopts="" -v -k "verbatim or recovery_command"
    tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_every_message_carries_the_specs_recovery_command PASSED [ 20%]
    tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_every_message_is_verbatim_from_the_spec PASSED [ 40%]
    tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_every_failure_action_is_verbatim_from_the_spec PASSED [ 60%]
    tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_inspects_and_pass_criterion_are_verbatim_from_the_spec PASSED [ 80%]
    tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_abort_class_set_is_verbatim_from_spec_4_1 PASSED [100%]

    ======================= 5 passed, 82 deselected in 0.44s =======================
    ```
    Those four compare `message`, `action`, `inspects` and `pass_criterion` PER CODE against the parsed spec table, so a reworded neighbouring cell would fail them. They pass, which is the proof no other row's text was altered.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `len(RUN_FINDING_CODES)` == 12 and `validate_finding_table()` reporting the table VALID (this is the assertion that catches a forgotten `!= 13` invariant, which would otherwise mark the shipped table invalid at runtime). Paste the diff of all four measured test assertions, and paste `python3 -m pytest tests/test_run_evidence_completion.py -o addopts=""` green.
    THE CAPABILITY MUST BE PROVEN UNTOUCHED, which is this item's central safety claim: paste `supports_deny_push` still `False` with its `probe_notes` reason, and paste `python3 -m pytest tests/test_host_capability_extension.py tests/test_host_sandbox_profile.py -o addopts=""` green WITHOUT having edited either file. If either file needed an edit, this item FAILS: that means the change reached into the 5.2 capability gate, which OQ-01 did not authorize (F-9).
    THE ANTI-FAIL-OPEN ASSERTION: paste the test proving `supports_deny_push` is NOT set True by the presence of `git_commit_helper.offer_commit`, a hook file, or a config value, and paste it FAILING against a deliberately fail-open stub so the test is shown to have teeth. A test that passes against a fail-open implementation pins nothing.
    Paste the bare `python3 -m pytest` summary line with a self-measured BEFORE baseline and the AFTER-minus-BEFORE failure set EMPTY. The review-measured baseline at HEAD `c0a9de73` is `1 failed, 5919 passed, 3 skipped, 2 xfailed`, the failure being the ENVIRONMENTAL `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` (a gitignored local dump). DISREGARD THE PLAN'S FORMER INSTRUCTION about "~14 `test_run_viewer.py` failures": that file is `75 passed` at HEAD (F-14), so any failure there IS this plan's to explain.
  - Observed evidence: THE COUNT AND THE RUNTIME SELF-CHECK:
    ```
    $ python3 -c "from agent_workflows.run_evidence import ..."
    len(RUN_FINDING_CODES) = 12
    validate_finding_table() = EvidenceValidationResult(ok=True, findings=())
    RUN-NO-PUSH present: False
    unbound: ('RUN-COMMIT-CONTENTS', 'RUN-COMMIT-GATEWAY')
    unbuilt: []
    ```
    THE `!= 13` INVARIANT WAS NOT MERELY UPDATED, IT WAS PROVEN LOAD-BEARING. I restored the invariant to `13` in a scratch copy, leaving the 12-row table, to show what a forgotten amendment costs:
    ```
    --- invariant left at 13: simulating a FORGOTTEN amendment ---
    ok = False
      EvidenceFinding(code='RC-COUNT', where='RUN_FINDING_CODES', message='spec 25kzda 4.2 defines 12 codes, table has 12', reason='finding-code table size does not match the spec')
    FAILED tests/test_run_no_push_boundary.py::TestRunNoPushIsRetiredFromTheVocabulary::test_the_table_reports_itself_valid_at_the_new_count
    FAILED tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_table_self_validation_passes
    ========================= 2 failed, 97 passed in 1.55s =========================
    ```
    The SHIPPED table reports itself INVALID at runtime, exactly as F-8 predicted, and two tests catch it. The scratch change was reverted and re-verified (`ok = True`, `99 passed`); `git status` shows only the four intended paths.
    THE FOUR MEASURED TEST ASSERTIONS, DIFFED:
    ```diff
    -    def test_spec_defines_exactly_thirteen_run_codes(self) -> None:
    -        self.assertEqual(len(self.spec_rows), 13, ...)
    +    def test_spec_defines_exactly_twelve_run_codes(self) -> None:
    +        self.assertEqual(len(self.spec_rows), 12, ...)
    +        self.assertNotIn("RUN-NO-PUSH", self.spec_rows, ...)
    -    def test_table_enumerates_exactly_the_specs_thirteen_codes(self) -> None:
    -        self.assertEqual(len(evidence.RUN_FINDING_CODES), 13)
    +    def test_table_enumerates_exactly_the_specs_twelve_codes(self) -> None:
    +        self.assertEqual(len(evidence.RUN_FINDING_CODES), 12)
    -        self.assertEqual(unbuilt, ["RUN-NO-PUSH"])
    +        self.assertEqual(unbuilt, [])
    ```
    The fourth, `test_table_self_validation_passes`, needed NO edit: it asserts the table self-validates, and it passes once the invariant is `12` (and fails when it is not, as pasted above). The count was amended deliberately rather than loosened to `len(RUN_FINDING_CODES)`, which would have deleted the guard.
    ```
    $ python3 -m pytest tests/test_run_evidence_completion.py -o addopts=""
    collected 87 items
    tests/test_run_evidence_completion.py .................................. [ 39%]
    .....................................................                    [100%]
    ============================== 87 passed in 1.40s ==============================
    ```
    THE CAPABILITY IS PROVEN UNTOUCHED, this item's central safety claim. `supports_deny_push` still `False`, with its reason (pasted in full in V-01):
    ```
    supports_deny_push default: False
    $ python3 -c "probe_runner_safety_capabilities()"
    supports_commit_gateway                False
    supports_deny_push                     False
    supports_fresh_verifier_session        True
    ```
    NEITHER CAPABILITY FILE WAS EDITED, which `git diff --name-only` proves (`host_sandbox_profile.py` does not appear at all):
    ```
    $ git diff --name-only
    .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    agent_workflows/run_evidence.py
    tests/test_run_evidence_completion.py
    $ python3 -m pytest tests/test_host_capability_extension.py tests/test_host_sandbox_profile.py -o addopts=""
    tests/test_host_capability_extension.py ................................ [ 41%]
    ................                                                         [ 62%]
    tests/test_host_sandbox_profile.py .............................         [100%]
    ============================== 77 passed in 0.97s ==============================
    ```
    So the 5.2 gate survived the 4.2 retirement with its five pinning assertions unedited. NOTE FOR THE REVIEWER: OQ-02's recorded answer OVERTURNS this item's "preserve" instruction (the maintainer chose to REMOVE the flag), but explicitly withholds that removal from this plan; it is carried by backlog `aagh7v` (`open`). I followed E-04 as written, deliberately (decision D3).
    THE ANTI-FAIL-OPEN TEST, WITH TEETH SHOWN. New `tests/test_run_no_push_boundary.py` (12 cases) asserts the verdict is not inferred from the PRESENCE of `git_commit_helper.offer_commit`, of `check_engine.check_push_authorization`, or of a registered probe, with each artifact confirmed PRESENT first so the inference is genuinely available to be made. Its teeth case runs the real forbidden logic (`hasattr(git_commit_helper, "offer_commit")`) and requires the assertion to FAIL against it:
    ```
    $ python3 -m pytest tests/test_run_no_push_boundary.py -o addopts=""
    collected 12 items
    tests/test_run_no_push_boundary.py ............                          [100%]
    ============================== 12 passed in 0.17s ==============================
    ```
    AND THE FILE ALREADY CAUGHT ME BEING WRONG, which is the honest evidence it is not vacuous: my first version asserted `CAP_DENY_PUSH not in _RUNNER_SAFETY_PROBES` and FAILED (`AssertionError: 'supports_deny_push' unexpectedly found in {...'supports_deny_push': None...}`). The real structure is key-present-mapped-to-None, deliberately, and the test now asserts that shape.
    THE BARE SUITE, SELF-MEASURED BEFORE AND AFTER. BEFORE, at HEAD `2815aa56` with no edits:
    ```
    1 failed, 8117 passed, 3 skipped, 2 xfailed, 3 warnings in 161.86s (0:02:41)
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    ```
    AFTER, with every change in place:
    ```
    1 failed, 8129 passed, 3 skipped, 2 xfailed, 3 warnings in 207.12s (0:03:27)
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    ```
    AFTER-MINUS-BEFORE FAILURE SET IS EMPTY: the same single test fails in both, and passed count rises by 12, exactly the new file's case count. THE ONE FAILURE IS ENVIRONMENTAL AND NOT MINE, and I proved it rather than asserting it: it asserts a non-isolated turn carries no `OPENCODE_CONFIG_CONTENT` denial policy, and MY OWN turn's environment exports that variable, which leaks into the child env the test builds. Cleared it and the file is green:
    ```
    $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py -o addopts=""
    ============================== 76 passed in 7.59s ==============================
    ```
    NOTE THE BASELINE THIS PLAN CITED IS STALE and I did not rely on it: the review recorded `1 failed, 5919 passed` at `c0a9de73` with `test_reporting_contract.py` failing. At `2815aa56` the suite has 8117 passing and that test passes; the single failure is a different, lane-specific one. I also confirmed F-14's point still holds (`tests/test_run_viewer.py` is not failing).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste a per-site verdict for all five remaining no-push sites (`:848`, `:864`, `:1115`, `:1129`, `:1154`), each saying EDITED or DEFENDED-AS-IS with its reason. Paste the diff for any edited site. State explicitly what was concluded about `:1154`'s claim that the `oc` descriptor "positively proves ... no-push enforcement" given `supports_deny_push` is hardcoded `False`; a verdict that silently leaves that contradiction unmentioned fails this item.
  - Observed evidence: LINE NUMBERS SHIFTED because E-03 added prose; both the plan's number and the current one are given so a reviewer can locate each site.

    | Plan cite | Now at | Text | Verdict | Reason |
    |---|---|---|---|---|
    | `:848` | `:1030` | "deny push-capable network routes and withhold remote credentials" | DEFENDED-AS-IS | It is an item in the list of what the 5.2 DESCRIPTOR must answer, i.e. a question asked of a HOST ("whether the host can"), not a claim that any host does. That capability is deliberately PRESERVED (F-9), and its honest answer today is No, which FAILS CLOSED. Deleting it would convert a refusal into no check. |
    | `:864` | `:1046` | capability table row listing "no-push enforcement" for plan/spec review | DEFENDED-AS-IS | Same artifact: it states what the review ACTION REQUIRES of a host, which is the `ACTION_REQUIREMENTS` map E-04 leaves untouched. A requirement that no host meets is a refusal, not a false promise. |
    | `:1115` | `:1333` | design principle 4, "No-push and hook guarantees require control of execution ... unattended mutation must fail closed" | DEFENDED-AS-IS | Retirement does not falsify it; it CONFIRMS it. The principle's own conclusion ("if a host cannot provide those controls, unattended mutation must fail closed") is exactly the shipped behavior, and the retirement removed the 4.2 claim that the control HAD been proven. |
    | `:1129` | `:1347` | descriptor field list, "the exact set of host sandbox capabilities used to deny push/network access" | DEFENDED-AS-IS | It sits under 6.2, "Implementation choices still requiring repository-level definition", i.e. it explicitly labels this as NOT YET DEFINED. That is the most accurate sentence in the spec on this subject and needs no change. |
    | `:1154` | `:1372` | worked example, the `oc` descriptor "positively proves ... no-push enforcement" | EDITED | FALSE, and false in TWO clauses rather than one. |

    THE `:1154` CONTRADICTION, STATED EXPLICITLY AS REQUIRED. The sentence claimed the CURRENT `oc` descriptor "positively proves standard isolated-worktree, commit-gateway, hook, fresh-session, and no-push enforcement". MEASURED at HEAD:
    ```
    supports_commit_gateway                False
    supports_deny_push                     False
    supports_fresh_verifier_session        True
    ```
    So the claim was false for NO-PUSH, and it was ALSO false for COMMIT-GATEWAY, which the plan did not predict: both are DECLARED AND NEVER PROBED, so the real descriptor proves neither. A reader taking the sentence at face value would have believed TWO protections were in force. The commit-gateway half is wrong INDEPENDENTLY of this retirement and is reported as a defect finding.
    THE EDIT, chosen over deleting the clauses because Section 7 is a worked example that needs one capability proven and one missing to demonstrate capability gating (decision D2):
    ```diff
    -The current `oc` capability descriptor positively proves standard isolated-worktree, commit-gateway, hook, fresh-session, and no-push enforcement. It does not prove the specialized `controlled_network_allowlist` capability required by `host06`.
    +ASSUME FOR THIS EXAMPLE that the `oc` capability descriptor positively proves standard isolated-worktree, commit-gateway, hook, fresh-session, and no-push enforcement, and that it does not prove the specialized `controlled_network_allowlist` capability required by `host06`. THAT ASSUMPTION IS COUNTERFACTUAL TODAY AND IS STATED AS AN ASSUMPTION FOR THAT REASON (corrected 2026-09-22 by plan `4h7tt0`; previously this sentence read "The current `oc` capability descriptor positively proves ...", a present-tense claim about the shipped descriptor). MEASURED: `probe_runner_safety_capabilities()` returns `supports_deny_push` False and `supports_commit_gateway` False, both DECLARED AND NEVER PROBED ... The COMMIT-GATEWAY half of the old claim was false independently of the no-push retirement.
    ```
    ONE ADDITIONAL EDIT, which E-05 authorizes ("if a site needs a second spec edit, make it and justify it"): a paragraph added above the 5.2 list naming the 4.2-code versus 5.2-capability distinction, so a reader can tell which sentence is current and does not read the three DEFENDED sites as leftovers of the retired promise. It also names backlog `aagh7v` as the owner of the flag's eventual removal. Both edits are inside `25kzda`; NO OTHER SPEC WAS TOUCHED, and no 4.2 row other than the removed one changed (V-03).
    `aw check specs` conforms with zero findings against this spec:
    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"specs","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":"aw specs check"}
    ```
    (The single diagnostic is the standard `check.collisions-not-checked` advisory, unrelated to this spec.)
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

OQ-02 IS NOW ANSWERED AND THE GATE IS CLEAR (updated at execution, 2026-09-22). The paragraph below is retained because it records why the plan was held: OQ-02 was `Blocking: yes` and unanswered, `aw ipd lint` refused it with `IPD-Q501`, and that was the correct fail-closed state. It was answered on 2026-09-10 (`Status: resolved`) and the plan was approved on 2026-09-13, so `aw ipd lint` reports `conforming` at execution time. THE ANSWER OVERTURNED E-04/V-04's "preserve" premise WITHOUT MOVING THE WORK HERE: the maintainer chose to REMOVE `supports_deny_push`, and explicitly placed that removal in a SEPARATE plan, which is now carried by backlog `aagh7v` (`open`). This plan therefore preserved the capability exactly as E-04 directs, and V-04 proves `host_sandbox_profile.py` and both capability test files are unedited. See decision D3.

THE ORIGINAL GATE TEXT, KEPT FOR THE RECORD: "OQ-02 IS OPEN AND `Blocking: yes`, SO THIS PLAN IS NOT READY TO EXECUTE. `aw ipd lint` refuses it at every checkpoint with `IPD-Q501` (verified in review), and `aw ipd set approved` will refuse while it stands. That is the correct fail-closed state, not an obstacle to route around: the question asks whether retiring the 4.2 REPORTING CODE also authorizes removing spec 5.2's `supports_deny_push` CAPABILITY, which currently makes three action classes refuse at preflight. Answer OQ-02 (`/askme`), then re-run the lint."

OQ-01, by contrast, IS ANSWERED and is `Blocking: no`, `Status: resolved`: the maintainer chose outcome (c) on 2026-09-08, recorded in commit `b23d447d` (verified in review: that commit is authored by the maintainer and states the decision and reasoning independently of the plan text, so the attestation is genuine and not agent-asserted). The gate previously claimed OQ-01 was `Blocking: yes` and unanswered, which CONTRADICTED the resolved question above it and would have told an executor to wait for an answer already given. Do not re-ask OQ-01.

After OQ-02 is answered, execution still requires explicit human approval (`- Status: approved`).

THE CURRENT STATE IS SAFE, WHICH CHANGES THE RISK CALCULUS. `supports_deny_push` already defaults `False` and fails closed, so there is no live hole to race. The wrong move here is not slowness; it is binding the code to something that does not enforce anything. Under every outcome, a fail-open binding is prohibited.

NEVER INFER SUPPORT FROM PRESENCE. Not from `git_commit_helper.offer_commit`, not from a hook file, not from a config flag. This is forbidden in writing at `host_sandbox_profile.py:88-95` and was already rejected once for the host capabilities; V-04 pins the refusal precisely so a future change cannot reintroduce it.

ONE SPEC ROW. 4.2's table is pinned FIELD BY FIELD to `RUN_FINDING_CODES` under test (F-6 corrects this paragraph's "byte-equal"); editing a neighbouring cell is a code change that will fail the suite. If the decision seems to need a second row, STOP and report. AT EXECUTION: exactly one row was removed, no other row's text changed, and the four field-comparison tests pass over the remaining 12 codes (V-03).

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT: run `aw runs` before starting.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

On completion, close backlog `d07nz2` (this plan carries `- From-Backlog: d07nz2` and inherits its `Blocks-Release: next`). The item's file records that its `RUN-BASELINE-OWNERSHIP` half was already dead; the close must not claim that half was built.
