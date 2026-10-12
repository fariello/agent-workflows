# IPD: Classify the two load-sensitive suite nodes and close the remaining test-all budget gap

- Date: 2026-10-12
- Kind: child
- Concern: Two suite nodes reported by backlog wc5c5e as failing under the parallel default run but passing alone need a recorded classification and, where one remains defective, a fix or a filed follow-up.
- Scope: Record the classification of both nodes against the current tree; give the remaining in-suite live-corpus node an explicit hang-guard budget; file the newly measured standing mypy-gate failure as its own release-gated bug rather than fixing it here.
- Scope-Paths: tests/test_verbose_flag_reach.py, .aw/records/backlog/open
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: wc5c5e
- Set: wc5c5e
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: z28jah

## Workflow history

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog wc5c5e with re-measured evidence; review-ready.

## Goal

Close backlog `wc5c5e` with a measured classification of both nodes: both have ALREADY been removed from the default fast suite since the item was filed (so the default gate no longer carries them), one remaining load-sensitivity gap in `make test-all` is closed with an explicit budget, and the one node that now fails for a real (non-load) reason is filed as its own bug so it is tracked instead of being misread as load noise.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Classification against the current tree

- [ ] E-01 Re-measure: run the bare default suite collection over the two files (`python3 -m pytest --collect-only -q tests/test_verbose_flag_reach.py tests/test_typecheck_gate.py`) and confirm both wc5c5e nodes are deselected by the default marker filter; record the output in V-01.
  - Depends on: none
  - Expected outcome: the collection output reports the two nodes as deselected (`2 tests were deselected by -m/-k`), proving the default gate every lane is judged against no longer contains either node.
  - Execution state: pending

### Task group 2: Close the test-all budget gap for the live-corpus node

- [ ] E-02 Add `@pytest.mark.timeout(300)` to `VerboseFlagReachTests.test_verbose_flag_end_to_end_observable_difference` in `tests/test_verbose_flag_reach.py`, directly beside its existing `@pytest.mark.livecorpus` marker, and extend the existing comment above it with one sentence stating the budget reason (the in-process live `.aw/records/` sweep's documented 27s-135s cost exceeds the conftest default 60s CPU arm under `make test-all` xdist contention).
  - Depends on: E-01
  - Expected outcome: the node carries an explicit budget matching its sibling `TypecheckGateTests.test_typecheck_gate_clean_exit` (`@pytest.mark.timeout(300)`), so under `-m ''` with `-n auto` it can no longer be killed by the per-test hang guard while still being guarded against a true hang.
  - Execution state: pending

- [ ] E-03 Run the node under the full-suite marker selection in parallel mode (`python3 -m pytest -m '' -n auto tests/test_verbose_flag_reach.py`) and confirm it passes.
  - Depends on: E-02
  - Expected outcome: `3 passed` (all three tests in the file, including the live-corpus node).
  - Execution state: pending

### Task group 3: File the standing typecheck failure separately

- [ ] E-04 First search for an existing item (`aw find backlog mypy` and `grep -rln "mypy agent_workflows" .aw/records/backlog/open`); if no open item already covers the mypy gate reporting errors, file one with `aw backlog new --summary "mypy gate (python -m mypy agent_workflows) reports errors at HEAD; tests.yml typecheck job and test_typecheck_gate_clean_exit fail" --work-kind bug --priority high --blocks-release next --slug mypy-gate-red` whose body pastes the measured `Found N errors in M files` line and the HEAD it was measured at. If an existing item covers it, cite its id6 in V-04 instead and file nothing.
  - Depends on: E-01
  - Expected outcome: exactly one open, release-gated (`- Blocks-Release: next`) `Work-Kind: bug` backlog item tracks the mypy gate failure, as required by AGENTS.md "Every live bug gates the next release".
  - Execution state: pending

## Project conventions discovered (Step 0)

- The default suite is `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'` (pyproject.toml `addopts`); `make test-all` runs `python3 -m pytest tests/ -m ''`, which re-includes `slow` and `livecorpus` nodes and is used by release-review (Makefile `test-all` target).
- Per-test hang guard: conftest.py `_DEFAULT_TEST_CPU_TIMEOUT = 60.0` and `_DEFAULT_TEST_WALL_TIMEOUT = 240.0`; `conftest._test_timeout_budgets` makes `@pytest.mark.timeout(seconds)` set the CPU budget and floor the wall ceiling at `max(default_wall, seconds)`. The backlog's "90.0s _DEFAULT_TEST_TIMEOUT" is stale: `_DEFAULT_TEST_TIMEOUT` is now an alias of the 60s CPU arm.
- `livecorpus` marker rationale is documented in pyproject.toml (`markers`: "livecorpus: asserts a property over EVERY artifact in this repository's own .aw/records/ tree ... Deselected by default ..."), which already serves as the repository documentation of option (c) for such nodes.
- AGENTS.md "Every live bug gates the next release": a live `Work-Kind: bug` item must carry `- Blocks-Release:`; the single `planned` release is `.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md`, so `next` resolves.
- No code-pinning tests (AGENTS.md execution contract): this plan adds a marker only and adds no test that reads source.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured in this worktree on 2026-10-12 (backlog measured at HEAD 4fbbc8386, 2026-10-02).

| Node | Change since filing (git) | Current default-suite status | Isolated result now | Classification |
|---|---|---|---|---|
| `tests/test_verbose_flag_reach.py::VerboseFlagReachTests::test_verbose_flag_end_to_end_observable_difference` | ffd2dc1be (2026-10-02) marked it `@pytest.mark.livecorpus`; b018130a5 (2026-10-07) added the fast synthetic twin `test_verbose_flag_synthetic_observable_difference` | deselected | passed, 14.92s call | (a) test defect: an in-process sweep of the live records tree whose cost scales with the corpus. Already moved out of the default gate with a synthetic twin; remaining gap is that it carries no explicit budget under `make test-all` (E-02). |
| `tests/test_typecheck_gate.py::TypecheckGateTests::test_typecheck_gate_clean_exit` | 7b75b6da1 (2026-10-03) added `@pytest.mark.timeout(300)`; b018130a5 marked `TypecheckGateTests` `@pytest.mark.slow` | deselected | FAILED, 17.56s call | Its load-sensitivity was a budget defect, already fixed by the 300s marker. It now fails for a DIFFERENT, standing reason: `python3 -m mypy agent_workflows` reports `Found 15 errors in 8 files (checked 193 source files)` (e.g. `agent_workflows/runner_shared.py ... Incompatible return value type (got "ScopeReconciliation", ...)`, several `Unsupported left operand type for + ("None")`). That is a real defect in the code under test (category b-adjacent: a type regression, not a concurrency bug) and is out of this chore's scope; filed separately (E-04). |

Measured commands and output (2026-10-12):

```
$ python3 -m pytest -o addopts="" -p no:cacheprovider -q -m "" --durations=0 <both nodes>
17.56s call     tests/test_typecheck_gate.py::TypecheckGateTests::test_typecheck_gate_clean_exit
14.92s call     tests/test_verbose_flag_reach.py::VerboseFlagReachTests::test_verbose_flag_end_to_end_observable_difference
FAILED tests/test_typecheck_gate.py::TypecheckGateTests::test_typecheck_gate_clean_exit
1 failed, 1 passed in 32.76s

$ python3 -m pytest --collect-only -q tests/test_verbose_flag_reach.py tests/test_typecheck_gate.py
tests/test_verbose_flag_reach.py: 3
NOTE: 2 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
```

Conclusion for wc5c5e's "what needs deciding": neither node is in the default gate any more, so the backlog's stated cost ("make the honest bar 'no newly failing test' rather than 'green'") no longer applies to these two nodes. The residual work is the test-all budget (E-02) and tracking the newly surfaced mypy failure (E-04).

## Proposed changes (ordered, validatable)

1. E-01: re-confirm deselection from the default suite (no edit).
2. E-02: add `@pytest.mark.timeout(300)` plus a one-sentence comment to the live-corpus verbose node in `tests/test_verbose_flag_reach.py`.
3. E-03: run that file with `-m '' -n auto` to show it passes with the budget.
4. E-04: file (or cite an existing) release-gated bug for the mypy gate failure under `.aw/records/backlog/open/`.

## Deferred / out of scope (with reason)

- Fixing the 15 mypy errors: a type regression across `cli.py`, `runner_shared.py`, `attention.py`, `research_refs.py`, `research_archive.py` and others is unrelated to test load-sensitivity and is far larger than this chore; it is tracked by the bug filed in E-04.
- Making the live-corpus sweep cheaper: the fast synthetic twin already covers the contract in the default suite (b018130a5), so optimizing the live sweep has no gate benefit.
- The three other failing nodes in the backlog text are already filed (6bolin, 8jeh4x, bxnhdj) and are not touched.

## Scope check

- Over-scope: none.
- Under-scope: none; both nodes named by wc5c5e are classified in Findings, and each residual defect has an E-item (E-02 budget, E-04 filing).

## Required tests / validation

- `python3 -m pytest --collect-only -q tests/test_verbose_flag_reach.py tests/test_typecheck_gate.py` shows both nodes deselected (V-01).
- `git diff -- tests/test_verbose_flag_reach.py` shows only the marker and comment addition (V-02).
- `python3 -m pytest -m '' -n auto tests/test_verbose_flag_reach.py` reports `3 passed` (V-03).
- `aw backlog check` conforms and the filed or cited item shows `- Work-Kind: bug` and `- Blocks-Release: next` (V-04).
- Bare `python3 -m pytest` shows no newly failing test relative to the pre-change baseline (regression, recorded under V-03).

## Spec / documentation sync

N/A: no spec governs per-test timeout markers; the `livecorpus`/`slow` marker documentation in pyproject.toml already describes the deselection, and the added code comment documents the budget at its point of use.

## Open questions

### OQ-01: Should this plan fix the mypy errors instead of filing them?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. The backlog item is a classification chore about load sensitivity; the mypy failure is a standing type regression unrelated to load, spanning eight production modules. AGENTS.md requires a live bug to carry its own `- Blocks-Release:` gate, which a separate backlog item provides; folding it into a `chore` plan would hide a release gate inside a non-gating work kind.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted actual output of `python3 -m pytest --collect-only -q tests/test_verbose_flag_reach.py tests/test_typecheck_gate.py` containing the line `2 tests were deselected`; a count other than 2 fails this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `git diff -- tests/test_verbose_flag_reach.py` showing `@pytest.mark.timeout(300)` added on `test_verbose_flag_end_to_end_observable_difference` beside `@pytest.mark.livecorpus`, plus the comment sentence, and no other hunk.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted actual runner output of `python3 -m pytest -m '' -n auto tests/test_verbose_flag_reach.py` ending in `3 passed`; plus the summary line of a bare `python3 -m pytest` run with any failing node listed and shown to also fail on the pre-change baseline.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the path of the filed (or pre-existing) backlog item and its pasted front matter showing `- Work-Kind: bug` and `- Blocks-Release: next`, its body containing a pasted `Found N errors in M files` mypy line, and pasted `aw backlog check` output reporting conformance.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Commit only the Scope-Paths through `aw commit z28jah -- <paths>`; never push. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above records `Result: pass` with pasted evidence.
