# IPD: Add aw partition command to cluster dependent plans into balanced runner shards

- Date: 2026-09-26
- Kind: child
- Concern: RUNNING MULTIPLE RUNNER TERMINALS CONCURRENTLY RISKS INADVERTENT DEPENDENCY FAILURES WHEN DEPENDENT PLANS ARE ARBITRARILY SPLIT ACROSS RUNS, AND CURRENTLY REQUIRES MANUAL SHELL CHUNKING. When operators run multiple `aw oc run` or `aw agy run` instances concurrently in separate terminals to burn down a queue faster (a supported configuration: `runner_shared` Policy B, "SERIALIZE THE INTEGRATION STEP, do not refuse a start"), a naive line-split (such as `split`, `awk`, or bash array slicing) can put a prerequisite plan into Runner 1 and its dependent into Runner 2. When Runner 2 drains with that external edge unmet, `runner_shared.classify_drain_block` classifies it PERMANENT and the dependent ends `fail-depend`. Operators must also hand-build the shell pipelines. `aw partition` selects plans (selectors and filters, or ids on stdin), keeps each connected component of the in-selection dependency graph in ONE shard whenever it fits, balances item counts across K shards, orders each shard dependency-first, and prints one ready-to-paste runner command per shard.
- Scope: IN: (a) `agent_workflows/partition.py`: in-selection dependency graph, weakly connected components, balanced greedy packing, dependency-first ordering within a shard, oversized-component splitting, and command formatting; (b) candidate selection through the EXISTING resolvers (positional selectors, `--status`, `--priority`, `--max`, or whitespace-separated ids on stdin); (c) `-n`/`--shards K` (default 3); (d) `--run {oc,agy,as,none}` output with `--model`/`--variant` passthrough and `--as <profile>` routed through the host-neutral `aw run as <profile>`; (e) register `aw partition` in `agent_workflows/cli.py` and declare it in `agent_workflows/command_surface.py`'s `COMMAND_INVENTORY`; (f) behavioral and CLI tests in `tests/test_partition.py`; (g) a CHANGELOG entry. OUT: in-runner worker pools; launching runs or mutating any record (read-only command); non-plan artifact types (the runners dispatch plans only today; see Deferred).
- Scope-Paths: agent_workflows/partition.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_partition.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- Set: partition
- Order: 1
- Highest E allocated: 06
- Author: antigravity
- Id: xu3yxw

## Workflow history

- 2026-09-26 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 all FIXED. Corrected two non-existent resolver names, replaced the head/tail placement rule (the runner re-sorts queues by dependency depth) with depth-ordered splitting plus reported cut edges, added the COMMAND_INVENTORY declaration the conformance test requires, routed --as through host-neutral `aw run as`, made stdin explicit, guarded empty shards, dropped the `batch` alias and `--type`. Readiness GO - PENDING HUMAN APPROVAL.
- 2026-09-26 to-review (antigravity): authored review-ready plan for aw partition command.
- 2026-09-26 draft (antigravity): created.

## Goal

Provide a read-only, dependency-aware `aw partition` that splits a selection of plans into K balanced shards, keeps every dependency chain that fits inside one shard, orders each shard prerequisites-first, and prints one runner command per shard, so concurrent runs stop failing dependents that a naive split separated from their prerequisites.

PRECISELY WHAT IMPROVES:
1. Prevents concurrent-run `fail-depend` outcomes caused by a split that cuts a prerequisite edge, for every component that fits in one shard.
2. Removes the ad-hoc `split`/`awk`/array shell scripting.
3. Keeps `aw attention` an observer: partitioning is a separate composable verb (`aw att ... -id | aw partition`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the pure algorithm

- [ ] E-01 GRAPH AND COMPONENTS in `agent_workflows/partition.py`. The unit is `attention.Item` (which already carries `item_dependencies` parsed by `ipd_schema.parse_item_dependencies`; do NOT call the private `ipd_schema._parse_item_dependency_edge`). `in_selection_edges(items) -> dict[str, set[str]]`: for every item, every dependency edge whose target id6 is ALSO in the selection (any edge kind: `executed:`, `exists:`, `state:`; edges to non-selected ids are external and ignored). `components(items) -> list[list[Item]]`: undirected weakly connected components over those edges, isolated items as singletons, returned in a deterministic order (by size descending, then smallest id6).
  - Depends on: none
  - Expected outcome: for synthetic selections (two independent chains, a fork-join, isolated nodes, a cycle), components are exactly the expected id6 sets in a deterministic order.
  - Execution state: pending

- [ ] E-02 PACKING AND ORDERING in `agent_workflows/partition.py`. `partition(items, k) -> Partition(shards: list[list[Item]], split_components: list[SplitNote])`, pure and deterministic. (1) `k` is clamped to `max(1, min(k, len(items)))`; an empty selection yields zero shards. (2) Capacity `cap = ceil(N / k)`. (3) Components with `size <= cap` are placed WHOLE, largest first, each into the currently smallest shard (ties broken by lowest shard index), which is LPT greedy. (4) A component with `size > cap` is SPLIT: order its items by `attention.dependency_depths` depth ascending (ties by id6), then place them one at a time in that order into the currently smallest shard, so prerequisites are placed before their dependents; record a `SplitNote(component_ids, shard_indexes, cut_edges)` naming every in-selection edge that now crosses shards. (5) Within each shard, order items by `attention.dependency_depths` depth then id6, so each shard's command lists prerequisites first; this matches the runner's own `queue_sort_key` direction, which re-sorts anyway. (6) Cycles reported by `dependency_depths` are passed through into the result, not repaired.
  - Depends on: E-01
  - Expected outcome: independent items spread within one item of each other; every component with `size <= cap` lands in exactly one shard; an oversized component is split, every crossing edge is listed in `split_components`, and within each shard prerequisites precede dependents; output is byte-identical across repeated runs.
  - REPLACES the original "head/tail buffering" rule. Measured reason: the runner re-sorts each queue by `queue_sort_key` (dependency depth first), so the order `aw partition` prints cannot put an item at a shard's "tail"; and when a cross-shard edge exists, the dependent's run fails it at drain regardless of position (`classify_drain_block`). The honest mitigation for an oversized component is to REPORT the cut (step 4) so the operator can run that component serially or raise `-n`'s capacity by lowering K, and plan `e54nz9` (Order 2) makes a draining run wait for a prerequisite a live peer is executing.
  - Execution state: pending

### Task group 2: selection and formatting

- [ ] E-03 CANDIDATE SELECTION in `agent_workflows/partition.py`: `collect(repo_root, selectors, statuses, priorities, max_count, stdin_ids) -> list[Item]`. Build the universe with `attention.scan(repo_root)` restricted to type `plan` (plans are the only type the runners can dispatch; see Deferred). With `stdin_ids`, keep items whose id6 is in that set and report every unknown or non-plan id on stderr (never silently dropped). Otherwise resolve positional selectors with `selectors.resolve_selectors(repo_root, "plans", tokens)` and intersect by path; no selectors means all plans. Apply `--status` (repeatable, exact match on `Item.status`) and `--priority` through `attention.parse_priority_filters` (so an invalid value errors rather than returning nothing, the defect that function's comment records). Exclude items in a terminal directory. `--max N` truncates AFTER filtering, keeping the first N in `dependency_depths` order (depth then id6) so a prerequisite is kept before its dependents.
  - Depends on: E-01
  - Expected outcome: each filter, stdin, and `--max` behave as stated on a fixture repo; an unknown stdin id and an invalid priority are reported, not swallowed.
  - Execution state: pending

- [ ] E-04 COMMAND FORMATTING in `agent_workflows/partition.py`: `format_shard(run, ids, *, profile, model, variant) -> str`. `none` -> space-separated id6s. `oc`/`agy` -> `aw <run> run <ids...>` then `--model <m>` / `--variant <v>` when given. `--as <profile>` -> the host-neutral `aw run as <profile> <ids...>` (plus passthrough flags), because a profile names its own runner (`runner_profiles`) and `aw run as` is the route that lets the profile pick the host (`cli` "HOST-NEUTRAL DISPATCH"); `--as` with `--run oc|agy` is a usage error rather than a guessed combination. Values are shell-quoted with `shlex.quote`. An empty shard prints nothing (not a command with no ids, which would mean `all`).
  - Depends on: E-03
  - Expected outcome: every format matches the runners' documented grammar (`aw oc run as gem SELECTOR`, `aw oc run SELECTOR --model ... --variant ...`); no command is ever emitted with an empty id list.
  - Execution state: pending

### Task group 3: CLI integration

- [ ] E-05 REGISTER `aw partition` in `agent_workflows/cli.py` using the shared `common` parent (so `--agent`/`--json`/`--color` behave like every other verb), and DECLARE it in `command_surface.COMMAND_INVENTORY` (class `read`, no mutation gate) so `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` stays green. No alias (`batch` is dropped: an alias is a second public name to support, and nothing requires it). Arguments: positional `selectors` (`nargs="*"`); `-n/--shards` (int, default 3, must be >= 1); `-s/--status` (append); `-p/--priority` (append); `--max` (int >= 1); `--run {oc,agy,none}` (default `oc`); `--as` (dest `as_profile`); `--model`; `--variant`; `--stdin` to read ids from standard input explicitly (a bare pipe is NOT auto-detected, so a scripted call cannot hang on an inherited terminal). Output: one line per non-empty shard on stdout; a summary (shard sizes, any `split_components` with their cut edges, any cycles, unknown ids) on stderr always, since those are warnings an operator must see; `--json` emits `{shards: [[id6...]], commands: [...], split_components: [...], cycles: [...], unknown: [...]}`. Exit 0 on success including an empty selection (prints a note, no commands), 2 on usage error.
  - Depends on: E-02, E-04
  - Expected outcome: `aw partition --help` documents every option; the inventory test passes; the command writes nothing to the repository.
  - Execution state: pending

### Task group 4: tests and changelog

- [ ] E-06 ADD `tests/test_partition.py` (behavioral; no source-text or AST pins, per the 2026-09-26 test-policy ruling) and a CHANGELOG entry. Tests: (a) components on synthetic `Item`s: two chains, fork-join, isolated, cycle; (b) packing: K=1, K > N (clamped), empty selection, balanced independents (sizes differ by at most one), a fitting component kept whole, an oversized component split with every cut edge reported and prerequisites before dependents in every shard; determinism (same input twice -> identical output); (c) selection on a fixture repo with real plan files: selectors, `--status`, `--priority` (and an invalid value erroring), `--max` keeping prerequisites, `--stdin` with an unknown id reported, terminal plans excluded; (d) formatting: `none`, `oc`, `agy`, `--as` -> `aw run as`, `--as` with `--run oc` refused, shell quoting, no empty-id command; (e) CLI: `cli.main(["partition", ...])` end to end on the fixture, `--json` shape, exit codes, and a before/after tree listing showing no file changed. CHANGELOG (user-facing, no dashes): a new `aw partition` command splits approved plans into balanced groups for running in several terminals at once, keeping dependent plans together.
  - Depends on: E-05
  - Expected outcome: all tests pass; the command-surface inventory test passes; the CHANGELOG entry exists.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `attention.Item` carries `item_dependencies`, parsed via the public `ipd_schema.parse_item_dependencies`; `attention.dependency_depths(items)` returns `(depth_by_id6, cycles)` and is cycle-safe and type-agnostic.
- Selector resolution: `selectors.resolve_selectors(repo_root, record_type, tokens)` is the public API (there is no `selectors.resolve_selector` or `selectors.resolve_artifact_by_id`).
- Priority filtering: `attention.parse_priority_filters` validates values (its comment records that an unvalidated `--priority med` silently returned 0 items).
- Runner grammar: `aw oc run --help`: "The `as <profile>` clause is POSITIONAL: it must come first, immediately after `run`"; `aw run as <profile> [SELECTOR ...]` is the host-neutral route where "the profile decides the host".
- The runner re-sorts its own queue: `runner_shared.queue_sort_key` puts `dependency_depth` first, so the ORDER of ids on a command line does not survive into execution order.
- Every CLI leaf must be declared in `command_surface.COMMAND_INVENTORY` (`tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves`).
- Shared CLI flags come from the `common` parent parser in `cli._build_parser`.
- Behavioral tests only (maintainer ruling 2026-09-26); suites run bare (`python3 -m pytest`), narrowed runs with `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or a quoted string, never a bare line number (spec `ipd-structure-and-linting` Section 10.2).

## Findings

Author F-1..F-4 measured at HEAD `98ff83f8`. Review corrections F-5..F-12 at the same HEAD in the `feat/aw-partition` worktree.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `runner_shared` (runconcur) | Concurrent runs are supported and serialized at integration, but the operator partitions selectors by hand. | "POLICY B, resolved by the maintainer 2026-09-22: SERIALIZE THE INTEGRATION STEP, do not refuse a start" |
| F-2 | HIGH | drain arm | A split that separates a prerequisite from its dependent fails the dependent at drain. | `classify_drain_block`: an external edge is PERMANENT ("There is no `--with-dependencies` closure inside a frozen run") |
| F-3 | MEDIUM | `attention.Item` | Parsed `item_dependencies` and `dependency_depths` already exist. | `Item(NamedTuple)` `item_dependencies: Optional[Tuple[str, ...]] = None`; `def dependency_depths(items: Sequence[Item])` |
| F-4 | INFO | runner help | `as <profile>` is positional immediately after `run`. | `aw oc run --help`: "The `as <profile>` clause is POSITIONAL" |
| F-5 | HIGH | original E-02 (a) | Named resolvers do not exist: no `selectors.resolve_selector`, no `selectors.resolve_artifact_by_id`. | `grep -n "def resolve" agent_workflows/selectors.py` -> `resolve`, `resolve_selectors` only |
| F-6 | MEDIUM | original E-01 (a) | Called the PRIVATE `ipd_schema._parse_item_dependency_edge` although `attention.Item` already holds the parsed edges via the public `parse_item_dependencies`. | `attention._extract_item_dependencies` calls `_schema.parse_item_dependencies` |
| F-7 | HIGH | original E-01 (c)(2) | "Head/tail buffering" cannot work: the runner re-sorts each queue by `queue_sort_key` (dependency depth first), so print order is discarded, and a cross-shard edge fails at drain regardless of position. | `runner_shared.queue_sort_key` docstring: "DECLARED EDGES WIN, and that is why `dependency_depth` stays FIRST" |
| F-8 | HIGH | original E-03 | A new verb must be declared in `COMMAND_INVENTORY` or the conformance test fails; `command_surface.py` was not in Scope-Paths. | `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` |
| F-9 | MEDIUM | original E-02 (b) | `aw oc run as <profile>` with an agy profile is a host mismatch the plan did not address; the host-neutral `aw run as` exists for exactly this. | `cli` "aw run as <profile> [SELECTOR ...] the profile decides the host" |
| F-10 | MEDIUM | original E-02/E-03 | Auto-detecting "piped stdin" can hang a scripted call on an inherited terminal; an empty shard printed as `aw oc run` with no ids would mean the whole queue; `--priority` must use the validating parser. | `attention.parse_priority_filters` comment; `aw oc run` with no selector selects `all` |
| F-11 | MEDIUM | original E-02 (a) | `-t/--type` implied non-plan types, but runners dispatch plans only (spec `z7nbn1` 4.1, "THE QUEUE ADMITS ONLY PLANS"). | `runner_shared.build_dynamic_manifest` compiles `discover_plans` alone |
| F-12 | LOW | whole plan | No determinism requirement, no read-only proof, no CHANGELOG, no JSON contract, no empty-selection behavior. | - |

## Proposed changes (ordered, validatable)

1. E-01: in-selection graph and components over `attention.Item`.
2. E-02: LPT packing, oversized-component split with reported cuts, dependency-first shard order.
3. E-03: selection through existing resolvers and validating filters.
4. E-04: runner command formatting, `--as` via `aw run as`.
5. E-05: CLI registration and command-surface declaration.
6. E-06: tests and changelog.

## Deferred / out of scope (with reason)

- In-runner `--parallel N` worker pool (Option B).
  - Carrier-Declined: needs multi-lane run state and TUI multiplexing; this plan is the lightweight alternative the operator can use today.
- Launching the shard commands automatically.
  - Carrier-Declined: `aw partition` is read-only by design; launching stays an explicit operator act.
- Partitioning specs or backlog items.
  - Carrier-Declined: the runners cannot queue them yet (spec `z7nbn1` 4.1); when that spec is implemented, a `--type` flag can be added without changing this command's shape.

## Scope check

- Over-scope: removed at review: the `batch` alias and the `-t/--type` filter (F-11), and the head/tail placement rule (F-7).
- Under-scope: added at review: command-surface declaration (F-8), host-neutral `--as` (F-9), explicit `--stdin`, empty-shard guard and validated priority (F-10), reported cut edges for oversized components (F-7), determinism, read-only proof, JSON shape, and CHANGELOG (F-12).

## Required tests / validation

- `python3 -m pytest tests/test_partition.py tests/test_command_surface_declarations.py -o addopts=""`.
- Bare `python3 -m pytest`.
- `python3 -m agent_workflows check all --agent`, naming pre-existing findings as pre-existing.

## Spec / documentation sync

No spec amendment: `aw partition` is a new read-only verb and changes no existing contract. `aw partition --help` is its user documentation, and `CHANGELOG.md` announces it (E-06). If the CLI reference in `README.md` lists every top-level verb at execution time, add one line there too and record it in V-06.

## Open questions

### OQ-01: Default runner output mode

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Default `--run` to `oc`; accept `agy` and `none`. `--as <profile>` emits the host-neutral `aw run as <profile>` form (revised at review, F-9), so the profile rather than `--run` picks the host.

### OQ-02: Handling oversized dependency clusters

- Blocking: no
- Status: resolved
- Owner: reviewer (opencode), on measured evidence
- Resolution or deferral rationale: REVISED AT REVIEW (F-7). A component that fits `ceil(N/K)` stays whole. An oversized one is split in dependency-depth order and EVERY resulting cross-shard edge is reported on stderr and in `--json`, so the operator can decide (run it serially, or use fewer shards). The original head/tail placement is dropped because the runner re-sorts its queue by dependency depth, so print order has no effect, and a cross-shard dependent fails at drain wherever it sits. Plan `e54nz9` (Order 2) addresses that failure directly by waiting on a live peer.

### OQ-03: Interaction between `--max` and dependencies

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Apply `--max N` after filtering and before graph construction, keeping the first N in dependency-depth order so a prerequisite is retained before its dependents. An edge to an id outside the selection is external (it must already be executed, or another run must execute it), matching `attention.dependency_depths`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the passing output of the component tests (two chains, fork-join, isolated, cycle) showing the exact id6 sets, and a grep showing `partition.py` does not call `_parse_item_dependency_edge`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the passing output of the packing tests, including the oversized case's reported cut edges and a determinism test that runs the partition twice and compares.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the passing selection tests on the fixture repo, including the invalid-priority error text and the unknown-stdin-id report.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste each format's output from the tests (`none`, `oc`, `agy`, `--as`), the refusal for `--as` with `--run oc`, and the test proving no empty-id command is emitted.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `aw partition --help`, the passing `test_zero_undeclared_parser_leaves` output, and a `--json` sample.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the full `tests/test_partition.py` run, the before/after tree comparison proving no file changed, the CHANGELOG entry, and the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Plan `e54nz9` (Order 2) depends on this one (`executed:xu3yxw`).

Scope fence (a DECLARATION for reconciliation, not a stop directive): the new `partition.py`, the `aw partition` parser and handler in `cli.py`, one `COMMAND_INVENTORY` entry, the new test file, and one CHANGELOG entry (plus a README line if E-06's condition applies). An out-of-scope edit, if one proves necessary, is made and justified at finalize with `--scope-reason`; a declared-but-unmodified path takes `--scope-ack`.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence. The terminal transition is `aw ipd finalize`: the runner owns it when this plan runs in a lane; a hand executor runs it only when no runner is driving.
