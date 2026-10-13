# IPD: Redact run_cli human-mode output so it matches the machine surface

- Date: 2026-10-12
- Kind: child
- Concern: `agent_workflows/run_cli.py` module docstring Contract block states "Redacts sensitive values in both human and machine outputs", but redaction is wired ONLY into `run_cli._emit_machine` (via `run_cli._redact_output`). Every human-mode `print(` in the module, including `run_cli._emit_error`'s `print(f"error: {message}")`, writes unredacted text, so a credential embedded in a target path or in ledger content is masked under `--agent` and printed verbatim in the human stream a person copies into bug reports and transcripts (backlog `94op6l`).
- Scope: Route every human-mode stdout write in `agent_workflows/run_cli.py` through one redacting helper that applies the same `run_cli._redact_output` the machine path uses, add behavioral tests that drive the real CLI and prove a token is absent from human output on every leaf and for ledger-content secrets, and record the fix in the CHANGELOG. The docstring bullet is KEPT (it becomes true); the redaction pattern set itself is not widened.
- Scope-Paths: agent_workflows/run_cli.py, tests/test_run_cli_human_redaction.py, CHANGELOG.md, .aw/records/plans/pending/20261012-runclileak-01-omst3h-redact-run-cli-human-mode-output-so-it-matches-the-machine-s.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: security
- Priority: medium
- From-Backlog: 94op6l
- Blocks-Release: next
- Set: runclileak
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: omst3h
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006
- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog 94op6l; leak re-measured at authoring HEAD on all seven read leaves.

## Goal

Make the human-mode output of `aw runs` / `aw run` apply the same secret redaction the `--agent`/`--json` surfaces already apply, so the docstring's stated safety property holds on the surface humans actually read and paste. Done means a token embedded in a target or in ledger content never appears verbatim in human stdout of any run-family leaf.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: single redacting human-output choke point

- [x] E-01 Add a module-private helper in `agent_workflows/run_cli.py` (suggested name `_print_human(*values, sep=" ", end="\n")`) that joins its values exactly as `print` would, passes the resulting string through `run_cli._redact_output`, and prints the result; then replace EVERY human-mode `print(` call in the module (the usage line in `run_cli.run_cli`, `_run_decisions`, `_run_questions`, `_emit_not_a_ledger`, the inline error prints in `_run_show`/`_run_evidence`/`_run_verify_ledger`/`_run_resume`/`_run_finalize`, `_emit_error`'s human branch, and every report line in show/evidence/verify-ledger/start/next/record/resume/cancel/status/finalize) with it. `_emit_machine` keeps calling `print` on already-redacted JSON. Keep the "Redacts sensitive values in both human and machine outputs" docstring bullet, and add one sentence beside it naming `_print_human` as the human choke point.
  - Depends on: none
  - Expected outcome: `grep -n "print(" agent_workflows/run_cli.py` shows `print(` only inside `_print_human` and `_emit_machine`; behavior otherwise unchanged (same text, same exit codes) for inputs carrying no secret.
  - Execution state: performed

### Task group 2: behavioral regression tests

- [x] E-02 Create `tests/test_run_cli_human_redaction.py` that, via `subprocess.run([sys.executable, "-m", "agent_workflows", ...])`, drives each read leaf `runs show|status|next|resume|evidence|verify-ledger` with a missing target `<tmp_path>/ghp_<24 chars>` in HUMAN mode and asserts the literal token is absent from stdout+stderr and `[REDACTED]` is present, with the exit code unchanged from the `--agent` run of the same call (both 2, `run_cli.EXIT_INVALID_INVOCATION`). Also drive `runs decisions <token-run-id>` and `runs questions <token-run-id>` (whose "no ... projection found" line echoes the path) in BOTH human and `--agent` mode and assert the token is absent in both: these two leaves have no machine branch and print the same raw line under `--agent`, so they leak on the machine surface too (F-6). Also drive the four writer leaves `run start|record|cancel|finalize <token-path>` in human mode: each reaches the absent-ledger refusal with no extra arguments (exit 2, F-6), so they are REQUIRED cases, not optional. Every case asserts the exit code equals the pre-fix value (2) so the fix changes text only.
  - Depends on: E-01
  - Expected outcome: test file exists; every parametrized case passes against the E-01 code and FAILS against the pre-E-01 code.
  - Execution state: performed

- [x] E-03 In the same test file, build a real ledger with `run_ledger_store.RunLedgerStore.append` (a `run` record plus a `tool_event` whose `argv` contains `"Authorization: Bearer ghp_<24 chars>"`, fields per `run_ledger_schema._KIND_FIELDS["tool_event"]`; every record also carries the common fields `schema_version: 1`, `run_id` matching `run-<hex>`, a known actor role such as `runtime`, and `parent: ""`, and `stdout_sha256` is a bare 64-hex digest, the shape `tests/test_run_cli_declarations.py` `_create_valid_one_record_ledger` uses and the review rehearsal confirmed `append` accepts, F-7), then run `aw runs evidence <ledger>` in human mode and assert the token is absent and `[REDACTED]` present, and run it with `--agent` and assert the same (parity). Do NOT pass a `RedactionPolicy` to `append`, so the secret is genuinely present on disk and only the output layer masks it; assert the raw ledger file DOES contain the token so the test cannot pass vacuously.
  - Depends on: E-01
  - Expected outcome: content-secret test passes post-fix and fails pre-fix; the on-disk precondition assertion holds.
  - Execution state: performed

### Task group 3: user-facing record

- [x] E-04 Add one `- Fixed:` line to the pending 2.0.0 section of `CHANGELOG.md` stating that `aw runs` and `aw run` human output now masks tokens (such as `ghp_` tokens and `Bearer` credentials) the same way `--agent` and `--json` already did. User-facing prose: no em or en dashes.
  - Depends on: E-01
  - Expected outcome: CHANGELOG carries the line; `grep -nP "[\x{2013}\x{2014}]"` on the added line finds nothing.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The module's machine payload shape is a bare dict (`ok`/`error`/`exit_code`), deliberately NOT `aw.agent/v1` (see `run_cli._emit_error` docstring, F-16); this plan does not touch machine payloads.
- The `error: ` prefix belongs to the human path (`run_cli._emit_ledger_not_found` docstring, F-17); `_print_human` must preserve it byte-for-byte.
- Existing run-CLI tests drive the real CLI by subprocess and assert on exit code + payload (`tests/test_run_cli_corruption_exit.py::test_missing_ledger_reports_invalid_invocation`); the new test follows that style (P16: behavior, no source reading).
- Ledger-level redaction at write time exists separately (`run_ledger_store.RedactionPolicy`); it is opt-in per append and is not what this plan fixes. Output-layer masking is the defense for secrets already on disk.
- Suite is run bare: `python3 -m pytest` (repo-local development contract in `AGENTS.md`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | Only `_emit_machine` calls `_redact_output`. | `grep -n "_redact_output" agent_workflows/run_cli.py` at authoring HEAD: the definition, its recursive self-calls, and the single call `sanitized = _redact_output(payload)` in `_emit_machine`. |
| F-2 | Human branch of `_emit_error` prints raw. | `else: print(f"error: {message}")` in `run_cli._emit_error`. |
| F-3 | Leak reproduced on every read leaf at authoring time. | Authoring measurement with target `/tmp/opencode/x/ghp_BBBBBBBBBBBBBBBBBBBBBBBB`: count of token occurrences in human stdout was 1 for `show`, `status`, `evidence`, `verify-ledger`, `next`, `resume`, and `decisions`; `--agent` was 0 for each of the first six. |
| F-4 | Ledger-content leak (backlog repro 2): `_run_evidence` human branch prints `f"  Command: {item.get('argv')}"` raw. | `run_cli._run_evidence`; the machine branch masks the same `argv` via `_emit_machine`. |
| F-5 | The redaction capability is adequate for the reported classes. | `_redact_output` regex `(ghp_[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._~+/-]+)`; idempotent on `[REDACTED]` (starts with `[`, so re-application is a no-op). |
| F-6 | Review re-measurement at HEAD `d1dfd6295`, target `/tmp/opencode/rv/ghp_<24 B>`: human token count 1 and exit 2 on ALL TWELVE leaves (`show status next resume evidence verify-ledger decisions questions` under `aw runs`, `start record cancel finalize` under `aw run`); `--agent` count 0 on the first six but 1 on `decisions` and `questions`, because `run_cli._run_decisions`/`_run_questions` print unconditionally with no machine branch. | Loop run in the review lane. |
| F-7 | The content-secret repro needs a schema-valid ledger: a minimal record is refused (`RL-E010` missing `schema_version`/`parent`, `RL-E014` unknown actor, `RL-E015` run_id shape, `RL-E034` stdout_sha256 shape). With the `_create_valid_one_record_ledger` field set plus a bare-hex `stdout_sha256`, the ledger holds the token on disk (count 1), human `runs evidence` prints `Authorization: Bearer ghp_...` verbatim at exit 0, and `--agent` prints `Authorization: [REDACTED]`. | Review-lane script, temp dir removed afterwards. |

## Proposed changes (ordered, validatable)

1. E-01: introduce `_print_human` and route all human prints through it (single choke point, same as `_emit_machine` is for machine output).
2. E-02/E-03: subprocess-driven tests for path-embedded and content-embedded secrets, with pre-fix failure confirmed.
3. E-04: CHANGELOG entry.

Alternative considered and rejected: wrapping `sys.stdout` with a redacting stream inside `run_cli.run_cli`. It would catch future prints automatically but redacts per `write` chunk (a token split across writes would escape), is invisible at call sites, and does not cover direct callers of the `_run_*` handlers. An explicit helper plus a test over every leaf is more reviewable.

## Deferred / out of scope (with reason)

- Widening `_redact_output`'s pattern set (other token formats, home-path redaction of human output): a separate policy decision; this plan only makes the existing property true on both surfaces.
  - Carrier-Declined: no measured leak class outside the existing pattern set is reported; widening it is a policy change with no defect behind it.
- Converting machine payloads to `aw.agent/v1`: explicitly out of scope per the `_emit_error` docstring (F-16).
  - Carrier-Declined: a deliberate, documented contract choice recorded in `run_cli._emit_error`'s docstring; not a defect of this item.
- The run viewer (`agent_workflows/run_viewer.py`, bare `aw runs` / `aw runs list`): a different module not covered by this docstring claim.
  - Carrier-Declined: no leak is measured there and the redaction claim being restored is `run_cli`'s own docstring.
- Backlog `h9kgjp` (exit-code half of the same docstring) is already `done`; nothing here depends on it.
  - Carrier-Evidence: .aw/records/backlog/done/20260930-h9kgjp-01-h9kgjp-run-cli-docstring-contradicts-own-exit-constants.backlog.md

## Scope check

- Over-scope: none.
- Under-scope: none known after review. The writer leaves (`aw run start|record|cancel|finalize`) reach the absent-ledger refusal with no extra arguments (F-6), so E-02 tests them explicitly. The `decisions`/`questions` machine-mode leak (F-6) is closed by the same E-01 routing and asserted by E-02.

## Required tests / validation

- New `tests/test_run_cli_human_redaction.py` (E-02, E-03) passes, and is shown to FAIL against the pre-E-01 `run_cli.py` (e.g. `git stash`-free check: run the tests at the pre-fix commit in a scratch worktree, or temporarily revert only `run_cli.py` in the lane and restore it).
- Existing run-CLI tests still pass: `python3 -m pytest tests/test_run_cli_corruption_exit.py tests/test_run_cli_declarations.py tests/test_run_recovery_cli.py tests/test_runs_subdir_root.py tests/test_runs_repo_alias.py tests/test_runs_flag_position_parity.py`.
- Full suite bare: `python3 -m pytest`, summary line pasted.
- Re-run the F-3 measurement loop post-fix: human-mode token count 0 on every leaf.

## Spec / documentation sync

- `agent_workflows/run_cli.py` module docstring: bullet kept, one sentence added naming the choke point (E-01).
- `CHANGELOG.md`: one Fixed line (E-04).
- Specs: N/A. No approved spec states the run CLI's human redaction property (`docs/cli-output-contract.md` "Path Sanitization and Leak Posture" governs machine surfaces only; spec `25kzda` mentions evidence redaction at capture, not output), so no spec text changes.

## Open questions

### OQ-01: Should human output also apply home-path redaction?

- Blocking: no
- Status: deferred
- Owner: plan author
- Resolution or deferral rationale: The machine surface does not apply home-path redaction in this module either, so doing it only on the human side would create a new asymmetry. Deferred as out of scope; parity with the existing `_redact_output` is the contract being restored. The `docs/cli-output-contract.md` home-path rule binds `aw.agent/v1` envelope fields, and this module's payloads are deliberately NOT `aw.agent/v1` (F-16), so whether it applies here is part of the declined `aw.agent/v1` conversion, not a gap this plan opens.
- Carrier-Declined: tied to the deliberately declined `aw.agent/v1` conversion (deferred row 2); a home path is not a credential and shows only on the operator's own surface.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `grep -n "print(" agent_workflows/run_cli.py` output showing `print(` only inside `_print_human` and `_emit_machine`; paste the post-fix re-run of the F-3 loop (human and `--agent` token counts per leaf for all twelve leaves: `runs show status evidence verify-ledger next resume decisions questions` and `run start record cancel finalize`), every count 0, with each exit code pasted and equal to 2. Code path observed: `run_cli.run_cli` dispatch into each `_run_*` handler, created by E-01.
  - Observed evidence:
    `grep -n "print(" agent_workflows/run_cli.py`:
    ```
    192:    print(_redact_output(text), end=end)
    201:                print(
    207:            print(
    213:        print(json.dumps(sanitized, sort_keys=True, indent=2, ensure_ascii=False))
    ```
    Post-fix F-3 measurement loop:
    ```
    runs show (human): count=0 [REDACTED]=1 exit=2
    runs show (--agent): count=0 [REDACTED]=1 exit=2
    runs status (human): count=0 [REDACTED]=1 exit=2
    runs status (--agent): count=0 [REDACTED]=1 exit=2
    runs evidence (human): count=0 [REDACTED]=1 exit=2
    runs evidence (--agent): count=0 [REDACTED]=1 exit=2
    runs verify-ledger (human): count=0 [REDACTED]=1 exit=2
    runs verify-ledger (--agent): count=0 [REDACTED]=1 exit=2
    runs next (human): count=0 [REDACTED]=1 exit=2
    runs next (--agent): count=0 [REDACTED]=1 exit=2
    runs resume (human): count=0 [REDACTED]=1 exit=2
    runs resume (--agent): count=0 [REDACTED]=1 exit=2
    runs decisions (human): count=0 [REDACTED]=1 exit=2
    runs decisions (--agent): count=0 [REDACTED]=1 exit=2
    runs questions (human): count=0 [REDACTED]=1 exit=2
    runs questions (--agent): count=0 [REDACTED]=1 exit=2
    run start (human): count=0 [REDACTED]=1 exit=2
    run start (--agent): count=0 [REDACTED]=1 exit=2
    run record (human): count=0 [REDACTED]=1 exit=2
    run record (--agent): count=0 [REDACTED]=1 exit=2
    run cancel (human): count=0 [REDACTED]=1 exit=2
    run cancel (--agent): count=0 [REDACTED]=1 exit=2
    run finalize (human): count=0 [REDACTED]=1 exit=2
    run finalize (--agent): count=0 [REDACTED]=1 exit=2
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the pytest output for `python3 -m pytest -o addopts="" tests/test_run_cli_human_redaction.py -v` post-fix (all pass, per-case names visible), AND the same command's output against pre-fix `run_cli.py` showing the E-02 cases failing.
  - Observed evidence:
    Pre-fix pytest output against baseline `run_cli.py`:
    ```
    =========================== short test summary info ============================
    FAILED tests/test_run_cli_human_redaction.py::test_projection_leaves_path_secret_redacted[human-decisions]
    FAILED tests/test_run_cli_human_redaction.py::test_writer_leaves_path_secret_redacted[cancel]
    FAILED tests/test_run_cli_human_redaction.py::test_writer_leaves_path_secret_redacted[finalize]
    FAILED tests/test_run_cli_human_redaction.py::test_writer_leaves_path_secret_redacted[record]
    FAILED tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[evidence]
    FAILED tests/test_run_cli_human_redaction.py::test_projection_leaves_path_secret_redacted[human-questions]
    FAILED tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[resume]
    FAILED tests/test_run_cli_human_redaction.py::test_runs_evidence_ledger_content_secret_redacted
    FAILED tests/test_run_cli_human_redaction.py::test_projection_leaves_path_secret_redacted[--agent-decisions]
    FAILED tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[status]
    FAILED tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[show]
    FAILED tests/test_run_cli_human_redaction.py::test_projection_leaves_path_secret_redacted[--agent-questions]
    FAILED tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[verify-ledger]
    FAILED tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[next]
    FAILED tests/test_run_cli_human_redaction.py::test_writer_leaves_path_secret_redacted[start]
    ============================= 15 failed in 24.76s ==============================
    ```
    Post-fix pytest output:
    ```
    tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[show] PASSED [  6%]
    tests/test_run_cli_human_redaction.py::test_projection_leaves_path_secret_redacted[human-questions] PASSED [ 13%]
    tests/test_run_cli_human_redaction.py::test_writer_leaves_path_secret_redacted[start] PASSED [ 20%]
    tests/test_run_cli_human_redaction.py::test_projection_leaves_path_secret_redacted[human-decisions] PASSED [ 26%]
    tests/test_run_cli_human_redaction.py::test_runs_evidence_ledger_content_secret_redacted PASSED [ 33%]
    tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[resume] PASSED [ 40%]
    tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[next] PASSED [ 46%]
    tests/test_run_cli_human_redaction.py::test_writer_leaves_path_secret_redacted[record] PASSED [ 53%]
    tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[evidence] PASSED [ 60%]
    tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[verify-ledger] PASSED [ 66%]
    tests/test_run_cli_human_redaction.py::test_read_leaves_path_secret_redacted[status] PASSED [ 73%]
    tests/test_run_cli_human_redaction.py::test_writer_leaves_path_secret_redacted[finalize] PASSED [ 80%]
    tests/test_run_cli_human_redaction.py::test_projection_leaves_path_secret_redacted[--agent-decisions] PASSED [ 86%]
    tests/test_run_cli_human_redaction.py::test_writer_leaves_path_secret_redacted[cancel] PASSED [ 93%]
    tests/test_run_cli_human_redaction.py::test_projection_leaves_path_secret_redacted[--agent-questions] PASSED [100%]
    ============================= 15 passed in 23.33s ==============================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the E-03 test's pass line post-fix and its failure line pre-fix (same two runs as V-02), and quote the test's assertion that the raw ledger file contains the token.
  - Observed evidence:
    Pre-fix failure line:
    `FAILED tests/test_run_cli_human_redaction.py::test_runs_evidence_ledger_content_secret_redacted`
    Post-fix pass line:
    `tests/test_run_cli_human_redaction.py::test_runs_evidence_ledger_content_secret_redacted PASSED [ 33%]`
    Test assertion that raw ledger file contains the token:
    `assert token in ledger_file.read_text(encoding="utf-8")`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `git diff -- CHANGELOG.md` showing the single added Fixed line, and the empty output of a dash check on it.
  - Observed evidence:
    `git diff -- CHANGELOG.md`:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 61245695c..de2fd2f46 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Fixed: aw runs and aw run human output now masks tokens (such as ghp_ tokens and Bearer credentials) the same way --agent and --json already did.
     - Fixed: closing a release-blocking backlog item with --evidence now refuses a cited plan that has not been executed, on both setter spellings.
     - Added: advisory check rule `check.source-test-citation-dangling` flags comments and docstrings in shipped source (`agent_workflows/` and `tools/`) citing nonexistent `tests/test_*.py` files. The rule runs during `aw check all` at `info` severity without altering the exit code, and deliberate historical citations can be silenced by naming the deleting commit hash.
     - Fixed: `RedactionPolicy` sensitive-key matching is now case-insensitive (security fix, backlog go20fk).
    ```
    Dash check (`git diff -- CHANGELOG.md | grep -nP "[\x{2013}\x{2014}]"`): empty (no em or en dashes).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This is a security fix to a stated safety property; reviewers should push hardest on completeness (that NO human-mode print escapes the helper, which V-01's grep and per-leaf measurement establish) and on the tests failing pre-fix (V-02/V-03), so they cannot pass vacuously.

EXECUTION CONTRACT. OQ-01 is deferred with a recorded reason and blocks nothing. Commit only the paths in `- Scope-Paths:` through `aw commit omst3h -- <paths>`; never `git add -A` or `-a`, and never push. Verify the staged set with `git diff --cached --name-only` before committing. Any pre-fix comparison (V-02/V-03) temporarily restores ONLY `agent_workflows/run_cli.py` from the base commit and puts the fixed file back; never commit that state. Run the suite bare as `python3 -m pytest`, and paste the actual command and runner output for every test claim: never assert a pass you did not run. Backlog `94op6l` must not be set `done` by this plan; it closes through the From-Backlog handoff once this plan is executed, carrying `Blocks-Release: next`.

SCOPE FENCE. The declared change is `agent_workflows/run_cli.py`, the new test module, `CHANGELOG.md`, and this plan; the redaction pattern set and machine payload shapes are untouched. An out-of-scope edit that proves necessary is made and justified with `aw ipd finalize --scope-reason`, never silently.

POST-GATE LIFECYCLE. After every `E-*` is performed and every `V-*` reads `pass` with pasted evidence, run `aw ipd lint --phase pre-transition` and require it conforming. In a managed runner lane (`AW_EXECUTION_ROLE=worker`) the RUNNER owns `aw ipd begin`/`aw ipd finalize`; executing by hand, run `aw ipd begin` before the first edit and `aw ipd finalize` for the terminal move. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`.
