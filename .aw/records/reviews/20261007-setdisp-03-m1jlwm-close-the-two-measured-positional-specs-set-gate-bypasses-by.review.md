# Review findings: plan m1jlwm

- Subject-Id: m1jlwm
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was committed and byte-identical to the lane input, so no
pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; `--phase review-finalize` after revision:
`clean`. Not an orchestrator.

Re-measured in a scratch repo with the lane package pinned (`PYTHONPATH`, `AW_NO_REEXEC=1`):
`specs set implemented abc123 --no-commit` on an `implementing` spec with no `--evidence` -> rc 0, file moved
to `specs/implemented/` (F-01 bypass LIVE). `specs set deferred def456 --gate-kind bogus-kind --gate-ref x`
-> refused ("aw set: --gate-kind must be one of [...]. Refusing before making changes."), file still in
`approved/`, no `Gate-*` line (F-02 bypass CLOSED). `python3 -m pytest -o addopts="" -n 4
tests/test_gate_pair_validation_parity.py` -> `12 passed in 2.00s`. Code: `status_set.validate_transition_allowed`
calls `attention_contract.validate_gate_flags` (kind, ref, summary) under the comment "setdispgate ju3rhs
E-02"; `specs._evidence_resolvable` accepts `.agents/plans/executed` or `.aw/records/plans/executed`. Records:
`ju3rhs` executed (`From-Backlog: fv4b6s`, Scope-Paths include `backlog.py`, `CHANGELOG.md`); `wdyz5n` approved
(`From-Backlog: h4fiwa`, deps none); `h4fiwa` and `fv4b6s` both `graduated`; CHANGELOG already carries the
gate-kind entry.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | C (duplicate path) / D | E-02 "Make the `deferred` gate-pair VALIDATION fire on the POSITIONAL spelling"; `status_set.validate_transition_allowed` "setdispgate ju3rhs E-02 ... validate_gate_flags"; scratch probe refused | E-02 orders a fix that executed plan `ju3rhs` already shipped. Running it as written would add a second copy of the validation, which is the exact defect class this Set exists to end. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now confirms only, with no production edit, and fixes any regression by consuming `validate_gate_flags`. F-02, Proposed change 2, V-02 and OQ-02 are updated. |
| PR-002 | HIGH | IN-SCOPE | Release-gate rules (AGENTS.md close-legitimacy) | E-05 "`aw backlog set done h4fiwa --evidence <this plan's executed path>`"; `h4fiwa`/`fv4b6s` `- Status: graduated` to `wdyz5n`/`ju3rhs` | Both carriers already belong to other plans that carry their `From-Backlog` gates. This plan closing them with SATISFIED would bypass the HANDOFF owner, and for `h4fiwa` could close the item before `wdyz5n` executes. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-05 and V-05 now record status and route. This plan closes an item only if its carrier plan was superseded unexecuted. A CHANGELOG entry is added only for a refusal no existing entry describes. |
| PR-003 | MEDIUM | IN-SCOPE | C (overlap) | `wdyz5n` approved, `Item-Dependencies: none`, same evidence fix; `63zo2f` OQ-02 "whichever executes second must consume" | E-01 ignored the parallel carrier that will probably land first. | Overall:Low | FIXED | E-01 now first checks `wdyz5n`. If it is executed, E-01 only confirms; otherwise it implements and notes the consume obligation. The expected outcome names the installing plan and requires one implementation. |
| PR-004 | MEDIUM | IN-SCOPE | E (unsatisfiable evidence) | E-03 outcome "cases (a), (b) and (d) demonstrably FAIL on the base commit"; F-02 closed at base | Case (d) cannot fail on the current base, and (a)/(b) cannot fail on base either if `wdyz5n` lands first. Deferred cases also duplicated `tests/test_gate_pair_validation_parity.py`. | Overall:Low | FIXED | Base failure is now demanded only for (a)/(b) when this plan implements E-01; otherwise sensitivity comes from a throwaway revert. Deferred cases are added only where the existing file does not cover them, with a per-case table. |
| PR-005 | LOW | IN-SCOPE | G (OQ resolvable; contract) | OQ-01/OQ-02 open with Owner executor; `_evidence_resolvable` return line; gate lacked finalize ownership and scope-ack | Both questions can be answered from code now. The gate lacked the conditional finalize step and `--scope-ack` for declared paths that may go untouched. | Overall:Low | FIXED | OQ-01 resolved (YES: the message wording is stale). OQ-02 resolved (backlog is already validated). The gate paragraph is extended. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Retire `m1jlwm` as superseded by setdispgate, or keep it? | Keep, reshaped to consume-and-pin; implement the evidence fix here only if `wdyz5n` has not landed. | Retire now. REJECTED: the F-01 bypass is still live and orchestrator `63zo2f` OQ-02 already chose to keep all three plans. | `63zo2f` OQ-02; scratch probe. | yes |
| D-2 | Who closes `h4fiwa`/`fv4b6s`? | Their graduated carrier plans, via HANDOFF. | This plan via SATISFIED. REJECTED: preempts the gate owners. | Both items `graduated` to `wdyz5n`/`ju3rhs`; AGENTS.md close-legitimacy rule. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
