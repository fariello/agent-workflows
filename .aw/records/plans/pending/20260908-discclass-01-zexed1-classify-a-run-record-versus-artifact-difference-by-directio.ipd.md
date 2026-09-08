# IPD: Classify a run-record versus artifact difference by direction with read git evidence instead of one red discrepancy bucket

- Date: 2026-09-08
- Kind: child
- Concern: THE "ARTIFACT & STATUS DISCREPANCIES" TABLE PAINTS LEGITIMATE POST-RUN PROGRESS AS A DEFECT. It compares each queue item's FROZEN run-record status against the artifact's PRESENT-DAY location and status, and reports every difference in red. But a run record is immutable history: gitignored box-local state (`.aw/.gitignore`, `records/runs/`) whose statuses were true when the run ended. When reality legitimately moves on, the table reports the CORRECT new state as a defect.
  MEASURED. After the lanes stranded by `run-20260905T050043Z-639569` were recovered and merged, four rows read `pending/ vs executed/` and `integration-blocked vs executed` (`76gsmv`, `eyh1fu`, `txc9l1`, `uyeko5`). All four are FALSE ALARMS: the record correctly says `integration-blocked` at 11:47Z; the artifacts correctly say `executed` now, because they were integrated afterward. Editing EITHER side to silence it would falsify a record.
  THE TABLE HAS REAL DIAGNOSTIC VALUE, WHICH IS WHY FALSE ROWS COST SOMETHING. The same output surfaced a genuine problem: `eulhzt` showed main's plan copy at 5/8 E-items while its lane copy was finalized at 8/8, which is how a fifth stranded lane was found and recovered. A four-row false-positive block trains an operator to skim past exactly the rows that matter.
  THE CODE IS STILL EXACTLY AS THE ITEM DESCRIBES, re-verified at HEAD `fac69fbd` by symbol. `StepArtifactAudit` (`agent_workflows/run_viewer.py:427`) carries the boolean triple `missing_entirely` (`:431`), `location_mismatch` (`:432`), `status_mismatch` (`:433`) and nothing directional. `audit_step_artifact` (`:467`) reads exactly two things: `actual_file.parent.name` (`:508`) and `_STATUS_LINE_RE` (`:423`) searched at `:515`. `format_artifact_audit_summary` (`:1419`) selects rows with `if a.missing_entirely or a.location_mismatch or a.status_mismatch` (`:1431`) and styles them red (`:1461`, `:1469`, `:1483`, `:1491`). The module touches git ZERO times: `grep -c subprocess` returns 0, and its imports are `argparse, json, re, sys, collections, dataclasses, datetime, pathlib, typing` plus first-party `agent_schema`, `platform_lock`, `attention`, `render_stream`, `term`. The table title is at `:1504` (the item cites `:1346`; it drifted ~158 lines, which is why every citation here was re-located by symbol).
  THE PREVIOUS ATTEMPT WAS ABANDONED AS UNSOUND AND THE REASON STILL BINDS. A 2026-09-05 maintainer ruling refused to infer "resolved" from lifecycle DIRECTION alone, because a legitimately finalized-and-integrated plan and a hand-edited `- Status: executed` plus `git mv` are BYTE-IDENTICAL to this audit. Classifying that pair as resolved would print a green OK for the exact bypass the executed-transition-gate hook exists to catch. THE UNBLOCKING FACT: the ruling named what a grounded fix needs, first option listed, "the in-tree `lifecycle(<id6>): finalize` commit read from git history", and that evidence form is now hook-enforced and established (`_intree_finalize_evidence_ok`, `agent_workflows/hooks/executed_transition_gate.py:261`). So the classifier can READ evidence instead of guessing.
- Scope: Replace the boolean mismatch pair with a DIRECTIONAL classification (`resolved`/`regressed`/`missing`/`unchanged`, plus an explicit `unknown`) grounded in a READ git-history check for the in-tree finalize commit, reserving the red styling for a difference that indicates something actually wrong, and keeping an unprovable row VISIBLE as `unknown` rather than green. EXCLUDES the `interrupted`-vs-`approved` row (`vdabn5` owns it and lands first); EXCLUDES extracting or relocating the audit (`6ltz1y` owns that and MUST land first); EXCLUDES the five-copy issue predicate's consolidation (`r2i1b1` E-03 owns it); EXCLUDES the run summary's outcome word (`ys1dor`) and the attention view (`pr5b0t`).
- Scope-Paths: agent_workflows/run_viewer.py, tests/test_run_viewer.py
- Item-Dependencies: none
- Status: to-review
- Set: discclass
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: zexed1
- From-Backlog: 1f9m2j

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `1f9m2j`. PARTIALLY OBSOLETE, ONE PARAGRAPH DEAD, AND THE SURVIVING CORE IS EXPLICITLY DISCLAIMED BY THREE PENDING PLANS, which is the strongest evidence it is genuinely unowned. DEAD: the item's final "ALSO WORTH CHECKING" paragraph, the `i6015i` row reading `interrupted` vs `approved`. Pending plan `vdabn5` (`runviewdisc-02`, `to-review`, `From-Backlog: 13ty0u`) E-01 adds `interrupted` to the existing status-tolerance branch (`run_viewer.py:527-536`, where `interrupted` is absent so it falls to the catch-all at `:537-539`), which makes that row not appear at all. Note the DIFFERENCE from what the item asked: `vdabn5` SUPPRESSES the row, it does not create the item's proposed separate bucket ("never completed; re-run needed"). If the bucket is still wanted it survives as a nuance, and E-03 here handles it; the alarm itself is `vdabn5`'s. ALIVE AND UNOWNED: the whole four-way classifier, the `integration-blocked` -> `executed` false-positive block, the git-evidence read, and the UNKNOWN treatment. `vdabn5` refuses them in writing four times (`:9` "excludes any new classification vocabulary or direction-aware classifier"; `:38` "PREFER EXTENDING THE EXISTING MECHANISM"; `:100` "ANY DIRECTION-AWARE CLASSIFIER ... That is what `1f9m2j` wanted and it proved unsound"; `:101` "THE `integration-blocked` + `executed` CASE. Backlog `1f9m2j`"). No code anywhere carries the vocabulary: `grep -rn "regressed" agent_workflows/*.py` returns nothing. ONE HARD ORDERING CONSTRAINT, which is why this plan must not be executed first: `6ltz1y` (`auditshare-01`, `to-review`) E-02 MOVES `audit_step_artifact` and `StepArtifactAudit` into a NEW module `agent_workflows/artifact_audit.py`, asserted by object identity, and its E-04 adds `aw doctor` as a SECOND consumer. So after it lands, this fix belongs in that module and must serve two surfaces. There is also a conflict of INTENT a reviewer must see: `6ltz1y` E-01 and its deferral forbid changing ANY audit verdict, while this plan changes verdicts. The two are compatible only SEQUENTIALLY, `6ltz1y` first, and this plan's `Item-Dependencies` is deliberately left `none` because `6ltz1y` is not yet `approved` and a hard edge to a to-review plan would wedge the queue; the constraint is stated in E-01 and OQ-03 instead. SECOND ORDERING NOTE: `r2i1b1` (`orchprobe-01`, `reviewed`) E-03 extracts the FIVE copies of the issue predicate (measured today at `run_viewer.py:1431`, `:1580`, `:2781`, `:2825`, `:2856`) into ONE function and E-04 extends it, so a classifier replacing the boolean pair must route through whatever predicate exists then. THE ITEM'S GATE IS CLOSED AND ITS EVIDENCE RE-MEASURED: `rnl3b7` is `done`, graduating to `29wvmj` (executed), which added `_intree_finalize_evidence_ok` (`executed_transition_gate.py:261`, the item's citation is EXACT). All five cited id6s have a finalize commit reachable from HEAD, verified per id6 with `git merge-base --is-ancestor`: `76gsmv` `443bbed4`, `eyh1fu` `c9db21a3`, `txc9l1` `43c87af5`, `uyeko5` `251b7399`, `eulhzt` `dd996d73`. The item's own self-correction about the `head -1` measurement artifact is CONFIRMED (four of the five match TWO commits, with the `integrate(manual)` merge listed first because `--grep` matches the message BODY, so a `head -1` hides the real finalize commit); build on the corrected version. ONE FINDING THE ITEM DID NOT HAVE, and it changes E-02: `_intree_finalize_evidence_ok` is NOT reusable as-is. It requires `incoming_commits` from a merge IN PROGRESS and evaluates the range `HEAD..<incoming>` (`:280`), whereas a read-only viewer needs "is a `lifecycle(<id6>): finalize` commit reachable from HEAD". Its nearest sibling `_lifecycle_commit_exists` (`ipd_lifecycle.py:1852`) checks only the TIP against a `pre_head` the viewer does not have. The subject string is not a shared constant (written at `ipd_lifecycle.py:2724`, matched at `executed_transition_gate.py:278`, prefix-matched at `ipd_lifecycle.py:1868`), and there is no general git-history helper (`grep -rn "log --grep" agent_workflows/` returns nothing). So E-02 must add a small reader and should promote the subject to one shared constant. DELIBERATELY NO `Blocks-Release`: the source item carries none (verified, no `Blocks-Release`, `Gate-Kind` or `Gate-Ref` in `1f9m2j`), so none is inherited; this is a false-positive reduction on a diagnostic table, not a release blocker.

## Goal

Make the discrepancy table's red mean "something is actually wrong" by classifying a difference by DIRECTION and grounding "resolved" in a git-history fact the viewer can read, so the four false rows stop training operators to skim past the fifth real one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: locate the code and characterize today's verdicts

- [ ] E-01 RE-LOCATE THE AUDIT AND DECIDE WHERE THIS FIX BELONGS, before writing anything, because the code may have MOVED. `6ltz1y` (`auditshare-01`) E-02 relocates `audit_step_artifact` and `StepArtifactAudit` into a new `agent_workflows/artifact_audit.py` with `run_viewer` keeping no local definition, and its E-04 adds `aw doctor` as a second consumer.
  IF `6ltz1y` HAS LANDED: implement in `artifact_audit.py`, and check what the SECOND consumer (`aw doctor`) does with the verdicts, because a directional classification must serve both surfaces and `aw doctor`'s use is advisory and liveness-aware.
  IF IT HAS NOT LANDED: implement in `run_viewer.py` and say so, and keep the change shaped so the later move is mechanical (one dataclass, one function, no new cross-module coupling).
  EITHER WAY, RECORD THE INTENT CONFLICT RATHER THAN STEPPING ON IT. `6ltz1y` E-01 and its deferral forbid changing ANY audit verdict, because its whole value is a provably behavior-preserving extraction. This plan CHANGES verdicts. If `6ltz1y` is still pending, executing this plan first would invalidate its characterization baseline; that is a real cost to a sibling plan and must be reported to the maintainer, not absorbed silently.
  CHARACTERIZE TODAY'S VERDICTS FIRST, on fixtures, so the change is measured rather than asserted: for each of `missing_entirely`, `location_mismatch`, `status_mismatch`, capture the input shape that produces it and the row it renders.
  - Depends on: none
  - Expected outcome: a recorded decision on the implementation module with `6ltz1y`'s status stated, the intent conflict reported if it is still pending, and a characterization of all three current boolean verdicts with their input shapes.
  - Execution state: pending

### Task group 2: read the evidence, then classify on it

- [ ] E-02 ADD A READ-ONLY GIT REACHABILITY CHECK FOR THE IN-TREE FINALIZE COMMIT, and do NOT reuse `_intree_finalize_evidence_ok` as-is: it answers a different question. That function (`hooks/executed_transition_gate.py:261`) requires `incoming_commits` from a merge IN PROGRESS and evaluates the range `HEAD..<incoming>` (`:280`), while the viewer needs "is a `lifecycle(<id6>): finalize` commit REACHABLE FROM HEAD". Its sibling `_lifecycle_commit_exists` (`ipd_lifecycle.py:1852`) checks only the tip against a `pre_head` the viewer does not have.
  PROMOTE THE SUBJECT STRING TO ONE SHARED CONSTANT. `lifecycle(<id>): finalize` is currently written literally in three places: produced at `ipd_lifecycle.py:2724`, matched at `executed_transition_gate.py:278`, prefix-matched at `ipd_lifecycle.py:1868`. A fourth literal is how the gate and the viewer silently disagree later. One constant, three (then four) references.
  BEWARE THE MEASUREMENT ARTIFACT THE ITEM ITSELF FELL INTO AND CORRECTED. `git log --grep` matches the full commit MESSAGE BODY, and the manual merge commits QUOTE the hook's demand in their bodies, so they match the finalize pattern; a `head -1` hides the real finalize commit underneath. Match on the SUBJECT (`--format=%s` and compare) exactly as `_intree_finalize_evidence_ok` does at `:280-285`, never on a body grep, and never take only the first match.
  THIS IS THE MODULE'S FIRST GIT DEPENDENCY, so treat it as a design change and not a line. `run_viewer.py` touches git ZERO times today (`grep -c subprocess` -> 0). Every failure mode must be handled: not a git repository, `git` not on PATH, a shallow clone, a detached HEAD, a nonzero exit, a timeout. EVERY ONE OF THEM RESOLVES TO `unknown`, never to a silent OK. Also consider cost: the table can hold many rows, so avoid one subprocess per row if a single query answers all of them.
  - Depends on: E-01
  - Expected outcome: a read-only reachability check matching on the commit SUBJECT via one shared constant, every failure mode resolving to `unknown`, no `head -1` style first-match logic, and a stated approach to per-row subprocess cost.
  - Execution state: pending

- [ ] E-03 REPLACE THE BOOLEAN PAIR WITH A DIRECTIONAL CLASSIFICATION carrying `resolved`, `regressed`, `missing`, `unchanged` and an explicit `unknown`. The item's shape is `resolved`/`regressed`/`missing`/`unchanged`; `unknown` is ADDED here and is not optional, because it is what keeps the 2026-09-05 ruling satisfied.
  `resolved` REQUIRES EVIDENCE, NOT DIRECTION. This is the entire reason the previous attempt was abandoned. A row may be classified `resolved` only when BOTH the lifecycle direction is forward (run-status `integration-blocked`/`substantially-complete`/`interrupted` -> artifact `executed` in `executed/`) AND E-02's reachability check finds the finalize commit. Direction alone must yield `unknown`, because a legitimate finalize and a hand-edited `- Status: executed` plus `git mv` are byte-identical to this audit, and calling that pair resolved would print a green OK for exactly the bypass the executed-transition-gate hook exists to catch.
  `regressed` IS THE ROW THAT KEEPS THE RED. The run recorded `executed` but the artifact is NOT in `executed/`, or the artifact is missing entirely: evidence the finalize did not stick. This is where the styling at `:1461`/`:1469`/`:1483`/`:1491` belongs, and the `eulhzt`-class real find must still land here.
  DECIDE THE `interrupted` ROW'S BUCKET, WITHOUT OWNING THE ALARM. `vdabn5` E-01 suppresses that row by adding `interrupted` to the tolerance branch (`:527-536`), and it lands first. If it has landed, the row is already gone and there is nothing to bucket; say so. If the item's proposed distinct bucket ("never completed; re-run needed") is still wanted on top, it is a nuance ON `vdabn5`'s work and must not re-introduce an alarm that plan deliberately removed.
  DO NOT COLLAPSE `unknown` INTO `unchanged`. They mean opposite things: `unchanged` is a positive finding, `unknown` is a confession. Conflating them is how a green OK reappears.
  - Depends on: E-02
  - Expected outcome: a five-value classification replacing the boolean pair, `resolved` gated on BOTH direction and E-02's evidence, `regressed` retaining the red, `unknown` distinct from `unchanged`, and the `interrupted` row's disposition recorded relative to `vdabn5`.
  - Execution state: pending

### Task group 3: render honestly and route through one predicate

- [ ] E-04 RENDER EACH CLASS DISTINCTLY AND KEEP EVERY UNPROVEN ROW VISIBLE, in `format_artifact_audit_summary` (`:1419`). Reserve the red (`:1461`, `:1469`, `:1483`, `:1491`) for `regressed` and `missing`. `resolved` reports in a non-alarming style or a separate section. `unknown` STAYS VISIBLE with its reason stated, because the whole point of the 2026-09-05 ruling was to refuse a green OK the data does not support.
  DO NOT SUPPRESS `unknown` BEHIND A FLAG. The item offers "suppress behind a flag" as one option for the resolved case, and that is acceptable for `resolved` (which HAS evidence). It is not acceptable for `unknown`: an invisible confession is indistinguishable from a green OK to every reader.
  SAY WHY A ROW IS `unknown`, in the row. "No finalize commit reachable" and "git unavailable" are different operator situations and a bare `unknown` teaches nothing.
  - Depends on: E-03
  - Expected outcome: `regressed`/`missing` red, `resolved` non-alarming or sectioned, `unknown` always visible with a per-row reason, and no suppression path for `unknown`.
  - Execution state: pending

- [ ] E-05 ROUTE THE ISSUE PREDICATE THROUGH WHATEVER SINGLE DEFINITION EXISTS, and do not add a sixth copy. The boolean triple is currently tested in FIVE places: `run_viewer.py:1431`, `:1580`, `:2781`, `:2825`, `:2856`.
  `r2i1b1` (`orchprobe-01`, `reviewed`) E-03 EXTRACTS THOSE FIVE INTO ONE FUNCTION and its E-04 extends that one predicate to count a refusal as an issue. If it has landed, change THAT function and nothing else. If it has not, this plan must not do the extraction (it is another plan's E-item) but must also not leave five hand-edited copies of a five-value classification, which would be strictly worse than the boolean version. State which situation you are in and what you did.
  IF `r2i1b1` HAS NOT LANDED, the honest minimum is a single helper used by all five sites, introduced without renaming or relocating anything, so `r2i1b1` E-03 can still complete its extraction. Report the overlap.
  - Depends on: E-04
  - Expected outcome: exactly one definition of "is this row an issue" consulted by all call sites, with `r2i1b1`'s status stated and its E-03 left able to complete.
  - Execution state: pending

### Task group 4: prove it on the measured cases

- [ ] E-06 PROVE ALL FIVE CLASSES ON FIXTURES, including the two the ruling was written about. Minimum cases: (a) forward direction WITH a reachable finalize commit -> `resolved`; (b) forward direction WITHOUT one -> `unknown`, NOT resolved; (c) run says `executed` but artifact is not in `executed/` -> `regressed`, red; (d) artifact missing entirely -> `missing`, red; (e) run and artifact agree -> `unchanged`; (f) git unavailable or not a repository -> `unknown` with a stated reason.
  CASE (b) IS THE ONE THAT MATTERS MOST. It is the hand-edit bypass: `- Status: executed` plus `git mv` with no finalize commit. If it classifies as `resolved`, this plan has reintroduced the exact defect that got the previous design abandoned. Assert it explicitly and quote the assertion.
  REPRODUCE THE MEASURED FOUR-ROW BLOCK AS A FIXTURE, using the shape of the real case (`integration-blocked` in the record, `executed` in `executed/`, a reachable `lifecycle(<id6>): finalize` commit). Show all four go non-red.
  AND KEEP THE REAL FIND RED. Reproduce the `eulhzt`-class row (main's copy behind its lane's finalized copy) and show it still alarms. A classifier that quiets the four false rows and also quiets the true one is a regression, not a fix.
  FIXTURES ONLY, AND NO LIVE RUN RECORDS. `.aw/records/runs/` is gitignored and absent from a fresh worktree, so a test reading it is exactly the defect `utwr6y` (`testiso-01`) exists to remove from this very test file. Build synthetic run trees; note `tests/test_run_viewer.py:22-27` already carries an in-file hazard note saying a new test must NOT read the live repository via `dir='.'`, and `_FIXTURE_RUN`/`_FIXTURE_SETID` constants exist at `:31`/`:33` to build on.
  - Depends on: E-05
  - Expected outcome: six fixture cases passing with case (b) asserted explicitly as `unknown`, the four measured rows shown non-red, the `eulhzt`-class row still red, and no test reading `.aw/records/runs/`.
  - Execution state: pending

- [ ] E-07 PROVE THE RECORD WAS NOT MUTATED AND NOTHING ELSE MOVED, because the item's hard prohibition is not to fix this by editing either side.
  NEGATIVE PROOF ON RUN RECORDS: no `state.json` written, no run record modified. The record's value IS that it freezes what was true, and it is the evidence base for resume, reconciliation and cost accounting.
  NEGATIVE PROOF ON PLANS: `git status --porcelain .aw/records/plans/` clean. Do not move a plan or edit a `- Status:` to make a row classify differently.
  SHOW THE OTHER `aw runs` OUTPUT IS UNCHANGED except the table in question, since `run_viewer.render` produces much more than this section and four other call sites test the same predicate.
  RUN THE SUITE BARE and judge on the DELTA, stating observed counts rather than quoting a baseline.
  - Depends on: E-06
  - Expected outcome: no run record and no plan mutated, the rest of `aw runs` output unchanged, and an empty bare-suite failure-set delta with observed counts stated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE MODULE TOUCHES GIT ZERO TIMES TODAY. `grep -c subprocess agent_workflows/run_viewer.py` -> 0; imports are stdlib plus `agent_schema`, `platform_lock`, `attention`, `render_stream`, `term`. Adding a git read is a design change to this module's dependencies, not a line edit.
- THE AUDIT READS EXACTLY TWO THINGS. `actual_file.parent.name` (`:508`) and `_STATUS_LINE_RE` (`:423`) at `:515`. That is why a legitimate finalize and a hand-edit are byte-identical to it, and why evidence must be READ rather than inferred.
- THE EVIDENCE FORM IS ESTABLISHED AND HOOK-ENFORCED. `_intree_finalize_evidence_ok` (`hooks/executed_transition_gate.py:261`) matches the SUBJECT `lifecycle(<id6>): finalize` via `git log --format=%s` (`:278-285`). But it needs a merge in progress, so it is a MODEL, not a callable for this use.
- THE SUBJECT STRING IS NOT A SHARED CONSTANT. Written at `ipd_lifecycle.py:2724`, matched at `executed_transition_gate.py:278`, prefix-matched at `ipd_lifecycle.py:1868`. Promote it rather than adding a fourth literal.
- THERE IS NO GENERAL GIT-HISTORY HELPER. `grep -rn "log --grep" agent_workflows/` returns nothing; `git_commit_helper.py` exposes only `validate_trailer`, `compose_message_with_trailers`, `run_item_trailers`, `offer_commit`, none of which reads history.
- `--grep` MATCHES THE BODY, WHICH ALREADY CAUSED ONE WRONG MEASUREMENT. Manual merge commits quote the hook's demand, so they match; four of five id6s return TWO commits with the merge first. Match on the subject and never take only the first result.
- THE ISSUE PREDICATE IS COPIED FIVE TIMES: `:1431`, `:1580`, `:2781`, `:2825`, `:2856`. `r2i1b1` E-03 owns consolidating them.
- THE CODE IS ABOUT TO MOVE. `6ltz1y` E-02 relocates the audit into `agent_workflows/artifact_audit.py` and E-04 adds `aw doctor` as a second consumer, and its E-01 forbids changing any verdict. Sequence matters; the conflict is real and must be reported, not absorbed.
- THIS TEST FILE HAS A LIVE-TREE HAZARD NOTE ALREADY. `tests/test_run_viewer.py:22-27` says a new test must NOT read the live repository via `dir='.'`, with `_FIXTURE_RUN`/`_FIXTURE_SETID` at `:31`/`:33`. Honor it; `.aw/records/runs/` is gitignored and absent from a fresh worktree.
- A RUN RECORD IS IMMUTABLE HISTORY. Gitignored box-local state, and the evidence base for resume, reconciliation and cost accounting. Never mutate it to quiet a row.
- Shared checkout, concurrent edits, suite runs BARE. Every citation here was re-located by symbol after the item's own line numbers drifted ~158 lines.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the boolean pair cannot express direction | `StepArtifactAudit` carries only `missing_entirely`/`location_mismatch`/`status_mismatch`; no classifier vocabulary exists anywhere (`grep -rn "regressed" agent_workflows/*.py` -> nothing). | `run_viewer.py:427-433` |
| F-2 | HIGH | four measured false alarms | `76gsmv`, `eyh1fu`, `txc9l1`, `uyeko5` each read `pending/ vs executed/` and `integration-blocked vs executed` after legitimate post-run integration. | item's measurement, retained |
| F-3 | HIGH | and one real find in the same output | `eulhzt` showed main's copy at 5/8 E-items against a lane copy finalized at 8/8, which is how a fifth stranded lane was found. False rows erode exactly this. | item's measurement, retained |
| F-4 | HIGH | the audit cannot distinguish a finalize from a hand-edit | It reads only `actual_file.parent.name` and a `- Status:` regex, so direction-only inference would green-light the bypass the executed-transition hook exists to catch. This is the 2026-09-05 ruling and it still binds. | `:508`, `:515`, `:423` |
| F-5 | HIGH | **the evidence now exists, which is what unblocks the item** | `_intree_finalize_evidence_ok` matches the subject `lifecycle(<id6>): finalize` via `git log --format=%s`; all five cited id6s have a finalize commit reachable from HEAD (`76gsmv` `443bbed4`, `eyh1fu` `c9db21a3`, `txc9l1` `43c87af5`, `uyeko5` `251b7399`, `eulhzt` `dd996d73`, each confirmed with `git merge-base --is-ancestor`). | `executed_transition_gate.py:261`, `:278-285`; measured at HEAD `fac69fbd` |
| F-6 | HIGH | **but it is NOT reusable as-is, which the item did not know** | It requires `incoming_commits` from a merge IN PROGRESS and evaluates `HEAD..<incoming>`; the viewer needs reachability from HEAD. `_lifecycle_commit_exists` (`ipd_lifecycle.py:1852`) checks only the tip against a `pre_head` the viewer lacks. It also has no direct unit test (`grep -rn "_intree_finalize_evidence_ok" tests/` -> nothing). | `:261-286`; `ipd_lifecycle.py:1852-1871` |
| F-7 | MEDIUM | the item's own self-correction is confirmed | `--grep` matches the message BODY and manual merge commits quote the hook's demand, so four of five id6s return two commits with `integrate(manual)` first; a `head -1` hides the finalize commit. Build on the corrected version. | re-measured per id6 |
| F-8 | MEDIUM | **the item's last paragraph is dead** | The `i6015i` `interrupted` vs `approved` row is removed by `vdabn5` E-01, which adds `interrupted` to the tolerance branch. It SUPPRESSES rather than bucketing, so the item's distinct "never completed" bucket survives only as a nuance. | `vdabn5` E-01; `run_viewer.py:527-539` |
| F-9 | MEDIUM | three pending plans explicitly disclaim the core | `vdabn5:9`, `:38`, `:100`, `:101` refuse the classifier by name; `6ltz1y` forbids changing any verdict; `r2i1b1` owns only the predicate copies. Unowned by construction. | those plans |
| F-10 | HIGH | **the code is about to move, and the intents conflict** | `6ltz1y` E-02 relocates `audit_step_artifact`/`StepArtifactAudit` into `artifact_audit.py` (object-identity asserted) and E-04 adds `aw doctor` as a second consumer, while its E-01/deferral forbid changing any verdict. Compatible only sequentially, `6ltz1y` first. | `6ltz1y` E-01, E-02, E-04, deferral |
| F-11 | MEDIUM | five copies of the issue predicate | `:1431`, `:1580`, `:2781`, `:2825`, `:2856`. `r2i1b1` E-03 consolidates them and E-04 extends the one. | measured |
| F-12 | MEDIUM | the previous attempt's replacement went the other way deliberately | `xtklpd` (superseded) was rejected partly because deriving a verdict from this audit "reads the LIVE FILESYSTEM" and so rewrites history; its replacement `ys1dor` deliberately scopes to `render_stream.py` and does not touch `run_viewer.py`. | `xtklpd:26`; `ys1dor:8` |
| F-13 | LOW | the item's gate is closed | `rnl3b7` is `done`, graduated to `29wvmj` (executed), which added the merge-aware in-tree evidence path. | `.aw/records/backlog/done/...rnl3b7...`; `.aw/records/plans/executed/...29wvmj...` |
| F-14 | LOW | the item carries no release gate | No `Blocks-Release`, `Gate-Kind` or `Gate-Ref` in `1f9m2j`, so this plan inherits none. | the item file |
| F-15 | LOW | the test file already forbids live-tree reads | `tests/test_run_viewer.py:22-27` carries the hazard note; `_FIXTURE_RUN`/`_FIXTURE_SETID` at `:31`/`:33`. `.aw/records/runs/` is gitignored and absent from a fresh worktree. | that file |

## Proposed changes (ordered, validatable)

1. Re-locate the audit, decide the implementation module against `6ltz1y`'s status, report the intent conflict, and characterize today's three verdicts (E-01).
2. Add a read-only finalize-commit reachability check on a shared subject constant, with every failure resolving to `unknown` (E-02).
3. Replace the boolean pair with `resolved`/`regressed`/`missing`/`unchanged`/`unknown`, gating `resolved` on evidence AND direction (E-03).
4. Render `regressed`/`missing` red, `resolved` quietly, and `unknown` always visible with a reason (E-04).
5. Route the issue test through one definition without pre-empting `r2i1b1` E-03 (E-05).
6. Prove six fixture cases, especially the no-evidence hand-edit case, the four measured rows going quiet, and the real find staying red (E-06).
7. Prove no run record and no plan was mutated and the rest of the output is unchanged (E-07).

## Deferred / out of scope (with reason)

- THE `interrupted` VS `approved` ROW. `vdabn5` (`runviewdisc-02`) E-01 owns it and lands first; it suppresses the row by adding `interrupted` to the existing tolerance branch. E-03 here only records the disposition and must not re-introduce an alarm that plan deliberately removed.
- EXTRACTING OR RELOCATING THE AUDIT. `6ltz1y` (`auditshare-01`) E-02 moves it to `agent_workflows/artifact_audit.py` and E-04 gives it a second consumer in `aw doctor`. This plan changes BEHAVIOR in place and must not do the extraction. It SHOULD run after, and E-01 states what to do in either case.
- CONSOLIDATING THE FIVE ISSUE-PREDICATE COPIES. `r2i1b1` (`orchprobe-01`) E-03 owns it; E-05 here routes through whatever single definition exists rather than pre-empting it.
- THE RUN SUMMARY'S OUTCOME WORD. `ys1dor` (`integearn-04`) owns `render_stream.py`, deliberately does not touch `run_viewer.py`, and took the opposite route from the abandoned `xtklpd` design for the reason in F-12.
- `aw attention` BLINDNESS TO A STRANDED LANE. `pr5b0t` (`lanestrand-01`, from backlog `nuanaw`) owns it.
- MUTATING ANY RUN RECORD, or editing any plan's `- Status:` or location. The item's hard prohibition, restated because it is the tempting shortcut: the record's value is that it freezes what was true, and it is the evidence base for resume, reconciliation and cost accounting.
- A GENERAL GIT-HISTORY HELPER FOR THE PACKAGE. None exists, and building one here would be an unreviewable widening. E-02 adds the narrow reader this table needs and promotes the subject STRING to a constant; a general helper is a separate decision.
- UNIT-TESTING `_intree_finalize_evidence_ok` ITSELF. It has no direct test (F-6), which is worth knowing, but it belongs to the hook's own suite. Report it; do not adopt it here.
- `aw doctor`'s ADVISORY BEHAVIOR. If `6ltz1y` E-04 has landed, E-01 must CHECK the second consumer, but changing `aw doctor`'s advisory policy is that plan's decision, not this one's.

## Scope check

- Over-scope: none. One dataclass's verdict field, one narrow git read, one render section, one predicate route, one test module.
- Scope-Paths justification: `agent_workflows/run_viewer.py` holds `StepArtifactAudit` (`:427`) and its boolean triple (`:431-433`), `audit_step_artifact` (`:467`) with its two observations (`:508`, `:515`), the status-tolerance branch (`:527-539`) whose `interrupted` case `vdabn5` owns, `format_artifact_audit_summary` (`:1419`) with its row predicate (`:1431`), red styling (`:1461`, `:1469`, `:1483`, `:1491`) and title (`:1504`), and the four other predicate copies (`:1580`, `:2781`, `:2825`, `:2856`); `tests/test_run_viewer.py` holds the fixture constants (`:31`, `:33`) and the live-tree hazard note (`:22-27`) that E-06's cases must honor. NOTE that if `6ltz1y` lands first the first path becomes `agent_workflows/artifact_audit.py`, which E-01 must record and which would require re-declaring scope.
- Under-scope, stated rather than left as `none`: this plan does not extract or move the audit, does not consolidate the five predicate copies, does not own the `interrupted` alarm, does not touch `render_stream.py` or the attention view, mutates no run record and no plan, builds no general git-history helper, does not unit-test the hook's own evidence function, and writes no spec.

## Required tests / validation

- SIX FIXTURE CASES (E-06), each named with pasted output: forward-with-evidence -> `resolved`; forward-WITHOUT-evidence -> `unknown`; run-says-executed-artifact-is-not -> `regressed` red; artifact missing -> `missing` red; agreement -> `unchanged`; git unavailable -> `unknown` with a reason.
- THE NO-EVIDENCE CASE QUOTED SEPARATELY AND EXPLICITLY, since classifying it `resolved` would reintroduce the defect that got the previous design abandoned. Quote the assertion, not just the result.
- THE FOUR MEASURED ROWS REPRODUCED AS A FIXTURE and shown non-red, with the rendered rows pasted.
- THE `eulhzt`-CLASS REAL FIND REPRODUCED and shown STILL RED, pasted. Quieting it would be a regression disguised as a fix.
- THE `unknown` ROW's REASON SHOWN IN THE OUTPUT, for both reasons (no reachable finalize commit; git unavailable), so a reader can tell the two operator situations apart.
- ONE-DEFINITION PROOF for the issue predicate: object identity or grep showing all call sites consult a single definition, with `r2i1b1`'s status stated.
- SUBJECT-CONSTANT PROOF: the `lifecycle(<id6>): finalize` string exists as ONE constant with all references pointing at it, pasted.
- NO-FIRST-MATCH PROOF: show the reachability check compares SUBJECTS and does not take only the first `--grep` result, since that artifact already produced one wrong measurement.
- NEGATIVE PROOF: no run record written or modified; `git status --porcelain .aw/records/plans/` clean; `git diff --stat` limited to the declared paths.
- THE REST OF `aw runs` OUTPUT UNCHANGED apart from this table, since `render` produces much more and four other sites share the predicate.
- `python3 -m pytest` BARE, before and after, both summary lines pasted and the failure-set DELTA stated as a set. Measured in this lane at HEAD `fac69fbd`: `5859 passed, 3 skipped, 2 xfailed`, and `tests/test_run_viewer.py` alone reported `68 passed`. State what YOU observe; the briefing's `1 failed, 5648 passed` baseline does not reproduce here. Criterion: AFTER minus BEFORE is EMPTY.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw ipd lint --phase pre-transition` conforming, pasted.
- `aw sanitize --agent` clean.

## Spec / documentation sync

NO SPEC FILE IS DECLARED, and the reasoning matters because this plan changes what a REPORTED VERDICT MEANS. The discrepancy table is a diagnostic rendering, not a gate: nothing consumes its verdicts to permit or refuse an action, and the executed-transition gate that DOES enforce this evidence is untouched. So no contract moves. If the executor finds a spec constraining the table's verdict vocabulary, STOP, add the spec path to `Scope-Paths`, and say why, per the "a plan may amend a spec, and must declare it" rule.

TWO CODE-LEVEL DOCUMENTATION OBLIGATIONS, both load-bearing rather than cosmetic.

FIRST, THE `resolved` DEFINITION MUST CARRY ITS RULING. Write at the classifier that `resolved` requires BOTH forward direction AND a reachable finalize commit, and WHY: a legitimate finalize and a hand-edited `- Status: executed` plus `git mv` are byte-identical to this audit, so direction alone would print a green OK for the bypass the executed-transition hook exists to catch. Without that sentence, a future reader "simplifies" the evidence check away and silently restores the abandoned design.

SECOND, THE NEW SHARED SUBJECT CONSTANT MUST SAY WHO ELSE READS IT, naming the producer (`ipd_lifecycle.py:2724`), the hook matcher (`executed_transition_gate.py:278`) and the tip check (`ipd_lifecycle.py:1868`), so a change to the commit subject cannot silently desynchronize the gate from the viewer.

OPERATOR-FACING TEXT: the table's own legend or help must explain the five classes, especially that `unknown` means the viewer could not prove either way and the row is deliberately still shown. Write no em or en dashes there.

## Open questions

### OQ-01: Should `resolved` rows be shown quietly or suppressed behind a flag?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: SHOW THEM QUIETLY BY DEFAULT, with suppression permitted for `resolved` ONLY. The item offers three options (non-alarming style, separate section, flag) and any is acceptable for `resolved` because that class HAS evidence behind it. The decision that matters is the one this resolves in the negative: `unknown` must NEVER be suppressible, because an invisible confession is indistinguishable from a green OK, and refusing a green OK the data does not support is the entire point of the 2026-09-05 ruling. E-04 therefore permits a flag for `resolved` and forbids one for `unknown`.

### OQ-02: Is one git subprocess per row acceptable?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: OPEN AS AN IMPLEMENTATION DECISION FOR E-02, deliberately not pre-decided, because the right answer depends on measurement this plan has not made. `run_viewer` touches git ZERO times today, so this is the module's first process spawn, and the table can carry many rows. A single query answering all rows at once is obviously preferable if one exists (for instance one `git log --format=%s` pass over the relevant range, matched in Python). Against premature optimization: correctness first, and a per-row call that is measurably fast enough on a real repository is acceptable. E-02 must state which it chose and why, and must handle the failure modes identically either way. Non-blocking because both routes satisfy the plan.

### OQ-03: Must this plan wait for `6ltz1y`?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN BECAUSE IT IS A SEQUENCING JUDGEMENT WITH A COST TO A SIBLING PLAN, and it is the maintainer's call rather than this plan's. `6ltz1y` (`auditshare-01`) E-02 MOVES the exact code this plan edits into a new module, asserted by object identity, and its E-01 plus deferral forbid changing ANY audit verdict because its value is a provably behavior-preserving extraction. This plan changes verdicts. Executing this one FIRST would invalidate `6ltz1y`'s characterization baseline and force it to re-characterize; executing `6ltz1y` first costs this plan only a re-location, which E-01 already handles. So the technically better order is `6ltz1y` then this. `Item-Dependencies` is nevertheless left `none` on purpose: `6ltz1y` is `to-review`, not `approved`, and a hard `executed:` edge to an unapproved plan would sit `dependency-blocked` indefinitely rather than expressing a preference. If the maintainer approves `6ltz1y`, adding the edge with `aw ipd dependencies set` is the right follow-up. `r2i1b1` (`reviewed`) has the same shape at lower stakes and E-05 handles either order.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: state `6ltz1y`'s status at execution time and which module you implemented in, with the path. Paste the characterization of all three current boolean verdicts with the input shape that produces each. If `6ltz1y` was still pending, paste the report you made to the maintainer about the intent conflict (it forbids changing any verdict; this plan changes verdicts). If it had landed, state what `aw doctor` does with the verdicts and how the classification serves it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new reachability check. Show it matches on the commit SUBJECT (not a body grep) and does not take only the first match, and name the artifact that makes this matter (`--grep` matches the body; manual merge commits quote the hook's demand). Paste the new shared subject constant and every reference to it, including the producer and the hook matcher. Paste evidence for EACH failure mode resolving to `unknown`: not a git repository, git absent, nonzero exit. State the per-row-cost decision and why.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the classification code showing five values and showing `resolved` requires BOTH forward direction AND E-02's evidence. QUOTE the code path proving direction alone yields `unknown`. Show `unknown` and `unchanged` are distinct values with distinct meanings. State the `interrupted` row's disposition and `vdabn5`'s status.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the rendered table for a fixture containing one row of EACH class, showing `regressed`/`missing` in the red styling, `resolved` non-alarming, and `unknown` visible with a per-row reason. Paste both `unknown` reasons (no reachable finalize commit; git unavailable). Confirm by inspection there is no code path that hides an `unknown` row.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste proof that all call sites consult ONE definition of "is this row an issue" (object identity or grep over the five former sites). State `r2i1b1`'s status and, if it had not landed, show that its E-03 extraction is still possible (nothing renamed or relocated).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the ACTUAL passing output of all six cases. QUOTE the forward-WITHOUT-evidence assertion separately and state in one sentence why classifying it `resolved` would reintroduce the abandoned design. Paste the four measured rows reproduced as a fixture and shown non-red, and the `eulhzt`-class row shown STILL RED. Confirm no test reads `.aw/records/runs/` and cite the hazard note the tests honor.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste negative proof that no run record was written or modified and that `git status --porcelain .aw/records/plans/` is clean. Paste `git diff --stat` limited to declared paths. Paste evidence the rest of `aw runs` output is unchanged apart from this table. THEN paste the BARE `python3 -m pytest` summaries before and after with the failure-set delta as a set and the counts you actually observed. Paste exit codes UNPIPED.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING QUESTION, but OQ-03 is a SEQUENCING decision a maintainer should make before execution: `6ltz1y` moves the code this plan edits and forbids verdict changes, so running this first imposes a re-characterization cost on that plan. E-01 handles either order and reports the conflict rather than absorbing it.

IT CARRIES NO `Blocks-Release`, deliberately: backlog `1f9m2j` carries none (verified: no `Blocks-Release`, `Gate-Kind` or `Gate-Ref`), so none is inherited. This is a false-positive reduction on a diagnostic table.

THE ONE WAY TO GET THIS WRONG IS TO CLASSIFY ON DIRECTION ALONE. A previous design was abandoned for exactly that, on a recorded maintainer ruling, because a legitimate finalize and a hand-edited `- Status: executed` plus `git mv` are byte-identical to this audit. `resolved` requires READ evidence; everything unprovable is a VISIBLE `unknown`. A reviewer should check E-03 and V-06 against that standard first.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `git add .`, never push. MUTATE NO RUN RECORD and no plan: the record freezes what was true and is the evidence base for resume, reconciliation and cost accounting. FIXTURES ONLY, honoring the hazard note at `tests/test_run_viewer.py:22-27`, because `.aw/records/runs/` is gitignored and absent from a fresh worktree. Re-locate every symbol by NAME: this file's line numbers already drifted ~158 lines from the item's citations. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the forward-without-evidence case asserted as `unknown`, the four measured rows going quiet, and the real find staying red.
