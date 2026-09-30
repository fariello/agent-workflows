# IPD: File the carrier for host-granular network filtering and close the decision with an honest capability report

- Date: 2026-09-29
- Kind: child
- Concern: This Set answers backlog `oq05nc`'s decision question PARTIALLY: it proves port denial and leaves the 443 gap open, because Landlock network rules are address-blind. If the Set ends there, the remaining work vanishes the moment these plans reach `executed` and class `done` in `aw attention`, which is the exact failure `check.ipd-uncarried-obligation` exists to catch and the reason backlog `oq05nc` itself had to be filed after plan `4h7tt0`.
- Scope: Verify the durable backlog carrier for host-granular network filtering (`sv9ce4`, filed at authoring time) is intact and honestly worded, point spec 5.2 at it, and verify the Set's end state reports honestly: no artifact claims push denial, no finding code was reintroduced, and the capability report matches what was actually probed. Records and verification only; no product code. NOTE the title says "File" because the filename derives from it and was minted before the carrier was moved earlier; the carrier is FILED at authoring time and this plan VERIFIES it, which is the stronger arrangement and is explained in E-01.
- Scope-Paths: .aw/records/backlog/open, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: executed:pi3bk8
- Status: approved
- Readiness: go-pending-approval
- From-Spec: 25kzda
- Work-Kind: feature
- Priority: low
- From-Backlog: oq05nc
- Set: denypush
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: wzhe4n
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review complete: APPROVE WITH REVISIONS APPLIED; PR-901..PR-908 all fixed

- 2026-09-30 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901 (HIGH, fixed), PR-902 (HIGH, fixed), PR-903 (MEDIUM, fixed), PR-904 (MEDIUM, fixed), PR-905 (MEDIUM, fixed), PR-906 (LOW, fixed), PR-907 (LOW, fixed), PR-908 (LOW, fixed). Findings recorded in `.aw/records/reviews/20260930-denypush-03-wzhe4n-file-the-carrier-for-host-granular-network-filtering-and-clo.review.md`. I RAN THIS PLAN'S OWN AUDIT rather than reading it, because an audit plan can only be reviewed by attempting its checks. Both serious findings share one shape: a check too narrow to find anything, reported honestly. PR-901: E-03(d) is the Set's ONLY defense against the combination-level overclaim and it named NO search term; measured on the current spec the hit count ranges from 2 to 28 by term (`deny push-capable` 2, `push denial` 3, `no-push` 7, `deny_push` 6, bare `push` 28), so the executor was choosing the audit's own thoroughness and the cheapest choice is narrowest. All five terms are now fixed in E-03 with each count required. PR-902: the spec asserts push denial at TWO sites, and orchestrator `l4vw9o`'s Cross-IPD section states "Order 03's E-03 and V-03 now name it" about Section 6.1 limit 4 while this plan mentioned Section 6.1, limit 4, or that heading ZERO times; the parent believed the obligation was discharged here and it was not, which is exactly how the Set could amend 5.2 to say denial is MEASURED while limit 4 keeps describing the design as requiring a control nothing provides. E-03 and V-03 now name limit 4 with its required judgement and the DO-NOT-AMEND resolution. PR-903: E-04's bar "All checks pass" was UNREACHABLE; measured on a clean tree `aw check` exits 1 with 60 findings and `aw research index --check` exits 1 with 96 (all `adopted-without-consumer` on ARCHIVED docs, none naming `uq4y6q` or `denypush`), 156 findings this Set does not own, so the bar is now a DELTA with counts re-derived at execution, while `aw backlog check` and `aw sanitize --agent` (both exit 0 today) stay held to a genuine zero. PR-904: the Scope check said `.aw/records/backlog/open` "is written by E-01" while E-01's first word is VERIFY, so finalize would surprise the executor with a `--scope-ack` demand; the entry is deliberately kept and the expectation recorded. Also fixed: the validation section cited `check.from-backlog-dangling`, which reports ZERO rows today, and `aw research index --check` "reports no drift", which it cannot. Verified sound and left alone: the carrier `sv9ce4` is `open`/`low`/`feature` with no `Blocks-Release:` and visible in `aw attention`, `len(RUN_FINDING_CODES)` is 12 with `validate_finding_table()` returning `ok=True`, 5.2's bullet and the 5.6 `deny_push` string are each present once, F-3's `4h7tt0` quotation is verbatim, and both OQs were already correctly resolved. A latent `to-review -> draft` history inversion was corrected. `aw ipd lint --phase review-finalize` conforming, zero findings.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored review-ready while graduating backlog `oq05nc`. Exists so the Set's unfinished half has a carrier a status view can see.
- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Leave the repository in a state where the honest answer to "can any host deny push?" is written down,
the remaining mechanism has a durable carrier that `aw attention` can see, and nothing this Set shipped
can be read as claiming more than it proved.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: carry the remaining work

- [ ] E-01 VERIFY, do not re-file, the residual-work carrier: backlog `sv9ce4` was filed AT AUTHORING TIME (2026-09-29) rather than left to this plan, deliberately, because a carrier that only exists if the Set executes is exactly the obligation-loss this Set exists to fix. Confirm it is still `open`, still carries no `Blocks-Release:`, still cites research `uq4y6q`, and still describes HOST-granular filtering rather than "push denial". If any of those drifted, correct it with `aw backlog set` and record what changed; if the item was closed or removed, re-file it with the same content and record why.
  - Depends on: none
  - Expected outcome: `sv9ce4` is confirmed present, `open`, ungated, and honestly worded, so the unbuilt half of spec 5.2's requirement has a carrier `aw attention` can see regardless of what the rest of this Set did.
  - Execution state: pending

- [ ] E-02 Amend spec `25kzda` 5.2 with one sentence naming backlog `sv9ce4` as the carrier for the remaining half of its push-denial requirement, so a reader of the requirement can find the work rather than re-deriving the feasibility analysis. Append a `## Workflow history` record with `aw specs note` naming this plan and the Set's outcome.
  - Depends on: E-01
  - Expected outcome: 5.2 points at a live carrier by id6. The requirement bullet, both tables, and the 5.6 packet example stay unchanged.
  - Execution state: pending

### Task group 2: verify the Set did not overclaim

- [ ] E-03 Audit the Set's end state for overclaim, treating this as a falsification exercise rather than a confirmation. Verify by RUNNING commands, not by reading the plans: (a) `aw host capabilities` output contains no `deny_push` and names the new capability with a note stating the port-granularity limit; (b) `run_evidence`'s finding table still holds exactly 12 codes and no push-denial code was added; (c) `ACTION_CLASSES` is still `(ACTION_READ_ONLY,)` so nothing is gated; (d) grep the spec and the module docstring for any sentence asserting push denial as an available guarantee, and report each hit with its context.
  - SUB-CHECK (d) MUST NAME ITS SEARCH TERMS, AND THE REQUIRED SET IS FIXED HERE, because an unnamed grep is the one thing in this Set that can silently pass. Measured at review on the current spec, the hit counts differ by an order of magnitude depending on the term chosen: `deny push-capable` = 2, `push denial` = 3, `no-push` = 7, `deny_push` = 6, bare `push` = 28. An executor free to pick a term therefore decides the audit's own thoroughness, and the cheapest choice is the narrowest. RUN ALL FIVE, state each count, and judge every hit of the first four; the bare-`push` run is a completeness sweep whose purpose is to surface a sentence the other four miss, so state its count and judge only hits not already covered.
  - JUDGE **BOTH** OF THE SPEC'S PUSH-DENIAL SITES BY NAME. `grep -c "deny push-capable"` returns 2 (measured at review), and the two are not equivalent: the first is 5.2's requirement bullet, which Order 01 amends; the SECOND is Section 6.1 limit 4, "**No-push and hook guarantees require control of execution.**", whose body says the design "requires the engine to own process launch, deny push-capable network/credentials, own commits, and record the commit gateway". MEASURED AT REVIEW: this plan previously did not mention Section 6.1, limit 4, or that heading ANYWHERE, while the orchestrator `l4vw9o` states in its Cross-IPD section that "Order 03's E-03 and V-03 now name it" and its V-03 fails an audit "reporting one hit". So the parent already delegated this to this item and this item did not carry it, which is exactly how the second site gets missed. THE REQUIRED JUDGEMENT ON LIMIT 4 IS "requirement/limit, acceptable, not an available-guarantee claim", and the resolution is DO-NOT-AMEND: limit 4 says the design REQUIRES these controls and that a host lacking them must fail closed, which is what this Set confirms rather than changes, and editing an accurate honest-limits entry to mention a port probe would itself be the overclaim this plan exists to catch.
  - Depends on: E-02
  - Expected outcome: Either a clean audit with pasted evidence for each of the four checks, or a named overclaim to fix before the Set closes. A hit in (d) is a finding to resolve, not a note to file. An audit that reports ONE `deny push-capable` hit has missed limit 4 and has not met this item.
  - Execution state: pending

- [ ] E-04 Run the full validation sweep and record the Set's honest outcome: the bare suite, `aw ipd lint` over every plan in the Set, `aw check`, `aw research index --check`, and `aw sanitize --agent`. Record in this plan, in plain language, what the Set DID deliver (a probed port-denial capability and two amended contracts) and what it did NOT (push denial, any enforcement, any gated action), so the record does not have to be reconstructed from four plans.
  - TWO OF THESE GATES EXIT NONZERO ON THIS REPOSITORY TODAY, so "all checks pass" is UNREACHABLE as an acceptance bar and must not be the criterion. Measured at review on a clean tree, before this Set runs: `aw check` exits **1** with **60** findings, and `aw research index --check` exits **1** with **96** findings (every one an `adopted-without-consumer` on an ARCHIVED research doc; none mentions `uq4y6q` or `denypush`). An executor holding itself to a zero exit would either be blocked on a backlog it does not own or would quietly declare success it did not have. THE CORRECT BAR IS A DELTA: capture each gate's finding COUNT and its rule breakdown BEFORE the Set's changes and again after, and require that no NEW finding names any artifact this Set touched. Where a count must be re-derived rather than trusted, re-derive it: these are LIVE populations that drift with every plan authored in the repository, so the numbers above are review-time context and not the bar.
  - `aw backlog check` AND `aw sanitize --agent` DO exit zero today (both measured at review), so for those two a nonzero exit is a genuine regression this Set introduced and must be treated as one.
  - Depends on: E-03
  - Expected outcome: Every gate's output pasted with its exit status; the two delta-judged gates show no new finding attributable to this Set; `aw backlog check` and `aw sanitize --agent` exit zero; and the Set's scope is stated in one place without overclaiming.
  - Execution state: pending

## Project conventions discovered (Step 0)

- An obligation recorded only in prose vanishes when a plan reaches `executed` and classes `done` in `aw attention`; the mechanism is `check.ipd-uncarried-obligation`, and it is what forced backlog `oq05nc` to be filed after plan `4h7tt0` left its sandbox row with `Carrier-Declined`. This plan exists to not repeat that.
- Backlog items are created with `aw backlog new` and never hand-named (AGENTS.md). `--priority` and `--work-kind` are required at filing time. Relevant here only if E-01 must RE-FILE a removed carrier; on the happy path nothing is created.
- `Work-Kind: feature` is NOT in the release-gating set (default `bug`), so the carrier must carry no `Blocks-Release:`. Inventing one would misrepresent a low-priority capability as a release blocker, and the backlog item `oq05nc` this Set graduates from carries none either. VERIFIED AT REVIEW: `sv9ce4` is `Status: open`, `Priority: low`, `Work-Kind: feature`, with no `Blocks-Release:` line, so E-01's expected state is the actual state today.
- Cite code by SYMBOL or quoted content string, never by a bare line number (`IPD-C801`).
- A plan may amend a spec and MUST declare it in `Scope-Paths` (AGENTS.md), which is what makes both runners announce the declared spec edit and reconcile it at finalize.
- `Scope-Paths` accepts a directory entry. `.aw/records/backlog/open` is declared as a directory because E-01's CORRECTIVE branch (`aw backlog set`, or re-filing a removed item whose name `aw backlog new` mints at execution time) cannot be predicted when authoring. On the happy path it is unmodified, which is why the Scope check records the `--scope-ack` this plan will be asked for.
- A `V-*` criterion that counts a LIVE artifact population must state the property and require re-derivation at execution time, not freeze an authoring-time number (spec `ipd-structure-and-linting`; the plan-review rubric's live-artifact convention). This bites in E-04: the `aw check` and `aw research index --check` finding counts drift with every plan authored in the repository, so the measured figures are recorded as context and the BAR is a delta with no new finding naming this Set's artifacts.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | The 443 gap is the whole remaining problem | Research `uq4y6q` Finding 3: with 443 allowed, both `140.82.113.4:443` and `1.1.1.1:443` connected; the rule struct has no address field | The carrier must name HOST-granular filtering specifically. A carrier that said "finish the network sandbox" would lose the reason. |
| F-2 | Host-granular filtering is blocked on this host today | Research `uq4y6q` host table: `unshare -Urn --map-root-user true` fails `Operation not permitted` while `bwrap`, `unshare` and `slirp4netns` are all installed | The carrier is a genuine project with a host-capability dependency, which is why it is `open` and low rather than something to attempt inside this Set. |
| F-3 | This repository has already lost one obligation this way | Plan `4h7tt0`'s deferred sandbox row carries `Carrier-Declined` reasoning that "no sandbox is owed", yet backlog `oq05nc` had to be filed on 2026-09-21 as "the DURABLE CARRIER for the obligation its retirement deliberately left open" | The precedent is direct and recent. A `Carrier-Declined` on a genuinely open mechanism is what produced the gap this Set is now closing. |
| F-4 | Overclaim is the specific failure mode to audit for | `run_evidence`'s retirement comment: reintroducing the code bound to a presence check "converts today's safe fail-closed state into a fail-OPEN checker, which is strictly worse than having no code at all" | E-03 audits by running commands, because the claim to falsify is about what the SHIPPED artifacts report, not about what the plans intended. |
| F-5 | The finding-code count is a runtime invariant | `run_evidence.validate_finding_table` hard-fails `len(RUN_FINDING_CODES) != 12` with `RC-COUNT`; spec 4.2 says editing the table without amending the invariant "makes the SHIPPED table report itself invalid at runtime" | E-03 (b) checks the count as a behavioral assertion, which is the cheapest proof no code was smuggled in. |
| F-6 | The Set ends with nothing enforced, by design | The module docstring's HONEST LIMIT already records that the preflight "prevents nothing on its own" because no production action requires a capability; this Set adds a capability and gates no action | E-04 must state this plainly. A reader who assumes a new capability means new enforcement would be wrong, and the record should not let them assume it. |
| F-7 | THE AUDIT'S OWN GREP DECIDES ITS THOROUGHNESS, AND E-03(d) NAMED NO TERM (measured at review) | Hit counts on the current spec vary by an order of magnitude with the term chosen: `deny push-capable` = 2, `push denial` = 3, `no-push` = 7, `deny_push` = 6, bare `push` = 28 | An unnamed grep lets the executor pick the narrowest term and pass honestly. E-03 now FIXES all five terms and requires each count stated, with the bare-`push` run as a completeness sweep. This is the single most consequential revision in this plan, because sub-check (d) is the Set's only defense against the combination-level overclaim the orchestrator's Cross-IPD section describes. |
| F-8 | THE SPEC'S SECOND PUSH-DENIAL SITE WAS DELEGATED TO THIS PLAN AND THIS PLAN DID NOT CARRY IT (measured at review) | `grep -c "deny push-capable"` on spec `25kzda` returns 2: 5.2's requirement bullet, and Section 6.1 limit 4 ("**No-push and hook guarantees require control of execution.**", body "deny push-capable network/credentials"). Orchestrator `l4vw9o`'s Cross-IPD section states "Order 03's E-03 and V-03 now name it" and its V-03 fails an audit "reporting one hit"; measured, this plan mentioned Section 6.1, limit 4, or that heading ZERO times | The parent believed the obligation was discharged here and it was not, which is precisely how the second site gets missed: the Set could amend 5.2 to say denial is MEASURED while limit 4 keeps describing the design as requiring a control nothing provides. E-03 and V-03 now name limit 4 and fix its required judgement (requirement/limit, acceptable, DO-NOT-AMEND). |
| F-9 | TWO PRESCRIBED GATES EXIT NONZERO ON A CLEAN TREE, so "all checks pass" was unreachable | Measured at review before this Set runs: `aw check` exits 1 with 60 findings; `aw research index --check` exits 1 with 96, every one an `adopted-without-consumer` on an ARCHIVED doc and none naming `uq4y6q` or `denypush`. `aw backlog check` and `aw sanitize --agent` both exit 0 | E-04's acceptance bar was impossible, which pushes an executor either to report a blocked run over a backlog it does not own or to claim a pass it did not get. E-04 and V-04 now judge those two gates by DELTA (no new finding naming this Set's artifacts, counts re-derived at execution because they are live populations) while holding the other two to a genuine zero exit. |
| F-10 | `.aw/records/backlog/open` IS EXPECTED TO GO UNMODIFIED, and the Scope check said the opposite | E-01's first word is VERIFY and the carrier was filed at authoring time, yet the Scope check read "`.aw/records/backlog/open` is written by E-01". `ipd_lifecycle` emits `declared-but-unmodified path needs a --scope-ack: <p>` for exactly this case (verified at review) | The contradiction would surface at finalize as an unexpected demand. The entry is deliberately KEPT (E-01's corrective branch needs it in scope) and the Scope check now records that a `--scope-ack` is the expected, ordinary answer rather than a failure. |

## Proposed changes (ordered, validatable)

1. VERIFY the host-granular filtering carrier is intact, `open`, ungated, and honestly worded (E-01).
   It was FILED at authoring time, so this step files nothing on the happy path; the previous wording
   here said "File the carrier", which contradicted E-01 and the Concern section alike.
2. Point spec 5.2 at it and record the Set's outcome in the spec's history (E-02).
3. Audit the shipped end state for overclaim by running commands, with the five search terms named and
   BOTH spec push-denial sites judged (E-03).
4. Run the full sweep, judging the two gates that exit nonzero on pre-existing findings by DELTA rather
   than by exit code, and state the Set's delivered and undelivered scope in one place (E-04).

## Deferred / out of scope (with reason)

- BUILDING host-granular filtering. That is the carrier's content, not this plan's: it needs a
  namespace, a proxy, a per-host capability probe, and a policy for which endpoints are allowed.
  - Carrier: sv9ce4
- REINTRODUCING a `RUN-NO-PUSH`-shaped finding code. The gate stated in backlog `oq05nc` ("Only after
  such a probe exists may a finding code be reintroduced in 4.2") is still unmet after this Set,
  because the probe that now exists proves PORT denial rather than push denial.
  - Carrier-Declined: NOT WANTED and not owed. The condition is recorded in the spec and in backlog
    `sv9ce4`, so a future reader finds it without anyone asserting pending work. Filing a carrier for
    a deliberately unmet gate would misrepresent it as scheduled.
- GATING any action on the port-denial capability, which would require populating
  `RUNNER_ACTION_TO_CONTRACT_ACTION` and re-adding an action class the repository deliberately removed.
  - Carrier: sv9ce4
- CLOSING backlog `oq05nc` as `done`. Not this plan's to do and not correct: the runner sets
  `graduated` on verification, and `graduated` is the accurate state because the design was handed off
  while the full boundary is not built.
  - Carrier-Declined: Out of scope by construction; the status transition is the runner's.

## Scope check

- Over-scope: none, but `.aw/records/backlog/open` IS EXPECTED TO GO UNMODIFIED and that is the
  correct outcome, not a miss. This entry was authored when E-01 FILED the carrier; the carrier is now
  filed at authoring time and E-01 only VERIFIES it, so on the happy path this plan writes nothing
  under that directory at all. The previous wording ("`.aw/records/backlog/open` is written by E-01")
  contradicted E-01's own first word, VERIFY. IT IS DELIBERATELY KEPT DECLARED rather than removed,
  because E-01 must be able to CORRECT drift (`aw backlog set`) or re-file a removed item without that
  edit reading as out-of-scope. THE CONSEQUENCE THE EXECUTOR MUST EXPECT: `aw ipd finalize` demands a
  `--scope-ack` per declared-but-unmodified path (verified at review in `ipd_lifecycle`, which emits
  `declared-but-unmodified path needs a --scope-ack: <p>`), so a clean run of this plan WILL be asked
  to ack this directory. That is an ordinary finalize answer and not a failure; supply
  `--scope-ack .aw/records/backlog/open=not-needed` (or the reason drift required an edit). E-03 and
  E-04 write only this plan's own evidence blocks, which the lifecycle allows implicitly.
- Under-scope: none. No product code changes here by design, which is why no source or test path is
  declared; E-03 READS shipped behavior via commands rather than editing it.

## Required tests / validation

- Run the suite BARE as `python3 -m pytest` and paste the actual summary line. No code changes here,
  so the expectation is unchanged counts; the run is what establishes the Set's end state is green.
- `aw ipd lint` over every plan in Set `denypush` reports conforming.
- `aw check` reports NO NEW violations, judged as a delta and not by exit code: it exits 1 with 60
  pre-existing findings today (measured at review; re-derive at execution). Verified at review that all
  four plans in this Set carry `- From-Backlog: oq05nc` and that `check.from-backlog-dangling` reports
  ZERO rows, so that rule is already clean and naming it as a gate proves nothing; the `release-gates`
  family is the one worth asserting, since the spec carries `- Blocks-Release: next` and no plan here
  moves it.
- `aw backlog check` passes: it exits 0 today, so a nonzero exit here is a regression this Set caused.
- `aw research index --check` reports no NEW drift. It exits 1 with 96 pre-existing
  `adopted-without-consumer` findings on ARCHIVED research docs (measured at review, none naming
  `uq4y6q` or `denypush`), so "reports no drift" as authored was unachievable. The claim to verify is
  that `uq4y6q` itself is clean after Order 01 sets `outcome: adopted` with `consumed-by: [x2dwu5]`
  (`x2dwu5` resolves today, so the pair will not dangle).
- `aw sanitize --agent` exits zero. It does today, so a nonzero exit is a regression; this plan pastes
  command output including spec greps, which is a realistic leak vector.

## Spec / documentation sync

- Spec `25kzda` is AMENDED (declared in `Scope-Paths`) with one sentence in 5.2 naming the carrier for
  the unbuilt half of the push-denial requirement. WHY this belongs here: 5.2's own preserved paragraph
  says the requirement is kept so "a future probed capability has somewhere to land", and after this Set
  a probed capability HAS landed while the requirement remains unmet. Without a pointer, the next
  reader cannot tell whether the residual gap is tracked or forgotten, which is the ambiguity that
  produced backlog `oq05nc` in the first place.
- No CHANGELOG entry: nothing user-visible changes in this plan.

## Open questions

### OQ-01: Should the residual work be ONE carrier or split into a capability probe item and a policy item?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: ONE carrier. The two halves are not independently
  useful, which is the test that decides it. A namespace-plus-proxy probe with no endpoint policy
  proves a mechanism nobody can switch on, and an endpoint policy with no proven mechanism is the
  config-flag row plan `4h7tt0`'s candidate table already rejected as having zero enforcement. Filing
  them separately would also invite the second to be closed on the first's evidence. The item's body
  can enumerate both parts as scope; splitting is cheap later if the work is picked up and proves large,
  and the carrier itself records that it is `1o4eif`-magnitude so nobody picks it up casually.

### OQ-02: Should this plan set backlog oq05nc's status?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM THE AUTHORING CONTRACT: no. The production contract
  for this turn states the runner sets `graduated` upon verification and that a plan must not set the
  item `done`. `graduated` is also the semantically correct end state: the design is handed off, and
  the code for a complete boundary is deliberately not written. So this plan touches the item's status
  not at all, and E-01 files a NEW item rather than re-opening or mutating `oq05nc`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Backlog `sv9ce4`'s path and full front matter pasted, showing `Status: open`, `Work-Kind: feature`, `Priority: low`, and NO `Blocks-Release:` line. Its summary must name host-granular or per-host filtering and must NOT be phrased as "deny push", since a carrier titled as push denial would recreate the overclaim. Paste `aw attention` output showing the item appears, which is the behavioral proof that the obligation is visible to a status view rather than only present on disk. Paste the grep showing it cites research `uq4y6q`. If anything was corrected under E-01, paste the before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff` of the spec showing the added sentence naming the carrier id6, plus the tail of its `## Workflow history` showing the new dated record naming `wzhe4n`. A grep must show the requirement bullet "deny push-capable network routes and withhold remote credentials" is byte-unchanged, since every plan in this Set is obliged to preserve it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Four pasted command outputs, one per sub-check: (a) `aw host capabilities opencode` showing no `deny_push` and showing the new capability's note naming the port limit; (b) a `python3 -c` printing `len(run_evidence.RUN_FINDING_CODES)` equal to 12 and `validate_finding_table` reporting valid (measured at review, it returns `EvidenceValidationResult(ok=True, findings=())`, so paste the object rather than paraphrasing "valid"); (c) a `python3 -c` printing `ACTION_CLASSES` equal to `(ACTION_READ_ONLY,)`; (d) the grep for push-denial assertions with every hit and its surrounding sentence, plus an explicit judgement on each hit stating whether it describes an available guarantee (a defect to fix) or a requirement/history/limit (acceptable). An empty grep result with no judgement recorded FAILS this item, because the check is the judgement and not the absence.
  - FOR (d), PASTE ALL FIVE TERM COUNTS AND NAME LIMIT 4 EXPLICITLY. The five terms E-03 fixes are `deny push-capable`, `push denial`, `no-push`, `deny_push` and bare `push`; state each count (review-time spec figures were 2, 3, 7, 6 and 28, to be RE-DERIVED rather than copied since the spec is amended three times in this Set). The evidence must contain the words Section 6.1 limit 4 and a judgement on it. AN AUDIT REPORTING ONE `deny push-capable` HIT FAILS THIS ITEM: there are two, and the orchestrator's own V-03 says so, so a single-hit report proves the grep was wrong rather than that the second site is absent.
  - ALSO CONFIRM (a) DID NOT FALSE-POSITIVE ON THE WORD `REFUSED`. Use `grep -c 'REFUSED  '` (two trailing spaces) if the audit reports on refused rows: measured at review, a bare `grep -c REFUSED` on `aw host capabilities opencode` returns 1 because the fresh-verifier probe note contains "a reused-identity run was REFUSED", while the two-space form returns 0. Reporting the bare hit as a gated action would be a false overclaim finding, which in an audit whose whole job is accuracy is the same defect pointed the other way.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted actual output of `python3 -m pytest` (the summary line), `aw ipd lint` over the Set, `aw check`, `aw research index --check`, `aw backlog check`, and `aw sanitize --agent` with its exit status. Plus the written statement of delivered versus undelivered scope, which must explicitly say that no action is gated and no push denial is enforced. A statement claiming the Set delivered push denial FAILS this item.
  - DO NOT REPORT "all checks pass": TWO OF THEM CANNOT. Measured at review on a clean tree, `aw check` exits 1 with 60 findings and `aw research index --check` exits 1 with 96 (all `adopted-without-consumer` on ARCHIVED docs, none naming `uq4y6q` or `denypush`). For those two, paste the finding COUNT and rule breakdown and assert the DELTA: no new finding naming any artifact this Set touched. RE-DERIVE both counts at execution time rather than comparing against the numbers above, which are live populations that drift with every plan authored. A pasted zero-exit claim for either gate is evidence the command was not run.
  - `aw backlog check` and `aw sanitize --agent` MUST exit 0, since both do today (measured at review); for those two a nonzero exit is a real regression and not pre-existing noise. Note also that `check.from-backlog-dangling`, which this plan's validation section names, reports ZERO rows today, so citing it as a gate is citing an already-clean rule; the live rule that does name this plan is the advisory `check.plan-spec-link-missing`, addressed by the `- From-Spec:` edge added at review.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is the Set's honesty gate. Its two jobs are to make sure the unbuilt half has a carrier a
status view can see, and to check by RUNNING things that nothing shipped claims a boundary that does
not exist. Both jobs exist because this repository has already lost this exact obligation once: plan
`4h7tt0` declined a carrier for the sandbox work, and backlog `oq05nc` had to be filed later to
recover it.

WHAT A REVIEWER SHOULD PUSH HARDEST ON, and what review found when it did (2026-09-30). An audit plan
fails in one specific way: by running a check too narrow to find anything and reporting the clean
result honestly. Both of this plan's serious findings were that shape. E-03(d), the Set's ONLY defense
against the combination-level overclaim, named no search term, and the hit count on the current spec
ranges from 2 to 28 depending on the term an executor picks (F-7). And the spec's SECOND push-denial
site, Section 6.1 limit 4, was delegated to this plan by the orchestrator's own Cross-IPD section while
this plan mentioned it zero times (F-8). Separately, E-04's bar of "all checks pass" was unreachable,
because two prescribed gates exit nonzero on a clean tree over 156 findings this Set does not own
(F-9). An audit whose criterion cannot be met teaches an executor to soften criteria, which is the
worst possible habit in the plan that exists to be strict.

Execution contract: commit only the paths named in `Scope-Paths`, through `aw commit <plan> -- <paths>`,
never `git add -A`, and never push. This is a SHARED CHECKOUT: verify the staged set with
`git diff --cached --name-only` before committing, unstage anything that is not yours with
`git restore --staged <path>`, and re-verify after any failed raw commit attempt. Run the suite BARE as
`python3 -m pytest` and PASTE ITS ACTUAL SUMMARY LINE; a summary you did not produce is not evidence,
and the same hard-MUST governs every pasted gate output, grep count, and exit status this plan's `V-*`
items demand. Paste skips explicitly rather than letting a green line hide one.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop). The two
`- Scope-Paths:` entries are the whole surface, and `.aw/records/backlog/open` is expected to be
UNMODIFIED on the happy path (F-10), so expect finalize to ask for
`--scope-ack .aw/records/backlog/open=not-needed`. THREE NEGATIVE CONSTRAINTS CARRY REAL WEIGHT.
FIRST, do NOT amend spec `25kzda` Section 6.1 limit 4: the orchestrator resolved it DO-NOT-AMEND, it is
already accurate, and editing an honest-limits entry to mention a port probe would be the overclaim
this plan exists to catch; E-03 RECORDS a judgement on it instead. SECOND, do NOT alter 5.2's
requirement bullet, either table, or the 5.6 packet example's `deny_push` string: V-02 re-greps the
bullet byte-for-byte because every plan in this Set is obliged to preserve it. THIRD, do NOT change
`oq05nc`'s status, add a finding code, or gate an action; OQ-02 records why the first is the runner's,
and the Deferred section records the other two. An out-of-scope edit that turns out to be necessary is
to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path; that is not a
reason to stop. IF THE AUDIT FINDS A REAL OVERCLAIM, fix it with a corrective plan rather than
annotating it, which V-03 already requires, and report it: an overclaim the Set shipped is a genuine
human decision point, unlike the routine finalize answers above.

LIFECYCLE TRANSITION. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete observed evidence.
Reaching `executed/` is UNCONDITIONALLY OWED, but its OWNER is CONDITIONAL: under `aw oc run` /
`aw agy run` the RUNNER owns the terminal transition and finalize, so do NOT invoke `aw ipd finalize`
yourself in a runner-driven execution; a HAND execution invokes it
(`aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`). Never hand-edit
`- Status:` and never hand-roll a `git mv` into `executed/`, which would skip the pre-transition
checkpoint. Backlog `oq05nc` is already `graduated` (verified at review); this plan must NOT set it
`done`.
