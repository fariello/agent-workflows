# IPD: Close xu3yxw execution gaps: shared edge parser, dead depth fallback, weak tests, agent output, lifecycle

- Date: 2026-09-26
- Kind: child
- Concern: `/verify-execution` of plan `xu3yxw` (commit `309bc790`) found the shipped `aw partition` works on this repository (16 approved plans -> 3 shards `[6, 5, 5]`, both real in-selection edges `cnzrxb -> xz59ai` and `2yqt0a -> wd6npl` kept in one shard) and the bare suite is green (2484 passed), but the execution did not meet its own plan in five ways. (1) `partition.in_selection_edges` parses dependency tokens by hand (`token.strip().split(":")[-1]`), so a `state:spec:approved:<id6>` or `exists:backlog:<id6>` edge whose id6 happens to equal a selected PLAN's id6 is treated as a plan-to-plan edge (measured: `state:spec:approved:bbbbbb` produced `{'aaaaaa': {'bbbbbb'}}`), a second parser beside `attention.dependency_depths`, which uses the shipped `ipd_schema._parse_item_dependency_edge` and checks `target_type`. (2) `_compute_in_selection_depths` is a duplicate depth algorithm justified as a "fallback when item IDs are synthetic/short"; measured, `dependency_depths` returns correct depths for the test ids (`{'n00001': 0, 'n00002': 1, 'n00003': 2}`), so the fallback is dead code that can only diverge. (3) `test_packing_oversized_component_split` asserts "prerequisites precede dependents" by checking ids are LEXICALLY ascending (`assert ids[i] < ids[i + 1]`), which is true of its fixture by construction and proves nothing; E-06 also required a `--stdin` CLI case, a positional-selector CLI case and a `--json` empty-selection case, none present. (4) `--agent` is accepted (shared `common` parent) but ignored: output is identical to the human form, while the declared `agent_record_kind="result"` promises an `aw.agent/v1` record. (5) The plan was marked with every `E-*`/`V-*` complete yet never went through the lifecycle: no `aw ipd begin` receipt exists, no `aw ipd finalize` ran, it is still `- Status: approved` in `pending/`, and its `Observed evidence` blocks paraphrase results instead of pasting runner output as its gate's HONESTY RULE requires.
- Scope: IN: fix (1)-(4) in `agent_workflows/partition.py` and `tests/test_partition.py`; OUT: re-doing any of `xu3yxw`'s correct work (algorithm shape, formatting, CLI flags, inventory entry, CHANGELOG), and any change to `attention`. The lifecycle gap (5) is closed by this plan's own execution through a runner, which begins and finalizes `xu3yxw`'s successor state; see the gate.
- Scope-Paths: agent_workflows/partition.py, tests/test_partition.py
- Item-Dependencies: none
- Status: approved
- Approval: 2026-09-26, human ("approved"): Human approved in chat: '.aw/worktrees/feat-partition/.aw/records/plans/pending/20260926-partition-03-jfza7e-close-xu3yxw-execution-gaps-shared-edge-parser-dead-depth-fa.ipd.md approve. Go!'
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- Set: partition
- Order: 3
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: jfza7e

## Workflow history

- 2026-09-26 approved (human): Human approved in chat: '.aw/worktrees/feat-partition/.aw/records/plans/pending/20260926-partition-03-jfza7e-close-xu3yxw-execution-gaps-shared-edge-parser-dead-depth-fa.ipd.md approve. Go!'
- 2026-09-26 reviewed (antigravity): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-003 fixed. Readiness GO - PENDING HUMAN APPROVAL.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Emitted by /verify-execution of xu3yxw (commit 309bc790); verdict INCOMPLETE / FIDELITY_PARTIAL. Every finding re-measured in the feat-partition worktree; run record .aw/workflow-artifacts/verify-execution/20260926-181803/.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`aw partition` reads dependency edges through the one shared parser, computes depth through the one shared function, is backed by tests that would actually fail on a wrong answer, and honors `--agent`, so that plan `xu3yxw`'s delivery is complete and can be finalized honestly.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one parser, one depth function

- [x] E-01 In `partition.in_selection_edges`, parse each token with `ipd_schema._parse_item_dependency_edge` (the same call `attention.dependency_depths` makes, so the two cannot disagree) and keep an edge only when it parses without error, its `target_type == "ipd"`, its `id6` is in the selection, and it is not a self-edge. Remove the `split(":")[-1]` parsing.
  - Depends on: none
  - Expected outcome: a `state:spec:approved:<id6>` or `exists:backlog:<id6>` edge never becomes a plan-to-plan edge, even when a selected plan shares that id6; `executed:`, `exists:ipd:` and `state:ipd:` edges to selected plans still do.
  - Execution state: performed

- [x] E-02 Delete `partition._compute_in_selection_depths` and both call sites (in `partition` and in `collect`'s `--max` branch), using `attention.dependency_depths` alone. If any test then fails, the test fixture is what is wrong (for example a hand-built `Item` whose tokens `ipd_schema` rejects): fix the fixture, never reintroduce a second depth algorithm.
  - Depends on: E-01
  - Expected outcome: `grep -n "_compute_in_selection_depths" agent_workflows/partition.py` returns nothing and every existing test still passes.
  - Execution state: performed

### Task group 2: honest tests and agent output

- [x] E-03 Replace the lexical assertion in `test_packing_oversized_component_split` with a real dependency check: for every shard, for every pair where item B declares an in-selection edge to item A in the same shard, assert A's index < B's index. Use a chain whose ids are NOT lexically ordered (for example `zzz001 <- aaa002 <- mmm003 <- bbb004`) so a lexical sort would fail it, and assert every in-selection cross-shard edge appears in `cut_edges` (exact set, not `len > 0`).
  - Depends on: E-02
  - Expected outcome: the test fails if within-shard ordering falls back to id order.
  - Execution state: performed

- [x] E-04 Add the CLI cases `xu3yxw` E-06 required and did not deliver: (a) `--stdin` end to end with `sys.stdin` replaced by `io.StringIO("pln001\nunknown99\n")`, asserting the command contains `pln001` and stderr names `unknown99`; (b) a positional selector (`set1`) end to end; (c) `--json` on an EMPTY selection, asserting exit 0, `shards == []`, `commands == []`; (d) a mixed-type edge fixture proving E-01 (a plan declaring `state:spec:approved:<id6>` where a selected plan has that id6 stays unconnected).
  - Depends on: E-01
  - Expected outcome: all four pass; (d) fails against the pre-E-01 parser.
  - Execution state: performed

- [x] E-05 Honor `--agent`: when `args.agent` is set, emit exactly one `aw.agent/v1` `result` record on stdout (the same fields as `--json`: `shards`, `commands`, `split_components`, `cycles`, `unknown`, plus normative `aw.agent/v1` result envelope fields: `schema="aw.agent/v1"`, `kind="result"`, `cmd="partition"`, `exit=0`, `outcome="ok"`, `verified=True`, `complete=True`), serialized through `agent_schema.render_jsonl_record` (which validates against schema invariants), and keep the human summary on stderr. Add a test asserting the single stdout line validates with `agent_schema.validate_agent_record`, parses as JSON with `schema == "aw.agent/v1"`, `kind == "result"`, and `cmd == "partition"`.
  - Depends on: E-02
  - Expected outcome: `aw partition -s approved --agent` prints one parseable, valid agent record, matching the inventory's declared `agent_record_kind="result"`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `attention.dependency_depths` parses edges with `ipd_schema._parse_item_dependency_edge` and keeps only `edge.id6 in present` (it does not filter by `target_type` because its view mixes types; partition's selection is plans only, so it MUST filter to `ipd`).
- `aw partition` is declared in `command_surface.COMMAND_INVENTORY` with `agent_record_kind="result"`.
- Every other verb honors `--agent` via the shared `common` parent parser in `cli._build_parser`.
- A runner owns `aw ipd begin`/`finalize` in a managed lane: running `finalize` by hand in the `feat-partition` worktree refuses with `AW-LIFECYCLE-ROLE-001`.
- Behavioral tests only (maintainer ruling 2026-09-26); run bare `python3 -m pytest`, narrowed with `-o addopts=""`.

## Findings

Measured 2026-09-26 in the `feat/aw-partition` worktree at `309bc790` (xu3yxw's execution commit).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `partition.in_selection_edges` | Hand-rolled token parsing ignores the edge's target type, so a spec/backlog edge sharing a plan's id6 becomes a plan edge. | `target = token.strip().split(":")[-1]`; probe: `state:spec:approved:bbbbbb` -> `{'aaaaaa': {'bbbbbb'}}` |
| F-2 | MEDIUM | `partition._compute_in_selection_depths` | A second depth algorithm, justified by a premise that measures false. | docstring "Fallback ... when item IDs are synthetic/short"; probe: `dependency_depths` -> `{'n00001': 0, 'n00002': 1, 'n00003': 2}` for the test ids |
| F-3 | HIGH | `tests/test_partition.py::test_packing_oversized_component_split` | The ordering assertion is lexical (`assert ids[i] < ids[i + 1]`) on a lexically ordered fixture, so it cannot detect a wrong order; `assert len(sn.cut_edges) > 0` does not check which edges. | the quoted assertions |
| F-4 | MEDIUM | `tests/test_partition.py` | Required CLI cases missing: `--stdin`, positional selector, empty-selection `--json`. | xu3yxw E-06 (c)/(e) vs the test file's CLI tests (`end_to_end`, `json_shape`, `exit_codes` only) |
| F-5 | MEDIUM | `partition.run_partition` | `--agent` accepted and ignored; output identical to human mode. | `aw partition -s approved --agent` printed the human summary and commands |
| F-6 | HIGH | plan `xu3yxw` lifecycle | Marked fully complete, never begun or finalized; evidence paraphrased, not pasted. | no `xu3yxw` receipt under `.aw/state`; plan still `- Status: approved` in `pending/`; V-06 "tests/test_partition.py passed 12 in 2.60s" with no pasted output |

## Proposed changes (ordered, validatable)

1. E-01: shared parser with an `ipd` target filter.
2. E-02: delete the duplicate depth function.
3. E-03: a real ordering and cut-edge assertion.
4. E-04: the missing CLI cases and the mixed-type proof.
5. E-05: `--agent` output.

## Deferred / out of scope (with reason)

- Changing `attention.dependency_depths` to filter by target type.
  - Carrier-Declined: its view is deliberately type-agnostic ("a plan declaring a `backlog` target orders against that backlog item"), so the filter belongs in partition's plans-only selection, not there.

## Scope check

- Over-scope: none; every item traces to F-1..F-5.
- Under-scope: F-6 (lifecycle) is not code; it is closed by executing this plan through a runner and by finalizing `xu3yxw` (see the gate).

## Required tests / validation

- `python3 -m pytest tests/test_partition.py tests/test_command_surface_declarations.py -o addopts=""`.
- Bare `python3 -m pytest`.
- `aw partition -s approved --dir <repo root>` and `--agent` against the real repository, output pasted.

## Spec / documentation sync

None: no spec governs `aw partition`, and its help text and CHANGELOG entry from `xu3yxw` remain accurate.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the `in_selection_edges` diff and the passing output of E-04 (d), plus the same test FAILING with E-01's hunk reverted.
  - Observed evidence: Verified with diff, passing test, and negative test failure on revert.
    `in_selection_edges` diff:
    ```diff
    @@ -54,9 +56,15 @@ def in_selection_edges(items: Sequence[_att.Item]) -> Dict[str, Set[str]]:
             if not it.id:
                 continue
             for token in it.item_dependencies or ():
    -            target = token.strip().split(":")[-1]
    -            if target and target in present_ids and target != it.id:
    -                edges[it.id].add(target)
    +            edge, err = _schema._parse_item_dependency_edge(token)
    +            if err or edge is None:
    +                continue
    +            if (
    +                edge.target_type == "ipd"
    +                and edge.id6 in present_ids
    +                and edge.id6 != it.id
    +            ):
    +                edges[it.id].add(edge.id6)
    ```
    Passing test output:
    ```
    $ python3 -m pytest tests/test_partition.py -k test_in_selection_edges_mixed_type_fixture -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: <worktree-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 17 items / 16 deselected / 1 selected

    tests/test_partition.py .                                                [100%]

    ======================= 1 passed, 16 deselected in 0.20s =======================
    ```
    Failing output with E-01 hunk reverted:
    ```
    __________________ test_in_selection_edges_mixed_type_fixture __________________
    ...
    >       assert edges["aaaaaa"] == {"dddddd"}
    E       AssertionError: assert {'bbbbbb', 'cccccc', 'dddddd'} == {'dddddd'}
    E
    E         Extra items in the left set:
    E         'bbbbbb'
    E         'cccccc'
    E         Use -v to get more diff

    tests/test_partition.py:125: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_partition.py::test_in_selection_edges_mixed_type_fixture - AssertionError: assert {'bbbbbb', 'cccccc', 'dddddd'} == {'dddddd'}
    ======================= 1 failed, 16 deselected in 0.21s =======================
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the empty `grep -n "_compute_in_selection_depths" agent_workflows/partition.py` output and the passing `tests/test_partition.py` run.
  - Observed evidence: Verified with empty grep exit code 1 and all tests passing.
    Empty grep output (exit code 1):
    ```sh
    $ grep -n "_compute_in_selection_depths" agent_workflows/partition.py
    ```
    Passing tests run:
    ```
    $ python3 -m pytest tests/test_partition.py tests/test_command_surface_declarations.py -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: <worktree-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 18 items

    tests/test_command_surface_declarations.py .                             [  5%]
    tests/test_partition.py .................                                [100%]

    ============================== 18 passed in 1.23s ==============================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the rewritten test and its passing output, then its FAILING output when within-shard sorting is temporarily changed to `key=lambda it: it.id`.
  - Observed evidence: Verified with passing non-lexical test and failure under ID-based sorting mutation.
    Rewritten test in `tests/test_partition.py`:
    ```python
    def test_packing_oversized_component_split() -> None:
        # 6 items in one chain with non-lexical ID order:
        # zzz001 <- aaa002 <- mmm003 <- bbb004 <- yyy005 <- ccc006
        # K = 3 -> cap = ceil(6 / 3) = 2.
        # Component size 6 > 2, so component must be split.
        items = [
            make_item("zzz001"),
            make_item("aaa002", ("executed:zzz001",)),
            make_item("mmm003", ("executed:aaa002",)),
            make_item("bbb004", ("executed:mmm003", "executed:zzz001")),
            make_item("yyy005", ("executed:bbb004",)),
            make_item("ccc006", ("executed:yyy005", "executed:mmm003")),
        ]
        p = part.partition(items, 3)
        assert len(p.shards) == 3
        assert len(p.split_components) == 1
    ...
    ```
    Passing test output:
    ```
    $ python3 -m pytest tests/test_partition.py -k test_packing_oversized_component_split -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: <worktree-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 17 items / 16 deselected / 1 selected

    tests/test_partition.py .                                                [100%]

    ======================= 1 passed, 16 deselected in 0.19s =======================
    ```
    Failing output when within-shard sorting is temporarily changed to `key=lambda it: it.id`:
    ```
    ____________________ test_packing_oversized_component_split ____________________
    ...
    >                       assert a_idx < b_idx, f"Prerequisite {a_id} must precede {b_id}"
    E                       AssertionError: Prerequisite zzz001 must precede bbb004
    E                       assert 1 < 0

    tests/test_partition.py:249: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_partition.py::test_packing_oversized_component_split - AssertionError: Prerequisite zzz001 must precede bbb004
    ======================= 1 failed, 16 deselected in 0.21s =======================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the passing output of the four new tests by name.
  - Observed evidence: Verified with four new CLI and edge tests passing.
    ```sh
    $ python3 -m pytest tests/test_partition.py -k "test_cli_partition_stdin_end_to_end or test_cli_partition_positional_selector or test_cli_partition_json_empty_selection or test_in_selection_edges_mixed_type_fixture" -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: <worktree-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 17 items / 13 deselected / 4 selected

    tests/test_partition.py ....                                             [100%]

    ======================= 4 passed, 13 deselected in 0.42s =======================
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `aw partition -s approved --agent` output from the real repository and the passing agent-record test asserting schema validity via `validate_agent_record`.
  - Observed evidence: Verified with agent output on real repository, passing agent schema test, and bare test suite passing.
    `aw partition -s approved --agent` output:
    ```
    Partitioned 19 items across 3 shard(s): [7, 6, 6]
    {"schema":"aw.agent/v1","kind":"result","cmd":"partition","exit":0,"outcome":"ok","verified":true,"complete":true,"shards":[["2a6phj","8y13kn","jfza7e","olkeju","slqvmx","wd6npl","2yqt0a"],["4petcj","dmxc5h","me227c","pyuhnl","xz59ai","cnzrxb"],["6vozur","isgno7","o7k6lt","s6ne9d","xu3yxw","e54nz9"]],"commands":["aw oc run 2a6phj 8y13kn jfza7e olkeju slqvmx wd6npl 2yqt0a","aw oc run 4petcj dmxc5h me227c pyuhnl xz59ai cnzrxb","aw oc run 6vozur isgno7 o7k6lt s6ne9d xu3yxw e54nz9"],"split_components":[],"cycles":[],"unknown":[]}
    ```
    Passing agent-record test output:
    ```sh
    $ python3 -m pytest tests/test_partition.py -k "test_cli_partition_agent_mode" -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: <worktree-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 17 items / 16 deselected / 1 selected

    tests/test_partition.py .                                                [100%]

    ======================= 1 passed, 16 deselected in 0.29s =======================
    ```
    Full test suite bare:
    ```
    $ python3 -m pytest
    2489 passed, 2 skipped, 3 warnings in 42.18s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after `/plan-review` and explicit human approval. Born `to-review` rather than `auto-approved` (D65): E-01 changes which edges keep plans together and E-05 adds an output contract, so it is not a purely mechanical correction.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/partition.py` and `tests/test_partition.py` only. An out-of-scope edit, if one proves necessary, is made and justified at finalize with `--scope-reason`; a declared-but-unmodified path takes `--scope-ack`.

HONESTY RULE (hard MUST): every `Observed evidence` block pastes the ACTUAL runner output, not a summary of it. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

LIFECYCLE (closes F-6): run this plan through a runner (`aw oc run jfza7e` or `aw agy run jfza7e`), which owns `aw ipd begin` and `aw ipd finalize`. Plan `xu3yxw` must ALSO be finalized honestly: its `Observed evidence` blocks must be replaced with pasted output and it must pass `aw ipd lint --phase pre-transition`, then be finalized by a runner (or by a hand executor only when no runner drives this worktree), because its code is already on the branch and a second implementation is not wanted. Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push).
