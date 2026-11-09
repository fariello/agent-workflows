# IPD: Make the typed aw index spellings aliases of aw index rebuild

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` 4.5 keeps `aw index plans|research|prompts` only as informational aliases of `aw index rebuild`. Today every typed `aw index` spelling still writes `INDEX.json` and `INDEX.md` through `plans_index.run_index`, `research_index.run_index` and `prompts_index.run_index` (see `q6epwc` F-03). This is part 1 of the round-3 split of `q6epwc` (Order 41), carrying `q6epwc` E-02 (originally `9o83cr` E-02).
- Scope: the alias function, its three `TYPE_BACKENDS` entries, its `command_surface` leaf, the `cli.py` research branch and help strings, the prompts content-drift wiring in `check_engine.check_content`, and the new test module `tests/test_index_aliases.py` (minus its `producers` case, which Order 223 of the split adds). EXCLUDES: deleting any automatic regeneration call (Orders 221 to 223), the stale-index rules (Orders 224 and 225), the documents (Orders 226 and 227), and the INDEX writers (`snin8q`).
- Scope-Paths: agent_workflows/meta_cli.py, agent_workflows/artifact_types.py, agent_workflows/command_surface.py, agent_workflows/cli.py, agent_workflows/check_engine.py, tests/test_index_aliases.py, .aw/records/plans/pending/20261109-metastore-220-tqknnc-make-the-typed-aw-index-spellings-aliases-of-aw-index-rebuil.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:sdzcur, executed:t4gl15
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 220
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: tqknnc

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from q6epwc (round 3, research nj8zdp guidance).

## Goal

After this plan, `aw index plans`, `aw index research`, `aw index prompts`, `aw index all` and the legacy `aw research index` print one alias notice and call `aw index rebuild`; none of them writes an INDEX file.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

The text of `q6epwc` E-02 is split across E-01 to E-05 here; together they equal it.

PIN RULE (carried from `9o83cr`): before an edit that changes a tested command's output, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/tqknnc/<E>-before.txt`); after it, run the same command into `<E>-after.txt`. A retargeted test keeps every input case; the evidence pastes both lists and maps each removed name to its successor.

### Task group 1: the alias

- [ ] E-01 In `agent_workflows/meta_cli.py`, add one alias function `meta_cli.index_alias(args)` beside `meta_cli.index_rebuild` (created by `1ajqaa`). It calls `meta_cli.index_rebuild` and prints one information line, "`aw index <type>` is an alias of `aw index rebuild`; INDEX files are no longer generated", as an `info` diagnostic in `--agent`/`--json` output and on stderr for humans. `--limit` is accepted and ignored with the same line. `--check` runs the surviving content drift rules of that type (`q6epwc` OQ-01) and exits as `aw check <type> --all` would (the `--all` path is the one that reaches `check_drift`, `q6epwc` F-04).
  - Depends on: none
  - Expected outcome: the function exists and is callable; it writes no file.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/artifact_types.py`, point the three `index` entries of `artifact_types.TYPE_BACKENDS` (today `plans_index.run_index`, `research_index.run_index`, `prompts_index.run_index`) at `meta_cli.index_alias`; then register the alias leaf in `agent_workflows/command_surface.py`.
  - Depends on: E-01
  - Expected outcome: `artifact_types.resolve_backend` returns the alias for `index` on all three types.
  - Execution state: pending

- [ ] E-03 In `agent_workflows/cli.py`, route the legacy research branch (`if research_cmd == "index":`, today `return ri.run_index(args)`) to `meta_cli.index_alias`, and rewrite the help strings that say "Regenerate INDEX.json + INDEX.md" to describe the alias.
  - Depends on: E-01
  - Expected outcome: `rg -n "Regenerate INDEX" agent_workflows/cli.py` prints nothing; `aw research index` prints the alias line.
  - Execution state: pending

- [ ] E-04 In `agent_workflows/check_engine.py`, wire `prompts_index.check_drift` into the prompts branch of `check_engine.check_content`, so its `name-metadata-mismatch` rule (today reached only through `aw index prompts --check`) keeps a home once `run_index` loses its write path.
  - Depends on: none
  - Expected outcome: `aw check prompts --all --agent` reports a planted `name-metadata-mismatch` prompt.
  - Execution state: pending

### Task group 2: test and commit

- [ ] E-05 Create `tests/test_index_aliases.py` (core, `pytestmark = pytest.mark.core`, records built with `tests/record_builder.py`) with seven cases: one per spelling (`aw index plans`, `research`, `prompts`, `all`, `aw research index`), plus `--limit` and `--check`. Each spelling case asserts exit 0, the information line, no `INDEX.*` file and an unchanged `git status --porcelain`; the `--check` case uses a fixture with a dangling plan citation and asserts a nonzero exit naming `dangling-citation`. Then run that module and the pinned modules, and commit through `aw commit tqknnc -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the module passes; the commit lists only Scope-Paths files.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Typed verbs route through `artifact_types.TYPE_BACKENDS` and `artifact_types.resolve_backend`, dispatched by `cli._run_noun_verb`; `aw research index` has its own branch in `cli.py`. `aw index rebuild` is `meta_cli.index_rebuild(repo_root) -> CommandResult` (from `1ajqaa`), routed before type normalization.
- Test data comes from ONE builder, `tests/record_builder.py` (`59aiyh`); core tests carry `pytestmark = pytest.mark.core`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `3d0ddb845`. `rg -n "run_index" agent_workflows/artifact_types.py agent_workflows/cli.py` shows the three `TYPE_BACKENDS` entries (`"index": "plans_index.run_index"`, `"research_index.run_index"`, `"prompts_index.run_index"`) and the research branch `return ri.run_index(args)`. `check_engine.check_content` calls `plans_index.check_drift` and `research_index.check_drift` but not `prompts_index.check_drift`. Background findings F-03, F-04 and F-22 stay in `q6epwc`.

## Proposed changes (ordered, validatable)

1. The alias function (E-01).
2. Route the three backends and the research branch to it (E-02, E-03).
3. Wire the prompts drift rule (E-04).
4. Test and commit (E-05).

## Deferred / out of scope (with reason)

- The `producers` case of `tests/test_index_aliases.py` and the regeneration-call deletions: they need every caller removed first.
  - Carrier: q6epwc
- Known C10a risk carried from the earlier split: test modules that call `aw index <type>` and assert written INDEX bytes (`tests/test_index_write_agent_records.py`, `tests/test_index_check_agent_records.py`) belong to `snin8q`; if they fail at this merge, pin them, map each failing case, and justify the edit at finalize (`--scope-reason`).
  - Carrier: snin8q

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 5 E-items, 6 work Scope-Paths.

## Required tests / validation

New core module `tests/test_index_aliases.py` (E-05). Commands: `python3 -m pytest -o addopts="" -v tests/test_index_aliases.py`, the bare core gate `python3 -m pytest`, `aw check prompts --all --agent`.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.5. The documents this makes false are updated by Orders 226 and 227 of the split, which execute before `q6epwc` closes the family.

## Open questions

### OQ-01: What does `aw index <type> --check` do once INDEX drift is gone?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Carried from `q6epwc` OQ-01: it runs the non-INDEX drift classes and exits as `aw check <type> --all` would, after the alias line. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff` hunk of `agent_workflows/meta_cli.py` adding `meta_cli.index_alias`, and `rg -n "write_text|INDEX" agent_workflows/meta_cli.py` showing the alias writes no file.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "\"index\":" agent_workflows/artifact_types.py` showing all three entries naming `meta_cli.index_alias`, and the `git diff` hunk of `agent_workflows/command_surface.py` registering the leaf.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n "Regenerate INDEX|ri.run_index" agent_workflows/cli.py` printing nothing, and a live `aw research index --agent; echo rc=$?` on this repository showing the `info` alias diagnostic and `rc=0`, with `git status --porcelain --ignored .aw/records | grep INDEX` before and after showing no new line. Code path: the `cli.py` research branch -> `meta_cli.index_alias` (E-03).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `git diff` hunk of `check_engine.check_content` and `aw check prompts --all --agent` on a fixture with one planted mismatched prompt, showing `name-metadata-mismatch`. Code path: `check_engine.check_content` -> `prompts_index.check_drift` (E-04).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_index_aliases.py` showing seven PASSED cases by name (five spellings, `--limit`, `--check`); the PIN before/after lists for any pinned module; the bare `python3 -m pytest` summary line beside them; and `git show --stat` of the `aw commit tqknnc` commit listing only Scope-Paths files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Scope fence: a needed file outside `- Scope-Paths:` is edited and then justified at finalize (`--scope-reason`). Honesty rule: paste the ACTUAL summary lines; never claim a result you did not run. Commits: only through `aw commit tqknnc -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
