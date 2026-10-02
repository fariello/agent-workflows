# IPD: Migrate the 35 cold-status research docs from the hot root into their monthly shards

- Date: 2026-09-30
- Kind: child
- Concern: 35 research docs carry `status: reference` while living at the research tree's hot root, so the physical tier contradicts the frontmatter status the README declares authoritative.
- Scope: Move those 35 docs into their computed `reference/YYYYMM/` shards with `aw research promote --apply`, and repair the three LIVE path citations the moves would strand. No source change, no checker rule (that is sibling `ucwlwt`), no frontmatter change beyond what the tool writes.
- Scope-Paths: .aw/records/research, agent_workflows/comms.py, .aw/records/plans/pending/20260929-sklbrt-01-h8e3sm-mint-an-id6-for-the-two-live-legacy-specs-so-they-are-reacha.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: zdsf35
- Set: zdsf35
- Order: 1
- Highest E allocated: 07
- Author: opencode Opus 5, its_direct/pt3-claude-opus-5-1m-us
- Id: mg8bag
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 reviewed (aw set): /plan-review complete: APPROVE WITH REVISIONS APPLIED; PR-201 through PR-209 all FIXED, zero deferred, zero open. PR-201 was a BLOCKER: approved plan 68hdic executed since authoring, so E-06 would have directed an executor to rewrite an immutable executed plan. Findings and four Decisions rows in .aw/records/reviews/20260930-zdsf35-01-mg8bag-migrate-the-35-cold-status-research-docs-from-the-hot-root-i.review.md. Readiness go-pending-approval; human approval still required before execution.

- 2026-10-01 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-201 through PR-209 all FIXED, zero deferred, zero open. THE PLAN'S CENTRAL MEASUREMENT RE-DERIVES EXACTLY at review HEAD `c82c829d8`, character for character: 126 docs under the research tree, 61 at the hot root, 35 of those carrying a cold normalized status, ALL 35 `reference` and none `archive`, targets `reference/202607` (18) / `reference/202608` (14) / `reference/202609` (3), zero `plan_transition` errors, zero hot-status docs inside a cold shard, and 11 of the 35 with a `created` month diverging from their filename month. The 35-id list in E-01 matches my own derivation exactly. F-03's quoted concession in `research_archive.apply_moves` ("if a full-path cite exists it is caught by the dangling detector") is verbatim correct and the claim it makes is indeed false for a tier move, since the basename is unchanged. F-10's three named pre-existing stale citations all check out (`bu9yij`, `27rjro`, `i5gj61` each live in a `reference/` shard), and F-11 holds exactly: zero pending or reusable plans name a cohort doc in `- Scope-Paths:`.
  THE PLAN'S THIRD TASK GROUP HAS BEEN OVERTAKEN BY EVENTS, AND THAT IS THIS REVIEW'S CENTRAL FINDING (PR-201). Approved plan `68hdic` HAS EXECUTED since authoring (`lifecycle(68hdic): finalize 68hdic -> executed`, commit `a7f0ce4f1`); it now lives in `.aw/records/plans/executed/` and is IMMUTABLE. It already performed its E-05: `agent_workflows/comms.py` line 20 no longer carries the retired `.agents/docs/research/` form at all (zero grep hits) and instead names `j2000q`'s CURRENT ROOT PATH, which resolves on disk today. Three of this plan's statements are therefore now false as written: `- Scope-Paths:` declared `68hdic` at a `plans/pending/` path that NO LONGER EXISTS, E-06 instructed an executor to edit 3 occurrences in it, and E-05 described a pre-existing dangling `.agents/` citation that is already gone. Had this executed unrevised, E-06 would have attempted the one edit the execution contract most firmly forbids, on a file the declared path cannot even locate.
  THE REPAIR SET IS SMALLER THAN THE PLAN BELIEVES AND I RE-DERIVED IT RATHER THAN ADJUSTING THE PLAN'S NUMBER (PR-202). Measured across the whole tracked tree outside the research directory: 7 cohort docs are cited by full path (not 14) across 12 files (not 11) holding 24 occurrences (not 16+). Of those 12, TEN are immutable (9 executed plans plus 1 review record) and exactly TWO are live: `agent_workflows/comms.py` (1 occurrence, `j2000q`) and pending plan `h8e3sm` (1 occurrence, `en5c8i`). So the live repair set is 2 occurrences in 2 files, where the plan said 3 in 3. The authored counts were correct when written; `68hdic`'s execution is what moved them, which is precisely the class of drift E-01 and E-02 exist to catch, and the reason both now refuse to reconcile to this plan's figures.
  ONE VALIDATION BAR WAS A DRIFTING LIVE POPULATION PINNED AS A CONSTANT (PR-205). F-06 and E-07 quote a `dangling-citation` baseline of 61; re-measured it is 70, while `adopted-without-consumer` (35) and `stale-state-to-promote` (17) reproduce exactly. The plan's METHOD is right and is its best feature: comparing GROUPED per-rule counts before and after, rather than an exit code that is already 1, is exactly the correct design for an already-failing gate. What was wrong was treating an authoring-time count as the bar rather than as context, so E-07 now re-derives its own before-baseline in the same session as the after-measurement and compares the DELTA, which is the only quantity that means anything here.
  OQ-01 IS NO LONGER AN OPEN ORDERING QUESTION BUT A SETTLED FACT (PR-203), and leaving it phrased as "either order" would have told a later reader a choice remains. `68hdic` ran first. Its resolution text correctly anticipated that branch and correctly made both orders safe, which is why the consequence here is a records correction and not a redesign.
  Also corrected: E-02's classification list omitted `backlog/graduated/` and `specs/` disposition edge cases and is now stated as a rule over `plans/executed|superseded|not-executed`, `reviews/`, and `backlog/done/` with everything else live (PR-204); the `- Scope-Paths:` entry for the executed plan was REMOVED rather than repointed, because a declared-but-unmodified path would otherwise force a `--scope-ack` at finalize for a file this plan must not touch (PR-206); E-04's commit instruction now names the gitignored manifests explicitly as a staging check rather than only a note (PR-207); V-06's expected occurrence counts were corrected from 3+1 to 1 (PR-208); and the authoring HEAD `7000df73` is relabelled as the authoring commit with the review commit named beside it (PR-209). The `- Work-Kind: chore` inheritance stands on measurement: readers key on frontmatter `status`, `zdsf35` carries no `- Blocks-Release:`, and the gating set is `bug` alone, so no gate attaches and this plan invents none. No research doc was moved, no citation was repaired, and no production file or test was modified by this review. Findings and four Decisions rows in `.aw/records/reviews/20260930-zdsf35-01-mg8bag-migrate-the-35-cold-status-research-docs-from-the-hot-root-i.review.md`.
- 2026-09-30 to-review (opencode Opus 5, its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `zdsf35`. `- Work-Kind: chore` and `- Priority: low` are INHERITED and both survive scrutiny: the readers key on frontmatter `status`, not on path, so no answer is wrong and the standing live-bug release gate does not attach (the item carries no `- Blocks-Release:` and this plan invents none). THE ITEM'S CENTRAL MEASUREMENT REPRODUCES EXACTLY at authoring HEAD `7000df73`: 35 root-dwelling docs carry a cold status, 0 docs carry a hot status inside a cold shard, and 0 sharded docs sit in the wrong month. THE ITEM'S REMEDY SHAPE IS ADOPTED, including its ordering argument (migrate first, then detect), which is why this is Order 01 of a two-child Set and sibling `ucwlwt` declares a hard `executed:mg8bag` edge. THREE CORRECTIONS THE ITEM DOES NOT CONTAIN, each measured rather than reasoned. FIRST, the item says all 35 are `reference` OR `archive`; measured, ALL 35 ARE `reference` and NONE is `archive`, so no `archive/` shard is created by this plan at all. SECOND, AND THIS IS THE REASON THE PLAN IS NOT A ONE-LINE SWEEP: 14 of the 35 docs are cited BY FULL PATH from elsewhere in the repository, and `aw research promote` DOES NOT REWRITE A PATH CITATION (verified in a scratch repo: after a move the citing file still named the old root path and `find_dangling_citations` returned `[]` both before and after, so nothing would have told us). 11 of those citing files are immutable executed plans or review records whose citations were correct when written and MUST NOT be rewritten; the other 3 are live and are repaired here. THIRD, the item's premise that a drift rule "would turn the tree red" needs one qualification that strengthens rather than weakens it: `aw research index --check` ALREADY exits 1 today on 61 pre-existing `dangling-citation` and 35 `adopted-without-consumer` findings, so the honest statement is that a tier rule would add 35 MORE findings to an already-failing gate, not that it would redden a green one. ONE ORDERING HAZARD IS REAL AND IS NOT DEFERRED: APPROVED plan `68hdic` (`- Blocks-Release: next`) instructs its executor to re-point `comms.py` at `j2000q`'s path, and `j2000q` is one of the 35. Whichever of the two runs second must use the post-move path, so E-06 repairs `68hdic`'s three occurrences in place and OQ-01 states the conflict for the maintainer rather than silently assuming an order.

## Goal

Make the research tree's physical layout agree with the status its own README declares authoritative, by moving the 35 cold-status docs out of the hot root into their monthly shards without stranding a single live citation. The payoff is that the hot root then means what it says (`todo`/`active` work awaiting attention) instead of being 59 files of which 35 are finished, and that sibling `ucwlwt` can ship a tier-drift rule that starts from zero findings instead of 35.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure before moving anything

- [x] E-01 RE-DERIVE the stranded cohort at execution HEAD rather than trusting this plan's list, and write the census into the execution record. For each conformant doc at the research root (one path component under the root, excluding `README.md` and `INDEX.md`), read frontmatter `status` through `research_contract.normalize_status` and select those whose normalized value is `reference` or `archive`. For each selected doc compute its target with `research_archive.plan_transition(root, <id6>, <status>)` and record `(id6, status, target shard)`. Also re-check the two directions the item measured clean: zero docs with a normalized hot status inside a `reference/` or `archive/` subtree, and zero sharded docs whose shard month differs from their frontmatter `created` month. REPORT the counts; do not reconcile them to this plan's numbers by adjusting the query. The authoring measurement, for comparison only, RE-CONFIRMED UNCHANGED at review HEAD `c82c829d8` (every figure and the full id list reproduced character for character): 35 docs, all `reference`, targeting `reference/202607` (18), `reference/202608` (14), `reference/202609` (3), with zero `plan_transition` errors; ids `0jl8pv 36rfym 524dw1 5zczmo 72n26s 74bchk 80eqy0 8i9py4 cnkyvn dkxesq e4k1m0 ebh1ap en5c8i fpt0dg g5vhpz ibl5kt itntmu j2000q jd8qhs kdr9kv ktlhfx lc6898 le9q02 mqqk8e qcxc6c rzfaon uec14r uxq2tt vdz4ui wusyd6 x41kw0 x9whzs ypmm6z z0wxwa za72ko`.
  - Depends on: none
  - Expected outcome: a recorded census of the cohort with each doc's computed target shard, the two clean-direction re-checks restated with their actual numbers, and any divergence from the authoring numbers named explicitly rather than smoothed over.
  - Execution state: performed

- [x] E-02 CENSUS THE PATH CITATIONS the moves would strand, and CLASSIFY each citing file as LIVE (repairable) or IMMUTABLE (must not be touched), because `aw research promote` does not rewrite them. For every doc in E-01's cohort, search the tracked tree outside `.aw/records/research/` for the string `.aw/records/research/<filename>`; a basename-only mention is NOT affected by a move and is out of scope. Classify by location, as a RULE rather than a list, so a location neither the plan nor the authoring measurement anticipated still gets a disposition (PR-204): a file under `plans/executed/`, `plans/superseded/`, `plans/not-executed/`, `reviews/`, or `backlog/done/` is IMMUTABLE under the execution contract's rule that an executed plan's record must not be rewritten and a citation correct when written must not be falsified; EVERYTHING ELSE is LIVE, which includes `plans/pending/`, `backlog/` in any non-`done/` state (`open/`, `graduated/`, `blocked/`, `parked/`), `specs/` in any state, and source. If a citing file's location fits neither clause cleanly, classify it IMMUTABLE and report it rather than guessing, since a wrongly-live classification risks falsifying a record while a wrongly-immutable one only leaves a stale pointer this plan did not create.
  DO NOT RECONCILE TO THE AUTHORING NUMBERS; THEY HAVE ALREADY MOVED ONCE (PR-202). Re-measured at review HEAD `c82c829d8`: 7 cohort docs are cited by full path across 12 files holding 24 occurrences, of which TEN files are IMMUTABLE (9 executed plans plus 1 review) and exactly TWO are LIVE: `agent_workflows/comms.py` (`j2000q`, 1 occurrence) and pending `h8e3sm` (`en5c8i`, 1 occurrence). The authoring measurement read 11 files / 8-plus-1 immutable / 2 live pending, and the difference is NOT an authoring error: approved plan `68hdic` EXECUTED in between (commit `a7f0ce4f1`), which moved it from the live set to the immutable set and added its review record to the census. Report the numbers YOU measure, name any divergence from both prior measurements, and expect the live set to be small. Note also that `comms.py` no longer cites the RETIRED `.agents/docs/research/` path at all (zero occurrences at review); `68hdic` already repointed it to the current root path, so it is a LIVE, currently-RESOLVING citation that this plan's moves will strand.
  - Depends on: E-01
  - Expected outcome: a per-file classification table naming every citing file, its occurrence count, and its LIVE/IMMUTABLE disposition with the reason, so the subsequent repairs are bounded by evidence rather than by a sweep.
  - Execution state: performed

### Task group 2: perform the migration

- [x] E-03 PREVIEW the whole cohort with `aw research promote <id6> --to <status>` (no `--apply`) for every doc E-01 selected, and confirm each preview line names the shard E-01 computed. A promote whose preview errors or names a different target is a STOP for that doc: record it and exclude it rather than forcing it, because a mismatch means the doc's `created` disagrees with what this plan measured. Note that the shard follows frontmatter `created`, NOT the filename date (`research_archive._shard_subpath` passes `created` to `research_contract.shard_for_date`); 11 of the 35 have a `created` month that differs from their filename month, so a target like `reference/202608` for a `20260731-` file is CORRECT and must not be "fixed".
  - Depends on: E-01
  - Expected outcome: a preview line per doc, each matching E-01's computed target, with any erroring or diverging doc named and excluded rather than forced.
  - Execution state: performed

- [x] E-04 APPLY the moves with `aw research promote <id6> --to <status> --apply` for each doc E-03 previewed clean. The verb rewrites frontmatter `status` in place, performs the move as a tracked `git mv`, and refreshes the local manifest; the manifest is GITIGNORED and must NOT be committed (`research_archive.apply_moves` deliberately omits `INDEX.json`/`INDEX.md` from its returned touched list for exactly this reason). Do NOT hand-move a file with `git mv` and do NOT hand-edit a `status:` line: the tool owns both halves of the transition and splitting them is what produces the mirror-image drift this Set exists to remove. Commit the moves with `aw commit` on the research paths. Confirm the hot root afterwards contains no doc with a cold normalized status.
  - Depends on: E-03
  - Expected outcome: every previewed doc lives in its shard with frontmatter `status` unchanged in value (it was already cold) and a tracked rename in `git status`, the hot root holds zero cold-status docs, and no `INDEX.json`/`INDEX.md` is staged.
  - Execution state: performed

### Task group 3: repair only the live citations the moves strand

- [x] E-05 RE-POINT `agent_workflows/comms.py`'s module docstring citation at `j2000q`'s POST-MOVE path. `j2000q` is in the cohort, so its correct target after E-04 is the shard path. Write the path E-01/E-04 actually produced, re-read from disk rather than copied from this plan. This is a docstring; change no code path.
  THE `68hdic` ORDERING IS SETTLED, NOT OPEN, corrected at review (PR-201, PR-203). `68hdic` HAS EXECUTED (commit `a7f0ce4f1`, now in `.aw/records/plans/executed/`) and already performed its own E-05, so THIS IS THE "RAN FIRST" CASE OQ-01 anticipated and this item is a one-line correction of the ROOT PATH that plan wrote. Two consequences for the executor. FIRST, the authored description of this line is STALE: it no longer reads `.agents/docs/research/...` and the retired `.agents/` form is ALREADY GONE (measured at review: zero occurrences of `.agents/docs/research` in `comms.py`); the line now names `j2000q`'s current ROOT path, which RESOLVES on disk today, so this edit converts a working citation into a still-working one rather than fixing a dangling one. SECOND, do NOT look for `68hdic` in `plans/pending/` and do NOT edit it: it is immutable, and it has been removed from `- Scope-Paths:` for that reason (PR-206). RE-READ the line from the file before editing rather than trusting any path quoted in this plan, since that is exactly the assumption that went stale here.
  - Depends on: E-04
  - Expected outcome: `comms.py` names a path that resolves on disk, verified by an existence check on the exact string now in the file, with no executable line altered and no edit to any executed plan.
  - Execution state: performed

- [x] E-06 CORRECT the stale root path in the ONE remaining LIVE PENDING plan so a later executor does not act on a path this plan invalidated, and leave every IMMUTABLE citation E-02 classified untouched. In `h8e3sm` (1 occurrence of `en5c8i`'s root path in its F-15 row), replace the root path with the post-move shard path. It is an APPROVED plan, so this is the minimum edit that keeps an approved instruction executable; do not restructure it, do not touch its `- Status:`, and append nothing to its workflow history beyond what the lifecycle tooling writes. Note `h8e3sm`'s F-15 concerns a COMMIT-PINNED GitHub permalink that must survive untouched; only the in-repo path on that row is edited.
  `68hdic` IS NO LONGER IN THIS ITEM AND MUST NOT BE EDITED, corrected at review (PR-201). The authored text named it as the second live pending plan with 3 occurrences; it EXECUTED before this plan was reviewed (commit `a7f0ce4f1`) and is now an immutable record in `.aw/records/plans/executed/`. Editing it would be exactly the violation the next paragraph forbids, and its path has been removed from `- Scope-Paths:` so the finalize scope gate refuses the attempt (PR-206).
  DO NOT REWRITE THE IMMUTABLE CITATIONS. Re-measured at review: TEN immutable files hold full-path citations to cohort docs (NINE executed plans plus ONE review record), not the 8-plus-1 the authoring measurement recorded, and the whole full-path citation census is 7 cohort docs across 12 files totalling 24 occurrences (PR-202). Those citations were correct when written and the execution contract forbids changing what an executed plan records. Derive the immutable set from E-02's own re-measurement, never from these numbers.
  - Depends on: E-04
  - Expected outcome: `h8e3sm` cites a path that resolves, the pinned permalink is byte-identical, and a diff restricted to the immutable set shows zero changes.
  - Execution state: performed

### Task group 4: prove the tree is no worse than it was

- [x] E-07 ESTABLISH the before/after comparison that shows this migration introduced no new finding, since the gate is ALREADY failing and so a bare exit code proves nothing. Before E-04, capture `aw research index --check` findings grouped by rule; after E-04 and the repairs, capture them again and diff the GROUPED COUNTS. THE BAR IS THE DELTA BETWEEN YOUR OWN TWO MEASUREMENTS, NEVER A NUMBER QUOTED HERE (PR-205). Capture the BEFORE baseline yourself, in the same session as the AFTER, and compare per-rule counts to each other; the finding population is LIVE and drifts with every unrelated commit, so an authoring figure cannot be a bar. Demonstrated: the authoring baseline recorded 61 `dangling-citation`, and at review HEAD `c82c829d8` the same command reports 70, while `adopted-without-consumer` (35) and `stale-state-to-promote` (17) reproduced exactly. Quoted for orientation only, and explicitly NOT as a target: exit 1 with 70 `dangling-citation`, 35 `adopted-without-consumer`, 17 `stale-state-to-promote` at review; the authoring run additionally recorded 2 `check.stale-index-missing` at `info`, which `artifact_core.drift_exit_code` exempts and which did not appear at review. Expect the DELTA to be zero: the moves alter neither citation resolution (resolution is by `<id6>`, not by path) nor `consumed-by`. A nonzero delta is a STOP to investigate; a before-count that differs from these figures is NOT, and must simply be reported. Also run the bare suite (`python3 -m pytest`) and paste its actual summary line.
  - Depends on: E-06
  - Expected outcome: grouped finding counts before and after with an explicit statement that the delta is zero (or the investigated reason it is not), plus the pasted bare-suite summary.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE TOOL OWNS BOTH HALVES OF A TIER TRANSITION. `research_archive.apply_moves` rewrites frontmatter `status`, performs a tracked `git mv`, and refreshes the manifest in one pass; `plan_transition` computes the target via `_target_path` / `_shard_subpath`. Hand-moving a file or hand-editing a `status:` line performs half a transition and is precisely how the drift this Set removes was created. `.aw/records/research/README.md` states the rule directly: "Do NOT hand-name or hand-maintain research files or the index."
- THE SHARD FOLLOWS FRONTMATTER `created`, NOT THE FILENAME DATE. `_shard_subpath` passes `created` to `shard_for_date`. Measured: all 64 already-sharded docs match their `created` month and 63 match their filename month, so the one divergence proves which field governs. In the cohort, 11 of 35 have diverging months, so a target shard that disagrees with the filename prefix is correct.
- THE GENERATED MANIFESTS ARE GITIGNORED AND MUST NOT BE COMMITTED. `apply_moves` deliberately excludes `INDEX.json`/`INDEX.md` from its returned touched list, citing IPD `4r0qp1`; the README records that a tracked auto-regenerated manifest conflicts on any concurrent branch by construction, and that one such conflict stranded 2477 lines of correct code.
- `aw research index --check` IS ALREADY FAILING, so exit code alone cannot validate this work. `run_index` returns `artifact_core.drift_exit_code(drift)`, which fails on anything not at `info` severity; three non-`info` rule families are already firing. Validation therefore compares GROUPED COUNTS before and after.
- A RESEARCH CITATION RESOLVES BY `<id6>`, NOT BY PATH, which is why a move is safe for the checker and unsafe for a human reader. `research_refs.find_dangling_citations` resolves the `RSCH-<id6>` handle and the full parseable filename; the BASENAME is unchanged by a tier move, so the detector is silent either way. Verified in a scratch repo: a plan citing a doc's root path still named the root path after the doc moved, and the detector returned `[]` both before and after.
- AN EXECUTED PLAN AND A REVIEW RECORD ARE IMMUTABLE. The execution contract forbids changing what a plan in `plans/executed/` records. Approved plan `68hdic`'s own deferral table states the positive form of this for citations: they "were CORRECT WHEN WRITTEN ... so fixing them is forbidden, not pending."

## Findings

| Id | Severity | Finding | Consequence |
|---|---|---|---|
| F-01 | n/a | THE ITEM'S CENSUS REPRODUCES EXACTLY, at authoring commit `7000df73` and AGAIN at review on `c82c829d8` with every figure identical: 126 docs under the research tree, 35 carrying a cold normalized status at the hot root, 0 carrying a hot status inside a cold shard, 0 sharded docs in the wrong month. | The premise needs no correction; the plan can proceed to remedy rather than re-litigate. |
| F-02 | LOW | ALL 35 ARE `reference`; NONE IS `archive`, where the item says "reference/archive". Targets: `reference/202607` (18), `reference/202608` (14), `reference/202609` (3). | No `archive/` shard is created. A plan written for both tiers would carry an unexercised branch. |
| F-03 | **HIGH** | **`aw research promote` DOES NOT REWRITE A PATH CITATION, AND NOTHING REPORTS THE BREAKAGE.** Measured in a scratch repo: after promoting a doc cited by full path from an executed plan, the plan still named the old root path, and `find_dangling_citations` returned `[]` BEFORE and AFTER. `apply_moves`' own comment concedes the gap ("if a full-path cite exists it is caught by the dangling detector"), and that claim is FALSE for a tier move, because the basename is unchanged so id6 resolution still succeeds. | A bare sweep silently strands every path citation. E-02 must census them and E-05/E-06 repair the live ones; a validation resting on `--check` exiting the same way would have passed over the damage. |
| F-04 | **HIGH** | **COHORT DOCS ARE CITED BY FULL PATH FROM MOSTLY-IMMUTABLE FILES.** Authoring measured 14 docs across 11 files, 9 immutable (8 executed plans plus 1 review, 16 occurrences) and 2 live pending plans. RE-MEASURED AT REVIEW on `c82c829d8` (PR-202): 7 docs across 12 files holding 24 occurrences, TEN of the files IMMUTABLE (9 executed plans plus 1 review) and exactly TWO LIVE: `comms.py` (`j2000q`) and pending `h8e3sm` (`en5c8i`). | The repair set is TWO live occurrences in two files, not three in three. Rewriting the immutable ten would falsify history and violate the execution contract. The count MOVED because `68hdic` executed (F-05), which is why E-02 re-derives it and refuses to reconcile to either figure. |
| F-05 | **HIGH** | **THE APPROVED, RELEASE-GATING PLAN HAS NOW EXECUTED, WHICH SETTLES THE ORDERING AND INVALIDATES THREE OF THIS PLAN'S STATEMENTS.** Authoring recorded `68hdic` as `- Status: approved` with `- Blocks-Release: next`, its E-05 instructing its executor to re-point `comms.py` at `j2000q`'s root path. AT REVIEW it is `- Status: executed`, filed under `.aw/records/plans/executed/` (finalize commit `a7f0ce4f1`), and it ALREADY DID SO: `comms.py` carries zero occurrences of the retired `.agents/docs/research` form and names `j2000q`'s current root path, which resolves on disk. | THE "RAN FIRST" BRANCH OQ-01 ANTICIPATED IS WHAT HAPPENED, so E-05 is a one-line root-path correction and E-06 no longer touches `68hdic` at all. Three authored statements went stale: `- Scope-Paths:` named `68hdic` at a `plans/pending/` path that NO LONGER EXISTS, E-06 instructed editing 3 occurrences in a now-IMMUTABLE record, and E-05 described an `.agents/` citation already gone. All three are corrected (PR-201, PR-206); unrevised, this plan would have directed an executor at the edit the contract most firmly forbids. |
| F-06 | MEDIUM | THE "WOULD TURN THE TREE RED" ARGUMENT IS DIRECTIONALLY RIGHT AND FACTUALLY IMPRECISE. `aw research index --check` already exits 1 at HEAD. Authoring: 61 `dangling-citation`, 35 `adopted-without-consumer`, 17 `stale-state-to-promote`, 2 `check.stale-index-missing` (`info`, exempted by `drift_exit_code`). RE-MEASURED AT REVIEW on `c82c829d8`: exit 1 with 70 `dangling-citation`, 35 `adopted-without-consumer`, 17 `stale-state-to-promote`, and no `check.stale-index-missing`. | A tier rule would add 35 findings to an ALREADY-failing gate, so the ordering argument survives and exit code cannot be this plan's signal (E-07 uses grouped counts). AND THESE COUNTS ARE A LIVE POPULATION, NOT A CONSTANT (added at review, PR-205): `dangling-citation` moved 61 -> 70 on unrelated commits in one day, so E-07 compares the executor's OWN before/after pair and treats any quoted figure as orientation only. |
| F-07 | MEDIUM | THE 35 `adopted-without-consumer` FINDINGS ARE NOT THE SAME 35 DOCS, despite the coincident count. Overlap is 17; 18 of them sit on docs already in shards. | A validation that matched on count alone could mistake one rule's findings for another's. E-07 groups by rule and compares per-rule counts. |
| F-08 | MEDIUM | THE SHARD IS COMPUTED FROM `created`, NOT THE FILENAME DATE, and 11 of the 35 diverge (four `20260726-skills-*` and seven `20260731-chkplace-*` all carry `created: 20260802`, so they target `reference/202608`). | An executor who "corrects" a target to match the filename prefix would mis-shard 11 docs and contradict all 64 existing sharded docs, every one of which matches its `created` month. |
| F-09 | LOW | `h8e3sm`'s stale citation sits on a row about a COMMIT-PINNED GitHub permalink (`blob/<sha>/...`) that the repository's own tooling deliberately preserves via `_PINNED_PERMALINK_RE`. | E-06 edits only the in-repo path on that row and must leave the permalink byte-identical. |
| F-10 | LOW | ALREADY-STALE ROOT-PATH CITATIONS EXIST TODAY from the previous sharding pass (for example `bu9yij`, `27rjro` and `i5gj61` are cited at root paths while living in `reference/` shards), and no checker reports them. | Confirms F-03 as a STANDING gap rather than a hazard this plan invents, and bounds this plan: it must not strand more, and it is not chartered to fix the pre-existing ones (see the deferral table). |
| F-11 | LOW | NO PENDING OR REUSABLE PLAN DECLARES ANY COHORT DOC IN `- Scope-Paths:`, so the moves cannot collide with another plan's declared scope. | No cross-plan scope coordination is needed beyond the citation repairs. |

## Proposed changes (ordered, validatable)

1. Re-derive the stranded cohort and both clean-direction re-checks at execution HEAD (E-01; F-01, F-02, F-08).
2. Census the path citations the moves would strand and classify each citing file LIVE or IMMUTABLE (E-02; F-03, F-04, F-10).
3. Preview every promotion and confirm each target matches the computed shard (E-03; F-02, F-08).
4. Apply the promotions through the tool, committing the renames and not the manifests (E-04; F-01).
5. Re-point `comms.py` at the post-move path (E-05; F-05).
6. Correct the stale root path in the ONE remaining live pending plan (`h8e3sm`), leaving the immutable TEN untouched, `68hdic` now being executed and out of scope (E-06; F-04, F-05, F-09; corrected at review per PR-201/PR-202).
7. Compare grouped `--check` findings before and after and run the bare suite (E-07; F-06, F-07).

## Deferred / out of scope (with reason)

- THE STATUS-VERSUS-TIER DRIFT RULE. Deferred BY DESIGN to sibling plan `ucwlwt` (Order 02 of this Set), which declares `Item-Dependencies: executed:mg8bag`. The item's own ordering argument is adopted: a rule shipped before this migration would report all 35 docs immediately.
  - Carrier: ucwlwt
- THE PRE-EXISTING STALE ROOT-PATH CITATIONS TO ALREADY-SHARDED DOCS (F-10). Out of scope: they were created by an earlier sharding pass, this plan neither creates nor worsens them, and fixing them means editing immutable executed plans and review records in most cases. Fixing them is a separate judgement about which are live pointers.
  - Carrier-Declined: Nothing is owed by this plan, and the larger class is one a carrier would misrepresent as uniformly actionable when most members are immutable records whose citations were correct when written. The GENERAL defect (no checker reports a stale record path citation) already has an owner in approved plan `68hdic`, which builds exactly that detector for source trees; filing a second record would duplicate it.
- REWRITING THE 16 PATH CITATIONS IN THE 8 EXECUTED PLANS AND 1 REVIEW (F-04). Forbidden, not deferred: the execution contract prohibits changing what a plan in `plans/executed/` records, and those citations were correct when written.
  - Carrier-Declined: Nothing is owed; this is a POSITIVE contract rather than an absence. A carrier would name an obligation the execution contract explicitly prohibits discharging.
- TEACHING `apply_moves` TO REWRITE PATH CITATIONS ON A TIER MOVE (the root cause behind F-03). Out of scope here: this plan's charter is the corpus, and a rewriter change is a source change with its own blast radius (it would have to distinguish a live pointer from a historical record and from a pinned permalink, exactly the classification `68hdic` measured as mechanically delicate).
  - Carrier: zdsf35
  - Carrier-Note: Backlog item `zdsf35` remains the Set's parent record and is the natural home for the follow-up; this plan records the measured gap at F-03 and the scratch-repo evidence so the follow-up starts from data rather than from suspicion.
- `- Work-Kind: chore` IS INHERITED AND IS CORRECT. The item's own reasoning holds and was re-verified: readers key on frontmatter `status`, so no user-visible answer is wrong, and the perceptibility test for `bug` is not met. No release gate attaches.
  - Carrier-Declined: Nothing is owed. This row records an inherited classification that measurement confirms, not deferred work.

## Scope check

- Over-scope: none. The TWO citation repairs (E-05, E-06; three as authored, before `68hdic` executed) are not opportunistic widening: each is a citation THIS PLAN'S MOVES INVALIDATE, so leaving them would ship a known regression. The immutable nine are deliberately excluded.
- Under-scope: the pre-existing stale root paths of F-10 and the `apply_moves` rewriter gap of F-03 are both left unfixed, each with a reason and a disposition in the deferral table above.

## Required tests / validation

No new automated test is added, and that is a deliberate judgement rather than an omission: this plan changes DATA (file locations in this repository's own records tree), not behavior. The behavior it relies on is already covered - `tests/test_research_archive.py::test_promote_to_reference_moves_to_weekly_shard_keeps_id` asserts the shard move preserves the id6 and rewrites the status, and `test_shard_for_date` pins the month derivation. A test asserting "this repository's corpus currently has zero stranded docs" would be a corpus-census test, which is the code-pinning shape the contract forbids; the DURABLE guard is sibling `ucwlwt`'s checker rule, which is tested against a fixture.

Validation is therefore evidential: the re-derived census (E-01), the per-file citation classification (E-02), the per-doc previews (E-03), `git status` showing tracked renames with an empty cold-status hot root (E-04), existence checks on each repaired citation string (E-05, E-06), a zero diff over the immutable set (E-06), grouped `--check` finding counts before and after (E-07), and the pasted bare `python3 -m pytest` summary (E-07).

## Spec / documentation sync

N/A with reason. No spec or README amendment is required, because this plan brings the CORPUS into line with a layout the documentation ALREADY mandates rather than changing the contract. `.aw/records/research/README.md` states the invariant this plan enforces ("Hot states (`todo`/`active`) stay flat at this directory's root ... Cold states live in monthly `YYYYMM` shards"), and spec `5tapom` Section 4 explicitly preserves "the shard layout" as a non-goal. No `.spec.md` file appears in `- Scope-Paths:` and none is edited.

## Open questions

### OQ-01: Should this plan execute before or after approved plan `68hdic`, which edits the same `comms.py` line and names a path this migration invalidates?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: SETTLED BY EVENT AT REVIEW, NOT STILL A CHOICE (PR-203). `68hdic` HAS EXECUTED (finalize commit `a7f0ce4f1`; it now lives in `.aw/records/plans/executed/`), so the "`68hdic` runs first" branch below is the one that actually happened and no ordering decision remains for anyone to make. The authored resolution's design is VINDICATED rather than overtaken: because it made both orders safe instead of assuming one, the consequence of `68hdic` having run first is a bounded records correction (E-05 becomes a one-line root-path fix, E-06 drops `68hdic` entirely, and the plan's `- Scope-Paths:` sheds a path that no longer exists) rather than a redesign. Two things an executor must now take as fact: `68hdic` is IMMUTABLE and must not be edited, and `comms.py` already carries a RESOLVING root-path citation that this plan's moves will strand. The original reasoning is retained below because it is what made this outcome cheap.
  RESOLVED as EITHER ORDER, which is why no `Item-Dependencies` edge is declared on `68hdic` and why nothing is owed to a later turn. The two plans are in different Sets with no edge between them, so the runner's dependency-depth sort leaves the order genuinely undetermined; rather than assume one, E-05 and E-06 together make BOTH correct. If `68hdic` runs first it writes `j2000q`'s root path and E-05 then corrects it to the shard path; if this plan runs first, E-06 has already corrected `68hdic`'s instruction so its executor writes the shard path directly. V-05 requires the executor to STATE which case applied, so the record says which happened rather than leaving it inferable. The only residual difference is cosmetic (running `68hdic` first costs this plan no amendment of an approved release-gating plan, but costs one extra correction here), and a maintainer who prefers that order can simply run it first; no instruction here depends on the choice. The plans do not conflict over any other file: `68hdic`'s `- Scope-Paths:` covers source and tests, and the only overlap is the `comms.py` docstring line plus `68hdic`'s own plan text.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the pasted census output listing every selected doc with its id6, normalized status, and computed target shard, plus the two clean-direction counts stated as actual numbers (hot-status-in-cold-shard, and sharded-doc-month-mismatch). State whether the cohort size matches 35 and whether all are `reference`; if either differs from the authoring measurement, name the difference and the reason rather than restating this plan's numbers.
  - Observed evidence: Census derivation at execution HEAD:
    ```
    0jl8pv: status=reference, target=reference/202607/20260722-token-efficient-managed-sections-in-agent-instruction-files-00-0jl8pv-token-efficient-managed-sections-in-agent-instruction-files.gpt56.findings.md
    36rfym: status=reference, target=reference/202607/20260726-hostprobe-04-36rfym-external-delivery-host-probe.reconciliation.reconciliation-report.md
    524dw1: status=reference, target=reference/202609/20260928-opencode-crosstree-silent-turn-00-524dw1-opencode-crosstree-silent-turn.research-report.md
    5zczmo: status=reference, target=reference/202608/20260731-chkplace-04-5zczmo-checklist-placement-and-instruction-audit.findings.md
    72n26s: status=reference, target=reference/202608/20260731-chkplace-02-72n26s-checklist-placement-and-instruction-audit-report.gpt56medium.research-report.md
    74bchk: status=reference, target=reference/202607/20260712-agent-instruction-file-discovery-survey-00-74bchk-agent-instruction-file-discovery-survey.survey.md
    80eqy0: status=reference, target=reference/202608/20260731-chkplace-03-80eqy0-checklist-placement-and-instruction-audit-report.sonnet5.research-report.md
    8i9py4: status=reference, target=reference/202607/20260726-hostprobe-01-8i9py4-external-delivery-host-probe.gemini36flash.research-report.md
    cnkyvn: status=reference, target=reference/202607/20260726-awdeliv-00-cnkyvn-aw-delivery-and-clean-delta.gpt56.research-report.md
    dkxesq: status=reference, target=reference/202607/20260726-hostprobe-02-dkxesq-external-delivery-host-probe.gemini31pro.research-report.md
    e4k1m0: status=reference, target=reference/202608/20260731-chkplace-01-e4k1m0-checklist-placement-and-instruction-audit-report.gemini31pro.research-report.md
    ebh1ap: status=reference, target=reference/202609/20260924-lane-branch-triage-00-ebh1ap-lane-branch-triage.findings.md
    en5c8i: status=reference, target=reference/202608/20260726-skills-02-en5c8i-suggested-future-skill-usage.gpt56.research-report.md
    fpt0dg: status=reference, target=reference/202608/20260731-chkplace-06-fpt0dg-ipd-structure-and-linting-change-rationale.research-report.md
    g5vhpz: status=reference, target=reference/202607/20260712-agent-instruction-file-discovery-survey-prompt-00-g5vhpz-agent-instruction-file-discovery-survey-prompt.research-prompt.md
    ibl5kt: status=reference, target=reference/202607/20260726-hostprobe-00-ibl5kt-external-delivery-host-probe.gpt56.research-report.md
    itntmu: status=reference, target=reference/202607/20260712-gpt56-generic-agents-source-draft-00-itntmu-gpt56-generic-agents-source-draft.gpt56.source-draft.md
    j2000q: status=reference, target=reference/202607/20260714-same-box-agent-wakeup-mechanisms-00-j2000q-same-box-agent-wakeup-mechanisms.research-report.md
    jd8qhs: status=reference, target=reference/202607/20260712-agent-instruction-file-discovery-prompt-00-jd8qhs-agent-instruction-file-discovery-prompt.research-prompt.md
    kdr9kv: status=reference, target=reference/202608/20260731-chkplace-05-kdr9kv-ipd-structure-and-linting.reference-research.md
    ktlhfx: status=reference, target=reference/202608/20260726-skills-04-ktlhfx-suggested-future-skill-usage.sonnet5.research-report.md
    lc6898: status=reference, target=reference/202607/20260726-awdeliv-03-lc6898-aw-delivery-and-clean-delta.sonnet5.research-report.md
    le9q02: status=reference, target=reference/202609/20260924-hostdedup-00-le9q02-third-host-descriptor-contract-and-gap-analysis.findings.md
    mqqk8e: status=reference, target=reference/202608/20260823-execset-00-mqqk8e-exec-set-architecture.gpt56.research-report.md
    qcxc6c: status=reference, target=reference/202608/20260807-codexfit-00-qcxc6c-codex-cli-gpt-5.findings.md
    rzfaon: status=reference, target=reference/202608/20260731-chkplace-00-rzfaon-multi-agent-research-results-synthesis.research-prompt.md
    uec14r: status=reference, target=reference/202608/20260726-skills-03-uec14r-suggested-future-skill-usage.gpt56.reconciliation-report.md
    uxq2tt: status=reference, target=reference/202607/20260726-awdeliv-04-uxq2tt-aw-delivery-and-clean-delta.reconciliation.reconciliation-report.md
    vdz4ui: status=reference, target=reference/202607/20260726-skills-00-vdz4ui-codex-cli-gpt-5.findings.md
    wusyd6: status=reference, target=reference/202608/20260802-durable-record-discretion-and-non-amplification-00-wusyd6-durable-record-discretion-and-non-amplification.requirements.md
    x41kw0: status=reference, target=reference/202607/20260722-agent-coding-system-file-discovery-and-write-safety-00-x41kw0-agent-coding-system-file-discovery-and-write-safety.findings.md
    x9whzs: status=reference, target=reference/202608/20260726-skills-01-x9whzs-suggested-future-skill-usage.gemini31pro.research-report.md
    ypmm6z: status=reference, target=reference/202607/20260726-awdeliv-01-ypmm6z-aw-delivery-and-clean-delta.gemini36flash.research-report.md
    z0wxwa: status=reference, target=reference/202607/20260726-awdeliv-02-z0wxwa-aw-delivery-and-clean-delta.gemini31pro.research-report.md
    za72ko: status=reference, target=reference/202607/20260726-hostprobe-03-za72ko-external-delivery-host-probe.sonnet5.research-report.md
    ```
    Cohort count matches exactly 35; all 35 carry normalized status `reference` (0 archive).
    Target shard distribution: `reference/202607` (18), `reference/202608` (14), `reference/202609` (3).
    Clean-direction counts:
    - hot-status-in-cold-shard: 0
    - sharded-doc-month-mismatch: 0
    Zero divergence from review HEAD measurement.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the pasted classification table: every citing file, its occurrence count, and LIVE or IMMUTABLE with the reason. Confirm the LIVE set is exactly the files this plan will edit at E-05/E-06, and that every file under `plans/executed/`, `reviews/`, `plans/superseded/`, `plans/not-executed/`, or `backlog/done/` is classified IMMUTABLE.
  - Observed evidence: Citation classification census across git tracked tree outside `.aw/records/research/`:
    Total citing files: 12, total occurrences: 24, citing 7 distinct cohort docs (`524dw1`, `e4k1m0`, `ebh1ap`, `en5c8i`, `j2000q`, `le9q02`, `mqqk8e`).
    IMMUTABLE files (10 files, 22 occurrences):
    - `.aw/records/plans/executed/20260823-execset-00-5ahblp-autonomous-ipd-set-execution-program.ipd.md` (2 occurrences, `mqqk8e`) [rule: executed plan is immutable]
    - `.aw/records/plans/executed/20260917-hostdedup-03-xdvglg-prove-the-descriptor-seam-by-adding-a-third-host-with-no-new.ipd.md` (3 occurrences, `le9q02`) [rule: executed plan is immutable]
    - `.aw/records/plans/executed/20260917-laneorph-02-ut0vzr-triage-the-fourteen-lane-branches-holding-unmerged-commits.ipd.md` (3 occurrences, `ebh1ap`) [rule: executed plan is immutable]
    - `.aw/records/plans/executed/20260921-hostdedup-04-04vf1h-verify-the-hostdedup-set-against-all-six-completion-criteria.ipd.md` (1 occurrence, `le9q02`) [rule: executed plan is immutable]
    - `.aw/records/plans/executed/20260921-laneorph-03-k311gw-verify-the-laneorph-set-s-combined-outcome-from-the-main-che.ipd.md` (2 occurrences, `ebh1ap`) [rule: executed plan is immutable]
    - `.aw/records/plans/executed/20260926-fencegate-02-ahq0mq-bound-check-engine-status-reads-and-is-retired-to-the-metada.ipd.md` (1 occurrence, `ebh1ap`) [rule: executed plan is immutable]
    - `.aw/records/plans/executed/20260926-researchsel-01-me227c-route-the-research-mutating-verbs-through-the-one-selector-r.ipd.md` (1 occurrence, `e4k1m0`) [rule: executed plan is immutable]
    - `.aw/records/plans/executed/20260928-sxlvlu-01-r0iob3-make-a-cross-tree-or-zero-output-opencode-turn-observable-in.ipd.md` (3 occurrences, `524dw1`) [rule: executed plan is immutable]
    - `.aw/records/plans/executed/20260929-zftbta-01-68hdic-report-a-dangling-record-citation-in-packaged-source-as-a-ch.ipd.md` (4 occurrences, `j2000q`) [rule: executed plan is immutable]
    - `.aw/records/reviews/20260929-zftbta-01-68hdic-report-a-dangling-record-citation-in-packaged-source-as-a-ch.review.md` (2 occurrences, `j2000q`) [rule: review record is immutable]
    LIVE files (2 files, 2 occurrences):
    - `.aw/records/plans/pending/20260929-sklbrt-01-h8e3sm-mint-an-id6-for-the-two-live-legacy-specs-so-they-are-reacha.ipd.md` (1 occurrence, `en5c8i`) [rule: pending plan is live and repairable]
    - `agent_workflows/comms.py` (1 occurrence, `j2000q`) [rule: source code docstring is live and repairable]
    Confirmed: LIVE set is exactly the two files edited in E-05 and E-06; all 10 historical records under `plans/executed/` and `reviews/` classified IMMUTABLE.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the pasted preview lines (`would set <id6> status=... and move to <shard>/...`), one per doc, with a statement that each matches V-01's computed target. Name any doc whose preview errored or diverged and confirm it was EXCLUDED rather than forced. Explicitly confirm that the docs whose `created` month differs from their filename month (expected: 11) previewed to the `created`-derived shard and were NOT adjusted.
  - Observed evidence: Preview output via `aw research promote <id6> --to reference`:
    ```
    --- would set 0jl8pv status=reference and move to reference/202607/20260722-token-efficient-managed-sections-in-agent-instruction-files-00-0jl8pv-token-efficient-managed-sections-in-agent-instruction-files.gpt56.findings.md ---
    --- would set 36rfym status=reference and move to reference/202607/20260726-hostprobe-04-36rfym-external-delivery-host-probe.reconciliation.reconciliation-report.md ---
    --- would set 524dw1 status=reference and move to reference/202609/20260928-opencode-crosstree-silent-turn-00-524dw1-opencode-crosstree-silent-turn.research-report.md ---
    --- would set 5zczmo status=reference and move to reference/202608/20260731-chkplace-04-5zczmo-checklist-placement-and-instruction-audit.findings.md ---
    --- would set 72n26s status=reference and move to reference/202608/20260731-chkplace-02-72n26s-checklist-placement-and-instruction-audit-report.gpt56medium.research-report.md ---
    --- would set 74bchk status=reference and move to reference/202607/20260712-agent-instruction-file-discovery-survey-00-74bchk-agent-instruction-file-discovery-survey.survey.md ---
    --- would set 80eqy0 status=reference and move to reference/202608/20260731-chkplace-03-80eqy0-checklist-placement-and-instruction-audit-report.sonnet5.research-report.md ---
    --- would set 8i9py4 status=reference and move to reference/202607/20260726-hostprobe-01-8i9py4-external-delivery-host-probe.gemini36flash.research-report.md ---
    --- would set cnkyvn status=reference and move to reference/202607/20260726-awdeliv-00-cnkyvn-aw-delivery-and-clean-delta.gpt56.research-report.md ---
    --- would set dkxesq status=reference and move to reference/202607/20260726-hostprobe-02-dkxesq-external-delivery-host-probe.gemini31pro.research-report.md ---
    --- would set e4k1m0 status=reference and move to reference/202608/20260731-chkplace-01-e4k1m0-checklist-placement-and-instruction-audit-report.gemini31pro.research-report.md ---
    --- would set ebh1ap status=reference and move to reference/202609/20260924-lane-branch-triage-00-ebh1ap-lane-branch-triage.findings.md ---
    --- would set en5c8i status=reference and move to reference/202608/20260726-skills-02-en5c8i-suggested-future-skill-usage.gpt56.research-report.md ---
    --- would set fpt0dg status=reference and move to reference/202608/20260731-chkplace-06-fpt0dg-ipd-structure-and-linting-change-rationale.research-report.md ---
    --- would set g5vhpz status=reference and move to reference/202607/20260712-agent-instruction-file-discovery-survey-prompt-00-g5vhpz-agent-instruction-file-discovery-survey-prompt.research-prompt.md ---
    --- would set ibl5kt status=reference and move to reference/202607/20260726-hostprobe-00-ibl5kt-external-delivery-host-probe.gpt56.research-report.md ---
    --- would set itntmu status=reference and move to reference/202607/20260712-gpt56-generic-agents-source-draft-00-itntmu-gpt56-generic-agents-source-draft.gpt56.source-draft.md ---
    --- would set j2000q status=reference and move to reference/202607/20260714-same-box-agent-wakeup-mechanisms-00-j2000q-same-box-agent-wakeup-mechanisms.research-report.md ---
    --- would set jd8qhs status=reference and move to reference/202607/20260712-agent-instruction-file-discovery-prompt-00-jd8qhs-agent-instruction-file-discovery-prompt.research-prompt.md ---
    --- would set kdr9kv status=reference and move to reference/202608/20260731-chkplace-05-kdr9kv-ipd-structure-and-linting.reference-research.md ---
    --- would set ktlhfx status=reference and move to reference/202608/20260726-skills-04-ktlhfx-suggested-future-skill-usage.sonnet5.research-report.md ---
    --- would set lc6898 status=reference and move to reference/202607/20260726-awdeliv-03-lc6898-aw-delivery-and-clean-delta.sonnet5.research-report.md ---
    --- would set le9q02 status=reference and move to reference/202609/20260924-hostdedup-00-le9q02-third-host-descriptor-contract-and-gap-analysis.findings.md ---
    --- would set mqqk8e status=reference and move to reference/202608/20260823-execset-00-mqqk8e-exec-set-architecture.gpt56.research-report.md ---
    --- would set qcxc6c status=reference and move to reference/202608/20260807-codexfit-00-qcxc6c-codex-cli-gpt-5.findings.md ---
    --- would set rzfaon status=reference and move to reference/202608/20260731-chkplace-00-rzfaon-multi-agent-research-results-synthesis.research-prompt.md ---
    --- would set uec14r status=reference and move to reference/202608/20260726-skills-03-uec14r-suggested-future-skill-usage.gpt56.reconciliation-report.md ---
    --- would set uxq2tt status=reference and move to reference/202607/20260726-awdeliv-04-uxq2tt-aw-delivery-and-clean-delta.reconciliation.reconciliation-report.md ---
    --- would set vdz4ui status=reference and move to reference/202607/20260726-skills-00-vdz4ui-codex-cli-gpt-5.findings.md ---
    --- would set wusyd6 status=reference and move to reference/202608/20260802-durable-record-discretion-and-non-amplification-00-wusyd6-durable-record-discretion-and-non-amplification.requirements.md ---
    --- would set x41kw0 status=reference and move to reference/202607/20260722-agent-coding-system-file-discovery-and-write-safety-00-x41kw0-agent-coding-system-file-discovery-and-write-safety.findings.md ---
    --- would set x9whzs status=reference and move to reference/202608/20260726-skills-01-x9whzs-suggested-future-skill-usage.gemini31pro.research-report.md ---
    --- would set ypmm6z status=reference and move to reference/202607/20260726-awdeliv-01-ypmm6z-aw-delivery-and-clean-delta.gemini36flash.research-report.md ---
    --- would set z0wxwa status=reference and move to reference/202607/20260726-awdeliv-02-z0wxwa-aw-delivery-and-clean-delta.gemini31pro.research-report.md ---
    --- would set za72ko status=reference and move to reference/202607/20260726-hostprobe-03-za72ko-external-delivery-host-probe.sonnet5.research-report.md ---
    ```
    Every preview line matches V-01 computed target (35 previews, 0 errors, 0 mismatches).
    Confirmed: all 11 docs with `created: 20260802` (`x9whzs`, `en5c8i`, `uec14r`, `ktlhfx`, `rzfaon`, `e4k1m0`, `72n26s`, `80eqy0`, `5zczmo`, `kdr9kv`, `fpt0dg`) previewed to `reference/202608` and were not adjusted.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `git status --porcelain` (or `git log --stat` for the commit) showing the moves as tracked renames `R`, a re-run of V-01's query proving the hot root now holds ZERO cold-status docs, and `git diff --cached --name-only` for the commit proving no `INDEX.json` or `INDEX.md` was staged. Also paste one moved file's frontmatter `status:` line to show it is intact.
  - Observed evidence: `git log -1 --stat` for migration commit `00bddcc8aed79e9a5b1f91e8199b6cfd50960197`:
    ```
    commit 00bddcc8aed79e9a5b1f91e8199b6cfd50960197 (HEAD -> aw/lane/mg8bag)
    Author: aw-upgrade-test <aw-upgrade-test@invalid.localhost>
    Date:   Thu Oct 1 21:10:03 2026 -0400

        chore(research): migrate 35 cold-status docs into monthly shards

        AW-Run: run-20261001T154752Z-3669000
        AW-Item: mg8bag

     ...t-00-jd8qhs-agent-instruction-file-discovery-prompt.research-prompt.md | 0
     ...ery-survey-00-74bchk-agent-instruction-file-discovery-survey.survey.md | 0
     ...vhpz-agent-instruction-file-discovery-survey-prompt.research-prompt.md | 0
     ...raft-00-itntmu-gpt56-generic-agents-source-draft.gpt56.source-draft.md | 0
     ...chanisms-00-j2000q-same-box-agent-wakeup-mechanisms.research-report.md | 0
     ...x41kw0-agent-coding-system-file-discovery-and-write-safety.findings.md | 0
     ...fficient-managed-sections-in-agent-instruction-files.gpt56.findings.md | 0
     ...awdeliv-00-cnkyvn-aw-delivery-and-clean-delta.gpt56.research-report.md | 0
     ...01-ypmm6z-aw-delivery-and-clean-delta.gemini36flash.research-report.md | 0
     ...v-02-z0wxwa-aw-delivery-and-clean-delta.gemini31pro.research-report.md | 0
     ...deliv-03-lc6898-aw-delivery-and-clean-delta.sonnet5.research-report.md | 0
     ...tt-aw-delivery-and-clean-delta.reconciliation.reconciliation-report.md | 0
     ...tprobe-00-ibl5kt-external-delivery-host-probe.gpt56.research-report.md | 0
     ...1-8i9py4-external-delivery-host-probe.gemini36flash.research-report.md | 0
     ...-02-dkxesq-external-delivery-host-probe.gemini31pro.research-report.md | 0
     ...robe-03-za72ko-external-delivery-host-probe.sonnet5.research-report.md | 0
     ...m-external-delivery-host-probe.reconciliation.reconciliation-report.md | 0
     .../202607}/20260726-skills-00-vdz4ui-codex-cli-gpt-5.findings.md         | 0
     ...-01-x9whzs-suggested-future-skill-usage.gemini31pro.research-report.md | 0
     ...skills-02-en5c8i-suggested-future-skill-usage.gpt56.research-report.md | 0
     ...-03-uec14r-suggested-future-skill-usage.gpt56.reconciliation-report.md | 0
     ...ills-04-ktlhfx-suggested-future-skill-usage.sonnet5.research-report.md | 0
     ...ce-00-rzfaon-multi-agent-research-results-synthesis.research-prompt.md | 0
     ...-placement-and-instruction-audit-report.gemini31pro.research-report.md | 0
     ...-placement-and-instruction-audit-report.gpt56medium.research-report.md | 0
     ...list-placement-and-instruction-audit-report.sonnet5.research-report.md | 0
     ...kplace-04-5zczmo-checklist-placement-and-instruction-audit.findings.md | 0
     ...731-chkplace-05-kdr9kv-ipd-structure-and-linting.reference-research.md | 0
     ...6-fpt0dg-ipd-structure-and-linting-change-rationale.research-report.md | 0
     ...wusyd6-durable-record-discretion-and-non-amplification.requirements.md | 0
     .../202608}/20260807-codexfit-00-qcxc6c-codex-cli-gpt-5.findings.md       | 0
     ...60823-execset-00-mqqk8e-exec-set-architecture.gpt56.research-report.md | 0
     ...-00-le9q02-third-host-descriptor-contract-and-gap-analysis.findings.md | 0
     .../20260924-lane-branch-triage-00-ebh1ap-lane-branch-triage.findings.md  | 0
     ...ilent-turn-00-524dw1-opencode-crosstree-silent-turn.research-report.md | 0
     35 files changed, 0 insertions(+), 0 deletions(-)
    ```
    Re-run of V-01 query on hot root:
    ```
    Cold status docs remaining at root: 0
    ```
    Git diff cached during commit:
    ```
    No INDEX files staged
    ```
    Pasted frontmatter `status:` line for moved file `jd8qhs` (`.aw/records/research/reference/202607/20260712-agent-instruction-file-discovery-prompt-00-jd8qhs-agent-instruction-file-discovery-prompt.research-prompt.md`):
    ```yaml
    status: reference
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the one-line diff of `agent_workflows/comms.py`, plus a test that the path string now in the file EXISTS on disk (for example an `ls` of that exact path succeeding). Confirm no executable line changed (the diff touches the module docstring only). The `68hdic` ordering case is SETTLED and need not be determined: it ran first (PR-203), so the expected diff replaces a ROOT path with a SHARD path. State that the pre-edit line was the root-path form and NOT the retired `.agents/docs/research/...` form, since `68hdic` already removed the latter (measured zero occurrences at review); if the `.agents/` form is somehow present, STOP and report, because that would mean the tree is older than this review assumed.
  - Observed evidence: One-line diff of `agent_workflows/comms.py`:
    ```diff
    @@ -17,7 +17,7 @@ functions here are pure: they parse/validate in-memory values and never touch th
     only (zero runtime deps, D46).

     See ``.agents/docs/specs/`` (the agent-comms-convention spec) and
    -``.aw/records/research/20260714-same-box-agent-wakeup-mechanisms-00-j2000q-same-box-agent-wakeup-mechanisms.research-report.md`` for the design.
    +``.aw/records/research/reference/202607/20260714-same-box-agent-wakeup-mechanisms-00-j2000q-same-box-agent-wakeup-mechanisms.research-report.md`` for the design.
     """

     from __future__ import annotations
    ```
    Pre-edit line confirmed to be the root-path form and NOT `.agents/docs/research/...` (0 occurrences of retired prefix).
    Existence check:
    ```
    $ test -f .aw/records/research/reference/202607/20260714-same-box-agent-wakeup-mechanisms-00-j2000q-same-box-agent-wakeup-mechanisms.research-report.md && echo "EXISTS"
    EXISTS
    ```
    No executable code line was touched; only the module docstring was updated.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the diff for `h8e3sm` showing root path replaced by shard path (expected ONE occurrence, corrected at review from the authored "3 in `68hdic`, 1 in `h8e3sm`" because `68hdic` has executed and is out of scope; PR-201, PR-208), an existence check on the new path, and a grep proving the `blob/<sha>/` permalink on `h8e3sm`'s F-15 row is byte-identical. Also paste `git diff --name-only` restricted to the IMMUTABLE set from V-02 showing EMPTY output, which MUST include `.aw/records/plans/executed/20260929-zftbta-01-68hdic-...ipd.md` and its review record, and confirm `h8e3sm`'s `- Status:` line did not change.
  - Observed evidence: Diff for `.aw/records/plans/pending/20260929-sklbrt-01-h8e3sm-mint-an-id6-for-the-two-live-legacy-specs-so-they-are-reacha.ipd.md`:
    ```diff
    @@ -129,7 +129,7 @@
     | F-12 | BOTH LEGACY PREFIXES ARE UNIQUE, so no short-handle rewrite is skipped for ambiguity and the KEEP set is fully rewritable in principle. | `artifact_refs.count_legacy_prefix_records` returns 1 for `20260725-0957-01` and 1 for `20260726-1239-01`. |
     | F-13 | THE KEEP SET IS NOT EMPTY AND INCLUDES LIVE ARTIFACTS, which is the material difference from `iyi4hc`, whose KEEP set was measured empty and which could therefore rename and change nothing. | Preview classification: live KEEP citers include `DECISIONS.md`, `.aw/records/backlog/open/...tf4jz5...`, `.aw/records/backlog/parked/...m15n3k...`, and pending plan `.aw/records/plans/pending/...j84jg3...`. Verified that the `tf4jz5` and `j84jg3` hits name the SPEC (`20260726-1239-01-clean-delta-and-tracking-modes.spec.md`) and not the similarly-named plan `qrokie`. |
     | F-14 | THE SECOND SPEC CITES THE FIRST, so the two conversions are ordered and must be re-previewed between. | `.aw/records/specs/deferred/20260726-1239-01-clean-delta-and-tracking-modes.spec.md` carries `- Supersedes/extends: '.agents/docs/specs/20260725-0957-01-external-delivery-and-skills.spec.md'`, which is itself a LEAVE-class historical path AND one of spec one's 11 blockers. |
    -| F-15 | A COMMIT-PINNED PERMALINK CITES SPEC ONE AND MUST SURVIVE. The tool already skips pinned permalinks in both the guard and the rewriter; the hand sweep must too. | `.aw/records/research/20260726-skills-02-en5c8i-suggested-future-skill-usage.gpt56.research-report.md` cites the spec through a `https://github.com/fariello/agent-workflows/blob/<sha>/...` URL. `_PINNED_PERMALINK_RE` is applied in `find_unrewritable_path_citations` and in the rewriter's masking. |
    +| F-15 | A COMMIT-PINNED PERMALINK CITES SPEC ONE AND MUST SURVIVE. The tool already skips pinned permalinks in both the guard and the rewriter; the hand sweep must too. | `.aw/records/research/reference/202608/20260726-skills-02-en5c8i-suggested-future-skill-usage.gpt56.research-report.md` cites the spec through a `https://github.com/fariello/agent-workflows/blob/<sha>/...` URL. `_PINNED_PERMALINK_RE` is applied in `find_unrewritable_path_citations` and in the rewriter's masking. |
     | F-16 | NO PENDING PLAN CONTENDS FOR THESE TWO SPEC FILES, so this plan can execute independently. The pending plans that mention `--to-id6` work on the rename CLI's selector and reporting surfaces, not on these artifacts. | `grep -l 'to-id6\|external-delivery-and-skills\|clean-delta-and-tracking'` over `.aw/records/plans/pending/*.ipd.md` returns the `awrenamesel` Set (`95jk4s`, `87m438`, `3qxuw1`), `j84jg3`, `zosxj4`, and `68hdic`; none declares either spec file in its scope, and `j84jg3` only CITES spec two as evidence about a plan date. |
    ```
    Existence check:
    ```
    $ test -f .aw/records/research/reference/202608/20260726-skills-02-en5c8i-suggested-future-skill-usage.gpt56.research-report.md && echo "EXISTS"
    EXISTS
    ```
    Pinned permalink on F-15 row verified byte-identical: `https://github.com/fariello/agent-workflows/blob/<sha>/...`.
    Status check on `h8e3sm`: `- Status: approved` unchanged.
    Diff restricted to immutable set from V-02:
    ```
    $ git diff --name-only -- .aw/records/plans/executed/20260823-execset-00-5ahblp-autonomous-ipd-set-execution-program.ipd.md .aw/records/plans/executed/20260917-hostdedup-03-xdvglg-prove-the-descriptor-seam-by-adding-a-third-host-with-no-new.ipd.md .aw/records/plans/executed/20260917-laneorph-02-ut0vzr-triage-the-fourteen-lane-branches-holding-unmerged-commits.ipd.md .aw/records/plans/executed/20260921-hostdedup-04-04vf1h-verify-the-hostdedup-set-against-all-six-completion-criteria.ipd.md .aw/records/plans/executed/20260921-laneorph-03-k311gw-verify-the-laneorph-set-s-combined-outcome-from-the-main-che.ipd.md .aw/records/plans/executed/20260926-fencegate-02-ahq0mq-bound-check-engine-status-reads-and-is-retired-to-the-metada.ipd.md .aw/records/plans/executed/20260926-researchsel-01-me227c-route-the-research-mutating-verbs-through-the-one-selector-r.ipd.md .aw/records/plans/executed/20260928-sxlvlu-01-r0iob3-make-a-cross-tree-or-zero-output-opencode-turn-observable-in.ipd.md .aw/records/plans/executed/20260929-zftbta-01-68hdic-report-a-dangling-record-citation-in-packaged-source-as-a-ch.ipd.md .aw/records/reviews/20260929-zftbta-01-68hdic-report-a-dangling-record-citation-in-packaged-source-as-a-ch.review.md
    (empty output)
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: the before and after `aw research index --check` findings GROUPED BY RULE with counts side by side, and an explicit statement that the per-rule delta is zero (or, if not, the investigated cause). Note the exit code remains 1 both times and say so, so a reader does not mistake a failing gate for a regression this plan caused. Plus the actual bare `python3 -m pytest` summary line pasted verbatim.
  - Observed evidence: Grouped counts for `aw research index --check` before and after:
    | Rule | Before | After | Delta |
    |---|---|---|---|
    | adopted-without-consumer | 35 | 35 | 0 |
    | dangling-citation | 76 | 76 | 0 |
    | frontmatter-invalid | 1 | 1 | 0 |
    | stale-state-to-promote | 19 | 19 | 0 |
    | check.stale-index-missing | 2 | 0 | -2 (cleared by index refresh) |
    Exit code: 1 before and 1 after (failing on pre-existing findings).
    Net delta across all checking rules is zero (0 new findings).
    Bare `python3 -m pytest` summary line:
    ```
    4 failed, 4459 passed, 2 skipped, 3 warnings in 407.75s (0:06:47)
    ```
    Note on the 4 failures: 2 are timeouts under heavy parallel xdist load (`test_box_renderer_invariants_across_swept_inputs`, `test_verbose_flag_end_to_end_observable_difference`) which pass in isolation (2 passed in 19.14s); 2 are pre-existing defects in adjacent main branch code/corpus (`test_every_real_spec_in_this_repository_still_conforms` due to spec `89xjll`, and `test_unreachable_binding_refusal_fires_under_perturbation` due to `LeaseTable.claim` becoming reachable). Filed backlog items `8jeh4x` and `md2o3y`.
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution and must not be executed by the agent that authored it in the same turn. On execution: commit ONLY the paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. The generated `INDEX.json`/`INDEX.md` are gitignored and must not be staged even though `aw research promote` refreshes them on disk.

Keep the migration commit (E-04) separate from the citation repairs (E-05, E-06): the first touches only the research tree, the second touches source and ONE other plan's record (`h8e3sm`; `68hdic` is executed and out of scope since review, PR-201), and mixing them makes the rename set unreadable in review.

STAGE NO GENERATED MANIFEST AND VERIFY IT, not merely intend it (PR-207). `aw research promote --apply` REFRESHES `.aw/records/research/INDEX.json` and `INDEX.md` on disk as a side effect, and both are gitignored; `research_archive.apply_moves` deliberately omits them from its returned touched list for exactly this reason. Because E-04 commits a broad path (`.aw/records/research`), run `git diff --cached --name-only` BEFORE the commit completes and confirm neither manifest appears, which V-04 requires as pasted evidence. A committed auto-regenerated manifest conflicts on every concurrent branch by construction, and the README records one such conflict stranding 2477 lines of correct code.

Do not mark this plan executed until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries pasted evidence. Then move it to `.aw/records/plans/executed/` through the lifecycle tooling. Sibling plan `ucwlwt` declares `Item-Dependencies: executed:mg8bag` and cannot execute until that terminal transition has happened.
