- Id: twvswo
- Status: open
- Set: attnblind
- Priority: medium
- Work-Kind: bug
- Summary: aw attention drops an unclassified file silently outside .agents/, so a records-tree blind spot reports valid: true

## Workflow history
- 2026-09-18 created (aw backlog): Found while executing plan m867ox (releases scan-root fix): the mechanism that let the releases gap report valid: true is still live for every other .aw/records/ tree.

MEASURED at HEAD cdace6a5 while executing plan m867ox.

attention.scan appends the attention.unclassified-tree drift ONLY when the scanned path starts with .agents/:

    pol = _classify_tree(rel)
    if pol is None:
        if (rel.startswith('.agents/') and not rel.endswith('/README.md') ...):
            drift.append(core.Drift(rel, 'attention.unclassified-tree', 'file under no inventoried tree'))
        continue

So a file under a .aw/records/ tree with no TreePolicy is dropped SILENTLY. That is exactly why the releases defect (a tracked tree matching no scan root, fixed by plan m867ox) produced 'valid: true' with zero violations for the whole time it was broken, instead of a violation naming the tree. Spec 20260808-1945-01 Section 8.6 has a violation mechanism for precisely this class ('a newly discovered tree that is neither is a violation') and it did not fire, because the repository's live layout is .aw/records/ while the check keys .agents/.

WHY IT IS NOT MERELY COSMETIC: the guard plan m867ox added (tests/test_attention_contract.py::TrackedTreeScanCoverageTests) closes the specific hazard for TRACKED trees at test time, but it cannot see a tree that has no TreePolicy at all. A new .aw/records/<type>/ tree added by any future work is still invisible with a green view.

WHY IT WAS NOT FIXED IN m867ox (explicitly deferred there, 'Deferred / out of scope'): making the drift fire outside .agents/ would immediately flag the four root docs (DECISIONS.md, TODO.md, README.md, ARCHITECTURE.md) and the three untracked .aw/records/ trees that are in SCAN_ROOTS by design, so it needs its own decision about what to exempt. That decision is the work.

Note it is RELATED TO BUT DISTINCT FROM ld08f1/diof9n (retire TODO.md): that item removes one of the entries this rule would flag; this item is about the rule itself.
