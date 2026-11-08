# IPD: Move the plans, research and prompts module reads onto artifact_meta

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` C5a requires every record module to read metadata through the cache, and AC-9 requires that no reader depend on an INDEX file. Measured 2026-11-07 at `ac76110f4`: the plans modules read metadata with their own regexes (`plans_index._META_RE` 7 patterns, `plans_archive` 5 `^-` regexes, `plans_refs` 5), the research modules through `research_contract.parse_frontmatter` and `research_index._META_ID_RE`, and `prompts_index` through `_parse_metadata_comment`; `research_index._doc_entry` also computes `has_body` in a way the 4.1 `aw-managed` banner will break (F-09). Part 3 of the split of `t4gl15` (Order 09).
- Scope: (a) The 4.4 search rows of `t4gl15` E-01 for the 31 files outside the gate and runner files (all path-only or non-metadata at the split, named in F-03). (b) `t4gl15` E-09 (plans modules), E-10 (research and prompts modules) and E-16 (research body test ignores the banner), whole. (c) Saving the INDEX baseline that `t4gl15` E-01 required before any edit, here before this plan's first edit, because only this plan's items compare against it. EXCLUDES: the review, orchestration, production-check and work modules (Order 36, `2zpw22`); deleting the INDEX writers and parsers (Order 11); the residual audit of these modules (`t4gl15` E-15).
- Scope-Paths: agent_workflows/plans_index.py, agent_workflows/plans_archive.py, agent_workflows/plans_refs.py, agent_workflows/ipd_set_plan.py, agent_workflows/completion.py, agent_workflows/research_index.py, agent_workflows/research_archive.py, agent_workflows/prompts_index.py, tests/test_readers_record_modules.py, tests/test_plans_index.py, .aw/records/plans/pending/20261107-metastore-35-jd7874-move-the-plans-research-and-prompts-module-reads-onto-artifa.ipd.md
- Item-Dependencies: executed:ffceq0, executed:g5hpbb, executed:h58z9n, executed:tve77h, executed:xexn45
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 35
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: jd7874

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from t4gl15 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).

## Goal

The plans, research and prompts modules answer from `artifact_meta.query`/`read`, so no reader depends on an INDEX file, each move keeps a named tested behavior, and the research pipeline position ignores the 4.1 banner.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

The pin-first rule of `ffceq0` applies to every move here (carried from `t4gl15`): BEFORE the edit, a behavioral test pins the reader's current observable behavior and runs green on the unmodified code; AFTER the edit, the same test runs unchanged except where decision D-1 (copied below) names it. For every existing module named as a baseline, save the per-test outcome list under the gitignored `.aw/state/t4gl15/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/t4gl15/<E>-before.txt`) before the move and into `<E>-after.txt` after it, where `<E>` is the ORIGINAL `t4gl15` item id named below. Run a new module's `-k` selection as its own command. New test modules set `pytestmark = pytest.mark.core`; none reads production source.

### Task group 1: search rows and INDEX baseline

- [ ] E-01 (carried from `t4gl15` E-01, remaining-file subset) Before any code edit of this plan, save the `aw index plans --check`, `aw index research --check` and `aw index prompts --check` exit codes and outputs to `.aw/state/t4gl15/index-before.txt`. Then record the 4.4 search rows for the 31 files outside the gate and runner files as table F-03 in this plan: run `rg -n -e '"show"' -e 'cat-file' -e '"ls-files", "-s"' -e '"--cached"' -e '":0:"' -e 'rev-parse' agent_workflows -g '!runner_shared.py' -g '!oc_runipd.py' -g '!agy_runipd.py' -g '!check_engine.py' -g '!hooks/*' -g '!plan_readiness.py' -g '!ipd_lifecycle.py' -g '!artifact_meta.py'` (115 hits in 70 functions at `ac76110f4`) and write ONE row per function of the 21 functions with a `show`, `cat-file`, `ls-files -s` or `:0:` hit (named in F-02), each classified as path-only reader, not a metadata read, or metadata reader, and ONE bulk path-only row that names the 49 functions whose only hits are `rev-parse` or `--cached` (a commit id, ref, path or staged path list cannot carry record metadata). Any metadata reader found is a defect of the 4.4 list: name it and add it to E-02 or E-03 if it is in this plan's modules, otherwise report it for `t4gl15` E-15.
  - Depends on: none
  - Expected outcome: `index-before.txt` exists; F-03 has 21 single rows and one bulk row naming 49 functions; every metadata-reader row names the item that moves it.
  - Execution state: pending

### Task group 2: plans, research and prompts modules

- [ ] E-02 (carried from `t4gl15` E-09) Pin, then move, `plans_index` (`plan_entry`, `scan_plans`, `query`, `_meta`, `check_drift` metadata reads), `plans_archive` (`_ID_RE`, date, status and Set reads in `sweep_candidates` and `_plan_status`), `plans_refs` read side, `ipd_set_plan` (Set inventory via `plans_index.scan_plans`) and `completion` (active Set ids) onto `artifact_meta.query`. `plans_index` entries keep their fields; `status` for a multi-word plan follows D-1 of `ffceq0` (canonical value). The INDEX writers keep writing INDEX files from the same entries until Order 11 deletes them (AC-9). Pin in `tests/test_readers_record_modules.py` and run `tests/test_plans_index.py`, `tests/test_plans_archive.py`, `tests/test_plans_archive_selectors.py`, `tests/test_ipd_set_plan.py` and `tests/test_completion.py` green before and after. (Measured units at `ac76110f4`: 23 functions with a reader site across the five modules, 5 baseline modules.)
  - Depends on: E-01
  - Expected outcome: all listed modules pass before and after; `aw index plans --check` reports the same exit code and output as `.aw/state/t4gl15/index-before.txt` (any change traced to D-1); `rg -n "re\.\w+\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/plans_index.py agent_workflows/plans_archive.py` prints nothing.
  - Execution state: pending

- [ ] E-03 (carried from `t4gl15` E-10) Pin, then move, `research_index` (`_scan_docs`, the `- Status:` line reader, `resolvable_consumer_ids` with `_META_ID_RE`), `research_archive` (`research_contract.parse_frontmatter` reads) and `prompts_index` (`_parse_metadata_comment` uses) onto `artifact_meta.query`/`read`; `research_contract.parse_frontmatter` and `prompts_index._parse_metadata_comment` stay defined (writers and the legacy loader still need the grammar until Order 11) but have no reader caller outside `artifact_meta`. Pin in `tests/test_readers_record_modules.py` and run `tests/test_research_index.py`, `tests/test_research_archive.py`, `tests/test_research_companion.py`, `tests/test_prompts_index.py` and `tests/test_index_check_agent_records.py` green before and after. (Measured units: 9 functions, 5 baseline modules.)
  - Depends on: E-02
  - Expected outcome: all listed modules pass before and after; `aw index research --check` and `aw index prompts --check` report the same result as before.
  - Execution state: pending

- [ ] E-04 (carried from `t4gl15` E-16) Make the research body test ignore the 4.1 `aw-managed` banner (F-09): the value that `research_index.derive_pipeline_positions` reads as `has_body` (today computed in `research_index._doc_entry` as "any non-blank text after the closing `---`") must be false when the only text after the front matter is the single leading `<!-- aw-managed: ... -->` banner comment of `4sd62s` 4.1 plus whitespace, and true when any other text follows it. Compute it in ONE place used by every reader of `has_body`, whether that is the moved `research_index` reader or a field `artifact_meta` exposes; do not strip arbitrary HTML comments, only the leading banner. Test in `tests/test_readers_record_modules.py` with `tmp_path` research trees written in the post-cutover shape (two-key front matter plus banner): a Set holding a `research-prompt` with `outcome: none-yet` and a `reconciliation-report` whose body is only the banner yields `unrun`; adding a `research-report` whose body is the banner plus one heading yields `partial`; giving the reconciliation report the banner plus a heading yields `synthesized`. The same three trees in the pre-cutover shape (no banner) yield the same three positions.
  - Depends on: E-03
  - Expected outcome: the six fixture cases yield `unrun`, `partial`, `synthesized` in both shapes; `aw index research --check` reports the same result as before on this checkout.
  - Execution state: pending

### Task group 3: residual audit and finish

- [ ] E-05 (carried from `t4gl15` E-15, this plan's module subset) Run `rg -n "re\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?[\"'](\(\?m\))?\^-" <files>` and `rg -n "Workflow history" <files>` over `agent_workflows/plans_index.py`, `agent_workflows/plans_archive.py`, `agent_workflows/plans_refs.py`, `agent_workflows/ipd_set_plan.py`, `agent_workflows/completion.py`, `agent_workflows/research_index.py`, `agent_workflows/research_archive.py` and `agent_workflows/prompts_index.py` (18 hits in 10 functions at `ac76110f4`, before this plan) and write table F-04 in this plan listing every remaining hit with its owner: writer (Orders 06/07, named; for example `plans_refs._set_metadata`), body-prose bullet kept by N3 (named pattern), or a parser that Order 11 deletes. A reader hit with no such owner is a defect of this plan and is moved before finishing. Then run every module named in E-02 to E-04 and the bare core gate `python3 -m pytest`, and commit through `aw commit jd7874 -- <each changed path>`, never `git add -A`, a bare `git add` or `git commit -a`. Never push.
  - Depends on: E-04
  - Expected outcome: F-04 has no unowned reader hit; all runs pass; every commit is path-scoped to Scope-Paths (or justified at finalize).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Interface names: `artifact_meta.read(id6) -> State`, `artifact_meta.query(...)` (type, status, Set, order, `path` filters, `incomplete` list), from `tve77h`; decision D-1 from `ffceq0`.
- The plans index writer and reader are one module (`plans_index.run_index`, `scan_plans`, `plan_entry`, `query`); `ipd_set_plan` and `completion` consume `scan_plans`; `plans_archive` reads `_idx._EXCLUDE_NAMES` and calls `scan_plans`.
- Cite code by SYMBOL (`module.function`), never a bare line number (advisory `IPD-C801`).

## Findings

Measured 2026-11-07 at `ac76110f4`; F-09 copied from `t4gl15` (measured 2026-11-05).

| Id | Evidence | Finding |
|---|---|---|
| F-01 | AST pass over `rg` hits of each module's reader symbols (`_META_RE`, `_ID_RE`, `_DATE_RE`, `_SET_LINE_RE`, `_ORDER_LINE_RE`, `scan_plans(`, `parse_frontmatter(`, `_parse_metadata_comment(`, `_META_ID_RE`, `_plan_status(` and the `^-` regex pattern): `plans_index` 12 sites in 6 functions, `plans_archive` 11 in 8, `plans_refs` 22 in 6, `ipd_set_plan` 1, `completion` 2, `research_index` 6 in 4, `research_archive` 2, `prompts_index` 3 | E-02 has 23 functions; E-03 has 9. |
| F-02 | The 21 functions outside the gate and runner files with a `show`/`cat-file`/`ls-files -s`/`:0:` hit at `ac76110f4`: `cli.<module>`, `cli._build_parser`, `cli._dispatch`, `cli._oc_profile_show`, `cli._rewrite_help_token`, `cli._run_oc_profile`, `cli._run_show`, `cli._run_show_meta`, `command_surface.<module>`, `completion.complete_query`, `layout_migration._is_removable_leftover`, `leak_sanitizer.scan_staged_counted`, `leak_sanitizer.scan_working_tree_counted`, `meta_cli.show_history`, `meta_cli.show_json`, `project_context._git_cached_entries`, `run_analytics_taxonomy.<module>`, `run_cli.run_cli`, `run_viewer.<module>`, `typecheck_gate._tree_declares_mypy`, `worktree_lease._lane_base_sha` | Most are the `show` sub-command NAME, not `git show`; `t4gl15` F-07 classified the rest as path-only or non-metadata. |
| F-03 | (written by E-01) the classified rows | 4.4 says the list is a minimum. |
| F-04 | (written by E-05) residual `^-` regex and `Workflow history` hits in this plan's eight modules, with owners. Measured at the split: `plans_index` 6, `plans_archive` 5, `plans_refs` 5, `research_index` 2, the other four 0 | Input to `t4gl15` E-15 and Order 11. |
| F-09 | `research_index._doc_entry` sets `has_body` true for any non-blank text after the closing `---`, and `derive_pipeline_positions` uses it to place a Set `unrun`, `partial` or `synthesized`. `4sd62s` 4.1 puts the `aw-managed` banner after the front matter of every artifact; forcing every `has_body` true moves Set `awclia` from `unrun` to `synthesized`, because its reconciliation report `v912ed` has no body today. Found by research `53jbi5` findings E-2/E-3. | E-04 fixes it before Order 13 (`cxxmyv`). |

READER LEDGER (copied from `t4gl15`):

| Reader | Prior behavior | Pinning test | After |
|---|---|---|---|
| `plans_index`, `plans_archive`, `ipd_set_plan`, `completion` | whole-file `_META_RE` reads (whole-line status) | `tests/test_plans_index.py`, `tests/test_plans_archive.py`, `tests/test_plans_archive_selectors.py`, `tests/test_ipd_set_plan.py`, `tests/test_completion.py` | D-1 status; other fields unchanged |
| `research_index`, `research_archive`, `prompts_index` | YAML and `aw-prompt` comment parse | `tests/test_research_index.py`, `tests/test_research_archive.py`, `tests/test_research_companion.py`, `tests/test_prompts_index.py`, `tests/test_index_check_agent_records.py` | cached fields |

DECISIONS (copied from `t4gl15`, whose text is authoritative): D-1 PLAN records return the canonical normalized status; `plans_index` and `ipd_set_plan` lose the prose status line for the 24 multi-word executed plans (none runnable or in a pending Set), and any `tests/test_plans_index.py` assertion on a whole-line status may change (in Scope-Paths). D-3 the cache carries research YAML status and `id`, so each consumer gets the answer it gets today.

## Proposed changes (ordered, validatable)

1. INDEX baseline and the remaining-file 4.4 rows (E-01).
2. Pin then move the plans modules (E-02), the research and prompts modules (E-03).
3. Banner-blind research body test (E-04).
4. Residual audit, commit (E-05).

## Deferred / out of scope (with reason)

- The review, orchestration, production-check, work and adoption modules.
  - Carrier: 2zpw22
- Deleting the INDEX writers and `plans_index._META_RE`.
  - Carrier: 9o83cr

## Scope check

- Over-scope: none. `tests/test_plans_index.py` changes only in D-1 assertions.
- Under-scope: none known. Size: 5 E-items, 11 Scope-Paths; per-item units: E-01 115 hits classified as 21 rows plus 1 bulk row, E-02 23 functions plus 5 baselines, E-03 9 plus 5, E-04 1 function plus 6 cases, E-05 18 hits in 10 functions.

## Required tests / validation

New test module: `tests/test_readers_record_modules.py` (core). CONTRIBUTES to `4sd62s` AC-9 (reader parts: no reader depends on an INDEX file; deletion is Order 11). Commands: every module named in E-02 to E-04, the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change. Implements the record-module part of `4sd62s` C5a.

## Open questions

### OQ-01: Why is the INDEX baseline taken here rather than in Order 33?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Only this plan's items compare against it, and no earlier part edits the INDEX code; `.aw/state/` is gitignored and does not travel between lane worktrees, so the baseline is taken in the same worktree that consumes it. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls -l .aw/state/t4gl15/index-before.txt` older than this plan's first code commit, the exact `rg` command of E-01 with its output line count, and the F-03 table (21 single rows and one bulk row naming 49 functions), every metadata-reader row naming the item that moves it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_readers_record_modules.py -k plans` all PASSED, `diff .aw/state/t4gl15/E-09-before.txt .aw/state/t4gl15/E-09-after.txt` (outcome lists of `tests/test_plans_index.py tests/test_plans_archive.py tests/test_plans_archive_selectors.py tests/test_ipd_set_plan.py tests/test_completion.py`) printing nothing or only D-1 lines, `aw index plans --check; echo $?` compared with `.aw/state/t4gl15/index-before.txt`, and the empty output of `rg -n "re\.\w+\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/plans_index.py agent_workflows/plans_archive.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_readers_record_modules.py -k "research or prompt"` all PASSED, `diff .aw/state/t4gl15/E-10-before.txt .aw/state/t4gl15/E-10-after.txt` (outcome lists of `tests/test_research_index.py tests/test_research_archive.py tests/test_research_companion.py tests/test_prompts_index.py tests/test_index_check_agent_records.py`) printing nothing, and `aw index research --check; echo $?` and `aw index prompts --check; echo $?` compared with `.aw/state/t4gl15/index-before.txt`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_readers_record_modules.py -k banner` with six tests PASSED (`unrun`, `partial`, `synthesized` for the banner shape and for the no-banner shape), each asserting the position `derive_pipeline_positions` returns for its `tmp_path` tree; `aw index research --check; echo $?` with the same exit code as `.aw/state/t4gl15/index-before.txt`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the two `rg` commands of E-05 and the F-04 table (every remaining hit with its owner, none unowned); the bare `python3 -m pytest` summary line and wall time; and every `aw commit jd7874` output listing only Scope-Paths (or paths justified at finalize).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every `- Item-Dependencies:` edge is executed. OQ-01 is resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every reader move is pin-first.

Honesty rule: run the named modules and `python3 -m pytest` (core gate), and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit jd7874 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
