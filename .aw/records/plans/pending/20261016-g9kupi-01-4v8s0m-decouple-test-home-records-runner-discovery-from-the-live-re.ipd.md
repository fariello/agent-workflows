# IPD: Decouple test_home_records_runner_discovery from the live records corpus

- Date: 2026-10-16
- Kind: child
- Concern: `tests/test_records_root_accessor.py::test_home_records_runner_discovery` reads a hardcoded live-corpus path (`.aw/records/plans/pending/20261015-cleantgt-01-kfnfji-...ipd.md`) that no longer exists because plan `kfnfji` was executed and moved to `.aw/records/plans/executed/`, so the test fails with `FileNotFoundError` on every run.
- Scope: Replace the live-corpus read in that one test with a self-contained synthetic fixture plan written by the test itself, preserving every behavioral assertion (home-backend `aw show` and `aw oc run start --prepare-only` discovery). No production code changes.
- Scope-Paths: tests/test_records_root_accessor.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: g9kupi
- Blocks-Release: next
- Set: g9kupi
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: 4v8s0m

## Workflow history

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored from backlog g9kupi; failure reproduced in lane before authoring.

## Goal

Make `test_home_records_runner_discovery` pass again and stay passing regardless of where any real plan lives in this repository's `.aw/records/` tree, by having the test author its own conforming fixture plan inside the isolated home-records directory instead of copying a live artifact.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Self-contained fixture

- [ ] E-01 In `tests/test_records_root_accessor.py::test_home_records_runner_discovery`, remove the `REPO_ROOT / ".aw/records/plans/pending/20261015-cleantgt-01-kfnfji-..."` read and instead write a synthetic, minimal, runner-eligible plan into `pending_dir` (inline text constant or a small helper in the same module), using a fixture-only Set id and id6 (for example Set `fixtset`, Order 01, a fixed 6-char id6 that is not a live repo id6) and a filename following `YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md`. The plan text must carry whatever status and metadata `aw oc run start --prepare-only` requires to queue it (determine the minimum by driving the command, not by reading runner source into the test); the executed-state copy of `kfnfji` is NOT reusable because its `- Status: executed` makes it ineligible for queueing.
  - Depends on: none
  - Expected outcome: the test no longer references any path under `REPO_ROOT / ".aw/records"` and no longer mentions `kfnfji`/`cleantgt` except in the module docstring provenance line.
  - Execution state: pending
- [ ] E-02 Update the assertions in the same test to the fixture identity: `aw show <fixture-id6>` returns 0 and its stdout contains the fixture filename stem prefix; `aw oc run start --prepare-only <fixture-id6>` returns 0 and its stdout contains `Run order (1 item(s)): 01 <fixture-id6>` and `<fixture-set> 01 <fixture-id6>`. Keep the assertion strength identical to the original (same two commands, same returncode and stdout checks).
  - Depends on: E-01
  - Expected outcome: assertions exercise the home-records backend discovery path exactly as before, against the fixture.
  - Execution state: pending
- [ ] E-03 Run the module and the routine gate and confirm no regression.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest tests/test_records_root_accessor.py -o addopts="" -q` reports all tests passed; bare `python3 -m pytest` shows no new failures attributable to this change.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Tests must exercise behavior via subprocess/CLI and assert on outputs and exit codes; no code-pinning (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"). The fix keeps the existing `run_aw` subprocess helper in the same module.
- Tests should not depend on the live `.aw/records/` corpus unless marked `livecorpus` (pytest's own note emitted on this failure: "If this test genuinely asserts a whole-corpus property ... mark it with @pytest.mark.livecorpus"). This test asserts no corpus property, so the correct fix is decoupling, not marking.
- Plan filenames follow `YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md` (AGENTS.md "Agent plans").
- Routine gate: bare `python3 -m pytest`; narrowed per-test runs with `-o addopts=""` (AGENTS.md "Repository development contract").

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | The test reads `REPO_ROOT / ".aw/records/plans/pending/20261015-cleantgt-01-kfnfji-route-every-records-reader-and-writer-through-one-records-ro.ipd.md"`. | `tests/test_records_root_accessor.py::test_home_records_runner_discovery`, the `real_plan = (...).read_text(...)` statement. |
| F-2 | That file now lives only under `executed/`. | `ls .aw/records/plans/*/*kfnfji*` -> `.aw/records/plans/executed/20261015-cleantgt-01-kfnfji-route-every-records-reader-and-writer-through-one-records-ro.ipd.md` |
| F-3 | The test fails deterministically. | `python3 -m pytest tests/test_records_root_accessor.py -o addopts="" -q -k runner_discovery` -> `FileNotFoundError: [Errno 2] No such file or directory: '.../.aw/records/plans/pending/20261015-cleantgt-01-kfnfji-...ipd.md'`, `1 failed, 17 deselected`. |
| F-4 | Simply repointing at `executed/` is wrong: the copy carries `- Status: executed`, so it would not be queued by `--prepare-only`, and it would re-break the next time records are archived/sharded. | Lifecycle described in AGENTS.md "Agent plans" and `aw archive plans` weekly-sharding of terminal plans. |

## Proposed changes (ordered, validatable)

1. E-01: synthetic fixture plan authored by the test into the home-records `plans/pending/` dir.
2. E-02: assertions retargeted to the fixture id6/Set.
3. E-03: run module and routine gate.

## Deferred / out of scope (with reason)

- Auditing other tests for similar live-corpus path reads: not requested by `g9kupi`; file a separate backlog item if found during execution.
- Any production code change: the failure is purely test-side.

## Scope check

- Over-scope: none.
- Under-scope: none; the single failing test is the entire reported defect.

## Required tests / validation

- `python3 -m pytest tests/test_records_root_accessor.py -o addopts="" -q` passes in full (V-01, V-02, V-03).
- Bare `python3 -m pytest` shows no new failures (V-03).

## Spec / documentation sync

N/A: test-only fix; no spec or user-facing doc describes this test's fixture.

## Open questions

### OQ-01: Minimum plan metadata required by `--prepare-only`

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: Determined empirically during E-01 by driving `aw oc run start --prepare-only` against the fixture; `aw ipd scaffold` output plus `- Status: approved` and concrete Scope-Paths/Item-Dependencies is the expected starting point, since the runner queues approved plans (AGENTS.md "SO: to answer 'what can I run unattended?', report the plans whose `- Status:` is `approved`").

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `grep -n "REPO_ROOT / \".aw/records\|kfnfji\|cleantgt" tests/test_records_root_accessor.py` showing no live-corpus path read remains (only the docstring provenance line may match), plus the diff hunk of the new fixture.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted output of `python3 -m pytest tests/test_records_root_accessor.py -o addopts="" -q -k runner_discovery` showing `1 passed`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted summary lines of `python3 -m pytest tests/test_records_root_accessor.py -o addopts="" -q` (all passed) and of bare `python3 -m pytest` (the `N passed` line, with any failures shown to be pre-existing and unrelated).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Commit only `tests/test_records_root_accessor.py` and this plan through `aw commit <plan> -- <paths>`; never push. Move to `.aw/records/plans/executed/` via the tooled lifecycle only after `aw ipd lint --phase pre-transition` conforms and every V-* item records pasted passing evidence.
