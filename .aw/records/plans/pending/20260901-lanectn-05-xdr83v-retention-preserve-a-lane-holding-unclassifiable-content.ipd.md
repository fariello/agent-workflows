# IPD: Retention: preserve a lane holding unclassifiable content

- Date: 2026-09-01
- Kind: child
- Concern: Teardown currently removes a lane without first asking what is in it, so content the driver cannot account for is destroyed silently. Ignored files are the specific hazard: treating "ignored" as "disposable" is what previously deleted lane content without a record, and a lane can legitimately hold a dirty tracked file or a submission that was never collected.
- Scope: Inventory a lane before teardown and REFUSE while it holds content the driver cannot classify, recording the reason as an event so preservation is auditable. Implements spec `7ckptx` R5.5, R5.6 and nothing else.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_lane_retention.py
- Item-Dependencies: executed:nna8yz
- From-Spec: 7ckptx
- Blocks-Release: next
- Status: to-review
- Set: lanectn
- Order: 5
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: xdr83v

## Workflow history

- 2026-09-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): fifth child of Set `lanectn`, and deliberately the smallest: 3 E-items. Requires `nna8yz` executed, because classification reads the sealed manifest that plan produces to decide what the driver itself wrote and may therefore discard. Narrower than it looks: the driver ALREADY emits a preservation event, so this plan adds the INVENTORY that decides when to emit it.
- 2026-09-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

A lane is destroyed only when the driver can account for everything in it, and any refusal names the reason in a durable record rather than leaving a surviving directory to be interpreted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

MEASURED DELTA, so do not rewrite what exists: the driver already emits a preservation event today. What is missing is the INVENTORY that decides when preservation is required. Verify the existing event and its emission site before adding anything, and extend rather than replace it.

### Task group 1: classify, then refuse (R5.5, R5.6)

- [ ] E-01 IMPLEMENTS R5.5 (classification). Inventory a lane's contents before teardown, enumerating so that IGNORED files are seen as well as untracked ones. Content the driver itself wrote under the lane control directory is classified discardable, established from the sealed manifest child `nna8yz` produces rather than from a hardcoded path list. Everything else is UNKNOWN.
  - Depends on: none
  - Expected outcome: the inventory reports, for a given lane, the dirty tracked files, the unknown untracked files, the unknown IGNORED files, and whether a submission remains uncollected, with driver-written control content excluded by manifest rather than by a path guess.
  - Execution state: pending
- [ ] E-02 IMPLEMENTS R5.5 (refusal). Make teardown REFUSE while the inventory reports any unknown content: a dirty tracked file, an unknown untracked or ignored file, or an uncollected submission. Only a fully classified lane may be torn down. Fail toward PRESERVATION: if the inventory itself cannot run, refuse rather than proceed, because a destroyed lane is unrecoverable while a preserved one costs only disk.
  - Depends on: E-01
  - Expected outcome: a lane with any unknown content still exists after the teardown call; a fully classified clean lane is removed; and an inventory failure results in preservation, not removal.
  - Execution state: pending
- [ ] E-03 IMPLEMENTS R5.6, and mirrors E-01 and E-02 into the agy twin. Record each refusal as an event naming WHICH condition held, so preservation is auditable rather than inferred from a directory that happens to survive. Extend the existing preservation event rather than adding a second one (CID-2). The two drivers are near-parity twins and a rule present in one only is a DEFECT (CID-3).
  - Depends on: E-02
  - Expected outcome: every refusal emits an event naming the specific condition that caused it, using the existing event rather than a new one, and the agy driver satisfies the same assertions as the oc driver.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Measured at HEAD `59e68d5a`; anchor on symbol names.
- The driver ALREADY emits a lane-preservation event. Extend it; adding a second would fork the rule (CID-2).
- Classification must read the sealed manifest from child `nna8yz` rather than hardcoding which paths the driver wrote, so the two cannot drift.
- The two drivers are near-parity twins; a rule in one only is a DEFECT.
- The suite must be run BARE and `make test-all` separately; a bare run deselects `slow` tests.

## Findings

| id | Finding | Evidence |
| --- | --- | --- |
| F-1 | Ignored files are the specific hazard this plan exists for. Enumerating only untracked content would leave ignored content invisible, and "ignored means disposable" is precisely the reasoning that previously destroyed lane content silently. R5.5 therefore names ignored files explicitly. | Spec `7ckptx` R5.5. |
| F-2 | This is a MEASURED DELTA, not new machinery: the preservation event already exists in the driver. The missing half is the inventory that decides when to emit it, which is why this is the smallest child in the Set. | The driver's existing preservation event and its emission site. |
| F-3 | Failing toward preservation is asymmetric on purpose. A wrongly destroyed lane is unrecoverable and can lose an entire turn's work; a wrongly preserved lane costs disk and a later cleanup. So an inventory that cannot run must refuse, which is the same fail-closed reasoning the repository applies to its execution-authority receipts. | Spec `7ckptx` R5.5; the fail-closed convention used by the lifecycle gate. |
| F-4 | Classification must come from the manifest rather than a path list, or the two definitions of "content the driver wrote" will drift the first time the control layout changes. This is the same single-definition rule CID-2 enforces elsewhere. | Spec `7ckptx` R6.1; child `nna8yz`'s manifest (R5.1). |

## Proposed changes (ordered, validatable)

1. Inventory the lane including ignored files, classifying driver-written content from the manifest (E-01).
2. Refuse teardown on any unknown content, and fail toward preservation if the inventory cannot run (E-02).
3. Record the reason on the existing preservation event, and mirror both into the agy twin (E-03).

## Deferred / out of scope (with reason)

- The manifest itself: child `nna8yz` owns R5.1-R5.4 and is this plan's prerequisite.
- Collecting submissions, which determines whether one is uncollected: child `cqx5v7` owns R2.
- The missing-input pause, which also preserves a lane but for a different reason: child `y5od1h` owns R3.2. Do NOT merge the two paths; they answer different questions and R6.1 is satisfied by each having one definition, not by forcing them together.
- Permission posture and turn bounds: child `lhmrhx` owns R4.
- Shared predicate bodies: child `604wra` owns R6.

## Scope check

- Over-scope: none. Three declared files and the two requirements assigned. This is the smallest child in the Set by design.
- Under-scope: none for its assigned requirements. Retention is not containment: this plan does not affect where a worker may write, only whether its lane may be destroyed afterwards.

## Required tests / validation

One new module, parameterized over BOTH drivers: `tests/test_lane_retention.py`, covering an unknown untracked file, an unknown IGNORED file, a dirty tracked file, an uncollected submission, a fully classified clean lane, and an inventory failure.

Baselines at HEAD `59e68d5a`: bare `python3 -m pytest` -> `3996 passed, 3 skipped, 4 xfailed`; `make test-all` -> `4 failed, 4394 passed, 3 skipped, 4 xfailed`. State the expected count SEPARATELY per invocation: bare `failed == 0`; `make test-all` `failed == 4` with no NEW failure.

## Spec / documentation sync

Spec `7ckptx` is normative; this plan cites requirement ids. No public command surface changes.

## Open questions

### OQ-01: Should a preserved lane be reported anywhere beyond the event, for example in the run summary?

- Blocking: no
- Status: deferred
- Owner: the implementing plan
- Resolution or deferral rationale: DEFERRED as a presentation choice, deliberately not decided here. R5.6 requires the reason be RECORDED as an event, which makes preservation auditable, and that is the contract. Surfacing it in a rendered summary would be a usability improvement, but it touches the run-reporting surface which this plan does not declare in its Scope-Paths, and widening the fence to add it is exactly the scope creep rule 6 of the execution contract forbids. If the executor believes it is worth doing, the conforming action is to RECOMMEND it in the walkthrough for a follow-up, not to add it here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01 (proves R5.5 classification; spec A15)
  - Required evidence: paste the inventory output for a lane containing, at minimum, one unknown untracked file, one unknown IGNORED file, and one driver-written control file, showing the first two reported as unknown and the third excluded as discardable. Paste evidence the exclusion came from the MANIFEST and not a hardcoded path list (show the lookup). Prove the enumeration sees ignored files: if the ignored file is missing from the report, the enumeration is wrong even if the test passes for the untracked one. SABOTAGE REQUIRED, and target the ignored path specifically because that is the case that previously destroyed content silently: drop the ignored-file half of the enumeration, paste the run showing the ignored file is NO LONGER reported as unknown, restore, paste it reported again plus `git status` proving the product is unmodified. An enumeration that passes for untracked files while silently missing ignored ones is the exact defect this requirement exists to prevent.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02 (proves R5.5 refusal; spec A15)
  - Required evidence: paste four cases: an unknown untracked file, an unknown IGNORED file, a dirty tracked file, and an uncollected submission, each showing the lane directory STILL EXISTS after the teardown call. Then paste a fully classified clean lane being removed, so the check is not simply refusing always. Then paste an inventory FAILURE resulting in preservation. SABOTAGE REQUIRED: make the refusal unconditional-pass (always tear down), paste the FAILING assertions, restore, paste them passing plus `git status` proving the product is unmodified.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03 (proves R5.6 and twin parity; spec A15, CID-2, CID-3)
  - Required evidence: paste the recorded event for each refusal condition, showing it names WHICH condition held rather than a generic message. Paste evidence the EXISTING preservation event was extended rather than a second one added (show there is still one emission path). Then paste the parameterized run proving both drivers satisfy the same assertions, showing the parameterization rather than two similar functions, and both whole-suite invocations with expected counts stated separately per invocation.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 3 E-leaves in 1 task group, far under both thresholds and the smallest child in this Set. Classify, refuse, and record are one decision expressed in three steps: a refusal without the inventory has nothing to decide on, and an inventory without the record leaves preservation to be inferred from a surviving directory.

Execution contract: this plan INHERITS the shared execution contract from orchestrator `h0zljh` verbatim, including its ten numbered rules. Restated here because these are the ones most likely to be skipped, and skipping them is how this work gets faked:

1. PROSE IS NEVER EVIDENCE. Paste real command output and exit codes, never a summary of them. A `V-*` whose command was not run stays `Result: pending`.
2. SABOTAGE the central assertions. Break the product behavior deliberately, paste the FAILING run, restore, paste the passing run plus `git status` proving the product is unmodified. This session already produced a test that passed while the product was broken; only sabotage exposed it.
3. ASSERT THE PROPERTY, NOT THE WORDING. Where the requirement states an absence, check the emitted output so a reworded violation still fails.
4. STRUCTURE, NOT GREP, for "only one of these exists". Use AST or the import graph, repo-wide; a text grep is satisfied by the checking code itself.
5. PREREQUISITE IS CHECKED, NOT ASSUMED: child `nna8yz` (Order 02) MUST be in `executed/` before this plan starts, because classification reads the sealed manifest it produces to decide what the driver itself wrote. Verify those symbols exist. If they are absent, STOP and report; do not substitute a hardcoded path list, which would fork the rule (CID-2).
6. THE SCOPE FENCE IS A STOP CONDITION. Touch only the declared `Scope-Paths`. If the work seems to need a sibling's surface, STOP AND REPORT; do not broaden and do not reimplement it, which would fork the rule (CID-2).
7. STATE THE HONEST LIMIT. Where a mechanism is an accident guard rather than a boundary, say so in the code comment and in this plan. Overstating a guarantee is the failure.

Commits are path-scoped and never pushed. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed or hook-interrupted commit.

Post-gate lifecycle: run `aw ipd lint --phase pre-transition`, then `aw ipd finalize`, never a hand edit. If validation did not pass, record `substantially-complete` honestly rather than marking this executed.
