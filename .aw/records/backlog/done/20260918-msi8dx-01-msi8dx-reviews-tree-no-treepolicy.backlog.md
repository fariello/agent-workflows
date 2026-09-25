- Id: msi8dx
- Status: done
- Set: msi8dx
- Priority: low
- Work-Kind: chore
- Summary: The reviews tree has no TreePolicy entry, so its records are outside the attention contract's typed policy surface

## Workflow history
- 2026-09-25 done (aw set): RETIRED (already fixed): attention_contract.py TREE_POLICY carries a 'reviews' TreePolicy (added 339d9578, durablecapture-02 m867ox, executed), and 'aw check reviews' is a valid type (outcome conforms, exit 0). Review records still get no content validation; that is a separate concern.
- 2026-09-18 created (aw backlog): The reviews tree has no TreePolicy entry, so its records are outside the attention contract's typed policy surface

Found while investigating durablecapture 01 (`rnkqrc`) and named in its deferred section; filed here so it has a durable carrier rather than living only in that plan's prose.

THE GAP: every other tracked records tree keys a `TreePolicy` entry, and the `reviews` tree does not, so review records sit outside that typed policy surface. Note the adjacent asymmetry `rnkqrc`'s neighbours already document: `aw check reviews` is not a valid check type today either, which is why `check.review-decision-unescalated` fires while checking PLANS even though the artifact it reads is a REVIEW.

The `releases`-tree half of the same deferred row is separately carried by plan `m867ox` (durablecapture 02), which is approved and pending; this item covers only the `reviews` half.
