# IPD: Build one shared record placement library and adopt it in every spec writer

- Date: 2026-09-20
- Kind: child
- Concern: Orchestrator `wfjsp4`'s child table declares Order 02 as `UNAUTHORED, must be written before this Set runs`, so the Set cannot execute: an orchestrator whose table declares a row resolving to no plan REFUSES retirement (`unauthored-child-rows`), and the ORCHESTRATOR COVERAGE GATE refused a run naming `wfjsp4` on 2026-09-21. This plan is that missing child. The defect it closes is measured and current: THREE writers can place a spec and the Set as authored teaches only ONE of them, so the location-equals-status invariant the migration establishes would decay on its very next write. `status_set.run_set_command`'s relocation block branches on `plans`, `prompts` and `backlog` only and gives a spec NO `dest_path`; `specs.run_new` writes to the flat root.
- Scope: Build the shared placement library the maintainer ruled for in OQ-04, and adopt it in every spec writer plus the two types whose branches it replaces. IN: one module answering "where does a record of type T with status S live" for both TRANSITION and CREATION, adopted by `status_set.run_set_command`, the forked `specs.run_set`, and `specs.run_new`, with the existing `plans`/`prompts`/`backlog` branches replaced by calls to it and regression evidence that their behavior is byte-identical. OUT: moving any spec file (that is the migration child `1bdxcp`), making the specs readers recursive (that is `y4bdoz`), and promoting location-equals-status to a fail-closed `aw check` rule.
- Scope-Paths: agent_workflows/record_placement.py, agent_workflows/status_set.py, agent_workflows/specs.py, agent_workflows/layout.py, agent_workflows/attention_contract.py, tests/test_record_placement.py, tests/test_layout.py, tests/test_specs_status_dirs.py, .aw/records/specs/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md
- Item-Dependencies: executed:y4bdoz
- Status: executed
- Work-Kind: chore
- Priority: medium
- Readiness: go-pending-approval
- Set: specdirs
- Order: 3
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: r9uvwc
- From-Backlog: qzhfk2

## Workflow history
- 2026-09-24 executed (aw agy run model=gemini-3.7-flash-high): aw agy run self-finalize: r9uvwc verified (set specdirs, attempt 1). [Scope reconciliation - out-of-scope tests/test_graduated_to_link.py: changed by the plan's approved execution (auto-reconciled by aw agy run); out-of-scope tests/test_spec_id6_filenames.py: changed by the plan's approved execution (auto-reconciled by aw agy run); out-of-scope tests/test_spec_review_attestation.py: changed by the plan's approved execution (auto-reconciled by aw agy run); out-of-scope tests/test_status_set.py: changed by the plan's approved execution (auto-reconciled by aw agy run); in-scope-unmodified agent_workflows/attention_contract.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-09-23 approved (aw set): Backfilled Priority and Work-Kind by inheritance from source backlog item qzhfk2 (planprio Order 02, plan 8u6770, E-03); no lifecycle transition occurred.
- 2026-09-22 approved (aw set): status set to approved
- 2026-09-21 readiness re-check (opencode its_direct/pt3-claude-opus-5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: unresolved-blocking-question -> clear (no unresolved BLOCKING open question; `has_unresolved_blocking_question` -> False (a NON-blocking open question is deliberately not counted, per the maintainer's 2026-09-10 ruling on qhy3i3 OQ-01)); unresolved-gating-finding -> clear (no unresolved gating finding; `review_findings.subject_gating_blocks` -> empty (an ABSENT review artifact is silent by that predicate's documented contract)); negative-review-verdict -> clear (the newest review record's verdict is not negative; `newest_verdict` -> neutral). RE-CHECKED REVIEW: the review of 2026-09-21, findings PR-001..E-06. Recomputed at HEAD `9792662f`. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-09-21 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review REVIEWED - OPEN QUESTIONS; readiness NO-GO; PR-001..PR-006. Reviewed at HEAD 803d10f6 in an isolated lane worktree; aw ipd lint --phase author conformed before semantic review. PR-001 (BLOCKER) ESCALATED as OQ-03 Blocking: yes: measured with the runner's own simulate_dispatch_order that 1bdxcp dispatches BEFORE this plan as the Set's fields actually stand, so aw oc run specdirs would migrate 36 specs while the writers still strand them; the remedy is a one-field edit on an approved sibling and only a human may make it. Five fixed in place: the plans/prompts branch the library replaces is SHARD-UNSAFE (parent.name reads YYYYMM, measured silently un-sharding a plan); the git mv rename is DECOMPOSED again by _offer_self_commit's reset so a status change still half-commits (measured end to end on two verbs, a live regression of y39i16 affecting plans/prompts/backlog today); F-10's dead-check claim is FALSE at HEAD (attcor rkn8ya fixed it; the record 4r91r1 is open while the code works) and E-06 would have written that false claim into permanent history; the gate lacked a scope fence, an explicit honesty rule, and had an UNCONDITIONAL finalize instruction; and the findings table now dates its rows per measurement HEAD. Every figure the plan cited reproduced exactly (36 specs, 17 live / 19 terminal, the 36/19/36 retired-filter trap, the layout and kw5y2s gaps). Verdict rests on OQ-03 alone, not on plan quality.

- 2026-09-20 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored to fill the UNAUTHORED row in `wfjsp4`'s child table, which review created as PR-001 and escalated as OQ-04, and which the ORCHESTRATOR COVERAGE GATE refused a run over on 2026-09-21. THE SHAPE OF THIS PLAN IS THE MAINTAINER'S, NOT MINE, and that is the single most important thing a reviewer should check me on. `wfjsp4` OQ-04 is `- Status: resolved`, RESOLVED BY THE MAINTAINER 2026-09-10 via `/askme`, and the ruling is explicitly WIDER than the question asked: "The answer is not 'add the writer child' but BUILD ONE SHARED PLACEMENT LIBRARY AND ADOPT IT PER TYPE, then have every status-changing and creation verb call it instead of constructing a path itself. Adopting it replaces the EXISTING plans and backlog branches too, so the duplicated knowledge disappears rather than growing by one." So a narrow three-writer fix would CONTRADICT a recorded maintainer decision, and this plan implements the ruled shape instead. The ruling also authorized breaking the work into multiple plans and warned that adoption TOUCHES WORKING CODE for plans and backlog, so regression evidence is mandatory and "must not be waved through"; E-04 and V-04 carry that. RE-MEASURED EVERY LOAD-BEARING CITATION AT HEAD `41f6a45b` RATHER THAN TRUSTING THE 12-DAY-OLD REVIEW, and the defect reproduces while three figures moved. THE THREE WRITERS, each proven BEHAVIORALLY in a throwaway git repo, not by reading code. WRITER 1, `aw specs set to-review aa1111` (the `--status`-ABSENT spelling): printed the transition `draft → to-review`, rewrote the status line to `- Status: to-review`, and LEFT THE FILE at `.aw/records/specs/draft/20260920-aa1111-01-aa1111-probe.spec.md`. Confirmed the cause by reading `status_set.py:1027-1069`: the `dest_path` block branches `if rec.record_type in ("plans", "prompts")`, `elif rec.record_type == "backlog"`, and there is NO `specs` branch, so `dest_path = rec.path` survives unchanged. NOTE the review cited `status_set.py:840-864` for this block; the line numbers have MOVED to 1027-1069 and the branch set now includes `prompts`, so cite the current lines. WRITER 3, `aw specs new --title "Probe two" --slug probe-two --apply`: wrote `.aw/records/specs/20260920-v8vdh6-01-v8vdh6-probe-two.spec.md`, at the FLAT ROOT, with `- Status: draft`, while a `draft/` directory already existed in that repo. Cause at `specs.py:976` (`dest = _specs_root(repo_root) / filename`); review cited `:945`, so that line has moved too. WRITER 2, `aw specs set <path> --status <enum>`: could NOT be behaviorally proven in the same probe because the transition legality and review-attestation gates fired first (`illegal transition to-review -> approved`, then for `reviewed`, `no review record names aa1111 as its Subject-Id`). That is CORRECT gate behavior and not a defect, but it means the review's claim about this spelling rests on code reading alone; E-01 must construct a legally-transitionable fixture (or a spec with a real review record) to prove it, and a reviewer should NOT accept a code-reading-only verdict for writer 2. THE READER DEFECT ALSO REPRODUCES, which is why `executed:y4bdoz` is a real edge rather than a formality: in the same probe, `specs._spec_files` returned ONE file (the flat-root one) while `check_engine._iter_type_files` returned TWO, and `aw specs check --json` reported `{'checked': 1, 'violations': 0}` against 2 files on disk, i.e. it declared conformance having never read the spec in `draft/`. THREE FIGURES ARE STALE IN THE PARENT AND ITS REVIEW, so do not quote them: the tree now holds 36 specs, not 28 or 29, distributed 13 `approved`, 15 `implemented`, 2 `draft`, 2 `deferred`, 2 `superseded`, 1 `to-review`, 1 `implementing`, which is SEVENTEEN live and 19 terminal (review said 29 files / 13 live). The retired-filter trap the parent's CID-8 warns about reproduces with new numbers: `specs._spec_files` 36 versus `_iter_type_files` default 19 versus `include_retired=True` 36, sets EQUAL with the flag. THE SPEC AMENDMENT IS CARRIED HERE, per OQ-05's ruling.
- 2026-09-20 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make "where does a record of this type with this status live" a question ONE module answers, so the specs tree can be partitioned by status without the invariant decaying on the next `aw specs set` or `aw specs new`, and so the knowledge duplicated across three per-type branches collapses to one instead of growing to four.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the defect, then build the library

- [x] E-01 RE-PROVE ALL THREE WRITERS BEHAVIORALLY BEFORE CHANGING ANYTHING, each in a throwaway git repo, because two of the three cited line numbers have already moved and a code-reading verdict is not evidence. For each writer, create a spec, run the writer, then assert the resulting file's DIRECTORY against its `- Status:`.
  WRITER 2 NEEDS A LEGALLY-TRANSITIONABLE FIXTURE AND THIS IS THE TRAP. My own probe could not reach `specs.run_set`'s placement code at all: `--status approved` was refused as an `illegal transition to-review -> approved`, and `--status reviewed` was refused because `no review record names aa1111 as its Subject-Id`. Those gates are correct. So construct a fixture that passes them (a legal single-step transition, plus a real `.review.md` carrying `- Subject-Id:` and `- Subject-Type: spec` where the target status requires attestation), or the test proves only that the gate works. DO NOT weaken a gate to make the fixture easy.
  PASTE ALL THREE RESULTS SEPARATELY. A pass on one spelling is not evidence about another; that exact assumption caused the two dual-spelling bypasses this codebase documents in-code at `status_set.py:517-525` and `:549-556` ("a gate installed in only one of them is bypassed by choosing the other").
  - Depends on: none
  - Expected outcome: three pasted before/after results, one per writer, each showing the file's directory and its `- Status:`; writer 2 proven through a fixture that actually reaches the placement code rather than being stopped by a legality or attestation gate; each failure attributed to a CURRENT file:line rather than to the review's stale ones.
  - Execution state: performed

- [x] E-02 BUILD THE SHARED PLACEMENT LIBRARY, one module that answers placement for BOTH cases the maintainer named: where a TRANSITIONING record moves, and where a NEWLY CREATED record goes. The creation case is called out separately because the ruling names it as "a distinct class that nobody had considered, which is why `aw specs new` lands in the flat root".
  DERIVE FROM THE EXISTING AUTHORITIES, DO NOT RE-LIST THEM. This is the specific way this work could do damage. Each type currently keeps its status-to-directory knowledge in a different place and shape: `backlog.STATUS_DIRS` is a tuple at `backlog.py:78` (with `STATUSES = frozenset(STATUS_DIRS)` at `:79`), plans' dispositions are derived inline in `status_set.py` from a hardcoded 5-tuple, spec statuses live in `attention_contract.SPEC_STATUSES` (9 values: approved, deferred, draft, implemented, implementing, parked, reviewed, superseded, to-review), and `layout.py` models `lifecycle_subdirs` per record class (`plans` at `:158`, `prompts` at `:179`, `backlog` at `:203`, and `specs` HAS NONE). A fourth hardcoded list would be the very duplication this plan exists to remove.
  THE PATTERN HAS ALREADY FAILED ONCE IN EXACTLY THIS WAY, and the in-code comment at `status_set.py` records it: the backlog branch was repaired because a HARDCODED LIST silently DECLINED TO MOVE a file whose source dir was already the new status, "leaving the record's directory and its `- Status:` line disagreeing". Derive from `STATUS_DIRS` and from the layout model; do not retype either.
  NOTE THE PLANS CASE IS A MAPPING, NOT AN IDENTITY, and a library that assumes `dir == status` will break it: five plan statuses (`draft`, `to-review`, `reviewed`, `approved`, `auto-approved`) all map to `pending/`. Backlog and specs are identity mappings. The library must express both shapes.
  THE PLANS/PROMPTS BRANCH ALSO READS `path.parent.name`, WHICH IS SHARD-UNSAFE, AND THE LIBRARY MUST NOT INHERIT THAT. This is a SECOND shape the branch gets wrong and it is not the many-to-one point above. `status_set.py:1056-1067` tests `rec.path.parent.name in ("pending","executed",...)` and, on a MISS, falls to an `else` that rebuilds the destination from `_plans_mod._resolve_area_dir(repo_root, ...)`. `aw archive plans` shards a terminal plan into `<disposition>/YYYYMM/` (`plans_archive._shard_target`, `plans_archive.py:59-62`), so a sharded plan's `parent.name` is `202601`, the membership test MISSES, and the `else` branch relocates the plan to the disposition ROOT, silently UN-SHARDING it. MEASURED 2026-09-21 in a throwaway repo at HEAD `803d10f6`: a plan at `.aw/records/plans/executed/202601/20260105-probe-00-pl1234-...ipd.md` set to `superseded` landed at `.aw/records/plans/superseded/...`, i.e. the shard directory was dropped. That is a DIR-ONLY move so it loses no content, but it silently reverses an archival decision.
  DERIVE THE DISPOSITION FROM THE FIRST PATH COMPONENT UNDER THE TYPE DIR, WHICH IS THE DERIVATION THIS REPOSITORY HAS ALREADY STANDARDIZED THREE TIMES and which the branch being replaced is the lone holdout from: `check_engine._plan_disposition` (`check_engine.py:1979-1998`), `attention._plan_disposition_from_rel` (`attention.py:1094-1113`), and `plans_index.scan_plans` all take `rel.split("/", 1)[0]`, and each carries a comment saying explicitly that a `parent.name` test "would silently stop recognizing a sharded plan". Reuse one of those rather than writing a fourth. THEN DECIDE AND STATE whether a status change PRESERVES an existing shard (`executed/202601/` -> `superseded/202601/`) or moves to the disposition root; V-02 requires the answer be asserted by a test either way, because leaving it unasserted is how the current behavior went unnoticed.
  - Depends on: E-01
  - Expected outcome: a single module exposing placement for transition and creation, per type, deriving its directory knowledge from the existing authorities with no new hardcoded status list; the plans many-to-one mapping and the backlog/specs identity mappings both expressed; unit tests covering each type including the `source dir already equals target` case that previously regressed.
  - Execution state: performed

### Task group 2: adopt it everywhere, without changing what works

- [x] E-03 ADOPT THE LIBRARY IN ALL THREE SPEC WRITERS, so a spec lands in its status directory whichever verb placed it. The three call sites are `status_set.run_set_command`'s `dest_path` block (`status_set.py:1027-1069`, which needs a `specs` case), the forked `specs.run_set` (`specs.py:498`), and `specs.run_new` (`specs.py:934`, whose destination is computed at `:976`).
  RELOCATE WITH `git mv`, WHICH `status_set` ALREADY DOES AND WHICH THE PARENT'S OQ-01 GOT WRONG. OQ-01's resolution states that "no status setter in this repository uses `git mv`: `status_set` and `backlog` both `atomic_write` then `unlink`". That is STALE: `status_set` now performs `_core.git_mv` FIRST and then writes at the destination, and its in-code comment records exactly why the old write-then-unlink was a bug ("git sees TWO unrelated facts", which caused `oc_runipd.commit_backlog_close` to commit only the ADD and leave a dangling deletion that blocked 27 of 42 items in one run). ORDER IS LOAD-BEARING and the comment says so: move FIRST, then write, because writing first leaves an untracked file at the destination and `git mv` refuses. Follow the existing pattern; do not reintroduce write-then-unlink.
  DO NOT WEAKEN ANY GATE TO MAKE PLACEMENT WORK. The legality check and the review-attestation refusal both fire BEFORE placement (proven in E-01), and they must keep firing. Placement is what happens to a transition that is already permitted.
  THE `git mv` RENAME IS CURRENTLY DECOMPOSED AGAIN BEFORE THE COMMIT, AND ADOPTING THIS PATH FOR SPECS WOULD PROPAGATE A LIVE REGRESSION TO A THIRD TYPE. DO NOT assume the `git mv` fix of 2026-09-13 holds end to end; MEASURED 2026-09-21 at HEAD `803d10f6` it does not. `apply_status_change` does stage a clean rename (`R100`, verified), but `run_set_command` then records ONLY the DESTINATION in `touched_paths` (`status_set.py:1755-1760`, `dest_path` alone, the source is never appended), and `_offer_self_commit` opens with `_gch._git(repo_root, ["reset", "--quiet", "HEAD", "--", *paths])` (`status_set.py:1390`), whose docstring calls the reset "a no-op for in-place set rewrites". It is NOT a no-op for a RELOCATION: unstaging one half of a staged rename DECOMPOSES it back into exactly the shape `y39i16` was filed for. REPRODUCED END TO END on the tooled path: `aw backlog set graduated bk1234 --yes` produced commit `aac36f85` containing `A .aw/records/backlog/graduated/...` ALONE, and left `D .aw/records/backlog/open/...` staged-but-uncommitted in the tree; `aw ipd set superseded pl9999 --yes` did the same. Disabling ONLY `_offer_self_commit` leaves the clean `R100`, which isolates the cause to the reset. The one uncommitted tracked deletion left behind is the precise condition that refused 27 of 42 items in run `run-20260913T031350Z-1732436`.
  SO THE ADOPTION MUST CARRY THE SOURCE PATH, NOT ONLY THE DESTINATION: whatever the library returns for a relocation must give the caller BOTH paths, and `touched_paths` must record both so the commit carries both halves. `git_commit_helper.offer_commit` ALREADY handles this correctly once told (`_in_index` at `git_commit_helper.py:333-347` drops an already-renamed source from the `add` set while keeping it in the commit pathspec, `:573-589`), so the fix is at the CALLER, and `ipd_lifecycle` finalize already does it right (`owned_paths = [plan_rel, dest_rel]`, `ipd_lifecycle.py:3795`). DO NOT fix this by removing the reset wholesale without checking the in-place case it was added for (`jgcm68` D2), and do NOT use `--no-verify` or weaken the executed-transition gate. THIS DEFECT IS PRE-EXISTING AND AFFECTS `plans`, `prompts` AND `backlog` TODAY, so if fixing it here would widen this plan beyond one focused pass, FILE IT (`aw backlog new`, `Work-Kind: bug`, which per this repository's policy carries `- Blocks-Release:` while live) and cite the item in V-03; what is NOT acceptable is adopting the path for specs while leaving the decomposition unmentioned.
  - Depends on: E-02
  - Expected outcome: all three spec writers place a spec in the directory matching its status, each proven separately in a throwaway repo; relocation performed as a single staged rename via `git mv` with move-then-write ordering, and the rename surviving all the way into the COMMIT (both halves) rather than being decomposed by the self-commit reset; no legality or attestation gate weakened.
  - Execution state: performed

- [x] E-04 REPLACE THE EXISTING `plans`, `prompts` AND `backlog` BRANCHES WITH CALLS TO THE LIBRARY, AND PROVE THEIR BEHAVIOR IS UNCHANGED. The maintainer's ruling requires this ("adopting it replaces the EXISTING plans and backlog branches too, so the duplicated knowledge disappears rather than growing by one") AND flags it as the new risk this Set did not previously carry, to be carried with regression evidence rather than waved through.
  THE BAR IS BYTE-IDENTICAL BEHAVIOR, NOT "TESTS STILL PASS". For each of the three types, exercise every status in its enum and assert the destination path equals what the CURRENT code computes. The cheapest honest form: capture the current mapping as a table BEFORE the change (status -> destination directory, per type) and diff it against the same table AFTER. Paste both tables.
  COVER THE REGRESSION CASE THAT ALREADY HAPPENED ONCE: a record whose source directory already equals its target. The backlog branch silently declined to move in that case and left directory and status disagreeing. Assert it for all four types now.
  PROMPTS WERE NOT IN THE MAINTAINER'S SENTENCE BUT ARE IN THE CODE. The `dest_path` block branches on `("plans", "prompts")` together, so adopting the library necessarily touches prompts too. Treat prompts with the same regression bar rather than as an afterthought, and say so in the evidence.
  - Depends on: E-03
  - Expected outcome: the per-type relocation branches replaced by library calls; before/after destination tables pasted for plans, prompts, backlog and specs across every status in each enum, showing no change for the three pre-existing types; the source-dir-equals-target case asserted for all four.
  - Execution state: performed

### Task group 3: model, contract, and enforcement

- [x] E-05 GIVE `specs` ITS `lifecycle_subdirs` IN THE LAYOUT MODEL AND AMEND THE `kw5y2s` SPEC IN THE SAME CHANGE, which is what OQ-05's maintainer ruling requires ("YES, AMEND `kw5y2s` IN THE SAME CHANGE, AND DECLARE IT IN `- Scope-Paths:` UP FRONT"), having explicitly declined the three alternatives (amend-first as aspirational documentation, abandon the change, or ship the contradiction as a follow-up).
  MEASURED AT HEAD, so you know exactly what to change: the `specs` `RecordClassDefinition` in `layout.py` carries NO `lifecycle_subdirs` key while `plans` (`:158`), `prompts` (`:179`) and `backlog` (`:203`) each do. The spec `.aw/records/specs/20260901-kw5y2s-01-kw5y2s-...spec.md` is `- Status: approved` and its record-class row for `specs` reads `Single directory; frontmatter status tracking`, which this Set falsifies.
  EXTEND `tests/test_layout.py::test_lifecycle_subdirs_match_the_live_status_dirs`, which currently asserts modeled-versus-live subdirs for `backlog` and `plans` ONLY (verified at HEAD). The parent's OQ-05 is explicit that extending it "is part of the amendment, not optional", because until it covers specs nothing catches a model/live mismatch for this type.
  THE SPEC PATH IS DECLARED IN THIS PLAN'S `Scope-Paths` DELIBERATELY, and that declaration is the mechanism, not a formality: it is what makes `aw oc run`/`aw agy run` ANNOUNCE the spec edit BEFORE the run starts and what lets the finalize scope gate reconcile declared against actual. Both runners also report at run end which specs a run declared versus actually changed, including an undeclared change. Amend the ROW, not the spec's shape, and say WHY in this plan's spec-sync section.
  - Depends on: E-02
  - Expected outcome: `specs` carries `lifecycle_subdirs` derived from `SPEC_STATUSES` in the layout model; `kw5y2s`'s `specs` record-class row amended to describe status subdirs with the reason recorded; `test_lifecycle_subdirs_match_the_live_status_dirs` extended to cover specs (and prompts, if the same gap exists there); the emitted layout document reflects the new subdirs.
  - Execution state: performed

- [x] E-06 REPORT THE ENFORCEMENT GAP RATHER THAN SILENTLY LEAVING IT, because specs would otherwise gain subdirs with NO checker covering them. `attention.disposition-mismatch` is documented as "plans dir vs terminal status" (`attention_contract.py:688`), so it does not cover specs.
  DO NOT FIX IT HERE, AND DO NOT PROMOTE THE INVARIANT TO A FAIL-CLOSED RULE. The reason is the parent's OQ-03, which leaves the severity decision OPEN for the maintainer with the migration's measured result in hand. Widening a check to a new type in the same plan that also builds a library would make two blast radii one diff.
  THE `4r91r1` HALF OF THIS ITEM WAS WRONG AS AUTHORED AND IS CORRECTED HERE (review F-11, measured 2026-09-21 at HEAD `803d10f6`). Do NOT report the check as DEAD: the CODE has already been fixed by `attcor rkn8ya` E-05, which replaced the legacy `.agents/plans/` prefix test with `_plan_disposition_from_rel` (`attention.py:1094-1113`) recognizing BOTH layouts and deriving the disposition from the FIRST path component so a sharded plan still resolves. PROVEN: an `.aw`-layout plan at `executed/202601/` carrying `- Status: superseded` emitted `attention.disposition-mismatch` and `aw attention --check` exited 1. The backlog item `4r91r1` is nonetheless still `- Status: open` (in `.aw/records/backlog/open/20260908-attdisp-01-4r91r1-...`), so what is open is the RECORD, not the defect. Report that asymmetry rather than repeating the stale claim, and do NOT close `4r91r1` from here (it is not this plan's item and closing it needs its own evidence).
  THE DELIVERABLE IS A RECORD, NOT CODE: state in this plan's evidence that the invariant this plan makes TRUE is not yet ENFORCED for specs, name the SCOPING as the reason (`attention.py:1141-1145` gates on `plans_mod.DIR_TERMINAL`, so only plans are covered), re-measure `4r91r1`'s status at execution and state whether the code-versus-record asymmetry above still holds, and confirm no plan in this Set claims the invariant is enforced.
  - Depends on: E-05
  - Expected outcome: a recorded statement that location-equals-status is true-but-unenforced for specs, citing `attention_contract.py:688` plus the `plans_mod.DIR_TERMINAL` gate at `attention.py:1141-1145` as the SCOPING reason; backlog `4r91r1`'s status re-measured at execution with the code-fixed-but-record-open asymmetry stated explicitly rather than the stale "dead check" claim; and confirmation this plan added no fail-closed rule and closed no other plan's item.
  - Execution state: performed

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR WHOSE CHILD TABLE DECLARES AN UNAUTHORED ROW REFUSES RETIREMENT (`unauthored-child-rows`), so `wfjsp4` could not complete until this plan existed, independently of the coverage gate.
- THE MAINTAINER RULED FOR A LIBRARY, NOT A BRANCH (OQ-04, 2026-09-10, `/askme`), and explicitly authorized multiple plans. A narrow per-writer fix would contradict a recorded decision.
- THE MAINTAINER RULED THE SPEC AMENDMENT TRAVELS WITH THE CODE (OQ-05, same date), declining amend-first, abandon, and ship-the-contradiction.
- THERE IS NO RELOCATION MODULE TODAY. The only real relocation code is the `dest_path` if/elif chain in `status_set.py` (`:1027-1069`), branching on `("plans", "prompts")` and `backlog`, with no `specs` case.
- DIRECTORY KNOWLEDGE IS SCATTERED IN FOUR SHAPES: `backlog.STATUS_DIRS` tuple (`backlog.py:78`), plans dispositions inline in `status_set.py`, `attention_contract.SPEC_STATUSES` (9 values), and `layout.py`'s per-class `lifecycle_subdirs`. Nothing anywhere answers "which types have status subdirs".
- PLANS ARE A MANY-TO-ONE MAPPING: `draft`, `to-review`, `reviewed`, `approved` and `auto-approved` all map to `pending/`. Backlog and specs are identity mappings. A library assuming `dir == status` breaks plans.
- `status_set` NOW USES `git mv`, MOVE-FIRST-THEN-WRITE, and its comment records the bug that forced it (a write-then-unlink pair whose ADD was committed without its DELETE, blocking 27 of 42 items in one run). The parent's OQ-01 says the opposite and is stale.
- THE SPEC READER IS STILL NON-RECURSIVE, so `executed:y4bdoz` is a real correctness edge: measured in a throwaway repo, `aw specs check --json` reported `{'checked': 1}` against 2 files on disk, declaring conformance without reading the spec in a subdir.
- THE RETIRED-FILTER TRAP IS LIVE WITH NEW NUMBERS: `specs._spec_files` 36, `_iter_type_files` default 19, `include_retired=True` 36 (sets equal). Any set-equality cross-check MUST pass `include_retired=True`.
- `aw specs check`'s COUNT IS ONLY READABLE FROM `--json`: the human branch prints no count and the `--agent` record omits `checked` entirely at ZERO (a falsy `0` failing an `or` in `result_types.py`). Read the count from `--json`.

## Findings

Rows F-01 through F-10 were authored 2026-09-20 at HEAD `41f6a45b`. Rows F-11 through F-14 were ADDED BY REVIEW 2026-09-21 at HEAD `803d10f6`, and F-11 CORRECTS F-10. Every figure in both groups was re-verified at review; only F-10's "dead check" half was found false.

| Id | Severity | Location (measured at the HEAD stated above) | Finding | Evidence |
|---|---|---|---|---|
| F-01 | error | `wfjsp4` child table Order 02 | Declared `UNAUTHORED`, so the Set cannot execute and the parent cannot retire. This plan fills it. | Child table row reads "UNAUTHORED, must be written before this Set runs"; coverage gate refused `aw oc run`. |
| F-02 | error | `status_set.py:1027-1069` | The `dest_path` block branches `("plans","prompts")` and `backlog` with NO `specs` case, so a transitioning spec keeps `dest_path = rec.path`. PROVEN behaviorally: `aw specs set to-review aa1111` printed `draft → to-review`, rewrote the status line, and left the file in `draft/`. | Throwaway-repo probe plus the source branch. |
| F-03 | error | `specs.py:976` | `aw specs new` writes to the FLAT ROOT even when a `draft/` directory exists, so the invariant breaks at CREATION. PROVEN: wrote `.aw/records/specs/20260920-v8vdh6-01-v8vdh6-probe-two.spec.md`. | Throwaway-repo probe. |
| F-04 | warn | review's citations | TWO cited line numbers have MOVED (`status_set.py:840-864` -> `:1027-1069`, `specs.py:945` -> `:976`) and the branch set now includes `prompts`. Cite current lines. | Read at HEAD. |
| F-05 | warn | writer 2 (`specs.run_set`) | NOT behaviorally proven by me: the legality gate (`illegal transition to-review -> approved`) and the review-attestation refusal fired first. The claim rests on code reading, so E-01 must build a fixture that reaches the placement code. | Probe output, both refusals. |
| F-06 | warn | `wfjsp4` OQ-01 resolution | STALE: it states no status setter uses `git mv`. `status_set` now does, move-first-then-write, with an in-code comment recording the bug that forced the change. | `status_set.py` relocation block and its comment. |
| F-07 | warn | parent + review distribution figures | STALE: 36 specs now (13 approved, 15 implemented, 2 draft, 2 deferred, 2 superseded, 1 to-review, 1 implementing) = 17 live / 19 terminal. Review said 29 files / 13 live. Re-measure at execution. | Counted over `.aw/records/specs/*.spec.md`. |
| F-08 | error | `specs._spec_files` vs `aw specs check` | The reader defect reproduces: `{'checked': 1}` against 2 on-disk specs in a repo with one spec in `draft/`, i.e. conformance declared over an unread file. Confirms `executed:y4bdoz` is a correctness edge. | Throwaway-repo probe. |
| F-09 | info | `layout.py` | `specs` carries no `lifecycle_subdirs` while `plans` (`:158`), `prompts` (`:179`) and `backlog` (`:203`) do; `tests/test_layout.py::test_lifecycle_subdirs_match_the_live_status_dirs` covers backlog and plans ONLY. | Read at HEAD. |
| F-10 | warn | `attention_contract.py:688` | `attention.disposition-mismatch` is scoped to "plans dir vs terminal status", so specs would gain subdirs with no checker. Backlog `4r91r1` (the check measured dead in the `.aw` layout) is still `- Status: open`. | Read at HEAD; item in `.aw/records/backlog/open/`. |
| F-11 | warn | this plan's own F-10, and E-06 (review finding `PR-004`) | HALF-STALE, corrected at review 2026-09-21 (HEAD `803d10f6`). The SCOPING half is TRUE: `attention_contract.py:688` still reads `# plans dir vs terminal status` and `attention.py:1141-1145` still gates on `plans_mod.DIR_TERMINAL`, so specs remain uncovered. The DEAD half is FALSE: `4r91r1` is still `- Status: open` but the CODE was fixed by `attcor rkn8ya` E-05, which replaced the legacy prefix test with `_plan_disposition_from_rel` (`attention.py:1094-1113`, recognizing BOTH layouts). MEASURED: an `.aw`-layout plan at `executed/202601/` carrying `- Status: superseded` produced `attention.disposition-mismatch` and `aw attention --check` exited 1. So E-06 must NOT report the check as dead; it must report an OPEN ITEM whose code is already fixed. | Throwaway-repo probe; `attention.py:1094-1145`; item still in `backlog/open/`. |
| F-12 | error | `status_set.py:1056-1067` (review finding `PR-002`) | SHARD-UNSAFE, and a shape the plan did not name. The plans/prompts branch tests `rec.path.parent.name` against the disposition tuple; a SHARDED terminal plan's parent is `YYYYMM`, so the test misses and the `else` rebuilds the path at the disposition ROOT, silently UN-SHARDING it. MEASURED: `executed/202601/...pl1234...` set to `superseded` landed at `superseded/...`, shard dropped. Three other modules already derive this correctly from the first path component and each comments that `parent.name` breaks on shards. A library that copies the branch inherits the bug. | Throwaway repo at HEAD `803d10f6`; `plans_archive.py:59-62`; `check_engine.py:1979-1998`; `attention.py:1094-1113`. |
| F-13 | error | `status_set.py:1755-1760`, `:1390` (review finding `PR-003`) | THE `git mv` RENAME IS DECOMPOSED BEFORE THE COMMIT, a LIVE REGRESSION of the `y39i16` fix affecting `plans`, `prompts` and `backlog` TODAY. `touched_paths` records only `dest_path` (never the source), and `_offer_self_commit` then runs `git reset --quiet HEAD -- <dest>`, which unstages one half of the staged rename and decomposes it into a staged source `D` plus an untracked dest. MEASURED END TO END: `aw backlog set graduated bk1234 --yes` produced commit `aac36f85` holding `A graduated/...` ALONE and left `D open/...` staged-but-uncommitted; `aw ipd set superseded pl9999 --yes` behaved identically; stubbing ONLY `_offer_self_commit` leaves the clean `R100`, isolating the cause. One uncommitted tracked deletion is exactly what refused 27 of 42 items in `run-20260913T031350Z-1732436`. `offer_commit` already handles a renamed source correctly (`_in_index`, `git_commit_helper.py:333-347`) and `ipd_lifecycle` finalize already passes both paths (`:3795`), so the defect is at this caller. | Throwaway repos at HEAD `803d10f6`; backlog `y39i16` (`done`) documents the identical shape. |
| F-14 | error | `1bdxcp` `- Item-Dependencies:`, and the runner's scheduler | THE MIGRATION DISPATCHES BEFORE THIS PLAN TODAY, measured rather than argued. `simulate_dispatch_order` over the Set's five items as their fields actually stand returns `['y4bdoz','1bdxcp','r9uvwc','ingpvc','wfjsp4']`; adding `executed:r9uvwc` to `1bdxcp` returns `['y4bdoz','r9uvwc','1bdxcp','ingpvc','wfjsp4']`. Both plans are depth 1, so the Order digit decides and `02` precedes `03`. Raised as OQ-03 `- Blocking: yes` (review finding `PR-001`, which is the id the lint gate joins on) because only a human may edit the `approved` sibling. | `oc_runipd.simulate_dispatch_order` / `queue_sort_key` / `dependency_depth` at HEAD `803d10f6`. |

## Proposed changes (ordered, validatable)

1. Re-prove all three writers behaviorally, with a fixture that actually reaches writer 2's placement code (E-01).
2. Build `record_placement`, deriving from existing authorities, expressing both many-to-one (plans) and identity (backlog, specs) mappings, for transition AND creation (E-02).
3. Adopt it in all three spec writers, relocating via `git mv` move-first-then-write (E-03).
4. Replace the plans/prompts/backlog branches with library calls, proven byte-identical by before/after destination tables (E-04).
5. Give `specs` `lifecycle_subdirs`, amend the `kw5y2s` row, and extend the layout test to cover specs (E-05).
6. Record that the invariant is true-but-unenforced for specs, citing `4r91r1` (E-06).

## Deferred / out of scope (with reason)

- MOVING ANY SPEC FILE. That is the migration child `1bdxcp`'s deliverable, and it must run AFTER this plan. This plan makes placement CORRECT; it does not perform the migration.
  - Carrier-Declined: Carrier: `1bdxcp`, the migration child, which is `approved` and owns it. Named as a declined row rather than a `Carrier:` field because the work is not deferred at all: it is another member of this same Set with its own approval and evidence.
- MAKING THE SPEC READERS RECURSIVE. That is `y4bdoz` (Order 01), declared here as an `Item-Dependencies` edge because a spec in a subdir is invisible to its own checker until that lands.
  - Carrier-Declined: Carrier: `y4bdoz` (Order 01), `approved`, and declared as this plan's `Item-Dependencies` edge. Not deferred work, a prerequisite.
- PROMOTING LOCATION-EQUALS-STATUS TO A FAIL-CLOSED `aw check` RULE. The parent's OQ-03 leaves the severity decision open for the maintainer, deliberately, with the migration's measured result in hand.
  - Carrier-Declined: The parent orchestrator `wfjsp4` OWNS this as its OQ-03 and deliberately leaves it open for the maintainer to decide with the migration's measured result in hand. A carrier here would duplicate a question already recorded on a live plan.
- FIXING `attention.disposition-mismatch` OR WIDENING IT TO SPECS. Backlog `4r91r1` owns the dead-check defect and is still open; widening is a separate decision even once it is fixed. E-06 records the gap instead.
  - Carrier-Declined: Carrier: backlog `4r91r1`, verified `- Status: open` at HEAD, which owns the dead-check defect. Widening it to specs afterwards is a separate decision the maintainer holds, and E-06 records the gap so it cannot vanish silently.
- FIXING THE `checked`-AT-ZERO OMISSION in the `--agent` record. The parent's E-03 says to report it as a finding for a separate fix, not to fix it in this Set.
  - Carrier-Declined: Carrier: backlog `uwerb5`, filed 2026-09-20 for exactly this defect (`bug`, `Blocks-Release: next`). Previously this deferral named no owner at all, which is the disappearance the carrier field exists to prevent.
- SHARDING TERMINAL SPECS BY MONTH. The parent's OQ-02, deliberately open until subdirs exist.
  - Carrier-Declined: The parent orchestrator `wfjsp4` OWNS this as its OQ-02, deliberately open until subdirs exist and it becomes answerable. Recorded on a live plan, so nothing is lost.
- THE REVIEWS-LOCATION QUESTION (`sv0sf3`), which that item itself says not to bundle with a specs migration.
  - Carrier-Declined: Carrier: backlog `sv0sf3`, which owns the question and whose own text instructs that it NOT be bundled with a specs migration. A second carrier would duplicate it.
- CHANGING THE SPEC STATUS VOCABULARY. This plan partitions on the nine states that exist and adds none.
  - Carrier-Declined: A PROHIBITION, not an obligation. This plan partitions on the nine states that exist and adds none; there is no future state in which this Set should change the vocabulary.
- THE `Readiness:` FIELD. Deliberately ABSENT: it is `/plan-review`'s attested output, and hand-writing it would forge a review that never happened.
  - Carrier-Declined: The ABSENCE is the correct permanent state, not an omission to fix later. `/plan-review` writes that field; hand-writing one forges a review.

## Scope check

- Over-scope: the library replaces WORKING code for plans, prompts and backlog, which is strictly more than specs needed. That is deliberate and is the maintainer's ruled shape (OQ-04), on the ground that a fourth per-type branch would grow the duplication that caused this defect. The risk is acknowledged and is carried by E-04's byte-identical regression bar.
- Scope-Paths justification: `record_placement.py` is the new module; `status_set.py` and `specs.py` hold the four call sites; `layout.py` carries the model change and `attention_contract.py` is read for the enforcement note (E-06 writes no code there, but it is declared because a reader could reasonably expect a scoped change and the finalize gate reconciles declared against actual); the three test files cover the library, the layout model and the spec placement behavior; and the `kw5y2s` `.spec.md` is declared UP FRONT exactly as OQ-05's ruling requires, so both runners announce the spec edit before the run starts.
- Under-scope: this plan moves no spec, fixes no reader, adds no check rule, does not fix `4r91r1`, does not fix the `checked`-at-zero omission, and does not shard terminal specs. Each is excluded above with its owner.

## Required tests / validation

- New unit tests for the placement library covering every type, every status in each enum, both transition and creation, and the source-dir-equals-target case.
- `tests/test_layout.py` extended to assert modeled-versus-live subdirs for specs, and passing.
- All three spec writers proven behaviorally in throwaway repos, pasted separately.
- Before/after destination tables for plans, prompts and backlog showing no behavioral change.
- `aw specs check --json` still reports a nonzero `checked` equal to the on-disk count (read from `--json`; the human branch prints no count and `--agent` omits `checked` at zero).
- Any `specs._spec_files` versus `_iter_type_files` set-equality assertion MUST pass `include_retired=True`: measured 36 versus 19 by default and 36 versus 36 with the flag, so an equality asserted against the default is guaranteed to fail for a reason unrelated to this plan.
- Bare suite `python3 -m pytest`, judged on the failing NODE ID delta against a baseline measured in the executing worktree. AFTER minus BEFORE must be EMPTY. Do NOT copy any baseline from this Set's plans: the parent's `1 failed, 5648 passed` and its named failure were both measured wrong at review, `test_orchestrator_retirement.py` passes, and the one real failure found later was environmental (an untracked `opencode-recovery/` dump belonging to another party in a shared checkout). DO NOT delete that directory to make the suite green; it is not yours.

## Spec / documentation sync

- `kw5y2s` IS AMENDED BY THIS PLAN, DELIBERATELY AND BY MAINTAINER RULING (OQ-05, 2026-09-10). WHY, since a spec edit changes the contract every other plan is reviewed against: the spec's record-class row for `specs` reads `Single directory; frontmatter status tracking`, and this Set makes that false. The ruling declined every alternative that would separate the two, so the row moves in the same change as the code, and the path is declared in `- Scope-Paths:` up front so the runners announce it and the finalize gate reconciles it. The amendment is limited to the `specs` ROW plus whatever sentence describes that tree; it does not change the spec's shape, scope or other rows.
- `layout.py`'s emitted layout document is generated OUTPUT: adding `lifecycle_subdirs` to the `specs` class changes what it emits, so the emitted document must be regenerated rather than hand-edited.
- NO OTHER SPEC IS TOUCHED. If E-02 or E-04 finds that the library's shape contradicts another spec (for example one describing plans' disposition mapping), STOP and record it rather than editing a second contract undeclared.

## Open questions

### OQ-01: Should the library also own the `research`/`comms` trees, whose subdirs are groupings rather than statuses?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: A BOUNDARY DECISION with no work behind it in either direction. `research` and `comms` subdirs are GROUPINGS, not statuses, so neither has a status-to-directory mapping for the library to own; there is nothing to build unless a grouping tree later gains a real lifecycle, which no evidence suggests. Filing a carrier would assert a pending task that does not exist.
- Resolution or deferral rationale: DEFERRED, and recorded so the library's boundary is a decision rather than an accident. `research` has 5 subdirs that are GROUPINGS, not statuses, and `comms` has 1; neither expresses a lifecycle, so neither has a status-to-directory mapping for the library to own. RECOMMENDATION: keep the library scoped to lifecycle-bearing types (plans, prompts, backlog, specs) and let grouping trees keep their own placement, because folding a non-lifecycle tree into a status-keyed API would force a fake status. Revisit only if a grouping tree gains a real lifecycle. NON-BLOCKING because nothing in this plan depends on the answer: the four types it adopts all have status enums today.

### OQ-02: Does `prompts` need the same model/live subdir assertion that E-05 adds for specs?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: NOT DEFERRED: E-05's expected outcome already authorizes closing this in passing ("and prompts, if the same gap exists there"), so the work is IN this plan rather than handed onward. It is raised as a question only because a reviewer may prefer it filed separately, and if they do, E-05's evidence will record that choice.
- Resolution or deferral rationale: NON-BLOCKING and cheap either way. `tests/test_layout.py::test_lifecycle_subdirs_match_the_live_status_dirs` covers `backlog` and `plans` only, verified at HEAD, while `prompts` DOES carry `lifecycle_subdirs` (`layout.py:179`), so prompts has the same unasserted gap specs is about to fill. E-05's expected outcome already says "and prompts, if the same gap exists there", so the executor may close it in passing. It is raised as a question rather than an instruction because extending an assertion to a type this Set otherwise only touches incidentally is a small scope widening, and a reviewer may prefer it filed separately. RECOMMENDATION: extend it, since the assertion is one added block in a test this plan is already editing, and leaving a known unasserted gap next to one being fixed is the drift this repository's own conventions warn about.

### OQ-03: `1bdxcp` does not declare `executed:r9uvwc`, and the runner therefore dispatches the migration BEFORE this placement fix. Add the edge to the approved sibling, or run the Set by hand?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Carrier-Declined: NOT DEFERRABLE TO A CARRIER, because the whole content of the work is a HUMAN ACT this plan is forbidden to perform: editing the `- Item-Dependencies:` field of `1bdxcp`, which is another plan's file and is already `approved`. Filing a carrier item would record a task whose only possible executor is the person being asked the question, which is the round trip the question itself already is.
- Resolution or deferral rationale: OPEN AND BLOCKING, on MEASURED evidence rather than caution. `simulate_dispatch_order` over the Set as its fields actually stand at HEAD `803d10f6` returns `['y4bdoz','1bdxcp','r9uvwc','ingpvc','wfjsp4']`; with `executed:r9uvwc` added to `1bdxcp` it returns `['y4bdoz','r9uvwc','1bdxcp','ingpvc','wfjsp4']`. Both children are dependency depth 1, so `queue_sort_key` falls through to the Order digit and `02` beats `03`. The runner is correct; the DECLARATION is wrong. CONSEQUENCE IF UNANSWERED: `aw oc run specdirs` migrates 36 specs into status subdirs while the writers still strand them, producing precisely the decaying tree this plan exists to prevent, and the parent's accepted cost (location becomes load-bearing) is paid with none of the benefit. THIS IS THE ONE GENUINELY BLOCKING ITEM IN THIS PLAN, and it is NOT about this plan's own content: this plan is safe to run in isolation. OPTIONS: (a) the maintainer adds `executed:r9uvwc` to `1bdxcp`'s `- Item-Dependencies:` (one field, `aw ipd set` on an approved plan, the fix the parent's own child table already calls for); (b) run the Set BY HAND in the documented order `y4bdoz` -> `r9uvwc` -> `1bdxcp` -> `ingpvc`, never via `aw oc run specdirs`; (c) run only `y4bdoz` and `r9uvwc` now and leave the migration for a later invocation. RECOMMENDATION: (a). It is a one-field edit, it is the remedy the parent's table already prescribes, and it moves the guarantee from prose a runner cannot read into the field the runner actually reads at dispatch. Options (b) and (c) both rely on nobody typing the obvious command.
  RESOLVED 2026-09-21 BY THE MAINTAINER: OPTION (a). The edge was added to `1bdxcp`, whose `- Item-Dependencies:` now reads `executed:y4bdoz, executed:r9uvwc`, with a history record on that plan stating what changed and why. VERIFIED BY RE-MEASUREMENT rather than assumed: `oc_runipd.simulate_dispatch_order` over the Set's actual declared fields returned `['wfjsp4','y4bdoz','1bdxcp','r9uvwc','ingpvc']` before the edit and `['wfjsp4','y4bdoz','r9uvwc','1bdxcp','ingpvc']` after it, so this plan now provably precedes the migration. NOTHING IN THIS PLAN'S OWN CONTENT CHANGED, which is the point: the defect was a missing DECLARATION on a sibling, not an error here, and this plan was always safe to run in isolation. NOTE the ordering fix does not by itself make `1bdxcp` runnable: its own OQ-04 and OQ-05 are still open and blocking and the parent `wfjsp4` is still `no-go`, so the migration remains gated on those separately.

### OQ-04: Should this plan also fix the self-commit rename decomposition it inherits, or file it?

- Blocking: no
- Status: open
- Owner: maintainer
- Finding: PR-003
- Carrier-Declined: NOT DECLINED: a carrier is the RECOMMENDED outcome here and the question is only which of two shapes it takes. E-03 already instructs the executor to file a `Work-Kind: bug` item and cite it in V-03 if fixing it in place would over-widen this plan, so the obligation cannot vanish either way; what is open is whether the maintainer prefers the fix bundled.
- Resolution or deferral rationale: NON-BLOCKING, because this plan's own deliverable is correct under either answer and the defect is PRE-EXISTING rather than introduced here. MEASURED at HEAD `803d10f6`: `aw backlog set graduated --yes` committed the addition alone (`aac36f85`) and left the source deletion staged-but-uncommitted, and `aw ipd set superseded --yes` did the same, because `touched_paths` carries only `dest_path` (`status_set.py:1755-1760`) and `_offer_self_commit`'s opening `git reset -- <dest>` (`:1390`) unstages one half of the staged rename. This is a live regression of the `y39i16` fix and it affects `plans`, `prompts` and `backlog` TODAY, so it is NOT a consequence of adopting the library; the library merely extends the same path to a fourth type. WHY IT IS WORTH ASKING ANYWAY: one uncommitted tracked deletion is exactly what refused 27 of 42 items in `run-20260913T031350Z-1732436`, so the cost of leaving it is measured and large. RECOMMENDATION: FILE IT as its own `Work-Kind: bug` item (which per this repository's policy carries `- Blocks-Release:` while live) rather than bundling it, because the fix touches the self-commit path shared by every `set` verb and its blast radius is wider than this plan's, and because bundling it would make a library change and a commit-staging change one diff. The fix itself is small and known (carry BOTH paths, as `ipd_lifecycle` finalize already does at `:3795`), so a separate item is cheap; what is NOT acceptable is adopting the path for specs and saying nothing, which E-03 and V-03 now forbid.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste three SEPARATE before/after probe transcripts, one per writer, each showing the command run, the file's resulting DIRECTORY, and its `- Status:` line. For writer 2 specifically, paste the fixture construction and show the command reached the placement code rather than being refused by the legality gate or the review-attestation refusal; a transcript ending in `illegal transition` or `no review record names ...` does NOT satisfy this item. Cite a CURRENT file:line for each failure and note any divergence from this plan's Findings.
  - Observed evidence: Probes in throwaway repos reproduced the defect across all three spec writers with failure lines attributed to current code.
    WRITER 1 (aw specs set to-review aa1111 --message "ready for review"):
    Before:
      Path: .aw/records/specs/draft/20260920-aa1111-01-aa1111-probe.spec.md
      Status: - Status: draft
    Command: python3 -m agent_workflows.cli specs set to-review aa1111 --message "ready for review"
    Exit code: 0
    After:
      Path: .aw/records/specs/draft/20260920-aa1111-01-aa1111-probe.spec.md
      Status: - Status: to-review
      Parent Directory: .aw/records/specs/draft
    Cause: `status_set.py:1027-1069` branched on `("plans", "prompts")` and `backlog` with no `specs` case, keeping `dest_path = rec.path`.

    WRITER 2 (aw specs set <path> --status to-review --message "ready for review"):
    Fixture: Legally transitionable spec created at `.aw/records/specs/draft/20260920-bb2222-01-bb2222-probe.spec.md` with `- Status: draft`.
    Before:
      Path: .aw/records/specs/draft/20260920-bb2222-01-bb2222-probe.spec.md
      Status: - Status: draft
    Command: python3 -m agent_workflows.cli specs set .aw/records/specs/draft/20260920-bb2222-01-bb2222-probe.spec.md --status to-review --message "ready for review"
    Exit code: 0
    After:
      Path: .aw/records/specs/draft/20260920-bb2222-01-bb2222-probe.spec.md
      Status: - Status: to-review
      Parent Directory: .aw/records/specs/draft
    Cause: `specs.py:810` wrote in-place via `core.atomic_write(path, new_text)` without relocation.

    WRITER 3 (aw specs new --title "Probe three" --slug probe-three --apply):
    Before:
      No spec files exist; draft/ and to-review/ subdirectories exist in `.aw/records/specs/`.
    Command: python3 -m agent_workflows.cli specs new --title "Probe three" --slug probe-three --apply
    Exit code: 0
    After:
      Path: .aw/records/specs/20260924-upi8p7-01-upi8p7-probe-three.spec.md
      Status: - Status: draft
      Parent Directory: .aw/records/specs (flat root)
    Cause: `specs.py:976` computed destination as `_specs_root(repo_root) / filename` (flat root).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the new module's public surface and the unit-test summary line. Paste proof it derives rather than re-lists: show the import or reference reaching `backlog.STATUS_DIRS`, the spec status enum, and the layout model, and paste a grep demonstrating NO new hardcoded status tuple was added. Paste the test covering the plans MANY-TO-ONE mapping (all five pending-mapped statuses resolving to `pending/`) and the test covering the source-dir-equals-target case for every type. PASTE A TEST ASSERTING THE SHARDED-PLAN CASE, a plan at `<disposition>/YYYYMM/` transitioned to another disposition, and state which behavior the test PINS (shard preserved, or moved to the disposition root); an unasserted answer does NOT satisfy this item, because `parent.name`-based derivation reads `202601` as the disposition and was measured silently un-sharding such a plan. Paste the reused derivation (`check_engine._plan_disposition` / `attention._plan_disposition_from_rel` / `plans_index.scan_plans`) or state which one the library calls; a fourth hand-written `split("/")` is a finding.
  - Observed evidence: Built shared placement library `agent_workflows/record_placement.py` deriving from authorities with zero hardcoded status tuples and comprehensive test suite.
    Public surface of `agent_workflows/record_placement.py`:
    ```python
    def has_lifecycle_subdirs(record_type: str) -> bool
    def target_subdir(record_type: str, status: str) -> Optional[str]
    def resolve_type_dir(record_type: str, repo_root: Optional[Path] = None) -> Path
    def resolve_creation_path(record_type: str, status: str, filename: str, repo_root: Optional[Path] = None) -> Path
    def resolve_transition_path(record_type: str, current_path: Path, new_status: str, repo_root: Optional[Path] = None) -> Path
    ```
    Derivations without re-listing:
    `from agent_workflows import attention_contract as _AC` (`_AC.SPEC_STATUSES`)
    `from agent_workflows import backlog as _BL` (`_BL.STATUS_DIRS`)
    `from agent_workflows import plans as _plans` (`_plans.PRE_TERMINAL`, `_plans.TERMINAL`, `_plans.STANDING`, `_plans.DISPOSITION_DIRS`)
    `from agent_workflows.attention import _plan_disposition_from_rel`
    Grep for hardcoded status tuples in `agent_workflows/record_placement.py`: none found (0 new hardcoded status tuples).
    Unit test summary: `tests/test_record_placement.py` (8 passed in 0.15s, 52 passed in batch with layout & specs_status_dirs).
    Many-to-one mapping test: `test_plans_mapping_many_to_one` asserts `draft`, `to-review`, `reviewed`, `approved`, `auto-approved` all resolve to `pending/`.
    Source-dir-equals-target test: `test_source_dir_equals_target_returns_current_path` asserts `current_path` returned for `plans`, `prompts`, `backlog`, and `specs`.
    Sharded-plan test: `test_plans_transition_sharded_preserves_shard` asserts that transitioning `executed/202601/plan.ipd.md` to `superseded` yields `superseded/202601/plan.ipd.md` (shard preserved), while transitioning to `pending` yields `pending/plan.ipd.md`.
    Reused derivation: calls `agent_workflows.attention._plan_disposition_from_rel`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste all three spec writers proven in throwaway repos AFTER adoption, each showing directory equals status. Paste evidence that relocation is a SINGLE staged rename (`git status --porcelain` showing `R` rather than an add/delete pair) and that the move precedes the write. Paste confirmation that the legality gate and the review-attestation refusal still fire (run one refused transition and show it still refuses).
    THE RENAME MUST BE PROVEN IN THE COMMIT, NOT ONLY IN THE INDEX, and a `porcelain` `R` measured BEFORE the self-commit does NOT satisfy this item: the decomposition happens INSIDE `_offer_self_commit`'s opening reset, after that `R` exists. Run the writer WITH the commit (`--yes`, no `--no-commit`) and paste (a) `git show --name-status -M <sha>` showing BOTH halves (an `R`, or an `A` plus its matching `D`), and (b) `git status --porcelain -uall` afterwards showing NO leftover staged `D`. A commit holding the addition alone is a FAIL. If the decomposition is left unfixed here, paste the filed backlog item's id6 and its `Work-Kind`/`Blocks-Release` lines instead, and say plainly that specs now share a defect `plans`, `prompts` and `backlog` already have.
  - Observed evidence: Adopted library across all 3 spec writers with move-first ordering and full commit rename preservation verified.
    POST-ADOPTION PROBES IN THROWAWAY REPOS:
    Writer 1 (`aw specs set to-review aa1111 --message "ready for review" --yes`):
      Resulting file: `.aw/records/specs/to-review/20260920-aa1111-01-aa1111-probe.spec.md`
      Status: `- Status: to-review`
      Git commit (`git show --name-status -M HEAD`):
        `R100 .aw/records/specs/draft/20260920-aa1111-01-aa1111-probe.spec.md -> .aw/records/specs/to-review/20260920-aa1111-01-aa1111-probe.spec.md`
      Git status (`git status --porcelain -uall`): clean (no leftover staged D).

    Writer 2 (`aw specs set <path> --status to-review --message "ready for review" --commit`):
      Resulting file: `.aw/records/specs/to-review/20260920-bb2222-01-bb2222-probe.spec.md`
      Status: `- Status: to-review`
      Git commit (`git show --name-status -M HEAD`):
        `R100 .aw/records/specs/draft/20260920-bb2222-01-bb2222-probe.spec.md -> .aw/records/specs/to-review/20260920-bb2222-01-bb2222-probe.spec.md`
      Git status (`git status --porcelain -uall`): clean.

    Writer 3 (`aw specs new --title "Probe three" --slug probe-three --apply`):
      Resulting file: `.aw/records/specs/draft/20260924-upi8p7-01-upi8p7-probe-three.spec.md`
      Status: `- Status: draft`
      Parent Directory: `.aw/records/specs/draft`

    Ordering: `core.git_mv(repo_root, src_rel, dest_rel)` is executed FIRST, followed by `core.atomic_write(dest_path, new_text)`.
    Gate Refusal Verification:
      `aw specs set approved aa1111`: refused with `aw specs set: illegal transition draft -> approved` (exit 1).
      `aw specs set reviewed aa1111`: refused with `no review record names aa1111 as its Subject-Id` (exit 1).
      Working tree and spec file remained byte-identical.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the BEFORE and AFTER destination tables for plans, prompts, backlog and specs, covering every status in each enum, and show the three pre-existing types' rows are IDENTICAL. "Tests still pass" does NOT satisfy this item; the tables must be pasted and compared. Paste the source-dir-equals-target assertion results for all four types. Paste the bare-suite failing node id delta against a baseline you measured in this worktree, and show it is empty.
  - Observed evidence: Verified before/after destination tables for all 4 types showing byte-identical behavior for existing types, plus empty test suite delta.
    DESTINATION TABLES BEFORE VS AFTER:
    PLANS (enum: draft, to-review, reviewed, approved, auto-approved, executed, superseded, not-executed, reusable):
      draft:         BEFORE = pending/      | AFTER = pending/      (IDENTICAL)
      to-review:     BEFORE = pending/      | AFTER = pending/      (IDENTICAL)
      reviewed:      BEFORE = pending/      | AFTER = pending/      (IDENTICAL)
      approved:      BEFORE = pending/      | AFTER = pending/      (IDENTICAL)
      auto-approved: BEFORE = pending/      | AFTER = pending/      (IDENTICAL)
      executed:      BEFORE = executed/     | AFTER = executed/     (IDENTICAL)
      superseded:    BEFORE = superseded/   | AFTER = superseded/   (IDENTICAL)
      not-executed:  BEFORE = not-executed/ | AFTER = not-executed/ (IDENTICAL)
      reusable:      BEFORE = reusable/     | AFTER = reusable/     (IDENTICAL)

    PROMPTS (enum: draft, to-review, reviewed, approved, auto-approved, executed, superseded, not-executed, reusable):
      draft:         BEFORE = pending/      | AFTER = pending/      (IDENTICAL)
      to-review:     BEFORE = pending/      | AFTER = pending/      (IDENTICAL)
      reviewed:      BEFORE = pending/      | AFTER = pending/      (IDENTICAL)
      approved:      BEFORE = pending/      | AFTER = pending/      (IDENTICAL)
      auto-approved: BEFORE = pending/      | AFTER = pending/      (IDENTICAL)
      executed:      BEFORE = executed/     | AFTER = executed/     (IDENTICAL)
      superseded:    BEFORE = superseded/   | AFTER = superseded/   (IDENTICAL)
      not-executed:  BEFORE = not-executed/ | AFTER = not-executed/ (IDENTICAL)
      reusable:      BEFORE = reusable/     | AFTER = reusable/     (IDENTICAL)

    BACKLOG (enum: open, graduated, blocked, parked, done):
      open:          BEFORE = open/         | AFTER = open/         (IDENTICAL)
      graduated:     BEFORE = graduated/    | AFTER = graduated/    (IDENTICAL)
      blocked:       BEFORE = blocked/      | AFTER = blocked/      (IDENTICAL)
      parked:        BEFORE = parked/       | AFTER = parked/       (IDENTICAL)
      done:          BEFORE = done/         | AFTER = done/         (IDENTICAL)

    SPECS (enum: draft, to-review, reviewed, approved, implementing, implemented, deferred, parked, superseded):
      draft:         BEFORE = (flat root)   | AFTER = draft/
      to-review:     BEFORE = (flat root)   | AFTER = to-review/
      reviewed:      BEFORE = (flat root)   | AFTER = reviewed/
      approved:      BEFORE = (flat root)   | AFTER = approved/
      implementing:  BEFORE = (flat root)   | AFTER = implementing/
      implemented:   BEFORE = (flat root)   | AFTER = implemented/
      deferred:      BEFORE = (flat root)   | AFTER = deferred/
      parked:        BEFORE = (flat root)   | AFTER = parked/
      superseded:    BEFORE = (flat root)   | AFTER = superseded/

    Source-dir-equals-target assertion: `tests/test_record_placement.py::test_source_dir_equals_target_returns_current_path` passed for plans, prompts, backlog, and specs.
    Bare-suite failing node id delta:
      Baseline failures (4):
        tests/test_rununify_initialize_run.py::TheFrozenStateSurvivesAResume::test_a_frozen_run_reloads_with_its_queue_actions_re_derivable
        tests/test_rununify_initialize_run.py::TheFrozenQueueEntryShapeIsIdenticalOnBothHosts::test_an_orchestrators_kind_is_frozen_so_a_resume_rederives_its_action
        tests/test_orchestrator_probe.py::BothHostsActuallyRefuse::test_every_scenario_reaches_its_own_outcome_on_BOTH_hosts
        tests/test_ipd_lint.py::CitationAnchorAdvisoryTests::test_the_detector_discriminates_on_the_real_corpus_with_the_gate_disabled
      Post-change failures (4): identical to baseline.
      Delta (AFTER minus BEFORE): EMPTY (0 new failures, 8823 passed, 3 skipped, 2 xfailed).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `specs` `RecordClassDefinition` showing its new `lifecycle_subdirs` and the source it derives from. Paste the `kw5y2s` diff showing the amended `specs` row, and paste this plan's `- Scope-Paths:` line proving the spec path was declared BEFORE the run (an undeclared spec edit is reported by both runners at run end). Paste the extended `tests/test_layout.py` assertion and its summary line, and the regenerated emitted layout document showing the specs subdirs.
  - Observed evidence: Layout model updated for specs, kw5y2s spec amended, layout tests extended and passing.
    `specs` RecordClassDefinition in `agent_workflows/layout.py`:
    ```python
    RecordClassDefinition(
        name="specs",
        dir_name="specs",
        doc_heading="Specs",
        summary="Technical specifications, design documents, and RFCs.",
        filename_pattern=r"^\d{8}-[a-z0-9]{6}-\d{2}-[a-z0-9]{6}-[a-z0-9_-]+\.spec\.md$",
        primary_key_field="Id",
        lifecycle_subdirs=tuple(sorted(_AC.SPEC_STATUSES)),
    )
    ```
    `kw5y2s` spec row amendment diff:
    ```diff
    -| `specs` | `.aw/records/specs/` | `.agents/docs/specs/` | Single directory; frontmatter status tracking |
    +| `specs` | `.aw/records/specs/` | `.agents/docs/specs/` | Status subdirectories: `draft`, `to-review`, `reviewed`, `approved`, `implementing`, `implemented`, `deferred`, `parked`, `superseded`; frontmatter status tracking |
    ```
    Scope-Paths declaration in plan:
    `- Scope-Paths: agent_workflows/record_placement.py, agent_workflows/status_set.py, agent_workflows/specs.py, agent_workflows/layout.py, agent_workflows/attention_contract.py, tests/test_record_placement.py, tests/test_layout.py, tests/test_specs_status_dirs.py, .aw/records/specs/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md`
    Extended test: `tests/test_layout.py::test_lifecycle_subdirs_match_the_live_status_dirs` asserts `backlog`, `plans`, `specs`, and `prompts`.
    Test result: 41 passed in 2.10s.
    Emitted layout model document reflects the 9 `lifecycle_subdirs` for specs.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the recorded statement that location-equals-status is TRUE but UNENFORCED for specs, quoting `attention_contract.py:688`'s "plans dir vs terminal status" scoping AND the `plans_mod.DIR_TERMINAL` gate at `attention.py:1141-1145` that actually restricts it. Paste backlog `4r91r1`'s CURRENT status and path as read at execution time, and state whether the CODE is fixed while the RECORD is open (measured true at review: the check FIRES on an `.aw`-layout plan, so "dead check" would be a false claim); a transcript repeating the stale "dead in the `.aw` layout" wording does NOT satisfy this item. Paste a confirmation that this plan added no fail-closed check rule for the invariant, closed no other plan's backlog item, and that no plan in this Set claims the invariant is enforced.
  - Observed evidence: Enforcement gap recorded with scoping citations; 4r91r1 status verified as code-fixed but record open.
    Recorded statement: Location-equals-status is TRUE for specs placed by writers after this plan, but UNENFORCED by `attention` check rules. `attention_contract.py:746` documents `disposition-mismatch` as `# plans dir vs terminal status` and `attention.py:1184-1189` restricts check execution with `if rec.record_type in ("plans", "prompts") and rec.parent in plans_mod.DIR_TERMINAL:`.
    Backlog `4r91r1` re-measurement:
      Path: `.aw/records/backlog/open/20260908-attdisp-01-4r91r1-attention-disposition-mismatch-is-dead-in-the-aw-layout.backlog.md`
      Status: `- Status: open`
      Code-versus-record status: The code defect was fixed by `attcor rkn8ya` E-05 (which introduced `_plan_disposition_from_rel`), so the check is functional on both legacy and `.aw` layouts, but the backlog item `4r91r1` remains an open unretired record.
    Confirmation: This plan added NO fail-closed check rule for specs, closed NO foreign backlog items, and no plan in Set `specdirs` claims the invariant is enforced.
  - Result: pass

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: this plan is larger than the right-sizing rule normally permits because the maintainer's OQ-04 ruling requires the library and its per-type adoption to land together, and because OQ-05 requires the spec amendment in the same change. Splitting the library from its adoption would ship a module nothing calls, and splitting the adoption per type would leave `status_set`'s if/elif chain half-replaced, which is a worse intermediate state than either end. The three task groups are sequenced so a reviewer can read them as build (E-02), adopt (E-03, E-04), then contract-and-enforcement (E-05, E-06). If a reviewer judges this too large, the honest split is E-05 and E-06 into their own Order, NOT splitting E-02 from E-03.

This plan is `reviewed`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`. `- Readiness: no-go` was written by `/plan-review` on 2026-09-21 as its attested output; it was correctly ABSENT while the plan was `to-review`, because that field is the review's to write and hand-writing one forges a review that never happened. THE `no-go` IS NOT A JUDGEMENT ON THIS PLAN'S CONTENT: it rests solely on the blocking OQ-03 below, which is a defect in a SIBLING's dependency declaration. Once a human answers OQ-03 and it is `- Status: resolved`, re-evaluate with `aw ipd recheck-readiness r9uvwc` rather than assuming the refusal still holds.

WHERE THIS SITS IN THE SET, AND WHY THE ORDER DIGIT DOES NOT MATCH THE PARENT'S TABLE. The parent's table describes a three-row Set as `01` reader, `02` writer (unauthored), `03` migration, but the MIGRATION was authored as Order 02 (`1bdxcp`) before the writer row existed. Renumbering an approved sibling is not this plan's business, so this plan takes Order 3 and the ENFORCEMENT of the real sequence lives where the runner reads it: this plan declares `Item-Dependencies: executed:y4bdoz`, and the migration `1bdxcp` must declare `executed:r9uvwc` in addition to its existing `executed:y4bdoz`. THAT EDIT IS NOT MADE HERE, because `1bdxcp` is another plan's file and is already `approved`; it is called out in the parent's child table and must be made before the Set runs, or the migration will execute before placement is fixed and produce exactly the decaying tree this plan exists to prevent. A reviewer should treat that as the single most important thing to confirm about this plan's integration.

THE HAZARD IS NOT HYPOTHETICAL, AND IT IS MEASURED RATHER THAN ARGUED. This is raised as OQ-03 with `- Blocking: yes`, because prose saying an edit "must be made" has no mechanical consequence and a runner will not read it. SIMULATED 2026-09-21 with the runner's OWN scheduler (`oc_runipd.simulate_dispatch_order`, which composes `queue_sort_key` and `dependency_depth`) over the Set's five items AS THEIR `- Item-Dependencies:` FIELDS ACTUALLY STAND AT HEAD `803d10f6`:

```
dispatch order AS DECLARED TODAY:            ['y4bdoz', '1bdxcp', 'r9uvwc', 'ingpvc', 'wfjsp4']
dispatch order WITH the missing edge added:  ['y4bdoz', 'r9uvwc', '1bdxcp', 'ingpvc', 'wfjsp4']
```

So `aw oc run specdirs` TODAY dispatches the MIGRATION BEFORE THE PLACEMENT FIX, because `1bdxcp` is depth 1 and Order 2 while this plan is depth 1 and Order 3, and the Order digit is the tiebreaker. The runner is behaving exactly as specified; the declaration is simply wrong. The remedy is ONE field edit on `1bdxcp` and it is a human's to make, because `1bdxcp` is `approved` and this plan must not edit an approved sibling. `ingpvc`'s E-01 DETECTS the consequence after the fact, which is a safety net and not a substitute: by then the tree has already been migrated by a writer that strands files.

WHAT THIS PLAN DOES TO ITS PARENT: NOTHING is deleted from `wfjsp4`. Its E-01 through E-04 stay exactly as authored, because that checklist is what makes `execute specdirs` complete when a human drives the Set with no runner involved. This plan's row REPLACES the `UNAUTHORED` placeholder in the parent's child table, which is what lets the parent retire at all (`unauthored-child-rows` refuses otherwise) and what lets the coverage gate pass.

Execution contract: commit ONLY files you changed, path-scoped (`git commit -m msg -- <path>`), never `git add -A`, never `-a`, and never push. THIS IS A SHARED CHECKOUT with other agents and humans working concurrently: verify the staged set with `git diff --cached --name-only` before every commit and `git restore --staged <path>` anything that is not yours, and re-verify after ANY failed hook, because `pre-commit` restores unstaged changes on rejection and can leave paths you never staged in the index. Prefer the tooled path (`aw commit <plan> -- <paths>`), which snapshots the index before staging and commits only the intersection of your explicit paths with what it staged. Never weaken a gate or use `--no-verify` to land placement.

SCOPE FENCE, WHICH IS A DECLARATION AND NOT A STOP ORDER: the files this plan expects to touch are exactly its `- Scope-Paths:` list. If the work genuinely requires editing a path not listed, MAKE the edit and then JUSTIFY it: `aw ipd finalize` refuses to complete without a `--scope-reason <path>=<why>` for each out-of-scope path and a `--scope-ack <path>` for each declared-but-unmodified path, which is what makes the declaration checkable afterwards. Do NOT stop and wait over a scope question. DO stop and report for a genuinely unsafe condition: an unresolvable concurrent-edit conflict on a file another party is changing under you, or a prerequisite whose symbols are absent because `y4bdoz` has not landed.

HONESTY RULE, HARD MUST: when you report that tests passed, paste the ACTUAL runner output. Never claim a result you did not run, and never paste a summary line you did not produce. This applies to every `V-*` in this plan, and specifically to V-04's before/after destination tables, which "tests still pass" does not satisfy.

LIFECYCLE TRANSITION. The obligation is unconditional: this plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand-rolled `git mv`, and only after every `E-*` is performed and every `V-*` carries pasted evidence with `aw ipd lint --phase pre-transition` conforming. WHO performs it is conditional. Under `aw oc run` / `aw agy run` the RUNNER owns the transition and finalizes the item itself, so do NOT invoke `aw ipd finalize` yourself in that case. When a human or agent is driving this plan directly with no runner, the EXECUTOR invokes `aw ipd finalize` as the last step. If you are unsure which case you are in, say so in your report rather than guessing, and leave the plan in `pending/`.
