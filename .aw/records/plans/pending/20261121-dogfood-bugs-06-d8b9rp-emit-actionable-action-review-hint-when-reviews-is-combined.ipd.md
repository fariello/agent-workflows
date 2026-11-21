# IPD: Emit actionable --action review hint when reviews is combined with another selector

- Date: 2026-11-21
- Kind: child
- Concern: Invoking `aw agy run reviews <setid>` or `aw oc run reviews <setid>` treats `'reviews'` as a literal plan/Set selector and fails with the confusing message `No IPD plan, Set, or file matching 'reviews' found under .aw/records/plans/.` instead of guiding the operator to `--action review <setid>`.
- Scope: Enhance `agent_workflows/runner_shared.py::describe_unresolved_plan_selector` so unresolved tokens matching `REVIEW_SELECTOR_TOKENS` (`reviews`, `review`, `to-review`) or `all` produce an explicit actionable hint explaining standalone status selectors versus `--action review <set-or-id6>`, and add behavioral tests covering both `agy` and `oc` drivers.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_runner_reviews_selector_hint.py, .aw/records/plans/pending/20261121-dogfood-bugs-06-d8b9rp-emit-actionable-action-review-hint-when-reviews-is-combined.ipd.md
- Item-Dependencies: none
- Status: to-review
- Short-Description: Detect status selector tokens in multi-selector invocations and guide users to --action review
- Work-Kind: bug
- Priority: medium
- From-Backlog: bqqhdu
- Blocks-Release: next
- Set: dogfood-bugs
- Order: 6
- Highest E allocated: 02
- Author: antigravity
- Id: d8b9rp

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-21 to-review (aw set): Review-ready child plans for dogfood-bugs
- 2026-11-21 draft (antigravity): created.

## Goal

Give operators an immediate, actionable CLI error message pointing to `--action review <selector>` (or standalone `reviews`) whenever a review sweep token (`reviews`, `review`, `to-review`) or `all` is mistakenly combined with another positional selector in `aw agy run` or `aw oc run`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Actionable status-selector misuse diagnostic

- [ ] E-01 Update `agent_workflows/runner_shared.py::describe_unresolved_plan_selector` so that when `sel_str.lower()` is in `REVIEW_SELECTOR_TOKENS` (`reviews`, `review`, `to-review`), the returned message explains that `sel_str` is a standalone sweep selector (not a subcommand) and suggests `--action review <selector>` to review a specific Set or plan, or passing `reviews` alone to sweep every reviewable IPD. When `sel_str.lower() == "all"`, explain that `all` must be passed as the sole selector.
  - Depends on: none
  - Expected outcome: Calling `describe_unresolved_plan_selector("reviews", repo)` (and running `expand_selectors` in both `agy_runipd` and `oc_runipd` with `["reviews", "perf-opt"]`) raises a `DriverError` whose message clearly explains `reviews` is a standalone selector and recommends `--action review <selector>` (without claiming a plan/Set named `'reviews'` was missing).
  - Execution state: pending

### Task group 2: Behavioral tests

- [ ] E-02 Add behavioral tests in `tests/test_runner_reviews_selector_hint.py` verifying `describe_unresolved_plan_selector` and both `agy_runipd.expand_selectors` and `oc_runipd.expand_selectors` for `["reviews", "perf-opt"]`, `["review", "perf-opt"]`, `["to-review", "perf-opt"]`, `["all", "perf-opt"]`, and confirming normal single-selector `["reviews"]` sweep behavior is unchanged.
  - Depends on: E-01
  - Expected outcome: All new tests and existing `tests/test_runner_shared.py` pass with zero regressions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows/runner_shared.py::STATUS_SELECTOR_TOKENS` (`{"reviews", "review", "to-review", "all"}`) and `REVIEW_SELECTOR_TOKENS` (`{"reviews", "review", "to-review"}`) are the single shared source of truth used by `is_status_selector` (which requires `len(tokens) == 1`).
- Both `agy_runipd` and `oc_runipd` delegate unresolved selector diagnostics to `runner_shared.describe_unresolved_plan_selector`, so fixing `runner_shared.describe_unresolved_plan_selector` fixes both host runners simultaneously with zero host drift.

## Findings

| ID | Severity | Area | Finding |
|---|---|---|---|
| DF-06 | Medium | `agent_workflows/runner_shared.py::describe_unresolved_plan_selector` | Observed on `polyopen`: running `aw agy run reviews perf-opt` printed `runagy: No IPD plan, Set, or file matching 'reviews' found under .aw/records/plans/.` with no hint that `reviews` is standalone or that `--action review perf-opt` is the right command. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/runner_shared.py::describe_unresolved_plan_selector` (`E-01`): Check `sel_str.lower() in REVIEW_SELECTOR_TOKENS` and `sel_str.lower() == "all"` before the generic `"No IPD plan, Set, or file matching..."` fallback and return an actionable hint naming `--action review <selector>` or standalone `reviews` / `all`.
2. `tests/test_runner_reviews_selector_hint.py` (`E-02`): Add behavioral tests covering `describe_unresolved_plan_selector` and both host drivers' `expand_selectors`.

## Deferred / out of scope (with reason)

- Changing the CLI grammar to accept `reviews <setid>` as a positional modifier is intentionally out of scope because `--action review <selector>` is already the documented contract in spec `25kzda` and `aw agy run --help`.
  - Carrier-Declined: Existing CLI contract already provides `--action review <selector>`; improving the error message resolves the confusion without adding ambiguous positional grammar.

## Scope check

- Over-scope: none. Only `agent_workflows/runner_shared.py` and the new test file are modified.
- Under-scope: none. Both `agy_runipd` and `oc_runipd` share `describe_unresolved_plan_selector`.

## Required tests / validation

- Run `python3 -m pytest tests/test_runner_reviews_selector_hint.py tests/test_runner_shared.py`.
- Run `make typecheck` and `aw sanitize --agent`.

## Spec / documentation sync

N/A with reason: `--action review` and standalone `reviews` are already documented in `aw agy run --help` and `aw oc run --help`.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition) (as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction) name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Paste `git diff -- agent_workflows/runner_shared.py` showing the `REVIEW_SELECTOR_TOKENS` and `"all"` diagnostic branch in `describe_unresolved_plan_selector`, plus pasted output of `python3 -m pytest tests/test_runner_reviews_selector_hint.py` confirming `--action review` appears in the error for both hosts.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste full output of `python3 -m pytest tests/test_runner_reviews_selector_hint.py tests/test_runner_shared.py`, `make typecheck`, and `aw sanitize --agent` showing all tests pass, 0 mypy errors, and 0 leak findings.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan must reach `approved` before execution. Execute inside an isolated worktree, commit only `Scope-Paths` files via `aw commit d8b9rp -- <paths>`, paste actual command output into each `V-*` Observed evidence block, and finalize via `aw ipd finalize d8b9rp`.
