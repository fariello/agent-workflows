# Review: send a refused finalize back to the same agent with the gate findings, child zzcrlo (Set finalback)

- Subject-Id: zzcrlo
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `fcbbccc1`. Structural preflight `aw ipd lint --phase author` CONFORMED with zero findings
before semantic review, and `--phase review-finalize` after the revisions reports only the deliberately-open
blocking question (`IPD-Q501` on OQ-04), which is the correct fail-closed state rather than an unrepaired
structural defect. No product code was modified by this review.

DISCLOSURE: the plan was authored by the same model family, so this is close to a self-review and is worth
less than an independent one. Its value therefore rests on what was EXECUTED rather than re-read. Fourteen
things were run: the real renderer against the incident's own `state.json`; the exit-code predicate against
that same queue; the `EXECUTION_SUCCESS_STATES` call-site enumeration across both drivers; the
`finalize_refusal`/`finalize_refused` write and read sites; `_PRIOR_ATTEMPT_SAFE_KEYS` and the prompt
interpolation; the length and tail of the refusal message; the `ipd_lint` checkpoint code and every emitter
of it; `finalize_precheck`'s refusal branches; the `ledger.jsonl` search across all run directories; the
`run_engine`/`run_state` grep on both drivers; thirteen spec citations line by line; the outcome-token
consumer search; the bare suite; and the front matter of the three sibling plans.

THE GROUNDWORK IS EXCELLENT AND I WEAKENED NONE OF IT. The central claim reproduces exactly: calling the real
`render_run_summary_table` on the incident's own state prints `Outcome: COMPLETED`, `Progress: 1/1
[==========] 100% (1 substantially-complete)`, and an item row reading `substantially-complete | verified`
with no indication anywhere that finalize refused. F-1, F-2, F-3, F-4, F-5, F-6, F-7, F-8, F-10, F-11 and
F-12 all verified true, including both corrections the plan makes to its own filing item: `finalize_refused`
IS in `_PRIOR_ATTEMPT_SAFE_KEYS` and IS interpolated into the recovery prompt, and the full 657-character
nine-finding message passes through the projection intact. The decision to split honest reporting from the
retry loop is right and independently valuable, and the refusal to attempt dishonesty-detection is both
correct and unusually well argued.

THE FINDING THAT DECIDES SEQUENCING IS PR-101, AND IT IS THE ONE THING A MAINTAINER MUST ACT ON. Plan
`r2i1b1` is `approved` with `Readiness: go-pending-approval`, declares `render_stream.py` in its own
`Scope-Paths`, and its E-01/E-02 build precisely the general mechanism this plan's E-01 needs: a per-item
refusal record written by "whatever refuses", with the diagnostics block of the SAME
`render_run_summary_table` rendering it for ANY status instead of a hardcoded allowlist. Its stated goal is
that a new refusal kind be surfaced by construction, and a refused finalize is exactly such a kind. So the
landing order decides whether E-01 is a one-off branch that `r2i1b1` must later generalize and reconcile, or
an edit this plan does not need to make at all. The plan's Deferred section asserts the two are cleanly
separated; for `aw runs`/`run_viewer.py` that is true, but for the summary renderer it is not. Escalated as
OQ-04 rather than decided, because ordering two plans is a maintainer call.

ONE CLAIM IN THE CONCERN IS FALSE AND WOULD HAVE MISDIRECTED THE FIX. The plan says the run "exited 0". It
did not. Exit comes from `runner_stop.deliberate_stop_exit_code` with `success_states=SUCCESS_STATES`, and
`SUCCESS_STATES` is `{executed, reviewed, approved}`, which excludes `substantially-complete`; evaluated on
the incident's own queue it returns `1`. So the process-level contract was already honest and only the
human-readable summary lied. That both lowers the blast radius (nothing keying on the exit code was misled)
and creates a concrete regression risk the plan did not name: E-01 must not "fix" an exit code that is
already correct.

E-02 UNDER-COUNTS ITS OWN BLAST RADIUS, AND THAT IS THE FINDING MOST LIKELY TO CAUSE A REGRESSION. It names
one reader of `EXECUTION_SUCCESS_STATES` and tells the executor to find the rest; there are five, in three
distinct roles. Two of them are not dependency checks at all: `oc_runipd.py:3560` and `:7393` (with
`agy_runipd.py:4405`) inject the set as `success_states=` into orchestrator dispatch, where its only use is
to decide that a child reached a non-success terminal state and therefore TERMINATE the whole Set as
`dead-children`. Treating a refused item as non-success there is arguably right, yet it converts a
recoverable refusal into a Set-wide kill at the very moment E-03 wants that item re-dispatched. Those two
intentions conflict directly. A third site, the dependency cascade at `:4273`, carries a docstring recording
a MEASURED incident where diverging from `edge_satisfied`'s bar made a review-mode Set run impossible, so it
must change together with the gate or reintroduce that defect.

E-03's TRIGGER CANNOT BE `IPD-S404`. That code is `C_CHECKPOINT`, emitted for every checkpoint diagnostic
including the status/checkpoint mismatch and the pre-execution blocking-question check. Worse,
`finalize_precheck` returns the identical `(1, message)` shape for a MISSING begin receipt, a STALE receipt,
and scope-reconciliation failures, and the driver keeps only `fin_rc`/`fin_msg` and treats every nonzero
alike. A stale receipt is spec 5.5's "changed frozen requirements" and an out-of-scope mutation is its first
never-retry entry, so the trigger as written would retry two classes the spec explicitly forbids, in a plan
whose own fence says to honor that list.

Also corrected: the suite baseline (92 tests low), a spec citation off by 400 lines, the absence of any
existing per-item dispatch bound (with an in-tree precedent of a measured 201-dispatch spin), the
attempt-ordering dependency the feedback channel rests on, OQ-02 resolved from evidence (nothing anywhere
parses the outcome token, so reusing `PARTIAL` carries no contract risk), and OQ-03 sharpened from an open
unknown to a near-certain "no" with the measurements behind it.

Ten findings. Nine FIXED in place, one escalated as a blocking open question. No deferrals. E-items and
V-items unchanged at six each, bijection intact.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | BLOCKER | IN-SCOPE | C. architecture; scope discipline | `r2i1b1` front matter (`- Status: approved`, `- Readiness: go-pending-approval`), its scope line and `Scope-Paths` declaring `agent_workflows/render_stream.py`, its E-01 (refusal record sited in `render_stream`) and E-02 (diagnostics block for ANY status) | **AN APPROVED PLAN ALREADY BUILDS THIS PLAN'S E-01 MECHANISM GENERALLY, IN THE SAME FUNCTION, AND THIS PLAN ASSERTS THEY DO NOT OVERLAP.** `r2i1b1` writes a per-item refusal record (code, reason, remedy) and makes the same `render_run_summary_table` diagnostics block render it for any status, explicitly so "a new refusal kind is surfaced by construction". A refused finalize is such a kind. Landing order decides whether E-01 is a one-off branch `r2i1b1` must reconcile or an edit this plan need not make, and it may change `Scope-Paths` | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | OPEN | ESCALATED as OQ-04 (`Blocking: yes`, `Finding: PR-101`) with three costed options and a recommendation. E-01 gated, Deferred entry corrected to state the overlap rather than assume separation, scope check records the OQ-04-dependent declaration, gate updated. NOT decided on reviewer authority: ordering two plans is a maintainer call |
| PR-102 | HIGH | IN-SCOPE | Evidence accuracy; A. correctness | `oc_runipd.py:7507-7511`, `:336`; `agy_runipd.py:4513-4517`; `runner_stop.py:764-790`; measured `deliberate_stop_exit_code(['substantially-complete'], success_states=SUCCESS_STATES, stopped=False)` -> `1` on the incident's own queue | **THE CONCERN'S "exited 0" IS FALSE, AND BELIEVING IT INVITES A REGRESSION.** Exit uses `SUCCESS_STATES` (`{executed, reviewed, approved}`), which excludes `substantially-complete`, so the measured run exited 1 and the process contract was already honest. Only the summary lied. An executor trusting the plan could "fix" a correct exit code | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Concern corrects the claim with the measurement and states the narrowed blast radius; E-01 carries an explicit DO NOT TOUCH THE EXIT CODE with the reason; V-01 requires the before/after exit code pasted; gate fence updated. New F-13 |
| PR-103 | HIGH | UNDER-SCOPE | A. correctness; D. anti-regression | `oc_runipd.py:3377`, `:4273`, `:3560`, `:7393`; `agy_runipd.py:4405`; `runner_shared.py:3201`, `:3212-3226`, `:2546-2549` | **`EXECUTION_SUCCESS_STATES` HAS FIVE CALL SITES IN THREE ROLES, AND TWO OF THEM CONFLICT WITH E-03.** Two sites inject it into orchestrator dispatch where a non-success child TERMINATES the Set as `dead-children`, at the same moment E-03 wants that item re-dispatched. A third (the cascade) carries a docstring recording a measured incident caused by diverging from `edge_satisfied`'s bar. E-02 names one site and delegates the rest to the executor | C:Medium; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-02 now carries the measured five-site enumeration by role, states the E-03 conflict explicitly, notes the asymmetry that retirement already refuses `substantially-complete` independently, and requires a DECIDED, tested treatment (no Set killed `dead-children` while its child has budget). V-02 requires that test plus proof sites 1 and 2 agree. New F-14 |
| PR-104 | HIGH | IN-SCOPE | A. correctness; B. security lens on gates | `ipd_lint.py:65`, `:754-812`; `ipd_lifecycle.py:1470-1520`; `oc_runipd.py:6727-6730`; `agy_runipd.py:3777-3780`; spec `:978-989` | **THE STATED RETRY TRIGGER WOULD RETRY CLASSES THE SPEC FORBIDS.** `IPD-S404` is the code for EVERY checkpoint diagnostic, and `finalize_precheck` refuses with the identical `(1, message)` shape for a missing receipt, a STALE receipt (spec 5.5 "changed frozen requirements") and scope failures (its first never-retry entry). The driver keeps only `fin_rc`/`fin_msg` and cannot tell them apart, so keying on the code or the exit status crosses the never-retry boundary this plan's own fence forbids crossing | C:Low; U:Low; S:Medium; F:High; Overall:Medium | FIXED | E-03 now forbids the code and the exit status as triggers, requires a POSITIVE allowlist of the four retryable finding texts with every finding in a message required to match, prefers structured diagnostics over regexing prose, and requires the strings pinned by test. V-03 requires three specific non-retryable fall-through cases. New F-15 |
| PR-105 | MEDIUM | IN-SCOPE | E. testing; D. anti-regression | bare `python3 -m pytest` at `fcbbccc1` -> `1 failed, 5958 passed, 3 skipped, 2 xfailed in 54.62s`; `.gitignore:49`; backlog `8kttqq` (`open`) | **THE STATED BASELINE IS 92 TESTS LOW**, in a plan whose validation is a suite delta. The named environmental failure and its cause are correct, but a wrong total invites an executor to treat drift as regression, and the tree causing it belongs to another party | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Conventions and V-06 carry the re-measured figure, the real node id, an explicit prohibition on touching another party's gitignored tree per the shared-checkout rule, and a node-id comparison. New F-20 |
| PR-106 | MEDIUM | IN-SCOPE | E. testing; C. operability | `oc_runipd.py:5392`, `:6478`, `:7301-7322`; `runner_shared.py:3175-3181` | **NO EXISTING MECHANISM BOUNDS PER-ITEM DISPATCH, so E-06's loop bound is load-bearing rather than defensive.** `max_items_per_session` rotates the SESSION after N turns and never stops dispatch; the selection loop re-picks any satisfied `queued` item. The in-tree precedent is a MEASURED 201-dispatch orchestrator spin that the drain path could not catch | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 states that no cap exists, names why `max_items_per_session` is not one, cites the measured 201-dispatch precedent, and requires the bound stated; V-06 requires it pasted. New F-17 |
| PR-107 | MEDIUM | IN-SCOPE | Evidence accuracy; G. executability | `run_recovery.py:269-277`, `:295-303`; `run_engine.py:117-127`; grep exit 1 for `run_engine`/`run_state` on both drivers; 0 `ledger.jsonl` in 143 run dirs; spec `25kzda:28` | **OQ-03's "MAIN UNKNOWN" IS ALREADY ANSWERED AND THE ANSWER IS NO.** `plan_retry` needs a `RunEngine` over a hash-chained `ledger.jsonl`; neither driver mentions `run_engine` or `run_state` at all (so even the "comment mention" the question cites is gone), no run directory contains a ledger, and the step-state vocabularies are disjoint. E-04's alternative branch is the expected path, not the exception | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-03 rewritten with the measurements and an expected path; E-04 records the poor fit and points at sibling `xipfy1`, which owns the same substrate question and carries a blocking decision on it; V-04 requires the divergence justified and the sibling's state stated. New F-16 |
| PR-108 | MEDIUM | IN-SCOPE | F. UX; A. correctness | `outcome_str` is local to `render_run_summary_table` and compared only against its own literals; no match for the outcome words in any other module or test | **OQ-02 ASKED FOR A FACT THAT WAS CHEAP TO MEASURE AND LEFT IT OPEN.** It says to check whether anything parses the outcome string before changing its domain. Nothing does, so the choice is free and turns purely on reader comprehension | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 RESOLVED as reuse `PARTIAL`, with the measurement, the reason the counter-argument is weaker (E-01 independently surfaces the refusal on the row, so the outcome word is not the sole carrier), and explicit permission to diverge if documented. Conventions records the no-consumer fact |
| PR-109 | MEDIUM | UNDER-SCOPE | A. correctness; E. testing | `oc_runipd.py:4816`, `agy_runipd.py:2341`; `lane_containment.py:177-212`; measured message length 657 | **THE FEEDBACK CHANNEL DEPENDS ON ATTEMPT ORDERING, WHICH THE PLAN NEVER STATES.** The prompt reads `attempts[-1]`, and `finalize_refused` is written on the attempt record, so the re-dispatched turn sees the findings only while the refused attempt is still last. The projection does not truncate (verified), but a change to attempt bookkeeping would empty the channel while every flag still looked correct | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 states the mechanism, records the verified non-truncation, and explains why V-03's assert-on-the-prompt requirement is the protection. New F-21 |
| PR-110 | LOW | IN-SCOPE | Evidence accuracy | spec `:968` versus the plan's `:568` (which is the Section 4 heading); the other twelve citations verified exact | **THE BUDGET-0 CITATION IS OFF BY 400 LINES**, and it is the one rule whose off-by-one converts a deliberate opt-out into a silent retry | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 and V-04 carry `:968` with the correction noted, plus the frozen-value read rule (`is None`, not truthiness) and the measured `options.retry_budget: 2` present in real run state. New F-19 |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the `r2i1b1` overlap (PR-101) be resolved by the reviewer choosing a landing order, or escalated? | Escalate as blocking OQ-04 with three costed options | Choosing (a) `r2i1b1` first myself; choosing (b) this plan first myself; marking PR-101 as merely a merge-ordering note and leaving it non-blocking | Ordering two independently approved/reviewed plans is a maintainer scheduling call with a release-gate dimension (both carry `Blocks-Release: next`), and the answer changes E-01's edit AND possibly `Scope-Paths`, which the finalize gate reconciles. Leaving it non-blocking was rejected because an executor would then edit the same function `r2i1b1` is approved to rewrite | yes |
| D-2 | Is the false "exited 0" claim (PR-102) grounds for `REJECT - NEEDS REPLAN`? | No: correct it in place and keep the plan | REJECT - NEEDS REPLAN on the ground that the Concern misstates the incident | The display defect it is built on REPRODUCES exactly, and the dependency-gate defect (F-2) is real and independently verified. The exit-code error narrows the blast radius without invalidating either defect, so bounded edits repair it | yes |
| D-3 | E-02 versus E-03 conflict over the orchestrator injection sites: pick the resolution, or require the executor to decide? | Require a DECIDED, stated, tested treatment, with the constraint named (no Set killed `dead-children` while its child has budget) | Picking "treat refused as non-actionable-but-not-dead" myself; picking "leave sites 3 to 5 alone" myself; leaving the conflict unmentioned | Both resolutions are defensible and the choice depends on implementation shape that does not exist yet, so fixing one would over-constrain the executor. What was NOT acceptable was silence: the plan shipped an instruction ("enumerate every reader") that would surface the conflict mid-execution with no guidance. Naming the invariant is the smallest sufficient fix | yes |
| D-4 | OQ-02 (`PARTIAL` versus a new token): resolve from evidence or leave to the executor? | Resolve as reuse `PARTIAL`, permitting a documented divergence | Leaving it open; mandating `PARTIAL` with no divergence allowed | The question itself named the deciding fact ("check whether anything parses the outcome string"), and measuring it cost one search: nothing parses it. With the domain free, reuse wins on comprehension, and E-01 independently surfaces the refusal on the item row so the outcome word is not the sole carrier of meaning. Left divergence permitted because the requirement is only "not `COMPLETED`" | yes |
| D-5 | Should the reviewer fix the environmental suite failure (another party's gitignored `opencode-recovery/` tree)? | No: record it, name the cause and the tracking item, forbid touching it | Deleting the tree; adjusting the parity test's expected set; adding it to `.gitignore` differently | It is another party's gitignored session transcripts in a shared checkout, and the shared-checkout rule forbids cleaning up work that is not mine. It is already tracked as backlog `8kttqq` (`open`), and it is outside both this plan's `Scope-Paths` and a review's authority, since reviews change plans and not code | yes |
