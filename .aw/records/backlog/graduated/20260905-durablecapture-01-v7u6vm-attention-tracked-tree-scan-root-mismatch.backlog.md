- Id: v7u6vm
- Status: graduated
- Set: durablecapture
- Priority: medium
- Work-Kind: bug
- Summary: releases is a declared tracked tree with no scan root, so release records are invisible to aw attention; the reviews tree has no policy at all

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan m867ox (durablecapture-02), carrying all three WHAT TO DO points. See the RE-MEASUREMENT section appended. Re-verified by import: releases is declared tracked and matches NO scan root while the other four each match at least one; aw attention returns 848 items (plans 557, backlog 158, research 105, specs 28) and ZERO releases with valid:true (this item measured 749 and the same zero). ONE CORRECTION that narrows the fix to one line plus a guard: releases ALREADY HAS a TreePolicy (tracked, owner aw releases) and _classify_tree already resolves a .aw/records/releases path to it, so the missing piece is only the SCAN_ROOT and an executor must NOT add a policy. Also explained why the view reports valid:true: the unclassified-tree drift fires only for .agents/ paths. The reviews half confirmed and strengthened (82 records, neither policy nor scan root, against five deliberate exclusions each carrying a reason). Corrected one citation: tests/test_attention_registry.py does not exist; the real homes are tests/test_artifact_core.py and tests/test_attention_contract.py. Hazard recorded: sibling ld08f1's plan diof9n also edits SCAN_ROOTS.
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

## RE-MEASUREMENT AND ONE CORRECTION, 2026-09-08 at HEAD a2e0438a during graduation

ALL CLAIMS RE-VERIFIED by importing the modules. Two numbers moved and one claim understates what
already exists, which SHRINKS the fix.

CONFIRMED: the two lists still disagree. Resolving every declared tracked tree against the scan roots:

    specs        -> ['.aw/records/specs']
    plans        -> ['.agents/plans', '.aw/records/plans']
    research     -> ['.aw/records/research']
    backlog      -> ['.agents/backlog', '.aw/records/backlog']
    releases     -> *** NONE ***

CONFIRMED EMPIRICALLY, with updated numbers: `aw attention --format json` returns 848 items (plans 557,
backlog 158, research 105, specs 28) and ZERO releases, with `valid: true` and zero violations, while
`.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md` exists. This item measured 749 items
and the same zero.

THE CORRECTION, AND IT NARROWS THE WORK TO ONE LINE PLUS A GUARD. This item says releases "has a
status->class map ... and is never scanned", which is right, but it does not say that `releases`
ALREADY HAS a `TreePolicy` and that classification already works. Measured:

    TreePolicy(name='releases', root='.agents/releases', tracked=True, owner='aw releases',
               reason='release records (ship-gate anchors); tracked lifecycle planned/blocked/shipped')
    _classify_tree(".aw/records/releases/x.release.md") -> that policy

`_classify_tree` rewrites `.aw/records/<type>` to `.agents/<type>` before matching, so a records-layout
releases path already resolves. The ONLY missing piece is the scan root: `core.iter_scan_files` never
yields the file, so the working classifier and the working map are never reached. An executor must NOT
add a policy, which would be two policies for one tree.

WHY THE VIEW REPORTS `valid: true` DESPITE OMITTING A DECLARED TREE, which this item observes but does
not explain: `attention.scan`'s `pol is None` branch appends `attention.unclassified-tree` drift ONLY
when the path starts with `.agents/`. Anything else is dropped with no violation. That is the same
mechanism sibling item `ld08f1` reports for `TODO.md`, and widening it would immediately implicate the
four root docs and three untracked `.aw/records/` trees that are in SCAN_ROOTS by design, so plan
`m867ox` deliberately defers that as too broad and closes the specific hazard with a cross-list guard
instead.

THE `reviews` HALF CONFIRMED AND STRENGTHENED: the tree now holds 82 records and has NEITHER a
`TreePolicy` nor a scan root, while the five DELIBERATELY excluded trees each carry a real reason
(walkthroughs "narrative records; no lifecycle status in v1 (OQ8)", roadmaps "intent, not commitment",
prompts and comms "deferred to Phase 3 (OQ3)", docs-prompts "the evergreen copy-paste prompt LIBRARY").
So this item's point stands: an absent policy for a consequential tree should be a DECISION with a
reason. Note that tracking it would require a native-status-to-class map that does not exist and would
be a contract change plus a 10 percent view increase, so plan `m867ox` OQ-01 escalates that to the
maintainer and recommends an explicit exclusion whose reason cites that review findings are ALREADY
policed by `check.review-finding-unescalated` at ERROR severity.

CONFIRMED: `aw check releases` is still wired fail-closed in CI (`.github/workflows/tests.yml:157-159`),
so release records are VALIDATED but not SURFACED, which is exactly what makes this easy to miss.

ONE CITATION IN THIS ITEM IS WRONG: it names `tests/test_attention_registry.py` implicitly by
implication of where a consistency check would live; that file DOES NOT EXIST. The modules that
already assert on these lists are `tests/test_artifact_core.py` (which pins three SCAN_ROOTS members)
and `tests/test_attention_contract.py`.

ONE NEW HAZARD: sibling item `ld08f1` was graduated in the same pass, and its plan `diof9n` may REMOVE
the `TODO.md` entry from `SCAN_ROOTS` while this item's plan ADDS a releases entry to the same tuple.
The two must not execute concurrently against it; each plan declares the other in its fence.

Confirmed NOT overlapping: pending plan `rnkqrc` (from `jys5dp`) names both halves of this item in its
deferred section as "both found while investigating, both their own items", so this work is unowned.

GRADUATED to plan `m867ox` (durablecapture-02), carrying all three of this item's WHAT TO DO points.
