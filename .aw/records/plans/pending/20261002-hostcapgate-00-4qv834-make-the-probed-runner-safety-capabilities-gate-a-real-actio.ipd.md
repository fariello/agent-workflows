# IPD: Make the probed runner-safety capabilities gate a real action, or record honestly that they cannot

- Date: 2026-10-02
- Kind: orchestrator
- Concern: A STRICT PROBE PRODUCES A CORRECT VERDICT AND NOTHING ASKS FOR IT. `host_sandbox_profile` defines `CAP_FRESH_VERIFIER_SESSION` and probes it by attempt, with a docstring stating the probe "requires BOTH that distinct identities finalize AND that a reused identity is REFUSED, because a contract that never refuses enforces no separation while a caller believes verification was independent". Measured in this lane at HEAD `6310b3e4`: `ACTION_CAPABILITY_REQUIREMENTS` contains exactly ONE row, `ACTION_READ_ONLY`, whose `required` tuple is EMPTY. So the probe's own stated failure mode is the current state of the action preflight.
  THE GAP HAS TWO HALVES AND THE BACKLOG ITEM NAMES ONE. The item blames the requirement table. `runner_shared.RUNNER_ACTION_TO_CONTRACT_ACTION` is ALSO `{}`, and `runner_action_contract_class` returns `None` for all three runner actions (`execute`, `review`, `plan`), measured in-process. Its comment says so: "This mapping is deliberately empty of production rows: it serves as the extension seam that successor plans ... will populate when a mutating action acquires a real capability requirement." A change that filled only the requirement table would gate nothing, because the runner never asks about `execute` at all. Both halves are in one child, deliberately, so neither can ship alone.
  THE ITEM'S STATED BLOCKER IS CLEAR, AND MEASURING IT CHANGED THIS SET'S SHAPE. The item says the work includes establishing "that hosts in real use actually pass the probe, or the row turns a working configuration into a refused one". Measured: `_probe_fresh_verifier_session()` returns `True` with the note "a distinct-identity run finalized and a reused-identity run was REFUSED", and `detect_host_capabilities` reports `supports_fresh_verifier_session=True` for `opencode`, `antigravity` AND `scripted`. The probe is in-process and platform-independent (it drives `agy_verifier.run_fresh_verifier`, touching no kernel feature and no host binary; 3.7ms average over five runs), so it is not the Linux-only hazard the sandbox rungs are. The item's blocker is therefore cleared rather than inherited, which is why this Set builds the gate instead of merely investigating whether one is possible.
  WHAT I FOUND INSTEAD, WHICH THE ITEM DOES NOT MENTION, IS WHY THIS SET HAS TWO CHILDREN. Activating the gate makes a per-item capability probe EXECUTE on the dispatch path, and that probe mutates process-global state. `host_sandbox_profile._capture_turn_argv` assigns `subprocess.Popen = fake_popen` to intercept each host's turn builder, and `fake_popen` raises `RuntimeError("stop-before-launch")` for any argv outside `("git", sys.executable, "bwrap")`. Measured by experiment: one `detect_host_capabilities` call left `subprocess.Popen` substituted for 271 of 633 samples taken by a watching thread, and a worker thread issuing ordinary `subprocess.run(["true"])` calls during six such calls got 238 failures against 62 successes. A run process is multi-threaded (`render_stream`'s stream pump, the stall watchdog, the telemetry sampler) and `run_analytics_telemetry.ResourceProbes._run_bounded` itself calls `subprocess.run`. So the policy change would ship a concurrency hazard as a side effect.
- Scope: Close the gap in the order that makes it safe. Order 01 removes the per-item probe from the dispatch path by freezing ONE descriptor per run at initialization, and makes the probe's `subprocess.Popen` interception stop refusing a launch it did not initiate. Order 02 then fills BOTH empty halves: a new action class for a mutating execute requiring `supports_fresh_verifier_session`, and the runner mapping that makes `execute` reach it, with the refusal proven reachable on an incapable descriptor and inert on a capable one.
  THE ORDERING IS A SAFETY PROPERTY, NOT A PREFERENCE, and it is the main thing this orchestrator exists to enforce. Order 02 declares `- Item-Dependencies: executed:bqtgmo` for the measured reason above: its mapping row is what makes the already-wired per-item probe begin executing, so landing it first would put the `subprocess.Popen` hazard into every live run.
  EXCLUDES, AND THIS FENCE IS LOAD-BEARING. (1) NO REQUIREMENT ON `supports_commit_gateway`. It is DECLARED AND NEVER PROBED with a False default by deliberate decision, so requiring it would refuse EVERY execute item on EVERY host; its spec-side overclaim is separately owned. (2) NO REINSTATEMENT of the `ACTION_REVIEW`/`ACTION_MUTATE`/`ACTION_CONTRACTLESS_PROMPT` constants that `01reg8` deleted on maintainer ruling `4h7tt0` OQ-02. One new class WITH a consumer is not a restoration of three classes without one, and no child may be read as reversing that ruling. (3) NO NEW PROBE. Every capability this Set consumes is already probed or already declared. (4) NO SPEC AMENDMENT: spec `25kzda` 5.2 already requires a "fresh verifier" for a mutating action and already specifies the exact per-item fail-closed refusal, and `01reg8` OQ-03 deliberately left that action table un-narrowed so a future requirement would have somewhere to land. No `.spec.md` appears in any child's `- Scope-Paths:`. (5) NO CROSS-RUN DESCRIPTOR CACHE with TTL or expiry; that is `host_capability_registry`'s separate concern.
- Scope-Paths: .aw/records/plans/pending/20261002-hostcapgate-00-4qv834-make-the-probed-runner-safety-capabilities-gate-a-real-actio.ipd.md
- Item-Dependencies: none
- Status: to-review
- Coverage: fail
- Coverage-Fingerprint: 5f4117b908d1e2168db7007615002b600a656028c91284f7e40e512e64028ff4
- Coverage-Checked: 2026-10-06 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: chore
- Priority: medium
- From-Backlog: s8veyk
- Set: hostcapgate
- Order: 0
- Highest E allocated: 02
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 4qv834

## Workflow history

- 2026-10-06 coverage fail (aw oc run): fingerprint 5f4117b908d1, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `s8veyk` in lane worktree `s8veyk` at HEAD `6310b3e4`. The item's central claim HELD on re-measurement (one requirement row, empty `required`, verdict gates nothing). FOUR MEASUREMENTS SHAPED THIS SET, and two of them contradict or extend the item.
  FIRST, THE ITEM'S STATED BLOCKER IS ALREADY CLEARED. It says the work includes establishing that hosts in real use pass the probe. They do, on every host reported (`opencode`, `antigravity`, `scripted`), with a probe that is in-process and platform-independent rather than kernel-gated. So this Set is not an investigation; it is a build with one measured refusal case (a descriptor requested for a platform the interpreter is not running on, which `detect_host_capabilities` gates behind `plat == running_platform`).
  SECOND, THE ITEM NAMES ONE EMPTY TABLE AND THERE ARE TWO. `RUNNER_ACTION_TO_CONTRACT_ACTION` is also `{}`. A plan that fixed only `ACTION_CAPABILITY_REQUIREMENTS` would ship a verifiably useless change, so Order 02 owns both halves and its V-items prove the mapping separately from the row.
  THIRD, AND THIS IS WHY THERE ARE TWO CHILDREN RATHER THAN ONE: the path the gate activates is hazardous. I measured `detect_host_capabilities` substituting `subprocess.Popen` process-wide (271 of 633 samples) and breaking a concurrent thread's launches (238 `RuntimeError: stop-before-launch` against 62 successes) in a process that runs daemon threads which themselves launch subprocesses. Folding that fix into the policy change would have asked a reviewer to judge a correctness repair and a behavior change in one pass, and the behavior change is the one needing the maintainer's attention.
  FOURTH, THE ACTION-CLASS QUESTION WAS ALREADY DECIDED AND I DID NOT REOPEN IT. `iot7hc`'s review recorded PR-102 (HIGH): mapping `execute -> read_only` is forbidden because `read_only`'s own `spec_basis` says "no agent session for a skip", and because `format_host_capability_finding` interpolates the action name verbatim into the spec's byte-exact operator message. I verified the second by rendering the message and seeing "action execute" appear. Order 02 therefore adds a new class, stated as settled in its Scope rather than left to its executor.
  ONE CHILD CARRIES A BLOCKING OPEN QUESTION BY DESIGN. Order 02's OQ-01 is `Blocking: yes`: a shipped test pins the requirement table to exactly one row and one action class, and that file is not in its `- Scope-Paths:`, so the executor would have to touch an undeclared path. `aw ipd lint` will refuse it with `IPD-Q501` until the maintainer answers, which is the correct fail-closed state and costs one line to clear. Order 01 has no blocking question and can be approved independently.
  NO SPEC AMENDED, and no `.spec.md` is in any child's `- Scope-Paths:`.

## Goal

Make the strictly-probed fresh-verifier capability actually decide whether an execute item runs, after first removing the per-item probe and the process-global launch interception that would otherwise make that gate a concurrency hazard.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: orchestration of the hostcapgate Set

- [ ] E-01 CONFIRM bqtgmo REACHED executed
  - Depends on: none
  Confirm child 01 (`bqtgmo`, freeze one host capability descriptor per run and stop re-probing on the dispatch path) is `executed` with its own validation evidence present, and confirm the cross-child properties before Order 02 runs: both children carry `- From-Backlog: s8veyk`, neither declares a `- Blocks-Release:` gate (the source item carries none, and `chore` is not in the release-gating work-kind set), and their `- Scope-Paths:` overlap only on files each child edits in disjoint regions, which must be stated rather than assumed.
  - Expected outcome: child 01 is `executed` with V-01..V-05 carrying pasted evidence; the two child rows below resolve to real files on disk; the three cross-child properties are checked and reported, including an explicit statement of which files both children touch and why that is safe given child 01 executes first; no product file is touched by this item.
  - Execution state: pending

- [ ] E-02 CONFIRM y9m1ya REACHED executed
  - Depends on: E-01
  Confirm child 02 (`y9m1ya`, require the probed fresh-verifier capability for the execute action) is `executed`, and confirm the Set-wide no-regression property after both children land: the gate refuses nothing on a host whose probe passes, so a capable host's queue behaves exactly as it did before the Set, proven by a before/after comparison rather than asserted.
  - Expected outcome: child 02 is `executed` with its blocking OQ-01 answered and V-01..V-05 carrying pasted evidence; `runner_action_contract_class("execute")` returns the new class while `("review")` and `("plan")` still return `None`; and an execute item on a capable descriptor is shown to dispatch unchanged, so the Set added a refusal path without refusing any measured host.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `bqtgmo` | `20261002-hostcapgate-01-bqtgmo-freeze-one-host-capability-descriptor-per-run-and-stop-re-pr.ipd.md` | Measures the host capability descriptor ONCE at run initialization, freezes a JSON-safe snapshot into durable run state, reads it on the dispatch path instead of probing per item, and makes the probe's `subprocess.Popen` interception delegate rather than refuse a launch it did not initiate. Adds NO requirement and refuses nothing. | none |
| 02 | `y9m1ya` | `20261002-hostcapgate-02-y9m1ya-require-the-probed-fresh-verifier-capability-for-the-execute.ipd.md` | Adds an action class for a mutating execute requiring `supports_fresh_verifier_session`, maps the runner's `execute` onto it, retracts the two comments asserting no shipped requirement exercises this reason, and proves the refusal is reachable on an incapable descriptor, inert on a capable one, correctly worded, and cascading without aborting. | `executed:bqtgmo` |

## Completion criteria (the whole Set is done only when)

1. BOTH children are `executed` and filed under `.aw/records/plans/executed/`, each with every `V-*` carrying concrete pasted evidence rather than an assertion: `bqtgmo` with V-01..V-05, `y9m1ya` with V-01..V-06.
2. THE PER-ITEM PROBE IS GONE FROM THE DISPATCH PATH. Dispatching several items in one run performs zero capability probes after initialization, demonstrated by a counted observation at a seam rather than by reading code, and a run's durable state carries exactly one descriptor snapshot with its host and observed-at timestamp.
3. THE LAUNCH INTERCEPTION NO LONGER REFUSES A LAUNCH IT DID NOT INITIATE. A concurrent thread issuing ordinary `subprocess.run`/`Popen` calls throughout a `detect_host_capabilities` call completes every one, measured against the pre-change transcript that recorded 238 refusals.
4. BOTH EMPTY HALVES ARE FILLED AND BOTH ARE PROVEN. `ACTION_CLASSES` carries a mutating-execute class whose `required` is exactly `('supports_fresh_verifier_session',)`, AND `runner_action_contract_class("execute")` returns it while `("review")` and `("plan")` still return `None`.
5. THE REFUSAL IS PROVEN REACHABLE AND PROVEN INERT. An execute item on a descriptor whose probe verdict is False is refused with no session started, its dependents cascaded and the run NOT aborted; an execute item on a capable descriptor dispatches byte-identically to before the Set. Reachability is shown to BITE by removing the mapping row and observing the test fail.
6. NOTHING CLAIMS MORE THAN WAS BUILT. No comment, docstring or message asserts that the runner enforces a mutation boundary: `rg -n "not yet exercised by any shipped requirement" agent_workflows/` returns nothing, and each replacement states both the new requirement AND that one capability of eight is required with the rest recorded `unrepresented` or deliberately excluded.
7. NO FENCE WAS CROSSED. `supports_commit_gateway` is required by no action; the three constants `01reg8` deleted are not reinstated; no probe was added or altered; no `.spec.md` was modified; and the suite is at or above each lane's re-measured baseline with every pre-existing failure accounted for individually.

## Cross-IPD validation

- ORDERING ACTUALLY HELD, not merely declared. Confirm from the children's own records that `bqtgmo` reached `executed` BEFORE `y9m1ya` executed, since the whole safety argument for this Set is that the policy change lands after the per-item probe is removed. A runner enforces this through `- Item-Dependencies: executed:bqtgmo`, but a hand-executed Set has no such enforcement, so the record is what proves it.
- THE TWO CHILDREN SHARE TWO FILES AND MUST NOT HAVE FOUGHT OVER THEM. Both declare `agent_workflows/host_sandbox_profile.py` and `agent_workflows/runner_shared.py`. Confirm the regions are disjoint: `bqtgmo` touches `_capture_turn_argv`'s interception plus the descriptor freeze and its dispatch read, while `y9m1ya` touches the action-class constant, `ACTION_CLASSES`, the requirement row, and the runner mapping with its comment. Report any overlap found rather than assuming the declaration prevented one.
- THE SECOND CHILD DID NOT REINTRODUCE WHAT THE FIRST REMOVED. After both land, confirm the dispatch path still performs no per-item probe, since `y9m1ya` edits the same function's neighborhood and a careless rehydration-to-probe reversion would silently restore the hazard while every one of its own tests still passed.
- THE SHIPPED CAPABILITY TESTS PASS AS A WHOLE, not just the two new modules. `tests/test_host_capability_extension.py` is edited by `y9m1ya` E-06 and guards the fail-OPEN omissions this Set could commit; run that module in full and confirm its four properties are intact rather than loosened.
- THE ADJACENT PRE-EXISTING FAILURE IS EXPLAINED ONCE, FOR THE SET. `test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation` fails at the Set's base commit AND perturbs the `RUN-HOST-CAPABILITY` row this Set changes the requirements behind. Both children must re-measure it; this item confirms the two explanations agree and that neither child's change altered its outcome.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- FAIL CLOSED, AND NEVER INFER A CAPABILITY FROM PRESENCE. `host_sandbox_profile`'s docstring records a measured counterexample where every inspectable signal said "sandbox available" on a host that could not enforce it, and concludes "Inspection MEASURABLY LIES".
- AN UNLISTED REQUIREMENT CAN NEVER FAIL, which is why `ActionRequirement.unrepresented` exists: "Omitting it would make the action PASS because the requirement was never listed, which is fail-OPEN."
- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN. Both E-items here confirm a child reached `executed` and check a cross-child property; neither produces a deliverable, establishes a baseline, or reconciles records, because the runner retires an orchestrator while SKIPPING the pre-transition E/V checkpoint, so work parked here would be marked complete having never been performed.
- RUN THE SUITE BARE as `python3 -m pytest`; `addopts` already supplies `-q -n auto --dist=worksteal` and the marker deselection.

## Findings

| Id | Finding | Evidence | Consequence for this Set |
|---|---|---|---|
| F-01 | The requirement table requires nothing | `ACTION_CLASSES == ('read_only',)`; `ACTION_CAPABILITY_REQUIREMENTS['read_only'].required == ()`, measured in-process | Order 02's first half |
| F-02 | The runner's action mapping is ALSO empty | `RUNNER_ACTION_TO_CONTRACT_ACTION == {}`; all three runner actions map to `None` | Order 02's second half; a one-half change would gate nothing |
| F-03 | The fresh-verifier probe PASSES on every reported host | `_probe_fresh_verifier_session()` -> `True` with note "a distinct-identity run finalized and a reused-identity run was REFUSED"; True for `opencode`, `antigravity`, `scripted` | The backlog item's stated blocker is CLEARED; the Set builds rather than investigates |
| F-04 | The probe is platform-independent and cheap | Drives `agy_verifier.run_fresh_verifier` in-process against a `verify_roles` packet; 3.7ms average over five runs | Requiring it is not a macOS/Windows outage the way a Landlock-gated requirement would be |
| F-05 | The descriptor call substitutes `subprocess.Popen` process-wide | A sampling thread saw a non-real `Popen` in 271 of 633 samples during one `detect_host_capabilities` call | Order 01 exists and must precede Order 02 |
| F-06 | A concurrent caller's launch is REFUSED, not merely intercepted | A worker thread got 238 `RuntimeError: stop-before-launch` and 62 successes during six concurrent calls; `fake_popen` raises for any `cmd[0]` outside `("git", sys.executable, "bwrap")` | The ordering is a safety property, not a preference |
| F-07 | The run process is multi-threaded and its threads launch subprocesses | `render_stream` and `runner_shared` start daemon threads (stream pump, stall watchdog, telemetry sampler via `register_active_sampler`); `run_analytics_telemetry.ResourceProbes._run_bounded` calls `subprocess.run` | F-06 is a live-run concern, not a test artifact |
| F-08 | The per-item probe is WIRED but currently UNREACHED | `execute_item_core` calls `_hsp.detect_host_capabilities(cli_host)` behind `if contract_action is not None`, and that guard is False for every runner action today | Nothing is broken today; this Set is prophylactic, and `chore` is the right kind |
| F-09 | Mapping `execute -> read_only` is forbidden, for two measured reasons | `read_only`'s `spec_basis` says "no agent session for a skip"; `format_host_capability_finding` rendered "...action execute..." verbatim | Order 02 adds a NEW class; settled by `iot7hc` PR-102 and not reopened |
| F-10 | Requiring `supports_commit_gateway` would be an outage | DECLARED AND NEVER PROBED with a False default; `_DECLARED_UNENFORCED` records that no commit-interception enforcement exists to attempt | Excluded by this Set's fence; the spec-side claim is carried elsewhere |
| F-11 | A shipped test pins the table to exactly one row and one action class | `test_host_capability_extension.py`'s requirement-map test asserts `set(ACTION_CAPABILITY_REQUIREMENTS) == {ACTION_READ_ONLY}` and `len(ACTION_CLASSES) == 1` | Order 02 DECLARES that file in `- Scope-Paths:` and its E-06 re-points the two pins to exact membership while leaving the four properties beside them intact |
| F-12 | Three suite failures pre-exist this Set's work | Bare `python3 -m pytest` at HEAD `6310b3e4`: `3 failed, 4624 passed, 2 skipped` (`test_selector_type_containment.py::test_must_not_refuse_matrix`, `test_run_finding_reachability.py::...test_unreachable_binding_refusal_fires_under_perturbation`, `test_spec_review_attestation.py::...test_every_real_spec_in_this_repository_still_conforms`) | Both children's V-items must account for each individually; the second perturbs the `RUN-HOST-CAPABILITY` row and is adjacent to this Set |

## Proposed changes (ordered, validatable)

1. Execute Order 01 (`bqtgmo`): freeze one descriptor per run, read it on the dispatch path, and make the probe's launch interception delegate rather than refuse. Adds no requirement.
2. Execute Order 02 (`y9m1ya`): add the mutating-execute action class requiring `supports_fresh_verifier_session`, map the runner's `execute` onto it, retract the falsified comments, and prove reachability, inertness, cascade and wording.

## Deferred / out of scope (with reason)

- REQUIRING `supports_commit_gateway` FOR ANY ACTION, and the spec-side claim that it is enforced. It is declared-never-probed with a False default by deliberate decision, so requiring it refuses every execute item on every host.
  - Carrier: gqy7yd
- A REAL PUSH-DENIAL BOUNDARY AND A CAPABILITY PROVING ONE. Pending Set `denypush` owns the mechanism work (`l4vw9o`, `pi3bk8`, `wzhe4n`); spec `25kzda` 5.2 already records the measured Landlock port-granularity limit that makes it hard.
  - Carrier: oq05nc
- ENFORCING VERIFIER SESSION INDEPENDENCE AT THE RUNNER'S OWN VERIFY SITE. That is a different mechanism from this capability row (a direct comparison of two session ids the runner already holds, versus a host descriptor requirement) and it is already planned, with this backlog item recorded as its deferred residual in its OQ-02.
  - Carrier: eow7p4
- REPRESENTING THE SIX `UNREPRESENTED_SPEC_CAPABILITIES` AS PROBED FIELDS. Order 02 RECORDS them in its new row's `unrepresented` tuple, which is the shipped mechanism for keeping an unrepresentable requirement visible instead of silently absent.
  - Carrier-Declined: Nothing is owed yet, because what each should BE is undecided rather than merely unbuilt: three of the six name guarantees the DRIVER provides as driver behavior, so whether a HOST capability field is even the right representation is an open design question this Set did not answer and has no evidence to settle. Filing six items would assert a conclusion nobody reached, and the keys already carry their spec phrase in code where a successor will meet them.
- A CROSS-RUN DESCRIPTOR CACHE WITH TTL/EXPIRY. `host_capability_registry` models expiry for a different question (which SKILL features a host supports), and `probe_runner_safety_capabilities`' docstring explicitly declines to import that model "by implication". A run-scoped freeze is the smallest object that removes the per-item probe.
  - Carrier-Declined: Nothing outstanding. This is a scope boundary rather than a dropped obligation: the run-scoped freeze satisfies the property the Set needs completely, and a cross-run cache would be an optimization whose necessity is unmeasured. The spec-field gap that IS real (descriptor entries carry no `evidence digest`, `expiry` or `assurance`) is recorded in Order 01's code comment rather than as a backlog row, because that is where a successor encounters it.
- AMENDING SPEC `25kzda`. Its 5.2 already requires a "fresh verifier" for a mutating action, already specifies the verbatim `RUN-HOST-CAPABILITY` refusal and its per-item fail-closed semantics, and already requires "a current capability descriptor". `01reg8` OQ-03 deliberately left the action table un-narrowed so a future requirement would have somewhere to land. This Set lands one in the code.
  - Carrier-Declined: Nothing is owed. The spec already specifies the behavior both children implement, so there is no divergence for a successor to reconcile; the Set moves the code toward the spec rather than the spec toward the code, and no `.spec.md` appears in any child's `- Scope-Paths:`.

## Scope check

- Over-scope: none. This orchestrator edits only itself. Across the two children: three product files, one new test module each, and one shipped test module (`tests/test_host_capability_extension.py`, declared by Order 02 because its one-row pin is falsified by design), with every edit confined to the action-requirement row, the runner mapping, the descriptor freeze, the launch interception, the comments those changes falsify, and the two pins that must be re-pointed.
- Under-scope: DELIBERATE AND STATED. The Set requires ONE capability for ONE action. Five of spec `25kzda` 5.2's mutation-row guarantees have no field in this contract and remain `unrepresented`, and one more (`commit_gateway`) is represented but deliberately not required. An operator must not read the result as a proven mutation boundary, and all three documents say so.
- THE MOST IMPORTANT LIMIT FOR AN APPROVER: on every host measured here the probe PASSES, so after this Set nothing is refused. The value delivered is that the guarantee becomes CHECKED rather than assumed, and that a host which ever fails the probe is refused instead of silently believed. This is not a fix for any failure observed in this repository, and no child claims one.

## Required tests / validation

- Each child owns its own validation and must paste the actual bare `python3 -m pytest` summary line against a baseline re-measured in its own lane. The authoring baseline was `3 failed, 4624 passed, 2 skipped` at HEAD `6310b3e4` (F-12), and each pre-existing failure must be accounted for individually rather than treated as noise.
- This orchestrator's own validation is limited to confirming each child reached `executed` with pasted evidence and that the cross-child and Set-wide properties hold. It runs no tests of its own and produces no deliverable.

## Spec / documentation sync

N/A with reason: no `.spec.md` is amended and none appears in this plan's or either child's `- Scope-Paths:`. Approved spec `25kzda` 5.2 already requires "a current capability descriptor backed by positive and fail-closed probe evidence", already lists "fresh verifier" among a mutating action's required host capabilities, and already specifies the verbatim `RUN-HOST-CAPABILITY` message with its `failed` / `host_capability_unavailable` per-item semantics. `01reg8` OQ-03 deliberately left that action table un-narrowed so a future requirement would have somewhere to land, and this Set lands one in the code. THE ADVISORY `check.plan-spec-link-missing` NUDGE IS DECLINED DELIBERATELY, not overlooked: `aw check` suggests `--from-spec 25kzda` because this plan cites that spec, and the rule is `info` precisely because, in its own words, "citing a spec as a constraint does not necessarily mean graduating from it". This plan graduated from backlog `s8veyk` and carries `- From-Backlog: s8veyk`; writing `- From-Spec:` would assert a provenance that did not happen. No user-facing documentation changes: the only operator-visible difference is a refusal on a path no measured host reaches, surfaced through the existing diagnostics block, `aw runs`' `Issue` column, and `aw host capabilities`.

## Open questions

### OQ-01: Is requiring ONE capability for ONE action the right size, or should the gate stay empty until more of the spec row can be represented?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFAULT IS THE NARROW GATE, and both children are written to it. The alternative (wait until a mutating action can require the whole spec row) is unreachable on measured ground: one of the row's named guarantees (`commit_gateway`) is represented by a field that is DECLARED AND NEVER PROBED because the enforcement does not exist here, and six more have no field at all, so "wait for the full row" means "never", while the strict probe that DOES pass keeps gating nothing. The narrow gate converts one assumed guarantee into a checked one at the cost of one row and one mapping entry, and it records the remaining six as `unrepresented` so the gap stays visible rather than being closed by omission.
  THE HONEST COST OF THE DEFAULT, so the maintainer can overrule it cheaply: a reader of the changed code could conclude the runner now enforces a mutation boundary, when what it enforces is one capability out of eight. All three documents in this Set say so explicitly, and Order 02's E-04 requires the operator-facing comments to say it too. Non-blocking because the narrow default is strictly safer than both alternatives: it refuses less than a wide gate and more than an empty one.
  - Carrier-Declined: There is nothing outstanding to carry. The question has a recorded default that is complete and safe, and the alternative ("keep the gate empty") is the status quo this Set exists to change rather than an unfixed defect, while the wider alternative is blocked by capabilities that measurably cannot be represented today. The visibility of that limit is handled inside the diff (the `unrepresented` tuple, plus Order 02's E-04 comments), which is a more durable location than a backlog row.

## Coverage findings

- "- THE TWO CHILDREN SHARE TWO FILES AND MUST NOT HAVE FOUGHT OVER THEM. Both declare `agent_workflows/host_sandbox_profile.py` and `agent_workflows/runner_shared.py`. Confirm the regions are disjoint: `bqtgmo` touches `_capture_turn_argv`'s interception plus the descriptor freeze and its dispatch read, while `y9m1ya` touches the action-class constant, `ACTION_CLASSES`, the requirement row, and the runner mapping with its comment. Report any overlap found rather than assuming the declaration prevented one."
- "- THE SECOND CHILD DID NOT REINTRODUCE WHAT THE FIRST REMOVED. After both land, confirm the dispatch path still performs no per-item probe, since `y9m1ya` edits the same function's neighborhood and a careless rehydration-to-probe reversion would silently restore the hazard while every one of its own tests still passed."
- "- THE SHIPPED CAPABILITY TESTS PASS AS A WHOLE, not just the two new modules. `tests/test_host_capability_extension.py` is edited by `y9m1ya` E-06 and guards the fail-OPEN omissions this Set could commit; run that module in full and confirm its four properties are intact rather than loosened."
- "- THE ADJACENT PRE-EXISTING FAILURE IS EXPLAINED ONCE, FOR THE SET. `test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation` fails at the Set's base commit AND perturbs the `RUN-HOST-CAPABILITY` row this Set changes the requirements behind. Both children must re-measure it; this item confirms the two explanations agree and that neither child's change altered its outcome."
- "Scope of this plan's own validation, stated so it is not mistaken for the children's: confirm each of the seven completion criteria above against the children's PASTED evidence and against a live interpreter rather than against this plan's prose; confirm the five cross-IPD properties above, naming any overlap, reversion or disagreement found; and cite no test result that did not come from a child's own recorded evidence, re-read from the executed plan rather than remembered."
- "7. NO FENCE WAS CROSSED. `supports_commit_gateway` is required by no action; the three constants `01reg8` deleted are not reinstated; no probe was added or altered; no `.spec.md` was modified; and the suite is at or above each lane's re-measured baseline with every pre-existing failure accounted for individually."

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

Scope of this plan's own validation, stated so it is not mistaken for the children's: confirm each of the seven completion criteria above against the children's PASTED evidence and against a live interpreter rather than against this plan's prose; confirm the five cross-IPD properties above, naming any overlap, reversion or disagreement found; and cite no test result that did not come from a child's own recorded evidence, re-read from the executed plan rather than remembered. This orchestrator runs no suite of its own and produces no deliverable.

- [ ] V-01 validates E-01
  - Required evidence: SHOW child `bqtgmo`'s on-disk status is `executed` and its file is under `.aw/records/plans/executed/`, by pasting the resolved path and its `- Status:` line. QUOTE each of its five `V-*` results, confirming each is `pass` with non-empty observed evidence rather than an assertion. PASTE the cross-child checks: both children's `- From-Backlog:` lines, both `- Blocks-Release:` states (expected absent, and state why `chore` is not auto-gated), and both `- Scope-Paths:` lines with an explicit statement of which files BOTH children edit and why child 01 executing first makes that safe. CONFIRM this item touched no product file.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: SHOW child `y9m1ya`'s on-disk status is `executed` and its file is under `.aw/records/plans/executed/`, by pasting the resolved path and its `- Status:` line. QUOTE each of its six `V-*` results, confirming each is `pass` with non-empty observed evidence. PASTE live interpreter output for the Set-wide property: `runner_action_contract_class` for `execute`, `review` and `plan`, showing exactly one is classified. PASTE the before/after comparison showing an execute item on a CAPABLE descriptor dispatches identically to before the Set, so the Set is proven to have added a refusal path without refusing any measured host. CONFIRM this item touched no product file.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

ORDER IS MANDATORY AND IS THE POINT OF THIS ORCHESTRATOR. Execute `bqtgmo` (Order 01) before `y9m1ya` (Order 02). Order 02's mapping row is what makes the already-wired per-item `detect_host_capabilities` call begin executing in live runs, and that call was measured substituting `subprocess.Popen` process-wide and refusing 238 of 300 concurrent launches in a process whose daemon threads themselves launch subprocesses (F-05..F-07). Running Order 02 first would ship that hazard as a side effect of a policy change. The dependency is declared machine-readably on Order 02 as `- Item-Dependencies: executed:bqtgmo`, so a runner enforces it; this paragraph exists for a human executing the Set by hand.

NEITHER CHILD CARRIES A BLOCKING OPEN QUESTION, and the one that could have was answered at authoring rather than deferred. A shipped test pins the requirement table to exactly one row and one action class, which Order 02 falsifies by design; rather than leave that as a maintainer question, Order 02 DECLARES `tests/test_host_capability_extension.py` in its `- Scope-Paths:` and its E-06 scopes the edit to re-pointing the two pins while keeping the four properties beside them. Declaring a path before approval is authoring, not a scope expansion. ORDER 01 can also be approved and executed independently of the policy decision, which is deliberate: its value (removing a per-item probe and a process-global launch hazard) stands whether or not the gate is ever required.

EXECUTION CONTRACT FOR THIS PLAN. This orchestrator's own items confirm child status and cross-child properties; they produce no deliverable and touch no product file. Commit only this plan file, through `aw commit <plan> -- <path>`, never `git add -A`, never `git commit -a`, never `--no-verify`, and never `git push`. Each child commits its own scope under its own contract.

WHAT AN APPROVER IS ACCEPTING ACROSS THE SET. Order 01 is a correctness repair with no behavior change: nothing an operator observes about which items run changes. Order 02 is a real behavior change: an execute item on a host whose fresh-verifier probe FAILS becomes refused, with no session started and its dependents cascaded, instead of running and being believed. On every host measured here the probe PASSES, so nothing is refused today; the one refusing case is a descriptor requested for a platform the interpreter is not running on, which is fail-closed and correct. You are NOT accepting a proven mutation boundary: one capability of eight is required, and the Set says so in three places.
