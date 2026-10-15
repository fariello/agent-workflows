# IPD: Report up-to-date and partial-update outcomes in aw index prompts human output

- Date: 2026-10-14
- Kind: child
- Concern: `prompts_index.run_index` compares `new_json` and `new_md` against disk (`json_changed` and `md_changed`) and skips writing unchanged files, and its `--agent`/`--json` branch (`artifact_core.emit_index_write_result`) reports `wrote`, `up to date`, or `updated` accordingly, but its human output branch ignores both flags and unconditionally prints `wrote INDEX.json (N prompts)` and `wrote INDEX.md` on every run (re-measured at review through `tests.conformance_matrix.run_cli(["index", "prompts"], ...)` on the `_setup_fixture_for_verb` fixture: first run, unchanged second run, `INDEX.md`-only edit, and `INDEX.json`-only edit all printed `wrote INDEX.json (1 prompts)\nwrote INDEX.md\n`, while `plans` and `research` printed `wrote`, `up to date`, and the two `updated` lines), unlike `plans_index.run_index` and `research_index.run_index` which render the four `(json_changed, md_changed)` states (`wrote`, `up to date`, and `updated` for `INDEX.md` or `INDEX.json` alone) with the repo-relative directory prefix via `Term.status_256`.
- Scope: Update the human output block of `prompts_index.run_index` in `agent_workflows/prompts_index.py` to render the four `(json_changed, md_changed)` outcome states (`up to date`, `wrote`, and `updated` for `INDEX.md` or `INDEX.json`) with `Term(color=_color)` and the styled repo-relative prompts directory prefix matching `plans_index.run_index` and `research_index.run_index`; add in-process change-detection and ANSI/outcome-word tests in `tests/test_prompts_index.py`; update `HUMAN_FIRST_RUN["prompts"]` and `HUMAN_SECOND_RUN["prompts"]` and add partial-update human subprocess assertions in `tests/test_index_write_agent_records.py`; and record the fix in `CHANGELOG.md`.
- Scope-Paths: agent_workflows/prompts_index.py, tests/test_prompts_index.py, tests/test_index_write_agent_records.py, CHANGELOG.md, .aw/records/plans/pending/20261014-promptidxword-01-whri6h-report-up-to-date-and-partial-update-outcomes-in-aw-index-pr.ipd.md
- Item-Dependencies: none
- Status: reviewed
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

## Workflow history
- 2026-10-15 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. Record: .aw/records/reviews/20261014-promptidxword-01-whri6h-report-up-to-date-and-partial-update-outcomes-in-aw-index-pr.review.md Round 1
- 2026-10-14 to-review (aw set): status set to to-review

- 2026-10-14 draft (Antigravity): created from backlog item `vcqobe`.

## Goal

Make `aw index prompts` (and `aw prompts index`) report the actual write outcome (`wrote`, `up to date`, or `updated` for `INDEX.md` or `INDEX.json` alone) with the repo-relative prompts directory prefix on its human output path, matching `aw index plans`, `aw index research`, and the `--agent`/`--json` summary already emitted by `artifact_core.emit_index_write_result`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Align prompts_index human output with plans_index and research_index

- [ ] E-01 In `agent_workflows/prompts_index.py` (`run_index`), replace the two unconditional `print(f"wrote {INDEX_JSON} ({len(entries)} prompts)")` and `print(f"wrote {INDEX_MD}")` lines inside `if not getattr(args, "quiet", False):` with the four-branch `Term` status line used by `plans_index.run_index` and `research_index.run_index`: resolve `_color` via `select_output(args).color` (falling back to `None if not getattr(args, "no_color", False) else False` on `Exception`), construct `term = Term(color=_color)`, compute `rel_dir` via `prompts_dir.relative_to(repo_root).as_posix()` (falling back to `prompts_dir.as_posix()` on `ValueError`), `dir_prefix = f"{rel_dir}/" if rel_dir and not rel_dir.endswith("/") else rel_dir`, and `dir_styled = term.color256(dir_prefix, 33)`, and emit `term.status_256("up to date", width=12)` with `f"{dir_styled}{INDEX_JSON}, {INDEX_MD} ({len(entries)} prompts)"` when `not json_changed and not md_changed`, `term.status_256("wrote", width=12)` with `f"{dir_styled}{INDEX_JSON}, {INDEX_MD} ({len(entries)} prompts)"` when `json_changed and md_changed`, `term.status_256("updated", width=12)` with `f"{dir_styled}{INDEX_MD} ({INDEX_JSON} up to date; {len(entries)} prompts)"` when `md_changed` alone, and `term.status_256("updated", width=12)` with `f"{dir_styled}{INDEX_JSON} ({INDEX_MD} up to date; {len(entries)} prompts)"` when `json_changed` alone.
  - Depends on: none
    Leave everything above that block unchanged: the `--check` branch, the write logic, the `--agent`/`--json` early return through `_core.emit_index_write_result`, and the preceding `if drift and not getattr(args, "quiet", False):` drift-line loop (drift lines still print before the status line, as in `plans_index`). Add a one-line comment pointing at the `plans_index.run_index` note on why these outcome words stay on `Term.status_256` and are not routed through the lifecycle resolver (plan `9zvl2w` E-01). `select_output` is already imported earlier in `run_index` (`from agent_workflows.result_types import select_output` before `ctx = select_output(args)`), so reuse that import; only `Term` needs importing.
  - Expected outcome: `prompts_index.run_index` emits exactly one line, `wrote`, `up to date`, or `updated`, with the repo-relative prompts directory prefix in human mode according to `(json_changed, md_changed)`, and still returns `0`. `quiet=True` still prints nothing (so the `status_set._auto_index_types` caller, which passes `quiet=True`, is unaffected), and `--agent`, `--json`, and `--check` output is unchanged.
  - Execution state: pending

### Task group 2: In-process and subprocess behavior tests and changelog

- [ ] E-02 In `tests/test_prompts_index.py`, add `RunIndexOutputTests` and `IndexOutcomeWordsAreNotLifecycleStatusesTests` (mirroring the test classes in `tests/test_plans_index.py` and `tests/test_research_index.py`) driving `prompts_index.run_index(argparse.Namespace(dir=str(root), limit=None, check=False, quiet=..., no_color=..., color=False, agent=..., json=...))` in-process with `contextlib.redirect_stdout` against the existing `PromptsIndexTests.setUp` fixture (three indexable prompts plus one ignored `untracked/` file under `.aw/records/prompts/`; reuse it by a shared fixture helper or base class), verifying: (a) first run of `prompts_index.run_index` with `no_color=True` returns `0` and prints `"wrote        .aw/records/prompts/INDEX.json, INDEX.md (3 prompts)\n"`; (b) second run unchanged returns `0` and prints `"up to date   .aw/records/prompts/INDEX.json, INDEX.md (3 prompts)\n"`; (c) third run after appending text to only `INDEX.md` returns `0` and prints `"updated      .aw/records/prompts/INDEX.md (INDEX.json up to date; 3 prompts)\n"`; (d) fourth run after overwriting only `INDEX.json` (for example with `"{}\n"`) returns `0` and prints `"updated      .aw/records/prompts/INDEX.json (INDEX.md up to date; 3 prompts)\n"`; (e) a run with `quiet=True` after modifying a file returns `0`, emits `""`, and still rewrites the file (assert the on-disk content was restored), so quiet suppresses output and not the write; (f) under `FORCE_COLOR=1`, the output contains `\033[1;38;5;46mwrote\033[0m` on a first run and `\033[1;38;5;46mup to date\033[0m` on a second run, and never `?`; and (g) `--agent`, `--json`, `--no-color`, `NO_COLOR=1`, `TERM=dumb`, and piped non-TTY stdout emit zero `\033` escape sequences (mirroring `test_machine_and_suppressed_modes_emit_no_ansi` in `tests/test_plans_index.py`, including popping `FORCE_COLOR` and `NO_COLOR` from the environment per case). No test reads production source (P16). Before relying on the new tests, show they are non-vacuous: run (a)-(d) once against the unmodified `run_index` (before E-01 lands, or with E-01's hunk temporarily absent via an in-process `mock.patch` only; never a source edit left in the tree) and record that (b), (c) and (d) fail.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_prompts_index.py` passes with all new human output, partial-update, `quiet=True`, and color/no-ANSI tests green.
  - Execution state: pending

- [ ] E-03 In `tests/test_index_write_agent_records.py`, update `HUMAN_FIRST_RUN["prompts"]` to `"wrote        .aw/records/prompts/INDEX.json, INDEX.md (1 prompts)\n"` and `HUMAN_SECOND_RUN["prompts"]` to `"up to date   .aw/records/prompts/INDEX.json, INDEX.md (1 prompts)\n"`, and extend `IndexWriteSubprocessTests.test_human_invariance_per_verb` (which drives `tests.conformance_matrix.run_cli(["index", verb], cwd=...)` on the `_setup_fixture_for_verb` fixture) to also verify the third run after appending a comment to `INDEX.md` (`updated      <rel_dir>/INDEX.md (INDEX.json up to date; 1 <noun>)\n`) and the fourth run after overwriting `INDEX.json` with `"{}\n"` (`updated      <rel_dir>/INDEX.json (INDEX.md up to date; 1 <noun>)\n`) across `plans`, `prompts`, and `research`, where `<rel_dir>` is the second value `_setup_fixture_for_verb` returns and `<noun>` is `plans`/`prompts`/`docs`. Add the expected strings as `HUMAN_MD_ONLY_RUN` / `HUMAN_JSON_ONLY_RUN` dicts beside the existing two. Also update the module docstring line "Human invariance: unflagged stdout on fixture matches legacy expected strings byte-exact" to say the prompts strings now match the shared four-state format (`vcqobe`). The plans and research strings were measured at review to already pass the third and fourth runs, so only the prompts row changes behavior.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_index_write_agent_records.py` passes with `prompts` human subprocess output verified across first run (`wrote`), second run (`up to date`), and single-file partial updates (`updated`).
  - Execution state: pending

- [ ] E-04 Add one `- Fixed:` bullet to `CHANGELOG.md` under the current `## 2.0.0 (pending)` heading, beside the existing `- Fixed:` bullets (this CHANGELOG has no `## [Unreleased]` or `### Fixed` headings), recording that `aw index prompts` now reports `wrote`, `up to date`, or `updated` with the repo-relative prompts directory path on its human output instead of printing `wrote` on every run (no em or en dashes). Then run the verification suite: `python3 -m pytest tests/test_prompts_index.py tests/test_index_write_agent_records.py`, the bare full suite `python3 -m pytest`, `aw ipd lint --phase pre-transition <this plan>`, and `aw check release-gates`.
  - Depends on: E-02, E-03
  - Expected outcome: `CHANGELOG.md` documents the fix with zero em/en dashes in the added line; the targeted modules and the bare full suite pass; `aw ipd lint --phase pre-transition` conforms and `aw check release-gates` exits 0. (`aw check all` is NOT a pass bar: it exits 1 at HEAD on repository-wide findings unrelated to this plan, measured at review as 27 errors, so demanding exit 0 would be unsatisfiable.)
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

- [ ] V-01 validates E-01
  - Required evidence: Pasted `git diff -- agent_workflows/prompts_index.py` showing that the only changed region is the final human `if not getattr(args, "quiet", False):` block, which now renders `up to date`, `wrote`, and both `updated` branches through `Term(color=_color)`, `term.status_256(..., width=12)` and `dir_styled = term.color256(dir_prefix, 33)`, with the `--check` branch, write logic, `emit_index_write_result` early return, and drift-line loop untouched. Plus pasted stdout of driving `python3 -m agent_workflows index prompts` four times on a scratch fixture under `.aw/state/` (first run, unchanged rerun, `INDEX.md`-only edit, `INDEX.json`-only edit), showing the four expected lines; the observation is produced by the `run_index` block E-01 writes.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" tests/test_prompts_index.py -v` with every test passing, whose test names show each of E-02's cases (a) to (g) is pinned; plus the pasted non-vacuity run showing (b), (c) and (d) FAIL against the unmodified human block, and `git status --short` showing no stray source edit remains.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted `git diff -- tests/test_index_write_agent_records.py` showing the updated prompts strings, the new `HUMAN_MD_ONLY_RUN` / `HUMAN_JSON_ONLY_RUN` expectations, the extended `test_human_invariance_per_verb`, and the refreshed docstring line; plus pasted output of `python3 -m pytest -o addopts="" tests/test_index_write_agent_records.py -v` with every test passing, including all three `test_human_invariance_per_verb` subtests.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `git diff -- CHANGELOG.md` showing the new `- Fixed:` bullet under `## 2.0.0 (pending)`; pasted output of a check over the added line for `\u2014` / `\u2013` returning no matches; and pasted output of the bare `python3 -m pytest` (with its summary line), `aw ipd lint --phase pre-transition <this plan>` (conforming), and `aw check release-gates` (exit 0).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved whri6h --by-human`); no open questions remain (OQ-01 is resolved from repository evidence). Begin with `aw ipd begin whri6h`, then perform `E-01` to `E-04` in dependency order. Do not mark any `E-*` item `performed` before running its action.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. STOP only for a genuinely unsafe condition: a concurrent edit to a scoped file that cannot be safely combined, or the human block in `prompts_index.run_index` no longer being the unconditional two-line `print` cited in F-01.

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*` `Observed evidence:`; never claim a result you did not run. Run `python3 -m pytest` bare (never `-n0`, never an extra `-q`, never `-p no:randomly`). Scratch fixtures and probe scripts go under the gitignored `.aw/state/` and are never committed.

Commits: commit only the Scope-Paths files you changed through `aw commit whri6h -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: under `aw oc run` / `aw agy run` the RUNNER owns finalize, so do not run it yourself; when executing by hand, after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize whri6h`. Never hand-roll a `git mv`.
