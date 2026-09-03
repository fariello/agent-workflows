# IPD: honor the operator's typed run order and announce every reordering

- Date: 2026-09-03
- Kind: child
- Concern: `aw oc run A B` silently executes B first. The operator's typed sequence IS recorded (as `position`) and is then discarded at dispatch: `queue_sort_key` (`oc_runipd.py:3614`) returns `(dependency_depth, setid, order, id6, position)`, so with two independent plans in different Sets the depths tie at 0 and `setid` decides ALPHABETICALLY. Measured from run `run-20260901T042331Z-118022`: the maintainer typed `aw oc run m73aet 6lu3rq`, the queue was built correctly (`position 1 m73aet` / `position 2 6lu3rq`), and `events.jsonl` shows `6lu3rq` started at 04:23:31 and `m73aet` at 04:44:10, because `"runmixed" < "runtrail"`. Nothing announced the inversion; the only way to discover it was to compare `events.jsonl` timestamps against `state.json` positions after the fact. This is a CORRECTNESS bug rather than a cosmetic one because a documented prerequisite ordering exists TODAY: `wlxkoz`'s review requires `m73aet` to land first (4 of its 13 `RUN-*` codes need the commit trailers `m73aet` adds), and `aw oc run m73aet wlxkoz` would silently invert it since `"runcodes" < "runtrail"`.
- Scope: Make the typed order authoritative among equally-ready nodes, and make EVERY divergence between the expressed order and the executed order LOUD. Two inseparable parts per the maintainer's ruling: (A) move `position` above `setid` in the single shared `queue_sort_key`, keeping `dependency_depth` FIRST so a declared edge always beats a typed sequence; (B) announce the execution order at queue build unconditionally, and warn distinctly when it differs from the expressed order, naming both orders and the specific causing edge per moved item. Also fixes the misleading preview and amends the spec rule this changes. Excludes any change to dependency SEMANTICS (a declared edge must keep winning), excludes making `position` mutable, and excludes prompting from anywhere a child process can inherit a TTY.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/render_stream.py, tests/test_runner_item_dependencies.py, tests/test_run_order_announcement.py, .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Set: runorder
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: prpipy
- Blocks-Release: next
- From-Backlog: xvx8ez

## Workflow history

- 2026-09-03 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-101..PR-105; GO - PENDING HUMAN APPROVAL. Verified at HEAD `25d3f0b0`, tree clean, plan committed and unchanged, so the pre-review snapshot was correctly skipped. `aw ipd lint --phase author` conforming before and `--phase review-finalize` conforming after. The plan's central claim RE-MEASURED AND TRUE, not taken on trust: `queue_sort_key` at `oc_runipd.py:3596` really does return `(dependency_depth, setid, order, id6, position)`; `agy_runipd.queue_sort_key is oc_runipd.queue_sort_key` is True at this HEAD; and run `run-20260901T042331Z-118022` really does show `selectors ['m73aet','6lu3rq']` with `position 1 m73aet`/`position 2 6lu3rq` in `state.json` while `events.jsonl` has `6lu3rq` `ipd-started` at 04:23:31 and `m73aet` at 04:44:10. THE DOMINANT FINDING (PR-101, HIGH, fixed by maintainer ruling): the plan was ONE-SIDED. The sort-key fix is genuinely shared, but the announcement belongs in `initialize_run` and the preview in `print_status`, and BOTH are separately defined per runner (`agy_runipd.print_status is oc_runipd.print_status` -> False; agy has its own `--prepare-only` at `agy_runipd.py:4691`), while `agy_runipd.py` was NOT in Scope-Paths - so `aw agy run` would have received the corrected ordering and neither the announcement nor the preview fix, which is precisely the one-sided-fix pattern the `rununify` Set exists to remove. MAINTAINER RULED widen to both drivers now, with the message text from ONE shared formatter in `render_stream.py`; added `agy_runipd.py` to Scope-Paths, added E-07, and required both drivers' output as evidence in V-04/V-05. Also FIXED: (PR-102) E-04 said "announce at queue build" without naming the site, and the only correct site is `initialize_run` (`oc_runipd.py:2860`, `agy_runipd.py:1920`) where `position` is assigned at `:2930`/`:1990`; named it, and named the expressed order's actual source (`state["selectors"]`, `initialize_run`'s `queue_ids`), which the plan never identified. (PR-103) the plan asserted the operator's typed order is what `position` records, but `expand_selectors` (`:2519`) expands a SETID or `all` into many positions, so `position` is only the TYPED order for the literal-id6 case; recorded, because E-04's "expressed order" must not claim to be typed when it was expanded. (PR-104) `--prepare-only` renders `state.get("queue")` in stored order (`render_stream.py:903`, `:929`) with no sort, confirming F-5 at the source. (PR-105) V-06 demanded `aw check` clean for the spec file, which is not achievable as stated (the repo carries 13 pre-existing `aw check plans` errors); restated as before/after parity. One decision recorded in the typed review record (D-1, reversible).
- 2026-09-03 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): graduated from backlog `xvx8ez`, which the maintainer had already decided in full on 2026-09-01, so nothing here is a fresh design proposal: the ruling (move `position` above `setid`), its safety argument (`dependency_depth` stays first, so a declared edge still wins), the mandatory second half (announce every reordering loudly), the three implementation traps, and the TTY constraint all come from the item. Authored review-ready, not draft. FOUR THINGS RE-VERIFIED OR FOUND AT AUTHORING rather than trusted from the item. (1) `agy_runipd.queue_sort_key IS oc_runipd.queue_sort_key` confirmed True at this HEAD, so one edit covers both drivers. (2) An EXISTING TEST WILL INVERT: `test_set_order_still_breaks_ties_among_equally_ready_nodes` (`tests/test_runner_item_dependencies.py:745`) builds `bbbbbb` at order=2/position=1 and `aaaaaa` at order=1/position=2 and asserts `["aaaaaa","bbbbbb"]`; under the fix `position` decides and the correct answer becomes `["bbbbbb","aaaaaa"]`. That test must be deliberately INVERTED with its reason recorded, never quietly deleted. (3) The preview bug is confirmed at the source: `print_status` (`oc_runipd.py:6141`) passes `state` straight to `render_run_summary_table` (`render_stream.py:875`) and NO sort is applied, so `--prepare-only` (`:6556`) shows position order and would have shown `01 m73aet, 02 6lu3rq` while still running `6lu3rq` first. (4) NEW FINDING the item does not record, added as F-7: ordering is computed BEFORE status is consulted, so a queue mixing `to-review` and `approved` plans interleaves review passes and code execution in alphabetical Set order, and `dependency_depth` still ranks a plan depth-1 when it is only being REVIEWED, where the prerequisite does not apply.

## Goal

Make `aw oc run A B` run A then B, and make any order the runner chooses for itself visible at the moment it chooses it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the bug, then fix the ordering

- [ ] E-01 Write the failing-first regression BEFORE touching the key, reproducing the measured case exactly: two independent plans whose Set ids sort OPPOSITE to the typed order (the real case was `runtrail` typed first while `runmixed` sorts first alphabetically), asserting dispatch follows the TYPED order. It must FAIL at current HEAD. Add, in the same file, the guard that stops this fix from breaking the property spec 25kzda 5.4 rule 5 protects: a DECLARED `Item-Dependencies` edge must still win over a contradicting typed order.
  - Depends on: none
  - Expected outcome: a test that fails at HEAD naming both orders, plus a passing declared-edge-wins test. Paste the failure.
  - Execution state: pending

- [ ] E-02 Change the ONE shared `queue_sort_key` (`oc_runipd.py:3596`) from `(dependency_depth, setid, order, id6, position)` to `(dependency_depth, position, setid, order, id6)`. VERIFIED at authoring: `agy_runipd.queue_sort_key is oc_runipd.queue_sort_key` returns True (re-exported, not reimplemented), so do NOT introduce a second copy. Rewrite the docstring in the same edit: it currently says "`position` is LAST and is a stable identity, never a priority", which this change makes FALSE, and it claims the sort is deterministic from artifact content alone, which stops being true once invocation order is an input. Both statements must be corrected honestly rather than left to mislead the next reader. PRESERVE the docstring's underlying point, which still holds: `position` is also the key for outcome/prompt/session filenames and this run's decision ids, so it must remain FROZEN at queue-build time. Making it a sort input must not make it mutable.
  - Depends on: E-01
  - Expected outcome: E-01's regression passes, the declared-edge test still passes, and the docstring states the new contract including the invocation-order dependency.
  - Execution state: pending

- [ ] E-03 Handle the EXISTING TEST THIS INVERTS, deliberately and visibly. `test_set_order_still_breaks_ties_among_equally_ready_nodes` (`tests/test_runner_item_dependencies.py:745`) constructs `bbbbbb` (order=2, position=1) and `aaaaaa` (order=1, position=2) and asserts `["aaaaaa", "bbbbbb"]` with the message "Order 1 precedes Order 2 on a tie". Under the fix `position` outranks `order`, so the correct expectation becomes `["bbbbbb", "aaaaaa"]`. INVERT it, do NOT delete it, and record in the test itself that the inversion is the intended consequence of this plan plus the id6, following the repo's precedent of pinning a behavior so a later phase must deliberately come and change it. Then check the whole file for any other assertion that depends on `order` outranking `position` and treat each the same way.
  - Depends on: E-02
  - Expected outcome: the inverted test passes with its reason recorded in-file; a stated list of every other assertion in that file examined, with each either unaffected or inverted-with-reason. A test deleted rather than inverted FAILS this item.
  - Execution state: pending

### Task group 2: make the order visible (the half that is not optional)

- [ ] E-04 Build the SHARED order-announcement FORMATTER in `render_stream.py`, as a pure function, and call it from the OpenCode driver's queue build. It ALWAYS renders the execution order, whether or not anything was reordered, so the order is auditable in the log rather than reconstructible from `events.jsonl` timestamps. When the executed order DIFFERS from the order the operator expressed it renders a distinct WARNING naming BOTH orders and, per moved item, the SPECIFIC reason. A bare "reordered" line is not acceptable: the operator must be able to distinguish a DECLARED prerequisite (correct and expected, e.g. "6lu3rq before m73aet: 6lu3rq declares `executed:m73aet`") from an arbitrary TIEBREAK, which is the case that bit them. Record the announcement in the run's durable state/events too, so a later reader sees it without terminal scrollback; `events.jsonl` currently carries `ipd-started` timestamps and no ordering rationale at all.
  MEASURED AT REVIEW so the executor does not have to locate the seam: the ONLY correct site is `initialize_run` (`oc_runipd.py:2860`), because that is where `position` is assigned (`for position, id6 in enumerate(queue_ids, start=1)` at `:2930`) and where the queue is frozen into `state`. The EXPRESSED order is `queue_ids` as returned by `expand_selectors` (equivalently `state["selectors"]` for the literal-id6 case); the EXECUTED order is that same list re-sorted by `queue_sort_key`. Neither the plan nor the item named either source, and getting the expressed order from the wrong place is the one way this item can silently produce a truthful-looking but wrong message.
  WORD THE MESSAGE HONESTLY about what "expressed" means (PR-103): `position` is the OPERATOR'S TYPED order only when the selectors were literal id6 tokens. `expand_selectors` (`:2519`) also accepts a SETID, `all`, `reviews`, and a file path, and each expands to MANY positions whose order comes from the manifest, not from the operator's typing. So the announcement must NOT claim "you typed" for an expanded selection; say "requested order" and reserve any typed-order phrasing for the literal case, or the message misinforms in exactly the direction that erodes trust in it.
  - Depends on: E-02
  - Expected outcome: a pure formatter in `render_stream.py` with no runner import; the OpenCode driver prints its execution order on EVERY run; a reordered run prints a warning naming both orders and a per-item cause that distinguishes a declared edge from a tiebreak; the rationale is present in durable run state, shown by reading it back; the message does not claim a typed order for an expanded selector.
  - Execution state: pending

- [ ] E-05 Fix the PREVIEW, which is a second defect and would have hidden this bug from a careful operator. MEASURED at authoring and RE-CONFIRMED at review: `print_status` (`oc_runipd.py:6141`) passes `state` directly to `render_run_summary_table` (`render_stream.py:875`) with NO sort applied, and the renderer iterates `state.get("queue", [])` in STORED order (`render_stream.py:903`, `:929`), printing `item.get("position", idx + 1)` as the leading column. So `--prepare-only` (`:6556`) renders POSITION order. That is why a preflight check would have shown `01 m73aet, 02 6lu3rq` and still executed `6lu3rq` first. Make the table show EXECUTION order, or show both explicitly labelled; a column a reader will read as sequence must not display identity. Note that once `position` drives the sort these agree in the common case BY CONSTRUCTION, so CONFIRM the fix on a case where a declared edge forces a divergence rather than assuming the problem disappeared.
  DO THE SORT IN THE SHARED RENDERER, not in one driver's `print_status`: `render_run_summary_table` is already shared and is called by BOTH drivers' `print_status`, so fixing it there fixes both hosts in one edit and cannot drift. If the renderer cannot reach `queue_sort_key` without importing a runner, sort in each driver before calling it and state that explicitly, because a renderer importing a runner would be a new layering defect.
  - Depends on: E-04
  - Expected outcome: `--prepare-only` shows the order the run will actually execute in, demonstrated on a queue where a declared edge makes execution order differ from position order, and demonstrated for BOTH drivers; no runner import was added to `render_stream.py`.
  - Execution state: pending

- [ ] E-07 Land the SAME announcement and the SAME preview behavior in the ANTIGRAVITY driver, so the fix is not one-sided. MAINTAINER RULING 2026-09-03 at review: widen to both drivers now. THIS IS NOT OPTIONAL POLISH, and the reason is measured: `queue_sort_key` IS shared (`agy_runipd.queue_sort_key is oc_runipd.queue_sort_key` -> True, so E-02 alone changes agy's ORDERING), but `initialize_run` and `print_status` are NOT (`agy_runipd.print_status is oc_runipd.print_status` -> False; agy defines its own at `agy_runipd.py:4331` and its own `--prepare-only` at `:4691`, with its own `initialize_run` at `:1920` assigning `position` at `:1990`). Without this item `aw agy run` would silently get the reordering and NEITHER the announcement nor the corrected preview, which is exactly the divergence class the `rununify` Set exists to remove and which this repo has already been bitten by (`Heartbeat`/`stallfp-01`).
  CALL THE SHARED FORMATTER E-04 built; do NOT re-implement the message text in `agy_runipd.py`. A second copy of the wording would be a fresh re-fork of the kind `tests/test_render_stream.py:539` already guards against on the oc side. Keep agy's own host label (`driver_label="antigravity"`) exactly as `print_status` supplies it today.
  - Depends on: E-04, E-05
  - Expected outcome: `aw agy run` prints its execution order on every run, prints the same distinguishable reorder warning, and its `--prepare-only` shows execution order; the message text comes from the ONE shared formatter (proved by object identity or by a single-definition check), not a copy.
  - Execution state: pending

### Task group 3: keep the spec and the code in agreement

- [ ] E-06 Amend spec `25kzda` 5.4 rule 4, which this plan CHANGES. It currently reads (`:826`): "Among simultaneously ready independent nodes, sort by dependency depth, type rank (`spec`, `backlog`, `ipd`, `prompt`), Set, numeric Order, stable ID, then canonical path" - and says nothing about operator order, which is why the runner was behaving to spec and the SPEC is what needed a decision. Insert the operator's expressed order between dependency depth and Set, and state explicitly that a declared edge still outranks it. Do NOT implement a divergence from an unamended spec and leave the two disagreeing. Record the maintainer's 2026-09-01 ruling as the authority.
  - Depends on: E-02
  - Expected outcome: rule 4 names the operator's order in its correct rank, with the declared-edge precedence stated; the spec and `queue_sort_key` agree, shown side by side.
  - Execution state: pending

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

## Spec / documentation sync

- Spec `25kzda` 5.4 rule 4 (`:826`) MUST be amended by E-06; code and spec must not be left disagreeing.
- `queue_sort_key`'s docstring is itself documentation of the contract and is rewritten by E-02.
- If any user-facing doc describes `aw oc run`'s ordering, update it; otherwise state N/A with the paths checked.

## Open questions

### OQ-01: Should the announcement ever PROMPT, or is printing enough?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT BLOCKING, because E-04 delivers the safety property either way and a prompt can be added later without redoing it. The maintainer's 2026-09-01 requirement said reordering must be announced "LOUDLY, and possibly interactively", leaving the prompt optional. This plan implements the announcement only, and the reason is the hard constraint recorded in the item: a nested `aw` that inherits a TTY once wedged a finalize for 1h49m, so any prompt must live in the DRIVER at queue-build time before the first child spawns and must degrade to non-interactive with no TTY, or an unattended overnight run can block for hours. If you want the prompt, say so and it becomes its own E-item under those constraints.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new regression FAILING at pre-change HEAD, showing the typed order and the actual (inverted) order, with Set ids that sort opposite to the typed sequence so the test reproduces the measured case rather than a synthetic one. Paste the declared-edge-wins test passing at that same pre-change HEAD, which proves it is a genuine guard and not an artifact of the fix. A regression never observed failing is not accepted.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new key. Paste E-01's regression now passing and the declared-edge test still passing. Paste `agy_runipd.queue_sort_key is oc_runipd.queue_sort_key` -> True AFTER the edit, proving no second copy was introduced. Paste the rewritten docstring, showing it no longer claims `position` is never a priority and no longer claims determinism from artifact content alone. Paste `test_position_is_never_renumbered_by_ordering` still green, proving identity did not become mutable.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the inverted test with its in-file reason and id6 reference, plus its passing output. Paste `test_missing_order_key_still_sorts` still green. ENUMERATE every other assertion in `tests/test_runner_item_dependencies.py` that touches ordering, stating for each whether it was unaffected or inverted-with-reason. If any test was DELETED rather than inverted, this item FAILS.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste an UNREORDERED run printing its execution order (proving the print is unconditional). Paste a REORDERED run printing both orders plus the per-item cause, and show the cause names the specific declared edge (e.g. "declares `executed:<id6>`") rather than a bare "reordered". Paste a TIEBREAK case whose message is DISTINGUISHABLE from the declared-edge case, since telling those two apart is the operator-facing point. Then paste the durable record read back from run state/events, since terminal output alone does not satisfy this item. Paste the formatter's definition site showing it lives in `render_stream.py` and imports NEITHER runner. Finally paste an EXPANDED-SELECTOR case (a setid or `all`, not literal id6 tokens) showing the message does NOT claim the operator typed that order (PR-103).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `--prepare-only` output for a queue where a DECLARED EDGE makes execution order differ from position order, showing the table reflects EXECUTION order (or shows both, labelled). A demonstration on a queue where the two coincide does NOT satisfy this item, because that is exactly the case the bug already looked correct in. Paste `rg -n "import" agent_workflows/render_stream.py` (or an AST check) showing no runner import was introduced.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the ANTIGRAVITY driver's own output for all three cases V-04 and V-05 require of the OpenCode driver: an unreordered run printing its order, a reordered run with a per-item cause, and `--prepare-only` showing execution order on a declared-edge queue. Then PROVE the wording is shared rather than copied: paste a package-wide check that the announcement formatter has exactly ONE definition (AST-based, across `agent_workflows/*.py`, following the precedent at `tests/test_render_stream.py:565`), and paste an identity assertion tying both drivers to it. A pasted agy output alone does NOT satisfy this item, because a copied message string would produce identical output while re-creating the divergence.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the amended spec rule 4 beside the new `queue_sort_key` tuple, showing they agree field for field, and that the declared-edge precedence is stated in the spec text rather than implied. Paste `aw check` BEFORE and AFTER the spec edit and show the finding set is UNCHANGED for this file. Do NOT require "clean": the repo carries pre-existing `aw check plans` errors (13 at the time of review, recorded in several sibling plans' histories), so "clean" is unachievable and would either block a correct edit or invite someone to claim it falsely. Parity against your own before-measurement is the honest bar.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 7 E-leaves across 3 task groups, under the thresholds. One concern throughout: make the executed order match what the operator expressed, and make any order the runner chooses for itself visible. Right-sizing re-assessed at review per E-item rather than by count: each of the seven names one deliverable with one test surface (E-01 the failing regression, E-02 the key plus its docstring, E-03 the inverted test, E-04 the shared formatter plus the oc wiring, E-05 the renderer sort, E-06 the spec text, E-07 the agy wiring). E-04 is the densest because the formatter and its first caller are one indivisible pass (a formatter with no caller cannot be demonstrated), which is why its V-item demands five separate pieces of evidence.

Open questions: OQ-01 (prompt or print) is non-blocking with the announcement implemented either way. No blocking question remains; the design was ruled by the maintainer on 2026-09-01 and this plan implements that ruling rather than reopening it.

This plan is `to-review` and requires explicit human approval before execution. It changes user-visible ordering behavior and a spec rule, so the review should confirm the spec amendment (E-06) matches the intent.

Scope fence: touch ONLY `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/render_stream.py`, `tests/test_runner_item_dependencies.py`, the new `tests/test_run_order_announcement.py`, and the `25kzda` spec file for rule 4. `agy_runipd.py` was ADDED at review by maintainer ruling (E-07): the announcement and preview sites are per-runner even though the sort key is shared, so an oc-only fix would ship a known divergence. Do NOT add a second `queue_sort_key` to `agy_runipd.py`, and do NOT copy the announcement's message text into `agy_runipd.py` - call the ONE shared formatter. Do NOT change dependency SEMANTICS: `dependency_depth` stays FIRST in the key, so a declared edge must keep winning. Do NOT make `position` mutable. Do NOT add a prompt that a child process could inherit. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt).

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. The load-bearing evidence here is the FAILING-FIRST regression and the inverted existing test: a green suite alone proves nothing, since the suite was green while the inversion was shipping. Do NOT describe E-03's inversion as a fix to a broken test; it is an intended contract change.

Execution contract: `oc_runipd.py` and `agy_runipd.py` are the highest-contention files in the repo (measured at review: 11 other unexecuted plans declare `oc_runipd.py` and 9 declare `agy_runipd.py`, including 7 `reviewed` `lanectn` plans and both `rununify` children), and `render_stream.py` was committed by another session earlier today (`a396cb1b`). RE-READ all three immediately before editing and locate code BY SYMBOL, not by the line numbers in this plan. Commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
