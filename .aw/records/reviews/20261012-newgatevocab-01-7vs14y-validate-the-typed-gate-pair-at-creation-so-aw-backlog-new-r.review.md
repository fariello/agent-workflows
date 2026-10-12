# Review findings: plan 7vs14y

- Subject-Id: 7vs14y
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `005039ed2` in an isolated review lane. The plan was committed and unchanged (`ae75b3bed`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified:
- `backlog.run_new` contains the presence-only check `"aw backlog new: a blocked item requires --gate-kind and --gate-ref"`, followed by `validate_release_exempt_flags`. `attention_contract` is imported as `A`.
- `attention_contract.validate_gate_flags` enforces presence, `GATE_KINDS` membership, `validate_gate_ref`, and the optional summary, returning the exact messages E-01 expects.
- Scratch repo reproduction: `bogus-kind x`, `date notadate`, `artifact docs/x.md`, and `--status open --gate-kind bogus` each exit 0 and write a file. `aw backlog check` reports `backlog.gate-ref-invalid ... 'notadate'` and `backlog.gate-kind-invalid ... 'bogus-kind'` (2 violations). The open item carries no gate line. Files land under `.agents/backlog/` in a repo without `.aw/`.
- `ju3rhs` is `executed`. `go8ztx` is `graduated` with `Blocks-Release: next`, and this plan inherits that. The ju3rhs CHANGELOG line exists in the pending section.
- `tests/test_backlog.py` `test_new_blocked_requires_gate` asserts only rc 2.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | D. Anti-regression (freezing accidental behavior) | E-02 (e); Deferred bullet on non-blocked flags | Case (e) asserted that `--status open` with an invalid gate kind "still succeeds". That freezes a silent discard of user input as desired behavior, so any future refusal would read as a regression. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | (e) now asserts only the at-rest safety property (no gate line on disk), not the rc. The Deferred bullet was updated to match. |
| PR-002 | LOW | IN-SCOPE | E. Test robustness | `check_engine` gateresolve (`jdaozp`) resolves `artifact`/`todo` refs; scratch layout `.agents/backlog/` | Case (d) could pass or fail depending on whether an `artifact` ref resolves in the scratch repo. File discovery could also hard-code a root that the scratch repo does not use. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | (d) uses a `date` pair, and tests locate files from the verb's `wrote` line. |
| PR-003 | LOW | IN-SCOPE | E. Baseline | V-01 (3) "compared against a baseline run at the same HEAD before E-01"; no E-item takes it | V-01 required a pre-change baseline that no E-item captured. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now captures the bare-suite baseline before any edit. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the OQ status, `aw ipd begin`, and the rule that the executor must not finalize under a runner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three were added. Added F-09 with the review re-measurement. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should (e) pin rc 0 for discarded non-blocked gate flags? | No; pin only "no gate line on disk" | Pin rc 0 (freezes accidental behavior); refuse the flags now (scope creep; the plan defers it) | plan-review rubric D "Do not freeze accidental behavior"; `backlog._render_item` writes the gate only for `blocked` | yes |
