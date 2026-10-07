# Review findings: plan l8wvv3

- Subject-Id: l8wvv3
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `e737e47eb`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`. `aw ipd coverage l8wvv3`: ready
before revision; after revision the lint reported `IPD-S408 coverage-record-stale` (fingerprint mismatch, an
expected consequence of editing), and re-running `aw ipd coverage l8wvv3 --no-commit` (attempt 1 of 2) returned
`ready: true, findings: []` and rewrote the fingerprint; `--phase review-finalize` then `clean`. Child table
rows: 2 -> 2 (no deletion).

Verified at review: children `dq9bj9` (`reviewed`) and `9i2hge` (`to-review`) exist in `pending/` with matching
Set/Order/Id; `9i2hge` declares `- Item-Dependencies: executed:dq9bj9`; `9i2hge` E-06/V-06 owns the Set-level
orphaned-golden, orphaned-symbol and tripled-assertion checks; `tests/conformance_matrix.py` still carries
three `citation="dtq6jr"` entries (`EXEMPTION_REGISTRY`) and `dtq6jr` is in `backlog/done/`;
`build_matrix(_build_parser())` returns `declared_absent == []` and `undeclared == []`; `68sur3` and `lbbo9s`
are both in `backlog/done/` (the latter via executed plan `7pnneh`); `2wowfy` is open and `vfv2db` pending, so
all live carriers resolve; `tests/fixtures/conformance_goldens/` holds 12 tracked files; `Exemption` now has a
live importer (`tests/test_command_surface_declarations.py`, via `gm9baj`), which child 01 already records.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric G (stale premise) | plan Completion criteria "The two non-conformant leaves ... stay with their filed owners (`68sur3`, `lbbo9s`)"; F-04; Proposed change 1 "pin widened to both filed absences"; `build_matrix(...).declared_absent == []`; both items in `backlog/done/` | Orchestrator still described the `declared_absent` pin as widened to two live absences, contradicting child `dq9bj9` E-04 (re-pin to `set()`) and the measured tree. A by-hand executor reading only the parent would set the wrong expectation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Completion criterion, F-04, Proposed change 1, Scope OUT, and the Deferred row now state the review re-measurement and the expected `set()` pin, preserving authoring provenance; `- Carrier-Evidence:` added for both finished carriers (clears `check.ipd-carrier-finished-unverified`). |
| PR-002 | MEDIUM | IN-SCOPE | Rubric G (internal consistency) | Scope "retire the harness's two STALE exemption entries"; E-01 "retire the two stale exemptions"; F-05 heading "TWO EXEMPTION ENTRIES ARE STALE"; `tests/conformance_matrix.py` three `citation="dtq6jr"` | Count of stale exemptions was "two" in four places while F-05's own body, child `dq9bj9` E-02 and the module show three. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All four sites now say three. |
| PR-003 | LOW | IN-SCOPE | Rubric G (cross-reference) | Cross-IPD validation OWNERS "`dq9bj9` V-04"; Required tests "(`dq9bj9` V-04, `9i2hge` V-05)"; `dq9bj9` V-06 carries the failure-set delta, V-04 is the module run | Parent cited the wrong child V-item as the owner of the bare-suite delta. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both citations now name `dq9bj9` V-06. |
| PR-004 | LOW | IN-SCOPE | Rubric G (stale arithmetic) | Concern "eight of its public symbols (... eleven listed)" and "only four (... six listed)" | Counts disagreed with the lists beside them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected to eleven and six. |
| PR-005 | LOW | UNDER-SCOPE | Rubric G (execution contract) | Approval and execution gate (no paste-output rule, no by-hand transition path, no scope-fence statement) | Gate lacked the honesty rule, the conditional runner/by-hand finalize ownership, child ordering for the by-hand path, and a scope-fence declaration. Also the tripled-assertion check did not acknowledge `dq9bj9` F-08's permitted precondition re-check. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added an EXECUTION CONTRACT block (order, conditional transition via runner retirement or `aw ipd finalize`, paste-actual-output, scope fence as declaration); tripled-assertion bullet now allows a stated precondition re-check. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the parent's `68sur3`/`lbbo9s` Deferred rows be deleted now both owners are done? | Keep them, annotated as historical. | Delete. REJECTED: loses provenance of why the original pin existed; carriers still resolve so no lint impact. | `backlog/done/*68sur3*`, `plans/executed/*7pnneh*`; `build_matrix` re-run. | yes |
| D-2 | Does the parent's tripled-assertion check conflict with `dq9bj9` keeping a precondition undeclared-leaf check? | No; reworded to permit a STATED precondition check. | Force child 01 to drop it. REJECTED: child F-08 justifies it as the matrix's own precondition. | `dq9bj9` F-08, E-04. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
