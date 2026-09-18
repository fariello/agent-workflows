# Review findings: plan li44r9

- Subject-Id: li44r9
- Subject-Type: ipd
- Reviewed-At: 2026-09-17
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `a3c103d7` in an isolated review lane. Structural preflight `aw ipd lint --phase author`
CONFORMED (exit 0) before revision; after revision the linter reports only `IPD-Q501`, which is the blocking
OQ-03 I raised doing its job. No pre-review snapshot was needed: the plan was committed and byte-identical to
the lane input. This is the child of `a5wdne`, which I reviewed in the previous turn; I re-measured
everything rather than importing conclusions.

THE SYMBOL SET IS EXACTLY RIGHT, and it is worth stating plainly because the rest of this record is about a
premise that is not. Re-running the plan's OWN method (`ast.unparse` after stripping docstrings) at review
HEAD:

```text
plan claims 17: 17
measured byte-identical: 29
claimed but NOT identical: []
identical but NOT claimed: ['_integrate_stranded_lanes', 'build_lane_outcome', 'collect_lane_earned_paths',
 'discover_plans', 'driver_begin', 'git_common_dir', 'git_head', 'git_status', 'handle_integrate_command',
 'run_checked', 'save_state', 'validate_manifest']
```

All twelve extras delegate to `runner_shared` already, so excluding them is correct and the 17/12 partition
verifies symbol for symbol. F-4 also confirms: zero `__file__` across all seventeen.

BUT THE PLAN'S CENTRAL SAFETY CLAIM IS FALSE FOR NINE OF THE SEVENTEEN, and this is the finding the review
exists for. The Goal asserted "identical bodies mean the shared version is the current body unchanged", on
the strength of a scan for exactly two hazards. It missed a third: A BYTE-IDENTICAL BODY CAN REFERENCE A
MODULE-LEVEL NAME WHOSE VALUE DIFFERS PER HOST, because AST comparison matches on the NAME. Measured:

```text
StallWatchdog          -> ['terminate_process']            (in-tranche)
_escalation_recorder   -> ['_detect_driver_command']
disable_lane_prompt    -> ['_LANE_PROMPT_DISABLED']
driver_finalize        -> ['_compute_scope_reconciliation', 'pinned_child_env', 'pinned_module_argv']
handle_stop_command    -> ['_detect_driver_command']
install_stop_triggers  -> ['_detect_driver_command']
locked_run             -> ['run_lock']                     (in-tranche)
set_plan_approved      -> ['FULL_AUTO_ACTOR', 'FULL_AUTO_APPROVAL_MESSAGE', 'pinned_module_argv']
terminate_process      -> ['_SIGINT_GRACE_SECONDS', '_SIGTERM_GRACE_SECONDS']
```

Comparing every one of those constants across hosts, exactly one differs, and it is the worst possible one:

```text
FULL_AUTO_ACTOR            DIFFERS
    oc : 'aw oc run --full-auto'
    agy: 'aw agy run --full-auto'
FULL_AUTO_APPROVAL_MESSAGE SAME
_LANE_PROMPT_DISABLED      SAME
_SIGINT_GRACE_SECONDS      SAME
_SIGTERM_GRACE_SECONDS     SAME
```

`set_plan_approved` reads `FULL_AUTO_ACTOR` at `oc_runipd.py:855` and `:886` and passes it as `--actor` to
`aw set auto-approved`, which lands in a plan's PERMANENT `## Workflow history`. A verbatim lift would make
every Antigravity auto-approval record that `aw oc run` did it. That is precisely the durable-history
misattribution `HostLabels`'s own no-defaults rationale cites as the harm it exists to prevent
(`runner_shared.py:8533-8537`). And three more symbols call `_detect_driver_command`, which is not
incidental plumbing: it IS each host's labels binding (`oc_runipd.py:8768` binds `OC_HOST_LABELS`,
`agy_runipd.py:5236` binds `AGY_HOST_LABELS`). So four of the seventeen need `HostLabels`, which this plan's
own convention note calls "a signal that symbol belongs in Order 02". That is a sequencing decision, not an
executor's judgement, so it is OQ-03 rather than something I resolved.

THE STRONGEST EVIDENCE THIS IS REAL RATHER THAN PEDANTIC is that the repository already has a category for
it: `tests/test_rununify_run_queue.py` carries `DIVERGENT_CONSTANTS = ('DEPENDENCY_BLOCK_RECOVERY_HINT',)`
beside `EQUAL_CONSTANTS`, because a shared body reaching a per-host constant is a known hazard here.
`FULL_AUTO_ACTOR` belongs in that tuple and is not in it.

F-5 UNDERCOUNTS THE PROSE CONTAMINATION. Scanning all seventeen for host tokens finds THREE, not two:
`evaluate_clean_base_for_launch:2407` ("the agy twin"), `terminate_process:5274` ("a child OpenCode
process") and `locked_run:8744` ("the per-turn `run_opencode` handlers"). All three are prose-only so the
safety conclusion stands, but E-03 as scoped lifts two and would leave `locked_run`'s docstring naming
`run_opencode`, a SYMBOL a third host will not have.

F-6 CITES THE WRONG GUARD, AND THAT WOULD HAVE COST AN EXECUTOR REAL TIME. It quotes
`test_every_still_double_defined_symbol_really_is_defined_in_both_runners` and its helpful "remove it from
STILL_DOUBLE_DEFINED" message. That test uses `assertIn(name, defs)`, and a WRAPPER is still a `def`, so it
keeps PASSING after a lift and the quoted message never prints. The test that fails is
`test_every_still_double_defined_symbol_is_a_REAL_fork_not_a_thin_wrapper`, verified by importing the guard
module and calling its own predicate:

```text
is_pure_delegation(wrapper) -> True  -> assertFalse test FAILS
```

And those tables live in THREE files for this tranche, not one: `test_rununify_execute_item.py` (4 symbols),
`test_rununify_run_queue.py` (4) and `test_rununify_initialize_run.py` (1). This is the defect I raised as
PR-001 on the parent `a5wdne` and could not fix there because the children were outside that ledger; this
plan IS in this ledger, so it is fixed here.

FIVE MORE ASSERTIONS BREAK IN TWO FILES NOBODY DECLARED, found by reading them rather than by guessing.
`test_runner_shutdown.py:160` asserts `inspect.getsource(mod.terminate_process)` contains
`"runner_shutdown.terminate_process"`; I confirmed the current oc body does contain it, and a post-lift
wrapper calling `runner_shared.terminate_process` will not. `:173` is worse because it is BEHAVIORAL: it sets
`oc._SIGINT_GRACE_SECONDS = 0.11` and requires the value to reach the reaper, a per-host tuning contract a
shared body reading shared constants would break. `test_runner_backlog_close.py:1145` requires the body to
contain both grace constants. All green today (`74 passed` across the two files). Two other pins survive and
I said so explicitly so they are not touched needlessly (`test_runner_stop_triggers.py:940` reads a CALL
SITE; `:2343` only checks `hasattr`).

THE SUITE BASELINE IS WRONG TWICE OVER. The plan pins `7825 passed`; measured at review HEAD, `env -u
AW_EXECUTION_ROLE python3 -m pytest` gives `7897 passed, 3 skipped, 2 xfailed` and a bare run in this managed
worker lane gives `31 failed, 7866 passed, 3 skipped, 2 xfailed`.

TWO SMALLER THINGS. The required-tests section asks for `oc_runipd.<sym> is agy_runipd.<sym>`, which is FALSE
under the wrapper design this plan deliberately chose (verified on the existing wrapper `git_head`: both
`oc.git_head is agy.git_head` and `oc.git_head is RS.git_head` are False), so the primary evidence form would
fail a correct implementation. And the gate demands "V-06's real driver execution" while the plan had only
V-01..V-05.

WHAT I FIXED. Replaced the false safety paragraph with the measured closure table and the two divergence
cases; corrected F-5 to three symbols and F-6 to the right assertion in three files; added F-9 through F-13;
added E-06 (closure enumeration before any lift), E-07 (re-base the five non-`rununify` assertions,
preserving the grace-constant contract behaviorally) and E-08 (carry the divergent closure through
`HostLabels` with no default, pinned by a both-directions attribution test), with V-06/V-07/V-08; rewrote
E-01 to commit the scanner and state its metric, E-02 to lift only what E-06 clears, E-03 to cover three
symbols, E-04 to name three files and the correct assertion, E-05 to assert delegation rather than identity;
corrected the required tests and both baselines; added four test files to `Scope-Paths`; added
`- From-Backlog: dstnso`; corrected the gate's V-06 reference and added the finalize-justification,
shared-checkout and suite-form clauses; raised OQ-03 `Blocking: yes` with `Finding: PR-001`; set
`Readiness: no-go`; raised `Highest E allocated` 05 -> 08.

WHAT I DID NOT DO. I did not perform any lift, edit any test, or touch product code. I did not decide OQ-03,
because whether the four divergent symbols stay here or move to Order 02 is a decision about how the Set is
sequenced and the orchestrator recorded that ordering as deliberate.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. correctness; D. domain invariants (durable history) | `oc_runipd.py:817` vs `agy_runipd.py:922`; reads at `:855`, `:886`; `HostLabels` no-defaults rationale `runner_shared.py:8533-8537` | **THE "DECISION-FREE LIFT" PREMISE IS FALSE FOR NINE OF SEVENTEEN, AND ONE CASE MISATTRIBUTES PERMANENT HISTORY.** A byte-identical body can close over a per-host name, because AST comparison matches on the NAME. `FULL_AUTO_ACTOR` differs per host and reaches a plan's `## Workflow history` via `--actor`, so a verbatim lift of `set_plan_approved` records every agy auto-approval as `aw oc run`. Three more symbols call `_detect_driver_command`, which IS the labels binding. | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | OPEN | ESCALATED as OQ-03 (`Blocking: yes`, `Finding: PR-001`) with two routes priced, because whether these four stay here or move to Order 02 is a Set-sequencing call and this plan's own convention note points at Order 02. Meanwhile: the closure table is written into the Goal, E-06 forbids lifting anything before the closure is classified, and E-08 specifies the descriptor treatment with a both-directions attribution test. Route (c), a verbatim lift, is refused and not offered. |
| PR-002 | HIGH | UNDER-SCOPE | D. anti-regression; E. testing | four pin tables enumerated by AST; `is_pure_delegation(wrapper)` -> True; `assertFalse` at `test_rununify_execute_item.py:190`, `test_rununify_run_queue.py:306`; `95 passed` today | **THE PIN RE-BASE NAMES ONE FILE OF THREE AND CITES AN ASSERTION THAT DOES NOT FIRE.** The quoted `assertIn` test still passes for a wrapper, so its remedy message never prints; the failing assertion is `assertFalse(is_pure_delegation(...))`, and this tranche's symbols are pinned in three files. This is the parent's PR-001, unfixable there. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-04 rewritten with all three files and their per-file symbol lists, the correct assertion named and the wrong one explained; `tests/test_rununify_execute_item.py` and `tests/test_rununify_run_queue.py` added to `Scope-Paths`; V-04 requires all three diffs and the four pin files run together; F-6 corrected in place. |
| PR-003 | HIGH | UNDER-SCOPE | D. anti-regression; E. testing | `test_runner_shutdown.py:160` (verified the current body contains the asserted string), `:173`; `test_runner_backlog_close.py:1145`; `74 passed` today | **FIVE ASSERTIONS IN TWO UNDECLARED FILES BREAK ON THE LIFT, ONE OF THEM A BEHAVIORAL CONTRACT.** Two read the wrapper's SOURCE and require strings a delegation will not contain; the third tunes a host's `_SIGINT_GRACE_SECONDS` and requires it to reach the reaper, which a shared body reading shared constants breaks. | C:Low; U:Medium; S:Low; F:High; Overall:Medium | FIXED | New E-07 re-bases all three with a per-assertion reason and REQUIRES the grace-constant pass-through to remain enforced behaviorally rather than re-worded away; both files added to `Scope-Paths`; V-07 added and refuses an assertion weakened into vacuity; the two pins that SURVIVE are named so they are not touched needlessly. |
| PR-004 | HIGH | IN-SCOPE | A. correctness (an incomplete hazard scan presented as complete) | host-token scan across all 17: three hits, at `:2407`, `:5274`, `:8744` | **F-5's "EXACTLY TWO" HOST-TOKEN MENTIONS IS THREE.** `locked_run`'s docstring names "the per-turn `run_opencode` handlers", and E-03 as scoped lifts only two, so a shared symbol would keep naming a FUNCTION that will not exist for a third host. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-5 corrected with all three locations; E-03 and V-03 cover three symbols; the Goal notes `run_opencode` is the worst of the three because it is a symbol name rather than a product name. |
| PR-005 | HIGH | UNDER-SCOPE | E. testing (a false baseline would be recorded) | measured `7897 passed` with `env -u`; `31 failed, 7866 passed` bare in a worker lane | **THE PINNED `7825 passed` BASELINE MATCHES NEITHER MEASUREMENT AND IS UNREACHABLE IN A WORKER LANE.** An executor would record a false failure or "fix" 31 tests that refuse by design. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Both measured numbers written into Required tests and V-05, with the invocation form required and the gate restated as NO NEW failures rather than an absolute count. |
| PR-006 | MEDIUM | IN-SCOPE | E. testing (evidence unsatisfiable under the chosen design) | verified `oc.git_head is agy.git_head` False and `oc.git_head is RS.git_head` False | **THE PRIMARY IDENTITY EVIDENCE FORM IS FALSE FOR A WRAPPER,** which is the form OQ-01 deliberately chose. `oc_runipd.<sym> is agy_runipd.<sym>` would fail a correct implementation; the "or both delegate" fallback carried the whole requirement. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Required tests, E-05 and V-02 now require a DELEGATION predicate and explicitly forbid the `is` check, with the measured reason; added to Project conventions. |
| PR-007 | MEDIUM | UNDER-SCOPE | E. testing (a criterion depending on a tool that does not exist) | no whole-runner fork scanner in `tests/`; parent PR-006 | The parent Set's headline criterion re-runs "the same AST scan", which is not committed anywhere, and this plan's E-01 was the natural place to produce it but did not say so. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now must COMMIT the scanner and state its metric; V-01 requires the scanner path plus its output. |
| PR-008 | MEDIUM | IN-SCOPE | A. correctness (unreproducible figures presented as measured) | claimed 380 total measures 583 by span / 196 by `ast.unparse`; `StallWatchdog` 59 measures 66/49; `set_plan_approved` 33 measures 77/11 | **THE LINE FIGURES REPRODUCE UNDER NO METRIC,** while the SYMBOL counts reproduce exactly. They appear in the Concern, F-1, F-8 and the Scope check as the cost argument. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-1, F-2, F-8 and the Scope check corrected to state which metric reproduces and to make the SYMBOL count the load-bearing number; E-01/V-01 compare against the symbol baseline rather than the line figure; F-8's argument restated in symbols. |
| PR-009 | MEDIUM | UNDER-SCOPE | G. traceability | `dstnso` (`open`, `high`) names 4 symbols this plan lifts | The plan graduates part of an open backlog item with no `From-Backlog` link, so the handoff is invisible to `aw attention` and the backlog close predicate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- From-Backlog: dstnso` added, matching the parent orchestrator. |
| PR-010 | LOW | IN-SCOPE | G. executability | gate cites "V-06's real driver execution"; plan had V-01..V-05 | The gate referenced a validation item that did not exist, so its non-optional requirement pointed at nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate corrected to cite V-05 (which carries the driver execution) and to note V-06 now validates the closure scan. |
| PR-011 | LOW | IN-SCOPE | A. correctness | OQ-02's conclusion is right; its cited test and single-file premise are wrong | OQ-02 resolves correctly ("no conflict, re-base it") on reasoning that quotes the non-firing assertion and assumes one pin file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A correction appended to OQ-02 preserving the resolution and fixing the reasoning, cross-referencing F-6 and E-04. |
| PR-012 | LOW | UNDER-SCOPE | G. executability | gate had worktree, path-scoped commit and never-push, but no finalize-justification, no shared-checkout re-verification, no suite-form rule | Three required execution-contract elements were missing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three added, with the finalize wording in DECLARE-and-JUSTIFY form (never "STOP and report" for a scope question) per the 2026-09-01 ruling. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Four symbols need a host-varying value. Decide the treatment myself, or escalate? | ESCALATE as `Blocking: yes` (OQ-03), while writing E-08 so either route is cheap to take. | (a) Decide route (a) myself and just add the descriptor field, rejected: the plan's own convention note says needing `HostLabels` means the symbol belongs in Order 02, so choosing (a) overrides a documented convention and blurs the Set's risk-ascending ordering, which the orchestrator records as a deliberate design decision. (b) Decide route (b) myself and move four symbols to Order 02, rejected: it changes two plans' contents across a declared dependency edge, which is the maintainer's sequencing call. (c) Let the executor decide at runtime, rejected outright: the wrong choice silently misattributes permanent history. | `FULL_AUTO_ACTOR` differing at `oc_runipd.py:817` / `agy_runipd.py:922`; the plan's own convention note; the orchestrator's risk-ordering rationale | yes |
| D-2 | Is PR-001 a BLOCKER? | YES. It is a silent invariant violation: a verbatim lift writes a false actor into a plan's permanent workflow history, and nothing in the authored plan would catch it. | (a) HIGH, rejected: the workflow reserves BLOCKER for a silent invariant violation, and durable-history misattribution with no test to catch it is exactly that. (b) MEDIUM on the grounds that it is one constant, rejected: the blast radius is every agy auto-approval, permanently, and the plan's premise (and therefore its whole risk argument) rests on the claim being false. | `--actor` reaching `## Workflow history`; `HostLabels` docstring naming this harm as its reason for existing | yes |
| D-3 | The pin-file defect is the parent's PR-001, which I left OPEN there. Fix it here? | YES, FIX IT FULLY. This plan is in this review's ledger, so the ledger objection that blocked me on the parent does not apply. | (a) Leave it escalated for consistency with the parent round, rejected: consistency is not a reason to leave a known guaranteed suite failure unfixed when I now have the authority to fix it. (b) Fix only the `Scope-Paths` line, rejected: the E-item also cited the wrong assertion, so declaring the files without correcting the guidance would still send the executor hunting a failure that never prints. | four pin tables measured; `is_pure_delegation(wrapper)` -> True; this plan's presence in the invocation | yes |
| D-4 | `test_runner_shutdown.py:173` is a behavioral contract a lift breaks. Require it preserved, or allow it re-based? | REQUIRE THE CONTRACT PRESERVED, allowing the assertion to be re-based only if something still enforces the pass-through. | (a) Treat it like the source pins and allow a straight re-base, rejected: it is not a source pin, it is a per-host tuning contract, and "re-basing" it into vacuity would delete a real behavior guarantee under cover of a mechanical edit. (b) Forbid touching it at all, rejected: the lift legitimately changes where the constants live, so the assertion's current form cannot survive unchanged; the contract must, its spelling need not. | the test body setting `oc._SIGINT_GRACE_SECONDS = 0.11` and asserting it reaches the spy; the maintainer's re-base-deliberately-never-weaken rule | yes |
| D-5 | The line figures do not reproduce. Recompute or flag? | FLAG, and make the SYMBOL count the gate. | (a) Substitute my `ast.unparse` numbers, rejected: I cannot know the author's metric, and the same figures appear in the parent and two siblings, so replacing them here alone would make the Set internally inconsistent. (b) Ignore it since the symbol set is right, rejected: F-8's cost argument is arithmetic on the line figure, so a reader funding the work is reading an unreproducible number. | four metrics computed at review; the identical treatment I applied to the parent (its PR-007) | yes |
| D-6 | Verdict and readiness, given one OPEN BLOCKER? | `REVIEWED - OPEN QUESTIONS`, readiness `no-go`, `Status: reviewed`. | (a) `APPROVE WITH REVISIONS APPLIED` / `go-pending-approval`, rejected: a BLOCKER left OPEN is the readiness table's definition of not-ready, and approving would greenwash a plan whose premise I just disproved. (b) `REJECT - NEEDS REPLAN`, rejected: thirteen of the seventeen symbols are genuinely decision-free, the approach and the wrapper target form are sound and well-precedented, and the fix for the other four is a bounded decision plus one new E-item. | workflow verdict/readiness tables; PR-001 `Decision: OPEN`; `aw ipd lint` now refusing on OQ-03 by design | yes |

### Escalation of the irreversible decisions

None of this round's six decisions is judged `Reversible: no`. Every one is undone by editing this plan
before it executes: nothing here publishes an interface, migrates data, deletes anything, or produces a
released artifact. D-1 LOOKS irreversible because the thing it defers is a change to permanent run history,
and that is exactly why it is deferred rather than decided: leaving OQ-03 blocking means the plan cannot
execute until a human chooses, so a wrong call costs one round trip instead of a permanent stream of
misattributed approvals. The irreversible act is deliberately not authorized by me.

### Honest limits of this review

- I DID NOT PERFORM THE LIFT. Every measurement is against unmodified HEAD `a3c103d7`, and `git status` was
  clean at the end of the review. PR-002 and PR-003 are proven by reading the assertions and by calling the
  guards' own `is_pure_delegation` predicate on a synthetic delegating body IN PROCESS, not by relocating a
  symbol and observing a red suite. The children's V-items must do that.
- MY CLOSURE SCAN IS NAME-BASED. I collected `ast.Name` and `ast.Attribute` references per symbol and
  intersected them with each runner's module-level names, then checked which were absent from `dir(runner_shared)`.
  A dependency reached dynamically (a `getattr`, a string-keyed dispatch) would not appear, so E-06 must
  re-derive the table rather than inherit mine; nine symbols and nine names is a LOWER BOUND.
- I CHECKED CONSTANT EQUALITY BY `ast.literal_eval`. A dependency whose value is computed at import time
  reports `<expr>` and I did not evaluate it, so a divergence hidden in an expression could have escaped.
  Of the five constants in scope, all five were literals.
- I DID NOT ENUMERATE EVERY CONSUMER OF THE SEVENTEEN. I searched the test tree for source-reading pins
  (`inspect.getsource` on a runner attribute) and for the specific symbols; a consumer reaching a symbol by
  another route would not have appeared. Five broken assertions in two files is a LOWER BOUND, which is why
  E-07 is written to re-base what it finds rather than exactly the three I named.
- I DID RUN THE FULL SUITE TWICE (that is how PR-005 was measured): `7897 passed, 3 skipped, 2 xfailed` with
  `env -u AW_EXECUTION_ROLE`, and `31 failed, 7866 passed, 3 skipped, 2 xfailed` bare in this worker lane.
  I also ran the four `test_rununify_*` pin files together (`95 passed`) and the two newly declared files
  (`74 passed`).
- I DID NOT RUN A DRIVER EXECUTION, which the plan itself requires and which I agree cannot be substituted
  by structural tests for lock, stop-trigger and lifecycle machinery.
- I DID NOT RESOLVE OQ-03, and I did not re-open OQ-01 (the wrapper-versus-direct-import question), whose
  resolution I verified is sound and whose chosen form is what PR-006's identity correction follows from.
