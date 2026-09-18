# Review findings: plan nmlx47

- Subject-Id: nmlx47
- Subject-Type: ipd
- Reviewed-At: 2026-09-17
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `0e9068dd` in an isolated review lane. Structural preflight `aw ipd lint --phase author`
CONFORMED (exit 0) before revision; after revision `--phase review-finalize` reports only two `IPD-Q501`,
which are the blocking OQ-04 and OQ-05 this round raised doing their job, not structural defects. No
pre-review snapshot was needed: the plan was committed and unmodified. This is child 02 of `a5wdne`, whose
review and whose sibling `li44r9`'s review I read but did not import: every number below was re-measured.

THE PARTITION IS RIGHT AND ONE FIGURE REPRODUCES ON THE FIRST TRY, which is worth stating because the rest
of this record is about defects and because THREE of the parent Set's four line figures reproduced under no
metric at all. Re-running an `ast.unparse` scan at review HEAD over the twelve named symbols:

```text
expand_selectors                          90/90   ratio=1.00
reclaim_lanes_on_interrupt                60/60   ratio=1.00
reconcile_disposition                     47/45   ratio=0.93
_lane_reclaim_prompt                      37/37   ratio=0.97
reconcile_interrupted                     37/37   ratio=1.00
_add_output_mode_flags                     6/6    ratio=0.92
enforce_dependency_preflight              15/11   ratio=0.28
classify_recovery_disposition             34/4    ratio=0.05
route_recovery_turn                       32/4    ratio=0.08
build_verify_and_continue_notice          37/4    ratio=0.05
retry_deferred_integrations               70/49   ratio=0.72
_record_forced_stop                       23/16   ratio=0.64
sum oc lines: 488
```

Every length pair matches the plan exactly and the total is 488 on the nose. The three agy stubs really are
stubs (`agy_runipd.py:2473`, `:2483`, `:2495`, each `from agent_workflows.oc_runipd import <name> as
_shared`), `HostLabels` is exactly as described (`runner_shared.py:9384`, no-defaults `NamedTuple`, both
host instances bound), and the guard hole is real: I ran
`test_review_findings_cascade.py::test_no_runner_to_runner_import` GREEN while 53 names are imported from
`oc_runipd` into `agy_runipd`. The three-shape insight ("a single de-duplication tactic applied to all
twelve would be wrong for at least two thirds of them") is the correct read and is the plan's best idea.

BUT THREE OF THE TWELVE CANNOT BE LIFTED AT ALL, AND ONE OF THEM BREAKS AN UNATTENDED RUN SILENTLY. This is
PR-001 and it is why "resolve all twelve to ONE definition" is not a hard target but an unreachable one.
`_lane_reclaim_prompt` READS the module-level MUTABLE `_LANE_PROMPT_DISABLED`; `disable_lane_prompt` WRITES
it through `global`; and `disable_lane_prompt` is PERMANENTLY unmovable, pinned by
`tests/test_runner_shared.py::UnmovableSymbolTests` and documented twice inside `runner_shared` itself
(`:106-107`, `:759-760`). Measured:

```text
runner_shared._LANE_PROMPT_DISABLED   False
runner_shared._lane_reclaim_prompt    False
oc._LANE_PROMPT_DISABLED is agy._LANE_PROMPT_DISABLED   True   (both False, i.e. equal VALUES)
oc.disable_lane_prompt is agy.disable_lane_prompt        False  (two functions, two flags)
```

So a shared reader would consult a flag no host ever sets. The symptom is the one `runner_shared`'s own
docstring names: an unattended run pausing to ask a question nobody is there to answer, with no error naming
the cause. `reclaim_lanes_on_interrupt` calls both and is transitively blocked (its closure includes both
names, neither resolvable in `runner_shared`).

THE STRONGEST EVIDENCE THIS IS A REAL BLOCKER RATHER THAN MY OPINION IS THAT IT IS ALREADY FILED. Open
backlog `8hx3g3` describes this EXACT deadlock, names `_lane_reclaim_prompt` AND
`reclaim_lanes_on_interrupt` as its scope, and states the remedy plainly: "Making these two symbols share
requires the FLAG to stop being module-level mutable state ... Any of those is a DESIGN decision about a
live interrupt path, not the mechanical 'move a constant, then lift'". It further records that
`runner_shared`'s "no module-level mutable state" rule independently forbids the naive fix and that the
maintainer already DECLINED a registration seam. A de-duplication plan that quietly absorbs that design act
is how a guarded exclusion gets "finished" by someone reading a count instead of a constraint.

`enforce_dependency_preflight` is the fourth unliftable one, and the plan contradicts itself about it: the
Concern files it among "SEVEN near-identical (ratio >0.9, no host token in code)" while its measured ratio
is 0.28, and the plan's OWN OQ-03 quotes `rununify` 02 settling its fate as "KEEP, narrowed". Note also
that the Concern's near-identical list ENUMERATES ONLY SIX names, so the seventh was never written down
(PR-005).

THE SECOND BLOCKER IS E-02's DIRECTION, and it would have set this plan against another approved Set.
E-02 asks for a guard on the COUPLING rather than one spelling; E-03 then says "re-point the remaining
runner-to-runner imports the E-02 guard names, or record per import why it must stay". Measured by AST walk,
that is 8 `ImportFrom` statements binding 53 names, of which 44 are DELIBERATE re-exports:

```text
:351   4 names   ToolIdentityError, assert_child_tool_identity, pinned_child_env, pinned_module_argv
:413  20 names   SuiteCheckResult, integration_is_earned, run_suite_check, BacklogCloseVerdict, ...
:437  16 names   DEPENDENCY_FATAL_RULES, _artifact_owners, cascade_dependency_blocked, ...
:479   9 names   SPEC_NOT_FINALIZED, SPEC_RECONCILED, queue_plan_path, ...
:1644  1 name    enforce_dependency_preflight
:2473  1 name    classify_recovery_disposition        <- this plan's
:2483  1 name    build_verify_and_continue_notice     <- this plan's
:2495  1 name    route_recovery_turn                  <- this plan's
```

Twelve of those names are pinned BY OBJECT IDENTITY in
`tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests._SHARED_NAMES`, whose
`test_the_implementation_is_shared_not_copied` exists precisely so agy BINDS rather than COPIES them, and
`cnwy8g` records that `ruff --fix` deleted 6 of them once already, which is why the `as <same-name>`
spelling is load-bearing. Their proper removal is a RE-HOMING into `runner_shared`, and that work is already
owned: backlog `cnwy8g` graduated into `runnerlayer` `9kmbr0` (classify all 47/48 and freeze the set) and
`1f7xno` (re-home in reviewable batches), BOTH `Status: approved` and unexecuted, both carrying
`- From-Backlog: cnwy8g`. So the authored E-02/E-03 would have this plan do `1f7xno`'s job with none of its
guards and none of its fence. Re-scoped to a NAMED RATCHET; the sequencing question is OQ-05.

THE FENCE OMITTED SEVEN FILES, and one omission is sharper than a missing pin table.
`tests/test_resumedupe.py::test_the_antigravity_twin_never_holds_a_second_implementation` accepts each of
E-03's three symbols ONLY in one of two shapes: a delegating stub (`assertIn("from agent_workflows.oc_runipd
import", rendered)`, at most two statements) or a `_LIFTED_TO_RUNNER_SHARED` entry with
`oc.X is agy.X is runner_shared.X`. E-03's lift makes the first false, so the second must be arranged IN THE
SAME CHANGE or that test fails on a file the plan never declared. I ran it green at review to confirm it is
live (`1 passed`). The same file AST-parses `_lane_commit_subjects` out of `module_source(OC)` at `:314-318`
and reads `OC.DISPOSITION_*` in 15 assertions, both of which E-03's closure move disturbs.

THE CLOSURE OF THE THREE STUBS WAS NEVER MEASURED, which is the same omission that cost siblings `li44r9`
and `i3d6ml` a review round each. Measured here:

```text
classify_recovery_disposition -> RecoveryDisposition, DISPOSITION_FRESH_EXECUTION,
                                 DISPOSITION_UNDETERMINED, DISPOSITION_VERIFY_AND_CONTINUE,
                                 _lane_commit_subjects      (all OC-ONLY, none in runner_shared)
route_recovery_turn           -> DISPOSITION_FRESH_EXECUTION, DISPOSITION_UNDETERMINED, save_state
build_verify_and_continue_notice -> _run_git                (already in runner_shared: clean)
```

agy imports NONE of the five, so a naive move raises `NameError` at import time in a 9,588-line and a
5,784-line module.

TWO "GENUINE DIFFERENCES" ARE NOT WHAT THE PLAN SAYS, and the correction makes E-05 smaller and its
mechanism different. Normalizing both bodies with docstrings stripped:

```text
retry_deferred_integrations: normalized 39/39, ONE differing line
  -   ... make_integration_validation_runner(state, run_dir, item))
  +   ... make_integration_validation_runner(state, run_dir, dict(item)))
_record_forced_stop: normalized 10/10, ONE differing line
  -   def _record_forced_stop(..., stop: runner_stop.StopNowForce) -> ...
  +   def _record_forced_stop(..., stop: 'runner_stop.StopNowForce') -> ...
```

The second is a QUOTED TYPE ANNOTATION, i.e. not a behavior difference at all. And the `aw agy` token the
plan says `HostLabels.command` exists to supply is in `retry_deferred_integrations`'s DOCSTRING, not its
code (scanned both bodies: `code-tokens: []`, `raw tokens: ['aw agy']` for agy only). Their real host-varying
content is CALLEES (`integrate_lane_branch`, `git_status`, `save_state`), which is the `INJECTED` wrapper
shape the maintainer already ruled on in `818uru` OQ-02, not a `HostLabels` case. V-05 as authored demanded
evidence of a code path that does not exist.

THE SUITE BASELINE MATCHES NEITHER MEASUREMENT. The plan pins `7825 passed, 3 skipped, 2 xfailed`. Measured
at review HEAD, bare `python3 -m pytest`:

```text
AW_EXECUTION_ROLE=worker (this lane):  32 failed, 7936 passed, 3 skipped, 2 xfailed in 109.50s
env -u AW_EXECUTION_ROLE:                        7968 passed, 3 skipped, 2 xfailed in 114.66s
```

The 32 are role refusals by design (`test_ipd_lifecycle_cli.py`, the driver integration suites), verified by
running one of those files with the variable unset: `89 passed`. An executor gating on "bare and green"
against `7825` would either record a false failure or "fix" tests that refuse on purpose.

WHAT I FIXED, AND WHAT I DELIBERATELY DID NOT. Fixed in place: the shape partition and its missing seventh
name; the Goal's unreachable promise, replaced with a measured per-symbol blocker table; E-01 extended to
scan the closure (the measurement whose absence is this Set's recurring defect); E-02 narrowed to a named
ratchet with the 44 pinned re-exports protected and their owner named; E-03 given the five closure names,
the `_LIFTED_TO_RUNNER_SHARED` obligation and the source-pin re-base; E-04 corrected from "seven" to the
closure-cleared set with the three defensive forms protected by citation; E-05 corrected on both false
premises with the two `getsource` pins named; E-06 extended from one pin file to four plus the
`_add_output_mode_flags` differ-assertion and the exact-53 import baseline; E-07 ADDED to make the residue a
deliverable; seven files added to the fence; the suite baseline superseded by both measurements; V-01..V-07
rewritten to demand the specific evidence each item can actually produce (and V-05 to REFUSE the impossible
evidence it previously asked for); the gate given the resolved-question list, the do-not-lift rule, the
declare-and-justify scope wording, the honesty rule, the shared-checkout re-verification step and the
conditional finalize ownership; and `Highest E allocated` 06 -> 07.

NOT FIXED, deliberately: OQ-04 (exclude the three and accept an unmet parent criterion, or graduate
`8hx3g3` first) and OQ-05 (order this plan against the approved `runnerlayer` Set, or declare an edge). Both
change either another Set's queue or the parent's acceptance criteria, and neither is an executor's or a
reviewer's call.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. correctness; D. anti-regression; G. executability | `tests/test_runner_shared.py::UnmovableSymbolTests`; `runner_shared.py:106-107`, `:759-760`; backlog `8hx3g3`; measured `hasattr(runner_shared, "_LANE_PROMPT_DISABLED")` -> False; closure scan naming `_lane_reclaim_prompt`+`disable_lane_prompt` in `reclaim_lanes_on_interrupt` | **THE PLAN PROMISES TWELVE AND THREE ARE UNLIFTABLE; THE SHORTEST PATH TO THE COUNT SILENTLY BREAKS AN UNATTENDED RUN.** `_lane_reclaim_prompt` reads module-level MUTABLE state that the permanently-unmovable `disable_lane_prompt` writes through `global`; a shared reader consults a flag no host sets, so prompt suppression on a repeated interrupt stops working with no error naming the cause. `reclaim_lanes_on_interrupt` is transitively blocked. `enforce_dependency_preflight` is settled as "KEEP, narrowed" at ratio 0.28. | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | OPEN | ESCALATED as OQ-04 (`Blocking: yes`, `Finding: PR-001`). NOT fixed here: the choice between excluding three symbols (leaving the parent's headline criterion unmet) and graduating `8hx3g3` first (a design decision on a live interrupt path, plus one more plan) is a scope call. Mitigated so route (a) is safe: E-07 added to make the residue a deliverable, E-06 now asserts exclusions in the INVERSE direction per `test_rununify_lift.py`'s precedent, the Goal names each blocker with its citation, and the gate carries an explicit do-not-lift rule for the two. |
| PR-002 | BLOCKER | OVER-SCOPE | C. architecture; E. testing; G. executability | AST walk: 8 statements / 53 names; `CrossDriverSymmetryTests._SHARED_NAMES` (12 names, `assertIs`); `cnwy8g` on the `ruff --fix` deletion; `9kmbr0` and `1f7xno` both `Status: approved` with `From-Backlog: cnwy8g` | **A GUARD BANNING THE COUPLING WOULD DEMAND THIS PLAN DELETE ANOTHER APPROVED SET'S WORK.** 44 of the 53 imported names are deliberate `as <same-name>` re-exports from three executed plans, 12 pinned by object identity so agy BINDS rather than COPIES them. E-03's "re-point the remaining imports or justify each" is 44 relocations or 44 justifications inside a fence declaring neither `test_runner_item_dependencies.py` nor the `runnerlayer` plans that own the work. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium-High | OPEN | PARTLY FIXED and the remainder ESCALATED as OQ-05 (`Blocking: yes`, `Finding: PR-002`). Fixed: E-02 re-scoped to a NAMED RATCHET over this plan's three symbols plus already-lifted `resolve_prior_lane`, with the assertion message required to name `cnwy8g`/`9kmbr0`/`1f7xno` as the owner of the general case; E-03's "re-point the remaining" clause deleted; V-02 now REJECTS a guard that fires on all 53 as mis-scoped and V-03 REJECTS "zero remaining imports" as the pass criterion. Escalated: whether this plan or `runnerlayer` runs first, and whether an `Item-Dependencies` edge should be declared, since that changes another approved Set's queue. |
| PR-003 | HIGH | UNDER-SCOPE | E. testing; G. executability | `tests/test_resumedupe.py:661` (the two accepted shapes), `:314-318` (`_lane_commit_subjects` AST pin), 15 `OC.DISPOSITION_*` reads; `tests/test_orchestrator_probe_cache.py:1238` (exact `53`); `tests/test_runner_shared.py:3527`/`:3531`/`:3783`; `tests/test_review_lane_isolation.py:1155`; four `STILL_DOUBLE_DEFINED` tables | **THE FENCE OMITTED SEVEN FILES THE CHANGE MUST EDIT, AND ONE OF THEM FORBIDS E-03's RESULT.** `test_resumedupe.py` accepts E-03's three symbols only as a delegating stub or as a `_LIFTED_TO_RUNNER_SHARED` entry, so the lift fails it unless that table is extended in the same change. Three `getsource` pins and an exact-53 import baseline also break. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | All seven added to `Scope-Paths` (13 paths total). E-03 now names the `_LIFTED_TO_RUNNER_SHARED` obligation and the `_lane_commit_subjects` re-base; E-05 names the two `retry_deferred_integrations` pins; E-06 names all four pin tables with their line numbers and this plan's symbols in each, plus the differ-assertion and the import baseline. V-02..V-06 require each affected file run and pasted. |
| PR-004 | HIGH | UNDER-SCOPE | A. correctness; D. anti-regression | closure scan: 5 OC-only names for `classify_recovery_disposition`, 3 for `route_recovery_turn`; agy imports none of them; `runner_shared` defines none of them | **E-03's CLOSURE WAS NEVER MEASURED, SO THE "ALREADY ONE OBJECT" FRAMING HIDES A `NameError`.** The three stubs' real bodies reach `RecoveryDisposition`, three `DISPOSITION_*` constants, `_lane_commit_subjects` and the wrapper-form `save_state`. A naive body move fails at import in the two largest modules in the package. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 extended to scan the closure of all twelve and classify every free name (a) resolves in `runner_shared` / (b) equal-valued / (c) host-divergent / (d) module-level mutable, with (d) routed to E-07 and never lifted. E-03 now enumerates the five names, requires their disposition stated per name, and notes oc must keep re-exporting the constants for `test_resumedupe.py`'s 15 assertions. V-01 refuses a classification with no closure table. |
| PR-005 | HIGH | IN-SCOPE | G. executability (a self-contradicting partition) | Concern's list enumerates 6 names for "SEVEN"; `enforce_dependency_preflight` ratio 0.28 measured; the plan's own OQ-03 quotes "SETTLED ... KEEP, narrowed" | **THE "SEVEN NEAR-IDENTICAL" LIST NAMES SIX, AND THE UNNAMED SEVENTH IS THE ONE SYMBOL THE PLAN ELSEWHERE SAYS MUST STAY.** By subtraction the seventh is `enforce_dependency_preflight`, whose ratio contradicts "ratio >0.9" and whose fate the plan's own open question records as settled. So E-04's target set was never actually written down. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Concern corrected to name six and to state the seventh explicitly as a settled exception; F-9 added with the measurement; E-04 re-scoped to "the symbols E-01's closure scan cleared" with the realistic four named and E-01's table made authoritative over the prose; `enforce_dependency_preflight` routed to E-07 and added to the Deferred section with its ruling. |
| PR-006 | MEDIUM | IN-SCOPE | A. correctness (a reconciliation that regresses) | `i3d6ml` F-5 and F-13; measured diffs showing `item.get("configured_file", "")` vs `item[...]` and `dict(item)` vs `item`; oc hedges 9 of its own 13 call sites | **"RECONCILE TO THE OC VERSION" REINTRODUCES A `KeyError` AN EXECUTED PLAN DELIBERATELY AVOIDED.** Three of the differences E-04 would reconcile are agy's defensive forms on a resume path where a queue entry frozen by an older driver legitimately lacks `configured_file`. The oc-preferred ruling presupposes drift; this is a deliberate hedge. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now names all three sites, instructs that the defensive form be PRESERVED with the `i3d6ml` citation, and V-04 requires that preservation be shown rather than asserted. Recorded as F-14. |
| PR-007 | MEDIUM | IN-SCOPE | A. correctness (a premise that does not survive measurement) | normalized diffs: 1 differing line each; `aw agy` present only in the docstring (`code-tokens: []`) | **BOTH OF E-05's "GENUINE DIFFERENCES" ARE ONE LINE, AND ONE OF THEM IS A QUOTED TYPE ANNOTATION.** `retry_deferred_integrations` differs only by `dict(item)`; `_record_forced_stop` only by `stop: "runner_stop.StopNowForce"`. The `aw agy` label text `HostLabels.command` was to supply lives in a docstring, so V-05 demanded evidence of a code path that does not exist. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 rewritten: both premises corrected with the measured single-line diffs, the mechanism redirected to the established `INJECTED` wrapper shape (`818uru` OQ-02) with `HostLabels` allowed only with a named consumer, and an explicit instruction not to invent a field to satisfy the old wording. V-05 now REFUSES the impossible per-host-command-text evidence and requires the differing line be named instead. |
| PR-008 | MEDIUM | UNDER-SCOPE | E. testing (a false baseline would be recorded) | measured `32 failed, 7936 passed` with `AW_EXECUTION_ROLE=worker`; `7968 passed` with `env -u`; `89 passed` for one refusing file with the variable unset | **THE PINNED SUITE BASELINE MATCHES NEITHER MEASUREMENT AND IS UNREACHABLE IN A MANAGED WORKER LANE.** `7825 passed` against a measured 7936+32 or 7968. An executor gating on "bare and green" would record a false failure or "fix" 32 tests that refuse by design. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Both measurements written into Required tests and into a new conventions bullet, superseding the authored figure; the gate now requires the invocation FORM be stated and a like-for-like PRE-work baseline pasted beside the post-work run, gating on NO NEW failures; and an explicit instruction not to "fix" the role-refusal tests. |
| PR-009 | MEDIUM | UNDER-SCOPE | D. anti-regression (an exclusion that can be silently finished) | `tests/test_rununify_lift.py` module docstring; `runner_shared.py:106-113`; `8hx3g3` | **NOTHING WOULD HAVE STOPPED A LATER AGENT "FINISHING" THE EXCLUDED SYMBOLS.** The plan had no item that records why a symbol was left forked, and its E-06 asserted only the moved direction. `test_rununify_lift.py` exists because a one-directional suite lets someone delete a deliberate wrapper, watch every test pass, and reverse a ruling. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-07 added: the residue is a DELIVERABLE (symbol, blocker, citation, prerequisite) and must state that the parent's "only the five large functions remain" criterion is unmet and by how much. E-06 extended to assert the excluded set as STILL FORKED with its blocker cited, both directions, following `test_rununify_lift.py`. V-07 added and refuses an empty table unless the closure scan measured every blocker cleared. |
| PR-010 | MEDIUM | UNDER-SCOPE | G. executability (missing execution-contract elements) | the authored gate had the worktree, path-scoped-commit, never-push and finalize clauses only | The execution contract omitted the resolved-question list, the scope fence in DECLARE-and-JUSTIFY form, the shared-checkout `git diff --cached --name-only` re-verification (33 other pending plans declare these files), the invocation-form honesty requirement, and the CONDITIONAL finalize ownership (runner vs hand-executed). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All added, with the fence in the declare-and-justify form per the 2026-09-01 maintainer ruling (never "STOP and report" for a scope question) while keeping a legitimate stop for a genuinely unsafe condition, and with the finalize obligation unconditional but its owner conditional. Plus the explicit do-not-lift and do-not-delete-a-pin rules. |
| PR-011 | LOW | IN-SCOPE | G. executability (stale citations) | `agy_runipd.py:2473`/`:2483`/`:2495` measured (plan said `:2444`/`:2454`/`:2466`); the evasion comment at `:1638-1643` (plan said `:1609-1614`); `HostLabels` at `runner_shared.py:9384` (plan said `:8530`) | Every line citation in the plan is stale by 20 to 850 lines, including the three stub sites an executor navigates to first. Navigating by them reads the wrong code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All corrected in place with the authored value shown beside the measured one, so a reader comparing the plan against its parent's review can see which changed. |
| PR-012 | LOW | IN-SCOPE | A. correctness (a count that is the wrong unit) | AST walk: 8 `ImportFrom` statements, 53 names; the 9th grep hit at `:1638` is a comment | "NINE such imports" counts grep-visible lines, one of which is the explanatory comment, and conflates statements with bound names. The number an executor must reason about is 53 names across 8 statements, which is also what `test_orchestrator_probe_cache.py` pins. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected in the Goal, F-4 and OQ-03, with the per-statement breakdown recorded so the 44-vs-3 split that drives E-02's re-scope is visible rather than asserted. |
| PR-013 | LOW | UNDER-SCOPE | F. UX (an undisclosed operator-visible change) | oc `--raw ... (legacy behavior)`, `-vv ... diff hunks and diagnostics` vs agy `-vv ... raw tool parameters`; `tests/test_rununify_build_parser.py:373` asserts the bodies differ | `_add_output_mode_flags`'s difference is `--help` TEXT, so whichever body wins, one host's documented CLI output changes. The plan filed it under drift, which would absorb a user-visible change silently. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-17; E-04 now requires the change be disclosed as operator-visible with both hosts' strings, V-04 requires them pasted before and after, and E-06 requires the differ-assertion be re-based rather than deleted. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001's remedy needs either a design change to a live interrupt path or an admission that the parent's criterion is unmet. Decide, or escalate? | ESCALATE as OQ-04 with both routes priced, and fix in place everything that makes route (a) safe to execute. | (a) Silently re-scope to nine symbols and say nothing, rejected: the parent Set's completion criterion reads "the forked-symbol count has fallen from 34 to the five large functions alone", and a child that cannot deliver it must say so or the parent records a false pass. (b) Attempt the `8hx3g3` design change inside this plan, rejected: it is an OPEN backlog item with no approved design, `runner_shared`'s docstring forbids the naive form, the maintainer already declined a registration seam, and the failure mode is invisible (an unattended run pausing for a question nobody answers). | `8hx3g3` naming both symbols and calling the remedy a design act; `UnmovableSymbolTests`; `runner_shared.py:106-113`; measured `hasattr(runner_shared, "_LANE_PROMPT_DISABLED")` -> False | yes |
| D-2 | Is PR-001 a BLOCKER or a HIGH? | BLOCKER. The tempting completion path produces a SILENT invariant violation on an unattended path, which is the workflow's definition. | (a) HIGH, rejected: the harm is not a coverage gap but a working feature that stops working with no error, in exactly the unattended scenario the runners are built for. (b) MEDIUM, rejected outright: three in-tree places pin the constraint precisely because the failure is invisible. | workflow severity definitions; `runner_shared`'s own statement of the symptom; `8hx3g3`'s description of the same hazard from the other side | yes |
| D-3 | E-02's blanket guard collides with an approved Set. Narrow it myself, or escalate the whole thing? | NARROW IT MYSELF to a named ratchet (the guard is this plan's own deliverable and the 3-vs-44 split is a measurement, not a judgement), and escalate ONLY the sequencing question. | (a) Escalate the whole of E-02, rejected: the maintainer would be asked to adjudicate a question the AST already answers, since 44 names are pinned by an identity test whose docstring states its purpose. (b) Leave the blanket form and let the executor discover it, rejected: it fails 44 names on first run and the tempting recovery is deleting a pinned re-export, which `cnwy8g` records `ruff` already did once. (c) Edit `9kmbr0`/`1f7xno`, rejected: outside this review's ledger. | `_SHARED_NAMES` with `assertIs`; `cnwy8g`'s ruff record; `9kmbr0` and `1f7xno` both `approved` with `From-Backlog: cnwy8g` | yes |
| D-4 | E-05's `HostLabels` mechanism rests on a docstring token. Substitute the `INJECTED` wrapper myself, or ask? | STATE THE MEASUREMENT AND PREFER THE ESTABLISHED SHAPE, without mandating it: E-05 now says prefer `INJECTED`, allow `HostLabels` only with a named consumer, and forbid inventing a field to satisfy the old wording. | (a) Mandate `INJECTED`, rejected: the executor will have E-01's closure table and may find a case I did not, so fixing the mechanism from a review is over-reach. (b) Leave `HostLabels` as written, rejected: V-05 demanded evidence of a per-host command text that no code path produces, so the item could only be satisfied by fabricating it or by silently reinterpreting the requirement. | measured single-line diffs; `code-tokens: []` for both bodies; `818uru` OQ-02 quoted in `runner_shared.run_checked`'s docstring | yes |
| D-5 | Three of the four parent-Set line figures were unreproducible. Re-check this child's? | RE-MEASURED AND REPORTED: 488 reproduces EXACTLY under raw `ast.unparse` line count, and every one of the twelve length pairs matches. Recorded in the Concern with the metric named. | (a) Inherit the parent review's "line figures are indicative only" caveat, rejected: it would be false here, and telling an executor to distrust a figure that is correct wastes a re-measurement. (b) Say nothing, rejected: the parent explicitly instructs children's figures be re-derived, so silence would read as unchecked. | the pasted 12-row scan summing to 488; the parent's own instruction to re-derive | yes |
| D-6 | Should I raise the `runnerlayer` collision as a hazard, given AGENTS.md forbids presenting file overlap as a runtime hazard? | RAISE IT AS AN AUTHORITY AND SEQUENCING question, explicitly NOT as a concurrency hazard, and say so in OQ-05. | (a) Warn that the two Sets cannot run concurrently, rejected and specifically forbidden: the runner isolates each item's worktree and merges through a revalidation gate, so file overlap is settled. (b) Omit it, rejected: this is not overlap, it is two plans instructed to perform the SAME edit under different guards, one of which (`1f7xno`) has a fence and a freeze test this plan lacks. | AGENTS.md runner-ownership paragraph; `1f7xno`'s `Scope-Paths` declaring `test_runner_layering.py` and `test_runner_refork_guard.py`, which this plan does not | yes |
| D-7 | Verdict and readiness, given two OPEN blockers? | `REVIEWED - OPEN QUESTIONS`, readiness `no-go`, `Status: reviewed`. | (a) `APPROVE WITH REVISIONS APPLIED` / `go-pending-approval`, rejected: two findings are left OPEN at BLOCKER, which the readiness table names as a genuine not-ready condition; claiming otherwise would greenwash a plan whose scope statement is unachievable as written. (b) `REJECT - NEEDS REPLAN`, rejected: the three-shape decomposition is sound, the 488-line measurement reproduces exactly, and both blockers are bounded (a scope decision and a sequencing decision), not a broken approach. | workflow verdict/readiness tables; PR-001 and PR-002 `Decision: OPEN`; `aw ipd lint` now refusing on OQ-04/OQ-05 by design | yes |

### Escalation of the irreversible decisions

None of this round's seven decisions is `Reversible: no`. Every one is undone by editing this plan before it
executes: nothing here publishes an interface, migrates data, deletes anything, or produces a released
artifact. The two that touch other artifacts are escalations rather than edits (OQ-04 and OQ-05 ask; they do
not change `8hx3g3`, `9kmbr0` or `1f7xno`), and they are reversible in the safe direction: leaving both
blocking means the plan cannot execute until a human answers, so a wrong call costs one round trip rather
than a broken interrupt path. Stated explicitly rather than left blank.

### Honest limits of this review

- I did NOT execute the lift, so every claim about what a lift breaks is derived from READING the assertions
  plus running them green in their current state. I ran `test_resumedupe.py -k never_holds_a_second`
  (1 passed), `test_orchestrator_probe_cache.py -k import` (2 passed) and the runner-import guard, which
  proves they are live and currently satisfied; it does not prove the exact failure text a lift produces.
- The residue count in E-07 is "at least three". E-01's closure scan may find more, and I say so in the item
  rather than pretending my scan is final: mine covered the twelve named symbols' direct free names, not
  transitive reachability through `runner_shared` back into a host.
- I did not evaluate whether the parent Set's ordering (this plan after `li44r9`) survives OQ-04's answer.
  If `8hx3g3` is graduated first, the Set gains a child and the Order numbering is the maintainer's call.
- The `aw agy` docstring finding means one of this plan's stated motivations for `HostLabels` evaporates.
  I did not re-examine whether Order 03's descriptor work still needs what this plan was to supply; that is
  `xdvglg`'s review, not this one.
