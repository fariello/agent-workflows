# IPD: Port lane containment onto current main: one authoritative signal per instruction, enforced not requested

- Date: 2026-09-01
- Kind: child
- Concern: An isolated (lane) turn receives CONTRADICTORY instructions about where it may work, and the contradiction is emitted by the driver itself. The prompt says "Do NOT read or write the main checkout" and then hands the agent FIVE absolute main-checkout paths, declaring them "the only exceptions ... you write them exactly as given" (verbatim, `build_isolation_notice`, `oc_runipd.py:3765`; measured live in `run-20260901T042331Z-118022`, where the executor prompt mentions the main checkout path 7 times, only 2 of them inside the lane). Containment therefore rests on an agent resolving a self-contradiction correctly on every turn, which is a request, not a boundary; `host_sandbox_profile`'s own docstring concedes a same-user agent "cannot be cryptographically or filesystem-enforced from prompts, hooks, environment variables, or Python role checks alone". The measured harm already happened once (`3f5752bd`, 18 files committed into MAIN while the lane branch stayed at zero commits, inside run `run-20260831T153226Z-3424176`), and the mitigation shipped 36 minutes LATER (`ae1ae9b7`, 17:21:54Z vs the leak at 16:45:48Z), so the current defense has been exercised by exactly ONE subsequent run with committing agents.
- Scope: Eliminate the mixed signals by construction rather than by instruction: make every worker-facing path in an isolated prompt LANE-RELATIVE, harvest the worker's submissions back to the run directory so the driver's readers are unchanged, add the runner-supplied host permission denial and the driver-side turn bounds that make an unanswerable ask impossible to wait on, materialize required inputs into the lane by copy with a sealed manifest, give a genuinely missing input a bounded repair path instead of an escape hatch, and generalize the ALREADY-PROVEN `AW_EXECUTION_ROLE=worker` selector so containment has an enforcement layer that does not depend on prose. Does NOT relocate machine state out of the repo (wtiso Phase 4), does NOT unify the two host runners (`rununify`), does NOT build OS-level confinement (that is `fjs11i` plus research `q65sz3`), and does NOT change the lifecycle transaction.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/wtiso_gate.py, tests/test_lane_containment.py, tests/test_wtiso_adversarial.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: none
- From-Backlog: vqv9im
- Blocks-Release: next
- Status: to-review
- Set: lanecontain
- Order: 1
- Highest E allocated: 12
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: tch3bo

## Workflow history

- 2026-09-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored as the PORT that backlog `vqv9im` decided on, replacing the merge path that approved `6knsrx` assumed (`6knsrx` is now de-armed to `reviewed`, `cea13ac0`). Re-scoped from `qcqhj7` against current main rather than transcribed: E-11 is DROPPED as already-solved-differently, E-03/E-10 are narrowed to the deltas main lacks, and one new E-item (E-12) generalizes the worker-role selector that landed for `i452hf`. Every claim below was measured at HEAD `cea13ac0`, not inherited from the lane's text.
- 2026-09-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make an isolated turn's instructions SELF-CONSISTENT and its containment ENFORCED rather than requested.

Two outcomes, stated so they can be falsified. (1) SIGNAL PURITY: for an isolated turn, the emitted prompt contains ZERO absolute paths outside the lane worktree, so no sentence has to explain an exception and no agent has to adjudicate one; measured today MAIN emits 5 such paths, the lane design emits 0. (2) DEFENSE IN DEPTH: containment stops depending on the agent reading prose correctly, gaining a host-side permission denial, a driver-side deadline that fires regardless of what the host decides, and an execution-role selector that makes the driver-owned verbs refuse inside a lane.

The honest bound on what this achieves is stated up front because it shapes every design choice below: this plan does NOT make a determined same-user agent unable to leave its lane. It removes the CONTRADICTION that makes leaving look sanctioned, and it makes the accidental case fail loudly. Hard confinement is `fjs11i` plus research `q65sz3`, deliberately out of scope.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

READ THIS BEFORE E-01. The ordering below is deliberate and load-bearing: the prompt (E-01) and the harvest (E-02) MUST land together in one pass, because either alone is a regression. A lane-relative instruction without a harvest means an obedient worker writes `<lane>/.aw/lane/<run>/<id6>/submissions/outcome.json` while `reconcile_disposition` reads `<run_dir>/outcomes/<NN>-<id6>.json`; the outcome is never found, the turn scores from the empty-outcome fallback (the lane measured `('partial', None)`), and because `partial` is outside the `{executed, substantially-complete}` gate the item then silently never finalizes. That is a WORSE failure than today's contradiction, because it is invisible. Do not split E-01 from E-02.

### Task group 1: eliminate the mixed signals (the core of `vqv9im`)

- [ ] E-01 In BOTH drivers' `build_prompt`, make every worker-facing path LANE-RELATIVE for an isolated turn, and DELETE the exception clause that authorizes absolute paths. Port the lane's `LanePaths`/`lane_paths` value type (keyed by `run_id`/`id6` so a resumed run, a retry, and a co-resident lane cannot collide) and emit `Plan file at launch`, `External run directory`, `Decisions/questions register`, `Required JSON outcome`, and `Driver report` as paths relative to the lane root. Then REMOVE from `build_isolation_notice` the sentence "When a path below is given as an absolute path outside the lane, it is a DRIVER-OWNED control path ... those are the only exceptions and you write them exactly as given" (`oc_runipd.py:3795-3798`), because after this item there ARE no exceptions and a stale exception clause is itself a mixed signal. Keep the rest of the "Work here" block: it is the plain-language statement of the rule and it is main's own work, not the lane's.
  - Depends on: none
  - Expected outcome: for an isolated item, `build_prompt(...)` returns a string containing ZERO absolute paths outside the lane root (asserted by regex over the emitted text, not by eyeball), the lane-relative submission paths are present, and the exception sentence is gone. For a NON-isolated turn the prompt is byte-identical to today's.
  - Execution state: pending
- [ ] E-02 Port `harvest_lane_submissions` and wire it into BOTH drivers' `execute_item` IMMEDIATELY BEFORE `reconcile_disposition`, so the driver-side readers are untouched by E-01. Copy (never move) the lane's `outcome.json`, its report, and its decisions contribution back to the run directory at the exact paths `reconcile_disposition` already reads. The decisions register must be APPENDED to, never overwritten, because it is run-wide and shared by every item; clobbering it would erase sibling lanes' recorded decisions. A lane that wrote nothing must still reconcile to the honest empty-outcome fallback rather than error.
  - Depends on: E-01
  - Expected outcome: after an isolated turn whose worker wrote a lane-side outcome declaring `executed`, `reconcile_disposition` returns that disposition (NOT `('partial', None)`), and the run directory holds the harvested outcome at `<run_dir>/outcomes/<NN>-<id6>.json`. A second lane's decisions contribution does not remove the first's.
  - Execution state: pending
- [ ] E-03 Make the `--file` attachments lane-local for an isolated turn in BOTH drivers. MEASURED DELTA, so this is narrower than the lane's original E-02: main ALREADY passes a lane-local plan path (`oc_runipd.py:4346` receives the `resolve_plan_path(lane_root, ...)` result), but the runbook is still attached by its MAIN path (`argv.extend(["--file", state["runbook"]])`, `oc_runipd.py:4341`). Copy the runbook into the lane by value and attach the lane-local copy; reuse E-05's materializer rather than copying twice.
  - Depends on: E-02
  - Expected outcome: for an isolated turn, EVERY `--file` value in the constructed argv resolves inside the lane (`all(Path(p).resolve().is_relative_to(lane_root) for p in file_args)`), and at least two `--file` values were checked so the assertion provably covers both the runbook and the plan.
  - Execution state: pending

### Task group 2: make the boundary enforced, not requested

- [ ] E-04 Add the runner-supplied host permission policy for an unattended isolated turn: `external_directory: "deny"` and `question: "deny"`, injected via `OPENCODE_CONFIG_CONTENT` in the child env (never by editing repository config), plus a read-back that OBSERVES the effective policy and records it on the attempt. The read-back is not optional: opencode config precedence places managed sources ABOVE `OPENCODE_CONFIG_CONTENT`, so a run that merely SETS the variable can believe it is protected when it is not; record either the observed values or an explicit `effective_policy_unverified` marker with its reason. Extend the ONE child-env construction that `cdef9c90` already introduced (`child_env = pinned_child_env()` in `run_opencode`) rather than forking a second one. Antigravity takes its posture from argv rather than an opencode-style config document, so for `agy_runipd` this item adds only the env seam and records that no policy document applies.
  - Depends on: E-03
  - Expected outcome: the child env for an isolated `--auto` turn carries `OPENCODE_CONFIG_CONTENT` whose parsed JSON has `permission.external_directory == "deny"` and `permission.question == "deny"`, inherited `PATH` still present, and the attempt record carries the observed effective policy or the explicit unverified marker.
  - Execution state: pending
- [ ] E-05 Add the driver-side turn bounds that fire REGARDLESS of what the host decides, because E-04 is a host-side request and this is the layer that does not trust it: a seconds-scale permission deadline armed by a parsed permission-request event (including a NESTED child-session ask, which is the shape qyaime actually observed), and an absolute per-turn deadline that noise cannot extend. On expiry, reap through the ONE shared `runner_shutdown.clean_shutdown` (spec `c4gd2h` R5 forbids a second reaper; do NOT call `terminate_process` directly and do NOT add a bare kill) and record `failed-safely` with an `interrupt_reason` naming which bound fired, reusing the existing vocabulary rather than inventing fields.
  - Depends on: E-04
  - Expected outcome: a unit test feeding a synthetic unanswered permission event observes the process reaped within the permission-deadline window (not at the 600s stall bound), with disposition `failed-safely` and `interrupt_reason` in {`permission_deadline`, `absolute_deadline`, `stall_timeout`}, and the reap is attributable to `clean_shutdown`.
  - Execution state: pending
- [ ] E-06 Gate the no-progress watchdog reset on a MEANINGFUL event. This is the one defect in this plan that is LIVE ON MAIN TODAY, independent of the prompt work: the stream loop calls `watchdog.touch()` UNCONDITIONALLY on every line (`oc_runipd.py`, immediately after `statusline.touch("stdout")`), so a wedged-but-chatty turn resets the 600s bound indefinitely. Port `is_meaningful_event` and gate ONLY `watchdog.touch()` plus the new bounds' progress note behind it. THREE THINGS MUST NOT CHANGE, and each has a reason: `statusline.touch("stdout")` stays UNCONDITIONAL (a progress DISPLAY must refresh on every line; a display timer and a liveness bound are different consumers of one stream with opposite reset requirements); the `stallfp` subagent poller stays UNGATED (resolved in `6knsrx` OQ-03 on measured evidence - it already filters via `classify_progress`/`PROGRESS_MESSAGE_KINDS`, it counts only lines proven to belong to a child session of THIS turn, and applying `is_meaningful_event` to its plain-text log lines would be a category error that re-breaks the `kaga7s` keepalive); and the `runstop` levels 1-4, checkpoint observer, and force-stop machinery stay exactly as they are.
  - Depends on: E-05
  - Expected outcome: in both drivers' turn loops, `watchdog.touch()` is reachable only under `is_meaningful_event(line)` while `statusline.touch(...)` remains ungated; a test feeding only noise lines observes the watchdog FIRE at its timeout, and the same test with interleaved meaningful events observes it NOT fire.
  - Execution state: pending
- [ ] E-12 Generalize the `AW_EXECUTION_ROLE=worker` selector from a lifecycle-only guard into the shared containment signal, and IMPLEMENT the `wtiso_gate` predicates this plan owns. `cdef9c90` already proved this seam end to end for `i452hf`: the driver marks an isolated child, and `ipd_lifecycle` refuses `begin`/`finalize` with the deterministic `AW-LIFECYCLE-ROLE-001`. This item makes that the general mechanism by filling in the FOUR Phase-0 stubs that name `qcqhj7` as their owner and currently raise `NotImplementedError` by design so a premature caller breaks visibly rather than silently allowing: `check_permission_deadline`, `format_missing_input`, `parse_missing_input`, and `check_scope`. NOTE on `check_scope`, which is the least obvious of the four and was nearly missed at authoring: its docstring assigns the PURE PREDICATE to `qcqhj7` while `rchpms` (Phase 2) wires the hook, `aw lane status`, the driver, and finalize to it "so the rules cannot diverge". So this plan owns the FUNCTION BODY and its unit tests ONLY; it must NOT wire any caller to it, or it would take Phase 2's work and, worse, fork the very rule the split exists to keep single. Do NOT touch the stubs owned by `rchpms` (`check_lifecycle_role`, `check_hook_bypass`, `classify_retention`, `check_receipt`) or by `2c122z` (`check_protected_refs`); leave them raising.
  - Depends on: E-06
  - Expected outcome: the FOUR `qcqhj7`-owned predicates have real bodies with unit tests, the other FIVE still raise `_unimplemented` with their owning phase named, `check_scope` has no product caller wired to it (that is Phase 2's), and `wtiso_gate` is imported by the driver for the deadline check rather than remaining unwired.
  - Execution state: pending

### Task group 3: make "no absolute paths" survivable

- [ ] E-07 Add the lane input materializer: copy the plan/IPD snapshot and the runbook (and any explicitly referenced safe file) into the lane at lane-local paths, and seal a read-only `input-manifest.json` recording per entry the repo-relative path, class, `source_digest`, `materialization: "copy"`, and worker policy. COPY-ONLY is the point and must be asserted: a symlink or hard link back to the original checkout would reintroduce exactly the coupling the lane exists to remove.
  - Depends on: E-03
  - Expected outcome: after materializing a lane, the lane holds the IPD and runbook copies plus `input-manifest.json` whose every entry has `materialization == "copy"` and a non-empty `source_digest`; no manifest-listed lane path is a symlink; each listed file exists with a digest matching what was written.
  - Execution state: pending
- [ ] E-08 Add the `AW_MISSING_INPUT:<repo-relative-path>:<why>` contract and its COORDINATOR-side classifier, so a genuinely missing file becomes a bounded repair cycle instead of a reason to reach out of the lane. This is what makes E-01 survivable rather than merely strict. The classifier resolves the path in driver code only and REJECTS, in order: an absolute path or one escaping via `..`; a coordinator-owned surface (REUSE `worktree_lease.path_is_worker_forbidden` / `FORBIDDEN_WORKER_PATH_HINTS` so the reject set cannot drift from the lease's); a sibling lane or the worktrees root; machine-local state; a directory; and a path that does not exist. Otherwise it copies a digest-verified snapshot into the lane. It NEVER grants access to the live original checkout, and `live_grant` is structurally always False.
  - Depends on: E-07
  - Expected outcome: a test drives the classifier with (i) a safe missing repo-relative file and observes a digest-verified lane copy created with NO live grant emitted, and (ii) a forbidden path (control root, sibling lane) and observes a reject with no copy and no grant.
  - Execution state: pending
- [ ] E-09 Add the pre-launch clean-tracked-base guard: before an unattended isolated turn, refuse if the target checkout has dirty TRACKED paths, naming them, because a lane is created from `HEAD` and an uncommitted tracked edit is silently absent from it. Untracked files are deliberately EXCLUDED (a lane is made from a commit, so untracked main content was never "omitted" the way a tracked edit is, and refusing on untracked files would make an unattended run unstartable in any working checkout). REUSE the existing porcelain parser behind `dirty_tree_overlap` rather than writing a second one, and state in the code comment how this differs from it: `dirty_tree_overlap` answers an INTEGRATION-time question (does an incoming lane's changed set intersect dirty paths), this answers a PRE-LAUNCH question (is the whole tracked tree clean), so it is complementary, not duplicative.
  - Depends on: none
  - Expected outcome: with a dirty tracked file in the target checkout, an unattended isolated run is refused BEFORE any agent process is spawned (spawn patched and asserted never called), with a message naming the dirty tracked paths; with a clean tracked checkout the same path proceeds.
  - Execution state: pending
- [ ] E-10 Extend teardown to PRESERVE on ambiguity. MEASURED DELTA, narrower than the lane's original: main already emits a `worktree-preserved` event, so this item adds the INVENTORY that decides when to emit it. Enumerate the lane with `git status --porcelain --untracked-files=all --ignored=matching` so IGNORED files are seen too (the previous force-teardown destroyed them silently, and "ignored means disposable" is exactly the reasoning the research forbids), classify content the driver itself wrote under the lane control dir as discardable, and treat anything else - a dirty tracked file, an unknown untracked or ignored file, or an unimported submission - as UNKNOWN, which BLOCKS teardown.
  - Depends on: E-07
  - Expected outcome: a lane holding an unknown untracked file is NOT torn down (the directory still exists and a `worktree-preserved` event is recorded with the reason); a fully classified clean lane is torn down.
  - Execution state: pending

### Task group 4: prove the mixed signals are gone, adversarially

- [ ] E-11 Add `tests/test_lane_containment.py` as the SIGNAL-PURITY regression net, and flip the two `qcqhj7`-owned strict-xfail tripwires in `tests/test_wtiso_adversarial.py`. The new file must assert the property, not the wording: build a real isolated prompt from both drivers and assert by REGEX that no absolute path outside the lane root appears anywhere in it, so a future edit that reintroduces one fails even if it words the exception differently. Add the adversarial trio: an unanswerable permission ask is killed rather than awaited; a missing input yields a verified lane copy and never a live grant; an isolated prompt names no main-repo path. Then update `test_missing_input_driver_denial_pinned_absent` and `test_nested_permission_bounded_kill_pinned_absent`, which are `xfail(strict=True)` pinned ABSENT and will report `failed [XPASS(strict)]` the moment E-05/E-08 land: convert each into a real positive assertion. Do NOT touch the two pins owned by `rchpms`/`2c122z`.
  - Depends on: E-01, E-02, E-05, E-08
  - Expected outcome: `tests/test_lane_containment.py` passes with the regex purity assertion and the adversarial trio; the two `qcqhj7`-owned xfail pins are converted to positive tests; the other two pins still report `xfailed`; and the whole suite's `xfailed` count drops by exactly 2 with `failed == 0`.
  - Execution state: pending

## Project conventions discovered (Step 0)

All measured at HEAD `cea13ac0`. Line numbers move (this plan edits these very modules), so anchor on SYMBOL NAMES and re-verify with `grep -n`.

- THE TWO HOST DRIVERS ARE DELIBERATE NEAR-PARITY TWINS. `oc_runipd.py` and `agy_runipd.py` share function shapes (`build_prompt`, `run_opencode`/`run_agy_turn`, `execute_item`, the worktree block, `terminate_process`). Every change here MUST land in both or they drift on a containment rule. `cdef9c90` is the precedent: it added the worker-role marking to both twins symmetrically in one pass.
- THERE IS EXACTLY ONE REAPER, AND SPEC `c4gd2h` R5 FORBIDS A SECOND. `runner_shutdown.terminate_process` is the only implementation (`:126`); both drivers' `terminate_process` are thin DELEGATING wrappers (verified by AST during `zpbx7o`'s verification: `oc_runipd.py:3994 DELEGATES`, `agy_runipd.py:2580 DELEGATES`). `os.killpg` appears as a call exactly once (`runner_shutdown.py:158`). E-05 must route through `clean_shutdown`, never a bare kill.
- `wtiso_gate.py` IS A PHASE-0 SKELETON BUILT FOR EXACTLY THIS WORK. It declares nine predicates that raise a uniform `NotImplementedError` naming their owning phase, with the rationale stated in-module: "Failing loudly (rather than returning a permissive default) is the point: a caller wired up before its owning phase lands must break visibly, never silently allow." FOUR name `qcqhj7` (this plan): `check_permission_deadline`, `format_missing_input`, `parse_missing_input`, and `check_scope` - the last of which assigns only the PURE PREDICATE here, with its wiring explicitly reserved for `rchpms`. It is currently imported by NO product module.
- `tests/test_wtiso_adversarial.py` IS A TRIPWIRE NET, and its own docstring explains the discipline: each guard is split into a passing half and an `xfail(strict=True)` half pinned ABSENT, because putting both in one function is "a greenwash hole". Its stated whole-suite invariant is `failed == 0 AND xfailed > 0`; `xfailed == 0` would mean the pins vanished. Measured now: `5 passed, 4 xfailed` for this file alone (`15 passed, 4 xfailed` across the three `wtiso` test files).
- WHICH PINS THIS PLAN FLIPS, checked per pin rather than assumed, because the count drives V-11's arithmetic. FOUR strict pins exist (a bare `grep -c 'xfail('` returns 6 and is WRONG: two of those hits are the docstring explaining the convention). By `reason=`: `test_missing_input_driver_denial_pinned_absent` ("lands in qcqhj7/Phase 1") and `test_nested_permission_bounded_kill_pinned_absent` ("permission-event deadline lands in qcqhj7/Phase 1") are THIS plan's and must flip. `test_forgetful_agent_driver_report_pinned_absent` ("lands in rchpms/Phase 2") is not. `test_hook_bypass_driver_rejection_pinned_absent` reads "qcqhj7/rchpms" and looks ambiguous, but its body calls `wtiso_gate.check_hook_bypass`, whose stub names `rchpms` as owner, so it must STAY pinned; leaving it is correct, not an oversight. Net: exactly 2 flip.
- THE CHILD ENV IS ALREADY EXPLICIT, AND THERE MUST STAY ONE CONSTRUCTION. Before `cdef9c90` the child inherited the environment implicitly (no `env` key at all). It now builds `child_env = pinned_child_env()` and sets/strips `AW_EXECUTION_ROLE`. E-04 EXTENDS that single construction; it must not fork a second one, and it must preserve the two-part import pin (`pinned_child_env` selects, `pinned_module_argv` suppresses).
- ISOLATION IS THE DEFAULT, so every change here is on the hot path: `isolate_worktree` defaults `True` (`oc_runipd.py:3001`, `:4820`).
- MAIN ALREADY SOLVED THE E-11 SEQUENCING PROBLEM DIFFERENTLY, and the difference matters. The lane's plan assumed `build_prompt` had to be MOVED after allocation. Main instead builds the prompt twice: a pre-lane draft, then a REBUILD after allocation with `lane_root` and the lane's plan path, re-writing the prompt file and re-taking its digest so "the digest ... describe[s] the prompt the agent actually received, not the pre-lane draft it replaced". That is a valid alternative and it is main's own work; this plan builds ON it rather than reverting to the lane's approach.
- THE SUITE MUST BE RUN BARE, and `make test-all` separately. `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`. CRITICAL LESSON from `mzy2so` (found during `zpbx7o`'s verification): a bare run DESELECTS the `slow` tests, so it reported `3996 passed` GREEN while a level-2 wind-down test was failing under `make test-all`. Any validation item here that claims "suite green" must say WHICH invocation it means.
- VALIDATE IN THE PRIMARY CHECKOUT. About 15 `test_run_viewer.py` tests fail in ANY lane worktree or fresh clone and pass in the primary tree; that is backlog `dh0uno`, not a regression.

## Findings

| id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **The driver emits the contradiction itself.** An isolated prompt says "Do NOT read or write the main checkout, and do NOT climb out with a relative path" and then, nine lines later, "When a path below is given as an absolute path outside the lane, it is a DRIVER-OWNED control path ... those are the only exceptions and you write them exactly as given." Containment therefore requires the agent to resolve a self-contradiction correctly every turn. | `build_isolation_notice`, `oc_runipd.py:3765-3801`; read verbatim from the prompt an agent actually received, `.aw/records/runs/run-20260901T042331Z-118022/prompts/01-m73aet-exec-attempt-1.md:13-16`. |
| F-2 | **Five absolute out-of-lane paths are emitted; the lane design emits zero.** Built a real isolated prompt from each side. MAIN: `<repo>/.aw/records/plans/pending/x.ipd.md`, `<repo>/.aw/records/runs/run-x`, `.../decisions-and-questions.md`, `.../execution-report.md`, `.../outcomes/01-aaaaaa.json`. LANE: none, of any kind. In the live prompt the main-checkout path appears 7 times, only 2 of them inside the lane. | `build_prompt(...)` invoked directly on both sides with a synthetic isolated item; regex over the returned text. Live: `grep -c` over the run's executor prompt. |
| F-3 | **The harm is measured, and the mitigation postdates it by 36 minutes, so it is barely tested.** The leak `3f5752bd` committed 18 files into MAIN at 16:45:48Z, inside run `run-20260831T153226Z-3424176`, while the lane branch stayed at zero commits. `ae1ae9b7`, which added the isolation notice, landed at 17:21:54Z. Of 21 isolated runs in the tree, 20 predate the notice; exactly ONE post-notice run had committing agents (`run-20260901T042331Z-118022`, 2 items). Its two items did stay in their lanes (both commits are off main's first-parent line, arriving only via the hand-merges `35525850`/`675fcfbe`) - one favorable observation, not a demonstration. | `git log -1 --format=%ci` on both commits, normalized to UTC (the raw timestamps are in mixed zones, which inverted the ordering on a first careless read); `git rev-list --first-parent main | grep -c <sha>` -> 0 for the agent commits; per-run `worktree-allocated` census over `.aw/records/runs/*/events.jsonl`. |
| F-4 | **The qyaime permission deadlock did NOT reproduce on the current host, so this plan is HARDENING against a latent hazard, not fixing a live outage.** The last real isolated run recorded ZERO permission/stall events and both agents successfully WROTE the out-of-lane absolute paths. On opencode `1.18.25` with `--auto`, and with no `permission` block in the user config, the host evidently permits the access rather than gating it. Stated plainly because it sets the priority honestly: if the host's default ever tightens, the same five paths become a hang instead of a leak. | `grep -c 'permission\|stall_timeout\|external_directory'` over the run's `events.jsonl` -> 0; both `outcomes/*.json` and `decisions-and-questions.md` exist under the MAIN run dir with run-time mtimes; `python3 -c` load of `~/.config/opencode/opencode.json` shows `permission` ABSENT. |
| F-5 | **ONE defect in this plan is live on main right now, independent of the prompt work.** `watchdog.touch()` is called unconditionally on every stream line, immediately after `statusline.touch("stdout")`, so a wedged-but-chatty turn resets the 600s no-progress bound indefinitely. `is_meaningful_event`, `detect_permission_request`, and `TurnBounds` are all ABSENT from main. This is E-06 and it is the cheapest real win in the plan. | Read of the `for line in process.stdout:` loop in `run_opencode`; `hasattr(oc_runipd, ...)` -> False for all three symbols. |
| F-6 | **The `AW_EXECUTION_ROLE=worker` seam is already proven end to end, which is why E-12 generalizes it rather than inventing a mechanism.** `cdef9c90` had the driver mark an isolated child and `ipd_lifecycle` refuse `begin`/`finalize` with `AW-LIFECYCLE-ROLE-001`; reproduced live during that work (the agent's in-lane finalize was refused and the driver's own then succeeded). Its honest limit is recorded in-module: an environment SELECTOR, not a hardened boundary, since a same-user worker can unset it. | `cdef9c90`; `grep -n EXECUTION_ROLE_ENV agent_workflows/oc_runipd.py` -> 2 sites; the `ipd_lifecycle` refusal path. |
| F-7 | **A git hook in the common dir FIRES inside every lane, so there is a real enforcement point that is not prose.** A linked worktree resolves `--git-path hooks` to the MAIN `.git/hooks`, and a `pre-commit` hook is installed there today. Recorded as available leverage for a FOLLOW-UP (the `wjl471` commit-guard family), deliberately NOT used by this plan: a hook sees the staged set but not the INTENT, so it cannot distinguish `git add -A` from an explicit path list. | `git -C .aw/worktrees/qcqhj7 rev-parse --git-path hooks` -> `<repo>/.git/hooks`; `ls .git/hooks/pre-commit` exists. |
| F-8 | **Prose alone cannot be the boundary, by this repository's own admission.** `host_sandbox_profile`'s docstring states a same-user agent with shell access "cannot be cryptographically or filesystem-enforced from prompts, hooks, environment variables, or Python role checks alone". This is the argument for E-04/E-05/E-12 as layers rather than for more emphatic wording, and the argument for stating this plan's bound honestly in the Goal. | `agent_workflows/host_sandbox_profile.py` docstring, quoted in `build_isolation_notice`'s own comment at `oc_runipd.py:3774-3779`. |
| F-9 | **The lane's payload is self-contained and its size is known.** The `wtiso-02 (qcqhj7) Phase 1` section on `aw/lane/qcqhj7` is ~516 lines and includes `LanePaths`/`lane_paths` (8 refs), `lane_contract_text` (3), `harvest_lane_submissions` (3), `materialize_lane_inputs` (2), `classify_missing_input` (1), `inventory_lane` (2), and `MISSING_INPUT_PREFIX` (3). This is what "port" means concretely. | `awk` extraction of the section on the lane branch; per-symbol `grep -c`. |
| F-10 | **Merging the lane branch is NOT an option, which is why this is a port.** The lane predates a large amount of main-side work and does not contain it: `runner_stop` 73 references on main vs 0 on the lane, plus `stall_progress` 3/0, `Statusline` 3/0, `_apply_execution_profile` 3/0, `build_isolation_notice` 2/0. A wholesale merge would destroy the entire `runstop` graceful-quit Set that was just verified and finalized in `zpbx7o`. | Per-symbol `grep -c` on `main` vs `git show aw/lane/qcqhj7:agent_workflows/oc_runipd.py`; the `wtiso` Set's terminal states. |
| F-11 | **Two of `rchpms`'s payload commits already landed, so a port must not re-land them.** `cdef9c90` took the frozen-region receipt digest (`1c751814`) and the worker-role authority rule from `cfe446d8` to fix `i452hf`. The rest of `rchpms` (`derive_lane_outcome`, `harvest_lane_submissions`, five-way retention, the `aw lane status`/`note` surface) is still lane-only; `aw lane` is not a registered command. | `cdef9c90`; `git log main..aw/lane/rchpms`; `aw lane --help` -> `invalid choice: 'lane'`. |
| F-12 | **The prompt carries a SECOND mixed signal that this plan deliberately does not fix, recorded so it is not mistaken for an oversight.** The executor prompt mentions finalize only negatively ("If the IPD cannot validly finalize, preserve partial work"), while the repository contract the agent correctly reads tells it `aw ipd finalize` IS the terminal transition (`.aw/records/plans/README.md:98`). That mismatch is what produced `i452hf`, and it is now handled by ENFORCEMENT (`AW-LIFECYCLE-ROLE-001` refuses the verb in a lane) rather than by prompt wording. E-12 extends that same enforcement-over-wording approach. | The live executor prompt; `.aw/records/plans/README.md:98`; `cdef9c90`. |

## Proposed changes (ordered, validatable)

1. Make the isolated prompt lane-relative and DELETE the exception clause, in both drivers (E-01).
2. Harvest the worker's submissions back to the run directory in the same pass, so the driver's readers are unchanged and no obedient worker's outcome is lost (E-02).
3. Attach the runbook from the lane copy, closing the last main-path `--file` (E-03).
4. Deny `external_directory`/`question` for an unattended isolated turn and OBSERVE the effective policy rather than assuming it (E-04).
5. Add the permission and absolute turn deadlines, reaping through the one shared routine (E-05).
6. Gate the no-progress reset on a meaningful event, leaving the statusline, the subagent poller, and all runstop machinery untouched (E-06).
7. Generalize the worker-role selector and implement the three `qcqhj7`-owned `wtiso_gate` predicates (E-12).
8. Materialize lane inputs by copy with a sealed manifest (E-07).
9. Add the `AW_MISSING_INPUT` repair contract with a coordinator-side classifier that never grants live access (E-08).
10. Refuse to launch an unattended isolated turn from a dirty tracked base (E-09).
11. Inventory a lane before teardown and preserve on anything unknown (E-10).
12. Add the signal-purity regression net and flip the two `qcqhj7`-owned tripwires (E-11).

## Deferred / out of scope (with reason)

- OS-LEVEL CONFINEMENT. Landlock/sandbox enforcement is `fjs11i` (the shipped hardened profile is live dead code: `options["execution_profile"]` is read once, set never, with no CLI flag) plus research `q65sz3`. Out of scope because it is Linux-only against a macOS-100%-MUST platform bar, and because it will refuse loudly until `dh0uno` lands.
- `dh0uno` (inner `aw` resolving state against the lane worktree). Fixed by the unmerged `7p9n2v`; a separate defect. This plan neither fixes nor depends on it.
- MACHINE-STATE RELOCATION out of the repo: wtiso Phase 4 (`58ha43`).
- RUNNER UNIFICATION: `rununify` (`5e4sb6`). This plan deliberately edits BOTH twins symmetrically instead of unifying them, because unification is a separate, larger decision whose numbers have rotted (measured 6601/4790 lines and 58 drifted symbols).
- THE COMMIT GUARD (`wjl471`) and the four unwired gates. F-7 records that a common-dir hook fires inside every lane, which is real leverage, but a hook cannot see INTENT (it cannot distinguish `git add -A` from an explicit path list), so it needs its own design.
- THE REMAINING `rchpms` PAYLOAD (`derive_lane_outcome`, five-way retention, `aw lane status`/`note`). Still lane-only per F-11; belongs to a Phase-2 successor, not here.
- REWORDING THE PROMPT'S FINALIZE GUIDANCE (F-12). Handled by enforcement instead; a wording change would re-introduce the mixed-signal pattern this plan exists to remove.

## Scope check

- Over-scope: none. Every E-item is either a `vqv9im` payload item or the one live defect (E-06) in the same code path.
- Under-scope, DELIBERATE AND NAMED: this plan does not make containment unbypassable. A same-user agent can unset `AW_EXECUTION_ROLE`, and F-8 records the repository's own admission that prompts, hooks, env vars, and role checks cannot enforce a boundary alone. What it does is remove the CONTRADICTION (E-01), make the accidental case fail loudly (E-04/E-05/E-06/E-12), and keep the honest escape hatch bounded (E-08). Hard enforcement is deferred above, with owners.
- Under-scope, ACCEPTED: `agy_runipd` gets the env seam and the bounds but no policy DOCUMENT in E-04, because Antigravity takes its permission posture from argv rather than an opencode-style config. Recorded rather than silently skipped.

## Required tests / validation

Run the suite BARE in the PRIMARY checkout (`python3 -m pytest`) AND run `make test-all` separately. Both are required, and the reason is a measured lesson rather than ceremony: during `zpbx7o`'s verification a bare run reported `3996 passed` GREEN while `make test-all` was failing a level-2 wind-down test, because the bare run's configured `-m 'not slow'` deselects it (`mzy2so`).

Baselines MEASURED at HEAD `cea13ac0`, immediately before authoring:

```text
python3 -m pytest      -> 3996 passed, 3 skipped, 4 xfailed
make test-all          -> 4 failed, 4394 passed, 3 skipped, 4 xfailed
```

The 4 `make test-all` failures are PRE-EXISTING CLI-surface declaration checks (`test_zero_undeclared_parser_leaves` reports 65 undeclared parser leaves, plus three siblings), reproduced at `5e5da9a0` and probably owned by `0soncw`. They must not get worse and are not this plan's to fix. Any NEW failure is a STOP.

The `xfailed` count must DROP BY EXACTLY 2 (the two `qcqhj7`-owned pins E-11 converts) and `failed` must stay 0. An `xfailed` of 4 after this plan means E-11 did not flip them; an `xfailed` of 0 means the remaining pins vanished, which is its own bug.

## Spec / documentation sync

- `.aw/records/specs/` needs no new spec: the design is already specified by research `x03wgn` (Sections 4, 6 Layers 1 and 6, 2, 8 Phase 1) and the decision is recorded on backlog `vqv9im`.
- The `wtiso_gate` module docstring must be updated by E-12 to say which three predicates are now REAL and which six still raise, so the skeleton does not lie about its own state.
- No user-facing doc changes: this plan changes no public command surface. If E-12's work makes `aw lane` desirable, that is `rchpms` successor territory (F-11), not here.

## Open questions

### OQ-01: Should the driver's control paths move INSIDE the lane, or stay outside and be harvested?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY DESIGN, harvest (the lane's approach), and the alternative is recorded so it is not silently re-litigated. The worker writes lane-relative submission paths and the DRIVER copies them out afterwards (E-02), rather than the driver's run directory being relocated into the lane. Two reasons from repository evidence. (1) The run directory is RUN-WIDE and shared by every item: `decisions-and-questions.md` is appended to by all lanes, so relocating it into one lane would either fork it per item or make one lane authoritative over its siblings. (2) The driver's readers (`reconcile_disposition`, the verifier turn, `aw runs`) already resolve `<run_dir>/outcomes/<NN>-<id6>.json`; harvesting keeps every one of them untouched, which is why E-02 is a copy-back rather than a reader migration. The cost is that the copy MUST happen before `reconcile_disposition` or the outcome is silently missed, which is why E-01 and E-02 are explicitly forbidden from being split.

### OQ-02: Does denying `external_directory` break anything today, given the host currently permits the access?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED ON MEASUREMENT, and this is exactly why E-01 must land WITH E-04 rather than after it. Today the five out-of-lane paths WORK (F-4: the last real run wrote all of them with zero permission events), so denying `external_directory` BEFORE the prompt stops naming them would convert a working run into a hard failure. After E-01 the prompt names no such path, so the denial has nothing legitimate left to block and becomes a pure backstop. The ordering in Task groups 1 then 2 encodes this. If an executor is tempted to land E-04 early as "the cheap safety win", that is the one sequencing mistake that will break a working runner: do not.

### OQ-03: Should this plan also gate the subagent progress poller behind `is_meaningful_event`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, resolved by carrying forward `6knsrx` OQ-03's measured answer rather than re-deriving it. The poller ALREADY filters: `stall_progress.classify_progress` counts only `PROGRESS_MESSAGE_KINDS` agent-loop lines and documents in-module that housekeeping lines return `None` "so a permission-deadlocked (but still chatty) process is NOT mistaken for a progressing one", which is precisely the property this plan wants. It also counts only lines PROVEN to belong to a child session of this turn. And applying `is_meaningful_event` to it would be a CATEGORY ERROR: that predicate parses each line as a JSON event and returns False on anything unparseable, whereas the poller reads opencode's plain-text log, so it would reject essentially every poller line and re-break the `kaga7s` sub-task keepalive. HONEST RESIDUAL RISK, recorded rather than hidden: if a stuck turn's only output is agent-loop-shaped log lines from a still-live child, the poller can still hold the turn open. By the poller's own definition that child IS progressing; if it ever proves a real failure mode it needs its own plan and a log-line-specific notion of progress, NOT a reuse of `is_meaningful_event`.

### OQ-04: Is `AW_EXECUTION_ROLE` the right carrier for general containment, given an agent can unset it?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES for this plan's threat model, with the limit stated in the artifact rather than oversold. The maintainer's model is ACCIDENT PREVENTION, not adversarial defense: agents act on trained reflex (a solo-repo agent is strongly trained that `git add -A` is correct), so a guard that refuses and names the correct alternative catches the realistic case even though a determined process could bypass it. Bypassability is therefore a FEATURE against accidents, and this is the same reasoning the maintainer applied to `mjx7ne` OQ-03 on 2026-09-01. The seam is also already PROVEN rather than speculative (F-6): `cdef9c90` used it to stop the exact double-finalize that stranded a real run. What would be WRONG is to let it read as a boundary: E-12 must carry the honest limit in the code comment, as `cdef9c90` already does.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the ACTUAL emitted prompt for an isolated turn from BOTH drivers, plus the output of a regex scan proving ZERO absolute paths outside the lane root appear in it (state the regex used; a visual scan does NOT satisfy this item). Paste a `grep` showing the exception sentence ("those are the only exceptions") is GONE from `build_isolation_notice`. Paste a byte-for-byte comparison proving the NON-isolated prompt is unchanged (e.g. a digest of the pre-change and post-change output for the same non-isolated inputs). A test that asserts specific WORDING instead of the absence PROPERTY does not satisfy this item, because a reworded exception must also fail.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a test run showing that after an isolated turn whose worker wrote a lane-side outcome declaring `executed`, `reconcile_disposition` returns that disposition and NOT `('partial', None)`. Paste the harvested file's path under `<run_dir>/outcomes/`. Separately paste evidence that a SECOND lane's decisions contribution does not remove the first's (append, not overwrite), and that a lane which wrote NOTHING still reconciles to the empty-outcome fallback without raising. State explicitly that the harvest call site is BEFORE `reconcile_disposition` in `execute_item`, with the source order shown.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the constructed argv for an isolated turn and an assertion over ALL `--file` values showing every one resolves inside the lane, with `len(file_args) >= 2` so the check provably covers both the runbook and the plan. Inspecting a single `--file` value does NOT satisfy this item.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the decoded child `OPENCODE_CONFIG_CONTENT` for an isolated `--auto` turn showing `permission.external_directory == "deny"` and `permission.question == "deny"`, plus proof inherited `PATH` survives and that the runner's import pin is intact (`AW_PIN_KEEP_ROOT` present). Paste the attempt record's observed effective policy OR its explicit `effective_policy_unverified` marker with the reason, and state the opencode version measured against. A run that neither observes the policy nor records the marker FAILS this item, because it would leave the run believing it is protected when a higher-precedence managed config may have overridden the deny.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste a test in which a synthetic UNANSWERED permission event (including the nested child-session shape) causes the process to be reaped within the permission-deadline window - demonstrably NOT at the 600s stall bound - with the recorded attempt showing disposition `failed-safely` and `interrupt_reason` naming which bound fired. Also paste evidence the reap went through `runner_shutdown.clean_shutdown` and that no second reaper or bare kill was introduced (an AST or import check, not a text grep, since the test file itself contains the symbols).
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the resolved turn loop from BOTH drivers showing `watchdog.touch()` indented under `if is_meaningful_event(...)` while `statusline.touch(...)` remains ungated. Paste a test in which a stream of ONLY noise lines lets the watchdog FIRE at its timeout, and the same stream with interleaved meaningful events does NOT. Paste proof the `stallfp` poller callback is UNCHANGED (a diff of that function showing no edit) and that the `runstop` machinery still passes: `python3 -m pytest tests/test_runner_stop.py tests/test_runner_stop_levels12.py tests/test_runner_stop_level3.py tests/test_runner_stop_level4.py tests/test_runner_stop_triggers.py tests/test_runner_shutdown.py -m ''` with its full summary line.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the materialized lane listing plus the `input-manifest.json` contents, showing every entry has `materialization == "copy"` and a non-empty `source_digest`, and paste an assertion that NO manifest-listed lane path is a symlink (`os.path.islink(p) is False` for all). Paste a digest comparison proving the lane copy matches the source bytes.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: paste both halves. (i) A SAFE missing repo-relative file drives the classifier and a digest-verified lane copy is created with NO live grant emitted (`live_grant is False` asserted). (ii) A FORBIDDEN path (control root and a sibling lane, at minimum) returns reject with no copy and no grant. Paste proof the reject set is the REUSED `worktree_lease.path_is_worker_forbidden` rather than a second copy of the rules (show the call, not a duplicated list).
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: paste a test where a dirty TRACKED file causes the unattended isolated run to be refused BEFORE any agent process is spawned (spawn patched and asserted never called, or the raised error shown), with the message naming the dirty tracked paths; plus the companion clean-tree case proceeding. Paste evidence that an UNTRACKED file does NOT trigger the refusal, since that exclusion is deliberate. Paste proof the porcelain parsing REUSES the existing helper rather than a second parser.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: paste a test where a lane holding an unknown UNTRACKED file is NOT torn down (directory still present) and a `worktree-preserved` event is recorded naming the reason; plus a companion fully-classified clean lane that IS torn down. Paste evidence that IGNORED files are seen by the inventory (the enumeration includes `--ignored=matching`), since silently discarding ignored content is the specific failure this item exists to prevent.
  - Observed evidence:
  - Result: pending
- [ ] V-11 validates E-11
  - Required evidence: paste `python3 -m pytest tests/test_lane_containment.py -m ''` with its full summary, showing the regex purity assertion and the adversarial trio passing. Paste `python3 -m pytest tests/test_wtiso_adversarial.py -m ''` showing the two `qcqhj7`-owned pins now PASS as positive tests while the two owned by `rchpms`/`2c122z` still report `xfailed`, i.e. the file's own stated invariant `failed == 0 AND xfailed > 0` still holds at `xfailed == 2`. Then paste BOTH whole-suite runs with their summary lines: bare `python3 -m pytest` AND `make test-all`, reconciled against the baselines in Required tests (`3996 passed, 4 xfailed` and `4 failed, 4394 passed, 4 xfailed`), with the total `xfailed` down by exactly 2, `failed` unchanged at 4 for `make test-all`, and every other delta explained against a named E-item. An unexplained failure means `Result: pending`, never a pass.
  - Observed evidence:
  - Result: pending
- [ ] V-12 validates E-12
  - Required evidence: paste unit-test output for the FOUR now-real `wtiso_gate` predicates (`check_permission_deadline`, `format_missing_input`, `parse_missing_input`, `check_scope`), and paste proof the OTHER FIVE still raise `NotImplementedError` naming their owning phase (call each and show the message). Paste proof that NO product module calls `check_scope` yet, since wiring it is Phase 2's work and doing it here would fork the shared rule, so the skeleton's fail-loud discipline is intact and no stub was silently made permissive. Paste the driver import showing `wtiso_gate` is now actually CONSUMED rather than unwired. Paste the updated module docstring stating which predicates are real. Paste the code comment carrying the honest limit that `AW_EXECUTION_ROLE` is an environment selector and not a hardened boundary.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: 12 E-leaves in 4 task groups, above the 18-leaf threshold on neither count but stated as an exception because the COUNT understates the coupling. These items are one indivisible change to a single failure surface: the prompt (E-01) and the harvest (E-02) are a matched pair that is a REGRESSION if split (a lane-relative instruction whose outcome nobody collects scores `partial` and silently never finalizes); the denial (E-04) is unsafe BEFORE the prompt stops naming the paths it denies (OQ-02); and the missing-input contract (E-08) is what makes "no absolute paths" survivable rather than merely strict. Splitting this into smaller plans would either ship a half-contained lane or force two plans to coordinate inside one uncommittable intermediate state. E-06 and E-09 are the two genuinely separable items: E-06 is the live defect and could ship alone if the maintainer wants the cheap win first; E-09 has `Depends on: none` for the same reason.

EXECUTION ORDER IS NOT NEGOTIABLE FOR TWO PAIRS, and both are recorded in OQs rather than left to judgment: E-01 with E-02 (never split), and E-01 BEFORE E-04 (denying `external_directory` while the prompt still names out-of-lane paths converts a working run into a hard failure, per F-4 and OQ-02).

Execution contract: commit ONLY files this plan changed, path-scoped, and never push. Other agents and runs are ACTIVE in this shared checkout, so before every commit verify the staged set with `git diff --cached --name-only` and `git restore --staged` anything not yours. RE-VERIFY AFTER ANY FAILED OR HOOK-INTERRUPTED COMMIT: observed twice on 2026-09-01, a `pre-commit` stash/restore split a `git mv` so the copy committed while the deletion stayed staged, leaving one record in two directories. Do not use `--no-verify` except for the `gjadwm` executed-transition false positive on a lane merge, and state the reason in the commit message if so.

Prose is never evidence. Every `V-*` above must carry the ACTUAL pasted stdout/stderr and exit code of the named command, run in this repo at execution time. "Tests pass", "verified", and "should work" are validation failures. Each of the three mandatory adversarial guards (V-05 unanswerable-prompt-killed, V-08 missing-input-safe-copy-not-live-grant, V-01 no-out-of-lane-path-in-prompt) must show pasted passing output before this plan may move.

Post-gate lifecycle: on completion run `aw ipd lint --phase pre-transition`, then move this plan to `.aw/records/plans/executed/` with `- Status: executed` via `aw ipd finalize`, never by hand. Do NOT mark it executed unless validation actually passed, and do not claim `xfailed` dropped by 2 without pasting the count.
