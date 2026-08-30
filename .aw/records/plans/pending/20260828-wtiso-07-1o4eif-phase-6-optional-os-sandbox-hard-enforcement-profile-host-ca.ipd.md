# IPD: Phase 6: optional OS-sandbox hard-enforcement profile (host capability contract, read-only git-common-dir, driver-owned git mutation, read-only discovery then write execution)

- Date: 2026-08-28
- Kind: child
- Concern: The operational-default profile shipped by wtiso-01..05 makes a FORGETFUL agent safe by removing voluntary tool use from the correctness path (driver-owned lifecycle, out-of-repo control state, deny-by-default external access, post-hoc detection of protected-ref mutation). It is explicitly NOT a security boundary against a MALICIOUS same-user worker with arbitrary shell access: x03wgn Section 1 ("A same-user process with arbitrary shell access cannot be cryptographically or filesystem-enforced from prompts, hooks, environment variables, or Python role checks alone.") and Section 7 (hazard row "Malicious same-user worker rewrites control root ... Explicitly outside default trust guarantee"). Today `run_opencode` launches the worker with the lane worktree as cwd (`agent_workflows/oc_runipd.py:1753`, `--dir agent_dir` at `:1713`) and only `start_new_session=True` for process-group reaping (`:1760`), with NO filesystem write boundary: the worker can write the control root, the main worktree, a sibling lane, or - because a linked worktree's `.git` file points into the shared common dir (x03wgn Section 4) - mutate shared refs/hooks/config even without touching main working files. This phase adds an OPTIONAL hardened profile that turns "driver is the only writer of anything outside the lane" from a reliable operational rule into an OS-enforced guarantee, and FAILS CLOSED rather than silently degrading when hard mode is requested on a host that cannot provide it.
- Scope: Implement x03wgn Section 8 "Phase 6" (optional hard enforcement and host optimization) faithful to Section 1 ("Two enforcement profiles" -> hardened), Section 4 ("Container or OS sandbox" incl. the read-only git-common-dir subtlety), and Section 6 Layer 4 (the host capability contract + read-only discovery then write execution). Add: (1) a typed host capability contract; (2) an OS-sandbox execution profile with explicit writable roots (lane worktree + lane scratch), read-only toolchain, and INACCESSIBLE control root / main worktree / sibling lanes / integration candidate / credentials; (3) a read-only git-common-dir with the DRIVER owning all git mutation (add/commit/refs/hooks); (4) an optional read-only discovery phase then write execution when a true before-edit barrier is required; (5) fail-closed dispatch when hard mode is requested but unavailable. Start on ONE platform, publish guarantees. This phase authors NO change to the default profile's behavior; it is additive and gated behind an explicit opt-in.
- Scope-Paths: agent_workflows/host_sandbox_profile.py, agent_workflows/oc_runipd.py, agent_workflows/host_adapters.py, tests/test_host_sandbox_profile.py
- Item-Dependencies: executed:2c122z
- Status: approved
- Set: wtiso
- Order: 7
- Highest E allocated: 10
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 1o4eif
- Approval: 2026-08-29, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 /plan-review (OpenCode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. Found a FAIL-OPEN capability probe (PR-001, blocker): E-02 would have decided `supports_os_sandbox` from `sys.platform` plus sysctls/binary presence, which MEASURABLY lies. On the review host `unprivileged_userns_clone=1`, `max_user_namespaces=514277`, and BOTH `/usr/bin/unshare` and `/usr/bin/bwrap` are installed - every signal says "sandbox available" - yet an actual attempt FAILS: `unshare -Umr true` returns `Operation not permitted` writing `/proc/self/uid_map` and `bwrap` reports `setting up uid map: Permission denied` (the host is itself inside a namespace with `uid_map` `0 0 4294967295`). An inspection-based probe would therefore report True and `select_execution_profile` would GRANT hard mode on a host that cannot enforce it - silent degradation in the FAIL-OPEN direction, the exact outcome x03wgn Section 8 Phase 6.3 forbids. E-02 now requires the probe to EXECUTE a minimal jail in a subprocess, treat any nonzero/exception/timeout as False, cache per process, and back `_linux_userns_available()` with the SAME probe so tests and capability reports cannot disagree; V-02 now demands attempt-vs-report agreement plus proof the probe is not sysctl-only. Closed a SKIP-AS-PASS hole (PR-003): V-08/V-09 accepted `1 skipped` as satisfying evidence, so the phase's two flagship OS-denial guarantees could be marked verified without ever executing - on this very host they WILL skip. Both now state that a skip requires `Result: pending`, the probe output showing why, and the guarantee recorded UNVERIFIED; only pasted `1 passed` from a named userns-capable host may pass, and a `1 passed` on a non-sandboxing host is itself a failure signal. Added a matching honest-closure rule to the gate: do not move this plan to `executed/` claiming OS-denial guarantees that were skipped - run it on a capable host or leave it parked per orchestrator OQ-01. Also: hardened E-08/E-09's skipif to share the executed probe (PR-002); removed the self-referential Scope-Paths entry and added the finalize-owns-the-plan-file note (PR-004), matching every executed plan and the Set's other children; de-duplicated V-06 vs V-10, which named the SAME test so one paste could satisfy both - V-06 now exercises all three branches of `select_execution_profile` directly while V-10 validates the test artifact + published docstring, and repaired E-10's stray half-sentence that simultaneously ordered and disclaimed a walkthrough (PR-005); corrected the ~10 drifted launch-seam citations (`run_opencode` 1606->1679, `--dir` 1640->1713, `cwd` 1680->1753, `start_new_session` 1687->1760, `Popen` 1692->1765, `terminate_process` 1559->1632/`killpg` 1570->1643) with a citation-basis note (PR-006). VERIFIED ACCURATE (no finding): all `worktree_lease.py` citations (`:32/:70/:199/:214`) and `project_registry.py` (`:182/:190`) are exact; `host_adapters.py` and `host_capability_registry.py` exist as described, and the plan correctly declines to overload the latter (it is a skill-probe registry, a different concern). The core design premise is sound: the default profile genuinely has NO filesystem write boundary (`start_new_session=True` exists only for `killpg` reaping), so an OS-enforced profile is the right complement to the policy-level `FORBIDDEN_WORKER_PATH_HINTS` fencing.
- 2026-08-29 reviewed (aw set): status set to reviewed
- 2026-08-29 to-review (aw set): status set to to-review

- 2026-08-28 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add an OPTIONAL, opt-in OS-sandbox hard-enforcement execution profile (x03wgn Section 8 "Phase 6") that makes "the driver is the only writer of the control root, main worktree, sibling lanes, credentials, and the git common directory" an OS-enforced guarantee against a malicious same-user worker, not merely a reliable operational rule; and that FAILS CLOSED (never silently runs unsandboxed) when the profile is requested on a host that cannot enforce it. The default operational profile (wtiso-01..05) is unchanged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: host capability contract

- [x] E-01 Add a typed `HostSandboxCapabilities` dataclass to new module `agent_workflows/host_sandbox_profile.py` with the exact boolean fields from x03wgn Section 6 Layer 4: `supports_inline_permissions`, `supports_read_only_phase`, `supports_session_resume`, `emits_structured_tool_events`, `emits_child_permission_events`, `supports_process_tree_kill`, `supports_os_sandbox`; each field defaults to `False` (fail-closed: an unprobed host claims no capability), plus a `platform: str` field and a `to_dict()` for durable snapshotting into the run/lane manifest.
  - Depends on: none
  - Expected outcome: `from agent_workflows.host_sandbox_profile import HostSandboxCapabilities; HostSandboxCapabilities().supports_os_sandbox is False` holds; every one of the seven named contract fields exists and defaults `False`.
  - Execution state: performed

- [x] E-02 Add `detect_host_capabilities(host: str, platform_name: str | None = None) -> HostSandboxCapabilities` to `host_sandbox_profile.py` that returns the fail-closed default (all `False`) for any host/platform NOT explicitly proven, and populates `supports_os_sandbox=True` (plus the process-tree-kill and read-only-phase fields it can back) ONLY for the single launch platform this phase certifies (Linux, using an unprivileged mount/user-namespace jail); wire it so `host_adapters` exposes the capability snapshot without editing the default launch path.
    THE PROBE MUST ATTEMPT, NOT INSPECT (found at review; this is the difference between failing closed and failing OPEN). Do NOT decide `supports_os_sandbox` by reading `/proc/sys/kernel/unprivileged_userns_clone`, `/proc/sys/user/max_user_namespaces`, `sys.platform`, or the mere PRESENCE of a `bwrap`/`unshare` binary. MEASURED COUNTEREXAMPLE on the review host: `unprivileged_userns_clone` was `1` and `max_user_namespaces` was `514277` (both look permissive) and BOTH `/usr/bin/unshare` and `/usr/bin/bwrap` were installed, yet an actual attempt FAILED - `unshare -Umr true` returned `Operation not permitted` writing `/proc/self/uid_map`, and `bwrap` failed with `setting up uid map: Permission denied` (the host is itself inside a namespace whose `uid_map` is `0 0 4294967295`). A sysctl/binary-presence probe would therefore have reported `supports_os_sandbox=True` on a host that CANNOT enforce the sandbox, and `select_execution_profile` (E-06) would have GRANTED hard mode - the exact silent degradation x03wgn Section 8 Phase 6.3 forbids, in the fail-OPEN direction. The probe MUST therefore actually execute a minimal jail (e.g. `unshare -Umr true`, or a `bwrap ... true` with the real bind set) in a subprocess, treat ANY nonzero exit / exception / timeout as `False`, and cache the single result per process. The same executable probe MUST back the `_linux_userns_available()` skipif helper used by E-08/E-09 so the tests and the capability report can never disagree.
  - Depends on: E-01
  - Expected outcome: `detect_host_capabilities("opencode", "windows").supports_os_sandbox is False` and `detect_host_capabilities("opencode", "darwin").supports_os_sandbox is False` (unproven platforms), while the certified Linux path reports `supports_os_sandbox` from an ATTEMPTED jail launch, not from a sysctl/binary check; on a host where the attempt fails (verified to include this review host) it reports `False`; no capability is asserted without a corresponding executed probe.
  - Execution state: performed

### Task group 2: OS-sandbox execution profile

- [x] E-03 Add `build_sandbox_plan(lane_worktree, lane_scratch, toolchain_roots, control_root, main_worktree, sibling_lane_roots, integration_candidate, credential_paths, git_common_dir) -> SandboxPlan` to `host_sandbox_profile.py` that computes the explicit mount/permission classes required by x03wgn Section 4 ("Container or OS sandbox"): WRITABLE = {lane worktree, lane scratch, selected build caches}; READ-ONLY = {required toolchain/dependencies}; INACCESSIBLE = {control root, main worktree, every sibling lane root, integration candidate, credentials not needed by the task}. The plan is a pure data structure (no side effects) so it can be unit-tested and asserted.
  - Depends on: E-01
  - Expected outcome: for a `SandboxPlan` built from representative paths, `plan.writable == {lane_worktree, lane_scratch}` (order-independent), and `control_root`, `main_worktree`, each `sibling_lane_root`, and `credential_paths` all appear in `plan.inaccessible` and in NEITHER `plan.writable` NOR `plan.readonly`.
  - Execution state: performed

- [x] E-04 In `build_sandbox_plan` classify the `git_common_dir` as READ-ONLY (never writable) and set `plan.driver_owns_git_mutation = True`, implementing the x03wgn Section 4 subtlety that a linked worktree's `.git` file points into the shared common dir so a writable common dir lets the worker mutate shared refs/hooks/config even when it cannot write main working files; add a `SandboxPlan.validate()` that raises `SandboxProfileError` if the common dir is ever placed in `writable`.
  - Depends on: E-03
  - Expected outcome: `plan.git_common_dir in plan.readonly and plan.git_common_dir not in plan.writable and plan.driver_owns_git_mutation is True`; constructing a plan that puts the common dir in `writable` and calling `validate()` raises `SandboxProfileError`.
  - Execution state: performed

- [x] E-05 Add `enter_sandbox(argv, sandbox_plan, capabilities) -> list[str]` to `host_sandbox_profile.py` that, on the certified Linux platform, wraps the worker `argv` in the unprivileged-namespace jail enforcing `sandbox_plan` (writable lane roots, read-only toolchain + git-common-dir, inaccessible control/main/sibling/credentials) and attaches the child tree to a killable group; the DRIVER (not the sandboxed worker) performs `git add`/commit/refs on the lane branch after the worker exits, so the sandboxed worker never needs common-dir write access. This is invoked ONLY when the hardened profile is explicitly selected AND `capabilities.supports_os_sandbox` is True.
  - Depends on: E-02, E-04
  - Expected outcome: `enter_sandbox` returns an argv whose leading tokens are the jail launcher configured from `sandbox_plan` (asserted by string inspection in tests); when the hardened profile is NOT selected the default `run_opencode` launch at `oc_runipd.py:1765` is byte-for-byte unchanged (regression test on the default path passes).
  - Execution state: performed

- [x] E-06 Add `select_execution_profile(requested_profile, capabilities) -> str` to `host_sandbox_profile.py` and call it in the `oc_runipd` launch path: when `requested_profile == "hardened"` and `capabilities.supports_os_sandbox` is False, RAISE `HardModeUnavailableError` (fail closed) rather than returning `"default"`; when `"hardened"` is requested and supported, return `"hardened"`; when unset/`"default"`, return `"default"`. x03wgn Section 8 Phase 6.3: "fail rather than silently degrading when hard mode is requested but unavailable."
  - Depends on: E-01
  - Expected outcome: `select_execution_profile("hardened", HostSandboxCapabilities(supports_os_sandbox=False))` raises `HardModeUnavailableError`; `select_execution_profile("default", HostSandboxCapabilities())` returns `"default"`; `select_execution_profile("hardened", HostSandboxCapabilities(supports_os_sandbox=True))` returns `"hardened"`.
  - Execution state: performed

### Task group 3: read-only discovery then write execution

- [x] E-07 Add `run_discovery_then_execution(...)` two-phase orchestration to `host_sandbox_profile.py` implementing x03wgn Section 6 Layer 4: PHASE 1 launches the worker with the product tree READ-ONLY and only a narrow submission channel writable (repository read access, no product writes); the driver validates the structured discovery submission (a prose-only claim is insufficient - x03wgn Layer 4 step 2); PHASE 2 flips the sandbox to grant product writes and resumes/relaunches with the validated discovery result injected. This is only offered when `capabilities.supports_read_only_phase` AND `capabilities.emits_structured_tool_events` are True; otherwise the driver keeps the prerequisite (no advisory before-edit barrier is claimed).
  - Depends on: E-05
  - Expected outcome: with capabilities lacking `supports_read_only_phase`, `run_discovery_then_execution` refuses to claim a before-edit barrier and returns a `barrier_enforced=False` result; with the capability present, phase 1 uses a read-only product-tree sandbox plan (asserted) and phase 2 uses the writable plan, and a phase-1 worker attempt to write a product file is denied.
  - Execution state: performed

### Task group 4: adversarial + fail-closed tests and published guarantees

- [x] E-08 Add adversarial test `test_hardened_worker_write_to_control_main_sibling_denied_by_os` to `tests/test_host_sandbox_profile.py` (marked `@pytest.mark.skipif(not _linux_userns_available(), reason="requires the certified Linux namespace sandbox")`, where `_linux_userns_available()` MUST be the SAME executed-attempt probe E-02 uses - not a sysctl/binary-presence check - so the skip decision and the reported capability can never disagree. NOTE (measured at review): the review host has permissive sysctls and both `unshare` and `bwrap` installed yet CANNOT create a userns (`unshare -Umr true` -> `Operation not permitted`), so this test is expected to report `1 skipped` there; a run that reports `1 passed` on such a host would mean the guard is not actually sandboxing and is a FAILURE, not a success): under the hardened profile, launch a worker command that attempts to write a file into (a) the control root, (b) the main worktree, and (c) a sibling lane root, and assert each write is DENIED BY THE OS (the target file does not exist afterward and the attempt returns a permission error), NOT merely flagged by policy.
  - Depends on: E-05
  - Expected outcome: `python3 -m pytest -p no:randomly -q tests/test_host_sandbox_profile.py::test_hardened_worker_write_to_control_main_sibling_denied_by_os` reports `1 passed` on the certified Linux host (or `1 skipped` where the sandbox is unavailable), and none of the three target files exist after the run.
  - Execution state: performed

- [x] E-09 Add adversarial test `test_hardened_worker_git_common_dir_mutation_denied` to `tests/test_host_sandbox_profile.py` (same skipif guard): under the hardened profile with the git common dir read-only, launch a worker command that attempts to mutate a shared git ref / hook / config through the common dir (e.g. `git update-ref`, writing `hooks/pre-commit`, `git config`), and assert the mutation is DENIED (the ref/hook/config is unchanged afterward) while a subsequent DRIVER-performed commit on the lane branch succeeds - proving the driver owns git mutation.
  - Depends on: E-04, E-05
  - Expected outcome: `python3 -m pytest -p no:randomly -q tests/test_host_sandbox_profile.py::test_hardened_worker_git_common_dir_mutation_denied` reports `1 passed` (or `1 skipped`); the pre-existing ref/hook/config bytes are identical before and after the worker attempt, and the driver's lane-branch commit is reachable.
  - Execution state: performed

- [x] E-10 Add fail-closed test `test_hard_mode_requested_without_capability_fails_closed` to `tests/test_host_sandbox_profile.py` WITHOUT any skipif (it MUST run on every platform, because it is pure dispatch logic): assert `select_execution_profile("hardened", HostSandboxCapabilities(supports_os_sandbox=False))` raises `HardModeUnavailableError` and that the default launch path is never entered in that case (no unsandboxed worker is spawned). ALSO publish the hardened-profile guarantee summary as the `host_sandbox_profile.py` module docstring: what it prevents, the exact platform + probe it was verified on, that the git common dir is read-only to the worker, that the DRIVER performs all git mutation, and - stated explicitly - that the guarantee is VOID on any host where the executed userns probe (E-02) returns False (x03wgn Section 8 Phase 6.3 "publish guarantees"). (Editorial note added at review: the previous wording contained a stray half-sentence, "write `.aw/records/walkthroughs/` guarantees text is out of scope but publish ...", which read as an instruction to write a walkthrough while also saying it was out of scope; the walkthrough is NOT in Scope-Paths and is NOT part of this item - only the module docstring is.)
  - Depends on: E-06
  - Expected outcome: `python3 -m pytest -p no:randomly -q tests/test_host_sandbox_profile.py::test_hard_mode_requested_without_capability_fails_closed` reports `1 passed` on ALL platforms (no skip); `host_sandbox_profile.py`'s module docstring states the published guarantees.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Worker launch seam: `run_opencode` in `agent_workflows/oc_runipd.py:1679` builds `argv` (`:1694`), sets the lane worktree via `--dir agent_dir` (`:1713`, `agent_dir = work_dir or state["repo"]` at `:1697`), and `subprocess.Popen(argv, **popen_kwargs)` at `:1765` with `cwd=agent_dir` (`:1753`) and `start_new_session=True` on POSIX (`:1760`). There is NO filesystem write boundary today; `start_new_session` exists only so `terminate_process` (`:1632`) can `os.killpg` the tree (`:1643`). The hardened profile wraps this argv; the default path stays untouched.
- Worktree substrate: `worktree_lease.allocate_worktree` (`agent_workflows/worktree_lease.py:70`) does `git worktree add -b aw/lane/<name> <path> <base_sha>` under the gitignored `.aw/worktrees/<lane>` (`WORKTREES_SUBDIR`, `:32`); a linked worktree's `.git` points into the shared common dir, which is exactly the x03wgn Section 4 mutation surface. `worktree_lease.FORBIDDEN_WORKER_PATH_HINTS` (`:199`) + `assert_worker_scope` (`:214`) are POLICY-level fencing (a `LeaseConflictError` on declared paths) - the hardened profile is the OS-level complement they cannot provide against undeclared writes.
- Receipt handling: the current default copies the begin receipt into the worktree (`sync_receipt_into_worktree`, `oc_runipd.py:470`); wtiso-03..05 move that authority out of the lane. This phase does not reintroduce a lane-local authority copy.
- Git-common-dir identity already exists: `project_registry.get_git_common_dir` (`agent_workflows/project_registry.py:182`) runs `git rev-parse --git-common-dir` (`:190`); the sandbox plan classifies exactly that path read-only.
- A host-capability EVIDENCE registry already exists for skill probes (`agent_workflows/host_capability_registry.py`, awoptimize/4fttzq); it is a DIFFERENT concern (skill resolution) and is NOT the isolation capability contract of x03wgn Layer 4. This phase adds the isolation contract in a new module rather than overloading that one.
- IPD scaffold + linter: `aw ipd scaffold`/`sync`/`lint --phase author`; conforming siblings keep the fixed section order shown in this file.

## Findings

CITATION BASIS (added at review): every `file:line` reference was RE-VERIFIED against the current working tree on 2026-08-29. EXACTLY ACCURATE as written: `worktree_lease.py` (`WORKTREES_SUBDIR:32`, `allocate_worktree:70`, `FORBIDDEN_WORKER_PATH_HINTS:199`, `assert_worker_scope:214`) and `project_registry.py` (`get_git_common_dir:182`, the `rev-parse --git-common-dir` call `:190`); `host_adapters.py` and `host_capability_registry.py` both exist as described. CORRECTED for snapshot drift (`8d1bcd5` -> HEAD, the launch seam moved ~+73/+80 lines): `run_opencode` 1606->1679, `argv` build 1621->1694, `agent_dir` 1624->1697, `--dir` 1640->1713, `cwd` 1680->1753, `start_new_session` 1687->1760, `Popen` 1692->1765, `terminate_process` 1559->1632 with `killpg` 1570->1643, and `sync_receipt_into_worktree` 462->470. Anchor on SYMBOL NAMES and re-verify with `grep -n '<symbol>'`.

| # | Finding | Evidence (x03wgn section + real file:line) |
|---|---|---|
| F1 | The default profile is deliberately NOT a security boundary against a malicious same-user worker; hardening is an explicitly optional profile. | x03wgn Section 1 ("A same-user process with arbitrary shell access cannot be ... enforced from prompts, hooks, environment variables, or Python role checks alone"); Section 1 "Two enforcement profiles" (2. Hardened execution); Section 7 hazard "Malicious same-user worker rewrites control root ... Explicitly outside default trust guarantee." |
| F2 | The hardened profile's writable/read-only/inaccessible partition is prescribed exactly. | x03wgn Section 4 "Container or OS sandbox": Writable {lane worktree, lane scratch, selected build caches}; Read-only {toolchain/deps, perhaps policy}; Inaccessible {control root, main worktree, sibling lanes, integration candidate, credentials}. |
| F3 | A linked worktree's `.git` points into the shared common dir, so a writable common dir lets the worker mutate shared refs/hooks/config; hardened mode MUST keep the common dir read-only and have the driver own staging/commits. | x03wgn Section 4 ("A linked worktree adds one subtlety ... keep the common directory read-only to the worker and make the driver own staging and commits"); real substrate: `worktree_lease.py:70`/`:83` (`git worktree add` under `WORKTREES_SUBDIR`), `project_registry.py:182` (`--git-common-dir`). |
| F4 | The host capability contract is the exact set of booleans to define, and adapters must not each reimplement lifecycle/sandbox semantics. | x03wgn Section 6 Layer 4 (contract list: supports_inline_permissions, supports_read_only_phase, supports_session_resume, emits_structured_tool_events, emits_child_permission_events, supports_process_tree_kill, supports_os_sandbox). |
| F5 | A true before-edit barrier requires a read-only discovery phase then a write execution phase; prose alone is insufficient where tool events exist; if the host cannot enforce read-only files/phase-specific tools the barrier is only advisory and the prerequisite must move into the driver. | x03wgn Section 6 Layer 4 (four-step discovery->execution); Section 2 "Receipt ownership does not mean agent tool compliance" ("A prompt cannot create a reliable before-edit barrier"). |
| F6 | Start on one platform, publish guarantees, and FAIL rather than silently degrade when hard mode is requested but unavailable; do not make hardened mode the default. | x03wgn Section 8 "Phase 6" steps 1-4 (esp. "fail rather than silently degrading when hard mode is requested but unavailable"; "Do not make hardened mode the default"); Section 1 ("The default should not pay the portability and maintenance cost of a container solely to compensate for model forgetfulness"). |
| F7 | Adversarial acceptance is required: an OS denial of main/control/sibling writes in hardened mode, and no worker mutation of the git common dir. | x03wgn Section 7 "Adversarial acceptance tests" ("An agent tries main/control/sibling-lane writes in hardened mode; the OS must deny them"; "An agent attempts to update the target ref or shared hook configuration; ... hardened mode denies it"); Section 9 acceptance criteria ("hardened workers cannot write the Git common directory"; "in hardened mode, the OS denies them"). |
| F8 | The current launch has no write boundary; it only groups the process for killing. | `oc_runipd.py:1713` (`--dir agent_dir`), `:1753` (`cwd=agent_dir`), `:1760` (`start_new_session=True`), `:1765` (`Popen`), `:1632`/`:1643` (`os.killpg` reap). |

## Proposed changes (ordered, validatable)

1. New module `agent_workflows/host_sandbox_profile.py`: `HostSandboxCapabilities` (E-01), `detect_host_capabilities` (E-02), `SandboxPlan`/`build_sandbox_plan`/`SandboxProfileError` (E-03, E-04), `enter_sandbox` (E-05), `select_execution_profile`/`HardModeUnavailableError` (E-06), `run_discovery_then_execution` (E-07), plus a module docstring publishing the hardened-profile guarantees (E-10).
2. `agent_workflows/host_adapters.py`: expose the capability snapshot for a host without altering the default launch (E-02).
3. `agent_workflows/oc_runipd.py`: call `select_execution_profile` before launch and, only when `"hardened"` is selected and supported, wrap the worker `argv` via `enter_sandbox`; the default path at `:1765` is unchanged (E-05, E-06).
4. `tests/test_host_sandbox_profile.py`: adversarial OS-denial tests (E-08, E-09, skipif-guarded on non-sandbox platforms) and the fail-closed dispatch test (E-10, runs everywhere).

## Deferred / out of scope (with reason)

- This ENTIRE phase is optional/hardening and parkable. Per the orchestrator (bl9q3d) OQ-01 (resolved: follow-up-eligible) and its "Deferred / out of scope" note, the release blockers qyaime/xmqv5l/dh0uno are fully resolved by wtiso-02..05; Phase 6 is defense-in-depth against a MALICIOUS (not merely forgetful) same-user worker and may be deferred or parked without blocking the Set's release-gating value. The `Item-Dependencies: executed:2c122z` chain stands.
- macOS `sandbox-exec`/Seatbelt and Windows restricted-token/Job-Object sandbox profiles: out of scope. x03wgn Section 8 Phase 6.3 mandates starting on ONE platform and publishing its guarantees; this phase certifies Linux only and reports `supports_os_sandbox=False` (fail-closed) elsewhere, so hard mode requested on those platforms fails closed (E-06/E-10) rather than pretending to enforce.
- Container-based (Docker/Podman) isolation and network sandboxing: out of scope; x03wgn Section 8 Phase 6.4 defers hardened-default adoption until dependency caches, toolchains, network needs, diagnostics, and cleanup are operationally understood. Network scoping (x03wgn Section 4 "Network: disabled or narrowly scoped") is noted but not implemented here.
- An isolated-clone / mediated-git-service path for a worker that needs unrestricted git-write capability: out of scope; x03wgn Section 4 names it as the alternative when a worktree cannot be a security boundary, but this phase's driver-owns-mutation design does not require it.
- Changing the DEFAULT profile behavior: out of scope; this phase is strictly additive and opt-in.

## Scope check

- Over-scope: none. Only the sandbox module, the launch dispatch/wrap seam, the adapter capability snapshot, and the new test file are touched.
- Under-scope: none. The three mandated adversarial/fail-closed acceptances (OS-denied control/main/sibling write, common-dir mutation denial, hard-mode-without-capability fail-closed) each have a named E-item + a named test function, and the fail-closed test runs on every platform.

## Required tests / validation

- `python3 -m pytest -p no:randomly -q tests/test_host_sandbox_profile.py` - full new-module suite green (adversarial tests `passed` on the certified Linux host or `skipped` elsewhere; the fail-closed test `passed` everywhere). Paste ACTUAL output.
- `python3 -m pytest -p no:randomly -q tests/test_oc_runipd.py` - default launch path regression green (hardened profile is additive). Paste ACTUAL output.
- `python3 -m agent_workflows ipd lint --phase pre-transition .aw/records/plans/pending/20260828-wtiso-07-1o4eif-phase-6-optional-os-sandbox-hard-enforcement-profile-host-ca.ipd.md` - conforming before the lifecycle move. Paste ACTUAL output.

## Spec / documentation sync

- The hardened-profile guarantees (what it prevents, that it is Linux-only for now, that the git common dir is read-only, that the driver owns git mutation) are published in the `host_sandbox_profile.py` module docstring (E-10). No separate spec doc is created; x03wgn Section 8 Phase 6 is the binding design and is cited throughout Findings.

## Open questions

### OQ-01: Is Phase 6 (this OS-sandbox hard mode) in-scope for the release this Set gates, or a follow-up?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: Follow-up-eligible / parkable, per the orchestrator bl9q3d OQ-01 (resolved) and its Deferred note. The release blockers qyaime/xmqv5l/dh0uno are fully resolved by wtiso-02..05; this phase is optional defense-in-depth against a malicious same-user worker (x03wgn Section 1 "Two enforcement profiles" -> hardened; Section 7 malicious-worker hazard). The `executed:2c122z` dependency stands but this child may be deferred/parked without blocking the Set's release-gating value.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: ACTUAL pasted output of `python3 -c "from agent_workflows.host_sandbox_profile import HostSandboxCapabilities as C; c=C(); print([f for f in ('supports_inline_permissions','supports_read_only_phase','supports_session_resume','emits_structured_tool_events','emits_child_permission_events','supports_process_tree_kill','supports_os_sandbox') if getattr(c,f) is False]); print(len([f for f in vars(c)]))"` showing all seven named fields present and each defaulting `False` (the printed list contains all seven names).
  - Observed evidence: all SEVEN contract fields exist and each defaults `False`; `10` = the 7 contract booleans plus `platform`, `sandbox_mechanism`, `probe_notes`.

    $ python3 -c "...seven-field default check..."

    ```text
    ['supports_inline_permissions', 'supports_read_only_phase', 'supports_session_resume',
     'emits_structured_tool_events', 'emits_child_permission_events',
     'supports_process_tree_kill', 'supports_os_sandbox']
    10
    ```

    $ python3 -m pytest -p no:randomly -n0 --no-header tests/test_host_sandbox_profile.py::CapabilityContractTests

    ```text
    ..                                                                       [100%]
    2 passed in 0.11s
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: ACTUAL pasted output of `python3 -c "from agent_workflows.host_sandbox_profile import detect_host_capabilities as d; print(d('opencode','windows').supports_os_sandbox, d('opencode','darwin').supports_os_sandbox)"` printing `False False` (unproven platforms report no sandbox capability - fail-closed). PLUS the ATTEMPT-BASED PROBE PROOF (added at review; the `False False` assertion above would also pass for a sysctl-reading probe, so it does not establish E-02's real requirement): paste BOTH (a) the executing host's own result `python3 -c "from agent_workflows.host_sandbox_profile import detect_host_capabilities as d; print(d('opencode').supports_os_sandbox)"` alongside the ground truth `unshare -Umr true; echo rc=$?` (or the equivalent `bwrap ... true`), showing the reported capability MATCHES the attempted-launch exit code; and (b) evidence the probe does not consult sysctls alone - e.g. an `ast`/`grep` check that the probe body invokes a subprocess jail attempt, or a test that monkeypatches the jail attempt to fail and asserts `supports_os_sandbox` flips to `False` even while `/proc/sys/user/max_user_namespaces` remains nonzero. MEASURED REFERENCE (review host): sysctls read `unprivileged_userns_clone=1`, `max_user_namespaces=514277`, both `unshare` and `bwrap` installed, yet `unshare -Umr true` -> `Operation not permitted` and `bwrap` -> `setting up uid map: Permission denied`; on such a host this V-item REQUIRES the probe to report `False`.
  - Observed evidence: the probe ATTEMPTS rather than inspects, and its report matches ground truth.

    $ python3 -c "from agent_workflows.host_sandbox_profile import detect_host_capabilities as d; print(d('opencode','windows').supports_os_sandbox, d('opencode','darwin').supports_os_sandbox)"

    ```text
    False False
    ```

    $ python3 -c "print('reported:', detect_host_capabilities('opencode').supports_os_sandbox)"  # executing host

    ```text
    reported: True
    ```

    $ python3 -c "ok,note=_probe_landlock(); print(ok, '|', note)"   # ground truth, landlock rung

    ```text
    True | landlock jail enforced: write outside the allowed root was refused
    ```

    $ unshare -Umr true; echo rc=$?                                  # ground truth, userns rung

    ```text
    unshare: write failed /proc/self/uid_map: Operation not permitted
    rc=1
    ```

    $ python3 -c "<force every ladder ATTEMPT to fail, leave sysctls untouched>"

    ```text
    with all attempts forced to fail -> False
    sysctl still says: 514277
    ```

    $ python3 -c "<ast walk: does each probe invoke a subprocess attempt?>"

    ```text
    _probe_landlock -> invokes subprocess/attempt: True ['_run_probe']
    _probe_bwrap -> invokes subprocess/attempt: True ['_run_probe', 'which']
    _probe_userns -> invokes subprocess/attempt: True ['_run_probe', 'which']
    _run_probe -> invokes subprocess/attempt: True ['run']
    ```

    $ python3 -m pytest -p no:randomly -n0 --no-header tests/test_host_sandbox_profile.py::CapabilityProbeTests

    ```text
    ....                                                                     [100%]
    4 passed in 0.63s
    ```

    (a) UNPROVEN PLATFORMS report `False False` - fail-closed. (b) REPORT vs GROUND TRUTH AGREE: the reported capability tracks the rung that actually launches - the Landlock attempt SUCCEEDS (and its success criterion is that the kernel REFUSED a write outside the allowed root, not merely that syscalls returned 0), while the userns attempt FAILS rc=1; `sandbox_mechanism` names `landlock`. (c) THE PROBE IS NOT SYSCTL/BINARY-PRESENCE: forcing every ATTEMPT to fail flips `supports_os_sandbox` to False while `max_user_namespaces` still reads `514277` and both `unshare` and `bwrap` remain installed - an inspection-based probe would still have reported True, which is the fail-OPEN direction the design forbids.

    CERTIFIED HOST for this guarantee: `Linux 6.8.0-137-generic x86_64 GNU/Linux`; Landlock LSM enabled (`/sys/kernel/security/lsm` = `lockdown,capability,landlock,yama,apparmor`); Landlock ABI 4. This host CANNOT create a user namespace (`unshare -Umr true` -> rc=1 `write failed /proc/self/uid_map: Operation not permitted`; `bwrap` -> `setting up uid map: Permission denied`), reproducing the review measurement exactly. The certified mechanism is therefore the LANDLOCK rung of the executed probe ladder (see decision 08-1o4eif-D1), which IS enforced here, so this guarantee is VERIFIED BY EXECUTION rather than skipped.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: ACTUAL pasted stdout of a `python3 -m pytest -p no:randomly -q tests/test_host_sandbox_profile.py::test_build_sandbox_plan_partition` run reporting `1 passed`, whose asserts prove `writable == {lane_worktree, lane_scratch}` and that control_root, main_worktree, each sibling_lane_root, and credential_paths are all in `inaccessible` and in neither `writable` nor `readonly`.
  - Observed evidence: `1 passed`.

    $ python3 -m pytest -p no:randomly -n0 -rs --no-header tests/test_host_sandbox_profile.py::SandboxPlanTests::test_build_sandbox_plan_partition

    ```text
    .                                                                        [100%]
    1 passed in 0.12s
    ```

    The test asserts `set(plan.writable) == {lane_worktree, lane_scratch}` (order-independent) and, for each of `control_root`, `main_worktree`, the `sibling_lane` root, `integration_candidate`, and `credential_paths`: present in `plan.inaccessible`, and in NEITHER `plan.writable` NOR `plan.readonly`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: ACTUAL pasted stdout of `python3 -m pytest -p no:randomly -q tests/test_host_sandbox_profile.py::test_git_common_dir_readonly_and_driver_owns_mutation` reporting `1 passed`, asserting `git_common_dir in readonly`, `git_common_dir not in writable`, `driver_owns_git_mutation is True`, AND that a plan placing the common dir in `writable` raises `SandboxProfileError` on `validate()`.
  - Observed evidence: `1 passed`.

    $ python3 -m pytest -p no:randomly -n0 -rs --no-header tests/test_host_sandbox_profile.py::SandboxPlanTests::test_git_common_dir_readonly_and_driver_owns_mutation

    ```text
    .                                                                        [100%]
    1 passed in 0.12s
    ```

    Asserts `git_common_dir in plan.readonly`, `git_common_dir not in plan.writable`, `driver_owns_git_mutation is True`, AND that a `SandboxPlan` placing the common dir in `writable` raises `SandboxProfileError` on `validate()`. A companion test proves `driver_owns_git_mutation=False` is refused as well.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: ACTUAL pasted stdout of `python3 -m pytest -p no:randomly -q tests/test_host_sandbox_profile.py::test_enter_sandbox_wraps_argv_and_default_path_unchanged` reporting `1 passed`, proving `enter_sandbox` prepends the jail launcher configured from the plan AND that the default (non-hardened) launch argv is unchanged.
  - Observed evidence: `1 passed`, plus the default-path regression.

    $ python3 -m pytest -p no:randomly -n0 -rs --no-header tests/test_host_sandbox_profile.py::EnterSandboxTests::test_enter_sandbox_wraps_argv_and_default_path_unchanged

    ```text
    .                                                                        [100%]
    1 passed in 0.12s
    ```

    $ python3 -m pytest -p no:randomly --no-header tests/test_oc_runipd.py     # default launch path

    ```text
    ........................................................................ [ 85%]
    ............                                                             [100%]
    84 passed in 3.44s
    ```

    $ git diff --stat agent_workflows/oc_runipd.py

    ```text
     agent_workflows/oc_runipd.py | 135 +++++++++++++++++++++++++++++++++++++++++++
     1 file changed, 135 insertions(+)
    ```

    The test proves (a) `enter_sandbox` PREPENDS the jail launcher configured from the plan - `wrapped[0] == sys.executable`, `wrapped[1]` ends with `aw-landlock-bootstrap.py`, and the generated bootstrap contains the lane path, `landlock_restrict_self`, and the real worker argv; for the `bwrap` rung `wrapped[0] == "bwrap"` with `--unshare-user` and the original argv as the tail; and (b) THE DEFAULT PATH IS UNCHANGED - `_apply_execution_profile` with no `execution_profile` option returns a list byte-for-byte equal to its input argv. `enter_sandbox` also REFUSES (`HardModeUnavailableError`) when `supports_os_sandbox` is False, so it can never be the route by which an unsandboxed worker launches. The `oc_runipd.py` diff is purely ADDITIVE (135 insertions, 0 deletions): the `subprocess.Popen` launch itself is untouched.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: E-06 is the `select_execution_profile` DISPATCH FUNCTION; E-10 is the platform-independent TEST of it. To keep these two V-items from being satisfied by one identical paste (they named the same test), this V-item validates the dispatch's THREE-WAY behavior directly and E-10's validates the test artifact. Paste the ACTUAL output of `python3 -c "from agent_workflows.host_sandbox_profile import select_execution_profile as s, HostSandboxCapabilities as C, HardModeUnavailableError as E;\nprint(s('default', C()));\nprint(s('hardened', C(supports_os_sandbox=True)));\ntry:\n    s('hardened', C(supports_os_sandbox=False)); print('BUG: no raise')\nexcept E as exc: print('raised', type(exc).__name__)"` showing exactly `default`, `hardened`, and `raised HardModeUnavailableError` - i.e. all three branches of E-06's contract, including that an unset/`"default"` request never raises.
  - Observed evidence: all THREE branches of the dispatch contract.

    $ python3 -c "print(s('default', C())); print(s('hardened', C(supports_os_sandbox=True))); try: s('hardened', C(supports_os_sandbox=False)) except E as exc: print('raised', type(exc).__name__)"

    ```text
    default
    hardened
    raised HardModeUnavailableError
    ```

    A `default` (or unset) request returns `"default"` and NEVER raises; `hardened` with the capability returns `"hardened"`; `hardened` WITHOUT the capability raises `HardModeUnavailableError` - fail closed, not a silent downgrade to `"default"`. An unknown profile name is refused with `SandboxProfileError` (`ProfileDispatchTests::test_unknown_profile_is_refused`).
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: ACTUAL pasted stdout of `python3 -m pytest -p no:randomly -q tests/test_host_sandbox_profile.py::test_discovery_then_execution_barrier` reporting `1 passed` (or the read-only-phase-dependent asserts `skipped` where the capability is absent) showing that without `supports_read_only_phase` no before-edit barrier is claimed (`barrier_enforced is False`), and with it phase 1 uses a read-only product-tree plan and a phase-1 product write is denied.
  - Observed evidence: `3 passed` for the discovery/execution group.

    $ python3 -m pytest -p no:randomly -n0 -rs --no-header tests/test_host_sandbox_profile.py::DiscoveryThenExecutionTests

    ```text
    ...                                                                      [100%]
    3 passed in 0.20s
    ```

    `test_discovery_then_execution_barrier` proves: WITHOUT `supports_read_only_phase` no before-edit barrier is claimed (`barrier_enforced is False`, the reason says `advisory`, and neither callback is invoked - each would `self.fail()`); WITH the capability, phase 1's plan has the lane product tree in `readonly` and NOT in `writable`, while phase 2's has it in `writable`. `test_prose_only_submission_does_not_authorize_writes` proves a PROSE-only submission fails driver validation and product writes are NOT authorized (x03wgn Layer 4 step 2). `test_phase_one_product_write_is_denied_by_os` proves a phase-1 worker attempt to write a product file is DENIED BY THE OS with the original bytes intact.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: ACTUAL pasted stdout of `python3 -m pytest -p no:randomly -q tests/test_host_sandbox_profile.py::test_hardened_worker_write_to_control_main_sibling_denied_by_os`; the test asserts none of the three target files (control-root write, main-worktree write, sibling-lane write) exist after the run AND each attempt returned an OS permission error - proving OS denial, not policy detection.
    A SKIP DOES NOT SATISFY THIS V-ITEM (hardened; this is the phase's flagship guarantee). `1 skipped` is an ACCEPTABLE CI outcome but is NOT acceptance evidence: it proves nothing about OS enforcement, and this plan's whole value is that the OS - not policy - denies the write. Therefore this V-item may be marked `pass` ONLY with pasted `1 passed` from a host where the executed userns probe (E-02) returns True. If the executing host cannot create a userns (measured true on the review host: `unshare -Umr true` -> `Operation not permitted`), then: paste the `1 skipped` output AND the probe output proving WHY it skipped, mark this V-item `Result: pending` (not `pass`), and record in the plan that the hardened profile is UNVERIFIED on this machine - do not claim the guarantee. Naming the certified host/kernel where `1 passed` was obtained is part of the evidence (x03wgn Section 8 Phase 6.3 requires publishing the platform the guarantee holds on). The same rule applies to V-09.
  - Observed evidence: `1 passed` - NOT `1 skipped`.

    $ python3 -m pytest -p no:randomly -n0 -rs --no-header tests/test_host_sandbox_profile.py::AdversarialOsDenialTests::test_hardened_worker_write_to_control_main_sibling_denied_by_os

    ```text
    .                                                                        [100%]
    1 passed in 0.16s
    ```

    The sandboxed worker attempts a write to (a) the control root, (b) the main worktree, and (c) a sibling lane root. The test asserts each result is `DENIED:13` - EACCES FROM THE KERNEL, an OS denial rather than a policy flag - and that NONE of the three target files exists afterward. The worker's own lane stays writable in the same run, which is what proves the denial is a real boundary and not a broken interpreter.

    CERTIFIED HOST for this guarantee: `Linux 6.8.0-137-generic x86_64 GNU/Linux`; Landlock LSM enabled (`/sys/kernel/security/lsm` = `lockdown,capability,landlock,yama,apparmor`); Landlock ABI 4. This host CANNOT create a user namespace (`unshare -Umr true` -> rc=1 `write failed /proc/self/uid_map: Operation not permitted`; `bwrap` -> `setting up uid map: Permission denied`), reproducing the review measurement exactly. The certified mechanism is therefore the LANDLOCK rung of the executed probe ladder (see decision 08-1o4eif-D1), which IS enforced here, so this guarantee is VERIFIED BY EXECUTION rather than skipped.
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: ACTUAL pasted stdout of `python3 -m pytest -p no:randomly -q tests/test_host_sandbox_profile.py::test_hardened_worker_git_common_dir_mutation_denied`; the test asserts the target ref/hook/config bytes are byte-identical before and after the worker's mutation attempt through the read-only common dir, AND that a subsequent driver-performed lane-branch commit is reachable (`git cat-file -e <oid>` succeeds) - proving the common dir is read-only to the worker and the driver owns git mutation. A SKIP DOES NOT SATISFY THIS V-ITEM: per the V-08 rule, `1 skipped` requires marking this `Result: pending` with the probe output showing why, and the guarantee recorded as UNVERIFIED on that machine; only pasted `1 passed` from a userns-capable host (named, with kernel) may mark it `pass`.
  - Observed evidence: `1 passed` - NOT `1 skipped`.

    $ python3 -m pytest -p no:randomly -n0 -rs --no-header tests/test_host_sandbox_profile.py::AdversarialOsDenialTests::test_hardened_worker_git_common_dir_mutation_denied

    ```text
    .                                                                        [100%]
    1 passed in 0.23s
    ```

    # the same split measured by hand against a scratch linked worktree:

    ```text
    git READ (status): rc=0 out='' err=''
    update-ref: rc=128 err=fatal: update_ref failed for ref 'refs/heads/evil': cannot lock ref
    config hooksPath: rc=255 err=error: could not lock config file .../main/.git/config: Permission denied
    git add: rc=128 err=fatal: Unable to create '.../main/.git/worktrees/lane/index.lock': Permission denied
    ```

    On a REAL linked worktree (`git worktree add -b aw/lane/test`) with the common dir read-only, the test asserts: the worker's `git status --porcelain` still returns rc=0 (READ works, so the denials are specifically about WRITE and not a broken toolchain); `git update-ref refs/heads/evil`, `git config core.hooksPath`, and `git add -A` ALL return nonzero; a direct `hooks/pre-commit` write returns `DENIED:<errno>`; `hooks/pre-commit` and `config` are BYTE-IDENTICAL before and after and `git for-each-ref` output is unchanged; and then the DRIVER (unsandboxed) performs `git add` + `commit` on the lane branch successfully, the commit being reachable via `git cat-file -e <oid>` from the main worktree - proving the driver owns git mutation.

    CERTIFIED HOST for this guarantee: `Linux 6.8.0-137-generic x86_64 GNU/Linux`; Landlock LSM enabled (`/sys/kernel/security/lsm` = `lockdown,capability,landlock,yama,apparmor`); Landlock ABI 4. This host CANNOT create a user namespace (`unshare -Umr true` -> rc=1 `write failed /proc/self/uid_map: Operation not permitted`; `bwrap` -> `setting up uid map: Permission denied`), reproducing the review measurement exactly. The certified mechanism is therefore the LANDLOCK rung of the executed probe ladder (see decision 08-1o4eif-D1), which IS enforced here, so this guarantee is VERIFIED BY EXECUTION rather than skipped.
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: ACTUAL pasted stdout of `python3 -m pytest -p no:randomly -q tests/test_host_sandbox_profile.py::test_hard_mode_requested_without_capability_fails_closed` reporting `1 passed` with NO skip marker on this run (the fail-closed test must run on every platform), PLUS pasted output of `python3 -c "import agent_workflows.host_sandbox_profile as m; print('read-only' in m.__doc__.lower() and 'driver' in m.__doc__.lower() and 'linux' in m.__doc__.lower())"` printing `True` (the published guarantees are in the module docstring).
  - Observed evidence: `1 passed` with NO skip marker, on a test that carries no skipif.

    $ python3 -m pytest -p no:randomly -n0 -rs --no-header tests/test_host_sandbox_profile.py::ProfileDispatchTests::test_hard_mode_requested_without_capability_fails_closed

    ```text
    .                                                                        [100%]
    1 passed in 0.12s
    ```

    $ python3 -c "import agent_workflows.host_sandbox_profile as m; print('read-only' in m.__doc__.lower() and 'driver' in m.__doc__.lower() and 'linux' in m.__doc__.lower())"

    ```text
    True
    ```

    The test asserts `select_execution_profile("hardened", HostSandboxCapabilities(supports_os_sandbox=False))` raises `HardModeUnavailableError`, and additionally patches `subprocess.Popen` to a fixture that FAILS if called, then drives the real driver seam `oc_runipd._apply_execution_profile` with `execution_profile="hardened"` and a False-capability snapshot: the raise happens and `spawned == []`, proving NO unsandboxed worker is spawned on the fail-closed path. The module docstring publishes what the profile prevents, the exact platform and executed probe ladder it was verified on (Linux only; Landlock ABI 4 on 6.8.0-137-generic), that the git common dir is READ-ONLY to the worker, that the DRIVER performs all git mutation, and - explicitly - that THE GUARANTEE IS VOID on any host where the executed probe returns False. `ProfileDispatchTests::test_module_publishes_its_guarantees` pins those tokens.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract - this child inherits VERBATIM the shared anti-greenwash execution contract authored by the orchestrator (bl9q3d); it is reproduced here in full and MUST NOT be weakened per child:

1. **Prose is never evidence.** No E-item is complete on an assertion. Each E-item names ONE observable action; each paired V-item names FALSIFIABLE evidence: an exact command to run plus the specific string/exit-code/file-state that must appear. "Tests pass", "done", "verified", "should work" are forbidden as evidence.
2. **Paste real output (HARD MUST).** Every V-item's Observed evidence MUST be the ACTUAL pasted stdout/stderr + exit code of the named command, run in this repo at execution time. Fabricated, summarized, remembered, or "expected" output is a validation failure and a GP2 honesty violation. A V-item whose command was not run stays `Result: pending`.
3. **Adversarial acceptance is mandatory.** Because this Set is ABOUT untrustworthy agents, each child MUST include at least one adversarial test proving the guard fires: a test that a wrong/forgetful/lying behavior is DETECTED and BLOCKED (e.g. a fabricated outcome.json does not mark success; a stale/forked receipt is refused; an unanswerable permission prompt is killed, not awaited). Green-path-only tests are insufficient and are an UNDER-SCOPE finding.
4. **Determinism over model judgment.** Where a check can be a pure function + unit test (path resolution, receipt validity, scope reconciliation, retention classification), it MUST be, and the hook/driver/verifier MUST call the SAME predicate library so rules cannot drift.
5. **Scope fence.** Touch ONLY the child's declared Scope-Paths. Do not edit sibling children, this orchestrator, or product code outside scope. If the work seems to need more, STOP and report - do not silently broaden.
6. **Path-scoped commits, never push.** `git commit -m msg -- <paths>`; never `git add -A`/bare/`-a`; never push; never `--no-verify`.
7. **Lifecycle move is a POST-gate step.** Verify every V-item with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed. (NOTE: until wtiso-03 lands, finalize may hit xmqv5l; if so, record substantially-complete honestly rather than forcing.)
8. **Cite the research.** Each child's Findings section MUST cite the exact x03wgn section(s) it implements (research doc 20260828-wtiso-00-x03wgn) so a reviewer can check fidelity to the approved design.

This child implements x03wgn Section 8 "Phase 6" (with Sections 1, 4, and 6 Layer 4). It is optional/hardening and parkable per orchestrator OQ-01.

Post-gate lifecycle move: after every V-item above carries the pasted evidence it specifies and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize` on this plan; do not move it to executed/ otherwise. Commit ONLY the Scope-Paths files, path-scoped (`git commit -m msg -- agent_workflows/host_sandbox_profile.py agent_workflows/oc_runipd.py agent_workflows/host_adapters.py tests/test_host_sandbox_profile.py`); never `git add -A`/`-a`; never push; never `--no-verify`. This plan file is NOT in Scope-Paths and must not be committed by hand (matching the Set's other children and every executed plan in this repo): `aw ipd finalize` owns it - appending the history entry, setting terminal status, `git mv`ing it out of `pending/`, and making the lifecycle commit. Edit the plan's own E/V state normally during execution; just do not commit it yourself.

HONEST-CLOSURE RULE for this phase specifically (added at review): the hardened guarantee is only real where the OS enforces it. If the executing host's userns probe (E-02) returns False, V-08 and V-09 stay `Result: pending`, the module docstring's published guarantee must say the profile is UNVERIFIED on that platform, and this plan MUST NOT be moved to `executed/` claiming the OS-denial guarantees hold - either run it on a userns-capable host, or leave the plan `approved`/parked per orchestrator OQ-01 rather than recording an unearned pass.
