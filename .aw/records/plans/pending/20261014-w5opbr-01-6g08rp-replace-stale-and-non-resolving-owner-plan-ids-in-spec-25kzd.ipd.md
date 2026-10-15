# IPD: Replace stale and non-resolving owner plan IDs in spec 25kzda Section 5.5 table

- Date: 2026-10-14
- Kind: child
- Concern: Spec 25kzda Section 5.5 retry policy table owner plan IDs, Order numbers, and status labels
- Scope: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md Section 5.5 ("### 5.5 Retry policy") and tests/test_fixfirst_end_to_end.py
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, tests/test_fixfirst_end_to_end.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
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
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
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

- [ ] E-02 In `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` under `### 5.5 Retry policy`, update the `verifier transport failure` row's `Notes` cell so it no longer cites `Order 04 (\`ytas91\`)` and instead cites `yd4tqw` (from backlog `jodcz3`), editing the row in place (one line stays one line). Re-derive `yd4tqw`'s location at execution time with `aw find plans yd4tqw`: write `Implementing: \`yd4tqw\` (from backlog \`jodcz3\`).` if it is still in `.aw/records/plans/pending/`, or `Shipped (\`yd4tqw\`, from backlog \`jodcz3\`).` if it is in `.aw/records/plans/executed/`. If `yd4tqw` E-05 has already rewritten the row (its form is `Implementing: yd4tqw (from backlog jodcz3).`, without backticks), keep its wording and only normalize the backticks and the status prefix to the rule above; do not touch the `verification_retry_decision` bullet, which `yd4tqw` E-05 owns. Then record a workflow history note on spec `25kzda` via `aw specs note` citing `6g08rp` and `w5opbr`.
  - Depends on: E-01
  - Expected outcome: The `verifier transport failure` row in Section 5.5 cites `yd4tqw` and `jodcz3` instead of the stale `ytas91` reference, line numbers above `## Workflow history` in spec `25kzda` are preserved unchanged, and `## Workflow history` records the update.
  - Execution state: pending

### Task group 2: End-to-end spec Section 5.5 owner-citation resolution test and suite validation

- [ ] E-03 In `tests/test_fixfirst_end_to_end.py`, add a module-level pure checker `_spec_5_5_owner_problems(spec_text: str, repo_root: Path) -> list[str]` and two tests on `TestFixFirstEndToEnd` beside `test_e05_spec_abort_classes_match`. The module has NO `locate_spec_25kzda` helper (that name exists only in `tests/test_retry_budget_citation.py` and `tests/test_run_finding_spec_transcription.py`), so add a local `_locate_spec_25kzda(repo_root)` that mirrors `tests/test_retry_budget_citation.py` `locate_spec_25kzda` (`rglob("*-25kzda-*.spec.md")` under `.aw/records/specs/`, raising unless exactly one match), with `repo_root = Path(__file__).resolve().parents[1]`. The checker slices the text from `### 5.5 Retry policy` up to `### 5.6`, takes the retry-policy table rows (lines starting `| ` after the `| Spec Class | Disposition(s) |` header, excluding the separator), and returns one problem string per violation of: (a) any of `k8n97m`, `120bhh`, `b8w5o6`, `5j73i6` appears anywhere in the slice; (b) a backticked token matching `artifact_core.ID6_RE` in a row's LAST (`Notes`) cell does not resolve via `selectors.resolve(repo_root, <type>, token, allow=frozenset({selectors.MATCH_ID6}))` to exactly one path for record type `plans` or `backlog` (DERIVE the token set from the table at run time; do not hard-code it); (c) for every Notes cell matching `Order (\d\d), \`(<id6>)\``, the cited id6 is a `plans` record whose `- Order:` equals that number, whose `- Set:` first token is `fixfirst`, whose `- Status:` (via `selectors.read_front_matter_status`) is `executed`, and the cell starts its status phrase with `Shipped` (any `Implementing:` beside an executed plan is a problem); and (d) the `verifier transport failure` row's Notes cell contains `yd4tqw` and `jodcz3` (backticked or not) and not `ytas91`. Test 1 (e.g. `test_e05_spec_5_5_table_owner_ids_resolve`) asserts the checker returns `[]` on the live spec. Test 2 (e.g. `test_e05_spec_5_5_checker_rejects_stale_owner`) feeds the checker three mutated copies of the live spec text (one row's Notes reverted to `Implementing: Order 05 (\`k8n97m\`).`; the `a red combined suite after merge` row's `Order 05` changed to `Order 06`; the `verifier transport failure` row reverted to `Implementing: Order 04 (\`ytas91\`).`) and asserts each yields a non-empty problem list, proving the guard fires. Test function names are pointers only.
  - Depends on: E-01, E-02
  - Expected outcome: The checker returns no problems on the live spec and returns at least one problem for each of the three mutated copies, so a reintroduced non-resolving id6, wrong Set `fixfirst` Order mapping, stale `Implementing:` label, or `ytas91` on the verifier-transport row fails `python3 -m pytest tests/test_fixfirst_end_to_end.py`.
  - Execution state: pending

- [ ] E-04 Run `aw specs check .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, the targeted module `python3 -m pytest tests/test_fixfirst_end_to_end.py`, the full test suite `python3 -m pytest`, and `aw sanitize --agent`.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `aw specs check` exits 0 with `valid: True`, `python3 -m pytest tests/test_fixfirst_end_to_end.py` and `python3 -m pytest` exit 0 with zero failures, and `aw sanitize --agent` exits 0 with `"outcome":"clean"`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec `25kzda` lives at `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (`- Status: approved`, `- Id: 25kzda`). Edits to an `approved` spec's body must preserve line offsets above `## Workflow history` whenever possible so `spec_citations.new_stale_anchors` (checked by the runner merge gate `spec-anchor-new-stale`) detects zero newly shifted `25kzda:L<N>` citations across the plans tree, and must record a `## Workflow history` note via `aw specs note`.
- `tests/test_fixfirst_end_to_end.py` has NO spec locator (corrected at review). `def locate_spec_25kzda(repo_root: pathlib.Path)` lives at `tests/test_retry_budget_citation.py:24` (and a twin at `tests/test_run_finding_spec_transcription.py:31`). `TestFixFirstEndToEnd` is at `tests/test_fixfirst_end_to_end.py:139`; `def test_e05_spec_abort_classes_match(self) -> None:` is at line ~1251 and compares `run_evidence.ABORT_CLASSES` with spec Section 4.1, not Section 5.5.
- `agent_workflows.selectors.resolve` (`def resolve(` at line 850 of `agent_workflows/selectors.py`; signature `resolve(repo_root, record_type, selector, *, allow=None, deny=None)`, returns a `Resolution` with `.kind` and `.paths`; review probe: `resolve(Path('.'), 'plans', 'w9nvq4', allow=frozenset({MATCH_ID6}))` -> kind `id6`, one path under `executed/`; `'backlog','jodcz3'` and `'backlog','oq05nc'` resolve; `'plans','k8n97m'` -> no paths) with `allow=frozenset({selectors.MATCH_ID6})` and `agent_workflows.selectors.read_front_matter_status` are the repository's public front-matter resolution primitives for verifying that an `<id6>` token resolves to a declared record in `.aw/records/` and checking its `- Status:` (`read_front_matter_status(text)` at line 501 takes file TEXT, not a path).
- Set `fixfirst` child Orders (orchestrator `lxb1ew` `## Child IPDs`, `.aw/records/plans/executed/20261007-fixfirst-00-lxb1ew-fix-first-send-agent-caused-run-failures-back-to-the-agent-i.ipd.md:98-109`, matching each child's `- Order:`): 02 `tha7a6`, 04 `ytas91`, 05 `w9nvq4`, 06 `psgyzw`, 07 `62sdwr`; all `- Status: executed`.
- Sibling `yd4tqw` (pending, `to-review`) also edits the `verifier transport failure` row (its E-05, which writes `Implementing: yd4tqw (from backlog jodcz3).` and never flips it to `Shipped`) and also edits `tests/test_fixfirst_end_to_end.py` (its E-04). Overlap is not a runtime hazard: the runner isolates each item in its own worktree and merges through the revalidate gate.
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
   - Add a pure checker plus a live-spec test and a mutated-copy contrastive test; parse the Section 5.5 table and verify via `agent_workflows.selectors.resolve` and `agent_workflows.selectors.read_front_matter_status` that every cited artifact ID in `Notes` resolves, that no non-resolving placeholder ID remains, that every `Order NN, <id6>` citation matches that plan's `- Order:` and Set `fixfirst` and that it is `Shipped` beside an `executed` plan, and that the `verifier transport failure` row cites `yd4tqw` and `jodcz3`.
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
- Resolution or deferral rationale: Resolved from repository evidence (`.aw/records/plans/pending/20261014-jodcz3-01-yd4tqw-classify-and-remand-verifier-transport-failures-under-verifi.ipd.md` E-05). Both plans agree that the `verifier transport failure` row must cite `yd4tqw` (from backlog `jodcz3`) instead of `ytas91`. E-02 checks whether `yd4tqw` is still pending or already executed at the moment `6g08rp` executes, writing `Implementing: \`yd4tqw\` (from backlog \`jodcz3\`).` if `yd4tqw` is pending or `Shipped (\`yd4tqw\`, from backlog \`jodcz3\`).` if `yd4tqw` has already executed, and the E-03 checker accepts either status prefix (and either backtick form) for `yd4tqw` while requiring both `yd4tqw` and `jodcz3` to be cited and to resolve. Corrected at review: `yd4tqw` E-05 writes `Implementing: yd4tqw (from backlog jodcz3).` and does NOT flip the row to `Shipped` on execution, so if `6g08rp` executes first the row reads `Implementing:` after `yd4tqw` executes too; flipping it then is outside this plan (it can only happen after `yd4tqw` executes) and is a follow-up for `yd4tqw` or a later sync, not something `6g08rp` can do. The E-03 checker deliberately does not require `Shipped` on this row for that reason.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Output of `git diff -- .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` showing the seven Set `fixfirst` rows in `### 5.5 Retry policy` updated in place to `Shipped (Order 04, \`ytas91\`).`, `Shipped (Order 05, \`w9nvq4\`).`, `Shipped (Order 06, \`psgyzw\`).`, `Shipped (Order 07, \`62sdwr\`).`, and `Shipped (Order 02, \`tha7a6\`).`, showing `#### Live legacy-spelled token: failed-safely` updated to `executed plan \`ytas91\` introduces`, and confirming zero occurrences of `k8n97m`, `120bhh`, `b8w5o6`, or `5j73i6` in the spec.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Output of `git diff -- .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` showing the `verifier transport failure` row in `### 5.5 Retry policy` citing `yd4tqw` and `jodcz3` instead of `ytas91`, plus the appended `## Workflow history` entry recorded via `aw specs note`, the pasted `aw find plans yd4tqw` output that decided the `Implementing:`/`Shipped` prefix, and `git diff --stat` / `git diff -U0` output showing every hunk above `## Workflow history` is a same-line replacement (no added or removed lines above that heading).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: The `git diff -- tests/test_fixfirst_end_to_end.py` hunk showing the checker deriving id6 tokens from the table (no hard-coded owner list) and both tests, plus pasted pytest output from `python3 -m pytest -o addopts="" tests/test_fixfirst_end_to_end.py -k "spec_5_5" -v` showing the live-spec test and the mutated-copy test both PASSED with zero failures (the names are pointers; re-derive them from the diff).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted command output from `AW_NO_REEXEC=1 python3 -m agent_workflows specs check .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, `python3 -m pytest tests/test_fixfirst_end_to_end.py`, `python3 -m pytest`, and `AW_NO_REEXEC=1 python3 -m agent_workflows sanitize --agent` showing all four commands exiting 0 with zero failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

- Execute only after human approval (`- Status: approved`, set with `aw ipd set approved 6g08rp --by-human ...`). OQ-01 is resolved; no open question remains.
- Order: E-01, E-02, E-03, E-04.
- Scope fence (a declaration, not a stop condition): changes are limited to `- Scope-Paths:`. An out-of-scope edit that proves necessary is made and then justified to the finalize scope gate (`--scope-reason`).
- Spec amendment: this plan edits approved spec `25kzda` (declared in `- Scope-Paths:`); edits above `## Workflow history` are same-line replacements so no `25kzda:L<N>` anchor shifts.
- Honesty rule: every `V-*` MUST carry the ACTUAL pasted command and runner output; never claim a pass that was not run.
- Commit only Scope-Paths files through `aw commit 6g08rp -- <paths>`; never `git add -A`; never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner owns begin/finalize, so do not run `aw ipd finalize` there. In a hand execution, run `aw ipd finalize 6g08rp` once every `V-*` reads `pass` and `aw ipd lint --phase pre-transition` conforms. Never hand-`git mv` the plan to `executed/` or hand-edit `- Status:`.
