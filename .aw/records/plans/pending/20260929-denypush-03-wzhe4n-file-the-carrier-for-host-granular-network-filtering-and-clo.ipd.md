# IPD: File the carrier for host-granular network filtering and close the decision with an honest capability report

- Date: 2026-09-29
- Kind: child
- Concern: This Set answers backlog `oq05nc`'s decision question PARTIALLY: it proves port denial and leaves the 443 gap open, because Landlock network rules are address-blind. If the Set ends there, the remaining work vanishes the moment these plans reach `executed` and class `done` in `aw attention`, which is the exact failure `check.ipd-uncarried-obligation` exists to catch and the reason backlog `oq05nc` itself had to be filed after plan `4h7tt0`.
- Scope: Verify the durable backlog carrier for host-granular network filtering (`sv9ce4`, filed at authoring time) is intact and honestly worded, point spec 5.2 at it, and verify the Set's end state reports honestly: no artifact claims push denial, no finding code was reintroduced, and the capability report matches what was actually probed. Records and verification only; no product code. NOTE the title says "File" because the filename derives from it and was minted before the carrier was moved earlier; the carrier is FILED at authoring time and this plan VERIFIES it, which is the stronger arrangement and is explained in E-01.
- Scope-Paths: .aw/records/backlog/open, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: executed:pi3bk8
- Status: to-review
- Work-Kind: feature
- Priority: low
- From-Backlog: oq05nc
- Set: denypush
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: wzhe4n

## Workflow history

- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored review-ready while graduating backlog `oq05nc`. Exists so the Set's unfinished half has a carrier a status view can see.

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
  - Depends on: E-02
  - Expected outcome: Either a clean audit with pasted evidence for each of the four checks, or a named overclaim to fix before the Set closes. A hit in (d) is a finding to resolve, not a note to file.
  - Execution state: pending

- [ ] E-04 Run the full validation sweep and record the Set's honest outcome: the bare suite, `aw ipd lint` over every plan in the Set, `aw check`, `aw research index --check`, and `aw sanitize --agent`. Record in this plan, in plain language, what the Set DID deliver (a probed port-denial capability and two amended contracts) and what it did NOT (push denial, any enforcement, any gated action), so the record does not have to be reconstructed from four plans.
  - Depends on: E-03
  - Expected outcome: All checks pass with pasted output, and the Set's scope is stated in one place without overclaiming.
  - Execution state: pending

## Project conventions discovered (Step 0)

- An obligation recorded only in prose vanishes when a plan reaches `executed` and classes `done` in `aw attention`; the mechanism is `check.ipd-uncarried-obligation`, and it is what forced backlog `oq05nc` to be filed after plan `4h7tt0` left its sandbox row with `Carrier-Declined`. This plan exists to not repeat that.
- Backlog items are created with `aw backlog new` and never hand-named (AGENTS.md). `--priority` and `--work-kind` are required at filing time.
- `Work-Kind: feature` is NOT in the release-gating set (default `bug`), so the new item must carry no `Blocks-Release:`. Inventing one would misrepresent a low-priority capability as a release blocker, and the backlog item `oq05nc` this Set graduates from carries none either.
- Cite code by SYMBOL or quoted content string, never by a bare line number (`IPD-C801`).
- A plan may amend a spec and MUST declare it in `Scope-Paths` (AGENTS.md), which is what makes both runners announce the declared spec edit and reconcile it at finalize.
- `Scope-Paths` accepts a directory entry (`.aw/records/backlog/open` is used here because the new item's filename is minted by `aw backlog new` at execution time and cannot be predicted when authoring).

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | The 443 gap is the whole remaining problem | Research `uq4y6q` Finding 3: with 443 allowed, both `140.82.113.4:443` and `1.1.1.1:443` connected; the rule struct has no address field | The carrier must name HOST-granular filtering specifically. A carrier that said "finish the network sandbox" would lose the reason. |
| F-2 | Host-granular filtering is blocked on this host today | Research `uq4y6q` host table: `unshare -Urn --map-root-user true` fails `Operation not permitted` while `bwrap`, `unshare` and `slirp4netns` are all installed | The carrier is a genuine project with a host-capability dependency, which is why it is `open` and low rather than something to attempt inside this Set. |
| F-3 | This repository has already lost one obligation this way | Plan `4h7tt0`'s deferred sandbox row carries `Carrier-Declined` reasoning that "no sandbox is owed", yet backlog `oq05nc` had to be filed on 2026-09-21 as "the DURABLE CARRIER for the obligation its retirement deliberately left open" | The precedent is direct and recent. A `Carrier-Declined` on a genuinely open mechanism is what produced the gap this Set is now closing. |
| F-4 | Overclaim is the specific failure mode to audit for | `run_evidence`'s retirement comment: reintroducing the code bound to a presence check "converts today's safe fail-closed state into a fail-OPEN checker, which is strictly worse than having no code at all" | E-03 audits by running commands, because the claim to falsify is about what the SHIPPED artifacts report, not about what the plans intended. |
| F-5 | The finding-code count is a runtime invariant | `run_evidence.validate_finding_table` hard-fails `len(RUN_FINDING_CODES) != 12` with `RC-COUNT`; spec 4.2 says editing the table without amending the invariant "makes the SHIPPED table report itself invalid at runtime" | E-03 (b) checks the count as a behavioral assertion, which is the cheapest proof no code was smuggled in. |
| F-6 | The Set ends with nothing enforced, by design | The module docstring's HONEST LIMIT already records that the preflight "prevents nothing on its own" because no production action requires a capability; this Set adds a capability and gates no action | E-04 must state this plainly. A reader who assumes a new capability means new enforcement would be wrong, and the record should not let them assume it. |

## Proposed changes (ordered, validatable)

1. File the host-granular filtering carrier with the measured reasons and the citation (E-01).
2. Point spec 5.2 at it and record the Set's outcome in the spec's history (E-02).
3. Audit the shipped end state for overclaim by running commands (E-03).
4. Run the full sweep and state the Set's delivered and undelivered scope in one place (E-04).

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

- Over-scope: none. `.aw/records/backlog/open` is written by E-01; the spec by E-02. E-03 and E-04 are
  read-only audits and write only this plan's own evidence blocks.
- Under-scope: none. No product code changes here by design, which is why no source or test path is
  declared; E-03 READS shipped behavior via commands rather than editing it.

## Required tests / validation

- Run the suite BARE as `python3 -m pytest` and paste the actual summary line. No code changes here,
  so the expectation is unchanged counts; the run is what establishes the Set's end state is green.
- `aw ipd lint` over every plan in Set `denypush` reports conforming.
- `aw check` reports no new violations, including `check.from-backlog-dangling` (every plan in this Set
  carries `- From-Backlog: oq05nc`) and the `release-gates` family.
- `aw backlog check` passes for the newly filed item.
- `aw research index --check` reports no drift.
- `aw sanitize --agent` exits zero.

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
  - Required evidence: Four pasted command outputs, one per sub-check: (a) `aw host capabilities opencode` showing no `deny_push` and showing the new capability's note naming the port limit; (b) a `python3 -c` printing `len(run_evidence.RUN_FINDING_CODES)` equal to 12 and `validate_finding_table` reporting valid; (c) a `python3 -c` printing `ACTION_CLASSES` equal to `(ACTION_READ_ONLY,)`; (d) the grep for push-denial assertions with every hit and its surrounding sentence, plus an explicit judgement on each hit stating whether it describes an available guarantee (a defect to fix) or a requirement/history/limit (acceptable). An empty grep result with no judgement recorded FAILS this item, because the check is the judgement and not the absence.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted actual output of `python3 -m pytest` (the summary line), `aw ipd lint` over the Set, `aw check`, `aw research index --check`, `aw backlog check`, and `aw sanitize --agent` with its exit status. Plus the written statement of delivered versus undelivered scope, which must explicitly say that no action is gated and no push denial is enforced. A statement claiming the Set delivered push denial FAILS this item.
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

Execution contract: commit only the paths named in `Scope-Paths`, through `aw commit <plan> -- <paths>`,
never `git add -A`, and never push. Paste actual command output rather than claiming success. On
completion, verify `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete
observed evidence before moving this plan to `.aw/records/plans/executed/`.
