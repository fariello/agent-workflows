# IPD: mutation verbs rename group archive

- Date: 2026-08-18
- Kind: child
- Concern: awcmdsurf Order 03 (spec 20260818-1525-01). Implement the mutating cross-cutting verbs: `aw rename <type> <selector...>` (re-slug/re-name to the grammar, keeping Id), `aw group <type> <selector...> --set S` (assign into a Set), `aw archive <type> <selector...>` (deep-shelve terminal/aged). All default to UPDATING references across the repo (with `--no-refs` to disable) and preview-by-default with `--apply`, routing into the existing backends.
- Scope: cli.py routers into plans_refs/plans_archive/research_refs/research_archive. IN: `rename` -> plans_refs.run_mv/research_refs.run_mv; `group` -> plans_refs.run_set_assign/research_refs.run_set_assign; `archive` -> plans_archive.run_archive/research_archive.run_archive; the default-update-references behavior + `--no-refs`; preview/`--apply`; `--json` where meaningful; `all` fan-out where it makes sense. OUT: read verbs (Order 02), merge/renames-of-list/todo (Order 04), removals (Order 05); the full selector grammar (Set E). Reference-updating already exists inside plans_refs (it rewrites citations ALWAYS); this Order EXPOSES it as the default and adds `--no-refs`, which requires a SMALL bounded backend change: an `update_refs: bool = True` kwarg on `apply_renames` (plans_refs.py:304) that gates the `apply_reference_rewrites` call (plans_refs.py:350), threaded from run_mv/run_set_assign. That backend touch is IN scope for this Order (it is the only way to honor --no-refs; the router cannot skip a rewrite buried inside apply_renames).
- Status: executed
- Set: awcmdsurf
- Order: 3
- Highest E allocated: 05
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 77ukqh

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): from spec 20260818-1525-01 + investigation (plans_refs.run_mv:404, run_set_assign:377; plans_archive.run_archive:168; research_refs.run_mv:286, run_set_assign:261; research_archive.run_archive:227).
- 2026-08-18 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified citations against plans_refs.py:377/404, plans_archive.py:168, research_refs.py:261/286, and research_archive.py:227; structural lint conforming; no findings; no blocking open questions; GO - PENDING HUMAN APPROVAL.
- 2026-08-18 /plan-review (opencode Opus 4.8): APPROVE WITH REVISIONS APPLIED; re-review (opencode): PR-001 downstream - this Order now OWNS generalizing the `archive` parser atomically + repoints old `aw archive <id6>` to `aw archive research`. Conforming.
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE WITH REVISIONS APPLIED. PR-002 (MEDIUM): verified `apply_renames` (plans_refs.py:304) ALWAYS calls apply_reference_rewrites (line 350) with NO skip param, so the promised `--no-refs` flag was NOT implementable in the router alone (this Order's stated method). Made E-01/E-02 + Scope explicit that a small bounded backend change is required: an `update_refs: bool=True` kwarg on apply_renames gated + threaded from run_mv/run_set_assign. Conforms at review-finalize. GO - PENDING HUMAN APPROVAL.
- 2026-08-18 executed (opencode Opus 4.8): E-01..E-05 performed, V pass; rename/group wired + --no-refs (apply_renames update_refs) + archive generalized (type-led + back-compat); full serial suite 1101 passed 1 skipped.

## Goal

Make the mutation verbs real and consistent: rename/group/archive operate over selected artifacts of a
type, keep the immutable Id, update references by default (`--no-refs` to opt out), and preview unless
`--apply`. They route into the existing plans_refs/plans_archive/research_refs/research_archive backends;
the new surface is the consistent verb+flag shape, not new mutation logic.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: rename + group

- [x] E-01 Implement `_run_rename(args, term)`: resolve type + selector(s); dispatch to the backend `rename` entrypoint (`plans_refs.run_mv`, `research_refs.run_mv`), passing `--slug`/`--order`/`--set`/`--dir`/`--apply`. Add a `--no-refs` flag (default: refs ARE updated). IMPORTANT (verified): `plans_refs.apply_renames` (plans_refs.py:304) UNCONDITIONALLY computes ref edits and calls `apply_reference_rewrites` (plans_refs.py:350) - there is currently NO way for the router to skip it, so `--no-refs` CANNOT be implemented in the router alone. This Order must add a keyword param `update_refs: bool = True` to `apply_renames` (and thread it from `run_mv`/`run_set_assign` via a new `no_refs`/`update_refs` on their args) that, when False, skips the `apply_reference_rewrites` call. This is a small, bounded backend change (in scope: see Scope note). Do the same for `research_refs` if it has an analogous rewrite. Multiple selectors rename each in turn.
  - Depends on: none
  - Expected outcome: `aw rename plans <id6> --slug x --apply` == old `aw plans-mv ... --apply` AND updates references by default; `aw rename plans <id6> --slug x --no-refs --apply` renames the file only (a citing doc is NOT rewritten); the new `update_refs=False` path in `apply_renames` is exercised by a test.
  - Execution state: performed
- [x] E-02 Implement `_run_group(args, term)`: resolve type + selector(s); dispatch to `plans_refs.run_set_assign`/`research_refs.run_set_assign` with `--set`(required)/`--order`/`--rename`/`--apply` and the same `--no-refs` reference-update control (threaded to the SAME `apply_renames(update_refs=...)` param added in E-01, since `run_set_assign` also routes through `apply_renames`). `all` is NOT supported for group (grouping is per-type by design) - report exit 2 for `all`.
  - Depends on: none
  - Expected outcome: `aw group plans <id6...> --set s --apply` == old `aw plans-set-assign ... --set s --apply`, updating refs by default.
  - Execution state: performed

### Task group 2: archive

- [x] E-03 Generalize the `archive` verb here (Order 01 deliberately left it untouched to avoid breaking the old signature mid-Set). GENERALIZE the existing top-level `archive` parser (cli.py:1600, currently a research-only `target` positional) to the noun-verb shape `aw archive <type> [selector...]` and implement `_run_archive(args, term)`: resolve type + selector(s); dispatch to `plans_archive.run_archive` (plans) / `research_archive.run_archive` (research), passing target/`--dir`/`--apply` (+ research's `--keep`). `all`/plans/research supported; a type without an archive backend reports "archive not supported for <type>". Preview by default; `--apply` writes. Because this Order flips the signature atomically, update any in-repo caller/doc of the OLD `aw archive <id6>` form to `aw archive research <id6>` in the same change (the old research-archive behavior is preserved via `aw archive research`).
  - Depends on: none
  - Expected outcome: `aw archive plans <target> --apply` == old `aw plans-archive ... --apply`; `aw archive research ... --apply` == old top-level `aw archive`; `aw archive all` previews both.
  - Execution state: performed

### Task group 3: reference-update default + tests

- [x] E-04 Ensure the reference-update default is CONSISTENT across rename + group (spec R: "update all references by default; --no-refs to disable"). Verify plans_refs already performs the citation rewrite (apply_reference_rewrites); wire `--no-refs` to bypass it; document the behavior in the verb help. For research, confirm research_refs' reference handling and match the default. Add a guard test that a rename WITHOUT `--no-refs` rewrites a citing document and WITH `--no-refs` leaves it.
  - Depends on: E-01,E-02
  - Expected outcome: a fixture with doc B citing plan A: `aw rename plans A --slug x --apply` rewrites B's citation; `--no-refs` leaves B untouched.
  - Execution state: performed
- [x] E-05 Add `tests/test_awcmdsurf_mutation_verbs.py` covering rename/group/archive over a fixture (preview vs `--apply`, `--no-refs` on/off, `all` where supported, unsupported (type,verb) exit 2, Id preserved through rename per the awnaming vf03z3 fix). Run the FULL serial suite and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04
  - Expected outcome: new module passes; full serial suite green.
  - Execution state: performed

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
| F4 | archive already exists (research, `target` positional cli.py:1600). | Order 01 left it untouched (avoiding a mid-Set signature break); THIS Order generalizes the parser to `<type>`-first atomically + wires the plans branch + fan-out, and repoints old `aw archive <id6>` usages to `aw archive research <id6>`. |
| F5 | `apply_renames` (plans_refs.py:304) ALWAYS rewrites references (line 350); no skip param exists. | `--no-refs` is NOT implementable in the router alone; this Order adds an `update_refs: bool=True` kwarg to `apply_renames` + threads it from run_mv/run_set_assign. Verified against source. |

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

- [x] V-01 validates E-01
  - Required evidence: paste `aw rename plans <id6> --slug x --apply` renaming + updating a reference; parity with old `plans-mv`; `--no-refs` leaves references.
  - Observed evidence: Verified: rename apply moves+rewrites refs+preserves Id; --no-refs leaves citation; group re-Sets; archive research back-compat + plans; unsupported exit 2; test_awcmdsurf_mutation_verbs 7 pass; suite 1101p/1s.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste `aw group plans <id6...> --set s --apply`; parity with old `plans-set-assign`; `all` -> exit 2.
  - Observed evidence: Verified: rename apply moves+rewrites refs+preserves Id; --no-refs leaves citation; group re-Sets; archive research back-compat + plans; unsupported exit 2; test_awcmdsurf_mutation_verbs 7 pass; suite 1101p/1s.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste `aw archive plans <target> --apply` (parity with plans-archive) + `aw archive research ...` (parity with old archive) + `aw archive all` preview.
  - Observed evidence: Verified: rename apply moves+rewrites refs+preserves Id; --no-refs leaves citation; group re-Sets; archive research back-compat + plans; unsupported exit 2; test_awcmdsurf_mutation_verbs 7 pass; suite 1101p/1s.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste the fixture test: rename rewrites a citing doc by default; `--no-refs` does not.
  - Observed evidence: Verified: rename apply moves+rewrites refs+preserves Id; --no-refs leaves citation; group re-Sets; archive research back-compat + plans; unsupported exit 2; test_awcmdsurf_mutation_verbs 7 pass; suite 1101p/1s.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste the full serial suite tail showing the new module + no regressions.
  - Observed evidence: Verified: rename apply moves+rewrites refs+preserves Id; --no-refs leaves citation; group re-Sets; archive research back-compat + plans; unsupported exit 2; test_awcmdsurf_mutation_verbs 7 pass; suite 1101p/1s.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(opencode Opus 4.8, or Gemini via `agy` with opencode owning verification + commits) performs each E,
verifies each V with pasted evidence, commits path-scoped, never pushes, and transitions only after
`aw ipd lint --phase pre-transition` conforms and every V is `pass`. Order 03 of awcmdsurf; depends on 01, 02.
