# IPD: Resolve a setid within the requested type and report candidates per type when it cannot

- Date: 2026-09-10
- Kind: child
- Concern: A setid is now a SHARED cross-type TOPIC label (DECISIONS D153, spec `2lcqno` N1), so one token routinely names artifacts of several types. The UNTYPED setter fans out across every type and then fails on the first artifact whose type cannot take the requested status. MEASURED at HEAD: `aw set approved agentadhere --dry-run` refuses with `Validation error ... Status 'approved' is not valid for backlog (valid: ['blocked', 'done', 'graduated', 'open', 'parked'])`, naming a BACKLOG item, when the operator plainly meant the plan Set. Nothing is wrong with the artifacts; the resolver simply has no way to hear "the plans called agentadhere".
  THE AUTHORED PREMISE WAS WRONG AND MEASUREMENT CORRECTED IT, WHICH CHANGES THIS PLAN'S SCOPE. The spec and the parent checklist both describe the defect as a TYPED-path failure, citing the historical error `Type mismatch: selector 'agentadhere' resolved to artifact(s) of type ['backlog', 'research'] ... scoped to 'plans'` (`status_set.py:1265`). That path is ALREADY FIXED: `match_selector` accepts `scoped_type` and restricts `record_types` to it (`status_set.py:315-317`), so `match_selector('agentadhere', ..., scoped_type='plans')` returns 7 matches, all of type `plans`, while the unscoped call returns 13 across three types. The refusal at `:1259-1268` therefore tests a condition that CANNOT occur on a scoped call, i.e. it is now dead code that documents a fixed bug. So this plan must fix the UNTYPED path and RETIRE the dead branch, not "add type scoping" that already exists.
  WHY THE UNTYPED PATH CANNOT SIMPLY GUESS: `aw set` is deliberately record-type-agnostic and serves plans, specs, prompts and backlog at once. Silently picking the type whose status vocabulary happens to accept the requested value would be a guess dressed as resolution, and would act on artifacts the operator never named. Spec `2lcqno` N4 requires the opposite: report the CANDIDATES BY TYPE and how to disambiguate, never guess.
- Scope: The untyped setter's behavior when one selector resolves across several record types, and the now-dead typed-mismatch refusal. IN: making the untyped `aw set` report candidates grouped BY TYPE with the exact typed command that would act on each, instead of failing on whichever foreign artifact it reached first; deciding and implementing what the untyped verb does when the requested status IS valid for several matched types; removing or repurposing the dead type-mismatch branch; a regression fixture built from the measured `agentadhere` case. OUT: the collision-check re-scope (Order 01, the sibling child); the status vocabularies themselves, which are correct per type; any change to what a bare setid MEANS for a single type (a whole Set, per IPD `laykok` E-07, which stays); artifact renaming, which the ruling forbids.
- Scope-Paths: agent_workflows/status_set.py, tests/test_status_set.py
- Item-Dependencies: none
- Status: to-review
- Set: setidfix
- Order: 2
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: w2y5ac
- From-Spec: 2lcqno

## Workflow history

- 2026-09-10 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from spec `2lcqno` N3/N4 as checklist item T-09, after the maintainer chose "write plans for both, ready for review" over coding directly. THE CENTRAL FINDING IS THAT THE AUTHORED DIAGNOSIS WAS WRONG, and it was caught by executing rather than reading: the typed path the spec blames is already correct (`match_selector` pre-filters by `scoped_type`, verified live at 7 plans versus 13 unscoped), so the `Type mismatch` refusal the spec quotes is unreachable on a scoped call. The live defect is on the UNTYPED path and produces a DIFFERENT error naming a backlog item's status vocabulary. Both facts are pasted in F-1 and F-2. A plan written from the spec's prose alone would have "fixed" working code and left the real failure in place. ALSO RECORDED, because it cost a near-miss during authoring: `aw ipd set` WRITES BY DEFAULT with no confirmation, so an attempt to REPRODUCE the historical error instead reverted 7 executed plans to `approved`/`pending` in one command; reverted with no commit, and filed as backlog `f5pttg` (high). That is why every reproduction step in this plan specifies `--dry-run`.
- 2026-09-10 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make one shared topic name usable as a selector: when an operator names a type, act within that type (already true, and pin it); when they do not, tell them exactly which types the name matched and what to run, instead of refusing on an artifact they did not mean.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin what already works, retire what is dead

- [ ] E-01 PIN THE TYPED PATH WITH A TEST, BECAUSE NOTHING CURRENTLY PROVES IT AND THIS PLAN'S WHOLE PREMISE DEPENDS ON IT. Add a case asserting that a selector naming a setid shared across types, resolved with `scoped_type='plans'`, returns ONLY plan artifacts. Use the measured shape: a setid carried by plans AND a backlog item AND research reports. This is the guard that makes the rest of the plan safe to write, since without it a future change to `match_selector`'s `record_types` narrowing (`status_set.py:315-317`) would silently reintroduce the original failure with no test failing.
  - Depends on: none
  - Expected outcome: a test fails if scoped resolution ever stops filtering by type.
  - Execution state: pending

- [ ] E-02 REMOVE THE DEAD TYPE-MISMATCH BRANCH at `status_set.py:1259-1268`, or convert it into an assertion, and SAY WHICH YOU DID AND WHY. It computes `mismatches = [m for m in matches if m.record_type != scoped_type_canonical]` on a `matches` list that `match_selector` already restricted to that single type, so the list is always empty and the refusal is unreachable. It is not harmless: it is the code a reader greps to when told "the typed path refuses on cross-type setids", so it actively documents a bug that no longer exists, which is how the spec's own diagnosis went wrong. If you convert rather than delete, make it an internal invariant assertion with a comment naming the pre-filter, NOT a user-facing refusal.
  - Depends on: E-01
  - Expected outcome: the unreachable user-facing refusal is gone; a reader can no longer mistake it for live behavior; E-01's pin still passes.
  - Execution state: pending

### Task group 2: fix the untyped path

- [ ] E-03 MAKE THE UNTYPED SETTER REPORT CANDIDATES BY TYPE INSTEAD OF FAILING ON THE FIRST FOREIGN ARTIFACT. Today `aw set approved <shared-setid>` reaches `_validate` and dies on whichever artifact's vocabulary rejects the status, naming that artifact (measured: a backlog item, when the operator meant plans). Per spec `2lcqno` N4 the tool MUST report the candidates grouped BY TYPE and how to disambiguate, and MUST NOT guess. Emit, for each matched type, the count and the exact typed command that would act on it (for example the plans, specs or backlog form of the setter), so the operator's next keystroke is in the message. DO NOT change the per-type status vocabularies: `approved` genuinely is invalid for a backlog item and that validation is correct.
  - Depends on: E-01
  - Expected outcome: the measured `agentadhere` case prints one line per matched type with counts and a runnable disambiguating command, and exits nonzero without writing.
  - Execution state: pending

- [ ] E-04 DECIDE AND IMPLEMENT THE MULTI-TYPE-VALID CASE, which E-03 does not cover and which is the genuinely ambiguous one. When the requested status is valid for SEVERAL matched types (for example a status in both the plan and spec vocabularies), there is no vocabulary error to stop on, so today the untyped setter would act on ALL of them. Under N4 that is a guess. Choose ONE: refuse with the same per-type candidate report and require a type scope; or act on all types but require an explicit confirmation flag; or act on all silently (the status quo, which N4 forbids). RECORD THE CHOICE AND ITS REASON in the code, and note the interaction with backlog `f5pttg`: `aw ipd set` already writes without confirmation, so adding a confirmation requirement here while the sibling verb has none would be inconsistent; say whether you are fixing that here or leaving it to `f5pttg`.
  - Depends on: E-03
  - Expected outcome: a shared setid whose status is valid for two types produces a deliberate, documented outcome rather than an unannounced multi-type write.
  - Execution state: pending

### Task group 3: pin the measured failure

- [ ] E-05 ADD THE REGRESSION FIXTURE FROM THE MEASURED CASE, not a synthetic one, because the synthetic version is what let the wrong diagnosis survive review. Build a tree with one setid carried by plans, a backlog item and research docs, then assert: the untyped setter reports per-type candidates and writes NOTHING; the typed setter acts on the plans only; and the historical `Type mismatch` string appears NOWHERE in the output of either (it is E-02's dead branch and its reappearance would mean the branch came back). Run every reproduction with `--dry-run` where the verb supports it: during authoring, a bare `aw ipd set approved agentadhere` WROTE, reverting 7 executed plans, which is filed as `f5pttg`.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: three assertions pinning untyped behavior, typed behavior, and the absence of the retired message.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `match_selector` ALREADY NARROWS BY TYPE (`status_set.py:296-320`): given `scoped_type`, it sets `record_types = (canonical,)`. This is the single fact that reframes the whole plan, and it is why E-01 pins it before anything else touches the area.
- A BARE SETID LEGITIMATELY MEANS THE WHOLE SET for a mutating setter, made deliberate by IPD `laykok` E-07, which distinguishes a setid fan-out (act on all, no `--force`) from a unique-id collision (always refuse) and a filename substring multi-match (refuse unless `--force`). This plan must NOT weaken that; the problem is cross-TYPE fan-out, not within-type fan-out.
- STATUS VOCABULARIES ARE PER TYPE and are correct: `approved` is valid for a plan and invalid for a backlog item (`['blocked', 'done', 'graduated', 'open', 'parked']`). The fix belongs in resolution and reporting, never in the vocabularies.
- `aw set` IS DELIBERATELY UNTYPED (`cli.py:10929` passes `scoped_type=None`) while `aw ipd set`, `aw spec set`, `aw backlog set` and the prompts setter pass a concrete type. So the untyped verb is the ONE surface that must handle multi-type resolution.
- MUTATING SETTERS HERE WRITE BY DEFAULT. `aw ipd set` has `--dry-run` as opt-in and did not prompt before a seven-file transition. Use `--dry-run` for every exploratory run; see backlog `f5pttg`.
- SUITE BARE: `python3 -m pytest`. Compare failing NODE IDS, never totals. Known environmental failure in the primary checkout only: `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` (a gitignored local `opencode-recovery/` dump); it passes in a clean worktree.

## Findings

| Id | Severity | Location (measured at HEAD) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `status_set.py:296-320` | THE TYPED PATH IS ALREADY CORRECT, so the spec's stated defect is stale. `match_selector` restricts `record_types` to the scoped type. | `match_selector('agentadhere', ..., scoped_type='plans')` -> 7 matches, types `['plans']`; unscoped -> 13 matches, types `['backlog', 'plans', 'research']` |
| F-2 | HIGH | the untyped `aw set` path | THE LIVE DEFECT IS ON THE UNTYPED PATH AND HAS A DIFFERENT ERROR than the one the spec quotes. | `aw set approved agentadhere --dry-run` -> `FAIL Validation error on ...3gr7fk...backlog.md: Status 'approved' is not valid for backlog (valid: ['blocked', 'done', 'graduated', 'open', 'parked'])` |
| F-3 | MEDIUM | `status_set.py:1259-1268` | THE `Type mismatch` REFUSAL IS UNREACHABLE on a scoped call, because `matches` is pre-filtered. It is dead code that documents a fixed bug, and it is what the spec's diagnosis was built on. | source read against F-1 |
| F-4 | MEDIUM | `status_set.py` `_validate` path | The untyped setter validates per artifact and dies on the FIRST foreign one, so the operator sees an unrelated type's vocabulary rather than a disambiguation prompt. | the F-2 output names a backlog item's valid-status list |
| F-5 | MEDIUM | this plan's own authoring | `aw ipd set` WRITES BY DEFAULT with no confirmation: `aw ipd set approved agentadhere` moved 7 plans from `executed/` to `pending/` and rewrote their status. Reverted, uncommitted. Filed as `f5pttg`. | the seven `executed → approved` lines and the resulting `git status`; restored byte-identical to HEAD |
| F-6 | LOW | IPD `laykok` E-07 | Within-type setid fan-out is DELIBERATE and must survive; only cross-type fan-out is the defect. Conflating them would break bulk Set transitions. | the kind-aware ambiguity block at `status_set.py:1229-1258` |

## Proposed changes (ordered, validatable)

1. E-01 pins the typed path, so the premise this plan rests on cannot silently regress.
2. E-02 retires the unreachable refusal that misled the spec's own diagnosis.
3. E-03 replaces the untyped path's first-foreign-artifact failure with a per-type candidate report.
4. E-04 settles the genuinely ambiguous multi-type-valid case with a recorded decision.
5. E-05 pins all of it with a fixture built from the measured corpus shape.

## Deferred / out of scope (with reason)

- THE COLLISION-CHECK RE-SCOPE: Order 01 of this Set (`216rgg`). Independent of resolution, separately reviewable.
- MAKING MUTATING SETTERS SAFE BY DEFAULT (dry-run default, confirmation on bulk, refusing backwards terminal transitions): backlog `f5pttg`. It is a real and arguably higher-severity defect, but it spans several verbs and its own decision about default behavior; E-04 must only state whether it depends on that outcome.
- THE PER-TYPE STATUS VOCABULARIES: correct as they are. The defect is resolution, not validation.
- WITHIN-TYPE SETID FAN-OUT: deliberate (`laykok` E-07) and preserved.

## Scope check

- Over-scope: none. Both declared paths are touched by named items: `status_set.py` (E-02, E-03, E-04) and `tests/test_status_set.py` (E-01, E-05).
- Under-scope: none remaining. The measurement sweep added E-01 (nothing pinned the typed path), E-02 (the dead branch, absent from the authored intent) and E-04 (the multi-type-valid case, which the spec's N4 requires but the checklist never named).

## Required tests / validation

`python3 -m pytest` bare, in an isolated worktree, baseline measured there and pasted, compared by failing NODE ID rather than by total. Beyond the suite: the measured `agentadhere` case run BEFORE and AFTER on both the untyped and typed paths, with output pasted, always with `--dry-run`; plus `git status --porcelain` after each exploratory run proving nothing was written, given F-5.

## Spec / documentation sync

NO SPEC IS AMENDED and none is declared in `- Scope-Paths:`. This plan IMPLEMENTS spec `2lcqno` N3 and N4 rather than changing them.

BUT ONE SPEC STATEMENT IS NOW KNOWN TO BE IMPRECISE AND THE REVIEWER SHOULD DECIDE WHAT TO DO WITH IT: `2lcqno` Section 1 finding 3 and its N3 both describe the defect as the TYPED setter giving up, citing the historical `Type mismatch` error. F-1 shows the typed path already resolves correctly, so that framing is stale even though N3's REQUIREMENT (resolve within the requested type) is satisfied by the code and worth keeping as a pinned invariant. Options: leave it (the requirement is right, only the example is dated), or amend Section 1 to name the untyped path as the live surface. Deliberately NOT amended here, because editing the governing spec from inside its own implementing plan is the kind of change a reviewer should sanction; raised as OQ-01.

## Open questions

### OQ-01: Should spec `2lcqno`'s stale example be amended, and by whom?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, because this plan's deliverables do not depend on the answer: N3's requirement stands either way and E-01 pins it. The question is bookkeeping about the SPEC's accuracy. It matters because the spec's stale example is exactly what produced this plan's original wrong diagnosis, so leaving it invites the next reader to repeat the error. NOT resolved unilaterally: the spec is `to-review`, and a plan editing its own governing spec's problem statement is a change a reviewer should sanction rather than inherit. RECOMMENDATION: amend Section 1 finding 3 to state that the typed path was fixed and the untyped path is the live surface, and add a one-line note under N3 that it is now a PINNED invariant rather than a fix to build. Cheapest done during the spec's own review, before either child executes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new test passing, AND a MUTATION CHECK proving it bites: break `match_selector`'s type narrowing (make `record_types` ignore `scoped_type`), show the test FAILS, restore, show it passes. Without the mutation this test could pass vacuously.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: state whether you deleted the branch or converted it to an assertion, and why. Paste a `grep` showing the user-facing `Type mismatch` string is gone from `status_set.py` (or, if converted, that it is no longer reachable as a user message). Paste the suite result for `tests/test_status_set.py` showing nothing depended on it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the BEFORE output (the measured `Validation error ... not valid for backlog` line) and the AFTER output for the same untyped command, showing one line per matched type with counts and a runnable typed command. Paste `git status --porcelain` proving nothing was written. Confirm the exit code is nonzero.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the chosen behavior exercised on a fixture where the status is valid for two matched types, plus the code comment recording the decision and its reason. State explicitly whether the outcome depends on backlog `f5pttg` and, if so, what happens until that lands.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste all three assertions passing (untyped reports and writes nothing; typed acts on plans only; the retired message appears nowhere). Paste the fixture's corpus shape showing it spans plans, backlog and research, so it matches the measured case rather than a simplified one.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Size note: 5 E-leaves in 3 groups. Two of the five (E-01, E-02) exist only because measurement contradicted the authored premise, and one (E-04) because the spec's N4 implies a case the checklist never named.
- Cohesion rationale: E-01 and E-02 are one concern seen from two sides, pinning behavior that is already correct and removing the code that claims otherwise; they must land together or the pin guards code a reader still believes is broken. E-03 and E-04 are the untyped path's two distinct outcomes (one type valid, several types valid) and are split because they have different failure modes and different tests. E-05 is the shared regression surface.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. When reporting tests passed, paste the ACTUAL runner output. USE `--dry-run` FOR EVERY EXPLORATORY SETTER RUN: `aw ipd set` writes by default and reverted 7 executed plans during this plan's authoring (backlog `f5pttg`). This is a SHARED CHECKOUT: never revert or commit a file you did not change.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved w2y5ac --by-human --message ...`) before execution. Its governing spec `2lcqno` is `to-review`, and OQ-01 asks whether that spec's stale example should be amended during its review; prefer letting the spec clear review first. On completion, transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
