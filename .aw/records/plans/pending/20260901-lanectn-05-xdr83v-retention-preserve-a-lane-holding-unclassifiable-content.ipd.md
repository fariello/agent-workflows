# IPD: Retention: preserve a lane holding unclassifiable content

- Date: 2026-09-01
- Kind: child
- Concern: Teardown currently removes a lane without first asking what is in it, so content the driver cannot account for is destroyed silently. Ignored files are the specific hazard: treating "ignored" as "disposable" is what previously deleted lane content without a record, and a lane can legitimately hold a dirty tracked file or a submission that was never collected.
- Scope: Inventory a lane before teardown and REFUSE while it holds content the driver cannot classify, recording the reason as an event so preservation is auditable. Implements spec `7ckptx` R5.5, R5.6 and nothing else. Also implements R5.6a (added 2026-09-01 by maintainer ruling).
- Scope-Paths: agent_workflows/lane_containment.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_lane_retention.py
- Item-Dependencies: executed:nna8yz
- From-Spec: 7ckptx
- Blocks-Release: next
- Status: reviewed
- Set: lanectn
- Order: 5
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: xdr83v

## Workflow history
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REVIEWED; round 2 is a DISCLOSED SELF-REVIEW (I authored this plan, so it is weaker evidence than round 1, which was independent and performed by codex/gpt-5). Round 1's PR-* findings were all resolved and moved to FIXED in the typed review record; round 2 then found 2 further findings, SR-002, SR-003 (both FIXED), of which four across the Set were defects I INTRODUCED while fixing round 1. Round 2 is appended to the plan-specific typed review record.
- 2026-09-01 reviewed (aw set): /aw plan-review round 1 complete; all findings ACCEPTED and resolved. Every one was verified against the artifact before fixing. Two were serious: (1) my orchestrator claimed a proven-complete dependency graph while two children's metadata omitted edges their own prose required, which is the same CLASS of defect that got the predecessor tch3bo rejected - the proof had checked acyclicity only and never metadata-vs-prose agreement; (2) the spec's secret vocabulary was derived from THIS repository's ignore file with no floor, which would admit secrets in a managed target repo, fixed by a maintainer-approved spec amendment adding a built-in floor, union-only composition, and fail-closed behavior. Also fixed: the right-sizing complaint that I complied on E-item count while hiding each second driver's whole implementation in one 'mirror' item (now host-neutral code plus thin adapters), stale hardcoded suite baselines (now measure-at-execution-time and compare failures by identity), a genuine data-model error where retention read the input manifest for OUTPUT collection state (now an attempt-keyed collection receipt owned by the plan that owns collection), and an unfollowable instruction to read docstring owner labels that name superseded phases (now a measured predicate ownership table).

- 2026-09-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): fifth child of Set `lanectn`, and deliberately the smallest: 3 E-items. Requires `nna8yz` executed, because classification reads the sealed manifest that plan produces to decide what the driver itself wrote and may therefore discard. Narrower than it looks: the driver ALREADY emits a preservation event, so this plan adds the INVENTORY that decides when to emit it.
- 2026-09-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

A lane is destroyed only when the driver can account for everything in it, and any refusal names the reason in a durable record rather than leaving a surviving directory to be interpreted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

HOST-NEUTRAL FIRST, ADAPTERS SECOND. Corrected after `/aw plan-review` finding PR-002: the original E-03 combined refusal-event semantics with mirroring the complete inventory and teardown guard into the second driver, and inventory coverage, classification, fail-closed behavior, teardown refusal, and event identity have different failure modes. E-01 and E-02 MUST place the classification and the refusal in HOST-NEUTRAL functions both drivers call, so E-03 adds only the event detail plus thin wiring.

THE SHARED HOME IS NAMED, and is `agent_workflows/lane_containment.py` (declared first in this plan's `Scope-Paths`). Added 2026-09-01 after a self-review found that requiring host-neutral code while the fence named only the two driver modules told the executor to do something the fence forbade. Put the host-neutral functions THERE. Do NOT improvise a home by putting them in one driver and importing from the other: that makes one host the de-facto shared library, which is the opposite of host-neutral, and spec R2.6 forbids it. If the module does not exist yet, the plan that reaches it first CREATES it; a later plan EXTENDS it.

MEASURED DELTA, so do not rewrite what exists: the driver already emits a preservation event today. What is missing is the INVENTORY that decides when preservation is required. Verify the existing event and its emission site before adding anything, and extend rather than replace it.

### Task group 1: classify, then refuse (R5.5, R5.6)

- [ ] E-01 IMPLEMENTS R5.5 (classification). Inventory a lane's contents before teardown, enumerating so that IGNORED files are seen as well as untracked ones. Content the driver itself wrote under the lane control directory is classified discardable, established from the sealed manifest child `nna8yz` produces rather than from a hardcoded path list. Everything else is UNKNOWN.
  - Depends on: none
  - Expected outcome: the inventory reports, for a given lane, the dirty tracked files, the unknown untracked files, the unknown IGNORED files, and whether a submission remains uncollected. TWO DIFFERENT SOURCES, and conflating them was a real defect caught by `/aw plan-review` (PR-001): driver-written control content is excluded using the sealed INPUT manifest from `nna8yz`, but the uncollected-submission question MUST be answered from the attempt-keyed COLLECTION RECEIPT that `cqx5v7` E-06 emits, because the input manifest cannot know anything about output. Do NOT guess from path presence: that either preserves every successful lane forever or deletes output whose collection failed.
  - Execution state: pending
- [ ] E-02 IMPLEMENTS R5.5 (refusal). Make teardown REFUSE while the inventory reports any unknown content: a dirty tracked file, an unknown untracked or ignored file, or an uncollected submission. Only a fully classified lane may be torn down. Fail toward PRESERVATION: if the inventory itself cannot run, refuse rather than proceed, because a destroyed lane is unrecoverable while a preserved one costs only disk.
  - Depends on: E-01
  - Expected outcome: a lane with any unknown content still exists after the teardown call; a fully classified clean lane is removed; and an inventory failure results in preservation, not removal.
  - Execution state: pending
- [ ] E-03 IMPLEMENTS R5.6, R5.6a, and WIRES the agy twin to the shared inventory. Record each refusal as an event naming WHICH condition held, extending the existing preservation event rather than adding a second one (CID-2). THEN SURFACE IT IN THE RUN'S SUMMARY OUTPUT, not only in the event log (spec R5.6a, maintainer ruling 2026-09-01): the summary must name each preserved lane and the reason. MEASURED justification, which is why this is a requirement and not a nicety: run `run-20260901T042331Z-118022` preserved TWO lanes and mentioned it ZERO times in the summary a human reads, no reader surfaced the event at all, and five preserved lanes were on disk at the time; the maintainer learned work had been stranded by ASKING, not from the run's output. An event nobody reads is close to no record at all, and reporting success in the summary while the log records preservation reproduces the silent-stranding failure this whole effort exists to remove. SCOPE NOTE, checked rather than assumed: the summary is written inside `oc_runipd.py` (`(run_dir / "execution-report.md").write_text(...)`), which this plan ALREADY declares, so no fence widening is required.
  - Depends on: E-02
  - Expected outcome: every refusal emits an event naming the specific condition, using the existing event rather than a new one; the run's summary output names each preserved lane and its reason; and the agy driver satisfies the same assertions as the oc driver.
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

BASELINES MUST BE MEASURED AT EXECUTION TIME, NOT COPIED FROM THIS PLAN. Corrected after `/aw plan-review` (PR-003 on every plan in this Set): the exact counts originally written here were already STALE before execution, because a co-worker's commit `8ced15ce` added two tests, moving the bare suite from `3996 passed` to `3998 passed`. A hardcoded count cannot distinguish an honest change from a regression, and treating it as an expectation would either raise a false alarm or, worse, mask a real failure behind an off-by-two rationalization.

SO DO THIS INSTEAD. Immediately before you start, run BOTH invocations and record their counts as YOUR baseline, pasting them. Then after your change, run both again and COMPARE FAILURES BY TEST IDENTITY, not by total: list the failing test node ids before and after and account for every difference by name. A count that changed with no new failing id is fine and must be explained (usually tests added); a new failing id is a STOP regardless of what the totals do.

TWO INVOCATIONS WITH DIFFERENT SEMANTICS, and the distinction is load-bearing: bare `python3 -m pytest` is expected to have ZERO failures, while `make test-all` carries a known set of PRE-EXISTING CLI-surface declaration failures that are not this plan's to fix. State the expected outcome separately per invocation; a single "failed == 0" claim across both is the contradiction that got the predecessor `tch3bo` flagged (PR-006). Identify the pre-existing set by NAME in your own measurement rather than trusting any number recorded here.

## Spec / documentation sync

Spec `7ckptx` is normative; this plan cites requirement ids. No public command surface changes.

## Open questions

### OQ-01: Should a preserved lane be reported anywhere beyond the event, for example in the run summary?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-01, asked interactively rather than deferred: YES, SURFACE IT IN THE RUN SUMMARY. Recorded as spec R5.6a with criterion A15b. I had deferred this as a presentation nicety and the measurement reversed my own position: run `run-20260901T042331Z-118022` preserved TWO lanes and mentioned it ZERO times in the summary a human reads, nothing that reads run output surfaced the event at all, five preserved lanes were on disk, and the maintainer learned work had been stranded by ASKING rather than from the run's output. An event nobody reads is close to no record at all, and reporting success in the summary while the log records preservation reproduces the silent-stranding failure this effort exists to remove. SCOPE: no fence widening was needed after all, because the summary is written inside `oc_runipd.py`, which this plan already declares.

### OQ-02: What authoritative collection state distinguishes a harvested submission from an uncollected one?

- Blocking: no
- Status: resolved
- Owner: none
- Finding: PR-001, PR-002
- Resolution or deferral rationale: RESOLVED 2026-09-01, and it required a new requirement rather than a choice. The sealed manifest records materialized INPUTS while collection is OUTPUT, so it cannot answer the question, and inferring from path presence either preserves every successful lane forever or deletes output whose collection FAILED. Spec R2.5 now requires an ATTEMPT-KEYED collection record carrying each submission's source digest and destination result, with absence meaning NOT collected and a failed collection recorded as failed rather than omitted. It is emitted by `cqx5v7` E-06, which owns collection, and consumed here; this plan uses the input manifest ONLY for driver-written content.

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
- [ ] V-03 validates E-03 (proves R5.6, R5.6a and twin parity; spec A15, A15b, CID-2, CID-3)
  - Required evidence: paste the RUN SUMMARY OUTPUT for a run that preserved a lane, showing it names the lane and the reason. A test asserting only that the EVENT was written does NOT satisfy this item: that is exactly the state measured on `run-20260901T042331Z-118022` (two lanes preserved, zero summary mentions), so an event-only assertion would pass while reproducing the defect. Then paste the recorded event for each refusal condition, showing it names WHICH condition held rather than a generic message. Paste evidence the EXISTING preservation event was extended rather than a second one added (show there is still one emission path). Then paste the parameterized run proving both drivers satisfy the same assertions, showing the parameterization rather than two similar functions, and both whole-suite invocations with expected counts stated separately per invocation.
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
5. PREREQUISITE IS CHECKED, NOT ASSUMED: child `nna8yz` (Order 02) MUST be in `executed/` before this plan starts, because classification reads the sealed INPUT manifest it produces to decide what the driver itself wrote. It ALSO requires the attempt-keyed COLLECTION RECEIPT from `cqx5v7` E-06 to answer the uncollected-submission question; `cqx5v7` is a transitive prerequisite through `nna8yz`, so no extra edge is needed, but VERIFY the receipt symbol exists before starting. Verify those symbols exist. If they are absent, STOP and report; do not substitute a hardcoded path list, which would fork the rule (CID-2).
6. THE SCOPE FENCE IS A DECLARATION, NOT A HALT CONDITION. Touch only the declared `Scope-Paths` as a default, and never expand casually; if the work genuinely requires more, MAKE THE EDIT AND JUSTIFY IT in the finalize reconciliation (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path), which is where an unjustified widening is caught. Do NOT halt the run over a scope question. If the work genuinely requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` will refuse to complete until every out-of-scope path you touched carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT at the gate rather than prevented by halting a run. Do NOT halt the run over a scope question. What you must NOT do is REIMPLEMENT a sibling's rule, which would fork it (CID-2): that is a correctness problem, not a scope one, so if a needed rule is missing, say so in the reconciliation reason.
7. STATE THE HONEST LIMIT. Where a mechanism is an accident guard rather than a boundary, say so in the code comment and in this plan. Overstating a guarantee is the failure.

Commits are path-scoped and never pushed. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed or hook-interrupted commit.

Post-gate lifecycle: run `aw ipd lint --phase pre-transition`, then `aw ipd finalize`, never a hand edit. If validation did not pass, record `substantially-complete` honestly rather than marking this executed.
