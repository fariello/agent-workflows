# IPD: Replace stale and non-resolving owner plan IDs in spec 25kzda Section 5.5 table

- Date: 2026-10-14
- Kind: child
- Concern: Spec 25kzda Section 5.5 retry policy table owner plan IDs, Order numbers, and status labels
- Scope: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md Section 5.5 ("### 5.5 Retry policy") and tests/test_fixfirst_end_to_end.py
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, tests/test_fixfirst_end_to_end.py
- Item-Dependencies: none
- Status: to-review
- From-Spec: 25kzda
- From-Backlog: w5opbr
- Work-Kind: bug
- Priority: medium
- Blocks-Release: f33nrj
- Set: w5opbr (Spec 25kzda Section 5.5 table owner ID cleanup)
- Order: 1
- Highest E allocated: 04
- Author: Antigravity
- Id: 6g08rp

## Workflow history
- 2026-10-14 to-review (aw set): Ready for review; addresses backlog w5opbr

- 2026-10-14 draft (Antigravity): created.

## Goal

Replace the four non-resolving owner plan IDs (`k8n97m`, `120bhh`, `b8w5o6`, `5j73i6`), wrong Set `fixfirst` Order numbers, and stale `Implementing:` status annotations in Section 5.5 (`### 5.5 Retry policy`) of spec `25kzda` with the resolving Set `fixfirst` child plan IDs (`tha7a6`, `ytas91`, `w9nvq4`, `psgyzw`, `62sdwr`) and `yd4tqw` (from backlog `jodcz3`), and enforce resolution of Section 5.5 owner citations in `tests/test_fixfirst_end_to_end.py`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Spec 25kzda Section 5.5 owner plan ID, Order number, and status corrections

- [ ] E-01 In `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` under `### 5.5 Retry policy` (`| What happens | Disposition | Notes |`), update the seven Set `fixfirst` rows and the `#### Live legacy-spelled token: failed-safely` prose in place (without adding or removing lines) so every row cites its actual executed Set `fixfirst` child plan ID, Order number, and `Shipped` status: (1) `stall or turn-limit expiry` from `Implementing: Order 04 (\`ytas91\`).` to `Shipped (Order 04, \`ytas91\`).`; (2) `a hook refusal of any commit` from `Implementing: Order 05 (\`k8n97m\`).` to `Shipped (Order 05, \`w9nvq4\`).`; (3) `a red combined suite after merge` from `Implementing: Order 06 (\`120bhh\`).` to `Shipped (Order 05, \`w9nvq4\`).`; (4) `an out-of-scope change (revert or justify)` from `Implementing: Order 07 (\`b8w5o6\`).` to `Shipped (Order 06, \`psgyzw\`).`; (5) `an unauthorized status change or plan move (undo, use the setter)` from `Implementing: Order 05 (\`k8n97m\`).` to `Shipped (Order 07, \`62sdwr\`).`; (6) `a hook-bypass commit (undo, recommit through the hooks)` from `Implementing: Order 05 (\`k8n97m\`).` to `Shipped (Order 07, \`62sdwr\`).`; (7) `an agent proposal that a gate, tool or approach must change (Order 02)` from `Implementing: Order 02 (\`5j73i6\`).` to `Shipped (Order 02, \`tha7a6\`).`; and (8) in `#### Live legacy-spelled token: failed-safely`, update `(or on the failure-kind marker approved plan \`ytas91\` introduces)` to `(or on the failure-kind marker executed plan \`ytas91\` introduces)`.
  - Depends on: none
  - Expected outcome: All seven Set `fixfirst` rows in the Section 5.5 retry-policy table and the `#### Live legacy-spelled token: failed-safely` paragraph cite the resolving executed Set `fixfirst` child plans (`tha7a6`, `ytas91`, `w9nvq4`, `psgyzw`, `62sdwr`) with their true Order numbers and `Shipped` status, and none of the non-resolving tokens (`k8n97m`, `120bhh`, `b8w5o6`, `5j73i6`) remains in Section 5.5.
  - Execution state: pending

- [ ] E-02 In `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` under `### 5.5 Retry policy`, update the `verifier transport failure` row's `Notes` cell so it no longer cites `Order 04 (\`ytas91\`)` and instead cites `yd4tqw` (from backlog `jodcz3`)—writing `Implementing: \`yd4tqw\` (from backlog \`jodcz3\`).` if `yd4tqw` is still in `.aw/records/plans/pending/`, or `Shipped (\`yd4tqw\`, from backlog \`jodcz3\`).` if `yd4tqw` has already moved to `.aw/records/plans/executed/`—and record a workflow history note on spec `25kzda` via `aw specs note` citing `6g08rp` and `w5opbr`.
  - Depends on: E-01
  - Expected outcome: The `verifier transport failure` row in Section 5.5 cites `yd4tqw` and `jodcz3` instead of the stale `ytas91` reference, line numbers above `## Workflow history` in spec `25kzda` are preserved unchanged, and `## Workflow history` records the update.
  - Execution state: pending

### Task group 2: End-to-end spec Section 5.5 owner-citation resolution test and suite validation

- [ ] E-03 In `tests/test_fixfirst_end_to_end.py`, add `TestFixFirstEndToEnd.test_e05_spec_5_5_table_owner_ids_resolve` alongside `TestFixFirstEndToEnd.test_e05_spec_abort_classes_match` that loads spec `25kzda` via `locate_spec_25kzda()`, extracts the Section 5.5 (`### 5.5 Retry policy`) table and prose up to `### 5.6`, and asserts that: (a) none of the non-resolving tokens (`k8n97m`, `120bhh`, `b8w5o6`, `5j73i6`) appears in Section 5.5; (b) every backticked 6-character artifact ID in the Section 5.5 table's `Notes` column (`ytas91`, `yd4tqw`, `jodcz3`, `w9nvq4`, `psgyzw`, `62sdwr`, `l4vw9o`, `oq05nc`, `tha7a6`) resolves via `agent_workflows.selectors.resolve` with `allow=frozenset({selectors.MATCH_ID6})` to an existing plan or backlog record in `.aw/records/`; (c) every Set `fixfirst` owner row (`ytas91`, `w9nvq4`, `psgyzw`, `62sdwr`, `tha7a6`) carries `Shipped (Order 0N, \`<id6>\`).` in `Notes` and its resolved plan has `- Status: executed` via `agent_workflows.selectors.read_front_matter_status`; and (d) the `verifier transport failure` row cites `yd4tqw` and `jodcz3` and does not cite `ytas91`.
  - Depends on: E-01, E-02
  - Expected outcome: `TestFixFirstEndToEnd.test_e05_spec_5_5_table_owner_ids_resolve` passes when run via `python3 -m pytest tests/test_fixfirst_end_to_end.py` and fails if any non-resolving id6, wrong Set `fixfirst` Order mapping, or stale `Implementing:` label is reintroduced into the Section 5.5 table.
  - Execution state: pending

- [ ] E-04 Run `aw specs check .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, the targeted module `python3 -m pytest tests/test_fixfirst_end_to_end.py`, the full test suite `python3 -m pytest`, and `aw sanitize --agent`.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `aw specs check` exits 0 with `valid: True`, `python3 -m pytest tests/test_fixfirst_end_to_end.py` and `python3 -m pytest` exit 0 with zero failures, and `aw sanitize --agent` exits 0 with `"outcome":"clean"`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec `25kzda` lives at `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (`- Status: approved`, `- Id: 25kzda`). Edits to an `approved` spec's body must preserve line offsets above `## Workflow history` whenever possible so `spec_citations.new_stale_anchors` (checked by the runner merge gate `spec-anchor-new-stale`) detects zero newly shifted `25kzda:L<N>` citations across the plans tree, and must record a `## Workflow history` note via `aw specs note`.
- `tests/test_fixfirst_end_to_end.py` already locates spec `25kzda` via `locate_spec_25kzda()` (`def locate_spec_25kzda() -> Path:` at line 88) and cross-checks Section 5.5 against runtime behavior in `TestFixFirstEndToEnd.test_e05_spec_abort_classes_match` (`def test_e05_spec_abort_classes_match(self) -> None:` at line 844).
- `agent_workflows.selectors.resolve` (`def resolve(` at line 850 of `agent_workflows/selectors.py`) with `allow=frozenset({selectors.MATCH_ID6})` and `agent_workflows.selectors.read_front_matter_status` are the repository's public front-matter resolution primitives for verifying that an `<id6>` token resolves to a declared record in `.aw/records/` and checking its `- Status:`.
- Full test suite runs via bare `python3 -m pytest` (no `-n0`, no `-q`, no `-p no:randomly`).

## Findings

| ID | Severity | Location | Observation |
| --- | --- | --- | --- |
| F-01 | medium | `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (`### 5.5 Retry policy`, lines 1450-1457) | Six rows in the Section 5.5 retry-policy mapping table cite four 6-character plan IDs (`k8n97m` on lines 1450, 1453, 1454; `120bhh` on line 1451; `b8w5o6` on line 1452; `5j73i6` on line 1457) that were written when `tb6lw3` (Order 01 of Set `fixfirst`) drafted the table before the sibling child plans were scaffolded, and that resolve to zero artifacts under `aw find`. |
| F-02 | medium | `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (`### 5.5 Retry policy`, lines 1451-1454) | Four rows in the Section 5.5 table also carry the wrong Set `fixfirst` Order numbers relative to orchestrator `lxb1ew` (`.aw/records/plans/executed/20261007-fixfirst-00-lxb1ew-make-fix-it-and-remand-the-default-when-a-turn-or-check-fail.ipd.md`, `## Child IPDs`): `a red combined suite after merge` says `Order 06` instead of `Order 05` (`w9nvq4` E-03); `an out-of-scope change (revert or justify)` says `Order 07` instead of `Order 06` (`psgyzw`); and `an unauthorized status change or plan move` and `a hook-bypass commit` say `Order 05` instead of `Order 07` (`62sdwr` E-01..E-03). |
| F-03 | low | `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (`### 5.5 Retry policy`, lines 1446 and 1468) | All eight children of Set `fixfirst` (`tb6lw3`, `tha7a6`, `mcbph5`, `ytas91`, `w9nvq4`, `psgyzw`, `62sdwr`, `iksylm`) and orchestrator `lxb1ew` are now `executed` under `.aw/records/plans/executed/`, but the Section 5.5 table rows still say `Implementing:` and line 1468 still says `approved plan \`ytas91\` introduces`. |
| F-04 | medium | `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (`### 5.5 Retry policy`, line 1449) | The `verifier transport failure` row says `Implementing: Order 04 (\`ytas91\`).`, but `ytas91` covered agent-turn crashes, stalls, and spawn failures, not verifier transport failure (`iksylm` F-06). Backlog item `jodcz3` was filed for verifier transport failure and graduated to IPD `yd4tqw` (`.aw/records/plans/pending/20261014-jodcz3-01-yd4tqw-classify-and-remand-verifier-transport-failures-under-verifi.ipd.md`). |

## Proposed changes (ordered, validatable)

1. **Update Set `fixfirst` rows and prose in Section 5.5 of spec `25kzda` (E-01)**:
   - Replace the seven Set `fixfirst` `Notes` cells in `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (`### 5.5 Retry policy`) in place so each names its executed Set `fixfirst` child plan ID, true Order number, and `Shipped` status (`Shipped (Order 04, \`ytas91\`).`, `Shipped (Order 05, \`w9nvq4\`).`, `Shipped (Order 06, \`psgyzw\`).`, `Shipped (Order 07, \`62sdwr\`).`, `Shipped (Order 02, \`tha7a6\`).`), and update `approved plan \`ytas91\` introduces` in `#### Live legacy-spelled token: failed-safely` to `executed plan \`ytas91\` introduces`.
2. **Update the `verifier transport failure` row and append workflow history on spec `25kzda` (E-02)**:
   - Replace `Implementing: Order 04 (\`ytas91\`).` on the `verifier transport failure` row with `Implementing: \`yd4tqw\` (from backlog \`jodcz3\`).` (or `Shipped (\`yd4tqw\`, from backlog \`jodcz3\`).` if `yd4tqw` has already executed before `6g08rp` runs), and record a `## Workflow history` note via `aw specs note`.
3. **Add `test_e05_spec_5_5_table_owner_ids_resolve` in `tests/test_fixfirst_end_to_end.py` (E-03)**:
   - Parse the Section 5.5 table in `tests/test_fixfirst_end_to_end.py` and verify via `agent_workflows.selectors.resolve` and `agent_workflows.selectors.read_front_matter_status` that every cited artifact ID in `Notes` resolves, that no non-resolving placeholder ID remains, that all Set `fixfirst` rows are marked `Shipped` and point to `executed` plans, and that the `verifier transport failure` row cites `yd4tqw` and `jodcz3`.
4. **Run spec check, test suite, and leak sanitizer (E-04)**:
   - Verify `aw specs check`, `python3 -m pytest tests/test_fixfirst_end_to_end.py`, `python3 -m pytest`, and `aw sanitize --agent`.

## Deferred / out of scope (with reason)

- Implementing verifier transport failure classification and remand in `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`: owned by sibling IPD `yd4tqw` (from backlog item `jodcz3`).
  - Carrier: yd4tqw

## Scope check

- Over-scope: none.
- Under-scope: none; every stale or non-resolving owner citation in Section 5.5 of spec `25kzda` identified by backlog item `w5opbr` is updated in E-01 and E-02 and guarded by an automated test in E-03.

## Required tests / validation

- `AW_NO_REEXEC=1 python3 -m agent_workflows specs check .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`
- `python3 -m pytest tests/test_fixfirst_end_to_end.py`
- `python3 -m pytest`
- `AW_NO_REEXEC=1 python3 -m agent_workflows sanitize --agent`

## Spec / documentation sync

- `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` is the primary target of E-01 and E-02; its Section 5.5 retry-policy table and `## Workflow history` are updated directly by this plan.

## Open questions

### OQ-01: How should E-02 handle the `verifier transport failure` row in Section 5.5 given that sibling plan `yd4tqw` (from backlog `jodcz3`) also updates that row when it executes?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved from repository evidence (`.aw/records/plans/pending/20261014-jodcz3-01-yd4tqw-classify-and-remand-verifier-transport-failures-under-verifi.ipd.md` E-05). Both plans agree that the `verifier transport failure` row must cite `yd4tqw` (from backlog `jodcz3`) instead of `ytas91`. E-02 checks whether `yd4tqw` is still pending or already executed at the moment `6g08rp` executes, writing `Implementing: \`yd4tqw\` (from backlog \`jodcz3\`).` if `yd4tqw` is pending (which `yd4tqw` E-05 then flips to `Shipped (\`yd4tqw\`, from backlog \`jodcz3\`).` upon execution) or `Shipped (\`yd4tqw\`, from backlog \`jodcz3\`).` if `yd4tqw` has already executed, and `test_e05_spec_5_5_table_owner_ids_resolve` in E-03 accepts either status prefix for `yd4tqw` while requiring both `yd4tqw` and `jodcz3` to be cited and to resolve.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Output of `git diff -- .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` showing the seven Set `fixfirst` rows in `### 5.5 Retry policy` updated in place to `Shipped (Order 04, \`ytas91\`).`, `Shipped (Order 05, \`w9nvq4\`).`, `Shipped (Order 06, \`psgyzw\`).`, `Shipped (Order 07, \`62sdwr\`).`, and `Shipped (Order 02, \`tha7a6\`).`, showing `#### Live legacy-spelled token: failed-safely` updated to `executed plan \`ytas91\` introduces`, and confirming zero occurrences of `k8n97m`, `120bhh`, `b8w5o6`, or `5j73i6` in the spec.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Output of `git diff -- .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` showing the `verifier transport failure` row in `### 5.5 Retry policy` citing `yd4tqw` and `jodcz3` instead of `ytas91`, plus the appended `## Workflow history` entry recorded via `aw specs note`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted pytest runner output from `python3 -m pytest tests/test_fixfirst_end_to_end.py -k test_e05_spec_5_5_table_owner_ids_resolve` showing `1 passed` and zero failures.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted command output from `AW_NO_REEXEC=1 python3 -m agent_workflows specs check .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, `python3 -m pytest tests/test_fixfirst_end_to_end.py`, `python3 -m pytest`, and `AW_NO_REEXEC=1 python3 -m agent_workflows sanitize --agent` showing all four commands exiting 0 with zero failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This IPD is authored at `- Status: to-review` to graduate backlog item `w5opbr`. Upon human review (`reviewed`) and approval (`approved`), execute E-01 through E-04 in an isolated worktree, populate V-01 through V-04 with concrete pasted command output, transition the plan to `executed` via `aw ipd set executed 6g08rp`, and commit all changes through `aw commit 6g08rp -- <paths>`.
