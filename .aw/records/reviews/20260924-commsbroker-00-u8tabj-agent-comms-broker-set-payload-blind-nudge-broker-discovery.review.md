# Review findings: plan u8tabj

- Subject-Id: u8tabj
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed the ORCHESTRATOR of Set `commsbroker` (Order 00). Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE semantic review, and
`--phase review-finalize` conforms after the revisions, so nothing below is structural. The plan file
was committed and unchanged at review start (`git status --porcelain` empty; tip
`b45d51d0 plans(u8tabj): write the commsbroker orchestrator rows in the typed grammar (IPD-S407)`), so
no pre-review snapshot was needed.

SCOPE OF THIS REVIEW, stated because it decides what is and is not a finding. This is an
ORCHESTRATOR: it holds three child-confirmation rows and contributes no code, no test, and no record.
So the review asks orchestrator questions - is the sequencing right, are the declared dependencies
real, is every deliverable owned by exactly one child, is every completion criterion owned by
something that actually checks it, and does the gate carry an execution contract - and does NOT
re-review the children's own content. All three children (`nomhl1`, `ex539u`, `ozcfjr`) read
`- Status: to-review` and none has been reviewed, so the Set cannot execute end to end on this
approval alone; that is now stated in the plan's gate rather than left implicit.

THE ORCHESTRATION IS SOUND AND THE STRUCTURE IS RIGHT, which is why this is a revisions-applied pass
rather than a replan. Verified independently:

```text
Kind: orchestrator            (own first `- Kind:` bullet, not a containment scan)
Highest E allocated: 03       3 E-items, 3 V-items, 1:1 bijection
IPD-S407 rows                 orchestrator_row_conformance -> applies=True conforming=True, 3/3 rows
                              E-01 nomhl1 executed (Depends on: none)
                              E-02 ex539u executed (Depends on: E-01)
                              E-03 ozcfjr executed (Depends on: E-01)
child table                   3 rows, Id column present, all three id6s resolve to real pending files
child Item-Dependencies       nomhl1: none | ex539u: executed:nomhl1 | ozcfjr: executed:nomhl1
                              -> agrees with the parent's E-02/E-03 `Depends on: E-01` edges
```

FIVE FINDINGS, ALL FIXED IN PLACE. One was a deterministic `error`-severity repository finding the
plan actually carried (PR-001), which is the only one a tool would have caught. Two are claims that
are FALSE as written and would have sent an executor into a wrong conclusion (PR-002, PR-003). One is
a Set-level completion criterion NO child checks, recorded rather than papered over (PR-004). One is a
materially incomplete gate (PR-005).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G (executability) / repository rule | `check_engine.evaluate_durable_carrier` driven on this file returned 1 finding, `check.ipd-uncarried-obligation`, severity `error`; `check_engine.carrier_severity_for_plan(text)` -> `error` (plan `- Date: 2026-09-24` is after `CARRIER_CUTOVER_DATE == "20260919"`) | OQ-01 CARRIED NO DURABLE CARRIER, so `aw check plans` reported an `error`-severity finding against this plan. The plan's `## Deferred / out of scope` rows were correctly carriered but its open question was not, and the rule covers both. The consequence the rule exists to prevent applies exactly here: once this plan reaches `executed` it classes `done` in `aw attention`, and OQ-01 would vanish with no record. All three children carry the identical defect (each has one uncarriered OQ-01), which is a finding against THEM and is not fixed here. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Carrier-Declined:` added to OQ-01 stating that its default holds with NO action because child 03's dependency edge enforces it mechanically, so there is no outstanding work to hand off. Re-measured after the edit: `evaluate_durable_carrier` returns 0 findings. The new OQ-02 was authored carrying its own `- Carrier-Declined:` from the start. |
| PR-002 | HIGH | IN-SCOPE | E (testing/verification) | `.aw/records/plans/pending/20260924-commsbroker-03-ozcfjr-...ipd.md` E-04 ("Add one paragraph to `engine._COMMS_README_TEMPLATE`" containing `python3 -m agent_workflows.comms_acks ack <msg-id> read --by <proj.agent>`); `agent_workflows/engine.py` `_COMMS_README_TEMPLATE` | THE CROSS-IPD OPT-IN CHECK WAS WRONG AND WOULD REPORT A FALSE POSITIVE ON ITS OWN SET. It read: `grep -rn "comms_broker\|comms_acks" agent_workflows/ --include=*.py` shows no importer, "which proves nothing is auto-started or installed". After child 03 executes, `engine.py` MATCHES that grep by design, because child 03's own E-04 writes the module invocation into the README template that lives in `engine.py`. So the Set's single opt-in proof fails on the Set's own intended end state, and a substring grep never proved "importer" in the first place (it matches prose, comments, and template text). | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Replaced with three checks that mean what the criterion wants, each to be RE-DERIVED at execution: an anchored import grep (`^\s*(from\|import)\s+.*comms_(broker\|acks)`) that must be empty; a grep of `pyproject.toml` and `command_surface.py` that must be empty (which is what actually rules out a console entry point and a declared CLI leaf); and an explicit statement that a hit in `engine.py` is legitimate ONLY for child 03's declared README paragraph, any other hit being an auto-start defect. Both greps measured EMPTY at review, establishing the baseline. |
| PR-003 | MEDIUM | IN-SCOPE | A (correctness) / G | No child plan contains any `aw backlog` instruction (`grep -rn "backlog set done\|aw backlog" .aw/records/plans/pending/20260924-commsbroker-0[123]-*.ipd.md` -> no match); `ipd_lifecycle` calls nothing in `backlog` | THE BACKLOG-CLOSURE CLAIM ASSERTED A ROUTE THAT DOES NOT EXIST. The plan said the three items "are closed by their own children's executors", but no child carries a closing instruction and `aw ipd finalize` performs no backlog write, so on the stated route the three `graduated` items are never closed and stay live in `aw attention` forever. The plan also gave no closer the command, which matters because a release-gated item's bare close fails closed. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Rewritten to state plainly that nothing in the Set closes them and that closure is a FOLLOW-UP after the Set completes, in the shape plan `wj5b53` already uses for a citation that does not exist until its plan is terminal. Three concrete `aw backlog set done ... --evidence ...` commands supplied. MEASURED and recorded: none of the three carries `- Blocks-Release:`, so `evaluate_blocking_close` returns `legitimate=True` via DE-GATED for all three and a bare close would also pass; `--evidence` is supplied anyway so the route stays correct if a gate is ever added. |
| PR-004 | MEDIUM | UNDER-SCOPE | G (live-artifact criteria / coverage) | The plan's `## Completion criteria`; `nomhl1` V-07, `ex539u` V-06, `ozcfjr` V-06 (each checks only its OWN spec bullet); `ipd_lifecycle.ROLLUP_OMITTED_GATES` | A SET-LEVEL COMPLETION CRITERION WAS OWNED BY NOTHING. "The comms spec's Deferred list ... still names mDNS, cross-box delivery and `Depends-On`" is a property of the FINAL merged spec, and no child can assert it: all three delete a different bullet from the same list and 02/03 have no order between them, so no child is structurally last. Because this is an orchestrator whose retirement SKIPS the pre-transition E/V checkpoint, an unowned criterion parked here would be reported satisfied having never been checked - and the correct fix is NOT to add an item to this parent, for exactly that reason. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Completion criteria rewritten as a table with an explicit OWNER column naming the child `V-*` that demands evidence for each, with `none` recorded honestly for the residual-Deferred criterion. New OQ-02 records the gap, states the recommendation (accept the per-child checks), states what IS covered (`ex539u` V-06 checks mDNS; `Depends-On` and cross-box sit in a fourth bullet no child touches, so nothing deletes them), names the narrow residual risk (a hand-resolved merge conflict), and names the correct remedy SHAPE if the maintainer wants more: a new Order 04 child, never an item on this parent. |
| PR-005 | MEDIUM | IN-SCOPE | G (executability) | The plan's `## Approval and execution gate` (three sentences before the fix); sibling orchestrator `zngiya` in the same `pending/` tree carries the full contract | THE GATE CARRIED ALMOST NO EXECUTION CONTRACT: human approval, a one-line retirement note, and "Nothing is pushed". Missing were the scope fence, the honesty rule, the commit discipline, the disposition of the open questions, and - most consequentially - the CONDITIONAL ownership of the lifecycle transition. As written it told a runner-path executor to "finalize with `aw ipd finalize`", which is wrong under a runner: `runner_shared.dispatch_orchestrator_item` -> `ipd_lifecycle.retire_orchestrator` retires this plan with no agent turn. It also did not tell a human approving the Set that child 01's E-01 starts a real local `opencode serve` process, which is the one thing about this Set a human might decline. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten to carry: per-child approval (with all three children measured `to-review`); OQ-01/OQ-02 dispositioned as non-blocking and explicitly not to be re-decided mid-run; what a human is actually approving (the loopback spike process, never a human's instance); a DECLARATION-style scope fence (make-then-justify with `--scope-reason`/`--scope-ack`, no stop-over-scope, with the genuinely-unsafe exception naming the 02/03 spec-hunk conflict and its correct response); the three declared spec edits the runners will announce; the hard-MUST honesty rule; path-scoped `aw commit` plus the shared-checkout `git diff --cached` check and never-push; the CONDITIONAL transition (runner retires with no agent turn, do NOT run `aw ipd finalize` under a runner, no hand-rolled `git mv`, executor owns it only by hand); and why the skipped checkpoint is tolerable here, tied to PR-004's recorded gap. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should this review also fix the identical uncarriered-OQ `error` finding (PR-001) in the three children, since all four plans carry it and `aw check plans` reports all four? | No. Fix it in the parent only and name it in the parent's finding as a defect of the children that is NOT fixed here. | Fixing all four. Rejected: it would edit three plans that are not in this review's ledger, and a reviewer editing a plan it did not review leaves an unexplained diff with no findings record behind it. | `plan-review` Step 0.1: the ledger contains ONLY plans explicitly named in the invocation plus any a documented eligibility rule adds; a file referenced only as evidence is not in scope. No repository rule adds a Set's children to a review of its parent. | yes |
| D-2 | The residual-Deferred criterion (PR-004) is owned by nothing. Should the fix be an E-item on this parent that reconciles the spec at the end? | No. Record it as an open question with a recommendation and name an Order 04 CHILD as the remedy shape if the maintainer wants coverage. | (a) Add an E-item to this parent. Rejected: `ipd_lifecycle.ROLLUP_OMITTED_GATES` skips the pre-transition E/V checkpoint on rollup, so a parent-only item is marked complete having never been performed - the precise failure the orchestrator coverage gate exists to prevent. (b) Author the Order 04 child during this review. Rejected: authoring a new plan is not a review act, and the Set's shape is the maintainer's scope call. | `AGENTS.md` ("if you are authoring a Set and find yourself writing a STEP on the Order-0 plan that no child covers, do NOT delete it: ADD A CHILD for it"); `ipd_lifecycle.ROLLUP_OMITTED_GATES["pre-transition-ev-checkpoint"]`; `runner_shared` orchestrator probe gate and `probe_refusal_remedy`, whose remedy is literally "ADD A CHILD". | yes |
| D-3 | Children 02 and 03 both edit the same spec hunk with no order between them. Is that a BLOCKER requiring a declared `03 depends on 02` edge? | No. Document the bounded hazard, its refusing failure mode, and the mechanical fix; do NOT add the edge. | Declaring `- Item-Dependencies: executed:ex539u` on child 03. Rejected: it asserts a dependency that does not exist (child 03 touches `comms_acks.py`, not the registry) and would make child 03 unreachable if child 02 were ever retired. | Per-item isolated worktrees are the default (`isolate_worktree`, opt out with `--no-isolate-worktree`) and `ipd_lifecycle.land_worktree_commit` REFUSES rather than clobbers, so the worst case is a refused merge naming the item, not a lost spec edit. `AGENTS.md` is explicit that file overlap between plans is not a runtime hazard to warn a maintainer about. | yes |
| D-4 | The plan's Order numbering does not match `ssmov3`'s "IPDs 2, 3, and 4" numbering (Order 02 is `ssmov3` IPD 4, Order 03 is IPD 3). Is that an error to renumber, or a presentation defect? | Presentation. Keep the Orders and add an explicit mapping table to the Concern. | Renumbering the Set so Order matches `ssmov3`'s IPD numbers. Rejected: the id6s are already cited in three backlog items' `- Graduated-To:` and in three plan filenames, and the dependency edges are correct as they stand; renumbering would churn four filenames to fix a reading hazard that one sentence fixes. | The Concern listed the three follow-ups in `ssmov3`'s order while the child table lists them in Order sequence, so a reader matching by position maps `ex539u` to agent acks. Both children's `- From-Backlog:` fields disambiguate it (`ex539u`->`lbhmi3` discovery, `ozcfjr`->`0gd5w6` acks), which is what made the mismatch detectable and also what makes it harmless once stated. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author           --agent u8tabj -> {"outcome":"clean","exit":0,"findings":0}
aw ipd lint --phase review-finalize  --agent u8tabj -> {"outcome":"clean","exit":0,"findings":0}   (after revisions)

ipd_lint.orchestrator_row_conformance(u8tabj):
  applies=True conforming=True rows=3 table_reason=(none)
  E-01 nomhl1 executed  depends_on=none
  E-02 ex539u executed  depends_on=E-01
  E-03 ozcfjr executed  depends_on=E-01

check_engine.evaluate_durable_carrier(u8tabj)  BEFORE -> 1 finding, severity error
                                                         (OQ-01, check.ipd-uncarried-obligation)
                                               AFTER  -> 0 findings
check_engine.carrier_severity_for_plan(u8tabj) -> error   (Date 2026-09-24 > CARRIER_CUTOVER_DATE 20260919)
same defect in the three children               -> 1 error finding EACH (not fixed here, see D-1)

children on disk    nomhl1 / ex539u / ozcfjr all in pending/, all `- Status: to-review`
child deps          nomhl1: none | ex539u: executed:nomhl1 | ozcfjr: executed:nomhl1
spec-path overlap   all THREE children declare the same
                    .aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md

backlog gates       ifeyjv / lbhmi3 / 0gd5w6 all `graduated`, `Graduated-To: commsbroker`,
                    NONE carries `- Blocks-Release:`
evaluate_blocking_close(item, "done") for all three
                    -> legitimate=True severity=ok path=DE-GATED "no release gate to preserve"

opt-in baseline (establishes PR-002's replacement checks measure something)
  grep -rnE '^\s*(from|import)\s+.*comms_(broker|acks)' agent_workflows/ --include=*.py  -> EMPTY
  grep -rn 'comms_broker|comms_acks' pyproject.toml agent_workflows/command_surface.py   -> EMPTY

environment claims the children rest on, spot-checked
  opencode --version        1.18.32   (matches both children's re-measurement note)
  import zeroconf           ModuleNotFoundError (matches ex539u F-2)
  comms.py ships            BROKER_ACK_STATES, AGENT_ACK_STATES, ACK_WRITER, validate_ack,
                            ack_filename, ack_writer_for, parse_not_before, is_filename_safe,
                            parse_envelope_header, validate_envelope_header - and no writer
  spec Deferred list        4 bullets: broker / agent-side ack WRITING / discovery-registry /
                            (Depends-On + transports + cross-box)  -> the fourth is untouched by
                            every child, which is PR-004's "nothing deletes them"
```

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. PR-001 through PR-005 all FIXED, none deferred, none open. OQ-01 and
the newly authored OQ-02 are both `Blocking: no` with recorded recommendations and durable carriers,
which under the 2026-09-10 maintainer ruling does not make the plan `NO-GO`.

Readiness `go-pending-approval`. Three things a human should know before approving, none of which is a
finding against this file. FIRST, all three children are still `to-review` and each carries the same
uncarriered-OQ `error` finding this parent just fixed, so the Set cannot execute end to end until each
child is reviewed. SECOND, child 01's E-01 is a spike that starts a real local `opencode serve --pure`
and makes live HTTP calls to it; that is now named in this plan's gate because this is where the Set is
approved. THIRD, closing the three backlog items is a deliberate FOLLOW-UP after the Set completes and
is nobody's E-item, with the exact commands now recorded in the plan.
