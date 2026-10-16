# Review findings: plan x9z0ve

- Subject-Id: x9z0ve
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `9232fa963`. Plan committed and byte-identical to the lane
input (sha256 `fff311cf...`), so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`.
Not an orchestrator (`- Kind: child`).

Re-measured at HEAD: `tests/test_run_evidence_completion.py` absent; spec `25kzda` is the single match of
`*-25kzda-*.spec.md` (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-...spec.md`);
`run_cli.EXIT_CORRUPTED_LEDGER == 5`; `run_evidence.ABORT_CLASSES == ('Corrupt run ledger',)`; zero
`ABORT_CONDITIONAL` codes; `f1f1bb5d7` and `552cf7f01` subjects match the plan. A scratch copy under
`.aw/state/` with the id6 lookup: `3 failed, 81 passed in 14.38s`, the same three node ids as E-01. After
E-02 (a)-(c) as written: one residual failure (PR-001). After the extra edit: `84 passed in 8.11s`. E-03
sabotage plugin demonstrated: two `TestCompletionPredicates` failures. Scratch files deleted;
`git status --short` clean.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Rubric D/E (masked superseded assertion) | `19313eed^:tests/test_run_evidence_completion.py` `test_conditional_abort_is_not_reported_as_unconditional` trailing `assertEqual(sorted(always), ["RUN-BASELINE-OWNERSHIP", "RUN-LEDGER-INTEGRITY"])`; `git show 552cf7f01 -- agent_workflows/run_evidence.py` (`RUN-BASELINE-OWNERSHIP` `ABORT_ALWAYS` -> `ABORT_NEVER`) | E-02 (c) updated only the first assertion of that test. A second superseded assertion in the same test is hidden behind the first. Executed as written, the module would still fail, so E-02's "all tests pass" outcome could not be reached. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 (c) now also updates the `always` list to `["RUN-LEDGER-INTEGRITY"]`, citing `552cf7f01`. Demonstrated `84 passed`. Added F4; V-02 diff demand includes the hunk. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric G (test-organization bars) | plan E-01 Expected outcome "81 pass and exactly ... fail"; V-02 "expected 84" | Bars were set as collected and passed counts, which are artifacts of test organization. | all Low | FIXED | The bar is now: collects, every failure is mapped to a superseding commit, then zero failures/errors. Counts kept as context. |
| PR-003 | LOW | UNDER-SCOPE | Rubric D | plan E-01 restores by `>` redirect | The restore would silently overwrite a module recreated by another change. | all Low | FIXED | E-01 now checks `git ls-files` first and stops if the file exists. V-01 requires the output. |
| PR-004 | LOW | IN-SCOPE | Rubric E (evidence) | plan E-03 | The sabotage mechanism was undemonstrated. | all Low | FIXED | Demonstrated at review (F5). Observed node ids added as non-binding pointers. |

Advisory `IPD-Z602` (info) on E-02 (multi-clause action): kept as one item. The three edits share one
concern (superseded-contract assertions in one module) and one V-02 test surface. See D-2.
`aw ipd lint --phase review-finalize --agent` after revisions: `clean` (1 info).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Update the masked `always` assertion, or treat it as a regression? | Update, citing `552cf7f01`. | File as `bug` (REJECTED: `552cf7f01` deliberately reclassified it, and spec `25kzda` 4.2 now reads "FAIL ITEM"). | `git show 552cf7f01`; spec 25kzda line 907. | yes |
| D-2 | Split E-02 per IPD-Z602? | Keep as one item. | Three E-items (REJECTED: one file, one concern, one validation). | Plan right-sizing rule; V-02 single diff. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
