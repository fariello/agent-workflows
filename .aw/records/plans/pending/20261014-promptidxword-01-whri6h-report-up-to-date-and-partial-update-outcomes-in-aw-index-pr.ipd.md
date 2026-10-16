# IPD: Report up-to-date and partial-update outcomes in aw index prompts human output

- Date: 2026-10-14
- Kind: child
- Concern: `prompts_index.run_index` compares `new_json` and `new_md` against disk (`json_changed` and `md_changed`) and skips writing unchanged files, and its `--agent`/`--json` branch (`artifact_core.emit_index_write_result`) reports `wrote`, `up to date`, or `updated` accordingly, but its human output branch ignores both flags and unconditionally prints `wrote INDEX.json (N prompts)` and `wrote INDEX.md` on every run (re-measured at review through `tests.conformance_matrix.run_cli(["index", "prompts"], ...)` on the `_setup_fixture_for_verb` fixture: first run, unchanged second run, `INDEX.md`-only edit, and `INDEX.json`-only edit all printed `wrote INDEX.json (1 prompts)\nwrote INDEX.md\n`, while `plans` and `research` printed `wrote`, `up to date`, and the two `updated` lines), unlike `plans_index.run_index` and `research_index.run_index` which render the four `(json_changed, md_changed)` states (`wrote`, `up to date`, and `updated` for `INDEX.md` or `INDEX.json` alone) with the repo-relative directory prefix via `Term.status_256`.
- Scope: Update the human output block of `prompts_index.run_index` in `agent_workflows/prompts_index.py` to render the four `(json_changed, md_changed)` outcome states (`up to date`, `wrote`, and `updated` for `INDEX.md` or `INDEX.json`) with `Term(color=_color)` and the styled repo-relative prompts directory prefix matching `plans_index.run_index` and `research_index.run_index`; add in-process change-detection and ANSI/outcome-word tests in `tests/test_prompts_index.py`; update `HUMAN_FIRST_RUN["prompts"]` and `HUMAN_SECOND_RUN["prompts"]` and add partial-update human subprocess assertions in `tests/test_index_write_agent_records.py`; and record the fix in `CHANGELOG.md`.
- Scope-Paths: agent_workflows/prompts_index.py, tests/test_prompts_index.py, tests/test_index_write_agent_records.py, CHANGELOG.md, .aw/records/plans/pending/20261014-promptidxword-01-whri6h-report-up-to-date-and-partial-update-outcomes-in-aw-index-pr.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: vcqobe
- Blocks-Release: next
- Set: promptidxword
- Order: 1
- Highest E allocated: 04
- Author: Antigravity
- Id: whri6h
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. Record: .aw/records/reviews/20261014-promptidxword-01-whri6h-report-up-to-date-and-partial-update-outcomes-in-aw-index-pr.review.md Round 1
- 2026-10-14 to-review (aw set): status set to to-review

- 2026-10-14 draft (Antigravity): created from backlog item `vcqobe`.

## Goal

Make `aw index prompts` (and `aw prompts index`) report the actual write outcome (`wrote`, `up to date`, or `updated` for `INDEX.md` or `INDEX.json` alone) with the repo-relative prompts directory prefix on its human output path, matching `aw index plans`, `aw index research`, and the `--agent`/`--json` summary already emitted by `artifact_core.emit_index_write_result`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Align prompts_index human output with plans_index and research_index

- [x] E-01 In `agent_workflows/prompts_index.py` (`run_index`), replace the two unconditional `print(f"wrote {INDEX_JSON} ({len(entries)} prompts)")` and `print(f"wrote {INDEX_MD}")` lines inside `if not getattr(args, "quiet", False):` with the four-branch `Term` status line used by `plans_index.run_index` and `research_index.run_index`: resolve `_color` via `select_output(args).color` (falling back to `None if not getattr(args, "no_color", False) else False` on `Exception`), construct `term = Term(color=_color)`, compute `rel_dir` via `prompts_dir.relative_to(repo_root).as_posix()` (falling back to `prompts_dir.as_posix()` on `ValueError`), `dir_prefix = f"{rel_dir}/" if rel_dir and not rel_dir.endswith("/") else rel_dir`, and `dir_styled = term.color256(dir_prefix, 33)`, and emit `term.status_256("up to date", width=12)` with `f"{dir_styled}{INDEX_JSON}, {INDEX_MD} ({len(entries)} prompts)"` when `not json_changed and not md_changed`, `term.status_256("wrote", width=12)` with `f"{dir_styled}{INDEX_JSON}, {INDEX_MD} ({len(entries)} prompts)"` when `json_changed and md_changed`, `term.status_256("updated", width=12)` with `f"{dir_styled}{INDEX_MD} ({INDEX_JSON} up to date; {len(entries)} prompts)"` when `md_changed` alone, and `term.status_256("updated", width=12)` with `f"{dir_styled}{INDEX_JSON} ({INDEX_MD} up to date; {len(entries)} prompts)"` when `json_changed` alone.
  - Depends on: none
    Leave everything above that block unchanged: the `--check` branch, the write logic, the `--agent`/`--json` early return through `_core.emit_index_write_result`, and the preceding `if drift and not getattr(args, "quiet", False):` drift-line loop (drift lines still print before the status line, as in `plans_index`). Add a one-line comment pointing at the `plans_index.run_index` note on why these outcome words stay on `Term.status_256` and are not routed through the lifecycle resolver (plan `9zvl2w` E-01). `select_output` is already imported earlier in `run_index` (`from agent_workflows.result_types import select_output` before `ctx = select_output(args)`), so reuse that import; only `Term` needs importing.
  - Expected outcome: `prompts_index.run_index` emits exactly one line, `wrote`, `up to date`, or `updated`, with the repo-relative prompts directory prefix in human mode according to `(json_changed, md_changed)`, and still returns `0`. `quiet=True` still prints nothing (so the `status_set._auto_index_types` caller, which passes `quiet=True`, is unaffected), and `--agent`, `--json`, and `--check` output is unchanged.
  - Execution state: performed

### Task group 2: In-process and subprocess behavior tests and changelog

- [x] E-02 In `tests/test_prompts_index.py`, add `RunIndexOutputTests` and `IndexOutcomeWordsAreNotLifecycleStatusesTests` (mirroring the test classes in `tests/test_plans_index.py` and `tests/test_research_index.py`) driving `prompts_index.run_index(argparse.Namespace(dir=str(root), limit=None, check=False, quiet=..., no_color=..., color=False, agent=..., json=...))` in-process with `contextlib.redirect_stdout` against the existing `PromptsIndexTests.setUp` fixture (three indexable prompts plus one ignored `untracked/` file under `.aw/records/prompts/`; reuse it by a shared fixture helper or base class), verifying: (a) first run of `prompts_index.run_index` with `no_color=True` returns `0` and prints `"wrote        .aw/records/prompts/INDEX.json, INDEX.md (3 prompts)\n"`; (b) second run unchanged returns `0` and prints `"up to date   .aw/records/prompts/INDEX.json, INDEX.md (3 prompts)\n"`; (c) third run after appending text to only `INDEX.md` returns `0` and prints `"updated      .aw/records/prompts/INDEX.md (INDEX.json up to date; 3 prompts)\n"`; (d) fourth run after overwriting only `INDEX.json` (for example with `"{}\n"`) returns `0` and prints `"updated      .aw/records/prompts/INDEX.json (INDEX.md up to date; 3 prompts)\n"`; (e) a run with `quiet=True` after modifying a file returns `0`, emits `""`, and still rewrites the file (assert the on-disk content was restored), so quiet suppresses output and not the write; (f) under `FORCE_COLOR=1`, the output contains `\033[1;38;5;46mwrote\033[0m` on a first run and `\033[1;38;5;46mup to date\033[0m` on a second run, and never `?`; and (g) `--agent`, `--json`, `--no-color`, `NO_COLOR=1`, `TERM=dumb`, and piped non-TTY stdout emit zero `\033` escape sequences (mirroring `test_machine_and_suppressed_modes_emit_no_ansi` in `tests/test_plans_index.py`, including popping `FORCE_COLOR` and `NO_COLOR` from the environment per case). No test reads production source (P16). Before relying on the new tests, show they are non-vacuous: run (a)-(d) once against the unmodified `run_index` (before E-01 lands, or with E-01's hunk temporarily absent via an in-process `mock.patch` only; never a source edit left in the tree) and record that (b), (c) and (d) fail.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_prompts_index.py` passes with all new human output, partial-update, `quiet=True`, and color/no-ANSI tests green.
  - Execution state: performed

- [x] E-03 In `tests/test_index_write_agent_records.py`, update `HUMAN_FIRST_RUN["prompts"]` to `"wrote        .aw/records/prompts/INDEX.json, INDEX.md (1 prompts)\n"` and `HUMAN_SECOND_RUN["prompts"]` to `"up to date   .aw/records/prompts/INDEX.json, INDEX.md (1 prompts)\n"`, and extend `IndexWriteSubprocessTests.test_human_invariance_per_verb` (which drives `tests.conformance_matrix.run_cli(["index", verb], cwd=...)` on the `_setup_fixture_for_verb` fixture) to also verify the third run after appending a comment to `INDEX.md` (`updated      <rel_dir>/INDEX.md (INDEX.json up to date; 1 <noun>)\n`) and the fourth run after overwriting `INDEX.json` with `"{}\n"` (`updated      <rel_dir>/INDEX.json (INDEX.md up to date; 1 <noun>)\n`) across `plans`, `prompts`, and `research`, where `<rel_dir>` is the second value `_setup_fixture_for_verb` returns and `<noun>` is `plans`/`prompts`/`docs`. Add the expected strings as `HUMAN_MD_ONLY_RUN` / `HUMAN_JSON_ONLY_RUN` dicts beside the existing two. Also update the module docstring line "Human invariance: unflagged stdout on fixture matches legacy expected strings byte-exact" to say the prompts strings now match the shared four-state format (`vcqobe`). The plans and research strings were measured at review to already pass the third and fourth runs, so only the prompts row changes behavior.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_index_write_agent_records.py` passes with `prompts` human subprocess output verified across first run (`wrote`), second run (`up to date`), and single-file partial updates (`updated`).
  - Execution state: performed

- [x] E-04 Add one `- Fixed:` bullet to `CHANGELOG.md` under the current `## 2.0.0 (pending)` heading, beside the existing `- Fixed:` bullets (this CHANGELOG has no `## [Unreleased]` or `### Fixed` headings), recording that `aw index prompts` now reports `wrote`, `up to date`, or `updated` with the repo-relative prompts directory path on its human output instead of printing `wrote` on every run (no em or en dashes). Then run the verification suite: `python3 -m pytest tests/test_prompts_index.py tests/test_index_write_agent_records.py`, the bare full suite `python3 -m pytest`, `aw ipd lint --phase pre-transition <this plan>`, and `aw check release-gates`.
  - Depends on: E-02, E-03
  - Expected outcome: `CHANGELOG.md` documents the fix with zero em/en dashes in the added line; the targeted modules and the bare full suite pass; `aw ipd lint --phase pre-transition` conforms and `aw check release-gates` exits 0. (`aw check all` is NOT a pass bar: it exits 1 at HEAD on repository-wide findings unrelated to this plan, measured at review as 27 errors, so demanding exit 0 would be unsatisfiable.)
  - Execution state: performed

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
         # Outcome words, not lifecycle statuses: see the note in plans_index.run_index (9zvl2w E-01).
         # select_output is already imported above (before `ctx = select_output(args)`).
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
   - Extend `test_human_invariance_per_verb` to also test single-file partial updates (`INDEX.md` only and `INDEX.json` only) in human mode across `plans`, `prompts`, and `research`, and refresh the module docstring's human-invariance line.

4. **`CHANGELOG.md`**:
   - Add a `- Fixed:` bullet under `## 2.0.0 (pending)` documenting that `aw index prompts` now reports `wrote`, `up to date`, and `updated` with the repo-relative prompts directory prefix in human mode instead of printing `wrote` on every run.

## Deferred / out of scope (with reason)

- Factoring the four-state human status line now copied in `plans_index.run_index`, `research_index.run_index`, and (after E-01) `prompts_index.run_index` into one shared helper in `artifact_core` (beside `emit_index_write_result`):
  - Carrier-Declined: `vcqobe` asks only that the prompts verb report the real outcome; extracting a helper would touch the two already-correct verbs' human paths, which are outside this plan's scope and its tests. The three copies stay byte-identical in output and are each pinned by `tests/test_index_write_agent_records.py` `test_human_invariance_per_verb`, so a later drift in any one is caught.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- In-process unit and behavior tests in `tests/test_prompts_index.py` (`RunIndexOutputTests` and `IndexOutcomeWordsAreNotLifecycleStatusesTests`) exercising all four `(json_changed, md_changed)` human output branches, `quiet=True`, `FORCE_COLOR=1`, and no-ANSI modes.
- Subprocess CLI behavior tests in `tests/test_index_write_agent_records.py` (`test_human_invariance_per_verb`) driving `aw index prompts`, `aw index plans`, and `aw index research` across first run (`wrote`), second run (`up to date`), and partial updates (`updated`).
- Full test suite run bare (`python3 -m pytest`), `aw ipd lint --phase pre-transition <this plan>`, and `aw check release-gates`.

## Spec / documentation sync

- N/A with reason: `prompts_index.py` module docstring and `.aw/records/specs/` do not specify the legacy two-line `wrote INDEX.json` / `wrote INDEX.md` wording, and aligning `aw index prompts` with `aw index plans` and `aw index research` keeps it consistent with spec `uonrjg` (`.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md`): R10.3 keeps generic `Term` outcomes outside the lifecycle resolver, A11/A14 require no ANSI under `NO_COLOR`, `TERM=dumb`, non-TTY, `--agent` and `--json`, and A20 is the `?` unknown-status path these outcome words must never reach. No spec edit. Only `CHANGELOG.md` requires an entry, under `## 2.0.0 (pending)`.

## Open questions

### OQ-01: Should `prompts_index.run_index` human output adopt the single-line four-state `Term.status_256` format shared by `plans_index.run_index`, `research_index.run_index`, and `artifact_core.emit_index_write_result`, or keep a two-line bare `print` format without directory prefix?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from repository evidence in favor of adopting the shared single-line four-state `Term.status_256` format (`wrote`, `up to date`, and `updated` with the repo-relative `prompts_dir` prefix): (1) `plans_index.run_index` (`agent_workflows/plans_index.py` around `if not json_changed and not md_changed:`) and `research_index.run_index` (`agent_workflows/research_index.py` around `if not json_changed and not md_changed:`) both use this exact `Term(color=_color)` and `term.status_256(..., width=12)` structure; (2) `artifact_core.emit_index_write_result` (`agent_workflows/artifact_core.py` around `def emit_index_write_result`, added in IPD `sn2svz`) already uses the same four-state single-line summary with `<dir_prefix>INDEX.json, INDEX.md (<count> prompts)` for `target="prompts"`; and (3) adopting the shared `Term` format makes the three index verbs print one uniform status line each, and honors the color-precedence contract (`select_output(args).color`) established in IPD `9zvl2w`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted `git diff -- agent_workflows/prompts_index.py` showing that the only changed region is the final human `if not getattr(args, "quiet", False):` block, which now renders `up to date`, `wrote`, and both `updated` branches through `Term(color=_color)`, `term.status_256(..., width=12)` and `dir_styled = term.color256(dir_prefix, 33)`, with the `--check` branch, write logic, `emit_index_write_result` early return, and drift-line loop untouched. Plus pasted stdout of driving `python3 -m agent_workflows index prompts` four times on a scratch fixture under `.aw/state/` (first run, unchanged rerun, `INDEX.md`-only edit, `INDEX.json`-only edit), showing the four expected lines; the observation is produced by the `run_index` block E-01 writes.
  - Observed evidence:
    `git diff -- agent_workflows/prompts_index.py`:
    ```diff
    diff --git a/agent_workflows/prompts_index.py b/agent_workflows/prompts_index.py
    index dff56bc45..e3e49baab 100644
    --- a/agent_workflows/prompts_index.py
    +++ b/agent_workflows/prompts_index.py
    @@ -353,6 +353,41 @@ def run_index(args: argparse.Namespace) -> int:
             for d in drift:
                 print(f"{d.location}: {d.rule}: {d.detail}")
         if not getattr(args, "quiet", False):
    -        print(f"wrote {INDEX_JSON} ({len(entries)} prompts)")
    -        print(f"wrote {INDEX_MD}")
    +        # Outcome words, not lifecycle statuses: see the note in plans_index.run_index (9zvl2w E-01).
    +        # select_output is already imported above (before `ctx = select_output(args)`).
    +        from agent_workflows.term import Term
    +
    +        try:
    +            _ctx = select_output(args)
    +            _color = _ctx.color
    +        except Exception:
    +            _color = None if not getattr(args, "no_color", False) else False
    +        term = Term(color=_color)
    +        try:
    +            rel_dir = prompts_dir.relative_to(repo_root).as_posix()
    +        except ValueError:
    +            rel_dir = prompts_dir.as_posix()
    +        dir_prefix = f"{rel_dir}/" if rel_dir and not rel_dir.endswith("/") else rel_dir
    +        dir_styled = term.color256(dir_prefix, 33)
    +
    +        if not json_changed and not md_changed:
    +            status_lbl = term.status_256("up to date", width=12)
    +            files_str = f"{dir_styled}{INDEX_JSON}, {INDEX_MD}"
    +            term.line(f"{status_lbl} {files_str} ({len(entries)} prompts)")
    +        elif json_changed and md_changed:
    +            status_lbl = term.status_256("wrote", width=12)
    +            files_str = f"{dir_styled}{INDEX_JSON}, {INDEX_MD}"
    +            term.line(f"{status_lbl} {files_str} ({len(entries)} prompts)")
    +        elif md_changed:
    +            status_lbl = term.status_256("updated", width=12)
    +            files_str = f"{dir_styled}{INDEX_MD}"
    +            term.line(
    +                f"{status_lbl} {files_str} ({INDEX_JSON} up to date; {len(entries)} prompts)"
    +            )
    +        else:
    +            status_lbl = term.status_256("updated", width=12)
    +            files_str = f"{dir_styled}{INDEX_JSON}"
    +            term.line(
    +                f"{status_lbl} {files_str} ({INDEX_MD} up to date; {len(entries)} prompts)"
    +            )
         return 0
    ```
    CLI run on scratch fixture under `.aw/state/`:
    ```
    $ python3 -m agent_workflows index prompts --dir .aw/state/scratch_prompts_v01
    wrote        .aw/records/prompts/INDEX.json, INDEX.md (1 prompts)
    $ python3 -m agent_workflows index prompts --dir .aw/state/scratch_prompts_v01
    up to date   .aw/records/prompts/INDEX.json, INDEX.md (1 prompts)
    $ echo "<!-- extra -->" >> .aw/state/scratch_prompts_v01/.aw/records/prompts/INDEX.md
    $ python3 -m agent_workflows index prompts --dir .aw/state/scratch_prompts_v01
    updated      .aw/records/prompts/INDEX.md (INDEX.json up to date; 1 prompts)
    $ echo "{}" > .aw/state/scratch_prompts_v01/.aw/records/prompts/INDEX.json
    $ python3 -m agent_workflows index prompts --dir .aw/state/scratch_prompts_v01
    updated      .aw/records/prompts/INDEX.json (INDEX.md up to date; 1 prompts)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" tests/test_prompts_index.py -v` with every test passing, whose test names show each of E-02's cases (a) to (g) is pinned; plus the pasted non-vacuity run showing (b), (c) and (d) FAIL against the unmodified human block, and `git status --short` showing no stray source edit remains.
  - Observed evidence:
    `python3 -m pytest -o addopts="" tests/test_prompts_index.py -v`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=3266207740
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/whri6h
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 15 items

    tests/test_prompts_index.py::RunIndexOutputTests::test_c_third_run_after_md_only_change_reports_updated PASSED [  6%]
    tests/test_prompts_index.py::RunIndexOutputTests::test_d_fourth_run_after_json_only_change_reports_updated PASSED [ 13%]
    tests/test_prompts_index.py::RunIndexOutputTests::test_b_second_run_reports_up_to_date PASSED [ 20%]
    tests/test_prompts_index.py::RunIndexOutputTests::test_e_quiet_suppresses_output_and_restores_files PASSED [ 26%]
    tests/test_prompts_index.py::RunIndexOutputTests::test_a_first_run_writes_both_indexes PASSED [ 33%]
    tests/test_prompts_index.py::IndexOutcomeWordsAreNotLifecycleStatusesTests::test_f_force_color_renders_generic_outcome_words_and_never_unknown_glyph PASSED [ 40%]
    tests/test_prompts_index.py::IndexOutcomeWordsAreNotLifecycleStatusesTests::test_g_machine_and_suppressed_modes_emit_no_ansi PASSED [ 46%]
    tests/test_prompts_index.py::PromptsIndexTests::test_scan_and_build_index_json PASSED [ 53%]
    tests/test_prompts_index.py::PromptsIndexTests::test_check_drift_stale_index PASSED [ 60%]
    tests/test_prompts_index.py::PromptsIndexTests::test_build_index_md PASSED [ 66%]
    tests/test_prompts_index.py::PromptsIndexTests::test_check_drift_name_metadata_mismatch PASSED [ 73%]
    tests/test_prompts_index.py::PromptsIndexTests::test_check_drift_missing_index PASSED [ 80%]
    tests/test_prompts_index.py::PromptsContentValidatorTests::test_rule_prompt_status_mismatch PASSED [ 86%]
    tests/test_prompts_index.py::PromptsContentValidatorTests::test_rule_prompt_id_mismatch PASSED [ 93%]
    tests/test_prompts_index.py::PromptsContentValidatorTests::test_rule_prompt_metadata_missing_post_cutover PASSED [100%]

    ============================== 15 passed in 0.40s ==============================
    ```
    Non-vacuity run before E-01 applied showing (b), (c), and (d) (along with (a) and (f)) FAIL against unmodified human block:
    ```
    FAILED tests/test_prompts_index.py::IndexOutcomeWordsAreNotLifecycleStatusesTests::test_f_force_color_renders_generic_outcome_words_and_never_unknown_glyph
    FAILED tests/test_prompts_index.py::RunIndexOutputTests::test_b_second_run_reports_up_to_date
    FAILED tests/test_prompts_index.py::RunIndexOutputTests::test_c_third_run_after_md_only_change_reports_updated
    FAILED tests/test_prompts_index.py::RunIndexOutputTests::test_d_fourth_run_after_json_only_change_reports_updated
    FAILED tests/test_prompts_index.py::RunIndexOutputTests::test_a_first_run_writes_both_indexes
    ========================= 5 failed, 10 passed in 0.56s =========================
    ```
    `git status --short`:
    ```
     M CHANGELOG.md
     M agent_workflows/prompts_index.py
     M tests/test_index_write_agent_records.py
     M tests/test_prompts_index.py
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted `git diff -- tests/test_index_write_agent_records.py` showing the updated prompts strings, the new `HUMAN_MD_ONLY_RUN` / `HUMAN_JSON_ONLY_RUN` expectations, the extended `test_human_invariance_per_verb`, and the refreshed docstring line; plus pasted output of `python3 -m pytest -o addopts="" tests/test_index_write_agent_records.py -v` with every test passing, including all three `test_human_invariance_per_verb` subtests.
  - Observed evidence:
    `git diff -- tests/test_index_write_agent_records.py`:
    ```diff
    diff --git a/tests/test_index_write_agent_records.py b/tests/test_index_write_agent_records.py
    index 7375489c5..277caa774 100644
    --- a/tests/test_index_write_agent_records.py
    +++ b/tests/test_index_write_agent_records.py
    @@ -18,7 +18,7 @@ against isolated fixture repositories (never the live tree), asserting:
       - research fixture with one frontmatter-invalid doc (exit 1, outcome findings,
         findings >= 1, a diagnostic naming that doc's repo-relative location and rule
         frontmatter-invalid, and the index files NOT written).
    -- Human invariance: unflagged stdout on fixture matches legacy expected strings byte-exact.
    +- Human invariance: unflagged stdout on fixture matches legacy expected strings byte-exact (prompts matches shared four-state format, vcqobe).
     - Unsupported type: index specs --agent emits a kind:error record at exit 2.

     In accordance with GUIDING_PRINCIPLES P16, this module performs zero static analysis:
    @@ -48,16 +48,28 @@ VERBS = ("plans", "prompts", "research")

     HUMAN_FIRST_RUN = {
         "plans": "wrote        .aw/records/plans/INDEX.json, INDEX.md (1 plans)\n",
    -    "prompts": "wrote INDEX.json (1 prompts)\nwrote INDEX.md\n",
    +    "prompts": "wrote        .aw/records/prompts/INDEX.json, INDEX.md (1 prompts)\n",
         "research": "wrote        .agents/docs/research/INDEX.json, INDEX.md (1 docs)\n",
     }

     HUMAN_SECOND_RUN = {
         "plans": "up to date   .aw/records/plans/INDEX.json, INDEX.md (1 plans)\n",
    -    "prompts": "wrote INDEX.json (1 prompts)\nwrote INDEX.md\n",
    +    "prompts": "up to date   .aw/records/prompts/INDEX.json, INDEX.md (1 prompts)\n",
         "research": "up to date   .agents/docs/research/INDEX.json, INDEX.md (1 docs)\n",
     }

    +HUMAN_MD_ONLY_RUN = {
    +    "plans": "updated      .aw/records/plans/INDEX.md (INDEX.json up to date; 1 plans)\n",
    +    "prompts": "updated      .aw/records/prompts/INDEX.md (INDEX.json up to date; 1 prompts)\n",
    +    "research": "updated      .agents/docs/research/INDEX.md (INDEX.json up to date; 1 docs)\n",
    +}
    +
    +HUMAN_JSON_ONLY_RUN = {
    +    "plans": "updated      .aw/records/plans/INDEX.json (INDEX.md up to date; 1 plans)\n",
    +    "prompts": "updated      .aw/records/prompts/INDEX.json (INDEX.md up to date; 1 prompts)\n",
    +    "research": "updated      .agents/docs/research/INDEX.json (INDEX.md up to date; 1 docs)\n",
    +}
    +

     def _setup_fixture_for_verb(root: Path, verb: str) -> tuple[Path, str]:
         """Create isolated fixture repo and return (index_dir, rel_dir_posix)."""
    @@ -314,7 +326,7 @@ class IndexWriteSubprocessTests(unittest.TestCase):
                 with self.subTest(verb=verb):
                     verb_dir = self.root / f"human_{verb}"
                     verb_dir.mkdir(parents=True, exist_ok=True)
    -                _setup_fixture_for_verb(verb_dir, verb)
    +                index_dir, _rel_dir = _setup_fixture_for_verb(verb_dir, verb)

                     res1 = run_cli(["index", verb], cwd=verb_dir)
                     self.assertEqual(res1.returncode, 0)
    @@ -324,6 +336,19 @@ class IndexWriteSubprocessTests(unittest.TestCase):
                     self.assertEqual(res2.returncode, 0)
                     self.assertEqual(res2.stdout, HUMAN_SECOND_RUN[verb])

    +                # Third run: append comment to INDEX.md
    +                with open(index_dir / "INDEX.md", "a", encoding="utf-8") as f:
    +                    f.write("\n<!-- comment -->\n")
    +                res3 = run_cli(["index", verb], cwd=verb_dir)
    +                self.assertEqual(res3.returncode, 0)
    +                self.assertEqual(res3.stdout, HUMAN_MD_ONLY_RUN[verb])
    +
    +                # Fourth run: overwrite INDEX.json with "{}\n"
    +                (index_dir / "INDEX.json").write_text("{}\n", encoding="utf-8")
    +                res4 = run_cli(["index", verb], cwd=verb_dir)
    +                self.assertEqual(res4.returncode, 0)
    +                self.assertEqual(res4.stdout, HUMAN_JSON_ONLY_RUN[verb])
    +
         # ----------------------------------------------------------------------------------
         # Unsupported-type regression assertion
         # ----------------------------------------------------------------------------------
    ```
    `python3 -m pytest -o addopts="" tests/test_index_write_agent_records.py -v`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=2976770510
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/whri6h
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 19 items

    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_human_invariance_per_verb PASSED [  5%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_drift_plans_missing_id PASSED [ 10%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_agent_write_research PASSED [ 15%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_agent_write_prompts PASSED [ 21%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_agent_write_plans PASSED [ 26%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_all_write_first_and_second_run PASSED [ 31%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_unsupported_type_specs PASSED [ 36%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_all_write_human_invariance PASSED [ 42%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_all_write_verbose_and_json_paths PASSED [ 47%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_all_write_mixed_outcome_refusal PASSED [ 52%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_json_write_prompts PASSED [ 57%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_json_write_plans PASSED [ 63%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_refusal_research_invalid_frontmatter PASSED [ 68%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_json_write_research PASSED [ 73%]
    tests/test_index_write_agent_records.py::IndexWriteMissingDirTests::test_partial_tree_all_write_refusal PASSED [ 78%]
    tests/test_index_write_agent_records.py::IndexWriteMissingDirTests::test_explicit_dir_inside_project PASSED [ 84%]
    tests/test_index_write_agent_records.py::IndexWriteMissingDirTests::test_inprocess_quiet_true PASSED [ 89%]
    tests/test_index_write_agent_records.py::IndexWriteMissingDirTests::test_bare_repo_agent_refusal_per_verb PASSED [ 94%]
    tests/test_index_write_agent_records.py::IndexWriteMissingDirTests::test_bare_repo_json_and_human_refusal_per_verb PASSED [100%]

    ============================= 19 passed in 22.11s ==============================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted `git diff -- CHANGELOG.md` showing the new `- Fixed:` bullet under `## 2.0.0 (pending)`; pasted output of a check over the added line for `\u2014` / `\u2013` returning no matches; and pasted output of the bare `python3 -m pytest` (with its summary line), `aw ipd lint --phase pre-transition <this plan>` (conforming), and `aw check release-gates` (exit 0).
  - Observed evidence:
    `git diff -- CHANGELOG.md`:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 6cb2458f2..e7eafe182 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -33,6 +33,7 @@ Major storage-layout boundary. The logical model (D126-D129) was superseded by t
     - Fixed: aw index all and aw index all --check now emit a single aggregate aw.agent/v1 result record under --agent and a single valid JSON document under --json, ensuring record exit parity with the process exit code and closing multi-document parsing failures.
     - Fixed: aw index plans, prompts, research, and all now refuse with exit code 2 (cannot-run) and a structured record when the records directory does not exist, instead of crashing with a FileNotFoundError traceback.
     - Fixed: aw index <type> --check --json no longer puts the absolute repository path (repo_root) or the human report text (human_rendered) in data; diagnostic locations stay repo-relative.
    +- Fixed: aw index prompts now reports wrote, up to date, or updated with the repo-relative prompts directory path on its human output instead of printing wrote on every run.
     - Fixed: aw ipd scaffold now accepts --dir and no longer writes a plan into an enclosing project, and project discovery stops at an enclosing git repository that has no agent-workflows install.
     - Fixed: aw rename and aw group now scan README.md files for citation rewrites while still skipping generated INDEX.md and STATUS.md manifests.
     - Fixed: aw pwatch, aw runners, and runner stream headers, statuslines, event prefixes, and run summaries now honor the color_depth pin and 16-color terminal detection, so none removes all ANSI color escapes from those surfaces and 16 uses basic 16-color ANSI codes instead of 256-color sequences.
    ```
    Dash check on added line:
    ```
    Added lines: ['+- Fixed: aw index prompts now reports wrote, up to date, or updated with the repo-relative prompts directory path on its human output instead of printing wrote on every run.']
    Dash check: clean (0 matches)
    ```
    Bare `python3 -m pytest`:
    ```
    707 passed in 35.63s
    ```
    `aw check release-gates`:
    ```
    AW check  release-gates                                                  1699 ms
    ✓ CONFORMS  102 release-gates checked

    Evidence
      backlog  40   specs  19   plans  42   releases  1
      errors  0   warnings  0   info  0
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved whri6h --by-human`); no open questions remain (OQ-01 is resolved from repository evidence). Begin with `aw ipd begin whri6h`, then perform `E-01` to `E-04` in dependency order. Do not mark any `E-*` item `performed` before running its action.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. STOP only for a genuinely unsafe condition: a concurrent edit to a scoped file that cannot be safely combined, or the human block in `prompts_index.run_index` no longer being the unconditional two-line `print` cited in F-01.

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*` `Observed evidence:`; never claim a result you did not run. Run `python3 -m pytest` bare (never `-n0`, never an extra `-q`, never `-p no:randomly`). Scratch fixtures and probe scripts go under the gitignored `.aw/state/` and are never committed.

Commits: commit only the Scope-Paths files you changed through `aw commit whri6h -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: under `aw oc run` / `aw agy run` the RUNNER owns finalize, so do not run it yourself; when executing by hand, after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize whri6h`. Never hand-roll a `git mv`.
