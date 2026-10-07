# IPD: Enforce the descriptive bound on a composed drift detail structurally, rather than per site by test

- Date: 2026-10-01
- Kind: orchestrator
- Concern: Backlog `0livgf` carries TWO deferred rows from executed plan `mc6r92`, and they are a mechanism and a site rather than one defect. Residue 1: nothing structurally enforces the Section 8.8 descriptive bound on a composed drift detail, because `artifact_core.Drift` does not validate its own `detail` and `attention_contract.is_safe_descriptive` is applied to no composed detail anywhere, so the bound rests on one per-site test on one producer out of 171 construction sites. Residue 2: the stranded-lane detail is not bounded by construction, because its prefix embeds a `run_id`, a worktree path, an `integration_signal` and a commit count, each of which can grow past the budget `mc6r92` derived from the then-observable worst case. This Set closes both, in the order measurement forces.
- Scope: Order the two children so the bound becomes a property of the `Drift` type without crashing `aw check` on the way. Order 01 bounds the lane producer by construction; Order 02 cleans the live over-bound population, adds the constructor refusal, and amends the spec. This plan itself carries NO implementation work.
- Scope-Paths: .aw/records/plans/pending/20261001-driftbound-00-itamry-enforce-the-descriptive-bound-on-a-composed-drift-detail-str.ipd.md
- Item-Dependencies: none
- Status: not-executed
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: 378987f1123b3af6572cfd4d130a940bf6ef8e6ab99d8d5699de26c52ee45da3
- Coverage-Checked: 2026-10-07 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: chore
- Priority: low
- From-Backlog: 0livgf
- Set: driftbound
- Order: 0
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: itamry

## Workflow history
- 2026-10-07 not-executed (aw set): Maintainer ruling 2026-10-07: do not length-enforce tool-composed drift details; sibling 62pkkg already retired not-executed and backlog 0livgf closed. Retiring the rest of Set driftbound.
- 2026-10-07 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Reviewed at HEAD `fe2ee961c` in an isolated review lane; plan byte-identical to the lane input, so no pre-review snapshot. Both children pending (`9sbfea` reviewed this sweep, `62pkkg` to-review with `executed:9sbfea`); child table, ordering edge and coverage confirmed (`aw ipd coverage itamry`: ready). Fixed: carriers `7stpjm` and `3jez8u` both finished, so Carrier-Evidence cited and stale bidi prose corrected (PR-001); E-02/V-02 demanded `0livgf` at `graduated` NOT `done`, but a runner closes the item `done` when its last carrier executes (precedent `7stpjm`), and the item is still `open` today, so the expectation now accepts either and forbids writing it (PR-002); suite bar made a by-name failure-set comparison and the byte-identical bar aligned with `9sbfea` (PR-003); gate given paste-output, scope-fence declaration, runner-retires vs hand-finalize ownership and Readiness ownership (PR-004); OQ owners recorded (PR-005). Coverage re-probed after edits (IPD-S408 repair attempt 1 of 2): pass.
- 2026-10-07 coverage pass (aw oc run): fingerprint 378987f1123b, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-06 coverage pass (aw oc run): fingerprint 7d1b71157b63, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `0livgf` as the parent of a two-child Set. THE SPLIT IS FORCED BY A MEASURED ORDERING CONSTRAINT, not by size. Driven in this lane: with a validating `Drift` constructor patched in, the exception propagates OUT of `check_engine.check_durable_carrier` on the FIRST over-bound finding, so `aw check` CRASHES rather than reporting; and the same evaluator backs `aw ipd lint --phase pre-transition`, so the plan transition gate would break too. Meanwhile the lane producer's worst reachable composition is 370 characters against a 300 bound, so the refusal landing before the lane fix would raise inside `aw attention --check` on a sufficiently long worktree path. Hence Order 01 (bound the lane) strictly precedes Order 02 (refuse at the type), declared as `- Item-Dependencies: executed:9sbfea` on the child rather than left to Set order. THE TWO CHILDREN ALSO DIFFER IN CONTRACT AUTHORITY, which is the second reason not to merge them: Order 02 must AMEND spec Section 8.8 (whose subject today is an authored artifact field, not a tool-composed detail), while Order 01 needs no amendment, and keeping the spec edit in exactly one child means one plan in the Set declares the `.spec.md` path.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Close both residues backlog `0livgf` carries, in the one order that does not break `aw check` or the plan transition gate on the way, so the Section 8.8 descriptive bound on a composed drift detail is enforced by the `Drift` type and stated by the spec rather than observed by a single test at a single site.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

THIS IS AN ORCHESTRATION CHECKLIST AND CARRIES NO WORK OF ITS OWN. Every item below confirms a CHILD reached `executed` with its own evidence; none of them produces a deliverable, establishes a baseline, or reconciles records, because a runner RETIRES an orchestrator once every child is `executed` and deliberately skips the pre-transition E/V checkpoint, so work parked here would be marked complete having never been performed. Anything this Set needs doing lives in a child.

### Task group 1: sequence the Set

- [ ] E-01 CONFIRM 9sbfea REACHED executed
  THIS MUST BE FIRST AND THE REASON IS MEASURED, NOT STYLISTIC. The lane producer's worst reachable composition is 370 characters against a 300-character bound (373 through the real producer in `9sbfea`'s existing case (c) fixture, re-measured 2026-10-07), using only a `run_id` length and a worktree directory name present in this tree today. So Order 02's constructor refusal, landing first, would raise inside `aw attention --check` for any lane whose worktree path is long enough. Order 02 declares `- Item-Dependencies: executed:9sbfea` for exactly this reason, and the runner re-checks that edge at dispatch.
  - Depends on: none
  - Expected outcome: `9sbfea` resolves to a file under `.aw/records/plans/executed/`, its `- Status:` is `executed`, and `aw ipd lint` reports it conforming.
  - Execution state: pending

- [ ] E-02 CONFIRM 62pkkg REACHED executed
  CHECK ITS SPEC AMENDMENT LANDED, because it is the item most easily dropped under time pressure and the refusal is illegitimate without it: Section 8.8's subject today is a list of AUTHORED artifact fields, so a refusal on a tool-composed detail enforces a contract the spec does not state until `62pkkg` E-06 extends it.
  Also confirm backlog item `0livgf`'s state and that both of its residues are named as closed by a child, with neither silently dropped. EXPECT `done` OR `graduated`, AND SAY WHICH: once every `From-Backlog: 0livgf` carrier is `executed`, a runner closes the item `done` itself (measured precedent: `7stpjm` "closed by aw agy run: IPD lxcexr executed (every IPD carrier is executed ...)"), while a hand execution leaves it `graduated` for the human to close with `aw backlog set done 0livgf`. At review (2026-10-07) the item is still `open`, never graduated; this item only CONFIRMS and must not write the backlog status. Both rows must be accounted for individually: `9sbfea` closes residue 2 (the stranded-lane detail) and `62pkkg` closes residue 1 (the constructor refusal).
  - Depends on: E-01
  - Expected outcome: `62pkkg` resolves to a file under `.aw/records/plans/executed/`, its `- Status:` is `executed`, its `V-06` evidence shows the amended Section 8.8, and `aw ipd lint` reports it conforming.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `9sbfea` | `.aw/records/plans/pending/20261001-driftbound-01-9sbfea-bound-the-stranded-lane-detail-by-construction-with-a-reusab.ipd.md` | Residue 2. Adds `attention_contract.compose_bounded_detail`, a pure composer bounded by arithmetic over one budget, and routes `attention.stranded_lane_drift` through it. Converts the existing case (c) from a recorded observation into a real bound assertion. | none |
| 02 | `62pkkg` | `.aw/records/plans/pending/20261001-driftbound-02-62pkkg-refuse-an-over-bound-detail-in-the-drift-constructor-itself.ipd.md` | Residue 1. Cleans the live over-bound population (two `check_engine` carrier rules, the `doctor` probe details), then makes `artifact_core.Drift` refuse a non-conforming `detail` at construction, and amends spec Section 8.8 to extend the bound to a tool-composed detail. | `executed:9sbfea` |

## Completion criteria (the whole Set is done only when)

- Both children are in `.aw/records/plans/executed/` with `- Status: executed` and every `V-*` carrying concrete pasted evidence.
- `artifact_core.Drift` refuses an over-bound, multi-line or control-character-bearing `detail` through all three construction routes (the constructor, `_replace`, `_make`), reusing `attention_contract.is_safe_descriptive` rather than re-deriving its rules.
- No surface (`aw check all`, `aw attention --check`, `aw doctor`, `aw ipd lint` over the pending plans) produces a finding whose `detail` exceeds `MAX_DESCRIPTIVE_LEN`, and none of them CRASHES.
- `aw ipd lint --phase pre-transition` still functions on a real plan, proving the refusal did not break the transition gate.
- Spec Section 8.8 states that the bound governs a tool-composed drift detail and names the constructor refusal as the enforcement point, with every pre-existing bullet intact.
- The stranded-lane detail is within the bound for a constructed worst-reachable shape whose naive composition exceeds it, and every in-bound row the live tree produces is byte-identical to its pre-Set row (per `9sbfea` E-04, which names any already-over-bound live row as the one expected change).
- Backlog `0livgf` is `done` (runner-closed) or `graduated` (hand execution, awaiting a human close), with both residues individually accounted for.

## Cross-IPD validation

- THE DEPENDENCY EDGE IS REAL AND MUST BE HONORED EVEN BY A HAND EXECUTION. Order 02 declares `- Item-Dependencies: executed:9sbfea`. A runner re-checks it at dispatch and marks the item `dependency-blocked` rather than running it early; an agent executing this Set by hand must honor the same order, because the reverse order raises inside `aw attention --check`.
- NEITHER CHILD MAY CHANGE `MAX_DESCRIPTIVE_LEN` OR `is_safe_descriptive`. A live Set (`qbz8i1`, orchestrator `xhr0dj`) excludes exactly that "in every child without exception", and both children here reuse the predicate unchanged. A child that widened or narrowed it would change what `aw specs check`, `aw backlog check` and `aw attention --check` reject across every tree.
- EXACTLY ONE CHILD EDITS THE SPEC. Order 02 declares the `.spec.md` path and Order 01 declares none, so the two cannot produce conflicting amendments to the same section. Pending plan `qpw45x` amends a DIFFERENT bullet of the same section, which is why Order 02 must amend rather than rewrite.
- THE COMPOSER IS SHARED BY DESIGN, AND ITS REUSE IS THE ONE CROSS-CHILD CHOICE LEFT OPEN. Order 01 places `compose_bounded_detail` in `attention_contract` (not inside `attention`) precisely so Order 02's E-02 can reuse it for the `check_engine` carrier details; Order 02's OQ-04 is open and its executor must record which route was taken and why.
- NO CHILD MAY DELETE THE OTHER'S COVERAGE. Order 02's E-07 explicitly judges whether Order 01's lane bound assertions became redundant once the constructor refuses, and records a decision to keep them; removing coverage because a stronger guard exists is how this repository lost tests before.

## Deferred / out of scope (with reason)

- **The 883 authored artifact descriptive fields that exceed the bound.** Disjoint from this Set by construction: those are AUTHORED fields in tracked artifacts, while both residues here concern a TOOL-COMPOSED `Drift.detail`. Enforcing the bound on authored fields at `error` would deadlock the lifecycle, because the setter re-validates prospective text and would refuse the very transition needed to fix an over-length artifact.
  - Carrier: tapqf2
- **The over-bound population as a standing concern.** Order 02 fixes the live instances and makes recurrence impossible, which is what closes it, but the item that tracks the population is `7stpjm` and its routes are the menu Order 02's E-02 chooses from. It stays carried until that item lands. STATUS AT REVIEW (2026-10-07): `7stpjm` is `done`, closed by executed plan `lxcexr`, which brought the carrier-rule details inside the bound; Order 02 must re-derive the remaining population (measured at the `9sbfea` review: 1 over-bound finding of 123) rather than inherit either number.
  - Carrier: 7stpjm
  - Carrier-Evidence: .aw/records/plans/executed/20261001-7stpjm-01-lxcexr-bring-every-carrier-obligation-check-detail-inside-the-secti.ipd.md
- **Per-surface escaping of a descriptive field at the attention board.** A different Section 8.8 bullet (deterministic escaping per surface), owned by live pending plan `qpw45x`, which declares the same two files Order 01 touches and amends the same spec section Order 02 touches. Complementary to a bound, not a substitute: this Set makes an unsafe value unconstructable, that plan makes a rendered value inert.
  - Carrier: llnvwj
- **Bidi control characters, which Section 8.8 names.** At authoring `_CONTROL_CHAR_RE` did not match them; that has since been widened by executed plan `0obt4k` (backlog `3jez8u`, now `done`), and measured at review `is_safe_descriptive('a\u202eb')` is `False`. Both children still reuse the predicate UNCHANGED, so they inherit the widened reading automatically, and neither may re-derive it.
  - Carrier: 3jez8u
  - Carrier-Evidence: .aw/records/plans/executed/20261002-3jez8u-01-0obt4k-widen-the-section-8-8-control-character-predicate-to-reject.ipd.md
- **Restoring the fuller pre-`mc6r92` SUPERSEDED lane sentence now that a composer would protect it.** An operator-facing wording decision about every superseded row, deliberately excluded from Order 01 so its byte-identical-output claim holds.
  - Carrier-Declined: nothing is owed, because no defect remains. The current sentence is correct and in bound; a longer one would be a readability preference with no contract behind it, and an open record whose only content is a preference would sit unactioned.

## Scope check

- Over-scope: none. This plan writes only its own file; every implementation path is declared by the child that writes it.
- Under-scope: both residues of backlog `0livgf` are owned by a child (residue 2 by `9sbfea`, residue 1 by `62pkkg`), and no step of either child is parked on this parent. NOT covered, each with a reason and a carrier recorded in Deferred above: the authored-field population, the tracked over-bound population item, per-surface escaping, bidi controls, and the lane sentence restoration.

## Required tests / validation

This plan runs no tests of its own; each child's own `## Required tests / validation` section governs its work, and the Set's whole-surface verification lives in Order 02's `V-04` and `V-05` (every surface's exit code unchanged, nothing crashed, the bare full suite's failure set unchanged BY NAME against a baseline re-derived before Order 01, and the transition gate still functional). The orchestration checks are: `aw ipd lint` conforming on both children, both children resolving under `.aw/records/plans/executed/`, and backlog `0livgf` at `done` or `graduated` per E-02.

## Open questions

### OQ-01: Why two children rather than one plan?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED on a measured ordering constraint rather than on size. Two facts force it. FIRST, a validating `Drift` constructor CRASHES `aw check`: driven in this lane, the exception propagated out of `check_engine.check_durable_carrier` on the first over-bound finding, and the same evaluator backs `aw ipd lint --phase pre-transition`, so the plan transition gate would break with it. SECOND, the lane producer's worst reachable composition is 370 characters against a 300 bound, so the refusal landing before the lane fix would raise inside `aw attention --check`. A single plan would therefore have to interleave a cleanup, a type change and a producer rewrite with an internal ordering that no dependency edge could express and no runner could enforce. As two children with a declared `executed:9sbfea` edge, the order is machine-checked at dispatch. A secondary reason: only Order 02 has spec-amendment authority here, and keeping the `.spec.md` in one child means the Set cannot produce two conflicting amendments.

### OQ-02: Could the constructor refusal be skipped, leaving only the lane fix?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED as NO, because that is precisely what executed plan `mc6r92` already did and what backlog `0livgf` was filed to carry. `mc6r92` bounded the lane detail with a shortened sentence plus a test and recorded both residues honestly. Shipping Order 01 alone would repeat that outcome at a higher quality (bounded by arithmetic rather than by observation) while leaving residue 1 exactly as filed: 171 construction sites with no structural guard, where a future edit to any detail assembly re-breaks the bound and only a per-site test at one site could catch it. The item's own framing is that the mechanism is the gap, so a Set that closes only the site has not graduated it.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw find plans 9sbfea` showing the resolved path under `.aw/records/plans/executed/`, paste its `- Status:` line, paste `aw ipd lint` on it reporting conforming, and paste its `V-01` through `V-05` `Result:` lines showing every one `pass` with non-empty `Observed evidence`. A `V-*` with an empty evidence block fails this item regardless of its `Result:`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw find plans 62pkkg` showing the resolved path under `.aw/records/plans/executed/`, paste its `- Status:` line, paste `aw ipd lint` on it reporting conforming, and paste its `V-01` through `V-07` `Result:` lines showing every one `pass` with non-empty `Observed evidence`. Additionally paste its `V-06` `Observed evidence` block in full and confirm from it that spec Section 8.8 was amended and that no pre-existing bullet was weakened. Also paste backlog item `0livgf`'s `- Status:` line (`done` if a runner closed it on the last carrier's execution, `graduated` after a hand execution; `open` fails this item and must be reported, not hand-fixed), naming which child closed which residue (`9sbfea` for residue 2, `62pkkg` for residue 1), with no dangling backlog findings.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is an orchestrator and carries no implementation work: each E-item above confirms a child reached `executed` with its own evidence. That checklist exists because most Sets are run by an agent told simply to execute the Set with no runner involved, and deleting it is what causes partial execution; it is not work parked on a parent, which is the thing a runner's coverage gate refuses and which would be marked complete having never been performed.

Execution requires explicit human approval first (`Status: approved`). The `- Readiness:` field is `/plan-review`'s output; no author or executor writes or changes it. Open questions: OQ-01 and OQ-02 are resolved; none blocks. Order 02 declares `- Item-Dependencies: executed:9sbfea`, so a runner will dispatch Order 01 first and mark Order 02 `dependency-blocked` if asked to run it early; an agent executing this Set by hand must honor the same order.

Commit through `aw commit itamry -- <paths>` with only this plan's declared path, verifying `git diff --cached --name-only` first; never `git add -A`, `-a`, `--no-verify`, or a push. Paste the ACTUAL output of every `aw find`, `aw ipd lint` and status read claimed in V-01/V-02; a confirmation not pasted is a confirmation not made.

SCOPE FENCE (a declaration the finalize scope gate reconciles, not a stop directive): this plan writes only its own file. It writes no child plan, no backlog status (including `0livgf`), and no spec; each child owns its own paths.

Lifecycle transition: under `aw oc run` / `aw agy run` the RUNNER retires this orchestrator to `executed` itself once both children are `executed` on disk, spending no agent turn, so the executor must not run `aw ipd finalize` on it. In a hand execution of the Set, once both children are executed and V-01/V-02 carry pasted evidence and `aw ipd lint --phase pre-transition` conforms, the executor runs `aw ipd finalize itamry`. Never `git mv` the plan.
