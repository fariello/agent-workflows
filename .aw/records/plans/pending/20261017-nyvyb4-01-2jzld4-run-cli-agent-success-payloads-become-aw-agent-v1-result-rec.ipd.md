# IPD: run_cli --agent success payloads become aw.agent/v1 result records and honor --fields

- Date: 2026-10-17
- Kind: child
- Concern: Every `aw run` / `aw runs` ledger leaf (`runs status|show|next|resume|evidence|verify-ledger|decisions|questions`, `run start|record|cancel|finalize|verify`) prints its SUCCESS answer under `--agent` as a bare dict through `run_cli._emit_machine`, not an `aw.agent/v1` record, so `agent_schema.validate_agent_record` reports three violations against it and the shared `--fields` projection is ignored (measured 2026-10-17 in this lane: `runs status <id> --agent --fields cmd` printed the full snapshot dict, exit 1; `runs show <id> --agent` fails validation with `Invalid schema`, `Invalid kind`, `Field 'cmd' must be a non-empty string`).
- Scope: Under `--agent` only, when a ledger leaf's answer exits 0 or 1, emit it as one validated `aw.agent/v1` `kind: "result"` record that keeps every existing top-level payload key (additive envelope: `schema`, `kind`, `cmd`, `exit`, `outcome`, `verified`, `complete`), is home-path-redacted and ANSI-free, and honors `--fields`. Leave `--json`, human output, every refusal payload (owned by `2t033b` for exit 2 and `p7bvku` for 1/3/4/5/6/7), and every success-shaped payload that exits 3 unchanged. Retire the now-false `sanctioned_raw` conformance exemptions, strengthen the live ledger sweep to validate the records, and update the docs, comments and CHANGELOG that describe the bare shape.
- Scope-Paths: agent_workflows/run_cli.py, agent_workflows/command_surface.py, tests/test_run_cli_agent_success_records.py, tests/test_live_conformance_sweep.py, tests/conformance_matrix.py, docs/cli-output-contract.md, CHANGELOG.md
- Item-Dependencies: executed:2t033b
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: nyvyb4
- Set: nyvyb4
- Order: 1
- Highest E allocated: 08
- Author: opencode
- Id: 2jzld4

## Workflow history
- 2026-10-17 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 fixed. Readiness go-pending-approval. Review record .aw/records/reviews/20261017-nyvyb4-01-2jzld4-run-cli-agent-success-payloads-become-aw-agent-v1-result-rec.review.md

- 2026-10-17 to-review (aw set): authored from backlog nyvyb4; review-ready
- 2026-10-17 draft (opencode): created.

## Goal

Make every `aw run` / `aw runs` ledger leaf's `--agent` success answer (exit 0 or 1) a schema-valid `aw.agent/v1` `kind: "result"` record that honors `--fields`, as every other `--agent` leaf already is, without breaking consumers that read the existing payload keys and without touching the run family's wider exit vocabulary (`docs/cli-output-contract.md` Section 3.1).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: emit the record

- [ ] E-01 In `agent_workflows/run_cli.py`, add a helper `_emit_result(args, payload, exit_code)` beside `_emit_machine`. When `--agent` (or `as_agent`) is active AND `exit_code in (EXIT_OK, EXIT_INCOMPLETE)` AND `payload` is a dict, it builds `rec = {**payload, "schema": agent_schema.SCHEMA_VERSION, "kind": "result", "cmd": _agent_cmd(args), "exit": exit_code, "outcome": "ok" if exit_code == EXIT_OK else "findings", "verified": True, "complete": True}` (envelope keys placed last so they always win over a same-named payload key) and hands it to `_emit_agent_record(args, rec)`, the ONE `--agent` record emitter plan `2t033b` E-01 adds for exactly this reuse (it applies `_redact_output`, recursive `agent_schema.redact_home_paths` plus ANSI stripping on every string value at any depth, the `--fields` projection via `agent_schema.filter_record_fields` with comma-string normalization, and `agent_schema.render_guarded_jsonl_record`). Do NOT re-implement that sequence here (P8, one emitter). Every other case (`--json`, any other exit code, a non-dict payload) calls `_emit_machine(args, payload)` unchanged. `_agent_cmd(args)` and `_emit_agent_record(args, rec)` are both added by `2t033b` E-01, which this plan depends on (`executed:2t033b`); if either is absent when this plan executes, add it exactly as `2t033b` E-01 specifies.
  - Depends on: none
  - Expected outcome: `_emit_result` exists and calls `_emit_agent_record` (no second copy of the redact / `--fields` / guarded-render sequence in `run_cli.py`); no call site changed yet; `python3 -m pytest tests/test_run_cli_error_payload_keys.py tests/test_run_init.py -o addopts="" -q` still passes.
  - Execution state: pending

- [ ] E-02 Route the READ leaves' success emits through `_emit_result`, computing the exit code BEFORE emitting: `_run_show` (rc `0 if evaluation.is_complete else 1`), `_run_evidence` (rc `1 if any_invalid else 0`), `_run_verify_ledger` clean-chain branch (rc `0` when `evidence_val.ok and evaluation.is_complete`, else `1`; the broken-chain exit-5 payload is untouched), and `_emit_projection` success branch (rc `exit_code`, already computed). Each function's return value is unchanged.
  - Depends on: E-01
  - Expected outcome: `runs show|evidence|verify-ledger|decisions|questions <id> --agent` each print one line that `validate_agent_record` accepts, with `exit` equal to the process exit code.
  - Execution state: pending

- [ ] E-03 Route the STATE leaves' success emits through `_emit_result`: `_run_status` (rc computed from `snapshot.state` before the emit using the existing tail logic: `EXIT_OK` for `STATE_COMPLETE`, `EXIT_BLOCKED` for `STATE_CANCELLED`, else `EXIT_INCOMPLETE`), `_run_next` (rc `EXIT_OK` when terminal or `runnable_ids` is non-empty, else `EXIT_BLOCKED`), `_run_resume` success branch (rc `EXIT_OK`). The exit-3 cases fall through `_emit_result` to the unchanged bare `_emit_machine` path, because `aw.agent/v1` caps `exit` at (0, 1, 2).
  - Depends on: E-01
  - Expected outcome: `runs status` on a pending run prints a record with `exit: 1`, `outcome: "findings"`; `runs next` with nothing runnable still prints the bare `{"run_id",...,"runnable_steps":[]}` dict and exits 3.
  - Execution state: pending

- [ ] E-04 Route the WRITER leaves' success emits through `_emit_result`: `_run_start` (rc `EXIT_OK`), `_run_record` (rc `EXIT_BLOCKED` when `outcome in (STATE_FAILED, STATE_BLOCKED)` else `EXIT_OK`, computed before the emit), `_run_cancel` (rc `EXIT_OK`), `_run_finalize` success tail (rc `EXIT_OK`; its exit-1 and exit-4 refusal payloads are untouched), `_run_verify` (rc `EXIT_BLOCKED` when `result in ("partial", "failed", "not_verifiable")` else `EXIT_OK`, computed before the emit). `run_viewer` still calls `run_cli._snapshot_payload` unchanged, so that function's return value is not altered.
  - Depends on: E-01
  - Expected outcome: `run start|record|cancel|finalize|verify ... --agent` on their exit-0 paths each print one valid `kind: "result"` record whose `cmd` is `"run <leaf>"`; `run record --state failed --agent` still prints the bare dict and exits 3.
  - Execution state: pending

- [ ] E-05 Update stale prose that describes the bare success shape: the `run_cli` module docstring `Contract:` list (add a bullet stating `--agent` exit-0/1 answers are `aw.agent/v1` result records that keep the legacy payload keys, while `--json`, exit-3 answers and non-2 refusals stay bare), the `_emit_projection` docstring ("the same bare-dict family as the other `aw runs` leaves"), and the `_emit_error` docstring paragraph as rewritten by `2t033b` E-03 so it no longer implies success payloads are bare; in `agent_workflows/command_surface.py`, the `runs next` and `runs resume` declaration comments' closing sentence (as left by `2t033b` E-03) so it says the contract is not capped at (0, 1, 2) because only exit-0/1 answers and exit-2 refusals are records while codes 3, 5 and 7 stay bare. RECONCILE WITH `u1ujw9`: plan `u1ujw9` (Set `p7bvku`, also `executed:2t033b`) rewrites the same `_emit_error` docstring paragraph and the same two `command_surface` sentences to say exit-1 REFUSALS are `kind: "result"` / `outcome: "fail"` records. Read the text as it stands at execution: if `u1ujw9` has landed, keep its exit-1-refusal statement and ADD the success-answer statement rather than replacing it; if it has not, say nothing about exit-1 refusals beyond "owned by backlog `p7bvku`". The final text must be true of the code at this plan's commit. No `CommandDeclaration(...)` field value changes.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: `git diff agent_workflows/command_surface.py` touches comment lines only; `grep -n "bare-dict family" agent_workflows/run_cli.py` returns nothing.
  - Execution state: pending

### Task group 2: tests

- [ ] E-06 Create `tests/test_run_cli_agent_success_records.py` (behavioral, subprocess via `tests.conformance_matrix.run_cli` against a `seed_ledger_fixture(tmp_path)` repo, P16). (a) A table-driven test over the read leaves (`runs show|status|next|resume|evidence|verify-ledger|decisions|questions`, with `--workflow <root>/wf.json` for `next|resume|status`, as `conformance_matrix.live_leaf_argv` builds) asserting exactly one stdout line, `validate_agent_record(rec) == []`, `rec["kind"] == "result"`, `rec["cmd"] == leaf`, `rec["exit"] == returncode`, `rec["outcome"] == ("ok" if returncode == 0 else "findings")`, and that the leaf's legacy key survives (`run_id` for show/status/next/resume, `ledger` for evidence, `chain_clean` for verify-ledger, `content` for decisions/questions). (b) The same leaves with `--agent --fields cmd` assert `set(rec) <= agent_schema._PRESERVED_FIELDS | {"cmd"}` and a valid record. (c) A writer sequence on a fresh fixture (`run start --step S-01`, `run record --step S-01 --state performed`, `run verify --requirement R-01 --result satisfied`, `run finalize`, then `run cancel` on a second fresh fixture) asserting each exit-0 answer is a valid record with `cmd == "run <leaf>"` and keeps `run_id`. (d) Unchanged shapes: `--json` on `runs status` parses to a dict with no `schema` key; `runs next --agent` after `run start --step S-01` exits 3 and prints a dict with no `schema` key; `run record --state failed --agent` exits 3 with no `schema` key. (e) Redaction: append a `tool_event` whose `cwd` is a POSIX home-style path assembled at test time as `"/".join(["", "home", "someuser", "work"])` (so this source file itself carries no literal home path) to the fixture ledger with `run_ledger_store.RunLedgerStore(...).append(...)` (record shape copied from `tests/test_run_evidence_completion._sample_run_records`), run `runs evidence <id> --agent`, and assert the record validates, the substring `someuser` is absent from stdout, and `"~/work"` is present.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: `python3 -m pytest tests/test_run_cli_agent_success_records.py -o addopts="" -v` passes; rows (a) to (c) and (e) would fail against the pre-change code, whose payloads lack `schema`/`kind`/`cmd`.
  - Execution state: pending

- [ ] E-07 Retire the false exemptions and strengthen the live sweep. In `tests/conformance_matrix.py`, delete the eight `EXEMPTION_REGISTRY` entries for `runs decisions|evidence|next|questions|resume|show|status|verify-ledger` (their stated reason, "Emits bare JSON dicts ... rather than aw.agent/v1 records", is false after E-02/E-03), update the `# sanctioned_raw (13):` count comment to `(5)`, and remove the clause "emits bare JSON dicts under docs/cli-output-contract.md Section 3.1;" from the `run cancel|finalize|record|start` `MUTATION_EXEMPTION_REGISTRY` reasons (their `arg_fixture_needed` kind and the rest of the reason stay). In `tests/test_live_conformance_sweep.py`, in `test_live_ledger_read_leaves_non_vacuous` assert `agent_schema.validate_agent_record(<last --agent line>) == []` and `rec["exit"] == res_agent.returncode` for every leaf, and in `test_live_ledger_mutation_leaves_conformance` assert the same for the agent mode of the `run start`, `run record` and `run cancel` steps ONLY. The sweep's `run finalize` step exits 1 through the incomplete-run REFUSAL in `run_cli._run_finalize` ("Completion predicate gate" branch, a bare `_emit_machine` payload), which this plan does not convert (that class is plan `u1ujw9`, backlog `p7bvku`); leave that step's existing parse-as-dict assertion unchanged, with a one-line comment naming `u1ujw9`, and assert neither record validity nor bareness for it, so the test stays correct whichever of the two plans lands first.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: `python3 -m pytest tests/test_live_conformance_sweep.py tests/test_agent_surface_conformance.py tests/test_shared_flag_honored.py tests/test_conformance_matrix_structure.py -o addopts="" -n auto` passes, with the eight `runs` leaves now present in the `test_agent_surface_conformance`, `test_json_flag_honored_read` and `test_fields_flag_honored_read` parametrization (these invoke the leaves without a target, so they exercise the parser's `kind: "error"` refusal, measured valid at review; non-vacuous success coverage is the live ledger sweep and E-06).
  - Execution state: pending

### Task group 3: documentation

- [ ] E-08 In `docs/cli-output-contract.md`: Section 3's "Verbs emitting bare JSON or non-agent payloads" bullet (stop naming `aw runs` as an example of a bare-payload verb for success answers), and Section 3.1's opening paragraph ("These commands emit bare JSON dictionaries or execution manifests rather than `aw.agent/v1` records") and its `aw run init` sentence, so they state: under `--agent`, every `aw run`/`aw runs` ledger leaf answer that exits 0 or 1 is an `aw.agent/v1` `kind: "result"` record (`outcome` `ok` for 0, `findings` for 1) that keeps the leaf's existing payload keys and honors `--fields`; answers and refusals exiting 3 to 7 and every `--json` payload keep the bare shape. The same paragraphs are also edited by plan `u1ujw9` (exit-1 refusals become `outcome: "fail"` records); apply the same reconcile rule as E-05: read the text as it stands, keep any exit-1-refusal statement `u1ujw9` wrote, and otherwise describe exit-1 refusals as still bare pending backlog `p7bvku`. Add one `Changed:` line to the top pending section of `CHANGELOG.md` describing the user-visible change (additive envelope, legacy keys kept), with no em or en dashes.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: `git diff docs/cli-output-contract.md CHANGELOG.md` shows only those edits; `python3 -m pytest tests/test_cli_agent_protocol_doc.py tests/test_docs_check.py -o addopts=""` passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_schema.validate_agent_record` caps `exit` at (0, 1, 2) for result/summary/error records, rejects a positive outcome (`clean`/`ok`/`conforms`) on exit 1, and rejects any string value carrying an ANSI escape or a home path. So only exit-0/1 answers can become records without a protocol decision; the run-family codes 3 to 7 are the Section 3.1 vocabulary that spec `25kzda` Section 5.6 row 4 records as deliberately not renumbered (backlog `p7bvku` owns that decision).
- Section 3 of `docs/cli-output-contract.md` defines exit 1 as "Domain Findings / Negative Result", which is why `findings` (not a positive outcome) is the exit-1 outcome, including for `runs decisions|questions` whose declared contract maps "nothing recorded" to 1 (`command_surface` "Exit 0 found / 1 none / 2 missing").
- Precedent for the record shape and `--fields` handling inside this module: `run_cli._run_init` (plan `tgfxin`) builds `kind: "result"`, `outcome: "ok"`, calls `agent_schema.filter_record_fields`, then `agent_schema.render_guarded_jsonl_record`.
- `agent_schema.render_guarded_jsonl_record` is strict under pytest (`PYTEST_CURRENT_TEST`) and in production substitutes a `kind: "error"` record for an invalid one; an unredacted home path in a success payload would therefore turn a success into an error in production, which is why E-01 redacts every string value, not only path-named keys.
- `agent_schema.redact_home_paths` handles one string; `agent_schema.normalize_repo_path` handles a whole path value. Ledger records carry user-written paths (`tool_event.cwd`, `evidence_envelope.worktree`) that `_run_evidence` copies into its payload, and `runs decisions|questions` copy file text into `content`.
- `agent_schema.filter_record_fields` keeps `_PRESERVED_FIELDS` (envelope plus `applied`/`total`/`emitted`/`omitted`/`next`); legacy keys such as `run_id` are not preserved, so `--fields cmd` drops them, matching every other `--agent` leaf.
- Plan `2t033b` E-01 factors the `--agent` redact / `--fields` / guarded-render sequence into `run_cli._emit_agent_record(args, rec)` explicitly so this plan and `u1ujw9` reuse it; E-01 here calls it rather than copying the sequence.
- The `run_cli._run_finalize` incomplete-run payload (exit 1) is a REFUSAL (`ok: false`, `error`), not a success answer; it is plan `u1ujw9`'s, so `run finalize` in the live mutation sweep stays out of this plan's record assertions (E-07).
- `run_viewer` reuses `run_cli._snapshot_payload` for its own output, so the wrapping happens at emit time, not in that function.
- `tests/conformance_matrix.EXEMPTION_REGISTRY` is documented as "A CEILING, NOT A CONVENIENCE"; removing entries whose reason became false is the intended direction. Leaves removed from it join `tests/test_agent_surface_conformance.UNIVERSE` and `tests/test_shared_flag_honored._fields_read_params`, which invoke them without a target and so exercise the parser's `kind: "error"` refusal (measured: `runs show --agent --fields cmd` already prints a valid error record, exit 2); the non-vacuous success coverage is the live ledger sweep plus the new test file.
- Tests: behavioral only (P16). None of the touched test files are core-tier, so they are run explicitly.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | Success payloads under `--agent` are bare dicts and fail validation. | Measured 2026-10-17 in this lane against a scratch `aw run init` ledger: `runs show <id> --agent` piped into `validate_agent_record` printed `["Invalid schema: expected 'aw.agent/v1', got 'None'", "Invalid kind: 'None' must be one of (...)", "Field 'cmd' must be a non-empty string"]`. |
| F-2 | `--fields` is ignored. | Same session: `runs status <id> --workflow wf.json --agent --fields cmd` printed the full `{"approvals":{},...,"workflow_id":"wf"}` snapshot, exit 1. |
| F-3 | All thirteen leaves reach `_emit_machine` with a bare dict on success. | Same session, the full writer/reader sequence (`run start`, `run record`, `run verify`, `runs next`, `runs resume`, `run finalize`, `runs status`, `runs show`, `runs verify-ledger`, `runs evidence`) each printed a dict with no `schema` key; `runs next` exited 3 with `runnable_steps: []`. |
| F-4 | Four success-shaped answers exit 3 and so cannot be records today. | `run_cli._run_next` (`return EXIT_OK if runnable_ids else EXIT_BLOCKED`), `_run_status` (`STATE_CANCELLED` -> `EXIT_BLOCKED`), `_run_record` (failed/blocked outcome -> `EXIT_BLOCKED`), `_run_verify` (partial/failed/not_verifiable -> `EXIT_BLOCKED`). |
| F-5 | Consumers key off legacy payload keys, so the envelope must be additive. | `tests/test_live_conformance_sweep.test_live_ledger_read_leaves_non_vacuous` reads `run_id`, `ledger`, `chain_clean`, `empty`, `content` from the `--agent` line; `tests/test_run_recovery_cli` `MACHINE_READ_VERBS` reads `run_id`; `tests/test_runs_machine_output_paths.test_projection_machine_output_parses_empty` reads `ok`, `projection`, `exit_code`; `tests/test_run_evidence_completion.test_aw_run_show_agent_json_mode` reads `is_complete`. None assert an exact key set on a success payload (searched `set(payload) ==` / `assert payload ==` across `tests/test_run*.py`). |
| F-6 | The conformance registry states the bare shape as its reason. | `tests/conformance_matrix.EXEMPTION_REGISTRY` entries for the eight `runs` leaves: "Emits bare JSON dicts through run_cli._emit_machine ... rather than aw.agent/v1 records." |
| F-7 | Plan `2t033b` (backlog `jndec6`, `reviewed`) edits the same docstring, `command_surface` comments and doc paragraphs and adds the `_agent_cmd` helper and the shared `_emit_agent_record` emitter this plan reuses; plan `u1ujw9` (backlog `p7bvku`, `to-review`, also `executed:2t033b`) edits the same three prose surfaces for exit-1 refusals and hands success payloads to this item. | `.aw/records/plans/pending/20261017-jndec6-01-2t033b-run-cli-agent-error-payloads-become-aw-agent-v1-error-record.ipd.md` E-01, E-03, E-06 and its Step 0 note naming `2jzld4`; `.aw/records/plans/pending/20261017-p7bvku-01-u1ujw9-decide-the-aw-agent-v1-protocol-boundary-for-run-cli-wide-ex.ipd.md` E-03, E-05 and Deferred (`- Carrier: nyvyb4`). |

## Proposed changes (ordered, validatable)

1. E-01: add `_emit_result`, the single choke point that wraps an exit-0/1 `--agent` answer in a sanitized, projected `aw.agent/v1` result record.
2. E-02: route the read leaves through it.
3. E-03: route the state leaves through it, leaving exit-3 answers bare.
4. E-04: route the writer leaves through it, leaving exit-3 answers bare.
5. E-05: correct the stale docstrings and `command_surface` comments.
6. E-06: add `tests/test_run_cli_agent_success_records.py`.
7. E-07: retire the eight false `sanctioned_raw` exemptions, fix the four mutation reasons, and validate records in the live ledger sweep.
8. E-08: update `docs/cli-output-contract.md` Sections 3 and 3.1 and add a CHANGELOG line.

## Deferred / out of scope (with reason)

- Success-shaped answers that exit 3 (`runs next` with nothing runnable, `runs status` on a cancelled run, `run record` of a failed/blocked outcome, `run verify` of a partial/failed/not_verifiable result) stay bare: `aw.agent/v1` cannot carry exit 3 and the run-family codes are not to be renumbered (spec `25kzda` 5.6 row 4). This is the same constraint plan `u1ujw9` (backlog `p7bvku`) OQ-01 records for refusals; that plan explicitly hands every SUCCESS payload back to this item (`u1ujw9` Deferred, `- Carrier: nyvyb4`), so naming it as the carrier would be circular. The boundary is instead decided here: documented by E-08 and pinned by E-06 (d).
  - Carrier-Declined: not representable in aw.agent/v1 without renumbering (spec 25kzda 5.6 row 4) or breaking exit parity; documented by E-08 and pinned by E-06 (d)
- `--agent` refusal payloads (exit 2 and exits 1/3/4/5/6/7) are not touched here: exit 2 is plan `2t033b`, the rest are backlog `p7bvku`.
  - Carrier: p7bvku
- `--json` success payloads keep the bare shape: the shared `--fields` help defines it as "Comma-separated field projection for --agent output", the backlog item names `--agent`, and plan `2t033b` OQ-01 and plan `tgfxin` OQ-01 resolved the same question the same way.
  - Carrier-Declined: deliberate design; `--json` is the full structured representation and stays bare (OQ-01, resolved)
- `runs decisions|questions` with nothing recorded keep exit 1 and so carry `outcome: "findings"`, although `docs/cli-output-contract.md` Section 11.1 asks an empty standing query for `outcome: "clean"`, exit 0. Changing the exit code would change the declared contract (`command_surface` "Exit 0 found / 1 none / 2 missing", pinned by `tests/test_live_conformance_sweep.EXPECTED_READ_EXIT_CODES`), which this item does not ask for; exit parity then leaves `findings` as the only valid outcome (OQ-04).
  - Carrier-Declined: pre-existing declared exit contract; changing it is a behavior change outside this item, and exit parity forces findings for exit 1 (OQ-04)
- `runs verify-ledger` keeps `findings` as a list of finding objects although `aw.agent/v1` records conventionally use `findings` as a count: renaming it would break the additive-envelope guarantee for no stated need.
  - Carrier-Declined: backward compatibility of the existing key outweighs the naming convention, which the validator does not enforce (OQ-03, resolved)

## Scope check

- Over-scope: none. `run_cli.py` is the fix; `command_surface.py` (comments only) and `docs/cli-output-contract.md` describe the old shape; `tests/conformance_matrix.py` carries exemptions whose stated reason becomes false; `tests/test_live_conformance_sweep.py` is the live gate that should now prove validity; the new test file is the behavioral guard; `CHANGELOG.md` is the user-facing record.
- Under-scope: none known. Tests that read `--agent` success payloads and are expected to stay green unchanged because the legacy keys are retained (F-5): `tests/test_run_recovery_cli.py`, `tests/test_runs_machine_output_paths.py`, `tests/test_run_evidence_completion.py`, `tests/test_run_init.py`, `tests/test_records_root_accessor.py`. They are in the regression command below; if one fails, that is a scope finding to resolve at execution, not a reason to drop the legacy keys.

## Required tests / validation

- `python3 -m pytest tests/test_run_cli_agent_success_records.py -o addopts="" -v` passes (E-02, E-03, E-04, E-06).
- `python3 -m pytest tests/test_live_conformance_sweep.py tests/test_agent_surface_conformance.py tests/test_shared_flag_honored.py tests/test_conformance_matrix_structure.py tests/test_command_surface_declarations.py -o addopts="" -n auto` passes (E-07).
- `python3 -m pytest tests/test_run_recovery_cli.py tests/test_runs_machine_output_paths.py tests/test_run_evidence_completion.py tests/test_run_init.py tests/test_run_cli_error_payload_keys.py tests/test_run_cli_corruption_exit.py tests/test_run_cli_human_redaction.py tests/test_run_cli_declarations.py tests/test_exit_contract_conformance.py tests/test_run_viewer.py tests/test_records_root_accessor.py -o addopts="" -n auto` passes (regressions, E-01, E-05).
- `python3 -m pytest tests/test_cli_agent_protocol_doc.py tests/test_docs_check.py -o addopts="" -q` passes (E-08).
- Routine gate `python3 -m pytest` passes.
- `aw sanitize --agent` reports no new finding on the changed files.

## Spec / documentation sync

No `.spec.md` is edited: no exit code, flag table or `CommandDeclaration` field changes, so spec `25kzda` 5.6 is untouched; the change brings the run family's exit-0/1 `--agent` answers under the existing `aw.agent/v1` protocol that `docs/cli-output-contract.md` Section 4 already defines. `docs/cli-output-contract.md` Sections 3 and 3.1 are updated (E-08) because they currently describe the bare shape as the rule for the whole family.

## Open questions

### OQ-01: Should `--json` success payloads become records too?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. The backlog item names `--agent` and `--fields`; `--fields` is defined only for `--agent` output; plans `tgfxin` and `2t033b` resolved the same question the same way. See Deferred.

### OQ-02: Nest the existing payload under a sub-key, or keep its keys at the top level?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Top level (additive envelope). `validate_agent_record` accepts extra keys, and every existing consumer (F-5) reads top-level keys; nesting would turn a conformance fix into a breaking change. No current payload key collides with an envelope key (checked against `_snapshot_payload`, `_run_show`, `_run_evidence`, `_run_verify_ledger`, `_emit_projection`, `_run_next`, `_run_resume` payloads), and E-01 makes envelope keys win if one ever does.

### OQ-03: Rename `runs verify-ledger`'s list-valued `findings`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. The validator does not type `findings` on result records, and renaming would break the additive guarantee (OQ-02). See Deferred.

### OQ-04: Which outcome for an exit-1 answer?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: `findings`. Exit 1 forbids a positive outcome (`validate_agent_record` exit-parity rule), and `docs/cli-output-contract.md` Section 3 defines exit 1 as "Domain Findings / Negative Result"; `unverified`, `partial` and `skipped` would misstate that the command ran fully (`verified: true`, `complete: true`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff agent_workflows/run_cli.py` hunk adding `_emit_result` showing it delegates to `_emit_agent_record` (and `_agent_cmd`/`_emit_agent_record` if E-01 had to add them), and the `N passed` line of `python3 -m pytest tests/test_run_cli_error_payload_keys.py tests/test_run_init.py -o addopts="" -q`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: against a scratch ledger made with `AW_NO_REEXEC=1 python3 -m agent_workflows run init --workflow <scratch>/wf.json --run-id run-abcdef1234 --dir <scratch>`, paste stdout and exit code of `runs show run-abcdef1234 --dir <scratch> --agent` and of `runs show run-abcdef1234 --dir <scratch> --agent --fields cmd` (code path `run_cli._run_show` -> `_emit_result`, changed by E-01/E-02), showing the first is one line with `"schema":"aw.agent/v1"`, `"kind":"result"`, `"cmd":"runs show"`, `"exit":1`, `"outcome":"findings"`, and `"run_id"`; the second carries no `run_id`; both exit 1. Paste the output of a one-liner piping the first line into `agent_schema.validate_agent_record` printing `[]`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: on the same scratch ledger after `run start run-abcdef1234 --step S-01 --workflow <scratch>/wf.json --dir <scratch>`, paste stdout and exit code of `runs status ... --agent` (a record, `exit: 1`) and `runs next ... --agent` (bare dict with no `schema` key, exit 3) (code paths `run_cli._run_status` / `_run_next` -> `_emit_result`, changed by E-03).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: on a fresh scratch ledger, paste stdout and exit code of `run start ... --step S-01 --agent` (record, `cmd: "run start"`, exit 0) and of `run record ... --step S-01 --state failed --agent` (bare dict, no `schema` key, exit 3) (code paths `run_cli._run_start` / `_run_record` -> `_emit_result`, changed by E-04).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff agent_workflows/command_surface.py` showing only comment lines changed, the rewritten `run_cli` docstring passages, the empty output of `grep -n "bare-dict family" agent_workflows/run_cli.py`, and the `N passed` line of `python3 -m pytest tests/test_run_cli_declarations.py tests/test_exit_contract_conformance.py tests/test_command_surface_declarations.py -o addopts="" -q`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the actual `python3 -m pytest tests/test_run_cli_agent_success_records.py -o addopts="" -v` output listing every test PASSED, including the `--fields`, unchanged-shape and redaction tests, with its `N passed` line; the falsifiability argument is that rows (a) to (c) and (e) require `schema`/`kind`/`cmd`, which the pre-change payloads (F-1, F-3) lack.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `git diff tests/conformance_matrix.py` showing the eight `EXEMPTION_REGISTRY` deletions, the `(5)` count and the four reason edits; paste `python3 -m pytest tests/test_live_conformance_sweep.py tests/test_agent_surface_conformance.py tests/test_shared_flag_honored.py tests/test_conformance_matrix_structure.py -o addopts="" -n auto` with its `N passed` line and zero failures; paste `python3 -m pytest tests/test_agent_surface_conformance.py -o addopts="" -q --collect-only | grep "runs "` showing the eight `runs` leaves are collected.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `git diff docs/cli-output-contract.md CHANGELOG.md`; paste `python3 -m pytest tests/test_cli_agent_protocol_doc.py tests/test_docs_check.py -o addopts="" -q` with its `N passed` line; paste the regression command from `## Required tests / validation` with its `N passed` line; paste the bare `python3 -m pytest` routine-gate summary line; paste the `aw sanitize --agent` result record.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and only after plan `2t033b` is `executed` (`- Item-Dependencies: executed:2t033b`), because that plan adds the `_agent_cmd` helper this plan reuses and edits the same docstrings, comments and doc paragraphs, which this plan then brings to their final state. All open questions are resolved (OQ-01 to OQ-04).

SCOPE FENCE. `- Scope-Paths:` is the expected edit set. An out-of-scope edit is permitted only when justified at finalize with `--scope-reason <path>=<why>`; acknowledge a declared path left unmodified with `--scope-ack`.

HONESTY. Every `V-*` evidence block MUST paste the ACTUAL runner or command output; never claim a pass that was not run.

COMMIT. Commit through `aw commit 2jzld4 -- agent_workflows/run_cli.py agent_workflows/command_surface.py tests/test_run_cli_agent_success_records.py tests/test_live_conformance_sweep.py tests/conformance_matrix.py docs/cli-output-contract.md CHANGELOG.md .aw/records/plans/pending/20261017-nyvyb4-01-2jzld4-run-cli-agent-success-payloads-become-aw-agent-v1-result-rec.ipd.md`; never `git add -A`, never push.

POST-GATE LIFECYCLE. Once every `E-*` is performed, every `V-*` is pass, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that transition; by hand run `aw ipd finalize 2jzld4 --actor <agent/model> --message <summary> --apply`. Never `git mv` the plan by hand.
