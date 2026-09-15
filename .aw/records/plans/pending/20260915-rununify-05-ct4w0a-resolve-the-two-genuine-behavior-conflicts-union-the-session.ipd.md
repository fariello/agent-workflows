# IPD: Resolve the two genuine behavior conflicts, union the session id reader and adopt the isolated begin baseline

- Date: 2026-09-15
- Kind: child
- Concern: `extract_session_id` and `driver_begin` are the ONLY two shared runner symbols where the hosts genuinely disagree about behavior rather than about strings or style. A blind "oc wins" breaks Antigravity's session tracking outright, because oc's reader cannot see agy's wire format.
- Scope: Unify both through `runner_shared.py` using the maintainer's 2026-09-14 per-symbol rulings: UNION for `extract_session_id` (a superset harming neither host), and ADOPT OC for `driver_begin` (agy gains the isolated-baseline declaration it silently lacks).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_rununify_conflicts.py
- Item-Dependencies: executed:i3d6ml
- Status: to-review
- Set: rununify
- Order: 5
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: ct4w0a
- From-Backlog: alw22r

## Workflow history
- 2026-09-15 to-review (aw set): Authored 2026-09-15 from a fresh measurement at HEAD; resolves part of the rununify parent's placeholder child rows per the maintainer's 2026-09-14 oc-preferred ruling.

- 2026-09-15 draft (opencode/its_direct-pt3-claude-opus-5): created.
- 2026-09-15 authored (opencode/its_direct-pt3-claude-opus-5): authored after both conflicts were measured symbol-by-symbol and put to the maintainer, who ruled union for one and adopt-oc for the other.

## Goal

Collapse the two symbols where the hosts really behave differently, keeping every capability each side
has today: one session-id reader that understands BOTH wire formats, and one `driver_begin` that
declares the correct `aw ipd begin` baseline for an isolated turn on either host.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the session id reader (UNION)

- [ ] E-01 Measure, at execution HEAD, what each host's session log ACTUALLY contains, before writing the union. Sample real logs under `.aw/records/runs/*/sessions/*.jsonl` for both hosts and record: which of the four keys appear (`sessionID`, `sessionId`, `session_id`, `conversation_id`), whether any appear NESTED under a `result` or `init` object, and whether the `ses_`-prefix preference oc encodes is observable in either. Do not write the union from the two source listings alone; the point is to keep a capability that is real, not one that is merely coded.
  - Depends on: none
  - Expected outcome: a pasted per-host census of observed keys and nesting; an explicit note for any key or nesting path that appears in NEITHER host's real logs, since that is a candidate for deletion rather than preservation.
  - Execution state: pending

- [ ] E-02 Implement ONE `extract_session_id` in `runner_shared.py` as the UNION per the maintainer's ruling: all four keys, checked flat AND inside a nested `result` or `init` mapping, with a non-dict event skipped rather than raising. PRESERVE oc's `ses_`-prefix PREFERENCE (return a `ses_`-prefixed value immediately, keep any other value as a fallback and return it only if no prefixed one is found) because that is a real oc behavior agy's version drops; and PRESERVE agy's `conversation_id` and nesting because that is agy's wire format. If E-01 shows a branch is unobservable in both hosts, say so and keep it anyway ONLY if a host's launcher documents that shape, otherwise drop it and record the deletion.
  - Depends on: E-01
  - Expected outcome: one definition both hosts import; oc's prefix preference and agy's key/nesting coverage BOTH demonstrably intact.
  - Execution state: pending

### Task group 2: the begin baseline (ADOPT OC)

- [ ] E-03 Adopt oc's `driver_begin` as the single definition, including its `isolated: bool = False` keyword and its `begin_baseline_env(isolated)` child-env overlay, and route agy's call site through it. THIS IS A CAPABILITY AGY GAINS: `aw ipd begin` gates execution authority on the plan's in-scope paths being unambiguous in the baseline the turn will EXECUTE against, and for an isolated turn that baseline is the LANE, not the main tree. agy passes no such declaration today, so an isolated agy turn measures the wrong baseline. Pass `isolated=` truthfully from each host's existing knowledge of whether the turn is isolated; do not default it to `True` for agy just to make the call sites match.
  - Depends on: none
  - Expected outcome: one definition; an isolated agy turn now declares the lane baseline to `aw ipd begin`; a non-isolated turn on either host declares exactly what it does today.
  - Execution state: pending

- [ ] E-04 Verify the adoption did not change the NON-isolated path on either host, since that is the path every current test exercises and a silent change there would be invisible. Compare the child env `driver_begin` builds for `isolated=False` against what each host built before this plan, and show they are equal.
  - Depends on: E-03
  - Expected outcome: pasted proof that `isolated=False` produces a byte-identical child env to the pre-change behavior for BOTH hosts.
  - Execution state: pending

### Task group 3: proof

- [ ] E-05 Add `tests/test_rununify_conflicts.py`: both symbols resolve to the SAME OBJECT from both hosts; the session reader finds an id for EVERY key and nesting shape in E-01's census AND still prefers a `ses_`-prefixed value over an unprefixed one; `driver_begin` emits the isolated declaration when and only when `isolated=True`; and an AST scan proves neither runner re-defines either symbol.
  - Depends on: E-02, E-03
  - Expected outcome: a suite that fails if either capability is lost, naming which one.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `begin_baseline_env(isolated)` already exists in `oc_runipd.py:915` with a docstring explaining the
  contract (`lanetruth` Order 02, `z2isfg`): `begin` gates execution authority on in-scope paths being
  unambiguous in the baseline the turn will execute against. Nothing needs inventing for E-03; the
  helper is written and only agy's route to it is missing.
- `_SESSION_ID_KEYS` is defined TWICE with different contents: `oc_runipd.py:3760` has three keys,
  `agy_runipd.py:2465` has four. The union must collapse those two constants as well as the function,
  or the next reader will re-fork from whichever constant they find first.
- Both hosts' session logs live under `.aw/records/runs/<run-id>/sessions/`, which is GITIGNORED and
  box-local, so E-01's census is only possible in a primary checkout with real run history. An isolated
  lane cannot perform it; say `AW_MISSING_INPUT: .aw/records/runs` if that is where execution lands.
- The execution contract forbids `git add -A`; commit only the declared `Scope-Paths`, path-scoped.

## Findings

| # | Sev | Where | Finding |
|---|---|---|---|
| F-1 | HIGH | `oc_runipd.py:3760` vs `agy_runipd.py:2465` | THE ONE CASE WHERE "OC WINS" WOULD BREAK A HOST. oc reads three flat `session*` keys; agy reads those plus `conversation_id`, and also looks inside nested `result` and `init` objects. Adopting oc alone leaves agy unable to find its own session id, which silently disables session resume (and therefore plan `b7xarm`'s one-shot defect-report re-ask, which refuses to fire without an observed session). |
| F-2 | HIGH | `extract_session_id`, both hosts | THE UNION IS NOT SYMMETRIC EITHER. oc encodes a PREFERENCE agy lacks: it returns a `ses_`-prefixed value immediately and keeps any other value only as a fallback. agy returns the first non-empty value it sees. A naive union built from agy's body would silently drop oc's preference, so the union must be built deliberately from both, not by taking the longer function. |
| F-3 | HIGH | `driver_begin`, `begin_baseline_env` | oc accepts `isolated` and passes a baseline-declaring env overlay to `aw ipd begin`; agy passes only `pinned_child_env()`. So an ISOLATED agy turn asks `begin` to gate on the wrong baseline. This is agy silently lacking a correctness feature, which is exactly the "one does A, the other NOT A" case, and it resolves toward oc. |
| F-4 | MED | `.aw/records/runs/` | The corpus needed for E-01's census is gitignored and absent inside an isolated lane. Both the census and any re-measurement must happen in a primary checkout, or be reported as `AW_MISSING_INPUT`. |
| F-5 | MED | measured at HEAD | Neither of these two symbols is currently a delegating stub on either side, unlike 14 of the Set's other shared symbols. Both are genuinely two implementations, which is why they were separated out of child 03 rather than lifted with it. |

## Proposed changes (ordered, validatable)

1. Census the real logs for both hosts before designing the union (E-01), so preserved branches are
   preserved for evidence rather than for symmetry.
2. Write the union reader, keeping oc's `ses_` preference AND agy's keys/nesting, collapsing the two
   `_SESSION_ID_KEYS` constants into one (E-02).
3. Adopt oc's `driver_begin` and route agy through it, passing `isolated=` truthfully (E-03).
4. Prove the non-isolated path is byte-identical on both hosts (E-04).
5. Add the capability-preservation suite (E-05).

## Deferred / out of scope (with reason)

- The 48 no-disagreement symbols (child 03, `i3d6ml`, this plan's dependency) and the 8 host-string
  symbols (child 04, `tx6q0h`).
- `PlanRecord`, `parse_plan_file`, `build_dynamic_manifest`: child 06.
- `execute_item`, `run_queue`, `initialize_run`, `build_parser`, `main`: children 07 through 11.
- CHANGING WHAT EITHER LAUNCHER EMITS. This plan makes the READER understand both formats; it does not
  ask either host to normalize its log shape, which would be a far larger change touching live process
  invocation.

## Scope check

- Over-scope: none. Three source files plus one new test file, two symbols.
- Under-scope: if E-01's census shows a nesting path that appears in NEITHER host's real logs, this plan
  keeps it only when a launcher documents that shape and otherwise deletes it, so the union does not
  become a permanent home for speculative branches.

## Required tests / validation

1. `tests/test_rununify_conflicts.py` (new): object identity across hosts for both symbols; the session
   reader finds an id for EVERY key and nesting shape in the census; the `ses_` preference still holds
   (a log containing both an unprefixed and a `ses_` value returns the prefixed one); `driver_begin`
   emits the isolated declaration if and only if `isolated=True`; AST scan proving no re-fork.
2. NON-VACUITY, two controls, because both rulings can regress silently: (a) drop `conversation_id`
   from the shared key list and show an agy-shaped log FAILS to resolve; (b) drop the `ses_` preference
   and show the mixed-value case FAILS. Restore both.
3. `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` green, both of which exercise session
   extraction and begin.
4. `tests/test_defect_report.py` green, named specifically because plan `b7xarm`'s re-ask REFUSES when
   no session id was observed, so a regression in this reader would disable that feature quietly rather
   than loudly.
5. Bare `python3 -m pytest`, summary pasted, no new failure against the baseline at execution time.

## Spec / documentation sync

No `.spec.md` change. Neither symbol is spec-governed: the session-id wire format belongs to each host's
launcher, and `aw ipd begin`'s baseline contract is already described by `begin_baseline_env`'s own
docstring and by the `lanetruth` Order 02 plan that introduced it. E-03 makes agy CONFORM to that
existing contract rather than altering it, which is a defect fix and not a contract change.

## Open questions

### OQ-01: For `extract_session_id`, does the maintainer's "oc is preferred" ruling mean oc's reader wins outright?

- Blocking: no
- Status: resolved
- Owner: maintainer, 2026-09-14
- Resolution or deferral rationale: NO, and the maintainer ruled explicitly on this symbol. The standing
  rule is "oc is preferred UNLESS there are significant differences (one does A the other NOT A)", and
  this is the clearest instance of that exception in the whole Set: agy reads a key and a nesting shape
  oc cannot see, and that shape IS agy's wire format. The ruling is UNION, which is a strict superset and
  harms neither host. F-2 records the non-obvious half: the union must also keep oc's `ses_` preference,
  so it is built from both bodies deliberately rather than by adopting the longer one.

### OQ-02: For `driver_begin`, is giving agy the isolated-baseline declaration a behavior change the parent forbids?

- Blocking: no
- Status: resolved
- Owner: maintainer, 2026-09-14
- Resolution or deferral rationale: The parent forbids a child CHANGING what a runner does as a
  side effect of unification. This is the maintainer's deliberate adoption of oc's version for a symbol
  where agy is measurably deficient: an isolated agy turn currently asks `aw ipd begin` to gate on the
  main tree's baseline when the turn will execute in a lane. Fixing that is the point of the ruling, not
  an accident of it. E-04 bounds the risk by proving the NON-isolated path, which every existing test
  exercises, is byte-identical afterwards.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted per-host census of session-log keys and nesting observed in real logs, with an explicit note for any coded branch that appears in neither host.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `oc_runipd.extract_session_id is agy_runipd.extract_session_id`; the single collapsed `_SESSION_ID_KEYS`; a resolved id for each key and each nesting shape; and the mixed-value case returning the `ses_`-prefixed value (F-2).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted identity result for `driver_begin`, and the child env it builds for `isolated=True` on BOTH hosts showing the baseline declaration present.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted byte-comparison of the `isolated=False` child env before and after the change, for both hosts, showing equality.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: THREE parts, all pasted. (a) `python3 -m pytest tests/test_rununify_conflicts.py -o addopts=""` green. (b) BOTH non-vacuity controls from Required tests item 2, each failing when its capability is removed and green when restored. (c) Bare `python3 -m pytest` with no new failure, plus `tests/test_defect_report.py` green by name.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the declared `Scope-Paths`, path-scoped; never `git add -A` and never
push. Paste the ACTUAL runner output for every `V-*`. Run the suite BARE as `python3 -m pytest`.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

REVIEWER'S HIGHEST-VALUE TARGETS: F-2, because the union can silently drop oc's `ses_` preference and
no existing test would notice; and the coupling in Required tests item 4, since a quiet regression in
this reader disables `b7xarm`'s defect-report re-ask by making it believe no session was observed.
