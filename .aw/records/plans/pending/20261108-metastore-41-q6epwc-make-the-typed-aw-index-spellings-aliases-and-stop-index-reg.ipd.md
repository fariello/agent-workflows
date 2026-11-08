# IPD: Make the typed aw index spellings aliases and stop INDEX regeneration and the stale-index rules

- Date: 2026-11-08
- Kind: child
- Concern: Spec `4sd62s` 4.5 says the SQLite cache REPLACES the `INDEX.{json,md}` files, with `aw index plans|research|prompts` kept only as informational aliases of `aw index rebuild` and `check.stale-index-*` deleted. Today every typed `aw index` spelling still writes INDEX files, eleven production call sites regenerate them after a mutation, and two registered rules report a missing or stale INDEX. Measured 2026-11-07 at `ac76110f4`: `rg -n "run_index|_auto_index_types|_refresh_plans_index_fail_loud|_default_refresh_index" agent_workflows` prints 44 lines in 14 files, of which 21 are call sites or definitions in production code; `rg -n "stale-index" agent_workflows` prints 36 lines in 7 modules (`check_engine` 18, `doctor` 8, `ipd_lifecycle` 3, the three `*_index` modules 2 each, `engine` 1). Part 1 of the split of `9o83cr` (Order 11).
- Scope: `9o83cr` E-02 (aliases), E-04 (regeneration calls), E-05 (stale-index rules) and E-15 (the INDEX statements in user documents), carried verbatim with their original ids, plus a finishing item E-17. The INDEX writers are NOT deleted here (Order 42, `snin8q`, deletes them): this plan stops every CALLER of the INDEX write path and the rules that report on INDEX files, so the writers become dead code that the next part deletes. EXCLUDES: deleting `build_index_json`/`build_index_md` and the `run_index` write path (Order 42, `snin8q`), the STATUS code and `_INDEX_CACHE`, the value writers and parsers (other parts of the `9o83cr` split), and the on-disk INDEX files and ignore lines (`cxxmyv`).
- Scope-Paths: agent_workflows/artifact_types.py, agent_workflows/command_surface.py, agent_workflows/cli.py, agent_workflows/check_engine.py, agent_workflows/doctor.py, agent_workflows/ipd_lifecycle.py, agent_workflows/status_set.py, agent_workflows/artifact_rename.py, agent_workflows/research_cmd.py, agent_workflows/research_refs.py, agent_workflows/plans_refs.py, agent_workflows/artifact_adopt.py, tests/test_index_aliases.py, tests/test_drift_rule_registration.py, tests/test_doctor.py, tests/test_nv_backend_args_climb.py, tests/test_rename_group_machine_output.py, tests/test_orchestrator_retirement.py, tests/test_artifact_refs_rewrite.py, tests/test_research_rename_frontmatter.py, tests/test_group_verb_policy.py, tests/test_installed_text_current.py, docs/cli-output-contract.md, docs/cli-agent-protocol.md, README.md, CONTRIBUTING.md, CHANGELOG.md, .aw/records/plans/README.md, .aw/records/research/README.md, .aw/system/workflows/templates/agents-docs-research-README.md, .aw/records/plans/pending/20261108-metastore-41-q6epwc-make-the-typed-aw-index-spellings-aliases-and-stop-index-reg.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:t4gl15
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 41
- Highest E allocated: 17
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: q6epwc

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 9o83cr per maintainer step-complexity rule (no single E/V item hides hundreds of steps).

## Goal

After this plan, no `aw` command writes an `INDEX.json` or `INDEX.md` file and no rule reports on one: the typed `aw index` spellings print an alias notice and call `aw index rebuild`, every mutation stops regenerating INDEX files, and `check.stale-index-*` is gone from the registry, the emitters and `doctor`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Item ids E-02, E-04, E-05 and E-15 are the ids these items had in `9o83cr` (E-15 depended on `9o83cr` E-03 there; it moved here, to the plan whose E-02 makes the INDEX statements false, so the documents and the behavior change in the same merge as C10a requires); they are kept so cross-references in sibling plans still point at the right item. E-01 and E-17 are new to this part: E-01 is this part's own baseline (a subset of `9o83cr` E-01, whose residual inventory stays in `9o83cr`), because `.aw/state/` does not travel between lane worktrees; "the E-01 baseline" in the carried text means this plan's E-01.

PIN RULE for every deletion or retarget (carried from `9o83cr`): before the edit, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/q6epwc/<E>-before.txt`); after it, run the same command into `<E>-after.txt`. A retargeted test keeps every input case, so the after-list may rename a test but not drop a case; the evidence pastes both lists and maps each removed name to its successor.

### Task group 1: baseline, aliases and callers

- [ ] E-01 Record this part's baseline before any edit: save to the gitignored `.aw/state/q6epwc/before/` (never `/tmp`, which a lane integration discards) the stdout and exit code of `aw index plans --agent`, `aw index research --check --agent`, `aw check plans --all --agent`, `aw check research --all --agent`, `aw check prompts --all --agent`, `aw doctor --agent`, and the rule-id multisets of `aw check all --agent` and `aw check all --all --agent` (`jq -r '.diagnostics[].rule' | sort | uniq -c`; `--all` matters because `check_engine.check_content` reaches the `check_drift` functions only when `include_retired` is set), plus the bare core gate summary line of `python3 -m pytest`.
  - Depends on: none
  - Expected outcome: the saved outputs and the core gate summary exist under `.aw/state/q6epwc/before/`.
  - Execution state: pending

- [ ] E-02 Convert the typed index spellings into informational aliases (4.5): `aw index plans`, `aw index research`, `aw index prompts`, `aw index all` and the legacy `aw research index` call `meta_cli.index_rebuild` and print one information line ("`aw index <type>` is an alias of `aw index rebuild`; INDEX files are no longer generated"), as an `info` diagnostic in `--agent`/`--json` output and on stderr for humans. `--limit` is accepted and ignored with the same information line. `--check` runs the surviving content drift rules of that type (OQ-01) and exits as `aw check <type> --all` would (the `--all` path is the one that reaches `check_drift`, F-04). For prompts, the surviving rules are `prompts_index.check_drift`'s `name-metadata-mismatch` (today reached only through `aw index prompts --check`, not through `check_engine.check_content`); E-02 also wires `prompts_index.check_drift` into the prompts branch of `check_engine.check_content`, so the rule keeps a home once `run_index` loses its write path. Point the three `artifact_types.TYPE_BACKENDS` `index` entries at one alias function, register it in `command_surface`, and update the `cli.py` help strings that say "Regenerate INDEX.json + INDEX.md". New test module `tests/test_index_aliases.py` (core, built with `tests/record_builder.py`). Measured units: 3 `TYPE_BACKENDS` entries, 1 `cli.py` research branch (`if research_cmd == "index":`), 1 help string, 1 `command_surface` leaf, 1 `check_content` wiring, 1 new test module with 7 cases: about 14.
  - Depends on: E-01
  - Expected outcome: each spelling exits 0, prints the information line, creates no `INDEX.*` file and leaves `git status --porcelain` unchanged; `--check` on a fixture with a dangling plan citation exits nonzero naming `dangling-citation`.
  - Execution state: pending

- [ ] E-04 Delete every automatic INDEX regeneration call (F-03): `ipd_lifecycle._refresh_plans_index_fail_loud` and its call in `ipd_lifecycle._finalize_transaction` (AC-26 freshness replaces it), `status_set._auto_index_types` and its two calls, the `run_index` calls in `artifact_rename.run_rename_generic` (four sites), `research_cmd` (two sites), `research_refs` (including the "manifest was not regenerated" notes), `plans_refs.apply_renames` and `artifact_adopt._default_refresh_index`. Each affected command's result loses only its INDEX-refresh line; pin each command's other output in the touched tests first. Also update the comments that describe the deleted refresh in `ipd_lifecycle` (five comment sites name `_refresh_plans_index_fail_loud`) and `lane_containment.inventory_lane` (one comment). Measured units at `ac76110f4`: 2 definitions plus 15 call sites (`ipd_lifecycle` 1 call, `status_set` 2 calls and 2 `run_index` inside it, `artifact_rename` 4, `research_cmd` 2, `research_refs` 1, `plans_refs` 1, `artifact_adopt` 2) and 6 comment sites, in 7 production files, plus the test modules that assert a command's INDEX-refresh line or file (measured by `rg -l "INDEX\.(json|md)" tests`: `tests/test_rename_group_machine_output.py`, `tests/test_orchestrator_retirement.py`, `tests/test_artifact_refs_rewrite.py`, `tests/test_research_rename_frontmatter.py`, `tests/test_group_verb_policy.py`; each is pinned and keeps every case, asserting only on the surviving output): about 28. The `run_index` calls inside `plans_archive._refresh_index` and `research_archive` write INDEX files directly with `build_index_json`/`build_index_md`; they are deleted with the writers by Order 42.
  - Depends on: E-02
  - Expected outcome: `rg -n "run_index\(|_auto_index_types|_refresh_plans_index_fail_loud|_default_refresh_index" agent_workflows` prints only the three `run_index` definitions in `plans_index`, `research_index` and `prompts_index` (deleted or reduced by Order 42); a finalize, a rename, a group, an adopt and a research set-outcome on fixtures create no `INDEX.*` file and their next `aw find` shows the change.
  - Execution state: pending

- [ ] E-05 Delete the stale-index rules: the `check.stale-index-missing` and `check.stale-index-stale` entries of `check_engine.RULE_REGISTRY`, the code in the three `check_drift` functions that emits them, the `"stale-index" in rule` remediation branch of `doctor.build_remediation`, the priority-4 stale-index case of `doctor.resolve_next_actions` and the other `stale-index` substring sites in `doctor`, and the `stale-index` comments in `check_engine` and `ipd_lifecycle` that describe the deleted rules. Update `tests/test_drift_rule_registration.py`, `tests/test_doctor.py` and `tests/test_nv_backend_args_climb.py` to the new rule set. Measured units at `ac76110f4`: 2 registry entries, 6 emitter lines in 3 `check_drift` functions, 8 `doctor` sites, 16 `check_engine` comment lines and 3 `ipd_lifecycle` comment lines (most are one-line comment edits), 3 test modules: about 25. The stale-index assertions in `tests/test_plans_index.py`, `tests/test_research_index.py`, `tests/test_prompts_index.py` and `tests/test_index_check_agent_records.py` test INDEX bytes and are retargeted or deleted by Order 42 with the writers; in this plan they are expected to change only where an assertion names a `check.stale-index-*` id, and each such case is pinned and mapped.
  - Depends on: E-02
  - Expected outcome: `rg -n "stale-index" agent_workflows` lists only the `.aw/.gitignore` template comment in `engine.py` (cutover, F-20); `aw doctor --agent` on a fresh clone fixture with no INDEX files reports no index finding. Deleting the registry entry and the emitters together matters: an unregistered rule falls through to `check_engine._DEFAULT_RULESPEC` (severity `error`).
  - Execution state: pending

### Task group 2: documents and finish

- [ ] E-15 Update the documents that describe INDEX generation as current behavior (they become wrong when E-02 and E-03 land, C10a): `docs/cli-output-contract.md` (the `--limit` hot-window sentence and the `index` step-cue example), `docs/cli-agent-protocol.md` (the `INDEX.md` hot-window sentence), `CONTRIBUTING.md` (the two manifest bullets), `README.md` (the research `INDEX.json`/`INDEX.md` mention), `.aw/records/plans/README.md` and `.aw/records/research/README.md` with its installed template `.aw/system/workflows/templates/agents-docs-research-README.md` (the INDEX paragraphs: replace with "`aw index rebuild` rebuilds the local cache; `aw index <type>` is an alias"), keeping `tests/test_installed_text_current.py` green; add one `CHANGELOG.md` `2.0.0 (pending)` line. Write no em or en dashes in this user-facing prose.
  - Depends on: E-02
  - Expected outcome: `rg -n "INDEX\.(json|md)|STATUS\.md" README.md CONTRIBUTING.md docs .aw/records/plans/README.md .aw/records/research/README.md .aw/system/workflows/templates/agents-docs-research-README.md` prints only lines that describe the removal; `tests/test_installed_text_current.py` passes.
  - Execution state: pending

- [ ] E-17 Finish: run every test module named in those items, the bare core gate `python3 -m pytest`, `aw check all --agent` and `aw check all --all --agent` (rule multisets equal the E-01 baselines minus the `check.stale-index-*` findings; any other difference traced to a record changed in between), `aw ipd lint` on this plan, and `aw sanitize --agent`; commit through `aw commit q6epwc -- <paths>` with only Scope-Paths files, never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-04, E-05, E-15
  - Expected outcome: all runs pass; every commit's `git show --stat` lists only Scope-Paths files (or paths justified at finalize).
  - Execution state: pending

## Project conventions discovered (Step 0)

- Typed verbs route through `artifact_types.TYPE_BACKENDS` (`"index": "plans_index.run_index"`, `"research_index.run_index"`, `"prompts_index.run_index"`) and `artifact_types.resolve_backend`, dispatched by `cli._run_noun_verb`; `aw research index` has its own branch in `cli.py` (`if research_cmd == "index":`). `aw index rebuild` is added by `1ajqaa` as `meta_cli.index_rebuild(repo_root) -> CommandResult`, routed before type normalization.
- Drift findings are `artifact_core.Drift(location, rule, detail)`; severities come from `check_engine.RULE_REGISTRY` (`RuleSpec`), and an unregistered rule falls through to `check_engine._DEFAULT_RULESPEC` (severity `error`), so deleting a rule's emitter and its registry entry must happen together.
- `doctor.build_remediation` matches `"stale-index" in rule` by substring, and its comment states the five `doctor` sites must change together.
- `check_engine.check_content` calls `plans_index.check_drift` and `research_index.check_drift` only when `include_retired` is set (the `--all` path), and those functions host non-INDEX rules (F-04), so they survive with their INDEX classes removed.
- Test data comes from ONE builder, `tests/record_builder.py` (`59aiyh`); core tests carry `pytestmark = pytest.mark.core`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-07 at `ac76110f4`. F-03 and F-04 are copied from `9o83cr` (measured at `0cbfcc706`, re-checked here).

| Id | Evidence | Finding |
|---|---|---|
| F-03 | `run_index` and refresh callers: `artifact_rename.run_rename_generic` (4), `status_set._auto_index_types` (2 calls), `research_cmd` (2), `research_refs` (1), `plans_refs.apply_renames` (1), `artifact_adopt._default_refresh_index`, `ipd_lifecycle._refresh_plans_index_fail_loud` (called from `_finalize_transaction`), `cli` research branch, `artifact_types.TYPE_BACKENDS` (3). Re-measured: `rg -n "run_index|_auto_index_types|_refresh_plans_index_fail_loud|_default_refresh_index" agent_workflows` 44 lines in 14 files. | E-02, E-04. |
| F-04 | Non-INDEX drift rules inside `check_drift`: `plans_index` emits `name-metadata-mismatch` and `dangling-citation`; `research_index` emits `stale-state-to-promote`, `dangling-consumed-by`, `adopted-without-consumer`, `unrecognized-model`, `research.frontmatter-key-repeated`, `status-tier-mismatch`, `check.research-companion-orphaned`; `prompts_index` emits `name-metadata-mismatch`. | Kept; E-02 `--check` reports them. |
| F-22 | `rg -c "stale-index" agent_workflows`: `check_engine` 18, `doctor` 8, `ipd_lifecycle` 3, `plans_index` 2, `research_index` 2, `prompts_index` 2, `engine` 1; tests naming it: `test_plans_index`, `test_research_index`, `test_prompts_index`, `test_index_check_agent_records`, `test_installed_text_current`, `test_doctor`, `test_nv_backend_args_climb`. | E-05 owns all but `engine.py` (cutover) and the INDEX-byte test modules (Order 42). |

## Proposed changes (ordered, validatable)

1. Record the baseline (E-01).
2. Aliases (E-02), then delete the regeneration calls (E-04) and the stale-index rules (E-05), and update the INDEX statements in user documents (E-15).
3. Validate and commit (E-17).

## Deferred / out of scope (with reason)

- Deleting the INDEX writers (`build_index_json`, `build_index_md`, `_set_last_touched`, the write path of `run_index`, `DEFAULT_INDEX_LIMIT`, `artifact_core.emit_index_*`, the `record_producers` entries) and the INDEX-byte tests: `9o83cr` E-03, a separate deletion over a different file set.
  - Carrier: snin8q
- The STATUS code, `_INDEX_CACHE`, value writers, adapters, parsers, and the AC-1 test and audit: other parts of the `9o83cr` split, and `9o83cr` itself.
  - Carrier: 9o83cr
- Deleting the on-disk INDEX files and the INDEX ignore lines and skip names: they protect unmigrated repositories until `m0001` step 5 deletes the files.
  - Carrier: cxxmyv

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 6 E-items, 31 Scope-Paths entries (12 production modules each touched at a handful of call sites, 10 test modules, 8 documents and this plan); the largest item (E-04) hides about 28 units.

## Required tests / validation

New test module (core, built with `tests/record_builder.py`): `tests/test_index_aliases.py` (E-02, E-04 `-k producers`). Retargeted modules: `tests/test_drift_rule_registration.py`, `tests/test_doctor.py`, `tests/test_nv_backend_args_climb.py`. Commands: `python3 -m pytest` (core gate), `aw check all --agent`, `aw check all --all --agent`, `aw sanitize --agent`.

Retargeted test also: `tests/test_installed_text_current.py` (E-15). CONTRIBUTES to AC-9 (owned by `9o83cr`; final proof `cxxmyv`) and AC-26 (owned by `tve77h`).

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.5 and section 7 step 7. Documentation: E-15 updates only the INDEX statements this change makes false; `CHANGELOG.md` gains one line.

## Open questions

### OQ-01: What does `aw index <type> --check` do once INDEX drift is gone?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Carried from `9o83cr` OQ-01. It runs the non-INDEX drift classes that the same `check_drift` reported before (F-04) and exits as `aw check <type>` would, after printing the alias information line. Reason: those classes were part of what `--check` gated, so silently passing would weaken a check a user may rely on, while refusing the flag would break scripts; no CI in this repository uses it (`9o83cr` F-05). Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls -l .aw/state/q6epwc/before/` showing each saved output with its exit code, both `aw check all` rule multisets, and the core gate `N passed` summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_index_aliases.py` with every test PASSED (one per spelling: `aw index plans`, `research`, `prompts`, `all`, `aw research index`, plus `--limit` and `--check`), and a live run on this repository of `aw index plans --agent; echo rc=$?` showing the `info` alias diagnostic and `rc=0`, followed by `git status --porcelain --ignored .aw/records | grep INDEX` before and after with no new line, and `aw check prompts --all --agent` showing a planted `name-metadata-mismatch` prompt fixture reported through `check_engine.check_content` (the E-02 wiring). Code path: `artifact_types.resolve_backend` -> the alias function -> `meta_cli.index_rebuild` (E-02).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the output of `rg -n "run_index\(|_auto_index_types|_refresh_plans_index_fail_loud|_default_refresh_index" agent_workflows` showing only the three `run_index` definitions, and `python3 -m pytest -o addopts="" -v tests/test_index_aliases.py -k producers` PASSED for the fixture test that runs `aw ipd finalize`, `aw rename plans`, `aw group plans`, `aw research set-outcome` and the adopt path, then asserts no `INDEX.*` exists and `aw find` shows the change.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `rg -n "stale-index" agent_workflows` listing only the `engine.py` `.aw/.gitignore` template comment; the summary lines of `python3 -m pytest -o addopts="" tests/test_drift_rule_registration.py tests/test_doctor.py tests/test_nv_backend_args_climb.py` all passing; and `aw doctor --agent` run in a fresh `git clone` of this repository at the plan's commit, with no `index` diagnostic in its output.
  - Observed evidence:
  - Result: pending

- [ ] V-15 validates E-15
  - Required evidence: paste the `git diff` hunks of each named document, the output of the E-15 `rg` command (only removal-describing lines), `python3 -m pytest -o addopts="" tests/test_installed_text_current.py` passing, and `grep -nP "[\x{2013}\x{2014}]"` over the changed user-facing lines printing nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-17 validates E-17
  - Required evidence: paste the bare `python3 -m pytest` summary line after the edits; the `aw check all --agent` and `aw check all --all --agent` rule multiset diffs against the baseline (only `check.stale-index-*` removed, any other difference traced); `aw sanitize --agent` with zero `fail`; and `git show --stat` of every `aw commit q6epwc` commit listing only Scope-Paths files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: 31 Scope-Paths entries against a guide of about 12. The eight documents (E-15) must change in the same merge that makes their INDEX statements false (C10a), so they cannot move to a later plan. Twelve are production modules that each lose one to four INDEX call sites or comment lines for ONE concern (no command writes or reports on INDEX files), and splitting the callers from the rules would leave an intermediate merge in which `doctor` remediates a rule whose producer is gone, or the reverse. The nine test modules are pinned, not rewritten: each loses only the INDEX-refresh assertion of a command whose other output it keeps. Every E-item stays at about 25 units (E-04 about 28).

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Every deletion is pin-first (PIN RULE above). Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`). Honesty rule: paste the ACTUAL summary lines; never claim a result you did not run. Commits: only through `aw commit q6epwc -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
