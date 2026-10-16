# Review findings: plan lpvcln

- Subject-Id: lpvcln
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `71d02242b`. The plan was committed and byte-identical to the lane input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean`. The plan is a child, not an orchestrator.

Verified by a scratch probe on `conformance_matrix.seed_ledger_fixture` (probe deleted afterwards):
- F-1: `runs decisions|questions <id>` under `--agent` and `--json` print `_No autonomous decisions recorded._` / `_No unresolved questions._` as raw text, rc 1.
- F-2: `runs evidence --agent` printed `"ledger":"<ROOT>/.aw/records/runs/<id>/ledger.jsonl"`, and the human header was absolute too.
- F-3: `runs verify-ledger` human printed `Ledger: <ROOT>/...`; its machine output carries no path.
- Also measured: `runs show` human printed `Ledger: <ROOT>/... (2 records)`, and a missing projection printed the absolute path `<ROOT>/.aw/workflow-artifacts/exec-set/nosuch/decisions.md` in human, `--agent` and `--json` modes (rc 2).
- `agent_schema.normalize_repo_path` on a `ghp_` path keeps the token, and `run_cli._redact_output` then scrubs it to `[REDACTED]`, so `test_projection_leaves_path_secret_redacted` stays satisfiable.
- `EXEMPTION_REGISTRY` counts: `sanctioned_raw: 11, not_runnable: 11`. `compute_conformance_universe` removes both kinds from the universe, so the not_runnable-to-sanctioned_raw move does not add the leaves to the aw.agent/v1 sweep. `test_command_surface_declarations` validates only `UNREACHABLE_COMMAND_ALLOW_SET` kinds.
- Baseline: `python3 -m pytest -o addopts="" -q tests/test_live_conformance_sweep.py tests/test_agent_surface_conformance.py tests/test_command_surface_declarations.py tests/test_run_cli_human_redaction.py tests/test_run_cli_error_payload_keys.py tests/test_run_init.py` -> `212 passed in 285.65s`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Durable-carrier rule / Rubric D (same defect) | `agent_workflows/run_cli.py:526` `_run_show` human `Ledger:`; `run_cli._emit_not_a_ledger` `"path": str(exc.path)`; the plan's deferred row 2 said "Recommend a follow-up backlog item" | The same absolute-path defect in the same file was deferred with no carrier, so it would vanish once the plan executed (`check.ipd-uncarried-obligation` fired on it). E-01 also printed the absolute path on the human missing-projection line. | all Low | FIXED | Added E-07/V-07 for `runs show` and `_emit_not_a_ledger`. E-01 now makes the missing-projection human line relative as well. Tests (g) and (h) added to E-04. The deferred row was removed. |
| PR-002 | MEDIUM | UNDER-SCOPE | Durable-carrier rule | pre-transition lint: `check.ipd-uncarried-obligation: 3 obligation(s) ... deferred row 1, 2, 3` | The deferred rows had no typed carrier fields. | all Low | FIXED | Added `Carrier-Declined` with a reason to the two remaining rows. The carrier rule no longer fires. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric E (RED proof) | V-04 "a note (or pasted run against a stash-free scratch revert)" | The RED proof could be satisfied by a note, and the test module was written after the fix, so RED was never captured. | all Low | FIXED | E-04 is now authored first (E-01/02/03/07 depend on it). V-04 requires the pasted RED run and GREEN run, and a note is refused. |
| PR-004 | MEDIUM | IN-SCOPE | Gate execution contract | old gate: one sentence, no scope fence, no resolved-OQ statement, "move the plan to `executed/`" | The gate lacked a scope-fence declaration, the paste-actual-output MUST, the resolved-OQ statement, and runner/executor ownership of the transition. | all Low | FIXED | Rewrote the gate with all of them; by hand the transition uses `aw ipd finalize`, never a hand `git mv`. |
| PR-005 | LOW | IN-SCOPE | Rubric E (validation completeness) / OQ owner | V-05 omitted the routine gate, `aw sanitize`, and `test_run_cli_error_payload_keys`/`test_run_init`; OQ-01 `Owner: none` | The Required tests were not demanded by any V item, `tests/test_run_recovery_cli.py` (which pins the not-a-ledger verdict) was absent, and OQ-01 had no owner. | all Low | FIXED | V-05 now demands the full Required-tests command, routine gate, sanitizer and diffs. `tests/test_run_recovery_cli.py` was added to Required tests. OQ-01 owner is now `plan author`. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Fold the `runs show` / not-a-ledger path leaks in, or file a backlog item? | Fold in as E-07. | File a new backlog item and add `- Carrier:` (REJECTED: two small edits in the same file and the same defect; a separate item adds a round trip and no isolation benefit). | Probe output above; `run_cli._run_show`, `run_cli._emit_not_a_ledger`; hbok5d's D92 rationale applies to them equally. | yes |
| D-2 | Should the missing-projection HUMAN line become relative (human output change)? | Yes. | Keep it absolute so human output is byte-identical (REJECTED: it would disagree with the machine `path`, and it is the same leak). | `test_projection_leaves_path_secret_redacted` asserts only rc 2 and redaction, which the review measured still hold. | yes |
| D-3 | Does moving the two exemptions to `sanctioned_raw` change the aw.agent/v1 universe? | No; both kinds are subtracted from the universe. | Delete the exemptions (REJECTED: the leaves would join the aw.agent/v1 universe and fail, because the payload is a bare dict by design, F-16). | `tests/test_agent_surface_conformance.py` `compute_conformance_universe` `candidates - set(EXEMPTION_REGISTRY.keys())`. | yes |
