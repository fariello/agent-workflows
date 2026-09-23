# IPD: Refuse a second concurrent unattended driver in one checkout instead of letting two runs race main

- Date: 2026-09-22
- Kind: child
- Concern: Two unattended drivers can run in the SAME checkout at the same time, both integrating verified lanes to `main`, with nothing arbitrating between them, so each can invalidate the other's verified merge base mid-flight. OBSERVED 2026-09-22: `aw oc run commitguard compinert finidem laneorph nopush planprio retrywire runghostid runverdict setidhard stalecrit stopcrash --unattended` and `aw oc run graduate migleftover orchprobe reaskscore revladder roleadv runnerlayer runtrailwire runviewdisc setterguard specsweep --unattended` were both live, in one working tree, for hours.
  THE HARM IS MEASURED, NOT HYPOTHETICAL. While a human was hand-integrating the first run's stranded lanes, the second run advanced `main` by five commits (landing `fduoj4`), which silently invalidated an ALREADY-COMPLETED full-suite validation and forced the whole integration to be rebuilt and re-validated against the new tip. It then happened a SECOND time in the same session: after the rebuild, the other driver landed `vhbvwz`, and a prepared `--ff-only` publish refused with "Not possible to fast-forward", forcing a third rebuild. So the cost is not a one-off; it recurs for as long as both drivers live.
  A SILENT-REVERT CLAIM WAS MADE HERE AND IS RETRACTED AS FALSE, recorded rather than deleted because the correction is the useful part. The original text asserted that publishing a merge prepared against the older tip "would have REVERTED that plan's `pending/` -> `executed/` transition" in a "clean, conflict-free merge". The maintainer challenged it and DIRECT MEASUREMENT PROVED THE MAINTAINER RIGHT. Three cases were constructed in throwaway repositories, each with `main` moving a plan `pending/` -> `executed/` while a lane forked from the older base: (1) the lane EDITS the file at its old `pending/` path -> git reports `CONFLICT (modify/delete): pending/plan.md deleted in HEAD and modified in lane`; (2) the same with bodies similar enough for rename detection to fire -> git follows the rename and reports `CONFLICT (content): Merge conflict in executed/plan.md`; (3) the lane does NOT touch the plan at all and only edits an unrelated file -> the merge succeeds and the plan REMAINS in `executed/`, because a side that changed nothing about a file cannot revert it. So a stale side either CONFLICTS LOUDLY or leaves the transition intact; there is no third path that silently un-executes a plan. The 13-file conflict this run actually produced on `8u6770` is case (1)/(2) and is exactly that loud refusal working correctly.
  WHAT THE REAL HAZARD IS, once the false one is removed: WASTED VALIDATION AND A REFUSED PUBLISH, not corruption. The measured costs above stand unchanged (two forced rebuilds, one `--ff-only` refusal), and they are costs in operator and machine time rather than in record integrity. That is a weaker claim than the original and it is the honest one; this plan is worth doing for the wasted work and the invisibility of a peer, and NOT on the strength of a corruption risk that git demonstrably prevents.
  A THIRD COST, PAID BY THE OPERATOR: deciding what was safe to merge required computing, by hand, the overlap between one run's lane contents and the other run's still-queued items (the `8u6770` lane rewrites front matter on ten plan files the other driver still had queued or running). Nothing in any command's output reveals that a second driver is even present, so that analysis cannot be done without reading both runs' `state.json` directly.
  THE PRIMITIVES TO FIX THIS ALREADY EXIST AND ARE ALREADY USED FOR THE ADJACENT QUESTION. Each run holds an exclusive, non-blocking `driver.lock` acquired through `platform_lock.acquire`, whose docstring records it is exclusive and NON-BLOCKING; `platform_lock.probe_free` answers "is this lock held right now?" three-valued (`True` free, `False` a live holder, `None` unanswerable) WITHOUT creating, truncating or modifying anything; and `attention.get_active_runs_map` already filters to runs "whose driver process currently holds driver.lock". So liveness detection is solved and shipped. What is missing is that the lock is scoped PER RUN DIRECTORY, so it makes a run singular while leaving the REPOSITORY unprotected: two runs are two different lock files and neither contends with the other.
- Scope: Prevent two concurrently-integrating unattended drivers in one checkout, by detecting a live peer driver at startup and refusing (or serializing the integration step alone), and make the presence of a peer VISIBLE in operator-facing output. Consume the existing `platform_lock` primitives and the existing liveness probe; add no new lock implementation. EXCLUDES any change to the per-run `driver.lock` contract (spec `c4gd2h` R2's observable release), excludes the stale-base and dirty-tree guards inside `integrate_lane_branch` (which work and are not the gap), and excludes attended/interactive runs beyond reporting.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/cli.py, agent_workflows/engine.py, AGENTS.md, tests/test_concurrent_driver_guard.py, .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md, agent_workflows/platform_lock.py, agent_workflows/command_surface.py, tests/test_platform_lock.py, tests/test_rununify_build_parser.py, tests/test_rununify_initialize_run.py, tests/test_runner_shared.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: runconcur
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: vddpml
- Approval: 2026-09-23, recorded via aw ipd set: status set to approved
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- From-Backlog: yuffut

## Workflow history
- 2026-09-23 approved (aw set): status set to approved
- 2026-09-22 reviewed (aw set): plan-review complete: APPROVE WITH REVISIONS APPLIED; 8 findings, all FIXED; blocking OQ-04 resolved from its own recorded recommendation; readiness go-pending-approval; typed review record under .aw/records/reviews/

- 2026-09-22 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008, all FIXED. Reviewed at HEAD `c1859b5e`; `aw ipd lint --phase author` exit 1 on `IPD-Q501` (the blocking OQ-04) before, `--phase review-finalize` conforming after. THE PROBLEM IS REAL AND THE PRIMITIVES CLAIMS ALL VERIFY: `platform_lock.probe_free` is three-valued and side-effect free exactly as quoted, `attention.get_active_runs_map` does filter to live `driver.lock` holders, `driver.lock` IS per-run (so F-4's scoping diagnosis is correct), the `--allow-uncovered-orchestrator-work` justification precedent is real, `engine._wire_optin_precommit_hook` exists with the four named callers, and the AGENTS.md managed block is generated from `engine.py`. The retracted silent-revert claim is correctly retracted and the backlog item `yuffut` records the same correction. FIVE MEASURED DEFECTS, each of which would have produced a guard that looks right and is not. (1) A LANE WORKTREE resolves to its OWN nonexistent runs root: `run_viewer.discover_run_dirs(Path("."))` returned 0 from this lane while `attention._resolve_runs_repo_root` + the same call returned 242, so a peer query built the obvious way reports NO PEER from every execute lane (PR-001). (2) Policy B needs a BLOCKING acquire, which `platform_lock` reserves to exactly one caller and warns "would HANG a driver rather than fail it"; the plan named no bound (PR-002). (3) E-04's flag cannot exist without amending spec `25kzda` 2.1, proven by construction: injecting one undeclared flag turned `test_the_spec_and_the_owned_table_agree_in_both_directions` RED while the file is otherwise `70 passed`, and the plan said it declared NO spec path "deliberately" (PR-003). (4) E-05's "same function object" is FALSE for a wrapper binding: measured, `oc_runipd.integrate_lane_branch is agy_runipd.integrate_lane_branch` is False and `is runner_shared....` is False, while the `state_root` re-export IS identical, so the authored assertion would fail a CORRECT implementation (PR-004). (5) OQ-04 option (iii)'s hook is blind to the driver's happy path, since `pre-merge-commit` does not run for a fast-forward and `integrate_lane_branch` publishes `--ff-only` first (PR-005/F-11). Also fixed: the blocking OQ-04 was already answered in its own body yet gated the plan at every checkpoint (PR-006); all six Deferred rows named no durable carrier, so `aw check` reported `check.ipd-uncarried-obligation` at error (PR-007); and E-03 was still a conditional A-or-B after OQ-01 resolved to B (PR-008). `aw check` now reports ZERO findings for this plan.
- 2026-09-22 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `yuffut`, inheriting its `Blocks-Release: next` gate. Every claim is from direct observation during a hand-integration on 2026-09-22 (two live pids in one checkout, `main` advanced twice mid-validation, one `--ff-only` publish refused), plus source reading of the existing lock primitives. The plan deliberately proposes the POLICY as an open question for the maintainer rather than choosing unilaterally, because refusing to start a second run is a workflow restriction whose acceptability is the maintainer's call, while serializing only the integration is more permissive but more complex; both are specified so the decision is a one-line answer rather than a re-plan.
- 2026-09-22 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make it impossible for two unattended drivers in one checkout to integrate to `main` concurrently, and make a peer driver's existence obvious to anyone (human or agent) about to touch `main`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: see the peer

- [x] E-01 Add a shared, READ-ONLY peer-driver query in `runner_shared` that reports every OTHER run directory in this repository whose `driver.lock` is currently held by a live process, returning the run id, pid, and selectors for each. It MUST use `platform_lock.probe_free` (or `run_viewer.driver_holder_state`, which already wraps it) and MUST preserve its three-valued answer: an unanswerable probe (`None`/`HOLDER_UNKNOWN`) is reported as UNKNOWN and never as "no peer". It must create, truncate, or modify nothing.
  - Depends on: none
  - RESOLVE THE RUNS ROOT THE WAY `attention` ALREADY DOES, NOT WITH A BARE `discover_run_dirs`, or the query returns EMPTY in exactly the place the guard matters most (PR-001, measured at review in this lane). A LANE WORKTREE resolves `runner_shared.state_root` to its OWN `.aw/records/runs`, which does not exist, so `run_viewer.discover_run_dirs(Path("."))` returned `0` run dirs from here while `attention._resolve_runs_repo_root(Path("."))` correctly returned the main checkout and the same call against THAT returned `242`. `attention.get_active_runs_map` is right because it resolves first; a naive implementation reading its docstring and calling `discover_run_dirs` directly would silently report NO PEER from every lane. Reuse the existing resolver rather than writing a third one.
  - Expected outcome: run from a checkout with one live driver, the query names that run; with none, it returns empty; with an unanswerable probe, it reports unknown. PLUS the query run from a LANE WORKTREE and shown to find the same peers as from the main checkout, which is the case a bare `discover_run_dirs` fails.
  - Execution state: performed
- [x] E-02 Surface the peer in operator-facing output at run start: when a peer is detected, print a clearly marked line naming the peer run id and its selectors, so an operator reading the banner learns a second driver exists. Report UNKNOWN distinctly from NONE.
  - Depends on: E-01
  - Expected outcome: starting a run while a peer is live prints the peer's identity; starting alone prints nothing new.
  - Execution state: performed

### Task group 2: act on it

- [x] E-03 Implement POLICY B (resolved in OQ-01, so this is no longer conditional): serialize the INTEGRATION STEP behind a repository-level lock, leaving parallel execution untouched. The seam is the shared `runner_shared.integrate_lane_branch`, which both hosts already reach through thin wrappers that bind only `host_label`/`run_checked`/`action_kind`, so the lock belongs THERE and not at startup. Re-resolve `main`'s tip INSIDE the lock, since a tip read before acquiring is exactly the stale read this plan exists to stop. The wait must name the holder. An UNKNOWN probe must NOT refuse, since refusing on an unanswerable question would make the driver unstartable on a platform whose locks cannot be probed.
  - Depends on: E-01
  - DO NOT PASS `platform_lock.acquire(blocking=True)` WITHOUT ADDRESSING ITS DOCUMENTED SOLE-CALLER RULE (PR-002). That module states "BLOCKING IS OPT-IN AND HAS EXACTLY ONE CALLER ... ``project_registry.save_registry`` ... it is the ONLY caller permitted to pass it. Adding a second blocking caller needs its own justification, because several callers turn the already-held case into an operator-facing refusal and an accidental block would HANG a driver rather than fail it." Policy B REQUIRES waiting, so this item is that second caller and MUST carry the justification into `platform_lock`'s own docstring in the same change (amending the "exactly one caller" sentence so it does not become false). PREFER A BOUNDED WAIT over an unbounded one: an integration runs a full suite, so an unbounded block can hold a driver for an hour with no output, which is indistinguishable from the hang the rule warns about. State the timeout, report progress while waiting, and define what happens on expiry (defer the integration and re-queue, rather than failing the lane).
  - THE LOCK FILE MUST NOT LIVE IN A RUN DIRECTORY, because that is precisely the scoping defect F-4 records. Put it under the resolved runs root (or the records root) so every run in the checkout contends over ONE path, and use the resolver from E-01 so a lane worktree and the main checkout agree on it. State the chosen path and why it is reachable identically from both.
  - Expected outcome: with a live peer INTEGRATING, the second driver waits (bounded, naming the holder) and re-resolves main's tip after acquiring; with no peer, the integration path is behaviorally unchanged; with UNKNOWN, it proceeds with a warning. Parallel EXECUTION is shown unaffected.
  - Execution state: performed
- [x] E-04 Provide the documented ESCAPE HATCH for the deliberate case, a flag that permits concurrent integration and REQUIRES a justification string which is recorded durably in the run record (mirroring how `--allow-uncovered-orchestrator-work` requires and records a reason). No silent override. Register it in the SHARED `runner_shared.RUN_POLICY_FLAGS` table with `kind="str"` and an `owner`, exactly as that flag is registered, so both hosts inherit it from one row rather than each parser growing a copy.
  - Depends on: E-03
  - AMENDING SPEC `25kzda` SECTION 2.1 IS PART OF THIS ITEM, NOT AN OPTIONAL FOLLOW-UP, AND WITHOUT IT THE SUITE GOES RED (PR-003). `RUN_POLICY_FLAGS` is a CLOSED LIST whose membership is asserted against the spec FILE by `tests/test_run_flag_surface.py`, which parses section 2.1's grammar block rather than copying it. PROVEN AT REVIEW BY CONSTRUCTION: adding one undeclared flag to `RUN_POLICY_FLAGS_BY_FLAG` turned `test_the_spec_and_the_owned_table_agree_in_both_directions` RED with "registered here but NOT in spec 2.1's grammar: ['--allow-concurrent-driver']", and the file is `70 passed` otherwise. The spec file is now declared in `Scope-Paths` for exactly this reason, and the plan's spec-sync section says why. The alternative sanctioned route, if the maintainer prefers the flag NOT be part of `run`'s public surface, is to list it in that test's `DECLARED_BUT_NOT_OWNED_HERE` with a reason and an owner; choosing that route instead is acceptable and must be stated, but SILENCE IS A FAILURE by that file's own contract.
  - Expected outcome: the flag permits concurrent integration, the run record carries the justification, and omitting the justification is refused by argparse (as `--allow-uncovered-orchestrator-work` is). PLUS `python3 -m pytest tests/test_run_flag_surface.py` green WITH the spec amendment in place, pasted.
  - Execution state: performed

### Task group 3: the non-runner actor

- [x] E-07 Expose the integration lock as an OPERATOR-REACHABLE verb so a human or a non-runner agent publishing by hand contends over the SAME lock the drivers use, rather than over nothing. It must acquire, report who holds it when busy, and release reliably on both success and failure. This is OQ-04 option (ii) and is the only thing that makes the serialization honorable by anyone outside the runner.
  - Depends on: E-03
  - IT MUST BE THE SAME LOCK PATH E-03 CHOSE, resolved through the same resolver, or the two mechanisms contend over nothing and the verb is theater. Pin that with a test asserting the verb and the driver derive the path from ONE function, not two string literals that happen to match today.
  - RELEASE ON SIGNAL, NOT ONLY ON RETURN. A hand integration is the case most likely to be interrupted (the motivating incident involved a signal-stopped run), so the verb needs the same discipline `runner_shutdown` already applies to `driver.lock`: drop the lock observably on `SIGINT`/`SIGTERM`, and be idempotent so a second release is harmless. Note the OS drops an `flock` when the holder dies, so a killed process does not strand the lock; what needs handling is the FILE and any recorded holder line, which is what V-07's interrupted case must actually show.
  - Expected outcome: with a driver holding the integration lock, the verb reports the holder and waits or refuses per policy; with nothing holding it, it acquires and releases cleanly; an interrupted invocation does not leak the lock; and the verb's lock path is shown to come from the same resolver the driver uses.
  - Execution state: performed
- [x] E-08 State the protocol for non-runner actors in the MANAGED AGENTS.md block, generated from `engine.py` so every managed repo inherits it: before touching `main` by hand, check for a live peer driver, hold the integration lock through E-07's verb, re-resolve `main`'s tip inside the lock, and publish with `--ff-only` so a diverged tip refuses instead of merging. Say plainly that this is a PROTOCOL and that the enforcing hook (OQ-04 option iii) is deliberately not part of it.
  - Depends on: E-01, E-07
  - STATE THE `--ff-only` LIMIT HONESTLY RATHER THAN SELLING IT AS A SAFETY NET (PR-005). `--ff-only` refuses a DIVERGED tip, which is genuinely useful and is what happened on the day. It does NOT detect a peer that advanced `main` in a way the local branch can still fast-forward over, and it is NOT a substitute for holding the lock. Write the protocol so the lock is the mechanism and `--ff-only` is the backstop, not the reverse; a reader who takes `--ff-only` as sufficient will skip the lock, which is the behavior that caused the incident.
  - Expected outcome: the managed block carries the protocol, is regenerated from `engine.py` rather than hand-edited, names the read-only peer query and the lock verb by their real spellings, and states the `--ff-only` limit. Written with NO em or en dashes, since the managed block is user-facing prose (AGENTS.md execution contract).
  - Execution state: performed

### Task group 4: prove it

- [x] E-05 Ensure both hosts share ONE implementation of the guard rather than a per-host copy, and pin that with a structural test, since a one-sided guard would leave `aw agy run` able to race `aw oc run`. Bind the shared symbol in each host exactly as other shared runner symbols are bound.
  - Depends on: E-03
  - ASSERT DELEGATION, NOT OBJECT IDENTITY, IF THE BINDING IS A WRAPPER (PR-004). Measured at review: `oc_runipd.integrate_lane_branch is agy_runipd.integrate_lane_branch` is FALSE and `is runner_shared.integrate_lane_branch` is also FALSE, because each host binds a thin wrapper supplying `host_label`/`action_kind`; by contrast a re-export like `state_root` IS identical on all three. So "the same guard function object" holds only for a bare re-export. Decide which binding shape you shipped and assert accordingly: object identity for a re-export, or delegation (the wrapper body reaches the one shared definition, the form `tests/test_runner_shared.py` already uses for the integration wrappers) for a wrapper. An identity assertion against a wrapper fails for a CORRECT implementation, which is worse than no test.
  - Expected outcome: a test that pins one shared implementation in whichever form was shipped, shown to FAIL if either host is pointed at a copy. State which form and why.
  - Execution state: performed
- [x] E-06 Add the regression file covering: peer detected -> the integration serializes; no peer -> unchanged behavior; UNKNOWN probe -> proceeds with warning and never refuses; a STALE lock file whose holder is gone -> treated as NO peer (so a crashed run cannot permanently block the repository); the escape hatch requiring its justification; AND the LANE-WORKTREE case, where a naive `discover_run_dirs` reports no peer (F-7).
  - Depends on: E-03, E-04, E-05
  - COVER THE WAIT'S EXPIRY, not only its success. A bounded wait has two outcomes and the timeout arm is the one that will be under-tested: assert that expiry defers/re-queues rather than failing the lane, since a lane failed on a lock timeout would discard a completed validation, which is the very cost this plan exists to avoid.
  - Expected outcome: the file is RED against pre-fix source and GREEN after, with the dead-holder case proven not to block, the lane case proven to find the peer, and the timeout arm proven to defer rather than fail.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `platform_lock.probe_free` is already the house primitive for "is this lock held right now?", is explicitly three-valued, and explicitly observes "WITHOUT creating, truncating, or modifying anything". This plan must not add a second liveness mechanism beside it.
- `attention.get_active_runs_map` already filters to live runs by `driver.lock` holder liveness, so the notion of a live run is established and must be reused rather than redefined.
- The repository already has a precedent for a gate that REQUIRES a recorded justification instead of allowing a silent override (`--allow-uncovered-orchestrator-work`), and for a gate that PROCEEDS with a loud warning rather than halting when a probe cannot be answered (the orchestrator coverage gate on model-host outage). E-03 and E-04 follow both precedents deliberately.
- A crashed driver leaves a lock file behind, and the run viewer already projects that as `ABANDONED` rather than `running`. The guard must inherit that reasoning or a dead run would block the repository forever; this is why E-06 pins the dead-pid case.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | Two unattended drivers ran concurrently in one checkout | two live pids observed, each with a full `--unattended` selector list, in the same working tree |
| F-2 | A peer advanced `main` mid-validation, twice | five commits landed (incl. `fduoj4`) during one validation; a later `--ff-only` publish then refused after `vhbvwz` landed |
| F-3 | A stale merge CANNOT silently revert a peer's lifecycle transition (claim retracted) | measured in three throwaway repos: an editing stale side gives `CONFLICT (modify/delete)` or, under rename detection, `CONFLICT (content)`; a non-editing stale side leaves the plan in `executed/`. No silent path exists |
| F-4 | The existing lock makes a RUN singular, not the REPOSITORY | `driver.lock` lives in the run directory, so two runs hold two different locks and never contend |
| F-5 | Liveness detection is already solved and shipped | `platform_lock.probe_free` (three-valued, side-effect free) and `attention.get_active_runs_map` (filters to live holders) |
| F-6 | A peer is invisible in operator output | deciding what was safe to merge required reading both runs' `state.json` by hand |
| F-7 | A LANE WORKTREE resolves to its OWN (nonexistent) runs root, so a naive peer query finds NOTHING | measured at review in this lane: `run_viewer.discover_run_dirs(Path("."))` returned `0` while `attention._resolve_runs_repo_root(Path("."))` returned the main checkout and the same call there returned `242`. `runner_shared.state_root` from the lane points at `<lane>/.aw/records/runs`, which does not exist |
| F-8 | POLICY B NEEDS A BLOCKING ACQUIRE, which `platform_lock` reserves to exactly ONE caller | the module docstring: "BLOCKING IS OPT-IN AND HAS EXACTLY ONE CALLER ... it is the ONLY caller permitted to pass it. Adding a second blocking caller needs its own justification, because ... an accidental block would HANG a driver rather than fail it" |
| F-9 | THE ESCAPE-HATCH FLAG CANNOT BE ADDED WITHOUT AMENDING SPEC `25kzda` 2.1 | `RUN_POLICY_FLAGS` is a closed list asserted against the spec FILE by `tests/test_run_flag_surface.py`. Proven at review by construction: injecting one undeclared flag turned `test_the_spec_and_the_owned_table_agree_in_both_directions` RED ("registered here but NOT in spec 2.1's grammar"); the file is `70 passed` otherwise |
| F-10 | "BOTH HOSTS RESOLVE TO THE SAME FUNCTION OBJECT" IS FALSE for a wrapper-shaped binding | measured: `oc_runipd.integrate_lane_branch is agy_runipd.integrate_lane_branch` -> False, and `is runner_shared.integrate_lane_branch` -> False (each host binds a thin wrapper), while the re-export `state_root` IS identical across all three |
| F-11 | OQ-04 option (iii)'s hook would MISS the driver's own happy path | `pre-merge-commit` "does NOT run for a fast-forward merge (no commit is created)" (`.pre-commit-config.yaml`), and `runner_shared.integrate_lane_branch` publishes with `git merge --ff-only` first, falling back to `--no-ff` only when main advanced. So the hook would fire exactly when the merge was already non-trivial and stay silent on the clean serial case |

## Proposed changes (ordered, validatable)

1. A shared read-only peer-driver query preserving the three-valued probe (E-01).
2. Peer identity surfaced at run start (E-02).
3. Policy B enforced at the SHARED integration seam with a bounded wait, main's tip re-resolved inside the
   lock, never refusing on UNKNOWN (E-03).
4. A justification-requiring escape hatch in the shared flag table, WITH the spec 2.1 amendment the closed
   list requires (E-04).
5. One shared implementation across both hosts, pinned in the form that matches the binding (E-05).
6. Regression coverage including the dead-holder, UNKNOWN, and lane-worktree cases (E-06).
7. The lock exposed as an operator-reachable verb over the SAME path the driver uses (E-07).
8. The non-runner protocol in the managed block, stating `--ff-only`'s limit honestly (E-08).

## Deferred / out of scope (with reason)

- The per-run `driver.lock` contract and its observable release (spec `c4gd2h` R2): working as specified and untouched. This plan ADDS a repository-scoped question; it does not change the run-scoped one.
  - Carrier-Declined: NOTHING IS OUTSTANDING. The run-scoped contract is shipped and correct; this plan adds a second, repository-scoped lock beside it. There is no deferred work to carry, and filing an item would assert a defect in a contract this review found sound.
- `integrate_lane_branch`'s stale-base and dirty-tree guards: they correctly protect against a contaminated base WITHIN a run, and they are not the gap. The gap is that a peer can move `main` between one run's validation and its publish.
  - Carrier-Declined: NOTHING IS OUTSTANDING. These guards are shipped and this plan's own E-03 hooks the same function they live in, so they are context rather than deferred work.
- Attended (non-`--unattended`) runs: reported by E-02 but not refused, because a human at a terminal can see and judge the peer. With OQ-01 resolved to policy B the distinction NARROWS considerably, since B serializes the integration step rather than refusing a start, and a serialized integration is as correct for an attended run as for an unattended one. The executor should state whether the integration lock applies to attended runs too (it should, and it costs nothing) rather than leaving `--unattended` as the condition.
  - Carrier-Declined: RESOLVED INTO E-03 RATHER THAN DEFERRED. Under policy B there is no start-refusal to widen, so the open question the authored row implied (should attended runs be gated) is answered by applying the integration lock unconditionally, which E-03 now requires. No residual work remains to carry.
- Cross-CHECKOUT coordination (two clones of the same repository): out of scope, since they do not share a working tree and cannot fast-forward each other's `main` locally. NOTE ONE EXCEPTION FOUND AT REVIEW, so the boundary is honest rather than assumed: with a non-`repository` `records_backend` (`companion`/`home`), two checkouts resolve to the SAME runs root through `runner_shared.state_root`, so the peer query would see across them even though the integration question really is per working tree. That is a reporting quirk, not a correctness hole, and the executor should note it rather than design for it. This repository is `records_backend: repository`, verified in `.aw/config/project.json`.
  - Carrier-Declined: OUT OF SCOPE BY CONSTRUCTION, not postponed. Two working trees cannot invalidate each other's local merge base, so there is no hazard to carry. The shared-records-root quirk is a reporting note for the executor and creates no work item.
- Retroactively fixing the 2026-09-22 session: the affected lanes were integrated by hand and validated green; there is nothing to recover.
  - Carrier-Declined: ALREADY DISCHARGED. The lanes were integrated and validated at the time, so there is no outstanding remediation; the backlog item `yuffut` records the incident for provenance.
- THE `pre-merge-commit` ENFORCEMENT HOOK (OQ-04 option iii): deliberately NOT implemented here, on that question's own recorded recommendation, because a merge-blocking hook can wedge a maintainer mid-conflict-resolution and needs its own escape hatch. Review added the reason it is also WEAKER than advertised: `pre-merge-commit` does not run for a fast-forward merge, which is the driver's own happy path (F-11).
  - Carrier-Declined: NO CARRIER EXISTS YET AND FILING ONE IS THE MAINTAINER'S CALL, not this plan's. OQ-04's recommendation is to "file (iii) separately"; that filing is a scoping decision about whether a locally-skippable, ff-blind hook is worth its wedging risk, and this plan must not pre-commit the maintainer to it by minting a backlog item. The reasoning and the measured limit are recorded in OQ-04 and F-11 so the decision can be made from evidence.

## Scope check

- SIX PATHS ADDED AT EXECUTION (2026-09-22), each REQUIRED by a shipped contract rather than chosen, and each named here because a widened fence with no stated reason is how a scope gate becomes decoration. FOUR are PINNED MEASUREMENT CENSUSES that by their own construction fail when the flag surface changes and whose failure messages ASK to be updated in the same change: `tests/test_rununify_build_parser.py` (`LIVE_PARTITION` shared 55 -> 56, `POLICY_FLAG_ROWS` 13 -> 14, `LIVE_STRINGS_FROM_POLICY_TABLE` 22 -> 23, plus `--allow-concurrent-driver` in the four per-subparser option-string frozensets; its own message says "If this change is intended, update EXPECTED_OPTION_STRINGS in the SAME change and say why"), `tests/test_rununify_initialize_run.py` (`SHARED_OPTION_KEYS` gains `allow_concurrent_driver`, `LIVE_OPTION_KEY_UNION` 35 -> 36; the HOST-SPECIFIC count is unmoved, which is the property that partition polices), and `tests/test_runner_shared.py` (`NATIVE_SHARED_RUN_CHECKED_CALLERS` gains `_resolved_main_tip`, which its own message directs: "A NEW shared caller belongs in `NATIVE_SHARED_RUN_CHECKED_CALLERS`"). `agent_workflows/platform_lock.py` is the F-8 docstring amendment the plan's own E-03 REQUIRES, so its absence from the authored list was an oversight in the fence rather than a decision. `agent_workflows/command_surface.py` is mandatory for E-07: `find_undeclared_leaves` fails CI on any parser leaf carrying no `CommandDeclaration`, so the verb could not ship without its declaration. `tests/test_platform_lock.py` is the one genuinely JUDGED edit: its sole-blocking-caller guard was a LINE-SUBSTRING search that a DOCSTRING trips, so it went RED against a tree that honors the rule exactly (`integration_lock`'s docstring quotes "`blocking=True`" while explaining that it does NOT use it). It is converted to an `ast.walk` for a real `ast.keyword`, the identical remedy `tests/test_runner_telemetry_integration.py` and `tests/test_run_analytics_telemetry.py` already adopted, and the wider sweep is filed as backlog `xelvyi` rather than done here.
- Over-scope: the two host files are declared only for the thin binding E-05 requires; all logic lands in `runner_shared`. If the seam turns out to be fully reachable from `runner_shared` alone, the executor should NOT edit the host files and must report them as declared-but-unmodified with a `--scope-ack`.
  - AT EXECUTION both host files WERE modified, so no `--scope-ack` is needed for them: each binds the six shared symbols as `as <same-name>` re-exports (E-05's form), and `oc_runipd` additionally carries E-02's peer announcement inside the SHARED `announce_run_order`, which `agy_runipd` imports as the same object so both hosts get it from one edit.
- Under-scope: this plan serializes the INTEGRATION step. It does not make an already-running pair's in-flight state safe, and it proposes no in-flight coordination protocol. That is acceptable under policy B because integration is the only step that touches `main`, which is where the measured harm occurred.
- Under-scope, closed at review (2026-09-22): the peer query would have returned EMPTY from every lane worktree, which is where execute items actually run (PR-001/F-7, now a resolver requirement plus a lane case in V-01); policy B's required blocking acquire collided with `platform_lock`'s documented sole-caller rule and had no bound, so it could hang a driver silently (PR-002/F-8, now a docstring amendment plus a bounded wait); the escape-hatch flag could not be registered at all without amending spec `25kzda` 2.1, which the plan had explicitly declined to declare (PR-003/F-9, now declared and required in the same change); E-05's identity assertion would have FAILED against a correct wrapper binding (PR-004/F-10, now form-aware); E-08 risked presenting `--ff-only` as sufficient when it is blind to a fast-forwardable peer advance (PR-005/F-11); the blocking OQ-04 was already answered in its own body yet held the plan at every lint checkpoint (PR-006); every Deferred row named no durable carrier (PR-007); and E-03 was still written as a conditional A-or-B choice after OQ-01 had resolved to B (PR-008).

## Required tests / validation

- `python3 -m pytest tests/test_concurrent_driver_guard.py` GREEN after, and RED before, the before-run produced by reverting only the source changes while keeping the new tests.
- `python3 -m pytest tests/test_run_flag_surface.py` GREEN with the spec amendment in place (F-9). Baseline measured at review: `70 passed`. This file is the gate E-04 cannot pass without the spec edit, so it must be run explicitly rather than left to the bare suite.
- `python3 -m pytest` bare, count line pasted, NO NEW failing node ids against a baseline taken THE SAME WAY in the same worktree before the change. MEASURED AT REVIEW HEAD in this lane so the executor is not surprised by a red baseline: `2 failed, 8521 passed, 3 skipped, 2 xfailed`, both failures unrelated to this plan (`tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`, which is an ambient `OPENCODE_CONFIG_CONTENT` leak and is `76 passed` under `env -u OPENCODE_CONFIG_CONTENT`; and `tests/test_orchestrator_retirement.py::RealRepositorySets`, unrelated corpus drift). The gate is no NEW failures, never an absolute green, and neither of those tests may be edited by this plan.
- A REAL two-process demonstration on the INTEGRATION lock (not a run's `driver.lock`, which is the wrong scope): one process holds it, the second's actual waiting/naming behavior pasted. A mocked lock alone is insufficient for E-03's central claim.
- The dead-holder case demonstrated with a real leftover lock file whose holder is gone, showing NO refusal. State plainly that the OS drops an `flock` on process death, so this case is about the FILE and the recorded holder line rather than about the flock itself.
- The lane-worktree case for the peer query (F-7), since a bare `discover_run_dirs` returns zero from a lane.
- E-05's structural test output in whichever form matches the shipped binding (identity for a re-export, delegation for a wrapper), with the form stated (F-10).

## Spec / documentation sync

A SECOND, NON-SPEC CONTRACT DOCUMENT IS ALSO AMENDED, and it is named here because it carries a RULE other
plans are held to: `agent_workflows/platform_lock.py`'s module docstring. Its "BLOCKING IS OPT-IN AND HAS
EXACTLY ONE CALLER" paragraph would have become MISLEADING the moment a second caller needed to WAIT (F-8),
so E-03 amends it in the same change. The amendment does NOT grant a second blocking caller: it records that
a caller needing to wait should POLL the non-blocking acquire (bounded, reporting, deferring on expiry), names
`runner_shared.integration_lock` as the case that established the pattern, and keeps the original sentence
TRUE because `project_registry.save_registry` remains the only `blocking=True` caller. A test re-derives that
caller set package-wide, so the sentence cannot silently go false later.

ONE SPEC EDIT IS NOW MANDATORY AND DECLARED, CORRECTED AT REVIEW. The authored version said `Scope-Paths`
"contains none, deliberately" and left the spec sentence to a later pass. That is not available, because
E-04's flag CANNOT be registered without amending spec `25kzda` section 2.1 in the SAME change:
`runner_shared.RUN_POLICY_FLAGS` is a CLOSED LIST whose membership `tests/test_run_flag_surface.py` asserts
against the spec FILE by parsing its grammar block. Proven at review by construction - injecting one
undeclared flag turned `test_the_spec_and_the_owned_table_agree_in_both_directions` RED with "registered
here but NOT in spec 2.1's grammar", while the file is otherwise `70 passed`. So
`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` is DECLARED in
`Scope-Paths`, which is also what makes both runners ANNOUNCE the declared spec edit before the run starts
and reconcile it at finalize (AGENTS.md). The sanctioned alternative is to keep the flag off `run`'s public
surface by listing it in that test's `DECLARED_BUT_NOT_OWNED_HERE` with a reason and an owner; either route
is acceptable, silence is not, and whichever is taken must be stated in V-04.

WHY THE CONTRACT CHANGE IS WORTH MAKING, since a spec edit is the highest-leverage change a run can make:
section 2.1 is the authority for what an operator can discover about `run`. A concurrency escape hatch that
exists in code but not in the spec is a surface no operator can find and that a later spec edit has no
reason to preserve, which is the exact failure that test exists to prevent.

WHAT THE 2.1 AMENDMENT ACTUALLY SAYS, recorded at execution so the contract change is reviewable without
opening the spec. The grammar block gained `[--allow-concurrent-driver <justification>]`, and 2.1's Rules
gained one bullet which states: what the lock DOES and does NOT serialize ("a repository holds at most one
INTEGRATING driver, never at most one driver", so two runs may EXECUTE in parallel and the flag is
irrelevant to that); that WITHOUT the flag an integration WAITS, bounded, naming the holder, and on expiry
DEFERS with the lane preserved rather than FAILING it, because a lane failed on a lock timeout would
discard a completed validation; that an UNPROBEABLE platform never refuses and a CRASHED holder cannot
wedge the repository, since the OS drops an `flock` when its holder dies; and that the flag waives no other
gate. It carries the date and the plan id so a later reader can find the measurement behind it.

SPEC `c4gd2h` (the run lifecycle and the `driver.lock` invariants) is a SEPARATE matter and is deliberately
NOT edited here. This plan adds a REPOSITORY-scoped rule beside the run-scoped one rather than changing it,
and the honest sequence is to let `c4gd2h` record the shipped rule afterwards: with OQ-01 resolved to policy
B, that sentence must say a repository holds at most one INTEGRATING driver, never at most one driver. It is
not declared in `Scope-Paths` because this plan does not write it.

## Open questions

### OQ-01: Refuse a second unattended run outright (A), or allow it and serialize only the integration step (B)?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-22 to POLICY B, serialize the integration step only, so two drivers may execute in parallel but never publish concurrently. The reasoning recorded at the time: executing in parallel was never what caused harm, concurrent publishing was, and policy A would have removed a working practice (two runs over disjoint Sets). The cost accepted with B is a wait that can be long, because each integration runs a full suite, plus the fact that a bug in a lock fails in a hard-to-diagnose way; E-06's coverage of the dead-holder and unanswerable-probe cases is what keeps that cost bounded.

### OQ-04: How does a NON-RUNNER actor (a human, or an agent integrating by hand) honor the serialization, and how is it ENFORCED rather than merely documented?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Finding: PR-006
- Resolution or deferral rationale: OPTIONS (i) AND (ii) IN THIS PLAN, (iii) FILED SEPARATELY AND EXPLICITLY NOT IMPLEMENTED HERE. Resolved at review 2026-09-22 from THIS QUESTION'S OWN RECORDED RECOMMENDATION rather than by reviewer judgement: the rationale below already ends "RECOMMENDATION: do (i) and (ii) in this plan, and file (iii) separately ... The executor must NOT implement (iii) under this plan", and E-07 (the operator-reachable lock verb, option ii) and E-08 (the managed-block protocol, option i) already implement exactly that pair while E-08 is required to say the hook is deliberately excluded. So the question was ANSWERED IN ITS OWN BODY and marked `Blocking: yes / open`, which made `aw ipd lint` refuse the plan at every checkpoint (`IPD-Q501`, observed exit 1 at `--phase author`) for a decision that was already recorded. It is reclassified rather than deleted so the reasoning survives.
  ONE THING THE MAINTAINER SHOULD KNOW BEFORE FILING (iii), added at review because it changes that option's value: a `pre-merge-commit` hook would MISS the driver's own happy path. `.pre-commit-config.yaml` states `pre-merge-commit` "does NOT run for a fast-forward merge (no commit is created)", and `runner_shared.integrate_lane_branch` publishes with `git merge --ff-only` first, falling back to `--no-ff` only when main advanced. So the hook fires only on the already-non-trivial merge and is silent on the clean serial case, which is most of them. That does not make (iii) worthless (it still catches a raw hand `git merge` that creates a commit) but it does mean it is NOT the "only option that stops raw `git merge`" in full generality, and the separate plan should say so rather than inherit the stronger claim. See F-11.
  FOR THE RECORD, the original rationale as written: RAISED BY THE MAINTAINER 2026-09-22 and it is the more important half of the problem, because the incident that motivated this plan was a HAND integration racing a driver, which a driver-side lock does not touch. What I actually did on the day was ad-hoc and unenforceable: I re-read `main`'s tip before publishing, rebuilt when it moved (twice), and used `--ff-only` so a diverged tip refused rather than silently merging. That worked only because I chose to do it. THREE ENFORCEMENT SURFACES EXIST, in increasing strength, and the choice is the maintainer's because each trades safety against friction. (i) A DOCUMENTED PROTOCOL in the managed AGENTS.md block plus a read-only `aw` verb that reports live peers, so any agent can and must check before touching `main`. Cheap, portable, but advisory: an agent that skips the check is not stopped. (ii) THE SAME REPO-LEVEL LOCK EXPOSED AS A VERB (`aw integrate --lock` or equivalent) that a human or agent is instructed to hold while publishing, making the driver and the hand path contend over ONE lock rather than two mechanisms. Enforceable for anyone who uses the verb; bypassable by raw `git merge`. (iii) A `pre-merge-commit` HOOK that refuses a merge into `main` while a peer holds the integration lock. This is the only option that stops raw `git merge`, and the repository already has the exact machinery for it: `engine._wire_optin_precommit_hook` is a shared, idempotent, no-clobber, OPT-IN wiring helper already used by `create_precommit_scope_gate_hook`, `create_prepush_authorization_gate_hook`, `create_backlog_close_gate_hook` and `create_dependency_gate_hook`, and `pre-merge-commit` is a standard hook git already ships a sample for. ITS HONEST LIMITS, which the repository already states for its sibling hooks, are that git hooks are local, are not cloned by default, and are skippable with `--no-verify`, so the portable authority remains the protocol plus whatever `aw check` can observe after the fact. RECOMMENDATION: do (i) and (ii) in this plan, and file (iii) separately, because a merge-blocking hook can wedge a maintainer mid-conflict-resolution and deserves its own plan with its own escape hatch rather than being bolted onto a concurrency guard. The executor must NOT implement (iii) under this plan.

### OQ-02: Should the guard also cover an agent or human hand-integrating, as happened here?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: OUT OF SCOPE for enforcement, IN SCOPE for visibility. A human with a shell cannot be locked out by a driver-side guard, and attempting it would be security theater. What genuinely helps is E-02's visibility plus the existing `aw attention` live-run reporting, so anyone about to touch `main` can SEE the peer. The AGENTS.md shared-checkout rules already govern the human/agent side by instruction.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the query's actual output pasted for three real cases: one live peer (naming run id, pid, selectors), no peer (empty), and an unanswerable probe (UNKNOWN). Plus evidence it mutated nothing: the lock file's mtime and size before and after. PLUS THE LANE-WORKTREE CASE (F-7): the query run from inside a lane worktree and shown to report the SAME peers as from the main checkout. A query that returns empty from a lane FAILS this item even if it is correct from the main checkout, because every execute item runs in a lane by default.
  - Observed evidence: THE RESOLVER IS REQUIRED, MEASURED FROM THIS LANE (F-7 reproduced before fixing it):
    `runner_shared.state_root(Path('.'))` -> `<lane>/.aw/records/runs`;
    `run_viewer.discover_run_dirs(Path('.'))` -> `0`;
    `attention._resolve_runs_repo_root(Path('.'))` -> the main checkout;
    `discover_run_dirs(<main>)` -> `246`. So a bare `discover_run_dirs` finds NOTHING from a lane.
    `runner_shared.runs_repo_root` delegates to that resolver, and from this lane
    `runs_repo_root(Path('.'))` -> the main checkout, `integration_lock_path(Path('.'))` ->
    `<main>/.aw/records/runs/integration.lock`.
    THE LIVE QUERY, run from this lane against the real repository (both drivers of this run's own
    session were live at the time):
    ```
    peers: 2
      run-20260923T004057Z-1957544 live 1957544 ('kl18sz',)
      run-20260923T004124Z-1963274 live 1963274 ('vddpml',)
    ```
    THE THREE CASES plus the LANE case are pinned as tests and pass:
    `PeerQueryTests` (no run -> `[]`; lock file present but unheld -> `[]`; STALE lock whose holder is
    gone -> `[]`; LIVE holder -> run id + pid `4242` + selectors `('setid-x','abc123')`; unprobeable
    probe -> `PEER_UNKNOWN`), and `LaneWorktreeResolutionTests` in a REAL `git worktree add` fixture:
    `test_a_bare_discover_run_dirs_finds_NOTHING_from_the_lane` (asserts the defect),
    `test_the_resolver_makes_the_lane_and_the_main_checkout_AGREE`,
    `test_the_peer_query_finds_the_SAME_peer_from_the_lane_as_from_main`,
    `test_the_LOCK_PATH_is_identical_from_the_lane_and_from_main`.
    MUTATES NOTHING, asserted by BYTES not inspection:
    `test_the_query_MUTATES_NOTHING` compares `driver.lock`'s `read_bytes()`, `st_mtime_ns` and
    `st_size` across the query and requires all three unchanged.
    `python3 -m pytest tests/test_concurrent_driver_guard.py -o addopts="" -q` -> `50 passed in 17.32s`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: the startup output pasted with a peer live and again with none, showing the peer line present in the first and absent in the second, and UNKNOWN rendered distinctly from NONE.
  - Observed evidence: `oc_runipd.announce_run_order` driven against a real run dir, THREE states:
    ```
    --- NO PEER ---
    (no peer lines)
    --- PEER LIVE ---
    PEER DRIVER LIVE in this checkout: run-peer (pid 12345) on: setidA, setidB
    Integration to main is serialized behind the repository integration lock (integration.lock); parallel EXECUTION is unaffected.
    --- PEER UNKNOWN (unprobeable) ---
    PEER DRIVER UNKNOWN (its driver.lock could not be probed, which is NOT proof it is absent): run-peer on: setidA, setidB
    Integration to main is serialized behind the repository integration lock (integration.lock); parallel EXECUTION is unaffected.
    ```
    So NONE prints nothing new, LIVE names run id + pid + selectors, and UNKNOWN is a DISTINCT line that
    explicitly declines to claim absence. Pinned by `PeerReportTests`, including
    `test_an_unknown_peer_renders_DISTINCTLY_from_both_none_and_live` (asserts `UNKNOWN` present in the
    unknown rendering, ABSENT in the live one, the two strings unequal, and `NOT proof` present so the
    line cannot overclaim). Emitted from the SHARED `announce_run_order`, which `agy_runipd` imports as
    the same object, so both hosts get it from one edit. It is wrapped in a catch that prints a NAMED
    failure line rather than nothing, so "no peer" and "the query crashed" cannot render identically.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: the TWO-PROCESS demonstration, with one process genuinely holding the INTEGRATION lock (not a run's `driver.lock`, which is the wrong scope per F-4) and the second's actual behavior pasted: it WAITS, names the holder, and re-resolves main's tip after acquiring. Plus the UNKNOWN case shown PROCEEDING with a warning rather than refusing; plus an uncontended integration shown behaviorally unchanged; plus evidence that parallel EXECUTION is unaffected, since policy B permits it by design.
  - Required evidence for the blocking-acquire rule (F-8): the amended `platform_lock` docstring pasted, showing the "exactly one caller" sentence updated rather than left false, with this caller's justification. PLUS the BOUNDED wait demonstrated: the timeout value stated, the wait shown emitting progress rather than going silent, and the expiry path shown deferring/re-queueing rather than failing the lane. An unbounded silent block does NOT satisfy this item; it is indistinguishable from the hang `platform_lock` warns about.
  - Required evidence for the lock path: the resolved path pasted from BOTH the main checkout and a lane worktree, shown identical.
  - Observed evidence: A REAL TWO-PROCESS DEMONSTRATION ON THE INTEGRATION LOCK (not a run's
    `driver.lock`), via the shipped operator verb, in a throwaway git repo:
    ```
    === status while HELD ===
    integration lock HELD at <repo>/.aw/records/runs/integration.lock by aw integration-lock pid=3149539 started=2026-09-23T01:53:57+00:00
    === WAITER that SUCCEEDS after the holder releases (bound 30s) ===
    aw integration-lock: holding <repo>/.aw/records/runs/integration.lock
    834c5a5 init
    real 0m8.397s
    rc=0
    === status after both released ===
    integration lock FREE at <repo>/.aw/records/runs/integration.lock
    ```
    The second process genuinely WAITED 8.4s for the first and only then acquired and ran its command:
    that is real mutual exclusion, not a mock.
    THE BOUNDED WAIT NAMES THE HOLDER AND EMITS PROGRESS (45s holder, 70s bound):
    ```
    aw integration-lock: waiting for the repository integration lock held by aw integration-lock pid=3149727 started=2026-09-23T01:54:13+00:00 (30s of 70s)
    aw integration-lock: holding <repo>/.aw/records/runs/integration.lock
    834c5a5 init
    rc=0
    ```
    EXPIRY DEFERS, NOT FAILS (holder live, bound 5s):
    ```
    aw integration-lock: the repository integration lock at <repo>/.aw/records/runs/integration.lock is held by an unrecorded holder; waited 5s (bound 5s) and gave up. The integration is DEFERRED with its lane preserved, not failed.
    real 0m5.351s
    rc=1
    ```
    The timeout value is `INTEGRATION_LOCK_TIMEOUT_SECONDS = 1800.0` (stated, finite, pinned by
    `BoundedWaitTests::test_the_default_bound_is_FINITE`), progress cadence
    `INTEGRATION_LOCK_PROGRESS_SECONDS = 30.0`. `test_expiry_DEFERS_rather_than_FAILING_the_lane`
    asserts the expiry returns `INTEGRATION_REFUSAL_TRANSIENT`, that
    `classify_integration_refusal(kind)` is True (deferrable, lane preserved), and that the integration
    callable was NOT invoked at all (`called == []`).
    THE BLOCKING-ACQUIRE RULE (F-8) IS HONORED WITHOUT A SECOND BLOCKING CALLER, and the
    `platform_lock` docstring is amended rather than left false. It now reads:
    "A CALLER THAT GENUINELY NEEDS TO WAIT SHOULD POLL THIS NON-BLOCKING ACQUIRE, NOT PASS
    ``blocking=True`` ... ``runner_shared.integration_lock`` (runconcur-01 ``vddpml``) is the case that
    established this ... It therefore loops on ``acquire`` (no ``blocking``), reports progress to the
    operator while waiting, expires at a stated bound, and DEFERS the work on expiry rather than failing
    it. The sentence above stays TRUE - ``save_registry`` remains the only ``blocking=True`` caller".
    Asserted both ways: `BoundedWaitTests::test_NOTHING_passes_blocking_True_to_platform_lock` walks the
    lock's AST for a `blocking` keyword, and `PlatformLockRuleTests::
    test_save_registry_is_still_the_ONLY_blocking_caller` re-derives the package-wide caller set as
    exactly `['project_registry.py']`.
    MAIN'S TIP IS RE-RESOLVED INSIDE THE LOCK: `SerializationTests::
    test_MAIN_S_TIP_is_re_resolved_INSIDE_the_lock` asserts the recorded
    `integration_serialization.main_tip_in_lock` equals the REAL current `git rev-parse HEAD` AND that
    the integration callable observed `probe_free(...) is False` at the moment it ran, proving the merge
    executes inside the held lock so the tip cannot move under it.
    UNCONTENDED IS UNCHANGED (`test_an_UNCONTENDED_integration_is_behaviorally_UNCHANGED` returns the
    performer's sentinel triple verbatim). UNKNOWN NEVER REFUSES: there is no `probe_free` consultation
    on the acquire path at all, so an unprobeable platform cannot be made unstartable; the three-valued
    answer is surfaced only by the REPORT, which refuses nothing.
    PARALLEL EXECUTION IS UNAFFECTED: the lock is taken only at the publish seam
    (`integrate_under_repository_lock`), never at startup or around a turn; nothing in
    `initialize_run` or the dispatch loop acquires it.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: the escape hatch exercised with a justification (permitted, justification pasted from the durable run record) and without one (refused by argparse, message pasted). PLUS the spec/flag-surface contract satisfied (F-9): `python3 -m pytest tests/test_run_flag_surface.py` GREEN pasted, together with EITHER the spec 2.1 grammar diff declaring the flag OR the `DECLARED_BUT_NOT_OWNED_HERE` entry with its reason and owner. A green run with neither is impossible by that file's contract, so its absence means the flag was not actually registered in the shared table.
  - Observed evidence: WITHOUT a justification, argparse refuses:
    ```
    runipd start: error: argument --allow-concurrent-driver: expected one argument
    ```
    WITH one, the value is frozen as the operator's TEXT on BOTH hosts (never coerced to a bool):
    ```
    agent_workflows.oc_runipd -> 'two disjoint Sets, measured'
    agent_workflows.agy_runipd -> 'two disjoint Sets, measured'
    ```
    It appears on both hosts' `--help` as `[--allow-concurrent-driver JUSTIFICATION]`, and the
    justification reaches the durable record: `SerializationTests::
    test_CONSENT_skips_the_lock_and_RECORDS_the_justification` holds the lock with a peer, then asserts
    the consented attempt PROCEEDS and that `item["integration_serialization"]` carries
    `serialized: False` and `consent: "disjoint Sets, measured"`.
    THE SPEC/FLAG-SURFACE CONTRACT IS SATISFIED BY THE SPEC AMENDMENT ROUTE (F-9), not by
    `DECLARED_BUT_NOT_OWNED_HERE`: the flag IS part of `run`'s public surface, so
    `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` section 2.1 was
    amended in this same change. The grammar block gained
    `[--allow-concurrent-driver <justification>]`, and 2.1's Rules gained a bullet stating what the lock
    does and does not serialize ("a repository holds at most one INTEGRATING driver, never at most one
    driver"), that omission WAITS and DEFERS with the lane preserved rather than failing it, and that an
    unprobeable platform never refuses and a crashed holder cannot wedge the repository.
    `python3 -m pytest tests/test_run_flag_surface.py` -> `70 passed in 10.00s`
    (the baseline this file was measured at, now green WITH the amendment in place; without the
    amendment `test_the_spec_and_the_owned_table_agree_in_both_directions` would report the flag as
    "registered here but NOT in spec 2.1's grammar").
    Registered as ONE row in the SHARED `runner_shared.RUN_POLICY_FLAGS` with `kind="str"` and
    `owner="runner_shared.integrate_under_repository_lock"`, so both hosts inherit it from that row
    rather than each parser growing a copy; `EscapeHatchFlagTests` asserts the row's shape, both hosts'
    inheritance, the bare-refusal, the text freeze, and that OMITTING it freezes NO consent (`""`).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: the structural test's output pinning ONE shared implementation, plus a demonstration that it FAILS if one host is pointed at a copy, plus a statement of WHICH form was asserted (object identity for a re-export, delegation for a wrapper) and why that matches the binding shipped. An identity assertion against a wrapper binding FAILS this item, because measured at review the integration wrappers are NOT identical objects across hosts while the `state_root` re-export is (F-10).
  - Observed evidence: THE FORM ASSERTED IS OBJECT IDENTITY, and that choice is measured rather than
    assumed. Measured in this lane before choosing:
    `oc_runipd.integrate_lane_branch is agy_runipd.integrate_lane_branch` -> `False`;
    `oc_runipd.integrate_lane_branch is runner_shared.integrate_lane_branch` -> `False`
    (each host binds a thin WRAPPER supplying `host_label`/`action_kind`), while the re-export
    `oc_runipd.state_root is runner_shared.state_root is agy_runipd.state_root` -> `True`.
    Everything this plan ships is host-NEUTRAL - a lock path, a peer query, a serializer, none of which
    carries a host label - so it is bound as a RE-EXPORT and IDENTITY is the correct, stronger
    assertion. An identity assertion against a wrapper would fail a CORRECT implementation, which is
    why the form is stated rather than assumed (F-10/PR-004).
    `SharedImplementationTests` pins it three ways over all six symbols (`peer_drivers`,
    `format_peer_driver_report`, `integration_lock`, `integration_lock_path`,
    `integrate_under_repository_lock`, `runs_repo_root`):
    `test_every_shared_symbol_IS_the_same_object_on_both_hosts` (object identity against
    `runner_shared`), `test_NEITHER_host_DEFINES_any_of_them` (AST over each host's module body - this
    is the test that FAILS if a host is pointed at a copy, since identity alone could be satisfied today
    and quietly broken later), and `test_exactly_ONE_definition_package_wide` (exactly one `def` per
    symbol across `agent_workflows/*.py`).
    PLUS THE UNBYPASSABILITY PROPERTY, which is what makes the guard real rather than merely present:
    `test_NO_integration_call_site_BYPASSES_the_serializer` walks `runner_shared`'s AST and requires the
    review publish to be reached through `integrate_under_repository_lock`, and requires exactly one
    serializer definition. All four call sites now route through it: the in-run EXECUTE publish, the
    in-run REVIEW publish, the deferral ladder's rung-1 re-attempt, the ladder's post-ask retry, and
    `reintegrate_lane` (the out-of-band `aw <host> integrate <id6>` verb and the `--retry-incomplete`
    resume path).
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: the verb exercised in a REAL two-process test: one process holds the integration lock, the second invocation pastes its actual output naming the holder; then the uncontended case pasted acquiring and releasing; then an INTERRUPTED invocation (killed mid-hold) shown not to leak the lock, evidenced by a subsequent acquire succeeding. PLUS evidence the verb and the driver derive the lock path from ONE function rather than two matching literals. NOTE WHAT THE KILL CASE DOES AND DOES NOT PROVE: the OS drops an `flock` when its holder dies, so a subsequent acquire succeeding is expected even with no cleanup code at all; the item is satisfied only if the evidence ALSO addresses the lock FILE and any recorded holder line, which is the part a killed process can genuinely strand.
  - Observed evidence: `aw integration-lock` (declared at the `aw` layer, since the actor it exists for
    has no host). A REAL TWO-PROCESS test, one process holding while the other asks and waits:
    ```
    === status while HELD ===
    integration lock HELD at <repo>/.aw/records/runs/integration.lock by aw integration-lock pid=3149539 started=2026-09-23T01:53:57+00:00
    ```
    THE UNCONTENDED CASE acquires and releases cleanly, and forwards its command's exit code:
    ```
    $ aw integration-lock --dir <repo> -- git log --oneline -1
    aw integration-lock: holding <repo>/.aw/records/runs/integration.lock
    834c5a5 init
    rc=0
    $ aw integration-lock --status --dir <repo>
    integration lock FREE at <repo>/.aw/records/runs/integration.lock
    ```
    `--status` ACQUIRES NOTHING (`OperatorVerbTests::test_status_ACQUIRES_NOTHING` asserts
    `probe_free(...) is True` afterwards) and is three-valued (FREE / HELD / UNKNOWN, where UNKNOWN
    states it is "NOT proof it is free").
    THE VERB AND THE DRIVER GENUINELY CONTEND, asserted in both directions:
    `test_the_verb_WAITS_for_a_driver_and_gives_up_bounded` (a driver-side `integration_lock` holds; the
    verb waits, names `driver-side`, exits 1 with `DEFERRED` and merges nothing) and
    `test_the_verb_and_the_driver_genuinely_CONTEND` (the VERB holds in a real subprocess; the
    driver-side `integration_lock` is then REFUSED).
    ONE FUNCTION, NOT TWO MATCHING LITERALS:
    `test_the_verb_and_the_DRIVER_derive_the_path_from_ONE_function` asserts the CLI calls
    `_rs.integration_lock_path(` and `_rs.integration_lock(` and that the CLI spells
    `INTEGRATION_LOCK_FILENAME` NOWHERE itself, so the two cannot drift into contending over nothing.
    THE INTERRUPTED CASE: a `SIGINT`/`SIGTERM` handler drops the lock observably and is idempotent, and
    `test_a_KILLED_holder_does_not_strand_the_lock` proves a subsequent acquire succeeds. NOTE WHAT THAT
    DOES AND DOES NOT PROVE, as V-07 requires: the OS drops an `flock` on holder death, so that acquire
    is expected regardless; the evidence therefore ALSO addresses the FILE and the recorded holder line,
    which is the part a kill can strand, and the test asserts the next holder's own line is what is read
    back.
    TWO OF MY OWN DEFECTS WERE FOUND BY MEASURING THIS AND ARE FIXED, recorded because the corrections
    are the useful part. FIRST, the holder line was stored INSIDE the lock file and a waiter reported
    "an unrecorded holder" one second after a live holder wrote its name: `filelock` opens with
    `O_CREAT | O_TRUNC`, so the waiter's own FAILED acquire blanked the record it was about to read
    (the hazard `platform_lock`'s docstring documents for probes, here reached through acquire). The
    holder line now lives in a SIDECAR `filelock` never opens
    (`INTEGRATION_LOCK_HOLDER_FILENAME`), pinned by
    `test_the_holder_line_SURVIVES_a_competing_failed_acquire`.
    SECOND, and more serious, the release path unlinked the lock file the way
    `runner_shutdown.RunLockHandle` does for `driver.lock`. Measured in a throwaway repo with two real
    processes: `BEFORE unlink: second acquire correctly REFUSED` / `AFTER unlink: second acquire
    SUCCEEDED while first still holds -> TWO HOLDERS`. Unlinking a HELD path lets the next process
    create a fresh inode at the same name and acquire it, which is a total mutual-exclusion failure and
    for THIS lock is exactly the concurrent publish it exists to prevent. `driver.lock` may unlink
    because it has ONE acquirer and everyone else merely probes it; this lock is contended by
    construction. The lock file is now NEVER unlinked (only the sidecar is cleared), pinned by
    `test_the_lock_file_is_NEVER_UNLINKED_on_release`.
  - Result: pass
- [x] V-08 validates E-08
  - Required evidence: the regenerated AGENTS.md managed block pasted, plus evidence it was produced by regenerating from `engine.py` and not hand-edited (show the generator invocation and a clean diff afterwards), plus confirmation the named verb spellings match the ones E-01/E-07 actually shipped. PLUS the block shown to state the `--ff-only` limit (F-11) rather than presenting it as sufficient, and to contain no em or en dashes.
  - Observed evidence: GENERATED, NOT HAND-EDITED. The section is authored in `engine.py`'s managed
    block prose and `AGENTS.md` was rewritten by REGENERATING:
    ```
    $ python3 -c "... engine.merge_aw_block(existing, engine.agents_managed_sections(target_layout='aw'), ...)"
    action: refreshed
    $ git diff --stat AGENTS.md
     AGENTS.md | 14 ++++++++++++++
     1 file changed, 14 insertions(+)
    ```
    A CLEAN 14-line insertion with nothing else touched, which is what "regenerated" looks like; the new
    section is `### Before you publish to main by hand, hold the integration lock`.
    THE NAMED SPELLINGS ARE THE ONES SHIPPED: the block names `aw integration-lock --status` and
    `aw integration-lock -- git merge --ff-only <branch>`, and
    `ManagedBlockProtocolTests::test_it_names_the_SHIPPED_verb_spellings` cross-checks that
    `integration-lock` is a LIVE parser leaf via `discover_parser_leaves(cli._build_parser())` rather
    than trusting the prose.
    THE `--ff-only` LIMIT IS STATED HONESTLY (F-11/PR-005) rather than sold as a safety net: "Publishing
    with `--ff-only` is a useful BACKSTOP, since a diverged tip then refuses instead of merging, but it
    is NOT a substitute for holding the lock: it is blind to a peer that advanced `main` in a way your
    branch can still fast-forward over. Hold the lock; let `--ff-only` catch what the lock cannot."
    THE HOOK IS NAMED AS DELIBERATELY EXCLUDED, with the reason: "A merge-blocking git hook is
    DELIBERATELY not part of this: it would be local-only and skippable, and it would also miss the
    driver's own happy path, because a fast-forward creates no commit for such a hook to run on."
    OQ-04 option (iii) was NOT implemented, as the plan's approval gate requires.
    NO EM OR EN DASHES: `'\u2014' in block` -> `False`, `'\u2013' in block` -> `False`, asserted by
    `test_the_managed_block_carries_NO_em_or_en_dashes`.
    `ManagedBlockProtocolTests` (5 tests) passes, including
    `test_the_repository_s_OWN_agents_file_carries_the_regenerated_block`.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: the new test file GREEN after and RED before, the bare suite count line, and the dead-pid case demonstrated with a real leftover lock file showing NO refusal (so a crashed run cannot block the repository).
  - Observed evidence: `tests/test_concurrent_driver_guard.py`, 50 tests.
    GREEN AFTER:
    ```
    $ python3 -m pytest tests/test_concurrent_driver_guard.py -o addopts="" -q
    ..................................................                       [100%]
    50 passed in 17.32s
    ```
    RED BEFORE, produced by stashing ONLY the source changes and keeping the new tests:
    ```
    $ git stash push -- agent_workflows/ AGENTS.md .aw/records/specs/ tests/test_rununify_build_parser.py
    $ python3 -m pytest tests/test_concurrent_driver_guard.py -o addopts="" -q
    45 failed, 5 passed in 96.44s (0:01:36)
    ```
    (the 5 that still pass pre-fix are the ones asserting the DEFECT itself, e.g.
    `test_a_bare_discover_run_dirs_finds_NOTHING_from_the_lane`, which must pass in both states.)
    THE DEAD-HOLDER CASE with a REAL leftover lock file whose holder is gone shows NO refusal:
    `PeerQueryTests::test_a_STALE_lock_whose_holder_is_gone_reports_NO_peer` writes a `driver.lock`
    recording `pid=999999` and asserts `peer_drivers(...) == []`; and
    `RealTwoProcessContentionTests::test_a_KILLED_holder_does_not_strand_the_lock` forks a REAL holder,
    `SIGKILL`s it, and asserts the next acquire SUCCEEDS. Stated plainly, as V-06 requires: the OS drops
    an `flock` when its holder dies, so that acquire would succeed with no cleanup code at all; the test
    therefore ALSO asserts the recorded holder line is the NEW holder's, which is the part a killed
    process can genuinely strand.
    THE LANE-WORKTREE CASE is covered in a real `git worktree add` fixture (see V-01).
    THE UNKNOWN PROBE proceeds and never refuses; the ESCAPE HATCH requires its justification.
    THE TIMEOUT ARM DEFERS rather than failing (see V-03).
    BARE SUITE, count lines pasted, taken THE SAME WAY in this worktree before and after:
    ```
    BASELINE (source stashed, new test file moved aside):
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 8567 passed, 3 skipped, 2 xfailed, 3 warnings in 128.47s (0:02:08)

    FINAL (all changes in place):
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 8617 passed, 3 skipped, 2 xfailed, 6 warnings in 119.04s (0:01:59)
    ```
    NO NEW failing node ids: the same single pre-existing failure on both sides, +50 passing. That
    failure is the known ambient `OPENCODE_CONFIG_CONTENT` leak and is NOT this plan's:
    `env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py` -> `76 passed in 4.12s`.
    Neither `tests/test_turn_bounds.py` nor `tests/test_orchestrator_retirement.py` was edited (the
    latter passed in both runs at this HEAD).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is human-approved before execution and is executed under the repository's standing agent execution contract: commit ONLY the declared `Scope-Paths` through `aw commit`, never `git add -A` and never push; paste ACTUAL runner output for every test claim; and do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete observed evidence. A worker-role lane may NOT perform the terminal transition (`AW-LIFECYCLE-ROLE-001`): the runner owns `aw ipd begin`/`aw ipd finalize`.

BOTH OPEN QUESTIONS ARE NOW RESOLVED, so nothing blocks execution on a decision. OQ-01 is POLICY B (the
maintainer, 2026-09-22): serialize the integration step, leave parallel execution alone. OQ-04 is OPTIONS (i)
AND (ii) HERE, (iii) FILED SEPARATELY, resolved at review from that question's own recorded recommendation;
E-07 and E-08 are those two options and the executor MUST NOT implement the hook.

THE SPECIFIC HAZARD OF THIS PLAN IS NO LONGER "REFUSES TOO EAGERLY", AND SAYING SO PRECISELY MATTERS BECAUSE
THE MITIGATION DIFFERS. Under policy B nothing refuses a start, so the failure mode is a WAIT THAT NEVER
ENDS: `platform_lock` warns in its own module docstring that "an accidental block would HANG a driver rather
than fail it", and an integration runs a full suite, so an unbounded wait is indistinguishable from a hang and
can silently consume a night. The mitigations are therefore a BOUNDED wait with progress output and a defined
expiry (E-03), plus the dead-holder and UNKNOWN cases pinned in E-06 so a crashed peer or an unprobeable
platform can never wedge the repository. A guard that hangs is worse than no guard, because no guard at least
makes progress.

THE SPEC EDIT IS PART OF THE WORK, NOT A FOLLOW-UP. `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`
is declared in `Scope-Paths` because E-04's flag cannot be registered without it (the closed-list contract
test parses that file). Both runners announce a declared spec edit before the run starts and reconcile it at
finalize, so an undeclared spec edit would be caught; an UNDECLARED-but-required one would simply fail the
suite. Say WHY in the spec-sync section, which it now does.

SCOPE FENCE. Touch ONLY the declared `Scope-Paths`. Specifically do NOT edit
`tests/test_turn_bounds.py` or `tests/test_orchestrator_retirement.py`, the two tests already failing at
review HEAD for unrelated reasons; they are neither this plan's to fix nor its to loosen. If the work
genuinely requires a path outside the fence, MAKE the edit and JUSTIFY it, since `aw ipd finalize` refuses to
complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path
carries a `--scope-ack`.
