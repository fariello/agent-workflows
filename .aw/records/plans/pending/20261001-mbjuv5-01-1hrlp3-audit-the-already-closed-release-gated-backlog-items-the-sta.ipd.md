# IPD: Audit the already-closed release-gated backlog items the staged-scoped gate rule can never see

- Date: 2026-10-01
- Kind: child
- Concern: `.aw/records/backlog/done/` holds backlog items that were closed `done` while carrying `- Blocks-Release:` and satisfying NONE of the three legitimacy paths, and NO shipped surface reports them. `check.blocking-item-closed-without-gate` is STAGED-SCOPED in every caller, so it reports 0 on a clean tree while 53 such items sit on disk, 47 of them closed AFTER the predicate shipped and 43 of those `- Work-Kind: bug`, every one gating the single `planned` release `f33nrj` (2.0.0). The dropped gates are therefore invisible to the release-blocker view that decides whether 2.0.0 may ship.
- Scope: Produce (a) a COMMITTED, re-runnable read-only auditor that censuses `done/` items whose close dropped a release gate, so the numbers in this plan can be re-derived next week by a different agent on a different machine rather than being thrown-away shell output; (b) a durable `.findings.md` audit REPORT under `.aw/records/research/` recording the population, its per-item adjudication, and the evidence each decision rests on; and (c) behavioral tests pinning the auditor's classification on synthetic fixtures. EXCLUDES mutating ANY already-closed item: no gate is written onto, cleared from, or re-asserted on a `done` record, because `AGENTS.md` states the release-gate rule governs LIVE items only and that gating an already-done item "would assert a history that did not happen". EXCLUDES changing `evaluate_blocking_close`, its three legitimacy paths, its severities, or `_carrier_is_executed`. EXCLUDES widening `check.blocking-item-closed-without-gate` from staged scope to whole-tree scope, which is a SEPARATE behavior change with its own exit-code blast radius (it would turn `aw check` red on 53 historical items at once) and is deferred with a carrier. EXCLUDES re-opening, re-gating, or re-closing any item the audit finds, and EXCLUDES editing `AGENTS.md`.
- Scope-Paths: tools/gate_drop_audit.py, tests/test_gate_drop_audit.py, .aw/records/research/
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: mbjuv5
- Set: mbjuv5
- Order: 1
- Highest E allocated: 06
- Author: aw oc run model=opencode
- Id: 1hrlp3

## Workflow history

- 2026-10-01 to-review (aw oc run model=opencode): authored from backlog `mbjuv5`; population measured on this tree at HEAD `615e03f68` (53 illegitimate historical closes, 47 post-predicate-ship), correcting the item's own authoring-time guess that the set "may well be empty". See `## Findings`.

## Goal

Determine, from repository evidence and WITHOUT mutating any closed record, which already-`done` backlog items dropped a release gate when they closed, and leave behind two durable things: a committed auditor that reproduces the census on demand, and a written report whose per-item adjudication a maintainer can act on or dismiss.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the re-runnable auditor

- [ ] E-01 Author `tools/gate_drop_audit.py`, a READ-ONLY auditor that censuses `done/` backlog items whose close dropped a release gate. It MUST open no file for writing, call no `git` mutation, and import `check_engine.evaluate_blocking_close` as the SINGLE authority for legitimacy rather than reimplementing any of the three paths. Follow the established committed-scanner pattern of `tools/runner_fork_scan.py`, whose module docstring states the contract this file inherits verbatim: the deliverable "is not 'a number' but 'the SAME number, next week, from a different machine, by a different agent'", which is exactly why the authoring-time shell measurement in `## Findings` is not sufficient on its own. Iterate candidates with `backlog._iter_items`, keep those whose path is under a `done/` segment AND whose `- Status:` metadata reads `done` (both conditions, because the directory and the field can disagree and the predicate's own staged caller checks the field via `check_engine._status_meta`), skip any item with no `- Blocks-Release:` line, then call the predicate with `item_text=` the on-disk text and record every item whose verdict is `legitimate=False` and `severity == "error"`. Emit one record per finding with: item id6, filename, `Work-Kind`, the gate value, the verdict `reason`, and the verdict's reason-class. DERIVE THE REASON-CLASS FROM THE VERDICT STRUCTURE, NOT BY MATCHING PROSE: the two error branches are distinguishable without string search because the carrier-not-executed branch is reached only when `find_from_backlog_artifacts` yields at least one same-gate carrier, so ask that question directly; a substring test against `reason` would silently reclassify every finding the day that sentence is reworded. Default to human-readable stdout plus an opt-in `--json` for machine use, and exit 0 ALWAYS on a successful census: this is a reporting tool, not a gate, and an auditor that exits nonzero on findings cannot be run from a clean-tree CI without turning it red, which is the very coupling this plan defers.
  - Depends on: none
  - Expected outcome: `python3 tools/gate_drop_audit.py --json` prints one record per illegitimate historical close and exits 0; run against this tree it reports a nonzero population, and the same invocation re-run produces byte-identical output.
  - Execution state: pending

- [ ] E-02 Give the auditor a CLOSE-DATE partition and a stated predicate-ship boundary, because the single most consequential distinction in this audit is NOT visible in the predicate's verdict. An item closed BEFORE the gate predicate shipped was never a bypass: no gate existed to bypass, so flagging it as one asserts a violation that could not have occurred. Read the close date from the item's first `## Workflow history` record whose status tag is `done`, `graduated`, or `set` (ALL THREE SPELLINGS ARE REQUIRED, and this is measured rather than defensive: the two CLI spellings write DIFFERENT lines, verified in a scratch repo at HEAD `615e03f68` where the flag spelling wrote `- 2026-10-01 set (aw backlog): status -> done` and the positional spelling wrote `- 2026-10-01 done (aw set): status set to done`, so a reader matching only `done` silently misses every flag-spelling close). Partition findings into `pre-predicate` and `post-predicate` against the date plan `orb9zb` was finalized, and make that boundary a NAMED CONSTANT carrying its derivation in a comment (`git log` on the `orb9zb` finalize commit gives 2026-08-25), not a bare literal. Report an item with NO datable close record in its own third bucket rather than guessing a side, since there is exactly one such item on this tree and silently defaulting it would be a fabricated date.
  - Depends on: E-01
  - Expected outcome: the auditor's output partitions findings into `pre-predicate`, `post-predicate`, and `undated` buckets, and prints the boundary date it used alongside the derivation.
  - Execution state: pending

- [ ] E-03 Make the auditor's corpus walk ONE pass rather than one per item, and state the measured reason in a comment so a later editor does not "simplify" it back. MEASURED on this tree: `find_from_backlog_artifacts` re-walks the complete plans tree plus the specs tree on EVERY call (230 ms for a single item), so asking it per candidate took 84.2 s across 250 gated `done` items, while the shared `check_engine._from_backlog_carrier_index` produced the whole mapping in 351 ms. THIS IS THE SAME DEFECT THE REPOSITORY HAS ALREADY FIXED TWICE on this exact helper, and `_from_backlog_carrier_index`'s own docstring records the second occurrence and its 54x measurement, so repeating it a third time in a new file would be a regression against a documented lesson. Use the shared index for the carrier question. DO NOT, however, reimplement the HANDOFF decision from that index: keep calling `evaluate_blocking_close` for the verdict itself and use the index only to classify and to answer "does a same-gate carrier exist", so the single-authority rule holds and the speedup is confined to the walk.
  - Depends on: E-01, E-02
  - Expected outcome: a full census of this tree completes in seconds rather than the 84.2 s the naive per-item form took, and reports the identical finding set.
  - Execution state: pending

### Task group 2: pin the auditor's behavior

- [ ] E-04 Author `tests/test_gate_drop_audit.py`, driving the auditor over SYNTHETIC temp-repo fixtures and asserting on its OUTPUT, never on its source. Model the fixture builder on `tests/test_check_engine_release_gate.py::_create_minimal_repo`, which already constructs a conformant tree with a `planned` release plus `backlog/done/`, `plans/executed/` and `specs/approved/` directories. Cover, at minimum, one fixture per discriminating case: an ungated `done` item (NOT reported); a gated `done` item with no carrier and no de-gate (reported, class `no-carrier`); a gated `done` item whose same-gate `From-Backlog` carrier IS under `executed/` (NOT reported, since that is a legitimate HANDOFF); a gated `done` item whose only same-gate carrier is `superseded/` (reported, class `carrier-not-executed`, which is the case `_carrier_is_executed` deliberately treats as unfinished and whose docstring explains why it does not use `is_retired`); one item closed before the boundary date (reported in the `pre-predicate` bucket); and one with no datable close line (the `undated` bucket). ASSERT ALSO THE READ-ONLY PROPERTY AS A TEST, not as a claim in prose: snapshot every file's bytes and mtime before the run and compare after, so a future edit that makes the auditor write cannot pass. EVERY assertion is an outcome assertion on the auditor's JSON records, its exit code, and the fixture tree's resulting state. Do NOT read `tools/gate_drop_audit.py` with `inspect`, `ast`, regex or substring search, do NOT assert caller counts or symbol censuses, and do NOT pin any docstring or comment banner (`AGENTS.md` execution contract; GUIDING_PRINCIPLES P16). THE SYNTHETIC-FIXTURE CHOICE IS LOAD-BEARING: a test asserting this repository's live count would be a code-pin against a moving corpus and would break every time an unrelated lane closes an item, so the live number belongs in the report (E-05), never in an assertion.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: a new test file whose cases pass, each discriminating one classification branch, with the read-only property asserted by byte-and-mtime comparison rather than claimed.
  - Execution state: pending

### Task group 3: the durable report and the per-item adjudication

- [ ] E-05 Produce the audit REPORT as a durable research record of kind `findings`, created with `aw research new --kind findings` (the tool owns naming, front matter, and the index; `.aw/records/research/README.md` states research files must NOT be hand-named, and `findings` is in the shipped kind vocabulary and is one of the two `SYNTHESIS_KINDS`). Then refresh the manifest with `aw research index`. The report MUST record: the auditor invocation and the HEAD it was run at, so the census is reproducible; the total population and its three-way date partition; the breakdown by reason-class and by `Work-Kind`; and a PER-ITEM table carrying, for each finding, the item id6, its close date, the actor spelling its history line records, the close MESSAGE, and a recommended disposition. STATE THE TWO LIMITS THE EVIDENCE IMPOSES, because a report that overclaims here is worse than none. FIRST, `--evidence` IS NOT PERSISTED: `backlog.run_set` passes it to the predicate and never writes it to the item, so an item closed legitimately through the SATISFIED path is INDISTINGUISHABLE on disk from one closed with no evidence at all. Every finding is therefore a CANDIDATE, and the population is an UPPER BOUND on genuine gate drops, never a count of proven ones. SECOND, the audit is retrospective: a carrier that was `pending` at close time and is `executed` today reads as legitimate now, so the verdict describes the tree's CURRENT state and not the state at the moment of the close.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: a committed `.findings.md` research record carrying the reproducible invocation, the partitioned population, the per-item table, and both stated limits; `aw check research` conforms.
  - Execution state: pending

- [ ] E-06 Record the audit's RECOMMENDATION per item WITHOUT mutating a single closed record, and make the no-mutation rule explicit in the report rather than implicit in what the plan happened not to do. For each finding, recommend exactly one of: NO ACTION (the close asserts the work shipped and a reader can verify that assertion, which is the large majority: 48 of 53 close messages on this tree assert shipped work, e.g. `Verified fixed:`, `Fixed and landed in <sha>`, `Closed by <set> Set (all child IPDs executed)`); NO ACTION, GRANDFATHERED (closed before the boundary date, so no gate existed to drop); or NEEDS A MAINTAINER LOOK (the close message asserts nothing verifiable, which is the small set worth a human's time: 3 items whose message is the bare default `status -> done` / `status set to done`, carrying no claim at all). THE DELIVERABLE IS THE RECOMMENDATION, NOT THE REMEDY: do not open a new backlog item per finding (53 items would bury the 3 that matter), do not re-gate, re-open or re-close anything, and do not edit any file under `.aw/records/backlog/`. If the maintainer wants remediation, that is a decision this report ENABLES rather than one it takes. Where the audit finds a systemic issue affecting a whole cohort rather than an individual item, say so once with its evidence instead of repeating it per row.
  - Depends on: E-05
  - Expected outcome: every finding in the report carries exactly one of the three dispositions with its supporting evidence; `git status` shows no modification to any file under `.aw/records/backlog/`.
  - Execution state: pending

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
| reason class `no-carrier-no-evidence` | 46 |
| reason class `carrier-not-executed` | 7 |
| `Work-Kind: bug` among the 53 | 47 |
| closed BEFORE the predicate shipped (grandfathered) | 5 |
| closed ON/AFTER the predicate shipped | **47** |
| no datable close record | 1 |
| `aw check release-gates` findings on a clean tree | **0 errors, 0 warnings** |
| `aw check release-gates --all` findings | **0 errors, 0 warnings** |

- F-01 THE BACKLOG ITEM'S CENTRAL EMPIRICAL GUESS IS WRONG, AND CORRECTING IT IS THIS PLAN'S FIRST RESULT. The item says the rule "reported 0 errors across 332 release-gates checked, so the population may well be empty; confirm that rather than assuming it either way". Confirmed, and it is NOT empty: 53 items on disk receive an error verdict from the shipped predicate. The item's instinct to verify rather than assume was correct; the inference that a 0 from `aw check` implied a possibly-empty population was not.
- F-02 WHY THE 0 AND THE 53 ARE BOTH TRUE: THE RULE CANNOT SEE HISTORY, IN ANY CALLER. `check_release_gate_consistency`'s Rule 1 iterates `_staged_backlog_done_items`, which runs `git diff --cached --name-status` and returns `[]` when nothing under `backlog/` is staged. Its own in-place comment states the design: "only a backlog item whose close-to-`done` is STAGED in THIS commit is examined, so historical `done/` items closed before this guard existed are grandfathered (never retroactively flagged)". Measured on this tree: `_staged_backlog_done_items` returned 0 paths and `check_release_gate_consistency` returned 0 findings, while the predicate itself returned 53 errors over the same corpus.
- F-03 THE BACKLOG ITEM'S STATED SCOPE MODEL IS INCORRECT AND SHOULD NOT BE CARRIED FORWARD. The item says the rule is "STAGED-PATH scoped in the commit-invariants caller and whole-tree scoped in the sweep, and those two scopes see different populations". It is NOT whole-tree in the sweep: Rule 1 is staged-scoped in its own body, so EVERY caller inherits that scope. Verified behaviorally rather than by reading alone: `aw check release-gates` reports `0 errors` over 556 checked, and `aw check release-gates --all` reports `0 errors` over 1985 checked, so even the explicit retired-and-terminal-inclusive surface reports nothing. The two scopes do not see different populations here; neither sees any.
- F-04 THE GATES POINT AT A LIVE RELEASE, WHICH IS WHAT MAKES THIS WORTH AUDITING RATHER THAN MERELY NOTING. Exactly one release record exists, `f33nrj` (2.0.0), with `- Status: planned`, and every one of the 53 carries `- Blocks-Release: next`, which resolves to it. 47 of the 53 are `Work-Kind: bug`. So the dropped gates are not historical trivia about a shipped release; they are absent from the blocker set for the release that has not shipped.
- F-05 THE TWO ERROR BRANCHES HAVE DIFFERENT MEANINGS AND MUST NOT BE POOLED. 46 findings reach the fail-closed branch (no same-gate carrier at all). The other 7 reach the distinct carrier-not-executed branch, and inspecting them shows 6 of the 7 have at least one carrier under `superseded/` while several ALSO have executed carriers: `kjzlgw` has eight executed carriers plus one `implementing/` spec, and `1ap48y` has three executed carriers plus one superseded plan. The predicate requires ALL same-gate carriers to be executed, so one superseded sibling is enough to make the verdict an error even when the work demonstrably shipped. These 7 are therefore the LEAST likely of the 53 to be genuine gate drops, which is precisely why E-01 classifies rather than pools them.
- F-06 THE CLOSE MESSAGE IS THE STRONGEST AVAILABLE EVIDENCE, AND IT MOSTLY EXONERATES. Of the 53, 48 carry a close message asserting the work shipped (`Verified fixed:`, `Fixed and landed in 6771e590`, `Closed by highpbacklog0822 Set (all child IPDs executed)`, `Design shipped: all SIX runstop children are executed`), 2 carry other prose, and only 3 carry the bare default (`status -> done` / `status set to done`) and so assert nothing checkable. That 3 is the set actually worth a maintainer's attention, and it is the reason E-06 recommends per item instead of filing 53 remediation items.
- F-07 THE HISTORY LINE DISTINGUISHES THE TWO CLI SPELLINGS, WHICH IS WHAT MAKES DATING POSSIBLE AT ALL. Measured in a scratch repo at HEAD `615e03f68`: the flag spelling wrote `- 2026-10-01 set (aw backlog): status -> done` (via `backlog._reattach_history`, which hardcodes the `set (aw backlog)` tag) while the positional spelling wrote `- 2026-10-01 done (aw set): status set to done` (via `status_set`, whose `actor` defaults to `"aw set"`). On the 53, 49 carry `done (aw set)` and 3 carry `set (aw backlog)`. DO NOT OVERREAD THIS INTO AN ATTRIBUTION OF THE BYPASS: the `aw set` tag is also what the untyped `aw set done <id6>` surface writes, and plan `47ttnv` has since closed the hole on both spellings, so the tag dates a close and names a surface but does not prove which spelling a human typed.
- F-08 `--evidence` IS NOT PERSISTED, SO THE 53 IS AN UPPER BOUND AND MUST BE REPORTED AS ONE. `backlog.run_set` reads `evidence=getattr(args, "evidence", None)` and passes it to the predicate; nothing writes it to the item. An item closed legitimately via SATISFIED is therefore byte-indistinguishable from one closed with no evidence. This is the single most important caveat in the audit and is why E-05 states it in the report rather than publishing 53 as a count of violations.
- F-09 THE NAIVE CENSUS IS SLOW ENOUGH THAT THE AUDITOR MUST NOT SHIP THAT WAY. Measured: the per-item form took 84.2 s over 250 candidates because `find_from_backlog_artifacts` re-walks the plans and specs trees on every call (230 ms for one item), whereas `_from_backlog_carrier_index` builds the whole mapping in 351 ms over 495 indexed ids. The same defect is recorded in that index's own docstring with a 54x measurement, having already been fixed twice on this helper; E-03 exists so a third instance is not introduced in a new file.
- F-10 ONE ITEM CANNOT BE DATED AND MUST NOT BE GUESSED. `j9v1kn` (`20260919-hdrtrunc-01-...`) has no `## Workflow history` record matching any of the three close-tag spellings, so it gets its own `undated` bucket in E-02 rather than being defaulted into either side.

## Proposed changes (ordered, validatable)

1. `tools/gate_drop_audit.py`: new read-only auditor over `done/` items, delegating legitimacy to `check_engine.evaluate_blocking_close` and classifying the two error branches structurally (E-01).
2. Same file: close-date extraction across all three history-tag spellings, plus the named predicate-ship boundary and the three-way partition including an `undated` bucket (E-02).
3. Same file: one shared corpus walk via `check_engine._from_backlog_carrier_index` instead of a per-item re-walk, with the measured reason in a comment (E-03).
4. `tests/test_gate_drop_audit.py`: new behavioral tests over synthetic fixtures, one per classification branch, including the read-only property asserted by byte-and-mtime snapshot (E-04).
5. `.aw/records/research/`: a new `.findings.md` audit report created through `aw research new --kind findings` and indexed with `aw research index`, carrying the reproducible invocation, the partitioned population, the per-item table, and both stated limits (E-05).
6. Same report: a per-item disposition from the three-value set, with no mutation of any closed record (E-06).

## Deferred / out of scope (with reason)

- WIDENING `check.blocking-item-closed-without-gate` TO WHOLE-TREE SCOPE. This is the obvious "fix", and it is deliberately NOT taken here. The rule is ERROR-severity and folded into the exit-blocking sweep, so widening it would turn `aw check` and CI red on 53 historical items the moment it landed, and `AGENTS.md` forbids the mutation that would clear most of them. Its own comment states grandfathering as the design intent, not an oversight. Whether to add a SEPARATE advisory whole-tree rule (non-exit-coding, like `check.orphaned-live-blocker`) is a real design question with a real blast radius, and it is a maintainer's call rather than an auditor's.
  - Carrier: pa0mjn
- PERSISTING `--evidence` ON THE ITEM so a SATISFIED close is afterwards distinguishable from an ungated one (F-08). This would make a future audit decisive instead of upper-bounded, and it is genuinely desirable, but it changes the backlog record SCHEMA and the setter's write path, which is far outside an audit's fence. Noted as the root cause of this audit's central limitation.
  - Carrier: gh409m
- REMEDIATING ANY FINDING. Out of scope by the backlog item's own framing ("THIS IS AN AUDIT, NOT A BACKFILL") and by `AGENTS.md`. E-06 recommends; it does not act.
  - Carrier-Declined: This owes nothing durable. The deliverable is a report that ENABLES a maintainer decision, and manufacturing a carrier for a decision nobody has taken yet would invent an obligation. If the maintainer acts on the 3 `NEEDS A MAINTAINER LOOK` rows, that action gets its own item at that time, informed by the report.
- THE `superseded`-CARRIER SEMANTICS QUESTION (F-05). Whether a gated item whose work shipped under a DIFFERENT, later plan should read as legitimate when its original carrier was superseded is a question about `_carrier_is_executed`, whose docstring records a deliberate maintainer ruling (2026-09-26) for the current behavior. Re-litigating a ruled decision is not an audit's job; the audit's job is to report that 6 of 7 such findings look exonerated on inspection.
  - Carrier-Declined: A deliberate, permanent fence rather than an outstanding obligation: the behavior is RULED and the ruling is recorded in the predicate's own docstring with its reasoning, so there is no pending work to lose track of. The audit surfaces the cohort and its evidence, which is what would justify re-opening the ruling if a maintainer ever wants to.

## Scope check

- Over-scope: none. Every path in `- Scope-Paths:` is touched by a numbered E-item: `tools/gate_drop_audit.py` (E-01, E-02, E-03), `tests/test_gate_drop_audit.py` (E-04), and `.aw/records/research/` (E-05, E-06, whose exact filename is tool-derived by `aw research new` and so is declared as the containing directory rather than guessed here).
- Under-scope: this plan REPORTS and does not REMEDIATE, and it leaves the staged-scope limitation in place. Both are deliberate: the first because `AGENTS.md` forbids mutating closed records, the second because widening an exit-blocking rule over 53 historical findings is a behavior change with its own blast radius, deferred above with its reasoning. The consequence a reviewer should weigh is that after this plan the 53 remain invisible to `aw check`; what changes is that they become KNOWN, reproducible, and adjudicated.

## Required tests / validation

New file `tests/test_gate_drop_audit.py`, built on the `_create_minimal_repo` fixture pattern from `tests/test_check_engine_release_gate.py`, one temp repo per case. Every assertion is an OUTCOME assertion on the auditor's JSON records, its exit code, and the fixture tree's state. NO test may read `tools/gate_drop_audit.py` with `inspect`, `ast`, regex or substring search, assert a caller count, or pin a docstring or comment banner (`AGENTS.md` execution contract; GUIDING_PRINCIPLES P16).

The classification cases are the point: ungated `done` (not reported); gated with no carrier (reported, `no-carrier`); gated with an EXECUTED same-gate carrier (not reported, legitimate HANDOFF); gated whose only same-gate carrier is `superseded/` (reported, `carrier-not-executed`); pre-boundary close (`pre-predicate` bucket); undatable close (`undated` bucket). The read-only property is itself a test, via a byte-and-mtime snapshot of the fixture tree before and after.

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

- [ ] V-01 validates E-01
  - Required evidence: paste the auditor's `--json` output head and its record count run against THIS repository, plus the exit code (must be 0 with findings present, proving it reports rather than gates). Paste also the passing fixture tests that discriminate reporting from not-reporting: the ungated `done` item absent from the output, and the gated no-carrier item present with class `no-carrier`. Paste the `N passed` summary line of `python3 -m pytest tests/test_gate_drop_audit.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the auditor output showing the three-way partition with its counts and the boundary date it printed, plus the derivation of that date (the `git log` output for the `orb9zb` finalize commit). Paste the passing fixture tests for a pre-boundary close landing in `pre-predicate` and an item with no datable close line landing in `undated`. Paste ALSO the evidence that all three history-tag spellings are needed: a fixture (or scratch-repo transcript) in which a close written as `set (aw backlog)` is dated correctly, demonstrating that matching only `done` would have missed it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a timing comparison on THIS repository between the shipped shared-index auditor and a deliberately naive per-item variant over the same corpus, showing the shared-index form is faster by a large factor, AND showing both produce the IDENTICAL finding set (the speedup must not change the answer). A bare timing number without the equal-results check does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_gate_drop_audit.py` with its `N passed` line, plus the test names, showing one case per classification branch (ungated, no-carrier, executed-carrier HANDOFF, superseded-carrier, pre-boundary, undated) and the read-only property test. Paste the read-only test's own assertion mechanism output (the before/after byte-and-mtime comparison), since that is the item's distinctive claim. Confirm by inspection and state explicitly that no test in the file reads the auditor's source via `inspect`, `ast`, regex or substring search.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the path of the created research record and the `aw research new` / `aw research index` output that produced and indexed it (proving it was tool-named, not hand-named). Paste `aw check research` conforming. Then paste the REPRODUCIBILITY check: the auditor run twice at the same HEAD producing byte-identical output (e.g. matching digests), and a line-by-line comparison of the report's live totals against the `## Findings` table, with any discrepancy resolved and explained rather than averaged. Quote the two stated limits (`--evidence` not persisted; retrospective verdict) from the committed report text.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the report's per-item disposition table and a count proving every finding carries exactly one of the three dispositions (no row blank, no row with two). Paste `git status --short` and `git diff --cached --name-only` at commit time showing NO path under `.aw/records/backlog/` is modified or staged, which is the no-mutation property this plan's whole framing rests on. Paste also the three `NEEDS A MAINTAINER LOOK` rows with their bare close messages quoted from the items, so a reviewer can confirm the classification was earned rather than asserted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only the paths this plan declares, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. This repository is a SHARED CHECKOUT: before each commit run `git diff --cached --name-only` and unstage with `git restore --staged <path>` anything you did not change, and re-verify after any failed raw commit attempt, since a rejecting hook can leave foreign paths in the index.

THE ONE PROHIBITION THAT DEFINES THIS PLAN: do not modify, move, re-gate, re-open or re-close ANY file under `.aw/records/backlog/`. The audit is read-only by policy, not by convenience (`AGENTS.md`: the gate rule governs LIVE items only, and gating a closed item asserts a history that did not happen). A commit from this plan touching a backlog record is a failure of the plan even if every test passes. V-06 requires the staged-set evidence that proves this.

ORDERING NOTE: author E-01 through E-03 and get E-04 green BEFORE producing the report in E-05. The report's numbers must come from the committed auditor, not from the authoring-time shell measurements in `## Findings`; those exist to be CHECKED by the auditor (V-05), and if the two disagree the shell numbers are the suspect ones.

POST-GATE LIFECYCLE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence. Perform the terminal transition with the tooled lifecycle (`aw ipd finalize`), never by hand-editing status or moving the file.
