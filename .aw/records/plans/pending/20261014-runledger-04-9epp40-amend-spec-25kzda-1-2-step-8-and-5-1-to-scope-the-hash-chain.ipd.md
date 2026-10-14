# IPD: Amend spec 25kzda 1.2 step 8 and 5.1 to scope the hash-chained run ledger to aw run

- Date: 2026-10-14
- Kind: child
- Concern: Align spec `25kzda` Section 1.2 step 8 and Section 5.1 with the 2026-10-08 maintainer Option (b) decision (`rdjka2` OQ-01, decision record `utb2qr`) so the spec states that driver runs (`aw oc run` / `aw agy run`) record execution in `state.json` and `events.jsonl` while the append-only, hash-chained run ledger (`ledger.jsonl`) is scoped to the discrete `aw run` / `aw runs` workflow execution path.
- Scope: Amend `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 1.2 step 8 and Section 5.1's admissible completion inputs bullet in place with dated provenance citing `rdjka2` OQ-01 and `utb2qr`, record the amendment in `## Workflow history` via `aw specs note`, and verify that all spec-citation and ledger-vs-driver boundary tests pass.
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 66ls4r
- Set: runledger
- Order: 4
- Highest E allocated: 03
- Author: AI Agent
- Id: 9epp40

## Workflow history
- 2026-10-14 to-review (aw set): Ready for review; graduates backlog 66ls4r

- 2026-10-14 draft (AI Agent): created from backlog `66ls4r` (`aw ipd scaffold --from-backlog 66ls4r`).

## Goal

Close the spec-versus-code divergence identified in backlog `66ls4r` and promised in executed plan `rdjka2` (`## Spec / documentation sync`) and decision record `utb2qr` (Section 5.2 True Cost #1 and Section 6 item 4) by amending spec `25kzda` Section 1.2 step 8 and Section 5.1's admissible completion inputs bullet in place so they accurately state the two-substrate architecture: driver runs (`aw oc run` / `aw agy run`) record durable execution state and events in `state.json` and `events.jsonl` and do not write `ledger.jsonl`, while the append-only, hash-chained run ledger (`ledger.jsonl`) is scoped to the discrete `aw run` / `aw runs` workflow execution path per the 2026-10-08 maintainer Option (b) decision (`rdjka2` OQ-01, `utb2qr`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Pre-edit baseline and stop-condition verification

- [ ] E-01 Re-measure the executing HEAD against the plan's baseline assumptions: (a) inspect `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 1.2 step 8 (`"8. Capture tool calls, outputs, changed paths, commits, and artifacts in a tamper-evident run ledger."`) and Section 5.1 (`"- the append-only, hash-chained run ledger."` under `"The following are admissible completion inputs:"`), (b) confirm `.aw/records/plans/executed/20261002-runledger-01-rdjka2-decide-whether-a-driver-run-writes-a-hash-chained-ledger-and.ipd.md` OQ-01 records `MAINTAINER RESOLUTION (2026-10-08, ...): OPTION (b)` and `.aw/records/research/20261007-runledger-00-utb2qr-driver-run-ledger-decision.findings.md` exists on disk, (c) confirm `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` have zero references to `ledger_store`, `RunLedgerStore`, or `ledger.jsonl`, (d) run `spec_citations.stale_spec_anchors('.', spec_citations.default_scan_roots('.'))` to confirm zero stale anchors prior to editing, and (e) run `python3 -m pytest tests/test_run_recovery_cli.py tests/test_run_finding_abort_partition.py tests/test_run_finding_spec_transcription.py` to establish the pre-edit test baseline. Stop and report without editing if Section 1.2 step 8 or Section 5.1 has already been amended or if either host driver now writes `ledger.jsonl`.
  - Depends on: none
  - Expected outcome: The unamended wording in `25kzda` Section 1.2 step 8 and Section 5.1, the Option (b) resolution in `rdjka2` OQ-01 and `utb2qr`, the zero `ledger.jsonl` references in `oc_runipd.py` and `agy_runipd.py`, the empty `stale_spec_anchors` list, and the green targeted pytest run are all observed and recorded.
  - Execution state: pending

### Task group 2: Spec `25kzda` Section 1.2 step 8 and Section 5.1 amendment and provenance

- [ ] E-02 Amend `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 1.2 step 8 and Section 5.1's ledger bullet in place (replacing each single line with a single line so line numbers below each edit do not shift):
  1. In Section 1.2 step 8, replace `"8. Capture tool calls, outputs, changed paths, commits, and artifacts in a tamper-evident run ledger."` with:
     `8. Capture tool calls, outputs, changed paths, commits, and artifacts in the run's durable execution record: driver runs (\`aw oc run\` / \`aw agy run\`) record run state and events in \`state.json\` and \`events.jsonl\` in the run directory and do not write \`ledger.jsonl\`, while the append-only, hash-chained run ledger (\`ledger.jsonl\`) is scoped to the discrete \`aw run\` / \`aw runs\` workflow execution path (amended 2026-10-14 per the 2026-10-08 maintainer Option (b) decision in plan \`rdjka2\` OQ-01 and decision record \`utb2qr\`).`
  2. In Section 5.1 under `"The following are admissible completion inputs:"`, replace `"- the append-only, hash-chained run ledger."` with:
     `- the append-only, hash-chained run ledger (\`ledger.jsonl\`, scoped to the discrete \`aw run\` / \`aw runs\` workflow execution path; driver runs \`aw oc run\` / \`aw agy run\` record execution in \`state.json\` and \`events.jsonl\` and do not write \`ledger.jsonl\`, per the 2026-10-08 maintainer Option (b) decision in plan \`rdjka2\` OQ-01 and decision record \`utb2qr\`).`
  Leave Section 6.2 (owned by sibling plan `v47z9u`), Section 4.2, Section 4.6, and all other sections of `25kzda` untouched.
  - Depends on: E-01
  - Expected outcome: `25kzda` Section 1.2 step 8 and Section 5.1 state both the driver substrate (`state.json` and `events.jsonl`) and the scoping of the hash-chained `ledger.jsonl` to the discrete `aw run` / `aw runs` workflow execution path, citing the 2026-10-08 maintainer Option (b) decision in `rdjka2` OQ-01 and decision record `utb2qr`, with zero line-offset shift in the remainder of `25kzda`.
  - Execution state: pending

- [ ] E-03 Record the amendment in `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` `## Workflow history` via `python3 -m agent_workflows specs note .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md --message "9epp40 (66ls4r): amend 1.2 step 8 and 5.1 in place to scope the hash-chained ledger.jsonl to the discrete aw run / aw runs workflow path and state that driver runs (aw oc run / aw agy run) record execution in state.json and events.jsonl per the 2026-10-08 maintainer Option (b) decision (rdjka2 OQ-01, utb2qr)."`, then run `aw specs check`, `spec_citations.stale_spec_anchors('.', spec_citations.default_scan_roots('.'))`, `aw check`, `aw sanitize --agent`, and the full test suite (`python3 -m pytest`).
  - Depends on: E-02
  - Expected outcome: `aw specs note` appends the dated entry to `## Workflow history` in `25kzda`; `aw specs check`, `stale_spec_anchors`, `aw check`, `aw sanitize --agent`, and `python3 -m pytest` all pass with zero errors.
  - Execution state: pending

## Project conventions discovered (Step 0)

- **Spec `25kzda` in-place dated amendment and provenance convention**: Prior spec-alignment plans (`00pirb`, `e6w056`, `sa13no`, `u28vqb`) amend individual clauses of `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` in place with explicit dated provenance and record the amendment in `## Workflow history` using `aw specs note <spec-path> --message "..."` (`agent_workflows/specs_cli.py`, `_cmd_specs_note`). Amending a clause on a single line preserves line offsets for downstream citations and keeps `spec_citations.stale_spec_anchors` clean.
- **Orthogonality within Set `runledger`**:
  - Order 00 research findings `utb2qr` (`.aw/records/research/20261007-runledger-00-utb2qr-driver-run-ledger-decision.findings.md`) analyzed Option (a) vs Option (b) and recommended Option (b) with a follow-on spec amendment to `25kzda` Section 1.2 step 8 and Section 5.1 (Section 5.2 True Cost #1 and Section 6 item 4).
  - Order 01 plan `rdjka2` (`.aw/records/plans/executed/20261002-runledger-01-rdjka2-decide-whether-a-driver-run-writes-a-hash-chained-ledger-and.ipd.md`, executed `2026-10-08`) recorded the maintainer's interactive resolution of OQ-01: `OPTION (b). Runner (driver) runs keep state.json/events.jsonl as their record; amend spec 25kzda to say so, correct the misleading comments, and leave the ledger code for the separate aw run path`. `rdjka2` corrected the misleading comments in `agent_workflows/run_cli.py`, `agent_workflows/run_LEDGER_store.py`, and `tests/test_run_recovery_cli.py` and added `TestLedgerResolutionAndWrongFormatVerdict.test_run_engine_step_sequence_without_run_header_refuses_ledger_creation`, while deferring the `25kzda` text edit to a follow-on plan.
  - Order 02 plan `1rozt5` (`.aw/records/plans/executed/20261011-runledger-02-1rozt5-make-run-suite-check-s-captured-ledger-records-schema-valid.ipd.md`, executed `2026-10-11`) made `run_suite_check`'s captured ledger records schema-valid.
  - Order 03 plan `v47z9u` (`.aw/records/plans/pending/20261012-runledger-03-v47z9u-add-aw-run-init-the-one-writer-of-a-conformant-ledger-header.ipd.md`, `to-review`, from backlog `hegwri`) adds `aw run init` and amends only Section 6.2 of `25kzda` (`"Leave Sections 1.2 step 8 and 5.1 unchanged (backlog 66ls4r)"`).
  - This plan (Order 04, `9epp40`, from backlog `66ls4r`) amends only Section 1.2 step 8 and Section 5.1 (plus `## Workflow history`), leaving Section 6.2 untouched so `v47z9u` and `9epp40` commute cleanly in any execution order.
- **No `- From-Spec:` header on un-gated chore plans that edit a release-gated spec**: Backlog `66ls4r` is an un-gated `chore` item (no `- Blocks-Release:` field), whereas `25kzda` carries `- Blocks-Release: next`. Listing `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` in `- Scope-Paths:` satisfies `check.plan-spec-link-missing` (`agent_workflows/check_engine.py` drops any cited spec whose path is in `Scope-Paths`), matching sibling plan `v47z9u`.
- **Behavioral test coverage already in tree (P16)**: `tests/test_run_recovery_cli.py` (`TestLedgerResolutionAndWrongFormatVerdict`) already tests the runtime boundary between driver runs (`state.json` + `events.jsonl`) and ledger runs (`ledger.jsonl`), including:
  - `test_every_verb_reaches_the_same_verdict_for_each_file_shape` (driver `events.jsonl` rejected with `EXIT_NOT_A_LEDGER = 7` and `"not a run ledger"` across `show`, `verify-ledger`, `evidence`, and `status`),
  - `test_the_signpost_appears_exactly_when_repair_would_work` (absent `ledger.jsonl` on a driver run directory emits `"no driver run writes one"` and `"events.jsonl"`),
  - `test_classifying_a_target_never_hands_the_event_log_to_a_ledger_parser` (`run_cli.resolve_ledger_path` returns `None` for a bare driver run id), and
  - `test_run_engine_step_sequence_without_run_header_refuses_ledger_creation` (`RunEngine` step sequence without a root `'kind': 'run'` record raises `SchemaInvalidRecordError` with `RL-E041`).

## Findings

| # | Severity | Location | Finding |
|---|---|---|---|
| F-1 | Drift (spec vs. decided runtime architecture) | `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 1.2 step 8 (`"8. Capture tool calls, outputs, changed paths, commits, and artifacts in a tamper-evident run ledger."`, line 148) | Section 1.2 lists the normative steps of a driver run (`aw oc run` / `aw agy run`). Step 8 still unconditionally requires a "tamper-evident run ledger" for driver runs, contradicting the 2026-10-08 maintainer Option (b) decision (`rdjka2` OQ-01, `utb2qr`) under which driver runs write `state.json` and `events.jsonl` in the run directory (`runner_shared.initialize_run_core`) and never write `ledger.jsonl`. |
| F-2 | Drift (spec vs. decided runtime architecture) | `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 5.1 (`"- the append-only, hash-chained run ledger."` under `"The following are admissible completion inputs:"`, line 1085) | Section 5.1 lists `"the append-only, hash-chained run ledger"` as an unqualified completion input alongside IPD file contents, git working tree / index / commit state, and verifier executions, without stating that `ledger.jsonl` is scoped to the discrete `aw run` / `aw runs` workflow execution path while driver runs (`aw oc run` / `aw agy run`) record execution in `state.json` and `events.jsonl`. |
| F-3 | Verified clean | `agent_workflows/spec_citations.py` (`stale_spec_anchors`) and `tests/` | `spec_citations.stale_spec_anchors('.', spec_citations.default_scan_roots('.'))` returns `[]`, and no test in `tests/` or module in `agent_workflows/` greps for the unamended string `"tamper-evident run ledger"` or `"append-only, hash-chained run ledger"`. Replacing each of the two bullets in place on a single line preserves all section headings and line offsets in `25kzda`. |

## Proposed changes (ordered, validatable)

1. **Pre-edit verification (`E-01`)**:
   - Inspect `25kzda` Section 1.2 step 8 and Section 5.1 to verify the exact unamended lines.
   - Confirm `rdjka2` OQ-01's 2026-10-08 Option (b) maintainer resolution and `utb2qr` on disk.
   - Confirm zero references to `ledger_store`, `RunLedgerStore`, or `ledger.jsonl` in `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`.
   - Confirm `spec_citations.stale_spec_anchors('.', spec_citations.default_scan_roots('.'))` returns `[]` and run the targeted pytest suite (`tests/test_run_recovery_cli.py`, `tests/test_run_finding_abort_partition.py`, `tests/test_run_finding_spec_transcription.py`).

2. **In-place amendment of spec `25kzda` Section 1.2 step 8 and Section 5.1 (`E-02`)**:
   - In `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 1.2 step 8 (line 148), replace the single line:
     ```markdown
     8. Capture tool calls, outputs, changed paths, commits, and artifacts in a tamper-evident run ledger.
     ```
     with:
     ```markdown
     8. Capture tool calls, outputs, changed paths, commits, and artifacts in the run's durable execution record: driver runs (`aw oc run` / `aw agy run`) record run state and events in `state.json` and `events.jsonl` in the run directory and do not write `ledger.jsonl`, while the append-only, hash-chained run ledger (`ledger.jsonl`) is scoped to the discrete `aw run` / `aw runs` workflow execution path (amended 2026-10-14 per the 2026-10-08 maintainer Option (b) decision in plan `rdjka2` OQ-01 and decision record `utb2qr`).
     ```
   - In `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 5.1 (line 1085), replace the single line:
     ```markdown
     - the append-only, hash-chained run ledger.
     ```
     with:
     ```markdown
     - the append-only, hash-chained run ledger (`ledger.jsonl`, scoped to the discrete `aw run` / `aw runs` workflow execution path; driver runs `aw oc run` / `aw agy run` record execution in `state.json` and `events.jsonl` and do not write `ledger.jsonl`, per the 2026-10-08 maintainer Option (b) decision in plan `rdjka2` OQ-01 and decision record `utb2qr`).
     ```

3. **Provenance note and validation (`E-03`)**:
   - Run `python3 -m agent_workflows specs note .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md --message "9epp40 (66ls4r): amend 1.2 step 8 and 5.1 in place to scope the hash-chained ledger.jsonl to the discrete aw run / aw runs workflow path and state that driver runs (aw oc run / aw agy run) record execution in state.json and events.jsonl per the 2026-10-08 maintainer Option (b) decision (rdjka2 OQ-01, utb2qr)."`
   - Run `aw specs check`, `spec_citations.stale_spec_anchors`, `aw check`, `aw sanitize --agent`, and the full pytest suite (`python3 -m pytest`).

## Deferred / out of scope (with reason)

- Adding `aw run init` and amending `25kzda` Section 6.2 (owned by sibling pending plan `v47z9u`, from backlog `hegwri`).
  - Carrier: v47z9u

## Scope check

- Over-scope: none.
- Under-scope: none. Both spec locations named in backlog `66ls4r` (`25kzda` Section 1.2 step 8 and Section 5.1) and the `## Workflow history` provenance note are covered.

## Required tests / validation

- Targeted behavioral and spec-transcription tests:
  - `python3 -m pytest tests/test_run_recovery_cli.py tests/test_run_finding_abort_partition.py tests/test_run_finding_spec_transcription.py`
- Spec and repository checks:
  - `AW_NO_REEXEC=1 python3 -m agent_workflows specs check`
  - `python3 -c "from agent_workflows import spec_citations; a = spec_citations.stale_spec_anchors('.', spec_citations.default_scan_roots('.')); assert not a, a; print('stale_spec_anchors:', len(a))"`
  - `AW_NO_REEXEC=1 python3 -m agent_workflows check`
  - `AW_NO_REEXEC=1 python3 -m agent_workflows sanitize --agent`
- Full test suite:
  - `python3 -m pytest`

## Spec / documentation sync

- `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` is the direct target of this plan (Section 1.2 step 8, Section 5.1, and `## Workflow history` via `aw specs note`). No other spec or user-facing documentation requires updating.

## Open questions

### OQ-01: Should `25kzda` Section 1.2 step 8 and Section 5.1 be amended to scope the hash-chained ledger to `aw run` / `aw runs`, or should they record an un-scoped divergence note?

- Blocking: no
- Status: resolved
- Owner: maintainer (resolved 2026-10-08 in `rdjka2` OQ-01; confirmed by `utb2qr` and `25kzda` amendment convention)
- Resolution or deferral rationale: Resolved from repository evidence. Backlog `66ls4r` noted that `rdjka2`'s `## Spec / documentation sync` section (authored on `2026-10-02` before `rdjka2` OQ-01 was answered) phrased the follow-on obligation as "either amend `25kzda` to scope the ledger requirement to the path that implements it, or record an accepted, dated divergence in the spec's own terms." Decision record `utb2qr` (`2026-10-07`) subsequently specified under Section 5.2 (Option (b) True Cost #1) `"Formalizing the divergence from spec 25kzda Section 1.2 Step 8 and Section 5.1 via a declared follow-on spec amendment"` and under Section 6 (Recommendation #4) `"schedules a tidy spec amendment for 25kzda"`. On `2026-10-08`, the maintainer interactively resolved `rdjka2` OQ-01 to Option (b) with the explicit instruction: `"OPTION (b). Runner (driver) runs keep state.json/events.jsonl as their record; amend spec 25kzda to say so, correct the misleading comments, and leave the ledger code for the separate aw run path"`. Moreover, under `25kzda`'s established in-place amendment convention (`00pirb`, `e6w056`, `sa13no`, `u28vqb`), an in-place dated amendment in Section 1.2 step 8 and Section 5.1 preserves the requirement text while stating both the driver substrate (`state.json` and `events.jsonl`) and the dated scoping of `ledger.jsonl` to `aw run` / `aw runs` (citing `rdjka2` OQ-01 and `utb2qr`), satisfying both formulations simultaneously.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output from (1) inspecting `25kzda` Section 1.2 step 8 and Section 5.1 showing the unamended lines, (2) confirming `rdjka2` OQ-01's `OPTION (b)` maintainer resolution and `utb2qr` on disk, (3) grepping `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` for `ledger_store|RunLedgerStore|ledger\.jsonl` showing 0 matches, (4) running `spec_citations.stale_spec_anchors('.', spec_citations.default_scan_roots('.'))` showing `0` stale anchors, and (5) running `python3 -m pytest tests/test_run_recovery_cli.py tests/test_run_finding_abort_partition.py tests/test_run_finding_spec_transcription.py` exiting `0` with pass count.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff` of `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` showing the single-line in-place amendments to Section 1.2 step 8 and Section 5.1 naming `state.json` and `events.jsonl` for driver runs (`aw oc run` / `aw agy run`), scoping `ledger.jsonl` to the discrete `aw run` / `aw runs` workflow execution path, and citing the 2026-10-08 maintainer Option (b) decision in `rdjka2` OQ-01 and decision record `utb2qr`, with Section 6.2, Section 4.2, and Section 4.6 untouched.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted output of (1) `aw specs note` entry in `25kzda` `## Workflow history`, (2) `AW_NO_REEXEC=1 python3 -m agent_workflows specs check` exiting `0`, (3) `spec_citations.stale_spec_anchors('.', spec_citations.default_scan_roots('.'))` returning `[]`, (4) `AW_NO_REEXEC=1 python3 -m agent_workflows check` and `AW_NO_REEXEC=1 python3 -m agent_workflows sanitize --agent` exiting `0`, and (5) `python3 -m pytest` exiting `0` with the full pass summary.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Do not execute this plan until it has been reviewed and approved (`- Status: approved`). When executing, commit only the modified spec and plan paths via `aw commit 9epp40 -- <paths>`.
