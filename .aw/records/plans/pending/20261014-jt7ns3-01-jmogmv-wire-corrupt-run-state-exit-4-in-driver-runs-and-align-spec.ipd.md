# IPD: Wire corrupt run state exit 4 in driver runs and align spec 25kzda 5.5 and 5.6

- Date: 2026-10-14
- Kind: child
- Concern: Driver runs (`aw oc run` / `aw agy run`) raise generic `DriverError` on a corrupt `state.json` and exit `2` rather than returning spec `25kzda` Section 5.6's run-wide abort exit code `4`, and spec `25kzda` Sections 5.5 and 5.6 do not reflect the settled `rdjka2` OQ-01 Option (b) decision (`utb2qr`) that driver runs persist `state.json` and `events.jsonl` rather than `ledger.jsonl`.
- Scope: Define `CORRUPT_RUN_LEDGER_ABORT_CLASS` and `CorruptRunStateError(DriverError)` in `agent_workflows/runner_shared.py`, raise `CorruptRunStateError` from `load_state` on unparseable or structurally corrupt `state.json`, pass `run_wide_abort_class` through `runner_shared.run_exit_code` to `run_evidence.aggregate_run_exit`, catch `CorruptRunStateError` in `main` of `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` (it already propagates out of `run_queue`) to abort the run and exit `4`, with the `--agent` surface handled per OQ-01, widen `oc runipd` and `agy runipd` `exit_contract` to `(0, 1, 2, 3, 4)` in `agent_workflows/command_surface.py`, sync spec `25kzda` Sections 5.5 and 5.6 and `docs/cli-output-contract.md` Section 3.1, and update `tests/test_fixfirst_end_to_end.py`, `tests/test_run_exit_aggregate.py`, and `tests/test_exit_vocabulary_boundary.py`.
- Scope-Paths: .aw/records/plans/pending/20261014-jt7ns3-01-jmogmv-wire-corrupt-run-state-exit-4-in-driver-runs-and-align-spec.ipd.md, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/command_surface.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, docs/cli-output-contract.md, tests/test_fixfirst_end_to_end.py, tests/test_run_exit_aggregate.py, tests/test_exit_vocabulary_boundary.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Work-Kind: bug
- Priority: medium
- From-Backlog: jt7ns3
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: jt7ns3
- Order: 1
- Highest E allocated: 05
- Author: Antigravity
- Id: jmogmv

## Workflow history
- 2026-10-15 reviewed (/plan-review opencode model=its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-002..PR-008 fixed; PR-001 open as blocking OQ-01; readiness NO-GO

- 2026-10-14 draft (Antigravity): created.
- 2026-10-14 to-review (Antigravity): populated review-ready IPD from backlog item `jt7ns3`.

## Goal

Ensure that a corrupt run state (`state.json`) on either host driver (`aw oc run` / `aw agy run`) aborts the run without dispatching any new turn and exits with spec `25kzda` Section 5.6's run-wide abort exit code `4` via `runner_shared.run_exit_code(..., run_wide_abort_class="Corrupt run ledger")`, while aligning spec `25kzda` Sections 5.5 and 5.6 and `docs/cli-output-contract.md` Section 3.1 with both the shipped exit `4` wiring and the maintainer's 2026-10-08 Option (b) ledger-substrate decision (`rdjka2` OQ-01, `utb2qr`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Corrupt run state exception and exit-code 4 wiring in `runner_shared`, `oc_runipd`, `agy_runipd`, and `command_surface`

- [ ] E-01 Define `CORRUPT_RUN_LEDGER_ABORT_CLASS` and `CorruptRunStateError(DriverError)`, validate `state.json` in `load_state`, and add `run_wide_abort_class` to `run_exit_code` in `agent_workflows/runner_shared.py`.
  - Depends on: none
  - Expected outcome: `agent_workflows/runner_shared.py` defines `CORRUPT_RUN_LEDGER_ABORT_CLASS: str = "Corrupt run ledger"` and `class CorruptRunStateError(DriverError):` alongside `EmptyStatusSelection`. `runner_shared.load_state(run_dir: Path) -> dict[str, Any]` reads `path = run_dir / "state.json"`: when `path` is missing (`FileNotFoundError`), it still raises plain `DriverError(f"Required file not found: {path}")` (preserving exit `2` for missing state files); when `path` exists on disk and `json.loads` raises `json.JSONDecodeError` or `UnicodeDecodeError`, `load_state` raises `CorruptRunStateError(f"Invalid JSON in {path}: {exc}") from exc`; and when the decoded JSON value is not a `dict` or has a `"queue"` key whose value is not a `list`, `load_state` raises `CorruptRunStateError(f"Corrupt run state in {path}: expected a JSON object with a list 'queue'")`. `runner_shared.load_json` remains unchanged for non-state callers. `runner_shared.run_exit_code(queue: Iterable[Mapping[str, Any]], *, stopped: bool, run_wide_abort_class: str | None = None) -> int` forwards `run_wide_abort_class=run_wide_abort_class` to `run_evidence.aggregate_run_exit(aggregated_run_items(queue, stopped=stopped), run_wide_abort_class=run_wide_abort_class)`, returning exit code `4` when `run_wide_abort_class == CORRUPT_RUN_LEDGER_ABORT_CLASS`.
  - Execution state: pending

- [ ] E-02 Re-export `CorruptRunStateError` and `CORRUPT_RUN_LEDGER_ABORT_CLASS` and wire run-wide abort exit `4` in `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, and `agent_workflows/command_surface.py`.
  - Depends on: E-01
  - Expected outcome: Both `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` re-export `CorruptRunStateError as CorruptRunStateError` and `CORRUPT_RUN_LEDGER_ABORT_CLASS as CORRUPT_RUN_LEDGER_ABORT_CLASS` from `agent_workflows.runner_shared` (and include them in `oc_runipd.__all__`). `run_queue` needs NO new handler: every `load_state(run_dir)` reload in the dispatch loop (`state = load_state(run_dir)` at the top of `while True:`) sits OUTSIDE the per-item `try: execute_item(...)` block, and neither `execute_item` nor `runner_shared.execute_item_core` calls `load_state`, so a mid-run `CorruptRunStateError` already propagates out of `run_queue` to `main` (review probe: corrupting `state.json` after item 1 made both hosts' `run_queue` raise `DriverError: Invalid JSON ...` with 1 turn dispatched; the structural case raised `AttributeError: 'str' object has no attribute 'get'`). Inside `main` in both drivers, `except CorruptRunStateError as exc:` precedes `except DriverError as exc:`, prints `f"runipd: {exc}"` (in `oc_runipd.main`) or `f"runagy: {exc}"` (in `agy_runipd.main`) to `sys.stderr`, and returns `runner_shared.run_exit_code((), stopped=False, run_wide_abort_class=runner_shared.CORRUPT_RUN_LEDGER_ABORT_CLASS)` (exit `4`). Under `--agent` (`runner_shared.is_agent_mode(args)`) the handler does whatever OQ-01 decides; do NOT call `runner_shared.emit_agent_run_refusal_record` or `emit_agent_run_start_record` with exit `4`, because `agent_schema.render_jsonl_record` raises `ValueError: Field 'exit' must be an integer in (0, 1, 2)` (measured at review). In `agent_workflows/command_surface.py`, update the comment above the `"oc runipd"` declaration (`# Neither \`4\` nor \`130\` is reachable through \`run_queue\``) so it states that `4` is returned by `main` on `CorruptRunStateError` and `130` remains signal-derived, and the `CommandDeclaration` entries for `"oc runipd"` and `"agy runipd"` declare `exit_contract=(0, 1, 2, 3, 4)`.
  - Execution state: pending

### Task group 2: Spec `25kzda` Sections 5.5 and 5.6 sync, CLI contract doc sync, and behavioral test coverage

- [ ] E-03 Sync `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Sections 5.5 and 5.6 and `docs/cli-output-contract.md` Section 3.1 in place, and append a workflow history note on spec `25kzda`.
  - Depends on: E-01, E-02
  - Expected outcome: In `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`: (1) under `### 5.5 Retry policy`, the group (c) list item (`(c) Failures that abort the run (1 member):` followed by `- corrupt run ledger only.`) and the `| corrupt run ledger only |` table row are updated in place, each as a single-line edit (preserving line offsets above `## Workflow history` and adding no new backticked 6-character ID to the Section 5.5 `Notes` cell) to state that per the 2026-10-08 maintainer Option (b) decision (`rdjka2` OQ-01, `utb2qr`), discrete `aw run` / `aw runs` invocations validate `ledger.jsonl` via `RunLedgerStore.verify_chain` whereas driver runs (`aw oc run` / `aw agy run`) persist their run record in `state.json` and `events.jsonl` and validate `state.json` via `runner_shared.load_state` (`CorruptRunStateError`), and that both paths abort the run with exit code `4`; (2) under `### 5.6 Reporting`, the `| 4 | Corrupt run ledger ... |` exit-code row is updated in place to record that `oc_runipd.main` and `agy_runipd.main` catch `CorruptRunStateError` from `runner_shared.load_state` and return `4` through `runner_shared.run_exit_code(..., run_wide_abort_class="Corrupt run ledger")` -> `run_evidence.aggregate_run_exit` (`jmogmv`, from backlog `jt7ns3`); and (3) `AW_NO_REEXEC=1 python3 -m agent_workflows specs note 25kzda --message ...` appends a `## Workflow history` entry. In `docs/cli-output-contract.md` Section 3.1, table 2's `- \`4\`: Run-wide abort class. ... not returned by current driver \`run_queue\` dispatch.` bullet is rewritten to say `oc runipd` and `agy runipd` return `4` from `main` when `state.json` is corrupt (unparseable, or not an object with a list `queue`), and the agent-surface behavior OQ-01 decides is stated beside it.
  - Execution state: pending

- [ ] E-04 Update `tests/test_fixfirst_end_to_end.py`, `tests/test_run_exit_aggregate.py`, and `tests/test_exit_vocabulary_boundary.py` to verify exit code `4` on corrupt run state across both drivers.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: (1) In `tests/test_fixfirst_end_to_end.py`, `TestFixFirstEndToEnd._run_corrupt_state` (`test_corrupt_state_oc` and `test_corrupt_state_agy`) asserts `self.assertEqual(rc, 4)` with zero sessions dispatched and `"Invalid JSON"` on stderr, and also verifies that a structurally corrupt `state.json` (`{"queue": "not-a-list"}`), a mid-run `state.json` corruption during `run_queue` (between item 1 and item 2 in a 2-item queue), and a missing `state.json` behave as specified (exit `4` with zero further sessions dispatched for both corruption cases, the mid-run case injected by a stubbed turn that overwrites `state.json` after its own `save_state`; exit `2` for missing `state.json`, asserting only the exit code because `runner_shared.resolve_run_dir` refuses first with `Run not found` before `load_state` runs); the agent-surface case is tested as OQ-01 decides; (2) in `tests/test_run_exit_aggregate.py`, `TestRunExitAggregate` verifies that `runner_shared.run_exit_code(queue, stopped=..., run_wide_abort_class=runner_shared.CORRUPT_RUN_LEDGER_ABORT_CLASS)` returns `4` (`run_evidence._CLASSIFICATION_EXITS[run_evidence.AGGREGATE_ABORT_RUN]`) under both `stopped=False` and `stopped=True` (outranking `needs_input` and item failures), and that `runner_shared.load_state` raises `runner_shared.CorruptRunStateError` for unparseable, non-object, and non-list-`queue` `state.json` while a valid one loads; and (3) in `tests/test_exit_vocabulary_boundary.py`, the `OUT_OF_RANGE_DECLARATION_ALLOWLIST` reasons for `"oc runipd"` and `"agy runipd"` describe exits `0-4` per spec `25kzda` Section 5.6, and a test in `ExitVocabularyBoundaryTests` drives each driver's `main` on a corrupt `state.json` and asserts the OBSERVED exit code is a member of `command_surface.get_declaration(<command>).exit_contract` (ties the declaration to behavior; no literal-tuple pin and no class-identity pin, P16).
  - Execution state: pending

- [ ] E-05 Run `aw specs check`, the targeted test modules, the full test suite `python3 -m pytest`, and `aw sanitize --agent`.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: `AW_NO_REEXEC=1 python3 -m agent_workflows specs check .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, `python3 -m pytest tests/test_fixfirst_end_to_end.py tests/test_run_exit_aggregate.py tests/test_exit_vocabulary_boundary.py tests/test_runwire_verifier_authority.py`, bare `python3 -m pytest`, and `AW_NO_REEXEC=1 python3 -m agent_workflows sanitize --agent` all exit 0 with zero failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- **Settled ledger-substrate boundary (`rdjka2` OQ-01 Option (b), `utb2qr`, `runwire` fence)**: On 2026-10-08, the maintainer resolved `rdjka2` OQ-01 (`.aw/records/plans/executed/20261002-runledger-01-rdjka2-decide-whether-a-driver-run-writes-a-hash-chained-ledger-and.ipd.md` and `.aw/records/research/20261007-runledger-00-utb2qr-driver-run-ledger-decision.findings.md`) as **Option (b)**: driver runs (`aw oc run` / `aw agy run`) record their durable run state in `state.json` and `events.jsonl` and do NOT write `ledger.jsonl`, while `ledger.jsonl`, `RunLedgerStore`, `verify_chain`, `run_engine.py`, and `run_recovery.py` are scoped to the discrete `aw run` / `aw runs` workflow execution path. `tests/test_runwire_verifier_authority.py::test_set_level_checks` (`def test_set_level_checks() -> None:` at line 657) enforces an explicit architectural fence forbidding `runner_shared.py`, `oc_runipd.py`, and `agy_runipd.py` from importing `run_engine` or `run_recovery`.
- **Sibling pending plans on spec `25kzda`**:
  - Sibling plan `9epp40` (`.aw/records/plans/pending/20261014-runledger-04-9epp40-amend-spec-25kzda-1-2-step-8-and-5-1-to-scope-the-hash-chain.ipd.md`, from backlog `66ls4r`) amends spec `25kzda` Section 1.2 step 8 and Section 5.1 to scope `ledger.jsonl` to discrete `aw run` / `aw runs` invocations and document `state.json` / `events.jsonl` for driver runs, leaving Sections 5.5 and 5.6 untouched.
  - Sibling plan `6g08rp` (`.aw/records/plans/pending/20261014-w5opbr-01-6g08rp-replace-stale-and-non-resolving-owner-plan-ids-in-spec-25kzd.ipd.md`, from backlog `w5opbr`) updates the Set `fixfirst` and `verifier transport failure` rows in Section 5.5 and adds `test_e05_spec_5_5_table_owner_ids_resolve` asserting on the backticked 6-character IDs in the Section 5.5 table's `Notes` column. To keep `jmogmv` and `6g08rp` conflict-free regardless of execution order, `jmogmv` updates only the `| corrupt run ledger only |` row and group (c) bullet in Section 5.5 (plus the `| 4 |` row in Section 5.6) in place without adding any new backticked 6-character ID to the Section 5.5 `Notes` cell, and preserves all line numbers above `## Workflow history` so `spec_citations.new_stale_anchors` remains empty.
- **Cross-driver exception subclass pattern**: Shared exceptions raised in `agent_workflows/runner_shared.py` (`EmptyStatusSelection`, `ToolIdentityError`, `StallTimeout`, `HostSpawnError`) subclass `DriverError`, are re-exported in both `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` via `from agent_workflows.runner_shared import X as X`, and have their dedicated `except` clause placed BEFORE the generic `except DriverError` clause in `run_queue` and `main`.
- **Section 4.2 byte-for-byte transcription lock**: `tests/test_run_finding_abort_partition.py` and `tests/test_run_finding_spec_transcription.py` compare `run_evidence.RUN_FINDING_CODES` against the Section 4.2 table in spec `25kzda` byte for byte; Section 4.2 must not be modified.

## Findings

| # | Location / symbol | Finding | Impact |
|---|---|---|---|
| F-01 | `agent_workflows/runner_shared.py` (`load_json`, `load_state`, `run_exit_code`) | `load_state(run_dir)` delegates directly to `load_json(run_dir / "state.json")`, which raises a generic `DriverError(f"Invalid JSON in {path}: {exc}")` on `json.JSONDecodeError` and performs no structural check that the decoded JSON root is a `dict` or that `"queue"` (when present) is a `list`. In addition, `run_exit_code(queue, *, stopped)` accepts no `run_wide_abort_class` parameter and never passes `run_wide_abort_class="Corrupt run ledger"` to `run_evidence.aggregate_run_exit`. | `run_evidence.aggregate_run_exit`'s `AGGREGATE_ABORT_RUN` (exit code `4`) branch is unreachable from `runner_shared.run_exit_code`, and corrupt `state.json` cannot be distinguished from a generic usage/refusal `DriverError` (exit `2`) or an unhandled `AttributeError`/`TypeError`. |
| F-02 | `agent_workflows/oc_runipd.py` (`run_queue`, `main`) and `agent_workflows/agy_runipd.py` (`run_queue`, `main`) | In `main` on both drivers (`oc_runipd.py` `except DriverError as exc:` at line 5764, `agy_runipd.py` `except DriverError as exc:` at line 4457), a `DriverError` from `load_state(run_dir)` on `resume` (or `status`/`report`/`start`) exits `2` instead of `4`. Corrected at review: `run_queue`'s per-item `try` wraps only `execute_item(...)`, and no `load_state` call is reachable inside it, so a mid-run corrupt `state.json` already propagates out of `run_queue` (probe: both hosts raised after 1 turn). A structurally corrupt `state.json` (`{"queue": "x"}`) instead surfaces as `AttributeError`, which `main` reports as `unexpected failure` and re-raises. Under `--agent`, `main` already emits an `aw.agent/v1` refusal record with `exit: 2` (probe), and that schema cannot carry `4`. | Measured in `iksylm` E-04(a) / F-04 (`tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::_run_corrupt_state`): corrupting `state.json` before `resume` exits `2` rather than spec `25kzda` Section 5.6's exit code `4`. |
| F-03 | `agent_workflows/command_surface.py` (`oc runipd`, `agy runipd`), `docs/cli-output-contract.md` (Section 3.1), and `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (`### 5.5 Retry policy`, `### 5.6 Reporting`) | `command_surface.py` and `docs/cli-output-contract.md` Section 3.1 declare `exit_contract=(0, 1, 2, 3)` for `oc runipd` and `agy runipd`, spec `25kzda` Section 5.5 (`| corrupt run ledger only |`) describes only `ledger.jsonl` hash/sequence/reference corruption without mentioning driver runs' `state.json` validation (`rdjka2` OQ-01 Option (b), `utb2qr`), and Section 5.6 (`| 4 | Corrupt run ledger ... |`) still documents the pre-fix state where neither driver returns `4`. | Once driver runs return `4` on corrupt `state.json`, `command_surface.py`, `docs/cli-output-contract.md`, and spec `25kzda` Sections 5.5 and 5.6 would disagree with runtime behavior unless updated in lockstep. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/runner_shared.py` (E-01)**:
   - Define `CORRUPT_RUN_LEDGER_ABORT_CLASS: str = "Corrupt run ledger"` and `class CorruptRunStateError(DriverError):` alongside `EmptyStatusSelection`.
   - Update `load_state(run_dir: Path) -> dict[str, Any]` so that:
     - missing `run_dir / "state.json"` (`FileNotFoundError`) still raises plain `DriverError(f"Required file not found: {path}")`;
     - invalid JSON or UTF-8 decoding error in `run_dir / "state.json"` (`json.JSONDecodeError`, `UnicodeDecodeError`) raises `CorruptRunStateError(f"Invalid JSON in {path}: {exc}") from exc`;
     - a decoded value where `not isinstance(data, dict)` or `("queue" in data and not isinstance(data["queue"], list))` raises `CorruptRunStateError(f"Corrupt run state in {path}: expected a JSON object with a list 'queue'")`.
   - Update `run_exit_code(queue: Iterable[Mapping[str, Any]], *, stopped: bool, run_wide_abort_class: str | None = None) -> int` to pass `run_wide_abort_class=run_wide_abort_class` through to `run_evidence.aggregate_run_exit`.
2. **`agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, and `agent_workflows/command_surface.py` (E-02)**:
   - Re-export `CorruptRunStateError as CorruptRunStateError` and `CORRUPT_RUN_LEDGER_ABORT_CLASS as CORRUPT_RUN_LEDGER_ABORT_CLASS` in both `oc_runipd.py` and `agy_runipd.py` (and add both names to `oc_runipd.__all__`).
   - No `run_queue` handler change (mid-run corruption already propagates to `main`; see F-02).
   - Agent-surface behavior per OQ-01.
   - In `main` in both `oc_runipd.py` and `agy_runipd.py`, add `except CorruptRunStateError as exc:` before `except DriverError as exc:` to print `f"runipd: {exc}"` / `f"runagy: {exc}"` to `sys.stderr` and return `runner_shared.run_exit_code((), stopped=False, run_wide_abort_class=runner_shared.CORRUPT_RUN_LEDGER_ABORT_CLASS)` (`4`).
   - In `agent_workflows/command_surface.py`, widen `exit_contract` on `"oc runipd"` and `"agy runipd"` to `(0, 1, 2, 3, 4)`.
3. **`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` and `docs/cli-output-contract.md` (E-03)**:
   - Update Section 5.5 group (c) and the `| corrupt run ledger only |` row and Section 5.6's `| 4 | Corrupt run ledger ... |` row in place (preserving line offsets above `## Workflow history`) and record a `## Workflow history` note via `aw specs note`.
   - Update `docs/cli-output-contract.md` Section 3.1 to list `0, 1, 2, 3, 4` for `oc runipd` and `agy runipd`.
4. **`tests/test_fixfirst_end_to_end.py`, `tests/test_run_exit_aggregate.py`, and `tests/test_exit_vocabulary_boundary.py` (E-04)**:
   - Update `TestFixFirstEndToEnd._run_corrupt_state` in `tests/test_fixfirst_end_to_end.py` to assert exit `4` on unparseable `state.json`, structurally corrupt `state.json`, and mid-run `state.json` corruption (and exit `2` on missing `state.json`), plus the OQ-01 agent-surface case.
   - Add unit tests in `tests/test_run_exit_aggregate.py` for `run_exit_code(..., run_wide_abort_class=CORRUPT_RUN_LEDGER_ABORT_CLASS)` returning `4` and for `load_state`'s three corruption shapes.
   - Update the `OUT_OF_RANGE_DECLARATION_ALLOWLIST` reasons in `tests/test_exit_vocabulary_boundary.py` and add the observed-exit-in-declared-contract test.
5. **Validation run (E-05)**:
   - Run `aw specs check`, the targeted pytest modules, bare `python3 -m pytest`, and `aw sanitize --agent`.

## Deferred / out of scope (with reason)

- Amending spec `25kzda` Section 1.2 step 8 and Section 5.1 to scope `ledger.jsonl` to discrete `aw run` / `aw runs` invocations: owned by sibling pending IPD `9epp40` (from backlog item `66ls4r`).
  - Carrier: 9epp40
- Updating stale Set `fixfirst` and `verifier transport failure` owner plan IDs in spec `25kzda` Section 5.5: owned by sibling pending IPD `6g08rp` (from backlog item `w5opbr`).
  - Carrier: 6g08rp

## Scope check

- Over-scope: none.
- Under-scope: none; both the driver runtime exit `4` behavior on corrupt `state.json` (`runner_shared.py`, `oc_runipd.py`, `agy_runipd.py`, `command_surface.py`) and the Section 5.5 / 5.6 spec and CLI contract alignment (`25kzda`, `docs/cli-output-contract.md`, and tests) required to close backlog item `jt7ns3` are covered in E-01 through E-05.

## Required tests / validation

- `AW_NO_REEXEC=1 python3 -m agent_workflows specs check .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`
- `python3 -m pytest tests/test_fixfirst_end_to_end.py tests/test_run_exit_aggregate.py tests/test_exit_vocabulary_boundary.py tests/test_runwire_verifier_authority.py`
- `python3 -m pytest`
- `AW_NO_REEXEC=1 python3 -m agent_workflows sanitize --agent`

## Spec / documentation sync

- `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (`### 5.5 Retry policy` group (c) and row `corrupt run ledger only`, `### 5.6 Reporting` exit code `4` row, and `## Workflow history`) and `docs/cli-output-contract.md` (Section 3.1) are updated in E-03.

## Open questions

The ledger-substrate question (`ledger.jsonl` vs `state.json`/`events.jsonl` on driver runs) was settled by the maintainer on 2026-10-08 as Option (b) in `rdjka2` OQ-01 (`utb2qr`), and exit code `4` for run-wide abort (`Corrupt run ledger`) is already specified in spec `25kzda` Section 5.6 and implemented in `run_evidence.aggregate_run_exit`. One public-contract question remains:

### OQ-01: What does `--agent` mode return on a corrupt `state.json`?

- Blocking: yes
- Finding: PR-001
- Status: open
- Owner: maintainer
- Context: under `--agent`, `oc_runipd.main` / `agy_runipd.main` today emit an `aw.agent/v1` refusal record with `exit: 2` (measured at review). `docs/cli-output-contract.md` Section 3 binds every `aw.agent/v1` record to exits `{0, 1, 2}` with exit parity (`agent_schema.render_jsonl_record` raises on `exit: 4`, measured), while the same section says a condition returns the same code on every audience surface. Exit `4` on the human surface and exit parity on the agent surface cannot both hold.
- Options: (a) agent mode keeps exit `2` with outcome `cannot-run` and a summary naming the corrupt run state, and the doc records this as a deliberate audience divergence; (b) agent mode emits no record and exits `4`, and the doc says run-family `--agent` surfaces are exempt from parity for exit `4`; (c) widen the `aw.agent/v1` exit vocabulary for the run family (a schema change out of this plan's scope).
- Recommendation: (a). It keeps every agent consumer's schema valid and changes no agent-visible behavior.
- Resolution or deferral rationale: pending maintainer decision; a public CLI contract decision the repository cannot answer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of `git diff -- agent_workflows/runner_shared.py` showing `CORRUPT_RUN_LEDGER_ABORT_CLASS`, `CorruptRunStateError(DriverError)`, `load_state` raising `CorruptRunStateError` on invalid JSON or corrupt root/queue structure while preserving plain `DriverError` on `FileNotFoundError`, and `run_exit_code` forwarding `run_wide_abort_class` to `run_evidence.aggregate_run_exit`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted output of `git diff -- agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py agent_workflows/command_surface.py` showing `CorruptRunStateError` and `CORRUPT_RUN_LEDGER_ABORT_CLASS` re-exported in both drivers, no new `run_queue` handler, the updated `command_surface.py` comment, the OQ-01 agent-surface branch, `except CorruptRunStateError as exc:` returning `runner_shared.run_exit_code((), stopped=False, run_wide_abort_class=runner_shared.CORRUPT_RUN_LEDGER_ABORT_CLASS)` (`4`) in `main`, and `exit_contract=(0, 1, 2, 3, 4)` on `"oc runipd"` and `"agy runipd"`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted output of `git diff -- .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md docs/cli-output-contract.md` showing the in-place updates to Section 5.5 (`corrupt run ledger only`) and Section 5.6 (exit code `4`), the appended `## Workflow history` note on spec `25kzda`, and the updated `0, 1, 2, 3, 4` exit range in `docs/cli-output-contract.md` Section 3.1.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted pytest runner output from `python3 -m pytest tests/test_fixfirst_end_to_end.py tests/test_run_exit_aggregate.py tests/test_exit_vocabulary_boundary.py -o addopts="" -v` showing all targeted tests passing (`rc == 4` on unparseable, structurally corrupt, and mid-run corrupt `state.json` across both drivers with no further session dispatched, `rc == 2` on missing `state.json`, the OQ-01 agent-surface case, `run_exit_code` returning `4` for `CORRUPT_RUN_LEDGER_ABORT_CLASS`, and the observed `4` being a member of each declared `exit_contract`); plus a pasted sensitivity run in which `main`'s `except CorruptRunStateError` handler is temporarily removed and the corrupt-state tests FAIL with `rc == 2`, followed by a pasted empty `git diff` of that temporary change after revert.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted command output from `AW_NO_REEXEC=1 python3 -m agent_workflows specs check .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, `python3 -m pytest tests/test_fixfirst_end_to_end.py tests/test_run_exit_aggregate.py tests/test_exit_vocabulary_boundary.py tests/test_runwire_verifier_authority.py`, bare `python3 -m pytest`, and `AW_NO_REEXEC=1 python3 -m agent_workflows sanitize --agent` showing all commands exiting 0 with zero failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after OQ-01 is answered and the plan is approved (`aw ipd set approved jmogmv --by-human`). Begin with `aw ipd begin jmogmv`, then execute `E-01` through `E-05` in dependency order.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. The spec `25kzda` edits are declared here because this plan amends an approved spec (Sections 5.5 and 5.6 only; Section 4.2 is transcription-locked and must not change). STOP only for a genuinely unsafe condition: a concurrent edit to spec `25kzda` Sections 5.5/5.6 (for example by sibling `6g08rp` or `9epp40`) that cannot be safely combined.

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never mark a `V-*` `pass` without concrete observed output. Run the full suite bare as `python3 -m pytest`.

Commits: commit only the Scope-Paths files you changed through `aw commit jmogmv -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: under `aw oc run` / `aw agy run` the RUNNER performs finalize after its merge-and-revalidate gate, so do not run it yourself. When executing by hand, once every `E-*` is `performed`, every `V-*` is `pass`, and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize jmogmv`. Never hand-roll a `git mv`.
