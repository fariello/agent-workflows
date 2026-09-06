# Review: runner-owned orchestrator retirement, orchestrator 84j8d7 (Set orchretire)

- Subject-Id: 84j8d7
- Subject-Type: ipd
- Reviewed-At: 2026-09-06
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `46da9b40`. Structural preflight `aw ipd lint --phase author` reported conforming
before semantic review and `--phase review-finalize` reported conforming after the revisions, on both
the orchestrator and the cross-plan-edited child `pgq326`.

DISCLOSURE, because it bears on what this review is worth: I authored this Set in the same session, so
this is a SELF-REVIEW, not an independent one. It is recorded because the repository requires a review
record before `to-review -> reviewed`, and because an adversarial re-reading has real value even from
the author. It is NOT evidence that a second party judged the design. What raises its value above a
rubber stamp is that it found one HIGH defect the authoring pass missed (PR-001), by reading the agy
runner's dispatch loop rather than trusting the plan's own account of it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G. Plan executability; spec R-10 | `agy_runipd.py:2973`, `:4138`; `.../orchretire-03-pgq326...ipd.md:52` | Completion criterion 5 and child 03's E-04/V-04 specified only the SHARED ACTION DECIDER, proven by object identity. That is half the job on agy: the token `orchestrate` appears nowhere in `agy_runipd.py` outside the unrelated `orchestrate_isolation` import, `execute_item` derives only `is_review = action == "review"` (`:2973`), and the queue loop calls `execute_item` unconditionally (`:4138`). So the Set could ship with agy DECIDING `orchestrate`, IGNORING it, and agent-executing the orchestrator exactly as today, while V-04's identity assertion PASSED. That is spec R-10's stated failure, surviving a green Set. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fixed in the OWNING plan `pgq326` (reviewer cross-plan rule): new E-07 (agy dispatch branch acting on the action, via the SHARED outcome path) and V-07 (dispatched OUTCOME with no agent turn, plus a sabotage showing V-04 still passes while V-07 fails). Watermark 06->07. Orchestrator criterion 5, the child table, and Cross-IPD validation now require the outcome at both levels. |
| PR-002 | HIGH | IN-SCOPE | D. Anti-regression; honesty | `.../orchretire-00-84j8d7...ipd.md` gate, "NOTE ON THIS PLAN'S OWN RETIREMENT" | The recursive self-retirement note called retiring this plan by the new rollup "the preferred proof". The rollup exists BECAUSE it skips the `pre-transition` E/V checkpoint (spec R-5 shape (b)), so retiring this plan that way discharges it WITHOUT performing E-01/V-01, the only whole-Set end-to-end evidence there is. It would produce an `executed` plan asserting a verification that never ran, which is the same class of never-true claim the Set exists to correct. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Note rewritten: E-01/V-01 evidence FIRST, transition after; a premature runner retirement is to be REPORTED, not claimed as proof. Exposure bounded honestly with verified facts (`action_for` returns `orchestrate` for `reviewed`, but `oc_runipd.py:2922-2924` admits only to-review/draft/approved/auto-approved as `queued`, so exposure begins at APPROVAL, not review). |
| PR-003 | MEDIUM | UNDER-SCOPE | Execution contract (plans README section 98-136) | `.../orchretire-00-84j8d7...ipd.md` gate, pre-revision | The gate carried a scope prohibition but none of the other four required contract elements: no declared scope fence in the mandated non-halting wording, no hard-MUST honesty rule, no path-scoped/never-push commit rule, no open-questions statement. Children 01/02/03 all carried theirs, so the orchestrator was the outlier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now carries all five: resolved-open-questions statement, a DECLARATION-style scope fence pointing at finalize's `--scope-reason`/`--scope-ack` reconciliation (and deliberately NOT telling the executor to stop over a scope question, per the 2026-09-01 maintainer ruling), the honesty rule, and the shared-checkout commit rule. |
| PR-004 | MEDIUM | IN-SCOPE | E. Testing and verification; honesty | `.../orchretire-00-84j8d7...ipd.md` completion criterion 1 vs OQ-01 | Criterion 1 said "a real run retires an eligible orchestrator" while OQ-01 resolves (maintainer-confirmed) that the accepted evidence is a SCRIPTED run over a synthetic Set. A criterion demanding more than the plan licenses is either unmeetable or an invitation to overclaim, and overclaiming is this Set's own subject matter. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Criteria 1 and 2 reworded to "scripted run"/"dispatch" with the limit stated inline and a standing instruction to read "real run" nowhere as an unattended proof; V-01 now requires naming it a scripted synthetic-Set rehearsal. |
| PR-005 | MEDIUM | UNDER-SCOPE | E. Testing and verification; spec R-9 | criterion 3 and V-01 (b), pre-revision | Spec R-9 names FOUR refusal causes and child 03 E-02 implements four, but the orchestrator's criterion 3 and V-01 required only "the three refusal causes". The omitted fourth is `transition refused`, the `rh5tt6` case, whose misclassification as RECONSIDER produces the infinite retry loop the Set calls the one regression worse than the bug. The Set's own top-level validation did not require demonstrating it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Criterion 3, E-01, and V-01 (b) now require all four causes, with the fourth explicitly shown to TERMINATE rather than retry. |

No finding was DEFERRED, left OPEN, or marked REPLAN, so no escalation to a `- Blocking: yes` open
question was required.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001 is a defect in child `pgq326`, not in the orchestrator under review. Fix it in the child, or only note it in the parent? | Fixed it in the OWNING plan `pgq326` (added E-07/V-07, advanced the watermark, recorded a history line saying its own review is still outstanding) and cross-referenced it from the orchestrator. | (a) Note it in the orchestrator only and let `pgq326`'s own review catch it, rejected because `pgq326` may be approved and executed without a further review pass, and E-04 would then ship a decider whose value agy ignores. (b) Restructure `pgq326`'s E-04 rather than add E-07, rejected as a larger edit to a plan I was not reviewing. | `plan-review.md:224-226` "When a finding spans plans, fix it in the owning plan and cross-reference it from dependent plans" | yes |
| D-2 | Does PR-001 warrant BLOCKER rather than HIGH? | HIGH. | BLOCKER, rejected: nothing ships broken to a user and no data is at risk; the consequence is a wasted agent turn plus a false parity claim, which is a material correctness/coverage gap rather than a normal-path failure or invariant violation. | `plan-review.md:504-509` severity definitions | yes |
| D-3 | Verdict `APPROVE WITH REVISIONS APPLIED` or `REVIEWED - OPEN QUESTIONS`, given OQ-01 is present in the plan? | `APPROVE WITH REVISIONS APPLIED`. | `REVIEWED - OPEN QUESTIONS`, rejected because OQ-01 carries `Status: resolved` and `Blocking: no`, resolved by the maintainer directly on 2026-09-06; a resolved question is a recorded decision, not an outstanding one. | plan OQ-01 body; `plan-review.md:525-529` | yes |
| D-4 | Readiness value to write. | `go-pending-approval`. | `go`, rejected: `Status` is `reviewed`, the human has not signed off, and `go` requires `Status: approved`. `no-go`, rejected: no open question and no unfixed BLOCKER/HIGH remains, and the workflow reserves `no-go` for genuine not-ready conditions rather than a missing signature. | `plan-review.md:531-546`; `.aw/records/plans/README.md:45-51` | yes |

No `Reversible: no` decision was taken, so no escalation under the irreversible-decision rule was
required.

### Verified claims

Every load-bearing measurement was re-run rather than carried from the authoring pass. The plan cites
HEAD `844d195c`; I measured at `46da9b40`, and all of it holds.

- Zero successes. `grep -rh orchestrator-finalized .aw/records/runs/*/events.jsonl | wc -l` is `0`;
  `orchestrator-deferred` is `28`, across 15 distinct id6s enumerated by parsing the event payloads
  (`3b4f8u`, `5e4sb6`, `88h0h8`, `bl9q3d`, `c2tvmm`, `dh5gnl`, `e6h1p3`, `r4mbcw`, `r7xku3`, `rh5tt6`,
  `ryvoi5`, `u5vyye`, `y0gg8o`, `yt93ir`, `zpbx7o`), matching the plan exactly.
- The run-record count. 103 `run-*` directories each with an `events.jsonl`. The plan says "all 102
  durable run records"; the count is now 103, an off-by-one against a moving denominator rather than an
  error in the measurement, and it does not affect the argument (the numerator is 0). Not raised as a
  finding.
- Born blocked, not regressed. `99760832` is dated 2026-08-24 and `801dd28a` 2026-08-27, and
  `git merge-base --is-ancestor 801dd28a 99760832` returns false, confirming the rollup was written
  against a gate that already refused it.
- The single `else`. `oc_runipd.py:6993` opens the orchestrate branch and `:7015` writes
  `runnable["status"] = "dependency-blocked"` on any failure, with the reason ternary distinguishing
  `not-all-children-executed` from `finalize-refused` in the EVENT only, not in the status.
- `dependency-blocked` is terminal and the finalize path is receipt-gated. `oc_runipd.py:261` places it
  in `TERMINAL_STATES`; `ipd_lifecycle.py:1337-1345` returns the "no begin receipt ... fail-closed"
  refusal before any other gate, and `:1355-1362` shows the receipt's `base_head` is what the scope
  delta is computed from, which is why R-6 cannot be answered by simply dropping the receipt without
  saying what replaces it as the scope baseline. Child 02's E-03 leaves that choice open but bounded.
- Queue-scoped completeness. `_set_children_all_executed` (`oc_runipd.py:751-770`) iterates
  `state["queue"]` only and returns `(False, [])` for a Set with no in-queue children, exactly as the
  plan and the backlog addendum describe.
- The documented claim is generated. `AGENTS.md:42` carries the self-finalization sentence and
  `engine.py:1207` is its source, so child 03 E-05's insistence on editing the generator is correct.
- The agy asymmetry, and MORE than the plan claimed. `agy_runipd.py:1510-1514` defines
  `determine_action` with no orchestrator concept and `:1783` calls it. Beyond the plan's account, the
  token `orchestrate` is absent from the whole module (excluding the unrelated `orchestrate_isolation`
  import), `execute_item` reads only `is_review` (`:2973`), and the loop calls `execute_item`
  unconditionally (`:4138`). That gap is PR-001.
- `action_for`'s real boundary. `oc_runipd.py:2450-2463` returns `orchestrate` for a `reviewed`
  orchestrator, not only an approved one; I verified by calling it. The queue-admission filter
  (`:2922-2924`) is what keeps a merely `reviewed` plan undispatched. Both facts are now stated in the
  plan, replacing a first revision of mine that overstated the exposure as beginning at review.

### Right-sizing and conceptual density

The orchestrator carries a single E-item that authors no product code, which is correct for its kind and
not a count to pad. Each child's E-items address one concern each; child 03 is the densest (now seven
E-items across two hosts, the generator, and tests) but its items are independently executable and
independently verifiable, and its `Scope-Paths` already covered the E-07 addition. No split recommended.

### Not verified, and stated as such

I did not execute the Set, run the suite, or exercise a runner. This review is a documentary and
source-reading pass; every code claim above is a read of the named `path:line` at `46da9b40`, not an
observed runtime behavior. The Set's own V-items are what must produce runtime evidence.
