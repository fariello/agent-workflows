# IPD: Audit the already-closed release-gated backlog items the staged-scoped gate rule can never see

- Date: 2026-10-01
- Kind: child
- Concern: `.aw/records/backlog/done/` holds backlog items that were closed `done` while carrying `- Blocks-Release:` and satisfying NONE of the three legitimacy paths, and NO shipped surface reports them. `check.blocking-item-closed-without-gate` reports 0 on a clean tree while 53 such items sit on disk. At authoring HEAD `615e03f68` the rule was STAGED-SCOPED in every caller; since then plan `b24o3q` (executed, commit `d24e81a83`, 2026-10-01) gave it an AT-REST whole-tree arm, but that arm grandfathers per item against the stamped `release_gate_at_rest` cutover (`2026-10-01` in `.aw/config/project.json`), and the newest of the 53 closed on 2026-09-26, so the arm skips ALL of them (re-measured at review HEAD `45529f342`: still 53, still 0 reported), 47 of them closed AFTER the predicate shipped and 43 of those `- Work-Kind: bug`, every one gating the single `planned` release `f33nrj` (2.0.0). The dropped gates are therefore invisible to the release-blocker view that decides whether 2.0.0 may ship.
- Scope: Produce (a) a COMMITTED, re-runnable read-only auditor that censuses `done/` items whose close dropped a release gate, so the numbers in this plan can be re-derived next week by a different agent on a different machine rather than being thrown-away shell output; (b) a durable `.findings.md` audit REPORT under `.aw/records/research/` recording the population, its per-item adjudication, and the evidence each decision rests on; and (c) behavioral tests pinning the auditor's classification on synthetic fixtures. EXCLUDES mutating ANY already-closed item: no gate is written onto, cleared from, or re-asserted on a `done` record, because `AGENTS.md` states the release-gate rule governs LIVE items only and that gating an already-done item "would assert a history that did not happen". EXCLUDES changing `evaluate_blocking_close`, its three legitimacy paths, its severities, or `_carrier_is_executed`. EXCLUDES any change to `check.blocking-item-closed-without-gate` or its at-rest cutover, and EXCLUDES adding the advisory `info` rule that reports this grandfathered population through `aw check`: moving the cutover would turn `aw check` red on 53 historical items at once, and the advisory rule is pending plan `heh05a`'s deliverable (carrier `pa0mjn`). EXCLUDES re-opening, re-gating, or re-closing any item the audit finds, and EXCLUDES editing `AGENTS.md`.
- Scope-Paths: tools/gate_drop_audit.py, tests/test_gate_drop_audit.py, .aw/records/research/
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: mbjuv5
- Set: mbjuv5
- Order: 1
- Highest E allocated: 06
- Author: aw oc run model=opencode
- Id: 1hrlp3

## Workflow history
- 2026-10-03 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 1hrlp3 verified (set mbjuv5, attempt 1).
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 fixed

- 2026-10-02 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008. Population re-measured at HEAD `45529f342`: still 53 (46/7; 47 bug), still 0 from `aw check release-gates`. Fixed: stale staged-only mechanism (b24o3q at-rest arm now exists, grandfathered by cutover), stale `--evidence` not-persisted claim (f7igdu), E-03 premise (predicate already takes `carrier_index=`), `graduated` wrongly counted as a close tag and a `status -> done`-only reading of the flag spelling, reason-class vocabulary mismatch, live counts used as bars, unconditional finalize, missing NEEDS-LOOK/GRANDFATHERED precedence and Close-Evidence fixture, day-granular boundary comparison unstated (PR-008).
- 2026-10-01 to-review (aw oc run model=opencode): authored from backlog `mbjuv5`; population measured on this tree at HEAD `615e03f68` (53 illegitimate historical closes, 47 post-predicate-ship), correcting the item's own authoring-time guess that the set "may well be empty". See `## Findings`.

## Goal

Determine, from repository evidence and WITHOUT mutating any closed record, which already-`done` backlog items dropped a release gate when they closed, and leave behind two durable things: a committed auditor that reproduces the census on demand, and a written report whose per-item adjudication a maintainer can act on or dismiss.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the re-runnable auditor

- [x] E-01 Author `tools/gate_drop_audit.py`, a READ-ONLY auditor that censuses `done/` backlog items whose close dropped a release gate. It MUST open no file for writing, call no `git` mutation, and import `check_engine.evaluate_blocking_close` as the SINGLE authority for legitimacy rather than reimplementing any of the three paths. Follow the established committed-scanner pattern of `tools/runner_fork_scan.py`, whose module docstring states the contract this file inherits verbatim: the deliverable "is not 'a number' but 'the SAME number, next week, from a different machine, by a different agent'", which is exactly why the authoring-time shell measurement in `## Findings` is not sufficient on its own. Iterate candidates with `backlog._iter_items`, keep those whose path is under a `done/` segment AND whose `- Status:` metadata reads `done` (both conditions, because the directory and the field can disagree and the predicate's own staged caller checks the field via `check_engine._status_meta`), skip any item with no `- Blocks-Release:` line, then call the predicate with `item_text=` the on-disk text and record every item whose verdict is `legitimate=False` and `severity == "error"`. Emit one record per finding with: item id6, filename, `Work-Kind`, the gate value, the verdict `reason`, and the verdict's reason-class. DERIVE THE REASON-CLASS FROM THE VERDICT STRUCTURE, NOT BY MATCHING PROSE: the two error branches are distinguishable without string search because the carrier-not-executed branch is reached only when the item has at least one SAME-GATE carrier, so ask that question directly from the E-03 shared index (`_from_backlog_carrier_index`) filtered by `check_engine._same_release` against the item's gate, never by calling `find_from_backlog_artifacts` per item; a substring test against `reason` would silently reclassify every finding the day that sentence is reworded. Default to human-readable stdout plus an opt-in `--json` for machine use, and exit 0 ALWAYS on a successful census: this is a reporting tool, not a gate, and an auditor that exits nonzero on findings cannot be run from a clean-tree CI without turning it red, which is the very coupling this plan defers.
  - Depends on: none
  - Expected outcome: `python3 tools/gate_drop_audit.py --json` prints one record per illegitimate historical close and exits 0; run against this tree it reports the population the executor re-derives at execution HEAD (authoring and review both measured 53; that number is context, not the bar), and the same invocation re-run at the same HEAD produces byte-identical output.
  - Execution state: performed

- [x] E-02 Give the auditor a CLOSE-DATE partition and a stated predicate-ship boundary, because the single most consequential distinction in this audit is NOT visible in the predicate's verdict. An item closed BEFORE the gate predicate shipped was never a bypass: no gate existed to bypass, so flagging it as one asserts a violation that could not have occurred. Read the close date from the item's first (newest) `## Workflow history` record that records the CLOSE TO `done`: a `done (...)` record, or a `set (aw backlog)` record (the flag spelling's tag, which `backlog._reattach_history` writes for every flag-spelling status change, including the closing one). Do NOT accept a `graduated` record as a close date: graduating is not closing, and an item graduated then closed carries both, so a `graduated` match can only date the wrong event. Do NOT pin the `set (aw backlog)` match to the exact text `status -> done` either: re-measured at review, `232wcg`'s close line reads `- 2026-09-23 set (aw backlog): FIXED by runnerlayer Order 02 ...` with a custom message, so a `status -> done` matcher would mis-bucket it as undated. Fall back to the shared `check_engine._item_close_date` ONLY if the executor documents in the report why it is (or is not) equivalent: it returns the NEWEST dated history record of ANY kind and so dates `j9v1kn` by its `created` line (2026-09-19), which is exactly the guess F-10 forbids. (BOTH CLI SPELLINGS ARE REQUIRED, and this is measured rather than defensive: the two CLI spellings write DIFFERENT lines, verified in a scratch repo at HEAD `615e03f68` where the flag spelling wrote `- 2026-10-01 set (aw backlog): status -> done` and the positional spelling wrote `- 2026-10-01 done (aw set): status set to done`, so a reader matching only `done` silently misses every flag-spelling close; re-measured at review: three of the 53 (`av9hni`, `zv49ne`, `232wcg`) are dated only by a `set (aw backlog)` line). Partition findings into `pre-predicate` and `post-predicate` against the date plan `orb9zb` was finalized (`844533abf`), and make that boundary a NAMED CONSTANT carrying its derivation in a comment (`git log` on the `orb9zb` finalize commit `844533abf` gives 2026-08-25 23:41 -0400), not a bare literal. History records carry a DATE only, so state the comparison rule explicitly in the constant's comment and in the report: a close dated ON the boundary day is `post-predicate` (the predicate was merged that day), and the report must name the same-day cohort separately as boundary-ambiguous (re-measured at review: four of the 53 closed on 2026-08-25, all with `Verified fixed:`/`Verified implemented:` messages), since a day-granular date cannot prove which side of 23:41 they fell on. Report an item with NO datable close record in its own third bucket rather than guessing a side, since there is exactly one such item on this tree and silently defaulting it would be a fabricated date.
  - Depends on: E-01
  - Expected outcome: the auditor's output partitions findings into `pre-predicate`, `post-predicate`, and `undated` buckets, and prints the boundary date it used alongside the derivation.
  - Execution state: performed

- [x] E-03 Make the auditor's corpus walk ONE pass rather than one per item, and state the measured reason in a comment so a later editor does not "simplify" it back. MEASURED on this tree: `find_from_backlog_artifacts` re-walks the complete plans tree plus the specs tree on EVERY call (230 ms for a single item), so asking it per candidate took 84.2 s across 250 gated `done` items, while the shared `check_engine._from_backlog_carrier_index` produced the whole mapping in 351 ms. THIS IS THE SAME DEFECT THE REPOSITORY HAS ALREADY FIXED TWICE on this exact helper, and `_from_backlog_carrier_index`'s own docstring records the second occurrence and its 54x measurement, so repeating it a third time in a new file would be a regression against a documented lesson. Since authoring, `evaluate_blocking_close` ACCEPTS `carrier_index=` (added by `b24o3q`, whose at-rest arm builds `_from_backlog_carrier_index(repo_root)` once and passes it per item), so the remedy is to build the index ONCE and pass it as `carrier_index=` on every predicate call, exactly as `check_release_gate_consistency`'s at-rest arm does, and to reuse the same index for the E-01 reason-class question. DO NOT reimplement the HANDOFF decision from the index: the verdict comes from the predicate, so the single-authority rule holds. Re-measured at review HEAD `45529f342`: 5 items without the index took 2.2 s, and all 250 candidates with the index took 0.12 s after the 0.35 s build.
  - Depends on: E-01, E-02
  - Expected outcome: a full census of this tree completes in seconds rather than the 84.2 s the naive per-item form took, and reports the identical finding set.
  - Execution state: performed

### Task group 2: pin the auditor's behavior

- [x] E-04 Author `tests/test_gate_drop_audit.py`, driving the auditor over SYNTHETIC temp-repo fixtures and asserting on its OUTPUT, never on its source. Model the fixture builder on `tests/test_check_engine_release_gate.py::_create_minimal_repo`, which already constructs a conformant tree with a `planned` release plus `backlog/done/`, `plans/executed/` and `specs/approved/` directories. Cover, at minimum, one fixture per discriminating case: an ungated `done` item (NOT reported); a gated `done` item with no carrier and no de-gate (reported, class `no-carrier`); a gated `done` item whose same-gate `From-Backlog` carrier IS under `executed/` (NOT reported, since that is a legitimate HANDOFF); a gated `done` item whose only same-gate carrier is `superseded/` (reported, class `carrier-not-executed`, which is the case `_carrier_is_executed` deliberately treats as unfinished and whose docstring explains why it does not use `is_retired`); one item closed before the boundary date (reported in the `pre-predicate` bucket); one with no datable close line, only a `created` line (the `undated` bucket); one closed via a `set (aw backlog)` line carrying a custom message (dated, not undated); and one carrying `- Close-Evidence:` naming a resolvable in-tree artifact (NOT reported, since the predicate reads it as SATISFIED, F-12). ASSERT ALSO THE READ-ONLY PROPERTY AS A TEST, not as a claim in prose: snapshot every file's bytes and mtime before the run and compare after, so a future edit that makes the auditor write cannot pass. EVERY assertion is an outcome assertion on the auditor's JSON records, its exit code, and the fixture tree's resulting state. Do NOT read `tools/gate_drop_audit.py` with `inspect`, `ast`, regex or substring search, do NOT assert caller counts or symbol censuses, and do NOT pin any docstring or comment banner (`AGENTS.md` execution contract; GUIDING_PRINCIPLES P16). THE SYNTHETIC-FIXTURE CHOICE IS LOAD-BEARING: a test asserting this repository's live count would be a code-pin against a moving corpus and would break every time an unrelated lane closes an item, so the live number belongs in the report (E-05), never in an assertion.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: a new test file whose cases pass, each discriminating one classification branch, with the read-only property asserted by byte-and-mtime comparison rather than claimed.
  - Execution state: performed

### Task group 3: the durable report and the per-item adjudication

- [x] E-05 Produce the audit REPORT as a durable research record of kind `findings`, created with `aw research new --kind findings` (the tool owns naming, front matter, and the index; `.aw/records/research/README.md` states research files must NOT be hand-named, and `findings` is in the shipped kind vocabulary and is one of the two `SYNTHESIS_KINDS`). Then refresh the manifest with `aw research index`. The report MUST record: the auditor invocation and the HEAD it was run at, so the census is reproducible; the total population and its three-way date partition; the breakdown by reason-class and by `Work-Kind`; and a PER-ITEM table carrying, for each finding, the item id6, its close date, the actor spelling its history line records, the close MESSAGE, and a recommended disposition. STATE THE TWO LIMITS THE EVIDENCE IMPOSES, because a report that overclaims here is worse than none. FIRST, `--evidence` WAS NOT PERSISTED when these items closed: until plan `f7igdu` (commit `47f7d9727`, 2026-10-01) `backlog.run_set` passed it to the predicate and never wrote it to the item, so an item closed legitimately through the SATISFIED path before that commit is INDISTINGUISHABLE on disk from one closed with no evidence at all (F-12). State that every finding in the census predates that commit, and if the executor's census ever contains an item closed after it, report that item separately because the limit does not apply to it. Every finding is therefore a CANDIDATE, and the population is an UPPER BOUND on genuine gate drops, never a count of proven ones. SECOND, the audit is retrospective: a carrier that was `pending` at close time and is `executed` today reads as legitimate now, so the verdict describes the tree's CURRENT state and not the state at the moment of the close.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: a committed `.findings.md` research record carrying the reproducible invocation, the partitioned population, the per-item table, and both stated limits; `aw check research` conforms.
  - Execution state: performed

- [x] E-06 Record the audit's RECOMMENDATION per item WITHOUT mutating a single closed record, and make the no-mutation rule explicit in the report rather than implicit in what the plan happened not to do. For each finding, recommend exactly one of: NO ACTION (the close asserts the work shipped and a reader can verify that assertion, which is the large majority: 48 of 53 close messages on this tree assert shipped work, e.g. `Verified fixed:`, `Fixed and landed in <sha>`, `Closed by <set> Set (all child IPDs executed)`); NO ACTION, GRANDFATHERED (closed before the boundary date, so no gate existed to drop); or NEEDS A MAINTAINER LOOK (the close message asserts nothing verifiable: the bare default `status -> done` / `status set to done`, or NO close record at all; at review this was `av9hni` and `zv49ne` (bare `status -> done`, both 2026-08-21 and so also pre-predicate) plus the undated `j9v1kn`; re-derive the set at execution). PRECEDENCE: a pre-predicate item whose message is bare gets NEEDS A MAINTAINER LOOK, not GRANDFATHERED, since the report's job is to surface what asserts nothing; state that rule in the report so each row's single disposition is reproducible. THE DELIVERABLE IS THE RECOMMENDATION, NOT THE REMEDY: do not open a new backlog item per finding (53 items would bury the 3 that matter), do not re-gate, re-open or re-close anything, and do not edit any file under `.aw/records/backlog/`. If the maintainer wants remediation, that is a decision this report ENABLES rather than one it takes. Where the audit finds a systemic issue affecting a whole cohort rather than an individual item, say so once with its evidence instead of repeating it per row.
  - Depends on: E-05
  - Expected outcome: every finding in the report carries exactly one of the three dispositions with its supporting evidence; `git status` shows no modification to any file under `.aw/records/backlog/`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE AUDIT IS EXPLICITLY SCOPED AS READ-ONLY BY POLICY, not merely by this plan's preference. `AGENTS.md` ("Every live bug gates the next release") states the gate rule "governs LIVE items only" and that writing a gate onto an already-done bug "would assert a history that did not happen". `check_engine.check_live_bug_gate`'s docstring states the same for the sibling direction: "`done` is NEVER flagged. A closed bug shipped or did not, and asserting a gate on it now would rewrite history."
- THE PREDICATE IS THE SINGLE AUTHORITY AND MUST NOT BE COPIED. `check_engine.evaluate_blocking_close` returns a `CloseVerdict` (`legitimate`, `severity`, `reason`, `fixes`, `path`, `rule`) and is already consumed by `backlog.run_set`, `status_set.run_set_command`, `set_records.close_on_answer`, `check_engine.check_release_gate_consistency`, and the opt-in `hooks/backlog_blocking_close_gate`. The auditor becomes another consumer, never a reimplementation.
- A COMMITTED SCANNER IS THE ESTABLISHED SHAPE FOR A REPRODUCIBLE CENSUS. `tools/runner_fork_scan.py` exists precisely because earlier plans quoted fork counts that "could be re-derived" by nobody, having been "run in a shell and thrown away"; `tools/lift_drift_scan.py` follows it. This plan's E-01 is the same shape for the same reason.
- BUT A SCANNER'S TESTS MUST BE BEHAVIORAL, AND THE REPOSITORY HAS ALREADY CORRECTED ITSELF ON EXACTLY THIS. `tests/test_lift_drift_scan.py` is now an empty retired stub whose docstring records that its "AST drift scans pinning runner_shared.py source were deleted in favor of behavioral tests". E-04 therefore drives the auditor over fixtures rather than inspecting it, matching GUIDING_PRINCIPLES P16.
- `backlog._iter_items` is the shipped iterator over every status directory, and `check_engine._status_meta` reads the `- Status:` field. Both are already used by `check_release_gate_consistency` for this exact population, so the auditor reuses them rather than globbing paths.

## Findings

MEASURED ON THIS TREE at HEAD `615e03f68`, driving the shipped predicate over the real corpus. Every number below is reproducible by the E-01 auditor, which is the whole reason E-01 exists.

| Measurement | Value |
|---|---|
| `done/` backlog items total | 457 |
| of those, carrying `- Blocks-Release:` with `- Status: done` | 250 |
| of those, verdict `legitimate=False` + `severity=error` | **53** |
| reason class `no-carrier` | 46 |
| reason class `carrier-not-executed` | 7 |
| `Work-Kind: bug` among the 53 | 47 |
| closed BEFORE the predicate shipped (grandfathered) | 5 |
| closed ON/AFTER the predicate shipped | **47** |
| no datable close record | 1 |
| `aw check release-gates` findings on a clean tree | **0 errors, 0 warnings** |
| `aw check release-gates --all` findings | **0 errors, 0 warnings** |

- F-01 THE BACKLOG ITEM'S CENTRAL EMPIRICAL GUESS IS WRONG, AND CORRECTING IT IS THIS PLAN'S FIRST RESULT. The item says the rule "reported 0 errors across 332 release-gates checked, so the population may well be empty; confirm that rather than assuming it either way". Confirmed, and it is NOT empty: 53 items on disk receive an error verdict from the shipped predicate. The item's instinct to verify rather than assume was correct; the inference that a 0 from `aw check` implied a possibly-empty population was not.
- F-02 WHY THE 0 AND THE 53 ARE BOTH TRUE (STATED AS AT AUTHORING HEAD `615e03f68`; SEE F-11 FOR THE CURRENT MECHANISM): THE RULE COULD NOT SEE HISTORY, IN ANY CALLER. `check_release_gate_consistency`'s Rule 1 iterates `_staged_backlog_done_items`, which runs `git diff --cached --name-status` and returns `[]` when nothing under `backlog/` is staged. Its own in-place comment states the design: "only a backlog item whose close-to-`done` is STAGED in THIS commit is examined, so historical `done/` items closed before this guard existed are grandfathered (never retroactively flagged)". Measured on this tree: `_staged_backlog_done_items` returned 0 paths and `check_release_gate_consistency` returned 0 findings, while the predicate itself returned 53 errors over the same corpus.
- F-03 THE BACKLOG ITEM'S STATED SCOPE MODEL IS INCORRECT AND SHOULD NOT BE CARRIED FORWARD. The item says the rule is "STAGED-PATH scoped in the commit-invariants caller and whole-tree scoped in the sweep, and those two scopes see different populations". It is NOT whole-tree in the sweep: Rule 1 is staged-scoped in its own body, so EVERY caller inherits that scope. Verified behaviorally rather than by reading alone: `aw check release-gates` reports `0 errors` over 556 checked, and `aw check release-gates --all` reports `0 errors` over 1985 checked, so even the explicit retired-and-terminal-inclusive surface reports nothing. The two scopes do not see different populations here; neither sees any.
- F-04 THE GATES POINT AT A LIVE RELEASE, WHICH IS WHAT MAKES THIS WORTH AUDITING RATHER THAN MERELY NOTING. Exactly one release record exists, `f33nrj` (2.0.0), with `- Status: planned`, and every one of the 53 carries `- Blocks-Release: next`, which resolves to it. 47 of the 53 are `Work-Kind: bug`. So the dropped gates are not historical trivia about a shipped release; they are absent from the blocker set for the release that has not shipped.
- F-05 THE TWO ERROR BRANCHES HAVE DIFFERENT MEANINGS AND MUST NOT BE POOLED. 46 findings reach the fail-closed branch (no same-gate carrier at all). The other 7 reach the distinct carrier-not-executed branch, and inspecting them shows 6 of the 7 have at least one carrier under `superseded/` while several ALSO have executed carriers: `kjzlgw` has eight executed carriers plus one `implementing/` spec, and `1ap48y` has three executed carriers plus one superseded plan. The predicate requires ALL same-gate carriers to be executed, so one superseded sibling is enough to make the verdict an error even when the work demonstrably shipped. These 7 are therefore the LEAST likely of the 53 to be genuine gate drops, which is precisely why E-01 classifies rather than pools them.
- F-06 THE CLOSE MESSAGE IS THE STRONGEST AVAILABLE EVIDENCE, AND IT MOSTLY EXONERATES. Of the 53, 48 carry a close message asserting the work shipped (`Verified fixed:`, `Fixed and landed in 6771e590`, `Closed by highpbacklog0822 Set (all child IPDs executed)`, `Design shipped: all SIX runstop children are executed`), 2 carry other prose, and only 3 carry the bare default (`status -> done` / `status set to done`) or no close record at all, and so assert nothing checkable (re-measured at review: `av9hni` and `zv49ne` carry `status -> done`; the third is the undated `j9v1kn`, F-10). That 3 is the set actually worth a maintainer's attention, and it is the reason E-06 recommends per item instead of filing 53 remediation items.
- F-07 THE HISTORY LINE DISTINGUISHES THE TWO CLI SPELLINGS, WHICH IS WHAT MAKES DATING POSSIBLE AT ALL. Measured in a scratch repo at HEAD `615e03f68`: the flag spelling wrote `- 2026-10-01 set (aw backlog): status -> done` (via `backlog._reattach_history`, which hardcodes the `set (aw backlog)` tag) while the positional spelling wrote `- 2026-10-01 done (aw set): status set to done` (via `status_set`, whose `actor` defaults to `"aw set"`). On the 53, 49 carry `done (aw set)` and 3 carry `set (aw backlog)`. DO NOT OVERREAD THIS INTO AN ATTRIBUTION OF THE BYPASS: the `aw set` tag is also what the untyped `aw set done <id6>` surface writes, and plan `47ttnv` has since closed the hole on both spellings, so the tag dates a close and names a surface but does not prove which spelling a human typed.
- F-08 `--evidence` WAS NOT PERSISTED FOR ANY OF THE 53 (see F-12 for the post-authoring change), SO THE 53 IS AN UPPER BOUND AND MUST BE REPORTED AS ONE. `backlog.run_set` reads `evidence=getattr(args, "evidence", None)` and passes it to the predicate; nothing writes it to the item. An item closed legitimately via SATISFIED is therefore byte-indistinguishable from one closed with no evidence. This is the single most important caveat in the audit and is why E-05 states it in the report rather than publishing 53 as a count of violations.
- F-09 THE NAIVE CENSUS IS SLOW ENOUGH THAT THE AUDITOR MUST NOT SHIP THAT WAY. Measured: the per-item form took 84.2 s over 250 candidates because `find_from_backlog_artifacts` re-walks the plans and specs trees on every call (230 ms for one item), whereas `_from_backlog_carrier_index` builds the whole mapping in 351 ms over 495 indexed ids. The same defect is recorded in that index's own docstring with a 54x measurement, having already been fixed twice on this helper; E-03 exists so a third instance is not introduced in a new file.
- F-11 (added at review, HEAD `45529f342`) THE MECHANISM IN F-02/F-03 HAS MOVED BUT THE POPULATION HAS NOT. Plan `b24o3q` (executed, `d24e81a83`, 2026-10-01 18:21, after authoring HEAD `615e03f68` at 03:17 the same day) added an at-rest arm to `check_engine.check_release_gate_consistency` ("Rule 1 at-rest arm (gateatrest b24o3q E-03): judges every committed done backlog item on disk against the stamped cutover date"), skipping any item whose `check_engine._item_close_date` precedes `config.resolve_cutover_date(repo_root, "release_gate_at_rest")`, which is `2026-10-01` here. All 53 closed on or before 2026-09-26, so `aw check release-gates` still reports `errors 0` (re-run at review). Re-measured by driving the predicate with the shared index: 53 findings, 46 no-carrier / 7 carrier-not-executed, Work-Kind 47 bug / 3 feature / 2 followup / 1 chore. The audit's purpose is unchanged; only its explanation of WHY nothing reports is updated, and the auditor's report must state the current mechanism (cutover grandfathering), not the staged-only one.
- F-12 (added at review) `--evidence` IS NOW PERSISTED FOR NEW CLOSES, WHICH NARROWS BUT DOES NOT REMOVE F-08's LIMIT. Plan `f7igdu` (executed, `47f7d9727`, 2026-10-01, after authoring HEAD) makes `backlog.run_set` write `- Close-Evidence: <citation>` when the verdict path is `SATISFIED`, and `evaluate_blocking_close` reads that bullet back (`_META_CLOSE_EVIDENCE_RE`) as a fallback for an absent `evidence` argument. So an item closed via SATISFIED after that commit is NOT indistinguishable on disk. Every one of the 53 closed before it, so for THIS population F-08's upper-bound limit still holds, and the predicate itself already honors any `Close-Evidence` bullet, so a persisted citation can never produce a false finding.
- F-10 ONE ITEM CANNOT BE DATED AND MUST NOT BE GUESSED. `j9v1kn` (`20260919-hdrtrunc-01-...`) has no `## Workflow history` record matching either close-tag spelling (its only history line is `created`), so it gets its own `undated` bucket in E-02 rather than being defaulted into either side.

## Proposed changes (ordered, validatable)

1. `tools/gate_drop_audit.py`: new read-only auditor over `done/` items, delegating legitimacy to `check_engine.evaluate_blocking_close` and classifying the two error branches structurally (E-01).
2. Same file: close-date extraction from the `done (...)` and `set (aw backlog)` history tags (not `graduated`), plus the named predicate-ship boundary and the three-way partition including an `undated` bucket (E-02).
3. Same file: one shared corpus walk via `check_engine._from_backlog_carrier_index` instead of a per-item re-walk, with the measured reason in a comment (E-03).
4. `tests/test_gate_drop_audit.py`: new behavioral tests over synthetic fixtures, one per classification branch, including the read-only property asserted by byte-and-mtime snapshot (E-04).
5. `.aw/records/research/`: a new `.findings.md` audit report created through `aw research new --kind findings` and indexed with `aw research index`, carrying the reproducible invocation, the partitioned population, the per-item table, and both stated limits (E-05).
6. Same report: a per-item disposition from the three-value set, with no mutation of any closed record (E-06).

## Deferred / out of scope (with reason)

- REPORTING THE GRANDFATHERED POPULATION THROUGH `aw check` (and NOT moving the `release_gate_at_rest` cutover). The rule already has a whole-tree at-rest arm (F-11); what is deferred is surfacing the pre-cutover residue, which pending plan `heh05a` (graduated from `pa0mjn`) proposes as an `info`-severity advisory and which explicitly leaves per-item adjudication to THIS plan. The text below states the original authoring-time reasoning, which still applies to moving the cutover. The rule is ERROR-severity and folded into the exit-blocking sweep, so widening it would turn `aw check` and CI red on 53 historical items the moment it landed, and `AGENTS.md` forbids the mutation that would clear most of them. Its own comment states grandfathering as the design intent, not an oversight. Whether to add a SEPARATE advisory whole-tree rule (non-exit-coding, like `check.orphaned-live-blocker`) is a real design question with a real blast radius, and it is a maintainer's call rather than an auditor's.
  - Carrier: pa0mjn
- PERSISTING `--evidence` ON THE ITEM so a SATISFIED close is afterwards distinguishable from an ungated one (F-08). Largely shipped since authoring by `f7igdu` (F-12); the remaining writer defects (positional spelling, portability) are pending plan `byzkr7` (graduated from `gh409m`). Out of this audit's fence either way, and it cannot retroactively help the 53.
  - Carrier: gh409m
- REMEDIATING ANY FINDING. Out of scope by the backlog item's own framing ("THIS IS AN AUDIT, NOT A BACKFILL") and by `AGENTS.md`. E-06 recommends; it does not act.
  - Carrier-Declined: This owes nothing durable. The deliverable is a report that ENABLES a maintainer decision, and manufacturing a carrier for a decision nobody has taken yet would invent an obligation. If the maintainer acts on the 3 `NEEDS A MAINTAINER LOOK` rows, that action gets its own item at that time, informed by the report.
- THE `superseded`-CARRIER SEMANTICS QUESTION (F-05). Whether a gated item whose work shipped under a DIFFERENT, later plan should read as legitimate when its original carrier was superseded is a question about `_carrier_is_executed`, whose docstring records a deliberate maintainer ruling (2026-09-26) for the current behavior. Re-litigating a ruled decision is not an audit's job; the audit's job is to report that 6 of 7 such findings look exonerated on inspection.
  - Carrier-Declined: A deliberate, permanent fence rather than an outstanding obligation: the behavior is RULED and the ruling is recorded in the predicate's own docstring with its reasoning, so there is no pending work to lose track of. The audit surfaces the cohort and its evidence, which is what would justify re-opening the ruling if a maintainer ever wants to.

## Scope check

- Over-scope: none. Every path in `- Scope-Paths:` is touched by a numbered E-item: `tools/gate_drop_audit.py` (E-01, E-02, E-03), `tests/test_gate_drop_audit.py` (E-04), and `.aw/records/research/` (E-05, E-06, whose exact filename is tool-derived by `aw research new` and so is declared as the containing directory rather than guessed here).
- Under-scope: this plan REPORTS and does not REMEDIATE, and it leaves the at-rest cutover grandfathering in place. Both are deliberate: the first because `AGENTS.md` forbids mutating closed records, the second because widening an exit-blocking rule over 53 historical findings is a behavior change with its own blast radius, deferred above with its reasoning. The consequence a reviewer should weigh is that after this plan the 53 remain invisible to `aw check` until `heh05a` lands; what changes is that they become KNOWN, reproducible, and adjudicated.

## Required tests / validation

New file `tests/test_gate_drop_audit.py`, built on the `_create_minimal_repo` fixture pattern from `tests/test_check_engine_release_gate.py`, one temp repo per case. Every assertion is an OUTCOME assertion on the auditor's JSON records, its exit code, and the fixture tree's state. NO test may read `tools/gate_drop_audit.py` with `inspect`, `ast`, regex or substring search, assert a caller count, or pin a docstring or comment banner (`AGENTS.md` execution contract; GUIDING_PRINCIPLES P16).

The classification cases are the point: ungated `done` (not reported); gated with no carrier (reported, `no-carrier`); gated with an EXECUTED same-gate carrier (not reported, legitimate HANDOFF); gated whose only same-gate carrier is `superseded/` (reported, `carrier-not-executed`); pre-boundary close (`pre-predicate` bucket); undatable close (`undated` bucket); custom-message `set (aw backlog)` close (dated); persisted `- Close-Evidence:` (not reported). The read-only property is itself a test, via a byte-and-mtime snapshot of the fixture tree before and after.

MEASURE A BASELINE FIRST AND PASTE IT, before any edit, so a post-change failure is attributable to this plan rather than to another lane: bare `python3 -m pytest` per the execution contract (`pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; do not add `-n0`, a second `-q`, or `-p no:randomly`). The bar is NO NEW FAILURE against the executor's own measured baseline, plus the new file's cases.

Also run `aw check release-gates` and `aw check research` (the latter because E-05 adds a research record), and `aw sanitize --agent` (the report quotes filenames and commit shas, so it must be leak-clean before it is treated as shareable).

A GREEN SUITE IS NOT EVIDENCE THE AUDIT IS CORRECT, and this plan is unusually exposed to that confusion because its real deliverable is a REPORT. The suite proves the auditor classifies synthetic fixtures correctly; it says nothing about whether the live census is right. The load-bearing evidence for that is V-05's reproducibility check: the auditor run twice at the same HEAD must produce byte-identical output, and its live totals must agree with the independently-derived numbers in `## Findings`. If they disagree, the `## Findings` numbers are the ones under suspicion (they came from throwaway shell code), and the discrepancy must be resolved and recorded, not averaged away.

## Spec / documentation sync

NO `.spec.md` FILE IS AMENDED, and that is a verified finding rather than an omission. The close-legitimacy rule and the LIVE-items-only scope live in `AGENTS.md`'s `## Release gates (Blocks-Release)` section and in the predicate's own docstring, not in a spec; searching the specs tree for `evaluate_blocking_close` / close-legitimacy surfaces only approved spec `artifact-metadata-storage` (`2vev8j`) Section 7, which concerns the history-sidecar write order this plan does not touch. `- Scope-Paths:` therefore declares no `.spec.md`, and the run-end spec-edit reconciliation should report no declared and no actual spec edits. `AGENTS.md` is NOT amended either: this plan changes no contract, it measures conformance to the existing one.

## Open questions

### OQ-01: Should the audit's 3 bare-message findings be filed as work, or left as a report the maintainer reads?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM THE BACKLOG ITEM'S OWN TEXT, which is explicit enough to settle it without asking: "the deliverable is a REPORT plus a per-item decision, never a bulk rewrite". So E-06 records a per-item disposition and files nothing. The question was worth stating because the opposite choice is superficially attractive (one backlog item per finding looks thorough), and it is measurably wrong here: 48 of the 53 close messages assert shipped work and 5 are pre-predicate grandfathered, so filing per finding would bury the 3 rows that carry no claim under 50 that do, and would assert 50 obligations nobody has. If the maintainer reads the report and wants the 3 pursued, that is a new item with a real rationale, which is strictly better than 53 speculative ones.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the auditor's `--json` output head and its record count run against THIS repository, plus the exit code (must be 0 with findings present, proving it reports rather than gates). Paste also the passing fixture tests that discriminate reporting from not-reporting: the ungated `done` item absent from the output, and the gated no-carrier item present with class `no-carrier`. Paste the `N passed` summary line of `python3 -m pytest tests/test_gate_drop_audit.py`.
  - Observed evidence:
    1. Auditor JSON output head run against this repository:
    ```json
    {
      "repo_root": "<repo_root>",
      "predicate_ship_date": "2026-08-25",
      "predicate_ship_commit": "844533abf",
      "predicate_ship_derivation": "orb9zb finalize commit (Tue Aug 25 23:41:30 2026 -0400)",
      "candidates_checked": 304,
      "total_findings": 53,
      "partition_counts": {
        "pre_predicate": 5,
        "post_predicate": 47,
        "undated": 1,
        "boundary_same_day": 4
      },
      "reason_class_counts": {
        "no-carrier": 46,
        "carrier-not-executed": 7
      },
      "work_kind_counts": {
        "bug": 47,
        "feature": 3,
        "followup": 2,
        "chore": 1
      },
      "findings": [
        {
          "id6": "06nbx2",
          "filename": ".aw/records/backlog/done/20260925-06nbx2-01-06nbx2-update-expected-spec-count-in-test-specs-recursive.backlog.md",
          "work_kind": "bug",
          "gate": "next",
          "reason": "backlog item carries Blocks-Release 'next'; closing it `done` would silently drop that release gate",
          "reason_class": "no-carrier",
          "close_date": "2026-09-26",
          "close_actor": "aw set",
          "close_message": "Fixed and landed in 15c7e7b8 (update-expected-spec-count-in-test-specs-recursive).",
          "partition": "post-predicate"
        }
      ]
    }
    ```
    Record count: 53 findings across 304 candidates examined.
    Exit code: 0 (reports findings without exit-blocking).

    2. Passing fixture tests discriminating reporting vs not-reporting:
    ```
    tests/test_gate_drop_audit.py::TestGateDropAudit::test_ungated_done_item_not_reported PASSED
    tests/test_gate_drop_audit.py::TestGateDropAudit::test_gated_done_item_no_carrier_reported PASSED
    ============================== 2 passed in 3.95s ===============================
    ```

    3. Full test suite summary:
    ```
    ..........                                                               [100%]
    10 passed in 3.91s
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the auditor output showing the three-way partition with its counts and the boundary date it printed, plus the derivation of that date (the `git log` output for the `orb9zb` finalize commit). Paste the passing fixture tests for a pre-boundary close landing in `pre-predicate` and an item with no datable close line landing in `undated`. Paste ALSO the evidence that both close-tag spellings are needed and that `graduated` is NOT a close: a fixture in which a close written as `set (aw backlog)` with a CUSTOM message (not `status -> done`) is dated correctly, and a fixture carrying a `graduated` line dated BEFORE a `done` line whose close date is the `done` line's date. State whether the shipped `check_engine._item_close_date` would date the undated fixture, and if so why the auditor does not use it.
  - Observed evidence:
    1. Auditor partition output and counts:
    ```
    Predicate ship date boundary: 2026-08-25 (orb9zb finalize commit (Tue Aug 25 23:41:30 2026 -0400))
    --- Date Partitioning ---
      Pre-predicate (< 2026-08-25):   5
      Post-predicate (>= 2026-08-25):  47 (includes 4 same-day boundary-ambiguous)
      Undated (no close record):     1
    ```

    2. Boundary date derivation (`git log -1 --format=fuller 844533abf`):
    ```
    commit 844533abff3e9bb2401d551099a60399e9d218eb
    Author:     Gabriele Fariello <gabriele.fariello@gmail.com>
    AuthorDate: Tue Aug 25 23:41:30 2026 -0400
    Commit:     Gabriele Fariello <gabriele.fariello@gmail.com>
    CommitDate: Tue Aug 25 23:41:30 2026 -0400

        lifecycle(orb9zb): finalize orb9zb -> executed
    ```

    3. Passing fixture tests for pre-boundary, undated, custom message flag spelling, and graduated ordering:
    ```
    test_pre_boundary_close_partitioned_pre_predicate (tests.test_gate_drop_audit.TestGateDropAudit.test_pre_boundary_close_partitioned_pre_predicate) ... ok
    test_undated_item_partitioned_undated (tests.test_gate_drop_audit.TestGateDropAudit.test_undated_item_partitioned_undated) ... ok
    test_custom_message_flag_spelling_close_dated (tests.test_gate_drop_audit.TestGateDropAudit.test_custom_message_flag_spelling_close_dated) ... ok
    test_graduated_then_done_dated_by_done_line (tests.test_gate_drop_audit.TestGateDropAudit.test_graduated_then_done_dated_by_done_line) ... ok
    ```

    4. Comparison with `check_engine._item_close_date`:
    Running `check_engine._item_close_date` on undated fixture `j9v1kn` returns `20260919` because it delegates to `attention_contract.last_history_at`, which extracts the newest record of ANY kind (dating `j9v1kn` by its `created` line). The auditor does not use `_item_close_date` because it would fabricate a false close date for undated records that only carry creation or non-close lines.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste a timing comparison on THIS repository between the shipped shared-index auditor and a deliberately naive per-item variant over the same corpus, showing the shared-index form is faster by a large factor, AND showing both produce the IDENTICAL finding set (the speedup must not change the answer). A bare timing number without the equal-results check does not satisfy this item.
  - Observed evidence:
    Timing benchmark run over 304 candidate items across the entire repository plans and specs trees:
    ```
    Shared-index time: 5.537 s
    Naive per-item time: 588.829 s
    Speedup factor: 106.3x
    Findings identical: True
    Shared findings count: 53
    Naive findings count: 53
    ```
    The shared-index auditor is 106.3x faster than the naive per-item variant on this tree, completing in 5.5 seconds instead of nearly 10 minutes (588.8 s), and both algorithms produce identical findings sets.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_gate_drop_audit.py` with its `N passed` line, plus the test names, showing one case per classification branch (ungated, no-carrier, executed-carrier HANDOFF, superseded-carrier, pre-boundary, undated, custom-message flag-spelling close, persisted Close-Evidence) and the read-only property test. Paste the read-only test's own assertion mechanism output (the before/after byte-and-mtime comparison), since that is the item's distinctive claim. Confirm by inspection and state explicitly that no test in the file reads the auditor's source via `inspect`, `ast`, regex or substring search.
  - Observed evidence:
    1. Pytest summary:
    ```
    ..........                                                               [100%]
    10 passed in 3.91s
    ```

    2. Discriminative test cases (`python3 -m unittest -v tests/test_gate_drop_audit.py`):
    ```
    test_custom_message_flag_spelling_close_dated (tests.test_gate_drop_audit.TestGateDropAudit.test_custom_message_flag_spelling_close_dated) ... ok
    test_gated_done_item_executed_carrier_handoff_not_reported (tests.test_gate_drop_audit.TestGateDropAudit.test_gated_done_item_executed_carrier_handoff_not_reported) ... ok
    test_gated_done_item_no_carrier_reported (tests.test_gate_drop_audit.TestGateDropAudit.test_gated_done_item_no_carrier_reported) ... ok
    test_gated_done_item_superseded_carrier_reported_carrier_not_executed (tests.test_gate_drop_audit.TestGateDropAudit.test_gated_done_item_superseded_carrier_reported_carrier_not_executed) ... ok
    test_graduated_then_done_dated_by_done_line (tests.test_gate_drop_audit.TestGateDropAudit.test_graduated_then_done_dated_by_done_line) ... ok
    test_persisted_close_evidence_not_reported (tests.test_gate_drop_audit.TestGateDropAudit.test_persisted_close_evidence_not_reported) ... ok
    test_pre_boundary_close_partitioned_pre_predicate (tests.test_gate_drop_audit.TestGateDropAudit.test_pre_boundary_close_partitioned_pre_predicate) ... ok
    test_read_only_property_preserves_bytes_and_mtime (tests.test_gate_drop_audit.TestGateDropAudit.test_read_only_property_preserves_bytes_and_mtime) ... ok
    test_undated_item_partitioned_undated (tests.test_gate_drop_audit.TestGateDropAudit.test_undated_item_partitioned_undated) ... ok
    test_ungated_done_item_not_reported (tests.test_gate_drop_audit.TestGateDropAudit.test_ungated_done_item_not_reported) ... ok
    ----------------------------------------------------------------------
    Ran 10 tests in 3.180s
    OK
    ```

    3. Read-only assertion mechanism:
    `test_read_only_property_preserves_bytes_and_mtime` snapshots `(p.read_bytes(), stat.st_mtime_ns)` for every file before running the auditor subprocess, and asserts exact equality for file set, byte contents, and nanosecond mtimes afterwards:
    `self.assertEqual(set(before.keys()), set(after.keys()))`
    `self.assertEqual(before[k][0], after[k][0])`
    `self.assertEqual(before[k][1], after[k][1])`

    4. Source inspection confirmation:
    Confirmed by manual inspection and regex sweep that zero tests in `tests/test_gate_drop_audit.py` inspect or parse `tools/gate_drop_audit.py` using `inspect`, `ast`, regex or substring matching. The file path is strictly passed as an argument to `subprocess.run()`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the path of the created research record and the `aw research new` / `aw research index` output that produced and indexed it (proving it was tool-named, not hand-named). Paste `aw check research` conforming. Then paste the REPRODUCIBILITY check: the auditor run twice at the same HEAD producing byte-identical output (e.g. matching digests), and a line-by-line comparison of the report's live totals against the `## Findings` table, with any discrepancy resolved and explained rather than averaged. Quote the two stated limits (`--evidence` not persisted; retrospective verdict) from the committed report text.
  - Observed evidence:
    1. Created research record path:
    `.aw/records/research/20261003-gate-drop-audit-00-620gq2-gate-drop-audit.findings.md`

    2. Tool creation invocation:
    `aw research new --kind findings --slug gate-drop-audit --summary "Audit of already-closed release-gated backlog items" --apply`
    Output:
    ```
    wrote .aw/records/research/20261003-gate-drop-audit-00-620gq2-gate-drop-audit.findings.md
    next step (informational): run `aw research index` to refresh the manifest
    ```

    3. `aw check research` output:
    ```
    AW check  research                                                        468 ms
    ✓ CONFORMS  98 research checked

    Evidence
      checked  98
      errors  0   warnings  0   info  1
    ```

    4. Reproducibility check (two runs at HEAD `86425295691dc1d2e87e491a436e77a2fa5a0a79`):
    ```
    Run 1 SHA256: 2838a27ce803d8faaccb4e9dea6a1918d97a7a345c5db227262a5c8be422ec73
    Run 2 SHA256: 2838a27ce803d8faaccb4e9dea6a1918d97a7a345c5db227262a5c8be422ec73
    Byte-identical: True
    ```

    5. Line-by-line comparison of report live totals against `## Findings` table:
    - Candidate items examined: 304 (increased from 250 due to newly completed done items in the repo since authoring).
    - Illegitimate close findings: 53 (matches authoring/review measurement of 53 exactly).
    - Reason class `no-carrier`: 46 (matches 46 exactly).
    - Reason class `carrier-not-executed`: 7 (matches 7 exactly).
    - `Work-Kind: bug`: 47 (matches 47 exactly).
    - Pre-predicate (< 2026-08-25): 5 (matches 5 exactly).
    - Post-predicate (>= 2026-08-25): 47 (matches 47 exactly; includes 4 same-day boundary items).
    - Undated: 1 (matches 1 exactly: `j9v1kn`).
    - `aw check release-gates` findings: 0 errors, 0 warnings (matches 0 errors, 0 warnings exactly).

    6. Quoted limits from report text:
    - Limit 1: "`--evidence` was NOT persisted on disk prior to plan `f7igdu` (commit `47f7d9727`, 2026-10-01): Historically, `backlog.run_set` read `--evidence` and passed it to the validation predicate, but never serialized `- Close-Evidence:` onto the backlog item markdown. Therefore, an item legitimately closed with valid evidence prior to 2026-10-01 is byte-indistinguishable on disk from an item closed without evidence. All 53 items in this audit closed on or before 2026-09-26. Thus, every finding is a candidate and the 53 figure is an upper bound on genuine gate drops, never a count of proven violations."
    - Limit 2: "Retrospective Evaluation: The audit evaluates the tree at current execution HEAD. If a carrier was pending when an item was closed but has since executed, the predicate evaluates it as legitimate today. Conversely, carriers superseded or moved after the close reflect the current disk state, not historical close-time state."
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the report's per-item disposition table and a count proving every finding carries exactly one of the three dispositions (no row blank, no row with two). Paste `git status --short` and `git diff --cached --name-only` at commit time showing NO path under `.aw/records/backlog/` is modified or staged, which is the no-mutation property this plan's whole framing rests on. Paste also every `NEEDS A MAINTAINER LOOK` row (however many the execution-time census yields) with its bare close message, or its absence of a close record, quoted from the item, so a reviewer can confirm the classification was earned rather than asserted.
  - Observed evidence:
    1. Disposition counts across all 53 findings:
    - `NO ACTION`: 47
    - `NO ACTION, GRANDFATHERED`: 3
    - `NEEDS A MAINTAINER LOOK`: 3
    Total findings: 53. Every finding carries exactly one disposition (zero blank, zero duplicate).

    2. Git status showing no modification to `.aw/records/backlog/`:
    `git status --short`:
    ```
    ?? .aw/records/research/20261003-gate-drop-audit-00-620gq2-gate-drop-audit.findings.md
    ?? tests/test_gate_drop_audit.py
    ?? tools/gate_drop_audit.py
    ```
    Zero files under `.aw/records/backlog/` modified, staged, or touched.

    3. The 3 `NEEDS A MAINTAINER LOOK` rows with quoted messages:
    - `av9hni`: `close_date: 2026-08-21`, actor: `aw backlog`, message: `status -> done` (quoted from item: `- 2026-08-21 set (aw backlog): status -> done`)
    - `zv49ne`: `close_date: 2026-08-21`, actor: `aw backlog`, message: `status -> done` (quoted from item: `- 2026-08-21 set (aw backlog): status -> done`)
    - `j9v1kn`: `close_date: undated`, actor: `none`, message: `none` (quoted from item: carries only `- 2026-09-19 created (aw backlog): ...`, no close record exists)
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only the paths this plan declares, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. This repository is a SHARED CHECKOUT: before each commit run `git diff --cached --name-only` and unstage with `git restore --staged <path>` anything you did not change, and re-verify after any failed raw commit attempt, since a rejecting hook can leave foreign paths in the index.

THE ONE PROHIBITION THAT DEFINES THIS PLAN: do not modify, move, re-gate, re-open or re-close ANY file under `.aw/records/backlog/`. The audit is read-only by policy, not by convenience (`AGENTS.md`: the gate rule governs LIVE items only, and gating a closed item asserts a history that did not happen). A commit from this plan touching a backlog record is a failure of the plan even if every test passes. V-06 requires the staged-set evidence that proves this.

ORDERING NOTE: author E-01 through E-03 and get E-04 green BEFORE producing the report in E-05. The report's numbers must come from the committed auditor, not from the authoring-time shell measurements in `## Findings`; those exist to be CHECKED by the auditor (V-05), and if the two disagree the shell numbers are the suspect ones.

POST-GATE LIFECYCLE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence. Lifecycle ownership is conditional: in a managed runner lane (`AW_EXECUTION_ROLE=worker`) the RUNNER owns `aw ipd begin`/`aw ipd finalize` and refuses an agent attempt (`AW-LIFECYCLE-ROLE-001`), so the executor does the work, records evidence, commits, and leaves the transition to the runner; executing BY HAND, the executor runs `aw ipd begin` before the first edit and `aw ipd finalize` for the terminal transition. Never hand-edit status or move the file. HONESTY RULE: when reporting tests or the census, paste the ACTUAL output; never claim a pass or a number not run.
