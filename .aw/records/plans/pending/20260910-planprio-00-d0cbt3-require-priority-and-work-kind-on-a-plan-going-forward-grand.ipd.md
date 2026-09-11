# IPD: Require Priority and Work-Kind on a plan going forward, grandfathering the existing corpus

- Date: 2026-09-10
- Kind: orchestrator
- Concern: `Priority` and `Work-Kind` were added to plans as recognized-but-OPTIONAL, and the maintainer states that permanent optionality was never their intent: they meant optional for LEGACY plans only. Adoption is consequently zero (0 of 104 pending plans carry either field), so the attention board renders an empty Priority column for every plan and the queue cannot be ordered by importance.
- Scope: Make both fields REQUIRED at the ready-to-execute gate for new plans while leaving the terminal corpus exempt, fix the scaffold that never emitted them (the root cause of zero adoption), backfill the 84 pending plans that can inherit from their source backlog item, and decide values for the remaining 20 that have no source. Does NOT change the shared `low|medium|high` vocabulary, does NOT introduce a priority-based sort key, and does NOT touch backlog items, specs or research.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: none
- Status: to-review
- Set: planprio
- Order: 0
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: d0cbt3

## Workflow history

- 2026-09-10 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from a maintainer correction during an `/askme` round. Reviewing plan `b5sfwm`'s question about the `-` clearing sentinel, I reported that 0 of 104 pending plans carry `Priority` or `Work-Kind`. The maintainer replied that they were "pretty sure that there was a time where plans had priority for sure, and some had Work-Kind", and then that their optionality decision "may have been misrecorded. I meant optional for legacy, but I'm pretty sure I did not intend for those fields to be optional going forward." INVESTIGATED, AND THE RECORD SUPPORTS THEM: the fields were genuinely added by Sets `xprio` (Priority, 2026-08-27) and `wkindname` (Work-Kind), both live in `META_RECOGNIZED` today with working `aw ipd set` flags; the phrase "recognized-but-optional" ORIGINATED for a different field (`Scope-Paths`, `3a195178`, 2026-08-23) where a REVIEW chose it explicitly "to avoid breaking every pending plan and the grandfather guarantee", and `Priority` inherited the phrasing BY ANALOGY rather than by a separate decision; the source backlog item `p9o1oo` records the maintainer's own words as "research, plans, specs, more or less everything need a priority" (it says NEED, and says nothing about optional); and the ONLY question ever put to the maintainer in that Set was whether an ABSENT value should render as unprioritized or as an implicit medium, which is a RENDERING question, not a requiredness one. So permanent optionality was an inherited default that no one put to them. HONEST LIMIT, stated because it bounds the claim: commit authorship is uniform across humans and agents in this repository, so this establishes what the artifacts SAY and where the wording came from, not what the maintainer intended; and the absence of a question is weak evidence, not proof.

## Goal

Make a plan's `Priority` and `Work-Kind` load-bearing rather than decorative, so the attention board can order the queue by importance, while leaving the 470 terminal plans untouched and unfailed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: sequence the Set and confirm its shared premise

- [ ] E-01 CONFIRM THE SET'S THREE PREMISES STILL HOLD AT EXECUTION TIME, before any child runs, because all three are counts that move as other agents work. RE-MEASURE AND RECORD: (a) how many pending plans carry `- Priority:` and `- Work-Kind:` (authored: 0 of 104 each); (b) how many pending plans carry a `- From-Backlog:` whose id6 RESOLVES to a backlog item carrying BOTH fields (authored: 84, with 0 dangling and 0 sources missing a field); (c) how many carry no `- From-Backlog:` at all (authored: 20). If (b) has fallen or (c) has grown, Order 02's and Order 03's populations move accordingly and the children must be told, not silently re-scoped.
  DO NOT DERIVE THE COUNTS FROM THIS PLAN. Re-run the measurement; the whole reason this Set exists is that a stated count went unchecked for two weeks.
  - Depends on: none
  - Expected outcome: a recorded three-line measurement with the commands that produced it, and an explicit statement of whether Order 02's and Order 03's populations differ from 84 and 20.
  - Execution state: pending

- [ ] E-02 RETIRE THIS ORCHESTRATOR ONLY WHEN ALL THREE CHILDREN ARE `executed`, and carry no work of its own beyond E-01. The children own every code and record change; this parent holds sequencing and the shared premise. Order 01 MUST land before Order 02 and Order 03, because it is what makes the fields required and emitted; backfilling before the gate exists would write values nothing enforces and leave the root cause (a scaffold that omits both fields) in place.
  - Depends on: E-01
  - Expected outcome: all three children `executed` with their own evidence, and this parent transitioned by the runner or by `aw ipd finalize` without performing any child's work.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | Id | Title | Depends on |
|---|---|---|---|
| 01 | `lkexaw` | Emit both fields on scaffold and enforce them at the ready-to-execute gate | none |
| 02 | `8u6770` | Backfill the 84 pending plans that can inherit from their source backlog item | `executed:lkexaw` |
| 03 | `lc4unl` | Decide and record values for the 20 pending plans with no source item | `executed:lkexaw` |

Orders 02 and 03 are INDEPENDENT of each other and may run in either order or concurrently; both depend on Order 01.

## Completion criteria (the whole Set is done only when)

1. A newly scaffolded plan carries both fields, and a plan reaching the ready-to-execute gate without them is REFUSED with a message naming the fix.
2. The 470 terminal plans are unaffected: `aw check` and `aw ipd lint` report no new finding against any plan in `executed/`, `superseded/` or `not-executed/`.
3. Every pending plan carries both fields with a value in the shared vocabulary, or carries the legacy exemption where Order 03 records that no value could be justified.
4. `aw att --type plan` renders a non-empty Priority column.
5. The bare suite passes, with the actual summary line pasted and compared against a baseline established BEFORE the first edit.

## Cross-IPD validation

Order 01's gate must be exercised against a plan from EACH disposition (pending, and one terminal) to prove the grandfather boundary is the disposition and not the date. Orders 02 and 03 must both re-run `aw check plans` afterwards and show no new diagnostic class.

## Deferred / out of scope (with reason)

- CHANGING THE VOCABULARY. `low|medium|high` is shared with backlog items by deliberate decision (source item `p9o1oo` rejected a 7-level scale as producing inconsistent assignment and a noisier board). Out of scope.
- INTRODUCING A PRIORITY-BASED SORT KEY. The `xprio` orchestrator's OQ-01 explicitly decided this Set's ancestor would not add one, and the shared sort remains attention-class/path/id. A sort key is a separate decision.
- SPECS AND RESEARCH. `xprio` gave those types the same optional field; whether they should also become required is the same question one level out, and is NOT decided here. Note this deliberately leaves an asymmetry that a later reader may want resolved.
- THE `-` CLEARING SENTINEL ON `aw backlog set`, which is plan `b5sfwm`'s own blocking question and is where this investigation started. Untouched.
- BACKFILLING TERMINAL PLANS. Their content is immutable by policy; the grandfather exemption exists precisely so they need no edit.

## Scope check

- Over-scope: none. This parent declares only the plans tree and performs no code change; each child declares its own paths.
- Under-scope: the Set does not make specs or research required (deferred above), and does not add the sort key that would make a populated Priority column maximally useful.

## Required tests / validation

Each child owns its own tests. Establish the suite baseline by running `python3 -m pytest` bare BEFORE the first edit and paste that output; no baseline figure is stated in this Set deliberately, because an unverified count is what produced this Set in the first place.

## Spec / documentation sync

Order 01 must state whether any spec describes these fields as optional. NOT YET MEASURED at authoring, and it must not be assumed absent: `xprio` amended the research frontmatter contract and the spec contract, so a spec may well carry the optionality claim. If one does, Order 01 declares that `.spec.md` in its own `Scope-Paths` and amends it in the same change, per the repository rule that a plan changing behavior a spec describes carries the amendment with it.

## Open questions

### OQ-01: Should the requirement also extend to specs and research, which `xprio` gave the same optional field?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DELIBERATELY OUT OF SCOPE HERE AND RAISED SO THE ASYMMETRY IS NOT SILENT. `xprio` added the same recognized-but-optional `Priority` to plans, specs AND research in one Set, so making it required for plans alone leaves the other two types where they are. That may be correct, since a spec and a research report are not queue items in the way a plan is, and the maintainer's original words were about prioritizing work. Non-blocking because this Set is coherent and complete for plans on its own; answering it later costs a separate Set rather than a rework of this one.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: the runner retires an orchestrator from child status. Do not fabricate an independent implementation checkpoint for this file.

- [ ] V-01 validates E-01
  - Required evidence: paste the three re-measured counts with the exact commands that produced them, and state explicitly whether they match the authored 0/104, 84 and 20. If any differs, paste the statement given to the affected child.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste each child's `- Status:` line read from its own file showing all three `executed`; paste `git diff --stat` over THIS parent's own commits showing it touched no file under `agent_workflows/` or `tests/`; paste `aw att --type plan` showing a non-empty Priority column; and paste `aw check plans` clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until it has been reviewed and a human sets it `approved`.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped, never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. This orchestrator carries E-01 deliberately (a premise check no child covers) and must not absorb any child's work; the runner retires it only when all three children are `executed`.
