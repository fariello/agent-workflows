# IPD: Stamp the scaffold's draft history record from the UTC clock so a plan born east of UTC does not fail the lifecycle-transition gate

- Date: 2026-10-02
- Kind: child
- Concern: `ipd_authoring.run_scaffold` stamps a NEW plan's `draft` history record from the LOCAL clock while `status_set.apply_status_change` stamps every later transition in UTC, so for a maintainer EAST of UTC the scaffold's record lands one day AHEAD of its own successor and `check.lifecycle-transition-invalid` fires on a plan nobody mis-authored. Measured end to end in this lane at HEAD `a3ed40a35` under `TZ=XXX-20` (local `2026-10-03`, UTC `2026-10-02`): a real `aw ipd scaffold --apply` followed by a real `aw ipd set to-review` produced `- 2026-10-02 to-review (aw set): to to-review` above `- 2026-10-03 draft (probe): created.`, and `aw check plans --agent` then exited 1 with `recorded lifecycle transition 'to-review' -> 'draft' is invalid: missing predecessor: backwards transition 'to-review' -> 'draft'`. The same two commands under `TZ=Pacific/Honolulu` exit 0, so the gate's verdict depends on the author's timezone rather than on the plan. THIS SITE WAS BELIEVED TO BE IN NO OTHER PLAN'S SCOPE (REVIEW CORRECTION: pending plan `rfyrvp` declares `agent_workflows/ipd_authoring.py` for the same split, and `5ivkdh` now names both; see OQ-03): `5ivkdh` declares `artifact_core.py`, `backlog.py`, `specs.py`, `status_set.py`, `releases.py` and `readiness_recheck.py`, and explicitly classifies `ipd_authoring` as a FILENAME-only site to leave alone ("`ipd_authoring`'s plan `- Date:` and its compact filename date (D55, leave)"); `ayhveg` declares only test files and derives its guard from setter/note verbs, which `aw ipd scaffold` is not.
- Scope: IN: give `ipd_authoring.build_skeleton` a separate history-date input so the `draft` RECORD can be stamped UTC while `- Date:` and the filename stay LOCAL per D55, wire `run_scaffold` to pass both, and add an outcome test that drives the real scaffold-then-transition sequence east of UTC and asserts the lifecycle gate reports clean. OUT, each with a reason recorded under "Deferred": the setter-family clock fix (owned by `5ivkdh`); the cross-spelling timezone guard (owned by `ayhveg`); the duplicate-item convergence (owned by `qjm4bg`); filename and `- Date:` prefixes, which D55 rules LOCAL; `prompts._today_iso`, which feeds no history record; and the direction-classification behavior of `_plan_status_event_groups` itself.
- Scope-Paths: agent_workflows/ipd_authoring.py, tests/test_scaffold_history_clock.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: jvw1kg
- Blocks-Release: next
- Set: jvw1kg
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 9wcei0

## Workflow history
- 2026-10-02 readiness re-check (agent (aw ipd recheck-readiness)): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: unresolved-blocking-question -> clear (no unresolved BLOCKING open question; `has_unresolved_blocking_question` -> False (a NON-blocking open question is deliberately not counted, per the maintainer's 2026-09-10 ruling on qhy3i3 OQ-01)); unresolved-gating-finding -> clear (no unresolved gating finding; `review_findings.subject_gating_blocks` -> empty (an ABSENT review artifact is silent by that predicate's documented contract)); negative-review-verdict -> clear (the newest review record's verdict is not negative; `newest_verdict` -> neutral). RE-CHECKED REVIEW: the review of 2026-10-02, findings PR-001..E-01. Recomputed at HEAD `9b562dc8f`. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-10-02 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: REVIEWED - OPEN QUESTIONS; PR-001, PR-002, PR-003, PR-004, PR-005. Defect re-reproduced at lane HEAD e4dba9b13 under TZ=XXX-20 (check plans rc=1; Honolulu rc=0). PR-001 OPEN: pending plan rfyrvp makes the same ipd_authoring split (escalated as blocking OQ-03). Fixed: always-in-window fixed-offset zones for the guard (PR-002); runnable E-01 scaffold flags and narrowed STOP (PR-003); scope fence + conditional finalize (PR-004); OQ owners (PR-005).

- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `jvw1kg`. The item describes the `backlog.run_set`-versus-`status_set` divergence, which is ALREADY owned by three review-ready plans (`5ivkdh` the production fix, `ayhveg` the guard, `qjm4bg` the duplicate convergence, that last one naming this very item as one of five pure duplicates it closes). Rather than author a ninth copy of the same fix, the authoring turn re-derived the item's own claim and found a SITE OF THE SAME DEFECT that none of the three covers: the `aw ipd scaffold` history writer, which `5ivkdh` deliberately classifies as a filename-only site. Reproduced end to end at HEAD `a3ed40a35` under `TZ=XXX-20`: `aw check plans --agent` exits 1 on a freshly scaffolded, freshly transitioned plan. The proposed fix shape was pre-verified in process (stamping the draft record UTC takes the same fixture from 1 finding to 0). Bare suite baseline at authoring: `3 failed, 4623 passed, 2 skipped` (all three failures pre-existing and in unrelated modules).
- 2026-10-02 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a brand-new plan's recorded `draft` date come from the same clock as every transition that
follows it, so `aw check plans` returns the same verdict for the same plan whatever timezone its
author sits in. Leave the plan's `- Date:` field and its filename prefix on the LOCAL clock, because
a separate and still-current ruling (`DECISIONS.md` D55) deliberately put human-facing names there.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

REVIEW NOTE (2026-10-02, `/plan-review` at lane HEAD `e4dba9b13`): A SECOND PENDING PLAN, `rfyrvp` (`.aw/records/plans/pending/20261002-lq2w86-01-rfyrvp-put-the-plan-family-created-record-on-the-utc-history-clock.ipd.md`, `to-review`, `From-Backlog: lq2w86`, `Blocks-Release: next`, Scope-Paths `agent_workflows/ipd_authoring.py, tests/test_ipd_authoring.py`), was authored 31 minutes BEFORE this one (commit `de75a42c1` 00:32 versus `3f84d12b3` 01:03) and makes the SAME `run_scaffold` clock split in the SAME file. Reviewed plan `5ivkdh` (E-05, and its Deferred carrier row) names BOTH `9wcei0` and `rfyrvp` as owners of this site. The two are not identical: this plan adds an optional `build_skeleton` history-date parameter, the `check plans` verdict assertion and the F-04 three-state narrowness; `rfyrvp` adds a `--path`-branch probe and a per-site date audit of the module. Executing both would apply the split twice. Which plan survives is a scope decision for the maintainer, recorded as OQ-03 (`Blocking: yes`). Neither plan should execute until it is answered.

### Task group 1: reproduce before changing anything

- [ ] E-01 Reproduce the defect THROUGH THE SHIPPED CLI at the executing HEAD, and capture the
  baseline the later items are measured against. This is its own item and it comes first because the
  whole plan rests on a claim about a gate's verdict, and that verdict depends on three things this
  plan does not own (the scaffold, the setter, and the checker's direction classifier), any of which
  a sibling plan may have moved since authoring.

    DRIVE IT, DO NOT READ IT. Run a real `aw ipd scaffold --kind child --title <t> --author <a> --set <s> --order 1 --priority low --work-kind chore --apply` (all of `--author`, `--priority` and `--work-kind` are required, and `--slug` is not a flag; measured at review). Pass the new plan to `aw ipd set to-review` by its `- Id:` and `--no-commit`. Run it as `aw ipd scaffold --kind child ... --apply` and then a real
    `aw ipd set to-review <plan>` inside a throwaway repository, under a timezone EAST of UTC, and
    then run `aw check plans --agent`. Record the two history records verbatim, the filename, and the
    exit code. Do the same under a timezone WEST of UTC to show the verdict differs. Do NOT assert
    that `ipd_authoring` calls `date.today()`; that is a code-structure pin forbidden by
    GUIDING_PRINCIPLES P16 and by the `AGENTS.md` no-code-pinning rule.

    PICK THE EAST TIMEZONE BY ARITHMETIC, NOT BY HABIT. The defect needs local > UTC, and a fixed
    offset is only ahead for `offset` hours of each day, so a zone chosen without checking is green
    most of the day whatever the bug. `Pacific/Kiritimati` (UTC+14) is ahead for 14 of 24 hours and
    is the widest real zone; the POSIX form `XXX-20` (UTC+20) is ahead for 20 of 24 and is what this
    plan's authoring measurement used when the real-zone window happened to be closed. Compute and
    RECORD the local and UTC dates at run time so the evidence proves a skew window was actually
    entered rather than assuming one.

    IF THE REPRODUCTION DOES NOT FIRE, establish WHY before stopping. If `rfyrvp` (or any other plan) has landed the split, record its commit, mark E-02 and E-03 `blocked` with that citation, and still perform E-04, because the guard is additive. If the checker's classifier moved instead, STOP AND REPORT, since the premise is gone. Re-measured at review HEAD `e4dba9b13` under `TZ=XXX-20` (local `2026-10-03`, UTC `2026-10-02`): `.aw/records/plans/pending/20261003-probeset-01-<id6>-probe-plan.ipd.md` with `- 2026-10-02 to-review (aw set)` above `- 2026-10-03 draft (probe): created.` and `aw check plans --agent` rc=1; under `Pacific/Honolulu`, rc=0. So the defect is live at review.
  - Depends on: none
  - Expected outcome: pasted evidence that `aw check plans --agent` exits 1 east of UTC and 0 west of UTC on a plan produced by the real scaffold plus one real transition, with both history records, the filename, the local date and the UTC date recorded for each run; plus the bare-suite baseline at the executing HEAD by FAILURE NAME; no source file changed yet.
  - Execution state: pending

### Task group 2: split the two date roles in the generator

- [ ] E-02 Give `ipd_authoring.build_skeleton` a SECOND, separate date input for the history record,
  defaulting to the existing `when` so every current caller keeps its exact output. The function
  takes one `when` today and spends it in two places with two different governing rulings: the
  `- Date:` metadata field and the `draft` record rendered from
  `_SECTION_BODY[S.H_WORKFLOW_HISTORY]`. Verified in process by pinning `when="1999-12-31"`, which
  came back on exactly those two lines and nowhere else.

    DEFAULT IT TO `when`, WHICH IS WHAT KEEPS THIS SAFE. `tests/test_ipd_templates.py` rebuilds both
    shipped templates by calling `build_skeleton` with a pinned `when` and asserts the result is
    byte-identical to the committed template, and at least nine test modules plus `tests/support.py`
    call the function with a pinned `when`. A required new parameter would break all of them and force
    a template regeneration; an optional one that falls back to `when` changes no existing byte.

    NAME IT FOR ITS ROLE, NOT FOR "TODAY". A bare second date argument is exactly the ambiguity that
    let these two clocks coexist in one value. Name it for the history record it stamps, and document
    on the parameter that the history date is UTC per spec `2vev8j` 4.4 while `- Date:` and the
    filename are LOCAL per `DECISIONS.md` D55, so the next reader does not "simplify" the two back
    into one.
  - Depends on: E-01
  - Expected outcome: `build_skeleton` accepts an optional history-date argument that defaults to `when`; called with only `when` it returns output byte-identical to before (demonstrated against both committed templates); called with both, the `draft` record carries the history date while `- Date:` carries `when`; `tests/test_ipd_templates.py` and `tests/test_ipd_authoring.py` pass with no template regenerated.
  - Execution state: pending

- [ ] E-03 Wire `ipd_authoring.run_scaffold` to pass a UTC history date beside its existing LOCAL
  `when`, and leave BOTH filename sites untouched. This is separate from E-02 because E-02 adds a
  capability that changes no behavior while this item is the actual behavior change, and a reviewer
  must be able to see which one moved the verdict.

    THERE ARE THREE DATE USES IN THIS FUNCTION AND ONLY ONE MOVES. `run_scaffold` computes `when` as
    an ISO local date and separately computes a compact local date for the derived clustered
    filename. The filename date and the `- Date:` field STAY LOCAL under D55; only the value feeding
    the history record becomes UTC. Expect the resulting plan to carry a filename prefix and a `draft`
    record one day apart inside a skew window, and do NOT "fix" that: it is the two rulings composing
    as written, `check_engine._artifact_compact_date` reads the filename and `- Date:`
    interchangeably and compares neither against a history date, and E-04 proves no checker objects.

    REUSE THE SHARED UTC HELPER IF IT EXISTS BY THEN, AND DO NOT AUTHOR A SECOND ONE. Sibling plan
    `5ivkdh` E-01 adds one documented UTC history-date helper to `artifact_core`, which
    `ipd_authoring` already imports, so if it has landed this item is a call to it. If it has not,
    write the UTC expression inline HERE with a comment naming `artifact_core` as its eventual home,
    and say in the evidence which route was taken. Taking an `executed:5ivkdh` dependency instead
    would gate a measured, release-blocking gate failure behind an unrelated plan's review, and the
    two are correct in either order because this plan changes a caller that plan does not declare.
  - Depends on: E-02
  - Expected outcome: a plan produced by the real `aw ipd scaffold --apply` east of UTC carries a UTC `draft` history record beside a LOCAL filename prefix and a LOCAL `- Date:`; the E-01 reproduction now reports `aw check plans --agent` exit 0 east AND west of UTC; the evidence states whether the shared helper was reused or an inline expression was written.
  - Execution state: pending

### Task group 3: pin the property so it cannot silently return

- [ ] E-04 Add a new `tests/test_scaffold_history_clock.py` that drives the real scaffold-then-
  transition sequence under timezones bracketing UTC and asserts the lifecycle gate reports clean,
  and demonstrate it RED at base. A guard never seen failing proves nothing, and that bar is not
  rhetorical here: no test in `tests/` calls `time.tzset()` at all today (measured: zero matches),
  so the suite currently cannot enter a skew window on purpose and measured `4623 passed` while this
  defect was live.

    ASSERT THE CHECKER'S VERDICT, NOT THE DATE STRING ALONE. The user-visible harm is `aw check
    plans` exiting 1, so the assertion is that `check_engine.check_lifecycle_transitions` returns no
    `check.lifecycle-transition-invalid` finding for a plan the tooling itself produced. Also assert
    the UTC-equality of the recorded `draft` date directly, because the two fail differently: a
    verdict-only test would pass if the classifier were loosened rather than the clock fixed, and a
    date-only test would miss a future classifier change that reintroduces the harm.

    COVER THE EXACT STATE THAT FIRES AND THE ONES THAT DO NOT, because this is the measurement most
    likely to be lost. Driven in process east of UTC: scaffold ALONE is clean (one record, nothing to
    compare); scaffold + `to-review` FIRES; scaffold + `to-review` + `reviewed` is clean AGAIN, because
    the setter prepends into the same contiguous block and two same-date records make
    `_plan_status_event_groups` classify that block's direction `unknown`, which sets `ordered=False`
    and SKIPS validation. So the window is a real plan state and it is NARROW, and a test written
    only against the three-record shape would pass against the unfixed code. Parameterize over all
    three and name each case.

    SET `TZ` FOR THE CODE UNDER TEST ONLY AND RESTORE IT UNCONDITIONALLY. `time.tzset()` mutates
    process-global state, and this suite runs under `pytest-randomly` with `-n auto`, so a leaked
    `TZ` corrupts unrelated tests nondeterministically and BY ORDER. Use a context manager with a
    `finally` restore, and prove no leak by co-running this file with
    `tests/test_specs_date_containment.py` in ONE process, since that file computes
    `dt.date.today()` locally and globs for the resulting prefix. Do NOT export `TZ` for the suite:
    that hides the bug behind an environment variable, which is the anti-pattern the two existing
    date masks already represent.
  - Depends on: E-03
    USE A FIXED-OFFSET POSIX ZONE THAT IS ALWAYS IN THE SKEW WINDOW, NOT A REAL ZONE. A real zone is in the window for only `offset` hours a day (F-07), so a test using `Pacific/Kiritimati` is RED at base for at most 14 of 24 hours, and a green run would prove nothing during the other 10. Measured at review: `XXX-24` (UTC+24) gives local `2026-10-03` against UTC `2026-10-02` at every wall-clock time, and `XXX+23:59` gives local one day BEHIND UTC except during the final minute of the UTC day. Use these as the east and west cases, and have the test FAIL LOUDLY (not skip) if its precondition `local_date != utc_date` is not met, so a mis-chosen zone cannot pass silently. Real zones such as `Pacific/Kiritimati` stay acceptable in the E-01 and V-04 validation runs, where the local and UTC dates are recorded.
  - Expected outcome: `tests/test_scaffold_history_clock.py` parameterizes over an east and a west timezone and over all three plan states (scaffold only, plus one transition, plus two), asserting both no `check.lifecycle-transition-invalid` finding and a UTC `draft` date; it is pasted RED at base (with E-02/E-03 reverted) naming the east case, and GREEN after; a single-process co-run with `tests/test_specs_date_containment.py` passes, proving `TZ` was restored.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- OUTCOME TESTS ONLY (`AGENTS.md`, GUIDING_PRINCIPLES P16). The clock property is proven by the date in a written artifact and by the checker's verdict on it, never by scanning `agent_workflows/*.py` for a `timezone.utc` token. P16's prohibition on `read_text()`/`ast.parse` against production code is unconditional.
- THE TWO CLOCK RULINGS ARE BOTH CURRENT AND DO NOT CONFLICT. Spec `2vev8j` Section 4.4 ("One timezone for every writer") rules history records UTC and is `approved` with a human attestation; `DECISIONS.md` D55 rules human-facing filename and name timestamps LOCAL, explicitly reversing an earlier UTC directive. They scope to different quantities, which is why this plan splits one value rather than unifying both.
- Run the suite BARE: `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and deselects `slow`/`livecorpus`; `-n0` is forbidden here, a second `-q` suppresses the `N passed` line this plan requires pasted, and `-p no:randomly` would disable the order randomization that makes E-04's `TZ`-leak concern real. Use `-o addopts=""` only when a narrowed run needs per-test counts.
- `aw` re-execs into the checkout's own package unless `AW_NO_REEXEC=1` is set; inside a lane worktree it prints a notice naming both paths. Set `AW_NO_REEXEC=1` on every `aw` invocation so the lane's own code runs and the notice does not pollute pasted evidence.
- A THROWAWAY REPO NEEDS `.aw/config/project.json` AND `git init`, or the verbs refuse: `project_context` will not resolve a root without the config file, and `check_engine` needs a git repo plus `include_untracked=True` to see an uncommitted artifact. Both were required to reproduce this defect.
- A release-blocking backlog item cannot be closed casually: `aw backlog set done` fails closed on an item carrying `- Blocks-Release:` unless the gate is HANDED OFF, SATISFIED with a resolvable in-tree citation, or explicitly DE-GATED. This plan closes nothing; the runner sets `jvw1kg` to `graduated` on the `From-Backlog` handoff.
- `tmp/` is gitignored and is the right home for probe scripts and throwaway fixture repositories in this checkout.

## Findings

Established in this lane at HEAD `a3ed40a35` by driving the shipped CLI, not by reading code alone. The skew window was entered with the POSIX zone `XXX-20` (UTC+20) because the machine's wall clock put every real zone's window closed at measurement time.

| # | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH (THE DEFECT, DRIVEN END TO END) | Under `TZ=XXX-20` (local `2026-10-03`, UTC `2026-10-02`) in a throwaway repo: `aw ipd scaffold --kind child --apply` then `aw ipd set to-review <plan>`, both exit 0, producing `- 2026-10-02 to-review (aw set): to to-review` above `- 2026-10-03 draft (probe): created.` and filename `20261003-probeset-01-<id6>-probe-plan.ipd.md`. `aw check plans --agent` then exits 1 with `check.lifecycle-transition-invalid`. The identical sequence under `TZ=Pacific/Honolulu` (local `2026-10-01`, UTC `2026-10-02`) exits 0. | **THE GATE'S VERDICT ON AN IDENTICALLY-AUTHORED PLAN DEPENDS ON THE AUTHOR'S TIMEZONE.** The failing detail reads `recorded lifecycle transition 'to-review' -> 'draft' is invalid: missing predecessor: backwards transition 'to-review' -> 'draft'`, which accuses the author of a backwards transition that never happened. This is the user-perceptible harm that earns the `bug` classification. |
| F-02 | HIGH (THIS SITE IS IN NO OTHER PLAN'S SCOPE - REVIEW CORRECTION: FALSE, `rfyrvp` declares it too; see the review note above Task group 1 and OQ-03) | `5ivkdh`'s `- Scope-Paths:` lists `artifact_core.py`, `backlog.py`, `specs.py`, `status_set.py`, `releases.py`, `readiness_recheck.py` and three test files; its E-05 audit classifies "`ipd_authoring`'s plan `- Date:` and its compact filename date (D55, leave)" and names no history record there. `ayhveg` declares only `tests/test_history_date_clock_parity.py`, `tests/test_history_label_parity.py` and `tests/test_backlog.py`, and derives its targets from setter/note verbs, which `COMMAND_INVENTORY` yields as `backlog set`, `backlog note`, `specs set`, `specs note`, `ipd set`, `prompts set` plus aliases - `ipd scaffold` is a separate declaration and is not in that set. `qjm4bg` declares seven `.backlog.md` files and no code. | **THE WORK IS ADDITIVE, NOT A NINTH DUPLICATE.** `5ivkdh`'s audit reached `ipd_authoring` and classified it correctly for the two dates it looked at, then missed that the SAME value also stamps a history record. So the omission is one line of classification, not an oversight of the module, and it is exactly the kind a derived guard would not catch either. |
| F-03 | HIGH (THE SUITE CANNOT SEE IT) | A search of `tests/*.py` for `tzset(` returns ZERO matches. The bare suite at this HEAD measured `3 failed, 4623 passed, 2 skipped` with the defect live; the three failures are `test_run_finding_reachability`, `test_selector_type_containment` and `test_spec_review_attestation`, none of which touches dates. | **"TESTS PASS" IS WORTHLESS EVIDENCE FOR THIS DEFECT**, so E-04's acceptance bar is a guard demonstrated RED at base. No test in the repository can enter a skew window on purpose today, which is why this survived while eight items were filed about its sibling. |
| F-04 | HIGH (THE WINDOW IS NARROW AND A CARELESS TEST MISSES IT) | Driven east of UTC, same fixture, three states: scaffold ALONE -> `aw check plans` rc 0; scaffold + `to-review` -> rc 1; scaffold + `to-review` + `reviewed` -> rc 0. In process, `_plan_status_event_groups` returns `ordered=True` for the two-record shape and `ordered=False` for the three-record shape, because the setter prepends into the SAME contiguous block and two same-date records make the block's direction `unknown`. `check_lifecycle_transitions` skips validation for an unordered group. | **A TEST WRITTEN AGAINST THE "OBVIOUS" FULLY-TRANSITIONED PLAN WOULD PASS AGAINST THE UNFIXED CODE.** This is the single most load-bearing measurement in this plan: it dictates that E-04 parameterize over all three states. It also bounds the blast radius honestly, since a plan that keeps moving stops failing. |
| F-05 | HIGH (THE FIX SHAPE IS PRE-VERIFIED) | A fixture built through the real `build_skeleton` with the `draft` record stamped UTC (`2026-10-02`) and everything else left LOCAL (`- Date: 2026-10-03`, filename `20261003-...`), plus the UTC `to-review` record: `check_lifecycle_transitions` returns 0 findings. The identical fixture with the `draft` record stamped LOCAL returns 1. | **STAMPING THE HISTORY RECORD UTC WHILE LEAVING THE FILENAME AND `- Date:` LOCAL ACTUALLY FIXES IT**, so this plan is not proposing a fix shape on theory. It also confirms the filename/history one-day gap is tolerated by the checker. |
| F-06 | MEDIUM (ONE VALUE, TWO ROLES, AND A BYTE-PINNED TEST) | `build_skeleton(when="1999-12-31", ...)` returns that value on exactly two lines: `- Date: 1999-12-31` and `- 1999-12-31 draft (probe): created.`. `tests/test_ipd_templates.py` rebuilds both committed templates from `build_skeleton` with a pinned `when` and asserts byte equality ("child template drifted from build_skeleton; regenerate it"); nine further test modules plus `tests/support.py` call it with a pinned `when`. | **THE SPLIT MUST BE AN OPTIONAL PARAMETER DEFAULTING TO `when`, NOT A REDEFINITION.** A required argument or an internal UTC call would break the template parity test and force a regeneration, turning a one-line clock fix into a template churn. This is why E-02 and E-03 are separate items. |
| F-07 | MEDIUM (THE EXPOSURE IS REAL BUT ONE-SIDED) | Computed over a 24-hour day: a zone is ahead of the UTC date for `offset` hours per day, so `Pacific/Kiritimati` (+14) is exposed 58.3% of the time, `Australia/Sydney` (+10) 41.7%, `Asia/Tokyo` (+9) 37.5%, `Asia/Kolkata` (+5.5) 22.9%, `Europe/Berlin` (+2) 8.3%; `UTC`, `America/New_York` and `Pacific/Honolulu` are 0%. | **ONLY AUTHORS EAST OF UTC ARE AFFECTED, AND THEY ARE AFFECTED FOR A LARGE FRACTION OF EACH DAY.** The maintainer's own machine (US Eastern) is at 0%, which explains why the clock cluster was filed eight times from the backlog side and this site never was. It also means CI in UTC cannot catch it. |
| F-08 | MEDIUM (NO EXISTING ARTIFACT IS AFFECTED) | Scanning all 1161 plans with derivable history in `.aw/records/plans/**` for a `draft` record dated AFTER its successor: ZERO matches. | **THIS PLAN FIXES A FORWARD-LOOKING DEFECT AND NEEDS NO CORPUS MIGRATION**, which is what keeps its scope to two files. Consistent with F-07: every plan in this corpus was authored at or west of UTC. |
| F-09 | LOW (THE ITEM'S OWN HEADLINE IS ALREADY OWNED THREE TIMES) | `jvw1kg`'s summary names `backlog.run_set` versus `status_set`. That exact divergence is reproduced live here (`- 2026-10-01 same-status (aw backlog): m` versus `- 2026-10-02 same-status (aw set): m`, both rc 0, under `TZ=Pacific/Honolulu`) and is owned by `5ivkdh` (production) and `ayhveg` (guard); `qjm4bg` E-03 names `jvw1kg` as one of five pure duplicates it closes with `--evidence`. | **AUTHORING THE ITEM'S LITERAL TEXT WOULD HAVE PRODUCED A FOURTH COLLIDING PLAN.** The honest graduation is the uncovered site of the same defect, with the literal text left to its existing carriers. Recorded so a reviewer can judge that scoping decision rather than re-derive it. |

## Proposed changes (ordered, validatable)

1. Reproduce the gate failure through the shipped CLI east and west of UTC, and capture the suite baseline by failure name (E-01).
2. `agent_workflows/ipd_authoring.py`: `build_skeleton` gains an optional history-date parameter defaulting to `when`, documented with both governing authorities (E-02).
3. `agent_workflows/ipd_authoring.py`: `run_scaffold` passes a UTC history date beside its LOCAL `when`, reusing `artifact_core`'s shared helper if `5ivkdh` has landed; both filename sites untouched (E-03).
4. `tests/test_scaffold_history_clock.py`: a new outcome guard over two timezones and all three plan states, demonstrated RED at base (E-04).

No spec is amended and no `.spec.md` appears in `- Scope-Paths:`. No `CHANGELOG.md` entry: see "Spec / documentation sync".

## Deferred / out of scope (with reason)

- THE SETTER-FAMILY CLOCK FIX IS NOT MADE HERE. `5ivkdh` owns `backlog.py`, `specs.py`, `status_set.py`, `releases.py` and `readiness_recheck.py` and declares them all. This plan touches a caller that plan does not declare, so the two are disjoint on every path and need no ordering edge.
  - Carrier: 5ivkdh
- THE CROSS-SPELLING TIMEZONE GUARD IS NOT BUILT HERE. `ayhveg` owns a `COMMAND_INVENTORY`-derived differential guard over setter/note verbs. `aw ipd scaffold` is not a setter and would not appear in its derivation, so E-04's guard is additive rather than a duplicate of it.
  - Carrier: ayhveg
- THE DUPLICATE-ITEM CONVERGENCE IS NOT PERFORMED HERE. `qjm4bg` E-03 closes `jvw1kg` along with four other pure duplicates once its two carriers execute. This plan writes no status onto any backlog item; the runner sets `jvw1kg` to `graduated` on the `From-Backlog` handoff, which preserves its gate.
  - Carrier: qjm4bg
- THE FILENAME PREFIX AND THE `- Date:` FIELD STAY LOCAL. `DECISIONS.md` D55 rules human-facing timestamp names LOCAL on an explicit UX rationale, reversing an earlier UTC directive, and is current. F-05 shows the checker tolerates the resulting one-day gap. Moving them would reverse a standing ruling and needs its own maintainer decision.
  - Carrier-Declined: not a defect; D55 is a deliberate, current ruling and the two clocks compose as written.
- `prompts._today_iso` IS NOT TOUCHED. It feeds a prompt's filename and its `created` metadata comment; a prompt carries no `## Workflow history` record in the shape the history readers parse, so there is no history date there to move.
  - Carrier-Declined: not a defect; the value stamps a name and a metadata field, both of which D55 rules local.
- THE DIRECTION CLASSIFIER IS NOT CHANGED. `_plan_status_event_groups`'s `unknown`-direction-means-unordered behavior is what makes the failure window narrow (F-04), and `ipd_lifecycle` carries an explicit note that the two readers answer different questions and must not be unified. Loosening the classifier would hide this defect rather than fix it, and would weaken a gate that is otherwise correct.
  - Carrier-Declined: not a defect; the classifier is conservative by design and the clock is what is wrong.
- NO CORPUS MIGRATION IS ATTEMPTED. F-08 measured zero affected artifacts among 1161 plans with derivable history. Rewriting committed history would assert dates that were never recorded (GUIDING_PRINCIPLES P4).
  - Carrier-Declined: not a defect; no artifact needs it and restamping history would be a false record.
- THE THREE PRE-EXISTING SUITE FAILURES ARE NOT FIXED. The bare suite measured `3 failed, 4623 passed, 2 skipped` at authoring, in `test_run_finding_reachability`, `test_selector_type_containment` and `test_spec_review_attestation`. None involves a date or the scaffold.
  - Carrier-Declined: unrelated to this plan's subject; it touches neither those modules nor the code they exercise.

## Scope check

- Over-scope: none. `agent_workflows/ipd_authoring.py` receives one optional parameter on `build_skeleton` (E-02) and one changed argument at its single production call site in `run_scaffold` (E-03); `tests/test_scaffold_history_clock.py` is new (E-04). `agent_workflows/status_set.py` is NOT declared and must not be committed even though E-01 drives it, because it is already UTC and is `5ivkdh`'s to touch. `agent_workflows/check_engine.py` and `agent_workflows/ipd_lifecycle.py` are NOT declared and must not be changed: E-01 and E-04 READ their verdicts, and changing the classifier is explicitly deferred above. `tests/test_ipd_templates.py` must pass UNMODIFIED, which is the proof E-02's default worked.
- Under-scope: E-03 may find that `5ivkdh` has landed and that the shared `artifact_core` helper exists, in which case this plan calls it rather than writing an inline expression; that is a narrowing, not a widening, and needs no new path. If E-04's `TZ`-leak co-run reveals a THIRD test that depends on the local clock in a way this guard disturbs, declare that path at execution and record the widening in the transition message; this note authorizes it. The plan's own file needs no declaration (implicit lifecycle-artifact allowance, spec `ipd-structure-and-linting` Section 4.5).

## Required tests / validation

- The BARE suite: `python3 -m pytest`, with the `N passed` line pasted. Establish the baseline AT THE EXECUTING HEAD rather than trusting the authoring number, since sibling plans land in between; compare FAILURE SETS BY NAME, not counts. Authoring baseline for reference: `3 failed, 4623 passed, 2 skipped`.
- `tests/test_scaffold_history_clock.py` run alone with `-o addopts=""`, every case named, demonstrated RED AT BASE (E-02 and E-03 reverted or stashed) and GREEN after. Paste the failure showing a LOCAL `draft` date where UTC was required, AND the `check.lifecycle-transition-invalid` finding, for the east-of-UTC two-record case specifically.
- The new guard's three plan states each shown individually (scaffold only, plus one transition, plus two), so the F-04 narrowness is pinned rather than assumed.
- `tests/test_ipd_templates.py` and `tests/test_ipd_authoring.py` run individually and passing, with `git diff --stat` for `tests/test_ipd_templates.py` showing NO change. Any edit to that file means E-02's default did not hold and the fix is wrong.
- A `TZ`-leak check: run the new file together with `tests/test_specs_date_containment.py` in ONE process (`-o addopts=""`, no xdist) and paste the result, proving the context manager restored `TZ` and did not corrupt a neighbor that depends on the local clock.
- The full suite run under an exported `TZ=Pacific/Kiritimati` (UTC+14) and again under `TZ=Pacific/Honolulu` (UTC-10), both pasted. These bracket UTC in both directions. This is a VALIDATION-TIME use of `TZ` to EXPOSE the defect, never a fix-time use to hide it.
- A manual end-to-end re-run of F-01's reproduction east of UTC: real `aw ipd scaffold --apply`, real `aw ipd set to-review`, then `aw check plans --agent` at exit 0, with the plan's filename, `- Date:` and both history records pasted so the local-name/UTC-history composition is visible in one artifact.
- `AW_NO_REEXEC=1 aw check`, `AW_NO_REEXEC=1 aw attention --check`, `AW_NO_REEXEC=1 aw sanitize --agent`. `aw check` and `aw attention --check` exit 1 on PRE-EXISTING conditions unrelated to this plan, so the honest bar is an UNCHANGED FINDING SET: re-derive before and after and diff. Do not "fix" another plan's finding or another lane's state. Redact absolute temp paths to `<tmp>` in pasted evidence.
- `AW_NO_REEXEC=1 aw ipd lint --phase pre-transition` on this plan, conforming.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Verify the staged set against this plan's `- Scope-Paths:` before committing.

## Spec / documentation sync

No spec is amended and no `.spec.md` file appears in `- Scope-Paths:`. This plan IMPLEMENTS spec
`2vev8j` Section 4.4 ("One timezone for every writer"), which is already `approved` and
human-attested, on one writer that ruling already covers and that no plan had reached. It changes no
contract.

`DECISIONS.md` gets no entry. D55 already rules filename and name timestamps LOCAL and stays exactly
as written; this plan does not touch a name. Recording the history-clock decision again would create
a second authority for a ruling 4.4 already holds, which is the duplication this cluster of items
exists to remove.

No `CHANGELOG.md` entry, and this is a deliberate judgement rather than an omission. The
user-visible announcement that history dates are UTC everywhere belongs to `5ivkdh`, which owns the
setter family and declares the changelog; a second entry for one clock decision would report two
changes to a reader where one happened. If `5ivkdh` is still unexecuted when this plan runs, say so
in the transition message so whoever executes it knows to cover this site in its entry.

## Open questions

### OQ-01: Should `aw ipd scaffold` keep writing the plan's filename and `- Date:` from the LOCAL clock while its history record moves to UTC?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, not referred to the maintainer, because the repository has already ruled on both halves and the rulings scope to different quantities. HISTORY RECORDS ARE UTC: spec `2vev8j` Section 4.4 states "Every writer, tool and human-facing helper alike, records UTC; local time is a RENDER-TIME concern only", and that spec is `approved` with a human attestation. HUMAN-FACING NAMES ARE LOCAL: `DECISIONS.md` D55 ("Human-facing timestamps use LOCAL time, not UTC") deliberately reverses the earlier UTC directive for filenames on a stated UX rationale and remains current, and its "Excluded (stay UTC, deliberately)" clause confirms it is a scoped ruling rather than a blanket one. The composition is also MEASURED SAFE rather than merely argued: F-05 shows a fixture carrying a LOCAL filename, a LOCAL `- Date:` and a UTC `draft` record one day apart draws zero findings from `check_lifecycle_transitions`, and `check_engine._artifact_compact_date` reads the filename and `- Date:` interchangeably while comparing neither against a history date. So the split is what both rulings require, and unifying the two would reverse one of them.

### OQ-02: Should this plan have been folded into `5ivkdh` rather than authored separately?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED AGAINST FOLDING, on three grounds, and recorded because it is the first objection a reviewer will raise. FIRST, THE SCOPE IS DISJOINT: `5ivkdh` declares six production files and `ipd_authoring.py` is not among them, so folding would require widening an already-authored, review-ready plan's `- Scope-Paths:`, which is the kind of edit the plan-review contract exists to prevent after review. SECOND, `5ivkdh` HAS ALREADY CLASSIFIED THIS MODULE AND REACHED THE OPPOSITE CONCLUSION: its E-05 audit names "`ipd_authoring`'s plan `- Date:` and its compact filename date (D55, leave)", so the omission is a specific misclassification of one value that serves two roles, and correcting it inside that plan would silently change an audit verdict a reviewer approved. THIRD, THE TWO FIXES ARE INDEPENDENTLY CORRECT AND NEED NO ORDERING: this plan changes a caller that plan does not declare, and E-03 reuses its shared helper IF present and writes an inline expression otherwise, so neither blocks the other. A hard `executed:5ivkdh` edge would gate a measured, release-blocking gate failure behind an unrelated plan's review queue for no correctness gain.

### OQ-03: This plan and pending plan `rfyrvp` both fix the same `run_scaffold` clock split in `agent_workflows/ipd_authoring.py`. Which one should carry the fix?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: RESOLVED 2026-10-02 by maintainer: Keep plan 9wcei0, fold in rfyrvp's --path-branch probe and module date audit into E-03/E-04, and retire rfyrvp as superseded. Plan 9wcei0 asserts the check plans checker verdict and three-state cases.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: the pasted transcript of the real `aw ipd scaffold --apply` plus `aw ipd set to-review` plus `aw check plans --agent` sequence under BOTH an east-of-UTC and a west-of-UTC timezone, showing exit 1 east and exit 0 west, with the full finding detail text quoted for the east run. For each run, the computed local date AND UTC date printed, proving a skew window was entered rather than assumed, plus the plan's filename and both history records verbatim. Plus the bare-suite baseline at the executing HEAD with its summary line pasted and its failures listed BY NAME. No assertion about any module's source text is acceptable as evidence here.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the new parameter's signature and its docstring quoted, showing it defaults to `when` and that the documentation names BOTH authorities (`2vev8j` 4.4 for the UTC history date, `DECISIONS.md` D55 for the local name). Plus proof the default changed no byte: `tests/test_ipd_templates.py` passing with `git diff --stat` showing that file unchanged, and `tests/test_ipd_authoring.py` passing. Plus a demonstration that passing BOTH dates puts them on the two different lines, by pasting the rendered `- Date:` line and the rendered `draft` record from one skeleton built with two distinct pinned values.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: one plan produced by the real `aw ipd scaffold --apply` east of UTC, pasted far enough to show its FILENAME prefix, its `- Date:` field and its `draft` history record together, with the local and UTC dates printed alongside, so the LOCAL-name/UTC-history composition is visible in a single artifact and proven to be inside a skew window. Plus the E-01 reproduction re-run and now reporting `aw check plans --agent` exit 0 east AND west of UTC, both pasted. Plus an explicit statement of which route E-03 took (shared `artifact_core` helper reused, or inline expression written) and, if inline, that the comment naming its eventual home is present.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the new guard pasted RED AT BASE with E-02/E-03 reverted, naming the east-of-UTC two-record case and showing BOTH the wrong date and the `check.lifecycle-transition-invalid` finding, then pasted GREEN after, each run with `-o addopts=""` and every case named. Plus all three plan states shown individually so F-04's narrow window is pinned. Plus the timezone context manager's source quoted showing `time.tzset()` inside it and an unconditional `TZ` restore in a `finally`. Plus the single-process co-run with `tests/test_specs_date_containment.py` pasted, proving no `TZ` leak. Plus the bare suite with its summary line, and the two whole-suite runs under `TZ=Pacific/Kiritimati` and `TZ=Pacific/Honolulu`. Plus the before-and-after finding sets for `aw check` and `aw attention --check`, shown UNCHANGED.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field: that field is an OUTPUT of
`/plan-review`, and writing one here would forge a review that has not happened. It requires
explicit human approval before execution.

EXECUTION CONTRACT, binding on whoever executes this plan:

1. OQ-01 and OQ-02 are resolved from cited repository evidence. OQ-03 is `Blocking: yes` and awaits the maintainer, because it decides whether this plan or `rfyrvp` carries the fix. Do not execute until it is resolved.
2. REPRODUCE BEFORE YOU CHANGE ANYTHING. E-01 is first for a reason: this plan's premise is a gate
   verdict that depends on three moving parts it does not own. If the reproduction does not fire east
   of UTC, STOP AND REPORT; do not "fix" a defect that is no longer there.
3. DO NOT LOOSEN THE CHECKER TO MAKE THIS PASS. If the guard fails, the clock is wrong, not the
   gate. `check_engine.py` and `ipd_lifecycle.py` are deliberately outside `- Scope-Paths:`, and
   weakening the direction classifier would hide this defect while removing a correct protection.
4. DO NOT TOUCH THE FILENAME OR `- Date:`. D55 rules them LOCAL. A plan whose filename prefix and
   `draft` record differ by one day inside a skew window is CORRECT, and F-05 proves no checker
   objects. "Fixing" that apparent inconsistency reverses a standing ruling.
5. `tests/test_ipd_templates.py` MUST PASS UNMODIFIED. It is the byte-parity guard on both shipped
   templates and it is the proof that E-02's optional default worked. If it needs editing, the fix
   shape is wrong: make the parameter optional instead of regenerating a template.
6. HARD MUST, HONESTY. When you report that validation passed, paste the ACTUAL command output.
   Every `V-*` above demands pasted evidence, and V-01, V-03 and V-04 demand a BEFORE/AFTER
   comparison that cannot be satisfied from memory. A guard never seen failing proves nothing, and
   per F-03 a green suite is not evidence for this defect.
7. DO NOT WRITE A STATUS ONTO `jvw1kg`. The runner sets it `graduated` on verification, which
   preserves its release gate. Writing it here would forge a transition this plan does not perform,
   and `qjm4bg` already owns that item's eventual closure.
8. COMMIT ONLY THIS PLAN'S OWN PATHS, through `aw commit <plan> -- <paths>`. Never `git add -A`,
   never bare `git add`, never `-a`, never `--no-verify`, and never push. This is a SHARED CHECKOUT:
   verify the staged set with `git diff --cached --name-only` before committing and unstage anything
   that is not yours with `git restore --staged <path>`.
9. SCOPE FENCE. `- Scope-Paths:` is a DECLARATION that finalize reconciles, not a stop condition: if the work genuinely needs another path, make the edit and JUSTIFY it with `--scope-reason <path>=<why>`, and acknowledge any declared-but-unmodified path with `--scope-ack`. The one genuine stop is an unresolvable concurrent edit to `agent_workflows/ipd_authoring.py` (for example by `rfyrvp`).
10. LIFECYCLE MOVE ON COMPLETION. OWNERSHIP IS CONDITIONAL: under `aw oc run` / `aw agy run` the RUNNER performs `aw ipd begin`/`aw ipd finalize` (an in-lane invocation is refused by design), so do not invoke it yourself. In a manual run, finalize with
   `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`, which runs the
   pre/post-transition gates, reconciles changed paths against the reviewed `- Scope-Paths:`, writes
   the attributed history newest-first, moves the plan to `.aw/records/plans/executed/`, and makes
   the path-scoped lifecycle commit as one transaction. Do not hand-move the file and do not claim
   `executed` until `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass`.
