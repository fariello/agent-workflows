# IPD: Make every spec reader recursive so a spec in a subdir cannot become invisible

- Date: 2026-09-08
- Kind: child
- Concern: A SPEC PLACED IN A SUBDIRECTORY OF `.aw/records/specs/` IS INVISIBLE TO ITS OWN CHECKER TODAY, AND `aw specs check` REPORTS SUCCESS HAVING READ NOTHING. PROVEN in a throwaway git repo, not inferred: with one real spec copied into `.aw/records/specs/approved/`, `aw specs check` printed `all specs conform`, while `specs._spec_files(repo)` returned ZERO files and `check_engine._iter_type_files(repo, "specs")` returned ONE. So the two surfaces already disagree about what a spec IS, and the disagreement resolves in the most dangerous direction: the type's own validator sees nothing and calls it clean.
  THE ROOT CAUSE IS ONE CHARACTER OF METHOD CHOICE. `specs._spec_files` (`specs.py:70`) collects with NON-recursive `glob("*.md")` (`:89`), while `check_engine._iter_type_files` uses `rglob("*.md")` (`check_engine.py:488`). Both walk the same roots and both resolve the same legacy `.agents/docs/specs` fallback; only the recursion differs.
  THIS IS A LATENT BUG INDEPENDENT OF ANY MIGRATION, which is why this child is worth executing even alone. Any subdirectory anyone creates under `.aw/records/specs/` for any reason (an `archive/`, a topical grouping, a stray directory from a partial move) silently removes every spec beneath it from `aw specs check`. Nothing warns, and the verb's output is indistinguishable from a genuinely clean tree.
  IT IS ALSO THE HARD PRECONDITION FOR ORDER 02. That child migrates 28 specs into status subdirectories. Performed before this fix, it would produce a tree in which `aw specs check` validates ZERO specs and reports conformance, which is a validated-looking tree that was validated against nothing. That is the single most dangerous outcome available in a records migration, and it is why the parent's CID-1 exists.
  THE FIX MUST NOT BE A ONE-LINE SWAP, because `_spec_files` is not the only reader and a partial fix is worse than none: it would make the surfaces agree in the case someone tested and disagree elsewhere. `_spec_files` has at least two consumers inside `specs.py` (`:430`, `:858`), and the module also resolves roots through `resolve_record_read_paths("specs", ...)` (`:74`), so the audit must establish every path by which a spec file is enumerated rather than fixing the one that was measured.
- Scope: Make every enumeration of spec files recursive, so a spec in any subdirectory is seen by `aw specs check` and by every other spec-reading surface, and prove the two currently-disagreeing surfaces agree. EXCLUDES moving any spec (Order 02 owns the migration), and excludes changing what any check REPORTS about a spec.
- Scope-Paths: agent_workflows/specs.py, tests/test_specs_recursive_read.py
- Item-Dependencies: none
- Status: to-review
- Set: specdirs
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: y4bdoz
- From-Backlog: qzhfk2

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `qzhfk2` as Order 01, covering a defect the ITEM DID NOT KNOW ABOUT. The item raised the subdirs question and named the migration cost as "check_names and the shared recursive type scanner in check_engine.py", i.e. it believed the shared scanner was the thing needing work and that it was already recursive. Measured, the opposite is the problem: `check_engine` IS recursive (`rglob`, `:488`) and `specs.py` is NOT (`glob`, `:89`). PROVEN in a throwaway repo: a spec in `.aw/records/specs/approved/` gives `aw specs check: all specs conform` while `specs._spec_files` finds ZERO files and `check_engine._iter_type_files` finds ONE. So this is a live latent bug today, worth fixing on its own, and it is the hard precondition for Order 02's migration, which would otherwise validate a tree against nothing. This child carries no `Item-Dependencies` and must execute FIRST in the Set.

## Goal

Stop a subdirectory from hiding a spec from its own validator, so the migration that follows cannot silently produce a tree validated against zero files.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce, then find every reader

- [ ] E-01 REPRODUCE THE INVISIBILITY AS A FAILING TEST FIRST, so the fix is demonstrated rather than asserted. In a throwaway repo, place a valid spec in `.aw/records/specs/approved/` and assert that `aw specs check` SEES it. That assertion must FAIL at HEAD.
  ASSERT THE FILE COUNT, NOT ONLY THE VERDICT. The dangerous behavior is a "conform" verdict over ZERO files, so a test that only checks the exit code or the words "all specs conform" would PASS at HEAD and prove nothing. Assert that the number of specs examined equals the number on disk.
  PIN THE CURRENT DISAGREEMENT EXPLICITLY: in the same fixture, assert `specs._spec_files` returns 0 while `check_engine._iter_type_files(..., "specs")` returns 1 at HEAD. That contrast is the defect in one assertion and is what makes the fix's effect legible.
  - Depends on: none
  - Expected outcome: a test failing at HEAD proving a subdir spec is invisible to `specs._spec_files` while visible to `check_engine`, asserted by COUNT rather than by verdict text.
  - Execution state: pending

- [ ] E-02 AUDIT EVERY PATH BY WHICH A SPEC FILE IS ENUMERATED, and write the list down before changing anything. A partial fix is worse than none, because it makes the surfaces agree in the tested case and disagree elsewhere.
  START FROM THE KNOWN POINTS AND EXPAND BY SEARCH, not by assumption: `specs._spec_files` (`specs.py:70`) with its non-recursive `glob` (`:89`); its consumers at `:430` and `:858`; the root resolution via `resolve_record_read_paths("specs", ...)` (`:74`) and the legacy `.agents/docs/specs` fallback (`:83`); and `check_engine`'s already-recursive `_iter_type_files` (`:488`). Then search the package for any OTHER place that globs or lists the specs directory.
  CHECK THE ADJACENT SURFACES TOO, because a spec is read by more than its own module: `selectors` resolves specs by id6/setid/status, `aw find specs` displays them, `aw attention` reads their status, and `aw doctor` runs the collision scan over them. Establish for EACH whether it recurses, and record the answer. Any that does not is part of this fix.
  IF A READER CANNOT BE MADE RECURSIVE SAFELY, SAY SO rather than forcing it. For example a reader that deliberately treats a subdirectory as a grouping (as `research` does) would need a different treatment; report that rather than making an unsafe change.
  - Depends on: E-01
  - Expected outcome: a written inventory of every spec enumeration path with its current recursion behavior, and an explicit note of any that cannot be made recursive safely.
  - Execution state: pending

### Task group 2: make them agree

- [ ] E-03 MAKE EVERY ENUMERATION RECURSIVE, and keep the two skip conventions the trees already rely on.
  THE MINIMAL CORRECT CHANGE is `glob("*.md")` -> `rglob("*.md")` at `specs.py:89`, plus any other non-recursive site E-02 found. Follow `check_engine._iter_type_files`'s shape, which is the in-repo model that already works.
  PRESERVE THE SKIPS. `_spec_files` already excludes `README.md`; `check_engine` excludes `README.md`, `INDEX.md` and `STATUS.md` via `_SKIP_NAMES`. Recursion must not start pulling in a nested `README.md` from a status directory, and Order 02 may well add one. Align the skip set with `check_engine`'s rather than inventing a third convention.
  DE-DUPLICATE BY RESOLVED PATH. `_spec_files` already returns `sorted(set(files))`, and the dual `.aw/`/`.agents/` roots can overlap; recursion widens the chance of a double count, so keep the dedup and prove it.
  DO NOT CHANGE WHAT ANY CHECK REPORTS about a spec. This item changes WHICH FILES are read, not the verdicts. If making a reader recursive newly surfaces a genuine finding on an existing spec, that is a real defect the fix EXPOSED: report it, do not fix it here and do not suppress it.
  - Depends on: E-02
  - Expected outcome: every enumeration recursive, `check_engine`'s skip convention adopted, dedup preserved and proven, and no verdict logic changed.
  - Execution state: pending

- [ ] E-04 PROVE THE SURFACES NOW AGREE, AND THAT THE FLAT TREE IS UNAFFECTED. Both halves matter: the fix must work for subdirs and must change nothing for the tree as it stands today.
  ASSERT AGREEMENT AS AN EQUALITY, on the real repository: the set of specs `specs._spec_files` returns must EQUAL the set `check_engine._iter_type_files(..., "specs")` returns. An equality over the live corpus is stronger than any fixture and is the property that was violated.
  ASSERT THE FLAT-TREE COUNT IS UNCHANGED. Today's 28 specs sit flat, so `aw specs check` must examine exactly the same 28 before and after. A change here would mean recursion picked up something it should have skipped.
  ASSERT THE SUBDIR CASE END TO END from the verb, not only from the helper: `aw specs check` in a fixture repo with a spec in a subdir must EXAMINE it, and if that spec is non-conforming the verb must REPORT it. A reader fix that finds the file but whose caller still ignores it is not a fix.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA. Baseline measured on main 2026-09-08: `1 failed, 5648 passed`, the failure being the pre-existing `tests/test_orchestrator_retirement.py` case. Inside a lane worktree roughly 32 further failures are environmental. Criterion: AFTER minus BEFORE is EMPTY.
  - Depends on: E-03
  - Expected outcome: set equality between the two surfaces on the live corpus, an unchanged flat-tree count, an end-to-end subdir report from the verb, and an empty bare-suite delta.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE DEFECT IS ONE METHOD CHOICE: `specs._spec_files` uses `glob("*.md")` (`specs.py:89`); `check_engine._iter_type_files` uses `rglob("*.md")` (`check_engine.py:488`). Same roots, same legacy fallback, different recursion.
- IT FAILS IN THE DANGEROUS DIRECTION: measured, a subdir spec yields `aw specs check: all specs conform` over ZERO files examined.
- THE TWO SURFACES ALREADY DISAGREE: `specs._spec_files` 0 versus `check_engine._iter_type_files` 1 on the same fixture. That is a bug today, not only a migration risk.
- SKIP CONVENTIONS DIFFER AND MUST BE ALIGNED: `_spec_files` skips only `README.md`; `check_engine` skips `README.md`, `INDEX.md`, `STATUS.md` via `_SKIP_NAMES`. Recursion makes the difference matter.
- THE DUAL ROOTS CAN OVERLAP: `_spec_files` resolves via `resolve_record_read_paths("specs", ...)` plus a `.agents/docs/specs` fallback and already dedups with `sorted(set(files))`. Keep that.
- `_spec_files` HAS AT LEAST TWO CONSUMERS in its own module (`:430`, `:858`), so the fix is behind a shared helper rather than at a call site.
- ADJACENT READERS EXIST: `selectors` (id6/setid/status resolution), `aw find specs`, `aw attention`, and `aw doctor`'s collision scan all read specs. E-02 must establish each one's recursion behavior.
- THE ITEM'S OWN COST ESTIMATE WAS INVERTED: `qzhfk2` named the shared `check_engine` scanner as the thing needing work; it is already correct, and the type's own module is the broken one.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | a subdir spec is invisible to its own checker | With a spec in `.aw/records/specs/approved/`, `aw specs check` printed `all specs conform` while examining ZERO files. | throwaway repo at HEAD |
| F-2 | HIGH | the two surfaces disagree today | `specs._spec_files` returned 0 and `check_engine._iter_type_files(..., "specs")` returned 1 on the same fixture. | measured directly |
| F-3 | HIGH | root cause is `glob` versus `rglob` | `specs.py:89` is non-recursive; `check_engine.py:488` is recursive. Same roots, same fallback. | read at HEAD |
| F-4 | HIGH | it is the hard precondition for the migration | Order 02 moves 28 specs into subdirs; performed first, it would leave `aw specs check` validating zero specs and reporting conformance. | F-1 plus Order 02's scope |
| F-5 | MEDIUM | a partial fix is worse than none | `_spec_files` has two in-module consumers and the module resolves roots separately, so fixing only the measured path would make the surfaces agree in one case and disagree elsewhere. | `specs.py:70`, `:74`, `:430`, `:858` |
| F-6 | MEDIUM | skip conventions differ | `_spec_files` skips only `README.md`; `check_engine` skips three names. Recursion could otherwise pull a nested README into the spec set, and Order 02 may add one. | both readers |
| F-7 | MEDIUM | the item's cost estimate was inverted | `qzhfk2` named `check_engine`'s shared scanner as the work; that scanner is already recursive and correct, while the specs module is not. | the item text versus measurement |
| F-8 | LOW | dedup already exists and must survive | `_spec_files` returns `sorted(set(files))` and the dual roots can overlap; recursion widens the double-count surface. | `specs.py:90` |
| F-9 | LOW | this is valuable standalone | Any subdirectory anyone creates under the specs tree for any reason already hides specs from `aw specs check`, with no warning. | F-1 generalized |

## Proposed changes (ordered, validatable)

1. Reproduce the invisibility as a failing test asserting the examined COUNT, not the verdict text (E-01).
2. Audit every spec enumeration path, including adjacent readers, and record each one's recursion behavior (E-02).
3. Make every enumeration recursive, aligning the skip set and preserving dedup (E-03).
4. Prove set equality between the surfaces, an unchanged flat-tree count, and an end-to-end subdir report (E-04).

## Deferred / out of scope (with reason)

- MOVING ANY SPEC. Order 02 (`1bdxcp`) owns the migration and depends on this child. This item creates no directory and relocates no file.
- CHANGING ANY CHECK VERDICT. This item changes WHICH FILES are read. If recursion newly exposes a genuine finding on an existing spec, that is a real defect to REPORT, not to fix here and not to suppress.
- MAKING `research`'s SUBDIRS RECURSIVE-SAFE. That tree's 5 subdirs are deliberate ad hoc groupings rather than statuses, so its enumeration semantics are a different question.
- THE `location must agree with status` INVARIANT. It has no meaning until subdirs exist; Order 02 establishes it and the parent's OQ-03 holds the severity question.
- ALIGNING EVERY RECORDS TYPE's SKIP SET. This item aligns SPECS with `check_engine`'s convention; auditing all ten trees for skip-set drift is a separate sweep.
- `aw archive` FOR SPECS. Deep-shelving terminal specs is the parent's OQ-02 and is deferred there.

## Scope check

- Over-scope: none. One helper's enumeration plus whatever E-02's audit proves is part of the same defect, and one test module.
- Scope-Paths justification: `agent_workflows/specs.py` holds `_spec_files` (`:70`), its non-recursive `glob` (`:89`), the root resolution and legacy fallback (`:74`, `:83`), and the two in-module consumers (`:430`, `:858`), which is the whole of E-03; `tests/test_specs_recursive_read.py` is new and carries the failing-first reproduction, the set-equality assertion and the end-to-end verb test. `agent_workflows/check_engine.py` is deliberately NOT declared: it is already recursive and correct, and this item's job is to make the specs module MATCH it, so editing it would be the wrong direction. If E-02 finds an adjacent reader outside `specs.py` that is non-recursive, that is a scope-widening finding to report and reconcile at finalize, not a silent addition.
- Under-scope, stated rather than left as `none`: this item moves no spec, changes no verdict, does not touch `research`'s grouping semantics, does not establish the location invariant, does not audit other types' skip sets, and does not address archiving. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- THE FAILING-FIRST TEST (E-01) shown FAILING at HEAD and PASSING after, both outputs pasted. It must assert the examined COUNT; a test asserting only the verdict text would pass at HEAD and prove nothing.
- THE HEAD DISAGREEMENT PINNED: `specs._spec_files` 0 versus `check_engine._iter_type_files` 1 on the same fixture, before the fix.
- SET EQUALITY on the LIVE repository after the fix: the specs `_spec_files` returns must equal those `check_engine` returns, as sets of resolved paths.
- THE FLAT-TREE COUNT UNCHANGED: `aw specs check` examines the same number of specs before and after (28 at authoring).
- AN END-TO-END SUBDIR TEST from the verb: a NON-CONFORMING spec in a subdirectory must be REPORTED by `aw specs check`, proving the caller acts on the newly-found file.
- THE E-02 AUDIT INVENTORY pasted, naming every enumeration path and its recursion behavior.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`_spec_files`'s DOCSTRING must state that enumeration is RECURSIVE and WHY: a spec in a subdirectory was previously invisible to `aw specs check`, which reported conformance over zero files. Without the reason recorded, a future performance pass will narrow it back to `glob` and silently restore the defect.

The skip-set alignment must be commented, naming `check_engine`'s `_SKIP_NAMES` as the source convention, so the two do not drift apart again in the other direction.

No spec amendment is expected: this is an internal reader fix. If the executor finds spec or README text asserting that the specs tree is FLAT and that enumeration therefore need not recurse, that text becomes misleading once Order 02 lands, and it should be REPORTED for Order 02 to handle with the README rather than edited here.

## Open questions

### OQ-01: Should the fix be `rglob`, or an explicit status-directory list?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `rglob`, because a hardcoded directory list is the defect this repository has already measured elsewhere. `run_viewer.find_artifact_file` hardcodes nine plan directories including one that does not exist, and it cannot follow the weekly-sharded archive; that is the failure mode a list produces as soon as the tree gains a directory nobody updated the list for. `rglob` also makes this child's fix correct for the parent's OQ-02 (month-sharded terminal specs) without revisiting it, and it matches `check_engine._iter_type_files`, which is the surface this fix exists to agree with. The cost is that recursion picks up any nested file, which is exactly why E-03 must align the skip set rather than only swapping the method.

### OQ-02: What if recursion newly surfaces findings on existing specs?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: REPORT THEM, FIX NOTHING, SUPPRESS NOTHING. Today the flat tree has no subdirectories, so recursion should find exactly the same 28 specs and surface nothing new; E-04 asserts that count is unchanged precisely to detect a surprise. If something IS newly surfaced, it means a spec exists somewhere the checker never looked, which is a genuine defect this fix EXPOSED rather than caused. Fixing it inside a reader change would conflate two things in one review, and suppressing it would recreate the invisibility in a new form. The honest output is a finding for a human, and it is also strong evidence the fix was worth making.

### OQ-03: Should this child also make the adjacent readers recursive?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEPENDS ON WHAT E-02's AUDIT FINDS, which is why it is open rather than pre-answered. `selectors`, `aw find specs`, `aw attention` and `aw doctor` all read specs, and `selectors._iter_paths` is already used recursively for other types, so several may already be correct. If the audit finds one that is NOT, the choice is between widening this child (keeping the Set's precondition genuinely complete) and filing it separately (keeping this diff minimal). The bias should be toward INCLUDING it: the parent's CID-3 requires that no spec become invisible at any point, and a non-recursive adjacent reader would violate that after Order 02 lands, so leaving it would ship the migration with a known hole. E-02 must present the audit and the executor should widen with a recorded justification rather than deferring silently.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new test and its ACTUAL FAILING output at HEAD. Quote the assertion showing it checks the examined COUNT rather than the verdict text, and explain in one sentence why a verdict-text assertion would have passed at HEAD. Paste the pinned disagreement: `specs._spec_files` 0 versus `check_engine._iter_type_files` 1 on the same fixture.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the audit inventory naming EVERY spec enumeration path with its current recursion behavior, including the adjacent readers (`selectors`, `aw find specs`, `aw attention`, `aw doctor`). State explicitly whether any is non-recursive, and if so whether you widened scope (with justification) or reported it, per OQ-03.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the changed enumeration and the aligned skip set with its comment naming `check_engine._SKIP_NAMES`. Paste proof the dedup survives (a case where the dual roots overlap yields no double count). Paste NEGATIVE proof that no verdict logic changed (a diff scoped to the enumeration).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the SET EQUALITY result on the live repository between `specs._spec_files` and `check_engine._iter_type_files`. Paste the flat-tree examined count before and after, equal (28 at authoring). Paste the end-to-end test showing a NON-CONFORMING spec in a subdirectory is REPORTED by `aw specs check`, with its unpiped exit code. THEN paste the BARE `python3 -m pytest` summary lines before and after and state the failure-set delta explicitly. If recursion surfaced any new finding, paste it as a report per OQ-02.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS CHILD MUST EXECUTE FIRST IN THE SET and carries no `Item-Dependencies` for that reason. Order 02 (`1bdxcp`) depends on it (`executed:y4bdoz`), because migrating specs into subdirectories while `specs._spec_files` is non-recursive would leave `aw specs check` validating ZERO specs and reporting conformance. That was PROVEN in a throwaway repo, not inferred.

IT IS ALSO WORTH EXECUTING ALONE, which is worth stating so it is not treated as mere migration scaffolding: any subdirectory under `.aw/records/specs/` today already hides specs from their own checker, silently, with output indistinguishable from a clean tree.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Write the FAILING TEST FIRST and paste its failure; a reader fix demonstrated only against the fixed code is not demonstrated. Do NOT move or create any spec file, and do NOT create a status directory: that is Order 02's work. Do NOT edit `check_engine.py`; it is already correct and this fix must match it. Re-locate every symbol by NAME rather than by the line numbers cited here. Never report a "conform" verdict over zero files as a pass. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the failing-then-passing contrast and the live-corpus set equality.
