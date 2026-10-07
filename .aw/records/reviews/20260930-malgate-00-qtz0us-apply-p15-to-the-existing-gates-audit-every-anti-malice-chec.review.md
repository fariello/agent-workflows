# Review findings: plan qtz0us

- Subject-Id: qtz0us
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-501 (HIGH, fixed), PR-502 (MEDIUM, fixed), PR-503 (LOW, fixed), PR-504 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `ba977bc5e`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) and `aw ipd coverage qtz0us`
reported ready before semantic review. The plan's own first `- Kind:` bullet reads `orchestrator`.

STATE OF THE SET, re-measured rather than read. All three children are in `.aw/records/plans/executed/` with
`- Status: executed` and every `V-*` reading `Result: pass` with pasted evidence. Execution order matches the
declared sequence: `d9564f8fb` (bec7ee record) precedes `9f70eda69` (38pxaz) which is an ancestor of
`bb0d7c7a1` (dmjp0u). `agent_workflows/wtiso_gate.py` is absent; `AW_MISSING_INPUT = "AW_MISSING_INPUT"` is
defined in `lane_containment.py`; neither "determined same-user agent requires" nor "orchestration
adversarial protections" remains under `agent_workflows/`; the `runner_shared` banner "THE TARGET IS
SLOPPINESS, NOT MALICE" is present; `git show --stat` of the two code commits touches only the declared files
(38pxaz: plan, spec `7ckptx`, `lane_containment.py`, `wtiso_gate.py`, the new token test; dmjp0u: plan,
`ipd_lifecycle.py`, `orchestrate_isolation.py`). So the Set's three recorded cross-checks reproduce.

THE DOMINANT FINDING (PR-501) is that criterion 4 and V-02 demanded evidence no child produced. Both asked
for "each child's own bare `python3 -m pytest` summary line pasted against its pre-execution baseline";
measured inside each child's validation section, none carries a full-suite line (38pxaz V-06 pastes a 4-test
targeted run and two mutation runs; dmjp0u and bec7ee paste none). The only full-suite figures anywhere in
the children are review-time baselines in workflow history. Executed records cannot be amended, so the
reviewer ran the bare suite on the combined tree and recorded it as a Set-level measurement:
`5219 passed, 2 skipped, 3 warnings in 138.58s (0:02:18)`, 256 deselected.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-501 | HIGH | UNDER-SCOPE | Rubric E / G (evidence feasibility) | Plan criterion 4 and V-02 ("quoted from that child's record: the pasted bare `python3 -m pytest` summary line"); `38pxaz` V-06 "4 passed in 0.40s"; no `N passed` line in any child `## Validation` section | Criterion 4's suite half and V-02's suite demand are unsatisfiable from the executed children, so the Set's "no behavior changed" claim had no full-suite evidence behind it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Ran bare suite on the combined tree (5219 passed, 2 skipped); recorded as a Set-level check under Cross-IPD validation owned by `dmjp0u` (last child, combined tree); criterion 4, V-02 and the E-02 validation line rewritten to cite it. |
| PR-502 | MEDIUM | IN-SCOPE | Rubric E (evidence feasibility) | V-01 demanded "a pasted `aw research index --check` confirming it is resolvable"; measured exit 1 with 19 `stale-state-to-promote` findings repo-wide, `wv570i` among them | A green `--check` cannot be produced; the item as written forces a refusal or a false pass. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now demands `aw find research <id6>` plus the `--check` lines naming the record, with only `stale-state-to-promote` tolerated. |
| PR-503 | LOW | IN-SCOPE | Evidence accuracy | `wv570i` summary "DELETE: 11 items" vs 12 `**DELETE**` table rows (1-10, 12, 13); plan Cross-IPD line repeated "11 DELETE rows" | Miscount propagated into the plan's reconciliation claim. No row is un-actored either way. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Plan reconciliation line corrected to 12 with rows named; record miscount noted in Deferred with Carrier-Declined (research record outside this plan's scope). |
| PR-504 | LOW | IN-SCOPE | Records hygiene | `aw research index --check`: "20260930-malgate-00-wv570i-p15-gate-audit.assessment.md: stale-state-to-promote" | Audit record still `status: todo` though cited by executed plans. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded in Deferred with Carrier-Declined: the checker already surfaces it and `aw research promote` is the remedy; not work this orchestrator holds. |

### Coverage repair loop (IPD-S408)

- Attempt 1: after adding the Set-level suite check, `aw ipd coverage qtz0us` reported six uncovered
  obligations (every Cross-IPD bullet, criterion 4, and the Required-tests cross-check line), because the
  new criterion-4 owner read "Set-level measurement" and the Cross-IPD bullets named no child id6. Rows in
  `## Child IPDs`: 3 -> 3.
- Attempt 2: each Cross-IPD bullet, criterion 4 and the cross-check line now lead with an `[Owner: <id6>...]`
  naming the child that performed it and stating nothing is outstanding. `aw ipd coverage qtz0us` reports
  "Orchestrator qtz0us is ready for review." Rows: 3 -> 3. No checklist item deleted.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01: write the audit before remediation or assemble it after? | Resolved as sequenced (before). | Assemble afterwards. Moot: the sequence already ran and the feared record/tree divergence did not occur. | Commit order `d9564f8fb` < `9f70eda69` < `bb0d7c7a1`; `wtiso_gate.py` wholly deleted, matching every DELETE row. | yes |
| D-2 | OQ-02: declare a dependency on `dvonrn` landing first? | No edge, as authored. | Declare the edge. Rejected: `dmjp0u` already executed with `e25iy9` at `approved`, reframed F-1 without naming the token, and `785a687bd` cited it as carrier evidence in `u4glub`/`e25iy9`. | `dmjp0u` V-02 observed evidence; commit `785a687bd`. | yes |
| D-3 | How to satisfy criterion 4's suite evidence when no child recorded one? | Reviewer runs the bare suite on the combined tree and records it as a Set-level measurement owned by the last child. | (a) Leave criterion 4 unsatisfied (NO-GO forever, since executed records cannot change). (b) Edit child records (forbidden by the plan contract). (c) Add a corrective child IPD just to run a suite (gold-plating for a measurement already obtained). | `python3 -m pytest` output in this round; AGENTS.md "Never change what a plan already in executed/ RECORDS". | yes |
