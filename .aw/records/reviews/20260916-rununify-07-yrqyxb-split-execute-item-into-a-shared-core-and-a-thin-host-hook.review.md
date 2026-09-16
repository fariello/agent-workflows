# Review findings: plan yrqyxb

- Subject-Id: yrqyxb
- Subject-Type: ipd
- Reviewed-At: 2026-09-16
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `96db8545`. Structural preflight `aw ipd lint --phase author` CONFORMED (exit 0) before
revision. No pre-review snapshot needed: the plan was committed and unmodified. This is the seventh
`rununify` child reviewed and the THIRD IN A ROW whose central premise inverted under the same test.

EVERY MEASUREMENT REPRODUCED, and the plan deserves that said first. Verified independently: 1212 oc lines
and 1074 agy; 893 and 870 CODE lines; 101 differing lines under AST normalization with docstrings stripped;
SequenceMatcher similarity 0.851. One number is off by one in the plan's own favor: the host-token count is
SEVEN, not eight (three `run_opencode`/`run_agy_turn` call pairs plus one `aw agy run` message string).
F-1's characterization of the function is exact, and F-2's hazard is not merely real but UNDERSTATED: I
counted SIXTEEN distinct safety gates called inside `execute_item`, present identically on both hosts
(`evaluate_clean_base_for_launch`, `clean_base_launch_decision`, `assert_child_tool_identity`,
`driver_begin`, `allocate_isolation_worktree`, `collect_lane_submissions`, `validate_defect_report`,
`run_suite_check`, `integration_is_earned`, `build_lane_outcome`, `integrate_lane_branch`,
`record_integration_refusal`, `reconcile_disposition`, `sync_receipt_into_worktree`, `driver_finalize`,
`process_backlog_close`).

THE BLOCKING DEFECT IS THE FAMILY ERROR: body difference was measured, liftability inferred. `execute_item`
closes over 57 module-level names. 20 resolve in `runner_shared`; 2 are equal constants; 11 are already ONE
object (agy imports them from oc, or both import a third module); 1 is the genuinely host-specific spawn
that F-3 correctly identifies; 2 are FALSE POSITIVES of a naive scan; and EIGHTEEN ARE STILL DEFINED TWICE,
reached by 24 call sites in oc and 23 in agy. The promised "relocation with a parameter" is a relocation
with eighteen parameters that de-duplicates none of them.

AND THIS PLAN IS WORSE OFF THAN ITS TWO SIBLINGS ON TWO INDEPENDENT COUNTS.

FIRST, THE PREREQUISITES DO NOT CLEAR THE PATH, which distinguishes a plan that is merely EARLY from one
whose premise may be unreachable. `Item-Dependencies: executed:ct4w0a` gains exactly ONE of the eighteen
(`driver_begin`). Sibling `i3d6ml` NAMES sixteen of them, but it was re-scoped at its own review from 48
symbols to 9, and only SIX of the eighteen fall in its surviving groups. So after every sibling executes as
re-scoped, at least ELEVEN of the eighteen remain double-defined. The Set's plan for this symbol does not
converge by sequencing alone.

SECOND, FOURTEEN PINS READ THIS FUNCTION'S BODY, and SIX assert the ORDERING of exactly the gates F-2 calls
load-bearing. Twelve use `inspect.getsource`, two do an AST lookup by function name, two use
`source.split("def execute_item")`, across ten files. The six ordering pins are the ones no characterization
suite can rescue, because they assert on SOURCE TEXT: `tests/test_lane_clean_base.py:172` and
`tests/test_dirty_base_gate.py:781` both require `evaluate_clean_base_for_launch` to appear BEFORE the spawn
and BEFORE `allocate_isolation_worktree`; `tests/test_lane_tool_identity.py:695` requires
`assert_child_tool_identity` before `driver_begin(`; `tests/test_lane_submission_collection.py:240` requires
submission collection before the disposition assignment; `tests/test_lane_session_isolation.py:125` requires
the `set_sessions` promotion under a `work_dir` guard; `tests/test_defect_report.py:809` requires the
defect-report block to contain no `raise`/status write/`driver_finalize`/`return`. I ran all ten files:
305 tests pass today. A thin caller contains none of those strings.

ONE HAZARD I CHECKED AND CLEARED, recorded so a later reader does not re-raise it. `execute_item` contains
NO `subprocess` call site on either host, so the nested-`aw` stdin guard
(`tests/test_nested_tty_noninteractive.py:172`, `:218`) that BLOCKS sibling `ct4w0a` does not apply here.
The agent spawn is inside `run_opencode` (`oc_runipd.py:6219`) and `run_agy_turn` (`agy_runipd.py:3144`),
both of which stay put. I verified the three nested-`aw` sites per driver resolve to `driver_begin`,
`driver_finalize` and the spawn function, none of them in `execute_item`.

A SMALLER TRAP WORTH NAMING, because a mechanical executor would fall in it. Two of the 37 unresolved names
are not module-level at all: `extract_log_metrics` is a FUNCTION-LOCAL import from `run_viewer`, kept local
deliberately per `run_analytics_sources.py:646` to preserve import order, and `reask_prompt_path` is a
LAMBDA PARAMETER. Injecting either would add a parameter that must not exist and move a deliberately-local
import to module scope.

WHAT I FIXED AND WHAT I LEFT. I added the six-class closure table to the Goal; added E-01 as a gating
measurement that excludes the two false positives BY NAME; rewrote E-02 to pin all sixteen gates as
BEHAVIOR rather than source text; added E-03 as a pin inventory that must produce a behavioral equivalent
for each of the six ordering pins and must NOT edit a test; converted the split into E-04, a written
analysis gated on OQ-03 that must answer whether the residual injection count is acceptable; rewrote E-05
to assert only what changed plus the inverse eighteen-still-double-defined assertion; made non-vacuity
bidirectional; fenced all ten pin files; recorded the `save_state` census (15 of 38 oc and 15 of 36 agy
sites live here); noted the spec consequence of converting an ordering pin; and cleared the subprocess
hazard on the record. I did NOT decide the route, because this is the largest symbol in the repository and
each route restructures a Set with nine pending children.

THE PLAN'S DIAGNOSIS IS EXCELLENT AND ITS REMEDY IS UNREACHABLE FROM HERE. F-1 through F-5 are the best
Findings table of the three split children I have reviewed; what fails is the inference that a small body
difference implies a cheap relocation, in the one function where that inference is most expensive.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | BLOCKER | IN-SCOPE | C. architecture (closure); G. executability | closure measurement at HEAD `96db8545` | **BODY DIFFERENCE MEASURED, LIFTABILITY INFERRED,** the third `rununify` child to make this error. `execute_item` closes over 57 module-level names: 20 resolve in `runner_shared`, and EIGHTEEN are still DEFINED TWICE, reached by 24 call sites in oc and 23 in agy. The promised relocation-with-a-parameter is a relocation with eighteen that de-duplicates none. Compounded by PR-003: at least ELEVEN survive the whole Set. | C:High; U:Low; S:Low; F:High; Overall:High | OPEN | Closure table added to the Goal; gating E-01 added; the split converted to E-04, an analysis deliverable. Route escalated as blocking OQ-03 with four options and a recommendation (shrink-first). NOT fixed by a plan edit because every route restructures the Set. |
| PR-002 | BLOCKER | UNDER-SCOPE | D. anti-regression; E. testing; B. security-adjacent safety | ten test files; six ordering pins enumerated in F-8; `305 passed` measured | **FOURTEEN PINS READ `execute_item`'s BODY AND SIX ASSERT THE ORDERING OF F-2's SAFETY GATES.** 12 `inspect.getsource`, 2 AST-by-name, 2 `source.split`. The six ordering pins require the clean-base guard before the spawn AND before lane allocation, the identity check before `driver_begin`, submission collection before disposition, the `set_sessions` promotion under a `work_dir` guard, and the defect-report block to raise nothing. A thin caller satisfies none, and characterization coverage cannot substitute, because these assert on SOURCE TEXT. None of the ten files was fenced. | C:Medium; U:Low; S:Medium; F:High; Overall:High | OPEN | All ten files fenced; F-8 enumerates all fourteen with `path:line`; E-03 must produce a per-pin verdict plus a behavioral equivalent for each ordering pin, and must NOT edit a test; V-03 requires the green baseline. Authority to REWRITE a pin an executed plan installed is explicitly part of OQ-03. |
| PR-003 | HIGH | IN-SCOPE | G. dependencies and sequencing | `i3d6ml`'s re-scoped groups A/B; `ct4w0a`'s scope; the 18 measured | **THE DECLARED PREREQUISITE CHAIN DOES NOT CLEAR THE PATH.** `executed:ct4w0a` gains ONE of the eighteen (`driver_begin`). `i3d6ml` names sixteen but its review re-scoped it from 48 symbols to 9, and only six of the eighteen fall in its surviving groups. So at least ELEVEN remain double-defined after the whole Set executes. This converts the question from "is this plan too early" into "is the Set's plan for this symbol achievable", which no sibling review has yet asked. | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | FIXED | Added as F-7 with the per-symbol accounting; E-04(b) must ANSWER whether the residual count is acceptable; folded into OQ-03 as the reason route (C) alone is insufficient. |
| PR-004 | HIGH | UNDER-SCOPE | A. correctness (a mechanical trap) | `oc_runipd.py:7144`, `:7363`; `agy_runipd.py:3913`, `:4098`; `run_analytics_sources.py:646` | **A NAIVE CLOSURE SCAN INVENTS TWO DEPENDENCIES AND INJECTING EITHER IS WRONG.** `extract_log_metrics` is a FUNCTION-LOCAL import from `run_viewer`, deliberately local to preserve module import order per a comment in `run_analytics_sources.py`; `reask_prompt_path` is a LAMBDA PARAMETER. An executor injecting every unresolved name would add two parameters that must not exist and hoist a deliberately-local import. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-9 with all four `path:line` citations; E-01 must exclude both BY NAME; V-01 requires the exclusions with their reason; E-05 asserts neither is module-level. |
| PR-005 | HIGH | UNDER-SCOPE | D. anti-regression; E. testing | 16 gates measured on both hosts | **F-2 NAMES THE HAZARD AND THE PLAN NEVER ENUMERATES IT,** so "every gate must be proven still fail-closed" had no list to check against and E-01 could have produced a suite covering three gates and claimed compliance. Measured: sixteen distinct gates per host. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | All sixteen enumerated in F-2 and in E-02, which now requires each pinned as BEHAVIOR on BOTH hosts; V-02 requires each named in the output and a sabotage that names the gate it broke. |
| PR-006 | MEDIUM | IN-SCOPE | C. architecture (a guard cited as evidence it is not) | `tests/test_review_findings_cascade.py:308-313`; 10 matches in agy | **THE PLAN CITES A GUARD THAT DOES NOT HOLD.** Project conventions claims `test_no_runner_to_runner_import` forbids a runner-to-runner import; it is a SUBSTRING check for `"import oc_runipd"` which agy's `from agent_workflows.oc_runipd import (...)` form evades ten times. ELEVEN of this function's closure names are single objects precisely BECAUSE agy imports them from oc, so the claim is not merely imprecise, it inverts why part of the closure already resolves. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected in Project conventions with the count and the reason, redirected to the AST-based `tests/test_runner_shared.py:955`. |
| PR-007 | MEDIUM | UNDER-SCOPE | E. testing (a pinned census) | `tests/test_runner_shared.py:1148`; ran it, passes at 38/36 | **THE SPLIT MOVES 39 PERCENT OF A PINNED CALL-SITE CENSUS.** Fifteen of oc's 38 and fifteen of agy's 36 `save_state` sites are inside `execute_item`. The test's own rule forbids repairing a moved count by editing the literal; the correct treatment is a documented RELOCATION subtraction, as `RELOCATED_RUN_CHECKED_CALLERS` does. Unmentioned. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-10 and to Project conventions with the measured counts; Required tests item 6 and V-05(c) require the test green at 38/36, which holds because the re-scoped plan adds no call site. |
| PR-008 | MEDIUM | UNDER-SCOPE | G. right-sizing and conceptual density | E-02 as authored; 11 `try` blocks, 4 `return`s per host | **ONE E-ITEM BUNDLED THE LARGEST RELOCATION IN THE REPOSITORY:** a 1212-line function's core, eighteen dependency decisions, import rewiring in files of 9,375 and 5,727 lines, and fourteen pin repairs across ten files, in one pass. The function also carries eleven `try` blocks and four `return`s per host, so its control flow does not decompose into a call with a parameter. A failure midway leaves the package unimportable. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as F-12; restructured into five items (measurement, gate pinning, pin inventory, analysis, guard suite), each test-only and one focused pass; `Highest E allocated` raised to 05. |
| PR-009 | MEDIUM | UNDER-SCOPE | E. non-vacuity | Required tests item 3 as authored | **NON-VACUITY WAS ONE-DIRECTIONAL.** "Sabotage the shared core and show the suites fail" cannot detect the opposite regression, a later agent collapsing one of the eighteen double definitions unilaterally, which is the most likely way this plan gets "finished" without the OQ-03 decision. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests item 5 now demands both controls: mis-classify a closure entry, and move one double-defined symbol into `runner_shared`; V-05(b) requires both pasted. |
| PR-010 | LOW | IN-SCOPE | A. correctness (a count in the plan's favor) | host-token measurement at HEAD | The Concern claims EIGHT host-token lines; the measured count is SEVEN. Small, and it errs in the direction that makes the split look cheaper, which is the same direction as PR-001, so it is worth correcting rather than absorbing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected in F-1 with the breakdown (three call pairs plus one message string) and the note that the conclusion survives but the inference does not. |
| PR-011 | LOW | UNDER-SCOPE | F. honest documentation; G. spec effects | `tests/test_lane_clean_base.py` R5.4/R6.1 citations; spec `c4gd2h` | **THE SPEC SECTION MISSES A CONSEQUENCE OF ITS OWN PIN PROBLEM.** Converting an ordering pin to a behavioral assertion changes a guarantee spec `c4gd2h` states in prose (the pins cite R5.4 and R6.1 by name), so it is a spec-governed change, not test churn. The original section's "no spec change expected" is true only because the re-scoped plan touches no product code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec section now states that a pin conversion carries a spec amendment in the same change with the path declared, and E-04 must surface the spec consequence before a route is chosen. |
| PR-012 | LOW | IN-SCOPE | E. achievable bar | sibling `i3d6ml`'s measured flake; item 5 as authored | The suite bar gave no baseline for a known load-dependent flake, and the gate's reviewer-targets paragraph pointed at an E-item that no longer performs the split. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Item 8 requires an own-HEAD baseline and reproduction before attribution; targets rewritten to F-6, F-7 and F-8; bare-run flags named in the contract; the ten-file ack expectation stated. |
| PR-013 | LOW | IN-SCOPE | D. anti-regression (a hazard correctly absent) | `execute_item` AST scan; `tests/test_nested_tty_noninteractive.py:172`, `:218` | NOT A DEFECT, recorded so it is not re-raised: `execute_item` contains NO `subprocess` site, so the nested-`aw` stdin guard that BLOCKS sibling `ct4w0a` does not apply here. Verified the three nested-`aw` sites per driver are `driver_begin`, `driver_finalize` and the spawn function. Without this note the next reviewer would spend the measurement again. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded in Project conventions as CLEARED, with the line citations for the spawn sites. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | The plan reports 101 differing lines and 8 host tokens. Accept, or re-measure? | RE-MEASURE. 101 reproduces exactly under AST normalization; the host-token count is 7, not 8. | (a) Accept both numbers, rejected because the same inference (small diff implies cheap move) was the BLOCKER in two sibling reviews this week, so the numbers had to be re-derived before anything was built on them. (b) Re-measure only the headline, rejected: the host-token count is what the plan uses to argue the divergence is drift rather than specificity, so it is load-bearing too. | AST-normalized diff with docstrings stripped at HEAD `96db8545`; SequenceMatcher similarity 0.851; the seven host-token lines enumerated | yes |
| D-2 | Does the closure test change the verdict here as it did for `i3d6ml` and `ty3cj6`? | YES, and more severely: 18 still-double-defined against `ty3cj6`'s 11, and at least 11 surviving the whole Set. | (a) Assume the two prior inversions made this one predictable and skip the measurement, rejected: a prediction is not a measurement, and the specific number (18, and 11 residual) is what makes route (C) insufficient. (b) Measure only the count, not what each sibling actually lifts, rejected: without the per-symbol accounting the residual-after-Set figure cannot be computed, and that figure is the whole reason this is a design question. | closure measurement at HEAD; `i3d6ml`'s re-scoped groups A/B membership; `ct4w0a`'s scope | yes |
| D-3 | Eighteen injections and fourteen broken pins. Choose a route myself, or ask? | ASK. Raised as OQ-03, `Blocking: yes`, four routes with costs and a recommendation (shrink-first, then split). | (a) Inject all eighteen myself, rejected: it contradicts the maintainer's `818uru` OQ-02 ruling at three times the scale that ruling addressed, and would break six safety-ordering guards at once. (b) Adopt shrink-first myself, rejected: it re-plans the Set's approach to its largest symbol and would need new child plans, which is the maintainer's scope call. (c) Re-order this plan last myself, rejected: F-7 shows it still leaves eleven injections, so it would look like a fix while solving little. (d) Declare `execute_item` unsplittable myself, rejected for the same authority reason, though it is a defensible outcome. | the `818uru` OQ-02 wrapper ruling quoted at `tests/test_runner_shared.py:64-70`; the 18/11 measurement; the six ordering pins | yes |
| D-4 | Six pins assert gate ORDERING. Should the plan be told to rewrite them into behavioral assertions? | NO. E-03 must produce the verdict AND the behavioral equivalent; the authority to change them is OQ-03's. | (a) Instruct the rewrite, rejected: these guards were installed by executed plans against incidents this repository actually paid for (a clean-base violation and a finalize wedged 1h49m are cited in the surrounding tests), and rewriting a guard to accommodate a refactor is how a guarantee quietly weakens. (b) Treat them as a permanent veto on splitting, rejected as overreaching: a maintainer may legitimately decide an ordering pin should become behavioral, and E-03's job is to make that decision cheap by pre-writing the equivalent. | `tests/test_lane_clean_base.py:158-190` docstring stating why ordering is asserted structurally; `tests/test_dirty_base_gate.py:770-790`; spec `c4gd2h` R5.4 | no |
| D-5 | Two unresolved names are not module-level. Silently drop them, or name them? | NAME THEM as explicit exclusions with `path:line` and the reason each is not a dependency. | (a) Drop them from the count silently, rejected: the next agent re-running the closure scan gets 37 again and has no way to know two were adjudicated, so it would re-inject them. (b) Leave them in the injection list as harmless, rejected outright: injecting `extract_log_metrics` would hoist an import kept local deliberately to preserve module import order, and `reask_prompt_path` is a lambda parameter, so both would be real defects. | `oc_runipd.py:7144`, `:7363`; `agy_runipd.py:3913`, `:4098`; `run_analytics_sources.py:646` on why the import stays local | yes |

### Deferred and open

- `PR-001` - `OPEN`:
  - Reason: The split needs eighteen injected dependencies, and at least eleven of them survive the entire Set (PR-003), so no sequencing fix resolves it. Every available route either contradicts the maintainer's standing `818uru` wrapper ruling, re-plans the Set's approach to its largest symbol, or abandons the split.
  - Remediation Risk: High
  - Axis: complexity, functionality
  - Required decision or evidence: the maintainer's answer to OQ-03, choosing among routes A through D.
  - Consequence if unresolved: `execute_item` stays duplicated, which is the WORST such outcome in the Set because it is the largest symbol and the one carrying all sixteen safety gates, so drift here is the most expensive drift available. The more dangerous outcome, however, is an executor following the plan as originally written: an eighteen-parameter shared core landing alongside fourteen broken pins, six of them the ordering guards that keep a lane from being created over a dirty base.
- `PR-002` - `OPEN`:
  - Reason: Six of the fourteen pins assert the ORDERING of safety gates by reading source text, and they were installed by executed plans against incidents that actually occurred. Repairing them is not mechanical: it decides whether a structural guarantee becomes a behavioral assertion or is retired, and the surrounding tests cite spec `c4gd2h` R5.4/R6.1 by name.
  - Remediation Risk: High
  - Axis: security, functionality
  - Required decision or evidence: OQ-03's answer, plus an explicit decision on whether the six ordering pins may be converted and to what, with the spec amendment that conversion implies.
  - Consequence if unresolved: no immediate harm, since all ten files are now fenced and E-03 must pre-write the behavioral equivalents without editing anything. The risk being held open is a future executor reading fourteen red tests as noise from its own refactor and rewriting them to pass, which would silently retire the guarantee that no worker process is spawned and no lane allocated before the clean-base guard runs.

### Escalation of the irreversible decision

D-4 is judged `Reversible: no`: it declines to authorize converting six source-text ordering pins into
behavioral assertions, and the OPPOSITE choice is what cannot be cleanly undone. A structural pin asserting
`guard_at < spawn_at` proves that NO code path, including one no test drives, can spawn before the guard;
its own docstring says exactly that (`tests/test_lane_clean_base.py:158-190`). A behavioral replacement
proves it only for the paths the test drives, and nothing in the resulting test records that a weaker
guarantee was accepted, so the next agent finds green tests and no trace of the trade. Escalated per the
workflow rather than merely recorded: it is raised in the plan as F-8 with all fourteen `path:line`
citations and the six ordering pins called out separately, E-03 carries the obligation to state a per-pin
verdict and a behavioral equivalent WITHOUT editing a test, V-03 requires the green baseline, the spec-sync
section now names the amendment a conversion would force, and the `Blocking: yes` OQ-03 puts the route
decision in front of the maintainer before any split executes. D-1, D-2, D-3 and D-5 are reversible (a plan
edit undoes each) and are recorded only.

### Honest limits of this review

- I DID NOT ATTEMPT THE SPLIT. The eighteen-injection figure is from static closure analysis plus live `is`
  comparisons, not from having built a shared core and imported it. E-01 re-derives it at execution HEAD,
  which is where the number becomes authoritative.
- I DID NOT RUN THE FULL SUITE. I ran the ten pin files (`305 passed`),
  `test_no_call_site_was_rewritten` (passes at 38/36) and `tests/test_wtiso_characterization.py` (3 passed).
  The plan's overall suite bar is unverified by me, and the flake I warn about is inherited from the sibling
  review's measurement rather than re-measured here.
- MY SIXTEEN-GATE COUNT IS A CALL-SITE SCAN, not a semantic audit. I confirmed each of the sixteen names is
  CALLED inside `execute_item` on both hosts; I did not verify that each still fails closed today, which is
  precisely what E-02 is written to establish.
- I DID NOT ENUMERATE EVERY CONSUMER of the eighteen double-defined symbols, only their call sites within
  `execute_item` and the sibling plans that name them. A consumer reaching one dynamically (a `getattr`, a
  monkeypatch in a test) would not appear in my scan.
- MY RESIDUAL-AFTER-SET FIGURE (eleven) ASSUMES the sibling children execute exactly as re-scoped at their
  own reviews. Two of those siblings are themselves `no-go` with open blocking questions, so their final
  scopes may differ and the figure could move in either direction. E-04(b) must recompute it rather than
  quote mine.
- I DID NOT DECIDE THE ROUTE (D-3), and my recommendation of shrink-first is a recommendation. I also did
  not evaluate whether the `rununify` Set's ambition for the five large functions remains worth its cost
  now that three of seven children reviewed have had their central premise inverted; that is a question
  about the Set, and it belongs to the orchestrator or the maintainer, not to this child.
