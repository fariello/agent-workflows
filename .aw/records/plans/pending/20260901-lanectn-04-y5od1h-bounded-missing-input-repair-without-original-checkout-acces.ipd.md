# IPD: Bounded missing-input repair without original-checkout access

- Date: 2026-09-01
- Kind: child
- Concern: Once an isolated worker is told to use only lane-relative paths, a genuinely missing file becomes a dead end: the worker's only recourse would be to reach out of the lane, which is exactly what containment forbids. Without a bounded repair route, strictness alone converts a recoverable situation into a failure or a permission hang. The shared reject predicate also has NO secret handling today, so a naive implementation would happily copy a credentials file into a lane.
- Scope: Implement the full missing-input repair cycle: a deterministic report token, preserve-and-pause, coordinator-only resolution with secret rejection, a digest-verified copy recorded as a manifest revision with authorization, resume, and a precise block when policy refuses. Implements spec `7ckptx` R3.1, R3.2, R3.3, R3.3a, R3.3b, R3.4, R3.5, R3.6, R3.7 and nothing else.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/worktree_lease.py, tests/test_missing_input_repair.py
- Item-Dependencies: executed:lhmrhx, executed:nna8yz
- From-Spec: 7ckptx
- Blocks-Release: next
- Status: reviewed
- Set: lanectn
- Order: 4
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: y5od1h

## Workflow history
- 2026-09-01 reviewed (aw set): /aw plan-review round 1 complete; all findings ACCEPTED and resolved. Every one was verified against the artifact before fixing. Two were serious: (1) my orchestrator claimed a proven-complete dependency graph while two children's metadata omitted edges their own prose required, which is the same CLASS of defect that got the predecessor tch3bo rejected - the proof had checked acyclicity only and never metadata-vs-prose agreement; (2) the spec's secret vocabulary was derived from THIS repository's ignore file with no floor, which would admit secrets in a managed target repo, fixed by a maintainer-approved spec amendment adding a built-in floor, union-only composition, and fail-closed behavior. Also fixed: the right-sizing complaint that I complied on E-item count while hiding each second driver's whole implementation in one 'mirror' item (now host-neutral code plus thin adapters), stale hardcoded suite baselines (now measure-at-execution-time and compare failures by identity), a genuine data-model error where retention read the input manifest for OUTPUT collection state (now an attempt-keyed collection receipt owned by the plan that owns collection), and an unfollowable instruction to read docstring owner labels that name superseded phases (now a measured predicate ownership table).
- 2026-09-01 to-review (aw set): plan-review 04/PR-001: E-04 routes a DENIED host-permission event through the classifier, and that seam is owned by lhmrhx. The prose said so; the metadata did not. A scheduler reading metadata could have started this plan before the event schema existed.

- 2026-09-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): fourth child of Set `lanectn`. Requires `nna8yz` executed, because R3.4's manifest REVISION uses the sealing and revision mechanism that plan builds. The predecessor `tch3bo` was rejected partly here (PR-004): it implemented classification and copying only, covering three of the research's five steps, and called that a bounded repair cycle. This plan implements all five.
- 2026-09-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

A worker that genuinely needs a file it does not have gets it through a deterministic, auditable cycle that never grants access to the original checkout, never hands over a secret, and never leaves the lane's input set diverging from its manifest.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

HOST-NEUTRAL FIRST, ADAPTERS SECOND. Corrected after `/aw plan-review` finding PR-003: the original E-06 combined refusal recording with the ENTIRE agy token, pause, classification, repair, block, resume, manifest-revision, and authorization cycle. Those are independently testable state transitions and cannot be established by one execution item, which is the same partial-completion trap the predecessor fell into. The whole cycle MUST therefore live in HOST-NEUTRAL code, with each driver item restricted to event adaptation; E-06 adds the precise block plus that wiring.

THE PREDECESSOR FAILED THIS EXACT ITEM BY DOING THREE OF FIVE STEPS. `tch3bo` implemented resolve, reject, and copy, and described that as the repair cycle; review finding PR-004 caught that it omitted preserve-and-pause, the manifest revision, the authorization record, and resume. All five steps are E-items here, and V-items demand evidence of each stage separately so a partial implementation cannot be reported as complete.

### Task group 1: report and pause (R3.1, R3.2)

- [ ] E-01 IMPLEMENTS R3.1, R3.2. Define ONE deterministic token form carrying the repo-relative path and the reason it is required, and on observing it PRESERVE AND PAUSE the lane rather than opening an interactive prompt. The worker emits the token and continues with independent work; it never waits. Child `cqx5v7` already names this token in the prompt (R1.4), so use that exact form rather than inventing a second.
  - Depends on: none
  - Expected outcome: the token form is parsed from a worker's output, the lane is preserved and marked paused rather than torn down or prompted, and the worker is not blocked waiting for an answer.
  - Execution state: pending

### Task group 2: classify, coordinator-side only (R3.3, R3.3a, R3.3b, R3.6, R3.7)

- [ ] E-02 IMPLEMENTS R3.3, R3.6. Resolve the requested path in COORDINATOR code only, and reject an absolute path, a path escaping the checkout, a coordinator-owned surface, a sibling lane or the worktrees root, machine-local state, the git administration directory, a directory rather than a file, and a nonexistent path. REUSE the shared worker-forbidden predicate rather than writing a second copy of the rules (CID-2). Make the no-live-grant property STRUCTURAL: the decision type must be incapable of representing a grant of access to the original checkout, so it cannot be set by accident.
  - Depends on: E-01
  - Expected outcome: each forbidden shape is rejected with a precise record and no copy; the decision type has no representation for a live grant; and the reject set is the shared predicate, shown by the call rather than a duplicated list.
  - Execution state: pending
- [ ] E-03 IMPLEMENTS R3.3a. EXTEND the shared reject predicate to refuse secret-bearing paths, and DERIVE the secret vocabulary from the repository's single existing source rather than transcribing it. Measured at authoring: the shared predicate today contains only five coordinator-owned surfaces and ZERO secret handling, so a request for an environment file would be materialized into the lane. The repository already declares its secret families under two explicit headings in its ignore file; derive from those so the two cannot drift, and extend the SHARED predicate rather than adding a check at one call site, so a second caller cannot miss it.
  - Depends on: E-02
  - Expected outcome: a representative path from each declared secret family is rejected with no copy; the vocabulary is derived from the existing source, shown by the derivation rather than a literal list; and the rule lives in the shared predicate.
  - Execution state: pending
- [ ] E-04 IMPLEMENTS R3.3b, R3.7. Implement the DEFINED meaning of "policy permits": the path survives every rejection test, is a regular file inside the checkout, AND is TRACKED by git. Untracked-but-present files are REFUSED by default, because a lane is created from a commit, so a tracked file is content the lane provably should have had while an untracked file is local machine state whose absence is correct. Then route a DENIED host permission event that points into the original checkout through this SAME classification path, so there is one rule rather than two.
  - Depends on: E-03
  - Expected outcome: a tracked safe file is permitted while an untracked otherwise-safe file is refused with a precise record; and a denied permission event for a path produces the same decision as the equivalent token for that path.
  - Execution state: pending

### Task group 3: repair or block (R3.4, R3.5)

- [ ] E-05 IMPLEMENTS R3.4. On a permitted request, materialize a digest-verified copy into the lane, record a NEW MANIFEST REVISION rather than editing an entry in place, record the corresponding authorization, and resume the same session or a new attempt with the change stated explicitly. All four parts are required: a classify-and-copy that omits the revision and the authorization is NOT a conforming repair cycle, because the lane's input set would silently diverge from its sealed manifest. Use the revision mechanism child `nna8yz` built; do not edit sealed entries.
  - Depends on: E-04
  - Expected outcome: a permitted request yields a digest-verified lane copy, a new manifest revision (with the prior revision still present and unmodified), a written authorization record, and an observable resume.
  - Execution state: pending
- [ ] E-06 IMPLEMENTS R3.5, and WIRES the agy twin to the shared cycle. On a refused request, BLOCK with a precise missing-input record naming the path and the reason for refusal, so the outcome is auditable rather than a bare failure. Then verify the whole cycle applies in the agy driver: the token, the pause, the classification, and the block. The two drivers are near-parity twins and a rule present in one only is a DEFECT (CID-3).
  - Depends on: E-05
  - Expected outcome: a refused request produces a precise record naming the path and the reason and creates no copy; and the agy driver satisfies the same assertions as the oc driver, proven by a parameterized test rather than a copied one.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Measured at HEAD `59e68d5a`; anchor on symbol names.
- The shared worker-forbidden predicate exists and currently holds FIVE coordinator-owned surfaces with NO secret handling. Extend it; do not fork it (CID-2).
- The repository's secret vocabulary already exists in one place, declared under explicit headings. Derive from it rather than transcribing, so the two cannot drift.
- The sealing and revision mechanism comes from child `nna8yz` (R5.1a). Use it; do not edit sealed manifest entries in place.
- The two drivers are near-parity twins; a rule in one only is a DEFECT.
- The suite must be run BARE and `make test-all` separately; a bare run deselects `slow` tests.

## Findings

| id | Finding | Evidence |
| --- | --- | --- |
| F-1 | The predecessor implemented THREE of the five required steps and described it as the full cycle. Review finding PR-004 caught the omission of preserve-and-pause, the manifest revision, the authorization record, and resume. This plan makes each a separate E-item with separate evidence so a partial implementation cannot be reported as complete. | `/aw plan-review` PR-004 on the retired `tch3bo`; spec `7ckptx` R3.2-R3.4. |
| F-2 | Secret rejection is genuinely absent today, not merely unspecified. The shared predicate contains five coordinator-owned surfaces and nothing about credentials, so a request for an environment file would be copied into the lane. The maintainer identified this as a gap in the spec itself before approval. | The shared predicate's contents; spec `7ckptx` R3.3a. |
| F-3 | "If policy permits" was undefined in the research and would have been left to executor judgment. The spec now fixes it as survives-all-rejections plus regular-file-in-checkout plus TRACKED, with untracked refused by default. A looser test would silently widen the rule. | Spec `7ckptx` R3.3b. |
| F-4 | Routing a denied permission event through the same classifier is what keeps ONE rule instead of two. Child `lhmrhx` produces the denial; this plan classifies what it catches, so the two must agree by construction rather than by review. | Spec `7ckptx` R3.7; child `lhmrhx` owns R4.1. |
| F-5 | The no-live-grant property must be STRUCTURAL rather than a convention, because a convention can be broken by a later edit that looks harmless. Making the decision type incapable of representing a grant means the guarantee survives careless maintenance. | Spec `7ckptx` R3.6. |

## Proposed changes (ordered, validatable)

1. Parse the token and preserve-and-pause the lane instead of prompting (E-01).
2. Classify coordinator-side, reusing the shared reject predicate, with no-live-grant made structural (E-02).
3. Extend the shared predicate to refuse secrets, deriving the vocabulary from the existing single source (E-03).
4. Implement the defined meaning of policy-permits, and route denied permission events through the same path (E-04).
5. Repair with a digest-verified copy plus a new manifest revision, an authorization record, and resume (E-05).
6. Block precisely when refused, and mirror the whole cycle into the agy twin (E-06).

## Deferred / out of scope (with reason)

- Prompt text naming the token: child `cqx5v7` owns R1.4. This plan uses that exact form and must not invent a second.
- The manifest, sealing, and the revision mechanism: child `nna8yz` owns R5.1-R5.4 and is this plan's prerequisite.
- The permission DENIAL that E-04 routes: child `lhmrhx` owns R4.1. This plan classifies; that plan denies.
- Retention and teardown: child `xdr83v` owns R5.5-R5.6.
- Shared predicate bodies beyond the secret extension this plan needs: child `604wra` owns R6.
- OS-level confinement: spec Non-goal 2.

## Scope check

- Over-scope: none. Four declared files and the nine requirements assigned. The change to the shared predicate is an EXTENSION of an existing rule required by R3.3a, not a new surface.
- Under-scope: none for its assigned requirements. This plan does not prevent a worker from reaching out of its lane; it removes the legitimate REASON to, which is the containment argument spec Goal 3 makes.

## Required tests / validation

One new module, parameterized over BOTH drivers: `tests/test_missing_input_repair.py`, covering the token, the pause, every reject shape including each secret family, the tracked-versus-untracked rule, the permitted repair with its revision and authorization, the precise block, and the denied-permission-event routing.

BASELINES MUST BE MEASURED AT EXECUTION TIME, NOT COPIED FROM THIS PLAN. Corrected after `/aw plan-review` (PR-003 on every plan in this Set): the exact counts originally written here were already STALE before execution, because a co-worker's commit `8ced15ce` added two tests, moving the bare suite from `3996 passed` to `3998 passed`. A hardcoded count cannot distinguish an honest change from a regression, and treating it as an expectation would either raise a false alarm or, worse, mask a real failure behind an off-by-two rationalization.

SO DO THIS INSTEAD. Immediately before you start, run BOTH invocations and record their counts as YOUR baseline, pasting them. Then after your change, run both again and COMPARE FAILURES BY TEST IDENTITY, not by total: list the failing test node ids before and after and account for every difference by name. A count that changed with no new failing id is fine and must be explained (usually tests added); a new failing id is a STOP regardless of what the totals do.

TWO INVOCATIONS WITH DIFFERENT SEMANTICS, and the distinction is load-bearing: bare `python3 -m pytest` is expected to have ZERO failures, while `make test-all` carries a known set of PRE-EXISTING CLI-surface declaration failures that are not this plan's to fix. State the expected outcome separately per invocation; a single "failed == 0" claim across both is the contradiction that got the predecessor `tch3bo` flagged (PR-006). Identify the pre-existing set by NAME in your own measurement rather than trusting any number recorded here.

Also re-run the tests that cover the shared predicate, since E-03 extends it: any existing suite touching worker-path fencing must stay green, and its summary must be pasted.

## Spec / documentation sync

Spec `7ckptx` is normative; this plan cites requirement ids. Child `604wra` updates the shared predicate module's docstring; if E-03's extension changes what that docstring should say, note it for that child rather than editing beyond this fence.

## Open questions

### OQ-01: Should an untracked-but-safe file ever be materialized, given R3.3b refuses it by default?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, not by this plan, and the default must not be widened here. R3.3b is explicit that a future policy MAY widen the tracked test but MUST do so explicitly, never by an implementation choosing a looser check. The reasoning is that a lane is created from a commit, so a tracked file is content the lane provably should have contained, whereas an untracked file is local machine state whose absence from the lane is CORRECT rather than a defect. If an executor encounters a real case where an untracked file is genuinely required, the conforming action is to STOP and report it as a spec amendment request, not to relax the test. V-04 pins both halves precisely so a later loosening is visible.

### OQ-02: What fail-closed, project-agnostic secret source should govern repair, and may execution begin before the dependency and sizing defects are fixed?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001, PR-002, PR-003
- Resolution or deferral rationale: Round 1 review found no repository authority for choosing a fallback when a target repository lacks the two expected ignore-file headings, so the approved spec needs a maintainer decision before implementation. The same review found the missing `lhmrhx` producer edge and an oversized E-06. Amend and approve the secret-rejection contract, add the dependency, decompose the mirror work, and re-review before resolving this question.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01 (proves R3.1, R3.2; spec A6)
  - Required evidence: paste evidence of all three: the token form parsed from worker output, the lane PRESERVED and marked paused (show the lane still exists and its paused state, not just a log line), and the absence of any interactive prompt. Also show the worker was not blocked waiting for an answer. SABOTAGE REQUIRED: make the handler tear the lane down instead of preserving it, paste the FAILING assertion, restore, paste it passing plus `git status` proving the product is unmodified.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02 (proves R3.3, R3.6; spec A7)
  - Required evidence: paste one case per forbidden shape (absolute, `..` escape, coordinator surface, sibling lane, machine state, git dir, directory, nonexistent), each showing a precise reject record and NO copy created. Paste evidence the reject decision comes from the SHARED predicate by showing the call, not a duplicated list. Then prove the no-live-grant property is STRUCTURAL: show the decision type cannot represent a grant (for example that no field exists to set), rather than asserting a value is false.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03 (proves R3.3a; spec A7b)
  - Required evidence: paste a rejection for a representative path from EACH declared secret family, at minimum an environment file, a certificate, a key, and a credentials file. A test proving only one family is rejected does NOT satisfy this item. Then paste evidence the vocabulary is DERIVED from the repository's existing single source rather than transcribed (show the derivation), and that the rule lives in the SHARED predicate so a second call site cannot miss it. SABOTAGE REQUIRED: add a new secret family to the source and show it is rejected WITHOUT editing the predicate, which proves derivation rather than duplication.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04 (proves R3.3b, R3.7; spec A7c, A19)
  - Required evidence: paste both halves of the tracked rule: a TRACKED safe file permitted and materialized, and an UNTRACKED otherwise-safe file REFUSED with a precise record. Then paste evidence that a denied host permission event for a path produces the SAME decision record as the equivalent token for that path, proving one classification path rather than two.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05 (proves R3.4; spec A6)
  - Required evidence: paste evidence of all FOUR parts separately, since the predecessor was rejected for delivering only some: the digest-verified lane copy; the NEW manifest revision with the prior revision still present and unmodified; the written authorization record; and the observable resume. A run that copies the file but shows no revision or no authorization FAILS this item. Also show no sealed manifest entry was edited in place.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06 (proves R3.5 and twin parity; spec A7, CID-3)
  - Required evidence: paste a refused request producing a precise record that names both the path and the reason, with no copy created. Then paste the parameterized run proving BOTH drivers satisfy the same assertions, showing the parameterization rather than two similar functions. Paste the existing shared-predicate suites still green, since E-03 extended that predicate. Finally paste both whole-suite invocations with expected counts stated separately per invocation; an unexplained new failure means `Result: pending`, never a pass.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 6 E-leaves in 3 task groups, under both thresholds. The groups are the three phases of ONE cycle (report, classify, repair-or-block) and are not separable: classification without the repair path leaves the worker with a dead end, and repair without classification is the live-grant this plan exists to prevent. The predecessor's failure was doing part of this cycle and calling it whole, which is why the phases are grouped but the evidence is demanded per stage.

Execution contract: this plan INHERITS the shared execution contract from orchestrator `h0zljh` verbatim, including its ten numbered rules. Restated here because these are the ones most likely to be skipped, and skipping them is how this work gets faked:

1. PROSE IS NEVER EVIDENCE. Paste real command output and exit codes, never a summary of them. A `V-*` whose command was not run stays `Result: pending`.
2. SABOTAGE the central assertions. Break the product behavior deliberately, paste the FAILING run, restore, paste the passing run plus `git status` proving the product is unmodified. This session already produced a test that passed while the product was broken; only sabotage exposed it.
3. ASSERT THE PROPERTY, NOT THE WORDING. Where the requirement states an absence, check the emitted output so a reworded violation still fails.
4. STRUCTURE, NOT GREP, for "only one of these exists". Use AST or the import graph, repo-wide; a text grep is satisfied by the checking code itself.
5. PREREQUISITE IS CHECKED, NOT ASSUMED: children `nna8yz` (Order 02) AND `lhmrhx` (Order 03) MUST both be in `executed/` before this plan starts. `nna8yz` because R3.4's manifest REVISION uses the sealing and revision mechanism that plan builds; `lhmrhx` because E-04 routes a DENIED host-permission event through this classifier and that event seam is owned by `lhmrhx`. THE SECOND EDGE WAS MISSING FROM THE METADATA AT FIRST AUTHORING and was added after `/aw plan-review` finding PR-002 caught it: the prose required it, the machine-readable field did not, and a scheduler reading metadata could have started this plan before the event schema existed. Verify those symbols exist. If they are absent, STOP and report; do not reimplement them, which would fork the rule (CID-2).
6. THE SCOPE FENCE IS A STOP CONDITION. Touch only the declared `Scope-Paths`. If the work seems to need a sibling's surface, STOP AND REPORT; do not broaden and do not reimplement it, which would fork the rule (CID-2).
7. STATE THE HONEST LIMIT. Where a mechanism is an accident guard rather than a boundary, say so in the code comment and in this plan. Overstating a guarantee is the failure.

Commits are path-scoped and never pushed. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed or hook-interrupted commit.

Post-gate lifecycle: run `aw ipd lint --phase pre-transition`, then `aw ipd finalize`, never a hand edit. If validation did not pass, record `substantially-complete` honestly rather than marking this executed.
