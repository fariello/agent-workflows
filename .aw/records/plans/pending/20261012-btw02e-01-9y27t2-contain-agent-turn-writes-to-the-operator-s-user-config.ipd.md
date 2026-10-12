# IPD: Contain agent-turn writes to the operator's user config

- Date: 2026-10-12
- Kind: child
- Concern: Backlog `btw02e`: an `aw oc run` agent turn in lane `.aw/worktrees/cvtg9u` ran `aw config set color_depth none` against the OPERATOR'S REAL `~/.config/agent-workflows/config.json` (opencode log run `204e56ba`, 2026-10-12T09:06:22Z; file mtime the same second) and never restored it, silently decoloring every lifecycle surface for the operator. Root cause: the runner isolates the REPO (per-item worktree) but not USER STATE. `runner_shared.pinned_child_env` starts from `os.environ.copy()` and both agent-turn launchers (`oc_runipd.run_opencode`, `agy_runipd.run_agy_turn`, each `child_env = pinned_child_env()`) add only the role marker and run/item ids, so every `aw` an agent runs resolves `config.config_dir()` to the operator's real directory.
- Scope: IN: an aw-specific `AW_CONFIG_DIR` override honored FIRST by `config.config_dir()` (and the two `except` fallbacks that mirror it); a per-turn seeded copy of the operator's aw user-config directory exported to each agent turn on BOTH hosts through one shared helper; a turn-end diff that DISCARDS changes, records each as a durable run event, and prints a warning; the end-of-run report line; the conftest scrub; behavioral tests; CHANGELOG and docs. OUT: redirecting `XDG_CONFIG_HOME` itself (see Findings F-04); `AW_HOME` containment (backlog `s4pys7`); `project_context`'s hard-coded `~/.config/agent-workflows` reader (backlog `m9dobx`); `aw runs` display of discarded changes (backlog `c4q9e8`); OS-level enforcement (the hardened profile already exists and is out of this plan's scope).
- Scope-Paths: agent_workflows/config.py, agent_workflows/leak_sanitizer.py, agent_workflows/model_vocab.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, conftest.py, tests/test_agent_user_config_containment.py, CHANGELOG.md, docs/security.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: btw02e
- Blocks-Release: next
- Set: btw02e
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 9y27t2
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed; review record .aw/records/reviews/20261012-btw02e-01-9y27t2-contain-agent-turn-writes-to-the-operator-s-user-config.review.md

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog `btw02e` at the maintainer's instruction to graduate it. Resolved the design questions from repository evidence (Findings F-01..F-08); filed the out-of-scope residue as backlog `m9dobx` (bug, gates next), `s4pys7` and `c4q9e8` (followups).

## Goal

An agent turn launched by `aw oc run` or `aw agy run` can no longer change the operator's aw user configuration. It reads the operator's settings unchanged (a seeded copy), any write it makes lands in a per-turn copy that is discarded, and the operator is told, durably and at run end, which keys an agent tried to change.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline and the override

- [ ] E-01 CAPTURE THE BASELINE: run the bare suite `python3 -m pytest` BEFORE the first edit and record its summary line and the failing node ids. The post-change bar is "no node id fails that did not fail here".
  - Depends on: none
  - Expected outcome: a recorded baseline summary line and failing-node-id list.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/config.py`, add a module constant `CONFIG_DIR_ENV = "AW_CONFIG_DIR"` and make `config.config_dir()` return `Path(os.environ["AW_CONFIG_DIR"]).expanduser()` when that variable is set and non-empty, checked BEFORE `XDG_CONFIG_HOME`. The override names the aw directory ITSELF (no `agent-workflows` suffix appended), so a seeded copy can be any directory. Update the docstring (and the module docstring's location sentence) to state the precedence `AW_CONFIG_DIR` > `$XDG_CONFIG_HOME/agent-workflows` > `~/.config/agent-workflows`, and WHY a separate variable exists (F-04: overriding XDG would also relocate opencode, gh and git config). Honor the override ONLY when, after `expanduser()`, it is an ABSOLUTE path that is not `Path.home()` itself; otherwise ignore it and fall through to the XDG rule, so a stray relative value cannot follow the agent's `cd` and an `AW_CONFIG_DIR=~` cannot make `save()` write `config.json` directly under `~/` (spec `pip-distribution-and-multi-repo-setup` constraint "never write under `~/` directly"). Mirror the same precedence and the same guard in the two `except` fallbacks `leak_sanitizer._config_dir` and `model_vocab._user_config_dir`, so a broken `config` import cannot silently bypass the override. Every other user-config store (`runner_profiles.store_dir`, `completion` notice stamp, leak hints, model vocab) already routes through `config.config_dir()` and follows with no edit (F-02). `project_context.get_default_aw_home` is deliberately NOT changed: it reads `AW_HOME`/`XDG_CONFIG_HOME` directly, so `AW_HOME` resolution is identical with or without `AW_CONFIG_DIR` and the two never split across real and sandbox in a way this plan did not choose (the backlog item's `AW_HOME` caveat; containment of `AW_HOME` itself is `s4pys7`).
  - Depends on: E-01
  - Expected outcome: `AW_CONFIG_DIR=<d> aw config set color_depth 16` writes `<d>/config.json` and leaves `$XDG_CONFIG_HOME/agent-workflows/config.json` untouched; a relative value or one equal to the home directory is ignored (the XDG location is used); unset, behavior is byte-identical to HEAD.
  - Execution state: pending

### Task group 2: per-turn seeded sandbox on both hosts

- [ ] E-03 In `agent_workflows/runner_shared.py`, add one shared helper pair used by BOTH hosts (no per-host fork, the same rule the role marker and trailer ids follow): `prepare_agent_user_config(run_dir, item, attempt_no, suffix="") -> AgentUserConfig` and `reconcile_agent_user_config(handle, run_dir, item) -> list[dict]`. `prepare` resolves the operator's real directory with `config.config_dir()` evaluated in the DRIVER's environment, creates `<run_dir>/agent-user-config/<NN>-<id6>-attempt-<N>[-<suffix>]/` (under the run dir, which is gitignored `records/runs/` and never inside the lane worktree, so it cannot enter an integration diff; F-05). THE KEY MUST BE UNIQUE PER TURN, not per attempt: the executor, the verifier (`log_suffix="verify"`) and the audit turn (`log_suffix="audit"`) share one `attempt_no`, so the caller passes its `log_suffix` and the name follows `runner_shared.attempt_log_path`'s `<NN>-<id6>-attempt-<n>[-<suffix>]` shape; a directory that already exists (a defect re-ask resuming the same attempt and suffix) is removed and re-seeded rather than reused, so one turn's stale writes are never attributed to the next. The directory is mode `0o700`; `prepare` copies every regular top-level file of the real directory into it preserving mode (`shutil.copy2`, which follows a symlinked dotfile and copies its content; a missing real directory yields an empty sandbox), and records a SHA-256 per seeded file (reuse `runner_shared.sha256_file`). `reconcile` compares every regular file under the sandbox (relative path, so a write into a new subdirectory is still seen) against the seed: for each file added, removed or changed it emits a record `{event: "agent-user-config-discarded", id6, attempt, file, change: added|removed|modified, keys: [...]}`, where `file` is the path RELATIVE to the sandbox (never absolute), and `keys` lists the changed TOP-LEVEL JSON keys when both sides parse as JSON objects (so `config.json` reports `["color_depth"]`) and is omitted otherwise; values are NEVER recorded (the config holds local paths, runner-profiles may hold institution-specific model ids, and `local-leaks-hints.json` exists to hold the operator's identifying tokens; AGENTS.md leak rule). Each record is appended to `<run_dir>/events.jsonl` via `append_jsonl` and also returned. Nothing is ever copied back to the real directory. AFTER diffing, `reconcile` DELETES the sandbox directory (best effort, also on a reconcile failure): the copies hold exactly the values the events refuse to record, so keeping one per turn in every run dir would multiply the operator's private config across the run corpus for no post-mortem gain the keyed events do not already give. HARDENED PROFILE, recorded rather than widened: under `execution_profile: hardened` the run dir lies inside the INACCESSIBLE control root (`oc_runipd._apply_execution_profile` passes `control_root=... or state_root(repo_root)`), so the agent cannot reach the sandbox; that is no regression, because the real `~/.config/agent-workflows` is in none of `build_sandbox_plan`'s writable or read-only roots either, so a hardened turn already saw a default config. Both functions FAIL OPEN with a printed warning (a seeding failure must not abort a run: fall back to exporting no override and say so loudly; a reconcile failure records one `agent-user-config-reconcile-failed` event), the same advisory posture `report_run_spec_edits` takes.
  - Depends on: E-02
  - Expected outcome: two shared functions; a unit-level call seeds a copy whose hashes equal the source, a subsequent modification is reported with keys, a relative `file`, and no values, two turns of one attempt (no suffix and `verify`) get distinct directories, and the sandbox directory is gone after reconcile.
  - Execution state: pending

- [ ] E-04 Wire the helper into both launchers. In `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn`, immediately after the existing run/item-id block that builds `child_env`, call `prepare_agent_user_config(run_dir, item, attempt_no, suffix=log_suffix)` and set `child_env[config.CONFIG_DIR_ENV] = str(handle.path)`; when preparation failed, POP the variable instead (never inherit an outer run's sandbox, the same overwrite-or-pop rule as `RUN_ID_ENV`). Reconcile only AFTER the child has exited: NOT in the inner `finally` that closes `breach_watch` (on the normal path that `finally` runs when stdout ends, BEFORE `process.wait()`, so a child still exiting could write after the diff), but in a new `try`/`finally` wrapping the whole launch from the `with (runner_shared.turn_telemetry(...), log_path.open(...))` block through `process.wait()`, so the normal exit, a stall (`StallTimeout`), a stop (`StopNowForce`/`StopAtCheckpoint`), an interrupt, and a `Popen` failure all reconcile, each after the child is reaped (`clean_shutdown` already runs on the exception paths). There call `reconcile_agent_user_config` (when a handle exists) and, for each record, print one yellow stderr line `  ! IPD <id6>: agent changed user config <file> (<keys>); change DISCARDED, your config is unchanged`. Apply this to EVERY agent turn the launchers start (executor, verifier, audit, defect re-ask), isolated or not: a non-isolated turn writes the same real config. The DRIVER process is not redirected (F-06), and the driver's own short-lived spawns that do not go through these two launchers (the coverage probe `runner_shared.ask_orchestrator_probe`, `oc_runipd.observe_opencode_policy`'s `opencode debug config`, the session-export probe) are out of scope: none is an agent turn with a shell. `host_sandbox_profile`'s argv-capture probe calls these launchers with a patched `Popen` that raises before launch; the `finally` therefore reconciles and deletes its temp sandbox, which is intended.
  - Depends on: E-03
  - Expected outcome: a fake-host turn on each host receives `AW_CONFIG_DIR` pointing under the run dir, and a write by the child is reported and discarded.
  - Execution state: pending

- [ ] E-05 Add the end-of-run line beside `report_run_spec_edits` / `report_driver_committed_reviews` at the primary summary site of BOTH hosts (`oc_runipd` and `agy_runipd`, where `report_driver_committed_reviews(state)` is called): a shared `report_discarded_user_config(run_dir)` in `runner_shared.py` that reads `agent-user-config-discarded` events from `events.jsonl` and prints `Agent user-config changes discarded: <n> (<id6>: <file> <keys>; ...)`, or nothing when there are none (silence means none, matching the spec-edit report's convention). Advisory and exception-safe like its neighbors.
  - Depends on: E-04
  - Expected outcome: a run whose turn wrote user config prints the line at exit; a clean run prints nothing new.
  - Execution state: pending

### Task group 3: test hygiene, tests, docs

- [ ] E-06 In `conftest.py`, add `os.environ.pop("AW_CONFIG_DIR", None)` at import time beside the existing `AW_RUN_ID`/`AW_ITEM_ID6` scrub, with a comment: an agent turn now exports it and every plan tells that agent to run the suite, so without the scrub the suite's own `XDG_CONFIG_HOME` sandbox would be bypassed by the outer turn's value. Also add `"AW_CONFIG_DIR"` handling to `_restore_home_sandbox` by POPPING it before and after each test (not setting it), so a test that sets it cannot leak it into the next.
  - Depends on: E-02
  - Expected outcome: a suite run inside an agent turn (with `AW_CONFIG_DIR` exported) resolves `config.config_dir()` to the conftest sandbox.
  - Execution state: pending

- [ ] E-07 Add `tests/test_agent_user_config_containment.py`, behavioral only (P16: drive code, assert outputs and side effects; no source reading). Cells: (a) `AW_CONFIG_DIR` precedence: with `XDG_CONFIG_HOME=<x>` and `AW_CONFIG_DIR=<d>`, `python -m agent_workflows config set color_depth 16` as a subprocess (`AW_NO_REEXEC=1`, `PYTHONPATH` at this checkout) writes `<d>/config.json` and leaves `<x>` absent/byte-identical; unset falls back to `<x>/agent-workflows`; a relative `AW_CONFIG_DIR` and one equal to `$HOME` are both ignored (the write lands in `<x>/agent-workflows`); (b) seed fidelity: `prepare_agent_user_config` over a real dir holding `config.json` and `runner-profiles.json` yields byte-identical copies, and `aw config get color_depth` run with the exported env returns the operator's value; (c) THE INCIDENT, end to end per host: drive `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn` with the host executable replaced by a small script (option `opencode` / `agy_executable` pointing at it) that runs `python -m agent_workflows config set color_depth none`; assert the operator's real config (the test's `XDG_CONFIG_HOME`) is byte-identical afterwards, `events.jsonl` holds one `agent-user-config-discarded` record with `keys == ["color_depth"]` and no value `none` anywhere in the record, and stderr carries the DISCARDED line, and no `agent-user-config/` sandbox directory remains under the run dir; the same cell also drives a verifier-style turn (`log_suffix="verify"`) of the same attempt and asserts its event is recorded separately, not merged with the executor's; (c2) a turn whose host script exits nonzero (and one whose `Popen` raises) still reconciles: the operator config is unchanged and no sandbox directory remains; (d) overwrite-or-pop: with `AW_CONFIG_DIR=/outer` in the driver env and seeding forced to fail, the child env has no `AW_CONFIG_DIR`, and with seeding succeeding it is the new per-turn path, never `/outer`; (e) `report_discarded_user_config` prints the summary for a run dir with one event and prints nothing for none; (f) the conftest scrub: `AW_CONFIG_DIR` is absent from `os.environ` inside a test. Reuse the Popen-mock harness of `tests/test_commit_run_trailers_env.py` where a real child is not needed, and a real subprocess where the cell is about a real write (cell c).
  - Depends on: E-04, E-05, E-06
  - Expected outcome: the file passes with the change and cell (c) FAILS with E-04 reverted (demonstrated once, see V-07).
  - Execution state: pending

- [ ] E-08 Docs: add one `- Fixed:` bullet at the top of `CHANGELOG.md`'s `## 2.0.0 (pending)` list (agents run by `aw oc run`/`aw agy run` can no longer change your aw user configuration; attempted changes are discarded and reported), and add a boundary paragraph to `docs/security.md` "The boundaries" describing user-config containment, `AW_CONFIG_DIR`, and its honest limit (an environment selector, not an enforcement boundary; a same-user agent can still write `~/.config` directly or unset the variable; the hardened execution profile is the enforcement option). No em or en dashes in either (user-facing prose rule).
  - Depends on: E-04
  - Expected outcome: one CHANGELOG bullet and one security-doc paragraph, no other lines changed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- One child-env construction: both launchers build the agent env from `runner_shared.pinned_child_env()` and then overwrite-or-pop per-run variables (`ipd_lifecycle.EXECUTION_ROLE_ENV`, `git_commit_helper.RUN_ID_ENV`, `ITEM_ID6_ENV`); comments in both say the two hosts "must not drift". New per-turn env goes in the same place, through a shared helper.
- One user-config directory resolver: `config.config_dir()`; `runner_profiles.store_dir`, `completion` notice-stamp path, `leak_sanitizer._config_dir`, `model_vocab._user_config_dir` all call it.
- Advisory end-of-run reports never raise (`runner_shared.report_run_spec_edits` docstring: "an exception escaping here would replace a completed run's summary with a traceback").
- Machine-local run state lives under the gitignored `records/runs/` (`.aw/.gitignore` "awrunsignore"); lane-local machine paths are refused from integration by `lane_containment.MACHINE_LOCAL_PREFIXES`.
- Test home isolation: `conftest.py` "Home isolation" sets `AW_HOME`/`XDG_CONFIG_HOME` unconditionally and restores them per test; run-scoped env vars are scrubbed at import (`AW_EXECUTION_ROLE`, `AW_RUN_ID`, `AW_ITEM_ID6`).
- Behavioral tests only (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE", GUIDING_PRINCIPLES P16). Run the suite bare (`python3 -m pytest`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
| --- | --- | --- |
| F-01 | The incident: an agent turn wrote the operator's real config and nothing restored it. | opencode log run `204e56ba` (directory `.aw/worktrees/cvtg9u`): `AW_NO_REEXEC=1 python3 -m agent_workflows config set color_depth none >/dev/null` at 2026-10-12T09:06:22Z; real `config.json` mtime 05:06:22 local (same second); contents then `"color_depth": "none"`. |
| F-02 | All aw user stores resolve through `config.config_dir()`, so one override covers them. | `config.config_dir` ("honoring XDG_CONFIG_HOME, else ~/.config"); callers `runner_profiles.store_dir`, `completion` (`NOTICE_STAMP_FILENAME` path), `leak_sanitizer._config_dir`, `model_vocab._user_config_dir`; the last two re-derive XDG only in an `except` fallback. Exception: `project_context.resolve_project_context` hard-codes `os.path.expanduser("~/.config/agent-workflows")` (filed as `m9dobx`). |
| F-03 | The agent env is inherited wholesale. | `runner_shared.pinned_child_env`: `merged = os.environ.copy()`; `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn` each `child_env = pinned_child_env()` then set only role and trailer ids. |
| F-04 | `XDG_CONFIG_HOME` is not aw-specific; overriding it would break the turn. | It is the freedesktop base-dir variable read by opencode itself (`oc_models.py` reads `$XDG_CONFIG_HOME/opencode/opencode.json`), `gh` (`~/.config/gh`, listed in `oc_runipd._hardened_credential_paths`), git's global config, fish completions (`completion.py`). Redirecting it would strip the agent's credentials, model config and git identity. Hence an aw-only variable. Precedent for the aw-only shape: `AW_HOME` already exists alongside XDG. |
| F-05 | Where the sandbox lives. | Run dir is gitignored (`.aw/.gitignore` "records/runs/"); keeping the copy there (not in the lane) means it can never enter a lane's integration diff and survives the lane for post-mortem. Keyed by item and attempt, the same collision reasoning as `lane_containment.lane_submission_root`. |
| F-06 | The driver must keep the real config. | The driver reads policy from it (`config.py` "User config: `$XDG_CONFIG_HOME/agent-workflows/config.json` at `run.on_conflict`") and runner profiles at run creation; only agent turns are untrusted writers. |
| F-07 | Discard, do not merge back. | The backlog item's ask; also no agent turn has a legitimate reason to change operator preferences, and a merge-back would need a conflict policy for concurrent turns. Reporting keys (not values) keeps evidence leak-safe (`config.json` holds local repo paths). |
| F-09 | Turn keying and reconcile timing (added at review). | One `attempt_no` serves several turns: `oc_runipd.run_opencode` is called with `log_suffix="verify"` (verifier) and `log_suffix="audit"` beside the executor, and `runner_shared.attempt_log_path` keys logs `<NN>-<id6>-attempt-<n>[-<suffix>]` for that reason. The inner `finally` closing `breach_watch` runs when the stdout loop ends, before `returncode = process.wait()` / `rc = process.wait()`, so reconciling there can race a still-exiting child. |
| F-10 | Hardened profile cannot reach the run dir (added at review). | `oc_runipd._apply_execution_profile` passes `control_root=state.get("control_root") or state_root(repo_root)` to `build_sandbox_plan`, whose INACCESSIBLE class includes the control root; `host_sandbox_profile._default_toolchain_roots` lists no `~/.config` path, so the real aw config dir was already unreachable under hardened, and the sandbox being unreachable too is no regression. |
| F-08 | Honest limit. | Same as the role marker (`oc_runipd.run_opencode` comment: "this is an environment SELECTOR, not a hardened boundary. A same-user worker with shell access can unset it"). The hardened profile (`_apply_execution_profile`) is the enforcement path and is unchanged. |

## Proposed changes (ordered, validatable)

1. `AW_CONFIG_DIR` override in `config.config_dir()` and its two fallback mirrors (E-02).
2. Shared seed/reconcile helpers in `runner_shared` (E-03).
3. Both launchers export the per-turn path and reconcile in `finally` (E-04).
4. End-of-run discarded-change line on both hosts (E-05).
5. Conftest scrub (E-06), tests (E-07), CHANGELOG and security doc (E-08).

## Deferred / out of scope (with reason)

- `project_context` hard-coded config path: a separate pre-existing XDG bug with its own blast radius; backlog `m9dobx` (bug, Blocks-Release next).
- `AW_HOME` containment: redirecting it would break a `records_backend: home` project whose records the agent must write; needs measurement and a ruling; backlog `s4pys7`.
- `aw runs` display of discarded changes: the events are durable from this plan; surfacing them in the cross-run view is backlog `c4q9e8`.
- Redirecting `XDG_CONFIG_HOME`: rejected (F-04).
- OS-level enforcement: already offered by the hardened execution profile; unchanged.

## Scope check

- Over-scope: none. Every Scope-Path is touched by an E-item: config/leak_sanitizer/model_vocab (E-02), runner_shared (E-03, E-05), oc_runipd/agy_runipd (E-04, E-05), conftest (E-06), test file (E-07), CHANGELOG/docs (E-08).
- Under-scope: none known; residue filed as `m9dobx`, `s4pys7`, `c4q9e8`.

## Required tests / validation

- New `tests/test_agent_user_config_containment.py` (E-07), including the end-to-end incident reproduction per host.
- Existing `tests/test_commit_run_trailers_env.py` and `tests/test_config.py` must still pass (child-env and config regressions).
- Full bare suite `python3 -m pytest` against the E-01 baseline.
- `aw sanitize --agent` clean (the events must not carry values or local paths).

## Spec / documentation sync

- No spec amendment: no approved spec describes the user-config location's env precedence beyond "honor `XDG_CONFIG_HOME`" (implemented spec `pip-distribution-and-multi-repo-setup`), which still holds; `AW_CONFIG_DIR` is an additional higher-precedence override set by the runner, not a change to that contract. If a reviewer reads it as a contract change, add that spec to Scope-Paths and amend its config-location bullet.
- `CHANGELOG.md` and `docs/security.md` updated (E-08).

## Open questions

### OQ-01: Discard the agent's change, or keep it and only report?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED to DISCARD and report. The backlog item `btw02e` (filed from the maintainer's diagnosis) specifies "do NOT propagate it; report it", and F-07: no agent turn has a legitimate need to change operator preferences; an agent that needs a setting should ask the human.

### OQ-02: Override `XDG_CONFIG_HOME` or add an aw-specific variable?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED to an aw-specific `AW_CONFIG_DIR` (F-04): XDG is shared by opencode, gh, git and others in the agent's process tree, and redirecting it would remove the turn's credentials and model config.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted pre-change `python3 -m pytest` summary line and the list of failing node ids.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted shell transcript in a temp dir: with `XDG_CONFIG_HOME=<x>` and `AW_CONFIG_DIR=<d>`, `aw config set color_depth 16` then `ls <d> <x>/agent-workflows` and `cat <d>/config.json` showing the write landed only in `<d>`; then with `AW_CONFIG_DIR` unset, the same command writing `<x>/agent-workflows/config.json`; then with `AW_CONFIG_DIR=relative-dir` and with `HOME=<h> AW_CONFIG_DIR=<h>`, the same command writing `<x>/agent-workflows/config.json` and creating neither `./relative-dir/config.json` nor `<h>/config.json`. Plus the `git diff` of `config.config_dir`, `leak_sanitizer._config_dir`, `model_vocab._user_config_dir`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted output of a Python snippet calling `prepare_agent_user_config` on a temp source dir, printing the sandbox dir mode (`0o700`) and path, calling it again for the same attempt with `suffix="verify"` and printing that the two paths differ, modifying the first sandbox's `config.json` (`color_depth`), then `reconcile_agent_user_config`, showing the returned record (`keys == ["color_depth"]`, `file == "config.json"` relative, no value), the matching `events.jsonl` line, the sandbox directory no longer existing, and the source dir unchanged (hash before/after).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the passing output of E-07 cells (c), (c2) and (d) for BOTH hosts (code path: `oc_runipd.run_opencode` / `agy_runipd.run_agy_turn` -> `prepare_agent_user_config` -> child env -> `reconcile_agent_user_config` in the outer `finally` after `process.wait()`), plus the pasted stderr DISCARDED line captured by cell (c), plus the `git diff` of both launchers showing the outer `try`/`finally` placement.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted output of `report_discarded_user_config` against a run dir with one event (the summary line) and against one without (empty), plus the diff showing the call at both hosts' primary summary site beside `report_driver_committed_reviews(state)`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted output of `AW_CONFIG_DIR=/tmp/outer python3 -m pytest tests/test_agent_user_config_containment.py -o addopts="" -q -k scrub` passing (cell f), demonstrating the scrub beats an exported outer value.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted passing run of `python3 -m pytest tests/test_agent_user_config_containment.py tests/test_commit_run_trailers_env.py tests/test_config.py`; pasted FAILING run of cell (c) with E-04's launcher wiring temporarily reverted (then restored, `git diff --stat` shown); pasted post-change bare `python3 -m pytest` summary line with no node id failing that was not in V-01's list; pasted `aw sanitize --agent` result.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: `git diff CHANGELOG.md docs/security.md` pasted, showing exactly one new CHANGELOG bullet and one new security paragraph, and a pasted `grep -nP "\x{2013}|\x{2014}"` over both changed hunks returning nothing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Ready for `/plan-review`, then explicit human approval (`aw ipd set approved 9y27t2 --by-human --message ...`). Both open questions are resolved from repository evidence and the backlog item's own ask; no maintainer decision is outstanding.

Execution contract once approved:

- Resolved questions: OQ-01 and OQ-02 are resolved; nothing remains for the maintainer.
- Order: perform E-01..E-08 in dependency order.
- Scope declaration (not a stop directive): `- Scope-Paths:` declares the files this plan expects to touch. If an edit outside them proves necessary, make it and justify it at finalize with `--scope-reason <path>=<why>`; acknowledge a declared but unmodified path with `--scope-ack`. Stop and report only for a genuinely unsafe condition (an unresolvable concurrent edit to a declared file, or a cited symbol absent at HEAD).
- Honesty: paste the ACTUAL runner output into every `V-*` `Observed evidence`; never record a pass you did not observe.
- Commits: commit only the declared paths through `aw commit 9y27t2 -- <paths>`; never `git add -A`, never push, never tag.
- Lifecycle transition: when run by `aw oc run` / `aw agy run` as an isolated worker, do NOT run `aw ipd begin`/`aw ipd finalize` in the lane (the role marker refuses them); the driver finalizes after integration. When executed by hand, finish with `aw ipd finalize 9y27t2` (never a hand-rolled `git mv` to `executed/`), and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass`.
- Release gate: this plan inherits `- Blocks-Release: next` from backlog `btw02e`; the item closes `done` through the handoff once this plan is executed.
