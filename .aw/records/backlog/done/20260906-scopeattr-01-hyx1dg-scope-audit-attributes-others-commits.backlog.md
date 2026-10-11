- Id: hyx1dg
- Status: done
- Close-Evidence: .aw/records/plans/executed/20260906-scopeattr-01-h9cn0y-attribute-a-scope-audit-to-the-execution-s-own-commits-inste.ipd.md
- Blocks-Release: next
- Set: scopeattr
- Priority: high
- Work-Kind: bug
- Summary: finalize's scope audit attributes every concurrent agent's commits to the finalizing plan, because it diffs against the begin receipt's base_head instead of the execution's own commits

## Workflow history
- 2026-10-11 done (aw set): status set to done
- 2026-09-18 graduated (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-07 graduated (aw set): Graduated to plan h9cn0y (scopeattr-01): attribute the scope audit's committed half by authorship instead of by time window. FOUND WHILE AUTHORING: this exact defect was already fixed once for the WORKING-TREE half by scopeattrib Order 01 (lbgzxg), whose test suite tests/test_finalize_scope_ownership.py states the defect in nearly identical words; this plan finishes the committed half that was left.
- 2026-09-06 created (aw backlog): finalize's scope audit attributes every concurrent agent's commits to the finalizing plan, because it diffs against the begin receipt's base_head instead of the execution's own commits

/tmp/opencode/f3.md
