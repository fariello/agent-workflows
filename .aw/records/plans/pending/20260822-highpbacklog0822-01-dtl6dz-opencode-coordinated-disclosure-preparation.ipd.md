# IPD: OpenCode Coordinated Disclosure Preparation

- Date: 2026-08-22
- Kind: child
- Concern: Make the OpenCode unauthenticated-local-server disclosure ready for a human to send, without an agent authoring or sending the report.
- Scope: Verify and assemble the existing disclosure-package artifacts and create a disclosure-lifecycle tracking record; NO agent-authored report text, NO send, NO clock start.
- Status: draft
- Set: highpbacklog0822
- Order: 1
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: dtl6dz

## Workflow history

- 2026-08-22 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created for backlog 2p6mgq, respecting the prior decision (retired IPD 20260819-backlog-medhigh-260819-03-38yl4s) that disclosure drafting and sending are human-owned.

## Goal

Bring the coordinated disclosure to a state where the human can review one assembled packet and send it, and track the 30-45 day clock, without an agent writing or transmitting the vulnerability report.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Inventory and verify the existing package

- [ ] E-01 Read `.aw/records/research/opencode-security/disclosure-package/00-README-index.md` and verify every artifact it references (advisory, executive summary, maintainer-scoping draft, test evidence, source validation, patch proposal, provenance) is present and readable; record any missing/archived artifact by its citation handle.
  - Depends on: none
  - Expected outcome: a verified inventory of the disclosure package with every referenced artifact accounted for or flagged missing.
  - Execution state: pending

### Material change 2: Create the tracking record

- [ ] E-02 Create a disclosure-lifecycle tracking record (under `.aw/records/` in the project's existing record convention) with fields: finding handle, package location, intended recipient/channel (per OpenCode's SECURITY.md), planned-vs-actual send date, the 30-45 day clock window (unstarted), and current status `prepared-awaiting-human-send`.
  - Depends on: E-01
  - Expected outcome: one tracking record exists that a human updates when they send; the clock is explicitly not started.
  - Execution state: pending

### Material change 3: Stage the human hand-off note

- [ ] E-03 Write a short hand-off note in the tracking record telling the human exactly what to review, that OpenCode's SECURITY.md bans AI-generated reports so the send MUST be human-authored/verified, and the single next action (review package, then send); do NOT author send-ready report prose.
  - Depends on: E-02
  - Expected outcome: the human has a one-glance next action and the human-owned boundary is stated in the record.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The disclosure package index lives at `.aw/records/research/opencode-security/disclosure-package/00-README-index.md`; the retired IPD `20260819-backlog-medhigh-260819-03-38yl4s` is the most complete on-disk narrative and cites the finding handles (advisory `kams1a`, exec summary `98m3pw`, etc.) and DECISIONS D86/D87.
- OpenCode's SECURITY.md bans AI-generated reports and treats opted-in server access as partly out-of-scope; the send must be human-authored and human-verified.
- A reusable reproduction/refutation protocol exists at `.aw/records/prompts/reusable/20260716-1342-01-opencode-cross-user-verification-protocol.prompt.md`.

## Findings

The finding is documented but the on-disk package is sparse: only the index is under `disclosure-package/`; several cited handle artifacts may be archived/renamed. The prior decision left disclosure human-owned and `2p6mgq` open. The gap this plan closes is preparation and tracking, not authorship or transmission.

## Proposed changes (ordered, validatable)

1. Verified package inventory (E-01).
2. A disclosure-lifecycle tracking record with an unstarted clock (E-02).
3. A human hand-off note stating the human-owned boundary and the single next action (E-03).

No source code changes. No agent-authored vulnerability report. No email/issue/send.

## Deferred / out of scope (with reason)

- Drafting the vulnerability report text: human-owned (OpenCode SECURITY.md bans AI-generated reports).
- Sending the disclosure and starting the 30-45 day clock: human-owned.
- Re-running the reproduction protocol: the finding is already validated; not needed to prepare the packet.

## Scope check

- Over-scope: none.
- Under-scope: if a cited artifact is genuinely missing (not just archived), flag it in the inventory for the human; do not reconstruct it as agent-authored disclosure text.

## Required tests / validation

Documentation-only change; no automated test. Validation is that the inventory accounts for every referenced artifact and the tracking record exists with the clock explicitly unstarted and the human-owned boundary stated. Run `aw sanitize --agent` on the new record to confirm it leaks no maintainer/machine identifying info, and paste the output.

## Spec / documentation sync

No spec change. The new tracking record IS the durable documentation; link it from the disclosure-package index if the convention allows.

## Open questions

### OQ-01: Where should the tracking record live and in what record class?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: place it under `.aw/records/research/opencode-security/` (the finding's existing home) as a tracking note, following the directory's README convention; if that directory defines no tracking-record class, use a plainly-named `disclosure-tracking.md` in that directory and link it from `00-README-index.md`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the inventory lists every artifact referenced by `00-README-index.md` with a present/missing verdict per artifact; paste the inventory.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the tracking record exists with all required fields, status `prepared-awaiting-human-send`, and the clock explicitly unstarted; `aw sanitize --agent` on it reports zero findings (paste the run).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the hand-off note states the human-owned/human-verified boundary and a single next action, and contains NO agent-authored report prose; quote the note.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three preparation steps around one human-owned disclosure; no code and no send.

Review and explicit approval required.

### Execution contract

1. Open questions RESOLVED: OQ-01 above is resolved; no blocking question remains. `Depends on: none`.
2. Scope fence: touch only files under `.aw/records/research/opencode-security/` (the inventory and the new tracking record) and, if the convention allows, a link from the package index. Do NOT write agent-authored disclosure/report text, do NOT send anything, do NOT start the clock, and do NOT change source code. If preparing seems to require authoring the report, STOP and report to the human.
3. Honesty rule (hard MUST): if you report the sanitizer or inventory checks passed, paste the ACTUAL output; never claim a check you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit. Backlog `2p6mgq` stays `open`/`parked` on the human send (it is closed only when the human actually sends the disclosure), so do NOT set `2p6mgq` to `done` from this plan.
