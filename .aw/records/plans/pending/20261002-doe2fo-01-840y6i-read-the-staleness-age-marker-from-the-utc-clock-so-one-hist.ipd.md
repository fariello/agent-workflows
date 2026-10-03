# IPD: Read the staleness age marker from the UTC clock so one history record does not get two verdicts by reader timezone

- Date: 2026-10-02
- Kind: child
- Concern: The eight sibling plans in this cluster move every history WRITER onto the UTC clock, and NONE of them touches a READER. `attention._age_marker` compares a history date against `date.today()` on the LOCAL clock, so the same stored record gets two different staleness verdicts depending on the reader's timezone, and after the writer fix lands the two sides of that comparison are on DIFFERENT clocks by construction. Measured in this lane at HEAD `3fca2e6c7` against the REAL corpus (`aw attention --all --format json`, 2318 items): TEN live artifacts flip from `''` to `'!'` between `TZ=UTC` and `TZ=XXX-20`, among them `.aw/records/backlog/done/20260828-stalereceipt-01-xmqv5l-...` and nine `plans/superseded/` records, every one of them stamped `2026-09-02` and reported "stale, untouched for over 30 days" by one reader and "recent" by another at the same instant. The module docstring claims determinism in exactly the terms this violates ("no timestamps/mtime/locale"). REVIEW CORRECTION (PR-001): a second reader was proposed here and is NOT a defect (see F-02); the original authoring text follows for the record only: `workflow_artifacts_prune._calculate_run_age` compares a run id minted in UTC (`runner_shared` builds `run-%Y%m%dT%H%M%SZ-<pid>` from `datetime.now(timezone.utc)`) against a LOCAL `date.today()`, measured giving `age_days=0` under `TZ=UTC` and `age_days=1` under `TZ=XXX-20` for one run id minted seconds earlier, which moves a DELETION boundary rather than a glyph.
- Scope: IN: put the history-date age READER `attention._age_marker` on the UTC clock with an injectable `today` seam (the run-id reader `workflow_artifacts_prune` was REMOVED at review, PR-001: the run ids it parses are LOCAL per D55), matching the shipped `docs_render._as_of` precedent, and add the outcome tests neither has today. OUT, each with a reason recorded under "Deferred": every history WRITER (owned by `5ivkdh`, `9wcei0`, `rfyrvp`, `dmrbqa`); the cross-spelling writer guard (`ayhveg`); the lifecycle-gate coverage companion (`5xq2ng`); the duplicate-item convergence (`qjm4bg`); the `plans_archive`, `research_archive` and `workflow_artifacts_prune` age readers, whose inputs stay LOCAL per D55; the 30-day threshold and the `older_than_days` default, which are policy this plan must not move; and the three pre-existing suite failures.
- Scope-Paths: agent_workflows/attention.py, tests/test_history_date_clock_readers.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- From-Spec: 2vev8j
- Work-Kind: bug
- Priority: medium
- From-Backlog: doe2fo
- Blocks-Release: next
- Set: doe2fo
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 840y6i
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (aw set): plan-review revisions applied; see review record

- 2026-10-02 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005 (review record 20261002-doe2fo-01-840y6i-...review.md).
- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `doe2fo`. THE ITEM'S HEADLINE IS A DUPLICATE AND ITS RESIDUAL SLICE IS NOT. `doe2fo` is the ninth filing of one defect; the WRITER side is already owned by eight plans, and `qjm4bg` E-03 lists `doe2fo` among five "pure duplicates ... none adds a measurement, a reproduction, or a fix constraint". That verdict was tested rather than accepted, and it holds for the writers and FAILS for the readers: a census of every local-clock date call in `agent_workflows/` found two readers that compare a UTC-stamped value against a LOCAL today, and no pending plan declares either site. The defect was measured on the REAL corpus (ten live artifacts flip verdict by reader timezone) and on a real run id (a deletion-boundary age differing by a day). The clock question needed no maintainer decision: spec `2vev8j` 4.4 is `approved` and human-attested. Bare suite baseline at authoring: `3 failed, 4624 passed, 2 skipped in 271.64s`, all three failures pre-existing and separately filed.
- 2026-10-02 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a staleness verdict depend only on WHEN something happened, never on the timezone of the
machine ASKING. The eight sibling plans fix the writers; this one fixes the one reader,
`attention._age_marker`, that compares a UTC-stamped history date against a local `today`. (A
second candidate, the workflow-artifacts prune age, was removed at review: its operands already
share the LOCAL clock D55 rules for run ids.)

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: pin the defect before changing it

- [x] E-01 Add `tests/test_history_date_clock_readers.py` asserting that a staleness verdict is INVARIANT under the reader's timezone, and demonstrate it RED at base. This comes first and is its own item because the suite cannot currently see the defect: a census of `tests/` found ZERO test referencing `_age_marker` and ZERO test setting `TZ` or calling `time.tzset()`, so "the suite is green" is worthless evidence here and a fix landed without a failing test first would be unfalsifiable.

    DRIVE BOTH SIDES OF UTC, not just one. Use a timezone EAST of UTC and one WEST of it, because which side is inside the skew window depends on the wall-clock hour the suite happens to run at: measured in this lane at 11:09 UTC, `TZ=XXX-20` (UTC+20) gives local `2026-10-03` against UTC `2026-10-02` and so skews, while `TZ=Pacific/Honolulu` (UTC-10) gives local `2026-10-02` and does NOT. A test pinned to only one side passes for part of every day for the wrong reason. Prefer fixed-offset zones over named cities, since a named zone's offset is a political value that can change under the test. CHOOSE THE PAIR SO THAT AT EVERY UTC HOUR AT LEAST ONE OF THEM IS ON A DIFFERENT CALENDAR DATE FROM UTC, and have the test compute and ASSERT that at least one case is in a skew window, so it can never pass vacuously: `XXX-20` (UTC+20) differs from UTC whenever the UTC hour is 04 or later, `XXX+12` (UTC-12) whenever it is before 12, so together they cover all 24 hours (measured at review at 20:50 UTC: `XXX-20` flips 10 real items, `XXX+12` flips 0, exactly as predicted).

    DRIVE THE CODE UNDER TEST IN A SUBPROCESS WITH `TZ` IN ITS ENVIRONMENT, rather than `os.environ['TZ'] = ...; time.tzset()` in the pytest worker: the suite runs under xdist and an in-process `tzset` changes the clock for every later test in that worker until undone. The subprocess pattern was demonstrated at review (`subprocess.run([sys.executable, '-c', ...], env={..., 'TZ': tz})`). Call `_age_marker` WITHOUT a `today` argument in these cases, so the test is RED at base for the real reason (a timezone-dependent verdict) and not because the base function lacks the new keyword; the injectable `today` gets its own separate case, GREEN after only, pinning that an explicit `today` is honored.

    ASSERT ON THE RETURNED VERDICT, never by reading the source for a `timezone.utc` token (GUIDING_PRINCIPLES P16 and the `AGENTS.md` no-code-pinning rule). The outcome is the marker string and the age integer.

    COVER THE BOUNDARY, NOT A MIDPOINT. The marker flips at `age_days > 30`, so a record 30 days before the UTC date is the only input that can expose a one-day reader error; a record 400 days old reads `'!'` under every timezone and would pass against the unfixed code. The measured flip set is exactly the `utc_today - 30 days` cohort.

    SET `TZ` FOR THE CODE UNDER TEST ONLY, restoring it afterwards, and never for the suite as a whole. A suite-wide `TZ=UTC` would hide this class of bug behind an environment variable, which is the anti-pattern `ayhveg` records the `jbipfa` masks as having introduced.
  - Depends on: none
  - Expected outcome: a new test file whose cases cover the marker boundary under an east and a west timezone, plus one case for the injectable `today`; the timezone cases demonstrated FAILING at base with the actual output pasted, naming each failing case.
  - Execution state: performed

### Task group 2: put the history-date reader on the UTC clock

- [x] E-02 Put `attention._age_marker` on the UTC clock with an INJECTABLE `today` parameter, and correct the docstring claim that is now false. The function compares `date.today()` against a date parsed out of `last_history_at`, which `attention_contract.last_history_at` derives from the artifact's `## Workflow history` and which spec `2vev8j` 4.4 rules is UTC.

    GIVE IT A `today: Optional[date] = None` SEAM DEFAULTING TO THE UTC DATE, following the shipped precedent `docs_render._as_of`, which takes an optional `now` and defaults to `datetime.now(timezone.utc)`. The seam is not decoration: E-01 needs to assert a boundary verdict without waiting for a real calendar day to pass, and the alternative (monkeypatching `datetime` inside the module) is the brittle pattern `tests/test_specs_date_containment.py` already had to build `_FakeDate`/`_FakeDateTime` for.

    FIX THE DOCSTRING IN THE SAME EDIT. It currently ends "Deterministic: compares ISO dates only", which is the precise claim this defect falsifies, and the module docstring's determinism paragraph says "no timestamps/mtime/locale". Leaving a sentence that asserts the property being repaired is how the next reader concludes the site is already correct and looks elsewhere. State which clock it reads and cite `2vev8j` 4.4.

    BOTH CALL SITES ARE RENDER-ONLY AND MUST BOTH BE CHECKED. `_age_marker` is called from `attention._render_item_row` and from one inline board renderer in `cli.py`; neither passes a `today`, so a defaulted parameter leaves both unchanged at the call site. Confirm by driving the board, because an added keyword that silently changes a caller's arity is exactly the kind of breakage a grep does not show.

    DO NOT CHANGE THE 30-DAY THRESHOLD OR THE `'!'`/`'?'`/`''` VOCABULARY. The verdict for an UNAMBIGUOUS input must be byte-identical before and after; only the AMBIGUOUS boundary cohort may move. That is what makes this a clock fix rather than a policy change, and V-02 proves it on the real corpus.
  - Depends on: E-01
  - Expected outcome: `_age_marker` resolves its reference date from the UTC clock, accepts an injectable `today`, and carries a docstring that names the clock and cites `2vev8j` 4.4; the human board renders unchanged outside the boundary cohort; the E-01 marker cases pass.
  - Execution state: performed

### Task group 3: prove the census, so "every reader" is checkable

- [x] E-04 Audit every REMAINING local-clock date call in `agent_workflows/` and record a per-site READER-or-WRITER-or-NEITHER verdict with the clock of its OTHER operand, converting nothing further without a measured mixed-clock comparison. This item exists because E-02 was chosen from a census, and a census can miss a site; a verdict table is what makes "every reader" checkable instead of asserted. It is deliberately the LAST item so its table describes the tree as this plan leaves it.

    FOUR SITES ARE ALREADY CLASSIFIED AND MUST BE RE-CONFIRMED RATHER THAN TRUSTED. `workflow_artifacts_prune._calculate_run_age` compares against `_parse_run_date`, which parses only a LEADING `YYYYMMDD`; the workflow-artifacts RUN_ID shape is `YYYYMMDD-HHMMSS`, which `DECISIONS.md` D55 rules LOCAL by name, and a runner `run-%Y%m%dT%H%M%SZ-<pid>` id does not parse at all (`_parse_run_date('run-20261002T110915Z-830789')` returns `None`, measured at review) and falls back to `date.fromtimestamp(mtime)`, also local. Both operands are LOCAL, so it must stay as it is (PR-001). `plans_archive._age_days` compares against `_plan_date`, read from a plan's `- Date:` front matter or filename prefix, which `DECISIONS.md` D55 rules LOCAL, so a LOCAL today is the MATCHING operand and converting it would introduce the very mixed-clock error this plan removes. `research_archive._age_days` compares against a research doc's `created` field, same reasoning. `attention._age_marker`'s `'?'` branch returns before any date arithmetic and is unaffected.

    STATE THE OTHER OPERAND'S CLOCK FOR EVERY ROW, because that is the whole test and a bare "local" verdict is not actionable. A local today against a local stored date is CORRECT and must not move; a local today against a UTC stored value is the defect. This distinction is why the correct outcome of this audit may legitimately be "no further conversion", and recording that explicitly is more useful than a silent skip.

    WATCH FOR A SITE THE WRITER PLANS ARE ABOUT TO MOVE. `5ivkdh`, `9wcei0`, `rfyrvp` and `dmrbqa` are all `to-review` and change what clock several stored dates carry. If any of them has executed by the time this item runs, a row whose verdict was "local today, local stored date, correct" may have become a defect. Re-derive each row against the tree as it actually is and name which sibling plans were executed at audit time.
  - Depends on: E-02
  - Expected outcome: a table of every remaining `date.today()`/`datetime.now()`-class call in `agent_workflows/`, each with a READER/WRITER/NEITHER verdict, the clock of its other operand, and a convert-or-leave decision; the enumerating command recorded so the census is reproducible; which sibling writer plans were executed at audit time stated; no site converted without a measured mixed-clock comparison.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- OUTCOME TESTS ONLY (`AGENTS.md`, GUIDING_PRINCIPLES P16). The clock fix is proven by the marker string and age integer a reader returns, never by asserting that a module calls `datetime.timezone.utc`.
- Run the suite BARE: `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and deselects `slow`/`livecorpus`; `-n0` is forbidden and a second `-q` suppresses the `N passed` line this plan requires pasted. Use `-o addopts=""` only when a narrowed run needs per-test counts.
- `aw` re-execs into the checkout's own package unless `AW_NO_REEXEC=1` is set; inside a lane worktree it prints a notice naming both paths. Set `AW_NO_REEXEC=1` on every `aw` invocation so the lane's own code runs and the notice does not pollute pasted evidence.
- THE TWO CLOCKS ARE BOTH CORRECT AND THE RULINGS DO NOT CONFLICT. `2vev8j` 4.4 scopes itself to history WRITERS and calls local time "a RENDER-TIME concern only"; D55 scopes itself to human-facing NAMES. A reader must match the clock of the value it compares against, which is why E-04's verdict column is the other operand's clock and not a blanket preference.
- AN INJECTABLE DATE SEAM IS THE ESTABLISHED SHAPE, not a novelty: `docs_render._as_of` takes an optional `now` defaulting to `datetime.now(timezone.utc)`, and `plans_archive._age_days`, `research_archive._age_days`, `plan_prune` and `_calculate_run_age` all already thread an explicit `today`. `_age_marker` is the outlier with no seam.
- DERIVE A VALUE, NEVER RE-LIST IT (GUIDING_PRINCIPLES P8). Adding a second inline `datetime.now(timezone.utc)` rather than resolving the date once per call reproduces in a reader the duplication this cluster exists to remove from the writers.

## Findings

Established in this lane at HEAD `3fca2e6c7` by driving the real CLI against the real corpus.

| # | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH (THE DEFECT, MEASURED ON THE REAL CORPUS) | `aw attention --all --format json` returned 2318 items. Replaying `_age_marker` over every item's real `last_history_at` under `TZ=UTC` and `TZ=XXX-20`: TEN items change verdict, all stamped `2026-09-02` (= `utc_today - 30d`), each `''` under UTC and `'!'` under UTC+20. Named: one `backlog/done/` item (`xmqv5l`) and nine `plans/superseded/` plans (`bl9q3d`, `qcqhj7`, `rchpms`, `7p9n2v`, `58ha43`, `2c122z`, `6knsrx`, and two siblings). | **TEN LIVE ARTIFACTS CARRY TWO CONTRADICTORY STALENESS VERDICTS AT THE SAME INSTANT**, decided by who is asking rather than by the record. This is user-visible on the board a maintainer reads to triage, and it is a measurement on the real tree rather than a constructed fixture. |
| F-02 | HIGH (THE SECOND READER, WORSE STAKES) | `runner_shared` mints run ids as `run-%Y%m%dT%H%M%SZ-<pid>` from `datetime.now(timezone.utc)` (measured: `run-20261002T110915Z-830789`). `workflow_artifacts_prune._parse_host_date`-equivalent `_parse_run_date` reads that leading `YYYYMMDD`; `plan_prune` defaults `today` to `date.today()`. For one id minted seconds earlier: `age_days=0` under `TZ=UTC`, `age_days=1` under `TZ=XXX-20`. | **CORRECTED AT REVIEW (PR-001): NOT A DEFECT.** The premise does not hold. `_parse_run_date` reads only a LEADING `YYYYMMDD`, so the `run-...Z-<pid>` id cited as evidence returns `None` and never reaches the date comparison (measured: `run-20261002T110915Z-830789 None`); it falls back to the local date of the newest mtime, compared with a local today, which is consistent. The ids that DO parse are workflow-artifacts RUN_IDs of shape `YYYYMMDD-HHMMSS` (`00-run-protocol.md` "Use a timestamp run ID"), which D55 explicitly rules LOCAL. A local today is therefore the matching operand, and converting it to UTC (the original E-03) would have introduced the mixed-clock error into a deletion planner. The `age_days=0`/`1` measurement can only arise from an id with a bare leading date, i.e. a local-named RUN_ID read as if it were UTC. E-03 and V-03 were removed. |
| F-03 | HIGH (NO PLAN OWNS EITHER SITE) | Every pending plan's `- Scope-Paths:` was collected. Five declare `agent_workflows/attention.py` (`r61br4`, `uxb0tz`, `qp8fn1`, and two others) and NONE mentions `_age_marker`, `last_history_at` or staleness in its items; `workflow_artifacts_prune.py` is declared by NO pending plan. The eight cluster plans are writer-only: `5ivkdh` lists the four age readers under "THE FOUR READ-ONLY AGE COMPARISONS ARE NOT TOUCHED" and declines them as "not a defect; these compare rather than write". | **THE READER SIDE IS AN ACKNOWLEDGED, UNCARRIED GAP.** `5ivkdh`'s declination is right for the two archive readers and WRONG for `_age_marker` (review found it RIGHT for `workflow_artifacts_prune`, PR-001), because it reasons from "compares rather than writes" when the actual test is whether the two operands share a clock. That is the distinction this plan supplies. |
| F-04 | HIGH (THE SUITE CANNOT SEE EITHER DEFECT) | `grep` over `tests/` for `_age_marker` returned ZERO hits; for `time.tzset()` or a `TZ` assignment, ZERO. Bare suite at base: `3 failed, 4624 passed, 2 skipped`. | **NO TEST FAILS TODAY AND NO TEST WOULD NOTICE THE FIX**, so a green suite proves nothing here. This is why E-01 precedes the fix and why its acceptance bar is a guard demonstrated RED at base. |
| F-05 | MEDIUM (THE CODE ASSERTS THE PROPERTY IT BREAKS) | `_age_marker`'s docstring ends "Deterministic: compares ISO dates only." The `attention` module docstring's determinism paragraph reads "no timestamps/mtime/locale; `last_history_at` parsed from history, never mtime." | **A FALSE DETERMINISM CLAIM SITS DIRECTLY ON THE DEFECT**, which is how a reader auditing for exactly this bug concludes the site is clean. Correcting the sentence is part of the fix (E-02), not cleanup. |
| F-06 | MEDIUM (THE FIX HAS A TRAP IN THE FALLBACK) | `_calculate_run_age` falls back to `date.fromtimestamp(newest_mtime)` when a run id carries no parseable date; `date.fromtimestamp` is LOCAL by definition. | **MOOT AFTER PR-001.** The fallback and the comparison date are both LOCAL, which is consistent; with no conversion, nothing can desynchronize them. Kept as the record of why a partial conversion would have been doubly wrong. |
| F-07 | MEDIUM (TWO READERS MUST NOT BE CONVERTED) | `plans_archive._age_days` compares against `_plan_date`, parsed from a plan's `- Date:` or filename prefix; `research_archive._age_days` compares against a research doc's `created`. Both stored values are LOCAL per `DECISIONS.md` D55. | **A LOCAL TODAY IS THE CORRECT OPERAND THERE, AND CONVERTING IT WOULD INTRODUCE THIS VERY DEFECT.** Recorded because "unify every date onto UTC" is the obvious reading of this cluster and is wrong; it is also why E-04's table records the other operand's clock rather than a verdict alone. |
| F-08 | MEDIUM (THIS ITEM'S HEADLINE IS GENUINELY A DUPLICATE) | `doe2fo`'s summary describes the backlog-setter writer defect, which eight plans already own. `qjm4bg` E-03 names `doe2fo` among five "pure duplicates" to be closed citing `5ivkdh`. The seven sibling items each graduated to a plan carrying a DISTINCT residual slice (`9wcei0` scaffold, `rfyrvp` plan-family created record, `dmrbqa` sidecar, `5xq2ng` lifecycle-gate coverage, `ayhveg` cross-spelling guard, `qjm4bg` convergence). | **THE WRITER SLICE IS CORRECTLY CLOSED AS A DUPLICATE AND THE READER SLICE IS NOT**, so this plan deliberately does NOT re-fix the writers. `qjm4bg`'s verdict on `doe2fo` is right about its headline and incomplete about the tree, which F-03 measures. |
| F-09 | LOW (SKEW REQUIRES THE RIGHT SIDE OF UTC) | Measured at 11:09 UTC: `TZ=XXX-20` gives local `2026-10-03` against UTC `2026-10-02` (skewed); `TZ=Pacific/Honolulu` gives local `2026-10-02` (NOT skewed). | **A TEST PINNED TO ONE TIMEZONE PASSES FOR PART OF EVERY DAY FOR THE WRONG REASON.** E-01 therefore requires one zone east and one west, and prefers fixed offsets over named cities whose offsets are political values. |
| F-10 | N/A (BASELINE) | Bare `python3 -m pytest` at HEAD `3fca2e6c7`: `3 failed, 4624 passed, 2 skipped, 3 warnings in 271.64s`. Failures: `test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`, `test_selector_type_containment.py::test_must_not_refuse_matrix`, `test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`. | **THREE PRE-EXISTING FAILURES, EACH ALREADY FILED** (`6bolin`, `bxnhdj`, `8jeh4x`). Compare FAILURE SETS BY NAME rather than counts, and do not fix another item's failure in this plan. |

## Proposed changes (ordered, validatable)

1. `tests/test_history_date_clock_readers.py`: the timezone-invariance guard for the staleness marker, demonstrated RED at base (E-01).
2. `agent_workflows/attention.py`: `_age_marker` resolves its reference date from the UTC clock via an injectable `today`, and its docstring stops claiming the determinism this defect falsified (E-02).
3. (Removed at review, PR-001: `workflow_artifacts_prune` stays LOCAL, recorded in E-04's table.)
4. The census table of every remaining local-clock date call with its other operand's clock and a convert-or-leave verdict, recorded as V-04 evidence (E-04).

## Deferred / out of scope (with reason)

- EVERY HISTORY WRITER IS OUT. `5ivkdh` owns the shared UTC helper plus the backlog/specs/releases/readiness writers, `9wcei0` and `rfyrvp` own the plan-family created records, and `dmrbqa` owns the gitignored sidecar. This plan takes NO dependency on them: a reader comparing like-for-like clocks is correct whether they land before or after, which is why it is safe to review in parallel rather than queued behind four plans.
  - Carrier: 5ivkdh
  - Carrier-Evidence: .aw/records/plans/executed/20261001-7qvs1c-01-5ivkdh-unify-every-artifact-history-date-onto-the-utc-clock-ruled-b.ipd.md
- THE CROSS-SPELLING WRITER GUARD IS OUT. `ayhveg` derives a timezone-parameterized guard from `command_surface.COMMAND_INVENTORY` setter/note verbs. That instrument covers writers; neither reader here is a CLI verb that writes a history record, so it would not reach them.
  - Carrier: ayhveg
- THE LIFECYCLE-GATE COVERAGE COMPANION IS OUT. `5xq2ng` reports when `check.lifecycle-transition-invalid` validates nothing once the writer fix removes the date variation it depends on. That is a different reader with a different failure mode (silent loss of coverage, not a timezone-dependent verdict).
  - Carrier: 5xq2ng
- THE DUPLICATE-ITEM CONVERGENCE IS OUT, INCLUDING THIS PLAN'S OWN SOURCE ITEM. `qjm4bg` closes the cluster's duplicates and names `doe2fo` among them. This plan writes no status onto `doe2fo`; the runner sets it `graduated` on the `From-Backlog` handoff. Note for whoever executes `qjm4bg`: `doe2fo` now has a carrier, so its HANDOFF route applies rather than the SATISFIED route E-03 assumed for it.
  - Carrier: qjm4bg
- THE `plans_archive` AND `research_archive` AGE READERS ARE NOT CONVERTED. Both compare a local `today` against a stored value that D55 rules LOCAL (a plan's `- Date:`/filename prefix, a research doc's `created`), so the clocks already MATCH and converting them would introduce the defect this plan removes (F-07). E-04 gives each an explicit verdict rather than silently skipping it.
  - Carrier-Declined: not a defect; both operands are already on the same clock, and a UTC today against a local stored date would be an off-by-one-day error.
- THE 30-DAY THRESHOLD, THE `'!'`/`'?'`/`''` VOCABULARY, AND `older_than_days` ARE NOT TOUCHED. Which calendar day counts as today is a correctness question; how many days old is too old is policy. Moving both at once would make it impossible to tell which change caused a verdict to move.
  - Carrier-Declined: not a defect; the thresholds are deliberate policy and no measurement suggests they are wrong.
- NO STORED DATE IS REWRITTEN. Records already written carry whichever clock wrote them, and the boundary cohort's verdicts legitimately change because the comparison was wrong, not because the records are. Restamping committed history would assert dates that were never recorded (GUIDING_PRINCIPLES P4).
  - Carrier-Declined: not a defect; the existing records are the honest history.
- THE THREE PRE-EXISTING SUITE FAILURES ARE NOT FIXED (F-10). Each is already filed (`6bolin`, `bxnhdj`, `8jeh4x`) and none involves a date clock.
  - Carrier-Declined: unrelated to this plan's subject; each already has its own filed carrier.

## Scope check

- Over-scope: none after review. Every declared path is edited by a numbered item: `tests/test_history_date_clock_readers.py` (E-01), `agent_workflows/attention.py` (E-02). `agent_workflows/workflow_artifacts_prune.py` was removed from scope at review (PR-001). E-04 produces evidence, not an edit.
- Under-scope: `CHANGELOG.md` is deliberately NOT declared. The user-visible statement about this cluster ("history dates are now UTC everywhere") belongs to `5ivkdh`, which owns the entry; a second entry for the reader half would split one user-facing change across two lines. If E-04's audit finds a reader whose fix is genuinely user-visible on its own, declare `CHANGELOG.md` at execution and record the widening in the transition message, which this note authorizes. E-04 may also find a history-date reader outside the declared set; same treatment. The plan's own file needs no declaration (implicit lifecycle-artifact allowance, spec `ipd-structure-and-linting` Section 4.5).

## Required tests / validation

- `tests/test_history_date_clock_readers.py` run alone with `-o addopts=""`, every case named, demonstrated RED AT BASE (stash or revert the source edits and paste the failure) and GREEN after. A guard never seen failing proves nothing, and F-04 measures that nothing else in the suite can see the defect.
- The BARE suite: `python3 -m pytest`, with the `N passed` line pasted. F-10's `3 failed, 4624 passed, 2 skipped` at HEAD `3fca2e6c7` is authoring-time CONTEXT, not the bar: run a bare suite at execution HEAD BEFORE any edit, paste it, and compare FAILURE SETS BY NAME against that; any new failing nodeid must be re-run in isolation and attributed.
- `tests/test_attention.py`, `tests/test_attention_contract.py`, `tests/test_workflow_artifacts_prune.py` and `tests/test_plans_archive.py`, each run individually with results pasted: E-02 edits the module the first two cover, and the last two guard D55 readers this plan must NOT move.
- THE REAL-CORPUS INVARIANCE CHECK, which is the strongest available evidence and the measurement F-01 was derived from: replay `_age_marker` over every item returned by `aw attention --all --format json` under `TZ=UTC` and under a timezone east of UTC, and assert ZERO items change verdict. At base this reports a NONZERO count, re-derived at execution (ten at authoring and again at review; the set is live); after the fix it must report none. Use an east zone that is skewed at the hour the check runs (see E-01), or both zones. Paste both numbers and the command.
- A REAL-CORPUS NO-POLICY-CHANGE CHECK: diff the full set of `(path, marker)` pairs before and after the fix under a FIXED `TZ=UTC`, and confirm the only differences are inside the boundary cohort F-01 names. This is what distinguishes a clock fix from a threshold change.
- `AW_NO_REEXEC=1 aw attention`, `AW_NO_REEXEC=1 aw attention --check`, `AW_NO_REEXEC=1 aw check` and `AW_NO_REEXEC=1 aw sanitize --agent`. `aw check` and `aw attention --check` exit 1 on PRE-EXISTING conditions unrelated to this plan, so the honest bar is an UNCHANGED FINDING SET: re-derive before and after and diff. Do not "fix" another plan's finding or another lane's state.
- `AW_NO_REEXEC=1 aw ipd lint --phase pre-transition` on this plan, conforming.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Verify the staged set against this plan's `Scope-Paths` before committing.

## Spec / documentation sync

No spec is amended and `- Scope-Paths:` declares no `.spec.md` file.

This plan IMPLEMENTS the reader half of spec `2vev8j` Section 4.4 ("One timezone for every writer"),
which is already `approved` with a human attestation, and respects `DECISIONS.md` D55, which is
already current. It changes neither contract. The `- From-Spec: 2vev8j` field records the link.

Section 4.4's wording is worth noting for a reviewer without proposing an edit: it says "Every
WRITER, tool and human-facing helper alike, records UTC; local time is a RENDER-TIME concern only."
Read narrowly, a staleness marker is a render-time concern and could be argued exempt. That reading
does not survive the measurement: F-01 shows the render disagreeing with ITSELF across two readers of
one record, so the ruling's purpose (one record, one answer) reaches it. Whether 4.4's text should be
widened to name readers explicitly is a maintainer call, recorded in OQ-02 and not assumed here.

`CHANGELOG.md` is deliberately not declared; see "Scope check" for why the entry belongs to `5ivkdh`.

## Open questions

### OQ-01: Which clock should a staleness or age READER use?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE AND MEASUREMENT, not referred to the maintainer. The rule is that a reader must use THE CLOCK OF THE VALUE IT COMPARES AGAINST, which makes the answer site-specific rather than global. `attention._age_marker` compares `last_history_at`, which `attention_contract.last_history_at` derives from `## Workflow history` and which spec `2vev8j` 4.4 (`approved`, human-attested `- 2026-09-09 approved (aw set, --by-human)`) rules is UTC, so that reader is UTC. `workflow_artifacts_prune` was originally classified UTC here; review CORRECTED that (PR-001): the only ids it parses are leading-`YYYYMMDD` workflow-artifacts RUN_IDs, which D55 rules LOCAL, and the runner's `run-...Z` ids do not parse at all, so that reader is LOCAL and stays. `plans_archive` and `research_archive` compare values `DECISIONS.md` D55 rules LOCAL, so those readers stay LOCAL (F-07). The blanket reading "unify every date onto UTC" is therefore WRONG and would break two correct readers, which is why E-04's audit records the other operand's clock for every row rather than a verdict alone.

### OQ-02: Should spec `2vev8j` Section 4.4 be widened to name READERS, not only writers?

- Blocking: no
- Status: deferred
- Owner: maintainer
- Carrier: 6ly144
- Resolution or deferral rationale: DEFERRED TO THE MAINTAINER AS A CONTRACT QUESTION, and deliberately NOT resolved here, because amending an `approved`, human-attested spec changes the contract every other plan in this cluster is reviewed against. 4.4's text binds "every writer" and calls local time "a RENDER-TIME concern only", so a reader is arguably outside its letter even though F-01 measures the render contradicting itself across two readers of one record. This plan needs no amendment to be correct: it is justified by the measurement alone, and the fix is right under either reading. What a maintainer may want is the stronger INVARIANT stated once in the spec (a stored value and the today it is compared against must share a clock), which would also make F-07's two leave-alone verdicts follow from the contract rather than from this plan's prose. Raising it rather than writing it is the point: the useful version of that sentence constrains readers the repository has not yet enumerated, and E-04's table is the input a maintainer would want before ruling.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: the full committed source of `tests/test_history_date_clock_readers.py`, plus its output run with `-o addopts=""` FAILING at base (source edits reverted or stashed, and say which) and PASSING after, every case named in both runs. The failing run must show the timezone cases failing on the verdict, not on a missing keyword (E-01). State explicitly which timezone is east and which west of UTC, and confirm from the pasted output that at least one case was INSIDE a skew window by printing the local and UTC dates the test observed (the test must itself assert this) (F-09: a run at the wrong hour can make a one-sided test pass vacuously). Confirm `TZ` was set only in subprocess environments and that no suite-wide or in-worker `TZ`/`tzset` was used. Confirm P16 compliance: state that no assertion calls `inspect`, reads production source text, or asserts on a symbol name.
  - Observed evidence:
    Full committed source of `tests/test_history_date_clock_readers.py`:
    ```python
    \"\"\"Tests for history date clock reader timezone invariance (IPD 840y6i).

    Asserts that staleness verdicts returned by attention._age_marker are invariant
    under the reader's timezone by testing across UTC, east of UTC (XXX-20, UTC+20),
    and west of UTC (XXX+12, UTC-12).

    Subprocesses are used to isolate environment variables (TZ) so no in-worker
    time.tzset() or os.environ mutation occurs under pytest-xdist.
    \"\"\"

    from __future__ import annotations

    import os
    import subprocess
    import sys
    import unittest
    from datetime import date, datetime, timedelta, timezone
    from pathlib import Path
    from typing import Optional

    REPO_ROOT = Path(__file__).resolve().parent.parent


    def _run_in_subprocess(code: str, args: list[str], tz: str) -> str:
        \"\"\"Run a small python snippet in a subprocess with a specific TZ.\"\"\"
        env = {
            **os.environ,
            "TZ": tz,
            "PYTHONPATH": str(REPO_ROOT),
            "AW_NO_REEXEC": "1",
        }
        proc = subprocess.run(
            [sys.executable, "-c", code, *args],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout


    def _get_observed_date(tz: str) -> date:
        \"\"\"Query date.today() in a subprocess under the given timezone.\"\"\"
        code = "from datetime import date; print(date.today().isoformat())"
        out = _run_in_subprocess(code, [], tz)
        return date.fromisoformat(out.strip())


    def _call_age_marker_subprocess(last_history_at: Optional[str], tree: str, tz: str) -> str:
        \"\"\"Call attention._age_marker in a subprocess with the given TZ.

        Crucially, calls _age_marker WITHOUT a 'today' keyword argument so the test
        asserts on verdict invariance under reader timezone rather than signature errors.
        \"\"\"
        code = (
            "import sys;"
            "from agent_workflows.attention import _age_marker;"
            "hist = None if sys.argv[1] == '__NONE__' else sys.argv[1];"
            "tree = sys.argv[2];"
            "sys.stdout.write(_age_marker(hist, tree))"
        )
        arg_hist = "__NONE__" if last_history_at is None else last_history_at
        return _run_in_subprocess(code, [arg_hist, tree], tz)


    class TestHistoryDateClockReadersTimezoneInvariance(unittest.TestCase):
        \"\"\"Verifies that attention._age_marker produces timezone-invariant staleness markers.\"\"\"

        def test_timezone_invariance_east_and_west_boundaries(self):
            \"\"\"Assert staleness verdicts are invariant under reader timezone across UTC, east, and west.

            East: XXX-20 (UTC+20)
            West: XXX+12 (UTC-12)
            \"\"\"
            # 1. Measure observed dates under UTC, east (XXX-20), and west (XXX+12)
            utc_date = _get_observed_date("UTC")
            east_date = _get_observed_date("XXX-20")
            west_date = _get_observed_date("XXX+12")

            print(
                f"\n[Skew Window Observation] UTC: {utc_date.isoformat()}, "
                f"East (XXX-20, UTC+20): {east_date.isoformat()}, "
                f"West (XXX+12, UTC-12): {west_date.isoformat()}"
            )

            # Confirm that at least one timezone is in a skew window (dates differ)
            # to ensure the test never runs vacuously (F-09).
            self.assertTrue(
                east_date != utc_date or west_date != utc_date,
                f"Neither east ({east_date}) nor west ({west_date}) differed from UTC ({utc_date}); "
                "cannot verify timezone invariance without clock skew.",
            )

            # 2. Test boundary cohort:
            # Boundary 1: exactly 30 days before UTC date.
            # Under UTC clock, age_days == 30. Threshold is age_days > 30, so verdict is ''.
            # Under a reader ahead of UTC (e.g. XXX-20 tomorrow), age_days would be 31 -> '!'.
            d30 = (utc_date - timedelta(days=30)).isoformat()

            # Boundary 2: exactly 31 days before UTC date.
            # Under UTC clock, age_days == 31. Threshold is age_days > 30, so verdict is '!'.
            # Under a reader behind UTC (e.g. XXX+12 yesterday), age_days would be 30 -> ''.
            d31 = (utc_date - timedelta(days=31)).isoformat()

            # Midpoint / non-boundary dates:
            d10 = (utc_date - timedelta(days=10)).isoformat()   # Recent -> ''
            d400 = (utc_date - timedelta(days=400)).isoformat() # Stale -> '!'

            test_cases = [
                ("boundary_30d_recent", d30, ""),
                ("boundary_31d_stale", d31, "!"),
                ("non_boundary_10d_recent", d10, ""),
                ("non_boundary_400d_stale", d400, "!"),
            ]

            for label, hist_date, expected_verdict in test_cases:
                utc_verdict = _call_age_marker_subprocess(hist_date, "plans", "UTC")
                east_verdict = _call_age_marker_subprocess(hist_date, "plans", "XXX-20")
                west_verdict = _call_age_marker_subprocess(hist_date, "plans", "XXX+12")

                self.assertEqual(
                    utc_verdict,
                    expected_verdict,
                    f"[{label}] UTC verdict {utc_verdict!r} did not match expected {expected_verdict!r} for date {hist_date}",
                )
                self.assertEqual(
                    east_verdict,
                    expected_verdict,
                    f"[{label}] East timezone XXX-20 (UTC+20) verdict {east_verdict!r} != expected {expected_verdict!r} for date {hist_date}",
                )
                self.assertEqual(
                    west_verdict,
                    expected_verdict,
                    f"[{label}] West timezone XXX+12 (UTC-12) verdict {west_verdict!r} != expected {expected_verdict!r} for date {hist_date}",
                )

        def test_age_marker_injectable_today_seam(self):
            \"\"\"Verify that _age_marker accepts an explicit injectable 'today' seam.\"\"\"
            from agent_workflows.attention import _age_marker

            # Explicit reference date
            fixed_ref = date(2026, 6, 15)
            # 30 days before 2026-06-15 is 2026-05-16 -> age_days=30 -> ''
            self.assertEqual(_age_marker("2026-05-16", tree="plans", today=fixed_ref), "")
            # 31 days before 2026-06-15 is 2026-05-15 -> age_days=31 -> '!'
            self.assertEqual(_age_marker("2026-05-15", tree="plans", today=fixed_ref), "!")

            # Passing today=None defaults to the UTC clock
            utc_today = datetime.now(timezone.utc).date()
            d30 = (utc_today - timedelta(days=30)).isoformat()
            d31 = (utc_today - timedelta(days=31)).isoformat()
            self.assertEqual(_age_marker(d30, tree="plans", today=None), "")
            self.assertEqual(_age_marker(d31, tree="plans", today=None), "!")

        def test_age_marker_edge_cases_and_historyless_trees(self):
            \"\"\"Verify None, malformed history dates, and history-less trees.\"\"\"
            from agent_workflows.attention import _age_marker

            # History-less trees suppress '?'
            self.assertEqual(_age_marker(None, tree="actions"), "")
            self.assertEqual(_age_marker(None, tree="research"), "")

            # Normal trees return '?' on missing or malformed history
            self.assertEqual(_age_marker(None, tree="plans"), "?")
            self.assertEqual(_age_marker(None, tree="backlog"), "?")
            self.assertEqual(_age_marker("invalid-date", tree="plans"), "?")


    if __name__ == "__main__":
        unittest.main()
    ```

    Failing run at base (`agent_workflows/attention.py` unedited):
    ```
    $ python3 -m pytest tests/test_history_date_clock_readers.py -o addopts="" -v
    collected 3 items

    tests/test_history_date_clock_readers.py::TestHistoryDateClockReadersTimezoneInvariance::test_age_marker_edge_cases_and_historyless_trees PASSED [ 33%]
    tests/test_history_date_clock_readers.py::TestHistoryDateClockReadersTimezoneInvariance::test_timezone_invariance_east_and_west_boundaries FAILED [ 66%]
    tests/test_history_date_clock_readers.py::TestHistoryDateClockReadersTimezoneInvariance::test_age_marker_injectable_today_seam FAILED [100%]

    =================================== FAILURES ===================================
    _ TestHistoryDateClockReadersTimezoneInvariance.test_timezone_invariance_east_and_west_boundaries _
    ...
    >           self.assertEqual(
                    east_verdict,
                    expected_verdict,
                    f"[{label}] East timezone XXX-20 (UTC+20) verdict {east_verdict!r} != expected {expected_verdict!r} for date {hist_date}",
                )
    E           AssertionError: '!' != ''
    E           - !
    E            : [boundary_30d_recent] East timezone XXX-20 (UTC+20) verdict '!' != expected '' for date 2026-09-03
    ----------------------------- Captured stdout call -----------------------------

    [Skew Window Observation] UTC: 2026-10-03, East (XXX-20, UTC+20): 2026-10-04, West (XXX+12, UTC-12): 2026-10-02
    =========================== short test summary info ============================
    FAILED tests/test_history_date_clock_readers.py::TestHistoryDateClockReadersTimezoneInvariance::test_timezone_invariance_east_and_west_boundaries
    FAILED tests/test_history_date_clock_readers.py::TestHistoryDateClockReadersTimezoneInvariance::test_age_marker_injectable_today_seam
    ========================= 2 failed, 1 passed in 3.95s ==========================
    ```

    Passing run after fix:
    ```
    $ python3 -m pytest tests/test_history_date_clock_readers.py -o addopts="" -v -s
    collected 3 items

    tests/test_history_date_clock_readers.py::TestHistoryDateClockReadersTimezoneInvariance::test_age_marker_injectable_today_seam PASSED
    tests/test_history_date_clock_readers.py::TestHistoryDateClockReadersTimezoneInvariance::test_age_marker_edge_cases_and_historyless_trees PASSED
    tests/test_history_date_clock_readers.py::TestHistoryDateClockReadersTimezoneInvariance::test_timezone_invariance_east_and_west_boundaries
    [Skew Window Observation] UTC: 2026-10-03, East (XXX-20, UTC+20): 2026-10-04, West (XXX+12, UTC-12): 2026-10-02
    PASSED

    ============================== 3 passed in 17.09s ==============================
    ```

    Timezones:
    - East of UTC: `XXX-20` (UTC+20, POSIX offset -20 hours -> local time is UTC + 20 hours). Observed local date: 2026-10-04 vs UTC 2026-10-03.
    - West of UTC: `XXX+12` (UTC-12, POSIX offset +12 hours -> local time is UTC - 12 hours). Observed local date: 2026-10-02 vs UTC 2026-10-03.
    Skew window: Confirmed inside skew window (East observed 2026-10-04, West observed 2026-10-02, UTC observed 2026-10-03; assertion passed).
    Environment isolation: `TZ` set strictly in `subprocess.run(..., env={...})` environments. No in-worker `time.tzset()` or `os.environ` modification in pytest worker process.
    P16 compliance: Zero calls to `inspect`, zero reads of production source code or AST, zero assertions on code structure or symbol names. Asserts strictly on returned marker string and behavior.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `git diff agent_workflows/attention.py`, showing the UTC reference date, the injectable `today` parameter, and the corrected docstring naming the clock and citing `2vev8j` 4.4; the old "Deterministic: compares ISO dates only" sentence must be gone. Plus THE REAL-CORPUS INVARIANCE CHECK: the replay over every `aw attention --all --format json` item under `TZ=UTC` and a timezone east of UTC, pasted, reporting a NONZERO re-derived count of flipping items at base and ZERO after. Plus THE NO-POLICY-CHANGE CHECK: the before/after diff of all `(path, marker)` pairs at a fixed `TZ=UTC`, with every difference shown to be inside the boundary cohort. Plus `AW_NO_REEXEC=1 aw attention` rendering a board without error, proving both call sites (`attention._render_item_row` and the `cli` board renderer) still work with the defaulted parameter. Plus `tests/test_attention.py` and `tests/test_attention_contract.py` results.
  - Observed evidence:
    `git diff agent_workflows/attention.py`:
    ```diff
    diff --git a/agent_workflows/attention.py b/agent_workflows/attention.py
    index 2248b56b4..300758f06 100644
    --- a/agent_workflows/attention.py
    +++ b/agent_workflows/attention.py
    @@ -20,6 +20,7 @@ import json
     import os
     import re
     import sys
    +from datetime import date, datetime, timezone
     from pathlib import Path
     from typing import (
         Any,
    @@ -2452,17 +2453,20 @@ def _common_dir_prefix(paths: List[str]) -> str:
     _HISTORYLESS_TREES = {"actions", "research"}


    -def _age_marker(last_history_at: Optional[str], tree: str = "") -> str:
    +def _age_marker(
    +    last_history_at: Optional[str],
    +    tree: str = "",
    +    today: Optional[date] = None,
    +) -> str:
         """awdoctor Order 01 + awdoctorfix Order 03: a compact staleness marker from last_history_at.
         '!' when older than ~30 days, '?' when unknown (None) EXCEPT on a history-less tree (returns ''),
    -    else '' (recent). Deterministic: compares ISO dates only."""
    +    else '' (recent). Reads the UTC clock per spec 2vev8j Section 4.4 so verdicts are invariant under reader timezone."""
         if last_history_at is None:
             return "" if tree in _HISTORYLESS_TREES else "?"
         try:
    -        from datetime import date
    -
    +        ref_date = today if today is not None else datetime.now(timezone.utc).date()
             y, m, d = (int(x) for x in last_history_at.split("-")[:3])
    -        age_days = (date.today() - date(y, m, d)).days
    +        age_days = (ref_date - date(y, m, d)).days
             return "!" if age_days > 30 else ""
         except (ValueError, TypeError):
             return "?"
    ```
    The old "Deterministic: compares ISO dates only" sentence is removed, replaced with explicit documentation that the function reads the UTC clock per spec `2vev8j` Section 4.4 so verdicts are invariant under reader timezone.

    Real-corpus invariance check:
    Replaying `_age_marker` over all 2382 items from `aw attention --all --format json` under `TZ=UTC` vs `TZ=XXX-20` (east of UTC) and `TZ=XXX+12` (west of UTC):
    - At base:
      `Diff UTC vs XXX-20 count: 5` (items stamped `2026-09-03` flipped from `''` to `'!'`)
      `Diff UTC vs XXX+12 count: 10` (items stamped `2026-09-02` flipped from `'!'` to `''`)
    - After fix:
      `Diff UTC vs XXX-20 count: 0`
      `Diff UTC vs XXX+12 count: 0`
    Zero items flip verdict across timezones after the fix.

    Real-corpus no-policy-change check:
    Diff of all `(path, marker)` pairs at fixed `TZ=UTC` across all 2382 items before and after fix:
    - `Diff under fixed TZ=UTC count: 0` (0 items change verdict).

    Board rendering check:
    `PYTHONPATH=. AW_NO_REEXEC=1 aw attention | head -n 35` rendered the attention board without error, confirming both call sites (`attention._render_item_row` and `cli.py` board renderer) work with the defaulted parameter.

    Test results:
    - `python3 -m pytest tests/test_attention.py tests/test_attention_contract.py`:
      `92 passed in 41.87s`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the full census table (every remaining `date.today()`/`datetime.now()`-class call in `agent_workflows/`), each row carrying the site, a READER/WRITER/NEITHER verdict, THE CLOCK OF ITS OTHER OPERAND, and a convert-or-leave decision with its reason; plus the exact command used to enumerate the sites so the census is reproducible. An explicit statement that no reader remains comparing a UTC-stamped value against a local today. An explicit row for `plans_archive._age_days`, `research_archive._age_days` and `workflow_artifacts_prune._calculate_run_age` recording them as correctly LOCAL with their stored operand named (F-07, PR-001), and confirmation via `tests/test_plans_archive.py`, `tests/test_workflow_artifacts_prune.py` and `git diff --name-only` that they were not changed. A statement naming which sibling writer plans (`5ivkdh`, `9wcei0`, `rfyrvp`, `dmrbqa`) were `executed` at audit time, since an executed one can move a stored value's clock and invalidate a row. Plus the bare-suite `N passed` line, and `aw check` / `aw attention --check` before-and-after finding sets showing no new finding.
  - Observed evidence:
    Enumeration command:
    `git grep -n -E "(today\(\)|now\(|fromtimestamp\()" agent_workflows/`
    Filtered for local-clock calls (excluding monotonic elapsed timers and explicit `timezone.utc` calls).

    Full census table:
    | Site | Verdict | Other Operand Clock | Decision | Reason |
    |---|---|---|---|---|
    | `agent_workflows/agy_sessions.py:173, 177, 183` (`fromtimestamp(...).astimezone()`) | NEITHER | None (display helper) | Leave | Epoch second conversion to local timezone for Antigravity session viewer display. No date comparison. |
    | `agent_workflows/artifact_adopt.py:771` (`date.today().strftime("%Y%m%d")`) | WRITER | None (file name) | Leave | Generates filename prefix date for adopted artifact. Governed by DECISIONS.md D55 (local time). |
    | `agent_workflows/backlog.py:1233` (`datetime.date.today().strftime("%Y%m%d")`) | WRITER | None (file name) | Leave | Generates filename prefix date for new backlog item. Governed by DECISIONS.md D55 (local time). |
    | `agent_workflows/contention_wait.py:61, 69, 77, 82` (`now()` / `time.monotonic`) | NEITHER | Monotonic float | Leave | Bounded wait timeout using monotonic clock. Not a calendar date. |
    | `agent_workflows/engine.py:474, 483` (`datetime.now().strftime(...)`) | WRITER | None (dir name) | Leave | Generates local backup directory name. Governed by DECISIONS.md D55. |
    | `agent_workflows/ipd_authoring.py:495` (`date.today().strftime("%Y-%m-%d")`) | WRITER | None (frontmatter) | Leave | Mints plan `- Date:` frontmatter. Governed by DECISIONS.md D55 (local time). |
    | `agent_workflows/ipd_authoring.py:543` (`date.today().strftime("%Y%m%d")`) | WRITER | None (file name) | Leave | Mints plan filename date prefix. Governed by DECISIONS.md D55 (local time). |
    | `agent_workflows/plans_archive.py:198` (`t = today or date.today()`) | READER | LOCAL (`_plan_date` from `- Date:` or filename) | Leave | Both operands are LOCAL per DECISIONS.md D55. Converting today to UTC would create an off-by-one mixed-clock defect. |
    | `agent_workflows/prompts.py:95, 385` (`_now().date().isoformat()`) | WRITER | None (frontmatter/file) | Leave | Mints prompt `- Date:` and filename date prefix. Governed by DECISIONS.md D55. |
    | `agent_workflows/record_history.py:64, 228` (`_date.today().strftime("%Y%m%d")`) | WRITER | None (sidecar record) | Leave | Activity log sidecar record stamping. Owned by pending plan `dmrbqa` (backlog `tl8qmc`). |
    | `agent_workflows/releases.py:83` (`date.today().strftime("%Y%m%d")`) | WRITER | None (file name) | Leave | Mints release filename prefix date. Governed by DECISIONS.md D55. (History date already moved to UTC by `5ivkdh`). |
    | `agent_workflows/research_archive.py:291` (`t = today or date.today()`) | READER | LOCAL (doc `created` field) | Leave | Both operands are LOCAL per DECISIONS.md D55. Converting today to UTC would create a mixed-clock error. |
    | `agent_workflows/research_cmd.py:201, 259` (`date.today().strftime("%Y%m%d")`) | WRITER | None (frontmatter/file) | Leave | Mints research document filename and created field. Governed by DECISIONS.md D55. |
    | `agent_workflows/research_refs.py:456` (`date.today().strftime("%Y%m%d")`) | WRITER | None (file name) | Leave | Mints research document filename prefix. Governed by DECISIONS.md D55. |
    | `agent_workflows/set_records.py:176, 267, 348` (`datetime.date.today()`) | WRITER | None (metadata/file) | Leave | Mints walkthrough Date and filename, and promoted backlog item filename. Governed by DECISIONS.md D55. |
    | `agent_workflows/specs.py:559, 1423` (`_today() = datetime.date.today().isoformat()`) | WRITER | None (file name) | Leave | Mints spec filename date prefix. Governed by DECISIONS.md D55. (History record already moved to UTC by `5ivkdh`). |
    | `agent_workflows/storage.py:347, 390` (`datetime.now().isoformat()`) | WRITER | None (metadata) | Leave | Local machine companion directory metadata timestamps. Governed by DECISIONS.md D55. |
    | `agent_workflows/upgrade_rehearsal.py:435, 748, 971` (`datetime.now()`) | WRITER | None (sandbox artifact) | Leave | Mints sandbox directory names and probe markers on disposable copies. |
    | `agent_workflows/workflow_artifacts_prune.py:127, 200` (`datetime.date.today()`) | READER | LOCAL (`_parse_run_date` leading `YYYYMMDD` or mtime) | Leave | Both operands are LOCAL per DECISIONS.md D55 and filesystem mtime. PR-001 confirmed leave. |
    | `agent_workflows/attention.py:2467` (`today or datetime.now(timezone.utc).date()`) | READER | UTC (`last_history_at` from `## Workflow history`) | Converted | Reader now uses UTC clock matching `last_history_at` governed by spec 2vev8j Section 4.4. Fixed in E-02. |

    Statement on readers: No reader remains in `agent_workflows/` comparing a UTC-stamped value against a local today.
    D55 readers unchanged:
    - `plans_archive._age_days`, `research_archive._age_days`, and `workflow_artifacts_prune._calculate_run_age` are confirmed correctly LOCAL with their stored operands named above.
    - Verified via `tests/test_plans_archive.py` and `tests/test_workflow_artifacts_prune.py`: `39 passed in 16.76s`.
    - `git diff --name-only` confirms neither file was modified.
    Sibling plans status at audit time:
    - `5ivkdh`: executed (.aw/records/plans/executed/20261001-7qvs1c-01-5ivkdh-unify-every-artifact-history-date-onto-the-utc-clock-ruled-b.ipd.md)
    - `9wcei0`: approved (.aw/records/plans/pending/20261002-jvw1kg-01-9wcei0-stamp-the-scaffold-s-draft-history-record-from-the-utc-clock.ipd.md)
    - `rfyrvp`: superseded (.aw/records/plans/superseded/20261002-lq2w86-01-rfyrvp-put-the-plan-family-created-record-on-the-utc-history-clock.ipd.md)
    - `dmrbqa`: to-review (.aw/records/plans/pending/20261002-tl8qmc-01-dmrbqa-put-the-gitignored-history-sidecar-on-the-utc-clock-so-one-e.ipd.md)
    Suite and health checks:
    - Bare suite `python3 -m pytest`: `1 failed, 4830 passed, 2 skipped, 3 warnings in 444.51s (0:07:24)`. Pre-existing failure: `tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta`.
    - `AW_NO_REEXEC=1 aw check`: Finding set unchanged from baseline.
    - `AW_NO_REEXEC=1 aw attention --check`: Finding set unchanged from baseline (`aw/lane/76ic0k: attention.lane-stranded`).
    - `AW_NO_REEXEC=1 aw sanitize --agent`: Clean (0 findings, exit 0).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries no `- Readiness:` field: that field is an OUTPUT of `/plan-review`
and writing one here would forge a review that has not happened. It requires explicit human approval
before execution.

WHAT THE HUMAN IS APPROVING, in one paragraph. Backlog `doe2fo` is the ninth filing of one defect, and
its headline (the backlog setter's local-clock history date) is genuinely a duplicate that eight plans
already own; `qjm4bg` is right to list it for closure. What this plan carries is the slice that census
missed: every one of those eight plans fixes a WRITER, and two READERS compare a UTC-stamped value
against a local `today`. That is measured, not argued: ten live artifacts in the real corpus carry two
contradictory staleness verdicts at the same instant, (a second, run-age claim was withdrawn at review,
PR-001). Three judgements are being approved. FIRST, that the
correct rule is per-site (match the clock of the value compared against) rather than global, which is
why three OTHER age readers are deliberately left LOCAL and why "unify every date onto UTC" would break
them. SECOND, that this plan takes NO dependency on the four writer plans, because a like-for-like
comparison is correct whichever order they land in. THIRD, that the 30-day threshold is
untouched, so any verdict that moves must be inside the boundary cohort, and V-02
proves that on the real tree. The honest limits are that OQ-02 leaves a spec-wording question with the
maintainer rather than amending an approved contract, and that E-04's census is a search and so a
completeness claim only as strong as its reproducible command.

Execution contract: commit ONLY the files this plan changed, limited to its `Scope-Paths`, through
`aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push.
Verify the staged set with `git diff --cached --name-only` before each commit and unstage anything
not this plan's with `git restore --staged <path>`; this is a shared checkout and another agent's
uncommitted work must never enter a commit here.

Validation is not optional and not inferable: every `V-*` item demands pasted output from a command
actually run. In particular, a claim that the fix works is NOT acceptable on a green suite alone,
because the suite is green at base while both defects are live (F-04). The new guard MUST be
demonstrated failing before the fix, and the real-corpus invariance check MUST be shown going from
a nonzero count of flipping items to zero.

DO NOT WRITE A STATUS ONTO `doe2fo`. The runner sets it `graduated` on the `From-Backlog` handoff;
writing one here would forge a transition this plan does not perform.

Post-gate lifecycle: run `aw ipd begin` before implementing. On completion, run `aw ipd lint --phase
pre-transition` to conforming. The terminal transition is MANDATORY and its owner is conditional: when
this plan is dispatched by `aw oc run` / `aw agy run`, the runner performs the finalize (path-scoped
commit and move to `.aw/records/plans/executed/`) after its merge-and-revalidate gate, so the executor
must NOT run `aw ipd finalize` itself; when executed by hand, the executor runs `aw ipd finalize`.
Never hand-`git mv` the file or hand-edit the terminal state. Scope-Paths is a DECLARATION the
finalize gate reconciles: an out-of-scope edit that proves necessary is made and justified with
`--scope-reason`, a declared-but-unmodified path with `--scope-ack`. Backlog item `doe2fo` is handed off via `- From-Backlog:` and should reach
`graduated`, not `done`: this plan carries its `- Blocks-Release: next` gate, and the gate is
released only when this plan is `executed`.
