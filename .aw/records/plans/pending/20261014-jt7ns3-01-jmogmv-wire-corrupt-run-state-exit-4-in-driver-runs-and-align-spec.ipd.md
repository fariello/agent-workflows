# IPD: Report corrupt driver run state as a clean exit 2 with recovery guidance and align spec 25kzda 5.5 and 5.6

- Date: 2026-10-14
- Kind: child
- Concern: Driver runs (`aw oc run` / `aw agy run`) handle a corrupt `state.json` inconsistently: unparseable JSON exits `2` with a bare `Invalid JSON` message and no recovery guidance, while undecodable bytes or a structurally wrong document (valid JSON, wrong shape) crash with an `unexpected failure` traceback (`UnicodeDecodeError`, `KeyError`, `AttributeError`). Spec `25kzda` Sections 5.5 and 5.6 describe a run-wide abort with exit `4` that the maintainer ruled out on 2026-10-15 (OQ-01): a corrupt run state is 'could not run' (exit `2`) on every output surface.
- Scope: Add `CorruptRunStateError(DriverError)` in `agent_workflows/runner_shared.py` and make `load_state` raise it, with a message naming the file and giving recovery guidance, for unparseable/undecodable JSON and for a document that is not an object with a list `queue` of objects; handle it in `main` of `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` so every output mode (human, `--json`, `--agent`) exits `2` with that message and no traceback; amend spec `25kzda` Sections 5.5 and 5.6 and `docs/cli-output-contract.md` Section 3.1 to drop exit `4` for this condition; update `agent_workflows/command_surface.py`'s reachability comment; add a CHANGELOG `Fixed` line; cover it with behavioral tests in `tests/test_fixfirst_end_to_end.py` and `tests/test_runner_shared.py`.
- Scope-Paths: .aw/records/plans/**/20261014-jt7ns3-01-jmogmv-wire-corrupt-run-state-exit-4-in-driver-runs-and-align-spec.ipd.md, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/command_surface.py, .aw/records/specs/**/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, docs/cli-output-contract.md, CHANGELOG.md, tests/test_fixfirst_end_to_end.py, tests/test_runner_shared.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: jt7ns3
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: jt7ns3
- Order: 1
- Highest E allocated: 06
- Author: Antigravity
- Id: jmogmv

## Workflow history
- 2026-10-16 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; round 2 PR-201..PR-209; plan re-cut to the maintainer's OQ-01 answer (exit 2 everywhere, recovery text)
- 2026-10-15 to-review (aw set): demoted reviewed -> to-review: returned to to-review: maintainer resolved OQ-01 on 2026-10-15 (exit 2 everywhere + recovery text), which inverts the plan's exit-4 design; it must be re-reviewed against that answer
- 2026-10-15 reviewed (/plan-review opencode model=its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-002..PR-008 fixed; PR-001 open as blocking OQ-01; readiness NO-GO
- 2026-10-14 to-review (Antigravity): populated review-ready IPD from backlog item `jt7ns3`.
- 2026-10-14 draft (Antigravity): created.

## Goal

A corrupt driver run state (`state.json`) on either host (`aw oc run` / `aw agy run`) is reported as "could not run": exit `2` in every output mode (human, `--json`, `--agent`), with a message that names the corrupt file and tells the operator how to recover, and never a traceback. The structural case (valid JSON, wrong shape) gets the same clean exit `2`. The run dispatches no further turn once the corruption is seen. Spec `25kzda` Sections 5.5 and 5.6 and `docs/cli-output-contract.md` Section 3.1 are amended to match, dropping exit `4` for this condition (maintainer ruling 2026-10-15, OQ-01). The filename slug still says "exit-4"; it is kept so that the plan's id6 references and Scope-Paths stay stable, and the title records the current intent.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Detect corrupt run state in `runner_shared`

- [ ] E-01 Add `CorruptRunStateError(DriverError)` beside `EmptyStatusSelection` in `agent_workflows/runner_shared.py`, and make `load_state` validate `state.json`.
  - Depends on: none
  - Expected outcome: `runner_shared.load_state(run_dir)` reads `path = run_dir / "state.json"` itself (it no longer delegates to `load_json`, which stays unchanged for its other callers). A missing file still raises plain `DriverError(f"Required file not found: {path}")`. `json.JSONDecodeError` or `UnicodeDecodeError` raises `CorruptRunStateError(...) from exc`. A decoded value that is not a `dict`, lacks a `"queue"` key, has a non-`list` `"queue"`, or has a `"queue"` entry that is not a `dict` also raises `CorruptRunStateError`. Both messages name `path`, say what is wrong (the decode error text or `expected a JSON object with a list 'queue' of objects`), and end with the recovery guidance the maintainer specified, in one shared constant: the run cannot be resumed, so start a new run (`aw oc run` / `aw agy run`); work already merged to main is kept; the old run's record of finished items is lost, so the new run re-checks them. `"repo"` is deliberately NOT required: `tests/test_runwire_state_translation.py::test_save_state_funnel_persistence_and_outcomes` and three `aw runs repair` tests load a state without it (measured at review), and the rule here is the shape every observed `load_state` call already satisfies. Leave `run_exit_code` unchanged (no `run_wide_abort_class` parameter; the exit-4 path is dropped).
  - Execution state: pending

### Task group 2: Report it cleanly in both drivers

- [ ] E-02 Handle `CorruptRunStateError` in `main` of `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`, and update the reachability comment in `agent_workflows/command_surface.py`.
  - Depends on: E-01
  - Expected outcome: Both drivers re-export `CorruptRunStateError as CorruptRunStateError` from `agent_workflows.runner_shared`, following the existing `from agent_workflows.runner_shared import X as X` pattern, and `oc_runipd.__all__` lists it. In each `main`, `except CorruptRunStateError as exc:` sits after `except EmptyStatusSelection:` and before `except DriverError as exc:`. Under `runner_shared.is_agent_mode(args)` it calls `runner_shared.emit_agent_run_refusal_record(exc, cmd="oc run"|"agy run", run_dir=run_dir)`, which already emits `exit: 2`, `outcome: "cannot-run"` and `summary: str(exc)`. In every mode it prints `f"runipd: {exc}"` / `f"runagy: {exc}"` to `sys.stderr` and returns `2`. It does NOT try to render the run summary table, because the generic `except DriverError` arm reloads `state.json` to render one and would hit the same corruption. `run_queue` needs no handler: its `load_state` reloads sit outside the per-item `try: execute_item(...)` (a review probe showed a mid-run `CorruptRunStateError` propagating out of `run_queue` on both hosts after 1 of 2 items had been dispatched). The exit-`4` explanation in the `command_surface.py` comment above the `"oc runipd"` declaration (`# Neither \`4\` nor \`130\` is reachable through \`run_queue\``) is rewritten to say that `4` is not returned by the drivers at all, because a corrupt run state exits `2` per spec `25kzda` Section 5.6 (maintainer ruling 2026-10-15). `exit_contract=(0, 1, 2, 3)` is unchanged.
  - Execution state: pending

### Task group 3: Contract sync

- [ ] E-03 Amend spec `25kzda` Sections 5.5 and 5.6 in place and record the amendment.
  - Depends on: E-01, E-02
  - Expected outcome: In `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, each edit is a single-line, in-place change, so every line offset above `## Workflow history` is preserved. (1) Under `### 5.5 Retry policy`, in the `- corrupt run ledger only.` bullet of group (c) and in the Notes cell of the `| corrupt run ledger only |` row, add no new backticked 6-character ID; the existing `(Shipped.)` wording may stay. They state that `ledger.jsonl` corruption on the discrete `aw run` / `aw runs` path is reported by `run_cli` (exit `5`), and that a corrupt driver run state (`state.json` on `aw oc run` / `aw agy run`, which write no ledger per the 2026-10-08 Option (b) decision) stops the run before any further turn and exits `2` with recovery guidance. (2) In `### 5.6 Reporting`, the `| 4 | ... |` row's sentence beginning `The drivers return \`0\`, \`1\`, \`2\`, and \`3\` today` is replaced in the same line, keeping the rest of the row (the UNRECONCILED CONFLICT record and the `u28vqb` reconciliation) intact. The replacement says that the drivers never return `4`: by maintainer ruling 2026-10-15 a corrupt driver run state is "could not run" and exits `2` on every output surface, with recovery guidance. (3) `AW_NO_REEXEC=1 python3 -m agent_workflows specs note <spec path> --message "AMENDED 2026-10-xx (plan jmogmv, backlog jt7ns3): Sections 5.5 and 5.6 ..."` appends the history record. Then re-run `python3 -m pytest -o addopts="" tests/test_fixfirst_end_to_end.py -k spec_5_5` (the `6g08rp` owner-ID guard on the Section 5.5 table) and confirm it still passes.
  - Execution state: pending

- [ ] E-04 Sync `docs/cli-output-contract.md` Section 3.1, the `command_surface` comment wording check, and CHANGELOG.
  - Depends on: E-03
  - Expected outcome: In `docs/cli-output-contract.md` Section 3.1, table 2's `- \`4\`: Run-wide abort class. ... not returned by current driver \`run_queue\` dispatch.` bullet is rewritten to say the drivers do not return `4`, and that a corrupt or unreadable run state (`state.json`) is reported as exit `2` in every output mode, with a message naming the file and how to recover. The `**Code 4**` bullet under "Disagreement on Codes 3 and 4" is updated to match. `CHANGELOG.md`'s `2.0.0 (pending)` list gains one `- Fixed:` line, in user-facing prose with no em or en dashes: a corrupt or unreadable run state file now makes `aw oc run` / `aw agy run` stop with a clear message naming the file and how to recover (start a new run; merged work is kept), instead of a crash traceback.
  - Execution state: pending

### Task group 4: Behavioral tests

- [ ] E-05 Update and add behavioral tests in `tests/test_fixfirst_end_to_end.py` and `tests/test_runner_shared.py`.
  - Depends on: E-01, E-02
  - Expected outcome: (1) `tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd._run_corrupt_state` (driven by `test_corrupt_state_oc` / `test_corrupt_state_agy`) is parameterized over these `state.json` bodies: `{corrupt json`, undecodable bytes `b"\xff\xfe"`, `[1]`, `{"queue": "x"}`, `{"queue": ["x"]}`, and `{"repo": "."}` (no queue). For each body it calls `mod.main(["resume", ...])` and asserts: `rc == 2`, no exception escapes, stderr names `state.json`, and stderr contains the recovery guidance ("start a new run"). The stale `# Measured: exits 2 ... not exit 4` comment is replaced. (2) A `--agent` variant on `{corrupt json` and `{"queue": "x"}` asserts `rc == 2` and that the last stdout line parses as an `aw.agent/v1` record with `exit == 2`, `outcome == "cannot-run"`, and a `summary` containing the recovery guidance. (3) A mid-run case uses a 2-item queue with `isolate_worktree: False` and a stubbed `fake_turn` that records each dispatched `id6`. Corruption is injected by wrapping the module's `load_state` (`mock.patch.object(mod, "load_state", ...)`) so it overwrites `state.json` with `{corrupt json` on the first reload after item 1 has left `queued`/`running`. A save-side hook does NOT work here: a review probe showed the driver rewrites state after it, so the run finished 4 turns with rc 1. The case asserts that `mod.run_queue` raises `runner_shared.CorruptRunStateError` and that item 2's `id6` was never dispatched; the review probe showed both outcomes on both hosts. (4) In `tests/test_runner_shared.py`, a test calls `runner_shared.load_state` on a valid state (it loads), on a missing `state.json` (`DriverError` raised, `CorruptRunStateError` not raised), and on the corrupt bodies from (1) (`CorruptRunStateError` raised). All of this is behavioral: no source reads, and no class-identity or literal-tuple pins (P16). None of these tests carries a `slow` or `livecorpus` mark.
  - Execution state: pending

### Task group 5: Validation

- [ ] E-06 Run the contract checks, the targeted modules, the routine suite, and the leak sanitizer.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: All of the following exit 0 with zero failures: `AW_NO_REEXEC=1 python3 -m agent_workflows specs check`, `python3 -m pytest -o addopts="" -n auto tests/test_fixfirst_end_to_end.py tests/test_runner_shared.py tests/test_exit_vocabulary_boundary.py tests/test_run_exit_aggregate.py tests/test_runwire_verifier_authority.py tests/test_runwire_state_translation.py tests/test_run_viewer.py tests/test_run_recovery_cli.py tests/test_runs_subdir_root.py`, bare `python3 -m pytest`, and `AW_NO_REEXEC=1 python3 -m agent_workflows sanitize --agent`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- **Maintainer ruling 2026-10-15 (OQ-01 below)**: a corrupt run state is "could not run", so it exits `2` in every output mode and exit parity holds; spec `25kzda` Section 5.6's exit `4` for this condition is dropped; the message names the file and gives recovery guidance; the structural case gets the same clean exit `2`.
- **Settled ledger-substrate boundary (`rdjka2` OQ-01 Option (b), `utb2qr`)**: driver runs record their state in `state.json` / `events.jsonl` and write no `ledger.jsonl`. `tests/test_runwire_verifier_authority.py::test_set_level_checks` fences `runner_shared.py`, `oc_runipd.py` and `agy_runipd.py` from importing `run_engine` or `run_recovery`, and this plan adds no such import.
- **Agent schema**: `agent_schema.render_jsonl_record` refuses any `exit` outside `(0, 1, 2)` (`agent_workflows/agent_schema.py`, `exit_code not in (0, 1, 2)`), and `runner_shared.emit_agent_run_refusal_record` already emits `exit: 2` / `outcome: "cannot-run"` / `summary: str(exc)`. Exit `2` everywhere is therefore schema-valid with no schema change.
- **Cross-driver exception pattern**: shared `DriverError` subclasses (`EmptyStatusSelection`, `StallTimeout`, `HostSpawnError`) live in `runner_shared.py` and are re-exported by both drivers, and their `except` arm in `main` precedes `except DriverError`.
- **Spec `25kzda` neighbours**: plans `9epp40` (Section 1.2 step 8 and 5.1 ledger scoping) and `6g08rp` (Section 5.5 owner IDs, guarded by `tests/test_fixfirst_end_to_end.py::test_e05_spec_5_5_table_owner_ids_resolve`) are both executed. Section 4.2 is transcription-locked by `tests/test_run_finding_spec_transcription.py` and is not touched.
- **Atomic writes**: `runner_shared.save_state` writes through `atomic_write_json` (temp file, fsync, `os.replace`), so the condition is rare in practice. The maintainer was told that a scan of 462 recorded `state.json` files found 0 corrupt.

## Findings

| # | Location / symbol | Finding | Impact |
|---|---|---|---|
| F-01 | `agent_workflows/runner_shared.py` `load_state` -> `load_json` | `load_state` delegates to `load_json`, which maps only `FileNotFoundError` and `json.JSONDecodeError` to `DriverError`. It does not catch `UnicodeDecodeError` and does no shape check. | Review probe on both hosts: `resume` on `{corrupt` gives rc 2 with a bare `Invalid JSON in ...` message and no recovery guidance; on `b"\xff\xfe"` it gives `unexpected failure` plus a re-raised `UnicodeDecodeError` (resume and `status --json`); on `[1]`, `{"queue":"x"}`, `{"queue":["x"]}` and `{"repo":"."}` it gives `unexpected failure` plus a re-raised `AttributeError`/`KeyError`. |
| F-02 | `oc_runipd.main` / `agy_runipd.main` `except DriverError as exc:` | The generic arm already exits `2` and, under `--agent`, emits a schema-valid `cannot-run` record. Without `--agent` it reloads `state.json` to render a summary table, swallowing any exception. | A dedicated `CorruptRunStateError` arm ahead of it makes the message and exit deterministic, and avoids a pointless second read of a file already known to be corrupt. |
| F-03 | Spec `25kzda` Section 5.5 `| corrupt run ledger only |` row and group (c) bullet; Section 5.6 `| 4 |` row; `docs/cli-output-contract.md` Section 3.1 table 2 bullet `4` | These texts describe a run-wide abort with exit `4`, which the maintainer has ruled out for driver runs. | Without an amendment the contracts contradict the shipped behaviour. |
| F-04 | `tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd._run_corrupt_state` | It asserts `rc == 2` on unparseable JSON only, with a comment that frames 2 as a defect ("not exit 4"). | The structural and undecodable cases and the recovery text are not covered. |

## Proposed changes (ordered, validatable)

1. `runner_shared.CorruptRunStateError` and validating `load_state` with a shared recovery message (E-01).
2. A dedicated exit-2 handler in both drivers' `main`, covering every output mode, plus the `command_surface.py` comment (E-02).
3. Spec `25kzda` Sections 5.5 and 5.6 in-place amendment plus an `aw specs note` record (E-03).
4. `docs/cli-output-contract.md` Section 3.1 and a CHANGELOG `Fixed` line (E-04).
5. Behavioral tests (E-05).
6. Validation (E-06).

## Deferred / out of scope (with reason)

- Amending spec `25kzda` Section 1.2 step 8 and Section 5.1 to scope `ledger.jsonl` to discrete `aw run` / `aw runs` invocations: owned by sibling IPD `9epp40` (from backlog item `66ls4r`), now executed.
  - Carrier: 9epp40
  - Carrier-Evidence: .aw/records/plans/executed/20261014-runledger-04-9epp40-amend-spec-25kzda-1-2-step-8-and-5-1-to-scope-the-hash-chain.ipd.md
- Updating stale Set `fixfirst` and `verifier transport failure` owner plan IDs in spec `25kzda` Section 5.5: owned by sibling IPD `6g08rp` (from backlog item `w5opbr`), now executed.
  - Carrier: 6g08rp
  - Carrier-Evidence: .aw/records/plans/executed/20261014-w5opbr-01-6g08rp-replace-stale-and-non-resolving-owner-plan-ids-in-spec-25kzd.ipd.md
- Widening the `oc runipd` / `agy runipd` `exit_contract` to include `4`, and threading `run_wide_abort_class` through `runner_shared.run_exit_code`: dropped by the maintainer's OQ-01 ruling (exit `2` everywhere).
  - Carrier-Declined: deliberate non-goal; the maintainer ruled exit 4 out for this condition on 2026-10-15
- The same validation for `aw runs repair` (`run_viewer.repair_run`, which reads through `oc_runipd.load_state`): it inherits the clearer message automatically, and its exit path is not changed here. A probe showed `aw runs repair` on a corrupt run already exits `2`.
  - Carrier-Declined: inherited behaviour, no separate change required

## Scope check

- Over-scope: none. The exit-4 wiring the previous revision carried (abort-class constant, `run_exit_code` parameter, `exit_contract` widening, the `test_exit_vocabulary_boundary.py` / `test_run_exit_aggregate.py` edits) was removed by this review, per OQ-01.
- Under-scope: none. The traceback-free structural case, the recovery text, and exit parity on `--agent` are all covered (E-01, E-02, E-05), as are the spec, doc and CHANGELOG sync (E-03, E-04).

## Required tests / validation

- `AW_NO_REEXEC=1 python3 -m agent_workflows specs check`
- `python3 -m pytest -o addopts="" -n auto tests/test_fixfirst_end_to_end.py tests/test_runner_shared.py tests/test_exit_vocabulary_boundary.py tests/test_run_exit_aggregate.py tests/test_runwire_verifier_authority.py tests/test_runwire_state_translation.py tests/test_run_viewer.py tests/test_run_recovery_cli.py tests/test_runs_subdir_root.py`
- `python3 -m pytest`
- `AW_NO_REEXEC=1 python3 -m agent_workflows sanitize --agent`

## Spec / documentation sync

This plan AMENDS approved spec `25kzda` (Sections 5.5 and 5.6 only; declared in Scope-Paths). Why: the maintainer's 2026-10-15 OQ-01 ruling changes the contract itself, from "a corrupt run state aborts the run with exit `4`" to "a corrupt run state is 'could not run', exit `2` on every surface, with recovery guidance". Shipping the code without the amendment would leave an approved spec describing an exit code the drivers deliberately never return. `docs/cli-output-contract.md` Section 3.1 and `CHANGELOG.md` are updated in E-04.

## Open questions

### OQ-01: What does a corrupt `state.json` return, on each output surface?

- Blocking: yes
- Finding: PR-001
- Status: resolved
- Owner: maintainer
- Context: under `--agent`, `oc_runipd.main` / `agy_runipd.main` emit an `aw.agent/v1` refusal record with `exit: 2`, and that schema cannot carry `4` (`agent_schema.render_jsonl_record` refuses it). Exit `4` on the human surface and exit parity on the agent surface could not both hold.
- Options: (a) agent mode keeps exit `2` and the doc records an audience divergence; (b) agent mode emits no record and exits `4`; (c) widen the `aw.agent/v1` exit vocabulary.
- Resolution or deferral rationale: RESOLVED by the maintainer 2026-10-15 (interactive /askme): exit 2 in EVERY output mode (human, --json, --agent), so a corrupt run state is 'could not run' everywhere and exit parity holds; the spec 25kzda Section 5.6 exit 4 for this condition is dropped (spec amendment needed). The message must name the corrupt file and give recovery guidance: start a new run; work already merged to main is kept; the old run's record of finished items is lost so the new run re-checks them. The structural-corruption case (valid JSON, wrong shape) must produce the same clean exit-2 message instead of a traceback. Context supplied to the maintainer: state.json is written atomically (runner_shared.atomic_write_json), and a scan of all 462 state.json files under .aw/records/runs found 0 corrupt; the only observed corruption is synthetic, in tests. This plan was re-cut to that answer by /plan-review round 2 (2026-10-16).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted `git diff -- agent_workflows/runner_shared.py`. It must show `class CorruptRunStateError(DriverError)`; `load_state` raising it on decode errors and on each shape violation (non-object, missing or non-list `queue`, non-object entry); plain `DriverError` kept for a missing file; the shared recovery text; `load_json` and `run_exit_code` unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff -- agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py agent_workflows/command_surface.py`. It must show the re-export (and the `__all__` entry), the `except CorruptRunStateError` arm placed between `EmptyStatusSelection` and `DriverError` in both `main`s, the `--agent` refusal-record call, `return 2`, no summary-table reload, the rewritten comment, and `exit_contract=(0, 1, 2, 3)` unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted `git diff -- <spec path>` showing only in-place changed lines in Section 5.5 (group (c) bullet and the `corrupt run ledger only` row) and Section 5.6 (the `| 4 |` row), plus the appended history record. Also the pasted `git diff --stat` line count for the spec (the added lines must equal the history lines alone), and the pasted passing output of `python3 -m pytest -o addopts="" tests/test_fixfirst_end_to_end.py -k spec_5_5`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `git diff -- docs/cli-output-contract.md CHANGELOG.md` showing the rewritten table-2 bullet `4`, the `**Code 4**` bullet, and the one `- Fixed:` line, which contains no em or en dash.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted `python3 -m pytest -o addopts="" -v tests/test_fixfirst_end_to_end.py -k corrupt` and `python3 -m pytest -o addopts="" -v tests/test_runner_shared.py -k load_state` output, showing every corrupt-body case passing on both hosts: rc 2 with the recovery text, the `--agent` record carrying `exit` 2 / `cannot-run`, and the mid-run case raising `CorruptRunStateError` with item 2 never dispatched. Plus a pasted sensitivity run. With the `except CorruptRunStateError` arm removed from `oc_runipd.main`, the oc recovery-text assertions FAIL. With `load_state` reverted to `return load_json(run_dir / "state.json")`, the structural cases FAIL with an escaped exception. Each sensitivity change is followed by its revert and a pasted empty `git diff --stat` for the touched file relative to the intended change.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted output, with the summary lines, of `specs check`, the targeted pytest command, bare `python3 -m pytest` (`N passed`, 0 failed), and `sanitize --agent` (outcome not `fail`).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

- Open questions: OQ-01 is resolved by the maintainer (2026-10-15); nothing blocks execution. Execute only after human approval (`aw ipd set approved jmogmv --by-human`).
- Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition. An edit outside it is allowed when needed and must be justified at finalize (`--scope-reason <path>=<why>`); a declared path left untouched is acknowledged with `--scope-ack`. This plan amends approved spec `25kzda` (Sections 5.5 and 5.6 only; Section 4.2 is transcription-locked and must not change).
- Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never mark a `V-*` `pass` without concrete observed output. Run the routine suite bare as `python3 -m pytest`.
- Commits: path-scoped via `aw commit jmogmv -- <paths>`; verify `git diff --cached --name-only` first; never `git add -A`, never push, never tag. Sensitivity edits from V-05 are reverted and never committed.
- Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize, so leave the plan in `pending/`. When executed by hand (`aw ipd begin jmogmv`), finish with `aw ipd finalize jmogmv --actor <agent/model> --message <summary> --apply` once every `E-*` is `performed`, every `V-*` is `pass`, and `aw ipd lint --phase pre-transition` conforms; never `git mv` the plan to `executed/`.
