# Review findings: plan skn8uk

- Subject-Id: skn8uk
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `249e6a8d`. The plan on disk was byte-identical to the sealed lane input (`diff`
reported no difference) and `git status --porcelain` was empty, so no pre-review snapshot was needed.
Structural preflight `aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0, and
`--phase review-finalize` reports `clean` after the revisions.

THE DIAGNOSIS IS CORRECT AND THE FIX IS THE RIGHT SHAPE. This is a well-built plan: one product file,
a pure comparison predicate with an explicit rank, a monotonic-improvement-only safety property, and a
correct refusal to touch the dependency cascade or `reconcile_disposition` itself. I re-verified the
mechanism by AST and by running the real collection code rather than by reading the plan's prose, and
the structural claims hold. Specifically confirmed: `execute_item_core` sets its six carrier fields in
one contiguous block immediately before the `if not is_review:` defect block; the defect event append
and the `integration_gate_relevant` assignment are separated by a 2-line gap at function top level
(4-space indent, outside the `if not is_review:` body), so the rescore has a real insertion point; an
existing top-level `save_state(run_dir, state)` sits downstream of that point, which is what lets E-04
add no new call site as the `test_no_call_site_was_rewritten` pin requires; `reconcile_disposition` is
bound per host by `getattr` and is pure in all three copies; and `integration_is_earned` really does
return `INTEGRATION_REFUSED_NO_SIGNAL` when `validate=False` with no suite result, which is exactly the
fail-closed posture OQ-02's resolution claims.

I also confirmed the re-ask is genuinely reachable in the measured case, which the plan asserts but does
not prove: `validate_defect_report(None)` returns `needs_reask=True` with state `absent`, `partial` is
NOT in `DEFECT_REASK_SKIPPED_STATUSES`, and `defect_reask_is_warranted` returns True given an observed
session id. So the path the whole plan depends on exists.

WHERE THIS REVIEW SPENT ITS EFFORT: the plan's central GATE, as specified, would have been decorative,
and one of its stated outcomes was impossible. Each finding below was measured, several by executing the
shipped code rather than reading it.

**1. The recollection gate reads the wrong receipt field, and as specified it cannot refuse the case it
exists to refuse.** E-02 required the gate be read "from the collection receipt via
`lane_containment.read_collection_receipt`", which is right, and V-02 then named the condition as the
receipt "recording `status: complete` and `outcome` collected". I ran `collect_lane_submissions` against
an EMPTY lane in a `tmp_path` fixture, which is precisely the measured first-turn case:

```text
EMPTY LANE receipt:
  status    = complete
  collected = []
  failed    = []
  outcome submission result = absent

  status == 'complete'?          True   <-- a status-only gate PASSES
  not receipt['failed']?         True   <-- a failed-empty gate PASSES
  'outcome' in receipt['collected']?  False   <-- the sound gate refuses
```

The cause is in the collector: `receipt["status"] = RECEIPT_COMPLETE` is assigned unconditionally once
the three `_collect_one` calls return, and `_collect_one` classifies a missing source `absent`, a result
that appears in NEITHER `collected` NOR `failed`. So both of the readings the plan's wording invites let
a rescore fire on a lane that submitted nothing, where it would call `reconcile_disposition` a second
time with no new evidence and re-derive the same `partial`. That is not a wrong answer, which is what
makes it dangerous: it is a gate that looks like a safeguard, passes its own happy-path test, and
protects nothing. Fixed by requiring `"outcome" in receipt["collected"]` explicitly in E-02, naming both
rejected readings with the measurement, and adding the absent-outcome fixture to V-02 as a mandatory
third negative control (a gate written the wrong way passes V-02's original two controls).

**2. E-05 and E-04 promised a run-report visibility that does not exist for any driver event.** E-05's
rationale said "the events ledger is what `aw runs` reads" and its expected outcome was that
`aw runs <run-id>` surfaces the event; E-04's said `aw runs <id>` describes the disposition. Measured:
`run_viewer.py` contains the string `events.jsonl` exactly once, inside a tuple of filenames used to
decide which files a run directory holds, and never parses a line of it. No driver event is rendered
there at all: `defect-report-recorded`, `dependency-blocked`, `ipd-stalled` and `turn-bound-expired` each
appear zero times. The `aw runs evidence` leaf concerns captured provenance envelopes and tool events,
not the drivers' `events.jsonl`. So an executor writing the test E-05's outcome demands would have it
fail for a reason this plan does not own, and the likely repair would be to edit `run_viewer.py`, which
is not in `Scope-Paths`. E-04's `last_outcome` claim is the opposite case and is CORRECT:
`run_viewer.py` really does read `item.get("last_outcome")`, so the stale `None` really is a reporting
bug. Fixed by dropping the events claim, keeping the honest durability claim, fencing `run_viewer.py`
out explicitly, and recording the pre-existing gap as non-blocking OQ-03.

**3. E-06 describes the AST pins wrongly in three ways, though its conclusion is right.** It says the
pins "anchor on the LAST `disposition, ...` tuple assignment" and that `execute_item` "calls
`reconcile_disposition` THREE times", implying three such assignments. Measured by AST on
`execute_item_core`: there is exactly ONE tuple-to-`disposition` assignment, because the two stop
handlers assign `item["status"], _ = reconcile_disposition(...)`, whose first target element is a
`Subscript` and not a `Name`, so the pins never see them. Second, pin 2 anchors on
`integrate_lane_branch`, not `integration_is_earned`, and those are far apart. Third, the docstring's
parenthetical cites `oc_runipd.py:7344` and `:7372` for the early-recovery calls and both offsets now
land on unrelated lines. The plan's CONCLUSION (both pins survive unweakened) is correct and I
re-derived it arithmetically against current line numbers. Fixed by replacing the description with the
measured one, keeping the verify-don't-assume instruction, requiring the two drifted offsets be
re-anchored by symbol, and specifying the new pin against `integration_is_earned` (strictly stronger than
pin 2 for this plan's property).

**4. E-01's refusal list is defence-in-depth, not the live safety property it reads as.**
`runner_stop.STOPPED_DISPOSITION` is `"interrupted"` and `FORCED_DISPOSITION` is `"unknown_outcome"`,
and BOTH are already in `DEFECT_REASK_SKIPPED_STATUSES`, so `defect_reask_is_warranted` refuses a re-ask
on either and neither can ever be the `before` value at the rescore point. Worth stating because it
changes where an implementer should spend care: `"integration-deferred"` is NOT in that skip set, so a
re-ask CAN fire on a deferred item and reach the rescore. That makes E-03 load-bearing rather than
theoretical, which is the opposite of how the two items' relative weight reads. Kept both entries
(a future widening of the skip set would make them live) and recorded the distinction.

**5. Every `runner_shared.py` citation has drifted; no other file's has.** Measured across all 25
distinct citations: the 12 `runner_shared.py` offsets all now land on unrelated lines (`:13107`, the
headline scoring-call anchor, reads `else None`; `:13337`, the integration gate, reads
`"event": "lane-submissions-collected"`), while every `oc_runipd.py`, `agy_runipd.py`,
`lane_containment.py`, `run_viewer.py` and `tests/` citation still resolves correctly. The asymmetry has
a mechanical cause: `runner_shared.py` grew 13844 -> 14082 lines after authoring. None is out of range,
so none announces itself. The substance of every claim was re-verified and holds. Re-anchored the
load-bearing ones by symbol and added a standing warning at the head of the conventions section.

**6. The cited run directories cannot be re-verified from the tree, though the commits can.** F-1, F-2
and F-5 cite on-disk artifacts in `run-20260918T193638Z-2963696` and `run-20260918T190723Z-2697256`;
`.aw/records/runs/` is gitignored and holds neither in this lane. That is expected rather than a defect,
and the plan already knows CI lacks the tree. What IS independently verifiable and was verified: both
cited lane commits exist with subjects matching the plan's description (`08416ebd` "docs(nobugship-01):
record no-known-bugs rule ... (zqs0px)", `8247a13c` "zz5yxq: split reviewed out of the run success bar
for execute action"), which corroborates F-3. Recorded in Required tests so an executor builds V-02's
fixture from the described shapes rather than hunting for a run directory.

**7. No scope fence was present.** The plan declared `Scope-Paths` but carried no fence paragraph in its
gate. Added one in the DECLARATION form the contract requires (make the edit and justify it at finalize,
never "stop and report"), naming the two files review found the plan leaning toward: `run_viewer.py` and
the three `reconcile_disposition` copies.

ON THE CARRIERS, which I checked and am deliberately NOT reporting as a finding. Two obligations carry
`- Carrier: s0gnha`, and a self-carrier-style terminal-resolution failure is the defect I found on the
parent in the previous review. Here it does NOT apply, and the ordering is why: the runner retires an
orchestrator only once EVERY child is `executed` (`evaluate_set_retirement` refuses with
`RETIRE_REFUSED_UNFINISHED_CHILDREN` otherwise), so at the instant `skn8uk` finalizes, `s0gnha` is still
pending and both carriers resolve. Simulating the post-Set state shows 2 failures, but by then `skn8uk`
is itself terminal and `check_durable_carrier` sweeps PENDING-lane plans only. The carriers are correct.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. correctness; E. testing | Measured by running `lane_containment.collect_lane_submissions` against an empty lane in `tmp_path`: `status='complete'`, `collected=[]`, `failed=[]`, outcome `result='absent'`. In the collector, `receipt["status"] = RECEIPT_COMPLETE` is unconditional after the three collects, and `_collect_one` returns `absent` for a missing source, which joins neither list | E-02's "recollection having reported success" and V-02's `status: complete` both PASS on a lane that submitted nothing, so the gate as specified cannot refuse the measured empty-first-turn case. A rescore behind either reading would re-call `reconcile_disposition` with no new evidence and re-derive `partial`: a decorative gate that passes its own happy-path test and protects nothing | C:Low; U:Low; S:Low; F:Medium-High; Overall:Low | FIXED | E-02 now requires `"outcome" in receipt["collected"]`, names both rejected readings with the measurement, and forbids gating on `status` or on an empty `failed`. V-02 now demands THREE negative controls including the absent-outcome fixture, which a wrongly-written gate passes |
| PR-002 | MEDIUM | IN-SCOPE | C. architecture; G. executability | `grep` in `run_viewer.py`: `events.jsonl` appears once, in a filename tuple; no `json.loads` of any events line; `defect-report-recorded`, `dependency-blocked`, `ipd-stalled`, `turn-bound-expired` each appear 0 times. `aw runs evidence` covers provenance envelopes and tool events, not driver events. Contrast: `run_viewer.py` DOES read `item.get("last_outcome")`, so E-04's other claim is sound | E-05's rationale ("the events ledger is what `aw runs` reads") and its expected outcome, plus E-04's, promise a run-report visibility that exists for NO driver event. An executor writing the demanded assertion would fail for a reason this plan does not own, and the natural repair edits `run_viewer.py`, outside `Scope-Paths` | C:Low; U:Medium; S:Low; F:Low; Overall:Low | FIXED | Events claim dropped from E-05 and E-04; the durable-and-greppable claim kept as the real auditability property; `run_viewer.py` fenced out explicitly; V-05 forbids asserting any `aw runs` rendering; pre-existing gap recorded as non-blocking OQ-03 |
| PR-003 | MEDIUM | IN-SCOPE | D. anti-regression; E. testing | AST measurement on `execute_item_core`: exactly ONE `ast.Assign` with a Tuple target containing a Name `disposition`; the two stop handlers assign `item["status"], _` (Subscript, invisible to the pins). Pin 2 asserts `max(disposition_assign) < first(integrate_lane_branch)`, not `integration_is_earned`. The docstring's `oc_runipd.py:7344`/`:7372` both land on unrelated lines | E-06 describes the pins it must not weaken in three incorrect ways (three tuple assignments where there is one, the wrong anchor for pin 2, two stale offsets in the docstring it is asked to correct). Its conclusion that both pins survive is right, but an implementer reasoning from the description would predict the wrong AST and mis-target the new pin | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 rewritten with the measured pin semantics, the arithmetic confirmation that both survive, an instruction to re-anchor the two drifted offsets by symbol, and the new pin targeted at `integration_is_earned` (strictly stronger than pin 2 here). Conventions section corrected to match |
| PR-004 | LOW | IN-SCOPE | A. correctness; honest reasoning | `runner_stop.STOPPED_DISPOSITION == 'interrupted'` and `FORCED_DISPOSITION == 'unknown_outcome'`, both in `runner_shared.DEFECT_REASK_SKIPPED_STATUSES`, so `defect_reask_is_warranted` refuses; `'integration-deferred'` is NOT in that set | E-01 presents refusing the stopped and forced dispositions as a live safety property; both are structurally unreachable at the rescore point. The genuinely reachable case is `integration-deferred`, which makes E-03 load-bearing rather than theoretical, the opposite of how the two items' weight reads | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now states the entries are defence-in-depth against a future widening of the skip set, and names `integration-deferred` as the live case, cross-referencing E-03 |
| PR-005 | MEDIUM | IN-SCOPE | E. testing; G. executability | Measured across 25 distinct citations: all 12 `runner_shared.py` offsets drifted (`:13107` -> `else None`; `:13337` -> `"event": "lane-submissions-collected"`; `:12483` -> `repo: Path,`), while every `oc_runipd.py`, `agy_runipd.py`, `lane_containment.py`, `run_viewer.py` and `tests/` citation resolves. `runner_shared.py` grew 13844 -> 14082 lines after authoring | Half the plan's anchors, including its headline scoring-call and integration-gate references, silently point at other plausible code. None is out of range, so none announces itself to an executor following it | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Load-bearing anchors re-anchored by symbol throughout (E-02, E-04, E-06, F-7, F-9, OQ-02, Deferred); a standing warning added at the head of the conventions section naming the measurement and instructing re-derivation by symbol |
| PR-006 | LOW | IN-SCOPE | E. testing; honest evidence | `.aw/records/runs/` is gitignored and holds neither cited run directory in this lane. Both cited lane commits DO exist: `08416ebd` "docs(nobugship-01): record no-known-bugs rule ... (zqs0px)" and `8247a13c` "zz5yxq: split reviewed out of the run success bar for execute action" | F-1, F-2 and F-5 cite on-disk run artifacts an executor cannot reach, with no note that they are unreachable, so a conscientious executor may hunt for them or copy a live run directory into a fixture | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests now states the run directories are gitignored and absent, records what IS verifiable (both lane commits, corroborating F-3), and directs the executor to build V-02's fixture from the described receipt and outcome shapes |
| PR-007 | LOW | UNDER-SCOPE | G. executability; execution contract | The gate carried the honesty rule, the path-scoped commit rule and the lifecycle move, but no scope fence | The plan's gate lacked the scope fence the execution contract requires as a DECLARATION, so nothing stated the intended surface for the finalize-time two-way reconciliation | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fence added in declaration form (make the edit and justify it at finalize, never "stop and report"), naming the two files review found the plan leaning toward: `run_viewer.py` and the three `reconcile_disposition` copies |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The recollection gate's field is wrong (PR-001). Specify the correct field myself, or escalate to the maintainer? | SPECIFY it: require `"outcome" in receipt["collected"]` in E-02 and add the absent-outcome negative control to V-02. | (a) Escalate as a blocking question: rejected, the workflow forbids asking the human what the repository answers, and I answered it by executing the shipped collector. (b) Leave E-02's wording and let the executor choose: rejected, that is the defect; two of the three plausible readings ship a gate that protects nothing and passes its own test. (c) Also require `failed` to be empty as a belt-and-braces condition: rejected as misleading, since an absent outcome is not in `failed` either, so the extra condition adds no discrimination while implying it does. | Ran `lane_containment.collect_lane_submissions` against an empty lane in `tmp_path`: `status='complete'`, `collected=[]`, `failed=[]`, outcome `result='absent'`. In the source, `receipt["status"] = RECEIPT_COMPLETE` is unconditional and `_collect_one` returns `absent` for a missing source. | yes |
| D-2 | E-05 promises `aw runs` visibility that no driver event has (PR-002). Drop the claim, or grow the plan to add the display? | DROP the claim, keep the durable-record rationale, fence `run_viewer.py` out, and record the gap as non-blocking OQ-03. | (a) Add `run_viewer.py` to `Scope-Paths` and render the event: rejected, it is a reporting concern spanning every event type rather than this one, it would be an undeclared expansion of a release-blocking defect fix, and deciding which events to show is a design question. (b) Leave the claim: rejected, an executor would write an assertion that fails for a reason this plan does not own. (c) Say nothing about the gap: rejected, the corrected claim leaves a real visibility hole and a later reader should know it is pre-existing and deliberate, not an oversight. | `run_viewer.py` mentions `events.jsonl` once, in a filename tuple, and parses no line of it; `defect-report-recorded`, `dependency-blocked`, `ipd-stalled`, `turn-bound-expired` appear 0 times each; `aw runs --help` scopes `evidence` to provenance envelopes and tool events. Contrast: `item.get("last_outcome")` IS read there, which is why E-04's other claim survives. | yes |
| D-3 | Two obligations carry `- Carrier: s0gnha`, the same shape that was a real defect on the parent. Report it, or clear it? | CLEAR it: not a finding, and say so in the record with the reason. | (a) Report it as a finding by analogy to the parent: rejected as measurably wrong here, and reporting a non-defect would cost the maintainer a pointless edit. (b) Convert them to `Carrier-Declined` defensively: rejected, `s0gnha` is a genuine and correct carrier for a Set-level question, and declining would misrepresent who owns it. | The retirement gate refuses unless EVERY child is `executed` (`evaluate_set_retirement` -> `RETIRE_REFUSED_UNFINISHED_CHILDREN`), so `s0gnha` is still pending when `skn8uk` finalizes and both carriers resolve; simulating the post-Set state shows 2 failures, but `check_durable_carrier` is scoped to pending-lane plans and `skn8uk` is terminal by then. | yes |
| D-4 | The verdict: two open questions remain (OQ-01 pre-existing, OQ-03 added by review), both non-blocking. APPROVE WITH REVISIONS APPLIED, or REVIEWED - OPEN QUESTIONS? | APPROVE WITH REVISIONS APPLIED, with `Readiness: go-pending-approval`. | (a) REVIEWED - OPEN QUESTIONS / `no-go`: rejected on the repository's own shipped predicates and on precedent. Both readiness predicates return clear (`plan_readiness.has_unresolved_blocking_question` -> False, `review_findings.subject_gating_blocks` -> empty), the workflow reserves NO-GO for "genuine not-ready conditions" and explicitly says a clean plan awaiting sign-off is never a bare NO-GO, and at least 8 pending plans already carry `go-pending-approval` alongside open non-blocking questions. (b) Resolve OQ-01 myself to remove the question: rejected, it asks whether an APPROVED spec should be amended, which is a contract change only a human may authorize. | `plan_readiness.has_unresolved_blocking_question(skn8uk)` -> False; `review_findings.subject_gating_blocks('skn8uk','ipd')` -> `()`; both OQ-01 and OQ-03 carry `- Blocking: no`; measured precedent of `go-pending-approval` plans with open non-blocking questions in `pending/`. | yes |
