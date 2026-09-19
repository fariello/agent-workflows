# Review findings: plan dy9ymn

- Subject-Id: dy9ymn
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `cf9c0d70`. The plan on disk was byte-identical to the sealed lane input (`diff`
reported no difference) and `git status --porcelain` was empty, so no pre-review snapshot was needed.
Structural preflight `aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0; after the
revisions `--phase review-finalize` also reports `clean`. Watermark 05 -> 06 (one E-item added).

THE DESIGN IS CORRECT AND ITS CENTRAL JUDGEMENT IS THE RIGHT ONE. Requiring evidence that something was
attempted before one item may block its Set, while refusing to loosen the cascade itself, is exactly the
right division, and the plan is honest about the cost of strictness. I verified the mechanical claims
against the code rather than accepting the prose, and these hold: the `--retry-incomplete` requeue shape
and `requeue_interrupted` are as described, including the latter's `is_indeterminate` refusal and the
recorded reason that "the two routes cannot disagree"; the `holds_work`-stays-True-after-`--no-ff`-merge
warning is real (the measured `BEFORE MERGE`/`AFTER MERGE` comment says so in terms); `ending_head` and
`ending_status` are written unconditionally before the disposition is computed, so E-01's inputs exist;
`_reset_item_for_retry` really does not exist, so F-6's warning is worth keeping; and the `graduated`
transition the gate prescribes really does work, writing its history message and preserving
`- Blocks-Release: next` (measured on a throwaway copy, `open -> graduated`).

WHERE THIS REVIEW SPENT ITS EFFORT: the plan points the executor at a seam that cannot fire, rests two of
its four evidence conditions on fields that are vacuous for the failure it measured, and asks for budget
behavior that has nothing to read. Each was measured.

**1. The cited requeue seam runs before the dispatch loop, so a retry placed there could never observe
an in-run turn.** E-04 said to reuse the requeue shape "as `oc_runipd.py:6455-6468` does". Locating those
lines inside `run_queue`: the function begins at absolute 6400, so 6455-6468 is function-relative 56-69,
and `while True:` is at function-relative 131. That block is the `--retry-incomplete` path, which runs
ONCE at resume time over statuses left by a previous invocation. A zero-work turn happens during the run,
at the `execute_item(...)` call at function-relative 298. So an executor who copied the shape into the
cited location would ship a retry that fires only for resumed runs and never for the measured case. The
plan's ORDERING claim is separately correct, and the window is more generous than it implies:
`cascade_dependency_blocked` sits at the TOP of the loop (function-relative 147), so it first observes
this turn's `partial` on the NEXT iteration, and anything after `execute_item` returns is early enough.
Split into a new E-06 with V-06 and a negative control, rather than edited into E-04, because it is a
distinct deliverable with its own test surface.

**2. Two of E-01's four conditions are true by construction for the shape the plan measured.**
`attempt["ending_head"]` and `attempt["ending_status"]` are assigned `git_head(repo)` and
`git_status(repo)`, where `repo` is the main checkout while the lane is `work_dir`. The measured failure
is an isolated lane turn, and a lane agent moves neither the main checkout's HEAD nor its working tree,
so `starting_head == ending_head` and an empty `ending_status` hold even for a lane that committed
substantial real work. They are genuine signals only for a `--no-isolate-worktree` turn. The plan
presents all four conditions as equally load-bearing ("any single sign of work refuses the verdict"),
which over-states the guarantee on the very shape it exists to fix, and V-02's demand for a negative
control per condition would produce two controls that cannot fail. The fix is available in shipped code:
`runner_shared.describe_lane` returns `commits_ahead` and `dirty` from
`worktree_lease.inspect_lane(repo, lane_id, base_commit=base)`, which is the only source that answers
"did THIS lane commit anything" and which also supplies the lane's own dirty state.

**3. The retry budget has a readable limit and no spend counter, so all three of E-04's budget behaviors
have nothing to read.** This is the finding I raised as PR-005 while reviewing the orchestrator `s0gnha`,
and reviewing it against this plan lets me state it more precisely, including correcting my own earlier
framing. READABLE: `freeze_run_policy_flags` resolves `--retry-budget` through `resolve_retry_budget` and
the effective integer lands in `state["options"]["retry_budget"]` at queue build, so reading the limit is
a one-liner, exactly as `integration_retry_limit` is read
(`int(options.get("integration_retry_limit", DEFAULT_INTEGRATION_RETRY_LIMIT))`). MISSING: no per-item
accounting of budget already spent. `grep` finds no read of the frozen `retry_budget` anywhere in
`agent_workflows/`, and `run_recovery.plan_retry` / `retry_budget_remaining` have zero callers outside
their own module because both require a `RunEngine` over a hash-chained `ledger.jsonl` that no driver run
writes. So "one retry within budget", "budget exhausted" and "`--retry-budget 0`" cannot be implemented
from what exists. My `s0gnha` PR-005 said there was "nothing to spend", which was too strong; the limit
is spendable, the counter is what is absent. The remedy is in the tree already: `runner_shared` solves
this for the sibling budget by keeping `attempts_used` on the ITEM (`integration_attempts`), which needs
no ledger, survives a resume in `state.json`, and adds no knob. E-04 now prescribes that, V-04 demands
the counter's value be pasted beside each outcome plus a case above one retry, and OQ-04 records the
division of labour with `xipfy1` so the two plans do not each assume the other owns the accounting.

**4. A self-carrier would have refused this plan's own finalize.** OQ-02 carried `- Carrier: dy9ymn`,
pointing at the plan that holds it. Measured by substituting an `executed` status for `dy9ymn` in the
live carrier index: the row flips from legitimate to failing with "carrier dy9ymn resolves only to a
terminal/hidden artifact (executed); nothing revisits it", at `error` severity (the plan's `- Date:` is on
or after the `20260919` cutover), evaluated at the `pre-transition` checkpoint that this plan's own gate
requires to report conforming. Worth contrasting with a sibling case I deliberately did NOT flag:
`skn8uk`'s `- Carrier: s0gnha` is legitimate, because the runner retires an orchestrator only after every
child is `executed`, so the parent is still pending when a child finalizes. A SELF-carrier has no such
protection. Converted to `Carrier-Declined` with the measurement recorded; re-measured at 0 failures. The
decline is also substantively right: OQ-02's owner is the executor and E-03 already requires the choice be
made and recorded during execution, so the obligation is discharged by execution rather than handed on.

**5. The gate prescribes an edit to an undeclared path.** The gate instructs the executor to set
`x7wfyx` `graduated`, which rewrites AND MOVES the file to `.aw/records/backlog/graduated/`. That path
appears in no `- Scope-Paths:` entry, so the finalize reconciliation sees an out-of-scope edited path and
refuses without a `--scope-reason`. The sibling `ty7w6o` DOES declare the same item at its `open/`
location, so the Set is internally inconsistent about it. Recorded as OQ-05 with both supported routes
rather than guessed, because the path CHANGES as a result of the edit being declared, which makes route A
awkward, while spec `25kzda` 5.5a makes an additive widening a finalize-time accept rather than a
refusal, so route B is a supported path and is the recommended default.

**6. E-02's refusals are almost entirely defence-in-depth, not live guards.** The zero-work branch is
entered only for an item whose disposition is the terminal `partial`, and each protected class carries a
different status at that point: a stopped item `interrupted`, a forced one `unknown_outcome`, a deferred
one `integration-deferred`, an unrun one `dependency-blocked` or `not-attempted`. A `review` action
cannot present as `partial` either, since its scorer returns `reviewed`, `approved` or `failed-safely`.
Keeping them is right (fail-closed redundancy is cheap, and a later change to the disposition vocabulary
would make them live), but presenting them as the safety property misdirects attention away from the
evidence conjunction, which is the property that actually prevents a retry over real work. This is the
same pattern I found in `skn8uk`, where the stopped and forced dispositions were already excluded upstream.

**7. All five `runner_shared.py` citations have drifted; every other file's are accurate.** Measured
across the plan's distinct citations: `:10573`, `:1141`, `:5564`, `:12483` and `:2544` all now land on
unrelated lines, while every `oc_runipd.py`, `agy_runipd.py`, `run_recovery.py` and `tests/` citation
resolves correctly, including `tests/test_turn_bounds.py:875`, `tests/test_defect_report.py:188` and
`tests/test_rununify_run_queue.py:165`. The asymmetry is the same one measured on both siblings: that one
file grew after authoring. Re-anchored by symbol.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. correctness; G. executability | `run_queue` begins at absolute 6400, so the cited `oc_runipd.py:6455-6468` is function-relative 56-69, while `while True:` is at 131, `cascade_dependency_blocked` at 147 and `execute_item(...)` at 298 | E-04 pointed the executor at the pre-loop `--retry-incomplete` block as "the requeue seam". That block runs once at resume time over statuses from a previous invocation, so a zero-work check placed there would never observe a turn that happens during the run, and the retry would silently only ever fire for resumed runs | C:Low; U:Low; S:Low; F:Medium-High; Overall:Low | FIXED | Split out as new E-06 (watermark 05 -> 06) naming the correct window (anywhere between `execute_item`'s return and the next iteration's cascade), with V-06 requiring an in-run fixture and a negative control that fails when the call is moved into the pre-loop block. E-04 keeps the shape guidance and now cross-references E-06 |
| PR-002 | HIGH | IN-SCOPE | A. correctness; E. testing | `attempt["ending_head"]`/`["ending_status"]` are `git_head(repo)`/`git_status(repo)` on the MAIN checkout while the lane is `work_dir`; the measured failure is an isolated lane turn. `runner_shared.describe_lane` exposes `commits_ahead`/`dirty` from `worktree_lease.inspect_lane` | Two of E-01's four conditions are TRUE BY CONSTRUCTION on an isolated turn, holding even for a lane that committed real work, so the conjunction is weaker than stated on exactly the shape it exists to fix, and V-02's per-condition negative controls would include two that cannot fail | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now reads the lane's own `commits_ahead`/`dirty` for an isolated turn, keeps conditions 2 and 4 for the shared-tree case, and must document which bite in which mode; V-02 now requires each control be built in the mode where it can actually fail, with the mode stated |
| PR-003 | HIGH | IN-SCOPE | C. architecture; G. executability | `state["options"]["retry_budget"]` is frozen by `freeze_run_policy_flags` and IS readable; no read of it exists anywhere in `agent_workflows/`; `plan_retry`/`retry_budget_remaining` have zero external callers (both need a `RunEngine` over an absent `ledger.jsonl`); contrast `int(options.get("integration_retry_limit", ...))` plus `item["integration_attempts"]`, the shipped per-item counter | E-04's three budget behaviors (0 / one / exhausted) require per-item spend accounting that does not exist, so the item could not be implemented as written. Corrects my own `s0gnha` PR-005 framing: the LIMIT is spendable, the COUNTER is what is missing | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 now prescribes counting on the item in the shipped `integration_attempts` shape (no ledger, resume-durable, no new knob) and explicitly does NOT use `plan_retry`; V-04 demands the counter's value beside each outcome plus a case above one retry; OQ-04 records the division with `xipfy1` |
| PR-004 | HIGH | IN-SCOPE | A. correctness; lifecycle | Measured by substituting `executed` for `dy9ymn` in the live carrier index: OQ-02's row flips to failing, "carrier dy9ymn resolves only to a terminal/hidden artifact (executed); nothing revisits it", at `error` severity (post-`20260919` date), evaluated at `pre-transition` | OQ-02 carried a SELF-carrier (`- Carrier: dy9ymn`), which resolves while pending and goes terminal exactly when the plan finalizes, so `check.ipd-uncarried-obligation` would refuse this plan's own lifecycle transition at the checkpoint its gate requires | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Converted to `Carrier-Declined` with the measurement and the contrast against a legitimate parent-carrier recorded; re-measured 0 failing. Substantively right too: E-03 already obliges the executor to decide and record the choice, so execution discharges it |
| PR-005 | MEDIUM | UNDER-SCOPE | G. executability; scope declaration | The `graduated` transition rewrites and MOVES the file (measured: `open -> graduated`, history written, `Blocks-Release` preserved); that path is in no `- Scope-Paths:` entry, while sibling `ty7w6o` declares it at `open/` | The gate prescribes an edit to an undeclared path, so finalize refuses without a `--scope-reason`, and the Set is internally inconsistent about which plan owns that record | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope check now states the measured move and its consequence; OQ-05 names both supported routes with route B (`--scope-reason` at finalize, per spec 5.5a's additive-widening accept) as the recommended default, since a moving path cannot be declared cleanly |
| PR-006 | LOW | IN-SCOPE | A. correctness; honest reasoning | The zero-work branch is entered only for a terminal `partial`; a stopped item is `interrupted`, forced `unknown_outcome`, deferred `integration-deferred`, unrun `dependency-blocked`/`not-attempted`; a `review` turn scores `reviewed`/`approved`/`failed-safely` | E-02 presents six refusals as the guard that keeps the change safe; none of them is currently reachable at the seam, so attention is drawn away from the evidence conjunction, which is the real guard. Same pattern found in sibling `skn8uk` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now states which refusals are unreachable and why, requires the code record it, and names the conjunction as the safety property; V-02 carries the same note |
| PR-007 | MEDIUM | IN-SCOPE | E. testing; G. executability | All five `runner_shared.py` offsets (`:10573`, `:1141`, `:5564`, `:12483`, `:2544`) land on unrelated lines; every `oc_runipd.py`, `agy_runipd.py`, `run_recovery.py` and `tests/` citation verified accurate | Five citations silently misdirect, including the `holds_work` warning and the budget-freeze reference an implementer would follow. None is out of range, so none announces itself | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Load-bearing anchors re-anchored by symbol and a standing conventions note records the measurement, the asymmetry and the instruction to re-derive by symbol |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The cited requeue seam cannot fire (PR-001). Correct E-04 in place, or add an item? | ADD a new E-06 (watermark 05 -> 06) owning the placement, with its own V-06 and negative control. | (a) Fix the citation inside E-04: rejected, placement is a distinct deliverable with its own test surface (an in-run versus resumed fixture), and burying it in an item about budget accounting is how it gets skipped. (b) Leave the citation and trust the executor to notice: rejected, the block is superficially the right shape, which is precisely why it would be copied. (c) Delete the citation entirely: rejected, it IS the correct shape to copy, just not the correct place. | `run_queue` starts at absolute 6400, so 6455-6468 is fn-rel 56-69; `while True:` at fn-rel 131; `cascade_dependency_blocked` at 147; `execute_item(...)` at 298. | yes |
| D-2 | Two of E-01's conditions are vacuous on an isolated turn (PR-002). Drop them, or re-scope them? | KEEP both for the shared-tree case, ADD the lane-facts reading for the isolated case, and require the predicate to document which conditions bite in which mode. | (a) Drop conditions 2 and 4: rejected, they are genuine signals for a `--no-isolate-worktree` turn, and dropping them would weaken the predicate in the one mode where they work. (b) Leave as written: rejected, the conjunction then over-claims on the measured shape and two of V-02's controls cannot fail. (c) Replace the attempt fields with lane facts everywhere: rejected, a shared-tree turn has no lane to inspect. | `ending_head`/`ending_status` assigned `git_head(repo)`/`git_status(repo)` with `repo` the main checkout and `work_dir` the lane; `describe_lane` exposes `commits_ahead`/`dirty` via `worktree_lease.inspect_lane`. | yes |
| D-3 | The budget has no spend counter (PR-003). Escalate as blocking (as I did on `s0gnha`), or prescribe the counter? | PRESCRIBE the item-local counter mirroring `integration_attempts`, and record the `xipfy1` relationship as non-blocking OQ-04. | (a) Escalate as blocking, consistent with my `s0gnha` PR-005: rejected on better evidence. There the plan was out of ledger so I could not fix it; here it is in ledger, and the repository already contains a shipped pattern that solves it without the absent ledger substrate, so the question is answerable from the repo and the workflow forbids asking the human what the repo answers. (b) Make `dy9ymn` depend on `executed:xipfy1`: rejected, `xipfy1` carries its own unresolved BLOCKER about the missing `RunEngine`/ledger, so the edge could stall this Set behind a plan that may not land as written. (c) Let the executor choose: rejected, the two routes differ in whether the plan can be executed at all. | `state["options"]["retry_budget"]` frozen and readable; zero reads of it in `agent_workflows/`; `plan_retry`/`retry_budget_remaining` zero external callers; `int(options.get("integration_retry_limit", ...))` plus `item["integration_attempts"] = attempts_used` as the shipped precedent. | yes |
| D-4 | OQ-02's self-carrier would refuse this plan's finalize (PR-004). Hand it to another artifact, or decline it? | DECLINE it, recording the measurement and why a decline is substantively correct. | (a) Hand it to `s0gnha`: rejected as dishonest, the parent does not revisit an implementation choice this plan's own E-03 obliges the executor to make and record. (b) Hand it to `x7wfyx`: rejected for the same reason; the backlog item is about the retry's existence, not the truncation signal's evidentiary role. (c) Leave it: rejected, it refuses the plan's own `pre-transition` gate. | Substituting `executed` for `dy9ymn` in the live carrier index flips the row to failing at `error` severity; `_CARRIER_TERMINAL_STATUSES` contains `executed`; `_CARRIER_CHECKPOINTS` is `pre-transition`; E-03 already requires the decision be recorded in code and V-03 requires it be quoted. | yes |
| D-5 | The gate edits an undeclared path (PR-005). Add it to `Scope-Paths` myself, or record the choice? | RECORD it as OQ-05 with both routes and a recommended default, and state the consequence in the Scope check so no executor hits the refusal uninstructed. | (a) Add the `open/` path to `Scope-Paths`: rejected as self-defeating, the transition MOVES the file, so the declared path is wrong immediately after the edit it declares. (b) Add the `graduated/` path: rejected, it does not exist at begin time, and declaring a path that is absent trips the declared-but-unmodified `--scope-ack` half of the reconciliation instead. (c) Say nothing: rejected, finalize would refuse with no instruction in the plan. | Measured `open -> graduated` move on a throwaway copy with history written and `Blocks-Release` preserved; the item absent from `- Scope-Paths:` while sibling `ty7w6o` declares it; spec `25kzda` 5.5a makes an additive widening a finalize-time accept rather than a never-retryable refusal. | yes |
