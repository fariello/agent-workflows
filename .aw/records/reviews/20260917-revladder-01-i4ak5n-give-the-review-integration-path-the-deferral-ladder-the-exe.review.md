# Review findings: plan i4ak5n

- Subject-Id: i4ak5n
- Subject-Type: ipd
- Reviewed-At: 2026-09-18
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `d3f418ff` in an isolated review lane, with the plan on disk byte-identical to the lane
input (`diff -q` clean), so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase
author` CONFORMED (exit 0) before revision; after revision the linter reports one `IPD-Q501`, which is the
blocking question this review raised doing its job.

THE DIAGNOSIS IS CORRECT AND I RE-PROVED IT INSTEAD OF INHERITING IT. F1's substance holds on BOTH hosts,
established by AST rather than by the plan's line ranges (which are already stale): the enclosing
`execute_item` containing the review integration call contains no reference to
`decide_integration_deferral`, `INTEGRATION_DEFERRED_STATUS`, `reattempt_deferred_integrations`, or
`deferred_integration_items`:

```text
oc_runipd.py  enclosing execute_item 6432-8110   all four symbols: False
agy_runipd.py enclosing execute_item 3211-4654   all four symbols: False
```

F2 verifies verbatim at `runner_shared.py:555` ("re-attempted once the base is clean"), and it is emitted
from `format_local_changes_refusal_reason`, which is called from the SHARED merge path both actions reach
(`:2295`), so the false promise really is shown to review operators. F5 verifies: `grep 'stash failed'`
across `agent_workflows/` and `hooks/` returns nothing. F4's self-correction is honest and exact:
`INTEGRATION_REFUSAL_TRANSIENT == INTEGRATION_BLOCKED_STATUS == 'integration-blocked'` (`:2344`, `:2347`)
while `INTEGRATION_REFUSAL_CONFLICT == 'merge-conflict'` (`:2350`), and `classify_integration_refusal`
returns True only for the transient kind (`:2390-2399`). The plan's refusal to touch that classifier, and
its insistence on inheriting all four terminal arms, are both right.

BUT THE PLAN'S CENTRAL PREMISE IS WRONG, AND IT IS THE PREMISE THAT SETS ITS SCOPE. The plan says "this
plan wires a caller in; it does not build a mechanism" and its Scope promises not to change "the ladder's
rung logic". Measured, the ladder is ACTION-BLIND in three places, so entering it as a review is not a
wiring change. I found this by reading what the ladder actually does with a deferred item rather than by
reading its docstring, which is where the plan stopped.

FIRST (PR-001, BLOCKER): THE RE-ATTEMPT WOULD REVALIDATE THE REVIEW. The per-host adapter binds
`integrate=_integrate`, and `_integrate` calls this host's execute wrapper, which pins
`action_kind=INTEGRATION_ACTION_EXECUTE` (`oc_runipd.py:2440-2448`); `action_kind ==
INTEGRATION_ACTION_EXECUTE` is exactly what triggers `execute_merge_and_revalidate_gate`
(`runner_shared.py:2204`). The review path deliberately uses `integrate_review_lane_branch`, which passes
`INTEGRATION_ACTION_REVIEW` and takes NO `validation_runner`, so that "a caller therefore CANNOT supply a
synthetic validation result through this path even by mistake, which is what OQ-01's load-bearing line
requires" (`oc_runipd.py:2451-2470`). Measured:

```text
_integrate references: ['integrate_lane_branch']
integrate_lane_branch params: [repo, handle, id6, validation_runner, host_label, run_checked, action_kind]
action_kind has a default: False        INTEGRATION_ACTION_EXECUTE: execute   ..._REVIEW: review
oc integrate_review_lane_branch signature: (repo, handle, id6)   -> no validation_runner, deliberately
ladder passes validation_runner_for=...: True
```

So E-03's status write alone makes the RETRY do the one thing the first attempt structurally forbids. The
`ajxr5d` OQ-01 ruling would hold on attempt 1 and be violated on attempt 2, which is the worst shape for a
safety property.

SECOND (PR-001 too, same root): THE SUCCESS PATH WOULD CORRUPT THE REVIEW ITEM. `finish_integrated=_finish`
references `item["status"] = "executed"`, `process_backlog_close`, `teardown_lane_if_classified` and
`resolve_plan_path` (measured by inspecting the adapter body; `oc_runipd.py:2524-2578`). A review executes
no plan and carries no backlog item, so three of those four are wrong by construction.

THIRD (PR-002, BLOCKER, and the structurally deepest): THE SWEEP LANE IS SHARED WHILE THE LADDER IS
PER-ITEM. There is exactly one sweep lane per run (`review_sweep_lane_id(run_id)`,
`runner_shared.py:1348-1354`), recorded at RUN level under `REVIEW_SWEEP_LANE_KEY`, and
`lane_records_including_sweep` says so in terms that settle it: "NOT an item's id6, because the lane belongs
to no ITEM" (`:1529-1531`). The ladder rebuilds a per-ITEM handle from `preserved_branch` /
`preserved_lane_id` / `preserved_base` and on success tears the lane down and deletes those keys
(`oc_runipd.py:2543-2570`). Measured that the selection filter is action-blind and DOES pick a review item:

```text
deferred_integration_items -> [('aaaaaa','review'), ('bbbbbb','execute')]
filter is action-BLIND: a review item IS selected: True
```

So two deferred reviews resolve to the same branch and the first success retires the lane the second still
needs, which is exactly the hazard `teardown_review_sweep_lane` already names for the per-item path:
"putting it on the per-item path would destroy the lane the NEXT review needs"
(`lane_containment.py:3356-3357`). The plan's authored E-04 asked only whether the lane is
RECONSTRUCTIBLE, which is the half that cannot fail; it did not ask what happens to the OTHER review.

I ALSO RESOLVED THE SPEC QUESTION THE PLAN LEFT FOR THE EXECUTOR, because the repository answers it. The
spec's ladder requirement (`25kzda:163`, `Status: approved`) is scoped to the REFUSAL CONDITION, not to the
action: "the disposition ladder applied when an integration is REFUSED because the main tree holds un-owned
dirty paths overlapping the incoming change ... The ladder applies ONLY to that transient dirty-overlap
refusal." It enumerates what the ladder must never apply to and says nothing restricting it to execute
turns, and it does not enumerate the statuses a review turn may reach. So this is a delivery gap, no
amendment is required, and no `.spec.md` belongs in `Scope-Paths`. The plan's own note that `63425h` also
edits that spec is now stale in a useful direction: `63425h` is `executed`, so its amendment is already in
the tree.

SMALLER CORRECTIONS. The plan names `decide_integration_deferral` as the function to reuse, but that is PURE
and is called only from inside `record_integration_refusal`; no driver calls it, and the shared write site
both hosts already use is `record_integration_refusal` (`:2688`), which also owns the durable attempt count
and the rung-naming event (PR-005). The recovery verb E-06 tells the operator to print,
`aw <host> run integrate <id6>`, does not exist: the alias is registered as `integrate` directly under the
host group (`cli.py:3929`), i.e. `aw oc integrate <id6>`, and `rl67b0` is `executed` rather than approved, so
the verb is live today (PR-004). And every line number in the plan is off by roughly 40 lines (PR-006).

WHAT I FIXED. Goal: added the three measured action-blindness findings with their transcripts and corrected
the "pure wiring" self-description. E-03: retargeted to `record_integration_refusal`. NEW E-04
(action-correct re-attempt) and NEW E-05 (shared-lane rule); old E-05/E-06/E-07 renumbered to E-06/E-07/E-08
with dependencies rewired; `Highest E allocated` 07 -> 08. V-04 rewritten to demand a raising validation
runner and a post-success item dump; NEW V-05 requires TWO deferred reviews in one run; V-07 requires the
verb be proven to parse; V-08 added. F8..F12 added, F7 corrected. Required tests gained the bare-run rule,
the 31-failure worker-lane baseline, the action-correctness item, the two-review item, and an
execute-path-unchanged item. Spec-sync rewritten with the requirement quoted and the question resolved.
Deferred section narrowed so the "rung logic untouched" bullet cannot be read as authority to skip E-04.
Gate now names four must-nots including "do not ship E-03 without E-04/E-05". OQ-02 raised blocking.

WHAT I DID NOT DO. I changed no code, test or spec; my probe script was throwaway and is deleted. I did not
choose the sweep-lane design (OQ-02) and I did not answer OQ-01, which remains the maintainer's.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | A. correctness; D. domain invariants | `oc_runipd.py:2440-2448` vs `:2451-2470`; `runner_shared.py:2204`; `oc_runipd.py:2524-2578`; measured `_integrate references: ['integrate_lane_branch']`, `_finish references: [status=executed, process_backlog_close, teardown_lane_if_classified, resolve_plan_path]` | **THE LADDER'S RE-ATTEMPT IS EXECUTE-SPECIFIC, so E-03's status write alone makes the retry REVALIDATE the review and mark it `executed`.** The adapter pins `action_kind=INTEGRATION_ACTION_EXECUTE`, which is precisely what triggers the revalidation gate the review path skips "by NOT RUNNING" per `ajxr5d` OQ-01; and the success path writes `status = executed` and closes a backlog item, neither valid for a review. | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | FIXED | New E-04 owns action-correctness: dispatch a review re-attempt to `integrate_review_lane_branch` and give it a review success path. V-04 rewritten to prove it with a validation runner that RAISES if called (not a passing verdict) plus a post-success item dump showing no `executed`, no backlog close, no plan-path resolution, plus the execute path unchanged. The gate now forbids shipping E-03 without E-04. Not escalated as blocking because the fix direction is determined by the code (the review wrapper already exists); only its scope needed correcting. |
| PR-002 | BLOCKER | UNDER-SCOPE | C. architecture; A. correctness | `runner_shared.py:1348-1354`, `:1529-1531`; `oc_runipd.py:2543-2570`; `lane_containment.py:3356-3357`; measured `deferred_integration_items` selecting a `review` item | **ONE SWEEP LANE IS SHARED BY EVERY REVIEW WHILE THE LADDER IS PER-ITEM AND TEARS THE LANE DOWN ON SUCCESS.** `lane_records_including_sweep` states "the lane belongs to no ITEM". With two deferred reviews both resolve to the same branch and the first success retires the lane the second needs, converting a recoverable stranding into a lost one, which is the hazard `teardown_review_sweep_lane` names for the per-item path. | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | OPEN | ESCALATED as OQ-02 (`Blocking: yes`, `Finding: PR-002`). Not decided by me: option (c) would reverse the recorded `ajxr5d` OQ-02 decision and re-open the `lanesess xd9sll` session hazard, and option (a) changes when a lane is reclaimed. Four options recorded with costs; my read (a) smallest, (d) most robust, (c) not this plan's to take. Meanwhile new E-05 carries the work, V-05 mandates a TWO-review test because one cannot expose the collision, and the gate forbids shipping without it. |
| PR-003 | HIGH | IN-SCOPE | G. plan executability (a false self-description that sets scope) | the Goal's "wires a caller in; it does not build a mechanism"; the Scope's "Does NOT change the ladder's rung logic"; PR-001 and PR-002's evidence | **THE PLAN DESCRIBES ITSELF AS PURE WIRING, WHICH IS FALSE AND WOULD HAVE CAPPED THE EXECUTOR'S SCOPE.** Taken literally, an executor ships E-03 and stops, producing a retry that revalidates reviews, marks them executed, and destroys a second review's lane; each is worse than today's honest refusal. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | Goal now states the three action-blindness findings with transcripts and says plainly that "simply not wired" understates the job. The deferred bullet claiming rung logic is untouched is NARROWED to distinguish the RUNGS (genuinely untouched) from the ADAPTER (must change). Scope check records this as the review's main structural finding under UNDER-SCOPE. |
| PR-004 | HIGH | IN-SCOPE | F. UX / honest documentation | `cli.py:3929`, `:11544`; `rl67b0` front matter `Status: executed`; `attention.py` lane_remedy_hint's "Do not print a verb that does not exist" | **E-06 TOLD THE OPERATOR TO RUN A COMMAND THAT DOES NOT EXIST.** `aw <host> run integrate <id6>` is not a verb; the alias is `integrate` directly under the host group (`aw oc integrate <id6>`, spelled out `aw oc runipd integrate <id6>`). The plan also called `rl67b0` "approved" when it is `executed`, i.e. the verb is live today. Printing a failing verb mid-incident is worse than printing none, a rule this repository already codified elsewhere. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-07 carries the correct spellings plus an instruction to verify against the parser at execution HEAD; V-07 refuses the item without evidence the verb parses. F7 corrected to `executed` with the registration cited. |
| PR-005 | MEDIUM | IN-SCOPE | C. architecture (wrong reuse target) | `grep decide_integration_deferral agent_workflows/` -> `runner_shared.py` only; `:2459` (pure) called only from `:2724`; both hosts call `record_integration_refusal` at `oc_runipd.py:7796` / `agy_runipd.py:4349` | The plan names `decide_integration_deferral` as the function to reuse, but it is PURE and no driver calls it. The shared WRITE site is `record_integration_refusal`, which owns the durable attempt count, the status write and the rung-naming event; wiring to the pure function would reimplement all three. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 retargeted to `record_integration_refusal` with the reason and the grep evidence stated; F11 added; conventions gained a bullet distinguishing the pure decision from the shared write site. |
| PR-006 | LOW | IN-SCOPE | A. correctness (stale citations) | authored `:7591-7625` vs actual call at `oc_runipd.py:7631`, refusal block `:7654-7669`; `reattempt_deferred_integrations` at `:2779` not `:2714`; `decide_integration_deferral` at `:2459` not `:2400` | Every cited line number is stale by roughly 40 lines, in a plan whose own E-01 says "refuse to proceed on this plan's line numbers". Harmless individually, but an executor checking a range and finding unrelated code may doubt the finding. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three corrected with the stale value noted so a reader can tell a correction from a typo; F1's substance re-established by AST on both hosts rather than by range; F12 records the staleness. |
| PR-007 | LOW | UNDER-SCOPE | E. testing (a false red baseline) | backlog `770fkp`; measured `31 failed, 7866 passed` bare in a lane this session | Required test 1 said "bare, pasted summary line, compared against the pre-execution baseline" with no note that a managed worker lane fails 31 lifecycle tests BY DESIGN, and no warning against adding flags (a second `-q` suppresses the summary the item requires). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required test 1 now states the bare-run rule with the reason, cites `770fkp`, and gates on NO NEW failures against a baseline taken in the same tree. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The ladder's adapter is execute-specific. Add the action-correctness work myself, or escalate it? | FIX IT IN PLACE as new E-04, because the code determines the answer: the review wrapper `integrate_review_lane_branch` already exists and is already the thing the first attempt uses, so "dispatch the re-attempt to it" is the only correct target, not a judgement call. | (a) Escalate as blocking, rejected: it would stall the plan on a question the repository already answers, and the plan cannot be safely executed without the fix either way. (b) Leave it as a note for the executor, rejected outright: the authored scope explicitly disclaims rung-side work, so a note would be read as out of scope and skipped, shipping a retry that revalidates reviews. | `oc_runipd.py:2440-2448` vs `:2451-2470`; `runner_shared.py:2204`; the `ajxr5d` OQ-01 ruling quoted in the review wrapper's docstring | yes |
| D-2 | Two deferred reviews collide on one sweep lane. Pick the design myself? | NO. Escalate as OQ-02 blocking, while adding E-05 to carry whichever design is chosen and V-05 to mandate the two-review test regardless. | (a) Choose option (a) (never tear down per item) myself, rejected though it is my recommendation: it changes WHEN a lane is reclaimed, which is operator-visible and interacts with the interrupt reclaimer. (b) Choose option (c) (one lane per review), rejected firmly: it reverses the recorded `ajxr5d` OQ-02 decision and re-opens the `lanesess xd9sll` session-binding hazard, which is not a side effect a wiring plan should cause. (c) Say nothing and let the executor discover it, rejected: the discovery would come after a real review's work was lost. | `runner_shared.py:1348-1354`, `:1529-1531`; `lane_containment.py:3356-3357`; `oc_runipd.py:2543-2570` | yes |
| D-3 | The plan left the spec question ("does the ladder apply to review turns?") for the executor. Test it now? | TEST IT NOW AND RECORD THE ANSWER: no amendment is required, because the spec scopes the ladder to the REFUSAL CONDITION and not to the action. | (a) Leave it to the executor as authored, rejected: it decides whether a `.spec.md` must be declared in `Scope-Paths`, and an undeclared spec edit is an unannounced contract change, so leaving it open leaves the plan's risk posture undetermined. (b) Declare the spec defensively, rejected: declaring a file this plan does not need to edit would make the runner announce a spec edit that never comes and would need a `--scope-ack` at finalize. | `25kzda:163` quoted, `Status: approved`; the requirement's own enumeration of what the ladder must never apply to | yes |
| D-4 | Should PR-001 be blocking, given PR-002 already is? | NO, FIXED rather than escalated, because its remedy is determined while PR-002's is a choice. | (a) Escalate both, rejected: two blocking questions where one has a single evidence-determined answer trains the maintainer to rubber-stamp. (b) Downgrade PR-001 to HIGH, rejected: shipping E-03 without E-04 actively violates a safety property the first attempt guarantees, which is BLOCKER-shaped even when the fix is obvious. | the existence of `integrate_review_lane_branch` as the sole correct target; the `ajxr5d` OQ-01 rule | yes |
| D-5 | Verdict and readiness? | `REVIEWED - OPEN QUESTIONS`, readiness `no-go`, `Status: reviewed`. | (a) `APPROVE WITH REVISIONS APPLIED`, rejected: one BLOCKER remains OPEN as OQ-02. (b) `REJECT - NEEDS REPLAN`, rejected: the diagnosis is exact and independently re-proved, the mechanism to reuse is the right one, and the remedy is one maintainer answer plus two added E-items, not a new approach. | workflow verdict/readiness tables; PR-002 `OPEN`; the verified F1/F2/F4/F5 | yes |

### Escalation of the irreversible decisions

None of this round's five decisions is `Reversible: no`: each is undone by editing the plan, and I changed no
code, test or spec. What they DEFER is not symmetric, though, and that is why OQ-02 blocks: a wrong
sweep-lane choice destroys a completed review turn's work (the measured cost of one such loss in the
incident this plan cites was $13.27 and 32m46s, and that one was recoverable by hand only because the branch
survived). A design in which the first re-attempt retires the shared lane would make the second review's
loss unrecoverable, so it is deliberately not authorized by me.

### Honest limits of this review

- MY THREE CENTRAL FINDINGS COME FROM A PROBE SCRIPT I WROTE AND DELETED. The transcripts are pasted
  verbatim from a real run in this lane, but a re-verifier must rebuild it. It did three things: inspected
  the `_integrate`/`_finish` adapter bodies textually inside `oc_runipd.retry_deferred_integrations`, read
  `inspect.signature` for `integrate_lane_branch` / `integrate_review_lane_branch` /
  `reattempt_deferred_integrations`, and called `deferred_integration_items` on a synthetic three-item state.
- I DID NOT RUN A DRIVER, DEFER A REAL REVIEW, OR RE-ATTEMPT ONE. Every claim about what the retry WOULD do
  is derived from the adapter bindings plus the `action_kind` branch, not from observing a deferred review
  recover. That is precisely why V-04 and V-05 demand live evidence and why I strengthened rather than
  relaxed them.
- PR-002's TWO-REVIEW COLLISION IS REASONED FROM THE LANE MODEL, NOT DEMONSTRATED. I proved the filter is
  action-blind and that the lane is run-scoped and that `_finish` tears the lane down; I did not construct a
  run with two deferred reviews and watch the second fail. The conclusion follows from those three facts,
  but it is an inference.
- I DID NOT VERIFY THE INCIDENT RUN. `run-20260917T193010Z-1207513` is not present in this workspace
  (`.aw/records/runs/` is gitignored and empty here), so F3's $13.27 / 32m46s figures, the `COMPLETED` verdict
  and the `1 reviewed` count are the author's and are unverified by me. What I could verify is that the
  branch name shape is real and that the refusal text and its false promise exist in the code.
- I DID NOT RE-RUN THE FULL SUITE. I changed no code. The `31 failed, 7866 passed, 3 skipped, 2 xfailed`
  baseline I cite for PR-007 was measured earlier in this session at a nearby HEAD; the counts at THIS HEAD
  are unverified by me, which is why the plan now requires the executor to take its own baseline.
- I DID NOT ESTABLISH WHETHER `aw <host> integrate` ACCEPTS A REVIEW LANE. Its help text describes a lane
  that "already finished, verified and finalized", which is execute-shaped. I recorded that as an explicit
  deferral in the plan rather than resolving it, because changing that verb is `rl67b0`'s territory.
- I DID NOT DECIDE OQ-01 (shared vs separate retry budget) OR OQ-02, and I touched no other plan.

## Round 2

Reviewed at HEAD `7a28ed11` with the maintainer.

OQ-02 RESOLVED AND PR-002 DISCHARGED. The maintainer ruled for Option (a): make the re-attempt NEVER tear down a sweep lane during re-attempt execution; leave retirement to the existing coordinator-owned `teardown_review_sweep_lane` at the end of the run. This preserves the `ajxr5d` OQ-02 design ("one lane for the whole sweep", preventing any session-sharing hazards recorded in `lanesess xd9sll`), keeps the per-item path safe from retiring a shared sweep lane that subsequent reviews need, and is fully compatible with E-05 and V-05. OQ-01 is also resolved to use the shared budget (`--integration-retry-limit`). All blocking questions on plan `i4ak5n` are resolved; finding PR-002 is dispositioned FIXED.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-002 | BLOCKER | UNDER-SCOPE | C. architecture; A. correctness | `runner_shared.py:1348-1354`, `:1529-1531`; `oc_runipd.py:2543-2570`; `lane_containment.py:3356-3357` | **ONE SWEEP LANE IS SHARED BY EVERY REVIEW WHILE THE LADDER IS PER-ITEM AND TEARS THE LANE DOWN ON SUCCESS.** | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | FIXED | Resolved by maintainer ruling for Option (a): re-attempts never tear down a sweep lane, preserving it until the coordinator teardown at run end. E-05 and V-05 enforce this contract. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-201 | OQ-02 resolution and PR-002 disposition | Option (a): re-attempts never tear down the sweep lane; promote readiness to `go-pending-approval` | Options (b), (c), (d) | Preserves ajxr5d OQ-02 single-sweep-lane invariant without session hazard | yes |
| D-202 | OQ-01 resolution | Shared budget with execute path (`--integration-retry-limit`) | Separate retry budget | Simplest operator interface; consistent retry bound | yes |
