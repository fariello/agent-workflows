# Review findings: plan entv1d

- Subject-Id: entv1d
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `c6c573a4` in a lane worktree. Structural preflight `aw ipd lint --phase author`
reported `conforming` with ZERO diagnostics; after revision `--phase review-finalize` also reports
`conforming` with ZERO diagnostics. No pre-review snapshot was owed: the plan was committed and
unmodified, and the lane-input copy under `.aw/state/lane-inputs/rev-42/` is byte-identical (verified by
`diff`). NO PRODUCTION FILE, TEST, OR SPEC WAS MODIFIED by this review; every measurement was a read or
an in-process probe that reimplemented the candidate fix in a local function rather than patching the
package. Bare suite at review HEAD: `3246 passed, 2 skipped, 3 warnings in 47.24s`. The F-12 fence
(eight modules) measured `197 passed in 20.00s`.

THIS IS AN UNUSUALLY WELL MEASURED PLAN AND I RE-DROVE EVERY LOAD-BEARING CLAIM. All of the following
reproduce at review HEAD. F-01: all three members of `EXECUTE_OR_RETIRED_REPORTING_SUCCESS_STATES`
(`approved`, `executed`, `retired`) with `integration_signal: suite-failed` measure
`integration_was_refused=True`, project onto `EXIT_SUCCESS_TOKEN`, and return `rc=0`. F-03: the same
probe with `substantially-complete` projects onto `substantially-complete` and returns `rc=1`, so the
plan is right that the fix must not be written at the status bar and right that the naive reading of the
backlog would put it there. F-07: a review item with `review_integrated: False` measures
`integration_was_refused=False` and `rc=0`, and `review_integration_was_refused` has exactly one
consumer (`format_stranded_work_section`); I additionally measured `item_reached_success=True` for that
shape, which the plan does not state and which is what makes the corrected narrow siting sufficient to
catch it. F-08: `integrate_retired_lane`'s call site does carry `and integration.earned`, `RETIRED_STATUS`
is `'retired'` and is a member of the execute-or-retired bar, so the production path the plan describes
is real. F-09: both `oc_runipd.run_queue` and `agy_runipd.run_queue` end in the identical
`runner_stop.deliberate_stop_exit_code(runner_shared.exit_code_statuses(state["queue"]), ...)` pair, so
neither host needs editing. F-10: `evaluate_unverifiable_admission` has exactly one call site, in
`runner_shared`, and its result is discarded with a comment saying so. F-11: the existing exit-code tests
cover exactly the five cases the plan lists and none asserts a stranded run's code. F-02: the backlog's
`25kzda:1057` offset has indeed rotted (the table is at `:1406-1415`) while every quoted string survives
verbatim, including row `4`'s `UNRECONCILED CONFLICT, recorded 2026-09-05`. F-04: the exit-`1` row's
three clauses are as quoted and a stranded item matches none. F-05: `docs/cli-output-contract.md`
Section 3 says "uniform three-state exit classification across all verbs" and the Exit Code Parity rule
says the embedded field "MUST equal the process exit code (`0`, `1`, `2`)", both verbatim. F-06: all
eight `run_cli.py` constants exist with the values the finding implies.

I ALSO DROVE THE PROPOSED FIX RATHER THAN REASONING ABOUT IT, which is what surfaced PR-501. A probe
implementation (composed predicate plus projection change, written locally, package untouched) turns
every one of E-05's cases the right colour: all three success-bar statuses with a refusing signal go to
`rc=1`, the review shape goes to `rc=1`, both earned signals stay `rc=0`, a missing `integration_signal`
key stays `rc=0`, a gate-released refusal stays `rc=0`, a mixed queue goes to `rc=1`, and a deliberate
stop over `queued` plus landed stays `rc=0`. So the approach is sound and the plan's central claim is
demonstrated, not merely argued.

PR-501 IS THE FINDING THAT CHANGES THE CODE, and it came out of probing the two candidate arm
placements side by side rather than from reading. E-03 specified a separate stranded arm placed BEFORE
the `item_reached_success` arm. That arm fires on ANY item carrying a refusing signal, including items
whose status is ALREADY a failure, so four real shapes stop reporting what happened:
`integration-blocked`, `failed`, `fail-gate` and `substantially-complete` each project onto their own
status today and would project onto the stranded token instead. That directly contradicts this
function's own docstring ("Every other non-success status is passed through unchanged, so it still reads
as a failure and a reader of a debugger frame still sees the real disposition"), and it is the
projection-layer twin of a hazard `render_stream.py` already documents at the headline ladder in almost
these words: "Testing the signal BEFORE the status would RELABEL that existing outcome to `STRANDED`,
which is a regression dressed as the feature." The plan CITES that very hazard as its reason for not
touching the ladder and then reproduces its shape one layer down. The fix is to site the test INSIDE the
success arm, so only an item that would otherwise have been called a success can lose it. I measured
both variants across all nine shapes: every exit code is IDENTICAL, so the narrow siting costs nothing
and only preserves information. This is a MEDIUM rather than a HIGH because no exit code is wrong either
way, but it would have degraded diagnosability on exactly the runs an operator debugs.

TWO SMALLER CORRECTIONS CAME FROM THE SAME PROBING. PR-502: a `queued` item can legitimately carry a
stale `integration_signal` from a refused earlier attempt, which is a stronger reason for the `queued`
arm's precedence than the plan gives ("a queued item never ran, so it cannot have stranded work" is not
quite true of the RECORD, only of the work). Measured: it projects onto `queued` under both placements
and a stop over it exits `0`, so the behavior is correct and now pinned. PR-503: the plan justifies its
module siting partly by citing
`tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`,
quoting `runner_shared.py`'s own import comment. That file DOES NOT EXIST; `git log --diff-filter=D`
names `19313eed` "test: trim test suite from 9,136 to under 2,000 tests" as the deletion. The plan's
subsidiary claim that `render_stream.py` "imports zero in-package modules" is also false: an AST scan
finds three (`lifecycle_style`, `run_selection_policy`, `term`). The CONCLUSION is nonetheless correct
and on firmer ground: `runner_shared` imports `render_stream` at module level, so a module-level reverse
import is a genuine cycle. Worth recording because a stale citation in a live source comment will
mislead the next reader, and because a plan resting an argument on a deleted guard is one edit away from
being wrong.

WHAT I DELIBERATELY DID NOT FLAG. The plan's refusal to reorder the outcome-word ladder is correct and
well reasoned, and its carrier `aaa2xx` genuinely exists as an open release-blocking item. Its refusal
to wire `run_evidence.aggregate_run_exit` is correct (that would change every run's classification and
land in the row-`4` conflict). Its refusal to touch the row-`4` note is correct, and I verified the note
already binds the reconciliation duty to a future change, so no new item is owed. Its E-01 STOP condition
is right and must not be removed: a premise that no longer reproduces is a genuinely unsafe condition to
proceed from, which the 2026-09-01 ruling preserves as distinct from a scope question. The choice of
exit `1` over a new code is settled by evidence the plan cites accurately. I checked whether `queued`,
`skip not-run`, `plan reviewed`, and malformed entries could regress under the fix: none does.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-501 | MEDIUM | IN-SCOPE | A (correctness) / D (anti-regression) | plan E-03 as authored ("Place the stranded arm AFTER the `queued` arm and BEFORE the `item_reached_success` arm"); `runner_shared.exit_code_statuses` docstring ("Every other non-success status is passed through unchanged ... a reader of a debugger frame still sees the real disposition"); `render_stream.py`'s ladder comment ("a regression dressed as the feature") | THE SPECIFIED ARM PLACEMENT SWALLOWS EVERY ALREADY-FAILING ITEM'S REAL DISPOSITION. An arm before the success arm fires on any refusing signal, so `integration-blocked`, `failed`, `fail-gate` and `substantially-complete` (each measured projecting onto itself today) would all project onto the stranded token, breaking the function's documented pass-through promise and reproducing one layer down the exact relabel hazard the plan cites as its reason for not touching the headline ladder. Both placements were driven across all nine shapes and every exit code is IDENTICAL, so the information loss buys nothing | C:Low; U:Low; S:Low; F:Medium (no exit code is wrong either way, but the projected token is what a debugger frame and any future reader see, and it would be wrong on exactly the failing runs an operator investigates); Overall:Medium | FIXED | E-03 rewritten to site the test INSIDE the success arm (`TOKEN if work_did_not_land(item) else EXIT_SUCCESS_TOKEN`), with the measurement, the docstring promise, and the ladder precedent quoted as the reason, and the `queued` precedence restated on its corrected basis. E-03's Expected outcome now requires the four verbatim projections. E-05 gains case (i) as the GUARD, requiring each of the four to assert its own status verbatim so a future edit moving the test above the arm turns red. V-03 now demands the four projections as explicit negative evidence plus a written statement of the siting. Proposed-changes and Scope-check lines swept. New F-13 |
| PR-502 | LOW | IN-SCOPE | A (correctness) / E (testing) | measured: `{"action":"execute","status":"queued","integration_signal":"suite-failed"}` projects onto `queued` under both placements; a stop over it plus a landed item returns `0` | THE `queued` ARM'S PRECEDENCE PROTECTS A REAL SHAPE THE PLAN MISDESCRIBES. E-03 justified it with "a queued item never ran, so it cannot have stranded work", which is true of the WORK but not of the RECORD: a requeued item retains `integration_signal` from its refused attempt. So the precedence is load-bearing for a reachable case, not merely a tidiness rule, and nothing in the authored test plan pinned it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03's comment requirement now states the corrected reason (a stale signal on a requeued item). E-05 gains case (h) pinning that a `queued` item carrying a refusing signal still projects onto `queued` and still exits `0` under a stop, so a future edit lifting the test above the `queued` arm breaks `c4gd2h` A1/A4 loudly. V-03 requires the projection. New F-14 |
| PR-503 | LOW | IN-SCOPE | F (honest documentation) / C (architecture) | `grep -rn test_no_new_module_level_first_party_import_in_runner_shared tests/` -> no match; `git log --diff-filter=D` -> `19313eed` "test: trim test suite from 9,136 to under 2,000 tests"; AST scan of `render_stream.py` module-level first-party imports -> three (`lifecycle_style`, `run_selection_policy`, `term`) | THE PLAN'S MODULE-SITING ARGUMENT RESTS ON A DELETED GUARD AND A FALSE COUNT. E-02 says `render_stream.py` "imports zero in-package modules" (it imports three) and the conventions section cites a test file that no longer exists, quoting a stale comment still live in `runner_shared.py`. The CONCLUSION is correct on stronger grounds (`runner_shared` imports `render_stream` at module level, so the reverse edge is a real cycle), so this is a documentation defect rather than a design error, but an argument resting on a deleted guard is one edit from being wrong | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02's siting paragraph corrected to rest on the genuine import cycle, with the false count retracted and an explicit instruction not to cite the deleted guard. Conventions bullet corrected. New F-15. The stale comment in `runner_shared.py` is recorded but NOT edited: added as a Deferred row with a `- Carrier-Declined:` explaining that the conclusion is safe, the defect is a dead citation, and editing it would widen the diff in the largest file in the package for no failing test |
| PR-504 | LOW | UNDER-SCOPE | G (execution contract) | plan gate as authored: "finalize through the tooled path", with no owner condition and no scope fence | THE LIFECYCLE INSTRUCTION HAS NO CONDITIONAL OWNER AND THE GATE HAS NO SCOPE FENCE. Under a managed lane the runner owns begin/finalize and a worker-role process is refused with `AW-LIFECYCLE-ROLE-001` (enforced inside the finalize transaction itself, so `aw ipd set executed` is refused too); an unconditional instruction spends an agent turn on an expected refusal. Separately, the gate declared no negative constraints, so finalize reconciliation had only `Scope-Paths` to work from and the plan's many load-bearing "do not touch" decisions lived only in item prose | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now separates the unconditional finalize obligation from the conditional owner, with the enforcement site named and both a hand-rolled `git mv` and a hand-edited `- Status:` forbidden. A SCOPE FENCE was added as a DECLARATION (not a stop directive, per the 2026-09-01 ruling) naming eleven negative constraints, each traceable to a finding, and stating that a necessary out-of-scope edit is made and then justified with `--scope-reason` |
| PR-505 | LOW | UNDER-SCOPE | G / durable-carrier convention | OQ-01 and all four Deferred rows as authored: carrier named in PROSE only; `ipd_schema.CARRIER_FIELD` / `DEFERRED_SUBFIELD_RE` match the typed `- Carrier:` field structurally and never prose | EVERY CARRIER REFERENCE WAS PROSE-ONLY, SO THE TOOLING CANNOT SEE ANY OF THEM. OQ-01 says "FILED, so the deferral has a durable carrier rather than living only in this plan's prose: backlog `aaa2xx`" while doing exactly that: the reference is in the rationale text, not in the typed field the schema documents as "matched STRUCTURALLY (`- Carrier: <id6>`), never by prose". The other three Deferred rows carried neither a `- Carrier:` nor a `- Carrier-Declined:` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 gains `- Carrier: aaa2xx` (verified to resolve to an `open`, `Blocks-Release: next` item) and a note saying why the typed field is required. The Deferred section gains a typed field on every row: `- Carrier: aaa2xx` on the headline row, and a reasoned `- Carrier-Declined:` on the aggregator row, the table-reconciliation row (declined because the spec's own row-`4` note already binds the duty, verified verbatim), the `aw attention --check` row (declined as not-a-defect, verified by running it), and the new F-15 row |
| PR-506 | LOW | UNDER-SCOPE | G (approval gate) | plan gate as authored: two sentences, `Cohesion rationale: not required`, no statement of what approval means | NO STATEMENT OF WHAT A HUMAN WOULD BE APPROVING, and this plan needs one more than most: its whole point is to CHANGE A PROCESS EXIT CODE, so approving it accepts that automation currently reading `0` from a stranded run will begin reading `1` and may newly fail. That consequence appeared nowhere in the gate | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a one-paragraph "WHAT A HUMAN WOULD BE APPROVING" naming the four files, stating the automation-visible consequence plainly as the thing to weigh, citing the contract that already defines `1` as "domain findings", identifying the reversed siting judgement as the contestable engineering call and its reversibility, and naming both things the plan deliberately leaves unfixed with their carriers |
| PR-507 | LOW | IN-SCOPE | E (testing) / F (honest documentation) | plan E-01 as authored (one contrast status); V-01 as authored (exit codes only, no projected tokens) | E-01'S BASELINE WAS TOO NARROW TO PROTECT THE CORRECTED FIX. It recorded one contrast status and only exit codes, so it could not establish the verbatim-projection baseline that PR-501's narrow siting must preserve, and V-01 could not detect a regression in it. The authored counts also invited reading the baseline as the bar rather than re-deriving | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now probes FOUR contrast statuses and records each one's PROJECTED TOKEN beside its exit code, plus the review shape's `item_reached_success=True` (the fact that makes the narrow siting sufficient, which the plan never stated). V-01 requires all of it and requires stating whether the result matched the review's re-measurement at `c6c573a4`. E-05's count updated from seven cases to nine throughout, and V-05 now requires case (i) to be shown failing under the rejected placement, then restored |

No finding was DEFERRED and none was left OPEN, so no escalation to a `- Blocking: yes` question is
owed (`check.review-finding-unescalated` satisfied vacuously). No BLOCKER and no HIGH was found: the
plan's goal, its defect characterization, its mechanism choice, and its refusal boundaries are all
correct, and the one substantive finding is a placement correction inside an item nobody has executed.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-03's specified arm placement loses information. Correct the placement, or accept it and document the loss? | Correct it to a test INSIDE the success arm, and add E-05 case (i) as a guard | Accepting the arm and documenting the loss, rejected because the loss is gratuitous: both placements were measured to give identical exit codes, so nothing is traded away by narrowing, and the function's own docstring makes a promise the wide placement breaks. Leaving the correction as prose without a test, rejected because the plan's own review precedent (`4po0sc` PR-602, in this repository) established that a placement argument nothing guards is exactly the regression a suite misses | driven both variants across nine shapes: exit codes identical, projections differ on four real statuses; `exit_code_statuses` docstring's pass-through promise; `render_stream.py`'s ladder comment naming the same hazard "a regression dressed as the feature" | yes |
| D-2 | The guard the plan cites for its module siting does not exist. Reopen the module-siting question, or re-base the argument? | Re-base the argument on the genuine import cycle and keep the siting | Reopening, rejected because the cycle is decisive on its own: `runner_shared` imports `render_stream` at module level, so the reverse module-level import is a real `ImportError`-class cycle regardless of any test. Filing an item to restore the deleted guard, rejected as out of this plan's concern and not obviously wanted (the trim deleted it deliberately as a structure pin, which GUIDING_PRINCIPLES P16 disfavours) | AST scans of both modules; `grep` finding no such test; `git log --diff-filter=D` naming `19313eed` | yes |
| D-3 | `runner_shared.py`'s live import comment cites the deleted guard. Fix it here, or leave it? | Leave it, record it in F-15, and decline it with a reason in the Deferred section | Fixing it here, rejected because the comment's CONCLUSION is correct (the cycle is real), so nothing is unsafe, and editing the largest file in the package for a comment no failing test touches widens the diff and the review surface of an exit-code change. Filing a backlog item, rejected because a stale citation inside a correct comment is not a defect a user can reach, and the record in F-15 plus the declined row is where a future reader will find it | verified the comment's conclusion independently by AST scan; the plan's own scope discipline (one projection change, one predicate, one test, one spec row) | yes |
| D-4 | Should a backlog item be filed for the two exit-code tables' disagreement above `4`? | No; the obligation is already carried by the spec's own row-`4` note | Filing one, rejected because it would duplicate a mandate the contract already binds to a future change: the row states the conflict, dates it, and says "Whoever binds the abort classes to exit codes MUST reconcile these two tables explicitly and update both". This plan also provably stays at `1` where the tables agree, so it neither worsens nor touches the conflict | row `4` of `25kzda`'s "Run exit codes" table, quoted verbatim at review; `run_cli.py`'s eight exit constants confirming the divergence the note describes | yes |
| D-5 | E-03 and E-05 each carry a density advisory after this review's additions. Split either? | Keep both whole, recording the rationale in the gate | Splitting E-05's nine cases across modules, rejected because they are one deliverable over one verification surface and scattering one contract across files is what P8 forbids. Splitting E-03's siting rationale from its edit, rejected because the rationale IS the edit's justification and separating them is how the wide placement gets reintroduced | the rubric's density diagnostics applied per item: one concern each, one test-surface each, one focused pass each; the advisories fire on rationale and case enumeration, not on multiple deliverables | yes |

No `Reversible: no` decision was taken, so no escalation is owed under the irreversible-decision rule.
