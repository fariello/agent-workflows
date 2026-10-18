# IPD: Replace the nonexistent tests/test_foo.py example citation in CONTRIBUTING.md and AGENTS.md

- Date: 2026-10-17
- Kind: child
- Concern: The suite-running instructions in CONTRIBUTING.md and in the repo-local section of AGENTS.md cite `python3 -m pytest tests/test_foo.py` as the example of an explicit-path run, but `tests/test_foo.py` does not exist, so a contributor or agent who copies the example gets a pytest "file or directory not found" error instead of the documented behavior.
- Scope: Replace the single `tests/test_foo.py` example in each of the two developer-facing documents with a real, existing test file (`tests/test_core_tier_selection.py`, the test module that exercises exactly the explicit-path behavior the sentence describes). No code, no tests, no other documents change.
- Scope-Paths: CONTRIBUTING.md, AGENTS.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: jiqna0
- Blocks-Release: next
- Set: jiqna0
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: mi6655
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001. Readiness go-pending-approval. Review record .aw/records/reviews/20261017-jiqna0-01-mi6655-replace-the-nonexistent-tests-test-foo-py-example-citation-i.review.md

- 2026-10-17 draft (opencode): created.
- 2026-10-17 to-review (opencode): authored from backlog jiqna0; body completed, ready for review.

## Goal

Make the explicit-path example in the two suite-running instructions copy-pasteable by citing a test file that actually exists, so following the documentation demonstrates the documented behavior (all non-slow tests in that path run, no core-marker deselection) instead of failing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Fix the two citations

- [x] E-01 In `CONTRIBUTING.md`, in the paragraph beginning "`make test` (or bare `python3 -m pytest`) runs the core test tier", replace `python3 -m pytest tests/test_foo.py` with `python3 -m pytest tests/test_core_tier_selection.py`. Change nothing else in the paragraph.
  - Depends on: none
  - Expected outcome: `CONTRIBUTING.md` no longer contains `tests/test_foo.py`; the sentence cites `tests/test_core_tier_selection.py`.
  - Execution state: performed
- [x] E-02 In `AGENTS.md`, in the repo-local "Repository development contract" section (BELOW the `<!-- /aw:block -->` marker), in the paragraph beginning "HOW TO RUN THE SUITE: run the routine gate BARE", replace `python3 -m pytest tests/test_foo.py` with `python3 -m pytest tests/test_core_tier_selection.py`. Do not touch any text inside the managed `<!-- aw:block -->` region.
  - Depends on: none
  - Expected outcome: `AGENTS.md` no longer contains `tests/test_foo.py`; the sentence cites `tests/test_core_tier_selection.py`; the managed block is byte-identical to before.
  - Execution state: performed

### Task group 2: Demonstrate the example now works

- [x] E-03 Run the corrected example command `python3 -m pytest tests/test_core_tier_selection.py` and the routine gate `python3 -m pytest`, capturing the summary lines.
  - Depends on: E-01, E-02
  - Expected outcome: the example command collects and runs tests (no "file or directory not found"), and the routine gate passes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- AGENTS.md is split into an installed managed block (`<!-- aw:block -->` ... `<!-- /aw:block -->`, rendered from `engine.py`) and repo-local sections below it. The `tests/test_foo.py` citation sits in the repo-local "Repository development contract" section, which carries the comment "THIS SECTION IS REPO-LOCAL AND MUST NOT BE INSTALLED INTO A MANAGED TARGET REPO", so editing it directly is correct and no `engine.py` template change is needed (`rg "non-slow in that path" agent_workflows` returns nothing).
- User-facing prose (CONTRIBUTING.md) must contain no em or en dashes; the edit replaces only a path token so introduces none.
- Commits go through `aw commit <plan> -- <paths>`; never push.
- `tests/test_foo.py` is a RECOGNIZED PLACEHOLDER in code-comment checks (`check_engine._SOURCE_TEST_CITATION_PLACEHOLDERS`, `tools/lost_guard_census.py`), which is why no checker flagged these citations; those placeholder sets are for docstring/comment illustrations in source and are correctly left alone. The defect is that user-run documentation presents it as a runnable command.
- The same placeholder in the `conftest.py` docstring of `pytest_collection_modifyitems` ("pytest tests/test_foo.py") is an illustrative code comment, not a runnable instruction, and is out of scope per the backlog item, which names only CONTRIBUTING.md and AGENTS.md.

## Findings

| Location | Text | Problem |
|---|---|---|
| `CONTRIBUTING.md`, paragraph starting "`make test` (or bare `python3 -m pytest`)" | `Running an explicit path (e.g. \`python3 -m pytest tests/test_foo.py\` or ...)` | `tests/test_foo.py` does not exist (`ls tests/test_foo.py` fails) |
| `AGENTS.md`, "Repository development contract", paragraph starting "HOW TO RUN THE SUITE" | same sentence | same |

Replacement choice: `tests/test_core_tier_selection.py` exists and its module docstring states it asserts "An explicit path invocation runs all non-slow tests (including non-core)", which is precisely the claim the sentence makes, so the example becomes self-demonstrating. No test reads either document's text for this sentence (`rg "non-slow in that path" tests` returns nothing), so no test changes.

## Proposed changes (ordered, validatable)

1. E-01: path-token replacement in `CONTRIBUTING.md`.
2. E-02: path-token replacement in the repo-local section of `AGENTS.md`.
3. E-03: run the corrected example and the routine gate.

## Deferred / out of scope (with reason)

- The `conftest.py` docstring and the `check_engine` / `lost_guard_census` placeholder sets: illustrative code comments and deliberate placeholder allowlists, not runnable user instructions; the backlog item names only the two documents.
  - Carrier-Declined: illustrative code comments and deliberate placeholder allowlists; out of scope per backlog item
- The executed plan `hguae9` that originally introduced the sentence: executed plans are immutable records.
  - Carrier-Declined: executed plans are immutable historical records; not modifiable

## Scope check

- Over-scope: none.
- Under-scope: none; `rg "test_foo" CONTRIBUTING.md AGENTS.md` shows exactly one occurrence in each file, both covered.

## Required tests / validation

- `rg -n "test_foo" CONTRIBUTING.md AGENTS.md` returns no matches (V-01, V-02).
- `git diff` of the two files shows only the path-token change; AGENTS.md managed block unchanged (V-01, V-02).
- `python3 -m pytest tests/test_core_tier_selection.py` runs and passes; bare `python3 -m pytest` passes (V-03).
- `aw sanitize --agent` reports no new finding in the touched files (V-03).

## Spec / documentation sync

The change is itself a documentation fix to CONTRIBUTING.md and AGENTS.md. No spec describes this sentence; N/A for specs. No CHANGELOG entry needed beyond what the maintainer's release flow collects for a doc typo fix.

## Open questions

### OQ-01: Which real file should replace the placeholder?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `tests/test_core_tier_selection.py`, because it exists and its docstring states it tests the very explicit-path behavior the sentence documents (see Findings).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted output of `rg -n "test_foo|test_core_tier_selection" CONTRIBUTING.md` showing zero `test_foo` matches and one `test_core_tier_selection` match, plus pasted `git diff -- CONTRIBUTING.md` showing a single-line change limited to the path token.
  - Observed evidence:
    ~~~
    $ rg -n "test_foo|test_core_tier_selection" CONTRIBUTING.md
    148:`make test` (or bare `python3 -m pytest`) runs the core test tier (budgeted under 30s wall time on 6 workers) that covers every first-party module and declared leaf command. The core tier is the runner merge gate. The budget is not enforced when the 1-minute load average exceeds the CPU count, and the budget banner prints the measured load. Running an explicit path (e.g. `python3 -m pytest tests/test_core_tier_selection.py` or `python3 -m pytest tests/`) runs everything non-slow in that path without marker deselection. Run `make test-all` or `aw suite --thorough` for the thorough tier (used before git push, in CI, and before release). Install the test dependencies with `pip install '.[test]'`.

    $ git diff -- CONTRIBUTING.md
    diff --git a/CONTRIBUTING.md b/CONTRIBUTING.md
    index 9cf84c384..5623c6b52 100644
    --- a/CONTRIBUTING.md
    +++ b/CONTRIBUTING.md
    @@ -145,7 +145,7 @@ layout migration, pypi_links) or the workflow tools (`scan_secrets.py`, `run_che
     make test
     ```

    -`make test` (or bare `python3 -m pytest`) runs the core test tier (budgeted under 30s wall time on 6 workers) that covers every first-party module and declared leaf command. The core tier is the runner merge gate. The budget is not enforced when the 1-minute load average exceeds the CPU count, and the budget banner prints the measured load. Running an explicit path (e.g. `python3 -m pytest tests/test_foo.py` or `python3 -m pytest tests/`) runs everything non-slow in that path without marker deselection. Run `make test-all` or `aw suite --thorough` for the thorough tier (used before git push, in CI, and before release). Install the test dependencies with `pip install '.[test]'`.
    +`make test` (or bare `python3 -m pytest`) runs the core test tier (budgeted under 30s wall time on 6 workers) that covers every first-party module and declared leaf command. The core tier is the runner merge gate. The budget is not enforced when the 1-minute load average exceeds the CPU count, and the budget banner prints the measured load. Running an explicit path (e.g. `python3 -m pytest tests/test_core_tier_selection.py` or `python3 -m pytest tests/`) runs everything non-slow in that path without marker deselection. Run `make test-all` or `aw suite --thorough` for the thorough tier (used before git push, in CI, and before release). Install the test dependencies with `pip install '.[test]'`.


     If you need the guaranteed no-dependency serial runner (for a minimal environment, or to
    ~~~
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted output of `rg -n "test_foo|test_core_tier_selection" AGENTS.md` showing zero `test_foo` matches and one `test_core_tier_selection` match located after the `<!-- /aw:block -->` line, plus pasted `git diff -- AGENTS.md` showing a single-line change limited to the path token.
  - Observed evidence:
    ~~~
    $ rg -n "test_foo|test_core_tier_selection" AGENTS.md
    304:HOW TO RUN THE SUITE: run the routine gate BARE, as `python3 -m pytest` (or `make test`). The root `conftest.py` hook selects the core test tier (budgeted under 30s wall time on 6 workers) that covers every first-party module and declared leaf command. The core tier is the runner merge gate. Running an explicit path (e.g. `python3 -m pytest tests/test_core_tier_selection.py` or `python3 -m pytest tests/`) runs everything non-slow in that path without marker deselection. Run `make test-all` or `aw suite --thorough` for the thorough tier (used before git push, in CI, and before release). `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. The xdist auto hook caps all runs at six workers and half the available CPUs. Do NOT pass another `-q`, which hides the `N passed` summary line this contract requires you to paste, or `-p no:randomly`, which disables order randomization. For per-test counts from a narrowed run, clear the defaults with `python3 -m pytest -o addopts=""`.

    $ git diff -- AGENTS.md
    diff --git a/AGENTS.md b/AGENTS.md
    index 54bb990d4..388fe80c0 100644
    --- a/AGENTS.md
    +++ b/AGENTS.md
    @@ -301,7 +301,7 @@ THIS SECTION IS REPO-LOCAL AND MUST NOT BE INSTALLED INTO A MANAGED TARGET REPO.
     deliberately BELOW the `<!-- /aw:block -->` marker, outside every managed block, because it contains
     developer rules and contracts specific to the agent-workflows repository itself.

    -HOW TO RUN THE SUITE: run the routine gate BARE, as `python3 -m pytest` (or `make test`). The root `conftest.py` hook selects the core test tier (budgeted under 30s wall time on 6 workers) that covers every first-party module and declared leaf command. The core tier is the runner merge gate. Running an explicit path (e.g. `python3 -m pytest tests/test_foo.py` or `python3 -m pytest tests/`) runs everything non-slow in that path without marker deselection. Run `make test-all` or `aw suite --thorough` for the thorough tier (used before git push, in CI, and before release). `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. The xdist auto hook caps all runs at six workers and half the available CPUs. Do NOT pass another `-q`, which hides the `N passed` summary line this contract requires you to paste, or `-p no:randomly`, which disables order randomization. For per-test counts from a narrowed run, clear the defaults with `python3 -m pytest -o addopts=""`.
    +HOW TO RUN THE SUITE: run the routine gate BARE, as `python3 -m pytest` (or `make test`). The root `conftest.py` hook selects the core test tier (budgeted under 30s wall time on 6 workers) that covers every first-party module and declared leaf command. The core tier is the runner merge gate. Running an explicit path (e.g. `python3 -m pytest tests/test_core_tier_selection.py` or `python3 -m pytest tests/`) runs everything non-slow in that path without marker deselection. Run `make test-all` or `aw suite --thorough` for the thorough tier (used before git push, in CI, and before release). `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. The xdist auto hook caps all runs at six workers and half the available CPUs. Do NOT pass another `-q`, which hides the `N passed` summary line this contract requires you to paste, or `-p no:randomly`, which disables order randomization. For per-test counts from a narrowed run, clear the defaults with `python3 -m pytest -o addopts=""`.

     ### Repository execution references
     - Release review and tags: Never create or push a git tag, a GitHub Release, or a registry/PyPI upload except inside release-review Section 9 after an explicit human GO (see `RELEASING.md`); no ad-hoc `git tag` or `git push --follow-tags`. See `CONTRIBUTING.md` and the .aw/records/plans README for detail.
    ~~~
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted pytest summary line from `python3 -m pytest tests/test_core_tier_selection.py` showing tests collected and passed (no "file or directory not found"), the pasted `N passed` summary line from bare `python3 -m pytest`, and pasted `aw sanitize --agent` result record.
  - Observed evidence:
    ~~~
    $ python3 -m pytest tests/test_core_tier_selection.py
    11 passed in 6.85s

    $ python3 -m pytest
    969 passed in 109.72s (0:01:49)

    $ aw sanitize --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5881,"findings":0,"evidence":["leak-scan"],"next":null}
    ~~~
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Open questions: OQ-01 is resolved; none remain. The executor follows the repository execution contract:

- Scope fence: `CONTRIBUTING.md` and `AGENTS.md` only (`- Scope-Paths:`). Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason`). Do not touch the managed `<!-- aw:block -->` region of `AGENTS.md`.
- Honesty (MUST): paste the ACTUAL runner output into each `V-*`; never claim a pass you did not run.
- Commit only the two files through `aw commit mi6655 -- CONTRIBUTING.md AGENTS.md`; never `git add -A`, never push.
- Lifecycle: the plan reaches `executed/` only through `aw ipd finalize` (never a hand `git mv`), and only after every `V-*` reads `pass` and `aw ipd lint --phase pre-transition` conforms. When run under `aw oc run` / `aw agy run`, the runner owns `aw ipd finalize`; the executor leaves the plan in `pending/` with evidence filled in. When executed by hand, the executor runs `aw ipd finalize mi6655 --actor <agent/model> --message <summary> --apply`.
