# Review findings: plan oehkmh

- Subject-Id: oehkmh
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `bd8b8e993` in an isolated review lane; plan committed and unchanged, no snapshot needed.
`aw ipd lint --phase author --agent` clean before semantic review; `--phase review-finalize` clean after.

Re-verified:
- `-k GrandfatheringAndCheckerTests -v`: 4 PASSED including `test_every_real_spec_in_this_repository_still_conforms`; `4 passed, 26 deselected`.
- `tests/test_descriptive_length_classes.py`: `6 passed`; `test_spec_validation_prose_and_oneline_fields` present.
- `specs.validate_spec` on `89xjll` -> `[]`; `aw specs check` exit 0, 0 `unsafe-field` lines.
- At `cb3ea8546` the spec was in `to-review/`, Scope 343 chars, `attention_contract.MAX_DESCRIPTIVE_LEN = 300` only.
- `8c460a9a1` shortened Scope 343 -> 257; later spec-review commits grew it to 358 (367-char line).
- `b325725d2` is `work(pl1lbb)`; `attention_contract.MAX_PROSE_DESCRIPTIVE_LEN = 4300`; `specs.validate_spec` uses `is_safe_prose_descriptive(scope)`.
- `md2o3y` is `graduated`, carried by `k6clui` (reviewed); `6bolin` `bug`, `Blocks-Release: next`.
- `aw check all` on this plan before edits: `check.ipd-uncarried-obligation` (error), `check.plan-spec-link-missing` (info); after edits neither fires.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Project rule (`check.ipd-uncarried-obligation`) | `## Deferred / out of scope` rows 1-2; `aw check all` ERROR "2 obligation(s) name no durable carrier" | Both deferral rows lacked a carrier, an error-severity finding against this plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Row 1 `- Carrier: k6clui`; row 2 `- Carrier-Declined` (forbidden shortcut). |
| PR-002 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Gate lacked the approval command, `aw ipd begin`, scope-as-declaration with `--scope-ack`, the MUST-paste rule, staged-set check, conditional finalize ownership, release-gate handoff, and omitted the plan file from what is committed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten to match sibling `k6clui`. |
| PR-003 | MEDIUM | UNDER-SCOPE | Spec sync | `attention_contract.MAX_PROSE_DESCRIPTIVE_LEN`; spec `attention-registry-and-cross-tree-status` Section 8.8 | An E-03 fix-forward changing a bound or field class would amend Section 8.8, but the spec was not declared and E-03 did not require it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec added to Scope-Paths; E-03 and spec-sync section require same-commit amendment. |
| PR-004 | LOW | IN-SCOPE | Evidence | F-2; `git show 8c460a9a1` Scope 343 -> 257 | F-2 implied the content fix still mattered; later edits regrew Scope past 300, so only the `pl1lbb` split keeps it passing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-2 records the lengths and the regrowth; F-4 adds review re-measurement. |
| PR-005 | LOW | IN-SCOPE | G. Live-artifact bar | E-01 / V-01 "all 4" / "`4 passed`" | A collected test count is a test-organization artifact, not a valid bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bar is now zero failed plus the named corpus test PASSED (`-v`), with nonzero selection; 4 kept as context. |
| PR-006 | LOW | IN-SCOPE | E. Testing / baseline | E-03 / V-03 bare suite | A fix-forward bare suite run had no baseline to compare against. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 takes a pre-edit FAILED-node baseline; V-03 compares. |
| PR-007 | LOW | IN-SCOPE | Executability | E-02 hard-coded spec path; `check.plan-spec-link-missing` | The spec path moves with status; unrelated drift had no disposition; plan cited `89xjll` without `From-Spec`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 locates by id6, counts `unsafe-field` lines, files unrelated drift via `aw backlog new`; `- From-Spec: none` added (plan graduated from backlog, not a spec). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `From-Spec` for a plan that cites `89xjll` but graduated from backlog | `- From-Spec: none` | `--from-spec 89xjll` (false provenance) | Backlog `6bolin` front matter `Graduated-To: 6bolin`; `check.plan-spec-link-missing` fix text | yes |
| D-2 | Declare the attention spec for a hypothetical fix-forward | Declare, `--scope-ack` in expected case | Leave undeclared | Sibling `k6clui` round 1 PR-002 made the same call; AGENTS.md "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT" | yes |
