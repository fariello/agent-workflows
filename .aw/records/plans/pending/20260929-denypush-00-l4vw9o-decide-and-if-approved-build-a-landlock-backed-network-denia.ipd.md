# IPD: Decide and, if approved, build a Landlock-backed network-denial capability for the no-push boundary

- Date: 2026-09-29
- Kind: orchestrator
- Concern: Backlog `oq05nc` asks a DECISION question: whether to build OS-level push-denial enforcement, the only mechanism plan `4h7tt0` found without a concrete agent-level evasion. Nobody had measured whether the mechanism is reachable, so the question could not be answered on evidence. It now is measured (research `uq4y6q`), and the answer is split: kernel TCP denial is real and cheap, but it is port-granular and therefore cannot deny an HTTPS push without also denying the model API the agent needs. This Set records that measurement, ships the narrower thing that is honestly true, and refuses to ship the claim that is not.
- Scope: Coordinate three children that (1) record the measurement and amend the two contracts that assert or disclaim push denial, (2) add ONE probed port-denial capability named for what it proves, gating no action and reintroducing no finding code, and (3) verify the Set did not overclaim and that the unbuilt half has a live carrier. This orchestrator performs no product change of its own.
- Scope-Paths: .aw/records/plans/pending/20260929-denypush-00-l4vw9o-decide-and-if-approved-build-a-landlock-backed-network-denia.ipd.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: low
- From-Backlog: oq05nc
- Set: denypush
- Order: 0
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: l4vw9o

## Workflow history

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
| 01 | x2dwu5 | `.aw/records/plans/pending/20260929-denypush-01-x2dwu5-record-the-measured-landlock-feasibility-and-amend-spec-25kz.ipd.md` | Re-measures the three Landlock probes on the executing host; amends spec `25kzda` 5.2 with the measured position (ABI-4 denial is real, port-granular, address-blind; the credential half is already shipped) and amends `host_sandbox_profile`'s module docstring where it currently calls network scoping out of scope. Records only: no probe, no capability, no finding code. | none |
| 02 | pi3bk8 | `.aw/records/plans/pending/20260929-denypush-02-pi3bk8-add-a-probed-supports-deny-remote-ssh-push-capability-provin.ipd.md` | Extends `landlock_bootstrap_source` to carry network rules; adds `_probe_deny_tcp_port`, a two-sided executed probe; adds the `supports_deny_tcp_port` capability defaulting False and registered with a REAL probe; amends the docstring; extends `CONTRACT_FIELDS` and the `PRESENCE_VS_OBSERVATION` table; re-points `DenyPushRemovedTests` without weakening it. Gates no action. | `executed:x2dwu5` |
| 03 | wzhe4n | `.aw/records/plans/pending/20260929-denypush-03-wzhe4n-file-the-carrier-for-host-granular-network-filtering-and-clo.ipd.md` | Verifies backlog `sv9ce4` (the host-granular filtering carrier) is intact, `open`, and honestly worded; points spec 5.2 at it; audits the shipped end state by RUNNING commands for four overclaim checks; runs the full validation sweep and states delivered versus undelivered scope. | `executed:pi3bk8` |

Note on the child titled "File the carrier": the carrier (backlog `sv9ce4`) was filed AT AUTHORING
TIME rather than by that child, deliberately. A carrier that only exists if the Set executes is the
exact obligation-loss this Set was created to fix, so Order 03 VERIFIES it instead. The filename was
minted from the original title and is left stable.

## Completion criteria (the whole Set is done only when)

- All three children are `executed`, each with concrete pasted evidence on every `V-*` item.
- Spec `25kzda` 5.2 records the MEASURED position: kernel TCP denial is real at Landlock ABI 4, it is
  port-granular and address-blind, the credential half of its bullet is already shipped in hardened
  mode, no host reports push denial, and the requirement remains fail-closed.
- Exactly ONE new capability exists, `supports_deny_tcp_port`, decided by an executed two-sided probe,
  defaulting False, with a `probe_notes` entry, visible in `aw host capabilities`.
- `supports_deny_push` and `CAP_DENY_PUSH` remain ABSENT, and `DenyPushRemovedTests` still passes with
  its assertions intact rather than deleted.
- `ACTION_CLASSES` is still `(ACTION_READ_ONLY,)`: no action is gated, and none of the three removed
  action classes returned.
- `run_evidence.RUN_FINDING_CODES` still holds exactly 12 codes: no `RUN-NO-PUSH`-shaped code returned.
- Backlog `sv9ce4` is `open`, ungated, and visible in `aw attention` as the carrier for the unbuilt half.
- The bare suite passes, `aw ipd lint` conforms over every plan in the Set, `aw check` reports no new
  violations, and `aw sanitize --agent` exits zero.

## Cross-IPD validation

- NO ARTIFACT CLAIMS PUSH DENIAL. This is the Set's single most important cross-cutting property and
  it is checked behaviorally by Order 03's audit (running `aw host capabilities`, printing
  `ACTION_CLASSES`, counting the finding table, and grepping the spec and docstring with a recorded
  judgement per hit) rather than by re-reading the plans. The reason it needs a cross-IPD check at all
  is that each child is individually honest while the COMBINATION is where an overclaim would appear:
  Order 01 writes that denial is real, Order 02 ships a working probe, and a reader who meets only
  those two could reasonably conclude push is now denied.
- THE NAME IS CONSISTENT ACROSS THE SET. Every child refers to the new capability as
  `supports_deny_tcp_port`, and none reintroduces `supports_deny_push`. Order 02's OQ-01 leaves the
  exact spelling open for the maintainer; if it changes at review, all three children and this
  orchestrator must be updated together, since a half-renamed Set would leave the spec naming a field
  that does not exist.
- THE SPEC IS AMENDED THREE TIMES AND MUST NOT DRIFT. Orders 01, 02 and 03 each amend spec `25kzda`,
  which is why each declares it in `Scope-Paths` and each is required to leave the requirement bullet
  "deny push-capable network routes and withhold remote credentials" BYTE-UNCHANGED (plan `01reg8`
  preserved it as this work's landing site). Order 03's V-02 re-greps it after the last amendment, so
  a drift introduced by any earlier child is caught at the end rather than assumed absent.
- THE MEASUREMENT IS RE-TAKEN, NOT INHERITED. Order 01's E-01 re-runs the probes on the executing
  host rather than trusting research `uq4y6q`'s numbers, because every finding there is host-specific
  by construction. If the executing host reports ABI < 4, Order 01 records that and Order 02's real
  denial test legitimately skips; the Set must then say so explicitly instead of pasting a green line
  that hides the skip, since a skip leaves the guarantee unverified on that machine.
- THE CARRIER OUTLIVES THE SET. Backlog `sv9ce4` is filed before any child runs, so the unbuilt half
  is visible to `aw attention` even if this Set is never executed or is abandoned partway.

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

- Each child runs its own validation; this orchestrator does not re-run them. The Set-level gates are
  the ones listed under Completion criteria, and Order 03's E-04 is what actually executes the sweep
  (bare `python3 -m pytest`, `aw ipd lint` over the Set, `aw check`, `aw research index --check`,
  `aw backlog check`, `aw sanitize --agent`) and pastes its output.
- This orchestrator's own `V-*` items verify only that each child genuinely reached `executed`, which
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
  - Required evidence: `pi3bk8`'s path under `.aw/records/plans/executed/`, pasted `aw ipd lint` reporting it `executed` and conforming, and pasted `aw host capabilities opencode` output showing the new capability row with its probe note. Also paste a `python3 -c` printing `ACTION_CLASSES`, which must still be `(ACTION_READ_ONLY,)`: that is the proof the capability shipped without silently acquiring enforcement.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `wzhe4n`'s path under `.aw/records/plans/executed/`, pasted `aw ipd lint` reporting it `executed` and conforming, and its V-03 audit evidence showing all four overclaim checks with a recorded judgement on each grep hit. Additionally paste `aw attention` showing backlog `sv9ce4` present and `oq05nc` no longer `open`. If the audit named an overclaim, this item FAILS until the overclaim is fixed by a corrective plan rather than annotated.
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

Execution contract: each child commits only the paths in its own `Scope-Paths`, through
`aw commit <plan> -- <paths>`, never `git add -A`, and never pushes. Paste actual test output, including
skips. Move each child to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition`
conforms and every `V-*` carries concrete observed evidence.
