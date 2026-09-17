# Review findings: plan ty3cj6

- Subject-Id: ty3cj6
- Subject-Type: ipd
- Reviewed-At: 2026-09-16
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `34aa40c0`. Structural preflight `aw ipd lint --phase author` CONFORMED (exit 0) before
revision. No pre-review snapshot needed: the plan was committed and unmodified. This is the sixth
`rununify` child reviewed, and it repeats the exact methodological error that reversed child `i3d6ml`.

EVERY NUMBER THIS PLAN STATES REPRODUCED, and that is worth saying first because the plan is careful
about the thing it measured. Verified independently: 381 oc lines and 336 agy; 229 and 227 CODE lines
after stripping comments and blanks; exactly TWELVE differing code lines; exactly TWO bearing a host
token. All seven enumerated differences (F-3 the signature default, F-5 the `repo` binding, F-6 the
`driver_label`, F-7 the `hint` binding, plus the two `register_signal_report` deltas) are real, and the
plan's classification of five of them as pure style is correct. It also correctly identifies `run_queue`
as the least-diverged of the five large functions: I measured all five, and its 12 differing code lines
compare to 189 for `execute_item`, 255 for `build_parser`, 56 for `main` and 41 for `initialize_run`.

THE HEADLINE HAZARD IS FALSE, AND FALSE IN THE DIRECTION THAT MATTERS. F-2 and F-4 assert that
`register_signal_report` is oc-only and must "become a capability the descriptor declares".
`agy_runipd.py:343` imports it from `oc_runipd`, `oc.register_signal_report is agy.register_signal_report`
is True, `tests/test_runner_backlog_close.py:1175` lists it in `_SHARED`,
`test_the_implementation_is_shared_not_copied` asserts that identity, and
`test_agy_does_not_redefine_any_of_the_shared_functions` forbids agy from re-declaring it. So the work
the plan nominates as its central hazard was completed by `bkclose` (`zhr6mc`). F-4 also gets both counts
wrong ("oc calls it twice and agy does not"): oc calls it FIVE times, agy THREE.

THE REAL ASYMMETRY IS A DEFECT, and it is the most valuable thing this review found. oc calls
`register_signal_report` after EVERY `state = load_state(...)` rebind inside the loop; agy omits it after
two, both in the integration-deferral ladder (oc at `oc_runipd.py:8169` and `:8237`, agy at neither).
`oc_runipd.py:8048` states the invariant verbatim, that the call is repeated "after each state reload so
the report never runs off a stale snapshot", and `:8106` repeats it. So on `aw agy run` a SIGINT arriving
after an integration re-attempt reports PRE-reload item states. Two lines fix it, no test covers it, and
it needs no split at all. The plan spent its HIGH finding on a resolved hazard and missed this.

THE BLOCKING DEFECT IS THE SAME ONE THAT REVERSED CHILD 03: body difference was measured, liftability was
inferred. `run_queue` is a DISPATCH LOOP, so its body is almost entirely calls, which is exactly WHY its
own lines barely differ and why nearly everything it does lives behind a name that has not been unified.
Closure-measured, it depends on 41 module-level names: 14 resolve in `runner_shared`, 27 do not, and
ELEVEN of the 27 are functions still DEFINED TWICE (`execute_item`, `retry_deferred_integrations`,
`reconcile_interrupted`, `requeue_interrupted`, `reclaim_lanes_on_interrupt`, `_observe_between_turn_stop`,
`_record_deliberate_stop`, `render_continuation_hint`, `write_report`, `driver_actor`,
`disable_lane_prompt`). Each becomes an injected parameter, and injecting one is the opposite of sharing
it. Worse, `disable_lane_prompt` is pinned PERMANENTLY unmovable by `UnmovableSymbolTests`
(`tests/test_runner_shared.py:1238`) because it mutates `_LANE_PROMPT_DISABLED` through `global` while each
host's diverged `_lane_reclaim_prompt` reads its own copy, so its injection would never become
transitional. The promised "relocation with a parameter" is a relocation with twelve, de-duplicating none.

SIX PINS READ THIS FUNCTION'S SOURCE OR AST AND THREE CANNOT SURVIVE A THIN CALLER.
`tests/test_runner_backlog_close.py:1228` requires `inspect.getsource(mod.run_queue)` to contain both
`emit_shutdown_report()` and `register_signal_report(` on BOTH hosts; `tests/test_oc_runipd_cli.py:233`
and `tests/test_agy_runipd_cli.py:1465` require it to contain `tracker = StreamTracker()` and the exact
string `execute_item(run_dir, state, runnable, recovery=recovery, tracker=tracker)`. Those three fail the
instant the body moves, and no amount of characterization coverage would catch it, because they assert on
SOURCE TEXT rather than behavior. Three more constrain it (`tests/test_lane_tool_identity.py:666` on
except-clause ORDER within the source, `tests/test_runner_stop.py:607` string-indexing from
`def run_queue(`, `tests/test_runner_shared.py:3234`/`:3270` on five required substrings), and
`tests/test_orchestrator_retirement.py:3483` requires an `orchestrate` branch with a `Continue` in agy's
OWN `run_queue` AST, its message stating explicitly that sharing the decider is not sufficient. None of
the seven files was fenced.

ONE MORE MEASUREMENT PIN. `test_no_call_site_was_rewritten` counts `save_state` call sites per runner and
expects 38 oc / 36 agy (I ran it: passes, and the arithmetic is 32+1+1+4 and 30+1+1+4). THIRTEEN per host
are inside `run_queue`, so a split moves a third of the counted population, and that test's own rule
forbids repairing it by editing the literal.

WHAT I FIXED AND WHAT I LEFT. I retracted F-2 and corrected F-4 in place rather than deleting them, so
the false premise stays visible as a retraction; added the closure measurement as a gating E-01 with its
six-class table in the Goal; added E-03 to repair agy's two missing refreshes as a standalone defect fix;
converted the split into E-04, a written ANALYSIS deliverable gated on OQ-03; rewrote E-05 to assert only
what actually changed plus the inverse `disable_lane_prompt` assertion; made non-vacuity bidirectional;
fenced all seven test files; corrected the Project-conventions claim that no runner-to-runner import
exists (the cited guard is a substring check that agy's `from agent_workflows.oc_runipd import (...)`
form evades ten times); and recorded the wrapper-census and host-divergent-constant hazards the plan
missed. I did NOT decide which of four routes the Set takes, because each restructures a Set with nine
pending children and an approved orchestrator.

THE PLAN'S ANALYSIS OF DIFFERENCES IS GOOD WORK RESTING ON THE WRONG QUESTION. It asked "how much do the
two bodies disagree", answered it exactly, and inferred an answer to "can this move", which is a
different question with a much worse answer.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | BLOCKER | IN-SCOPE | C. architecture (closure); G. executability | closure measurement at HEAD `34aa40c0`; `tests/test_runner_shared.py:1238` | **BODY DIFFERENCE WAS MEASURED, LIFTABILITY WAS INFERRED,** the identical error that reversed sibling `i3d6ml`. "12 differing code lines" is exact and is the wrong property. `run_queue` closes over 41 module-level names: 14 resolve in `runner_shared`, 27 do not, and 11 of the 27 are still DEFINED TWICE. `disable_lane_prompt` is pinned permanently unmovable, so its injection can never become transitional. The promised relocation-with-a-parameter is a relocation with TWELVE parameters that de-duplicates none of them. | C:High; U:Low; S:Low; F:High; Overall:High | OPEN | Closure table added to the Goal with all six classes; E-01 added as a gating measurement; the split converted to E-04, an analysis deliverable. The route decision is escalated as OQ-03 with four options and a recommendation. NOT fixed by a plan edit because every route restructures the Set. |
| PR-002 | BLOCKER | UNDER-SCOPE | D. anti-regression; E. testing | `tests/test_runner_backlog_close.py:1228`; `tests/test_oc_runipd_cli.py:233`; `tests/test_agy_runipd_cli.py:1465` | **THREE PINS ASSERT SUBSTRINGS OF `inspect.getsource(run_queue)` THAT A THIN CALLER CANNOT CONTAIN,** and three more parse its source or count its sites (`tests/test_lane_tool_identity.py:666`, `tests/test_runner_stop.py:607`, `tests/test_runner_shared.py:3234`/`:3270`), plus `tests/test_orchestrator_retirement.py:3483` requiring an `orchestrate` branch in agy's OWN `run_queue` AST with the message that the shared decider is not sufficient. Characterization coverage cannot catch these: they assert on SOURCE TEXT, not behavior. None of the seven files was in `Scope-Paths`, so `aw ipd finalize` would refuse every edit as out of scope. | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | OPEN | All seven files fenced; F-10 enumerates each pin with the substring or AST shape it requires; E-04 must state a per-pin verdict on whether a thin caller satisfies it; V-05(c) requires all seven green by name. Whether the pins should be REWRITTEN is part of OQ-03, since three of them were installed by executed plans and rewriting a pin is how a guarantee quietly weakens. |
| PR-003 | HIGH | IN-SCOPE | A. correctness (a false premise); D. anti-regression | `agy_runipd.py:343`; `tests/test_runner_backlog_close.py:1175`, `:1228`; live `is` check | **F-2's HAZARD DOES NOT EXIST AND F-4 INVERTS ITS OWN DIRECTION.** `register_signal_report` is already ONE object reached by both hosts (agy imports it; identity asserted by an existing test; agy forbidden from re-declaring it), so "must become a capability the descriptor declares" describes completed work. F-4's counts are also both wrong: oc calls it five times, agy three, not "oc twice and agy none". The plan spent its central HIGH finding on a resolved problem. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-2 RETRACTED in place with the three citations (retained rather than deleted so the false premise stays visible); F-4 corrected with all five oc line numbers and all three agy; both now point to F-9 as the finding that replaces them. |
| PR-004 | HIGH | UNDER-SCOPE | A. correctness; D. anti-regression | `oc_runipd.py:8048`, `:8106`, `:8169`, `:8237`; `agy_runipd.py:4733`, `:4819`, `:5046` | **AGY IS MISSING TWO `register_signal_report` REFRESHES AND THAT IS A LIVE DEFECT THE PLAN DID NOT FIND.** oc refreshes after every in-loop `state = load_state(...)` rebind; agy omits both integration-ladder sites. oc's own comment states the invariant ("called again after each state reload so the report never runs off a stale snapshot"). So a SIGINT on `aw agy run` after an integration re-attempt reports pre-reload item states. Two lines, no split needed, no test covers it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-9 and as E-03, a standalone repair authorized unconditionally; V-03 requires the count going 3 -> 5 site-for-site plus a test proving post-reload reporting on both hosts. This is now the one product change this plan makes today. |
| PR-005 | MEDIUM | UNDER-SCOPE | E. testing (a pinned census) | `tests/test_runner_shared.py:1148`; ran it: passes at 38/36 | **THE SPLIT MOVES 13 OF 38 AND 13 OF 36 PINNED `save_state` CALL SITES.** `test_no_call_site_was_rewritten` expects those exact counts, and its own documented rule forbids repairing a moved count by editing the literal ("if a count moves and you cannot name the new call site, the wrapper ruling has been undone"). The correct treatment is a documented RELOCATION subtraction, as `RELOCATED_RUN_CHECKED_CALLERS` already does for six moved callers. The plan does not mention the test. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-11 and to Project conventions with the measured counts; Required tests item 6 and V-03(d) require the test green with its 38/36 expectation unchanged, which holds because E-03 adds no `save_state` site. |
| PR-006 | MEDIUM | IN-SCOPE | C. architecture (a guard cited as evidence it is not) | `tests/test_review_findings_cascade.py:308-313`; 10 matches of `from agent_workflows.oc_runipd import` in agy | **THE PLAN CITES A GUARD THAT DOES NOT HOLD.** Project conventions claims `test_no_runner_to_runner_import` forbids a runner-to-runner import. That test is a SUBSTRING check for `"import oc_runipd"`, which agy's `from agent_workflows.oc_runipd import (...)` form does not match; agy uses it ten times, and eight of the names `run_queue` closes over reach agy exactly that way. Citing it as evidence the coupling is absent would mislead an executor about the module graph it is refactoring. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Correction written into Project conventions with the line citation and the count, redirecting to `tests/test_runner_shared.py:955` (`test_runner_shared_imports_neither_runner`), which IS AST-based and does hold. |
| PR-007 | MEDIUM | UNDER-SCOPE | A. correctness (a host-divergent constant) | `oc_runipd.py:366` vs `agy_runipd.py:448`; `tests/test_runner_telemetry_integration.py:597` | **A NINTH DIFFERENCE, INVISIBLE TO A LINE DIFF.** `run_queue` reads `DEPENDENCY_BLOCK_RECOVERY_HINT` twice and the two hosts' values DIFFER (`aw oc runipd resume` versus `aw agy runipd resume`); an existing test records that it "differs per host by design". Lifting it unchanged would print the wrong recovery command on one host. The plan's enumeration missed it because the constant is referenced on IDENTICAL lines. The other three constants it closes over are equal and can move. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-12 with both definitions and the test citation; classified in the Goal table as the single host-divergent constant, so it is a hook input rather than a lift. |
| PR-008 | MEDIUM | UNDER-SCOPE | G. right-sizing and conceptual density | E-02 as authored | **ONE E-ITEM BUNDLED THE ENTIRE SPLIT** (relocating a 381-line dispatch loop, twelve dependency decisions, import rewiring in files of 9,375 and 5,727 lines, and the repair of seven test files), which the count-based lint cannot see. A failure midway leaves the package unimportable, exactly as `i3d6ml`'s F-14 found. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as F-13 and restructured: E-01 measurement, E-02 test-only baseline, E-03 two-line repair, E-04 written analysis, E-05 guard suite. One focused pass each, and `Highest E allocated` raised to 05. |
| PR-009 | LOW | IN-SCOPE | G. dependencies and sequencing | child 03's re-scoped 9 symbols vs this plan's 27 closure names | **THE DECLARED EDGE IS SATISFIED BUT BUYS NOTHING.** `executed:i3d6ml` is honest but child 03 was itself re-scoped at review from 48 symbols to 9, and NONE of the 9 is among the 27 names `run_queue` closes over, so executing it does not reduce this plan's injection count. The children that WOULD are 04 and 07, and this plan is ordered BEFORE 07 while child 11 (`main`) declares `executed:ty3cj6` and therefore waits on this one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-14. The edge is LEFT IN PLACE (it is not false, merely unhelpful) and the useful direction is folded into OQ-03 route B, so the Set's ordering can be corrected once rather than edited from here. |
| PR-010 | LOW | UNDER-SCOPE | E. non-vacuity | Required tests item 3 as authored | **NON-VACUITY WAS ONE-DIRECTIONAL.** "Sabotage the shared core and show the suites fail" proves a guard can fail when something is REMOVED; it says nothing about whether the guard would notice a symbol being MOVED that must not move, which is the specific regression `UnmovableSymbolTests` exists to catch and the one most likely to be committed by a later agent "finishing" the split. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests item 4 now demands BOTH controls: remove an added `register_signal_report` call and show the failure; and move `disable_lane_prompt` into `runner_shared` and show both the new suite and `UnmovableSymbolTests` fail. V-05(b) requires both pasted. |
| PR-011 | LOW | IN-SCOPE | E. achievable bar; F. honest documentation | sibling `i3d6ml` review's measured flake; the plan's item 5 | **THE SUITE BAR LEAVES A KNOWN FLAKE TO BE REDISCOVERED.** "No new failure against the baseline at execution time" gives the executor no baseline; the sibling review measured a load-dependent timeout that passes in isolation. Separately, the gate's reviewer-targets paragraph pointed at F-2, now retracted, so it would have aimed the next reviewer at a false premise. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests item 8 now requires the executor take its own baseline at its own HEAD and reproduce any single failure against it before attributing it; the reviewer-targets paragraph rewritten to F-8, F-9 and F-10; the run-bare flags (`-n0`, second `-q`, `-p no:randomly`) named in the execution contract. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | The plan's central HIGH finding (F-2) asserts `register_signal_report` is oc-only. Accept it, or check? | CHECK, and reject it: the symbol is already shared, and F-4's counts are inverted as well. | (a) Accept the plan's framing, rejected because it is exactly the class of claim a review exists to verify, and a single `is` comparison settles it. (b) Delete F-2 and F-4 as simply wrong, rejected: a retracted finding left visible tells the next reader that the hazard was considered and disproved, whereas a deleted one invites its rediscovery. | `agy_runipd.py:343`; `oc.register_signal_report is agy.register_signal_report` is True; `tests/test_runner_backlog_close.py:1175` and `test_the_implementation_is_shared_not_copied` | yes |
| D-2 | The plan measures 12 differing lines and concludes the split is near-free. Accept, or apply the closure test that reversed child 03? | APPLY THE CLOSURE TEST, and it inverts the conclusion: 27 of 41 names unresolved, 11 still double-defined, 1 permanently unmovable. | (a) Trust the line count, rejected: the identical inference was the BLOCKER in child 03's review three days earlier, and a dispatch loop is the shape most likely to hide it, since its body is nearly all calls. (b) Spot-check a few dependencies rather than enumerate, rejected: a partial closure list produces exactly the confident-but-wrong plan under review. | closure measurement at HEAD `34aa40c0`; child 03's review record F-7; `tests/test_runner_shared.py:1238` | yes |
| D-3 | The split needs twelve injected dependencies. Choose a route myself, or ask? | ASK. Raised as OQ-03, `Blocking: yes`, four routes with costs and a recommendation (re-order behind children 07/09/10/11). | (a) Inject all twelve myself, rejected: it contradicts the maintainer's `818uru` OQ-02 ruling, which chose the thin-wrapper form over uniform injection at SMALLER scale, and it would permanently inject a symbol pinned unmovable. (b) Re-order the Set myself, rejected: it moves the position of a plan that child 11 declares a dependency on, so it is a Set-level sequencing change and the maintainer's call. (c) Reduce the plan to the two host-token lines silently, rejected: that abandons the Set's stated goal for this symbol without saying so. (d) Declare `run_queue` permanently unsplittable myself, rejected for the same reason. | the maintainer's `818uru` OQ-02 wrapper ruling quoted at `tests/test_runner_shared.py:64-70`; `UnmovableSymbolTests`; child 11's `Item-Dependencies: executed:ty3cj6` | yes |
| D-4 | Should the two-line agy `register_signal_report` repair go in this plan, or be deferred as a separate item? | IN THIS PLAN, as E-03, declared explicitly as a DEFECT FIX rather than folded into the relocation. | (a) Defer it to a new backlog item, rejected: the plan already owns this symbol on both hosts and the fix is two lines, so deferring it would leave a known signal-reporting defect live while its owning plan sits blocked on an unrelated decision. (b) Fold it into the split as "part of the reconciliation", rejected outright: it CHANGES agy's behavior, and the parent Set forbids a child changing behavior, so it must be declared as a fix and validated as one, not smuggled in under a no-behavior-change claim. | `oc_runipd.py:8048` stating the invariant; the parent orchestrator's no-behavior-change constraint; the two missing sites measured | yes |
| D-5 | Three pins assert substrings of `run_queue`'s source. Should the plan be told to rewrite them? | NO. E-04 must report a per-pin VERDICT; whether to rewrite is part of OQ-03. | (a) Instruct the executor to rewrite them to behavioral assertions, rejected: all three were installed by executed plans as deliberate guards, and rewriting a pin to accommodate a refactor is how a guarantee quietly weakens; that is the same failure `test_no_call_site_was_rewritten` exists to prevent. (b) Treat them as a hard blocker on ever splitting, rejected as overreaching: a maintainer may legitimately decide a source-text pin should become a behavioral one. | `tests/test_runner_backlog_close.py:1228`; `tests/test_oc_runipd_cli.py:233`; `tests/test_agy_runipd_cli.py:1465`; the invert-do-not-delete precedent in `tests/test_wtiso_characterization.py` | no |

### Deferred and open

- `PR-001` - `OPEN`:
  - Reason: The closure measurement shows the split needs twelve injected dependencies, one of them permanent, and every available route (inject, re-order the Set, reduce the scope, or do not split) either contradicts a standing maintainer ruling or restructures a Set with nine pending children and an approved orchestrator.
  - Remediation Risk: High
  - Axis: complexity, functionality
  - Required decision or evidence: the maintainer's answer to OQ-03, choosing among routes A through D.
  - Consequence if unresolved: `run_queue` stays duplicated. That is the mildest consequence of any blocker in this Set, because at 12 differing code lines out of 229 it is the least drifted of the five large functions, so the ongoing drift cost is genuinely small. The dangerous outcome is not inaction but an executor following the plan as originally written, producing a twelve-parameter shared core and three broken pins.

- `PR-002` - `OPEN`:
  - Reason: Three pins assert substrings of `inspect.getsource(run_queue)` that a thin caller cannot contain, and they were installed by executed plans as deliberate guards. Repairing them is not a mechanical edit: it decides whether a source-text guarantee becomes a behavioral one, which changes what the guard can still catch.
  - Remediation Risk: Medium-High
  - Axis: functionality
  - Required decision or evidence: the maintainer's answer to OQ-03; if a split is authorized, an explicit decision on whether these three pins may be rewritten and to what.
  - Consequence if unresolved: no immediate harm, since the fence now names all seven files and E-04 must report a per-pin verdict. The risk being held open is that a future executor reads three red tests as noise from its own refactor and rewrites them to pass, which would silently retire the shutdown-report and tracker-wiring guarantees.

### Escalation of the irreversible decision

D-5 is judged `Reversible: no`: it declines to authorize rewriting three source-inspection pins, and the
OPPOSITE choice is what cannot be cleanly undone. A pin rewritten from `assertIn("emit_shutdown_report()",
inspect.getsource(run_queue))` to something a thin caller satisfies no longer proves what the original
proved, and nothing in the resulting test records that a weaker guarantee was accepted; the next agent
finds a green test and no trace of the trade. Escalated per the workflow rather than merely recorded: it
is raised in the plan as F-10 with all seven file:line citations, E-04 carries the obligation to state a
per-pin verdict, V-05(c) requires all seven suites green by name, and the `Blocking: yes` OQ-03 puts the
route decision in front of the maintainer before any split executes. D-1, D-2, D-3 and D-4 are reversible
(a plan edit undoes each) and are recorded only.

### Why OQ-03 was not asked interactively

This run had NO interactive question tool available, so the six-part question set could not be put to the
maintainer through a prompt. Per the workflow's non-interactive path, OQ-03 is left explicitly `open`
with `Blocking: yes`, the verdict is `REVIEWED - OPEN QUESTIONS`, and readiness is `no-go`. The full
question, its measurement, all four routes with their costs, and the recommendation are written INTO the
plan's OQ-03 block, so the decision is answerable from the plan alone whenever a channel exists; nothing
required to decide it lives only in this session. `aw ipd lint` refuses the plan at every checkpoint until
it is answered (IPD-Q501, verified firing), which is the intended fail-closed stop rather than a defect.

### Honest limits of this review

- I DID NOT ATTEMPT THE SPLIT. The claim that a shared core needs twelve injected parameters is derived
  from a static closure analysis plus live `is` comparisons, not from having built the core and imported
  it. E-01 re-derives the table at execution HEAD, which is where the number becomes authoritative.
- I DID NOT RUN THE FULL SUITE. I ran the specific pins I cite (`test_no_call_site_was_rewritten`,
  `test_both_drivers_emit_the_shutdown_report_on_normal_exit`, the `test_lane_tool_identity` selection,
  `test_between_item_poll_is_in_the_dequeue_loop`) and they pass. The plan's suite bar is unverified by me
  and the flake I warn about is inherited from the sibling review's measurement, not re-measured here.
- MY `register_signal_report` DEFECT ANALYSIS IS STATIC. I established that oc calls it at five sites and
  agy at three, that both agy omissions follow a `state = load_state(...)` rebind, and that oc's comments
  state the refresh invariant. I did NOT drive a real agy run to an integration deferral and send it a
  SIGINT, so the operator-visible symptom is inferred from the mechanism rather than observed. E-03's
  required test is written to be that proof.
- I DID NOT ENUMERATE EVERY CONSUMER of the 27 closure names. I classified them by definition site and
  import form; a consumer reaching one dynamically (a `getattr`, a string dispatch) would not appear, and
  a monkeypatching test could depend on a name resolving in a particular module.
- I DID NOT DECIDE THE ROUTE (D-3), and my recommendation of route B is a recommendation. I also did not
  evaluate whether the `rununify` Set's remaining ambition for the five large functions is still worth its
  cost given that two of six children reviewed have now had their central premise inverted; that is a
  broader question than this plan.

## Round 2

DISCHARGE ONLY. NO NEW REVIEW WAS PERFORMED. This round records that round 1's gating findings were
resolved by the maintainer's own directive, given on 2026-09-16 in an interactive session. Nothing in the
plan was re-reviewed here and no new finding was sought; appending a round is the mechanism
`plan-review.md` prescribes for this, since the gate reads only the current round. Round 1 is left exactly
as written, and its measurements remain the specification the execution must reproduce at execution HEAD.

THE DIRECTIVE, quoted: "at the end of the SET, there should be one code base shared by the two runners
that contains 100% of the otherwise redundant code that currently is duplicated between the two runners."

TWO SUPPORTING RULINGS the maintainer gave in the same session, because round 1's findings rested on
premises both of them contradict. FIRST, TESTS ARE NOT IMMOVABLE: asked directly whether the
source-reading guards prevent this work, the answer was no, and the maintainer pointed at this
repository's own precedent where such a guard was already re-based for shared code
(`tests/test_nested_tty_noninteractive.py:190-203`, whose docstring records the reasoning; all 41 tests in
that file and `tests/test_lane_tool_identity.py` pass at this HEAD, verified 2026-09-16). SECOND,
COORDINATED DE-DUPLICATION IS PERMITTED: many functions may be de-duplicated together before testing, so
a dependency that is still double-defined because a sibling has not landed is an ordering matter, not a
blocker. What remains forbidden is weakening a guard silently.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | round 1 finding, discharged by directive | this plan's resolved `OQ-03`; the maintainer's 2026-09-16 directive | Body difference was measured but liftability was not: the function closes over names that are still defined twice, so a shared core would need many injected parameters. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The maintainer ruled 2026-09-16 that the objective is 100% de-duplication and that the injected-parameter form IS the sanctioned mechanism, not a violation of it: the 2026-09-03 `818uru` OQ-02 ruling established "shared file owns the real function taking explicit parameters, each runner keeps a one-line wrapper at the original name and signature", and what it rejected was threading a parameter through ~86 CALL SITES, which the wrapper form avoids. The maintainer also confirmed many functions may be de-duplicated together before testing, so a still-double-defined dependency is handled by working in dependency order, not by refusing. See the resolved OQ-03. |
| PR-002 | BLOCKER | IN-SCOPE | round 1 finding, discharged by directive | this plan's resolved `OQ-03`; the maintainer's 2026-09-16 directive | Tests read this function's source text or patch names it resolves, and a thin caller satisfies none of them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The maintainer ruled 2026-09-16 that these pins are work, not vetoes, citing the existing precedent where such a guard was already re-based onto shared code successfully (`tests/test_nested_tty_noninteractive.py:190-203`, all 41 related tests passing at this HEAD). A pin is to be re-based on the new location with its property preserved and its injected-regression proof kept; silently weakening one (lowering a threshold, deleting an assertion) remains forbidden. Where a behavioral assertion can replace a source-text one without losing coverage, prefer it and say so. See the resolved OQ-03. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does the maintainer's directive discharge round 1's gating findings, or do they need a fresh review pass? | It discharges them; record the discharge and leave round 1 untouched. | A further full review round on this plan, rejected on cost and on relevance: round 1 already measured the mechanics correctly and its findings were escalations of a SCOPE decision, which is the maintainer's to make and which they have now made. | The findings' own recorded remedy was a maintainer decision, and that decision is now recorded in this plan's resolved OQ-03 with its reasoning and its two supporting rulings. | yes |

HONEST LIMIT, stated because it bounds what this round proves: the discharge rests on the maintainer's
directive, NOT on an independent reviewer's re-examination of the plan's content. Round 1 is where that
assurance lives. Specifically NOT re-verified here: the closure and pin measurements round 1 recorded
(each plan's E-01 re-measures them at execution HEAD and is required to refuse on a stale list), and
whether the re-based guards preserve their properties (each plan's V-items require that evidence). This
round changes the DECISION column and nothing else.
