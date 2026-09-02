# IPD: Bounded missing-input repair without original-checkout access

- Date: 2026-09-01
- Kind: child
- Concern: Once an isolated worker is told to use only lane-relative paths, a genuinely missing file becomes a dead end: the worker's only recourse would be to reach out of the lane, which is exactly what containment forbids. Without a bounded way to REPORT the need, strictness alone converts a recoverable situation into a silent failure or a permission hang. AMENDED 2026-09-01: this plan formerly also repaired the need by copying the file in, which required classifying secrets; spec `R3.3a` withdrew both, so the cycle now reports and refuses.
- Scope: Implement the missing-input REPORT-AND-REFUSE cycle: a deterministic report token, preserve-and-pause, coordinator-only resolution, one shared classification path for a denied permission event, and a precise refusal record. Implements spec `7ckptx` R3.1, R3.2, R3.3, R3.5, R3.6, R3.7 and nothing else. AMENDED 2026-09-01: R3.3a withdrew the permit-and-copy branch, the secret vocabulary (R3.3a-1/1a/1b/2), R3.3b's tracked-file test, and R3.4's copy; this plan no longer implements any of them.
- Scope-Paths: agent_workflows/lane_containment.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/worktree_lease.py, tests/test_missing_input_repair.py
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
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REVIEWED; round 2 is a DISCLOSED SELF-REVIEW (I authored this plan, so it is weaker evidence than round 1, which was independent and performed by codex/gpt-5). Round 1's PR-* findings were all resolved and moved to FIXED in the typed review record; round 2 then found 2 further findings, SR-001, SR-002 (both FIXED; also amended by the R3.3a withdrawal), of which four across the Set were defects I INTRODUCED while fixing round 1. Full round-2 record: `.aw/records/reviews/20260901-lanectn-round2-selfreview.review.md`.
- 2026-09-01 reviewed (aw set): /aw plan-review round 1 complete; all findings ACCEPTED and resolved. Every one was verified against the artifact before fixing. Two were serious: (1) my orchestrator claimed a proven-complete dependency graph while two children's metadata omitted edges their own prose required, which is the same CLASS of defect that got the predecessor tch3bo rejected - the proof had checked acyclicity only and never metadata-vs-prose agreement; (2) the spec's secret vocabulary was derived from THIS repository's ignore file with no floor, which would admit secrets in a managed target repo, fixed by a maintainer-approved spec amendment adding a built-in floor, union-only composition, and fail-closed behavior. Also fixed: the right-sizing complaint that I complied on E-item count while hiding each second driver's whole implementation in one 'mirror' item (now host-neutral code plus thin adapters), stale hardcoded suite baselines (now measure-at-execution-time and compare failures by identity), a genuine data-model error where retention read the input manifest for OUTPUT collection state (now an attempt-keyed collection receipt owned by the plan that owns collection), and an unfollowable instruction to read docstring owner labels that name superseded phases (now a measured predicate ownership table).
- 2026-09-01 to-review (aw set): plan-review 04/PR-001: E-04 routes a DENIED host-permission event through the classifier, and that seam is owned by lhmrhx. The prose said so; the metadata did not. A scheduler reading metadata could have started this plan before the event schema existed.

- 2026-09-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): fourth child of Set `lanectn`. Requires `nna8yz` executed, because R3.4's manifest REVISION uses the sealing and revision mechanism that plan builds. The predecessor `tch3bo` was rejected partly here (PR-004): it implemented classification and copying only, covering three of the research's five steps, and called that a bounded repair cycle. This plan implements all five.
- 2026-09-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

A worker that genuinely needs a file it does not have has a deterministic, auditable way to SAY SO, and the driver answers with a precise refusal record rather than a copy, so no path ever grants access to the original checkout and the lane's input set never diverges from its sealed manifest. AMENDED 2026-09-01 by spec `R3.3a`: the answer is a RECORD, not a repair.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

HOST-NEUTRAL FIRST, ADAPTERS SECOND. Corrected after `/aw plan-review` finding PR-003: the original E-06 combined refusal recording with the ENTIRE agy token, pause, classification, repair, block, resume, manifest-revision, and authorization cycle. Those are independently testable state transitions and cannot be established by one execution item, which is the same partial-completion trap the predecessor fell into. The whole cycle MUST therefore live in HOST-NEUTRAL code, with each driver item restricted to event adaptation; E-06 adds the precise block plus that wiring.

THE SHARED HOME IS NAMED, and is `agent_workflows/lane_containment.py` (declared first in this plan's `Scope-Paths`). Added 2026-09-01 after a self-review found that requiring host-neutral code while the fence named only the two driver modules told the executor to do something the fence forbade. Put the host-neutral functions THERE. Do NOT improvise a home by putting them in one driver and importing from the other: that makes one host the de-facto shared library, which is the opposite of host-neutral, and spec R2.6 forbids it. If the module does not exist yet, the plan that reaches it first CREATES it; a later plan EXTENDS it.

HISTORY WORTH KEEPING, because it explains why the evidence here is demanded per stage. The predecessor `tch3bo` implemented three of the research's five steps (resolve, reject, copy) and described that as the whole repair cycle; review finding PR-004 caught the omission of preserve-and-pause, the manifest revision, the authorization record, and resume. This plan then specified all five. On 2026-09-01 the maintainer WITHDREW the repair half entirely (spec `R3.3a`), so the cycle is now report-and-refuse and only the report, the pause, the classification, and the refusal remain. The per-stage evidence discipline is kept regardless, because the failure mode it guards against (doing part of a cycle and calling it whole) is independent of how many stages there are.

### Task group 1: report and pause (R3.1, R3.2)

- [ ] E-01 IMPLEMENTS R3.1, R3.2. Define ONE deterministic token form carrying the repo-relative path and the reason it is required, and on observing it PRESERVE AND PAUSE the lane rather than opening an interactive prompt. The worker emits the token and continues with independent work; it never waits. Child `cqx5v7` already names this token in the prompt (R1.4), so use that exact form rather than inventing a second.
  - Depends on: none
  - Expected outcome: the token form is parsed from a worker's output, the lane is preserved and marked paused rather than torn down or prompted, and the worker is not blocked waiting for an answer.
  - Execution state: pending

### Task group 2: classify, coordinator-side only (R3.3, R3.3a as amended, R3.6, R3.7)

- [ ] E-02 IMPLEMENTS R3.3, R3.6. Resolve the requested path in COORDINATOR code only, and reject an absolute path, a path escaping the checkout, a coordinator-owned surface, a sibling lane or the worktrees root, machine-local state, the git administration directory, a directory rather than a file, and a nonexistent path. REUSE the shared worker-forbidden predicate rather than writing a second copy of the rules (CID-2). Make the no-live-grant property STRUCTURAL: the decision type must be incapable of representing a grant of access to the original checkout, so it cannot be set by accident.
  - Depends on: E-01
  - Expected outcome: each forbidden shape is rejected with a precise record and no copy; the decision type has no representation for a live grant; and the reject set is the shared predicate, shown by the call rather than a duplicated list.
  - Execution state: pending
- [ ] E-03 WITHDRAWN by spec R3.3a (amended 2026-09-01); NO WORK IS REQUIRED and none may be done. This item previously extended the shared reject predicate with a secret vocabulary derived from the target repository's ignore file. That is withdrawn for three reasons recorded in the spec: policing secrets invites blame for a miss while `gitleaks` and `aw sanitize` already cover them; the research said do-not-COPY rather than adjudicate-requests; and decisively, nothing is materialized on request any more, so there is nothing to classify. An executor MUST NOT add a secret vocabulary, and MUST record in the walkthrough that this item was withdrawn rather than skipped.
  - Depends on: E-02
  - Expected outcome: no secret vocabulary exists in the shared predicate, and the walkthrough records that this item was withdrawn by spec amendment rather than left undone.
  - Execution state: pending
- [ ] E-04 IMPLEMENTS R3.7. Route a DENIED host permission event that points into the original checkout through the SAME classification path as a missing-input report, so there is one rule rather than two. AMENDED 2026-09-01: this item previously also implemented R3.3b's "policy permits" definition (tracked files permitted, untracked refused). Spec R3.3a WITHDREW that test along with the copy branch it gated, because a lane is a git worktree at a commit and therefore already contains every tracked file, making the permit path inert. Only the routing survives.
  - Depends on: E-03
  - Expected outcome: a denied permission event for a path produces the SAME decision record as the equivalent missing-input token for that path, proving one classification path rather than two.
  - Execution state: pending
### Task group 3: refuse and record (R3.5)

- [ ] E-05 IMPLEMENTS R3.5. RECORD THE REFUSAL PRECISELY. On any missing-input report, write an entry naming the path and the reason it was refused, so the outcome is auditable rather than a bare failure. AMENDED 2026-09-01: this item previously implemented the permit-and-copy branch (copy plus manifest revision plus authorization plus resume). Spec R3.3a WITHDREW that branch, so there is no permitted path and NOTHING is copied into a lane on request. Do NOT implement a copy here; a test asserting a successful copy would assert behavior the spec now forbids.
  - Depends on: E-04
  - Expected outcome: every missing-input report produces a precise record naming the path and the refusal reason, creates no copy in the lane, and emits no grant of access to the original checkout.
  - Execution state: pending
- [ ] E-06 IMPLEMENTS R3.5, and WIRES the agy twin to the shared cycle. On a refused request, BLOCK with a precise missing-input record naming the path and the reason for refusal, so the outcome is auditable rather than a bare failure. Then verify the whole cycle applies in the agy driver: the token, the pause, the classification, and the block. The two drivers are near-parity twins and a rule present in one only is a DEFECT (CID-3).
  - Depends on: E-05
  - Expected outcome: a refused request produces a precise record naming the path and the reason and creates no copy; and the agy driver satisfies the same assertions as the oc driver, proven by a parameterized test rather than a copied one.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Measured at HEAD `59e68d5a`; anchor on symbol names.
- The shared worker-forbidden predicate exists and holds FIVE coordinator-owned surfaces. REUSE it for the reject set; do not fork it (CID-2). Do NOT extend it with a secret vocabulary: spec `R3.3a` withdrew that, and adding one now would ship the liability the maintainer explicitly declined.
- The sealing and revision mechanism comes from child `nna8yz` (R5.1a). Use it; do not edit sealed manifest entries in place.
- The two drivers are near-parity twins; a rule in one only is a DEFECT.
- The suite must be run BARE and `make test-all` separately; a bare run deselects `slow` tests.

## Findings

| id | Finding | Evidence |
| --- | --- | --- |
| F-1 | The predecessor implemented THREE of the five research steps and called it the full cycle; review finding PR-004 caught the omission. That is why evidence here is demanded PER STAGE rather than per item, a discipline retained even though the 2026-09-01 withdrawal reduced the cycle to report, pause, classify, and refuse. | `/aw plan-review` PR-004 on the retired `tch3bo`; spec `7ckptx` R3.2 and R3.3a as amended. |
| F-2 | Secret rejection is genuinely absent today, not merely unspecified. The shared predicate contains five coordinator-owned surfaces and nothing about credentials, so a request for an environment file would be copied into the lane. The maintainer identified this as a gap in the spec itself before approval. | The shared predicate's contents; spec `7ckptx` R3.3a. |
| F-3 | WITHDRAWN 2026-09-01 with the permit-and-copy branch. It formerly recorded that "if policy permits" was undefined in the research and that the spec had fixed it as survives-all-rejections plus regular-file-in-checkout plus TRACKED. Spec `R3.3a` withdrew `R3.3b` entirely, and the reason is worth keeping: a lane is a `git worktree` at a commit, so it ALREADY contains every tracked file (measured: 0 of 1470 absent), which made a tracked-only permit test inert, while the inputs the research actually worried about are IGNORED or UNTRACKED. | Spec `7ckptx` R3.3a as amended; the measurement is recorded there. |
| F-4 | Routing a denied permission event through the same classifier is what keeps ONE rule instead of two. Child `lhmrhx` produces the denial; this plan classifies what it catches, so the two must agree by construction rather than by review. | Spec `7ckptx` R3.7; child `lhmrhx` owns R4.1. |
| F-5 | The no-live-grant property must be STRUCTURAL rather than a convention, because a convention can be broken by a later edit that looks harmless. Making the decision type incapable of representing a grant means the guarantee survives careless maintenance. | Spec `7ckptx` R3.6. |

## Proposed changes (ordered, validatable)

1. Parse the token and preserve-and-pause the lane instead of prompting (E-01).
2. Classify coordinator-side, reusing the shared reject predicate, with no-live-grant made structural (E-02).
3. E-03 is WITHDRAWN by spec `R3.3a`: no secret vocabulary is added, and none may be.
4. Implement the defined meaning of policy-permits, and route denied permission events through the same path (E-04).
5. RECORD THE REFUSAL precisely, naming the path and the reason (E-05). AMENDED 2026-09-01: this step formerly repaired with a digest-verified copy plus a manifest revision, an authorization record, and resume; spec `R3.3a` WITHDREW that branch, so nothing is copied into a lane on request.
6. Block precisely when refused, and mirror the whole cycle into the agy twin (E-06).

## Deferred / out of scope (with reason)

- Prompt text naming the token: child `cqx5v7` owns R1.4. This plan uses that exact form and must not invent a second.
- The manifest, sealing, and the revision mechanism: child `nna8yz` owns R5.1-R5.4 and is this plan's prerequisite.
- The permission DENIAL that E-04 routes: child `lhmrhx` owns R4.1. This plan classifies; that plan denies.
- Retention and teardown: child `xdr83v` owns R5.5-R5.6.
- Shared predicate bodies: child `604wra` owns R6. This plan REUSES the existing worker-forbidden predicate and adds nothing to it.
- OS-level confinement: spec Non-goal 2.

## Scope check

- Over-scope: none. Four declared files and the nine requirements assigned. The change to the shared predicate is an EXTENSION of an existing rule required by R3.3a, not a new surface.
- Under-scope: none for its assigned requirements. This plan does not prevent a worker from reaching out of its lane; it removes the legitimate REASON to, which is the containment argument spec Goal 3 makes.

## Required tests / validation

One new module, parameterized over BOTH drivers: `tests/test_missing_input_repair.py`, covering the token, the pause, every reject shape, the precise refusal record, and the denied-permission-event routing. It must NOT cover a secret family, a tracked-versus-untracked permit rule, or a successful copy: all three were withdrawn by spec `R3.3a`, and asserting them would assert behavior the spec forbids.

BASELINES MUST BE MEASURED AT EXECUTION TIME, NOT COPIED FROM THIS PLAN. Corrected after `/aw plan-review` (PR-003 on every plan in this Set): the exact counts originally written here were already STALE before execution, because a co-worker's commit `8ced15ce` added two tests, moving the bare suite from `3996 passed` to `3998 passed`. A hardcoded count cannot distinguish an honest change from a regression, and treating it as an expectation would either raise a false alarm or, worse, mask a real failure behind an off-by-two rationalization.

SO DO THIS INSTEAD. Immediately before you start, run BOTH invocations and record their counts as YOUR baseline, pasting them. Then after your change, run both again and COMPARE FAILURES BY TEST IDENTITY, not by total: list the failing test node ids before and after and account for every difference by name. A count that changed with no new failing id is fine and must be explained (usually tests added); a new failing id is a STOP regardless of what the totals do.

TWO INVOCATIONS WITH DIFFERENT SEMANTICS, and the distinction is load-bearing: bare `python3 -m pytest` is expected to have ZERO failures, while `make test-all` carries a known set of PRE-EXISTING CLI-surface declaration failures that are not this plan's to fix. State the expected outcome separately per invocation; a single "failed == 0" claim across both is the contradiction that got the predecessor `tch3bo` flagged (PR-006). Identify the pre-existing set by NAME in your own measurement rather than trusting any number recorded here.

Also re-run the tests that cover the shared predicate, since E-03 extends it: any existing suite touching worker-path fencing must stay green, and its summary must be pasted.

## Spec / documentation sync

Spec `7ckptx` is normative; this plan cites requirement ids. Child `604wra` updates the shared predicate module's docstring; if E-03's extension changes what that docstring should say, note it for that child rather than editing beyond this fence.

## Open questions

### OQ-01: Should an untracked-but-safe file ever be materialized?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: MOOT AS OF 2026-09-01, and recorded rather than deleted so the
  reasoning survives. This question presupposed a permit-and-copy branch gated by `R3.3b`'s tracked-file
  test. Spec `R3.3a` withdrew both, so NOTHING is materialized on request, tracked or untracked, and the
  question has no subject. The withdrawal's own rationale subsumes the answer: the tracked-only test was
  inert because a lane already contains every tracked file, and the untracked inputs the research worried
  about (`.venv`, `node_modules`, generated schemas) were exactly what the test refused. If a turn is
  genuinely blocked on a missing ignored input, the conforming fix is up-front lane assembly under an
  explicit policy, not a request-time copy.

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
- [ ] V-03 validates E-03 (WITHDRAWN work; proves the withdrawal was honored)
  - Required evidence: paste evidence that NO secret vocabulary was added to the shared predicate (show the predicate's contents), and quote the walkthrough statement recording that E-03 was WITHDRAWN by spec amendment rather than skipped or forgotten. An executor who implements a secret vocabulary here FAILS this item, because it would ship the liability the maintainer explicitly declined and would assert behavior the amended spec forbids.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04 (proves R3.7; spec A19)
  - Required evidence: paste evidence that a denied host permission event for a path produces the SAME decision record as the equivalent missing-input token for that path, proving one classification path rather than two. Do NOT test a tracked-versus-untracked permit rule: R3.3b was withdrawn, so there is no permit path to test, and asserting one would contradict the spec.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05 (proves R3.5; spec A6)
  - Required evidence: paste a missing-input report producing a precise record that names both the path and the refusal reason, with NO copy created in the lane and no grant emitted. SABOTAGE REQUIRED: make the recorder omit the reason, paste the FAILING assertion, restore, paste it passing plus `git status` proving the product is unmodified. Also paste evidence that no code path copies a requested file into a lane (show the absence structurally, not by reading), since that is the behavior the amendment removed.
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
6. THE SCOPE FENCE IS A DECLARATION, NOT A HALT CONDITION. Touch only the declared `Scope-Paths` as a default, and never expand casually; if the work genuinely requires more, MAKE THE EDIT AND JUSTIFY IT in the finalize reconciliation (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path), which is where an unjustified widening is caught. Do NOT halt the run over a scope question. If the work genuinely requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` will refuse to complete until every out-of-scope path you touched carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT at the gate rather than prevented by halting a run. Do NOT halt the run over a scope question. What you must NOT do is REIMPLEMENT a sibling's rule, which would fork it (CID-2): that is a correctness problem, not a scope one, so if a needed rule is missing, say so in the reconciliation reason.
7. STATE THE HONEST LIMIT. Where a mechanism is an accident guard rather than a boundary, say so in the code comment and in this plan. Overstating a guarantee is the failure.

Commits are path-scoped and never pushed. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed or hook-interrupted commit.

Post-gate lifecycle: run `aw ipd lint --phase pre-transition`, then `aw ipd finalize`, never a hand edit. If validation did not pass, record `substantially-complete` honestly rather than marking this executed.
