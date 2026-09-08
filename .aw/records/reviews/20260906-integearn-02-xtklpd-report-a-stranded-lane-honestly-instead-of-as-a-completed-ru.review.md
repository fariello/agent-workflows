# Review: report a stranded lane honestly instead of as a completed run (child xtklpd, Set integearn)

- Subject-Id: xtklpd
- Subject-Type: ipd
- Reviewed-At: 2026-09-08
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `8dc4e0bc`. Structural preflight `aw ipd lint --phase author` conformed BEFORE semantic
review (exit 0, `outcome: clean`), and `--phase review-finalize` conformed after the revisions, now
additionally reporting `[blocking]` because a blocking question was added.

DISCLOSURE, TWICE OVER. The same agent identity authored this Set, so this is a self-review and every
load-bearing claim was RE-RUN rather than recalled. Separately and more importantly: THIS REVIEWER
CAUSED ONE OF THE TWO SUITE FAILURES recorded below. The immediately preceding `/plan-review` on sibling
`32ij2j` gave it a legitimate `REJECT - NEEDS REPLAN`, and `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`
asserts that NO pending plan carries a negative verdict. So the assertion now fails on `32ij2j`. That is
disclosed rather than quietly absorbed into a baseline number, because a reviewer who moves the baseline
and then reports the baseline is reporting their own footprint.

WHAT THE PLAN GETS RIGHT, and most of it does. The DIAGNOSIS is correct and re-verified at every point
that matters: the outcome really is computed from per-item status with no integration term, with
`substantially-complete` inside the COMPLETED tuple; `COMPLETED` really is green; the incident really
printed COMPLETED at 100 percent for a run whose entire product sat on a branch; `reconcile_disposition`
really does silently override an agent's `executed` claim; and the event log really does go silent at the
integration fork (re-counted: exactly ten events, none naming an integration decision). The insistence
that the anti-fabrication override is CORRECT and only its silence is the defect is exactly the right
call, and the refusal to reclassify `substantially-complete` is likewise right.

THE BEST NEWS IS THAT THE PLAN UNDERSTATES ITS OWN POSITION. It says the integration verdict is
DISCARDED. Measured on the incident's own `state.json`, it is not: `attempt["integration_signal"]` is
`"suite-failed"`, `attempt["integration_detail"]` holds the entire verdict reason, `item["integration_signal"]`
mirrors it, and `item["preserved_branch"]` is `"aw/lane/mm6wuz_attempt3"`. Both drivers write all of
them. The field the plan inspected, `attempt["integration"]`, is a DIFFERENT one, written only on the
integrate-ATTEMPTED path and legitimately absent when integration was never attempted. Meanwhile `grep`
finds ZERO readers of `integration_signal` in either `render_stream.py` or `run_viewer.py`. So the
verdict, its reason, AND the recovery route were all durably recorded at the time, and the whole defect
is a missing READER. That makes this plan smaller, cheaper, and stronger than authored: no new
persistence, no cross-module coupling, no filesystem access.

AND THAT MATTERS BECAUSE THE AUTHORED DATA SOURCE CANNOT REPRODUCE THIS PLAN'S OWN INCIDENT. E-04
proposed deriving the outcome from `run_viewer.audit_step_artifact`, praised as "already computed". It IS
already computed, and it reads the LIVE FILESYSTEM: it globs the plans tree via `find_artifact_file` and
parses the plan's `- Status:`. Auditing the incident's `mm6wuz` TODAY returns `expected=executed
actual=executed location_mismatch=False`, because the hand recovery moved the plan. So re-rendering that
run's summary under the authored design would report COMPLETED again. A run summary whose verdict about a
FINISHED run changes as the tree moves underneath it is a worse defect than the one being fixed, and it
would make the plan's own E-06 fixture unbuildable without either fabricating a tree or pinning to live
plan files, which is precisely the anti-pattern behind this suite's other long-standing failure.

TWO FURTHER MEASURED OBSTACLES TO THE AUDIT ROUTE, either of which alone would force a redesign.
`audit_step_artifact` takes a `StepSummary` dataclass of 21 fields while the renderer holds raw
`state["queue"]` dicts, so consuming it means constructing `StepSummary` objects inside a renderer. And
`render_run_summary_table`'s own docstring declares it deliberately "a PURE renderer: it must not import
a runner", which is why it reads `state["run_order"]` rather than calling `queue_sort_key`. Importing
`run_viewer` to reach the filesystem is that same invariant broken in a new direction. Deriving from run
state satisfies both constraints for free, which is why the recommendation is (a) and why OQ-03, whose
premise was "audit or reimplement", is superseded: there was a third option it did not consider.

ONE HAZARD THE PLAN DID NOT NAME AND THE NEW LABEL MUST NOT FALL INTO. The gate records a verdict only
when it is RELEVANT (`self_finalize` on, not a review action, disposition in the success set), so for
every other item the field is legitimately absent. If absent were read as stranded, every
`--no-self-finalize` run and every review sweep would report the new label, which is the pessimistic
failure the plan's own gate warns against. Absent must mean not-applicable.

THREE SMALLER CORRECTIONS. `format_discrepancy_table` DOES NOT EXIST; the real renderer is
`format_artifact_audit_summary`, and an executor searching for the cited name would find nothing to
consume. `yocdq4`, the `integrate` verb the summary would point at, is a BACKLOG id and not a plan in an
"integpath Set", so the summary must offer only the preserved branch. And E-04's precedence list omitted
the two branches that come FIRST: `exit_reason`, which short-circuits everything, and INTERRUPTED. Every
line citation has also drifted, by roughly 73 lines in `render_stream.py` and 78 in `oc_runipd.py`, with
the substance correct at each new coordinate.

WHY OPEN QUESTIONS AND NOT REPLAN. Unlike its sibling, this plan's problem is one DATA SOURCE, not its
foundation. E-02, E-03, the diagnosis, and the whole reporting-honesty goal survive unchanged and were
re-verified; the fix as redirected is strictly SIMPLER than authored. So the plan was hardened in place
and gated on a single question, rather than sent back.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-023 | BLOCKER | IN-SCOPE | A. correctness; C. architecture; E. testing | `audit_step_artifact(StepSummary(id6="mm6wuz", status="substantially-complete"), Path("."))` -> `expected=executed actual=executed location_mismatch=False`; `run_viewer.py:465`, `find_artifact_file:439`; `render_stream.py:1656` docstring ("must not import a runner"); `StepSummary` 21 fields vs raw queue dicts | **THE AUTHORED DATA SOURCE WOULD REWRITE HISTORY AND CANNOT REPRODUCE THIS PLAN'S OWN INCIDENT.** E-04 derives the outcome from a filesystem audit, so once a stranded lane is recovered the same run re-renders as COMPLETED, which is the exact defect the plan exists to remove. It also makes E-06's fixture unbuildable without pinning to live plan files (the anti-pattern behind this suite's other failure), requires constructing a 21-field `StepSummary` inside a renderer, and breaks the renderer's documented purity invariant by importing a runner | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | OPEN | Escalated as OQ-04 with `- Blocking: yes` and `- Finding: PR-023`, owner maintainer, three costed options with (a) recommended (derive from run state). OQ-03 marked SUPERSEDED with its still-valid one-source-of-truth reasoning preserved. E-04 rewritten to derive from state with the measurement stated; E-06's fixture respecified as a synthesized state dict and given a new HISTORY-PROPERTY assertion (a since-moved plan must not change a stored run's verdict); V-04 requires stating which option was implemented and, for (a), proving no `run_viewer` import or filesystem access was added. New F-11. NOT FIXED: it decides whether a finished run's verdict may change later, which is a contract question |
| PR-024 | HIGH | IN-SCOPE | Evidence accuracy; F. KISS | `.aw/records/runs/run-20260907T010730Z-3199043/state.json`: `attempt["integration_signal"]="suite-failed"`, `attempt["integration_detail"]` full reason, `item["integration_signal"]="suite-failed"`, `item["preserved_branch"]="aw/lane/mm6wuz_attempt3"`; `oc_runipd.py:6475-6477`; `agy_runipd.py:3742-3744`; `grep -rn integration_signal agent_workflows/render_stream.py agent_workflows/run_viewer.py` -> no hits | **THE VERDICT IS NOT DISCARDED; IT IS ALREADY PERSISTED AND NOTHING READS IT.** F-5 and E-01 rest on `attempt["integration"]` being `None`, but that is a different field written only when integration was ATTEMPTED (`:6636`). The verdict, its reason and the recovery route are all already durable on both paths and on both hosts. The real gap is a missing READER, which makes the plan smaller and removes the need for any new persistence | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-5 WITHDRAWN as false; new F-10 with the measurements. E-01 shrunk from "persist the verdict" to "expose a machine-readable `earned` boolean (or a shared predicate) so the consumer need not hardcode a signal-name list", with an explicit instruction not to rename `integration_signal` (written by both drivers, present in 135 run records). V-01 now requires pasting the already-existing fields FIRST, so the corrected premise is on the record. Concern paragraph and two conventions bullets rewritten |
| PR-025 | MEDIUM | UNDER-SCOPE | A. correctness | `oc_runipd.py:6450-6453` (`integration_gate_relevant = self_finalize and not is_review and disposition in (...)`), `:6474` (fields written only under that guard) | **AN ABSENT VERDICT MUST NOT READ AS STRANDED, AND THE PLAN NEVER SAID SO.** The gate records a verdict only when it is relevant, so the field is legitimately absent for `--no-self-finalize` runs, review actions, and any non-success disposition. A consumer treating absent as not-earned would label every review sweep stranded, which is exactly the pessimistic failure the plan's own gate paragraph forbids | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | The gate paragraph gains an explicit "absent means not-applicable, fall through to today's behavior" rule with the guard cited; E-04's expected outcome and E-06's precedence cases pin it |
| PR-026 | MEDIUM | IN-SCOPE | G. executability | `render_stream.py:1857-1881`: `exit_reason` -> INTERRUPTED -> FAILED -> BLOCKED -> COMPLETED -> PARTIAL -> QUEUED; color expression keys on the outcome STRING with a cyan fallthrough | **THE PRECEDENCE LIST OMITTED THE TWO BRANCHES THAT COME FIRST.** E-04 said the order is FAILED, BLOCKED, COMPLETED, PARTIAL, QUEUED, missing `exit_reason` (which short-circuits everything and carries STOPPED/wind-down) and INTERRUPTED. An executor placing the new label per the plan's list could mask a STOPPED or INTERRUPTED run. Also unstated: `integration-blocked` and `merge-conflict` ALREADY yield FAILED, so the new label is specifically for integration never ATTEMPTED, and an unknown label silently takes the CYAN color branch | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 states the full measured order, the already-FAILED statuses, and the color fallthrough with a warning not to put `FAIL` in the label unintentionally; E-06 requires three precedence cases and V-04 four; new F-12 |
| PR-027 | MEDIUM | IN-SCOPE | Evidence accuracy; G. executability | `grep -rn format_discrepancy_table agent_workflows/ tests/` -> no hits; the real renderer is `run_viewer.format_artifact_audit_summary:1337`; `grep -rn '^- Id: yocdq4' .aw/records/plans/` -> empty (it is `backlog/graduated/...-yocdq4-...`) | **TWO NAMED THINGS DO NOT EXIST AS CITED.** `format_discrepancy_table` appears nowhere in the package (twice cited, including in the re-locate-by-symbol instruction), so an executor would search for a consumer that is not there. And `yocdq4`, described as a plan in the "integpath Set" that the summary will point at, is a BACKLOG id with no plan, so a summary naming the `integrate` verb would advertise something that does not exist | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected to `format_artifact_audit_summary` in F-4, the conventions and the re-locate instruction, with an explicit note that the old name does not exist; the Deferred entry and E-04 now say the summary must offer only the preserved branch. New F-13 |
| PR-028 | MEDIUM | IN-SCOPE | E. testing; honest reporting | bare `python3 -m pytest` at `8dc4e0bc`: `2 failed, 5650 passed, 3 skipped, 2 xfailed`; plan records `1 failed, 5612 passed`; `plan_readiness.newest_verdict(32ij2j)` -> `negative`; `tests/test_plan_readiness.py:789-798` | **THE BASELINE MOVED AND GREW A SECOND FAILURE, WHICH THIS REVIEW ITSELF CAUSED.** `test_plan_readiness::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today` asserts no pending plan carries a negative verdict, and sibling `32ij2j` now does after its `REJECT - NEEDS REPLAN` verdict from this same reviewer. It is the same test-design flaw as the long-standing `RealRepositorySets` failure: an assertion pinned to the live mutable plan corpus. Neither failure belongs to this plan | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both measurements recorded with both failing NODE IDS named and attributed, the causation disclosed, and instruction to trust neither total and compare node ids; the gate's BASELINE HONESTY paragraph updated to name both. New F-15. The test flaw itself is NOT fixed here (out of fence, and it is a pre-existing pattern worth its own item) |
| PR-029 | LOW | IN-SCOPE | Evidence accuracy | `grep -n` per symbol at `8dc4e0bc`: outcome expr `:1869-1877` (plan `:1795-1803`), green `:1891-1893` (`:1817-1819`), `reconcile_disposition` `:5892-5902` (`:5814-5822`), `EXECUTION_SUCCESS_STATES` `:328` (`:321`) | Every line citation has drifted, by roughly 73 lines in `render_stream.py` and 78 in `oc_runipd.py`. Substance verified correct at each new coordinate, and the plan already instructs re-location by symbol, so this is presentational | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Load-bearing citations updated in the Concern, E-03, E-04, the conventions and F-2/F-3/F-9; F-14 records the drift; the re-locate instruction strengthened |
| PR-030 | LOW | UNDER-SCOPE | C. architecture | `grep -rn render_run_summary_table`: `oc_runipd.py:7267`, `:8124`, `:8170`; `agy_runipd.py:4489`, `:5078`, `:5124` | The plan treats the renderer as a single shared surface, which is true for the OUTCOME LOGIC (one function, so E-04 is one edit) but understates that it has SIX call sites across both drivers, so any signature change is a six-site edit. E-02's event emission is likewise per-driver and must be done twice, which the plan did not say | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A conventions bullet records the six call sites and the one-edit-for-logic distinction; E-02 now explicitly requires emission on BOTH hosts with the agy mirror cited; E-05 requires the event asserted on both drivers |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Is this REPLAN like its sibling, or repairable with a blocking question? | REPAIRABLE. Harden in place and gate on ONE question about E-04's data source | REPLAN, rejected because unlike `32ij2j` the foundation holds: the diagnosis re-verified at every point, E-02 and E-03 are sound, and the redirected fix is strictly SIMPLER than authored rather than differently scoped. Revisions-applied with no blocking question, rejected because the data-source choice decides whether a finished run's verdict may change later, which is a contract question | re-verified outcome expression, green color, silent override, ten-event log; measured that state already carries the verdict so the fix shrinks | yes |
| D-2 | Where does the summary's verdict come from? | RECOMMEND the run's own state; ESCALATE the decision as OQ-04 | Keep the filesystem audit as authored, rejected on measurement: `mm6wuz` audits clean TODAY, so the plan's own incident would re-render as COMPLETED. Use both (state for the verdict, audit for a tree-drift note), recorded as option (c) since it is more honest but doubles the mechanisms. Decide (a) myself and rewrite E-04 silently, rejected because it changes what a run summary MEANS over time | `audit_step_artifact` on `mm6wuz` -> `location_mismatch=False`; `find_artifact_file` globs the tree; `render_stream.py:1656` purity docstring; `StepSummary` shape; ESCALATED as OQ-04 with `- Finding: PR-023`, maintainer told 2026-09-08 | no |
| D-3 | E-01 was authored to persist a verdict that is already persisted. Delete the item or repurpose it? | REPURPOSE to the one genuinely missing piece: a machine-readable `earned` boolean or an equivalent shared predicate | Delete E-01 entirely, rejected because without it E-04's consumer must hardcode a list of `INTEGRATION_EARNED_BY_*`/`INTEGRATION_REFUSED_*` signal names, which drifts the moment a new refusal reason is added. Leave it as authored, rejected because it would re-add fields that exist and risk renaming `integration_signal`, which both drivers write and 135 run records carry | measured all four fields present in the incident state and written by both drivers; zero readers in the two reporting modules; `:6636` shows `attempt["integration"]` is the attempted-path field | yes |
| D-4 | Should an ABSENT integration verdict be treated as stranded? | NO. Absent means not-applicable; fall through to today's behavior | Treat absent as not-earned (fail-closed by analogy to the gate itself), rejected because the field is absent by DESIGN for `--no-self-finalize` runs, review actions and non-success dispositions, so every review sweep would report the new label, which is the pessimistic failure the plan's own gate paragraph forbids. Leave it unstated, rejected because an executor reaching for fail-closed instincts would plausibly choose wrong | `oc_runipd.py:6450-6453` guard and `:6474` conditional write | yes |
| D-5 | This review's own prior verdict broke a suite test. Absorb it into the baseline or disclose it? | DISCLOSE it explicitly, in the plan, in this record, and in the final report, and do NOT fix the test here | Silently record `2 failed` as the new baseline, rejected because a reviewer who moves the baseline and then reports the baseline is reporting their own footprint as ambient noise. Fix the test as a courtesy, rejected as outside this plan's fence and a pre-existing test-design pattern deserving its own item | `plan_readiness.newest_verdict(32ij2j)` -> `negative` after commit `8dc4e0bc`; `tests/test_plan_readiness.py:789-798` asserts an empty refused list over the live pending corpus | yes |
