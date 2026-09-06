# IPD: the shared on-disk Set-completeness decision predicate

- Date: 2026-09-06
- Kind: child
- Concern: The runner cannot answer "is this Set now complete?". `_set_children_all_executed` (`oc_runipd.py:751-770`) inspects `state["queue"]` ONLY, so a run that executes the Set's LAST outstanding child while earlier children were executed in PREVIOUS runs sees one child, not the Set. `wslayout` passed its check only incidentally (child `wpu5zu` executed in an earlier run and absent from the queue; the four present children happened to be `executed`). Its "no children in-queue" branch returns `(False, [])`, which produced `5e4sb6`'s event with `unfinished_children: []` and a run summary reading "dependency-blocked (unmet dependencies)" naming no dependency. And a check over EXISTING members is not sufficient: `rununify`'s two children are both `executed` on disk, yet its child table declares a row `03+` that was never authored, so a naive "all members executed" rule would wrongly retire `5e4sb6`.
- Scope: Build ONE shared, host-neutral predicate in `runner_shared.py` that decides whether a Set is retirement-eligible, reading the PLANS TREE rather than a run queue, and returning a typed reason for every refusal. Implements spec `77tr3o` R-1, R-2, R-3, R-9, R-10. It DECIDES ONLY and performs no transition (child 02 owns that) and touches no dispatch site (child 03 owns that). It does NOT change `_set_children_all_executed`'s callers, does NOT alter `EXECUTION_SUCCESS_STATES` (spec Section 4), and does NOT touch the `dependency-blocked` write.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_orchestrator_retirement.py
- Item-Dependencies: none
- Status: to-review
- Readiness: go-pending-approval
- Set: orchretire
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 5942n7
- From-Backlog: kxkc04
- From-Spec: 77tr3o

## Workflow history

- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored complete from approved spec 77tr3o. Every cited line and measurement verified at HEAD 844d195c.
- 2026-09-06 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give both runners one truthful answer to "may this Set's orchestrator be retired now?", computed from
the plans tree so it is correct across runs, and carrying a typed reason so the four distinct refusal
causes stop sharing one misleading message.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the predicate

- [ ] E-01 Add a host-neutral Set-membership reader to `runner_shared.py` that returns every member of a Set from the PLANS TREE with its `Id`, `Order`, `Kind` and `Status`. Reuse the existing resolvers rather than adding a third "which plans exist" mechanism: `selectors.resolve(repo_root, "plans", setid)` already returns members across `pending/` and `executed/`, and `ipd_lint.parse(text).meta_fields` already yields the four fields. Verified working at HEAD: for `wslayout` it returns 5 children all `executed` plus orchestrator `rh5tt6` `approved`; for `lanectn` it returns 4 `executed` children plus `nna8yz`/`xdr83v` at `approved`.
  - Depends on: none
  - Expected outcome: a function that, given a repo root and a setid, returns the Set's members read from disk; a Set with members only in `executed/` is returned in full, which is the case the queue-scoped check cannot see.
  - Execution state: pending

- [ ] E-02 Add the retirement-eligibility predicate returning a typed decision, not a bare bool. It is eligible ONLY when the Set has at least one child AND every child's on-disk `Status` is exactly `executed` (spec R-2). Refuse with a DISTINCT typed reason for each of: children exist but are unfinished (naming the unfinished ids and their actual statuses); the Set has no children at all; the orchestrator's child table declares rows that resolve to no plan (spec R-3, the `rununify` case). `substantially-complete` MUST NOT qualify: it means finalize refused (`i452hf`), and `nna8yz` carries it today while its work sits unintegrated on a lane branch.
  - Depends on: E-01
  - Expected outcome: `wslayout` -> eligible; `lanectn` -> refused naming `nna8yz` and `xdr83v`; `rununify` -> refused for unauthored child rows, NOT eligible.
  - Execution state: pending

- [ ] E-03 Implement the unauthored-child-row detection E-02 depends on, and make it FAIL CLOSED. Parse the orchestrator's `## Child IPDs, sequence, and dependencies` table for declared Order tokens and compare against the Orders that actually resolve to plans. `5e4sb6`'s row is literally `03+`, so the parser must treat a non-numeric or open-ended token as "declares more children than exist" rather than skipping it. When the table cannot be parsed at all, REFUSE (spec OQ-2 permits a conservative refusal and R-3 requires one); never treat an unparseable table as "fully authored".
  - Depends on: E-01
  - Expected outcome: `5e4sb6`'s `03+` row is detected as unauthored; `rh5tt6`'s table, whose five rows all resolve, is detected as fully authored; a table with no recognizable rows refuses.
  - Execution state: pending

- [ ] E-04 Write `tests/test_orchestrator_retirement.py` covering the predicate against synthetic Sets in a temp repo, one test per typed reason, plus the three REAL cases as fixtures derived from this repo's own measured states (all-executed, unfinished-children, unauthored-rows). Include the cross-run case explicitly: a Set whose children are all in `executed/` and NONE of which is in any queue must be eligible, because that is the maintainer's stated requirement and the defect the queue-scoped check causes.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: a new test module whose failures name the specific reason that regressed.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Run the suite BARE (`python3 -m pytest`). `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; adding `-n0` is 4-6x slower here and a second `-q` suppresses the summary line this plan's evidence requires.
- The anti-re-fork discipline from `2r306y`/`818uru` is binding: shared runner logic lives in `runner_shared.py` exactly once and is IMPORTED by both hosts, never copied. This plan's whole purpose is to put the decision in that one place.
- `substantially-complete` is in `EXECUTION_SUCCESS_STATES` (`oc_runipd.py:274`) for DEPENDENCY-EDGE purposes. That is out of scope (spec Section 4) and must not be changed here; this predicate simply does not accept it.
- Reuse `selectors.resolve` and `ipd_lint.parse`; do not add a path literal for the plans tree.

## Findings

| # | Sev | Where | Finding | Evidence |
|---|-----|-------|---------|----------|
| F-1 | HIGH | `oc_runipd.py:751-770` | `_set_children_all_executed` reads `state["queue"]` only, so Set completeness cannot be evaluated across runs. This is why the maintainer's "fires when the last outstanding child completes" requirement is unimplementable today. | source read at HEAD `844d195c` |
| F-2 | HIGH | `rununify` | A completeness check over existing members is unsound: both children `executed`, orchestrator would be wrongly retired, but child row `03+` was never authored. | `aw find plans --set rununify` shows only Orders 01, 02; `5e4sb6` child table row `03+` |
| F-3 | MED | `5e4sb6` event | "no children in queue" returns `(False, [])`, producing "dependency-blocked (unmet dependencies)" naming none. The safe default is right; the message is the defect. | `events.jsonl`: `reason: not-all-children-executed, unfinished_children: []` |
| F-4 | MED | `nna8yz` | `substantially-complete` must not count as executed: its work is real but stranded on `aw/lane/nna8yz` (tip `396ddebf`, not an ancestor of HEAD), and its plan is still in `pending/`. | `git merge-base --is-ancestor` returns false; `aw find plans --id nna8yz` shows `pending` |

## Proposed changes (ordered, validatable)

1. E-01 membership reader over the plans tree, reusing `selectors.resolve` + `ipd_lint.parse`.
2. E-03 unauthored-row detection, failing closed on an unparseable table.
3. E-02 eligibility predicate returning a typed decision consuming both.
4. E-04 tests, including the cross-run and the three real-world cases.

## Deferred / out of scope (with reason)

- Performing the transition: child 02. This plan decides only, so a wrong decision cannot move a plan.
- Wiring the dispatch sites and removing the terminal-status write: child 03.
- `EXECUTION_SUCCESS_STATES` accepting `substantially-complete` for dependency EDGES: spec Section 4; a real defect (it is why `xdr83v` was dispatched against an unlanded prerequisite) but separately owned.
- Retiring the four currently-stuck orchestrators: a consequence of the Set, not part of the mechanism.

## Scope check

- Over-scope: none.
- Under-scope: the predicate is unreachable from a real run until child 03 wires it. That is deliberate sequencing, and child 02 and 03 both declare the dependency.

## Required tests / validation

`python3 -m pytest` bare, with the new module's per-reason tests passing and no pre-existing test regressing. The baseline MUST be measured at execution time and pasted, not carried from this plan: the suite reported `4517 passed, 3 skipped, 4 xfailed` at HEAD `844d195c`, and a lane worktree legitimately reports more failures (35 measured on `xdr83v`'s lane, all lane-environment artifacts), so compare failing NODE IDS, never totals.

## Spec / documentation sync

Spec `77tr3o` R-1/R-2/R-3/R-9/R-10 are implemented here; no spec text changes. `AGENTS.md` correction is child 03 (R-11).

## Open questions

### OQ-01: how strictly must the child-IPD table be parsed to satisfy R-3?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED, and CONFIRMED BY THE MAINTAINER 2026-09-06 when asked directly (spec `77tr3o` OQ-2). He chose TABLE PARSING over the alternative of requiring an explicit "child set complete" field on every orchestrator, because the field would have to be backfilled everywhere before the check could be trusted, and until then an unbackfilled parent would be indistinguishable from an incomplete one. He accepted the acknowledged weakness: the table is prose and `5e4sb6`'s row token is literally `03+`, so exact numeric parsing is impossible in the one case that matters. E-03 therefore treats any non-numeric or open-ended token, and any unparseable table, as "declares more children than exist" and refuses. This can only produce a FALSE REFUSAL (an orchestrator lingers, the status quo), never a false retirement, so the failure direction is safe by construction.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python session calling the new reader for `wslayout` and `lanectn` against this repo, showing the returned members with Id/Order/Kind/Status. `wslayout` must show 5 children all `executed` plus orchestrator `rh5tt6`; `lanectn` must show `nna8yz` and `xdr83v` not executed. Both must be read with NO run state present, proving the plans tree is the source.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the typed decision for all three real Sets: `wslayout` eligible; `lanectn` refused naming both unfinished ids; `rununify` refused for unauthored rows. Also paste a synthetic case where a child is `substantially-complete` and show it is REFUSED, with the reason naming that status.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the detection result for `5e4sb6` (unauthored, triggered by the `03+` token) and for `rh5tt6` (fully authored, all five rows resolve), plus a synthetic unparseable table showing it REFUSES rather than passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the bare `python3 -m pytest` summary line showing the new module's tests passing and the total not regressing against a baseline measured in the same worktree at execution time. Then paste one deliberate SABOTAGE per typed reason (e.g. flip a child's status to `substantially-complete`) showing the corresponding test FAILS, proving the tests bind behavior rather than merely passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Stay inside `Scope-Paths`; `oc_runipd.py` and `agy_runipd.py` are explicitly OUT of
bounds for this child even though they are the eventual consumers, because child 03 owns wiring and two
plans editing the same dispatch region is the contention this Set is sequenced to avoid. Do not change
`EXECUTION_SUCCESS_STATES`, `TERMINAL_STATES`, or the `dependency-blocked` write. PASTE ACTUAL OUTPUT for
every `V-*`; a claim of success without pasted evidence is a contract violation. Measure the suite
baseline in YOUR worktree before asserting a regression, and compare failing node ids rather than totals.
All open questions are resolved; no maintainer decision is outstanding.

POST-GATE LIFECYCLE. Do not claim done or move this plan until every `V-*` is verified with concrete
pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed
by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
