# IPD: Phase 1: stop the deadlock and silent loss (in-lane-only worker paths, deny external+question, permission+no-progress+absolute watchdog, minimal input manifest, AW_MISSING_INPUT, clean-base check, teardown preservation)

- Date: 2026-08-28
- Kind: child
- Concern: Worktree-isolated `aw oc run` / `aw agy run` deadlocks forever on opencode's `external_directory` permission prompt (backlog qyaime) and silently loses lane work on teardown. The driver launches the agent with cwd inside the lane worktree (`--dir <worktree>`, oc_runipd.py:1713, agent_dir at :1697; agy_runipd.py:1766+) but its `build_prompt` hands the agent ABSOLUTE main-repo paths for the run directory, outcome JSON, decisions register, and report (oc_runipd.py:1461-1472, esp. the `run_dir`-derived lines at :1469-1472 which come from `state_root(repo)/run_id`, oc_runipd.py:1162; agy_runipd.py:1546+). The runbook is also attached by main-repo path (`--file state["runbook"]`, oc_runipd.py:1735). First access to any such path crosses opencode's `external_directory` gate; under `--auto` non-interactive there is no answerer, so the turn blocks in the permission socket forever (opencode issues #43888 and #36868). Research x03wgn Section 6 (permission-deadlock layered defense) and Section 8 "Phase 1" prescribe the fix; this child implements the "delivery order" items 1-2 (internal-only prompt paths + external auto-deny + permission-event timeout; clean-base check, minimal input manifest, missing-input repair without original access).
- Scope: Make every worker-facing path in the driver prompt LANE-LOCAL; deny unattended `external_directory` + `question` asks via runner-supplied opencode config; add a permission-event deadline + no-progress watchdog + absolute turn deadline that kill the process tree and record `failed-safely`; add a minimal lane input-manifest that copies the task/IPD + explicitly-referenced safe files into the lane; add the `AW_MISSING_INPUT` response contract (never auto-approve original-checkout access); require a clean tracked main checkout before an unattended integration run; inventory lane content and PRESERVE on unknown/dirty/unimported before teardown. Apply symmetrically to BOTH `oc_runipd.py` and `agy_runipd.py`. Does NOT relocate machine state out of repo (Phase 4), does NOT move lifecycle authority into the driver (Phase 2), does NOT unify the resolver (Phase 3).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/worktree_lease.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_lane_isolation_phase1.py, tests/test_permission_watchdog.py, tests/test_lane_input_manifest.py
- Item-Dependencies: executed:8zgybk
- From-Backlog: qyaime
- Blocks-Release: next
- Status: approved
- Set: wtiso
- Order: 2
- Highest E allocated: 11
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: qcqhj7
- Approval: 2026-08-29, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 /plan-review (OpenCode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007. Found TWO defects that would each have left qyaime reproducible after a "successful" Phase 1. (1) IMPOSSIBLE SEQUENCING (PR-002): E-01 required lane-relative prompt paths "when the turn is isolated", but `build_prompt` takes no `work_dir` and, verified in `execute_item`, is CALLED at oc_runipd.py:1867 and PERSISTED by `write_prompt` at :1869 - 87 lines BEFORE `allocate_isolation_worktree` at :1954. The lane does not exist when the prompt is built, so E-01 was unexecutable as written; added E-11 (numbered above the watermark per ipd-structure-and-linting 5.6, ordered first via `Depends on:`) to move allocation before prompt-build and thread `work_dir`, with V-11 asserting both the new parameter and the source-order inversion. (2) MISSED SECOND BOUNDARY CROSSING (PR-003): E-02 fixed only the runbook `--file`, but `run_opencode` emits TWO `--file` args - the runbook (:1735) and `str(plan_path)` (:1741), where `plan_path` comes from `resolve_plan_path(repo, ...)` and is an ABSOLUTE main-repo path (confirmed live). Fixing one would leave the other as an independent `external_directory` trigger; E-02 and V-02 now cover both and V-02 requires `len(file_args) >= 2`. Also: added the missing `Blocks-Release: next` (PR-001) that made this plan fire the exit-blocking `check.from-backlog-gate-mismatch` rule against its own `From-Backlog: qyaime` (verified: repo-wide drift 4 -> 3); required E-04 to CREATE the child `env` (verified `popen_kwargs` has no `env` key today, so the child inherits the parent env) and to record the OBSERVED effective policy because managed config outranks `OPENCODE_CONFIG_CONTENT` (PR-004, x03wgn R9); pinned E-05's (b) clause to the verified unconditional `watchdog.touch()` at :1776 that lets spinner noise reset the 600s bound, and directed reuse of the existing `interrupt_reason`/`failed-safely` seams (PR-005); recorded that E-09 must reuse the existing `dirty_tree_overlap` porcelain parser rather than fork a second one, with an explicit note on how whole-tree-pre-launch differs from overlap-at-integration (PR-006, contract rule 4); and corrected ~14 stale `file:line` citations against snapshot drift of ~70-80 lines, adding a citation-basis note (PR-007). OQ-01 RESOLVED as design: the nested-ask question is third-party behavior unanswerable from repo evidence (opencode 1.18.25 installed), but the E-05/E-06 bounds were VERIFIED driver-side (`terminate_process` os.killpg on a timer) hence independent of any opencode permission decision, so the phase needs the answer KNOWN and RECORDED, not correct - E-04/V-04 now require the observed effective policy or an explicit `effective_policy_unverified` marker.
- 2026-08-29 reviewed (aw set): status set to reviewed
- 2026-08-29 to-review (aw set): status set to to-review

- 2026-08-28 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Stop the live permission-deadlock (qyaime) and silent lane-loss by making every worker-facing path lane-local, denying unattended `external_directory`/`question` asks, bounding every non-interactive turn with a permission-event deadline + no-progress watchdog + absolute deadline that kill the process tree and record `failed-safely`, materializing required inputs into the lane with an `AW_MISSING_INPUT` repair contract that never grants original-checkout access, refusing a dirty tracked main before an unattended integration run, and preserving the lane on any unclassified content before teardown, symmetrically across `oc_runipd.py` and `agy_runipd.py`. Acceptance is pasted command output and observed git/filesystem/process state, never an agent's prose claim.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: lane-local worker paths (x03wgn Section 6 Layer 1, Section 8 Phase 1 item 1-2)

- [ ] E-11 PREREQUISITE SEQUENCING FIX (added at review; E-01 cannot be done without it. Numbered E-11 per ipd-structure-and-linting Section 5.6/line 202: a new leaf takes the next suffix ABOVE the allocation watermark, never a lower/unused one, even though it must EXECUTE FIRST - execution order is expressed by `Depends on:`, not by id ordering). In `oc_runipd.execute_item` (`oc_runipd.py:1852`), the lane worktree is allocated at `oc_runipd.py:1954` (`allocate_isolation_worktree` -> `work_dir`), but `build_prompt` is CALLED at `oc_runipd.py:1867` and the prompt is already persisted by `write_prompt` at `:1869` - i.e. 87 lines BEFORE the lane exists (verified at review). `build_prompt(item, state, run_dir, plan_path, recovery)` (`oc_runipd.py:1448`) also takes NO `work_dir`/lane parameter, so it currently CANNOT know the turn is isolated nor what the lane root is. Restructure `execute_item` so the isolation worktree is allocated BEFORE the prompt is built and written (moving the `if isolate:` allocation block above the `build_prompt`/`write_prompt` calls, keeping the begin-gate ordering intact), and add an explicit `work_dir: str | None = None` parameter to `build_prompt` threaded from that allocation. Apply the mirror-image restructuring in `agy_runipd.execute_item`/`build_prompt` (`agy_runipd.py:1546`). Do NOT change what the prompt says in this item - only make the lane root available at prompt-build time.
  - Depends on: none
  - Expected outcome: `inspect.signature(oc_runipd.build_prompt)` includes a `work_dir` parameter; in `execute_item` the source line index of the `allocate_isolation_worktree(` call is LESS than that of the `build_prompt(` call (assert with `inspect.getsource` index comparison) for both drivers; the existing non-isolated behavior is unchanged (`work_dir=None` reproduces today's prompt byte-for-byte).
  - Execution state: pending

- [ ] E-01 In `oc_runipd.py` `build_prompt` (`oc_runipd.py:1448`), when the turn is isolated (the `work_dir` parameter added by E-11 is set), compute the outcome JSON, decisions register, and report as paths RELATIVE to the lane worktree root (e.g. `.aw/lane/<run>/<id6>/submissions/outcome.json`) and rewrite the prompt so no absolute main-repo path (nothing under `state["repo"]`, no `run_dir = state_root(repo)/run_id` from `oc_runipd.py:1162`) appears in the emitted instructions; add a short lane contract line telling the agent this cwd is the complete authorized workspace and to never inspect parent dirs or the original checkout. The current absolute-path emissions to replace are `Plan file at launch:`, `External run directory:`, `Decisions/questions register:`, `Required JSON outcome:`, and `Driver report:` (`oc_runipd.py:1468-1472`).
  - Depends on: E-11
  - Expected outcome: for an isolated item, `build_prompt(...)` returns a string containing NO substring equal to `str(state["repo"])` and NO `state_root`/main-run absolute path; it contains the lane-relative submission path and the lane-contract sentence. For `work_dir=None` the prompt is unchanged from today.
  - Execution state: pending

- [ ] E-02 In `oc_runipd.py` `run_opencode` (`oc_runipd.py:1679`), make BOTH `--file` attachments lane-local for an isolated turn. VERIFIED AT REVIEW: `run_opencode` emits TWO `--file` arguments, not one - (i) the runbook `--file state["runbook"]` (`oc_runipd.py:1735`) and (ii) `--file str(plan_path)` (`oc_runipd.py:1741`), where `plan_path` comes from `resolve_plan_path(repo, ...)` (`oc_runipd.py:1859`) which resolves against the MAIN repo and returns an ABSOLUTE main-checkout path (confirmed live: it returned `<repo>/.aw/records/plans/pending/...ipd.md`). The plan file is therefore a SECOND `external_directory` boundary crossing and an independent deadlock trigger; fixing only the runbook would leave qyaime reproducible. Copy BOTH by value into the lane (the plan/IPD copy is the same artifact E-07's input-manifest materializes - reuse that single copy rather than copying twice) and attach the lane-local paths, so no `--file` argument names a path outside `agent_dir` (`oc_runipd.py:1697`/`:1713`). Mirror in `agy_runipd.run_agy_turn` (`agy_runipd.py:1766`).
  - Depends on: E-01
  - Expected outcome: for an isolated turn the constructed `argv` contains no `--file` value that resolves outside the lane `work_dir` - asserted over ALL `--file` values (both the runbook and the plan), i.e. `all(Path(p).resolve().is_relative_to(work_dir) for p in file_args)` with `len(file_args) >= 2`.
  - Execution state: pending

- [ ] E-03 Mirror E-01 in `agy_runipd.py` `build_prompt` (`agy_runipd.py:1546`): isolated prompt paths are lane-relative, no `state["repo"]`/main-run absolute path is emitted, and the same lane-contract sentence is present, keeping OC/AGY prompt semantics in parity.
  - Depends on: E-11, E-01
  - Expected outcome: `agy_runipd.build_prompt(...)` for an isolated item returns a string with NO `str(state["repo"])` substring and WITH the lane-relative submission path + lane-contract sentence, matching the oc_runipd assertion.
  - Execution state: pending

### Task group 2: deny unattended external_directory + question (x03wgn Section 6 Layer 1, R8/R9; issues #43888, #36868)

- [ ] E-04 Add a runner-supplied opencode permission policy (passed via `OPENCODE_CONFIG_CONTENT` in the child env, never by editing repo config) that sets `external_directory: "deny"` and `question: "deny"` for an unattended isolated turn, and wire it into `run_opencode` (`oc_runipd.py:1679`) so an unexpected external-directory or interactive-question request FAILS fast (repairable tool error) rather than blocking; add the parallel wiring in `agy_runipd.run_agy_turn` (`agy_runipd.py:1766`) via that host's config mechanism. IMPLEMENTATION NOTE (verified at review): `run_opencode`'s `popen_kwargs` currently has NO `env` key at all (`cwd`/`text`/`stdout`/`stderr`/`bufsize`, plus `start_new_session` on POSIX), so the child INHERITS the parent environment. This item must therefore CREATE the explicit child env (`os.environ.copy()` + the policy var) and pass it as `popen_kwargs["env"]`; do not assume an env dict already exists to extend. Keep inheritance of everything else so `PATH`/auth/toolchain vars are preserved. ALSO (x03wgn Section 6 Layer 1 closing sentence, R9): after launch, VERIFY the policy actually took effect rather than trusting that the env var won - opencode config precedence places managed/higher-precedence sources ABOVE `OPENCODE_CONFIG_CONTENT`, so a managed policy can silently override the deny; record the observed effective policy (or an explicit `effective_policy_unverified` marker) in the attempt record so a run cannot silently believe it is protected when it is not.
  - Depends on: E-02
  - Expected outcome: the child process environment built for an isolated `--auto` turn contains `OPENCODE_CONFIG_CONTENT` whose parsed JSON has `permission.external_directory == "deny"` and `permission.question == "deny"`, and `popen_kwargs["env"]` exists and still carries inherited `PATH`; a unit test decoding that env var asserts both values plus `"PATH" in env`; the attempt record carries the observed effective policy or the `effective_policy_unverified` marker.
  - Execution state: pending

### Task group 3: bounded execution - permission deadline + no-progress + absolute deadline (x03wgn Section 6 Layer 6)

- [ ] E-05 In `oc_runipd.py`, extend the stream/watchdog path (`run_opencode`, `oc_runipd.py:1679`; `StallWatchdog`, `oc_runipd.py:132`, instantiated at `:1769`) so that (a) a parsed permission-request event (including a nested/child-session `external_directory` ask, matching the `message=asking ... permission=external_directory patterns=["<repo-root>/*"]` line qyaime OBSERVED) starts a short permission deadline (seconds), (b) the existing no-progress watchdog is retained but resets only on meaningful events not spinner/heartbeat noise, and (c) an absolute per-turn deadline that cannot be extended by noise; on any of the three expiring, `terminate_process` (`oc_runipd.py:1632`, process-group kill via `os.killpg`) kills the whole tree and the attempt is recorded with disposition `failed-safely` and an `interrupt_reason` naming which bound fired. VERIFIED AT REVIEW (the (b) defect is real and precisely located): the stream loop calls `watchdog.touch()` UNCONDITIONALLY on every line read from stdout (`oc_runipd.py:1776`, right after `heartbeat.touch()` at `:1775`), so ANY output - including spinner/heartbeat noise - currently resets the 600s no-progress bound; (b) must gate that `touch()` on a meaningful-event predicate instead of removing it. Reuse the EXISTING `interrupt_reason` seam (already set to `"stall_timeout"` at `oc_runipd.py:2024`) and the existing `failed-safely` disposition (already in the vocabulary at `oc_runipd.py:79`) rather than inventing parallel fields.
  - Depends on: E-04
  - Expected outcome: a unit test feeding a synthetic permission event with no answer observes the process terminated within the permission-deadline window and an attempt/event record with `interrupt_reason` in {`permission_deadline`,`absolute_deadline`,`stall_timeout`} and disposition `failed-safely`, never an unbounded wait.
  - Execution state: pending

- [ ] E-06 Mirror E-05 in `agy_runipd.py` (`run_agy_turn`, `agy_runipd.py:1766`; `StallWatchdog`, `agy_runipd.py:308`) so the same three bounds + process-tree kill + `failed-safely` recording apply, keeping OC/AGY supervision in parity.
  - Depends on: E-05
  - Expected outcome: the agy unit test analogous to E-05's asserts the same bounded-kill + `failed-safely` record for a simulated unanswerable permission prompt.
  - Execution state: pending

### Task group 4: minimal lane input-manifest + AW_MISSING_INPUT + clean-base (x03wgn Section 3 lane-assembly & missing-input recovery, Section 8 Phase 1 item 3-4)

- [ ] E-07 Add a minimal lane input-materializer used at worktree allocation that copies the task/IPD snapshot and the runbook (and any explicitly-referenced safe files) into the lane at lane-local paths, writes a read-only `input-manifest.json` recording each entry (repo_relative_path, class, source_digest, materialization=copy, worker_policy), and NEVER symlinks/hard-links back to the original checkout; place it in `oc_runipd.py` and reuse it from `agy_runipd.py`.
  - Depends on: E-02
  - Expected outcome: after materializing a lane, the lane contains the IPD + runbook copies and an `input-manifest.json` whose entries all have `materialization == "copy"` and a `source_digest`; a unit test asserts no manifest entry is a symlink and every listed lane file exists with a matching digest.
  - Execution state: pending

- [ ] E-08 Define the `AW_MISSING_INPUT:<repo-relative-path>:<why>` response contract in the lane prompt and a driver-side classifier: on that signal (or a denied `external_directory` event pointing into the original checkout) the driver PRESERVES/pauses the lane, resolves the path only in coordinator code, REJECTS control paths / sibling lanes / secrets / paths outside the checkout, and if policy permits copies a digest-verified snapshot into the lane; it NEVER auto-approves the live original-checkout path. Reuse `worktree_lease.path_is_worker_forbidden` (worktree_lease.py:208) / `FORBIDDEN_WORKER_PATH_HINTS` (worktree_lease.py:199) for the reject set.
  - Depends on: E-07
  - Expected outcome: a unit test drives the classifier with (i) a safe missing repo-relative file -> a verified lane copy is created and NO live-grant is emitted, and (ii) a forbidden path (control root / sibling lane) -> classifier returns reject and creates no copy and no live grant.
  - Execution state: pending

- [ ] E-09 Add a pre-launch clean-base guard: before an unattended isolated integration run, require the target checkout to have no tracked staged or unstaged changes (a `git status --porcelain` on tracked paths must be empty); on a dirty tracked main, FAIL before agent launch with a precise message rather than silently launching a lane from `HEAD` that omits the uncommitted content. Wire into both drivers' run-item path. RELATIONSHIP TO EXISTING CODE (verified at review; contract rule 4 - do not fork a rule): both drivers ALREADY have `dirty_tree_overlap(repo, changed_files)` (`oc_runipd.py:516`, `agy_runipd.py:658`, from driverfin-03) which parses `git status --short --untracked-files=all` and returns dirty paths INTERSECTED with an incoming lane's changed files, used at INTEGRATION time to refuse clobbering. That is a DIFFERENT question from this guard (whole-tree tracked-cleanliness, checked PRE-LAUNCH, before any changed-file set exists), so this is a complementary check, NOT a duplicate. Implement it by EXTRACTING/REUSING the existing porcelain-parsing helper (including its `orig -> dest` rename handling) rather than writing a second independent parser, and state in the code comment how the two differ so a later reader does not collapse them.
  - Depends on: none
  - Expected outcome: a unit test with a dirty tracked file in the target checkout observes the run refused BEFORE any agent process is spawned, with a message naming the dirty tracked paths; the same test with a clean tracked checkout proceeds.
  - Execution state: pending

### Task group 5: teardown preservation (x03wgn Section 8 Phase 1 item 7, Section 2 retention table)

- [ ] E-10 Before `teardown_isolation_worktree` (`oc_runipd.py:463` -> `worktree_lease.teardown_worktree(..., force=True)`, `worktree_lease.py:106`; `agy_runipd.py:585`), inventory lane content (`git status --porcelain` + explicit untracked/ignored enumeration) and PRESERVE the worktree+branch (skip force-teardown, record a `worktree-preserved` event) when any of these hold: unknown untracked/ignored content, dirty tracked files, an unimported lane submission, an unresolved transaction, or an unrecorded commit; only classified/clean lanes may be torn down. Apply symmetrically in both drivers.
  - Depends on: E-07
  - Expected outcome: a unit test with an unknown untracked file in a lane observes teardown REFUSED (worktree dir still exists, a `worktree-preserved` event is recorded); a companion test with a fully-classified clean lane observes teardown proceeds.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The two host drivers are deliberate near-parity twins: `oc_runipd.py` and `agy_runipd.py` share function shapes (`build_prompt`, `StallWatchdog`, `run_opencode`/`run_agy_turn`, the driverfin-02 worktree block, `sync_receipt_into_worktree`, `teardown_isolation_worktree`). Any Phase-1 change MUST land in both to avoid drift.
- Worktree isolation already exists (driverfin-02 / emus4n): each execute child runs on branch `aw/lane/<id6>` in `.aw/worktrees/<id6>` via `worktree_lease.allocate_worktree(repo, id6, base_commit="HEAD")` (oc_runipd.py:452-460). The lane cwd is passed as `--dir` (oc_runipd.py:1713) and `cwd` (oc_runipd.py:1752 `popen_kwargs["cwd"]`). The bug is purely that the PROMPT and runbook `--file` still name main-repo paths.
- Process-group kill already exists: `terminate_process` uses `os.killpg` with SIGINT->SIGTERM->SIGKILL (oc_runipd.py:1632+) and `start_new_session=True` (oc_runipd.py:1760). Phase 1 reuses it as the kill primitive for the new deadlines.
- A no-progress `StallWatchdog` (default 600s, oc_runipd.py:132; `DEFAULT_STALL_TIMEOUT` at :1629) already exists and must be RETAINED as a backstop, not replaced (x03wgn Section 9 finding 4).
- `worktree_lease.FORBIDDEN_WORKER_PATH_HINTS` (worktree_lease.py:199) + `path_is_worker_forbidden` (worktree_lease.py:208) already encode a worker-forbidden path set; reuse it for the `AW_MISSING_INPUT` reject list rather than duplicating rules (anti-greenwash contract point 4: one predicate library).
- Tests are `unittest`-style under `tests/`, launching the driver as `python3 -m agent_workflows.oc_runipd` with `PYTHONPATH` pinned to `REPO_ROOT` (tests/test_oc_runipd.py header). New tests follow that convention.

## Findings

CITATION BASIS (added at review): every `file:line` reference below and in the E-items was RE-VERIFIED against the current working tree on 2026-08-29 and corrected where it had drifted. The research report cites the pinned snapshot `8d1bcd5` (its R1 references) and `agent_workflows/oc_runipd.py` has since grown by roughly 70-80 lines above most cited regions (e.g. `build_prompt` 1375 -> 1448; `run_opencode` 1606 -> 1679; the runbook `--file` 1663 -> 1735; `terminate_process` 1559 -> 1632; `StallWatchdog` 124 -> 132; `state_root` 1143 -> 1162; `teardown_isolation_worktree` 455/459 -> 463; `agy_runipd.build_prompt` 1483 -> 1546; `run_agy_turn` 1703 -> 1766; `agy StallWatchdog` 296 -> 308). Every BEHAVIORAL claim was re-confirmed true against live code. Anchor on SYMBOL NAMES (stable) and treat line numbers as secondary - this Phase edits these very modules, so the numbers will move again during execution; re-verify with `grep -n '<symbol>'`.

| # | Finding | Evidence (x03wgn section + real file:line + issue) |
|---|---|---|
| F1 | The prompt hands the isolated agent absolute main-repo paths (run dir, outcome, decisions, report), which is the direct cause of the `external_directory` deadlock. | x03wgn Section 6 Layer 1 ("The generated prompt names only paths under the lane worktree"); oc_runipd.py:1468-1472 (`Plan file at launch`/`External run directory`/`Decisions...register`/`Required JSON outcome`/`Driver report`), oc_runipd.py:1162 (`state_root`); agy_runipd.py:1546+. |
| F2 | The runbook is attached by main-repo path, a second external boundary crossing. | x03wgn Section 3 lane-assembly item 2 ("Rewrite prompt references to lane-relative paths"); oc_runipd.py:1735 (`--file state["runbook"]`) AND oc_runipd.py:1741 (`--file str(plan_path)`, a SECOND main-repo crossing). |
| F3 | `--auto` non-interactive has no answerer, so an `external_directory` ask blocks forever; documented intent must not be the only defense. | x03wgn Section 6 Layer 1 & Layer 6; opencode issue #43888 (non-interactive `opencode run` hangs on a subagent `external_directory` ask), opencode issue #36868 (`--auto` hangs when a Task subagent requests permission); backlog qyaime OBSERVED line. |
| F4 | The existing 600s stall watchdog is a coarse backstop; a seconds-scale permission deadline + absolute deadline + child-session event parsing are needed. | x03wgn Section 6 Layer 6 ("Permission-request deadline: seconds, not minutes"; "No-progress watchdog: resets only on meaningful events"; "Absolute turn deadline"); oc_runipd.py:132 (class), :1769 (instantiation), :1776 (unconditional `touch()`); x03wgn Section 9 finding 4. |
| F5 | A dirty tracked main is silently omitted from a `HEAD`-based lane; the recommended integration mode must require clean tracked main. | x03wgn Section 3 lane-assembly item 1 ("For unattended integration, require the target checkout to have no tracked staged or unstaged changes"); Section 8 Phase 1 item 3. |
| F6 | Required inputs must be materialized by copy with a sealed manifest; missing inputs get `AW_MISSING_INPUT` repair, never a live original-checkout grant. | x03wgn Section 3 "Lane assembly" (manifest entry shape) + "Missing-input recovery without original-checkout access"; Section 8 Phase 1 item 4. |
| F7 | Teardown currently force-removes the worktree; unknown/dirty/unimported content must PRESERVE the lane. | x03wgn Section 2 retention table (`unknown` -> "Worktree and branch remain preserved"); Section 8 Phase 1 item 7; oc_runipd.py:463 / worktree_lease.py:106 (`force=True`). |
| F8 | Both host drivers must change symmetrically. | x03wgn Section 8 Phase 1 (applies to the runner generally); oc_runipd.py + agy_runipd.py parity (near-identical `build_prompt`/watchdog/teardown blocks); backlog qyaime FIX "Apply to BOTH oc_runipd.py and agy_runipd.py". |

## Proposed changes (ordered, validatable)

1. E-01/E-03: lane-local prompt paths + lane-contract sentence in both drivers' `build_prompt`.
2. E-02: attach runbook by lane-local copy, not main-repo `--file`.
3. E-04: deny `external_directory` + `question` via `OPENCODE_CONFIG_CONTENT` for unattended isolated turns (and the agy equivalent).
4. E-05/E-06: permission deadline + retained no-progress watchdog + absolute deadline -> process-tree kill + `failed-safely`, in both drivers.
5. E-07: minimal lane input-materializer + sealed `input-manifest.json` (copy-only, digested).
6. E-08: `AW_MISSING_INPUT` contract + coordinator-only classifier reusing `path_is_worker_forbidden`.
7. E-09: pre-launch clean-tracked-main guard for unattended integration.
8. E-10: pre-teardown lane inventory + preserve-on-ambiguity in both drivers.

## Deferred / out of scope (with reason)

- Moving lifecycle authority (driver-created receipts, worker-role verb refusal, OBSERVED-from-git) into the driver: Phase 2 (child rchpms).
- The typed `ExecutionContext`/`PathResolver` + AST guard: Phase 3 (child 7p9n2v).
- Relocating machine state out of repo (`.aw/state` may temporarily remain under the main checkout's ignored `.aw/`, per x03wgn Section 8 Phase 1 closing note): Phase 4 (child 58ha43).
- Real candidate-merge integration + full recovery + cross-platform locks: Phase 5 (child 2c122z).
- OS-sandbox hard mode: Phase 6 (child 1o4eif).
- The five-way output classifier + verified artifact harvest beyond preserve-on-ambiguity: Phase 2 (this child only PRESERVES on ambiguity; it does not implement the full harvest).

## Scope check

- Over-scope: none. Every E-item is a Phase-1 delivery-order item (x03wgn Section 8 Phase 1 / delivery order 1-2). No Phase 2-6 authority/resolver/relocation work is done here.
- Under-scope: none. All three mandatory adversarial guards (lane-local no-external-prompt turn, watchdog-killed unanswerable prompt, missing-input safe-copy without live grant) are covered by E-05/E-08 and their V-items, and both drivers are changed.

## Required tests / validation

- New adversarial tests (named exactly): `tests/test_lane_isolation_phase1.py::test_isolated_turn_has_no_main_repo_path`, `tests/test_permission_watchdog.py::test_unanswerable_permission_prompt_is_killed_and_failed_safely`, `tests/test_lane_input_manifest.py::test_missing_input_yields_safe_copy_not_live_grant` and `::test_forbidden_missing_input_is_rejected`, plus `tests/test_lane_isolation_phase1.py::test_teardown_preserves_unknown_lane_content` and `::test_dirty_tracked_main_refused_before_launch`. Agy parity assertions extend `tests/test_agy_runipd_cli.py`; oc assertions extend `tests/test_oc_runipd.py`.
- Full-suite regression: `python3 -m pytest -p no:randomly -q` must stay green. Paste ACTUAL output.

## Spec / documentation sync

- N/A for a spec doc in Phase 1. The behavior change is captured by the new tests and the backlog qyaime item, which child rchpms/58ha43 later reference; no tracked spec file is authored here (would be premature before the resolver/lifecycle phases). If a `permission policy` doc is warranted it is deferred to Phase 2 with reason: the policy shape may change when lifecycle authority moves into the driver.

## Open questions

### OQ-01: Does the supported opencode version honor `permission.external_directory: "deny"` under `--auto` for NESTED/subagent asks, or only the root session?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: RESOLVED AS DESIGN, with the empirical answer converted from an open unknown into a REQUIRED execution-time measurement (reviewer resolution 2026-08-29). The question cannot be answered from repository evidence - it is behavior of a third-party binary (installed version verified at review: opencode `1.18.25`) across versions, which is precisely why x03wgn Section 9 Q1 lists it as "verify before implementation is complete" rather than a design choice. Two facts make it non-blocking rather than pending: (1) VERIFIED INDEPENDENCE - the E-05/E-06 bounds are enforced entirely DRIVER-SIDE by `terminate_process` (`oc_runipd.py:1632`) using `os.killpg` on a timer in the driver process, so they fire regardless of any opencode-side permission decision; the backstop does not depend on the answer. (2) DEFENCE IN DEPTH BY CONSTRUCTION - E-01/E-02/E-03 remove the main-repo paths that trigger the ask at all, so the deny policy is the second layer and the watchdog the third. Therefore this phase does NOT need the answer to be correct, it needs the answer to be KNOWN and RECORDED: E-04 now requires the run to verify and record the OBSERVED effective policy (or an explicit `effective_policy_unverified` marker) in the attempt record, and V-04 requires that recorded value as pasted evidence. If execution observes that a nested ask is NOT denied, that is a legitimate, documented outcome of this phase (the watchdog still bounds the turn) and becomes input to Phase 6's hard-mode profile (child 1o4eif) - not a reason to block Phase 1.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-11 validates E-11
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_lane_isolation_phase1.py -k prompt_built_after_lane_allocation` exits 0 showing `passed`. The test must prove the SEQUENCING fix two ways for BOTH drivers: (i) `"work_dir" in inspect.signature(oc_runipd.build_prompt).parameters` (and the agy equivalent), and (ii) inside `inspect.getsource(oc_runipd.execute_item)`, the character/line index of `allocate_isolation_worktree(` is LESS than the index of `build_prompt(` - i.e. the lane exists before the prompt is built (at review the order was the REVERSE: `build_prompt` at oc_runipd.py:1867 and `write_prompt` at :1869 ran 87 lines BEFORE `allocate_isolation_worktree` at :1954). Also assert the non-isolated path is unchanged: with `work_dir=None` the prompt equals today's output for the same inputs.
  - Observed evidence:
  - Result: pending

- [ ] V-01 validates E-01
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_lane_isolation_phase1.py::test_isolated_turn_has_no_main_repo_path` exits 0; the pasted output shows `1 passed`. The test builds an isolated item, calls `oc_runipd.build_prompt`, and asserts `str(state["repo"]) not in prompt` AND the lane-relative submission path + lane-contract sentence are present.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_lane_isolation_phase1.py -k runbook_lane_local` exits 0 showing `passed`; the test asserts that for an isolated turn EVERY `--file` value in the constructed argv resolves under `work_dir` (`Path(p).resolve().is_relative_to(work_dir)` is True for all) AND that at least TWO `--file` values were checked (`len(file_args) >= 2`), so the assertion provably covers BOTH the runbook (`oc_runipd.py:1735`) and the plan/IPD (`oc_runipd.py:1741`, whose `plan_path` is a `resolve_plan_path`-produced ABSOLUTE main-repo path). Neither the runbook main-repo path nor the main-repo plan path may appear. A test that only inspects one `--file` value does NOT satisfy this V-item.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_agy_runipd_cli.py -k isolated_no_main_repo_path` exits 0 showing `passed`; the test asserts `str(state["repo"]) not in agy_runipd.build_prompt(...)` for an isolated item and that the lane-relative submission path + lane-contract sentence match the oc_runipd form.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_permission_watchdog.py -k config_denies_external_and_question` exits 0 showing `passed`; the test decodes the child env `OPENCODE_CONFIG_CONTENT` built for an isolated `--auto` turn and asserts `json.loads(env["OPENCODE_CONFIG_CONTENT"])["permission"]["external_directory"] == "deny"` and `["question"] == "deny"`, AND that `popen_kwargs["env"]` was created with inherited `PATH` preserved (it does not exist today - verified at review that `popen_kwargs` has no `env` key, so this proves the env was actually constructed rather than assumed). PLUS the OQ-01 closure evidence: paste the recorded OBSERVED effective policy (or the explicit `effective_policy_unverified` marker) from the attempt record, and state the opencode version it was measured against. A run that neither observes the effective policy nor records the unverified marker does NOT satisfy this V-item, because it would leave the run silently believing it is protected when a managed/higher-precedence config may have overridden the deny (x03wgn Section 6 Layer 1 closing sentence, R9).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_permission_watchdog.py::test_unanswerable_permission_prompt_is_killed_and_failed_safely` exits 0 showing `passed`. The test feeds a synthetic `permission=external_directory` event with no answer, asserts the process is terminated within the permission-deadline (bounded, not the 600s stall), and that the recorded attempt has `disposition == "failed-safely"` with `interrupt_reason` in {`permission_deadline`,`absolute_deadline`,`stall_timeout`}. ADVERSARIAL guard (b): proves an unanswerable prompt is killed, never awaited.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_permission_watchdog.py -k agy_unanswerable_prompt_killed` exits 0 showing `passed`; the agy-parity test asserts the same bounded process-tree kill + `failed-safely` record for a simulated unanswerable prompt in `agy_runipd.run_agy_turn`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_lane_input_manifest.py -k manifest_copies_and_digests` exits 0 showing `passed`; the test materializes a lane, then asserts (i) the lane contains IPD + runbook copies, (ii) `input-manifest.json` exists and every entry has `materialization == "copy"` and a non-empty `source_digest`, (iii) no manifest-listed lane path is a symlink (`os.path.islink(p) is False` for all).
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_lane_input_manifest.py::test_missing_input_yields_safe_copy_not_live_grant tests/test_lane_input_manifest.py::test_forbidden_missing_input_is_rejected` exits 0 showing `2 passed`. The safe-copy test drives `AW_MISSING_INPUT:<safe relative path>:need it` and asserts a digest-verified lane copy is created and NO live-grant/external-approval is emitted; the reject test drives a forbidden path (control root / sibling lane, matched by `worktree_lease.path_is_worker_forbidden`) and asserts the classifier returns reject with no copy and no grant. ADVERSARIAL guard (c): missing input never becomes a live original-checkout grant.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_lane_isolation_phase1.py::test_dirty_tracked_main_refused_before_launch` exits 0 showing `passed`; with a dirty tracked file in the target checkout the test asserts the run is refused BEFORE any agent subprocess is spawned (spawn is patched and asserted never-called / a `DriverError` is raised naming the dirty tracked path), and with a clean tracked checkout it proceeds.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_lane_isolation_phase1.py::test_teardown_preserves_unknown_lane_content` exits 0 showing `passed`; with an unknown untracked file in the lane the test asserts `teardown` was REFUSED (the worktree directory still exists after the teardown call and a `worktree-preserved` event is recorded), and a companion clean-lane assertion shows teardown proceeds. Plus paste the full-suite `python3 -m pytest -p no:randomly -q` result showing no regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: one live-failure surface (the isolated worker-path/permission-deadlock/silent-loss class) fixed as a single coordinated Phase-1 cut across the two twin host drivers; the E-items are interdependent facets of that one fix (lane-local paths enable the deny policy; the deny policy needs the watchdog backstop; the manifest enables the missing-input contract and teardown preservation) and are not independently shippable without leaving the deadlock partially open, so they are one cohesive exception rather than separable standard plans.

This child inherits the Set's shared anti-greenwash execution contract from orchestrator bl9q3d verbatim:

1. **Prose is never evidence.** No E-item is complete on an assertion. Each E-item names ONE observable action; each paired V-item names FALSIFIABLE evidence: an exact command to run plus the specific string/exit-code/file-state that must appear. "Tests pass", "done", "verified", "should work" are forbidden as evidence.
2. **Paste real output (HARD MUST).** Every V-item's Observed evidence MUST be the ACTUAL pasted stdout/stderr + exit code of the named command, run in this repo at execution time. Fabricated, summarized, remembered, or "expected" output is a validation failure and a GP2 honesty violation. A V-item whose command was not run stays `Result: pending`.
3. **Adversarial acceptance is mandatory.** Because this Set is ABOUT untrustworthy agents, each child MUST include at least one adversarial test proving the guard fires: a test that a wrong/forgetful/lying behavior is DETECTED and BLOCKED (e.g. a fabricated outcome.json does not mark success; a stale/forked receipt is refused; an unanswerable permission prompt is killed, not awaited). Green-path-only tests are insufficient and are an UNDER-SCOPE finding.
4. **Determinism over model judgment.** Where a check can be a pure function + unit test (path resolution, receipt validity, scope reconciliation, retention classification), it MUST be, and the hook/driver/verifier MUST call the SAME predicate library so rules cannot drift.
5. **Scope fence.** Touch ONLY the child's declared Scope-Paths. Do not edit sibling children, this orchestrator, or product code outside scope. If the work seems to need more, STOP and report - do not silently broaden.
6. **Path-scoped commits, never push.** `git commit -m msg -- <paths>`; never `git add -A`/bare/`-a`; never push; never `--no-verify`.
7. **Lifecycle move is a POST-gate step.** Verify every V-item with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed. (NOTE: until wtiso-03 lands, finalize may hit xmqv5l; if so, record substantially-complete honestly rather than forcing.)
8. **Cite the research.** Each child's Findings section MUST cite the exact x03wgn section(s) it implements (research doc 20260828-wtiso-00-x03wgn) so a reviewer can check fidelity to the approved design.

Post-gate lifecycle move: after every V-item shows pasted passing evidence and the full suite is green, run `aw ipd lint --phase pre-transition` on this file, then `aw ipd finalize` it (honoring the contract note about xmqv5l until wtiso-03 lands). Commit ONLY the Scope-Paths files, path-scoped, never push. The three mandatory adversarial guards (V-05 unanswerable-prompt-killed, V-08 missing-input-safe-copy-not-live-grant, and V-01 lane-local-no-external-prompt) must each show pasted passing output before this plan may move to executed/.
