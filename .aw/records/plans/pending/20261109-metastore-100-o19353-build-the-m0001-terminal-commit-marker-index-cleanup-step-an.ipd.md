# IPD: Build the m0001 terminal-commit marker, INDEX cleanup step and hook marker acceptance

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` 5.2 steps 4a and 5 need the migration to delete `plans/STATUS.md` and the INDEX files, and to let its own one big commit through the two pre-commit gates (`hooks/executed_transition_gate`, `hooks/backlog_blocking_close_gate`) by a positive, tree-bound marker. Plan `dcerjg` owned this as E-11 beside the census, round trip and clone proof, which made it a 6-item plan; research `nj8zdp` guidance (at most 5 E-items per plan) moves it here, split from `dcerjg` in round 3 on 2026-11-09.
- Scope: Steps 4a (journal marker holding the migration id and the staged `git write-tree` id) and 5 (delete `plans/STATUS.md`, every `INDEX.json`/`INDEX.md` under plans, research and prompts, and the INDEX ignore lines of the target repository's `.aw/.gitignore`) in `agent_workflows/migrations/m0001_metadata_v2.py`; read-only marker acceptance in `hooks/executed_transition_gate.check` and `hooks/backlog_blocking_close_gate.check`; and `tests/test_m0001_gate_marker.py` (the `dcerjg` E-14 subset that tests E-11). Everything runs only on `tmp_path` fixtures. EXCLUDES: the census, round trip, family test run, clone proof and changelog (`dcerjg`).
- Scope-Paths: agent_workflows/migrations/m0001_metadata_v2.py, agent_workflows/hooks/executed_transition_gate.py, agent_workflows/hooks/backlog_blocking_close_gate.py, tests/test_m0001_gate_marker.py, .aw/records/plans/pending/20261109-metastore-100-o19353-build-the-m0001-terminal-commit-marker-index-cleanup-step-an.ipd.md
- Item-Dependencies: executed:tve77h, executed:vxevph, executed:1vfqdu, executed:dky26u, executed:ghhzb6, executed:hpedmn
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 100
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: o19353

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from dcerjg (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The migration removes the INDEX/STATUS files and can land its own terminal commit through both pre-commit gates by a marker bound to the exact staged tree, proven on fixtures, so `dcerjg`'s clone proof (its E-15 step (d)) can commit.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: terminal marker and cleanup (steps 4a, 5)

- [ ] E-01 (carried verbatim from `dcerjg` E-11) Implement steps 4a and 5 on the scratch result: step 5 deletes `plans/STATUS.md` and every `INDEX.json`/`INDEX.md` under plans, research and prompts, and removes the INDEX ignore lines from the target repository's `.aw/.gitignore`; step 4a writes, after the apply stages the migration's own path list, a positive marker into the journal holding the migration id and the `git write-tree` id of the staged index. In `hooks/executed_transition_gate.check` and `hooks/backlog_blocking_close_gate.check`, accept a staged change ONLY when such a marker exists at the journal path resolved from `project_context.resolve_project_context(repo).logical_roots` `state_durable` (never a literal path) and its tree id equals the current `git write-tree`; any other staged content, including the same paths with one extra edit, is judged by the existing rules. The hooks only READ the marker; `m0001` deletes it after the commit succeeds (and on rollback), so a stale marker can never admit a later commit, and a marker whose tree id no longer matches is ignored and reported once on stderr. `git write-tree` is the only git write the hooks perform, and it writes only tree objects that already describe the staged index. `--no-verify` is never used or suggested.
  - Depends on: none
  - Expected outcome: in a tmp repository holding an executed plan and a release-blocking `done` backlog item, a staged migration result is refused by each hook without the marker, accepted with a matching marker, refused again after one extra staged edit, and refused after the marker is consumed by a completed commit.
  - Execution state: pending

### Task group 2: tests

- [ ] E-02 Add `tests/test_m0001_gate_marker.py` (the `dcerjg` E-14 subset for E-11), on `tmp_path` fixture repositories built with real `git init`, calling the real hook functions and asserting on return values, stderr and file bytes (no source reading): for EACH of the two hooks, one test per E-01 case (refused without marker, accepted with matching tree id, refused after one extra staged edit, refused after the marker is consumed); plus one step-5 test that the fixture's `plans/STATUS.md`, each `INDEX.json`/`INDEX.md` and the INDEX ignore lines are gone from the scratch result. Mark it `core`, or `slow` if its slowest test exceeds 2 s in `--durations=10`, named in V-02.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_m0001_gate_marker.py` passes every test.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Path roots come from `project_context.resolve_project_context` (`config_project`, `state_durable`, `records`), never `<repo>/.aw/...` literals (spec 4.5, 5.1) (carried from `dcerjg` Step 0).
- Tests exercise code and assert on outputs (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `dcerjg` F-11: `hooks/executed_transition_gate._staged_plan_executed_transitions` flags a plan "ARRIVING in an `executed/` directory ... not ALREADY there at HEAD under the SAME `- Id:`"; `hooks/backlog_blocking_close_gate.check` delegates to `check_engine.check_release_gate_consistency` | The renamed executed plans and every rewritten terminal file need the positive marker (5.2 step 4a). |
| F-02 | `dcerjg` F-14: `.aw/.gitignore` INDEX lines for plans, research, prompts; tracked `.aw/records/plans/STATUS.md` | Inputs to step 5. |
| F-03 | `ipd_lint` IPD-Z603 on `dcerjg` (2026-11-09, cutover patched): "plan has 6 E-items (guidance: at most 5)" | Moving E-11 and its test module here brings `dcerjg` to 5 items. |

## Proposed changes (ordered, validatable)

1. E-01: steps 4a and 5 and hook marker acceptance.
2. E-02: the gate-marker test module.

## Deferred / out of scope (with reason)

- The census, round trip, the ten-module family gate run, the clone proof (which exercises this marker in its step (d)) and the changelog.
  - Carrier: dcerjg

## Scope check

- Over-scope: none. The hook edits are additive marker acceptance; `m0001_metadata_v2.py` gains only steps 4a and 5.
- Under-scope: none for `dcerjg` E-11 and its test module.

## Required tests / validation

New module: `tests/test_m0001_gate_marker.py` (`core`). Existing: `tests/test_m0001_preflight.py` (journal it writes into). Gate: bare `python3 -m pytest`, pasted beside the named module run.

## Spec / documentation sync

No spec change; implements `4sd62s` 5.2 steps 4a and 5. The CHANGELOG line is written once by `dcerjg` E-16.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff` hunks of `agent_workflows/hooks/executed_transition_gate.py` and `agent_workflows/hooks/backlog_blocking_close_gate.py` showing the marker read in each `check`; the `git diff` hunk of `agent_workflows/migrations/m0001_metadata_v2.py` showing the step-4a marker write, its deletion after commit and on rollback, and the step-5 deletions; and `rg -n "no-verify" agent_workflows/hooks/executed_transition_gate.py agent_workflows/hooks/backlog_blocking_close_gate.py agent_workflows/migrations/m0001_metadata_v2.py` printing nothing.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_gate_marker.py --durations=10` with each test node id PASSED: refused without marker, accepted with matching tree id, refused after one extra staged edit, refused after the marker is consumed, for each of the two hooks (eight node ids), plus the step-5 cleanup test; and, beside it, the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. All open questions are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Safety: this plan NEVER runs `aw migrate metadata --apply` in this checkout. Every apply is on a `tmp_path` fixture. If an apply would touch this checkout's records, stop and report.

Honesty rule: run the named test module and the bare core gate `python3 -m pytest`, and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit o19353 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize o19353` itself.
