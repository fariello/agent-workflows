# IPD: Restore behavioral coverage of selector setid precedence over filename substring

- Date: 2026-10-14
- Kind: child
- Concern: The frozen selector precedence (`setid` and `status` outrank the filename `stem` and `substring` rules) has no live behavioral guard since `tests/test_selector_zero_open.py` was deleted in `19313eed`.
- Scope: Add one new outcome-only test module that drives `selectors.resolve` on temporary fixture trees and asserts which rule wins when a token is both a Set id (or Status) and a filename fragment; repoint the stale "no live guard" code comment in `agent_workflows/selectors.py` to the new module.
- Scope-Paths: tests/test_selector_precedence_outcomes.py, agent_workflows/selectors.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: ni8n5s
- Set: ni8n5s
- Order: 1
- Highest E allocated: 04
- Author: OpenCode Claude Opus
- Id: q9f0k7

## Workflow history

- 2026-10-15 draft (OpenCode Claude Opus): created.
- 2026-10-15 to-review (OpenCode Claude Opus): authored from backlog ni8n5s; review-ready.

## Goal

Restore behavioral coverage of the selector precedence property recorded as site S-26 in plan `ev7t1w` (`RETIRE-UNGUARDED`): when a token is simultaneously a Set id and a filename fragment, `selectors.resolve` must return the `setid` match, not the `substring` match. The restored tests exercise the resolver and assert on its returned `Resolution`, never on source text or on the `_PRECEDENCE` tuple (GUIDING_PRINCIPLES P16).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Outcome tests

- [ ] E-01 Create `tests/test_selector_precedence_outcomes.py` with a temporary-repo fixture (plans tree under `.aw/records/plans/pending/`, several plans declaring `- Set: demo`, plus one colliding plan declaring `- Set: other` whose FILENAME contains `demo`) and a test asserting `selectors.resolve(root, "plans", "demo")` returns `kind == selectors.MATCH_SETID`, contains every `Set: demo` plan, and excludes the colliding file.
  - Depends on: none
  - Expected outcome: The test passes against the current resolver and would fail if `substring` were evaluated before `setid`.
  - Execution state: pending

- [ ] E-02 In the same module add (a) a `status`-over-`substring` collision test (a token that is a declared `- Status:` value of some plans AND a fragment of another plan's filename resolves with `kind == selectors.MATCH_STATUS` and excludes the filename-only hit), and (b) a fall-through test: a token that is a filename fragment only (no record declares it as Set or Status) resolves with `kind == selectors.MATCH_SUBSTRING` to exactly that file, proving the setid result above came from precedence and not from substring being broken.
  - Depends on: E-01
  - Expected outcome: Three behavioral tests in the module, all asserting on `Resolution.kind` and `Resolution.paths` only; no `inspect`, `ast`, regex over source, or reference to `selectors._PRECEDENCE`.
  - Execution state: pending

- [ ] E-03 Prove the setid test is falsifiable: temporarily reorder `_PRECEDENCE` in a scratch copy (or monkeypatch `selectors._PRECEDENCE` in an ad-hoc, uncommitted `python3 -c` session) so `MATCH_SUBSTRING` precedes `MATCH_SETID`, run the E-01 test, observe it FAIL, then restore. Nothing from this probe is committed.
  - Depends on: E-02
  - Expected outcome: Captured failing pytest output under the reordered precedence; `git diff agent_workflows/selectors.py` shows no precedence change afterwards.
  - Execution state: pending

### Task group 2: Comment repoint and commit

- [ ] E-04 Edit the `_PRECEDENCE IS FROZEN AS SEMANTICS` comment in `agent_workflows/selectors.py` (the paragraph reading "Formerly pinned by `tests/test_selector_zero_open.py::PrecedenceForcesFrontMatterReadsTests` (deleted in `19313eed`; no live guard currently asserts this)") so it names `tests/test_selector_precedence_outcomes.py` as the live behavioral guard, keeping the historical reference. Comment-only change; then run the bare suite and commit via `aw commit q9f0k7 -- tests/test_selector_precedence_outcomes.py agent_workflows/selectors.py`.
  - Depends on: E-03
  - Expected outcome: Comment updated, no code change in `selectors.py`, bare suite passes, single path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- GUIDING_PRINCIPLES P16 and AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE": restored coverage must call the code and assert on outputs. The deleted `PrecedenceForcesFrontMatterReadsTests.test_precedence_places_filename_rules_last` read `selectors._PRECEDENCE` indices, a structure pin; it is deliberately NOT restored. Its `test_a_filename_query_still_reads_because_earlier_rules_must_lose_first` asserted open counts via patched `builtins.open`, an implementation-cost proxy; also not restored (out of the backlog item's stated property).
- Precedent for this exact restoration style: `tests/test_selector_two_dialect_readers.py` (module docstring cites the same deleted file and restores only outcomes on temp fixtures, no `slow`/`livecorpus` marker).
- Resolver contract: `selectors.resolve` docstring, "Precedence (first rule that yields matches wins)": path, id6, setid, status, stem, substring; constants `selectors.MATCH_SETID`, `selectors.MATCH_STATUS`, `selectors.MATCH_SUBSTRING` are the public result kinds carried on `Resolution.kind`.
- Suite runs bare: `python3 -m pytest` (AGENTS.md repo-local contract); commits through `aw commit`.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | The property lost is setid-over-substring precedence. | `git show 19313eed^:tests/test_selector_zero_open.py`, `PrecedenceForcesFrontMatterReadsTests.test_a_token_can_be_both_a_setid_and_a_filename_fragment` resolved `"demo"` with a colliding `...-dd0001-demo-shaped-name.ipd.md` and asserted `MATCH_SETID`. |
| F-02 | Plan `ev7t1w` classified site S-26 `RETIRE-UNGUARDED`. | `ev7t1w` disposition table row S-26: "tested setid outranking substring in selector resolution; deleted in `19313eed`". |
| F-03 | No live test asserts this today. | `rg -n "MATCH_SUBSTRING" tests/` is empty; `tests/test_selector_two_dialect_readers.py` asserts `MATCH_SETID` only on non-colliding YAML research fixtures. |
| F-04 | The source comment explicitly records the gap. | `agent_workflows/selectors.py` comment: "no live guard currently asserts this". |

## Proposed changes (ordered, validatable)

1. E-01/E-02: new module `tests/test_selector_precedence_outcomes.py` with three outcome tests.
2. E-03: one-off falsifiability probe (not committed).
3. E-04: comment repoint in `agent_workflows/selectors.py`, bare suite, commit.

## Deferred / out of scope (with reason)

- Read-cost/open-count assertions from the deleted file (E-05 of `e32j35`): a cost proxy, not the backlog item's property, and borderline P16.
- `id6`-over-`setid` and `stem`-over-`substring` orderings: not named by the backlog item; can be filed separately if wanted.
- Any change to resolver behavior: the property is restored as-is.

## Scope check

- Over-scope: none. The `selectors.py` edit is comment-only and removes a now-false statement.
- Under-scope: none. The backlog item's single property (setid precedence over filename substring) is covered by E-01, with E-02 adding the status sibling and the fall-through control that make E-01 meaningful.

## Required tests / validation

- `python3 -m pytest tests/test_selector_precedence_outcomes.py -o addopts=""` shows 3 passed.
- Falsifiability probe (E-03) shows the setid test failing under reordered precedence.
- Bare `python3 -m pytest` passes.
- `aw ipd lint` on this plan conforms.

## Spec / documentation sync

N/A: no spec or user-facing doc describes this test; the only documentation touch is the in-source comment updated by E-04. No `.spec.md` is edited.

## Open questions

### OQ-01: Restore the `_PRECEDENCE` index assertion too?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. It reads an internal constant (structure pin), prohibited by P16 and by the backlog item text "only behavioral outcomes may be restored, never a source-reading pin".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of `python3 -m pytest tests/test_selector_precedence_outcomes.py -o addopts="" -v` showing the setid-collision test PASSED, plus the test source excerpt showing the colliding file is a `Set: other` plan whose filename contains `demo` and the assertions on `kind == selectors.MATCH_SETID` and exclusion of the colliding path.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Same verbose pytest output showing the status-collision and substring fall-through tests PASSED (3 passed total), and pasted `rg -n "inspect|import ast|_PRECEDENCE|read_text\(.*selectors" tests/test_selector_precedence_outcomes.py` returning no matches.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted pytest output of the setid-collision test FAILING with `selectors._PRECEDENCE` monkeypatched to place `MATCH_SUBSTRING` before `MATCH_SETID` (produced by the E-03 probe), and pasted `git diff --stat agent_workflows/selectors.py` showing no change to the `_PRECEDENCE` tuple.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `git show --stat HEAD` naming exactly the two Scope-Paths, pasted `git show HEAD -- agent_workflows/selectors.py` showing only comment lines changed, and the pasted summary line of a bare `python3 -m pytest` run showing all passed with zero failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Follow the agent execution contract: commit only the Scope-Paths through `aw commit q9f0k7 -- <paths>`, never push, paste actual runner output for every `V-*`. Move to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` is `pass`.
