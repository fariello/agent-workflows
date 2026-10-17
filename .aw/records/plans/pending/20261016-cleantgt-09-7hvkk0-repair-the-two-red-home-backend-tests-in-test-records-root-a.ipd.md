# IPD: Repair the two red home-backend tests in test_records_root_accessor

- Date: 2026-10-16
- Kind: child
- Concern: `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py` reports `2 failed, 16 passed` at HEAD `f0ac1c64c`. `test_home_records_runner_discovery` reads its plan fixture from the LIVE corpus path `.aw/records/plans/pending/20261015-cleantgt-01-kfnfji-...ipd.md`, which no longer exists because kfnfji moved to `executed/`. `test_home_records_reproduction_prompts_index` expects `aw index prompts` to create the home-backed prompts directory, but plan fbdxmh (commit `8bad89081`) deliberately made every index write REFUSE (exit 2, `cannot-run`) when the resolved records directory is absent, and the `home_records_env` fixture never materializes that directory the way `aw install` does. Both are test defects: production behavior is correct in both cases (measured, see Findings).
- Scope: IN: make `test_home_records_reproduction_prompts_index` materialize the home-backed `records/prompts` directory (as `aw install` does) before asserting the write lands under `AW_HOME`, and add a sibling test pinning the fbdxmh refusal for the absent-directory case on a home-backed project (exit 2, nothing created in the target or under `AW_HOME`, no traceback). The OTHER half of backlog 5mnbaz, decoupling `test_home_records_runner_discovery` from the live `.aw/records/` corpus, is OWNED by the already-approved plan `4v8s0m` (Set g9kupi, backlog g9kupi, same defect, same test), and is NOT duplicated here (review PR-001). The two plans are independent and may execute in either order; this plan's module-level bar tolerates exactly the known runner-discovery failure while `4v8s0m` is unexecuted (E-01, E-05). OUT: any change to `agent_workflows/` (production behavior is correct); `test_home_records_runner_discovery` (owned by `4v8s0m`); the `home_records_env` fixture shape used by the other tests in the module; ki6t17's walkers.
- Scope-Paths: tests/test_records_root_accessor.py
- Item-Dependencies: executed:kfnfji, executed:fbdxmh
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 5mnbaz
- Blocks-Release: next
- Set: cleantgt
- Order: 9
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7hvkk0
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): plan-review: revisions applied (PR-001..PR-005)

- 2026-10-16 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-16 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-16 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog 5mnbaz at HEAD f0ac1c64c; both failures reproduced and root-caused by measurement.

## Goal

Return `tests/test_records_root_accessor.py` to green without weakening what it proves: the prompts index test must keep proving the write lands under `AW_HOME` and never in the target, while also pinning the fbdxmh refusal it currently contradicts. The runner discovery test is returned to green by `4v8s0m`, so once both plans execute the whole module is green.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure

- [x] E-01 Re-measure the module at the executing HEAD before changing anything, and record where `4v8s0m` is (`ls .aw/records/plans/*/ | grep 4v8s0m`).
  - Depends on: none
  - Expected outcome: pasted output of `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py` showing `test_home_records_reproduction_prompts_index` failing (exit 2, `records directory records/prompts does not exist; nothing was written.`). `test_home_records_runner_discovery` passes if `4v8s0m` is executed, else fails with `FileNotFoundError` on the `plans/pending/...kfnfji...` path; no other test fails. If the prompts index test already passes, or any test fails other than these, stop and record the divergence in this plan before continuing.
  - Execution state: performed

### Task group 2: prompts index test

- [x] E-04 In `test_home_records_reproduction_prompts_index`, before running `aw index prompts`, create the home-backed prompts directory exactly where the resolver places it: `(project_context.project_records_dir(target, aw_home=aw_home) / "prompts").mkdir(parents=True)` (this mirrors `engine._records_member_destination`, through which `aw install` creates the records tree). Keep the existing assertions (exit 0, no `target/.aw/records/prompts`, exactly one `*/records/prompts/INDEX.json` under `AW_HOME/projects`). Update the docstring to say the directory is pre-created because index writes refuse on an absent directory (fbdxmh).
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py -k prompts_index` passes.
  - Execution state: performed

- [x] E-05 Add `test_home_records_prompts_index_refuses_absent_dir(home_records_env)`: on the unmodified fixture (no prompts directory anywhere), run `aw index prompts --dir <target> --agent` and assert exit `2`, no `Traceback` in stderr, the last stdout line parses as JSON with `outcome == "cannot-run"` and a `records-dir-missing` diagnostic whose location does NOT start with `.aw/records/` (proving it names the home-resolved directory, not an in-repo one), and afterwards neither `target/.aw/records` nor any `AW_HOME/projects/*/records/prompts` exists.
  - Depends on: E-04
  - Expected outcome: the new test passes, and the whole module reports zero failures and zero errors, EXCEPT that while `4v8s0m` is not yet executed exactly `test_home_records_runner_discovery` may fail, and only with the `FileNotFoundError` on the `plans/pending/...kfnfji...` path (re-derive the collected count at execution; it is not a bar).
  - Execution state: performed

## Project conventions discovered (Step 0)

- The routine gate is `python3 -m pytest` (pyproject `addopts` supplies `-q -n auto ... -m 'not slow and not livecorpus'`); `tests/test_records_root_accessor.py` is not in `testpaths`, so it is run explicitly with `-o addopts=""`.
- `test_home_records_runner_discovery`'s live-corpus read is owned by approved plan `.aw/records/plans/pending/20261016-g9kupi-01-4v8s0m-decouple-test-home-records-runner-discovery-from-the-live-re.ipd.md` (backlog g9kupi), which replaces it with a synthetic in-test fixture plan (id6 `zq9fx1`, Set `fixtset`).
- Index writes refuse on an absent directory by design: `artifact_core.emit_index_missing_dir_refusal`, called from `prompts_index.run_index` under `if not prompts_dir.is_dir():` (plan fbdxmh, executed). Its docstring states the reason: a mkdir would write under `$HOME/.aw/projects/` for a home-backend resolution and shadow a later in-repo tree.
- `aw install` creates the home records tree through `engine._records_member_destination`, which maps `.aw/records/<tail>` onto `project_context.project_records_dir(repo_root) / tail`.
- Tests must exercise behavior through subprocess CLI calls and assert on outputs, exit codes, and side effects (AGENTS.md, no code-pinning).

## Findings

| ID | Severity | Location | Finding |
|---|---|---|---|
| F-01 | medium | `tests/test_records_root_accessor.py` `test_home_records_runner_discovery` | OWNED BY `4v8s0m`, not remediated here (review PR-001); retained as the measured diagnosis. Reads `REPO_ROOT/.aw/records/plans/pending/20261015-cleantgt-01-kfnfji-...ipd.md`; kfnfji is now in `.aw/records/plans/executed/` (measured with `ls .aw/records/plans/*/`), so `read_text` raises FileNotFoundError. Merely repointing to `executed/` is not enough: measured, a copy of the executed plan (Status `executed`) is not queueable, and a hand-flipped `approved` copy is refused by `aw oc run start --prepare-only` (`IPD-M104` Approval required). The plan text at commit `5acca6ce5` (Status `approved`, real Approval and review history) DOES queue: measured in a home-backed temp repo with ids renamed to `hrrun1`/`hrfix`, `aw show hrrun1` exit 0 and prepare-only exit 0 printing `Run order (1 item(s)): 01 hrrun1` and a row containing `hrfix 01 hrrun1`. |
| F-02 | medium | `tests/test_records_root_accessor.py` `test_home_records_reproduction_prompts_index`, `home_records_env` | The fixture writes only `.aw/config/project.json` (`records_backend: home`) and never creates the home records tree. Since fbdxmh, `aw index prompts` refuses (exit 2) instead of creating it. Measured: the refusal names `records/prompts` (home-resolved, NOT `.aw/records/prompts`), so the kfnfji regression (writing to / crashing on the in-repo path) is NOT back. Measured: after `aw install . -y --no-interactive --preset private-target --records-backend home` the home tree includes `records/prompts` and `aw index prompts` exits 0; and with only `project_records_dir(target, aw_home) / "prompts"` pre-created, the index writes exactly `awh/projects/<id>/records/prompts/INDEX.json`. Conclusion for the backlog's "determine which": the fixture no longer creates the directory; production is correct. |

## Proposed changes (ordered, validatable)

1. Pre-create the home-resolved prompts dir in the prompts index test (E-04).
2. Pin the fbdxmh refusal on a home-backed project in a new test (E-05).

## Deferred / out of scope (with reason)

- Changing `aw index` to create a missing home records directory: rejected, it reverses the deliberate fbdxmh decision (OQ-01 there, resolved from evidence).
  - Carrier-Declined: not a defect; fbdxmh's refusal is the intended contract and this plan pins it (E-05).
- Changing `home_records_env` to run a full `aw install`: rejected, it would change the setup of seven other passing tests and slow the module; only the one test needs the directory.
  - Carrier-Declined: not a defect; a design alternative rejected on scope, nothing is left outstanding.
- Decoupling `test_home_records_runner_discovery` from the live corpus: owned by approved plan `4v8s0m`.
  - Carrier: 4v8s0m
  - Carrier-Evidence: .aw/records/plans/executed/20261016-g9kupi-01-4v8s0m-decouple-test-home-records-runner-discovery-from-the-live-re.ipd.md
- Walker reverse-mapping and `tests/test_clean_target_recognition.py`: separate items.
  - Carrier: ki6t17, a48b4m

## Scope check

- Over-scope: none; no production code changes.
- Under-scope: none; of the two failures named by backlog 5mnbaz, F-02 is covered here by E-04/E-05 and F-01 is carried by `4v8s0m` (Deferred row 3).

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py` with zero failures, modulo the E-05 `4v8s0m` exception (V-05).
- `python3 -m pytest -o addopts="" -q tests/test_index_write_agent_records.py` still passes (V-05), proving the fbdxmh refusal contract is unchanged.
- Routine gate `python3 -m pytest` (V-05).

## Spec / documentation sync

N/A: test-only change; no behavior, CLI surface, or spec contract changes, and no user-facing docs describe these tests.

## Open questions

### OQ-01: Is the prompts index failure a production regression or fixture drift?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from repository evidence: fixture drift. The refusal is the intended fbdxmh behavior (`artifact_core.emit_index_missing_dir_refusal` docstring), it names the home-resolved `records/prompts` rather than the in-repo path (so kfnfji's routing fix holds), and both `aw install --records-backend home` and a pre-created home prompts dir make the index write land under `AW_HOME` (F-02).

### OQ-02: Freeze a fixture, repoint to `executed/`, or mark `livecorpus`?

- Blocking: no
- Status: resolved
- Owner: plan reviewer
- Resolution or deferral rationale: RESOLVED at review (PR-001): moot here. The same defect is already owned by the approved plan `4v8s0m` (Set g9kupi), whose review demonstrated a synthetic in-test fixture queues under `aw oc run start --prepare-only`; carrying a second, conflicting rewrite of the same test (a frozen kfnfji copy under `tests/fixtures/`) would make whichever plan runs second fail its own premise. The author's measurement that the renamed `5acca6ce5` text queues was reproduced at review but is no longer needed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the executing HEAD sha, the `ls .aw/records/plans/*/ | grep 4v8s0m` output, and the pre-change pytest output showing the prompts index failure (and, only if `4v8s0m` is unexecuted, the runner discovery `FileNotFoundError`) with their error lines.
  - Observed evidence: PASS. Pre-change measurement reproduced exactly the prompts index refusal; 4v8s0m is executed so runner discovery already passes.
    - Executing HEAD: `8f3c1c09800a863bb7510ba4c2198b39cba1e029`
    - `ls .aw/records/plans/*/ | grep 4v8s0m` -> `20261016-g9kupi-01-4v8s0m-decouple-test-home-records-runner-discovery-from-the-live-re.ipd.md` (in `executed/`), so runner discovery is expected to pass.
    - Pre-change `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py`:
      ```
      E       AssertionError: stdout:
      E         stderr: error: aw index prompts: records directory records/prompts does not exist; nothing was written.
      E         Run 'aw install .' at the project root to restore it.
      E       assert 2 == 0
      tests/test_records_root_accessor.py:216: AssertionError
      FAILED tests/test_records_root_accessor.py::test_home_records_reproduction_prompts_index
      1 failed, 17 passed in 12.78s
      ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `git diff` hunk for the prompts index test and the passing output of `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py -k "prompts_index and not refuses"`.
  - Observed evidence: PASS. Prompts index test pre-creates the home-resolved prompts dir and passes.
    - Diff hunk:
      ```
      @@ -205,8 +205,17 @@ def test_home_records_reproduction_history_sidecar(home_records_env):
       def test_home_records_reproduction_prompts_index(home_records_env):
      -    """aw index prompts must succeed and write under AW_HOME, not fail with FileNotFoundError."""
      +    """aw index prompts must succeed and write under AW_HOME, not fail with FileNotFoundError.
      +
      +    The home-backed prompts directory is pre-created first, exactly where the resolver
      +    places it (as `aw install` does), because index writes refuse on an absent records
      +    directory by design (plan fbdxmh). The refusal itself is pinned by
      +    test_home_records_prompts_index_refuses_absent_dir.
      +    """
           target, home, aw_home = home_records_env
      +    (project_context.project_records_dir(target, aw_home=aw_home) / "prompts").mkdir(
      +        parents=True
      +    )
      ```
    - `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py -k "prompts_index and not refuses"`:
      ```
      1 passed, 18 deselected in 1.50s
      ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the new test's diff; the full output of `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py tests/test_index_write_agent_records.py` with zero failures (or, only while `4v8s0m` is unexecuted, exactly the one runner-discovery `FileNotFoundError` failure, shown); the summary line of the routine gate `python3 -m pytest`; and `git diff --stat` showing only `tests/test_records_root_accessor.py` changed. Also paste the new test's observed refusal JSON line (produced by `prompts_index.run_index` -> `artifact_core.emit_index_missing_dir_refusal`).
  - Observed evidence: PASS. New refusal test passes; module and fbdxmh contract tests all pass; routine gate green; only the scoped test file changed.
    - New test `test_home_records_prompts_index_refuses_absent_dir` added (hunk `@@ -224,6 +233,38 @@`): runs `aw index prompts --dir <target> --agent` on the unmodified fixture and asserts exit 2, no `Traceback`, last stdout JSON `outcome == "cannot-run"`, a `records-dir-missing` diagnostic whose location does not start with `.aw/records/`, no `target/.aw/records`, and no `AW_HOME/projects/*/records/prompts`.
    - `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py tests/test_index_write_agent_records.py`:
      ```
      ......................................                                   [100%]
      38 passed in 42.84s
      ```
    - Routine gate `aw suite`: `745 passed in 65.34s (0:01:05)`
    - `git diff --stat`: ` tests/test_records_root_accessor.py | 43 ++++++++++++++++++++++++++++++++++++-` / ` 1 file changed, 42 insertions(+), 1 deletion(-)`
    - Observed refusal JSON (same invocation reproduced in a scratch home-backed repo): `{"schema":"aw.agent/v1","kind":"error","cmd":"index","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"applied":false,"target":"prompts","findings":1,"findings_by_severity":{"error":1,"warning":0,"info":0},"diagnostics":[{"location":"records/prompts","rule":"records-dir-missing"}],"next":"aw install ."}`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval (`- Status: approved`) before execution.

EXECUTION CONTRACT. Commit only the declared `- Scope-Paths:` through `aw commit 7hvkk0 -- <paths>` (never `git add -A`), never push, and paste actual runner output for every test claim. SCOPE FENCE: the declared scope is `tests/test_records_root_accessor.py` only; no production module under `agent_workflows/` is expected to change and `tests/test_records_root_accessor.py::test_home_records_runner_discovery` belongs to `4v8s0m`. Any out-of-scope edit is made and then justified at finalize (`--scope-reason`). All open questions are resolved.

RELEASE GATE. Backlog `5mnbaz` is `Work-Kind: bug` with `- Blocks-Release: next`; this plan inherits `- Blocks-Release: next` and carries `- From-Backlog: 5mnbaz`, so the gate is handed off and the item closes `done` only once this plan is executed.

POST-GATE LIFECYCLE. Do not mark this plan `executed` until `aw ipd lint --phase pre-transition` conforms and all three `V-*` items carry pasted evidence with `Result: pass`. Under `aw oc run` or `aw agy run` the runner owns begin/finalize; by hand, use `aw ipd finalize`, never a hand `git mv`.
