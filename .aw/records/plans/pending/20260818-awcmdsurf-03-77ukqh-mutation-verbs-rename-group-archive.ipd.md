# IPD: mutation verbs rename group archive

- Date: 2026-08-18
- Kind: child
- Concern: awcmdsurf Order 03 (spec 20260818-1525-01). Implement the mutating cross-cutting verbs: `aw rename <type> <selector...>` (re-slug/re-name to the grammar, keeping Id), `aw group <type> <selector...> --set S` (assign into a Set), `aw archive <type> <selector...>` (deep-shelve terminal/aged). All default to UPDATING references across the repo (with `--no-refs` to disable) and preview-by-default with `--apply`, routing into the existing backends.
- Scope: cli.py routers into plans_refs/plans_archive/research_refs/research_archive. IN: `rename` -> plans_refs.run_mv/research_refs.run_mv; `group` -> plans_refs.run_set_assign/research_refs.run_set_assign; `archive` -> plans_archive.run_archive/research_archive.run_archive; the default-update-references behavior + `--no-refs`; preview/`--apply`; `--json` where meaningful; `all` fan-out where it makes sense. OUT: read verbs (Order 02), merge/renames-of-list/todo (Order 04), removals (Order 05); the full selector grammar (Set E). Reference-updating already exists inside plans_refs (it rewrites citations); this Order EXPOSES it as the default and adds `--no-refs`.
- Status: reviewed
- Set: awcmdsurf
- Order: 3
- Highest E allocated: 05
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 77ukqh

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): from spec 20260818-1525-01 + investigation (plans_refs.run_mv:404, run_set_assign:377; plans_archive.run_archive:168; research_refs.run_mv:286, run_set_assign:261; research_archive.run_archive:227).
- 2026-08-18 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified citations against plans_refs.py:377/404, plans_archive.py:168, research_refs.py:261/286, and research_archive.py:227; structural lint conforming; no findings; no blocking open questions; GO - PENDING HUMAN APPROVAL.

## Goal

Make the mutation verbs real and consistent: rename/group/archive operate over selected artifacts of a
type, keep the immutable Id, update references by default (`--no-refs` to opt out), and preview unless
`--apply`. They route into the existing plans_refs/plans_archive/research_refs/research_archive backends;
the new surface is the consistent verb+flag shape, not new mutation logic.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: rename + group

- [ ] E-01 Implement `_run_rename(args, term)`: resolve type + selector(s); dispatch to the backend `rename` entrypoint (`plans_refs.run_mv`, `research_refs.run_mv`), passing `--slug`/`--order`/`--set`/`--dir`/`--apply`. Add `--no-refs` (default: refs ARE updated); when NOT set, ensure the backend's reference-rewrite runs (plans_refs already rewrites citations via apply_reference_rewrites); when `--no-refs`, skip the rewrite. Multiple selectors rename each in turn.
  - Depends on: none
  - Expected outcome: `aw rename plans <id6> --slug x --apply` == old `aw plans-mv ... --apply` AND updates references by default; `--no-refs` renames the file only.
  - Execution state: pending
- [ ] E-02 Implement `_run_group(args, term)`: resolve type + selector(s); dispatch to `plans_refs.run_set_assign`/`research_refs.run_set_assign` with `--set`(required)/`--order`/`--rename`/`--apply` and the same `--no-refs` default-on reference update. `all` is NOT supported for group (grouping is per-type by design) - report exit 2 for `all`.
  - Depends on: none
  - Expected outcome: `aw group plans <id6...> --set s --apply` == old `aw plans-set-assign ... --set s --apply`, updating refs by default.
  - Execution state: pending

### Task group 2: archive

- [ ] E-03 Implement `_run_archive(args, term)` as the GENERAL router (generalizing the existing research-only `archive` from Order 01): resolve type + selector(s); dispatch to `plans_archive.run_archive` (plans) / `research_archive.run_archive` (research), passing target/`--dir`/`--apply` (+ research's `--keep`). `all`/plans/research supported; a type without an archive backend reports "archive not supported for <type>". Preview by default; `--apply` writes.
  - Depends on: none
  - Expected outcome: `aw archive plans <target> --apply` == old `aw plans-archive ... --apply`; `aw archive research ... --apply` == old top-level `aw archive`; `aw archive all` previews both.
  - Execution state: pending

### Task group 3: reference-update default + tests

- [ ] E-04 Ensure the reference-update default is CONSISTENT across rename + group (spec R: "update all references by default; --no-refs to disable"). Verify plans_refs already performs the citation rewrite (apply_reference_rewrites); wire `--no-refs` to bypass it; document the behavior in the verb help. For research, confirm research_refs' reference handling and match the default. Add a guard test that a rename WITHOUT `--no-refs` rewrites a citing document and WITH `--no-refs` leaves it.
  - Depends on: E-01,E-02
  - Expected outcome: a fixture with doc B citing plan A: `aw rename plans A --slug x --apply` rewrites B's citation; `--no-refs` leaves B untouched.
  - Execution state: pending
- [ ] E-05 Add `tests/test_awcmdsurf_mutation_verbs.py` covering rename/group/archive over a fixture (preview vs `--apply`, `--no-refs` on/off, `all` where supported, unsupported (type,verb) exit 2, Id preserved through rename per the awnaming vf03z3 fix). Run the FULL serial suite and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04
  - Expected outcome: new module passes; full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Backends: `plans_refs.run_mv` (plans_refs.py:404), `plans_refs.run_set_assign` (:377), `plans_archive.run_archive` (plans_archive.py:168), `research_refs.run_mv` (research_refs.py:286), `research_refs.run_set_assign` (:261), `research_archive.run_archive` (research_archive.py:227).
- plans_refs ALREADY updates citations on rename/set-assign (apply_reference_rewrites, plan_reference_rewrites); the awnaming Set fixed rename to preserve Id/Order/Date (RenamePlan.order). So `rename` already keeps Id; `--no-refs` is the new opt-out.
- Preview-by-default + `--apply` is the established pattern across all these backends.
- The `all` fan-out makes sense for archive (sweep terminal/aged across types) but NOT for group (per-type Set assignment); rename over `all` is unusual - support per-type, treat `all` as exit-2 "specify a type" for rename+group.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | Reference rewrite already exists in plans_refs. | `--no-refs` is the new lever; default-on matches spec + existing behavior. |
| F2 | Id/Order/Date preserved by the awnaming fix. | rename is safe; the test just re-asserts preservation. |
| F3 | group/rename over `all` is ill-defined. | Report exit 2 with a "specify a type" message rather than guess. |
| F4 | archive already exists (research). | Order 01 stood up the general parser; this Order fills the plans branch + fan-out. |

## Proposed changes (ordered, validatable)

1. `_run_rename` + `--no-refs` (E-01). 2. `_run_group` (E-02). 3. `_run_archive` general router (E-03). 4. Consistent ref-update default + guard (E-04). 5. Tests + suite (E-05).

## Deferred / out of scope (with reason)

- Read verbs: Order 02. list/todo/merge: Order 04. Removals: Order 05.
- Full selector grammar: Set E (awselect); Order 03 uses the minimal selector.

## Scope check

- Over-scope: none - only the three mutation verbs + the ref-update default.
- Under-scope: none - rename/group/archive fully functional with preview/apply + refs.

## Required tests / validation

`tests/test_awcmdsurf_mutation_verbs.py` (E-05) + full serial suite. Each V-item pins one E.

## Spec / documentation sync

No AGENTS.md change here (Order 05). Spec stays draft.

## Open questions

### OQ-01: should `rename`/`group` accept `all`, or require a concrete type?

- Blocking: no
- Status: open
- Owner: opencode (resolve during execution)
- Resolution or deferral rationale: Recommendation: require a concrete type for rename+group (a cross-type mass rename is dangerous and rarely intended); `all` -> exit 2 with guidance. archive supports `all` (a sweep is the intent). Non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw rename plans <id6> --slug x --apply` renaming + updating a reference; parity with old `plans-mv`; `--no-refs` leaves references.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `aw group plans <id6...> --set s --apply`; parity with old `plans-set-assign`; `all` -> exit 2.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `aw archive plans <target> --apply` (parity with plans-archive) + `aw archive research ...` (parity with old archive) + `aw archive all` preview.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the fixture test: rename rewrites a citing doc by default; `--no-refs` does not.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the full serial suite tail showing the new module + no regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(opencode Opus 4.8, or Gemini via `agy` with opencode owning verification + commits) performs each E,
verifies each V with pasted evidence, commits path-scoped, never pushes, and transitions only after
`aw ipd lint --phase pre-transition` conforms and every V is `pass`. Order 03 of awcmdsurf; depends on 01, 02.
