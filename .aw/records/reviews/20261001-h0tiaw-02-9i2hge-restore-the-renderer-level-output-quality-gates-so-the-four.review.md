# Review findings: plan 9i2hge

- Subject-Id: 9i2hge
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `8fecdffcb`. The plan was committed and unchanged, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before revision, and `review-finalize` was clean after it.

Re-measured at review:
- `git show 19313eed7^:tests/test_cli_quality_gates.py` recovers the module. Its imports are `from tests.conformance_matrix import ANSI_RE, GOLDEN_DIR`, it has seven gate classes, `BYTE_BUDGET = 1200`, `TOKEN_BUDGET = 400`, and no `pytestmark`.
- The module was executed in-process from stdin, with `AW_CONFORMANCE_UPDATE_GOLDENS` asserted unset and nothing written to the tree: `Ran 14 tests in 0.289s`, `FAILED (failures=1)`. The one failure is `test_human_plain_goldens_stable (fixture='check_findings')`, with the golden reading `Fix: run 'aw rename plans a.md' ...` and the render reading `Fix: a.md does not carry a clustered identity ...`. E-01's prediction still holds at HEAD. `git status --short` was empty afterwards.
- `_read_or_write_golden` reads `if UPDATE or not path.exists(): path.write_text(...); return actual`, which matches F-06.
- `git ls-files tests/fixtures/conformance_goldens` lists 12 files. Neither `tests/test_cli_quality_gates.py` nor `tests/test_conformance_matrix_structure.py` exists yet.
- `CONTRIBUTING.md` step 6 (line 244) matches the quoted text. `tests/test_exit_contract_conformance.py:141` carries `@pytest.mark.slow`. `.github/workflows/tests.yml` has the slow step with `continue-on-error: true`.
- Sibling `dq9bj9` is `reviewed` / `go-pending-approval`. Its E-03 keeps `GOLDEN_DIR` and `ANSI_RE`. It keeps `RunResult`, `Exemption` and `_pinned_env` as internal with zero importers. Its F-08 permits a third undeclared-leaf assertion if it is labelled as a precondition. `tests/test_model_vocab.py:385` contains `test_10_zero_undeclared_leaves`.
- Orchestrator `l8wvv3` assigns the orphan and tripled checks to this plan's E-06/V-06.
- Carriers `2wowfy` and `h0tiaw` exist in `backlog/open/`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Cross-plan consistency | E-06(c) "NOT re-made by `dq9bj9`'s `tests/test_conformance_matrix_structure.py`"; `dq9bj9` E-04 lists "zero undeclared parser leaves" among its four assertions and F-08 permits it "as the matrix's own precondition" | E-06(c) would FAIL on the design the sibling plan explicitly permits, so an executor following both plans faithfully would report a false Set failure. | all Low | FIXED | E-06(c), its outcome and V-06 now accept either absence or presence labelled as a precondition. |
| PR-002 | MEDIUM | IN-SCOPE | E. Evidence feasibility | E-06(b) "either a test imports it or it is absent"; `dq9bj9` E-03 keeps `RunResult`, `Exemption`, `_pinned_env` with zero importers | The orphan check had no category for names that are used internally but never imported, so it would flag three names the sibling plan keeps deliberately. | all Low | FIXED | Added a third category, "used internally by an imported name", and required re-derivation at execution. |
| PR-003 | LOW | IN-SCOPE | E. Evidence strength | E-06(a) tree-wide `rg '\.golden' --glob '!*.golden'` "returns at least one hit" | Plan and review prose under `.aw/records/` already match, so the check passes trivially without any test reading the goldens. | all Low | FIXED | Scoped to `tests/`, and each golden must be mapped to its reading test method and fixture/suffix pair. |
| PR-004 | LOW | UNDER-SCOPE | G. Execution contract | Approval gate | Missing: the hard-MUST paste-actual-output rule, the scope-fence declaration wording, and conditional runner or executor ownership of finalize. | all Low | FIXED | Added all three. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which plan yields on the tripled-assertion conflict? | This plan (9i2hge) relaxes E-06(c) | Edit `dq9bj9` to forbid the third assertion | `dq9bj9` is already `reviewed`, and its F-08 rationale (a precondition for the coverage assertion) is sound; this review is scoped to 9i2hge | yes |
| D-2 | Keep the "stop if a second golden is staged" clause? | Keep | Remove it as a scope-question stop | It guards a possible concurrent-lane edit to a reviewed artifact, which is the legitimate unsafe-condition case plan-review preserves | yes |
