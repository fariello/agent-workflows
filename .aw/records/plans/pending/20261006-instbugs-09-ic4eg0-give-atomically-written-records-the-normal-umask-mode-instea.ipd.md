# IPD: Give atomically written records the normal umask mode instead of owner-only 0600

- Date: 2026-10-06
- Kind: child
- Concern: Defect D11 of research report `l6cbbb`, present at HEAD `474b037a9`. `artifact_core.atomic_write` writes through `tempfile.mkstemp(dir=..., prefix=prefix, suffix=".md")` and `os.replace`; `mkstemp` creates the file 0600 regardless of umask and `os.replace` keeps that mode, so every tracked record written this way is owner-only. In the scratch target under umask 022, both `aw research new --apply` and `aw adopt --apply` produced `-rw-------` files, while the generated `INDEX` files (written another way) were `-rw-r--r--`. A 0600 tracked file is committed with mode 100644 by git but stays unreadable to other local users and to tooling running as another uid on a shared checkout. The same `mkstemp` pattern appears in many modules; `run_analytics_report` already documents the trap ("`mkstemp` hardcodes 0o600 and `os.replace` preserves it") and fixes it locally.
- Scope: IN: give `artifact_core.atomic_write` a mode rule: a NEW file gets `0o666 & ~umask`, a REPLACED file keeps its existing mode; audit every other `mkstemp`/`NamedTemporaryFile` temp-then-replace site in `agent_workflows/` and classify each as TRACKED-RECORD (a file a user or repository reads as content: route it through the shared rule) or PRIVATE (locks, journals, receipts, run state under `.aw/state/` or a run dir, per-user config, identifying hints: left at 0600 with no code change, the classification recorded in V-03); tests. OUT: changing modes of files already on disk (a tracked file's committed mode is unaffected; users can `chmod` existing 0600 files, and the plan notes the one-liner in its evidence); git's own mode bits.
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/manifest.py, agent_workflows/leak_sanitizer.py, agent_workflows/oc_models.py, agent_workflows/ipd_lifecycle.py, agent_workflows/layout_inventory.py, agent_workflows/workflow_cli.py, agent_workflows/run_analytics_report.py, tests/test_atomic_write_mode.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
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

- 2026-10-07 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008. Reviewed at lane HEAD `3c7058184`; plan committed and byte-identical to the lane input, so no pre-review snapshot. Reproduced 0600 for research, adopt, ipd scaffold, backlog new and `managed-sections.json`, and a 640 plan reset to 600 by `aw ipd set` (F-05); demonstrated the chmod mechanism (F-06). Fixed: umask read mechanism named, `/proc/self/status` with fallback, shared helper (PR-001); Scope-Paths and E-03 reclassified per site, adding `manifest`, `leak_sanitizer`, `oc_models` (PR-002); allowlist vs user-hints split inside `leak_sanitizer._atomic_write` (PR-003); no comment churn on PRIVATE sites (PR-004); exact E-01 verbs, subprocess-only umask, POSIX guard, `managed-sections` and PRIVATE controls in E-04 (PR-005); preserve-rule consequence for already-0600 files stated (PR-006); `Carrier-Declined:` replaces the malformed carrier failing `check.ipd-uncarried-obligation`, `- Blocks-Release: next` added (PR-007); gate gains honesty rule, scope fence, temp HOME, conditional finalize ownership (PR-008). `project_layout` mkstemp fd leak reported to the maintainer.
- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 09 of Set `instbugs` after measuring `-rw-------` on files from `aw research new --apply` and `aw adopt --apply` in a scratch target under umask 022 and listing every `mkstemp` caller in `agent_workflows/`.

## Goal

Records the tool writes into a repository get the same permissions any normal editor would give them (umask-derived for new files, preserved for existing ones), while genuinely private state keeps owner-only permissions on purpose.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD under `umask 022`: in a temp git repo installed with `AW_NO_REEXEC=1 HOME=<tmp> aw install . -y --preset private-target`, run `aw research new --kind research-report --slug probe --apply`; `aw adopt .aw/inbox/ext.md --kind findings --slug ext --apply` on a dropped inbox file; `AW_IPD_AUTHOR=probe aw ipd scaffold --kind child --title 'Probe plan' --set probe --order 1 --priority low --work-kind chore --apply`; `aw backlog new --summary 'Probe item' --priority low --work-kind chore --apply`; then `chmod 640` the plan and run `aw ipd set to-review <id6> --no-commit -m probe`. Paste `stat -c '%a %n'` for each record and for `.aw/system/managed-sections.json`. If any record is already 644, record that and drop it from E-04's failing expectations.
  - Depends on: none
  - Expected outcome: 600 for every created record and for `managed-sections.json`, and 600 for the plan after the `aw ipd set` rewrite of the 640 file, pasted with the HEAD sha (all reproduced at review, F-05).
  - Execution state: pending

### Task group 2: fix

- [ ] E-02 Lift `run_analytics_report._current_umask` into `artifact_core` as a shared `current_umask()` that reads the `Umask:` line of `/proc/self/status` when present (no global flip; the runner is multi-threaded, e.g. `runner_shared`, `runner_stop`) and falls back to the existing set-and-restore idiom; add `artifact_core.replacement_mode(path)` returning `stat.S_IMODE(os.stat(path).st_mode)` when `path` exists, else `0o666 & ~current_umask()`. In `artifact_core.atomic_write`, `os.chmod(tmp, replacement_mode(path))` before `os.replace`. Point `run_analytics_report` at the shared helper (its published-report behavior unchanged: it writes new files). Keep `mkstemp` itself (random name, `O_EXCL`).
  - Depends on: E-01
  - Expected outcome: new files written by `atomic_write` are 644 under umask 022, 664 under umask 002, 600 under umask 077; a pre-existing 640 file stays 640 after rewrite; the process umask is unchanged afterwards (demonstrated with a stand-alone sketch of this exact mechanism at review, F-06).
  - Execution state: pending

- [ ] E-03 Audit every other temp-then-replace site, re-derived at execution with `grep -rn 'mkstemp\|NamedTemporaryFile' agent_workflows/*.py`, and record one row per site: module, function, what it writes, TRACKED-RECORD or PRIVATE, action. Starting classification from review (verify each, do not copy it): TRACKED-RECORD, apply `replacement_mode` before `os.replace`: `manifest.save` (`.aw/system/managed-sections.json`, measured 600 after a fresh install), `leak_sanitizer.resolve_allowlist_path` writes through `leak_sanitizer._atomic_write` (tracked allowlist; the SAME helper writes the user-hints file, which is PRIVATE, so give the helper a mode choice and keep hints at 0600), `oc_models._atomic_write` (`opencode.json`; the preserve branch keeps a user-level config's mode), `ipd_lifecycle` rollback restore of a plan's original `.md` (the `.rb-` prefix site; must restore the original file's mode), `layout_inventory._atomic_json` (user-requested `--output` path), `workflow_cli._write_generated` (generated package source). PRIVATE, no code change: `commit_lock`, `comms_acks`, `comms_broker` (`untracked/`), `completion` (notice stamp), `config.save`, `ipd_lifecycle._atomic_write_json_at`/`_atomic_write_json` (`.aw/state/` journals and receipts), `lane_containment._atomic_write_text` (run-dir registers and receipts), `project_layout` (journal backups), `project_registry`, `runner_profiles` (institution-specific model ids), `runner_shared.atomic_write_json` (run-dir state), `runner_stop`, `work_cmd` (`.aw/state/work`). UNUSED: `project_schema.atomic_save_json` (no caller at review). A module whose classification differs from this list is changed or left accordingly and justified at finalize (`--scope-reason` / `--scope-ack`).
  - Depends on: E-02
  - Expected outcome: a complete classification table covering every site the grep returns; no TRACKED-RECORD writer still yields 0600 for a new file under umask 022; every PRIVATE writer still yields 0600.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-04 Add `tests/test_atomic_write_mode.py` (POSIX only; skip on Windows, where `os.chmod` sets only the read-only bit): drive each verb as a subprocess through `sh -c 'umask 022 && exec python3 -m agent_workflows ...'` so the test process's own umask is never changed (xdist workers share nothing else), with `HOME`/`XDG_CONFIG_HOME` isolated to the temp dir and `AW_NO_REEXEC=1`. Assert: (a) `aw research new --apply` creates a 644 file; (b) `aw adopt --apply` creates a 644 file; (c) `aw ipd scaffold --apply` creates a 644 plan and `aw ipd set` to a terminal status moves it with 644; (d) a plan chmodded to 640 and then rewritten by `aw ipd set` stays 640; (e) under `umask 002` a new record is 664; (f) `aw install` leaves `.aw/system/managed-sections.json` 644; (g) a PRIVATE writer is still 600: `aw config set defaults.prune false` writes `$XDG_CONFIG_HOME/agent-workflows/config.json` through `config.save` (measured 600 at review). Prove (a) can fail by removing the chmod from `atomic_write` and pasting the failure, then restore it.
  - Depends on: E-03
  - Expected outcome: the new tests pass; the mutation fails; assertions are on file modes produced by real CLI runs (P16).
  - Execution state: pending

## Project conventions discovered (Step 0)

- `artifact_core.atomic_write` is the shared writer for records created by the research, adopt and plan verbs.
- `run_analytics_report` already carries the comment "`mkstemp` hardcodes 0o600 and `os.replace` preserves it, so a published bundle would be ..." and a local fix (`os.chmod(temp_name, 0o666 & ~_current_umask())`); `_current_umask` is set-and-restore, which its own docstring says is racy only against a concurrent umask change in the same process. That is the precedent.
- Many modules call `artifact_core.atomic_write` (`research_cmd`, `artifact_adopt`, `ipd_authoring`, `backlog`, `specs`, `status_set`, `set_records`, `releases`, `prompts`, `model_vocab`, `artifact_rename`, `artifact_refs`, `plans_refs`, `research_refs`, `record_producers`), so fixing it once fixes every record verb.
- `lane_containment` seals files at `SEALED_FILE_MODE = 0o444` and unseals before rewriting; the preserve rule must not fight that (it keeps whatever mode the caller set).
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | `atomic_write` creates 0600 files. | `artifact_core.atomic_write`: `fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=prefix, suffix=".md")` then `os.replace` |
| F-02 | Research and adopt records are owner-only. | scratch target, umask 022: `-rw-------` for the `aw research new --apply` and `aw adopt --apply` outputs; INDEX files `-rw-r--r--` |
| F-03 | The trap is known and fixed in one place. | `run_analytics_report` comment "`mkstemp` hardcodes 0o600 and `os.replace` preserves it" |
| F-04 | Many other `mkstemp` callers exist, some private by design. | `grep -rln mkstemp agent_workflows/*.py` lists 20 modules including `commit_lock` and `config`; `project_schema.atomic_save_json` uses `tempfile.NamedTemporaryFile` (also 0600) and has no caller |
| F-05 | Reproduced at review HEAD `3c7058184`, and wider than research/adopt. | scratch `private-target` install, umask 022: `aw research new`, `aw adopt`, `aw ipd scaffold`, `aw backlog new` all 600; `.aw/system/managed-sections.json` 600; a plan chmodded 640 became 600 after `aw ipd set to-review` and stayed 600 after `aw ipd set not-executed`. This repository already holds six 0600 tracked records written by the current review sweep (`find .aw/records -type f -perm 600`). |
| F-06 | The proposed mechanism works. | stand-alone sketch: `mkstemp`, then `os.chmod(tmp, existing mode or 0o666 & ~umask)` with the umask read from `/proc/self/status`: umask 022 -> 644, 002 -> 664, 077 -> 600, existing 640 -> 640, process umask unchanged afterwards |

## Proposed changes (ordered, validatable)

1. Mode rule in `atomic_write` (E-02).
2. Per-site audit and classification (E-03).
3. Behavior tests with mutation proof (E-04).

## Deferred / out of scope (with reason)

- Repairing modes of existing 0600 files on disk: not the tool's file to silently chmod. Consequence of OQ-01, stated so it is not a surprise: a file this bug already wrote 0600 STAYS 0600 through every later rewrite, since it cannot be told apart from a deliberate chmod. The evidence records `find .aw/records .aw/system -type f -perm 600 -exec chmod 644 {} +` as a user-run remedy (not `.aw/state/`, which holds PRIVATE files).
  - Carrier-Declined: deliberately not done; a user-run one-liner recorded in V-03 evidence is the remedy, and git does not record the 600/644 distinction, so no committed state is wrong.
- The whole-Set regression that checks research composition modes end to end.
  - Carrier: kck7a5

## Scope check

- Over-scope: none.
- Under-scope: none; private files are explicitly classified and left 0600.
- Observed at review, out of scope: `project_layout` builds a backup name from `int(tempfile.mkstemp()[0])`, which leaks an open fd and leaves an empty file in the system temp dir on each call. Reported to the maintainer, not fixed here.

## Required tests / validation

- `tests/test_atomic_write_mode.py` (E-04) with the mutation proof; narrowed run as `python3 -m pytest -o addopts="" tests/test_atomic_write_mode.py`.
- Existing run-analytics report tests still pass after `_current_umask` moves (re-derive with `grep -ln run_analytics_report tests/`).
- Bare `python3 -m pytest` summary line pasted, before the edit and after.

## Spec / documentation sync

- N/A: no spec states record file modes.

## Open questions

### OQ-01: Should replaced files be reset to the umask mode or keep their mode?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: keep the existing mode. That is what an in-place editor does, it respects a user's deliberate chmod, and it avoids widening a file someone narrowed. Accepted cost: files this bug already wrote 0600 stay 0600 until a user chmods them (see Deferred).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the pre-edit `stat -c '%a %n'` lines for every E-01 record, `managed-sections.json`, and the 640-then-`aw ipd set` plan, with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the same `stat` lines post-edit (644, the 640 plan still 640), plus umask 002 (664) and umask 077 (600) runs, the process-umask-unchanged check, and the `git diff` of `agent_workflows/artifact_core.py` and `agent_workflows/run_analytics_report.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the grep output, the complete classification table (one row per site it returns), the `git diff --stat` of changed modules, a `stat` line for one new file per changed TRACKED-RECORD writer (644) and for one PRIVATE writer (600), and the user-run chmod one-liner.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the narrowed run of the new test file (cases (a) to (g) passing), the mutation failure output for case (a), the run-analytics test run, and the bare `python3 -m pytest` summary line before and after.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one mode rule applied at one shared writer, plus the audit that keeps the rule consistent across the other writers.

EXECUTION CONTRACT. OQ-01 is resolved; no question is open. Execute E-items in order (E-01, E-02, E-03, E-04). Commit only files changed for this plan through `aw commit ic4eg0 -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout. HONESTY RULE (hard MUST): every `V-*` demands PASTED actual output; run the suite BARE as `python3 -m pytest` and paste the actual summary line; a claim without pasted output satisfies no item. Run every scratch install and `aw` subprocess with `AW_NO_REEXEC=1` and `HOME` pointed at a temp dir, and never change the umask of the test or executor process itself. SCOPE FENCE: `- Scope-Paths:` is a DECLARATION; an out-of-scope edit (for example a site E-03 classifies differently) is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. LIFECYCLE, CONDITIONAL OWNERSHIP: under `aw oc run` / `aw agy run` the runner finalizes this plan after its merge-and-revalidate gate, so the executor does not; in a hand execution, the executor fills every `V-*`, confirms `aw ipd lint --phase pre-transition` conforms, and transitions with `aw ipd finalize ic4eg0`, never by a hand `git mv`.
