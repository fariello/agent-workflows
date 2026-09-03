---
id: tvnq50
created: 20260903
set: rununify
order: 00
topic: [runners, de-duplication, rununify]
model:
kind: findings
status: todo
outcome: none-yet
summary: Function-by-function four-class partition of oc_runipd.py and agy_runipd.py (E-01 of plan 5e4sb6), measured by AST comparison at HEAD 769989ce
consumed-by: []
---

# Runner symbol inventory: the four-class partition

E-01 of plan `5e4sb6` (`rununify-00`). This is the function-by-function inventory backlog item
`dhuape` names as its first required deliverable, and the measurement every child scope in that Set
must be drawn from.

MEASUREMENT HEAD: `769989ce`. Every number below was taken at that commit and WILL move; the
reproduction script is in the Method section so a reader can re-run it rather than trust it.

## Headline: the plan's own numbers were stale, and the shape of the problem changed

The plan quantifies its case at HEAD `c7f41b9`. Re-measured here, four of its five load-bearing
figures moved, and two moved enough to change a decision.

| Quantity | Plan (at `c7f41b9`) | Measured (at `769989ce`) | Consequence |
|---|---|---|---|
| Shared top-level symbols | 72 | **88** | +16 |
| Byte/AST-identical of those | 35 | **33** (+1 host-naming-only = 34) | The "pure move" slice is SMALLER than the plan sized it |
| Diverged of those | 37 | **52** | The hard slice grew by 15 symbols |
| `oc_runipd.py` / `agy_runipd.py` size | 3144 / 3143 lines | **6683 / 4819** | The files are no longer near-equal in size |
| Class (d) re-forks | 4 named (`Palette`, `_one_line`, `_strip_ansi`, `Heartbeat`) | **5**, and NOT the same five | `Heartbeat` is already fixed; two NEW ones found |
| opencode-only / antigravity-only | 5 / 7 | **47 / 3** | Not a symmetric pair of runners any more |

TWO FINDINGS THAT CHANGE A DECISION, not just a number:

1. **`Heartbeat` is no longer a re-fork; it was fixed while the plan sat.** `agy_runipd.py:43` now
   reads `from agent_workflows.render_stream import Heartbeat as Heartbeat`. The plan's child 01, and
   the `stallfp-01` E-05 overlap it warns about, are therefore PARTLY DONE. Child 01 must be
   re-scoped to what is actually left, not executed as written.

2. **`driver_actor` is no longer the "differs only by host naming" case.** The plan states that
   measurement found exactly ONE symbol differing by naming alone, `driver_actor`, and builds the
   host-token-normalization distinction on it. At this HEAD `driver_actor` is STRUCTURALLY diverged
   (8 lines both sides, so a line-count check cannot see it), and the sole host-naming-only symbol is
   now `print_status`. The distinction is still worth making; the example that motivated it is gone.

## The partition

| Class | Meaning | Count | oc lines |
|---|---|---|---|
| (a) COMMON | identical, or identical after host-token normalization | **34** | 551 |
| (b) HOST-SPECIFIC | present on one side only, no other owner | **50** (47 oc, 3 agy) | 1761 oc / 413 agy |
| (c) DIVERGED | present in both, structurally drifted | **52** | 3639 |
| (d) ALREADY-EXTRACTED | a non-runner module already owns matching code | **5** | 6 shared + 28 agy-only |

LINE-MASS ACCOUNTING, which reframes the plan's "roughly 93 percent duplicated" claim: of
`oc_runipd.py`'s 5957 top-level-definition lines, 4196 (**70.4 percent**) sit in shared symbols; of
`agy_runipd.py`'s 4293, 3880 (**90.4 percent**) do. The asymmetry is the story. The antigravity runner
is almost entirely shared logic, while the opencode runner has grown 1761 lines of genuinely
host-specific surface. So this is not two copies of one program any more: it is one shared program
plus an opencode-specific extension.

## Class (d) ALREADY-EXTRACTED: delete these, do not extract them

This is the class a two-runner-only comparison is structurally blind to, and the sweep therefore
compared every runner symbol against ALL of `agent_workflows/*.py`.

| Symbol | Re-forked in | Lines | Owning module | Match |
|---|---|---|---|---|
| `_read_id` | BOTH runners | 3 / 3 | `selectors.py` | AST-identical |
| `_read_status` | BOTH runners | 3 / 3 | `selectors.py` | AST-identical |
| `Palette` | `agy_runipd.py:262` | 20 | `render_stream.py` | AST-identical |
| `_one_line` | `agy_runipd.py:288` | 6 | `render_stream.py` | AST-identical |
| `_strip_ansi` | `agy_runipd.py:284` | 2 | `render_stream.py` | AST-identical |

NOTE ON `resolve_agy`: the raw sweep also flags it as matching `agy_run.py`. It is NOT a re-fork to
delete blindly; `agy_run.py` is the antigravity entry-point module, so the two may legitimately be one
symbol re-exported. Resolve it when child 01 is scoped, and do not let the mechanical match decide it.

METHOD CORRECTION WORTH RECORDING, because the naive sweep gets this wrong: matching on symbol NAME
alone reports 11 shared re-forks including `main`, `build_parser`, `load_state`, `should_color`,
`terminate_process`, `validate_manifest`, `sha256_file`, `_run_git` and `PlanRecord`. Those are NAME
COLLISIONS, not re-forks: nine different modules define a `main`. Only a comparison of the actual code
distinguishes them, which is why the classifier compares normalized AST dumps and not names. A
future executor repeating this sweep by name will "find" nine re-forks that do not exist.

## Class (a) COMMON: the provably behavior-neutral slice

34 symbols, 551 lines. 33 are AST-identical across both runners; `print_status` is identical after
host-token normalization. This is the plan's "pure move, zero reconciliation" slice, and an identity
assertion can verify it.

| Symbol | oc lines | oc:line | agy:line | Sub-class |
|---|---|---|---|---|
| `build_recovery_lane_notice` | 72 | 3716 | 2314 | AST-identical |
| `describe_unresolved_plan_selector` | 53 | 2464 | 1578 | AST-identical |
| `_lane_records_from_state` | 40 | 1526 | 743 | AST-identical |
| `validate_manifest` | 40 | 2422 | 1536 | AST-identical |
| `print_lane_interrupt_report` | 37 | 1834 | 1053 | AST-identical |
| `format_lane_report` | 36 | 1599 | 816 | AST-identical |
| `describe_lane` | 29 | 1568 | 785 | AST-identical |
| `resolve_plan_path` | 28 | 2694 | 1804 | AST-identical |
| `run_checked` | 26 | 497 | 459 | AST-identical |
| `discover_plans` | 22 | 2339 | 1484 | AST-identical |
| `atomic_write_json` | 20 | 2115 | 1293 | AST-identical |
| `resolve_run_dir` | 17 | 6147 | 1886 | AST-identical |
| `allocate_isolation_worktree` | 15 | 1480 | 697 | AST-identical |
| `plan_bucket` | 15 | 2724 | 1838 | AST-identical |
| `should_color` | 11 | 189 | 249 | AST-identical |
| `_run_git` | 10 | 2043 | 1103 | AST-identical |
| `_read_set` | 9 | 2203 | 1372 | AST-identical |
| `git_branch` | 9 | 2083 | 1261 | AST-identical |
| `teardown_isolation_worktree` | 9 | 1497 | 714 | AST-identical |
| `load_json` | 7 | 2106 | 1284 | AST-identical |
| `append_jsonl` | 6 | 2137 | 1315 | AST-identical |
| `sha256_file` | 6 | 2098 | 1276 | AST-identical |
| `disable_lane_prompt` | 4 | 1643 | 860 | AST-identical |
| `git_common_dir` | 4 | 2073 | 1251 | AST-identical |
| `save_state` | 4 | 3047 | 2095 | AST-identical |
| `print_status` | 4 | 6141 | 4331 | host-naming only |
| `_read_order` | 3 | 2214 | 1383 | AST-identical |
| `new_run_id` | 3 | 2765 | 1881 | AST-identical |
| `DriverError` | 2 | 202 | 379 | AST-identical |
| `git_head` | 2 | 2079 | 1257 | AST-identical |
| `git_status` | 2 | 2094 | 1272 | AST-identical |
| `load_state` | 2 | 3043 | 2091 | AST-identical |
| `state_root` | 2 | 2770 | 1877 | AST-identical |
| `utc_now` | 2 | 493 | 455 | AST-identical |

## Class (c) DIVERGED: the actual intellectual work

52 symbols, 3639 oc lines. Sorted by absolute line delta. The last column is the coverage measurement
that makes the plan's F11 concern concrete: `grep -rl <symbol> tests/*.py` versus
`grep -rl <symbol> tests/*agy*`.

| Symbol | oc lines | agy lines | delta | oc:line | agy:line | test files (all/agy) |
|---|---|---|---|---|---|---|
| `run_queue` | 316 | 246 | +70 | 5735 | 4002 | 10/1 |
| `build_parser` | 248 | 218 | +30 | 6185 | 4356 | 17/1 |
| `build_isolation_notice` | 36 | 10 | +26 | 3790 | 2388 | 1/0 |
| `execute_item` | 759 | 739 | +20 | 4780 | 3092 | 8/1 |
| `integrate_lane_branch` | 86 | 66 | +20 | 1955 | 1183 | 0/0 |
| `set_plan_approved` | 77 | 60 | +17 | 534 | 493 | 2/1 |
| `driver_begin` | 48 | 34 | +14 | 688 | 565 | 6/1 |
| `initialize_run` | 181 | 169 | +12 | 2860 | 1920 | 5/1 |
| `_observe_between_turn_stop` | 40 | 29 | +11 | 5670 | 3950 | 1/0 |
| `_record_forced_stop` | 43 | 33 | +10 | 4249 | 2703 | 1/0 |
| `extract_session_id` | 20 | 30 | -10 | 3140 | 2165 | 1/0 |
| `sync_receipt_into_worktree` | 19 | 9 | +10 | 1873 | 1092 | 1/0 |
| `requeue_interrupted` | 43 | 34 | +9 | 5625 | 3914 | 2/0 |
| `run_lock` | 45 | 36 | +9 | 2146 | 1324 | 4/0 |
| `install_stop_triggers` | 41 | 34 | +7 | 6466 | 4608 | 1/0 |
| `render_continuation_hint` | 48 | 41 | +7 | 6091 | 4288 | 1/0 |
| `build_prompt` | 91 | 85 | +6 | 3828 | 2400 | 4/0 |
| `PlanRecord` | 19 | 14 | +5 | 2262 | 1414 | 2/1 |
| `dirty_tree_overlap` | 30 | 25 | +5 | 1923 | 1156 | 2/1 |
| `_detect_driver_command` | 7 | 11 | -4 | 6082 | 4275 | 0/0 |
| `_findings_block_reason` | 23 | 19 | +4 | 3162 | 2197 | 1/0 |
| `enforce_dependency_preflight` | 28 | 24 | +4 | 2815 | 1388 | 1/0 |
| `expand_selectors` | 173 | 169 | +4 | 2519 | 1633 | 2/1 |
| `locked_run` | 26 | 22 | +4 | 6054 | 4251 | 3/0 |
| `make_integration_validation_runner` | 16 | 12 | +4 | 2055 | 1142 | 3/1 |
| `reconcile_disposition` | 63 | 59 | +4 | 4715 | 3031 | 4/0 |
| `_escalation_recorder` | 36 | 33 | +3 | 4176 | 2634 | 0/0 |
| `build_review_prompt` | 23 | 20 | +3 | 3691 | 2292 | 1/0 |
| `reconcile_interrupted` | 82 | 79 | +3 | 5541 | 3833 | 3/0 |
| `StallTimeout` | 2 | 4 | -2 | 206 | 383 | 0/0 |
| `StallWatchdog` | 66 | 64 | +2 | 425 | 389 | 3/0 |
| `_compute_scope_reconciliation` | 30 | 28 | +2 | 738 | 601 | 2/1 |
| `_lane_reclaim_prompt` | 44 | 46 | -2 | 1649 | 866 | 1/0 |
| `_record_deliberate_stop` | 21 | 19 | +2 | 5712 | 3981 | 1/0 |
| `build_dynamic_manifest` | 28 | 26 | +2 | 2392 | 1508 | 3/0 |
| `build_lane_outcome` | 27 | 25 | +2 | 1894 | 1115 | 0/0 |
| `dependency_status_detailed` | 59 | 57 | +2 | 3304 | 2225 | 1/0 |
| `driver_finalize` | 48 | 46 | +2 | 770 | 631 | 4/1 |
| `parse_plan_file` | 54 | 52 | +2 | 2283 | 1430 | 2/0 |
| `_budget_breach_recorder` | 32 | 31 | +1 | 4142 | 2601 | 1/0 |
| `_record_checkpoint_stop` | 33 | 32 | +1 | 4214 | 2669 | 1/0 |
| `determine_action` | 6 | 5 | +1 | 2741 | 1855 | 0/0 |
| `handle_stop_command` | 29 | 30 | -1 | 6435 | 4576 | 1/0 |
| `main` | 171 | 172 | -1 | 6509 | 4644 | 232/3 |
| `terminate_process` | 14 | 15 | -1 | 4019 | 2581 | 6/0 |
| `write_prompt` | 11 | 12 | -1 | 3990 | 2556 | 1/0 |
| `_add_output_mode_flags` | 17 | 17 | +0 | 6166 | 4337 | 0/0 |
| `attempt_log_path` | 9 | 9 | +0 | 4003 | 2570 | 1/0 |
| `build_verifier_prompt` | 67 | 67 | +0 | 3921 | 2487 | 2/0 |
| `driver_actor` | 8 | 8 | +0 | 661 | 555 | 2/1 |
| `reclaim_lanes_on_interrupt` | 137 | 137 | +0 | 1695 | 914 | 2/0 |
| `write_report` | 59 | 59 | +0 | 3053 | 2101 | 1/0 |

### Authoritative side: what the evidence actually supports, and what it does not

The plan requires a per-symbol authoritative-side decision WITH evidence, and sets the rule that
reconciliation must go to an EXISTING behavior on one side, never to a new synthesis. Its stated
default presumption is that opencode is authoritative for lifecycle and finalize logic, and that
neither side is presumed authoritative for anything else.

WHAT THE MEASUREMENT SUPPORTS. Three mechanical signals were computed per symbol: the last-touch date
of each side's region (`git log -L`), whether one side's call set is a strict SUPERSET of the other's
after host-token normalization, and test-reference counts. The superset signal is the strongest
available proxy for "one side gained a capability the other never received", and it fires for
opencode on five symbols and for antigravity on one:

| Symbol | Superset side | Calls present on that side only |
|---|---|---|
| `run_queue` | opencode | `StreamTracker`, `_set_children_all_executed`, `finalize_orchestrator` |
| `driver_begin` | opencode | `begin_baseline_env` |
| `extract_session_id` | opencode | `startswith` |
| `parse_plan_file` | opencode | `_read_kind` |
| `dependency_status_detailed` | opencode | `dependency_target_id6`, `edge_satisfied`, `parse_dependency_token` |
| `build_isolation_notice` | antigravity | `_shared` |

`run_queue` is the clearest case and it corroborates the backlog item's central claim: the opencode
side calls `finalize_orchestrator` and `_set_children_all_executed`, which antigravity never does.
That is lifecycle work that landed on one side only, exactly the divergence bug `dhuape` describes.
`build_isolation_notice` is the counter-example that stops "opencode always wins" from becoming the
rule: antigravity is the superset there, and it is 26 lines SHORTER, so brevity is not a reliable
signal either.

WHAT THE MEASUREMENT DOES NOT SUPPORT, stated plainly rather than papered over. **This inventory does
NOT deliver a defensible authoritative-side decision for all 52 symbols, and it should not pretend
to.** For 46 of them the mechanical signals are silent or tied: last-touch dates are IDENTICAL on both
sides for 51 of 52 symbols (only `main` differs, oc 2026-09-01 vs agy 2026-08-30), because the two
files are habitually edited in the same commit, so git recency has almost no discriminating power
here. Deciding those 46 requires reading 46 pairs of implementations and judging intent, which is
genuinely the work the plan assigns to E-01 and which a single mechanical pass cannot honestly
shortcut. Recording a guess per symbol would be worse than recording the gap, because a child plan
would then reconcile to an unexamined "decision" while believing it was evidenced.

SO THE HONEST STATE OF OQ-03 is: the RULE is fixed (reconcile to an existing behavior, record the
evidence), six symbols have a measured authoritative side, and 46 remain undecided pending
per-symbol reading. Those 46 are all in the slice the maintainer's sequencing gate defers anyway.

## Class (b) HOST-SPECIFIC

opencode-only (47): `BacklogCloseVerdict`, `IntegrationVerdict`, `SuiteCheckResult`, `ToolIdentityError`, `_apply_execution_profile`, `_artifact_owners`, `_carrier_kind`, `_event_session_id`, `_git_common_dir`, `_hardened_credential_paths`, `_read_from_backlog`, `_read_item_dependencies`, `_read_kind`, `_set_children_all_executed`, `action_for`, `assert_child_tool_identity`, `begin_baseline_env`, `cascade_dependency_blocked`, `close_backlog_item`, `collect_earned_paths`, `commit_backlog_close`, `dependency_depth`, `dependency_reasons`, `dependency_status`, `dependency_target_id6`, `edge_satisfied`, `emit_shutdown_report`, `evaluate_backlog_close`, `finalize_orchestrator`, `integration_is_earned`, `parse_dependency_token`, `pinned_child_env`, `pinned_module_argv`, `preflight_dependency_findings`, `process_backlog_close`, `queue_sort_key`, `record_unclosed_backlog_items`, `register_signal_report`, `render_runs_pointer`, `render_unclosed_report`, `resolve_backlog_item`, `run_earned_paths`, `run_opencode`, `run_suite_check`, `runner_package_root`, `signal_report_callback`, `unclosed_backlog_items`

antigravity-only (3): `render_agy_event`, `resolve_agy`, `run_agy_turn`

The 47-to-3 asymmetry is itself a finding. It is NOT 47 features antigravity is missing: most are
opencode-specific stream/permission/event-shape handling that has no antigravity analogue. But the
list is where any "opencode-only lifecycle feature that agy silently lacks" would hide, so a child
plan proposing to unify a symbol from it must justify per-symbol that it is genuinely host-neutral.

## OQ-02, answered from measurement: DESIGNATE, do not absorb

The plan's OQ-02 asks where the shared library lives and whether it absorbs `plan_readiness.py`, and
E-01 is required to state which of absorb-or-designate it chose. The answer is **DESIGNATE**, and it is
forced by evidence rather than preference.

`plan_readiness.py` (219 lines) is NOT a runner-only helper. Its consumers are
`agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, **`agent_workflows/status_set.py`** and
**`agent_workflows/ipd_schema.py`**. The last two are not runners. Absorbing it into a runner library
would therefore make the schema layer and the status-transition layer depend on a driver runtime
module, which inverts the dependency direction. So the shared runner library must DESIGNATE
`plan_readiness.py` as a peer it may import, and must not swallow it.

`host_runner.py` (349 lines: `TaskPacket`, `RawWorkerResult`, `run_worker_process`,
`classify_worker_state`, `build_terminal_envelope`, `validate_terminal_envelope`, `evidence_gate`)
remains the right CONVENTION precedent and the wrong home, exactly as OQ-02 resolved: it serves the Set
coordinator's worker-envelope contract, not a driver's turn loop.

## Method (reproducible)

1. Parse both runners with `ast`, taking every top-level `FunctionDef`/`AsyncFunctionDef`/`ClassDef`.
2. Fingerprint each symbol as `ast.dump(ast.parse(ast.unparse(node)), include_attributes=False)`.
   Round-tripping through `unparse` normalizes formatting and comments, and dropping attributes drops
   line numbers, so the comparison sees STRUCTURE and not layout. Two symbols with the same
   fingerprint are class (a).
3. Repeat the fingerprint over host-token-normalized source (`opencode`/`antigravity`/`agy`/`oc_`/
   `gemini` and their case variants mapped to a placeholder). Equal only after normalization = class
   (a) host-naming sub-case. Still unequal = class (c).
4. Class (d) sweep: build a name-to-definition map over ALL of `agent_workflows/*.py` excluding the two
   runners, then for each runner symbol compare fingerprints against every same-named definition. A
   MATCH is a re-fork; a same name with a different fingerprint is a name collision and is discarded.
5. Authoritative-side signals: `git log -1 -L<start>,<end>:<file>` per symbol region; normalized call
   sets per side with a subset test; `grep -rl` test-reference counts.

The script is small enough to re-derive from this description; it was run from a scratch directory and
is deliberately NOT committed, because a future run must re-measure at its own HEAD rather than trust a
checked-in snapshot of a moving number.

## What this means for the Set (input to the maintainer's sequencing decision)

1. **Child 01 must be re-scoped, not executed as written.** `Heartbeat` is already fixed; the real
   remaining re-fork list is the five symbols above, and it now includes two the plan never named
   (`_read_id`, `_read_status`, owned by `selectors.py` and duplicated in BOTH runners). The
   `stallfp-01` overlap the plan warns about is already resolved.
2. **The byte-identical slice is 34 symbols / 551 lines, not 35.** Still the right second step, still
   provably behavior-neutral, but smaller than the plan sized it.
3. **The diverged slice grew from 37 to 52 while the plan waited**, which is precisely the cost the
   plan predicted for deferring. It will keep growing.
4. **The sequencing gate cannot be evaluated as written.** It defers the diverged slice until
   `runstop`, `wtiso` and `lanetruth` land. `runstop` (7 plans) and `lanetruth` (4 plans) are in
   `executed/`, but SIX of eight `wtiso` plans were retired UNLANDED on 2026-09-02 and replaced by the
   `lanectn` Set (7 plans, `reviewed`, not executed), which edits these same files. The gate is waiting
   on something that will never arrive while its real successor is still ahead of it. That is a
   maintainer decision, not a measurement, and it is deliberately left open here.
5. **E-02's characterization baseline is still required and still load-bearing.** The coverage
   asymmetry the plan measured HOLDS: `tests/test_oc_runipd.py` collects 93 tests against
   `tests/test_agy_runipd_cli.py`'s 20, and `integrate_lane_branch` (a 20-line divergence) still has
   ZERO references anywhere in `tests/`. An agy-side regression in it would leave both suites green.
