# IPD: Decide the aw.agent/v1 protocol boundary for run_cli wide-exit refusals and convert the exit-1 class

- Date: 2026-10-17
- Kind: child
- Concern: After plan `2t033b` (Set `jndec6`) makes every `aw run`/`aw runs` exit-2 refusal under `--agent` an `aw.agent/v1` `kind: "error"` record, the refusals that exit 1 (`EXIT_INCOMPLETE`), 3 (`EXIT_BLOCKED`), 4 (`EXIT_INVALID_EVIDENCE`), 5 (`EXIT_CORRUPTED_LEDGER`), 6 (`EXIT_OPERATIONAL`) and 7 (`EXIT_NOT_A_LEDGER`) are still bare `{"ok": false, "error": ..., "exit_code": N}` dicts. Backlog `p7bvku` records that converting them "needs a protocol decision", because `agent_schema.validate_agent_record` caps `exit` at (0, 1, 2), `docs/cli-output-contract.md` Section 4 requires the record's `exit` to equal the process exit code, and spec `25kzda` Section 5.6 row 4 (citing spec `6kwd2e` R7.3) forbids renumbering the run family into {0, 1, 2}. Nobody has written that decision down, so the boundary looks like an unfinished conversion rather than a contract.
- Scope: Record the protocol decision (OQ-01): the exit-1 refusal class IS representable in `aw.agent/v1` without renumbering anything, so convert it to a `kind: "result"`, `outcome: "fail"`, `exit: 1` record under `--agent` (legacy `ok`/`error`/`exit_code` and extra keys retained, home-path-redacted, `--fields` honored); codes 3 to 7 are NOT representable without either renumbering (forbidden) or breaking exit parity / the {0, 1, 2} bound (an `aw.agent/v1` breaking change, Section 8), so they stay bare by documented design. Implement the exit-1 conversion in `run_cli`, correct the comments and docs that describe the boundary, add behavioral tests that pin both halves, and add a CHANGELOG line. `--json` output, human output, every success payload, and every exit code value stay unchanged.
- Scope-Paths: agent_workflows/run_cli.py, agent_workflows/command_surface.py, tests/test_run_cli_wide_exit_refusal_shape.py, docs/cli-output-contract.md, CHANGELOG.md
- Item-Dependencies: executed:2t033b
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: p7bvku
- From-Spec: none
- Set: p7bvku
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: u1ujw9

## Workflow history
- 2026-10-17 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed. Readiness go-pending-approval. Review record .aw/records/reviews/20261017-p7bvku-01-u1ujw9-decide-the-aw-agent-v1-protocol-boundary-for-run-cli-wide-ex.review.md

- 2026-10-17 to-review (opencode): authored from backlog p7bvku; review-ready.
- 2026-10-17 draft (opencode): created.

## Goal

Turn the open "needs a protocol decision" note into a written, tested contract: `aw run`/`aw runs` refusals under `--agent` are `aw.agent/v1` records for every exit code the protocol can carry (2 via plan `2t033b`, 1 via this plan), and deliberately bare, with the reason documented, for the run family's wider codes 3 to 7.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: emit the exit-1 record

- [ ] E-01 In `agent_workflows/run_cli.py`, extend the `--agent` record branch that plan `2t033b` E-01 adds to `run_cli._emit_error` (reusing its `_agent_cmd(args)` helper and handing the record to its `_emit_agent_record(args, rec)` emitter, which owns the redact / `--fields` / `render_guarded_jsonl_record` sequence; do NOT copy that sequence) so that when `--agent` (or `as_agent`) is active AND `exit_code == EXIT_INCOMPLETE`, it builds `rec = {**(extra or {}), "error": message, "ok": False, "exit_code": 1, "schema": agent_schema.SCHEMA_VERSION, "kind": "result", "cmd": _agent_cmd(args), "exit": 1, "outcome": "fail", "verified": True, "complete": True, "next": f"aw runs status {target}" when `getattr(args, "target", None)` is a non-empty string else "aw runs status --help"}` and returns after `_emit_agent_record(args, rec)`. `extra` comes FIRST so an `extra` key can never override an envelope or legacy key, the same ordering rule `2t033b` E-01 uses for exit 2. `verified`/`complete` are True because the command fully read the ledger and evaluated the predicates; the verdict is the negative `fail`, which `validate_agent_record` accepts with exit 1. Every other case keeps its current path: exit 2 stays `2t033b`'s error record, exit 3, 4, 5, 6 and 7 stay the bare dict, `--json` and human mode are byte-for-byte unchanged. Return value unchanged.
  - Depends on: none
  - Expected outcome: the exit-1 branch calls `_emit_agent_record` (no second copy of the sanitize / project / render sequence in `run_cli.py`); `aw run finalize <incomplete-run-id> --agent` (once E-02 routes it here) prints one JSONL line that `validate_agent_record` accepts, with `kind: "result"`, `cmd: "run finalize"`, `exit: 1`, `outcome: "fail"`, `exit_code: 1`, `ok: false`; process exit stays 1.
  - Execution state: pending

- [ ] E-02 In `run_cli._run_finalize`, in the "Completion predicate gate" branch (`if not evaluation.is_complete:`), replace the machine-mode `_emit_machine(args, {"ok": False, "error": "run is incomplete; completion predicates not satisfied", "reasons": ..., "predicates": ..., "exit_code": EXIT_INCOMPLETE})` call with `_emit_error(args, "run is incomplete; completion predicates not satisfied", EXIT_INCOMPLETE, extra={"reasons": ..., "predicates": ...})`, built from the same expressions. Keep the human `else:` branch (the `error: run is incomplete; refusing to finalize` line plus one line per reason) exactly as it is, so only machine mode routes through `_emit_error`. The `except run_state.PredicateUnsatisfiedError` site already calls `_emit_error(..., EXIT_INCOMPLETE)` and needs no change.
  - Depends on: E-01
  - Expected outcome: `aw run finalize <incomplete-run-id> --json` output is unchanged (same keys `error`, `exit_code`, `ok`, `predicates`, `reasons`, same values, `_emit_machine` already sorts keys); no `_emit_machine` call in `run_cli.py` still builds a literal `"exit_code": EXIT_INCOMPLETE` payload.
  - Execution state: pending

- [ ] E-03 Rewrite the `run_cli._emit_error` docstring paragraph that `2t033b` E-03 leaves describing the split, so it states the decision of this plan's OQ-01: exit 2 is a `kind: "error"` record, exit 1 is a `kind: "result"` `outcome: "fail"` record, and exits 3 to 7 stay bare because `aw.agent/v1` cannot carry them without renumbering (spec `25kzda` 5.6 row 4) or breaking exit parity and the {0, 1, 2} bound (`docs/cli-output-contract.md` Sections 3 and 4, a `v2` change per Section 8); name `tests/test_run_cli_wide_exit_refusal_shape.py` as the guard. In `agent_workflows/command_surface.py`, update the `runs next` and `runs resume` declaration comment sentence that `2t033b` E-03 writes ("only the exit-2 refusals are `aw.agent/v1` records and the wider codes stay bare") to say the exit-1 and exit-2 refusals are records and codes 3 to 7 stay bare. RECONCILE WITH `2jzld4`: plan `2jzld4` (Set `nyvyb4`, also `executed:2t033b`) rewrites the same docstring paragraph and the same two `command_surface` sentences to say exit-0/1 SUCCESS answers are `kind: "result"` records. Read the text as it stands at execution: if `2jzld4` has landed, keep its success-answer statement and ADD this plan's exit-1-refusal statement rather than replacing it; if it has not, describe success payloads as still bare pending backlog `nyvyb4`. The final text must be true of the code at this plan's commit. Comment lines only; no `exit_contract` tuple changes.
  - Depends on: E-01
  - Expected outcome: `git diff agent_workflows/command_surface.py` touches comment lines only.
  - Execution state: pending

### Task group 2: tests

- [ ] E-04 Create `tests/test_run_cli_wide_exit_refusal_shape.py` (behavioral, P16; scratch repo fixture shaped like `tests/test_run_init.py` `_create_scratch_repo`, ledgers created through `aw run init` so no ledger is hand-built) with: (a) `run finalize <run-id> --agent` on a freshly initialized run (no step attempts) asserts exit 1, exactly one non-empty line, `agent_schema.validate_agent_record(rec) == []`, `rec["kind"] == "result"`, `rec["cmd"] == "run finalize"`, `rec["exit"] == rc == rec["exit_code"] == 1`, `rec["outcome"] == "fail"`, `rec["ok"] is False`, `rec["reasons"]` non-empty, `rec["next"] == f"aw runs status {run_id}"`; (b) the same with `--fields cmd` asserts exit 1, a valid record, `set(rec) <= agent_schema._PRESERVED_FIELDS | {"cmd"}`; (c) the same with `--json` asserts the payload has no `schema` key and its key set is exactly `{"ok", "error", "exit_code", "reasons", "predicates"}`; (d) a parametrized table asserting that each wider code stays bare under `--agent` (no `schema` key, `payload["ok"] is False`, `payload["exit_code"] == rc`) for: exit 3 (`run start <run-id> --step S-02` where the init workflow makes `S-02` depend on `S-01`), exit 5 (`runs status <run-id>` after rewriting the header's `run_id` to an invalid value, which the store reports as schema corruption), exit 6 (a second `run init --run-id <same id>`), exit 7 (`runs status <path>` on a JSONL file carrying `{"x": 1}`). Exit 4 is not separately driven here because its only site is the finalize evidence gate, already pinned by `tests/test_run_recovery_cli.py` (`finalize with a tool_event that exited nonzero`) and unchanged by this plan.
  - Depends on: E-01, E-02
  - Expected outcome: `python3 -m pytest tests/test_run_cli_wide_exit_refusal_shape.py -o addopts="" -v` passes; rows (a) and (b) fail against the pre-change code (which emits a dict with no `schema`/`kind`/`cmd`), and the (d) rows fail if anyone later converts a wider code without revisiting the decision.
  - Execution state: pending

### Task group 3: documentation

- [ ] E-05 In `docs/cli-output-contract.md` Section 3 (the "Verbs emitting bare JSON or non-agent payloads" bullet) and Section 3.1 (the paragraph `2t033b` E-06 writes about exit-2 refusals), state: `aw run`/`aw runs` refusals under `--agent` are `aw.agent/v1` records for exit 2 (`kind: "error"`) and exit 1 (`kind: "result"`, `outcome: "fail"`), both also carrying `ok` and `exit_code` and honoring `--fields`; refusals exiting 3 to 7 are deliberately bare JSON because `aw.agent/v1` cannot carry those codes without renumbering them (spec `25kzda` 5.6 row 4) or giving up exit parity and the {0, 1, 2} bound (Section 4), and either change would be an `aw.agent/v2` change under Section 8. The same paragraphs are also edited by plan `2jzld4` (success answers become records); apply the E-03 reconcile rule: keep any success-answer statement `2jzld4` wrote, otherwise describe success payloads as still bare pending backlog `nyvyb4`. Add one `Fixed:` line to the top pending section of `CHANGELOG.md` describing the user-visible change (`aw run finalize --agent` on an incomplete run now emits an `aw.agent/v1` record), with no em or en dashes.
  - Depends on: E-01
  - Expected outcome: `git diff docs/cli-output-contract.md CHANGELOG.md` shows only those edits; `python3 -m pytest tests/test_cli_agent_protocol_doc.py tests/test_docs_check.py -o addopts=""` passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_schema.validate_agent_record` rejects any `exit` outside (0, 1, 2) ("Field 'exit' must be an integer in (0, 1, 2)"), requires a `kind: "error"` record to carry `exit=2`, and allows a `kind: "result"` with `exit: 1` and `outcome: "fail"` (measured while authoring: `validate_agent_record({... "kind": "result", "cmd": "run finalize", "exit": 1, "outcome": "fail", "verified": True, "complete": True, "ok": False, "exit_code": 1, ...})` returned `[]`; the same dict with `kind: "error"` returned three violations).
- `docs/cli-output-contract.md` Section 4 "Exit Code Parity: The embedded `exit` field in every record MUST equal the process exit code (`0`, `1`, `2`)", and Section 3 "Verbs emitting `aw.agent/v1` records: Strictly bound to `{0, 1, 2}`"; `tests/test_agent_surface_conformance.py` asserts `last_rec.get("exit") == res.returncode`. Section 8: "Any breaking modification to record schema or field semantics requires a version bump (`aw.agent/v2`)".
- Spec `25kzda` Section 5.6 row 4: "renumbering shipped codes was explicitly refused on evidence ... approved spec `6kwd2e` R7.3 forbids collapsing the run family into `{0,1,2}`".
- Precedent for a non-agent-protocol wide exit coexisting with records: the drivers' `runner_shared.emit_agent_run_start_record` passes `exit_code=rc` straight into `exit`, so an `aw oc run --agent` returning 3 renders a record the validator rejects; that is a separate surface and is not touched here (see Deferred).
- Plan `2t033b` (Set `jndec6`, reviewed) owns the exit-2 conversion, the `_agent_cmd` helper, and the shared `_emit_agent_record(args, rec)` emitter that holds the redact / `--fields` / guarded-render sequence (its E-01 names this plan as a reuser); it explicitly hands codes 1 and 3 to 7 to this backlog item (`- Carrier: p7bvku`). This plan builds on that code and therefore depends on it (`executed:2t033b`).
- E-01 also converts the second exit-1 site, `except run_state.PredicateUnsatisfiedError` in `_run_finalize` (`_emit_error(..., EXIT_INCOMPLETE)`), because it already routes through `_emit_error`. That arm is reached only when `evidence.evaluate_completion` passes but `run_engine` (`run_engine.py:481`) refuses at commit time, which no CLI fixture produces deterministically, so E-04 pins the shape through the predicate-gate site only; both sites share the one branch E-01 adds.
- Plan `2jzld4` (Set `nyvyb4`, reviewed) converts exit-0/1 SUCCESS answers and edits the same docstring, `command_surface` sentences and doc paragraphs; its E-07 deliberately leaves the live sweep's `run finalize` step (this plan's refusal) out of its record assertions so either plan may land first. E-03 and E-05 carry the mirror reconcile rule.
- `run_cli._emit_machine` sorts keys, so routing the finalize payload through `_emit_error` leaves `--json` output identical.
- `run_cli._redact_output` scrubs token patterns and secret-named keys (measured: `coordinator_authority` renders as `"[REDACTED]"` in today's finalize payload); that stays as is.
- Tests are behavioral only (P16) and drive the CLI via `tests.support.run_cli` subprocesses.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | The exit-1 refusal on `run finalize` is a bare dict under `--agent`. | Measured 2026-10-17 in this lane on a scratch repo after `aw run init --run-id run-0123456789abcdef`: `aw run finalize run-0123456789abcdef --agent` printed `{"error":"run is incomplete; completion predicates not satisfied","exit_code":1,"ok":false,"predicates":{...},"reasons":["unsatisfied requirements: ['R-01']","no step attempts recorded"]}`, rc=1. |
| F-2 | Codes 5, 6, 7 are bare dicts under `--agent` today. | Same scratch repo: `aw runs status <tampered run> --agent` printed `{"error":"ledger corruption detected: ...","exit_code":5,"ok":false}` rc=5; a second `aw run init --run-id run-0123456789abcdef --agent` printed `{"error":"run directory already exists: ...","exit_code":6,"ok":false}` rc=6; `aw runs status foo.jsonl --agent` printed `{"corrupted":false,...,"exit_code":7,"not_a_ledger":true,"ok":false,"path":"foo.jsonl"}` rc=7. |
| F-3 | The only exit-1 REFUSAL sites in `run_cli` are both in `_run_finalize`. | Census of `EXIT_INCOMPLETE` in `run_cli.py`: the inline "run is incomplete; completion predicates not satisfied" payload and the `PredicateUnsatisfiedError` `_emit_error` call. Other exit-1 returns (`_run_status` incomplete, `_run_evidence`/`verify-ledger` invalid, `_emit_projection` empty) are SUCCESS payloads owned by backlog `nyvyb4`. |
| F-4 | No representation of codes 3 to 7 inside `aw.agent/v1` satisfies all three constraints at once. | Options in OQ-01: an `exit` of 3 to 7 fails the validator; an `exit` remapped into {0, 1, 2} breaks Section 4 parity; renumbering the process code breaks `25kzda` 5.6 row 4 and `6kwd2e` R7.3. |
| F-5 | `--json` and human finalize outputs are pinned by existing tests that must stay green. | `tests/test_run_recovery_cli.py` row "finalize refuses an incomplete run" (`--json`, `text-in "incomplete"`, exit 1); `tests/test_live_conformance_sweep.py::test_live_ledger_mutation_leaves_conformance` (`run finalize` expected rc 1 in every mode, `--agent` last line must parse as a dict). |

## Proposed changes (ordered, validatable)

1. E-01: add the exit-1 `kind: "result"` / `outcome: "fail"` branch to `_emit_error`'s `--agent` record path.
2. E-02: route `_run_finalize`'s machine-mode incomplete payload through `_emit_error`.
3. E-03: correct the `_emit_error` docstring and the `command_surface` comments to state the decided boundary.
4. E-04: add `tests/test_run_cli_wide_exit_refusal_shape.py` pinning both halves.
5. E-05: update `docs/cli-output-contract.md` Sections 3 and 3.1 and add a CHANGELOG line.

## Deferred / out of scope (with reason)

- Converting refusals that exit 3, 4, 5, 6 or 7 into `aw.agent/v1` records: not possible without renumbering (forbidden by spec `25kzda` 5.6 row 4 / `6kwd2e` R7.3) or relaxing exit parity and the {0, 1, 2} bound, which is a breaking `aw.agent/v1` change requiring `aw.agent/v2` (`docs/cli-output-contract.md` Section 8). This plan records that as the decided contract (OQ-01).
  - Carrier-Declined: deliberate design; the wider run-family codes stay bare JSON under aw.agent/v1, and any reversal is an aw.agent/v2 protocol decision for the maintainer (OQ-01, resolved)
- `--agent` SUCCESS payloads of the `aw run`/`aw runs` leaves, including the exit-1 success results of `runs status`, `runs evidence` and `runs verify-ledger`.
  - Carrier: nyvyb4
- `runner_shared.emit_agent_run_start_record` passing a driver exit of 3 into a record's `exit` (a different command family, `aw oc run`/`aw agy run`, not `run_cli`); noted in Step 0 as context, not changed here.
  - Carrier-Declined: outside backlog p7bvku, which names run_cli refusals only; no defect was measured on that path in this turn, so filing it would be an unmeasured hunch

## Scope check

- Over-scope: none. `run_cli.py` is the fix; `command_surface.py` (comments only) and `docs/cli-output-contract.md` describe the boundary and would otherwise be stale; the new test file is the guard; `CHANGELOG.md` is the user-facing record.
- Under-scope: none known. `tests/test_run_recovery_cli.py`, `tests/test_live_conformance_sweep.py`, `tests/test_run_init.py` and `tests/test_run_cli_error_payload_keys.py` read finalize or wider-code refusals and are expected to stay green unchanged (F-5; `--json` unchanged, `--agent` last line is still a dict, wider codes unchanged). If one fails, that is a scope finding to resolve at execution. `tests/conformance_matrix.py`'s `run finalize` `MUTATION_EXEMPTION_REGISTRY` entry is `arg_fixture_needed` (it needs a target positional), which stays true whatever the payload shape; its reason text is plan `2jzld4`'s to edit.

## Required tests / validation

- `python3 -m pytest tests/test_run_cli_wide_exit_refusal_shape.py -o addopts="" -v` passes (E-01, E-02, E-04).
- `python3 -m pytest tests/test_run_recovery_cli.py tests/test_run_cli_error_payload_keys.py tests/test_run_cli_corruption_exit.py tests/test_run_init.py tests/test_live_conformance_sweep.py tests/test_run_cli_declarations.py tests/test_exit_contract_conformance.py -o addopts="" -n auto -m "not livecorpus"` passes (regressions, E-02, E-03).
- `python3 -m pytest tests/test_cli_agent_protocol_doc.py tests/test_docs_check.py -o addopts="" -q` passes (E-05).
- Routine gate `python3 -m pytest` passes.
- `aw sanitize --agent` reports no new finding on the changed files.

## Spec / documentation sync

No `.spec.md` is edited: no exit code value changes, so spec `25kzda` Section 5.6 stays accurate, and the decision this plan records concerns the output protocol, which `docs/cli-output-contract.md` owns. That document's Sections 3 and 3.1 are updated (E-05) so the boundary is written down as a contract instead of reading as an unfinished conversion.

## Open questions

### OQ-01: Which representation should the wider run-family refusal codes (1, 3 to 7) take under `--agent`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Options weighed: (A) keep all non-2 codes bare; (B) convert only what `aw.agent/v1` can carry as-is (exit 1, as a `result`/`fail` record) and keep 3 to 7 bare by documented design; (C) emit records whose `exit` is remapped into {0, 1, 2} while the process exits 3 to 7, which breaks Section 4 exit parity and `tests/test_agent_surface_conformance.py`'s parity assertion; (D) renumber the process codes into {0, 1, 2}, refused by spec `25kzda` 5.6 row 4 and `6kwd2e` R7.3; (E) widen the validator's exit set, a breaking change Section 8 reserves for `aw.agent/v2`. Chose (B): it is the only option that adds protocol coverage while changing no public contract, it is reversible, and it is testable. (C), (D) and (E) each change a published contract, which is the maintainer's call and is recorded in Deferred as declined pending such a decision.

### OQ-02: `kind: "result"` or `kind: "error"` for the exit-1 refusal?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: `result`. `validate_agent_record` requires `kind: "error"` to carry exit 2, and `docs/cli-output-contract.md` Section 4 reserves `error` for exit 2; exit 1 is a domain finding ("the run is incomplete"), which Section 3 classifies as `1`, paired with `fail`.

### OQ-03: Keep the legacy `ok` / `exit_code` keys, and which `next`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Keep them, for the same reason `2t033b` OQ-02 gives (extra keys are valid and existing consumers read them). `next` is `aw runs status <target>`, the read that shows which predicates are unsatisfied, falling back to `aw runs status --help` when no target is set.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: in a scratch repo, after `AW_NO_REEXEC=1 python3 -m agent_workflows run init --workflow <wf.json> --run-id run-0123456789abcdef --dir <scratch>`, paste stdout and exit code of `AW_NO_REEXEC=1 python3 -m agent_workflows run finalize run-0123456789abcdef --dir <scratch> --agent` and the same with `--fields cmd` (code path `run_cli._run_finalize` -> `run_cli._emit_error`, changed by E-01 and E-02), showing one line with `"schema":"aw.agent/v1"`, `"kind":"result"`, `"cmd":"run finalize"`, `"exit":1`, `"outcome":"fail"`, `"exit_code":1`, `"ok":false`, `"next":"aw runs status run-0123456789abcdef"`, the projected line carrying no `error`/`ok`/`exit_code`, both rc=1; and paste a one-liner feeding the first line to `agent_schema.validate_agent_record` printing `[]`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `git diff agent_workflows/run_cli.py` hunks for `_emit_error` (showing the exit-1 branch delegating to `_emit_agent_record`, with `extra` spread before the envelope keys) and for `_run_finalize`, and the stdout of the same finalize with `--json` showing exactly the keys `error`, `exit_code`, `ok`, `predicates`, `reasons` and no `schema` key, rc=1.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff agent_workflows/command_surface.py` showing only comment lines changed, and the rewritten `_emit_error` docstring paragraph; paste `python3 -m pytest tests/test_run_cli_declarations.py tests/test_exit_contract_conformance.py -o addopts="" -q` with its `N passed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the actual `python3 -m pytest tests/test_run_cli_wide_exit_refusal_shape.py -o addopts="" -v` output listing every test (a), (b), (c) and each (d) row for exits 3, 5, 6, 7 as PASSED, with the `N passed` line; then paste the regression command from Required tests (`tests/test_run_recovery_cli.py ... tests/test_exit_contract_conformance.py`) with its `N passed` line and zero failures. Falsifiability: rows (a)/(b) require `schema`/`kind`/`cmd`, which the F-1 pre-change payload lacks.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff docs/cli-output-contract.md CHANGELOG.md`; paste `python3 -m pytest tests/test_cli_agent_protocol_doc.py tests/test_docs_check.py -o addopts="" -q` with its `N passed` line; paste the bare `python3 -m pytest` routine-gate summary line; paste the `aw sanitize --agent` result record.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after plan `2t033b` is executed (`- Item-Dependencies: executed:2t033b`), since E-01 extends the record branch that plan adds. All open questions are resolved (OQ-01, OQ-02, OQ-03); OQ-01 records a protocol decision a reviewer should confirm.

SCOPE FENCE. `- Scope-Paths:` is the expected edit set. An out-of-scope edit is permitted only when justified at finalize with `--scope-reason <path>=<why>`; acknowledge a declared path left unmodified with `--scope-ack`.

HONESTY. Every `V-*` evidence block MUST paste the ACTUAL runner or command output; never claim a pass that was not run.

COMMIT. Commit through `aw commit u1ujw9 -- agent_workflows/run_cli.py agent_workflows/command_surface.py tests/test_run_cli_wide_exit_refusal_shape.py docs/cli-output-contract.md CHANGELOG.md .aw/records/plans/pending/20261017-p7bvku-01-u1ujw9-decide-the-aw-agent-v1-protocol-boundary-for-run-cli-wide-ex.ipd.md`; never `git add -A`, never push.

POST-GATE LIFECYCLE. Once every `E-*` is performed, every `V-*` is pass, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that transition; by hand run `aw ipd finalize u1ujw9 --actor <agent/model> --message <summary> --apply`. Never `git mv` the plan by hand.
