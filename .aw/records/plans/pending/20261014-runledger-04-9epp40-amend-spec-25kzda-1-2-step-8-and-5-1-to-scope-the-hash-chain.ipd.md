# IPD: Amend spec 25kzda 1.2 step 8 and 5.1 to scope the hash-chained run ledger to aw run

- Date: 2026-10-14
- Kind: child
- Concern: Align spec `25kzda` Section 1.2 step 8 and Section 5.1 with the 2026-10-08 maintainer Option (b) decision (`rdjka2` OQ-01, decision record `utb2qr`) so the spec states that driver runs (`aw oc run` / `aw agy run`) record execution in `state.json` and `events.jsonl` while the append-only, hash-chained run ledger (`ledger.jsonl`) is scoped to the discrete `aw run` / `aw runs` workflow execution path.
- Scope: Amend `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 1.2 step 8, Section 5.1's admissible completion inputs bullet, and the four Section 5.3 sentences that make the same driver-run ledger claim (the durable-state intro, the snapshot/replay sentence, the 5.3a telemetry "hash-chained ledger is the run's record" clause, and resume algorithm step 1) in place with dated provenance citing `rdjka2` OQ-01 and `utb2qr`; correct the matching user-facing claim in `docs/evidence.md`; record the amendment in `## Workflow history` via `aw specs note`; and verify that all spec-citation and ledger-vs-driver boundary tests pass.
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, docs/evidence.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 66ls4r
- Set: runledger
- Order: 4
- Highest E allocated: 05
- Author: AI Agent
- Id: 9epp40
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
- 2026-10-14 to-review (aw set): Ready for review; graduates backlog 66ls4r

- 2026-10-14 draft (AI Agent): created from backlog `66ls4r` (`aw ipd scaffold --from-backlog 66ls4r`).

## Goal

Close the spec-versus-code divergence identified in backlog `66ls4r` and promised in executed plan `rdjka2` (`## Spec / documentation sync`) and decision record `utb2qr` (Section 5.2 True Cost #1 and Section 6 item 4) by amending spec `25kzda` Section 1.2 step 8 and Section 5.1's admissible completion inputs bullet in place so they accurately state the two-substrate architecture: driver runs (`aw oc run` / `aw agy run`) record durable execution state and events in `state.json` and `events.jsonl` and do not write `ledger.jsonl`, while the append-only, hash-chained run ledger (`ledger.jsonl`) is scoped to the discrete `aw run` / `aw runs` workflow execution path per the 2026-10-08 maintainer Option (b) decision (`rdjka2` OQ-01, `utb2qr`). The same claim also appears in four Section 5.3 / 5.3a sentences and in `docs/evidence.md`, so those are corrected in the same change (F-4, F-5) to keep the spec internally consistent.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Pre-edit baseline and stop-condition verification

- [ ] E-01 Re-measure the executing HEAD against the plan's baseline assumptions: (a) inspect `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 1.2 step 8 (`"8. Capture tool calls, outputs, changed paths, commits, and artifacts in a tamper-evident run ledger."`) and Section 5.1 (`"- the append-only, hash-chained run ledger."` under `"The following are admissible completion inputs:"`), (b) confirm `.aw/records/plans/executed/20261002-runledger-01-rdjka2-decide-whether-a-driver-run-writes-a-hash-chained-ledger-and.ipd.md` OQ-01 records `MAINTAINER RESOLUTION (2026-10-08, ...): OPTION (b)` and `.aw/records/research/20261007-runledger-00-utb2qr-driver-run-ledger-decision.findings.md` exists on disk, (c) confirm `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` have zero references to `ledger_store`, `RunLedgerStore`, or `ledger.jsonl` (the only hits in `agent_workflows/runner_shared.py` are explanatory comments, and its sole `run_recovery` import is the retry-budget validator), (d) locate the four Section 5.3 / 5.3a anchors E-03 names by quoted string and the `docs/evidence.md` line-3 anchor E-04 names, (e) run `spec_citations.stale_spec_anchors('.', spec_citations.default_scan_roots('.'))` to confirm zero stale anchors prior to editing, (f) run `python3 -m pytest tests/test_run_recovery_cli.py tests/test_run_finding_abort_partition.py tests/test_run_finding_spec_transcription.py` to establish the pre-edit test baseline, (g) record `wc -l` of the spec, and (h) capture the pre-edit `AW_NO_REEXEC=1 python3 -m agent_workflows check --agent` result record (its `findings_by_severity` and the set of `error` rule ids) as the baseline E-05 compares against, because the corpus carries pre-existing `error` findings unrelated to this plan (19 at review HEAD `23863c32a`; re-derive, do not reuse that number). Stop and report without editing if any targeted anchor has already been amended or if either host driver now writes `ledger.jsonl`.
  - Depends on: none
  - Expected outcome: The unamended wording at every E-02, E-03, and E-04 anchor, the Option (b) resolution in `rdjka2` OQ-01 and `utb2qr`, the zero `ledger.jsonl` references in `oc_runipd.py` and `agy_runipd.py`, the empty `stale_spec_anchors` list, the green targeted pytest run, the spec line count, and the `aw check` baseline are all observed and recorded.
  - Execution state: pending

### Task group 2: Spec `25kzda` amendments and user-facing doc correction

- [ ] E-02 Amend `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 1.2 step 8 and Section 5.1's ledger bullet in place (replacing each single line with a single line so line numbers below each edit do not shift):
  1. In Section 1.2 step 8, replace `"8. Capture tool calls, outputs, changed paths, commits, and artifacts in a tamper-evident run ledger."` with:
     `8. Capture tool calls, outputs, changed paths, commits, and artifacts in the run's durable execution record: driver runs (\`aw oc run\` / \`aw agy run\`) record run state and events in \`state.json\` and \`events.jsonl\` in the run directory (append-plus-fsync, not hash-chained, so not tamper-evident) and do not write \`ledger.jsonl\`, while the append-only, hash-chained run ledger (\`ledger.jsonl\`) is scoped to the discrete \`aw run\` / \`aw runs\` workflow execution path. Wherever this spec otherwise says "run ledger" or "ledger" of a driver run, it means that driver's durable run record; the hash-chain properties (sequence, parent link, record hash, chain verification) hold only for \`ledger.jsonl\` (amended 2026-10-14 per the 2026-10-08 maintainer Option (b) decision in plan \`rdjka2\` OQ-01 and decision record \`utb2qr\`).`
  2. In Section 5.1 under `"The following are admissible completion inputs:"`, replace `"- the append-only, hash-chained run ledger."` with:
     `- the append-only, hash-chained run ledger (\`ledger.jsonl\`, scoped to the discrete \`aw run\` / \`aw runs\` workflow execution path; driver runs \`aw oc run\` / \`aw agy run\` record execution in \`state.json\` and \`events.jsonl\` and do not write \`ledger.jsonl\`, per the 2026-10-08 maintainer Option (b) decision in plan \`rdjka2\` OQ-01 and decision record \`utb2qr\`).`
  Leave Section 4.2 (byte-for-byte transcription-locked by `tests/test_run_finding_spec_transcription.py`), Section 4.6, Sections 5.5 and 5.6 (owned by sibling plan `jmogmv`), Section 6.2 (owned by sibling plan `v47z9u`), and every section E-03 does not name untouched.
  - Depends on: E-01
  - Expected outcome: `25kzda` Section 1.2 step 8 and Section 5.1 state both the driver substrate (`state.json` and `events.jsonl`, not hash-chained) and the scoping of the hash-chained `ledger.jsonl` to the discrete `aw run` / `aw runs` workflow execution path, step 8 carries the terminology clause, both cite `rdjka2` OQ-01 and `utb2qr`, and the spec's line count is unchanged.
  - Execution state: pending

- [ ] E-03 Amend the four Section 5.3 / 5.3a sentences of the same spec that assert a hash-chained record for every run, each by an in-place substitution inside its existing line (no line added or removed). Re-measure each anchor by its quoted string first; the line numbers are hints from HEAD `23863c32a`:
  1. Section 5.3 intro (anchor `"The engine stores repository-local, crash-safe run state."`, line 1290): append to the end of that same line: ` For a driver run (\`aw oc run\` / \`aw agy run\`) the event log is \`events.jsonl\` beside the \`state.json\` snapshot, written append-plus-fsync but not hash-chained: the monotonic sequence, parent event, and previous-event hash fields below are carried only by the \`aw run\` path's \`ledger.jsonl\` (amended 2026-10-14, \`rdjka2\` OQ-01 Option (b), \`utb2qr\`).`
  2. Section 5.3 (anchor `"A snapshot is a cache; replaying the ledger is authoritative."`, line 1302): replace that sentence with `On the \`aw run\` path a snapshot is a cache and replaying \`ledger.jsonl\` is authoritative; a driver run's authoritative record is its \`state.json\` (atomic replacement) together with its \`events.jsonl\` (amended 2026-10-14, \`rdjka2\` OQ-01 Option (b)).`
  3. Section 5.3a (anchor `"The hash-chained ledger is the run's record and replaying it is authoritative;"`, line 1312): replace that clause with `The run's durable record (Section 5.3: \`ledger.jsonl\` on the \`aw run\` path, \`state.json\` plus \`events.jsonl\` for a driver run) is authoritative;`, leaving the rest of the bullet byte-identical.
  4. Section 5.3 resume algorithm step 1 (anchor `"1. \`aw <host> run resume <run-id>\` verifies the ledger chain before doing anything."`, line 1337): replace the line with `1. \`aw <host> run resume <run-id>\` loads the run's durable record before doing anything: a driver run reads its \`state.json\` and refuses the resume when that file is missing or unparseable, while the \`aw run\` path (\`aw runs resume\`) reads \`ledger.jsonl\` and refuses on ledger corruption (amended 2026-10-14, \`rdjka2\` OQ-01 Option (b)).` Before writing, confirm the driver half by reading `runner_shared.load_state` / `runner_shared.load_json` (raises `DriverError` on `FileNotFoundError` and `json.JSONDecodeError`) and the `aw runs` half by reading `run_cli._run_resume` (returns `EXIT_CORRUPTED_LEDGER` on `store.LedgerCorruption`); if sibling `jmogmv` has landed `CorruptRunStateError` first, the wording "refuses the resume" still holds and must not name an exit code.
  - Depends on: E-02
  - Expected outcome: none of the four anchors still asserts a hash chain or chain verification for a driver run, each carries the dated `rdjka2` provenance, Steps 2 through 9 of the resume algorithm and the 5.3 event field bullets are byte-identical, and the spec's line count is unchanged.
  - Execution state: pending

- [ ] E-04 Correct the user-facing claim in `docs/evidence.md` line 3 (anchor `"Every run records tamper-evident evidence in an append-only ledger."`): replace that one sentence with `A workflow run driven through \`aw run\` records tamper-evident evidence in an append-only ledger. Runner runs (\`aw oc run\` / \`aw agy run\`) keep their record in \`state.json\` and \`events.jsonl\` instead and do not write a ledger.` Reflow the paragraph to the file's existing wrap width if needed; the following sentence (`The modules are ...`) and the rest of the file stay unchanged. This is user-facing prose: write no em or en dashes.
  - Depends on: E-01
  - Expected outcome: `docs/evidence.md` no longer claims every run writes a ledger, names both substrates, and contains no em or en dash.
  - Execution state: pending

### Task group 3: Provenance and validation

- [ ] E-05 Record the amendment in the spec's `## Workflow history` via `AW_NO_REEXEC=1 python3 -m agent_workflows specs note .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md --message "9epp40 (66ls4r): amend 1.2 step 8, 5.1, 5.3 (intro, snapshot sentence, resume step 1) and 5.3a in place to scope the hash-chained ledger.jsonl to the discrete aw run / aw runs workflow path and state that driver runs (aw oc run / aw agy run) record execution in un-chained state.json and events.jsonl, per the 2026-10-08 maintainer Option (b) decision (rdjka2 OQ-01, utb2qr)."`, then run every command in `## Required tests / validation`.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the dated entry is the newest line under the spec's `## Workflow history`; `aw specs check` exits 0; `stale_spec_anchors` returns `[]`; `aw check --agent` reports no diagnostic located at this plan's file, the spec, or `docs/evidence.md` with severity `warning` or `error`, and no error rule absent from the E-01 baseline; `aw sanitize --agent` exits 0 with outcome `clean`; bare `python3 -m pytest` exits 0.
  - Execution state: pending

## Project conventions discovered (Step 0)

- **Spec `25kzda` in-place dated amendment and provenance convention**: Prior spec-alignment plans (`00pirb`, `e6w056`, `sa13no`, `u28vqb`) amend individual clauses of `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` in place with explicit dated provenance and record the amendment in `## Workflow history` using `aw specs note <spec-path> --message "..."` (`agent_workflows/specs_cli.py`, `_cmd_specs_note`). Amending a clause on a single line preserves line offsets for downstream citations and keeps `spec_citations.stale_spec_anchors` clean.
- **Orthogonality within Set `runledger`**:
  - Order 00 research findings `utb2qr` (`.aw/records/research/20261007-runledger-00-utb2qr-driver-run-ledger-decision.findings.md`) analyzed Option (a) vs Option (b) and recommended Option (b) with a follow-on spec amendment to `25kzda` Section 1.2 step 8 and Section 5.1 (Section 5.2 True Cost #1 and Section 6 item 4).
  - Order 01 plan `rdjka2` (`.aw/records/plans/executed/20261002-runledger-01-rdjka2-decide-whether-a-driver-run-writes-a-hash-chained-ledger-and.ipd.md`, executed `2026-10-08`) recorded the maintainer's interactive resolution of OQ-01: `OPTION (b). Runner (driver) runs keep state.json/events.jsonl as their record; amend spec 25kzda to say so, correct the misleading comments, and leave the ledger code for the separate aw run path`. `rdjka2` (commit `3b84f5c8b`) corrected the misleading comments in `agent_workflows/runner_shared.py`, `agent_workflows/run_recovery.py`, and `docs/recovery.md` and added `TestLedgerResolutionAndWrongFormatVerdict.test_run_engine_step_sequence_without_run_header_refuses_ledger_creation`, while deferring the `25kzda` text edit to a follow-on plan.
  - Order 02 plan `1rozt5` (`.aw/records/plans/executed/20261011-runledger-02-1rozt5-make-run-suite-check-s-captured-ledger-records-schema-valid.ipd.md`, executed `2026-10-11`) made `run_suite_check`'s captured ledger records schema-valid.
  - Order 03 plan `v47z9u` (`.aw/records/plans/pending/20261012-runledger-03-v47z9u-add-aw-run-init-the-one-writer-of-a-conformant-ledger-header.ipd.md`, `to-review`, from backlog `hegwri`) adds `aw run init` and amends only Section 6.2 of `25kzda` (`"Leave Sections 1.2 step 8 and 5.1 unchanged (backlog 66ls4r)"`).
  - This plan (Order 04, `9epp40`, from backlog `66ls4r`) amends Section 1.2 step 8, Section 5.1, and four sentences of Sections 5.3 / 5.3a (plus `## Workflow history`), leaving Section 6.2 untouched so `v47z9u` and `9epp40` commute cleanly in any execution order.
  - Out-of-Set sibling `jmogmv` (`.aw/records/plans/pending/20261014-jt7ns3-01-jmogmv-wire-corrupt-run-state-exit-4-in-driver-runs-and-align-spec.ipd.md`, `to-review`) amends Sections 5.5 and 5.6 of the same spec and names this plan as the carrier for 1.2 step 8 and 5.1 (its `## Deferred / out of scope`). Neither plan touches the other's sections, and every edit here is a same-line substitution, so the two commute; both append to `## Workflow history` through `aw specs note`, which inserts a line and is merge-safe.
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
| F-4 | Drift (same claim, unlisted locations) | spec `25kzda` Section 5.3 intro (`"The engine stores repository-local, crash-safe run state."`, line 1290), Section 5.3 (`"A snapshot is a cache; replaying the ledger is authoritative."`, line 1302), Section 5.3a (`"The hash-chained ledger is the run's record and replaying it is authoritative;"`, line 1312), Section 5.3 resume step 1 (`"verifies the ledger chain before doing anything."`, line 1337) | Each asserts a monotonic-sequence / previous-event-hash event log or a chain verification for every run, including driver runs. `runner_shared.append_jsonl` writes un-chained JSON lines with `fsync` only (`utb2qr` F-10), `runner_shared.load_state` reads `state.json` through `load_json` with no chain, and `aw oc run resume` (`oc_runipd.main`, `args.command == "resume"`) loads `state.json`. Amending only 1.2 and 5.1 would leave the spec self-contradictory on the same question. Added at review (PR-001). |
| F-5 | Drift (user-facing doc) | `docs/evidence.md:3` (`"Every run records tamper-evident evidence in an append-only ledger."`) | The user-facing statement of the same claim, false for every `aw oc run` / `aw agy run` run under Option (b). Added at review (PR-002). |
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
     8. Capture tool calls, outputs, changed paths, commits, and artifacts in the run's durable execution record: driver runs (`aw oc run` / `aw agy run`) record run state and events in `state.json` and `events.jsonl` in the run directory (append-plus-fsync, not hash-chained, so not tamper-evident) and do not write `ledger.jsonl`, while the append-only, hash-chained run ledger (`ledger.jsonl`) is scoped to the discrete `aw run` / `aw runs` workflow execution path. Wherever this spec otherwise says "run ledger" or "ledger" of a driver run, it means that driver's durable run record; the hash-chain properties (sequence, parent link, record hash, chain verification) hold only for `ledger.jsonl` (amended 2026-10-14 per the 2026-10-08 maintainer Option (b) decision in plan `rdjka2` OQ-01 and decision record `utb2qr`).
     ```
   - In `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 5.1 (line 1085), replace the single line:
     ```markdown
     - the append-only, hash-chained run ledger.
     ```
     with:
     ```markdown
     - the append-only, hash-chained run ledger (`ledger.jsonl`, scoped to the discrete `aw run` / `aw runs` workflow execution path; driver runs `aw oc run` / `aw agy run` record execution in `state.json` and `events.jsonl` and do not write `ledger.jsonl`, per the 2026-10-08 maintainer Option (b) decision in plan `rdjka2` OQ-01 and decision record `utb2qr`).
     ```

3. **Section 5.3 / 5.3a same-line amendments (`E-03`)**: the four substitutions listed verbatim in E-03.

4. **User-facing doc correction (`E-04`)**: the one-sentence replacement in `docs/evidence.md` listed verbatim in E-04.

5. **Provenance note and validation (`E-05`)**:
   - Run the `aw specs note` command given verbatim in E-05.
   - Run every command in `## Required tests / validation`.

## Deferred / out of scope (with reason)

- Adding `aw run init` and amending `25kzda` Section 6.2 (owned by sibling pending plan `v47z9u`, from backlog `hegwri`).
  - Carrier: v47z9u

## Scope check

- Over-scope: none.
- Under-scope: none after review. Both spec locations named in backlog `66ls4r` (`25kzda` Section 1.2 step 8 and Section 5.1) are covered, plus the four Section 5.3 / 5.3a sentences making the same claim (F-4) and the user-facing `docs/evidence.md` statement (F-5), so the amendment does not leave the spec or docs contradicting it. Other uses of "run ledger" in the spec (for example Sections 2.x consent records and 4.1 `ABORT RUN`) are covered by E-02's terminology clause rather than edited one by one, because Section 4.2 is transcription-locked and Sections 5.5 / 5.6 belong to `jmogmv`.

## Required tests / validation

- Targeted behavioral and spec-transcription tests:
  - `python3 -m pytest tests/test_run_recovery_cli.py tests/test_run_finding_abort_partition.py tests/test_run_finding_spec_transcription.py`
- Spec and repository checks:
  - `AW_NO_REEXEC=1 python3 -m agent_workflows specs check`
  - `python3 -c "from agent_workflows import spec_citations; a = spec_citations.stale_spec_anchors('.', spec_citations.default_scan_roots('.')); assert not a, a; print('stale_spec_anchors:', len(a))"`
  - `AW_NO_REEXEC=1 python3 -m agent_workflows check --agent` (exits 1 on the pre-existing corpus findings; the bar is the E-05 comparison against the E-01 baseline, not exit 0)
  - `AW_NO_REEXEC=1 python3 -m agent_workflows sanitize --agent`
  - `wc -l .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (equal to the E-01 count plus the one `## Workflow history` line `aw specs note` adds)
  - `grep -nP '[\x{2013}\x{2014}]' docs/evidence.md` (no output)
- Full test suite:
  - `python3 -m pytest`

## Spec / documentation sync

- `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` is the direct target of this plan (Section 1.2 step 8, Section 5.1, four Section 5.3 / 5.3a sentences, and `## Workflow history` via `aw specs note`), declared in `- Scope-Paths:`. WHY a spec edit: the maintainer's 2026-10-08 Option (b) resolution (`rdjka2` OQ-01) explicitly instructed "amend spec 25kzda to say so"; the spec currently states a requirement the decided architecture does not meet, so every plan reviewed against `25kzda` inherits a false premise until it is amended. The amendment records a decision already taken and changes no code behavior.
- `docs/evidence.md` line 3 is corrected (E-04) because it is the user-facing statement of the same claim. `docs/architecture.md` ("Evidence and ledger" layer, describing `run_evidence.py` / `run_ledger_store.py` per step attempt) is accurate as written for the `aw run` runtime it describes and is not changed. `docs/recovery.md` was already corrected by `rdjka2`.

## Open questions

### OQ-01: Should `25kzda` Section 1.2 step 8 and Section 5.1 be amended to scope the hash-chained ledger to `aw run` / `aw runs`, or should they record an un-scoped divergence note?

- Blocking: no
- Status: resolved
- Owner: maintainer (resolved 2026-10-08 in `rdjka2` OQ-01; confirmed by `utb2qr` and `25kzda` amendment convention)
- Resolution or deferral rationale: Resolved from repository evidence. Backlog `66ls4r` noted that `rdjka2`'s `## Spec / documentation sync` section (authored on `2026-10-02` before `rdjka2` OQ-01 was answered) phrased the follow-on obligation as "either amend `25kzda` to scope the ledger requirement to the path that implements it, or record an accepted, dated divergence in the spec's own terms." Decision record `utb2qr` (`2026-10-07`) subsequently specified under Section 5.2 (Option (b) True Cost #1) `"Formalizing the divergence from spec 25kzda Section 1.2 Step 8 and Section 5.1 via a declared follow-on spec amendment"` and under Section 6 (Recommendation #4) `"schedules a tidy spec amendment for 25kzda"`. On `2026-10-08`, the maintainer interactively resolved `rdjka2` OQ-01 to Option (b) with the explicit instruction: `"OPTION (b). Runner (driver) runs keep state.json/events.jsonl as their record; amend spec 25kzda to say so, correct the misleading comments, and leave the ledger code for the separate aw run path"`. Moreover, under `25kzda`'s established in-place amendment convention (`00pirb`, `e6w056`, `sa13no`, `u28vqb`), an in-place dated amendment in Section 1.2 step 8 and Section 5.1 preserves the requirement text while stating both the driver substrate (`state.json` and `events.jsonl`) and the dated scoping of `ledger.jsonl` to `aw run` / `aw runs` (citing `rdjka2` OQ-01 and `utb2qr`), satisfying both formulations simultaneously.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output from (1) `grep -n` of each E-02, E-03, and E-04 anchor string in the spec and in `docs/evidence.md`, showing every unamended line, (2) `grep -n` showing `rdjka2` OQ-01's `OPTION (b)` maintainer resolution and `ls` of `utb2qr` on disk, (3) `grep -nE 'ledger_store|RunLedgerStore|ledger\.jsonl' agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` showing no matches, (4) the `stale_spec_anchors` command from `## Required tests / validation` printing `stale_spec_anchors: 0`, (5) the targeted pytest command exiting `0` with its summary line, (6) the spec's `wc -l`, and (7) the baseline `aw check --agent` result record's `findings_by_severity` plus its sorted `error` rule ids.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff -U0` hunks for the spec showing exactly two single-line replacements, at Section 1.2 step 8 and at Section 5.1's ledger bullet, whose new text names `state.json` and `events.jsonl` for driver runs (`aw oc run` / `aw agy run`), scopes `ledger.jsonl` to the discrete `aw run` / `aw runs` path, carries the step 8 terminology clause, and cites `rdjka2` OQ-01 and `utb2qr`; plus `git diff --stat` showing no hunk inside Sections 4.2, 4.6, 5.5, 5.6, or 6.2.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted `git diff -U0` hunks for the spec showing the four in-line substitutions at the Section 5.3 intro, the snapshot sentence, the 5.3a telemetry clause, and resume step 1, each with dated `rdjka2` provenance; plus pasted `grep -n` output showing the strings `"replaying the ledger is authoritative"`, `"The hash-chained ledger is the run's record"`, and `"verifies the ledger chain before doing anything"` no longer occur in the spec, and the pasted `load_state` / `load_json` and `run_cli._run_resume` excerpts that E-03 item 4 required reading.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `git diff` of `docs/evidence.md` showing only the line-3 sentence replaced (and any reflow of that paragraph), and the pasted (empty) output of `grep -nP '[\x{2013}\x{2014}]' docs/evidence.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted output of (1) `sed -n` of the spec's `## Workflow history` heading plus the next line showing the new `9epp40 (66ls4r)` entry first, (2) `AW_NO_REEXEC=1 python3 -m agent_workflows specs check` exiting `0`, (3) the `stale_spec_anchors` command printing `stale_spec_anchors: 0`, (4) the post-edit `aw check --agent` result record compared with the V-01 baseline: no `warning` or `error` diagnostic located at this plan, the spec, or `docs/evidence.md`, and no `error` rule id absent from the baseline, (5) `AW_NO_REEXEC=1 python3 -m agent_workflows sanitize --agent` exiting `0` with outcome `clean`, (6) the spec's `wc -l` equal to the V-01 count plus one, and (7) bare `python3 -m pytest` exiting `0` with its pass summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`- Status: approved`). Open questions: all resolved (OQ-01). Scope fence: `- Scope-Paths:` is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Stop only for a genuinely unsafe condition: an E-01 anchor already amended, a host driver now writing `ledger.jsonl`, or a concurrent edit to the same spec line that cannot be combined. Commit only your own paths (the spec, `docs/evidence.md`, and this plan) through `aw commit 9epp40 -- <paths>`; never push. Paste the actual runner output for every test and check claim; a claim without pasted output is not evidence. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize 9epp40` only after `aw ipd lint --phase pre-transition` conforms.
