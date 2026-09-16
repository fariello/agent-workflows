# Review findings: plan i3d6ml

- Subject-Id: i3d6ml
- Subject-Type: ipd
- Reviewed-At: 2026-09-16
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `476354fc`. Structural preflight `aw ipd lint --phase author` CONFORMED (exit 0)
before revision, and that is the first thing worth saying about this plan: it was structurally
immaculate and substantively unexecutable. Every E/V pair was present and bijective, every open
question was dispositioned, the scope fence and execution contract were correct, and the prose was
unusually careful. None of that could see the defect, because the defect is in the MEASUREMENT the
plan is built on. No pre-review snapshot was needed: the plan was committed and unmodified.

THE PLAN MEASURED THE WRONG PROPERTY, AND EVERYTHING ELSE FOLLOWS FROM THAT. It partitioned the 66
shared runner symbols by BODY EQUALITY (AST compare, docstrings stripped) and treated the 48 that
agree as liftable. Body equality says the two hosts do not DISAGREE. It says nothing about whether a
definition can MOVE, which requires that every module-level name the body closes over be resolvable in
`runner_shared`. I re-measured all 48 with that closure test. Five are liftable. Four more are liftable
but change observable output. Eleven must never be lifted. Twenty-eight close over at least one name
that is neither in `runner_shared` nor in the 48. Executed as written, each of E-02, E-03 and E-04
would fail partway through on a `NameError` at import time, having already relocated part of a
9,375-line and a 5,727-line module.

TWO OF THE THREE MOVE ITEMS INSTRUCT THE EXECUTOR TO REVERSE A MAINTAINER DECISION. This is the
finding I would most want a human to see. E-02 calls ten symbols "already thin delegations" and directs
that the delegating stub be DELETED. Those ten are the `INJECTED` set: their implementation is ALREADY
single and shared in `runner_shared`, and the surviving one-line host wrapper is the deliberate
mechanism that binds a host-specific dependency. The ruling is `818uru` OQ-02, quoted verbatim in
`oc_runipd.run_checked`'s own docstring along with the two alternatives that were rejected (threading
the parameter through ~86 call sites; a registration seam, declined because process-global state makes
behavior depend on import order). `SingleDefinitionTests` exists to assert those wrappers persist. So
E-02's instruction would delete precisely what the ruling installed, for zero de-duplication gain,
because there is nothing left to de-duplicate. E-03 separately includes `disable_lane_prompt`, which
three places in the tree declare unmovable: it writes `_LANE_PROMPT_DISABLED` through `global`, so
lifting it makes it write the SHARED flag while each host's still-diverged `_lane_reclaim_prompt` reads
its own. That failure is silent. No exception, no test naming the cause, just an unattended overnight
run pausing to ask a question nobody is there to answer.

THE SET CONTAINS A CYCLE THAT THE DEPENDENCY CHECKER STRUCTURALLY CANNOT SEE. This plan declares
`Item-Dependencies: none`. Six of its symbols need a symbol that children 04, 05 and 06 own
(`write_report`, `_detect_driver_command`, `_compute_scope_reconciliation`, `extract_session_id`,
`parse_plan_file`), and all three of those children declare `Item-Dependencies: executed:i3d6ml`. The
coupling is by SYMBOL and the declaration is by PLAN, so nothing in the toolchain reports it. An agent
executing the Set in order would hit it as a runtime failure in the first child.

I CORRECTED TWO PLACES WHERE THE PLAN REACHED A RIGHT ANSWER FROM A FALSE PREMISE, because a right
answer resting on a false premise is the kind a later agent "simplifies" away. OQ-02 chose oc's
filename form on the stated ground that "nothing parses them by position (they are globbed by `id6`)".
That is false. `run_analytics_statistics._VERIFY_LOG_RE` is anchored on `-attempt-<n>-verify.jsonl`,
which only oc produces, so every agy verifier session log is TODAY misclassified as an execute log by
the verifier-phase analytics. The answer stays oc's form, but because adopting it REPAIRS a live defect
on the agy side, which makes it a disclosed improvement rather than an accepted cosmetic risk. I also
found the plan understated its own `write_prompt` finding: the difference is not tag ORDER but
SEMANTICS (oc's `suffix` replaces the `exec`/`review` prefix, agy's appends to it), so the same call
yields `03-abc123-verify-attempt-1.md` on one host and `03-abc123-exec-verify-attempt-1.md` on the
other. Separately, OQ-01's defensive-form argument was correct but speculative ("a missing key raises
on a recovery path"); the real exposure is narrow and nameable, a queue frozen by an older driver build
and resumed by this one, and oc itself already hedges 9 of its own 13 call sites with `.get`.

RIGHT-SIZING FAILED AND THE COUNT-BASED LINT COULD NOT SEE IT. E-02, E-03 and E-04 relocated 14, 21
and 13 symbols across 400, 664 and 783 lines respectively: roughly 1,850 lines moved between the two
files the parent plan itself calls the highest-contention files in the repo, in three checklist items,
each symbol needing its own dependency analysis, docstring-merge decision and import rewiring. `aw ipd
lint` passed it as `standard` because it counts E-leaves and groups, not concepts. The revised items
are 5 symbols, 4 symbols and a disclosure.

WHAT I FIXED AND WHAT I DELIBERATELY DID NOT. I rewrote the checklist to the 9 symbols that are sound
today, converted the 11 exclusions into an explicit DELIVERABLE (E-04) with proof-of-absence evidence
(V-04) so a later agent cannot mistake the omission for unfinished work, made the non-vacuity control
BIDIRECTIONAL so the suite catches over-lifting as well as under-lifting, named every blocked symbol
with its specific blocker, added the five test files the change must edit to the scope fence, and
corrected the suite baseline against a pre-existing flake I measured. What I did NOT do is choose the
re-scope. Four defensible options exist and each restructures a Set with nine pending children and an
approved orchestrator whose retirement gate reads the child table. That is a scope and priority
decision, so it is OQ-03, `Blocking: yes`, with my recommendation stated and the reasoning for each
option's cost recorded.

THE PLAN IS NOW EXECUTABLE AS REVISED and delivers a real, if small, slice: 9 symbols unified, one
live analytics defect repaired, and 11 permanent exclusions documented against a future mistake. The
gap between that and the 48 it promised is what the maintainer needs to rule on.

VERIFIED RATHER THAN TRUSTED, every measured claim in the plan. The 66-symbol total and the seven-way
partition in F-2 both reproduce exactly. The 6231-line `runner_shared` figure is exact. The 57
oc-to-agy import count is exact. `DriverError` is genuinely one shared class now. What did NOT
reproduce is the inference layered on top: of those 57 imports only 5 are among the 48 and 4 of the 5
are blocked, so the plan's claim that E-02 "makes the guard meaningful again" is false and the
realistic import-count decrease is one, not fourteen.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | BLOCKER | IN-SCOPE | A. correctness; G. plan executability | the plan's own partition method (body equality) versus the closure test; measured at HEAD `476354fc` | **THE PARTITION MEASURES THE WRONG PROPERTY, so the 48-symbol scope is not achievable.** Body equality proves the hosts AGREE; liftability requires that every module-level free name a body closes over be resolvable in `runner_shared`. Re-measured with the closure test: 5 of 48 are closure-clean, 4 more are closure-clean but change observable output, and 28 close over a name that is neither in `runner_shared` nor in the 48. Each of E-02/E-03/E-04 would fail partway through on an import-time `NameError`, after partially relocating two of the largest modules in the package. | C:Medium-High; U:Low; S:Low; F:High; Overall:High | OPEN | The measurement is settled and recorded (F-7 plus the eight-group table in Goal). The RE-SCOPE is not mine to choose: escalated as OQ-03 (`Blocking: yes`) with four options, costs, and a recommendation. Checklist rewritten meanwhile to the 9 symbols that are sound, so the plan is executable as revised. |
| PR-002 | BLOCKER | IN-SCOPE | D. anti-regression; C. architecture (canonical mechanisms) | `tests/test_runner_shared.py:76` (`INJECTED`), `:541`, `:573`; `agent_workflows/oc_runipd.py:557` docstring quoting `818uru` OQ-02 | **E-02 INSTRUCTS THE EXECUTOR TO DELETE A MECHANISM THE MAINTAINER RULED ON.** Ten of its fourteen "already thin delegations" are the `INJECTED` set: implementation ALREADY single and shared, with a deliberate one-line host wrapper binding a host-specific dependency (`pinned_child_env`, `write_report`, `parse_plan_file`, `parse_dependency_token`, `driver_label`, `run_checked`, `host_label`). The ruling records two rejected alternatives. "Deletes the delegating stub" would undo it for zero gain, since there is no second implementation to remove. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | The 10 are removed from the lift scope permanently (not deferred) and become E-04, whose deliverable is the DISCLOSURE. V-04 requires proof the wrappers still exist and `SingleDefinitionTests` is green. E-05's table now asserts their presence, so the suite fails if a later agent lifts them. |
| PR-003 | BLOCKER | IN-SCOPE | D. anti-regression; F. prevent silent failure | `tests/test_runner_shared.py:1238` (`UnmovableSymbolTests`); `agent_workflows/runner_shared.py:95`, `:620`; `tests/test_lane_allocation_idempotent.py:816` | **E-03 INCLUDES A SYMBOL THREE PLACES DECLARE UNMOVABLE.** `disable_lane_prompt` writes `_LANE_PROMPT_DISABLED` through `global`; lifting it writes the SHARED flag while each host's diverged `_lane_reclaim_prompt` reads its own. Prompt suppression on a repeated interrupt silently stops working. There is no exception and no test that names the cause: the symptom is an unattended run pausing for a question nobody will answer. | C:Low; U:Medium; S:Low; F:High; Overall:Medium | FIXED | Removed from scope permanently; folded into E-04's disclosure with its pinned reason and the citations. V-04 requires proof it is still defined in BOTH runners and absent from `runner_shared`, with `UnmovableSymbolTests` green. |
| PR-004 | HIGH | IN-SCOPE | C. architecture (sequencing); G. dependencies and sequencing | `- Item-Dependencies: none` versus `executed:i3d6ml` in children `tx6q0h`, `ct4w0a`, `sy7uwh` | **THE SET CONTAINS A CYCLE THE DEPENDENCY CHECKER CANNOT SEE.** Six symbols here need `write_report`, `_detect_driver_command`, `_compute_scope_reconciliation` (child 04), `extract_session_id` (child 05) or `parse_plan_file` (child 06); all three children declare they run AFTER this plan. The coupling is by SYMBOL, the declaration by PLAN, so nothing reports it and an agent executing the Set in order meets it as a runtime failure. | C:Medium; U:Low; S:Low; F:Medium-High; Overall:Medium-High | OPEN | Cannot be fixed inside this plan: resolving it means either moving 6 symbols out (changing this plan's scope) or re-pointing three children's dependencies (changing the Set's shape). Both are the maintainer's call and are options under OQ-03. Documented as group G with each symbol's owning child named, so the executor cannot walk into it. |
| PR-005 | HIGH | IN-SCOPE | A. correctness; E. testing (observable behavior) | `agent_workflows/oc_runipd.py:5511`/`:5524` versus `agy_runipd.py:2809`/`:2823`; `agent_workflows/run_analytics_statistics.py:1248` | **F-4 UNDERSTATES ITS OWN FINDING TWICE.** (1) `write_prompt` differs SEMANTICALLY, not by tag order: oc's `suffix` REPLACES the `exec`/`review` prefix, agy's ADDS to it, so a verifier prompt is `03-abc123-verify-attempt-1.md` on oc and `03-abc123-exec-verify-attempt-1.md` on agy. (2) `attempt_log_path`'s divergence is a LIVE DEFECT: `_VERIFY_LOG_RE` matches `-attempt-<n>-verify.jsonl`, oc's shape only, so agy's verifier logs are already misclassified as execute logs by the verifier-phase analytics. The plan files both under "mechanical only" and so loses the one user-visible improvement it makes. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now states the semantic difference with both filenames, and V-03 requires a demonstration that `verifier_phase_of_log` returns `verify` for the new agy name where it returned `execute`. OQ-02's false premise ("nothing parses them by position") is corrected in place with the parser that does. |
| PR-006 | HIGH | UNDER-SCOPE | G. right-sizing and conceptual density | E-02/E-03/E-04 as authored; measured 400 / 664 / 783 oc lines | **EACH MOVE ITEM BUNDLES A WHOLE GROUP AS ONE PASS.** ~1,850 lines relocated in three items, between two files the parent plan calls the highest-contention in the repo, each symbol needing its own dependency analysis, docstring-merge decision and import rewiring; a mid-item failure leaves the package unimportable. `aw ipd lint` passed it because it counts E-leaves and groups, not concepts, which is exactly the gap the rubric warns a passing size lint does not clear. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Items re-scoped to 5 symbols, 4 symbols, and a disclosure: one focused pass each. The size assessment now records the failed original and the reasoning, so the `standard` verdict is earned rather than inherited. |
| PR-007 | MEDIUM | IN-SCOPE | A. correctness (the argued reason, not the answer) | `agent_workflows/oc_runipd.py:3452`, `agy_runipd.py:2267`; 9 of oc's 13 `configured_file` call sites already use `.get` | **THE DEFENSIVE-FORM EXCEPTION IS ARGUED FROM THE WRONG DIRECTION, though its conclusion is right.** F-5/OQ-01 justify keeping agy's `.get` by a `KeyError` "on a recovery path", which reads as speculative and invites a later agent to simplify it away. `initialize_run` writes `configured_file` on every entry it freezes, so a live entry always has it; the real exposure is a queue frozen by an OLDER driver build and resumed by this one. Narrow, real, and nameable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01's rationale replaced with the measured reason and the call-site corroboration, plus a note that all three governed symbols are blocked for other reasons so the decision stands unexercised by this plan as re-scoped. |
| PR-008 | MEDIUM | UNDER-SCOPE | G. scope fence completeness | `tests/test_runner_refork_guard.py`; `tests/test_runner_backlog_close.py:1141`; `tests/test_runner_shutdown.py:160`; `tests/test_orchestrator_probe_cache.py:1203`; `tests/test_lane_allocation_idempotent.py:816` | **THE SCOPE FENCE OMITS FIVE TEST FILES THE CHANGE MUST EDIT.** Two assert via `inspect.getsource` that `terminate_process`'s body names the grace constants (so a constant lift breaks them without any spec changing), one carries the `Owned` table enumerating shared symbols and their exclusions, one pins the import-count baseline, one exercises prompt suppression in both hosts. A fence that omits them makes `aw ipd finalize` demand a `--scope-reason` for edits the plan always required. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All five added to `Scope-Paths`; each named in Project conventions or Required tests with the specific assertion that constrains the change. |
| PR-009 | MEDIUM | IN-SCOPE | C. architecture (import cycles) | `agent_workflows/lane_containment.py:55` imports `runner_shared` | **A GROUP-H LIFT CAN CREATE AN IMPORT CYCLE, and nothing in the plan warns of it.** Two symbols (`build_isolation_notice`, `evaluate_clean_base_for_launch`) need `lane_containment`, which already imports `runner_shared` at module level. Adding the reverse edge at module level makes the package unimportable, which is a whole-toolkit outage rather than a test failure. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded on group H with the required remedy (function-local import, the convention `runner_shared` already uses in 20-plus places) and a new validation item requiring a clean two-way import check. |
| PR-010 | LOW | IN-SCOPE | E. testing (non-vacuity direction) | V-05(b) as authored | **THE NON-VACUITY CONTROL IS ONE-DIRECTIONAL, and the likelier mistake is in the other direction.** Sabotaging a lifted definition proves the suite notices under-lifting. Given PR-002 and PR-003, the more probable error is OVER-lifting: deleting a ruled wrapper or moving the unmovable symbol. A suite asserting only what moved would bless exactly that. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05(b) now requires both directions, and E-05's test table carries the excluded sets with inverse assertions so the suite fails if an excluded symbol is lifted. |
| PR-011 | LOW | IN-SCOPE | E. testing (achievable bar) | measured bare `python3 -m pytest` at HEAD: `1 failed, 7308 passed, 3 skipped, 2 xfailed`; the failure passes in isolation at `7 passed in 1.13s` | **THE 7308 BASELINE IS RIGHT AND ITS ZERO-FAILURE BAR IS NOT MEETABLE.** `ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130` fails under parallel load on a 30s subprocess timeout and passes in isolation. As written, V-05(c) sends the executor chasing a defect this plan did not cause. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05(c) now requires NO NEW failures against that named flake, with the isolation re-run as the disposing evidence. Recorded as F-16 with the measurement. |
| PR-012 | LOW | IN-SCOPE | A. measured claims are verified | `tests/test_orchestrator_probe_cache.py:1203`; 5 of 57 imports are among the 48, 4 of them blocked | **A STATED CONSEQUENCE DOES NOT FOLLOW FROM THE MEASUREMENT.** The plan says E-02 "removes those imports outright and makes the guard meaningful again" and implies a large import-count drop. Only 5 of the 57 oc-to-agy imports are among the 48, and 4 are blocked, so the realistic decrease is ONE and the guard stays as technically-satisfied as today. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 corrected with the per-symbol measurement; the Project conventions claim rewritten; V-05(d) now asks for the ACTUAL decrease rather than an assumed one. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | The plan's own partition contradicts my re-measurement. Trust the plan's 48, or re-measure and rebuild the scope? | RE-MEASURE with the closure test and rebuild the scope from it. | (a) Trust the plan, rejected: I reproduced its body-equality partition exactly and it is correct as far as it goes, so the disagreement is not about data but about which property predicts liftability, and closure demonstrably does. (b) Flag the doubt without measuring, rejected: that hands the maintainer a suspicion instead of an answer, and the measurement is mechanical and cheap. | reproduced the 66-symbol total and the F-2 seven-way partition exactly; then the closure test at HEAD `476354fc` yielding 5 clean, 4 output-changing, 11 excluded, 28 blocked | yes |
| D-2 | Do the 10 `INJECTED` wrappers count as remaining duplication to remove, or as a decided mechanism to preserve? | PRESERVE, and remove them from scope PERMANENTLY rather than deferring them. | (a) Lift them as E-02 says, rejected: the implementation is already single, so there is no duplication to remove, and deleting the wrapper would undo a ruling with two recorded rejected alternatives. (b) Defer them to a later child, rejected as misleading: "deferred" implies the work is still wanted, and it is not. | `818uru` OQ-02 quoted verbatim in `oc_runipd.py:557`; `INJECTED` at `tests/test_runner_shared.py:76`; `SingleDefinitionTests` at `:541` and the wrapper-shape assertion at `:573` | no |
| D-3 | `disable_lane_prompt` is in E-03. Lift it, or honor the pin? | HONOR THE PIN and exclude it permanently. | (a) Lift it and move the flag too, rejected on the pinned reasoning: each host's `_lane_reclaim_prompt` is still DIVERGED and reads its own module's flag, so a shared flag breaks suppression silently. (b) Lift it together with `_lane_reclaim_prompt`, rejected as out of scope here: that symbol is group E (blocked on `LANE_PROMPT_TIMEOUT`) and the pair is a different, larger act. | `UnmovableSymbolTests` at `tests/test_runner_shared.py:1238` with its stated reason; `runner_shared.py:95` and `:620`; behavior exercised at `tests/test_lane_allocation_idempotent.py:816` | no |
| D-4 | OQ-02 chose oc's filename form on the premise that nothing parses these names. That premise is false. Keep the answer, or reopen it? | KEEP oc's form, REPLACE the reasoning: adopting it repairs a live agy analytics defect. | (a) Reopen as a maintainer question, rejected: the evidence points harder at oc's form than the plan's own false premise did, so there is nothing left to decide. (b) Leave the premise standing, rejected: a right answer resting on a false premise is what a later agent "simplifies" away. | `run_analytics_statistics._VERIFY_LOG_RE` at `agent_workflows/run_analytics_statistics.py:1248` matching only oc's shape; `run_viewer.py:761` preferring the oc name with a loose glob fallback | yes |
| D-5 | Four re-scope options exist for the 39 symbols this plan cannot lift. Choose one, or ask? | ASK. Raised as OQ-03, `Blocking: yes`, with all four options, their costs, and my recommendation (option 1). | (a) Choose option 1 myself and re-point three children's dependencies, rejected: it creates a child and restructures a Set with nine pending children and an approved orchestrator whose retirement gate reads the child table, which is scope and priority, reserved to the human. (b) Retire the plan superseded, rejected as the most expensive option chosen unilaterally. (c) Leave the scope as authored and only note the problem, rejected: that leaves an unexecutable plan that lints clean. | GUIDING_PRINCIPLES reserving scope/priority to the maintainer; the orchestrator's child-table retirement gate; the nine pending children's existing numbering and dependency edges | yes |

### Deferred and open

- `PR-001` - `OPEN`:
  - Reason: The measurement is settled; the REMEDY is a Set-restructuring choice among four defensible options, each with different cost, and choosing it for the maintainer would re-shape a Set with nine pending children and an approved orchestrator.
  - Remediation Risk: High
  - Axis: complexity, functionality
  - Required decision or evidence: the maintainer's answer to OQ-03 (execute-as-revised plus a precursor child; absorb groups E/F/H here; retire and re-derive the Set; or execute-as-revised plus a backlog item).
  - Consequence if unresolved: the plan is executable but delivers 9 of 48 symbols, and the remaining 39 have no owner, so the `rununify` orchestrator still cannot retire honestly.
- `PR-004` - `OPEN`:
  - Reason: Not fixable within this plan. Either 6 symbols leave this plan's scope or three children's dependency edges are re-pointed; both change the Set's shape.
  - Remediation Risk: Medium-High
  - Axis: complexity, functionality
  - Required decision or evidence: same OQ-03 answer, which determines where the group-G symbols live.
  - Consequence if unresolved: the symbol-level cycle stays invisible to the dependency checker, and an agent executing the Set in order meets it as a runtime failure in child 04.

### Escalation of the two irreversible decisions

D-2 and D-3 are judged `Reversible: no`: both concern DELETING a mechanism (a ruled injection wrapper,
a pinned unmovable definition), and a wrong call there is discovered as a silent behavior loss in an
unattended run rather than as a test failure. Escalated per the workflow, not merely recorded: both are
raised in the plan as findings F-8 and F-9, both are cited by the `Blocking: yes` OQ-03 whose
`- Finding:` field names them, and both are converted into standing assertions by E-05's inverse
table, so the suite refuses the deletion even if a future agent disagrees with me. The maintainer sees
them at the OQ-03 gate before anything executes.

### Honest limits of this review

- I DID NOT EXECUTE THE LIFT, so "group A is closure-clean" is proven by static closure analysis and by
  reading, not by having moved the code and imported it. The residual risk is a dynamic reference the
  AST walk does not see (a `getattr`, a string-keyed dispatch). E-01 re-runs the measurement at
  execution HEAD, which is where that would surface.
- I DID NOT DECIDE THE RE-SCOPE, deliberately (D-5). My recommendation of option 1 is a recommendation.
- THE GROUP BOUNDARIES FOR E, F, G AND H ARE MINE, not the maintainer's, and a symbol blocked on two
  things is filed under the blocker I judged primary (for example `enforce_dependency_preflight` needs
  both an oc-only helper and a host-divergent constant; I filed it F and noted it is really child 04's).
  A different reviewer could partition those 28 differently without contradicting the measurement.
- I VERIFIED THE SUITE BASELINE ONCE, at 7308 passed with one load-dependent flake. A second run under
  different load could surface a different flake; the plan now names the mechanism for disposing of one
  rather than pretending none exists.
