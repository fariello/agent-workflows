# Review findings: plan lxb1ew

- Subject-Id: lxb1ew
- Subject-Type: ipd
- Reviewed-At: 2026-10-11
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed round 2), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (HIGH, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `a8523e163`. The plan was committed (`824ff9e1c`) and byte-identical to the lane input (sha256 `34cede69...`), so no pre-review snapshot. `- Kind: orchestrator`, so S407/S408 apply.

Preflight: `aw ipd lint --phase author --agent` -> `clean` with one `IPD-S408` advisory. `aw ipd coverage lxb1ew` -> `[child-lint-failing] tb6lw3: ... IPD-Q501 OQ-02: BLOCKING question is still 'open'`.

Verified: all eight child plans exist in `pending/` with ids, Orders and `Item-Dependencies` matching the child table exactly (01 none; 02 `executed:tb6lw3`; 03 `executed:tha7a6`; 04 to 07 `executed:mcbph5`; 08 `executed:ytas91, executed:w9nvq4, executed:psgyzw, executed:62sdwr`). `runner_shared.TURN_RETRYABLE_DISPOSITIONS` == `frozenset({'failed-safely'})` (probed). `runner_shared.perform_coordinator_backlog_close` and `runner_shared.ToolIdentityError` exist. Carriers resolve: `coivul` graduated with `Blocks-Release: f33nrj`; release `f33nrj` planned; `p47qfu` pending (ytas91 E-06 supersedes it); `38hwvk` and `oq05nc` open; spec `6kwd2e` approved. All children carry `Blocks-Release: f33nrj`, `From-Backlog: coivul`, `From-Spec: 25kzda`. The parent's E-items are pure child-confirmation orchestration and every completion criterion has a named `iksylm` owner.

### S408 repair attempts

- Attempt 1: `aw ipd coverage lxb1ew` reported `child-lint-failing` for `tb6lw3` (blocking `OQ-02` open, `Owner: maintainer`). Not repairable by a reviewer: resolving it needs the maintainer's ruling. Change made: escalated it into this plan as `OQ-02` (`Blocking: yes`, `Finding: PR-001`) and made Scope and criterion 4 conditional on the ruling.
- Attempt 2: re-ran `aw ipd coverage lxb1ew` after the edit (which also rewrote the stale coverage record to fingerprint `fd50f81b2152`); same single `child-lint-failing (tb6lw3)` finding. Budget exhausted. Plan left `- Status: to-review`, `- Readiness:` ABSENT.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness / human decision | `tb6lw3` OQ-02 (`Blocking: yes`, `Status: open`); `runner_shared.ToolIdentityError`; `aw ipd coverage lxb1ew` child-lint-failing | The orchestrator's Scope and criterion 4 assert "only a corrupt ledger aborts", but shipped code also aborts on a tool-identity mismatch and child 01 has not ruled which; `iksylm` E-04 would test the wrong set either way. | C:Medium; U:Low; S:Medium; F:High; Overall:High | OPEN | Escalated as blocking OQ-02 (answer at `tb6lw3` OQ-02); Scope and criterion 4 rewritten to defer to the ruled set. |
| PR-002 | MEDIUM | IN-SCOPE | Traceability | `## Cross-IPD validation` bullet 1; measured: zero `25kzda` mentions in the Validation sections of Orders 02 to 07 | Claimed each code child's V-items quote the amended spec row; none do, so the claimed owner does not exist. | Overall:Low | FIXED | Ownership reassigned to `iksylm` E-05 (which does map rows to tests) with the measurement recorded. |
| PR-003 | MEDIUM | IN-SCOPE | Architecture (one message path) | Orders 05 and 07 text: zero `build_fix_it_notice` mentions | The "only fix-it text" invariant is not stated in two of the four consuming children. | Overall:Low | FIXED | Noted on the Cross-IPD bullet for those children's reviewers; Set-level check stays `iksylm` E-02. Child plans not edited (out of this review's ledger). |
| PR-004 | LOW | UNDER-SCOPE | Execution contract | `## Approval and execution gate` | Lacked conditional finalize ownership, commit/never-push, paste-output rule. | Overall:Low | FIXED | Added. |
| PR-005 | LOW | IN-SCOPE | Coverage record | `IPD-S408: coverage-record-stale` after edit | Edits invalidated the coverage fingerprint. | Overall:Low | FIXED | `aw ipd coverage lxb1ew` re-run: `Coverage: pass`, fingerprint `fd50f81b2152`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Resolve tb6lw3 OQ-02 here? | No; escalate, owner maintainer. | Adopt the child's recommendation (A). Rejected: it is marked `Owner: maintainer` and changes a spec contract. | `tb6lw3` OQ-02; plan-review Step 3 "never guess a human decision". | yes |
| D-2 | Edit the child plans for PR-003? | No; note it here. | Edit 05/07 (outside this review's ledger). | plan-review 0.1 ledger rule. | yes |

PR-001 is OPEN at HIGH and is escalated as OQ-02 with `- Finding: PR-001`.

### Driver correction turn 1 of 2 (2026-10-08)

- Reported: `[child-lint-failing] tb6lw3: IPD-Q501 OQ-02: BLOCKING question is still 'open'`, remedy "fix the child's named lint finding".
- Searched for a recorded maintainer answer: backlog `coivul` (ruling 2026-10-07 covers push, hook bypass, status changes and out-of-scope edits, not tool identity), spec `25kzda`, and review record `tb6lw3` PR-003 (which raised the question). None answers it.
- Change made: none. The only lint-clearing edits are resolving the question or setting `Blocking: no`. Either one would invent a maintainer decision (`Owner: maintainer`, changes the spec's abort contract) or misclassify a question the child's reviewer judged blocking, so both are refused under plan-review Step 3 ("never guess a human decision"). Rows: 8 -> 8 (child table unchanged). `lxb1ew` stays `to-review` with `- Readiness:` absent, and OQ-02 (`Finding: PR-001`) is still open.
- Needed to proceed: the maintainer answers `tb6lw3` OQ-02 (A: corrupt ledger and tool-identity mismatch both abort, the recommendation; B: ledger only; C: tool identity counts as a corrupt ledger), then resolves `lxb1ew` OQ-02 citing that answer.

### Driver correction turn 2 of 2 (2026-10-08)

- Reported: the same `[child-lint-failing] tb6lw3: IPD-Q501 OQ-02` finding as turn 1.
- Re-checked: `tb6lw3` OQ-02 is still `Blocking: yes`, `Status: open`. No answer has landed in `.aw/records/comms/` (inbox empty) or in any Set record since turn 1 (`fa8b56bec`).
- Change made: none, for the same reason as turn 1. Clearing the finding requires a maintainer decision, which a reviewer may not invent. Rows: 8 -> 8.
- Outcome (R6 honest exhaustion): the correction budget (2) is exhausted with the finding unresolved. `lxb1ew` stays `- Status: to-review`, `- Readiness:` stays ABSENT, and OQ-02 / PR-001 stay open. Next step: the maintainer answers `tb6lw3` OQ-02, then `/plan-review` is run again on `tb6lw3` and `lxb1ew`.

## Round 2

Re-reviewed 2026-10-11 in an isolated review lane at HEAD `4b191408f`. The plan was committed and byte-identical to the
lane input (sha256 prefix `06856086e608d32f`), so no pre-review snapshot. `aw ipd lint --phase author --agent` ->
`clean`. `aw ipd coverage lxb1ew` -> "Orchestrator lxb1ew is ready for review." (no S407/S408 findings, so no repair
loop was needed). After the edits, `coverage` was re-run to refresh the fingerprint, and
`aw ipd lint --phase review-finalize --agent` -> `clean`.

Re-verified: child status on disk is `tb6lw3`, `tha7a6`, `mcbph5`, `w9nvq4`, `psgyzw` executed; `ytas91` approved;
`62sdwr` and `iksylm` to-review. All eight carry `- From-Backlog: coivul` and `- Blocks-Release: f33nrj` (release
`2.0.0`, `Status: planned`), and their `Item-Dependencies` match the child table. `tb6lw3` OQ-02 reads "Resolved by
maintainer 2026-10-08: Option B chosen", Carrier `03y5g6`. Spec `25kzda` now reads "**ABORT RUN**: stop all dispatch
only for corrupt run ledger", and `run_evidence.ABORT_CLASSES` is `("Corrupt run ledger",)`. Backlog `03y5g6` is
`open`, `Work-Kind: bug`, `Blocks-Release: next`. Shipped code still aborts on tool identity in both hosts:
`oc_runipd.run_queue` and `agy_runipd.run_queue` both have `except ToolIdentityError:` ... `raise`, commented
"RUN-FATAL". `runner_shared.build_fix_it_notice` exists; it is named by Orders 04, 05 and 06 and not by Order 07.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness / human decision | `lxb1ew` OQ-02 `Status: resolved` (maintainer 2026-10-08, via `tb6lw3` OQ-02 Option B) | Stale: the escalated question is answered. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Cleared on the answered OQ-02 (`- Finding: PR-001`). Scope, criterion 4 and the child table rewritten to the ruled set (corrupt ledger only). |
| PR-006 | HIGH | IN-SCOPE | Anti-regression / spec-code agreement | `oc_runipd.run_queue` and `agy_runipd.run_queue` `except ToolIdentityError: ... raise` ("RUN-FATAL"); backlog `03y5g6` open; criteria 4 and 5 as written | With Option B, criterion 4 ("No run aborts except on ... the abort set") and criterion 5 ("spec, transcription and behavior agree") are unsatisfiable by this Set: the spec and `ABORT_CLASSES` say ledger-only, the code still aborts on tool identity, and the ruling moved that change outside the Set. `iksylm` would either fail or overclaim. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Criterion 4 now covers the classes this Set touches and forbids reporting "only a corrupt ledger aborts" while `03y5g6` is open. Criterion 5 permits exactly one named divergence that E-05 must record. Added a Deferred row and a Scope exclusion, both with Carrier `03y5g6`. |
| PR-007 | LOW | IN-SCOPE | Traceability (stale measurement) | Cross-IPD bullet 2: "Orders 05 and 07 do not name the builder"; measured `build_fix_it_notice` mentions: 04=2, 05 present, 06=2, 07=0 | Order 05 now names the builder. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Re-measured and rewritten: only Order 07 (`62sdwr`) lacks the name. |
| PR-008 | LOW | IN-SCOPE | Execution contract (stale gate) | Gate: "OQ-02 is blocking and must be resolved ... before this plan can be reviewed"; OQ-02 Context "(blocking, open)" | Gate and context still described the question as open. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now records the resolution and notes that `62sdwr` and `iksylm` are still `to-review`. Context updated. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-3 | How should the orchestrator's criteria treat the tool-identity abort the ruling moved out of the Set? | Name it as the one permitted divergence, carried by `03y5g6`, and forbid the "only a corrupt ledger aborts" claim while it is open. | (a) Add a child to change `run_queue`: rejected, since the maintainer filed it as a separate backlog item and adding a child widens the Set's scope. (b) Leave the criteria as written: rejected, they would be unsatisfiable. | `tb6lw3` OQ-02 resolution text ("carrier backlog item `03y5g6` is filed to update `run_queue`"); backlog `03y5g6`. | yes |
