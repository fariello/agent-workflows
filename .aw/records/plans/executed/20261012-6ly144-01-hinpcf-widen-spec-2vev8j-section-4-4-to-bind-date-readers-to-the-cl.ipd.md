# IPD: Widen spec 2vev8j Section 4.4 to bind date READERS to the clock of the value they compare against

- Date: 2026-10-12
- Kind: child
- Concern: Spec `2vev8j` Section 4.4 ("One timezone for every writer") binds only WRITERS ("Every writer, tool and human-facing helper alike, records UTC; local time is a RENDER-TIME concern only"). It says nothing about code that COMPARES a stored date against "today", so the reader rule that executed plan `840y6i` had to derive (a reader must use the clock of the value it compares against) lives only in that plan's prose (`840y6i` OQ-01, F-07, E-04 table). That gap is not hypothetical: `840y6i` F-01 measured TEN live artifacts carrying two contradictory staleness verdicts at the same instant because `attention._age_marker` compared a UTC history date against a local `date.today()`, and its own review (PR-001) caught a near-miss in the opposite direction, where the obvious "unify every reader onto UTC" reading would have put a mixed-clock error into the `workflow_artifacts_prune` DELETION planner. The literal 4.4 sentence "local time is a RENDER-TIME concern only" reads as license for exactly that mistake, because the three correctly-LOCAL readers (`plans_archive._age_days`, `research_archive._age_days`, `workflow_artifacts_prune._calculate_run_age`) compare against values `DECISIONS.md` D55 rules LOCAL. Backlog `6ly144` (raised as `840y6i` OQ-02) asks whether the contract should state the invariant once.
- Scope: IN: re-derive the census of every date-comparing READER in `agent_workflows/` with its stored operand's clock, so the amendment is written against the tree as it is at execution and not against `840y6i`'s 2026-10-02 snapshot; add one behavioral test module asserting the invariant on the four known readers under two always-skewed timezones, including a negative control proving the test can see a mixed-clock pairing; amend spec `2vev8j` Section 4.4 by APPENDING a reader paragraph (the heading and the existing writer sentence are left byte-unchanged, because three test modules quote the heading text "One timezone for every writer" and others cite "2vev8j 4.4"); record the amendment in the spec's `## Workflow history` with `aw specs note`. OUT, each with a reason under "Deferred": converting or otherwise editing any reader or writer (none is wrong at authoring, measured below); `DECISIONS.md` D55 (its scope is human-facing NAMES and needs no change for readers to follow it); re-approving the spec or writing any approval attestation; the per-artifact journal migration the spec itself specifies; closing the backlog item (the runner sets `graduated`).
- Scope-Paths: .aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md, tests/test_date_reader_clock_parity.py, .aw/records/plans/pending/20261012-6ly144-01-hinpcf-widen-spec-2vev8j-section-4-4-to-bind-date-readers-to-the-cl.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: 6ly144
- From-Spec: 2vev8j
- Set: 6ly144
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: hinpcf

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: hinpcf verified (set 6ly144, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog `6ly144` (OQ-02 of executed `840y6i`). The item is a CONTRACT-WORDING question, so this plan PROPOSES a concrete amendment and the maintainer's approval of this plan is the ruling; declining it means retiring the plan to `not-executed`, which leaves today's correct code untouched. Measured at authoring in this lane: under `TZ=XXX-24` a just-minted LOCAL date `20261013` gives `plans_archive._age_days`=0.0 and `research_archive._age_days`=0.0, and the UTC history date `2026-10-12` gives `attention._age_marker`='' (recent), while the MIXED pairing (local today minus UTC history date) is 1 day; under `TZ=XXX+23:59` the mixed pairing is -1 day. So every known reader already matches its operand's clock and the amendment codifies rather than changes behavior. No pending plan scopes the spec file (grep of `.aw/records/plans/pending/` for the spec path: only this plan). Backlog item carries no `- Blocks-Release:`; none is invented.

## Goal

State once, in the approved contract that every history-clock plan is reviewed against, that a date READER must compute "today" on the SAME clock that wrote the stored value it compares against, so the three deliberately-LOCAL readers and the one UTC reader follow from spec `2vev8j` rather than from one executed plan's prose. Back the sentence with a behavioral test so the invariant is checkable, not merely asserted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-derive the reader census the amendment is written against

- [x] E-01 Record a baseline and re-derive the READER census at your own execution HEAD before any edit. Run the bare suite (`python3 -m pytest`) and record the FAILURE SET by node id (not only counts; the suite drifts), plus `aw specs check` on the spec and `aw check` finding sets. Then enumerate candidate date calls with `git grep -n -E "(today\(\)|now\(|fromtimestamp\()" agent_workflows/` (250 raw hits at authoring, most of them writers, timers or display) and narrow to READERS, meaning a site whose result is SUBTRACTED FROM or COMPARED WITH a stored date (age, staleness, retention, sweep). For each reader record: site by symbol, the stored operand and where it is minted, that operand's ruled clock (UTC per `2vev8j` 4.4 for `## Workflow history`/journal dates; LOCAL per `DECISIONS.md` D55 for filename prefixes, `- Date:`/`created` front matter, workflow-artifacts RUN_IDs), the reader's own clock, and MATCH or MISMATCH. Re-confirm, rather than trust, the four rows `840y6i` E-04 recorded (`attention._age_marker` UTC; `plans_archive._age_days`, `research_archive._age_days`, `workflow_artifacts_prune._calculate_run_age` LOCAL). If a MISMATCH reader is found, do NOT fix it here (outside `- Scope-Paths:`): file it with `aw backlog new --work-kind bug` carrying `--blocks-release next` per the AGENTS.md release-gate rule, cite the new id6 in the table, and still name it in E-03's paragraph only as a known exception with that id6.
  - Depends on: none
  - Expected outcome: the baseline failure set and check findings recorded; a reader table (one row per reader site) with operand, operand clock, reader clock and MATCH/MISMATCH; the enumeration command recorded so the census is reproducible; any MISMATCH filed as a gated bug with its id6.
  - Execution state: performed

### Task group 2: make the invariant checkable

- [x] E-02 Create `tests/test_date_reader_clock_parity.py`, a behavioral test that a value minted by a real writer and read back by its reader has age ZERO under a timezone in which the local and UTC dates differ. Run every case in a CHILD process (`subprocess.run([sys.executable, "-c", ...], env=...)`) whose env sets `TZ`, `AW_NO_REEXEC=1`, and `PYTHONPATH` with the repository root PREPENDED, the shape `tests/test_history_date_clock_readers.py._run_in_subprocess` uses, so the pytest worker's process-global time state is never mutated under xdist. Use the two always-skewed POSIX zones `tests/test_scaffold_history_clock.py` established, `XXX-24` (local always one day ahead of UTC) and `XXX+23:59` (behind except in the final UTC minute), and in each child first assert the precondition that `date.today()` differs from the UTC date, so a non-skewed run fails loudly rather than passing vacuously. Cases, each parameterized over both zones: (a) UTC operand: `artifact_core.utc_history_date()` read by `attention._age_marker(value, "plans")` returns `''`, AND a BOUNDARY history date where the clock decides the verdict returns the UTC-correct marker: under `XXX-24` a history date 30 days before the UTC today gives `''` (with a LOCAL today it would be `'!'`), and under `XXX+23:59` a date 31 days before the UTC today gives `'!'` (with a LOCAL today it would be `''`) (measured at review, F-06). A fresh date alone cannot discriminate, because `_age_marker` returns `''` for an age of 0 and of plus or minus 1 alike; (b) LOCAL plan operand: a plan scaffolded with `aw ipd scaffold --kind child --title x --set xset --order 1 --author probe --priority low --work-kind chore --apply` (CLI subprocess in a temp repo with `.aw/config/project.json` and a `pending/` dir, as `tests/test_scaffold_history_clock.py._setup_repo` builds; every one of those flags is required, and there is no `--slug`, measured at review) has its date resolved by `plans_archive._resolve_plan_date(name, text)` and `plans_archive._age_days(...)` returns `0.0`; (c) LOCAL research operand: a doc written by `aw research new --kind finding --slug probe-x --apply` in a temp repo, with `HOME` and `XDG_CONFIG_HOME` pointed into the test's temp dir (as `tests/test_research_date_containment.py` does), because with a real HOME the doc is written OUT OF TREE under `~/.aw/projects/<slug>/records/research/` (measured at review, F-06), which would both pollute the user's home and miss the file; locate the written doc from the command's `wrote <path>` stdout line, and read its front-matter `created` and `research_archive._age_days(created)` returns `0.0`; (d) NEGATIVE CONTROL, driven THROUGH the readers' own `today` seams so it exercises the same code as (a) to (c): `attention._age_marker(boundary_date, "plans", today=<LOCAL today>)` returns the OPPOSITE marker from case (a)'s boundary assertion, and `plans_archive._age_days(plan_date, today=<UTC today>)` and `research_archive._age_days(created, today=<UTC today>)` are NONZERO (measured `-1.0` east and `1.0` west for the plan). This proves the cases above would see a clock mismatch. Every assertion is on a returned value from calling the code; no source reading, `inspect`, `ast`, or text matching against production modules. `workflow_artifacts_prune._calculate_run_age` is covered by E-01's census row rather than here, because its LOCAL RUN_ID operand is minted by the workflow-artifacts protocol, not by a callable writer this test can drive.
  - Depends on: E-01
  - Expected outcome: the new module exists, every case passes at execution HEAD (the readers already match, measured at authoring), and the negative control demonstrates nonzero mixed-clock ages; running it with `python3 -m pytest tests/test_date_reader_clock_parity.py -o addopts=""` reports the per-case counts.
  - Execution state: performed

### Task group 3: amend the contract

- [x] E-03 Amend spec `2vev8j` Section 4.4 by APPENDING one paragraph after the existing writer sentence, leaving the heading `### 4.4 One timezone for every writer` and the existing paragraph byte-unchanged (three test modules quote that heading and more cite "2vev8j 4.4"; renaming it would orphan those citations). Use this text, substituting the execution date and adjusting the reader list ONLY if E-01's census differs from authoring:

      READERS ARE BOUND TOO, BY THE CLOCK OF THEIR STORED OPERAND (amended YYYY-MM-DD by plan `hinpcf`,
      backlog `6ly144`). Any code that compares a stored date against "today" (an age, staleness,
      retention or sweep computation) MUST compute today on the SAME clock that wrote the stored value:
      a date this section rules UTC (a `## Workflow history` or journal date) is compared against a UTC
      today, and a date minted on the LOCAL clock (a filename date prefix or workflow-artifacts RUN_ID, which
      `DECISIONS.md` D55 rules LOCAL, and the `- Date:` and `created` front-matter dates the same
      writers stamp beside those names) is compared against a LOCAL today. A reader does
      NOT adopt UTC by default: "local time is a RENDER-TIME concern" governs DISPLAY, not comparison,
      and converting a LOCAL-operand reader to UTC introduces the very mixed-clock error this rule
      prevents. Motivation, measured: plan `840y6i` F-01 found ten live artifacts whose staleness
      verdict flipped with the reader's timezone because `attention._age_marker` compared a UTC history
      date against a local today. Under this rule `attention._age_marker` reads UTC, while
      `plans_archive._age_days`, `research_archive._age_days` and
      `workflow_artifacts_prune._calculate_run_age` correctly read LOCAL. A reader whose stored operand
      has no ruled clock must be given one before it may compare. Guarded by
      `tests/test_date_reader_clock_parity.py`.

  Do NOT touch any other section, the front matter, `- Status:`, C1-C8, or any acceptance criterion.
  - Depends on: E-02
  - Expected outcome: `git diff` of the spec shows only added lines inside Section 4.4, after the existing paragraph and before `### 4.5`; heading and prior paragraph unchanged.
  - Execution state: performed

- [x] E-04 Record the amendment in the spec's `## Workflow history` through the tool, with `aw specs note .aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md --message "amend Section 4.4: bind date readers to the clock of their stored operand (IPD hinpcf, backlog 6ly144)"`. Do NOT use `aw specs set ... --by-human` and do NOT write any approval attestation: the spec stays `approved` on its existing attestation, and the maintainer's approval of THIS plan is the ruling. Then run `aw specs check` and `aw check` and compare finding sets against E-01's baseline.
  - Depends on: E-03
  - Expected outcome: a new `note (aw specs)` line in the spec's history; `aw specs check` reports the spec conforms; `aw check` shows no finding absent from the E-01 baseline.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Spec `2vev8j` Section 4.4, verbatim: "Every writer, tool and human-facing helper alike, records UTC; local time is a RENDER-TIME concern only." `- Status: approved`, human-attested (`- 2026-09-09 approved (aw set, --by-human)`).
- `DECISIONS.md` D55 ("Human-facing timestamps use LOCAL time, not UTC"): covers plan/walkthrough filenames and `workflow-artifacts/` RUN_IDs (`YYYYMMDD-HHMMSS`); D55 is scoped to NAMES and is silent on comparison.
- A spec amendment carried by a plan is precedented: executed plan `ulepef` E-05 amended `2vev8j` Section 7 and declared the spec in `- Scope-Paths:`. That plan recorded via `aw specs set approved --by-human`; this plan deliberately uses `aw specs note` instead, because it was not given a fresh human attestation to record and writing one would forge it (AGENTS.md "NEVER WRITE ANOTHER ROLE'S ATTESTATION FIELD").
- Correct beside a dated record, never over it: the amendment is APPENDED and carries its own date and carrier, matching how `ulepef` corrected Section 7.
- Timezone tests run in child processes with `TZ` set (`tests/test_history_date_clock_readers.py._run_in_subprocess`) or with a strictly-restored `time.tzset()` context (`tests/test_scaffold_history_clock.temporary_timezone`); the always-skewed zones `XXX-24`/`XXX+23:59` come from `tests/test_scaffold_history_clock.ScaffoldHistoryClockTests.EAST_TZ`/`WEST_TZ`.
- `artifact_core.utc_history_date` is the single UTC history-date minter (its docstring cites 4.4 as authority).
- Run the suite BARE (`python3 -m pytest`); use `-o addopts=""` only to read per-test counts of a narrowed run.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence | Consequence |
|---|---|---|---|
| F-01 | 4.4 binds writers only; the reader rule exists only in executed plan prose. | Spec text above; `840y6i` OQ-01 ("a reader must use THE CLOCK OF THE VALUE IT COMPARES AGAINST") and OQ-02 (deferred this question). | A future reader author reviewing against the spec alone has no rule, and the literal "RENDER-TIME concern only" invites the wrong one. |
| F-02 | The wrong reading has already nearly shipped once. | `840y6i` review PR-001: the original E-03 would have converted `workflow_artifacts_prune`'s LOCAL-operand reader to UTC, putting a mixed-clock error into a deletion planner. | The amendment must state BOTH directions, not "readers use UTC". |
| F-03 | Every known reader already matches its operand's clock; the amendment codifies, it does not change behavior. | Probe at authoring in this lane under `TZ=XXX-24`: local `20261013`, UTC history `2026-10-12`, `plans_archive._age_days`=0.0, `research_archive._age_days`=0.0, `_age_marker`=''; mixed pairing 1 day. Under `XXX+23:59`: local `20261011`, mixed pairing -1. | No code edit is in scope; the test passes at base and its negative control is what proves it is not vacuous. |
| F-04 | The heading text is quoted by tests. | `git grep -l "One timezone for every writer" tests/`: `test_history_date_clock.py`, `test_history_date_clock_parity.py`, `test_history_date_clock_sidecar.py`; plus "2vev8j 4.4" comment cites in `test_backlog.py`, `test_backlog_history_dedup_parity.py`. | Append a paragraph; do not retitle 4.4. |
| F-06 | (Review, 2026-10-12) The E-02 cases are reachable as specified once the argv and HOME are fixed, and only a BOUNDARY date discriminates the UTC reader. | Scratch probe, deleted. Under `XXX-24`: `_age_marker('2026-09-12','plans')`=`''`, and with `today=<local>` it is `'!'`; scaffold `20261013-xset-01-...` resolved `20261013`, `_age_days`=0.0, and with `today=<utc>` it is -1.0; research `created: 20261013`, age 0.0. Under `XXX+23:59`: `_age_marker('2026-09-11')`=`'!'`, and with a local today it is `''`; plan 0.0 / 1.0; research 0.0. `aw ipd scaffold` refused without `--kind/--order`, then `--author`, then `--priority/--work-kind`; `aw research new` wrote under `<HOME>/.aw/projects/repo-<hash>/records/research/`. | E-02 corrected: boundary case, the full argv, HOME isolation, and a negative control routed through the reader seams. |
| F-05 | No other pending plan edits the spec. | grep of `.aw/records/plans/pending/` for the spec path at authoring: only this plan; `8chbn9` carries `From-Spec: 2vev8j` but does not scope the file. | `- Item-Dependencies: none`. |

## Proposed changes (ordered, validatable)

1. Baseline and re-derived reader census with operand clocks (E-01).
2. New behavioral test `tests/test_date_reader_clock_parity.py` with a negative control (E-02).
3. Appended reader paragraph in spec `2vev8j` Section 4.4 (E-03).
4. Amendment recorded via `aw specs note`; spec and repo checks clean versus baseline (E-04).

## Deferred / out of scope (with reason)

- Editing any reader or writer: F-03 measured none mismatched; a mismatch found by E-01 is filed as a gated bug, not fixed here.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- `DECISIONS.md` D55: scoped to names; the reader rule references it and needs no change to it.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Re-approving the spec or writing `--by-human`: no fresh attestation was given to record; plan approval is the ruling and `aw specs note` records the edit.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- The journal migration, `seq`, and C5 work in the same spec: owned by `ms06pi` and other plans.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Backlog status: the runner sets `graduated`.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none. Each declared path is edited by a numbered item: the spec (E-03, E-04) and the new test (E-02).
- Under-scope: none known. If E-01 finds a mismatched reader, its fix is deliberately filed elsewhere, and only its id6 enters E-03's text.

## Required tests / validation

- `python3 -m pytest tests/test_date_reader_clock_parity.py -o addopts=""` with every case passing and the negative control asserting nonzero mixed ages (E-02).
- The shipped clock suites, run individually and pasted: `tests/test_history_date_clock.py`, `tests/test_history_date_clock_parity.py`, `tests/test_history_date_clock_readers.py`, `tests/test_history_date_clock_sidecar.py`, `tests/test_scaffold_history_clock.py`, `tests/test_plans_archive.py`, `tests/test_research_archive.py`.
- Bare suite `python3 -m pytest`, failure set compared by node id to E-01's baseline, no new failure.
- `aw specs check` and `aw check` with no finding absent from the baseline (E-04).

## Spec / documentation sync

ONE SPEC FILE IS EDITED AND IT IS DECLARED: `.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md` is in `- Scope-Paths:`. WHY: Section 4.4 is the authority every history-clock plan cites, and it currently binds only writers, so the reader rule two executed plans relied on (`840y6i`, and its review's PR-001 correction) is invisible to the next author. The edit is additive (one appended paragraph) and changes no criterion, acceptance test, or status. No CHANGELOG entry: no user-visible behavior changes (F-03).

## Open questions

### OQ-01: Should 4.4 be widened at all, and in which direction?

- Blocking: no
- Status: resolved
- Owner: plan author (recommendation; the maintainer ratifies it by approving this plan or declines it by retiring the plan)
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE TO A RECOMMENDATION, which the maintainer ratifies or declines by approving or retiring this plan. Options: (a) leave 4.4 as is (cost: the reader rule stays in executed-plan prose, and F-02 shows the wrong reading is the natural one); (b) amend to "readers use UTC" (WRONG: breaks three correct LOCAL readers, F-02/F-03); (c) amend to "a reader uses the clock of its stored operand" (recommended: matches every reader measured, explains both the UTC and LOCAL verdicts, and is reversible as a one-paragraph edit). Chosen: (c). Because amending an approved, human-attested spec is the maintainer's call, the plan carries the exact text in E-03 so approval is an informed ruling; if declined, retire this plan to `not-executed` and no code is affected.

### OQ-02: Must the spec be re-approved after the amendment?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Precedent `ulepef` amended Section 7 of the same spec while it stayed `approved`. This plan records the edit with `aw specs note` rather than `aw specs set approved --by-human`, because writing a human attestation the executor did not receive would forge it; the maintainer's approval of this plan is the attestation of record and is visible in this plan's history.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the pasted bare-suite summary line and failure set by node id at execution HEAD; `aw specs check` and `aw check` output; the exact enumeration command; the full reader table with one row per reader site (symbol, stored operand, operand clock with its authority, reader clock, MATCH/MISMATCH), explicitly including rows for `attention._age_marker`, `plans_archive._age_days`, `research_archive._age_days` and `workflow_artifacts_prune._calculate_run_age`; and either the statement that no MISMATCH reader exists or the id6 of each filed bug with `aw backlog` output showing `- Blocks-Release: next`.
  - Observed evidence:
    1. Bare-suite summary line and failure set by node id at execution HEAD (`5e6a8b13f`):
       ```
       FAILED tests/test_host_capability_extension.py::InspectionVerbTests::test_the_verbs_write_nothing_to_the_repository
       1 failed, 7733 passed, 4 skipped, 3 warnings in 974.29s (0:16:14)
       ```
    2. `aw specs check` baseline output:
       ```
       aw specs check: all specs conform. 40 specs checked.
       aw specs check: all specs conform. 1 specs checked.
       ```
    3. `aw check` baseline findings:
       ```
       AW check  all                                                           90042 ms
       ✗ FINDINGS  112 finding(s) detected across 2790 all
       Evidence
         plans  99   specs  21   prompts  2   research  100   backlog  117   walkthroughs  26   roadmaps  1   comms  1   releases  1   reviews  1025   other  1397
         errors  3   warnings  4   info  105
       ```
    4. Exact date enumeration command:
       `git grep -n -E "(today\(\)|now\(|fromtimestamp\()" agent_workflows/`
       Narrowed via AST analysis to date comparison/subtraction sites.
    5. Reader table:
       | Symbol | Stored Operand | Where Minted | Operand Ruled Clock & Authority | Reader Clock | Match/Mismatch |
       |---|---|---|---|---|---|
       | `agent_workflows.attention._age_marker` | `last_history_at` from `## Workflow history` | `artifact_core.utc_history_date()` / lifecycle writers | UTC per spec `2vev8j` Section 4.4 | UTC (`datetime.now(timezone.utc).date()`) | MATCH |
       | `agent_workflows.plans_archive._age_days` | `plan_date` from `- Date:` or `YYYYMMDD` filename | `aw ipd scaffold` (`ipd_authoring.py`) | LOCAL per `DECISIONS.md` D55 and spec `2vev8j` 4.4 | LOCAL (`date.today()`) | MATCH |
       | `agent_workflows.research_archive._age_days` | `created` from front matter or `YYYYMMDD` filename | `aw research new` (`research_cmd.py:265`) | LOCAL per `DECISIONS.md` D55 / `research_cmd.py` | LOCAL (`date.today()`) | MATCH |
       | `agent_workflows.workflow_artifacts_prune._calculate_run_age` | leading `YYYYMMDD` from `run_id` or fallback `mtime` | Workflow runner (`run_id` format) / filesystem | LOCAL per `DECISIONS.md` D55 / filesystem mtime | LOCAL (`datetime.date.today()`) | MATCH |
    6. Mismatch finding: No MISMATCH reader exists. All four readers match the clock of their stored operand.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted output of `python3 -m pytest tests/test_date_reader_clock_parity.py -o addopts=""` showing every case passing for both `XXX-24` and `XXX+23:59`; the negative-control assertions' observed nonzero mixed-clock ages printed or asserted in the output; and a demonstration that the test can FAIL: temporarily invert one reader's clock in a scratch copy or by passing a `today` on the wrong clock through the reader's `today` seam inside the test run, show the failing assertion, then show the committed file passing. Also paste evidence that the research case wrote its doc under the test's temp `HOME`, not the real one. Confirm by `git diff --name-only` that no `agent_workflows/` file changed.
  - Observed evidence:
    1. Pasted output of `python3 -m pytest tests/test_date_reader_clock_parity.py -o addopts="" -v -s`:
       ```
       tests/test_date_reader_clock_parity.py::TestDateReaderClockParity::test_local_research_operand_west [XXX+23:59] Research doc written under temp isolation: /tmp/test_research_reader_fdp8tnzg/repo/.aw/records/research/20261012-probe-x-01-1uvs2f-probe-x.findings.md
       [XXX+23:59] Research created: 20261012, age: 0.0
       PASSED
       tests/test_date_reader_clock_parity.py::TestDateReaderClockParity::test_negative_control_west [XXX+23:59] Negative control attention: UTC verdict='!' vs mixed=''
       [XXX+23:59] Negative control plan: local age=0.0 vs mixed age=1.0
       [XXX+23:59] Negative control research: local age=0.0 vs mixed age=1.0
       PASSED
       tests/test_date_reader_clock_parity.py::TestDateReaderClockParity::test_local_plan_operand_west [XXX+23:59] Plan scaffold date: 20261012, age: 0.0
       PASSED
       tests/test_date_reader_clock_parity.py::TestDateReaderClockParity::test_utc_operand_east [XXX-24] UTC boundary 30d verdict: '' (correctly recent)
       PASSED
       tests/test_date_reader_clock_parity.py::TestDateReaderClockParity::test_utc_operand_west [XXX+23:59] UTC boundary 31d verdict: '!' (correctly stale)
       PASSED
       tests/test_date_reader_clock_parity.py::TestDateReaderClockParity::test_negative_control_east [XXX-24] Negative control attention: UTC verdict='' vs mixed='!'
       [XXX-24] Negative control plan: local age=0.0 vs mixed age=-1.0
       [XXX-24] Negative control research: local age=0.0 vs mixed age=-1.0
       PASSED
       tests/test_date_reader_clock_parity.py::TestDateReaderClockParity::test_local_plan_operand_east [XXX-24] Plan scaffold date: 20261014, age: 0.0
       PASSED
       tests/test_date_reader_clock_parity.py::TestDateReaderClockParity::test_local_research_operand_east [XXX-24] Research doc written under temp isolation: /tmp/test_research_reader_wiw6i2wi/repo/.aw/records/research/20261014-probe-x-01-bwqxeq-probe-x.findings.md
       [XXX-24] Research created: 20261014, age: 0.0
       PASSED

       ============================== 8 passed in 4.55s ===============================
       ```
    2. Negative control observed nonzero mixed-clock ages:
       - East (`XXX-24`): `attention._age_marker` verdict with `today=local_today` inverted to `'!'` (UTC verdict was `''`); `plans_archive._age_days` with `today=utc_today` was `-1.0` (local age was `0.0`); `research_archive._age_days` with `today=utc_today` was `-1.0` (local age was `0.0`).
       - West (`XXX+23:59`): `attention._age_marker` verdict with `today=local_today` inverted to `''` (UTC verdict was `'!'`); `plans_archive._age_days` with `today=utc_today` was `1.0` (local age was `0.0`); `research_archive._age_days` with `today=utc_today` was `1.0` (local age was `0.0`).
    3. Failure demonstration:
       - Inverted plan reader clock in scratch copy `tests/test_date_reader_clock_parity_fail_demo.py` (`today=utc_today` under `XXX-24`):
         ```
         FAILED tests/test_date_reader_clock_parity_fail_demo.py::TestDateReaderClockParity::test_local_plan_operand_east
         AssertionError: Expected plan age 0.0, got -1.0
         ======================= 1 failed, 7 deselected in 0.73s ========================
         ```
       - Committed file passes: `python3 -m pytest tests/test_date_reader_clock_parity.py -o addopts=""` -> `8 passed in 4.56s`.
    4. Research doc isolation:
       - Output shows docs written to `/tmp/test_research_reader_fdp8tnzg/repo/...` and `/tmp/test_research_reader_wiw6i2wi/repo/...`. Asserted in test that path is relative to test temp dir and does not leak to `~/.aw`.
    5. Confirmed by `git diff --name-only` that no `agent_workflows/` file changed.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the pasted `git diff` of the spec file showing ONLY added lines, all between the existing 4.4 paragraph and `### 4.5`, with the heading line and the existing writer sentence unchanged; the reader list in the added text matching V-01's table.
  - Observed evidence:
    `git diff .aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md`:
    ```diff
    diff --git a/.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md b/.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md
    index 85de02bc4..b08d8d84f 100644
    --- a/.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md
    +++ b/.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md
    @@ -187,6 +187,23 @@ The UTC-versus-local defect (`tk1gqo`'s second defect) is INDEPENDENT and needs
     alone leaves timestamps still claiming an evening action happened tomorrow. Every writer, tool and
     human-facing helper alike, records UTC; local time is a RENDER-TIME concern only.

    +READERS ARE BOUND TOO, BY THE CLOCK OF THEIR STORED OPERAND (amended 2026-10-13 by plan `hinpcf`,
    +backlog `6ly144`). Any code that compares a stored date against "today" (an age, staleness,
    +retention or sweep computation) MUST compute today on the SAME clock that wrote the stored value:
    +a date this section rules UTC (a `## Workflow history` or journal date) is compared against a UTC
    +today, and a date minted on the LOCAL clock (a filename date prefix or workflow-artifacts RUN_ID, which
    +`DECISIONS.md` D55 rules LOCAL, and the `- Date:` and `created` front-matter dates the same
    +writers stamp beside those names) is compared against a LOCAL today. A reader does
    +NOT adopt UTC by default: "local time is a RENDER-TIME concern" governs DISPLAY, not comparison,
    +and converting a LOCAL-operand reader to UTC introduces the very mixed-clock error this rule
    +prevents. Motivation, measured: plan `840y6i` F-01 found ten live artifacts whose staleness
    +verdict flipped with the reader's timezone because `attention._age_marker` compared a UTC history
    +date against a local today. Under this rule `attention._age_marker` reads UTC, while
    +`plans_archive._age_days`, `research_archive._age_days` and
    +`workflow_artifacts_prune._calculate_run_age` correctly read LOCAL. A reader whose stored operand
    +has no ruled clock must be given one before it may compare. Guarded by
    +`tests/test_date_reader_clock_parity.py`.
    +
     ### 4.5 Exactly ONE inline history line remains, as a pure cache

     The reports SPLIT here and this spec settles it. `xn6f6u` and `takpys` say strip the block entirely;
    ```
    Heading line `### 4.4 One timezone for every writer` and existing writer sentence left byte-unchanged; only additions between 4.4 and 4.5; reader list matches V-01.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the pasted `aw specs note` output and the new history line in the spec; `aw specs check` reporting the spec conforms; `aw check` finding set compared to V-01's baseline with no new finding; the seven clock/archive suites listed under "Required tests / validation" run individually with their pasted pass lines; the bare-suite summary line with no failure absent from the baseline; and `git diff --cached --name-only` before the commit listing only the two declared paths plus this plan.
  - Observed evidence:
    1. `aw specs note` output:
       `aw specs note: appended a history record to .aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md`
       New history line in spec:
       `- 2026-10-13 note (aw specs): amend Section 4.4: bind date readers to the clock of their stored operand (IPD hinpcf, backlog 6ly144)`
    2. `aw specs check` output:
       `aw specs check: all specs conform. 1 specs checked.`
       `aw specs check: all specs conform. 40 specs checked.`
    3. `aw check` output compared to baseline:
       `112 finding(s) detected across 2790 all` (errors: 3, warnings: 4, info: 105).
       Identical finding set to baseline; 0 new findings.
    4. Seven clock/archive suites run individually:
       - `python3 -m pytest tests/test_history_date_clock.py -o addopts=""`:
         `5 passed in 7.27s`
       - `python3 -m pytest tests/test_history_date_clock_parity.py -o addopts=""`:
         `6 passed in 14.33s`
       - `python3 -m pytest tests/test_history_date_clock_readers.py -o addopts=""`:
         `3 passed in 3.49s`
       - `python3 -m pytest tests/test_history_date_clock_sidecar.py -o addopts=""`:
         `4 passed in 1.39s`
       - `python3 -m pytest tests/test_scaffold_history_clock.py -o addopts=""`:
         `8 passed in 0.42s`
       - `python3 -m pytest tests/test_plans_archive.py -o addopts=""`:
         `15 passed in 0.44s`
       - `python3 -m pytest tests/test_research_archive.py -o addopts=""`:
         `26 passed in 1.21s`
    5. Bare-suite summary line:
       ```
       FAILED tests/test_host_capability_extension.py::InspectionVerbTests::test_the_verbs_write_nothing_to_the_repository
       1 failed, 7741 passed, 4 skipped, 3 warnings in 774.08s (0:12:54)
       ```
       No new failures; exactly 8 additional tests passed corresponding to the 8 cases in `tests/test_date_reader_clock_parity.py`.
    6. `git diff --cached --name-only` confirmed before commit:
       Lists only the two declared paths plus this plan.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval of this plan, and that approval is also the maintainer's ruling on backlog `6ly144`'s contract question (OQ-01). Execute E-01 through E-04 in order. If the maintainer declines the amendment, retire this plan to `.aw/records/plans/not-executed/` with a `RETIRED` header; no code is affected either way.

Execution contract:
- Scope declaration: `- Scope-Paths:` declares the intended paths. It is a declaration, not a stop condition. An out-of-scope edit that turns out to be genuinely required is made and then justified at finalize with `--scope-reason`. A declared path left unmodified is acknowledged with `--scope-ack`. A MISMATCH reader found by E-01 is filed with `aw backlog new` rather than fixed, per E-01.
- Honesty: you MUST paste the ACTUAL runner output for every test claim. Never claim a pass you did not run.
- Commits: commit only the declared paths through `aw commit hinpcf -- <paths>`. Never use `git add -A`, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize and the move to `executed/`, so do not run `aw ipd finalize` yourself. When executing by hand, finalize through `aw ipd finalize` once `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `Result: pass` with observed evidence. Never hand-roll a `git mv` into `executed/`.
