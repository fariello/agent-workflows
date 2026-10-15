# Review findings: plan tosnwd

- Subject-Id: tosnwd
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`a6ba82d2e`), so no snapshot was needed. `aw ipd lint --phase author` was clean before review. `--phase review-finalize` is clean after the revisions. `--phase pre-transition` no longer reports `check.ipd-uncarried-obligation`.

Re-measured at HEAD `ba8709ea4` with a scratch prototype under the gitignored `.aw/state/`, deleted afterwards:

- The four not-mine releases gave `[True, True, True, True]`.
- The differing record keys were `['suite_baseline']` for completed-vs-absent, corroborating-vs-contradicting, and absent-vs-None.
- `mine` gave `False False mine ['suite_baseline']`.

E-03 mechanism check: plugins rebinding `runner_shared.perform_gate_answer`, run with `-o addopts="" -p <plugin>`:

| Run | Result |
|---|---|
| unmutated | `2 passed` |
| mutant A | `1 failed, 1 passed` |
| mutant B | `1 failed, 1 passed` |
| mutant C (fail closed on unknown baseline) | `1 failed, 1 passed` |

The cited history resolves: `80db6750c^:tests/test_suite_baseline.py` holds `class NothingRefusesOnTheBaseline` at line 892, and `19313eed7` deleted the file.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | G. Lifecycle gate | pre-transition lint: `check.ipd-uncarried-obligation 3 obligation(s) name no durable carrier: deferred row 1, deferred row 2, deferred row 3` | None of the three Deferred rows had a carrier, so the plan could never finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a reasoned `Carrier-Declined` to each row. The rule is cleared. |
| PR-002 | MEDIUM | UNDER-SCOPE | D. Anti-regression / docs honesty | `agent_workflows/runner_shared.py` `perform_gate_answer` docstring: "(deleted in `19313eed`; no live guard currently asserts this)" | Once this plan lands, the production docstring would falsely say the property is unguarded and point readers at a deleted file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F5, plus E-04/V-04 for a docstring-only correction. `runner_shared.py` added to Scope-Paths. The commit step is renumbered to E-05/V-05. |
| PR-003 | MEDIUM | IN-SCOPE | E. Mutation coverage | `perform_gate_answer` docstring: "`not-mine` -> RELEASE ... in ANY run"; review mutant C killed | The probe covered refusal on a contradicting baseline and rescue of `mine`, but not the most plausible well-meant regression: failing closed when the baseline is absent or unknown. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added mutant C to E-03/V-03. |
| PR-004 | LOW | IN-SCOPE | E. Test robustness | `validate_gate_answer` "a `not-mine`/`fixed` with no reason ... yield an unusable verdict" | E-01 did not require a reason in the answer dict. Omitting one makes the test fail for the wrong reason. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires a non-empty `reason` and asserts `record["answer"] == "not-mine"`. |
| PR-005 | LOW | IN-SCOPE | AGENTS.md test-run rule / E. Evidence | E-03 command `-o addopts="" -q -n0 -p ...`; V-01 `rg` pattern matching `inspect` or `ast.` as bare text | `-n0` was redundant once `addopts` is cleared, and the repo contract forbids it. V-01's regex would also match ordinary words such as "last." in prose. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Dropped `-n0` with an explanation, and tightened the V-01 pattern to imports, attribute use, `getsource` and `read_text(`. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract | old gate: "Move the plan to `.aw/records/plans/executed/` only after ..." | The gate implied a hand move and lacked the ownership split and scope fence. OQ-01 had `Owner: none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with the standard contract and set the owner to the plan author. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Correct the stale production docstring in this plan? | Yes, docstring only | Leave it (the docstring would lie); file a separate backlog item (more process for a one-line truth fix) | `runner_shared.perform_gate_answer` docstring | yes |
| D-2 | Add a CHANGELOG line? | No | Add one | Test-only plus an internal docstring; no user-visible change | yes |
| D-3 | Accept OQ-01 (new purpose-named file)? | Yes, as authored | Recreate `tests/test_suite_baseline.py` | `df486j` precedent cited in the plan | yes |
