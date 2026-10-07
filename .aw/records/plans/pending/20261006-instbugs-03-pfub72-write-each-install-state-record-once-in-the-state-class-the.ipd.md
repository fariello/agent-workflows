# IPD: Write each install state record once, in the state class the spec names, with the real version

- Date: 2026-10-06
- Kind: child
- Concern: Defect D05 of research report `l6cbbb` plus a new defect N2 found while reproducing it, both present at HEAD `474b037a9`. D05: a fresh scratch install contains BOTH `.aw/state/install.json` and `.aw/state/durable/install.json`, and BOTH `.aw/state/history/installs.jsonl` and `.aw/state/durable/history/installs.jsonl`. Two writers produce them: `install_history.record_install_history` (called from `cli.py` after every install, writing under the LOGICAL `state` root `ctx.logical_roots["state"]`, i.e. `.aw/state/`), and `install_wizard.persist_project_policy` steps 3 and 4 (writing under `durable_state_dir`). Spec `kw5y2s` Section 3.3 puts install receipts and history under `state/durable/` and runtime material under `state/runtime/`; nothing belongs at the `state/` root. N2: `persist_project_policy` step 3 writes `"installed_version": "2026.8.10"` as a LITERAL, and writes `policy.to_dict()` unredacted (including `aw_home`, an absolute home path), whereas `record_install_history` redacts through `_redact_details`.
- Scope: IN: one writer for the install snapshot and the install history, writing under `state/durable/` (`install.json`, `history/installs.jsonl`); the snapshot carries the running version (`agent_workflows.__version__`) and no absolute home path; `persist_project_policy` stops writing state (it keeps writing `config/project.json` and `config/local.json`); an upgrade migrates any root-level `state/install.json` and `state/history/installs.jsonl` into `state/durable/` (merging history lines without duplication) and removes the root copies; readers (`config._find_install_history_cutover`) read the durable path first and keep the legacy root as a fallback. OUT: the git policy of `state_durable` (Order 02 `gi1w75`); what is staged (Order 04 `gzsfqn`); any other `state/runtime/` producer.
- Scope-Paths: agent_workflows/install_history.py, agent_workflows/install_wizard.py, agent_workflows/config.py, agent_workflows/engine.py, tests/test_install_state_records.py
- Item-Dependencies: executed:gi1w75
- Status: to-review
- Work-Kind: bug
- Priority: high
- Set: instbugs
- Order: 3
- Highest E allocated: 05
- Author: antigravity/claude-opus-5.5
- Id: pfub72

## Workflow history

- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 03 of Set `instbugs` after reproducing D05 in a scratch target at HEAD `474b037a9` and finding N2 while tracing the two writers.

## Goal

Each install leaves exactly one install snapshot and one append-only history under `.aw/state/durable/`, carrying the real version and no machine-identifying absolute path, so the state tree matches the spec and a single ignore rule covers it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD: fresh `aw install . --preset private-target -y --no-interactive` into a temp git repo (with `AW_NO_REEXEC=1`), then `find .aw/state -type f | sort`, `cat .aw/state/durable/install.json`, and `python3 -m agent_workflows check-local-leaks .aw/state --agent`.
  - Depends on: none
  - Expected outcome: pasted evidence of the four files, the literal `"installed_version": "2026.8.10"`, and any leak findings. STOP and report if only one set of files is written.
  - Execution state: pending

### Task group 2: one writer

- [ ] E-02 Make `install_history.record_install_history` write under the `state_durable` physical class (`ctx.physical_classes[RootClass.STATE_DURABLE.value]`) instead of the logical `state` root, and extend its snapshot with `installed_version` set to `agent_workflows.__version__` and a REDACTED policy summary (preset, placements, git policies, delivery mode, records backend; `aw_home` and any absolute path replaced through the existing `_redact_details` logic or omitted). Keep the history file append-only with mode `0o644` as today.
  - Depends on: E-01
  - Expected outcome: one snapshot and one history file, both under `.aw/state/durable/`, carrying the running version and no absolute home path.
  - Execution state: pending

- [ ] E-03 Remove steps 3 and 4 (the durable snapshot and history writes) from `install_wizard.persist_project_policy`, so the wizard writes only `config/project.json` and `config/local.json` and the cutover sync; confirm by call-site search that the CLI path still records history exactly once per install (`cli.py` calls `record_install_history` after the install).
  - Depends on: E-02
  - Expected outcome: a fresh install writes the snapshot once; no literal version string remains in the wizard.
  - Execution state: pending

- [ ] E-04 Upgrade migration and readers: in the install path that already reconciles legacy layout (beside `engine.migrate_root_workflow_artifacts`), move a root-level `.aw/state/install.json` into `state/durable/` when no durable snapshot exists (else delete it), append root `history/installs.jsonl` lines not already present in the durable history, then delete the root history file and its empty directory; print one line naming what was migrated. Make `config._find_install_history_cutover` read the durable history first, falling back to the root path.
  - Depends on: E-03
  - Expected outcome: an upgrade over the four-file layout leaves only the durable pair, with every distinct history line preserved; a second install migrates nothing and prints nothing.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_install_state_records.py`: (a) fresh install into a temp git repo: `find .aw/state -type f` lists exactly `durable/install.json` and `durable/history/installs.jsonl`; the snapshot's `installed_version` equals `agent_workflows.__version__`; the snapshot and history contain neither the temp HOME path nor the username (set `HOME` to a temp dir with a distinctive name and assert it is absent); (b) upgrade: seed the four-file layout with two distinct root history lines and one shared line, reinstall, assert the durable history holds each distinct line once and the root files are gone; (c) the cutover reader returns the same date from a durable-only and a root-only fixture. Prove (a) can fail by restoring the wizard's step 3 and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the new tests pass; the mutation fails (a); no test reads production source.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec `kw5y2s` Section 3.3 is the authority for the state hierarchy (`state/durable/` holds `history/` and install receipts; `state/runtime/` holds locks, staging, transactions, cache, tmp).
- `layout.py` records that `install` is a FILE (`"install": "install.json"`), not a directory, which is the live value; this plan keeps `install.json` as a file.
- Leak containment (D92): state may record machine context, but redaction through `install_history._redact_details` is the existing mechanism; reuse it.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Four state files after one fresh install. | scratch target `find`: `.aw/state/durable/history/installs.jsonl`, `.aw/state/durable/install.json`, `.aw/state/history/installs.jsonl`, `.aw/state/install.json` |
| F-02 | Two writers. | `install_history.record_install_history`: `state_root = Path(ctx.logical_roots[LogicalRoot.STATE.value])` ... `install_file = state_root / "install.json"`; `install_wizard.persist_project_policy`: "# 3. Update durable install snapshot (.aw/state/durable/install.json)" |
| F-03 | Hardcoded version and unredacted policy. | `persist_project_policy`: `snapshot_data = {"installed_version": "2026.8.10", "schema_version": 2, "policy": policy.to_dict()}` |
| F-04 | A reader already tolerates both locations. | `config.py` `_find_install_history_cutover` lists `repo_root / ".aw" / "state" / "history" / "installs.jsonl"` and `... / "durable" / "history" / "installs.jsonl"` |

## Proposed changes (ordered, validatable)

1. One writer, durable class, real version, redacted (E-02, E-03).
2. Upgrade migration and reader order (E-04).
3. Tests (E-05).

## Deferred / out of scope (with reason)

- THE GIT POLICY OF `state_durable`.
  - Carrier: gi1w75
- STAGING AND THE INSTALL REPORT.
  - Carrier: gzsfqn

## Scope check

- Over-scope: none.
- Under-scope: other producers that may write directly under `.aw/state/` are not audited here; at HEAD the scratch install produced none besides these two writers, and the AW repo's own `.aw/state/runtime/` already holds locks and transactions in the spec location.

## Required tests / validation

- `tests/test_install_state_records.py` (E-05) with the mutation proof.
- Bare `python3 -m pytest` summary line pasted against a pre-edit baseline.

## Spec / documentation sync

- N/A for specs: this plan brings the code into line with spec `kw5y2s` Section 3.3 without changing it. Update the `install_history` module docstring ("`state/install.json` snapshot + `state/history/installs.jsonl`") to name the durable paths.

## Open questions

### OQ-01: Should the durable snapshot keep the full resolved policy for debugging?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: keep the policy minus absolute paths. The policy's portable parts are already in `config/project.json`; the only part unique to the snapshot is machine context, which is exactly what D92 says must not be recorded in a form that can leak. Redaction keeps the debugging value (which preset, which placements) without the path.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the pre-edit `find .aw/state -type f | sort`, the durable `install.json`, and the leak-check output, with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE a post-edit fresh install's `find .aw/state -type f | sort` and `cat .aw/state/durable/install.json` showing the running version and no absolute path, plus `check-local-leaks .aw/state --agent` showing zero fail findings.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE `grep -n "2026.8.10\|durable_state_dir / \"install.json\"" agent_workflows/install_wizard.py` returning nothing, and the call-site search showing `record_install_history` is reached once per install.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE an upgrade over a seeded four-file layout: the migration line from the install output, `find .aw/state -type f` after, the durable history content, and a second install's output showing no migration line.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: D05 and N2 are one defect seen twice: removing the duplicate writer is the same edit that removes the hardcoded version and the unredacted policy.

EXECUTION CONTRACT. Execute after Order 02 (`gi1w75`) is executed. Execute E-items in order. Commit only files changed for this plan through `aw commit pfub72 -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first. Run the suite BARE as `python3 -m pytest` and paste the actual summary line. On completion move the plan to `executed/` with `aw ipd set executed pfub72`.
