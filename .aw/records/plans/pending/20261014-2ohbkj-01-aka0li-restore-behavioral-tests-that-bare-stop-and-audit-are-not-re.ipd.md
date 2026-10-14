# IPD: Restore behavioral tests that bare stop and audit are not rewritten into start

- Date: 2026-10-14
- Kind: child
- Concern: The implicit-start shim in `agent_workflows/oc_runipd.py` (`main`) and `agent_workflows/agy_runipd.py` (`main`) prepends `"start"` to any first CLI token not listed in its inline `subcommands` set (`{start, resume, status, report, stop, integrate, audit, -h, --help}`). If `"stop"` or `"audit"` is omitted from either driver's `subcommands` set, a bare `stop <run-id> --now` or `audit <id6>` is rewritten into `start stop ...` or `start audit ...`, attempting to launch a run with `"stop"` or `"audit"` as a plan selector instead of routing to `handle_stop_command` or `handle_audit_command`. Commit `19313eed7` deleted both `tests/test_runner_stop_triggers.py` (which held `ImplicitStartShimTests._stop_is_not_rewritten`) and `tests/test_standalone_verify.py` (which held `TheVerbSurface.test_a_bare_audit_is_not_rewritten_into_a_run_launch` for `oc_runipd` only). Measured at authoring HEAD `408b1115d`: `rg -n 'main\(\["(stop|audit)"' tests/` returns zero matches, while `integrate` remains covered through `main()` in `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py`, and six comment lines in `oc_runipd.main` and `agy_runipd.main` explicitly state that restoring behavioral `stop` and `audit` coverage is tracked by backlog `2ohbkj`.
- Scope: Add one focused behavioral test module `tests/test_runner_bare_verb_shim.py` that drives `oc_runipd.main(["stop", ...])`, `agy_runipd.main(["stop", ...])`, `oc_runipd.main(["audit", ...])`, and `agy_runipd.main(["audit", ...])` against real temporary git repositories (including repositories with pending `approved` plans in Set `stop` and Set `audit` so an accidental shim rewrite into `start` would mint a run directory), asserting exit codes, stderr/stdout routing diagnostics, stop-request recording on a locked run, and the absence of any minted run directory. Prove mutation sensitivity against all four `(host, verb)` pairs, and update the twin `main()` shim comments in `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` so they cite the new behavioral test module instead of claiming `stop` and `audit` have no coverage and are awaiting `2ohbkj`. Do NOT restore any AST, `inspect`, or regex `_shim_set` code-pinning test (`GUIDING_PRINCIPLES` P16). No executable statement in any production module changes.
- Scope-Paths: tests/test_runner_bare_verb_shim.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, .aw/records/plans/pending/20261014-2ohbkj-01-aka0li-restore-behavioral-tests-that-bare-stop-and-audit-are-not-re.ipd.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: low
- From-Backlog: 2ohbkj
- Set: 2ohbkj
- Order: 1
- Highest E allocated: 06
- Author: antigravity
- Id: aka0li

## Workflow history
- 2026-10-14 to-review (antigravity): authored review-ready plan graduating backlog 2ohbkj; measured at HEAD 408b1115d

- 2026-10-14 draft (antigravity): created.

## Goal

Restore behavioral regression coverage proving that bare `stop` and `audit` first tokens are routed to `handle_stop_command` and `handle_audit_command`—and never rewritten into `start`—in both `oc_runipd.main` and `agy_runipd.main`, and update the twin `main()` shim comments so they accurately cite the restored coverage.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure baseline

- [ ] E-01 Re-measure the pre-edit baseline at execution HEAD: record `git rev-parse --short HEAD`, run `rg -n 'main\(\["(stop|audit)"' tests/` (expect no matches), and run `rg -n '2ohbkj' agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` to confirm the six comment lines inside `oc_runipd.main` and `agy_runipd.main` that point at backlog `2ohbkj`.
  - Depends on: none
  - Expected outcome: execution HEAD recorded, zero pre-edit matches for `main(["stop"...` or `main(["audit"...` under `tests/`, and the six `2ohbkj` comment hits in `oc_runipd.py` and `agy_runipd.py` confirmed.
  - Execution state: pending

### Task group 2: Author behavioral stop and audit shim tests

- [ ] E-02 Create `tests/test_runner_bare_verb_shim.py` with `BareStopNotRewrittenTests(unittest.TestCase)` driving `oc_runipd.main(["stop", ...])` and `agy_runipd.main(["stop", ...])` explicitly (with literal `oc_runipd.main(["stop", ...])` and `agy_runipd.main(["stop", ...])` calls so `rg -n 'main\(\["(stop|audit)"' tests/` matches both hosts). Include two behavioral test methods covering both hosts:
  1. `test_bare_stop_unknown_run_routes_to_stop_and_mints_no_run_dir`: initialize a temporary git repo containing a conformant `approved` pending plan in Set `stop` (`stop01`, formatted from `tests.test_oc_runipd._CONFORMING_PLAN` with `- Set: stop`), patch `run_queue` on the driver under test to raise `AssertionError("stop was rewritten into start and dispatched run_queue")`, invoke `oc_runipd.main(["stop", "run-nonexistent-abcdef", "--now", "--repo", os.fspath(repo)])` and `agy_runipd.main(["stop", "run-nonexistent-abcdef", "--now", "--repo", os.fspath(repo)])` with stdout/stderr captured, and assert `rc == 2`, stdout is empty, stderr contains `"Run not found: run-nonexistent-abcdef (nothing was created or modified)"`, and `<repo>/.aw/records/runs` either does not exist or is empty.
  2. `test_bare_stop_live_run_records_request_without_minting_second_run_dir` (decorated with `@unittest.skipIf(fcntl is None, "POSIX flock required for live run lock")`): create `<repo>/.aw/records/runs/<run-id>` and hold an exclusive non-blocking `fcntl.flock` on `<run-dir>/driver.lock`, invoke `oc_runipd.main(["stop", run_id, "--now", "--repo", os.fspath(repo)])` and `agy_runipd.main(["stop", run_id, "--now", "--repo", os.fspath(repo)])`, and assert `rc == 0`, `runner_stop.read_stop_request(run_dir).level == runner_stop.LEVEL_NOW`, stdout contains `"stop accepted: level 3 (now)"` and the host-specific escalation hint (`"aw oc run stop"` for `oc_runipd`, `"aw agy run stop"` for `agy_runipd`), and the only directory under `<repo>/.aw/records/runs` is `<run-id>`.
  - Depends on: E-01
  - Expected outcome: `tests/test_runner_bare_verb_shim.py` exists and both `BareStopNotRewrittenTests` test methods pass against `oc_runipd` and `agy_runipd`.
  - Execution state: pending

- [ ] E-03 In `tests/test_runner_bare_verb_shim.py`, add `BareAuditNotRewrittenTests(unittest.TestCase)` driving `oc_runipd.main(["audit", ...])` and `agy_runipd.main(["audit", ...])` explicitly (with literal `oc_runipd.main(["audit", ...])` and `agy_runipd.main(["audit", ...])` calls). Include two behavioral test methods covering both hosts:
  1. `test_bare_audit_with_matching_pending_set_routes_to_audit_and_mints_no_run_dir`: initialize a temporary git repo containing a conformant `approved` pending plan in Set `audit` with id6 `audt01` (`20260828-audit-01-audt01-demo.ipd.md`, formatted from `tests.test_oc_runipd._CONFORMING_PLAN` with `- Set: audit`) so that if `"audit"` were omitted from `subcommands`, the rewritten `["start", "audit", "audt01", "--repo", ...]` would resolve Set `audit` / plan `audt01` as valid `start` selectors and `initialize_run` would mint a run directory under `<repo>/.aw/records/runs` before reaching `run_queue` (which is patched to raise `AssertionError("audit was rewritten into start and dispatched run_queue")`). Assert that `oc_runipd.main(["audit", "audt01", "--repo", os.fspath(repo)])` returns `rc == 1` with empty stdout, `"audit refused (audit-plan-not-executed)"` on stderr, and no directory under `<repo>/.aw/records/runs`; and assert that `agy_runipd.main(["audit", "audt01", "--repo", os.fspath(repo)])` returns `rc == 2` with empty stdout, `"audit is not implemented on the Antigravity host"` and `"aw oc run audit audt01"` on stderr, and no directory under `<repo>/.aw/records/runs`.
  2. `test_bare_audit_unknown_plan_routes_to_audit_and_mints_no_run_dir`: on the same repository fixture, invoke `oc_runipd.main(["audit", "nosuch", "--repo", os.fspath(repo)])` and `agy_runipd.main(["audit", "nosuch", "--repo", os.fspath(repo)])`; assert `oc_runipd` returns `1` with `"audit refused (audit-plan-not-found)"` on stderr, `agy_runipd` returns `2` with `"audit is not implemented on the Antigravity host"` and `"aw oc run audit nosuch"` on stderr, and neither creates a directory under `<repo>/.aw/records/runs`.
  - Depends on: E-02
  - Expected outcome: all tests in `BareStopNotRewrittenTests` and `BareAuditNotRewrittenTests` pass via `python3 -m pytest -o addopts="" -v tests/test_runner_bare_verb_shim.py`.
  - Execution state: pending

### Task group 3: Prove mutation sensitivity and sync runner shim comments

- [ ] E-04 Run a one-off mutation-sensitivity probe (never committed) against all four `(module, verb)` pairs—`(agent_workflows/oc_runipd.py, "stop")`, `(agent_workflows/agy_runipd.py, "stop")`, `(agent_workflows/oc_runipd.py, "audit")`, and `(agent_workflows/agy_runipd.py, "audit")`—wrapping each in a `try`/`finally` that records the pre-mutation `sha256`, removes only that verb literal from the inline `subcommands` set in `main()`, runs `python3 -m pytest -o addopts="" tests/test_runner_bare_verb_shim.py`, confirms the suite exits nonzero with the corresponding test failing, and restores the exact original bytes in `finally:`, verifying equal pre/post `sha256` digests and `git diff --quiet -- agent_workflows/`.
  - Depends on: E-03
  - Expected outcome: each of the four single-verb removals turns `tests/test_runner_bare_verb_shim.py` red, and both production files are restored byte-for-byte (`sha256` equal before and after).
  - Execution state: pending

- [ ] E-05 Update the twin implicit-start shim comments in `agent_workflows/agy_runipd.py` (`main`) and `agent_workflows/oc_runipd.py` (`main`) so they no longer say `stop` and `audit` lack `main()` coverage or await backlog `2ohbkj`: state that `tests/test_runner_bare_verb_shim.py` drives bare `stop` and `audit` through both drivers' `main()` (while `integrate` is driven through `main()` in `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py`), and that the historical structural guard (`tests/test_runner_stop_triggers.py`, which read `subcommands` from source) was a code pin deleted in `19313eed7` that will not return under P16 so non-hazardous set lockstep remains held by review. Verify with a one-off AST comparison against the E-01 base commit (`ast.dump(..., include_attributes=False)` with docstrings stripped) that both `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` print `EQUAL`.
  - Depends on: E-04
  - Expected outcome: `rg -n '2ohbkj' agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` shows no remaining claim that `stop`/`audit` lack live coverage (or cites `2ohbkj` only as the completed origin of `tests/test_runner_bare_verb_shim.py`), `rg -n 'main\(\["(stop|audit)"' tests/` matches all four `(host, verb)` calls in `tests/test_runner_bare_verb_shim.py`, and the AST comparison prints `EQUAL` for both runner modules.
  - Execution state: pending

### Task group 4: Full-suite verification and commit

- [ ] E-06 Run `python3 -m pytest -o addopts="" -v tests/test_runner_bare_verb_shim.py`, `aw check`, `aw sanitize --agent`, and the bare fast suite `python3 -m pytest`; confirm no regressions and commit only the scoped paths via `aw commit aka0li -- <paths>`.
  - Depends on: E-05
  - Expected outcome: new test module, `aw check`, `aw sanitize --agent`, and bare `python3 -m pytest` pass; changes committed cleanly on the lane branch without pushing.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `AGENTS.md` ("TEST OUTCOMES, NOT CODE STRUCTURE") and `GUIDING_PRINCIPLES.md` P16 forbid tests that read production source (`inspect`, `ast`, regex, substring) or pin code structure. The deleted `ImplicitStartShimTests._shim_set`, `test_the_hazardous_verbs_are_listed_in_both_shims_subcommand_sets`, and `test_the_inline_copy_matches_both_drivers` in `19313eed7^:tests/test_runner_stop_triggers.py` were AST/source pins and must NOT be restored; backlog `2ohbkj` explicitly states "Do NOT restore the AST/regex `_shim_set` pin (P16)".
- Precedent for restoring behavioral coverage from files deleted in `19313eed7`: executed plan `df486j` (backlog `mv18lz`, `tests/test_manifest_entry_selectable.py`) and approved plan `z2ugxc` (backlog `yf1p8y`, `tests/test_runner_backlog_close_behavior.py`) place the restored behavioral tests in a focused new test module, prove mutation sensitivity against the production code without committing the mutation, and update any production comment that claimed coverage was missing and tracked by the graduating backlog item, proving via AST dump equality that no executable production statement changed (same technique as `65d5zf` V-06).
- Executed plan `ml7b9e` (backlog `j7daih`) added an advisory `aw check` rule (`check.source-dangling-test-citation`) that flags shipped source comments citing a `tests/test_*.py` file that does not exist unless inside a retirement statement; citing `tests/test_runner_bare_verb_shim.py` in `oc_runipd.py` and `agy_runipd.py` in the same commit that creates `tests/test_runner_bare_verb_shim.py` satisfies that rule cleanly.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Run the test suite BARE as `python3 -m pytest` (no `-n0`, no extra `-q`, no `-p no:randomly`); clear `addopts` with `-o addopts=""` only for narrowed single-file runs.

## Findings

| Id | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | MEDIUM | At HEAD `408b1115d`, `rg -n 'main\(\["(stop\|audit)"' tests/` -> no matches; `git show 19313eed7^:tests/test_runner_stop_triggers.py` (`ImplicitStartShimTests._stop_is_not_rewritten`) and `git show 19313eed7^:tests/test_standalone_verify.py` (`TheVerbSurface.test_a_bare_audit_is_not_rewritten_into_a_run_launch`) show both were deleted in `19313eed7` | Neither `oc_runipd.main` nor `agy_runipd.main` has any live test driving a bare `stop` or `audit` first token through `main()`. Notice also that `test_standalone_verify.py` only ever drove `oc_runipd.main(["audit", ...])` and tested `agy_runipd.handle_audit_command` directly via `argparse.Namespace`, bypassing `agy_runipd.main`'s implicit-start shim entirely. |
| F-02 | MEDIUM | `initialize_run_core` in `agent_workflows/runner_shared.py` (`discover_plans(repo)`) raises `DriverError("No pending IPDs found...")` with exit code `2` before creating `.aw/records/runs` when invoked on an empty repository | On an empty repository with no pending plans, removing `"audit"` from `agy_runipd.main`'s `subcommands` rewrites `["audit", "nosuch", "--repo", repo]` into `["start", "audit", "nosuch", "--repo", repo]`, which fails in `discover_plans` with exit code `2` and creates no run directory—matching `agy_runipd.handle_audit_command`'s exit code `2` and no-run-dir outcome if stderr and a matching pending Set are not checked. Including a conformant `approved` pending plan in Set `audit` (`audt01`) AND asserting on stderr makes the test doubly discriminating: under mutation `initialize_run` resolves Set `audit` / `audt01`, mints a real run directory under `.aw/records/runs`, and dispatches `run_queue`. |
| F-03 | LOW | `rg -n '2ohbkj' agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` at HEAD `408b1115d` matches lines 4233, 4241, 4252 in `agy_runipd.main` and lines 5431, 5435, 5459 in `oc_runipd.main` (written by executed plan `65d5zf`) | Both drivers' `main()` shim comments currently state that `stop` and `audit` have no live coverage through `main()` and that restoring it is tracked by backlog `2ohbkj`. Leaving those comments untouched when `2ohbkj` executes would make all six lines stale. |
| F-04 | INFO | `tests/test_oc_runipd.py::HostIntegrateCliSurfaceTests` (`driver.main(["integrate", ...])`) and `tests/test_agy_runipd_cli.py::AgyIntegrateCliSurfaceTests` (`agy_runipd.main(["integrate", ...])`) | Bare `integrate` is already behaviorally covered through `main()` on both hosts, as noted in the backlog item (`2ohbkj`). |

## Proposed changes (ordered, validatable)

1. Re-measure the pre-edit baseline at execution HEAD (E-01).
2. Create `tests/test_runner_bare_verb_shim.py` with `BareStopNotRewrittenTests` covering unknown-run refusal and live-locked-run stop recording through `oc_runipd.main` and `agy_runipd.main` (E-02).
3. Add `BareAuditNotRewrittenTests` in `tests/test_runner_bare_verb_shim.py` covering pending Set `audit` collision and unknown-plan refusal through `oc_runipd.main` and `agy_runipd.main` (E-03).
4. Prove mutation sensitivity across all four `(host, verb)` pairs with byte-identical restoration (E-04).
5. Update the twin `main()` shim comments in `agent_workflows/agy_runipd.py` and `agent_workflows/oc_runipd.py` to cite `tests/test_runner_bare_verb_shim.py`, and prove via AST dump comparison that no executable statement changed (E-05).
6. Run `tests/test_runner_bare_verb_shim.py`, `aw check`, `aw sanitize --agent`, and the bare `python3 -m pytest` suite, then commit via `aw commit` (E-06).

## Deferred / out of scope (with reason)

- Restoring `_shim_set`, `SHIM_SUBCOMMANDS`, `test_the_hazardous_verbs_are_listed_in_both_shims_subcommand_sets`, or `test_the_inline_copy_matches_both_drivers` from the deleted `tests/test_runner_stop_triggers.py`.
  - Carrier-Declined: forbidden by `AGENTS.md` ("TEST OUTCOMES, NOT CODE STRUCTURE"), `GUIDING_PRINCIPLES` P16, and backlog `2ohbkj` ("Do NOT restore the AST/regex `_shim_set` pin (P16)").
- Adding duplicate bare-`integrate` shim tests.
  - Carrier-Declined: bare `integrate` is already driven through `oc_runipd.main` in `tests/test_oc_runipd.py::HostIntegrateCliSurfaceTests` and through `agy_runipd.main` in `tests/test_agy_runipd_cli.py::AgyIntegrateCliSurfaceTests` (F-04).
- Implementing `audit` execution on the Antigravity host (`agy_runipd.handle_audit_command`).
  - Carrier-Declined: deliberate architectural decision of executed plan `mp289j` and spec `i4gpto` (`audit` is declared on both hosts and implemented on OpenCode only, with `agy_runipd.handle_audit_command` refusing with exit code `2` and naming `aw oc run audit <id6>`).

## Scope check

- Over-scope: `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` are included alongside `tests/test_runner_bare_verb_shim.py` for comment-only edits in `main()` because `65d5zf` E-05/E-06 wrote six lines in those two comment blocks stating that `stop` and `audit` have no live `main()` coverage and are tracked by `2ohbkj` (F-03); E-05/V-05 proves via AST dump comparison that no executable production statement changes.
- Under-scope: none. Both hazardous verbs lacking live `main()` coverage (`stop` and `audit`) are covered on both hosts (`oc_runipd` and `agy_runipd`) and proven mutation-sensitive across all four `(host, verb)` combinations (E-04).

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_runner_bare_verb_shim.py` passes all four test methods across both drivers (E-02, E-03).
- `rg -n 'main\(\["(stop|audit)"' tests/` matches `oc_runipd.main(["stop", ...])`, `agy_runipd.main(["stop", ...])`, `oc_runipd.main(["audit", ...])`, and `agy_runipd.main(["audit", ...])` in `tests/test_runner_bare_verb_shim.py` (E-05).
- Each of the four `(host, verb)` inline-set removals in `oc_runipd.main` and `agy_runipd.main` causes `tests/test_runner_bare_verb_shim.py` to fail, and original bytes are restored with verified `sha256` equality (E-04).
- AST comparison of `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` against the E-01 base commit prints `EQUAL` (E-05).
- `aw check`, `aw sanitize --agent`, and a bare `python3 -m pytest` run pass without regressions (E-06).

## Spec / documentation sync

N/A with reason: no `.spec.md` or user-facing documentation file changes. The behavior under test (`stop` in spec `c4gd2h` R14/R15 and `audit` in spec `i4gpto` R-5) is already specified and shipped; this plan restores behavioral tests and updates internal source comments in `oc_runipd.main` and `agy_runipd.main`.

## Open questions

### OQ-01: Should the restored behavioral tests live in a new focused module or be split across `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved in favor of one focused module `tests/test_runner_bare_verb_shim.py`. Placed together, the two hosts' `stop` and `audit` shim behaviors are tested side-by-side with shared fixtures in under 2 seconds (whereas `tests/test_oc_runipd.py` + `tests/test_agy_runipd_cli.py` take ~125s), giving both drivers' `main()` shim comments one canonical test module to cite and matching the precedent of `tests/test_manifest_entry_selectable.py` (`df486j`) and `tests/test_runner_backlog_close_behavior.py` (`z2ugxc`).

### OQ-02: Should the `2ohbkj` comment references in `oc_runipd.main` and `agy_runipd.main` be updated in this plan?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes (F-03). Executed plan `65d5zf` E-05/E-06 wrote six lines in `oc_runipd.main` and `agy_runipd.main` stating that `stop` and `audit` have no live `main()` coverage and pointing at `2ohbkj`; updating those comments in the same commit that lands `tests/test_runner_bare_verb_shim.py` prevents them from becoming stale, and E-05's AST comparison proves the production edits are comment-only.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of `git rev-parse --short HEAD`, `rg -n 'main\(\["(stop|audit)"' tests/` (showing zero pre-edit matches), and `rg -n '2ohbkj' agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` (showing the six pre-edit comment lines).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_runner_bare_verb_shim.py -k BareStopNotRewrittenTests` showing both `test_bare_stop_unknown_run_routes_to_stop_and_mints_no_run_dir` and `test_bare_stop_live_run_records_request_without_minting_second_run_dir` passing (produced by driving `oc_runipd.main` and `agy_runipd.main` created in E-02), plus the quoted test source showing literal `oc_runipd.main(["stop", ...])` and `agy_runipd.main(["stop", ...])` calls.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_runner_bare_verb_shim.py` showing all four tests in `BareStopNotRewrittenTests` and `BareAuditNotRewrittenTests` passing (produced by driving `oc_runipd.main` and `agy_runipd.main` created in E-02 and E-03), plus the quoted `BareAuditNotRewrittenTests` source showing the pending Set `audit` (`audt01`) fixture and literal `oc_runipd.main(["audit", ...])` and `agy_runipd.main(["audit", ...])` calls.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted output of the one-off mutation probe over all four `(module, verb)` pairs—`(oc_runipd, "stop")`, `(agy_runipd, "stop")`, `(oc_runipd, "audit")`, and `(agy_runipd, "audit")`—showing for each pair the failing test node id(s) when the verb is removed from `subcommands` in `main()`, the pre-mutation and post-restoration `sha256` digests of `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` (equal), and `git diff --quiet -- agent_workflows/` exiting 0.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: The rewritten `agy_runipd.main` and `oc_runipd.main` shim comment blocks quoted in full; pasted output of `rg -n 'main\(\["(stop|audit)"' tests/` showing matches for `stop` and `audit` on both `oc_runipd` and `agy_runipd` in `tests/test_runner_bare_verb_shim.py`; and pasted AST comparison script + output comparing `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` against the E-01 base commit (`ast.dump(..., include_attributes=False)` with docstrings stripped) printing `EQUAL` for both files.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_runner_bare_verb_shim.py`, `aw check`, `aw sanitize --agent`, the bare `python3 -m pytest` summary line (no flags added), and `git show --stat HEAD` after `aw commit aka0li -- <paths>`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). OQ-01 and OQ-02 are resolved; no blocking open question remains. Scope fence: commit only the declared `- Scope-Paths:` through `aw commit aka0li -- <paths>`, never `git add -A`, never push, and never commit while an E-04 mutation probe is active. Do NOT write any source-reading (`inspect`, `ast`, regex, substring) test in `tests/test_runner_bare_verb_shim.py` (`GUIDING_PRINCIPLES` P16). Change no executable statement in `agent_workflows/oc_runipd.py` or `agent_workflows/agy_runipd.py` (proven by V-05's AST comparison). Paste actual runner output for every validation item. Under `aw oc run` / `aw agy run`, the runner owns `aw ipd begin` and `aw ipd finalize`; in a manual run, use `aw ipd begin aka0li`, complete every `E-*`/`V-*` with pasted evidence, verify `aw ipd lint --phase pre-transition` conforms, and run `aw ipd finalize aka0li`.
