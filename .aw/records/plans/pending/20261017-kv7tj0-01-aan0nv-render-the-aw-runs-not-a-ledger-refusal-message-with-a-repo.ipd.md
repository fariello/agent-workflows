# IPD: Render the aw runs not-a-ledger refusal message with a repo-relative path

- Date: 2026-10-17
- Kind: child
- Concern: The shared `aw runs` not-a-ledger refusal (`run_cli._emit_not_a_ledger`, exit 7) builds its message as `f"error: not a run ledger: {exc}"`, and `str(exc)` comes from `run_ledger_store.NotALedgerError.__init__`, which formats `f"{self.path} is not a run ledger file"` with the ABSOLUTE path. So the human line and the machine `error` key both leak the absolute filesystem path (home directory, username), even though plan `lpvcln` already made the machine `path` key repo-relative via `agent_schema.normalize_repo_path`. The two keys of one record disagree, and the `error` key is exactly what the leak-sanitizer exists to keep out of shared output.
- Scope: Change only the CLI-layer rendering in `run_cli._emit_not_a_ledger` so the message is composed from the repo-relative path plus `exc.detail`, in both human and machine modes; leave `NotALedgerError` (store layer, which has no repo root) unchanged. Add behavioral regression tests driving the real CLI.
- Scope-Paths: agent_workflows/run_cli.py, tests/test_runs_machine_output_paths.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: kv7tj0
- Set: kv7tj0
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: aan0nv

## Workflow history
- 2026-10-17 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (review record `.aw/records/reviews/20261017-kv7tj0-01-aan0nv-render-the-aw-runs-not-a-ledger-refusal-message-with-a-repo.review.md`)

- 2026-10-17 draft (opencode): created.
- 2026-10-17 to-review (opencode): authored from backlog kv7tj0; findings measured against source in this lane.

## Goal

Make every `aw runs` not-a-ledger refusal (exit 7) render the offending file as a repo-relative path in its human line and its machine `error` key, so the record agrees with its own `path` key and never carries a home path or username.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: CLI-layer message rendering

- [ ] E-01 In `agent_workflows/run_cli.py` `_emit_not_a_ledger`, compute the repo-relative path ONCE as `rel = agent_schema.normalize_repo_path(exc.path, resolve_verb_repo_root(getattr(args, "dir", None)))`, build the message as `f"error: not a run ledger: {rel} is not a run ledger file"` followed by `f": {exc.detail}"` only when `exc.detail` is non-empty (mirroring the shape `NotALedgerError.__init__` produces, so only the path spelling changes), and use that same `rel` for the existing machine `path` key. Do NOT use `str(exc)` anywhere in this function. Do NOT change `run_ledger_store.NotALedgerError`, its `detail` text, the exit code `EXIT_NOT_A_LEDGER`, the `corrupted: False` / `not_a_ledger: True` keys, or any of the four call sites (`_run_show`, `_run_evidence`, `_run_verify_ledger`, and `_build_engine`, which serves the `aw run` lifecycle verbs such as `_run_start` and `_run_finalize`), which all already funnel through this one emitter. Update the docstring to state that the message is rendered from the repo-relative path because the store-level message carries the absolute path (backlog `kv7tj0`). This item runs AFTER E-02 and E-03 on purpose: those tests are authored and run red against the unmodified `run_cli.py` first, so V-02 and V-03 can paste the failing run.
  - Depends on: E-02, E-03
  - Expected outcome: `_emit_not_a_ledger` no longer interpolates `exc`; the machine `error` value and the human stdout line are the same text (measured at review: `_print_human` prints the lowercase `error:` prefix verbatim), reading `error: not a run ledger: .aw/records/runs/run-feedfeed00/events.jsonl is not a run ledger file: the file is valid JSONL but carries none of the ledger envelope fields ...`, and the `path` key is unchanged in value.
  - Execution state: pending

### Task group 2: Behavioral regression tests

- [ ] E-02 In `tests/test_runs_machine_output_paths.py`, extend the not-a-ledger section (h): parametrize the existing `test_not_a_ledger_machine_path_is_relative` over `--json` and `--agent` (parsing with the file's `_parse_machine(res.stdout, mode)`, which also enforces the one-line `--agent` shape), keep its existing `path` assertions, and add assertions, via the real CLI subprocess against the `tmp_path` repo, that `str(repo.resolve())` does NOT appear in `data["error"]`, that `data["error"]` starts with `error: not a run ledger: ` and contains `data["path"]` verbatim, that the word `corrupt` does not appear in `data["error"]`, and that the exit code is 7. Factor the foreign-file seeding into a small local helper so this test and E-03's share it. Run it against the unmodified `run_cli.py` before E-01 and keep the failing output for V-02.
  - Depends on: none
  - Expected outcome: machine-mode regression tests that fail on the pre-change code (absolute path in `error`, measured at review in both modes) and pass after E-01.
  - Execution state: pending
- [ ] E-03 In the same file, add `test_not_a_ledger_human_line_is_relative`: run `aw runs show <foreign events.jsonl> --dir <repo>` with no machine flag and assert exit 7, that stdout contains `not a run ledger`, that `str(repo.resolve())` is NOT in stdout, that stdout contains the repo-relative `.aw/records/runs/run-feedfeed00/events.jsonl`, and that `corrupt` is not in stdout. Run it against the unmodified `run_cli.py` before E-01 and keep the failing output for V-03.
  - Depends on: none
  - Expected outcome: a human-mode regression test that fails before E-01 and passes after it.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `aw runs` machine output is emitted only through `run_cli._emit_machine` (redaction via `_redact_output`) and human output through `run_cli._print_human`; path normalization for agent-facing output is `agent_schema.normalize_repo_path(path, repo_root)` with the root from `project_context.resolve_verb_repo_root(args.dir)`, the exact pattern `_emit_not_a_ledger` already uses for its `path` key.
- The not-a-ledger wording must never contain the word `corrupt` (comment in `RunLedgerStore._require_ledger_shape`, and `_emit_not_a_ledger` docstring citing `e6b9kt`); existing contract tests in `tests/test_run_recovery_cli.py` grep for the substring `not a run ledger` and `json-eq not_a_ledger True`, both of which this plan preserves.
- Tests in this repository are behavioral (P16): they drive the real CLI via `tests.conformance_matrix.run_cli` and assert on stdout, parsed JSON, and exit codes; no source-reading tests.
- Suite: routine gate is bare `python3 -m pytest`; narrowed runs use an explicit path.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | The absolute path enters through the store exception's message. | `run_ledger_store.NotALedgerError.__init__`: `self.path = Path(path)` then `msg = f"{self.path} is not a run ledger file"`; `RunLedgerStore._require_ledger_shape` raises it with `self._path`, which is the resolved ledger file the CLI passed in. |
| F-02 | The CLI interpolates that message verbatim into both output modes. | `run_cli._emit_not_a_ledger`: `err_msg = f"error: not a run ledger: {exc}"`, used for the machine `"error"` key and for `_print_human(err_msg)`. |
| F-03 | The machine `path` key is already repo-relative, so the record is internally inconsistent. | Same function: `"path": agent_schema.normalize_repo_path(exc.path, resolve_verb_repo_root(getattr(args, "dir", None)))`; covered by `tests/test_runs_machine_output_paths.py::test_not_a_ledger_machine_path_is_relative`, which checks `path` but not `error`. Executed plan `lpvcln` V-07 notes "the `error` message text (from `store.NotALedgerError.__str__`, outside this plan's scope) still embeds the absolute path; reported as a follow-up finding". |
| F-04 | There is ONE emitter, so one change covers every reader. | All four `except store.NotALedgerError as exc:` arms in `run_cli.py` (two `read_records(verify=True)` readers, the `verify_chain(raise_on_error=False)` reader, and `_build_engine`) call `_emit_not_a_ledger(args, exc)`. `run_viewer` catches the exception silently (`unreadable_state`) and prints no message, so it is unaffected. |
| F-05 | The store layer cannot fix this itself. | `RunLedgerStore` is constructed from a path only and has no repo root; normalizing there would require threading a root through every store caller. Rendering at the CLI boundary, where the root is known, is the least disruptive fix. |
| F-06 | Measured at review on a `seed_ledger_fixture` repo: `aw runs show <foreign events.jsonl> --dir <repo>` exits 7 in `--json`, `--agent` and human mode, and every one carries the absolute `/tmp/...` path in the message while `path` is `.aw/records/runs/run-feedfeed00/events.jsonl`; `runs verify-ledger` and `runs evidence` give the same record. Human mode prints the lowercase `error: not a run ledger: ...` line verbatim. | review probe via `tests.conformance_matrix.run_cli` |

## Proposed changes (ordered, validatable)

1. E-02: machine-mode (`--json`, `--agent`) regression tests on the `error` key, run red first.
2. E-03: human-mode regression test on the stdout line, run red first.
3. E-01: re-render the refusal message in `run_cli._emit_not_a_ledger` from the repo-relative path and `exc.detail`; E-02/E-03 then pass.

## Deferred / out of scope (with reason)

- Changing `NotALedgerError.__str__` itself: the store has no repo root (F-05) and other callers may legitimately want the full path in a traceback.
  - Carrier-Declined: store layer has no repo root; callers may legitimately want full path in tracebacks
- Other `aw runs` error messages that may embed paths (for example `LedgerCorruption` text rendered by `_emit_error`): not named by backlog `kv7tj0`; if found during execution, file a new backlog item rather than broadening scope.
  - Carrier-Declined: not named by backlog kv7tj0; out of scope for this focused fix

## Scope check

- Over-scope: none. Two files, one function and its tests.
- Under-scope: none. F-04 shows every not-a-ledger refusal funnels through the one emitter changed in E-01, and E-02/E-03 cover both output modes.

## Required tests / validation

- `python3 -m pytest tests/test_runs_machine_output_paths.py -o addopts="" -q` passes, including the new and extended not-a-ledger tests.
- The new assertions fail on the pre-change code (E-02/E-03 are authored first and run against the unmodified `run_cli.py`, per their dependency order; paste the failure; do not use `git stash`).
- `python3 -m pytest tests/test_run_recovery_cli.py -o addopts="" -q` still passes (the `not a run ledger` substring and `not_a_ledger` contract rows).
- Routine gate `python3 -m pytest` passes.
- `aw sanitize --agent` reports no new finding attributable to these files.

## Spec / documentation sync

N/A: no spec documents the wording of the not-a-ledger message; the exit code, keys, and `not a run ledger` substring are unchanged, so no contract text moves.

## Open questions

### OQ-01: Should the store-level exception message itself become relative?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. The store has no repo root (F-05), and the backlog item asks only that human and machine output stop embedding the absolute path; rendering at the CLI boundary achieves that without touching the store contract.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git diff agent_workflows/run_cli.py` showing `_emit_not_a_ledger` composing the message from `normalize_repo_path(...)` and `exc.detail` with no `{exc}` interpolation, and pasted stdout of `python3 -m agent_workflows runs show <tmp repo>/.aw/records/runs/run-feedfeed00/events.jsonl --dir <tmp repo> --json` (code path: `run_cli` show reader -> `RunLedgerStore.read_records` -> `NotALedgerError` -> `_emit_not_a_ledger`, created by E-01) whose `error` value contains the repo-relative path and no absolute prefix, with exit code 7.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output of the E-02 machine-mode tests FAILING on the unmodified `run_cli.py` (absolute path found in `error`) and the same tests PASSING after E-01, with the `N passed` summary line for `tests/test_runs_machine_output_paths.py`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output of `test_not_a_ledger_human_line_is_relative` failing before E-01 and passing after, plus pasted passing output (`N passed`) of `python3 -m pytest tests/test_run_recovery_cli.py -o addopts="" -q` and of the routine gate `python3 -m pytest` (with `echo "exit=$?"`), and the pasted `aw sanitize --agent` result record showing no finding located in `agent_workflows/run_cli.py` or `tests/test_runs_machine_output_paths.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit aan0nv -- agent_workflows/run_cli.py tests/test_runs_machine_output_paths.py` (never `git add -A`, never push). You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with Result: pass, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
