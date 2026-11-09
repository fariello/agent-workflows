# IPD: Move the research_refs move and set-assign field writers onto artifact_meta

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 7 step 4 requires the research shelf verbs (`aw research mv`, `aw research set-assign`, `aw archive research`) to write their metadata edits through `artifact_meta` in phase B. They edit research front matter by hand today (`research_refs.run_mv`, `research_refs.run_set_assign`, and the status rewrite `research_archive._rewrite_status_in_text` called by `research_archive.apply_moves`). This is part of `bsl45u` (itself part of `xexn45`), split 2026-11-09.
- Scope: Move the `research_refs.run_mv` and `research_refs.run_set_assign` front-matter edits and the status edit in `research_archive.apply_moves` onto `artifact_meta.append` (`bsl45u` E-01, research subset). EXCLUDES: `artifact_rename` (`1hfmpb`), `plans_refs` (`fnu6kw`).
- Scope-Paths: agent_workflows/research_refs.py, agent_workflows/research_archive.py, agent_workflows/artifact_meta.py, .aw/records/plans/pending/20261109-metastore-129-9gy5jk-move-the-research-refs-move-and-set-assign-field-writers-ont.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827, executed:fnu6kw
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 129
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 9gy5jk

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from bsl45u (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The research shelf verbs edit front matter only through `artifact_meta`; the file moves stay git moves.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the test modules its V-item names GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/9gy5jk/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/9gy5jk/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: research shelf writers

- [ ] E-01 Move the front-matter edits of `research_refs.run_mv` and `research_refs.run_set_assign` onto `artifact_meta.append`, pinned first (`bsl45u` E-01): the edited YAML keys become `set` events rendered by the legacy writer's research form; the move itself stays `artifact_core.git_mv`. Behaviors kept: `tests/test_research_rename_frontmatter.py`, `tests/test_research_set_assign_date_containment.py`.
  - Depends on: none
  - Expected outcome: the two pinned modules pass before and after with equal outcome lists.
  - Execution state: pending

- [ ] E-02 Move the status edit in `research_archive.apply_moves` (today `research_archive._rewrite_status_in_text` then `_atomic_write`) onto `artifact_meta.append`, pinned first (`bsl45u` E-01). Behaviors kept: `tests/test_research_archive.py::test_promote_to_reference_moves_to_weekly_shard_keeps_id`.
  - Depends on: E-01
  - Expected outcome: `tests/test_research_archive.py` passes before and after with equal outcome lists.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `append(id6, events, *, expect_seq)`, `create(...)`, `validate_new_events(type, events, *, records_root, migration_import=False)`. In phase B, `append` and `create` render through the one legacy renderer `artifact_meta.write_legacy` (file form) and `artifact_meta.render_legacy_text` (string form), both added by `7yr827`.
- UTC history days come from `artifact_core.utc_history_date` (spec `2vev8j` 4.4); atomic replacement is `artifact_core.atomic_write(path, text, *, prefix)`.
- Core tier: `pyproject.toml` marker `core`; modules set `pytestmark = pytest.mark.core`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by a line number alone (advisory `IPD-C801`).
- The rename ledger is `record_history.record_rename`, written by `artifact_rename` and `plans_refs`; the sidecar is gitignored (`.aw/.gitignore` `records/history.jsonl`).
- File moves stay `artifact_core.git_mv` in phase B; section 7: "the writers of path-bearing events start at the cutover commit".

## Findings

| Id | Evidence (measured 2026-11-09 at `3d0ddb845`) | Finding |
|---|---|---|
| F-01 | `rg -n "^def (run_mv|run_set_assign)\(" agent_workflows/research_refs.py`: both exist; `rg -n "_rewrite_status_in_text\(" agent_workflows/research_archive.py`: the def and one call inside `apply_moves` | Three writer sites, two files. |
| F-02 | Pinned-module test counts: `test_research_rename_frontmatter` 17, `test_research_set_assign_date_containment` 21, `test_research_archive` 26 | E-01 names 6 units, E-02 5. |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-2 (new bullet position). KEPT: in place when present; otherwise after `- Status:`, else after `- Id:`, else end of block; never in the body (a88210). No reader depends on bullet order (`ipd_schema.parse_metadata_block` is order-free).

## Proposed changes (ordered, validatable)

1. Move the research_refs edits (E-01).
2. Move the archive status edit (E-02).

## Deferred / out of scope (with reason)

- The family close-out (the after-run of the four shared rename modules against `.aw/state/bsl45u/family-before.txt`, the D-4 ledger check), and the final gates of the writer move.
  - Carrier: bsl45u

## Scope check

- Over-scope: none.
- Under-scope: none. `agent_workflows/artifact_meta.py` is declared for the research YAML form; acknowledge it at finalize when unmodified.

## Required tests / validation

No new module. Pinned before and after: the modules of V-01 and V-02.

## Spec / documentation sync

None. Implements `4sd62s` section 7 step 4 for the research shelf verbs; no documented behavior changes.

## Open questions

None open. Every question this work raised was resolved before the split; the decisions above carry the answers.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `diff` of `.aw/state/9gy5jk/E-01-before.txt` and `.aw/state/9gy5jk/E-01-after.txt` (must print nothing), and from `-after.txt` the PASSED lines of each named unit: the per-module PASSED counts (equal before and after) of `tests/test_research_rename_frontmatter.py` and `tests/test_research_set_assign_date_containment.py`. Plus `rg -n "atomic_write\(|write_text\(" agent_workflows/research_refs.py` with each remaining hit labeled by its enclosing `def` and none inside `run_mv` or `run_set_assign` writing front matter.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `diff` of `.aw/state/9gy5jk/E-02-before.txt` and `.aw/state/9gy5jk/E-02-after.txt` (must print nothing), and from `-after.txt` the PASSED lines of each named unit: `tests/test_research_archive.py::test_promote_to_reference_moves_to_weekly_shard_keeps_id`; the per-module PASSED count (equal before and after) of `tests/test_research_archive.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit 9gy5jk -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 9gy5jk` itself.
