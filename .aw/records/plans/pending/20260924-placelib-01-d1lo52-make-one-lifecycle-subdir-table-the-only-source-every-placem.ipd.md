# IPD: Make one lifecycle-subdir table the only source every placement consumer reads

- Date: 2026-09-24
- Kind: child
- Concern: Which record types have status subdirectories, and what those subdirectories are, is still written out as independent string literals in several modules; `record_placement` (r9uvwc) unified the WRITERS but reads these literals rather than owning them, so a status added to one copy silently desyncs the others.
- Scope: IN: a new dependency-free leaf module `agent_workflows/lifecycle_dirs.py` holding the one table; every literal copy of a lifecycle-subdir set re-derived from it (`layout.build_default_layout`, `backlog.STATUS_DIRS`, `plans.DISPOSITION_DIRS`, `engine.PLAN_LIFECYCLE_SUBDIRS`/`PROMPT_LIFECYCLE_SUBDIRS`, `ipd_lint._dir_of`, `attention_contract.SPEC_STATUSES` and its two re-listings in `status_set.TYPE_STATUSES`/`ipd_schema._ITEM_DEP_STATE_STATUSES`, and the fallback/valid-subdir literals inside `record_placement`); the two creation verbs that still hardcode a subdir (`backlog` new, `ipd_authoring` scaffold) take the subdir from `record_placement.target_subdir`; a consumer-agreement test plus an AST drift guard. OUT: changing any status vocabulary or any file location; the plans many-to-one status mapping itself (already owned by `record_placement.target_subdir`); promoting location-equals-status to a fail-closed `aw check` rule.
- Scope-Paths: agent_workflows/lifecycle_dirs.py, agent_workflows/layout.py, agent_workflows/backlog.py, agent_workflows/plans.py, agent_workflows/engine.py, agent_workflows/ipd_lint.py, agent_workflows/record_placement.py, agent_workflows/attention_contract.py, agent_workflows/status_set.py, agent_workflows/ipd_schema.py, agent_workflows/ipd_authoring.py, tests/test_lifecycle_dirs.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- Id: d1lo52
- From-Backlog: x9qv9q
- Set: placelib
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog x9qv9q; re-measured that r9uvwc's `record_placement` already replaced the status_set if/elif chain and the `specs new` flat-root write, and that an AST scan of `agent_workflows/*.py` still finds 12 independent literal copies of a lifecycle-subdir set across 9 modules.

## Goal

Own "which record types have status subdirectories and what they are" in exactly one table, make every consumer derive from it, and add a test that fails if any consumer disagrees with the table or if a new literal copy appears.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the table and its guard

- [ ] E-01 Create `agent_workflows/lifecycle_dirs.py`, importing nothing from `agent_workflows`, defining `LIFECYCLE_SUBDIRS: Mapping[str, Tuple[str, ...]]` (a `types.MappingProxyType`) with exactly four keys in the current on-disk order: `plans` and `prompts` = `("pending", "executed", "superseded", "not-executed", "reusable")`, `specs` = the nine `attention_contract.SPEC_STATUSES` values in their current listed order, `backlog` = `("open", "graduated", "blocked", "parked", "done")`; plus `subdirs_for(record_type) -> Tuple[str, ...]` returning `()` for any other type, and `PLANS_DONE_ALIAS = "done"` with a comment that it is a legacy read alias, not a subdir.
  - Depends on: none
  - Expected outcome: `python3 -c "from agent_workflows import lifecycle_dirs as L; print(dict(L.LIFECYCLE_SUBDIRS))"` prints the four rows; `grep -n "^from agent_workflows\|^import agent_workflows" agent_workflows/lifecycle_dirs.py` prints nothing.
  - Execution state: pending

- [ ] E-02 Add `tests/test_lifecycle_dirs.py` with two classes. `ConsumerAgreementTests`: for EVERY name in `layout.build_default_layout().record_classes`, assert `record_classes[name].lifecycle_subdirs == subdirs_for(name)` and `record_placement.has_lifecycle_subdirs(name) == bool(subdirs_for(name))`; for every type with subdirs and every subdir `d`, assert `record_placement.target_subdir(type, d) == d`; assert `backlog.STATUS_DIRS == LIFECYCLE_SUBDIRS["backlog"]`, `set(plans.DISPOSITION_DIRS) == set(LIFECYCLE_SUBDIRS["plans"]) | {"done"}`, `engine.PLAN_LIFECYCLE_SUBDIRS == LIFECYCLE_SUBDIRS["plans"]`, `engine.PROMPT_LIFECYCLE_SUBDIRS == LIFECYCLE_SUBDIRS["prompts"]`, `attention_contract.SPEC_STATUSES == frozenset(LIFECYCLE_SUBDIRS["specs"])`, `status_set.TYPE_STATUSES["specs"] == set(LIFECYCLE_SUBDIRS["specs"])`, `ipd_schema._ITEM_DEP_STATE_STATUSES["spec"] == frozenset(LIFECYCLE_SUBDIRS["specs"])`, and `ipd_lint._dir_of(Path("x") / d / "p.ipd.md") == d` for every plans subdir. `LiteralDriftGuardTests`: `ast`-walk every `agent_workflows/**/*.py` except `lifecycle_dirs.py`, and fail naming `file:line` for any `Tuple`/`List`/`Set` of only `str` constants whose value set is a superset of any table row with at most one extra element (the same predicate as the probe `/tmp/opencode/g2/probe-placelib/lit.py`, so wider status vocabularies such as the 11-element `status_set.TYPE_STATUSES["plans"]` do not trip it). Run it BEFORE E-03..E-06 so it fails.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_lifecycle_dirs.py` FAILS at this point, and the drift guard's message lists the literal sites (12 at authoring time).
  - Execution state: pending

### Task group 2: move every consumer onto the table

- [ ] E-03 In `layout.build_default_layout`, replace the four `lifecycle_subdirs=(...)` literals for `plans`, `specs`, `prompts`, `backlog` with `lifecycle_subdirs=_LD.subdirs_for("<name>")` (`from agent_workflows import lifecycle_dirs as _LD`, a leaf, so layout stays import-light). In `engine`, set `PLAN_LIFECYCLE_SUBDIRS = _LD.LIFECYCLE_SUBDIRS["plans"]` and `PROMPT_LIFECYCLE_SUBDIRS = _LD.LIFECYCLE_SUBDIRS["prompts"]`.
  - Depends on: E-02
  - Expected outcome: `python3 -m agent_workflows layout --json` (in-process model source; the emitted `.aw/system/layout.json` is gitignored) prints output byte-identical to the pre-change capture.
  - Execution state: pending

- [ ] E-04 Set `backlog.STATUS_DIRS = _LD.LIFECYCLE_SUBDIRS["backlog"]` (keeping `STATUSES = frozenset(STATUS_DIRS)`), `plans.DISPOSITION_DIRS = _LD.LIFECYCLE_SUBDIRS["plans"] + (_LD.PLANS_DONE_ALIAS,)`, and `attention_contract.SPEC_STATUSES = frozenset(_LD.LIFECYCLE_SUBDIRS["specs"])`; replace the `status_set.TYPE_STATUSES["specs"]` literal with `set(_AC.SPEC_STATUSES)` and the `ipd_schema._ITEM_DEP_STATE_STATUSES["spec"]` literal with `_AC.SPEC_STATUSES`, each with a one-line comment in the style of the existing "bklgrad Order 01 (v58bvy)" derivation comments.
  - Depends on: E-02
  - Expected outcome: `python3 -c` printing `backlog.STATUS_DIRS`, `plans.DISPOSITION_DIRS`, `sorted(attention_contract.SPEC_STATUSES)` shows values equal to the pre-change capture, in the same order.
  - Execution state: pending

- [ ] E-05 In `ipd_lint._dir_of`, iterate `_LD.LIFECYCLE_SUBDIRS["plans"]` instead of the literal `("pending", "executed", "superseded", "not-executed", "reusable")`. In `record_placement`, replace the `has_lifecycle_subdirs` fallback `record_type in ("plans", "prompts", "backlog", "specs")` with `bool(_LD.subdirs_for(record_type))`, and replace the `valid_subdirs` expression (`set(_BL.STATUS_DIRS) if record_type == "backlog" else set(_AC.SPEC_STATUSES)`) with `set(_LD.subdirs_for(record_type))`.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_record_placement.py tests/test_ipd_lint.py` passes unchanged.
  - Execution state: pending

- [ ] E-06 In `backlog` creation (the statement `dest = _resolve_backlog_root(repo_root) / status / filename`), take the subdir from `record_placement.target_subdir("backlog", status)` while keeping `_resolve_backlog_root` as the type dir (so the neither-tree-exists fallback to `.agents/backlog` is unchanged). In `ipd_authoring` scaffold (the statement `pending = repo_root / ".aw" / "records" / "plans" / "pending"`), replace the literal `"pending"` with `record_placement.target_subdir("plans", "to-review")`.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_backlog.py` passes, and a scratch-repo `aw backlog new` and `aw ipd scaffold --apply` write to `open/` and `pending/` respectively, same as before.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-07 Run `python3 -m pytest -o addopts="" tests/test_lifecycle_dirs.py tests/test_layout.py tests/test_record_placement.py` and re-run the authoring probe `/tmp/opencode/g2/probe-placelib/lit.py` (or its in-test equivalent) to confirm the only remaining hits are in `lifecycle_dirs.py`.
  - Depends on: E-03, E-04, E-05, E-06
  - Expected outcome: all pass; the probe prints only `agent_workflows/lifecycle_dirs.py` lines.
  - Execution state: pending

- [ ] E-08 Run the bare suite `python3 -m pytest`.
  - Depends on: E-07
  - Expected outcome: summary line shows 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Derive, never re-list: `status_set.TYPE_STATUSES["backlog"]` and `ipd_schema._ITEM_DEP_STATE_STATUSES["backlog"]` already derive from `backlog.STATUSES` with comments citing "GUIDING_PRINCIPLES P8" after a hardcoded copy desynced (`graduated`). This plan extends that exact pattern.
- `attention_contract` is deliberately "dependency-light" (its own comment); the new module must be a leaf so `attention_contract`, `layout`, `backlog` and `plans` can all import it without a cycle.
- Tests run bare (`python3 -m pytest`); narrowed runs clear addopts with `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Re-measured at HEAD `cfc7f5c1` against the backlog item's claims:

| Backlog claim | Now | Evidence |
|---|---|---|
| status_set if/elif placement chain | FIXED by r9uvwc | `status_set` calls `record_placement.resolve_transition_path` ("Determine destination path using the shared record placement library") |
| `specs new` writes to flat root | FIXED by r9uvwc | `specs` calls `record_placement.resolve_creation_path("specs", "draft", ...)` |
| specs have no subdir knowledge | FALSE now | `layout` specs `lifecycle_subdirs` lists the nine statuses |
| nothing answers "which types have subdirs" | PARTLY: `record_placement.has_lifecycle_subdirs` answers, but by reading `layout`, with its own literal fallback | `record_placement.has_lifecycle_subdirs` |

The four sources of truth the task names still exist independently: (1) `backlog.STATUS_DIRS`, (2) `plans.DISPOSITION_DIRS`, (3) `attention_contract.SPEC_STATUSES`, (4) `layout.build_default_layout` `lifecycle_subdirs`. The probe also found further copies: `engine.PLAN_LIFECYCLE_SUBDIRS`, `engine.PROMPT_LIFECYCLE_SUBDIRS`, `ipd_lint._dir_of`, `ipd_schema._ITEM_DEP_STATE_STATUSES["spec"]`, `status_set.TYPE_STATUSES["specs"]`, plus two literal-set expressions inside `record_placement`. The only thing tying them together today is `tests/test_layout.py` `test_lifecycle_subdirs_match_the_live_status_dirs`, which hardcodes the plans set a fifth time and checks only layout.

## Proposed changes (ordered, validatable)

1. Leaf table module (E-01).
2. Agreement test plus AST drift guard, shown failing first (E-02).
3. Re-derive each consumer (E-03 layout/engine, E-04 vocab modules, E-05 lint/placement, E-06 creation verbs).
4. Prove zero remaining literals and a green suite (E-07, E-08).

## Deferred / out of scope (with reason)

- A fail-closed `aw check` rule that a record's directory equals its status: separate enforcement concern, out of this item's scope.
  - Carrier-Declined: not requested by x9qv9q; r9uvwc's Scope already names it OUT, and no defect is measured today.
- Simplifying `tests/test_layout.py` `test_lifecycle_subdirs_match_the_live_status_dirs` to read the table: left as-is because it stays correct and is subsumed by `ConsumerAgreementTests`.
  - Carrier-Declined: redundant but harmless; removing it gains nothing measurable.

## Scope check

- Over-scope: E-04 also re-derives two spec-status re-listings (`status_set`, `ipd_schema`); they are copies of the same nine-element set and the drift guard would flag them, so leaving them would make E-02 unpassable.
- Under-scope: none known; the drift guard is what makes this claim checkable rather than asserted.

## Required tests / validation

New `tests/test_lifecycle_dirs.py` (agreement across every layout record class, plus AST drift guard), shown failing before migration; existing `tests/test_layout.py`, `tests/test_record_placement.py`, `tests/test_backlog.py`, `tests/test_ipd_lint.py` pass unchanged as the byte-identical-behavior regression bar; bare suite green.

## Spec / documentation sync

N/A: spec `kw5y2s` documents the `lifecycle_subdirs` JSON emitted by the layout; E-03 keeps that output byte-identical, so no spec text changes and no `.spec.md` is in Scope-Paths.

## Open questions

### OQ-01: Should the drift guard's superset-plus-one predicate be widened later?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Resolved from repo evidence: the predicate as probed flags exactly the 12 copies and none of the wider status vocabularies (`status_set.TYPE_STATUSES["plans"]` has 11 elements against a 5-element row), so it catches a re-listed copy without false positives today. A literal spelling that evades it (for example built by concatenation) is accepted as a known limit; the agreement tests still pin every named consumer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the output of `python3 -c "from agent_workflows import lifecycle_dirs as L; print(dict(L.LIFECYCLE_SUBDIRS)); print(L.subdirs_for('research'))"` showing the four rows and `()`, and the empty output of `grep -n "^from agent_workflows\|^import agent_workflows" agent_workflows/lifecycle_dirs.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the FAILING output of `python3 -m pytest -o addopts="" tests/test_lifecycle_dirs.py` run after E-01 and before E-03..E-06, showing `LiteralDriftGuardTests` listing the `file:line` literal sites and a nonzero failed count.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `diff` of `python3 -m agent_workflows layout --json` captured before and after E-03 (empty), and `python3 -c "from agent_workflows import engine as E; print(E.PLAN_LIFECYCLE_SUBDIRS, E.PROMPT_LIFECYCLE_SUBDIRS)"` showing the five-element tuples.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a before/after `python3 -c` print of `backlog.STATUS_DIRS`, `plans.DISPOSITION_DIRS`, `sorted(attention_contract.SPEC_STATUSES)`, `sorted(status_set.TYPE_STATUSES['specs'])`, `sorted(ipd_schema._ITEM_DEP_STATE_STATUSES['spec'])`, identical in value and order.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the pass summary of `python3 -m pytest -o addopts="" tests/test_record_placement.py tests/test_ipd_lint.py`, and `git diff agent_workflows/ipd_lint.py agent_workflows/record_placement.py` showing no literal subdir tuple remains.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the pass summary of `python3 -m pytest -o addopts="" tests/test_backlog.py`, and from a scratch repo under `/tmp` the paths printed by `aw backlog new ... --apply` (under `backlog/open/`) and `aw ipd scaffold ... --apply` (under `plans/pending/`).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the pass summary of `python3 -m pytest -o addopts="" tests/test_lifecycle_dirs.py tests/test_layout.py tests/test_record_placement.py` and the probe output showing only `agent_workflows/lifecycle_dirs.py` hits.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the final summary line of the bare `python3 -m pytest` run showing `passed` and no `failed`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Commit through `aw commit <this plan> -- <Scope-Paths>`; never push. Move this plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every V item carries pasted evidence. Setting x9qv9q to `done` is a separate step after execution, not part of authoring.
