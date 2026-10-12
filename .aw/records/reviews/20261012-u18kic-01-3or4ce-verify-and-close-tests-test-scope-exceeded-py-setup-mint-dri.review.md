# Review findings: plan 3or4ce

- Subject-Id: 3or4ce
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `142f2c5b7` in an isolated review lane. The plan was committed and unchanged (`ec0074360`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified:
- Commit `64b8c94f3` ("test(scope_exceeded): drop the deleted driver-attestation setup") deletes 7 lines from `tests/test_scope_exceeded.py`. Commit `86181232a` is `work(e25iy9): Delete driver token ...`.
- `grep -rn mint_driver_attestation agent_workflows tests --include=*.py` returned no output (rc=1). `git grep -n mint_driver_attestation -- ':!*.md'` returned no output.
- `python3 -m pytest -o addopts="" tests/test_scope_exceeded.py -q` gave `7 passed in 1.78s`. The module has one class, `TestScopeExceededMetadataAndSendBack`, with 7 `test_*` methods.
- `u18kic` is `graduated` with `Blocks-Release: next`. This plan is its only `From-Backlog` carrier and carries the same gate.
- Duplicates `fdkkco` and `i6dzbj` are `done`, closed with walkthrough `04qifi` as evidence.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Evidence feasibility | `pyproject.toml` `addopts` (`-q -n auto`); AGENTS.md repo-local contract | E-02 ran `python3 -m pytest tests/test_scope_exceeded.py` with the configured defaults, which give a quiet xdist run with no per-test lines. The bars "`7 passed`" were also a test-count bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02, V-02 and V-03 now use `-o addopts="" -v` and require every collected test to pass. The count of 7 is kept as context only. |
| PR-002 | LOW | IN-SCOPE | Evidence | `grep -rn` over `tests/` includes `__pycache__` binaries and untracked files | E-01 searched the working tree instead of tracked files, so stale `.pyc` files or untracked files could produce false hits. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 and V-01 now use `git grep` with the exit status recorded, and Markdown history mentions are explicitly excluded as non-callers. |
| PR-003 | MEDIUM | UNDER-SCOPE | Release gate / provenance | `.aw/records/backlog/done/20261009-fdkkco-...`, `...-i6dzbj-...` (`Close-Evidence: ...04qifi...`) | The plan did not mention that two duplicate items for the same defect are already `done`. It also did not say how `u18kic`, which carries `Blocks-Release: next`, closes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-5 and a closing note naming the HANDOFF route, with runner and hand variants. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the OQ status, the scope-as-declaration wording (including `--scope-ack` for the expected no-change outcome), `aw ipd begin`, the staged-set check, conditional finalize ownership and the no-`git mv` rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with every element. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Retire this plan as redundant, given the fix already landed and its duplicates are closed? | No; keep a verify-and-close plan | Close `u18kic` by hand with `--evidence` walkthrough `04qifi` (skips the pasted re-verification the gated item requires) | `u18kic` `Blocks-Release: next`; AGENTS.md release-gate HANDOFF rule; the plan's own V-items produce the evidence | yes |
