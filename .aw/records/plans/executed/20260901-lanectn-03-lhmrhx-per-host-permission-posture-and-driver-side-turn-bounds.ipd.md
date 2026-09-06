# IPD: Per-host permission posture and driver-side turn bounds

- Date: 2026-09-01
- Kind: child
- Concern: Containment currently has no layer that works without the worker's cooperation. On OpenCode the host permits out-of-lane access by default and nothing requests otherwise; on Antigravity no denial posture exists at all and auto-approve is a DECIDED constraint, so that host contributes nothing at the permission layer. Meanwhile an unanswerable permission request is bounded only by a coarse no-progress timeout, so a turn can wait far longer than it should.
- Scope: Request the strongest permission posture each host actually supports, OBSERVE what took effect rather than assuming, preserve any operator-supplied configuration, and add driver-side deadlines that fire regardless of what the host decides. Implements spec `7ckptx` R4.1, R4.1a, R4.1b, R4.1c, R4.2, R4.3, R4.4, R4.5, R4.6 and nothing else. Also implements R4.4a (added 2026-09-01 by maintainer ruling). Also implements R4.4b (the permission bound ships disabled until detection is proven), R4.4c (no new config or CLI surface; KISS), and R4.4d (document the antigravity 240m overlap).
- Scope-Paths: agent_workflows/lane_containment.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_lane_permission_posture.py, tests/test_turn_bounds.py
- Item-Dependencies: executed:cqx5v7
- From-Spec: 7ckptx
- Blocks-Release: next
- Status: executed
- Readiness: go-pending-approval
- Set: lanectn
- Order: 3
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: lhmrhx

## Workflow history
- 2026-09-06 executed (aw oc run): aw oc run self-finalize: lhmrhx verified (set lanectn, attempt 1).
- 2026-09-05 executed (aw oc run, run-20260905T211011Z-3780617 position 8): all six E-items performed and all six V-items verified with pasted evidence. THREE THINGS A READER SHOULD KNOW. (1) `PERMISSION_TIMEOUT` SHIPS AT `0`, NOT 30s: V-04's required-evidence text says 30s, but E-04 / spec R4.4b / criterion A10c all require it disabled until detection is proven against a real ask, and detection is NOT proven (the host exposes no flag to force an ask, the last real run's stdout carried zero permission events, and the motivating evidence came from opencode's log file rather than stdout). A10c option (ii) was taken and the consequence is written down: `MAX_TURN_TIMEOUT` is currently the only bound covering a permission deadlock. See DECISION 08-lhmrhx-D1 and D2. (2) SABOTAGE CAUGHT A REAL TEST DEFECT: V-01's first test asserted the injection by SOURCE TEXT and stayed GREEN while the product was broken; it was replaced with one that captures the env actually handed to `Popen`, which fails on the sabotaged product. (3) ONE PRE-EXISTING TEST NEEDED ACCOMMODATION: `test_runner_stop.py::PollWiringTests` measures character distance between `watchdog.touch()` and the in-turn poll, and my comment pushed the poll out of its window; since that file is outside this plan's Scope-Paths I shortened my own comment rather than widening someone else's test. R4.4d resolved by OFFSET (D3) so the driver bound fires first on antigravity and a kill is attributable; the posture stays isolation-scoped while the bounds are uniform (D4).
- 2026-09-05 approved (aw set): status set to approved
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REVIEWED; round 2 is a DISCLOSED SELF-REVIEW (I authored this plan, so it is weaker evidence than round 1, which was independent and performed by codex/gpt-5). Round 1's PR-* findings were all resolved and moved to FIXED in the typed review record; round 2 then found 1 further findings, SR-002 (FIXED), of which four across the Set were defects I INTRODUCED while fixing round 1. Round 2 is appended to the plan-specific typed review record.
- 2026-09-01 reviewed (aw set): /aw plan-review round 1 complete; all findings ACCEPTED and resolved. Every one was verified against the artifact before fixing. Two were serious: (1) my orchestrator claimed a proven-complete dependency graph while two children's metadata omitted edges their own prose required, which is the same CLASS of defect that got the predecessor tch3bo rejected - the proof had checked acyclicity only and never metadata-vs-prose agreement; (2) the spec's secret vocabulary was derived from THIS repository's ignore file with no floor, which would admit secrets in a managed target repo, fixed by a maintainer-approved spec amendment adding a built-in floor, union-only composition, and fail-closed behavior. Also fixed: the right-sizing complaint that I complied on E-item count while hiding each second driver's whole implementation in one 'mirror' item (now host-neutral code plus thin adapters), stale hardcoded suite baselines (now measure-at-execution-time and compare failures by identity), a genuine data-model error where retention read the input manifest for OUTPUT collection state (now an attempt-keyed collection receipt owned by the plan that owns collection), and an unfollowable instruction to read docstring owner labels that name superseded phases (now a measured predicate ownership table).

- 2026-09-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): third child of Set `lanectn`. Requires `cqx5v7` executed, and that ordering is NORMATIVE not stylistic: spec R4.6 forbids the permission denial landing before the prompt stops naming out-of-lane paths, because the host CURRENTLY PERMITS those writes and denying them first would convert a working run into a hard failure.
- 2026-09-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Every isolated turn has at least one containment layer that does not depend on the worker reading prose, the layer's real strength is RECORDED per host rather than assumed uniform, and no turn can wait indefinitely on a permission request nobody will answer.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

HOST-NEUTRAL FIRST, ADAPTERS SECOND, AND THIS ONE IS A SELECTIVE PORT. Corrected after `/aw plan-review` finding PR-001: the original E-06 combined the role selector with every applicable agy mirror of policy reporting, operator-value handling, event observation, both deadlines, termination, and safe-failure recording. Because the agy host has NO policy document by design (R4.1), that was never a mechanical mirror, which makes an omitted seam likely. So the deadlines, the reporting, and the safe-failure recording MUST be host-neutral functions both drivers call; E-06 wires them and adapts this host's event shapes. It MUST also mark the policy-document step explicitly INAPPLICABLE for agy rather than leaving its absence to be inferred.

THE SHARED HOME IS NAMED, and is `agent_workflows/lane_containment.py` (declared first in this plan's `Scope-Paths`). Added 2026-09-01 after a self-review found that requiring host-neutral code while the fence named only the two driver modules told the executor to do something the fence forbade. Put the host-neutral functions THERE. Do NOT improvise a home by putting them in one driver and importing from the other: that makes one host the de-facto shared library, which is the opposite of host-neutral, and spec R2.6 forbids it. If the module does not exist yet, the plan that reaches it first CREATES it; a later plan EXTENDS it.

READ R4.6 BEFORE E-01. The permission denial in E-01 MUST NOT be delivered before child `cqx5v7` has removed the out-of-lane paths from the prompt. MEASURED: run `run-20260901T042331Z-118022` recorded ZERO permission events and both workers successfully wrote all five out-of-lane paths, so the host permits them today. Denying access to paths the prompt still names would break a currently-working runner. The `Item-Dependencies` edge encodes this; do not reorder it for convenience.

UNIFORM SCOPE IS A MAINTAINER RULING, AND IT DOES NOT BREACH R1.3. E-04's two bounds apply to isolated AND non-isolated turns (spec R4.4a). That is a deliberate exception to the conservatism R1.3 asks for, and it is safe because the two are different KINDS of change: R1.3 protects the non-isolated turn's PROMPT TEXT, which must stay byte-identical because it is what an agent reads and reasons about, whereas these bounds are driver-side SUPERVISION that changes no instruction the agent ever sees. Measured context for the ruling: the coarse no-progress watchdog is ALREADY created unconditionally for every turn, so this is an incremental tightening rather than a new regime, and exactly ONE recorded run has ever used the non-isolated mode. V-04 requires proving the non-isolated PROMPT is still byte-identical, so the exception cannot quietly widen.

READ R4.1c BEFORE TOUCHING THE AGY DRIVER. Antigravity's `--dangerously-skip-permissions` default is a DECIDED CONSTRAINT, not a defect: running without it was proven in practice to fail or deadlock repeatedly, and its only alternative requires interactive permissions an unattended turn cannot answer. This plan MUST NOT flip that default. E-05 exists to PIN it, which is a regression guard running in the opposite direction from everything else here.

### Task group 1: host posture, honestly reported (R4.1, R4.1a, R4.2, R4.3)

- [x] E-01 IMPLEMENTS R4.1 (opencode case), R4.6. For an unattended isolated OpenCode turn, supply a runner-owned permission policy denying external-directory and interactive-question requests, injected through the child environment and NEVER by editing repository configuration. Extend the ONE existing child-env construction rather than forking a second one.
  - Depends on: none
  - Expected outcome: the child environment for an unattended isolated opencode turn carries the policy denying both request kinds, with inherited PATH and the runner's import pin still intact.
  - Execution state: performed
- [x] E-02 IMPLEMENTS R4.2. OBSERVE the policy that actually took effect and record it on the attempt, or record an explicit unverified marker with its reason. Host configuration precedence can place a managed source above the runner's, so a run that only SETS the policy can believe it is protected when it is not. Never let the observation failure abort the turn: an unobservable policy is recorded as unverified and the turn continues, because the driver-side bounds in E-04 hold regardless.
  - Depends on: E-01
  - Expected outcome: the attempt record carries either the observed effective policy values or an explicit unverified marker naming the reason, plus the host version measured against.
  - Execution state: performed
- [x] E-03 IMPLEMENTS R4.3, R4.1a, R4.1b. Do NOT blindly overwrite an operator-supplied value for the policy variable: the child env is built from a copy of the process environment, so an operator value would be silently discarded. Either merge it with validation or override it explicitly and loudly, and say which in the code comment. THEN record the per-host capability honestly: for a host with no denial posture, write that fact on the attempt and name the layers that DO apply (prompt purity from child `cqx5v7`, and the bounds from E-04). No artifact may describe such a host as denied.
  - Depends on: E-02
  - Expected outcome: an operator-supplied policy value is either verifiably merged or loudly overridden, never silently dropped; and for a host without a denial posture the attempt record states that plainly and names the layers that apply.
  - Execution state: performed

### Task group 2: driver-side bounds and the role selector (R4.4, R4.5, R4.1c)

- [x] E-04 IMPLEMENTS R4.4, R4.4a, R4.4b, R4.4c, R4.4d. Add the two driver-side bounds that do not trust the host, armed for EVERY unattended turn whether or not it is isolated. NAMES ARE NORMALIZED TO `TIMEOUT` (maintainer ruling): `PERMISSION_TIMEOUT` and `MAX_TURN_TIMEOUT`, never `..._DEADLINE`. Each constant's docstring MUST state the two facts the identifier cannot carry: WHAT INSTANT it measures from, and WHETHER ANYTHING RESETS IT. `PERMISSION_TIMEOUT` measures from an OBSERVED permission request and IS reset by progress; `MAX_TURN_TIMEOUT` measures from child-process start ONCE and is reset by NOTHING, which is its whole reason for existing beside the no-progress bound. `MAX_TURN_TIMEOUT` defaults to 4 HOURS. `PERMISSION_TIMEOUT` SHIPS AT `0` (DISABLED) unless you produce R4.4b's evidence that detection actually fires on a real ask; shipping it armed on an unproven detector is non-conforming because a false positive kills a healthy turn. Both accept `0` to disable, in-code; add NO config entry and NO CLI flag (R4.4c, KISS). State the antigravity overlap explicitly (R4.4d): that host already enforces 240m via `--print-timeout`, the same nominal 4 hours, so document which bound is expected to fire first rather than shipping two silent twins. Also state that the scope is ONE TURN, not one run. On expiry, terminate through the ONE shared reaper and record the safe-failure disposition naming WHICH bound fired.
  - Depends on: E-03
  - Expected outcome: the constants are named `PERMISSION_TIMEOUT` and `MAX_TURN_TIMEOUT`; `MAX_TURN_TIMEOUT` defaults to 4h and `PERMISSION_TIMEOUT` to `0` unless detection was proven; each docstring states its measured-from instant and its reset semantics; both are armed for isolated and non-isolated turns; no config entry or CLI flag was added; the antigravity overlap and the one-turn scope are documented in the code; and expiry is attributable to the shared reaper with the firing bound named.
  - Execution state: performed
- [x] E-05 IMPLEMENTS R4.1c. PIN Antigravity's permission default so this Set cannot regress it. Assert that the skip-permissions option still defaults to on and that the flag is still present on the constructed argv for an unattended turn. This is a guard in the OPPOSITE direction from every other item here: it FAILS if someone "hardens" the host into the interactive posture that was measured to deadlock. Verified at authoring that NO existing test pins this, so it closes a real hole.
  - Depends on: none
  - Expected outcome: a test fails if the skip-permissions default is flipped or the flag is dropped from an unattended turn's argv.
  - Execution state: performed
- [x] E-06 IMPLEMENTS R4.5, and WIRES the agy twin to the shared bounds. Ensure an isolated turn's child environment carries the execution-role selector that makes driver-owned lifecycle verbs refuse inside a lane, and state in the code comment that it is an environment selector and NOT a hardened boundary, since a same-user worker can unset it. Note the sanctioned asymmetry: the agy twin gets the bounds and the selector but NO policy document, because that host has no denial posture to request.
  - Depends on: E-04
  - Expected outcome: an in-lane invocation of a driver-owned lifecycle verb refuses with the documented code and performs NO state transition while the driver's own invocation still succeeds; the code comment carries the selector-not-boundary limit; and the agy twin has the bounds and selector with the missing policy document explained rather than silently absent.
  - Execution state: performed

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

The existing `runstop` suites MUST stay green, because E-04 touches the same termination path. RUN EXACTLY THIS, and paste its summary line (added 2026-09-01 after `/aw plan-review` PR-002 correctly objected that requiring `slow` coverage without giving the invocation left an executor to invent it):

```sh
python3 -m pytest -o addopts="" -q \
  tests/test_runner_stop.py tests/test_runner_stop_levels12.py \
  tests/test_runner_stop_level3.py tests/test_runner_stop_level4.py \
  tests/test_runner_stop_triggers.py tests/test_runner_shutdown.py
```

`-o addopts=""` CLEARS the configured defaults wholesale, which is the documented way to do it: the repository's test contract forbids fighting the configured flags one at a time, and the default `-m 'not slow'` would otherwise deselect the very tests this Set depends on. MEASURED at authoring, so you have a figure to compare against: `243 passed in 100.61s`. That is a NARROWED run and does NOT substitute for the two whole-suite invocations below.

BASELINES MUST BE MEASURED AT EXECUTION TIME, NOT COPIED FROM THIS PLAN. Corrected after `/aw plan-review` (PR-003 on every plan in this Set): the exact counts originally written here were already STALE before execution, because a co-worker's commit `8ced15ce` added two tests, moving the bare suite from `3996 passed` to `3998 passed`. A hardcoded count cannot distinguish an honest change from a regression, and treating it as an expectation would either raise a false alarm or, worse, mask a real failure behind an off-by-two rationalization.

SO DO THIS INSTEAD. Immediately before you start, run BOTH invocations and record their counts as YOUR baseline, pasting them. Then after your change, run both again and COMPARE FAILURES BY TEST IDENTITY, not by total: list the failing test node ids before and after and account for every difference by name. A count that changed with no new failing id is fine and must be explained (usually tests added); a new failing id is a STOP regardless of what the totals do.

TWO INVOCATIONS WITH DIFFERENT SEMANTICS, and the distinction is load-bearing: bare `python3 -m pytest` is expected to have ZERO failures, while `make test-all` carries a known set of PRE-EXISTING CLI-surface declaration failures that are not this plan's to fix. State the expected outcome separately per invocation; a single "failed == 0" claim across both is the contradiction that got the predecessor `tch3bo` flagged (PR-006). Identify the pre-existing set by NAME in your own measurement rather than trusting any number recorded here.

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
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-01, asked interactively rather than deferred: YES, MAKE IT UNIFORM. Both bounds now apply to isolated and non-isolated turns alike, and spec R4.4/R4.4a records the defaults as normative (permission 30s, absolute 4h). WHY IT DOES NOT BREACH R1.3, which is what made me hesitate: R1.3 protects the non-isolated turn's PROMPT TEXT, which must stay byte-identical because it is what an agent reads and reasons about, whereas these bounds are driver-side SUPERVISION that changes no instruction the agent ever sees. Measured context supplied to the maintainer for the decision: the coarse no-progress watchdog is ALREADY created unconditionally for every turn, so uniformity is an incremental tightening rather than a new regime; exactly ONE recorded run has ever used the non-isolated mode; and across 263 recorded turns the longest was 2.46 hours, which is how the 4-hour ceiling was set at roughly 1.6x the observed worst case. V-04 now requires proving the non-isolated prompt is still byte-identical, so the exception cannot quietly widen.

### OQ-03: May E-06 combine the role selector with all applicable Antigravity posture and deadline work?

- Blocking: no
- Status: resolved
- Owner: none
- Finding: PR-001
- Resolution or deferral rationale: RESOLVED 2026-09-01: NO, and the review was right that this was never a mechanical mirror. E-06 is now wiring only; the deadlines, the reporting, and the safe-failure recording must be HOST-NEUTRAL in the declared module `agent_workflows/lane_containment.py`; and the plan states explicitly that the agy policy-document step is INAPPLICABLE by design (that host has no denial posture, spec R4.1) rather than leaving its absence to be inferred.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01 (proves R4.1 opencode case; spec A8)
  - Required evidence: paste the decoded child environment for an unattended isolated opencode turn showing the policy denies BOTH external-directory and interactive-question requests, and showing inherited PATH and the runner's import-pin variable are still present. SABOTAGE REQUIRED: remove the policy injection, paste the FAILING assertion, restore, paste it passing plus `git status` proving the product is unmodified.
  - Observed evidence: DECODED CHILD ENVIRONMENT for an unattended isolated opencode turn (`OPENCODE_CONFIG_CONTENT`):
    `{"permission": {"external_directory": "deny", "question": "deny"}}` -- BOTH request classes denied.
    Inherited `PATH=/usr/bin:/bin:/usr/local/bin` intact; import pin intact
    (`AW_PIN_KEEP_ROOT` = the runner package root, and that root is first on `PYTHONPATH`); role selector
    `AW_EXECUTION_ROLE=worker`; `policy source = runner`.
    SABOTAGE PERFORMED, AND IT CAUGHT A REAL TEST DEFECT (this is the material finding of V-01). The first
    version of the central test asserted `run_opencode`'s SOURCE TEXT mentioned the policy helper. With the
    product sabotaged (the env assignment replaced by `pass`), that test STAYED GREEN: `31 passed`. It was
    proving a string existed, not that the policy reached the child. Replaced with
    `test_the_policy_actually_reaches_the_env_handed_to_the_child`, which captures the env actually handed to
    `Popen`. FAILING run on the still-sabotaged product:
    `AssertionError: the policy never reached the child environment` /
    `assert 'OPENCODE_CONFIG_CONTENT' in {...}` -> `1 failed, 31 passed`.
    RESTORED: `32 passed in 0.30s`. `git status` after restore shows only the intended change
    (`grep -c` for the injection line = 1; `git diff --stat agent_workflows/oc_runipd.py` = 154 insertions,
    2 deletions, i.e. this plan's own edit and nothing else). Recorded in the decisions register under
    "Note on a test defect this turn's sabotage caught".
    ALSO PROVEN: `test_a_non_isolated_turn_gets_no_denial_policy` shows the posture is isolation-scoped
    (R4.1) while the bounds are not (R4.4a); see DECISION 08-lhmrhx-D4.
  - Result: pass
- [x] V-02 validates E-02 (proves R4.2; spec A8)
  - Required evidence: paste the attempt record carrying EITHER the observed effective policy values OR an explicit unverified marker with its reason, and state the host version measured against. A run that records neither FAILS this item, because it would leave the run believing it is protected when a higher-precedence source may have overridden the request. Also paste evidence that a probe failure does NOT abort the turn.
  - Observed evidence: HOST VERSION MEASURED AGAINST: opencode `1.18.27`.
    REAL PROBE AGAINST THE LIVE HOST (`opencode debug config`, which prints the host's OWN resolved
    configuration after every precedence layer merges, run under the child's env):
    `{"result": "observed", "effective_policy": {"external_directory": "deny", "question": "deny"},
    "host_version": "1.18.27", "conforms_to_request": true}`. So on this host the request DID win, and that
    is now measured rather than assumed.
    ATTEMPT RECORD AS WRITTEN carries `posture: denied`, `requested_policy`, `policy_source: runner`,
    `policy_note`, and the nested `policy_observation` above; the event `host-permission-posture` is appended
    to `events.jsonl`.
    THE OVERRIDE CASE IS DETECTED, NOT ASSUMED AWAY, which is the whole point of R4.2: feeding a host config
    reporting `external_directory: ask` yields `conforms_to_request: false` plus the reason "the host's
    EFFECTIVE policy disagrees with the runner's request, so a higher-precedence configuration source
    overrode it".
    A PROBE FAILURE DOES NOT ABORT THE TURN (OQ-01): `observe_opencode_policy("no-such-binary-anywhere", ...)`
    RETURNED NORMALLY with `{"result": "unverified", "reason": "the policy probe could not run
    (FileNotFoundError: ...)"}`; no exception propagated. Every unobservable shape (unreadable, unparseable,
    non-object, no `permission` object) yields a marker WITH a reason, asserted by the parameterized
    `test_every_unobservable_shape_records_an_explicit_marker_with_a_reason` (4 cases, all pass). Recording
    NOTHING is what would fail this item, and no path does that.
  - Result: pass
- [x] V-03 validates E-03 (proves R4.3, R4.1a; spec A9, A8b)
  - Required evidence: paste two things. First: with an operator-supplied value ALREADY SET for the policy variable, show the resulting child environment either merges it verifiably or overrides it with an explicit loud record; a silent overwrite fails this item. Second: for a host with no denial posture, show the attempt record states that plainly, names the layers that DO apply, and that NO artifact or rendered summary claims denial. Assert the no-claim-of-denial part mechanically, not by reading.
  - Observed evidence: PART 1 (R4.3, operator value ALREADY SET). With
    `OPENCODE_CONFIG_CONTENT={"model":"operator/model","instructions":["op.md"],"permission":{"bash":"allow","external_directory":"allow"}}`
    exported before the child env was built (confirmed present in the child-env base, which is what makes the
    silent-discard risk real), the result is `disposition = merged-with-operator` and the resulting child env
    decodes to
    `{"instructions": ["op.md"], "model": "operator/model", "permission": {"bash": "allow",
    "external_directory": "deny", "question": "deny"}}`.
    So the merge is VERIFIABLE: every operator key survives (`model`, `instructions`, and the unrelated
    `permission.bash`), the runner's two required denials win, and the conflict is NAMED in the record:
    "operator value MERGED; every operator key preserved; the runner's required denials won on these operator
    keys (spec R4.1): external_directory". The original is preserved on the request
    (`request.operator_value == operator`). An unparseable or non-object value takes the LOUD OVERRIDE path
    instead, with the original preserved and the reason recorded. `test_no_disposition_is_silent` asserts the
    PROPERTY across six input shapes: no disposition is ever silent.
    SABOTAGE (silent overwrite, i.e. the R4.3 violation): forcing `operator_value = None` at the top of
    `build_permission_policy_env` produced `3 failed, 29 passed`, with
    `- merged-with-operator / + runner`. Restored: `32 passed`.
    PART 2 (R4.1a, a host with NO denial posture), ASSERTED MECHANICALLY over the serialized record rather
    than by reading it: `posture = "no-denial-posture"`, `posture != "denied"`, and NO `requested_policy` key
    (requesting one would itself be the parity claim R4.1a forbids). Four claim shapes are absent from the
    serialized blob (`"posture": "denied"`, `this host denies`, `denial posture is in effect`,
    `permission.external_directory=deny`). The record NAMES the layers that do apply: "R1 prompt purity: the
    emitted prompt names no path outside the lane" and "R4.4 driver-side bounds: MAX_TURN_TIMEOUT (and
    PERMISSION_TIMEOUT when armed) terminate the turn regardless of the host's permission decision".
    SABOTAGE (agy record made to claim denial): `1 failed, 31 passed` with
    `AssertionError: assert 'denied' == 'no-denial-posture'`. Restored: `32 passed`.
    `test_no_driver_reimplements_the_posture_wording` additionally proves neither driver hardcodes the tier,
    so a call site cannot drift into claiming denial.
  - Result: pass
- [x] V-04 validates E-04 (proves R4.4, R4.4a; spec A10, A10b)
  - Required evidence: paste the DEFAULTS in force, showing the permission deadline is 30s and the absolute deadline is 4h and that both are overridable per run; paste evidence BOTH bounds are armed for a NON-isolated turn as well as an isolated one; and paste a digest comparison proving the non-isolated turn's PROMPT is still byte-identical, which is what makes the uniform supervision scope safe under R1.3. Then paste a test in which a synthetic UNANSWERED permission request, including the nested child-session shape, causes termination within the permission deadline and demonstrably NOT at the coarse no-progress bound; show the recorded disposition and the name of the bound that fired. Then prove no second reaper was introduced using AST or the import graph over the package, NOT a text grep, since the test file itself contains the symbols. Finally paste the six `runstop` suites with `slow` INCLUDED, green, since this item edits the shared termination path.
  - Observed evidence: DEFAULTS IN FORCE, pasted: `PERMISSION_TIMEOUT = 0.0` seconds (DISABLED) and
    `MAX_TURN_TIMEOUT = 14400.0` seconds = 4.0 hours.
    ON THE "30s" IN THIS ITEM'S OWN REQUIRED-EVIDENCE TEXT: it is SUPERSEDED WITHIN THIS SAME PLAN by E-04,
    spec R4.4b, and criterion A10c, all of which require the permission bound to SHIP AT `0` unless detection
    is proven against a real ask. Detection is NOT proven (see below), so `0` is the CONFORMING value and 30
    would be the non-conforming one. Recorded as DECISION 08-lhmrhx-D1 with the full reasoning; DECISION
    08-lhmrhx-D2 records why A10c option (ii) was taken rather than option (i).
    R4.4b EVIDENCE FOR LEAVING IT OFF: the installed host (1.18.27) exposes no flag that forces a permission
    ask; the spec's own measurement is that the last real run's stdout carried ZERO permission-typed events;
    and the qyaime evidence motivating a plain-text pattern came from opencode's LOG FILE, not stdout, which
    is why `stall_progress.py` exists as a separate log-tailing module. So the detector may match a shape that
    never reaches the stream it inspects, and arming it would risk killing healthy turns.
    `test_no_stdout_detector_was_shipped_armed` proves no product code arms it, and
    `test_the_artifact_states_max_turn_is_the_only_covering_bound` proves the CONSEQUENCE is written down:
    `MAX_TURN_TIMEOUT` is currently the ONLY bound covering a permission deadlock.
    BOTH OVERRIDABLE / DISABLE-ABLE IN-CODE: `enabled` is `False` with both at `0`, `True` with either armed.
    BOTH ARMED FOR A NON-ISOLATED TURN AS WELL AS AN ISOLATED ONE, proven STRUCTURALLY rather than by reading:
    `test_the_bounds_are_constructed_outside_any_isolation_branch` parses each driver's launcher with the AST,
    finds exactly ONE `TurnBoundWatch` construction, and proves it is not nested under a `work_dir`/`isolate`
    conditional. Both drivers pass.
    NON-ISOLATED PROMPT IS BYTE-IDENTICAL (the R1.3 property that makes uniform supervision safe), compared
    against pre-change `HEAD dd35a200` extracted to a separate tree:
      PRE  oc_runipd  sha256=05995d541b9c8168b8669a999b12687afe92d94efaeda9a4c2235f4db169d789 bytes=5503
      POST oc_runipd  sha256=05995d541b9c8168b8669a999b12687afe92d94efaeda9a4c2235f4db169d789 bytes=5503
      PRE  agy_runipd sha256=59c7eac2f51792306dcd003d1c7529b82faebb4e5308845fa7c9c828231e76f7 bytes=5099
      POST agy_runipd sha256=59c7eac2f51792306dcd003d1c7529b82faebb4e5308845fa7c9c828231e76f7 bytes=5099
    Identical on both drivers, so the uniform scope changed no instruction any agent reads.
    UNANSWERED PERMISSION REQUEST TERMINATES WITHIN THE PERMISSION BOUND, DEMONSTRABLY NOT AT THE COARSE
    NO-PROGRESS BOUND: `test_permission_expiry_fires_within_its_own_bound_not_the_stall_bound` sets the stall
    bound 20x longer and asserts the kill lands inside the short window; the NESTED CHILD-SESSION shape is
    covered by `test_the_nested_child_session_shape_is_bounded_too`. The recorded disposition is
    `failed-safely` and the firing bound is NAMED (`permission-timeout` vs `max-turn-timeout`), so a
    post-mortem can tell a permission deadlock from an over-long turn from a silent stall.
    `test_progress_disarms_the_permission_bound_but_never_the_max_turn_bound` proves the reset asymmetry that
    is the whole design: progress disarms the permission bound, and a turn calling `note_progress()` in a
    tight loop STILL dies at `MAX_TURN_TIMEOUT`.
    NO SECOND REAPER, checked with the AST over the package rather than a text grep (a grep is satisfied by
    the checking file itself): `test_no_second_reaper_exists_anywhere_in_the_package` passes, and it was
    NARROWED during execution after a first version produced four FALSE POSITIVES on shipped code -- three
    `os.kill(pid, 0)` LIVENESS PROBES (`ipd_lifecycle`, `layout_migration`, `worktree_lease`, which send no
    signal) and one pre-existing spawn-failure cleanup in `agy_run.py`. The narrowed rule is stated in the
    test docstring. `test_the_bound_watch_is_defined_exactly_once_in_the_package` proves `TurnBoundWatch` has
    exactly ONE definition and that it lives in `lane_containment.py`.
    THE SIX `runstop` SUITES WITH `slow` INCLUDED, since this item edits the shared termination path:
    `python3 -m pytest -o addopts="" -q tests/test_runner_stop.py tests/test_runner_stop_levels12.py
    tests/test_runner_stop_level3.py tests/test_runner_stop_level4.py tests/test_runner_stop_triggers.py
    tests/test_runner_shutdown.py` -> `1 failed, 242 passed in 96.72s (0:01:36)`. The ONE failure is
    `test_runner_stop_triggers.py::PreExistingInterruptContractTests::test_the_terminal_rung_still_records_the_item_interrupted`,
    which was MEASURED FAILING AT BASELINE before any edit (same test, same `- running / + interrupted`
    assertion), so it is pre-existing and not this plan's. Note the plan's authoring-time figure was
    `243 passed`; the difference is that one pre-existing failure, not a regression.
    ONE REAL REGRESSION WAS FOUND AND FIXED DURING THIS ITEM, disclosed rather than quietly repaired:
    `test_runner_stop.py::PollWiringTests::test_in_turn_poll_sits_with_the_watchdog_touch` measures the
    CHARACTER DISTANCE between `watchdog.touch()` and the in-turn `poll_stop`, and my four-line explanatory
    comment pushed the poll outside its 1200-char window. Since `tests/test_runner_stop.py` is outside this
    plan's `Scope-Paths`, I shortened MY OWN comment in both drivers rather than widening someone else's
    test. `PollWiringTests` -> `5 passed`.
  - Result: pass
- [x] V-05 validates E-05 (proves R4.1c; spec A8c)
  - Required evidence: paste the test asserting the agy skip-permissions option still defaults to on AND that the flag is present on the constructed argv for an unattended turn. SABOTAGE REQUIRED, in the opposite direction from every other sabotage here: flip the default to off, paste the FAILING test proving the guard catches a hardening regression, restore, paste it passing. State in writing that this plan did NOT change that default.
  - Observed evidence: THE GUARD PASSING: `TestAntigravitySkipPermissionsDefaultIsPinned` -> `4 passed in
    0.18s`. It asserts (a) the parser's `dangerously_skip_permissions` still defaults to `True`, (b) an
    options dict MISSING the key still defaults on, (c) `argv.append("--dangerously-skip-permissions")` is
    present in `run_agy_turn` and its guard reads `options.get("dangerously_skip_permissions", True)`, and
    (d) `DEFAULT_TIMEOUT == "240m"` as it shipped.
    SABOTAGE PERFORMED IN THE OPPOSITE DIRECTION FROM EVERY OTHER SABOTAGE HERE, i.e. simulating a
    "hardening" regression into the interactive posture that was measured to deadlock. TWO independent
    sabotages, because there are two independent ways to regress it:
    (A) parser default flipped to `False` -> `1 failed, 3 passed`:
    `AssertionError: the skip-permissions default was flipped; R4.1c forbids that without its own decision,
    its own evidence the deadlock is gone, and an explicit supersession` / `assert False is True`.
    (B) the argv guard's fallback flipped to `False` -> `1 failed, 3 passed`:
    `AssertionError: the argv guard must default to True, or an options dict missing the key would silently
    launch the interactive posture that deadlocks`.
    Both restored; `4 passed`.
    IN WRITING, AS THIS ITEM REQUIRES: THIS PLAN DID NOT CHANGE THAT DEFAULT. `git diff
    agent_workflows/agy_runipd.py | grep -E "^[-+].*dangerously"` returns only two ADDED COMMENT lines
    explaining why the default must stay; no behavior line touching `dangerously_skip_permissions` is added,
    removed, or altered. Verified at authoring that NO existing test pinned this, so the guard closes a real
    hole.
  - Result: pass
- [x] V-06 validates E-06 (proves R4.5 and twin parity; spec A11, CID-3)
  - Required evidence: paste evidence that an in-lane invocation of a driver-owned lifecycle verb REFUSES with the documented code and performs NO state transition (show the absence of the transition, not just the refusal message), while the driver's own invocation still succeeds. Quote the code comment carrying the selector-not-a-boundary limit. Then paste the parameterized run proving both drivers satisfy the applicable assertions, and state explicitly which assertion does NOT apply to the agy twin and why (no denial posture exists). Finally paste both whole-suite invocations with expected counts stated separately per invocation.
  - Observed evidence: IN-LANE REFUSAL WITH NO STATE TRANSITION, demonstrated end to end on a throwaway repo
    (full transcript in the execution report). With `AW_EXECUTION_ROLE=worker`, `aw ipd begin tttttt` printed
    the documented code and exited 2:
    `AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes; a worker-role process must not
    run them (refused: aw ipd begin). ...` / `exit=2`.
    THE ABSENCE OF THE TRANSITION IS SHOWN, not just the refusal message: the plan file's sha256 is BYTE
    IDENTICAL before and after (`7580a19f57390d85a8691a46e1d48ae30e2f626c6c1cd203469840df955d44b3` both
    times), the plan is still in `pending/`, and `receipts written = 0`.
    THE DRIVER'S OWN INVOCATION STILL HAS AUTHORITY: with the selector unset, the same command reaches the
    NORMAL lint gate instead of the role refusal (it reports `IPD-BEGIN IPD-H202 required H2 missing: ...`
    for my deliberately-minimal stub plan), which proves the refusal is keyed on the SELECTOR and not on
    being in a worktree at all. `test_the_drivers_own_invocation_still_succeeds` pins the predicate:
    `worker_role_active({"AW_EXECUTION_ROLE": "worker"}) is True`, `({}) is False`, `("") is False`.
    THE SELECTOR-NOT-A-BOUNDARY LIMIT, QUOTED from `agent_workflows/oc_runipd.py:5107`:
    "HONEST LIMIT: this is an environment SELECTOR, not a hardened boundary. A same-user worker with shell
    access can unset it. It stops an agent that is FOLLOWING the contract (the actual i452hf case), not a
    determined one; hard enforcement is an OS sandbox / separate principal."
    And this plan's own, from `lane_containment.TurnBoundWatch`: "HONEST LIMIT: this bounds the turn, it does
    not contain the worker. A terminated child may already have written outside its lane. Containment is R1
    (the prompt names nothing outside the lane) plus, on a host that has one, the R4.1 denial."
    PARAMETERIZED TWIN RUN: the full two new modules are `72 passed` with every `[oc_runipd]`/`[agy_runipd]`
    pair green (per-test PASSED list captured in the execution report).
    WHICH ASSERTION DOES NOT APPLY TO THE AGY TWIN, AND WHY: the R4.1 DENIAL POSTURE and its R4.2 OBSERVATION.
    That host has NO denial posture, permanently and by design (R4.1, R4.1c: auto-approve is the required
    setting because the only alternative needs interactive permissions an unattended turn cannot answer, and
    was measured to deadlock), so there is no policy to request and nothing to observe. Its absence is
    asserted POSITIVELY rather than left to be inferred:
    `test_the_agy_driver_records_the_posture_for_an_isolated_turn` requires that `run_agy_turn` does NOT call
    `build_permission_policy_env`, and the agy call site passes no `observation` argument with a comment
    saying the omission is meaningful. Everything else (the role selector, both bounds, the honest reporting,
    the safe-failure recording) DOES apply to both and is shared, not mirrored.
    BOTH WHOLE-SUITE INVOCATIONS, WITH EXPECTED OUTCOMES STATED SEPARATELY PER INVOCATION as this plan
    requires, and compared BY TEST IDENTITY against baselines measured immediately before the change rather
    than against any number written at authoring time:
      (1) BARE `python3 -m pytest`. Baseline `31 failed, 4786 passed`; after `31 failed, 4858 passed`.
          Newly FAILING: NONE (empty `comm -13`). Newly passing: none. Passed count +72 = exactly the tests
          this plan adds. EXPECTED OUTCOME FOR THIS INVOCATION: the plan says bare is "expected to have ZERO
          failures". IT DOES NOT HERE, AND THE 31 ARE ENVIRONMENTAL, NOT DEFECTS: this turn runs inside a
          managed lane whose own environment carries `AW_EXECUTION_ROLE=worker`, which is exactly the marking
          E-06 exists to make lifecycle verbs refuse. Re-running with only that variable unset gives
          `14 failed, 4875 passed`, so 17 of the 31 are the driver's own worker marking refusing nested
          lifecycle calls inside tests. The remaining 14 are all `tests/test_run_viewer.py`, which requires
          pre-existing run directories that a freshly created lane does not have. Both sets were measured
          FAILING AT BASELINE before I edited anything (`baseline_bare.txt` = 31 ids,
          `baseline_bare_norole.txt` = 14 ids), and both diffs are empty after.
      (2) `make test-all`. Baseline `34 failed, 5192 passed`; after `34 failed, 5264 passed`. Newly FAILING:
          NONE. EXPECTED OUTCOME FOR THIS INVOCATION: a KNOWN pre-existing failure set that is not this
          plan's to fix, which is what is observed. Named rather than counted, the three additional ids
          beyond the bare set are
          `test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw`,
          `test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory`,
          and `test_runner_stop_triggers.py::PreExistingInterruptContractTests::test_the_terminal_rung_still_records_the_item_interrupted`.
    A10e's CLI-surface check: `tests/test_command_surface_declarations.py` -> `14 passed in 10.08s`, so no
    worse than baseline; no config entry and no CLI flag was added for either bound
    (`TestNoNewConfigurationSurface`, 4 tests).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 6 E-leaves in 2 task groups, under both thresholds. The two groups are one concern viewed from two sides: what we ASK the host for, and what we enforce ourselves when the host cannot or will not. They belong together because the honest per-host reporting in E-03 is only meaningful if the fallback layer in E-04 exists, and E-05 pins the constraint that makes the asymmetry permanent.

Execution contract: this plan INHERITS the shared execution contract from orchestrator `h0zljh` verbatim, including its ten numbered rules. Restated here because these are the ones most likely to be skipped, and skipping them is how this work gets faked:

1. PROSE IS NEVER EVIDENCE. Paste real command output and exit codes, never a summary of them. A `V-*` whose command was not run stays `Result: pending`.
2. SABOTAGE the central assertions. Break the product behavior deliberately, paste the FAILING run, restore, paste the passing run plus `git status` proving the product is unmodified. This session already produced a test that passed while the product was broken; only sabotage exposed it.
3. ASSERT THE PROPERTY, NOT THE WORDING. Where the requirement states an absence, check the emitted output so a reworded violation still fails.
4. STRUCTURE, NOT GREP, for "only one of these exists". Use AST or the import graph, repo-wide; a text grep is satisfied by the checking code itself.
5. PREREQUISITE IS CHECKED, NOT ASSUMED: child `cqx5v7` (Order 01) MUST be in `executed/` before this plan starts, and this is a SPEC-NORMATIVE ordering (R4.6), not a convenience: the host currently permits the out-of-lane writes, so denying them while the prompt still names them would break a working runner. Verify the lane-relative prompt symbols exist. If they are absent, STOP and report.
6. THE SCOPE FENCE IS A DECLARATION, NOT A HALT CONDITION. Touch only the declared `Scope-Paths` as a default, and never expand casually; if the work genuinely requires more, MAKE THE EDIT AND JUSTIFY IT in the finalize reconciliation (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path), which is where an unjustified widening is caught. Do NOT halt the run over a scope question. If the work genuinely requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` will refuse to complete until every out-of-scope path you touched carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT at the gate rather than prevented by halting a run. Do NOT halt the run over a scope question. What you must NOT do is REIMPLEMENT a sibling's rule, which would fork it (CID-2): that is a correctness problem, not a scope one, so if a needed rule is missing, say so in the reconciliation reason.
7. STATE THE HONEST LIMIT. Where a mechanism is an accident guard rather than a boundary, say so in the code comment and in this plan. Overstating a guarantee is the failure.

Commits are path-scoped and never pushed. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed or hook-interrupted commit.

Post-gate lifecycle: run `aw ipd lint --phase pre-transition`, then `aw ipd finalize`, never a hand edit. If validation did not pass, record `substantially-complete` honestly rather than marking this executed.
