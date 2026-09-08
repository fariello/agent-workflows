# IPD: Migrate the 28 specs into status subdirs and make location agree with status

- Date: 2026-09-08
- Kind: child
- Concern: THE SPEC TREE CANNOT ANSWER "WHAT NEEDS ATTENTION" BY BEING READ, WHICH IS WHAT THE HIERARCHY IS FOR. MEASURED at HEAD: `ls .aw/records/specs/` prints 28 date-prefixed filenames and reveals NOTHING about state, and finding the live ones required a scripted loop over every file. That loop returned TWELVE specs needing attention (6 `approved`, 2 `draft`, 1 `implementing`, 1 `to-review`, plus 2 `deferred`) against 16 terminal (15 `implemented`, 1 `superseded`). Every other lifecycle-bearing type answers the same question from a directory name: `plans` 5 subdirs, `backlog` 5, `prompts` 5.
  SPECS ARE THE ONLY OUTLIER, AND THE FLAT TYPES ARE FLAT FOR A REASON. Measured across all ten records trees: `roadmaps` has 0 of 1 files carrying a `- Status:`, `reviews` 1 of 81, `walkthroughs` 2 of 17, and `releases` is a single record. So flatness elsewhere reflects an absent lifecycle, while specs carry `- Status:` on all 28 with a genuine nine-value vocabulary owned by `aw specs set`. The inconsistency is specs', not the other trees'.
  THE SETTER DOES NOT MOVE FILES TODAY, AND THAT IS THE HALF THAT MAKES THE INVARIANT REAL RATHER THAN DECORATIVE. `specs.run_set` (`specs.py:498`) reads the path, rewrites metadata and appends history; it never relocates. Its sibling does: `backlog.py:534` records "Rewrite metadata bullets in place; move file to the new status dir; append history", with a dry-run line at `:600` printing `would move <src> -> <dest>`. Without the same behavior here, the very next `aw specs set` after this migration would leave a spec in the wrong directory, and the tree would drift immediately.
  THE MIGRATION IS ONLY SAFE AFTER ORDER 01, and this is a correctness edge rather than a preference. PROVEN in a throwaway repo: a spec placed in `.aw/records/specs/approved/` made `aw specs check` print `all specs conform` while `specs._spec_files` returned ZERO files. So performed first, this migration would produce a tree whose own validator reports success having read nothing. Hence `Item-Dependencies: executed:y4bdoz`.
  LITERAL PATHS TO SPECS EXIST IN THE TREE AND WILL BREAK, which is the migration's main hazard and is measurable. `25kzda` is cited constantly, and at least one plan in flight declares a spec's literal path in its `- Scope-Paths:` (`wenmg4`, this session's `specfresh-01`, declares `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`). A plan whose declared scope path no longer exists would fail its finalize scope gate for a reason unrelated to its own work, so the migration must update or preserve every literal citation it moves.
- Scope: Move the 28 specs into status subdirectories, teach `aw specs set` to relocate a spec on transition the way `aw backlog set` already does, and update every literal spec path citation the move invalidates. EXCLUDES making the readers recursive (Order 01 owns it and this depends on it), and excludes promoting location-versus-status to a fail-closed check rule (the parent's OQ-03).
- Scope-Paths: agent_workflows/specs.py, .aw/records/specs, .aw/records/plans/pending, tests/test_specs_status_dirs.py
- Item-Dependencies: executed:y4bdoz
- Status: to-review
- Set: specdirs
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 1bdxcp
- From-Backlog: qzhfk2

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `qzhfk2` as Order 02, ON A MAINTAINER RULING of 2026-09-08 that humans and agents use the HIERARCHY to see what is pending, so a lifecycle-bearing type that does not partition on status fails the surface the hierarchy exists to serve. An earlier recommendation in this session was to PARK the item; that was inherited from the item's framing rather than tested, and testing changed the answer. THREE MEASUREMENTS DECIDED IT: specs are the only lifecycle-bearing type not partitioned (every flat type lacks a lifecycle: `reviews` 1 of 81 files carry a Status, `roadmaps` 0 of 1, `walkthroughs` 2 of 17); the LIVE set grew from the item's 8 to 12 while terminal held at 16, so the flat tree's noise is worsening; and finding those twelve required a scripted loop over all 28 files. TWO THINGS THE ITEM DID NOT KNOW, both shaping this child: `aw specs set` does NOT move files (`specs.py:498`) while `aw backlog set` does (`backlog.py:534`), so without the setter change the invariant would be decorative and drift on the next transition; and a plan in flight (`wenmg4`) declares a literal spec path in its `Scope-Paths`, so the move can break another plan's finalize gate. The item's own counter-argument (subdirs promote "location must agree with status" from not-applicable to load-bearing) is ACCEPTED as a cost, not dismissed.

## Goal

Make the spec tree answer "what needs attention" by being listed, and make the setter keep that answer true on every future transition.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: verify the precondition and inventory what moves

- [ ] E-01 CONFIRM ORDER 01 LANDED, BY BEHAVIOR, BEFORE MOVING ANY FILE. This is the Set's load-bearing check and a status read is not sufficient evidence.
  THE TEST: in a THROWAWAY repo, place a spec in a subdirectory and confirm `aw specs check` EXAMINES it, asserting the examined COUNT rather than the verdict text. A "conform" verdict over zero files is precisely the failure this guards against, and it is indistinguishable from success by exit code alone.
  IF ORDER 01 HAS NOT LANDED, STOP. Do not proceed to any file move and do not implement Order 01's fix here: report the unmet precondition. Migrating first would produce a tree validated against nothing.
  - Depends on: none
  - Expected outcome: a behavioral demonstration that a subdir spec is examined by `aw specs check`, or an explicit STOP with the precondition unmet.
  - Execution state: pending

- [ ] E-02 INVENTORY EVERY SPEC AND EVERY LITERAL CITATION BEFORE MOVING ANYTHING, because the move is mechanical but its blast radius is not.
  BUILD THE STATUS MAP: every `*.spec.md` with its `- Status:`. Authoring baseline, to be re-measured: 28 files, 15 `implemented`, 6 `approved`, 2 `deferred`, 2 `draft`, 1 `superseded`, 1 `implementing`, 1 `to-review`. Three other agents are authoring concurrently, so the count and distribution WILL differ.
  MAP THE STATUS VOCABULARY TO DIRECTORY NAMES EXPLICITLY, and decide the edge cases rather than discovering them: `deferred` and `parked` are legitimate spec statuses that have no plans-tree equivalent, so their directories are a decision this item must record. Follow the plans/backlog convention of one directory per status unless a status is genuinely transient.
  FIND EVERY LITERAL SPEC PATH IN THE TREE. Grep for `.aw/records/specs/` and for `.agents/docs/specs`, across plans, specs, backlog, prose, tests and code. Name each hit and classify it: a `- Scope-Paths:` declaration (which breaks a finalize gate), a prose citation, a test fixture, or a code constant. `wenmg4`'s declaration of `.aw/records/specs/20260826-0718-01-...` is a known instance.
  DO NOT MOVE A SPEC ANOTHER AGENT IS EDITING. Check `git status` first; three agents are authoring in this checkout and a concurrent edit to a file you are relocating is the shared-checkout hazard the contract forbids you to resolve by overwriting.
  - Depends on: E-01
  - Expected outcome: a re-measured status map, an explicit status-to-directory mapping including `deferred`/`parked`, a classified inventory of every literal spec citation, and confirmation no target file is concurrently modified.
  - Execution state: pending

### Task group 2: make the setter maintain the invariant

- [ ] E-03 TEACH `aw specs set` TO RELOCATE THE FILE, following `aw backlog set` exactly rather than inventing a mechanism. Do this BEFORE the bulk move, so the migration can use the same code path it will maintain.
  THE MODEL IS IN THE REPOSITORY: `backlog.py:534` documents "Rewrite metadata bullets in place; move file to the new status dir; append history", and `:600` prints a dry-run `would move <src> -> {dest}` line. Mirror both, including the dry-run affordance, because a migration of 28 files should be previewable.
  USE `git mv`, NOT A PLAIN MOVE, so history follows the file. The plans lifecycle setters move files as the authoritative act and `check_engine` reads a plan's disposition from its PATH for that reason; a move that loses history would make the spec's own record harder to follow.
  THE MOVE MUST BE THE AUTHORITATIVE ACT, not a side effect. If the status write succeeds and the move fails, the tree is inconsistent in exactly the way this Set is meant to prevent, so the two must be one transaction or the failure must leave the file untouched. State which you implemented.
  DO NOT CHANGE THE STATUS VOCABULARY OR THE TRANSITION RULES. `aw specs set` owns which transitions are legal and enforces the human-attestation rule for `approved`; this item changes WHERE the file lands, not WHETHER a transition is allowed.
  - Depends on: E-02
  - Expected outcome: `aw specs set` relocates via `git mv` with a dry-run preview, the move is transactional with the metadata write, and no transition rule or status vocabulary changed.
  - Execution state: pending

### Task group 3: migrate, then prove the affordance and the citations

- [ ] E-04 MOVE THE SPECS USING THE SETTER'S OWN PATH, and preserve every id6 and filename. This is a RELOCATION, not a rename.
  DO NOT RENAME ANY SPEC. The grandfathered pre-cutover names (`25kzda`, `4w7d6s`, `5tapom` and the other legacy-named specs) stay exactly as they are: renaming them is a separate maintainer call per record, is what `f8m2z2`'s Order 02 reports on advisorily, and would break far more citations than the move itself.
  PREVIEW FIRST, THEN APPLY. Use the dry-run from E-03 over all specs and paste the preview before executing it. A 28-file move with no preview is not reviewable.
  UPDATE EVERY LITERAL CITATION E-02 FOUND, in the same change. The `- Scope-Paths:` case is the urgent one: a plan declaring a path that no longer exists would fail its finalize scope gate for an unrelated reason. `wenmg4` is a known instance and is in flight this session.
  CREATE A README OR EXTEND THE EXISTING ONE so the new layout is documented where a browser lands. `.aw/records/specs/README.md` exists and describes the tree; it must state which directory each status maps to and that location agrees with status.
  - Depends on: E-03
  - Expected outcome: all specs relocated with filenames and id6s unchanged, a pasted dry-run preview, every literal citation updated, and the README describing the layout.
  - Execution state: pending

- [ ] E-05 PROVE THE BROWSE AFFORDANCE ARRIVED, which is the whole purpose and is a claim about a human surface.
  THE PRIMARY EVIDENCE IS A DIRECTORY LISTING, before and after, side by side. `ls .aw/records/specs/` must show status directories, and listing ONE of them must answer "what specs are in this state" with no tool and no file opened.
  ASSERT LOCATION EQUALS STATUS MECHANICALLY over EVERY spec, not a sample. That is the invariant this Set accepted a cost to gain, and a half-enforced invariant delivers the cost without the benefit.
  DO NOT SUBSTITUTE `aw attention` OUTPUT AS PROOF. It already surfaces live specs today, and its sufficiency is exactly the argument the maintainer rejected; the deliverable is the hierarchy.
  - Depends on: E-04
  - Expected outcome: before/after listings, a mechanical location-equals-status check over all specs, and no substitution of tool output for the hierarchy claim.
  - Execution state: pending

- [ ] E-06 PROVE NOTHING THAT READS A SPEC BROKE, across every surface, because 28 moved files are cited widely.
  THE SURFACES, each with its own command: `aw specs check` examining a count EQUAL to the on-disk `*.spec.md` count and never zero; `aw check specs` and `aw check all --agent` per-rule counts, with any change explained; `aw find specs <id6>` for a spec in EACH status directory; `aw attention` still listing live specs; and `aw doctor` agreeing with `aw check` on the spec set, since those two have measurably disagreed before over the retired-path filter.
  RE-RUN THE SETTER END TO END after the migration: transition a throwaway spec and confirm it MOVES to the matching directory. That proves the invariant is maintained going forward rather than only established once.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA. Baseline measured on main 2026-09-08: `1 failed, 5648 passed`, the failure being the pre-existing `tests/test_orchestrator_retirement.py` case. Inside a lane worktree roughly 32 further failures are environmental. Criterion: AFTER minus BEFORE is EMPTY. Watch for tests carrying literal spec paths as fixtures; if one breaks, it is a citation E-02 missed.
  - Depends on: E-05
  - Expected outcome: every spec-reading surface proven working, the setter demonstrated maintaining the invariant, and an empty bare-suite delta with any literal-path fixture failure traced to a missed citation.
  - Execution state: pending

## Project conventions discovered (Step 0)

- SPECS ARE THE ONLY LIFECYCLE-BEARING TYPE NOT PARTITIONED: `plans`/`backlog`/`prompts` have 5 subdirs each, `specs` has 0, and every flat type lacks a lifecycle (`reviews` 1 of 81 carry a Status, `roadmaps` 0 of 1, `walkthroughs` 2 of 17, `releases` a single record).
- THE FLAT TREE HIDES TWELVE LIVE SPECS: 6 `approved`, 2 `draft`, 1 `implementing`, 1 `to-review`, 2 `deferred`, against 16 terminal. Finding them required a loop over all 28 files.
- `aw specs set` DOES NOT MOVE FILES (`specs.py:498`); `aw backlog set` DOES (`backlog.py:534`, dry-run at `:600`). That asymmetry is why the invariant would be decorative without E-03.
- THE PLANS PRECEDENT IS THAT THE MOVE IS AUTHORITATIVE: `check_engine` reads a plan's disposition from its PATH because the setters move the file as the authoritative act, and status text may lag.
- A MIGRATION PRECEDENT EXISTS: `plans` gained subdirs via the executed `plans-adopter` Set (`lus9ou`, `7qx7ys`, `8q6yr9`), and `records-taxonomy-cleanup` (`u7xtni`) did the same class of work.
- LITERAL SPEC PATHS EXIST IN PLANS' `Scope-Paths`: `wenmg4` declares `.aw/records/specs/20260826-0718-01-...`, so a move can fail another plan's finalize scope gate.
- THE GRANDFATHERED NAMES MUST NOT BE RENAMED: pre-cutover specs keep their legacy filenames by documented decision, and `f8m2z2`'s Order 02 reports on them advisorily rather than renaming.
- SPECS HAVE STATUSES PLANS DO NOT: `deferred` and `parked` are legitimate, so the directory mapping needs a recorded decision rather than a copy of the plans list.
- ORDER 01 IS A HARD PRECONDITION, proven: a subdir spec yields `all specs conform` over ZERO files examined while `specs._spec_files` is non-recursive.
- Shared checkout, three agents authoring concurrently. Check `git status` before moving any file. Suite runs BARE.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the hierarchy answers nothing today | `ls .aw/records/specs/` shows 28 date-prefixed names and no state; finding the 12 live specs required a scripted loop over every file. | measured at HEAD |
| F-2 | HIGH | specs are the sole lifecycle outlier | `plans`/`backlog`/`prompts` partition 5 ways; `specs` 0. Every flat type lacks a lifecycle (`reviews` 1 of 81, `roadmaps` 0 of 1, `walkthroughs` 2 of 17). | all ten trees measured |
| F-3 | HIGH | the setter would let the tree drift immediately | `specs.run_set` rewrites metadata and appends history but never relocates (`specs.py:498`), while `backlog.py:534` explicitly moves. Without E-03 the invariant is decorative. | both read at HEAD |
| F-4 | HIGH | Order 01 is a correctness precondition | A spec in a subdir gives `aw specs check: all specs conform` while `specs._spec_files` returns ZERO files. Migrating first validates the tree against nothing. | throwaway repo |
| F-5 | HIGH | literal citations will break, including a live one | `wenmg4` declares a spec's literal path in `- Scope-Paths:`, so a move could fail that plan's finalize scope gate for an unrelated reason. `25kzda` is cited widely. | `wenmg4`'s metadata |
| F-6 | MEDIUM | the live set is growing while terminal is flat | The item measured 24 specs / 8 live; HEAD is 28 / 12 with terminal held at 16, so the flat tree's noise is worsening. | both counts |
| F-7 | MEDIUM | specs have statuses plans lack | `deferred` and `parked` have no plans-tree equivalent, so the status-to-directory mapping is a decision, not a copy. | the spec status vocabulary |
| F-8 | MEDIUM | a migration precedent exists | `plans-adopter` (`lus9ou`, `7qx7ys`, `8q6yr9`) and `records-taxonomy-cleanup` (`u7xtni`) both executed this class of work. | those executed plans |
| F-9 | MEDIUM | the accepted cost is real | Subdirs promote "location must agree with status" from not-applicable to load-bearing, which is the invariant generating the plans artifact/status discrepancy class. Accepted by maintainer ruling, not dismissed. | the item's own AGAINST argument |
| F-10 | LOW | renaming is out of scope and would be worse | Grandfathered pre-cutover names stay; renaming is a per-record maintainer call and would break more citations than the move. | the spec-name cutover decision |

## Proposed changes (ordered, validatable)

1. Confirm Order 01 landed by behavior, stopping if not (E-01).
2. Re-measure the status map, decide the directory mapping including `deferred`/`parked`, and classify every literal citation (E-02).
3. Teach `aw specs set` to relocate via `git mv` with a dry-run, transactionally (E-03).
4. Move the specs through that path, renaming nothing, updating every citation and the README (E-04).
5. Prove the browse affordance with before/after listings and a mechanical location-equals-status check (E-05).
6. Prove every spec-reading surface still works and the setter maintains the invariant (E-06).

## Deferred / out of scope (with reason)

- MAKING THE READERS RECURSIVE. Order 01 (`y4bdoz`) owns it and this child DEPENDS on it. Implementing it here would collapse the safety ordering the Set exists to enforce.
- RENAMING ANY SPEC. Grandfathered pre-cutover names stay by documented decision; renaming is a per-record maintainer call, is reported advisorily by `f8m2z2`'s Order 02, and would break more citations than the relocation.
- PROMOTING `location must agree with status` TO A FAIL-CLOSED CHECK RULE. The parent's OQ-03 holds that severity decision. This child makes the invariant TRUE and checkable; whether `aw check` errors on a violation is a separate call with its own blast radius.
- MONTH-SHARDING THE TERMINAL SPECS. The parent's OQ-02. `implemented/` holds about 15 files, which is browsable; sharding now would add a second structural change to a migration whose value is legibility.
- CHANGING THE SPEC STATUS VOCABULARY OR TRANSITION RULES. `aw specs set` owns which transitions are legal and enforces the human-attestation rule for `approved`; this child changes WHERE a file lands.
- THE REVIEWS-LOCATION QUESTION (`sv0sf3`). The item explicitly forbids bundling, and that item's own premise is separately falsified (80 of 81 reviews are `Subject-Type: ipd`).
- EDITING THE AGENTS.md MANAGED BLOCK. It describes `aw specs` to every agent and is installed from `engine.py`; hand-editing it is how a managed block drifts. RECORD a finding if it needs the new layout.

## Scope check

- Over-scope: none for the deliverable, but the `.aw/records/specs` and `.aw/records/plans/pending` entries are deliberately broad and need justifying, below.
- Scope-Paths justification: `agent_workflows/specs.py` holds `run_set` (`:498`), which E-03 teaches to relocate; `.aw/records/specs` is the tree being restructured plus its README (E-04), and it is declared as a DIRECTORY because the move touches all 28 files and creating per-file entries would be unreadable; `.aw/records/plans/pending` is declared ONLY because E-04 must update literal spec paths inside other plans' `- Scope-Paths:` declarations (`wenmg4` is a known instance) and a plan whose declared path vanished would fail its own finalize gate, so this edit is a REPAIR of other plans' citations rather than a change to their content, and the executor must touch NOTHING else in that directory; `tests/test_specs_status_dirs.py` is new and carries the mapping, setter-move and invariant tests. `agent_workflows/check_engine.py` is NOT declared: it is already recursive and Order 01 makes the specs module match it.
- Under-scope, stated rather than left as `none`: this child does not make readers recursive, renames no spec, does not promote the invariant to a fail-closed rule, does not month-shard terminal specs, changes no status vocabulary or transition rule, does not touch the reviews question, and does not edit the managed block. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY. A test carrying a literal spec path as a fixture that breaks is a citation E-02 MISSED, not an environmental failure.
- THE ORDER 01 PRECONDITION demonstrated behaviorally (E-01), asserting the examined COUNT not the verdict text.
- BEFORE AND AFTER `ls .aw/records/specs/` listings, side by side, as the primary evidence of the browse affordance.
- A MECHANICAL LOCATION-EQUALS-STATUS CHECK over EVERY spec, not a sample.
- `aw specs check` examining a count EQUAL to the on-disk `*.spec.md` count and nonzero. A "conform" verdict over zero files is a FAILURE.
- `aw check specs` and `aw check all --agent` PER-RULE counts before and after, with any change explained.
- `aw find specs <id6>` for a spec in EACH status directory.
- `aw attention` still listing live specs; `aw doctor` agreeing with `aw check` on the spec set.
- THE DRY-RUN PREVIEW of the whole 28-file move, pasted before it was applied.
- EVERY LITERAL SPEC CITATION shown resolving after the move, naming `wenmg4`'s `Scope-Paths` entry explicitly.
- A SETTER ROUND TRIP after the migration: transition a throwaway spec and show the file MOVED to the matching directory.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`.aw/records/specs/README.md` MUST document the new layout: which directory each of the nine statuses maps to, and the rule that location agrees with status. That file is where a human browsing the tree lands, so it is the documentation that matters most for this change, and E-04 owns it.

`aw specs set`'s help text and `run_set`'s docstring must state that a transition MOVES the file, mirroring how `aw backlog set` is documented ("moves the file between the disposition dirs"). Without that, an operator will not expect a relocation and may look for a spec where they left it.

THE AGENTS.md MANAGED BLOCK describes the spec lifecycle and `aw specs` to every agent, and is installed from `engine.py`. Do NOT hand-edit it. If it needs to state the new layout, that is a change to `engine.py`'s installed text plus a re-install, which is a separate decision; RECORD it as a finding.

No spec amendment is expected: the lifecycle states are unchanged and only their physical arrangement changes. If the executor finds spec text asserting the specs tree is FLAT, that text becomes false with this change and the spec file must be declared in `Scope-Paths` before editing, per the spec-amendment rule. Write no em or en dashes in the README or help text.

## Open questions

### OQ-01: Which directory names do `deferred` and `parked` get?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ONE DIRECTORY PER STATUS, NAMED FOR THE STATUS, including `deferred/` and `parked/`. The alternative (folding them into a shared `inactive/`) would break the single property that makes this migration worth its cost: that the directory name IS the status, so a listing answers the question without a lookup table. The backlog tree already carries `parked/` as a first-class directory alongside `open`/`graduated`/`blocked`/`done`, so a spec `parked/` is consistent rather than novel, and `deferred` is meaningful enough to warrant its own shelf given a deferred spec must carry a typed gate. The cost is a directory holding one or two files, which is the same shape the plans tree already tolerates for `reusable/`.

### OQ-02: Should the migration move files with `git mv` or rewrite and delete?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `git mv`, so history follows the file. A spec's history is load-bearing here in a way it is not for a scratch file: `sd2wz5`/`wenmg4` exists precisely because a spec paragraph's CORRECTION history (`a59f2c5`) is the evidence a reader needs, and `25kzda` carries a long workflow-history record of maintainer rulings. A rewrite-and-delete would make `git log --follow` on a spec stop at the migration, which is exactly when someone auditing a decision would need to cross it. This also matches the plans-tree convention, where the lifecycle setters move files as the authoritative act.

### OQ-03: What happens if a spec's status is missing or unrecognized during the migration?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN BECAUSE THE SAFE ANSWER AND THE TIDY ANSWER DIFFER, and the choice should be made with the measured count in hand. All 28 specs carry a `- Status:` today, so this may be vacuous; E-02's re-measurement will confirm, and three agents are authoring concurrently so a new spec could arrive mid-migration without one. The SAFE answer is to LEAVE such a file at the tree root and report it, since a spec whose status cannot be read is exactly the artifact you do not want silently filed under a guess. The TIDY answer is a `draft/` default, which risks asserting a state the file never claimed. The bias should be toward leaving and reporting, because this migration's whole premise is that location carries meaning, and a guessed location is a false statement in the surface being created.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the behavioral demonstration that a spec in a subdirectory is EXAMINED by `aw specs check` after Order 01, showing the examined COUNT and not merely the verdict text. Paste `y4bdoz`'s `- Status:` and lifecycle directory. If the precondition was unmet, paste the STOP and confirm no file was moved.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the re-measured status map (every spec with its status) and the totals, compared against the authoring baseline of 28 files / 12 live / 16 terminal. Paste the status-to-directory mapping including `deferred` and `parked`. Paste the classified inventory of EVERY literal spec citation, naming `wenmg4`'s `Scope-Paths` entry. Paste `git status` proving no target file was concurrently modified.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the setter change and confirm by inspection it mirrors `backlog.py:534`'s documented behavior. Paste the dry-run output showing a `would move <src> -> <dest>` line. State whether the move and the metadata write are one transaction and how a partial failure behaves. Paste NEGATIVE proof that no transition rule or status vocabulary changed.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the full dry-run preview of the 28-file move AS RUN BEFORE APPLYING, then the applied result. Paste proof every filename and id6 is unchanged (a before/after name list). Paste each updated literal citation. Paste the README text describing the layout. Confirm in one sentence that no spec was renamed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `ls .aw/records/specs/` BEFORE and AFTER, side by side, plus a listing of ONE status directory demonstrating it answers "what is in this state" unaided. Paste the mechanical location-equals-status check over EVERY spec with its result. Do NOT offer `aw attention` output as this item's proof.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `aw specs check`'s examined count alongside the on-disk `*.spec.md` count, equal and nonzero. Paste `aw check specs` and `aw check all --agent` per-rule counts before and after with any change explained. Paste `aw find specs <id6>` for a spec in each status directory, `aw attention` listing live specs, and `aw doctor` agreeing with `aw check`. Paste the setter round trip showing a transitioned spec MOVED. THEN paste the BARE `python3 -m pytest` summary lines before and after with the failure-set delta stated; trace any literal-path fixture failure to a missed citation rather than calling it environmental.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS CHILD CARRIES `Item-Dependencies: executed:y4bdoz` AS A CORRECTNESS EDGE, not a preference. Order 01 makes the spec readers recursive; until it lands, a spec in a subdirectory is invisible to `aw specs check`, which then reports `all specs conform` having examined ZERO files. Running this migration first would produce a validated-looking tree validated against nothing, which is the worst available outcome of a records migration and was PROVEN in a throwaway repo rather than inferred.

THE SET EXISTS BECAUSE OF A MAINTAINER RULING, and reviewers should know an earlier recommendation in this session was to PARK the item. That recommendation was inherited from the item's own framing and did not survive testing: specs turned out to be the only lifecycle-bearing type not partitioned, every flat type is flat because it has no lifecycle, and the live spec set has grown from 8 to 12 while terminal held at 16.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. PREVIEW THE MOVE BEFORE APPLYING IT and paste the preview. Use `git mv` so history follows. RENAME NO SPEC. Do NOT touch anything in `.aw/records/plans/pending` except a literal spec path inside another plan's `Scope-Paths` that this move invalidates, and do not alter that plan's content otherwise. Check `git status` before moving any file, since three agents are authoring in this checkout and a concurrent edit to a file you relocate must be reported rather than overwritten. Do NOT hand-edit the AGENTS.md managed block. Never report a "conform" verdict over zero files as a pass. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the dry-run preview, the before/after directory listings, and the mechanical location-equals-status check over every spec.
