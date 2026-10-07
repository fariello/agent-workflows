# IPD: Write each install state record once, in the state class the spec names, with the real version

- Date: 2026-10-06
- Kind: child
- Concern: Defect D05 of research report `l6cbbb` plus a new defect N2 found while reproducing it, both present at HEAD `474b037a9`. D05: a fresh scratch install contains BOTH `.aw/state/install.json` and `.aw/state/durable/install.json`, and BOTH `.aw/state/history/installs.jsonl` and `.aw/state/durable/history/installs.jsonl`. Two writers produce them: `install_history.record_install_history` (called from `cli.py` after every install, writing under the LOGICAL `state` root `ctx.logical_roots["state"]`, i.e. `.aw/state/`), and `install_wizard.persist_project_policy` steps 3 and 4 (writing under `durable_state_dir`). Spec `kw5y2s` Section 3.3 puts install receipts and history under `state/durable/` and runtime material under `state/runtime/`; nothing belongs at the `state/` root. N2: `persist_project_policy` step 3 writes `"installed_version": "2026.8.10"` as a LITERAL, and writes `policy.to_dict()` unredacted (including `aw_home`, an absolute home path, which is `null` on a fresh install but is filled from `resolve_existing_policy`'s `aw_home=str(ctx.effective_aw_home)` on every reinstall), whereas `record_install_history` redacts its `details` through `_redact_details`.
- Scope: IN: one writer for the install snapshot and the install history, writing under `state/durable/` (`install.json`, `history/installs.jsonl`); the snapshot carries the running version (`agent_workflows.__version__`) and no absolute home path; `persist_project_policy` stops writing state (it keeps writing `config/project.json` and `config/local.json`); an upgrade migrates any root-level `state/install.json` and `state/history/installs.jsonl` into `state/durable/` (merging history lines without duplication) and removes the root copies; readers (`config._find_install_history_cutover`) read the durable path first and keep the legacy root as a fallback. OUT: the git policy of `state_durable` (Order 02 `gi1w75`); what is staged (Order 04 `gzsfqn`); any other `state/runtime/` producer.
- Scope-Paths: agent_workflows/install_history.py, agent_workflows/install_wizard.py, agent_workflows/config.py, agent_workflows/engine.py, tests/test_install_state_records.py, tests/test_config.py
- Item-Dependencies: executed:gi1w75
- Status: approved
- Readiness: go-pending-approval
- Blocks-Release: f33nrj
- From-Spec: kw5y2s
- Work-Kind: bug
- Priority: high
- Set: instbugs
- Order: 3
- Highest E allocated: 05
- Author: antigravity/claude-opus-5.5
- Id: pfub72
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0

- 2026-10-07 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008. Reviewed at lane HEAD `2493daf03`; plan committed and byte-identical to the lane input, so no pre-review snapshot. Reproduced D05 and N2 in a scratch target with a distinctive temp HOME, and found the `aw_home` leak appears only on reinstall (F-05); measured that `check-local-leaks` reports clean on the gitignored state tree (F-06). Fixed: leak oracle replaced with a direct HOME-name search (PR-001); nested policy excluded by a portable-field whitelist instead of top-level-only `_redact_details`, reinstall added to E-01, V-02 and E-05 (PR-002); E-04 migration placement, ordering, reporting, dry run and reader reorder specified, `tests/test_config.py` added to Scope-Paths (PR-003); third test-only writer `project_layout.install_system_tree` recorded (PR-004); V-03 behavioral evidence (PR-005); spec `install/` vs `install.json` divergence noted and `- From-Spec: kw5y2s` added (PR-006); `- Blocks-Release: next` (PR-007); gate gains honesty rule, scope fence, temp HOME and conditional finalize ownership (PR-008).
- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 03 of Set `instbugs` after reproducing D05 in a scratch target at HEAD `474b037a9` and finding N2 while tracing the two writers.

## Goal

Each install leaves exactly one install snapshot and one append-only history under `.aw/state/durable/`, carrying the real version and no machine-identifying absolute path, so the state tree matches the spec and a single ignore rule covers it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD: with `AW_NO_REEXEC=1` and `HOME` set to a temp dir with a distinctive name (e.g. `<tmp>/pfhome-zzuniq`), fresh `aw install . --preset private-target -y --no-interactive` into a temp git repo, then a second `aw install . -y --no-interactive`; after each, `find .aw/state -type f | sort`, `cat .aw/state/durable/install.json`, `wc -l` of both history files, and `grep -c pfhome-zzuniq` over `.aw/state`. Do NOT use `check-local-leaks` here: it scans git-TRACKED content, and `.aw/state/` is gitignored, so it reports clean whatever the files contain (measured at review, F-06). If only one set of files is written, record that and narrow E-02/E-03 to what remains.
  - Depends on: none
  - Expected outcome: the four files, the literal `"installed_version": "2026.8.10"`, `"aw_home": null` after the first install and the temp HOME path after the second, and two lines in each history after the second install (all reproduced at review, F-05).
  - Execution state: pending

### Task group 2: one writer

- [ ] E-02 Make `install_history.record_install_history` write under the `state_durable` physical class (`ctx.physical_classes[RootClass.STATE_DURABLE.value]`, which resolves to `.aw/state/durable` for target placements, as measured at review) instead of the logical `state` root, using the `layout.DURABLE_STATE_CLASSES` names (`install.json`, `history`). Extend its snapshot with `installed_version` set to `agent_workflows.__version__` (whose correctness for an installed build is Order 01 `whz0oi`'s fix, not this plan's) and a policy summary built from `ProjectPolicySchema`'s portable fields only (preset, role, placements, git policies, enabled hosts, delivery mode, records backend), which by construction excludes `aw_home` and `companion_dir` (rather than relying on `_redact_details` for the policy, since it only redacts top-level string values that trip a leak rule). Keep the snapshot write atomic and the history append-only with mode `0o644` as today. Update the module docstring to name the durable paths.
  - Depends on: E-01
  - Expected outcome: one snapshot and one history file, both under `.aw/state/durable/`, carrying the running version and neither the temp HOME path nor `aw_home`/`companion_dir` keys, after a fresh install and after a reinstall.
  - Execution state: pending

- [ ] E-03 Remove steps 3 and 4 (the durable snapshot and history writes) from `install_wizard.persist_project_policy`, along with the now-unused `durable_state_dir` creation, so the wizard writes only `config/project.json`, `config/local.json` and the cutover sync. Confirm by call-site search that `record_install_history` is reached once per repo install (`cli.py`, after `install_into_repo` returns, the block commented "Record install history event"). Note for the executor: `project_layout.install_system_tree` also writes `durable/install.json` and `installs.jsonl` with a literal `"installed_at": "2026-08-10T00:00:00Z"` and an absolute `system_root`, but at review it has no caller outside `tests/test_installer.py`, so it is not on the install path and is left alone (recorded in Scope check).
  - Depends on: E-02
  - Expected outcome: a fresh install and a reinstall each add exactly one history line; no literal version string remains in the wizard.
  - Execution state: pending

- [ ] E-04 Upgrade migration and readers: in `engine.install_into_repo`, beside `migrate_root_workflow_artifacts` (it runs before `install_all`; the `migrated` list is what the install reports), add a migration that runs before `record_install_history` appends: when a root-level `.aw/state/install.json` exists, move it into `state/durable/install.json` if no durable snapshot exists, else delete it; append each root `history/installs.jsonl` line not already present byte-for-byte in the durable history (preserving root order, appended after the existing durable lines); delete the root history file and the root `history/` directory if empty; report through the `migrated` list only when something moved (silent otherwise, matching `migrate_root_workflow_artifacts`), and do nothing under `dry_run`. Make `config._find_install_history_cutover` read the durable history first and fall back to the root path (today the root path is first and the loop breaks on the first file with entries).
  - Depends on: E-03
  - Expected outcome: an upgrade over the four-file layout leaves only the durable pair, with every distinct history line preserved once; a second install migrates nothing and reports nothing; a dry run changes nothing; the cutover reader returns the same date for durable-only and root-only fixtures.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_install_state_records.py`: (a) fresh install AND a second install into a temp git repo with `AW_NO_REEXEC=1` and `HOME`/`XDG_CONFIG_HOME` set to a temp dir with a distinctive name: `.aw/state` holds exactly `durable/install.json` and `durable/history/installs.jsonl` (other durable or runtime files the install legitimately creates elsewhere are not asserted against, only that nothing is at the `state/` root); the snapshot's `installed_version` equals the running `agent_workflows.__version__` as reported by the same subprocess interpreter; neither file contains the temp HOME path or an `aw_home`/`companion_dir` key; the history has two lines after two installs; (b) upgrade: seed the four-file layout with two distinct root history lines and one line shared with the durable history, reinstall, assert the durable history holds each distinct line once and the root files are gone; (c) the cutover reader returns the same date from a durable-only and a root-only fixture. Prove (a) can fail by restoring the wizard's step 3 and pasting the failure, then restore. The existing `tests/test_config.py` cutover tests seed the ROOT history path; they must keep passing (the fallback), and are only edited if E-04's reorder changes their outcome.
  - Depends on: E-04
  - Expected outcome: the new tests pass; the mutation fails (a); no test reads production source.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec `kw5y2s` Section 3.3 is the authority for the state hierarchy (`state/durable/` holds `history/` and install receipts; `state/runtime/` holds locks, staging, transactions, cache, tmp).
- `layout.py` records that `install` is a FILE (`"install": "install.json"`), not a directory, which is the live value; this plan keeps `install.json` as a file.
- Leak containment (D92): `install_history._redact_details` redacts caller `details` (top-level string values that trip a leak rule); it does not walk nested dicts, so the policy summary must exclude path-bearing fields by construction. `ProjectPolicySchema` (the `config/project.json` writer in `persist_project_policy`) already carries exactly the portable fields.
- `.aw/state/` is gitignored by the framework-owned `.aw/.gitignore` (`/state/`, `engine._AW_GITIGNORE_TEMPLATE`), and `check-local-leaks` scans tracked content, so leak absence in state must be measured by direct search, not by the sanitizer.
- Spec `kw5y2s` Section 3.3 lists `install/` (a directory) for receipts; `layout.DURABLE_STATE_CLASSES` records the live value `install.json` (a file) and says Order 03 of that Set must reproduce it. This plan follows the live value and does not edit the spec.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Four state files after one fresh install. | scratch target `find`: `.aw/state/durable/history/installs.jsonl`, `.aw/state/durable/install.json`, `.aw/state/history/installs.jsonl`, `.aw/state/install.json` |
| F-02 | Two writers. | `install_history.record_install_history`: `state_root = Path(ctx.logical_roots[LogicalRoot.STATE.value])` ... `install_file = state_root / "install.json"`; `install_wizard.persist_project_policy`: "# 3. Update durable install snapshot (.aw/state/durable/install.json)" |
| F-03 | Hardcoded version and unredacted policy. | `persist_project_policy`: `snapshot_data = {"installed_version": "2026.8.10", "schema_version": 2, "policy": policy.to_dict()}` |
| F-04 | A reader already tolerates both locations. | `config.py` `_find_install_history_cutover` lists `repo_root / ".aw" / "state" / "history" / "installs.jsonl"` and `... / "durable" / "history" / "installs.jsonl"`, root first, `break` on the first file with entries |
| F-05 | Reproduced at review HEAD `2493daf03`, and the leak is real on reinstall. | scratch `private-target` install, temp HOME `pfhome-zzuniq`: four state files; durable snapshot `"installed_version": "2026.8.10"`, `"aw_home": null`; after a second install `aw_home` became `<tmp HOME>/.config/agent-workflows` and the durable history contained the temp HOME path; each history had 2 lines |
| F-06 | The sanitizer cannot see state. | same target: `git status --short --ignored .aw/state` -> `!! .aw/state/`; `check-local-leaks . --agent` -> `"outcome":"clean"` while the history contained the HOME path |
| F-07 | A third writer exists off the install path. | `project_layout.install_system_tree` writes `durable/install.json` with `"installed_at": "2026-08-10T00:00:00Z"` and `str(system_root)`; callers: `tests/test_installer.py` only |

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
- Observed at review, out of scope: `project_layout.install_system_tree` (F-07) writes a literal timestamp and an absolute path into the durable snapshot but is reached only by tests; reported to the maintainer, not changed here.

## Required tests / validation

- `tests/test_install_state_records.py` (E-05) with the mutation proof; narrowed run as `python3 -m pytest -o addopts="" tests/test_install_state_records.py`.
- `tests/test_config.py` (cutover reader) and `tests/test_installer.py` (durable install paths) still pass.
- Bare `python3 -m pytest` summary line pasted, before the edit and after.

## Spec / documentation sync

- N/A for specs: this plan brings the code into line with spec `kw5y2s` Section 3.3 without changing it (the `install/` vs `install.json` naming difference is pre-existing and documented in `layout.DURABLE_STATE_CLASSES`). Update the `install_history` module docstring ("`state/install.json` snapshot + `state/history/installs.jsonl`") to name the durable paths.

## Open questions

### OQ-01: Should the durable snapshot keep the full resolved policy for debugging?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: keep the policy minus absolute paths. The policy's portable parts are already in `config/project.json`; the only part unique to the snapshot is machine context, which is exactly what D92 says must not be recorded in a form that can leak. Redaction keeps the debugging value (which preset, which placements) without the path.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the pre-edit `find .aw/state -type f | sort`, the durable `install.json` and the history line counts after each of the two installs, and the `grep -c` of the temp HOME name over `.aw/state`, with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE, after a post-edit fresh install and a second install, `find .aw/state -type f | sort`, `cat .aw/state/durable/install.json` showing the running version and no `aw_home`/`companion_dir` key, and `grep -rc <temp HOME name> .aw/state` returning 0 for every file.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the `git diff` of `agent_workflows/install_wizard.py` removing steps 3 and 4, the `grep -rn record_install_history agent_workflows/` call-site listing, and the history line counts (1 then 2) from the V-02 runs.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE an upgrade over a seeded four-file layout: the migration report from the install output, `find .aw/state -type f` after, the durable history content, a second install's output showing no migration report, a `--dry-run` over a fresh seed showing the files unchanged, and the `git diff` of `config._find_install_history_cutover`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file (cases (a) to (c) passing), the mutation failure output for case (a), the `tests/test_config.py` and `tests/test_installer.py` runs, and the bare `python3 -m pytest` summary line before and after.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: D05 and N2 are one defect seen twice: removing the duplicate writer is the same edit that removes the hardcoded version and the unredacted policy.

EXECUTION CONTRACT. OQ-01 is resolved; no question is open. Execute after Order 02 (`gi1w75`) is executed (`- Item-Dependencies:`; the runners enforce it at dispatch). Execute E-items in order (E-01 to E-05). Commit only files changed for this plan through `aw commit pfub72 -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout. HONESTY RULE (hard MUST): every `V-*` demands PASTED actual output; run the suite BARE as `python3 -m pytest` and paste the actual summary line; a claim without pasted output satisfies no item. Run every scratch install and `aw` subprocess with `AW_NO_REEXEC=1` and `HOME` pointed at a temp dir. SCOPE FENCE: `- Scope-Paths:` is a DECLARATION; an out-of-scope edit (for example a test that pins the root state path) is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. LIFECYCLE, CONDITIONAL OWNERSHIP: under `aw oc run` / `aw agy run` the runner finalizes this plan after its merge-and-revalidate gate, so the executor does not; in a hand execution, the executor fills every `V-*`, confirms `aw ipd lint --phase pre-transition` conforms, and transitions with `aw ipd finalize pfub72`, never by a hand `git mv`.
