- Id: 2rnswc
- Status: done
- Graduated-To: gateresolve
- Set: 2rnswc
- Priority: low
- Work-Kind: feature
- Summary: Decide whether a typed Gate-Ref should be resolved against its target rather than only shape-checked, since artifact, decision and todo refs all validate today while pointing at nothing

## Workflow history
- 2026-10-07 done (aw backlog): closed by aw agy run: IPD jdaozp executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-gateresolve-01-jdaozp-resolve-a-typed-gate-ref-against-its-target-so-a-gate-cannot.ipd.md); evidence .aw/records/plans/executed/20261002-gateresolve-01-jdaozp-resolve-a-typed-gate-ref-against-its-target-so-a-gate-cannot.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221821Z-1985969: jdaozp
- 2026-10-01 created (aw backlog): Decide whether a typed Gate-Ref should be resolved against its target rather than only shape-checked, since artifact, decision and todo refs all validate today while pointing at nothing

SCOPE. This is the GENERAL question deliberately left out of the ruling-carrier work (plan graduated from backlog 0szu1p), which fixes only the decision kind's GRAMMAR. Three gate kinds accept a ref that resolves to nothing: artifact is regex-shape-only (measured and recorded in two deferred specs whose Gate-Ref: TODO.md still validates after the awaited content was migrated away), decision accepts any D-number (driven: validate_gate_ref('decision','D99999') returns True while DECISIONS.md stops at D156), and todo accepts any _TODO_ID_RE token. So a gate can be repointed or outlived and nothing detects it.

WHY IT IS NOT URGENT. Exactly ONE item in the live corpus carries a gate at all (driven over backlog.parse_item: artifact/yvvf98/blocked), so the blast radius today is one record. The question is about the contract, not a live outage.

THE TENSION TO RESOLVE. attention_contract is deliberately data-plus-validators with NO file IO (no open/read_text/Path/rglob in the module), and class_of is documented PURE. Resolving a ref needs the filesystem, so resolution cannot live in validate_gate_ref without breaking that property. The shipped precedent for the split is the dangling family (check.from-backlog-dangling, check.from-spec-dangling, check.review-dangling): SHAPE in the contract module, RESOLUTION in a check_engine sweep rule. Whoever takes this should follow that split rather than adding IO to the contract module.

OPEN. Which kinds to resolve (artifact and decision are checkable in-tree; issue and external are not), and at what severity.
