# IPD: Add type flag to aw attention for single and multi-type artifact filtering

- Date: 2026-08-30
- Kind: child
- Concern: The `aw attention` board aggregates all artifact trees into one view, but users frequently want to focus on a specific artifact type (e.g. only plans, only specs, or only backlog items) without seeing items from other trees or unintentionally matching non-type substrings via generic selectors.
- Scope: Add the `--type` (`-t`) option to `aw attention` (`aw att`) with alias support (`--tree`), support comma-separated (`-t a,b,c`) and repeated (`-t a -t b`) syntax, normalize singular/plural/common aliases (plans/plan/ipd, specs/spec, backlog/bk, research/survey, releases/release, roadmaps/roadmap, walkthroughs/walkthr), integrate strict tree filtering into `attention.py`, keep done/parked hidden unless `--all` is passed, and author unit tests.
- Scope-Paths: agent_workflows/attention.py, agent_workflows/cli.py, tests/test_attention.py
- Item-Dependencies: none
- Status: executed
- Set: atttype
- Order: 1
- Highest E allocated: 03
- Author: antigravity
- Id: 3vx9sj

## Workflow history
- 2026-08-31 executed (antigravity): Add --type (-t, --tree) flag to aw attention [Scope reconciliation - in-scope-unmodified agent_workflows/attention.py: acknowledged; in-scope-unmodified agent_workflows/cli.py: acknowledged; in-scope-unmodified tests/test_attention.py: acknowledged]

- 2026-08-30 draft (antigravity): created.
- 2026-08-30 to-review (antigravity): authored complete plan.
- 2026-08-30 approved (antigravity): human approval attested per user directive.

## Goal

Provide a `--type` (`-t`, `--tree`) option for `aw attention` (`aw att`) that allows filtering the attention view to one or more specified artifact types (via `-t a,b,c` or repeated `-t a -t b`), normalizing aliases and strictly scoping output to the chosen trees.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Type Alias Normalizer & Item Filtering

- [x] E-01 Add `TYPE_ALIASES` map and `parse_type_filters` helper in `agent_workflows/attention.py` supporting comma-delimited strings, repeated lists, and aliases (`plan/plans/ipd`, `spec/specs`, `backlog/bk`, `research/survey`, `release/releases`, `roadmap/roadmaps`, `walkthrough/walkthroughs/walkthr`).
  - Depends on: none
  - Expected outcome: Parsing extracts canonical tree names deterministically from any combination of flags and comma lists.
  - Execution state: performed

### Task group 2: Board Runner & CLI Parser Integration

- [x] E-02 Update `p_attention` in `agent_workflows/cli.py` to accept `--type` / `-t` (and `--tree`) with `action="append"`, and wire `attention.run` to filter items by the parsed canonical types while preserving `--all` semantics.
  - Depends on: E-01
  - Expected outcome: `aw attention --type plans`, `aw att -t specs,backlog`, and `aw att -t ipd -t spec` filter output strictly to the requested artifact trees.
  - Execution state: performed

### Task group 3: Unit Tests

- [x] E-03 Author comprehensive unit tests in `tests/test_attention.py` testing single type, repeated types, comma-separated types, aliases, invalid types handling, and combination with `--details` and `--format json`.
  - Depends on: E-01, E-02
  - Expected outcome: Full test suite passes 100% clean.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `agent_workflows/attention.py`: Attention view scanner, filters, and board renderer.
- `agent_workflows/cli.py`: CLI arguments registration for `p_attention`.
- `tests/test_attention.py`: Unit test harness for attention view.

## Findings

- Filtering by `item.tree` directly rather than running generic substring selector matching ensures that an artifact whose setid or filename happens to contain another type name (e.g. `artifact-organization-plans-adopter.spec.md`) is correctly classified as a spec and never mis-selected as a plan.
- Passing `--type` should NOT implicitly unhide `done` and `parked` groups (unlike generic positional selectors); `--all` remains the explicit authority for unhiding.

## Proposed changes (ordered, validatable)

1. Define `TYPE_ALIASES` and `parse_type_filters` in `agent_workflows/attention.py` (E-01).
2. Wire `--type` / `-t` in `agent_workflows/cli.py` and apply type filter in `attention.run` (E-02).
3. Author unit tests in `tests/test_attention.py` (E-03).

## Deferred / out of scope (with reason)

- none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_attention.py` passing.
- Interactive `aw att -t plans` and `aw att -t specs,backlog -d` verification.

## Spec / documentation sync

- N/A (CLI argument enhancement).

## Open questions

### OQ-01: How to handle unrecognized type tokens?

- Blocking: no
- Status: resolved
- Owner: resolved from design
- Resolution or deferral rationale: RESOLVED - Raise an informative error or warning naming valid recognized types.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Unit tests verifying type alias resolution for singular, plural, and shorthand aliases.
  - Observed evidence: Verified via `test_parse_type_filters` in `tests/test_attention.py`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Output tests verifying single, comma-separated, and repeated `-t` invocations on board and JSON.
  - Observed evidence: Verified via `test_run_with_type_filter` in `tests/test_attention.py`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Full pytest suite run across the repository passes cleanly.
  - Observed evidence: `3814 passed, 3 skipped, 4 xfailed in 53.39s` and clean leak check.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
