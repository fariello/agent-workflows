# IPD: Refuse or expand a directory argument in the commit path so a records move cannot land one half, and cover the untracked-destination shape the rename fix cannot see

- Date: 2026-09-23
- Kind: child
- Concern: BACKLOG `mx1b4v`'S ROOT CAUSE IS ALREADY FIXED, AND A DIFFERENT ROUTE TO THE SAME CORRUPTION IS NOT. The item says the runner's backlog-close commit "lands the addition but not the deletion", because `git_commit_helper._staged_paths` read `git diff --name-only --cached`, which prints only the destination of a staged rename. Commit `26519096` ("fix(commit): commit both sides of a staged rename, not just the destination") replaced that with `--name-status --cached -z` and parses `R`/`C` records as two paths. VERIFIED WORKING at HEAD `22cf67d9` on a realistic 30-line item: naming BOTH sides as explicit files produced ONE commit containing `R095 open/a.md -> done/a.md` and left `git status --porcelain` EMPTY.
  WHAT IS STILL BROKEN IS THE UNTRACKED-DESTINATION SHAPE, WHICH THE RENAME FIX CANNOT SEE, AND I HIT IT IN PRODUCTION WHILE GRADUATING `mx1b4v` ITSELF. `aw backlog set` relocates by `core.atomic_write(dest, ...)` then `src.unlink()` (`backlog.py`), with NO `git mv`, so before staging the destination is UNTRACKED and the source deletion is UNSTAGED. A rename record only exists once BOTH sides are in the index, so if the destination never gets staged there is no `R` record for the `26519096` parser to find, and the fix is inert by construction.
  MEASURED TWICE, ONCE FOR REAL AND ONCE IN ISOLATION. FOR REAL: committing ten status moves through `aw commit --no-plan` while naming the destinations as DIRECTORIES (`.aw/records/backlog/done/`) produced commit `ca8e22e4` containing ten `D open/...` lines and NO `A done/...` lines, leaving all ten destinations staged-but-uncommitted; at that commit every one of those ten items existed in NEITHER tree. It took a second commit (`65109c8c`) naming the ten destination FILES to repair it. IN ISOLATION on a throwaway repo, `offer_commit(root, ["open/a.md", "done/"], ...)` returned `status='committed'` with `staged=('open/a.md',)` and committed `D open/a.md` alone, while the same call with `["open/a.md", "done/a.md"]` committed the paired `R095` and left a clean tree. So the discriminator is precisely DIRECTORY-VERSUS-FILE, not rename detection.
  WHY THIS IS THE SAME SEVERITY AS THE ITEM IT COMPLETES. `mx1b4v` is `high`/`Blocks-Release: next` because it duplicated 22 items across `graduated/` and `done/`. This route is the MIRROR IMAGE and is strictly worse per occurrence: a duplicated item is visible to `aw attention` as `attention.duplicate-id` (loud, and that is how the 36-item incident was found), whereas an item committed as a deletion with no addition is SILENTLY ABSENT from every status tree, and no rule reports a record that exists nowhere. A caller gets `status='committed'` and a success message either way.
- Scope: Make it impossible for the shared commit path to land one half of a records move. IN: (a) decide and implement the directory-argument behavior per OQ-01, either REFUSING a directory argument with a message naming the files it would have to expand to, or EXPANDING it to the files it contains before the intersection is computed; (b) make the success report honest, so a caller that named N paths and got fewer committed is TOLD rather than reading `committed`; (c) a regression test using the UNTRACKED-DESTINATION shape production actually produces, since no existing test reaches it. OUT: re-fixing the staged-rename parser, which `26519096` shipped and this plan VERIFIES rather than changes; converting `aw backlog set` to `git mv` (a plausible alternative fix, deliberately deferred to OQ-02 because it changes a writer rather than the commit gateway every writer shares, and the gateway fix protects callers that will never be converted).
- Scope-Paths: agent_workflows/git_commit_helper.py, tests/test_git_commit_helper.py
- Item-Dependencies: none
- Status: to-review
- Set: movehalf
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: hv9gar
- From-Backlog: mx1b4v
- Blocks-Release: next

## Workflow history

- 2026-09-23 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `mx1b4v`, NARROWED and RE-AIMED by measurement. The item's stated cause (rename detection hiding the source) is FIXED at `26519096` and verified working here (`R095`, clean tree). What survives is a route the rename fix cannot reach: an UNTRACKED destination never forms a rename record, so a directory argument silently commits the deletion alone. `- Blocks-Release: next` is INHERITED from `mx1b4v`.
  THIS DEFECT BIT ME WHILE GRADUATING THE ITEM THAT DESCRIBES IT, which is the strongest evidence for it and is why the plan exists rather than the item simply being closed. Ten backlog status moves committed as ten deletions with no additions (`ca8e22e4`), repaired by a second commit (`65109c8c`). I then reproduced it in a throwaway repo to isolate the discriminator as directory-versus-file rather than rename detection.
  I DELIBERATELY DID NOT WIDEN THIS TO `aw backlog set`'s write+unlink. Converting that writer to `git mv` would ALSO fix my case, and it is recorded as OQ-02 rather than adopted, because the gateway is what every writer shares and a per-writer fix leaves the next writer exposed.

## Goal

Make the shared commit gateway incapable of committing one half of a records move: a directory argument must not silently drop the files it names, and a short commit must not report success as if it were complete.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm the split before changing the gateway

- [ ] E-01 REPRODUCE BOTH SHAPES AT YOUR HEAD AND CONFIRM WHICH IS ALREADY FIXED. This plan asserts that one route is closed and another is open, and an executor who trusts that could either re-fix the parser or miss the live hole.
  PROVE THE FIXED ROUTE STILL WORKS: on a throwaway repo, move a realistic (30+ line) record file by write+unlink, `git add` BOTH sides, then call `offer_commit` naming both as explicit FILES. Expect ONE commit carrying a single `R<score> old -> new` record and an EMPTY `git status --porcelain`. At authoring: `R095`, clean.
  PROVE THE OPEN ROUTE IS OPEN: the same fixture, but call `offer_commit` naming the source file and the destination DIRECTORY. At authoring this returned `status='committed'`, `staged=('open/a.md',)`, committed `D open/a.md` alone, and left `A done/a.md` staged. Paste both.
  READ `_staged_paths`' DOCSTRING BEFORE TOUCHING ANYTHING. It records the 36-item incident and explains why `--name-status -z` is the fix rather than post-processing `--name-only`. Nothing here may regress that.
  - Depends on: none
  - Expected outcome: both shapes reproduced with pasted output, confirming the staged-rename route is closed and the untracked-destination-via-directory route is open; any divergence reported rather than absorbed.
  - Execution state: pending

### Task group 2: close the gateway

- [ ] E-02 DECIDE AND IMPLEMENT THE DIRECTORY-ARGUMENT BEHAVIOR, per OQ-01. Today a directory in `rel_paths` contributes nothing to `our_staged`, because that set is an intersection against paths git reports as staged and git reports FILES; the directory simply fails to match and its contents are silently excluded.
  BOTH CANDIDATE FIXES ARE ACCEPTABLE AND SILENCE IS NOT. REFUSING is the smaller change and is defensible for a safety-relevant primitive: a caller that names a directory has made a mistake the helper cannot safely guess at. EXPANDING is friendlier and matches what a caller obviously meant. What must NOT survive is the current behavior, where a directory argument is accepted, contributes nothing, and the call reports success.
  IF YOU REFUSE, NAME THE FILES. A refusal that says only "directories are not accepted" forces the caller to re-derive the list the helper already has; it should print the files the directory contains so the corrected invocation is copy-pasteable.
  DO NOT FORCE-ADD ANYTHING. `_staged_paths`' docstring states "A path this function reports is never force-added and never staged by it: this is a READ", and the surrounding contract is that only caller-named paths are ever staged. Expansion, if chosen, must respect `.gitignore` exactly as the existing staging does.
  - Depends on: E-01
  - Expected outcome: a directory argument either refuses with the contained files named, or expands to them before the intersection; either way it can no longer contribute zero paths while the call reports success; no force-add and no gitignore bypass introduced.
  - Execution state: pending

- [ ] E-03 MAKE A SHORT COMMIT REPORT ITSELF. Independently of E-02, `offer_commit` returned `committed 1 path(s)` for a call that named 2, and `committed 11 path(s)` for my real call that named 13. The count is present but the SHORTFALL is not surfaced, so neither a human skimming output nor an agent checking a status field learns that some named path was dropped.
  THIS IS THE DEFENSE-IN-DEPTH HALF AND IT MATTERS EVEN IF E-02 LANDS PERFECTLY, because the same silent-shortfall shape is reachable by any future argument form the intersection does not match (a glob, a pathspec, a typo'd path). E-02 fixes one cause; E-03 makes the whole class visible.
  DO NOT TURN A LEGITIMATE SHORTFALL INTO A FAILURE. A caller may legitimately name a path with nothing to commit (unchanged file), and that must stay a success. The requirement is that the outcome SAYS which named paths contributed nothing, not that it refuses.
  - Depends on: E-01
  - Expected outcome: an `offer_commit` outcome that named paths which contributed nothing reports them explicitly; an unchanged-path shortfall remains a success; no existing caller's success/failure classification changes.
  - Execution state: pending

### Task group 3: cover the shape production actually produces

- [ ] E-04 TEST THE UNTRACKED-DESTINATION SHAPE, which no existing test reaches. `mx1b4v` already records why the suite was green over the ORIGINAL defect: the fixture's 3-line stub paired at `R055` and reported both paths, while a realistic item pairs at `R098` and reported one. The lesson generalizes and must be applied to this fix too.
  THE FIXTURE MUST START FROM THE WRITER'S REAL OUTPUT SHAPE: destination UNTRACKED, source deletion UNSTAGED, which is exactly what `core.atomic_write` + `src.unlink()` leaves. A fixture that pre-stages both sides tests the ALREADY-FIXED route and proves nothing about this one.
  ASSERT THE TREE, NOT JUST THE COMMIT. The failure signature is a clean-looking commit plus residue in the index, so the test must assert `git status --porcelain` is EMPTY after the commit, and that the resulting commit contains BOTH halves (as a rename record or as paired `A`/`D`). Asserting only the return value would have passed against the broken code.
  ADD THE DIRECTORY-ARGUMENT CASE EXPLICITLY, asserting E-02's chosen behavior (refusal or expansion), so the specific invocation that corrupted `ca8e22e4` is pinned.
  - Depends on: E-02, E-03
  - Expected outcome: a test that fails against pre-E-02 code and passes after, built on the untracked-destination shape, asserting both an empty tree and a both-halves commit, plus an explicit directory-argument case.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `git_commit_helper.offer_commit` is THE shared commit gateway: `aw set`, `aw rename`, `aw commit` and both runners route through it (module docstring; `commit_lock` names the same four). A fix sited here protects every writer, which is the argument for fixing the gateway rather than one writer.
- ONLY CALLER-NAMED PATHS ARE EVER STAGED, and the helper snapshots the index first so a co-worker's staged change cannot be swept in. Any expansion added by E-02 must preserve that property rather than widening what gets staged.
- `aw backlog set` relocates by `core.atomic_write(dest, ...)` + `src.unlink()`, NOT `git mv`, while `status_set` was converted to `git mv` in 2026-09-13 precisely so a move is one staged rename. That inconsistency between two record writers is the root of this plan's shape and is OQ-02.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER | `git_commit_helper.offer_commit` | A DIRECTORY argument contributes zero paths to `our_staged` (an intersection against git-reported FILES) and the call still reports success, so a records move lands its deletion alone and the record exists in NO status tree. Silent: no rule reports a record that exists nowhere. | isolated repo: `offer_commit(root, ["open/a.md","done/"])` -> `status='committed'`, `staged=('open/a.md',)`, commit `D open/a.md`, `A done/a.md` left staged |
| F-2 | BLOCKER | production, commit `ca8e22e4` | Hit for real while graduating `mx1b4v`: ten status moves committed as ten `D` lines with no `A` lines; all ten items existed in neither tree at that commit. Repaired by `65109c8c`. | `git show --name-status ca8e22e4`: 10 `D`, 0 `A` for the moved items |
| F-3 | HIGH (narrowing) | `git_commit_helper._staged_paths` | `mx1b4v`'s STATED cause is FIXED at `26519096` (`--name-status --cached -z`, `R`/`C` parsed as two paths). Naming both sides as explicit files commits `R095` and leaves a clean tree. The rename fix is INERT for F-1 by construction, because an untracked destination forms no rename record. | isolated repo: explicit-files call -> `R095 open/a.md done/a.md`, `git status --porcelain` empty |
| F-4 | MED | `git_commit_helper.offer_commit` | The outcome reports a COUNT but not a SHORTFALL, so `committed 11 path(s)` for 13 named paths reads as success. Any argument form the intersection does not match (directory, glob, typo) is silently dropped. | my real call named 13, message said 11; isolated call named 2, message said 1 |
| F-5 | MED | `tests/test_git_commit_helper.py` | No test uses the untracked-destination shape `atomic_write` + `unlink` produces, so F-1 is uncovered. This repeats the exact reason the ORIGINAL defect shipped green (`mx1b4v`: stub paired `R055` and reported both paths; a realistic item paired `R098` and reported one). | `mx1b4v`'s own recorded analysis; no such fixture found |

## Proposed changes (ordered, validatable)

1. E-01 reproduces both shapes and confirms which route is already closed.
2. E-02 makes a directory argument either refuse (naming the contained files) or expand, never silently contribute nothing.
3. E-03 surfaces a shortfall so a dropped named path cannot read as success.
4. E-04 covers the untracked-destination shape and the directory-argument invocation, asserting an empty tree and a both-halves commit.

## Deferred / out of scope (with reason)

- RE-FIXING THE STAGED-RENAME PARSER. `26519096` shipped it and F-3 verifies it working; E-01 re-proves it rather than changing it.
- CONVERTING `aw backlog set` TO `git mv` (OQ-02). It would also fix my case, and it is deliberately not adopted here: the gateway is shared by every writer, and a per-writer fix leaves the next one exposed. Worth doing on its own merits, as a SUCCESSOR PLAN rather than a backlog item: the change is already designed (convert the writer's write+unlink to `artifact_core.git_mv`, mirroring the 2026-09-13 `status_set` conversion), so it needs authoring and review, not re-discovery.
- A CHECK RULE FOR "RECORD EXISTS IN NO STATUS TREE". This is the detection counterpart to F-1 and is genuinely missing (a duplicated record is caught by `attention.duplicate-id`; an absent one is caught by nothing). It belongs with backlog `4y7nzh`'s write-time integrity work rather than in the commit gateway, and is named here so it is not lost.
- CHANGING `aw commit`'s CLI SURFACE to reject directories at parse time. Defensible, but the defect is in the shared helper and fixing it at one CLI leaves the other callers exposed; E-02 fixes the gateway instead.

## Scope check

- Over-scope: `git_commit_helper.py` is in scope ONLY for the directory-argument behavior (E-02) and the shortfall report (E-03). Do not alter `_staged_paths`' rename parsing, the index snapshot, or the locking.
- Under-scope: if E-02 chooses EXPANSION, verify no caller currently relies on a directory argument being a silent no-op before changing it; if any does, report that rather than breaking it.

## Required tests / validation

- `python3 -m pytest` bare, per the execution contract, with the actual summary line pasted.
- Targeted: `tests/test_git_commit_helper.py`.
- E-04's new test must be demonstrated FAILING against pre-E-02 code and passing after; given F-5, a test that never failed proves nothing here.
- The four gateway callers (`aw set`, `aw rename`, `aw commit`, the runners) must keep their current behavior for explicit-file arguments, proved by their existing tests staying green.

## Spec / documentation sync

- `offer_commit`'s docstring should state what a directory argument does once E-02 decides it, since the current silence is what made F-1 invisible.
- No `.spec.md` edit is anticipated. If E-02's refusal changes a documented CLI contract for `aw commit`, declare the spec file in `- Scope-Paths:` before editing it, per the spec-amendment rule.

## Open questions

### OQ-01: Should a directory argument be refused, or expanded to its files?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-02 must implement one of the two and either closes F-1, so the plan terminates correctly either way. REFUSING is smaller, is defensible for a safety-relevant primitive, and cannot surprise a caller by staging more than it named; it does break any caller that passes a directory today expecting a no-op, which E-02's scope check must confirm is nobody. EXPANDING matches obvious caller intent and would have made my own invocation correct, but it must respect `.gitignore` and must not become a force-add, so it carries more ways to be subtly wrong. Recommend REFUSING with the contained files named, because the failure this plan exists to prevent is silence, and a refusal is the loudest possible fix.

### OQ-02: Should `aw backlog set` relocate with `git mv` like `status_set` already does?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking and deliberately OUT of this plan's scope. `status_set` was converted on 2026-09-13 so a move is ONE staged rename "with no halves to pair up and no half to lose", while `aw backlog set` still writes-and-unlinks; that asymmetry is why an untracked destination reaches the gateway at all. Converting it would fix this plan's case at the writer, but the gateway fix is the one that protects writers nobody has converted yet, so the two are complementary rather than alternatives. Raised for the maintainer because it is a second writer change with its own test surface.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of both reproductions: the explicit-files call producing one `R<score>` record and an empty `git status --porcelain`, and the directory-argument call producing a deletion-only commit with the destination left staged.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the directory-argument invocation from F-1 re-run, pasted, showing either a refusal that NAMES the contained files or a commit containing BOTH halves; plus confirmation that no path outside those named was staged.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted outcome for a call naming a path that contributes nothing, showing the shortfall is reported; plus a case proving an unchanged-path shortfall is still a success.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the new test pasted FAILING against pre-E-02 code and PASSING after; the test's fixture shown to use an UNTRACKED destination and UNSTAGED source deletion; assertions on both an empty `git status --porcelain` and a both-halves commit; plus the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the paths named in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, naming destination FILES rather than directories (which is this plan's own subject), never `git add -A`, and never pushes. Test claims must paste actual runner output. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the plan moves to `.aw/records/plans/executed/`.
