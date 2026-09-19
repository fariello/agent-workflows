# IPD: Migrate every pending orchestrator checklist to the typed row and grandfather nothing silently

- Date: 2026-09-19
- Kind: child
- Concern: Once child 03 lands, every pending orchestrator refuses a run, because the typed row grammar is new and nothing authored before it satisfies it by accident. Measured at HEAD `21eff5d8`: ZERO of the live `E-*` rows conform. This child is the migration that makes the corpus runnable again, and spec `r07vma` criterion 12 sets the bar it must clear: after whichever route is chosen, every pre-existing orchestrator either CONFORMS or is EXPLICITLY grandfathered with its mechanism named, and NONE is left in a state where a run refuses it with no available remedy.
  THE POPULATION MOVES UNDER THE PLAN, WHICH IS WHY NO COUNT HERE IS A FIXTURE. Measured three times during this Set's design: ten pending `Kind: orchestrator` plans, then eleven hours later, then TWELVE at authoring (38 `E-*` rows total, the widest being `2xz59a` at 9 rows). An executor MUST re-derive the population and report the denominator rather than quoting this plan; a migration that covers the twelve named here and misses one authored since has not met criterion 12.
  AND MOST ROWS ARE NOT A MECHANICAL REWRITE. Only about a third are close to schema-shaped (a single resolvable child reference and a short body); the rest have first lines between 133 and 1528 characters, carrying real orchestration meaning that must be RELOCATED rather than deleted: into continuation lines (R1a leaves those unparsed), into the orchestrator's own prose sections, or into a final child (R1b). Deleting it is the failure R2 exists to prevent, and AGENTS.md records that a prohibition-only message gets complied with by exactly that.
- Scope: Migrating the pre-existing pending orchestrators to the typed row, and disposing of any that cannot be. IN: re-deriving the population; rewriting each orchestrator's `E-*`/`V-*` rows into the R1a form; relocating displaced prose into continuation lines, prose sections, or a new final child per R1b; recording a per-orchestrator disposition; and choosing and JUSTIFYING the route (migrate-all, date cutover, or explicit grandfather) against criterion 12. OUT: the grammar and function (child 01); the review loop (child 02); the runner gate (child 03); the merged proof (child 05); authoring the CONTENT of any new final child beyond what relocation requires; and changing any orchestrator's Status or lifecycle position.
- Scope-Paths: .aw/records/plans/pending, agent_workflows/ipd_lint.py, tests/test_orchestrator_row_grammar.py
- Item-Dependencies: executed:0xmk4e
- Status: to-review
- Set: orchtyped
- Order: 4
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 68uhp0
- From-Spec: r07vma
- Blocks-Release: next
- Work-Kind: bug
- Priority: high

## Workflow history

- 2026-09-19 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from approved spec `r07vma` as Order 04 of Set `orchtyped`. THE POPULATION WAS RE-MEASURED AT AUTHORING and had moved again: 12 pending orchestrators carrying 38 `E-*` rows, up from the 11 recorded in the spec's own cost 3 and the 10 measured during design. That instability is the reason E-01 re-derives rather than trusting any list, and it is evidence for criterion 12's shape-not-count phrasing. This child depends on `0xmk4e` deliberately, so the migration is verified against the same gate a run will apply.

## Goal

Make the live corpus conform to the typed row, with every displaced piece of orchestration meaning relocated rather than deleted, and with a recorded per-orchestrator disposition that shows no Set was left refused with no remedy.

READ THE SCOPE PRECISELY: this child edits OTHER AGENTS' PLANS, which is the one place in this Set where that is authorised and necessary. It is authorised only for the checklist rewrite the grammar requires. It may not change a plan's Status, its lifecycle position, its Scope, or its meaning, and where relocation is genuinely ambiguous the right move is to report rather than to guess.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure, then choose the route

- [ ] E-01 RE-DERIVE THE POPULATION AND THE ROW CENSUS BEFORE TOUCHING ANYTHING, reading each plan's OWN first `- Kind:` bullet rather than searching the file (a whole-file search misclassified a `Kind: child` plan during this Set's authoring, because it quoted the bullet in prose). For each orchestrator record: its id6, its Status, its row count, and per row whether it is already close to schema-shaped or carries prose that must be relocated. Report the denominator.
  DO NOT TRUST ANY COUNT IN THIS SET'S DOCUMENTS. The figure was 10, then 11, then 12 within about a day. The census is the input to every later item, so it must be taken at execution.
  - Depends on: none
  - Expected outcome: a per-orchestrator, per-row census taken at execution time, with the population count and its denominator stated.
  - Execution state: pending

- [ ] E-02 CHOOSE AND JUSTIFY THE MIGRATION ROUTE against criterion 12, which constrains the OUTCOME rather than the method. Three are admissible: migrate every orchestrator now; a date cutover following `check_engine.CARRIER_CUTOVER_DATE`'s pattern (a compact `YYYYMMDD` constant plus a per-artifact severity helper that downgrades a pre-cutover artifact); or an explicit grandfather clause naming its mechanism. Record which, and WHY, in the plan.
  THE BAR IS THAT NO SET IS LEFT REFUSED WITH NO AVAILABLE REMEDY. A cutover that leaves an approved orchestrator refusing with no path forward fails criterion 12 even though it "made the check pass" for new plans. State explicitly what happens to an orchestrator that is mid-flight when this lands.
  - Depends on: E-01
  - Expected outcome: the route chosen and justified against criterion 12; the fate of a mid-flight orchestrator stated.
  - Execution state: pending

### Task group 2: do the migration, losing nothing

- [ ] E-03 REWRITE EACH ORCHESTRATOR'S ROWS INTO THE R1a FORM, one plan at a time, with its displaced prose RELOCATED rather than removed. The three destinations, in order of preference: continuation lines under the row (R1a leaves them unparsed, so context survives beside the row it explains); the orchestrator's own prose sections; or a new final child whose `- Item-Dependencies:` name every sibling (R1b), when the displaced text is genuinely an obligation no child covers.
  PREFER A BARE INDENTED LINE OVER A `- Context:` SUBFIELD FOR OBLIGATION-BEARING TEXT (added at review, PR-005), because the two are NOT equivalent to the semantic probe that remains the control for this residue. Measured at review: `runner_shared.e_item_action_blocks` stops collecting at the first line matching `ipd_lint._SUBFIELD_RE` (`^\s+- ([A-Za-z][A-Za-z /-]*?):\s?(.*)$`), so a bare indented line under a row IS in the probe's payload while the same words written as `- Context: ...` are NOT; and a prose SECTION is outside the payload entirely (`probe_cache_payload` returns only `e_items` and `child_table_rows`). This Set's own parent `d1u4sy` writes its relocated text as `- Context:` lines, which is why its probe payload reduces to five bare `CONFIRM ... REACHED executed` strings. So relocating an obligation into a `- Context:` line or a prose section moves it OUT of reach of both controls at once, which is not deletion but is closer to it than the plan's three-destinations list implies. Where relocated text merely EXPLAINS the row, any destination is fine. Where it carries meaning a reader could mistake for an obligation, use a bare indented line and record that choice in the disposition record. Do not widen the probe payload to fix this: payload and cache key must move together, which backlog `rmcqw8` tracks.
  DELETION IS THE FAILURE MODE, NOT THE SHORTCUT. R2 keeps the checklist because a hand-run Set executes from it, and AGENTS.md records that a prohibition-only message gets complied with by deleting the checklist. So a row's meaning must land somewhere; a diff that only removes text is a failed migration even if the grammar then passes.
  WHERE RELOCATION IS AMBIGUOUS, REPORT IT. Some rows weld a tracking half to a condition half (measured examples: `y9s4vm` E-02, `lyo1tz` E-02, `s0gnha` E-02, all three of which turned out to be either duplication of a child's own assertion or already relocated into a child). Judging which half is redundant is a real decision; where the repository does not answer it, raise it rather than guessing.
  - Depends on: E-02
  - Expected outcome: every orchestrator the chosen route covers has conforming rows; every displaced piece of prose is traceable to its new location; no row's meaning was dropped.
  - Execution state: pending

- [ ] E-04 RECORD A PER-ORCHESTRATOR DISPOSITION, so criterion 12 is auditable rather than asserted. For each: conformed (with the relocation summary), grandfathered (with the mechanism named), or escalated (with the decision needed). An orchestrator missing from the disposition record has not been migrated, whatever the grammar says.
  - Depends on: E-03
  - Expected outcome: a disposition per orchestrator in the census's denominator, with no unexplained omissions.
  - Execution state: pending

- [ ] E-05 RE-RUN THE CENSUS AFTER THE MIGRATION and confirm the conforming count matches the disposition record. This is the item that catches a silent miss: a plan authored while the migration was in flight, or one the route deliberately excluded, must appear as grandfathered or escalated rather than as an unexplained non-conformer.
  - Depends on: E-04
  - Expected outcome: post-migration census reconciles exactly against the disposition record, with any delta explained by a named route decision.
  - Execution state: pending

## Project conventions discovered (Step 0)

- READ A PLAN'S KIND FROM ITS OWN FIRST `- Kind:` BULLET. A whole-file search misclassified `m7gvuz` (a `Kind: child` plan) as an orchestrator during this Set's authoring, because it quotes the bullet in prose.
- THE POPULATION IS UNSTABLE: 10, then 11, then 12 within roughly a day, as Sets are authored and orchestrators finalized. Any count is a dated snapshot.
- `check_engine.CARRIER_CUTOVER_DATE` IS THE IN-REPO CUTOVER PATTERN: a module-level compact `YYYYMMDD` constant plus a per-artifact helper returning a legacy severity for a pre-cutover artifact. E-02 may follow it rather than inventing a mechanism.
- THIS IS A SHARED CHECKOUT AND THESE ARE OTHER AGENTS' PLANS. Editing them is authorised here only for the checklist rewrite. Never change a Status, never move a plan between lifecycle directories, and never sweep an unrelated staged change into a commit.
- R1a LEAVES CONTINUATION LINES UNPARSED ON PURPOSE, which is what makes relocation possible without loss: context can sit under the row it explains.
- THE PARENT `d1u4sy` IS ALREADY CONFORMING, having been authored in the grammar. It should appear in the census as conforming with no work needed, which is a useful control: if the migration reports it as non-conforming, the grammar or the parent has drifted.
- REWRITING A ROW INVALIDATES AN IN-FLIGHT BEGIN RECEIPT, WHICH IS THE MID-FLIGHT CASE OQ-01 ASKS ABOUT AND IS ITS REAL MECHANISM (added at review, PR-006). `ipd_lifecycle.frozen_region_digest` covers each E-item's ACTION TEXT, so changing `CONFIRM <id6> REACHED <status>` MOVES the digest and `finalize_precheck` then refuses with "the begin receipt ... is STALE". Verified at review on a synthetic orchestrator: swapping the child id6 in one row CHANGES the digest, while adding a BARE continuation line does NOT (the digest reads `Leaf.text`, the opening line only). TWO CONSEQUENCES for E-02's route decision, which currently treats the mid-flight case as purely a checklist edit. FIRST, rewriting a row on a plan with a LIVE begin receipt is not free: that plan can no longer finalize against its receipt. SECOND, the safe ordering follows from the measurement: a plan with no live receipt may be rewritten freely, and a plan with one should either be left until its receipt is consumed or be rewritten and have the staleness accepted DELIBERATELY with the reason recorded. Eleven of the twelve orchestrators measured at review are `approved` or `reviewed` rather than mid-execution, so this is expected to be rare, and 'rare' is not 'impossible': check for a live receipt per plan before rewriting it rather than assuming.
- SUITE BARE: `python3 -m pytest`; compare failing NODE IDS, not totals.

## Findings

| Id | Severity | Location (symbol / content anchor) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | the live pending-plans tree | ZERO rows conform pre-migration, so every pending orchestrator refuses once child 03 lands. That is expected and is this child's reason to exist, not a defect in child 03. | measured against the R1a grammar at HEAD `21eff5d8` |
| F-2 | HIGH | the same tree, measured three times | The population moved 10 -> 11 -> 12 within about a day (38 `E-*` rows at authoring, widest `2xz59a` at 9). No count may be treated as a fixture, and E-01 re-derives. | three measurements during design and authoring |
| F-3 | HIGH | rows with first lines of 133 to 1528 characters | Most rows are not a mechanical rewrite: they carry orchestration meaning that must be relocated. A migration that deletes it satisfies the grammar and breaks R2. | the row-length census |
| F-4 | MEDIUM | `y9s4vm` E-02; `lyo1tz` E-02; `s0gnha` E-02 | Some rows weld a tracking half to a condition half. All three measured cases resolved to duplication of a child's own assertion or to work already relocated into a child (`svacmz`), so the usual answer is DELETE the duplicate half; but that judgement is per row and must be evidenced, not assumed. | each child's own Scope and V-items read |
| F-5 | MEDIUM | `check_engine.CARRIER_CUTOVER_DATE` | A cutover mechanism already exists and is the precedent E-02 should weigh, rather than inventing one. | source read |
| F-6 | MEDIUM | `d1u4sy` (this Set's parent) | Already conforming by construction, so it is a control on the census rather than migration work. | the parent's five rows |
| F-7 | LOW | criterion 12 | The bar is outcome-shaped ("no Set left refused with no remedy"), so a route that fixes new plans while stranding an approved one fails it even though the check passes for future work. | the criterion's text |

## Proposed changes (ordered, validatable)

1. E-01 re-derives the population and the per-row census, reading each plan's own Kind bullet.
2. E-02 chooses and justifies the route against criterion 12, including the mid-flight case.
3. E-03 rewrites the rows, relocating displaced prose to one of three destinations and reporting ambiguity.
4. E-04 records a per-orchestrator disposition.
5. E-05 re-runs the census and reconciles it against that disposition.

## Deferred / out of scope (with reason)

- THE GRAMMAR, THE FUNCTION, THE REVIEW LOOP, AND THE RUNNER GATE: children 01, 02 and 03 own them. This child consumes the grammar and must not adjust it to make a stubborn plan pass; a grammar that cannot express a legitimate row is a finding against child 01, not a licence to widen it here.
  - Carrier-Declined: Owned by named siblings in this Set.
- AUTHORING THE SUBSTANCE OF ANY NEW FINAL CHILD beyond what relocation requires: if displaced text turns out to be a real uncovered obligation, this child creates the child plan and moves the text; designing that work properly is its own plan.
  - Carrier: wtd5m2
- CHANGING ANY ORCHESTRATOR'S STATUS OR LIFECYCLE POSITION: strictly out of scope. These are other agents' plans and several are `approved`; a checklist rewrite is not a lifecycle event.
  - Carrier-Declined: An explicit boundary rather than deferred work.
- MIGRATING TERMINAL ORCHESTRATORS (`executed/`, `superseded/`): out of scope. A terminal plan is a historical record and rewriting its checklist would falsify it; the gate only reaches queued plans.
  - Carrier-Declined: Editing history is never correct here, so there is nothing to carry.

## Scope check

- Over-scope: `agent_workflows/ipd_lint.py` and `tests/test_orchestrator_row_grammar.py` are declared because E-02 may need to add a cutover constant and its pin. If the chosen route is migrate-all, both are reconciled UNCHANGED with a `--scope-ack`, which is the honest record of "checked, no change needed".
- Under-scope: `.aw/records/plans/pending` is declared as a directory because the exact set of plan files is not knowable until E-01 runs. An executor must still list, in the disposition record, every file it actually edited, so the reconciliation is auditable despite the broad declaration.

## Required tests / validation

`python3 -m pytest` BARE, in an isolated worktree, baseline measured there, compared by failing NODE ID.

Beyond the suite, and this is where the real validation lives: the pre- and post-migration censuses with their denominators; the per-orchestrator disposition; and for a SAMPLE of migrated plans, a before/after diff showing each displaced piece of prose in its new location. `aw ipd lint` must still report every migrated plan conforming, since a rewrite that breaks the plan schema has traded one refusal for another.

## Spec / documentation sync

N/A with reason: spec `r07vma` criterion 12 constrains this child's outcome and is implemented as written. No `.spec.md` path is declared. If the chosen route requires a cutover date, that is a code constant rather than a spec change. Note that if an executor finds criterion 12 unachievable by any of the three admissible routes, that is a finding against the spec worth reporting rather than a reason to lower the bar.

## Open questions

### OQ-01: What happens to an orchestrator that is mid-flight (children partly executed) when the gate lands?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, because E-02 must state an answer as part of choosing the route, and every admissible route can accommodate one. SHARPENED AT REVIEW (PR-006): the mid-flight hazard is NOT only that the Set is in progress, it is that rewriting a row MOVES `frozen_region_digest` and so STALES any live begin receipt, measured at review. So the answer E-02 must state is per-plan and mechanical: does this orchestrator have a live begin receipt, and if so is the rewrite deferred until the receipt is consumed or performed with the staleness accepted and recorded. It is recorded because the wrong answer strands work: an orchestrator whose children are half executed cannot simply be refused until rewritten, since the Set is already in progress and the runner retires the parent programmatically once the children finish. PROPOSED DIRECTION: migrate mid-flight orchestrators FIRST and explicitly, since their rewrite is purely a checklist edit and does not touch any child's state or the parent's Status; that keeps them runnable and avoids needing a grandfather path at all. If a mid-flight parent cannot be rewritten safely for some reason this plan has not anticipated, grandfather that one plan by name with the reason recorded, rather than adding a general exemption that would outlive the migration.
- Carrier-Declined: SELF-CLOSING INSIDE THIS PLAN'S OWN EXECUTION (added at review, PR-002). E-02 must state the mid-flight answer as part of choosing the route, and V-02 demands that answer as pasted evidence, so the question is discharged by this plan's own gate rather than handed onward. A grandfather clause, if one is chosen, is recorded per orchestrator in E-04's disposition record, which is this plan's artifact.


## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the pre-migration census in full: every orchestrator's id6, Status and row count, plus the total row count and the population denominator, all read at execution time. State how Kind was determined and show it was the plan's OWN first bullet. Confirm the count against this plan's 12 and EXPLAIN any difference rather than absorbing it, since a difference is expected.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: state the route chosen and the reasoning, explicitly against criterion 12's bar. State what happens to a mid-flight orchestrator (OQ-01). If a cutover was chosen, paste the constant and the helper; if migrate-all, say so and confirm the two code paths are reconciled unchanged with a `--scope-ack`. ALSO state, per orchestrator you intend to rewrite, whether it has a LIVE begin receipt, and what you did about it (PR-006): rewriting a row moves `frozen_region_digest` and stales such a receipt, so 'it is only a checklist edit' is not a sufficient answer for a plan mid-execution.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: for at least THREE migrated orchestrators spanning the range (one nearly schema-shaped, one with a long prose row, one with a welded tracking-plus-condition row), paste the before and after checklists side by side and NAME where each displaced piece of prose went. Paste `aw ipd lint` conforming for each migrated plan. Explicitly confirm no row's meaning was deleted; a diff that only removes text FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the disposition record covering every orchestrator in E-01's denominator, each marked conformed, grandfathered (mechanism named) or escalated (decision named). Confirm the count matches the denominator exactly; an omission is a failed migration regardless of what the grammar reports.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the post-migration census and reconcile it line by line against the disposition record. Confirm `d1u4sy` appears as conforming with no work needed, which is the control. Explain every non-conformer by a named route decision; an unexplained non-conformer means the migration missed a plan and this item FAILS.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Size note: 5 E-leaves in 2 groups. The row count is modest (38 at authoring) but the work is per-plan judgement rather than a sweep, which is why the census and disposition items exist around the rewrite.
- Cohesion rationale: E-01 and E-02 are measure-then-decide and must precede any edit, because the route determines which plans are touched. E-03 through E-05 are the migration and its audit: the rewrite, the per-plan disposition that makes criterion 12 checkable, and the reconciliation that catches a silent miss. Splitting the audit from the rewrite would leave a migration nobody can verify.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since a rejected hook can leave paths in the index. When reporting tests passed, paste the ACTUAL runner output. THIS CHILD EDITS OTHER AGENTS' PLANS, which is authorised here ONLY for the checklist rewrite: never change a Status, never move a plan between directories, never touch a terminal plan, and never sweep a co-worker's unrelated staged change into a commit. Prefer many small path-scoped commits over one large one, so a mistake on one plan is revertable without touching the rest.

Post-gate lifecycle: requires `/plan-review` then explicit human approval (`aw ipd set approved 68uhp0 --by-human --message ...`). Do NOT hand-write a `- Readiness:` field. Its `- Item-Dependencies:` refuse dispatch until `0xmk4e` is executed. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
