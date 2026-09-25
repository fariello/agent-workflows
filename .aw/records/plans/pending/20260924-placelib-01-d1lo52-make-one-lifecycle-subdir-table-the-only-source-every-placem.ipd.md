# IPD: Make one lifecycle-subdir table the only source every placement consumer reads

- Date: 2026-09-24
- Kind: child
- Concern: Which record types have status subdirectories, and what those subdirectories are, is still written out as independent string literals in several modules; `record_placement` (r9uvwc) unified the WRITERS but reads these literals rather than owning them, so a status added to one copy silently desyncs the others.
- Scope: IN: a new dependency-free leaf module `agent_workflows/lifecycle_dirs.py` holding the one table; every literal copy of a lifecycle-subdir set re-derived from it (`layout.build_default_layout`, `backlog.STATUS_DIRS`, `plans.DISPOSITION_DIRS`, `engine.PLAN_LIFECYCLE_SUBDIRS`/`PROMPT_LIFECYCLE_SUBDIRS`, `ipd_lint._dir_of`, `attention_contract.SPEC_STATUSES` and its two re-listings in `status_set.TYPE_STATUSES`/`ipd_schema._ITEM_DEP_STATE_STATUSES`, and the fallback/valid-subdir literals inside `record_placement`); the verbs that still hardcode a status-to-subdir path join (`backlog` new AND `backlog set`, `ipd_authoring` scaffold) take the subdir from `record_placement.target_subdir`; a consumer-agreement test plus an AST drift guard. OUT: changing any status vocabulary or any file location; the plans many-to-one status mapping itself (already owned by `record_placement.target_subdir`); promoting location-equals-status to a fail-closed `aw check` rule; `ipd_authoring`'s hardcoded `.aw/records/plans` type-dir PREFIX (only its `"pending"` subdir is in scope, because the resulting path feeds `_existing_plan_ids`' walk); and `record_placement`'s two literal TYPE-name lists, which name record types rather than subdirs.
- Scope-Paths: agent_workflows/lifecycle_dirs.py, agent_workflows/layout.py, agent_workflows/backlog.py, agent_workflows/plans.py, agent_workflows/engine.py, agent_workflows/ipd_lint.py, agent_workflows/record_placement.py, agent_workflows/attention_contract.py, agent_workflows/status_set.py, agent_workflows/ipd_schema.py, agent_workflows/ipd_authoring.py, tests/test_lifecycle_dirs.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- Id: d1lo52
- From-Backlog: x9qv9q
- Set: placelib
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us

## Workflow history
- 2026-09-25 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): Reviewed via /plan-review; 8 findings (PR-701..PR-708), all FIXED. Corrected E-01 to source the spec row's order from layout rather than from attention_contract.SPEC_STATUSES, which is a frozenset whose iteration order varies per process and whose order approved spec kw5y2s pins as a JSON array. Split the bundled test item because its two classes have OPPOSITE pre-migration expectations (agreement must pass, drift guard must fail). Corrected the Findings claim that the guard sees record_placement's literals (measured: zero hits; they are type names). Found a thirteenth hardcoded status join in backlog's set path. Pinned the previously untested has_lifecycle_subdirs alias behavior. Corrected V-04/V-05 to compare tuples positionally and sets with sorted(). Rewrote the gate.

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog x9qv9q; re-measured that r9uvwc's `record_placement` already replaced the status_set if/elif chain and the `specs new` flat-root write, and that an AST scan of `agent_workflows/*.py` still finds 12 independent literal copies of a lifecycle-subdir set across 9 modules.

## Goal

Own "which record types have status subdirectories and what they are" in exactly one table, make every consumer derive from it, and add a test that fails if any consumer disagrees with the table or if a new literal copy appears.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the table and its guard

- [ ] E-01 Create `agent_workflows/lifecycle_dirs.py`, importing nothing from `agent_workflows`, defining `LIFECYCLE_SUBDIRS: Mapping[str, Tuple[str, ...]]` (a `types.MappingProxyType`) with exactly four keys: `plans` and `prompts` = `("pending", "executed", "superseded", "not-executed", "reusable")`, `specs` = `("draft", "to-review", "reviewed", "approved", "implementing", "implemented", "deferred", "parked", "superseded")`, `backlog` = `("open", "graduated", "blocked", "parked", "done")`; plus `subdirs_for(record_type) -> Tuple[str, ...]` returning `()` for any other type, and `PLANS_DONE_ALIAS = "done"` with a comment that it is a legacy read alias, not a subdir. TAKE THE SPEC ROW'S ORDER FROM `layout.build_default_layout()`'s `specs` `lifecycle_subdirs` TUPLE, which is the ordered authority, and NOT from `attention_contract.SPEC_STATUSES`: that symbol is a `frozenset`, so it HAS no order and its iteration order varies per process with `PYTHONHASHSEED` (measured at review: three consecutive interpreters produced three different orders). ORDER IS A SHIPPED CONTRACT, not cosmetic: approved spec `kw5y2s` pins `"lifecycle_subdirs": ["draft", "to-review", "reviewed", "approved", "implementing", "implemented", "deferred", "parked", "superseded"]` as a JSON ARRAY, and `layout.WorkspaceLayout.to_dict` emits `list(rc.lifecycle_subdirs)` positionally, so a set-derived row would emit a spec-violating permutation that differs between runs. Write the row as a LITERAL TUPLE in this module (this is the one file the drift guard exempts, and it is now the single ordered source).
  - Depends on: none
  - Expected outcome: `python3 -c "from agent_workflows import lifecycle_dirs as L; print(dict(L.LIFECYCLE_SUBDIRS))"` prints the four rows with the spec row in the order above; `grep -n "^from agent_workflows\|^import agent_workflows" agent_workflows/lifecycle_dirs.py` prints nothing; and `python3 -c "..."` run three times under different `PYTHONHASHSEED` values prints the spec row IDENTICALLY each time.
  - Execution state: pending

- [ ] E-02 Add `tests/test_lifecycle_dirs.py` `ConsumerAgreementTests`: for EVERY name in `layout.build_default_layout().record_classes`, assert `record_classes[name].lifecycle_subdirs == subdirs_for(name)` and `record_placement.has_lifecycle_subdirs(name) == bool(subdirs_for(name))`; for every type with subdirs and every subdir `d`, assert `record_placement.target_subdir(type, d) == d`; assert `backlog.STATUS_DIRS == LIFECYCLE_SUBDIRS["backlog"]`, `plans.DISPOSITION_DIRS == LIFECYCLE_SUBDIRS["plans"] + (PLANS_DONE_ALIAS,)` (an ORDERED tuple comparison, not the `set(...) == set(...) | {"done"}` shape originally written: `plans.DISPOSITION_DIRS`' order is user-visible, since `plans.collect` and the board renderer both iterate it positionally to order the `## <disp>/` sections, so a set comparison would pass on a permutation that visibly reorders the board), `engine.PLAN_LIFECYCLE_SUBDIRS == LIFECYCLE_SUBDIRS["plans"]`, `engine.PROMPT_LIFECYCLE_SUBDIRS == LIFECYCLE_SUBDIRS["prompts"]`, `attention_contract.SPEC_STATUSES == frozenset(LIFECYCLE_SUBDIRS["specs"])`, `status_set.TYPE_STATUSES["specs"] == set(LIFECYCLE_SUBDIRS["specs"])`, `ipd_schema._ITEM_DEP_STATE_STATUSES["spec"] == frozenset(LIFECYCLE_SUBDIRS["specs"])`, and `ipd_lint._dir_of(Path("x") / d / "p.ipd.md") == d` for every plans subdir. ALSO assert `layout.build_default_layout().to_dict("0")["record_classes"]["specs"]["lifecycle_subdirs"] == list(LIFECYCLE_SUBDIRS["specs"])` POSITIONALLY, which is the assertion that pins approved spec `kw5y2s`'s JSON array order (see E-01). AND assert the ALIAS behavior `record_placement.has_lifecycle_subdirs("plan") is True` and `("spec") is True`, which holds today only because `has_lifecycle_subdirs` resolves aliases through `layout.get_record_class` BEFORE reaching its fallback; no existing test pins it (`tests/test_record_placement.py` covers only `research`/`walkthroughs`), so E-06 could silently lose it.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_lifecycle_dirs.py::ConsumerAgreementTests` PASSES immediately after E-01 and before any migration, because every consumer already agrees with the table by value; it is the pre-migration BASELINE that proves the table transcribes today's truth rather than changing it. (Verified at review: all of these assertions hold at HEAD.)
  - Execution state: pending

- [ ] E-03 Add `tests/test_lifecycle_dirs.py` `LiteralDriftGuardTests`: `ast`-walk every `agent_workflows/**/*.py` except `lifecycle_dirs.py`, and fail naming `file:line` for any `Tuple`/`List`/`Set` whose elements are ALL `str` constants and whose value set is a superset of some table row with at most one extra element. Run it BEFORE E-04..E-07 so it fails. STATE THE PREDICATE'S TWO MEASURED LIMITS in the test's own docstring, because the plan's enforcement claim rests on them. FIRST, it sees only literal COLLECTIONS OF SUBDIR NAMES, so it does NOT see `record_placement`'s two literals: those are lists of TYPE names (`("plans", "prompts", "backlog", "specs")` and `("backlog", "specs")`), which no table row is a subset of, so E-06's `record_placement` edits are NOT guarded by this test and are pinned only by `ConsumerAgreementTests` and `tests/test_record_placement.py`. SECOND, the at-most-one-extra bound is what keeps the 11-element `status_set.TYPE_STATUSES["plans"]` and the 6-element `ipd_schema._ITEM_DEP_STATE_STATUSES["ipd"]` from tripping, so a genuine future copy that happens to carry two extra elements would evade it.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_lifecycle_dirs.py` FAILS on `LiteralDriftGuardTests` only, listing the 12 sites named by symbol in the Findings section (re-derive the `file:line` offsets at execution time; the Findings list is the authoring measurement re-verified at review, and is context rather than the bar). The bar is that every site listed is one E-04..E-06 removes, and that no site outside those items is listed.
  - Execution state: pending

### Task group 2: move every consumer onto the table

- [ ] E-04 In `layout.build_default_layout`, replace the four `lifecycle_subdirs=(...)` literals for `plans`, `specs`, `prompts`, `backlog` with `lifecycle_subdirs=_LD.subdirs_for("<name>")` (`from agent_workflows import lifecycle_dirs as _LD`, a leaf, so layout stays import-light). In `engine`, set `PLAN_LIFECYCLE_SUBDIRS = _LD.LIFECYCLE_SUBDIRS["plans"]` and `PROMPT_LIFECYCLE_SUBDIRS = _LD.LIFECYCLE_SUBDIRS["prompts"]`. NOTE the import-light claim is MEASURED, not assumed: `layout` today pulls only 4 `agent_workflows` modules (`_compat`, `versioning`, itself, the package), and `attention_contract`, `plans` and `layout` each currently have ZERO intra-package imports, so this plan adds the FIRST such edge to three deliberately dependency-free modules. That is acceptable only because `lifecycle_dirs` imports nothing from the package and therefore cannot participate in a cycle; state that reason in the new module's docstring so a later reader does not add an import to it.
  - Depends on: E-03
  - Expected outcome: `python3 -m agent_workflows layout --json` (in-process model source; the emitted `.aw/system/layout.json` is gitignored) prints output byte-identical to the pre-change capture, and the `specs` `lifecycle_subdirs` array is in spec `kw5y2s`'s pinned order. (Verified at review that this command is stable across runs, so a `diff` of two captures is a meaningful test.)
  - Execution state: pending

- [ ] E-05 Set `backlog.STATUS_DIRS = _LD.LIFECYCLE_SUBDIRS["backlog"]` (keeping `STATUSES = frozenset(STATUS_DIRS)`), `plans.DISPOSITION_DIRS = _LD.LIFECYCLE_SUBDIRS["plans"] + (_LD.PLANS_DONE_ALIAS,)`, and `attention_contract.SPEC_STATUSES = frozenset(_LD.LIFECYCLE_SUBDIRS["specs"])`; replace the `status_set.TYPE_STATUSES["specs"]` literal with `set(_LD.LIFECYCLE_SUBDIRS["specs"])` and the `ipd_schema._ITEM_DEP_STATE_STATUSES["spec"]` literal with `frozenset(_LD.LIFECYCLE_SUBDIRS["specs"])`, each with a one-line comment in the style of the existing "bklgrad Order 01 (v58bvy)" derivation comments. DERIVE BOTH FROM THE TABLE DIRECTLY, not from `attention_contract.SPEC_STATUSES` as originally written: `ipd_schema` does NOT import `attention_contract` today (measured: its intra-package imports are `artifact_core`, `backlog`, `plans`), so routing through it would add a second, avoidable import edge to reach a value the leaf table already holds, and it would make `ipd_schema`'s vocabulary depend on a module whose own row this plan is simultaneously re-deriving. `status_set` already imports `attention_contract`, so either spelling works there; use the table for symmetry so both re-listings cite one source. `plans.DISPOSITION_DIRS`' concatenation order is load-bearing (see E-02) and the formula above reproduces the current tuple exactly, verified at review.
  - Depends on: E-03
  - Expected outcome: `python3 -c` printing `backlog.STATUS_DIRS`, `plans.DISPOSITION_DIRS` (ordered tuples, compared positionally) and `sorted(...)` of the three set-typed symbols shows values equal to the pre-change capture. Use `sorted()` for `SPEC_STATUSES`, `TYPE_STATUSES["specs"]` and `_ITEM_DEP_STATE_STATUSES["spec"]` because all three are sets and their raw iteration order is not reproducible between processes; a raw-order comparison would be a flaky test, not a stricter one.
  - Execution state: pending

- [ ] E-06 In `ipd_lint._dir_of`, iterate `_LD.LIFECYCLE_SUBDIRS["plans"]` instead of the literal `("pending", "executed", "superseded", "not-executed", "reusable")`. PRESERVE THE ITERATION ORDER EXACTLY: `_dir_of` returns the FIRST anchor of that tuple found anywhere in the resolved path's parts, so for a path containing two anchors the answer is decided by the tuple's order and not by the path's (measured at review: both `/tmp/executed/pending/p.ipd.md` and `/tmp/pending/executed/p.ipd.md` return `pending`). The table row preserves that order, so this is behavior-neutral; it is called out because a future reordering of the row would silently change lint's directory attribution. In `record_placement`, replace the `has_lifecycle_subdirs` FALLBACK `record_type in ("plans", "prompts", "backlog", "specs")` with `bool(_LD.subdirs_for(record_type))`, keeping the `layout.get_record_class` lookup as the PRIMARY path so ALIAS resolution (`"plan"`, `"spec"`) is unchanged; and replace the `valid_subdirs` expression (`set(_BL.STATUS_DIRS) if record_type == "backlog" else set(_AC.SPEC_STATUSES)`) with `set(_LD.subdirs_for(record_type))`.
  - Depends on: E-03
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_record_placement.py tests/test_ipd_lint.py` passes unchanged, AND `record_placement.has_lifecycle_subdirs("plan")` / `("spec")` still return True (E-02's new alias assertions), which is the check that the fallback replacement did not collapse the alias path.
  - Execution state: pending

- [ ] E-07 In `backlog` creation (the statement `dest = _resolve_backlog_root(repo_root) / status / filename`), take the subdir from `record_placement.target_subdir("backlog", status)` while keeping `_resolve_backlog_root` as the type dir (so the neither-tree-exists fallback to `.agents/backlog` is unchanged). This is behavior-neutral because `target_subdir("backlog", s)` is measurably an IDENTITY for every input including an unrecognized one (both of its branches return `status`), so no status can start landing somewhere new. ALSO convert the SECOND such join in the same module, `dest_dir = _resolve_backlog_root(repo_root) / new_status` in the `backlog set` path: it is the same hardcoded status-to-subdir join as the creation site, the plan's own Findings missed it, and leaving one of a matched pair converted is how the next reader concludes the migration was deliberate and partial. In `ipd_authoring` scaffold (the statement `pending = repo_root / ".aw" / "records" / "plans" / "pending"`), replace the literal `"pending"` with `record_placement.target_subdir("plans", "to-review")`. Do NOT also try to route that statement's `.aw/records/plans` prefix through `record_placement.resolve_type_dir`: the resulting `pending` variable is passed to `_existing_plan_ids`, whose `_plans_root_for` walk expects that shape, so changing the type-dir resolution is a separate behavior change this plan has not measured.
  - Depends on: E-03
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_backlog.py` passes, and a scratch-repo `aw backlog new` and `aw ipd scaffold --apply` write to `open/` and `pending/` respectively, same as before; `aw backlog set` moves an item to its status dir exactly as before.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-08 Re-run the drift guard and the consumer agreement, now expecting BOTH to pass: `python3 -m pytest -o addopts="" tests/test_lifecycle_dirs.py tests/test_layout.py tests/test_record_placement.py`. The guard itself is the probe, so there is no separate script to re-run; assert it reports ZERO sites rather than re-running an authoring-time scratch file.
  - Depends on: E-04, E-05, E-06, E-07
  - Expected outcome: all pass, `LiteralDriftGuardTests` now reporting no sites. Also paste the guard's own site list from E-03's failing run beside this passing one, so the 12 -> 0 transition is visible; the accounting is E-04 removing 6 (layout x4, engine x2), E-05 removing 5 (`backlog`, `plans`, `attention_contract`, `status_set`, `ipd_schema`) and E-06 removing 1 (`ipd_lint`), which is exactly 12.
  - Execution state: pending

- [ ] E-09 Run the bare suite `python3 -m pytest`.
  - Depends on: E-08
  - Expected outcome: summary line shows 0 failed, against a baseline taken the same way at the start of execution.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Derive, never re-list: `status_set.TYPE_STATUSES["backlog"]` and `ipd_schema._ITEM_DEP_STATE_STATUSES["backlog"]` already derive from `backlog.STATUSES` with comments citing "GUIDING_PRINCIPLES P8" after a hardcoded copy desynced (`graduated`). This plan extends that exact pattern.
- `attention_contract` is deliberately "dependency-light" (its own comment); the new module must be a leaf so `attention_contract`, `layout`, `backlog` and `plans` can all import it without a cycle. MEASURED AT REVIEW: `attention_contract`, `plans` and `layout` currently have ZERO intra-package imports (not merely few), and importing `layout` pulls only 4 `agent_workflows` modules, so this plan adds the first such edge to each of the three. A leaf cannot cycle, which is what makes it acceptable; the new module's docstring must say so, since the invariant is only preserved by nobody adding an import to it later.
- A `frozenset` is not an ordered source. `attention_contract.SPEC_STATUSES` and `ipd_schema._ITEM_DEP_STATE_STATUSES["spec"]` are sets; `layout`'s `lifecycle_subdirs`, `backlog.STATUS_DIRS`, `plans.DISPOSITION_DIRS` and `engine`'s two constants are ordered tuples whose order is consumed positionally (layout JSON per spec `kw5y2s`, the plans board's section order, `ipd_lint._dir_of`'s first-match anchor scan). Compare tuples positionally and sets with `sorted()`; doing the reverse is either a flaky test or a test that passes on a visible reordering.
- Tests run bare (`python3 -m pytest`); narrowed runs clear addopts with `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Re-measured at HEAD `cfc7f5c1` against the backlog item's claims:

| Backlog claim | Now | Evidence |
|---|---|---|
| status_set if/elif placement chain | FIXED by r9uvwc | `status_set` calls `record_placement.resolve_transition_path` ("Determine destination path using the shared record placement library") |
| `specs new` writes to flat root | FIXED by r9uvwc | `specs` calls `record_placement.resolve_creation_path("specs", "draft", ...)` |
| specs have no subdir knowledge | FALSE now | `layout` specs `lifecycle_subdirs` lists the nine statuses |
| nothing answers "which types have subdirs" | PARTLY: `record_placement.has_lifecycle_subdirs` answers, but by reading `layout`, with its own literal fallback | `record_placement.has_lifecycle_subdirs` |

The four sources of truth the task names still exist independently: (1) `backlog.STATUS_DIRS`, (2) `plans.DISPOSITION_DIRS`, (3) `attention_contract.SPEC_STATUSES`, (4) `layout.build_default_layout` `lifecycle_subdirs`. The probe also found further copies: `engine.PLAN_LIFECYCLE_SUBDIRS`, `engine.PROMPT_LIFECYCLE_SUBDIRS`, `ipd_lint._dir_of`, `ipd_schema._ITEM_DEP_STATE_STATUSES["spec"]`, `status_set.TYPE_STATUSES["specs"]`. That is TWELVE sites in NINE modules, re-verified at review by re-running the predicate, each named by the SYMBOL that owns it: `attention_contract.SPEC_STATUSES`, `backlog.STATUS_DIRS`, `engine.PLAN_LIFECYCLE_SUBDIRS`, `engine.PROMPT_LIFECYCLE_SUBDIRS`, `ipd_lint._dir_of`'s anchor tuple, `ipd_schema._ITEM_DEP_STATE_STATUSES["spec"]`, the `plans`/`specs`/`prompts`/`backlog` `lifecycle_subdirs=` arguments in `layout.build_default_layout` (four sites), `plans.DISPOSITION_DIRS`, and `status_set.TYPE_STATUSES["specs"]`. The only thing tying them together today is `tests/test_layout.py` `test_lifecycle_subdirs_match_the_live_status_dirs`, which hardcodes the plans and prompts sets and checks only layout (it compares the backlog and specs rows against their live symbols, so it is not a fifth full copy).

CORRECTED AT REVIEW: the sentence above originally counted "two literal-set expressions inside `record_placement`" among the copies the drift guard finds. It does not find them, and cannot. Both are lists of TYPE names, not subdir names (`("plans", "prompts", "backlog", "specs")` in `has_lifecycle_subdirs`' fallback and `("backlog", "specs")` in the `valid_subdirs` branch test), and no table row is a subset of either, so the superset predicate never matches them. Measured: running the predicate over `record_placement.py` yields ZERO hits, and the 12 sites above are all in other modules. This matters because it means E-06's `record_placement` edits carry NO drift-guard protection and are pinned only by `ConsumerAgreementTests` and the existing `tests/test_record_placement.py`; the guard's clean run after migration is therefore not evidence about that file.

TWO ORDERING FACTS MEASURED AT REVIEW, because the plan's E-01 and E-02 both depended on them and both had them wrong. FIRST, `attention_contract.SPEC_STATUSES` is a `frozenset`, so it has NO order: three consecutive interpreters printed `list(SPEC_STATUSES)` in three different orders. The ordered authority is `layout`'s `specs` `lifecycle_subdirs` TUPLE, and approved spec `kw5y2s` pins that exact sequence as a JSON array, which `layout.WorkspaceLayout.to_dict` emits positionally via `list(rc.lifecycle_subdirs)`. SECOND, `plans.DISPOSITION_DIRS`' order is USER-VISIBLE: `plans.collect` and the board renderer both iterate it positionally to order the `## <disp>/` sections, and `ipd_lint._dir_of` iterates its own copy positionally too, returning the FIRST anchor present in a path rather than the path's own first anchor (measured: `/tmp/executed/pending/p.ipd.md` and `/tmp/pending/executed/p.ipd.md` both return `pending`).

A THIRTEENTH SITE THE PROBE CANNOT SEE, found at review by reading `backlog.py` rather than by AST: `backlog`'s `set` path joins `_resolve_backlog_root(repo_root) / new_status` exactly as its creation path joins `/ status / filename`. It is the same hardcoded status-to-subdir join E-07 converts at the creation site, it is invisible to a literal-collection predicate because it is a path join and not a collection, and the plan's Findings missed it. E-07 now converts both.

AN ALIAS BEHAVIOR NO TEST PINS, also found at review: `record_placement.has_lifecycle_subdirs` resolves ALIASES, so `has_lifecycle_subdirs("plan")` and `("spec")` are both True today, because `layout.get_record_class` maps an alias to its class BEFORE the literal fallback is reached. `tests/test_record_placement.py` covers only `research` and `walkthroughs`, so nothing would have caught a change that collapsed the alias path into a table lookup. E-02 now asserts it and E-06 is explicit that the layout lookup stays primary.

## Proposed changes (ordered, validatable)

1. Leaf table module, with the spec row's order taken from `layout` and not from a frozenset (E-01).
2. Consumer agreement test FIRST, expected to PASS immediately, as the baseline proving the table transcribes today's truth (E-02); then the AST drift guard, expected to FAIL, as the enforcement (E-03). These are separate items because they have opposite pre-migration expectations, and a single test file reporting one failure count cannot distinguish a real drift finding from a broken baseline.
3. Re-derive each consumer (E-04 layout/engine, E-05 vocab modules, E-06 lint/placement, E-07 creation verbs including the second backlog join).
4. Prove zero remaining literals with the 12 -> 0 accounting, then a green suite (E-08, E-09).

## Deferred / out of scope (with reason)

- A fail-closed `aw check` rule that a record's directory equals its status: separate enforcement concern, out of this item's scope.
  - Carrier-Declined: not requested by x9qv9q; r9uvwc's Scope already names it OUT, and no defect is measured today.
- Simplifying `tests/test_layout.py` `test_lifecycle_subdirs_match_the_live_status_dirs` to read the table: left as-is because it stays correct and is subsumed by `ConsumerAgreementTests`.
  - Carrier-Declined: redundant but harmless; removing it gains nothing measurable. Verified at review that it compares the backlog and specs rows against their LIVE symbols and only hardcodes the plans/prompts sets, so after this plan it still passes and is not a surviving copy the drift guard would flag (it is a test file, which the guard does not walk in any case).
- Routing `ipd_authoring` scaffold's `.aw/records/plans` type-dir prefix through `record_placement.resolve_type_dir`, alongside the `"pending"` subdir E-07 does convert.
  - Carrier-Declined: ADDED AT REVIEW. The resulting `pending` path is passed to `_existing_plan_ids`, whose `_plans_root_for` walk expects that shape, so changing type-dir resolution there is a behavior change this plan has not measured and the backlog item did not ask for. The subdir half is the part that is a lifecycle-table concern.
- Removing `record_placement`'s two literal TYPE-name lists, or making the drift guard able to see them.
  - Carrier-Declined: they are type names, not subdir names, so they are outside this plan's table concern; widening the guard to also police type-name lists would need the canonical type list as a second table and is a different unification. E-06 still re-derives the one that is a genuine fallback duplicate of the table's key set.

## Scope check

- Over-scope: E-05 also re-derives two spec-status re-listings (`status_set`, `ipd_schema`); they are copies of the same nine-element set and the drift guard DOES flag them (`status_set.TYPE_STATUSES["specs"]` and `ipd_schema._ITEM_DEP_STATE_STATUSES["spec"]`, both confirmed flagged at review), so leaving them would make E-03's guard unpassable. Nothing else in the plan touches behavior.
- Under-scope: the authored plan had four gaps, each now fixed and named in Findings — the spec row's order sourced from an unordered frozenset (E-01), the drift guard and the agreement baseline bundled into one item with opposite expectations (E-02/E-03), a thirteenth hardcoded status join in `backlog`'s `set` path (E-07), and an unpinned alias behavior in `has_lifecycle_subdirs` (E-02/E-06). The drift guard plus the agreement test are what make the remaining claim checkable, with the guard's two measured limits stated rather than implied.

## Required tests / validation

New `tests/test_lifecycle_dirs.py`: `ConsumerAgreementTests` passing BEFORE migration (the baseline) and `LiteralDriftGuardTests` failing before and passing after (the enforcement), with the two runs kept distinguishable. The agreement test additionally pins spec `kw5y2s`'s array order positionally through `to_dict`, and the `has_lifecycle_subdirs` alias behavior. Determinism evidence for the spec row across three `PYTHONHASHSEED` values. Existing `tests/test_layout.py`, `tests/test_record_placement.py`, `tests/test_backlog.py`, `tests/test_ipd_lint.py` pass unchanged as the behavior-preservation bar (verified at review: 75 passed across the first three at HEAD). Driven scratch-repo evidence for `aw backlog new`, `aw backlog set` and `aw ipd scaffold --apply`. Bare suite green against a baseline.

## Spec / documentation sync

No `.spec.md` is edited, so none is in `- Scope-Paths:`. But spec `kw5y2s` is NOT merely descriptive here and the distinction is load-bearing: it PINS `"lifecycle_subdirs": ["draft", "to-review", ...]` as an ordered JSON array for `plans` and `specs`, and `layout.WorkspaceLayout.to_dict` emits `list(rc.lifecycle_subdirs)` positionally. So the table's row order is a shipped contract this plan must reproduce exactly, which is why E-01 sources it from `layout` rather than from a set and why E-02 asserts the emitted array positionally. E-04 keeping `aw layout --json` byte-identical is the evidence that the contract held; a set-derived row would have violated it non-deterministically, differing between runs of the same code.

## Open questions

### OQ-01: Should the drift guard's superset-plus-one predicate be widened later?

- Blocking: no
- Status: resolved
- Owner: none
- Carrier-Declined: The question asks whether to widen a guard that is being introduced by this plan and that measurably covers every site this plan removes. There is no outstanding obligation: if a future copy evades it, that copy is the defect and gets its own item then, and E-03 writes both limits into the test's docstring so the next reader inherits the measurement instead of re-deriving it. Widening now would be speculative work against no observed miss.
- Resolution or deferral rationale: Resolved from repo evidence, and the evidence was RE-RUN at review rather than trusted: the predicate flags exactly the 12 sites listed in Findings and none of the wider status vocabularies (`status_set.TYPE_STATUSES["plans"]` has 11 elements against a 5-element row; `ipd_schema._ITEM_DEP_STATE_STATUSES["ipd"]` has 6 against the same row and also does not trip). TWO LIMITS ARE NOW STATED EXPLICITLY rather than left as a general caveat, because one of them materially bounds this plan's enforcement claim. (a) The guard sees only literal COLLECTIONS OF SUBDIR NAMES, so it never sees `record_placement`'s two TYPE-name lists (measured: zero hits in that file) and never sees a hardcoded path JOIN such as `backlog`'s `/ new_status` (the thirteenth site, found by reading, not by AST). So a clean guard run is NOT evidence that `record_placement` or `backlog` were migrated; `ConsumerAgreementTests`, `tests/test_record_placement.py`, `tests/test_backlog.py` and V-07's driven output are. (b) The at-most-one-extra bound is exactly what prevents the two wider vocabularies above from tripping, so a genuine future copy carrying two or more extra elements would evade it. Both limits are recorded in the test's own docstring by E-03.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the output of `python3 -c "from agent_workflows import lifecycle_dirs as L; print(dict(L.LIFECYCLE_SUBDIRS)); print(L.subdirs_for('research'))"` showing the four rows and `()`, and the empty output of `grep -n "^from agent_workflows\|^import agent_workflows" agent_workflows/lifecycle_dirs.py`. PLUS the determinism proof the ordering finding demands: run `PYTHONHASHSEED=0`, `PYTHONHASHSEED=1` and `PYTHONHASHSEED=2` printing `LIFECYCLE_SUBDIRS["specs"]` and paste all three, IDENTICAL; and paste `python3 -c "from agent_workflows import layout; print(layout.build_default_layout().record_classes['specs'].lifecycle_subdirs)"` showing the table row equals layout's ordered tuple. A row derived from `attention_contract.SPEC_STATUSES` would differ between those three runs, so this is the evidence that it was not.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the PASSING output of `python3 -m pytest -o addopts="" tests/test_lifecycle_dirs.py::ConsumerAgreementTests` run after E-01 and BEFORE any migration, with the collected test count, establishing the pre-migration baseline that every consumer already agrees with the table. Include the alias assertions' results and the positional `to_dict` spec-array assertion explicitly, since those two are new at review and are what pin `kw5y2s` and the `has_lifecycle_subdirs` alias path.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the FAILING output of `python3 -m pytest -o addopts="" tests/test_lifecycle_dirs.py` run after E-02 and before E-04..E-07, showing `LiteralDriftGuardTests` FAILING with its `file:line` site list and `ConsumerAgreementTests` still PASSING (the two must be distinguishable, or a single failure count cannot tell a real drift finding from a broken baseline). Name every listed site and confirm each is one E-04..E-06 removes.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `diff` of `python3 -m agent_workflows layout --json` captured before and after E-04 (empty), the `record_classes.specs.lifecycle_subdirs` array from the after-capture showing spec `kw5y2s`'s pinned order, and `python3 -c "from agent_workflows import engine as E; print(E.PLAN_LIFECYCLE_SUBDIRS, E.PROMPT_LIFECYCLE_SUBDIRS)"` showing the five-element tuples.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste a before/after `python3 -c` print of `backlog.STATUS_DIRS` and `plans.DISPOSITION_DIRS` as RAW TUPLES (positional comparison, since both are ordered and `DISPOSITION_DIRS`' order drives the board's section order), and of `sorted(attention_contract.SPEC_STATUSES)`, `sorted(status_set.TYPE_STATUSES['specs'])`, `sorted(ipd_schema._ITEM_DEP_STATE_STATUSES['spec'])` (sorted, because those three are sets with no reproducible iteration order). Also paste `git diff agent_workflows/ipd_schema.py` showing the new derivation reads the TABLE and did not add an `attention_contract` import.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the pass summary of `python3 -m pytest -o addopts="" tests/test_record_placement.py tests/test_ipd_lint.py`, `git diff agent_workflows/ipd_lint.py agent_workflows/record_placement.py` showing no literal subdir tuple remains AND that `has_lifecycle_subdirs` still calls `layout.get_record_class` before its fallback, and `python3 -c` output showing `has_lifecycle_subdirs("plan")` and `("spec")` both True. Also paste `_dir_of` driven on a two-anchor path (for example `/tmp/executed/pending/p.ipd.md`) returning the same answer as before the change, which is the order-preservation check.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the pass summary of `python3 -m pytest -o addopts="" tests/test_backlog.py`, and from a scratch repo the paths printed by `aw backlog new ... --apply` (under `backlog/open/`) and `aw ipd scaffold ... --apply` (under `plans/pending/`). PLUS evidence for the second backlog join this item now also converts: drive `aw backlog set` on a scratch item through at least two statuses and paste the resulting paths, showing the item lands in the status dir exactly as before. Use a scratch repo inside the workspace or the agent's own permitted temp area; do not assume `/tmp` is writable by policy.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the pass summary of `python3 -m pytest -o addopts="" tests/test_lifecycle_dirs.py tests/test_layout.py tests/test_record_placement.py` with `LiteralDriftGuardTests` now PASSING, beside V-03's failing site list, so the 12 -> 0 transition is visible in one place. State the per-item accounting (E-04: 6, E-05: 5, E-06: 1) and confirm it sums to the number V-03 listed.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the final summary line of the bare `python3 -m pytest` run showing `passed` and no `failed`, with the baseline summary line taken the same way before execution.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (own the lifecycle-subdir table once and make every consumer derive from it). E-02 and E-03 are separate items despite living in one new test file because their pre-migration expectations are OPPOSITE — the agreement baseline must PASS, the drift guard must FAIL — and a single item could report one aggregate failure count that cannot distinguish a real drift finding from a broken baseline. E-04..E-07 are split by consumer group because each has its own regression evidence (a byte-identical JSON capture, ordered-tuple prints, lint/placement tests, driven scratch-repo paths).

WHAT A HUMAN IS APPROVING. A pure-refactor unification with NO intended behavior change, whose correctness bar is that eleven existing behaviors stay byte-for-byte identical. Two things are worth an explicit look. FIRST, this plan adds the FIRST intra-package import to three modules that today have ZERO (`layout`, `plans`, `attention_contract`), which is a deliberate relaxation of their dependency-free posture; it is safe only because `lifecycle_dirs` imports nothing from the package and so cannot participate in a cycle, and that reason is required to be written into the new module's docstring. SECOND, the table's spec-row ORDER is a shipped contract from approved spec `kw5y2s`, so the new module becomes the single authority for a sequence the spec pins; a later edit to that row changes emitted layout JSON and the plans board's section order, and the module must say so.

SCOPE FENCE (a declaration, so the runner can reconcile afterwards; not an instruction to stop over a scope question). Within the declared paths the intended surface is: `lifecycle_dirs.py` NEW, the four rows plus `subdirs_for` and `PLANS_DONE_ALIAS`, importing nothing from the package; `layout.py` the four `lifecycle_subdirs=` arguments only; `engine.py` the two module constants only; `backlog.py` `STATUS_DIRS` plus the TWO status-to-subdir path joins (creation and `set`); `plans.py` `DISPOSITION_DIRS` only; `attention_contract.py` `SPEC_STATUSES` only; `status_set.py` the `TYPE_STATUSES["specs"]` entry only; `ipd_schema.py` the `_ITEM_DEP_STATE_STATUSES["spec"]` entry only; `ipd_lint.py` `_dir_of`'s anchor tuple only; `record_placement.py` `has_lifecycle_subdirs`' fallback and the `valid_subdirs` expression only; `tests/test_lifecycle_dirs.py` NEW. DELIBERATELY NOT IN SCOPE, mirroring Deferred: any status VOCABULARY change, any file relocation, the plans many-to-one status mapping in `target_subdir`, a directory-equals-status `aw check` rule, `tests/test_layout.py`, `ipd_authoring`'s type-dir prefix, and `record_placement`'s two TYPE-name lists. An out-of-scope edit that proves necessary should be MADE and then justified with `--scope-reason` at finalize.

HONESTY RULE (hard MUST). Paste the ACTUAL command output for every `V-*` item. Two specific temptations to refuse: do not record V-02/V-03 from a single combined pytest run, because the point is that one file's two classes have opposite expectations at that moment; and do not report the drift guard's clean post-migration run as evidence about `record_placement` or `backlog`, which it measurably cannot see.

STOP CONDITIONS (genuinely unsafe, distinct from a scope question). Stop and report if: `ConsumerAgreementTests` FAILS at E-02, before any migration, because that means the table does not transcribe current truth and every later "identical" claim would be measured against the wrong baseline; the `aw layout --json` before/after diff is non-empty, since that is a shipped-contract violation rather than a test to adjust; or a symbol this plan expects to edit has been changed under you by concurrent work.

Execute only after explicit human approval (`- Status: approved`). Commit through `aw commit d1lo52 -- <Scope-Paths>`; never push. After every `V-*` item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, the lifecycle transition to `executed/` is performed by the RUNNER when one is driving this plan, and by the executor via `aw ipd finalize` only when no runner owns the transition; do not hand-roll a `git mv`. Setting x9qv9q to `done` is a separate step after execution, not part of authoring (it carries no `- Blocks-Release:`, so no release gate is owed and none may be invented).
