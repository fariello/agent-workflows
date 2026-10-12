# Review: Correct host_runner redaction docstrings to say detected-and-refused, not masked

- Subject-Id: 0ev8cz
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Verified at lane HEAD `04ba026c0`; no commit since the plan's measured HEAD `8c520062c` touches
`agent_workflows/host_runner.py`, `security_hardening.py`, `tests/test_host_runner_redaction.py`, or
`docs/security.md`. Plan committed and unchanged (snapshot skipped). `aw ipd lint --phase author`
reported `clean` before review.

- Module docstring REDACTION bullet ends "a planted home-path/secret is masked/blocked." (F-01 true).
- `redact_worker_output` docstring "Returns (possibly-masked RawWorkerResult, BoundaryResult)." and the
  inline comment "The RedactionPolicy masks matched secrets/keys; ..." both present (F-02 true).
- `default_redaction_policy` passes no patterns and keys `authorization`..`bearer`;
  `RedactionPolicy._redact_value` masks only on `parent_key in sensitive_keys` or pattern match, so
  `stdout`/`stderr`/`diff` values are never changed (F-02 mechanism true).
- `check_evidence_redaction` only detects via `ls.scan_text` and returns `ok=False` (F-03 true).
- `run_task` replaces with `[REDACTED-LEAK]` and uses `WORKER_FAILED_FINAL` (F-04 true).
- `python3 -m pytest -o addopts="" -q tests/test_host_runner_redaction.py` -> `2 passed in 0.22s` (F-05).
- `docs/security.md` boundary 4 already accurate (F-06 true).
- F-08 FALSE: pending `n09qoq` declares `host_runner.py` and depends on `executed:0ev8cz`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A. Correctness (evidence) / cross-plan coupling | `.aw/records/plans/pending/20261012-lfko0e-01-n09qoq-gate-worker-output-evidence-on-the-canonical-secret-scanner.ipd.md:7-8` (Scope-Paths includes `agent_workflows/host_runner.py`; `Item-Dependencies: executed:0ev8cz`), `:60` (E-06 (iii) replaces "any statement that free-text credential detection is not evaluated (or the `lfko0e` citation)") | F-08 claims no pending plan declares `host_runner.py`; `n09qoq` does, and its E-06 (iii) edits the exact bullet this plan's E-01 writes. E-01 allowed "say so OR cite lfko0e", leaving the downstream plan to find either form. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-08 corrected with the sibling and its dependency edge. E-01 now requires BOTH the explicit "not evaluated" statement and the `lfko0e` citation; V-01 now demands a grep showing both, so `n09qoq` can locate the text it replaces. |
| PR-002 | LOW | IN-SCOPE | G. Executability (execution contract) | plan `## Approval and execution gate` (was: "transition the plan to `executed/` through the tooled lifecycle (`aw ipd` begin/finalize)"); `plan-review.md` Step 4 lifecycle rule | The gate instructed finalize unconditionally and lacked conditional runner/executor ownership and an explicit scope-fence declaration. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now states the runner owns finalize under `aw oc run`/`aw agy run`, the hand executor runs `aw ipd finalize 0ev8cz`, never hand `git mv`, and the scope fence is a declaration justified via `--scope-reason`. |
| PR-003 | LOW | IN-SCOPE | Citation convention | plan E-02 said the quoted sentence is on the docstring's "first line"; actual: second line of the first paragraph (`agent_workflows/host_runner.py`, `redact_worker_output`) | Positional description slightly wrong; the quoted string itself resolves. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 re-anchored to "the sentence ... at the end of its first paragraph". |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should E-01 require both the "not evaluated" statement and the `lfko0e` citation? | Require both | Keep "either"; drop the credential sentence entirely | `n09qoq` E-06 (iii) and its `executed:0ev8cz` edge (`...n09qoq...ipd.md:8,60`); `docs/security.md` boundary 4 states both | yes |
| D-2 | Is OQ-01 (option a vs b) correctly resolved without a human? | Keep resolved (a) | Reopen as blocking | `tests/test_host_runner_redaction.py` pins non-masking (`2 passed`); `n09qoq` OQ-02 independently keeps refuse-not-mask; comment-only change is trivially reversible | yes |
