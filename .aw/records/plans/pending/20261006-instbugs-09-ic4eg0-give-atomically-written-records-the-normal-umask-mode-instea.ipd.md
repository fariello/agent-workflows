# IPD: Give atomically written records the normal umask mode instead of owner-only 0600

- Date: 2026-10-06
- Kind: child
- Concern: Defect D11 of research report `l6cbbb`, present at HEAD `474b037a9`. `artifact_core.atomic_write` writes through `tempfile.mkstemp(dir=..., prefix=prefix, suffix=".md")` and `os.replace`; `mkstemp` creates the file 0600 regardless of umask and `os.replace` keeps that mode, so every tracked record written this way is owner-only. In the scratch target under umask 022, both `aw research new --apply` and `aw adopt --apply` produced `-rw-------` files, while the generated `INDEX` files (written another way) were `-rw-r--r--`. A 0600 tracked file is committed with mode 100644 by git but stays unreadable to other local users and to tooling running as another uid on a shared checkout. The same `mkstemp` pattern appears in many modules; `run_analytics_report` already documents the trap ("`mkstemp` hardcodes 0o600 and `os.replace` preserves it") and fixes it locally.
- Scope: IN: give `artifact_core.atomic_write` a mode rule: a NEW file gets `0o666 & ~umask`, a REPLACED file keeps its existing mode; audit every other `mkstemp` site in `agent_workflows/` and classify each as TRACKED-RECORD (should follow the same rule, switch it to the shared helper or apply the rule) or PRIVATE (lock files, caches, credentials-adjacent or per-user state that should stay 0600, left alone with a one-line comment saying so); tests. OUT: changing modes of files already on disk (a tracked file's committed mode is unaffected; users can `chmod` existing 0600 files, and the plan notes the one-liner in its evidence); git's own mode bits.
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/ipd_lifecycle.py, agent_workflows/manifest.py, agent_workflows/layout_inventory.py, agent_workflows/project_layout.py, agent_workflows/work_cmd.py, agent_workflows/workflow_cli.py, agent_workflows/comms_broker.py, agent_workflows/comms_acks.py, agent_workflows/runner_shared.py, agent_workflows/run_analytics_report.py, tests/test_atomic_write_mode.py
- Item-Dependencies: none
- Status: to-review
- Blocks-Release: f33nrj
- Work-Kind: bug
- Priority: medium
- Set: instbugs
- Order: 9
- Highest E allocated: 04
- Author: antigravity/claude-opus-5.5
- Id: ic4eg0

## Workflow history
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0

- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 09 of Set `instbugs` after measuring `-rw-------` on files from `aw research new --apply` and `aw adopt --apply` in a scratch target under umask 022 and listing every `mkstemp` caller in `agent_workflows/`.

## Goal

Records the tool writes into a repository get the same permissions any normal editor would give them (umask-derived for new files, preserved for existing ones), while genuinely private state keeps owner-only permissions on purpose.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD: in a temp repo with an installed `.aw` layout and `umask 022`, run `aw research new --apply` and `aw adopt --apply` on a dropped inbox file, and `aw ipd new` (or the plan scaffold verb); paste `stat -c '%a %n'` for each created file. STOP and report if they are already 644.
  - Depends on: none
  - Expected outcome: the 600 modes pasted with the HEAD sha.
  - Execution state: pending

### Task group 2: fix

- [ ] E-02 In `artifact_core.atomic_write`, after writing the temp file and before `os.replace`, `os.chmod` it to the existing target's mode (`stat.S_IMODE(os.stat(path).st_mode)`) when the target exists, else to `0o666 & ~current_umask` (read the umask without a race-prone global flip where possible; the `run_analytics_report` fix is the in-repo precedent to reuse or lift into a shared helper).
  - Depends on: E-01
  - Expected outcome: new files written by `atomic_write` are 644 under umask 022 and 664 under umask 002; a pre-existing 640 file stays 640 after rewrite.
  - Execution state: pending

- [ ] E-03 Audit every other `mkstemp` caller (at HEAD: `commit_lock`, `comms_acks`, `comms_broker`, `completion`, `config`, `ipd_lifecycle`, `lane_containment`, `layout_inventory`, `leak_sanitizer`, `manifest`, `oc_models`, `project_layout`, `project_registry`, `run_analytics_report`, `runner_profiles`, `runner_shared`, `runner_stop`, `work_cmd`, `workflow_cli`). For each, record in the plan evidence a table row: module, function, what it writes, TRACKED-RECORD or PRIVATE, action. TRACKED-RECORD sites route through `atomic_write` or apply the same mode rule; PRIVATE sites keep 0600 and gain a one-line comment stating it is intentional. Only modules that change are committed; Scope-Paths lists the modules expected to hold tracked-record writers and is amended in the evidence if the audit finds otherwise.
  - Depends on: E-02
  - Expected outcome: a complete classification table; no tracked-record writer still yields 0600.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-04 Add `tests/test_atomic_write_mode.py`: under a forced `umask 022` in a subprocess, (a) `aw research new --apply` creates a 644 file; (b) `aw adopt --apply` creates a 644 file; (c) `aw ipd` plan creation and an `aw ipd set` lifecycle move yield 644; (d) a record chmodded to 640 and then rewritten by a verb stays 640; (e) under `umask 002` a new record is 664. Prove (a) can fail by removing the chmod from `atomic_write` and pasting the failure.
  - Depends on: E-03
  - Expected outcome: the new tests pass; the mutation fails; assertions are on file modes produced by real CLI runs.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `artifact_core.atomic_write` is the shared writer for records created by the research, adopt and plan verbs.
- `run_analytics_report` already carries the comment "`mkstemp` hardcodes 0o600 and `os.replace` preserves it, so a published bundle would be ..." and a local fix; that is the precedent.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | `atomic_write` creates 0600 files. | `artifact_core.atomic_write`: `fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=prefix, suffix=".md")` then `os.replace` |
| F-02 | Research and adopt records are owner-only. | scratch target, umask 022: `-rw-------` for the `aw research new --apply` and `aw adopt --apply` outputs; INDEX files `-rw-r--r--` |
| F-03 | The trap is known and fixed in one place. | `run_analytics_report` comment "`mkstemp` hardcodes 0o600 and `os.replace` preserves it" |
| F-04 | Many other `mkstemp` callers exist, some private by design. | `grep -rln mkstemp agent_workflows/` lists 20 modules including `commit_lock` and `config` |

## Proposed changes (ordered, validatable)

1. Mode rule in `atomic_write` (E-02).
2. Per-site audit and classification (E-03).
3. Behavior tests with mutation proof (E-04).

## Deferred / out of scope (with reason)

- Repairing modes of existing 0600 files on disk: not the tool's file to silently chmod; the evidence records `find .aw/records -type f -perm 600 -exec chmod 644 {} +` as a user-run remedy.
  - Carrier: none (user-run one-liner recorded in V-03 evidence)
- The whole-Set regression that checks research composition modes end to end.
  - Carrier: kck7a5

## Scope check

- Over-scope: none.
- Under-scope: none; private files are explicitly classified and left 0600.

## Required tests / validation

- `tests/test_atomic_write_mode.py` (E-04) with the mutation proof.
- Bare `python3 -m pytest` summary line pasted against a pre-edit baseline.

## Spec / documentation sync

- N/A: no spec states record file modes.

## Open questions

### OQ-01: Should replaced files be reset to the umask mode or keep their mode?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: keep the existing mode. That is what an in-place editor does, it respects a user's deliberate chmod, and it avoids widening a file someone narrowed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the pre-edit `stat -c '%a %n'` lines with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the same `stat` lines post-edit (644), plus the 640-preserved and umask-002 (664) checks.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the complete classification table (one row per `mkstemp` site) and the user-run chmod one-liner.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the narrowed run of the new test file, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one mode rule applied at one shared writer, plus the audit that keeps the rule consistent across the other writers.

EXECUTION CONTRACT. Execute E-items in order. Commit only files changed for this plan through `aw commit ic4eg0 -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first. Run the suite BARE as `python3 -m pytest` and paste the actual summary line. On completion move the plan to `executed/` with `aw ipd set executed ic4eg0`.
