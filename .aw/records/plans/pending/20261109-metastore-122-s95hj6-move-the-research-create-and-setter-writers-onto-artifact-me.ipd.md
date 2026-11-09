# IPD: Move the research create and setter writers onto artifact_meta

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 7 step 4 requires every metadata writer to write through `artifact_meta` in phase B. The research creating and setter commands still write their front matter and history by hand (`rg -c "atomic_write\(|write_text\(|git_mv\(" agent_workflows/research_cmd.py`: 5). This is part of `n5sxxk` (itself part of `xexn45`), split 2026-11-09 so each item names one module's writers.
- Scope: Move `research_cmd.run_new` and `research_cmd.run_new_comparison` onto `artifact_meta.create` (`n5sxxk` E-01, research subset) and `research_cmd.run_set_outcome` and `research_cmd.run_set_priority` onto `artifact_meta.append` (`n5sxxk` E-02, research subset). EXCLUDES: prompts and plan scaffold (`ernmom`), adopt and set_records (`x2dxvf`), `--summary` (`bir7xm`).
- Scope-Paths: agent_workflows/research_cmd.py, agent_workflows/artifact_meta.py, .aw/records/plans/pending/20261109-metastore-122-s95hj6-move-the-research-create-and-setter-writers-onto-artifact-me.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827, executed:g6tw94
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 122
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: s95hj6

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from n5sxxk (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The research create and field-setter commands write through `artifact_meta`, each keeping a named, tested behavior.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the test modules its V-item names GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/s95hj6/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/s95hj6/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: research writers

- [ ] E-01 Move the research creating commands onto `artifact_meta.create`, pinned first (`n5sxxk` E-01, research subset): `research_cmd.run_new` and `research_cmd.run_new_comparison`. Each passes its fields and its created-history message as events; the body text stays the command's own rendering. Behaviors kept: descriptive refusals before any write (`tests/test_research_descriptive_safety.py`, `tests/test_descriptive_refusal_hoist.py`); research creation (`tests/test_research_cmd_create.py`). `research_cmd.run_new_comparison` has no direct test caller; it shares the create path that `tests/test_research_cmd_create.py` drives.
  - Depends on: none
  - Expected outcome: the three pinned modules pass before and after with equal outcome lists; `rg -n "Workflow history" agent_workflows/research_cmd.py` shows no text-building of the history section in either create function.
  - Execution state: pending

- [ ] E-02 Move the research field setters onto `artifact_meta.append`, pinned first (`n5sxxk` E-02, research subset): `research_cmd.run_set_outcome` and `research_cmd.run_set_priority`. Behaviors kept: `tests/test_research_cmd_create.py::test_run_set_outcome_apply_writes`, `tests/test_research_priority.py`.
  - Depends on: E-01
  - Expected outcome: the two pinned modules pass before and after with equal outcome lists; `rg -n "f\"- \{(date|today|hdate)\} " agent_workflows/research_cmd.py` prints no hand-built history line.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `append(id6, events, *, expect_seq)`, `create(...)`, `validate_new_events(type, events, *, records_root, migration_import=False)`. In phase B, `append` and `create` render through the one legacy renderer `artifact_meta.write_legacy` (file form) and `artifact_meta.render_legacy_text` (string form), both added by `7yr827`.
- UTC history days come from `artifact_core.utc_history_date` (spec `2vev8j` 4.4); atomic replacement is `artifact_core.atomic_write(path, text, *, prefix)`.
- Core tier: `pyproject.toml` marker `core`; modules set `pytestmark = pytest.mark.core`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by a line number alone (advisory `IPD-C801`).
- Descriptive refusals: `attention_contract.refuse_unsafe_descriptive` with `MAX_DESCRIPTIVE_LEN` 300 and `MAX_PROSE_DESCRIPTIVE_LEN` 4300.

## Findings

| Id | Evidence (measured 2026-11-09 at `3d0ddb845`) | Finding |
|---|---|---|
| F-01 | `rg -n "^def (run_new|run_new_comparison|run_set_outcome|run_set_priority)\(" agent_workflows/research_cmd.py`: all four exist | Four writer functions, one file. |
| F-02 | Pinned-module test counts (`rg -c "^\s*def test_"`): `test_research_descriptive_safety` 24, `test_descriptive_refusal_hoist` 3, `test_research_cmd_create` 20, `test_research_priority` 11 | E-01 names 6 units, E-02 names 5. |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-2 (new bullet position). KEPT: in place when present; otherwise after `- Status:`, else after `- Id:`, else end of block; never in the body (a88210). No reader depends on bullet order (`ipd_schema.parse_metadata_block` is order-free).

## Proposed changes (ordered, validatable)

1. Move the research create commands (E-01).
2. Move the research field setters (E-02).

## Deferred / out of scope (with reason)

- The family finish (the cross-module `rg` audits of the five modules and the core gate) and, after the whole writer move, the merge-independence test, the AC-21 obligations test, the raw-write audit (F-09), the documentation lines and the full gates.
  - Carrier: n5sxxk

## Scope check

- Over-scope: none.
- Under-scope: none. `agent_workflows/artifact_meta.py` is declared in case a field mapping must be added; acknowledge it at finalize when unmodified.

## Required tests / validation

No new module. Pinned before and after (equal outcome lists): the three modules of V-01 and the two of V-02.

## Spec / documentation sync

None. Implements `4sd62s` section 7 step 4 for the research commands; no documented behavior changes.

## Open questions

None open. Every question this work raised was resolved before the split; the decisions above carry the answers.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `diff` of `.aw/state/s95hj6/E-01-before.txt` and `.aw/state/s95hj6/E-01-after.txt` (must print nothing), and from `-after.txt` the PASSED lines of each named unit: the per-module PASSED counts (equal before and after) of `tests/test_research_descriptive_safety.py`, `tests/test_descriptive_refusal_hoist.py` and `tests/test_research_cmd_create.py`. Plus the E-01 `rg -n "Workflow history" agent_workflows/research_cmd.py` output, each hit labeled by its enclosing `def`, none inside `research_cmd.run_new` or `research_cmd.run_new_comparison`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `diff` of `.aw/state/s95hj6/E-02-before.txt` and `.aw/state/s95hj6/E-02-after.txt` (must print nothing), and from `-after.txt` the PASSED lines of each named unit: `tests/test_research_cmd_create.py::test_run_set_outcome_apply_writes`; the per-module PASSED count (equal before and after) of `tests/test_research_priority.py`. Plus the E-02 `rg` output for `agent_workflows/research_cmd.py` printing nothing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit s95hj6 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize s95hj6` itself.
