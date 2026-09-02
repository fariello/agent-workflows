# IPD: Rename attention to aw next and add an explicit --order-by including dependency depth so it can answer what to work on in what order

- Date: 2026-08-31
- Kind: child
- Concern: Nothing in the repo answers "do these things, in this order". `aw attention` is an unordered SET whose sort key is `(class, path, id)` with priority deliberately excluded, roadmaps are explicitly non-commitments, and `Item-Dependencies` can only be DECLARED BY a plan. Ordered work therefore lives in agent chat or a gitignored scratch file, i.e. nowhere durable.
- Scope: Rename `aw attention` to `aw next` (keeping `attention`, `att` and `todo` as aliases), and add `--order-by/-o` selecting the sort, with the current `(class, path, id)` as the unchanged DEFAULT and every other order an explicit opt-in. Includes `depth`, computed from the existing type-agnostic dependency index, so the command can sequence dependent work. Does NOT change any artifact format, does NOT add a committed ordering field or artifact, and does NOT alter what the view SELECTS (only how it is ordered and named).
- Scope-Paths: agent_workflows/attention.py, agent_workflows/attention_contract.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/completion.py, docs/, README.md, tests/test_attention.py, tests/test_next_ordering.py
- Item-Dependencies: none
- Status: reviewed
- Set: worksequence
- Order: 1
- Highest E allocated: 10
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: i6015i
- From-Backlog: 2k42zu

## Workflow history
- 2026-09-02 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001 BLOCKER (-o depth uncomputable / second-scan violation) through PR-007 all fixed

- 2026-09-01 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1 at HEAD `8108fb87`: APPROVE WITH REVISIONS APPLIED, PR-001..PR-007, all FIXED. PR-001 BLOCKER: `-o depth` was UNCOMPUTABLE as drafted and its obvious workaround violated the plan's own single-scan rule. `attention.Item` carries no dependency field and `attention.py` has zero `Item-Dependencies` references, so `sort_items(items, order_by)` cannot compute depth; reaching for `build_dependency_index` re-reads every artifact (measured 0.19s/782 records + 0.22s), the second scan `releases.py:328-333` and E-09 forbid. Resolved by extracting edges in `scan()` (which already holds the text at `attention.py:171`) onto a trailing optional `Item` field, plus a new one-scan call-count guard (E-10 case (i)) because a second scan is invisible in output. PR-002 HIGH: `todo` is NOT an argparse alias but a separate parser accepting only `--all` plus a dispatch special-case (`cli.py:2478-2481,9086-9089`); measured, `aw todo --format json` FAILS and its `--help` still advertises the deleted action ledger, so E-01's byte-identical claim was false. E-01 now converts it and deletes the special-case. PR-003 HIGH: the fail-closed evidence E-09/V-09 planned to use is GONE (the `ntf6sx` duplicate id no longer exists; `aw attention --check` exits 0 with zero drift), replaced by a constructed fixture. PR-004 MEDIUM: coverage figures stale and one materially wrong (filename grammar is 78%, not 96%; 708 items, not 675). PR-005 MEDIUM: `docs/` and `README.md` added to Scope-Paths (D-3) since E-02 requires a docs edit. PR-006 MEDIUM: `Item` shape change affects out-of-module consumers; grep + suite added. PR-007 LOW: four stale citations, two landing in unrelated code, and no spec filename contains `25kzda`. Both OQs resolved from verified evidence. Review record: `.aw/records/reviews/20260901-worksequence-01-i6015i-rename-attention-to-aw-next-and-add-an-explicit-order-by.review.md`.
- 2026-08-31 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): graduated from backlog `2k42zu`. One of the item's OWN PREMISES is falsified and the design changes accordingly (F-1): `Item-Dependencies` is NOT plan-only, it already accepts `backlog` and `spec` TARGETS; only the SOURCE side is plan-restricted. Its Q1 (new artifact vs backlog field) is answered DERIVED, its Q3 (can it be derived) YES, its Q4 (must not contradict the attention view) satisfied BY CONSTRUCTION since the order consumes the same single scan. Q2 (durable vs ephemeral) answered ephemeral-and-computed, which is also what the item's own INTERIM PRACTICE recommends. Two maintainer rulings recorded: `--order-by/-o` with the current sort as default (F-4, which is what preserves the `xprio` contract by construction), and absent sort values sort LAST rather than being hidden or defaulted (F-5). Dependency `depth` is IN this plan by maintainer ruling, because it is the only key that actually answers the item's ask.
- 2026-08-31 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give the repo one honest answer to "what do I work on next, and in what order", computed on demand from data that already exists rather than hand-maintained in a file that rots. The name `aw next` becomes true rather than aspirational: today a rename alone would label a path-sorted set as an ordering.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the rename, without breaking anything

- [ ] E-01 Make `next` the canonical command and `attention`, `att` and `todo` its aliases, inverting today's arrangement where `attention` is canonical (`command_surface.py:194-203`) and `att`/`todo` are declared aliases (`:96-114`). Add a `CommandDeclaration` for EVERY leaf including each alias, because `discover_parser_leaves` treats an alias as its own leaf and `find_undeclared_leaves` (`command_surface.py:1283`) fails CI on any leaf lacking a declaration. Mirror `attention`'s existing declaration exactly: `command_class="read"`, `human_recipe="board"`, `agent_record_kind="result"`, `mutation_gate="none"`, `empty_error_renderer="shared_empty_result"`.

  `todo` IS NOT AN ARGPARSE ALIAS TODAY AND MUST BE CONVERTED, which is more work than "declare it" (F-10, MEASURED). `att` is a true argparse alias (`cli.py:2847` `aliases=["att"]`), but `todo` is a SEPARATE parser (`cli.py:2478-2481`) that accepts only `--all` and is routed to `attention.run` by a dispatch special-case (`cli.py:9086-9089`). Consequences an executor must handle: `aw todo --format json` FAILS with `unrecognized arguments: --format json`, its `--help` still advertises the DELETED action ledger ("List the open operational AW actions"), and it works at all only because `attention.run` reads every option through `getattr(args, ..., default)` (`attention.py:976-979`). So the "byte-identical for the same arguments" outcome is FALSE for `todo` until it is converted. Fold `todo` into the canonical parser's `aliases=[...]` list and DELETE both the standalone `p_todo` parser and the `cli.py:9086` dispatch special-case, so all four names share one parser and one option set. Verify no other dispatch site keys on `args.command == "todo"`.
  - Depends on: none
  - Expected outcome: `aw next`, `aw attention`, `aw att` and `aw todo` all work and produce byte-identical output for the same arguments INCLUDING `--format json`, `--check`, `--long` and `--details`; `aw todo --help` no longer mentions an action ledger; the standalone `p_todo` parser and its dispatch special-case are gone; `find_undeclared_leaves(_build_parser())` returns an empty set.
  - Execution state: pending

- [ ] E-02 Update the shell completion registration (`completion.py`) and the docs surface so the new name is discoverable and no documentation references an undeclared subcommand. `docs_check.check_aw_commands` (`docs_check.py:120-140`) validates `aw <sub>` mentions against `known_subcommands()`, so a doc naming `aw next` before it is declared is a finding, and a doc still naming only `aw attention` is not wrong but is now stale.
  - Depends on: E-01
  - Expected outcome: completion offers `next`; `aw check` reports no docs finding; the README/docs name `aw next` as canonical with the aliases noted.
  - Execution state: pending

### Task group 2: --order-by, with the current order as the default

- [ ] E-03 Add `ORDER_KEYS`, a closed vocabulary, to `attention_contract.py` beside the existing `ATTENTION_CLASS_ORDER`: `class` (the default), `priority`, `date`, `set`, `order`, `blocking`, `depth`, `id6`, `path`, `status`, `tree`. Declare it as data, not as a chain of conditionals, so the CLI choices, the completion list and the tests all read ONE definition and cannot drift. Note that `attention_contract` today has NO notion of priority or order beyond the class display order, and its stated purity clause (`:29-31`) forbids inferring anything from prose, dates, mtime or agent context; a NAMED sort key selected by the caller does not violate that, but a heuristic blend of keys would, so do not add one.
  - Depends on: none
  - Expected outcome: `ORDER_KEYS` exists as a module-level tuple; `aw next --order-by bogus` is refused by argparse with the valid list shown; the CLI choices are generated FROM the tuple rather than re-typed.
  - Execution state: pending

- [ ] E-04 Add `--order-by/-o` to the parser (beside `--format`, `--check`, `--all`, `--long`, `--details`, `--type` at `cli.py:2839-2875`) defaulting to `class`, and implement `sort_items(items, order_by)` in `attention.py` replacing the inline `items.sort(...)` at `attention.py:218-224`. THE DEFAULT PATH MUST PRODUCE BYTE-IDENTICAL OUTPUT to today: the `xprio` Set pinned "the shared attention sort key is UNCHANGED" as required evidence in all four of its plans, so `class` is not merely the default but the preserved contract. Every non-default key must FALL THROUGH to the existing `(class, path, id)` tail so every order is TOTAL and deterministic, honoring the module's stated determinism contract (`attention.py:11-13`: no timestamps, no mtime, no locale).
  - Depends on: E-03
  - Expected outcome: `aw next` and `aw attention` with no `-o` produce output byte-identical to today's `aw attention`; every `-o` value produces a stable total order that is unchanged across repeated runs.
  - Execution state: pending

- [ ] E-05 Place items MISSING the selected key LAST, then fall through to the default tail (maintainer ruling). RE-MEASURED AT REVIEW on the live tree (the plan's figures were stale; see F-5): 708 items, `priority` present on 118 (17%), `blocks_release` on 96 (14%), so `-o priority` must place 590 unprioritized items somewhere. Do NOT fabricate a value: `xprio`'s OQ-01 already ruled that an absent Priority renders as UNPRIORITIZED and must not be defaulted to `medium`, and the sort must match that ruling rather than contradict it. Do NOT hide them either; filtering stays the job of `--all` and the existing selector filter. Re-measure again at execution time and cite the numbers you observe rather than these, since the tree moves daily.
  - Depends on: E-04
  - Expected outcome: `-o priority` lists high, then medium, then low, then every item with no Priority in default order; the item count is IDENTICAL to `aw next` with no `-o`, proving ordering never filters.
  - Execution state: pending

- [ ] E-06 Implement the metadata-only keys as pure reads off the existing scan, adding no new file reads: `priority` (rank high>medium>low, reusing `check_engine._PRIORITY_RANK` at `:1489` rather than a second rank table), `date` (`last_history_at`, newest first, re-measured 582/708 = 82% coverage), `blocking` (`blocks_release` present first), `id6`, `path`, `status` (`native_status`), `tree`. Take `set` and `order` from the filename grammar `YYYYMMDD-<setid>-NN-<id6>-<slug>`; RE-MEASURED AT REVIEW only 554 of 708 items (78%) satisfy it, NOT the 96% the plan claimed, so 154 items sort as absent per E-05 rather than raising. That absent set is not a rounding error and is concentrated in `plans` (97), `research` (23), `specs` (19) and `backlog` (15), largely grandfathered pre-cutover names, so `-o set` and `-o order` are legitimately partial keys and must be described that way rather than as complete orderings. Note `set` is ALSO available structurally as `status_set.ArtifactRecord.set_id`; prefer a structural read over filename parsing if one is reachable without a second scan.
  - Depends on: E-05
  - Expected outcome: each key produces its stated order, verified against hand-checked expectations; the scan performs no additional file opens versus today (the `Item` NamedTuple already carries `priority`, `blocks_release`, `last_history_at`, `native_status` and `tree`); a filename outside the grammar sorts as absent without raising.
  - Execution state: pending

### Task group 3: dependency depth, the key that actually sequences

- [ ] E-07 Implement `-o depth` by REUSING the shipped type-agnostic substrate rather than building a second graph: `check_engine.build_dependency_index` (`:1981`, not `:1978`) maps id6 to `(record_type, status, path)` over `status_set.inventory_all_artifacts`, and `check_engine._resolve_edge` (`:1999`) resolves `ipd`, `spec` AND `backlog` targets (`ipd_schema.ITEM_DEP_TYPES` at `:533`). Compute the longest declared prerequisite chain, following the semantics of the runner's `oc_runipd.dependency_depth` (`:3547`, not `:3340`) but WITHOUT its queue-membership restriction (its `edge.id6 not in by_id` filter at `:3564`), since here every tracked artifact is in scope. Prerequisites sort BEFORE their dependents, which is the whole point.

  FIRST RESOLVE THE DATA GAP, because the plan as drafted could not compute this key at all (F-11, MEASURED). `attention.Item` carries no dependency edges (its fields are exactly `id, path, tree, native_status, attention_class, gate, last_history_at, priority, blocks_release, detail_kind, detail_text`), and `attention.py` contains ZERO references to `Item-Dependencies`. So `sort_items(items, order_by)` receiving only `Item`s CANNOT compute depth, and reaching for `build_dependency_index` inside the sort would perform a SECOND full-tree scan (`inventory_all_artifacts` re-reads every artifact; measured 0.19s for 782 records, plus 0.22s for the index), which is exactly what E-09 and `releases.py:328-333` forbid.

  Take the ONE-SCAN option and state it as the design: `scan()` already reads each artifact's full text at `attention.py:171` and then DISCARDS it, so parse the edges there and carry them on `Item` as a new trailing optional field (for example `item_dependencies: Optional[Tuple[str, ...]] = None`), appended LAST so every existing positional `Item(...)` construction keeps working, which is the same additive pattern `priority`/`blocks_release` used (`attention.py:44-48`). Parse with the shipped `ipd_schema.parse_item_dependencies` rather than a new regex. Then `-o depth` is a pure function of the scan result and no second scan occurs. If the executor instead finds a way to reuse `build_dependency_index` without a second artifact read, that is acceptable ONLY if V-09's one-scan evidence still holds; the field-on-`Item` route is the recommended one.
  - Depends on: E-06
  - Expected outcome: for a chain A <- B <- C, `-o depth` lists A before B before C regardless of their paths or ids; an artifact with no declared edges has depth 0 and sorts among the roots; `Item` carries the edges and only ONE artifact-reading pass occurs per invocation.
  - Execution state: pending

- [ ] E-08 Make `-o depth` cycle-safe and never-hanging. Reuse the pure `ipd_schema.item_dependency_cycles` (`:756`) to detect a cycle rather than re-implementing detection, and mirror the runner's defensive stance (`oc_runipd.py:3344-3346` notes that although preflight refuses a cycle, "a hand-edited state.json must not hang the scheduler here"). A cycle must degrade to the default order for the affected nodes and be REPORTED, not silently absorbed: a view that quietly reorders around a cycle hides a real defect that `aw check` already has a rule for.
  - Depends on: E-07
  - Expected outcome: a deliberately constructed cyclic edge set produces terminating output plus a visible notice naming the cycle; the command does not hang and does not raise.
  - Execution state: pending

- [ ] E-09 Preserve the fail-closed `--check` behavior and the single-authority rule for every order. `--check` must still exit nonzero on contract violations regardless of `-o`, per `attention.py:1247-1248` ("a plain view still fails closed if invalid, so consumers cannot treat an invalid view as authoritative"). The order MUST be computed from the SAME `scan()` result the view already produces, never from a second scan: `releases.py:328-333` records why ("a second scan could drift from the answer `aw attention` and `aw doctor` give"), and the backlog item's own Q4 demands the ordering cannot contradict the attention view. `attention.run` calls `scan()` exactly once (`:1016`); keep it that way, which is also what forces E-07's data-gap resolution.

  THE PLANNED FAIL-CLOSED EVIDENCE NO LONGER EXISTS (F-9, re-measured): the `ntf6sx` duplicate id is GONE (the plan is now only in `executed/`) and `aw attention --check` exits 0 with ZERO drift on the current tree. So do NOT rely on a live pre-existing violation. Prove fail-closed on a CONSTRUCTED fixture instead (for example a temp repo with the same artifact id6 in two trees, which is what `attention.duplicate-id` detects at `attention.py:186-193`), asserting nonzero exit under every `-o` value. A constructed fixture is strictly better evidence anyway: it does not silently pass the day someone repairs the tree.
  - Depends on: E-08
  - Expected outcome: `aw next --check -o <key>` exits nonzero on a CONSTRUCTED invalid fixture for every key, and exits 0 on a valid tree; the set of items is provably identical across all `-o` values, differing only in sequence; exactly one `scan()` call per invocation.
  - Execution state: pending

### Task group 4: falsifiable tests

- [ ] E-10 Add `tests/test_next_ordering.py` and SABOTAGE every assertion before trusting it. Required cases: (a) THE CONTRACT REGRESSION TEST, asserting default output is byte-identical to today's `aw attention` (this is the `xprio` guarantee and the highest-value test here); (b) all four names produce identical output FOR THE SAME FLAGS, and specifically that `aw todo --format json` and `aw todo --check` now work (they do not today, F-10), which is the assertion that proves E-01's parser conversion actually happened; (c) each `-o` key produces its expected order on a fixture with hand-known values; (d) absent values sort LAST and the item COUNT is unchanged, proving ordering never filters; (e) `-o depth` orders a prerequisite before its dependent, including across a plan->backlog edge, which is the cross-type case the item cares about; (f) a cyclic fixture terminates with a notice; (g) `--check` fails closed under every `-o` on a CONSTRUCTED invalid fixture (E-09; the live violation is gone); (h) `find_undeclared_leaves` is empty; (i) ONE-SCAN GUARD: assert `scan()` (or the artifact read) is invoked exactly once per invocation under `-o depth`, by counting calls with a patch or counter, since E-07's whole risk is a silent second scan that no output assertion would reveal. Assert on the ORDERED SEQUENCE of ids, not on substring presence, since a substring assertion would pass against an unsorted list.
  - Depends on: E-09
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_next_ordering.py tests/test_attention.py` passes, and each case was verified to FAIL when its branch is deliberately broken.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `attention.scan` is a pure read that writes NOTHING (`attention.py:5`); an earlier eager `mkdir` on this path was treated as a defect and fixed ("write-on-read", `:201-204`). Keep it pure.
- Determinism is an observable contract (`attention.py:11-13`): sort by class order then normalized path then id, no timestamps, no mtime, no locale, fixed JSON key order.
- Single authority, no second scan (`releases.py:328-333`): a derived view must consume the existing scan so two surfaces cannot disagree. `attention.run` calls `scan()` exactly once, at `:1016`.
- `scan()` reads each artifact's full text (`attention.py:171`) and then discards it; `Item` keeps only extracted fields. Any new per-item datum should be extracted THERE rather than by a second read (this is what E-07 depends on).
- `Item`'s optional fields are appended TRAILING with defaults precisely so existing positional constructions keep working (`attention.py:44-48`, added by `awdoctorfix`). Follow that pattern for any new field.
- `attention.run` reads every option via `getattr(args, name, default)` (`:976-979`), which is why a narrower alias parser silently "works" instead of failing loudly. Do not mistake that tolerance for equivalence.
- Fail closed on an invalid view (`attention.py:1247-1248`), so `--check` cannot be defeated by a display option.
- Every CLI leaf AND every alias needs a `CommandDeclaration`, enforced by three tests (`tests/test_command_surface_declarations.py:45`, `tests/test_cli_conformance_matrix.py:52`, `tests/conformance_matrix.py:341`). The first is marked `slow`, so a bare run will NOT catch it; `make test-all` will.
- One shared vocabulary per concept: `backlog.PRIORITIES` is imported by every type rather than forked, and `_ITEM_DEP_STATE_STATUSES["backlog"]` is DERIVED from `backlog.STATUSES` because a second hardcoded copy previously desynced (`ipd_schema.py:555-559`).

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **The item's premise that `Item-Dependencies` "orders PLANS ONLY" is FALSE, which is why a derived cross-type order is cheap.** `ITEM_DEP_TYPES = ("ipd", "spec", "backlog")` (`ipd_schema.py:533`), and verified live: `state:backlog:open:2k42zu` and `exists:spec:25kzda` both parse; `research` and `release` targets are rejected. Only the SOURCE side is plan-restricted (`status_set.py:1475-1482` refuses a non-plan selector; `check_engine._iter_plan_ipds` globs `*.ipd.md`). | `ipd_schema.py:533`; live `parse_item_dependencies` output for four edge strings. |
| F-2 | **A mixed-type ordering is ALREADY SPECIFIED and its absence is already recorded as a deliberate gap.** Spec `25kzda` 5.4 rule 4 defines the order as dependency depth, then a type rank (`spec`, `backlog`, `ipd`, `prompt`), then Set, Order, id, path. `oc_runipd.queue_sort_key` implements it MINUS the type rank, whose docstring says it is "deliberately NOT implemented: this runner's queue is homogeneous (IPDs only ...) so a rank over types that cannot appear would be untestable dead code. Recorded rather than silently skipped." That is a pre-authored TODO for exactly this surface. VERIFIED at review, with the file located by Id since no filename contains `25kzda`: `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` (`- Id: 25kzda` at `:7`), section 5.4 at `:817`, rule 4 at `:824`. | Spec `:817-825`; `oc_runipd.queue_sort_key` at `:3572` with the type-rank note at `:3581-3584`. |
| F-3 | **Note that the specified order EXCLUDES priority, so this plan's `-o priority` is an addition to it, not an implementation of it.** Spec 5.4 rule 4 ranks by depth and type, never by priority, and rule 5 states declared edges always win with Set/Order only a tiebreaker. Recorded so `-o depth` and `-o priority` are understood as different answers rather than one being a broken version of the other. | Spec 5.4 rules 4-5 read in full. |
| F-4 | **`--order-by` preserves the `xprio` contract BY CONSTRUCTION, which a hardcoded new sort would have broken.** All four `xprio` plans pinned "the shared sort key is UNCHANGED (priority not added to the sort tuple)" as REQUIRED EVIDENCE, and the orchestrator states the Set "adds LABELING only" and "does NOT introduce a priority-based sort key". Making `class` the default and every other order opt-in keeps that literally true. | `xprio-00-u5vyye` Scope and OQ-01; the pasted "sort key is NOT in the diff" evidence in each child. |
| F-5 | **Absent values are the common case, not an edge case, so their placement is a primary design decision.** RE-MEASURED AT REVIEW over 708 items (the plan's 675-item figures were stale, and one was materially wrong): `priority` on 118 (17%), `blocks_release` on 96 (14%), `last_history_at` on 582 (82%), `gate` on 3 (0%), and the filename set/order grammar on only **554 (78%), not the claimed 96%** - 154 items miss it, concentrated in `plans` (97), `research` (23), `specs` (19), `backlog` (15). That makes `-o set`/`-o order` substantially partial keys rather than near-complete ones. Maintainer ruling stands: absent sorts LAST, never hidden and never defaulted, matching `xprio`'s UNPRIORITIZED display ruling. | Live `attention.scan` field-coverage measurement at HEAD `8108fb87`. |
| F-6 | **`/whatnext` already exists but computes NOTHING, so it is not a substitute.** It reads `aw attention --format json` then asks the MODEL to rank: "You decide the order on the merits. There is no fixed priority formula" (`whatnext.md:28`), with a hand-written fallback that is explicitly "a fallback, not a formula" (`:89-92`), and it caps output at 3 items so it cannot answer "these six, in this order". It also still points at `TODO.md` as a source the attention view cannot see. | `.aw/system/workflows/whatnext/whatnext.md:28`, `:50`, `:78-83`, `:89-92`, `:94-112`. |
| F-7 | **`next` is free and the rename is low-risk, but the name is currently a promise the code does not keep.** VERIFIED: `python3 -m agent_workflows next` returns `invalid choice: 'next'` and enumerates the top-level commands, with no `next` among them. `aw run next` exists (`cli.py:1474`, `:1552`) but is scoped to ONE run's step graph. Renaming without ordering would label a `(class, path, id)`-sorted set as an ordering. Note the "alias" half of this claim is only partly true; see F-10. | `python3 -m agent_workflows next` -> invalid choice; `command_surface.py:105-114`; `cli.py:1474`. |
| F-8 | **Derived beats authored here on the item's own reasoning, and the precedent is overwhelming.** Computed-fresh-writes-nothing views already include `aw attention`, `aw doctor` ("Composes existing checks; reimplements none; writes nothing"), `aw status`, `aw releases show` blockers, `aw check`, `aw run next`, `aw ipd board` and `aw find`. The item itself warns a hand-maintained committed sequence "goes stale the moment work lands, and a stale committed sequence is arguably worse than none", and its INTERIM PRACTICE says order belongs in a disposable worklist. | `doctor.py:1-4`; `attention.py:5`; backlog `2k42zu` Q2 and INTERIM PRACTICE. |
| F-9 | **CORRECTED AT REVIEW: the view is now VALID, so the plan's planned fail-closed evidence NO LONGER EXISTS.** The `ntf6sx` duplicate id is gone (the plan is present only in `executed/`), `attention.scan` returns ZERO drift, and `aw attention --check` exits 0. E-09/V-09 therefore cannot gather fail-closed evidence from the live tree and must use a CONSTRUCTED invalid fixture, which is better evidence regardless because it does not evaporate when someone repairs the tree. The instruction not to fix `ntf6sx` is now moot. | `python3 -m agent_workflows attention --check` -> exit 0; `attention.scan` -> 0 drift; only `.aw/records/plans/executed/...ntf6sx...` exists. |
| F-10 | **HIGH REVIEW FINDING: `todo` is NOT an argparse alias, so E-01's "byte-identical for the same arguments" outcome is FALSE as drafted.** `att` is a real alias (`cli.py:2847`), but `todo` is a SEPARATE parser accepting only `--all` (`cli.py:2478-2481`) that reaches `attention.run` through a dispatch special-case (`cli.py:9086-9089`). MEASURED: `aw todo --format json` fails with `unrecognized arguments: --format json`, while `aw att --format json` emits JSON; `aw todo --help` still advertises the DELETED action ledger ("List the open operational AW actions"). Bare output happens to match (all three names hash `3d0e3259...`) only because `attention.run` reads options via `getattr` defaults (`attention.py:976-979`). E-01 now converts `todo` into a true alias and deletes both the standalone parser and the special-case; E-10 (b) asserts `--format json` and `--check` work under `todo`. | The three commands run live; `cli.py:2478-2481,2847,9086-9089`; `attention.py:976-979`. |
| F-11 | **BLOCKER REVIEW FINDING: `-o depth` was uncomputable as drafted, and the obvious workaround violates the plan's own single-scan rule.** `attention.Item` has no dependency field (fields are exactly `id, path, tree, native_status, attention_class, gate, last_history_at, priority, blocks_release, detail_kind, detail_text`) and `attention.py` contains ZERO occurrences of `Item-Dependencies`, so `sort_items(items, order_by)` cannot compute depth from what it is given. Calling `check_engine.build_dependency_index` inside the sort would re-read every artifact via `status_set.inventory_all_artifacts` (measured 0.19s / 782 records, plus 0.22s for the index), i.e. a SECOND scan, which E-09 and `releases.py:328-333` forbid. Resolved by extracting the edges in `scan()`, which already holds the text at `attention.py:171`, and carrying them on a trailing optional `Item` field; E-10 (i) adds a one-scan guard test. | Field list and grep measured live; timing measured live; `attention.py:171`; `releases.py:328-333`. |
| F-12 | **Four line citations were stale; two pointed into unrelated code.** `oc_runipd.py:3340` lands in `SUITE_CHECK_TIMEOUT_SECONDS` prose (`dependency_depth` is at `:3547`, `queue_sort_key` at `:3572`); `check_engine.build_dependency_index` is at `:1981` not `:1978`; `releases.py:331-333` is off by a few lines (`:328-333`); and no spec filename contains `25kzda` (locate it by `- Id:`). Corrected throughout and re-anchored on symbol names. | `sed -n` / `grep -n` at each site, HEAD `8108fb87`. |

## Proposed changes (ordered, validatable)

1. Invert the canonical/alias relationship so `next` is canonical and `attention`/`att`/`todo` are aliases, CONVERTING `todo` from its own divergent parser into a real alias and deleting its dispatch special-case, with a declaration per leaf (E-01) and completion plus docs updated (E-02).
2. A closed `ORDER_KEYS` vocabulary in the contract module (E-03), a `--order-by/-o` flag defaulting to today's order (E-04), absent-sorts-last (E-05), and the metadata-only keys as pure reads (E-06).
3. `-o depth` computed from edges extracted during the EXISTING single scan and carried on `Item` (E-07), cycle-safe and reporting rather than absorbing (E-08), with fail-closed `--check` proven on a constructed fixture and single-scan authority proven by call count (E-09).
4. Sabotage-verified tests led by a byte-identical-default contract regression test (E-10).

## Deferred / out of scope (with reason)

- **Letting a BACKLOG item declare its own `Item-Dependencies` edge (unblocking the source side).** This is the real remaining gap after F-1: an IPD can point at a backlog item, but a backlog item cannot declare an edge, so non-plan work like "merge this lane" still cannot be sequenced by hand. Deliberately deferred because it changes a schema, a setter and an evaluator's file glob, and because `-o depth` delivers value over EXISTING edges first. Worth its own plan; note the substrate already resolves backlog targets, so it is smaller than it looks.
- **A committed ordering field or a new worklist artifact type.** Rejected on the item's own reasoning (F-8) and by the roadmap precedent (excluded from attention as "intent, not commitment"). If a durable sequence is ever wanted, it should be argued separately against the staleness objection.
- **The `prompt` type rank from spec 5.4 rule 4.** The spec's rank names four types; `prompts` is a tracked tree but is not in `ITEM_DEP_TYPES`, so a prompt cannot carry or be a dependency edge today. Implementing a rank over a type that cannot participate would repeat exactly the untestable-dead-code mistake `queue_sort_key` avoided.
- **Rewiring `/whatnext` to consume `-o`.** The workflow would benefit (F-6), but it is a prose workflow with its own review path, and changing an agent-facing workflow is a separate concern from adding the capability it would consume.
- **Fixing the `ntf6sx` duplicate id (F-9).** MOOT as of review: it is already gone and the view is valid, so there is nothing to defer. E-09 now uses a constructed fixture instead.
- **Sorting by a BLEND of keys (e.g. a weighted score).** Explicitly out: `attention_contract`'s purity clause forbids inferring importance from prose or context, and a blended score is unexplainable to the user. Each `-o` value names exactly one key with a deterministic tail.

## Scope check

- Over-scope: none. Every Scope-Paths entry is touched by a named E-item. `check_engine.py` and `ipd_schema.py` are CONSUMED by E-07/E-08 but not modified, so they are deliberately absent.
- Under-scope, RESOLVED AT REVIEW (D-3): `docs/` and `README.md` are now DECLARED, because E-02's own success condition is that the docs name `aw next` and that `docs_check` reports no stale reference, so a docs edit is planned work rather than an incidental touch. `docs_check.check_aw_commands` validates `aw <sub>` mentions against the live parser (`docs_check.py:118-126`), so a doc naming `aw next` is only valid AFTER E-01 lands; sequence accordingly.
- Under-scope note on E-07's data change: adding a trailing field to `attention.Item` is a change to a shape consumed OUTSIDE `attention.py` (for example `releases.get_release_blockers`, `releases.py:328-340`). The trailing-with-default pattern keeps positional constructions valid, but the executor must grep for `Item(` constructions and for consumers that enumerate fields, and must run those suites (see Required tests).
- A declared path left unmodified needs a `--scope-ack` at finalize, so if the docs turn out to need no edit, acknowledge rather than force one.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_next_ordering.py tests/test_attention.py` for per-test counts.
- **`make test-all`, not just a bare run**: VERIFIED, both undeclared-leaf guards are module-level `slow` (`tests/test_command_surface_declarations.py:37` and `tests/test_cli_conformance_matrix.py:46`, each `pytestmark = pytest.mark.slow`) and are EXCLUDED from the bare fast suite, so a bare-only run would miss the tests most likely to catch a missing alias declaration.
- Also run `python3 -m pytest -o addopts="" tests/test_releases.py` (or whichever suite covers `releases.get_release_blockers`), because E-07 changes the `Item` shape that function's callers consume.
- The full suite BARE, `python3 -m pytest`, from the PRIMARY checkout. Re-measure the baseline on unmodified HEAD at execution time rather than trusting the recorded `3863 passed, 3 skipped, 4 xfailed`, which predates several commits. If a pre-existing environment-only failure appears (the plan previously noted `test_only_expected_files_contain_the_full_contract_prose` tripping on gitignored `opencode-recovery/` transcripts), confirm it against unmodified HEAD before attributing it to this work.
- A byte-comparison proving default output is unchanged: capture `aw attention --format json` BEFORE the change and diff it against `aw next --format json` after. Capture the BEFORE artifact FIRST, since the change is not reversible in-session once applied.
- `aw ipd lint --phase pre-transition` conforming on this plan.

## Spec / documentation sync

- Spec `25kzda` 5.4 rule 4 needs NO change: this plan implements a superset (its depth key) plus additional named keys, and F-3 records that the spec's order excludes priority so the two are not in conflict. Do not edit that spec to match this plan.
- `.aw/system/workflows/whatnext/whatnext.md` should eventually consume `-o` instead of asking the model to invent an order (F-6), but that is deferred above; do not edit it here.
- Docs and README must name `aw next` as canonical with `attention`/`att`/`todo` as aliases (E-02), or `docs_check` will report stale command references.

## Open questions

### OQ-01: Should `-o depth` order prerequisites FIRST or last?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED prerequisites FIRST, and the cited basis is VERIFIED at review: `queue_sort_key` (`oc_runipd.py:3572-3597`) puts `dependency_depth(...)` first in its ascending tuple, and its docstring states "a depth-0 node always precedes a node that declares an in-queue prerequisite, whatever their Order numbers say". Spec `25kzda` 5.4 rule 4 orders by dependency depth in the same direction. This also matches the order work must actually be done in. A reverse view is a small addition later if wanted.

### OQ-02: Should the default remain `class` forever, or become `depth` once it is proven?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED `class` as the permanent default in THIS plan. F-4's basis is VERIFIED: all four `xprio` plans pin "the shared sort key is UNCHANGED (priority not added to the sort tuple)" as required evidence, and three of them recorded that pin as OBSERVED evidence at execution, so the contract is live rather than aspirational. Keeping `class` default is what makes it literally true and what lets E-10 case (a) be a byte-identical regression test. Changing the default later is a deliberate, separately reviewable decision needing its own evidence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw next`, `aw attention`, `aw att` and `aw todo` output (or their sha256) showing all four identical BARE, and then again under `--format json`, `--check` and `--details`, showing all four identical there too (today `todo` ERRORS on `--format json`; that is the regression this proves fixed, F-10). Paste `aw todo --help` showing the action-ledger text is gone. Paste a grep proving the standalone `p_todo` parser and the `args.command == "todo"` dispatch special-case were DELETED. Paste `find_undeclared_leaves(_build_parser())` showing an empty set, plus the new `CommandDeclaration` for each of the four leaves.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the completion output offering `next`, and `aw check` output showing no docs finding for the renamed command.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `ORDER_KEYS` and the argparse refusal for `-o bogus` showing the valid list; confirm by grep that the CLI choices and completion are generated FROM the tuple and not re-typed.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the byte-comparison (diff or matching sha256) of `aw attention --format json` captured BEFORE the change against `aw next --format json` after, showing NO difference. This is the `xprio` contract and the single most important piece of evidence in this plan. Also paste two consecutive runs of one non-default `-o` showing identical output (determinism).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `-o priority` output showing high, then medium, then low, then unprioritized items, AND the item counts for `aw next` versus `aw next -o priority` proving they are EQUAL (ordering must never filter). State the measured coverage figures used.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste, for each of `date`, `set`, `order`, `blocking`, `id6`, `path`, `status`, `tree`, the first few ordered entries alongside the hand-checked expectation. Also show a filename that does NOT match the set/order grammar sorting as absent rather than raising.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `-o depth` output for a constructed chain A <- B <- C showing A, B, C in that order regardless of path/id, INCLUDING one cross-type edge (a plan declaring a `backlog` target) so the cross-type case the item asked for is actually demonstrated. Paste the DATA-GAP RESOLUTION: the new `Item` field (or the alternative chosen) and the parse site inside `scan()`, plus proof that no second artifact-reading pass was added, i.e. the call-count evidence from E-10 (i) rather than a prose assurance. Confirm in prose that `ipd_schema.parse_item_dependencies` and, if used, `check_engine._resolve_edge` were reused rather than reimplemented, citing the import lines.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the terminating output plus the cycle notice for a deliberately cyclic fixture, and confirm the process neither hung nor raised. Confirm `item_dependency_cycles` was reused, citing the import.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste `aw next --check -o <key>` exit codes on a CONSTRUCTED invalid fixture (a duplicate id6 across two trees) showing nonzero for EVERY `-o` value, plus exit 0 on the valid live tree. Do NOT cite the `ntf6sx` duplicate: it no longer exists and `aw attention --check` now exits 0 (F-9). Paste the sorted id sets for two different `-o` values proving they are IDENTICAL as sets and differ only in order. Prove the single-scan rule by CALL COUNT (E-10 case (i)), not by inspection alone.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste the COMPLETE `python3 -m pytest -o addopts="" tests/test_next_ordering.py tests/test_attention.py` output with per-test names and exit code, PLUS for each of the NINE cases (a) through (i) the FAILING output produced when its branch is deliberately broken, then confirm each break was reverted. Case (i)'s sabotage MUST be "introduce a second scan" and MUST fail, since a silent second scan is otherwise invisible in output. ALSO paste the `make test-all` result for the `slow` undeclared-leaf guard, and the bare full-suite summary line, re-measuring the baseline on unmodified HEAD at execution time rather than trusting the recorded `3863 passed, 3 skipped, 4 xfailed`, with any delta explained change-by-change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and requires explicit human approval before execution. It renames a command that agents and CI both invoke and touches the sort of the repo's primary read-only view, so there are THREE dangerous failures, none of which may be waived:

1. A silently CHANGED default order, which would break the `xprio` contract and every consumer's expectations. V-04's byte-comparison covers it (capture the BEFORE artifact first).
2. A missing alias declaration, which fails CI only in the `slow` suite. V-01's declaration evidence plus `make test-all` covers it.
3. A SILENT SECOND SCAN introduced by `-o depth`, identified at review (F-11). This one produces correct-looking output while breaking the single-authority rule that keeps `aw next`, `aw attention` and `aw doctor` from disagreeing, so no output assertion can detect it. E-10 case (i)'s call-count guard and V-07/V-09's call-count evidence exist for exactly this.

Execution contract: commit only files this plan changed, path-scoped, and never push. Other agents and runs are ACTIVE in this shared checkout, so before every commit verify the staged set with `git diff --cached --name-only` and `git restore --staged` anything not yours. Validate in the PRIMARY checkout, never a scratch worktree (`dh0uno`). Report validation by pasting the ACTUAL runner output; never claim a test result you did not run. Run `make test-all` and not only the bare suite, for the reason given under Required tests. Do NOT edit spec `25kzda` (located by `- Id:` at `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:7`) or the `whatnext` workflow.

Scope fence (a DECLARATION, so the runner can reconcile afterwards): the declared Scope-Paths are the five `agent_workflows/` modules, `docs/`, `README.md`, and the two test files. An edit outside that set is permitted but must be JUSTIFIED with a per-path `aw ipd finalize --scope-reason`; a declared path left unmodified needs a `--scope-ack`. Do NOT stop over a scope question. Do stop and report if a file you must edit is being changed concurrently and the two sets of changes cannot be safely combined.

Post-gate lifecycle: on completion move this plan to `.aw/records/plans/executed/` with `- Status: executed`, per the `ipd-lifecycle` workflow, only after every `V-*` above carries pasted evidence.
