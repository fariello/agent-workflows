# IPD: Refuse a second concurrent unattended driver in one checkout instead of letting two runs race main

- Date: 2026-09-22
- Kind: child
- Concern: Two unattended drivers can run in the SAME checkout at the same time, both integrating verified lanes to `main`, with nothing arbitrating between them, so each can invalidate the other's verified merge base mid-flight. OBSERVED 2026-09-22: `aw oc run commitguard compinert finidem laneorph nopush planprio retrywire runghostid runverdict setidhard stalecrit stopcrash --unattended` and `aw oc run graduate migleftover orchprobe reaskscore revladder roleadv runnerlayer runtrailwire runviewdisc setterguard specsweep --unattended` were both live, in one working tree, for hours.
  THE HARM IS MEASURED, NOT HYPOTHETICAL. While a human was hand-integrating the first run's stranded lanes, the second run advanced `main` by five commits (landing `fduoj4`), which silently invalidated an ALREADY-COMPLETED full-suite validation and forced the whole integration to be rebuilt and re-validated against the new tip. It then happened a SECOND time in the same session: after the rebuild, the other driver landed `vhbvwz`, and a prepared `--ff-only` publish refused with "Not possible to fast-forward", forcing a third rebuild. So the cost is not a one-off; it recurs for as long as both drivers live.
  THE NEAR-MISS IS WORSE THAN THE COST. A merge prepared against the older tip still held `fduoj4`'s plan in `pending/`, so publishing it would have REVERTED that plan's `pending/` -> `executed/` transition and re-opened a plan the other run had genuinely executed. Nothing in the tooling would have flagged that: it is a clean, conflict-free merge that quietly undoes another run's lifecycle transition. This is the same class of stale-snapshot hazard the runner ALREADY guards for its own lanes (`integrate_lane_branch` fails closed on a contaminated base and on a stale base), but no guard exists BETWEEN two drivers.
  A THIRD COST, PAID BY THE OPERATOR: deciding what was safe to merge required computing, by hand, the overlap between one run's lane contents and the other run's still-queued items (the `8u6770` lane rewrites front matter on ten plan files the other driver still had queued or running). Nothing in any command's output reveals that a second driver is even present, so that analysis cannot be done without reading both runs' `state.json` directly.
  THE PRIMITIVES TO FIX THIS ALREADY EXIST AND ARE ALREADY USED FOR THE ADJACENT QUESTION. Each run holds an exclusive, non-blocking `driver.lock` acquired through `platform_lock.acquire`, whose docstring records it is exclusive and NON-BLOCKING; `platform_lock.probe_free` answers "is this lock held right now?" three-valued (`True` free, `False` a live holder, `None` unanswerable) WITHOUT creating, truncating or modifying anything; and `attention.get_active_runs_map` already filters to runs "whose driver process currently holds driver.lock". So liveness detection is solved and shipped. What is missing is that the lock is scoped PER RUN DIRECTORY, so it makes a run singular while leaving the REPOSITORY unprotected: two runs are two different lock files and neither contends with the other.
- Scope: Prevent two concurrently-integrating unattended drivers in one checkout, by detecting a live peer driver at startup and refusing (or serializing the integration step alone), and make the presence of a peer VISIBLE in operator-facing output. Consume the existing `platform_lock` primitives and the existing liveness probe; add no new lock implementation. EXCLUDES any change to the per-run `driver.lock` contract (spec `c4gd2h` R2's observable release), excludes the stale-base and dirty-tree guards inside `integrate_lane_branch` (which work and are not the gap), and excludes attended/interactive runs beyond reporting.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_concurrent_driver_guard.py
- Item-Dependencies: none
- Status: to-review
- Set: runconcur
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: vddpml
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- From-Backlog: yuffut

## Workflow history

- 2026-09-22 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `yuffut`, inheriting its `Blocks-Release: next` gate. Every claim is from direct observation during a hand-integration on 2026-09-22 (two live pids in one checkout, `main` advanced twice mid-validation, one `--ff-only` publish refused), plus source reading of the existing lock primitives. The plan deliberately proposes the POLICY as an open question for the maintainer rather than choosing unilaterally, because refusing to start a second run is a workflow restriction whose acceptability is the maintainer's call, while serializing only the integration is more permissive but more complex; both are specified so the decision is a one-line answer rather than a re-plan.
- 2026-09-22 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make it impossible for two unattended drivers in one checkout to integrate to `main` concurrently, and make a peer driver's existence obvious to anyone (human or agent) about to touch `main`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: see the peer

- [ ] E-01 Add a shared, READ-ONLY peer-driver query in `runner_shared` that reports every OTHER run directory in this repository whose `driver.lock` is currently held by a live process, returning the run id, pid, and selectors for each. It MUST use `platform_lock.probe_free` and MUST preserve its three-valued answer: an unanswerable probe (`None`) is reported as UNKNOWN and never as "no peer". It must create, truncate, or modify nothing.
  - Depends on: none
  - Expected outcome: run from a checkout with one live driver, the query names that run; with none, it returns empty; with an unanswerable probe, it reports unknown.
  - Execution state: pending
- [ ] E-02 Surface the peer in operator-facing output at run start: when a peer is detected, print a clearly marked line naming the peer run id and its selectors, so an operator reading the banner learns a second driver exists. Report UNKNOWN distinctly from NONE.
  - Depends on: E-01
  - Expected outcome: starting a run while a peer is live prints the peer's identity; starting alone prints nothing new.
  - Execution state: pending

### Task group 2: act on it

- [ ] E-03 Implement the maintainer-chosen policy from OQ-01 at the startup seam, fail-closed on a DETECTED live peer for an `--unattended` run: either REFUSE to start (policy A) or proceed with integration serialized behind a repository-level lock (policy B). The refusal or the wait must name the peer run and say what the operator can do. An UNKNOWN probe must NOT refuse, since refusing on an unanswerable question would make the driver unstartable on a platform whose locks cannot be probed.
  - Depends on: E-01
  - Expected outcome: with a live peer, a second `--unattended` run behaves per the chosen policy; with no peer, startup is byte-unchanged; with UNKNOWN, startup proceeds with a warning.
  - Execution state: pending
- [ ] E-04 Provide the documented ESCAPE HATCH for the deliberate case, a flag that permits a second concurrent run and REQUIRES a justification string which is recorded durably in the run record (mirroring how `--allow-uncovered-orchestrator-work` requires and records a reason). No silent override.
  - Depends on: E-03
  - Expected outcome: the flag permits the start, and the run record carries the justification; omitting the justification is refused.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 Ensure both hosts share ONE implementation of the guard rather than a per-host copy, and pin that with a structural test, since a one-sided guard would leave `aw agy run` able to race `aw oc run`. Bind the shared symbol in each host exactly as other shared runner symbols are bound.
  - Depends on: E-03
  - Expected outcome: a test asserts both hosts resolve to the same guard function object, and would fail if either forked it.
  - Execution state: pending
- [ ] E-06 Add the regression file covering: peer detected -> chosen policy applied; no peer -> unchanged startup; UNKNOWN probe -> proceeds with warning and never refuses; a STALE lock file whose pid is dead -> treated as NO peer (so a crashed run cannot permanently block the repository); and the escape hatch requiring its justification.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: the file is RED against pre-fix source and GREEN after, with the dead-pid case proven not to block.
  - Execution state: pending

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
| F-3 | A stale merge could silently revert a peer's lifecycle transition | the older tip still held `fduoj4` in `pending/`, so a clean merge would have undone its `pending/` -> `executed/` move |
| F-4 | The existing lock makes a RUN singular, not the REPOSITORY | `driver.lock` lives in the run directory, so two runs hold two different locks and never contend |
| F-5 | Liveness detection is already solved and shipped | `platform_lock.probe_free` (three-valued, side-effect free) and `attention.get_active_runs_map` (filters to live holders) |
| F-6 | A peer is invisible in operator output | deciding what was safe to merge required reading both runs' `state.json` by hand |

## Proposed changes (ordered, validatable)

1. A shared read-only peer-driver query preserving the three-valued probe (E-01).
2. Peer identity surfaced at run start (E-02).
3. The chosen policy enforced at startup, fail-closed on a detected peer, never on UNKNOWN (E-03).
4. A justification-requiring escape hatch, recorded durably (E-04).
5. One shared implementation across both hosts, structurally pinned (E-05).
6. Regression coverage including the dead-pid and UNKNOWN cases (E-06).

## Deferred / out of scope (with reason)

- The per-run `driver.lock` contract and its observable release (spec `c4gd2h` R2): working as specified and untouched. This plan ADDS a repository-scoped question; it does not change the run-scoped one.
- `integrate_lane_branch`'s stale-base and dirty-tree guards: they correctly protect against a contaminated base WITHIN a run, and they are not the gap. The gap is that a peer can move `main` between one run's validation and its publish.
- Attended (non-`--unattended`) runs: reported by E-02 but not refused, because a human at a terminal can see and judge the peer. If review wants attended runs gated too, that is a one-line widening of E-03's condition.
- Cross-CHECKOUT coordination (two clones of the same repository): out of scope, since they do not share a working tree and cannot fast-forward each other's `main` locally.
- Retroactively fixing the 2026-09-22 session: the affected lanes were integrated by hand and validated green; there is nothing to recover.

## Scope check

- Over-scope: the two host files are declared only for the thin binding E-05 requires; all logic lands in `runner_shared`. If the startup seam turns out to be fully reachable from `runner_shared` alone, the executor should NOT edit the host files and must report them as declared-but-unmodified.
- Under-scope: this plan guards the START of a run. It does not make an already-running pair safe, so if the maintainer chooses policy A, two runs started before this lands remain unguarded. That is acceptable because the guard's purpose is to prevent the situation arising, and no in-flight coordination protocol is proposed here.

## Required tests / validation

- `python3 -m pytest tests/test_concurrent_driver_guard.py` GREEN after, and RED before, the before-run produced by reverting only the source changes while keeping the new tests.
- `python3 -m pytest` bare, count line pasted, no new failing node ids against a baseline taken in the same worktree before the change.
- A REAL two-process demonstration: hold a `driver.lock` in a temporary run directory from one process, then run the guard from another, pasting the actual refusal or serialization behavior. A mocked lock alone is insufficient for E-03's central claim.
- The dead-pid case demonstrated with a real leftover lock file whose recorded pid does not exist, showing NO refusal.
- E-05's structural test output showing both hosts resolve to the same function object.

## Spec / documentation sync

Spec `c4gd2h` describes the run lifecycle and the `driver.lock` invariants; this plan adds a REPOSITORY-scoped concurrency rule that the spec does not currently state. The executor MUST declare any `.spec.md` edit in `Scope-Paths` before making it (the current declaration contains none, deliberately), and the recommended sequence is to implement the guard first and then propose the spec sentence once the chosen policy is settled by OQ-01, so the spec records a shipped rule rather than an intention. If the maintainer chooses policy B (serialize integration), the spec sentence must say that a repository holds at most one INTEGRATING driver rather than at most one driver.

## Open questions

### OQ-01: Refuse a second unattended run outright (A), or allow it and serialize only the integration step (B)?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT the executor's call, because the two policies trade throughput against simplicity and the acceptable answer depends on how the maintainer actually works. POLICY A (refuse) is simple, total, and easy to prove correct, but it forbids a workflow the maintainer has demonstrably been using: two runs covering disjoint Sets, which is a legitimate way to parallelize. POLICY B (serialize integration behind a repository-level lock, re-resolving `main`'s tip inside the lock) preserves that parallelism and fixes the actual harm, since executing in parallel was never the problem and concurrent publishing was, but it is more code, it introduces a wait that can be long because each integration runs a full suite, and a bug in it fails in the hardest-to-diagnose way. RECOMMENDATION: B, because the measured harm is entirely in the publish step and A would remove a working practice. The executor must NOT choose: with no answer this plan stops after E-02, which is pure observability and safe to land alone.

### OQ-02: Should the guard also cover an agent or human hand-integrating, as happened here?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: OUT OF SCOPE for enforcement, IN SCOPE for visibility. A human with a shell cannot be locked out by a driver-side guard, and attempting it would be security theater. What genuinely helps is E-02's visibility plus the existing `aw attention` live-run reporting, so anyone about to touch `main` can SEE the peer. The AGENTS.md shared-checkout rules already govern the human/agent side by instruction.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the query's actual output pasted for three real cases: one live peer (naming run id, pid, selectors), no peer (empty), and an unanswerable probe (UNKNOWN). Plus evidence it mutated nothing: the lock file's mtime and size before and after.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the startup output pasted with a peer live and again with none, showing the peer line present in the first and absent in the second, and UNKNOWN rendered distinctly from NONE.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the TWO-PROCESS demonstration, with one process genuinely holding a `driver.lock` and the second's actual behavior pasted per the chosen policy; plus the UNKNOWN case shown PROCEEDING with a warning rather than refusing; plus a no-peer start shown unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: the escape hatch exercised with a justification (start permitted, justification pasted from the durable run record) and without one (refused, message pasted).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: the structural test's output showing both hosts' guard resolving to the same object, plus a demonstration that the test FAILS if one host is pointed at a copy.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: the new test file GREEN after and RED before, the bare suite count line, and the dead-pid case demonstrated with a real leftover lock file showing NO refusal (so a crashed run cannot block the repository).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is human-approved before execution and is executed under the repository's standing agent execution contract: commit ONLY the declared `Scope-Paths` through `aw commit`, never `git add -A` and never push; paste ACTUAL runner output for every test claim; and do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete observed evidence. A worker-role lane may NOT perform the terminal transition (`AW-LIFECYCLE-ROLE-001`): the runner owns `aw ipd begin`/`aw ipd finalize`.

OQ-01 IS BLOCKING AND MUST BE ANSWERED BY THE MAINTAINER BEFORE E-03. An executor reaching E-03 without an answer must stop after E-02 (pure observability, safe to land alone) and record the stop, rather than choosing a concurrency policy on the maintainer's behalf. THE SPECIFIC HAZARD OF THIS PLAN is that a guard which refuses too eagerly makes the driver unstartable: a stale lock from a crashed run, or a platform where locks cannot be probed, must NEVER block a start, which is why those two cases are pinned in E-06 rather than left to judgement.
