# IPD: Decide and, if approved, build a Landlock-backed network-denial capability for the no-push boundary

- Date: 2026-09-29
- Kind: orchestrator
- Concern: Backlog `oq05nc` asks a DECISION question: whether to build OS-level push-denial enforcement, the only mechanism plan `4h7tt0` found without a concrete agent-level evasion. Nobody had measured whether the mechanism is reachable, so the question could not be answered on evidence. It now is measured (research `uq4y6q`), and the answer is split: kernel TCP denial is real and cheap, but it is port-granular and therefore cannot deny an HTTPS push without also denying the model API the agent needs. This Set records that measurement, ships the narrower thing that is honestly true, and refuses to ship the claim that is not.
- Scope: Coordinate three children that (1) record the measurement and amend the two contracts that assert or disclaim push denial, (2) add ONE probed port-denial capability named for what it proves, gating no action and reintroducing no finding code, and (3) verify the Set did not overclaim and that the unbuilt half has a live carrier. This orchestrator performs no product change of its own.
- Scope-Paths: .aw/records/plans/pending/20260929-denypush-00-l4vw9o-decide-and-if-approved-build-a-landlock-backed-network-denia.ipd.md
- Item-Dependencies: none
- Status: to-review
- Coverage: pass
- Coverage-Fingerprint: 85d00a1ba1d43deaa76f3fce916c4809b9f52d072bf4b3ad929b4cc064f5c74e
- Coverage-Checked: 2026-10-07 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: feature
- Priority: low
- From-Backlog: oq05nc
- Set: denypush
- Order: 0
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: l4vw9o

## Workflow history
- 2026-10-07 coverage pass (aw oc run): fingerprint 85d00a1ba1d4, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 /plan-review (opencode uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed. Review record `.aw/records/reviews/20261007-denypush-00-l4vw9o-decide-and-if-approved-build-a-landlock.review.md`.
- 2026-10-07 to-review (aw set): returned to review: Set-level checks owned by wzhe4n E-03/E-04 (runs last); carrier sv9ce4 already exists; coverage pass recorded
- 2026-10-07 coverage pass (aw oc run): fingerprint 69dd49745d53, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): each criterion and Set-level check now leads with its owner (`wzhe4n` E-03/E-04 for the cross-child audit and sweep).
- 2026-10-07 coverage fail (aw oc run): fingerprint 05ced26f246f, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): the carrier bullet the coverage probe quoted describes a backlog item that already exists (`sv9ce4`, open), not a step; reworded to say so.
- 2026-10-06 draft (aw set): demoted approved -> draft: APPROVAL WITHDRAWN: returned to authoring by gradcover 52opph: uncovered obligation: - THE CARRIER OUTLIVES THE SET. Backlog `sv9ce4` is filed before any child runs, so the unbuilt half
- 2026-10-06 coverage fail (aw oc run): fingerprint 6029f33b9741, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (aw set): status set to reviewed

- 2026-09-30 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-601 (MEDIUM, fixed), PR-602 (MEDIUM, fixed), PR-603 (MEDIUM, fixed), PR-604 (LOW, fixed), PR-605 (LOW, fixed). Findings recorded in `.aw/records/reviews/20260930-denypush-00-l4vw9o-decide-and-if-approved-build-a-landlock-backed-network-denia.review.md`. I RE-MEASURED THE SET'S ENTIRE TECHNICAL PREMISE FROM THE KERNEL UP rather than reading research `uq4y6q`, and every load-bearing claim holds: this host reports Landlock ABI 4 (kernel 6.8.0), a `CONNECT_TCP` ruleset with no net rule denies every outbound connect (`EPERM(13)`), a ruleset allowing only port 443 permits `1.1.1.1:443` AND `8.8.8.8:443` while refusing `1.1.1.1:22`, which is exactly the two-sided denial plus PORT-GRANULAR, ADDRESS-BLIND result the Set's whole decision rests on. So the measurement is sound and the conclusion (kernel TCP denial is real but cannot separate a git remote from the model API on 443) is correct. The five code-level completion criteria were each verified against the tree: `ACTION_CLASSES == (ACTION_READ_ONLY,)`, `len(RUN_FINDING_CODES) == 12` with no `NO-PUSH` code, `supports_deny_push`/`CAP_DENY_PUSH` absent, `DenyPushRemovedTests` live, and spec 5.2's requirement bullet present at its landing site. The child table matches all three children's real ids, orders, and `Item-Dependencies` chain. Carriers `sv9ce4` and `wcbpqf` are both `open` and honestly worded, and `wcbpqf` is an unusually good decision carrier: it holds all three of the Set's maintainer decisions with the measured context and a close procedure. THE ONE REAL GAP: spec `25kzda` contains TWO sites asserting push denial, 5.2's requirement bullet and Section 6.1 limit 4 ("deny push-capable network/credentials"), and NO plan in the Set mentions 6.1 at all, so the Set could amend 5.2 to say denial is measured while limit 4 continues to describe the design as requiring a control nothing provides. Order 03's audit grep would surface it but nothing tells that executor it is an expected hit or who owns fixing it. Now assigned to Order 03 with a recorded judgement requirement, and the parent's byte-unchanged invariant widened to name both sites. Also fixed: V-03 demanded `aw attention` show `oq05nc` "no longer open" when the item is ALREADY `graduated` (measured) so the check was a tautology that would have passed without the Set running; V-02's `aw host capabilities opencode` evidence needed the negative half stated; and a `probe_notes` wording risk that my own measurement demonstrated, since I initially mis-set the network bit to `BIND_TCP` (`1<<0`) instead of `CONNECT_TCP` (`1<<1`) and got a silent total-denial result that looked like working enforcement, which is precisely the fail-open-looking-like-fail-closed shape child 02's two-sided probe must exclude.

- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored review-ready while graduating backlog `oq05nc`. Carries orchestration only; every product change belongs to a child.

## Goal

Answer backlog `oq05nc`'s decision question with measured evidence, then deliver exactly the part of
it that is enforceable: a probed port-denial capability, two honestly amended contracts, and a durable
carrier for the part that is not. Nothing this Set ships may be readable as a push-denial guarantee.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: run the Set in order

- [ ] E-01 CONFIRM x2dwu5 REACHED executed
  - Depends on: none
  - Expected outcome: `x2dwu5` (re-measure the probes; amend spec `25kzda` 5.2 and the `host_sandbox_profile` module docstring) is in `.aw/records/plans/executed/` with status `executed`, every `V-*` carrying concrete evidence.
  - Execution state: pending

- [ ] E-02 CONFIRM pi3bk8 REACHED executed
  - Depends on: E-01
  - Expected outcome: `pi3bk8` (add the probed `supports_deny_tcp_port` capability) is in `.aw/records/plans/executed/` with status `executed`, every `V-*` carrying concrete evidence. It declares `Item-Dependencies: executed:x2dwu5`, so it cannot legitimately start before E-01: the capability's honest description depends on the spec amendment landing first.
  - Execution state: pending

- [ ] E-03 CONFIRM wzhe4n REACHED executed
  - Depends on: E-02
  - Expected outcome: `wzhe4n` (verify the carrier and audit the Set for overclaim) is in `.aw/records/plans/executed/` with status `executed`, every `V-*` carrying concrete evidence and its audit reporting no overclaim.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | x2dwu5 | `.aw/records/plans/executed/20260929-denypush-01-x2dwu5-record-the-measured-landlock-feasibility-and-amend-spec-25kz.ipd.md` | Re-measures the three Landlock probes on the executing host; amends spec `25kzda` 5.2 with the measured position (ABI-4 denial is real, port-granular, address-blind; the credential half is BOUNDED, not shipped: files are hidden only under opt-in Linux hardened mode and environment-carried credentials are not withheld) and amends `host_sandbox_profile`'s module docstring where it currently calls network scoping out of scope. Records only: no probe, no capability, no finding code. | none |
| 02 | pi3bk8 | `.aw/records/plans/pending/20260929-denypush-02-pi3bk8-add-a-probed-supports-deny-remote-ssh-push-capability-provin.ipd.md` | Extends `landlock_bootstrap_source` to carry network rules; adds `_probe_deny_tcp_port`, a two-sided executed probe; adds the `supports_deny_tcp_port` capability defaulting False and registered with a REAL probe; amends the docstring; extends `CONTRACT_FIELDS` and the `PRESENCE_VS_OBSERVATION` table; re-points `DenyPushRemovedTests` without weakening it. Gates no action. | `executed:x2dwu5` |
| 03 | wzhe4n | `.aw/records/plans/pending/20260929-denypush-03-wzhe4n-file-the-carrier-for-host-granular-network-filtering-and-clo.ipd.md` | Verifies backlog `sv9ce4` (the host-granular filtering carrier) is intact, `open`, and honestly worded; points spec 5.2 at it; audits the shipped end state by RUNNING commands for four overclaim checks, INCLUDING a recorded judgement on BOTH of the spec's two push-denial sites (5.2's bullet and Section 6.1 limit 4, which no child amends); runs the full validation sweep and states delivered versus undelivered scope. | `executed:pi3bk8` |

Note on the child titled "File the carrier": the carrier (backlog `sv9ce4`) was filed AT AUTHORING
TIME rather than by that child, deliberately. A carrier that only exists if the Set executes is the
exact obligation-loss this Set was created to fix, so Order 03 VERIFIES it instead. The filename was
minted from the original title and is left stable.

## Completion criteria (the whole Set is done only when)

- [Owner: each child in its own V-items; this plan's V-01..V-03 confirm] All three children are `executed`, each with concrete pasted evidence on every `V-*` item.
- [Owner: x2dwu5 (already executed, its V-items pass) for the amendment; wzhe4n E-02 for the carrier sentence and V-02 for the final byte-unchanged re-grep] Spec `25kzda` 5.2 records the MEASURED position: kernel TCP denial is real at Landlock ABI 4, it is
  port-granular and address-blind, the credential half of its bullet is BOUNDED rather than complete
  (credential files hidden only under opt-in Linux hardened mode; environment-carried credentials such
  as `GH_TOKEN` or a forwarded `SSH_AUTH_SOCK` are NOT withheld), no host reports push denial, and the
  requirement remains fail-closed.
- [Owner: wzhe4n E-03 sub-check (d) / V-03] Spec `25kzda` Section 6.1 limit 4 is left UNCHANGED and that is recorded as a deliberate judgement in
  Order 03's audit, not an omission. It is the spec's SECOND push-denial site (measured: two hits) and
  it remains accurate, so the Set's obligation is to show it was considered rather than to edit it.
- [Owner: pi3bk8 E-02/E-03 and their V-items; wzhe4n E-03 sub-check (a) re-confirms] Exactly ONE new capability exists, `supports_deny_tcp_port`, decided by an executed two-sided probe,
  defaulting False, with a `probe_notes` entry, visible in `aw host capabilities`.
- [Owner: pi3bk8 E-07/V-07; wzhe4n E-03 sub-checks (a) and (e) re-confirm] `supports_deny_push` and `CAP_DENY_PUSH` remain ABSENT, and `DenyPushRemovedTests` still passes with
  its assertions intact rather than deleted.
- [Owner: wzhe4n E-03 sub-check (c) / V-03] `ACTION_CLASSES` is still `(ACTION_READ_ONLY,)`: no action is gated, and none of the three removed
  action classes returned.
- [Owner: wzhe4n E-03 sub-check (b) / V-03] `run_evidence.RUN_FINDING_CODES` still holds exactly 12 codes: no `RUN-NO-PUSH`-shaped code returned.
- [Owner: wzhe4n E-01 / V-01] Backlog `sv9ce4` is `open`, ungated, and visible in `aw attention` as the carrier for the unbuilt half.
- [Owner: wzhe4n E-04 / V-04, judged as a DELTA for `aw check` and `aw research index --check`, which already exit 1 before the Set] The bare suite passes, `aw ipd lint` conforms over every plan in the Set, `aw check` reports no new
  violations, and `aw sanitize --agent` exits zero.

## Cross-IPD validation

- [Owner: wzhe4n E-03 (overclaim audit) and E-04 (validation sweep), which runs last] NO ARTIFACT CLAIMS PUSH DENIAL. This is the Set's single most important cross-cutting property and
  it is checked behaviorally by Order 03's audit (running `aw host capabilities`, printing
  `ACTION_CLASSES`, counting the finding table, and grepping the spec and docstring with a recorded
  judgement per hit) rather than by re-reading the plans. The reason it needs a cross-IPD check at all
  is that each child is individually honest while the COMBINATION is where an overclaim would appear:
  Order 01 writes that denial is real, Order 02 ships a working probe, and a reader who meets only
  those two could reasonably conclude push is now denied.
- [Owner: wzhe4n E-03 (overclaim audit) and E-04 (validation sweep), which runs last] THE NAME IS CONSISTENT ACROSS THE SET. Every child refers to the new capability as
  `supports_deny_tcp_port`, and none reintroduces `supports_deny_push`. Order 02's OQ-01 was RESOLVED at
  review to keep `supports_deny_tcp_port`, with backlog `wcbpqf` still available to the maintainer; if
  the name changes later, all three children and this
  orchestrator must be updated together, since a half-renamed Set would leave the spec naming a field
  that does not exist.
- [Owner: wzhe4n E-03 (overclaim audit) and E-04 (validation sweep), which runs last] THE SPEC IS AMENDED THREE TIMES AND MUST NOT DRIFT. Orders 01, 02 and 03 each amend spec `25kzda`,
  which is why each declares it in `Scope-Paths` and each is required to leave the requirement bullet
  "deny push-capable network routes and withhold remote credentials" BYTE-UNCHANGED (plan `01reg8`
  preserved it as this work's landing site). Order 03's V-02 re-greps it after the last amendment, so
  a drift introduced by any earlier child is caught at the end rather than assumed absent.
- [Owner: wzhe4n E-03 (overclaim audit) and E-04 (validation sweep), which runs last] THE SPEC ASSERTS PUSH DENIAL IN **TWO** PLACES AND ONLY ONE IS AMENDED, WHICH IS DELIBERATE AND MUST
  BE RECORDED RATHER THAN DISCOVERED (added at review). Measured: `grep -c "deny push-capable"` on
  spec `25kzda` returns **2**. The first is 5.2's requirement bullet, which every child knows about. The
  second is Section 6.1 limit 4, "**No-push and hook guarantees require control of execution**", whose
  body says the design "requires the engine to own process launch, deny push-capable
  network/credentials, own commits, and record the commit gateway". Measured at review: NO plan in this
  Set mentions Section 6.1, limit 4, or that heading anywhere. That matters because 6.1 is the spec's
  own "honest limits" section, so a reader who meets an amended 5.2 saying denial is MEASURED and an
  untouched limit 4 saying the design REQUIRES a control is left to reconcile them. The resolution taken
  is NOT to amend limit 4: it is already accurate (it says the design requires these controls and that a
  host lacking them must fail closed, which is exactly what this Set confirms and does not change), and
  editing an accurate honest-limits entry to mention a port probe would itself be the overclaim this Set
  exists to avoid. What IS required is that Order 03's audit (its E-03 sub-check (d)) report the limit-4
  hit EXPLICITLY with the judgement "requirement/limit, acceptable, not an available-guarantee claim",
  so the second site is visibly considered rather than silently missed. Order 03's E-03 and V-03 now
  name it, and this row exists so a reviewer of any single child can see why their child does not.
- [Owner: wzhe4n E-03 (overclaim audit) and E-04 (validation sweep), which runs last] THE MEASUREMENT IS RE-TAKEN, NOT INHERITED. Order 01's E-01 re-runs the probes on the executing
  host rather than trusting research `uq4y6q`'s numbers, because every finding there is host-specific
  by construction. If the executing host reports ABI < 4, Order 01 records that and Order 02's real
  denial test legitimately skips; the Set must then say so explicitly instead of pasting a green line
  that hides the skip, since a skip leaves the guarantee unverified on that machine.
- [Owner: wzhe4n E-03 (overclaim audit) and E-04 (validation sweep), which runs last] THE ONE-SIDED MEASUREMENT TRAP, DEMONSTRATED AT REVIEW ON THIS SET'S OWN SUBJECT MATTER (added at
  review, and the reason Order 02's two-sided probe is not optional rigour). Re-deriving the Landlock
  measurement, the reviewer set `handled_access_net` to `1 << 0` and observed every outbound connect
  refused with `EPERM(13)`, including the port that was explicitly ALLOWED. Read one-sidedly that is a
  working boundary. It was not: `1 << 0` is `LANDLOCK_ACCESS_NET_BIND_TCP` and `CONNECT_TCP` is
  `1 << 1`, so the ruleset handled a right the test never exercised, the port rule matched nothing, and
  the total denial came from handling-with-no-matching-rule. Corrected to `1 << 1`, the same script
  yields the real result: allowed port 443 connects to TWO distinct hosts SUCCEED while port 22 is
  refused. Two consequences for the Set. FIRST, Order 02's `_probe_deny_tcp_port` MUST require the
  allowed connect to SUCCEED and not merely the denied one to fail, which its E-02 already specifies as
  three distinguishable exit shapes including "allowed-connect-denied (jail too tight)"; that arm is the
  one this trap trips, so it must not be simplified away. SECOND, no plan in the Set may state the bit
  NUMERICALLY. Every child and the research refer to `LANDLOCK_ACCESS_NET_CONNECT_TCP` by NAME, which is
  why none of them inherited this error, and that convention is now load-bearing rather than incidental.
- [Already true; no step owed] THE CARRIER OUTLIVES THE SET. Backlog `sv9ce4` already exists (filed at
  authoring, `- Status: open` in `.aw/records/backlog/open/`), so the unbuilt half is visible to `aw attention`
  even if this Set is never executed or is abandoned partway. Nothing is filed by this plan or any child.

## Deferred / out of scope (with reason)

- BUILDING a real push-denial boundary. Measurement shows the available mechanism cannot deliver it:
  Landlock net rules are port-only and push shares TCP 443 with the model API the confined agent needs.
  - Carrier: sv9ce4
- ENFORCEMENT of any kind. This Set adds a REPORTED capability and gates no action, because gating on
  port denial would imply a boundary that the 443 gap leaves open.
  - Carrier: sv9ce4
- REINTRODUCING a `RUN-NO-PUSH`-shaped finding code in spec 4.2. Backlog `oq05nc` gates that on a real
  probe existing, and the probe this Set ships proves PORT denial, not push denial, so the gate stays
  unmet on purpose.
  - Carrier-Declined: NOT WANTED and not owed. Binding a push-denial code to a port probe is the
    fail-OPEN inference `run_evidence`'s retirement comment forbids in writing. The condition for a
    legitimate future reintroduction is recorded in the spec and in backlog `sv9ce4`, so it is findable
    without asserting that anyone intends to do it.
- UNDOING plan `4h7tt0`'s retirement of `RUN-NO-PUSH` or `01reg8`'s removal of `supports_deny_push`.
  Backlog `oq05nc` states explicitly: "THIS ITEM IS NOT A REQUEST TO UNDO THAT."
  - Carrier-Declined: Both were maintainer decisions and this Set honors them; nothing is owed.
- CONTAINER isolation, which the module docstring also lists as out of scope and which this Set does
  not touch.
  - Carrier-Declined: Unrelated to push denial; nothing is owed.

## Scope check

- Over-scope: none. This orchestrator declares only its own file, because it changes nothing else:
  every product and record change belongs to a child and is declared there.
- Under-scope: none. The three children cover the measurement, the contracts, the capability, the
  tests, the carrier, and the audit. The unbuilt mechanism is deliberately outside the Set and carried
  by `sv9ce4`.

## Required tests / validation

- [Owner: wzhe4n E-04/V-04] Each child runs its own validation; this orchestrator does not re-run them. The Set-level gates are
  the ones listed under Completion criteria, and Order 03's E-04 is what actually executes the sweep
  (bare `python3 -m pytest`, `aw ipd lint` over the Set, `aw check`, `aw research index --check`,
  `aw backlog check`, `aw sanitize --agent`) and pastes its output.
- [Owner: wzhe4n E-04/V-04] This orchestrator's own `V-*` items verify only that each child genuinely reached `executed`, which
  is a state on disk and is checkable without re-running the children's tests.

## Open questions

### OQ-01: Should this Set ship the port-denial capability at all, or record the measurement and stop?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: wcbpqf
- Resolution or deferral rationale: NOT BLOCKING, because the Set is ordered so the answer can be
  given at review without rework: Order 01 is records-only and stands alone, so a maintainer who wants
  only the measurement can approve Order 01 and decline Orders 02 and 03. RECOMMENDED: ship it. The
  case FOR is that it is the first PROBED answer to a 5.2 requirement that has only ever had declared
  ones, it proves something real (SSH-based push on port 22 IS denied outright, measured), it costs one
  dataclass field plus a probe because the ruleset already carries the network member, and it gates
  nothing so its blast radius is a report row. The case AGAINST is genuine and a reviewer should weigh
  it: a capability that cannot stop the push path anyone actually uses (HTTPS) may mislead an operator
  reading `aw host capabilities`, and this area's whole history is of names promising more than they
  deliver. That risk is mitigated by the name and by the required `probe_notes` limit, and Order 03's
  audit exists to check the mitigation held. If the maintainer judges the mitigation insufficient,
  declining Orders 02 and 03 leaves the measurement recorded and the carrier filed, which is still a
  strict improvement on the state before this Set.

### OQ-02: Should backlog oq05nc be closed by this Set, given the decision is answered only partially?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM THE AUTHORING CONTRACT: the runner sets the item
  `graduated` on verification, and no plan here sets it `done`. `graduated` is also the accurate word:
  the item asked a DECISION question, the decision is made and recorded on measured grounds, and the
  design is handed off, while the code for a complete boundary is deliberately not written. The
  residual mechanism does not stay attached to `oq05nc` as unfinished business; it moves to backlog
  `sv9ce4`, which is what makes closing `oq05nc` honest rather than a quiet abandonment.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `git log --oneline` showing `x2dwu5`'s commit, the plan's path under `.aw/records/plans/executed/`, and pasted `aw ipd lint` output reporting it `executed` and conforming. Spot-check that its V-01 observed-evidence block contains the actual probe output rather than a summary, since the whole Set rests on that measurement.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `pi3bk8`'s path under `.aw/records/plans/executed/`, pasted `aw ipd lint` reporting it `executed` and conforming, and pasted `aw host capabilities opencode` output showing the new capability row with its probe note. THE PROBE NOTE IS THE EVIDENCE, NOT THE ROW: quote it and confirm it states the port-granularity limit, since the row alone is what an operator over-reads and the note is the whole mitigation OQ-01 rests on. Also paste a `python3 -c` printing `ACTION_CLASSES`, which must still be `(ACTION_READ_ONLY,)`: that is the proof the capability shipped without silently acquiring enforcement. AND state the NEGATIVE half explicitly: that the same `aw host capabilities` output contains no `deny_push` and no `REFUSED` row, because a capability that quietly acquired a gate would show up there and nowhere else in this item's evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `wzhe4n`'s path under `.aw/records/plans/executed/`, pasted `aw ipd lint` reporting it `executed` and conforming, and its V-03 audit evidence showing all four overclaim checks with a recorded judgement on each grep hit. THE GREP JUDGEMENT MUST ACCOUNT FOR BOTH SPEC SITES: `grep -c "deny push-capable"` on spec `25kzda` returns 2 (measured at review), so an audit reporting one hit has missed Section 6.1 limit 4 and does NOT satisfy this item; the expected outcome is two hits, each judged, with limit 4 judged acceptable for the reason in the Cross-IPD row above. Additionally paste `aw attention` showing backlog `sv9ce4` present as the residual carrier and `wcbpqf` present as the decision carrier. DO NOT use `oq05nc`'s status as evidence of anything: its status reflects this orchestrator's authoring round trips, not the Set's outcome (it was `graduated` at authoring, then reopened to `open` on 2026-10-06 when coverage returned this plan to authoring, measured 2026-10-07), so it can pass or fail regardless of what the children did. For `wcbpqf`, show it present in `aw attention` and state its status. Measured 2026-10-07, it is `graduated`, with its only handoff plan `d5ntkj` in `not-executed/`. If the audit named an overclaim, this item FAILS until the overclaim is fixed by a corrective plan rather than annotated.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This orchestrator carries orchestration ONLY: its three E-items each name one child, and every product
change, record change, test, and audit is owned by a child that performs and validates it. There is no
step here that no child covers, which is the property that makes retiring this plan on child completion
honest.

What a reviewer should push hardest on is OQ-01, because it is the actual decision backlog `oq05nc`
asked for and it is the one place this Set could go wrong in a way the tests cannot catch: the
measurement is unambiguous, but whether a port-granular capability is worth reporting to an operator is
a judgement about how a partial guarantee reads, and this area's history is exactly a history of names
that promised more than they delivered.

WHAT REVIEW ESTABLISHED FOR THAT DECISION, so the maintainer weighs evidence rather than a summary
(2026-09-30). The technical premise was re-derived from the kernel, not read from research `uq4y6q`:
this host reports Landlock ABI 4, a `CONNECT_TCP` ruleset with no net rule refuses every outbound
connect with `EPERM(13)`, and a ruleset allowing only port 443 lets `1.1.1.1:443` AND `8.8.8.8:443`
through while refusing `1.1.1.1:22`. So BOTH halves of the decision's factual basis are confirmed: the
denial is real and two-sided, and it is port-granular and address-blind, which is precisely why it
cannot separate a git remote from the model API. Nothing in the measurement favours one answer to
OQ-01 over the other; it establishes that the capability under discussion would report something TRUE
and PARTIAL. The decision remains a judgement about how a partial guarantee reads, which is the
maintainer's, and it is carried durably by backlog `wcbpqf` together with the other
two decisions this Set raises (measured 2026-10-07: `wcbpqf` is `graduated`, but its only handoff plan,
`d5ntkj`, was REJECTED and sits in `not-executed/`, so the item's status overstates progress; the
maintainer should reopen it with `aw backlog set` if it is to read as an outstanding decision). APPROVING
Orders 02 and 03 IS the maintainer's answer to OQ-01; declining them is the other answer, so declining Orders 02 and 03 loses nothing that is not written down.

Execution contract: OQ-02 is resolved, and OQ-01 is a non-blocking maintainer decision answered by
approving or declining Orders 02 and 03. SCOPE FENCE: this is a declaration for the runner to reconcile,
not an instruction to stop. This plan modifies only its own file; each child modifies only its own
`Scope-Paths`. An out-of-scope edit is made and then justified with `aw ipd finalize --scope-reason`.
Each child commits only those paths, through `aw commit <plan> -- <paths>`, never `git add -A`, and
NEVER pushes. HONESTY RULE: paste actual test output, including skips; never claim a pass that was not
run. LIFECYCLE: the transition is owed unconditionally, but its owner is conditional. Under
`aw oc run` / `aw agy run` the RUNNER finalizes each child, and retires this orchestrator once every child
is `executed` on disk; the executor must not run `aw ipd finalize`. Executed by hand, each child is
finalized only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete
observed evidence, via `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`, and this
orchestrator the same way after V-01..V-03 pass. Never hand-roll a `git mv` into `executed/` and never
hand-edit `- Status: executed`.
