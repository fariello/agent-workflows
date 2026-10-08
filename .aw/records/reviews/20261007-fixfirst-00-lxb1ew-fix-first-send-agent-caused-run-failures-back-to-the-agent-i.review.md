# Review findings: plan lxb1ew

- Subject-Id: lxb1ew
- Subject-Type: ipd
- Reviewed-At: 2026-10-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Findings: PR-001 (HIGH, open), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

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
