# IPD: Re-measure spec 25kzda's infrastructure paragraph and stop it going stale a third time

- Date: 2026-09-08
- Kind: child
- Concern: SPEC `25kzda`'s "STILL NET-NEW and to be built" ENUMERATION HAS GONE STALE TWICE AND IS STALE AGAIN NOW, and its whole function is to stop a graduating Set from rebuilding shipped machinery. The paragraph (`:22-31`) was itself a CORRECTION, added in `a59f2c5` on 2026-08-30 because the original text "declared ALL of the below net-new and nonexistent, which is no longer true and would mislead a graduating Set into rebuilding shipped machinery". RE-MEASURED AT HEAD, item by item, and the paragraph is unchanged since the item was filed:
  1. `From-Spec` "(absent from `ipd_schema.META_RECOGNIZED`)" is FALSE. Measured: `META_FROM_SPEC in META_RECOGNIZED` is `True`. Shipped with `check.from-spec-dangling`.
  2. `AW-Run:`/`AW-Item:` trailers "(the ledger is built but UNWIRED)" HOLDS. Measured: zero commits in the last 400 across all refs carry an `AW-Run` trailer. Note the WRITER machinery exists (`git_commit_helper`), so the honest wording is that the trailers are built and unpassed, which is what plan `wao266` (from `a8eufb`) now addresses.
  3. prompt `Run contract` block HOLDS. Measured: zero occurrences of "Run contract" in either host driver.
  4. per-host capability descriptor is MORE STALE THAN THE ITEM SAYS, and this is the finding that most changes the fix. The item calls it "MISLEADING rather than false" because `hostcap-01` (`mjx7ne`) was then PENDING and scoped to EXTEND. `mjx7ne` HAS SINCE EXECUTED. `HostSandboxCapabilities` now carries THIRTEEN fields including the three runner-safety ones the item said "genuinely does not exist" (`supports_commit_gateway`, `supports_deny_push`, `supports_fresh_verifier_session`). So the descriptor is not partially shipped; it is shipped, and the correct statement is that two of its fields are declared-and-never-probed by deliberate decision.
  5. `aw hooks install` "(no such verb today)" HOLDS. Measured: the verb does not resolve.
  SO TWO OF FIVE ARE NOW WRONG, one in each direction of harm: item 1 would send a Set to add a SECOND `From-Spec` recognition path, and item 4 would send it to CREATE a capability module that exists, which is precisely the defect that killed `a54m79` and forced `hostcap-01` to be written in the first place.
  THE DEEPER PROBLEM IS THE ONE THE ITEM NAMES AND THIS PLAN MUST DECIDE, not the two wrong entries. A spec paragraph that enumerates "what is not built yet" acquires a maintenance burden nothing enforces, and it has now decayed twice in nine days. The item offers three options and its own audit supplies the evidence for choosing: (a) keep correcting it, (b) delete the enumeration and let plans measure current state themselves, "which is what every recent plan review actually does", or (c) keep it but mark it explicitly as a point-in-time snapshot with its measurement date and commit. The audit's finding that reviews re-measure regardless means the list's real function is to WARN, not to inform.
  THE AUDIT HALF IS CLOSED AND MUST NOT BE REDONE. The item searched all 24 specs (now 28) for stale-existence claims and found hits in exactly ONE: `25kzda` with 4. `prompt-purity-lint`, `research-lifecycle-reliability`, `c4gd2h`, `external-delivery-and-skills` and `clean-delta-and-tracking-modes` all scored 0. So this is confined to one spec and no spec family inherited it.
- Scope: Correct the two factually wrong entries in `25kzda`'s infrastructure paragraph, and decide what stops it decaying a third time. This is a FACTUAL-STATUS correction plus a durability decision; it changes NO design and the spec stays `approved`, on the `a59f2c5` precedent. EXCLUDES re-running the 24-spec audit (closed), and excludes building any of the five enumerated items.
- Scope-Paths: .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: to-review
- Set: specfresh
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: wenmg4
- From-Backlog: sd2wz5

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `sd2wz5`. All five enumerated claims were re-measured at HEAD rather than trusted, and the paragraph is unchanged since filing. FOUR OF FIVE MATCH THE ITEM EXACTLY: `From-Spec` is recognized (item 1 stale, as filed); trailers still unpassed (item 2 holds, 0 in 400 commits); no `Run contract` block (item 3 holds, 0 hits in both drivers); `aw hooks install` absent (item 5 holds). ITEM 4 IS MORE STALE THAN THE ITEM RECORDS, which changes the fix: the item calls the capability descriptor "MISLEADING rather than false" on the basis that `mjx7ne` was PENDING and would EXTEND it. `mjx7ne` HAS EXECUTED, and `HostSandboxCapabilities` now carries 13 fields including all three runner-safety fields the item said "genuinely does not exist", two of which are declared-and-never-probed by deliberate decision. So the honest correction for item 4 is stronger than the item's suggested rewording. THE AUDIT HALF IS CLOSED and is explicitly not redone: 28 specs now (was 24), hits still confined to `25kzda`. This plan carries no `Blocks-Release` because the item carries none; it is `Work-Kind: chore` and the maintainer did not gate it.

## Goal

Make a paragraph whose only job is preventing duplicated work stop causing it, and decide whether a hand-maintained "not built yet" list should exist at all.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure before editing a spec

- [ ] E-01 RE-MEASURE ALL FIVE ENUMERATED ITEMS AT YOUR HEAD AND WRITE THE RESULTS DOWN, because this paragraph's whole failure mode is being edited from a stale reading. Do not trust this plan's measurements; they will themselves be days old.
  THE FIVE, WITH THE EXACT CHECK FOR EACH: `From-Spec` -> `ipd_schema.META_FROM_SPEC in ipd_schema.META_RECOGNIZED`; the trailers -> `git log --format='%(trailers:key=AW-Run,valueonly)'` over recent history, counting non-empty; the prompt `Run contract` block -> grep both host drivers; the capability descriptor -> enumerate `HostSandboxCapabilities`'s dataclass fields and check `mjx7ne`'s lifecycle directory; `aw hooks install` -> attempt the verb and read its exit.
  AUTHORING BASELINE, for comparison only: item 1 STALE (recognized), item 2 HOLDS (0 of 400), item 3 HOLDS (0 hits), item 4 STALE AND STRONGER (13 fields, `mjx7ne` executed), item 5 HOLDS (verb absent).
  IF AN ENTRY HAS MOVED AGAIN, THAT IS THE POINT, NOT AN OBSTACLE. Record it and correct it in E-02. A third decay between this plan's authoring and its execution is the strongest possible argument for E-03's durability decision, so report it prominently rather than quietly folding it in.
  - Depends on: none
  - Expected outcome: a per-item measured verdict at your HEAD with the command used for each, and an explicit note of any entry that moved since this plan was authored.
  - Execution state: pending

### Task group 2: correct the facts

- [ ] E-02 AMEND ONLY THE FACTUALLY WRONG ENTRIES, and change no design. This is the same class of edit as `a59f2c5` itself, which is the precedent that keeps the spec `approved`.
  MOVE `From-Spec` OUT OF "STILL NET-NEW" and into the already-shipped list, citing the commit that landed it together with `check.from-spec-dangling`. The item names `8c437188` (merged `b0eb74e6`); VERIFY that sha resolves at your HEAD before citing it, since a cited sha that does not resolve is worse than no citation.
  REWORD THE CAPABILITY DESCRIPTOR ENTRY TO MATCH WHAT SHIPPED, which is stronger than the item's suggestion. It is not "partially shipped": `mjx7ne` executed and the descriptor now carries all three runner-safety fields. The honest statement is that the descriptor EXISTS and must be EXTENDED not created, that `host_sandbox_profile.py` owns it, and that `supports_commit_gateway`/`supports_deny_push` are DECLARED AND NEVER PROBED by deliberate decision so they fail closed. Naming that last part matters, because a Set reading "exists" might otherwise assume those two are usable.
  LEAVE ITEMS 2, 3 AND 5 ALONE if E-01 confirms they hold. Do not "improve" wording that is still true; every touch of this paragraph is a chance to introduce a new inaccuracy.
  SHARPEN ITEM 2 ONLY IF E-01 SUPPORTS IT: the trailers' WRITER machinery exists while nothing passes them, and plan `wao266` (from `a8eufb`) now owns the wiring. If that is still true, saying "built but never passed, owned by `wao266`" is more useful than "built but UNWIRED" and is still a factual-status edit rather than a design change.
  - Depends on: E-01
  - Expected outcome: exactly the wrong entries amended with resolving citations; items that still hold are untouched; no design text changed; the spec remains `approved`.
  - Execution state: pending

- [ ] E-03 DECIDE WHAT STOPS THE THIRD DECAY, and implement that decision in the same edit. This is the item's real question and the reason it is worth a plan rather than a one-line correction.
  THE THREE OPTIONS, with the evidence the item's own audit supplies. (a) KEEP CORRECTING IT: rejected by track record, since it has decayed twice in nine days and nothing enforces the maintenance. (b) DELETE THE ENUMERATION and let plans measure current state, which the audit observes "is what every recent plan review actually does"; the cost is losing the WARNING that stopped `a54m79`'s duplication class. (c) KEEP IT AS AN EXPLICIT POINT-IN-TIME SNAPSHOT carrying its measurement date and commit, so a reader knows to re-verify.
  (c) IS THE DEFENSIBLE DEFAULT AND (b) IS THE HONEST RUNNER-UP. (c) preserves the warning function while making the staleness self-evident rather than invisible, and it costs one sentence. (b) is genuinely attractive because it removes the burden entirely, but it deletes the only text that tells a graduating Set "consume, do not rebuild", and that text has demonstrably prevented at least one duplication. Whichever is chosen, the choice must be RECORDED IN THE SPEC, not just in this plan, or the next reader re-litigates it.
  IF (c): the snapshot must carry a DATE AND A COMMIT and must say "re-verify before relying on this", so the paragraph's own instruction defeats its staleness. State plainly that a Set MUST measure rather than trust it.
  IF (b): the deletion must be replaced by a one-line instruction to measure current state, or the spec loses the warning entirely and this plan reintroduces the `a54m79` risk it exists to prevent.
  - Depends on: E-02
  - Expected outcome: one of the three options implemented in the spec text with its reasoning recorded there, and under (c) or (b) the warning function preserved rather than dropped.
  - Execution state: pending

### Task group 3: record it the tooled way and prove nothing else moved

- [ ] E-04 APPEND THE CORRECTION VIA `aw specs note`, NOT BY HAND, and prove the spec's status and design are untouched.
  USE THE TOOLED VERB: `aw specs note <path> --message ...` appends a workflow-history record WITHOUT changing status, which is exactly this edit's shape. The precedent is in the same spec: its `2026-09-07 note (aw specs)` entry records a maintainer-ruled amendment at length. Do not hand-append a history line; the setter owns that format.
  DO NOT CHANGE `- Status:`. The spec is `approved` and a factual-status correction is not a design change, on the `a59f2c5` precedent. An agent may not set a spec `approved` or `implemented` in any case, so touching status here would be both wrong and forbidden.
  PROVE THE DESIGN TEXT IS UNCHANGED. Paste a diff scoped to the spec showing only the infrastructure paragraph and the history region moved. In particular, DO NOT touch Section 4.2's finding-code table: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` under a byte-equality test, so an incidental edit there IS a code change and would fail the suite.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA. Baseline measured on main 2026-09-08: `1 failed, 5648 passed`, the failure being the pre-existing `tests/test_orchestrator_retirement.py` case. Inside a lane worktree roughly 32 further failures are environmental. Criterion: AFTER minus BEFORE is EMPTY. A spec-text edit should move nothing, so any delta is a signal that a byte-pinned region was touched.
  - Depends on: E-03
  - Expected outcome: the correction recorded via `aw specs note`; status unchanged at `approved`; a scoped diff proving only the paragraph and history changed; Section 4.2 untouched; bare-suite delta empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE PARAGRAPH IS ITSELF A CORRECTION. `a59f2c5` (2026-08-30) added it precisely because the original claimed everything was net-new and "would mislead a graduating Set into rebuilding shipped machinery". That is the precedent for a factual-status edit keeping the spec `approved`.
- IT HAS NOW DECAYED TWICE IN NINE DAYS, which is the argument against option (a).
- `aw specs note` IS THE TOOLED SURFACE for exactly this: it appends a workflow-history record WITHOUT changing status. The same spec already carries a long `2026-09-07 note (aw specs)` entry as precedent.
- AN AGENT MAY NOT SET A SPEC `approved` OR `implemented`. Status must not be touched here, which aligns with the edit being factual rather than design.
- SECTION 4.2's TABLE IS BYTE-PINNED into `run_evidence.RUN_FINDING_CODES`, so an incidental edit there is a code change that fails the suite. Stay out of it.
- THE AUDIT HALF IS CLOSED: stale-existence claims are confined to this one spec (28 specs scanned now, was 24 at filing). Do not re-run it.
- ITEM 4 MOVED SINCE FILING: `mjx7ne` executed, so `HostSandboxCapabilities` carries 13 fields including the three runner-safety ones, two of them declared-and-never-probed by deliberate decision.
- ITEM 2's OWNER NOW EXISTS: plan `wao266` (from `a8eufb`) owns passing the trailers at the one shared commit call site.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | item 1 is FALSE | `From-Spec` is listed as "absent from `ipd_schema.META_RECOGNIZED`". Measured `True`. A Set reading this could add a SECOND recognition path. | `META_FROM_SPEC in META_RECOGNIZED` -> True |
| F-2 | HIGH | item 4 is FALSE AND MORE STALE THAN THE ITEM RECORDS | The item calls it "MISLEADING" because `mjx7ne` was PENDING. `mjx7ne` has EXECUTED and the descriptor carries 13 fields including all three runner-safety ones the item said do not exist. Reading it as net-new invites creating a parallel module, the exact defect that killed `a54m79`. | `dataclasses.fields(HostSandboxCapabilities)` -> 13; `mjx7ne` in `executed/` |
| F-3 | MEDIUM | item 2 HOLDS, with a sharper truth available | Zero `AW-Run` trailers in the last 400 commits across all refs. The WRITER exists (`git_commit_helper`) and nothing passes it; plan `wao266` now owns the wiring. | trailer scan; `wao266`'s scope |
| F-4 | MEDIUM | item 3 HOLDS | Zero occurrences of "Run contract" in `oc_runipd.py` and `agy_runipd.py`. | grep both drivers |
| F-5 | MEDIUM | item 5 HOLDS | `aw hooks install` does not resolve. | verb attempted |
| F-6 | HIGH | the paragraph's function is anti-duplication | Its own preamble says the original text "would mislead a graduating Set into rebuilding shipped machinery", so a stale entry causes exactly the harm the paragraph exists to prevent. | spec `:22-24` |
| F-7 | MEDIUM | nothing enforces the maintenance | Two decays in nine days, and no test, check or gate reads this paragraph. That is why E-03 is a durability decision rather than another correction. | `a59f2c5` then this item |
| F-8 | MEDIUM | reviews re-measure anyway | The item's audit observes that letting plans measure current state "is what every recent plan review actually does", so the list's real function is to WARN rather than to inform. | the item's own audit conclusion |
| F-9 | LOW | the audit half is closed and confined | Stale-existence claims hit only `25kzda` (4); five other live specs scored 0. Corpus grew 24 -> 28 with no new offender. | the item's audit; re-counted at HEAD |
| F-10 | LOW | a cited sha must be verified | The item cites `8c437188` (merged `b0eb74e6`) for `From-Spec`. E-02 must confirm it resolves before writing it into an approved spec. | E-02's requirement |

## Proposed changes (ordered, validatable)

1. Re-measure all five entries at HEAD and record any that moved again (E-01).
2. Amend only the wrong entries, with verified citations, leaving true entries untouched (E-02).
3. Implement a durability decision so the paragraph cannot decay invisibly a third time (E-03).
4. Record the correction via `aw specs note`, prove status and design unchanged, keep Section 4.2 untouched (E-04).

## Deferred / out of scope (with reason)

- RE-RUNNING THE 24-SPEC AUDIT. Closed by the item and re-confirmed: claims are confined to `25kzda`. Re-running it would be work whose answer is already recorded.
- BUILDING ANY OF THE FIVE ENUMERATED ITEMS. This plan corrects a STATUS description. The trailers are `wao266`'s (from `a8eufb`); `aw hooks install` and the prompt `Run contract` block have no owner yet and are NOT filed by this plan, because inventing scope for them from a spec paragraph is how the false-premise problem started.
- CHANGING ANY DESIGN TEXT IN `25kzda`. Factual-status only, on the `a59f2c5` precedent, which is also what keeps it `approved`.
- TOUCHING SECTION 4.2's FINDING-CODE TABLE. Byte-pinned into `run_evidence.RUN_FINDING_CODES`; an incidental edit is a code change.
- CHANGING THE SPEC'S STATUS. It stays `approved`. An agent may not set `approved` or `implemented` regardless.
- FILING ITEMS FOR THE STILL-UNBUILT ENTRIES. Tempting and out of scope: items 3 and 5 genuinely do not exist, but whether they are WANTED is a design question this plan has no mandate to answer, and a spec listing something is not by itself a decision to build it.
- AUDITING WHETHER OTHER SPECS ENUMERATE "not built yet" IN FUTURE. E-03's decision may imply a general convention, but generalizing it across 28 specs is a separate change with its own review surface.

## Scope check

- Over-scope: none. One spec file, one paragraph, one history note.
- Scope-Paths justification: `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` is the ONLY file this plan edits. It is declared deliberately and prominently, because the runners announce declared spec edits before a run starts and the finalize scope gate reconciles them; a plan amending a spec it never declared is exactly the drift that declaration requirement exists to catch. NO code path is in scope: this plan changes a description of code, not code, and if the executor concludes a code change is needed, that is a scope-widening finding to report rather than to make.
- Under-scope, stated rather than left as `none`: this plan does not re-run the audit, does not build any enumerated item, changes no design text, does not touch Section 4.2, does not change the spec's status, files no items for the unbuilt entries, and does not generalize its convention across other specs. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY. A spec-text edit should move NOTHING, so any delta means a byte-pinned region was touched.
- THE FIVE PER-ITEM MEASUREMENTS (E-01) pasted with the command used for each, and an explicit statement of any entry that moved since this plan was authored.
- THE CITED SHA VERIFIED to resolve before it is written into the spec.
- A SCOPED DIFF of the spec showing ONLY the infrastructure paragraph and the workflow-history region changed.
- PROOF SECTION 4.2 IS UNTOUCHED, and the byte-equality test over `RUN_FINDING_CODES` passing.
- THE SPEC'S `- Status:` shown unchanged at `approved` before and after.
- `aw check specs` before and after, per-rule, showing no new finding.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean, and no em or en dash introduced into the spec.

## Spec / documentation sync

THIS PLAN IS ITSELF A SPEC AMENDMENT, which is why `25kzda` is declared in `Scope-Paths` and why that declaration is the plan's most important structural feature. The runners announce declared spec edits at run start and the finalize gate reconciles what was actually changed against what was declared.

WHY THE AMENDMENT IS LEGITIMATE WITHOUT A STATUS CHANGE: `a59f2c5` set the precedent that a factual-status correction to this paragraph is not a design change, and the spec stayed `approved` through it. This plan makes the same class of edit. The `2026-09-07 note (aw specs)` entry in the same spec shows the recording mechanism.

E-03's DECISION MUST BE RECORDED IN THE SPEC ITSELF, not only in this plan's history. If the enumeration survives as a dated snapshot, the spec must say so and must instruct a reader to re-verify; if it is deleted, the spec must retain a one-line instruction to measure current state. Either way the next reader must find the reasoning without reading this plan.

No OTHER spec is amended. The item's audit established that stale-existence claims are confined to this one spec, so there is no sibling correction owed.

## Open questions

### OQ-01: Should the "not built yet" enumeration survive at all?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: GENUINELY THE MAINTAINER'S CALL, but deliberately NON-BLOCKING because the plan delivers value under every answer: E-01 and E-02 correct two false statements regardless, and only E-03's shape depends on this. The evidence is balanced and worth stating. FOR DELETION: the paragraph has decayed twice in nine days, nothing enforces it, and the item's own audit found that plan reviews re-measure current state anyway, so the list informs nobody who was going to check. FOR KEEPING IT AS A DATED SNAPSHOT: its preamble records that the ORIGINAL version's inaccuracy "would mislead a graduating Set into rebuilding shipped machinery", and the `a54m79` duplication it warns about actually happened, so the warning has demonstrated value even when its details rot. The judgement is how much a maintainer wants a hand-maintained fact list in an approved spec, which is a preference about their own review process. E-03 defaults to the dated snapshot as the option that preserves the warning at the lowest cost, and requires the reasoning to be written into the spec either way.

### OQ-02: Should the still-unbuilt entries get backlog items?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, NOT FROM THIS PLAN. Items 3 (`Run contract` block) and 5 (`aw hooks install`) genuinely do not exist, and filing work for them from a spec paragraph would repeat the exact error this plan is fixing: treating an enumeration as a mandate. A spec LISTING something is not a decision to build it, and neither entry has a recorded maintainer decision behind it. Item 2's trailers already have an owner (`wao266`, from `a8eufb`) and item 4 is shipped. So the correct output is an accurate description; whether the two genuine gaps are WANTED is a separate question for a human, and this plan says so rather than manufacturing scope.

### OQ-03: Does correcting an approved spec require re-approval?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, ON THE `a59f2c5` PRECEDENT, and the item states the rule plainly: "the spec is `approved`, so it stays approved: a factual-status note is not a design change". `a59f2c5` made exactly this class of edit to exactly this paragraph while the spec remained approved. The independent constraint reinforcing this: an agent may not set a spec `approved` at all (that requires an attested human act), so any reading that demanded re-approval would make the correction unperformable by the agent doing it, which cannot be right for a factual fix. The boundary E-02 must respect is that this licence covers FACTS only: the moment an edit changes what the spec REQUIRES, it is a design change and needs the maintainer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the ACTUAL output for all five measurements with the command used for each: the `META_RECOGNIZED` membership test, the `AW-Run` trailer scan with its count and window, the `Run contract` grep over both drivers, the `HostSandboxCapabilities` field enumeration plus `mjx7ne`'s directory, and the `aw hooks install` attempt with its unpiped exit code. State explicitly whether any entry moved since this plan was authored, and if so say so prominently as evidence for E-03.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the amended paragraph in full. Confirm by quoting that `From-Spec` now sits in the shipped list and that the capability-descriptor entry says the descriptor EXISTS, must be extended not created, names `host_sandbox_profile.py`, and states that two fields are declared-and-never-probed. Paste proof the cited sha RESOLVES (`git log -1 <sha>`). Paste a diff showing items that still hold were NOT reworded except where E-01 supported sharpening item 2.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: state which of the three options was implemented and paste the spec text implementing it. If the snapshot survives, quote the date, the commit and the re-verify instruction. If the enumeration was deleted, quote the replacement instruction to measure current state, and confirm in one sentence that the anti-duplication warning was preserved rather than dropped. Confirm the reasoning is recorded IN THE SPEC, not only in this plan.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `aw specs note` command and its output. Paste the spec's `- Status:` line before and after, both `approved`. Paste a scoped `git diff` of the spec proving only the infrastructure paragraph and the history region changed, and confirm Section 4.2's table is byte-identical. Paste the byte-equality test over `RUN_FINDING_CODES` passing. THEN paste the BARE `python3 -m pytest` summary lines before and after and state the failure-set delta explicitly; a nonempty delta on a spec-text edit means a pinned region was touched.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO `Blocks-Release` because the backlog item carries none: it is `Work-Kind: chore` and the maintainer did not gate it. That is recorded explicitly so a reader does not assume the gate was dropped. The defect's harm is real (a Set could duplicate shipped machinery) but it is a documentation-accuracy problem, not shipped-behavior breakage.

OQ-01 IS OPEN BUT NON-BLOCKING BY DESIGN. E-01 and E-02 correct two false statements under any answer; only E-03's shape depends on the maintainer, and it defaults to the lowest-cost option that preserves the warning.

EXECUTION CONTRACT. Commit only the spec file, path-scoped (`git commit -m msg -- <path>`); never `git add -A` and never push. Use `aw specs note` rather than hand-appending history. Do NOT change the spec's `- Status:`, and do NOT touch Section 4.2's finding-code table, which is byte-pinned into `run_evidence.RUN_FINDING_CODES`. Verify every sha before citing it in an approved spec. Re-locate every symbol by NAME rather than by the line numbers cited here. Write no em or en dashes into the spec. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook, since `pre-commit` can leave another agent's paths in the index.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the five per-item measurements and the scoped diff proving no design text moved.
