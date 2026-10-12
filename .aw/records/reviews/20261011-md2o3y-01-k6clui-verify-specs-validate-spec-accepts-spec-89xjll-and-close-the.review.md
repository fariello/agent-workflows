# Review findings: plan k6clui

- Subject-Id: k6clui
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `66401aeb1` in an isolated review lane; plan committed and unchanged, no snapshot needed.
`aw ipd lint --phase author --agent` clean before semantic review; `--phase review-finalize` clean after.

Re-verified:
- `specs.validate_spec` over 40 `*.spec.md` (recursive): 0 with drift; `89xjll` -> `[]`.
- `aw specs check` -> exit 0, 0 `unsafe-field` lines.
- `89xjll` `- Scope:` line length 367.
- E-02 `-k "LengthClass or Grandfathering or prose"` collects both named guards: `10 passed, 26 deselected`; files unfiltered: `36 passed`.
- `attention_contract.MAX_DESCRIPTIVE_LEN = 300`, `MAX_PROSE_DESCRIPTIVE_LEN = 4300`, `PROSE_DESCRIPTIVE_FIELDS` is a `frozenset`; `specs.validate_spec` uses `is_safe_prose_descriptive` for Scope.
- `b325725d2` is `work(pl1lbb)`; pl1lbb's Scope-Paths include spec `attention-registry-and-cross-tree-status` (Section 8.8 owns the bound).
- Backlog `md2o3y`: `bug`, `Blocks-Release: next`, graduated to this plan. Sibling `6bolin` (`Blocks-Release: next`) carried by `oehkmh` (to-review).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Missing approval command, `aw ipd begin`, scope-as-declaration with `--scope-ack` (every Scope-Path is expected unmodified, so finalize needs acks), MUST-paste wording, staged-set check, conditional finalize ownership, and the release-gate handoff. "Commit only paths changed under Scope-Paths" also omitted the plan file itself, which always changes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten. |
| PR-002 | MEDIUM | UNDER-SCOPE | Spec sync | `attention_contract.MAX_PROSE_DESCRIPTIVE_LEN`; pl1lbb Scope-Paths | An E-03 fix-forward that changed a bound or a field's class would change spec Section 8.8, but the spec was not declared and E-03 did not require amending it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec added to Scope-Paths; E-03 requires the same-commit amendment; spec-sync section explains. |
| PR-003 | LOW | IN-SCOPE | E. Testing / baseline | E-03 bare suite | Fix-forward bare-suite run had no baseline. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03/V-03 compare failing-test names to a pre-edit baseline. |
| PR-004 | LOW | IN-SCOPE | Evidence | F-3 "369"; conventions "tuple" | Measured 367 and `frozenset`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected; F-4 adds the review re-measurement. |
| PR-005 | LOW | IN-SCOPE | Executability | E-01 hard-coded path; unrelated drift | Spec path may move with status; a non-`unsafe-field` drift on another spec had no disposition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 locates by id6, prints counts, and files unrelated drift via `aw backlog new`. |
