- Id: wx95o4
- Status: open
- Blocks-Release: next
- Set: id6global
- Priority: medium
- Work-Kind: bug
- Summary: id6 is minted per-tree not globally, D140's identity-slot rule cannot catch a walkthrough that DECLARES a plan's id6, and the cross-type collision rule only runs in the full sweep

## Workflow history
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the defect is live on main, so the item now carries Blocks-Release: next. Status and Priority unchanged; no code touched.

OBSERVED 2026-08-31, and it produced a REAL violation in this session rather than being theoretical.

WHAT HAPPENED. A walkthrough was written for plan `y6mfgo` that both DECLARES `- Id: y6mfgo` and
carries `y6mfgo` in its filename identity slot, i.e. it claims the PLAN's identity as its own. That
is exactly what DECISIONS.md D140 forbids: "the `<id6>` in the `YYYYMMDD-<setid>-NN-<id6>-<slug>`
filename identity slot is the UNIQUE IDENTITY of that ONE file, and must equal that file's own
declared `- Id:`. Identity and reference are distinct roles: an artifact MUST NOT place another
artifact's id6 in its own identity slot."

MEASURED at HEAD `cd09d469`: 560 artifacts carry an id6, 558 are distinct, 2 collide. One is the
known `ntf6sx` duplicate (the same plan in both `pending/` and `executed/`, which is what makes
`aw attention` report VIEW INVALID). The other is this `y6mfgo` walkthrough. A sweep of every
walkthrough found exactly ONE violation, so this is not widespread; it is a repeat of the specific
defect D140 was written to stop.

NOT A ONE-OFF, WHICH IS THE POINT. D140's own Context calls the original `p7dqwz` reuse "a one-off
habit of one agent (Gemini in the Antigravity IDE, which also over-produced walkthroughs), not a
systemic pattern." The maintainer confirms the same agent still does this periodically. So the
recurrence is by the same actor, after the decision was recorded, which means the DECISION EXISTS AND
DOES NOT PREVENT THE BEHAVIOR. A rule that is written but unenforceable at the moment of authoring is
a rule that will keep being broken.

THREE DISTINCT DEFECTS, all measured. They are related but not the same bug, so a fix must address
each explicitly rather than assuming one covers the others.

1. MINTING IS PER-TREE, NOT GLOBAL. `artifact_core.generate_id6(existing)` is collision-checked
   against a caller-supplied set, and every caller supplies only its OWN tree:
   `ipd_authoring._existing_plan_ids()` scans only the plans tree; `backlog.py:356` scans only backlog
   items; `releases.py:62` only releases. So a walkthrough, research doc or backlog item can be minted
   with an id6 that a PLAN already owns, and nothing at mint time notices. The unified inventory
   (`status_set.inventory_all_artifacts`) already spans every type and is what the collision CHECKER
   uses, so the substrate for global minting exists and is simply not consumed here.

2. ONE CALLER PASSES AN EMPTY SET, so it performs no collision check at all:
   `ipd_authoring.py:152` calls `_core.generate_id6(set())`. Any id6 is "unique" against an empty set.
   Whether this path is reachable in a way that can actually collide needs checking before it is
   called a live bug, but an empty-set collision check is wrong on its face and should either be given
   the real inventory or be documented as deliberately unchecked with the reason.

3. D140's IDENTITY-SLOT RULE CANNOT CATCH THIS SHAPE, by construction. Read
   `check_engine.py:781-830`: rule (a) fires when a file DECLARES an Id and its slot differs from it;
   rule (b) fires when a file declares NO Id and its slot id6 is owned by someone else. The `y6mfgo`
   walkthrough satisfies NEITHER: it declares an Id AND its slot equals that declared Id, so (a)
   passes and (b) is skipped. The original `p7dqwz` case declared no Id and was caught by (b); this
   variant is strictly worse (it asserts ownership rather than merely borrowing) and is invisible to
   the rule written for it.

4. THE RULE THAT DOES CATCH IT ONLY RUNS IN THE FULL SWEEP. `check_collisions` DOES find it (verified:
   it emits `check.id6-collision` for the walkthrough naming the plan, plus a `check.setid-collision`),
   and `walkthroughs` IS in its `SUPPORTED` set. But it is invoked only from the aggregate path
   (`check_engine.py:1425`, gated on `collisions`) and from `doctor.py:508`. So `aw check walkthroughs`
   reports 2 findings, NEITHER of which is the collision, while `aw check all` reports it. An author
   who checks the type they just wrote is told they are fine.

WHAT TO SOLVE FOR, not prescribed here.

- Should minting consult the UNIFIED inventory so a cross-type collision is impossible at creation
  rather than detected afterwards? That is the fix that makes the other three moot for new artifacts.
  Note it does not repair existing violations.
- Should the identity-slot rule gain a third case: a file whose declared Id is ALSO another file's
  declared Id, where the other file is of a different type? That overlaps `check.id6-collision`, so
  the answer may be "no, just surface the existing rule better" (see below).
- Should per-type `aw check <type>` run the collision rule for the type being checked? The counter is
  cost (the collision check builds a repo-wide inventory), so perhaps it belongs behind a flag, or
  perhaps the per-type report should simply SAY that collisions are only checked in the full sweep.
- Is a pre-commit hook warranted, given the maintainer's observation that the behavior recurs? A hook
  is local and skippable, so the portable authority is the `aw check` rule plus CI, never the hook
  alone.

RELATED. Backlog `sjsoqq` is the sibling problem (enforce setid uniqueness across types, hard/prevented)
and should probably be solved WITH this rather than separately, since `check_collisions` already emits
both `check.id6-collision` and `check.setid-collision` from one pass and the `y6mfgo` walkthrough trips
BOTH. D140 is the governing decision. The `ntf6sx` duplicate is a different defect (one plan in two
lifecycle directories) that happens to surface through the same rule.

IMMEDIATE, SEPARABLE CLEANUP: the `y6mfgo` walkthrough needs its own id6 and a typed reference to its
source plan (D140 suggests `Target-Id:`/`References:`). That is a small rename plus a frontmatter edit
and does not need to wait for the design questions above.
