# IPD: Emit a structured record from aw sanitize's --fix branch and its exit-2 error branches under --agent and --json

- Date: 2026-10-12
- Kind: child
- Concern: `aw sanitize --agent` / `--json` (and the `check-local-leaks` spelling) writes ZERO bytes to stdout on the `--fix` branch and on both exit-2 error branches (not a git repository; `OSError`/`zipfile.BadZipFile`), so a scripted caller using the advertised machine flag gets an empty string and `json.loads` raises. `docs/cli-output-contract.md` Section 11.3 requires a mutation to report `applied`/`changes` (a preview with `next` for `--dry-run`) and Section 11.4 requires a `kind: error` record with `outcome: cannot-run` and `exit: 2`. Authoring also found the interactive `--fix` path writes its `input()` prompt (`Rewrite leak-class paths in <rel>? [y/N]`) to STDOUT, which would corrupt a machine payload even once one is emitted.
- Scope: In `leak_sanitizer.main`, resolve the `OutputContext` (threaded `context` or `select_output(args)`) BEFORE the `--fix` branch and the scan, and route the `--fix` outcome (applied, preview, nothing-to-fix, unfixable) and the three exit-2 handlers through `get_renderer(ctx).emit` with a `CommandResult` when `ctx.is_agent or ctx.is_json`. Under a machine context, `--fix` with neither `--yes` nor `--dry-run` refuses with a `cannot-run` exit-2 record instead of prompting (OQ-01). The HUMAN path (no machine flag) stays byte-identical on stdout, stderr and exit code. Add behavioral coverage driving `cli.main` with separated streams. EXCLUDES any change to the scan ruleset, the rewrite logic in `fix_working_tree`/`_rewrite_line`, the payload content of the already-correct scan branch (owned by `wyy09f`, executed), home-path redaction policy (`9yd6tx`), `cli._run_check_local_leaks` (the context is already threaded by `wyy09f`), and the other forwarded driver leaves.
- Scope-Paths: agent_workflows/leak_sanitizer.py, tests/test_leak_sanitizer_machine_flags.py, CHANGELOG.md
- Item-Dependencies: executed:wyy09f
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: k84fqu
- Blocks-Release: next
- Set: k84fqu
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 0e41gc

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 0e41gc verified (set k84fqu, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed

- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed (review record `.aw/records/reviews/20261012-k84fqu-01-0e41gc-emit-a-structured-record-from-aw-sanitize-s-fix-branch-and-i.review.md`). F-04/F-05 re-measured at review HEAD `04ba026c0` (in-process `cli.main`, stdin at EOF): `--fix --agent` -> rc 0, stdout `'Rewrite leak-class paths in a.md? [y/N] '`; `--fix --dry-run --agent`/`--json` -> rc 0, stdout empty, stderr `would rewrite: a.md`.
- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog item `k84fqu` (inherits `- Blocks-Release: next`, `- Work-Kind: bug`, `- Priority: medium`). The item's prerequisite `wyy09f` is EXECUTED (`.aw/records/plans/executed/20261002-xym8g8-01-wyy09f-...ipd.md`, commit `97c4b5743`), so `leak_sanitizer.main` already accepts a keyword-only `context` and `cli._run_check_local_leaks` already passes it; this plan therefore touches only the engine, not `cli.py`. All three measured defects re-verified at authoring HEAD `9d4d8750735ddb92fd0c25aed766c50d9d8797a1` (F-01..F-03), and authoring found a fourth (F-04, prompt on stdout) that the item's fix shape would otherwise leave behind.

## Goal

Make every exit of `aw sanitize` / `aw check-local-leaks` under `--agent` or `--json` emit exactly one schema-valid record on stdout (a mutation record for `--fix`, an error record for exit 2), while leaving the human output byte-identical, so no machine caller can receive an empty string.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure and write failing tests first

- [x] E-01 RE-MEASURE at execution HEAD (record the sha) the four facts this plan rests on, capturing stdout and stderr SEPARATELY for each: (1) `python3 -m agent_workflows sanitize . --fix --dry-run --agent` exits 0 with zero stdout bytes; (2) `sanitize <tmpdir-not-a-git-repo> --agent` (run with `GIT_CEILING_DIRECTORIES` set to the tmpdir's parent, so an enclosing repo cannot satisfy git discovery) and `--json` each exit 2 with zero stdout bytes and `check-local-leaks: not a git repository or git unavailable` on stderr; (3) `sanitize . --wheel <missing-path> --agent` exits 2 with zero stdout bytes and the `OSError` text on stderr; (4) in a scratch repo with a planted home path, `sanitize <repo> --fix --agent` with stdin at EOF writes the `[y/N]` prompt to stdout. Also confirm `leak_sanitizer.main` still has the keyword-only `context` parameter and `cli._run_check_local_leaks` still passes `context=context` (the `wyy09f` precondition). IF the `context` threading is gone, STOP and report: this plan assumes it.
  - Depends on: none
  - Expected outcome: recorded HEAD sha and each fact marked CONFIRMED or CORRECTED with byte counts, exit codes, and stderr text, plus the precondition check result.
  - Execution state: performed

- [x] E-02 EXTEND `tests/test_leak_sanitizer_machine_flags.py` (reuse its `_init_repo`, `_commit`, `_capture_cli_separate` helpers and its `XDG_CONFIG_HOME` pin; synthesize leak tokens at runtime as the file already does) with a `--fix` test table driving `cli.main` in-process over scratch repos, on BOTH spellings (`check-local-leaks`, `sanitize`) and under `--agent`: (a) `--fix --dry-run` on a planted home path: exactly one stdout line, `json.loads` succeeds, `outcome == "preview"`, `applied is False`, `exit == 0`, `changes` lists the planted file, `next` is a non-null string containing `--yes`, and the file bytes are UNCHANGED on disk; (b) `--fix --yes` on the same: `applied is True`, `exit == 0`, `changes` lists the file, and the file on disk no longer contains the planted user segment; (c) `--fix --yes` on a clean tree: `exit == 0`, `outcome == "clean"`, no `changes`; (d) `--fix --yes` on a private-repo identity token (built from `leak_sanitizer._R1`, the pattern `tests/test_leak_sanitizer.py` uses): `exit == 1`, `outcome == "findings"`, `findings >= 1`, some `diagnostics[*].rule == "private-repo"`, file bytes unchanged; (e) `--fix` with neither `--yes` nor `--dry-run`: `exit == 2`, `kind == "error"`, `outcome == "cannot-run"`, stdout contains NO `[y/N]` text, and the file is unchanged. Add one `--json` row for (a) asserting the `CommandResult.to_dict` key names (`status == "preview"`, `exit_code == 0`, non-empty `changes`). Add HUMAN-path controls (no machine flag) on a fresh planted repo for `--fix --dry-run` (stdout empty, stderr exactly `would rewrite: <rel>\n`, exit 0, file unchanged), `--fix --yes` (stdout empty, stderr exactly `rewrote: <rel>\n`, exit 0), and `--fix --yes` on a clean tree (stderr exactly `No auto-fixable local leaks found.\n`), so the byte-identical human `--fix` contract is pinned by behavior and not only asserted in prose; these controls are expected to PASS at baseline. In every row assert stderr carries no JSON payload AND carries none of the human `--fix` prose (`would rewrite:`, `rewrote:`, `Needs manual edit`, `No auto-fixable local leaks found.`), since `docs/cli-output-contract.md` Section 7 forbids duplicating a diagnostic across both streams and the already-correct scan branch prints no prose under a machine context. The in-process run relies on pytest's non-readable stdin: at baseline row (e) reaches `_prompt_stdin`, whose `input()` raises `EOFError` (caught, returns False), so the baseline run cannot hang (measured at review: `input()` under pytest capture raised `EOFError` after writing the prompt to the redirected stdout). RUN at the unfixed baseline and record the verbatim failures.
  - Depends on: E-01
  - Expected outcome: new `--fix` coverage that fails at baseline with recorded messages, asserting outcomes and on-disk side effects (not code structure).
  - Execution state: performed

- [x] E-03 EXTEND the same file with exit-2 error coverage: for a directory outside any git repo (a fresh `tempfile` dir, no `git init`, with `GIT_CEILING_DIRECTORIES` set to that dir's parent for the test, saved and restored like the existing `XDG_CONFIG_HOME` pin, following `tests/test_release_readiness.py`'s `monkeypatch.setenv("GIT_CEILING_DIRECTORIES", ...)`, so git discovery cannot climb into an enclosing repository when `TMPDIR` lives inside one), under `--agent` on both spellings, for the plain scan AND for `--fix --yes` (the `--yes` is required: bare `--fix` under a machine context hits E-05's OQ-01 refusal before `fix_working_tree` runs, so it would never reach the fix branch's `CalledProcessError` handler), assert exit 2, exactly one stdout record, `kind == "error"`, `outcome == "cannot-run"`, `exit == 2`, `verified is False`, `complete is False`, `next == "aw sanitize --help"` (which distinguishes this handler from the OQ-01 refusal, whose `next` is the `--dry-run` command), and stderr is EMPTY; under `--json` assert `exit_code == 2`, `status == "cannot-run"`, and `summary` contains `not a git repository`. For the `OSError` branch, pass `--wheel <path-that-does-not-exist>` against a valid scratch repo and assert the same `--agent` error shape. Add a HUMAN-path control for each branch (no machine flag): stdout is EMPTY, stderr equals the exact pre-change prose (`check-local-leaks: not a git repository or git unavailable\n`, and the `check-local-leaks: <exc>` line), and exit is 2, so the byte-identical human contract is pinned by behavior. RUN at baseline and record the failures (the human controls are expected to PASS at baseline; say so).
  - Depends on: E-02
  - Expected outcome: exit-2 coverage failing at baseline for the machine rows and passing for the human controls, with both recorded.
  - Execution state: performed

### Task group 2: Implement

- [x] E-04 IN `leak_sanitizer.main`, move the `get_renderer`/`CommandResult`/`select_output` imports and `ctx = context or select_output(args)` ABOVE the `if args.fix:` branch, and add a small local helper (for example `_emit_error(ctx, summary) -> int`) that, when `ctx.is_agent or ctx.is_json`, emits `CommandResult(command="check-local-leaks", status="cannot-run", exit_code=2, summary=..., verified=False, complete=False, next_actions=[NextAction(command="aw sanitize --help")])` and returns 2; use it in the `--fix` branch's `CalledProcessError` handler and in both scan-branch handlers (`CalledProcessError`, `(OSError, zipfile.BadZipFile)`). The summary for the `OSError` case is `str(exc)`; the record's existing home-path redaction (`redact_home_paths` in `to_dict`/`to_agent_record`) handles any path in it, so do not add bespoke redaction. Under a machine context the helper prints NOTHING to stderr (the record is the single diagnostic, per `docs/cli-output-contract.md` Section 7). In the human context, keep the existing `print(..., file=sys.stderr); return 2` lines exactly as they are.
  - Depends on: E-03
  - Expected outcome: the E-03 machine rows pass; the human controls still pass; `ls.main(argv)` with no context still works (exercised by `tests/test_leak_sanitizer.py`).
  - Execution state: performed

- [x] E-05 IN the same function's `if args.fix:` branch, under a machine context: (i) if neither `args.assume_yes` nor `args.dry_run`, emit the OQ-01 refusal (`status="cannot-run"`, `exit_code=2`, summary naming `--yes` and `--dry-run`, `next` = `aw sanitize <dir> --fix --dry-run`) BEFORE calling `fix_working_tree`, so no prompt is issued and nothing is written; (ii) otherwise call `fix_working_tree` as today and emit a `CommandResult` with `changes=[Change(path=rel, kind="modify", applied=not args.dry_run) ...]`, `diagnostics` for each unfixable finding (same `Diagnostic` shape the scan branch builds), `exit_code = 1 if unfixable else 0`, `status = "findings"` if unfixable, else `"preview"` for dry run with changes, else `"ok"` with `applied=True` when changes were written, else `"clean"`; set `applied=False` for preview and add `next_actions=[NextAction(command="aw sanitize <dir> --fix --yes")]` for a preview. Use the user-supplied `args.dir` (default `.`) in `next`, passed through `shlex.quote`, not the resolved absolute path. Under a machine context print NONE of the human `--fix` prose to stderr (the record carries it); keep the human `--fix` prose and exit codes byte-identical when no machine flag is set (the E-02 human controls are the guard). Add a comment naming backlog `k84fqu` and stating that a machine caller must never be prompted because `input()` writes to stdout.
  - Depends on: E-04
  - Expected outcome: every E-02 row passes; human `--fix` behavior unchanged; each emitted record passes `agent_schema.assert_valid_agent_record` (enforced inside `to_agent_record`, so a schema-invalid record would surface as an exit-2 substitution and fail the tests).
  - Execution state: performed

- [x] E-06 PROVE sensitivity and completeness, then record the user-facing fix: (1) re-run the four E-01 commands and paste that each now emits exactly one parseable record on stdout (fact 4 now refuses with exit 2 and no prompt text); (2) MUTATION: with a restoring wrapper (`try`/`finally` rewriting the original bytes), revert `leak_sanitizer.py` to its pre-E-04 bytes, confirm the new tests FAIL, restore, and confirm the `sha256` of the file equals the post-E-05 hash; (3) add one `- Fixed:` line to the top `## 2.0.0 (pending)` section of `CHANGELOG.md` describing that `aw sanitize --agent`/`--json` now emit a record for `--fix` and for cannot-run errors and no longer prompt a machine caller (no em or en dashes; user-facing prose); (4) run the full fast suite BARE as `python3 -m pytest` and paste the summary line; for any failure, re-run that selection at the base commit and report whether it is pre-existing.
  - Depends on: E-05
  - Expected outcome: pasted end-to-end evidence, mutation fail/restore with matching hashes, the CHANGELOG line, and a bare-suite `N passed` summary with any failure attributed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `wyy09f` (executed) established the context-threading seam: `leak_sanitizer.main(argv, *, context=None)` with `ctx = context or select_output(args)`, and `cli._run_check_local_leaks(args, term, context)` passing `context=context`. This plan reuses that seam and must not reintroduce argv forwarding of machine flags.
- `tests/test_leak_sanitizer_machine_flags.py` (from `wyy09f`) already provides separated-stream capture via `cli.main` in-process, `XDG_CONFIG_HOME` pinning, and runtime leak synthesis; extending it is the local convention. `tests/test_local_leaks.py`'s combined-stream helper must NOT be used (it is what hid the original defect).
- `CommandResult.to_agent_record` maps `exit_code == 2` or `status in ("error","cannot-run")` to `kind: "error"`, `verified: False`, `complete: False`, and runs `agent_schema.assert_valid_agent_record`; `exit 2` requires outcome `cannot-run` or `error`, and preview is exempt from the complete/positive greenwash rule when `applied is False`. These are the invariants the emitted records must satisfy.
- Non-interactive mutation refusal precedent: `artifact_adopt` returns `_emit("cannot-run", 2, "... pass --yes to attest ...")` rather than prompting when no human can answer, and `cli.py` carries "Non-interactive without --yes: refuse to change things silently." OQ-01 follows this.
- `GUIDING_PRINCIPLES.md` P16: every assertion invokes `cli.main` and inspects real stdout/stderr/exit/file bytes; no source inspection.
- Run the suite bare: `python3 -m pytest` (`pyproject.toml` `addopts` supplies `-q -n auto --dist=worksteal`).

## Findings

| # | Finding | Evidence (authoring HEAD `9d4d8750735d`) |
|---|---|---|
| F-01 | `--fix --dry-run --agent` emits nothing on stdout | `python3 -m agent_workflows sanitize . --fix --dry-run --agent`: exit 0, `stdout bytes: 0`, stderr `No auto-fixable local leaks found.` |
| F-02 | Not-a-git-repo exit 2 emits nothing under `--agent` and `--json` | `sanitize <tmpdir> --agent` -> `2 0 check-local-leaks: not a git repository or git unavailable`; same for `--json` |
| F-03 | `OSError` exit 2 emits nothing | `sanitize . --wheel <tmp>/nope.whl --agent` -> `2 0 check-local-leaks: [Errno 2] No such file or directory: ...` |
| F-04 | Interactive `--fix` writes its prompt to stdout under `--agent` | scratch repo with planted home path, `sanitize <repo> --fix --agent`, stdin DEVNULL -> exit 0, stdout `'Rewrite leak-class paths in a.md? [y/N] '`, stderr `No auto-fixable local leaks found.` (`_prompt_stdin` uses `input()`) |
| F-05 | `--fix --yes` and `--fix --dry-run` on a planted leak also emit nothing | same scratch repo: `['--dry-run'] 0 '' 'would rewrite: a.md'`; `['--yes'] 0 '' 'rewrote: a.md'` |
| F-06 | Root cause | in `leak_sanitizer.main`, the `if args.fix:` branch and the `except subprocess.CalledProcessError` / `except (OSError, zipfile.BadZipFile)` handlers `return` before `ctx = context or select_output(args)` is evaluated |
| F-07 | Prerequisite satisfied | `wyy09f` is in `plans/executed/`; `cli._run_check_local_leaks` ends `return leak_sanitizer.main(passthrough, context=context)` |

## Proposed changes (ordered, validatable)

1. E-01 re-measure (F-01..F-05, F-07).
2. E-02/E-03 failing behavioral tests first.
3. E-04 hoist context resolution and emit error records on the three exit-2 handlers.
4. E-05 emit mutation records on `--fix`, refuse un-attested machine `--fix`.
5. E-06 end-to-end proof, mutation sensitivity, CHANGELOG, bare suite.

## Deferred / out of scope (with reason)

- Rewrite semantics of `fix_working_tree` / `_rewrite_line`: correct today and covered by `tests/test_leak_sanitizer.py`'s FIXES table; this plan changes only reporting.
  - Carrier-Declined: not a defect; the rewrite behavior is correct and already tested, so nothing is owed.
- Moving `_prompt_stdin`'s prompt to stderr for the HUMAN path: a human-visible behavior change outside the item; under machine mode the prompt is never reached after E-05, which is what the item needs.
  - Carrier-Declined: in human mode the prompt on stdout is the intended interactive UX, not a defect; no work is owed.
- `cli.py`: no change needed; the context is already threaded (F-07).
  - Carrier-Declined: no work exists; `wyy09f` already delivered the threading.
- Home-path redaction policy in payloads: decided by `9yd6tx` (executed); this plan reuses the existing redaction in `CommandResult` serialization.
  - Carrier-Declined: already delivered by executed plan `9yd6tx`; nothing outstanding.

## Scope check

- Over-scope: none. CHANGELOG is the user-facing record of a release-gating bug fix.
- Under-scope: F-04 is included because emitting a record while the prompt still writes to stdout would leave the payload unparseable, so the item's acceptance (a parseable record) cannot be met without it.

## Required tests / validation

- `tests/test_leak_sanitizer_machine_flags.py` new `--fix` rows (E-02) and exit-2 rows with human controls (E-03), failing at baseline and passing after E-04/E-05.
- Existing `tests/test_leak_sanitizer.py`, `tests/test_local_leaks.py`, `tests/test_json_surface_leak_posture.py`, `tests/test_flag_surface_uniformity.py` pass unchanged.
- Mutation sensitivity and end-to-end CLI re-measurement (E-06).
- Bare `python3 -m pytest` summary pasted (E-06).

## Spec / documentation sync

- `docs/cli-output-contract.md` Sections 11.3 and 11.4 already state the required behavior; this plan brings the command into conformance, so no doc edit. No `.spec.md` governs this command's output; none is touched.
- `CHANGELOG.md`: one `- Fixed:` line (E-06).

## Open questions

### OQ-01: Under `--agent`/`--json`, what should `--fix` do with neither `--yes` nor `--dry-run`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Refuse with a `cannot-run` exit-2 record naming `--yes` and `--dry-run`, writing nothing and issuing no prompt. Evidence: the interactive path calls `input()`, which writes the prompt to stdout (F-04) and so cannot coexist with a single-record stdout; the repository precedent for an un-attested non-interactive mutation is refusal (`artifact_adopt`'s `--allow-leaks` without a TTY returns `cannot-run`/2 with "pass --yes to attest"; `cli.py` "Non-interactive without --yes: refuse to change things silently."). Silently declining every file (today's EOF behavior) would report `clean` for a tree that still has fixable leaks, a greenwash. The choice is reversible and confined to machine mode; the human path is unchanged.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted execution-HEAD sha and, for each of the four commands, the exit code, stdout byte count, and stderr text (stdout and stderr captured separately), plus the pasted `context=context` call line from `cli._run_check_local_leaks`. Observation produced by E-01's own CLI invocations.
  - Observed evidence: execution-HEAD sha `9dfc35de4d341e293f30f30010907e648e1ff203`.
    Fact 1: exit=0, stdout_bytes=0, stdout=b'', stderr='No auto-fixable local leaks found.\n' [CONFIRMED]
    Fact 2 (agent): exit=2, stdout_bytes=0, stdout=b'', stderr='check-local-leaks: not a git repository or git unavailable\n' [CONFIRMED]
    Fact 2 (json): exit=2, stdout_bytes=0, stdout=b'', stderr='check-local-leaks: not a git repository or git unavailable\n' [CONFIRMED]
    Fact 3: exit=2, stdout_bytes=0, stdout=b'', stderr="check-local-leaks: [Errno 2] No such file or directory: '/tmp/nonexistent_wheel_test_path.whl'\n" [CONFIRMED]
    Fact 4: exit=0, stdout_bytes=41, stdout=b'Rewrite leak-class paths in f.txt? [y/N] ', stderr='No auto-fixable local leaks found.\n' [CONFIRMED]
    Precondition check in `agent_workflows/cli.py` line 11110: `return leak_sanitizer.main(passthrough, context=context)` and `leak_sanitizer.main(argv: Optional[list[str]] = None, *, context: Optional[OutputContext] = None) -> int:` [CONFIRMED].
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the diff of the new `--fix` rows in `tests/test_leak_sanitizer_machine_flags.py` and the verbatim pytest failure output for those rows at the unfixed baseline (`python3 -m pytest -o addopts="" -q tests/test_leak_sanitizer_machine_flags.py` or equivalent narrowed run), showing the machine rows failing because of empty stdout / prompt text (not test errors or a hang), and the human `--fix` control rows PASSING at baseline.
  - Observed evidence: diff adds `test_fix_machine_flags_and_human_controls` covering (a)-(e) on both spellings under `--agent`, `--json`, and human controls.
    Baseline run verbatim failure:
    `FAILED tests/test_leak_sanitizer_machine_flags.py::LeakSanitizerMachineFlagsTests::test_fix_machine_flags_and_human_controls`
    `E AssertionError: 0 != 1`
    `tests/test_leak_sanitizer_machine_flags.py:251: AssertionError`
    `1 failed in 18.86s`
    Human control validation: `All 3 human --fix controls PASS at baseline`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the diff of the exit-2 rows and human controls, and the verbatim baseline run showing the machine rows FAIL and the human-control rows PASS.
  - Observed evidence: diff adds `test_exit_2_error_coverage_and_human_controls` covering non-git tree under `--agent` (plain and `--fix --yes`) and `--json`, `--wheel` missing path under `--agent`, and human controls.
    Baseline run verbatim failure:
    `FAILED tests/test_leak_sanitizer_machine_flags.py::LeakSanitizerMachineFlagsTests::test_exit_2_error_coverage_and_human_controls`
    `E AssertionError: 0 != 1`
    `tests/test_leak_sanitizer_machine_flags.py:445: AssertionError`
    `1 failed in 19.73s`
    Human control validation: `All 3 human exit-2 controls PASS at baseline`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the `leak_sanitizer.py` diff for the hoisted context and error helper, and a pasted narrowed pytest run where every E-03 row passes, plus `tests/test_leak_sanitizer.py` passing (proving the no-context argv path is intact).
  - Observed evidence: diff in `leak_sanitizer.py` hoists imports and context resolution, introduces `_emit_error(ctx, summary)` routing exit-2 errors through `get_renderer(ctx).emit` with `status="cannot-run"` and `exit_code=2` under machine context while preserving human stderr and exit codes.
    Narrowed test run: `tests/test_leak_sanitizer_machine_flags.py` passed (`4 passed in 23.93s`).
    `tests/test_leak_sanitizer.py` passed: `16 passed in 31.06s` (under `-m "slow or not slow"`).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the `--fix` branch diff, and a pasted narrowed pytest run where every E-02 row passes (including the on-disk unchanged/changed assertions, the no-`[y/N]` refusal row, the no-human-prose-on-stderr assertions, and the human `--fix` controls still passing), plus a pasted human-mode `sanitize <scratch> --fix --dry-run` stderr showing the unchanged `would rewrite: <rel>` line.
  - Observed evidence: diff in `leak_sanitizer.py` adds OQ-01 refusal under machine mode when neither `--yes` nor `--dry-run` is passed, and routes `--fix` results via `CommandResult` (`changes`, `diagnostics`, `status`, `applied`, `next_actions`).
    Narrowed test run: `tests/test_leak_sanitizer_machine_flags.py` passes all 4 tests (`4 passed in 23.93s`).
    Human-mode stderr verification:
    `EXIT: 0`
    `STDOUT: ''`
    `STDERR: 'would rewrite: leak.txt\n'`
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: pasted stdout (one JSON record each) and exit codes for the four re-run E-01 commands; pasted mutation output showing the tests FAIL under the reverted file and the before/after `sha256` values matching after restore; the CHANGELOG diff line; and the bare `python3 -m pytest` summary line (`N passed`), with any failure's base-commit comparison. Observations produced by E-06's own invocations.
  - Observed evidence:
    Re-run E-01 commands:
    Fact 1: `exit=0, stdout_lines=1, stderr=''` -> `stdout record: {'schema': 'aw.agent/v1', 'kind': 'result', 'cmd': 'check-local-leaks', 'outcome': 'clean', 'exit': 0, 'verified': True, 'complete': True, 'findings': 0, 'next': None}`
    Fact 2 (agent): `exit=2, stdout_lines=1, stderr=''` -> `stdout record: {'schema': 'aw.agent/v1', 'kind': 'error', 'cmd': 'check-local-leaks', 'outcome': 'cannot-run', 'exit': 2, 'verified': False, 'complete': False, 'findings': 0, 'next': 'aw sanitize --help'}`
    Fact 2 (json): `exit=2, stdout_lines=18, stderr=''` -> `stdout record: {'schema': 'aw.agent/v1', 'command': 'check-local-leaks', 'status': 'cannot-run', 'exit_code': 2, 'summary': 'not a git repository or git unavailable', 'verified': False, 'complete': False, 'diagnostics': [], 'changes': [], 'evidence': [], 'next_actions': [{'command': 'aw sanitize --help'}], 'data': {}}`
    Fact 3: `exit=2, stdout_lines=1, stderr=''` -> `stdout record: {'schema': 'aw.agent/v1', 'kind': 'error', 'cmd': 'check-local-leaks', 'outcome': 'cannot-run', 'exit': 2, 'verified': False, 'complete': False, 'findings': 0, 'next': 'aw sanitize --help'}`
    Fact 4: `exit=2, stdout_lines=1, stderr=''` -> `stdout record: {'schema': 'aw.agent/v1', 'kind': 'error', 'cmd': 'check-local-leaks', 'outcome': 'cannot-run', 'exit': 2, 'verified': False, 'complete': False, 'findings': 0, 'next': 'aw sanitize /tmp/.../repo --fix --dry-run'}`
    Mutation sensitivity test:
    Pre-E-04 hash: `70707fba91c63ba44ba05a43d5228c89e6c00fea90207e27c5f57c6c44e47fc7`
    Post-E-05 hash: `5e16fa4bbf9022da9a9ad7603295d036b42993b992c11d6b5bcbe89a0f74eb05`
    Mutation failure: exit code 1; `FAILED tests/test_leak_sanitizer_machine_flags.py::LeakSanitizerMachineFlagsTests::test_exit_2_error_coverage_and_human_controls`, `FAILED tests/test_leak_sanitizer_machine_flags.py::LeakSanitizerMachineFlagsTests::test_fix_machine_flags_and_human_controls` (2 failed in 17.10s).
    Restored hash: `5e16fa4bbf9022da9a9ad7603295d036b42993b992c11d6b5bcbe89a0f74eb05` (matches post-E-05).
    CHANGELOG diff line: `- Fixed: aw sanitize and aw check-local-leaks under --agent and --json now emit structured records on stdout for the --fix branch and for cannot-run errors, and refuse un-attested machine --fix calls with an error record instead of prompting on stdout.`
    Bare pytest summary: `7458 passed, 2 skipped, 3 warnings in 964.97s (0:16:04)`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. OQ-01 is resolved from repository evidence and is non-blocking.

The executing agent must commit ONLY the three declared `Scope-Paths` through `aw commit <plan> -- <paths>`, never `git add -A` and never `--no-verify`; paste actual runner output for every test claim; and run the full suite bare as `python3 -m pytest`. Do NOT edit `cli.py`: if E-01 finds the `wyy09f` context threading absent, stop and report rather than re-threading it here. Keep the human-mode stdout, stderr, and exit codes byte-identical on every branch; the E-02 and E-03 human controls are the guard. `- Scope-Paths:` is a declaration, not a stop condition: an out-of-scope edit the work genuinely needs is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. Begin execution with `aw ipd begin`, and before every commit verify the staged set with `git diff --cached --name-only`. Do not claim done while any `V-*` is pending: every `V-*` carries pasted observed evidence, and `aw ipd lint --phase pre-transition` must report conforming before the plan moves to `.aw/records/plans/executed/`. Under `aw oc run`/`aw agy run` the runner owns that finalize; executed by hand, the executor runs `aw ipd finalize`. Never `git mv` this plan by hand. The inherited `- Blocks-Release: next` gate travels with this plan; backlog `k84fqu` (currently `graduated`) closes `done` through the normal handoff once this plan is executed.
