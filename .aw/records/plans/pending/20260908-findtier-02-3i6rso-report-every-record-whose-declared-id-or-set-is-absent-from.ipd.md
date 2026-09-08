# IPD: Report every record whose declared Id or Set is absent from its filename

- Date: 2026-09-08
- Kind: child
- Concern: THERE IS NO SIGNAL FOR A RECORD WHOSE DECLARED IDENTITY IS ABSENT FROM ITS FILENAME, so the exception set that forces `aw find`'s content fallback is invisible and cannot be shown to be shrinking. MEASURED at HEAD: NINE tracked records carry a declared `- Id:` that does not appear in their own filename, and `aw check specs` reports ZERO naming findings for the grandfathered ones. Verified the tolerance directly: `artifact_naming.is_clustered_conformant` returns `False` for both `20260808-0004-00-plans-adopter-orchestrator.ipd.md` and `20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, yet neither is reported, because the check engine's naming rule deliberately exempts legacy shapes. So the exception set exists, is load-bearing for `find`'s design, and nothing counts it.
  WHY THAT MATTERS RATHER THAN BEING TIDINESS, and it is the item's own argument: "the long-term prize is being able to TRUST filenames and retire the content fallback, which is only reachable if the exception set is visible and shrinking." Order 01 (`826o13`) must keep a mandatory content fallback precisely BECAUSE these nine exist. Without a report, nobody can tell whether the set is nine or ninety, or whether it grew last week, so the fallback can never be retired on evidence.
  THE NINE ARE NOT ALL THE SAME THING, which is the finding that shapes this plan and which the item did not have. EIGHT are genuine pre-id6-grammar or grandfathered names: plans `4o5lt9`, `wvlk84`, `lus9ou`, `8q6yr9`, `7qx7ys` and specs `4w7d6s`, `25kzda`, `5tapom`. The NINTH is `uyeko5` "declared" by research prompt `27rjro`, which is a QUOTED EXAMPLE in that document's body, not a real declaration; it is the parser artifact owned by `cqytxf`/`76w6mq`. So a report built today would show 9 and should show 8, and the difference is not a naming problem at all. A report that conflates them would send someone to rename a research prompt whose name is already correct.
  THE ITEM IS EXPLICIT THAT THIS IS ADVISORY AND NOT AUTO-RENAME, and both reasons are real constraints rather than caution: `executed/` plan bodies are immutable by policy, and the grandfathered specs are a documented decision. `25kzda` in particular is cited constantly across the repository, so renaming it would break every citation for a cosmetic gain. Hence "EXPLICITLY NOT auto-rename: each rename is a maintainer call per record."
  THE ITEM ALSO NAMES A MEASURED FALSE-POSITIVE SOURCE that this report must handle or it will lie on its first run: quoting. One apparent miss in the item's own audit was a phantom, because front matter read `` set: `awoptimize` `` WITH BACKTICKS. Compare stripped values or the report invents drift.
- Scope: Add an ADVISORY report naming every record whose declared `- Id:` or `- Set:` is absent from its filename, with the exact `aw rename` that would fix each, and with the quoting normalization that stops phantom findings. EXPLICITLY EXCLUDES auto-renaming anything, changing the check engine's legacy exemption into an error, and the resolver work in Order 01.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_name_identity_report.py
- Item-Dependencies: none
- Status: to-review
- Set: findtier
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 3i6rso
- From-Backlog: f8m2z2

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `f8m2z2` as Order 02, covering the item's second added requirement ("RAISE non-conforming filenames"). The item's premise was verified rather than trusted: `is_clustered_conformant` returns False for both a legacy plan name and a legacy spec name, while `aw check specs` reports ZERO naming findings, so the tolerance is real and the exception set is genuinely invisible. THE COUNT IS NINE, NOT THE ITEM'S EIGHT, AND THE NINTH IS NOT A NAMING PROBLEM: `uyeko5` is a QUOTED EXAMPLE in research prompt `27rjro`'s body, the parser artifact owned by `cqytxf`/`76w6mq`, so a report built today would show 9 and should show 8. That distinction is now E-02's explicit job, because conflating them would send someone to rename a correctly-named research prompt. Split from Order 01 because this is a reporting surface with its own test bed, and because it is what makes Order 01's mandatory content fallback retirable on evidence rather than permanently assumed.

## Goal

Make the set of records whose filename cannot be trusted countable, so the content fallback can eventually be retired on evidence instead of assumed forever.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure the real set before reporting on it

- [ ] E-01 ENUMERATE THE EXCEPTION SET AT YOUR HEAD AND CLASSIFY EVERY MEMBER, before writing any report. The count is the deliverable's whole point, so it must be established rather than inherited.
  SCAN EVERY TRACKED RECORD, not just plans: compare each file's declared `- Id:` and `- Set:` against its own filename. The authoring baseline is NINE records for the `- Id:` case, and the `- Set:` case must be measured separately since a record can carry a correct id6 and a mismatched setid.
  CLASSIFY EACH INTO ONE OF THREE BUCKETS, because the remedies differ completely: (a) LEGACY GRAMMAR, a pre-id6 or grandfathered name whose rename is a maintainer call (the eight); (b) PARSER ARTIFACT, where the declared value comes from a QUOTED EXAMPLE in the body rather than front matter (the `uyeko5`/`27rjro` case, owned by `cqytxf`/`76w6mq`); (c) GENUINE DRIFT, a modern-grammar file whose name and metadata simply disagree, which would be a real defect.
  IF BUCKET (c) IS NON-EMPTY, REPORT IT PROMINENTLY. None was found at authoring, and a genuine drift case would be a live naming defect rather than a grandfathering question, so it deserves its own attention rather than being folded into an advisory count.
  RE-MEASURE AFTER CHECKING WHETHER `76w6mq` HAS LANDED. If it has, bucket (b) should be EMPTY and the count should be eight. Say which state you observed.
  - Depends on: none
  - Expected outcome: the exception set enumerated at your HEAD with every member classified into legacy / parser-artifact / genuine-drift, the `- Set:` case measured separately, and `76w6mq`'s status stated.
  - Execution state: pending

- [ ] E-02 MAKE THE REPORT DISTINGUISH THE THREE BUCKETS RATHER THAN EMITTING ONE COUNT, because a single number would be actively misleading on its first run.
  THE PARSER-ARTIFACT BUCKET MUST NOT BE REPORTED AS A NAMING PROBLEM. `27rjro`'s filename is CORRECT; its declared-`- Id:` reading is a bug in the reader that `76w6mq` fixes. Reporting it as "rename this file" would send an operator to damage a correct name, and the item's own instruction for that document (via `cqytxf`) is that "the fix is in the reader, not the doc."
  THE CLEANEST IMPLEMENTATION IS TO READ IDENTITY THE WAY THE FIXED READER WILL. If `76w6mq` has landed, consume its metadata-region-bounded reader and bucket (b) disappears by construction. If it has NOT landed, the report must EXCLUDE body-quoted declarations explicitly and say why in its own output, so it does not carry a known-false finding.
  NORMALIZE QUOTING, which the item records as a measured phantom: a backtick-quoted `` set: `awoptimize` `` produced a false miss in its audit. Compare stripped values.
  - Depends on: E-01
  - Expected outcome: a report that separates legacy-grammar records from parser artifacts and genuine drift, never reporting a correctly-named file as needing a rename, with quoting normalized.
  - Execution state: pending

### Task group 2: make it advisory and actionable

- [ ] E-03 EMIT IT AS AN ADVISORY WITH THE EXACT REMEDY PER RECORD, and do NOT promote the legacy exemption to an error.
  ADVISORY IS THE ITEM'S EXPLICIT REQUIREMENT and the reason is measured: `executed/` plan bodies are immutable by policy and the grandfathered specs are a documented decision, so an error-severity rule would fail the tree for states the maintainer deliberately chose. `check_engine`'s own precedent is the same shape: its review-escalation rule keeps the ABSENT case SILENT because a fail-closed absent case "would mass-fail the entire corpus on day one".
  NAME THE EXACT `aw rename` PER RECORD, which is what makes the report actionable rather than a lament. The item asks for "the exact `aw rename` that would fix it". Note the verb differs by type (`aw rename plans` versus `aw rename specs`) and that `--to-id6` exists for adopting the id6 grammar; get the per-record command right, because a wrong suggested command is worse than none.
  DO NOT TOUCH THE EXISTING LEGACY EXEMPTION. `check_engine`'s naming rule deliberately exempts legacy shapes, and the spec-name cutover deliberately grandfathers pre-cutover specs. This plan ADDS a report; it does not reclassify what is already tolerated.
  RESPECT THE SPEC CUTOVER RULE. Specs adopted the id6 grammar going forward with pre-cutover names grandfathered, so a pre-cutover spec appearing in this report is EXPECTED and its remedy line should say the rename is optional and a maintainer call, not overdue.
  - Depends on: E-02
  - Expected outcome: an advisory-severity report with a correct per-record `aw rename` suggestion, no change to the existing exemption, and pre-cutover specs described as optional rather than overdue.
  - Execution state: pending

- [ ] E-04 DECIDE WHERE THE REPORT SURFACES, and choose a place that cannot mass-fail CI.
  THE CANDIDATES: a new advisory `check.*` rule in the full sweep; a dedicated flag on `aw check`; or `aw doctor` only. Each has a different blast radius, and the deciding constraint is that `aw check` is FAIL-CLOSED in CI, so even an advisory must be verified not to change the exit code.
  MEASURE THE FINDING COUNT BEFORE CHOOSING, and state it. Nine records is small enough that a sweep rule is defensible; if E-01's `- Set:` scan turns up many more, a flag or doctor-only becomes the better answer.
  IF A NEW RULE CODE IS ADDED IT MUST BE REGISTERED. `check_engine`'s `RuleSpec` table assigns severity, assurance class and determinism; an unregistered code carries no contract. Register it as a warning, matching the advisory decision.
  VERIFY THE EXIT CODE IS UNCHANGED for a tree whose only new findings are these. That is the single most important check in this item, because an advisory that flips CI red is not an advisory.
  - Depends on: E-03
  - Expected outcome: a chosen surface with the finding count that justified it, a registered rule code if one was added, and proof `aw check`'s exit code is unchanged.
  - Execution state: pending

### Task group 3: prove it counts the right things

- [ ] E-05 PROVE THE REPORT IS CORRECT ON ALL THREE BUCKETS AND COSTS NOTHING ELSE.
  FIVE ASSERTIONS MINIMUM, from fixtures: a legacy-named record IS reported with the right `aw rename`; a conformant modern record is NOT reported; a record whose declared value appears only in a QUOTED body block is NOT reported as a naming problem; a backtick-quoted front-matter value produces NO phantom finding; and a genuine-drift record (modern grammar, mismatched metadata) IS reported and distinguished from legacy.
  BUILD FIXTURES, NOT LIVE-TREE ASSERTIONS. The nine live records will change: `76w6mq` removes one, and four agents are authoring concurrently. Use the live tree only for the count in evidence.
  ASSERT THE LIVE COUNT AS EVIDENCE, SEPARATELY, and name every member. That count is the artifact a future reader compares against to see whether the set is shrinking, which is the item's stated long-term prize.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA. Baseline measured on main 2026-09-08: `1 failed, 5648 passed`, the failure being the pre-existing `tests/test_orchestrator_retirement.py` case. Inside a lane worktree roughly 32 further failures are environmental. Criterion: AFTER minus BEFORE is EMPTY.
  COMPARE `aw check` PER RULE, never by total, since several counts drift for unrelated reasons.
  - Depends on: E-04
  - Expected outcome: five fixture assertions passing, the live count recorded with members named, per-rule comparison showing only the new code appearing, and an empty bare-suite delta.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE TOLERANCE IS REAL AND MEASURED: `is_clustered_conformant` returns `False` for a legacy plan name and a legacy spec name, while `aw check specs` reports ZERO naming findings, because the naming rule deliberately exempts legacy shapes.
- THE EXCEPTION SET IS NINE FOR THE `- Id:` CASE at HEAD, of which EIGHT are legacy/grandfathered and ONE is a parser artifact.
- THE NINTH IS NOT A NAMING PROBLEM: `uyeko5` comes from a QUOTED EXAMPLE in `27rjro`'s body; `cqytxf`'s instruction is that "the fix is in the reader, not the doc", and `76w6mq` implements it.
- SPECS GRANDFATHER PRE-CUTOVER NAMES by documented decision, adopting the id6 grammar GOING FORWARD, so a pre-cutover spec in this report is expected rather than overdue.
- `executed/` PLAN BODIES ARE IMMUTABLE by policy, which is half the reason the item forbids auto-rename.
- `25kzda` IS CITED CONSTANTLY, so renaming it would break citations for a cosmetic gain; that is the other half.
- `check_engine` HAS AN ADVISORY PRECEDENT: its review-escalation rule keeps the absent case SILENT because a fail-closed absent case "would mass-fail the entire corpus on day one".
- RULE CODES ARE CONTRACTS: severity, assurance class and determinism come from `check_engine`'s `RuleSpec` table; an unregistered code carries none.
- `aw check` IS FAIL-CLOSED IN CI, so even an advisory must be proven not to change the exit code.
- QUOTING CAUSED A PHANTOM MISS ONCE: a backtick-quoted `` set: `awoptimize` ``.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | there is genuinely no signal today | `is_clustered_conformant` is False for a legacy plan and a legacy spec name, yet `aw check specs` reports ZERO naming findings. The exception set is invisible. | both measured at HEAD |
| F-2 | HIGH | the count is nine, and the item said eight | Nine tracked records declare an `- Id:` absent from their filename at HEAD (item recorded 8 of 751). | scan of all tracked records |
| F-3 | HIGH | the ninth is a parser artifact, not a rename candidate | `uyeko5` is a QUOTED EXAMPLE in `27rjro`'s body; the document's filename is CORRECT. Reporting it as a rename target would damage a correct name. Owned by `cqytxf`/`76w6mq`. | the `27rjro` document; `cqytxf`'s "fix is in the reader" |
| F-4 | HIGH | this is what makes Order 01's fallback retirable | Order 01 must keep a mandatory content fallback BECAUSE these records exist; without a count, the fallback can never be retired on evidence. | the item's stated long-term prize; Order 01's scope |
| F-5 | MEDIUM | auto-rename is forbidden for two real reasons | `executed/` bodies are immutable by policy and grandfathered specs are a documented decision; `25kzda` is cited constantly so a rename breaks citations. | the item; the spec cutover decision |
| F-6 | MEDIUM | advisory has an in-repo precedent | `check_engine`'s review-escalation rule keeps the absent case silent to avoid mass-failing the corpus on day one. | that rule's docstring |
| F-7 | MEDIUM | `aw check` is fail-closed in CI | So even an advisory must be verified not to change the exit code; that is E-04's most important check. | CI runs `aw check` fail-closed |
| F-8 | MEDIUM | the `- Set:` case is unmeasured | The item and this plan measured the `- Id:` case; a record can carry a correct id6 and a mismatched setid, and that set size is unknown. E-01 must measure it. | scope of the measurements taken |
| F-9 | LOW | quoting produced a phantom once | A backtick-quoted `` set: `awoptimize` `` was a false positive in the item's audit. | the item's record |
| F-10 | LOW | the remedy differs by type | `aw rename plans` versus `aw rename specs`, and `--to-id6` exists for adopting the grammar; a wrong suggested command is worse than none. | `aw rename` surface |

## Proposed changes (ordered, validatable)

1. Enumerate the exception set and classify every member into legacy / parser-artifact / genuine-drift, measuring the `- Set:` case separately (E-01).
2. Make the report distinguish the buckets so a correctly-named file is never reported as needing a rename (E-02).
3. Emit it advisory with the exact per-record `aw rename`, without touching the existing exemption (E-03).
4. Choose a surface, measure the count that justified it, register any new rule code, and prove the exit code is unchanged (E-04).
5. Prove all five bucket cases from fixtures and record the live count with members named (E-05).

## Deferred / out of scope (with reason)

- AUTO-RENAMING ANY RECORD. Explicitly forbidden by the item, for two measured reasons: `executed/` bodies are immutable by policy and the grandfathered specs are a documented decision. `25kzda` alone is cited constantly enough that a rename would break more than it fixes.
- PROMOTING THE LEGACY EXEMPTION TO AN ERROR. This plan adds a report; reclassifying what the naming rule already tolerates would fail the tree for states the maintainer deliberately chose, and is a separate decision.
- THE RESOLVER AND ITS FILENAME TIER. Order 01 (`826o13`) owns it. This plan produces the COUNT that tells a future maintainer whether Order 01's mandatory fallback can ever be dropped.
- FIXING THE `27rjro` PARSER ARTIFACT. Owned by `cqytxf`/`76w6mq`. This plan must EXCLUDE it from the naming report, not fix it.
- RENAMING THE PRE-CUTOVER SPECS. Grandfathered by documented decision; the report describes their rename as optional and a maintainer call.
- A `--fix` OR BULK-RENAME MODE. The item's per-record maintainer-call requirement rules it out, and a bulk rename across `executed/` would violate the immutability policy at scale.
- THE RESEARCH YAML DIALECT. `05aqbj`/`xo3244` own it; this plan consumes whatever reader exists and, if `76w6mq` has not landed, excludes body-quoted declarations explicitly.

## Scope check

- Over-scope: none. One advisory report and its tests.
- Scope-Paths justification: `agent_workflows/check_engine.py` holds the naming rule, the `RuleSpec` severity table, and the `_iter_type_files` traversal the report must reuse, so the scan, the bucket classification and the rule registration all land there (E-02, E-03, E-04); `tests/test_name_identity_report.py` is new and carries the five fixture cases plus the live-count evidence. `agent_workflows/artifact_naming.py` is deliberately NOT declared: the report CONSUMES `is_clustered_conformant` and the parse helpers read-only, and changing the naming authority would alter what every type considers conformant. `agent_workflows/selectors.py` is likewise not declared even though Order 01 edits it, so the two children cannot collide at the finalize scope gate.
- Under-scope, stated rather than left as `none`: this plan renames nothing, does not promote the exemption to an error, does not touch the resolver, does not fix the parser artifact, adds no `--fix` mode, and does not teach any reader a second dialect. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- FIVE FIXTURE CASES (E-05): legacy reported with the right command; conformant not reported; body-quoted declaration NOT reported as a naming problem; backtick-quoted value producing no phantom; genuine drift reported and distinguished.
- THE LIVE COUNT recorded as evidence with every member NAMED, since that count is what a future reader compares against.
- THE `- Set:` CASE measured and reported separately from the `- Id:` case.
- `aw check all --agent` PER-RULE counts before and after, showing only the new code appearing and no existing rule's count changing.
- `aw check`'s UNPIPED EXIT CODE before and after on the live tree, proving the advisory did not flip CI red.
- THE SUGGESTED COMMAND VERIFIED for at least one record of each type: run it in `--dry-run` (or equivalent) and show it resolves, since a wrong suggestion is worse than none.
- `76w6mq`'s STATUS stated, and the report's behavior under both states (landed / not landed) described.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

The new rule's registration in `check_engine`'s table must carry a comment stating WHY it is advisory rather than an error: `executed/` bodies are immutable and the grandfathered specs are a documented decision, so an error would fail the tree for chosen states. Without that, a future tightening pass will promote it and break CI.

The report's own output must say what it is FOR, in one line: this is the exception set that forces `aw find`'s content fallback, and it is expected to shrink. A count with no purpose gets ignored; a count with a stated purpose gets acted on.

The bucket distinction must be documented at the code, especially the parser-artifact exclusion, because the next reader will otherwise "fix" the report by including `27rjro` and send someone to rename a correct filename.

No spec change is expected. The spec-name cutover is already documented in `check_engine`'s SUPPORTED comment (pre-cutover specs grandfathered, id6 required going forward), and this plan HONORS it rather than amending it. If the executor finds spec text requiring every record's filename to carry its id6 unconditionally, that contradicts the grandfathering and must be REPORTED rather than edited.

## Open questions

### OQ-01: Where should the report surface?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN BUT NARROW, because the constraint is clear even if the preference is not: `aw check` is FAIL-CLOSED in CI, so wherever this lands it must not change an exit code. A sweep rule at warning severity is defensible at nine findings and gives the count the visibility the item wants; a `aw doctor`-only home is safer but reaches fewer readers, since agents and CI are pointed at `aw check`; a flag is the most conservative and the least likely to be run. E-04 requires measuring the count BEFORE choosing, which is the fact that should decide it: if E-01's `- Set:` scan turns up many more than nine, the sweep option weakens considerably. Non-blocking because every option delivers the count, and E-04's exit-code proof is required regardless.

### OQ-02: Should the report include the parser-artifact case?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, AND THIS IS THE PLAN'S MOST IMPORTANT EXCLUSION. `27rjro`'s filename is CORRECT; the apparent mismatch exists only because the reader harvests a `- Id:` from a QUOTED EXAMPLE in its body, which is a reader bug `cqytxf` filed and `76w6mq` fixes, with the explicit instruction that "the fix is in the reader, not the doc". A report that listed it would suggest renaming a correctly-named research prompt, which is worse than reporting nothing: it would manufacture damage while appearing helpful. E-02 therefore requires the exclusion, and the cleanest implementation is to consume `76w6mq`'s bounded reader once it lands, at which point the exclusion becomes structural rather than a special case.

### OQ-03: Should a genuine-drift record be advisory too, or an error?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ADVISORY IN THIS PLAN, WITH THE DISTINCTION RECORDED, and the reasoning is that severity should follow evidence rather than intuition. A modern-grammar file whose name and metadata disagree IS a real defect, unlike a grandfathered name, so it deserves a stronger signal in principle. But NONE was found at authoring, so promoting a class with zero known members would be tuning a rule against no data, and the first real instance might turn out to have a legitimate explanation this plan has not anticipated. E-01 must report prominently if bucket (c) is non-empty, and if it is, the honest next step is a separate decision on severity with real examples in hand rather than a guess encoded now.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the enumerated exception set at your HEAD with EVERY member named and its bucket (legacy / parser-artifact / genuine-drift). Paste the `- Set:` case count separately from the `- Id:` case. State `76w6mq`'s status. If bucket (c) is non-empty, paste those records prominently as a finding rather than folding them into a count.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the report's ACTUAL output on the live tree and confirm by inspection that `27rjro` does NOT appear as a rename candidate. Quote the code implementing the exclusion, and state whether it works by consuming `76w6mq`'s bounded reader or by an explicit body-quote exclusion. Paste the quoting-normalization code.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the report's per-record remedy lines and VERIFY at least one per type by running the suggested command in dry-run, showing it resolves. Quote the line describing a pre-cutover spec's rename as optional rather than overdue. Paste proof the existing legacy exemption was NOT changed (a diff over the naming rule).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: state the chosen surface and the finding count that justified it. Paste the `RuleSpec` registration showing warning severity with its explanatory comment. Paste `aw check`'s UNPIPED exit code before and after on the live tree, unchanged. Paste per-rule counts showing only the new code appeared.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the ACTUAL passing output of all five fixture cases, QUOTING the body-quoted-declaration assertion and the backtick-quoting assertion separately since those are the two false-positive guards. Paste the live count with members named as standing evidence. THEN paste the BARE `python3 -m pytest` summary lines before and after and state the failure-set delta explicitly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS IS ORDER 02 OF A TWO-CHILD SET AND CARRIES NO DEPENDENCY EDGE, deliberately: it can execute before or after Order 01. The two are complementary rather than sequential, since Order 01 makes lookups cheaper while this one makes the exception set that constrains Order 01 countable. If both are run, whichever lands second must re-read the other's changes, because Order 01 edits `selectors.py` and this one edits `check_engine.py` with no overlap by construction.

IT CARRIES NO `Blocks-Release`, because backlog `f8m2z2` carries none. It is `Work-Kind: feature` at `Priority: medium` and the maintainer did not gate it; stated so a reader does not assume a gate was dropped.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. RENAME NOTHING: the report is advisory and every rename is a maintainer call per record, and an `executed/` plan body is immutable by policy. Do NOT promote the existing legacy exemption to an error. Do NOT list `27rjro` as a rename candidate; its filename is correct. Build every case from FIXTURES, never from live records, since the live set will change as `76w6mq` lands and four agents author concurrently. Re-locate every symbol by NAME rather than by the line numbers cited here. Compare `aw check` findings PER RULE, never by total, and prove the exit code is unchanged. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the classified exception set and the unchanged `aw check` exit code.
