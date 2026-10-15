# IPD: Strip trailing hyphens after slug slice in hand-formatted backlog filenames

- Date: 2026-10-14
- Kind: child
- Concern: `aw backlog new` (and the deferred-question promotion path) can write a backlog filename whose slug ends in `-`, which `aw check backlog` immediately flags as `check.name-nonconformant`.
- Scope: Strip trailing hyphens after the fixed-length slug slice in the two hand-formatted backlog filename builders (`backlog.run_new`, `set_records.promote_question_to_backlog`), with behavioral regression tests. No other naming path changes.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/set_records.py, tests/test_slug_slice_trailing_hyphen.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: g73xcx
- Set: g73xcx
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: 1i2kgq

## Workflow history

- 2026-10-14 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored from backlog g73xcx; plan complete and lint-conforming.

## Goal

Make every backlog filename minted by the toolkit conform to the clustered grammar by stripping the trailing hyphen that a fixed-length slice of a kebab slug can leave, so a freshly created item never fails `aw check backlog`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Fix the two hand-formatted slug slices

- [ ] E-01 In `agent_workflows/backlog.py` `run_new`, change the slug expression `core.kebab(getattr(args, "slug", None) or item.summary or "item")[:50] or "item"` to strip hyphens after the slice (`[:50].strip("-") or "item"`), matching the existing idiom in `prompts.py` (`core.kebab(slug_arg)[:60].strip("-")`).
  - Depends on: none
  - Expected outcome: a summary whose kebab form has `-` at index 49 yields a slug with no trailing hyphen; all other slugs are unchanged.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/set_records.py` `promote_question_to_backlog`, change `(_core.kebab(summary or "question")[:50]) or "question"` to `_core.kebab(summary or "question")[:50].strip("-") or "question"`.
  - Depends on: none
  - Expected outcome: a promoted deferred question whose summary has `-` at kebab index 49 is written with a conformant filename instead of being refused or written nonconformant.
  - Execution state: pending

### Task group 2: Behavioral regression tests

- [ ] E-03 Add `tests/test_slug_slice_trailing_hyphen.py` with behavioral tests that (a) drive `backlog.run_new` in a temp repo with a summary engineered so its kebab form has a hyphen at index 49 (e.g. `"a" * 49 + " tail words"`), assert exit 0, assert the written filename does not match `-\.backlog\.md$`, and assert `backlog.run_check` on that repo returns 0; and (b) call `set_records.promote_question_to_backlog` with the same kind of summary and assert the returned `path.name` does not end in `-.backlog.md` and the file passes `backlog.validate_item` (no drift). Tests exercise the code; they do not read source.
  - Depends on: E-01, E-02
  - Expected outcome: both tests fail on the pre-fix code and pass after E-01/E-02.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `artifact_core.kebab` already strips leading/trailing hyphens, but only BEFORE any caller slice; a slice after kebab can reintroduce a trailing hyphen.
- `artifact_naming.build_clustered_name` re-applies `_core.kebab(slug)` to its slug argument, so callers that route through it (or `plans_refs.clustered_name`, which delegates to it) are already safe even with an unstripped slice.
- `prompts.py` uses the established idiom `core.kebab(slug_arg)[:60].strip("-")`.
- Existing backlog verb tests live in `tests/test_backlog.py` (`BacklogVerbTests`, helper `_new`/`_args`); a new focused test module is used to keep this change isolated.
- Suite is run bare: `python3 -m pytest`.

## Findings

| Site | Expression | Routes via `build_clustered_name`? | Affected |
|---|---|---|---|
| `backlog.run_new` (the item text calls it `cmd_new`) | `core.kebab(...)[:50] or "item"`, hand-formatted f-string filename | No | Yes |
| `set_records.promote_question_to_backlog` | `(_core.kebab(summary or "question")[:50]) or "question"`, hand-formatted `.format` filename | No | Yes |
| `specs.py` spec new | `core.kebab(slug_arg or title)[:60] or "spec"` | Yes (`_naming.build_clustered_name(..., slug=slug, ...)`) | No: re-kebab strips the hyphen |
| `ipd_authoring.py` scaffold | `_refs._core.kebab(title)[:60] or "ipd"` | Yes (`_refs.clustered_name`, delegating to `build_clustered_name`) | No |

Reproduced: `kebab("a"*49 + " b")[:50]` returns `'aaaa...a-'` (49 a's plus `-`).

## Proposed changes (ordered, validatable)

1. E-01: add `.strip("-")` after the slice in `backlog.run_new`.
2. E-02: add `.strip("-")` after the slice in `set_records.promote_question_to_backlog`.
3. E-03: add behavioral regression tests covering both paths.

## Deferred / out of scope (with reason)

- `specs.py` and `ipd_authoring.py` slices: verified safe because `build_clustered_name` re-kebabs the slug (see Findings); changing them is unnecessary churn. A defensive `.strip("-")` there is optional and not included.
- Replacing the hand-formatted backlog filenames with `build_clustered_name`: a larger refactor beyond the backlog item's ask.

## Scope check

- Over-scope: none.
- Under-scope: none; both affected sites named by the backlog item audit are covered, and the two unaffected sites are explained.

## Required tests / validation

- New `tests/test_slug_slice_trailing_hyphen.py` passes (V-03), and fails against the pre-fix code (demonstrated by running it before applying E-01/E-02, or by reverting temporarily).
- Full fast suite `python3 -m pytest` passes with no new failures.
- `aw ipd lint` conforms for this plan.

## Spec / documentation sync

N/A: the clustered naming grammar already forbids a trailing hyphen in the slug; this change makes the implementation conform to it. No spec or user-facing doc describes the slice.

## Open questions

### OQ-01: Should spec and IPD slug slices also gain `.strip("-")`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Both route through `artifact_naming.build_clustered_name`, which applies `_core.kebab(slug)` and strips trailing hyphens, so they cannot produce the defect.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git diff agent_workflows/backlog.py` showing `.strip("-")` applied after the `[:50]` slice in `run_new`, plus pasted output of the E-03 `run_new` test passing (that test drives `backlog.run_new` and `backlog.run_check`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `git diff agent_workflows/set_records.py` showing `.strip("-")` applied after the `[:50]` slice in `promote_question_to_backlog`, plus pasted output of the E-03 promotion test passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output for `tests/test_slug_slice_trailing_hyphen.py` failing on pre-fix code and passing after the fix, and pasted summary line of a bare `python3 -m pytest` run with no new failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Commit only the Scope-Paths files through `aw commit <plan> -- <paths>`; never push. After every V-item passes with pasted evidence and `aw ipd lint --phase pre-transition` conforms, transition the plan to `executed/` through the tooled lifecycle.
