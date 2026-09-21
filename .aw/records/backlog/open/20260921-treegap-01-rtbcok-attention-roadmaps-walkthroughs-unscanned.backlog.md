- Id: rtbcok
- Status: open
- Set: treegap
- Priority: low
- Work-Kind: chore
- Summary: aw attention still cannot see the roadmaps and walkthroughs trees, so a selector naming one is answered only by the vocabulary exemption

## Workflow history
- 2026-09-21 created (aw backlog): aw attention still cannot see the roadmaps and walkthroughs trees, so a selector naming one is answered only by the vocabulary exemption

MEASURED 2026-09-21 at HEAD ef640388 while executing plan fqnj8k (attsel). This is the RESIDUAL of a gap whose other half is already closed, which is why it is filed fresh rather than pointed at the old carrier.

WHAT IS ALREADY FIXED. Plan m867ox (durablecapture-02, now in .aw/records/plans/executed/) closed the RELEASES half: `attention_contract.TRACKED_TREES` is ('specs','plans','research','backlog','releases') and a live scan now yields items from all five, including 1 releases item. Plan fqnj8k's deferred section originally named m867ox as the carrier for the whole gap; that is no longer a live carrier, and the remaining half needs one of its own.

WHAT REMAINS. `.aw/records/roadmaps/` and `.aw/records/walkthroughs/` are populated (walkthroughs has many files) and NEITHER is in TRACKED_TREES, so neither appears in `aw attention` under any selector or `--all`. `aw att <a-walkthrough-id6>` therefore finds nothing.

WHY IT IS A CHORE AND NOT A BUG. The impact is now MASKED rather than misleading, and the masking is deliberate. fqnj8k made a zero-match selector refuse at exit 2, and it had to decide what `aw att roadmaps` should do; the answer is that `roadmaps` and `walkthroughs` are in `attention.selector_vocabulary()` (derived from `TYPE_ALIASES`, which accepts both), so such a token is treated as a standing question and answers cleanly at exit 0 instead of being called a typo. So no operator is told a real artifact does not exist. What they get is an empty answer to a question the tool cannot yet answer, which is a completeness gap rather than a wrong answer.

A DESIGN NOTE, not a prescription. The two trees are not obviously the same case. A WALKTHROUGH is a narrative record with no status and no lifecycle, so it has no native status to map onto an attention class and arguably does not belong in a "what should I work on" view at all; the honest fix may be to decide it stays out and record that decision, rather than to invent a status for it. A ROADMAP is more plausibly real work with a state. Whoever takes this should settle that question FIRST, because "add both trees" and "add roadmaps and document why walkthroughs stay out" are different deliverables.

WHERE THE WORK LANDS. `attention_contract.py` (TRACKED_TREES plus a CLASS_MAPS fragment per added tree) and `attention.py`'s `_TREE_TO_SCAN_ROOTS`/`_classify_tree`. Note that adding a tree also widens the vocabulary automatically, since `selector_vocabulary()` derives from the contract symbols; no edit is needed there.

NOT FIXED IN fqnj8k, whose scope explicitly excludes changing which artifacts are shown, and which proved by `git diff --stat` that it left `attention_contract.py` untouched.
