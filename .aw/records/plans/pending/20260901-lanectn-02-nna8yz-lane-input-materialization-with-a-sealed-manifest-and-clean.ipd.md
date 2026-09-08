# IPD: Lane input materialization with a sealed manifest and clean-base guard

- Date: 2026-09-01
- Kind: child
- Concern: An isolated worker is told to use only lane-relative paths (child `cqx5v7`), but nothing guarantees the files it needs are actually IN the lane, and one attachment is still handed to it by its main-checkout path. Separately, a lane is created from `HEAD`, so an uncommitted tracked edit in the target checkout is silently absent from the lane and the worker cannot know it is working against an incomplete base.
- Scope: Materialize required inputs into the lane BY COPY with a sealed manifest, make every `--file` style attachment resolve inside the lane, and refuse to launch an unattended isolated turn from a dirty tracked base. Implements spec `7ckptx` R5.1, R5.1a, R5.2, R5.3, R5.4 and nothing else.
- Scope-Paths: agent_workflows/lane_containment.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_lane_input_manifest.py, tests/test_lane_clean_base.py
- Item-Dependencies: executed:cqx5v7
- From-Spec: 7ckptx
- Blocks-Release: next
- Status: approved
- Readiness: go-pending-approval
- Set: lanectn
- Order: 2
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: nna8yz
- Approval: 2026-09-05, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-05 approved (aw set): status set to approved
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REVIEWED; round 2 is a DISCLOSED SELF-REVIEW (I authored this plan, so it is weaker evidence than round 1, which was independent and performed by codex/gpt-5). Round 1's PR-* findings were all resolved and moved to FIXED in the typed review record; round 2 then found 1 further findings, SR-002 (FIXED), of which four across the Set were defects I INTRODUCED while fixing round 1. Round 2 is appended to the plan-specific typed review record.
- 2026-09-01 reviewed (aw set): /aw plan-review round 1 complete; all findings ACCEPTED and resolved. Every one was verified against the artifact before fixing. Two were serious: (1) my orchestrator claimed a proven-complete dependency graph while two children's metadata omitted edges their own prose required, which is the same CLASS of defect that got the predecessor tch3bo rejected - the proof had checked acyclicity only and never metadata-vs-prose agreement; (2) the spec's secret vocabulary was derived from THIS repository's ignore file with no floor, which would admit secrets in a managed target repo, fixed by a maintainer-approved spec amendment adding a built-in floor, union-only composition, and fail-closed behavior. Also fixed: the right-sizing complaint that I complied on E-item count while hiding each second driver's whole implementation in one 'mirror' item (now host-neutral code plus thin adapters), stale hardcoded suite baselines (now measure-at-execution-time and compare failures by identity), a genuine data-model error where retention read the input manifest for OUTPUT collection state (now an attempt-keyed collection receipt owned by the plan that owns collection), and an unfollowable instruction to read docstring owner labels that name superseded phases (now a measured predicate ownership table).

- 2026-09-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): second child of Set `lanectn`. Requires `cqx5v7` executed. Small by construction: 5 E-items across two concerns that share one mechanism (the materializer), which is why R5.3 lives here rather than in `cqx5v7` - putting it there would have created the dependency cycle that got the predecessor `tch3bo` rejected (its E-03 cited a materializer owned by a LATER item).
- 2026-09-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Everything an isolated worker is told to use is provably inside its lane, recorded in a manifest it cannot silently rewrite, and a run never starts from a base that omits uncommitted tracked work.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

HOST-NEUTRAL FIRST, ADAPTERS SECOND. Corrected after `/aw plan-review` finding PR-001: the original E-05 bundled the clean-base refusal WITH mirroring materialization, inode independence, sealing, revision behavior, and attachment localization into the second driver, which are separate failure modes that one checkbox cannot establish. E-01 through E-04 MUST therefore place the materializer, the seal, and the attachment resolution in HOST-NEUTRAL functions both drivers call, so E-05 adds only the clean-base guard plus thin wiring. Re-implementing any of them per driver would fork the rule (CID-2) and is a STOP-and-report condition.

THE SHARED HOME IS NAMED, and is `agent_workflows/lane_containment.py` (declared first in this plan's `Scope-Paths`). Added 2026-09-01 after a self-review found that requiring host-neutral code while the fence named only the two driver modules told the executor to do something the fence forbade. Put the host-neutral functions THERE. Do NOT improvise a home by putting them in one driver and importing from the other: that makes one host the de-facto shared library, which is the opposite of host-neutral, and spec R2.6 forbids it. If the module does not exist yet, the plan that reaches it first CREATES it; a later plan EXTENDS it.

WHY R5.3 IS HERE AND NOT IN `cqx5v7`: making every attachment lane-local requires a lane-local COPY of the runbook, and the copier is E-01 of THIS plan. Assigning R5.3 to `cqx5v7` would have made that plan depend on a mechanism a later plan owns, which is precisely the circular reference that got `tch3bo` rejected (PR-002). Recorded so a later reader does not "tidy" it back.

### Task group 1: materialize inputs by copy (R5.1, R5.1a, R5.2)

- [x] E-01 IMPLEMENTS R5.1. Add a lane input materializer that COPIES the plan/IPD snapshot and the runbook into the lane at lane-local paths and writes a manifest recording, per entry, the repo-relative path, its class, a source digest, and the materialization mode. Copy-only is the point: a link of any kind back to the original checkout reintroduces the coupling the lane exists to remove.
  - Depends on: none
  - Expected outcome: after materializing a lane, the lane holds the copies and a manifest whose every entry records mode `copy` with a non-empty source digest matching the bytes actually written.
  - Execution state: performed
- [x] E-02 IMPLEMENTS R5.2. Guarantee LINK INDEPENDENCE, not merely symlink absence. A hard link satisfies a symlink check AND a digest comparison while still sharing an inode with the original, so the materializer must produce files whose identity is independent of the source, and the check must establish that.
  - Depends on: E-01
  - Expected outcome: for every manifest-listed lane file: it is not a symlink, and its inode identity differs from the source file's, so no listed path shares storage with a file outside the lane.
  - Execution state: performed
- [x] E-03 IMPLEMENTS R5.1a. SEAL the manifest, which spec R5.1a defines as three things and not one: the manifest file itself is written without the owner write bit, each materialized input file is likewise read-only, and any legitimate change to the input set arrives as a NEW REVISION rather than an in-place edit. Label it in the code comment as an accident guard and NOT immutability, because the owning user can restore the write bit.
  - Depends on: E-02
  - Expected outcome: the manifest file and every materialized input have no owner write bit; the code comment states the accident-guard limit; the revision mechanism exists for a later caller (child `y5od1h`) to use without editing entries in place.
  - Execution state: performed

### Task group 2: attachments and base (R5.3, R5.4)

- [x] E-04 IMPLEMENTS R5.3. Make every `--file` style attachment for an isolated turn resolve inside the lane. MEASURED DELTA so this is narrower than it sounds: the plan path is ALREADY lane-local (the driver passes the lane-resolved plan), but the runbook is still attached by its main-checkout path. Attach the lane-local copy E-01 makes; do not copy it a second time.
  - Depends on: E-01
  - Expected outcome: for an isolated turn, every attachment value in the constructed argv resolves inside the lane, checked over ALL such values with at least two present.
  - Execution state: performed
- [x] E-05 IMPLEMENTS R5.4, and WIRES the agy twin to the shared materializer. Add a pre-launch guard that refuses an unattended isolated turn when the target checkout has dirty TRACKED paths, naming them, before any worker process is spawned. Untracked files are deliberately EXCLUDED (a lane is made from a commit, so untracked content was never silently omitted the way an uncommitted tracked edit is, and refusing on it would make an unattended run unstartable in any working checkout). REUSE the existing porcelain parser rather than writing a second one, and state in the comment how this differs from the integration-time overlap check: that one asks whether an incoming lane's changed set intersects dirty paths, this one asks whether the whole tracked tree is clean before launch.
  - Depends on: E-04
  - Expected outcome: a dirty tracked file causes refusal before spawn with the paths named; a clean tree proceeds; an untracked file does NOT trigger refusal; and the agy driver satisfies the same assertions as the oc driver.
  - Execution state: performed

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

- Blocking: no
- Status: resolved
- Owner: none
- Finding: PR-001
- Resolution or deferral rationale: RESOLVED 2026-09-01: NO. The materializer, the seal, and attachment resolution must be HOST-NEUTRAL in the declared module `agent_workflows/lane_containment.py`, so E-05 now adds only the clean-base guard plus thin wiring rather than mirroring materialization, inode independence, sealing, revision behavior, and attachment localization in a single item. The inode, owner-write-bit, revision, attachment, and dirty-base assertions are unchanged.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01 (proves R5.1; spec A12)
  - Required evidence: paste the materialized lane listing and the full manifest contents, showing every entry records mode `copy` with a non-empty source digest, and paste a digest comparison proving each lane copy matches the source bytes. SABOTAGE REQUIRED: make the materializer skip the digest (or record a wrong one), paste the FAILING check, restore, paste it passing plus `git status` proving the product is unmodified.
  - Observed evidence: PASS. Lane listing, full manifest, and digest comparison pasted below; every entry records mode `copy` with a non-empty digest matching the bytes on disk. Sabotage (wrong digest) FAILED 4 tests, restored, 24 passed, 0 sabotage markers remain.

    MATERIALIZED LANE LISTING (note every mode is `-r--r--r--`, i.e. 0444):

    ```
    $ ls -la <lane>/.aw/state/lane-inputs/rev-1
    total 20
    drwxr-xr-x 2 ... 4096 Sep  8 00:06 .
    drwxr-xr-x 3 ... 4096 Sep  8 00:06 ..
    -r--r--r-- 1 ...  848 Sep  8 00:06 manifest.json
    -r--r--r-- 1 ...   12 Sep  8 00:06 plan-plan.ipd.md
    -r--r--r-- 1 ...   16 Sep  8 00:06 runbook-runbook.md
    ```

    FULL MANIFEST CONTENTS:

    ```json
    {
      "inputs": [
        {
          "bytes": 12,
          "input_class": "plan",
          "mode": "copy",
          "path": ".aw/state/lane-inputs/rev-1/plan-plan.ipd.md",
          "source_path": "plan.ipd.md",
          "source_sha256": "1c653131076feca0cbc421d7ed543846484638ca444c2c5d816f260abbeaae3f"
        },
        {
          "bytes": 16,
          "input_class": "runbook",
          "mode": "copy",
          "path": ".aw/state/lane-inputs/rev-1/runbook-runbook.md",
          "source_path": null,
          "source_sha256": "9bf40062e6cb9d0da8756c0bb0591942e36a161355debcef5bd4709e62826623"
        }
      ],
      "revision": 1,
      "schema_version": 1,
      "seal_note": "Read-only is an ACCIDENT GUARD, not immutability and not a boundary: the owning user can restore the write bit. A legitimate change to the input set is a NEW REVISION, never an in-place edit of an existing entry.",
      "sealed": true
    }
    ```

    Every entry records `"mode": "copy"` with a non-empty `source_sha256`. `source_path` is `null` for
    the runbook because it came from the coordinator's run directory and has NO repo-relative location;
    an absolute coordinator path is deliberately never recorded (R1.1 applied to the manifest itself).

    DIGEST COMPARISON, lane copy vs source bytes:

    ```
    plan:    recorded=1c653131076feca0 lane=1c653131076feca0 source=1c653131076feca0 match=True
    runbook: recorded=9bf40062e6cb9d0d lane=9bf40062e6cb9d0d source=9bf40062e6cb9d0d match=True
    ```

    SABOTAGE (recorded digest replaced with 64 zeros instead of digesting the written bytes):

    ```
    === SABOTAGE V-01 ACTIVE: digest not computed from written bytes ===
    FAILED tests/test_lane_input_manifest.py::SealTests::test_part_iii_a_change_is_a_new_revision_not_an_edit
    FAILED tests/test_lane_input_manifest.py::MaterializationTests::test_a_wrong_recorded_digest_is_caught
    FAILED tests/test_lane_input_manifest.py::MaterializationTests::test_every_entry_is_a_copy_with_a_matching_digest
    FAILED tests/test_lane_input_manifest.py::LinkIndependenceTests::test_restored_copy_passes_again
    ========================= 4 failed, 20 passed in 2.29s =========================
    ```

    RESTORED, passing, and the product provably unmodified (0 sabotage markers remain):

    ```
    === RESTORED; V-01 sabotage reverted ===
    tests/test_lane_input_manifest.py ........................               [100%]
    ============================== 24 passed in 2.05s ==============================
    $ grep -c "SABOTAGE" agent_workflows/lane_containment.py
    0
    ```
  - Result: pass
- [x] V-02 validates E-02 (proves R5.2; spec A12)
  - Required evidence: paste, for every manifest-listed lane file, evidence that it is not a symlink AND that its inode identity differs from the source file's. A test asserting only `not islink` plus digest equality does NOT satisfy this item: state explicitly why (a hard link passes both). SABOTAGE REQUIRED: replace one copy with a HARD LINK to the source, paste the FAILING check proving the check catches it, restore, paste it passing.
  - Observed evidence: PASS. Hard-link sabotage proves the naive check (`not islink` + digest equality) says OK while the real check FAILS on `st_nlink=2` and identical inode 26107245; symlink and restore cases included. Detail below.

    WHY `not islink` PLUS DIGEST EQUALITY IS INSUFFICIENT, demonstrated rather than asserted. A hard
    link is not a symlink, and its bytes are identical to the source, so both halves of the naive check
    PASS while the lane file still shares one inode with the original - meaning a later write through
    either name mutates the other, which is exactly the coupling the lane exists to remove. Digest
    equality is evidence of FIDELITY and says nothing about INDEPENDENCE.

    ```
    --- BEFORE sabotage: real check ---
    independent: True
    --- AFTER replacing the copy with a HARD LINK ---
    NAIVE check (not islink AND digest equal) says OK: True
      st_nlink=2  lane inode=26107245  source inode=26107245  same=True
    REAL check independent: False
    REAL check violations: ('.aw/state/lane-inputs/rev-1/plan-plan.ipd.md: st_nlink=2 (expected 1); another name shares this inode, so it is a hard link and not an independent copy', '.aw/state/lane-inputs/rev-1/plan-plan.ipd.md: shares inode 26107245 with plan.ipd.md')
    composed manifest conforming: False
    ```

    So the naive check reports OK for the arrangement R5.2 forbids, and `verify_link_independence`
    catches it on BOTH grounds: `st_nlink != 1` and identical `(st_dev, st_ino)`.

    PER-FILE EVIDENCE for every manifest-listed lane file on the clean path
    (`test_a_fresh_copy_is_link_independent` asserts all three per entry): not a symlink,
    `st_nlink == 1`, and `(st_dev, st_ino)` differing from the source's.

    SABOTAGE, RESTORE, AND PASS, as automated tests so they re-run forever:

    ```
    tests/test_lane_input_manifest.py::LinkIndependenceTests::test_hard_link_is_caught PASSED
    tests/test_lane_input_manifest.py::LinkIndependenceTests::test_symlink_is_caught PASSED
    tests/test_lane_input_manifest.py::LinkIndependenceTests::test_restored_copy_passes_again PASSED
    tests/test_lane_input_manifest.py::LinkIndependenceTests::test_a_fresh_copy_is_link_independent PASSED
    ============================== 24 passed in 2.31s ==============================
    ```

    HONEST NOTE on the link-count check: `st_nlink == 1` is sufficient on its own to prove no second
    name shares the storage, which is what makes this hold even when the source is GONE or has no
    repo-relative path (the synthesized runbook). The inode comparison is kept because it NAMES the
    counterparty in the failure message.
  - Result: pass
- [x] V-03 validates E-03 (proves R5.1a; spec A12b)
  - Required evidence: paste the manifest file's mode and each materialized input's mode showing no owner write bit; paste evidence that an attempted in-place edit of an existing manifest entry is refused while a legitimate input change appears as a NEW REVISION; and quote the code comment stating this is an accident guard and NOT immutability. A claim of sealing without all three parts fails this item.
  - Observed evidence: PASS. Manifest and both inputs are mode 0444; in-place edits raise PermissionError; a legitimate change appears as rev-2 with rev-1 byte-identical; the accident-guard/NOT-immutability comment is quoted below.

    PART (i) and (ii), MODES with no write bit anywhere:

    ```
    === MODES (R5.1a parts i and ii) ===
    manifest manifest.json: 0444
    input .aw/state/lane-inputs/rev-1/plan-plan.ipd.md: 0444
    input .aw/state/lane-inputs/rev-1/runbook-runbook.md: 0444

    verify_lane_input_seal: True
    verify_lane_input_manifest: True
    ```

    PART (iii), in-place edit REFUSED and a legitimate change arriving as a NEW REVISION:

    ```
    === R5.1a (iii): in-place edit REFUSED, change arrives as a NEW REVISION ===
    in-place manifest edit REFUSED: PermissionError Permission denied
    in-place input edit REFUSED: PermissionError Permission denied
    new revision: rev-2 at rev-2
    rev-1 manifest byte-identical after the revision: True
    latest revision: 2
    both revisions conform: True True
    ```

    Note `rev-1 manifest byte-identical after the revision: True`: the earlier revision's record is not
    reopened, which is what makes part (iii) structural rather than a convention.

    THE CODE COMMENT, quoted verbatim from `agent_workflows/lane_containment.py` on `SEALED_FILE_MODE`:

    ```
    #: HONEST LIMIT, and it must be stated wherever this is used (spec R5.1a, plan E-03 / V-03): this is
    #: an ACCIDENT GUARD, NOT IMMUTABILITY and NOT a boundary. The owning user can restore the write bit
    #: with one `chmod`, and the worker RUNS AS the owning user. What it buys is that an accidental
    #: in-lane write - a stray editor save, a script that rewrites what it meant to read - FAILS LOUDLY
    #: instead of silently rewriting the record of what was authorized. Under the threat model in spec 0.2
    #: (an honest worker that can be confused, not an adversary) that is the whole intent. Any artifact
    #: describing this as immutability is WRONG and spec R5.1a forbids it.
    ```

    The same limit travels IN the artifact (the manifest's own `seal_note` field, quoted under V-01), so
    a reader of the manifest alone cannot mistake the seal for immutability.
    `test_the_artifact_states_the_accident_guard_limit` asserts the property on both surfaces, and
    `test_a_restored_write_bit_is_detected` sabotages the seal and proves the check refuses it.

    ON THE REVISION MECHANISM'S CONSUMER, recorded because this plan's prose implies one that cannot
    exist: spec R3.4 was WITHDRAWN by R3.3a, so nothing is ever materialized on request and no caller
    needs to revise a manifest. R3.4 permits the MECHANISM to be built by the plan owning the manifest
    "on the condition that it MUST state that it has no consumer rather than implying one", so
    `revise_lane_inputs` states exactly that, and
    `RevisionMechanismHasNoProductCallerTests::test_revise_lane_inputs_is_not_called_by_product_code`
    enforces it by AST over the whole package (not grep, per execution-contract rule 4). See decision
    03-nna8yz-D2.
  - Result: pass
- [x] V-04 validates E-04 (proves R5.3; spec A13)
  - Required evidence: paste the constructed argv for an isolated turn and an assertion over ALL attachment values showing each resolves inside the lane, with at least two values checked so the assertion provably covers both the runbook and the plan. Inspecting a single attachment does not satisfy this item.
  - Observed evidence: PASS. Real `opencode run` argv captured from the product path: both `--file` values resolve inside the lane, neither main-checkout path appears, asserted over ALL values. Corrects this plan's finding F-3 (see decision D1). Detail below.

    THE REAL ARGV, captured from the product `run_opencode` path (Popen intercepted at the
    `opencode run` invocation, so this is what the child would have received):

    ```
    ['opencode', 'run', '--dir', '/tmp/tmp5cieznjd/lane', '--format', 'json', '--auto',
     '--title', 'aw-exec-run-x-lanectn-nna8yz',
     '--file', '/tmp/tmp5cieznjd/lane/.aw/state/lane-inputs/rev-1/runbook-runbook.md',
     '--file', '/tmp/tmp5cieznjd/lane/.aw/state/lane-inputs/rev-1/plan-20260901-lanectn-02-nna8yz-x.ipd.md',
     '--', 'do the thing']
    ```

    ASSERTION OVER ALL ATTACHMENT VALUES (two present, covering BOTH the runbook and the plan):

    ```
    ALL --file values (count=2):
        /tmp/tmp5cieznjd/lane/.aw/state/lane-inputs/rev-1/runbook-runbook.md
        /tmp/tmp5cieznjd/lane/.aw/state/lane-inputs/rev-1/plan-20260901-lanectn-02-nna8yz-x.ipd.md

    lane root: /tmp/tmp5cieznjd/lane
    attachments OUTSIDE the lane: []

    RESULT: all 2 attachments resolve INSIDE the lane

    main-checkout plan path passed in : /tmp/tmp5cieznjd/main/.aw/records/plans/pending/20260901-...ipd.md
      present in argv? False
    coordinator runbook path in state: /tmp/tmp5cieznjd/coordinator/runbook.md
      present in argv? False
    ```

    The assertion is over ALL values via `attachment_values` / `attachments_outside_lane` (realpath on
    both sides, so a symlinked lane or a `..` segment cannot masquerade as contained), not over one
    hand-picked attachment.

    THIS PLAN'S FINDING F-3 IS WRONG AND THE CORRECTION IS PART OF THE RESULT. F-3 states the plan
    attachment "is ALREADY lane-local (the driver passes the lane-resolved plan)" and that only the
    runbook needed changing. MEASURED at `44d4950d`: `execute_item` passes `lane_plan_path` to
    `build_prompt` (so the PROMPT names the lane copy, which is what F-3 actually observed) but passes
    the OUTER `plan_path` - `resolve_plan_path(repo, ...)` against MAIN, line 5922 - to
    `run_opencode`, which is what becomes `--file`. So BOTH attachments named the main checkout and
    both are now localized. Following F-3 literally would have left R5.3 false for one of two
    attachments. Recorded as decision 03-nna8yz-D1.

    SABOTAGE, as a permanent test: `test_an_out_of_lane_attachment_is_detected` feeds the PRE-CHANGE
    argv shape and proves the check reports the out-of-lane value, so a regression cannot pass silently.

    ```
    tests/test_lane_input_manifest.py::AttachmentLocalizationTests::test_both_attachments_are_localized PASSED
    tests/test_lane_input_manifest.py::AttachmentLocalizationTests::test_an_out_of_lane_attachment_is_detected PASSED
    tests/test_lane_input_manifest.py::AttachmentLocalizationTests::test_a_non_isolated_turn_is_untouched PASSED
    tests/test_lane_input_manifest.py::AttachmentLocalizationTests::test_traversal_cannot_masquerade_as_contained PASSED
    ```

    ASYMMETRY WITH THE AGY TWIN IS REAL, NOT AN OMISSION: that driver has no `--file` surface at all
    (it passes the prompt inline via `-p`), so there is no attachment to localize.
    `test_agy_driver_has_no_file_attachment_surface` pins that premise, so a later `--file` addition
    there fails loudly instead of silently escaping R5.3.
  - Result: pass
- [x] V-05 validates E-05 (proves R5.4 and twin parity; spec A14, CID-3)
  - Required evidence: paste three cases: a dirty TRACKED file causing refusal BEFORE spawn (spawn patched and asserted never called, or the raised error shown) with the dirty paths named; a clean tree proceeding; and an UNTRACKED file NOT triggering refusal. Paste evidence the porcelain parsing REUSES the existing helper rather than a second parser (show the call). Then paste the parameterized run proving both drivers satisfy the same assertions, and both whole-suite invocations with expected counts stated separately per invocation.
  - Observed evidence: PASS. All three R5.4 cases hold for BOTH drivers (dirty tracked refuses and names paths, clean proceeds, untracked does NOT refuse), guard precedes spawn and allocation, parser reuse removed a pre-existing fork, two sabotage directions caught. Both suite invocations compared by identity: zero new failures. Detail below.

    THE THREE CASES, on a real git checkout, PARAMETERIZED OVER BOTH DRIVERS (each test loops the
    `DRIVERS` tuple, so every assertion below holds for `oc_runipd` and `agy_runipd` alike):

    ```
    tests/test_lane_clean_base.py::CleanBaseOnARealRepositoryTests::test_case_1_a_dirty_tracked_file_refuses_and_names_it PASSED
    tests/test_lane_clean_base.py::CleanBaseOnARealRepositoryTests::test_case_1_a_staged_tracked_change_also_refuses PASSED
    tests/test_lane_clean_base.py::CleanBaseOnARealRepositoryTests::test_case_2_a_clean_tree_proceeds PASSED
    tests/test_lane_clean_base.py::CleanBaseOnARealRepositoryTests::test_case_3_an_untracked_file_does_NOT_refuse PASSED
    tests/test_lane_clean_base.py::CleanBaseOnARealRepositoryTests::test_both_drivers_agree_on_every_case PASSED
    ```

    Case 1 asserts the dirty path is BOTH in `result.dirty_paths` and NAMED in `result.reason`; case 3
    asserts `clean` is True and `dirty_paths` is empty with two untracked files present.
    `test_both_drivers_agree_on_every_case` walks clean -> untracked-only -> dirty-tracked and asserts
    the two hosts return the SAME verdict at each step, giving `[True, True, False]`.

    BEFORE SPAWN, asserted structurally on each driver's `execute_item`
    (`test_guard_precedes_spawn_and_allocation`): the guard's position precedes BOTH the launch call
    (`run_opencode(` / `run_agy_turn(`) and `allocate_isolation_worktree(`. It is placed ahead of
    `driver_begin` too, so a refusal leaves NO lifecycle side effect to unwind - no receipt, no lane.
    `test_refusal_records_the_dirty_paths_on_the_attempt` proves the refusal is auditable
    (`attempt["clean_base_dirty_paths"]` plus a `clean-base-refused` event), not merely printed.

    THE PARSER IS REUSED, NOT FORKED, and this actually REMOVED a pre-existing duplicate. The porcelain
    parsing was written out twice, verbatim, in `oc_runipd.dirty_tree_overlap` and
    `agy_runipd.dirty_tree_overlap`; both now call the shared predicate, and the guard uses the same one
    rather than adding a third copy:

    ```python
    # both drivers, dirty_tree_overlap:
    _rc, out, _err = _run_git(repo, ["status", "--short", "--untracked-files=all"])
    return sorted(incoming & lane_containment.parse_porcelain_paths(out))

    # both drivers, evaluate_clean_base_for_launch:
    _rc, out, _err = _run_git(repo, ["status", "--porcelain", "--untracked-files=no"])
    return lane_containment.evaluate_clean_base(out)
    ```

    `test_both_guards_delegate_to_the_shared_rule` and
    `test_dirty_tree_overlap_no_longer_forks_the_parser` assert the delegation AND the absence of the
    hand-rolled loop, for both hosts. `test_overlap_behaviour_is_preserved_after_the_refactor` proves
    the refactor did not change what `dirty_tree_overlap` answers.

    THE TWO CHECKS ANSWER DIFFERENT QUESTIONS, asserted as behaviour rather than only stated in a
    comment (`test_the_two_checks_answer_different_questions`): with `b.txt` dirty and an incoming
    change of `a.txt` only, `dirty_tree_overlap` returns `[]` (no overlap, integration permitted) while
    the clean-base guard REFUSES (the base is incomplete regardless of which paths a lane will touch).

    SABOTAGE, both directions. (1) Guard forced to always report clean:

    ```
    === SABOTAGE V-05 ACTIVE: guard always reports clean ===
    FAILED tests/test_lane_clean_base.py::CleanBaseRuleTests::test_dirty_tracked_paths_are_named
    FAILED tests/test_lane_clean_base.py::CleanBaseRuleTests::test_a_rename_dirties_both_endpoints
    FAILED tests/test_lane_clean_base.py::CleanBaseOnARealRepositoryTests::test_both_drivers_agree_on_every_case
    FAILED tests/test_lane_clean_base.py::CleanBaseOnARealRepositoryTests::test_case_1_a_dirty_tracked_file_refuses_and_names_it
    FAILED tests/test_lane_clean_base.py::CleanBaseOnARealRepositoryTests::test_case_1_a_staged_tracked_change_also_refuses
    FAILED tests/test_lane_clean_base.py::SharedPredicateTests::test_the_two_checks_answer_different_questions
    ========================= 6 failed, 9 passed in 0.45s ==========================
    ```

    (2) The OPPOSITE sabotage, guarding against the tempting wrong "fix" of tightening the guard to
    include untracked files (which finding F-4 forbids). Note it trips the CID-3 parity test too:

    ```
    === SABOTAGE ACTIVE: oc guard tightened to include untracked files ===
    E   AssertionError: hosts disagree: [(False, ('untracked.txt',)), (True, ())]
    FAILED tests/test_lane_clean_base.py::CleanBaseOnARealRepositoryTests::test_case_3_an_untracked_file_does_NOT_refuse
    FAILED tests/test_lane_clean_base.py::CleanBaseOnARealRepositoryTests::test_both_drivers_agree_on_every_case
    ========================= 2 failed, 13 passed in 0.48s ==========================
    ```

    RESTORED and passing, with no sabotage markers left in the product:

    ```
    === RESTORED ===
    agent_workflows/oc_runipd.py:0
    agent_workflows/lane_containment.py:0
    tests/test_lane_input_manifest.py ........................               [ 61%]
    tests/test_lane_clean_base.py ...............                            [100%]
    ============================== 39 passed in 2.32s ==============================
    ```

    BOTH WHOLE-SUITE INVOCATIONS, WITH EXPECTATIONS STATED SEPARATELY PER INVOCATION. Baselines were
    MEASURED THIS TURN, not copied from this plan, and failures are compared BY TEST IDENTITY.

    (a) BARE `python3 -m pytest`. Expectation per this plan: zero failures. ACTUAL: 15 failures both
    before and after, all ENVIRONMENTAL and none in this plan's scope, so the honest expectation for a
    lane-executed run is "the failing set is unchanged by identity". Run with `env -u AW_EXECUTION_ROLE`
    because this turn's own worker role marking otherwise fails 17 further tests that assert the driver
    is not worker-marked (see decision 03-nna8yz-D3 for the per-group attribution).

    ```
    BEFORE: 15 failed, 5634 passed, 3 skipped, 2 xfailed in 92.43s
    AFTER:  15 failed, 5673 passed, 3 skipped, 2 xfailed in 67.61s

    $ diff baseline_ids.txt final_ids.txt
    IDENTICAL: no new failures by identity (15 pre-existing, all environmental)
    ```

    The +39 passed is exactly this plan's two new modules (24 + 15). The 15 pre-existing failures are 14
    in `tests/test_run_viewer.py` (its `discover_run_dirs` needs a non-empty gitignored
    `.aw/records/runs/`, absent in a fresh lane) plus `test_runprofile_refuses_for_R2_...` (pins plan
    `kgpptv` as `reviewed` while main now has it `approved`).

    (b) `make test-all`. Expectation per this plan: a KNOWN set of pre-existing CLI-surface declaration
    failures that are not this plan's to fix. Identified by NAME through my own measurement (my changes
    stashed, then restored) rather than trusting any recorded number:

    ```
    BASELINE (my changes stashed): 57 failed, 6095 passed, 3 skipped, 2 xfailed in 236.74s
    AFTER:                         21 failed, 6131 passed, 3 skipped, 2 xfailed in 385.70s

    === NEW failures introduced by my change ===
    (none)

    === excluding my two new modules from both sides ===
    baseline: 21   after: 21
    IDENTICAL: 21 pre-existing failures, unchanged
    ```

    The 57 -> 21 drop is an artifact of the baseline measurement: with my product code stashed, my own
    36 new tests failed. Excluding my two modules from BOTH sides gives 21 = 21, byte-identical by node
    id. The 21 pre-existing failures are the CLI-surface declaration set
    (`test_cli_conformance_matrix.py` x2, `test_command_surface_declarations.py`,
    `test_installer.py`, `test_cli.py`, `test_runner_stop_triggers.py`), the 14 `test_run_viewer.py`
    tests, and the orchestrator-retirement test named above.

    ONE OUT-OF-SCOPE EDIT, disclosed rather than hidden: `tests/test_runner_shared.py` pins call-site
    COUNTS to prove no existing call site was rewritten, and the guard's refusal branch adds one
    `save_state` caller per driver. Recorded as a documented additive entry exactly as the file's two
    prior rulings were (decision 03-nna8yz-D4); it will carry a `--scope-reason` at finalize.
    `python3 -m pytest tests/test_runner_shared.py` -> 43 passed.
  - Result: pass

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
