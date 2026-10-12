# Review findings: plan p1kbhl

- Subject-Id: p1kbhl
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `924e40840` in an isolated review lane; plan committed and unchanged, no snapshot needed.
`aw ipd lint --phase author --agent` clean before semantic review; `--phase review-finalize` clean after.

Re-verified:
- `docs/cli-output-contract.md` headings: `## 3. Exit Code Semantics`, `### 3.1 Run-Execution Exit Vocabulary`,
  `#### Disagreement on Codes 3 and 4`, `### 3.2 Severity Tier Contract and Gate Semantics` + three `####` children.
- Both quoted sentences ("- `warning`: Evaluates to failing", "Practical consequence: to author a rule ...")
  are inside 3.2.
- `rg "Section 3\.1|section 3\.1" agent_workflows/ tests/`: only the two `check_engine.py` comments
  (`check.plan-date-filename` "WHY `info` AND NOT `warning`" block; `check.ipd-carrier-ungated` block) plus
  `tests/test_plan_review_feasibility_rule.py`, which concerns the plan-review workflow file.
- The plan's filtered tree-wide grep: the remaining `3.1` hits (README, cli-human-guide, cli-agent-protocol,
  cli-migration) are run-exit citations and correct; DECISIONS.md hit is an unrelated version string.
- `u28vqb` and `rwvzqm` are in `executed/`; backlog `2cqs11` is `chore`, graduated, no `Blocks-Release`.
- Four named test files exist; `69 passed in 5.27s` at review HEAD.
- Target lines measure 99 and 101 characters.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Scope-fence wording (plan-review Step 4, 2026-09-01 ruling) | Scope bullet (2) and E-01 "STOP and report (do not edit) ... if any live reference ... exists outside `agent_workflows/check_engine.py`" | A stop directive for the out-of-scope-edit case contradicts the ruling that out-of-scope edits are made and justified with `--scope-reason`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope, E-01, E-02, Scope check now retarget any further stale citation and justify it at finalize; the only remaining stop is Section 3.2 no longer being the severity section (a genuine wrong-destination condition). |
| PR-002 | LOW | IN-SCOPE | E. Testing / executability | E-02 / V-02 "exactly two changed comment lines"; `check_engine.py` lines carrying the citations are 99 and 101 characters | Inserting the title adds ~45 characters, so a width-preserving edit must re-wrap, making "exactly two lines" either unsatisfiable or forcing over-long lines. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 permits re-wrapping within the two comment blocks; Expected outcome and V-02 now demand all changed lines be comments inside the two named blocks, text otherwise identical. |
| PR-003 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Lacked OQ status, scope-as-declaration, the MUST-paste honesty rule, staged-set check, and conditional runner/executor finalize ownership ("finalize through the runner or `aw ipd set`" is wrong: `aw ipd set` does not finalize). It also told the executor to commit the plan file through `aw commit`, which is outside Scope-Paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now carries a bulleted execution contract with all elements. |
| PR-004 | LOW | IN-SCOPE | Open questions | OQ-01 `- Owner: none` | A resolved author decision should name its owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owner set to plan author, confirmed by review. |
| PR-005 | LOW | IN-SCOPE | Traceability | Scope OUT "F-03 here records its stale F-01 framing" | Cross-reference points at the wrong finding; the `u28vqb` F-01 drift is recorded in F-04. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected to F-04. E-03 / V-03 also gained `git diff --check`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Apply backlog `2cqs11`'s recommended action (pick a free number before running runexitvocab)? | No; fix the residue only | Re-anchor doc headings (breaks four correct `#31-run-execution-exit-vocabulary` links) | `docs/cli-output-contract.md` headings; `u28vqb` executed | yes |
| D-2 | Stop on an out-of-scope stale citation, or retarget and justify? | Retarget and justify with `--scope-reason` | Stop and report (contradicts the 2026-09-01 scope-fence ruling) | `.aw/system/workflows/plan-review/plan-review.md` Step 4 SCOPE-FENCE WORDING | yes |
