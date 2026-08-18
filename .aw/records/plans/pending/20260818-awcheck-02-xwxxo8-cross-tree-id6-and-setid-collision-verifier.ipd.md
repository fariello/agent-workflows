# IPD: cross-tree id6 and setid collision verifier

- Date: 2026-08-18
- Kind: child
- Concern: awcheck Order 02 (spec 20260818-1525-01; TODO item 23). Add a collision verifier so name checks guarantee id6 AND setid UNIQUENESS. Today the only id6 uniqueness check is inside `attention.scan` (attention.py:153-163) and `backlog.run_check` (backlog.py:447-463, backlog-only); there is NO setid collision check anywhere. Add a reusable collision sub-check to the Order-01 check engine that verifies id6 uniqueness across ALL record trees and detects setid inconsistencies.
- Scope: extend `agent_workflows/check_engine.py` (from Order 01) + its test file. IN: a `check_collisions(repo_root) -> List[Drift]` that scans every record tree for `- Id:` and flags any id6 appearing on more than one file (rule `check.id6-collision`), plus a setid consistency check (rule `check.setid-collision` for the same setid used with conflicting metadata as defined below); wire it into `check_types` when `all` (or a new `collisions` kind). OUT: the engine core (Order 01, done), the `--legacy`/message work (Order 03), CLI wiring (awcmdsurf).
- Status: to-review
- Set: awcheck
- Order: 2
- Highest E allocated: 03
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: xwxxo8

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from investigation (attention id6 dedup attention.py:153-163; backlog id dup backlog.py:447-463; is_valid_id6 artifact_core.py:45; no setid check exists).

## Goal

Guarantee global uniqueness: add a `check_collisions` sub-check to the check engine that scans every
record tree, flags any id6 used by more than one file (across all trees, not just within one), and
flags setid collisions per the rule below. It reuses the same dedup pattern already proven in
attention/backlog, generalized to all trees.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not performed validation.

FOR THE EXECUTOR: Edit ONLY `agent_workflows/check_engine.py` and `tests/test_check_engine.py` (both
created in Order 01, which MUST be executed first). Return Drift; never print.

### Task group 1: id6 collision scan

- [ ] E-01 Add `check_collisions(repo_root: Path) -> List[Drift]` to `check_engine.py`. Iterate every record type in `SUPPORTED` (plus `research`), resolve each type's dirs via `_rp.resolve_record_read_paths(...)`, walk `*.md` (skip README/INDEX/STATUS), read each file's `- Id:` with the regex `^- Id:\s*([0-9a-z]{6})\s*$` (re.MULTILINE), and build a `seen: Dict[str, str]` mapping id6 -> first path. When an id6 recurs, emit `Drift(str(path), "check.id6-collision", f"id6 {id6} also on {seen[id6]}")`. This mirrors attention.py:153-163 / backlog.py:447-463 but spans ALL trees. Read files in `try/except OSError: continue`.
  - Depends on: none
  - Expected outcome: over a fixture where a plan and a spec BOTH carry `- Id: dup111`, `check_collisions(root)` returns exactly one `check.id6-collision` Drift naming both files.
  - Execution state: pending

### Task group 2: setid collision scan

- [ ] E-02 Extend `check_collisions` to also detect SETID collisions. Define the rule precisely: a setid collision is when the SAME setid token appears under TWO DIFFERENT record types (e.g. a `demo` set in both plans and specs) OR when the same setid maps to two different descriptive names within one type. Build a `setids: Dict[str, tuple]` mapping setid -> (type, descriptive-or-None, first-path); when a later file uses the same setid with a DIFFERENT (type) or a DIFFERENT non-None descriptive, emit `Drift(str(path), "check.setid-collision", f"setid {sid} conflicts with {first_path} (<reason>)")`. Parse the setid as the first token before `(` of the `- Set:` line (mirror plans_index.set_terse_id). If a setid legitimately spans a type by design, this is still worth surfacing as drift the maintainer can whitelist later; keep the rule as stated.
  - Depends on: E-01
  - Expected outcome: over a fixture where setid `demo` is used in a plan with descriptive `(Alpha)` and another plan with descriptive `(Beta)`, `check_collisions` returns a `check.setid-collision` Drift; a consistent reuse (same descriptive) does NOT.
  - Execution state: pending

### Task group 3: wire into the engine + tests

- [ ] E-03 Wire `check_collisions` into the engine's fan-out: in `check_types`, when the caller passes `["all"]` (or a new explicit `collisions=True` kwarg), APPEND `check_collisions(repo_root)` ONCE to the aggregate (collisions are cross-tree, so run once, not per type). Add a `collisions` kwarg to `check_types(repo_root, types, names_only=False, legacy=False, collisions=False)` defaulting False; `all` implies collisions=True. Add tests to `tests/test_check_engine.py` (class `CollisionTests`): `test_id6_collision` (duplicate id6 across plans+specs flagged), `test_no_collision_clean` (unique ids -> no collision drift), `test_setid_collision` (same setid, conflicting descriptive -> flagged), `test_all_runs_collisions_once` (`check_types(root,["all"])` includes exactly one collision pass, not N). Run the FULL serial suite and paste the tail.
  - Depends on: E-01,E-02
  - Expected outcome: the four tests pass; `check_types(root,["all"])` includes collision drift exactly once; full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Existing dedup pattern to generalize: attention.scan `seen_ids` (attention.py:153-163) + backlog.run_check `seen_ids` (backlog.py:447-463). Both key on a valid id6 (`core.is_valid_id6`, artifact_core.py:45).
- No setid collision check exists anywhere - this Order introduces it.
- setid parse: first token before `(` in the `- Set:` line (mirror plans_index.set_terse_id, plans_index.py:66).
- Collisions are CROSS-TREE, so run once over all trees, not once per type; the engine appends it a single time in the `all` fan-out.
- Drift rules are new ids: `check.id6-collision`, `check.setid-collision` (namespaced under `check.` like the Order-01 engine rules).

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | id6 dedup already proven twice (attention, backlog). | Generalize the pattern; low risk. |
| F2 | No setid uniqueness check today. | Genuinely new; define the collision rule crisply (E-02) so Medium implements it deterministically. |
| F3 | Collisions are cross-tree. | Run once in the `all` fan-out, not per-type, to avoid N passes + duplicate drift. |

## Proposed changes (ordered, validatable)

1. `check_collisions` id6 scan (E-01). 2. setid collision extension (E-02). 3. wire into `check_types` + tests (E-03).

## Deferred / out of scope (with reason)

- Engine core: Order 01 (done). `--legacy`/stale message/ipd-lint integration: Order 03. CLI wiring: awcmdsurf.
- Whitelisting a deliberately cross-type setid: not now; surfaced as drift the maintainer can address later.

## Scope check

- Over-scope: none - one collision sub-check + its tests.
- Under-scope: none - id6 (cross-tree) + setid collisions both covered and wired into `all`.

## Required tests / validation

`tests/test_check_engine.py::CollisionTests` (E-03, four methods) + the full serial suite. Each V pins one E.

## Spec / documentation sync

No doc change. No spec transition (orchestrator advances the spec).

## Open questions

### OQ-01: is a setid intentionally shared across types ever legitimate?

- Blocking: no
- Status: open
- Owner: maintainer (resolve if the check proves too noisy)
- Resolution or deferral rationale: The rule flags a cross-type setid as drift. If the maintainer later wants deliberate cross-type sets, add a whitelist; for now surfacing it is the safer default (uniqueness is the stated goal, item 23). Non-blocking - the check is correct as specified.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `check_collisions` over a fixture with a duplicated id6 across two trees, returning one `check.id6-collision` Drift naming both files.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a `check.setid-collision` Drift for a conflicting-descriptive setid, and no drift for a consistent reuse.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `pytest tests/test_check_engine.py -p no:xdist -q` (CollisionTests passing) + proof `check_types(root,["all"])` runs collisions exactly once + the full serial suite tail.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY
`check_engine.py` + `tests/test_check_engine.py` path-scoped (never `git add -A`), never pushes, and
transitions only after `aw ipd lint --phase pre-transition` conforms and every V is `pass`. Order 02 of
awcheck; depends on Order 01 (the engine).
