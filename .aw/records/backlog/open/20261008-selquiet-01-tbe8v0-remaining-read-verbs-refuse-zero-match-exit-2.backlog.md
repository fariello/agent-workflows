- Id: tbe8v0
- Status: open
- Blocks-Release: next
- Set: selquiet
- Priority: medium
- Work-Kind: bug
- Summary: Make remaining selector-taking read verbs refuse zero-match with exit 2

## Workflow history
- 2026-10-08 created (aw backlog): Make remaining selector-taking read verbs refuse zero-match with exit 2

Survey in IPD zyj8io (E-08) measured 13 selector-taking read verbs. Four do not conform to spec 25kzda Section 2.3 exit 2 on zero-match selectors: reviews decisions (exits 0), record-history (exits 0), graduation (exits 0), ipd recheck-readiness (exits 1).
