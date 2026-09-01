# IPD: Lane input materialization with a sealed manifest and clean-base guard

- Date: 2026-09-01
- Kind: child
- Concern: An isolated worker is told to use only lane-relative paths (child `cqx5v7`), but nothing guarantees the files it needs are actually IN the lane, and one attachment is still handed to it by its main-checkout path. Separately, a lane is created from `HEAD`, so an uncommitted tracked edit in the target checkout is silently absent from the lane and the worker cannot know it is working against an incomplete base.
- Scope: Materialize required inputs into the lane BY COPY with a sealed manifest, make every `--file` style attachment resolve inside the lane, and refuse to launch an unattended isolated turn from a dirty tracked base. Implements spec `7ckptx` R5.1, R5.1a, R5.2, R5.3, R5.4 and nothing else.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_lane_input_manifest.py, tests/test_lane_clean_base.py
- Item-Dependencies: executed:cqx5v7
- From-Spec: 7ckptx
- Blocks-Release: next
- Status: reviewed
- Set: lanectn
- Order: 2
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: nna8yz

## Workflow history
- 2026-09-01 reviewed (aw set): /aw plan-review round 1 complete; all findings ACCEPTED and resolved. Every one was verified against the artifact before fixing. Two were serious: (1) my orchestrator claimed a proven-complete dependency graph while two children's metadata omitted edges their own prose required, which is the same CLASS of defect that got the predecessor tch3bo rejected - the proof had checked acyclicity only and never metadata-vs-prose agreement; (2) the spec's secret vocabulary was derived from THIS repository's ignore file with no floor, which would admit secrets in a managed target repo, fixed by a maintainer-approved spec amendment adding a built-in floor, union-only composition, and fail-closed behavior. Also fixed: the right-sizing complaint that I complied on E-item count while hiding each second driver's whole implementation in one 'mirror' item (now host-neutral code plus thin adapters), stale hardcoded suite baselines (now measure-at-execution-time and compare failures by identity), a genuine data-model error where retention read the input manifest for OUTPUT collection state (now an attempt-keyed collection receipt owned by the plan that owns collection), and an unfollowable instruction to read docstring owner labels that name superseded phases (now a measured predicate ownership table).

- 2026-09-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): second child of Set `lanectn`. Requires `cqx5v7` executed. Small by construction: 5 E-items across two concerns that share one mechanism (the materializer), which is why R5.3 lives here rather than in `cqx5v7` - putting it there would have created the dependency cycle that got the predecessor `tch3bo` rejected (its E-03 cited a materializer owned by a LATER item).
- 2026-09-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Everything an isolated worker is told to use is provably inside its lane, recorded in a manifest it cannot silently rewrite, and a run never starts from a base that omits uncommitted tracked work.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

HOST-NEUTRAL FIRST, ADAPTERS SECOND. Corrected after `/aw plan-review` finding PR-001: the original E-05 bundled the clean-base refusal WITH mirroring materialization, inode independence, sealing, revision behavior, and attachment localization into the second driver, which are separate failure modes that one checkbox cannot establish. E-01 through E-04 MUST therefore place the materializer, the seal, and the attachment resolution in HOST-NEUTRAL functions both drivers call, so E-05 adds only the clean-base guard plus thin wiring. Re-implementing any of them per driver would fork the rule (CID-2) and is a STOP-and-report condition.

WHY R5.3 IS HERE AND NOT IN `cqx5v7`: making every attachment lane-local requires a lane-local COPY of the runbook, and the copier is E-01 of THIS plan. Assigning R5.3 to `cqx5v7` would have made that plan depend on a mechanism a later plan owns, which is precisely the circular reference that got `tch3bo` rejected (PR-002). Recorded so a later reader does not "tidy" it back.

### Task group 1: materialize inputs by copy (R5.1, R5.1a, R5.2)

- [ ] E-01 IMPLEMENTS R5.1. Add a lane input materializer that COPIES the plan/IPD snapshot and the runbook into the lane at lane-local paths and writes a manifest recording, per entry, the repo-relative path, its class, a source digest, and the materialization mode. Copy-only is the point: a link of any kind back to the original checkout reintroduces the coupling the lane exists to remove.
  - Depends on: none
  - Expected outcome: after materializing a lane, the lane holds the copies and a manifest whose every entry records mode `copy` with a non-empty source digest matching the bytes actually written.
  - Execution state: pending
- [ ] E-02 IMPLEMENTS R5.2. Guarantee LINK INDEPENDENCE, not merely symlink absence. A hard link satisfies a symlink check AND a digest comparison while still sharing an inode with the original, so the materializer must produce files whose identity is independent of the source, and the check must establish that.
  - Depends on: E-01
  - Expected outcome: for every manifest-listed lane file: it is not a symlink, and its inode identity differs from the source file's, so no listed path shares storage with a file outside the lane.
  - Execution state: pending
- [ ] E-03 IMPLEMENTS R5.1a. SEAL the manifest, which spec R5.1a defines as three things and not one: the manifest file itself is written without the owner write bit, each materialized input file is likewise read-only, and any legitimate change to the input set arrives as a NEW REVISION rather than an in-place edit. Label it in the code comment as an accident guard and NOT immutability, because the owning user can restore the write bit.
  - Depends on: E-02
  - Expected outcome: the manifest file and every materialized input have no owner write bit; the code comment states the accident-guard limit; the revision mechanism exists for a later caller (child `y5od1h`) to use without editing entries in place.
  - Execution state: pending

### Task group 2: attachments and base (R5.3, R5.4)

- [ ] E-04 IMPLEMENTS R5.3. Make every `--file` style attachment for an isolated turn resolve inside the lane. MEASURED DELTA so this is narrower than it sounds: the plan path is ALREADY lane-local (the driver passes the lane-resolved plan), but the runbook is still attached by its main-checkout path. Attach the lane-local copy E-01 makes; do not copy it a second time.
  - Depends on: E-01
  - Expected outcome: for an isolated turn, every attachment value in the constructed argv resolves inside the lane, checked over ALL such values with at least two present.
  - Execution state: pending
- [ ] E-05 IMPLEMENTS R5.4, and WIRES the agy twin to the shared materializer. Add a pre-launch guard that refuses an unattended isolated turn when the target checkout has dirty TRACKED paths, naming them, before any worker process is spawned. Untracked files are deliberately EXCLUDED (a lane is made from a commit, so untracked content was never silently omitted the way an uncommitted tracked edit is, and refusing on it would make an unattended run unstartable in any working checkout). REUSE the existing porcelain parser rather than writing a second one, and state in the comment how this differs from the integration-time overlap check: that one asks whether an incoming lane's changed set intersects dirty paths, this one asks whether the whole tracked tree is clean before launch.
  - Depends on: E-04
  - Expected outcome: a dirty tracked file causes refusal before spawn with the paths named; a clean tree proceeds; an untracked file does NOT trigger refusal; and the agy driver satisfies the same assertions as the oc driver.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Measured at HEAD `59e68d5a`; anchor on symbol names.
- The two drivers are near-parity twins; a rule in one only is a DEFECT (CID-3).
- An existing porcelain-parsing helper already backs the integration-time dirty-overlap check. REUSE it (CID-2 forbids forking a rule); the two checks answer different questions and the code comment must say so.
- The suite must be run BARE and `make test-all` separately; a bare run deselects `slow` tests.

## Findings

| id | Finding | Evidence |
| --- | --- | --- |
| F-1 | A hard link defeats the obvious test, which is why R5.2 demands link independence. A hard link is not a symlink and its content digest matches the source exactly, so a check asserting `not islink` plus digest equality PASSES while the lane file still shares an inode with the original. This was raised by the maintainer as a review gap on the spec itself. | Spec `7ckptx` R5.2 and criterion A12; the gap was identified in maintainer review of the spec. |
| F-2 | "Sealed" had no testable meaning until the spec defined it, so an implementation could have claimed it with no read-only anywhere. R5.1a now fixes three concrete parts. | Spec `7ckptx` R5.1a; the word appeared twice in an earlier draft with no definition. |
| F-3 | R5.3 is a MEASURED DELTA, not a rewrite: the plan attachment is already lane-local and only the runbook still names the main checkout. Verifying this before editing avoids re-doing work main already did. | The driver's attachment construction: one attachment uses the lane-resolved plan path, the other uses the runbook's main path. |
| F-4 | The untracked exclusion in R5.4 is deliberate and must not be "fixed" into a stricter check. A lane is created from a commit, so an untracked file's absence from the lane is CORRECT; refusing on untracked files would make an unattended run unstartable in any working checkout. | Spec `7ckptx` R5.4. |

## Proposed changes (ordered, validatable)

1. Add the copy-only materializer with a digested manifest (E-01).
2. Establish link independence, not just symlink absence (E-02).
3. Seal the manifest and inputs read-only, labelled as an accident guard (E-03).
4. Attach the lane-local runbook copy so every attachment is inside the lane (E-04).
5. Refuse a dirty tracked base before spawn, and mirror everything into the agy twin (E-05).

## Deferred / out of scope (with reason)

- The missing-input classifier and the manifest REVISION caller: child `y5od1h` owns R3 and will use the revision mechanism E-03 provides. This plan builds the mechanism; it must not implement the classifier.
- Retention and teardown decisions that READ this manifest: child `xdr83v` owns R5.5-R5.6.
- Permission posture and turn deadlines: child `lhmrhx` owns R4.
- Shared predicate bodies: child `604wra` owns R6.
- Prompt text and submission collection: child `cqx5v7` owns R1-R2 and is this plan's prerequisite.

## Scope check

- Over-scope: none. Four declared files and the five requirements assigned.
- Under-scope: none for its assigned requirements. It does not by itself stop a worker leaving the lane; it removes the legitimate REASONS to (a missing file, a main-path attachment) and refuses an incomplete base.

## Required tests / validation

Two new modules, parameterized over BOTH drivers rather than duplicated: `tests/test_lane_input_manifest.py` (R5.1, R5.1a, R5.2, R5.3) and `tests/test_lane_clean_base.py` (R5.4).

BASELINES MUST BE MEASURED AT EXECUTION TIME, NOT COPIED FROM THIS PLAN. Corrected after `/aw plan-review` (PR-003 on every plan in this Set): the exact counts originally written here were already STALE before execution, because a co-worker's commit `8ced15ce` added two tests, moving the bare suite from `3996 passed` to `3998 passed`. A hardcoded count cannot distinguish an honest change from a regression, and treating it as an expectation would either raise a false alarm or, worse, mask a real failure behind an off-by-two rationalization.

SO DO THIS INSTEAD. Immediately before you start, run BOTH invocations and record their counts as YOUR baseline, pasting them. Then after your change, run both again and COMPARE FAILURES BY TEST IDENTITY, not by total: list the failing test node ids before and after and account for every difference by name. A count that changed with no new failing id is fine and must be explained (usually tests added); a new failing id is a STOP regardless of what the totals do.

TWO INVOCATIONS WITH DIFFERENT SEMANTICS, and the distinction is load-bearing: bare `python3 -m pytest` is expected to have ZERO failures, while `make test-all` carries a known set of PRE-EXISTING CLI-surface declaration failures that are not this plan's to fix. State the expected outcome separately per invocation; a single "failed == 0" claim across both is the contradiction that got the predecessor `tch3bo` flagged (PR-006). Identify the pre-existing set by NAME in your own measurement rather than trusting any number recorded here.

## Spec / documentation sync

Spec `7ckptx` is normative; this plan cites requirement ids. No public command surface changes, so no user-facing documentation change.

## Open questions

### OQ-01: Should the read-only seal apply to the lane's control directory as a whole, or only to the manifest and the materialized inputs?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ONLY the manifest and the materialized inputs, as R5.1a states. Sealing the whole control directory would break the worker's own submissions, which it MUST be able to write: the outcome JSON, the report, and the decisions contribution all live under the lane control root and are the very files child `cqx5v7` collects. A blanket seal would therefore convert a working turn into a permission failure, which is the same class of mistake spec R4.6 exists to prevent for the permission policy. Recorded because "seal the control directory" is the tempting over-application of this requirement.

### OQ-02: May E-05 retain the clean-base guard and every Antigravity materialization concern in one item?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: Round 1 review found that E-05 spans the clean-base refusal, copy materialization, inode independence, sealing, revisions, and attachment localization. Split these concerns or extract and separately validate a shared materializer before execution.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01 (proves R5.1; spec A12)
  - Required evidence: paste the materialized lane listing and the full manifest contents, showing every entry records mode `copy` with a non-empty source digest, and paste a digest comparison proving each lane copy matches the source bytes. SABOTAGE REQUIRED: make the materializer skip the digest (or record a wrong one), paste the FAILING check, restore, paste it passing plus `git status` proving the product is unmodified.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02 (proves R5.2; spec A12)
  - Required evidence: paste, for every manifest-listed lane file, evidence that it is not a symlink AND that its inode identity differs from the source file's. A test asserting only `not islink` plus digest equality does NOT satisfy this item: state explicitly why (a hard link passes both). SABOTAGE REQUIRED: replace one copy with a HARD LINK to the source, paste the FAILING check proving the check catches it, restore, paste it passing.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03 (proves R5.1a; spec A12b)
  - Required evidence: paste the manifest file's mode and each materialized input's mode showing no owner write bit; paste evidence that an attempted in-place edit of an existing manifest entry is refused while a legitimate input change appears as a NEW REVISION; and quote the code comment stating this is an accident guard and NOT immutability. A claim of sealing without all three parts fails this item.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04 (proves R5.3; spec A13)
  - Required evidence: paste the constructed argv for an isolated turn and an assertion over ALL attachment values showing each resolves inside the lane, with at least two values checked so the assertion provably covers both the runbook and the plan. Inspecting a single attachment does not satisfy this item.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05 (proves R5.4 and twin parity; spec A14, CID-3)
  - Required evidence: paste three cases: a dirty TRACKED file causing refusal BEFORE spawn (spawn patched and asserted never called, or the raised error shown) with the dirty paths named; a clean tree proceeding; and an UNTRACKED file NOT triggering refusal. Paste evidence the porcelain parsing REUSES the existing helper rather than a second parser (show the call). Then paste the parameterized run proving both drivers satisfy the same assertions, and both whole-suite invocations with expected counts stated separately per invocation.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 5 E-leaves in 2 task groups, under both thresholds. The two groups share one mechanism: the materializer built in group 1 is what makes group 1's attachment requirement satisfiable, which is why R5.3 is here rather than in the prerequisite plan. Everything separable went to siblings.

Execution contract: this plan INHERITS the shared execution contract from orchestrator `h0zljh` verbatim, including its ten numbered rules. Restated here because these are the ones most likely to be skipped, and skipping them is how this work gets faked:

1. PROSE IS NEVER EVIDENCE. Paste real command output and exit codes, never a summary of them. A `V-*` whose command was not run stays `Result: pending`.
2. SABOTAGE the central assertions. Break the product behavior deliberately, paste the FAILING run, restore, paste the passing run plus `git status` proving the product is unmodified. This session already produced a test that passed while the product was broken; only sabotage exposed it.
3. ASSERT THE PROPERTY, NOT THE WORDING. Where the requirement states an absence, check the emitted output so a reworded violation still fails.
4. STRUCTURE, NOT GREP, for "only one of these exists". Use AST or the import graph, repo-wide; a text grep is satisfied by the checking code itself.
5. PREREQUISITE IS CHECKED, NOT ASSUMED: child `cqx5v7` (Order 01) MUST be in `executed/` before this plan starts, and the lane-relative prompt symbols it added MUST exist. If they are absent, STOP and report; do not reimplement them.
6. THE SCOPE FENCE IS A DECLARATION, NOT A HALT CONDITION. Touch only the declared `Scope-Paths` as a default, and never expand casually; if the work genuinely requires more, MAKE THE EDIT AND JUSTIFY IT in the finalize reconciliation (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path), which is where an unjustified widening is caught. Do NOT halt the run over a scope question. If the work genuinely requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` will refuse to complete until every out-of-scope path you touched carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT at the gate rather than prevented by halting a run. Do NOT halt the run over a scope question. What you must NOT do is REIMPLEMENT a sibling's rule, which would fork it (CID-2): that is a correctness problem, not a scope one, so if a needed rule is missing, say so in the reconciliation reason.
7. STATE THE HONEST LIMIT. Where a mechanism is an accident guard rather than a boundary, say so in the code comment and in this plan. Overstating a guarantee is the failure.

Commits are path-scoped and never pushed. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed or hook-interrupted commit.

Post-gate lifecycle: run `aw ipd lint --phase pre-transition`, then `aw ipd finalize`, never a hand edit. If validation did not pass, record `substantially-complete` honestly rather than marking this executed.
