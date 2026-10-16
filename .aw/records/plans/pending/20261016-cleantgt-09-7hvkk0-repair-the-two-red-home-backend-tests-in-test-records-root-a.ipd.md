# IPD: Repair the two red home-backend tests in test_records_root_accessor

- Date: 2026-10-16
- Kind: child
- Concern: `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py` reports `2 failed, 16 passed` at HEAD `f0ac1c64c`. `test_home_records_runner_discovery` reads its plan fixture from the LIVE corpus path `.aw/records/plans/pending/20261015-cleantgt-01-kfnfji-...ipd.md`, which no longer exists because kfnfji moved to `executed/`. `test_home_records_reproduction_prompts_index` expects `aw index prompts` to create the home-backed prompts directory, but plan fbdxmh (commit `8bad89081`) deliberately made every index write REFUSE (exit 2, `cannot-run`) when the resolved records directory is absent, and the `home_records_env` fixture never materializes that directory the way `aw install` does. Both are test defects: production behavior is correct in both cases (measured, see Findings).
- Scope: IN: (1) decouple `test_home_records_runner_discovery` from the live `.aw/records/` corpus by reading a frozen, self-contained plan fixture under `tests/fixtures/` that carries its own id6 and Set, so no lifecycle move in this repository can turn it red; (2) make `test_home_records_reproduction_prompts_index` materialize the home-backed `records/prompts` directory (as `aw install` does) before asserting the write lands under `AW_HOME`, and add a sibling test pinning the fbdxmh refusal for the absent-directory case on a home-backed project (exit 2, nothing created in the target or under `AW_HOME`, no traceback). OUT: any change to `agent_workflows/` (production behavior is correct); the `home_records_env` fixture shape used by the other tests in the module; ki6t17's walkers.
- Scope-Paths: tests/test_records_root_accessor.py, tests/fixtures/home_records_runner_plan.md
- Item-Dependencies: executed:kfnfji, executed:fbdxmh
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 5mnbaz
- Blocks-Release: next
- Set: cleantgt
- Order: 9
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7hvkk0

## Workflow history

- 2026-10-16 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-16 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog 5mnbaz at HEAD f0ac1c64c; both failures reproduced and root-caused by measurement.

## Goal

Return `tests/test_records_root_accessor.py` to green without weakening what it proves: the home-records runner discovery test must keep proving `aw show` and `aw oc run start --prepare-only` find a plan stored under `AW_HOME`, and the prompts index test must keep proving the write lands under `AW_HOME` and never in the target, while also pinning the fbdxmh refusal it currently contradicts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure

- [ ] E-01 Re-measure both failures at the executing HEAD before changing anything.
  - Depends on: none
  - Expected outcome: pasted output of `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py` showing exactly `test_home_records_runner_discovery` (FileNotFoundError on the `plans/pending/...kfnfji...` path) and `test_home_records_reproduction_prompts_index` (exit 2, `records directory records/prompts does not exist; nothing was written.`) failing. If either already passes, or a different test fails, stop and record the divergence in this plan before continuing.
  - Execution state: pending

### Task group 2: runner discovery fixture

- [ ] E-02 Create `tests/fixtures/home_records_runner_plan.md`: a frozen copy of the kfnfji plan as it stood when it was approved and runnable (`git show 5acca6ce5:.aw/records/plans/pending/20261015-cleantgt-01-kfnfji-route-every-records-reader-and-writer-through-one-records-ro.ipd.md`), with every occurrence of the id6 `kfnfji` replaced by `hrrun1` and every occurrence of the Set id `cleantgt` replaced by `hrfix`, and nothing else changed. Before writing it, confirm `hrrun1` and `hrfix` occur nowhere in `.aw/records/`, `agent_workflows/`, or `tests/` (`grep -rl` returns nothing). Use the `.md` suffix (not `.ipd.md`) so no plan scanner mistakes the fixture for a live plan.
  - Depends on: E-01
  - Expected outcome: the fixture exists, `grep -c kfnfji tests/fixtures/home_records_runner_plan.md` prints `0`, and `grep -c cleantgt` prints `0`.
  - Execution state: pending

- [ ] E-03 In `tests/test_records_root_accessor.py` `test_home_records_runner_discovery`, read the plan text from `REPO_ROOT / "tests" / "fixtures" / "home_records_runner_plan.md"` instead of the live `.aw/records/plans/pending/` path, write it under the external `plans/pending/` as `20261015-hrfix-01-hrrun1-route-every-records-reader-and-writer-through-one-records-ro.ipd.md`, and update the selector and every assertion string (`aw show hrrun1`, `aw oc run start --prepare-only hrrun1`, `"20261015-hrfix-01-hrrun1"`, `"Run order (1 item(s)): 01 hrrun1"`, `"hrfix 01 hrrun1"`). Keep every other step and assertion of the test unchanged.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py -k runner_discovery` passes and the LIVE-CORPUS NOTE no longer appears for it.
  - Execution state: pending

### Task group 3: prompts index test

- [ ] E-04 In `test_home_records_reproduction_prompts_index`, before running `aw index prompts`, create the home-backed prompts directory exactly where the resolver places it: `(project_context.project_records_dir(target, aw_home=aw_home) / "prompts").mkdir(parents=True)` (this mirrors `engine._records_member_destination`, through which `aw install` creates the records tree). Keep the existing assertions (exit 0, no `target/.aw/records/prompts`, exactly one `*/records/prompts/INDEX.json` under `AW_HOME/projects`). Update the docstring to say the directory is pre-created because index writes refuse on an absent directory (fbdxmh).
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py -k prompts_index` passes.
  - Execution state: pending

- [ ] E-05 Add `test_home_records_prompts_index_refuses_absent_dir(home_records_env)`: on the unmodified fixture (no prompts directory anywhere), run `aw index prompts --dir <target> --agent` and assert exit `2`, no `Traceback` in stderr, the last stdout line parses as JSON with `outcome == "cannot-run"` and a `records-dir-missing` diagnostic whose location does NOT start with `.aw/records/` (proving it names the home-resolved directory, not an in-repo one), and afterwards neither `target/.aw/records` nor any `AW_HOME/projects/*/records/prompts` exists.
  - Depends on: E-04
  - Expected outcome: the new test passes, and the whole module reports `19 passed` (or the measured count, which must show zero failures).
  - Execution state: pending

## Project conventions discovered (Step 0)

- The routine gate is `python3 -m pytest` (pyproject `addopts` supplies `-q -n auto ... -m 'not slow and not livecorpus'`); `tests/test_records_root_accessor.py` is not in `testpaths`, so it is run explicitly with `-o addopts=""`.
- `pyproject.toml` defines the `livecorpus` marker for tests that assert a property over the whole live `.aw/records/` tree. `test_home_records_runner_discovery` does NOT assert a corpus property; it only borrowed one plan as sample data, so the right fix is a frozen fixture, not the marker.
- Existing frozen plan fixtures live in `tests/fixtures/` (e.g. `tests/fixtures/conforming-orchestrator.md`, loaded via `tests/support.CONFORMING_ORCHESTRATOR`) with a fixture-only id6.
- Index writes refuse on an absent directory by design: `artifact_core.emit_index_missing_dir_refusal`, called from `prompts_index.run_index` under `if not prompts_dir.is_dir():` (plan fbdxmh, executed). Its docstring states the reason: a mkdir would write under `$HOME/.aw/projects/` for a home-backend resolution and shadow a later in-repo tree.
- `aw install` creates the home records tree through `engine._records_member_destination`, which maps `.aw/records/<tail>` onto `project_context.project_records_dir(repo_root) / tail`.
- Tests must exercise behavior through subprocess CLI calls and assert on outputs, exit codes, and side effects (AGENTS.md, no code-pinning).

## Findings

| ID | Severity | Location | Finding |
|---|---|---|---|
| F-01 | medium | `tests/test_records_root_accessor.py` `test_home_records_runner_discovery` | Reads `REPO_ROOT/.aw/records/plans/pending/20261015-cleantgt-01-kfnfji-...ipd.md`; kfnfji is now in `.aw/records/plans/executed/` (measured with `ls .aw/records/plans/*/`), so `read_text` raises FileNotFoundError. Merely repointing to `executed/` is not enough: measured, a copy of the executed plan (Status `executed`) is not queueable, and a hand-flipped `approved` copy is refused by `aw oc run start --prepare-only` (`IPD-M104` Approval required). The plan text at commit `5acca6ce5` (Status `approved`, real Approval and review history) DOES queue: measured in a home-backed temp repo with ids renamed to `hrrun1`/`hrfix`, `aw show hrrun1` exit 0 and prepare-only exit 0 printing `Run order (1 item(s)): 01 hrrun1` and a row containing `hrfix 01 hrrun1`. |
| F-02 | medium | `tests/test_records_root_accessor.py` `test_home_records_reproduction_prompts_index`, `home_records_env` | The fixture writes only `.aw/config/project.json` (`records_backend: home`) and never creates the home records tree. Since fbdxmh, `aw index prompts` refuses (exit 2) instead of creating it. Measured: the refusal names `records/prompts` (home-resolved, NOT `.aw/records/prompts`), so the kfnfji regression (writing to / crashing on the in-repo path) is NOT back. Measured: after `aw install . -y --no-interactive --preset private-target --records-backend home` the home tree includes `records/prompts` and `aw index prompts` exits 0; and with only `project_records_dir(target, aw_home) / "prompts"` pre-created, the index writes exactly `awh/projects/<id>/records/prompts/INDEX.json`. Conclusion for the backlog's "determine which": the fixture no longer creates the directory; production is correct. |

## Proposed changes (ordered, validatable)

1. Freeze the runnable kfnfji plan text as `tests/fixtures/home_records_runner_plan.md` with fixture-only ids (E-02).
2. Point `test_home_records_runner_discovery` at the fixture and the renamed ids (E-03).
3. Pre-create the home-resolved prompts dir in the prompts index test (E-04).
4. Pin the fbdxmh refusal on a home-backed project in a new test (E-05).

## Deferred / out of scope (with reason)

- Changing `aw index` to create a missing home records directory: rejected, it reverses the deliberate fbdxmh decision (OQ-01 there, resolved from evidence).
- Changing `home_records_env` to run a full `aw install`: rejected, it would change the setup of seven other passing tests and slow the module; only the one test needs the directory.
- Walker reverse-mapping (ki6t17) and `tests/test_clean_target_recognition.py` (a48b4m): separate items.

## Scope check

- Over-scope: none; no production code changes.
- Under-scope: none; both failures named by the backlog item are covered (F-01 by E-02/E-03, F-02 by E-04/E-05).

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py` with zero failures (V-03, V-05).
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
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from measurement: freeze a fixture. Repointing to `executed/` fails because an executed plan is not queueable (F-01), and would break again on archive moves; `livecorpus` is for whole-corpus property tests (pyproject marker text), which this is not. A frozen fixture with fixture-only ids is the established pattern (`tests/fixtures/conforming-orchestrator.md`) and was measured to queue.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the executing HEAD sha and the pre-change pytest output showing exactly the two named failures with their error lines.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the empty `grep -rl "hrrun1\|hrfix" .aw/records agent_workflows tests` output taken BEFORE the fixture was written, then `grep -c kfnfji tests/fixtures/home_records_runner_plan.md` and `grep -c cleantgt tests/fixtures/home_records_runner_plan.md` both printing `0`, and the fixture's `- Id:` and `- Status:` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff tests/test_records_root_accessor.py` for the runner-discovery test and the passing output of `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py -k runner_discovery` with no LIVE-CORPUS NOTE (the observation is produced by the test's own `aw show` and `aw oc run start --prepare-only` subprocess calls).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `git diff` hunk for the prompts index test and the passing output of `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py -k "prompts_index and not refuses"`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new test's diff; the full output of `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py tests/test_index_write_agent_records.py` with zero failures; and the summary line of the routine gate `python3 -m pytest`; and `git diff --stat` showing only the two Scope-Paths changed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval (`- Status: approved`) before execution.

EXECUTION CONTRACT. Commit only the declared `- Scope-Paths:` through `aw commit 7hvkk0 -- <paths>` (never `git add -A`), never push, and paste actual runner output for every test claim. No production module under `agent_workflows/` may change; if one seems to need changing, stop and record why.

RELEASE GATE. Backlog `5mnbaz` is `Work-Kind: bug` with `- Blocks-Release: next`; this plan inherits `- Blocks-Release: next` and carries `- From-Backlog: 5mnbaz`, so the gate is handed off and the item closes `done` only once this plan is executed.

POST-GATE LIFECYCLE. Do not mark this plan `executed` until `aw ipd lint --phase pre-transition` conforms and all five `V-*` items carry pasted evidence with `Result: pass`. Under `aw oc run` or `aw agy run` the runner owns begin/finalize; by hand, use `aw ipd finalize`, never a hand `git mv`.
