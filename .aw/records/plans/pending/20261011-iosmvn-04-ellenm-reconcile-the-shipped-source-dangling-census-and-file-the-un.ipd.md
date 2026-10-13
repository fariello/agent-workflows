# IPD: Reconcile the shipped-source dangling census and file the unguarded behavioral claims

- Date: 2026-10-11
- Kind: child
- Concern: Orders 01 to 03 retire or repoint 87 residual `19313eed` dangling citations (41 + 19 + 27 at authoring HEAD `8538be828`). Two things no single child can do: (a) prove the WHOLE shipped-source population reached zero once all three have landed, and (b) give every RETIRE-UNGUARDED property (a behavioral guard deleted in `19313eed` that no live test replaces) a tracked carrier, so retiring the citation does not silently abandon the coverage gap. That second point is the backlog item's purpose: "ensure that no dangling test citations are silently abandoned."
- Scope: IN: (1) whole-population measurement over every tracked `agent_workflows/*.py` and `tools/*.py`; (2) cross-check of the three children's disposition tables against that measurement; (3) filing, with `aw backlog new`, one backlog item per cluster of RETIRE-UNGUARDED properties (grouped by deleted test file), each `Work-Kind: chore` unless the child recorded a user-perceptible defect, citing the child plan and site ids, unless an existing live item already owns the file (then record that owner instead). OUT: writing any test (each filed item's own work); editing production source; the sibling-owned clusters, whose own plans carry them.
- Scope-Paths: .aw/records/backlog/open/, .aw/records/plans/pending/20261011-iosmvn-04-ellenm-reconcile-the-shipped-source-dangling-census-and-file-the-un.ipd.md
- Item-Dependencies: executed:yuhl6o, executed:9rthek, executed:ev7t1w
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: iosmvn
- Set: iosmvn
- Order: 4
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ellenm

## Workflow history

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog `iosmvn`.

## Goal

Close the rollup honestly: the shipped-source residual reaches zero, and every behavioral guard that the retirements expose as lost has a backlog carrier.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Reconcile

- [ ] E-01 Run the Set measurement command over `$(git ls-files 'agent_workflows/*.py' 'tools/*.py')` at execution HEAD and record the output and HEAD sha. Expected residual: exactly one line, `tools/lost_guard_census.py` `print_classifier`'s `mixed_example = "tests/test_dependency_verb.py"` (`ev7t1w` F-01, a census input); any other line is a site a child missed, reported with its file and symbol.
  - Depends on: none
  - Expected outcome: `UNRETIRED 1` whose single line is the F-01 census fixture, or each extra line is listed and attributed.
  - Execution state: pending

- [ ] E-02 Cross-check: collect the appended disposition tables from executed plans `yuhl6o`, `9rthek`, `ev7t1w`; confirm their row counts sum to the children's E-01 measurements and that every row has a disposition in {REPOINT, RETIRE-PIN, RETIRE-UNGUARDED}. Produce the RETIRE-UNGUARDED list grouped by deleted test file.
  - Depends on: E-01
  - Expected outcome: a pasted grouped list; totals reconcile.
  - Execution state: pending

### Task group 2: File carriers

- [ ] E-03 For each RETIRE-UNGUARDED group: run `aw find backlog <basename>` and `rg -l <basename> .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked`; if a live item already owns restoring that file's behavioral coverage (for example `mv18lz` for `test_runner_item_dependencies.py::InRunExecutedDependencyTests`, `2ohbkj`, `yf1p8y`), record the owner. Otherwise file one item with `aw backlog new --summary "Restore behavioral coverage <file> held for <property>" --priority low --work-kind chore --set <short-setid> --apply` (add `--blocks-release next` only if the item is filed `bug`, per the release-gate rule), whose body names the deleted file, the property, the child plan id6 and site ids, and states that only behavioral outcomes may be restored (P16). Record the id6 or owner per group in this plan.
  - Depends on: E-02
  - Expected outcome: every RETIRE-UNGUARDED group carries a filed id6 or a named live owner; `aw check` reports no new errors.
  - Execution state: pending

## Project conventions discovered (Step 0)

- SET MEASUREMENT COMMAND: verbatim as recorded in sibling plan `yuhl6o` (Order 01) Project conventions.
- Backlog items are created only through `aw backlog new` (managed block, "What needs attention"); `TODO.md` is not a work surface.
- A `bug` work-kind backlog item must carry `- Blocks-Release:` while live (AGENTS.md "Every live bug gates the next release"); the default here is `chore` because a lost test is a coverage gap, not a user-visible defect, unless the child recorded otherwise.
- Prior art for the same shape: executed `oyh28b` (census filing) and pending `xmr5qj` (uncitedaudit filing).

## Findings

| ID | Evidence | Finding |
|---|---|---|
| F-01 | Set measurement at HEAD `8538be828` over all tracked `agent_workflows/*.py` and `tools/*.py`: `UNRETIRED 88` | 87 sites are split across Orders 01-03; the 88th is `tools/lost_guard_census.py` `print_classifier`'s `mixed_example`, a census fixture (`ev7t1w` F-01) that E-01 will show; it is the only expected survivor. |
| F-02 | `python3 tools/lost_guard_census.py --dedupe` at HEAD `8538be828`: "SHIPPED-SOURCE SUBSET ... Unowned: 44" | The backlog's "46 unowned" has drifted to 44; this Set reaches every one of them plus owned-by-basename paths that no sibling plan actually edits (e.g. `test_lane_tool_identity.py`, owned only by this rollup's own text). |

## Proposed changes (ordered, validatable)

1. E-01 whole-population measurement. 2. E-02 cross-check and grouped RETIRE-UNGUARDED list. 3. E-03 file or attribute a carrier per group.

## Deferred / out of scope (with reason)

- Writing replacement behavioral tests.
  - Carrier-Declined: each backlog item E-03 files carries its own restoration; this Set only retires citations and records carriers.
- The census fixture survivor (F-01).
  - Carrier-Declined: a classifier input, not a citation; see `ev7t1w` F-01.

## Scope check

- Over-scope: none; only new backlog files and this plan.
- Under-scope: none; whole-population closure and carrier filing are both itemized.

## Required tests / validation

- Whole-population measurement (E-01).
- `aw check` after filing, no new errors (E-03).

## Spec / documentation sync

N/A: no spec governs these comments; the only new records are backlog items created by the tool.

## Open questions

### OQ-01: One backlog item per site, per deleted file, or one rollup?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Per deleted file. A rollup is what this item already was and it proved hard to act on; per-site is too fine (several sites cite one behavioral class). Per-file matches the existing dedicated items `mv18lz`, `yf1p8y`, `2ohbkj`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted whole-population measurement output and HEAD sha, with every surviving line attributed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted row-count reconciliation per child and the grouped RETIRE-UNGUARDED list.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: per group, the pasted `aw backlog new` output (id6 and path) or the owning item's id6 with the `rg` hit; and the pasted `aw check` summary.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval and after Orders 01-03 are executed. Commit through `aw commit ellenm -- <paths>` limited to the declared Scope-Paths; never push. Move to `executed/` only via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` is `pass` with pasted evidence.
