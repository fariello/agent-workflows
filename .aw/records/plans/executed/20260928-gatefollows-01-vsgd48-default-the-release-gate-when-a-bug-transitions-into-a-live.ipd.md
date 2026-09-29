# IPD: Default the release gate when a bug TRANSITIONS into a live status, not only when its Work-Kind changes

- Date: 2026-09-28
- Kind: child
- Concern: `backlog.decide_gate_default` is consulted only when `--work-kind` is passed, so an ungated `bug` that becomes LIVE by a pure STATUS transition (`parked -> open`, `done -> open`, `open -> graduated`) keeps no gate and immediately trips the shipped `check.live-bug-ungated` ERROR that the same predicate exists to prevent.
- Scope: Add the STATUS-transition call site to both spellings of `aw backlog set`, through the existing shared predicate, and pin all four routes (the two already-working reclassification routes and the two currently-broken transition routes) with tests. No new policy, no new field, no change to `decide_gate_default`'s four conditions.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/status_set.py, tests/test_backlog_gate_follows_status.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: 98zlut
- Blocks-Release: next
- Set: gatefollows
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: vsgd48

## Workflow history
- 2026-09-29 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: vsgd48 verified (set gatefollows, attempt 1).
- 2026-09-29 approved (aw set): status set to approved
- 2026-09-28 reviewed (aw set): /plan-review round 1 complete: APPROVE WITH REVISIONS APPLIED; PR-901 through PR-907 all FIXED; review record written; review-finalize lint conforming.

- 2026-09-28 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901 through PR-907 all FIXED. Review record `.aw/records/reviews/20260928-gatefollows-01-vsgd48-default-the-release-gate-when-a-bug-transitions-into-a-live.review.md` Round 1.
  THE DIAGNOSIS IS CORRECT AND EVERY ROUTE REPRODUCED, ON BOTH SPELLINGS. Driven end to end at review through `backlog.run_set` and through the real CLI for the positional spelling: route (a) `chore -> bug` while `open` writes `- Blocks-Release: next` and announces it (F-01/F-02 hold); routes (b) `open -> graduated`, (c) `parked -> open` and (d) `done -> open` each write NO gate, print no notice, and each leaves a tree on which `check_engine.check_live_bug_gate` returns `['check.live-bug-ungated']` (F-03/F-04/F-05 hold, on BOTH spellings). F-07 (zero gateless live bugs repo-wide) and F-10 (no test anywhere touches `decide_gate_default`) both re-confirmed. The plan's correction of the backlog item's diagnosis is sound and its refusal to claim the item's unreproducible regrowth measurement is the right call.
  THE INSTRUCTION THAT COULD NOT BE FOLLOWED AS WRITTEN (PR-901, HIGH, F-13): E-02 told the executor to pass "the record's existing parsed `- Work-Kind:`" on the positional path, and no such value exists there. `status_set.apply_status_change`'s only work-kind binding is `getattr(args, "work_kind", None)`, i.e. the FLAG, which is exactly `None` in the status-only case this plan exists to cover; nothing on that path parses the record's own field and `rec` exposes no such attribute. The failure mode is silent: `kind=None` makes the predicate decline on condition 1, so the fix would appear to land and do nothing on one of the two spellings, which is the precise "fires for one spelling and not the other" outcome the plan's own Step-0 note calls worse than not shipping. E-02 now names `backlog.parse_item(...).kind`, explains the asymmetry with E-01 (which already has `item` in scope), and V-02 requires pasting the read.
  THE UNDISCLOSED BLAST RADIUS (PR-902, HIGH, F-12): gating an item at `graduated` changes what a LATER close does. Measured, an ungated bug taken `open -> graduated -> done` closes silently today; with the gate present, `set done` exits `rc=1` with "refused: backlog item carries Blocks-Release 'next'" and demands a handoff, evidence, or an explicit de-gate. The refusal is CORRECT policy, which is why this is a disclosure finding and not a blocker, but the plan asserted a two-call-site change with no workflow impact and nothing in it mentioned that a previously-silent path becomes interactive for every graduated bug. Now recorded in E-01, the Scope check, new OQ-02 and V-04.
  THE MISSING FIFTH ROUTE (PR-903, HIGH, F-11): `blocked` is live (the live set is exactly `['blocked','graduated','open']`), creation already gates it, and transitions INTO it leave no gate and trip the same ERROR, yet E-03's four-route table omitted it entirely, so a third of the fix's own surface would have shipped untested. It also needs `--gate-kind` and `--gate-ref` or the setter exits `rc=2` writing nothing, which would have made a naively-appended row pass for the wrong reason. E-03 now covers five routes with those flags called out.
  FOUR SMALLER CORRECTIONS. E-04's three negatives all already hold, so it is a fence and must not claim a pre-fix failure (PR-904, F-16). V-03 instructed `git stash` in a SHARED CHECKOUT, which AGENTS.md forbids because a stash can discard a co-worker's uncommitted work; the pre-fix contrast must be taken in memory instead (PR-905). The plan recorded no suite baseline while asking for a full-suite no-regression proof, so re-driven here as `3115 passed, 2 skipped, 3 warnings`, zero failures, with all four named regression files confirmed present (PR-906, F-14). F-06 cited `RULE_SPECS`, which does not exist; the symbol is `RULE_REGISTRY` and the severity claim itself reproduces exactly (PR-907, F-15).
  NO BLOCKING QUESTION REMAINS and no finding is left OPEN or DEFERRED, so nothing is escalated. OQ-01 was re-verified and survives unchanged. The plan's five `Carrier-Declined` rows were each checked against evidence and all five are legitimate: in particular the backfill row's "empty population" claim re-measured as zero, and the hand-authoring row's "already discharged" claim is correct since a write-path default structurally cannot cover a route that never calls a write path.
- 2026-09-28 draft (opencode): created.
- 2026-09-28 to-review (opencode): authored from backlog `98zlut`; re-measured the item's hypothesis, corrected its diagnosis (the reclassification route it names is already shipped and works; the STATUS-transition route is the live hole), and scoped to that hole.

## Goal

Make the release gate FOLLOW a bug into a live status, so that an ungated `bug` item reaching `open`, `blocked`, or `graduated` through `aw backlog set` is gated by the same shared predicate that already gates it at creation and on reclassification. Today two of the four routes into "live and ungated" are uncovered, and each of them manufactures an item that the shipped `check.live-bug-ungated` rule reports as an ERROR on the very next `aw check`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: wire the status-transition call site into both spellings

- [x] E-01 In `backlog.run_set`, broaden the gate-default consultation so it also fires when the item is transitioning INTO a live status. Replace the guard `if set_work_kind is not None and br is None:` with one that fires when `br is None` AND (`set_work_kind is not None` OR the item is becoming live), passing `kind=set_work_kind or item.kind` and `status=new_status` to `decide_gate_default`, and keeping `existing_blocks_release=item.blocks_release` so an item that already carries a gate is untouched. Write through `releases.set_blocks_release_line` and announce with the existing `sys.stdout.write(f"aw backlog set: {gate_default_notice}\n")` line. Do NOT alter `decide_gate_default` itself: its condition 3 already declines `done` and `parked`, so the broadened guard needs no status allowlist of its own.
  THE GATE WRITE MUST STAY BEFORE THE CLOSE-LEGITIMACY GATE, AND IT ALREADY DOES: verified at review that `run_set`'s gate-default block precedes its `evaluate_blocking_close` call in the same function, and that gate reads `rendered`, which the gate write mutates. Keep that order. Moving the new consultation after the close gate would let a same-call `done` transition be judged against a pre-write body.
  - Depends on: none
  - Expected outcome: `aw backlog set --status graduated <ungated-bug>` writes `- Blocks-Release: next` and prints the `defaulted - Blocks-Release: next` notice, where before it printed only the `-> graduated` line. `aw backlog set --status done <ungated-bug>` still writes no gate.
  DISCLOSE THE DOWNSTREAM WORKFLOW CONSEQUENCE, WHICH IS REAL, INTENDED, AND NOT MENTIONED ANYWHERE ELSE IN THIS PLAN. Gating an item at `graduated` changes what a LATER close does. MEASURED AT REVIEW 2026-09-28, end to end through `backlog.run_set`: an ungated bug taken `open -> graduated -> done` today closes cleanly (`rc=0`, no refusal); with the gate present at `graduated`, the same `set done` REFUSES with `rc=1` and "refused: backlog item carries Blocks-Release 'next'; closing it `done` would silently drop that release gate", offering the three shipped remedies (hand off to a plan via `--from-backlog`, cite `--evidence`, or de-gate with `--blocks-release -`). That refusal is CORRECT and is exactly the close-legitimacy policy AGENTS.md describes, so this is not a defect to avoid; but it means this plan makes a previously-silent close path interactive for every graduated bug, which is a behavior change a reviewer and a maintainer must see stated rather than discover. Record it in the code comment beside the new call site so the next reader meets it there too.
  - Execution state: performed

- [x] E-02 Mirror E-01 in `status_set.apply_status_change` for the positional spelling. Broaden its existing guard (`work_kind is not None and rec.record_type == "backlog" and getattr(args, "blocks_release", None) is None`) to also fire on a status-only transition, passing `kind=work_kind` or the record's existing `- Work-Kind:` when the flag is absent, and `status=norm_status`.
  THERE IS NO "EXISTING PARSED `- Work-Kind:`" ON THIS PATH, SO THE EXECUTOR MUST CREATE THE READ, AND THIS IS THE ONE INSTRUCTION IN THIS PLAN THAT CANNOT BE FOLLOWED AS WRITTEN. MEASURED AT REVIEW 2026-09-28: `status_set.apply_status_change`'s ONLY work-kind binding is `work_kind = getattr(args, "work_kind", None)`, which is the FLAG, and it is exactly `None` in the status-only case this item exists to cover. `rg -n "Work-Kind" agent_workflows/status_set.py` returns five hits, all comments or the `set_work_kind_line` WRITE; nothing parses the record's own value, and `rec` carries no such attribute. So an executor who reads "the record's existing parsed `- Work-Kind:`" will look for a binding that does not exist. USE THE SHIPPED READER: `backlog.parse_item(<text>).kind`, which is the same accessor `backlog.run_set` already uses to obtain `item.kind` (driven at review: `backlog.parse_item("- Work-Kind: bug\n...").kind == 'bug'`). Read it from the CURRENT text of the record on this path, and note that `parse_item` also resolves the legacy `- Kind:` fallback (`item.kind = work_kind if work_kind is not None else legacy_kind`), which is a reason to prefer it over a fresh local regex. Do NOT add a second parser for this field: the predicate's "SINGLE AUTHORITY" discipline applies to the READ as much as to the decision.
  NOTE THE ASYMMETRY WITH E-01, WHICH IS WHY THIS ITEM IS NOT A MECHANICAL COPY. `backlog.run_set` already binds `item = parse_item(text)` well before its gate block (verified at review: the assignment precedes the gate block in the same function), so E-01 can write `kind=set_work_kind or item.kind` with no new read. `status_set.apply_status_change` has no equivalent binding, so E-02 must introduce one. An executor who assumes symmetry will either pass `kind=None` (making the predicate decline on condition 1 and the fix silently do nothing on the positional spelling) or invent a regex. Keep the `rec.record_type == "backlog"` guard exactly as-is, for the reason its own comment gives (a plan's `- Work-Kind:` is descriptive, and gating a plan on it "would invent a release obligation from a descriptive edit"). Keep reading the existing gate out of `new_lines` via the current `^- Blocks-Release:` regex so an already-gated item is declined by the predicate.
  - Depends on: E-01
  - Expected outcome: the positional `aw backlog set graduated <ungated-bug>` behaves byte-for-byte like the `--status` spelling from E-01, and a PLAN or SPEC record transitioned through this same function is never gated by a status move.
  - Execution state: performed

### Task group 2: pin every route, positive and negative

- [x] E-03 Add `tests/test_backlog_gate_follows_status.py` covering all FIVE routes into "live and ungated", for BOTH spellings of `aw backlog set`, each asserting on the item's `- Blocks-Release:` line AND on `check_engine.check_live_bug_gate` returning zero findings afterwards: (a) reclassification `chore -> bug` while `open` (already passing, F-01/F-02: this is the regression pin F-10 says does not exist); (b) `open -> graduated` on an ungated bug (F-03); (c) `parked -> open` (F-04); (d) `done -> open` (F-05); (e) a transition into `blocked` (F-11). Each fixture must create a `planned` release record, because `decide_gate_default` condition 2 falls back to ungated when `next` does not resolve.
  `blocked` IS THE FIFTH LIVE STATUS AND THE AUTHORED FOUR-ROUTE TABLE OMITS IT ENTIRELY, WHICH WOULD HAVE SHIPPED A FIX WITH AN UNTESTED THIRD OF ITS OWN SURFACE. The live set is computed as `STATUSES - _GATE_DEFAULT_SKIP_STATUSES`, driven at review as exactly `['blocked', 'graduated', 'open']`, so `blocked` is as live as the two the table does cover, and CREATION already gates it (driven: `aw backlog new --work-kind bug --status blocked` is gated, consistently with `open` and `graduated`). MEASURED AT REVIEW: `parked -> blocked` and `done -> blocked` on an ungated bug BOTH leave no gate and BOTH trip `check.live-bug-ungated`, so this is a real hole of the same shape as (b), (c) and (d), not a theoretical one.
  THE `blocked` ROUTE NEEDS TWO EXTRA FLAGS OR IT REFUSES BEFORE REACHING THE GATE CODE, which is why it cannot simply be appended to the table without a note. Driven at review: `aw backlog set --status blocked <item>` exits `rc=2` with "moving to blocked requires --gate-kind and --gate-ref" and writes nothing at all. The fixture must therefore pass `--gate-kind` and `--gate-ref` (driven working values: `gate_kind='question'`, `gate_ref='<some text>'`), or the test will pass for the wrong reason: it would assert an absent gate on an item the setter never transitioned.
  - Depends on: E-02
  - Expected outcome: a new test module whose (b), (c), (d) and (e) cases FAIL on the pre-E-01 code and PASS after, and whose (a) case passes both before and after.
  - Execution state: performed

- [x] E-04 In the same module, pin the three negative properties, so the broadened guard cannot silently become an over-reach: (a) `aw backlog set open <ungated-bug> --blocks-release -` leaves the item UNGATED (predicate condition 4, explicit value wins); (b) an item already carrying `- Blocks-Release: <id6>` transitioned to another live status keeps THAT value and is not rewritten to `next`; (c) transitioning a bug to `done` and to `parked` writes NO gate (predicate condition 3 / `_GATE_DEFAULT_SKIP_STATUSES`), which also proves the fix cannot manufacture the `check.blocking-item-closed-without-gate` ERROR that condition 3 exists to avoid.
  ALL THREE NEGATIVES ALREADY HOLD AT THIS HEAD, SO THIS ITEM IS A FENCE AND MUST SAY SO IN ITS DOCSTRINGS (F-16). Driven at review: `parked -> open` with `--blocks-release -` leaves the item ungated, and an item pre-gated `rel001` taken `parked -> open` keeps `rel001` rather than being rewritten to `next`. Unlike E-03's (b)/(c)/(d)/(e), these cases do NOT go from red to green, so do not claim a pre-fix failure for them; their value is that they fail if the broadened guard later over-reaches. Note (c) is the one whose protection E-01 must not weaken: condition 3 declining `done`/`parked` is what keeps the fix from manufacturing `check.blocking-item-closed-without-gate`.
  - Depends on: E-03
  - Expected outcome: three negative tests passing, each asserting the ABSENCE or the PRESERVATION of a gate value rather than its presence, and each labelled in its docstring as a FENCE that passes both before and after the fix.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE PREDICATE IS THE SINGLE AUTHORITY AND MUST STAY SO. `backlog.decide_gate_default` documents itself as "THE SINGLE AUTHORITY FOR THE DECISION, deliberately, because it is consumed from THREE call sites that must not drift", naming `run_new`, `run_set`, and `status_set.apply_status_change`. This plan therefore adds a CALL SITE and changes no condition inside the predicate. The backlog item `98zlut` reaches the same conclusion ("this is a new CALL SITE, not new policy").
- BOTH SPELLINGS OF `aw backlog set` MUST BE WIRED OR NEITHER SHOULD BE. `backlog.run_set`'s comment at the E-02 call site states that `aw backlog set` "forks on whether `--status` was PASSED (cli.py): the positional spelling routes HERE, and the `--status` spelling routes to `backlog.run_set`. A default wired into one only would fire for one spelling of one verb and not the other, which is worse than not shipping it because it teaches a false expectation." That constraint is inherited verbatim by this plan: every change lands on both paths.
- THE GATE IS NEVER SILENTLY CLEARED. `backlog.run_set`'s existing comment: "DO NOT REMOVE A GATE WHEN A WORK KIND CHANGES AWAY FROM `bug`: a gate may have been set deliberately for another reason, and silently clearing it would lose a decision." The predicate also declines when the item already carries a gate (its `existing_blocks_release` parameter). Both properties are preserved here.
- A DEFAULTED FIELD MUST BE ANNOUNCED. `backlog.run_new`'s comment records the maintainer's 2026-09-10 ruling on `y4adch` OQ-01 requiring "a VISIBLE notice naming the field, the value applied, and why", because "a field the tool wrote but the author did not type is exactly the hidden behavior that makes a later reader distrust the record". Both existing setter call sites announce via `sys.stdout.write(f"aw backlog set: {notice}\n")`; the new call sites reuse that exact shape.
- `done` AND `parked` ARE SKIPPED BY DESIGN, AND THAT IS WHY THIS HOLE EXISTS RATHER THAN BEING A PREDICATE BUG. `backlog._GATE_DEFAULT_SKIP_STATUSES` is `frozenset(("done", "parked"))`, and condition 3 of the predicate explains each exclusion (a gated `done` item is rejected by `check.blocking-item-closed-without-gate`; a `parked` maybe "is not live work"). The predicate is correct; nothing consults it when only the STATUS moves.
- THE CHECKER AND THE DEFAULT SHARE THE SAME LIVE SET, so a hole in one is exactly visible in the other. `check_engine.check_live_bug_gate` computes `live = _backlog.STATUSES - _backlog._GATE_DEFAULT_SKIP_STATUSES` and its docstring says this "matches `backlog._GATE_DEFAULT_SKIP_STATUSES` exactly, so the creation default and this check agree". They agree on the STATUS SET; they do not agree on WHEN the default is consulted, which is the defect.
- THE CHECKER RULE IS AN EXIT-BLOCKING ERROR, so the product of this hole is not cosmetic: `check_engine.RULE_SPECS` registers `"check.live-bug-ungated": RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07")`, and `AGENTS.md` records `aw check release-gates` running "as a named fail-closed step in `tests.yml`".
- THE FIELD WRITE GOES THROUGH ONE SHARED PRIMITIVE. Both existing gate-write sites call `releases.set_blocks_release_line`; `status_set.apply_status_change` documents its neighbours (Blocks-Release, From-Backlog, Item-Dependencies, Priority/Work-Kind, Graduated-To) as "hoisted, status-branch-independent field-write[s] ... funnelling through the single shared ... primitive so there is no duplicate write path". The new writes use the same primitive.
- THE DEFAULT IS SCOPED TO BACKLOG RECORDS ON THE SHARED PATH. `status_set.apply_status_change` guards its existing call with `rec.record_type == "backlog"` and explains why: a plan's or spec's `- Work-Kind:` is "a recognized-but-optional descriptive field", and "Defaulting a gate onto a plan because someone labelled it `bug` would invent a release obligation from a descriptive edit." The new guard carries the same `record_type` condition.
- AN EXPLICIT `--blocks-release` ALWAYS WINS, INCLUDING `-`. Predicate condition 4: "AN EXPLICIT VALUE ALWAYS WINS, INCLUDING `-`. A default is not a prohibition; an author may legitimately file an ungated bug". Both existing setter call sites are already guarded by `br is None` / `getattr(args, "blocks_release", None) is None`; the new call sites must share that guard so a deliberate `--blocks-release -` on the same call is not overridden.

## Findings

The backlog item asks the executor to "first classify a sample of the 20260917/20260918 items by route ... so the fix targets the dominant one". That classification was performed while authoring this plan, and it CONTRADICTS the item's own leading hypothesis. The findings below are the corrected diagnosis.

| # | Finding | Evidence |
|---|---|---|
| F-01 | The RECLASSIFICATION route the item names as the gap is ALREADY FIXED and works on the `--status` spelling. Filing a `chore` then running `aw backlog set --status open <id> --work-kind bug` writes `- Blocks-Release: next` and announces it. | Driven in a temp fixture via `backlog.run_new` then `backlog.run_set`: output `aw backlog set: defaulted - Blocks-Release: next on this bug item (no --blocks-release given)...`, and the resulting item carries `- Blocks-Release: next`. The call site is `backlog.run_set`'s `if set_work_kind is not None and br is None:` block, commented "nobugship di08i9 E-02: DEFAULT THE GATE ON A RECLASSIFICATION TOO". |
| F-02 | The positional spelling carries the same reclassification default, so BOTH spellings are covered for the `--work-kind` route. | `status_set.apply_status_change` contains the parallel block guarded by `work_kind is not None and rec.record_type == "backlog" and getattr(args, "blocks_release", None) is None`, commented "nobugship di08i9 E-02: THE POSITIONAL SPELLING'S HALF OF THE RECLASSIFICATION DEFAULT". |
| F-03 | THE ACTUAL LIVE HOLE IS THE STATUS TRANSITION. An ungated `bug` moved `open -> graduated` by `aw backlog set` keeps no gate, because nothing consults the predicate when `--work-kind` is absent. | Driven: filed `--work-kind bug --blocks-release -` (ungated by choice), then `backlog.run_set(status="graduated")`. Output was only `aw backlog set: <file> -> graduated` with NO gate notice, and the item's front matter after the transition had no `- Blocks-Release:` line. |
| F-04 | `parked -> open` has the same hole, and it is the WORST case because the predicate DELIBERATELY declined at creation. A `bug` filed `parked` is correctly left ungated ("not defaulting ... because its status is 'parked'"), and un-parking it to `open` never revisits that decision. | Driven: `aw backlog new --status parked --work-kind bug` printed the declining notice and wrote no gate; `backlog.run_set(status="open")` then printed no notice and wrote no gate; `check_engine.check_live_bug_gate` on the resulting tree returned `['check.live-bug-ungated']`. |
| F-05 | `done -> open` (reopening a fixed bug) has the same hole, for the same reason: `done` is in `_GATE_DEFAULT_SKIP_STATUSES`, so the creation-time decline is never revisited when the item is reopened. | Driven: `aw backlog new --status done --work-kind bug` printed the declining notice; `backlog.run_set(status="open")` wrote no gate; `check_engine.check_live_bug_gate` returned `['check.live-bug-ungated']`. |
| F-06 | Each uncovered route immediately manufactures an EXIT-BLOCKING finding, so the defect's product is a CI failure, not untidiness. | `check_engine.rule_spec("check.live-bug-ungated")` returns severity `"error"` (the registry symbol is `RULE_REGISTRY`, not `RULE_SPECS` as authored; see F-15); `AGENTS.md` records `aw check release-gates` as "a named fail-closed step in `tests.yml`". F-03/F-04/F-05 each reproduced that exact rule id, re-driven at review. |
| F-07 | THE ITEM'S CENTRAL MEASUREMENT DOES NOT REPRODUCE, and its stated cause is wrong. The item reports the gateless population TRIPLING to 65 after `di08i9` shipped, clustering in items dated 20260917/20260918. Re-measured at this lane's HEAD there are ZERO gateless live bugs repo-wide. | `check_engine.check_live_bug_gate(Path('.'))` returned 0 findings; `aw check release-gates --agent` emitted `"outcome":"conforms","findings":0`. The 20260917/18 backfill the item describes was completed (those items' own histories read "Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled"). |
| F-08 | The item's "created AFTER di08i9 landed" cluster is a MEASUREMENT ARTIFACT of status-directory moves, not evidence of the creation default failing. Counting first-add commits WITHOUT `--follow` attributes a file to the commit that moved it between status directories. | Without `--follow`: 24 items looked "created as bug and ungated", 11 of them apparently after `di08i9` merged, all 11 sharing a single timestamp `2026-09-24T21:32:08-04:00` (one bulk move). With `--follow --diff-filter=A` against `di08i9`'s merge time `2026-09-18T18:00:18-04:00`: 38 pre-`di08i9` ungated, 10 post-`di08i9` GATED, and **0** post-`di08i9` created-as-bug-and-ungated. The creation default has no counterexample. |
| F-09 | So the item's "regrowth by tens of items per week" premise is unsupported, but its SUGGESTED FIX is still correct and still needed, on the narrower and fully-reproduced grounds of F-03/F-04/F-05. This plan implements that fix and does NOT claim the item's regrowth measurement. | F-07 and F-08 above; F-03/F-04/F-05 are each independently driven. |
| F-10 | NO TEST ANYWHERE EXERCISES `decide_gate_default`, on any route, so even the shipped reclassification default is unpinned and could regress silently. CONFIRMED AT REVIEW: both searches still return nothing. | `grep -rln "decide_gate_default" tests/` returns nothing; `grep -rn "nobugship\|di08i9" tests/*.py` returns nothing. The only gate-rule test file, `tests/test_check_engine_release_gate.py`, tests the CHECKER, not the defaulting predicate's call sites. Re-run at review 2026-09-28. |
| F-11 | `blocked` IS A FIFTH UNCOVERED LIVE ROUTE AND THE AUTHORED TEST TABLE OMITS IT. The live set is exactly `['blocked', 'graduated', 'open']`, creation already gates `blocked` consistently with the other two, and a transition INTO `blocked` on an ungated bug leaves no gate and trips the ERROR, identically to routes (b)/(c)/(d). A transition to `blocked` also REFUSES (`rc=2`, nothing written) unless `--gate-kind` and `--gate-ref` are both supplied, so a fixture omitting them would assert an absent gate on an item that never moved. | Driven 2026-09-28: `sorted(backlog.STATUSES - backlog._GATE_DEFAULT_SKIP_STATUSES)` -> `['blocked','graduated','open']`; `aw backlog new --work-kind bug --status blocked` -> gated `next`; `run_set(status='blocked')` without the gate flags -> `rc=2` "moving to blocked requires --gate-kind and --gate-ref"; with `gate_kind='question'`/`gate_ref` supplied, `parked -> blocked` and `done -> blocked` both -> no gate and `['check.live-bug-ungated']`. |
| F-12 | GATING AT `graduated` MAKES A LATER `done` CLOSE REFUSE, a real and intended workflow change this plan does not disclose anywhere. Today an ungated bug taken `open -> graduated -> done` closes silently; with the gate present at `graduated`, the same close exits `rc=1` and demands one of three shipped remedies. The refusal is exactly the close-legitimacy policy AGENTS.md describes, so it is correct, but it converts a previously-silent path into an interactive one for every graduated bug. | Driven 2026-09-28 through `backlog.run_set` twice: PRE-FIX `graduated` then `done` -> `rc=0`, no refusal; with a gate written at `graduated`, `set done` -> `rc=1` and "refused: backlog item carries Blocks-Release 'next'; closing it `done` would silently drop that release gate" listing the `--from-backlog` / `--evidence` / `--blocks-release -` remedies. |
| F-13 | E-02's INSTRUCTION NAMES A VALUE THAT DOES NOT EXIST ON ITS CODE PATH. `status_set.apply_status_change`'s only work-kind binding is `work_kind = getattr(args, "work_kind", None)`, i.e. the FLAG, which is precisely `None` in the status-only case; nothing on that path parses the record's own `- Work-Kind:`, and `rec` exposes no such attribute. The shipped reader is `backlog.parse_item(<text>).kind`, which also resolves the legacy `- Kind:` fallback. `backlog.run_set` by contrast already binds `item = parse_item(text)` before its gate block, which is why E-01 needs no new read and E-02 does. | `rg -n "work_kind = " agent_workflows/status_set.py` -> one hit, the `getattr(args, ...)`; `rg -n "Work-Kind" agent_workflows/status_set.py` -> five hits, all comments or the `set_work_kind_line` write; `backlog.parse_item("- Work-Kind: bug...").kind` -> `'bug'`; `backlog.py` line `item.kind = work_kind if work_kind is not None else legacy_kind`; AST-verified that `item = parse_item(text)` precedes `run_set`'s gate block. |
| F-14 | THE PLAN RECORDS NO SUITE BASELINE, though its own validation asks for a full-suite run. Re-driven at review the bare suite is `3115 passed, 2 skipped, 3 warnings` with ZERO failures, and all four named regression files exist. A plan that asks an executor to prove "no regression" without stating what the clean state is invites accepting a pre-existing failure as noise, which is the trap a sibling plan in this sweep actually shipped. | Bare `python3 -m pytest` -> `3115 passed, 2 skipped, 3 warnings in 69.19s`; existence check over `tests/test_check_engine_release_gate.py`, `tests/test_backlog.py`, `tests/test_status_set.py`, `tests/test_backlog_handoff_close.py` -> all four present. |
| F-15 | F-06 NAMES A SYMBOL THAT DOES NOT EXIST. The registry is `check_engine.RULE_REGISTRY`, not `RULE_SPECS` (driven: `hasattr(ce,'RULE_SPECS')` is `False`, `hasattr(ce,'RULE_REGISTRY')` is `True`). The CLAIM is unaffected and reproduces exactly: `rule_spec("check.live-bug-ungated")` returns `RuleSpec(severity='error', assurance='repository', determinism='deterministic', invariant='I-07')`. | `python3 -c` over both attribute names and `ce.rule_spec('check.live-bug-ungated')`, 2026-09-28. |
| F-16 | BOTH NEGATIVE PROPERTIES E-04 PINS ALREADY HOLD TODAY, so E-04 is a fence rather than a fix and must be labelled as one. Driven: `parked -> open` with `--blocks-release -` leaves the item ungated; an item pre-gated `rel001` taken `parked -> open` keeps `rel001` and is not rewritten to `next`. | Driven 2026-09-28 through `backlog.run_set` on two temp fixtures, printing the resulting `- Blocks-Release:` line in each case (`None`, and `- Blocks-Release: rel001`). |

## Proposed changes (ordered, validatable)

1. E-01: in `backlog.run_set` (the `--status` spelling), consult `decide_gate_default` when an item is TRANSITIONING INTO a live status and carries no gate, in addition to the existing `--work-kind` condition. Announce via the existing notice shape.
2. E-02: mirror E-01 in `status_set.apply_status_change` (the positional spelling), under the same `rec.record_type == "backlog"` guard, through the same `releases.set_blocks_release_line` primitive, INTRODUCING the record's own work-kind read via `backlog.parse_item(...).kind` because that path has none (F-13).
3. E-03: pin ALL FIVE live routes in a new test module, including `blocked` (F-11, with its required `--gate-kind`/`--gate-ref`) and the two that already work (F-01/F-02), closing the total absence of coverage F-10 reports.
4. E-04: pin the three NEGATIVE properties, which already hold (F-16), so the broadened guard cannot later become an over-reach: an explicit `--blocks-release -` on the same call still wins; an existing gate is never overwritten; and a `-> done` / `-> parked` transition is never gated.

## Deferred / out of scope (with reason)

- BACKFILLING EXISTING ITEMS is out of scope, because there is nothing to backfill: F-07 measured zero gateless live bugs repo-wide at this lane's HEAD. Adding a backfill step would be work with no population.
  - Carrier-Declined: Nothing is owed, because the population is EMPTY and measured so. `check_live_bug_gate(Path('.'))` returned 0 findings and `aw check release-gates` reported `findings:0` at this lane's HEAD, so a carrier would name work with no members. Should a gateless live bug appear later, the shipped `check.live-bug-ungated` ERROR reports it on the next `aw check` and names its own remedy; that is a standing detector, not a deferred task.
- THE HAND-AUTHORING ROUTE (an item written straight into the tree, bypassing every setter) is out of scope and stays a CHECKER concern. The backlog item names it as a second route, and the item itself records that `rgaasb`'s checker "now does" catch it; a write-path default cannot cover a path that never calls the write path. `check.live-bug-ungated` is the correct owner.
  - Carrier-Declined: This obligation is ALREADY DISCHARGED by shipped code, so there is nothing to carry. A default applied at a write path is structurally incapable of covering a route that never calls a write path; the correct owner is a whole-tree checker, and that checker exists and fires at `error` (`RULE_SPECS["check.live-bug-ungated"]`, driven to a finding while authoring this plan). Filing a carrier would schedule work that is done.
- THE `- Work-Kind:` CLASSIFICATION LEAK is out of scope. Both `check_live_bug_gate`'s docstring ("HONEST LIMIT: the rule keys on `- Work-Kind:`, which is an AUTHOR'S CLASSIFICATION") and `AGENTS.md` ("the gate keys on an AUTHOR'S CLASSIFICATION ... the rule is a strict improvement over nothing and it is not a completeness claim") already record this limit. A genuine defect filed `chore` is invisible to both the checker and this default, and closing that is a judgement problem, not a call-site problem.
  - Carrier-Declined: This is an ACCEPTED, DOCUMENTED LIMIT rather than an outstanding defect, and both places a reader looks already state it as such: the checker's own docstring calls it an "HONEST LIMIT ... NOT a completeness claim", and `AGENTS.md` records the same in the release-gate section. Closing it would require a mechanism that judges whether an author's classification is correct, which no deterministic rule can do; a carrier would assert that a known-and-accepted boundary is a task someone owes.
- CHANGING `decide_gate_default`'s FOUR CONDITIONS is out of scope and is deliberately refused. Each condition is documented as measured rather than assumed, two of them cite maintainer rulings, and condition 2's fallback exists because refusing "broke 10 existing tests whose fixtures create no release record". This plan adds call sites only.
  - Carrier-Declined: This row is a SCOPE BOUNDARY on a predicate that is behaving correctly, not a deferred fix. Nothing measured here shows any of the four conditions wrong: the two `done`/`parked` declines reproduced exactly as condition 3 specifies, and condition 2 encodes a maintainer ruling. Filing a carrier would schedule the revisiting of decisions that have evidence behind them and no counterevidence against them.
- AN EXPLICIT PER-ITEM EXEMPTION FIELD is out of scope. `check_live_bug_gate`'s recovery text invites the author to "file an explicit exemption if this bug genuinely does not gate the release", but no exemption mechanism exists in the code (no `exempt` key in `backlog.py` or `config.py`), and the existing escape hatch (`--blocks-release -`) already serves the case. Introducing a new field is new policy and belongs to its own plan.
  - Carrier-Declined: Nothing is owed, because the CAPABILITY the recovery text describes already exists under a different spelling: `--blocks-release -` files or leaves an item ungated deliberately, and predicate condition 4 guarantees that explicit choice always wins. The only genuine gap is the recovery STRING implying a mechanism named "exemption", which is a wording nit inside a fix hint and not a missing feature. A new front-matter field would be new policy requiring a maintainer decision, so it cannot be carried by this plan in any case.

## Scope check

- Over-scope: none. The change is two call sites plus one test module; the shared predicate, the shared write primitive, the notice shape, the status vocabulary, and the checker are all untouched.
- Under-scope: the hand-authoring route and the `- Work-Kind:` misclassification leak are NOT closed by this plan (see Deferred). Both are recorded limits owned by `check.live-bug-ungated`, and neither is reachable from a setter call site. The backlog item's own "regrowth" framing is likewise not addressed, because F-07/F-08 show that measurement does not reproduce.
- A DOWNSTREAM BEHAVIOR CHANGE IS IN SCOPE AND IS NOT A SCOPE BREACH, recorded here because it is easy to mistake for one at finalize (F-12). Gating an item at `graduated` makes a later `aw backlog set done` on that item REFUSE under the shipped close-legitimacy predicate until the author hands the gate off, cites evidence, or de-gates. No code outside the two declared call sites changes to produce that; it is the existing `evaluate_blocking_close` behaving correctly on a newly-gated item, and it is exactly the policy AGENTS.md states. It is declared so the reconciliation and any later reader see it as foreseen.
- E-02 INTRODUCES A READ THAT DID NOT EXIST ON ITS PATH (F-13), namely the record's own `- Work-Kind:` via `backlog.parse_item(...).kind`. That is inside `agent_workflows/status_set.py`, a declared path, so it is in scope; it is noted because the authored item described it as consuming an existing value, and an executor comparing the diff against the plan's prose would otherwise see an unexplained addition.

## Required tests / validation

- `python3 -m pytest tests/test_backlog_gate_follows_status.py` for the new module (run bare; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`).
- `python3 -m pytest tests/test_check_engine_release_gate.py tests/test_backlog.py tests/test_status_set.py tests/test_backlog_handoff_close.py` as the targeted regression set: these own the checker family, both setter spellings, and the close-legitimacy predicate that shares the `done` status with the skip set.
- `python3 -m pytest` (full fast suite) to prove no order-dependent or cross-module regression, compared against a baseline RE-MEASURED IN THIS LANE IMMEDIATELY BEFORE THE CHANGE. At review the bare suite was `3115 passed, 2 skipped, 3 warnings` with ZERO failures (F-14), so any failure is a signal rather than noise; do not accept one as pre-existing without re-measuring first.
- A DOWNSTREAM-CLOSE CHECK, because this plan changes what a later close does and no other listed check would notice (F-12): take one bug `open -> graduated` (now gated) and then `set done`, and show it REFUSES with the close-legitimacy message and its three remedies. Then show the de-gate remedy works (`set done --blocks-release -` succeeds). This is asserting INTENDED behavior, not a defect, and it is what proves the plan understood its own blast radius.
- `aw check release-gates --agent` must still report `"outcome":"conforms","findings":0` on the repository tree, proving the change introduces no new finding of its own.
- PRE-FIX FALSIFICATION IS REQUIRED, not optional: V-03 must show the new (b)/(c)/(d) cases FAILING against the pre-E-01 code, because a test that passes before the fix proves nothing about the fix.

## Spec / documentation sync

N/A with reason. This plan changes WHEN an existing predicate is consulted, not what the rule is. The rule itself is already written in `AGENTS.md` under "Every live bug gates the next release" ("a backlog item, spec, or plan whose `- Work-Kind:` is in the repository's gating set ... MUST carry `- Blocks-Release:` while it is LIVE, meaning `open`, `blocked`, or `graduated`"), and that text already covers the transition case this plan makes true in code: the defect is that the code did not implement the documented rule on two routes. `.aw/records/backlog/README.md` likewise already states "a live `bug` item must carry `- Blocks-Release:`" and delegates the detail to `AGENTS.md`. No `.spec.md` file governs the defaulting call sites, hence no `.spec.md` path appears in `- Scope-Paths:`.

## Open questions

### OQ-01: When a status-only transition gates a bug, should the notice distinguish the TRANSITION trigger from the RECLASSIFICATION trigger?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: reuse the existing notice text unchanged. `decide_gate_default` composes the notice itself and returns it as the second tuple element, so a trigger-specific string would have to be assembled at the call site, which is precisely the drift the predicate's "SINGLE AUTHORITY" docstring exists to prevent. The existing text already names the field, the value, and the why ("every live bug item gates the next release; pass '--blocks-release -' to file an ungated bug item"), which is the whole of what the `y4adch` OQ-01 ruling requires. Non-blocking either way: the field write is identical under both wordings.

### OQ-02: Gating at `graduated` makes a later `done` close refuse. Is that acceptable, or should the fix skip `graduated`?

- Blocking: no
- Status: resolved
- Owner: plan-review (opencode its_direct/pt3-claude-opus-5-1m-us)
- Resolution or deferral rationale: RESOLVED as ACCEPTABLE, from the written policy, with the consequence DISCLOSED rather than avoided. MEASURED (F-12): an ungated bug taken `open -> graduated -> done` closes silently today; once the gate is present at `graduated`, `set done` exits `rc=1` demanding a handoff, evidence, or an explicit de-gate. Three grounds make the refusal right rather than a regression. FIRST, AGENTS.md states the rule this plan implements: a bug's gate must be carried while it is LIVE, and `graduated` is explicitly named as live, so an ungated graduated bug is the defect and the gate is the correction. SECOND, the refusal is the shipped close-legitimacy predicate behaving exactly as designed, and its three remedies are precisely the handoff the repository wants (a graduated item's gate is meant to travel to the plan that inherits it via `- From-Backlog:`). THIRD, skipping `graduated` to avoid the friction would reintroduce the hole this plan exists to close, since `open -> graduated` is F-03, the item's own reproduced case. The alternative considered and rejected was adding `graduated` to `_GATE_DEFAULT_SKIP_STATUSES`: that is a predicate change this plan's scope refuses, it would contradict the creation default (which already gates `graduated`), and it would put the default and the checker's live set back out of agreement, which the Step-0 notes identify as the root shape of this whole defect. What review DID change is that the consequence is now stated in E-01, the Scope check, and V-04 rather than being discovered by whoever next closes a graduated bug. REVERSIBLE: yes; a maintainer may later exclude `graduated` at the cost of one predicate condition.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the actual terminal output of `aw backlog set --status graduated <id6>` run against a temp-fixture ungated `bug` item, showing the literal line `aw backlog set: defaulted - Blocks-Release: next on this bug item`; then paste the item's front matter showing `- Blocks-Release: next`. Separately paste the same command run with `--status done` against another ungated bug, showing NO `defaulted` line and front matter with no `- Blocks-Release:` line. Also paste the `git diff` of `agent_workflows/backlog.py` proving `decide_gate_default` itself was not modified.
  - Observed evidence: PASS. Full evidence pasted below:
```
=== CMD1 (graduated):
$ aw backlog set .aw/records/backlog/open/20260928-v01gaa-01-v01gaa-test.backlog.md --status graduated --no-commit
aw backlog set: defaulted - Blocks-Release: next on this bug item (no --blocks-release given): every live bug item gates the next release; pass '--blocks-release -' to file an ungated bug item
aw backlog set: 20260928-v01gaa-01-v01gaa-test.backlog.md -> graduated

Item front matter:
- Id: v01gaa
- Status: graduated
- Blocks-Release: next
- Set: v01gaa
- Priority: medium
- Work-Kind: bug
- Summary: Test defect

=== CMD2 (done):
$ aw backlog set .aw/records/backlog/open/20260928-v01daa-01-v01daa-test.backlog.md --status done --no-commit
aw backlog set: not defaulting - Blocks-Release: on this bug item because its status is 'done': a gated done item is rejected by check.blocking-item-closed-without-gate, and a parked maybe is not live work
aw backlog set: 20260928-v01daa-01-v01daa-test.backlog.md -> done

Item front matter:
- Id: v01daa
- Status: done
- Set: v01daa
- Priority: medium
- Work-Kind: bug
- Summary: Test defect

=== git diff agent_workflows/backlog.py (proving decide_gate_default untouched):
diff --git a/agent_workflows/backlog.py b/agent_workflows/backlog.py
index 4f4fba18..8d5f5d19 100644
--- a/agent_workflows/backlog.py
+++ b/agent_workflows/backlog.py
@@ -1376,21 +1376,31 @@ def run_set(args) -> int:
         if set_work_kind is not None:
             rendered = _releases.set_work_kind_line(rendered, set_work_kind)

-    # nobugship di08i9 E-02: DEFAULT THE GATE ON A RECLASSIFICATION TOO, so the gate FOLLOWS a work
-    # kind becoming `bug` instead of depending on the author remembering a second flag. This is the
+    # nobugship di08i9 E-02 / gatefollows vsgd48 E-01: DEFAULT THE GATE ON RECLASSIFICATION AND ON
+    # STATUS TRANSITIONS INTO A LIVE STATUS. The gate follows a work kind becoming `bug` AND follows
+    # an ungated `bug` item transitioning into a live status (open, graduated, blocked). This is the
     # `--status` spelling of `aw backlog set`; the POSITIONAL spelling routes through
-    # `status_set.apply_status_change`, which carries the SAME call to the SAME shared predicate. Both
-    # were required: `aw backlog set` forks on whether `--status` was passed, so a default wired into
+    # `status_set.apply_status_change`, which carries the SAME broadened call to the SAME shared predicate.
+    # Both are required: `aw backlog set` forks on whether `--status` was passed, so a default wired into
     # one path would fire for one spelling and not the other.
     #
+    # DOWNSTREAM WORKFLOW CONSEQUENCE (DISCLOSED, OQ-02): Gating an item at `graduated` changes what
+    # a LATER close does. An ungated bug taken open -> graduated -> done closed silently before;
+    # with the gate present at `graduated`, a later `set done` REFUSES with rc=1 under the shipped
+    # close-legitimacy gate (evaluate_blocking_close below), demanding a handoff (--from-backlog),
+    # evidence (--evidence), or an explicit de-gate (--blocks-release -). That refusal is intended
+    # policy (AGENTS.md release-gates rule), but makes a previously-silent close interactive.
+    #
     # DO NOT REMOVE A GATE WHEN A WORK KIND CHANGES AWAY FROM `bug`: a gate may have been set
     # deliberately for another reason, and silently clearing it would lose a decision. Hence the
     # predicate is consulted only for the kind the item is BECOMING, it never clears, and it declines
-    # when the item already carries a gate (`existing_blocks_release`).
-    if set_work_kind is not None and br is None:
+    # when the item already carries a gate (`existing_blocks_release`). Do not alter `decide_gate_default`
+    # itself: its condition 3 already declines `done` and `parked`, so the broadened guard needs no
+    # status allowlist of its own.
+    if br is None:
         gate_default, gate_default_notice = decide_gate_default(
             repo_root,
-            kind=set_work_kind,
+            kind=set_work_kind or item.kind,
             status=new_status,
             explicit_blocks_release=None,
             existing_blocks_release=item.blocks_release,
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the actual output of the POSITIONAL spelling (`aw backlog set graduated <id6>`) on an ungated bug fixture, showing the same `defaulted - Blocks-Release: next` notice and resulting front matter as V-01's `--status` run, so the two spellings are demonstrably identical. Then paste a run transitioning a PLAN record carrying `- Work-Kind: bug` through the same function, showing NO gate was written, proving the `rec.record_type == "backlog"` guard still holds.
    PASTE THE WORK-KIND READ ITSELF, because F-13 measured that the value E-02 was originally told to use does not exist on this path. Paste the committed line that obtains the record's own kind and confirm it goes through `backlog.parse_item(...).kind` rather than a new local regex, and paste a driven status-only positional transition on an ungated bug showing the gate IS written, which is the assertion that fails if `kind=None` reached the predicate (in which case condition 1 declines and the fix silently does nothing on this spelling).
  - Observed evidence: PASS. Full evidence pasted below:
```
=== Positional spelling on ungated bug fixture:
$ aw backlog set graduated v02pos --yes --no-commit
aw backlog set: defaulted - Blocks-Release: next on this bug item (no --blocks-release given): every live bug item gates the next release; pass '--blocks-release -' to file an ungated bug item
-    backlog     20260928-v02pos-01-v02pos  [medium]  open → ●  graduated

Front matter:
- Id: v02pos
- Status: graduated
- Blocks-Release: next
- Set: v02pos
- Priority: medium
- Work-Kind: bug
- Summary: Test defect

=== Plan record carrying Work-Kind: bug transitioned through status_set.apply_status_change:
$ aw ipd set to-review p00001 --yes --no-commit
-    plan        20260928-demo-01-p00001  pending → ◔  to-review

Plan content (showing no gate was written):
# IPD: Test plan

- Date: 2026-09-28
- Kind: child
- Status: to-review
- Work-Kind: bug
- Set: demo
- Order: 1
- Id: p00001
- Summary: Demo plan

=== Work-Kind read in status_set.py:
Committed lines:
        _current_text = "\n".join(new_lines)
        _effective_kind = work_kind or _backlog.parse_item(_current_text).kind
Confirmed reading through backlog.parse_item(_current_text).kind rather than a local regex.
The driven positional transition above on ungated bug (v02pos) wrote '- Blocks-Release: next', confirming kind='bug' reached decide_gate_default rather than None.
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the full `python3 -m pytest tests/test_backlog_gate_follows_status.py` output including the `N passed` summary line. Then paste the PRE-FIX run of the same module, showing cases (b), (c), (d) AND (e) FAILING and case (a) PASSING, with the assertion text visible. A module that passes before the fix does not validate E-03.
    DO NOT USE `git stash` IN THIS SHARED CHECKOUT TO OBTAIN THE PRE-FIX RUN. The authored evidence line suggests `git stash` or `git stash push -- agent_workflows/`, and AGENTS.md forbids exactly that shape here: a stash operates on the whole working tree and can discard or unstage a co-worker's uncommitted work in a checkout other agents are using. Obtain the contrast WITHOUT mutating the tree: run the pre-fix module against the two call sites patched IN MEMORY (monkeypatch the broadened guard off, or drive `decide_gate_default`'s call sites through a patched wrapper), or run it before applying the edits and paste that output, keeping the tracked tree untouched throughout. State which route was used.
    PASTE THE `blocked` ROW's FLAGS EXPLICITLY (F-11): show the fixture passes `--gate-kind` and `--gate-ref`, and show the transition's return code is 0, because without those flags the setter exits `rc=2` and writes nothing, and the test would then pass for the wrong reason by asserting an absent gate on an item that never moved.
  - Observed evidence: PASS. Full evidence pasted below:
```
=== Post-fix full test output:
$ python3 -m pytest tests/test_backlog_gate_follows_status.py
bringing up nodes...
..................                                                       [100%]
18 passed in 2.35s

=== Pre-fix run (obtained before applying edits to agent_workflows/, keeping tracked tree untouched throughout):
$ python3 -m pytest tests/test_backlog_gate_follows_status.py
FAILED tests/test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_route_d_done_to_open_positional_spelling - AssertionError: '- Blocks-Release: next' not found in '- Id: bk0004\n- Status: open\n- Set: bk0004\n- Priority: medium\n- Work-Kind: bug\n- Summary: Test defect\n\n## Workflow history\n- 2026-09-29 open (aw set): status set to open\n- 2026-09-28 created (tester): initial\n'
FAILED tests/test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_route_d_done_to_open_status_spelling - AssertionError: '- Blocks-Release: next' not found in '- Id: bk0004\n- Status: open\n- Set: bk0004\n- Priority: medium\n- Work-Kind: bug\n- Summary: Test defect\n\n## Workflow history\n- 2026-09-28 set (aw backlog): status -> open\n- 2026-09-28 created (tester): initial\n'
FAILED tests/test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_route_e_transition_to_blocked_positional_spelling - AssertionError: '- Blocks-Release: next' not found in '- Id: bk0005\n- Status: blocked\n- Gate-Kind: question\n- Gate-Ref: Waiting on clarification\n- Set: bk0005\n- Priority: medium\n- Work-Kind: bug\n- Summary: Test defect\n\n## Workflow history\n- 2026-09-29 blocked (aw set): status set to blocked\n- 2026-09-28 created (tester): initial\n'
FAILED tests/test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_route_c_parked_to_open_status_spelling - AssertionError: '- Blocks-Release: next' not found in '- Id: bk0003\n- Status: open\n- Set: bk0003\n- Priority: medium\n- Work-Kind: bug\n- Summary: Test defect\n\n## Workflow history\n- 2026-09-28 set (aw backlog): status -> open\n- 2026-09-28 created (tester): initial\n'
FAILED tests/test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_route_b_open_to_graduated_status_spelling - AssertionError: '- Blocks-Release: next' not found in '- Id: bk0002\n- Status: graduated\n- Set: bk0002\n- Priority: medium\n- Work-Kind: bug\n- Summary: Test defect\n\n## Workflow history\n- 2026-09-28 set (aw backlog): status -> graduated\n- 2026-09-28 created (tester): initial\n'
FAILED tests/test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_route_e_transition_to_blocked_status_spelling - AssertionError: '- Blocks-Release: next' not found in '- Id: bk0005\n- Status: blocked\n- Gate-Kind: question\n- Gate-Ref: Waiting on clarification\n- Set: bk0005\n- Priority: medium\n- Work-Kind: bug\n- Summary: Test defect\n\n## Workflow history\n- 2026-09-28 set (aw backlog): status -> blocked\n- 2026-09-28 created (tester): initial\n'
FAILED tests/test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_route_c_parked_to_open_positional_spelling - AssertionError: '- Blocks-Release: next' not found in '- Id: bk0003\n- Status: open\n- Set: bk0003\n- Priority: medium\n- Work-Kind: bug\n- Summary: Test defect\n\n## Workflow history\n- 2026-09-29 open (aw set): status set to open\n- 2026-09-28 created (tester): initial\n'
FAILED tests/test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_route_b_open_to_graduated_positional_spelling - AssertionError: '- Blocks-Release: next' not found in '- Id: bk0002\n- Status: graduated\n- Set: bk0002\n- Priority: medium\n- Work-Kind: bug\n- Summary: Test defect\n\n## Workflow history\n- 2026-09-29 graduated (aw set): status set to graduated\n- 2026-09-28 created (tester): initial\n'
8 failed, 10 passed in 2.35s
(Cases (b), (c), (d), and (e) failed across both spellings, and case (a) passed both before and after)

=== Route (e) blocked transition flags and return code:
Flags passed in fixture:
  --gate-kind question --gate-ref "Waiting on clarification"
Return code asserted:
  self.assertEqual(rc, 0)
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the three negative tests' names and outcomes from the pytest output, plus, for the `--blocks-release -` case, the actual item front matter after the call showing NO `- Blocks-Release:` line, and for the preserved-gate case, front matter showing the ORIGINAL release id6 (not `next`). State in one sentence that all three pass BOTH before and after the fix (F-16), so they are fences and no pre-fix failure is claimed for them. Then paste `python3 -m pytest` (full fast suite) with its `N passed` summary compared against a baseline re-measured in this lane immediately before the change (NOT against any figure written in this plan), and `aw check release-gates --agent` showing `"outcome":"conforms"` and `"findings":0`.
    PASTE THE DOWNSTREAM-CLOSE EVIDENCE HERE (F-12), since this is the last item before commit and no other check covers it: take one bug `open -> graduated` so the new default gates it, then run `set done` and paste the actual refusal including the `refused: backlog item carries Blocks-Release` line and its three remedies; then paste `set done --blocks-release -` succeeding. Label it explicitly as INTENDED behavior that this plan introduces, not a regression, so a later reader is not left to guess whether the refusal was foreseen.
  - Observed evidence: PASS. Full evidence pasted below:
```
=== Three negative tests' names and outcomes:
PASSED tests/test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_negative_explicit_blocks_release_dash_wins_status_spelling
PASSED tests/test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_negative_explicit_blocks_release_dash_wins_positional_spelling
PASSED tests/test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_negative_existing_gate_preserved_status_spelling
PASSED tests/test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_negative_existing_gate_preserved_positional_spelling
PASSED tests/test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_negative_transition_to_done_writes_no_gate_status_spelling
PASSED tests/test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_negative_transition_to_done_writes_no_gate_positional_spelling
PASSED tests/test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_negative_transition_to_parked_writes_no_gate_status_spelling
PASSED tests/test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_negative_transition_to_parked_writes_no_gate_positional_spelling

All three negative fence properties pass BOTH before and after the fix (F-16), ensuring the broadened guard does not over-reach.

--blocks-release - front matter:
- Id: bk0006
- Status: open
- Set: bk0006
- Priority: medium
- Work-Kind: bug
- Summary: Test defect

Preserved gate front matter:
- Id: bk0007
- Status: open
- Blocks-Release: rel001
- Set: bk0007
- Priority: medium
- Work-Kind: bug
- Summary: Test defect

=== Full test suite comparison:
Baseline re-measured in this lane immediately before the change:
  3217 passed, 2 skipped, 3 warnings in 85.89s (0:01:25)
Full fast suite post-fix:
  3235 passed, 2 skipped, 3 warnings in 57.55s
Outcome: +18 passed (the 18 tests in tests/test_backlog_gate_follows_status.py), 0 regressions.

=== aw check release-gates --agent:
{"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"release-gates","findings":0,"evidence":["inventory","rules"],"next":"aw releases list"}

=== Downstream-close evidence (F-12, INTENDED behavior):
1. Transition open -> graduated on ungated bug:
$ aw backlog set .aw/records/backlog/open/20260928-v04cla-01-v04cla-test.backlog.md --status graduated --no-commit
Front matter now carries:
- Id: v04cla
- Status: graduated
- Blocks-Release: next

2. Close graduated bug with 'set done':
$ aw backlog set .aw/records/backlog/graduated/20260928-v04cla-01-v04cla-test.backlog.md --status done --no-commit
Exit code: 1
aw backlog set: refused: backlog item carries Blocks-Release 'next'; closing it `done` would silently drop that release gate.
  - hand the gate to a plan: add `- From-Backlog: <this id6>` (and the same `- Blocks-Release`) to a plan via `aw ipd set ... --from-backlog <id6>`
  - cite satisfying evidence: `aw backlog set done <item> --evidence <in-tree artifact path>`
  - explicitly release the gate first: `aw backlog set done <item> --blocks-release -`

3. Close graduated bug using de-gate remedy 'set done --blocks-release -':
$ aw backlog set .aw/records/backlog/graduated/20260928-v04cla-01-v04cla-test.backlog.md --status done --blocks-release - --no-commit
Exit code: 0
aw backlog set: 20260928-v04cla-01-v04cla-test.backlog.md -> done
Front matter:
- Id: v04cla
- Status: done
- Set: v04cla
- Priority: medium
- Work-Kind: bug
- Summary: Downstream close test
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval recorded as `- Status: approved` with an `- Approval:` attestation; this plan is authored `to-review` and carries no `- Readiness:` field, because that field is an OUTPUT of `/plan-review` and writing one here would forge a review that has not happened.

Execution contract: commit only the paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`; never push. Run the suite bare as `python3 -m pytest` and paste actual output, against a baseline re-measured in this lane immediately before the change. Do not mark any `V-*` item complete without the concrete evidence it names, and specifically do not mark V-03 complete without the PRE-FIX failing run.

DO NOT USE `git stash` TO OBTAIN THE PRE-FIX CONTRAST. This is a SHARED CHECKOUT, and a stash operates on the whole working tree, so it can discard or unstage a co-worker's uncommitted work. V-03's authored evidence line originally suggested it; obtain the contrast in memory (patch the broadened guard off) or by running the module before applying the edits, and say which route was used. AGENTS.md's shared-checkout rule governs here and overrides the convenience.

WHAT THIS PLAN CHANGES BEYOND THE TWO CALL SITES, stated so nobody meets it by surprise: once a graduated bug carries a gate, closing it `done` REFUSES until the gate is handed to a plan, satisfied with evidence, or explicitly released (F-12, measured end to end). That is the shipped close-legitimacy policy working as written and is the intended outcome of implementing AGENTS.md's rule, not a regression; OQ-02 records the reasoning and V-04 requires the evidence.

Post-gate lifecycle: after every `E-*` is performed and every `V-*` is verified with pasted evidence, run `aw ipd lint --phase pre-transition` and move this plan to `.aw/records/plans/executed/` through the tooled transition. This plan carries `- From-Backlog: 98zlut` and inherits that item's `- Blocks-Release: next`, so executing it is what legitimately discharges the item's release gate; the backlog item itself moves to `graduated`, never to `done`, at authoring time.
