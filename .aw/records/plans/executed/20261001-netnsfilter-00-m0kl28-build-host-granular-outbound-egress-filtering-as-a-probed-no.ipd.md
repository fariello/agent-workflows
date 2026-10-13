# IPD: Build host-granular outbound egress filtering as a probed, non-evadable boundary

- Date: 2026-10-01
- Kind: orchestrator
- Concern: Spec `25kzda` 5.2 requires a host descriptor answering whether a host can "deny push-capable network routes", and guarantee row 1 asserts a push attempt aborts the run. No mechanism in this repository can deliver that. Research `uq4y6q` measured why: Landlock network rules are `{allowed_access, port}` with no address field, so they cannot separate a git remote from the model API on TCP 443, and the confined process IS the agent that needs the model API. Backlog `sv9ce4` names the only mechanism that can (a network namespace plus a filtering proxy) and records it as blocked and unmeasured.
- Scope: Orchestrate the Set that builds destination-granular egress filtering as a PROBED, per-host, fail-closed capability: a two-sided hermetic probe, a parent-owned policy and broker, worker confinement that survives an agent's teardown attempt, and the contract amendments plus an audited honest capability report. The Set must not produce any artifact claiming push denial beyond what it measures, and gates no action.
- Scope-Paths: .aw/records/plans/pending/20261001-netnsfilter-00-m0kl28-build-host-granular-outbound-egress-filtering-as-a-probed-no.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: 3ba064065d63a65c687fb254166bcfc9d102c1805e9cb3969416e8d2d0e3d08e
- Coverage-Checked: 2026-10-12 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- From-Backlog: sv9ce4
- From-Spec: 25kzda
- Work-Kind: feature
- Priority: low
- Set: netnsfilter
- Order: 0
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: m0kl28

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): RETIRED as the orchestrator rollup step of a runner Set completion, not executed by an agent: every child of Set netnsfilter reached executed, so the runner (run run-20261013T012806Z-1261662) retired this Order-0 plan as bookkeeping. Its own E-*/V-* items were NOT performed; the runner superseded them by enforcing the ordering, the isolation and the per-child merge gate. Justifying children: nxh5s4, rozdkp, 2j4pd0, wn956n.
- 2026-10-12 coverage pass (aw oc run): fingerprint 3ba064065d63, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-11 coverage fail (aw oc run): fingerprint 0873f75ad43c, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-11 coverage fail (aw oc run): fingerprint b46b0ab10a6a, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-11 coverage fail (aw oc run): fingerprint cdf16d40ee59, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-11 coverage fail (aw oc run): fingerprint 0ed0fd14d09d, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-11 coverage fail (aw oc run): fingerprint 0ed0fd14d09d, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-11 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): children 2j4pd0 and wn956n retired not-executed by maintainer decision (option a); their child-table rows and checklist items E-03/E-04, V-03/V-04 removed per 2pv5xd OQ-02; completion criteria that depended on them marked WITHDRAWN; the Set-level sweep is recorded as not performed.
- 2026-10-11 same-status (aw set): child wn956n retired not-executed (maintainer decision, option a; see the 2j4pd0 line).
- 2026-10-11 same-status (aw set): child 2j4pd0 retired not-executed: maintainer decision (option a), 2026-10-11. No observed agent push motivated the work; the costs of a runner-level network gate outweigh the benefit here. The executed probe (nxh5s4) and broker (rozdkp) stay, unused by default. No replacement.
- 2026-10-08 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006. Reviewed at HEAD 2f90a295f. E-01 no longer claims a parent-owned baseline; the real-remote git completion criterion is replaced by child 2j4pd0 E-05's hermetic same-port test; V-01..V-04 demand pasted status, post-transition lint and quoted child evidence; gate corrected for sv9ce4 being open and gains the scope-fence wording; OQ-02 (non-blocking, maintainer) notes wcbpqf's text does not yet carry it. Review record .aw/records/reviews/20261001-netnsfilter-00-m0kl28-build-host-granular-outbound-egress-filtering-as-a-probed-no.review.md.
- 2026-10-07 to-review (aw set): returned to review: Set-level validation sweep owned by wn956n E-05/V-05; coverage pass recorded; open questions are non-blocking
- 2026-10-07 coverage pass (aw oc run): fingerprint a2cc304d9eb7, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: Bare pytest run green with actual summary line pasted

- 2026-10-06 coverage fail (aw oc run): fingerprint b0a8608603fb, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored review-ready while graduating backlog `sv9ce4`. Authoring was preceded by MEASURING the mechanism end to end, recorded as research `akmzyq`, because the item's own premise (that user namespaces are unavailable and the direction is therefore unmeasurable) did not reproduce on the authoring host.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Deliver the mechanism that makes spec `25kzda` 5.2's network requirement answerable for the first
time: outbound egress confined so that a git remote can be refused while the model API stays
reachable, proven BY ATTEMPT per host, non-evadable by the confined agent, and reported with a
capability note that states exactly what it does and does not cover.

## Detailed Implementation Checklist (TODO)


> Its own E-*/V-* items were NOT performed; the runner superseded them by enforcing the ordering, the isolation and the per-child merge gate.

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

THIS IS AN ORCHESTRATOR AND ITS ITEMS ARE ORCHESTRATION ONLY. Every deliverable in this Set is owned
by a CHILD, deliberately: the runner retires an orchestrator once every child is `executed` and
SKIPS the pre-transition E/V checkpoint on the premise that a parent's items are performed by nobody,
so work parked here would be marked complete having never been performed. The items below sequence
and verify children and produce no artifact of their own.

### Task group 1: sequence and verify the Set

- [ ] E-01 CONFIRM nxh5s4 REACHED executed
  - Depends on: none
  Confirm child 01 (`nxh5s4`, probe host-granular egress filtering) reached `executed`, with its two-sided verdict recorded in ITS OWN V-01. This item reads that record and produces nothing of its own; a False verdict is a legitimate outcome (fail-closed), after which child 03's namespace tests skip with a stated reason rather than the Set stalling.
  - Expected outcome: `nxh5s4` is in `executed/` and its V-01 carries the pasted `(bool, note)` for the real host, so the executing host's namespace availability is known before child 02 runs.
  - Execution state: pending

- [ ] E-02 CONFIRM rozdkp REACHED executed
  - Depends on: E-01
  Confirm child 02 (`rozdkp`, build egress policy and parent-owned filtering broker) reached `executed`. Confirms destination allow-list policy type and filtering broker are implemented and tested.
  - Expected outcome: Destination allow-list policy type and parent-owned broker implemented; policy refuses unlisted destination in unit test.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `nxh5s4` | `20261001-netnsfilter-01-nxh5s4-probe-host-granular-egress-filtering-by-attempt-two-sided-an.ipd.md` | Adds the hermetic two-sided executed probe and the capability field, reported and gating nothing | none |
| 02 | `rozdkp` | `20261001-netnsfilter-02-rozdkp-build-the-egress-policy-and-the-parent-owned-filtering-broke.ipd.md` | Adds the destination allow-list policy type and the parent-owned filtering broker that enforces it | executed:nxh5s4 |

RETIRED CHILDREN (2026-10-11, maintainer decision, option a): Order 03 `2j4pd0` (worker confinement) and Order 04 `wn956n` (contract amendment and Set-level audit) were retired `not-executed` and removed from this table, with their checklist rows E-03/E-04 and V-03/V-04, as `2pv5xd` OQ-02 requires. The work they owned is NOT reassigned: it is deliberately not being done. Their retirement is recorded in each plan under `plans/not-executed/` and in this plan's workflow history.

The order is forced by evidence dependency and not by preference. The probe (01) must exist before a
policy is worth enforcing, because a policy on a host that cannot create the namespace is
unverifiable. The policy (02) must exist before a worker is confined by it (03), because confinement
with no allow list denies the model API and therefore denies the product. And the contracts (04) must
be amended LAST, after the boundary's real limits are measured rather than predicted, since the
specific failure this Set guards against is a contract written to a hoped-for capability.

## Completion criteria (the whole Set is done only when)

- A capability on `HostSandboxCapabilities` reports destination-granular egress filtering, set True only by an executed two-sided probe, with a `probe_notes` entry naming its limits. OWNER: `nxh5s4` (executed).
- The probe returns False, with an explanatory note and no exception, on a host that cannot create a network namespace. Fail-closed is a REQUIREMENT of done, not a degraded outcome. OWNER: `nxh5s4` (executed).
- WITHDRAWN 2026-10-11 with children 03 and 04 (retired not-executed): the same-port confined-worker demonstration, the teardown-refusal proof, the contract amendment, and the Set-level sweep (bare suite, lint over the Set, overclaim audit) are not required. That spec note is ALREADY DONE, not owed: spec `25kzda` 5.2 was amended on 2026-10-11 in the same commit that retired the children (sentence beginning "DECIDED 2026-10-11 (maintainer): that half is NOT being built."), recorded by `aw specs note`.
- No action is gated: `ACTION_CLASSES` is unchanged and `RUNNER_ACTION_TO_CONTRACT_ACTION` stays empty. Enforcement is a separate decision with its own carrier. OWNER: `nxh5s4` and `rozdkp` (both executed; neither gates an action).

## Cross-IPD validation

- NO CHILD MAY SET A CAPABILITY TRUE WITHOUT AN EXECUTED PROBE. Child 01 owns the probe and children
  02 and 03 consume its verdict; none of them may infer support from the presence of `unshare`,
  `iptables`, `slirp4netns` or a config flag. Research `akmzyq` Finding 0 is the direct
  counterexample: three relevant binaries were installed on `uq4y6q`'s host and namespace creation
  still failed. Presence inference is forbidden in writing in `host_sandbox_profile`'s module
  docstring and again in `run_evidence`'s retirement comment.
- THE NAME `supports_deny_push` MUST NOT APPEAR as a new field, constant, or capability in any child.
  `DenyPushRemovedTests` pins its absence and plan `01reg8` removed it deliberately. Nothing this Set
  measures justifies a claim that broad, because an allow-listed host remains reachable and a
  proxying model endpoint would be a hole (research `akmzyq`, "what is NOT established").
- NO CHILD MAY ADD A FINDING CODE. `run_evidence.validate_finding_table` hard-fails a count other
  than 12 with `RC-COUNT`. Backlog `oq05nc`'s ordering rule allows a code only after a probe exists,
  and whether THIS probe satisfies that gate is a maintainer decision, not a child's to assume.
- WITHDRAWN 2026-10-11 (child 03 `2j4pd0` retired not-executed): three constraints that bound the worker-confinement child are moot because no worker is confined. They required (i) that child 03 keep child 01's fail-closed path, (ii) that the confined worker lose `CAP_NET_ADMIN` (research `akmzyq` Finding 6 measured the naive arrangement torn down in one command), and (iii) that every teardown check be verified from outside the sandbox. They are kept here as the record of what any future attempt must satisfy, not as live obligations.

## Deferred / out of scope (with reason)

- GATING any action on the new capability, which would require populating
  `RUNNER_ACTION_TO_CONTRACT_ACTION` and re-adding an action class this repository deliberately
  removed. Excluded because gating is a posture decision about refusing work on incapable hosts, and
  it should follow a shipped and measured boundary rather than accompany it.
  - Carrier: wcbpqf
- REINTRODUCING a `RUN-NO-PUSH`-shaped finding code in spec 4.2. Backlog `oq05nc` gates this on a
  probe existing; this Set produces one, so the gate's factual precondition is met for the first
  time. Whether to reintroduce a code is still a MAINTAINER decision and not this Set's to take.
  - Carrier: wcbpqf
- MACOS AND NON-LINUX hosts. Every measurement in research `akmzyq` is Linux namespace behavior, and
  the capability fails closed off Linux via the existing `CERTIFIED_PLATFORM` gate.
  - Carrier-Declined: NOT WANTED and not owed. No equivalent mechanism was measured, so filing a
    carrier would assert scheduled work where there is not even a candidate mechanism. The honest
    state is a capability that reports False off Linux, which the platform gate already produces.
- DISCOVERING the model endpoint automatically rather than taking it from configuration. Deferred
  because endpoint discovery is a policy question whose wrong answer silently denies the product,
  and child 02 makes the allow list explicit configuration precisely so the failure is visible.
  - Carrier: sv9ce4
- WITHHOLDING remote credentials, the other half of spec 5.2's bullet. Partly built already and
  untouched here: `oc_runipd._hardened_credential_paths` makes `~/.ssh`, `~/.netrc`,
  `~/.git-credentials` and peers inaccessible in hardened mode, while `runner_shared.pinned_child_env`
  is an `os.environ.copy()` that passes a `GH_TOKEN` or `SSH_AUTH_SOCK` through untouched.
  - Carrier-Declined: Nothing is owed BY THIS SET, which adds no credential handling. The bounded
    state is already recorded in the spec by the `denypush` Set's Order 01. This row exists so a
    reader of this Set does not infer the credential half is complete.

## Scope check

- Over-scope: none. This plan's only declared path is ITSELF, which is what an orchestrator carrying
  no deliverable of its own should touch. Every product and test path is declared by the child that
  changes it, so the finalize scope gate reconciles each change against the plan that owns it.
- Under-scope: none, and ONE OMISSION IS DELIBERATE. No spec path is declared here even though the
  Set amends spec `25kzda`, because child 04 owns that amendment and declares the spec in its own
  `Scope-Paths`. Declaring it in both would make the runner announce a spec edit this plan never
  makes and demand a `--scope-ack` at finalize for a path it was never going to touch.

## Required tests / validation

NONE OWED BY THIS PLAN OR ANY CHILD (re-scoped 2026-10-11). The Set-level sweep was owned by Order 04 `wn956n`, which was retired not-executed by maintainer decision, so no Set closeout sweep is performed. The two shipped children validated themselves: `nxh5s4` and `rozdkp` are `executed` with their own pasted suite, lint and sanitizer evidence. This plan's only remaining work is V-01/V-02 (confirm those two reached `executed`), after which the runner retires it.

Originally specified, and withdrawn with `wn956n`: a bare `python3 -m pytest`, `aw ipd lint` over the Set, an `aw check` delta, `aw sanitize --agent`, and `aw host capabilities opencode` output.

## Open questions

### OQ-01: Should the Set ship the capability as REPORTED-ONLY, or also gate the hardened profile on it?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: reported-only, with gating deferred to `wcbpqf`. The
  deciding evidence is in the repository's own history rather than in preference. The last time a
  capability in this area was wired to a consumer before its boundary was proven, the result was a
  claim nothing enforced: `RUN-NO-PUSH` promised "Capability preflight proved push denial" and plan
  `4h7tt0` retired it because nothing ever enforced either half, while `supports_deny_push` was
  declared and never probed and plan `01reg8` deleted it. Reported-only inverts that order: the
  verdict is published and auditable before anything depends on it. It is also the reversible
  direction, since adding a requirement row to `ACTION_CAPABILITY_REQUIREMENTS` later is a small
  change, whereas retracting a gate operators have built around is not.

### OQ-02: Does this Set's probe satisfy backlog oq05nc's gate for reintroducing a finding code in spec 4.2?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: wcbpqf
- Resolution or deferral rationale: DELIBERATELY LEFT OPEN FOR THE MAINTAINER, and it does not block
  this Set because every plan here refuses to add a code regardless of the answer. The factual
  precondition oq05nc states ("Only after such a probe exists may a finding code be reintroduced in
  4.2") is met for the first time by child 01. What remains is a judgement this repository has
  twice got wrong in the same direction: whether a boundary that filters BY DESTINATION, trusts its
  own allow list, and is unavailable on hosts that cannot create a namespace, is strong enough for a
  reporting code that reads as a proof of push denial. The honest input to that decision is research
  `akmzyq`'s "what is NOT established" list. Carried by `wcbpqf`, which already holds this area's
  maintainer decisions, so the question does not vanish when these plans reach `executed`.
  REVIEW NOTE (2026-10-07): `wcbpqf` is `graduated` and its only handoff plan, `d5ntkj`, is in
  `not-executed/`, and its body names only the `denypush` decisions. It still surfaces as `active`
  in `aw attention`, so the carrier is visible, but the maintainer should add this question to it
  (or file a fresh carrier) when ruling on `denypush`, since nothing in its text yet mentions it.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: The pasted `- Status: executed` line of `nxh5s4` from `.aw/records/plans/executed/`, the pasted `aw ipd lint --phase post-transition --agent` result for it, and its V-01 real-host `(bool, note)` QUOTED from its record (not re-run here).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: The pasted `- Status: executed` line of `rozdkp` and its post-transition lint result, plus its V-01 (unlisted destination DENIED) and V-03 (broker decision log, parent process) evidence QUOTED from its record.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This Set builds a security boundary, and backlog `sv9ce4` warns it is `1o4eif`-magnitude work that
"should not be picked up casually". That warning stands, with one correction the authoring
measurements force: the item also records the mechanism as BLOCKED on the measuring host, and that is
host-specific rather than general. Research `akmzyq` measured the whole mechanism working end to end
on the authoring host, including a real `git ls-remote` refused with `rc 128` while an allow-listed
HTTPS endpoint succeeded, and including the confined agent's own teardown attempt being refused. So
the risk in this Set is not feasibility. It is OVERCLAIM.

WHAT A REVIEWER SHOULD PUSH HARDEST ON. First, that no plan here lets the capability be set True by
anything other than an executed two-sided probe, since this area's entire history is of names
promising more than they delivered. Second, that child 03 drops `CAP_NET_ADMIN`: without it the
boundary is removable in one command (measured, `FLUSH SUCCEEDED`), and a plan could pass review
describing a convention as a boundary. Third, that every teardown check is verified from OUTSIDE the
sandbox, because the authoring measurement that nearly reported the wrong answer did so by trusting a
pipeline's exit status over the parent's own view of the rules. Fourth, that the capability's note
names the limits that remain: an allow-listed host is reachable for ANY purpose, a model endpoint
that proxies traffic would be a hole, and nothing here is proven off Linux.

Execution contract: commit only the paths named in each plan's `Scope-Paths`, through
`aw commit <plan> -- <paths>`, never `git add -A`, and never push. This is a SHARED CHECKOUT: verify
the staged set with `git diff --cached --name-only` before committing, unstage anything that is not
yours with `git restore --staged <path>`, and re-verify after any failed raw commit attempt. Run the
suite BARE as `python3 -m pytest` and PASTE ITS ACTUAL SUMMARY LINE; a summary you did not produce is
not evidence, and that hard-MUST governs every pasted probe verdict, grep count, and exit status the
`V-*` items demand. Paste skips explicitly rather than letting a green line hide one.

LIFECYCLE TRANSITION. This plan is an ORCHESTRATOR: under `aw oc run` / `aw agy run` the runner
RETIRES it to `executed` once every child is `executed` on disk, spending no agent turn, so do not
invoke `aw ipd finalize` on it in a runner-driven execution. A HAND execution of the Set runs the
children in Order and then finalizes this plan last. Never hand-edit `- Status:` and never hand-roll
a `git mv` into `executed/`. Backlog `sv9ce4` must NOT be set `done` by any plan here. It is
currently `open` (the 2026-10-06 coverage demotion reopened it with "re-run graduation to complete
the handoff"), so graduation must be RE-RUN once this Set is back at `to-review` or later; the
correct state after that is `graduated`, never `done`, while the boundary is designed and handed off.
Scope fence: each plan's `Scope-Paths` is a DECLARATION; an out-of-scope edit is made and then
justified at finalize with `--scope-reason`, never a reason to stop.
