# IPD: ipd lint accepts multiple files and defaults to all pending

- Date: 2026-08-18
- Kind: child
- Concern: `aw ipd lint` accepts at most a SINGLE IPD path today. `run_lint` (ipd_lint.py:761) reads one `args.path` (the positional is `nargs="?"` at cli.py:692), errors with "a FILE is required (or use --all)" when zero are given (ipd_lint.py:802-804), and only the separate `--all` flag (cli.py:703) does a batch (over ONE root via `_iter_plan_files`, ipd_lint.py:744). There is no way to lint a hand-picked set of files in one call, and no ergonomic "lint everything in pending" default. This addresses TODO item #2.
- Scope: `agent_workflows/cli.py` (the `lint` `path` positional) + `agent_workflows/ipd_lint.py` (`run_lint`) ONLY, plus ONE test. IN: change the `path` positional to `nargs="*"` (accept zero-or-more files); in `run_lint`, when zero paths are given AND `--all` is not set, DEFAULT to every `*.ipd.md`/`*.md` (excluding README/INDEX/STATUS) under BOTH pending dirs (`.aw/records/plans/pending/` and legacy `.agents/plans/pending/`) discovered via `record_producers.resolve_record_read_paths("plans")`; when multiple explicit paths are given, lint EACH; aggregate exit codes across all linted files (1 if any ERROR disposition, else 0); keep the existing `--agent` tab-separated per-file output. OUT: no change to `--all`'s existing meaning; no change to per-file lint rules/phases; no recursive tree-wide lint beyond the pending dirs.
- Status: approved
- Approval: 2026-08-18, human ("Approve ALL 21 IPDs now ... Execute everything one at a time using Gemini ... then do it yourself.") after /plan-review (rigorous, opencode Opus 4.8; APPROVE / APPROVE WITH REVISIONS APPLIED).
- Set: awlintmulti
- Order: 1
- Highest E allocated: 04
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: o1ynz3

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from TODO item 2 (ipd lint multi-file + default-all-pending).
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE. Verified run_lint:761, path positional nargs='?' cli.py:692, _iter_plan_files:744, --all error:803; the default-pending helper reuses resolve_record_read_paths('plans') (plans is a valid RecordClass, no resolver crash) and preserves the --all branch. No findings.

## Goal

Let `aw ipd lint` take ONE OR MORE IPD files in a single invocation and, given NO path, default to
linting every plan in BOTH pending directories (`.aw/records/plans/pending/` and legacy
`.agents/plans/pending/`), aggregating the per-file results into one process exit code (1 if any file
is an ERROR disposition, else 0) so a whole batch can be validated in one command.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: edit ONLY `agent_workflows/cli.py` and `agent_workflows/ipd_lint.py`, and add ONE
test file `tests/test_ipd_lint_multi.py`. Do NOT change the `--all` code path (ipd_lint.py:771-799),
`_iter_plan_files` (ipd_lint.py:744), `lint_file`, or any lint rule. Do NOT hardcode either pending
directory: discover them through `record_producers.resolve_record_read_paths("plans")` and append
`"pending"` to each returned base. Preserve the `--agent` tab-separated per-file output format
(`{path}\t{code}\t{message}` per diagnostic, or `{path}\tDISPOSITION\t{disposition}` when a file has
no diagnostics), which is identical to what the `--all` path already prints.

### Task group 1: accept multiple files (or zero)

- [ ] E-01 In `agent_workflows/cli.py`, change the `lint` `path` positional from `nargs="?"` to `nargs="*"` so it accepts zero-or-more files. Replace this exact block (cli.py:692-697):
  ```python
  p_ipd_lint.add_argument(
      "path",
      nargs="?",
      default=None,
      help="IPD file to lint (or a repo root with --all).",
  )
  ```
  with:
  ```python
  p_ipd_lint.add_argument(
      "path",
      nargs="*",
      default=[],
      help="Zero or more IPD files to lint. With no path, lint every plan in both pending dirs; with --all, treat the single value as a repo root.",
  )
  ```
  - Depends on: none
  - Expected outcome: `args.path` is now a LIST (empty when no path is given); `aw ipd lint a.ipd.md b.ipd.md` parses two paths; `aw ipd lint` parses `[]`.
  - Execution state: pending

### Task group 2: run_lint iterates a list and defaults to both pending dirs

- [ ] E-02 In `agent_workflows/ipd_lint.py`, add a helper that enumerates the default pending files across BOTH pending dirs, and refactor `run_lint` (ipd_lint.py:761) so that, when `--all` is NOT set, it lints a LIST of files: the explicit `args.path` list when non-empty, else the default pending set. Do NOT touch the `--all` branch. Add this helper immediately after `_iter_plan_files` (after ipd_lint.py:758):
  ```python
  def _iter_pending_files(root: Path) -> List[Path]:
      # Default target when `aw ipd lint` is given no path and --all is not set:
      # every IPD in BOTH pending dirs (current `.aw/records/plans/pending/` and legacy
      # `.agents/plans/pending/`), resolved via the shared read-path helper (never hardcoded).
      from agent_workflows.record_producers import resolve_record_read_paths

      out: List[Path] = []
      seen = set()
      try:
          bases = resolve_record_read_paths("plans", target_repo=str(root))
      except Exception:
          bases = [root / ".aw" / "records" / "plans"]
      for base in bases:
          pending = base / "pending"
          if not pending.is_dir():
              continue
          for p in sorted(pending.rglob("*.md")):
              if p.name in _NON_IPD_BASENAMES:
                  continue
              key = str(p.resolve())
              if key in seen:
                  continue
              seen.add(key)
              out.append(p)
      return out
  ```
  Then replace the single-target block (ipd_lint.py:801-822), i.e. from `target = getattr(args, "path", None)` through `return 1 if res.disposition == S.DISPOSITION_ERROR else 0`, with a list-driven block:
  ```python
      raw = getattr(args, "path", None)
      if isinstance(raw, (list, tuple)):
          explicit = [str(x) for x in raw]
      elif raw:
          explicit = [str(raw)]
      else:
          explicit = []

      if explicit:
          files = [Path(x) for x in explicit]
          for f in files:
              if not f.is_file():
                  print("error: not a file: {0}".format(f))
                  return 2
      else:
          files = _iter_pending_files(Path(getattr(args, "dir", None) or "."))
          if not files:
              print("error: no pending IPDs found (and no FILE given; use --all for a repo root)")
              return 2

      any_error = False
      for path in files:
          res = lint_file(path, checkpoint=checkpoint, legacy=legacy)
          if res.disposition == S.DISPOSITION_ERROR:
              any_error = True
          if agent:
              for d in res.diagnostics:
                  print(
                      "{0}\t{1}\t{2}".format(path, d.code, d.message.replace("\t", " "))
                  )
              if not res.diagnostics:
                  print("{0}\t{1}\t{2}".format(path, "DISPOSITION", res.disposition))
          else:
              if res.diagnostics:
                  for d in res.diagnostics:
                      print(d.render(str(path)))
              print("disposition: {0}: {1}".format(res.disposition, path))
      return 1 if any_error else 0
  ```
  - Depends on: E-01
  - Expected outcome: `aw ipd lint a.ipd.md b.ipd.md` lints BOTH files in one call; `aw ipd lint` (no path, no `--all`) lints every `*.md` (excluding README/INDEX/STATUS) under both pending dirs; a non-existent explicit path exits 2; the `--all` branch is unchanged.
  - Execution state: pending

### Task group 3: exit-code aggregation across files

- [ ] E-03 Confirm the aggregation semantics land exactly as written in E-02: the loop tracks `any_error` across ALL linted files and the final `return 1 if any_error else 0` yields 1 when ANY file's disposition is `S.DISPOSITION_ERROR` and 0 otherwise, matching the single-file exit convention (`1 if error else 0`, formerly ipd_lint.py:822) and the `--all` convention (ipd_lint.py:799). The `--agent` tab-separated per-file output (one `{path}\t{code}\t{message}` per diagnostic, or `{path}\tDISPOSITION\t{disposition}` when clean) is preserved verbatim inside the loop.
  - Depends on: E-02
  - Expected outcome: a mixed batch of a conforming file and an error file exits 1; an all-conforming batch exits 0; the `--agent` output prints one block per file with the disposition line for clean files.
  - Execution state: pending

### Task group 4: test

- [ ] E-04 Add `tests/test_ipd_lint_multi.py` with a `unittest.TestCase` `IpdLintMultiTests` that, in a tmp repo fixture, writes at least two conforming IPDs under `.aw/records/plans/pending/` (use `aw ipd scaffold`/`aw ipd sync`, or copy a known-conforming plan, then edit the `- Id:`/filename so they differ) plus one deliberately broken IPD (e.g. a missing required heading) and asserts: (a) invoking lint with the two explicit conforming file paths returns exit 0 and prints a per-file block for each (multi-file); (b) invoking lint with NO path (and no `--all`) enumerates the pending files across both dirs - assert the broken file is among the linted set and the exit is 1 (no-path default + aggregation); (c) invoking lint with one conforming AND one broken explicit path returns exit 1 (aggregation: any error -> 1) while a two-conforming batch returns 0. Invoke the CLI in-process (build args via the parser, or call `ipd_lint.run_lint` with a small args stub carrying `path=[...]`, `phase="author"`, `agent=True/False`, `all=False`, `legacy=False`, `dir=<repo>`). Run the FULL serial suite and paste the tail.
  - Depends on: E-01,E-02,E-03
  - Expected outcome: all three assertions pass; the full serial suite is green (no regression in single-file or `--all` behavior).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `run_lint` (ipd_lint.py:761) is the lint entrypoint. It has TWO branches today: the `--all` batch over one root via `_iter_plan_files` (ipd_lint.py:771-799), and a single-target branch that reads one `args.path` and errors when empty (ipd_lint.py:801-822).
- The CLI `lint` positional is `path`, currently `nargs="?"` with `default=None` (cli.py:692-697); `--all` (cli.py:703), `--phase` (cli.py:698), `--legacy` (cli.py:708), `--agent` (cli.py:713) also exist.
- `_iter_plan_files(root)` (ipd_lint.py:744) resolves ONE plans base (`.aw/records/plans` with a legacy `.agents/plans` read-fallback) and globs `*.md` excluding `_NON_IPD_BASENAMES` (`README.md`, `STATUS.md`, `INDEX.md`, ipd_lint.py:741). The new pending default reuses `_NON_IPD_BASENAMES` but must union BOTH pending dirs.
- Dual pending dirs are resolved centrally by `resolve_record_read_paths("plans")` (record_producers.py:597), which returns the plans BASE dirs (primary `.aw/records/plans` + legacy `.agents/plans` when present); the new helper appends `"pending"` to each base. Do NOT hardcode either path.
- The `--agent` output format is `{path}\t{code}\t{message}` per diagnostic, or `{path}\tDISPOSITION\t{disposition}` when a file has no diagnostics (ipd_lint.py:783-791 in the `--all` branch; the new list loop reuses the identical format).
- Exit convention for lint: `1 if any ERROR disposition else 0` (single-file ipd_lint.py:822; `--all` ipd_lint.py:799). The multi-file loop takes the max over files (any error -> 1). Invocation/internal errors (missing file, bad phase) stay exit 2 (ipd_lint.py:766, 804, 807, 826).

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | `run_lint` already batches for `--all` with the exact `--agent` output we need. | The multi-file loop reuses the same per-file print format; no new output shape. |
| F2 | Path positional is `nargs="?"` returning a scalar/None. | Switch to `nargs="*"` (returns a list, `default=[]`); `run_lint` must handle a list, tolerating the old scalar for safety. |
| F3 | `resolve_record_read_paths("plans")` returns plans BASE dirs, not pending subdirs. | The default-discovery helper appends `"pending"` to each base and unions them (de-duped by resolved path). |
| F4 | `_NON_IPD_BASENAMES` already excludes README/STATUS/INDEX. | The pending helper reuses it, so generated index/status files are never linted. |
| F5 | Single-file and `--all` both exit `1 if error else 0`. | The multi-file aggregation is the same rule taken across all files; no new severity mapping is introduced. |

## Proposed changes (ordered, validatable)

1. `path` positional `nargs="?"` -> `nargs="*"` with `default=[]` (E-01). 2. Add `_iter_pending_files` (both pending dirs via `resolve_record_read_paths`) and make `run_lint` iterate a file list, defaulting to the pending set when no explicit path and no `--all` (E-02). 3. Aggregate per-file exit codes to one process exit (`1 if any error else 0`), preserving `--agent` per-file output (E-03). 4. `tests/test_ipd_lint_multi.py` covering multi-file, no-path default, and aggregation + full serial suite (E-04).

## Deferred / out of scope (with reason)

- Recursively linting arbitrary trees (`executed/`, `reusable/`): out of scope; the no-path default is the pending trees only.
- Changing lint rules, phases, or the `--all` semantics: out of scope; this plan only changes file selection and per-file result aggregation.
- Changing the exit-code convention to a 0/1/2 severity ladder for warnings: out of scope; lint's disposition set maps to `1 if error else 0` and the multi-file rule preserves it.

## Scope check

- Over-scope: none - no lint-rule, phase, or `--all` changes; only the positional arity, the list loop, the pending-default helper, and a test.
- Under-scope: none - multi-file, the pending default across BOTH dirs, and exit aggregation are all covered and tested.

## Required tests / validation

`tests/test_ipd_lint_multi.py` (E-04): multiple explicit files linted in one call, the no-path default enumerating both pending dirs (broken file present, exit 1), and exit-code aggregation (conforming+broken -> 1, all-conforming -> 0). Plus the full serial suite to confirm no regression in single-file lint or `--all`.

## Spec / documentation sync

Update the `aw ipd lint` `path` positional help to reflect `nargs="*"` and the no-path pending default (done inline in E-01). No separate spec doc change; the orchestrator (if any) advances any Set-level spec.

## Open questions

### OQ-01: when a listed file path does not exist, should lint fail the whole batch or skip-with-warning?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: FAIL the batch with exit 2 on the first missing EXPLICIT path (per E-02: `if not f.is_file(): return 2`), so typos are surfaced immediately - consistent with the current single-file `error: not a file` (ipd_lint.py:806-808). The no-path pending default simply enumerates whatever exists (never errors on absence, only on an empty pending set). Non-blocking and easily adjusted.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw ipd lint --help` showing the `path` positional now describes zero-or-more files with the no-path pending default (evidence the arity changed), and paste `aw ipd lint a.ipd.md b.ipd.md --agent` printing a per-file block for BOTH files in one call.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `aw ipd lint --agent` (NO path, no `--all`) in a repo showing it enumerates plans from the pending dir(s) - show the file list it covered - and confirm a legacy `.agents/plans/pending/` file is included when present (or note none present in the fixture).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste a mixed batch `aw ipd lint <conforming> <broken> --agent; echo "exit=$?"` showing exit=1, and an all-conforming batch `aw ipd lint <conforming1> <conforming2>; echo "exit=$?"` showing exit=0.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `pytest tests/test_ipd_lint_multi.py -p no:xdist -q` (passing) + the full serial suite tail (no regressions in single-file lint or `--all`).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, with opencode Opus 4.8 owning verification and path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the changed
`agent_workflows/cli.py` + `agent_workflows/ipd_lint.py` + the new `tests/test_ipd_lint_multi.py`
path-scoped (never `git add -A`), never pushes, and the plan moves to `.aw/records/plans/executed/`
only after `aw ipd lint --phase pre-transition` conforms and every V is `pass`.
