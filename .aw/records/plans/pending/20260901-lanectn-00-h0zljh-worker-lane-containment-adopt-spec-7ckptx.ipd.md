# IPD: Worker lane containment: adopt spec 7ckptx

- Date: 2026-09-01
- Kind: orchestrator
- Concern: Approved spec `7ckptx` defines 36 requirements for containing an isolated (lane) turn, and NONE of them are implemented. The shipped driver emits five absolute out-of-lane paths and then declares them authorized exceptions, so containment currently depends on an agent resolving a self-contradiction correctly on every turn. The predecessor attempt (`tch3bo`) was REJECTED for bundling all of it into one plan with a circular dependency graph that `aw ipd lint` reported as conforming.
- Scope: Sequence six small, independently-executable children that together satisfy every requirement of `7ckptx`, define their dependency order, own the whole-Set verification, and carry the shared anti-greenwash execution contract. Implements no product code itself.
- Scope-Paths: .aw/records/plans/pending, .aw/records/plans/executed, .aw/records/walkthroughs
- Item-Dependencies: none
- From-Spec: 7ckptx
- From-Backlog: vqv9im
- Blocks-Release: next
- Status: reviewed
- Set: lanectn
- Order: 0
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: h0zljh

## Workflow history
- 2026-09-01 reviewed (aw set): /aw plan-review round 1 complete; all findings ACCEPTED and resolved. Every one was verified against the artifact before fixing. Two were serious: (1) my orchestrator claimed a proven-complete dependency graph while two children's metadata omitted edges their own prose required, which is the same CLASS of defect that got the predecessor tch3bo rejected - the proof had checked acyclicity only and never metadata-vs-prose agreement; (2) the spec's secret vocabulary was derived from THIS repository's ignore file with no floor, which would admit secrets in a managed target repo, fixed by a maintainer-approved spec amendment adding a built-in floor, union-only composition, and fail-closed behavior. Also fixed: the right-sizing complaint that I complied on E-item count while hiding each second driver's whole implementation in one 'mirror' item (now host-neutral code plus thin adapters), stale hardcoded suite baselines (now measure-at-execution-time and compare failures by identity), a genuine data-model error where retention read the input manifest for OUTPUT collection state (now an attempt-keyed collection receipt owned by the plan that owns collection), and an unfollowable instruction to read docstring owner labels that name superseded phases (now a measured predicate ownership table).


- 2026-09-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored after spec `7ckptx` was APPROVED by the maintainer (`59e68d5a`). Supersedes the rejected single-plan approach `tch3bo` (PR-001 right-sizing, PR-002 dependency cycle). The partition was validated programmatically BEFORE any child was written: 36 of 36 requirements owned exactly once, zero duplicates, zero unowned, and the dependency graph proven acyclic. The maintainer additionally asked for smaller children and maximum resistance to greenwashing and to a weak executing model, which is why Section "Shared execution contract" below is unusually prescriptive and every child inherits it verbatim.
- 2026-09-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal


Land spec `7ckptx` as six small plans, each independently executable and independently verifiable, in an order that makes the spec's two normative sequencing rules STRUCTURAL rather than advisory.

Success is not "six plans executed". It is: an isolated turn's instructions contain no absolute path outside its lane, an obedient worker's output is never lost, a missing input has a bounded repair path, a lane is never destroyed while holding content the driver cannot classify, and every guarantee is stated with its honest limit.

## Detailed Implementation Checklist (TODO)


Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: sequence and verify the Set

- [ ] E-01 Execute the six children in the Order below, each to `executed/` with its own pasted evidence, honoring the two BLOCKING sequencing rules recorded in the child table. Do not start a child whose declared prerequisite is not in `executed/`; if its symbols are absent, STOP and report rather than proceeding.
  - Depends on: none
  - Expected outcome: children `cqx5v7`, `nna8yz`, `lhmrhx`, `y5od1h`, `xdr83v`, `604wra` are each in `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending
- [ ] E-02 Run the whole-Set verification against spec `7ckptx` Section 4: demonstrate each of A1 through A20 (including A7b, A7c, A8b, A8c, A12b) with pasted command evidence, and write the verification record to `.aw/records/walkthroughs/` (declared in `Scope-Paths`, so E-02 has a legal place to write its own output). Any criterion that cannot be demonstrated MUST be recorded UNVERIFIED with its reason, never silently dropped. Author no product code here.
  - Depends on: E-01
  - Expected outcome: a single verification record demonstrating every acceptance criterion or explicitly recording it unverified with a reason; any FAILING criterion blocks the Set and this orchestrator stays non-terminal.
  - Execution state: pending
- [ ] E-03 Reconcile the records this Set closes: set backlog `vqv9im` to `done` citing the merge evidence, and report (do NOT set) whether spec `7ckptx` has reached `implemented`. An agent may NOT set a spec `implemented`; state the evidence and leave the transition to the maintainer.
  - Depends on: E-02
  - Expected outcome: `vqv9im` is `done` with cited evidence; a written statement of `7ckptx`'s implementation status naming which requirements are demonstrated, addressed to the maintainer for the `implemented` decision.
  - Execution state: pending

## Child IPDs, sequence, and dependencies


Order is by dependency DEPTH, not convenience. `Depth` is the longest path to a child with no prerequisite.

| Order | Id | Depth | Requirements owned | Prerequisite | What it delivers |
| --- | --- | --- | --- | --- | --- |
| 01 | `cqx5v7` | 0 | R1.1, R1.2, R1.3, R1.4, R2.1, R2.2, R2.3, R2.4 | none | The lane-relative prompt AND the collection of the worker's submissions back to the run directory. |
| 02 | `nna8yz` | 1 | R5.1, R5.1a, R5.2, R5.3, R5.4 | `cqx5v7` | Copy-only input materialization with a sealed manifest, all attachments lane-local, and the clean-tracked-base refusal. |
| 03 | `lhmrhx` | 1 | R4.1, R4.1a, R4.1b, R4.1c, R4.2, R4.3, R4.4, R4.5, R4.6 | `cqx5v7` | Per-host permission posture with honest reporting, and the driver-side deadlines that fire regardless of the host. |
| 04 | `y5od1h` | 2 | R3.1, R3.2, R3.3, R3.5, R3.6, R3.7 (R3.3a/-1/-1a/-1b/-2, R3.3b, R3.4 withdrawn) | `nna8yz`, `lhmrhx` | The full missing-input repair cycle, including secret rejection and the manifest revision. |
| 05 | `xdr83v` | 2 | R5.5, R5.6 | `nna8yz` | Retention: refuse teardown while a lane holds unclassifiable content, and record why. |
| 06 | `604wra` | 3 | R6.1, R6.2, R6.3 | `y5od1h`, `lhmrhx` | The shared predicates behind the above, and the fail-loud discipline for the ones this Set does not own. |

PARTITION PROOF, and an honest account of how it was WRONG the first time. The six children own every LIVE requirement id the spec declares (34 after the 2026-09-01 amendment withdrew the permit-and-copy branch and the secret vocabulary), with ZERO duplicates and ZERO unowned, and the graph is acyclic with every prerequisite at a strictly lower depth.

CORRECTED 2026-09-01 after `/aw plan-review` (orchestrator PR-001, children 04/PR-001 and 06/PR-002). The original proof asserted the graph was "complete and acyclic" and was checked for ACYCLICITY ONLY. It never checked that the machine-readable `Item-Dependencies` matched what each child's PROSE required, and two edges were missing: `y5od1h` needed `lhmrhx` (its E-04 routes a denied host-permission event owned by that child) and `604wra` needed `lhmrhx` (its prose said so explicitly). A scheduler reading metadata could therefore have started work before the required seams existed. This is the same CLASS of defect that got the predecessor `tch3bo` rejected, reintroduced in a different form while I claimed to have proven it absent.

THE PROOF NOW VERIFIES BOTH PROPERTIES, and the second one is the one that was missing: (i) the graph is acyclic, and (ii) for every child, the set of ids named in its prose as required-executed is a SUBSET of its `Item-Dependencies`. Verified after correction: zero mismatches across all six children, depths 0/1/1/2/2/3.

RE-VERIFY BOTH before executing, not just the first. An acyclic graph that disagrees with its own prose is exactly as dangerous as a cyclic one, and it passes `aw ipd lint`.

### The two BLOCKING sequencing rules (spec-normative, not preferences)

RULE 1 (spec R2.1): the lane-relative prompt and the collection of submissions MUST SHIP TOGETHER. They are both inside child `01` for exactly this reason and MUST NOT be split into separate plans or separate commits that could land apart. A lane-relative instruction whose output nobody collects fails INVISIBLY: the worker writes inside the lane, the driver's reconciliation reads the run directory, finds nothing, scores the turn from the empty-outcome fallback, and because that disposition is outside the gating set the successful turn silently never finalizes. That is WORSE than the contradiction it replaces.

RULE 2 (spec R4.6): child `03`'s permission denial MUST NOT land before child `01`'s prompt work. MEASURED: the host currently PERMITS the out-of-lane writes (run `run-20260901T042331Z-118022` recorded zero permission events and both workers wrote all five paths), so denying access to paths the prompt still names would convert a currently-working run into a hard failure. The `Depends on` edge from `03` to `01` encodes this; do not reorder it for convenience.

## Completion criteria (the whole Set is done only when)


Numbered so E-02 can cite each one. Every criterion is an OBSERVABLE state, never a claim.

1. All six children are in `.aw/records/plans/executed/` with `- Status: executed`.
2. Every child's `V-*` items carry pasted command output; the count of EMPTY `Observed evidence:` lines
   across the Set is ZERO.
3. Every acceptance criterion of spec `7ckptx` Section 4 (A1-A20 plus A8b, A8c, A12b; A6 AMENDED to test refusal, and A7b, A7b-1, A7b-2, A7b-3, A7c WITHDRAWN with R3.3a on 2026-09-01) is
   demonstrated with pasted evidence, or recorded UNVERIFIED with its reason. Silent omission fails.
4. An isolated prompt from BOTH drivers contains ZERO absolute paths outside the lane root, asserted by
   pattern match over the emitted text (spec R1.1, A1).
5. No exception clause authorizing an out-of-lane path survives anywhere in either driver's prompt
   construction (spec R1.2).
6. A worker's lane-side submission is found by the driver's reconciliation and yields the worker's
   disposition, not the empty-outcome fallback (spec R2.1, A3).
7. Re-running a turn's collection does not duplicate its contribution to the run-wide register, and does
   not remove a sibling lane's (spec R2.3, A4).
8. A missing-input report is REFUSED with a precise record naming the path and the reason, and NOTHING is
   copied into the lane (spec R3.3a as amended 2026-09-01, A6). The former criterion here required a
   derived secret vocabulary; that was withdrawn with the permit-and-copy branch, so an implementation
   that adds one FAILS this criterion rather than exceeding it.
9. On a host with no denial posture, the attempt record says so and no artifact claims denial
   (spec R4.1a, A8b); and Antigravity's `--dangerously-skip-permissions` default is still `True`
   (spec R4.1c, A8c).
10. An unanswerable permission request terminates the turn within its deadline through the ONE shared
    reaper, with the bound named (spec R4.4, A10).
11. A lane holding an unknown untracked OR IGNORED file is not torn down, and an event records the reason
    (spec R5.5, R5.6, A15).
12. CID-1 through CID-5 all pass, with CID-1 and CID-2 established by AST or import graph over
    `agent_workflows/` rather than text grep.
13. Both suite invocations are reported with their expected counts stated SEPARATELY: bare
    `failed == 0`; `make test-all` `failed == 4` with no new failure.
14. `tests/test_wtiso_adversarial.py` still satisfies its own invariant `failed == 0 AND xfailed > 0`,
    with the `xfailed` delta explained per pin.
15. Every mechanism that is an accident guard rather than a boundary is labelled as such in both the code
    comment and the plan (spec Goal 5).

A criterion that cannot be met is a STOP: this orchestrator stays non-terminal and the gap is reported,
rather than the Set being declared complete.

## Cross-IPD validation


Cross-IPD drift checks (CID), verified by E-02. Each is phrased so a text grep cannot satisfy it.

- CID-1 ONE reaper. No child may introduce a second process-terminating implementation; spec `c4gd2h` R5 forbids it. Prove by AST over `agent_workflows/`, repo-wide, NOT per file: at review time exactly one `terminate_process` body exists (`runner_shutdown.py`) and both drivers delegate to it. A per-file check would pass while two copies existed.
- CID-2 ONE predicate per rule. No child may fork a containment rule that another surface already implements (spec R6.1). Prove by showing each rule has one definition and that every consumer imports it.
- CID-3 TWIN PARITY. Every containment change lands in BOTH `oc_runipd.py` and `agy_runipd.py`, or the child states explicitly why a host differs (the only sanctioned asymmetry is the permission posture in R4.1). A rule present in one driver only is a DEFECT, not partial delivery.
- CID-4 NO HOST HARDENING REGRESSION. No child may flip Antigravity's `--dangerously-skip-permissions` default (spec R4.1c). Prove the default is still `True` and the flag is still on the constructed argv.
- CID-5 THE TRIPWIRE NET STILL WORKS. `tests/test_wtiso_adversarial.py` keeps its own stated invariant `failed == 0 AND xfailed > 0`. Children that satisfy a pinned-absent guard MUST convert that pin to a positive test; children that do not MUST leave it pinned. Report the exact `xfailed` count before and after with the delta explained per pin.

## Deferred / out of scope (with reason)


- OS-level confinement: spec Non-goal 2; owned by `fjs11i` and research `q65sz3`.
- Changing Antigravity's permission default: spec Non-goal 7 and R4.1c FORBID it.
- The noise-gated no-progress watchdog: spec Section 5.1 DECLINES it on measurement (920 real stream lines contained zero noise events, and the measured live risk on this host is spurious kills, which gating worsens). A child that implements it is out of scope.
- Relocating machine state, unifying the runners, commit-scope enforcement at the git layer: spec Non-goals 3, 4, 5.
- `dh0uno`: a separate defect fixed by the unmerged `7p9n2v`.

### Proposed changes (ordered, validatable)


1. Execute child `01` (prompt + collection, inseparable).
2. Execute children `02` and `03` (either order; both depend only on `01`).
3. Execute children `04` and `05` (either order; both depend on `02`).
4. Execute child `06` (depends on `04` and `03`).
5. Run the whole-Set verification against spec Section 4 and write the record.
6. Close `vqv9im`; REPORT on `7ckptx`'s implementation status without setting it.

## Scope check


- Over-scope: none. This orchestrator writes no product code; its Scope-Paths are the plan and walkthrough trees only.
- Under-scope: none. Every requirement of `7ckptx` is owned by exactly one child, proven by the partition computation in F-2.

## Required tests / validation


E-02 runs the whole-Set verification.

DO NOT COPY A BASELINE FROM THIS PLAN. Corrected after `/aw plan-review` (PR-003 on every plan in this Set): the counts originally recorded here were already STALE before execution, because a co-worker's commit `8ced15ce` added two tests and moved the bare suite from `3996 passed` to `3998 passed`. A hardcoded total cannot distinguish an honest change from a regression, and it invites exactly the off-by-N rationalization that hides a real failure.

MEASURE, THEN COMPARE BY IDENTITY. Run both invocations immediately before the Set's first child starts and record those counts as the Set's baseline. After each child, run both again and account for every difference by FAILING TEST NODE ID, not by total. A changed total with no new failing id is fine and must be explained; a new failing id is a STOP whatever the totals say.

TWO INVOCATIONS, DIFFERENT EXPECTED OUTCOMES, and the distinction is load-bearing. Bare `python3 -m pytest` is expected to have ZERO failures. `make test-all` carries a known set of PRE-EXISTING CLI-surface declaration failures, reproduced as far back as `5e5da9a0` and probably owned by `0soncw`; they must not get worse and are not this Set's to fix. Identify that set BY NAME in your own measurement rather than trusting a number. A single "failed == 0" claim spanning both invocations is the contradiction `tch3bo` PR-006 flagged.

### Project conventions discovered (Step 0)


- Measured at HEAD `59e68d5a`. Anchor on SYMBOL NAMES; this Set edits these modules so line numbers will move.
- The two host drivers are deliberate near-parity twins; `cdef9c90` is the precedent for changing both symmetrically in one pass.
- Exactly one reaper exists (`runner_shutdown.terminate_process`); both drivers delegate. Verified by AST during `zpbx7o`'s whole-Set verification.
- `wtiso_gate.py` is a fail-loud skeleton: a stub raises `NotImplementedError` naming its owning phase so a premature caller breaks visibly. It is currently imported by NO product module.
- The suite MUST be run BARE (`python3 -m pytest`) AND `make test-all` separately. A bare run deselects `slow` tests: during `zpbx7o` a bare run reported `3996 passed` GREEN while `make test-all` was failing (`mzy2so`). Any child claiming "suite green" MUST say which invocation.
- Validate in the PRIMARY checkout. About 15 `test_run_viewer.py` tests fail in any lane worktree or fresh clone and pass in the primary tree; that is `dh0uno`, not a regression.

### Findings


| id | Finding | Evidence |
| --- | --- | --- |
| F-1 | The predecessor `tch3bo` was rejected for two structural faults this Set is designed to avoid: it bundled everything into one plan (PR-001) and its dependency graph contained a real cycle (PR-002) that structural lint reported as conforming. | `/aw plan-review` verdict on `tch3bo`; the retired plan carries the full record in `.aw/records/plans/superseded/`. |
| F-2 | The partition is provably total and acyclic, computed before authoring. | 36 requirement ids owned across six children, zero duplicates, zero unowned; every prerequisite at a strictly lower depth. |
| F-3 | Containment on Antigravity rests ENTIRELY on children `01` and `03`'s driver-side half, because that host contributes nothing at the permission layer by design (spec R4.1, R4.1c). This raises the priority of child `01` rather than lowering it. | Spec `7ckptx` R4.1 antigravity case; `agy_runipd.py:2767` and the `default=True` at `:4429`. |
| F-4 | The hazard is LATENT, not a live outage, and this Set must not be sold as an outage fix. The host currently permits the out-of-lane writes. | Run `run-20260901T042331Z-118022`: zero permission events, both workers wrote all five out-of-lane paths successfully. |

### Spec / documentation sync


- Spec `7ckptx` is APPROVED and is the normative source; children cite requirement ids rather than restating them.
- Child `06` must update `wtiso_gate.py`'s module docstring to state which predicates are real and which still raise, so the skeleton does not lie about its own state.
- No user-facing documentation changes: this Set changes no public command surface.

## Open questions


### OQ-01: May children 02 and 03 execute in parallel, and may 04 and 05?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THEY MAY, in dependency terms: `02` and `03` both depend only on `01`, and `04` and `05` both depend only on `02`, so no edge orders them relative to each other. But they MUST NOT be run concurrently in this repository, for a reason unrelated to dependencies: `02`, `03`, and `04` all edit `oc_runipd.py` and `agy_runipd.py`, the two most contended files in the tree, and concurrent lanes editing the same file produce a merge conflict the runner cannot resolve. So the recorded answer is SERIAL EXECUTION in Order sequence, with the freedom to swap `02`/`03` or `04`/`05` if a human chooses. This is an EDIT-SERIALIZATION constraint, not a dependency; recorded distinctly so a later reader does not mistake it for one.

### OQ-02: May this Set proceed before its machine-readable dependencies and mirror-item decomposition are corrected?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001, PR-002
- Resolution or deferral rationale: NO execution is safe in the current state. Round 1 review found that `y5od1h` and `604wra` omit required producer edges and that five children hide multiple independently testable concerns inside one mirror item. Revise the child metadata and decomposition, recompute the dependency proof, and re-review the Set before resolving this question.

## Validation and cross-check (verify before reporting the Set complete)


Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls .aw/records/plans/executed/ | grep lanectn` showing all six children present, and for each child paste its `- Status:` line reading `executed`. Then paste, for each child, the count of its V-items and the count at `Result: pass`, plus the count of EMPTY `Observed evidence:` lines, which MUST be zero. A child whose V-items carry prose but no pasted output has not satisfied this item, and reporting it as complete is the greenwashing failure this Set is built to prevent.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the verification record path under `.aw/records/walkthroughs/`, and in it demonstrate EVERY acceptance criterion of spec `7ckptx` Section 4 (A1-A20 plus A8b, A8c, A12b; A6 AMENDED to test refusal, and A7b, A7b-1, A7b-2, A7b-3, A7c WITHDRAWN with R3.3a on 2026-09-01) with the command run and its actual output. For each of CID-1 through CID-5 paste the check and its result, with CID-1 and CID-2 done by AST or import graph over `agent_workflows/` and NOT by text grep (a grep is satisfied by the checking code itself). Paste BOTH suite invocations with their summary lines, reconciled against the baselines above, stating the expected count per invocation separately. Any criterion recorded UNVERIFIED must name its reason; a criterion silently omitted is a validation failure.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `aw backlog set done vqv9im` output with its cited evidence, and paste the written statement of `7ckptx`'s implementation status. State explicitly that the spec was NOT set to `implemented` by an agent and name the maintainer decision it awaits. Claiming the spec implemented, or setting it, fails this item.
  - Observed evidence:
  - Result: pending

## Approval and execution gate


- Size assessment: standard
- Cohesion rationale: 3 E-leaves in 1 task group, far under both thresholds. This orchestrator deliberately does no product work: it sequences, verifies, and reconciles. The product work is partitioned into six children each of which is independently executable and independently verifiable, which is the spec's own stated preference for work spanning several code regions and for a weaker executing tier.

### Shared execution contract (every child INHERITS this verbatim)


These rules exist because a plan is executed by an agent that may be fast, weak, or over-eager. Each rule
names a specific failure it prevents.

1. PROSE IS NEVER EVIDENCE. Every `V-*` must carry the ACTUAL pasted stdout/stderr and exit code of a
   named command, run in this repository at execution time. "Tests pass", "verified", "done", "should
   work", and remembered or expected output are validation FAILURES. A `V-*` whose command was not run
   stays `Result: pending`.
2. A TEST THAT CANNOT FAIL IS NOT A TEST. For every central assertion, SABOTAGE it: break the product
   behavior deliberately, paste the FAILING run, restore, and paste the passing run plus `git status`
   proving the product is unmodified. Measured precedent from this session: a fixture fix PASSED and was
   still wrong, because the assertion passed for an unrelated reason; only sabotage exposed it.
3. ASSERT THE PROPERTY, NOT THE WORDING. Where the spec states an absence (no absolute path outside the
   lane), assert it by pattern-matching the EMITTED OUTPUT, so a reworded violation still fails. A test
   pinned to a specific sentence is satisfied by rephrasing the sentence.
4. STRUCTURE, NOT GREP, FOR "ONLY ONE OF THESE EXISTS". Use AST or the import graph, repo-wide. A text
   grep is satisfied by the checking code itself, and a per-file check passes while two copies exist.
5. CITE THE REQUIREMENT. Every `E-*` names the `7ckptx` requirement id it implements and every `V-*`
   names the acceptance criterion it proves. An item that cites nothing is out of scope by definition.
6. THE SCOPE FENCE IS A DECLARATION, NOT A HALT CONDITION. Touch only the paths in your own
   `Scope-Paths` as a default, and do not expand scope CASUALLY. But if the work GENUINELY requires a
   path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until
   every out-of-scope path you touched carries a `--scope-reason` and every declared-but-unmodified
   path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE. Do NOT halt the run
   over a scope question. The fence exists so the runner can tell afterwards whether an out-of-scope
   file was edited or an in-scope file was not; it was never meant to abort execution, and wording that
   told an executor to stop over scope propagated widely before being corrected on 2026-09-01. Still
   forbidden regardless: editing a sibling child's plan or this orchestrator, and REIMPLEMENTING a rule
   another child owns (that forks the rule, CID-2, which is a correctness problem rather than a scope
   one, so report the missing rule instead of recreating it).
7. PREREQUISITES ARE CHECKED, NOT ASSUMED. Before starting, verify your declared prerequisite child is in
   `executed/` AND that the symbols you depend on exist. If they are absent, STOP and report; do not
   reimplement them, which would fork the rule (CID-2).
8. PATH-SCOPED COMMITS, NEVER PUSH. `git commit -m msg -- <paths>`; never `git add -A`, bare, or `-a`.
   Other agents are active in this checkout. Verify the staged set with `git diff --cached --name-only`
   before every commit and `git restore --staged` anything not yours. RE-VERIFY AFTER ANY FAILED OR
   HOOK-INTERRUPTED COMMIT: observed twice on 2026-09-01, a `pre-commit` stash/restore split a rename so
   the copy committed while the deletion stayed staged.
9. STATE THE HONEST LIMIT. Where a mechanism is an accident guard rather than a boundary, the code comment
   and the plan must say so. Overstating a guarantee is the failure; shipping an honestly-labelled guard
   is not.
10. DO NOT MARK EXECUTED ON UNVERIFIED WORK. Run `aw ipd lint --phase pre-transition`, then
    `aw ipd finalize`, never a hand edit. If validation did not pass, record `substantially-complete`
    honestly instead.
