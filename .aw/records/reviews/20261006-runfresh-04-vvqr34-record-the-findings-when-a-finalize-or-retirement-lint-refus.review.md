# Review findings: plan vvqr34

- Subject-Id: vvqr34
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T030816Z-4078927` at HEAD `5f6180714`. The plan was
committed and byte-identical to the sealed lane input (rev-5); no snapshot needed. `- Kind: child`, so `IPD-S407`
and `IPD-S408` do not apply. `aw ipd lint --phase author` clean before review; `review-finalize` clean after.

Reproduced at review: a git-backed fixture orchestrator (one executed child, a pass coverage record, an extra
`- Bogus-Field: x` front-matter field) dispatched through `runner_shared.dispatch_orchestrator_item` with the real
`ipd_lifecycle.retire_orchestrator` ended `terminate`/`finalize-refused` with
`findings=('IPD-M103 Bogus-Field: unknown field',)`, while the detail, the `Refusal` reason, the
`orchestrator-deferred` event and `aw runs`' Refusals block read only "post-transition validation failed".
`aw runs` printed the reason untruncated.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | C architecture / F UX | `ipd_lifecycle.run_finalize` `_emit`: `for d in diags or []: print(f"  {d.rule} {d.detail}")`; `runner_shared.driver_finalize` re-appends each diagnostic | E-01 appended findings to `FinalizeResult.message`, but the CLI already renders `result.findings` as `IPD-FINALIZE` diagnostics, so every finding would print twice on the child finalize path and in its recorded refusal. The only real gap is the in-process retirement caller. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now changes only `runner_shared.dispatch_orchestrator_item`; `ipd_lifecycle` dropped from Scope-Paths; E-03(d) guards exactly-once. |
| PR-002 | MEDIUM | IN-SCOPE | F UX | `render_stream.render_run_summary_table`: `diag_lines.append(f"  • {id6}: {st} ({refusal.reason})")`; `refusal_of_item` legacy arm "FLATTENED TO ONE LINE" | One-finding-per-line text inside a single-line diagnostics entry breaks the block's alignment, the defect the legacy arm already avoids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Helper renders one line `findings (N): a; b; ...`. |
| PR-003 | MEDIUM | IN-SCOPE | E testing | `dispatch_orchestrator_item` calls `orchestrator_readiness.review_readiness(..., ask=True)` before retiring | The E-03 fixture was unspecified about the coverage re-check, which would try to ask a model. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 writes a pass coverage record with `commit=False` (measured working at review). |
| PR-004 | MEDIUM | IN-SCOPE | D anti-regression | `tests/test_orchestrator_retirement.py` `class _No: exit_code = 3; message = ...` patched over `retire_orchestrator` | Reading `result.findings` directly would raise on the existing test double. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 uses `getattr(result, "findings", ())`. |
| PR-005 | LOW | IN-SCOPE | G executability | Required tests named `tests/test_ipd_lifecycle.py` (absent); gate lacked scope-fence, honesty-MUST and lifecycle wording | Stale test path and incomplete execution contract. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Real test files named; gate completed; V-items rewritten to demand concrete evidence. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where do findings get added? | Only the retirement refusal detail in `runner_shared` | append to every `FinalizeResult.message` (double-print) | `run_finalize` `_emit`; `driver_finalize` | yes |
| D-2 | One line or one per finding? | One line, `; `-joined | one per line (breaks summary block) | `render_run_summary_table` diag line; `refusal_of_item` flattening comment | yes |
