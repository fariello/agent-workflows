# IPD: honor the operator's typed run order and announce every reordering

- Date: 2026-09-03
- Kind: child
- Concern: `aw oc run A B` silently executes B first. The operator's typed sequence IS recorded (as `position`) and is then discarded at dispatch: `queue_sort_key` (`oc_runipd.py:3614`) returns `(dependency_depth, setid, order, id6, position)`, so with two independent plans in different Sets the depths tie at 0 and `setid` decides ALPHABETICALLY. Measured from run `run-20260901T042331Z-118022`: the maintainer typed `aw oc run m73aet 6lu3rq`, the queue was built correctly (`position 1 m73aet` / `position 2 6lu3rq`), and `events.jsonl` shows `6lu3rq` started at 04:23:31 and `m73aet` at 04:44:10, because `"runmixed" < "runtrail"`. Nothing announced the inversion; the only way to discover it was to compare `events.jsonl` timestamps against `state.json` positions after the fact. This is a CORRECTNESS bug rather than a cosmetic one because a documented prerequisite ordering exists TODAY: `wlxkoz`'s review requires `m73aet` to land first (4 of its 13 `RUN-*` codes need the commit trailers `m73aet` adds), and `aw oc run m73aet wlxkoz` would silently invert it since `"runcodes" < "runtrail"`.
- Scope: Make the typed order authoritative among equally-ready nodes, and make EVERY divergence between the expressed order and the executed order LOUD. Two inseparable parts per the maintainer's ruling: (A) move `position` above `setid` in the single shared `queue_sort_key`, keeping `dependency_depth` FIRST so a declared edge always beats a typed sequence; (B) announce the execution order at queue build unconditionally, and warn distinctly when it differs from the expressed order, naming both orders and the specific causing edge per moved item. Also fixes the misleading preview and amends the spec rule this changes. Excludes any change to dependency SEMANTICS (a declared edge must keep winning), excludes making `position` mutable, and excludes prompting from anywhere a child process can inherit a TTY.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/render_stream.py, tests/test_runner_item_dependencies.py, tests/test_run_order_announcement.py, .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: runorder
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: prpipy
- Approval: 2026-09-04, recorded via aw ipd set: status set to approved
- Blocks-Release: next
- From-Backlog: xvx8ez

## Workflow history
- 2026-09-04 approved (aw set): status set to approved

- 2026-09-03 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-101..PR-105; GO - PENDING HUMAN APPROVAL. Verified at HEAD `25d3f0b0`, tree clean, plan committed and unchanged, so the pre-review snapshot was correctly skipped. `aw ipd lint --phase author` conforming before and `--phase review-finalize` conforming after. The plan's central claim RE-MEASURED AND TRUE, not taken on trust: `queue_sort_key` at `oc_runipd.py:3596` really does return `(dependency_depth, setid, order, id6, position)`; `agy_runipd.queue_sort_key is oc_runipd.queue_sort_key` is True at this HEAD; and run `run-20260901T042331Z-118022` really does show `selectors ['m73aet','6lu3rq']` with `position 1 m73aet`/`position 2 6lu3rq` in `state.json` while `events.jsonl` has `6lu3rq` `ipd-started` at 04:23:31 and `m73aet` at 04:44:10. THE DOMINANT FINDING (PR-101, HIGH, fixed by maintainer ruling): the plan was ONE-SIDED. The sort-key fix is genuinely shared, but the announcement belongs in `initialize_run` and the preview in `print_status`, and BOTH are separately defined per runner (`agy_runipd.print_status is oc_runipd.print_status` -> False; agy has its own `--prepare-only` at `agy_runipd.py:4691`), while `agy_runipd.py` was NOT in Scope-Paths - so `aw agy run` would have received the corrected ordering and neither the announcement nor the preview fix, which is precisely the one-sided-fix pattern the `rununify` Set exists to remove. MAINTAINER RULED widen to both drivers now, with the message text from ONE shared formatter in `render_stream.py`; added `agy_runipd.py` to Scope-Paths, added E-07, and required both drivers' output as evidence in V-04/V-05. Also FIXED: (PR-102) E-04 said "announce at queue build" without naming the site, and the only correct site is `initialize_run` (`oc_runipd.py:2860`, `agy_runipd.py:1920`) where `position` is assigned at `:2930`/`:1990`; named it, and named the expressed order's actual source (`state["selectors"]`, `initialize_run`'s `queue_ids`), which the plan never identified. (PR-103) the plan asserted the operator's typed order is what `position` records, but `expand_selectors` (`:2519`) expands a SETID or `all` into many positions, so `position` is only the TYPED order for the literal-id6 case; recorded, because E-04's "expressed order" must not claim to be typed when it was expanded. (PR-104) `--prepare-only` renders `state.get("queue")` in stored order (`render_stream.py:903`, `:929`) with no sort, confirming F-5 at the source. (PR-105) V-06 demanded `aw check` clean for the spec file, which is not achievable as stated (the repo carries 13 pre-existing `aw check plans` errors); restated as before/after parity. One decision recorded in the typed review record (D-1, reversible).
- 2026-09-03 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): graduated from backlog `xvx8ez`, which the maintainer had already decided in full on 2026-09-01, so nothing here is a fresh design proposal: the ruling (move `position` above `setid`), its safety argument (`dependency_depth` stays first, so a declared edge still wins), the mandatory second half (announce every reordering loudly), the three implementation traps, and the TTY constraint all come from the item. Authored review-ready, not draft. FOUR THINGS RE-VERIFIED OR FOUND AT AUTHORING rather than trusted from the item. (1) `agy_runipd.queue_sort_key IS oc_runipd.queue_sort_key` confirmed True at this HEAD, so one edit covers both drivers. (2) An EXISTING TEST WILL INVERT: `test_set_order_still_breaks_ties_among_equally_ready_nodes` (`tests/test_runner_item_dependencies.py:745`) builds `bbbbbb` at order=2/position=1 and `aaaaaa` at order=1/position=2 and asserts `["aaaaaa","bbbbbb"]`; under the fix `position` decides and the correct answer becomes `["bbbbbb","aaaaaa"]`. That test must be deliberately INVERTED with its reason recorded, never quietly deleted. (3) The preview bug is confirmed at the source: `print_status` (`oc_runipd.py:6141`) passes `state` straight to `render_run_summary_table` (`render_stream.py:875`) and NO sort is applied, so `--prepare-only` (`:6556`) shows position order and would have shown `01 m73aet, 02 6lu3rq` while still running `6lu3rq` first. (4) NEW FINDING the item does not record, added as F-7: ordering is computed BEFORE status is consulted, so a queue mixing `to-review` and `approved` plans interleaves review passes and code execution in alphabetical Set order, and `dependency_depth` still ranks a plan depth-1 when it is only being REVIEWED, where the prerequisite does not apply.

## Goal

Make `aw oc run A B` run A then B, and make any order the runner chooses for itself visible at the moment it chooses it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the bug, then fix the ordering

- [x] E-01 Write the failing-first regression BEFORE touching the key, reproducing the measured case exactly: two independent plans whose Set ids sort OPPOSITE to the typed order (the real case was `runtrail` typed first while `runmixed` sorts first alphabetically), asserting dispatch follows the TYPED order. It must FAIL at current HEAD. Add, in the same file, the guard that stops this fix from breaking the property spec 25kzda 5.4 rule 5 protects: a DECLARED `Item-Dependencies` edge must still win over a contradicting typed order.
  - Depends on: none
  - Expected outcome: a test that fails at HEAD naming both orders, plus a passing declared-edge-wins test. Paste the failure.
  - Execution state: performed

- [x] E-02 Change the ONE shared `queue_sort_key` (`oc_runipd.py:3596`) from `(dependency_depth, setid, order, id6, position)` to `(dependency_depth, position, setid, order, id6)`. VERIFIED at authoring: `agy_runipd.queue_sort_key is oc_runipd.queue_sort_key` returns True (re-exported, not reimplemented), so do NOT introduce a second copy. Rewrite the docstring in the same edit: it currently says "`position` is LAST and is a stable identity, never a priority", which this change makes FALSE, and it claims the sort is deterministic from artifact content alone, which stops being true once invocation order is an input. Both statements must be corrected honestly rather than left to mislead the next reader. PRESERVE the docstring's underlying point, which still holds: `position` is also the key for outcome/prompt/session filenames and this run's decision ids, so it must remain FROZEN at queue-build time. Making it a sort input must not make it mutable.
  - Depends on: E-01
  - Expected outcome: E-01's regression passes, the declared-edge test still passes, and the docstring states the new contract including the invocation-order dependency.
  - Execution state: performed

- [x] E-03 Handle the EXISTING TEST THIS INVERTS, deliberately and visibly. `test_set_order_still_breaks_ties_among_equally_ready_nodes` (`tests/test_runner_item_dependencies.py:745`) constructs `bbbbbb` (order=2, position=1) and `aaaaaa` (order=1, position=2) and asserts `["aaaaaa", "bbbbbb"]` with the message "Order 1 precedes Order 2 on a tie". Under the fix `position` outranks `order`, so the correct expectation becomes `["bbbbbb", "aaaaaa"]`. INVERT it, do NOT delete it, and record in the test itself that the inversion is the intended consequence of this plan plus the id6, following the repo's precedent of pinning a behavior so a later phase must deliberately come and change it. Then check the whole file for any other assertion that depends on `order` outranking `position` and treat each the same way.
  - Depends on: E-02
  - Expected outcome: the inverted test passes with its reason recorded in-file; a stated list of every other assertion in that file examined, with each either unaffected or inverted-with-reason. A test deleted rather than inverted FAILS this item.
  - Execution state: performed

### Task group 2: make the order visible (the half that is not optional)

- [x] E-04 Build the SHARED order-announcement FORMATTER in `render_stream.py`, as a pure function, and call it from the OpenCode driver's queue build. It ALWAYS renders the execution order, whether or not anything was reordered, so the order is auditable in the log rather than reconstructible from `events.jsonl` timestamps. When the executed order DIFFERS from the order the operator expressed it renders a distinct WARNING naming BOTH orders and, per moved item, the SPECIFIC reason. A bare "reordered" line is not acceptable: the operator must be able to distinguish a DECLARED prerequisite (correct and expected, e.g. "6lu3rq before m73aet: 6lu3rq declares `executed:m73aet`") from an arbitrary TIEBREAK, which is the case that bit them. Record the announcement in the run's durable state/events too, so a later reader sees it without terminal scrollback; `events.jsonl` currently carries `ipd-started` timestamps and no ordering rationale at all.
  MEASURED AT REVIEW so the executor does not have to locate the seam: the ONLY correct site is `initialize_run` (`oc_runipd.py:2860`), because that is where `position` is assigned (`for position, id6 in enumerate(queue_ids, start=1)` at `:2930`) and where the queue is frozen into `state`. The EXPRESSED order is `queue_ids` as returned by `expand_selectors` (equivalently `state["selectors"]` for the literal-id6 case); the EXECUTED order is that same list re-sorted by `queue_sort_key`. Neither the plan nor the item named either source, and getting the expressed order from the wrong place is the one way this item can silently produce a truthful-looking but wrong message.
  WORD THE MESSAGE HONESTLY about what "expressed" means (PR-103): `position` is the OPERATOR'S TYPED order only when the selectors were literal id6 tokens. `expand_selectors` (`:2519`) also accepts a SETID, `all`, `reviews`, and a file path, and each expands to MANY positions whose order comes from the manifest, not from the operator's typing. So the announcement must NOT claim "you typed" for an expanded selection; say "requested order" and reserve any typed-order phrasing for the literal case, or the message misinforms in exactly the direction that erodes trust in it.
  - Depends on: E-02
  - Expected outcome: a pure formatter in `render_stream.py` with no runner import; the OpenCode driver prints its execution order on EVERY run; a reordered run prints a warning naming both orders and a per-item cause that distinguishes a declared edge from a tiebreak; the rationale is present in durable run state, shown by reading it back; the message does not claim a typed order for an expanded selector.
  - Execution state: performed

- [x] E-05 Fix the PREVIEW, which is a second defect and would have hidden this bug from a careful operator. MEASURED at authoring and RE-CONFIRMED at review: `print_status` (`oc_runipd.py:6141`) passes `state` directly to `render_run_summary_table` (`render_stream.py:875`) with NO sort applied, and the renderer iterates `state.get("queue", [])` in STORED order (`render_stream.py:903`, `:929`), printing `item.get("position", idx + 1)` as the leading column. So `--prepare-only` (`:6556`) renders POSITION order. That is why a preflight check would have shown `01 m73aet, 02 6lu3rq` and still executed `6lu3rq` first. Make the table show EXECUTION order, or show both explicitly labelled; a column a reader will read as sequence must not display identity. Note that once `position` drives the sort these agree in the common case BY CONSTRUCTION, so CONFIRM the fix on a case where a declared edge forces a divergence rather than assuming the problem disappeared.
  DO THE SORT IN THE SHARED RENDERER, not in one driver's `print_status`: `render_run_summary_table` is already shared and is called by BOTH drivers' `print_status`, so fixing it there fixes both hosts in one edit and cannot drift. If the renderer cannot reach `queue_sort_key` without importing a runner, sort in each driver before calling it and state that explicitly, because a renderer importing a runner would be a new layering defect.
  - Depends on: E-04
  - Expected outcome: `--prepare-only` shows the order the run will actually execute in, demonstrated on a queue where a declared edge makes execution order differ from position order, and demonstrated for BOTH drivers; no runner import was added to `render_stream.py`.
  - Execution state: performed

- [x] E-07 Land the SAME announcement and the SAME preview behavior in the ANTIGRAVITY driver, so the fix is not one-sided. MAINTAINER RULING 2026-09-03 at review: widen to both drivers now. THIS IS NOT OPTIONAL POLISH, and the reason is measured: `queue_sort_key` IS shared (`agy_runipd.queue_sort_key is oc_runipd.queue_sort_key` -> True, so E-02 alone changes agy's ORDERING), but `initialize_run` and `print_status` are NOT (`agy_runipd.print_status is oc_runipd.print_status` -> False; agy defines its own at `agy_runipd.py:4331` and its own `--prepare-only` at `:4691`, with its own `initialize_run` at `:1920` assigning `position` at `:1990`). Without this item `aw agy run` would silently get the reordering and NEITHER the announcement nor the corrected preview, which is exactly the divergence class the `rununify` Set exists to remove and which this repo has already been bitten by (`Heartbeat`/`stallfp-01`).
  CALL THE SHARED FORMATTER E-04 built; do NOT re-implement the message text in `agy_runipd.py`. A second copy of the wording would be a fresh re-fork of the kind `tests/test_render_stream.py:539` already guards against on the oc side. Keep agy's own host label (`driver_label="antigravity"`) exactly as `print_status` supplies it today.
  - Depends on: E-04, E-05
  - Expected outcome: `aw agy run` prints its execution order on every run, prints the same distinguishable reorder warning, and its `--prepare-only` shows execution order; the message text comes from the ONE shared formatter (proved by object identity or by a single-definition check), not a copy.
  - Execution state: performed

### Task group 3: keep the spec and the code in agreement

- [x] E-06 Amend spec `25kzda` 5.4 rule 4, which this plan CHANGES. It currently reads (`:826`): "Among simultaneously ready independent nodes, sort by dependency depth, type rank (`spec`, `backlog`, `ipd`, `prompt`), Set, numeric Order, stable ID, then canonical path" - and says nothing about operator order, which is why the runner was behaving to spec and the SPEC is what needed a decision. Insert the operator's expressed order between dependency depth and Set, and state explicitly that a declared edge still outranks it. Do NOT implement a divergence from an unamended spec and leave the two disagreeing. Record the maintainer's 2026-09-01 ruling as the authority.
  - Depends on: E-02
  - Expected outcome: rule 4 names the operator's order in its correct rank, with the declared-edge precedence stated; the spec and `queue_sort_key` agree, shown side by side.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `agy_runipd` RE-EXPORTS `queue_sort_key` rather than reimplementing it, and the repo has an established anti-fork pattern for exactly this (`evgi9n`). One edit covers both drivers; introducing a second copy would recreate the divergence the `rununify` Set exists to remove.
- The repo pins behavior it intends to change later, so a future phase must deliberately come and invert the assertion (precedent: `tests/test_wtiso_characterization.py`). E-03 follows that convention rather than deleting the inverted test.
- Interactive prompts are constrained by hard-won experience: `oc_runipd.py:711-715` records that a nested `aw` inheriting a TTY "believes it may prompt, and blocks on input() forever while its prompt goes into the pipe", verified to have WEDGED A FINALIZE FOR 1h49m (backlog `v1ex5z`, plan `g40w37`), which is why children get `stdin=subprocess.DEVNULL`.
- `position` is load-bearing identity, not just a number: outcome/prompt/session filenames and decision ids all key on it.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | The typed order is recorded then discarded. `position` is the LAST tiebreaker, by deliberate design, and the function's own docstring says so. | `oc_runipd.py:3614` returns `(dependency_depth, setid, order, id6, position)`; docstring at `:3610` |
| F-2 | Measured inversion, not inferred: queue built as `position 1 m73aet` / `position 2 6lu3rq`, dispatch ran `6lu3rq` 04:23:31 then `m73aet` 04:44:10, because `"runmixed" < "runtrail"`. | run `run-20260901T042331Z-118022`: `state.json` positions, `events.jsonl` `ipd-started` timestamps |
| F-3 | ONE function fixes both drivers. | `agy_runipd.queue_sort_key is oc_runipd.queue_sort_key` -> True, re-verified at this HEAD |
| F-4 | AN EXISTING TEST WILL INVERT, and it must be inverted rather than deleted. It builds `bbbbbb` (order=2, position=1) and `aaaaaa` (order=1, position=2) and asserts `["aaaaaa","bbbbbb"]`; under the fix the right answer is `["bbbbbb","aaaaaa"]`. | `tests/test_runner_item_dependencies.py:745-757` |
| F-5 | The PREVIEW would not have helped and is a second defect: no sort is applied between state and table, so `--prepare-only` renders position order. | `print_status` at `oc_runipd.py:6141` -> `render_run_summary_table` at `render_stream.py:875`; `--prepare-only` at `:6556` |
| F-6 | Nothing announces ordering today. The only way to find the inversion was comparing timestamps to positions after the fact. | greps for a queue/order announcement in `oc_runipd.py` return only comments; `events.jsonl` has `ipd-started` but no rationale |
| F-7 | **NEW, not in the backlog item.** Ordering is computed BEFORE status is consulted (`action_for` at `:2749` is applied per item only after selection at `:5844`), so a queue mixing `to-review` and `approved` plans interleaves REVIEW passes and CODE EXECUTION in alphabetical Set order. Worse, `dependency_depth` ranks a plan depth-1 even when it is only being REVIEWED, where the prerequisite does not apply: reviewing `818uru` does not require `2r306y` to be executed. | `queue_sort_key` takes no status input; `action_for:2749`; single sort site `:5844` |
| F-8 | The severity is HIGH because the failure is SILENT, not because this run lost work. The two plans were genuinely independent (zero shared Scope-Paths). | backlog `xvx8ez`'s own honest-severity note |
| F-9 | **FOUND AT REVIEW (PR-101), and it re-scoped this plan.** The fix as authored was ONE-SIDED. `queue_sort_key` is shared, so E-02 alone changes ordering for BOTH drivers - but the announcement's site (`initialize_run`) and the preview's site (`print_status`) are each defined SEPARATELY per runner, and `agy_runipd.py` was not in Scope-Paths. `aw agy run` would therefore have received the reordering with NO announcement and a still-misleading preview. Maintainer ruled: widen to both drivers now, message text from one shared formatter. E-07 added. | `agy_runipd.print_status is oc_runipd.print_status` -> False; `agy_runipd.py:4331` (`print_status`), `:4691` (`--prepare-only`), `:1920` (`initialize_run`), `:1990` (`position` assignment); `agy_runipd.queue_sort_key is oc_runipd.queue_sort_key` -> True |
| F-10 | **FOUND AT REVIEW (PR-103).** "The operator's typed order" is only literally true for LITERAL ID6 selectors. `expand_selectors` also accepts a setid, `all`, `reviews`, and a file path, and each expands into many positions ordered by the MANIFEST, not by the operator. Measured: `expand_selectors(m, ['all'])` returns 30 ids whose leading positions come from `wslayout` order 0..5, i.e. manifest order. So `position` records REQUEST order, which equals typed order only in the literal case. E-04's message must not claim otherwise. | `oc_runipd.py:2519` (`expand_selectors`), `:2930` (`position` assignment from `queue_ids`); `build_dynamic_manifest:2392` sorts each set by `(order, path.name)` |
| F-11 | **FOUND AT REVIEW (PR-104), confirming F-5 at the renderer rather than only at the caller.** `render_run_summary_table` iterates `state.get("queue", [])` in STORED order and prints `item.get("position", idx + 1)` as its leading column, so the misleading preview is a property of the shared renderer, not of one driver's `print_status`. That is why E-05's fix belongs in the renderer, where it covers both hosts. | `render_stream.py:903` (`queue = state.get("queue", [])`), `:929` (`for idx, item in enumerate(queue)`), `:930` (`pos = item.get("position", idx + 1)`) |

## Proposed changes (ordered, validatable)

1. Failing-first regression on the measured case, plus the declared-edge-wins guard (E-01).
2. Move `position` above `setid` in the one shared key; rewrite the now-false docstring (E-02).
3. Invert the existing tie test with its reason recorded; sweep the file for siblings (E-03).
4. Build the shared announcement formatter in `render_stream.py` and wire the OpenCode driver: announce always, warn with both orders and a per-item cause when reordered, persist the rationale (E-04).
5. Make `--prepare-only` show execution order, fixed in the shared renderer (E-05).
6. Land the same announcement and preview in the ANTIGRAVITY driver, calling the same formatter (E-07).
7. Amend spec 25kzda 5.4 rule 4 so code and spec agree (E-06).

## Deferred / out of scope (with reason)

- DETECTING EXPLICIT-VS-EXPANDED SELECTIONS. The maintainer's ruling considered and rejected this: honoring `position` is meaningful for a small typed list and a harmless no-op for a large selector expansion (measured: a 12-item run spanning 6 Sets, where `position` merely reflects expansion order and any total order is equally defensible). Detecting the difference would need the runner to record HOW the queue was built, i.e. new durable state and more surface, for no gain in the expansion case.
- REFUSING on a contradicting order (the item's option (b)). Rejected by the ruling in favour of honoring the typed order. Its warning requirement survives as E-04, which is the useful half of that option.
- INTERACTIVE CONFIRMATION. The item's recommended shape allows prompting when the order changed AND there is a real TTY AND the run is not unattended. NOT taken on here: the announcement (E-04) delivers the safety, and a prompt adds the wedge risk the TTY constraint exists to avoid for a condition that is usually legitimate. If you want the prompt, it must be built in the DRIVER at queue-build time before the first child spawns, and must fall back to non-interactive with no TTY, or an unattended overnight run can block for hours.
- F-7's MIXED-STATUS INTERLEAVING. Recorded here and filed rather than fixed: this plan makes the ORDER honest, but whether a single run should mix review passes and code execution at all is a separate UX question, and the depth-ranking of a review-only item needs its own decision. Do not silently fix it inside this plan.
- The `type rank` clause of spec rule 4, deliberately unimplemented because this runner's queue is homogeneous (IPDs only). Unchanged here.

## Scope check

- Over-scope: none. Every edit either changes the order, makes the order visible, or keeps the spec truthful about the order.
- Under-scope: this does NOT decide whether mixing `to-review` and `approved` items in one run is sensible (F-7), and it does not add the interactive prompt the item floated. Both are named above with reasons.

## Required tests / validation

- The failing-first regression: two independent plans whose Sets sort opposite to the typed order, failing at HEAD and passing after.
- A declared edge STILL wins over a contradicting typed order, so fixing this cannot silently break spec 5.4 rule 5.
- The inverted tie test, passing, with its reason in-file.
- `position` is still never renumbered by sorting (`test_position_is_never_renumbered_by_ordering` must stay green, since E-02 must not make identity mutable).
- A legacy queue entry with no `order` key still sorts without crashing (`test_missing_order_key_still_sorts` stays green).
- The announcement: an unreordered run prints its order; a reordered run prints both orders plus a per-item cause distinguishing a declared edge from a tiebreak; the rationale is readable from durable state afterwards.
- `--prepare-only` shows execution order, demonstrated on a queue where a declared edge makes it differ from position order.
- BOTH DRIVERS, for the announcement AND the preview, not only OpenCode (E-07). Plus a single-definition check proving the message text was shared rather than copied.
- The announcement does not claim a TYPED order for an EXPANDED selector (setid / `all`), per F-10.
- Both driver suites green: `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py`.
- Full suite bare (`python3 -m pytest`), compared against YOUR OWN pre-change measurement. Baseline at authoring HEAD `b0f2d6bd`: `4096 passed, 3 skipped, 4 xfailed`. No `-n0`, no second `-q`, no `-p no:randomly`.

### Full-suite result (measured at execution, 2026-09-04)

Bare `python3 -m pytest` in BOTH trees, the changed lane and a detached worktree at the pre-change HEAD `5eeee9be`. No `-n0`, no second `-q`, no `-p no:randomly`. Re-measured AFTER the implementation commit, at `git rev-parse HEAD` -> `a834774eb7a3cc069c3ff3269d5729a35a5e7457`, giving the identical `15 failed, 4110 passed, 3 skipped, 4 xfailed in 29.88s`:

```
BASE   : ['15 failed, 4088 passed, 3 skipped, 4 xfailed in 31.55s']
CHANGED: ['15 failed, 4110 passed, 3 skipped, 4 xfailed in 30.45s']
failing sets IDENTICAL: True
newly failing: (none)
newly fixed  : (none)
```

+22 passing (21 new tests in `tests/test_run_order_announcement.py`, +1 from the E-03 split) and ZERO new failures, with the failing test-id SET proved identical rather than only the counts compared.

TWO ENVIRONMENTAL CAVEATS, stated plainly rather than reported as a green suite:

1. The 15 failures are ALL `tests/test_run_viewer.py` and are PRE-EXISTING, failing identically at the unmodified base HEAD. Cause: `run_viewer.discover_run_dirs(Path("."))` requires run directories to exist in the checkout, and a fresh lane worktree has no `.aw/records/runs/`. Unrelated to this change and not introduced by it.
2. `python3 -m pytest` must be run with `AW_EXECUTION_ROLE` UNSET. This driver exports `AW_EXECUTION_ROLE=worker`, which makes 13 lifecycle tests in `tests/test_oc_runipd.py` / `tests/test_agy_runipd_cli.py` hit the deliberate `AW-LIFECYCLE-ROLE-001` begin/finalize refusal. With the variable unset those 13 pass in both trees; the numbers above are from that condition, applied identically to base and lane.

The six directly affected files, run together: `python3 -m pytest -o addopts="" -p no:randomly tests/test_run_order_announcement.py tests/test_runner_item_dependencies.py tests/test_run_summary_table.py tests/test_render_stream.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py` -> `234 passed in 18.84s`.

`aw sanitize --agent` -> `{"outcome":"clean","exit":0,"findings":0}`. `ruff format` applied to all five touched Python files; `ruff check` delta versus base is only 3 new `PLC0414` in `agy_runipd.py`, which is that file's established intentional re-export convention (35 pre-existing instances at base) and is not enforced by the configured hooks.

## Spec / documentation sync

- Spec `25kzda` 5.4 rule 4 (`:826`) MUST be amended by E-06; code and spec must not be left disagreeing.
- `queue_sort_key`'s docstring is itself documentation of the contract and is rewritten by E-02.
- If any user-facing doc describes `aw oc run`'s ordering, update it; otherwise state N/A with the paths checked.
- DONE at execution. No prose DOC describes the runner's ordering: searched `docs/`, `README.md`, and every top-level `*.md` for `aw oc run`/`aw agy run` (one hit, `docs/reporting-contract.md`, which mentions "Order" only as a plan-Set field and says nothing about queue ordering) and for `queue.*order|ordering|sort by dependency` (one hit, `CHANGELOG.md:259`, an unrelated advisory-ordering entry). So no existing doc was left disagreeing.
- ADDED beyond the declared Scope-Paths: `CHANGELOG.md`, with a `--scope-reason` at finalize. This is a USER-VISIBLE behavior change to a shipped command (`aw oc run A B` executes in a different order than it did yesterday) plus two new user-facing output behaviors, and this repo records exactly that class in the CHANGELOG. Shipping the ordering flip with no changelog entry would leave an operator who relied on the old alphabetical order with no notice. Three entries were added under `1.3.0 (pending)`: the ordering fix (stating that a declared dependency still wins), the announcement, and the corrected preview. Written in user-facing register with no em or en dashes, per the execution contract.

## Open questions

### OQ-01: Should the announcement ever PROMPT, or is printing enough?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT BLOCKING, because E-04 delivers the safety property either way and a prompt can be added later without redoing it. The maintainer's 2026-09-01 requirement said reordering must be announced "LOUDLY, and possibly interactively", leaving the prompt optional. This plan implements the announcement only, and the reason is the hard constraint recorded in the item: a nested `aw` that inherits a TTY once wedged a finalize for 1h49m, so any prompt must live in the DRIVER at queue-build time before the first child spawns and must degrade to non-interactive with no TTY, or an unattended overnight run can block for hours. If you want the prompt, say so and it becomes its own E-item under those constraints.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the new regression FAILING at pre-change HEAD, showing the typed order and the actual (inverted) order, with Set ids that sort opposite to the typed sequence so the test reproduces the measured case rather than a synthetic one. Paste the declared-edge-wins test passing at that same pre-change HEAD, which proves it is a genuine guard and not an artifact of the fix. A regression never observed failing is not accepted.
  - Observed evidence: `git rev-parse HEAD` -> `5eeee9be64ab3dddcf3e6bd3b5b482b2155ae638`, `tests/test_run_order_announcement.py` written, `queue_sort_key` UNTOUCHED. `python3 -m pytest -o addopts="" -p no:randomly tests/test_run_order_announcement.py::RequestedOrderIsAuthoritativeTests -v`:

```
tests/test_run_order_announcement.py::RequestedOrderIsAuthoritativeTests::test_declared_edge_still_beats_a_contradicting_typed_order PASSED [ 16%]
tests/test_run_order_announcement.py::RequestedOrderIsAuthoritativeTests::test_position_stays_frozen_identity PASSED [ 33%]
tests/test_run_order_announcement.py::RequestedOrderIsAuthoritativeTests::test_the_key_is_one_shared_object FAILED [ 50%]
tests/test_run_order_announcement.py::RequestedOrderIsAuthoritativeTests::test_transitive_chain_still_orders_by_depth_against_the_typed_order PASSED [ 66%]
tests/test_run_order_announcement.py::RequestedOrderIsAuthoritativeTests::test_typed_order_beats_alphabetical_setid FAILED [ 83%]
tests/test_run_order_announcement.py::RequestedOrderIsAuthoritativeTests::test_typed_order_beats_numeric_order_too FAILED [100%]
========================= 3 failed, 3 passed in 0.20s ==========================
```

    THE MEASURED CASE, failing with BOTH orders named, and using the REAL Set ids (`runtrail` typed first, `runmixed` sorting first) rather than synthetic ones:

```
    def test_typed_order_beats_alphabetical_setid(self):
        """The MEASURED case: `aw oc run m73aet 6lu3rq` ran 6lu3rq first because runmixed < runtrail."""
        queue = [
            _item("m73aet", setid="runtrail", order=1, position=1),
            _item("6lu3rq", setid="runmixed", order=1, position=2),
        ]
E       AssertionError: Lists differ: ['6lu3rq', 'm73aet'] != ['m73aet', '6lu3rq']
E       - ['6lu3rq', 'm73aet']
E       + ['m73aet', '6lu3rq'] : the operator typed m73aet first; alphabetical Set id must not invert it
```

    THE DECLARED-EDGE GUARD PASSING AT THAT SAME PRE-CHANGE HEAD (`PASSED [ 16%]` above), which is what proves it is a genuine guard and not an artifact of the fix: `test_declared_edge_still_beats_a_contradicting_typed_order` builds `depend` (position 1, order 1, declaring `executed:prereq`) against `prereq` (position 2, order 9) and asserts `["prereq","depend"]`. It passed BEFORE the key changed and still passes after (V-02), so `dependency_depth` staying first is verified in both directions. `test_position_stays_frozen_identity` and `test_transitive_chain_...` likewise passed pre-change. The third pre-change failure, `test_the_key_is_one_shared_object`, fails only because it also asserts identity of the not-yet-written `run_order_rationale`.
    INDEPENDENT REPRODUCTION OF THE MEASURED BUG at the pre-change HEAD, outside the test suite, run from a detached worktree at `5eeee9be` against a two-plan fixture repo (`runtrail`/`runmixed`, no declared edges):

```
PRE-CHANGE HEAD 5eeee9be
  frozen positions (what the preview showed): [(1, 'm73aet'), (2, '6lu3rq')]
  dispatch order  (what run_queue selects): ['6lu3rq', 'm73aet']
  run_order recorded in state? False
  key for m73aet: (0, 'runtrail', 1, 'm73aet', 1)
  key for 6lu3rq: (0, 'runmixed', 1, '6lu3rq', 2)
```

    That is F-1, F-2, F-5 and F-6 in one run: the request was recorded, discarded at dispatch on Set id alone, previewed in the WRONG order, and nothing was recorded or announced.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the new key. Paste E-01's regression now passing and the declared-edge test still passing. Paste `agy_runipd.queue_sort_key is oc_runipd.queue_sort_key` -> True AFTER the edit, proving no second copy was introduced. Paste the rewritten docstring, showing it no longer claims `position` is never a priority and no longer claims determinism from artifact content alone. Paste `test_position_is_never_renumbered_by_ordering` still green, proving identity did not become mutable.
  - Observed evidence: THE NEW KEY (`agent_workflows/oc_runipd.py`, `queue_sort_key`), `position` moved from LAST to immediately after `dependency_depth`:

```
    return (
        dependency_depth(item["id6"], by_id),
        item.get("position", 0),
        str(item.get("setid") or ""),
        item.get("order") if isinstance(item.get("order"), int) else 999,
        item["id6"],
    )
```

    E-01's REGRESSION NOW PASSING with the declared-edge guard still passing, same command as V-01:

```
tests/test_run_order_announcement.py::RequestedOrderIsAuthoritativeTests::test_declared_edge_still_beats_a_contradicting_typed_order PASSED [ 16%]
tests/test_run_order_announcement.py::RequestedOrderIsAuthoritativeTests::test_position_stays_frozen_identity PASSED [ 33%]
tests/test_run_order_announcement.py::RequestedOrderIsAuthoritativeTests::test_transitive_chain_still_orders_by_depth_against_the_typed_order PASSED [ 66%]
tests/test_run_order_announcement.py::RequestedOrderIsAuthoritativeTests::test_typed_order_beats_alphabetical_setid PASSED [ 83%]
tests/test_run_order_announcement.py::RequestedOrderIsAuthoritativeTests::test_typed_order_beats_numeric_order_too PASSED [100%]
```

    NO SECOND COPY WAS INTRODUCED, asserted by object identity after the edit and by an AST single-definition scan of the whole package:

```
queue_sort_key shared          : True
run_order_rationale shared     : True
announce_run_order shared      : True

queue_sort_key                     defined in: ['oc_runipd.py']
run_order_rationale                defined in: ['oc_runipd.py']
announce_run_order                 defined in: ['oc_runipd.py']
```

    THE REWRITTEN DOCSTRING, which retracts BOTH now-false claims explicitly rather than quietly dropping them. It no longer says "`position` is LAST and is a stable identity, never a priority"; it now says the opposite and says why, and it states the invocation-order dependency as an HONEST LIMIT instead of claiming determinism from artifact content alone:

```
    `position` IS A PRIORITY (runorder prpipy; maintainer ruling 2026-09-01), ranked immediately
    after dependency depth and therefore ABOVE Set, Order, and id6. ...

    HONEST LIMITS OF THIS KEY, both of which the pre-prpipy docstring got wrong:

    * The sort is NO LONGER a function of artifact content alone. `position` comes from the
      INVOCATION (`expand_selectors` -> `initialize_run`), so the same plans selected in a different
      order legitimately execute in a different order. That is the intended contract, not drift.
    * `position` is a priority AND STILL A FROZEN IDENTITY. Outcome/prompt/session filenames and this
      run's decision ids all key on it, so it is assigned exactly once at queue-build time and is
      never renumbered by sorting. Reading it here must not make it mutable.
```

    The docstring also PRESERVES the plan's required point (frozen identity) and adds the F-10 caveat that `position` equals a TYPED order only for literal id6 selectors. IDENTITY DID NOT BECOME MUTABLE, `test_position_is_never_renumbered_by_ordering` green (`tests/test_runner_item_dependencies.py`), alongside every other ordering test in that file:

```
tests/test_runner_item_dependencies.py::OrderingAndCascadeTests::test_position_is_never_renumbered_by_ordering PASSED [ 81%]
tests/test_runner_item_dependencies.py::OrderingAndCascadeTests::test_declared_edges_beat_set_order_when_the_two_disagree PASSED [ 36%]
tests/test_runner_item_dependencies.py::OrderingAndCascadeTests::test_missing_order_key_still_sorts PASSED [ 63%]
====================== 11 passed, 45 deselected in 0.26s =======================
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the inverted test with its in-file reason and id6 reference, plus its passing output. Paste `test_missing_order_key_still_sorts` still green. ENUMERATE every other assertion in `tests/test_runner_item_dependencies.py` that touches ordering, stating for each whether it was unaffected or inverted-with-reason. If any test was DELETED rather than inverted, this item FAILS.
  - Observed evidence: THE INVERTED TEST, with its in-file reason and the `prpipy` id6 named in the docstring, renamed so the name states the new contract instead of the retired one (`test_set_order_still_breaks_ties_among_equally_ready_nodes` -> `test_request_order_outranks_set_order_among_equally_ready_nodes`):

```
    def test_request_order_outranks_set_order_among_equally_ready_nodes(self):
        """DELIBERATELY INVERTED by runorder `prpipy`; this is a CONTRACT CHANGE, not a broken test.

        This assertion used to read `["aaaaaa", "bbbbbb"]` with the message "Order 1 precedes Order 2
        on a tie", pinning 8guhs0's key `(depth, setid, order, id6, position)`. `prpipy` moved
        `position` from LAST to immediately after `depth` on the maintainer's 2026-09-01 ruling,
        because ranking it last recorded the operator's requested order and then discarded it (run
        `run-20260901T042331Z-118022` inverted `aw oc run m73aet 6lu3rq` on Set id alone). So among
        equally-ready nodes the REQUESTED order now decides and `Order` is the next tiebreaker down.
        Inverted rather than deleted, following this repo's pin-then-deliberately-change convention.

        What did NOT change, and is asserted separately above: a declared edge still outranks both
        (`test_declared_edges_beat_set_order_when_the_two_disagree`), because `dependency_depth`
        remains FIRST in the key.
        """
        ...
        self.assertEqual(
            ordered,
            ["bbbbbb", "aaaaaa"],
            "prpipy: the requested order (position) outranks Order on a tie",
        )
```

    NOTHING WAS DELETED. The file's test count went UP, from 55 to 56: the inversion is one test, plus a NEW sibling `test_set_order_still_breaks_ties_when_the_request_order_ties` added because inverting the old one would otherwise have left `Order`'s surviving role (it dropped one rank, it did not stop mattering) unpinned. THE ENUMERATION, every ordering-touching test in the file found by AST scan for `queue_sort_key`/`dependency_depth` (not by eye), with each one's disposition:

    | Test | Disposition |
    |---|---|
    | `test_dependency_depth_counts_only_in_queue_ipd_edges` (L695) | UNAFFECTED. Asserts `dependency_depth` values only; does not compare the key tuple. |
    | `test_dependency_depth_is_cycle_safe` (L718) | UNAFFECTED. Asserts the depth of a cycle member is an `int`. |
    | `test_declared_edges_beat_set_order_when_the_two_disagree` (L726) | UNAFFECTED, and load-bearing: it pins the property this change must NOT break (`dependency_depth` first). Passed before and after. |
    | `test_request_order_outranks_set_order_among_equally_ready_nodes` (L745) | INVERTED WITH REASON, as pasted above. The only assertion in the file that depended on `order` outranking `position`. |
    | `test_set_order_still_breaks_ties_when_the_request_order_ties` (L775) | NEW. Equal positions -> `Order` still decides, so the inversion cannot be misread as "Order stopped mattering". |
    | `test_position_is_never_renumbered_by_ordering` (L790) | UNAFFECTED. Asserts identity is not mutated by sorting; still true and now more important (V-02). |
    | `test_missing_order_key_still_sorts` (L800) | UNAFFECTED. A legacy entry with no `order` key still sorts. |

    ALL GREEN, including the two named explicitly by this item:

```
tests/test_runner_item_dependencies.py::OrderingAndCascadeTests::test_request_order_outranks_set_order_among_equally_ready_nodes PASSED [ 90%]
tests/test_runner_item_dependencies.py::OrderingAndCascadeTests::test_set_order_still_breaks_ties_when_the_request_order_ties PASSED [100%]
tests/test_runner_item_dependencies.py::OrderingAndCascadeTests::test_missing_order_key_still_sorts PASSED [ 63%]
====================== 11 passed, 45 deselected in 0.26s =======================
```

    Whole file green: `python3 -m pytest -o addopts="" -p no:randomly tests/test_runner_item_dependencies.py` -> `56 passed in 1.57s` (was `54 passed` + 1 failing inversion immediately after E-02, and `55 passed` at base).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste an UNREORDERED run printing its execution order (proving the print is unconditional). Paste a REORDERED run printing both orders plus the per-item cause, and show the cause names the specific declared edge (e.g. "declares `executed:<id6>`") rather than a bare "reordered". Paste a TIEBREAK case whose message is DISTINGUISHABLE from the declared-edge case, since telling those two apart is the operator-facing point. Then paste the durable record read back from run state/events, since terminal output alone does not satisfy this item. Paste the formatter's definition site showing it lives in `render_stream.py` and imports NEITHER runner. Finally paste an EXPANDED-SELECTOR case (a setid or `all`, not literal id6 tokens) showing the message does NOT claim the operator typed that order (PR-103).
  - Observed evidence: (1) UNREORDERED RUN STILL PRINTS ITS ORDER, proving the print is UNCONDITIONAL. This is the MEASURED case (`m73aet` in `runtrail` typed first, `6lu3rq` in `runmixed` sorting first), now correct. `python3 -m agent_workflows.oc_runipd start m73aet 6lu3rq --repo <fixture> --prepare-only`:

```
Run order (2 item(s)): 01 m73aet  02 6lu3rq
  Matches the typed order; nothing was reordered.
Run ID: run-20260904T044551Z-1136851
```

    Note the announcement precedes the `Run ID` line, i.e. it is emitted at queue build before any child session could start.
    (2) REORDERED RUN PRINTS BOTH ORDERS PLUS A PER-ITEM CAUSE NAMING THE SPECIFIC EDGE, not a bare "reordered" (fixture: `depend` in Set `aaaset` declaring `executed:prereq`, `prereq` in Set `zzzset`):

```
Run order (2 item(s)): 01 prereq  02 depend
WARNING: the execution order DIFFERS from the typed order.
  typed order:  01 depend  02 prereq
  execution order: 01 prereq  02 depend
  - prereq: declared dependency: depend declares `executed:prereq`, so prereq must run first
  - depend: declared dependency: depend declares `executed:prereq`, so it waits for prereq
```

    (3) A TIEBREAK CASE, VISIBLY DISTINGUISHABLE from the declared-edge case above, which is the operator-facing point of this item. Same formatter, side by side:

```
=== TIEBREAK case (legacy entries with no position; nothing declared) ===
Run order (2 item(s)): 01 aaaaaa  02 bbbbbb
  Requested order was expanded from selector all in manifest order, not typed item by item.
WARNING: the execution order DIFFERS from the requested order.
  requested order:  01 bbbbbb  02 aaaaaa
  execution order: 01 aaaaaa  02 bbbbbb
  - aaaaaa: tiebreak: no declared dependency explains this move; ranked by requested position unset, Set 'aaaset', Order unset, id6
  - bbbbbb: tiebreak: no declared dependency explains this move; ranked by requested position unset, Set 'zzzset', Order unset, id6

=== DECLARED-EDGE case, for side-by-side contrast ===
Run order (2 item(s)): 01 prereq  02 depend
WARNING: the execution order DIFFERS from the typed order.
  typed order:  01 depend  02 prereq
  execution order: 01 prereq  02 depend
  - prereq: declared dependency: depend declares `executed:prereq`, so prereq must run first
  - depend: declared dependency: depend declares `executed:prereq`, so it waits for prereq
```

    A `declared dependency:` cause is correct-and-expected and names the edge; a `tiebreak:` cause names the comparator fields that decided and says plainly that NOTHING declared explains the move. That is the case that bit the maintainer, and it is now labelled as such. Asserted by `test_tiebreak_divergence_is_labelled_differently` and `test_declared_edge_divergence_names_the_specific_edge`.
    (4) THE DURABLE RECORD, READ BACK FROM DISK, since terminal output alone does not satisfy this item. From `state.json` (new `run_order` key) and `events.jsonl` (new `run-order` event; before this change `events.jsonl` carried `ipd-started` timestamps and NO ordering rationale at all):

```
=== DURABLE state.json run_order (read back from disk) ===
{
  "causes": {
    "depend": "declared dependency: depend declares `executed:prereq`, so it waits for prereq",
    "prereq": "declared dependency: depend declares `executed:prereq`, so prereq must run first"
  },
  "executed": ["prereq", "depend"],
  "reordered": true,
  "request_kind": "typed",
  "requested": ["depend", "prereq"],
  "selectors": ["depend", "prereq"]
}

=== DURABLE events.jsonl run-order event ===
{
  "at": "2026-09-04T04:46:14+00:00",
  "causes": { ... same two causes ... },
  "event": "run-order",
  "executed": ["prereq", "depend"],
  "reordered": true,
  "request_kind": "typed",
  "requested": ["depend", "prereq"],
  "run_id": "run-20260904T044614Z-1137313"
}
```

    (5) THE FORMATTER'S DEFINITION SITE is `render_stream.py` and it imports NEITHER runner. AST single-definition scan across `agent_workflows/*.py`, plus the module's complete import list:

```
format_run_order_announcement      defined in: ['render_stream.py']

=== render_stream imports (no runner) ===
22:from __future__ import annotations
24:import datetime as dt
25:import json
26:from pathlib import Path
27:import re
28:import signal
29:import threading
30:import time
31:from typing import Any, Callable, TextIO
```

    Also asserted in-suite by `test_formatter_is_pure_and_imports_no_runner` (walks the module's AST and fails on any import whose name contains `runipd`) and `test_exactly_one_definition_in_the_package`. The split is deliberate: the WORDING is pure and lives in `render_stream`; the runner-state computation (`run_order_rationale`) and the I/O (`announce_run_order`) live in `oc_runipd`, so the renderer never needs `queue_sort_key`.
    (6) AN EXPANDED SELECTOR DOES NOT CLAIM THE OPERATOR TYPED THAT ORDER (PR-103 / F-10). `python3 -m agent_workflows.oc_runipd start all --repo <fixture> --prepare-only`:

```
Run order (2 item(s)): 01 m73aet  02 6lu3rq
  Requested order was expanded from selector all in manifest order, not typed item by item.
  Matches the requested order; nothing was reordered.
```

    The phrase is "requested order" throughout and the expansion is named; "typed order" appears ONLY for literal id6 selectors. `test_expanded_selection_is_not_called_a_typed_order` checks `all`, a setid, `reviews`, and a literal-id6 list that does not match the frozen queue, and `test_expanded_selection_message_never_claims_a_typed_order` asserts the string "typed order" is absent from the rendered message.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `--prepare-only` output for a queue where a DECLARED EDGE makes execution order differ from position order, showing the table reflects EXECUTION order (or shows both, labelled). A demonstration on a queue where the two coincide does NOT satisfy this item, because that is exactly the case the bug already looked correct in. Paste `rg -n "import" agent_workflows/render_stream.py` (or an AST check) showing no runner import was introduced.
  - Observed evidence: THE REQUIRED DIVERGENT CASE, a queue where a DECLARED EDGE makes execution order differ from position order (`depend` at position 01 declares `executed:prereq`, so it must run SECOND). `python3 -m agent_workflows.oc_runipd start depend prereq --repo <fixture> --prepare-only`:

```
├─────┬─────┬────────┬────────┬─────────┬────────┬────────┬──────────┬───────┬─────────┬────────┬─────────┬───────────┤
│ Run │ Pos │ ID6    │ Set    │ Action  │ Status │ Verify │ Duration │ Spend │ Tok tot │ Tok in │ Tok out │ Tok cache │
├─────┼─────┼────────┼────────┼─────────┼────────┼────────┼──────────┼───────┼─────────┼────────┼─────────┼───────────┤
│  01 │  02 │ prereq │ zzzset │ execute │ queued │ -      │        - │     - │       - │      - │       - │         - │
│  02 │  01 │ depend │ aaaset │ execute │ queued │ -      │        - │     - │       - │      - │       - │         - │
```

    Rows are in EXECUTION order (`prereq` first) and BOTH sequences are shown, LABELLED: `Run` is the execution sequence, `Pos` the frozen identity. Note `Run 01 / Pos 02`, i.e. the two genuinely diverge here, so this is NOT the coincident case the item rules out. THE SAME FIXTURE AT THE PRE-CHANGE HEAD, for contrast, showing the old single `#` column presenting identity as sequence:

```
├────┬────────┬──────────┬─────────┬────────┬────────┬──────────┬───────┬─────────┬────────┬─────────┬───────────┤
│  # │ ID6    │ Set      │ Action  │ Status │ Verify │ Duration │ Spend │ Tok tot │ Tok in │ Tok out │ Tok cache │
├────┼────────┼──────────┼─────────┼────────┼────────┼──────────┼───────┼─────────┼────────┼─────────┼───────────┤
│ 01 │ m73aet │ runtrail │ execute │ queued │ -      │        - │     - │       - │      - │       - │         - │
│ 02 │ 6lu3rq │ runmixed │ execute │ queued │ -      │        - │     - │       - │      - │       - │         - │
```

    That is the F-5/F-11 defect verbatim: the preview said `01 m73aet, 02 6lu3rq` while dispatch would run `6lu3rq` first (proved in V-01), and there was no announcement to contradict it.
    BOTH DRIVERS, as the item's Expected outcome requires (agy's own output is also pasted in V-07). Fixed ONCE in the shared `render_run_summary_table`, so `print_status` on either host inherits it; asserted by `test_both_drivers_print_status_in_execution_order`, which drives `oc_runipd.print_status` and `agy_runipd.print_status` over the same divergent state and requires row order `["prereq","depend"]` from each.
    NO RUNNER IMPORT WAS INTRODUCED. The renderer reads the runner-recorded `state["run_order"]["executed"]` instead of reaching for `queue_sort_key`, which is exactly why it stays pure. Complete import list of `agent_workflows/render_stream.py`:

```
22:from __future__ import annotations
24:import datetime as dt
25:import json
26:from pathlib import Path
27:import re
28:import signal
29:import threading
30:import time
31:from typing import Any, Callable, TextIO
```

    AST-checked in-suite by `test_formatter_is_pure_and_imports_no_runner`. GRACEFUL DEGRADATION verified rather than assumed: a run directory frozen before this change has no `run_order` key, so the renderer falls back to stored order and still renders every row, pinned by `test_table_falls_back_to_stored_order_without_a_recorded_run_order`. The pre-existing table suite is unchanged and green (`tests/test_run_summary_table.py` -> `10 passed`), including its border-width and alignment assertions, which the added column had to keep satisfying; the totals-row column spans are now DERIVED from `headers.index("Duration")` rather than the hardcoded literal `6` that appeared in five places, so the next column added cannot silently mis-span them.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the ANTIGRAVITY driver's own output for all three cases V-04 and V-05 require of the OpenCode driver: an unreordered run printing its order, a reordered run with a per-item cause, and `--prepare-only` showing execution order on a declared-edge queue. Then PROVE the wording is shared rather than copied: paste a package-wide check that the announcement formatter has exactly ONE definition (AST-based, across `agent_workflows/*.py`, following the precedent at `tests/test_render_stream.py:565`), and paste an identity assertion tying both drivers to it. A pasted agy output alone does NOT satisfy this item, because a copied message string would produce identical output while re-creating the divergence.
  - Observed evidence: THE ANTIGRAVITY DRIVER'S OWN OUTPUT, all three required cases. `python3 -m agent_workflows.agy_runipd start depend prereq --repo <fixture> --prepare-only` covers the REORDERED run with a per-item cause AND the `--prepare-only` preview on a declared-edge queue in one invocation:

```
Run order (2 item(s)): 01 prereq  02 depend
WARNING: the execution order DIFFERS from the typed order.
  typed order:  01 depend  02 prereq
  execution order: 01 prereq  02 depend
  - prereq: declared dependency: depend declares `executed:prereq`, so prereq must run first
  - depend: declared dependency: depend declares `executed:prereq`, so it waits for prereq
Run ID: run-20260904T044541Z-1136652
State directory: /tmp/.../.aw/records/runs/run-20260904T044541Z-1136652
╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ AW RUN SUMMARY: run-20260904T044541Z-1136652 (antigravity)                                                          │
│ Outcome: QUEUED   Duration: 0s   Spend: $0.00   Tokens: 0 (In: 0 │ Out: 0 │ Cache: 0)                               │
│ Progress: 0/2  [          ]   0% (2 queued)                                                                         │
├─────┬─────┬────────┬────────┬─────────┬────────┬────────┬──────────┬───────┬─────────┬────────┬─────────┬───────────┤
│ Run │ Pos │ ID6    │ Set    │ Action  │ Status │ Verify │ Duration │ Spend │ Tok tot │ Tok in │ Tok out │ Tok cache │
├─────┼─────┼────────┼────────┼─────────┼────────┼────────┼──────────┼───────┼─────────┼────────┼─────────┼───────────┤
│  01 │  02 │ prereq │ zzzset │ execute │ queued │ -      │        - │     - │       - │      - │       - │         - │
│  02 │  01 │ depend │ aaaset │ execute │ queued │ -      │        - │     - │       - │      - │       - │         - │
```

    The host label is agy's own (`(antigravity)`), exactly as `print_status` supplies it, and `Run 01 / Pos 02` shows the preview reflects EXECUTION order on a genuinely divergent queue. THE UNREORDERED CASE for agy, proving its print is unconditional too, asserted by `test_unreordered_run_announces_and_records_its_order`, which loops over BOTH drivers and requires `"Run order"` and `01 m73aet` in stdout with `"WARNING"` ABSENT, plus the `run-order` event present in `events.jsonl` exactly once and `state["run_order"]["executed"] == ["m73aet","6lu3rq"]`:

```
tests/test_run_order_announcement.py::QueueBuildAnnouncementTests::test_unreordered_run_announces_and_records_its_order PASSED
tests/test_run_order_announcement.py::QueueBuildAnnouncementTests::test_reordered_run_warns_and_records_the_cause PASSED
tests/test_run_order_announcement.py::PreviewShowsExecutionOrderTests::test_both_drivers_print_status_in_execution_order PASSED
```

    Each of those three iterates `_DRIVERS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))` under `subTest`, so agy is verified by the suite and not only by the pasted terminal output.
    THE WORDING IS SHARED, NOT COPIED, which is the part a pasted agy output cannot establish. AST-based package-wide single-definition scan across `agent_workflows/*.py`, following the `Heartbeat` precedent:

```
format_run_order_announcement      defined in: ['render_stream.py']
run_order_rationale                defined in: ['oc_runipd.py']
announce_run_order                 defined in: ['oc_runipd.py']
queue_sort_key                     defined in: ['oc_runipd.py']
```

    OBJECT IDENTITY tying both drivers to those single definitions:

```
queue_sort_key shared          : True
run_order_rationale shared     : True
announce_run_order shared      : True
formatter shared (oc)          : True
formatter shared (agy)         : True
```

    In-suite equivalents: `test_both_drivers_bind_the_same_formatter_object` (asserts `mod.format_run_order_announcement is render_stream.format_run_order_announcement` for both drivers), `test_exactly_one_definition_in_the_package`, and `test_the_key_is_one_shared_object` (which also pins `run_order_rationale`). `agy_runipd.py` gained only three re-export bindings in the `as <same-name>` form this module already uses for its shared surface, and NO copy of the message text: not just the wording but the whole announcement path (`announce_run_order`) and the rationale computation (`run_order_rationale`) are the same objects, so the divergence class named in F-9 is closed at three levels rather than one. Both driver suites green: `tests/test_oc_runipd.py` + `tests/test_agy_runipd_cli.py` -> included in `234 passed in 18.84s` over the six affected files.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the amended spec rule 4 beside the new `queue_sort_key` tuple, showing they agree field for field, and that the declared-edge precedence is stated in the spec text rather than implied. Paste `aw check` BEFORE and AFTER the spec edit and show the finding set is UNCHANGED for this file. Do NOT require "clean": the repo carries pre-existing `aw check plans` errors (13 at the time of review, recorded in several sibling plans' histories), so "clean" is unachievable and would either block a correct edit or invite someone to claim it falsely. Parity against your own before-measurement is the honest bar.
  - Observed evidence: THE AMENDED RULE 4 (spec `25kzda`, section 5.4), with the requested order inserted between dependency depth and Set:

```
4. Execute sequentially by default. Among simultaneously ready independent nodes, sort by dependency
depth, THE ORDER THE OPERATOR REQUESTED (the frozen queue position), type rank (`spec`, `backlog`,
`ipd`, `prompt`), Set, numeric Order, stable ID, then canonical path. The requested order ranks BELOW
dependency depth and ABOVE Set, so a declared edge still outranks it (rule 5) while `aw <host> run A B`
runs A before B whenever both are independent and ready. Amended 2026-09-03 on the maintainer's
ruling, implemented by `runorder` plan `prpipy`: ...
```

    BESIDE THE NEW KEY, agreeing FIELD FOR FIELD:

    | Spec rule 4 rank | `queue_sort_key` element |
    |---|---|
    | dependency depth | `dependency_depth(item["id6"], by_id)` |
    | the order the operator requested (frozen queue position) | `item.get("position", 0)` |
    | type rank (`spec`, `backlog`, `ipd`, `prompt`) | deliberately unimplemented, documented in the docstring and in this plan's Deferred section (queue is IPD-only, so it would be untestable dead code) |
    | Set | `str(item.get("setid") or "")` |
    | numeric Order | `item.get("order") if isinstance(...) else 999` |
    | stable ID | `item["id6"]` |
    | canonical path | not reached; `id6` is already unique in a queue |

    THE DECLARED-EDGE PRECEDENCE IS STATED IN THE SPEC TEXT, not implied: rule 4 says "The requested order ranks BELOW dependency depth and ABOVE Set, so a declared edge still outranks it (rule 5)", and rule 5 was restated symmetrically so the new rank is covered by the same guarantee rather than left to inference:

```
5. Explicit declared dependencies always win. The requested order and Set/Order are only
deterministic tiebreakers among nodes already ready; neither a lower Order nor an earlier requested
position can make an unsatisfied node runnable, and neither a higher Order nor a later requested
position can delay an otherwise independent prerequisite relationship.
```

    A NEW RULE 5a was added for the announcement half, so E-04/E-07's behavior is specified rather than being undocumented code:

```
5a. Any divergence between the requested order and the executed order MUST be announced at queue
build, before the first host session, naming both orders and, per moved item, whether a declared
dependency or a lower-ranked tiebreaker caused the move. The executed order is announced whether or
not it diverged, and the comparison is recorded in durable run state, so the order is auditable from
the run record rather than reconstructible from event timestamps.
```

    `AW CHECK` BEFORE AND AFTER, compared programmatically (base = a detached worktree at the pre-change HEAD `5eeee9be`, not a re-run of the same tree), as a full `(location, rule)` set rather than a count:

```
BEFORE findings: 30
AFTER  findings: 30
spec-file BEFORE: (none)
spec-file AFTER : (none)
IDENTICAL SET: True
added: []
removed: []
```

    The finding set is BYTE-IDENTICAL and, specifically, ZERO findings name the amended spec file before or after. As the item instructs, "clean" was NOT the bar: the repo carries 30 pre-existing findings (`check.lifecycle-transition-invalid`, `check.name-nonconformant`, `check.setid-collision`, `check.from-backlog-dangling`, `check.from-backlog-gate-mismatch`), none of them mine and none of them touched. The spec's `## Workflow history` entry was written by the tool (`aw specs note`), not by hand, and the spec's `Status` remains `approved` since this records a maintainer ruling rather than reopening review.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 7 E-leaves across 3 task groups, under the thresholds. One concern throughout: make the executed order match what the operator expressed, and make any order the runner chooses for itself visible. Right-sizing re-assessed at review per E-item rather than by count: each of the seven names one deliverable with one test surface (E-01 the failing regression, E-02 the key plus its docstring, E-03 the inverted test, E-04 the shared formatter plus the oc wiring, E-05 the renderer sort, E-06 the spec text, E-07 the agy wiring). E-04 is the densest because the formatter and its first caller are one indivisible pass (a formatter with no caller cannot be demonstrated), which is why its V-item demands five separate pieces of evidence.

Open questions: OQ-01 (prompt or print) is non-blocking with the announcement implemented either way. No blocking question remains; the design was ruled by the maintainer on 2026-09-01 and this plan implements that ruling rather than reopening it.

This plan is `to-review` and requires explicit human approval before execution. It changes user-visible ordering behavior and a spec rule, so the review should confirm the spec amendment (E-06) matches the intent.

Scope fence: touch ONLY `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/render_stream.py`, `tests/test_runner_item_dependencies.py`, the new `tests/test_run_order_announcement.py`, and the `25kzda` spec file for rule 4. `agy_runipd.py` was ADDED at review by maintainer ruling (E-07): the announcement and preview sites are per-runner even though the sort key is shared, so an oc-only fix would ship a known divergence. Do NOT add a second `queue_sort_key` to `agy_runipd.py`, and do NOT copy the announcement's message text into `agy_runipd.py` - call the ONE shared formatter. Do NOT change dependency SEMANTICS: `dependency_depth` stays FIRST in the key, so a declared edge must keep winning. Do NOT make `position` mutable. Do NOT add a prompt that a child process could inherit. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt).

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. The load-bearing evidence here is the FAILING-FIRST regression and the inverted existing test: a green suite alone proves nothing, since the suite was green while the inversion was shipping. Do NOT describe E-03's inversion as a fix to a broken test; it is an intended contract change.

Execution contract: `oc_runipd.py` and `agy_runipd.py` are the highest-contention files in the repo (measured at review: 11 other unexecuted plans declare `oc_runipd.py` and 9 declare `agy_runipd.py`, including 7 `reviewed` `lanectn` plans and both `rununify` children), and `render_stream.py` was committed by another session earlier today (`a396cb1b`). RE-READ all three immediately before editing and locate code BY SYMBOL, not by the line numbers in this plan. Commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
