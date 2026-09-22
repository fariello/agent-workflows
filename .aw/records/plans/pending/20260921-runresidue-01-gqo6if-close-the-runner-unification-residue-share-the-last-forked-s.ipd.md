# IPD: Close the runner unification residue: share the last forked symbols or record each as genuinely host-specific

- Date: 2026-09-21
- Kind: child
- Concern: The `rununify` Set substantially met the maintainer's 2026-09-16 directive ("at the end of the SET, there should be one code base shared by the two runners that contains 100% of the otherwise redundant code that currently is duplicated between the two runners") but did not fully meet it, and its orchestrator is about to retire. MEASURED 2026-09-22 at HEAD `f763be8c` by classifying each shared symbol's BODY: of 57 symbols defined in BOTH `oc_runipd` and `agy_runipd`, 32 have BOTH sides delegating into `runner_shared` and 5 have one side delegating, which is the extraction working. A residue does not. THE RESIDUE IS REPORTED AS A RANGE, 7 to 20 symbols, because two defensible tests disagree and the difference is itself the finding: under a STRICT test (neither side calls ANY `runner_shared` symbol anywhere in its body) it is 7 symbols / 170 agy lines; under a LOOSE test (neither side is a single-statement delegation) it is 20 symbols / 667 agy lines. The 13 symbols between the two tests call into shared code somewhere but still carry substantial per-host bodies, so whether each is "shared" is exactly the judgement this plan exists to make per symbol rather than by picking a threshold. ONE CASE IS UNAMBIGUOUS AND IS THE ANCHOR: `reclaim_lanes_on_interrupt` is 174 lines on EACH side at 0.998 similarity after host-token normalisation, i.e. copied code rather than a host difference.
- Scope: Per symbol in the residue, either SHARE it (one implementation in `runner_shared`, host-shaped shell on each side) or RECORD IT AS GENUINELY HOST-SPECIFIC against the maintainer's own test ("one host does A, the other NOT A") with the evidence. IN: the 7 strict-test symbols, which are unambiguous; the 13 loose-test symbols, each decided and recorded; and `reclaim_lanes_on_interrupt`, which the strict test misses only because both copies call shared helpers while remaining near-identical to each other. OUT: re-doing any of the 11 executed `rununify` children's work, changing the five large host-shaped functions the Set always expected as residue (`run_queue`, `main`, `build_parser` and their kin already delegate), and any behavior change at all - this is extraction, so a behavior difference found mid-flight is a finding to report, not a thing to fix here.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, agent_workflows/runner_shutdown.py, tests/test_runner_shared.py, tests/test_runner_refork_guard.py, tests/test_rununify_characterization.py, .aw/records/research
- Item-Dependencies: none
- Status: to-review
- Set: runresidue
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: gqo6if

## Workflow history

- 2026-09-21 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.
- 2026-09-21 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored at the maintainer's explicit direction of 2026-09-22, given through `/askme` when they resolved `rununify`'s orchestrator question: "Mark it done, file the rest as new work ... BUT Write the plan NOW. Don't wait." So this plan exists BEFORE that orchestrator retires, which removes the one risk their chosen option rested on - that a deferred follow-up never gets filed. It carries `- From-Plan-Verdict: 40it5e` in spirit: `40it5e` E-04 is the item that must name this Set as the carrier of the residue.

## Goal

Finish what the directive asked for, or state precisely and with evidence why the remainder cannot be
finished. Either outcome is acceptable; an unexamined remainder is not. The deliverable is that after this
plan, every symbol still defined in both runners is either ONE implementation with two host shells, or
carries a recorded per-symbol justification a reader can check against the maintainer's own test.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure, then decide per symbol

- [ ] E-01 COMMIT THE SCANNER, so every figure in this plan is reproducible and the next reader is not taking a number on trust. The `rununify` Set's own PR-006 records that its original baseline came from an ad-hoc scan that no longer exists, which is precisely why its headline figure could not be re-derived and why one measurement in this area has already been quoted wrongly. So: commit a scanner that takes both runner modules, classifies each shared top-level symbol as BOTH-DELEGATE / ONE-SIDE-DELEGATES / NEITHER-DELEGATES, reports the strict and loose counts SEPARATELY with the test each uses stated in its own output, and prints a per-symbol table with line counts and a host-token-normalised similarity. It must be runnable by a reader with one command.
  - Depends on: none
  - Expected outcome: a committed scanner plus its pasted output at execution HEAD, reporting both the strict count and the loose count and naming which test produced each. A single number without its test named FAILS this item.
  - Execution state: pending

- [ ] E-02 DECIDE EVERY RESIDUE SYMBOL AGAINST THE MAINTAINER'S OWN TEST, per symbol, and immortalize the table. The test is theirs and is quoted in `rununify`'s own child-breakdown note: `oc_runipd` is the preferred version "unless a difference is a real capability (one host does A, the other NOT A)". Apply exactly that. For each symbol record: the two line counts, the normalised similarity, the decision (SHARE or HOST-SPECIFIC), and for HOST-SPECIFIC the capability difference in one sentence naming what one host does that the other does not. A similarity figure is NOT a decision - `_record_forced_stop` at 0.683 may be a real capability difference while `_lane_reclaim_prompt` at 0.967 may be pure duplication - so do not let the number decide for you.
  - Depends on: E-01
  - Expected outcome: a research artifact created with `aw research new` (never hand-named) holding the per-symbol table for every residue symbol, with a SHARE/HOST-SPECIFIC decision and, for each HOST-SPECIFIC, the capability sentence. The counts must reconcile with E-01's output.
  - Execution state: pending

### Task group 2: share what should be shared

- [ ] E-03 SHARE `reclaim_lanes_on_interrupt` FIRST, because it is the unambiguous case and it de-risks the rest. 174 lines on each side at 0.998 similarity after host-token normalisation: this is copied code, not a host difference, and it is the single largest true duplication in the residue. Lift it to ONE implementation in `runner_shared` with whatever host-specific values it needs injected (follow the `HostLabels` precedent the `hostdedup` Set established rather than inventing a second mechanism), leave a thin host-shaped shell on each side, and re-base any guard that pins it as forked. PURE MOVE, NO BEHAVIOR CHANGE.
  - Depends on: E-02
  - Expected outcome: one implementation, two shells, both hosts' suites green, and the scanner from E-01 showing this symbol moved out of the NEITHER-DELEGATES class.
  - Execution state: pending

- [ ] E-04 SHARE EVERY OTHER SYMBOL E-02 DECIDED `SHARE`, grouped so each pass is reviewable. The residue clusters naturally: STOP/SIGNAL handling (`_record_forced_stop`, `_record_checkpoint_stop`, `_record_deliberate_stop`, `_observe_between_turn_stop`, `install_stop_triggers`, `handle_stop_command`, `terminate_process`, `requeue_interrupted`, `reconcile_interrupted`), LIFECYCLE (`driver_finalize`, `set_plan_approved`), LOCK/BASE (`run_lock`, `locked_run`, `evaluate_clean_base_for_launch`), and the remainder (`_lane_reclaim_prompt`, `_escalation_recorder`, `_budget_breach_recorder`, `_add_output_mode_flags`, `build_isolation_notice`, `disable_lane_prompt`). TREAT THE STOP CLUSTER WITH PARTICULAR CARE: it is the code that runs when an operator interrupts a run, so a regression there is discovered at the worst possible moment, and spec `c4gd2h` R19 governs what a stopped item may and may not do. If a symbol resists sharing for a reason E-02 did not anticipate, RECORD THAT and leave it forked rather than forcing it.
  - Depends on: E-03
  - Expected outcome: every `SHARE` symbol has one implementation; the scanner shows the NEITHER-DELEGATES class reduced to exactly the `HOST-SPECIFIC` set E-02 recorded; any symbol that resisted is named with its reason.
  - Execution state: pending

- [ ] E-05 PROVE NO BEHAVIOR CHANGED, on the terms `rununify` itself established. The suites are asymmetric - measured in that Set at 95 opencode runner tests against 21 agy - so "both suites green" is NOT sufficient evidence for an agy-side change, which is the precise reason its E-02 called for a characterization baseline. Extend `tests/test_rununify_characterization.py` (authored by `40it5e`; create it if that plan has not executed) to pin the CURRENT observable behavior of both hosts for every symbol this plan touches, BEFORE touching it, and show the pinned tests still pass afterwards. Then paste a bare `python3 -m pytest`.
  - Depends on: E-04
  - Expected outcome: characterization tests written BEFORE each change and passing after, named per symbol; plus the bare suite summary line. A green suite alone does NOT satisfy this item.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- THE MAINTAINER'S TEST FOR A LEGITIMATE HOST DIFFERENCE is "one host does A, the other NOT A", recorded in `rununify`'s child-breakdown note together with the ruling that `oc_runipd` is the preferred version otherwise. This plan applies that test rather than inventing a similarity threshold.
- `HostLabels` IS THE ESTABLISHED MECHANISM for expressing a real per-host difference behind one implementation (the `hostdedup` Set). Do not invent a second one.
- SOURCE-READING TESTS ARE WORK, NOT VETOES (`rununify`'s supporting ruling of 2026-09-16): 44 test files assert on the SHAPE of source, so a test pinning a duplication is a thing to update, not a reason to abandon a unification.
- SYMBOL COUNTS OVER LINE COUNTS, per `rununify`'s Goal: its symbol figures reproduced at review while its line figures did not.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH | AST body-classification at HEAD `f763be8c` | Of 57 symbols defined in both runners, 32 have BOTH sides delegating to `runner_shared` and 5 have one side delegating. So the `rununify` Set substantially SUCCEEDED, and any report of its outcome that counts those 32 as duplication is wrong. |
| F-02 | HIGH | strict vs loose classification, same HEAD | The residue is 7 symbols / 170 agy lines under a strict test (neither side calls any shared symbol) and 20 symbols / 667 agy lines under a loose test (neither side is a single-statement delegation). The 13 between them call shared code while keeping substantial per-host bodies. THE DISAGREEMENT IS THE FINDING: no threshold resolves it, so E-02 decides per symbol. |
| F-03 | HIGH | `difflib` similarity after host-token normalisation | `reclaim_lanes_on_interrupt` is 174/174 lines at 0.998. That is copied code, and the strict test misses it only because both copies call shared helpers. It is the anchor case and E-03's sole subject. |
| F-04 | MEDIUM | `rununify` PR-006, quoted | That Set's original headline figure came from an ad-hoc scan that does not exist in-tree, so it could not be re-derived. A measurement in this area has ALREADY been quoted wrongly once (58 symbols / 2711 lines, corrected to 20 / 667 in `40it5e` OQ-01). E-01 commits a scanner so this plan's numbers cannot rot the same way. |
| F-05 | MEDIUM | `rununify` E-02, quoted | The two hosts' suites are asymmetric (95 oc runner tests to 21 agy), and `integrate_lane_branch` once had ZERO references anywhere in `tests/`. So a reconciliation can change agy behavior with both suites green, which is why E-05 requires characterization pins written BEFORE each change. |
| F-06 | LOW | the residue table | The stop/signal cluster is 9 of the 20 loose-test symbols. It is the code that runs when an operator interrupts a run, and spec `c4gd2h` R19 constrains it, so E-04 calls it out for particular care rather than treating it as ordinary extraction. |

## Proposed changes (ordered, validatable)

1. Commit a scanner reporting both tests with their definitions (E-01).
2. Decide every residue symbol SHARE or HOST-SPECIFIC against the maintainer's test, and immortalize the table (E-02).
3. Share `reclaim_lanes_on_interrupt`, the unambiguous 174/174 case (E-03).
4. Share every other `SHARE` symbol, by cluster (E-04).
5. Prove no behavior changed, with characterization pins written first (E-05).

## Deferred / out of scope (with reason)

- THE FIVE LARGE HOST-SHAPED FUNCTIONS. `run_queue` (456 agy lines) makes 10 calls into `runner_shared`;
  `main`, `build_parser`, `expand_selectors` and `retry_deferred_integrations` all delegate too. They are
  the host-shaped shells the Set always expected to remain, so they are not residue and this plan does not
  touch them.
- RE-DOING ANY EXECUTED `rununify` CHILD'S WORK. All 11 are `executed`; this plan starts from their result.
- ANY BEHAVIOR CHANGE. This is extraction. A behavior difference discovered mid-flight is a finding to
  REPORT (and, if it matters, a separate plan), because fixing it inside a pure-move item would make the
  move unverifiable.
- THE ORCHESTRATOR'S RETIREMENT. The maintainer decided 2026-09-22 that `rununify`'s parent retires as
  `executed` with the residue filed as this new Set. This plan does not reopen that.

## Scope check

- Over-scope: none.
- Under-scope: none. Every symbol in the loose-test residue is either shared (E-03/E-04) or recorded
  host-specific with evidence (E-02).

## Required tests / validation

`tests/test_rununify_characterization.py` extended per symbol before each change (E-05), both hosts' runner
suites, the re-fork guard in `tests/test_runner_refork_guard.py` re-based as symbols move, and a bare
`python3 -m pytest` judged on failing-node DELTA against a baseline measured in the same session.

## Spec / documentation sync

N/A for contracts: this plan moves implementations without changing behavior or any public surface. If
E-04 finds that sharing a stop-handling symbol would change what spec `c4gd2h` R19 guarantees, that is a
finding to report and the spec amendment becomes its own decision rather than a silent rider here.

## Open questions

### OQ-01: Should a symbol whose two copies differ only in log or prompt WORDING count as host-specific?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO - IT IS SHARED, WITH THE WORDING INJECTED. Resolved from the repository rather than deferred: `HostLabels` exists precisely to express a per-host string behind one implementation, and the `hostdedup` Set already classified "differs only by a host string" as a UNIFY case (8 of its symbols), not as a capability difference. The maintainer's own test settles it too - differing wording is not "one host does A, the other NOT A". So a wording-only difference is shared with the label injected, and E-02 must not record it as host-specific.

### OQ-02: If a residue symbol's two copies turn out to differ in BEHAVIOR rather than shape, what then?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: REPORT IT AND LEAVE THE SYMBOL FORKED; do not reconcile the behavior inside this plan. Resolved from this plan's own scope fence and from why that fence exists: this is an extraction plan, and its whole validation rests on "no behavior changed", so a pass that also CHANGES behavior cannot be verified by the characterization pins E-05 relies on. A genuine behavioral divergence is a product question about which host is right, which is the maintainer's to settle and may well be a defect in one host. E-04 already instructs recording a symbol that resists rather than forcing it, so this resolution adds the reason rather than a new mechanism.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the scanner's committed in-tree path, the single command a reader runs, and its pasted output showing BOTH the strict and the loose count with each test's definition printed alongside. A report of one number without its test named FAILS, because that is the exact shape of the figure this area has already got wrong once.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the `aw research new` artifact path (tool-created), plus the full per-symbol table quoted, each row carrying two line counts, a similarity, a SHARE/HOST-SPECIFIC decision, and for every HOST-SPECIFIC row a one-sentence capability difference naming what one host does that the other does not. A row justified by a similarity number alone FAILS, per E-02's own instruction.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `git diff --stat` showing one implementation and two shells; the scanner re-run showing `reclaim_lanes_on_interrupt` no longer in NEITHER-DELEGATES; and the characterization pins for it passing both before and after. Paste all three.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the scanner re-run showing the NEITHER-DELEGATES class reduced to EXACTLY the HOST-SPECIFIC set E-02 recorded, quoted side by side so a reader can check the two sets match; plus, for any symbol that resisted sharing, the named reason. A NEITHER-DELEGATES set that does not match E-02's HOST-SPECIFIC set FAILS this item, in either direction.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: for each touched symbol, the characterization test named, shown passing BEFORE the change (pinning present behavior) and AFTER; plus the bare `python3 -m pytest` summary and an EMPTY failing-node delta against a same-session baseline. A green suite offered without the before-pins FAILS this item: F-05 records that both suites stayed green through an agy-side behavior change once already.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY files this plan changed, path-scoped; never `git add -A`; never push.
When reporting tests passed, paste the ACTUAL runner output. Do NOT mark an `E-*` item performed for work
not done, and do NOT fill a `V-*` `Observed evidence` block with anything but observed output.

THE HONESTY RULE THAT MATTERS MOST HERE is the residue count. This plan's own headline number has already
been stated wrongly once in this repository's history (58 symbols / 2711 lines, when the body-level truth
was 20 / 667 loose and 7 / 170 strict), because a NAME-level count treats a genuinely shared function as
duplicated whenever each host keeps a wrapper. So: never report a residue figure without naming the test
that produced it, never let a similarity score stand in for a per-symbol decision, and if the two tests
disagree report BOTH rather than picking the flattering one.

SCOPE FENCE. Touch ONLY the paths in `- Scope-Paths:`. Change NO behavior; if a symbol's copies differ
behaviorally, report it and leave it forked (OQ-02). Do not touch the five large host-shaped functions. If
the work genuinely requires a path outside the fence, make the edit and justify it, since `aw ipd finalize`
refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-
unmodified path carries a `--scope-ack`.

POST-GATE LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` item
must carry observed evidence before the plan moves to `.aw/records/plans/executed/`. The runner owns the
terminal transition; a worker-role process is refused by `AW-LIFECYCLE-ROLE-001`.
