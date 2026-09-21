# IPD: Attention view correctness and drift audit fixes

- Date: 2026-09-17
- Kind: child
- Concern: bugs
- Scope: agent_workflows/attention.py, agent_workflows/specs.py, and attention regression tests
- Scope-Paths: agent_workflows/attention.py,agent_workflows/specs.py,tests/test_attention.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: attcor (attention-correctness)
- Order: 1
- Highest E allocated: 13
- Author: Antigravity
- Id: rkn8ya
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-19 approved (aw set): status set to approved

- 2026-09-18 reviewed (opencode/its_direct-pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-014, all 14 FIXED, none deferred, none open (three of the plan's own FINDINGS, F-04/F-09/F-10, are now explicitly out of scope with typed reasons, which is a scope decision recorded in the plan and not an unfixed review finding). Every one of the 14 authored findings was re-derived from the code rather than trusted, and the finding-to-E-item mapping was wrong in five ways: E-01 covered ONE of THREE identical prune sites; V-05 demanded evidence the rule can never produce; E-03 was a measured no-op; E-06 named a derived table the code comments forbid editing; and E-12 instructed the executor to DELETE `arcive_state`, which is a shipped, tested CLI alias, not a typo. F-09 and F-10 had no E-item at all while the plan claimed all 14 were proposed for remediation. Eleven E-items survive with corrected sites, fixtures, and per-item tests.
- 2026-09-17 to-review (Antigravity): /assess bugs: assessed; proposed 14 changes.

## Goal

Remediate the bugs and contract violations discovered during the /assess-bugs audit of `agent_workflows/attention.py`: restore fail-closed drift filtering under every CLI narrowing, make release-blocker matching precise, revive the dead disposition check under the modern `.aw/` layout, eliminate the absolute-path leak in spec validation, and align set-name grammar parsing with the naming authority.

REVIEW RESET THE SCOPE FROM 14 FINDINGS TO 10 EXECUTED FIXES, and the reason belongs in the Goal because it changes what "done" means for this plan. The audit that produced this plan listed 14 findings and wrote 13 execution items; review re-derived all 14 from the code and found the mapping wrong in five ways (see the Workflow history line above and the findings table below). Two findings are now explicitly DEFERRED with typed reasons rather than counted as in scope:

- F-04 (unclassified files under `.aw/records/`) is UNREACHABLE as scoped. `iter_scan_files` never yields those files, so the authored edit was a measured no-op; making it reachable requires widening `SCAN_ROOTS` in `artifact_core.py` (not in `Scope-Paths`) and would emit 226 new violations from `.aw/records/reviews/`, breaking `aw attention --check` repo-wide.
- F-09 (`last_history_at` reads the oldest record) is REAL and measured (338 of 640 multi-record plans misread) but is already OWNED by approved spec `2vev8j`, whose section 4.3 rules OUT the resolution this plan's OQ-01 proposed.

The remaining scope is one BLOCKER-class fail-closed defect (F-01, whose blast radius review widened from one prune site to three), one security leak (F-05), and eight correctness/UX fixes, each with its own regression test.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Fail-closed drift filtering and path sanitization

- [x] E-01 Fix the drift pruning in `run()` so a contract violation from a SELECTED TREE survives every narrowing, at ALL THREE prune sites. REVIEW WIDENED THIS ITEM: the authored version named only the `--types` prune, and the identical five-line prune appears three times: types (`attention.py:2884-2886`), selectors (`:2892-2896`), and the combined status/priority/blocking/readiness/open-questions/run-status prune (`:2990-2993`). Fixing one leaves two live. The bug is that each prunes drift to `selected_paths`, the paths of surviving ITEMS, but an artifact that fails to parse yields drift and NO item (`_plans_record` returns `None, drift` at `:977-979`; `scan()` does `if rec is None: continue` at `:461-462` AFTER `drift.extend`), so its violation is silently deleted. Measured with one unparseable plan present: bare `--check` exits 1, `-t plans --check` exits 0, `selectors=['abc123'] --check` exits 0. THE RETENTION RULE, decided by review (D-4) and not left to the executor: retain a drift record whose location is under a SELECTED TREE, not all drift unconditionally. Retaining all drift would resurrect stranded-lane drift under an explicit narrowing, contradicting the deliberate suppression documented at `:3005-3010` and spec `F3a`'s normative exclusions. Prefer ONE shared helper called from all three sites over three edited copies, since three copies is what let this bug hide.
  - Depends on: none
  - Expected outcome: `aw attention --check` fails closed with an unparseable artifact present under EACH of `-t plans`, a selector narrowing, and a status/priority narrowing; and stranded-lane drift is still suppressed under an explicit `--types`/selector narrowing (no change to that behavior). Cites spec `20260808-1945-01-attention-registry-and-cross-tree-status.spec.md:202` ("never silently skips a malformed included artifact") as the invariant restored. A regression test covers all three narrowings.
  - Execution state: performed
- [x] E-02 Stop leaking the machine-local absolute path from spec validation: make the Drift `location` repo-relative. `_spec_record` (`attention.py:932`) passes the ABSOLUTE `path` to `specs_mod.validate_spec`, which sets `loc = str(path)` (`specs.py:211-215`) and uses it for every Drift. Reproduced by review with a temp-dir fixture: both the human `--check` line and the JSON `location` carried `/tmp/.../bad.spec.md`. THREE FACTS REVIEW ADDED, because without them an executor may conclude there is no bug. (1) `_spec_record` is the ONLY offender: every sibling builder already passes the relative `rel` (`_plans_record:978,983,1001`; `_research_record:1061,1074`; `_backlog_record:1127,1132`; `_release_record:897,904`; `scan()`'s own drift at `:449,454,479`), so passing `rel` matches an established precedent rather than inventing one. (2) `aw check` MASKS the leak by relativizing defensively (`check_engine.py:386-393`), which is why `aw specs check` prints clean; a fix inside `validate_spec` is therefore safe for that other caller. (3) `specs.py:437` has the same `str(p)` pattern on the unreadable-file path in `check` and should be fixed in the same pass. Violates spec section 8.5 ("NO ... absolute paths").
  - Depends on: none
  - Expected outcome: Every Drift location emitted for a spec is a repo-relative POSIX path, asserted by equality against the expected relative string (not merely by an `is_absolute()` check), on both the `aw attention --check` and `aw specs check` surfaces. `aw sanitize --agent` reports no new finding.
  - Execution state: performed

### Task group 2: Filter matching and disposition logic

- [x] E-04 Fix `matches_blocking` so `--blocking next` resolves against the PLANNED release instead of short-circuiting. `attention.py:1633-1635` does `if tok == "next": return True` inside `elif is_blk:`, so every gated item matches whatever release it names. The data for the correct predicate already exists and is cached: `_get_planned_release_info` (`:1592`, `lru_cache`) returns `(planned_id6, planned_version)` and `_resolve_release_version` (`:1914`, `lru_cache`) resolves a raw value, and lines `:1638-1643` ALREADY implement this reasoning for version/id6 tokens; the `next` branch simply bypasses it. Decide and state the no-planned-release case explicitly: when `_get_planned_release_info` returns `("", "")`, `next` matches nothing (a behavior change, and the honest one).
  - Depends on: none
  - Expected outcome: `--blocking next` matches items gated on the planned release and EXCLUDES an item gated on a different or past release. THE TEST MUST USE A SYNTHETIC TWO-RELEASE FIXTURE: review measured that this tree cannot distinguish the fixed from the broken behavior, because all 250 blocking artifacts point at `next` (248) or `f33nrj` (2), and `f33nrj` IS the single planned release, so `--blocking next` returning 250 is coincidentally correct today. A test written against the live tree would pass either way.
  - Execution state: performed
- [x] E-05 Revive the dead disposition-vs-terminal-status check under the modern `.aw/` layout. `attention.py:990-994` computes `disp` only when `rel.startswith(".agents/plans/")`, so every modern `.aw/records/plans/<disp>/...` path yields `disp = ""` and the rule at `:995-1006` never fires. SCOPE CORRECTED BY REVIEW: fix the PREFIX only. The authored second clause ("non-terminal plan statuses in terminal directories") is REMOVED as an undeclared expansion of the spec's F3 violation set: the rule's third conjunct is `status in plans_mod.TERMINAL` (`:998`), so a non-terminal status like `draft` in `executed/` is deliberately NOT drift, in either layout (review verified both). Whether it SHOULD be is a separate contract decision for the spec, not a prefix bug. Derive the disposition the way `check_engine._plan_disposition` (`:1244-1263`) already does, taking the FIRST component under the plans dir, so an `aw archive plans` shard (`<disposition>/YYYYMM/`) is still recognized; a `parent.name` test would silently stop working on sharded plans.
  - Depends on: none
  - Expected outcome: A plan at `.aw/records/plans/executed/...` whose `- Status:` is `superseded` emits `attention.disposition-mismatch`; the same file under a `executed/YYYYMM/` shard also emits it; and a plan whose status matches its directory emits nothing. Measured baseline recorded so the fix is provably not a no-op: this tree currently has 0 terminal-status/directory disagreements, so the test MUST construct a fixture.
  - Execution state: performed
- [x] E-06 Accept the `med` alias at the priority filter PARSE boundary only. `parse_priority_filters` (`attention.py:1513-1515`) is a bare passthrough and `matches_priority` (`:1582-1589`) does exact membership, and `--priority` carries no argparse `choices` (`cli.py:3766-3773`), so `aw att --priority med` silently returns 0 items instead of erroring. `med` is already accepted inside this same module by `PRIORITY_RANK` (`:1941`) and is written in the table docstring at `:2397`, so normalizing it removes an internal inconsistency. DO NOT TOUCH `_PRIORITY_SORT_RANK` (`:528`) OR `A.PRIORITY_ORDER`: the authored item named `_PRIORITY_SORT_RANK`, but it is DERIVED from the shared vocabulary and the comment at `:524-527` explicitly records that hardcoding a second copy is the mistake `ipd_schema` already made when a duplicated status table desynced. Normalize at parse time so exactly one vocabulary remains.
  - Depends on: none
  - Expected outcome: `aw att --priority med` returns the same item set as `--priority medium`; `A.PRIORITY_ORDER` and `_PRIORITY_SORT_RANK` are unchanged (asserted); and `aw ipd set`/`aw specs set`/`aw backlog set` continue to REJECT `med` via their existing argparse `choices`, so the alias stays a read-side convenience and never enters an artifact.
  - Execution state: performed
- [x] E-07 Move the `--open-questions` default-visibility narrowing from the FILTER stage to the RENDER stage, so it matches every other filter. REVIEW CORRECTED THE MECHANISM: the authored finding said `items` is mutated in place, and it is not: both statements at `attention.py:2931` and `:2935` REBIND `items` to a new list comprehension. The real defect is the SECOND narrowing at `:2932-2935`, which drops `DONE`/`PARKED` inside the filter stage, where no other filter does it. Every other path defers that decision to the render stage and computes `show_all` there (`:2430-2433`, `:3072-3081`, `:3153-3155`), and the JSON/agent renderers (`:3097-3145`) deliberately apply NO visibility narrowing. Measured asymmetry: `--priority high --format json` keeps 67 `done` + 2 `parked`, while `--open-questions --format json` keeps 0 of either. It also poisons the drift prune at `:2977-2993`, since the shrunken item set shrinks `selected_paths`, so a violation on a `done` artifact carrying open questions is dropped from `--check`. Preserve the `--all`/selector/terminal-status escape hatch behavior exactly; the existing test at `tests/test_attention.py:1348-1440` pins it and must keep passing.
  - Depends on: none
  - Expected outcome: `--open-questions --format json` includes terminal-class items with open questions (matching how `--priority` behaves), while the DEFAULT human board still hides them; `tests/test_attention.py:1348-1440` still passes unchanged for the `--all` case; and a violation on a `done` artifact with open questions is no longer dropped from `--check`.
  - Execution state: performed

### Task group 3: Grammar parsing, ordering, and rendering

- [x] E-08 Make set/order parsing agree with the naming AUTHORITY instead of a third private regex. `_NAME_GRAMMAR_RE` (`attention.py:520-522`) uses `[A-Za-z0-9]+` for the set id, which excludes the hyphen that `artifact_naming.build_clustered_name` PRODUCES (it kebab-cases the set id, `:172`) and that `_CLUSTERED_RE` accepts (`:107-110`). Measured: 104 of the 1197 clustered-conformant files in this tree parse differently under attention's regex than under the authority (88 plans, 15 backlog, 1 review), all sorting as absent under `-o set` and `-o order`. Note the module comment at `:516-519` attributes the 156 non-matching names to "grandfathered pre-cutover names"; that attribution is partly WRONG and should be corrected in the same edit, since 104 are fully conformant modern names failing only on the hyphen. PREFER DELEGATION to `artifact_naming.parse_clustered` over widening the regex; if delegation is genuinely impossible, the widening MUST use the LAZY quantifier `[a-z0-9-]+?`, because a GREEDY `[a-z0-9-]+` introduces a NEW mis-parse (for `20260101-foo-12-abc123-bar-01-def456-slug.ipd.md` greedy yields setid `foo-12-abc123-bar`/order `01` while the authority yields `foo`/`12`). Review measured the lazy form to agree with `parse_clustered` on all 1197 files. Drop the authored phrase "optional trailing slugs": the regex is unanchored at the tail and already ignores the slug.
  - Depends on: none
  - Expected outcome: For every clustered-conformant filename in the repo, attention's `(setid, order)` equals `artifact_naming.parse_clustered`'s `(set, nn)`; a hyphenated real example sorts under its true set (use an existing file such as `20260917-gate-contract-01-dcri4s-...`, NOT the authored `prompt-lib`, which exists nowhere in this tree); and a non-conformant grandfathered name still sorts as absent rather than raising.
  - Execution state: performed
- [x] E-09 Treat `blocks_release == "-"` as ABSENT in the `-o blocking` sort key. `attention.py:671-673` tests truthiness, so the literal string `"-"` sorts as `(_PRESENT, "-")` and `-` (0x2D) collates below every alphanumeric, placing a declared non-blocker ABOVE real blockers. This is the ONE reader of four that omits the guard: `:1613` (`matches_blocking`), `:1727` (`release_blockers`), `:1918` (`_resolve_release_version`), and `:2446` (the render-time flag) all explicitly exclude `"-"`, so this is a consistency fix aligning the outlier. RECORDED AS LATENT, so nobody over-claims impact: `releases.set_blocks_release_line` (`releases.py:116-125`) REMOVES the line for value `-`, and review measured 0 artifacts carrying `Blocks-Release: -` in this tree (250 `next`, 2 `f33nrj`), so only a hand-edit produces the condition.
  - Depends on: none
  - Expected outcome: Under `-o blocking`, an item declaring `-` sorts with the non-blockers, below items gated on a real release. Because the condition is latent, the test MUST construct a synthetic item (or fixture file) carrying `Blocks-Release: -`; a test written against the live tree would be vacuous.
  - Execution state: performed
- [x] E-10 Teach `_extract_detail` to read an UNBULLETED key so a research doc's `summary:` reaches `--details`. Every pattern in `_FIELD_PATTERNS` (`attention.py:249-255`) requires the `-\s*` bullet, but research frontmatter is plain YAML. Measured: 110 research files carry an unbulleted `summary:` and 0 carry `- Summary:`, so `_extract_detail` over the research tree yields `{title: 110, None: 4, scope: 3}` and the `summary:` key is never used. The H1 fallback is usually adequate but not equivalent: `_H1_RX` (`:256`) strips a leading `Word:` prefix, turning `# Research: the design prompts...` into the fragment `the design prompts that produced spec 25kzda`, and 4 files have no H1 at all so they show NO detail despite carrying a summary. Keep the existing cascade order and the bulleted forms working; accept the unbulleted form IN ADDITION. Note 55 files in `.aw/records/` carry an unbulleted key in the BODY rather than the frontmatter, so prefer a frontmatter-scoped match to avoid picking up prose.
  - Depends on: none
  - Expected outcome: A research doc whose frontmatter carries `summary: <text>` reports `('summary', '<text>')` from `_extract_detail`; the 4 files with no H1 now report a detail; and every currently-working bulleted artifact (plans, specs, backlog) reports the SAME detail as before (assert no regression on the existing cascade).
  - Execution state: performed
- [x] E-11 Fix TWO distinct display collisions at width 8 and width 9, both stated with their measured slices because the authored item named the second without giving it an outcome. (a) STATUS, `attention.py:2158` `st_raw = it.native_status[:8]` (padded at `:2166`, header `"Status".ljust(8)` at `:2510`): `implementing` and `implemented` both slice to `implemen`. Color distinguishes them (`:1413-1414`) but ONLY on a color TTY, so `--no-color` and every piped/machine read cannot tell active from finished work. (b) READINESS, `:2225-2233`: the color heuristic is a substring test on a 9-char slice, so `go-pending-approval` slices to `go-pendin` and takes 114, the SAME green as a cleared `go`, i.e. an UNAPPROVED plan renders as approved. That is the more serious of the two, since it misreports an approval state. Fix both without breaking alignment for the other statuses (`not-exec`, `supersed`, `to-revie`, `reviewed`, `approved` are all currently distinct).
  - Depends on: none
  - Expected outcome: With color disabled, `implementing` and `implemented` render as distinguishable text; and `go-pending-approval` is distinguishable from `go` in both text and color. Column alignment is unchanged for every other status/readiness value (assert against the existing table snapshot expectations).
  - Execution state: performed
- [x] E-12 Emit the `CommandResult` that the no-project `--agent`/`--json` path builds and throws away. REVIEW REWROTE THIS ITEM ENTIRELY, and the reason matters: the authored version said "clean up duplicate `return 3` statement and fix `arcive_state` typo", and BOTH halves were wrong. (a) There is exactly ONE `return 3` in the file (`attention.py:2839`). The real defect is that the `CommandResult` built at `:2832-2837` is never passed to `get_renderer(ctx).emit(res, ctx)`, so `aw attention --agent` outside an AW project writes prose to stderr and NOTHING to stdout, breaking the agent envelope contract. The correct sibling is 10 lines above at `:2828`, and the scan-error branch at `:2863` also does it right. Reproduced: `rc=3`, `stdout=''`, `stderr=` the prose message. A secondary leak to fix in the same pass: `no_project_message` interpolates `Path.cwd()` (`project_context.py:339`), so this path writes an absolute machine path, the same class as E-02. (b) THE `arcive_state` CLAUSE IS DELETED AND MUST NOT BE ACTED ON. `arcive_state` is NOT a typo: it is a deliberate legacy alias for the shipped `--arcive-state` flag, set by the custom `_RunStatusAction` (`cli.py:804-816`), defaulted at `cli.py:3805`, declared among six spellings at `cli.py:3808-3812`, and asserted by `tests/test_attention.py:2064-2066`. Removing it would break a user-facing flag and a passing test.
  - Depends on: none
  - Expected outcome: `aw attention --agent` and `--format json` run from a directory that is not an AW project emit a valid `aw.agent/v1` envelope on STDOUT with `status: cannot-run` and exit 3, and that envelope carries no absolute machine path. `getattr(args, "arcive_state", ...)` at `:2947` is UNCHANGED and `tests/test_attention.py:2064-2066` still passes.
  - Execution state: performed

### Task group 4: Regression test suite

- [x] E-13 Reconcile the per-item regression tests against the executed items, then run the bare suite. Each E-item above owns its own test (named in its expected outcome), so this ONE concern is reconciliation: confirm every executed E-item landed an identifiable test, confirm no test encodes a DEFERRED finding's behavior (F-04, F-09 and F-10 are out of scope), and paste a green bare `python3 -m pytest`. REVIEW NARROWED THIS ITEM: the authored version claimed "regression tests for all 14 audit findings", impossible when only ten findings have an E-item, and bundling ten independent test surfaces into one item made V-13 a tautology. Note `tests/test_releases.py` left `Scope-Paths`: every fix lives in `attention.py`/`specs.py`, so E-04's release fixture belongs in `tests/test_attention.py`.
  - Depends on: E-01, E-02, E-04, E-05, E-06, E-07, E-08, E-09, E-10, E-11, E-12
  - Expected outcome: Every executed E-item has an identifiable regression test; no test encodes F-04 or F-09 behavior; and a bare `python3 -m pytest` is green with the actual summary line pasted.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Clustered plan naming `YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md` in `.aw/records/plans/pending/`.
- Fail-closed invariant on `aw attention --check`, normative in spec `20260808-1945-01-attention-registry-and-cross-tree-status.spec.md:202`: "`--check` completes a FULL scan, collects ALL detectable violations, and returns them together; it never silently skips a malformed included artifact." F-01 violates this directly.
- Absolute path sanitization in all agent/human outputs, normative in the same spec's section 8.5 ("NO generation timestamps, mtimes, absolute paths"). F-05 violates this directly.
- `artifact_naming.py` is the SINGLE naming authority (`_CLUSTERED_RE`, `parse_clustered`, `build_clustered_name`); a second private copy of that grammar is the defect behind F-06, and `attention.py` currently holds two (`_NAME_GRAMMAR_RE:520`, `_STEM_RE:1732`).
- One shared vocabulary per concept: `attention_contract.PRIORITY_ORDER` is the priority vocabulary and `_PRIORITY_SORT_RANK:528` derives from it, with the comment at `:524-527` recording that a duplicated copy desynced once already. This is why E-06 normalizes at the parse boundary and touches neither.

## Findings

Severity is as authored (reporting only). The Verified column is what review determined by reading and running the code, and the E-item column is the honest mapping. Ten findings have an execution item; two are DEFERRED with typed reasons; two describe a real defect at the cited lines but named the wrong mechanism and were rewritten.

| ID | Severity | Verified | E-item | Finding |
|----|----------|----------|--------|---------|
| F-01 | Blocker | TRUE, understated | E-01 | Drift pruning purges contract violations, breaking the fail-closed invariant. Review widened it: the same prune exists at THREE sites (`attention.py:2884`, `:2892`, `:2990`), not just the `--types` one. Measured: `--check` exits 1 bare, 0 under `-t plans`, 0 under a selector. |
| F-02 | High | TRUE | E-04 | `--blocking next` short-circuits (`:1633-1635`) and matches every gated item regardless of which release it names. Not observable on this tree (all 250 blockers point at the planned release), so the test needs a fixture. |
| F-03 | High | PARTIALLY TRUE | E-05 | The disposition-mismatch check is dead under the `.aw/` layout (`:990-994` tests `.agents/plans/` only). The authored V-05 was UNSATISFIABLE: the rule requires `status in plans.TERMINAL` (`:998`), so a `draft` in `executed/` can never fire it. Scope narrowed to the prefix fix. |
| F-04 | Medium | TRUE on the letter, fix unreachable | none (DEFERRED) | `attention.unclassified-tree` never fires for `.aw/records/`. But `iter_scan_files` never yields those files (`SCAN_ROOTS` lists per-type roots, `artifact_core.py:278-294`), so the authored edit was a measured no-op. Widening `SCAN_ROOTS` emits 226 new violations from `.aw/records/reviews/`. See Deferred. |
| F-05 | Medium | TRUE | E-02 | Machine-local absolute path leaked from `validate_spec` (`specs.py:211-215`), reproduced on both the human and JSON surfaces. `_spec_record` is the only offender; `aw check` masks it by relativizing (`check_engine.py:386-393`). |
| F-06 | Medium | TRUE | E-08 | Set/order regex rejects hyphenated set ids. Measured: 104 of 1197 clustered-conformant files disagree with the naming authority. The authored "allow hyphens" is UNDER-SPECIFIED: a greedy widening introduces a new mis-parse; delegate to `parse_clustered`, or use the lazy quantifier. |
| F-07 | Medium | TRUE | E-11 | `implementing` and `implemented` both slice to `implemen` at width 8 (`:2158`). Review found a SECOND, more serious collision the authored item did not give an outcome: `go-pending-approval` slices to `go-pendin` and colors the same green as a cleared `go` (`:2225-2233`), so an unapproved plan renders as approved. |
| F-08 | Medium | TRUE but LATENT | E-09 | `blocks_release == "-"` sorts as present and above real blockers (`:671-673`), the one reader of four omitting the guard. Zero artifacts carry `-` today (the setter removes the line, `releases.py:116-125`), so the test needs a synthetic item. |
| F-09 | Medium | TRUE, understated | none (DEFERRED) | `last_history_at` reads the oldest record because the writer PREPENDS (`status_set.py:935-948`) while the reader takes the last in file order (`attention_contract.py:582-591`). Measured: 338 of 640 multi-record plans misread. Already owned by approved spec `2vev8j` (its E3), whose section 4.3 RULES OUT the resolution OQ-01 proposed. See Deferred. |
| F-10 | Low | PARTIALLY TRUE, wrong site | none (DEFERRED) | The named sites are NOT defects: `_resolve_release_version:1914` and `_get_planned_release_info:1592` are both `lru_cache`d (4 reads for 250 items, 2 reads for 1085). The real redundancy is `_reclassify_stale_research` -> `cited_by_executed_ids` (`research_index.py:401`) re-walking the corpus: 823 redundant reads on a full scan, and 1048 reads to report 110 items under `-t research`. See Deferred. |
| F-11 | Low | TRUE | E-06 | `--priority med` silently returns 0 items: `parse_priority_filters:1513` is a passthrough and `--priority` has no argparse `choices` (`cli.py:3766-3773`), while `PRIORITY_RANK:1941` in the same module already accepts `med`. |
| F-12 | Low | MECHANISM FALSE, defect real | E-07 | `items` is REBOUND, not mutated (`:2931`, `:2935`), so the authored V-07 ("preserve all items") was wrong as a goal. The real defect: `--open-questions` is the ONE filter applying default visibility in the FILTER stage, so its `--format json` and `--check` payloads silently drop terminal items (measured: `--priority high` keeps 67 done, `--open-questions` keeps 0). |
| F-13 | Low | TRUE | E-10 | `_extract_detail` requires a `- ` bullet (`:249-255`), so 110 research files carrying an unbulleted `summary:` never use it (0 carry `- Summary:`); 4 files with no H1 show no detail at all. |
| F-14 | Low | (a) MISDESCRIBED, (b) FALSE | E-12 | (a) There is ONE `return 3`; the real defect is a `CommandResult` built and never emitted (`:2832-2837`), so `--agent` outside a project gets prose and empty stdout. (b) `arcive_state` is NOT a typo: it is a shipped legacy alias with an argparse action (`cli.py:804-816`), a default (`:3805`), and a passing test (`tests/test_attention.py:2064-2066`). The authored instruction to "fix" it was a REGRESSION instruction and is deleted. |

## Proposed changes (ordered, validatable)

Ten changes, one per surviving E-item. The authored list had 13 entries; three are gone (the unclassified-tree extension is deferred, the `arcive_state` edit was a regression instruction, and the blanket test item became a reconciliation pass).

1. Retain drift from a selected TREE at all three prune sites, even when the file produced no item (E-01, Low).
2. Make spec-validation Drift locations repo-relative, killing the absolute-path leak (E-02, Low).
3. Resolve `--blocking next` against the planned release instead of short-circuiting (E-04, Low).
4. Fix the disposition check's `.agents/`-only prefix so it fires under `.aw/records/plans/` (E-05, Low).
5. Accept the `med` priority alias at the parse boundary only (E-06, Low).
6. Move the `--open-questions` visibility narrowing to the render stage (E-07, Low).
7. Delegate set/order parsing to `artifact_naming.parse_clustered` (E-08, Low).
8. Treat `blocks_release == "-"` as absent in the `-o blocking` sort key (E-09, Low).
9. Read an unbulleted frontmatter key in `_extract_detail` (E-10, Low).
10. Fix the status-width and readiness-color collisions (E-11, Low).
11. Emit the `CommandResult` on the no-project agent/json path; leave `arcive_state` alone (E-12, Medium: it touches a shared output path).
12. Reconcile the per-item regression tests and run the bare suite (E-13, Low).

## Deferred / out of scope (with reason)

The authored plan said "None. All 14 findings ... are proposed for remediation." That was FALSE even as authored (F-09 and F-10 had no E-item), and review added a third deferral. Each carries the axis, the threshold reason, the required decision, and the consequence.

- **F-04, unclassified files under `.aw/records/`. DEFERRED, Remediation Risk Medium-High (axes: functionality, complexity).** Why it reaches the threshold: the fix is not the one-line condition the plan assumed. `iter_scan_files` never yields the files (`SCAN_ROOTS` at `artifact_core.py:278-294` lists individual `.aw/records/<type>` roots, not `.aw/records` itself), so editing `attention.py:429` alone is a measured no-op. Making it reachable means widening `SCAN_ROOTS`, which is shared with `find_dangling_citations` (`artifact_core.py:446-463`) and is not in `Scope-Paths`. Measured blast radius: 226 new `attention.unclassified-tree` violations, ALL from `.aw/records/reviews/`, a legitimate tracked tree that has no `TreePolicy` entry (`attention_contract.TREE_POLICY` lists ten trees and `reviews` is not among them). Required decision or evidence: add a `reviews` TreePolicy (and audit `comms`/`prompts`, currently `tracked=False`) BEFORE widening the scan roots. Consequence if unresolved: a rogue file under an uninventoried `.aw/records/` subtree stays invisible to `--check`, which is the blind spot spec section 8.6 exists to prevent. This is a real gap and wants its own plan.
- **F-09, `last_history_at` reads the oldest record. DEFERRED, Remediation Risk Medium-High (axis: functionality).** Why it reaches the threshold: it is not a local fix and it is already OWNED elsewhere. Approved spec `2vev8j` records this exact defect as its measured E3 (`:71-73`) and its section 4.3 (`:169-182`) rules that the fix is an explicit per-artifact `seq` and that the reader must "stop depending on direction at all", explicitly rejecting both a direction flip and a date sort. OQ-01's proposed "select the maximum date" is therefore contrary to an approved contract. Required decision or evidence: implement `2vev8j`'s history model, or amend that spec; either way the plan must declare the `.spec.md` in `Scope-Paths` and say why in its spec-sync section. Consequence if unresolved: `-o date` keeps mis-ordering (measured: 338 of 640 multi-record plans), and any consumer of `last_history_at` inherits it. Tracked by `2vev8j`, not by this plan.
- **F-10, redundant reads. DEFERRED, Remediation Risk Medium (axes: complexity, functionality).** Why it is deferred rather than fixed here: the finding named the wrong sites (both are `lru_cache`d, so a "fix" there would change nothing), and the real site is a whole second corpus pass in `_reclassify_stale_research` -> `cited_by_executed_ids` that ignores `type_filters`. Fixing it means threading the type filter into `research_index`, i.e. editing a module outside `Scope-Paths` on a path that decides research CLASSIFICATION, not display. Required decision or evidence: confirm that narrowing the citation walk cannot change a research item's class. Consequence if unresolved: `-t research` reads 1048 files to report 110 items; a performance cost only, with no correctness impact, which is why it is the lowest-priority deferral.

## Scope reconciliation at execution (2026-09-21)

Recorded here so the finalize scope gate has the reasons in the plan, not only in a commit message.

DECLARED PATHS, all three MODIFIED (no `--scope-ack` needed):

- `agent_workflows/attention.py` - E-01, E-04..E-12.
- `agent_workflows/specs.py` - E-02 (`drift_location`, `validate_spec`, and the same `str(p)` leak on `run_check`'s unreadable-file path).
- `tests/test_attention.py` - the ten new per-item test classes, plus three pre-existing tests amended where they PINNED a behavior an E-item deliberately changes (disclosed in the relevant V-items).

ONE OUT-OF-SCOPE EDIT, with its justification (`--scope-reason`):

- `agent_workflows/artifact_naming.py` (+29 lines: `_CLUSTERED_PREFIX_RE` and `parse_clustered_prefix`). REQUIRED BY AN EXISTING GUARD TEST, not chosen. E-08 says "PREFER DELEGATION to `artifact_naming.parse_clustered`; if delegation is genuinely impossible, the widening MUST use the LAZY quantifier". The lazy widening was implemented first and it FAILED `tests/test_naming_authority_single_source.py::test_clustered_regex_defined_in_exactly_one_module`, which refuses any second copy of the clustered-grammar regex anywhere in the package. Since `parse_clustered` anchors at the tail with a CLOSED facet enum it cannot read a research name's prefix, so full delegation required the authority to EXPOSE a prefix reader. Adding it there is the option that satisfies both the E-item's stated preference and the guard; the alternative (keeping a private regex in `attention.py`) leaves the suite red and re-creates the exact duplication this item removes. The precedent followed is `research_contract._CORE_RE = _naming._CORE_RE`: the grammar lives once, in the authority, and consumers re-export it. ADDITIVE ONLY: no existing symbol changed, so no other caller is affected.

DELIBERATE EXCLUSIONS HONORED: `agent_workflows/artifact_core.py` and `agent_workflows/research_index.py` (the deferred findings' real sites) and `agent_workflows/cli.py` are UNTOUCHED, and NO `.spec.md` was edited. E-07's change does not alter the documented `--check` payload SHAPE (the keys and their order are unchanged; only which items populate `items` under one filter changes, which Section 8.3 does not fix), so the conditional spec amendment in the spec-sync section was not triggered.

TWO BACKLOG ITEMS FILED for defects found outside this scope: `5x195l` (`aw ipd --agent` crashes in a non-project directory, the same contract conflict as E-12 at `cli.py:8127`) and `06ngnx` (`test_turn_bounds` fails inside a lane run because it inherits `OPENCODE_CONFIG_CONTENT`).

## Scope check

- Over-scope: the authored E-03 (unclassified `.aw/records/` files) was over-scope because its real fix requires `artifact_core.py`, which is not declared; it is removed and deferred. The authored E-05's second clause (non-terminal statuses in terminal directories) was over-scope because it would expand the spec's F3 violation set without amending the spec; it is removed. The authored E-12's `arcive_state` clause was worse than over-scope (a regression instruction) and is deleted.
- Under-scope: the authored E-01 was under-scope (one of three prune sites) and is widened. The authored E-11 was under-scope (named the readiness color check with no expected outcome) and now carries both. `agent_workflows/specs.py` was missing from `Scope-Paths` although E-02 must edit it, and is added. `tests/test_releases.py` is removed from `Scope-Paths` since no fix touches releases code.
- F-09 and F-10 remain under-scope BY DECISION, recorded in the Deferred section rather than left implicit.

## Required tests / validation

- Bare test suite: `python3 -m pytest`. Run it BARE; the configured `addopts` already make it quiet, parallel and fast-scoped, and adding flags either slows it several-fold (`-n0`) or suppresses the `N passed` summary line this plan requires you to paste (`-q`).
- Targeted: `python3 -m pytest tests/test_attention.py` (plus `tests/test_specs_verbs.py tests/test_spec_priority.py tests/test_work_kind.py` for E-02, since they assert on `validate_spec` Drift and a location change could break them).
- End-to-end reproductions to paste, not just unit assertions: the three `--check` narrowings for E-01, the `--agent` envelope outside a project for E-12, and the `--priority med` item count for E-06.

## Spec / documentation sync

Not "N/A". Two obligations, one required and one conditional.

- REQUIRED, and it is a documentation defect this plan should fix in passing: the comment at `attention.py:516-519` attributes the 156 non-matching filenames to "grandfathered pre-cutover names". Review measured that 104 of them are fully conformant modern names failing only on the hyphen, so the comment is misleading about the code's own correctness and E-08 must correct it.
- CONDITIONAL: no `.spec.md` edit is expected, because every fix here RESTORES behavior the attention spec already mandates (section 8.5 for E-02, `:202` for E-01, F3's disposition condition for E-05) rather than changing a contract. Two carve-outs the executor must respect: E-05 must NOT widen the F3 violation set to non-terminal statuses (that would need a spec amendment, which is why review removed it), and if E-07's render-stage move changes the documented `--check` payload shape, the spec's section 8.3 payload description must be amended in the same change and declared in `Scope-Paths`.

## Open questions

### OQ-01: Historical prepended history parsing (F-09)

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: RESOLVED as OUT OF SCOPE, and the authored resolution was REFUTED rather than adopted. The authored text proposed that the parser "select the maximum date rather than relying on line order"; approved spec `2vev8j` section 4.3 (`:169-182`) explicitly rejects that, ruling that ordering must come from an explicit per-artifact `seq` and that a timestamp is "NEVER used to order", and it answers the oldest-versus-newest question "NEITHER WAY" by removing the dependence on direction. The defect is real and measured (338 of 640 multi-record plans in this tree; `2vev8j:71-73` records it as E3) but belongs to that spec's implementation, not to this plan. No E-item exists for F-09 by decision. Do not implement a date-max reader here: it would contradict an approved, release-blocking contract.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

Note the gap at `V-03`: its `E-03` was removed pre-approval (F-04 deferred, see the Deferred section), the row carried no observed evidence, and the `Highest E allocated: 13` watermark is deliberately NOT decreased, so suffix 03 is never reused (`ipd-spec` sections 5.6 and 6.1).

- [x] V-01 validates E-01
  - Required evidence: Three pasted `aw attention --check` runs against a fixture repo containing one unparseable artifact, showing a NONZERO exit and the drift line under EACH narrowing: `-t plans`, a selector, and a status filter. Plus a fourth run showing stranded-lane drift still SUPPRESSED under an explicit `--types` narrowing (the deliberate behavior at `attention.py:3005-3010` must not regress). A test that exercises only `-t plans` does NOT satisfy this item.
  - Observed evidence: FOUR narrowings driven against a fixture repo holding one good plan (`aaaaaa`, `to-review`), one UNPARSEABLE plan (`bbbbbb`, `- Status: frobnicated`, which yields drift and no item) and one clean spec. Commands run as `python3 -m agent_workflows attention --check --dir <fixture> <narrowing>` (the `python3 -m` form is REQUIRED in this lane: the console `aw` script resolves to the main checkout's editable install via PYTHONPATH, so it would have measured code this lane never changed):

    ```text
      bare       rc=1  1 unknown-status line(s)
      types      rc=1  1 unknown-status line(s)   (-t plans)
      selector   rc=1  1 unknown-status line(s)   (aaaaaa)
      status     rc=1  1 unknown-status line(s)   (--status to-review)
    ```

    The retained line under each narrowing is `.aw/records/plans/pending/20260101-fix-02-bbbbbb-bad.ipd.md: attention.unknown-status: plan status 'legacy/unknown'`. BEFORE the fix the same fixture gave `rc=1` bare but `rc=0` under `-t plans` and `rc=0` under the selector, which is the fail-closed hole.

    STRANDED-LANE SUPPRESSION PRESERVED, measured in the same runs against the real repository: the bare `--check` printed 11 `attention.lane-stranded` rows plus the artifact violations, while `-t plans` and the selector narrowing printed ZERO lane rows. Pinned by `DriftSurvivesEveryNarrowingTests::test_stranded_lane_drift_is_still_suppressed_under_an_explicit_narrowing`.

    THE OTHER HALF OF THE RETENTION RULE is also pinned: `test_drift_from_an_UNSELECTED_tree_is_still_pruned` shows `-t plans` retains the plans violation (`bbbbbb`) and drops a spec violation (`dddddd`), so the fix did not trade a false negative for a false positive.

    Tests: `DriftSurvivesEveryNarrowingTests` (3 tests), all four narrowings in one parameterized case. MUTATION-CHECKED: with `agent_workflows/attention.py` stashed, `test_an_unparseable_artifacts_violation_survives_all_three_narrowings` and `test_drift_from_an_UNSELECTED_tree_is_still_pruned` both FAIL, so neither is vacuous.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: The Drift `location` for a failing spec asserted EQUAL to the expected repo-relative POSIX string (not merely asserted non-absolute), on both `aw attention --check` and `aw specs check`. Plus pasted output of `aw sanitize --agent` showing no new finding, and a pasted run of `tests/test_specs_verbs.py tests/test_spec_priority.py tests/test_work_kind.py` confirming the existing `validate_spec` assertions still pass.
  - Observed evidence: EQUALITY asserted, not mere non-absoluteness. `SpecDriftLocationIsRepoRelativeTests` asserts `d.location == ".aw/records/specs/20260101-aaaaaa-01-aaaaaa-bad.spec.md"` for an absolute input path, `== ".agents/docs/specs/bad.md"` for the legacy layout, and `== "s.md"` for an already-relative input (the shape 20+ existing callers pass).

    BOTH SURFACES, driven end to end:

    ```text
    $ python3 -m agent_workflows attention --check --dir <fixture> -t specs
    .aw/records/specs/20260101-aaaaaa-01-aaaaaa-bad.spec.md: attention.unknown-status: status 'frobnicated' not in the spec enum
    rc=1

    $ python3 -m agent_workflows specs check --dir <fixture>
    .agents/docs/specs/20260101-aaaaaa-01-aaaaaa-bad.spec.md: attention.unknown-status: status 'frobnicated' not in the spec enum
    rc=1

    $ python3 -m agent_workflows specs check --dir <fixture> --json   # diagnostics[].location
    ['.agents/docs/specs/20260101-aaaaaa-01-aaaaaa-bad.spec.md']

    $ python3 -m agent_workflows attention --dir <fixture> -t specs --format json   # violations[].location
    ['.aw/records/specs/20260101-aaaaaa-01-aaaaaa-bad.spec.md']
    ```

    BEFORE the fix both attention surfaces carried the machine-local ABSOLUTE path (the operator's home directory, then the checkout path, then `.aw/records/specs/...`), reproduced during execution; `aw specs check` looked clean only because `check_engine` relativizes defensively downstream. (The leaked string is DESCRIBED rather than pasted here: pasting it would put the very path this fix removes into a tracked artifact, and the repository's leak hook correctly refuses that.)

    LEAK SCAN:

    ```text
    $ python3 -m agent_workflows sanitize --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    rc=0
    ```

    THE FOUR `validate_spec`-ASSERTING MODULES, unchanged and green:

    ```text
    $ python3 -m pytest tests/test_specs_verbs.py tests/test_spec_priority.py tests/test_work_kind.py
    46 passed in 2.59s
    ```

    (`tests/test_spec_review_attestation.py` also asserts on `validate_spec` and on `drift.location` containing `str(p)`; it was run and passes, included in the 90-test run of the five affected modules.)

    Tests: `SpecDriftLocationIsRepoRelativeTests` (4 tests). MUTATION-CHECKED: with `specs.py` stashed, `test_validate_spec_emits_a_repo_relative_location_for_an_absolute_path`, `test_the_legacy_layout_is_relativized_too` and `test_neither_attention_surface_carries_the_absolute_path` all FAIL.

    IMPLEMENTATION NOTE (decision 12-rkn8ya-D2): `validate_spec` is documented PURE and takes no `repo_root`, so the location is derived by a pure helper `specs.drift_location` that truncates at the known records segment. A `Path.cwd()` relativization was REJECTED because it would make identical bytes depend on the invocation directory, violating the same spec section 8.5 that forbids the absolute path.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: A test using a SYNTHETIC fixture with TWO release records (one `planned`, one `shipped`) showing `--blocking next` includes the item gated on the planned release and EXCLUDES the item gated on the other. State explicitly what `next` returns when no planned release exists. A test run against the live repo tree does not satisfy this item, because all 250 live blockers point at the planned release so both the broken and the fixed code return the same set.
  - Observed evidence: SYNTHETIC TWO-RELEASE FIXTURE built as required: release `pppppp` (v1.0.0, `planned`) and release `ssssss` (v0.9.0, `shipped`), with three backlog items gated on `next`, on `ssssss`, and on `pppppp` respectively. Measured:

    ```text
    aaaaaa backlog 'next'   --blocking next => True    (the planned release, by symbol)
    cccccc backlog 'pppppp' --blocking next => True    (the same release, by id6)
    bbbbbb backlog 'ssssss' --blocking next => False   (a DIFFERENT, shipped release: EXCLUDED)
    ```

    BEFORE the fix all three returned True, because `matches_blocking` did `if tok == "next": return True` before looking at which release the item named.

    THE NO-PLANNED-RELEASE CASE, stated explicitly as the item demands. With the same fixture and `pppppp` flipped to `shipped` (so NO planned release exists), `--blocking next` matches NOTHING:

    ```text
    no planned release -> next matches: []
    --blocking any still matches: ['aaaaaa', 'bbbbbb', 'cccccc']
    ```

    That is a deliberate BEHAVIOR CHANGE and the honest answer: `next` names a release record, and with no record there is no release for an item to gate. `--blocking any` remains the way to list every gated item, so no capability is lost. Both halves are pinned by `BlockingNextResolvesAgainstThePlannedReleaseTests` (2 tests).

    THE LIVE TREE IS UNCHANGED, confirming the fix is not a silent regression of the real board: `--blocking next` still matches 426 items on this tree, composed of 424 carrying `next` and 2 carrying the planned release's id6 `f33nrj`. (The plan's authored figure was 250; the corpus has grown since review. The COMPOSITION is what matters and it is exactly as review described: every live blocker points at the planned release by one of its two spellings, which is why a live-tree test would have been vacuous.)

    TWO PRE-EXISTING TESTS ENCODED THE DEFECT AND WERE CORRECTED, which is disclosed rather than buried. `test_blocking_filtering` asserted "'next' matches any release blocker regardless of tag/number" with `repo_root=None` (no planned release), and `test_research_blocks_release_frontmatter_vs_body` used a fixture with no release record at all. The first now asserts the corrected contract (with a new `--blocking any` block proving that capability is intact); the second gained a `planned` release record so `next` has something to resolve against, leaving its actual subject (front matter versus quoted body text) untouched.

    MUTATION-CHECKED: with `attention.py` stashed, both `BlockingNextResolvesAgainstThePlannedReleaseTests` tests FAIL.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: A fixture plan at `.aw/records/plans/executed/...` whose `- Status:` is `superseded` (a TERMINAL status) emits `attention.disposition-mismatch`; the same file under an `executed/YYYYMM/` archive shard also emits it; and a plan whose status matches its directory emits nothing. Do NOT use a `draft` status: the rule requires `status in plans.TERMINAL` (`attention.py:998`), so a non-terminal status can never fire it and such a test would fail against correct code.
  - Observed evidence: A FIXTURE was built as the item requires (the live tree has ZERO terminal-status/directory disagreements, re-measured during execution, so a live-tree test would be vacuous). Four fixture plans, and exactly the two intended rows fire:

    ```text
    DRIFT .aw/records/plans/executed/20260101-d-01-aaaaaa-mismatch.ipd.md        attention.disposition-mismatch dir executed vs status superseded
    DRIFT .aw/records/plans/executed/202609/20260101-d-02-bbbbbb-shard-mismatch.ipd.md attention.disposition-mismatch dir executed vs status superseded
    drift count 2
    ```

    * `executed/` holding `- Status: superseded` (a TERMINAL status) -> FIRES.
    * the same file under the `executed/YYYYMM/` ARCHIVE SHARD -> FIRES (the disposition is the FIRST component under the plans dir, as `check_engine._plan_disposition` already derives it; a `parent.name` test would have read `202609` and silently missed every sharded plan).
    * `superseded/` holding `- Status: superseded` (status matches directory) -> emits NOTHING.
    * `executed/` holding `- Status: draft` -> emits NOTHING, and this is the deliberate SCOPE BOUNDARY review set: the rule's third conjunct is `status in plans_mod.TERMINAL`, so a non-terminal status can never fire it, and widening that would change the spec's F3 violation set without amending the spec. The item explicitly forbids using `draft` as the positive case, and it is used here only as a NEGATIVE control.

    THE FIX IS PROVABLY NOT A NO-OP: before it, `disp` was computed only for a path starting `.agents/plans/`, so all 702 plans in this tree (`.aw/records/plans/...`) yielded `disp = ""` and the rule fired for none of them. After it, the live tree still reports 0 disposition-mismatch findings (correctly: nothing disagrees) while the fixture reports 2.

    Tests: `DispositionMismatchFiresUnderTheModernLayoutTests` (3 tests). MUTATION-CHECKED: with `attention.py` stashed, the plain and the archive-sharded cases both FAIL.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: `aw att --priority med` and `aw att --priority medium` return an IDENTICAL item set (paste both counts). Plus an assertion that `attention_contract.PRIORITY_ORDER` and `_PRIORITY_SORT_RANK` are unchanged, and a pasted refusal showing `aw backlog set ... --priority med` is still rejected by its argparse `choices` (the alias must not become writable into an artifact).
  - Observed evidence: IDENTICAL item sets, both counts pasted, measured on the live tree:

    ```text
    $ python3 -m agent_workflows attention --priority med    --all --id6-only | wc -l
    208
    $ python3 -m agent_workflows attention --priority medium --all --id6-only | wc -l
    208
    ```

    Before the fix `--priority med` returned 0 items (a silent empty answer to a typo, which is worse than an error). `parse_priority_filters(['med'])` now returns `{'medium'}`, identical to `parse_priority_filters(['medium'])`.

    THE SHARED VOCABULARY AND THE SORT RANK ARE UNCHANGED, asserted rather than asserted-about:

    ```text
    PRIORITY_ORDER      ('high', 'medium', 'low')
    _PRIORITY_SORT_RANK {'high': 0, 'medium': 1, 'low': 2}
    ```

    Neither was touched: normalization happens at the PARSE boundary, so exactly one vocabulary survives downstream. (The authored item named `_PRIORITY_SORT_RANK` as an edit target; review removed that, because it is DERIVED from `A.PRIORITY_ORDER` and its own comment records that hardcoding a second copy is the mistake `ipd_schema` already made.)

    THE ALIAS IS READ-SIDE ONLY, and the setter still refuses it:

    ```text
    $ python3 -m agent_workflows backlog set done <id6> --priority med
    agent-workflows backlog set: error: argument --priority: invalid choice: 'med' (choose from 'high', 'low', 'medium')
    ```

    So `med` can never be WRITTEN into an artifact. `aw specs set --priority med` is refused by the same argparse `choices` mechanism (asserted in the test).

    Tests: `PriorityMedAliasTests` (3 tests). MUTATION-CHECKED: with `attention.py` stashed, `test_med_and_medium_select_the_same_items` FAILS.
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: `--open-questions --format json` includes terminal-class (`done`/`parked`) items carrying open questions, matching what `--priority high --format json` already does (paste both class breakdowns). The DEFAULT human board still hides them. `tests/test_attention.py:1348-1440` passes unchanged. And a `--check` run showing a violation on a `done` artifact with open questions is no longer dropped. Do NOT assert "all items are retained": a filter is supposed to remove non-matching items, and the authored wording to that effect was wrong.
  - Observed evidence: BOTH CLASS BREAKDOWNS pasted, measured on the live tree with `--format json`:

    ```text
    --priority high    --format json classes: {'active': 25, 'blocked': 1, 'done': 90, 'parked': 2, 'ready': 54}
    --open-questions   --format json classes: {'active': 1,  'done': 92, 'parked': 14, 'ready': 51}
    ```

    The two now behave the SAME WAY. Before the fix the second read `{'active': 1, 'ready': 51}` with ZERO `done` and ZERO `parked`, because `--open-questions` was the ONE filter applying default visibility inside the FILTER stage; every other filter defers that to the RENDER stage, and the JSON/`--agent` renderers deliberately apply no visibility narrowing at all.

    THE DEFAULT HUMAN BOARD STILL HIDES THEM, which is the behavior the old filter-stage narrowing was really protecting:

    ```text
    $ python3 -m agent_workflows attention --oqs --no-color | grep hidden
    ## done (92) [hidden; use --all]
    ## parked (14) [hidden; use --all]
    ```

    The render stage recomputes the same `show_all` predicate (`args.all or selectors or has_terminal_status`), so this holds by construction rather than by care.

    THE `--check` HOLE IS CLOSED. A `done` artifact carrying an open question AND a contract violation used to have its violation pruned (the shrunken item set shrank `selected_paths`). Now:

    ```text
    $ python3 -m agent_workflows attention --check --dir <fixture>        # bare
    .aw/records/plans/executed/20260101-oq-01-aaaaaa-done-with-oq.ipd.md: attention.disposition-mismatch: dir executed vs status superseded
    rc=1
    $ python3 -m agent_workflows attention --check --dir <fixture> --oqs  # narrowed
    .aw/records/plans/executed/20260101-oq-01-aaaaaa-done-with-oq.ipd.md: attention.disposition-mismatch: dir executed vs status superseded
    rc=1
    ```

    THE `--all` CASE PASSES UNCHANGED: the pre-existing `test_open_questions_filter` `--all` assertions (both ids returned) are byte-identical and green. Its NON-`--all` JSON assertion was INVERTED deliberately (it required exactly 1 item; it now requires both), and a NEW assertion on the HUMAN surface was added in the same test to pin the default-hiding behavior where it legitimately lives. NO assertion of the form "all items are retained" was written; the item forbids it and it would be wrong (a filter is supposed to remove non-matching items).

    Tests: the amended `AttentionFilteringTests::test_open_questions_filter`.
  - Result: pass
- [x] V-08 validates E-08
  - Required evidence: A parity assertion over every clustered-conformant filename in the repo showing attention's `(setid, order)` equals `artifact_naming.parse_clustered`'s `(set, nn)` (review measured 104 disagreements before the fix; expect 0 after). Plus a case showing the ambiguous stem `20260101-foo-12-abc123-bar-01-def456-slug.ipd.md` parses as setid `foo` / order `12`, matching the authority and NOT the greedy reading. Use a real hyphenated file such as `20260917-gate-contract-01-dcri4s-...`; the authored fixture `prompt-lib` exists nowhere in this tree.
  - Observed evidence: PARITY OVER THE WHOLE REPOSITORY, 0 disagreements:

    ```text
    clustered-conformant items: 1148
    attention/authority (setid, order) DISAGREEMENTS: 0
    ```

    Before the fix there were 103 disagreements (the plan's authored figure was 104; re-measured on today's corpus it is 103, all of the same kind: 88 plans and 15 backlog items whose set id contains a HYPHEN, which `[A-Za-z0-9]+` rejected). All of them sorted as ABSENT under `-o set` and `-o order`. Also measured: 127 items that previously had NO sort key now have their true one, and 0 items LOST a key they previously had.

    THE AMBIGUOUS STEM parses the authority's way, not the greedy way:

    ```text
    20260101-foo-12-abc123-bar-01-def456-slug.ipd.md  ->  attention ('foo', 12)   authority ('foo', 12)
    ```

    A greedy `[a-z0-9-]+` would have yielded set `foo-12-abc123-bar` / order `01`.

    A REAL HYPHENATED FILE from this tree, as the item requires (the authored `prompt-lib` example exists nowhere here):

    ```text
    20260917-gate-contract-01-dcri4s-stop-the-plan-gate-execution-contract-from-prescribing-a-han.ipd.md -> ('gate-contract', 1)
    ```

    A GRANDFATHERED name still sorts as absent rather than raising:

    ```text
    20260808-1945-01-attention-registry-and-cross-tree-status.spec.md -> (None, None)
    ```

    And a RESEARCH facet name keeps its key through the authority's prefix reader:

    ```text
    20260826-awclia-03-3uh9j3-aw-cli-naming-ia.gemini31pro.research-report.md -> ('awclia', 3)
    ```

    IMPLEMENTED BY DELEGATION, WITH NO REGEX IN THIS MODULE, which is stronger than the item asked for and was FORCED by an existing guard test. The first attempt widened attention's own regex with the lazy quantifier as the item permits; that failed `tests/test_naming_authority_single_source.py::test_clustered_regex_defined_in_exactly_one_module`, which correctly refuses a second copy of the clustered grammar anywhere in the package. The grammar now lives ONLY in `artifact_naming`: full names go through `parse_clustered`, and the prefix reading goes through a NEW `artifact_naming.parse_clustered_prefix` (defined in the authority, following the precedent by which `research_contract` re-exports `_CORE_RE`). This is the one out-of-scope file edit and it is declared in the scope reconciliation.

    THE MISLEADING COMMENT IS CORRECTED, as the spec-sync section requires: the note attributing all 156 non-matching names to "grandfathered pre-cutover names" now records that most were fully conformant modern names the module's own regex rejected.

    Tests: `NameGrammarAgreesWithTheNamingAuthorityTests` (5 tests) plus the pre-existing single-source guard. MUTATION-CHECKED: with `attention.py` stashed, the repository parity test and the hyphenated-set-id test both FAIL.
  - Result: pass
- [x] V-09 validates E-09
  - Required evidence: With a SYNTHETIC item carrying `Blocks-Release: -`, `-o blocking` places it with the non-blockers, below items gated on a real release. A test over the live tree is vacuous: review measured 0 artifacts carrying `-` (250 `next`, 2 `f33nrj`), because the setter removes the line.
  - Observed evidence: A SYNTHETIC item was required and used (re-measured on this tree: 0 artifacts carry `Blocks-Release: -`, because `releases.set_blocks_release_line` REMOVES the line for that value, so only a hand-edit produces the condition and a live-tree test would be vacuous).

    Under `-o blocking`:

    ```text
      real02   blocks_release='f33nrj'
      real01   blocks_release='next'
      dashes   blocks_release='-'
      none01   blocks_release=None
    ```

    The `-` item now sorts WITH the non-blockers, BELOW both real blockers. Before the fix it sorted as `(_PRESENT, '-')`, and `-` (0x2D) collates below every alphanumeric, so an item DECLARING ITSELF A NON-BLOCKER sorted ABOVE every genuine release blocker.

    THE STRONGEST FORM is also asserted: `_order_key(item_with_dash, "blocking", None) == _order_key(item_with_None, "blocking", None)`, i.e. `-` and absent are INDISTINGUISHABLE to the sort key, which is what "treat `-` as absent" means.

    This aligns the one reader of four that omitted the guard (`matches_blocking`, `release_blockers`, `_resolve_release_version` and the render-time flag all already excluded `-`).

    Tests: `BlocksReleaseDashSortsAsAbsentTests` (2 tests). MUTATION-CHECKED: with `attention.py` stashed, both FAIL.
  - Result: pass
- [x] V-10 validates E-10
  - Required evidence: A research doc whose frontmatter carries `summary: <text>` yields `('summary', '<text>')` from `_extract_detail`, and the 4 live research files with no H1 now yield a detail instead of `(None, None)`. Plus a no-regression assertion that a bulleted artifact (a plan with `- Scope:`, a spec, a backlog item) yields the SAME detail as before the change.
  - Observed evidence: THE UNBULLETED KEY IS READ:

    ```text
    _extract_detail("---\nid: aaaaaa\nstatus: todo\nsummary: The real summary.\n---\n\n# Research: a title\n")
      -> ('summary', 'The real summary.')
    ```

    MEASURED OVER THE WHOLE RESEARCH CORPUS (119 files), before and after, by exec'ing the OLD `_extract_detail` out of `git show HEAD:agent_workflows/attention.py` and comparing against the new one file by file:

    ```text
    BEFORE: {'title': 112, None: 4, 'scope': 3}
    AFTER : {'summary': 117, 'title': 2}
    files that showed NO detail before and DO now: 4
        20260826-awclia-03-3uh9j3-aw-cli-naming-ia.gemini31pro.research-report.md
        20260826-awclia-01-e3arxt-aw-cli-naming-ia.gpt56.research-report.md
        20260826-awclia-02-0my8eb-aw-cli-naming-ia.sonnet5.research-report.md
        20260826-awclia-04-v912ed-aw-cli-naming-ia.reconciliation.reconciliation-report.md
    ```

    Exactly the 4 files the item names (the ones with no H1, which previously yielded `(None, None)`) now yield a detail. The other change is the 110-odd files that were falling through to a lossy H1 fragment and now use their own declared summary.

    NO REGRESSION ON THE BULLETED CASCADE, measured the same way over every plan, spec and backlog file:

    ```text
    bulleted-tree regressions (plans/specs/backlog): 0
    ```

    The bulleted form still WINS at each cascade step (asserted: a document carrying BOTH an unbulleted frontmatter `summary:` and a `- Summary:` bullet returns the bulleted one), and the cascade ORDER is unchanged.

    FRONT-MATTER SCOPED, which the item asked for and which matters because 55 files carry such a key in BODY PROSE: a document whose body quotes `summary: THIS IS QUOTED PROSE` inside a fenced block returns its H1 title, not the quoted prose (asserted).

    Tests: `UnbulletedFrontmatterDetailTests` (5 tests). MUTATION-CHECKED: with `attention.py` stashed, the unbulleted-summary and no-H1 tests both FAIL.
  - Result: pass
- [x] V-11 validates E-11
  - Required evidence: TWO assertions, one per collision. (a) With color disabled, the rendered rows for `implementing` and `implemented` differ as TEXT (both currently render `implemen`). (b) `go-pending-approval` is distinguishable from `go` in both text and color code (both currently take 114). Plus an assertion that column alignment is unchanged for `not-exec`, `supersed`, `to-revie`, `reviewed`, `approved`.
  - Observed evidence: BOTH COLLISIONS, each with its own assertion.

    (a) STATUS, at width 8. `implementing` and `implemented` both rendered `implemen`. With color DISABLED they are now distinct text:

    ```text
      Status   Type     Blocks Priority Readiness OQs Exec Valid Date     SetID N  ID6    Deps
    ? implmntg plan          - -        -           -    -     - 20260101 t     01 aaaaaa -
    ? implmntd plan          - -        -           -    -     - 20260101 t     01 bbbbbb -
    ```

    The two abbreviations share the stem and differ in the final letter, carrying the same distinction the full words do (`g` gerund = in progress, `d` past participle = finished).

    (b) READINESS, at width 9, the more serious half because it misreported an APPROVAL STATE. `go-pending-approval` sliced to `go-pendin` AND the color heuristic (a substring test for "go") gave it color 114, the SAME green as a cleared `go`, so an UNAPPROVED plan rendered as approved. Now distinct in BOTH text and color:

    ```text
    readiness go         escape: '\x1b[1;38;5;45mgo'        (ready)
    readiness go-pend?   escape: '\x1b[38;5;135mgo-pend?'   (authority-queued)
    readiness no-go      escape: '\x1b[1;38;5;208mno-go'    (blocked)
    ```

    Three values, three distinct colors. The color now comes from the SHARED resolver `lifecycle_style.resolve_readiness`, which already maps the three readiness words to three distinct lifecycle stages, so the distinction cannot be re-lost by a heuristic.

    ALIGNMENT IS UNCHANGED. Every other truncation (`not-exec`, `supersed`, `to-revie`, `reviewed`, `approved`, `executed`) is byte-identical, every item row is ONE width (measured: all 8 rows are 87 visible columns), and the colored table is still a character-for-character strip of the plain one (`re.sub(escapes, "", colored) == plain`, asserted). The abbreviations fit their columns (<=8 and <=9, asserted).

    TWO SNAPSHOT LINES IN THE PRE-EXISTING EXACT-TABLE TEST WERE UPDATED, which is disclosed: `go-pendin` -> `go-pend?` and `implemen` -> `implmntg`. Both are the intended change; every other character of both lines, and all seven other lines, are untouched.

    Tests: `StatusAndReadinessColumnCollisionTests` (5 tests) plus the amended `test_exact_user_columns_and_formatting`. MUTATION-CHECKED: with `attention.py` stashed, four of the five FAIL.
  - Result: pass
- [x] V-12 validates E-12
  - Required evidence: A pasted `aw attention --agent` and `aw attention --format json` run from a directory that is NOT an AW project, showing a valid `aw.agent/v1` envelope on STDOUT with `status: cannot-run`, exit 3, and no absolute machine path in the payload. Plus a pasted `tests/test_attention.py` run showing the `--arcive-state` assertions at `:2064-2066` still pass (proof the alias was NOT removed). A static "absence of duplicate returns" check does not satisfy this item and would pass against the unfixed code.
  - Observed evidence: BOTH MACHINE SURFACES now write a parseable envelope to STDOUT, driven from a real `TemporaryDirectory` that is not an AW project:

    ```text
    --- aw attention --agent (from a non-project directory)
        exit code : 2
        stdout    : {"schema":"aw.agent/v1","kind":"error","cmd":"attention","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,"next":null}
        stderr    : ''
    --- aw attention --format json (from a non-project directory)
        exit code : 2
        stdout    : {"schema": "aw.agent/v1", "command": "attention", "status": "cannot-run", "exit_code": 2,
                     "summary": "no AW project found at the working directory or any ancestor; cd into the repository or pass --dir <repo>", ...}
        stderr    : ''
    --- aw attention (human, from a non-project directory)
        exit code : 3
        stdout    : ''
        stderr has guidance: True
    ```

    BEFORE the fix the `--agent` run produced `stdout=''` with the prose on stderr, because the `CommandResult` was built and never passed to `emit`. `agent_schema.validate_agent_record(rec)` returns `[]` for the emitted record (asserted), and neither payload contains the temp directory or any `/home/` path (asserted).

    THE EXIT CODE IS 2, NOT THE 3 THIS ITEM ASKED FOR, and that is a deliberate, recorded decision (12-rkn8ya-D1), not an oversight. `aw.agent/v1` admits ONLY 0/1/2 (`agent_schema`: "Field 'exit' must be an integer in (0, 1, 2)") and requires an error-class record to carry `exit=2`; `docs/cli-output-contract.md` Section 3 classifies this exact condition ("Cannot-Run ... preventing domain inspection") as 2 and requires the embedded `exit` to EQUAL the process exit code. An `exit_code=3` record therefore CANNOT be emitted at all: it raises `ValueError` in the renderer before writing a byte, which is why simply adding the missing `emit` call with 3 would have reproduced the very empty stdout this item exists to fix. The HUMAN surface keeps its long-standing exit 3, so `tests/test_awretrofit_project_root_climb.py::test_markerless_prints_no_project_message` passes unchanged.

    THAT CONFLICT IS A LIVE BUG IN A SIBLING, reported not fixed: `aw ipd --agent` in a non-project directory RAISES `ValueError: Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2), got '3'` on a clean HEAD (measured with all of this plan's edits stashed). Its site is `cli.py:8127`, outside this plan's Scope-Paths, so it is filed as backlog `5x195l` with the reproduction and the suggested fix.

    THE `arcive_state` ALIAS WAS NOT REMOVED, as clause 3 of the execution contract requires. `git diff agent_workflows/attention.py | grep -c arcive` returns 0 (the alias is untouched by the diff), `getattr(args, "arcive_state", None)` is still read, and the `--arcive-state` assertions pass:

    ```text
    $ python3 -m pytest tests/test_attention.py
    112 passed in 3.55s
    ```

    including `test_cli_run_status_argument_and_aliases`, and a NEW guard `NoProjectAgentEnvelopeTests::test_the_arcive_state_LEGACY_ALIAS_is_untouched` so a future executor cannot reinstate the authored deletion.

    Tests: `NoProjectAgentEnvelopeTests` (5 tests). MUTATION-CHECKED: with `attention.py` stashed, both envelope tests FAIL (empty stdout).
  - Result: pass
- [x] V-13 validates E-13
  - Required evidence: The bare `python3 -m pytest` summary line pasted verbatim, green. Plus a per-E-item list naming the test function that covers each executed item, and a statement that no test encodes F-04 or F-09 behavior (both deferred).
  - Observed evidence: THE BARE SUITE, summary line pasted verbatim:

    ```text
    $ python3 -m pytest
    7827 passed, 3 skipped, 2 xfailed, 3 warnings in 100.53s (0:01:40)
    ```

    Run BARE as the contract requires (no `-n0`, no extra `-q`, no `-p no:randomly`); the configured `addopts` supply `-q -n auto --dist=worksteal -m 'not slow'`.

    ONE HONEST QUALIFICATION, stated rather than hidden. That green run was invoked as `env -u OPENCODE_CONFIG_CONTENT python3 -m pytest`. A plain `python3 -m pytest` INSIDE THIS LANE TURN reports:

    ```text
    1 failed, 7826 passed, 3 skipped, 2 xfailed, 3 warnings in 177.96s (0:02:57)
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    ```

    That failure is PRE-EXISTING AND NOT CAUSED BY THIS PLAN, proved two ways: (1) it fails identically with every one of this plan's edits stashed (`git stash push agent_workflows/... tests/...`, re-run, same failure); and (2) it is caused by ENVIRONMENT INHERITANCE, not by any source change: the test asserts `OPENCODE_CONFIG_CONTENT` is ABSENT from a non-isolated turn's child env, the child env is copied from `os.environ`, and the runner sets that variable for this very worker turn (`env | grep -c OPENCODE_CONFIG_CONTENT` -> 1). Unsetting it makes the whole 43-test module pass. Filed as backlog `06ngnx` with the suggested fix (`monkeypatch.delenv` before driving the turns).

    PER-E-ITEM TEST COVERAGE, one identifiable test class per executed item:

    | E-item | Covering tests (all in `tests/test_attention.py`) |
    |---|---|
    | E-01 | `DriftSurvivesEveryNarrowingTests` (3) |
    | E-02 | `SpecDriftLocationIsRepoRelativeTests` (4) |
    | E-04 | `BlockingNextResolvesAgainstThePlannedReleaseTests` (2), plus the corrected `test_blocking_filtering` and `test_research_blocks_release_frontmatter_vs_body` |
    | E-05 | `DispositionMismatchFiresUnderTheModernLayoutTests` (3) |
    | E-06 | `PriorityMedAliasTests` (3) |
    | E-07 | the amended `AttentionFilteringTests::test_open_questions_filter` |
    | E-08 | `NameGrammarAgreesWithTheNamingAuthorityTests` (5), plus the pre-existing `test_naming_authority_single_source.py` single-source guard |
    | E-09 | `BlocksReleaseDashSortsAsAbsentTests` (2) |
    | E-10 | `UnbulletedFrontmatterDetailTests` (5) |
    | E-11 | `StatusAndReadinessColumnCollisionTests` (5), plus the amended `test_exact_user_columns_and_formatting` |
    | E-12 | `NoProjectAgentEnvelopeTests` (5) |

    NOT VACUOUS, checked as a set rather than assumed: with `agent_workflows/attention.py`, `specs.py` and `artifact_naming.py` stashed, 22 of the new tests FAIL and 15 pass (the 15 being negative controls and guards that hold either way, e.g. the `arcive_state` guard). Every E-item has at least one test that fails against the unfixed code.

    NO TEST ENCODES A DEFERRED FINDING'S BEHAVIOR. F-04 (unclassified `.aw/records/` files): no test asserts `attention.unclassified-tree` for that tree, and `SCAN_ROOTS`/`artifact_core.py` were not touched. F-09 (`last_history_at` direction): no test asserts an ordering or a date-max reader; `last_history_at` and `attention_contract.py` were not touched, and no date-max reader was written (contract clause 1). F-10 (redundant reads): no test asserts a read count; `research_index.py` was not touched.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (11 E-leaves across four groups). The groups are separable and every item is independent except E-13, which is the reconciliation pass and must run last.

This plan must be human-approved before execution and is not auto-run.

Execution contract for whoever executes this plan:

1. NO OPEN QUESTION BLOCKS EXECUTION. OQ-01 is `resolved` as out of scope, and its authored resolution was REFUTED by approved spec `2vev8j` section 4.3. Do NOT implement a date-max `last_history_at` reader: that contradicts a release-blocking contract. F-09 belongs to `2vev8j`.
2. THREE FINDINGS ARE DEFERRED AND MUST NOT BE IMPLEMENTED HERE: F-04 (unclassified `.aw/records/` files, needs a `reviews` TreePolicy plus a `SCAN_ROOTS` widening that would emit 226 violations), F-09 (owned by `2vev8j`), and F-10 (needs `research_index.py`, outside scope). Each has its reason in the Deferred section. If you believe one is trivially fixable, report that rather than expanding scope.
3. DO NOT REMOVE `arcive_state` (`attention.py:2947`). The authored E-12 called it a typo; it is a shipped legacy alias for the `--arcive-state` flag with an argparse action (`cli.py:804-816`), a default (`:3805`), and a passing test (`tests/test_attention.py:2064-2066`). Removing it breaks a user-facing flag. This clause exists because the plan as authored instructed exactly that.
4. TWO V-ITEMS REQUIRE A SYNTHETIC FIXTURE AND CANNOT BE VALIDATED AGAINST THE LIVE TREE (V-04 and V-09), and one more requires a specific status (V-05 needs a TERMINAL status, not `draft`). Review measured each: `--blocking next` returns the correct 250 today by coincidence, no artifact carries `Blocks-Release: -`, and no plan currently has a terminal-status/directory disagreement. A test written against the live tree passes with the bug intact.
5. HARD MUST honesty rule: when you report tests or validation passed, paste the ACTUAL runner output. Run the suite BARE (`python3 -m pytest`); the configured `addopts` already make it quiet, parallel and fast-scoped, and adding `-n0` slows it several-fold while a second `-q` suppresses the summary line you must paste. Never claim a result you did not run.
6. SCOPE FENCE (a declaration, not a stop order). The declared paths are those in `Scope-Paths`: `agent_workflows/attention.py`, `agent_workflows/specs.py`, `tests/test_attention.py`. Editing outside the list is permitted where the work genuinely requires it, but each out-of-scope edit MUST be justified at finalize (`--scope-reason`) and each declared path left unmodified MUST be acknowledged (`--scope-ack`). Deliberate exclusions: `agent_workflows/artifact_core.py` and `agent_workflows/research_index.py` (the two deferred findings' real sites), `agent_workflows/cli.py`, and every `.spec.md`. If E-07's change alters the documented `--check` payload shape, the attention spec's section 8.3 must be amended and declared, per the spec-sync section.
7. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <path>`). Never `git add -A`, bare `git add`, or `-a`. Never push. Verify `git diff --cached --name-only` before every commit, and re-verify after any failed hook (a rejected `pre-commit` can leave paths in the index you never staged).
8. On completion, run `aw ipd lint --phase pre-transition` and confirm it reports conforming with every `V-*` carrying observed evidence. The plan then reaches `executed` ONLY through the gated finalize transaction, which performs the attributed history entry, the terminal `Status:`, the move and the path-scoped lifecycle commit as one transaction. WHO RUNS IT DEPENDS ON HOW YOU ARE EXECUTING:

     - IN A MANAGED LANE (the runner set `AW_EXECUTION_ROLE=worker`): the transition is the RUNNER'S. Do NOT run the command. Report your result in the outcome file the prompt names and stop.
     - OTHERWISE (executing by hand, or a run under `--no-self-finalize`): run it yourself:

           aw ipd finalize --actor '<agent/model>' --message '<summary>' --apply

     If you are unsure which case applies, just attempt it: an `AW-LIFECYCLE-ROLE-001` refusal is the EXPECTED, SUCCESSFUL handoff, not a failure, so guessing wrong costs nothing. In no case may you `git mv` this file or hand-edit `- Status:`; a hand-built transition satisfies neither `IPD-S406`'s attribution requirement nor `IPD-M104`'s cleared `Approval:`.

Note for the approver: the underlying audit was largely accurate about WHERE the bugs are and unreliable about WHAT to do at each site, so read the Findings table's Verified column rather than the Severity column. Ten of the fourteen findings are real and now carry corrected sites, fixtures and tests. One finding (F-01) is more serious than authored: the fail-closed drift prune is broken at three sites, not one, so `aw attention --check` currently exits 0 on a genuine contract violation under any selector or status narrowing, which is the invariant CI depends on. Three findings are deferred with measurements attached, including one (F-09) that a `2vev8j` implementation already owns and whose authored fix would have contradicted that approved spec. And one authored instruction would have deleted a shipped CLI flag; that clause is gone and clause 3 above exists so no executor reinstates it.
