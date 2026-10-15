# IPD: Restore behavioral coverage of parse_plan_file and front-matter readers loose leading whitespace tolerance

- Date: 2026-10-14
- Kind: child
- Concern: Commit `19313eed` deleted `tests/test_runner_refork_guard.py`, and with it `FrontMatterReaderBehaviorTests` (`test_public_readers_tolerate_loose_leading_whitespace`, `test_both_runners_still_accept_every_spelling_they_did_before`, `test_selector_internal_readers_stay_strict`, `test_public_status_reader_keeps_the_single_token_contract`), the only behavioral tests that the runners' plan parser `runner_shared.parse_plan_file` (bound to the PERMISSIVE public readers `selectors.read_front_matter_id` / `read_front_matter_status`) tolerates any whitespace after the leading `-`, while `selectors`' strict internal readers (the `aw find` matching contract) do not. Executed plan `yuhl6o` recorded that site as S-06 RETIRE-UNGUARDED. A regression is silent: if `parse_plan_file` were swapped to the strict readers, a plan spelled `-  Status: approved` or `-\tStatus: approved` would lose its declared status and degrade to the directory bucket (`pending`), so an approved plan would silently stop being selected for execution.
- Scope: Add one new behavioral test module that drives the real `parse_plan_file` on both hosts against real temporary plan files, and the public and internal `selectors` readers on text, then repoint the one `runner_shared.parse_plan_file` docstring sentence that says "no live guard currently asserts this loose-whitespace tolerance". No production behavior change.
- Scope-Paths: tests/test_front_matter_loose_whitespace.py, agent_workflows/runner_shared.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: qmpvcy
- Set: qmpvcy
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: lcjlc3

## Workflow history

- 2026-10-15 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored from backlog `qmpvcy`; review-ready.

## Goal

Restore behavioral (never source-reading, P16) test coverage that `parse_plan_file`, on both hosts, and the public `selectors.read_front_matter_*` readers accept `- `, `-  ` and `-\t` front-matter spellings, while the strict internal `selectors._read_id` / `_read_status` reject the loose spellings and the single-token status contract is preserved, so the tolerance is proven present and bounded.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: parse_plan_file tolerates loose leading whitespace (yuhl6o S-06)

- [ ] E-01 Create `tests/test_front_matter_loose_whitespace.py` with a test that, for each spelling prefix in (`"- "`, `"-  "`, `"-\t"`) and each host in (`oc_runipd`, `agy_runipd`), writes a real plan file under a temporary `<tmp>/.aw/records/plans/pending/plan.md` whose metadata lines are `<prefix>Id: abc123`, `<prefix>Status: approved`, `<prefix>Kind: child` followed by a `## Goal` heading, calls `host.parse_plan_file(path, tmp)` and asserts the returned record has `id6 == "abc123"`, `status == "approved"` (NOT the directory bucket `pending`), and `kind == "child"`. Use `subTest(host=..., spelling=...)`.
  - Depends on: none
  - Expected outcome: New module exists; the test passes for all six host x spelling subtests.
  - Execution state: pending

### Task group 2: the public readers are permissive and the internal readers stay strict

- [ ] E-02 In the same module, add a test that `selectors.read_front_matter_id` and `selectors.read_front_matter_status` return `"abc123"` / `"approved"` for all three spellings, and a test that the strict internal `selectors._read_id` / `selectors._read_status` return the values for the one-space spelling and `None` for the two-space and tab spellings (the `aw find` contract is not widened). Assert on returned values only; do not assert on regex `.pattern` strings.
  - Depends on: E-01
  - Expected outcome: Both tests pass.
  - Execution state: pending

- [ ] E-03 In the same module, add a test that the single-token status contract survives: `selectors.read_front_matter_status` and `selectors._read_status` return `None` for `- Status: EXECUTED (approved by maintainer)`, and `runner_shared.parse_plan_file` on a real file under `.../plans/pending/` carrying only that status line returns `status == "pending"` (the directory fallback). Do not read source files, use `ast`/`inspect`, or pin symbol identity or counts.
  - Depends on: E-02
  - Expected outcome: Test passes.
  - Execution state: pending

### Task group 3: comment repointing

- [ ] E-04 Repoint the `runner_shared.parse_plan_file` docstring paragraph beginning "THE ALIASES ARE THE PERMISSIVE PUBLIC READERS" that cites `tests/test_runner_refork_guard.py::FrontMatterReaderBehaviorTests` and says "no live guard currently asserts this loose-whitespace tolerance", so it names `tests/test_front_matter_loose_whitespace.py` as the live guard. Docstring-only edit.
  - Depends on: E-03
  - Expected outcome: `rg -n "no live guard currently asserts this loose-whitespace" agent_workflows/` returns no matches; no code change.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Tests must exercise behavior (P16, AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): no source reading, no `ast`/`inspect`, no symbol censuses, no regex-pattern string pins (the deleted `test_selector_internal_readers_stay_strict` asserted `_ID_RE.pattern`; that half is NOT restored).
- `runner_shared.parse_plan_file` imports `selectors.read_front_matter_id as _read_id` and `read_front_matter_status as _read_status` function-locally; when no status is read it falls back to `plan_bucket(path)`. Both hosts re-export it (`oc_runipd.parse_plan_file`, `agy_runipd.parse_plan_file`).
- Public readers use `_FRONT_MATTER_ID_RE = (?m)^-\s*Id:...` and `_FRONT_MATTER_STATUS_RE = (?m)^-\s*Status:\s*(\S+)\s*$`; internal `_ID_RE` / `_STATUS_RE` require `^- Id:` / `^- Status:` exactly.
- Measured in this lane (AW_NO_REEXEC=1, temporary repo): for prefixes `"- "`, `"-  "`, `"-\t"`, `parse_plan_file` on `runner_shared`, `oc_runipd` and `agy_runipd` all returned `('abc123', 'approved', 'child')`; `selectors._read_id` / `_read_status` returned `abc123 approved` for one space and `None None` for two-space and tab; `plan_bucket` returned `pending`; a file with `- Status: EXECUTED (approved)` parsed to status `pending`. So a strict-reader swap would observably flip `approved` to `pending`, which makes E-01 non-vacuous.
- Existing partial coverage: `tests/test_runner_shared.py::CrossHostReadIdReExportTests` covers only `_read_id` on text (not status, not `parse_plan_file`, not the strict half).
- Suite is run bare: `python3 -m pytest`.

## Findings

| Site | Lost test (in `19313eed^:tests/test_runner_refork_guard.py`) | Live coverage today |
|---|---|---|
| yuhl6o S-06 | `FrontMatterReaderBehaviorTests` (four tests) | Partial: `tests/test_runner_shared.py::CrossHostReadIdReExportTests` asserts the hosts' `_read_id` on loose spellings; nothing drives `parse_plan_file`, the status reader, the strict internal readers, or the single-token contract. |

## Proposed changes (ordered, validatable)

1. New `tests/test_front_matter_loose_whitespace.py` (E-01..E-03).
2. Docstring repoint in `agent_workflows/runner_shared.py` `parse_plan_file` (E-04).

## Deferred / out of scope (with reason)

- The `.pattern` string assertions of the deleted `test_selector_internal_readers_stay_strict`: source-structure pins forbidden by P16; replaced by return-value assertions.
- The deleted file's `SymmetricReForkGuardTests` (AST/identity re-fork guards, yuhl6o S-12 RETIRE-PIN): not named by backlog `qmpvcy` and forbidden by P16.
- Other stale `tests/test_runner_refork_guard.py` comments in `oc_runipd.py` / `agy_runipd.py`: they describe the identity/re-fork pins, not this property.
- Any production change to the readers: behavior is correct; only its guard is missing.

## Scope check

- Over-scope: none; no production logic changes.
- Under-scope: none; S-06 gets behavioral guards for both the permissive and strict halves plus the single-token contract.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_front_matter_loose_whitespace.py` passes.
- Non-vacuity: in a scratch, uncommitted edit, change `parse_plan_file`'s import to `from agent_workflows.selectors import _read_status`; the E-01 test fails on the two-space and tab subtests (status `pending`); revert.
- Full suite `python3 -m pytest` passes.

## Spec / documentation sync

N/A: test-only addition plus a docstring repoint; no spec text changes.

## Open questions

### OQ-01: Should the deleted regex-pattern pins and re-fork identity guards also be restored?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Backlog `qmpvcy` names only the loose leading whitespace tolerance property and states "only behavioral outcomes may be restored, never a source-reading pin (P16)"; the strict half is restored as return-value assertions instead.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_front_matter_loose_whitespace.py` showing the `parse_plan_file` test passing; plus pasted output of the scratch non-vacuity run (strict `_read_status` imported in `runner_shared.parse_plan_file`) showing it FAIL with status `pending`, then `git diff --stat agent_workflows/runner_shared.py` showing the scratch edit reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted pytest output showing the public-permissive and internal-strict tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted pytest output showing the single-token test passing, and `rg -n "import ast|import inspect|\.pattern|read_text\(.*\.py" tests/test_front_matter_loose_whitespace.py` returning no matches.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `git diff agent_workflows/runner_shared.py` showing only docstring lines changed and naming `tests/test_front_matter_loose_whitespace.py`; pasted `rg -n "no live guard currently asserts this loose-whitespace" agent_workflows/` with no matches; pasted bare `python3 -m pytest` summary line showing the full suite passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only the Scope-Paths files through `aw commit <plan> -- <paths>`; never push. After every `V-*` item records pasted evidence with `Result: pass` and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through the tooled lifecycle (`aw ipd finalize`).
