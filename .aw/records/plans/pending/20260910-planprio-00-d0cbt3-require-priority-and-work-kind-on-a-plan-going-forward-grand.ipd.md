# IPD: Require Priority and Work-Kind on a plan going forward, grandfathering the existing corpus

- Date: 2026-09-10
- Kind: orchestrator
- Concern: `Priority` and `Work-Kind` were added to plans as recognized-but-OPTIONAL, and the maintainer states that permanent optionality was never their intent: they meant optional for LEGACY plans only. Adoption is consequently near-zero, so the attention board labels almost no plan with a priority and the queue cannot be ordered by importance. RE-MEASURED AT REVIEW (2026-09-12, HEAD `3ae4735e`), because the authored figures are stale and one of them was FALSE: pending plans 120 (authored 104); carrying BOTH fields 11 (authored 0, so "adoption is zero" is now wrong although the thesis survives, since 109 of 120 remain unlabelled); carrying `- From-Backlog:` 92, ALL resolving and ALL sources carrying both fields, of which 81 still lack at least one field (authored 84); carrying no source 28 (authored 20). Terminal plans 508 (470 `executed` + 34 `superseded` + 4 `not-executed`). Do NOT re-quote any of these either: the corpus moves daily and each child re-derives its own population.
- Scope: Make both fields REQUIRED at the ready-to-execute gate for new plans while leaving the terminal corpus exempt, fix the scaffold that never emitted them (the root cause of near-zero adoption), backfill the pending plans that can inherit from their source backlog item, and decide values for the remainder that have no source. Does NOT change the shared `low|medium|high` vocabulary, does NOT introduce a priority-based sort key, and does NOT touch backlog items, specs or research.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Set: planprio
- Order: 0
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: d0cbt3

## Workflow history

- 2026-09-12 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 (BLOCKER, OPEN and escalated to blocking OQ-02), PR-002..PR-009 FIXED; readiness `no-go` because one blocking question remains. Record: `.aw/records/reviews/20260910-planprio-00-d0cbt3-require-priority-and-work-kind-on-a-plan-going-forward-grand.review.md`. `aw ipd lint --phase author` CONFORMING (clean, 0 findings) before semantic review. DISCLOSURE: same agent/model family authored this Set, so treat this as a near-self-review worth less than an independent one; its value rests on what was EXECUTED rather than re-read. NINE things were measured rather than reasoned: the pending/terminal populations and the inheritance graph were recomputed from disk; `check_plan_priority`/`check_plan_work_kind` were DRIVEN against a plan carrying `grandfathered`, `unresolved` and `TODO` in each field; `ipd_lint.lint_file` was driven on an APPROVED pending plan with its gate field removed at `--phase author` and on an `executed/` plan at `--phase pre-execution`; `aw check plans` was run bare; the bare suite was run; `aw att --type plan` was run piped, with `FORCE_COLOR=1`, and with `--format json`; the `-` callers were grepped; and the `oorry1` precedent plan was read in full.
  THE SET'S THESIS IS SOUND AND ITS SEQUENCING IS NOT, which is why every finding is a correction rather than a rejection. The one BLOCKER is that Order 01 lands the gate FIRST while both backfills depend on it, and the gate fires at EVERY phase for a plan already at the ready-to-execute tier, so 18 currently-approved pending plans become unrunnable the moment Order 01 lands and stay unrunnable until Order 03's human decision table is answered. The shipped precedent this Set copies (`oorry1`) avoided exactly that by stamping the grandfather sentinel onto the pre-cutoff pending corpus in the SAME child that added the gate; this Set omits that step. Escalated as blocking OQ-02 with three costed options. Also corrected: the chosen sentinel collides with two SHIPPED enum rules that reject any out-of-vocabulary value (measured), two prescribed evidence commands cannot produce what they ask for (`aw att`'s Priority column does not exist on a piped surface; `aw check plans` is 140 errors deep before this Set touches anything), the parent parked a measurement DELIVERABLE on an orchestrator the runner retires without performing or verifying its items, and four population figures were stale with one of them false.
- 2026-09-10 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from a maintainer correction during an `/askme` round. Reviewing plan `b5sfwm`'s question about the `-` clearing sentinel, I reported that 0 of 104 pending plans carry `Priority` or `Work-Kind`. The maintainer replied that they were "pretty sure that there was a time where plans had priority for sure, and some had Work-Kind", and then that their optionality decision "may have been misrecorded. I meant optional for legacy, but I'm pretty sure I did not intend for those fields to be optional going forward." INVESTIGATED, AND THE RECORD SUPPORTS THEM: the fields were genuinely added by Sets `xprio` (Priority, 2026-08-27) and `wkindname` (Work-Kind), both live in `META_RECOGNIZED` today with working `aw ipd set` flags; the phrase "recognized-but-optional" ORIGINATED for a different field (`Scope-Paths`, `3a195178`, 2026-08-23) where a REVIEW chose it explicitly "to avoid breaking every pending plan and the grandfather guarantee", and `Priority` inherited the phrasing BY ANALOGY rather than by a separate decision; the source backlog item `p9o1oo` records the maintainer's own words as "research, plans, specs, more or less everything need a priority" (it says NEED, and says nothing about optional); and the ONLY question ever put to the maintainer in that Set was whether an ABSENT value should render as unprioritized or as an implicit medium, which is a RENDERING question, not a requiredness one. So permanent optionality was an inherited default that no one put to them. HONEST LIMIT, stated because it bounds the claim: commit authorship is uniform across humans and agents in this repository, so this establishes what the artifacts SAY and where the wording came from, not what the maintainer intended; and the absence of a question is weak evidence, not proof.

## Goal

Make a plan's `Priority` and `Work-Kind` load-bearing rather than decorative, so the attention board can order the queue by importance, while leaving the 508 terminal plans (470 `executed`, 34 `superseded`, 4 `not-executed`, re-measured at review) untouched and unfailed AND without stranding the pending plans that are already approved to run.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: sequence the Set

- [ ] E-01 SEQUENCE THE SET AND HOLD EACH CHILD UNTIL ITS PREDECESSOR IS `executed` ON DISK, reading each child's own `- Status:` line rather than trusting a queue view. This item is ORCHESTRATION, not work: it dispatches and gates, and it produces no deliverable of its own.
  THE ORDER IS WHAT OQ-02 IS ABOUT AND IS NOT YET SETTLED. As authored, Order 01 lands the gate first and Orders 02 and 03 both carry `- Item-Dependencies: executed:lkexaw`. Review found that ordering strands the already-approved pending plans (finding PR-001), so DO NOT DISPATCH THIS SET UNTIL OQ-02 IS ANSWERED; the answer may reverse this order or add a stamping step inside Order 01.
  DO NOT RE-DERIVE ANY POPULATION HERE, AND DO NOT PARK THAT MEASUREMENT ON THIS PLAN. It was previously written as this orchestrator's own E-01, which was a defect: the runner retires an orchestrator administratively (`oc_runipd.finalize_orchestrator`, `oc_runipd.py:836-860`, no agent turn) and DELIBERATELY skips the pre-transition E/V checkpoint (spec `77tr3o`, OQ-1 ruling), so a measurement parked here is marked complete having never been performed OR verified. It is covered where it is actually consumed: Order 02's E-01 re-derives the inheritance table and Order 03's E-01 re-derives the no-source population, and BOTH are explicitly told to trust no count from any plan.
  - Depends on: none
  - Expected outcome: each child dispatched only after its declared predecessor reads `executed` in its own file, with the read pasted; no population figure derived here; no code or record change made by this item.
  - Execution state: pending

- [ ] E-02 RETIRE THIS ORCHESTRATOR ONLY WHEN ALL THREE CHILDREN ARE `executed`, and carry no work of its own beyond the sequencing in E-01. The children own every code and record change; this parent holds sequencing only.
  IF THE RUNNER REFUSES THE RETIREMENT, THAT IS NOT A RUN FAILURE and must be reported with the reason it recorded rather than forced: retirement is gated on every child being `executed` and on nothing else qualifying, and a refusal leaves this plan in `pending/`.
  - Depends on: E-01
  - Expected outcome: all three children `executed` with their own evidence, and this parent transitioned by the runner or by `aw ipd finalize` without performing any child's work; any refusal reported verbatim.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | Id | Title | Depends on |
|---|---|---|---|
| 01 | `lkexaw` | Emit both fields on scaffold and enforce them at the ready-to-execute gate | none (SEE OQ-02) |
| 02 | `8u6770` | Backfill the pending plans that can inherit from their source backlog item | `executed:lkexaw` (SEE OQ-02) |
| 03 | `lc4unl` | Decide and record values for the pending plans with no source item | `executed:lkexaw` (SEE OQ-02) |

Orders 02 and 03 are INDEPENDENT of each other and may run in either order or concurrently.

THE EDGES ABOVE ARE UNDER QUESTION, NOT SETTLED. Both backfills depending on Order 01 is what finding PR-001 identifies as the Set's blocking defect, because the gate Order 01 installs fires at EVERY lint phase for a plan already at the ready-to-execute tier. Whichever option OQ-02 selects, the child front matter must be brought into agreement with this table in the same change: the `- Item-Dependencies:` lines live in the children's own files and were deliberately NOT edited by this review, since only this orchestrator was in the review's scope ledger.

## Completion criteria (the whole Set is done only when)

1. A newly scaffolded plan carries both fields, and a plan reaching the ready-to-execute gate without them is REFUSED with a message naming the fix.
2. The 508 terminal plans are unaffected: `aw check` and `aw ipd lint` report no new finding against any plan in `executed/`, `superseded/` or `not-executed/`.
3. NO PENDING PLAN IS LEFT UNRUNNABLE BY THIS SET. Every pending plan either carries both fields with a value in the shared vocabulary, or carries whatever exemption marker Order 01 defines, and no plan that was `approved`/`auto-approved` before the Set began is refused by `aw ipd lint` or `aw ipd begin` after it. This is the criterion PR-001 exists to protect, and it is the one most likely to be quietly missed, because the refusal appears on a DIFFERENT plan from the one being executed.
4. THE EXEMPTION MARKER IS ACCEPTED BY THE SHIPPED ENUM CHECKS, not merely by the new gate. `check.priority-invalid` and `check.work-kind-invalid` accept ONLY `low|medium|high` and `bug|feature|chore|security|followup` and treat ABSENT as fine (`check_engine.py:2643-2695` and `:2697-2755`); MEASURED at review, a plan carrying `- Priority: grandfathered` (and likewise `unresolved` or `TODO`, and the same three on `- Work-Kind:`) is flagged by both rules. So whatever sentinel Order 01 chooses must either be admitted by those two rules in the same change (Order 01 already declares `check_engine.py`) or must not be a metadata value at all. A criterion saying "a value in the shared vocabulary OR an exemption marker" is self-contradictory until that is resolved.
5. A plan's priority is observable on a surface an AGENT can capture. `aw att --type plan` piped emits `- [tree] path (status)` with NO Priority column: the column exists only in the COLORED table renderer (`attention.py:2084-2101`, reached from `render_board` only when the term is colored, `:2280-2296`). The two surfaces that answer the question are `FORCE_COLOR=1 aw att --type plan` (renders the column) and `aw att --type plan --format json` (carries a per-item `priority` key, `:1083`). Use those, and state the count of items whose `priority` is non-null.
6. The bare suite passes, with the actual summary line pasted and compared against a baseline established BEFORE the first edit.

## Cross-IPD validation

Order 01's gate must be exercised against a plan from THREE states, not two, because the grandfather boundary is the disposition OR the persisted status and the second half is what bites this Set:

1. A TERMINAL plan carrying neither field must produce NO finding at any phase. Terminal-dir files short-circuit to the `legacy` disposition before the checkpoint layer (`ipd_lint.py:1052`); verified at review, an `executed/` plan with neither field lints clean at `--phase pre-execution` (0 findings).
2. A PENDING plan at `to-review`/`reviewed` carrying neither field must lint clean at `--phase author`, so drafting is not blocked.
3. A PENDING plan whose `- Status:` is `approved` or `auto-approved` carrying neither field must be REFUSED, AND that refusal must be shown to fire at `--phase author` as well as `pre-execution`, because `_scope_paths_gate_applies` (`ipd_lint.py:904-913`, the predicate Order 01 mirrors) returns true on the STATUS regardless of the requested checkpoint. Verified at review with the `Scope-Paths` original: an approved pending plan with the field removed reports `IPD-M106` at `--phase author`. This is the case that strands the approved queue, so it must be exercised deliberately rather than inferred.

Orders 02 and 03 must both re-run `aw check plans` afterwards and show NO NEW rule id and no increased count against a baseline each captures BEFORE its first edit. Do NOT require a CLEAN run: measured bare at review (HEAD `3ae4735e`), `aw check plans` exits 1 with `errors 140  warnings 0`, none of it attributable to this Set (124 `check.scope-drift` on two plans holding live begin receipts, 15 `check.lifecycle-transition-invalid`, 1 `check.review-decision-unescalated`). An executor told to make that output clean would either stall or "fix" other agents' plans in a shared checkout, which is the one thing the shared-checkout rule forbids.

## Deferred / out of scope (with reason)

- CHANGING THE VOCABULARY. `low|medium|high` is shared with backlog items by deliberate decision (source item `p9o1oo` rejected a 7-level scale as producing inconsistent assignment and a noisier board). Out of scope.
- INTRODUCING A PRIORITY-BASED SORT KEY. The `xprio` orchestrator's OQ-01 explicitly decided this Set's ancestor would not add one, and the shared sort remains attention-class/path/id. A sort key is a separate decision.
- SPECS AND RESEARCH. `xprio` gave those types the same optional field; whether they should also become required is the same question one level out, and is NOT decided here. Note this deliberately leaves an asymmetry that a later reader may want resolved.
- THE `-` CLEARING SENTINEL ON `aw backlog set`, which is plan `b5sfwm`'s own blocking question and is where this investigation started. Untouched.
- THE `-` CLEARING SENTINEL ON `aw specs set`, which Order 01's E-07 deliberately does NOT remove even while removing or narrowing the plan-side twin. This is a knowing asymmetry and it has a named cost: `tests/test_work_kind.py:212-236` pins the argparse `choices` to `set(backlog.KINDS) | {"-"}` for BOTH `("ipd","set")` AND `("specs","set")` in one assertion, so changing the plan side necessarily edits a test that also guards the spec side, and the two verbs then diverge. Two further callers exercise the sentinel through the real CLI and will break if it is removed without them: `tests/test_ipd_priority.py:155-167` (`--priority -`) and `tests/test_work_kind.py:362-377` plus `:425-443` (`--work-kind -`, the second also asserting the structural `- Kind:` survives a Work-Kind clear). Order 01 owns updating them; this parent records WHY the asymmetry is acceptable, namely that the field stays genuinely OPTIONAL on a spec while becoming conditionally required on a plan, so clearing it means different things on the two types.
- BACKFILLING TERMINAL PLANS. Their content is immutable by policy; the grandfather exemption exists precisely so they need no edit.

## Scope check

- Over-scope: none. This parent declares only the plans tree and performs no code change; each child declares its own paths.
- Under-scope: the Set does not make specs or research required (deferred above), and does not add the sort key that would make a populated Priority column maximally useful. IT ALSO DOES NOT, AS AUTHORED, PROTECT THE ALREADY-APPROVED PENDING PLANS from the gate it installs, which is finding PR-001 and is the subject of blocking OQ-02; that is a genuine gap rather than deliberate sequencing, and the Set is not executable until it is closed.

## Required tests / validation

Each child owns its own tests. Establish the suite baseline by running `python3 -m pytest` bare BEFORE the first edit and paste that output. FOR REFERENCE ONLY, review measured it bare at HEAD `3ae4735e`: `5971 passed, 3 skipped, 2 xfailed in 64.82s`, with no failure. Do NOT quote that as your baseline; re-measure and judge on the delta, because an unverified count is what produced this Set in the first place. Run the suite BARE (`python3 -m pytest`): the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`, and adding `-n0` or a second `-q` makes the run slower and suppresses the very summary line the execution contract requires you to paste.

## Spec / documentation sync

Order 01 must state whether any spec describes these fields as optional. NOT YET MEASURED at authoring, and it must not be assumed absent: `xprio` amended the research frontmatter contract and the spec contract, so a spec may well carry the optionality claim. If one does, Order 01 declares that `.spec.md` in its own `Scope-Paths` and amends it in the same change, per the repository rule that a plan changing behavior a spec describes carries the amendment with it.

## Open questions

### OQ-01: Should the requirement also extend to specs and research, which `xprio` gave the same optional field?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DELIBERATELY OUT OF SCOPE HERE AND RAISED SO THE ASYMMETRY IS NOT SILENT. `xprio` added the same recognized-but-optional `Priority` to plans, specs AND research in one Set, so making it required for plans alone leaves the other two types where they are. That may be correct, since a spec and a research report are not queue items in the way a plan is, and the maintainer's original words were about prioritizing work. Non-blocking because this Set is coherent and complete for plans on its own; answering it later costs a separate Set rather than a rework of this one.

### OQ-02: Landing the gate first strands the plans that are already approved to run. Reverse the order, stamp the corpus inside Order 01, or stage the gate?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: THE DEFECT IS MEASURED, NOT PREDICTED, and the numbers are what make it blocking. The gate Order 01 installs mirrors `_scope_paths_gate_applies` (`ipd_lint.py:904-913`), which fires when the requested checkpoint is `pre-execution` OR the plan's persisted `- Status:` is at the ready-to-execute tier, so it applies at EVERY phase to an already-approved plan; verified at review by removing `Scope-Paths` from an approved pending plan and getting `IPD-M106` at `--phase author`. MEASURED at HEAD `3ae4735e`: 25 pending plans are `approved`/`auto-approved` and 18 of them carry neither field. Of those 18, only 5 can be reached by Order 02's inheritance; the other 13 (one `lanectn`, two `orchprobe`, nine `runanalytics`, one `runnerbugs`) carry no `- From-Backlog:` at all and therefore need Order 03's human decision table. Because Orders 02 and 03 both declare `- Item-Dependencies: executed:lkexaw`, the moment Order 01 lands those 18 plans fail `aw ipd lint` at every phase and `aw ipd begin` refuses them fail-closed (`ipd_lifecycle.py:991-1007`), so `aw oc run` / `aw agy run` cannot execute them until BOTH backfills have run and, for the 13, until a human has answered a table. The parent's authored justification for the ordering ("backfilling before the gate exists would write values nothing enforces") does not survive contact with the mechanism: a value written before the gate exists is precisely what the gate then finds satisfied.
  THE SHIPPED PRECEDENT THIS SET COPIES ALREADY SOLVED THIS AND THE SET DROPPED THE STEP. `20260823-ipdgates-02-oorry1-canonical-scope-paths-allowlist-schema-and-grandfather-polic.ipd.md` is the plan that introduced the `Scope-Paths` gate this Set mirrors, and its E-03 (`:48`) STAMPED `Scope-Paths: grandfathered` onto ~21 pre-cutoff pending plans in the SAME child that added the gate, for the stated reason that "none is retroactively blocked once E-02's gate is live" (`:50`). Measured today, 20 plans still carry that sentinel, all now in `executed/`. Nothing in this Set writes an exemption marker onto any existing pending plan, so the exemption exists in the code and on zero artifacts.
  THREE OPTIONS, EACH COSTED. (a) STAMP INSIDE ORDER 01: Order 01 writes the exemption marker onto every existing pending plan in the same change that installs the gate, exactly as `oorry1` did. Cost: Order 01's `Scope-Paths` must grow `.aw/records/plans/pending`, its diff gains ~109 one-line metadata edits in a shared checkout, and OQ-02's answer must also settle the criterion-4 collision (the marker must be accepted by the two shipped enum rules). Benefit: the boundary becomes auditable per plan, the queue never breaks, and Orders 02 and 03 then merely REPLACE a marker with a real value, which is a strictly safer operation than filling a hole. (b) REVERSE THE ORDER: run 02 and 03 first and make Order 01 depend on both. Cost: the 13 no-source plans gate the entire Set on a human answering a table before any code lands, and both children's `- Item-Dependencies:` lines must be rewritten; a plan authored between the backfill and the gate lands with no fields and no marker. Benefit: no sentinel is ever written. (c) STAGE THE GATE: Order 01 lands the lint diagnostic as ADVISORY and a later step flips it to blocking after the backfills. Cost: contradicts Order 01's E-03 as authored, and an unflipped advisory is the failure mode this whole Set exists to correct (a rule that gates nothing). Benefit: nothing breaks at any instant.
  RECOMMENDATION (a), because it is the shipped precedent for this exact hazard in this exact gate, it keeps the maintainer's "required going forward, grandfather the legacy corpus" intent literally true of the artifacts rather than only of the code, and it removes the dependency edge that makes the Set fragile. DELIBERATELY NOT DONE HERE: this review did not reorder the Set, did not edit either child's `- Item-Dependencies:`, and did not widen Order 01's `Scope-Paths`. Only this orchestrator was in the review's scope ledger, and choosing among the three is a scope-and-appetite call that belongs to the maintainer.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: the runner retires an orchestrator from child status. Do not fabricate an independent implementation checkpoint for this file.

- [ ] V-01 validates E-01
  - Required evidence: paste OQ-02's recorded answer and state which of the three options it selected, then paste the resulting dependency order as it stands in each child's own `- Item-Dependencies:` line (a `grep` over the three child files), showing the children agree with this plan's child table. Then paste, for each child dispatched, the `- Status:` line read from its predecessor's own file at dispatch time showing `executed`. Confirm no population count was derived by this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste each child's `- Status:` line read from its own file showing all three `executed`. Paste `git diff --stat` over THIS parent's own commits showing it touched no file under `agent_workflows/` or `tests/`. Paste BOTH priority surfaces: `FORCE_COLOR=1 aw att --type plan` showing the Priority column populated, and `aw att --type plan --format json` with the count of items whose `priority` is non-null (do NOT paste a piped `aw att --type plan` and call the missing column a failure; that surface has no Priority column by design). Paste `aw check plans` with its error count COMPARED to the pre-Set baseline, naming any new rule id; do not claim it clean, and do not edit another party's plan to reduce the count. Finally, paste `aw ipd lint --phase pre-execution` on three of the plans that were `approved` before the Set began, showing each still conforms, which is the PR-001 criterion.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and carries `- Readiness: no-go`. It must NOT be executed: blocking OQ-02 is open, so `aw ipd lint` refuses this plan at every checkpoint until the maintainer answers it, and a human must then set it `approved`. Answer it with `/askme` (or `aw ipd set ... --by-human`-attested approval AFTER the answer is recorded), not by an executor deciding it mid-run.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped, never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. This orchestrator holds SEQUENCING ONLY and must not absorb any child's work; the runner retires it only when all three children are `executed`.

FOUR CORRECTIONS FROM REVIEW THAT MUST NOT BE RE-INHERITED, because each would send an executor down a wrong path:

1. Do NOT re-quote the authored population figures (`0 of 104`, `84`, `20`, `470 terminal`). Re-measured at review: 120 pending, 11 already carrying both fields, 92 with a resolving source of which 81 still need a field, 28 with no source, 508 terminal. Each child re-derives its own population; trust neither set of numbers.
2. Do NOT require `aw check plans` to be CLEAN. It carries 140 pre-existing errors that this Set does not cause. Compare against a baseline instead.
3. Do NOT read a piped `aw att --type plan` for the Priority column. That surface has none; use `FORCE_COLOR=1` or `--format json`.
4. Do NOT park a measurement or any other deliverable on THIS plan. The runner retires an orchestrator without an agent turn and skips its E/V checkpoint, so anything parked here is marked done having never been performed. If the Set needs a step no child covers, ADD A CHILD for it.
