# IPD: Build one shared record placement library and adopt it in every spec writer

- Date: 2026-09-20
- Kind: child
- Concern: Orchestrator `wfjsp4`'s child table declares Order 02 as `UNAUTHORED, must be written before this Set runs`, so the Set cannot execute: an orchestrator whose table declares a row resolving to no plan REFUSES retirement (`unauthored-child-rows`), and the ORCHESTRATOR COVERAGE GATE refused a run naming `wfjsp4` on 2026-09-21. This plan is that missing child. The defect it closes is measured and current: THREE writers can place a spec and the Set as authored teaches only ONE of them, so the location-equals-status invariant the migration establishes would decay on its very next write. `status_set.run_set_command`'s relocation block branches on `plans`, `prompts` and `backlog` only and gives a spec NO `dest_path`; `specs.run_new` writes to the flat root.
- Scope: Build the shared placement library the maintainer ruled for in OQ-04, and adopt it in every spec writer plus the two types whose branches it replaces. IN: one module answering "where does a record of type T with status S live" for both TRANSITION and CREATION, adopted by `status_set.run_set_command`, the forked `specs.run_set`, and `specs.run_new`, with the existing `plans`/`prompts`/`backlog` branches replaced by calls to it and regression evidence that their behavior is byte-identical. OUT: moving any spec file (that is the migration child `1bdxcp`), making the specs readers recursive (that is `y4bdoz`), and promoting location-equals-status to a fail-closed `aw check` rule.
- Scope-Paths: agent_workflows/record_placement.py, agent_workflows/status_set.py, agent_workflows/specs.py, agent_workflows/layout.py, agent_workflows/attention_contract.py, tests/test_record_placement.py, tests/test_layout.py, tests/test_specs_status_dirs.py, .aw/records/specs/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md
- Item-Dependencies: executed:y4bdoz
- Status: to-review
- Set: specdirs
- Order: 3
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: r9uvwc
- From-Backlog: qzhfk2

## Workflow history

- 2026-09-20 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored to fill the UNAUTHORED row in `wfjsp4`'s child table, which review created as PR-001 and escalated as OQ-04, and which the ORCHESTRATOR COVERAGE GATE refused a run over on 2026-09-21. THE SHAPE OF THIS PLAN IS THE MAINTAINER'S, NOT MINE, and that is the single most important thing a reviewer should check me on. `wfjsp4` OQ-04 is `- Status: resolved`, RESOLVED BY THE MAINTAINER 2026-09-10 via `/askme`, and the ruling is explicitly WIDER than the question asked: "The answer is not 'add the writer child' but BUILD ONE SHARED PLACEMENT LIBRARY AND ADOPT IT PER TYPE, then have every status-changing and creation verb call it instead of constructing a path itself. Adopting it replaces the EXISTING plans and backlog branches too, so the duplicated knowledge disappears rather than growing by one." So a narrow three-writer fix would CONTRADICT a recorded maintainer decision, and this plan implements the ruled shape instead. The ruling also authorized breaking the work into multiple plans and warned that adoption TOUCHES WORKING CODE for plans and backlog, so regression evidence is mandatory and "must not be waved through"; E-04 and V-04 carry that. RE-MEASURED EVERY LOAD-BEARING CITATION AT HEAD `41f6a45b` RATHER THAN TRUSTING THE 12-DAY-OLD REVIEW, and the defect reproduces while three figures moved. THE THREE WRITERS, each proven BEHAVIORALLY in a throwaway git repo, not by reading code. WRITER 1, `aw specs set to-review aa1111` (the `--status`-ABSENT spelling): printed the transition `draft → to-review`, rewrote the status line to `- Status: to-review`, and LEFT THE FILE at `.aw/records/specs/draft/20260920-aa1111-01-aa1111-probe.spec.md`. Confirmed the cause by reading `status_set.py:1027-1069`: the `dest_path` block branches `if rec.record_type in ("plans", "prompts")`, `elif rec.record_type == "backlog"`, and there is NO `specs` branch, so `dest_path = rec.path` survives unchanged. NOTE the review cited `status_set.py:840-864` for this block; the line numbers have MOVED to 1027-1069 and the branch set now includes `prompts`, so cite the current lines. WRITER 3, `aw specs new --title "Probe two" --slug probe-two --apply`: wrote `.aw/records/specs/20260920-v8vdh6-01-v8vdh6-probe-two.spec.md`, at the FLAT ROOT, with `- Status: draft`, while a `draft/` directory already existed in that repo. Cause at `specs.py:976` (`dest = _specs_root(repo_root) / filename`); review cited `:945`, so that line has moved too. WRITER 2, `aw specs set <path> --status <enum>`: could NOT be behaviorally proven in the same probe because the transition legality and review-attestation gates fired first (`illegal transition to-review -> approved`, then for `reviewed`, `no review record names aa1111 as its Subject-Id`). That is CORRECT gate behavior and not a defect, but it means the review's claim about this spelling rests on code reading alone; E-01 must construct a legally-transitionable fixture (or a spec with a real review record) to prove it, and a reviewer should NOT accept a code-reading-only verdict for writer 2. THE READER DEFECT ALSO REPRODUCES, which is why `executed:y4bdoz` is a real edge rather than a formality: in the same probe, `specs._spec_files` returned ONE file (the flat-root one) while `check_engine._iter_type_files` returned TWO, and `aw specs check --json` reported `{'checked': 1, 'violations': 0}` against 2 files on disk, i.e. it declared conformance having never read the spec in `draft/`. THREE FIGURES ARE STALE IN THE PARENT AND ITS REVIEW, so do not quote them: the tree now holds 36 specs, not 28 or 29, distributed 13 `approved`, 15 `implemented`, 2 `draft`, 2 `deferred`, 2 `superseded`, 1 `to-review`, 1 `implementing`, which is SEVENTEEN live and 19 terminal (review said 29 files / 13 live). The retired-filter trap the parent's CID-8 warns about reproduces with new numbers: `specs._spec_files` 36 versus `_iter_type_files` default 19 versus `include_retired=True` 36, sets EQUAL with the flag. THE SPEC AMENDMENT IS CARRIED HERE, per OQ-05's ruling.
- 2026-09-20 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make "where does a record of this type with this status live" a question ONE module answers, so the specs tree can be partitioned by status without the invariant decaying on the next `aw specs set` or `aw specs new`, and so the knowledge duplicated across three per-type branches collapses to one instead of growing to four.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the defect, then build the library

- [ ] E-01 RE-PROVE ALL THREE WRITERS BEHAVIORALLY BEFORE CHANGING ANYTHING, each in a throwaway git repo, because two of the three cited line numbers have already moved and a code-reading verdict is not evidence. For each writer, create a spec, run the writer, then assert the resulting file's DIRECTORY against its `- Status:`.
  WRITER 2 NEEDS A LEGALLY-TRANSITIONABLE FIXTURE AND THIS IS THE TRAP. My own probe could not reach `specs.run_set`'s placement code at all: `--status approved` was refused as an `illegal transition to-review -> approved`, and `--status reviewed` was refused because `no review record names aa1111 as its Subject-Id`. Those gates are correct. So construct a fixture that passes them (a legal single-step transition, plus a real `.review.md` carrying `- Subject-Id:` and `- Subject-Type: spec` where the target status requires attestation), or the test proves only that the gate works. DO NOT weaken a gate to make the fixture easy.
  PASTE ALL THREE RESULTS SEPARATELY. A pass on one spelling is not evidence about another; that exact assumption caused the two dual-spelling bypasses this codebase documents in-code at `status_set.py:517-525` and `:549-556` ("a gate installed in only one of them is bypassed by choosing the other").
  - Depends on: none
  - Expected outcome: three pasted before/after results, one per writer, each showing the file's directory and its `- Status:`; writer 2 proven through a fixture that actually reaches the placement code rather than being stopped by a legality or attestation gate; each failure attributed to a CURRENT file:line rather than to the review's stale ones.
  - Execution state: pending

- [ ] E-02 BUILD THE SHARED PLACEMENT LIBRARY, one module that answers placement for BOTH cases the maintainer named: where a TRANSITIONING record moves, and where a NEWLY CREATED record goes. The creation case is called out separately because the ruling names it as "a distinct class that nobody had considered, which is why `aw specs new` lands in the flat root".
  DERIVE FROM THE EXISTING AUTHORITIES, DO NOT RE-LIST THEM. This is the specific way this work could do damage. Each type currently keeps its status-to-directory knowledge in a different place and shape: `backlog.STATUS_DIRS` is a tuple at `backlog.py:78` (with `STATUSES = frozenset(STATUS_DIRS)` at `:79`), plans' dispositions are derived inline in `status_set.py` from a hardcoded 5-tuple, spec statuses live in `attention_contract.SPEC_STATUSES` (9 values: approved, deferred, draft, implemented, implementing, parked, reviewed, superseded, to-review), and `layout.py` models `lifecycle_subdirs` per record class (`plans` at `:158`, `prompts` at `:179`, `backlog` at `:203`, and `specs` HAS NONE). A fourth hardcoded list would be the very duplication this plan exists to remove.
  THE PATTERN HAS ALREADY FAILED ONCE IN EXACTLY THIS WAY, and the in-code comment at `status_set.py` records it: the backlog branch was repaired because a HARDCODED LIST silently DECLINED TO MOVE a file whose source dir was already the new status, "leaving the record's directory and its `- Status:` line disagreeing". Derive from `STATUS_DIRS` and from the layout model; do not retype either.
  NOTE THE PLANS CASE IS A MAPPING, NOT AN IDENTITY, and a library that assumes `dir == status` will break it: five plan statuses (`draft`, `to-review`, `reviewed`, `approved`, `auto-approved`) all map to `pending/`. Backlog and specs are identity mappings. The library must express both shapes.
  - Depends on: E-01
  - Expected outcome: a single module exposing placement for transition and creation, per type, deriving its directory knowledge from the existing authorities with no new hardcoded status list; the plans many-to-one mapping and the backlog/specs identity mappings both expressed; unit tests covering each type including the `source dir already equals target` case that previously regressed.
  - Execution state: pending

### Task group 2: adopt it everywhere, without changing what works

- [ ] E-03 ADOPT THE LIBRARY IN ALL THREE SPEC WRITERS, so a spec lands in its status directory whichever verb placed it. The three call sites are `status_set.run_set_command`'s `dest_path` block (`status_set.py:1027-1069`, which needs a `specs` case), the forked `specs.run_set` (`specs.py:498`), and `specs.run_new` (`specs.py:934`, whose destination is computed at `:976`).
  RELOCATE WITH `git mv`, WHICH `status_set` ALREADY DOES AND WHICH THE PARENT'S OQ-01 GOT WRONG. OQ-01's resolution states that "no status setter in this repository uses `git mv`: `status_set` and `backlog` both `atomic_write` then `unlink`". That is STALE: `status_set` now performs `_core.git_mv` FIRST and then writes at the destination, and its in-code comment records exactly why the old write-then-unlink was a bug ("git sees TWO unrelated facts", which caused `oc_runipd.commit_backlog_close` to commit only the ADD and leave a dangling deletion that blocked 27 of 42 items in one run). ORDER IS LOAD-BEARING and the comment says so: move FIRST, then write, because writing first leaves an untracked file at the destination and `git mv` refuses. Follow the existing pattern; do not reintroduce write-then-unlink.
  DO NOT WEAKEN ANY GATE TO MAKE PLACEMENT WORK. The legality check and the review-attestation refusal both fire BEFORE placement (proven in E-01), and they must keep firing. Placement is what happens to a transition that is already permitted.
  - Depends on: E-02
  - Expected outcome: all three spec writers place a spec in the directory matching its status, each proven separately in a throwaway repo; relocation performed as a single staged rename via `git mv` with move-then-write ordering; no legality or attestation gate weakened.
  - Execution state: pending

- [ ] E-04 REPLACE THE EXISTING `plans`, `prompts` AND `backlog` BRANCHES WITH CALLS TO THE LIBRARY, AND PROVE THEIR BEHAVIOR IS UNCHANGED. The maintainer's ruling requires this ("adopting it replaces the EXISTING plans and backlog branches too, so the duplicated knowledge disappears rather than growing by one") AND flags it as the new risk this Set did not previously carry, to be carried with regression evidence rather than waved through.
  THE BAR IS BYTE-IDENTICAL BEHAVIOR, NOT "TESTS STILL PASS". For each of the three types, exercise every status in its enum and assert the destination path equals what the CURRENT code computes. The cheapest honest form: capture the current mapping as a table BEFORE the change (status -> destination directory, per type) and diff it against the same table AFTER. Paste both tables.
  COVER THE REGRESSION CASE THAT ALREADY HAPPENED ONCE: a record whose source directory already equals its target. The backlog branch silently declined to move in that case and left directory and status disagreeing. Assert it for all four types now.
  PROMPTS WERE NOT IN THE MAINTAINER'S SENTENCE BUT ARE IN THE CODE. The `dest_path` block branches on `("plans", "prompts")` together, so adopting the library necessarily touches prompts too. Treat prompts with the same regression bar rather than as an afterthought, and say so in the evidence.
  - Depends on: E-03
  - Expected outcome: the per-type relocation branches replaced by library calls; before/after destination tables pasted for plans, prompts, backlog and specs across every status in each enum, showing no change for the three pre-existing types; the source-dir-equals-target case asserted for all four.
  - Execution state: pending

### Task group 3: model, contract, and enforcement

- [ ] E-05 GIVE `specs` ITS `lifecycle_subdirs` IN THE LAYOUT MODEL AND AMEND THE `kw5y2s` SPEC IN THE SAME CHANGE, which is what OQ-05's maintainer ruling requires ("YES, AMEND `kw5y2s` IN THE SAME CHANGE, AND DECLARE IT IN `- Scope-Paths:` UP FRONT"), having explicitly declined the three alternatives (amend-first as aspirational documentation, abandon the change, or ship the contradiction as a follow-up).
  MEASURED AT HEAD, so you know exactly what to change: the `specs` `RecordClassDefinition` in `layout.py` carries NO `lifecycle_subdirs` key while `plans` (`:158`), `prompts` (`:179`) and `backlog` (`:203`) each do. The spec `.aw/records/specs/20260901-kw5y2s-01-kw5y2s-...spec.md` is `- Status: approved` and its record-class row for `specs` reads `Single directory; frontmatter status tracking`, which this Set falsifies.
  EXTEND `tests/test_layout.py::test_lifecycle_subdirs_match_the_live_status_dirs`, which currently asserts modeled-versus-live subdirs for `backlog` and `plans` ONLY (verified at HEAD). The parent's OQ-05 is explicit that extending it "is part of the amendment, not optional", because until it covers specs nothing catches a model/live mismatch for this type.
  THE SPEC PATH IS DECLARED IN THIS PLAN'S `Scope-Paths` DELIBERATELY, and that declaration is the mechanism, not a formality: it is what makes `aw oc run`/`aw agy run` ANNOUNCE the spec edit BEFORE the run starts and what lets the finalize scope gate reconcile declared against actual. Both runners also report at run end which specs a run declared versus actually changed, including an undeclared change. Amend the ROW, not the spec's shape, and say WHY in this plan's spec-sync section.
  - Depends on: E-02
  - Expected outcome: `specs` carries `lifecycle_subdirs` derived from `SPEC_STATUSES` in the layout model; `kw5y2s`'s `specs` record-class row amended to describe status subdirs with the reason recorded; `test_lifecycle_subdirs_match_the_live_status_dirs` extended to cover specs (and prompts, if the same gap exists there); the emitted layout document reflects the new subdirs.
  - Execution state: pending

- [ ] E-06 REPORT THE ENFORCEMENT GAP RATHER THAN SILENTLY LEAVING IT, because specs would otherwise gain subdirs with NO checker covering them. `attention.disposition-mismatch` is documented as "plans dir vs terminal status" (`attention_contract.py:688`), so it does not cover specs.
  DO NOT FIX IT HERE, AND DO NOT PROMOTE THE INVARIANT TO A FAIL-CLOSED RULE. Two reasons, both recorded: the parent's OQ-03 leaves the severity decision OPEN for the maintainer with the migration's measured result in hand, and the check was separately measured DEAD in the `.aw` layout, tracked as backlog `4r91r1` (verified still `- Status: open` at HEAD, in `.aw/records/backlog/open/20260908-attdisp-01-4r91r1-...`). Fixing a dead check and widening it to a new type in the same plan that also builds a library would make three blast radii one diff.
  THE DELIVERABLE IS A RECORD, NOT CODE: state in this plan's evidence that the invariant this plan makes TRUE is not yet ENFORCED for specs, name `4r91r1` as the prerequisite, and confirm no plan in this Set claims otherwise. If `4r91r1` has been fixed by the time this runs, say so and state that widening it to specs is still a separate decision.
  - Depends on: E-05
  - Expected outcome: a recorded statement that location-equals-status is true-but-unenforced for specs, citing `attention_contract.py:688` and backlog `4r91r1` with its current status, and confirming this plan added no fail-closed rule.
  - Execution state: pending

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

| Id | Severity | Location (measured at HEAD `41f6a45b`) | Finding | Evidence |
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

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste three SEPARATE before/after probe transcripts, one per writer, each showing the command run, the file's resulting DIRECTORY, and its `- Status:` line. For writer 2 specifically, paste the fixture construction and show the command reached the placement code rather than being refused by the legality gate or the review-attestation refusal; a transcript ending in `illegal transition` or `no review record names ...` does NOT satisfy this item. Cite a CURRENT file:line for each failure and note any divergence from this plan's Findings.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new module's public surface and the unit-test summary line. Paste proof it derives rather than re-lists: show the import or reference reaching `backlog.STATUS_DIRS`, the spec status enum, and the layout model, and paste a grep demonstrating NO new hardcoded status tuple was added. Paste the test covering the plans MANY-TO-ONE mapping (all five pending-mapped statuses resolving to `pending/`) and the test covering the source-dir-equals-target case for every type.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste all three spec writers proven in throwaway repos AFTER adoption, each showing directory equals status. Paste evidence that relocation is a SINGLE staged rename (`git status --porcelain` showing `R` rather than an add/delete pair) and that the move precedes the write. Paste confirmation that the legality gate and the review-attestation refusal still fire (run one refused transition and show it still refuses).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the BEFORE and AFTER destination tables for plans, prompts, backlog and specs, covering every status in each enum, and show the three pre-existing types' rows are IDENTICAL. "Tests still pass" does NOT satisfy this item; the tables must be pasted and compared. Paste the source-dir-equals-target assertion results for all four types. Paste the bare-suite failing node id delta against a baseline you measured in this worktree, and show it is empty.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `specs` `RecordClassDefinition` showing its new `lifecycle_subdirs` and the source it derives from. Paste the `kw5y2s` diff showing the amended `specs` row, and paste this plan's `- Scope-Paths:` line proving the spec path was declared BEFORE the run (an undeclared spec edit is reported by both runners at run end). Paste the extended `tests/test_layout.py` assertion and its summary line, and the regenerated emitted layout document showing the specs subdirs.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the recorded statement that location-equals-status is TRUE but UNENFORCED for specs, quoting `attention_contract.py:688`'s "plans dir vs terminal status" scoping and backlog `4r91r1`'s CURRENT status and path as read at execution time (it was `open` when this plan was authored). Paste a confirmation that this plan added no fail-closed check rule for the invariant, and that no plan in this Set claims the invariant is enforced.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: this plan is larger than the right-sizing rule normally permits because the maintainer's OQ-04 ruling requires the library and its per-type adoption to land together, and because OQ-05 requires the spec amendment in the same change. Splitting the library from its adoption would ship a module nothing calls, and splitting the adoption per type would leave `status_set`'s if/elif chain half-replaced, which is a worse intermediate state than either end. The three task groups are sequenced so a reviewer can read them as build (E-02), adopt (E-03, E-04), then contract-and-enforcement (E-05, E-06). If a reviewer judges this too large, the honest split is E-05 and E-06 into their own Order, NOT splitting E-02 from E-03.

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`. No `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened.

WHERE THIS SITS IN THE SET, AND WHY THE ORDER DIGIT DOES NOT MATCH THE PARENT'S TABLE. The parent's table describes a three-row Set as `01` reader, `02` writer (unauthored), `03` migration, but the MIGRATION was authored as Order 02 (`1bdxcp`) before the writer row existed. Renumbering an approved sibling is not this plan's business, so this plan takes Order 3 and the ENFORCEMENT of the real sequence lives where the runner reads it: this plan declares `Item-Dependencies: executed:y4bdoz`, and the migration `1bdxcp` must declare `executed:r9uvwc` in addition to its existing `executed:y4bdoz`. THAT EDIT IS NOT MADE HERE, because `1bdxcp` is another plan's file and is already `approved`; it is called out in the parent's child table and must be made before the Set runs, or the migration will execute before placement is fixed and produce exactly the decaying tree this plan exists to prevent. A reviewer should treat that as the single most important thing to confirm about this plan's integration.

WHAT THIS PLAN DOES TO ITS PARENT: NOTHING is deleted from `wfjsp4`. Its E-01 through E-04 stay exactly as authored, because that checklist is what makes `execute specdirs` complete when a human drives the Set with no runner involved. This plan's row REPLACES the `UNAUTHORED` placeholder in the parent's child table, which is what lets the parent retire at all (`unauthored-child-rows` refuses otherwise) and what lets the coverage gate pass.

Execution contract: commit ONLY files you changed, path-scoped (`git commit -m msg -- <path>`), never `git add -A`, never `-a`, and never push. THIS IS A SHARED CHECKOUT with other agents and humans working concurrently: verify the staged set with `git diff --cached --name-only` before every commit and `git restore --staged <path>` anything that is not yours, and re-verify after ANY failed hook, because `pre-commit` restores unstaged changes on rejection and can leave paths you never staged in the index. Prefer the tooled path (`aw commit <plan> -- <paths>`), which snapshots the index before staging and commits only the intersection of your explicit paths with what it staged. Never weaken a gate or use `--no-verify` to land placement. When every `E-*` is performed and every `V-*` carries pasted evidence, move this plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never by hand.
