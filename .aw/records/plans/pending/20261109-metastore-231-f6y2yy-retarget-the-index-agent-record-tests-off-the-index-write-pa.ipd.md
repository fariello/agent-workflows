# IPD: Retarget the index agent-record tests off the INDEX write path

- Date: 2026-11-09
- Kind: child
- Concern: `snin8q` E-03 deletes the INDEX write path. Two test modules exist to test it: `tests/test_index_write_agent_records.py` (19 tests that drive `aw index <type>` as a writer and assert `INDEX.json`/`INDEX.md` changes) and `tests/test_index_check_agent_records.py` (16 tests whose fixture writes INDEX files with `plans_index.build_index_json`, `build_index_md` and their prompts and research twins). After Order 220 (`tqknnc`) the typed `aw index` spellings are aliases, so the write cases no longer describe real behavior. This is part 2 of the round-3 split of `snin8q` (Order 42), carrying that test subset of `snin8q` E-03 ("Delete or retarget the tests that assert INDEX bytes ... keeping every assertion about `aw find` results and non-INDEX drift findings").
- Scope: retarget or delete the cases of those two modules, under the PIN RULE, before any builder is deleted. EXCLUDES the builder deletions (Orders 233 to 235) and the per-type index test modules.
- Scope-Paths: tests/test_index_write_agent_records.py, tests/test_index_check_agent_records.py, .aw/records/plans/pending/20261109-metastore-231-f6y2yy-retarget-the-index-agent-record-tests-off-the-index-write-pa.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:54a80m, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:q6epwc, executed:t4gl15
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 231
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: f6y2yy

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from snin8q (round 3, research nj8zdp guidance).

## Goal

After this plan, neither module calls an INDEX builder or asserts an INDEX file, and every case that proved agent-record shape, refusal, or a non-INDEX finding still proves it through the alias or `aw check`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN RULE (carried from `9o83cr`): before the edit, save the module's per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <module> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/f6y2yy/<E>-before.txt`); after it, the same into `<E>-after.txt`. A retargeted test keeps every input case; the evidence pastes both lists and maps each removed name to its successor. "A test whose only subject is a deleted INDEX writer is deleted, and the mapping names it as an INDEX-byte-only test" (carried from `snin8q`).

### Task group 1: two modules

- [ ] E-01 Pin `tests/test_index_write_agent_records.py` and `tests/test_index_check_agent_records.py` (PIN RULE, `E-01-before.txt`).
  - Depends on: none
  - Expected outcome: `.aw/state/f6y2yy/E-01-before.txt` exists.
  - Execution state: pending

- [ ] E-02 `tests/test_index_write_agent_records.py`: delete the write-only cases (the `test_agent_write_*`, `test_json_write_*`, `test_all_write_first_and_second_run` and `test_all_write_verbose_and_json_paths` families, whose only subject is INDEX file changes); retarget the cases that prove refusal, record shape or a non-INDEX diagnostic (`test_drift_plans_missing_id`, `test_refusal_research_invalid_frontmatter`, `test_unsupported_type_specs`, `test_bare_repo_agent_refusal_per_verb`, `test_partial_tree_all_write_refusal`, `test_bare_repo_json_and_human_refusal_per_verb`, `test_explicit_dir_inside_project`, `test_inprocess_quiet_true`, and the human-invariance and mixed-outcome cases) to the alias output.
  - Depends on: E-01
  - Expected outcome: `rg -n "INDEX\.(json|md)|build_index|run_index" tests/test_index_write_agent_records.py` prints only lines asserting a file is ABSENT; the module passes.
  - Execution state: pending

- [ ] E-03 `tests/test_index_check_agent_records.py`: remove the fixture that writes INDEX files with the six builders (`plans_index.build_index_json`/`build_index_md`, `prompts_index.build_index_json`/`build_index_md`, `research_index.build_index_json`/`build_index_md`); each `--check` case keeps its non-INDEX findings and the agent-record shape assertions.
  - Depends on: E-01
  - Expected outcome: `rg -n "build_index" tests/test_index_check_agent_records.py` prints nothing; the module passes.
  - Execution state: pending

- [ ] E-04 Save `E-04-after.txt`, run both modules, and commit through `aw commit f6y2yy -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-02, E-03
  - Expected outcome: both modules pass; the mapping accounts for all 35 pinned cases.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Both modules drive the CLI through `tests.conformance_matrix.run_cli_inproc` or subprocesses and validate records with `agent_schema.validate_agent_record`.
- Tests assert on behavior, never on source text (GUIDING_PRINCIPLES P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `3d0ddb845`: `rg -c "def test"`: `tests/test_index_write_agent_records.py` 19, `tests/test_index_check_agent_records.py` 16. `rg -n "build_index" tests/test_index_check_agent_records.py` prints 6 builder calls in one fixture.

## Proposed changes (ordered, validatable)

1. Pin (E-01).
2. Retarget the write module (E-02) and the check module (E-03).
3. Verify and commit (E-04).

## Deferred / out of scope (with reason)

- Deleting the builders: Orders 233 to 235.
  - Carrier: snin8q

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 4 E-items, 2 work Scope-Paths.

## Required tests / validation

The two retargeted modules with their PIN lists, then the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change.

## Open questions

### OQ-01: Should the whole write module be deleted?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Its refusal and record-shape cases still describe the alias verbs, which keep `--agent`/`--json` contracts; only the write-only cases lose their subject. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `wc -l .aw/state/f6y2yy/E-01-before.txt` (35 lines expected) and one line from each named module.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "INDEX\.(json|md)|build_index|run_index" tests/test_index_write_agent_records.py` showing only absence assertions, and `python3 -m pytest -o addopts="" -v tests/test_index_write_agent_records.py` with each surviving case PASSED by name.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n "build_index" tests/test_index_check_agent_records.py` printing nothing, and `python3 -m pytest -o addopts="" -v tests/test_index_check_agent_records.py` with each case PASSED by name.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `diff .aw/state/f6y2yy/E-01-before.txt .aw/state/f6y2yy/E-04-after.txt` with each removed name mapped to a successor or named "INDEX-byte-only", and `git show --stat` of the `aw commit f6y2yy` commit listing only Scope-Paths files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Pin-first. Scope fence: a needed file outside `- Scope-Paths:` is edited and then justified at finalize (`--scope-reason`). Honesty rule: paste the ACTUAL summary lines. Commits: only through `aw commit f6y2yy -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
