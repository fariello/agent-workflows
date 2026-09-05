- Id: v7u6vm
- Status: open
- Set: durablecapture
- Priority: medium
- Work-Kind: bug
- Summary: releases is a declared tracked tree with no scan root, so release records are invisible to aw attention; the reviews tree has no policy at all

## Workflow history
- 2026-09-05 created (aw backlog): releases is a declared tracked tree with no scan root, so release records are invisible to aw attention; the reviews tree has no policy at all

THE DEFECT. `attention_contract.TRACKED_TREES` declares five trees:

    ('specs', 'plans', 'research', 'backlog', 'releases')

But `artifact_core.SCAN_ROOTS` contains no releases path. Measured 2026-09-05:

    SCAN_ROOTS = ('DECISIONS.md', 'TODO.md', 'README.md', 'ARCHITECTURE.md',
                  '.agents/plans', '.agents/docs', '.agents/backlog',
                  '.aw/records/plans', '.aw/records/specs', '.aw/records/research',
                  '.aw/records/walkthroughs', '.aw/records/roadmaps',
                  '.aw/records/prompt-library', '.aw/records/backlog')

No `.aw/records/releases` and no `.agents/releases`. So `releases` is declared tracked, has a
status->class map (`attention_contract.py:261-265`: planned->ready, blocked->blocked,
shipped->done), and is never scanned.

CONFIRMED EMPIRICALLY. `aw attention --format json` returns 749 items broken down as
plans 484, backlog 133, research 105, specs 27 - and ZERO releases, despite
`.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md` existing. The view reports
`valid: true` while silently omitting an entire declared tree.

WHY THIS MATTERS MORE THAN A MISSING COUNT. Releases are the anchor for the whole
`Blocks-Release` gating mechanism. AGENTS.md instructs agents to consume `aw attention` for the
cross-tree view and states it "computes the view ON DEMAND" and that "aw attention surfaces the
outstanding release-blocker set for the active release". If the release records themselves are
invisible to that view, the release side of that contract is not being read from where the
documentation says it is read. Any conclusion an agent draws about release readiness from
`aw attention` alone is drawn without the release records.

Note `aw check releases` IS wired and fail-closed in CI (`.github/workflows/tests.yml:157-159`), so
release records are validated - just not surfaced in the attention view. That split is exactly what
makes this easy to miss.

SECOND, RELATED GAP - THE `reviews` TREE HAS NO POLICY AT ALL. `.aw/records/reviews/` has neither a
`TreePolicy` entry (`attention_contract.py:83-154`) nor a scan root. Unlike `walkthroughs`,
`roadmaps`, `prompts`, `comms`, and `docs-prompts` - each DELIBERATELY excluded with a recorded
reason (`:112-146`) - reviews are simply absent from the contract. Given that
`check.review-finding-unescalated` (`check_engine.py:154-156`) treats an unescalated review finding
as an ERROR, a review record carrying gating findings is consequential enough that its
exclusion should be a DECISION with a recorded reason, not an omission.

WHAT TO DO.
  1. Add the releases scan root(s) to `SCAN_ROOTS` so the declared tracked tree is actually scanned,
     and verify a release record appears in `aw attention` output afterward.
  2. Decide `reviews` deliberately: either give it a `TreePolicy` (tracked or explicitly excluded
     WITH a reason, matching how the other five exclusions are recorded), or document why it is out
     of scope.
  3. ADD A CONSISTENCY CHECK so this class of bug cannot recur silently: assert that every tree in
     `TRACKED_TREES` has at least one corresponding entry in `SCAN_ROOTS`. Two lists encoding one
     fact will drift again otherwise. This is the same "one shared authority" discipline
     `check_engine.py:147-152` states for CI and local checks ("no forked/inlined policy"), and the
     same reasoning behind `_DEFAULT_RULESPEC` (`check_engine.py:274`) ensuring "a new rule is never
     SILENTLY unclassified". A declared-but-unscanned tree is the tree-level version of that hazard.

DISCOVERED WHILE investigating enforcement mechanisms for `jys5dp`. Independent of it: that item is
about capturing known defects durably, this is about the attention view honestly covering what it
claims to cover.
