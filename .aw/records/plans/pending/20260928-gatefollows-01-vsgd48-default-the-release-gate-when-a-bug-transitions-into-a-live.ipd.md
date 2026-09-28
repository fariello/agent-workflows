# IPD: Default the release gate when a bug TRANSITIONS into a live status, not only when its Work-Kind changes

- Date: 2026-09-28
- Kind: child
- Concern: `backlog.decide_gate_default` is consulted only when `--work-kind` is passed, so an ungated `bug` that becomes LIVE by a pure STATUS transition (`parked -> open`, `done -> open`, `open -> graduated`) keeps no gate and immediately trips the shipped `check.live-bug-ungated` ERROR that the same predicate exists to prevent.
- Scope: Add the STATUS-transition call site to both spellings of `aw backlog set`, through the existing shared predicate, and pin all four routes (the two already-working reclassification routes and the two currently-broken transition routes) with tests. No new policy, no new field, no change to `decide_gate_default`'s four conditions.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/status_set.py, tests/test_backlog_gate_follows_status.py
- Item-Dependencies: none
- Status: to-review
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

- 2026-09-28 draft (opencode): created.
- 2026-09-28 to-review (opencode): authored from backlog `98zlut`; re-measured the item's hypothesis, corrected its diagnosis (the reclassification route it names is already shipped and works; the STATUS-transition route is the live hole), and scoped to that hole.

## Goal

Make the release gate FOLLOW a bug into a live status, so that an ungated `bug` item reaching `open`, `blocked`, or `graduated` through `aw backlog set` is gated by the same shared predicate that already gates it at creation and on reclassification. Today two of the four routes into "live and ungated" are uncovered, and each of them manufactures an item that the shipped `check.live-bug-ungated` rule reports as an ERROR on the very next `aw check`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: wire the status-transition call site into both spellings

- [ ] E-01 In `backlog.run_set`, broaden the gate-default consultation so it also fires when the item is transitioning INTO a live status. Replace the guard `if set_work_kind is not None and br is None:` with one that fires when `br is None` AND (`set_work_kind is not None` OR the item is becoming live), passing `kind=set_work_kind or item.kind` and `status=new_status` to `decide_gate_default`, and keeping `existing_blocks_release=item.blocks_release` so an item that already carries a gate is untouched. Write through `releases.set_blocks_release_line` and announce with the existing `sys.stdout.write(f"aw backlog set: {gate_default_notice}\n")` line. Do NOT alter `decide_gate_default` itself: its condition 3 already declines `done` and `parked`, so the broadened guard needs no status allowlist of its own.
  - Depends on: none
  - Expected outcome: `aw backlog set --status graduated <ungated-bug>` writes `- Blocks-Release: next` and prints the `defaulted - Blocks-Release: next` notice, where before it printed only the `-> graduated` line. `aw backlog set --status done <ungated-bug>` still writes no gate.
  - Execution state: pending

- [ ] E-02 Mirror E-01 in `status_set.apply_status_change` for the positional spelling. Broaden its existing guard (`work_kind is not None and rec.record_type == "backlog" and getattr(args, "blocks_release", None) is None`) to also fire on a status-only transition, passing `kind=work_kind` or the record's existing parsed `- Work-Kind:` when the flag is absent, and `status=norm_status`. Keep the `rec.record_type == "backlog"` guard exactly as-is, for the reason its own comment gives (a plan's `- Work-Kind:` is descriptive, and gating a plan on it "would invent a release obligation from a descriptive edit"). Keep reading the existing gate out of `new_lines` via the current `^- Blocks-Release:` regex so an already-gated item is declined by the predicate.
  - Depends on: E-01
  - Expected outcome: the positional `aw backlog set graduated <ungated-bug>` behaves byte-for-byte like the `--status` spelling from E-01, and a PLAN or SPEC record transitioned through this same function is never gated by a status move.
  - Execution state: pending

### Task group 2: pin every route, positive and negative

- [ ] E-03 Add `tests/test_backlog_gate_follows_status.py` covering all four routes into "live and ungated", for BOTH spellings of `aw backlog set`, each asserting on the item's `- Blocks-Release:` line AND on `check_engine.check_live_bug_gate` returning zero findings afterwards: (a) reclassification `chore -> bug` while `open` (already passing, F-01/F-02: this is the regression pin F-10 says does not exist); (b) `open -> graduated` on an ungated bug (F-03); (c) `parked -> open` (F-04); (d) `done -> open` (F-05). Each fixture must create a `planned` release record, because `decide_gate_default` condition 2 falls back to ungated when `next` does not resolve.
  - Depends on: E-02
  - Expected outcome: a new test module whose (b), (c), (d) cases FAIL on the pre-E-01 code and PASS after, and whose (a) case passes both before and after.
  - Execution state: pending

- [ ] E-04 In the same module, pin the three negative properties, so the broadened guard cannot silently become an over-reach: (a) `aw backlog set open <ungated-bug> --blocks-release -` leaves the item UNGATED (predicate condition 4, explicit value wins); (b) an item already carrying `- Blocks-Release: <id6>` transitioned to another live status keeps THAT value and is not rewritten to `next`; (c) transitioning a bug to `done` and to `parked` writes NO gate (predicate condition 3 / `_GATE_DEFAULT_SKIP_STATUSES`), which also proves the fix cannot manufacture the `check.blocking-item-closed-without-gate` ERROR that condition 3 exists to avoid.
  - Depends on: E-03
  - Expected outcome: three negative tests passing, each asserting the ABSENCE or the PRESERVATION of a gate value rather than its presence.
  - Execution state: pending

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
| F-06 | Each uncovered route immediately manufactures an EXIT-BLOCKING finding, so the defect's product is a CI failure, not untidiness. | `RULE_SPECS["check.live-bug-ungated"]` is severity `"error"`; `AGENTS.md` records `aw check release-gates` as "a named fail-closed step in `tests.yml`". F-03/F-04/F-05 each reproduced that exact rule id. |
| F-07 | THE ITEM'S CENTRAL MEASUREMENT DOES NOT REPRODUCE, and its stated cause is wrong. The item reports the gateless population TRIPLING to 65 after `di08i9` shipped, clustering in items dated 20260917/20260918. Re-measured at this lane's HEAD there are ZERO gateless live bugs repo-wide. | `check_engine.check_live_bug_gate(Path('.'))` returned 0 findings; `aw check release-gates --agent` emitted `"outcome":"conforms","findings":0`. The 20260917/18 backfill the item describes was completed (those items' own histories read "Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled"). |
| F-08 | The item's "created AFTER di08i9 landed" cluster is a MEASUREMENT ARTIFACT of status-directory moves, not evidence of the creation default failing. Counting first-add commits WITHOUT `--follow` attributes a file to the commit that moved it between status directories. | Without `--follow`: 24 items looked "created as bug and ungated", 11 of them apparently after `di08i9` merged, all 11 sharing a single timestamp `2026-09-24T21:32:08-04:00` (one bulk move). With `--follow --diff-filter=A` against `di08i9`'s merge time `2026-09-18T18:00:18-04:00`: 38 pre-`di08i9` ungated, 10 post-`di08i9` GATED, and **0** post-`di08i9` created-as-bug-and-ungated. The creation default has no counterexample. |
| F-09 | So the item's "regrowth by tens of items per week" premise is unsupported, but its SUGGESTED FIX is still correct and still needed, on the narrower and fully-reproduced grounds of F-03/F-04/F-05. This plan implements that fix and does NOT claim the item's regrowth measurement. | F-07 and F-08 above; F-03/F-04/F-05 are each independently driven. |
| F-10 | NO TEST ANYWHERE EXERCISES `decide_gate_default`, on any route, so even the shipped reclassification default is unpinned and could regress silently. | `grep -rln "decide_gate_default" tests/` returns nothing; `grep -rn "nobugship\|di08i9" tests/*.py` returns nothing. The only gate-rule test file, `tests/test_check_engine_release_gate.py`, tests the CHECKER, not the defaulting predicate's call sites. |

## Proposed changes (ordered, validatable)

1. E-01: in `backlog.run_set` (the `--status` spelling), consult `decide_gate_default` when an item is TRANSITIONING INTO a live status and carries no gate, in addition to the existing `--work-kind` condition. Announce via the existing notice shape.
2. E-02: mirror E-01 in `status_set.apply_status_change` (the positional spelling), under the same `rec.record_type == "backlog"` guard, through the same `releases.set_blocks_release_line` primitive.
3. E-03: pin ALL FOUR routes in a new test module, including the two that already work (F-01/F-02), closing the total absence of coverage F-10 reports.
4. E-04: pin the three NEGATIVE properties so the fix cannot become an over-reach: an explicit `--blocks-release -` on the same call still wins; an existing gate is never overwritten; and a `-> done` / `-> parked` transition is never gated.

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

## Required tests / validation

- `python3 -m pytest tests/test_backlog_gate_follows_status.py` for the new module (run bare; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`).
- `python3 -m pytest tests/test_check_engine_release_gate.py tests/test_backlog.py tests/test_status_set.py tests/test_backlog_handoff_close.py` as the targeted regression set: these own the checker family, both setter spellings, and the close-legitimacy predicate that shares the `done` status with the skip set.
- `python3 -m pytest` (full fast suite) to prove no order-dependent or cross-module regression.
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

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the actual terminal output of `aw backlog set --status graduated <id6>` run against a temp-fixture ungated `bug` item, showing the literal line `aw backlog set: defaulted - Blocks-Release: next on this bug item`; then paste the item's front matter showing `- Blocks-Release: next`. Separately paste the same command run with `--status done` against another ungated bug, showing NO `defaulted` line and front matter with no `- Blocks-Release:` line. Also paste the `git diff` of `agent_workflows/backlog.py` proving `decide_gate_default` itself was not modified.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the actual output of the POSITIONAL spelling (`aw backlog set graduated <id6>`) on an ungated bug fixture, showing the same `defaulted - Blocks-Release: next` notice and resulting front matter as V-01's `--status` run, so the two spellings are demonstrably identical. Then paste a run transitioning a PLAN record carrying `- Work-Kind: bug` through the same function, showing NO gate was written, proving the `rec.record_type == "backlog"` guard still holds.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the full `python3 -m pytest tests/test_backlog_gate_follows_status.py` output including the `N passed` summary line. Then paste the PRE-FIX run of the same module against stashed-implementation code (e.g. `git stash` of the E-01/E-02 edits, or `git stash push -- agent_workflows/`), showing cases (b), (c), (d) FAILING and case (a) PASSING, with the assertion text visible. A module that passes before the fix does not validate E-03.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the three negative tests' names and outcomes from the pytest output, plus, for the `--blocks-release -` case, the actual item front matter after the call showing NO `- Blocks-Release:` line, and for the preserved-gate case, front matter showing the ORIGINAL release id6 (not `next`). Then paste `python3 -m pytest` (full fast suite) with its `N passed` summary, and `aw check release-gates --agent` showing `"outcome":"conforms"` and `"findings":0`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval recorded as `- Status: approved` with an `- Approval:` attestation; this plan is authored `to-review` and carries no `- Readiness:` field, because that field is an OUTPUT of `/plan-review` and writing one here would forge a review that has not happened.

Execution contract: commit only the paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`; never push. Run the suite bare as `python3 -m pytest` and paste actual output. Do not mark any `V-*` item complete without the concrete evidence it names, and specifically do not mark V-03 complete without the PRE-FIX failing run.

Post-gate lifecycle: after every `E-*` is performed and every `V-*` is verified with pasted evidence, run `aw ipd lint --phase pre-transition` and move this plan to `.aw/records/plans/executed/` through the tooled transition. This plan carries `- From-Backlog: 98zlut` and inherits that item's `- Blocks-Release: next`, so executing it is what legitimately discharges the item's release gate; the backlog item itself moves to `graduated`, never to `done`, at authoring time.
