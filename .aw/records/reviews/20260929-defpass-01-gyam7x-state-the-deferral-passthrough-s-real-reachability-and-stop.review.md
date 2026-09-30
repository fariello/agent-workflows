# Review findings: plan gyam7x

- Subject-Id: gyam7x
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `f2326296` in an isolated review lane. The plan file was committed and byte-identical to
the lane input (`diff -q` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0) with one `IPD-Z602` advisory BEFORE semantic
review; `--phase review-finalize` reports `conforming` with no advisory after revision.

EVERY ONE OF THE PLAN'S EIGHT FINDINGS WAS RE-DERIVED BY RUNNING CODE, AND ALL EIGHT HOLD. F-05, the most
concrete: `rescore_is_an_improvement`'s docstring cites `oc_runipd.py:6120-6132` and the file is 5278 lines, so
both endpoints are past end of file. F-01 and F-02's ordering: `execute_item_core` spans lines 30498 to 34542,
the `item["status"] = "running"` write is at 30905, the first score at 31694, the rescore at 32214, and the only
in-body `record_integration_refusal(` calls are at 32818, 34075 and 34087, all after it. So neither scoring
point can observe `merge-retry`, exactly as claimed. F-03: `item["status"] = decision.status` at line 10213 is
the SOLE assignment of that status anywhere in `agent_workflows/`, it sits inside `record_integration_refusal`
(span 10137 to 10303), and both hosts' `--retry-incomplete` sets list `integration-deferred` and `merge-retry`
with the in-tree comment that a deferral "can outlive its run". F-04: `merge-retry` is absent from all three
`TERMINAL_STATES`, `outcome_precedence_disposition(None, {"disposition": "merge-retry"})` returns `None`, and
`fail-verify`/`fail-gate` are both terminal. F-06: both comments are present as quoted. F-07: the existing test
asserts exit code 0 only with no negative control, and `test_deferral_behavior` uses a SCRIPTED reconcile that
returns the status, so it proves nothing about production. F-08: five host-line citations, four past EOF.

I WENT FURTHER AND DEMONSTRATED EVERY ASSERTION THE PLAN ONLY SPECIFIES, because this plan's deliverable is a
test and a specified-but-unrun assertion is the same risk class as the comment it is fixing. All three E-05
assertions are implementable as written: a `merge-retry` item returns `('merge-retry', None)` at BOTH exit
codes; a `running` item returns `('fail-verify', None)` and `('fail-gate', None)`; and the assertion (3)
recorder, driven through `RescoreAfterAReaskTests._drive`'s own `reconcile=` seam, captures exactly
`['running', 'fail-verify']` from two calls with no `merge-retry`. I ALSO RAN E-06's FALSIFICATION: deleting
the two-line passthrough in place makes assertion (1) return `fail-verify` at exit 0 and `fail-gate` at
nonzero, while assertions (2) and (3) are unchanged, which is precisely the scope split E-06 predicts. The
mutation was reverted by path name and `agent_workflows/` is clean.

WHAT REVIEW FOUND THAT AUTHORING DID NOT is one gate-level HIGH, one contract violation, and two test-rigour
gaps.

THE GATE-LEVEL ONE: FIVE DEFERRED ROWS NAMED NO DURABLE CARRIER, so `check.ipd-uncarried-obligation` reported
this plan at severity `error` and it could not have reached `approved`. Four of the five are genuine non-tasks
(a REFUSED deletion, and two explicit no-change decisions) and now carry `Carrier-Declined` with the reason
each is nobody's work. The fifth is the interesting one: OQ-01 deferred a real design question "to the
follow-up backlog item in Deferred", and that item DID NOT EXIST, which is exactly the vanishing-obligation
shape the rule is built to catch. I filed `ma8aig` during review, carrying the four-citation sweep AND OQ-01's
question, with every offset re-resolved against both host files so the sweep starts from measurement. OQ-01 is
now `resolved` with the substance unchanged and the obligation durable (PR-001, PR-002, F-11).

THE CONTRACT VIOLATION: E-06 instructed the executor to make a "THROWAWAY copy of the tree OUTSIDE this
worktree". An executing agent's authorized workspace IS its lane, and writing outside it defeats the driver's
integration and can corrupt another agent's tree. It is also unnecessary: the mutation is two lines, reverted
by one path-scoped `git checkout --`, which I verified by doing it. E-06 now mutates in place, requires the
`git status --short` proof, forbids `git stash`/bare `reset`/`checkout .`, and states why the outside-the-lane
instruction must not be reinstated (PR-003, F-12).

THE TEST-RIGOUR GAPS. First, E-05's assertion (3) named the harness but not HOW to install the recorder, and
the natural reading (script a return value) would reproduce F-07's exact weakness: a stub that returns
`merge-retry` proves nothing about whether production can produce it there. The harness has a `reconcile=`
parameter that installs a callable via `mock.patch.object`, so the recorder must DELEGATE to the real function
after capturing. E-05 now says so, and names the `first_outcome`/`reask_outcome` pairing that actually triggers
a re-ask, because a pairing that completes on the first outcome yields ONE call and makes the assertion
vacuous. Second, and this is the sharper finding: THE RESCORE DOES NOT SEE `running`, IT SEES THE FIRST SCORE'S
OWN RESULT. The captured pair is `['running', 'fail-verify']` because `item["status"] = disposition` runs
between the two scoring points. That makes the rescore's blindness structural rather than an ordering
accident, and it is a stronger argument than F-02 gives; E-05 now asserts the captured COUNT too (PR-004,
PR-005, F-09, F-10).

TWO SMALLER ITEMS. F-02's enumeration of intervening `item["status"]` assignments omitted `fail-gate` (the
measured set is `fail-gate`, `fail-lane` three times, `fail-begin`, `interrupted`, and the scored
`disposition`); the omission does not weaken the conclusion, since none writes the deferred status, but the
list is now complete as measured (PR-006). And the gate said "finalize through the tooled path" without the
conditional runner-versus-executor ownership, which invites an executing agent under a runner to finalize a
transition the driver owns (PR-007).

ONE NOTE ON SELF-CONSISTENCY, since this plan's subject IS citation hygiene: my own first draft of the new
E-07 quoted the bare offset it discusses, and `IPD-C801` caught it at `review-finalize`. Rewritten to locate
the citation by content string instead. The plan's Step 0 convention ("this plan's subject matter IS an expired
offset, so every citation it writes obeys the rule it is enforcing") is the right standard and the linter
enforces it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Anti-regression (an `error` rule fires on the plan) | `ce.check_durable_carrier(root)` returns `check.ipd-uncarried-obligation` at `error`: "5 obligation(s) name no durable carrier: deferred row 1 records an outstanding obligation with NO durable carrier; once this plan reaches `executed` it classes `done` in `aw attention` and this vanishes with no record" | **Five Deferred rows and open questions named no durable carrier, so the shipped gate reported this plan at severity `error` and it could not have reached `approved`.** Four rows record genuine non-tasks and needed an explicit decline rather than silence; the fifth (OQ-01) deferred real work to an item that did not exist | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added `Carrier-Declined` to the four non-task rows, each stating why nobody owes the work (a refused deletion, two no-change decisions). Filed `ma8aig` for OQ-01's real obligation and pointed the row at it. `ce.check_durable_carrier` now returns nothing for this plan |
| PR-002 | HIGH | IN-SCOPE | G. Plan executability (an obligation deferred to a nonexistent item) | OQ-01 as authored: `Status: open`, "DEFERRED to the follow-up backlog item in Deferred"; no such item existed (`aw find` over the backlog returns nothing for the four-citation sweep before review) | **OQ-01 deferred a real design question and the four-citation sweep to a follow-up item that was never filed, so both would have vanished when the plan reached `executed`.** The plan's own Deferred section says "Recommend a single follow-up backlog item", which is a recommendation to a reader rather than a durable record | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Filed `ma8aig` during review with all seven host-line citations re-resolved against both host files, the four-versus-three split between past-EOF and resolves-to-wrong-code, and OQ-01's design question stated with that sample as its evidence. OQ-01 now `resolved`, `Owner: plan reviewer`, substance unchanged, carrying `- Carrier: ma8aig` |
| PR-003 | HIGH | IN-SCOPE | G. Plan executability (instruction violates the execution contract) | E-06 as authored: "In a THROWAWAY copy of the tree OUTSIDE this worktree (never committed)"; review performed the same mutation in place and reverted with one `git checkout --`, `git status --short` clean | **E-06 told the executor to write outside its authorized workspace, which defeats the driver's lane integration and can corrupt another agent's tree, for a mutation that is two lines.** The instruction is also self-defeating: a copy outside the lane is not the tree the suite and the tooling are configured against | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | E-06 now mutates IN PLACE and reverts by path name, requires the `git status --short` proof, forbids `git stash`/bare `reset`/`checkout .` (shared checkout), and records why the outside-the-lane instruction must not be reinstated. V-06 now refuses a scratch-copy report as evidence and calls it a contract violation to report. The Required-tests bullet was swept to match. New F-12 |
| PR-004 | MEDIUM | UNDER-SCOPE | E. Testing (the specified test would reproduce the weakness it replaces) | E-05 as authored named the harness but not the installation mechanism; `RescoreAfterAReaskTests._drive` carries a `reconcile=` parameter installed via `mock.patch.object(oc_runipd, "reconcile_disposition", reconcile)`; F-07 records the existing test's stub returning `R.INTEGRATION_DEFERRED_STATUS` | **E-05's assertion (3) could be satisfied by a scripted recorder, which is exactly the defect F-07 identifies in the existing coverage.** A stub that returns the deferred status proves nothing about whether production can produce it at that point, and the plan's own finding says so about `test_deferral_behavior` | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now names the `reconcile=` seam, requires the recorder to DELEGATE to the real `reconcile_disposition` after capturing, and names the `first_outcome=NO_REPORT_PARTIAL`/`reask_outcome=REASK_STILL_PARTIAL` pairing that actually reaches the rescore. V-05 fails the item for a scripted return and requires the captured list and count. Review ran the probe and measured `['running', 'fail-verify']` |
| PR-005 | MEDIUM | IN-SCOPE | A. Correctness (a stronger fact than the plan states) | Recorder probe captured `['running', 'fail-verify']`; `item["status"] = disposition` measured at line 32051, between the `"running"` write (30905) and the rescore (32214) | **The rescore does not see `running`; it sees the first score's own result, which makes the unreachability structural rather than an ordering accident.** The plan's F-02 argues from call ORDER alone, which is true but weaker: even if a refusal moved earlier, the rescore would read whatever the first score wrote. Stating it correctly also guards E-05 against a vacuous pairing that produces one call | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-10 records the captured pair and the intervening assignment. E-05 now asserts the captured COUNT is two and explains why, so a pairing that completes on the first outcome cannot satisfy it |
| PR-006 | LOW | IN-SCOPE | A. Correctness (an incomplete enumeration) | Measured assignments to `item["status"]` between line 30905 and 32214: `fail-gate` (30997), `fail-lane` (31057, 31123, 31229), `fail-begin` (31156), `interrupted` (31555), `disposition` (32051) | **F-02 lists the intervening status assignments and omits `fail-gate`.** The conclusion is unaffected (none writes the deferred status, which is the only thing that matters) but an enumeration presented as exhaustive should be exhaustive, in a plan whose whole subject is comments that overstate what they know | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02's list corrected to the measured set with the multiplicity of `fail-lane` shown, and labelled as corrected at review with an explicit note that the conclusion does not change |
| PR-007 | LOW | UNDER-SCOPE | G. Plan executability (gate missing conditional finalize ownership) | The gate's POST-GATE LIFECYCLE paragraph said only "finalize through the tooled path"; precedent gates in this repository carry the runner-versus-executor split | **The gate does not say WHO finalizes, so an executing agent under a runner may run `aw ipd finalize` on a transition the driver owns.** The review workflow's Step 4 requires the lifecycle transition with conditional ownership, and its absence is the gap that produces a double transition or a hand-rolled move | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now states that the DRIVER owns the transition under `aw oc run`/`aw agy run` and the executor finalizes only on a hand run, forbids hand-editing `- Status:` and `git mv` into `executed/` with the reason, and says to answer a scope-gate refusal with `--scope-ack` rather than a cosmetic edit |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01 asked whether a mechanical check should refuse a past-EOF `<file>:<line>` citation, and deferred it to a nonexistent item. Ask the maintainer, resolve the design question, or file the carrier? | File the carrier (`ma8aig`) and resolve OQ-01 as "defer the DECISION, not the OBLIGATION" | Asking the maintainer whether to build the check, which is a design question nobody can answer better with a sample of one sentence; resolving the design question here, which would put a repo-wide rule behind a two-comment fix; leaving OQ-01 open, which the `error` gate refuses | The authoring reasoning about the check was substantively RIGHT and only structurally incomplete, so overturning it would be wrong; what was missing is a durable home. Measured at review: `check.ipd-uncarried-obligation` fires at `error` on an obligation naming no carrier, so leaving it open is not a state the plan can be approved in. The filed item carries the full sample (four past-EOF, three resolving to `)`, `#`, and an unrelated comment), which is the evidence the decision actually needs and which no amount of asking would produce | yes |
| D-2 | Four of the five uncarried rows are refusals or no-change decisions. Declare `Carrier-Declined`, or file items for them too? | `Carrier-Declined` on all four, each with its own reason | Filing an item per row, which would create four items recording work the plan argues AGAINST doing; leaving them uncarried, which the gate refuses | A declined obligation must be one needing no carrier, and all four qualify on measurement: the passthrough deletion is REFUSED (`merge-retry` absent from all three `TERMINAL_STATES`, `outcome_precedence_disposition` returns `None`, so deletion would relabel a non-terminal deferral terminal); adding `merge-retry` to `DEFECT_REASK_SKIPPED_STATUSES` is a behavior change the plan argues against; and the refusal tuple plus rank table measure correct as they stand. Filing items for work nobody should do is the mirror-image dishonesty of leaving real work uncarried | yes |
| D-3 | E-06's falsification needs the passthrough deleted. In place, or in a copy outside the lane as authored? | In place, reverted by path name | The authored outside-the-worktree copy; a `git stash`-based mutation; a separate scratch clone inside the lane | The lane IS the authorized workspace and writing outside it defeats the driver's integration, which is a contract rule and not a preference. Verified the in-place path is sufficient by doing it: two lines deleted, assertion (1) went RED as `('fail-verify', None)` and `('fail-gate', None)`, `git checkout --` restored the file and `git status --short` came back clean. `git stash` was rejected because this checkout is shared and a stash can capture a co-worker's unstaged work | yes |
| D-4 | `IPD-Z602` flagged E-01 as bundling multiple concerns. Split it into per-fact items, or restructure it? | Split out the citation re-measurement as E-07, and restructure the ordering fact as ONE proof rather than a list of checks | Splitting into four items, one per lettered sub-fact; leaving E-01 as authored and accepting the advisory | Measured by decomposition: sub-facts (a) and (b) are the SAME comparison stated twice (`run[0] < first[0]`), and (a) through (c) are all answered by one sorted position list, so splitting them would create items with no independent work. The citation check (d) IS independent: it reads a different file, proves a different claim, and has its own failure mode (past-EOF versus resolves-to-wrong-code) needing different downstream wording. So the correct split is two, not four, and the advisory cleared | yes |
| D-5 | E-05's assertion (3) recorder: require delegation to the real function, or allow a scripted return? | Require delegation | Allowing a scripted recorder, which is simpler to write and is what the existing `test_deferral_behavior` does | The plan's own F-07 identifies the scripted stub as the reason existing coverage "proves nothing about whether production can produce that value there". Permitting the same shape in the new test would reproduce the defect the plan exists to close, one file over. Verified delegation works through the harness's `reconcile=` seam and captures `['running', 'fail-verify']`, so the stricter requirement is also the demonstrated one | yes |
| D-6 | The captured pair shows the rescore reading `fail-verify`, not `running`. Correct F-02's argument, or leave it? | Add F-10 recording the sharper fact and leave F-02's ordering argument standing | Rewriting F-02 to the stronger argument, which would discard the measured call-order evidence; leaving the sharper fact unrecorded, since the conclusion is the same either way | Both arguments are true and they fail differently, which is the reason to keep both: F-02's ORDER argument breaks if a refusal call moves earlier, while F-10's argument (the rescore reads the first score's own result) survives that change. Recording both means a future reader who invalidates one still has the other, and E-05's count assertion now pins the observable that F-10 rests on | yes |
