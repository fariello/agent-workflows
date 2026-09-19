# IPD: Cross-artifact lifecycle symbols and ANSI status styling: one resolver, one palette, every human view

- Date: 2026-09-19
- Kind: orchestrator
- Concern: Spec `uonrjg` (`approved`, `Blocks-Release: next`, 882 lines) requires one shared lifecycle presentation system across every human terminal view, and today the repository has four independent and disagreeing palettes. The work is too large for one plan and has a hard ordering: a re-review gate the spec imposes on itself, then a semantic resolver, then the depth ladder, then the rendering boundary, then four conversion steps that must not delete the old tables until the last one, then the mandatory spec amendment. This orchestrator sequences those eight children so the Set executes completely and in order when an agent is told "execute lifeglyph" with no runner involved.
- Scope: IN: ordering, dependency edges, and whole-Set completion criteria for children 01 through 08. OUT: every unit of implementation work, each of which belongs to exactly one child; this plan performs none of it.
- Scope-Paths: none
- Item-Dependencies: executed:yaxr4i
- Status: to-review
- Set: lifeglyph
- Order: 0
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 2xz59a
- From-Spec: uonrjg
- Blocks-Release: next

## Workflow history

- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored as the Order-0 orchestrator for spec uonrjg's implementation, sequencing eight children per spec Section 12 plus the Section 12a upstream dependency and re-review gate. Carries the spec's `Blocks-Release: next` gate.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Sequence the eight children that implement spec `uonrjg`, so the resolver is built against a settled contract, the conversions happen in an order that never leaves a view broken, and the duplicate tables are deleted only once nothing reads them.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

THIS CHECKLIST IS ORCHESTRATION, NOT WORK. Every item below is "confirm child X reached `executed`", which is performed by executing that child. No item here produces a deliverable, establishes a baseline, or reconciles records, because an orchestrator's items are performed by nobody when a runner retires it: `aw oc run` and `aw agy run` retire an Order-0 parent once every child is `executed` on disk and deliberately SKIP the pre-transition E/V checkpoint. Work parked here would therefore be marked complete having never been performed. The orchestrator coverage gate probes for exactly that and refuses unattended; if it ever fires on this plan, the fix is to ADD A CHILD, never to delete an item.

### Task group 1: Gate and foundations

- [ ] E-01 Confirm child 01 `n4xq3l` (re-review spec uonrjg against the shipped yaxr4i flag surface) reached `executed`.
  - Depends on: none
  - Expected outcome: `n4xq3l` is in `.aw/records/plans/executed/` with `Status: executed`, and the spec carries a re-review round dated after `yaxr4i` executed.
  - Execution state: pending

- [ ] E-02 Confirm child 02 `udgilu` (the stdlib-only lifecycle_style resolver with owner-enum coverage tests) reached `executed`.
  - Depends on: E-01
  - Expected outcome: `udgilu` is `executed`; `agent_workflows/lifecycle_style.py` exists and its A2 enumeration test fails when an owner status lacks a mapping.
  - Execution state: pending

- [ ] E-03 Confirm child 03 `pow5sj` (one depth resolver, the authored 16-color tier, and aw config pinning) reached `executed`.
  - Depends on: E-02
  - Expected outcome: `pow5sj` is `executed`; exactly one depth resolver exists and the R9.3a.2 precedence chain holds at every rung.
  - Execution state: pending

- [ ] E-04 Confirm child 04 `bn026f` (the Term lifecycle rendering helpers and capability matrix) reached `executed`.
  - Depends on: E-03
  - Expected outcome: `bn026f` is `executed`; resolution and rendering are separate and testable, and the six-profile capability matrix passes.
  - Execution state: pending

### Task group 2: Conversions, in the order that never breaks a view

- [ ] E-05 Confirm child 05 `f9t5hz` (convert attention.py with identical status and id6 treatment) reached `executed`.
  - Depends on: E-04
  - Expected outcome: `f9t5hz` is `executed`; `attention.py` holds no lifecycle color literal and no known status renders as silent gray.
  - Execution state: pending

- [ ] E-06 Confirm child 06 `9zvl2w` (convert indexes, status commands, lint views, run viewers) reached `executed`.
  - Depends on: E-05
  - Expected outcome: `9zvl2w` is `executed`; every non-runner human lifecycle view routes through the shared resolver.
  - Execution state: pending

- [ ] E-07 Confirm child 07 `qdd5jq` (convert both runners and render_stream, then delete every duplicate table) reached `executed`.
  - Depends on: E-06
  - Expected outcome: `qdd5jq` is `executed`; `grep -rn "STATUS_COLOR_256" agent_workflows/` returns nothing and the A17 guard test is in place.
  - Execution state: pending

### Task group 3: The mandatory spec amendment

- [ ] E-08 Confirm child 08 `7p3tt8` (amend 25kzda Section 5.6 and ship the canonical legend) reached `executed`.
  - Depends on: E-07
  - Expected outcome: `7p3tt8` is `executed`; `25kzda` Section 5.6 points at `uonrjg`, the user guide's stale 16-color claim is gone, and the legend is generated rather than hand-maintained.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | `20260919-lifeglyph-01-n4xq3l-re-review-spec-uonrjg-against-the-shipped-yaxr4i-flag-surfac.ipd.md` | Discharges the spec's own Section 12a re-review gate against the shipped `yaxr4i` flag surface and rewritten output contract. | `executed:yaxr4i` |
| 02 | `20260919-lifeglyph-02-udgilu-land-the-stdlib-only-lifecycle-style-resolver-with-exhaustiv.ipd.md` | Creates `lifecycle_style.py`: 21 stages, native/runner/ledger mappings, precedence resolver, self-validation, A2 owner-enum tests. | `executed:yaxr4i`, `executed:n4xq3l` |
| 03 | `20260919-lifeglyph-03-pow5sj-resolve-color-depth-once-in-term-py-and-add-the-authored-16.ipd.md` | One depth resolver with the 256/16/none ladder, the authored 16-color palette, and an `aw config` depth pin. | `executed:yaxr4i`, `executed:udgilu` |
| 04 | `20260919-lifeglyph-04-bn026f-add-the-term-lifecycle-rendering-helpers-and-the-capability.ipd.md` | The R10.2 rendering helpers, Section 9.1/9.2 styling rules, grapheme safety, and the A16 capability matrix. | `executed:udgilu`, `executed:pow5sj` |
| 05 | `20260919-lifeglyph-05-f9t5hz-convert-attention-py-to-the-shared-resolver-with-identical-s.ipd.md` | Converts `attention.py`, the first consumer, and replaces its silent gray fallthrough with A20 behavior. | `executed:bn026f` |
| 06 | `20260919-lifeglyph-06-9zvl2w-convert-indexes-status-commands-lint-views-and-run-viewers-t.ipd.md` | Converts `plans_index`, `research_index`, `status_set`, `ipd_lint`, `run_viewer`, and `cli` lifecycle sites. | `executed:f9t5hz` |
| 07 | `20260919-lifeglyph-07-qdd5jq-convert-both-runner-displays-and-render-stream-lifecycle-row.ipd.md` | Converts both runners and `render_stream`, dismantles the re-export chain, deletes every duplicate table, adds the A17 guard. | `executed:9zvl2w` |
| 08 | `20260919-lifeglyph-08-7p3tt8-amend-spec-25kzda-section-5-6-and-ship-the-canonical-legend.ipd.md` | Performs the spec's MANDATORY `25kzda` Section 5.6 amendment, corrects the stale user-guide claim, ships one generated legend. | `executed:qdd5jq` |

The chain is strictly linear by design. Two reasons, both load-bearing rather than stylistic: every child after 02 consumes the module the previous one produced, and the table deletion in 07 is only safe once 05 and 06 have moved their consumers off it. The runner sorts the queue by dependency depth as its FIRST key and re-checks each edge at dispatch, so a child whose edge is unmet is marked `dependency-blocked` and the run continues rather than failing.

## Completion criteria (the whole Set is done only when)

- All eight children are `executed` in `.aw/records/plans/executed/`.
- `agent_workflows/lifecycle_style.py` is the ONLY lifecycle color and glyph table in the package: `grep -rn "STATUS_COLOR_256\|_STATUS_COLOR" agent_workflows/` returns no palette definition or re-export (criterion A17).
- Every acceptance criterion A1 through A21 of spec `uonrjg` has evidence in a child's validation section. No criterion is orphaned across the Set.
- `25kzda` Section 5.6 points at `uonrjg`, so no second live color table remains in the specs tree either (Section 0.5's requirement).
- The full suite passes BARE (`python3 -m pytest`) and `git diff --check` is clean (criterion A21).

## Cross-IPD validation

- CRITERION COVERAGE: A1 to A21 map onto children as follows, and the mapping must be checked rather than assumed. A1/A2/A20 -> `udgilu`; A12a-A12d -> `pow5sj`; A3/A10/A13/A15/A16 -> `bn026f` and `qdd5jq`; A4/A5/A6 -> `udgilu` and `bn026f`; A7/A8/A9 -> `udgilu` (resolver) and `qdd5jq` (runner display); A14 -> `f9t5hz`, `9zvl2w`, `qdd5jq`; A17/A18 -> `qdd5jq`; A19 -> `udgilu`; A21 -> every child's suite run.
- NO ORPHANED CRITERION: if any of A1 to A21 has no child claiming it at review time, that is a missing child and a new one must be authored, not a criterion quietly dropped.
- DELETION ORDERING: no child before 07 may delete `term.py`'s `STATUS_COLOR_256`, because 05 and 06's consumers still read it. A child that deletes early breaks live views.
- MACHINE OUTPUT INVARIANT: each converting child (05, 06, 07) must independently prove `--agent` and `--json` output unchanged. Proving it once is insufficient, because each conversion touches different renderers.
- SPEC AMENDMENT LAST: child 08 documents "no second table remains", which is only true after 07. Landing 08 early would document a state that does not exist.

## Deferred / out of scope (with reason)

- Spec `uonrjg` OQ-02 (whether `needs_input` or `awaiting-human` retires once `run_gates` is wired): the spec holds it open, non-blocking, and explicitly not its own to decide.
  - Carrier-Declined: The spec OWNS this question and declined to answer it on the recorded ground that collapsing two state vocabularies is a lifecycle change its Section 3 excludes. It states its own closing condition (whoever wires `run_gates` into the runners decides) and confirms its tables need no change either way. It is an upstream vocabulary question, not an obligation this presentation Set incurs, so filing a carrier would assert a work item the spec deliberately did not create.
- A shared display-width helper (a wcwidth-style 0/1/2 table): spec Section 9.4 permits one but records that reusing `render_stream`'s ASCII-table-behind-a-capability-flag pattern satisfies the section without one, and calls that the cheaper, already-proven route.
  - Carrier-Declined: A conforming alternative is CHOSEN, not postponed. Section 9.4's contract is satisfied in full by the ASCII route (children `bn026f` and `qdd5jq` both take it), so nothing is outstanding. If a future consumer genuinely needs true display width, Section 9.4 already binds it to be shared rather than per-module, which is that change's constraint and not this Set's debt.
- `25kzda`'s outcome vocabulary, exit codes, and reporting columns: spec Section 0.5 scopes its override to DISPLAY only.
  - Carrier-Declined: Excluded by the granting authority itself rather than deferred. The maintainer's 2026-09-13 ruling bounds the override to display and says so explicitly; there is no obligation to carry, and creating one would assert work the ruling forbids.

## Scope check

- Over-scope: none. This plan carries no implementation item; each of E-01 to E-08 is a child-completion confirmation.
- Under-scope: none. Every unit of work spec Section 12 names is owned by exactly one child, and the Cross-IPD validation section's criterion map is what makes that checkable rather than asserted. The two items spec Section 12a places on the implementing plan are both discharged: the `executed:yaxr4i` edge is declared here and on children 01 to 03, and the re-review obligation is child 01's whole purpose.

## Required tests / validation

This orchestrator runs no tests of its own, because it performs no work. The Set's validation is the union of its children's, and the whole-Set gates are in Completion criteria above: the full BARE suite (`python3 -m pytest`), `git diff --check`, and the A17 grep proving one table remains.

## Open questions

### OQ-01: Is a strictly linear eight-child chain the right shape, or should the conversions run in parallel?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: A SHAPE QUESTION ANSWERED BY THIS PLAN'S OWN STRUCTURE, carrying no residual work. The chain is already authored linearly and the reasons are recorded above (each child consumes the previous child's module; the deletion in 07 requires 05 and 06 to have landed first). If the maintainer prefers more parallelism at review, the remedy is to edit the dependency edges of this Set before approval, which is a review-time revision rather than an obligation that outlives execution. Nothing needs a later record either way.
- Resolution or deferral rationale: NOT BLOCKING because the linear chain is CORRECT if conservative: it cannot produce a broken intermediate state, whereas a parallel arrangement could. The genuine candidates for parallelism are narrow: children 05 and 06 touch disjoint files and could in principle run concurrently once 04 lands, since the runner isolates each execute item in its own worktree and re-validates on merge. I did not do so because 06's "no second table remains" reasoning is easier to validate against a known-converted attention board, and because the spec's own Section 12 lists these as sequential steps 3 and 4. Raised for the maintainer since serializing them costs wall-clock time they may not want to spend.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste `aw show n4xq3l` showing `Status: executed` and a path under `.aw/records/plans/executed/`. Paste the spec's re-review history round, with its date provably after `yaxr4i` executed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste `aw show udgilu` showing `Status: executed`. Paste `ls agent_workflows/lifecycle_style.py` succeeding and the A2 test name from the suite output.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste `aw show pow5sj` showing `Status: executed`. Paste the per-rung precedence evidence from that child's V-items, including the `NO_COLOR`-beats-pinned-depth case.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste `aw show bn026f` showing `Status: executed`. Paste the six capability profiles from that child's V-05 evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste `aw show f9t5hz` showing `Status: executed`. Paste `grep -n "_STATUS_COLOR_256" agent_workflows/attention.py` returning nothing, and the empty `--agent`/`--json` diffs.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste `aw show 9zvl2w` showing `Status: executed`. Paste the per-command empty `--agent`/`--json` diffs for each of the six converted modules.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Paste `aw show qdd5jq` showing `Status: executed`. Paste `grep -rn "STATUS_COLOR_256" agent_workflows/` returning NO matches, and the A17 guard test shown failing against a reintroduced palette then passing.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: Paste `aw show 7p3tt8` showing `Status: executed`. Paste the `25kzda` Section 5.6 diff pointing at `uonrjg`, and the legend drift-guard shown failing against an uncovered 22nd stage then passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Each child requires its own human approval before it executes; approving this orchestrator does not approve them. `aw set approved <id6> --by-human` is the tooled path, and the runner refuses to dispatch an unapproved item.

WHAT A RUNNER DOES WITH THIS PLAN: it is not agent-executed. Once every child of Set `lifeglyph` is `executed` on disk, `aw oc run` and `aw agy run` retire this parent to `executed` in that same run, spending no agent turn. Retirement is gated on every child being `executed` and refuses otherwise, naming which condition it hit: an unauthored row in the child table, a Set with no children, children this run cannot finish, or a refused transition. Such a refusal leaves this plan in `pending/` and is not a run failure; it needs a human act, so report it rather than retrying.

THE ORCHESTRATOR COVERAGE GATE APPLIES TO THIS PLAN. Before any agent turn, a run asks a model once whether this parent carries work no child covers, and refuses unattended when it does. The checklist above is deliberately confined to child-completion confirmations so that gate passes honestly. If it ever fires, ADD A CHILD that owns the uncovered work and add its row to the table above; do NOT delete items to make it pass, which destroys the orchestration checklist and causes the lost work the gate exists to prevent.

On completion: append the workflow-history line, set the terminal `Status: executed`, and `git mv` this plan to `.aw/records/plans/executed/` as a post-gate lifecycle step via `aw ipd finalize`, never as a checklist item. Commit path-scoped; never push.
