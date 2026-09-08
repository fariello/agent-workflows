# IPD: Give specs the lifecycle subdirs every other lifecycle-bearing type already has

- Date: 2026-09-08
- Kind: orchestrator
- Concern: SPECS ARE THE ONLY RECORD TYPE THAT CARRIES A REAL LIFECYCLE AND DOES NOT PARTITION ON IT, so the directory hierarchy, which is how a human sees what needs attention, tells you nothing about a spec. MEASURED at HEAD across every records tree: `plans` 5 subdirs, `backlog` 5, `prompts` 5, `research` 5 (ad hoc groupings), `comms` 1, and `specs` ZERO. The types that are flat are flat for a good reason: `roadmaps` has 0 of 1 files carrying a `- Status:`, `reviews` 1 of 81, `walkthroughs` 2 of 17, and `releases` is a single record. Specs carry `- Status:` on all 28 with a genuine six-state lifecycle (`draft` -> `to-review` -> `reviewed` -> `approved` -> `implementing` -> `implemented`, plus `deferred`/`parked`/`superseded`) owned by `aw specs set`. So the flatness is an inconsistency, not a design.
  THE COST IS CONCRETE AND WAS MEASURED, NOT ARGUED. `ls .aw/records/specs/` prints 28 date-prefixed filenames and reveals NOTHING about state. Finding what needs attention required a scripted loop over all 28 files, which returned TWELVE live specs: 6 `approved`, 2 `draft`, 1 `implementing`, 1 `to-review` (plus 2 `deferred`). A maintainer browsing the tree cannot see those twelve without opening files or running a tool, while the same question about plans or backlog is answered by reading a directory name.
  THE DISTRIBUTION HAS MOVED IN THE DIRECTION THAT ARGUES FOR THIS, which is the opposite of what a stale-item check might assume. Backlog `qzhfk2` measured 24 specs with 16 terminal (8 live). At HEAD there are 28 specs with 16 terminal, so terminal held flat while the LIVE set grew from 8 to 12. The signal-to-noise of the flat tree is getting worse, not better.
  THERE IS A DIRECT MIGRATION PRECEDENT rather than a novel design. `plans` gained its status subdirs through the executed `plans-adopter` Set (`lus9ou` orchestrator, `7qx7ys` "migrate existing plans", `8q6yr9`), and `records-taxonomy-cleanup` (`u7xtni`) did the same class of work for the wider tree. The machinery specs need already exists too: `aw specs set` owns transitions and `aw archive` owns deep-shelving.
  ONE REAL BLOCKER EXISTS AND MUST BE FIXED FIRST, and it is a latent bug independent of this Set. `specs._spec_files` (`specs.py:70`) enumerates with NON-recursive `glob("*.md")` (`:89`), while `check_engine._iter_type_files` uses `rglob`. PROVEN in a throwaway repo: a spec placed in `.aw/records/specs/approved/` made `aw specs check` print "all specs conform" while `specs._spec_files` found ZERO files and `check_engine` found ONE. So the two surfaces already disagree about what a spec is, and moving specs into subdirs before fixing that would silently remove every spec from its own checker. That is why Order 01 exists and why Order 02 depends on it.
  THE ITEM'S OWN COUNTER-ARGUMENT IS REAL AND IS ACCEPTED AS A COST, not dismissed: subdirs promote "location must agree with status" from NOT APPLICABLE to LOAD-BEARING for this tree, which is the invariant that generates the artifact/status discrepancy class for plans. The maintainer's ruling (2026-09-08) is that the browse affordance is worth that cost, because it is what the hierarchy is FOR and because the same trade was already accepted for plans, backlog and prompts.
- Scope: Coordinate a two-child Set that makes specs partition by status like every other lifecycle-bearing type: first make every spec reader recursive so a subdir cannot hide a spec, then migrate the 28 specs and make location agree with status. This orchestrator changes NO product code; it sequences the children and verifies the whole-Set outcome. EXCLUDES the reviews-location question (`sv0sf3`, deliberately not bundled per that item's instruction) and excludes giving subdirs to types with no lifecycle.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: none
- Status: to-review
- Set: specdirs
- Order: 0
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: wfjsp4
- From-Backlog: qzhfk2

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `qzhfk2` ON A MAINTAINER RULING of 2026-09-08 that resolved the item's central open question. THE QUESTION WAS "should specs get lifecycle subdirs?" and the item left it open with a real counter-argument. The maintainer's position, recorded verbatim in substance: humans and to a lesser extent agents USE THE HIERARCHY to see what is pending and to browse what needs to happen, so a lifecycle-bearing type that does not partition on status is failing the surface the hierarchy exists to serve. I initially recommended PARKING this item and was wrong; the recommendation was inherited from the item's framing rather than tested. TESTING IT CHANGED THE ANSWER, and three measurements decided it: (1) specs are the ONLY type with a lifecycle that does not partition, measured across all ten records trees, while every flat type is flat because it has no lifecycle (`reviews` 1 of 81 files carry a Status, `roadmaps` 0 of 1, `walkthroughs` 2 of 17); (2) the live set GREW from the item's 8 to 12 of 28 while terminal held at 16, so the flat tree's noise is worsening; (3) finding those twelve required a scripted loop over every file, which is precisely the affordance the maintainer named. ALSO FOUND, and it reshapes the Set into two children: `specs._spec_files` uses NON-recursive `glob("*.md")` (`specs.py:89`) while `check_engine` uses `rglob`, and I PROVED in a throwaway repo that a spec in a subdir yields "all specs conform" from `aw specs check` while being invisible to `specs._spec_files` (0 files) and visible to `check_engine` (1 file). That is a latent bug today and a data-loss-shaped hazard if the migration went first, so Order 01 fixes readers and Order 02 depends on it.

## Goal

Make the spec tree answer "what needs attention" by being read, the way the plans and backlog trees already do, without letting a subdir hide a spec from its own checker.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: sequence the Set and hold its one hard precondition

- [ ] E-01 EXECUTE THE CHILDREN IN DEPENDENCY ORDER AND CONFIRM ORDER 01 LANDED BEFORE ORDER 02 TOUCHES A FILE. The order is a correctness requirement, not a preference: migrating first would remove every spec from `aw specs check` silently.
  THE CHILD TABLE AND THE DEPENDENCY REASONING live in `## Child IPDs, sequence, and dependencies` below. The single rule to carry here: Order 02 carries `Item-Dependencies: executed:y4bdoz` because a spec moved into a subdir is INVISIBLE to `specs._spec_files` until that reader is recursive, and an invisible spec is one `aw specs check` reports as conforming while never reading it.
  VERIFY THE PRECONDITION BY MEASUREMENT, not by reading a status. Before Order 02 runs, place a spec in a subdir in a THROWAWAY repo and confirm `aw specs check` now SEES it. That is the check that proves Order 01 actually fixed the reader rather than merely editing it.
  - Depends on: none
  - Expected outcome: Order 01 `executed` before Order 02 begins, with the subdir-visibility precondition demonstrated in a throwaway repo rather than assumed.
  - Execution state: pending

### Task group 2: verify the whole Set

- [ ] E-02 VERIFY THE BROWSE AFFORDANCE ACTUALLY ARRIVED, which is the entire point of the Set and the one thing no child can demonstrate alone.
  THE ACCEPTANCE TEST IS A HUMAN ONE, stated mechanically: `ls .aw/records/specs/` must show status directories, and listing any ONE of them must answer "what specs are in this state" without opening a file or running a tool. Paste the before and after listings side by side.
  ASSERT THE TWELVE LIVE SPECS ARE FINDABLE BY DIRECTORY. Measured at authoring: 6 `approved`, 2 `draft`, 1 `implementing`, 1 `to-review`, 2 `deferred`, and 16 terminal (15 `implemented`, 1 `superseded`). Re-measure at execution, since three other agents are authoring specs concurrently, and confirm every live spec sits in a directory matching its `- Status:`.
  DO NOT ACCEPT `aw attention` AS THE PROOF. It already surfaces specs today (verified: it lists `prompt-purity-lint` as approved), and its adequacy is exactly the argument this Set rejects. The deliverable is the HIERARCHY, so the evidence must be a directory listing.
  - Depends on: E-01
  - Expected outcome: before/after directory listings showing status partitioning, every live spec in a directory matching its status, and the count re-measured at execution.
  - Execution state: pending

- [ ] E-03 VERIFY NOTHING THAT READS A SPEC BROKE, across every surface, because this Set moves 28 files that are cited constantly.
  THE SURFACES TO PROVE, each with its own command: `aw specs check` (sees all 28, not zero); `aw check specs` and `aw check all` (per-rule counts unchanged apart from anything the migration legitimately fixes); `aw find specs <id6>` for a spec in each status directory; `aw attention` (still lists live specs); and `aw doctor` (agrees with `aw check`, since the two have disagreed before on the retired-path filter).
  CITATIONS MUST STILL RESOLVE. `25kzda` is referenced across plans, prose and tests, and `.aw/records/specs/20260826-0718-01-...` appears as a LITERAL PATH in at least one plan's `Scope-Paths` (`wenmg4`, this session's `specfresh-01`). Grep the tree for literal spec paths and confirm each still resolves, or is updated by Order 02. A migration that breaks a declared `Scope-Paths` entry would make that plan's finalize scope gate fail for an unrelated reason.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA. Baseline measured on main 2026-09-08: `1 failed, 5648 passed`, the failure being the pre-existing `tests/test_orchestrator_retirement.py` case. Inside a lane worktree roughly 32 further failures are environmental. Criterion: AFTER minus BEFORE is EMPTY.
  - Depends on: E-02
  - Expected outcome: every spec-reading surface proven working, literal spec path citations resolving, `doctor` agreeing with `check`, and an empty bare-suite delta.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | What it delivers | Why it sits here |
|---|---|---|---|
| 01 | `y4bdoz` | Make every spec reader recursive; prove a spec in a subdir is visible to `aw specs check` | MUST be first. `specs._spec_files` uses non-recursive `glob("*.md")`, so a spec in a subdir is invisible to its own checker TODAY. Migrating first would silently remove all 28 specs from validation. |
| 02 | `1bdxcp` | Migrate the 28 specs into status subdirs; make location agree with status; update literal path citations | Depends on Order 01 (`executed:y4bdoz`). Only safe once no reader can miss a subdir. |

THE DEPENDENCY IS A CORRECTNESS EDGE, NOT A PREFERENCE, and it is the reason this is a two-child Set rather than one plan. PROVEN in a throwaway repo at authoring: a spec placed in `.aw/records/specs/approved/` produced `aw specs check: all specs conform` while `specs._spec_files` returned ZERO files and `check_engine._iter_type_files` returned ONE. So before Order 01, the migration would produce a tree whose checker reports success having read nothing, which is the most dangerous possible outcome of a records migration.

ORDER 01 IS ALSO VALUABLE ALONE. Even if Order 02 were never executed, making the readers agree fixes a latent bug: `specs.py` and `check_engine.py` currently disagree about what counts as a spec, and any subdir anyone creates for any reason (an `archive/`, a grouping) already hides specs from `aw specs check`.

## Completion criteria (the whole Set is done only when)

1. Both children are `executed` on disk, with Order 01 demonstrably finalized before Order 02 moved any file.
2. `ls .aw/records/specs/` shows status directories, and listing one answers "what is in this state" with no tool and no file open.
3. Every spec's directory agrees with its `- Status:`, verified mechanically over all specs, not sampled.
4. `aw specs check` sees ALL specs (a count equal to the file count, never zero), and `aw check specs`/`aw check all` per-rule counts are unchanged apart from anything the migration legitimately fixes.
5. Every literal spec path citation in the tree still resolves, including any in a plan's `Scope-Paths`.
6. `aw doctor` and `aw check` agree on the spec set.
7. The bare suite's AFTER failure set minus its BEFORE set is EMPTY.

## Cross-IPD validation

- CID-1 ORDER 01 MUST PRECEDE ANY FILE MOVE. Verify by comparing the two children's finalize commits, not by trusting Order digits. A migration that ran first produced a tree whose checker read nothing, so this is the Set's load-bearing check.
- CID-2 THE READER FIX MUST BE PROVEN BY BEHAVIOR, NOT BY DIFF. Order 01's evidence must include a throwaway repo where a spec in a subdir is SEEN by `aw specs check`. An edit that looks recursive but leaves another reader non-recursive is the failure mode.
- CID-3 NO SPEC MAY BECOME INVISIBLE AT ANY POINT. After the migration, `aw specs check`'s file count must equal the number of `*.spec.md` files on disk. A count of zero reporting "all conform" is the exact hazard CID-1 exists to prevent.
- CID-4 LOCATION MUST AGREE WITH STATUS FOR EVERY SPEC, checked over the whole tree. This invariant is NEW for this type and is the cost the maintainer accepted; shipping it half-enforced would deliver the cost without the benefit.
- CID-5 LITERAL PATH CITATIONS MUST SURVIVE. At least one plan in flight (`wenmg4`) declares a literal spec path in `Scope-Paths`, and `25kzda` is cited across the tree. Order 02 must update or preserve every one, and E-03 verifies it.
- CID-6 `aw specs set` MUST MOVE THE FILE, not merely rewrite the status line, once directories are load-bearing. If Order 02 leaves the setter writing status without relocating, the tree drifts on its very next transition and the invariant is decorative.

## Deferred / out of scope (with reason)

- THE REVIEWS-LOCATION QUESTION (`sv0sf3`). Deliberately NOT bundled: that item explicitly says "DO NOT bundle this with the reviews-location question ... entangling a specs migration with a new artifact tree would make both harder to review." Its own premise is separately falsified (80 of 81 reviews are `Subject-Type: ipd`), so it is being parked rather than graduated.
- SUBDIRS FOR TYPES WITH NO LIFECYCLE. `roadmaps` (0 of 1 files carry a Status), `reviews` (1 of 81), `walkthroughs` (2 of 17) and `releases` (1 record) are correctly flat, and the item already decided NO for releases and roadmaps. Flatness there is a design, not an oversight.
- CHANGING THE SIX-STATE SPEC VOCABULARY. The lifecycle is owned by `aw specs set` and specified elsewhere; this Set partitions on the states that exist and adds none.
- ARCHIVING OR SHELVING TERMINAL SPECS. `aw archive` owns deep-shelving and the plans tree shards by `<disposition>/YYYYMM/`. Whether 16 terminal specs should also shard is a follow-on question once subdirs exist; doing both at once would make the migration unreviewable.
- THE `research` TREE's AD HOC SUBDIRS. Its 5 subdirs are groupings, not statuses, which the item notes makes a `reviews/` dir there unremarkable. Not this Set's business.
- RETROFITTING `location must agree with status` AS A HARD `aw check` RULE FOR SPECS. Order 02 must make the invariant TRUE and checkable, but promoting it to a fail-closed CI error is a severity decision with its own blast radius, and the plans tree's equivalent rule already exists as precedent to follow later.

## Scope check

- Over-scope: none. This orchestrator writes no product code; it sequences two children and verifies the whole-Set outcome.
- Scope-Paths justification: `.aw/records/plans/pending` only, because an orchestrator's deliverable is coordination plus the whole-Set verification record. Every product-code and records path is declared by the child that touches it, which is what makes the runners' pre-run announcement and the finalize scope gate meaningful per child.
- Under-scope, stated rather than left as `none`: this orchestrator does not itself fix a reader, does not move a spec, does not touch the reviews question, does not change the spec status vocabulary, and does not archive terminal specs. Each is a child's job or is excluded above.

## Required tests / validation

- `python3 -m pytest` BARE after the last child, with the summary line pasted. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- BEFORE AND AFTER `ls .aw/records/specs/` listings, pasted side by side, as the primary evidence that the browse affordance arrived.
- `aw specs check` FILE COUNT equal to the on-disk `*.spec.md` count, proving no spec became invisible. A "conform" verdict over zero files is a FAILURE, not a pass.
- A MECHANICAL LOCATION-VERSUS-STATUS CHECK over every spec, not a sample.
- `aw check specs` and `aw check all --agent` PER-RULE counts before and after, with any change explained.
- `aw find specs <id6>` for a spec in EACH status directory.
- `aw attention` still listing live specs, and `aw doctor` agreeing with `aw check` on the spec set.
- EVERY LITERAL SPEC PATH CITATION in the tree shown resolving, including plans' `Scope-Paths` entries.
- A THROWAWAY-REPO DEMONSTRATION that a spec in a subdir is seen by `aw specs check` (CID-2).
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`.aw/records/specs/README.md` documents the spec tree and MUST describe the new layout, including which directory each of the nine statuses maps to and the rule that location agrees with status. Order 02 owns that edit and must declare the README in its own `Scope-Paths`.

THE AGENTS.md MANAGED BLOCK describes `aw specs` and the spec lifecycle to every agent. It is installed from `engine.py`, so it must NOT be hand-edited; if it needs to state the new layout, that is a change to `engine.py`'s installed text plus a re-install, which is a separate decision. Order 02 must RECORD that as a finding rather than editing the block.

No spec amendment is expected. The spec lifecycle's states are unchanged; only their physical arrangement changes. If the executor finds spec text asserting that the specs tree is FLAT, that is a claim this Set falsifies and the spec file must be declared in the relevant child's `Scope-Paths` before editing, per the spec-amendment rule.

Write no em or en dashes in user-facing prose any child authors.

## Open questions

### OQ-01: Should `aw specs set` move the file, or only rewrite the status line?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: IT MUST MOVE THE FILE, because otherwise the invariant is decorative and the tree drifts on its very next transition. The precedent is exact and already shipped: `aw backlog set` "transitions status (moves the file between the disposition dirs)" and the plans lifecycle setters move the file as the authoritative act, which is why `check_engine` reads a plan's disposition from its PATH rather than its status text. A specs setter that wrote `- Status: approved` while leaving the file in `draft/` would create the artifact/status discrepancy class immediately, which is the cost the maintainer accepted only in exchange for the browse benefit. CID-6 pins this and Order 02 owns it.

### OQ-02: Should the 16 terminal specs also shard by month, as archived plans do?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFERRED DELIBERATELY, and it is the right shape of question to leave open because it only becomes answerable once subdirs exist. The plans tree shards archived plans as `<disposition>/YYYYMM/` via `aw archive`, and 16 of 28 specs are terminal, so an `implemented/` directory would hold 15 files today, which is browsable without sharding. Sharding now would add a second structural change to a migration whose whole value is legibility, and would make Order 02's diff harder to review for no present benefit. Revisit when `implemented/` becomes large enough that listing it stops answering a question, which is the same trigger the plans tree used.

### OQ-03: Does making location load-bearing for specs warrant a fail-closed check rule immediately?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN, because the item's counter-argument lands exactly here and the maintainer accepted the cost without specifying the severity. Making location agree with status introduces a new class of possible inconsistency for this type, and the honest question is whether `aw check` should ERROR on a mismatch (as the plans equivalent effectively does) or report it advisorily first. The argument for erroring immediately is that a decorative invariant is worse than none. The argument for advisory-first is the one `check_engine`'s own review-escalation rule records: a fail-closed rule introduced against an unswept corpus "would mass-fail the entire corpus on day one". Since Order 02 makes the tree correct BY CONSTRUCTION, the corpus should be clean at introduction and the mass-fail risk is low, which favors erroring. Left open because it is a severity decision the maintainer should make with Order 02's measured result in hand.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste both children's final `- Status:` and lifecycle directories. Paste evidence Order 01 finalized BEFORE Order 02 moved any file (compare finalize commits or timestamps). Paste the throwaway-repo demonstration that a spec in a subdir is SEEN by `aw specs check` after Order 01, with the file count. If Order 02 ran first, report it as a finding rather than accepting the end state.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `ls .aw/records/specs/` BEFORE and AFTER, side by side. Paste a listing of ONE status directory showing it answers "what is in this state" unaided. Paste the re-measured status distribution at execution time and a mechanical check that every spec's directory equals its `- Status:`. Do NOT offer `aw attention` output as the proof; the deliverable is the hierarchy.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw specs check`'s file count alongside the on-disk `*.spec.md` count, equal and nonzero. Paste `aw check specs` and `aw check all --agent` PER-RULE counts before and after with any change explained. Paste `aw find specs <id6>` for a spec in each status directory. Paste `aw attention` still listing live specs and `aw doctor` agreeing with `aw check`. Paste the grep for literal spec path citations with each shown resolving, naming `25kzda` and `wenmg4`'s `Scope-Paths` entry explicitly. THEN paste the BARE `python3 -m pytest` summary lines before and after with the failure-set delta stated.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS SET EXISTS BECAUSE OF A MAINTAINER RULING, and that provenance matters for how it should be reviewed. Backlog `qzhfk2` left "should specs get lifecycle subdirs?" deliberately open with a real counter-argument, and an earlier recommendation in this session was to PARK it. The maintainer overruled that on the grounds that humans and agents use the hierarchy to see what is pending and to browse what needs to happen. The measurements then supported the ruling rather than the recommendation: specs are the only lifecycle-bearing type that does not partition, every flat type is flat because it lacks a lifecycle, and the live spec set has grown from 8 to 12 while terminal held at 16.

THE ONE HARD PRECONDITION IS NOT NEGOTIABLE. Order 01 must land before Order 02 moves a file, because `specs._spec_files` is non-recursive today and a spec in a subdir is invisible to `aw specs check` while that holds. This was PROVEN, not inferred: a subdir spec yielded "all specs conform" over zero files read. A migration performed first would produce a validated-looking tree that had been validated against nothing.

EXECUTION CONTRACT for every child. Commit only files that child changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Do NOT hand-edit the AGENTS.md managed block; record a finding if it needs the new layout. Do NOT move a spec another agent is concurrently editing without checking `git status` first, since three agents are authoring in this checkout. Re-locate every symbol by NAME rather than by the line numbers cited here. Paste ACTUAL command output; a "conform" verdict over zero files is a FAILURE and must never be reported as a pass. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. This orchestrator retires only when both children are `executed` on disk. Do not claim done or move it to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and V-01..V-03 carry concrete pasted evidence. NOTE the runner rollup deliberately SKIPS an orchestrator's own E/V checkpoint (backlog `5ev6lh`, graduated into the `orchprobe` Set), so E-02's browse-affordance proof and E-03's surface sweep are exactly the class of parent-only work a runner retirement discharges unperformed. If this Set is run by `aw oc run` or `aw agy run`, E-02 and E-03 must be performed BY HAND before the parent is retired.
