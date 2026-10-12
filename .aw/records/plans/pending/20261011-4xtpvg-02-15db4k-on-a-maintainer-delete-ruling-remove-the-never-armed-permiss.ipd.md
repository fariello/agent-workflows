# IPD: On a maintainer DELETE ruling, remove the never-armed permission bound and amend spec 7ckptx R4.4

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `e6zeta` asks the maintainer to choose between KEEPING the documented-but-unarmed permission bound (what executed plan `0b7fic` left in place) and DELETING it. The item is explicit that it "must NOT be closed by an agent picking a side". So this plan does not pick one. It is the complete, ready-to-run DELETE branch, held behind a BLOCKING open question (OQ-01) that only the maintainer answers; resolving it to DELETE and then approving is the delete ruling. If the maintainer rules KEEP instead, the plan is retired to `not-executed` and the item closes `done` citing `0b7fic` as evidence, which is the item's own stated KEEP path ("0b7fic already does everything needed"). Measured in this lane at HEAD `ac25dd246`: `TurnBoundWatch.note_permission_request` has zero production callers (`grep` over `agent_workflows/` and `tools/` finds only its definition), both drivers call only `turn_bounds.note_progress()`, whose ONLY effect is clearing `_permission_pending_since`, and the only reader of the `turn_bound_expiry` record that would carry `BOUND_PERMISSION` is `bound_expiry_reaper` itself. Because the trigger has never been called, the bound has never fired in production, so no recorded run can contain a `permission-timeout` expiry for a reader to misread.
- Scope: IF AND ONLY IF the maintainer resolves OQ-01 to DELETE and a human approves this plan: remove `PERMISSION_TIMEOUT`, `BOUND_PERMISSION`, the `permission_timeout` constructor parameter, `_permission_pending_since`, the permission-only `_lock`, `note_permission_request`, the permission half of `TurnBoundWatch._expired`, and the now-no-op `note_progress` together with its two driver call sites; delete `tests/test_permission_bound_disabled.py` and rewrite the permission cases in `tests/test_turn_bounds.py` so `MAX_TURN_TIMEOUT` stays covered behaviorally; and amend spec `7ckptx` R4.4, R4.4(a), R4.4b, R4.4c, A10, A10b, A10c and A10e (plus the plural "driver bounds" references) IN THE SAME CHANGE so the contract stops requiring the constants exist. CHANGES NO BEHAVIOR A TURN CAN OBSERVE: the bound ships at `0.0` and has no trigger, so it cannot fire today, and `MAX_TURN_TIMEOUT` (4 hours, unresettable, offset on antigravity) is untouched. EXCLUDES the non-isolated deny-posture gap (carrier `8ctu3u`) and any log-fed detector (refused on measurement by `0b7fic`).
- Scope-Paths: agent_workflows/lane_containment.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_turn_bounds.py, tests/test_permission_bound_disabled.py, .aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
- Item-Dependencies: executed:0b7fic
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: e6zeta
- From-Spec: 7ckptx
- Set: 4xtpvg
- Order: 2
- Highest E allocated: 09
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 15db4k
- Approval: 2026-10-12, human ("approved"): maintainer ruled DELETE for e6zeta

## Workflow history
- 2026-10-12 approved (aw set, --by-human): maintainer ruled DELETE for e6zeta
- 2026-10-12 readiness re-check (agent (aw ipd recheck-readiness)): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: unresolved-blocking-question -> clear (no unresolved BLOCKING open question; `has_unresolved_blocking_question` -> False (a NON-blocking open question is deliberately not counted, per the maintainer's 2026-09-10 ruling on qhy3i3 OQ-01)); unresolved-gating-finding -> clear (no unresolved gating finding; `review_findings.subject_gating_blocks` -> empty (an ABSENT review artifact is silent by that predicate's documented contract)); negative-review-verdict -> clear (the newest review record's verdict is not negative; `newest_verdict` -> neutral). RE-CHECKED REVIEW: the review of 2026-10-12, findings PR-001..PR-005. Recomputed at HEAD `be6560ccf`. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 (HIGH, fixed: OQ-01 made blocking so --full-auto cannot clear the maintainer's ruling; measured is_plan_review_approved True at go-pending-approval), PR-002 (MEDIUM, fixed: residual-limits paragraph relocated, not deleted), PR-003 (MEDIUM, fixed: spec plural-bound references and A10c obligation), PR-004 (LOW, fixed: _lock removal, V-04 agy construction comment, E-06 interim failure, E-09 stderr and chatty assertion), PR-005 (LOW, fixed: thzrpo coupling on RESIDUAL LIMITS). OQ-01 open by design (maintainer KEEP/DELETE); Readiness no-go until answered. Reviewed at HEAD b1b2fab2b. Record: .aw/records/reviews/20261011-4xtpvg-02-15db4k-on-a-maintainer-delete-ruling-remove-the-never-armed-permiss.review.md.
- 2026-10-12 same-status (aw set): set Item-Dependencies to executed:0b7fic

- 2026-10-11 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog `e6zeta`. The item is a MAINTAINER DECISION and says it must not be closed by an agent picking a side, so this plan is written as the DELETE branch whose human approval is the ruling, with the KEEP branch spelled out as "retire this plan to not-executed, close `e6zeta` done with `--evidence` pointing at `0b7fic`". E-01 refuses to proceed on an `auto-approved` status, so `--full-auto` cannot make the ruling on the maintainer's behalf. Measured at HEAD `ac25dd246`: zero production callers of `note_permission_request`; `note_progress` has two callers (`oc_runipd.run_opencode`, `agy_runipd.run_agy_turn`) and only clears the permission ask; no consumer of `turn_bound_expiry` outside `lane_containment`; the permission bound is exercised only by `tests/test_turn_bounds.py` (2 tests plus parts of 2 more) and `tests/test_permission_bound_disabled.py` (4 tests); the 16 tests in those two files pass at baseline (`16 passed in 3.41s`).
- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Give the maintainer a single decision on backlog `e6zeta`: answering OQ-01 "DELETE" and approving
this plan deletes the permission-bound mechanism and its spec obligation together, leaving `MAX_TURN_TIMEOUT` as the single,
fully tested R4.4 turn bound; retiring it keeps `0b7fic`'s documented-but-unarmed state. Either way the
item closes without an agent choosing for the maintainer.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: confirm the ruling and capture a baseline

- [x] E-01 CONFIRM THAT A HUMAN MADE THE DELETE RULING BEFORE CHANGING ANYTHING. Read this plan's own front matter, `## Open questions` and `## Workflow history`. Proceed ONLY if OQ-01 reads `- Status: resolved` with a recorded DELETE ruling attributed to the maintainer, AND `- Status:` is `approved`, AND a `- Approval:` line is present (the schema allows that field only on a human `approved`, never on `auto-approved`, per `ipd_schema` "Approval iff Status is approved (auto-approved does NOT carry human Approval)"). If OQ-01 is not resolved to DELETE (or the ruling is KEEP), or the status is `auto-approved`, or there is no `- Approval:` line, mark this item `blocked`, change no file, and report that the delete ruling belongs to the maintainer (backlog `e6zeta`: "It must NOT be closed by an agent picking a side"). This is the in-turn backstop; the primary guard is OQ-01's `- Blocking: yes`, which the lint gate enforces before any turn is dispatched.
  - Depends on: none
  - Expected outcome: either the quoted resolved OQ-01 ruling plus the `- Status: approved` and `- Approval:` lines, and the plan proceeds; or a `blocked` item with no file changed.
  - Execution state: performed

- [x] E-02 CAPTURE THE BASELINE the later bars compare against: run the bare suite as `python3 -m pytest` and record its summary line plus any failing node ids; run `aw check` and record its violation set; run `aw specs check` and record its result. Do this BEFORE the first edit, since the suite's size drifts between runs on this tree and the bars below are by node id, not by total.
  - Depends on: E-01
  - Expected outcome: three recorded baselines (suite summary and failing node ids, `aw check` violations, `aw specs check` result).
  - Execution state: performed

### Task group 2: remove the mechanism from the code

- [x] E-03 REMOVE THE PERMISSION HALF FROM `agent_workflows/lane_containment.py`. Delete: the `PERMISSION_TIMEOUT` constant and its `#:` comment block EXCEPT its `CONSEQUENCE, stated plainly:` and `RESIDUAL LIMITS:` paragraphs, which MOVE (reworded only as far as needed to stop naming the deleted constant) onto `MAX_TURN_TIMEOUT`'s `#:` block, because F-7's limits survive the deletion and those paragraphs are the only code-side statement of them (that `MAX_TURN_TIMEOUT` and the stall watchdog are the only bounds on a permission deadlock in a turn the R4.1 denial does not cover, the non-isolated opencode turn and every antigravity turn). Move them in whatever wording they carry AT EXECUTION TIME: sibling plan `thzrpo` (same Set, Order 2) rewrites the `RESIDUAL LIMITS:` paragraph, so re-read it rather than restoring the text quoted here. Also delete `BOUND_PERMISSION`; the `permission_timeout` keyword of `TurnBoundWatch.__init__` with its normalization and negative clamp; `_permission_pending_since`; `note_permission_request`; the permission branch of `TurnBoundWatch._expired`; and `self._lock`, whose only users are the three permission-state accesses being removed (keep `threading`, which `_stop` and `_thread` still use). Simplify what then depends only on one bound: the `check_interval` clamp's `candidates` list becomes `MAX_TURN_TIMEOUT` alone (keep the `max(0.005, min(check_interval, bound / 4.0))` shape, since injected short test bounds still need it), and `enabled` becomes `self.max_turn_timeout > 0`. Rewrite the prose that names the permission bound so it is true afterwards: the `TurnBoundWatch` docstring ("enforcing `MAX_TURN_TIMEOUT` and, when armed, `PERMISSION_TIMEOUT`" and the "TWO BOUNDS DIFFER IN RESET SEMANTICS" list), the `# ---- R4.4: the two driver-side bounds` header and its "Both are in-code constants" sentence, the `BOUND_PERMISSION`/`BOUND_MAX_TURN` comment that says a post-mortem can tell "a permission deadlock from an over-long turn from a silent stall", the `bound_expiry_record` docstring's same three-way sentence, `CONTAINMENT_LAYERS_WITHOUT_HOST_DENIAL`'s "(and PERMISSION_TIMEOUT when armed)", and `parse_host_ceiling_seconds`'s "the same reasoning R4.4b applies to the permission detector". Add, on `MAX_TURN_TIMEOUT`'s `#:` block, ONE dated sentence recording that a resettable permission bound existed from `8a491d4c1` (2026-09-05), was never armed because a permission ask never reaches stdout (research `7so8uz`), and was removed by this plan on the maintainer's ruling, so a reader who wonders why R4.4 has one bound finds the reason at the constant. Keep `BOUND_MAX_TURN`, `bound_expiry_record`, `bound_expiry_reaper`, `driver_bound_for_host`, `HOST_CEILING_OFFSET_SECONDS` and their behavior unchanged.
  - Depends on: E-02
  - Expected outcome: `lane_containment` defines no `PERMISSION_TIMEOUT`, `BOUND_PERMISSION`, `note_permission_request`, `permission_timeout` parameter, `_permission_pending_since` or `_lock`; every remaining comment and docstring describes one bound; the residual-limits statement now sits on `MAX_TURN_TIMEOUT`'s block; `MAX_TURN_TIMEOUT`'s value and semantics are unchanged.
  - Execution state: performed

- [x] E-04 REMOVE `TurnBoundWatch.note_progress` AND ITS TWO DRIVER CALL SITES. Once E-03 lands, its body only clears a field that no longer exists, so it would be a method that does nothing on every stdout line. Delete the method, then in `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn` delete the `turn_bounds.note_progress()` line and the two-line `# lanectn lhmrhx E-04: progress DISARMS the permission bound (resettable)` comment above each. In `oc_runipd.run_opencode`'s `TurnBoundWatch` construction comment, replace "See `lane_containment.PERMISSION_TIMEOUT` / `MAX_TURN_TIMEOUT` for each one's measured-from instant and reset semantics" with a pointer to `MAX_TURN_TIMEOUT` alone, and "the two driver-side bounds" with the one. Also correct the `MissingInputObserver` docstring in `lane_containment`, which says `observe_line` is called "exactly like `TurnBoundWatch.note_progress` already is", so it no longer names a deleted method. Do not touch `watchdog.touch()`, `statusline.touch(...)`, the observer calls, or the `TurnBoundWatch(...)` construction arguments other than any `permission_timeout=` (neither driver passes one today).
  - Depends on: E-03
  - Expected outcome: no `note_progress` symbol remains in `agent_workflows/`; each driver's stdout loop is otherwise byte-for-byte unchanged; both drivers still construct and enter `TurnBoundWatch` exactly as before.
  - Execution state: performed

### Task group 3: tests

- [x] E-05 DELETE `tests/test_permission_bound_disabled.py`. All four of its tests (`test_default_construction_does_not_arm`, `test_armed_it_fires`, `test_progress_disarms_it`, and the no-observation case) exercise only the permission half, so after E-03 none of them has a subject. Do not port them.
  - Depends on: E-03
  - Expected outcome: the file is gone (`git rm`), and nothing in `tests/` imports `BOUND_PERMISSION` or calls `note_permission_request`.
  - Execution state: performed

- [x] E-06 STRIP THE PERMISSION CASES FROM `tests/test_turn_bounds.py`, so the file tests only the bound that remains (GUIDING_PRINCIPLES P16: no `inspect`, no `ast`, no reading of `agent_workflows/` source). The tests to delete are `test_real_child_permission_bound_kills_process` and `test_reset_asymmetry_permission_disarmed_by_progress`. Every remaining `TurnBoundWatch(...)` call loses its `permission_timeout=` keyword. In `test_constants_names_defaults_and_zero_disable` the `PERMISSION_TIMEOUT`, `BOUND_PERMISSION` and `PERMISSION_DEADLINE` lines go, replaced by one behavioral assertion that `TurnBoundWatch(reap=..., permission_timeout=1.0)` raises `TypeError`, so a reintroduced permission knob is a visible interface change. `test_permission_bound_disabled_by_default_and_unproven_detector` becomes `test_max_turn_is_the_only_turn_bound`, keeping only its real wedged child terminated by `MAX_TURN_TIMEOUT`, with its "RECORDED FINDING (2026-09-30 ...) unproven detector" docstring replaced by one line citing spec R4.4 as amended by this plan. The module docstring's criteria list and the `# Task group 3: the unproven detector and the host overlap (A10c, A10d)` banner are updated to what survives E-07. `test_non_isolated_prompt_byte_identical_and_names_neither_bound` stays unchanged, since its forbidden-token list still correctly asserts the prompt names no bound constant.
  - Depends on: E-04, E-05
  - Expected outcome: `tests/test_turn_bounds.py` names no permission symbol except inside the `TypeError` assertion's keyword (and the prompt test's unchanged forbidden-token list), and every remaining test passes EXCEPT `test_reset_asymmetry_max_turn_survives_progress`, which still calls the deleted `note_progress()` until E-09 replaces it.
  - Execution state: performed

- [x] E-09 REPLACE `test_reset_asymmetry_max_turn_survives_progress`, which today proves "nothing resets `MAX_TURN_TIMEOUT`" by looping on the deleted `note_progress()`, WITH A REAL CHATTY CHILD. Spawn a `sys.executable -c` loop that prints and flushes a line every 10ms (with `stderr=subprocess.DEVNULL`, since the shared reaper's SIGINT makes the child print a `KeyboardInterrupt` traceback), drain its stdout in a reader thread so the pipe never fills, and count the lines it reads so the test can also assert the child produced output throughout (a line count well above zero, proving the turn was chatty rather than silent), and arm `TurnBoundWatch` with `max_turn_timeout=0.3` and the default `bound_expiry_reaper`. Assert a negative return code within a 3s wait ceiling, `elapsed >= 0.3`, and `item["turn_bound_expiry"]["bound"] == BOUND_MAX_TURN`. This is the chatty-but-wedged turn `MAX_TURN_TIMEOUT` exists for, now proven against a process that keeps producing output rather than against a reset method.
  - Depends on: E-06
  - Expected outcome: one new passing test in `tests/test_turn_bounds.py` that a stubbed `_expired` makes fail. Demonstrated feasible at review on HEAD `b1b2fab2b` with a scratch script of exactly this shape: real watch gave rc `-2` at 0.43s, bound `max-turn-timeout`, 33 lines read; with `_expired` stubbed to `lambda self, now: None` the child survived to the 3.0s ceiling with 295 lines read and no expiry record.
  - Execution state: performed

### Task group 4: the spec contract

- [x] E-07 AMEND SPEC `7ckptx` IN THE SAME CHANGE, declared in `- Scope-Paths:`. Without this the code would violate an approved contract, since A10b currently requires the constants be named `PERMISSION_TIMEOUT` and `MAX_TURN_TIMEOUT` and that `PERMISSION_TIMEOUT` default to `0`. Follow the spec's own withdrawal convention ("WITHDRAWN by R3.3a. Formerly: ..."), keeping the original text after "Formerly:" so history stays readable. Specifically: R4.4's "Two bounds, whose defaults are NORMATIVE" becomes one bound, with the TIMEOUT naming rationale kept; R4.4(a) becomes "WITHDRAWN by maintainer ruling (backlog `e6zeta`, plan `15db4k`). Formerly: ..." and states the reason in one sentence (a permission ask never reaches the driver's stdout, research `7so8uz`; the R4.1 deny posture closed the isolated-turn deadlock class by denial; GUIDING_PRINCIPLES P6); R4.4b is withdrawn the same way; R4.4c's "Neither bound" and "Both bounds MUST still accept `0`" and R4.4's "EXPIRY BEHAVIOR for both" refer to `MAX_TURN_TIMEOUT` alone; A10 (synthetic unanswered permission request) is withdrawn, and its surviving obligations (safe-failure disposition, the record names which bound fired, termination through the one shared reaper) are kept as the max-turn version of the criterion; A10b asserts only `MAX_TURN_TIMEOUT` (name, 4-hour default, accepts `0`, armed for isolated and non-isolated turns, docstring states measured-from and reset facts); A10c is withdrawn, and its surviving obligation (the artifact states that `MAX_TURN_TIMEOUT` is the only driver bound covering a permission deadlock) moves into A10b, matched by the paragraph E-03 relocates; A10e's "neither bound" and "both bounds" refer to the one; and the plural "R4.4 driver bounds" / "driver-side bounds" wherever it appears (measured at review: the early host-posture summary, R4.1, R4.1a, and A8b) becomes singular. Find every plural reference with `grep -n "R4.4 driver bounds\|driver-side bounds\|two bounds\|both bounds\|neither bound" <spec>` rather than trusting this list (R4.4d's "the two bounds would fire" means the HOST timer plus the driver timer, is still true, and stays). DO NOT weaken R4.4's core obligation that the driver bound EVERY unattended turn independently of the host, which `MAX_TURN_TIMEOUT` still meets; do NOT change R4.4a, R4.4d, A10d, or the spec's `- Status:`. Record the amendment through the owner verb, `aw specs note <spec path> --message "AMENDED <date> (4xtpvg-02 15db4k): R4.4 and R4.4(a)/R4.4b/R4.4c, A10/A10b/A10c/A10e amended on the maintainer's DELETE ruling for backlog e6zeta; the permission bound is removed and MAX_TURN_TIMEOUT is the single R4.4 turn bound"`, matching the existing `AMENDED ...` notes, rather than hand-writing a history line.
  - Depends on: E-03
  - Expected outcome: no requirement or criterion in the spec requires a `PERMISSION_TIMEOUT`, a permission detector, or a second bound; the withdrawn text remains readable after "Formerly:"; the spec's history carries the `AMENDED` note; `aw specs check` is no worse than E-02's baseline.
  - Execution state: performed

- [x] E-08 SWEEP FOR SURVIVING REFERENCES AND RECONCILE. Run `grep -rn "PERMISSION_TIMEOUT\|BOUND_PERMISSION\|note_permission_request\|permission_timeout\|_permission_pending_since\|note_progress\|test_permission_bound_disabled" agent_workflows tools tests docs .aw/records/specs` and resolve every hit inside `- Scope-Paths:` (a hit in a withdrawn spec clause's "Formerly:" text, or in a spec `## Workflow history` note, is correct and stays). A hit OUTSIDE `- Scope-Paths:` is a scope finding: report it and do not edit it, since the finalize scope gate reconciles declared against actual paths. Historical records (`.aw/records/plans/executed/`, `reviews/`, `walkthroughs/`, `research/`, `backlog/done/`) are NOT edited: they were true when written and AGENTS.md forbids rewriting an executed plan.
  - Depends on: E-04, E-06, E-07, E-09
  - Expected outcome: the pasted grep output, with every remaining hit classified as either a withdrawn-clause quotation, a history note, a historical record, or an out-of-scope finding reported rather than edited.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Tests assert behavior, never code structure (GUIDING_PRINCIPLES P16). This is why E-06 and E-09 prove the remaining bound with real child processes and an interface-level `TypeError`, and why no test asserts that a symbol is absent by reading source or counting callers.
- A plan MAY amend a spec and MUST declare the `.spec.md` path in `- Scope-Paths:`; both runners announce declared spec edits before the run and reconcile them at finalize (`AGENTS.md`, "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT"). Spec history is written through `aw specs note`, matching the `AMENDED <date> (<set>-<NN> <id6>): ...` notes already in `7ckptx`.
- The spec's withdrawal convention is "WITHDRAWN by <authority>. Formerly: <original text>" (for example R3.4 and A7b in `7ckptx`), which keeps a withdrawn requirement readable instead of deleting it.
- R4.4c's KISS ruling forbids adding a config entry or CLI flag for a bound; deletion adds none, so A10e's negative criterion still holds.
- `- Approval:` is present only on a human `approved` plan; `auto-approved` (the `--full-auto` tier) must not carry it (`ipd_schema`: "Approval iff Status is approved (auto-approved does NOT carry human Approval)"). E-01 relies on this to tell a human ruling from an automated clear, as a backstop to OQ-01.
- An open question carrying `- Blocking: yes` makes `aw ipd lint` report `IPD-Q501` at `author`, `review-finalize` and `pre-execution` alike (re-measured at review on a scratch copy of this plan: exit 1 with `IPD-Q501` at all three), which is what holds a policy decision away from `--full-auto`.
- Executed plans, reviews, walkthroughs and research records are historical and are not edited (AGENTS.md execution contract).

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | The trigger has never had a production caller | `grep -rn note_permission_request agent_workflows tools` at HEAD `ac25dd246` returns only the definition in `lane_containment.TurnBoundWatch`; `git log -S note_permission_request -- agent_workflows` returns exactly one commit, `8a491d4c1` (2026-09-05), which introduced it. | The bound cannot have fired in production, so deleting it changes no runtime behavior a turn can observe. |
| F-2 | `note_progress` exists only for the permission bound | Its body is `with self._lock: self._permission_pending_since = None`, and its docstring says it "Deliberately does NOT touch `MAX_TURN_TIMEOUT`". Callers: `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn`, each once per stdout line, under the comment "progress DISARMS the permission bound (resettable)". | Keeping it after E-03 would leave a no-op method called on every stdout line, so E-04 removes it and both call sites. |
| F-3 | No reader of run records depends on `permission-timeout` | `turn_bound_expiry` and the `turn-bound-expired` event are written only by `lane_containment.bound_expiry_reaper` and read by no module in `agent_workflows/` (`grep -rn "turn_bound_expiry\|turn-bound-expired\|permission-timeout" agent_workflows`). Pending plan `ytas91` (fixfirst Order 04) cites `bound_expiry_reaper._expire` for its turn-limit kind, keyed on the max-turn record. | Removing `BOUND_PERMISSION` breaks no consumer. `ytas91` depends only on the max-turn path, which this plan keeps. |
| F-4 | Test surface is two files | `tests/test_permission_bound_disabled.py` (4 tests, all permission-only) and `tests/test_turn_bounds.py` (12 tests; 2 permission-only, 2 using `note_progress` or permission args in part, the rest passing `permission_timeout=0.0` explicitly). No other test references `TurnBoundWatch`, `note_progress`, or a permission symbol. Baseline: `python3 -m pytest -o addopts="" -q tests/test_turn_bounds.py tests/test_permission_bound_disabled.py` gives `16 passed in 3.41s`. | E-05, E-06 and E-09 cover every affected test. |
| F-5 | The spec requires the constants exist | `7ckptx` A10b: "Assert the two constants are named `PERMISSION_TIMEOUT` and `MAX_TURN_TIMEOUT` ... `PERMISSION_TIMEOUT` defaults to `0`"; R4.4: "Two bounds, whose defaults are NORMATIVE"; R4.4(a) and R4.4b specify the permission bound; A10 demands a synthetic unanswered permission request be terminated "within the permission deadline". | Deletion without E-07 would violate an approved spec, which is why the backlog item called this the larger change and why spec and code move together here. |
| F-6 | The cause was closed another way | Research `7so8uz` (2026-10-01, HEAD `ce55ef615`): zero permission-typed events across 788,504 recorded stdout events; driver-turn asks 1,102 before `8a491d4c1`, 0 across 640 driver turns since 2026-09-13, after the R4.1 deny posture landed in the same commit. Not re-measured here (the corpora are gitignored or outside the lane). | This is the GUIDING_PRINCIPLES P6 case for deleting, cited as a dated measurement. It does not decide the question, and the maintainer does. |
| F-7 | Two honest limits survive deletion unchanged | The deny posture applies to isolated opencode turns only (`oc_runipd.run_opencode` applies `build_permission_policy_env` inside `if work_dir:`; carrier `8ctu3u`), and antigravity has no denial posture by design (spec R4.1, R4.1c). On both, `MAX_TURN_TIMEOUT` and the stall watchdog were already the only effective bounds, because the permission bound was never armed. | Deletion does not widen either gap. E-03's dated sentence on `MAX_TURN_TIMEOUT` should not imply a host-wide closure. |

## Proposed changes (ordered, validatable)

1. Confirm OQ-01 records the maintainer's DELETE ruling and a human approved this plan, then capture the suite, `aw check` and `aw specs check` baselines (E-01, E-02).
2. Remove the permission half of `TurnBoundWatch` and its constants, and rewrite the prose that named it (E-03).
3. Remove the now-no-op `note_progress` and its two driver call sites (E-04).
4. Delete the permission-only test file, strip the permission cases from `tests/test_turn_bounds.py`, and add a real chatty-child max-turn test (E-05, E-06, E-09).
5. Amend spec `7ckptx` R4.4 and A10 family in the same change, recorded through `aw specs note` (E-07).
6. Sweep for surviving references and reconcile within scope (E-08).

## Deferred / out of scope (with reason)

- THE KEEP BRANCH. If the maintainer rules KEEP, nothing in this plan runs: retire it with `aw ipd set not-executed 15db4k --message "maintainer ruled KEEP for e6zeta"` and close the item with `aw backlog set done e6zeta --evidence .aw/records/plans/executed/20261001-4xtpvg-01-0b7fic-record-that-stdout-permission-detection-is-impossible-keep-t.ipd.md`, which is the item's own KEEP path.
  - Carrier-Declined: the KEEP outcome needs no new work; `0b7fic` already documents and tests the unarmed bound, as backlog `e6zeta` states.
- CLOSING THE NON-ISOLATED DENY-POSTURE GAP (F-7). A behavior change for a turn class that legitimately works in the main checkout, with its own risk profile.
  - Carrier: 8ctu3u
- A LOG-FED PERMISSION DETECTOR. Refused on measurement by `0b7fic` (15 false kills of 1,149 healthy turns at 30s, zero cases the stall watchdog misses; research `7so8uz`). Deleting the mechanism makes that refusal structural.
  - Carrier-Declined: deliberately not wanted on current evidence; a future host whose stdout carries a permission event would reopen it as new design work.
- EDITING HISTORICAL RECORDS that cite the removed symbols or `tests/test_permission_bound_disabled.py` (executed plan `0b7fic`, reviews, walkthroughs, research `7so8uz`, backlog `4xtpvg`). They were true when written and the execution contract forbids rewriting an executed plan.
  - Carrier-Declined: historical records are left as written by policy; the spec's `AMENDED` note and E-03's dated sentence point a reader forward.
- A CHANGELOG ENTRY. The removed constants and method were internal, never armed, and reachable by no CLI flag or config entry (R4.4c), so no user-visible behavior changes.
  - Carrier-Declined: nothing user-visible changes, so no CHANGELOG entry is owed.

## Scope check

- Over-scope: one temptation. An executor who is removing a bound may want to also "tidy" the stall watchdog, `HOST_CEILING_OFFSET_SECONDS`, or the reaper. Do not: those are untouched, and pending plan `ytas91` edits `bound_expiry_reaper`'s record next, so changing it here creates needless churn.
- Under-scope: none known. `docs/` and `tools/` hold no reference to the removed symbols (measured with the E-08 grep at authoring), and no consumer reads a `permission-timeout` expiry (F-3). If E-08 finds a reference outside `- Scope-Paths:`, it is reported, not silently edited.

## Required tests / validation

1. The bare suite, `python3 -m pytest`, with its ACTUAL summary line pasted. Bars are by NODE ID: no test that passed in E-02's baseline may fail, except the ones this plan deliberately deletes or renames (listed by node id).
2. `python3 -m pytest -o addopts="" tests/test_turn_bounds.py -v`, with every test named and its result shown.
3. A MUTATION CHECK proving the rewritten chatty-child test can FAIL: in a throwaway process, stub `TurnBoundWatch._expired` with `mock.patch.object(lane_containment.TurnBoundWatch, "_expired", lambda self, now: None)` and show the chatty-child test fails (the child survives to the wait ceiling) while restoring it passes. Never edit `agent_workflows/lane_containment.py` to mutate; paste `git status --porcelain` afterwards.
4. A pasted search over `tests/test_turn_bounds.py` showing zero uses of `inspect.getsource`, `inspect.getfile`, `ast.parse`, `ast.walk`, and zero `read_text()` on an `agent_workflows/` path (P16).
5. `aw specs check` no worse than E-02's baseline.
6. `aw ipd lint --phase pre-transition` conforming.
7. `aw check` reporting no NEW violations relative to E-02's baseline.
8. `aw sanitize --agent` exiting zero.

## Spec / documentation sync

- Spec `7ckptx` IS AMENDED (E-07) and is declared in `- Scope-Paths:`. WHY: a spec edit changes the contract every other plan is reviewed against, and this one REMOVES a required constant rather than narrowing its prospects (as `0b7fic` did), so it must move together with the code or the tree violates A10b the moment E-03 lands. The core R4.4 obligation (bound every unattended turn regardless of host) is preserved and still met by `MAX_TURN_TIMEOUT`. The spec's `- Status:` (`implementing`) is not changed.
- `agent_workflows/lane_containment.py` carries the published rationale for the bounds in `#:` blocks and docstrings; E-03 and E-04 rewrite it to describe one bound, and E-03 adds the dated removal note on `MAX_TURN_TIMEOUT`.
- Research `7so8uz` is cited, not edited: its `consumed-by` provenance points at `0b7fic`, which consumed its measurement; this plan consumes the same finding only as a cited reason.
- `CHANGELOG.md`, `README.md`, `AGENTS.md`, `RELEASING.md`, `docs/`: N/A, none documents either bound (measured).

## Open questions

### OQ-01: Keep the permission-bound mechanism documented-but-unarmed, or delete it?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Carrier: e6zeta
- Resolution or deferral rationale: RESOLVED 2026-10-12 by maintainer: Maintainer ruled DELETE. The permission bound is never armed and has no callers; remove the dead mechanism, tests, and spec obligations per GUIDING_PRINCIPLES P6. OPEN FOR THE MAINTAINER, and deliberately BLOCKING (review PR-001, 2026-10-12). The author made this non-blocking on the theory that human approval itself is the ruling, but the review measured that `plan_readiness.is_plan_review_approved` returns `True` for this plan at `Status: reviewed` with `- Readiness: go-pending-approval` (the value the original gate told a reviewer to set), so `aw oc run --full-auto` would have promoted it to `auto-approved` and dispatched an execute turn, leaving E-01 as the only stop. A blocking open question makes the stop mechanical instead: `aw ipd lint` reports `IPD-Q501` at every checkpoint, the review records `- Readiness: no-go`, and `aw ipd set approved` refuses without `--allow-open-questions`. TO ANSWER IT: for DELETE, set this question's `- Status:` to `resolved`, write the ruling here (date, "DELETE", who), run `aw ipd recheck-readiness 15db4k --apply` (which can lift `no-go` only to `go-pending-approval`), then `aw ipd set approved 15db4k --by-human --message ...`. For KEEP, retire this plan and close `e6zeta` as described under Deferred; this question then needs no edit. The status quo is safe while it waits (a bound at `0.0` with no caller cannot fire). EXPECTED SIDE EFFECT while open: `aw check` reports `check.graduation-incomplete` (error) on backlog `e6zeta` and spec `7ckptx`, because their graduation handoff requires this plan to pass author lint; it clears when this question is answered, or when the plan is retired on KEEP. The two readings, from backlog `e6zeta`: KEEP, because `TurnBoundWatch` already gets the resettable semantics right, the runtime cost at `0.0` is zero, `0b7fic` made it tested, and a host whose stdout does carry a permission event could arm it with no redesign; DELETE, because GUIDING_PRINCIPLES P6 refuses a mechanism kept for a hypothetical need, the trigger has never had a caller since `8a491d4c1`, and the deadlock class was closed by denial instead (research `7so8uz`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: OQ-01's `- Status: resolved` line and its recorded DELETE ruling pasted verbatim, the plan's own `- Status: approved` and `- Approval: ...` lines pasted verbatim, plus the newest `## Workflow history` line showing the transition to `approved`. If OQ-01 is unresolved or records KEEP, or the status was `auto-approved` or `- Approval:` was absent, paste that instead, mark E-01 `blocked`, and paste `git status --porcelain` showing no file changed.
  - Observed evidence:
    OQ-01 resolution:
    - Status: resolved
    - Resolution or deferral rationale: RESOLVED 2026-10-12 by maintainer: Maintainer ruled DELETE. The permission bound is never armed and has no callers; remove the dead mechanism, tests, and spec obligations per GUIDING_PRINCIPLES P6.
    Plan status and approval lines:
    - Status: approved
    - Approval: 2026-10-12, human ("approved"): maintainer ruled DELETE for e6zeta
    Workflow history entry:
    - 2026-10-12 approved (aw set, --by-human): maintainer ruled DELETE for e6zeta
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the pasted pre-edit `python3 -m pytest` summary line and any failing node ids, the pasted `aw check` violation summary, and the pasted `aw specs check` result, each captured before the first edit (state the HEAD they were taken at).
  - Observed evidence:
    Captured at HEAD be6560ccf:
    Suite baseline:
    39 failed, 7180 passed, 2 skipped, 3 warnings in 233.29s (0:03:53)
    (39 failing nodes due to /tmp/.aw directory detection during non-project climbing tests)
    aw check baseline:
    Evidence: plans 117 specs 21 prompts 2 research 100 backlog 139 walkthroughs 26 roadmaps 1 comms 1 releases 1 reviews 940 other 1352
    errors 46 warnings 5 info 119
    aw specs check baseline:
    aw specs check: all specs conform. 40 specs checked.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the pasted `git diff -- agent_workflows/lane_containment.py`; a pasted `python3 -c` run showing `hasattr(lane_containment, "PERMISSION_TIMEOUT")`, `hasattr(lane_containment, "BOUND_PERMISSION")` and `hasattr(lane_containment.TurnBoundWatch, "note_permission_request")` all `False`, `lane_containment.MAX_TURN_TIMEOUT == 14400.0`, and `lane_containment.TurnBoundWatch(reap=lambda b, t: None).enabled` `True`; and the rewritten `MAX_TURN_TIMEOUT` `#:` block pasted, showing the measured-from and reset facts survive, the dated removal sentence is present, and the relocated residual-limits statement (non-isolated opencode and antigravity turns, `MAX_TURN_TIMEOUT` plus the stall watchdog as their only bounds) is present.
  - Observed evidence:
    `python3 -c` verification:
    False False False True True
    Rewritten MAX_TURN_TIMEOUT doc block:
    #: Seconds from child-process start after which the turn is terminated no matter what.
    #:
    #: MEASURED FROM: child process start, ONCE.
    #: RESET BY: NOTHING. That is its entire reason for existing alongside the no-progress watchdog: a
    #: chatty-but-wedged turn keeps resetting a no-progress window forever and cannot reset this.
    #:
    #: DEFAULT 4 HOURS. Measured when it was chosen: across 263 recorded turns the longest was 2.46
    #: hours, so this is roughly 1.6x the observed worst case. Accepts `0` to disable.
    #:
    #: SCOPE IS ONE TURN, NOT ONE RUN. Each queue item gets its own fresh budget, so a 22-item run has no
    #: run-wide ceiling and could legitimately span days; a run-wide ceiling does not exist in this design
    #: and is explicitly not required (spec Non-goal 8). Expiry terminates the CHILD, not the driver: the
    #: driver records the safe-failure disposition and proceeds to the next item.
    #:
    #: ANTIGRAVITY OVERLAP, stated rather than discovered (R4.4d). That host ALREADY enforces a per-turn
    #: ceiling of `240m` via `--print-timeout`, numerically the same 4 hours, so two timers with different
    #: owners would fire at the same nominal instant. RESOLUTION: the driver bound is deliberately OFFSET
    #: to fire FIRST on that host (see `driver_bound_for_host`), so a termination is attributable to the
    #: driver, which records WHICH bound fired, rather than to an opaque host timeout. OpenCode has no
    #: host-enforced equivalent, so here the bound is genuinely new.
    #:
    #: CONSEQUENCE, stated plainly: `MAX_TURN_TIMEOUT` is the ONLY driver-side bound covering a permission
    #: deadlock.
    #:
    #: RESIDUAL LIMITS: the R4.1 deny posture applies to ISOLATED opencode turns only (`oc_runipd.run_opencode`
    #: applies `build_permission_policy_env` inside `if work_dir:`), so a non-isolated unattended turn can
    #: still ask (carrier `8ctu3u`); and antigravity has NO denial posture at all, permanently and by design
    #: (R4.1, R4.1c), so there `MAX_TURN_TIMEOUT` is the whole of the bound half.
    #:
    #: HISTORICAL NOTE: a resettable permission bound existed from `8a491d4c1` (2026-09-05), was never
    #: armed because a permission ask never reaches stdout (research `7so8uz`), and was removed on 2026-10-12
    #: on the maintainer's DELETE ruling (plan `15db4k`, backlog `e6zeta`).
    MAX_TURN_TIMEOUT: float = 4 * 60 * 60.0
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the pasted `git diff -- agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py`, showing, in each driver, only the `note_progress()` line and its two-line comment removed, plus in `oc_runipd` alone the `TurnBoundWatch` construction comment rewritten (the `agy_runipd` construction comment names no permission symbol and stays unchanged); and a pasted `grep -rn "note_progress" agent_workflows` returning no hits.
  - Observed evidence:
    `git diff -- agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py`:
    diff --git a/agent_workflows/agy_runipd.py b/agent_workflows/agy_runipd.py
    @@ -2719,9 +2719,6 @@ def run_agy_turn(
                         statusline.touch("stdout")
                         watchdog.touch()
                         observer.note_stdout_line(raw_line)
    -                    # lanectn lhmrhx E-04: progress DISARMS the permission bound (resettable);
    -                    # `MAX_TURN_TIMEOUT` is deliberately NOT reset. See `TurnBoundWatch`.
    -                    turn_bounds.note_progress()
                         # runstop gq6m2u: the IN-TURN cooperative checkpoint (spec `c4gd2h` R7); the
    diff --git a/agent_workflows/oc_runipd.py b/agent_workflows/oc_runipd.py
    @@ -3171,10 +3171,10 @@ def run_opencode(
                     prior_completed_label=checkpoint_observer.last_checkpoint_label,
                 )

    -        # lanectn Order 03 (`lhmrhx`) E-04, spec R4.4/R4.4a/R4.4b/R4.4c/R4.4d: the two driver-side
    -        # bounds that do not trust the host. See `lane_containment.PERMISSION_TIMEOUT` /
    -        # `MAX_TURN_TIMEOUT` for each one's measured-from instant and reset semantics, which are the
    -        # two facts an identifier cannot carry, and for the one-turn (not one-run) scope.
    +        # lanectn Order 03 (`lhmrhx`) E-04, spec R4.4/R4.4a/R4.4c/R4.4d: the driver-side
    +        # bound that does not trust the host. See `lane_containment.MAX_TURN_TIMEOUT` for its
    +        # measured-from instant and reset semantics, which are the facts an identifier cannot carry,
    +        # and for the one-turn (not one-run) scope.
             #
             # ARMED FOR EVERY UNATTENDED TURN, ISOLATED OR NOT (R4.4a): constructed here, outside any
             # `work_dir` branch, on purpose. R1.3 protects the non-isolated turn's PROMPT TEXT, which
    @@ -3218,9 +3218,6 @@ def run_opencode(
                         log.flush()
                         statusline.touch("stdout")
                         watchdog.touch()
    -                    # lanectn lhmrhx E-04: progress DISARMS the permission bound (resettable);
    -                    # `MAX_TURN_TIMEOUT` is deliberately NOT reset. See `TurnBoundWatch`.
    -                    turn_bounds.note_progress()
                         # Learn our PARENT session id from the stream; it is the key the observer
    `grep -rn --exclude-dir=__pycache__ "note_progress" agent_workflows` returned 0 hits.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted `git status --porcelain -- tests/test_permission_bound_disabled.py` showing the deletion, and a pasted `grep -rn "BOUND_PERMISSION\|note_permission_request" tests` returning no hits.
  - Observed evidence:
    `git status --porcelain -- tests/test_permission_bound_disabled.py`:
    D  tests/test_permission_bound_disabled.py
    `grep -rn "BOUND_PERMISSION\|note_permission_request" tests` returned 0 hits.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the pasted `git diff -- tests/test_turn_bounds.py` showing the two deleted tests, the removed `permission_timeout=` keywords, the rename to `test_max_turn_is_the_only_turn_bound`, and the added `TypeError` assertion; the pasted `python3 -m pytest -o addopts="" tests/test_turn_bounds.py -v` output naming every test and its result; and the pasted P16 search (required test 4) returning zero hits.
  - Observed evidence:
    `python3 -m pytest -o addopts="" tests/test_turn_bounds.py -v`:
    tests/test_turn_bounds.py::test_real_child_max_turn_bound_kills_process PASSED [ 10%]
    tests/test_turn_bounds.py::test_launcher_uniform_arming_opencode PASSED  [ 20%]
    tests/test_turn_bounds.py::test_reset_asymmetry_max_turn_survives_progress PASSED [ 30%]
    tests/test_turn_bounds.py::test_constants_names_defaults_and_zero_disable PASSED [ 40%]
    tests/test_turn_bounds.py::test_launcher_uniform_arming_antigravity PASSED [ 50%]
    tests/test_turn_bounds.py::test_non_isolated_prompt_byte_identical_and_names_neither_bound PASSED [ 60%]
    tests/test_turn_bounds.py::test_antigravity_overlap_and_attribution PASSED [ 70%]
    tests/test_turn_bounds.py::test_max_turn_is_the_only_turn_bound PASSED   [ 80%]
    tests/test_turn_bounds.py::test_bookkeeping_failure_does_not_block_reap PASSED [ 90%]
    tests/test_turn_bounds.py::test_dead_child_not_reaped_twice PASSED       [100%]
    ============================== 10 passed in 2.54s ==============================
    P16 search:
    `grep -n "inspect\.getsource\|inspect\.getfile\|ast\.parse\|ast\.walk\|read_text" tests/test_turn_bounds.py` returned 0 hits.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: the pasted `git diff` of the spec showing R4.4, R4.4(a), R4.4b, R4.4c, A10, A10b, A10c and A10e changed as E-07 specifies, with each withdrawn clause still readable after "Formerly:"; the pasted `aw specs note` command and the new `AMENDED` history line; the pasted `aw specs check` result compared against V-02's baseline; a pasted `grep -n "MUST bound EVERY unattended turn" <spec>` showing R4.4's core obligation intact; and the pasted plural-reference grep from E-07 with each surviving hit classified (singularized, a "Formerly:" quotation, or R4.4d's host-plus-driver sense).
  - Observed evidence:
    `aw specs note` command:
    aw specs note .aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md --message "AMENDED 2026-10-12 (4xtpvg-02 15db4k): R4.4 and R4.4(a)/R4.4b/R4.4c, A10/A10b/A10c/A10e amended on the maintainer's DELETE ruling for backlog e6zeta; the permission bound is removed and MAX_TURN_TIMEOUT is the single R4.4 turn bound"
    `aw specs check`: all specs conform. 40 specs checked.
    `grep -n "MUST bound EVERY unattended turn"`:
    328:R4.4 The driver MUST bound EVERY unattended turn independently of the host's permission decision, whether
    Plural reference grep classification:
    384:antigravity the two bounds would fire at the same nominal time with different owners. (R4.4d host-plus-driver sense; kept)
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: the pasted E-08 grep output, with every remaining hit classified (withdrawn-clause quotation, history note, historical record, or out-of-scope finding reported); the pasted bare `python3 -m pytest` summary line compared by node id against V-02 (the deleted and renamed tests listed); the pasted `aw check` result showing no new violations against V-02; the pasted `aw ipd lint --phase pre-transition` result; and the pasted `aw sanitize --agent` exit status.
  - Observed evidence:
    E-08 grep:
    tests/test_turn_bounds.py:205 (TypeError assertion parameter keyword)
    tests/test_turn_bounds.py:393, 404 (forbidden prompt token list)
    spec 7ckptx:346, 369 (withdrawn clause "Formerly:" quotes)
    Bare test suite:
    39 failed, 7174 passed, 2 skipped, 3 warnings in 205.67s (0:03:25)
    (Same 39 failing nodes as V-02 baseline; 6 fewer passed tests matching deleted tests)
    aw check:
    errors 46 warnings 5 info 119 (identical to baseline, 0 new violations)
    aw sanitize --agent:
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: the new chatty-child test's name and PASSED line from the `-v` run; and the pasted mutation result (required test 3) showing that test FAILS with `TurnBoundWatch._expired` stubbed to `lambda self, now: None` (the child survives to the 3s ceiling) and PASSES without the stub, followed by `git status --porcelain` showing no production file touched.
  - Observed evidence:
    `tests/test_turn_bounds.py::test_reset_asymmetry_max_turn_survives_progress PASSED`
    Mutation failure with _expired returning None:
    FAILED tests/test_turn_bounds.py::test_reset_asymmetry_max_turn_survives_progress
    AssertionError: child survived wait timeout (rc='TIMEOUT(survived)' elapsed=3.002s fired=None record=None)
    `git status --porcelain`: no production files modified by mutation check.
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THE MAINTAINER'S DELETE RULING FOR BACKLOG `e6zeta` IS RECORDED BY RESOLVING OQ-01, then approving.
OQ-01 is `- Blocking: yes` and `open`, so `aw ipd lint` reports `IPD-Q501` at every checkpoint and the
review readiness is `no-go`: neither `--full-auto` nor a reviewer can clear this plan, because the
remaining question is policy, not plan quality. (Measured at review: with OQ-01 non-blocking and
`- Readiness: go-pending-approval`, `plan_readiness.is_plan_review_approved` returned `True`, i.e. the
`--full-auto` auto-approve predicate would have cleared it.) DELETE path: the maintainer resolves OQ-01
recording "DELETE", runs `aw ipd recheck-readiness 15db4k --apply`, then
`aw ipd set approved 15db4k --by-human --message ...`; E-01 re-checks all three before any edit. KEEP
path: retire this plan to `not-executed` and close `e6zeta` as described under Deferred.

ORDERING WITH SIBLING `thzrpo` (same Set, Order 2, same `lane_containment.py` and spec): they share no
dependency edge on purpose, since each is valid alone and the runner's isolated worktrees plus the
merge-and-revalidate gate handle the shared files. The only semantic coupling is `thzrpo` E-04's edit
to the `RESIDUAL LIMITS:` paragraph, which E-03 here MOVES rather than deletes; re-read it at execution.
If `thzrpo` has not executed, E-03 moves it as it reads now and `thzrpo` must then edit it at its new
home on `MAX_TURN_TIMEOUT` (report that in this plan's execution record so `thzrpo`'s executor sees it).

WHAT A REVIEWER SHOULD CHECK HARDEST: that E-07 removes every spec obligation that names the
permission bound (R4.4, R4.4(a), R4.4b, R4.4c, A10, A10b, A10c, A10e) while leaving R4.4's core "bound
every unattended turn" obligation intact; and that E-09's chatty-child test really fails under the
`_expired` mutation, since it replaces the only test of "nothing resets `MAX_TURN_TIMEOUT`".

Execution contract: commit ONLY the paths named in `- Scope-Paths:`, through
`aw commit 15db4k -- <paths>`, never `git add -A`, and never push. This is a SHARED CHECKOUT: check
the staged set with `git diff --cached --name-only` before committing and re-check after any failed
raw commit attempt. Run the suite BARE as `python3 -m pytest` and PASTE ITS ACTUAL SUMMARY LINE. The
same rule applies to every grep, diff, mutation result, and check the `V-*` items require. The
terminal move to `executed/` goes through the lifecycle tooling (`aw ipd finalize`, or the runner in
a managed lane), only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass`.
