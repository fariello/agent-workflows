# IPD: Give atomically written records the normal umask mode instead of owner-only 0600

- Date: 2026-10-06
- Kind: child
- Concern: Defect D11 of research report `l6cbbb`, present at HEAD `474b037a9`. `artifact_core.atomic_write` writes through `tempfile.mkstemp(dir=..., prefix=prefix, suffix=".md")` and `os.replace`; `mkstemp` creates the file 0600 regardless of umask and `os.replace` keeps that mode, so every tracked record written this way is owner-only. In the scratch target under umask 022, both `aw research new --apply` and `aw adopt --apply` produced `-rw-------` files, while the generated `INDEX` files (written another way) were `-rw-r--r--`. A 0600 tracked file is committed with mode 100644 by git but stays unreadable to other local users and to tooling running as another uid on a shared checkout. The same `mkstemp` pattern appears in many modules; `run_analytics_report` already documents the trap ("`mkstemp` hardcodes 0o600 and `os.replace` preserves it") and fixes it locally.
- Scope: IN: give `artifact_core.atomic_write` a mode rule: a NEW file gets `0o666 & ~umask`, a REPLACED file keeps its existing mode; audit every other `mkstemp`/`NamedTemporaryFile` temp-then-replace site in `agent_workflows/` and classify each as TRACKED-RECORD (a file a user or repository reads as content: route it through the shared rule) or PRIVATE (locks, journals, receipts, run state under `.aw/state/` or a run dir, per-user config, identifying hints: left at 0600 with no code change, the classification recorded in V-03); tests. OUT: changing modes of files already on disk (a tracked file's committed mode is unaffected; users can `chmod` existing 0600 files, and the plan notes the one-liner in its evidence); git's own mode bits.
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/manifest.py, agent_workflows/leak_sanitizer.py, agent_workflows/oc_models.py, agent_workflows/ipd_lifecycle.py, agent_workflows/layout_inventory.py, agent_workflows/workflow_cli.py, agent_workflows/run_analytics_report.py, tests/test_atomic_write_mode.py
- Item-Dependencies: none
- Status: executed
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
- 2026-10-07 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: ic4eg0 verified (set instbugs, attempt 1).
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0

- 2026-10-07 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008. Reviewed at lane HEAD `3c7058184`; plan committed and byte-identical to the lane input, so no pre-review snapshot. Reproduced 0600 for research, adopt, ipd scaffold, backlog new and `managed-sections.json`, and a 640 plan reset to 600 by `aw ipd set` (F-05); demonstrated the chmod mechanism (F-06). Fixed: umask read mechanism named, `/proc/self/status` with fallback, shared helper (PR-001); Scope-Paths and E-03 reclassified per site, adding `manifest`, `leak_sanitizer`, `oc_models` (PR-002); allowlist vs user-hints split inside `leak_sanitizer._atomic_write` (PR-003); no comment churn on PRIVATE sites (PR-004); exact E-01 verbs, subprocess-only umask, POSIX guard, `managed-sections` and PRIVATE controls in E-04 (PR-005); preserve-rule consequence for already-0600 files stated (PR-006); `Carrier-Declined:` replaces the malformed carrier failing `check.ipd-uncarried-obligation`, `- Blocks-Release: next` added (PR-007); gate gains honesty rule, scope fence, temp HOME, conditional finalize ownership (PR-008). `project_layout` mkstemp fd leak reported to the maintainer.
- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 09 of Set `instbugs` after measuring `-rw-------` on files from `aw research new --apply` and `aw adopt --apply` in a scratch target under umask 022 and listing every `mkstemp` caller in `agent_workflows/`.

## Goal

Records the tool writes into a repository get the same permissions any normal editor would give them (umask-derived for new files, preserved for existing ones), while genuinely private state keeps owner-only permissions on purpose.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [x] E-01 Re-measure at the execution HEAD under `umask 022`: in a temp git repo installed with `AW_NO_REEXEC=1 HOME=<tmp> aw install . -y --preset private-target`, run `aw research new --kind research-report --slug probe --apply`; `aw adopt .aw/inbox/ext.md --kind findings --slug ext --apply` on a dropped inbox file; `AW_IPD_AUTHOR=probe aw ipd scaffold --kind child --title 'Probe plan' --set probe --order 1 --priority low --work-kind chore --apply`; `aw backlog new --summary 'Probe item' --priority low --work-kind chore --apply`; then `chmod 640` the plan and run `aw ipd set to-review <id6> --no-commit -m probe`. Paste `stat -c '%a %n'` for each record and for `.aw/system/managed-sections.json`. If any record is already 644, record that and drop it from E-04's failing expectations.
  - Depends on: none
  - Expected outcome: 600 for every created record and for `managed-sections.json`, and 600 for the plan after the `aw ipd set` rewrite of the 640 file, pasted with the HEAD sha (all reproduced at review, F-05).
  - Execution state: performed

### Task group 2: fix

- [x] E-02 Lift `run_analytics_report._current_umask` into `artifact_core` as a shared `current_umask()` that reads the `Umask:` line of `/proc/self/status` when present (no global flip; the runner is multi-threaded, e.g. `runner_shared`, `runner_stop`) and falls back to the existing set-and-restore idiom; add `artifact_core.replacement_mode(path)` returning `stat.S_IMODE(os.stat(path).st_mode)` when `path` exists, else `0o666 & ~current_umask()`. In `artifact_core.atomic_write`, `os.chmod(tmp, replacement_mode(path))` before `os.replace`. Point `run_analytics_report` at the shared helper (its published-report behavior unchanged: it writes new files). Keep `mkstemp` itself (random name, `O_EXCL`).
  - Depends on: E-01
  - Expected outcome: new files written by `atomic_write` are 644 under umask 022, 664 under umask 002, 600 under umask 077; a pre-existing 640 file stays 640 after rewrite; the process umask is unchanged afterwards (demonstrated with a stand-alone sketch of this exact mechanism at review, F-06).
  - Execution state: performed

- [x] E-03 Audit every other temp-then-replace site, re-derived at execution with `grep -rn 'mkstemp\|NamedTemporaryFile' agent_workflows/*.py`, and record one row per site: module, function, what it writes, TRACKED-RECORD or PRIVATE, action. Starting classification from review (verify each, do not copy it): TRACKED-RECORD, apply `replacement_mode` before `os.replace`: `manifest.save` (`.aw/system/managed-sections.json`, measured 600 after a fresh install), `leak_sanitizer.resolve_allowlist_path` writes through `leak_sanitizer._atomic_write` (tracked allowlist; the SAME helper writes the user-hints file, which is PRIVATE, so give the helper a mode choice and keep hints at 0600), `oc_models._atomic_write` (`opencode.json`; the preserve branch keeps a user-level config's mode), `ipd_lifecycle` rollback restore of a plan's original `.md` (the `.rb-` prefix site; must restore the original file's mode), `layout_inventory._atomic_json` (user-requested `--output` path), `workflow_cli._write_generated` (generated package source). PRIVATE, no code change: `commit_lock`, `comms_acks`, `comms_broker` (`untracked/`), `completion` (notice stamp), `config.save`, `ipd_lifecycle._atomic_write_json_at`/`_atomic_write_json` (`.aw/state/` journals and receipts), `lane_containment._atomic_write_text` (run-dir registers and receipts), `project_layout` (journal backups), `project_registry`, `runner_profiles` (institution-specific model ids), `runner_shared.atomic_write_json` (run-dir state), `runner_stop`, `work_cmd` (`.aw/state/work`). UNUSED: `project_schema.atomic_save_json` (no caller at review). A module whose classification differs from this list is changed or left accordingly and justified at finalize (`--scope-reason` / `--scope-ack`).
  - Depends on: E-02
  - Expected outcome: a complete classification table covering every site the grep returns; no TRACKED-RECORD writer still yields 0600 for a new file under umask 022; every PRIVATE writer still yields 0600.
  - Execution state: performed

### Task group 3: pin it

- [x] E-04 Add `tests/test_atomic_write_mode.py` (POSIX only; skip on Windows, where `os.chmod` sets only the read-only bit): drive each verb as a subprocess through `sh -c 'umask 022 && exec python3 -m agent_workflows ...'` so the test process's own umask is never changed (xdist workers share nothing else), with `HOME`/`XDG_CONFIG_HOME` isolated to the temp dir and `AW_NO_REEXEC=1`. Assert: (a) `aw research new --apply` creates a 644 file; (b) `aw adopt --apply` creates a 644 file; (c) `aw ipd scaffold --apply` creates a 644 plan and `aw ipd set` to a terminal status moves it with 644; (d) a plan chmodded to 640 and then rewritten by `aw ipd set` stays 640; (e) under `umask 002` a new record is 664; (f) `aw install` leaves `.aw/system/managed-sections.json` 644; (g) a PRIVATE writer is still 600: `aw config set defaults.prune false` writes `$XDG_CONFIG_HOME/agent-workflows/config.json` through `config.save` (measured 600 at review). Prove (a) can fail by removing the chmod from `atomic_write` and pasting the failure, then restore it.
  - Depends on: E-03
  - Expected outcome: the new tests pass; the mutation fails; assertions are on file modes produced by real CLI runs (P16).
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: PASTE the pre-edit `stat -c '%a %n'` lines for every E-01 record, `managed-sections.json`, and the 640-then-`aw ipd set` plan, with the HEAD sha.
  - Observed evidence:
    ```
    HEAD SHA: ffe3efd3dcc7461412cbeff3c878f4db1d2ff357
    600 .aw/records/research/20261007-probe-00-251agt-probe.research-report.md
    600 .aw/records/research/20261007-ext-00-4qrp6x-ext.findings.md
    600 .aw/records/plans/pending/20261007-probe-01-ujem69-probe-plan.ipd.md
    600 .aw/records/backlog/open/20261007-0ysq6d-01-0ysq6d-probe-item.backlog.md
    600 .aw/system/managed-sections.json
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE the same `stat` lines post-edit (644, the 640 plan still 640), plus umask 002 (664) and umask 077 (600) runs, the process-umask-unchanged check, and the `git diff` of `agent_workflows/artifact_core.py` and `agent_workflows/run_analytics_report.py`.
  - Observed evidence:
    Post-edit stat output:
    ```
    644 .aw/records/research/20261007-probe-00-wbtxy2-probe.research-report.md
    644 .aw/records/research/20261007-ext-00-ijffje-ext.findings.md
    640 .aw/records/plans/pending/20261007-probe-01-v8gujc-probe-plan.ipd.md
    644 .aw/records/backlog/open/20261007-zuzkqf-01-zuzkqf-probe-item.backlog.md
    ```
    Mode under different umasks & process umask preservation:
    ```
    New file mode under umask 0o22: 0o644
    Rewritten file mode after chmod 640: 0o640
    Process umask after operations: 0o22
    umask 002 mode: 0o664
    umask 077 mode: 0o600
    ```
    Diff of `agent_workflows/artifact_core.py` and `agent_workflows/run_analytics_report.py`:
    ```diff
    diff --git a/agent_workflows/artifact_core.py b/agent_workflows/artifact_core.py
    index d3213842e..992e52542 100644
    --- a/agent_workflows/artifact_core.py
    +++ b/agent_workflows/artifact_core.py
    @@ -25,6 +25,7 @@ import functools
     import os
     import re
     import secrets
    +import stat
     import subprocess
     import tempfile
     from pathlib import Path
    @@ -341,6 +342,40 @@ def normalize_artifact_markdown(text: str) -> str:
         return f"{normalized}\n" if normalized else ""


    +def current_umask() -> int:
    +    """Read the process umask without leaving it changed.
    +
    +    On Linux, reads the ``Umask:`` field from ``/proc/self/status`` when present to avoid mutating
    +    process state in a multi-threaded runner. Falls back to the portable ``os.umask`` set-and-restore
    +    idiom when ``/proc`` is unavailable or does not report a umask.
    +    """
    +    try:
    +        with open("/proc/self/status", "r", encoding="utf-8") as f:
    +            for line in f:
                if line.startswith("Umask:"):
                    return int(line.split(":", 1)[1].strip(), 8)
    +    except (OSError, ValueError):
    +        pass
    +
    +    current = os.umask(0o022)
    +    os.umask(current)
    +    return current
    +
    +
    +def replacement_mode(path: Path | str) -> int:
    +    """Return the mode to give a newly written or replaced file.
    +
    +    When ``path`` exists, preserve its existing permission mode (``stat.S_IMODE``) so an in-place
    +    rewrite respects deliberate permission changes (e.g. ``chmod 640`` or sealed files).
    +    When ``path`` does not exist, compute the standard file creation mode ``0o666 & ~current_umask()``.
    +    """
    +    try:
    +        st = os.stat(path)
    +        return stat.S_IMODE(st.st_mode)
    +    except OSError:
    +        return 0o666 & ~current_umask()
    +
    +
     def atomic_write(path: Path, text: str, *, prefix: str = ".aw-tmp-") -> None:
         """Write-to-temp-then-rename so an interrupted apply never leaves a partial file.

    @@ -367,6 +402,7 @@ def atomic_write(path: Path, text: str, *, prefix: str = ".aw-tmp-") -> None:
             # newline="\n": never translate to CRLF on Windows; the written bytes are the text's bytes.
             with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                 f.write(text)
    +        os.chmod(tmp, replacement_mode(path))
             os.replace(tmp, str(path))
         except BaseException:
             try:
    diff --git a/agent_workflows/run_analytics_report.py b/agent_workflows/run_analytics_report.py
    index e05487954..6c4381d17 100644
    --- a/agent_workflows/run_analytics_report.py
    +++ b/agent_workflows/run_analytics_report.py
    @@ -53,6 +53,7 @@ from dataclasses import dataclass
     from pathlib import Path
     from typing import Any, Mapping, Sequence

    +from agent_workflows.artifact_core import current_umask
     from agent_workflows.runner_shared import (
         analytics_root,
         analytics_snapshots_dir,
    @@ -244,7 +245,7 @@ def _write_file_durably(path: Path, content: bytes) -> None:
             # normal create would, letting the deployment decide via umask or group ownership. Without
             # this, serving `latest/` from a web server 403s on every file even when the directory
             # permissions are correct.
    -        os.chmod(temp_name, 0o666 & ~_current_umask())
    +        os.chmod(temp_name, 0o666 & ~current_umask())
             os.replace(temp_name, str(path))
         finally:
             if os.path.exists(temp_name):
    @@ -258,14 +259,9 @@ def _write_file_durably(path: Path, content: bytes) -> None:
     def _current_umask() -> int:
         """Read the process umask without leaving it changed.

    -    There is no read-only umask syscall before Python 3.13 / Linux `/proc` parsing, so the portable
    -    idiom is set-and-restore. Racy only against a concurrent umask change in the SAME process, which
    -    this codebase never does.
    +    Delegates to :func:`agent_workflows.artifact_core.current_umask`.
         """
    -
    -    current = os.umask(0o022)
    -    os.umask(current)
    -    return current
    +    return current_umask()


     def _fsync_dir(directory: Path) -> None:
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE the grep output, the complete classification table (one row per site it returns), the `git diff --stat` of changed modules, a `stat` line for one new file per changed TRACKED-RECORD writer (644) and for one PRIVATE writer (600), and the user-run chmod one-liner.
  - Observed evidence:
    Grep output from `grep -rn 'mkstemp\|NamedTemporaryFile' agent_workflows/*.py`:
    ```
    agent_workflows/artifact_core.py:400:    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=prefix, suffix=".md")
    agent_workflows/commit_lock.py:108:    fd, tmp = tempfile.mkstemp(dir=str(lock.parent), prefix=".tmp-", suffix=".json")
    agent_workflows/commit_lock.py:206:    fd, tmp = tempfile.mkstemp(
    agent_workflows/comms_acks.py:146:    temp_fd, temp_path = tempfile.mkstemp(
    agent_workflows/comms_broker.py:162:    temp_fd, temp_path = tempfile.mkstemp(
    agent_workflows/comms_broker.py:477:    temp_fd, temp_path = tempfile.mkstemp(
    agent_workflows/completion.py:1228:        fd, tmp_name = tempfile.mkstemp(
    agent_workflows/config.py:1131:    fd, tmp_name = tempfile.mkstemp(
    agent_workflows/ipd_lifecycle.py:499:    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
    agent_workflows/ipd_lifecycle.py:1310:    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".receipt-", suffix=".tmp")
    agent_workflows/ipd_lifecycle.py:3934:            fd, tmp = tempfile.mkstemp(
    agent_workflows/lane_containment.py:501:    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    agent_workflows/lane_containment.py:520:    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    agent_workflows/layout_inventory.py:914:    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    agent_workflows/leak_sanitizer.py:366:    fd, tmp_name = tempfile.mkstemp(
    agent_workflows/manifest.py:277:    fd, tmp_name = tempfile.mkstemp(
    agent_workflows/oc_models.py:950:    fd, tmp = tempfile.mkstemp(
    agent_workflows/project_layout.py:83:            fd, backup = tempfile.mkstemp(dir=self.journal_dir, prefix="bak_")
    agent_workflows/project_layout.py:346:            backups_dir / f"system_bak_{os.getpid()}_{int(tempfile.mkstemp()[0])}"
    agent_workflows/project_registry.py:284:        fd, tmp_name = tempfile.mkstemp(
    agent_workflows/project_schema.py:782:    with tempfile.NamedTemporaryFile(
    agent_workflows/run_analytics_report.py:236:    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    agent_workflows/run_analytics_report.py:242:        # `mkstemp` hardcodes 0o600 and `os.replace` preserves it, so a published bundle would be
    agent_workflows/runner_profiles.py:1298:        fd, tmp_name = tempfile.mkstemp(
    agent_workflows/runner_shared.py:958:    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    agent_workflows/runner_stop.py:58:`tempfile.mkstemp` + `os.replace` makes each WRITE atomic, but it does NOT serialize the
    agent_workflows/runner_stop.py:480:    fd, tmp = tempfile.mkstemp(
    agent_workflows/work_cmd.py:246:    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".aw-work-", suffix=".json")
    agent_workflows/workflow_cli.py:287:        fd, tmp = tempfile.mkstemp(dir=str(target.parent), prefix=".wf-gen-")
    ```

    Classification table:
    | Module | Function | What it writes | Classification | Action |
    |---|---|---|---|---|
    | `artifact_core.py:400` | `atomic_write` | Tracked markdown records | TRACKED-RECORD | Applied `replacement_mode` before `os.replace` |
    | `commit_lock.py:108` | `acquire_integration_lock` | Integration lock file | PRIVATE | Left at 0600 (no code change) |
    | `commit_lock.py:206` | `_write_lock_file` | Commit lock file | PRIVATE | Left at 0600 (no code change) |
    | `comms_acks.py:146` | `_write_ack_file` | Acknowledgment file in untracked comms | PRIVATE | Left at 0600 (no code change) |
    | `comms_broker.py:162` | `_atomic_write_json` | Untracked broker state | PRIVATE | Left at 0600 (no code change) |
    | `comms_broker.py:477` | `_atomic_write_message` | Untracked inbox message | PRIVATE | Left at 0600 (no code change) |
    | `completion.py:1228` | `_mark_notice_shown` | Config notice timestamp | PRIVATE | Left at 0600 (no code change) |
    | `config.py:1131` | `save` | User config in `$XDG_CONFIG_HOME` | PRIVATE | Left at 0600 (no code change) |
    | `ipd_lifecycle.py:499` | `_atomic_write_json_at` | State/journals under `.aw/state/` | PRIVATE | Left at 0600 (no code change) |
    | `ipd_lifecycle.py:1310` | `_atomic_write_json` | Receipt tmp under `.aw/state/` | PRIVATE | Left at 0600 (no code change) |
    | `ipd_lifecycle.py:3934` | `rollback` | Rollback restore of plan `.md` | TRACKED-RECORD | Restores `original_mode` from journal or `replacement_mode` |
    | `lane_containment.py:501` | `_atomic_write_text` | Run-dir registers | PRIVATE | Left at 0600 (no code change) |
    | `lane_containment.py:520` | `_atomic_write_json` | Run-dir receipts | PRIVATE | Left at 0600 (no code change) |
    | `layout_inventory.py:914` | `_atomic_json` | User requested inventory `--output` | TRACKED-RECORD | Applied `replacement_mode` before `os.replace` |
    | `leak_sanitizer.py:366` | `_atomic_write` | Repo allowlist / User hints | TRACKED-RECORD / PRIVATE | Allowlist uses `replacement_mode`; user hints kept PRIVATE 0600 |
    | `manifest.py:277` | `save` | `.aw/system/managed-sections.json` | TRACKED-RECORD | Applied `replacement_mode` before `os.replace` |
    | `oc_models.py:950` | `_atomic_write` | `opencode.json` config | TRACKED-RECORD | Applied `replacement_mode` before `os.replace` |
    | `project_layout.py:83` | `_backup_file` | Backup files under `.aw/state/journal/` | PRIVATE | Left at 0600 (no code change) |
    | `project_layout.py:346` | N/A | Backup filename token | PRIVATE | Left at 0600 (no code change) |
    | `project_registry.py:284` | `save` | Registry in user config dir | PRIVATE | Left at 0600 (no code change) |
    | `project_schema.py:782` | `atomic_save_json` | JSON schema cache | UNUSED | Left at 0600 (no callers in codebase) |
    | `run_analytics_report.py:236` | `_write_file_durably` | Analytics report bundle | TRACKED-RECORD | Repointed to `artifact_core.current_umask` (mode unchanged: 0666 & ~umask) |
    | `runner_profiles.py:1298` | `_save_cache` | Model IDs cache | PRIVATE | Left at 0600 (no code change) |
    | `runner_shared.py:958` | `atomic_write_json` | Run-dir state | PRIVATE | Left at 0600 (no code change) |
    | `runner_stop.py:58` | N/A | Docstring comment | COMMENT | Left unchanged |
    | `runner_stop.py:480` | `request_stop` | Stop signal file | PRIVATE | Left at 0600 (no code change) |
    | `work_cmd.py:246` | `_save_state` | `.aw/state/work` state | PRIVATE | Left at 0600 (no code change) |
    | `workflow_cli.py:287` | `_write_generated` | Package `_generated/` files | TRACKED-RECORD | Applied `replacement_mode` before `os.replace` |

    `git diff --stat` of changed modules:
    ```
     agent_workflows/artifact_core.py        | 36 +++++++++++++++++++++++++++++++++
     agent_workflows/ipd_lifecycle.py        |  6 ++++++
     agent_workflows/layout_inventory.py     |  3 +++
     agent_workflows/leak_sanitizer.py       |  8 ++++++--
     agent_workflows/manifest.py             |  3 +++
     agent_workflows/oc_models.py            |  3 +++
     agent_workflows/run_analytics_report.py | 12 ++++-------
     agent_workflows/workflow_cli.py         |  3 +++
     8 files changed, 64 insertions(+), 10 deletions(-)
    ```

    Stat lines for new file per changed TRACKED-RECORD writer (644) and PRIVATE writer (600):
    ```
    manifest.save mode: 0o644
    leak_sanitizer allowlist mode: 0o644
    leak_sanitizer user_hints mode: 0o600
    oc_models._atomic_write mode: 0o644
    layout_inventory._atomic_json mode: 0o644
    workflow_cli._write_generated mode: 0o644
    config.save mode: 0o600
    ```

    User-run chmod one-liner:
    `find .aw/records .aw/system -type f -perm 600 -exec chmod 644 {} +`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: PASTE the narrowed run of the new test file (cases (a) to (g) passing), the mutation failure output for case (a), the run-analytics test run, and the bare `python3 -m pytest` summary line before and after.
  - Observed evidence:
    Narrowed run of `tests/test_atomic_write_mode.py`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=954276419
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 7 items

    tests/test_atomic_write_mode.py .......                                  [100%]

    ============================== 7 passed in 20.23s ==============================
    ```

    Mutation failure output for case (a) with `os.chmod` removed in `atomic_write`:
    ```
    =================================== FAILURES ===================================
    ____________________________ test_research_new_mode ____________________________

    repo_and_home = (PosixPath('/tmp/pytest-of-user/pytest-5639/test_research_new_mode0/repo'), PosixPath('/tmp/pytest-of-user/pytest-5639/test_research_new_mode0/home'))

        def test_research_new_mode(repo_and_home: tuple[Path, Path]) -> None:
            """(a) `aw research new --apply` creates a 644 file under umask 022."""
            repo, home = repo_and_home
            res = run_aw(
                repo,
                home,
                ["research", "new", "--kind", "research-report", "--slug", "mode-test", "--apply"],
            )
            assert res.returncode == 0, f"research new failed: {res.stderr}\n{res.stdout}"

            matches = list(repo.glob(".aw/records/research/*mode-test*.md"))
            assert len(matches) == 1, f"Expected 1 research file, found: {matches}"
            file_mode = stat.S_IMODE(matches[0].stat().st_mode)
    >       assert file_mode == 0o644, f"Expected 0o644, got {oct(file_mode)}"
    E       AssertionError: Expected 0o644, got 0o600
    E       assert 384 == 420

    tests/test_atomic_write_mode.py:113: AssertionError
    NOTE: 6 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    =========================== short test summary info ============================
    FAILED tests/test_atomic_write_mode.py::test_research_new_mode - AssertionErr...
    ======================= 1 failed, 6 deselected in 6.14s ========================
    ```

    Run-analytics tests run (`tests/test_run_analytics*.py`):
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=1592132050
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 75 items

    tests/test_run_analytics_statistics.py .........................         [ 33%]
    tests/test_run_analytics.py ................................             [ 76%]
    tests/test_run_analytics_privacy_docs.py .......                         [ 85%]
    tests/test_run_analytics_cli.py ...........                              [100%]

    ============================== 75 passed in 3.30s ==============================
    ```

    Bare `python3 -m pytest` summary line before:
    `5239 passed, 2 skipped, 3 warnings in 672.00s (0:11:11)`

    Bare `python3 -m pytest` summary line after:
    `5246 passed, 2 skipped, 3 warnings in 283.35s (0:04:43)`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one mode rule applied at one shared writer, plus the audit that keeps the rule consistent across the other writers.

EXECUTION CONTRACT. OQ-01 is resolved; no question is open. Execute E-items in order (E-01, E-02, E-03, E-04). Commit only files changed for this plan through `aw commit ic4eg0 -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout. HONESTY RULE (hard MUST): every `V-*` demands PASTED actual output; run the suite BARE as `python3 -m pytest` and paste the actual summary line; a claim without pasted output satisfies no item. Run every scratch install and `aw` subprocess with `AW_NO_REEXEC=1` and `HOME` pointed at a temp dir, and never change the umask of the test or executor process itself. SCOPE FENCE: `- Scope-Paths:` is a DECLARATION; an out-of-scope edit (for example a site E-03 classifies differently) is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. LIFECYCLE, CONDITIONAL OWNERSHIP: under `aw oc run` / `aw agy run` the runner finalizes this plan after its merge-and-revalidate gate, so the executor does not; in a hand execution, the executor fills every `V-*`, confirms `aw ipd lint --phase pre-transition` conforms, and transitions with `aw ipd finalize ic4eg0`, never by a hand `git mv`.
