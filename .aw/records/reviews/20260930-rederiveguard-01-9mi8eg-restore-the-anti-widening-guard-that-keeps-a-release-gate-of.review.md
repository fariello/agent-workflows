# Review findings: plan 9mi8eg

- Subject-Id: 9mi8eg
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-R01 (HIGH, fixed), PR-R02 (HIGH, fixed), PR-R03 (MEDIUM, fixed), PR-R04 (MEDIUM, fixed), PR-R05 (MEDIUM, fixed), PR-R06 (LOW, fixed), PR-R07 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `a14f96d58`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` with ZERO findings before semantic review, and
`--phase review-finalize --agent` reports `clean` with zero findings after revision. The plan is
`- Kind: child`, so the `IPD-S407` orchestrator row check does not apply.

THE PLAN'S CENTRAL CLAIM IS TRUE AND I RE-MEASURED IT RATHER THAN TRUSTING IT. The guard really is gone
(`git ls-files --error-unmatch tests/test_records_only_lane_rederive.py` errors; `19313eed` shows
`1 file changed, 679 deletions(-)`), the carve-out really has no test caller
(`rg 'REDERIVABLE_FRONT_MATTER_KEYS|classify_records_only_front_matter_conflict|rederive_front_matter|REDERIVE_SHAPE' tests/`
returns nothing), and the widening really is silent. I went one step further than the plan did and
ISOLATED the mechanism, which is the sharpest available evidence: with the allow-list widened to include
`Blocks-Release`, `rederive_front_matter` handed a positively classified verdict carrying
`added_keys=(("Blocks-Release","next"),)` WROTE `- Blocks-Release: next` onto executed-plan text and raised
nothing; with the shipped constant the identical call raises
`DriverError: refusing to write non-allow-listed front-matter key 'Blocks-Release' (allow-list: ['Priority', 'Work-Kind'])`.
So the control exists, is reachable, and is simply uncalled. That strengthens the plan's case rather than
weakening it, and it is recorded into F-03 so the executor inherits the isolated probe instead of only the
whole-suite one.

F-05's P16 compliance claim also verifies: the deleted file contains no `inspect`, no `ast`, no `getsource`
and no production-source `read_text()`, and it drove real `git` subprocesses. Restoring it does not
reintroduce a code-pinning test, so the plan's premise for restoring rather than rewriting is sound.

THREE MATERIAL DEFECTS, ALL OF THE SAME CLASS: the plan asserts facts about the tree that have drifted or
were never checked, and in two cases an executor following it literally would have been forced into either a
false claim or an unexplained stall.

PR-R01 is the one that would have cost a pass. E-01 instructs the executor to recover the deleted file and
"re-verify against CURRENT signatures", but nowhere states that the recovered file DOES NOT PASS. I restored
`19313eed^`'s copy into a scratch path and ran it: `1 failed, 37 passed in 0.88s`. The failure is
`test_the_E02_refusal_CHANGES_NO_CONTRACT_only_the_message`, asserting
`runner_shared.INTEGRATION_REFUSAL_CONFLICT == "merge-refused"`; commit `6b94a4d9d` ("statusvocab: rename
the terminal status vocabulary so a label names its refusing authority", 2026-09-25) renamed that constant
to `"fail-merge"` ONE DAY after the trim deleted the file, so the recovered arm encodes a pre-rename
spelling. This matters beyond the inconvenience: the plan's own Scope check granted a standing licence to
DROP "an arm that no longer applies", and the single arm that fails is exactly the kind an executor under
that licence would delete, destroying a property that is still true (a non-re-derived conflict still returns
the terminal refusal kind). Recorded as F-10 with the remedy, E-01 now names the arm and forbids satisfying
the item by deleting it, the fix is to compare against `runner_shared.INTEGRATION_REFUSAL_CONFLICT` itself
rather than re-hardcoding a spelling that can rename again, and the Scope check's drop licence is narrowed to
"the PROPERTY no longer exists", not "a literal moved". The same measurement also establishes the good news
the plan should have carried: the other 37 assertions pass against current source unmodified, so the
restoration is feasible as written.

PR-R02 set an unreachable validation bar. V-05 demanded a bare suite run "demonstrating the whole suite is
green". The suite is NOT green in this checkout: on an UNMODIFIED tree, bare `python3 -m pytest` reports
`1 failed, 3414 passed, 2 skipped, 3 warnings`. The failure is
`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a known,
filed, time-dependent defect owned by backlog `fnb8pl` (`open`, `bug`, `Blocks-Release: next`): `backlog.py`
stamps history from local `date.today()` while `status_set.py` uses UTC, so for part of each day the two
writers disagree, and the observed diff is exactly the `2026-09-30` versus `2026-10-01` one that item
describes. An executor holding V-05's bar would have had to claim a green suite falsely, stall on an
unrelated defect, or wander out of scope to fix someone else's bug. Recorded as F-11; V-05 and the
validation list now demand a DELTA (no new failing test id, pass count rises by the restored file's
contribution), name the permitted pre-existing failure, and forbid fixing it.

PR-R03 is the live-count rule applied to the plan's own evidence. The plan pins `3284 passed` as a baseline
and V-05 told the executor to "compare the count against" it. Collected at review: `3417/3624 tests
collected (207 deselected)`, bare run `3414 passed`. The 130-test gap is ordinary growth from other lanes,
and an executor comparing against `3284` would read it as a regression. The plan's own conventions section
cites the re-derivation rule for live-artifact counts and then violated it with a suite-wide pass count,
which is the textbook case. Recorded as F-12; the `Concern`, F-03 and V-05 now carry the authoring figure as
CONTEXT ONLY and require re-derivation.

TWO CORRECTIONS THAT REMOVE A FALSE CHOICE, AND TWO SMALLER FIXES.

PR-R04: E-02 parametrized the writer control over FOUR keys (`Status`, `Readiness`, `Approval`,
`Blocks-Release`) while E-05 had to reconcile a source comment naming FIVE (adding `Item-Dependencies`),
which guaranteed E-05 would find a gap and left it choosing between narrowing a claim that is actually TRUE
and leaving the comment overstating. I measured all five at the writer: every one raises
`refusing to write non-allow-listed front-matter key '<key>'` under the shipped constant. E-02 now covers
five, so E-05's expected result is that the comment is already true and needs no edit. The fifth case costs
one list entry and preserves a true claim rather than weakening it.

PR-R05: E-05 was framed as "correct the stale citation", which presumes an edit. After PR-R04 the honest
framing is a VERIFICATION whose expected outcome is no change, and that has a scope consequence the plan did
not state: `agent_workflows/runner_shared.py` is then a DECLARED-BUT-UNMODIFIED path at finalize (E-04's and
V-02's edits being reverted by design), which `aw ipd finalize` requires a `--scope-ack` for. The Scope check
now says so and supplies the reason, so the executor does not read a clean diff on a declared path as a
defect.

PR-R06: E-04's RED probe was unscoped. Under the widened constant a BARE suite run also carries F-11's
unrelated failure, so RED and GREEN would each show a failure and the evidence would not establish what
objected. E-04 and V-04 now narrow the probe to the restored file and name the arm that must fail
(the `Blocks-Release` writer case), which I measured to be the one the widening breaks.

PR-R07: the gate's lifecycle instruction told the executor unconditionally to "transition the plan to
`executed` through the tooled lifecycle (`aw ipd set`)". Under `aw oc run` / `aw agy run` the RUNNER owns
that transition, so an executor obeying this would duplicate or race it. Rewritten to the house form: the
transition is unconditionally OWED, its OWNER is conditional, and a hand execution invokes
`aw ipd finalize` while a runner-driven one does not.

ONE THING I CHECKED AND DID NOT FLAG, recorded because rejecting a correct citation is the costlier error.
The plan declines `- From-Spec: 25kzda` with a stated reason (the field names the spec a plan GRADUATED
from, and this plan graduated from backlog `mgz3f1`). I re-ran the nudge: `aw check plans` exits 1 with 61
findings, 34 of them `check.plan-spec-link-missing`, this plan among them, and the exit code is 1 with or
without this plan. The advisory is `info`, the reasoning is correct on the field's definition in `AGENTS.md`,
and 33 other pending plans sit in the same position. Judgement upheld; the paragraph is updated with the
re-measured numbers so the next reader sees current figures rather than authoring-time ones.

I also verified F-09's claim about spec `25kzda` Section 2.1b (present, dated 2026-09-27, implemented via
`merge_conflict_sendback` / `MERGE_CONFLICT_RETRY_COUNT_KEY`, covered by `tests/test_merge_conflict_sendback.py`
whose `DriverConflictSendbackTests` really does carry cases a through e), and F-08's non-collision claim
(the three sibling restore items name different files; no other pending plan touches this path). Both hold.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-R01 | HIGH | UNDER-SCOPE | E. Testing and verification | plan E-01 and Scope check; `agent_workflows/runner_shared.py:9613` symbol `INTEGRATION_REFUSAL_CONFLICT`; commit `6b94a4d9d` | The recovered file DOES NOT PASS as recovered (`1 failed, 37 passed`): `test_the_E02_refusal_CHANGES_NO_CONTRACT_only_the_message` asserts `INTEGRATION_REFUSAL_CONFLICT == "merge-refused"`, renamed to `"fail-merge"` on 2026-09-25, one day after the trim. The plan did not know this, and its standing licence to drop "an arm that no longer applies" made deleting this still-true property the path of least resistance. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-10 naming the arm, the commit, and the remedy. E-01 now requires repairing the literal (compare against the constant itself) and forbids satisfying the item by deletion; V-01 requires the arm pasted as passing with its assertion line. Scope check's drop licence narrowed to a lost PROPERTY, not a moved literal. |
| PR-R02 | HIGH | IN-SCOPE | E. Testing and verification | plan V-05 "the whole suite is green"; measured bare run `1 failed, 3414 passed, 2 skipped`; `.aw/records/backlog/open/20260930-fnb8pl-01-fnb8pl-unify-the-history-date-clock-across-both-backlog-s.backlog.md` | The validation bar was unreachable: the suite is not green on an unmodified tree here. The pre-existing failure is `test_release_exempt_setter_roundtrip_and_parity`, a filed time-dependent local-versus-UTC clock defect owned by `fnb8pl`. An executor would have had to claim a false green, stall, or fix an out-of-scope bug. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-11. V-05 and the validation list now require a DELTA (no new failing id; pass count rises by the restored file's contribution), name the permitted pre-existing failure by id, and forbid fixing it. |
| PR-R03 | MEDIUM | IN-SCOPE | G. Plan executability (live-artifact criteria) | plan F-03 `3284 passed` and V-05 "compare the count against the 3284-passed baseline"; measured `3417/3624 collected`, `3414 passed` | A suite-wide pass count is a LIVE population, and the authored figure had drifted by 130 tests. V-05 instructed a comparison against it, so ordinary growth would read as regression. The plan's own conventions section states the re-derivation rule and then broke it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-12. `Concern`, F-03 and V-05 now carry `3284` as context only and require re-derivation at execution; V-05 demands a baseline run measured on the tree rather than any authored absolute. |
| PR-R04 | MEDIUM | UNDER-SCOPE | D. Anti-regression and domain invariants | plan E-02 (four keys) versus E-05 (five keys); `runner_shared.REDERIVABLE_FRONT_MATTER_KEYS` comment; measured writer refusal for all five | E-02 covered four keys at the writer while E-05 had to reconcile a comment naming five, guaranteeing a gap and forcing E-05 to narrow a claim that is in fact TRUE. All five keys are refused by the shipped writer today. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 parametrized over all five keys (`Item-Dependencies` added) with the measurement cited; E-05 reframed so its expected result is that the comment is already true; V-02 requires all five passing. |
| PR-R05 | MEDIUM | IN-SCOPE | G. Plan executability (scope fence) | plan Scope check and E-05; `aw ipd finalize` scope reconciliation | Once E-05 is a verification expected to change nothing, `agent_workflows/runner_shared.py` ends DECLARED BUT UNMODIFIED (its only edits being reverted negative controls), which finalize requires a `--scope-ack` for. The plan described the path as "touched" and never stated this, so a clean diff on a declared path would look like a defect. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope check now states the path is expected byte-identical at the end, names it a declared-but-unmodified path, and supplies the `--scope-ack` reason. |
| PR-R06 | LOW | IN-SCOPE | E. Testing and verification | plan E-04 and V-04 ("the RED run output"); F-11's pre-existing failure | The RED probe was unscoped, so under the widened constant a bare suite run would show F-11's unrelated failure in BOTH the RED and GREEN output, leaving the evidence ambiguous about what objected. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 and V-04 narrow the probe to `tests/test_records_only_lane_rederive.py` and require the `Blocks-Release` writer case among the named failures, which review measured to be the arm the widening breaks. |
| PR-R07 | LOW | IN-SCOPE | G. Plan executability (execution contract) | plan "POST-GATE LIFECYCLE MOVE" paragraph | The gate unconditionally instructed the executor to transition the plan via `aw ipd set`, but under `aw oc run` / `aw agy run` the RUNNER owns that transition, so obeying it would duplicate or race the runner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten to the house form: the transition is unconditionally owed, its owner is conditional (runner owns it in a runner-driven execution; a hand execution invokes `aw ipd finalize`), and hand-rolled `git mv` and hand-edited status lines stay forbidden. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The recovered file's one failing arm asserts a renamed constant. Repair the literal, or drop the arm under the plan's own drop licence? | REPAIR, comparing against `runner_shared.INTEGRATION_REFUSAL_CONFLICT` itself rather than any spelling, and forbid satisfying E-01 by deletion. | Drop the arm (the plan's licence permits it, and it is the cheapest route); re-hardcode `"fail-merge"`. | The arm's PROPERTY is still true and still enforced in production: `agent_workflows/runner_shared.py:9613` defines `INTEGRATION_REFUSAL_CONFLICT = "fail-merge"` and `tests/test_runner_shared.py:2735` already asserts that value, so only the literal is stale. Re-hardcoding would re-create the same staleness at the next rename, which `6b94a4d9d` proves happens. | yes |
| D-2 | V-05 demands a green suite the tree cannot produce. Relax the bar, or hold it and let the executor stall? | Relax to a DELTA bar (no new failing id, pass count rises), naming the permitted pre-existing failure. | Hold the green bar (forces a false claim or a stall); let the executor fix `fnb8pl`'s defect in passing (out of scope, and it has an owner). | Measured: bare `python3 -m pytest` on an unmodified tree gives `1 failed, 3414 passed`, and `.aw/records/backlog/open/20260930-fnb8pl-...backlog.md` owns that failure as an `open` `bug` with `Blocks-Release: next`. GUIDING_PRINCIPLES P16's "never weaken an assertion so it passes everywhere" is not breached: the delta bar is STRICTER about this plan's own effect than a green bar would be, since it forbids any new failure while a green bar would simply be unmeetable. | yes |
| D-3 | E-02 covered four writer keys while the source comment names five. Narrow the comment, or widen the coverage? | Widen E-02 to all five keys, leaving the comment true and unedited. | Narrow the comment to four keys (what E-05 as authored implied); leave the mismatch for the executor to resolve. | Measured at review: the shipped writer refuses all five (`Status`, `Readiness`, `Approval`, `Blocks-Release`, `Item-Dependencies`), each raising `refusing to write non-allow-listed front-matter key '<key>'`. Narrowing a true claim would weaken the documented contract for no gain; the fifth case costs one list entry. | yes |
| D-4 | Should the declined `- From-Spec: 25kzda` be overruled, given `aw check plans` nudges for it? | UPHOLD the declination. | Add the field to silence the advisory. | `AGENTS.md` defines `- From-Spec:` as naming the spec a plan GRADUATED FROM; this plan graduated from backlog `mgz3f1`, recorded in `- From-Backlog:`, and cites `25kzda` as the governing contract it neither implements nor amends. The rule is `info` severity, and re-measured `aw check plans` exits 1 with 34 instances across pending plans with or without this plan. | yes |
| D-5 | E-04's revised action text tripped the `IPD-Z602` density advisory. Split the item, or restructure the text? | Restructure: move the rationale into sub-bullets, keeping one action sentence. | Split E-04 into two E-items (a RED item and a GREEN item). | A RED/GREEN pair around a single reverted source edit is ONE concern executable in one focused pass, and splitting it would let the tree be left widened between two items, which is the hazard the plan exists to prevent. Confirmed by re-running: `ipd_schema.e_item_density_advisory` returns `None` for every E-item after the restructure, and `aw ipd lint --phase review-finalize` reports zero findings. | yes |

No `Reversible: no` decision was taken in this round, so no escalation is owed under the irreversible-decision rule.

### Escalations

None. Every finding is `FIXED`, so no finding at or above the `HIGH` gate threshold is left `OPEN` or
`DEFERRED` and no `- Blocking: yes` question is owed.
