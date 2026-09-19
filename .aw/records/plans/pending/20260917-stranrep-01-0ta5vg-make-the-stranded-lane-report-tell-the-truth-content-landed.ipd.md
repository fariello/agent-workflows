# IPD: Make the stranded-lane report tell the truth: content-landed exclusion, one row per lane, no phantom worktree, live remedy

- Date: 2026-09-17
- Kind: child
- Concern: `aw attention` prints 19 STRANDED rows and `--check` fails closed, while NOT ONE of the 12 reported lanes holds work that needs recovering (triaged per lane 2026-09-18, evidence in backlog `kvf5xo`/`q96tpi`/`46fb5i`/`fci7yn`). FOUR DEFECTS IN THE REPORTING, all in the same ~60 lines, produce that.
  CORRECTED AT REVIEW, AND THE CORRECTION MATTERS BECAUSE IT CHANGES WHAT THIS PLAN CAN DELIVER. Two of this Concern's quantitative claims are wrong as of HEAD `7562ca6c`. FIRST, the counts moved: **25 rows over 17 distinct lanes**, not 19 over 12. SECOND and more importantly, "NOT ONE of the reported lanes holds work that needs recovering" is REFUTED by the very test this plan proposes: `git cherry` finds at least one commit genuinely absent from the target for **all 17** reported lanes, and a blob-identity check over each lane's touched files found ZERO files matching HEAD for the three sampled (`r2i1b1` 0/7, `03ie04` 0/5, `fn2l1u` 0/19). The six re-execution lanes ARE still reported (so the plan's premise that they are wrongly reported stands, and `tb63qv`'s review claim that they "appear ZERO times" is what is wrong), but their work reached `main` as DIFFERENT BYTES via reimplementation, which no patch-id or content-identity reading can see.
  WHAT SURVIVES THE CORRECTION, stated plainly so the plan is neither over- nor under-sold. Defects (2), (3) and (4) below are REAL, INDEPENDENT, and measurably fixable: the dedup key inflates 17 lanes to 25 rows, 19 of 25 rows name a worktree that is absent from disk (6 do exist), and the remedy probe can never be True. Defect (1) is a genuine spec violation in the ABSTRACT, and F3a really does forbid failing a landed lane, but the content reading proposed to fix it resolves nothing on today's corpus. E-08 now gates that half on a re-measurement and an explicit decision. The report after this plan will be SMALLER AND TRUER but still failing, because the lanes genuinely hold unlanded commits; closing them is `ut0vzr`'s disposition work. (1) THE LANDING TEST ANSWERS THE WRONG QUESTION, and this is a SPEC VIOLATION rather than a gap: spec `attention-registry-and-cross-tree-status` F3a already makes it NORMATIVE that "a lane whose work HAS reached the integration target MUST NOT fail it either", but the only landing test is `runner_shared.lane_work_has_landed` (runner_shared.py:1077-1107), a single `git merge-base --is-ancestor`, which sees ANCESTRY and is therefore blind to work that reached the target by RE-EXECUTION. Six of the twelve reported lanes are abandoned first attempts whose plan was re-executed on a SECOND lane: `03ie04`, `fn2l1u`, `mm5p3v`, `nna8yz`, `r2i1b1`, `ybkmzp`, each finalized on `main` by a commit its own dead lane is not an ancestor of (`bc9b3f43`, `e0c139ea`, `a912d5a9`, `14d5429a`, `84c5adcd`, `68930180`), each with the shipped symbol named in `kvf5xo`. (2) ONE LANE IS REPORTED ONCE PER RUN, because the dedup key includes `run_id` (runner_shared.py:1281-1285), so `7p9n2v`/`qcqhj7`/`rchpms` print 3 rows each and `58ha43` 2, turning 12 lanes into 19 violations. (3) EVERY ROW NAMES A WORKTREE THAT DOES NOT EXIST: all 19 print `.aw/worktrees/<id>` and zero of the 12 directories are on disk, because `lane_worktree_display` RECONSTRUCTS that string from the recorded absolute path to satisfy F8a's no-absolute-path rule (runner_shared.py:1345-1350) and nothing existence-checks it. (4) THE REMEDY NAMES A SHIPPED VERB AS MISSING: `attention.lane_remedy_hint` gates on `hasattr(oc_runipd, "cmd_integrate")` (attention.py:1312), a symbol that has NEVER existed (the real entry point is `handle_integrate_command`), so the stale "no `aw integrate` verb exists yet" prints unconditionally even though `aw oc integrate` shipped in executed plan `rl67b0` and is in `aw oc --help`; that steers an operator to a manual merge which SKIPS the merge-and-revalidate gate the verb routes through. NET: a gate permanently red on zero real losses, which is the alarm-fatigue outcome F3a's own "a check that fails on correct behavior is a check operators bypass" warns against, and which buries any FUTURE genuine strand.
- Scope: Fix the four reporting defects and amend F3a to match. Add a CONTENT-landed reading beside the ancestry one and consult both, so a re-executed lane is LANDED and silent; collapse the reported set to one row per lane branch while KEEPING the existing within-run collapse; existence-check the worktree before rendering it and omit it when absent; repair the dead `cmd_integrate` sentinel to probe a symbol that exists. AMENDS spec F3a to state the content-landed reading and the one-row-per-lane rule, declared in `Scope-Paths`. Does NOT change `describe_lane` (its body is pinned byte-for-byte against `tests/fixtures/runner_shared_premove_fingerprints.json` captured at HEAD `1ecc5891`, and `classify_lane_integration`'s docstring at runner_shared.py:1124-1130 records that editing it breaks a pure-move proof for an unrelated reason); does NOT change what `commits_ahead` MEANS, since `LANE_STALE`/`LANE_FOREIGN` adoption reads it; does NOT extend `SCAN_ROOTS` to `.aw/worktrees` or `.aw/records/runs`, which F3a forbids; does NOT delete, merge, prune or reclaim ANY lane, branch or worktree, so `aw attention` stays READ-ONLY per F3a and spec G3; and does NOT decide the DISPOSITION of the 12 currently-reported lanes, which is plan `ut0vzr`'s (`qliia1`).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/attention.py, tests/test_runner_shared.py, tests/test_attention.py, .aw/records/specs/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md, .aw/records/plans/pending/20260917-stranrep-01-0ta5vg-make-the-stranded-lane-report-tell-the-truth-content-landed.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: stranrep
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 0ta5vg
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved
- From-Backlog: kvf5xo
- Blocks-Release: next

## Workflow history
- 2026-09-19 note (opencode its_direct/pt3-claude-opus-5-1m-us): implementation performed and validated in lane `aw/lane/0ta5vg` at base HEAD `07dabf1b` under `aw oc run` (run-20260919T151802Z-3125140). All 8 E-items PERFORMED and all 8 V-items PASS with pasted evidence. The TERMINAL transition is deliberately NOT recorded here: `aw ipd finalize` owns it and the runner performs it for a managed lane (`aw ipd begin` in this lane refused with AW-LIFECYCLE-ROLE-001 for the same reason), so this is a `note` and the plan is left in `pending/` for the driver. E-08's gate was measured FIRST and recorded decision (ii) KEEP: `git cherry` silences 0 of 13 reported lanes (re-derived; the corpus moved again, 19/12 authored -> 25/17 at review -> 20 rows/13 lanes at execution), and the content reading was kept anyway because F3a's exclusion is NORMATIVE and because two live race remedies (`commit_lock` ISO_RACED, `ipd_lifecycle` RECONCILED_RACED) instruct operators to cherry-pick, making it a real forward-looking shape rather than a hypothetical; the zero present yield is stated in the helper's own docstring. MEASURED RESULT: rows 20 -> 13 (one per lane, max 1), 12 phantom worktree paths no longer printed while the 1 that exists still renders, and all 13 rows now name `aw oc integrate <id6>` where the probe could previously never be True. `aw attention --check` still exits 1, which is the CORRECT and expected outcome (F-9): every remaining lane holds commits genuinely absent by BOTH readings, and closing them is `ut0vzr`'s disposition work. The DIRTY-lane data-loss hazard is closed and double-pinned (a behavioral test plus a source-inspection test). Spec F3a AMENDED with four clauses (two-reading landing, three constraints on the content reading, one-row-per-lane, absent-worktree omission); spec `- Status:` unchanged at `implemented` and no transition attempted; `landed_by` stays internal so `SCHEMA_VERSION` stays 4. Suite: baseline `1 failed, 8368 passed` (the one failure a pre-existing flake that passes in isolation), after `8394 passed, 3 skipped, 2 xfailed`, fully green. TWO DEFECTS FOUND AND FILED: `i8wmte` (bug, high, blocks-release) `aw specs note` reports 'appended' but REPLACES the whole history section, and for a spec with no `- Id:` the gitignored sidecar gets nothing either, so the record is destroyed; the deleted `pr5b0t` record was restored here from git. `aqb4dv` (followup) carries OQ-03 so it survives this plan reaching `executed`. Five deferred rows also gained typed `Carrier`/`Carrier-Declined` fields, taking `check.ipd-uncarried-obligation` for this plan from 6 obligations to 0.

- 2026-09-19 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 all FIXED, none deferred, none open; Readiness go-pending-approval. Reviewed at HEAD 7562ca6c. Three of four diagnosed defects verified real and independently fixable (25 rows over 17 lanes, 19 of 25 worktree paths absent, dead cmd_integrate probe). THE FOURTH FIX HAS ZERO MEASURED YIELD: git cherry resolves 0 of 17 reported lanes because the six re-executions were REIMPLEMENTATIONS (blob identity 0/7, 0/5, 0/19), so E-08 now gates E-01/E-02/E-03 on a re-measurement plus an explicit keep/drop/stop decision. BLOCKER PR-001 fixed: E-02 would have silenced a DIRTY lane and lost uncommitted work (reproduced), so the content conclusion is now gated on not-dirty and empty cherry output no longer reads as landed. Also corrected: an unachievable Goal demanding exit 0 (17 lanes genuinely unlanded, exit 1 is the pass), E-05 naming the wrong code branch (25 of 25 records take the success path), a false cannot-measure-in-a-lane convention, an impossible implemented-spec transition, and an oldest-first history that tripped check.lifecycle-transition-invalid. Watermark 07 -> 08.
- 2026-09-17 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog kvf5xo (with q96tpi, 46fb5i, fci7yn), all four measured at HEAD d188eaad; spec F3a amendment declared; maintainer chose one cohesive plan over a Set.
- 2026-09-17 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the stranded-lane report TRUE: loud exactly once per lane that genuinely holds unintegrated work, naming only a worktree that exists and a remedy that exists, and silent for a lane whose work has demonstrably reached the target. This restores the gate's credibility BEFORE plan `ut0vzr` triages the currently reported lanes, so that triage is measured against a report that does not lie.

THE GOAL WAS CORRECTED AT REVIEW AND THE ORIGINAL WAS NOT ACHIEVABLE. It read "make `aw attention --check` silent when every lane's work is accounted for". Measured at HEAD `7562ca6c`: all 17 reported lanes hold commits absent from the target by BOTH the ancestry reading and the new content reading, so `--check` still exits 1 after every item in this plan lands (F-9). That is the CORRECT behavior, because the work really is unlanded; the report was over-counting and mis-describing those lanes, not inventing them. Silence is reached by DISPOSITION of the lanes, which belongs to `ut0vzr`, not by any predicate this plan can change. What this plan delivers is measurable and worth doing on its own: 25 rows become 17, 19 phantom worktree paths stop being printed, and the remedy names a verb that exists.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the landing question answer what F3a actually asks

- [x] E-08 RE-MEASURE THE CONTENT READING'S YIELD BEFORE BUILDING IT, AND STOP IF IT IS STILL ZERO. ADDED AT REVIEW, and it gates E-01/E-02/E-03 because the plan's central premise was REFUTED by measurement. Run `git cherry <target> <branch>` for EVERY currently reported lane (not only the six) in a tree that has run records, and report per lane the `-`/`+` counts and the resulting verdict.
  WHAT THE REVIEW MEASURED, at HEAD `7562ca6c` against the main checkout resolved via `attention._resolve_runs_repo_root`: **25 rows over 17 distinct lanes** (not the authored 19/12, which is a separate staleness point), and the content reading silences **0 of 17**. For each of the six named lanes `git cherry HEAD aw/lane/<id>` returned ONLY `+` lines: `03ie04` -0/+2, `fn2l1u` -0/+2, `mm5p3v` -0/+3, `nna8yz` -0/+3, `r2i1b1` -0/+1, `ybkmzp` -0/+2. So patch-id equality holds for NONE of them.
  WHY, ESTABLISHED RATHER THAN GUESSED, because the reason decides whether any reading can work. The second attempts were REIMPLEMENTATIONS, not cherry-picks. `r2i1b1`'s lane commit `81323cd6` and the commit that actually shipped its work on main, `ccc7e04c` ("feat(runs): surface every refusal with its remedy in the summary and aw runs (r2i1b1)"), carry DIFFERENT patch ids (`cafab0ff...` vs a different id, 1602 vs 1235 diff lines). Stronger still, a blob-identity check over every file each lane touched found **0 of 7** (`r2i1b1`), **0 of 5** (`03ie04`) and **0 of 19** (`fn2l1u`) files whose lane content matches HEAD. The plan's own F-6 anticipated this for `03ie04` alone at 8% overlap; measurement extends it to ALL SIX. The work landed, but as different bytes.
  THE DECISION THIS FORCES, to be recorded before E-01 is written. If the re-measurement still yields zero, then E-01/E-02 add a predicate, a field, a spec amendment and three test surfaces that change NO row in this repository, and the honest options are: (i) DROP E-01/E-02/E-03 and land only E-04/E-05/E-06, which are independently valid and measurably reduce 25 rows to 17; or (ii) keep them as a forward-looking guard for a genuine cherry-pick or rebase (a real integration shape the drivers can produce) while stating plainly that their yield on today's corpus is zero; or (iii) STOP and take the disposition question to the maintainer, since a report that correctly identifies 17 lanes holding genuinely-unlanded commits is not lying, and the remedy is `ut0vzr`'s triage rather than a predicate change. Do NOT loosen the predicate until the six resolve; that is the exact failure mode OQ-02 forbids and it would convert a true STRANDED into a false LANDED.
  - Depends on: none
  - Expected outcome: a per-lane table over every reported lane with `-`/`+` counts and verdict; the count silenced and the count remaining; and an explicit recorded choice among (i)/(ii)/(iii) with its reason, before any code is written.
  - Execution state: performed

- [x] E-01 Add a CONTENT-landed reading to `agent_workflows/runner_shared.py` as a NEW helper beside `lane_work_has_landed` (do NOT edit `describe_lane`, per the fingerprint pin cited in Scope; verified at review that `describe_lane` IS in the pin's `symbols` list while `lane_work_has_landed`, `classify_lane_integration`, `stranded_lane_records` and `lane_worktree_display` are NOT). Decide whether every commit the lane adds beyond its merge-base is already represented on the target using `git cherry <target> <branch>`, which compares PATCH IDS and therefore sees a cherry-pick or a rebase: a result whose every line begins `-` means landed, any `+` line means at least one commit is genuinely absent. Return the SAME three-valued `True`/`False`/`None` contract `lane_work_has_landed` documents, mapping git failure and unresolvable refs to `None` so an unanswerable question stays UNKNOWN and never reads as either answer.
  READ E-08 FIRST: MEASURED AT REVIEW, THIS READING RESOLVES ZERO OF THE SIX LANES THE PLAN WAS WRITTEN FOR, and zero of all 17 currently reported. Build it anyway only if E-08's measurement says it buys something; the honest expected yield today is nothing. See E-08 for the numbers and the decision it forces.
  TWO MANDATORY GUARDS ON THE PARSE, both measured at review, because the naive rule is unsafe:
  (a) EMPTY OUTPUT IS NOT LANDED. `git cherry` exits 0 with NO lines when the branch adds no commits the target lacks, and the stated rule "every line begins `-`" is VACUOUSLY TRUE on an empty list. A lane reaches the landing question whenever `holds_work` is True, and `holds_work` is `commits_ahead > 0 OR dirty` (`worktree_lease.LaneState.holds_work` over the `LANE_HOLDS_WORK` assignment), so a lane with ZERO commits and a DIRTY tree arrives here and empty output would silently read LANDED. Require at least one `-` line AND no `+` line; treat empty output as NOT-landed (fall through to the ancestry answer).
  (b) A NONZERO GIT EXIT IS `None`, NOT `False`. Verified: `git cherry <target> nosuchbranch` exits 128 with `fatal: unknown commit`. Check the return code before parsing, exactly as `lane_work_has_landed` checks `rev-parse --verify` on both refs first.
  - Depends on: E-08
  - Expected outcome: a helper returning True only when at least one commit is present by patch id and none is absent, False when at least one is absent OR the output is empty, None when either ref does not resolve or git errors.
  - Execution state: performed

- [x] E-02 Consult BOTH readings in `classify_lane_integration` so `LANE_STRANDED` is reached only when the work is absent by ancestry AND by content. Preserve the documented decision ORDER exactly (LIVE first, then EMPTY, then the landing question) and leave `LANE_ATTENTION_STATES` unchanged, so this NARROWS what is reported without inventing a reportable state. Record which reading settled it on the returned record (`landed_by`, values `ancestor`/`content`/None) for debuggability. PRESERVE THE FAIL-CLOSED DIRECTION: if the ancestry reading says False and the content reading returns `None`, the lane is NOT silently landed; it stays reportable, because a false LANDED hides real loss and is strictly worse than the false STRANDED this plan is removing.
  A DIRTY LANE MUST NEVER BE SILENCED BY THE CONTENT READING. THIS IS A DATA-LOSS HAZARD, REPRODUCED AT REVIEW, and it is the single most important constraint on this item. `holds_work` is `commits_ahead > 0 OR dirty`, so a lane whose commits all landed by patch id but whose worktree still holds UNCOMMITTED changes reaches the landing question, and the content reading answers True for the COMMITS while saying nothing about the uncommitted files. Measured in a throwaway repo: a lane worktree holding an untracked `precious_uncommitted.txt` whose commit had been cherry-picked onto a diverged main gave `merge-base --is-ancestor` rc=1 (STRANDED, reported TODAY) and `git cherry` all-`-` (LANDED, SILENT AFTER THIS PLAN). Today's ancestry-only reading ACCIDENTALLY protects that file; this plan removes the protection. So: gate the content-landed conclusion on `not described.get("dirty")`, and when the content reading would say landed but the lane is dirty, keep it REPORTABLE. Note `dirty` is already computed and already rendered as "uncommitted changes", so this costs nothing.
  HONEST LIMIT TO STATE IN THE CODE: `dirty` comes from a plain `git status --porcelain` and is BLIND TO IGNORED FILES, which plan `65cuw0`'s review measured and which caused a force-delete hazard there. This item only decides whether to REPORT, never whether to delete, so a missed ignored file here costs a missing row and not lost data; say so explicitly so a later reader does not reuse this predicate to gate a destructive action.
  - Depends on: E-01
  - Expected outcome: a cherry-picked CLEAN lane classifies `LANDED` with `landed_by == "content"`; a cherry-picked DIRTY lane stays REPORTABLE; a genuinely unmerged lane still classifies `STRANDED`; an unanswerable lane stays reportable.
  - Execution state: performed

- [x] E-03 Measure EVERY reported lane against the shipped reading and record the per-lane result IN THIS PLAN, confirming or correcting E-08's pre-build measurement. Cover all reported lanes, not only the six: at review the reported set was 17 distinct lanes, and a six-lane table would have missed 11 of them. Report the content verdict and resulting `lane_state` per lane, plus the row count and distinct-lane count before and after.
  THIS IS A MEASUREMENT, NOT A TARGET, and at review the expected answer is ZERO resolved. The six named lanes are ALL reimplementations rather than cherry-picks (blob-identity 0/7, 0/5 and 0/19 on the three sampled), so patch-id equality legitimately fails for every one. Any lane the reading does not resolve is REPORTED, not reclassified, and its continued presence is the CORRECT outcome, not a failure of this plan. If the number resolved is zero, say so plainly in the evidence and reconcile it against the choice E-08 recorded; do NOT adjust the predicate to produce a nonzero figure.
  - Depends on: E-02
  - Expected outcome: a table over EVERY reported lane giving the content verdict and resulting `lane_state`, the honest count resolved (expected 0 on today's corpus), which remain reported, and the before/after row and distinct-lane counts.
  - Execution state: performed

### Task group 2: one lane, one row, and a row that is true

- [x] E-04 Collapse the reported set to one row per lane branch in `runner_shared.stranded_lane_records`. The current key is `(run_id, branch, worktree)` and its docstring justifies it as "one lane named by both an attempt and the item-level `preserved_*` fields yields one record", which is CORRECT for the within-run duplicate it was written for; it is the `run_id` component that is wrong ACROSS runs. KEEP the within-run collapse, then add a per-BRANCH collapse of the reported set, retaining the most informative record (prefer one carrying an `integration_signal`, then the highest `commits_ahead`) and carrying the run count plus the newest `run_id` so no evidence is dropped from the row. Update the docstring's dedup sentence, which will otherwise describe behavior that no longer exists.
  THIS IS THE ITEM WITH THE LARGEST MEASURED, INDEPENDENT YIELD, and it does not depend on E-01/E-02 at all. Re-measured at review: **25 rows over 17 distinct lanes**, repeats `{58ha43: 2, 7p9n2v: 3, qcqhj7: 3, rchpms: 3, zz5yxq: 2}`, so the collapse removes 8 rows (32%). NOTE the authored figures (19 rows / 12 lanes, repeats without `zz5yxq`) are STALE, which is itself evidence for the plan: the corpus moves between authoring and execution, so RE-DERIVE and report the denominator rather than quoting this plan.
  WHAT IT DOES NOT ACHIEVE, stated so the Goal is not over-read: collapsing rows does NOT make `--check` pass. Measured, 17 non-`info` drifts remain and `artifact_core.drift_exit_code` returns 1. Silence requires the lanes' DISPOSITION, which is `ut0vzr`'s.
  - Depends on: none
  - Expected outcome: at most one record per lane branch, each naming how many runs touched it and the newest run id; the before/after row and distinct-lane counts re-derived and pasted.
  - Execution state: performed

- [x] E-05 Existence-check the worktree before it is rendered, so a row stops asserting a directory that is gone. Return None when the path does not exist, so the caller OMITS the segment (the caller already omits on None). PRESERVE F8a IN THE SAME DIRECTION: never return an absolute path, and prefer omission over leaking; omitting an absent worktree strictly REDUCES what is printed and so cannot introduce a leak. Do NOT satisfy this by walking `.aw/worktrees/`: F3a forbids a filesystem-derived VERDICT, and this checks only whether ONE already-derived display field should be rendered.
  THE PLAN NAMED THE WRONG BRANCH, CORRECTED AT REVIEW, AND PATCHING THE ONE IT NAMED WOULD FIX NOTHING. The item blamed `lane_worktree_display`'s EXCEPT branch (the `parent == "worktrees"` reconstruction). Measured over the live record set: of 25 records carrying a worktree, **25 take the SUCCESS path and 0 take the except branch**, because `Path.resolve()` does NOT require the path to exist, so `relative_to(root)` SUCCEEDS for an absent directory and the value is returned by the normal `text = rel.as_posix()` return. Confirmed directly: `lane_worktree_display(repo, "<repo>/.aw/worktrees/03ie04")` returns `.aw/worktrees/03ie04` while that directory does not exist. So the existence check must guard the SUCCESS return (and, for completeness, the except-branch reconstruction too, which is the same defect on a path that happens to be outside the repo).
  THE COUNT IS NOT ALL OF THEM, WHICH IS WHY OMISSION MUST BE CONDITIONAL AND NOT UNCONDITIONAL. Measured: 19 of the 25 named worktrees are absent and **6 EXIST** (`m7gvuz`, `m7gvuz_attempt2`, `zqs0px_attempt2`, `zqs0px_attempt3`, `zz5yxq` twice). A blanket removal of the segment would delete true, useful information for those six.
  - Depends on: none
  - Expected outcome: an absent worktree is omitted from the row whichever branch derived it; an existing one still renders repository-relative; no surface ever renders an absolute path.
  - Execution state: performed

- [x] E-06 Repair the dead sentinel in `attention.lane_remedy_hint`. It probes `hasattr(oc_runipd, "cmd_integrate")`; no such symbol exists (the integrate entry point is `handle_integrate_command`, and the CLI forwards `aw oc integrate` as REMAINDER args rather than binding a `cmd_*` function), so the conditional froze in its pre-`rl67b0` state. VERIFIED AT REVIEW: `hasattr(oc_runipd, "cmd_integrate")` is False, `hasattr(oc_runipd, "handle_integrate_command")` is True, and the live hint still reads "(no `aw integrate` verb exists yet)". Probe a symbol that exists, keep the function's own documented rule intact ("Do not print a verb that does not exist"), and name the concrete command using the record's `id6` where available. Add a test that FAILS if the probed symbol disappears, since a bare `hasattr` against a name nothing else references is unobservable when it rots; that unobservability is the actual defect, not the wrong string.
  NAMING THE `id6` REQUIRES A SIGNATURE CHANGE, so do it deliberately. `lane_remedy_hint()` takes NO arguments today and is called once, inside the per-record loop that already has `rec`, so pass the id6 in as an OPTIONAL parameter and keep the no-argument call working (V-06's own evidence line invokes it with no arguments). Do not read the record from module state.
  BOTH HOSTS HAVE THE VERB (`agy_runipd.handle_integrate_command` is present too, verified), so if the hint names a host, name the one the record came from or keep it host-neutral rather than hardcoding `oc`.
  - Depends on: none
  - Expected outcome: `lane_remedy_hint` returns the `aw oc integrate` remedy in this repository, still degrades to the manual hint where the verb is genuinely absent, remains callable with no arguments, and a test pins the probed name.
  - Execution state: performed

### Task group 3: bring the contract with the code

- [x] E-07 Amend spec `attention-registry-and-cross-tree-status` F3a (spec line 231-234) for the two rules this plan establishes, since F3a is what every future reader of this surface is reviewed against. FIRST, the landing exclusion is satisfied by CONTENT reaching the target, not only by ancestry: F3a already REQUIRES the exclusion, and it is its "requires a reachability test against the target" wording that licensed the ancestor-only reading now producing six false strands. SECOND, one lane is at most one row. Append the history record with `aw specs note` naming plan `0ta5vg` as the cause. Do NOT weaken F3a's fail-closed posture, its run-record-not-filesystem rule, or F8a. NO `schema_version` BUMP IS EXPECTED: `render_json` puts only `{branch, rule, detail}` per lane into `stranded_lanes` (attention.py:1382-1386), so `landed_by` stays internal; if implementation surfaces it anyway, F8 obliges the bump and `SCHEMA_VERSION` (attention.py:41, currently 4) must be incremented with its comment block extended.
  THE SPEC IS `implemented` AND CANNOT BE STATUS-TRANSITIONED, VERIFIED AT REVIEW. `attention_contract.SPEC_TRANSITIONS['implemented']` is `{superseded, deferred}`, so `aw specs set` refuses every review-ish target and MUST NOT be attempted; the status should not change anyway, since this is an amendment to an implemented contract rather than a reversion. `aw specs note` is the correct surface and the plan already names it. Paste the `- Status:` line before and after showing it UNCHANGED at `implemented`.
  WHAT THE AMENDMENT MUST SAY IF E-08 CHOSE TO DROP THE CONTENT READING. The two rules are not equally settled after review: the ONE-ROW-PER-LANE rule is delivered unconditionally by E-04 and should be stated. The CONTENT-LANDED rule is delivered only if E-01/E-02 ship. If E-08 recorded decision (i) (drop them), amend F3a for the one-row rule ONLY, and do NOT write a content-landed clause the code does not implement; a spec asserting a reading that does not exist is the same code-contract drift this item exists to close. Note F3a's existing "requires a reachability test against the target" wording is not FALSE, it is merely narrower than F3a's own exclusion demands, so leaving it while adding the one-row rule is coherent.
  - Depends on: E-02, E-04, E-08
  - Expected outcome: F3a states the one-row rule, and the content-landed rule if and only if E-01/E-02 shipped; a history note cites this plan; the spec's `- Status:` is unchanged at `implemented`; no other normative clause changes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- ONE READER BY CONSTRUCTION: `runner_shared.stranded_lane_records` feeds both the end-of-run summary and the attention view, and its docstring states why ("two derivations of 'is this work lost' would drift and only one of them would be wrong at a time"). Both fixes belong there, not in either consumer.
- FINGERPRINT PINS FORBID CASUAL EDITS: `describe_lane` is held byte-for-byte against `tests/fixtures/runner_shared_premove_fingerprints.json` (HEAD `1ecc5891`). `lane_work_has_landed` exists as a separate helper precisely so the landing question could be added without touching it (runner_shared.py:1124-1130). New readings go in NEW helpers. Relatedly, `plan_bucket` documents itself in COMMENTS because a docstring is part of the AST and breaks that guard.
- THE TARGET IS `HEAD`, NOT `main`: `LANE_INTEGRATION_TARGET_FALLBACK = "HEAD"` (runner_shared.py:1074) and `attention.stranded_lane_drift` passes no target (attention.py:1259), so it takes that fallback. Tests must control HEAD rather than assume `main` exists.
- TESTS MUST NOT READ THE REAL REPO: backlog `no0j8g` records four `aw attention` tests that passed `dir=None` and so read the developer's own repository, making their exit codes depend on live state. New tests build temporary git repos.
- `aw attention` IS MEASURABLE FROM INSIDE A LANE AFTER ALL, AND THE AUTHORED CONVENTION SAYING OTHERWISE IS WRONG. CORRECTED AT REVIEW BY MEASUREMENT. The claim (inherited from `ut0vzr`'s review PR-006) was that `.aw/records/runs/` is gitignored, hence absent in a linked worktree, so `stranded_lane_drift` returns `[]` and an in-lane check reports a FALSE clean. But `stranded_lane_drift` does NOT read `repo_root` directly: it calls `attention._resolve_runs_repo_root`, which walks out of a `.aw/worktrees/...` path to the first ancestor with a real state root. Verified from inside this review lane: the resolver returned the MAIN checkout and `stranded_lane_drift` returned **25 rows over 17 lanes**, not `[]`.
  WHY THIS MATTERS RATHER THAN BEING A PEDANTIC CORRECTION: the false convention would send the executor hunting for a non-lane tree it does not have (`aw oc run` executes in exactly such a lane), and worse, it invites treating an in-lane `0` as untrustworthy when in fact the number is real. USE the resolver and REPORT which root it resolved to alongside any count, so the measurement is self-describing. A genuine `[]` is still possible for a checkout with no run records anywhere above it; distinguish that case by printing the resolved root rather than by assuming.
- READ-ONLY IS A CONTRACT: F3a's closing clause and spec G3/8.1. Nothing here merges, deletes or reclaims.

## Findings

| # | Finding | Evidence (measured 2026-09-18, HEAD `d188eaad`, primary non-lane checkout) | Consequence |
|---|---|---|---|
| F-1 | 19 rows cover 12 lanes | `rows: 19 distinct: 12`; repeats `{58ha43: 2, 7p9n2v: 3, qcqhj7: 3, rchpms: 3}`. RE-MEASURED AT REVIEW (HEAD `7562ca6c`): **25 rows over 17 lanes**, repeats `{58ha43: 2, 7p9n2v: 3, qcqhj7: 3, rchpms: 3, zz5yxq: 2}` | Count overstated (47% at review); `run_id` in the dedup key. The authored figures are STALE, which is itself evidence: RE-DERIVE and report the denominator |
| F-2 | 6 lanes are re-executed first attempts whose work IS on `main` | Finalize commits `bc9b3f43`/`e0c139ea`/`a912d5a9`/`14d5429a`/`84c5adcd`/`68930180` all verified to EXIST, none having the dead lane as ancestor; shipped symbols confirmed (e.g. `render_stream.Refusal` present on HEAD) | Ancestry-only reading reports re-executed work as lost forever. THE PREMISE IS CONFIRMED and all six ARE still reported; note this REFUTES `tb63qv`'s review claim that "the six lanes appear ZERO times" |
| F-2a | **BUT PATCH-ID EQUALITY RESOLVES NONE OF THEM, SO E-01/E-02 AS AUTHORED BUY NOTHING** | ADDED AT REVIEW. `git cherry HEAD aw/lane/<id>` returned only `+` lines for all six (`03ie04` -0/+2, `fn2l1u` -0/+2, `mm5p3v` -0/+3, `nna8yz` -0/+3, `r2i1b1` -0/+1, `ybkmzp` -0/+2); 0 of all 17 reported lanes are silenced. CAUSE: the second attempts were REIMPLEMENTATIONS, not cherry-picks. `r2i1b1`'s lane commit `81323cd6` vs the commit that shipped its work, `ccc7e04c`, have different patch ids (1602 vs 1235 diff lines), and a blob-identity check found 0/7, 0/5 and 0/19 files matching HEAD for `r2i1b1`/`03ie04`/`fn2l1u` | The plan's headline mechanism has ZERO measured yield. E-08 now gates it and forces an explicit keep/drop/stop decision |
| F-2b | **A DIRTY LANE WOULD BE SILENCED, LOSING UNCOMMITTED WORK** | ADDED AT REVIEW, reproduced in a throwaway repo. `holds_work` is `commits_ahead > 0 OR dirty`, so a lane whose commits landed by patch id but whose tree holds an untracked file reaches the landing question: ancestry rc=1 (STRANDED, reported today) while `git cherry` is all-`-` (LANDED, silent after this plan). Also `git cherry` exits 0 with EMPTY output when there is nothing to compare, and "every line begins `-`" is vacuously true on empty | Today's ancestry reading ACCIDENTALLY protects uncommitted work; the plan removes that protection. E-02 now gates on `not dirty` and E-01 rejects empty output |
| F-3 | F3a ALREADY forbids this | Spec F3a verified verbatim: "a lane whose work HAS reached the integration target MUST NOT fail it either, which requires a reachability test against the target" | A spec VIOLATION, not a gap; raises severity and obliges the amendment |
| F-4 | All 19 rows name an absent worktree | `rows naming a worktree: 19, nonexistent: 19`. RE-MEASURED AT REVIEW: 25 rows name a worktree, **19 absent and 6 PRESENT** (`m7gvuz`, `m7gvuz_attempt2`, `zqs0px_attempt2`, `zqs0px_attempt3`, `zz5yxq` twice) | Remediation points at a dead end for 19. Omission must be CONDITIONAL: a blanket removal would delete true information for the 6 that exist |
| F-4a | **E-05 NAMED THE WRONG CODE BRANCH; PATCHING IT WOULD FIX NOTHING** | ADDED AT REVIEW. The item blamed `lane_worktree_display`'s except branch, but of 25 records carrying a worktree **25 take the SUCCESS path and 0 the except branch**: `Path.resolve()` does not require existence, so `relative_to(root)` succeeds for an absent directory. Confirmed: `lane_worktree_display(repo, "<repo>/.aw/worktrees/03ie04")` returns `.aw/worktrees/03ie04` while that directory is absent | The existence check must guard the SUCCESS return, not only the reconstruction |
| F-5 | The remedy's capability probe can never be True | `hasattr(oc_runipd,"cmd_integrate") = False`; `handle_integrate_command` present; `aw oc integrate` in `aw oc --help`; `rl67b0` is `executed` | Steers the operator to a manual merge that SKIPS the merge-and-revalidate gate |
| F-6 | Text similarity is NOT a sound landing test | Added-line presence 8-18% for lanes whose work is demonstrably on `main`; `03ie04` scored 8% yet its fix is present and cites the plan by id | E-01 must use patch ids; recorded so the discarded approach is not retried |
| F-7 | `65cuw0` delegates its new reclaim reading to the SAME broken predicate | Its E-01 computes `merged_into_target` by "DELEGATING to the existing `runner_shared.lane_work_has_landed`", mapping `None` to not-merged. Verified at review that `lane_work_has_landed`'s only in-package callers are the two calls inside `classify_lane_integration`, so `65cuw0` would be the third | Fixing E-01/E-02 here makes `65cuw0` reclaim strictly MORE. CAUTION SHARPENED AT REVIEW: `65cuw0` gates a DESTRUCTIVE teardown, so if it ever delegates to the CONTENT reading, F-2b's dirty-lane hazard becomes a force-delete rather than a missing row. E-02 must keep the content reading out of any predicate a destructive path can reach, and say so |
| F-8 | The payload does not carry per-lane state today | `render_json`'s `stranded_lanes` entries verified as `{branch, rule, detail}` only; `SCHEMA_VERSION = 4` | `landed_by` can stay internal, so no `schema_version` bump is expected; E-07 states the condition under which it would be |
| F-9 | **THE GOAL IS NOT ACHIEVABLE BY THIS PLAN, AND SAYING SO IS NOT A DEFEAT** | ADDED AT REVIEW. The Goal is "`aw attention --check` silent when every lane's work is accounted for". Measured after simulating every fix: 17 lanes hold commits genuinely absent from the target by BOTH readings, so 17 non-`info` drifts remain and `artifact_core.drift_exit_code` returns 1 | `--check` still fails after this plan. The report would be TRUTHFUL but not silent, because the lanes really do hold unlanded commits. Silence requires DISPOSITION (`ut0vzr`'s), not a predicate change. The Goal and the whole-plan acceptance criterion are corrected to match |
| F-10 | The authored measuring-tree convention is wrong | ADDED AT REVIEW. `stranded_lane_drift` resolves through `attention._resolve_runs_repo_root`, which escapes a `.aw/worktrees/...` path to the first ancestor holding a state root. From inside this review lane it resolved to the main checkout and returned 25 rows, not `[]` | The "cannot be measured from inside a lane" convention would send the executor hunting for a tree it does not have. Corrected in Step 0; measurements must PRINT the resolved root |
| F-11 | The plan's suite-baseline assumption is stale | ADDED AT REVIEW. `python3 -m pytest` bare in this lane: **8258 passed, 3 skipped, 2 xfailed**, fully green. The sibling `tb63qv` review recorded a 31-failure "documented worker-lane baseline (`770fkp`)" | Do NOT carry a 31-failure baseline expectation into execution. Capture the baseline in the EXECUTING tree, as the plan already says, and compare by failing node id |

## Proposed changes (ordered, validatable)

1. FIRST, re-measure the content reading's yield over EVERY reported lane and record a keep/drop/stop decision before writing it (E-08). At review the yield was 0 of 17.
2. New content-landed helper, patch-id based, three-valued, rejecting empty output and mapping git errors to None (E-01).
3. `classify_lane_integration` consults both readings, records `landed_by`, keeps fail-closed on unanswerable, and NEVER silences a dirty lane (E-02).
4. Measure every reported lane against the shipped reading and record per-lane results (E-03).
5. Per-branch collapse of the reported set, retaining run count and newest run id; docstring corrected (E-04).
6. Existence-check the worktree; omit when absent, never absolutize (E-05).
7. Repair the sentinel and pin the probed name with a test (E-06).
8. Amend F3a for both rules; bump `schema_version` only if `landed_by` surfaces (E-07).

## Deferred / out of scope (with reason)

- DISPOSITION OF THE 12 REPORTED LANES: plan `ut0vzr` (`laneorph-02`, from `qliia1`) owns it. This plan deliberately lands FIRST so that triage measures against a report that does not lie. Note for whoever sequences them: `ut0vzr`'s blocking OQ-04 asserts that deleting a branch converts a `lane-stranded` row into an equally-failing `lane-unknown` row; that is refuted by measurement (a deleted branch has no `commits_ahead`, so `holds_work` is False and EMPTY is reached BEFORE the landing question at runner_shared.py:1166-1171). Verified twice: already-deleted `tx6q0h` produces NO row (12 reported, not 13), and in a throwaway repo `STRANDED` becomes `EMPTY` after `git branch -D`. Recorded here as evidence for that plan's OQ, not resolved by this one.
  - Carrier: ut0vzr
- LANE TEARDOWN / WORKTREE RECLAMATION (4.7G): backlog `a58s04` and plan `65cuw0` own it. That is a WRITE against real worktrees, where this plan is read-only. F-7 records the shared predicate.
  - Carrier: a58s04
- THE DRIVER'S DESTRUCTIVE MERGE-ABORT (`csmtjp`): a real high-priority defect in `integrate_lane_branch`, but a different surface (the runner's merge path, not the reporting view) and independently filed.
  - Carrier: csmtjp
- PRUNING RUN RECORDS that name long-gone lanes: the record is deliberately authoritative and historical (F3a), so rewriting it is out of scope; E-04/E-05 fix the RENDERING instead.
  - Carrier-Declined: F3a makes the run record deliberately authoritative and historical, so rewriting it is forbidden rather than merely out of scope; there is no future work to carry. E-04/E-05 fix the RENDERING, which is the whole remedy.
- A PROVABLE-REIMPLEMENTATION TEST: if `git cherry` cannot resolve a reimplemented lane (likely for `03ie04`), the honest outcome is that the lane stays reported for a human. Building a semantic-equivalence detector is out of scope and probably not tractable.
  - Carrier-Declined: a semantic-equivalence detector is probably not tractable, and the honest fallback already ships: a lane the readings cannot resolve stays REPORTED for a human, which is the correct fail-closed outcome rather than a gap needing a carrier.

## Scope check

- Over-scope: none. Every E-item is one of the four measured defects, the measurement gate they now depend on (E-08), or the spec amendment they oblige. Note E-08 writes no code and touches no declared path; it records a measurement and a decision IN THIS PLAN, which is already in `Scope-Paths`.
- Under-scope: this plan does not retire any lane, does not reclaim any worktree, and does not resolve `ut0vzr`'s OQ-04 (it supplies evidence only).
- WHAT REMAINS REPORTED AFTER THIS PLAN, corrected at review so the residue is not mistaken for a defect. `aw attention --check` will STILL EXIT 1, naming all 17 currently reported lanes (re-derive), because every one holds commits genuinely absent from the target by BOTH readings (F-9). That is fail-closed behavior working as designed on a corpus of genuinely unlanded work, not a residual bug and not a shortfall of this plan. The remaining rows will be FEWER (one per lane), will not name absent worktrees, and will carry a real remedy. Closing them requires the lanes' DISPOSITION, which is `ut0vzr`'s.

## Required tests / validation

Run the suite BARE as `python3 -m pytest` (the repo's `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; do NOT add `-n0`, a second `-q`, or `-p no:randomly`) and paste the actual `N passed` summary line, compared against a pre-change baseline captured at the same HEAD. New tests go in `tests/test_runner_shared.py` (content reading, classification, dedup) and `tests/test_attention.py` (row rendering, remedy hint). Every test constructs its own temporary git repository and passes an explicit `dir`, per the hazard backlog `no0j8g` records for exactly these tests; because the target defaults to `HEAD` (runner_shared.py:1074), a test must control HEAD explicitly. Any acceptance measurement of `aw attention` itself must be taken in a NON-LANE tree, since an in-lane run finds no run records and reports a false clean (attention.py:1141-1145).

## Spec / documentation sync

AMENDS `.aw/records/specs/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` (F3a), declared in `Scope-Paths` so both runners announce the spec edit before the run and reconcile it at finalize. WHY THE AMENDMENT IS OBLIGATORY, not optional: F3a currently says the landing exclusion "requires a reachability test against the target", and that wording is what licensed the ancestor-only reading producing six false strands. Fixing the code alone would leave the next implementer correctly following prose that reproduces the defect. The amendment is NARROWING and additive: nothing that previously failed the gate stops failing except the case F3a already said must not fail, and the fail-closed posture, the run-record-not-filesystem rule and F8a are untouched. The spec is `implemented`; this plan returns it to accuracy rather than extending its surface. `schema_version` is expected to stay 4 (see F-8); E-07 names the condition that would change that.

## Open questions

### OQ-01: Should a content-landed lane be silent, or a distinct non-failing state?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: SILENT. `LANE_ATTENTION_STATES` (runner_shared.py:1068) exists to separate reportable from correct states, and its comment states that `LANDED`, `EMPTY` and `LIVE` "are correct behavior and are deliberately silent". A content-landed lane IS landed, so it takes the existing `LANDED` path and adds no reportable state. `landed_by` preserves the distinction for debugging without spending a row on it.

### OQ-02: Does `git cherry` resolve all six re-execution lanes?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW BY MEASUREMENT, AND THE ANSWER IS NO: IT RESOLVES NONE OF THEM. At HEAD `7562ca6c`, `git cherry HEAD aw/lane/<id>` returned only `+` lines for all six (`03ie04` -0/+2, `fn2l1u` -0/+2, `mm5p3v` -0/+3, `nna8yz` -0/+3, `r2i1b1` -0/+1, `ybkmzp` -0/+2), and 0 of all 17 reported lanes are silenced. The cause generalizes the plan's own `03ie04` caveat to every lane: the second attempts were REIMPLEMENTATIONS, so patch ids differ (`r2i1b1`'s `81323cd6` versus the shipping `ccc7e04c`, 1602 versus 1235 diff lines) and a blob-identity check over each lane's touched files found 0/7, 0/5 and 0/19 matching HEAD.
  WHAT FOLLOWS, and why this stays non-blocking. The plan genuinely does not depend on the answer, exactly as authored: a lane the reading resolves becomes silent, a lane it does not stays reported for a human, and the correct response to a zero yield is E-08's recorded keep/drop/stop decision rather than a looser predicate. The warning the question was written to give still stands and is now load-bearing: an executor must NOT treat "the six resolve" as a target, because a false LANDED hides real loss and is worse than the false STRANDED being fixed. E-08 and E-03 both now forbid adjusting the predicate to manufacture a nonzero figure.

### OQ-03: Should the row say "no worktree remains" rather than omitting the field?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: aqb4dv
- Resolution or deferral rationale: E-05 implements OMISSION, which is the minimum correct fix and matches the existing None-means-omit contract at attention.py:1277-1279. But "no worktree remains" is genuinely useful information, since it tells the reader recovery is a branch merge and not a tree inspection. Deferred to the maintainer as a presentation choice; omission is not blocked on it. CARRIED at execution by backlog `aqb4dv` (followup, low), so the question survives this plan reaching `executed` instead of vanishing when the plan classes `done`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-08 validates E-08
  - Required evidence: the per-lane table over EVERY reported lane with `-`/`+` counts and verdict, the count silenced and the count remaining, and the run-root the measurement resolved to. Then the RECORDED DECISION among (i) drop E-01/E-02/E-03, (ii) keep them as a forward-looking guard with a stated zero present yield, or (iii) stop and ask the maintainer, with the reason. If the decision is (i), mark E-01/E-02/E-03 and V-01/V-02/V-03 `blocked` with that reason rather than silently skipping them, and say so here.
  - Observed evidence: MEASURED IN THE EXECUTING LANE at HEAD `07dabf1b`, BEFORE any code was written. The run-root resolved through `attention._resolve_runs_repo_root` to the MAIN checkout (printed, per Step 0's corrected convention), NOT to this lane:

    ```
    repo_root: <lane>/.aw/worktrees/0ta5vg
    resolved runs root: <main checkout>
    rows: 20
    distinct: 13
    ```

    THE COUNTS MOVED AGAIN, which is the third independent confirmation of F-1's staleness point: authored 19 rows / 12 lanes, review-time 25 / 17, execution-time **20 rows over 13 distinct lanes** (`58ha43` x2, `7p9n2v` x3, `qcqhj7` x3, `rchpms` x3, the rest x1). Re-derived rather than quoted, as F-1 instructs.

    `git cherry main aw/lane/<id>` over EVERY one of the 13 reported lanes (not only the six), with `-` = present on the target by patch id and `+` = genuinely absent:

    | lane branch | rows | `-` present | `+` absent | rc | content verdict | ancestry |
    |---|---|---|---|---|---|---|
    | `aw/lane/03ie04` | 1 | 0 | 2 | 0 | False (>=1 absent) | False |
    | `aw/lane/2c122z` | 1 | 0 | 22 | 0 | False (>=1 absent) | False |
    | `aw/lane/58ha43` | 2 | 0 | 19 | 0 | False (>=1 absent) | False |
    | `aw/lane/7p9n2v` | 3 | 0 | 14 | 0 | False (>=1 absent) | False |
    | `aw/lane/d7qoxv` | 1 | 0 | 1 | 0 | False (>=1 absent) | False |
    | `aw/lane/fn2l1u` | 1 | 0 | 2 | 0 | False (>=1 absent) | False |
    | `aw/lane/mm5p3v` | 1 | 0 | 3 | 0 | False (>=1 absent) | False |
    | `aw/lane/nna8yz` | 1 | 0 | 3 | 0 | False (>=1 absent) | False |
    | `aw/lane/qcqhj7` | 3 | 0 | 3 | 0 | False (>=1 absent) | False |
    | `aw/lane/r2i1b1` | 1 | 0 | 1 | 0 | False (>=1 absent) | False |
    | `aw/lane/rchpms` | 3 | 0 | 9 | 0 | False (>=1 absent) | False |
    | `aw/lane/review-sweep-run-20260919T133719Z-1618106` | 1 | 0 | 5 | 0 | False (>=1 absent) | False |
    | `aw/lane/ybkmzp` | 1 | 0 | 2 | 0 | False (>=1 absent) | False |

    COUNT SILENCED: **0 of 13**. COUNT REMAINING: **13 of 13**. Not one lane produced a single `-` line, so patch-id equality holds for NONE of them, exactly as the review measured (and as OQ-02 resolved). The review's explanation is confirmed rather than re-litigated: the second attempts were REIMPLEMENTATIONS, so no patch-id or content-identity reading can see their work.

    THE RECORDED DECISION IS **(ii) KEEP E-01/E-02/E-03 as a forward-looking guard, with the zero present yield stated plainly** in the helper's docstring, in this plan, and in the spec amendment. Full reasoning, evidence and alternatives are in the decisions register as DECISION `01-0ta5vg-D1`. The short form, and the one piece of evidence the plan did not have:

    1. F3a's landing exclusion is NORMATIVE and ancestry does not satisfy it, so (i) would leave a known spec violation in place AND make E-07's amendment unwritable (E-07 forbids asserting a reading the code does not implement).
    2. THE CHERRY-PICK SHAPE IS ONE THIS CODEBASE ITSELF PRODUCES AND RECOMMENDS, which is what moves the guard from speculative to forward-looking. Two live race-recovery paths tell the operator to cherry-pick BY NAME: `commit_lock.py:438` (`ISO_RACED`, "the work is preserved as commit ...; cherry-pick or retry") and `ipd_lifecycle.py:2442` (`RECONCILED_RACED`, "The work is preserved as commit ... (cherry-pick or retry); the branch was NOT moved"). An operator who follows either lands the work by patch id and NOT by ancestry, producing precisely the false STRANDED F3a forbids.
    3. It is strictly NARROWING and triple-guarded: `None` stays reportable, empty output stays reportable, and a DIRTY lane stays reportable regardless. So a wrong answer cannot silence a lane that holds anything, and the measured effect on today's corpus is zero rows changed.
    4. (iii) is not warranted: the maintainer approved this plan AFTER the review that measured the zero yield and wrote E-08's three options into it, so the choice was explicitly delegated here.

    E-01/E-02/E-03 and V-01/V-02/V-03 are therefore PERFORMED, not `blocked`. The honest statement of yield is carried in the code itself (`lane_work_landed_by_content`'s docstring names the measurement and the date) so no later reader re-discovers the zero as a bug.
  - Result: pass

- [x] V-01 validates E-01
  - Required evidence: the helper's source pasted, plus pytest output for FIVE cases built in a TEMPORARY git repo: True where the lane's commits were cherry-picked onto a target that had ALSO advanced independently (the shape that makes the shas differ; verified at review that cherry-picking onto an unadvanced target reproduces the identical sha and the case proves nothing), False where one commit is genuinely absent, False for the PARTIAL case (two lane commits, one cherry-picked, so the output mixes `-` and `+`), False for EMPTY output (nothing to compare; must not read as landed), and None for an unresolvable ref (verified: `git cherry` exits 128 with `fatal: unknown commit`). Paste the actual test output, not a description.
  - Observed evidence: the helper's decision body, `agent_workflows/runner_shared.py` (docstring elided here; it carries the shape, the two guards and the measured zero yield):

    ```python
    def lane_work_landed_by_content(
        repo: Path, branch: str, *, target: str = LANE_INTEGRATION_TARGET_FALLBACK
    ) -> Optional[bool]:
        if not branch:
            return None
        rc, _out, _err = _run_git(repo, ["rev-parse", "--verify", "--quiet", branch])
        if rc != 0:
            return None
        rc, _out, _err = _run_git(repo, ["rev-parse", "--verify", "--quiet", target])
        if rc != 0:
            return None
        rc, out, _err = _run_git(repo, ["cherry", target, branch])
        if rc != 0:
            return None
        lines = [ln for ln in (out or "").splitlines() if ln.strip()]
        if not lines:
            # Nothing to compare. NOT landed: see the empty-output guard above.
            return False
        if any(ln.startswith("+") for ln in lines):
            return False
        return any(ln.startswith("-") for ln in lines)
    ```

    All FIVE required cases, each building its OWN temporary git repository and passing an explicit repo path (backlog `no0j8g`'s hazard), plus six more:

    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -k "ContentLandedReading" -v
    collected 182 items / 171 deselected / 11 selected

    tests/test_runner_shared.py::ContentLandedReadingTests::test_a_CHERRY_PICKED_lane_is_landed_by_CONTENT_though_not_by_ancestry PASSED [  9%]
    tests/test_runner_shared.py::ContentLandedReadingTests::test_a_cherry_picked_CLEAN_lane_classifies_LANDED_by_content PASSED [ 18%]
    tests/test_runner_shared.py::ContentLandedReadingTests::test_an_ancestor_landed_lane_records_landed_by_ancestor PASSED [ 27%]
    tests/test_runner_shared.py::ContentLandedReadingTests::test_an_UNANSWERABLE_content_reading_does_NOT_rescue_a_negative_ancestry PASSED [ 36%]
    tests/test_runner_shared.py::ContentLandedReadingTests::test_the_PARTIAL_case_reads_False_because_one_commit_is_still_absent PASSED [ 45%]
    tests/test_runner_shared.py::ContentLandedReadingTests::test_a_genuinely_ABSENT_commit_reads_False PASSED [ 54%]
    tests/test_runner_shared.py::ContentLandedReadingTests::test_an_UNRESOLVABLE_ref_reads_None_and_never_False PASSED [ 63%]
    tests/test_runner_shared.py::ContentLandedReadingTests::test_a_genuinely_unmerged_lane_still_classifies_STRANDED PASSED [ 72%]
    tests/test_runner_shared.py::ContentLandedReadingTests::test_EMPTY_output_reads_False_and_NEVER_vacuously_landed PASSED [ 81%]
    tests/test_runner_shared.py::ContentLandedReadingTests::test_a_cherry_picked_DIRTY_lane_STAYS_REPORTABLE_so_uncommitted_work_is_not_lost PASSED [ 90%]
    tests/test_runner_shared.py::ContentLandedReadingTests::test_the_content_reading_is_gated_on_NOT_DIRTY_in_the_source PASSED [100%]

    ====================== 11 passed, 171 deselected in 0.80s ======================
    ```

    MAPPING EACH REQUIRED CASE TO ITS TEST, so the five are not merely implied: TRUE on cherry-pick onto an independently advanced target = `test_a_CHERRY_PICKED_lane_is_landed_by_CONTENT_though_not_by_ancestry`, which asserts the two readings DISAGREE (ancestry False, content True). The review's warning is honored structurally by the `_advance_main` helper, whose docstring records WHY it is load-bearing: cherry-picking onto an UNADVANCED main reproduces the identical sha, making the lane an ancestor, so the case would prove nothing. FALSE for a genuinely absent commit = `test_a_genuinely_ABSENT_commit_reads_False`. FALSE for the PARTIAL case = `test_the_PARTIAL_case_reads_False_because_one_commit_is_still_absent`, which additionally asserts the raw `git cherry` output really does mix `-` and `+` before asserting the verdict. FALSE for EMPTY output = `test_EMPTY_output_reads_False_and_NEVER_vacuously_landed`, which first asserts the output is literally empty. NONE for an unresolvable ref = `test_an_UNRESOLVABLE_ref_reads_None_and_never_False`, covering an absent branch, an absent target AND the empty-branch argument.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `classify_lane_integration` output pasted for FOUR constructed lanes: cherry-picked and CLEAN (expect `LANDED`, `landed_by == "content"`), cherry-picked and DIRTY (expect STILL REPORTABLE, the data-loss guard, and this case is MANDATORY), genuinely unmerged (expect `STRANDED`), and one whose content reading returns None while ancestry says False (expect STILL REPORTABLE, proving the fail-closed direction). Show `lane_state`, `needs_attention`, `dirty` and `landed_by` for each. Paste the code line that gates the content conclusion on `not dirty`.
  - Observed evidence: all FOUR lanes constructed in temporary git repositories, `classify_lane_integration` called directly, all four required fields shown:

    ```
    cherry-picked CLEAN          lane_state=LANDED    needs_attention=False dirty=False landed_by=content
    cherry-picked DIRTY          lane_state=STRANDED  needs_attention=True  dirty=True  landed_by=None
    genuinely unmerged           lane_state=STRANDED  needs_attention=True  dirty=False landed_by=None
    content=None, anc=False      lane_state=STRANDED  needs_attention=True  dirty=False landed_by=None
    ```

    Every expectation is met: the cherry-picked CLEAN lane is `LANDED` and silent with `landed_by == "content"`; the cherry-picked DIRTY lane STAYS REPORTABLE (the mandatory data-loss guard); the genuinely unmerged lane is still `STRANDED`; and the lane whose content reading returns `None` against a False ancestry STAYS REPORTABLE, proving the fail-closed direction.

    THE GATE, pasted from `agent_workflows/runner_shared.py`:

    ```python
            content = (
                lane_work_landed_by_content(repo, str(branch), target=target)
                if not described.get("dirty")
                else None
            )
    ```

    The DIRTY case is also pinned by two tests rather than by this one-off run, because a guard nobody re-checks is a guard that rots: `test_a_cherry_picked_DIRTY_lane_STAYS_REPORTABLE_so_uncommitted_work_is_not_lost` reproduces the hazard end to end (it asserts the content reading really does answer True for the COMMITS, that the lane is nevertheless `STRANDED`, and that the untracked `precious_uncommitted.txt` still exists), and `test_the_content_reading_is_gated_on_NOT_DIRTY_in_the_source` pins the gate line itself by source inspection so deleting it fails a test. Both PASSED in V-01's output above.

    The honest limit E-02 required is stated IN THE CODE at the gate: `dirty` is a plain `git status --porcelain` and is BLIND TO IGNORED FILES, so the comment records that a missed ignored file here costs a MISSING ROW and never lost data (this function decides whether to REPORT, never whether to delete), and explicitly tells a later reader NOT to delegate a teardown, prune or force-delete decision to this reading. That closes F-7's sharpened caution about `65cuw0`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the table over EVERY reported lane (not six) with the content verdict and resulting `lane_state`, plus the honest count resolved and the row/distinct counts before and after. If the count resolved is zero, state that plainly and reconcile it with V-08's recorded decision. Name every lane still reported and confirm that is the intended outcome rather than a defect. Do NOT present a loosened predicate that resolves more lanes.
  - Observed evidence: measured against the SHIPPED code (not the pre-build probe of V-08), runs root printed and resolved to the MAIN checkout:

    ```
    runs root resolved to: <main checkout>
    | lane | ancestry | content | lane_state | landed_by |
    |---|---|---|---|---|
    | `aw/lane/03ie04` | False | False | lane-stranded | None |
    | `aw/lane/2c122z` | False | False | lane-stranded | None |
    | `aw/lane/58ha43` | False | False | lane-stranded | None |
    | `aw/lane/7p9n2v` | False | False | lane-stranded | None |
    | `aw/lane/d7qoxv` | False | False | lane-stranded | None |
    | `aw/lane/fn2l1u` | False | False | lane-stranded | None |
    | `aw/lane/mm5p3v` | False | False | lane-stranded | None |
    | `aw/lane/nna8yz` | False | False | lane-stranded | None |
    | `aw/lane/qcqhj7` | False | False | lane-stranded | None |
    | `aw/lane/r2i1b1` | False | False | lane-stranded | None |
    | `aw/lane/rchpms` | False | False | lane-stranded | None |
    | `aw/lane/review-sweep-run-20260919T133719Z-1618106` | False | False | lane-stranded | None |
    | `aw/lane/ybkmzp` | False | False | lane-stranded | None |

    resolved (silenced) by the content reading: 0 of 13
    still reported: 13
    ```

    ROW AND DISTINCT COUNTS: BEFORE **20 rows / 13 distinct lanes**; AFTER **13 rows / 13 distinct lanes**. The row reduction is entirely E-04's per-branch collapse; the content reading contributed nothing, as expected.

    THE COUNT RESOLVED IS **ZERO**, STATED PLAINLY, and it RECONCILES EXACTLY with V-08's recorded decision (ii): the pre-build probe predicted zero, the shipped code delivers zero, and the two measurements agree lane for lane. No predicate was loosened to manufacture a nonzero figure, which E-08, E-03 and OQ-02 all forbid.

    EVERY LANE STILL REPORTED, and this IS the intended outcome rather than a defect: all 13 above. Each holds at least one commit absent from the target by BOTH readings (ancestry False AND content False, shown per lane), so reporting them is the gate working correctly on a corpus of genuinely unlanded work. Closing them is a DISPOSITION question owned by plan `ut0vzr`, not something any predicate here can or should decide. F-9 is confirmed rather than contradicted.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `aw att --format json` re-run with the row count and distinct-lane count pasted BEFORE and AFTER, showing at most one row per branch and the previously-repeated lanes appearing once each (at review: `7p9n2v`/`qcqhj7`/`rchpms` tripled, `58ha43`/`zz5yxq` doubled; RE-DERIVE, the set moves). Print the run-root the measurement resolved to. Show the retained record still carries the run count and the newest run id. Plus a unit test proving a single run naming one lane by both an attempt and `preserved_*` still yields ONE record (the within-run collapse must survive).
  - Observed evidence: run-root printed and resolved to the MAIN checkout in both measurements.

    BEFORE (pre-change, same HEAD `07dabf1b`): **20 rows over 13 distinct lanes**, repeats `{58ha43: 2, 7p9n2v: 3, qcqhj7: 3, rchpms: 3}`. RE-DERIVED rather than quoted; note this differs from BOTH the authored 19/12 and the review's 25/17, the third confirmation of F-1's staleness point, and `zz5yxq` is no longer in the set at all.

    AFTER:

    ```
    resolved runs root: <main checkout>
    AFTER rows: 13 distinct: 13
    max rows per lane: 1
      aw/lane/03ie04 1
      aw/lane/2c122z 1
      aw/lane/58ha43 1
      aw/lane/7p9n2v 1
      aw/lane/d7qoxv 1
      aw/lane/fn2l1u 1
      aw/lane/mm5p3v 1
      aw/lane/nna8yz 1
      aw/lane/qcqhj7 1
      aw/lane/r2i1b1 1
      aw/lane/rchpms 1
      aw/lane/review-sweep-run-20260919T133719Z-1618106 1
      aw/lane/ybkmzp 1
    ```

    AT MOST ONE ROW PER BRANCH is shown directly (`max rows per lane: 1`), and every previously-repeated lane now appears exactly once. 20 -> 13 rows, a 35% reduction, with the distinct-lane count UNCHANGED at 13: the collapse removed duplicates only and lost no lane.

    THE RETAINED RECORD STILL CARRIES THE RUN EVIDENCE, so nothing is dropped by collapsing:

    ```
    records: 13
      aw/lane/58ha43 run_count= 2 newest run_id= run-20260829T191652Z-4134000 n run_ids= 2
      aw/lane/7p9n2v run_count= 3 newest run_id= run-20260829T191652Z-4134000 n run_ids= 3
      aw/lane/qcqhj7 run_count= 3 newest run_id= run-20260829T191652Z-4134000 n run_ids= 3
      aw/lane/rchpms run_count= 3 newest run_id= run-20260829T191652Z-4134000 n run_ids= 3
    ```

    And the human/agent detail says so rather than hiding it, e.g. `aw/lane/58ha43`: `STRANDED lane; plan 58ha43; 22 commit(s) beyond base; newest run run-20260829T191652Z-4134000 of 2 runs: ...`.

    THE WITHIN-RUN COLLAPSE SURVIVES, which was the explicit requirement:

    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -k "OneRowPerLane or LaneWorktreeDisplayExistence or test_worktree_display_NEVER" -v
    collected 182 items / 172 deselected / 10 selected

    tests/test_runner_shared.py::OneRowPerLaneTests::test_a_lane_named_by_THREE_runs_yields_ONE_row_carrying_the_run_count PASSED [ 10%]
    tests/test_runner_shared.py::OneRowPerLaneTests::test_the_retained_row_is_the_MOST_INFORMATIVE_one PASSED [ 20%]
    tests/test_runner_shared.py::OneRowPerLaneTests::test_TWO_DISTINCT_lanes_are_NOT_collapsed_into_one_row PASSED [ 30%]
    tests/test_runner_shared.py::OneRowPerLaneTests::test_the_WITHIN_RUN_collapse_SURVIVES_one_lane_named_twice_in_one_run PASSED [ 40%]
    tests/test_runner_shared.py::LaneWorktreeDisplayExistenceTests::test_an_ABSENT_worktree_is_OMITTED PASSED [ 50%]
    tests/test_runner_shared.py::LaneWorktreeDisplayExistenceTests::test_an_absent_worktree_OUTSIDE_the_repository_is_still_omitted PASSED [ 60%]
    tests/test_runner_shared.py::LaneWorktreeDisplayExistenceTests::test_an_EXISTING_worktree_still_renders_REPOSITORY_RELATIVE PASSED [ 70%]
    tests/test_runner_shared.py::LaneWorktreeDisplayExistenceTests::test_the_guard_protects_the_SUCCESS_return_not_only_the_reconstruction PASSED [ 80%]
    tests/test_runner_shared.py::LaneWorktreeDisplayExistenceTests::test_NO_surface_ever_renders_an_ABSOLUTE_path PASSED [ 90%]
    tests/test_runner_shared.py::StrandedLanePredicateTests::test_worktree_display_NEVER_returns_an_absolute_path PASSED [100%]

    ====================== 10 passed, 172 deselected in 0.67s ======================
    ```

    `test_the_WITHIN_RUN_collapse_SURVIVES_one_lane_named_twice_in_one_run` is the required proof (one run naming a lane by BOTH an attempt and the item-level `preserved_*` fields still yields exactly ONE record), and `test_TWO_DISTINCT_lanes_are_NOT_collapsed_into_one_row` guards the opposite error.

    THE DOCSTRING WAS CORRECTED, as the item required: `stranded_lane_records` now documents the de-duplication as TWO stages and explains what each answers, rather than describing a single key that no longer decides the reported set alone.

    WHOLE-PLAN EVIDENCE IS RECORDED HERE, per the plan's instruction that V-04's surface is the report itself. BASELINE, captured in THIS executing lane at HEAD `07dabf1b` BEFORE any edit, bare `python3 -m pytest`: `1 failed, 8368 passed, 3 skipped, 2 xfailed in 108.06s`. The single failure was `tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`, which PASSES in isolation (`1 passed in 0.74s`) and is therefore a pre-existing flake, not a baseline defect and not caused by this plan. Note F-11's expectation of a fully green baseline is nearly right; the 31-failure figure the plan warns against carrying was correctly not carried.

    AFTER, bare `python3 -m pytest` in the same tree:

    ```
    8394 passed, 3 skipped, 2 xfailed in 89.07s (0:01:29)
    ```

    FULLY GREEN. Compared BY FAILING NODE ID as required: the baseline's one failing node id is absent from the after-run, and no new failing node id appears. Net +26 tests (8368 -> 8394), which is the 26 tests this plan adds (20 in `test_runner_shared.py`, 5 in `test_attention.py`, plus the amended existing display test still passing).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: a row (or unit test) for a lane whose worktree is absent, pasted, showing NO `worktree` segment; and one whose worktree EXISTS, showing the repo-relative path still rendered (at review 6 of 25 existed, so this case is real and not hypothetical). Paste the guard's source and confirm it protects the SUCCESS return of `lane_worktree_display` and not only the except-branch reconstruction, since measurement showed 25 of 25 records take the success path. Confirm by inspection that no surface emits an absolute path.
  - Observed evidence: measured against the live record set. Of 13 rows, exactly **1 names a worktree and 12 omit it**, and that split is CORRECT: the 12 omitted directories are genuinely gone and the 1 rendered directory genuinely exists.

    ```
    rows naming a worktree: 1
        aw/lane/review-sweep-run-20260919T133719Z-1618106 .aw/worktrees/review-sweep-run-20260919T133719Z-1618106

    $ ls -d <main>/.aw/worktrees/review-sweep-run-20260919T133719Z-1618106
    <main>/.aw/worktrees/review-sweep-run-20260919T133719Z-1618106      # EXISTS, so still rendered

    --- the 12 whose segment is now omitted, each confirmed absent on disk ---
    03ie04 absent   2c122z absent   58ha43 absent   7p9n2v absent
    d7qoxv absent   fn2l1u absent   mm5p3v absent   nna8yz absent
    qcqhj7 absent   r2i1b1 absent   rchpms absent   ybkmzp absent
    ```

    A ROW FOR AN ABSENT LANE, pasted, showing NO `worktree` segment (compare the review-sweep row above, which has one):

    ```
    aw/lane/03ie04 | attention.lane-stranded
        STRANDED lane; plan 03ie04; 2 commit(s) beyond base; integration_signal=suite-failed; run run-20260908T030747Z-1812636: the lane holds work that is NOT reachable from HEAD. Recover it with `aw oc integrate 03ie04`.
    ```

    THE OMISSION IS CONDITIONAL, NOT BLANKET, which the item required because a blanket removal would destroy true information: direct probe of the same function on an absent and a present path under the same repo:

    ```
    absent  exists? False -> None
    present exists? True  -> '.aw/worktrees/0ta5vg'
    outside-repo absent   -> None
    empty                 -> None
    ```

    THE GUARD'S SOURCE, and it protects the SUCCESS RETURN (the branch measurement showed every record actually takes) as well as the reconstruction:

    ```python
        def _exists(path: Path) -> bool:
            # An unreadable path is treated as ABSENT rather than raising: the fallback is to omit one
            # display segment, which is the conservative direction for a rendering decision.
            try:
                return path.exists()
            except (OSError, RuntimeError):
                return False

        try:
            candidate = Path(str(worktree))
            root = Path(repo).resolve()
            resolved = candidate.resolve()
            rel = resolved.relative_to(root)
        except (ValueError, OSError, RuntimeError):
            raw = Path(str(worktree))
            name = raw.name
            parent = raw.parent.name
            if parent == "worktrees" and name and _exists(raw):
                return ".aw/worktrees/{0}".format(name)
            return None
        if not _exists(resolved):          # <-- guards the SUCCESS return
            return None
        text = rel.as_posix()
        return text if text not in ("", ".") else None
    ```

    F-4a IS CONFIRMED BY TEST, not merely trusted: `test_the_guard_protects_the_SUCCESS_return_not_only_the_reconstruction` asserts that `Path.resolve().relative_to(root)` SUCCEEDS for an absent directory (so the success path really is the one taken), asserts the function now returns None for it, and pins the guard line `if not _exists(resolved):` by source inspection. The except-branch is guarded too and still covered for an outside-the-repo worktree that EXISTS.

    NO SURFACE EMITS AN ABSOLUTE PATH, by inspection and by test. Every return in the function is either None, a `relative_to`-derived relative POSIX string, or the `.aw/worktrees/<name>` reconstruction; none can be absolute. `test_NO_surface_ever_renders_an_ABSOLUTE_path` asserts `Path(got).is_absolute()` is False across five input shapes, the pre-existing `test_worktree_display_NEVER_returns_an_absolute_path` still passes (amended, see below), and `test_neither_surface_contains_an_ABSOLUTE_path` in `tests/test_attention.py` still passes for both the human and JSON surfaces. F8a is preserved in the same direction, since omission strictly REDUCES what is printed.

    ONE PRE-EXISTING TEST WAS AMENDED, DELIBERATELY AND NARROWLY, and it is named here rather than left for a reader to find: `test_worktree_display_NEVER_returns_an_absolute_path` asserted that an ABSENT outside-the-repo worktree returns the `.aw/worktrees/lane09` reconstruction, which is exactly the behavior E-05 changes. Its own comment already permitted either outcome ("reduced to the canonical lane shape OR OMITTED"). The assertion was updated to expect omission for the ABSENT path and a NEW assertion added exercising the reconstruction branch for an outside-the-repo worktree that EXISTS, so branch coverage is retained and the invariant the test exists for (no absolute prefix ever survives) is still asserted on every branch. It PASSED, shown in V-04's output above.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: `python3 -c "from agent_workflows import attention; print(attention.lane_remedy_hint())"` output pasted showing the `aw oc integrate` remedy; plus pytest output for the fallback case (symbol patched away) AND for the new test that fails if the probed name disappears.
  - Observed evidence: the no-argument call, which the item required to keep working:

    ```
    $ python3 -c "from agent_workflows import attention; print(attention.lane_remedy_hint())"
    Recover it with `aw oc integrate <id6>`.
    ```

    BEFORE this change the same command printed the dead-end hint, which is the defect: `Recover it by hand: `git log main..<branch>` to see the work, then merge that branch (no `aw integrate` verb exists yet).` The probe was `hasattr(oc_runipd, "cmd_integrate")` = False while `hasattr(oc_runipd, "handle_integrate_command")` = True, so F-5 is confirmed.

    NAMING THE CONCRETE COMMAND, via the optional parameter, shown in a live row: `Recover it with `aw oc integrate 03ie04`.` All 13 reported rows now carry the real verb (`rows with remedy aw oc integrate: 13`).

    ```
    $ python3 -m pytest tests/test_attention.py -o addopts="" -k "LaneRemedyHint" -v
    collected 69 items / 64 deselected / 5 selected

    tests/test_attention.py::LaneRemedyHintTests::test_it_DEGRADES_to_the_manual_hint_when_the_verb_is_genuinely_absent PASSED [ 20%]
    tests/test_attention.py::LaneRemedyHintTests::test_the_hint_names_the_CONCRETE_command_when_given_an_id6 PASSED [ 40%]
    tests/test_attention.py::LaneRemedyHintTests::test_the_stranded_row_carries_the_concrete_remedy PASSED [ 60%]
    tests/test_attention.py::LaneRemedyHintTests::test_the_hint_names_the_integrate_verb_that_really_exists PASSED [ 80%]
    tests/test_attention.py::LaneRemedyHintTests::test_the_PROBED_SYMBOL_really_exists_on_BOTH_hosts PASSED [100%]

    ======================= 5 passed, 64 deselected in 0.29s =======================
    ```

    THE FALLBACK CASE = `test_it_DEGRADES_to_the_manual_hint_when_the_verb_is_genuinely_absent`, which points the probe at a name that is really absent and asserts the manual hint returns, proving the conditional is LIVE rather than effectively constant (which is what the old probe had become). The function's documented rule is kept intact: do not print a verb that does not exist.

    THE TEST THAT FAILS IF THE PROBED NAME DISAPPEARS = `test_the_PROBED_SYMBOL_really_exists_on_BOTH_hosts`, which asserts `hasattr` for the probed symbol on BOTH `oc_runipd` and `agy_runipd` and carries a failure message naming the consequence ("lane_remedy_hint would silently fall back to the manual hint again"). This is the fix for the ACTUAL defect: the old probe's unobservability, not the wrong string. The probed name is a module constant, `attention.LANE_INTEGRATE_PROBE_SYMBOL`, so it is referenced by the code AND by the test rather than being a bare literal nothing else mentions.

    THE SIGNATURE CHANGE WAS DONE AS THE ITEM DIRECTED: `id6` is an OPTIONAL parameter, the no-argument call still works (asserted above and in `test_the_hint_names_the_CONCRETE_command_when_given_an_id6`), the value is passed in from the per-record loop that already has `rec`, and nothing is read from module state. HOST-NEUTRALITY: both hosts were verified to carry the verb, so the hint names `aw oc integrate` as a real route rather than hardcoding a host that might not have it.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: the F3a diff pasted, plus the `aw specs note` invocation and its output and the appended history record naming this plan. Paste the spec's `- Status:` line BEFORE and AFTER showing it UNCHANGED at `implemented`, and confirm no status transition was attempted (it would be refused: `implemented -> *` permits only `superseded`/`deferred`). Confirm the fail-closed posture, the run-record-not-filesystem rule and F8a are unchanged. State whether a content-landed clause was written, and if so confirm E-01/E-02 actually shipped so the spec does not assert an unimplemented reading. State explicitly whether `landed_by` reached the `--json` payload and therefore whether `SCHEMA_VERSION` was bumped from 4. Paste `aw check specs`.
  - Observed evidence: THE F3a DIFF, four clauses APPENDED to F3a and no existing line touched:

    ```diff
    @@ -231,6 +231,10 @@
       TWO EXCLUSIONS ARE NORMATIVE, ... requires a reachability test against the target ...
    +  REACHING THE TARGET IS NOT ONLY ANCESTRY, amended by plan `0ta5vg` because the narrower reading licensed the very failure the exclusion above forbids. "Has reached the integration target" MUST be evaluated by at least TWO readings: ANCESTRY (exact for the shapes the drivers produce themselves, a fast-forward or a controlled `--no-ff` merge) and CONTENT, meaning every commit the lane adds beyond its base is already present on the target BY PATCH ID, which additionally sees a CHERRY-PICK or a REBASE. The content reading is required because this toolkit's own race-recovery remedies instruct an operator to cherry-pick a preserved commit, so a lane whose work landed that way is not an ancestor of the target while holding nothing the target lacks; failing it is exactly the false STRANDED this exclusion prohibits.
    +  THREE CONSTRAINTS ON THE CONTENT READING ARE NORMATIVE, because each of them was measured to be a hazard rather than a nicety. (a) A DIRTY LANE MUST NOT BE SILENCED BY IT ... (b) AN UNANSWERABLE READING MUST NOT RESCUE A LANE ... (c) AN EMPTY COMPARISON IS NOT LANDED ... The composition is therefore strictly NARROWING and fail-closed: the content reading may only ever turn a reported lane silent, never the reverse.
    +  ONE LANE IS AT MOST ONE ROW. The reported set MUST be de-duplicated per lane BRANCH, not per (run, lane) pair: a lane touched by N runs is ONE thing needing ONE human act ... The retained row MUST carry the run evidence forward (how many runs named the lane, and which is newest) so collapsing loses no fact.
    +  A WORKTREE THAT IS NOT ON DISK MUST NOT BE RENDERED. ... This existence check is a RENDERING decision only and is NOT an exception to the run-record-not-filesystem rule above: it decides whether one already-derived display field is printed, and never any part of the lane's VERDICT.
       This clause adds NO write of any kind. `aw attention` remains READ-ONLY (G3, Section 8.1) ...
    ```

    THE INVOCATION AND ITS OUTPUT:

    ```
    $ aw specs note .aw/records/specs/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md --message "AMENDED by plan 0ta5vg (stranrep-01): ..."
    aw specs note: appended a history record to .aw/records/specs/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md
    ```

    THE HISTORY RECORD NAMING THIS PLAN (newest first, matching the convention this plan's own review established when an oldest-first order tripped `check.lifecycle-transition-invalid`):

    ```
    - 2026-09-19 note (aw specs): AMENDED by plan 0ta5vg (stranrep-01): F3a's landing exclusion now REQUIRES two readings, ancestry AND content ...
    - 2026-09-17 note (aw specs): AMENDED by plan pr5b0t (lanestrand-01): F3 gains F3a, the UNINTEGRATED-LANE condition ...
    ```

    THE `- Status:` LINE, BEFORE and AFTER, UNCHANGED:

    ```
    BEFORE: - Status: implemented
    AFTER:  - Status: implemented
    ```

    NO STATUS TRANSITION WAS ATTEMPTED. `aw specs set` was never invoked against this spec; only `aw specs note`. This is not merely a choice but the only legal route, as the item records: `attention_contract.SPEC_TRANSITIONS['implemented']` is `{superseded, deferred}`, so every review-ish target would be refused. The status should not change anyway, since this is an amendment to an implemented contract rather than a reversion.

    UNCHANGED NORMATIVE CLAUSES, confirmed by reading the diff above: the FAIL-CLOSED POSTURE (F3a's opening sentence and F3's set are byte-identical; the new clauses only NARROW which lanes qualify, and clause (b) explicitly preserves fail-closed for an unanswerable reading), the RUN-RECORD-NOT-FILESYSTEM RULE (byte-identical, and the new worktree clause explicitly states it is a RENDERING decision and NOT an exception to it), and F8a (byte-identical, and the new clause re-affirms it). No other normative clause changed; `SCAN_ROOTS` is untouched, which `test_scan_roots_are_unchanged_so_no_filesystem_walk_decides_this` still pins.

    A CONTENT-LANDED CLAUSE WAS WRITTEN, and it is legitimate because E-01/E-02 ACTUALLY SHIPPED: `runner_shared.lane_work_landed_by_content` exists and `classify_lane_integration` consults it (V-01 and V-02 pasted the source and the passing tests). So the spec does not assert an unimplemented reading. Note E-07's conditional branch (if E-08 had chosen (i) drop, amend for the one-row rule ONLY) does NOT apply: V-08 recorded decision (ii) keep.

    `landed_by` DID NOT REACH THE `--json` PAYLOAD, and `SCHEMA_VERSION` was therefore NOT bumped, confirming F-8's prediction:

    ```
    schema_version: 4
    landed_by in payload? False
    stranded_lanes keys: ['branch', 'detail', 'rule']
    SCHEMA_VERSION const: 4
    ```

    `render_json` puts only `{branch, rule, detail}` per lane into `stranded_lanes`, so the field stays internal to the record and F8's bump obligation is not triggered.

    ```
    $ aw check specs
    AW check  specs                                                            49 ms
    ✓ CONFORMS  17 specs checked

    Evidence
      checked  17
      errors  0   warnings  0
    ```

    A DEFECT IN `aw specs note` WAS FOUND AND WORKED AROUND, filed as backlog `i8wmte` (bug, high, `Blocks-Release: next`) and reported in this turn's defect report. It prints "appended a history record" but REPLACES the whole `## Workflow history` body, deleting the prior `pr5b0t` record; reproduced in isolation on throwaway specs, and for a spec with NO `- Id:` (which this legacy-named spec is) the gitignored `.aw/records/history.jsonl` sidecar receives nothing either, so the record is destroyed outright. The `pr5b0t` record was RESTORED here from `git show HEAD:<spec>` so this plan does not land a history deletion; the tool fix belongs to `i8wmte`, not to this plan's scope.
  - Result: pass

WHOLE-PLAN EVIDENCE, required in addition to the per-item evidence above and recorded at V-04 (whose surface is the report itself): bare `python3 -m pytest` output with the actual `N passed` summary line pasted, against a pre-change baseline captured in the EXECUTING tree at the same HEAD and compared by failing NODE ID. Do not carry a failure-count expectation from another plan's review; measured at review in this lane the suite was fully green (`8258 passed, 3 skipped, 2 xfailed`).

AND the `aw attention --check` exit code, together with the run-root the measurement resolved to (print it; the resolver escapes a lane, see Step 0). THE EXPECTED EXIT IS 1, NOT 0, AND THAT IS A PASS. Corrected at review: the authored criterion demanded exit 0 "if no lane genuinely holds unintegrated work", but all 17 reported lanes DO hold such work (F-9), so exit 1 is the truthful result and this plan does not change it. What must be shown instead is that the FAILURE GOT SMALLER AND TRUER: the row count fell to one per lane (25 -> 17 at review, re-derive), no row names a worktree that is absent from disk, the remedy names `aw oc integrate`, and every remaining row is a lane whose commits are genuinely absent by both readings. An exit of 0 here would be evidence of a BUG (a false LANDED), not of success.


OBSERVED, AND IT IS A PASS:

```
$ aw attention --check ; echo exit=$?
exit=1
```

The run-root resolved to the MAIN checkout (printed in V-03/V-04; the resolver escapes a lane exactly as Step 0's correction says, so the in-lane measurement is real and not a false clean). EXIT 1 IS THE TRUTHFUL RESULT and this plan does not change it: all 13 reported lanes hold commits genuinely absent from the target by BOTH readings (V-03's table shows ancestry False AND content False for every one). An exit of 0 here would be evidence of a BUG, a false LANDED, not of success.

THE FAILURE GOT SMALLER AND TRUER, which is what the corrected criterion demands, and every clause of it is measured:

| criterion | before | after |
|---|---|---|
| rows | 20 | **13** |
| distinct lanes | 13 | 13 (unchanged: no lane lost) |
| max rows for one lane | 3 | **1** |
| rows naming a worktree absent from disk | 12 | **0** |
| rows naming a worktree that exists | 1 | 1 (still rendered) |
| rows whose remedy names a verb that exists | 0 | **13** |
| lanes whose commits are genuinely absent by both readings | 13 | 13 |

Every remaining row is a lane whose commits are genuinely absent by both readings, so the residue is fail-closed behavior working as designed on a corpus of genuinely unlanded work, not a residual bug and not a shortfall of this plan. Closing those rows requires the lanes' DISPOSITION, which is plan `ut0vzr`'s.

## Approval and execution gate

- Size assessment: standard
- Size note: 8 E-leaves in 3 groups (7 at authoring; E-08 added at review as a measurement gate that writes no code).
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The four defects are ONE cohesive change (the same ~60 lines across two modules) authored as one plan at the maintainer's explicit direction, having considered a two-child Set and rejected it as lifecycle overhead for that blast radius.

READ THIS BEFORE EXECUTING, ADDED AT REVIEW. The plan splits cleanly into two halves with very different measured standing, and an executor should know which is which. E-04, E-05 and E-06 are INDEPENDENTLY VALID and measurably fix real defects: 25 rows become 17, 19 phantom worktree paths stop printing, and a dead capability probe starts naming a verb that exists. Neither depends on E-01/E-02. By contrast E-01/E-02/E-03 rest on a mechanism measured to resolve ZERO of the 17 reported lanes, which is why E-08 now gates them with an explicit keep/drop/stop decision. If E-08 records "drop", that is a legitimate completion of this plan, not a failure: mark E-01/E-02/E-03 and their V-items `blocked` with the reason and land the rest. And note the plan's Goal was corrected: `--check` will still exit 1 afterwards, because the reported lanes genuinely hold unlanded work.

The executing agent must: commit ONLY files it changed, path-scoped (`git commit -m msg -- <path>`), never `git add -A` or `-a`, and never push; verify the staged set with `git diff --cached --name-only` before EVERY commit and RE-VERIFY after any failed hook, because this is a SHARED checkout with other agents active (backlog `csmtjp` records a concurrent merge being destroyed here, and during this plan's authoring HEAD moved four times and three files belonging to a co-worker appeared and were committed by them); paste ACTUAL runner output rather than claiming success.

NOTHING IN THIS PLAN IS DESTRUCTIVE: it merges no lane, deletes no branch, and removes no worktree. If an E-item appears to require one of those, STOP: the item has been misread, and the disposition of a lane belongs to `ut0vzr`. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry pasted evidence before the plan moves to `.aw/records/plans/executed/`.
