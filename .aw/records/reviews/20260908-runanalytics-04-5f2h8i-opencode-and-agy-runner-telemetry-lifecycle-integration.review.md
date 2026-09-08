# Review: OpenCode and Agy runner telemetry lifecycle integration (child 5f2h8i, Set runanalytics)

- Subject-Id: 5f2h8i
- Subject-Type: ipd
- Reviewed-At: 2026-09-08
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `d9a32cdd`. Structural preflight `aw ipd lint --phase author` conformed BEFORE semantic
review (exit 0, `outcome: clean`), and `--phase review-finalize` conformed after the revisions. The
linter earned its keep mid-review: an eighth V-item covering a plan-wide suite obligation tripped
`IPD-I302`, correctly, since a validation leaf must validate a specific E-item; the obligation moved into
V-07 and the required-tests section instead.

METHOD. This is the child that edits both host drivers and amends an APPROVED spec, so the first question
was not "is the instrumentation well placed" but "what already guards these two files, and what does that
spec's own test suite do when the spec changes". Both answers were load-bearing and neither was in the
plan. Every claim below was established by reading the guards and the contract test rather than by
reasoning about what such tests probably assert.

WHAT THE PLAN GETS RIGHT. The central discipline is correct and hard: telemetry must be observational,
best-effort, and incapable of turning working runs into failures, and the plan says so in its Goal, its
spec-sync section and its gate. Insisting the two hosts stay semantically aligned to prevent
host-specific observability drift is exactly the right worry for this codebase. The Findings section's
reasoning about per-invocation identity is genuinely sharp: it correctly sees that multiple executor
attempts, an independent verifier invocation, and a later resume in the same run directory mean identity
cannot be inferred from a run-level snapshot. Refusing to let telemetry become the authority for cost and
token totals, and refusing to copy prompts, child stdout or session JSONL into telemetry, are both right.
The instruction to test through injected collectors to avoid timing flakes shows the author had actually
thought about how driver tests fail.

THE BLOCKER IS THAT ONE CONVENTION SENTENCE INSTRUCTED THE EXECUTOR TO DO A FORBIDDEN THING. "Runner
shutdown and stop modules centralize signal behavior; cleanup must be registered there when necessary
rather than relying only on happy-path `finally` blocks." The first clause is true. The second reads
naturally as "register a signal handler in the driver", and that is prohibited by FOUR separate executed
plans' guard tests, each asserting `signal.signal(` appears in NEITHER driver
(`tests/test_lane_allocation_idempotent.py:406`, `tests/test_runner_stop.py:652`,
`tests/test_runner_stop_level3.py:792`, `tests/test_runner_stop_level4.py:785`), reserving that
registration for `runstop` Phase 5 (`71vjbn`). The repository has already litigated this precise question:
`oc_runipd.py:1587-1610` is a twenty-four-line comment recording a prior plan being REFUSED permission to
install those handlers, and it does not merely cite the guards, it explains that the designs are
"incompatible, not merely double-registered" and that seizing the registration would have deleted a
measured handler deadlock fix and a roughly 50 percent lost-escalation race fix. Spec `c4gd2h` R5
independently forbids divergent per-level cleanup, with A9 requiring a structural check that exactly one
cleanup implementation exists. So an executor following the authored convention would have gone four
suites red and re-broken two races that a previous plan had measured and fixed. What makes this the worst
kind of defect is that the instruction sounds like diligence: it is telling the executor to be thorough
about cleanup, and thoroughness is precisely what the guards forbid here. E-05 now routes teardown through
the funnels that already exist, permits a `runner_shutdown.py` edit ONLY to teach the existing routine to
stop a registered sampler, and V-05 demands both a grep and the four guards passing unmodified.

SECOND, THE SPEC IS BOUND TO THE CODE IN BOTH DIRECTIONS BY A TEST, AND THE PLAN'S AMENDMENT ORDER WOULD
HAVE BROKEN THE SUITE. `tests/test_run_flag_surface.py` reads spec `25kzda` as a FILE (`SPEC_PATH`,
`:43-50`), extracts Section 2.1's grammar block, and asserts both that every spec-declared flag is either
registered or explicitly excluded (`:136`) and that no registered flag is absent from the spec (`:150`).
E-03-as-authored said to amend the spec "in the same execution before implementation depends on the new
artifact contract", which is the wrong order if the amendment declares a flag. This is settled precedent
rather than my inference: the spec's own Workflow history for 2026-09-07 records Section 2.1 being
deliberately NOT amended, because "the two ladder flags plan `51vw4y` needs cannot be declared before they
are registered, since `tests/test_run_flag_surface.py` binds spec and code bidirectionally, so that
amendment lands inside `51vw4y`'s own execution as one atomic change". Worth noting what this does NOT
mean: amending an approved spec here is legitimate and the file is properly declared in `Scope-Paths`, so
the pre-run announcement will name it. The constraint is only about atomicity. OQ-01 additionally
defaults to adding no flag at all, since Order 03's own OQ-01 already resolved telemetry configuration to
a `project.json` key with a machine-local override rather than a CLI surface, and a second control surface
for one setting is the duplication three siblings in this Set were already corrected for.

THIRD, THE EXECUTION ID AS SPECIFIED COULD NOT SATISFY THE PLAN'S OWN REQUIREMENT. The Findings section
demands identity not be inferable "from a single run-level snapshot", which is right. But measured,
`attempt_no = len(item.get("attempts", [])) + 1` (`oc_runipd.py:5917`) reads a list that is PERSISTED in
`state.json` (appended at `:5947`), so it does not reset on resume. That is correct for attempt numbering
and it means a composite of `(position, id6, attempt_no, phase)` is STABLE across a resume and would
collide with the pre-resume invocation's file, silently overwriting or appending to it. Separately,
executor and verifier are distinguished today only by a `suffix="verify"` string handed to
`attempt_log_path` (`:4939-4947`), so phase must be an explicit field rather than inferred from a
filename, which is the kind of derived-from-presentation coupling that breaks the moment a filename
changes. E-02 and OQ-02 now own this, with a mutation check requiring the resume test be shown capable of
failing.

FOURTH, THE GOAL HARDCODED A RUN-RELATIVE PATH INSIDE A SET WHOSE ORDER 01 EXISTS TO DELETE THAT LITERAL.
`runner_shared.state_root` (`:188-189`) returns `repo / ".aw" / "records" / "runs"` consulting no
authority, while the records root is relocatable by `records_backend` of `repository`, `companion` or
`home` (`project_context.py:783-790`). Order 01's review established that `state_root` IS the defect and
that the literal is built at six live sites. Composing `<run>/telemetry/...` by hand would add a seventh
and would file telemetry in the wrong place for any non-repository backend. The plan also never stated
that telemetry is NOT inside Order 01's reserved `analytics/` tree, which an executor could reasonably
assume given the Set's name; it is a per-run artifact, and that is now explicit.

THE SMALLEST CORRECTION WITH THE LARGEST EFFECT ON EFFORT is that "wrap all OpenCode subprocess invocation
boundaries" overstates the target by six sites. Measured, there is exactly ONE agent-launch `Popen` per
host (`oc_runipd.py:5526` inside `run_opencode:5304`; `agy_runipd.py:2889` inside `run_agy_turn:2768`),
each already wrapped in `runner_shutdown.track_child`, each with exactly two callers (executor and
verifier). The other `subprocess.run` calls in `oc_runipd` (`:604`, `:923`, `:1011`, `:5041`, `:5262`,
`:5275`) are version probes and helpers; instrumenting them would emit telemetry for work nobody wants
measured and would inflate the event volume Order 03's overhead budget is sized against. The work is
smaller and more precisely located than the plan implied.

ON NON-INTERFERENCE, WHICH IS THE PLAN'S OWN HEADLINE CLAIM. It appeared as one clause inside a bundled
item and required no CONTROL run. "The instrumented run still succeeded" and "the instrumented run
succeeded for the same reasons" are different claims, and only the second is non-interference; without a
paired uninstrumented control, a validation could pass while a state transition had quietly changed.
E-06 is now its own item and V-06 requires the paired control for each injected fault.

ON SIZING. Three E-items, and E-02-as-authored named four independent deliverables (agy integration,
shutdown wiring, resume identity, sampler non-orphaning) across unrelated test surfaces, while E-03
bundled an approved-spec amendment with an entire non-interference matrix. Eight of the Set's eleven plans
carry exactly three items, which is a template rather than eleven judgements, and the count-based lint
conformed both before and after the split into seven. This is now the third sibling split for the same
reason (`bzz5e6` 3->6, `lhccjf` 3->8), which is worth saying plainly to the maintainer: the pattern is in
the authoring pipeline, not in any one plan.

WHY APPROVE WITH REVISIONS RATHER THAN OPEN QUESTIONS. Nothing here needed a human. Both unmade decisions
were answerable from shipped code, guard tests and the spec's own recorded history, and are recorded as
D-1 and D-2. The four authority corrections are settled repository facts. No BLOCKER or unfixed HIGH
remains. One thing a human should notice beyond this child: this plan is the fourth in a row whose gate
carried no execution contract and whose backticks were escaped, so the remaining seven unreviewed
siblings will almost certainly need the same two mechanical fixes.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-053 | BLOCKER | IN-SCOPE | A. correctness; C. architecture; D. anti-regression | `tests/test_lane_allocation_idempotent.py:406`; `tests/test_runner_stop.py:652`; `tests/test_runner_stop_level3.py:792`; `tests/test_runner_stop_level4.py:785`; `oc_runipd.py:1587-1610`; spec `c4gd2h` R5/A9 | **THE CONVENTIONS SECTION INSTRUCTED A CHANGE FOUR EXECUTED PLANS' GUARDS FORBID.** "Cleanup must be registered there ... rather than relying only on happy-path `finally` blocks" reads as "register a signal handler", and four guards assert `signal.signal(` appears in NEITHER driver, reserving SIGINT/SIGTERM for `runstop` Phase 5 (`71vjbn`). A prior plan was refused exactly this; the record states the designs are "incompatible, not merely double-registered" and that seizing registration would have deleted a measured handler deadlock fix and a ~50% lost-escalation race fix. Spec `c4gd2h` R5 forbids divergent cleanup, A9 requiring exactly one implementation. The instruction sounds like diligence, which is what makes it dangerous: an executor being thorough goes four suites red and re-breaks two fixed races | C:Low; U:Low; S:Medium; F:High; Overall:Medium | FIXED | The convention is REPLACED with the measured prohibition and the available funnels (`clean_shutdown`'s 7 call sites; `except KeyboardInterrupt`, which needs no registration). E-05 is its own item requiring teardown through those funnels, permitting a `runner_shutdown.py` edit ONLY to have the EXISTING routine stop a registered sampler, never a new path; V-05 requires a grep over both drivers plus the four guards passing UNMODIFIED; the fence and a gate stop condition repeat it. New F-1 |
| PR-054 | HIGH | IN-SCOPE | Spec synchronization; E. testing; G. executability | `tests/test_run_flag_surface.py:43-50`, `:136`, `:150`; spec `25kzda` Workflow history 2026-09-07 | **THE SPEC IS BOUND TO THE CODE BIDIRECTIONALLY BY A CONTRACT TEST AND THE PLAN'S AMENDMENT ORDER WOULD HAVE BROKEN THE SUITE.** That test reads the spec FILE, extracts Section 2.1's grammar, and fails both when the spec declares a flag the code neither registers nor explicitly excludes and on the converse. E-03 said to amend the spec "in the same execution BEFORE implementation", so a flag-declaring amendment turns the suite red until registration lands. The spec's own history records Section 2.1 being deliberately left unamended for exactly this reason | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-07 states the binding, the two failing assertions and the recorded precedent, and requires any flag land ATOMICALLY with its registration; the spec-sync section is rewritten with the same; OQ-01 defaults to NO flag, since Order 03's OQ-01 already resolved telemetry config to a `project.json` key rather than a CLI surface; V-07 requires the test passing and an explicit statement of whether 2.1 was touched. New F-2 |
| PR-055 | HIGH | IN-SCOPE | A. correctness (uniqueness); D. anti-regression | `oc_runipd.py:5917` (`len(attempts) + 1`), `:5947` (persisted); `attempt_log_path:4939-4947` (`suffix="verify"`) | **THE EXECUTION ID COULD NOT SATISFY THE PLAN'S OWN UNIQUENESS REQUIREMENT.** `attempt_no` derives from a list PERSISTED in `state.json`, so it does not reset on resume, making `(position, id6, attempt_no, phase)` STABLE across a resume and colliding with the pre-resume invocation, which the plan's Findings section explicitly forbids. Phase is today distinguished only by a `suffix="verify"` string on the log path, so inferring it from a filename couples identity to a presentation detail | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | New E-02 owns invocation identity, requires a per-invocation component and an explicit phase field, and requires the uniqueness argument be RECORDED; OQ-02 states the measurement and rejects reusing the session-log naming; V-02 requires two ids across a simulated resume shown DIFFERENT plus a mutation check proving the test can fail. New F-3 |
| PR-056 | HIGH | IN-SCOPE | C. architecture; F. KISS | `runner_shared.state_root:188-189`; `project_context.py:783-790`; Order 01 (`xbwq8n`) review record | **THE GOAL HARDCODED A RUN PATH INSIDE A SET WHOSE ORDER 01 EXISTS TO REMOVE THAT LITERAL.** `state_root` consults no authority while the records root is relocatable via `records_backend`; Order 01's review established `state_root` IS the defect and the literal is built at six live sites. Composing the telemetry path by hand adds a seventh and misplaces telemetry for any non-repository backend. The plan also never said telemetry is NOT in Order 01's reserved `analytics/` tree, which the Set's name invites an executor to assume | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Goal and E-01 require resolution THROUGH Order 01's resolver plus a named constant, state the six-site measurement, and state that telemetry is a per-run artifact outside `analytics/`; V-01 requires a non-`repository` backend tested (a repository-only assertion passes vacuously) and a grep proving no new literal. New F-4 |
| PR-057 | MEDIUM | OVER-SCOPE | C. operability; E. testing | `oc_runipd.py:5526` (the one agent `Popen`) versus `:604`, `:923`, `:1011`, `:5041`, `:5262`, `:5275`; `agy_runipd.py:2889`; callers at `:6147`/`:6392` and `:3437`/`:3657` | **"WRAP ALL OPENCODE SUBPROCESS INVOCATION BOUNDARIES" OVERSTATED THE TARGET BY SIX SITES.** There is exactly one agent-launch `Popen` per host with two callers each; the rest are version probes and helpers. Instrumenting them would emit telemetry for work nobody wants measured and inflate the event volume Order 03's overhead budget is sized against | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and E-04 name the exact `Popen` sites and both callers per host, and E-03 states explicitly that the six `subprocess.run` sites are NOT instrumented; a conventions bullet records the measurement; V-03 requires proof they were left alone |
| PR-058 | MEDIUM | UNDER-SCOPE | G. right-sizing and conceptual density | `grep -c '^- \[ \] E-'` across the Set -> eight of eleven plans at exactly 3; lint conforming BOTH before and after the split | **THE E-ITEMS WERE MECHANICALLY SIZED.** E-02 named four independent deliverables across unrelated test surfaces; E-03 bundled an approved-spec amendment with an entire non-interference matrix. The count-based lint cannot see this. Third sibling with the identical finding (`bzz5e6` 3->6, `lhccjf` 3->8) | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into SEVEN items across four groups (seam, identity, two host wirings, sampler teardown, non-interference, spec); `Highest E allocated` 03 -> 07; V-01..V-07 rewritten to bijection; a right-sizing note records the measurement; cohesion rationale restated to say it justifies one PLAN, not one ITEM |
| PR-059 | MEDIUM | UNDER-SCOPE | G. executability | plan gate as authored (two sentences); sibling review records for `xbwq8n`, `bzz5e6`, `lhccjf` | **THE GATE CARRIED NO EXECUTION CONTRACT**: no scope fence, no path-scoped-commit / never-push rule, no paste-actual-output honesty rule, no lifecycle-move instruction, no re-locate-by-symbol warning. Fourth sibling in a row, so it is a Set-wide authoring pattern rather than an oversight here | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Full contract added: approval requirement, the load-bearing `executed:lhccjf` dependency and the two dependents; a fence naming eight measured prohibitions with the finalize `--scope-reason`/`--scope-ack` mechanics; path-scoped commit with re-verify-after-failed-hook and the concurrent-checkout warning; the honesty rule; re-locate-by-symbol; and THREE stop conditions (no signal handler, no second cleanup routine, no weakening a guard test) |
| PR-060 | MEDIUM | UNDER-SCOPE | D. anti-regression; E. testing | plan's non-interference clause as authored; V-01-as-authored | **THE PLAN'S HEADLINE CLAIM HAD NO CONTROL RUN.** "Never let telemetry failure alter the work result" was one clause inside a bundled item, and V-01 asked only that lifecycle tests show "without changed run outcomes". "The run still succeeded" and "the run succeeded for the same reasons" are different claims; without a paired uninstrumented control a validation could pass while a state transition had quietly changed | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New E-06 owns non-interference by FAULT INJECTION (probe raises, timeout, unwritable dir, append failure, constructor raises, close raises); V-06 requires each instrumented result pasted BESIDE a paired uninstrumented control showing exit status, item statuses, merge decision and cleanup report identical; the required-tests section states the reason |
| PR-061 | LOW | UNDER-SCOPE | C. architecture (no re-fork) | AST walk: `agy_runipd` imports 47 names from `oc_runipd`; `tests/test_runner_refork_guard.py` (`test_no_runner_redefines_an_already_extracted_symbol`, `test_every_runner_attribute_is_the_owning_modules_object`) | The plan required the hosts stay "semantically aligned" without naming the shared-definition discipline or the guard test enforcing it. A second telemetry implementation inside the agy driver would satisfy a reviewer reading for parity of BEHAVIOR while forking the code, which is exactly what that guard exists to catch | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 requires ONE seam in `runner_shared` reached by both hosts, never through the other host's driver, citing the 47-name surface and the guard; E-04 requires parity asserted as a TEST rather than by inspection, with the measured host-parameterized-text carve-out stated so it is not read as demanding byte-identical strings; V-01 requires object identity plus an unchanged import count |
| PR-062 | LOW | IN-SCOPE | Evidence accuracy; Presentation | bare `python3 -m pytest` at `d9a32cdd` -> `2 failed, 5655 passed, 3 skipped, 2 xfailed`; `grep -c '\\`'` -> 18 before the fix | Two mechanical gaps: no measured baseline despite requiring a bare suite run, so an executor meeting two pre-existing failures could not tell them from its own; and 18 escaped backtick pairs rendering as literal backslashes, after Order 01's six, Order 02's four and Order 03's ten from the same authoring pipeline | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline recorded with both node ids named and attributed as pre-existing, plus the compare-node-ids-not-totals rule and the empty-delta criterion; the six guard suites most likely to catch a mistake here are named for explicit running; all 18 backticks unescaped and verified zero remaining |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How does the sampler stop on signal paths, given the plan said to register cleanup in the shutdown modules? | Through the EXISTING funnels only: `clean_shutdown` and the `except KeyboardInterrupt` path. A `runner_shutdown.py` edit may only teach the EXISTING routine to stop a registered sampler | Register `signal.signal` handlers as the convention implied, rejected on measurement: four executed plans' guards assert that call appears in neither driver, `runstop` Phase 5 (`71vjbn`) owns the registration, and `oc_runipd.py:1587-1610` records the designs as incompatible with a measured handler deadlock and a ~50% lost-escalation race at stake. Add a second cleanup routine for telemetry, rejected because spec `c4gd2h` R5 forbids divergent cleanup and A9 requires a structural check that exactly one exists. Rely only on `finally`, rejected because the plan is right that a signal path would then orphan the sampler; the answer is the existing funnel, not a new one | the four guard assertions; the refusal comment; spec `c4gd2h` R5/A9; `clean_shutdown`'s 7 call sites | yes |
| D-2 | Does the spec amendment add a run flag? | DEFAULT TO NO FLAG; if one is added, it lands atomically with its registration | Amend Section 2.1 spec-first as E-03 said, rejected because `tests/test_run_flag_surface.py` binds spec and code bidirectionally and the suite goes red until registration lands, exactly as the spec's own 2026-09-07 history records for `51vw4y`. Add a `--no-telemetry` flag, rejected as the default because Order 03's OQ-01 already resolved telemetry configuration to a `project.json` key with a machine-local override, so a CLI surface would be a second control for one setting. Skip the amendment, rejected because the run-artifact inventory genuinely changes and an undocumented artifact is what the spec exists to prevent | `test_run_flag_surface.py:43-50`, `:136`, `:150`; spec history 2026-09-07; Order 03 OQ-01 | yes |
| D-3 | How is an execution id made unique when `attempt_no` does not reset on resume? | Require a per-invocation component and an explicit phase field, with the uniqueness argument recorded and mutation-checked | Key on `(position, id6, attempt_no, phase)`, rejected on measurement: `attempts` is persisted in `state.json`, so that tuple is stable across a resume and collides with the earlier invocation, defeating the plan's own stated requirement. Infer phase from the `suffix="verify"` log-path convention, rejected because it couples identity to a presentation detail that changes independently. Leave it to the executor, rejected because the collision is invisible until a resumed run overwrites a prior file | `oc_runipd.py:5917` and `:5947`; `attempt_log_path:4939-4947` | yes |
| D-4 | Which subprocess boundaries get instrumented? | The ONE agent-launch `Popen` per host, at both callers (executor and verifier); not the version/helper `subprocess.run` sites | Wrap all subprocess boundaries as the Proposed-changes section said, rejected on measurement: six of the sites in `oc_runipd` are version probes and helpers, and instrumenting them emits telemetry for work nobody wants measured while inflating the event volume Order 03's overhead budget is sized against. Wrap only the executor, rejected because the verifier is a distinct invocation with its own model and the plan's own Findings require per-phase identity | traced every subprocess site in both drivers and their callers | yes |
| D-5 | Split the three E-items, or accept them since the lint passes? | SPLIT into seven | Accept the authored three, rejected because E-02 named four independent deliverables across unrelated test surfaces and the controlling workflow states that a passing count-based size lint does NOT clear right-sizing. Split into separate child PLANS, rejected because the cohesion argument is genuine: parity between the two hosts is the whole point, so both wirings must ship together. Keep the spec amendment inside the test item, rejected because it is the one item with a hard external constraint (the bidirectional contract test) and it deserves its own verification | eight of eleven Set plans at exactly 3 items; lint conforming before and after; plan-review's right-sizing diagnostics answering YES for E-02 | yes |
