# Review findings: plan cntxsm

- Subject-Id: cntxsm
- Subject-Type: ipd
- Reviewed-At: 2026-10-13
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `fbb2e3799`. The pending plan matched the sealed lane input byte for byte and was committed (`c0a449dae`, with later coverage records), so no snapshot commit was needed. `- Kind: orchestrator`. `aw ipd lint --phase author` and `--phase review-finalize` reported `clean` (no `IPD-S407`). `aw ipd coverage cntxsm` reported ready before revision (cached), and again after (re-probed, 1 call, `Coverage: pass` re-recorded).

Verified at review: `gh run list --workflow tests.yml --status success --limit 1` gives headSha `f69ad318a`, created 2026-09-27, and the ten most recent completed runs are all `failure`, confirming Concern. The four children exist in `pending/` with `- Set: cihealth`, Orders 1 to 4, all `reviewed`; their edges match the child table (`s4z5n8` `executed:n7xlhm, executed:ezyb4a`; `mnwkqu` `executed:fz3i3m`; 01 and 02 `none`). `fz3i3m` is `approved` and its prerequisites `mt54wr`/`atpvao` are executed. `l85xvi` is under `superseded/`. Backlog `5st6e5` is `graduated`, `Blocks-Release: next`, matching this plan. `n7xlhm` defines `ci_checkup_interval_commits`, and `s4z5n8` reads the saved record ("never GitHub") and resolves its exemption as setting `ci_red_exempt_sets = ["cihealth"]`. Every E-item is pure orchestration.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | G (execution contract) | Plan `## Approval and execution gate` (one line: order and retirement) | The gate carried no execution contract: no human-approval statement, no open-question status, no commit/never-push rule, no paste-actual-output rule, and no hand-execution finalize path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added every element. Sequencing now defers to the child table. |
| PR-002 | LOW | IN-SCOPE | A (sequencing consistency) | E-02 `Depends on: E-01`; child table row 02 `Depends on: none`; `n7xlhm` `- Item-Dependencies: none` | The checklist ordered Order 02 after Order 01, which the table and the child's own edges do not require. An agent executing the Set by hand would have serialized 02 behind CI repair for no reason. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now `Depends on: none`. |
| PR-003 | LOW | IN-SCOPE | E (evidence sufficiency) | V-01 "the `gh run list` row showing `success` for a main commit"; `ezyb4a` V-06 demands `git merge-base --is-ancestor` | Under the old wording, any historical green run (for example `f69ad318a`) would have satisfied V-01. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01/V-01 now require the green run's head to contain `ezyb4a`'s commits, with the ancestry check pasted. |
| PR-004 | LOW | IN-SCOPE | Cross-IPD accuracy | Cross-IPD bullet "always-allowed set includes this Set's plans"; `s4z5n8` OQ resolving to `ci_red_exempt_sets` | The bullet did not name the mechanism `s4z5n8` chose, so a reader could expect a hard-coded exemption. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bullet names `ci_red_exempt_sets = ["cihealth"]` set by Order 03. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should Order 02 wait on Order 01? | No; follow the child table and `n7xlhm`'s `Item-Dependencies: none`. | Keep the checklist edge; add `executed:ezyb4a` to `n7xlhm`. | The checkup reads CI's state whether red or green, and its job is to make the red state visible; only Order 03's hard stop must wait for green (plan text "Order 03 must not ship before Order 01"). | yes |
