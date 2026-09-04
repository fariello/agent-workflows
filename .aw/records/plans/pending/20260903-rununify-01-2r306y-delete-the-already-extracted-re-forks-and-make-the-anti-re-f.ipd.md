# IPD: delete the already-extracted re-forks and make the anti-re-fork guards symmetric

- Date: 2026-09-03
- Kind: child
- Concern: Five symbols are DEFINED inside the runner modules even though a non-runner module already owns an AST-identical definition, so a fix to the owner silently does not reach the runner. This is not hypothetical: it is exactly how `Heartbeat` drifted (`stallfp-01`/`kaga7s`), and the reason it went unnoticed is that the anti-re-fork guard was written for ONE runner only. `tests/test_render_stream.py:539` (`test_oc_runipd_source_has_no_inline_definitions`) asserts ten render-layer names are absent from `oc_runipd`, and NOTHING makes the same assertion about `agy_runipd`; its only agy-side guard (`:554`) covers `Heartbeat` alone. So agy still carries `Palette` (`agy_runipd.py:262`), `_strip_ansi` (`:284`) and `_one_line` (`:288`), all three AST-identical to `render_stream`'s, and BOTH runners carry `_read_id`/`_read_status` (`oc_runipd.py:2193`/`:2198`, `agy_runipd.py:1362`/`:1367`) AST-identical to `selectors.py`'s. Measured at HEAD `c8bb11ae` by research `tvnq50` (E-01 of orchestrator `5e4sb6`).
- Scope: Delete those five re-forked definitions and import them from their owning modules instead, then make the guard SYMMETRIC so a re-fork in either runner fails a test. This is the Set's cheapest and most clearly-correct slice: every deletion is provably behavior-neutral because the replacement definition is AST-identical, verified per symbol rather than assumed. Excludes extracting the class (a) common symbols (that is child 02), excludes reconciling any diverged symbol (deferred behind `lanectn` and the E-02 characterization baseline), excludes changing `render_stream`, permits only public aliases for `_read_id`/`_read_status` in `selectors`, and excludes `Heartbeat`, which is ALREADY FIXED (`agy_runipd.py:43` imports it) so this plan must not "re-fix" it.
- Scope-Paths: agent_workflows/agy_runipd.py, agent_workflows/oc_runipd.py, agent_workflows/selectors.py, tests/test_render_stream.py, tests/test_runner_refork_guard.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: rununify
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 2r306y
- Approval: 2026-09-04, recorded via aw ipd set: status set to approved
- Blocks-Release: next

## Workflow history
- 2026-09-04 approved (aw set): status set to approved

- 2026-09-03 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-201..PR-204; GO - PENDING HUMAN APPROVAL. Verified at HEAD `25d3f0b0`, tree clean, plan committed and unchanged, so the pre-review snapshot was correctly skipped. `aw ipd lint` conforming at `--phase author` and again at `--phase review-finalize`. EVERY LOAD-BEARING CLAIM RE-MEASURED INDEPENDENTLY, not read from the plan: all five re-forks exist at the cited lines and all five are AST-identical to their owners' definitions (verified per symbol by comparing `ast.dump(ast.parse(ast.unparse(node)))`, the method the plan itself specifies), so the behavior-neutrality claim HOLDS; the guard really is one-sided (9 `assertNotIn` lines for oc, `Heartbeat` only for agy); `Heartbeat` really is already fixed at `agy_runipd.py:43`; `selectors.py` really declares no `__all__`; and the reference counts in F-5 are accurate. THE ONE MATERIAL DEFECT (PR-201, HIGH, fixed): the plan told the executor to delete `Palette`/`_strip_ansi`/`_one_line` from `agy_runipd.py` but never mentioned that all four MODULE-LEVEL CONSTANTS those bodies close over (`_ANSI_RESET`, `_ANSI_CODES`, `_ANSI_STRIP_RE`, `_STATUS_COLOR`) are ALSO duplicated in agy and are ALSO AST-identical to `render_stream`'s - and that `_STATUS_COLOR` has a live non-`Palette` caller at `agy_runipd.py:3797`. Deleting the three functions while leaving four stale identical constants behind would leave the SAME defect class the plan exists to remove, one layer down, and `oc_runipd.py:64-68` already imports exactly those four from `render_stream`, so the precedent the plan cites already answers it. E-02 now covers them and V-02 requires the evidence. Also FIXED: (PR-202, MEDIUM) `_read_id`/`_read_status` are NOT behaviorally interchangeable with `selectors`', despite being AST-identical: they close over DIFFERENT regexes (`selectors._ID_RE` requires exactly one space after `-`, the runners' `_ID_RE` allows `\s*`), so the swap E-03 orders is a real behavior change on `-  Id:` and `-\tId:` input, measured live. The plan's "AST-identical means behavior-neutral" reasoning is sound for the render trio and UNSOUND here; E-03 now requires the regex question be settled first, and the plan no longer claims neutrality it does not have. (PR-203, MEDIUM) E-04 says to fold in "ten oc-side names" but the guard contains NINE `assertNotIn` calls; the table must be built by reading the file, not from this count. (PR-204, LOW) the guard E-01 replaces is in `tests/test_render_stream.py`, which another session committed today (`a396cb1b`), so F-8's contention warning applies to the file E-04 must EDIT, not only to the modules. Two decisions recorded in the typed review record (D-1, D-2; both reversible).
- 2026-09-03 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored FROM E-01's inventory (research `tvnq50`), as orchestrator `5e4sb6`'s SECOND GATE requires ("the children do not exist and must be authored FROM E-01's inventory, not before it. A reviewer should refuse any child plan whose scope was written without the measurement behind it"). RE-SCOPED against the orchestrator's own child table, which is now stale in two ways: it names FOUR re-forks (`Palette`/`_one_line`/`_strip_ansi`/`Heartbeat`), but `Heartbeat` was fixed while the orchestrator sat, and the repo-wide sweep found TWO the table never named (`_read_id`, `_read_status`, owned by `selectors.py`, re-forked in BOTH runners rather than only agy). So the real list is five, and one of the two new ones makes this plan touch `oc_runipd` as well, which the table assumed it would not. Authored review-ready, not draft.
- 2026-09-03 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make each of these five symbols have exactly ONE definition in the package, and make the guard that enforces it cover BOTH runners, so the `Heartbeat` failure mode cannot recur silently in either direction.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the guard is missing before relying on it

- [x] E-01 Write the SYMMETRIC anti-re-fork guard FIRST, in a new `tests/test_runner_refork_guard.py`, and prove it FAILS at current HEAD. It must assert, for BOTH `oc_runipd` and `agy_runipd` and for every symbol in a declared table, that (a) the runner's source does NOT contain a top-level definition of that symbol, and (b) the runner's attribute IS the owning module's object (`assertIs`), which is the check that catches a copy that is textually different but semantically stale. Drive it from a DATA table of `(symbol, owning module)` pairs, not from repeated hand-written assertions, because the existing one-sided guard's ten hand-written `assertNotIn` lines are precisely why adding a symbol did not extend the guarantee. Use AST parsing to find top-level definitions, NOT substring matching: `assertNotIn("class Palette:", src)` also matches a comment or a docstring and misses `class Palette (object):`.
  - Depends on: none
  - Expected outcome: a new test that FAILS at HEAD naming all five re-forks (3 agy-side, 2 in both runners), and that would also fail if `Heartbeat` regressed. Paste the failure.
  - Execution state: performed
  - Execution note: `tests/test_runner_refork_guard.py` added, table-driven from `REFORK_TABLE` (17 rows of an `Owned` NamedTuple), AST-based via `top_level_definitions()` which walks `ast.parse(...).body` and counts `FunctionDef`/`AsyncFunctionDef`/`ClassDef`/`Assign`/`AnnAssign` (so a re-forked CONSTANT counts, and an `import` deliberately does not). It failed at pre-change HEAD `76c83c8c` naming ELEVEN re-forked definitions, which is the plan's five symbols expanded to their true closure: 7 in agy (4 ANSI constants + `Palette`/`_strip_ansi`/`_one_line`) and `_read_id`/`_read_status` in BOTH runners. ONE DESIGN ADDITION the plan did not anticipate: the table needed a `runner_name` column, because the runners bind `selectors`' readers under DIFFERENT names (`_read_id` locally vs the public alias on the owner), so a single-name table would have silently failed to detect those four re-forks at all. The AST half now forbids EITHER spelling and the identity half checks the name the call sites actually use.

### Task group 2: delete the re-forks

- [x] E-02 Delete the three render-layer re-forks from `agy_runipd.py` (`Palette` at `:262`, `_strip_ansi` at `:284`, `_one_line` at `:288`) and import them from `render_stream` instead. The import already exists at `agy_runipd.py:45` (`from agent_workflows.render_stream import (...)`), so ADD the three names to it rather than adding a second import statement. Follow the shape `oc_runipd` already uses (`oc_runipd.py:64-102`), including its re-export comment convention, since `Palette` is referenced 11 times in agy and 14 in oc and 6 test files reference it, so the name must stay reachable as `agy_runipd.Palette`.
  DELETE THE FOUR RE-FORKED CONSTANTS TOO (added at review, PR-201). The three bodies CLOSE OVER four module-level constants that are THEMSELVES duplicated in agy and THEMSELVES AST-identical to `render_stream`'s: `_ANSI_RESET` (`agy_runipd.py:215`), `_ANSI_CODES` (`:216`), `_ANSI_STRIP_RE` (`:227`), `_STATUS_COLOR` (`:229`). Verified at review: all four compare AST-identical to `render_stream.py:35`/`:36`/`:47`/`:50`. Deleting only the functions would leave four stale identical copies behind, i.e. the SAME defect class one layer down, and a later fix to the palette's color map would still not reach `aw agy run`. This is not a scope widening but the completion of the same deletion: `oc_runipd.py:64-68` ALREADY imports exactly these four names from `render_stream`, so the precedent this item cites has already answered the question. NOTE `_STATUS_COLOR` has a live caller OUTSIDE the three functions (`agy_runipd.py:3797`), so it must remain reachable as a module attribute after the swap, exactly as `oc_runipd.py:100` keeps it in `__all__`.
  - Depends on: E-01
  - Expected outcome: `agy_runipd` defines none of the three functions and none of the four constants; each of the seven names satisfies `agy_runipd.<name> is render_stream.<name>`; the 11 agy `Palette` call sites and the `_STATUS_COLOR` caller at `:3797` are unchanged and still work; E-01's guard now passes for all seven.
  - Execution state: performed
  - Execution note: All seven deleted; the three names were ADDED to the EXISTING `render_stream` import (now `agy_runipd.py:56-68`), no second import statement introduced. All seven satisfy `is render_stream.<name>`. LINE NUMBERS IN THIS PLAN WERE ALREADY STALE, as F-8 warned: the symbols were at `:232`/`:233`/`:244`/`:246`/`:279`/`:301`/`:305` and the surviving `_STATUS_COLOR` caller at `:3781`, not the cited `:215`-`:229`/`:3797`. Located by name, per the execution contract. AN UNANTICIPATED FINDING that strengthens the plan's case: the duplicate `Palette` was not merely stale, it was a DIFFERENT TYPE, and the type checker reported `"agy_runipd.Palette" is not assignable to "render_stream.Palette"` at four call sites the moment the constants were removed; that mismatch is now gone and `isinstance(agy_runipd.Palette(True), render_stream.Palette)` is True. SEE DECISION 04-2r306y-D2: `should_color` sits inside the deleted block and is a THIRD copy of `term.py:74`'s, but `oc_runipd.py:37-38` records that it deliberately stays local to the caller per the prior extraction's OQ-01, so it was left untouched and is NOT a guard-table row (adding it would have failed the table against oc for a symbol the repo intentionally keeps local).

- [x] E-03 Add public aliases for `_read_id` and `_read_status` in `selectors.py`, then delete the private-name copies from BOTH runners (`oc_runipd.py:2193`/`:2198`, `agy_runipd.py:1362`/`:1367`) and import the public aliases. RESOLVED BY MAINTAINER 2026-09-03 (OQ-01): use public aliases rather than cross-module private imports. The aliases must preserve behavior and introduce no new parsing or selection semantics.
  STOP: THIS ONE IS NOT BEHAVIOR-NEUTRAL, and the plan's general "AST-identical means safe" argument DOES NOT APPLY HERE (found at review, PR-202, and it is the reason this item is riskier than E-02). The two function BODIES are AST-identical, but they close over DIFFERENT module-level regexes, so swapping the definition swaps the behavior. MEASURED at review: `selectors._ID_RE` is `^- Id:\s*([0-9a-z]{6})\s*$` (`selectors.py:110`, exactly ONE space after the dash) while both runners' `_ID_RE` is `^-\s*Id:\s*([0-9a-z]{6})\s*$` (`oc_runipd.py:168`, `agy_runipd.py:197`, ANY whitespace). On input `-  Id: abc123` the runner reader returns `abc123` and the selectors reader returns `None`; same for a tab, and the same divergence holds for `_read_status`. So a literal swap makes both runners STOP recognizing a front-matter bullet written with two spaces or a tab.
  RESOLVE THE REGEX QUESTION BEFORE DELETING ANYTHING, and do not resolve it by widening `selectors._ID_RE`/`_STATUS_RE`: `selectors.py:111-120` carries an explicit PARITY CONSTRAINT warning that `_STATUS_RE`'s exact strictness is a MATCHING-BEHAVIOR CONTRACT (`aw find plans EXECUTED`), that its twin `plans_index._META_RE` deliberately disagrees on 24 records, and that harmonizing them is a contract change and not a cleanup. The acceptable resolutions are: (a) give the new public aliases their OWN permissive pattern matching the runners' current behavior, leaving `selectors`' internal readers untouched; or (b) MEASURE that no real artifact in the tree uses the loose spelling and record that as the basis for accepting the stricter behavior. At review the measurement for (b) came out CLEAN (all 1382 `.md` records under `.aw/records/` yield identical `- Id:` and `- Status:` values under both regexes, 0 disagreements), so (b) is available - but it is a decision about tolerated INPUT, so record whichever you choose and why, and do not present the swap as behavior-preserving if you take (b).
  - Depends on: E-01
  - Expected outcome: neither runner defines either symbol; both resolve to the public `selectors` aliases by `assertIs`; the 2 oc and 3 agy call sites per symbol are unchanged; AND an explicit statement of which regex resolution was taken, with the measurement or the new pattern pasted, plus a test pinning the chosen behavior on `-  Id:` (two spaces) and `-\tId:` (tab) input so the decision cannot be silently reversed later.
  - Execution state: performed
  - Execution note: RESOLUTION TAKEN: ROUTE (a), THE PERMISSIVE ALIAS, so this item IS behavior-preserving for both runners (see DECISION 04-2r306y-D1). Added `selectors.read_front_matter_id` / `read_front_matter_status` with their own `_FRONT_MATTER_ID_RE = re.compile(r"(?m)^-\s*Id:\s*([0-9a-z]{6})\s*$")` and `_FRONT_MATTER_STATUS_RE = re.compile(r"(?m)^-\s*Status:\s*(\S+)\s*$")`, i.e. the runners' own patterns, and bound both runners' historical private names to them. `selectors._ID_RE`/`_STATUS_RE` and the internal readers are BYTE-UNCHANGED, so `aw find` matching is untouched and the parity constraint at `selectors.py:111-119` is honored. Route (b) was genuinely available (I re-ran the measurement: 838 `.md` records under `.aw/records/`, 0 disagreements for both fields) but was NOT taken, for a reason the plan's own measurement did not cover: `status_set.py:132-133`, the module that WRITES these bullets, itself matches on the LOOSE `^-\s*Id:`/`^-\s*Status:`, as do `check_engine.py:1565`/`:1572`, `backlog.py:73-74` and `research_index.py:420` (via `[ \t]*`), so the strict spelling is the outlier rather than the norm, and the failure mode of tightening is SILENT (a `None` status makes `parse_plan_file` fall back to a directory-derived status at `oc_runipd.py:2322-2324`). Four tests in `FrontMatterReaderBehaviorTests` pin both halves of the decision: the runners still accept one-space/two-space/tab, and `selectors`' internal readers still REJECT the loose forms. Note the runners' now-unused `_ID_RE`/`_STATUS_RE` were deliberately left in place: the plan's Scope check assigns those to child 02's class (a) extraction.

### Task group 3: retire the one-sided guard in favour of the symmetric one

- [x] E-04 Fold the existing one-sided guard into the symmetric one and DELETE the superseded assertions rather than leaving both. `tests/test_render_stream.py:539` (`test_oc_runipd_source_has_no_inline_definitions`) and `:554` (`test_agy_runipd_has_no_inline_heartbeat_copy`) are the one-sided pair; their oc-side names and the agy-side `Heartbeat` name must all appear in E-01's data table first, so the guarantee STRICTLY GROWS and nothing is silently dropped. BUILD THAT LIST BY READING THE FILE, not from a count written here: this plan said "ten oc-side names" and the guard actually contains NINE `assertNotIn` calls (measured at review, PR-203), so a table built from the number rather than the source would either drop a name or invent one. Enumerate them mechanically and paste the enumeration. Keep `test_heartbeat_is_the_same_object_in_both_drivers` (`:561`) and `test_exactly_one_heartbeat_definition_in_the_package` (`:565`): the first is already symmetric and the second is a repo-wide check this plan does not replace.
  - Depends on: E-02, E-03
  - Expected outcome: the two one-sided tests are gone, every name they asserted is in the symmetric table, and the coverage difference is stated explicitly (which names are newly guarded, which merely moved).
  - Execution state: performed
  - Execution note: Both one-sided tests deleted from `tests/test_render_stream.py` and replaced by a comment recording why they were retired and where the guarantee now lives. The name list was built MECHANICALLY by parsing the retired functions' `assertNotIn` literals, not from this plan's prose, and F-11 IS ITSELF WRONG IN BOTH DIRECTIONS: the oc-side guard has TEN `assertNotIn` calls (not the nine F-11 claims, nor the ten the plan body claims and F-11 "corrects"), and the agy-side guard covered TWO names (`Heartbeat` AND `statusline_action_for_item`), not `Heartbeat` alone as F-1/F-11 and the Concern both state. Reading the source rather than the count is exactly what the item demanded. Measured coverage delta: 12 (runner, symbol) pairs retired -> 28 covered, 0 DROPPED. `test_heartbeat_is_the_same_object_in_both_drivers` and `test_exactly_one_heartbeat_definition_in_the_package` retained as instructed.

- [x] E-05 Prove the symmetric guard is load-bearing rather than decorative, by SABOTAGE in BOTH directions. Re-insert a copy of one symbol into `oc_runipd`, confirm the guard fails, revert; then do the same in `agy_runipd`, confirm it fails, revert. A guard that has only been observed passing is not evidence, and the one-sided direction is exactly what let `Heartbeat` drift, so the agy direction specifically must be demonstrated.
  - Depends on: E-04
  - Expected outcome: two pasted failures, one per runner, each naming the re-inserted symbol, plus a clean run after both reverts and `git status` showing no residue.
  - Execution state: performed
  - Execution note: Both directions sabotaged and both caught, by BOTH halves of the guard each time. The sabotages were chosen to be adversarial rather than trivial. (1) oc direction: re-inserted `class Palette (object):` - the SPACE-BEFORE-PAREN spelling that F-7 names as the retired substring guard's blind spot. Confirmed in the same run that `"class Palette:" not in src` is True, i.e. the OLD guard would have PASSED this re-fork, while the new AST guard failed with `oc_runipd.py:192 re-defines Palette`. (2) agy direction: re-inserted a DRIFTED `_STATUS_COLOR = {"executed": "blue"}`, the exact historical `Heartbeat` shape and the direction the one-sided guard could never see; caught as both a re-definition and an identity mismatch (`got {'executed': 'blue'}`). Reverts verified by md5 against pre-sabotage checkpoints, `rg SABOTAGE` over `agent_workflows/` and `tests/` returns nothing, and `git status --porcelain` shows only the five in-scope paths.

## Project conventions discovered (Step 0)

- The shared-render precedent is `oc_runipd.py:64-102`: import the names from `render_stream` and re-export them, with a comment recording why (`# Re-exported from render_stream for backward-compatible access via ``oc_runipd``.`). Follow it; do not invent a second pattern.
- `agy_runipd.py:43` already imports `Heartbeat` from `render_stream` with an explanatory comment at `:34` recording that the module "silently did not reach `aw agy run`". That comment is the historical record of this exact defect class and should not be deleted.
- Guards in this repo are expected to be sabotage-verified. `tests/test_render_stream.py:565` already checks "exactly one definition in the package" by walking the package rather than by grep, which is the standard this plan's E-01 follows.
- The orchestrator's hard constraint: a child must land in BOTH runners or neither, and every guard it adds must assert over BOTH runners.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | The guard is ONE-SIDED, and that is the root cause rather than the re-forks themselves. Ten render-layer names are asserted absent from `oc_runipd`; the agy side checks only `Heartbeat`. | `tests/test_render_stream.py:539-552` (oc, ten `assertNotIn`), `:554-560` (agy, `Heartbeat` only) |
| F-2 | THREE render re-forks remain in agy, all AST-identical to the owner, so deleting them cannot change behavior. | `agy_runipd.py:262` `Palette`, `:284` `_strip_ansi`, `:288` `_one_line`; AST-identical to `render_stream`'s, verified per symbol |
| F-3 | TWO re-forks the orchestrator's child table never named, and they sit in BOTH runners, not just agy. This is why this plan's Scope-Paths include `oc_runipd.py`, which the table assumed it would not touch. | `oc_runipd.py:2193`/`:2198` and `agy_runipd.py:1362`/`:1367`, both AST-identical to `selectors.py`'s `_read_id`/`_read_status` |
| F-4 | `Heartbeat` is ALREADY FIXED, so the orchestrator's child table is stale and a literal execution of it would be a no-op plus confusion. | `agy_runipd.py:43`: `from agent_workflows.render_stream import Heartbeat as Heartbeat` |
| F-5 | The names must stay REACHABLE as runner attributes after the move; this is not a pure deletion. `Palette` alone is referenced 11 times in agy, 14 in oc, and by 6 test files. | `rg -c` per symbol: `Palette` 11/14, `_strip_ansi` 1/2, `_one_line` 3/2, `_read_id` 2/2, `_read_status` 3/3 |
| F-6 | HAZARD for E-03: `_read_id`/`_read_status` are private-by-convention and `selectors.py` declares no `__all__`, so a cross-module private import is legal but couples to another module's internals. | `rg -c "^__all__" agent_workflows/selectors.py` -> 0 |
| F-7 | Substring guards are weak. The existing one-sided guard uses `assertNotIn("class Palette:", src)`, which a comment satisfies and which `class Palette (object):` evades. E-01 therefore uses AST parsing. | `tests/test_render_stream.py:542` |
| F-8 | CONTENTION, live at authoring: another session committed `render_stream.py` and `tests/test_render_stream.py` in `a396cb1b` (progress-bar percentage formatting). Unrelated to this work, but both files are in this plan's blast radius. NOTE ADDED AT REVIEW (PR-204): `tests/test_render_stream.py` is not merely in the blast radius, it is a file E-04 must EDIT (it holds the one-sided guard being folded in), so re-read it immediately before that edit rather than trusting the line numbers here. | `git log --oneline -1 a396cb1b`; `tests/test_render_stream.py:539`, `:554` |
| F-9 | **FOUND AT REVIEW (PR-201), and it changes E-02's deletion list from three names to seven.** The three render functions close over FOUR module-level constants that are themselves re-forked in agy and themselves AST-identical to `render_stream`'s. Deleting the functions alone would leave the identical defect one layer down. `oc_runipd` already imports exactly these four, so the fix is the cited precedent, not a widening. `_STATUS_COLOR` additionally has a caller outside the three functions, so it must stay reachable. | `agy_runipd.py:215` `_ANSI_RESET`, `:216` `_ANSI_CODES`, `:227` `_ANSI_STRIP_RE`, `:229` `_STATUS_COLOR`, all AST-identical to `render_stream.py:35`/`:36`/`:47`/`:50`; live caller at `agy_runipd.py:3797`; precedent `oc_runipd.py:64-68` and `__all__` at `:97-100` |
| F-10 | **FOUND AT REVIEW (PR-202). The single genuine BEHAVIOR RISK in this plan, and it is invisible to the AST test the plan relies on.** `_read_id`/`_read_status` have AST-identical BODIES but close over DIFFERENT regexes, so E-03's swap changes what front-matter spellings the runners accept. Measured live: on `-  Id: abc123` (two spaces) the runner reader returns `abc123` and the `selectors` reader returns `None`; same for a tab; same for `- Status:`. So "AST-identical, therefore behavior-neutral" is TRUE for the render trio and FALSE here. Mitigating measurement, also at review: across all 1382 `.md` records under `.aw/records/`, both regex pairs agree on every file (0 disagreements), so no artifact in the tree currently depends on the loose spelling. | `selectors.py:110` vs `oc_runipd.py:168` and `agy_runipd.py:197`; `selectors.py:120` vs `:169`/`:198`; the parity-constraint warning at `selectors.py:111-119`; live comparison over `.aw/records/**/*.md` |
| F-11 | The guard fold's own count was wrong in this plan: it says "ten oc-side names", the guard has NINE `assertNotIn` calls plus one positive `assertIn`. Small, but it is exactly the kind of number an executor would use to build the table instead of reading the source. | `tests/test_render_stream.py:539-552`, counted mechanically: 9 `assertNotIn` |
| F-12 | **FOUND AT EXECUTION. F-11 IS ITSELF WRONG, and so are F-1 and the Concern, in the opposite direction.** Counted mechanically by parsing the retired functions' `assertNotIn` literals at HEAD `76c83c8c`: the oc-side guard has **TEN** `assertNotIn` calls (the plan body's "ten" was right and F-11's "nine correction" was wrong), and the agy-side guard covers **TWO** names, `Heartbeat` AND `statusline_action_for_item`, not `Heartbeat` alone as F-1, F-11 and the Concern all assert. This does not change the plan's conclusion (the guard was still radically one-sided, 10 vs 2) but it is why E-04 insisted on enumerating from the source: three separate places in this plan state the count, and two of them are wrong. | `tests/test_render_stream.py:551-573` parsed with `ast`, 10 + 2 `assertNotIn`; enumeration pasted in V-04 |
| F-13 | **FOUND AT EXECUTION, and it materially changed E-01's design.** The guard table needs a RUNNER-LOCAL NAME column, which the plan did not anticipate. A runner does not always bind an owner's symbol under the owner's name: both runners call the readers as `_read_id`/`_read_status` while `selectors` exposes them publicly, so a single-name table would have looked for `read_front_matter_id` in the runners, found nothing, and PASSED while all four re-forks were still present. The AST half now forbids either spelling and the identity half checks the locally-used name. | `Owned.runner_name`/`.forbidden` in `tests/test_runner_refork_guard.py`; the 4 reader rows in V-01's failure output |
| F-14 | **FOUND AT EXECUTION. The re-forked `Palette` was not merely stale, it was a DIFFERENT TYPE, which is stronger evidence for this plan than anything in the original findings.** Removing the four ANSI constants made the type checker immediately report `Argument of type "Palette" cannot be assigned to parameter "pal" of type "Palette"` at four live agy call sites, spelling out `"agy_runipd.Palette" is not assignable to "render_stream.Palette"`. So agy was passing its own incompatible class into shared `render_stream` functions; it worked only by duck typing. After the swap `isinstance(agy_runipd.Palette(True), render_stream.Palette)` is True. | type-checker output on the intermediate edit; `agy_runipd.py` call sites at `:2829`, `:4219`, `:4327`, `:4763` (pre-edit numbering) |
| F-16 | The `pre-commit` `ruff` hook CAUGHT A REAL DEFECT in my first commit attempt and is recorded rather than quietly fixed: I had placed the two `selectors` import statements next to the deleted functions mid-file, which is `E402 module level import not at top of file` (4 errors, 2 per runner). Moved both pairs into each module's top-of-file import block, re-verified the identity bindings and the whitespace tolerance, and re-ran the full suite (same result, zero new failures). Also confirmed after the failed hook that the index still held ONLY my five paths, per the shared-checkout contract. | first attempt: `agy_runipd.py:1345-1346`, `oc_runipd.py:2200-2201`; after the move `ruff check --select E402,E9,F` -> `All checks passed!`; commit `637c6f8a` passed all hooks |
| F-15 | The runners' `_ID_RE`/`_STATUS_RE` are now DEAD CODE (their only readers were the deleted `_read_id`/`_read_status`), but they were deliberately LEFT IN PLACE: they are class (a) COMMON constants that this plan's own Scope check assigns to child 02. Recorded so their survival is not mistaken for an oversight, and so child 02 knows they are now unreferenced and can simply be deleted rather than extracted. | `oc_runipd.py:171-172`, `agy_runipd.py:232-233`; `rg "_ID_RE\|_STATUS_RE"` on both runners shows definitions with no remaining uses |

## Proposed changes (ordered, validatable)

1. Add the symmetric, AST-based, table-driven re-fork guard and prove it fails at HEAD (E-01).
2. Delete the three agy render re-forks AND the four re-forked ANSI constants they close over; extend the existing `render_stream` import (E-02).
3. Settle the regex-behavior question, then delete `_read_id`/`_read_status` from both runners and import the public `selectors` aliases (E-03).
4. Fold the one-sided guards into the symmetric table and delete them, growing coverage strictly (E-04).
5. Sabotage-verify the guard in both directions (E-05).

## Deferred / out of scope (with reason)

- The class (a) COMMON extraction (34 symbols): that is child 02, and it needs a new shared module, which this plan deliberately does not create.
- Every class (c) DIVERGED symbol: gated behind `lanectn` landing AND E-02's characterization baseline, per the orchestrator's re-pointed sequencing gate.
- `Heartbeat`: already fixed (F-4). Not re-fixed here; only folded into the symmetric guard so it cannot regress.
- Changing `render_stream` or `selectors` behavior; E-03 may add only the two public aliases chosen by the maintainer.
- The 40 names `agy_runipd` imports FROM `oc_runipd`. This is a genuine structural finding of E-01 (the runners are not peers; agy already depends on oc), but re-homing them is a shared-module design question for child 02 and beyond, not a re-fork deletion. Recorded so it is not mistaken for part of this slice.

## Scope check

- Over-scope: none. Every edit deletes a duplicate definition or strengthens the guard that prevents it. The four ANSI constants added to E-02 at review are not a widening: they are the closure of the same three deletions, and `oc_runipd` already imports them from the same owner.
- Under-scope: this plan does not reduce the runners' line counts materially (the five symbols are ~40 lines total). Its value is the GUARD, not the deletion: without a symmetric guard the next extraction re-forks again, which is F-1's whole point.
- Under-scope, RECORDED AT REVIEW: this plan does not unify the runners' OWN copies of `_ID_RE`/`_STATUS_RE`/`_SET_RE`/`_ORDER_RE`/`ID6_RE`/`SCHEMA_VERSION`/`_PLAN_FILENAME_RE`, all of which are duplicated between the two runners and AST-identical (measured at review). They are class (a) COMMON constants and belong to child 02's extraction, not to a re-fork deletion. Named here so the next reader does not mistake their survival for an oversight.

## Required tests / validation

- The new symmetric guard, demonstrated FAILING at HEAD and passing after, plus sabotage in both runner directions (E-05).
- `python3 -m pytest tests/test_render_stream.py tests/test_runner_refork_guard.py` green, with counts.
- Both driver suites green: `tests/test_oc_runipd.py` (93 tests at authoring) and `tests/test_agy_runipd_cli.py` (20).
- Full suite bare (`python3 -m pytest`), compared against YOUR OWN pre-change measurement, not a number written here. Baseline at authoring HEAD `c8bb11ae`: `4092 passed, 3 skipped, 4 xfailed`. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`.
- An `assertIs` check per symbol, since object identity is what proves the runner sees the owner's definition rather than an equal-looking copy.

## Spec / documentation sync

- No spec governs the render layer's ownership, and no DOCUMENTED public contract changes: every affected name remains reachable at its existing runner attribute path (F-5).
- CORRECTED AT REVIEW: the blanket "changes no public contract" was too strong. E-03 can change what front-matter spellings the runners ACCEPT (F-10), which is an input-tolerance contract even though no document states it. If E-03 takes the stricter `selectors` behavior, record that decision in `selectors.py` beside the existing parity-constraint comment at `:111-119`, which is where this repo already documents exactly this class of matching-behavior decision. If it takes the permissive-alias route, no doc change is needed.

## Open questions

### OQ-01: For `_read_id`/`_read_status`, import the private names or add a public alias to `selectors`?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-03: add public aliases in `selectors.py` and import those aliases from both runners. This documents the cross-module API rather than coupling the runners to private names. `selectors.py` is included in Scope-Paths solely for those behavior-preserving aliases.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the new guard FAILING at pre-change HEAD, with the failure naming all five re-forked symbols and identifying which runner each is in. Paste the data table itself, showing it is a table rather than repeated assertions, and show the definition check is AST-based (paste the parsing code, not a grep). A guard never observed failing is not accepted as evidence.
  - Observed evidence: Measured at pre-change HEAD `76c83c8c11760f892056ffce15b9f387101bbb31`, tree carrying only the new test file.

    THE GUARD FAILING AT HEAD, naming all eleven re-forked definitions (the plan's five symbols, expanded to their real closure) and which runner each is in:

    ```
    $ python3 -m pytest -o addopts="" tests/test_runner_refork_guard.py
    E       AssertionError: Lists differ: ['agy_runipd.py:232 re-defines `_ANSI_RESE[1099 chars]us`'] != []
    E       Diff is 1250 characters long. ... : RE-FORK(S) FOUND. Import the symbol from its owning module instead of defining a second copy; a fix to the owner does not reach a copy.
    E         agy_runipd.py:232 re-defines `_ANSI_RESET`, which `render_stream.py` already owns as `_ANSI_RESET`
    E         agy_runipd.py:233 re-defines `_ANSI_CODES`, which `render_stream.py` already owns as `_ANSI_CODES`
    E         agy_runipd.py:244 re-defines `_ANSI_STRIP_RE`, which `render_stream.py` already owns as `_ANSI_STRIP_RE`
    E         agy_runipd.py:246 re-defines `_STATUS_COLOR`, which `render_stream.py` already owns as `_STATUS_COLOR`
    E         agy_runipd.py:279 re-defines `Palette`, which `render_stream.py` already owns as `Palette`
    E         agy_runipd.py:305 re-defines `_one_line`, which `render_stream.py` already owns as `_one_line`
    E         agy_runipd.py:301 re-defines `_strip_ansi`, which `render_stream.py` already owns as `_strip_ansi`
    E         oc_runipd.py:2196 re-defines `_read_id`, which `selectors.py` already owns as `read_front_matter_id`
    E         agy_runipd.py:1379 re-defines `_read_id`, which `selectors.py` already owns as `read_front_matter_id`
    E         oc_runipd.py:2201 re-defines `_read_status`, which `selectors.py` already owns as `read_front_matter_status`
    E         agy_runipd.py:1384 re-defines `_read_status`, which `selectors.py` already owns as `read_front_matter_status`
    ========================= 3 failed, 2 passed in 0.41s ==========================
    ```

    IT IS A DATA TABLE, not repeated assertions (`tests/test_runner_refork_guard.py`), 17 rows driving all assertions:

    ```python
    class Owned(NamedTuple):
        symbol: str
        owner: str
        runners: tuple[str, ...]
        runner_name: str | None = None

    REFORK_TABLE: tuple[Owned, ...] = (
        Owned("_ANSI_RESET", "render_stream", BOTH),
        ...
        Owned("read_front_matter_id", "selectors", BOTH, runner_name="_read_id"),
        Owned("read_front_matter_status", "selectors", BOTH, runner_name="_read_status"),
    )
    ```

    THE DEFINITION CHECK IS AST-BASED, not a grep:

    ```python
    def top_level_definitions(module) -> dict[str, int]:
        source = module_source(module)
        found: dict[str, int] = {}
        for node in ast.parse(source).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                found.setdefault(node.name, node.lineno)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        found.setdefault(target.id, node.lineno)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                found.setdefault(node.target.id, node.lineno)
        return found
    ```

    A `Heartbeat` regression would also fail: it is row `Owned("Heartbeat", "render_stream", BOTH)`, and E-05's agy sabotage demonstrates that exact detection on a sibling symbol.

    INDEPENDENT AST-IDENTITY MEASUREMENT confirming every deletion was behavior-neutral (comparing `ast.dump(ast.parse(ast.unparse(node)))` per symbol, the method the plan specifies):

    ```
    _ANSI_RESET      agy_line=  232 rs_line=   35 AST-identical=True
    _ANSI_CODES      agy_line=  233 rs_line=   36 AST-identical=True
    _ANSI_STRIP_RE   agy_line=  244 rs_line=   47 AST-identical=True
    _STATUS_COLOR    agy_line=  246 rs_line=   50 AST-identical=True
    Palette          agy_line=  279 rs_line=   70 AST-identical=True
    _strip_ansi      agy_line=  301 rs_line=   92 AST-identical=True
    _one_line        agy_line=  305 rs_line=   96 AST-identical=True
    _read_id       oc   line=2196 sel_line=239 AST-identical=True
    _read_id       agy  line=1379 sel_line=239 AST-identical=True
    _read_status   oc   line=2201 sel_line=244 AST-identical=True
    _read_status   agy  line=1384 sel_line=244 AST-identical=True
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `rg -n "^class Palette|^def _strip_ansi|^def _one_line" agent_workflows/agy_runipd.py` returning NOTHING. Paste `agy_runipd.Palette is render_stream.Palette` (and the same for the other two) evaluating True. Paste the amended import statement showing the three names were ADDED to the existing `render_stream` import at `agy_runipd.py:45` rather than a second import being introduced. Confirm the 11 agy `Palette` call sites are untouched by pasting the count before and after.
  ALSO REQUIRED (PR-201): paste `rg -n "^_ANSI_RESET|^_ANSI_CODES|^_ANSI_STRIP_RE|^_STATUS_COLOR" agent_workflows/agy_runipd.py` returning NOTHING, and paste the four `is render_stream.<name>` identity checks evaluating True. Then paste evidence the surviving caller still works: `_STATUS_COLOR` is used at `agy_runipd.py:3797` outside the three moved functions, so exercise that path (or the test covering it) and paste the result. Leaving the four constants behind FAILS this item, because that reproduces the very defect class the plan removes.
  - Observed evidence: All seven deletions and all seven identity bindings verified.

    NO DEFINITION REMAINS for any of the seven (functions and constants in one command; both required greps, returning nothing):

    ```
    $ rg -n "^class Palette|^def _strip_ansi|^def _one_line|^_ANSI_RESET|^_ANSI_CODES|^_ANSI_STRIP_RE|^_STATUS_COLOR" agent_workflows/agy_runipd.py
    (no output; exit 1)
    ```

    ALL SEVEN IDENTITY CHECKS True (this is the proof, not the grep):

    ```
    agy_runipd.Palette          is render_stream.Palette          -> True
    agy_runipd._strip_ansi      is render_stream._strip_ansi      -> True
    agy_runipd._one_line        is render_stream._one_line        -> True
    agy_runipd._ANSI_RESET      is render_stream._ANSI_RESET      -> True
    agy_runipd._ANSI_CODES      is render_stream._ANSI_CODES      -> True
    agy_runipd._ANSI_STRIP_RE   is render_stream._ANSI_STRIP_RE   -> True
    agy_runipd._STATUS_COLOR    is render_stream._STATUS_COLOR    -> True
    ```

    THE EXISTING IMPORT WAS EXTENDED, not duplicated (`agy_runipd.py:56-68`; one statement, seven names added):

    ```python
    from agent_workflows.render_stream import (
        Statusline,
        render_run_summary_table,
        install_exit_signal_handler,
        statusline_action_for_item,
        Palette as Palette,
        _strip_ansi as _strip_ansi,
        _one_line as _one_line,
        _ANSI_RESET as _ANSI_RESET,
        _ANSI_CODES as _ANSI_CODES,
        _ANSI_STRIP_RE as _ANSI_STRIP_RE,
        _STATUS_COLOR as _STATUS_COLOR,
    )
    ```

    CALL SITES UNCHANGED. `rg -c Palette` gives agy 15 / oc 15. NOTE the plan's "11 in agy" is a BEFORE-count of a different quantity: the 11 pre-existing references remain untouched and the count rose to 15 only because the import statement and the two explanatory comment blocks I added mention the name; no call site was edited (`git diff` shows no change to any `Palette(...)` line). Both runners now report the same count, which is itself the symmetry this plan is enforcing.

    THE SURVIVING NON-`Palette` CALLER STILL WORKS. It is at `agy_runipd.py:3781`, not the `:3797` this plan cites (line numbers had already drifted; located by name per the execution contract). Exercised that exact expression form (`_STATUS_COLOR.get(disposition, "yellow")`):

    ```
    executed         -> color 'green'    status()='\x1b[32mexecuted\x1b[0m'
    partial          -> color 'yellow'   status()='\x1b[33mpartial\x1b[0m'
    failed-safely    -> color 'red'      status()='\x1b[31mfailed-safely\x1b[0m'
    merge-conflict   -> color 'red'      status()='\x1b[31mmerge-conflict\x1b[0m'
    nonesuch         -> color 'yellow'   status()='nonesuch'
    strip: 'x'  one_line: 'a b c'
    cross-module type compat: True
    ```

    The last line matters: BEFORE this change `agy_runipd.Palette` was a DIFFERENT CLASS from `render_stream.Palette`, and removing the constants made the type checker surface it at four real call sites (`Argument of type "Palette" cannot be assigned to parameter "pal" of type "Palette"`). That mismatch is now resolved, which is evidence the re-fork was not merely redundant but actively wrong.

    `tests/test_render_stream.py` (which covers this render layer for both drivers) fully green, and the agy driver suite's failures are byte-identical to the pre-change baseline:

    ```
    $ python3 -m pytest -o addopts="-q" tests/test_agy_runipd_cli.py tests/test_render_stream.py
    6 failed, 51 passed in 3.14s
    $ diff <baseline agy failures> <post-change agy failures>
    IDENTICAL to baseline: no new failure, none fixed
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `rg -n "^def _read_id|^def _read_status" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` returning NOTHING, i.e. BOTH runners, since a one-sided deletion recreates the divergence. Paste `assertIs` results tying both names in both runners to `selectors`' definitions. Paste the public `selectors` aliases and the `assertIs` results tying both runner names to them.
  THE REGEX EVIDENCE IS MANDATORY AND IS THE POINT OF THIS ITEM (PR-202): identity assertions alone do NOT satisfy it, because the bodies were always AST-identical while the behavior differed. State which resolution E-03 took, and paste for BOTH readers the result on THREE inputs: `- Id: abc123` (one space), `-  Id: abc123` (two spaces), `-\tId: abc123` (tab), plus the same three for `- Status:`. If you took the permissive-alias route, the loose spellings must still parse. If you took the measured-clean route, paste the measurement over the real tree AND paste the new test that pins the now-stricter behavior, so the tolerated-input decision is recorded in code rather than only in this plan. A pasted `assertIs` with no input-behavior evidence FAILS this item.
  - Observed evidence: **RESOLUTION TAKEN: ROUTE (a), THE PERMISSIVE PUBLIC ALIAS.** Both runners keep their exact prior input tolerance, so this swap IS behavior-preserving; `selectors`' internal readers are byte-unchanged, so `aw find` matching is untouched. Rationale and the rejected alternatives are in DECISION 04-2r306y-D1.

    NEITHER RUNNER DEFINES EITHER SYMBOL (both runners in one command, since a one-sided deletion recreates the divergence):

    ```
    $ rg -n "^def _read_id|^def _read_status" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
    (no output; exit 1)
    ```

    IDENTITY, all four bindings tied to the public `selectors` aliases:

    ```
    oc._read_id      is selectors.read_front_matter_id     -> True
    agy._read_id     is selectors.read_front_matter_id     -> True
    oc._read_status  is selectors.read_front_matter_status -> True
    agy._read_status is selectors.read_front_matter_status -> True
    ```

    THE PUBLIC ALIASES (`selectors.py`), with their own permissive patterns:

    ```python
    _FRONT_MATTER_ID_RE = re.compile(r"(?m)^-\s*Id:\s*([0-9a-z]{6})\s*$")
    _FRONT_MATTER_STATUS_RE = re.compile(r"(?m)^-\s*Status:\s*(\S+)\s*$")

    def read_front_matter_id(text: str) -> str | None:
        m = _FRONT_MATTER_ID_RE.search(text)
        return m.group(1) if m else None

    def read_front_matter_status(text: str) -> str | None:
        m = _FRONT_MATTER_STATUS_RE.search(text)
        return m.group(1) if m else None
    ```

    THE MANDATORY INPUT-BEHAVIOR EVIDENCE, all three spellings, both fields, both readers. The runners' columns are what E-03 must preserve; the strict-internal column is what must NOT change:

    ```
    input        oc._read_id  agy._read_id  PUBLIC alias  strict internal
    one space    abc123       abc123        abc123        abc123
    two spaces   abc123       abc123        abc123        None
    tab          abc123       abc123        abc123        None

    input        oc._read_status  agy._read_status  PUBLIC alias   strict internal
    one space    approved         approved          approved       approved
    two spaces   approved         approved          approved       None
    tab          approved         approved          approved       None
    ```

    The loose spellings STILL PARSE for both runners, as route (a) requires. The `(\S+)` single-token contract is preserved: `read_front_matter_status("- Status: EXECUTED (approved by maintainer)")` -> `None`, matching the internal reader.

    SELECTOR MATCHING PROVABLY UNTOUCHED (the parity constraint at `selectors.py:111-119` is honored):

    ```
    selector matching UNCHANGED: _ID_RE (?m)^- Id:\s*([0-9a-z]{6})\s*$
    selector matching UNCHANGED: _STATUS_RE (?m)^- Status:\s*(\S+)\s*$
    ```

    THE DECISION IS PINNED IN CODE, not only in this plan: `tests/test_runner_refork_guard.py::FrontMatterReaderBehaviorTests` has four tests asserting (i) the public readers tolerate all three spellings, (ii) BOTH runners still accept every spelling they did before, (iii) the internal readers stay strict AND both patterns are literally unchanged, and (iv) the single-token status contract holds. So a later "harmonization" in either direction fails a test.

    Route (b)'s measurement, re-run independently (it was available; I did not take it):

    ```
    records scanned: 838
    - Id: disagreements strict vs loose : 0
    - Status: disagreements strict vs loose: 0
    ```

    `tests/test_selector_zero_open.py`, which pins the `_STATUS_RE` parity contract, is green (80 passed with the render + guard suites).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `rg -n "test_oc_runipd_source_has_no_inline_definitions|test_agy_runipd_has_no_inline_heartbeat_copy" tests/` returning NOTHING. Paste the MECHANICAL enumeration of the names the retired guard asserted (read from the file, not from this plan's prose, which said ten where the source has nine) beside the new symmetric table, showing every enumerated name is present, so coverage strictly grew. State which names are NEWLY guarded on the agy side versus merely relocated, so the growth is auditable rather than asserted. Paste `tests/test_render_stream.py` still green, and confirm `test_heartbeat_is_the_same_object_in_both_drivers` and `test_exactly_one_heartbeat_definition_in_the_package` were retained.
  - Observed evidence: The one-sided pair is gone, nothing was dropped, and coverage grew from 12 to 28 (runner, symbol) pairs.

    ```
    $ rg -n "def test_oc_runipd_source_has_no_inline_definitions|def test_agy_runipd_has_no_inline_heartbeat_copy" tests/
    (no output; exit 1)
    ```

    MECHANICAL ENUMERATION, parsed from the retired functions' `assertNotIn` literals rather than read from prose. **THIS PLAN'S OWN COUNTS WERE WRONG IN BOTH DIRECTIONS, which is exactly why the item demanded reading the source:** the oc-side guard had TEN `assertNotIn` calls (F-11 claims nine), and the agy-side guard covered TWO names, not `Heartbeat` alone as F-1, F-11 and the Concern all state:

    ```
    RETIRED guards asserted 12 (runner, symbol) pairs:
      agy_runipd  Heartbeat                    from 'class Heartbeat:'                 -> in new table: True
      agy_runipd  statusline_action_for_item   from 'def statusline_action_for_item('  -> in new table: True
      oc_runipd   Heartbeat                    from 'class Heartbeat:'                 -> in new table: True
      oc_runipd   Palette                      from 'class Palette:'                   -> in new table: True
      oc_runipd   Statusline                   from 'class Statusline:'                -> in new table: True
      oc_runipd   StreamTracker                from 'class StreamTracker:'             -> in new table: True
      oc_runipd   _one_line                    from 'def _one_line('                   -> in new table: True
      oc_runipd   _strip_ansi                  from 'def _strip_ansi('                 -> in new table: True
      oc_runipd   format_statusline            from 'def format_statusline('           -> in new table: True
      oc_runipd   format_tokens                from 'def format_tokens('               -> in new table: True
      oc_runipd   render_event                 from 'def render_event('                -> in new table: True
      oc_runipd   statusline_action_for_item   from 'def statusline_action_for_item('  -> in new table: True

    DROPPED (must be empty): []

    NEW table covers 28 (runner, symbol) pairs.
    ```

    NEWLY GUARDED vs MERELY RELOCATED, so the growth is auditable. The 12 pairs above merely RELOCATED. These 16 are NEW (10 of them agy-side, which is the one-sidedness this plan exists to fix):

    ```
    NEWLY guarded (not in the retired guards) = 16:
      agy_runipd  Palette                     agy_runipd  read_front_matter_id
      agy_runipd  Statusline                  agy_runipd  read_front_matter_status
      agy_runipd  _ANSI_CODES                 oc_runipd   _ANSI_CODES
      agy_runipd  _ANSI_RESET                 oc_runipd   _ANSI_RESET
      agy_runipd  _ANSI_STRIP_RE              oc_runipd   _ANSI_STRIP_RE
      agy_runipd  _STATUS_COLOR               oc_runipd   _STATUS_COLOR
      agy_runipd  _one_line                   oc_runipd   read_front_matter_id
      agy_runipd  _strip_ansi                 oc_runipd   read_front_matter_status
    ```

    Additionally, every relocated pair gained the IDENTITY half it never had (only `Heartbeat` and the three `statusline_action_for_item`-adjacent names had an `assertIs` before), and the definition half moved from substring matching to AST parsing.

    RETAINED as instructed:

    ```
    $ rg -n "def test_heartbeat_is_the_same_object_in_both_drivers|def test_exactly_one_heartbeat_definition_in_the_package" tests/
    tests/test_render_stream.py:562:    def test_heartbeat_is_the_same_object_in_both_drivers(self):
    tests/test_render_stream.py:566:    def test_exactly_one_heartbeat_definition_in_the_package(self):
    ```

    Both suites green:

    ```
    $ python3 -m pytest -o addopts="-q" tests/test_render_stream.py tests/test_runner_refork_guard.py
    44 passed in 0.79s
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: TWO pasted failures from deliberate sabotage, one per runner, each naming the re-inserted symbol; then the guard green after both reverts; then `git status --porcelain` showing no sabotage residue. Also paste both driver suites and the full bare suite with counts, compared against your own pre-change measurement.
  - Observed evidence: Both directions sabotaged, both caught by both halves of the guard, both reverted cleanly.

    SABOTAGE 1, oc DIRECTION. Re-inserted `class Palette (object):` deliberately using the space-before-paren spelling F-7 identifies as the retired substring guard's blind spot, to show the new guard is strictly stronger and not merely relocated:

    ```
    --- old-style substring guard would have MISSED it:
    assertNotIn("class Palette:") would PASS -> True
    --- the new AST guard:
    E       AssertionError: Lists differ: ['oc_runipd.py:192 re-defines `Palette`, w[46 chars]te`'] != []
    E         oc_runipd.py:192 re-defines `Palette`, which `render_stream.py` already owns as `Palette`
    E       AssertionError: Lists differ: ["oc_runipd.Palette is NOT `render_stream.[86 chars]pd)"] != []
    E         oc_runipd.Palette is NOT `render_stream.Palette` (got <class 'agent_workflows.oc_runipd.Palette'> from agent_workflows.oc_runipd)
    ========================= 2 failed, 7 passed in 0.49s ==========================
    ```

    Reverted and verified by checksum, guard green again:

    ```
    $ md5sum -c <<< "dde950dd20435c5154803980daecee6e  agent_workflows/oc_runipd.py"
    agent_workflows/oc_runipd.py: OK
    9 passed in 0.46s
    ```

    SABOTAGE 2, agy DIRECTION (the direction the one-sided guard could never catch, and the one this plan exists for). Re-inserted a DRIFTED `_STATUS_COLOR = {"executed": "blue"}`, i.e. the exact historical `Heartbeat` failure shape rather than an identical copy:

    ```
    E       AssertionError: Lists differ: ['agy_runipd.py:256 re-defines `_STATUS_CO[59 chars]OR`'] != []
    E         agy_runipd.py:256 re-defines `_STATUS_COLOR`, which `render_stream.py` already owns as `_STATUS_COLOR`
    E       AssertionError: Lists differ: ["agy_runipd._STATUS_COLOR is NOT `render_[52 chars] ?)"] != []
    E         agy_runipd._STATUS_COLOR is NOT `render_stream._STATUS_COLOR` (got {'executed': 'blue'} from ?)
    ========================= 2 failed, 7 passed in 0.50s ==========================
    ```

    Reverted, guard green, NO RESIDUE:

    ```
    $ md5sum -c <<< "8e2ac5eb9c0e51d81db2dc1bd1a0aa4d  agent_workflows/agy_runipd.py"
    agent_workflows/agy_runipd.py: OK
    9 passed in 0.47s
    $ rg -n "SABOTAGE" agent_workflows/ tests/
    (no output; exit 1)
    $ git status --porcelain
     M agent_workflows/agy_runipd.py
     M agent_workflows/oc_runipd.py
     M agent_workflows/selectors.py
     M tests/test_render_stream.py
    ?? tests/test_runner_refork_guard.py
    ```

    BOTH DRIVER SUITES (run together with the render/guard/selector suites):

    ```
    $ python3 -m pytest -o addopts="-q -p no:randomly" tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_render_stream.py tests/test_runner_refork_guard.py tests/test_selector_zero_open.py
    13 failed, 178 passed in 12.67s
    ```

    All 13 driver failures are PRE-EXISTING, proved by set comparison against my own pre-change measurement rather than by assertion:

    ```
    === new in driver suites (must be empty) ===
    (empty)
    === all after-failures are baseline failures: ===
    13
    13
    ```

    FULL BARE SUITE, compared against MY OWN pre-change measurement at HEAD `76c83c8c` (NOT the plan's authoring-time `4092 passed`, which is stale; this tree has 33 pre-existing failures, all lifecycle-role/worktree/run-viewer tests unrelated to this plan):

    ```
    BEFORE (my measurement, pre-change, same HEAD):  33 failed, 4214 passed, 3 skipped, 4 xfailed in 46.17s
    AFTER  (all five files changed):                 32 failed, 4222 passed, 3 skipped, 4 xfailed in 29.77s

    NEW failures: (none)
    baseline-only: tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130
    ```

    ZERO NEW FAILURES; +8 passed (the new guard file). The one baseline failure absent from the after-run is a LOAD-ORDER FLAKE, NOT A FIX BY THIS PLAN, and I verified that rather than claiming credit: it passes 3/3 in isolation both WITH my changes and with my changes stashed away (`git stash push -u` of exactly my five paths, then popped, work intact). Run bare per the contract: no `-n0`, no second `-q`, no `-p no:randomly` (the `-o addopts` and `-p no:randomly` forms above are only for the narrowed per-file runs the plan asks to be reported with counts).

    Additional checks: `aw sanitize --agent` -> `{"outcome":"clean","exit":0,"findings":0}`; `aw ipd lint` -> `approved plan 20260903-rununify-01-2r306y [blocking] conforming`; `ruff check --select E9,F` clean on all five paths and `ruff format` applied.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 5 E-leaves across 3 task groups, under the thresholds. One concern throughout: give each already-extracted symbol a single definition and make the guard that enforces it symmetric.

Open questions: none. OQ-01 was resolved by the maintainer 2026-09-03: add public `selectors` aliases. No blocking question remains, so this plan is executable once approved.

This plan is `to-review` and requires explicit human approval before execution.

Scope fence: touch ONLY `agent_workflows/agy_runipd.py`, `agent_workflows/oc_runipd.py`, `agent_workflows/selectors.py`, `tests/test_render_stream.py`, and the new `tests/test_runner_refork_guard.py`. Do NOT change `render_stream.py` at all. `selectors.py` may receive only the two public aliases required by resolved OQ-01, plus (if E-03 takes the measured-clean route) a comment recording the tolerated-input decision beside the existing parity-constraint note at `:111-119`. Do NOT widen `selectors._ID_RE` or `selectors._STATUS_RE`: that comment documents their strictness as a MATCHING-BEHAVIOR CONTRACT affecting `aw find`, and harmonizing them is a separate contract change this plan does not own. Do NOT create the shared runner module (that is child 02). Do NOT touch any class (c) diverged symbol. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt). Do NOT edit a sibling plan or the orchestrator, and do NOT reimplement a rule another plan owns.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Do NOT claim a de-duplication on the strength of a grep: the identity assertions are the proof. Do NOT describe this plan as reducing duplication materially; it removes ~40 lines plus four constants and installs the guard that stops the next re-fork, which is the real deliverable. AND DO NOT CALL E-03 BEHAVIOR-PRESERVING unless you took the permissive-alias route: F-10 measured that the swap changes which front-matter spellings parse, so claiming neutrality for the stricter route would be exactly the false claim this rule exists to prevent.

Execution contract: RE-READ both runner modules immediately before editing and locate every symbol BY NAME, not by the line numbers in this plan: another session committed `render_stream.py` and `tests/test_render_stream.py` in `a396cb1b` while this plan was being authored, and the runners are the highest-contention files in the repo. Commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
