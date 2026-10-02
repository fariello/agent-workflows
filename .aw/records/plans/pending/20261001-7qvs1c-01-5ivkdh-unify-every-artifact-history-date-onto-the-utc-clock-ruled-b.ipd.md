# IPD: Unify every artifact history date onto the UTC clock ruled by spec 2vev8j 4.4 while keeping filename dates local per D55

- Date: 2026-10-01
- Kind: child
- Concern: Two writers stamp an artifact's `## Workflow history` from two different clocks, so the same user intent records a different date depending on which CLI spelling the user typed. `status_set.apply_status_change` reads the UTC clock; `backlog._reattach_history`, `specs._today`, `releases.render_new_release` and `readiness_recheck` read the machine-local clock. Measured in this lane under `TZ=Pacific/Honolulu` (UTC-10, inside the live skew window): `aw backlog set <id> --status open` wrote `- 2026-10-01 same-status (aw backlog): m` while `aw backlog set open <id>` wrote `- 2026-10-02 same-status (aw set): m` on an identical fixture. Spec `2vev8j` Section 4.4 ("One timezone for every writer") already RULES this in UTC's favor and is `approved` with a human attestation, so the clock is not an open question; it is an unimplemented ruling.
- Scope: IN: add ONE shared UTC date helper to `artifact_core` and route every HISTORY-RECORD date writer through it, so `2vev8j` 4.4 holds for all of them; unmask the two date-normalizing parity tests so the UTC property is pinned by a test instead of hidden from one; add a timezone-parameterized regression guard that fails under a local/UTC skew. OUT, each with a reason under "Deferred": FILENAME date prefixes, which `DECISIONS.md` D55 deliberately rules LOCAL and which this plan must not touch; the `aw set` family's missing `--date` override; the dispatch-fork unification owned by the `setdisp` Set; closing the six sibling carrier items.
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/backlog.py, agent_workflows/specs.py, agent_workflows/status_set.py, agent_workflows/releases.py, agent_workflows/readiness_recheck.py, tests/test_history_date_clock.py, tests/test_backlog.py, tests/test_history_label_parity.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 7qvs1c
- Blocks-Release: next
- Set: 7qvs1c
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 5ivkdh

## Workflow history

- 2026-10-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `7qvs1c`. The clock question the sibling items leave open was RESOLVED from repository evidence rather than referred to the maintainer: spec `2vev8j` 4.4 (approved, human-attested) rules history dates UTC, and `DECISIONS.md` D55 rules filename dates LOCAL. The divergence was reproduced end to end in this lane at HEAD `6c18c158f` under `TZ=Pacific/Honolulu`; the base suite measured bare at `4405 passed, 2 skipped`.
- 2026-10-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make an artifact's recorded history date depend only on WHEN the action happened, never on which CLI
spelling invoked it or which timezone the machine sits in, by giving every history writer one shared
UTC date source. Leave filename dates on the local clock, because a different and still-current
ruling (D55) deliberately put them there.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: establish the one clock source

- [ ] E-01 Add ONE shared history-date helper to `artifact_core` and nothing else in this item. Name it for what it IS (a UTC history date), not for "today", so the next reader cannot mistake it for the filename clock: a bare `today()` is exactly the ambiguity that let these two clocks coexist. Give it a docstring that cites spec `2vev8j` 4.4 as the authority, states that it returns `YYYY-MM-DD` in UTC, and states in the same breath that FILENAME dates are LOCAL per `DECISIONS.md` D55 and must NOT call it.

    PUT IT IN `artifact_core`, NOT IN A NEW MODULE. Measured in this lane: `backlog`, `specs`, `set_records`, `record_history`, `releases` and `ipd_authoring` ALL already import `agent_workflows.artifact_core`, and `status_set` imports it as `_core`. So every writer this plan touches can reach it with no new import edge and no import cycle. A new `dates.py` would add an edge to seven modules to hold one function.

    ALSO ADD A COMPACT (`YYYYMMDD`) UTC VARIANT ONLY IF E-05 PROVES A CALLER NEEDS IT. Do not author an unused second function speculatively; `record_history.append` takes a compact date, so decide this from E-05's measurement, not now.
  - Depends on: none
  - Expected outcome: `artifact_core` exports one documented helper returning the UTC date as `YYYY-MM-DD`; it is called by nothing yet; the bare suite is unchanged from the `4405 passed, 2 skipped` baseline because no behavior has moved.
  - Execution state: pending

### Task group 2: route the history writers onto it

- [ ] E-02 Route the BACKLOG history writers onto the shared helper, and leave `backlog`'s FILENAME date alone. The three history sites are `backlog._reattach_history`'s `today` (the transition record, and the one measured as divergent), and the `created` record rendered in both branches of the item renderer. `backlog.run_note` already honors an explicit `--date` and must KEEP that precedence, falling back to the shared helper only when `--date` is absent.

    DO NOT TOUCH THE FILENAME SITE. `backlog.run_new` computes a separate compact date for the `YYYYMMDD-...backlog.md` name. That one is governed by D55 and stays LOCAL. Both a history date and a filename date are computed in this one module from the same-looking expression, which is precisely why this item names the sites by their ROLE rather than changing every `date.today()` the file contains.

    EXPECT A ONE-DAY DISAGREEMENT BETWEEN AN ITEM'S FILENAME AND ITS OWN `created` RECORD inside the skew window, and do not "fix" it. That is the two rulings composing exactly as written, it is already true of every artifact type today, and V-05 proves no checker objects.
  - Depends on: E-01
  - Expected outcome: a backlog transition and a backlog creation both record the UTC date; `aw backlog note --date <d>` still honors `<d>`; the filename prefix is still local; `tests/test_backlog.py` and `tests/test_history_provenance.py` pass.
  - Execution state: pending

- [ ] E-03 Route the SPECS history writer onto the shared helper WITHOUT moving the spec filename date, which requires splitting one existing value. `specs._today` is called from four places, and the call in `specs.run_new` feeds BOTH the `- Date:` front matter plus the `created` history record AND, via a compact form, the spec FILENAME. So a blunt redefinition of `_today` silently moves a filename onto UTC and reverses D55.

    SPLIT THE TWO ROLES AT THAT CALL SITE: keep a LOCAL value for the filename and derive a UTC value for the history record, with a comment naming both authorities. The other three callers (the status setter, the migrate path and the note path) are history-only and move wholesale, each preserving its existing `--date` precedence.

    `tests/test_specs_date_containment.py::test_non_regression_omitted_date_defaults_today` IS THE GUARD THAT CATCHES GETTING THIS WRONG: it computes `date.today()` LOCALLY and then globs for a file whose name carries that compact date. It passes under `TZ=Pacific/Honolulu` at base (measured), and it must still pass after this change. If it fails, the filename moved to UTC and the fix is wrong, so do NOT edit that test to accommodate.
  - Depends on: E-01
  - Expected outcome: a spec status transition, a migrate and a note all record the UTC date; `aw specs new` writes a LOCAL filename prefix and a UTC `created` record; `tests/test_specs_date_containment.py` passes unchanged under both timezones.
  - Execution state: pending

- [ ] E-04 Route the REMAINING history writers onto the shared helper: the release record's `created` line in `releases.render_new_release`, and `readiness_recheck`'s `today`, which it passes into the plan history writer and the stale-findings path.

    THE RELEASE FUNCTION HAS THE SAME SPLIT AS E-03 IN MINIATURE and is the reason this is its own item: it computes a compact date for the `.release.md` FILENAME and an ISO date for the `created` HISTORY line, as two separate expressions. Move ONLY the history one.

    `readiness_recheck` IS THE ONE MODULE HERE THAT DOES NOT YET IMPORT `artifact_core` (measured: zero references), so it needs a new import. That is the single new import edge this plan adds, and it is worth noting in the evidence so a reviewer does not read it as unrelated churn.
  - Depends on: E-01
  - Expected outcome: a created release records the UTC date in its history and keeps a LOCAL filename prefix; a readiness recheck records the UTC date; the walkthrough/promotion sites in `set_records` are audited by E-05 rather than assumed.
  - Execution state: pending

- [ ] E-05 Audit every REMAINING local-clock date call in the package and record a per-site HISTORY-or-FILENAME-or-NEITHER verdict, converting only the history ones. This item exists because the previous four were chosen from a measured inventory and an inventory can miss a site; a verdict table is what makes the claim "every writer" checkable instead of asserted.

    THE SITES ALREADY CLASSIFIED, so the audit is a confirmation plus a search for anything absent: `set_records`'s walkthrough `- Date:` (front matter of a narrative doc, not a history record) and its two compact filename dates (D55, leave); `record_history.append` and the rename recorder (the sidecar, compact, and `2vev8j` 4.2 makes it a GITIGNORED advisory log, not the durable store, so changing it is cosmetic and OUT unless the audit shows a user reads it); `ipd_authoring`'s plan `- Date:` and its compact filename date (D55, leave); `prompts._today_iso` (feeds a prompt filename and `- Date:`, not a history record); and the four read-only age comparisons in `attention`, `plans_archive`, `research_archive` and `workflow_artifacts_prune`, which compare rather than write and must NOT move, since comparing a stored local date against a UTC today would shift every age boundary by up to a day.

    `set_records.close_on_answer` NEEDS NO EDIT AND SAY SO EXPLICITLY: it delegates its history write to `backlog._reattach_history`, so E-02 fixes it transitively. Verify that by driving it, not by reading it.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: a table of every remaining `date.today()`-class call in `agent_workflows/` with a HISTORY/FILENAME/NEITHER verdict and the reason; every HISTORY verdict converted; no FILENAME or NEITHER site changed; a stated confirmation that no history writer remains on the local clock.
  - Execution state: pending

### Task group 3: pin the property that was being hidden

- [ ] E-06 Replace the two date-MASKING normalizations with the real assertion, and add a timezone-parameterized guard in a new `tests/test_history_date_clock.py`. Two existing tests currently delete the date from their comparison with a regex substitution before asserting equality, each carrying a comment naming this bug as out of scope: the cross-spelling case in `tests/test_backlog.py` and the shared normalizer in `tests/test_history_label_parity.py`. Those masks are why the suite is green today while the defect is live, so leaving them would let this plan claim a fix no test can see.

    REMOVE ONLY THE DATE MASK, NOT THE ACTOR MASK. The actor difference (`(aw backlog)` versus `(aw set)`) is deliberate and truthfully identifies the writer, as both comments state, and is owned elsewhere. Deleting it would make these tests fail for a reason this plan is not fixing.

    THE NEW GUARD MUST FAIL ON TODAY'S CODE, and that is the acceptance bar for this item. Drive the real CLI under at least one timezone EAST of UTC and one WEST of it (`Pacific/Kiritimati` at UTC+14 and `Pacific/Honolulu` at UTC-10 are the pair measured in this lane, and together they guarantee a skew window exists whatever the wall-clock hour), then assert the recorded date equals the UTC date. Set `TZ` and call `time.tzset()` for the child process only; do NOT set `TZ` for the suite, which would hide the bug behind an environment variable, the exact anti-pattern the `jbipfa` plan warned against when it introduced these masks.

    ASSERT ON THE WRITTEN FILE, never by reading the source for a `timezone.utc` token (GUIDING_PRINCIPLES P16, and `AGENTS.md`'s no-code-pinning rule): the outcome is the date in the artifact.
  - Depends on: E-05
  - Expected outcome: `tests/test_history_date_clock.py` asserts both CLI spellings record the UTC date under an east and a west timezone, and is demonstrated RED at base and GREEN after; both masked tests compare dates literally again while still normalizing the actor; the bare suite is green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- OUTCOME TESTS ONLY (`AGENTS.md`, GUIDING_PRINCIPLES P16). The clock fix is proven by the date written into an artifact, never by asserting that a module calls `datetime.timezone.utc`.
- Run the suite BARE: `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and deselects `slow`/`livecorpus`; `-n0` is forbidden and a second `-q` suppresses the `N passed` line this plan requires pasted. Use `-o addopts=""` only when a narrowed run needs per-test counts.
- `aw` re-execs into the checkout's own package unless `AW_NO_REEXEC=1` is set; inside a lane worktree it prints a notice naming both paths. Set `AW_NO_REEXEC=1` on every `aw` invocation so the lane's own code runs and the notice does not pollute pasted evidence.
- DERIVE A VALUE, NEVER RE-LIST IT (GUIDING_PRINCIPLES P8). This plan's whole thesis is that one clock decision must have one implementation, so adding a second inline `datetime.now(timezone.utc)` instead of calling the shared helper would reproduce the defect in the act of fixing it.
- THE TWO CLOCKS ARE BOTH CORRECT AND THE RULINGS ARE NOT IN CONFLICT. `2vev8j` 4.4 scopes itself to WRITERS of history and calls local time "a RENDER-TIME concern only"; D55 scopes itself to human-facing NAMES and explicitly excludes machine/telemetry timestamps. A reviewer who assumes one clock must win will read E-03's split as inconsistent, so each split site names both authorities in a comment.
- A release-blocking backlog item CANNOT be closed casually: `aw backlog set done` fails closed on an item carrying `- Blocks-Release:` unless the gate is HANDED OFF, SATISFIED with a resolvable in-tree citation, or explicitly DE-GATED. This plan closes nothing; the runner sets `7qvs1c` to `graduated` on the From-Backlog handoff.

## Findings

Established in this lane at HEAD `6c18c158f`, reading both writers in full and driving the CLI.

| # | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH (THE DEFECT, MEASURED) | Under `TZ=Pacific/Honolulu` (UTC-10, local `2026-10-01`, UTC `2026-10-02`), two `cli.main` calls on identical fixtures: `backlog set aa0001 --status open` wrote `date=2026-10-01 actor=aw backlog`; `backlog set open aa0001` wrote `date=2026-10-02 actor=aw set`. Both exited 0. | **THE SAME INTENT RECORDS TWO DIFFERENT DATES DEPENDING ON ARGUMENT ORDER.** This is user-visible, in permanent history, and reachable from five CLI spellings that route to `status_set.run_set_command`. It is a real defect and not a theoretical race. |
| F-02 | HIGH (THE RULING ALREADY EXISTS) | Spec `2vev8j` Section 4.4 is titled "One timezone for every writer" and reads "Every writer, tool and human-facing helper alike, records UTC; local time is a RENDER-TIME concern only." The spec is `approved` with `- 2026-09-09 approved (aw set, --by-human)`. | **THE CLOCK IS NOT AN OPEN QUESTION, SO THIS PLAN NEEDS NO MAINTAINER DECISION.** That matters because the sibling item `tl8qmc` asserts the choice is still open and argues both sides; it was filed without knowledge of 4.4. This plan IMPLEMENTS a ruling rather than making one, which is why OQ-01 is resolved rather than blocking. |
| F-03 | HIGH (THE TRAP) | `DECISIONS.md` D55 ("Human-facing timestamps use LOCAL time, not UTC") covers filename `YYYYMMDD` prefixes and explicitly excludes telemetry from its local rule. The naming spec `uniform-artifact-naming-grammar` says `YYYYMMDD` is "creation date (local)". `artifact_naming.build_clustered_name` holds NO clock; every caller supplies the date. | **THE OBVIOUS FIX IS WRONG: UNIFYING ALL DATES ONTO ONE CLOCK SILENTLY REVERSES D55.** A single `sed` of `date.today()` to a UTC call would move every filename prefix too. This is the finding that shapes E-02/E-03/E-04 into role-specific edits, and it is why the plan title names both rulings. |
| F-04 | HIGH (ONE VALUE, TWO ROLES) | `specs.run_new` computes `date_iso` once from `_today()`, validates it, then derives `date_compact` for `build_clustered_name` AND passes `date_iso` into the rendered spec body. `releases.render_new_release` has the same shape with two separate expressions. | **TWO SITES CANNOT BE CONVERTED WHOLESALE BECAUSE ONE VALUE SERVES BOTH A HISTORY RECORD AND A FILENAME.** Redefining `specs._today` alone looks like a clean one-line fix and would reverse D55 for every new spec. E-03 and E-04 split the roles instead. |
| F-05 | HIGH (THE SUITE CANNOT SEE THE BUG) | `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` substitutes `- HIST_DATE ` for the date before comparing, commented "This clock skew is live bug fnb8pl (out of scope for jbipfa)". `tests/test_history_label_parity.py::_normalize_history_record` does the same. Both measured PASSING under `TZ=Pacific/Honolulu` inside the skew window. | **NO TEST FAILS TODAY AND NO TEST WOULD NOTICE THE FIX**, so "tests pass" is worthless as evidence here. E-06's acceptance bar is therefore a guard demonstrated RED at base, and unmasking is part of the fix rather than cleanup. The backlog item's claim of a "test failure" is now STALE: the mask was added after it was filed. |
| F-06 | MEDIUM (SCOPE BOUNDARY) | The `setdisp` Set (children 00-05, pending) migrates both setters onto the shared engine. Child `vhiqo6` F-03 records that the clock items name FIVE local-clock sites in `backlog.py` while that migration removes only the one reached through `run_set`, and lists `backlog.run_note`, the `created` line and `set_records.close_on_answer` as remaining. | **A SET ALREADY IN FLIGHT FIXES THIS DEFECT FOR ONE PATH AS A SIDE EFFECT, AND DELIBERATELY DEFERS THE REST TO A CARRIER.** This plan is that carrier. The two are compatible in either order: `setdisp` removes a duplicate CALLER, this plan corrects the clock in every caller. Ordering is argued in "Deferred" rather than asserted as a dependency. |
| F-07 | MEDIUM (NO CHECKER OBJECTS) | A search for a rule comparing a filename date against a front-matter or history date found none; `check_engine._artifact_compact_date` reads the filename date and FALLS BACK to `- Date:`, using them interchangeably for cutover decisions only. | **FILENAME-VERSUS-HISTORY SKEW IS ALREADY TOLERATED AND IS NOT A NEW HAZARD.** Worth recording because the composition of the two rulings means a record can legitimately carry a local filename date and a UTC history date one day apart, and a reviewer may expect that to trip `aw check`. V-05 verifies it does not rather than relying on this search. |
| F-08 | LOW (SIX DUPLICATE FILINGS) | Seven open, release-gated, `Work-Kind: bug` items describe this one defect: `7qvs1c`, `fnb8pl`, `tl8qmc`, `jvw1kg`, `2wae2x`, `doe2fo`, `lq2w86`. Only `fnb8pl` and `tl8qmc` carry diagnostic content; the rest are near-identical one-liners. | **ONE DEFECT IS GATING THE RELEASE SEVEN TIMES.** Deduplication is a maintainer call, not something to resolve from evidence, so this plan closes none of them and raises it in "Deferred" instead. |
| F-09 | N/A (BASELINE) | Bare `python3 -m pytest` at HEAD `6c18c158f`: `4405 passed, 2 skipped, 3 warnings in 272.96s`. | **THE BASE IS GREEN**, so any failure after this plan's edits is attributable to it. Per F-05 the green baseline is time-INDEPENDENT only because the masks hide the skew. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/artifact_core.py`: one documented UTC history-date helper citing `2vev8j` 4.4 and warning that filename dates are local per D55 (E-01).
2. `agent_workflows/backlog.py`: the transition record and both `created` records onto the helper, `--date` precedence preserved, filename date untouched (E-02).
3. `agent_workflows/specs.py`: `_today`'s three history callers onto the helper; `run_new` split so the filename stays local and the history record is UTC (E-03).
4. `agent_workflows/releases.py`, `agent_workflows/readiness_recheck.py`: the release `created` history line and the recheck history date onto the helper, release filename untouched (E-04).
5. `agent_workflows/status_set.py`: its inline UTC expression replaced by the shared helper, so one clock has one implementation (E-01, E-05). Behavior-neutral by construction; it is already UTC.
6. `tests/test_history_date_clock.py`: the timezone-parameterized guard, red at base (E-06).
7. `tests/test_backlog.py`, `tests/test_history_label_parity.py`: date masks removed, actor masks kept (E-06).
8. `CHANGELOG.md`: one entry stating history dates are now UTC everywhere and filenames remain local (E-06).

## Deferred / out of scope (with reason)

- FILENAME DATE PREFIXES STAY LOCAL. `DECISIONS.md` D55 reverses an earlier UTC directive for human-facing names on an explicit UX rationale and is still current. Changing them is not in this plan's goal and would need its own maintainer decision to reverse a standing ruling.
  - Carrier-Declined: not a defect; D55 is a deliberate, current ruling and the two clocks compose as written.
- THE `aw set` FAMILY GAINS NO `--date` OVERRIDE. `backlog.run_note` and all four `specs._today` callers honor `--date`; `status_set.apply_status_change` accepts none, so the positional spellings cannot override the date even for a test. That is a real asymmetry in flag surface, but it is a feature gap rather than the clock defect, and `wy9aru` Section 7 assigns flag convergence to the dispatch Set.
  - Carrier: fcnz1r
- THE DISPATCH FORK IS NOT UNIFIED HERE. The `setdisp` Set makes both setter spellings reach one engine. This plan deliberately fixes the CLOCK IN EVERY WRITER rather than reducing the writer count, so it is correct whether `setdisp` lands before or after: if `setdisp` lands first, E-02's `_reattach_history` edit may become dead code, which E-05's audit will catch and report. Taking a dependency on a six-child pending Set would block a measured release-gated defect behind unrelated review.
  - Carrier: fcnz1r
- THE SIX SIBLING CARRIERS ARE NOT CLOSED. `fnb8pl`, `tl8qmc`, `jvw1kg`, `2wae2x`, `doe2fo` and `lq2w86` describe this same defect (F-08). This plan graduates only `7qvs1c`, the item it was authored from. Closing the others requires a per-item verdict against each item's own scope, and whether to dedupe them is a maintainer decision.
  - Carrier: fnb8pl
- THE GITIGNORED HISTORY SIDECAR IS NOT CONVERTED UNLESS E-05 FINDS A READER. `record_history.append` stamps a compact LOCAL date, but `2vev8j` 4.2 makes that file an advisory, gitignored log rather than the durable store, and nothing gates on it. E-05 gives it an explicit verdict rather than silently skipping it.
  - Carrier-Declined: no user-visible effect; the sidecar is gitignored and advisory, so a date change there is unobservable.
- THE FOUR READ-ONLY AGE COMPARISONS ARE NOT TOUCHED. `attention`, `plans_archive`, `research_archive` and `workflow_artifacts_prune` compare a stored date against today. Moving them to UTC while stored dates stay local would shift every age and archive boundary by up to a day, which is a behavior change this plan has no mandate for.
  - Carrier-Declined: not a defect; these compare rather than write, and a mixed-clock comparison would introduce an off-by-one-day error.
- THE MIGRATION OF HISTORIC RECORDS IS NOT ATTEMPTED. Records already written carry whichever clock wrote them. Rewriting committed history to assert a date that was not recorded would be a false record (GUIDING_PRINCIPLES P4).
  - Carrier-Declined: not a defect; existing records are the honest history.

## Scope check

- Over-scope: none. Every declared path is edited by a numbered item: `artifact_core.py` (E-01), `backlog.py` (E-02), `specs.py` (E-03), `releases.py` + `readiness_recheck.py` (E-04), `status_set.py` (E-01/E-05), `tests/test_history_date_clock.py` + `tests/test_backlog.py` + `tests/test_history_label_parity.py` (E-06), `CHANGELOG.md` (E-06).
- Under-scope: E-05's audit may find a history writer outside the declared set, since the inventory was measured but a search can miss a site. If it does, declare the path at execution and record the widening in the transition message, which this note authorizes. E-06 may find a third test that masks or pins a date; same treatment. The plan's own file needs no declaration (implicit lifecycle-artifact allowance, spec `ipd-structure-and-linting` Section 4.5).

## Required tests / validation

- The BARE suite: `python3 -m pytest`, with the `N passed` line pasted. Baseline is `4405 passed, 2 skipped` at HEAD `6c18c158f` (F-09); compare FAILURE SETS BY NAME, not counts.
- `tests/test_history_date_clock.py` run alone with `-o addopts=""`, every case named, demonstrated RED AT BASE (stash or revert the source edits and paste the failure) and GREEN after. A guard never seen failing proves nothing.
- The full suite run a second time under an exported `TZ=Pacific/Kiritimati` (UTC+14) and a third under `TZ=Pacific/Honolulu` (UTC-10), both pasted. These bracket UTC in both directions so one of them is always inside a skew window. This is a VALIDATION-TIME use of `TZ` to expose the bug, not a fix-time use to hide it.
- `tests/test_specs_date_containment.py` run alone under both timezones: it globs for a LOCAL compact filename date and is the guard that catches E-03 accidentally moving the spec filename to UTC. It must pass UNCHANGED; editing it to accommodate a changed filename would be reversing D55.
- `tests/test_backlog.py`, `tests/test_history_label_parity.py`, `tests/test_history_provenance.py` and `tests/test_git_commit_helper.py`, each run individually with results pasted, since E-06 edits the first two and the history writers underpin the rest.
- A manual end-to-end re-run of F-01's reproduction under `TZ=Pacific/Honolulu`: both `aw backlog set` spellings on identical fixtures must now record the SAME date, and it must equal the UTC date. Paste both records.
- A created spec and a created release inspected under a skew timezone to show the intended composition: a LOCAL filename prefix and a UTC `created` history record in the same artifact.
- `AW_NO_REEXEC=1 aw check`, `AW_NO_REEXEC=1 aw backlog check`, `AW_NO_REEXEC=1 aw specs check`, `AW_NO_REEXEC=1 aw attention --check` and `AW_NO_REEXEC=1 aw sanitize --agent`. `aw check` and `aw attention --check` exit 1 on PRE-EXISTING conditions unrelated to this plan, so the honest bar is an UNCHANGED FINDING SET: re-derive before and after and diff. Do not "fix" another plan's finding or another lane's state.
- `AW_NO_REEXEC=1 aw ipd lint --phase pre-transition` on this plan, conforming.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Verify the staged set against this plan's `Scope-Paths` before committing.

## Spec / documentation sync

No spec is amended. This plan IMPLEMENTS `2vev8j` Section 4.4, which is already `approved`, and
respects `DECISIONS.md` D55, which is already current; it changes neither contract, so no
`.spec.md` file appears in `Scope-Paths`.

Two documentation notes, both deliberate:

- `DECISIONS.md` gets NO new entry. The decision was already made (4.4) and recording it again would
  create a second authority for one ruling, which is the duplication this plan exists to remove.
- `.aw/records/plans/README.md` and `.aw/records/specs/README.md` both state that the `YYYYMMDD-HHMM`
  filename convention is local time. Those remain CORRECT under D55 and are left untouched. They are
  named here so a reviewer who greps for "local time" during review does not read them as drift this
  plan failed to update.

`CHANGELOG.md` gets one entry, because the change is user-visible in recorded history: it must say
that history dates are now UTC for every writer and that filename dates deliberately remain local.

## Open questions

### OQ-01: Which clock should an artifact's history date use, UTC or the machine's local time?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, not referred to the maintainer, because the repository has already ruled twice and the two rulings answer different questions. HISTORY DATES ARE UTC: spec `2vev8j` Section 4.4, "One timezone for every writer", states "Every writer, tool and human-facing helper alike, records UTC; local time is a RENDER-TIME concern only." That spec is `approved` and carries a human attestation (`- 2026-09-09 approved (aw set, --by-human)`). Three independent artifacts already treat it as binding: spec `4sd62s` inherits "its UTC rule (4.4)", spec `wy9aru` lists 4.4 as a constraint "CONSUMED here as settled", and executed plan `63h054` cites "spec 2vev8j 4.4" for exactly this skew. FILENAME DATES ARE LOCAL: `DECISIONS.md` D55 reverses the earlier UTC directive for human-facing names on an explicit UX rationale. The sibling item `tl8qmc` asserts the question is open and argues both sides; it is STALE, having been filed without knowledge of 4.4, and its framing additionally treats the filename date as "the same question", which it is not. Worth flagging to the maintainer (and not resolvable from evidence): `tl8qmc`'s text should be corrected, since an implementer following it would unify both clocks and silently reverse D55.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: the helper's source quoted, showing it returns a UTC `YYYY-MM-DD` and that its docstring cites `2vev8j` 4.4 AND warns that filename dates are local per D55. Plus a pasted bare-suite run equal to the `4405 passed, 2 skipped` baseline, proving the addition alone changed no behavior. If a compact variant was added, the E-05 caller requiring it must be named; if not, state that none did.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: under `TZ=Pacific/Honolulu`, a pasted backlog transition record and a pasted `created` record both showing the UTC date, with the local and UTC dates printed alongside to prove the run was inside a skew window. Plus the item's FILENAME showing the LOCAL compact date in the same output, proving the filename site was not moved. Plus `aw backlog note --date 2020-01-01` writing `2020-01-01`, proving `--date` still wins. Plus `tests/test_backlog.py` and `tests/test_history_provenance.py` results.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: a spec created under a skew timezone, with its FILENAME (local compact date) and its `created` history record (UTC date) both pasted from the same artifact, differing by one day. Plus a spec status transition recording the UTC date. Plus `tests/test_specs_date_containment.py` passing UNCHANGED under both `TZ=Pacific/Kiritimati` and `TZ=Pacific/Honolulu`, with a statement that the file was not edited (`git diff --stat` for it showing no change).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: a release record created under a skew timezone with its local filename prefix and UTC `created` line both pasted. Plus a `readiness_recheck` run recording the UTC date. Plus the new `readiness_recheck` import shown, confirming it is the only new import edge this plan adds.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the full per-site verdict table (every remaining `date.today()`-class call in `agent_workflows/`, each HISTORY/FILENAME/NEITHER with its reason), plus the command used to enumerate the sites so the census is reproducible. An explicit statement that no HISTORY writer remains on the local clock. A demonstration that `set_records.close_on_answer` records UTC by DRIVING it, not by reading it. And `aw check` / `aw backlog check` / `aw specs check` / `aw attention --check` before-and-after finding sets, proving a local filename date beside a UTC history date in one artifact trips no rule (F-07).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `tests/test_history_date_clock.py` pasted FAILING at base (with the source edits reverted) and PASSING after, each run with `-o addopts=""` and every case named, covering one timezone east and one west of UTC. The diff of both unmasked tests showing the date normalization removed and the ACTOR normalization retained. The bare suite green with its `N passed` line, plus the two whole-suite runs under `TZ=Pacific/Kiritimati` and `TZ=Pacific/Honolulu`. The F-01 reproduction re-run showing both spellings now agreeing on the UTC date. The `CHANGELOG.md` entry quoted, containing no em or en dash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries no `- Readiness:` field: that field is an OUTPUT of `/plan-review`
and writing one here would forge a review that has not happened. It requires explicit human approval
before execution.

Execution contract: commit ONLY the files this plan changed, limited to its `Scope-Paths`, through
`aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push.
Verify the staged set with `git diff --cached --name-only` before each commit and unstage anything
not this plan's with `git restore --staged <path>`; this is a shared checkout and another agent's
uncommitted work must never enter a commit here.

Validation is not optional and not inferable: every `V-*` item demands pasted output from a command
actually run. In particular, a claim that the fix works is NOT acceptable on a green suite alone,
because the suite is green at base while the defect is live (F-05). The new guard MUST be
demonstrated failing before the fix.

Post-gate lifecycle: on completion, run `aw ipd lint --phase pre-transition` to conforming, then move
this plan to `.aw/records/plans/executed/` through the tooled lifecycle transition. Do not hand-edit
the terminal state. Backlog item `7qvs1c` is handed off via `- From-Backlog:` and should reach
`graduated`, not `done`: this plan carries its `- Blocks-Release: next` gate, and the gate is
released only when this plan is `executed`.
