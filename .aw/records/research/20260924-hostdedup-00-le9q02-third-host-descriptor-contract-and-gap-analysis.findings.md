---
id: le9q02
created: 20260924
set: hostdedup
order: 00
topic: [hostdedup, host-descriptor, runner-architecture]
model:
kind: findings
status: reference
outcome: adopted
summary: Host descriptor contract and third-host gap analysis
consumed-by: [xdvglg]
priority: high
---

# Host Descriptor Contract and Third-Host Gap Analysis

## 1. Executive Summary

This research establishes whether "a new host is a descriptor, not a runner" holds in practice by introducing a third scripted host (`scripted`) without writing a third runner module (`*_runipd.py`).

The experiment proves:
1. **The descriptor seam succeeds at pre-execution lifecycle stages**: A host defined solely by `HostLabels` can successfully initialize runs through `runner_shared.initialize_run_core`, produce clean run state with unambiguous host attribution (`state["driver"]["id"] = "scripted"`), be parsed by both `run_analytics_sources` and `run_viewer`, and report capabilities in `aw host capabilities`.
2. **The descriptor seam is insufficient for turn execution**: `HostLabels` is a passive metadata record (9 strings/flags) and does not model turn execution (argv assembly, process spawn, stream decoding, or host options). Furthermore, turn dispatch is currently blocked because `execute_item` and `run_queue` remain forked per runner.

---

## 2. Enumerated Host Contract

The complete set of inputs a host must supply to the runner subsystem, measured from code:

| Contract Component | Items / Specifics | Consumers | Modelled in `HostLabels`? |
|---|---|---|---|
| **Host Identification & UI Strings** | `id`, `command`, `review_command`, `argv_tokens`, `argv_subcommands`, `product`, `report_title`, `shell_tool`, `emits_launch_identity`, `full_auto_actor` | `runner_shared` (reconciliation, finalize, actor, prompt, report, refusals), `run_analytics_sources`, `run_viewer` | **YES** (10 fields in `HostLabels` with no defaults) |
| **Driver Identity State** | `state["driver"]["id"]`, `state["driver"]["path"]`, `state["driver"]["sha256"]` | `run_analytics_sources.driver_generation`, `run_viewer.load_run_summary` | **YES** (`driver.id` carries `HostLabels.id`; `path`/`sha256` are optional for runner-less hosts) |
| **Host-Specific Options** | 13 host-only keys: 7 oc-only (`agent`, `auto`, `launch_profile`, `no_audit`, `opencode`, `validate`, `variant`), 6 agy-only (`agy_executable`, `dangerously_skip_permissions`, `effort`, `new_session`, `no_verify`, `timeout`); plus conditional `verify_*` options on oc | `initialize_run`, `execute_item`, `select_execution_profile`, `run_opencode`, `run_agy_turn` | **NO** (passed via `host_options: dict` to `initialize_run_core`) |
| **Turn Launch Argv Construction** | CLI executable path, flag syntax (`--session`/`--dir`/`--model` vs `-p`/`--output-format stream-json`), output format switches | `oc_runipd.py:5648`, `agy_runipd.py:2730`, verifier launch in `runner_shared.py:15192` | **NO** (fully host-specific with zero overlap) |
| **Turn Spawn Function** | `run_opencode` (13 parameters) vs `run_agy_turn` (12 parameters, different signature and process manager) | Called by name in each host's `execute_item` | **NO** (no shared spawn callable or protocol) |
| **Sandbox & Permissions Posture** | Landlock OS sandbox, process-tree kill, structured tool events, session resume, permission bypass | `host_sandbox_profile.detect_host_capabilities`, `preflight_host_capabilities` | **NO** (modelled in `host_sandbox_profile.HostSandboxCapabilities`) |
| **Label Binding Sites** | 9 binding sites per runner passing `labels=` to shared functions | `oc_runipd.py`, `agy_runipd.py` | **NO** (binding sites exist inside runner modules) |
| **Shared Code Host Branches** | Stream fallback parsing (`_render_turn_stream_fallback`), verifier argv (`_build_verifier_turn_argv`), orchestrator coverage (`enforce_orchestrator_coverage`), mixed type refusal | `runner_shared.py:15149, 15192, 15560, 23355` | **NO** (hardcoded host string branches) |

---

## 3. Third-Host Experiment and Measured Boundary

A third host (`scripted`) was constructed with `SCRIPTED_HOST_LABELS = HostLabels(id="scripted", command="aw scripted run", ...)` without creating any `scripted_runipd.py` module.

### What Succeeded
- **Run Initialization**: `runner_shared.initialize_run_core` initializes a run with `driver: {"id": "scripted", "path": None, "sha256": None}`.
- **Analytics Attribution**: `run_analytics_sources.driver_generation` reads `driver.id` and infers `"scripted"` (and `generation_host("scripted") == "scripted"`). Historical pre-cutover runs without `driver.id` continue resolving to `"oc_runipd"`, `"agy_runipd"`, `"runipd"`, `"ipdrunner"` via basename fallback.
- **Run Viewer**: `run_viewer.load_run_summary` attributes the run to `"scripted"` directly from `driver.id`.
- **Capabilities Inspection**: `host_cmd.DEFAULT_HOSTS` includes `"scripted"`, and `aw host capabilities` reports fail-closed capabilities cleanly.

### Where Execution Stopped (The Three Predicted Walls)
When attempting to drive an IPD turn end-to-end:
1. **Wall 1 (No Argv Contract)**: There is no shared argv constructor for launching a turn.
2. **Wall 2 (No Spawn Seam)**: `execute_item` is forked in `oc_runipd.py` and `agy_runipd.py`, calling `run_opencode` and `run_agy_turn` respectively by name.
3. **Wall 3 (Label Binding Sites)**: The 9 `HostLabels` call sites live inside the runner modules. Without a runner module, there is no entry point that binds `SCRIPTED_HOST_LABELS` into the turn execution loop.

---

## 4. Gap Classification

Every identified gap is classified into one of four distinct categories:

### (a) Missing `HostLabels` Field
- **Driver Identifier (`id`)**: Previously, driver identity was implicitly derived from `__file__` basename in each runner module.
- **Resolution**: Added `id: str` to `HostLabels` (`"oc_runipd"`, `"agy_runipd"`), recorded it in `state["driver"]["id"]`, and updated `run_analytics_sources` and `run_viewer` with fallback to `driver.path` for historical records (OQ-02).

### (b) Genuine Host Capability
- **Execution guarantees**: `supports_os_sandbox`, `supports_process_tree_kill`, `emits_structured_tool_events`, `supports_session_resume`.
- **Classification**: These are dynamic platform/executable guarantees appropriately owned by `host_sandbox_profile.HostSandboxCapabilities` via executed probes rather than passive label strings in `HostLabels`.

### (c) Structural Limits of the Seam
- **Passive Metadata vs Executable Behavior**: `HostLabels` is a passive `NamedTuple` of strings/booleans. It does not provide a turn runner protocol, process lifecycle interface, or CLI invocation contract.
- **Label Binding Location**: Because labels are passed as arguments to shared helpers inside runner modules, a descriptor has no mechanism to inject itself into the execution loop without a runner module or a shared runner dispatch layer.

### (d) Blocked on the Remaining Fork
- **Forked Lifecycle Functions**: The five core execution functions (`main`, `build_parser`, `initialize_run`, `run_queue`, `execute_item`) were originally duplicated across `oc_runipd.py` and `agy_runipd.py`.
- While `initialize_run` has been unified into `runner_shared.initialize_run_core`, `execute_item` and `run_queue` remain forked in both runners. Turn dispatch cannot accept a third host until `run_queue` and `execute_item` are unified behind an injectable host runner protocol.

---

## 5. Architectural Recommendations

For future host integrations (Codex, Claude, Hermes):
1. **Do not expand `HostLabels` into an execution engine**: Keep `HostLabels` focused on operator-facing strings and identifiers.
2. **Define a `HostRunner` / `HostTurnLauncher` protocol**: Unify `run_queue` and `execute_item` into `runner_shared.py`, parameterizing the turn spawn via an injectable launcher interface (`Callable[[TurnRequest], TurnResult]`).
3. **Migrate remaining host branches**: Replace hardcoded `if host == "agy":` checks in `runner_shared.py` (stream fallback parsing, verifier argv) with capabilities or descriptor properties.
