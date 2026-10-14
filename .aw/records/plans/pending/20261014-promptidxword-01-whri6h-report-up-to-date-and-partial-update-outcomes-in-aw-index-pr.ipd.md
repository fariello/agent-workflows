# IPD: Report up-to-date and partial-update outcomes in aw index prompts human output

- Date: 2026-10-14
- Kind: child
- Concern: `prompts_index.run_index` compares `new_json` and `new_md` against disk (`json_changed` and `md_changed`) and skips writing unchanged files, and its `--agent`/`--json` branch (`artifact_core.emit_index_write_result`) reports `wrote`, `up to date`, or `updated` accordingly, but its human output branch ignores both flags and unconditionally prints `wrote INDEX.json (N prompts)` and `wrote INDEX.md` on every run, unlike `plans_index.run_index` and `research_index.run_index` which render the four `(json_changed, md_changed)` states (`wrote`, `up to date`, and `updated` for `INDEX.md` or `INDEX.json` alone) with the repo-relative directory prefix via `Term.status_256`.
- Scope: Update the human output block of `prompts_index.run_index` in `agent_workflows/prompts_index.py` to render the four `(json_changed, md_changed)` outcome states (`up to date`, `wrote`, and `updated` for `INDEX.md` or `INDEX.json`) with `Term(color=_color)` and the styled repo-relative prompts directory prefix matching `plans_index.run_index` and `research_index.run_index`; add in-process change-detection and ANSI/outcome-word tests in `tests/test_prompts_index.py`; update `HUMAN_FIRST_RUN["prompts"]` and `HUMAN_SECOND_RUN["prompts"]` and add partial-update human subprocess assertions in `tests/test_index_write_agent_records.py`; and record the fix in `CHANGELOG.md`.
- Scope-Paths: agent_workflows/prompts_index.py, tests/test_prompts_index.py, tests/test_index_write_agent_records.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: vcqobe
- Blocks-Release: next
- Set: promptidxword
- Order: 1
- Highest E allocated: 04
- Author: Antigravity
- Id: whri6h

## Workflow history
- 2026-10-14 to-review (aw set): status set to to-review

- 2026-10-14 draft (Antigravity): created from backlog item `vcqobe`.

## Goal

Make `aw index prompts` (and `aw prompts index`) report the actual write outcome (`wrote`, `up to date`, or `updated` for `INDEX.md` or `INDEX.json` alone) with the repo-relative prompts directory prefix on its human output path, matching `aw index plans`, `aw index research`, and the `--agent`/`--json` summary already emitted by `artifact_core.emit_index_write_result`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Align prompts_index human output with plans_index and research_index

- [ ] E-01 In `agent_workflows/prompts_index.py` (`run_index`), replace the two unconditional `print(f"wrote {INDEX_JSON} ({len(entries)} prompts)")` and `print(f"wrote {INDEX_MD}")` lines inside `if not getattr(args, "quiet", False):` with the four-branch `Term` status line used by `plans_index.run_index` and `research_index.run_index`: resolve `_color` via `select_output(args).color` (falling back to `None if not getattr(args, "no_color", False) else False` on `Exception`), construct `term = Term(color=_color)`, compute `rel_dir` via `prompts_dir.relative_to(repo_root).as_posix()` (falling back to `prompts_dir.as_posix()` on `ValueError`), `dir_prefix = f"{rel_dir}/" if rel_dir and not rel_dir.endswith("/") else rel_dir`, and `dir_styled = term.color256(dir_prefix, 33)`, and emit `term.status_256("up to date", width=12)` with `f"{dir_styled}{INDEX_JSON}, {INDEX_MD} ({len(entries)} prompts)"` when `not json_changed and not md_changed`, `term.status_256("wrote", width=12)` with `f"{dir_styled}{INDEX_JSON}, {INDEX_MD} ({len(entries)} prompts)"` when `json_changed and md_changed`, `term.status_256("updated", width=12)` with `f"{dir_styled}{INDEX_MD} ({INDEX_JSON} up to date; {len(entries)} prompts)"` when `md_changed` alone, and `term.status_256("updated", width=12)` with `f"{dir_styled}{INDEX_JSON} ({INDEX_MD} up to date; {len(entries)} prompts)"` when `json_changed` alone.
  - Depends on: none
  - Expected outcome: `prompts_index.run_index` emits `wrote`, `up to date`, or `updated` with the repo-relative prompts directory prefix in human mode according to `(json_changed, md_changed)` while preserving `quiet=True`, `--agent`, `--json`, and `--check` behavior unchanged.
  - Execution state: pending

### Task group 2: In-process and subprocess behavior tests and changelog

- [ ] E-02 In `tests/test_prompts_index.py`, add `RunIndexOutputTests` and `IndexOutcomeWordsAreNotLifecycleStatusesTests` (mirroring the test classes in `tests/test_plans_index.py` and `tests/test_research_index.py`) verifying: (a) first run of `prompts_index.run_index` with `no_color=True` returns `0` and prints `"wrote        .aw/records/prompts/INDEX.json, INDEX.md (3 prompts)\n"`; (b) second run unchanged returns `0` and prints `"up to date   .aw/records/prompts/INDEX.json, INDEX.md (3 prompts)\n"`; (c) third run after modifying only `INDEX.md` returns `0` and prints `"updated      .aw/records/prompts/INDEX.md (INDEX.json up to date; 3 prompts)\n"`; (d) fourth run after modifying only `INDEX.json` returns `0` and prints `"updated      .aw/records/prompts/INDEX.json (INDEX.md up to date; 3 prompts)\n"`; (e) fifth run with `quiet=True` returns `0` and emits `""`; (f) under `FORCE_COLOR=1`, `wrote` and `up to date` render with `\033[1;38;5;46m...\033[0m` and never `?`; and (g) `--agent`, `--json`, `--no-color`, `NO_COLOR=1`, `TERM=dumb`, and piped non-TTY stdout emit zero `\033` escape sequences.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_prompts_index.py` passes with all new human output, partial-update, `quiet=True`, and color/no-ANSI tests green.
  - Execution state: pending

- [ ] E-03 In `tests/test_index_write_agent_records.py`, update `HUMAN_FIRST_RUN["prompts"]` to `"wrote        .aw/records/prompts/INDEX.json, INDEX.md (1 prompts)\n"` and `HUMAN_SECOND_RUN["prompts"]` to `"up to date   .aw/records/prompts/INDEX.json, INDEX.md (1 prompts)\n"`, and extend `IndexWriteSubprocessTests.test_human_invariance_per_verb` to also verify the third run after appending a comment to `INDEX.md` (`updated      <rel_dir>/INDEX.md (INDEX.json up to date; 1 <noun>)\n`) and the fourth run after overwriting `INDEX.json` (`updated      <rel_dir>/INDEX.json (INDEX.md up to date; 1 <noun>)\n`) across `plans`, `prompts`, and `research`.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_index_write_agent_records.py` passes with `prompts` human subprocess output verified across first run (`wrote`), second run (`up to date`), and single-file partial updates (`updated`).
  - Execution state: pending

- [ ] E-04 Add a `CHANGELOG.md` entry under `## [Unreleased]` -> `### Fixed` documenting that `aw index prompts` now reports `wrote`, `up to date`, or `updated` with the repo-relative prompts directory path on its human output path instead of printing `wrote` on every run (using no em or en dashes), and run the verification suite (`python3 -m pytest tests/test_prompts_index.py tests/test_index_write_agent_records.py`, `python3 -m pytest`, and `python3 -m agent_workflows check all`).
  - Depends on: E-02, E-03
  - Expected outcome: `CHANGELOG.md` documents the fix with zero em/en dashes and the test suite and `aw check all` pass with zero errors.
  - Execution state: pending

## Project conventions discovered (Step 0)

- **Index human output format and lifecycle-resolver exemption (`agent_workflows/plans_index.py`, `agent_workflows/research_index.py`)**: Both `plans_index.run_index` (around `if not json_changed and not md_changed:`) and `research_index.run_index` (around `if not json_changed and not md_changed:`) format human output via `Term(color=_color)` with `term.status_256(..., width=12)` and `term.color256(dir_prefix, 33)` across four states (`up to date`, `wrote`, `updated` for `INDEX.md`, and `updated` for `INDEX.json`). As documented in IPD `9zvl2w` E-01 and spec `uonrjg` R10.3 (criteria A11, A14, A20), `up to date`, `wrote`, and `updated` are generic command outcome words kept outside the lifecycle status resolver (`resolve_lifecycle`), which would otherwise map them to `?`.
- **Color precedence via `select_output` (`agent_workflows/result_types.py`)**: `select_output(args)` (`agent_workflows/result_types.py` around `def select_output`) resolves `ctx.color` using `should_color(stdout, override=...)` so that `--no-color`, `NO_COLOR=1`, `TERM=dumb`, `--agent`, `--json`, and non-TTY pipes never emit ANSI escape sequences.
- **Shared machine write-result summary parity (`agent_workflows/artifact_core.py`)**: `artifact_core.emit_index_write_result` (`agent_workflows/artifact_core.py` around `def emit_index_write_result`, added in IPD `sn2svz`) already computes its `summary` field for `target="prompts"`, `noun="prompts"` using the same four `(json_changed, md_changed)` branches (`up to date: <dir_prefix>INDEX.json, INDEX.md (<count> prompts)`, `wrote <dir_prefix>INDEX.json, INDEX.md (<count> prompts)`, `updated <dir_prefix>INDEX.md (INDEX.json up to date; <count> prompts)`, `updated <dir_prefix>INDEX.json (INDEX.md up to date; <count> prompts)`).
- **Pinned legacy strings in `tests/test_index_write_agent_records.py`**: IPD `sn2svz` E-01 explicitly pinned `HUMAN_FIRST_RUN["prompts"]` and `HUMAN_SECOND_RUN["prompts"]` to `"wrote INDEX.json (1 prompts)\nwrote INDEX.md\n"` to keep human output byte-identical while fixing `--agent`/`--json`, and filed `vcqobe` to own updating the human output path of `prompts_index.run_index`.

## Findings

| ID | Severity | Location | Finding |
| :--- | :--- | :--- | :--- |
| F-01 | medium | `agent_workflows/prompts_index.py` (`run_index`) | `prompts_index.run_index` computes `json_changed` and `md_changed` and skips writing `INDEX.json` and `INDEX.md` when unchanged, and passes both booleans to `_core.emit_index_write_result` for `--agent` and `--json`. However, its human branch (`if not getattr(args, "quiet", False):`) ignores `json_changed` and `md_changed` and executes `print(f"wrote {INDEX_JSON} ({len(entries)} prompts)")` followed by `print(f"wrote {INDEX_MD}")` on every run, so a human caller cannot tell whether files were written, updated, or already up to date. |
| F-02 | low | `tests/test_index_write_agent_records.py` (`HUMAN_FIRST_RUN`, `HUMAN_SECOND_RUN`), `tests/test_prompts_index.py` | `tests/test_index_write_agent_records.py` pins the pre-`vcqobe` two-line `"wrote INDEX.json (1 prompts)\nwrote INDEX.md\n"` string on both `HUMAN_FIRST_RUN["prompts"]` and `HUMAN_SECOND_RUN["prompts"]` (as noted in IPD `sn2svz` E-01), and `tests/test_prompts_index.py` has no `RunIndexOutputTests` or `IndexOutcomeWordsAreNotLifecycleStatusesTests` coverage despite listing `- run_index CLI behavior` in its module docstring. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/prompts_index.py` (`run_index`)**:
   - In `run_index`, replace the final `if not getattr(args, "quiet", False):` print block:
     ```python
     if not getattr(args, "quiet", False):
         print(f"wrote {INDEX_JSON} ({len(entries)} prompts)")
         print(f"wrote {INDEX_MD}")
     ```
     with the four-state `Term` block matching `plans_index.run_index` and `research_index.run_index`:
     ```python
     if not getattr(args, "quiet", False):
         from agent_workflows.result_types import select_output
         from agent_workflows.term import Term

         try:
             _ctx = select_output(args)
             _color = _ctx.color
         except Exception:
             _color = None if not getattr(args, "no_color", False) else False
         term = Term(color=_color)
         try:
             rel_dir = prompts_dir.relative_to(repo_root).as_posix()
         except ValueError:
             rel_dir = prompts_dir.as_posix()
         dir_prefix = f"{rel_dir}/" if rel_dir and not rel_dir.endswith("/") else rel_dir
         dir_styled = term.color256(dir_prefix, 33)

         if not json_changed and not md_changed:
             status_lbl = term.status_256("up to date", width=12)
             files_str = f"{dir_styled}{INDEX_JSON}, {INDEX_MD}"
             term.line(f"{status_lbl} {files_str} ({len(entries)} prompts)")
         elif json_changed and md_changed:
             status_lbl = term.status_256("wrote", width=12)
             files_str = f"{dir_styled}{INDEX_JSON}, {INDEX_MD}"
             term.line(f"{status_lbl} {files_str} ({len(entries)} prompts)")
         elif md_changed:
             status_lbl = term.status_256("updated", width=12)
             files_str = f"{dir_styled}{INDEX_MD}"
             term.line(
                 f"{status_lbl} {files_str} ({INDEX_JSON} up to date; {len(entries)} prompts)"
             )
         else:
             status_lbl = term.status_256("updated", width=12)
             files_str = f"{dir_styled}{INDEX_JSON}"
             term.line(
                 f"{status_lbl} {files_str} ({INDEX_MD} up to date; {len(entries)} prompts)"
             )
     ```

2. **`tests/test_prompts_index.py`**:
   - Add `RunIndexOutputTests` testing `prompts_index.run_index` across all four `(json_changed, md_changed)` combinations (`wrote`, `up to date`, `updated` when only `INDEX.md` changed, and `updated` when only `INDEX.json` changed) plus `quiet=True`.
   - Add `IndexOutcomeWordsAreNotLifecycleStatusesTests` verifying that under `FORCE_COLOR=1` the outcome words render with `\033[1;38;5;46m...\033[0m` and never `?`, and that `--agent`, `--json`, `--no-color`, `NO_COLOR=1`, `TERM=dumb`, and piped non-TTY stdout emit no `\033`.

3. **`tests/test_index_write_agent_records.py`**:
   - Update `HUMAN_FIRST_RUN["prompts"]` to `"wrote        .aw/records/prompts/INDEX.json, INDEX.md (1 prompts)\n"` and `HUMAN_SECOND_RUN["prompts"]` to `"up to date   .aw/records/prompts/INDEX.json, INDEX.md (1 prompts)\n"`.
   - Extend `test_human_invariance_per_verb` to also test single-file partial updates (`INDEX.md` only and `INDEX.json` only) in human mode across `plans`, `prompts`, and `research`.

4. **`CHANGELOG.md`**:
   - Add an entry under `## [Unreleased]` -> `### Fixed` documenting that `aw index prompts` now reports `wrote`, `up to date`, and `updated` with the repo-relative prompts directory prefix in human mode instead of printing `wrote` on every run.

## Deferred / out of scope (with reason)

- None.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- In-process unit and behavior tests in `tests/test_prompts_index.py` (`RunIndexOutputTests` and `IndexOutcomeWordsAreNotLifecycleStatusesTests`) exercising all four `(json_changed, md_changed)` human output branches, `quiet=True`, `FORCE_COLOR=1`, and no-ANSI modes.
- Subprocess CLI behavior tests in `tests/test_index_write_agent_records.py` (`test_human_invariance_per_verb`) driving `aw index prompts`, `aw index plans`, and `aw index research` across first run (`wrote`), second run (`up to date`), and partial updates (`updated`).
- Full test suite (`python3 -m pytest`) and repository conformance checks (`python3 -m agent_workflows check all`).

## Spec / documentation sync

- N/A with reason: `prompts_index.py` module docstring and `.aw/records/specs/` do not specify the legacy two-line `wrote INDEX.json` / `wrote INDEX.md` wording, and aligning `aw index prompts` with `aw index plans` and `aw index research` brings it into conformance with spec `uonrjg` R10.3 (criteria A11/A14/A20). Only `CHANGELOG.md` requires an `[Unreleased]` entry.

## Open questions

### OQ-01: Should `prompts_index.run_index` human output adopt the single-line four-state `Term.status_256` format shared by `plans_index.run_index`, `research_index.run_index`, and `artifact_core.emit_index_write_result`, or keep a two-line bare `print` format without directory prefix?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved from repository evidence in favor of adopting the shared single-line four-state `Term.status_256` format (`wrote`, `up to date`, and `updated` with the repo-relative `prompts_dir` prefix): (1) `plans_index.run_index` (`agent_workflows/plans_index.py` around `if not json_changed and not md_changed:`) and `research_index.run_index` (`agent_workflows/research_index.py` around `if not json_changed and not md_changed:`) both use this exact `Term(color=_color)` and `term.status_256(..., width=12)` structure; (2) `artifact_core.emit_index_write_result` (`agent_workflows/artifact_core.py` around `def emit_index_write_result`, added in IPD `sn2svz`) already uses the same four-state single-line summary with `<dir_prefix>INDEX.json, INDEX.md (<count> prompts)` for `target="prompts"`; and (3) `aw index all` loops across `("plans", "prompts", "research")` in `cli._run_noun_verb`, so adopting the shared `Term` format produces three uniform status lines and honors the color-precedence contract (`select_output(args).color`) established in IPD `9zvl2w`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: `git diff agent_workflows/prompts_index.py` showing `run_index` rendering `up to date`, `wrote`, and both `updated` branches via `Term(color=_color)` and `term.status_256(..., width=12)` with `dir_styled = term.color256(dir_prefix, 33)`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted output of `python3 -m pytest tests/test_prompts_index.py` showing all tests passing, including `RunIndexOutputTests` (`wrote`, `up to date`, `updated` on `INDEX.md` only, `updated` on `INDEX.json` only, and `quiet=True`) and `IndexOutcomeWordsAreNotLifecycleStatusesTests` (`FORCE_COLOR=1` and no-ANSI modes).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted output of `python3 -m pytest tests/test_index_write_agent_records.py` showing all tests passing, including `test_human_invariance_per_verb` verifying `wrote`, `up to date`, and single-file `updated` outputs across `plans`, `prompts`, and `research`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git diff CHANGELOG.md` showing the new `[Unreleased]` -> `### Fixed` entry (with zero em/en dashes) plus pasted output of `python3 -m pytest` and `python3 -m agent_workflows check all` exiting `0`.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This IPD is authored to `to-review` status from backlog item `vcqobe` and awaits review and approval before execution. Upon execution and passing validation (`V-01` through `V-04`), finalize the plan via `aw ipd finalize whri6h`.
