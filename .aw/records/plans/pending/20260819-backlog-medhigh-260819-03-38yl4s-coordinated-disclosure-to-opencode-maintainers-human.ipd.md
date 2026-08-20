# IPD: coordinated disclosure to opencode maintainers human

- Date: 2026-08-19
- Kind: child
- Concern: Prepare the AGENT-doable artifacts for coordinated disclosure to the OpenCode maintainers of the previously verified unauthenticated local-server finding: a self-contained disclosure packet assembled from the cited internal finding records, and a tracking record for the disclosure lifecycle. The actual SEND and the 30-45 day coordinated-disclosure clock are HUMAN-OWNED and explicitly out of scope.
- Scope: Authoring and organizing tracked artifacts under `.aw/records/` only. No code change, no network send, no starting of a disclosure clock, no publication. Backlog item `2p6mgq` is touched only to annotate it; it is NOT closed to done by this plan (see OQ-01).
- Status: draft
- Set: backlog-medhigh-260819
- Order: 3
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 38yl4s

## Workflow history

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-19 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): drafted the body from the cited finding records (advisory `kams1a`, executive summary `98m3pw`, disclosure-package index, maintainer-scoping draft `zmgkwf`, D86/D87). Send + clock kept human-owned and out of scope.

## Goal

Produce the artifacts an agent CAN safely produce so the human is one confident step away from sending a coordinated-disclosure report to the OpenCode maintainers: (1) a human-ready disclosure packet assembled from the already-verified internal finding records, and (2) a tracking record that follows the disclosure through send, acknowledgement, and the 30-45 day deadline. This plan deliberately stops at the point where a human must send; an agent must never send a disclosure or start a disclosure clock.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: assemble the disclosure packet from cited records

- [ ] E-01 Read and confirm the cited internal finding records are present and self-consistent: the advisory `.aw/records/research/20260716-opencode-unauthenticated-local-server-advisory-00-kams1a-...advisory.md`, the executive summary `.aw/records/research/20260716-ocsec-00-98m3pw-executive-summary-and-report.executive-summary.md`, the disclosure-package index `.aw/records/research/opencode-security/disclosure-package/00-README-index.md`, and the maintainer-scoping draft `.aw/records/research/20260716-ocsec-08-zmgkwf-maintainer-scoping-question-draft-for-human.research-report.md`.
  - Depends on: none
  - Expected outcome: A short confirmation note (in this plan's walkthrough or the tracking record) listing each source path and that it exists; any missing source is flagged rather than invented.
  - Execution state: pending

- [ ] E-02 Assemble the disclosure packet document under `.aw/records/research/opencode-security/disclosure-package/` (a new markdown file created via `aw research` naming, or an addition consistent with the existing index) that ASSEMBLES FROM THE CITED FINDING RECORDS: a high-level finding description, impact, affected-versions placeholder, suggested remediation, and the coordinated-disclosure timeline. It cites the source records by path rather than restating exploit specifics, and marks every field the human must fill (exact affected version + commit, recipient/contact, send date) as an explicit `HUMAN FILLS` placeholder.
  - Depends on: E-01
  - Expected outcome: A packet file exists that a human can read top-to-bottom, contains no secret/exploit detail beyond what the internal advisory already frames at a high level, and carries visible `HUMAN FILLS` placeholders for every human-owned specific.
  - Execution state: pending

- [ ] E-03 Add a prominent header to the packet stating the SEND and the 30-45 day clock are HUMAN-OWNED, that OpenCode's SECURITY.md bans AI-generated reports (so the human must rewrite in their own voice and be able to defend each claim), and that nothing here is published.
  - Depends on: E-02
  - Expected outcome: The packet's opening section explicitly names the human-owned send + clock and the AI-report caveat, mirroring the honesty notes already in the disclosure-package index.
  - Execution state: pending

### Task group 2: create the tracking record and a human send-checklist

- [ ] E-04 Create a tracking record (an `aw backlog`-adjacent note or a dedicated tracking markdown under `.aw/records/research/opencode-security/disclosure-package/`) that tracks the disclosure lifecycle states the human will advance: `packet-drafted` -> `sent (date + recipient)` -> `acknowledged (date)` -> `deadline (send + 30-45 days)` -> `resolved/published`. The tracking record starts at `packet-drafted` and leaves all downstream dates blank for the human.
  - Depends on: E-02
  - Expected outcome: A tracking record exists with the lifecycle states enumerated, only `packet-drafted` marked done, and all send/ack/deadline fields empty and labelled human-owned.
  - Execution state: pending

- [ ] E-05 Add a human send-checklist to the packet (or tracking record) drawn from the maintainer-scoping draft: re-pin exact latest released version + commit, use synthetic credentials only, submit via the private GitHub Security Advisory channel, choose scope framing, and record the send date to start the clock. The checklist items are unchecked and addressed to the human.
  - Depends on: E-02
  - Expected outcome: A checklist of human pre-send actions exists, unchecked, with each item phrased as an action for the human, and it references the private security channel without inventing new contact details.
  - Execution state: pending

- [ ] E-06 Annotate backlog item `2p6mgq` with a workflow-history note recording that the agent-doable artifacts (packet + tracking record) are drafted and that the item REMAINS OPEN until the human sends the disclosure (per OQ-01). Do NOT set the item to done. Use `aw backlog set --status open --message ...` so the annotation is recorded without changing disposition.
  - Depends on: E-02, E-04
  - Expected outcome: `2p6mgq` remains `open` with a new history line noting the drafted artifacts and that the human still owns the send; the item is not moved to done.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The finding is already fully recorded and cross-reviewed internally. It is decision D86 in `DECISIONS.md` (OpenCode local control server is unauthenticated-by-default; cross-user stealth hijack confirmed on shared hosts) with the use-stance D87. Disclosure posture is stated as COORDINATED with a 30-45 day deadline, kept internal until then.
- A disclosure package already exists under `.aw/records/research/opencode-security/disclosure-package/` (currently just `00-README-index.md`) and points at the sibling `ocsec` research files (executive summary `98m3pw`, test evidence `vcnu3f`, source validation `e4ule1`, patch proposal `jfoccf`, provenance `zhkhky`). The advisory `kams1a` is the consolidated finding record.
- A maintainer-scoping draft (`zmgkwf`) already exists, explicitly written FOR A HUMAN to rewrite and send; it names the private GitHub Security Advisory channel and stresses OpenCode's SECURITY.md ban on AI-generated reports.
- Research/analysis relied on for a decision is immortalized under `.aw/records/research/` via the `aw research` verbs; committed backlog work lives under `.aw/records/backlog/` managed by `aw backlog new|set|check`; the leak sanitizer is `aw sanitize --agent`.
- The agent execution contract forbids sending disclosures, starting a disclosure clock, publishing, or pushing. All artifacts here are tracked-file authoring only.

## Findings

At a high level (no exploit specifics restated here; see the cited records):

| Item | High-level statement | Source record |
|------|----------------------|---------------|
| Finding class | OpenCode's local control HTTP server is unauthenticated by default; on shared/multi-user hosts this enables cross-user reach of an opted-in server. | D86 in `DECISIONS.md`; advisory `kams1a` |
| Verification | Verified across two real Unix accounts and source-validated; adversarially cross-reviewed by independent AI agents. | executive summary `98m3pw`; disclosure-package index |
| Severity/posture | High on shared/multi-user hosts running an unsecured listener; negligible single-user; mitigable today via server password. | D86; advisory `kams1a` |
| In-scope candidates | The narrower items likely separate from "you opted into server mode" (e.g. secret return via the config endpoint, a non-loopback bind footgun) are the recommended disclosure focus. | maintainer-scoping draft `zmgkwf` |
| Disclosure posture | Coordinated: notify maintainers privately first, hold public disclosure until they respond or a 30-45 day deadline elapses; internal-only until then; AI-report ban means a human must author/verify. | D86; disclosure-package index; scoping draft `zmgkwf` |

The finding detail is sufficient in the cited records; this plan's packet ASSEMBLES from them and marks human-owned specifics (exact affected version + commit, recipient, send date, final scope framing) as placeholders rather than inventing them.

## Proposed changes (ordered, validatable)

1. Confirm the cited finding records exist and are self-consistent (E-01).
2. Assemble the human-ready disclosure packet from those records, with `HUMAN FILLS` placeholders and no secret/exploit specifics (E-02).
3. Add the human-owned-send + AI-report-ban header to the packet (E-03).
4. Create the disclosure lifecycle tracking record starting at `packet-drafted` (E-04).
5. Add the human pre-send checklist drawn from the scoping draft (E-05).
6. Annotate backlog `2p6mgq` that artifacts are drafted and the item stays open until the human sends (E-06).

## Deferred / out of scope (with reason)

- The actual SEND of the disclosure + starting the disclosure clock is HUMAN-OWNED (agent must not send). An agent must never transmit a security disclosure to a third party, contact maintainers, open a security advisory, or begin the 30-45 day coordinated-disclosure timer. Reason: the send is an irreversible external action with legal, reputational, and coordination consequences, and OpenCode's SECURITY.md requires a human-authored, human-verifiable report; the human owns timing, recipient, and final wording.
- Choosing the recipient/contact and the exact send date: human decision (see OQ-01), left as placeholders in the packet.
- Re-pinning exact affected version + commit against the current upstream release: human verification step, listed in the send-checklist, not performed here (our internal line numbers came from a fork's `dev` and must be re-verified).
- Any code change, patch submission, or PR to OpenCode: out of scope; the patch proposal already exists as a design spec (`jfoccf`) and its submission is a separate human-owned decision.
- Publication of the advisory: out of scope; everything stays internal until the coordinated-disclosure process resolves.

## Scope check

- Over-scope: none. This plan does not send, publish, contact anyone, change code, or start a clock.
- Under-scope: the disclosure is NOT completed by this plan; the load-bearing act (the human send) is intentionally left out. That is by design: the slug's `-human` suffix marks the send as human-owned. The plan produces only the artifacts that make the human's send fast and safe.

## Required tests / validation

This is a documentation/process item; validation is artifact existence plus clean sanitizer/spec checks, not a pytest suite.

- The disclosure packet file exists and is readable, contains the high-level finding/impact/remediation/timeline, cites its source records by path, and carries `HUMAN FILLS` placeholders for human-owned specifics.
- The tracking record exists and enumerates the disclosure lifecycle states with only `packet-drafted` marked.
- `aw specs check --agent` (and `aw backlog check`) report clean for any records this plan touches.
- `aw sanitize --agent` reports clean: no maintainer/machine identifying info, no live secret, no exploit specifics leaked into the new artifacts (exit zero, no `fail`).
- Backlog `2p6mgq` remains `open` with the new annotation; it is NOT moved to done.

## Spec / documentation sync

- No spec change required. The finding and disclosure posture are already recorded in `DECISIONS.md` (D86/D87) and the `ocsec` research set. The new packet and tracking record are additions consistent with the existing disclosure-package index; if the index enumerates a fixed contents list, update it to reference the new packet/tracking files. `aw research index --check` should pass after any research-tree addition.

## Open questions

### OQ-01: Does executing this DRAFT close backlog `2p6mgq`, or does the item stay OPEN until the human sends?

- Blocking: no
- Status: open
- Owner: human/maintainer
- Resolution or deferral rationale: RECOMMEND leaving `2p6mgq` OPEN. The disclosure is not complete until it is actually sent to the maintainers, and the send is human-owned. Executing this plan completes only the agent-doable artifacts (packet + tracking record). Closing the item to done on artifact creation would falsely assert the disclosure happened. Therefore E-06 annotates the item that artifacts are drafted while keeping it `open`; the human closes it (or the tracking record advances) once the disclosure is sent. The recipient/contact and the exact send date are human decisions and remain placeholders in the packet.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: The confirmation note lists each cited source path and its existence; any missing source is flagged, none invented.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: The disclosure packet file exists; it contains high-level finding/impact/affected-versions-placeholder/remediation/timeline, cites source records by path, and shows `HUMAN FILLS` placeholders for human-owned specifics; it restates no exploit specifics beyond the advisory's high-level framing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: The packet's opening section explicitly states the send + 30-45 day clock are human-owned and names the AI-report caveat.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: The tracking record exists, enumerates the lifecycle states (`packet-drafted` -> `sent` -> `acknowledged` -> `deadline` -> `resolved/published`), marks only `packet-drafted`, and leaves send/ack/deadline fields blank and labelled human-owned.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: The human send-checklist exists, unchecked, addressed to the human, referencing the private security channel and the re-pin/synthetic-credentials steps, inventing no new contact details.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `aw backlog check` passes; `2p6mgq` is still under `open/` with a new workflow-history line noting drafted artifacts and human-owned send; the item is not in `done/`. Additionally `aw sanitize --agent` and `aw specs check --agent` exit clean over the touched artifacts.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is AGENT-doable authoring only: it drafts a disclosure packet and a tracking record and annotates a backlog item, all as tracked files under `.aw/records/`. Per the agent execution contract, the executor commits only the files it changed, path-scoped, never `git add -A` and never pushes; it pastes actual `aw sanitize --agent`, `aw specs check --agent`, and `aw backlog check` output as evidence rather than claiming success. The executor MUST NOT send the disclosure, contact the maintainers, open a security advisory, publish anything, or start the 30-45 day clock; those are human-owned and out of scope. Do not mark this plan executed or move it to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item is verified with concrete evidence. Backlog `2p6mgq` stays OPEN (OQ-01); the human closes it after the send.
