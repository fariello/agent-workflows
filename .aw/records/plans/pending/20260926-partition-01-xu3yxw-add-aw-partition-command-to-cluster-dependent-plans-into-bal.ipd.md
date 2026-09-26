# IPD: Add aw partition command to cluster dependent plans into balanced runner shards

- Date: 2026-09-26
- Kind: child
- Concern: RUNNING MULTIPLE RUNNER TERMINALS CONCURRENTLY RISKS INADVERTENT DEPENDENCY FAILURES WHEN DEPENDENT PLANS ARE ARBITRARILY SPLIT ACROSS RUNS, AND CURRENTLY REQUIRES MANUAL SHELL CHUNKING. When operators run multiple `aw oc run` or `aw agy run` instances concurrently in separate terminals to burn down a queue faster, a naive line-split (such as `split`, `awk`, or bash array slicing) risks putting a prerequisite plan into Runner 1 and its dependent into Runner 2. If Runner 2 dispatches the dependent plan before Runner 1 merges the prerequisite, Runner 2 marks it `fail-depend` (dependency-blocked) and skips it. Furthermore, operators must manually construct shell pipelines to extract and chunk IDs. An external `aw partition` command solves both issues by selecting artifacts (with selectors, filters, and `--max`), grouping connected components of the cross-dependency graph together, balancing total items across K shards via greedy bin packing, and formatting ready-to-run `aw oc run` or `aw agy run` command lines with passthrough flags for launch profile (`--as`), model (`--model`), and variant (`--variant`).
- Scope: IN: (a) create `agent_workflows/partition.py` implementing graph extraction from declared `Item-Dependencies`, connected component clustering, greedy multiway number partitioning (Largest Processing Time / largest component to smallest bucket), topological depth ordering within each shard, and runner command formatting; (b) support selector tokens and filters (`-t`/`--type`, `-s`/`--status`, `--priority`, `--max`) as well as piped stdin of IDs; (c) support `-n`/`--shards K` (default 3); (d) support runner formatting (`--run {oc,agy,none}`) with passthrough options: `--as <profile>`, `--model <model>`, and `--variant <variant>`; (e) register `aw partition` in `agent_workflows/cli.py`; (f) comprehensive behavioral and CLI unit tests in `tests/test_partition.py`. OUT: in-runner multi-threading / worker pools (Option B, which requires runner state-machine overhaul and multi-lane TUI redesign); mutating the repository or executing the plans directly (this is a command-line query and partition generator).
- Scope-Paths: agent_workflows/partition.py, agent_workflows/cli.py, tests/test_partition.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: medium
- Set: partition
- Order: 1
- Highest E allocated: 04
- Author: antigravity
- Id: xu3yxw

## Workflow history

- 2026-09-26 to-review (antigravity): authored review-ready plan for aw partition command.
- 2026-09-26 draft (antigravity): created.

## Goal

Provide a dedicated, dependency-aware command line utility `aw partition` that partitions selected plans into K balanced shards while preserving cross-plan dependency chains within the same shard, formatting cut-and-paste runner commands (`aw oc run` / `aw agy run`) with passthrough flags for `--as`, `--model`, and `--variant`.

PRECISELY WHAT IMPROVES:
1. Prevents concurrent runner failures (`fail-depend`) caused by naive sharding cutting across prerequisite-dependent edges.
2. Eliminates operator shell scripting friction (no need for ad-hoc `split`, `awk`, or bash array arithmetic).
3. Preserves observer purity: keeps `aw attention` focused on repository observation while providing clean composability via piping or standalone queries.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: core clustering and partitioning algorithm

- [ ] E-01 IMPLEMENT GRAPH EXTRACTION, TWO-TIER CONNECTED COMPONENTS, AND GREEDY PARTITIONING IN `agent_workflows/partition.py`.
  In `agent_workflows/partition.py`, implement:
  (a) `extract_dependency_graph(items: Sequence[PlanItem]) -> tuple[dict[str, set[str]], dict[str, PlanItem]]`: parses `Item-Dependencies` using `ipd_schema._parse_item_dependency_edge`, restricting edges to targets present within the selected set.
  (b) `connected_components(items: Sequence[PlanItem]) -> list[list[PlanItem]]`: computes undirected weakly connected components (clusters of mutually dependent items). Isolated items become single-element clusters.
  (c) `partition_clusters(items: Sequence[PlanItem], k: int) -> list[list[PlanItem]]`:
      - Two-tier rule:
        (1) PREFERENTIAL CLUSTERING: for any component whose item count is within the fair shard capacity (<= ceil(N/K)), keep the entire component intact as an atomic cluster.
        (2) TOPOLOGICAL RANK SPLITTING WITH HEAD/TAIL BUFFERING (the giant-component fallback): when a component exceeds ceil(N/K) items, partition it along topological depth boundaries (computed via longest-path depth). Place upstream/prerequisite items (low depth) into earlier shards positioned at the HEAD of the shard's queue, and downstream/dependent items (high depth) into later shards positioned at the TAIL of the shard's queue, maximizing execution lead-time for prerequisites across concurrent runners.
      - Greedy bin packing balances total items across K shards (Largest Processing Time / largest component into the currently smallest bucket).
  (d) `topological_sort_shard(shard: list[PlanItem]) -> list[PlanItem]`: within each shard, orders items so prerequisites precede their dependents (using dependency depth logic derived from `attention.dependency_depths`).
  - Depends on: none
  - Expected outcome: unit tests confirm that independent plans distribute evenly across K shards, dependent plans within fair budgets stay grouped together, and oversized components are split topologically with prerequisites at the head of earlier shards and dependents at the tail of later shards.
  - Execution state: pending

### Task group 2: selection, stdin ingestion, and runner formatting

- [ ] E-02 IMPLEMENT SELECTION, STDIN INGESTION, MAX TRUNCATION, AND COMMAND FORMATTING IN `agent_workflows/partition.py`.
  In `agent_workflows/partition.py`, implement:
  (a) `collect_candidates(repo_root: Path, selectors: Sequence[str], types: Sequence[str], statuses: Sequence[str], priorities: Sequence[str], max_count: Optional[int], stdin_text: Optional[str]) -> list[PlanItem]`:
      - If `stdin_text` is provided (non-empty), parses whitespace-separated or newline-separated ID tokens and resolves matching plans via `selectors.resolve_artifact_by_id`.
      - Otherwise, resolves candidates using `selectors.resolve_selector` / `attention.scan()` filtering by type (defaulting to `plan`/`plans`), status (e.g. `approved`), and priority.
      - If `max_count` is specified, truncates candidate list to at most `max_count` items.
  (b) `format_shard_command(runner: str, ids: Sequence[str], profile: Optional[str], model: Optional[str], variant: Optional[str]) -> str`:
      - If `runner == "none"`, returns space-separated IDs.
      - If `runner in ("oc", "agy")`, constructs `aw <runner> run` with optional positional `as <profile>` (e.g. `aw oc run as gem <ids>`), followed by IDs, followed by passthrough options (`--model <model>` and `--variant <variant>`).
  - Depends on: E-01
  - Expected outcome: candidate collection honors selectors, filters, `--max`, and stdin; formatting outputs valid runner strings matching `oc_runipd` and `agy_runipd` command grammar.
  - Execution state: pending

### Task group 3: CLI integration

- [ ] E-03 REGISTER `aw partition` IN `agent_workflows/cli.py` AND WIRE HANDLER.
  In `agent_workflows/cli.py`:
  (a) Add parser `p_partition = sub.add_parser("partition", ...)` with aliases `["batch"]`.
  (b) Add arguments:
      - `selectors` (nargs="*", default=[]): positional selector tokens (id6, setid, status, e.g. `approved`).
      - `-n`, `--shards` (type=int, default=3): number of shards K.
      - `-t`, `--type` (action="append", default=[]): filter by type (defaults to `plan`).
      - `-s`, `--status` (action="append", default=[]): filter by status (e.g. `approved`).
      - `-p`, `--priority` (action="append", default=[]): filter by priority.
      - `--max` (type=int, default=None): maximum number of items to select.
      - `--run` (choices=["oc", "agy", "none"], default="oc"): runner formatting.
      - `--as` (dest="as_profile", default=None): runner launch profile.
      - `--model` (default=None): passthrough model flag.
      - `--variant` (default=None): passthrough variant flag.
      - `--verbose`, `-v` (action="store_true"): show shard summary diagnostics on stderr.
  (c) Connect `_run_partition` handler to invoke `partition.main()`.
  - Depends on: E-02
  - Expected outcome: `aw partition --help` documents all options; executing `aw partition` correctly processes arguments and outputs runner lines.
  - Execution state: pending

### Task group 4: verification suite

- [ ] E-04 ADD COMPREHENSIVE BEHAVIORAL AND CLI TESTS IN `tests/test_partition.py`.
  In `tests/test_partition.py`:
  (a) Unit test graph extraction and component clustering on synthetic DAGs (independent chains, fork-join, cycles, isolated nodes).
  (b) Unit test greedy multiway number partitioning with edge cases (K=1, K > N, empty items, oversized cluster).
  (c) Unit test stdin ingestion and `--max` truncation.
  (d) Unit test runner command formatting with `--as`, `--model`, and `--variant` passthrough.
  (e) Integration test invoking the CLI parser via `cli.main(["partition", ...])` on test repositories with real plan files.
  - Depends on: E-03
  - Expected outcome: all tests pass cleanly under `python3 -m pytest tests/test_partition.py`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `attention.Item` and `attention.dependency_depths` in `agent_workflows/attention.py` parse `Item-Dependencies` via `ipd_schema._parse_item_dependency_edge`. Reusing this edge parsing ensures consistency with `aw check` and `aw attention`.
- `runner_shared.expand_selectors` and `selectors.resolve_selector` are the standard selector expansion mechanisms across the package.
- Runner command syntax (`oc_runipd.py` and `agy_runipd.py`): the `as <profile>` clause is strictly positional immediately following `run` (e.g. `aw oc run as gem <ids>`), and options `--model <model>` and `--variant <variant>` follow.
- Test policy (maintainer ruling 2026-09-26): behavioral tests only, no AST pins. Suites run bare (`python3 -m pytest tests/test_partition.py`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2).

## Findings

Measured at HEAD `98ff83f8` (2026-09-26).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `agent_workflows/runner_shared.py` (runconcur) | Multi-process runner execution is safe and serialized via `integration.lock`, but requires manual selector partitioning. | `POLICY B: SERIALIZE THE INTEGRATION STEP, do not refuse a start. Two drivers may EXECUTE in parallel; they may not INTEGRATE in parallel.` |
| F-2 | HIGH | `agent_workflows/runner_shared.py`, `edge_satisfied` | Naive line splitting risks splitting parent and child plans into separate runs, causing `fail-depend` (dependency-blocked) when the child is reached before the parent merges. | `runner_shared.edge_satisfied`: an unmet prerequisite in an independent run marks the child `fail-depend`. |
| F-3 | MEDIUM | `agent_workflows/attention.py`, line 86 | `attention.Item` already stores parsed `item_dependencies`, and `dependency_depths` provides cycle detection and longest-path depth calculation. | `Item(NamedTuple)` includes `item_dependencies: Optional[Tuple[str, ...]] = None`. |
| F-4 | INFO | `agent_workflows/oc_runipd.py`, line 4433 | `aw oc run` accepts positional `as <profile>` immediately following `run`, followed by selectors, followed by `--model` and `--variant`. | `aw oc run as <profile> SELECTOR --model ... --variant ...` grammar. |

## Proposed changes (ordered, validatable)

1. E-01 implements graph extraction, component clustering, and greedy partitioning in `agent_workflows/partition.py`.
2. E-02 implements candidate selection, stdin ingestion, `--max` limiting, and runner command formatting.
3. E-03 registers `aw partition` in `agent_workflows/cli.py`.
4. E-04 adds full behavioral and integration test suite in `tests/test_partition.py`.

## Deferred / out of scope (with reason)

- Option B (In-runner `--parallel N` / `--threads N` worker pool).
  - Carrier-Declined: Requires major state machine overhaul (`state.json` multi-lane tracking), terminal TUI multiplexing, and cross-host coordination. Preserved as a future runner milestone.
- Mutating plan status or launching processes automatically.
  - Carrier-Declined: `aw partition` is a deterministic command generator. Launching execution remains the operator's explicit action via pasting into terminals or subshells.

## Scope check

- Over-scope: none.
- Under-scope: none; covers selection, filtering, `--max`, graph clustering, bin packing, runner formatting with passthrough flags, and testing.

## Required tests / validation

- Unit tests for connected component clustering and greedy partitioning.
- Behavioral tests for stdin piping (`aw att ... -id | aw partition`).
- Passthrough verification for `--as`, `--model`, and `--variant`.
- Clean pytest run: `python3 -m pytest tests/test_partition.py`.

## Spec / documentation sync

- `N/A with reason`: `aw partition` is a new utility verb in `cli.py`; no existing spec contract is modified.

## Open questions

### OQ-01: Default runner output mode

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Default `--run` to `oc` (OpenCode driver), as it is the most common execution target, but accept `--run agy` for Antigravity and `--run none` for bare space-separated IDs.

### OQ-02: Handling oversized dependency clusters

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: When a connected component fits within the fair shard capacity (<= ceil(N/K)), keep it intact in a single shard. When a component exceeds that capacity (the giant-component case), split it across shards along topological depth boundaries. Place upstream prerequisite items at the head of earlier shards and downstream dependent items at the tail of later shards, maximizing the completion lead-time buffer between concurrent runners.

### OQ-03: Interaction between `--max` and dependencies

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Apply `--max N` during initial candidate selection before graph construction. Any prerequisite edge pointing to an ID not in the selected $N$ items is treated as external (must already be executed), matching `attention.dependency_depths`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Unit tests demonstrate that independent items balance across K shards and dependent items remain grouped in the same shard with prerequisite-first ordering.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Unit tests demonstrate candidate collection filters by type/status/priority, truncates to `--max N`, parses stdin tokens, and formats runner strings with `--as`, `--model`, and `--variant`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: CLI integration test verifies `cli.main(["partition", ...])` parses all flags and outputs expected runner command lines to stdout.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Captured output of `python3 -m pytest tests/test_partition.py` showing all tests passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Standard child plan implementing a single focused command-line utility. Execution will follow the standard IPD lifecycle in the isolated worktree `feat/aw-partition`.
