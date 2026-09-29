# IPD: Record the measured Landlock feasibility and amend spec 25kzda 5.2 to state what a host can and cannot enforce

- Date: 2026-09-29
- Kind: child
- Concern: Spec `25kzda` 5.2 asks whether a host can "deny push-capable network routes and withhold remote credentials" and the repository has never measured whether ANY host can. Plan `4h7tt0` named OS-level enforcement as the only candidate without an agent-level evasion but declined it for scope, leaving the feasibility question unanswered in writing. This plan answers it with measured evidence and amends the spec to say what is actually enforceable, so the next reader inherits a measurement rather than a direction.
- Scope: Amend spec `25kzda` 5.2's push-denial requirement to carry the measured Landlock result (ABI 4 network denial is real, but port-granular and therefore cannot separate a git remote from the model API on TCP 443), and amend `host_sandbox_profile`'s module docstring where it currently declares network scoping out of scope. Records only: this plan adds NO probe, NO capability field, and NO finding code.
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, agent_workflows/host_sandbox_profile.py, .aw/records/research/20260929-denypush-00-uq4y6q-landlock-network-push-denial-feasibility.findings.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: low
- From-Backlog: oq05nc
- Set: denypush
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: x2dwu5

## Workflow history

- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored review-ready while graduating backlog `oq05nc`. Carries the measured Landlock findings (`uq4y6q`) into the spec.

## Goal

Replace the repository's unmeasured assumption about push denial with a measured one, in the two
places that assert it: spec `25kzda` 5.2's host requirement list and `host_sandbox_profile`'s module
docstring. After this plan a reader learns, from the spec itself, that kernel-level network denial is
available at Landlock ABI 4 and that it is PORT-GRANULAR, so it cannot by itself deny an HTTPS push
without also denying the model API the agent needs. No code behavior changes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the measurement on the executing host

- [ ] E-01 Re-run the three Landlock probes from research `uq4y6q` on the executing host and retain their verbatim output: (a) a `CONNECT_TCP` ruleset with one `LANDLOCK_RULE_NET_PORT` rule allowing a loopback listener, proving the allowed connect succeeds AND a port-443 connect is refused; (b) a combined ruleset carrying both `handled_access_fs` and `handled_access_net`, proving one `restrict_self` enforces both classes; (c) a port-443-allowed ruleset connecting to two distinct hosts on 443 and one on 22, proving the rule is port-granular and address-blind. Do NOT add these scripts to the tree (research `uq4y6q` records why a throwaway measurement script that nothing calls would rot).
  - Depends on: none
  - Expected outcome: Three captured outputs. If the executing host reports Landlock ABI < 4, (a) and (b) legitimately report unsupported; record that verbatim and treat it as the measurement, since a host-specific result is the expected shape here and the spec amendment in E-03 must then say the capability was unavailable on the measuring host rather than asserting a universal.
  - Execution state: pending

### Task group 2: amend the two records that currently assert or disclaim this

- [ ] E-02 Amend `host_sandbox_profile`'s module docstring, whose published-guarantees section currently ends with the sentence "Network scoping and container isolation are out of scope here." Replace the network half of that claim with the measured position: network scoping is now MEASURED rather than out of scope, `handled_access_net` is already the second member of the ruleset attr `landlock_bootstrap_source` packs (it passes a literal `0` today), and the reason no network rule is added is the port-granularity limit, not absence of a mechanism. Keep container isolation out of scope, which is unchanged and still true.
  - Depends on: E-01
  - Expected outcome: The docstring names the measured limit and stops implying nobody looked. No code outside the docstring is touched by this item, so no test behavior changes.
  - Execution state: pending

- [ ] E-03 Amend spec `25kzda` 5.2 in place. The bullet "deny push-capable network routes and withhold remote credentials" STAYS (plan `01reg8` deliberately preserved it as this work's landing site, and its own deferred row says narrowing it "would delete that work's landing site"). Add prose immediately after the existing paragraph that already explains why the requirement outlived 4.2's `RUN-NO-PUSH`, recording: that the requirement is now MEASURED and not merely aspirational; that kernel-level TCP denial is real at Landlock ABI 4 with two-sided proof; that the mechanism is port-granular with no address field, so it cannot separate a git remote from the model API on 443; that the credential half is ALREADY built and shipped (`oc_runipd._hardened_credential_paths` makes `~/.ssh`, `~/.netrc`, `~/.git-credentials`, `~/.config/gh` and peers inaccessible in hardened mode, wired through `build_sandbox_plan`'s `credential_paths`); and that the remaining gap is host-granular filtering. State explicitly that no host reports this capability today and the answer remains fail-closed.
  - Depends on: E-01
  - Expected outcome: 5.2 records the measurement and the credential half already shipped. The requirement bullet, the 5.2 action table, and the 5.6 packet example's `deny_push` string are all UNCHANGED, so nothing that depends on them moves.
  - Execution state: pending

- [ ] E-04 Append a `## Workflow history` record to spec `25kzda` with `aw specs note` naming this plan and the measurement, and set research `uq4y6q`'s outcome and consumed-by provenance with `aw research set-outcome` so the findings doc is linked to the plan that consumed it. Refresh the research manifest with `aw research index`.
  - Depends on: E-03
  - Expected outcome: The spec's history shows the amendment with its date and this plan's id6; `aw research find --id uq4y6q` reports the consumed-by link; `aw research index --check` reports no drift.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This plan's subject is itself a case study: backlog `oq05nc` cites the anti-inference rule at `host_sandbox_profile.py:109-115`, plan `4h7tt0` cites the SAME rule at `:88-95`, and both are stale. Every citation below names a symbol or quotes a string.
- A plan may amend a spec and MUST declare it (AGENTS.md). The spec file is therefore listed in `Scope-Paths`, which is what makes the amendment legitimate rather than a silent weakening, and what makes both runners announce the declared spec edit before the run starts.
- Spec status is owned by `aw specs`, and history is appended with `aw specs note` rather than hand-edited. This plan does NOT change the spec's `- Status:` (it stays `approved`); it amends content and appends history.
- A capability may only be set True by code that executed a probe for it (`HostSandboxCapabilities`' own docstring: "an UNPROBED host claims NOTHING"). This plan adds no capability at all, so it cannot violate that; it is named because the Order-02 sibling depends on it.
- Research artifacts are created and indexed with `aw research`, never hand-named (AGENTS.md). `uq4y6q` was created that way.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | Landlock ABI 4 network denial WORKS on the measuring host, two-sided | Research `uq4y6q` Finding 1: `abi: 4`, allowed loopback connect `True`, port-443 connect `PermissionError(13, 'Permission denied')`, `RESULT: ENFORCED` | The direction `4h7tt0` named is reachable. The spec may honestly stop calling it hypothetical. |
| F-2 | One ruleset carries BOTH fs and net rules | Research `uq4y6q` Finding 2: combined ruleset, `fs denied write: EPERM -> ENFORCED` and `net 443: EPERM -> ENFORCED` | `landlock_bootstrap_source` extends in place. Its `struct.pack("=QQ", ALL, 0)` already passes `handled_access_net` as that literal `0`. |
| F-3 | Net rules are PORT-ONLY, with no address field | Research `uq4y6q` Finding 3: `net_port rule struct size: 16 (allowed_access u64 + port u64; NO address field)`; with 443 allowed, BOTH `140.82.113.4:443` and `1.1.1.1:443` connected, while `:22` was refused | THE governing limit. A port rule cannot separate a git remote from the model API. This is what the spec amendment must say. |
| F-4 | The confined process is the one that needs the model API | `oc_runipd._apply_execution_profile` is called on the worker `argv` that launches the coding agent; `enter_sandbox` wraps that argv | Denying 443 denies the product. Allowing 443 permits HTTPS push. Neither setting is the goal, so Landlock alone is not a push boundary. |
| F-5 | The CREDENTIAL half of 5.2's requirement is already built and shipped | `oc_runipd._hardened_credential_paths` enumerates `~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.netrc`, `~/.git-credentials`, `~/.config/gh`, `~/.docker/config.json`, `~/.kube`, `~/.npmrc`, `~/.pypirc`; passed as `build_sandbox_plan(credential_paths=...)`, which folds them into the INACCESSIBLE class | The spec understates what exists. 5.2's bullet is two requirements joined by "and", and one of them is DONE in hardened mode. Saying so is part of making the record honest. |
| F-6 | `supports_deny_push` no longer exists, and a live test pins its absence | Plan `01reg8` removed the field, `CAP_DENY_PUSH`, and three unconsumed verdicts; `tests/test_host_capability_extension.py` class `DenyPushRemovedTests` asserts the field is absent from `dataclasses.fields(HostSandboxCapabilities)`, that `CAP_DENY_PUSH` is absent from `hsp.__all__`, and that `aw host capabilities` output contains no `deny_push` | This plan must NOT reintroduce the name. It touches no code path that test reads, which is deliberate: the name question belongs to the Order-02 sibling. |
| F-7 | Reintroducing a finding code is gated and expensive | `run_evidence.validate_finding_table` hard-fails `len(RUN_FINDING_CODES) != 12` with `RC-COUNT`; spec 4.2's own prose says "adding or removing a row here without amending that invariant makes the SHIPPED table report itself invalid at runtime"; backlog `oq05nc` says "Only after such a probe exists may a finding code be reintroduced in 4.2" | No finding code in this Set. The gate is not met: no probe exists yet, and after Order 02 the probe will prove port denial, not push denial. |
| F-8 | The measurement is host-specific by construction | Research `uq4y6q` host table: `bwrap`, `unshare` and `slirp4netns` are ALL installed, yet `unshare -Urn --map-root-user true` fails `write failed /proc/self/uid_map: Operation not permitted` | E-01 re-measures on the executing host rather than trusting `uq4y6q`'s numbers. This is the same measured counterexample that made the existing probes attempt-not-inspect. |

## Proposed changes (ordered, validatable)

1. Re-measure on the executing host and retain verbatim output (E-01). Nothing is edited until the
   evidence exists, because the whole point of this plan is that the record should follow a
   measurement and not the reverse.
2. Amend `host_sandbox_profile`'s module docstring so its network disclaimer matches the measurement
   (E-02). Docstring-only; no symbol, signature, or behavior changes.
3. Amend spec `25kzda` 5.2 with the measured position, the already-shipped credential half, and the
   named remaining gap (E-03). Additive prose; the requirement bullet and both tables are untouched.
4. Record provenance on both records with the owning tools (E-04).

## Deferred / out of scope (with reason)

- BUILDING the probe or the capability field: that is the Order-02 sibling's whole job, and keeping
  it out of this plan is what lets the spec amendment be reviewed on its own merits rather than
  bundled with a code change.
  - Carrier: pi3bk8
- HOST-GRANULAR network filtering (network namespace plus a filtering proxy), which is the only
  mechanism that would close the 443 gap F-3 and F-4 identify. It is unavailable on the measuring
  host today (F-8) and is the `1o4eif`-magnitude project `d07nz2` predicted.
  - Carrier: sv9ce4
- REINTRODUCING a `RUN-NO-PUSH`-shaped finding code. Gated by F-7 and explicitly by backlog
  `oq05nc`, and the gate is not met by this Set: after Order 02 the proven capability is port
  denial, not push denial. Binding a push-denial code to a port probe would be precisely the
  fail-OPEN inference `run_evidence`'s retirement comment forbids in writing.
  - Carrier-Declined: NOT WANTED, which is a decision rather than a deferral. The condition for
    reintroduction is stated in the spec and in backlog `oq05nc`, so a future reader can find it
    without anyone asserting that work is owed. Filing a carrier would misrepresent a deliberately
    unmet gate as pending work.
- CHANGING the spec's `- Status:` or its `- Blocks-Release: next`. This plan amends content only;
  status is owned by `aw specs` and the release gate is not this plan's to move.
  - Carrier-Declined: Out of scope by construction; nothing is owed.

## Scope check

- Over-scope: none. Every declared path is read or written by an E-item: the spec by E-03/E-04, the
  module docstring by E-02, the research doc by E-04. The research manifest files
  (`.aw/records/research/INDEX.json`, `INDEX.md`) are deliberately NOT declared even though E-04
  regenerates them: they are GITIGNORED generated artifacts (`.aw/.gitignore` lines 47-48), so
  declaring them would name paths the finalize scope gate can never see committed.
- Under-scope: none. E-01 writes nothing (its scripts are deliberately not retained, per `uq4y6q`),
  and no test file changes because no behavior changes. Confirmed by F-6: this plan touches no path
  `DenyPushRemovedTests` reads.

## Required tests / validation

- Run the suite BARE as `python3 -m pytest` and paste the actual summary line. The expectation is
  unchanged counts: this plan edits one docstring, one spec, and records. A docstring edit CAN break
  a test if one asserts on docstring text, so the run is what establishes it did not.
- `aw ipd lint` on this plan reports conforming.
- `aw check` reports no new violations, specifically none in the `release-gates` family (the spec
  carries `- Blocks-Release: next` and this plan does not move it).
- `aw research index --check` reports no drift after E-04.
- `aw sanitize --agent` reports no `fail` finding on the edited files: E-01's captured probe output is
  pasted into this plan and could carry host-identifying paths, so this is a real check and not a
  formality.

## Spec / documentation sync

- Spec `25kzda` is AMENDED by E-03 and is declared in `Scope-Paths`. WHY the amendment is warranted:
  5.2 currently asks whether a host can deny push-capable routes and withhold credentials, and the
  repository has never measured the first half while the second half is already shipped (F-5). The
  spec is the contract every other plan is reviewed against, so leaving it asserting an unmeasured
  requirement means every future reader re-derives the feasibility question, which is exactly what
  `4h7tt0` left behind and what backlog `oq05nc` exists to stop.
- `host_sandbox_profile`'s module docstring is the published-guarantees contract for this area
  (x03wgn Section 8 Phase 6.3 "publish its guarantees"), so a measured change to what the module
  could enforce belongs there and not only in the spec.
- No `docs/` page changes: `docs/runner-profiles.md` documents how hardened mode is REQUESTED, which
  this plan does not change.
- CHANGELOG: no entry. Nothing user-visible changes; the amendment is to internal contracts.

## Open questions

### OQ-01: Should spec 25kzda 5.2's single bullet be SPLIT into its two independent halves, given that the credential half is shipped and the network half is not?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: wcbpqf
- Resolution or deferral rationale: NOT BLOCKING, because E-03 is written to be correct either way:
  it adds prose recording that the credential half is already enforced in hardened mode and the
  network half is not, which makes the asymmetry readable without restructuring the list. The case
  FOR splitting is that 5.2's list is a set of independent questions ("answers, independently,
  whether the host can"), and a single bullet joining a DONE requirement to an UNMET one with "and"
  can only ever be answered No, which loses the information that half of it works. The case AGAINST
  is that `01reg8` deliberately preserved this bullet verbatim as this work's landing site and its
  review warned that narrowing it "would collide with backlog `oq05nc`", so re-editing its shape in
  the same breath as claiming to honor it invites the exact confusion that record was protecting
  against. Recommended: keep the bullet, add the prose, and let the maintainer split it later if the
  Order-02 capability makes the asymmetry load-bearing. A reviewer who prefers the split should say
  so at review time, when it is a one-line change to E-03.

### OQ-02: Does amending an `approved` spec require re-approval?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: no. AGENTS.md states plainly
  that "Specs are living contracts, not immutable history: a plan that changes behavior a spec
  describes SHOULD carry the spec amendment in the same change", and the mechanism that makes it
  legitimate is declaring the spec in `Scope-Paths` (done) so both runners announce the declared
  spec edit before the run starts and reconcile it at finalize. Spec `25kzda`'s own
  `## Workflow history` records ten-plus prior amendments by plans while it stayed `approved`,
  including `01reg8`'s removal of `supports_deny_push` from this very area. So the established
  pattern is amend-and-record, not re-approve. This plan does not touch the spec's `- Status:`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: The three probe outputs pasted verbatim, each showing the command's own printed result lines. Probe (a) must show BOTH sides (an allowed connect succeeding AND a denied connect refused), because a one-sided result cannot distinguish an enforcing jail from a permissive one, which is the standard `_denial_checker_source` already sets. Probe (c) must show two distinct hosts connecting on the SAME allowed port, which is what proves address-blindness rather than merely asserting it. A host reporting ABI < 4 must paste that verbatim instead, and V-03 must then reflect the unavailable result rather than a universal claim.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff` of `agent_workflows/host_sandbox_profile.py` showing only docstring lines changed, plus the pasted `python3 -m pytest` summary line showing the suite still passes. Additionally paste `python3 -c "import agent_workflows.host_sandbox_profile as m; print(m.__doc__.count('out of scope'))"` or an equivalent grep proving the stale "Network scoping and container isolation are out of scope here" sentence no longer asserts the network half. The diff must show NO change to any `def`, signature, or constant.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `git diff` of the spec showing the added prose, and a grep proving the three preserved artifacts are BYTE-UNCHANGED: the requirement bullet "deny push-capable network routes and withhold remote credentials", the 5.2 action-table row naming no-push enforcement, and the 5.6 packet example's `"deny_push"` string. The added prose must state all four of: ABI-4 denial is real, it is port-granular and address-blind, the credential half is already shipped, and no host reports the capability today (fail-closed). A diff that removes or narrows the bullet FAILS this item, since `01reg8` preserved it deliberately.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted output of `aw research index --check` reporting no drift, `aw research find --id uq4y6q` showing the consumed-by provenance naming this plan, and the tail of the spec's `## Workflow history` showing the new dated record naming `x2dwu5`. Also paste `aw check` output showing no new violations and `aw sanitize --agent` exiting zero, since V-01's pasted probe output is the realistic leak vector in this plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is records-only by design: it produces a measurement and writes it into the two contracts
that currently assert or disclaim push denial. It adds no probe, no capability field, and no finding
code, so it cannot make any host report a capability it does not have. That separation is deliberate,
because the failure this whole area guards against is a record claiming enforcement that does not
exist, and the cheapest way to re-create it would be to bundle a spec claim with a code change and
review them as one thing.

Execution contract: commit only the paths named in `Scope-Paths`, through `aw commit <plan> -- <paths>`,
never `git add -A`, and never push. Paste actual test output rather than claiming success. On
completion, verify `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete
observed evidence before moving this plan to `.aw/records/plans/executed/`.
