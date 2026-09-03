- Id: h2ceme
- Status: open
- Blocks-Release: next
- Set: findflagdupe
- Priority: medium
- Work-Kind: bug
- Summary: aw find renders a duplicate id6 as an ordinary multi-result list with exit 0, bypassing the resolver's own UNIQUE_KINDS collision policy; it must flag the violation and name the remedy

## Workflow history
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the defect is live on main, so the item now carries Blocks-Release: next. Status and Priority unchanged; no code touched.

OBSERVED 2026-08-31, maintainer-requested. `aw find` presents a duplicate id6 as an ordinary
multi-result answer, so the surface an operator uses to LOOK UP an artifact is also the surface most
likely to be the first to encounter a corrupt identity, and it says nothing.

MEASURED at HEAD `cd09d469`, both real cases in the tree today:

    $ aw find y6mfgo
    executed      y6mfgo  locksafe   executed/20260830-locksafe-01-y6mfgo-...ipd.md
    -             y6mfgo             .aw/records/walkthroughs/20260831-locksafe-01-y6mfgo-...walkthrough.md
    -             -                  .aw/records/reviews/20260831-locksafe-01-y6mfgo-...review.md

    $ aw find ntf6sx
    executed      ntf6sx  terseout   executed/20260829-terseout-01-ntf6sx-...ipd.md
    pending       ntf6sx  terseout   pending/20260829-terseout-01-ntf6sx-...ipd.md

    $ aw find ntf6sx >/dev/null; echo $?
    0

Two DISTINCT violations rendered as an unremarkable list, with exit 0. `y6mfgo` is a walkthrough that
claims a plan's identity (a D140 breach); `ntf6sx` is one plan present in two lifecycle directories
(the defect that makes `aw attention` report VIEW INVALID). Neither is flagged, neither is explained,
and nothing tells the operator what to do. A reader would reasonably conclude the id6 legitimately
spans several files.

WHY THIS IS WORTH FIXING RATHER THAN DOCUMENTING. The judgement already exists elsewhere in the
package and `aw find` simply does not consult it. `selectors.resolve` treats exactly this case as
fatal, in its own words: an id6 matching multiple files is "a `id6` collision matching multiple files
(a data bug to fix, not overridable by --force)" (`selectors.py:476-480`), because `MATCH_ID6` is in
`UNIQUE_KINDS` (`:46`) alongside path and stem, while `MATCH_SETID` is explicitly allowed to be
multi-target (`:474`). So the repo has already decided that a duplicate id6 is corruption, not a
legitimate one-to-many; `aw find` is the one place that renders it as normal.

ROOT CAUSE, measured: `plans_index.run_find` (`:401-410`) does its own `scan_plans(plans_dir)` +
`query(...)` and never calls `resolve()`, so the `UNIQUE_KINDS` collision policy is bypassed. This is
the same class of gap as the cross-type collision rule only running in the full sweep (see
`id6global` `wx95o4`): the rule exists, the surface does not consult it.

RECOMMENDED COURSE OF ACTION (maintainer asked for one; this is a recommendation, not a decision).

1. FLAG, DO NOT REFUSE. `aw find` is a read-only lookup and is often exactly what someone runs WHILE
   diagnosing a mess, so it must still SHOW every match. Refusing to answer would make the tool
   useless at the moment it is most needed. Print the results AND a distinct warning line naming the
   violation, e.g.
   `! id6 y6mfgo is held by 2 artifacts (plans, walkthroughs); an id6 identifies exactly ONE file (D140)`.
2. NAME THE RULE AND THE FIX IN THE OUTPUT, not just the symptom. The two shapes have DIFFERENT
   remedies and conflating them would send the reader down the wrong path:
   - same id6 across DIFFERENT types (the `y6mfgo` shape) -> the non-owning artifact needs its own
     id6 plus a typed reference to its source (`aw rename <type> <path> --to-id6`, then a
     `Target-Id:`/`References:` field), per D140;
   - same id6, same type, two lifecycle directories (the `ntf6sx` shape) -> ONE of the two copies is
     stale and must be removed or retired; this is not an identity problem but a lifecycle one.
   Emitting one generic message for both is worse than useless.
3. REUSE THE EXISTING DETECTOR; DO NOT WRITE A SECOND ONE. `check_engine.check_collisions` already
   emits `check.id6-collision` for both cases above (verified), already spans every type via
   `SUPPORTED`, and is already consumed by `aw check` and `aw doctor`. `aw find` should consult that
   predicate (or `selectors.resolve`'s existing verdict) rather than growing its own duplicate-scan,
   or the two surfaces will drift and disagree about what counts as a collision. This repo has paid
   for that kind of fork before.
4. DECIDE THE EXIT CODE DELIBERATELY. A warning that leaves exit 0 is invisible to scripts; a nonzero
   exit changes the contract of a read verb and could break a caller that pipes `aw find`. RECOMMEND:
   keep exit 0 for the human path, and surface the violation as a structured finding in `--agent`/
   `--json` output so machine consumers can act on it. If a hard signal is wanted, put it behind an
   explicit `--check` flag, mirroring `aw attention --check`, rather than changing the default.
5. SCOPE HONESTLY: `aw find` currently resolves through the plans index, so a cross-TYPE duplicate is
   only visible if the lookup already spans types. Confirm that before implementing, because a
   plans-only `find` cannot see a walkthrough at all and the fix would then be vacuous for the
   `y6mfgo` shape.

DEPENDENCY / SEQUENCING NOTE. Pending plan `e32j35` (findidx) is re-authoring `aw find` as two-tier
filesystem-first and its review added the requirement that `find` returns matching ARTIFACTS, not
references, plus that non-conforming filenames must be RAISED. This item is adjacent and should
probably be folded into that re-authoring rather than landing as a competing change to the same
surface; measured, `e32j35` currently says nothing about duplicates or collisions
(grep for duplicate/collision/ambiguous returns ZERO), so it is a genuine gap in that plan, not an
overlap.

RELATED. `id6global` (`wx95o4`) covers the minting and enforcement half (per-tree minting, the
empty-set collision check, D140's blind spot for a DECLARED duplicate, and the collision rule only
running in the full sweep). This item is specifically about the `aw find` SURFACE. `sjsoqq` covers
setid uniqueness. D140 is the governing decision.
