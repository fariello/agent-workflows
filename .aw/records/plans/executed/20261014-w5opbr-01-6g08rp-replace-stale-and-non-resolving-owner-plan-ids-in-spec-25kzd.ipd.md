# IPD: Replace stale and non-resolving owner plan IDs in spec 25kzda Section 5.5 table

- Date: 2026-10-14
- Kind: child
- Concern: Spec 25kzda Section 5.5 retry policy table owner plan IDs, Order numbers, and status labels
- Scope: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md Section 5.5 ("### 5.5 Retry policy") and tests/test_fixfirst_end_to_end.py
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, tests/test_fixfirst_end_to_end.py
- Item-Dependencies: none
- Status: executed
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

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 6g08rp verified (set w5opbr, attempt 1).
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-14 to-review (aw set): Ready for review; addresses backlog w5opbr

- 2026-10-14 draft (Antigravity): created.

## Goal

Replace the four non-resolving owner plan IDs (`k8n97m`, `120bhh`, `b8w5o6`, `5j73i6`), wrong Set `fixfirst` Order numbers, and stale `Implementing:` status annotations in Section 5.5 (`### 5.5 Retry policy`) of spec `25kzda` with the resolving Set `fixfirst` child plan IDs (`tha7a6`, `ytas91`, `w9nvq4`, `psgyzw`, `62sdwr`) and `yd4tqw` (from backlog `jodcz3`), and enforce resolution of Section 5.5 owner citations in `tests/test_fixfirst_end_to_end.py`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Spec 25kzda Section 5.5 owner plan ID, Order number, and status corrections

- [x] E-01 In `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` under `### 5.5 Retry policy` (`| What happens | Disposition | Notes |`), update the seven Set `fixfirst` rows and the `#### Live legacy-spelled token: failed-safely` prose in place (without adding or removing lines) so every row cites its actual executed Set `fixfirst` child plan ID, Order number, and `Shipped` status: (1) `stall or turn-limit expiry` from `Implementing: Order 04 (\`ytas91\`).` to `Shipped (Order 04, \`ytas91\`).`; (2) `a hook refusal of any commit` from `Implementing: Order 05 (\`k8n97m\`).` to `Shipped (Order 05, \`w9nvq4\`).`; (3) `a red combined suite after merge` from `Implementing: Order 06 (\`120bhh\`).` to `Shipped (Order 05, \`w9nvq4\`).`; (4) `an out-of-scope change (revert or justify)` from `Implementing: Order 07 (\`b8w5o6\`).` to `Shipped (Order 06, \`psgyzw\`).`; (5) `an unauthorized status change or plan move (undo, use the setter)` from `Implementing: Order 05 (\`k8n97m\`).` to `Shipped (Order 07, \`62sdwr\`).`; (6) `a hook-bypass commit (undo, recommit through the hooks)` from `Implementing: Order 05 (\`k8n97m\`).` to `Shipped (Order 07, \`62sdwr\`).`; (7) `an agent proposal that a gate, tool or approach must change (Order 02)` from `Implementing: Order 02 (\`5j73i6\`).` to `Shipped (Order 02, \`tha7a6\`).`; and (8) in `#### Live legacy-spelled token: failed-safely`, update `(or on the failure-kind marker approved plan \`ytas91\` introduces)` to `(or on the failure-kind marker executed plan \`ytas91\` introduces)`.
  - Depends on: none
  - Expected outcome: All seven Set `fixfirst` rows in the Section 5.5 retry-policy table and the `#### Live legacy-spelled token: failed-safely` paragraph cite the resolving executed Set `fixfirst` child plans (`tha7a6`, `ytas91`, `w9nvq4`, `psgyzw`, `62sdwr`) with their true Order numbers and `Shipped` status, and none of the non-resolving tokens (`k8n97m`, `120bhh`, `b8w5o6`, `5j73i6`) remains in Section 5.5.
  - Execution state: performed

- [x] E-02 In `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` under `### 5.5 Retry policy`, update the `verifier transport failure` row's `Notes` cell so it no longer cites `Order 04 (\`ytas91\`)` and instead cites `yd4tqw` (from backlog `jodcz3`), editing the row in place (one line stays one line). Re-derive `yd4tqw`'s location at execution time with `aw find plans yd4tqw`: write `Implementing: \`yd4tqw\` (from backlog \`jodcz3\`).` if it is still in `.aw/records/plans/pending/`, or `Shipped (\`yd4tqw\`, from backlog \`jodcz3\`).` if it is in `.aw/records/plans/executed/`. If `yd4tqw` E-05 has already rewritten the row (its form is `Implementing: yd4tqw (from backlog jodcz3).`, without backticks), keep its wording and only normalize the backticks and the status prefix to the rule above; do not touch the `verification_retry_decision` bullet, which `yd4tqw` E-05 owns. Then record a workflow history note on spec `25kzda` via `aw specs note` citing `6g08rp` and `w5opbr`.
  - Depends on: E-01
  - Expected outcome: The `verifier transport failure` row in Section 5.5 cites `yd4tqw` and `jodcz3` instead of the stale `ytas91` reference, line numbers above `## Workflow history` in spec `25kzda` are preserved unchanged, and `## Workflow history` records the update.
  - Execution state: performed

### Task group 2: End-to-end spec Section 5.5 owner-citation resolution test and suite validation

- [x] E-03 In `tests/test_fixfirst_end_to_end.py`, add a module-level pure checker `_spec_5_5_owner_problems(spec_text: str, repo_root: Path) -> list[str]` and two tests on `TestFixFirstEndToEnd` beside `test_e05_spec_abort_classes_match`. The module has NO `locate_spec_25kzda` helper (that name exists only in `tests/test_retry_budget_citation.py` and `tests/test_run_finding_spec_transcription.py`), so add a local `_locate_spec_25kzda(repo_root)` that mirrors `tests/test_retry_budget_citation.py` `locate_spec_25kzda` (`rglob("*-25kzda-*.spec.md")` under `.aw/records/specs/`, raising unless exactly one match), with `repo_root = Path(__file__).resolve().parents[1]`. The checker slices the text from `### 5.5 Retry policy` up to `### 5.6`, takes the retry-policy table rows (lines starting `| ` after the `| Spec Class | Disposition(s) |` header, excluding the separator), and returns one problem string per violation of: (a) any of `k8n97m`, `120bhh`, `b8w5o6`, `5j73i6` appears anywhere in the slice; (b) a backticked token matching `artifact_core.ID6_RE` in a row's LAST (`Notes`) cell does not resolve via `selectors.resolve(repo_root, <type>, token, allow=frozenset({selectors.MATCH_ID6}))` to exactly one path for record type `plans` or `backlog` (DERIVE the token set from the table at run time; do not hard-code it); (c) for every Notes cell matching `Order (\d\d), \`(<id6>)\``, the cited id6 is a `plans` record whose `- Order:` equals that number, whose `- Set:` first token is `fixfirst`, whose `- Status:` (via `selectors.read_front_matter_status`) is `executed`, and the cell starts its status phrase with `Shipped` (any `Implementing:` beside an executed plan is a problem); and (d) the `verifier transport failure` row's Notes cell contains `yd4tqw` and `jodcz3` (backticked or not) and not `ytas91`. Test 1 (e.g. `test_e05_spec_5_5_table_owner_ids_resolve`) asserts the checker returns `[]` on the live spec. Test 2 (e.g. `test_e05_spec_5_5_checker_rejects_stale_owner`) feeds the checker three mutated copies of the live spec text (one row's Notes reverted to `Implementing: Order 05 (\`k8n97m\`).`; the `a red combined suite after merge` row's `Order 05` changed to `Order 06`; the `verifier transport failure` row reverted to `Implementing: Order 04 (\`ytas91\`).`) and asserts each yields a non-empty problem list, proving the guard fires. Test function names are pointers only.
  - Depends on: E-01, E-02
  - Expected outcome: The checker returns no problems on the live spec and returns at least one problem for each of the three mutated copies, so a reintroduced non-resolving id6, wrong Set `fixfirst` Order mapping, stale `Implementing:` label, or `ytas91` on the verifier-transport row fails `python3 -m pytest tests/test_fixfirst_end_to_end.py`.
  - Execution state: performed

- [x] E-04 Run `aw specs check .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, the targeted module `python3 -m pytest tests/test_fixfirst_end_to_end.py`, the full test suite `python3 -m pytest`, and `aw sanitize --agent`.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `aw specs check` exits 0 with `valid: True`, `python3 -m pytest tests/test_fixfirst_end_to_end.py` and `python3 -m pytest` exit 0 with zero failures, and `aw sanitize --agent` exits 0 with `"outcome":"clean"`.
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: Output of `git diff -- .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` showing the seven Set `fixfirst` rows in `### 5.5 Retry policy` updated in place to `Shipped (Order 04, \`ytas91\`).`, `Shipped (Order 05, \`w9nvq4\`).`, `Shipped (Order 06, \`psgyzw\`).`, `Shipped (Order 07, \`62sdwr\`).`, and `Shipped (Order 02, \`tha7a6\`).`, showing `#### Live legacy-spelled token: failed-safely` updated to `executed plan \`ytas91\` introduces`, and confirming zero occurrences of `k8n97m`, `120bhh`, `b8w5o6`, or `5j73i6` in the spec.
  - Observed evidence:
    `git diff -- .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` hunks for table and prose:
    ```diff
    @@ -1446 +1446 @@ The normative mapping between the retry classes above and the runner's dispositi
    -| stall or turn-limit expiry | `failed-safely`, `timeout` | `turn_failure_is_retryable` | Yes | Host stall or turn-limit expiry without response. Evidence: turn timer or runner watchdog. Implementing: Order 04 (`ytas91`). |
    +| stall or turn-limit expiry | `failed-safely`, `timeout` | `turn_failure_is_retryable` | Yes | Host stall or turn-limit expiry without response. Evidence: turn timer or runner watchdog. Shipped (Order 04, `ytas91`). |
    @@ -1449,6 +1449,6 @@ The normative mapping between the retry classes above and the runner's dispositi
    -| verifier transport failure | `verifier-transport-error` | `verification_retry_decision` | Yes | Skeptical verifier session crash or transport failure. Implementing: Order 04 (`ytas91`). |
    -| a hook refusal of any commit | `hook-refused` | `turn_failure_is_retryable` / commit gateway | Yes | Pre-commit hook rejected commit. Worktree preserved; fix-it turn given hook output. Implementing: Order 05 (`k8n97m`). |
    -| a red combined suite after merge | `integration-test-failed` | integration gate | Yes | Verification suite failed after merge in lane or integration worktree. Implementing: Order 06 (`120bhh`). |
    -| an out-of-scope change (revert or justify) | `fail-gate` | `turn_failure_is_retryable` / finalize gate | Yes | Delta outside frozen scope. Agent may revert edit or record justification widening scope. Implementing: Order 07 (`b8w5o6`). |
    -| an unauthorized status change or plan move (undo, use the setter) | `fail-gate` | `turn_failure_is_retryable` / finalize gate | Yes | Unsanctioned status mutation or plan file relocation. Fix-it turn instructs undo and setter invocation. Implementing: Order 05 (`k8n97m`). |
    -| a hook-bypass commit (undo, recommit through the hooks) | `fail-gate` | `turn_failure_is_retryable` / commit gateway | Yes | Commit attempted with `--no-verify` or bypass. Fix-it turn instructs undo and recommit via hooks. Implementing: Order 05 (`k8n97m`). |
    +| verifier transport failure | `verifier-transport-error` | `verification_retry_decision` | Yes | Skeptical verifier session crash or transport failure. Implementing: `yd4tqw` (from backlog `jodcz3`). |
    +| a hook refusal of any commit | `hook-refused` | `turn_failure_is_retryable` / commit gateway | Yes | Pre-commit hook rejected commit. Worktree preserved; fix-it turn given hook output. Shipped (Order 05, `w9nvq4`). |
    +| a red combined suite after merge | `integration-test-failed` | integration gate | Yes | Verification suite failed after merge in lane or integration worktree. Shipped (Order 05, `w9nvq4`). |
    +| an out-of-scope change (revert or justify) | `fail-gate` | `turn_failure_is_retryable` / finalize gate | Yes | Delta outside frozen scope. Agent may revert edit or record justification widening scope. Shipped (Order 06, `psgyzw`). |
    +| an unauthorized status change or plan move (undo, use the setter) | `fail-gate` | `turn_failure_is_retryable` / finalize gate | Yes | Unsanctioned status mutation or plan file relocation. Fix-it turn instructs undo and setter invocation. Shipped (Order 07, `62sdwr`). |
    +| a hook-bypass commit (undo, recommit through the hooks) | `fail-gate` | `turn_failure_is_retryable` / commit gateway | Yes | Commit attempted with `--no-verify` or bypass. Fix-it turn instructs undo and recommit via hooks. Shipped (Order 07, `62sdwr`). |
    @@ -1457 +1457 @@ The normative mapping between the retry classes above and the runner's dispositi
    -| an agent proposal that a gate, tool or approach must change (Order 02) | `needs_input` / `needs_human_approval` | outcome evaluator / gate | No | Agent proposes modifying gate, tool, or approach. Persisted for human decision. Implementing: Order 02 (`5j73i6`). |
    +| an agent proposal that a gate, tool or approach must change (Order 02) | `needs_input` / `needs_human_approval` | outcome evaluator / gate | No | Agent proposes modifying gate, tool, or approach. Persisted for human decision. Shipped (Order 02, `tha7a6`). |
    @@ -1468 +1468 @@ The normative mapping between the retry classes above and the runner's dispositi
    -The runner still writes `failed-safely` for contained host/driver failures by design. Live producers writing this token are the `oc_runipd.run_queue` and `agy_runipd.run_queue` `except DriverError` arms, `runner_shared.refuse_undispatchable_typed_entry`, `runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS`, `runner_shared.TURN_RETRY_EXHAUSTED_STATUS`, and `lane_containment.BOUND_EXPIRY_DISPOSITION`, along with the agent outcome-schema literal in `runner_shared.build_prompt`. An agent-recorded `failed-safely` is an agent self-claim that `runner_shared.outcome_precedence_disposition` canonicalizes to `fail-gate` (non-retryable) by design, so the raw-token rule below governs runner-written tokens. The token is not migrated to `fail-gate` because `fail-gate` is the non-retryable gate-refusal class in this same table, so a migration would silently move host failures out of the retryable class. `TERMINAL_STATUS_ALIASES` maps it to `fail-gate` for display and cross-generation grouping only, and a reader that decides retryability or ownership must key on the raw token (or on the failure-kind marker approved plan `ytas91` introduces), never on `canonical_terminal_status`. The 2026-09-25 history note's "no longer written by the runner" does not apply to `failed-safely`. An item whose turn or finalize correction budget is exhausted is written `failed-safely` (`TURN_RETRY_EXHAUSTED_STATUS` / `FINALIZE_RETRY_EXHAUSTED_STATUS`, with a `turn-retry` or finalize refusal record), and is not re-classified as retryable because `turn_failure_is_retryable` runs only at the end of a dispatched turn, while `--retry-incomplete` remains the operator's manual route.
    +The runner still writes `failed-safely` for contained host/driver failures by design. Live producers writing this token are the `oc_runipd.run_queue` and `agy_runipd.run_queue` `except DriverError` arms, `runner_shared.refuse_undispatchable_typed_entry`, `runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS`, `runner_shared.TURN_RETRY_EXHAUSTED_STATUS`, and `lane_containment.BOUND_EXPIRY_DISPOSITION`, along with the agent outcome-schema literal in `runner_shared.build_prompt`. An agent-recorded `failed-safely` is an agent self-claim that `runner_shared.outcome_precedence_disposition` canonicalizes to `fail-gate` (non-retryable) by design, so the raw-token rule below governs runner-written tokens. The token is not migrated to `fail-gate` because `fail-gate` is the non-retryable gate-refusal class in this same table, so a migration would silently move host failures out of the retryable class. `TERMINAL_STATUS_ALIASES` maps it to `fail-gate` for display and cross-generation grouping only, and a reader that decides retryability or ownership must key on the raw token (or on the failure-kind marker executed plan `ytas91` introduces), never on `canonical_terminal_status`. The 2026-09-25 history note's "no longer written by the runner" does not apply to `failed-safely`. An item whose turn or finalize correction budget is exhausted is written `failed-safely` (`TURN_RETRY_EXHAUSTED_STATUS` / `FINALIZE_RETRY_EXHAUSTED_STATUS`, with a `turn-retry` or finalize refusal record), and is not re-classified as retryable because `turn_failure_is_retryable` runs only at the end of a dispatched turn, while `--retry-incomplete` remains the operator's manual route.
    ```
    Confirmation of zero occurrences of `k8n97m`, `120bhh`, `b8w5o6`, `5j73i6`:
    ```sh
    $ grep -n -E "k8n97m|120bhh|b8w5o6|5j73i6" .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    (exit code 1, zero occurrences)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Output of `git diff -- .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` showing the `verifier transport failure` row in `### 5.5 Retry policy` citing `yd4tqw` and `jodcz3` instead of `ytas91`, plus the appended `## Workflow history` entry recorded via `aw specs note`, the pasted `aw find plans yd4tqw` output that decided the `Implementing:`/`Shipped` prefix, and `git diff --stat` / `git diff -U0` output showing every hunk above `## Workflow history` is a same-line replacement (no added or removed lines above that heading).
  - Observed evidence:
    `aw find plans yd4tqw` output:
    ```
    ◕  pending       yd4tqw  jodcz3          .aw/records/plans/pending/20261014-jodcz3-01-yd4tqw-classify-and-remand-verifier-transport-failures-under-verifi.ipd.md
    ```
    `git diff --stat`:
    ```
     ...25kzda-aw-run-deterministic-run-and-verify.spec.md | 19 ++++++++++---------
     1 file changed, 10 insertions(+), 9 deletions(-)
    ```
    `git diff -U0` showing same-line replacements above `## Workflow history` and the single appended history record:
    ```diff
    diff --git a/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md b/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    index 9ec19d5d2..f67787b22 100644
    --- a/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    +++ b/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    @@ -1446 +1446 @@ The normative mapping between the retry classes above and the runner's dispositi
    -| stall or turn-limit expiry | `failed-safely`, `timeout` | `turn_failure_is_retryable` | Yes | Host stall or turn-limit expiry without response. Evidence: turn timer or runner watchdog. Implementing: Order 04 (`ytas91`). |
    +| stall or turn-limit expiry | `failed-safely`, `timeout` | `turn_failure_is_retryable` | Yes | Host stall or turn-limit expiry without response. Evidence: turn timer or runner watchdog. Shipped (Order 04, `ytas91`). |
    @@ -1449,6 +1449,6 @@ The normative mapping between the retry classes above and the runner's dispositi
    -| verifier transport failure | `verifier-transport-error` | `verification_retry_decision` | Yes | Skeptical verifier session crash or transport failure. Implementing: Order 04 (`ytas91`). |
    -| a hook refusal of any commit | `hook-refused` | `turn_failure_is_retryable` / commit gateway | Yes | Pre-commit hook rejected commit. Worktree preserved; fix-it turn given hook output. Implementing: Order 05 (`k8n97m`). |
    -| a red combined suite after merge | `integration-test-failed` | integration gate | Yes | Verification suite failed after merge in lane or integration worktree. Implementing: Order 06 (`120bhh`). |
    -| an out-of-scope change (revert or justify) | `fail-gate` | `turn_failure_is_retryable` / finalize gate | Yes | Delta outside frozen scope. Agent may revert edit or record justification widening scope. Implementing: Order 07 (`b8w5o6`). |
    -| an unauthorized status change or plan move (undo, use the setter) | `fail-gate` | `turn_failure_is_retryable` / finalize gate | Yes | Unsanctioned status mutation or plan file relocation. Fix-it turn instructs undo and setter invocation. Implementing: Order 05 (`k8n97m`). |
    -| a hook-bypass commit (undo, recommit through the hooks) | `fail-gate` | `turn_failure_is_retryable` / commit gateway | Yes | Commit attempted with `--no-verify` or bypass. Fix-it turn instructs undo and recommit via hooks. Implementing: Order 05 (`k8n97m`). |
    +| verifier transport failure | `verifier-transport-error` | `verification_retry_decision` | Yes | Skeptical verifier session crash or transport failure. Implementing: `yd4tqw` (from backlog `jodcz3`). |
    +| a hook refusal of any commit | `hook-refused` | `turn_failure_is_retryable` / commit gateway | Yes | Pre-commit hook rejected commit. Worktree preserved; fix-it turn given hook output. Shipped (Order 05, `w9nvq4`). |
    +| a red combined suite after merge | `integration-test-failed` | integration gate | Yes | Verification suite failed after merge in lane or integration worktree. Shipped (Order 05, `w9nvq4`). |
    +| an out-of-scope change (revert or justify) | `fail-gate` | `turn_failure_is_retryable` / finalize gate | Yes | Delta outside frozen scope. Agent may revert edit or record justification widening scope. Shipped (Order 06, `psgyzw`). |
    +| an unauthorized status change or plan move (undo, use the setter) | `fail-gate` | `turn_failure_is_retryable` / finalize gate | Yes | Unsanctioned status mutation or plan file relocation. Fix-it turn instructs undo and setter invocation. Shipped (Order 07, `62sdwr`). |
    +| a hook-bypass commit (undo, recommit through the hooks) | `fail-gate` | `turn_failure_is_retryable` / commit gateway | Yes | Commit attempted with `--no-verify` or bypass. Fix-it turn instructs undo and recommit via hooks. Shipped (Order 07, `62sdwr`). |
    @@ -1457 +1457 @@ The normative mapping between the retry classes above and the runner's dispositi
    -| an agent proposal that a gate, tool or approach must change (Order 02) | `needs_input` / `needs_human_approval` | outcome evaluator / gate | No | Agent proposes modifying gate, tool, or approach. Persisted for human decision. Implementing: Order 02 (`5j73i6`). |
    +| an agent proposal that a gate, tool or approach must change (Order 02) | `needs_input` / `needs_human_approval` | outcome evaluator / gate | No | Agent proposes modifying gate, tool, or approach. Persisted for human decision. Shipped (Order 02, `tha7a6`). |
    @@ -1468 +1468 @@ The normative mapping between the retry classes above and the runner's dispositi
    -The runner still writes `failed-safely` for contained host/driver failures by design. Live producers writing this token are the `oc_runipd.run_queue` and `agy_runipd.run_queue` `except DriverError` arms, `runner_shared.refuse_undispatchable_typed_entry`, `runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS`, `runner_shared.TURN_RETRY_EXHAUSTED_STATUS`, and `lane_containment.BOUND_EXPIRY_DISPOSITION`, along with the agent outcome-schema literal in `runner_shared.build_prompt`. An agent-recorded `failed-safely` is an agent self-claim that `runner_shared.outcome_precedence_disposition` canonicalizes to `fail-gate` (non-retryable) by design, so the raw-token rule below governs runner-written tokens. The token is not migrated to `fail-gate` because `fail-gate` is the non-retryable gate-refusal class in this same table, so a migration would silently move host failures out of the retryable class. `TERMINAL_STATUS_ALIASES` maps it to `fail-gate` for display and cross-generation grouping only, and a reader that decides retryability or ownership must key on the raw token (or on the failure-kind marker approved plan `ytas91` introduces), never on `canonical_terminal_status`. The 2026-09-25 history note's "no longer written by the runner" does not apply to `failed-safely`. An item whose turn or finalize correction budget is exhausted is written `failed-safely` (`TURN_RETRY_EXHAUSTED_STATUS` / `FINALIZE_RETRY_EXHAUSTED_STATUS`, with a `turn-retry` or finalize refusal record), and is not re-classified as retryable because `turn_failure_is_retryable` runs only at the end of a dispatched turn, while `--retry-incomplete` remains the operator's manual route.
    +The runner still writes `failed-safely` for contained host/driver failures by design. Live producers writing this token are the `oc_runipd.run_queue` and `agy_runipd.run_queue` `except DriverError` arms, `runner_shared.refuse_undispatchable_typed_entry`, `runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS`, `runner_shared.TURN_RETRY_EXHAUSTED_STATUS`, and `lane_containment.BOUND_EXPIRY_DISPOSITION`, along with the agent outcome-schema literal in `runner_shared.build_prompt`. An agent-recorded `failed-safely` is an agent self-claim that `runner_shared.outcome_precedence_disposition` canonicalizes to `fail-gate` (non-retryable) by design, so the raw-token rule below governs runner-written tokens. The token is not migrated to `fail-gate` because `fail-gate` is the non-retryable gate-refusal class in this same table, so a migration would silently move host failures out of the retryable class. `TERMINAL_STATUS_ALIASES` maps it to `fail-gate` for display and cross-generation grouping only, and a reader that decides retryability or ownership must key on the raw token (or on the failure-kind marker executed plan `ytas91` introduces), never on `canonical_terminal_status`. The 2026-09-25 history note's "no longer written by the runner" does not apply to `failed-safely`. An item whose turn or finalize correction budget is exhausted is written `failed-safely` (`TURN_RETRY_EXHAUSTED_STATUS` / `FINALIZE_RETRY_EXHAUSTED_STATUS`, with a `turn-retry` or finalize refusal record), and is not re-classified as retryable because `turn_failure_is_retryable` runs only at the end of a dispatched turn, while `--retry-incomplete` remains the operator's manual route.
    @@ -1743,6 +1743,7 @@ This example demonstrates the revised guarantees: `all` is safely bounded; depen

     ## Workflow history

    +- 2026-10-16 note (aw specs): Section 5.5 retry policy table owner citations, Order numbers, and status labels updated per plan 6g08rp (backlog w5opbr)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: The `git diff -- tests/test_fixfirst_end_to_end.py` hunk showing the checker deriving id6 tokens from the table (no hard-coded owner list) and both tests, plus pasted pytest output from `python3 -m pytest -o addopts="" tests/test_fixfirst_end_to_end.py -k "spec_5_5" -v` showing the live-spec test and the mutated-copy test both PASSED with zero failures (the names are pointers; re-derive them from the diff).
  - Observed evidence:
    `git diff -- tests/test_fixfirst_end_to_end.py` (hunks showing dynamic token derivation and tests):
    ```diff
    @@ -142,6 +145,131 @@

    +def _locate_spec_25kzda(repo_root: Path) -> Path:
    +    """Locate spec 25kzda recursively under .aw/records/specs/ across any status subdirectory."""
    +    specs_dir = repo_root / ".aw" / "records" / "specs"
    +    matches = sorted(specs_dir.rglob("*-25kzda-*.spec.md"))
    +    if len(matches) != 1:
    +        raise ValueError(
    +            f"Expected exactly 1 spec matching *-25kzda-*.spec.md under {specs_dir}, "
    +            f"found {len(matches)}: {matches}"
    +        )
    +    return matches[0]
    +
    +
    +def _spec_5_5_owner_problems(spec_text: str, repo_root: Path) -> list[str]:
    +    """Check spec 25kzda Section 5.5 retry policy table for owner citations and resolution."""
    +    problems: list[str] = []
    +    start_idx = spec_text.find("### 5.5 Retry policy")
    +    if start_idx == -1:
    +        return ["Section '### 5.5 Retry policy' not found in spec text"]
    +    end_idx = spec_text.find("### 5.6", start_idx)
    +    if end_idx == -1:
    +        return ["Section '### 5.6' not found in spec text after '### 5.5'"]
    +    slice_text = spec_text[start_idx:end_idx]
    +
    +    # (a) any of k8n97m, 120bhh, b8w5o6, 5j73i6 appears anywhere in the slice
    +    for stale_id in ("k8n97m", "120bhh", "b8w5o6", "5j73i6"):
    +        if stale_id in slice_text:
    +            problems.append(f"Stale owner ID `{stale_id}` found in §5.5 slice")
    +
    # Extract retry-policy table rows (lines starting '| ' after header, excluding separator)
    +    in_table = False
    +    table_rows: list[str] = []
    +    for line in slice_text.splitlines():
    +        stripped = line.strip()
    +        if stripped.startswith("| Spec Class | Disposition(s) |"):
    +            in_table = True
    +            continue
    +        if in_table:
    +            if not stripped.startswith("|"):
    +                break
    +            if re.match(r"^\|(\s*:?-+:?\s*\|)+$", stripped):
    +                continue
    +            table_rows.append(stripped)
    +
    +    # (b), (c), (d)
    +    for row_line in table_rows:
    +        cells = [c.strip() for c in row_line.split("|")[1:-1]]
    +        if len(cells) < 5:
    +            continue
    +        spec_class = cells[0]
    +        notes_cell = cells[-1]
    +
    +        # (b) backticked token matching artifact_core.ID6_RE in LAST cell
    +        # does not resolve via selectors.resolve to exactly one path for plans or backlog
    +        backticked_tokens = re.findall(r"`([^`]+)`", notes_cell)
    +        for token in backticked_tokens:
    +            if artifact_core.ID6_RE.match(token):
    +                p_res = selectors.resolve(
    +                    repo_root, "plans", token, allow=frozenset({selectors.MATCH_ID6})
    +                )
    +                b_res = selectors.resolve(
    +                    repo_root, "backlog", token, allow=frozenset({selectors.MATCH_ID6})
    +                )
    +                if len(p_res.paths) != 1 and len(b_res.paths) != 1:
    +                    problems.append(
    +                        f"Row '{spec_class}': token `{token}` does not resolve to exactly one path "
    +                        f"for plans or backlog (plans={len(p_res.paths)}, backlog={len(b_res.paths)})"
    +                    )
    ...
    ```
    Pytest output (`python3 -m pytest -o addopts="" tests/test_fixfirst_end_to_end.py -k "spec_5_5" -v`):
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=2935738348
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 29 items                                                            collected 29 items / 27 deselected / 2 selected

    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_e05_spec_5_5_checker_rejects_stale_owner PASSED [ 50%]
    tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_e05_spec_5_5_table_owner_ids_resolve PASSED [100%]

    NOTE: 27 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ====================== 2 passed, 27 deselected in 19.33s =======================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted command output from `AW_NO_REEXEC=1 python3 -m agent_workflows specs check .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, `python3 -m pytest tests/test_fixfirst_end_to_end.py`, `python3 -m pytest`, and `AW_NO_REEXEC=1 python3 -m agent_workflows sanitize --agent` showing all four commands exiting 0 with zero failures.
  - Observed evidence:
    `AW_NO_REEXEC=1 python3 -m agent_workflows specs check .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`:
    ```
    aw specs check: all specs conform. 1 specs checked.
    ```
    `python3 -m pytest tests/test_fixfirst_end_to_end.py`:
    ```
    bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...
    .............................                                            [100%]
    29 passed in 22.54s
    ```
    `python3 -m pytest`:
    ```
    bringing up nodes...
    created: 6/6 workers
    bringing up nodes...

    ........................................................................ [ 10%]
    ......................................................................... [ 20%]
    ........................................................................ [ 30%]
    ........................................................................ [ 41%]
    ........................................................................ [ 51%]
    ........................................................................ [ 61%]
    ........................................................................ [ 71%]
    ........................................................................ [ 82%]
    ........................................................................ [ 92%]
    .....................................................                    [100%]
    NOTE: 5 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    702 passed in 27.62s
    ```
    `AW_NO_REEXEC=1 python3 -m agent_workflows sanitize --agent`:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5218,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

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
