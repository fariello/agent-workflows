# IPD: Per-host permission posture and driver-side turn bounds

- Date: 2026-09-01
- Kind: child
- Concern: Containment currently has no layer that works without the worker's cooperation. On OpenCode the host permits out-of-lane access by default and nothing requests otherwise; on Antigravity no denial posture exists at all and auto-approve is a DECIDED constraint, so that host contributes nothing at the permission layer. Meanwhile an unanswerable permission request is bounded only by a coarse no-progress timeout, so a turn can wait far longer than it should.
- Scope: Request the strongest permission posture each host actually supports, OBSERVE what took effect rather than assuming, preserve any operator-supplied configuration, and add driver-side deadlines that fire regardless of what the host decides. Implements spec `7ckptx` R4.1, R4.1a, R4.1b, R4.1c, R4.2, R4.3, R4.4, R4.5, R4.6 and nothing else.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_lane_permission_posture.py, tests/test_turn_bounds.py
- Item-Dependencies: executed:cqx5v7
- From-Spec: 7ckptx
- Blocks-Release: next
- Status: to-review
- Set: lanectn
- Order: 3
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: lhmrhx

## Workflow history

- 2026-09-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): third child of Set `lanectn`. Requires `cqx5v7` executed, and that ordering is NORMATIVE not stylistic: spec R4.6 forbids the permission denial landing before the prompt stops naming out-of-lane paths, because the host CURRENTLY PERMITS those writes and denying them first would convert a working run into a hard failure.
- 2026-09-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Every isolated turn has at least one containment layer that does not depend on the worker reading prose, the layer's real strength is RECORDED per host rather than assumed uniform, and no turn can wait indefinitely on a permission request nobody will answer.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

READ R4.6 BEFORE E-01. The permission denial in E-01 MUST NOT be delivered before child `cqx5v7` has removed the out-of-lane paths from the prompt. MEASURED: run `run-20260901T042331Z-118022` recorded ZERO permission events and both workers successfully wrote all five out-of-lane paths, so the host permits them today. Denying access to paths the prompt still names would break a currently-working runner. The `Item-Dependencies` edge encodes this; do not reorder it for convenience.

READ R4.1c BEFORE TOUCHING THE AGY DRIVER. Antigravity's `--dangerously-skip-permissions` default is a DECIDED CONSTRAINT, not a defect: running without it was proven in practice to fail or deadlock repeatedly, and its only alternative requires interactive permissions an unattended turn cannot answer. This plan MUST NOT flip that default. E-05 exists to PIN it, which is a regression guard running in the opposite direction from everything else here.

### Task group 1: host posture, honestly reported (R4.1, R4.1a, R4.2, R4.3)

- [ ] E-01 IMPLEMENTS R4.1 (opencode case), R4.6. For an unattended isolated OpenCode turn, supply a runner-owned permission policy denying external-directory and interactive-question requests, injected through the child environment and NEVER by editing repository configuration. Extend the ONE existing child-env construction rather than forking a second one.
  - Depends on: none
  - Expected outcome: the child environment for an unattended isolated opencode turn carries the policy denying both request kinds, with inherited PATH and the runner's import pin still intact.
  - Execution state: pending
- [ ] E-02 IMPLEMENTS R4.2. OBSERVE the policy that actually took effect and record it on the attempt, or record an explicit unverified marker with its reason. Host configuration precedence can place a managed source above the runner's, so a run that only SETS the policy can believe it is protected when it is not. Never let the observation failure abort the turn: an unobservable policy is recorded as unverified and the turn continues, because the driver-side bounds in E-04 hold regardless.
  - Depends on: E-01
  - Expected outcome: the attempt record carries either the observed effective policy values or an explicit unverified marker naming the reason, plus the host version measured against.
  - Execution state: pending
- [ ] E-03 IMPLEMENTS R4.3, R4.1a, R4.1b. Do NOT blindly overwrite an operator-supplied value for the policy variable: the child env is built from a copy of the process environment, so an operator value would be silently discarded. Either merge it with validation or override it explicitly and loudly, and say which in the code comment. THEN record the per-host capability honestly: for a host with no denial posture, write that fact on the attempt and name the layers that DO apply (prompt purity from child `cqx5v7`, and the bounds from E-04). No artifact may describe such a host as denied.
  - Depends on: E-02
  - Expected outcome: an operator-supplied policy value is either verifiably merged or loudly overridden, never silently dropped; and for a host without a denial posture the attempt record states that plainly and names the layers that apply.
  - Execution state: pending

### Task group 2: driver-side bounds and the role selector (R4.4, R4.5, R4.1c)

- [ ] E-04 IMPLEMENTS R4.4. Add two driver-side bounds that do not trust the host: a seconds-scale deadline armed by an OBSERVED permission request, including a nested child-session request, and an absolute per-turn deadline that output cannot extend. On expiry, terminate through the ONE shared reaper (spec `c4gd2h` R5 forbids a second; do not call a lower-level terminator directly and do not add a bare kill) and record the safe-failure disposition with the bound that fired named.
  - Depends on: E-03
  - Expected outcome: a synthetic unanswered permission request terminates the turn within the permission deadline, demonstrably not at the coarse no-progress bound, with the disposition and the firing bound recorded, and the termination attributable to the shared reaper.
  - Execution state: pending
- [ ] E-05 IMPLEMENTS R4.1c. PIN Antigravity's permission default so this Set cannot regress it. Assert that the skip-permissions option still defaults to on and that the flag is still present on the constructed argv for an unattended turn. This is a guard in the OPPOSITE direction from every other item here: it FAILS if someone "hardens" the host into the interactive posture that was measured to deadlock. Verified at authoring that NO existing test pins this, so it closes a real hole.
  - Depends on: none
  - Expected outcome: a test fails if the skip-permissions default is flipped or the flag is dropped from an unattended turn's argv.
  - Execution state: pending
- [ ] E-06 IMPLEMENTS R4.5, and mirrors E-01 through E-04 into the agy twin where each applies. Ensure an isolated turn's child environment carries the execution-role selector that makes driver-owned lifecycle verbs refuse inside a lane, and state in the code comment that it is an environment selector and NOT a hardened boundary, since a same-user worker can unset it. Note the sanctioned asymmetry: the agy twin gets the bounds and the selector but NO policy document, because that host has no denial posture to request.
  - Depends on: E-04
  - Expected outcome: an in-lane invocation of a driver-owned lifecycle verb refuses with the documented code and performs NO state transition while the driver's own invocation still succeeds; the code comment carries the selector-not-boundary limit; and the agy twin has the bounds and selector with the missing policy document explained rather than silently absent.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Measured at HEAD `59e68d5a`; anchor on symbol names.
- Exactly ONE process reaper exists and spec `c4gd2h` R5 forbids a second; both drivers already delegate to it, verified by AST during `zpbx7o`'s whole-Set verification. E-04 must route through it.
- The child environment is ALREADY explicit and there must stay ONE construction: an earlier change built it from a copy of the process environment and set the execution-role selector. Extend that, do not fork it.
- The execution-role selector is already PROVEN end to end: it was used to stop a real double-finalize that stranded a live run. E-06 generalizes a working mechanism rather than inventing one.
- The suite must be run BARE and `make test-all` separately; a bare run deselects `slow` tests.

## Findings

| id | Finding | Evidence |
| --- | --- | --- |
| F-1 | The ordering constraint is measured, not theoretical. Run `run-20260901T042331Z-118022` recorded ZERO permission events and both workers wrote all five out-of-lane paths successfully, so the host permits them today. Landing the denial before the prompt work would break a working runner. | The run's `events.jsonl` and the presence of both outcome files at their main-repo paths; spec `7ckptx` R4.6. |
| F-2 | Antigravity's auto-approve is a DECIDED CONSTRAINT with operational evidence behind it, not an unclosed gap. Running without `--dangerously-skip-permissions` was proven to fail or deadlock repeatedly, and its only alternative requires interactive permissions an unattended turn cannot answer. Spec Non-goal 7 and R4.1c forbid changing it. | Spec `7ckptx` R4.1 antigravity case and R4.1c; maintainer ruling recorded there. |
| F-3 | A blind environment overwrite is a REAL risk, not hypothetical: the child env is built from a copy of the process environment, so an operator-supplied policy value would be silently discarded with no warning. This was identified in maintainer review of the spec. | The child-env construction copies the process environment; spec `7ckptx` R4.3. |
| F-4 | The host layer contributes NOTHING on Antigravity, permanently and by design, which makes the prompt purity from child `cqx5v7` and the bounds from E-04 load-bearing rather than defence-in-depth on that host. This raises their priority and must be stated rather than glossed. | Spec `7ckptx` R4.1a; the agy driver's permission handling. |
| F-5 | Policy observation must never abort a turn. It is a diagnostic: if the probe cannot run, the correct outcome is an unverified marker plus continuation, because the driver-side bounds hold regardless. Letting a probe failure propagate would kill turns that were otherwise fine, which is strictly worse than the unknown it was trying to remove. | Spec `7ckptx` R4.2; the same reasoning is recorded in the retired predecessor's E-04. |

## Proposed changes (ordered, validatable)

1. Request the opencode denial policy through the existing single child-env construction (E-01).
2. Observe what actually took effect and record it, or record an honest unverified marker (E-02).
3. Preserve an operator-supplied value, and report a host's real capability rather than implying parity (E-03).
4. Add the permission and absolute turn deadlines, reaping through the one shared routine (E-04).
5. Pin the agy permission default so this Set cannot regress it into a deadlock (E-05).
6. Carry the execution-role selector with its honest limit, and mirror the applicable parts into the agy twin (E-06).

## Deferred / out of scope (with reason)

- Prompt text and submission collection: child `cqx5v7` owns R1-R2 and is this plan's prerequisite.
- Input materialization, the sealed manifest, and the clean-base guard: child `nna8yz` owns R5.1-R5.4.
- The missing-input classifier, including the routing of a DENIED permission event into it (R3.7): child `y5od1h` owns R3. This plan produces the denial; that plan classifies what the denial catches.
- Retention and teardown: child `xdr83v` owns R5.5-R5.6.
- Shared predicate bodies: child `604wra` owns R6.
- Changing Antigravity's permission default: spec Non-goal 7 and R4.1c FORBID it. E-05 pins it against exactly that.
- The noise-gated no-progress watchdog: spec Section 5.1 DECLINES it on measurement (920 real stream lines contained zero noise events; the measured live risk on this host is spurious kills, which gating worsens). Implementing it here would be out of scope AND against the spec.

## Scope check

- Over-scope: none. Four declared files and the nine requirements assigned.
- Under-scope: none for its assigned requirements. It does not make containment unbypassable: a same-user worker can unset the role selector, and spec Goal 5 requires that limit be stated rather than closed.

## Required tests / validation

Two new modules, parameterized over BOTH drivers where the requirement applies to both: `tests/test_lane_permission_posture.py` (R4.1, R4.1a, R4.1c, R4.2, R4.3) and `tests/test_turn_bounds.py` (R4.4, R4.5).

The existing `runstop` suites MUST stay green, because E-04 touches the same termination path: run `tests/test_runner_stop.py`, `tests/test_runner_stop_levels12.py`, `tests/test_runner_stop_level3.py`, `tests/test_runner_stop_level4.py`, `tests/test_runner_stop_triggers.py`, and `tests/test_runner_shutdown.py` with the `slow` tests INCLUDED and paste the summary.

Baselines at HEAD `59e68d5a`: bare `python3 -m pytest` -> `3996 passed, 3 skipped, 4 xfailed`; `make test-all` -> `4 failed, 4394 passed, 3 skipped, 4 xfailed`. State the expected count SEPARATELY per invocation: bare `failed == 0`; `make test-all` `failed == 4` with no NEW failure.

## Spec / documentation sync

Spec `7ckptx` is normative; this plan cites requirement ids. No public command surface changes. If E-03's honest per-host reporting appears in any rendered run summary, that text must not claim denial on a host that has none (spec R4.1a).

## Open questions

### OQ-01: If the policy observation in E-02 cannot run, should the turn abort?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO. The observation is a DIAGNOSTIC, not a precondition, and the reasoning is the same one the retired predecessor recorded: if the probe cannot run we record an unverified marker and CONTINUE, because the driver-side deadlines in E-04 bound the turn regardless of what the host decided. Letting a probe failure propagate would abort turns that were otherwise fine, which is strictly worse than the unknown it was trying to eliminate. What is NOT acceptable is recording nothing, because then a run silently believes it is protected; V-02 requires either the observed values or an explicit marker with its reason.

### OQ-02: Should the permission deadline also apply to a NON-isolated turn?

- Blocking: no
- Status: deferred
- Owner: the implementing plan
- Resolution or deferral rationale: DEFERRED, and deliberately not decided here, because the spec scopes R4.4 to an unattended isolated turn and widening it would change behavior for a mode this Set is not chartered to touch (spec R1.3 requires the non-isolated path stay unchanged in child `cqx5v7`, and the same conservatism applies). If the executor finds the bound is trivially applicable to both, it may say so in the walkthrough as a RECOMMENDATION for a follow-up, but it MUST NOT widen the scope in this plan. Recorded as deferred rather than silently narrowed so a reviewer can see the choice was considered.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01 (proves R4.1 opencode case; spec A8)
  - Required evidence: paste the decoded child environment for an unattended isolated opencode turn showing the policy denies BOTH external-directory and interactive-question requests, and showing inherited PATH and the runner's import-pin variable are still present. SABOTAGE REQUIRED: remove the policy injection, paste the FAILING assertion, restore, paste it passing plus `git status` proving the product is unmodified.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02 (proves R4.2; spec A8)
  - Required evidence: paste the attempt record carrying EITHER the observed effective policy values OR an explicit unverified marker with its reason, and state the host version measured against. A run that records neither FAILS this item, because it would leave the run believing it is protected when a higher-precedence source may have overridden the request. Also paste evidence that a probe failure does NOT abort the turn.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03 (proves R4.3, R4.1a; spec A9, A8b)
  - Required evidence: paste two things. First: with an operator-supplied value ALREADY SET for the policy variable, show the resulting child environment either merges it verifiably or overrides it with an explicit loud record; a silent overwrite fails this item. Second: for a host with no denial posture, show the attempt record states that plainly, names the layers that DO apply, and that NO artifact or rendered summary claims denial. Assert the no-claim-of-denial part mechanically, not by reading.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04 (proves R4.4; spec A10)
  - Required evidence: paste a test in which a synthetic UNANSWERED permission request, including the nested child-session shape, causes termination within the permission deadline and demonstrably NOT at the coarse no-progress bound; show the recorded disposition and the name of the bound that fired. Then prove no second reaper was introduced using AST or the import graph over the package, NOT a text grep, since the test file itself contains the symbols. Finally paste the six `runstop` suites with `slow` INCLUDED, green, since this item edits the shared termination path.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05 (proves R4.1c; spec A8c)
  - Required evidence: paste the test asserting the agy skip-permissions option still defaults to on AND that the flag is present on the constructed argv for an unattended turn. SABOTAGE REQUIRED, in the opposite direction from every other sabotage here: flip the default to off, paste the FAILING test proving the guard catches a hardening regression, restore, paste it passing. State in writing that this plan did NOT change that default.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06 (proves R4.5 and twin parity; spec A11, CID-3)
  - Required evidence: paste evidence that an in-lane invocation of a driver-owned lifecycle verb REFUSES with the documented code and performs NO state transition (show the absence of the transition, not just the refusal message), while the driver's own invocation still succeeds. Quote the code comment carrying the selector-not-a-boundary limit. Then paste the parameterized run proving both drivers satisfy the applicable assertions, and state explicitly which assertion does NOT apply to the agy twin and why (no denial posture exists). Finally paste both whole-suite invocations with expected counts stated separately per invocation.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 6 E-leaves in 2 task groups, under both thresholds. The two groups are one concern viewed from two sides: what we ASK the host for, and what we enforce ourselves when the host cannot or will not. They belong together because the honest per-host reporting in E-03 is only meaningful if the fallback layer in E-04 exists, and E-05 pins the constraint that makes the asymmetry permanent.

Execution contract: this plan INHERITS the shared execution contract from orchestrator `h0zljh` verbatim, including its ten numbered rules. Restated here because these are the ones most likely to be skipped, and skipping them is how this work gets faked:

1. PROSE IS NEVER EVIDENCE. Paste real command output and exit codes, never a summary of them. A `V-*` whose command was not run stays `Result: pending`.
2. SABOTAGE the central assertions. Break the product behavior deliberately, paste the FAILING run, restore, paste the passing run plus `git status` proving the product is unmodified. This session already produced a test that passed while the product was broken; only sabotage exposed it.
3. ASSERT THE PROPERTY, NOT THE WORDING. Where the requirement states an absence, check the emitted output so a reworded violation still fails.
4. STRUCTURE, NOT GREP, for "only one of these exists". Use AST or the import graph, repo-wide; a text grep is satisfied by the checking code itself.
5. PREREQUISITE IS CHECKED, NOT ASSUMED: child `cqx5v7` (Order 01) MUST be in `executed/` before this plan starts, and this is a SPEC-NORMATIVE ordering (R4.6), not a convenience: the host currently permits the out-of-lane writes, so denying them while the prompt still names them would break a working runner. Verify the lane-relative prompt symbols exist. If they are absent, STOP and report.
6. THE SCOPE FENCE IS A STOP CONDITION. Touch only the declared `Scope-Paths`. If the work seems to need a sibling's surface, STOP AND REPORT; do not broaden and do not reimplement it, which would fork the rule (CID-2).
7. STATE THE HONEST LIMIT. Where a mechanism is an accident guard rather than a boundary, say so in the code comment and in this plan. Overstating a guarantee is the failure.

Commits are path-scoped and never pushed. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed or hook-interrupted commit.

Post-gate lifecycle: run `aw ipd lint --phase pre-transition`, then `aw ipd finalize`, never a hand edit. If validation did not pass, record `substantially-complete` honestly rather than marking this executed.
