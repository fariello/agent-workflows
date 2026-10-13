# IPD: Reconcile the shipped-source dangling census and file the unguarded behavioral claims

- Date: 2026-10-11
- Kind: child
- Concern: Orders 01 to 03 retire or repoint 87 residual `19313eed` dangling citations (41 + 19 + 27 at authoring HEAD `8538be828`). Two things no single child can do: (a) prove the WHOLE shipped-source population reached zero once all three have landed, and (b) give every RETIRE-UNGUARDED property (a behavioral guard deleted in `19313eed` that no live test replaces) a tracked carrier, so retiring the citation does not silently abandon the coverage gap. That second point is the backlog item's purpose: "ensure that no dangling test citations are silently abandoned."
- Scope: IN: (1) whole-population measurement over every tracked `agent_workflows/*.py` and `tools/*.py`; (2) cross-check of the three children's disposition tables against that measurement; (3) filing, with `aw backlog new`, one backlog item per cluster of RETIRE-UNGUARDED properties (grouped by deleted test file), each `Work-Kind: chore` unless the child recorded a user-perceptible defect, citing the child plan and site ids, unless an existing live item already owns the file (then record that owner instead). OUT: writing any test (each filed item's own work); editing production source; the sibling-owned clusters, whose own plans carry them.
- Scope-Paths: .aw/records/backlog/open/, .aw/records/plans/pending/20261011-iosmvn-04-ellenm-reconcile-the-shipped-source-dangling-census-and-file-the-un.ipd.md
- Item-Dependencies: executed:yuhl6o, executed:9rthek, executed:ev7t1w
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: iosmvn
- Set: iosmvn
- Order: 4
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ellenm
- Approval: 2026-10-13, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-13 approved (aw set): status set to approved
- 2026-10-13 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed.

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog `iosmvn`.

## Goal

Close the rollup honestly: the shipped-source residual reaches zero, and every behavioral guard that the retirements expose as lost has a backlog carrier.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Reconcile

- [ ] E-01 Run the Set measurement command over `$(git ls-files 'agent_workflows/*.py' 'tools/*.py')` at execution HEAD and record the output and HEAD sha. Expected residual: only the census fixture, `tools/lost_guard_census.py` `print_classifier`'s `mixed_example = "tests/test_dependency_verb.py"` (`ev7t1w` F-01, a census input). Any other line is either a site a child missed or a citation introduced after the child ran; record each with file, enclosing symbol, and which (check the child's E-01 list). This plan edits no source, so every such extra line becomes a RETIRE-UNGUARDED-equivalent entry in E-02's grouped list under a `RESIDUAL` group and gets a carrier in E-03.
  - Depends on: none
  - Expected outcome: the surviving set is exactly the F-01 census fixture (re-derived at execution; `UNRETIRED 1` is the expected shape, not the bar), or every extra line is listed, attributed, and carried into E-02 as `RESIDUAL`.
  - Execution state: pending

- [ ] E-02 Cross-check: collect the appended disposition tables from executed plans `yuhl6o`, `9rthek`, `ev7t1w`; confirm each table's row count equals that child's own recorded E-01 `UNRETIRED N`, and that every row has a disposition in {REPOINT, RETIRE-PIN, RETIRE-UNGUARDED}. Produce the RETIRE-UNGUARDED list grouped by deleted test file (one group per basename; each group lists property, child id6, and site ids), plus the `RESIDUAL` group from E-01 if non-empty. Append it to this plan's Findings as a `Group | Deleted file | Property | Child / sites | Carrier` table with the Carrier column empty until E-03.
  - Depends on: E-01
  - Expected outcome: per-child row count equals that child's E-01 count; the grouped table is appended; any mismatch is listed by child and site.
  - Execution state: pending

### Task group 2: File carriers

- [ ] E-03 First capture `aw check backlog --agent` (the pre-filing baseline; at review HEAD `cb23fb012` it reported 3 findings: 2 `check.name-nonconformant`, 1 `check.collisions-not-checked`). Then, for each E-02 group: (a) dedupe with `rg -lwF <basename> .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending` (`aw find backlog` is NOT a text search: at review `aw find backlog test_lane_permission_posture` gave `no artifact matched`), and run the item's `aw backlog new ...` WITHOUT `--apply` to read its advisory duplicate report. OPEN each hit and judge whether it actually owns restoring that property (`owned-confirmed`) or merely mentions the file (`owned-rejected`); this Set's own plans and backlog `iosmvn` itself never count as owners. Known live owners at review: `mv18lz` (graduated, plan `df486j`) for `test_runner_item_dependencies.py::InRunExecutedDependencyTests`; `2ohbkj` (open) for `test_runner_stop_triggers.py` stop/audit shim routing; `yf1p8y` (graduated, plan `z2ugxc`) for `test_runner_backlog_close.py`. (b) If owned-confirmed, record the owner id6. Otherwise file one item with `aw backlog new --summary "Restore behavioral coverage of <property> lost with tests/<file>" --priority low --work-kind chore --body "<deleted file; property; child plan id6 and site ids; only behavioral outcomes may be restored, never a source-reading pin (P16)>" --apply`, letting the setid default to the item's own id6 (a singleton, as `2ohbkj`). File `--work-kind bug --blocks-release next` instead only when the child's disposition row recorded a user-perceptible defect, citing that row. (c) Write the owner or filed id6 into the E-02 table's Carrier column. Finally re-run `aw check backlog --agent`.
  - Depends on: E-02
  - Expected outcome: every E-02 group has a Carrier (filed id6 or owned-confirmed id6); the post-filing `aw check backlog` diagnostics equal the baseline set (no new rule id or location naming a newly filed item).
  - Execution state: pending

## Project conventions discovered (Step 0)

- SET MEASUREMENT COMMAND: verbatim as recorded in sibling plan `yuhl6o` (Order 01) Project conventions.
- Backlog items are created only through `aw backlog new` (managed block, "What needs attention"); `TODO.md` is not a work surface.
- A `bug` work-kind backlog item must carry `- Blocks-Release:` while live (AGENTS.md "Every live bug gates the next release"); the default here is `chore` because a lost test is a coverage gap, not a user-visible defect, unless the child recorded otherwise.
- Prior art for the same shape: executed `oyh28b` (census filing) and pending `xmr5qj` (uncitedaudit filing).
- `aw find backlog <selector>` matches id6, status, Set and filename only, not body text; body dedupe needs `rg` plus the advisory duplicate report that `aw backlog new` prints without `--apply` (F-03).
- `aw backlog new` writes under `.aw/records/backlog/open/` and does not commit; the executor commits the new files through `aw commit`.

## Findings

| ID | Evidence | Finding |
|---|---|---|
| F-01 | Set measurement at HEAD `8538be828` over all tracked `agent_workflows/*.py` and `tools/*.py`: `UNRETIRED 88` | 87 sites are split across Orders 01-03; the 88th is `tools/lost_guard_census.py` `print_classifier`'s `mixed_example`, a census fixture (`ev7t1w` F-01) that E-01 will show; it is the only expected survivor. Re-measured at review HEAD `cb23fb012` (after `yuhl6o` was integrated but before it executed): `UNRETIRED 88`, with the same per-file split (41 `runner_shared.py`, 19 across the six Order 02 files, 27 across the 17 Order 03 files, 1 `tools/lost_guard_census.py` `print_classifier` `mixed_example`). |
| F-02 | `python3 tools/lost_guard_census.py --dedupe` at HEAD `8538be828`: "SHIPPED-SOURCE SUBSET ... Unowned: 44" | The backlog's "46 unowned" has drifted to 44; this Set reaches every one of them plus owned-by-basename paths that no sibling plan actually edits (e.g. `test_lane_tool_identity.py`, owned only by this rollup's own text). Re-run at review HEAD `cb23fb012`: still `Unowned: 44`. Context only; nothing here is a bar. |
| F-03 | Review at `cb23fb012`: `aw find backlog test_lane_permission_posture` -> `no artifact matched selector`; `aw backlog new --summary "...InRunExecutedDependencyTests" --priority low --work-kind chore` (no `--apply`) -> `candidate duplicate(s) detected ... mv18lz [graduated]` | The original E-03 dedupe (`aw find backlog <basename>`) would have reported every group unowned. The advisory detector plus `rg -lwF` is the working dedupe. Known RETIRE-UNGUARDED candidate already identified at review: `9rthek` S-14 (`tests/test_lane_permission_posture.py`, agy `dangerously_skip_permissions` default); `rg -lwF test_lane_permission_posture` over live backlog finds no owner. |

## Proposed changes (ordered, validatable)

1. E-01 whole-population measurement. 2. E-02 cross-check and grouped RETIRE-UNGUARDED list. 3. E-03 file or attribute a carrier per group.

## Deferred / out of scope (with reason)

- Writing replacement behavioral tests.
  - Carrier-Declined: each backlog item E-03 files carries its own restoration; this Set only retires citations and records carriers.
- The census fixture survivor (F-01).
  - Carrier-Declined: a classifier input, not a citation; see `ev7t1w` F-01.
- Closing backlog `iosmvn` itself.
  - Carrier-Declined: not this plan's act. Under `aw oc run`/`aw agy run` the runner's backlog-close path (`runner_shared.process_backlog_close`) closes a `From-Backlog` item when the run earns it; this plan neither hand-edits nor sets `iosmvn`.

## Scope check

- Over-scope: none; only new backlog files under `.aw/records/backlog/open/` (written by `aw backlog new`) and this plan. No source, test, or other plan is edited.
- Under-scope: none; whole-population closure and carrier filing are both itemized.

## Required tests / validation

- Whole-population measurement (E-01).
- `aw check backlog --agent` before and after filing; the diagnostic set is unchanged except for none naming a new item (E-03). The whole-repo `aw check` is not used as the bar: at review it exits 1 on 178 pre-existing findings across unrelated trees and takes minutes.

## Spec / documentation sync

N/A: no spec governs these comments; the only new records are backlog items created by the tool.

## Open questions

### OQ-01: One backlog item per site, per deleted file, or one rollup?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Per deleted file. A rollup is what this item already was and it proved hard to act on; per-site is too fine (several sites cite one behavioral class). Per-file matches the existing dedicated items `mv18lz`, `yf1p8y`, `2ohbkj`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted whole-population measurement output (every hit line plus `UNRETIRED N`) and `git rev-parse --short HEAD`, with every surviving line attributed (census fixture, or child-missed / introduced-later with file and enclosing symbol).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: per child, the pasted E-01 `UNRETIRED N` from its executed plan beside the row count of its disposition table, and the count of each disposition; plus the appended grouped table (including any `RESIDUAL` group) quoted from this plan.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: per group, the pasted `rg -lwF` output and dry-run duplicate report, then either the pasted `aw backlog new ... --apply` output (id6 and path) or the owner's id6 with the line of its body that owns the property; `grep -n 'Blocks-Release' <path>` for any item filed `bug` (or a statement none was); the completed Carrier column quoted from this plan; and the pasted before and after `aw check backlog --agent` diagnostics.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval recorded through `aw ipd set approved`, and after Orders 01-03 are executed (`- Item-Dependencies:`; the runner re-checks this at dispatch). OQ-01 is resolved; no open question remains.

EXECUTION CONTRACT. Scope fence: the declared Scope-Paths; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), not a stop. Commit only those paths (this plan plus the new backlog files) through `aw commit ellenm -- <paths>`; never `git add -A`, bare, or `-a`, never `--no-verify`, never push; verify `git diff --cached --name-only` before committing. You MUST paste the actual command output for every measurement, dedupe search, `aw backlog new`, and `aw check`; never claim a result you did not run.

POST-GATE LIFECYCLE MOVE. After every `V-*` is `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms: under `aw oc run`/`aw agy run` the runner performs `aw ipd begin`/`aw ipd finalize`; in a manual run use `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never `git mv` the plan or hand-edit `- Status:`. Backlog `iosmvn` carries no `- Blocks-Release:` to inherit.
