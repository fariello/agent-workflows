# Review: Retire the redundant escape_detail calls on drift details

- Subject-Id: 8cu5ml
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Verified at HEAD `cfd95bdb5`; `aw ipd lint --phase author` conforming before and after. Census re-measured:
`rg -c "escape_detail\("` gives releases 2, attention 12, attention_contract 1, cli 1, research_index 3,
specs 8 (F-02 holds); every F-03/F-04/F-05 site located by its quoted string. F-03 reproduced: a backlog
fixture with `- Status: we\ird` through `attention.scan` yields `"backlog status 'we\\\\\\\\ird'"` (Python
repr). Docstring of `attention_contract.escape_detail` still names the TSV record (F-01). Spec Section 8.8
bullet still names the `--agent` TSV form (F-07). All six regression test modules named exist; the new
module does not yet.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Evidence accuracy / E. Testing | `python3 -m agent_workflows.cli attention --check --json --dir <tmp>` output: top-level `diagnostics[0].detail` present | E-02(c) claimed the `aw.agent/v1` diagnostics carry no `detail` key. Under `--json` they do (both `diagnostics[].detail` and `data.drift[].detail`); only the compact `--agent` result omits it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02(c) corrected with the measured payload shape and asserts on both. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing (feasibility) | `attention._prompt_disposition_from_rel`: `norm = rel.replace("\\", "/")` | E-02(a) demanded a backslash-bearing value for the prompts producer; a backslash in the bucket name is converted to a path separator before the drift branch, so that case is unreachable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Prompts case now uses a TAB-bearing bucket (repr renders `\t`, the wrapper doubles it) with a recorded fallback. |
| PR-003 | LOW | IN-SCOPE | G. Live-artifact bar | E-01 / V-01 "26 call sites" | A live census count was the bar with no instruction for drift. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01/V-01 now require classifying any added/removed site into F-03/F-04/F-05 before proceeding. |
| PR-004 | LOW | IN-SCOPE | G. Executability | OQ-01/OQ-02 `Owner: none`; gate "The runner sets backlog `4ep6mp` to `graduated`" | Resolved questions had no owner; the gate misdescribed the backlog item, which is already `graduated` with no Blocks-Release. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owners set to `plan author`; gate states the From-Backlog handoff closes the item. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to exercise the prompts repr-wrapped site? | TAB in an unrecognized bucket name, fallback to plain bucket | Backslash (unreachable); drop the case | `attention._prompt_disposition_from_rel` backslash normalization | yes |
| D-2 | Which `--json` field is the end-to-end oracle? | Both `data.drift[].detail` and `diagnostics[].detail` | `data.drift` only | Measured payload at review | yes |
