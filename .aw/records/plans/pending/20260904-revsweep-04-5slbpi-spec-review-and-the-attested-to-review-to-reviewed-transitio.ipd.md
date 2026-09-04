# IPD: spec review and the attested to-review to reviewed transition

- Date: 2026-09-04
- Kind: child
- Concern: A SPEC'S `to-review -> reviewed` TRANSITION IS AN UNATTESTED STATUS FLIP, and there is no spec review to attest it. Two measured facts combine into one integrity hole. First, no spec-review capability exists: `.aw/system/workflows/` holds `plan-review` and `plan-review-long` and nothing that reviews a spec; `/spec` states plainly that it "PRODUCES the artifact"; `/advise spec-editor` coaches interactively and yields no verdict, no findings, and no transition. Second, `to-review -> reviewed` has NO entry in `attention_contract.TRANSITION_AUTHORITY` (`:339-365` covers only `->approved`, `->implementing`, `->implemented`, `->deferred`), so an agent may set a spec `reviewed` with no review, no findings, and no record. The same claim on a PLAN is policed by `check.review-finding-unescalated` and the approval verdict guard. Specs are the artifact that AUTHORIZES plans, so the weakest-attested transition in the tree sits at the top of the authority chain. Spec `25kzda` Section 3.3 mandates the missing action ("Run spec review; apply corrections; tool-set `reviewed`") and Section 4.8 already names three deterministic checks for it (`SPEC-REVIEW-COMPLETE`, `SPEC-REVIEW-TRANSITION`, `SPEC-REVIEW-STRUCTURE`) that nothing can satisfy.
- Scope: Deliver a spec review that can legally advance a spec from `to-review` to `reviewed`, make that transition require evidence a review occurred, and let needs-review discovery reach the specs tree. Four deliverables: the workflow-shape decision (new `spec-review/` versus generalizing `plan-review/`) made against the code and recorded, the spec review itself, the attested transition with grandfathering, and cross-type discovery so `aw <host> review --type spec` resolves. EXCLUDES the review record's shape (`eyh1fu` owns it and this plan depends on it), excludes the needs-review predicate and draft gate (`6ypimw`), excludes `--type` registration on the runners (`uyeko5`), and excludes widening review to any type beyond specs.
- Scope-Paths: .aw/system/workflows, .aw/system/workflows/index.md, agent_workflows/specs.py, agent_workflows/attention_contract.py, agent_workflows/check_engine.py, agent_workflows/review_findings.py, agent_workflows/runner_shared.py, agent_workflows/run_selection_policy.py, tests/test_specs.py, tests/test_review_findings.py, tests/test_attention_contract.py
- Item-Dependencies: executed:eyh1fu, executed:6ypimw
- Status: to-review
- Set: revsweep
- Order: 4
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 5slbpi
- Blocks-Release: next
- From-Spec: 6m4kow

## Workflow history

- 2026-09-04 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored with the `revsweep` Set, graduating requirements R-06 through R-16 of spec `6m4kow`, which completes spec `25kzda` Section 3.3 and makes its Section 4.8 checks satisfiable. THE STRONGEST ARGUMENT IS THE UNATTESTED TRANSITION, and it was measured rather than assumed: `TRANSITION_AUTHORITY` (`attention_contract.py:339-365`) has entries for `->approved`, `->implementing`, `->implemented` and `->deferred`, and NONE for `->reviewed`, so `aw specs set reviewed <id6>` succeeds with no evidence of any kind. THREE BLOCKERS MEASURED AT `3d4e5414` for the review itself, each independently fatal: no spec-review workflow exists; `/plan-review` would CORRUPT a spec if handed one, because it REQUIRES writing `- Readiness:` (`plan-review.md:377-398`, a field absent from the spec schema, whose own text warns "a consumer that finds no field FAILS CLOSED") and it hand-edits `- Status:` (`:371-372`), which `.aw/records/specs/README.md:23-24` forbids and a `status_untooled_gate` hook exists to catch; and its structural preflight runs `aw ipd lint --phase author` (`:114-117`), an IPD-only linter, guarded by a condition that silently SKIPS for a non-IPD, so the gate would pass by not running. THE WORKFLOW-SHAPE DECISION IS DELIBERATELY LEFT TO EXECUTION (spec `6m4kow` R-10 and Section 5) because it needs the code in front of it, and E-01 exists to make it a recorded decision with evidence rather than a silent choice; what the spec DOES fix is the constraint either answer must satisfy, namely that the findings/verdict/record machinery stays shared exactly once. ALSO RECORDED: the manifest at `.aw/system/workflows/index.md:44` and `.opencode/commands/spec.md:2` already CLAIM that specs are the artifact "plan-review reviews", which is documented intent the plan-review body does not honor, so the docs are already wrong and E-05 must correct them rather than leaving two contradictory statements. POPULATION MEASURED so nobody reads this as throughput work: 0 specs at `to-review`, 2 at `draft`, 20 at `approved` or `implemented` with no review records (hence the grandfathering in E-04), and 35 existing review records all of them plan reviews.

## Goal

Give specs a real review that can legally advance them to `reviewed`, make that transition prove a review happened, and let the review sweep reach the specs tree.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: decide the shape, then build the review

- [ ] E-01 MAKE AND RECORD THE WORKFLOW-SHAPE DECISION before writing any workflow text: a new `spec-review/` package, or a generalization of `plan-review/`. Spec `6m4kow` R-10 leaves this open deliberately and Section 5 states the tradeoff; this item converts it into a decision with cited evidence.
  DECIDE AGAINST THE CODE, not from preference. Read the plan-review body and count what is plan-specific: at minimum the `aw ipd lint --phase author` preflight, the required `- Readiness:` write, and the E/V-bijection and Scope-Paths rubric items. If generalizing, EVERY one of those becomes a conditional branch in a body an agent reads under load, and a mis-taken branch is a wrong lifecycle write; also note `plan-review` and `plan-review-long` are held in DELIBERATE PARITY, so generalizing means changing two bodies in lockstep.
  THE CONSTRAINT THAT BINDS EITHER ANSWER: the findings/verdict/record machinery is shared EXACTLY ONCE. `review_findings` stays the single writer and parser, and the verdict vocabulary stays `plan_readiness.VERDICTS`. A design that forks the record is wrong regardless of which shape it picks.
  Record the decision, the evidence, and the rejected option's cost in this plan's history AND in the workflow's own README, so the next reader does not re-litigate it.
  - Depends on: none
  - Expected outcome: one recorded decision with cited counts of plan-specific machinery, the rejected option's cost stated, and explicit confirmation that the record machinery stays single-sourced.
  - Execution state: pending

- [ ] E-02 Build the spec review to the shape E-01 chose. It MUST produce: a findings table using the existing columns, a verdict from the existing four-value vocabulary, a conforming review record with `Subject-Type: spec` (which `eyh1fu` made possible), and a legal tool-authored transition to `reviewed`.
  THREE HARD PROHIBITIONS, each one a measured way `/plan-review` would corrupt a spec. (a) DO NOT write `- Readiness:` onto a spec: it is a plan field, spec `25kzda` 3.3 stops a reviewed spec at an unconditional human approval gate even under `--full-auto`, so there is no automated readiness signal to record and inventing one would create a machine signal no consumer may act on. (b) DO NOT hand-edit `- Status:` or the workflow-history section: both are owned by `aw specs set`/`aw specs note`, the spec README forbids it, and a `status_untooled_gate` hook exists for this bypass. (c) DO NOT run `aw ipd lint` against a spec: it is IPD-only, and worse, plan-review's preflight is GUARDED so it would silently SKIP rather than fail, making the gate pass by not running. The spec equivalent is `aw specs check`, which is exactly what `25kzda`'s `SPEC-REVIEW-STRUCTURE` recovery command already names.
  ASK SPEC QUESTIONS, NOT PLAN QUESTIONS, in whatever rubric the chosen shape uses: are the requirements testable, do the acceptance criteria cover them, are the decisions recorded with rationale, are the open questions dispositioned. A plan rubric applied to a spec produces findings about the wrong artifact.
  - Depends on: E-01
  - Expected outcome: a spec at `to-review` can be reviewed end to end, producing findings, a verdict, a `Subject-Type: spec` record, and a tool-authored transition; none of the three prohibitions is violated; the rubric asks spec questions.
  - Execution state: pending

- [ ] E-03 Register the capability in the workflow manifest and correct the DOCUMENTATION THAT IS ALREADY WRONG. `.aw/system/workflows/index.md:44` and `.opencode/commands/spec.md:2` currently claim specs are the artifact "`plan-review` reviews", which the plan-review body does not honor.
  So this is not additive documentation: leaving those lines while adding a real spec review would give the repository two contradictory statements about which workflow reviews a spec, which is worse than the single wrong one it has now.
  If the manifest is generated rather than hand-maintained, use the compiler (`aw workflow compile`) and verify with `aw workflow check-generated` rather than hand-editing a generated file.
  - Depends on: E-02
  - Expected outcome: the capability appears in the manifest through the proper mechanism; both incorrect claims corrected; no generated file hand-edited; `aw workflow check-generated` clean for any touched package.
  - Execution state: pending

### Task group 2: attest the transition and widen discovery

- [ ] E-04 Make `to-review -> reviewed` REQUIRE evidence a review occurred: a conforming review record whose `Subject-Id` is that spec. Add the `->reviewed` entry to `TRANSITION_AUTHORITY` and enforce it through ONE shared predicate consulted by the setter and the checker alike, never a second copy.
  GRANDFATHER EXISTING SPECS, and measure before you do. 20 specs are already `approved` or `implemented` with no review record, so a naive rule would retroactively invalidate them. Bind the requirement to transitions performed AFTER the change, exactly as spec `25kzda` Section 2.11 grandfathers pre-cutover dependency statements. Verify no existing spec becomes non-conforming.
  FAIL CLOSED, and give the refusal a recovery command naming the missing record, the way every other refusal in this repository does.
  DO NOT MAKE A MISSING REVIEW AN ERROR FOR PLANS. Absence is deliberately silent there (`review_findings.py:768-769` records why: zero review files existed against 428 plans), and 428 plans still have none. This item's new pressure applies to the SPEC transition only.
  - Depends on: E-03
  - Expected outcome: `aw specs set reviewed` refuses without a conforming record and succeeds with one; the rule is one shared predicate; all 20 pre-existing `approved`/`implemented` specs remain conforming; plan behavior is unchanged.
  - Execution state: pending

- [ ] E-05 Let needs-review discovery reach the SPECS tree. `6ypimw` made the predicate type-aware while its knowledge stayed IPD-only because `runner_shared.discover_plans` walks only `.aw/records/plans` and `.agents/plans`; this item supplies the specs enumeration so `--type spec` resolves to real artifacts.
  ENUMERATE THROUGH THE EXISTING AUTHORITY, not a new path literal: use the record-path resolution the rest of the package uses, the way `check_engine.check_review_dangling` deliberately avoids hardcoding the reviews path.
  BEWARE ONE MEASURED TRAP: `aw find specs --status` SILENTLY IGNORES ITS FILTER at authoring, returning all 26 specs for every one of the nine status values. So anything built on that filter inherits the bug. Either fix it (stating that you did) or avoid depending on it, and do NOT assume it works because the flag exists.
  TYPE SCOPING IS FIXED BY SPEC `25kzda` 2.4a: IPDs only with no `--type`, so adding spec discovery must NOT silently widen the default sweep. A spec must appear only when `--type spec` names it.
  - Depends on: E-04
  - Expected outcome: specs are enumerable and `--type spec` resolves to real specs; the default sweep still selects IPDs only; no new path literal; the broken status filter is fixed or avoided, stated either way.
  - Execution state: pending

- [ ] E-06 Prove the END-TO-END path on a real spec: a `to-review` spec selected by the sweep, reviewed, recorded, and transitioned, with `aw check all` clean for the new record.
  CREATE THE FIXTURE HONESTLY. There were ZERO specs at `to-review` at authoring and 2 at `draft`, so a real end-to-end run needs either a fixture spec or a genuine `draft -> to-review` promotion through the setter. Do NOT promote one of the 2 real draft specs merely to demonstrate this plan: that is a lifecycle write on someone else's artifact for a test's convenience. Use a fixture, and say which you used.
  ALSO EXERCISE THE THREE `25kzda` 4.8 CHECKS by name (`SPEC-REVIEW-COMPLETE`, `SPEC-REVIEW-TRANSITION`, `SPEC-REVIEW-STRUCTURE`), since making them satisfiable is a stated acceptance criterion (spec `6m4kow` A-08) and they are the spec's own definition of a verified spec review.
  - Depends on: E-05
  - Expected outcome: one complete end-to-end spec review demonstrated on a fixture; `aw check all` clean for the record; the three named checks each exercised; no real draft spec promoted for test convenience.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A SPEC'S STATUS AND HISTORY ARE TOOL-OWNED. `aw specs set` validates against the legal transition table and appends history; `.aw/records/specs/README.md:23-24` forbids hand-editing either, and `hooks/status_untooled_gate.py` exists to catch the bypass. Any workflow body must call the verb, never edit the field.
- `TRANSITION_AUTHORITY` CARRIES TWO KINDS OF REQUIREMENT: `by_human` (an explicit `--by-human` attestation, described in `APPROVAL_FLOOR` as a conscious speed bump and explicitly NOT anti-malicious crypto) and `evidence` (a resolvable citation whose presence, format, and resolvability are enforced, but NOT semantic verification that the work happened). A `->reviewed` entry should be honest about being the second kind.
- `plan-review` AND `plan-review-long` ARE HELD IN DELIBERATE PARITY (`plan-review.md:17`), which is the single biggest cost of the generalize option.
- WORKFLOW PACKAGES MAY BE COMPILED. `aw workflow validate|compile|check-generated` exists, and a `_generated/` projection must never be hand-edited; check whether the target package is compiled before editing it.
- THE VERDICT VOCABULARY IS SOURCED VERBATIM FROM THE WORKFLOW BODY into `plan_readiness.VERDICTS` (`:102-108`), and `_REVIEW_PREFIX = "/plan-review"` (`:352`) is how a history entry is recognized as a review. A new workflow name means that recognition must be widened deliberately, not left to chance.
- `aw specs check` IS THE SPEC'S STRUCTURAL GATE and is already named by `25kzda`'s own `SPEC-REVIEW-STRUCTURE` recovery command.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | **THE SPEC `->reviewed` TRANSITION IS UNATTESTED, which is this plan's strongest justification.** `TRANSITION_AUTHORITY` has no `->reviewed` entry, so `aw specs set reviewed` requires no evidence of any kind, while the equivalent claim on a plan is policed. Specs authorize plans, so the least-attested transition sits highest in the authority chain. | `attention_contract.py:339-365` (entries only for `->approved`, `->implementing`, `->implemented`, `->deferred`); plan side policed by `check_engine.py:154` (`check.review-finding-unescalated`) and the `apprvguard` verdict guard |
| F-2 | NO SPEC-REVIEW CAPABILITY EXISTS, and the two nearest workflows are explicit non-substitutes: `/spec` says it PRODUCES the artifact, `/advise spec-editor` coaches with per-change consent and yields no verdict, findings, or transition. | `.aw/system/workflows/` listing (20 packages, `plan-review` and `plan-review-long` only); `spec/spec.md:13-15` ("`spec` PRODUCES the artifact"), `:17-18` ("then `plan-review` before building") |
| F-3 | **`/plan-review` WOULD CORRUPT A SPEC IN THREE MEASURED WAYS**, so "just point it at a spec" is not an option: it REQUIRES writing `- Readiness:` (absent from the spec schema, and its own text warns a consumer finding no field FAILS CLOSED), it hand-edits `- Status:` (forbidden, hook-guarded), and its structural preflight is IPD-only AND GUARDED, so on a spec the gate would SKIP rather than fail, passing by not running. | `plan-review.md:377-398` (Readiness required), `:371-372` (status write), `:114-117` (`aw ipd lint --phase author`, guarded by "that is an agent-executable IPD"), `:123-124` ("Only a `conforming` disposition proceeds"); `.aw/records/specs/README.md:23-24`; `hooks/status_untooled_gate.py` |
| F-4 | THE DOCUMENTATION ALREADY MAKES A FALSE CLAIM, so E-03 corrects rather than adds: the manifest and the OpenCode command shim both say specs are what `plan-review` reviews, which F-3 shows the body does not honor. | `.aw/system/workflows/index.md:44`; `.opencode/commands/spec.md:2` |
| F-5 | GRANDFATHERING IS MANDATORY, with a measured population: 20 specs are already `approved` (5) or `implemented` (15) with no review record, so an ungrandfathered rule would retroactively invalidate most of the specs tree. | measured at authoring: first `- Status:` bullet per file across `.aw/records/specs/*.spec.md` gives 15 `implemented`, 5 `approved`, 2 `draft`, 2 `deferred`, 1 `superseded`, 1 `implementing`; 35 review records, all plan reviews |
| F-6 | ABSENCE OF A REVIEW IS DELIBERATELY SILENT FOR PLANS and must stay so: the gating predicate returns EMPTY when no review artifact exists, documented because zero review files existed against 428 plans. This plan's new pressure is spec-only. | `review_findings.py:758` with rationale at `:768-769` |
| F-7 | THERE IS NO SPEC AT `to-review` TO TEST WITH (0 at authoring; 2 at `draft`), so E-06 needs a fixture. Promoting a real draft spec to demonstrate this plan would be a lifecycle write on another author's artifact for test convenience. | `aw find specs --status` is unreliable (F-8), so counted by direct grep: 0 `to-review`, 2 `draft` |
| F-8 | **`aw find specs --status` SILENTLY IGNORES ITS FILTER**, returning all 26 specs for every one of the nine status values, so any discovery built on it inherits the bug and would appear to work. | verified during research for all nine statuses; the 26-file total equals the unfiltered count |
| F-9 | A NEW WORKFLOW NAME BREAKS REVIEW-ENTRY RECOGNITION unless widened deliberately: `plan_readiness` recognizes a review history entry by the literal `/plan-review` prefix, so a `/spec-review` entry would not be recognized as a review at all. | `plan_readiness.py:352` (`_REVIEW_PREFIX = "/plan-review"`), used by `is_review_history_entry:355` and `newest_verdict:378` |

## Proposed changes (ordered, validatable)

1. Decide and record the workflow shape against counted plan-specific machinery, with the record-machinery constraint restated (E-01).
2. Build the spec review honoring the three prohibitions and asking spec-shaped questions (E-02).
3. Register it in the manifest and correct the two already-false documentation claims (E-03).
4. Add the `->reviewed` authority entry with one shared predicate and measured grandfathering (E-04).
5. Enumerate specs for discovery without widening the default sweep, working around or fixing the broken status filter (E-05).
6. Demonstrate the whole path on a fixture spec and exercise the three named `25kzda` checks (E-06).

## Deferred / out of scope (with reason)

- THE REVIEW RECORD'S SHAPE: `eyh1fu` owns it, and this plan DEPENDS on it (`- Item-Dependencies: executed:eyh1fu`) because a spec review cannot be filed until the record can name a spec.
- THE NEEDS-REVIEW PREDICATE AND THE DRAFT ADMISSION GATE: `6ypimw`, also a dependency, since this plan supplies the specs enumeration that its type-aware predicate was shaped for.
- `--type` REGISTRATION ON THE RUNNERS: `uyeko5` owns the spec 2.1 flag surface. This plan makes specs ENUMERABLE; the operator-facing flag that selects them is that plan's. Until both land, `--type spec` is reachable only where the flag already exists.
- MAKING A MISSING REVIEW AN ERROR FOR PLANS (F-6): deliberately silent, 428 plans affected, no spec behind such a change.
- REVIEWING BACKLOG, RESEARCH, RELEASE, OR WALKTHROUGH RECORDS: spec `6m4kow` D-03. None has a `to-review` status; `25kzda` 3.6 gray-skips three of them and 3.4 gives backlog `graduate`, not `review`.
- RETROACTIVELY REVIEWING THE 20 GRANDFATHERED SPECS. They will never have review records (spec `6m4kow` honest limits), and manufacturing records for them would fabricate evidence of reviews that did not happen.
- CHANGING PLAN-REVIEW'S RUBRIC, SEVERITY, OR VERDICT VOCABULARY. If E-01 chooses generalization, the plan path's behavior must stay identical; only spec handling is added.

## Scope check

- Over-scope: `agent_workflows/run_selection_policy.py` and `runner_shared.py` are in Scope-Paths although `6ypimw` owns the predicate. Justified and bounded: this plan supplies the SPECS ENUMERATION that the type-aware predicate consumes, which necessarily touches discovery. It must not re-edit the predicate's logic; if `6ypimw` left the seam clean, the change here is additive.
- Over-scope: `check_engine.py` and `review_findings.py` are shared with `eyh1fu`. This plan's edits are the `->reviewed` attestation predicate only, not the record's subject fields, which `eyh1fu` already changed. Sequencing (`executed:eyh1fu`) is what keeps these from colliding.
- Under-scope, DELIBERATE: after this plan, a spec can be reviewed and the transition is attested, and the OPERATOR-FACING `--type spec` flag still depends on `uyeko5`. Stated rather than implied.
- Under-scope: the 20 grandfathered specs remain unattested forever. That is a permanent honest hole recorded in spec `6m4kow`, not a defect this plan can close.

## Required tests / validation

- A spec at `to-review` reviewed END TO END on a FIXTURE: findings, verdict, `Subject-Type: spec` record, tool-authored transition. State which fixture, and confirm NO real draft spec was promoted for test convenience (F-7).
- THE THREE PROHIBITIONS PROVEN NEGATIVELY, which is the load-bearing evidence for E-02 because each is a measured way `/plan-review` corrupts a spec: no `- Readiness:` on any spec, no hand-written `- Status:` or history line (the setter did it), and `aw ipd lint` never invoked against a spec. A passing review does NOT prove these; they must be checked directly.
- `aw specs set reviewed` REFUSED without a conforming record, with the recovery command shown, and SUCCEEDING with one.
- ALL 20 pre-existing `approved`/`implemented` specs still conforming after the attestation lands (F-5). Paste the before/after count, not a claim.
- ONE shared attestation predicate, proven by grep, consulted by both the setter and the checker.
- Plan behavior UNCHANGED: a missing review is still silent for plans, and no plan-side gate got stricter (F-6).
- `--type spec` resolving to real specs, and the DEFAULT sweep still selecting IPDs only (spec `25kzda` 2.4a).
- Whether `aw find specs --status` was fixed or avoided, stated explicitly (F-8).
- Review-entry recognition still working for the chosen workflow name (F-9): if the workflow is not `/plan-review`, show that its history entries are recognized as reviews.
- The three `25kzda` 4.8 checks exercised by name.
- `aw workflow check-generated` clean for any touched package; no generated file hand-edited.
- `aw check all` NO-WORSENING against your own fresh baseline; do NOT claim it passes.
- Full suite BARE (`python3 -m pytest`), compared against your own pre-change measurement at the HEAD you started from. No `-n0`, no second `-q`, no `-p no:randomly`.
- Measure in the PRIMARY checkout, not a scratch worktree (backlog `dh0uno`).

## Spec / documentation sync

- This plan implements spec `6m4kow` R-06 through R-16 and makes spec `25kzda` Section 4.8's three spec checks satisfiable. It MUST NOT change either spec's text; if execution proves a requirement wrong, amend with `aw specs note` and say so.
- E-01's decision must be recorded in the workflow's own README as well as this plan's history, so it is not re-litigated by the next reader.
- Two documentation claims are ALREADY FALSE and must be corrected, not merely supplemented (F-4): `.aw/system/workflows/index.md:44` and `.opencode/commands/spec.md:2`.
- `.aw/records/specs/README.md` must gain the attestation requirement, since it documents the lifecycle a human follows.

## Open questions

### OQ-01: Should the spec review be a new `spec-review/` workflow or a generalization of `plan-review/`?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: NOT BLOCKING because E-01 is exactly the item that decides it, with cited evidence, and either answer yields a working capability. Deliberately left open by spec `6m4kow` R-10 and its Section 5 because it needs the code in front of it: the cost of generalizing is real but only countable by reading the body (the `aw ipd lint` preflight, the required `Readiness` write, the E/V and Scope-Paths rubric items, all becoming conditionals in a body an agent reads under load, in TWO files held in parity), and the cost of forking is a second rubric drifting from the first. The constraint that makes either answer safe is fixed and not open: the findings/verdict/record machinery stays shared exactly once, so a design that forks the record is rejected either way. Owner is the executor rather than the maintainer because the decision is technical and evidence-driven; escalate only if the counted evidence is genuinely balanced.

### OQ-02: Should `->reviewed` attestation require a review record, or accept a tool-authored history receipt?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED as REQUIRING A RECORD, per spec `6m4kow` R-11, and recorded here because the weaker option is tempting and would be a false gate. A history receipt is written by the same agent making the transition, in the same file, so it attests only that the agent claimed a review; the repository already learned this distinction on the plan side, where `plan-review.md:394-398` states the history-line prose "IS NOT THE MACHINE SIGNAL" and a consumer finding no structured field FAILS CLOSED. A separate record with a verdict and findings is at least an artifact whose absence is detectable. Honest limit, restated so the gate is not oversold: neither option proves review QUALITY, only that a review occurred and was recorded.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the recorded decision with its CITED COUNTS of plan-specific machinery in the plan-review body (the `aw ipd lint` preflight, the `Readiness` write, the E/V and Scope-Paths rubric items, and anything else found), the rejected option's stated cost, and explicit confirmation that `review_findings` remains the single record writer/parser and `plan_readiness.VERDICTS` the single verdict vocabulary. Paste the same decision recorded in the workflow README, since a decision only in a plan is invisible to the next reader.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a complete spec review on a fixture: the findings table, the verdict, the rendered record showing `Subject-Type: spec`, and the setter-authored transition. THEN PROVE THE THREE PROHIBITIONS NEGATIVELY, which a passing review does NOT demonstrate: a grep showing NO `- Readiness:` on any spec, evidence the `- Status:` and history changes came from `aw specs set`/`aw specs note` rather than a text edit, and evidence `aw ipd lint` was never invoked against a spec. Note especially that plan-review's IPD-lint preflight is GUARDED and would SKIP on a spec, so "the gate passed" is not evidence it ran.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the manifest entry created through the proper mechanism, and paste BOTH corrected documentation claims (`index.md:44` and `.opencode/commands/spec.md:2`) showing they no longer say `plan-review` reviews specs. Paste `aw workflow check-generated` clean for any touched package, and confirm no `_generated/` file was hand-edited.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw specs set reviewed` REFUSED without a conforming record, including the recovery command, and SUCCEEDING with one. Paste the `->reviewed` entry in `TRANSITION_AUTHORITY` and a grep proving ONE shared predicate serves both the setter and the checker. Paste the count of conforming specs BEFORE and AFTER, proving all 20 pre-existing `approved`/`implemented` specs survived grandfathering; a claim is not evidence here, because retroactive invalidation of the specs tree is the main risk of this item. Paste evidence plan behavior is unchanged (a missing review still silent for plans).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `--type spec` resolving to real specs, AND paste the default sweep still selecting IPDs only, since silently widening the default would violate spec `25kzda` 2.4a. State explicitly whether `aw find specs --status` was FIXED or AVOIDED and show which (F-8); if avoided, show what was used instead. Confirm no new records-path literal was added.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the end-to-end run on the FIXTURE (name it) with `aw check all` clean for the new record, and confirm NO real draft spec was promoted for test convenience. Paste each of the three `25kzda` 4.8 checks (`SPEC-REVIEW-COMPLETE`, `SPEC-REVIEW-TRANSITION`, `SPEC-REVIEW-STRUCTURE`) exercised by name with the evidence each inspects. If the chosen workflow is not `/plan-review`, paste evidence its history entries are still recognized as reviews (F-9), since `_REVIEW_PREFIX` is a literal. Then `aw check all` no-worsening against your own fresh baseline and the bare full suite with counts, compared against your own pre-change measurement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: 6 E-leaves across 2 task groups, one concern: a spec review that exists and a transition that proves it happened. Assessed `exception` rather than `standard`, honestly and with the reason stated: E-02 authors a workflow body and E-04 adds a lifecycle gate bearing on 26 existing specs, which are two independent high-blast-radius surfaces in one plan. They are nonetheless one plan because the gate is meaningless without the review that satisfies it, and the review is unattested without the gate: shipping either alone leaves the integrity hole this plan exists to close. E-01 is separate and first because the shape decision determines E-02's entire form. E-05 and E-06 are separate because enumeration and end-to-end proof have different failure modes: a discovery bug returns the wrong set, an end-to-end bug corrupts a lifecycle.

Open questions: OQ-01 (workflow shape) is non-blocking and owned by E-01, which must decide it with cited evidence. OQ-02 (record versus history receipt) is RESOLVED as requiring a record, with the reason recorded so the weaker option is not adopted later. No blocking question remains.

This plan is `to-review` and requires explicit human approval before execution. It has TWO hard prerequisites, `- Item-Dependencies: executed:eyh1fu, executed:6ypimw`: it cannot file a conforming spec review until the record can name a spec (`eyh1fu`), and it supplies the specs enumeration that `6ypimw`'s type-aware predicate was shaped to consume. Both edges are `executed:` rather than `exists:` because this plan needs their behavior in place, not merely their files present.

Scope fence: touch ONLY the paths in Scope-Paths. Do NOT change the review record's subject fields (`eyh1fu` did that). Do NOT re-edit the needs-review predicate's logic (`6ypimw` owns it); this plan supplies enumeration. Do NOT register `--type` on the runners (`uyeko5`). Do NOT write `- Readiness:` onto a spec. Do NOT hand-edit any spec's `- Status:` or workflow history; use `aw specs set`/`aw specs note`. Do NOT run `aw ipd lint` against a spec. Do NOT make a missing review an error for plans. Do NOT manufacture review records for the 20 grandfathered specs. Do NOT promote one of the 2 real draft specs to demonstrate this plan; use a fixture. Do NOT hand-edit a `_generated/` file. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at, from the PRIMARY checkout. The load-bearing evidence is (1) V-02's NEGATIVE proof of the three prohibitions, because a spec review can complete successfully while having corrupted the spec exactly as `/plan-review` would, and plan-review's IPD-lint preflight is guarded such that a skipped gate looks like a passed one; and (2) V-04's before/after conforming-spec count, because retroactive invalidation of the specs tree is this plan's main risk and a claim would hide it. Do NOT describe the attestation as proving review QUALITY: it proves a review occurred and was recorded, and spec `25kzda` 6.1 already states that limit. Do NOT claim `aw check all` passes; the bar is no-worsening against your own fresh baseline. Do NOT report `--type spec` as operator-reachable unless `uyeko5` has landed the flag; say which.

Execution contract: RE-READ the plan-review body, `specs.py`, and `attention_contract.py` immediately before editing and locate every site BY SYMBOL, never by the line numbers in this plan. If E-01 chooses generalization, `plan-review` and `plan-review-long` must be changed IN LOCKSTEP; changing one is a fork. Commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption, since a failed hook invalidates the check. If a co-worker's in-flight change cannot be safely combined with an edit, STOP and report rather than overwriting.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
