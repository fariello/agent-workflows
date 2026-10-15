# IPD: Honor the shared --fields projection under --agent across the nine unprojected leaves

- Date: 2026-10-14
- Kind: child
- Concern: Nine CLI leaves accept the shared `--fields` flag declared on `cli._build_parser`'s `common` parent yet emit unprojected terminal records under `--agent`, violating `docs/cli-output-contract.md` Section 6 and forcing agent callers to pay for unrequested tokens: `ipd coverage` (`[detail, summary]`), `partition` (`[commands, cycles, shards, split_components]` on exit 0 and `[blocked_sets]` on exit 2), `oc update-models` (`[findings]`), `storage reattach` (`[findings]`), and `upgrade-test env`, `list`, `probe`, `sandboxes`, and `clean` (`[findings]`). All nine are currently registered as strict-xfail ceiling entries in `tests/test_shared_flag_honored.KNOWN_BROKEN` citing backlog `aws1tg`.
- Scope: Fix the five distinct bypass mechanisms across those nine leaves (plus `upgrade-test new` and the `oc sync-models` alias, which share the same handlers) so every `aw.agent/v1` terminal record they emit under `--agent` filters through `agent_schema.filter_record_fields` when `--fields` is supplied, while leaving `--json` payloads unprojected. Remove the nine `(leaf, "--fields"): "aws1tg"` entries from `tests/test_shared_flag_honored.KNOWN_BROKEN` and add branch-complete behavioral regression coverage (present without `--fields`, absent with `--fields`) in `tests/test_shared_flag_honored.py`. EXCLUDES the five `--json` parseability failures owned by `jfdk7p` and the four parser usage-refusal `--fields` failures owned by `4y614a`.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/oc_models.py, agent_workflows/orchestrator_readiness.py, agent_workflows/partition.py, agent_workflows/upgrade_rehearsal.py, tests/test_shared_flag_honored.py, .aw/records/plans/pending/20261014-aws1tg-01-83ns86-honor-the-shared-fields-projection-under-agent-across-the-ni.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: aws1tg
- Blocks-Release: next
- Set: aws1tg
- Order: 1
- Highest E allocated: 07
- Author: agy/gemini-4-argon-high
- Id: 83ns86

## Workflow history
- 2026-10-15 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-14 to-review (agy/gemini-4-argon-high): Authored review-ready child IPD from backlog item aws1tg

- 2026-10-14 draft (agy/gemini-4-argon-high): created.

## Goal

Make all nine `aws1tg` CLI leaves honor `--fields` projection under `--agent` as promised by `docs/cli-output-contract.md` Section 6, and retire their nine `"aws1tg"` entries from the `tests/test_shared_flag_honored.KNOWN_BROKEN` ceiling so the CI gate enforces projection on them directly.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure baseline and fix the five bypass mechanisms

- [ ] E-01 RE-DERIVE at execution HEAD, and record the HEAD sha, the three baseline facts this plan rests on rather than trusting the authoring-time measurements. (1) Run `tests.conformance_matrix.run_cli` with `["--agent", "--fields", "cmd"]` across all nine leaves (`ipd coverage`, `partition`, `upgrade-test env`, `upgrade-test list`, `upgrade-test probe`, `upgrade-test sandboxes` in the read universe, and `oc update-models`, `storage reattach`, `upgrade-test clean` inside a `clone_isolated_project` of `build_installed_project_template`, with `RUNNABLE_ARGV` extras) and record each leaf's exit code and unrequested keys outside `agent_schema._PRESERVED_FIELDS | {"cmd"}`. SAFETY (review PR-001): `oc update-models` WRITES the resolved OpenCode config by default (`--dry-run` previews) and fetches over the network; with no `--config` it resolves `$OPENCODE_CONFIG`, a project `opencode.json`, `$XDG_CONFIG_HOME`, then `~/.config/opencode/opencode.json`, i.e. the operator's REAL config. Every `oc update-models` / `oc sync-models` / `oc_models.run` invocation in this plan (measurement, demonstration, or test) MUST pass `--config <tmp>/opencode.json` pointing at a throwaway file AND either `--dry-run` or an in-process `fetch=` stub (as `tests/test_oc_models.py` does), and any subprocess form MUST run with an isolated `HOME`/`XDG_CONFIG_HOME` (the `clone_isolated_project` env). Never run it bare. (2) Run `python3 -m pytest tests/test_shared_flag_honored.py -k "fields"` and confirm the nine `aws1tg` cases report `XFAIL`. (3) Inspect the five code sites named in F-02..F-06 and mark each fact CONFIRMED or CORRECTED against F-01..F-06.
  - Depends on: none
  - Expected outcome: execution HEAD sha recorded, all nine leaves' unrequested keys and `XFAIL` status pasted, and F-01..F-06 marked CONFIRMED or CORRECTED.
  - Execution state: pending

- [ ] E-02 FIX `ipd coverage` (`agent_workflows/orchestrator_readiness.py`) so `run_coverage` honors `--fields` under `--agent`. In `orchestrator_readiness.run_coverage`, `ctx = context or select_output(args)` is already resolved; at all five `if ctx.is_agent or ctx.is_json:` emission sites (the four `cannot-run` exit-2 branches — no project root, no targets, no matching plans, no orchestrator plans — and the normal exit-0/1 branch emitting `summary` and `data`), filter `rec` through `_as.filter_record_fields(rec, ctx.fields)` when `ctx.is_agent and ctx.fields` before `print(_as.render_jsonl_record(rec), end="")` (for example via a local `_emit_coverage_machine(rec: dict[str, Any]) -> None` helper inside `run_coverage`). Keep `--json` (`ctx.is_json`) unprojected so `aw ipd coverage ... --json` continues to emit the full record. Do NOT change `orchestrator_readiness.render_agent`: `run_coverage` never calls it (its only caller is `tests/test_orchestrator_child_retired.py`), so it emits nothing to a `--fields` user and a `fields` parameter there would be unused surface (review PR-002).
  - Depends on: E-01
  - Expected outcome: all five machine emission sites in `orchestrator_readiness.run_coverage` project via `agent_schema.filter_record_fields` when `ctx.is_agent and ctx.fields`, while `--json` remains unprojected and `render_agent` is unchanged.
  - Execution state: pending

- [ ] E-03 FIX `partition` (`agent_workflows/partition.py`) so `run_partition` honors `--fields` on both of its `--agent` emission branches. `cli._run_partition` already passes `context=context` to `partition.run_partition(args, term, context=context)`, which currently ignores `context`. Resolve `fields` in `run_partition` from `getattr(context, "fields", None)` when `context is not None`, falling back to `select_output(args).fields` when `context is None` (or parsing `getattr(args, "fields", None)` via `select_output`). At BOTH `if is_agent:` sites in `run_partition` — the `blocked_sets` whole-batch refusal (`outcome: "cannot-run"`, exit 2, carrying `blocked_sets`) and the normal partition completion (`outcome: "ok"`, exit 0, carrying `shards`, `commands`, `split_components`, `cycles`, and optional `held_back_orchestrators`) — apply `record = agent_schema.filter_record_fields(record, fields)` when `fields` is truthy before `sys.stdout.write(agent_schema.render_jsonl_record(record))`. Leave both `if is_json:` branches unprojected.
  - Depends on: E-01
  - Expected outcome: both `if is_agent:` branches in `partition.run_partition` project through `agent_schema.filter_record_fields` when `--fields` is supplied, and `--json` output is unchanged.
  - Execution state: pending

- [ ] E-04 FIX `oc update-models` and its `oc sync-models` alias (`agent_workflows/cli.py` and `agent_workflows/oc_models.py`) by threading the resolved `OutputContext` into `oc_models.run` and declaring `--fields` on `oc_models.build_parser()`. Give `oc_models.run` an optional keyword parameter `context: Optional[Any] = None` (preserving its existing `(argv=None, fetch=None, env=None)` positional signature for `tests/test_oc_models.py` and `oc_models.main`), resolve `ctx = context if context is not None else select_output(args)` inside `oc_models.run`, and pass `context=context` at the `if oc_cmd in ("update-models", "sync-models"):` dispatch site in `cli._dispatch`. Also add `parser.add_argument("--fields", default=None, help=argparse.SUPPRESS)` to `oc_models.build_parser()` so direct `oc_models.run(argv)` callers passing `--agent --fields ...` without a pre-resolved `context` also project. Every machine branch in `oc_models.run` already emits via `get_renderer(ctx).emit(res, ctx)` -> `CommandResult.to_agent_record(context=ctx)`, so all six branches honor `ctx.fields` once `ctx` carries it. SAFETY (review PR-001): `oc update-models` WRITES the resolved OpenCode config by default (`--dry-run` previews) and fetches over the network; with no `--config` it resolves `$OPENCODE_CONFIG`, a project `opencode.json`, `$XDG_CONFIG_HOME`, then `~/.config/opencode/opencode.json`, i.e. the operator's REAL config. Every `oc update-models` / `oc sync-models` / `oc_models.run` invocation in this plan (measurement, demonstration, or test) MUST pass `--config <tmp>/opencode.json` pointing at a throwaway file AND either `--dry-run` or an in-process `fetch=` stub (as `tests/test_oc_models.py` does), and any subprocess form MUST run with an isolated `HOME`/`XDG_CONFIG_HOME` (the `clone_isolated_project` env). Never run it bare.
  - Depends on: E-01
  - Expected outcome: `cli._dispatch` passes `context=context` to `oc_models.run`, `oc_models.build_parser()` accepts `--fields`, and `oc update-models` / `oc sync-models` project records under `--agent --fields`.
  - Execution state: pending

- [ ] E-05 FIX `storage reattach` (`agent_workflows/cli.py`) so `_StorageReattachResult.to_agent_record` honors `context.fields` and `cli._dispatch` threads `context=context`. In `cli._run_storage_reattach`, update `_StorageReattachResult.to_agent_record(self, context=None)` to import `filter_record_fields` from `agent_workflows.agent_schema` and apply `if context is not None and context.fields: rec = filter_record_fields(rec, context.fields)` before `assert_valid_agent_record(rec)`, matching `CommandResult.to_agent_record`. At the `if storage_cmd == "reattach":` branch in `cli._dispatch`, pass `context=context` to `_run_storage_reattach(args, term, context=context)`.
  - Depends on: E-01
  - Expected outcome: `_StorageReattachResult.to_agent_record` projects `rec` when `context.fields` is set, and `cli._dispatch` passes `context=context` to `_run_storage_reattach`.
  - Execution state: pending

- [ ] E-06 FIX the `upgrade-test` family (`agent_workflows/upgrade_rehearsal.py` and `agent_workflows/cli.py`) so `_emit_agent` propagates `--fields` across every subcommand and error handler without altering `--json` behavior. Add an optional `args: Optional[argparse.Namespace] = None` parameter to `upgrade_rehearsal._emit_agent` and pass `fields=getattr(args, "fields", None)` into the `argparse.Namespace(agent=True, json=False, no_color=False, color=False, fields=getattr(args, "fields", None))` argument of `select_output`. Pass `args=args` at all ten `_emit_agent` call sites (nine in `upgrade_rehearsal.py`, one in `cli.py`; re-count at execution with `grep -n "_emit_agent(" agent_workflows/upgrade_rehearsal.py agent_workflows/cli.py`): `cmd_list`, `cmd_new`, `cmd_sandboxes`, `cmd_probe`, `cmd_env`, all three `--agent` branches of `cmd_clean` (empty targets, preview without `-y`, and post-clean results), `upgrade_rehearsal.main`'s `except HarnessError` handler, and `cli._dispatch`'s `except upgrade_rehearsal.HarnessError` handler. Also add `common.add_argument("--fields", default=argparse.SUPPRESS, help="Comma-separated field projection for --agent output.")` to `upgrade_rehearsal.build_parser()`'s `common` parent so standalone `upgrade_rehearsal.main(argv)` calls accept `--fields`. Do NOT modify any `--json` branch in `upgrade_rehearsal.py` (owned by `jfdk7p`).
  - Depends on: E-01
  - Expected outcome: `upgrade_rehearsal._emit_agent` threads `fields` from `args` into `select_output` at all ten call sites, standalone `upgrade_rehearsal.build_parser()` accepts `--fields`, and `upgrade-test env`, `list`, `probe`, `sandboxes`, `clean`, and `new` project under `--agent --fields` while `--json` behavior is untouched.
  - Execution state: pending

### Task group 2: Retire the KNOWN_BROKEN ceiling entries, add branch coverage, and verify sensitivity

- [ ] E-07 RETIRE the nine `aws1tg` entries from `tests/test_shared_flag_honored.KNOWN_BROKEN`, add branch-level behavioral regression tests, prove mutation sensitivity, and run the bare test suite. (1) Remove the nine `(leaf, "--fields"): "aws1tg"` entries from `KNOWN_BROKEN` in `tests/test_shared_flag_honored.py` (leaving `jfdk7p` and `4y614a` entries untouched; if `KNOWN_BROKEN` is empty at execution time because both sibling items already landed, drop the `assert seen_citations` guard in `test_known_broken_citations_resolve` so an empty ceiling is valid). (2) Add behavioral tests in `tests/test_shared_flag_honored.py` asserting both presence (without `--fields`) and absence (with `--agent --fields cmd`) of unrequested domain keys across the branches the sweep's single `RUNNABLE_ARGV` invocation per leaf does not reach: (a) `ipd coverage` on the exit-2 `cannot-run` path (`detail`/`summary` omitted under `--fields cmd`, `summary` retained and `detail` omitted under `--fields cmd,summary`, both present without `--fields`, and `--json --fields cmd` still carrying both) and on the exit-0/1 completion path (`data`/`summary` omitted under `--fields cmd`, present without), driving `cli.main` in-process with `runner_shared.ask_orchestrator_probe` patched as `tests/test_coverage_not_written.py` does so no model is called; (b) `partition` on BOTH `if is_agent:` branches — normal exit-0 `outcome: "ok"` (`shards`, `commands`, `split_components`, `cycles` omitted under `--fields cmd`, present without `--fields`) and blocked-Set exit-2 `outcome: "cannot-run"` (`blocked_sets` omitted under `--fields cmd`, present without `--fields`; reuse the incomplete-Set fixture shape of `tests/test_partition_set_cohesion.py` `cohesion_repo` / `test_agent_refusal_record`) — plus confirming `partition --json --fields cmd` remains unprojected; (c) `oc update-models`, its `oc sync-models` alias, and standalone `oc_models.run(["--config", <tmp>, "--dry-run", "--agent", "--fields", "cmd"], fetch=<stub>)` (`findings` omitted under `--fields cmd`, present without `--fields`), every form honoring the E-04 SAFETY rule (temp `--config`, `--dry-run` or `fetch=` stub, isolated `HOME`/`XDG_CONFIG_HOME`); (d) `storage reattach` on the missing-`--companion-dir` `_StorageReattachResult` exit-1 branch (`findings` omitted under `--fields cmd`, present without; that record carries no `evidence`) and, as a regression guard for the already-projecting path, the `--dry-run --companion-dir` `CommandResult` exit-0 branch (`findings`/`evidence` omitted under `--fields cmd`, present without; review probe showed this branch already projects); and (e) standalone `upgrade_rehearsal.main(["list", "--agent", "--fields", "cmd"])` (`findings` omitted under `--fields cmd`, present without `--fields`). (3) Prove mutation sensitivity via a restoring `try/finally` wrapper on disk: temporarily revert the `filter_record_fields` call in `_StorageReattachResult.to_agent_record` (or `partition.run_partition`), run `python3 -m pytest tests/test_shared_flag_honored.py -k "storage_reattach or partition"`, confirm the corresponding case FAILS, restore the original bytes, and verify matching before/after `sha256`. (4) Run `python3 -m pytest tests/test_shared_flag_honored.py` and then the full fast suite BARE as `python3 -m pytest`, pasting the actual runner output.
  - Depends on: E-02, E-03, E-04, E-05, E-06
  - Expected outcome: all nine `aws1tg` leaves pass directly in `tests/test_shared_flag_honored.py` (no longer xfailed), branch-level presence/absence tests pass, mutation sensitivity is demonstrated with matching before/after `sha256`, and the bare `python3 -m pytest` suite passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `GUIDING_PRINCIPLES.md` P16: tests must exercise real code and assert observable outcomes (parsed stdout records, exit codes, and both presence without `--fields` and absence with `--fields` so a vacuous projection cannot pass), never inspecting source text via `ast`, `inspect`, or regex.
- `docs/cli-output-contract.md` Section 6 specifies that `--fields <list>` projects `aw.agent/v1` records down to requested fields while preserving `agent_schema._PRESERVED_FIELDS` (`schema, kind, cmd, exit, outcome, complete, verified, applied, total, emitted, omitted, next`). `--fields` scopes to `--agent` output; `--json` emits full unprojected payloads (`wyy09f` F-09 / E-03).
- `tests/test_shared_flag_honored.KNOWN_BROKEN` is a strict-xfail (`pytest.mark.xfail(strict=True)`) ceiling: fixing any of the nine `aws1tg` leaves without removing its `(leaf, "--fields"): "aws1tg"` entry turns the test suite red with `XPASS(strict)`.
- `oc update-models` writes the operator's real OpenCode config unless given `--config` and `--dry-run` (measured at review: a bare `aw oc update-models --agent --fields cmd` returned `applied:true` and rewrote `~/.config/opencode/opencode.json`, which the reviewer restored from the `.bak` it wrote). See the E-04 SAFETY rule.
- The established pattern for commands with an inner `main`/`run` entry point (`wyy09f` E-04 on `leak_sanitizer.main`) is to thread the already-resolved `OutputContext` from `cli.main` as an optional `context=None` parameter while preserving the standalone `argv` signature for direct callers.

## Findings

| Id | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-01 | All nine `aws1tg` leaves reproduce at authoring HEAD `b685776fb54713fc0b6619051824a78193411bb2` with the exact unrequested keys recorded in `aws1tg`. | Running `tests.conformance_matrix.run_cli` with `["--agent", "--fields", "cmd"]`: `ipd coverage` rc 2 extra `['detail', 'summary']`; `partition` rc 0 extra `['commands', 'cycles', 'shards', 'split_components']`; `upgrade-test env` rc 2, `list` rc 0, `probe` rc 2, `sandboxes` rc 0, `clean` rc 0, `oc update-models` rc 2, `storage reattach` rc 1 all extra `['findings']`. | All nine leaves in `aws1tg` are live defects and in scope. |
| F-02 | `orchestrator_readiness.run_coverage` resolves `ctx = context or select_output(args)` but bypasses `agent_schema.filter_record_fields` at all five `if ctx.is_agent or ctx.is_json:` emission sites. | `orchestrator_readiness.run_coverage` constructs `rec = {"schema": _as.SCHEMA_VERSION, "kind": "result", "cmd": "ipd coverage", ...}` at four exit-2 `cannot-run` branches (carrying `summary` and `detail`) and one exit-0/1 completion branch (carrying `summary` and `data`), calling `print(_as.render_jsonl_record(rec), end="")` directly. `orchestrator_readiness.render_agent` likewise returns an unprojected dict. | E-02 filters `rec` through `_as.filter_record_fields(rec, ctx.fields)` when `ctx.is_agent and ctx.fields` across all five sites; `render_agent` is not on the CLI path and is left unchanged (review PR-002). |
| F-03 | `partition.run_partition` accepts `context: Any = None` from `cli._run_partition` but never consults `context.fields`, emitting unprojected records at both `if is_agent:` branches. | `partition.run_partition` has two `if is_agent:` sites: the `blocked_sets` whole-batch refusal (exit 2, `outcome: "cannot-run"`, emitting `blocked_sets`, which `cgsrnb` V-01 observed when an approved Set was incomplete) and the normal partition return (exit 0, `outcome: "ok"`, emitting `shards`, `commands`, `split_components`, `cycles`, and optional `held_back_orchestrators`). Both call `sys.stdout.write(agent_schema.render_jsonl_record(record))` directly. | E-03 filters `record` through `agent_schema.filter_record_fields` at both `if is_agent:` sites, and E-07 tests both branches. |
| F-04 | `cli._dispatch` for `oc update-models` (and `oc sync-models`) has the same argv-reserialization seam `wyy09f` fixed for `check-local-leaks`: it builds `forwarded = []` omitting `--fields` and calls `oc_models.run(forwarded)` without `context=context`. | In `cli._dispatch` (`if oc_cmd in ("update-models", "sync-models"):`), `forwarded` copies `--config`, `--apply`, `--dry-run`, `--no-backup`, `--allow-insecure`, `--agent`, `--json`, and `--no-color`, dropping `--fields`. `wyy09f` F-05's `grep -n "passthrough"` missed this site because the list is named `forwarded`. Inside `oc_models.run`, every machine branch already calls `get_renderer(ctx).emit(res, ctx)` on a `CommandResult`. | E-04 threads `context=context` into `oc_models.run` and declares `--fields` on `oc_models.build_parser()` for standalone callers. |
| F-05 | `cli._run_storage_reattach` defines a local `CommandResult` subclass `_StorageReattachResult` whose overridden `to_agent_record(self, context=None)` omits `filter_record_fields`. | `_StorageReattachResult.to_agent_record` in `cli._run_storage_reattach` builds `rec` with `"findings": 0` and calls `assert_valid_agent_record(rec)` without the `if context is not None and context.fields: rec = _schema.filter_record_fields(rec, context.fields)` step present in `CommandResult.to_agent_record`. It is the only `to_agent_record` override in `agent_workflows/`. Review probe: only this exit-1 branch is unprojected (extra `findings`); the `--dry-run` `CommandResult` branch already projects because `ctx = context or select_output(args)` reads `args.fields`. | E-05 adds `filter_record_fields` to `_StorageReattachResult.to_agent_record` and passes `context=context` at `cli._dispatch`. |
| F-06 | `upgrade_rehearsal._emit_agent` constructs a synthetic `argparse.Namespace(agent=True, json=False, no_color=False, color=False)` without `fields`, dropping `args.fields` across all `upgrade-test` subcommands and `HarnessError` handlers. | `upgrade_rehearsal._emit_agent` is called at ten sites (`cmd_list`, `cmd_new`, `cmd_sandboxes`, `cmd_probe`, `cmd_env`, three branches of `cmd_clean`, `upgrade_rehearsal.main`'s `except HarnessError`, and `cli._dispatch`'s `except upgrade_rehearsal.HarnessError`). Passing `args=args` into `_emit_agent` and `fields=getattr(args, "fields", None)` into the namespace lets `select_output` and `CommandResult.to_agent_record` project without touching any `--json` branch. | E-06 threads `args=args` into `_emit_agent` at all ten sites and adds `--fields` to `upgrade_rehearsal.build_parser()`'s `common` parent. |

## Proposed changes (ordered, validatable)

1. Re-measure all nine leaves under `--agent --fields cmd` and confirm the five root-cause mechanisms at execution HEAD (E-01).
2. Filter `ipd coverage` agent records through `agent_schema.filter_record_fields` at all five emission sites in `orchestrator_readiness.run_coverage` (E-02).
3. Filter `partition` agent records through `agent_schema.filter_record_fields` at both `if is_agent:` sites in `partition.run_partition` (E-03).
4. Thread `context=context` from `cli._dispatch` into `oc_models.run` and declare `--fields` on `oc_models.build_parser()` (E-04).
5. Apply `agent_schema.filter_record_fields` inside `_StorageReattachResult.to_agent_record` and pass `context=context` to `_run_storage_reattach` in `cli._dispatch` (E-05).
6. Thread `args=args` into `upgrade_rehearsal._emit_agent` across all ten call sites in `upgrade_rehearsal.py` and `cli.py`, and declare `--fields` on `upgrade_rehearsal.build_parser()`'s `common` parent (E-06).
7. Remove the nine `"aws1tg"` entries from `tests/test_shared_flag_honored.KNOWN_BROKEN`, add branch-level presence/absence tests, verify mutation sensitivity with a restoring wrapper, and run the bare suite (E-07).

## Deferred / out of scope (with reason)

- THE FIVE LEAVES THAT FAIL `json.loads` UNDER `--json` (`config get`, `config is`, `upgrade-test env`, `upgrade-test probe`, `upgrade-test clean`). Separate defect population with its own open release-blocking backlog item and its own `("--json"): "jfdk7p"` entries in `tests/test_shared_flag_honored.KNOWN_BROKEN`; modifying `--json` branches here would cross into `jfdk7p`'s scope and trigger strict-xfail `XPASS` failures on those entries.
  - Carrier: jfdk7p
- THE FOUR LEAVES WHERE PARSER USAGE REFUSAL FOR MISSING REQUIRED ARGUMENTS IGNORES `--fields` (`ipd scaffold`, `research new`, `research new-comparison`, `storage move`). Filed during `cgsrnb` E-01 as a separate open release-blocking bug in `cli._build_parser`'s `ArgumentParser.error` path and registered in `KNOWN_BROKEN` citing `4y614a`.
  - Carrier: 4y614a

## Scope check

- Over-scope: none. Every file in `Scope-Paths` directly houses one of the five bypass mechanisms (`agent_workflows/orchestrator_readiness.py`, `agent_workflows/partition.py`, `agent_workflows/oc_models.py`, `agent_workflows/upgrade_rehearsal.py`, `agent_workflows/cli.py`), the `KNOWN_BROKEN` ceiling and behavioral regression tests (`tests/test_shared_flag_honored.py`), or this plan itself.
- Under-scope: none for `aws1tg`. All nine leaves named in `aws1tg` (plus `upgrade-test new` and the `oc sync-models` alias, which share `_emit_agent` and `oc_models.run` respectively) are fixed and tested across both their sweep paths and their non-sweep branches.

## Required tests / validation

- `python3 -m pytest tests/test_shared_flag_honored.py` passing with all nine `aws1tg` entries removed from `KNOWN_BROKEN` (zero `aws1tg` xfails remaining) and all new branch-level presence/absence regression tests passing (E-07).
- Direct behavioral verification of both presence (without `--fields`) and absence (under `--agent --fields cmd`) of unrequested domain keys across `ipd coverage` (exit-2 `cannot-run` and exit-0/1 completion with the probe patched), `partition` (both exit-0 `ok` and exit-2 `blocked_sets` branches, plus `--json` unprojected), `oc update-models` / `oc sync-models` / standalone `oc_models.run` (temp `--config` and `--dry-run` or `fetch=` stub only), `storage reattach` (`_StorageReattachResult` exit-1 and `CommandResult` `--dry-run` exit-0), and `upgrade-test` (`env`, `list`, `probe`, `sandboxes`, `clean`, and standalone `upgrade_rehearsal.main`) (E-02..E-07).
- Mutation-sensitivity proof using a restoring `try/finally` wrapper showing `tests/test_shared_flag_honored.py` fails when a fix is reverted and passes after restoration with matching before/after `sha256` (E-07).
- Full fast test suite run BARE via `python3 -m pytest` with the `N passed` summary pasted (E-07).

## Spec / documentation sync

N/A with reason: no `.spec.md` or user-facing documentation file is modified. `docs/cli-output-contract.md` Sections 1.3 and 6 already specify that every leaf declaring `--fields` on the shared `common` parent projects `aw.agent/v1` records down to the requested fields plus `agent_schema._PRESERVED_FIELDS` and already names `tests/test_shared_flag_honored.py` as the enforcing gate; this plan brings the nine non-conforming leaves into compliance with the existing contract.

## Open questions

### OQ-01: Should `orchestrator_readiness.run_coverage` and `partition.run_partition` apply `--fields` projection under `--json` as well as `--agent`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE toward scoping `--fields` projection strictly to `--agent` (`ctx.is_agent` / `is_agent`) and leaving `--json` unprojected. Both the `--fields` flag help text (`"Comma-separated field projection for --agent output (envelope fields are preserved)"`) and `docs/cli-output-contract.md` Section 6 specify that `--fields` is an `aw.agent/v1` token-control projection while `--json` emits the full unprojected payload (`wyy09f` F-09 / E-03 verified that `JsonRenderer` never calls `filter_record_fields`). Filtering only when `ctx.is_agent` (or `is_agent`) keeps both commands aligned with the rest of the CLI.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: The execution HEAD sha; pasted output of running the nine `aws1tg` leaves through `tests.conformance_matrix.run_cli` with `["--agent", "--fields", "cmd"]` showing each leaf's exit code and unrequested keys prior to the fix; pasted `python3 -m pytest tests/test_shared_flag_honored.py -k "fields"` output showing the nine `aws1tg` cases as `XFAIL`; and an explicit CONFIRMED or CORRECTED mark for each of F-01..F-06.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Diff or excerpt of `agent_workflows/orchestrator_readiness.py` showing `filter_record_fields` applied across all five `run_coverage` emission sites when `ctx.is_agent and ctx.fields` and `render_agent` unchanged; plus pasted output from `cli.main` / `orchestrator_readiness` showing `aw ipd coverage --agent --fields cmd` emits only preserved keys (`detail` and `summary` absent), `aw ipd coverage --agent --fields cmd,summary` retains `summary` while omitting `detail`, `aw ipd coverage --agent` (without `--fields`) still emits both `detail` and `summary`, `aw ipd coverage --json --fields cmd` remains unprojected, and the patched-probe exit-0/1 completion record omits `data`/`summary` under `--fields cmd`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Diff or excerpt of `agent_workflows/partition.py` showing `agent_schema.filter_record_fields` applied at both `if is_agent:` sites in `run_partition`; plus pasted output demonstrating that on BOTH branches — normal `outcome: "ok"` (exit 0) and `blocked_sets` `outcome: "cannot-run"` (exit 2) — `--agent --fields cmd` omits the domain keys (`shards`, `commands`, `split_components`, `cycles` on exit 0; `blocked_sets` on exit 2) while `--agent` without `--fields` includes them and `--json --fields cmd` remains unprojected.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Diff or excerpt of `agent_workflows/cli.py` and `agent_workflows/oc_models.py` showing `context=context` passed at `cli._dispatch` (`if oc_cmd in ("update-models", "sync-models"):`), `context: Optional[Any] = None` accepted in `oc_models.run`, and `--fields` declared on `oc_models.build_parser()`; plus pasted output, from invocations that each carry a temp `--config` and `--dry-run` (or a `fetch=` stub) and leave the operator's real OpenCode config untouched (paste `sha256sum` of the resolved real config before and after, or show `$HOME`/`XDG_CONFIG_HOME` pointed at a temp dir), showing `oc update-models` (and `oc sync-models` and standalone `oc_models.run`) omits `findings` under `--agent --fields cmd` and includes `findings` under `--agent` without `--fields`, and that `python3 -m pytest tests/test_oc_models.py` passes.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Diff or excerpt of `agent_workflows/cli.py` showing `filter_record_fields` in `_StorageReattachResult.to_agent_record` and `context=context` passed at `if storage_cmd == "reattach":`; plus pasted output showing `aw storage reattach --agent --fields cmd` (exit 1) and `aw storage reattach --companion-dir <tmp> --dry-run --agent --fields cmd` (exit 0) emit only preserved envelope keys (exit 1 omitting `findings`; exit 0 omitting `findings`/`evidence`), and include them without `--fields`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Diff or excerpt of `agent_workflows/upgrade_rehearsal.py` and `agent_workflows/cli.py` showing `args=args` threaded into `_emit_agent` across all ten call sites (with the pasted `grep -n "_emit_agent("` count) and `--fields` added to `upgrade_rehearsal.build_parser()`'s `common` parent; plus pasted output showing `upgrade-test env`, `list`, `probe`, `sandboxes`, `clean`, and standalone `upgrade_rehearsal.main(["list", "--agent", "--fields", "cmd"])` omit `findings` under `--agent --fields cmd` and include `findings` under `--agent` without `--fields`, and that `python3 -m pytest tests/test_aw_upgrade_test.py` passes.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Pasted `python3 -m pytest tests/test_shared_flag_honored.py` output showing all nine `aws1tg` leaves passing (and any remaining `jfdk7p`/`4y614a` entries still xfailing cleanly); pasted output of the restoring-wrapper mutation check showing a reverted fix causes `tests/test_shared_flag_honored.py` to FAIL and restoration produces the exact pre-mutation `sha256`; and pasted output of the bare full fast suite `python3 -m pytest` showing the `N passed` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (standing rules from `AGENTS.md` and `.aw/records/plans/README.md`):
1. All open questions are RESOLVED (OQ-01 is resolved above).
2. Scope fence (a declaration, not a stop condition): changes are limited to `Scope-Paths` (`agent_workflows/cli.py`, `agent_workflows/oc_models.py`, `agent_workflows/orchestrator_readiness.py`, `agent_workflows/partition.py`, `agent_workflows/upgrade_rehearsal.py`, `tests/test_shared_flag_honored.py`, and this plan file). An out-of-scope edit that proves necessary is made and then justified to the finalize scope gate (`--scope-reason`).
2a. Safety: never run `oc update-models` / `oc sync-models` / `oc_models.run` without a temp `--config` and `--dry-run` or a `fetch=` stub (E-04 SAFETY rule); it otherwise rewrites the operator's real OpenCode config and calls the network.
3. Honesty rule (HARD MUST): when reporting tests or validation passed, paste the ACTUAL runner output into each `V-*` item's `Observed evidence:`; never claim success you did not run. Run the full suite bare as `python3 -m pytest`.
4. Commit only the files changed for this plan, path-scoped via `aw commit 83ns86 -- <paths>`, never `git add -A`/`-a`, and never push.
5. Lifecycle: under `aw oc run` / `aw agy run` the runner owns begin/finalize, so do not run `aw ipd finalize` there. In a hand execution, run `aw ipd finalize 83ns86 --actor <agent/model> --message <summary> --apply` once every `V-*` reads `pass` and `aw ipd lint --phase pre-transition --agent` conforms. Never hand-`git mv` the plan to `executed/` or hand-edit `- Status:`.
