# IPD: Emit aw.agent/v1 cannot-run records on remaining handler usage refusals

- Date: 2026-10-14
- Kind: child
- Concern: Remaining early `return 2` usage and input-validation refusal branches in `backlog.run_new`, `specs.run_new`, `prompts.run_new`, and `ipd_authoring.run_scaffold` return exit code 2 without emitting an `aw.agent/v1` `kind: "error"`, `outcome: "cannot-run"` record on stdout under `--agent` or `--json`.
- Scope: Route all remaining early `return 2` usage and input-validation refusal branches in `agent_workflows/backlog.py` (`backlog.run_new`, 11 arms), `agent_workflows/specs.py` (`specs.run_new`, 5 arms), `agent_workflows/prompts.py` (`prompts.run_new`, 5 arms), and `agent_workflows/ipd_authoring.py` (`ipd_authoring.run_scaffold` and `ipd_authoring._setid_length_guard`, 13 arms) through `renderers.emit_usage_refusal`, update `tests/test_backlog_descriptive_safety.py` (`BacklogDescriptiveSafetyTests.test_agent_mode_refusal_shape`), and expand `tests/test_usage_refusal_agent_record.py` (`HandlerRefusalRecordTests`) to cover every branch under `--agent`, `--json`, and human mode.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/specs.py, agent_workflows/prompts.py, agent_workflows/ipd_authoring.py, tests/test_backlog_descriptive_safety.py, tests/test_usage_refusal_agent_record.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: mmpjti
- Blocks-Release: next
- Set: mmpjti (handler-refusal-agent-records)
- Order: 1
- Highest E allocated: 08
- Author: antigravity
- Id: xvv7n4

## Workflow history
- 2026-10-15 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007

- 2026-10-14 to-review (antigravity): created from backlog item mmpjti, ready for review.

## Goal

Ensure every remaining early `return 2` usage and input-validation refusal branch in `backlog.run_new`, `specs.run_new`, `prompts.run_new`, and `ipd_authoring.run_scaffold` emits a schema-valid `aw.agent/v1` `kind: "error"`, `outcome: "cannot-run"`, `exit: 2` record on stdout under `--agent` and `--json` via `renderers.emit_usage_refusal` while keeping human-mode output and exit codes unchanged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline verification and handler refusal wiring

- [ ] E-01 Run the pre-change baseline probe across representative unhandled refusal branches in `backlog.run_new`, `specs.run_new`, `prompts.run_new`, and `ipd_authoring.run_scaffold` under `--agent` and run `python3 -m pytest tests/test_usage_refusal_agent_record.py tests/test_backlog_descriptive_safety.py tests/test_specs_date_containment.py tests/test_ipd_authoring.py` to record baseline pre-change stdout, stderr, and exit codes.
  - Depends on: none
  - Expected outcome: The probe confirms `backlog new`, `specs new`, and `prompts new` return `rc == 2` with `stdout == ""` on unhandled refusal branches under `--agent`, `ipd scaffold` returns `rc == 2` with plain-text `"error: ..."` on stdout and `stderr == ""` under `--agent`, and the existing test files pass on baseline HEAD. Also record, as context for E-05, that a SUCCESSFUL `ipd scaffold --agent` whose `--author` is normalized (e.g. `--author 'a (b)'`) or whose `--set` is 15-24 characters prints a `note:` line on stdout BEFORE the `aw.agent/v1` result record (measured at review HEAD `eb0787c43`).
  - Execution state: pending

- [ ] E-02 In `agent_workflows/backlog.py` (`backlog.run_new`, lines 1101-1432), define a local helper `_refuse(err_msg: str) -> int` that prints `err_msg` to `sys.stderr` and returns `emit_usage_refusal("backlog new", err_msg.removeprefix("aw backlog new: "), "aw backlog new --help", ctx)`, route all 13 `return 2` refusal arms in `backlog.run_new` (the 2 arms wired by `0z7ds3` plus the 11 remaining arms for invalid `status`, `_setid_err`, invalid `item.priority`, invalid `item.kind`, `_summary_err`, `_gr_err`, `status == "blocked"` missing `--gate-kind`/`--gate-ref`, `_gate_err`, `_exempt_err`, unknown `--blocks-release`, and `_msg_err`) through `_refuse`, and remove the redundant second `ctx = select_output(args)` assignment later in `backlog.run_new` (verify it is not reassigned between the two before deleting). NOTE: the invalid-`status` arm is unreachable through `cli.main` because the `backlog new` parser declares `--status` with `choices=`; it is still wired, and is exercised by calling `backlog.run_new` directly with an `argparse.Namespace` (the existing `tests/test_backlog_descriptive_safety.py` `_call_new` pattern).
  - Depends on: E-01
  - Expected outcome: Every `return 2` refusal path in `backlog.run_new` writes its existing message to `sys.stderr`, returns `2`, writes nothing to stdout in `HUMAN` mode, and emits a schema-valid `aw.agent/v1` `kind: "error"`, `cmd: "backlog new"`, `outcome: "cannot-run"`, `exit: 2`, `next: "aw backlog new --help"` record on stdout in `AGENT` and `JSON` modes.
  - Execution state: pending

- [ ] E-03 In `agent_workflows/specs.py` (`specs.run_new`, lines 1044-1149), define a local helper `_refuse(err_msg: str) -> int` that prints `err_msg` to `sys.stderr` and returns `emit_usage_refusal("specs new", err_msg.removeprefix("aw specs new: "), "aw specs new --help", ctx)`, and route all 6 `return 2` refusal arms in `specs.run_new` (empty `--title`, `_title_err`, `_summary_err`, lexical `--date` format mismatch, calendar-invalid `--date` `ValueError`, and destination-containment `ValueError`) through `_refuse`. For the destination-containment arm, the stderr line keeps its existing text, but the message passed to `emit_usage_refusal` must NOT carry `dest` / `specs_dir` as absolute paths (`renderers.emit_usage_refusal` applies only `agent_schema.redact_home_paths`, which leaves `/tmp/...` and other non-home absolute paths intact, measured at review): render both through `agent_schema.normalize_repo_path(..., repo_root)` in the machine message. The containment arm is a defense-in-depth branch not reachable through `--date` (the `\A\d{4}-\d{2}-\d{2}\Z` check refuses every traversal first, as `tests/test_specs_date_containment.py` shows); exercise it by monkeypatching `record_placement.resolve_creation_path` to return a path outside the specs tree.
  - Depends on: E-01
  - Expected outcome: Every `return 2` refusal path in `specs.run_new` writes its existing message to `sys.stderr`, returns `2`, writes nothing to stdout in `HUMAN` mode, and emits a schema-valid `aw.agent/v1` `kind: "error"`, `cmd: "specs new"`, `outcome: "cannot-run"`, `exit: 2`, `next: "aw specs new --help"` record on stdout in `AGENT` and `JSON` modes.
  - Execution state: pending

- [ ] E-04 In `agent_workflows/prompts.py` (`prompts.run_new`, lines 492-562), define a local helper `_refuse(err_msg: str) -> int` that prints `err_msg` to `sys.stderr` and returns `emit_usage_refusal("prompts new", err_msg.removeprefix("aw prompts new: "), "aw prompts new --help", ctx)`, and route all 6 `return 2` refusal arms in `prompts.run_new` (empty `--slug`, post-kebab empty `slug`, unrecognized `--kind`, invalid `--date`, invalid `--time`, and `set_err` from `_resolve_set_id`) through `_refuse`.
  - Depends on: E-01
  - Expected outcome: Every `return 2` refusal path in `prompts.run_new` writes its existing message to `sys.stderr`, returns `2`, writes nothing to stdout in `HUMAN` mode, and emits a schema-valid `aw.agent/v1` `kind: "error"`, `cmd: "prompts new"`, `outcome: "cannot-run"`, `exit: 2`, `next: "aw prompts new --help"` record on stdout in `AGENT` and `JSON` modes.
  - Execution state: pending

- [ ] E-05 In `agent_workflows/ipd_authoring.py` (`ipd_authoring._setid_length_guard`, lines 404-430, and `ipd_authoring.run_scaffold`, lines 433-656), resolve `ctx = select_output(args)` at the top of `ipd_authoring.run_scaffold` and route all 13 early validation `return 2` refusal arms (invalid `--kind`, empty `--title`, `set_name is None` and `order is None` (both unreachable through `cli.main`, whose parser marks `--set` and `--order` `required=True`; exercise them by calling `ipd_authoring.run_scaffold` directly), `_setid_length_guard` refusal (give `_setid_length_guard` a `ctx` keyword so its `error:` / `note:` lines follow the same routing; its only caller is `run_scaffold`), orchestrator `order != 0`, child `order < 1`, missing `--author`, unknown `--from-backlog`, missing `--priority`/`--work-kind`, invalid `--priority`, invalid `--work-kind`, and non-conforming `--path` without `--legacy-name`) through a local helper `_refuse_scaffold(msg: str, ctx: OutputContext) -> int` that in `HUMAN` mode preserves `print(f"error: {msg}")` on stdout and returns `2`, and in `AGENT` or `JSON` mode writes `f"error: {msg}"` to `sys.stderr` and returns `emit_usage_refusal("ipd scaffold", msg, "aw ipd scaffold --help", ctx)`, while routing `note:` notices in `ipd_authoring._setid_length_guard` and `ipd_authoring.run_scaffold` to `sys.stderr` when `ctx.is_agent or ctx.is_json` so machine stdout contains only the `aw.agent/v1` record. This includes the SUCCESS path: the `--author` normalization `note:` and the setid-length warning `note:` must also go to stderr under `--agent` / `--json`, so `ipd scaffold --agent` stdout is exactly one JSONL record on success as well as on refusal. Leave the post-validation `scaffold write failed` arm (already a `CommandResult` emit) unchanged.
  - Depends on: E-01
  - Expected outcome: All 13 validation refusal arms in `ipd_authoring.run_scaffold` emit a schema-valid `aw.agent/v1` `kind: "error"`, `cmd: "ipd scaffold"`, `outcome: "cannot-run"`, `exit: 2`, `next: "aw ipd scaffold --help"` record on stdout under `--agent` and `--json` without stray `error:` or `note:` lines on stdout, a successful `--agent` scaffold with a normalized author or a 15-24 character setid emits exactly one stdout line (the result record) with the `note:` on stderr, while human-mode callers (including `tests/test_ipd_authoring.py` and `tests/test_ipd_lifecycle_cli.py`) observe byte-identical `error:` and `note:` lines on stdout.
  - Execution state: pending

### Task group 2: Test updates, comprehensive branch coverage, and full-suite validation

- [ ] E-06 In `tests/test_backlog_descriptive_safety.py` (`BacklogDescriptiveSafetyTests.test_agent_mode_refusal_shape`, lines 401-409), update the `--agent` assertion so that `_call_new(self.repo, summary="bad\nsummary", agent=True, slug="agent-mode")` parses `out` as JSON, validates it via `agent_schema.validate_agent_record`, and asserts `rec["kind"] == "error"`, `rec["cmd"] == "backlog new"`, `rec["outcome"] == "cannot-run"`, `rec["exit"] == 2`, `rec["next"] == "aw backlog new --help"`, and keeps the existing `self.assertIn("newline", err.lower())` stderr assertion (the `aw.agent/v1` error record produced by `CommandResult.to_agent_record` carries NO message field, measured at review: keys are `cmd, complete, exit, findings, kind, next, outcome, schema, verified`, so the diagnostic text is asserted on stderr, not in the record). Add a human-mode call (`agent=False`) asserting `out == ""` and the same stderr text, since the existing test has no human arm.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest tests/test_backlog_descriptive_safety.py` passes with 0 failures and verifies the `aw.agent/v1` `cannot-run` record on `--agent` descriptive-safety refusals.
  - Execution state: pending

- [ ] E-07 In `tests/test_usage_refusal_agent_record.py`, add a table-driven test module section (beside the existing `test_e04_missing_required_handler_leaves`) exercising every remaining refusal arm across `backlog.run_new` (11 arms), `specs.run_new` (5 arms, including calendar-invalid `--date 9999-99-99` and the monkeypatched destination-containment arm), `prompts.run_new` (5 arms), and `ipd_authoring.run_scaffold` (13 validation arms), each under `--agent`, `--json`, and human mode. Drive reachable arms through `cli.main` in a scratch repo under `tmp_path` (cwd or `--dir` as the leaf accepts; `ipd scaffold` has no `--dir`), and the four CLI-unreachable arms (backlog invalid `status`; scaffold `set_name is None`, `order is None`; specs containment) by calling the handler with an `argparse.Namespace` carrying `agent=True` / `json=True`. Assertions per mode: `--agent`: exactly one non-empty stdout line, `agent_schema.validate_agent_record(rec) == []`, `kind == "error"`, `cmd`, `outcome == "cannot-run"`, `exit == 2`, `next == "aw <cmd> --help"`; `--json`: stdout parses as one JSON object with `status == "cannot-run"`, `exit_code == 2`, and a `next_actions` entry whose `command == "aw <cmd> --help"` (the `JsonRenderer` emits `CommandResult.to_dict()`, which is NOT an `aw.agent/v1` record and fails `validate_agent_record` by construction, measured at review; mirror `test_required_arg_leaf_json_mode`); human: `rc == 2`, stdout `""` (or `error: ...` for `ipd scaffold`), stderr non-empty. Every mode asserts no `tmp_path` string in stdout. Add the scaffold success-path arm from E-05 (normalized author, one stdout line). Show the new cases RED against the pre-change handlers (stdout `""` / `error: ...`) before E-02..E-05.
  - Depends on: E-02, E-03, E-04, E-05, E-06
  - Expected outcome: every new case passes, and the pre-change RED run shows them failing for the reason above.
  - Execution state: pending

- [ ] E-08 Run the targeted files, the full bare suite (`python3 -m pytest`), and `aw sanitize --agent`, then commit through `aw commit xvv7n4 -- <paths>`.
  - Depends on: E-07
  - Expected outcome: zero new failures by node id against an execution-base baseline, sanitize `clean`, and one commit containing only the Scope-Paths files plus this plan.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `renderers.emit_usage_refusal` (`agent_workflows/renderers.py`, lines 413-444, `"def emit_usage_refusal("`) is the shared helper introduced by executed plan `0z7ds3` (`.aw/records/plans/executed/20261012-91pjax-01-0z7ds3-emit-an-aw-agent-v1-cannot-run-record-when-argparse-or-an-ea.ipd.md`). In `HUMAN` mode (`not context.is_agent and not context.is_json`), it returns `2` immediately without writing to stdout. In `AGENT` or `JSON` mode, it redacts home paths from `message`, sets `next: next_cmd`, and emits a validated `aw.agent/v1` `kind: "error"`, `outcome: "cannot-run"`, `exit: 2` record on stdout (compact JSONL via `AgentRenderer.render_error` in `AGENT` mode; pretty-printed JSON via `JsonRenderer.render_error` in `JSON` mode).
- Under `--json`, `renderers.JsonRenderer` emits `CommandResult.to_dict()` (`schema`, `command`, `status`, `exit_code`, `summary`, `next_actions`, ...), which is NOT an `aw.agent/v1` record; `--agent` emits `CommandResult.to_agent_record`, which carries no message field. `tests/test_usage_refusal_agent_record.py` `test_required_arg_leaf_json_mode` is the precedent for the `--json` assertion shape.
- `backlog.run_new` (`agent_workflows/backlog.py`, lines 1101-1280), `specs.run_new` (`agent_workflows/specs.py`, lines 1044-1149), and `prompts.run_new` (`agent_workflows/prompts.py`, lines 492-562) write human refusal diagnostics to `sys.stderr` prefixed with `"aw <cmd>: "` and write nothing to `sys.stdout` in human mode.
- `ipd_authoring.run_scaffold` (`agent_workflows/ipd_authoring.py`, lines 433-548) historically printed `f"error: {msg}"` and `f"note: ..."` to `sys.stdout` in human mode before resolving `ctx = select_output(args)` at `"ctx = select_output(args)"` (line 611). Existing human-mode unit tests in `tests/test_ipd_authoring.py` (`ScaffoldTests.test_scaffold_requires_set_and_order`, lines 46-50, and `ScaffoldTests.test_scaffold_clustering_and_auto_derivation`, lines 198-250) and `tests/test_ipd_lifecycle_cli.py` (`IpdLifecycleCliTests.test_run_scaffold_notice_behavior`, line 3035) capture `stdout` via `redirect_stdout` in human mode (`agent=False`, `json=False`) and assert that `error:` and `note:` strings appear on `stdout`. Preserving `print(f"error: {msg}")` and `print(f"note: ...")` on `stdout` when `not ctx.is_agent and not ctx.is_json` while routing them to `sys.stderr` and emitting `emit_usage_refusal("ipd scaffold", msg, "aw ipd scaffold --help", ctx)` on `stdout` when `ctx.is_agent or ctx.is_json` satisfies both contracts without breaking human-mode tests.
- `tests/test_backlog_descriptive_safety.py` (`BacklogDescriptiveSafetyTests.test_agent_mode_refusal_shape`, lines 401-409, `"def test_agent_mode_refusal_shape(self) -> None:"`) explicitly pinned the pre-`mmpjti` empty stdout (`self.assertEqual(out, "")`) when `backlog.run_new` refused an embedded newline under `agent=True`. Backlog item `mmpjti` explicitly notes that this test was written before `91pjax` established the `cannot-run` agent record contract and must be updated to assert the `cannot-run` record on stdout.

## Findings

Baseline probe measured at HEAD `99a1da97a` across the four handlers:

| Handler (`module.function`) | Total early `return 2` validation arms | Wired in `0z7ds3` | Remaining silent / non-JSON under `--agent` & `--json` | Pre-change `--agent` stdout |
| --- | --- | --- | --- | --- |
| `backlog.run_new` (`agent_workflows/backlog.py`, lines 1101-1280) | 13 | 2 (missing `--priority`/`--work-kind` at line 1156; empty `--summary` at line 1183) | 11 (invalid `status` line 1106; `_setid_err` line 1135; invalid `item.priority` line 1173; invalid `item.kind` line 1178; `_summary_err` line 1203; `_gr_err` line 1212; `status == "blocked"` missing `--gate-kind`/`--gate-ref` line 1216; `_gate_err` line 1226; `_exempt_err` line 1235; unknown `--blocks-release` line 1249; `_msg_err` line 1275) | `""` (0 bytes) |
| `specs.run_new` (`agent_workflows/specs.py`, lines 1044-1149) | 6 | 1 (empty `--title` at line 1058) | 5 (`_title_err` line 1072; `_summary_err` line 1081; lexical `--date` format mismatch line 1101; calendar-invalid `--date` `ValueError` line 1106; destination-containment `ValueError` line 1147) | `""` (0 bytes) |
| `prompts.run_new` (`agent_workflows/prompts.py`, lines 492-562) | 6 | 1 (empty `--slug` at line 499) | 5 (empty post-kebab `slug` line 510; unrecognized `--kind` line 517; invalid `--date` line 528; invalid `--time` line 541; `set_err` from `_resolve_set_id` line 553) | `""` (0 bytes) |
| `ipd_authoring.run_scaffold` & `ipd_authoring._setid_length_guard` (`agent_workflows/ipd_authoring.py`, lines 404-548) | 13 | 0 | 13 (invalid `--kind` line 438; empty `--title` line 443; `set_name is None` line 448; `order is None` line 451; `_setid_length_guard` `err` line 428/456; orchestrator `order != 0` line 458; child `order < 1` line 461; missing `--author` line 465; unknown `--from-backlog` line 498; missing `--priority`/`--work-kind` line 509; invalid `--priority` line 520; invalid `--work-kind` line 524; non-conforming `--path` without `--legacy-name` line 543) | Plain-text `"error: ..."` line (not JSON) |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/backlog.py` (`backlog.run_new`)**:
   - Immediately after `ctx = select_output(args)` at `"ctx = select_output(args)"` (line 1102), define:
     ```python
     def _refuse(err_msg: str) -> int:
         print(err_msg, file=sys.stderr)
         clean_msg = err_msg.removeprefix("aw backlog new: ")
         return emit_usage_refusal("backlog new", clean_msg, "aw backlog new --help", ctx)
     ```
   - Replace all 13 `print(..., file=sys.stderr)` + `return 2` blocks in `backlog.run_new` (lines 1104-1275) with `return _refuse(...)`.
   - Remove the redundant second `ctx = select_output(args)` at `"ctx = select_output(args)"` (line 1431).

2. **`agent_workflows/specs.py` (`specs.run_new`)**:
   - Immediately after `ctx = select_output(args)` at `"ctx = select_output(args)"` (line 1045), define:
     ```python
     def _refuse(err_msg: str) -> int:
         print(err_msg, file=sys.stderr)
         clean_msg = err_msg.removeprefix("aw specs new: ")
         return emit_usage_refusal("specs new", clean_msg, "aw specs new --help", ctx)
     ```
   - Replace all 6 `print(..., file=sys.stderr)` + `return 2` blocks in `specs.run_new` (lines 1051-1148) with `return _refuse(...)`.

3. **`agent_workflows/prompts.py` (`prompts.run_new`)**:
   - Immediately after `ctx = select_output(args)` at `"ctx = select_output(args)"` (line 493), define:
     ```python
     def _refuse(err_msg: str) -> int:
         print(err_msg, file=sys.stderr)
         clean_msg = err_msg.removeprefix("aw prompts new: ")
         return emit_usage_refusal("prompts new", clean_msg, "aw prompts new --help", ctx)
     ```
   - Replace all 6 `print(..., file=sys.stderr)` + `return 2` blocks in `prompts.run_new` (lines 496-556) with `return _refuse(...)`.

4. **`agent_workflows/ipd_authoring.py` (`ipd_authoring._setid_length_guard` and `ipd_authoring.run_scaffold`)**:
   - Move `ctx = select_output(args)` to the start of `ipd_authoring.run_scaffold` (line 434).
   - Define local helpers in `ipd_authoring.py` (or inside `run_scaffold` and `_setid_length_guard`):
     - When `ctx.is_agent or ctx.is_json`, `_refuse_scaffold(msg, ctx)` prints `f"error: {msg}"` to `sys.stderr` and returns `emit_usage_refusal("ipd scaffold", msg, "aw ipd scaffold --help", ctx)`. When `HUMAN`, it prints `f"error: {msg}"` to `sys.stdout` and returns `2`.
     - When `ctx.is_agent or ctx.is_json`, `note:` notices in `_setid_length_guard` and `run_scaffold` print to `sys.stderr` so stdout remains pure JSON/JSONL; when `HUMAN`, they continue printing to `sys.stdout`.
   - Route all 13 validation `return 2` arms in `ipd_authoring.run_scaffold` (lines 437-544, including `_setid_length_guard`) through `_refuse_scaffold(msg, ctx)`.

5. **Tests (`tests/test_backlog_descriptive_safety.py` and `tests/test_usage_refusal_agent_record.py`)**:
   - Update `BacklogDescriptiveSafetyTests.test_agent_mode_refusal_shape` (`tests/test_backlog_descriptive_safety.py`, lines 401-409) to validate the `aw.agent/v1` `cannot-run` JSON record on stdout under `agent=True`.
   - Expand `HandlerRefusalRecordTests` (`tests/test_usage_refusal_agent_record.py`, lines 149-189) to test all remaining refusal branches in `backlog.run_new` (11 arms), `specs.run_new` (5 arms), `prompts.run_new` (5 arms), and `ipd_authoring.run_scaffold` (13 arms) across `--agent`, `--json`, and human mode.

## Deferred / out of scope (with reason)

none.

## Scope check

- Over-scope: none.
- Under-scope: none; all four handlers named in backlog item `mmpjti` (`backlog.run_new`, `specs.run_new`, `prompts.run_new`, and `ipd_authoring.run_scaffold`) and the existing test `tests/test_backlog_descriptive_safety.py` named in `mmpjti` are covered.

## Required tests / validation

- Targeted unit and CLI tests:
  - `python3 -m pytest tests/test_usage_refusal_agent_record.py tests/test_backlog_descriptive_safety.py tests/test_specs_date_containment.py tests/test_ipd_authoring.py tests/test_ipd_lifecycle_cli.py tests/test_plan_priority_required.py`
- Full repository test suite:
  - `python3 -m pytest`
- Plan lint and leak-sanitizer checks:
  - `aw ipd lint --citation-anchors --detail`
  - `aw sanitize --agent`

## Spec / documentation sync

- N/A with reason: `docs/cli-output-contract.md` and `docs/cli-agent-protocol.md` already specify that exit-code-2 (`cannot-run`) refusals under `--agent` and `--json` emit an `aw.agent/v1` `kind: "error"` record on stdout, and `CHANGELOG.md` under `## 2.0.0 (pending)` already includes the user-facing bullet `- Fixed: usage errors such as a missing required argument or an invalid choice now emit an aw.agent/v1 cannot-run error record on stdout under --agent and --json.` (added in `0z7ds3`).

## Open questions

### OQ-01: How should `ipd_authoring.run_scaffold` emit `cannot-run` records under `--agent` and `--json` without breaking existing human-mode tests that capture `stdout`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolve `ctx = select_output(args)` at entry in `ipd_authoring.run_scaffold` (`agent_workflows/ipd_authoring.py`, line 434). When `ctx.is_agent or ctx.is_json`, write the `error: ...` (and any `note: ...`) line to `sys.stderr` and return `emit_usage_refusal("ipd scaffold", msg, "aw ipd scaffold --help", ctx)` so stdout contains only the `aw.agent/v1` `cannot-run` JSON/JSONL record. When `not ctx.is_agent and not ctx.is_json` (`HUMAN` mode), keep `print(f"error: {msg}")` and `print(f"note: ...")` on `sys.stdout` so existing human-mode tests in `tests/test_ipd_authoring.py` and `tests/test_ipd_lifecycle_cli.py` remain 100% green.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Paste the command and output from the baseline probe driving `cli.main` across `backlog.run_new`, `specs.run_new`, `prompts.run_new`, and `ipd_authoring.run_scaffold` under `--agent` together with the baseline `python3 -m pytest tests/test_usage_refusal_agent_record.py tests/test_backlog_descriptive_safety.py tests/test_specs_date_containment.py tests/test_ipd_authoring.py` pass summary recorded during `E-01`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Run a Python verification command invoking `backlog.run_new` / `cli.main` (updated by `E-02` in `agent_workflows/backlog.py`) across all 11 newly wired refusal arms under `--agent`, `--json`, and human mode, asserting `rc == 2`, in `--agent` `agent_schema.validate_agent_record(json.loads(stdout)) == []` with `cmd == "backlog new"`, `kind == "error"`, `outcome == "cannot-run"`, `exit == 2`, `next == "aw backlog new --help"`; in `--json` one JSON object with `status == "cannot-run"`, `exit_code == 2`, and `next_actions[*].command == "aw backlog new --help"`; and `stdout == ""` in human mode; paste the command and its output.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Run a Python verification command invoking `specs.run_new` / `cli.main` (updated by `E-03` in `agent_workflows/specs.py`) across all 5 newly wired refusal arms (`_title_err`, `_summary_err`, lexical `--date`, calendar-invalid `--date 9999-99-99`, and destination-containment `ValueError`) under `--agent`, `--json`, and human mode, asserting `rc == 2`, in `--agent` `agent_schema.validate_agent_record(json.loads(stdout)) == []` with `cmd == "specs new"`, `kind == "error"`, `outcome == "cannot-run"`, `exit == 2`, `next == "aw specs new --help"`; in `--json` one JSON object with `status == "cannot-run"`, `exit_code == 2`, and `next_actions[*].command == "aw specs new --help"`; and `stdout == ""` in human mode; paste the command and its output.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Run a Python verification command invoking `prompts.run_new` / `cli.main` (updated by `E-04` in `agent_workflows/prompts.py`) across all 5 newly wired refusal arms (post-kebab empty `--slug=---`, unrecognized `--kind`, invalid `--date`, invalid `--time`, and invalid `--set`) under `--agent`, `--json`, and human mode, asserting `rc == 2`, in `--agent` `agent_schema.validate_agent_record(json.loads(stdout)) == []` with `cmd == "prompts new"`, `kind == "error"`, `outcome == "cannot-run"`, `exit == 2`, `next == "aw prompts new --help"`; in `--json` one JSON object with `status == "cannot-run"`, `exit_code == 2`, and `next_actions[*].command == "aw prompts new --help"`; and `stdout == ""` in human mode; paste the command and its output.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Run a Python verification command invoking `ipd_authoring.run_scaffold` / `cli.main` (updated by `E-05` in `agent_workflows/ipd_authoring.py`) across all 13 validation refusal arms (the two CLI-unreachable ones via direct `run_scaffold` calls) plus the normalized-author success case under `--agent`, `--json`, and human mode, asserting `rc == 2`, in `--agent` `agent_schema.validate_agent_record(json.loads(stdout)) == []` with `cmd == "ipd scaffold"`, `kind == "error"`, `outcome == "cannot-run"`, `exit == 2`, `next == "aw ipd scaffold --help"`; in `--json` one JSON object with `status == "cannot-run"`, `exit_code == 2`, and `next_actions[*].command == "aw ipd scaffold --help"`; and `stdout.startswith("error: ")` in human mode, and the success case emitting exactly one stdout line with the `note:` on stderr; paste the command and its output.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Run `python3 -m pytest tests/test_backlog_descriptive_safety.py` (updated by `E-06`) and paste the actual runner output showing all tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the pre-change RED run of the new cases (pasted, failing on empty or `error:` stdout), and the post-change `python3 -m pytest -o addopts="" -v tests/test_usage_refusal_agent_record.py` output listing each new case passing.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" tests/test_usage_refusal_agent_record.py tests/test_backlog_descriptive_safety.py tests/test_specs_date_containment.py tests/test_ipd_authoring.py tests/test_ipd_lifecycle_cli.py tests/test_plan_priority_required.py` (0 failed), the execution-base and post-change bare `python3 -m pytest` summary lines and failure lists showing zero new failures by node id, `aw sanitize --agent` with `outcome: clean`, and `git log -n 1 --stat` showing only declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`- Status: approved`). Open questions: all resolved. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit xvv7n4 -- <paths>`, verifying `git diff --cached --name-only` first; never `git add -A`, never push. Paste the actual runner output for every test claim; a claim without pasted output is not evidence. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize xvv7n4` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `Result: pass`.
