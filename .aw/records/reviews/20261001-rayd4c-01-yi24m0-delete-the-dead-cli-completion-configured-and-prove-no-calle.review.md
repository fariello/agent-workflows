# Review findings: plan yi24m0

- Subject-Id: yi24m0
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T032752Z-4094028` at HEAD `baf4983ed`. The plan was
committed and byte-identical to the sealed lane input (rev-13); no snapshot needed. `- Kind: child`, so `IPD-S407`
and `IPD-S408` do not apply. `aw ipd lint --phase author` clean before review; `review-finalize` clean after.

Re-measured: `cli._completion_configured` still defined with zero callers; `cli._completion_state` docstring still
names it; `cli._configure_completion` still calls `_completion.is_completion_installed(shell)`. Plan `s2yf26` is now
in `executed/` (work commit `00c460141`), and `tests/test_completion.StaleCompletionWarningTests`'s docstring no
longer names the deleted symbol. `grep -rn "_completion_configured" --include="*.py" .` now returns three hits: the
`def`, the `_completion_state` docstring, and `tests/test_completion_stale_notice.py`
`self.assertNotIn("_completion_configured", doc)`. `tests/test_completion.py` collects 31 (1 slow).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G executability / stale premise | `tests/test_completion_stale_notice.py:505` `self.assertNotIn("_completion_configured", doc)`; `tests/test_completion.py:2322` "`is_completion_installed` was a PRESENCE check" | `s2yf26` executed after authoring: E-02's target is already corrected, and it added an out-of-scope absence-assertion literal, so E-02/V-02's "zero hits repository-wide" bar was unsatisfiable without editing an undeclared file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01/E-02/V-02 and validation now expect exactly that one literal hit; E-02 is verify-only with a `--scope-ack` for the unmodified file; F-05 annotated moot. |
| PR-002 | LOW | IN-SCOPE | G live-artifact criteria | E-02/V-02 "collected count unchanged at 31" | A collected test count is a test-organization artifact and may not be a V-item bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bar is now equality with the executor's own pre-edit `--collect-only` count; 31 kept as context. |
| PR-003 | LOW | UNDER-SCOPE | Execution contract | Gate "move this plan ... through the tooled lifecycle transition" | Gate lacked conditional runner/executor finalize ownership and the scope-fence-is-a-declaration wording. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate states runner-owned begin/finalize vs manual `aw ipd finalize ... --apply`, never `git mv`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the `assertNotIn("_completion_configured", ...)` literal in `tests/test_completion_stale_notice.py` be removed or tolerated? | Tolerate it as the single expected grep hit; out of scope | Add the file to Scope-Paths and delete/reword the assertion (touches an executed plan's shipped test for no behavior gain) | `tests/test_completion_stale_notice.py:501-505`; plan `s2yf26` executed | yes |
