# IPD: Add the Graduated-To forward link and its dangling check mirroring From-Backlog

- Date: 2026-09-08
- Kind: child
- Concern: GRADUATION IS RECORDED IN ONE DIRECTION ONLY, SO THE SHARED SETID IS DOING THE OTHER DIRECTION'S JOB. A graduated plan carries `- From-Backlog: <id6>` pointing at its source, and `check.from-backlog-dangling` validates it (`releases.py:580-619`). Nothing points the other way. MEASURED: `Graduated-To` occurs ZERO times anywhere in `agent_workflows/`. So the only way a reader (or a tool) can get from a backlog item to the plan Set it became is the shared setid, which is exactly the collision the parent Set is removing. Take the setid away without adding the forward link and the relationship becomes unreadable in that direction.
  THE MIRROR TO BUILD ALREADY EXISTS AND MUST BE FOLLOWED, NOT REINVENTED. `check_from_backlog` (`releases.py:580`) is the precise shape: it `rglob`s three trees (`plans`, `specs`, `backlog`) under both the `.aw/records/` and legacy `.agents/` roots, skips `README.md`/`INDEX.md`/`STATUS.md` and ignored paths, resolves the value against `backlog.existing_backlog_ids(repo_root)`, and rides the once-per-full-sweep seam in `check_types` where `check_blocks_release` and `check_from_spec_dangling` already sit. Its own docstring records that it "tolerates it anywhere for symmetry" even though "the graduation link's primary home is the plan". The new check is that function with the resolution target changed from an id6 set to a plan-Set setid set.
  THE FIELD IS MULTI-VALUED AND THAT IS THE ONE STRUCTURAL DIFFERENCE FROM ITS TWIN, so it cannot be a copy. Spec `4w7d6s` G3 requires `Graduated-To: <setid>[, <setid>...]` as a LIST because "a source may graduate more than once over its life (a spec may spawn several plan Sets; a re-graduation adds an entry)". Every existing link field in this repository is single-valued: `_ITEM_FROM_BACKLOG_RE` and its siblings match `(\S+)`, a single non-whitespace token. So the parser, the writer and the check must each handle a comma-separated list, and a regex copied from the twin would silently capture only the first entry and validate only that one.
  THE ASYMMETRY IS DELIBERATE AND MUST NOT BE "FIXED". Spec G4: the back-link is by id6 because each child points at exactly ONE source item; the forward link is by SETID because a source points at the whole generated Set (orchestrator plus children). A reviewer or a later agent will be tempted to make both id6 for consistency; the spec calls that asymmetry "intentional and correct, not an inconsistency", and pointing the forward link at a single child's id6 would lose the Set.
  THERE IS ALREADY A CONSUMER WAITING FOR IT. `check_engine.evaluate_blocking_close` lets a release-gated backlog item close `done` only via HANDOFF (a plan carrying `From-Backlog`), SATISFIED (a cited artifact) or DE-GATED. Spec G7 records that a resolvable `Graduated-To` is itself satisfaction evidence and would strengthen that guard. This plan does NOT wire that consumer, deliberately (see Deferred), but the field must be shaped so it can be.
- Scope: Add the `Graduated-To` forward link to backlog items and specs as a multi-valued setid list, with a reader, a writer on the graduation path, and `check.graduated-to-dangling` built as the direct mirror of `check_from_backlog`. EXCLUDES the fresh-setid mint and creation-time prevention (Order 03), the collision sweep (Order 01), and wiring the close-legitimacy predicate to consume the new link (deferred with a reason).
- Scope-Paths: agent_workflows/releases.py, agent_workflows/check_engine.py, agent_workflows/backlog.py, agent_workflows/specs.py, .aw/records/backlog/README.md, tests/test_graduated_to_link.py, tests/test_releases.py
- Item-Dependencies: none
- Status: to-review
- Set: setidhard
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: bwgyum
- From-Backlog: sjsoqq

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `sjsoqq` deliverable #4 (plus G3/G5 of spec `4w7d6s`). Verified at HEAD rather than trusted: `Graduated-To` occurs ZERO times in the package, so this is genuinely unbuilt; `check_from_backlog` (`releases.py:580-619`) is the exact mirror to follow and its structure was read, not assumed. TWO THINGS THE ITEM DID NOT SAY that shape the work. FIRST, the field is MULTI-VALUED (spec G3) while every existing link field in the repository is single-valued (`_ITEM_FROM_BACKLOG_RE` matches one `(\\S+)` token), so a regex copied from the twin would capture only the first entry and silently validate one of several. SECOND, a consumer already exists and is named by spec G7: `check_engine.evaluate_blocking_close` could treat a resolvable `Graduated-To` as satisfaction evidence for closing a release-gated item; this plan deliberately does NOT wire it, but shapes the field so it can be. This child carries NO `Item-Dependencies` and can execute first in the Set, which is correct: Order 03 depends on IT, because Order 03 may only stop minting a shared setid once the typed link that replaces it exists.

## Goal

Give graduation a machine-readable forward link so a source can say what it became, making the shared setid unnecessary rather than merely forbidden.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the field and its reader

- [ ] E-01 DEFINE AND PARSE `Graduated-To` AS A MULTI-VALUED SETID LIST, and do not copy a single-value regex. Spec G3 requires `- Graduated-To: <setid>[, <setid>...]`.
  DO NOT REUSE THE SINGLE-TOKEN PATTERN. `_ITEM_FROM_BACKLOG_RE` and every sibling link regex match one `(\S+)`, which is correct for an id6 and WRONG here: a comma-separated list would parse as the single token `first,second` or capture only `first`, and the check would then validate one entry while reporting the field as clean. Write a list parser that splits on commas, strips whitespace, drops empties, and preserves order.
  DECIDE AND RECORD THE DUPLICATE AND EMPTY CASES rather than letting them fall out: a repeated setid in one field, and a `- Graduated-To:` line with no value. Both are author errors an agent will produce, and silently tolerating either makes the field untrustworthy. Prefer treating an empty field as absent and a duplicate as a finding, and say so in the docstring.
  VALIDATE THE TOKEN SHAPE against the naming authority rather than accepting any string, since a setid has a defined form and a typo that happens to look like prose would otherwise resolve to nothing and be reported as dangling with a confusing message.
  - Depends on: none
  - Expected outcome: a list-aware reader that returns setids in order, with the duplicate and empty cases decided and documented; no single-token regex reused.
  - Execution state: pending

- [ ] E-02 BUILD `check.graduated-to-dangling` AS THE DIRECT MIRROR OF `check_from_backlog`, in the same module, with the same traversal, registered at the same seam.
  FOLLOW THE EXISTING FUNCTION EXACTLY where it is right: `rglob` over `plans`, `specs`, `backlog` under both `.aw/records/` and `.agents/`; skip `README.md`/`INDEX.md`/`STATUS.md` and ignored paths; tolerate the field anywhere for symmetry even though its primary home is the SOURCE (the mirror image of the twin's note that the back-link's primary home is the plan).
  THE RESOLUTION TARGET IS DIFFERENT AND IS THE ONLY REAL DESIGN CHOICE: the twin resolves an id6 against `backlog.existing_backlog_ids`; this must resolve a SETID against the set of setids that name a real PLAN Set. Derive that set from the plans tree (the plans index or a scan), and state in the docstring what counts as "a real plan Set", because a setid naming a Set whose only member was retired is a genuine edge case a reader will hit.
  REGISTER IT AT THE ONCE-PER-FULL-SWEEP SEAM in `check_types`, beside `check_blocks_release`, `check_from_backlog` and `check_from_spec_dangling`, inside its OWN `try/except` rather than sharing one. The existing code already does this deliberately, with the comment that a separate guard is used "so a failure in either scan cannot suppress the other".
  REGISTER THE RULE IN THE SEVERITY TABLE. `check_engine`'s `RuleSpec` table assigns severity, assurance class and determinism; an unregistered rule code is not a contract. Match the twin: `check.from-backlog-dangling` is an `error`.
  - Depends on: E-01
  - Expected outcome: a mirror check in the same module and seam, resolving setids against real plan Sets, with its own try/except and a registered severity matching its twin.
  - Execution state: pending

### Task group 2: the writer

- [ ] E-03 WRITE THE LINK ON THE GRADUATION PATH, ATOMICALLY WITH THE CHILD'S BACK-LINK, per spec G6 ("mints the fresh setid (G1), writes the child back-links (G2), and updates the source's `Graduated-To` (G3) as one path-scoped change").
  THE HONEST DIFFICULTY, AND IT MUST BE FACED RATHER THAN ASSUMED AWAY: there is no single "graduation operation" in this repository today. Graduation is performed by an AGENT authoring plans and then running `aw backlog set graduated <item>`. So "the graduation path" in practice means the SETTER, which is the one tooled step every graduation passes through. Establish that by inspection before implementing, and if a dedicated graduation verb has appeared since, prefer it and say so.
  THE SETTER IS THEREFORE THE PRAGMATIC SITE: `aw backlog set graduated <item> --graduated-to <setid>[,<setid>]`. That keeps the write tooled and path-scoped, and it composes with the existing history append, so the forward link and the status transition land together.
  DO NOT MAKE IT MANDATORY IN THIS PLAN. A required flag would break every concurrent graduation the moment it lands, and four other agents are graduating items right now. Make it OPTIONAL here; Order 03 (which owns the fresh-setid mint) is the correct place to consider requiring it, because that is when the shared setid stops carrying the relationship.
  ALSO ACCEPT THE SPEC SOURCE. G3 applies to specs as well as items, so `aw specs set` needs the same optional setter. If that is a materially larger change, implement the backlog half and RECORD the spec half as a finding rather than half-implementing it silently.
  - Depends on: E-02
  - Expected outcome: an optional tooled setter writing the forward link on the backlog graduation path (and the spec path, or a recorded finding explaining why not), landing in the same path-scoped change as the status transition; nothing made mandatory.
  - Execution state: pending

### Task group 3: prove it both ways

- [ ] E-04 TEST THE LIST SEMANTICS AND THE DANGLING CHECK FROM FIXTURES, including the cases a copied single-value implementation would fail.
  SIX ASSERTIONS MINIMUM: a single-entry field resolves; a MULTI-entry field resolves EVERY entry (the case that catches a single-token regex); one bad entry among three good ones is reported and names WHICH entry; an absent field is silent; an EMPTY field is treated as decided in E-01; a duplicate entry is treated as decided in E-01.
  ASSERT THE MULTI-ENTRY CASE EXPLICITLY AND SEPARATELY. This is the one assertion that distinguishes a correct implementation from a plausible-looking copy of the twin, so it must not be folded into a general "resolves" test.
  BUILD FIXTURES, NOT LIVE-TREE ASSERTIONS. The tree is being modified by four concurrent agents and by Order 01's sweep, so a test pinned to a real item's setid would fail for reasons unrelated to this code. Measure the live tree only as evidence.
  - Depends on: E-03
  - Expected outcome: all six cases asserted from fixtures with the multi-entry case standing alone; no test depends on live records.
  - Execution state: pending

- [ ] E-05 PROVE THE NEW RULE ADDS NO FINDINGS TO THE CURRENT TREE, AND THAT ITS TWIN IS UNAFFECTED. This is what makes the rule safe to land while other work is in flight.
  THE EXPECTED RESULT IS ZERO NEW FINDINGS, because no artifact carries the field yet (measured: zero occurrences package-wide). If the sweep reports anything, that is either an authored field this plan does not know about or a bug in the traversal, and either way it must be explained rather than accepted.
  ASSERT `check.from-backlog-dangling` IS UNCHANGED. Both scans now run in the same seam over the same trees, and the twin currently reports exactly ONE finding at HEAD (measured); a change in that count means the new code perturbed the existing scan.
  COMPARE PER RULE, NEVER BY TOTAL. `aw check all` reports 98 findings at HEAD across rules this plan does not touch.
  RUN THE SUITE BARE and judge on the DELTA. Baseline on main 2026-09-08: `1 failed, 5648 passed`, the failure being the pre-existing `tests/test_orchestrator_retirement.py` case. Criterion: AFTER minus BEFORE is EMPTY.
  - Depends on: E-04
  - Expected outcome: zero new findings on the current tree with any exception explained; `check.from-backlog-dangling`'s count unchanged; per-rule comparison stated; bare-suite delta empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE MIRROR EXISTS: `check_from_backlog` (`releases.py:580-619`) is the traversal, the skip list, the dual-root handling and the resolution shape to copy, and its docstring records the "tolerates it anywhere for symmetry" rule.
- THE SEAM EXISTS: `check_types` runs the cross-tree scans ONCE in the `collisions` branch, each in its OWN `try/except` deliberately "so a failure in either scan cannot suppress the other".
- EVERY EXISTING LINK FIELD IS SINGLE-VALUED (`(\S+)`), so the multi-valued requirement is a genuine structural difference and not a formatting detail.
- THE ASYMMETRY IS SPECIFIED AS CORRECT (spec G4): back-link by id6 (one source), forward link by setid (a whole Set). Do not "harmonize" them.
- A CONSUMER IS ALREADY NAMED (spec G7): `evaluate_blocking_close`'s HANDOFF/SATISFIED/DE-GATED ladder could treat a resolvable forward link as satisfaction evidence. Not wired here; shape the field so it can be.
- THERE IS NO SINGLE GRADUATION OPERATION TODAY: graduation is an agent authoring plans plus `aw backlog set graduated`. The setter is the only tooled chokepoint.
- `Graduated-To` IS UNBUILT: zero occurrences in `agent_workflows/`.
- `check.from-backlog-dangling` REPORTS EXACTLY ONE FINDING AT HEAD, which is the baseline E-05 must hold constant.
- `aw check all` IS NOT GREEN (98 findings). Compare per RULE.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the field is genuinely unbuilt | `Graduated-To` occurs ZERO times in `agent_workflows/`. Nothing to reuse, nothing to migrate. | grep over the package |
| F-2 | HIGH | the mirror is exact and must be followed | `check_from_backlog` rglobs `plans`/`specs`/`backlog` under both roots, skips the index files, resolves against `existing_backlog_ids`, and rides the once-per-sweep seam. The new check differs ONLY in its resolution target. | `releases.py:580-619` |
| F-3 | HIGH | multi-valued is a real structural difference | Spec G3 requires a comma list; every existing link regex matches a single `(\S+)`. A copied regex would capture one entry and validate one of several while reporting clean. | spec G3; `_ITEM_FROM_BACKLOG_RE` |
| F-4 | HIGH | the removal of the shared setid needs this first | Order 03 stops minting a shared setid. Without the forward link, the source-to-plan direction becomes unreadable, which is why Order 03 depends on THIS child rather than the reverse. | spec G1/G3; Order 03's dependency edge |
| F-5 | MEDIUM | the asymmetry is specified, not accidental | Spec G4 calls the id6/setid asymmetry "intentional and correct, not an inconsistency". A reviewer will want to harmonize it. | spec G4 |
| F-6 | MEDIUM | a consumer is already named | Spec G7: a resolvable forward link is satisfaction evidence for `evaluate_blocking_close`'s ladder. Not wired here. | spec G7; `check_engine.evaluate_blocking_close` |
| F-7 | MEDIUM | there is no graduation verb to hook | Graduation is an agent authoring plans plus `aw backlog set graduated`. The setter is the only tooled chokepoint, so G6's "one path-scoped change" means the setter. | inspected the backlog setter and the promotion README |
| F-8 | MEDIUM | making the flag mandatory would break concurrent work | Four agents are graduating items right now; a required flag would fail every one of them the moment it lands. | the concurrent-graduation protocol |
| F-9 | LOW | the twin's baseline must hold | `check.from-backlog-dangling` reports exactly ONE finding at HEAD; both scans will share a seam and traversal. | `aw check all --agent` per-rule counts |
| F-10 | LOW | rule codes are contracts | Severity, assurance class and determinism come from `check_engine`'s `RuleSpec` table; an unregistered code carries no contract. The twin is an `error`. | `check_engine.py:95-110` region |

## Proposed changes (ordered, validatable)

1. Parse `Graduated-To` as an ordered, multi-valued setid list with the empty and duplicate cases decided (E-01).
2. Build `check.graduated-to-dangling` as the direct mirror, resolving setids against real plan Sets, registered in the severity table and at the once-per-sweep seam (E-02).
3. Write the link optionally on the graduation setter, in the same path-scoped change as the status transition (E-03).
4. Assert six list and dangling cases from fixtures, with the multi-entry case standing alone (E-04).
5. Prove zero new findings on the current tree and an unchanged twin count (E-05).

## Deferred / out of scope (with reason)

- WIRING `evaluate_blocking_close` TO ACCEPT A RESOLVABLE `Graduated-To` AS SATISFACTION EVIDENCE (spec G7). Deliberately deferred: that predicate is the fail-closed gate on closing a release-blocking item, it is shared by the setter, three `aw check` rules and an opt-in pre-commit hook, and loosening its ladder is a separate decision with its own blast radius. This plan shapes the field so that wiring is possible; it does not weaken a release gate as a side effect of adding a link.
- THE FRESH-SETID MINT AND CREATION-TIME PREVENTION. Order 03 (`dw7i3m`). This child provides the link that makes the shared setid unnecessary; Order 03 is what stops minting it.
- THE COLLISION SWEEP. Order 01 (`drzbs9`), which CONSUMES this child's link when it records what each regrouped source became.
- MAKING THE FORWARD LINK MANDATORY. Excluded on measured risk (F-8): four agents are graduating concurrently. Order 03 is the right place to consider requiring it.
- BACKFILLING `Graduated-To` ONTO THE 21 EXISTING GRADUATED ITEMS. That is Order 01's sweep, which regroups those sources anyway and can write the link in the same pass. Doing it here would touch the same files twice.
- GENERALIZING TO SPEC-TO-SPEC OR BACKLOG-TO-SPEC GRADUATION. The spec's own OQ-01 defers it: the field targets plan Sets by default and generalizes only if a real case appears.
- CHANGING `check_from_backlog` ITSELF. It is correct and its baseline must hold; E-05 asserts it did not move.

## Scope check

- Over-scope: none. One reader, one check, one optional setter flag, documentation, and tests.
- Scope-Paths justification: `agent_workflows/releases.py` holds `check_from_backlog`, the mirror this check must live beside (E-02); `agent_workflows/check_engine.py` holds the `RuleSpec` severity table and the once-per-full-sweep seam where the scan registers (E-02); `agent_workflows/backlog.py` holds the item reader and the `set` transition where the optional writer belongs (E-01, E-03); `agent_workflows/specs.py` is the spec-side twin of that setter, since G3 applies to specs too (E-03, and if it proves materially larger this path may finish unchanged with a recorded finding); `.aw/records/backlog/README.md` documents the promotion convention, which becomes incomplete the moment a forward link exists (E-03); `tests/test_graduated_to_link.py` is new and carries the six fixture cases (E-04); `tests/test_releases.py` is the twin check's existing suite and must show `check_from_backlog` unperturbed (E-05).
- Under-scope, stated rather than left as `none`: this child does not wire the close-legitimacy predicate, does not mint fresh setids, does not prevent creation-time collisions, does not sweep or backfill existing items, does not make the link mandatory, does not generalize beyond plan-Set targets, and does not modify `check_from_backlog`. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- SIX FIXTURE CASES (E-04), with the MULTI-ENTRY case asserted separately and its assertion quoted, since it is the one that catches a copied single-token regex.
- `aw check all --agent` PER-RULE counts before and after. `check.graduated-to-dangling` must be ZERO on the current tree (no artifact carries the field yet), and `check.from-backlog-dangling` must stay at its baseline of exactly ONE.
- A DANGLING DEMONSTRATION: a fixture source carrying a `Graduated-To` naming a nonexistent Set produces the finding, and the message names WHICH entry when three others resolve.
- THE SETTER ROUND TRIP: `aw backlog set graduated <fixture> --graduated-to <setid>` writes the field and the history line in ONE path-scoped change, and the resulting field parses back as a list.
- NEGATIVE PROOF that the new flag is OPTIONAL: a graduation performed WITHOUT it still succeeds and produces no finding.
- NEGATIVE PROOF that `evaluate_blocking_close`'s ladder is unchanged (show the searches), since G7 is deliberately not wired.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`.aw/records/backlog/README.md` is IN SCOPE and must change: its "Promotion to a plan" section currently says to "author an IPD under `.aw/records/plans/pending/`, then `aw backlog set <item> --status done`", which is already doubly stale (the honest terminal state for a handoff is `graduated`, not `done`) and says nothing about a forward link. Add the forward link to that description without rewriting the `graduated` versus `done` distinction, which is another item's territory. This is user-facing prose: write no em or en dashes.

The `- Field:` grammar documented in that README's "Item format" block must gain `Graduated-To`, marked optional and multi-valued, or an author has no way to know the field exists.

`check_from_backlog`'s docstring should gain a cross-reference to its new mirror, so the next reader finds both scans from either one; that is a comment-only change to a function this plan otherwise must not touch.

Spec `4w7d6s` is the authority for G3/G4/G5 and is `- Status: draft`. This plan IMPLEMENTS it and does not amend it, so the spec file is deliberately NOT in `Scope-Paths`. Order 00's E-02 holds the approval gate; if the maintainer's answer to the spec's OQ-01 widens the field's targets beyond plan Sets, this plan's resolution target changes and it must be re-authored rather than stretched.

## Open questions

### OQ-01: What resolves as "a real plan Set" for the dangling check?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ANY SETID CARRIED BY AT LEAST ONE PLAN FILE IN ANY LIFECYCLE DIRECTORY, INCLUDING TERMINAL ONES. The alternative (only live Sets resolve) is wrong for the same reason the id6 twin's retired-path filter was wrong: a graduated source's Set will eventually be entirely `executed`, and a forward link that starts resolving and later dangles because the work FINISHED would fire on exactly the successful case. This mirrors how `From-Backlog` resolves against all backlog ids regardless of the item's status. The edge case worth documenting rather than solving: a Set whose only member was retired to `not-executed/` still resolves, which is correct, because the source really did graduate into it and the record should say so.

### OQ-02: Should the forward-link flag be required on graduation?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NOT IN THIS PLAN, and the reason is operational rather than architectural. Four agents are graduating items into this checkout concurrently; a required flag would make every one of their `aw backlog set graduated` calls fail the moment this lands, which is a self-inflicted outage for a field nothing yet consumes. Optional-then-required is also the pattern this repository already used for `trailers` on `offer_commit` (added with an empty default so no caller changed) and for `Work-Kind`'s dual-read window. Order 03 owns the point at which the shared setid stops carrying the relationship, and that is the correct place to reconsider requiring it.

### OQ-03: Where does the writer belong, given there is no graduation verb?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THE `aw backlog set graduated` SETTER, because it is the only tooled step every graduation passes through, and spec G6 requires the forward link to land in ONE path-scoped change with the rest of the transition. Graduation in this repository is an AGENT authoring plans followed by that setter; there is no single operation to hook, and inventing a `aw graduate` verb would be a much larger surface than this item asks for. E-03 requires the executor to re-establish this by inspection first, because if a dedicated verb has appeared since authoring, it is the better site and should be preferred.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the reader implementation and QUOTE the list-splitting logic, showing it is not a single-`(\S+)` match. Paste its ACTUAL output for a three-entry field, proving all three parse in order. State the decided behavior for an EMPTY field and for a DUPLICATE entry, and paste the docstring text recording both decisions.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new check beside `check_from_backlog` and confirm by inspection that the traversal, skip list and dual-root handling match. Paste the `RuleSpec` table entry showing the registered severity equals the twin's (`error`). Paste the registration at the once-per-sweep seam showing it has its OWN `try/except`. Paste the docstring sentence defining what resolves as a real plan Set (OQ-01).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the setter round trip: the ACTUAL command, the resulting front matter, and the history line, demonstrating both landed in ONE path-scoped commit. Paste NEGATIVE proof the flag is OPTIONAL by performing a graduation without it and showing it succeeds with no finding. State whether the SPEC-side setter was implemented or recorded as a finding, and if the latter, paste the finding.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the ACTUAL passing output of all six fixture cases. QUOTE the multi-entry assertion separately and confirm in one sentence that it would fail against a single-token regex. Confirm no test reads live records, by pasting the fixture construction.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `aw check all --agent` PER-RULE counts before and after, showing `check.graduated-to-dangling` at ZERO on the current tree and `check.from-backlog-dangling` unchanged at exactly ONE. If the new rule reported anything, explain it rather than accepting it. Paste NEGATIVE proof that `evaluate_blocking_close`'s ladder was not modified (show the searches). THEN paste the BARE `python3 -m pytest` summary lines before and after and state the failure-set delta explicitly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS CHILD CARRIES NO `Item-Dependencies` AND MAY EXECUTE FIRST IN THE SET, which is deliberate: Order 03 depends on IT, because Order 03 may only stop minting a shared setid once the typed link that replaces it exists, and Order 01's sweep consumes the link when recording what each regrouped source became.

IT STILL INHERITS ORDER 00's TWO BLOCKING QUESTIONS. OQ-01 there is the spec-approval gate (`4w7d6s` is `draft` with three open questions), and OQ-02 there asks whether hard cross-type uniqueness is the right answer at all. If the maintainer narrows I1 instead of hardening it, this child is still probably wanted (a typed forward link is useful independently of the uniqueness rule) but its urgency changes, and that is a judgement for the human rather than a reason to proceed.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Re-locate every symbol by NAME rather than by the line numbers cited here. Do NOT modify `check_from_backlog`'s behavior or `evaluate_blocking_close`'s ladder. Do NOT make the new flag mandatory. Build tests from FIXTURES, never from live records, since Order 01's sweep and four concurrent agents are changing the records trees. Paste ACTUAL command output and compare `aw check` findings PER RULE, never by total. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the standalone multi-entry assertion and the unchanged twin count.
