# IPD: Give the UTC history-date ruling a durable cross-spelling guard that covers every artifact family, not just backlog

- Date: 2026-10-01
- Kind: child
- Concern: Spec `2vev8j` Section 4.4 rules that every history writer records UTC, and the repository violates it on TWO artifact families, not the one the eight filed items describe. Measured live in this lane inside the skew window (local `2026-10-01`, UTC `2026-10-02`): `aw backlog set <path> --status open` wrote `- 2026-10-01 same-status (aw backlog): m` while `aw backlog set open <id6>` wrote `- 2026-10-02 same-status (aw set): m`; AND `aw specs set <path> --status to-review` wrote `- 2026-10-01 to-review (aw specs): m` while `aw set to-review <id6>` wrote `- 2026-10-02 to-review (aw set): m`. The SPEC divergence is in none of the eight items and in no plan's `Scope-Paths`. Worse, the suite CANNOT see any of it: `tests/test_history_label_parity.py` and `tests/test_backlog.py` both substitute the date away before comparing, zero test in `tests/` calls `time.tzset()` or sets `TZ`, and both files measured `51 passed` at HEAD `0c8ba47ed` while the defect was live on two families. So the behavioral fix plan `5ivkdh` can land, be validated against a green suite, and silently regress with nothing to catch it. UPDATE AT REVIEW 2026-10-07: `5ivkdh` HAS EXECUTED and itself removed those two masks and shipped a hand-listed TZ guard (F-10); what remains for this plan is the DERIVED-surface guard, the cross-spelling agreement assertion, and a third mask (F-11).
- Scope: IN: one timezone-parameterized differential guard that derives the history-writing surface from `command_surface.COMMAND_INVENTORY` rather than hand-listing it, drives every derived spelling under a timezone east AND west of UTC, and asserts the recorded history date equals the UTC date; plus removal of the date MASK from the two tests that hide this today. OUT, each with a reason recorded under "Deferred": the production clock fix itself (owned by `5ivkdh`, which this plan takes a hard dependency on); filename dates, which `DECISIONS.md` D55 rules LOCAL; the actor asymmetry; the dispatch unification; closing the seven sibling items.
- Scope-Paths: tests/test_history_date_clock_parity.py, tests/test_history_label_parity.py, tests/test_backlog_history_dedup_parity.py
- Item-Dependencies: executed:5ivkdh
- Status: executed
- Readiness: go-pending-approval
- From-Spec: 2vev8j
- Work-Kind: bug
- Priority: medium
- From-Backlog: a2zpzq
- Blocks-Release: next
- Set: a2zpzq
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: ayhveg

## Workflow history
- 2026-10-07 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: ayhveg verified (set a2zpzq, attempt 1).
- 2026-10-07 approved (aw set): status set to approved

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-100, PR-101, PR-102, PR-103, PR-104. Reviewed at HEAD `fe2ee961c` in an isolated review lane; plan committed and byte-identical to the lane input, so no pre-review snapshot. The hard dependency `5ivkdh` is EXECUTED (`3c55295a3`) and had already removed both masks E-04 targeted and shipped a hand-listed TZ guard `tests/test_history_date_clock.py`; `57 passed` over that file plus the two former masked files. Re-scoped: E-04 now removes the THIRD mask in `tests/test_backlog_history_dedup_parity.py` (measured green with the mask disabled inside a live skew window) and fixes one stale comment; `tests/test_backlog.py` dropped from Scope-Paths (PR-100). E-03 now extends rather than duplicates the shipped guard (PR-101). E-01 prefers subprocess `env=` TZ as both shipped TZ suites do (PR-102). RED-AT-BASE re-specified as a detached scratch worktree at `3c55295a3^` instead of stash/revert in a shared checkout, demonstrated by running the shipped guard there (fails `'2026-10-06' not found in {'2026-10-07'}`) (PR-103). Carrier-Evidence added for finished carrier `7qvs1c` (PR-104). Also measured: `backlog note`, `specs note` and the positional `aw set` for specs already record UTC under Honolulu.
- 2026-10-07 reviewed (aw set): plan-review: re-scoped after 5ivkdh executed; PR-100..PR-103
- 2026-10-02 same-status (aw set): Record the From-Spec link to 2vev8j, whose Section 4.4 this plan enforces (closes the check.plan-spec-link-missing advisory).

- 2026-10-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `a2zpzq`. The clock question was RESOLVED from repository evidence (spec `2vev8j` 4.4, approved and human-attested, rules history dates UTC; `DECISIONS.md` D55 rules filename dates LOCAL), so no maintainer decision is required to proceed. Both the backlog AND the previously-unreported spec divergence were reproduced end to end in this lane at HEAD `0c8ba47ed` inside a live skew window; `tests/test_history_label_parity.py` plus `tests/test_backlog.py` measured `51 passed` at the same instant, which is the finding that motivates this plan.
- 2026-10-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the UTC history-date ruling ENFORCED rather than merely implemented, by replacing the masks that
hide clock skew with one derived, timezone-parameterized guard that fails whenever any history writer
on any artifact family drifts back onto the local clock.

This plan writes NO production code. It is the test half of a defect whose production half is
`5ivkdh`, and it exists because that plan's own validation would otherwise rest on a suite that
provably cannot observe the bug.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: make a skew window reachable from a test at all

- [x] E-01 Build the timezone-skew harness in a new `tests/test_history_date_clock_parity.py` and prove it can observe a skew window on demand, independent of the wall-clock hour the suite happens to run at. This is its own item because EVERY later item depends on it and because it is the part most likely to produce a FALSE GREEN: a guard that silently never enters a skew window passes forever while proving nothing.

    USE A TIMEZONE PAIR, NOT ONE TIMEZONE, AND THE REASON IS ARITHMETIC. A single fixed offset only disagrees with UTC for part of the day, so a one-timezone guard is green for most of a day whatever the bug. `Pacific/Kiritimati` (UTC+14) and `Pacific/Honolulu` (UTC-10) bracket UTC in both directions and are 24 hours apart, so AT LEAST ONE of them is always inside a skew window. Assert that property as a PRECONDITION of the harness rather than assuming it: compute the local date under each and require that at least one differs from the UTC date, failing loudly if neither does, because that would mean the harness lost its ability to detect anything.

    SET `TZ` FOR THE CODE UNDER TEST ONLY, PREFERABLY IN A SUBPROCESS. The shipped sibling guard `tests/test_history_date_clock.py` (from `5ivkdh`) and `tests/test_history_date_clock_readers.py` (from `840y6i`) both pass `TZ` in a CHILD process's `env=` (`subprocess.run([sys.executable, "-m", "agent_workflows", ...], env={**os.environ, "TZ": zone, "AW_NO_REEXEC": "1"})`), which leaves the pytest worker's process-global time state untouched. Reuse that shape (plan-review 2026-10-07, PR-102). If an in-process `os.environ["TZ"]` plus `time.tzset()` is used instead, it MUST sit inside a context manager with an unconditional restore (including a second `time.tzset()`) in `finally`, since `tzset()` mutates PROCESS-GLOBAL state and the suite runs under `pytest-randomly` with `-n auto`. Do NOT export `TZ` for the suite as a whole; that would hide the bug behind an environment variable.
    THE SKEW-WINDOW PRECONDITION MUST BE COMPUTED FOR THE SAME INSTANT THE ASSERTION USES. Compute each zone's local date in the same child-process style (or via `zoneinfo.ZoneInfo(zone)` on one `datetime.now(timezone.utc)` reading), and tolerate a UTC midnight crossing during the run the way `test_history_date_clock._expected_utc_dates` does.
  - Depends on: none
  - Expected outcome: `tests/test_history_date_clock_parity.py` holds a reusable timezone-scoped runner (subprocess `env=`, or an in-process context manager with guaranteed restore) plus a self-check case asserting that at least one of the two timezones is inside a skew window, and, for the in-process form only, that `TZ` is restored to its prior value after use; the file runs green; no production file is touched.
  - Execution state: performed

### Task group 2: derive the surface instead of hand-listing it

- [x] E-02 Derive the set of history-writing spellings from `command_surface.COMMAND_INVENTORY` rather than hard-coding a list, and assert the derivation is non-empty and covers every artifact family that has a typed setter. This item is the difference between a guard that catches THIS defect and one that catches the NEXT one: the measured failure mode of the eight filed items is that each names only the backlog pair, and the spec pair diverged identically while nobody was looking.

    THE REGISTRY IS ALREADY AUTHORITATIVE AND MACHINE-READABLE. Re-measured at review HEAD `fe2ee961c`: `command_surface.COMMAND_INVENTORY` is a tuple of `CommandDeclaration` (fields include `command`, `command_class`, `mutation_gate`, `canonical_command`), and filtering for a last word of `set`/`note` yields `set` (the bare `aw set`), `ipd set`, `backlog set`, `backlog note`, `specs set`, `specs note`, `prompts set`, `config set`, `ipd dependencies set`, plus the `spec set`/`spec note` aliases (`command_class='alias'`, `canonical_command` naming the target). Filter on `command_class == 'mutation'` and resolve aliases through `canonical_command` rather than exercising them twice. Deriving from it means a NEW typed setter added later is covered the day it is declared, with no edit to this test. Hand-listing reproduces, in the guard, the very omission that let the spec divergence survive.

    ASSERT A NON-VACUITY FLOOR, NOT AN EXACT CENSUS. Require that the derived set contains AT LEAST the backlog and specs setters and that it is non-empty, so a filter bug that silently matches nothing fails the test. Do NOT assert an exact count: that is a census pin (GUIDING_PRINCIPLES P16) and it would turn every legitimate new command into a false failure.

    SKIP, WITH A RECORDED REASON, ANY DERIVED SPELLING THAT WRITES NO HISTORY RECORD. `config set` is not an artifact verb, and `ipd dependencies set` edits a dependency field; verify by driving it whether it appends a history record before skipping it. `prompts set` routes to `status_set` and so is expected to be UTC already, so it is EXERCISED, not skipped; the test must report which spellings it exercised and which it skipped and why, so a reader can tell a deliberate exclusion from a silent miss.
  - Depends on: E-01
  - Expected outcome: the test derives its target spellings from `COMMAND_INVENTORY`, asserts a non-vacuity floor including both the backlog and specs setters, exercises each derived history-writing spelling, and reports its exercised and skipped sets; no spelling is named by a hard-coded literal list.
  - Execution state: performed

### Task group 3: assert the ruling on every family

- [x] E-03 Assert, for every derived spelling under both timezones, that the history record's date equals the UTC date, and that the two spellings of one family agree with EACH OTHER. Two assertions rather than one, because they fail differently and a reviewer needs to tell them apart: agreement alone would be satisfied by both spellings being wrong in the same direction, and UTC-equality alone would not catch a family whose two spellings drift apart on some other axis.

    ASSERT ON THE WRITTEN ARTIFACT, NEVER ON THE SOURCE. Read the date out of the `## Workflow history` record in the file the CLI actually wrote. Do NOT assert that any module calls `datetime.timezone.utc`: that is a code-structure pin, forbidden outright by GUIDING_PRINCIPLES P16 ("Never use `inspect.getsource` ... `ast.parse`, `read_text()`, or substring/regex searches against production code") and by `AGENTS.md`'s no-code-pinning rule, and `5ivkdh` E-06 already applies that ruling to this exact property.

    COVER BOTH THE TRANSITION AND THE SAME-STATUS RECORD. The measured reproduction used a same-status write, which is the case the positional spelling deduplicates; a genuine transition exercises a different branch. Both write a dated record, so both are in scope for the clock.

    DO NOT ASSERT ON THE FILENAME DATE. `DECISIONS.md` D55 rules human-facing filename prefixes LOCAL, so inside a skew window a correct artifact legitimately carries a local filename date and a UTC history date one day apart. Positively assert that composition on at least one family rather than leaving it implicit, so a future reader does not "fix" the apparent inconsistency and reverse D55.
    DO NOT DUPLICATE THE SHIPPED PER-FAMILY GUARD; EXTEND IT. `5ivkdh` (EXECUTED) already shipped `tests/test_history_date_clock.py`, which under both timezones drives `backlog set` (both spellings), `backlog new`, `specs set --status`, `specs new` and `releases new` and asserts a UTC history date plus a LOCAL filename prefix. That file is HAND-LISTED and is NOT in this plan's `Scope-Paths`, so leave it untouched. What this plan adds is exactly what that file lacks: DERIVED coverage (so `backlog note`, `specs note`, `ipd set`, `prompts set`, the bare `aw set` positional spelling for specs, and any later setter are covered), and the cross-spelling AGREEMENT assertion. The local-filename/UTC-history composition is already pinned there for three families, so E-03's composition case may cite it instead of repeating it, but must still assert it once for a family the derived set reaches (plan-review 2026-10-07, PR-101).
  - Depends on: E-02
  - Expected outcome: every derived spelling records the UTC date under both timezones; the two spellings of the backlog family and of the specs family each agree with one another; one case positively asserts a LOCAL filename prefix beside a UTC history record in the same artifact; every case is individually named in the run output.
  - Execution state: performed

### Task group 4: remove the masks that hid this

- [x] E-04 Remove the REMAINING date mask, keeping every ACTOR mask intact. AT AUTHORING two tests masked the date: `tests/test_history_label_parity.py`'s `_normalize_history_record` and `tests/test_backlog.py`'s cross-spelling parity case. `5ivkdh` (EXECUTED, commit `3c55295a3`) has ALREADY removed both masks and rewritten their comments and the label-parity module docstring, so those two edits are DONE and must not be repeated (plan-review 2026-10-07, PR-100). What remains, re-measured at review HEAD `fe2ee961c`:
    (a) A THIRD mask the plan did not list: `tests/test_backlog_history_dedup_parity.py` `_DATE_RE = re.compile(r"-\s+\d{4}-\d{2}-\d{2}\s+")` and `_normalize_history_record` substitute `- <DATE> ` for the date, and its module docstring and helper docstring both say the date is normalized "so local vs UTC clock differences ... do not produce false parity failures". Remove the date substitution, keep `_ACTOR_PAREN`, and rewrite both docstrings to say dates are compared literally per spec `2vev8j` 4.4. Measured at review inside a live skew window (TZ=Pacific/Honolulu, local 2026-10-06, UTC 2026-10-07), that module's six tests pass with the date regex disabled, so removal is expected green.
    (b) One stale comment left by `5ivkdh`: `tests/test_history_label_parity.py` still reads `# Normalized comparison (hiding actor and date skew)` above the graduated-record comparison. Correct it to name the actor only.
    Re-derive at execution with `rg -n "HIST_DATE|<DATE>|date skew|by shape" tests/` and treat any further hit the same way, declaring its path at finalize.

    REMOVE ONLY THE DATE NORMALIZATION. The actor difference (`(aw backlog)` versus `(aw set)`) is deliberate and truthfully identifies the writer, as both comments state, and is owned elsewhere. Deleting the actor mask would make these tests fail for a reason this plan is not fixing, and would invite an executor to "fix" a correct behavior.

    UPDATE EACH MASK'S COMMENT AND DOCSTRING IN THE SAME EDIT. A stale comment asserting a mask that no longer exists is worse than no comment: the next reader trusts it and re-adds the mask.
  - Depends on: E-03
  - Expected outcome: `tests/test_backlog_history_dedup_parity.py` compares history dates LITERALLY while still normalizing the actor, with its module and helper docstrings rewritten; the stale `hiding actor and date skew` comment in `tests/test_history_label_parity.py` names the actor only; the re-derivation `rg` returns no date-mask hit in `tests/`; all touched files pass; the bare suite is green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- OUTCOME TESTS ONLY (`AGENTS.md`, GUIDING_PRINCIPLES P16). This plan is ENTIRELY a test plan, which makes P16 its governing constraint rather than a footnote: the UTC property must be proven by the date in a written artifact, never by scanning `agent_workflows/*.py` for a `timezone.utc` token. P16's prohibition on `read_text()` and `ast.parse` against production code is unconditional and is not rescued by its narrow exception, which covers only artifacts that ARE text under test.
- NO CENSUS PINS (GUIDING_PRINCIPLES P16, "No count or census pins"). E-02 therefore asserts a non-vacuity FLOOR over the derived command set rather than an exact count, since an exact count would fail on every legitimately added command.
- Run the suite BARE: `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and deselects `slow`/`livecorpus`; `-n0` is forbidden here, a second `-q` suppresses the `N passed` line this plan requires pasted, and `-p no:randomly` would disable the order randomization that makes E-01's `TZ`-leak concern real. Use `-o addopts=""` only when a narrowed run needs per-test counts.
- `-n auto` PLUS `pytest-randomly` IS WHY `tzset()` DISCIPLINE IS LOAD-BEARING, not pedantry: `time.tzset()` mutates process-global state shared by every test in a worker, and random ordering means a leak surfaces as an unrelated test failing on some runs and not others.
- `aw` re-execs into the checkout's own package unless `AW_NO_REEXEC=1` is set; inside a lane worktree it prints a notice naming both paths. Set `AW_NO_REEXEC=1` on every `aw` invocation so the lane's own code runs and the notice does not pollute pasted evidence.
- DERIVE A VALUE, NEVER RE-LIST IT (GUIDING_PRINCIPLES P8). This is E-02's whole justification: the eight filed items each hand-listed the backlog pair and all eight missed the spec pair, so a hand-listed guard would reproduce the omission it exists to prevent.
- A release-blocking backlog item CANNOT be closed casually: `aw backlog set done` fails closed on an item carrying `- Blocks-Release:` unless the gate is HANDED OFF, SATISFIED with a resolvable in-tree citation, or explicitly DE-GATED. This plan closes nothing; the runner sets `a2zpzq` to `graduated` on the `From-Backlog` handoff.

## Findings

Established in this lane at HEAD `0c8ba47ed`, by driving the CLI inside a live skew window (machine local `2026-10-01`, UTC `2026-10-02`) rather than by reading code alone.

| # | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH (THE DEFECT, MEASURED ON TWO FAMILIES) | Two `cli.main` calls per family on identical fixtures. BACKLOG: `backlog set <path> --status open` wrote `- 2026-10-01 same-status (aw backlog): m`; `backlog set open aa0001` wrote `- 2026-10-02 same-status (aw set): m`. SPECS: `specs set <path> --status to-review` wrote `- 2026-10-01 to-review (aw specs): m`; `set to-review bb0002` wrote `- 2026-10-02 to-review (aw set): m`. All four exited 0. | **THE DIVERGENCE IS NOT BACKLOG-ONLY.** Every one of the eight filed items names only `backlog.py` versus `status_set.py`, and the SPEC pair diverges identically. This is the finding that makes this plan additive rather than a duplicate: a fix validated only against the backlog pair leaves a second family silently broken. |
| F-02 | HIGH (THE SUITE CANNOT SEE IT) | At the same instant as F-01, with the defect live on two families: `python3 -m pytest tests/test_history_label_parity.py tests/test_backlog.py -o addopts="" -q` reported `51 passed in 7.07s`. | **"TESTS PASS" IS WORTHLESS EVIDENCE FOR THIS DEFECT**, so `5ivkdh` cannot be validated on a green suite and this plan's guard must be demonstrated RED before the fix. The green is not luck: the two files substitute the date away before comparing. |
| F-03 | HIGH (ZERO TIMEZONE COVERAGE EXISTS) | A search of `tests/*.py` for `tzset(` returns ZERO matches; a search for `TZ=` or `timezone.utc` matches five files, none of which exercises a setter (`test_comms_acks.py`, `test_comms_broker.py`, `test_comms_broker_registry.py`, `test_host_capability_registry.py`, `test_run_viewer.py`). | **NO TEST IN THE REPOSITORY CAN ENTER A SKEW WINDOW ON PURPOSE.** So the defect's visibility is left to the wall-clock hour CI happens to run at, which is why it survived eight filings. E-01 exists to build that capability, and it is a genuinely new test capability rather than an extension of an existing one. |
| F-04 | HIGH (THE SURFACE IS DERIVABLE) | `command_surface.COMMAND_INVENTORY` holds 163 declarations; filtering for setter/note verbs yields `ipd set`, `backlog set`, `backlog note`, `specs set`, `specs note`, `prompts set`, plus the `spec set`/`spec note` aliases, each with a `command_class` and `mutation_gate`. | **THE GUARD CAN ENUMERATE ITS OWN TARGETS, so it covers a setter added AFTER it is written.** Given F-01, a hand-listed guard is not a neutral style choice: hand-listing is the measured cause of the spec family being missed eight times. |
| F-05 | MEDIUM (ONLY TWO FAMILIES FORK) | Reading the dispatch per family: `backlog set` forks on `--status` (flag branch to `backlog_mod.run_set`, else `status_set.run_set_command`) and `specs set` forks the same way; `ipd set` and `prompts set` route UNCONDITIONALLY to `status_set.run_set_command`; `releases` has no `set` verb. | **THE BLAST RADIUS IS EXACTLY TWO FAMILIES, NOT ALL OF THEM**, which bounds this plan honestly and stops it claiming a sweep it did not make. It also predicts that `ipd set` and `prompts set` are ALREADY UTC, which E-02 verifies by driving them rather than assuming. |
| F-06 | MEDIUM (THE SPLIT-ROLE TRAP) | `specs._today` is called from four sites; the `run_new` call feeds BOTH the `- Date:` front matter and, via a compact form, the spec FILENAME. `DECISIONS.md` D55 rules human-facing filename prefixes LOCAL. `tests/test_specs_date_containment.py::test_non_regression_omitted_date_defaults_today` computes `dt.date.today()` LOCALLY and globs for that compact prefix. | **A GUARD THAT ASSERTS "EVERY DATE IS UTC" WOULD DEMAND A D55 VIOLATION.** This is why E-03 asserts on the HISTORY RECORD only and positively asserts the local-filename/UTC-history composition. It is also why this plan must not touch `test_specs_date_containment.py`: that test is the tripwire catching a filename wrongly moved to UTC. |
| F-07 | MEDIUM (THE PRODUCTION FIX IS ALREADY OWNED) | At authoring, `.aw/records/plans/pending/20261001-7qvs1c-01-5ivkdh-...ipd.md` was `to-review` (now in `executed/`, F-10), `Blocks-Release: next`, `From-Backlog: 7qvs1c`, and declares `artifact_core.py`, `backlog.py`, `specs.py`, `status_set.py`, `releases.py`, `readiness_recheck.py` in `Scope-Paths`. Its E-01 adds the shared UTC helper; `artifact_core` has no such helper today (a probe of its namespace returns only `shard_for_date`). | **THIS PLAN MUST NOT REIMPLEMENT THE FIX**, so it declares NO production path and takes `Item-Dependencies: executed:5ivkdh`. Authoring the guard to run BEFORE that plan lands would make it red on arrival on two families, which is a broken queue item rather than a useful guard. |
| F-08 | LOW (EIGHT DUPLICATE FILINGS) | Eight open, release-gated, `Work-Kind: bug` items describe this one defect: `a2zpzq`, `7qvs1c`, `fnb8pl`, `tl8qmc`, `jvw1kg`, `2wae2x`, `doe2fo`, `lq2w86`, `o8l2y2`. `- From-Backlog:` is single-valued (`releases._ITEM_FROM_BACKLOG_RE` matches one token, and its own comment contrasts this with the multi-valued `- Graduated-To:`), and `check_engine.evaluate_blocking_close`'s HANDOFF route resolves carriers for ONE item id6. | **ONE DEFECT GATES THE RELEASE EIGHT TIMES AND THE HANDOFF ROUTE CANNOT DISCHARGE MORE THAN ONE ITEM PER PLAN.** So the remaining items need either a per-item `--evidence` citation or an explicit de-gate, which is a maintainer call. This plan closes none of them and raises it under "Deferred". |
| F-10 | HIGH (THE DEPENDENCY LANDED AND ABSORBED HALF THIS PLAN) | Re-measured at review HEAD `fe2ee961c`: `5ivkdh` is in `.aw/records/plans/executed/`; its commit `3c55295a3` removed the date masks from `tests/test_backlog.py` and `tests/test_history_label_parity.py` (including the module docstring) and added `tests/test_history_date_clock.py`, a hand-listed six-case guard over `backlog set` (both spellings), `backlog new`, `specs set --status`, `specs new`, `releases new` under `Pacific/Kiritimati` and `Pacific/Honolulu`. `python3 -m pytest -o addopts="" -q tests/test_history_date_clock.py tests/test_history_label_parity.py tests/test_backlog.py` -> `57 passed`. | **E-04 AS AUTHORED WAS ALREADY DONE AND E-03 OVERLAPPED A SHIPPED GUARD.** The plan's remaining value is the DERIVED surface (E-02), the cross-spelling AGREEMENT assertion, and the THIRD mask in `tests/test_backlog_history_dedup_parity.py`. Revised accordingly. |
| F-11 | MEDIUM (A THIRD MASK, AND IT IS SAFE TO REMOVE) | `tests/test_backlog_history_dedup_parity.py` `_DATE_RE` and `_normalize_history_record` substitute `- <DATE> `. With the regex disabled under TZ=Pacific/Honolulu inside a live skew window (local 2026-10-06, UTC 2026-10-07), its tests reported `ran 6 fail 0 err 0`. | **THE MASK NO LONGER HIDES A LIVE DEFECT BUT STILL WOULD HIDE A REGRESSION**, so removing it is now cheap and green. |
| F-12 | MEDIUM (THE UNCOVERED SPELLINGS ARE ALREADY UTC) | Driven at review under TZ=Pacific/Honolulu (local 2026-10-06, UTC 2026-10-07): `aw backlog note <path> --message notez` wrote `- 2026-10-07 note (aw backlog): notez`; `aw specs note <path> --message notez` wrote `- 2026-10-07 note (aw specs): notez`; `aw set to-review sp0001 --message posz` wrote `- 2026-10-07 to-review (aw set): posz`. | **THE DERIVED GUARD IS NOT EXPECTED TO BE RED ON ARRIVAL.** If it is, the plan's gate already says the fix belongs in production under a corrective plan, not in the test. |
| F-09 | N/A (STALENESS CORRECTION) | `tl8qmc` and `fnb8pl` both assert the parity test FAILS inside the skew window. Measured here INSIDE the skew window: it PASSES (F-02), because the date mask was added after those items were filed. | **THE TWO DIAGNOSTIC ITEMS ARE NOW STALE ON THEIR HEADLINE SYMPTOM**, and an implementer trusting them would look for a red test that no longer exists and might conclude the defect was fixed. Recorded so review does not re-derive it. |

## Proposed changes (ordered, validatable)

1. `tests/test_history_date_clock_parity.py`: the timezone context manager with guaranteed restore, plus the skew-window self-check (E-01).
2. Same file: the `COMMAND_INVENTORY`-derived target set with a non-vacuity floor and a reported exercised/skipped split (E-02).
3. Same file: the UTC-equality and cross-spelling agreement assertions over both timezones, plus the positive local-filename/UTC-history composition case (E-03).
4. `tests/test_backlog_history_dedup_parity.py`: date mask removed, actor mask kept, docstrings corrected (E-04 (a)).
5. `tests/test_history_label_parity.py`: the one stale `date skew` comment corrected (E-04 (b)). The two masks this plan originally targeted were already removed by `5ivkdh`.

No production file is edited, and none is declared in `Scope-Paths`. That is deliberate per F-07.

## Deferred / out of scope (with reason)

- THE PRODUCTION CLOCK FIX IS NOT MADE HERE. `5ivkdh` owns it and is now EXECUTED (F-10). This plan is its enforcement half and depends on it.
  - Carrier: 7qvs1c
  - Carrier-Evidence: .aw/records/plans/executed/20261001-7qvs1c-01-5ivkdh-unify-every-artifact-history-date-onto-the-utc-clock-ruled-b.ipd.md
- FILENAME DATE PREFIXES ARE NOT ASSERTED AS UTC. `DECISIONS.md` D55 rules human-facing names LOCAL on an explicit UX rationale and is current. E-03 asserts the local filename beside the UTC history record rather than treating the difference as a defect.
  - Carrier-Declined: not a defect; D55 is a deliberate, current ruling and the two clocks compose as written.
- `tests/test_specs_date_containment.py` IS NOT EDITED. It is the tripwire that catches a spec filename wrongly moved to UTC (F-06). Editing it to accommodate a changed filename would reverse D55; it must pass UNCHANGED.
  - Carrier-Declined: not a defect; the test is correct and is load-bearing for D55.
- THE ACTOR ASYMMETRY IS NOT FIXED. `(aw backlog)` versus `(aw set)` truthfully identifies the writer, both existing masks say so deliberately, and E-04 keeps that mask.
  - Carrier: fcnz1r
- THE DISPATCH FORK IS NOT UNIFIED. The `setdisp` Set (children 00-05, pending) moves both `--status` spellings onto the shared engine, and its child `afdmn6` builds a cross-spelling differential harness for roughly forty axes. This plan is compatible in either order and deliberately does NOT depend on that Set: `afdmn6` normalizes the date by SHAPE (it is explicitly a tests-only harness for axes that already agree), so it does not assert the clock and does not subsume this guard. If `setdisp` lands first, the fork disappears and this guard still holds, because it asserts an OUTCOME per spelling rather than a code path.
  - Carrier: fcnz1r
- NO `aw check` RULE IS ADDED. A source-scanning rule was considered and rejected on measured grounds: a `date.today()` call site cannot be classified HISTORY versus FILENAME versus read-only age comparison from the call alone (F-06 shows one value serving two roles), which is the same false-positive problem that got backlog item `ku8szz` deferred rather than built. A rule scanning `agent_workflows/*.py` is also meaningless in a managed TARGET repository, which is the objection plan `76ic0k` records against exactly this mechanism.
  - Carrier-Declined: not a defect; the outcome assertion in E-03 covers the property without a source scan, and a token-keyed rule would be mostly false positives.
- THE SEVEN SIBLING ITEMS ARE NOT CLOSED. `7qvs1c`, `fnb8pl`, `tl8qmc`, `jvw1kg`, `2wae2x`, `doe2fo`, `lq2w86` and `o8l2y2` describe this same defect (F-08), and the single-valued `- From-Backlog:` field cannot hand off more than one item per carrier. This plan graduates only `a2zpzq`.
  - Carrier: fnb8pl
- THE TWO STALE ITEM DESCRIPTIONS ARE NOT REWRITTEN. `tl8qmc` and `fnb8pl` claim a test failure that no longer occurs (F-09). Editing another item's recorded diagnosis is a records change this plan has no mandate for, and the honest route is a note from whoever owns dedup.
  - Carrier: fnb8pl

## Scope check

- Over-scope: none. Every declared path is edited by a numbered item: `tests/test_history_date_clock_parity.py` (E-01, E-02, E-03) and `tests/test_backlog_history_dedup_parity.py` plus `tests/test_history_label_parity.py` (E-04). `tests/test_backlog.py` was dropped from `Scope-Paths` at review because `5ivkdh` already made its edit. No production path is declared, which is itself the scope decision F-07 records.
- Under-scope: E-02's derivation may surface a history-writing spelling outside the two families measured in F-01 (for example a typed setter added between authoring and execution). If it does, exercise it, and record the widening in the transition message; this note authorizes that, and the derived-surface design is what makes it cheap. E-04 may find a THIRD test masking a history date; same treatment, declaring the path at execution. The plan's own file needs no declaration (implicit lifecycle-artifact allowance, spec `ipd-structure-and-linting` Section 4.5).

## Required tests / validation

- The BARE suite: `python3 -m pytest`, with the `N passed` line pasted. Establish the baseline at the executing HEAD rather than trusting a number from this document: `5ivkdh` lands first and changes the tree, so a count copied from here would be stale. Compare FAILURE SETS BY NAME, not counts.
- `tests/test_history_date_clock_parity.py` run alone with `-o addopts=""`, every case named, demonstrated RED AT BASE and GREEN after. "At base" means a DETACHED SCRATCH WORKTREE at `3c55295a3^` (the parent of `5ivkdh`'s commit) with the new test file copied in: `git worktree add --detach <scratch> 3c55295a3^`, run, then `git worktree remove --force <scratch>`. Never revert or `git stash` production edits in the working checkout, which is shared. Demonstrated feasible at review: the shipped `tests/test_history_date_clock.py` copied into such a worktree fails with `'2026-10-06' not found in {'2026-10-07'} : Under Pacific/Honolulu, backlog created line wrote 2026-10-06`. Paste the failure showing a LOCAL date where UTC was required, for BOTH the backlog and the specs family. A guard never seen failing proves nothing, and per F-02 a green suite is not evidence here.
- The new guard run a second time with the two timezones SWAPPED in the parameterization, confirming the result does not depend on which of the pair is tried first.
- The new guard's skew-window self-check (E-01) demonstrated firing: temporarily narrow the timezone pair to UTC alone and paste the loud failure, proving the harness refuses to pass vacuously when no skew window exists. Restore the pair afterwards.
- A `TZ`-leak check: run the new file together with `tests/test_specs_date_containment.py` in ONE process (`-o addopts=""`, no xdist) and paste the result, proving the context manager restored `TZ` and did not corrupt a neighbor that depends on the local clock.
- The full suite run under an exported `TZ=Pacific/Kiritimati` and again under `TZ=Pacific/Honolulu`, both pasted. These bracket UTC in both directions so one run is always inside a skew window. This is a VALIDATION-TIME use of `TZ` to EXPOSE the defect, never a fix-time use to hide it.
- `tests/test_specs_date_containment.py` run alone under both timezones, passing UNCHANGED, with `git diff --stat` for it showing no change (F-06).
- `tests/test_backlog_history_dedup_parity.py`, `tests/test_history_label_parity.py`, `tests/test_backlog.py`, `tests/test_history_date_clock.py` and `tests/test_history_provenance.py` each run individually with results pasted; E-04 edits the first two, and the shipped `5ivkdh` guard must still pass alongside the new one.
- A manual end-to-end re-run of F-01's reproduction on BOTH families under a skew timezone: all four invocations must now record the SAME date, equal to the UTC date. Paste all four records.
- `AW_NO_REEXEC=1 aw check`, `AW_NO_REEXEC=1 aw backlog check`, `AW_NO_REEXEC=1 aw specs check`, `AW_NO_REEXEC=1 aw attention --check` and `AW_NO_REEXEC=1 aw sanitize --agent`. `aw check` and `aw attention --check` exit 1 on PRE-EXISTING conditions unrelated to this plan, so the honest bar is an UNCHANGED FINDING SET: re-derive before and after and diff. Do not "fix" another plan's finding or another lane's state.
- `AW_NO_REEXEC=1 aw ipd lint --phase pre-transition` on this plan, conforming.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Verify the staged set against this plan's `Scope-Paths` before committing.

## Spec / documentation sync

No spec is amended and no `.spec.md` file appears in `Scope-Paths`. This plan ENFORCES spec `2vev8j`
Section 4.4, which is already `approved` and human-attested, and respects `DECISIONS.md` D55, which is
already current. It changes neither contract.

No `CHANGELOG.md` entry. The user-visible behavior change (history dates becoming UTC everywhere) is
`5ivkdh`'s to announce, and this plan adds test coverage only; a second entry for one change would
misreport two changes to a reader.

`DECISIONS.md` gets no new entry, for the same reason: the decision was already made in 4.4, and
recording it again would create a second authority for one ruling.

## Open questions

### OQ-01: Which clock should an artifact's history date use, UTC or the machine's local time?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE rather than referred to the maintainer, because the repository has already ruled twice and the two rulings answer DIFFERENT questions. HISTORY DATES ARE UTC: spec `2vev8j` Section 4.4, titled "One timezone for every writer", states "Every writer, tool and human-facing helper alike, records UTC; local time is a RENDER-TIME concern only." That spec is `approved` and carries a human attestation. FILENAME DATES ARE LOCAL: `DECISIONS.md` D55 reverses the earlier UTC directive for human-facing names on an explicit UX rationale and is current. The sibling item `tl8qmc` asserts the question is still open and argues both sides; it is stale, having been filed without knowledge of 4.4, and it additionally treats the filename date as "part of the same question", which D55 settles the other way. This plan therefore enforces a ruling rather than making one.

### OQ-02: Should this guard have been a source-scanning `aw check` rule instead of a test?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AGAINST A CHECK RULE, on three measured grounds, and recorded here because it is the first alternative a reviewer will propose. FIRST, THE CLASSIFICATION IS NOT DECIDABLE FROM THE CALL SITE: `date.today()` appears in history writers, in filename builders that D55 requires stay local, and in read-only age comparisons, and `specs.run_new` derives BOTH a filename and a history date from ONE value (F-06). A token-keyed rule would be mostly false positives, which is exactly why backlog item `ku8szz` was DEFERRED rather than built after an AST sweep found 258 token sites of which all 15 bare comparisons belonged to other vocabularies. SECOND, `aw check` RUNS AGAINST MANAGED TARGET REPOSITORIES (`--dir`), so a rule scanning `agent_workflows/*.py` is meaningless there and would impose this repository's internal policy on a codebase that never adopted it; plan `76ic0k` records this objection against this same mechanism. THIRD, A SOURCE-SCANNING TEST IS FORBIDDEN OUTRIGHT by GUIDING_PRINCIPLES P16, and `5ivkdh` E-06 already applies that ruling to this property. The outcome assertion in E-03 proves the same property from the written artifact, which is both permitted and strictly stronger evidence than a token's presence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: the timezone-scoped runner's source quoted, showing either `TZ` passed only in a child process's `env=` or, for an in-process form, `time.tzset()` called inside a context manager with `TZ` restored (and `tzset()` re-called) in a `finally`. Plus the self-check case demonstrated FIRING: paste the loud failure produced when the timezone pair is temporarily narrowed to UTC alone, proving the harness refuses a vacuous pass, and state that the pair was restored. Plus the single-process co-run with `tests/test_specs_date_containment.py` pasted, proving no `TZ` leaked to a neighbor. Plus the local date computed under each of the two timezones printed alongside the UTC date, showing which one is inside the skew window at validation time.
  - Observed evidence:
    1. Quoted source of timezone-scoped runners in `tests/test_history_date_clock_parity.py`:
    Subprocess runner passing `TZ` in child process `env=`:
    ```python
    def _run_aw(
        self, args: list[str], zone: str
    ) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "TZ": zone, "AW_NO_REEXEC": "1"}
        return subprocess.run(
            [sys.executable, "-m", "agent_workflows", *args],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
        )
    ```
    In-process context manager with guaranteed restore:
    ```python
    @contextlib.contextmanager
    def scoped_timezone(zone: str):
        """Context manager setting TZ for in-process operations with guaranteed restore."""
        old_tz = os.environ.get("TZ")
        os.environ["TZ"] = zone
        if hasattr(time, "tzset"):
            time.tzset()
        try:
            yield
        finally:
            if old_tz is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = old_tz
            if hasattr(time, "tzset"):
                time.tzset()
    ```
    2. Self-check case demonstrated FIRING when narrowed to UTC alone:
    `AW_TEST_ZONES=UTC python3 -m pytest tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_precondition_at_least_one_zone_in_skew_window -o addopts=""`:
    ```
    FAILED tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_precondition_at_least_one_zone_in_skew_window
    =================================== FAILURES ===================================
    _ HistoryDateClockParityTests.test_precondition_at_least_one_zone_in_skew_window _
    ...
    E   AssertionError: No timezone in ['UTC'] is inside a skew window relative to UTC (2026-10-07). Local dates: {'UTC': '2026-10-07'}. Skew harness cannot observe divergence.
    ============================== 1 failed in 0.82s ===============================
    ```
    The timezone pair was restored to `Pacific/Kiritimati` and `Pacific/Honolulu` afterwards.
    3. Single-process co-run with `tests/test_specs_date_containment.py` in one process without xdist:
    `python3 -m pytest tests/test_history_date_clock_parity.py tests/test_specs_date_containment.py -o addopts=""`:
    ```
    ============================= 21 passed in 57.27s ==============================
    ```
    4. Local dates printed alongside UTC date at validation time:
    ```
    SKEW PRECONDITION CHECK:
      UTC date: 2026-10-07
      Pacific/Kiritimati: 2026-10-08 (INSIDE SKEW WINDOW)
      Pacific/Honolulu: 2026-10-07 (same as UTC)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the test's pasted report of the spellings it DERIVED, the ones it EXERCISED, and the ones it SKIPPED with each skip reason, plus the command that produced it. The derivation code quoted, showing it reads `command_surface.COMMAND_INVENTORY` and contains no hard-coded list of command names. An explicit statement that the floor assertion names the backlog and specs setters and that no exact count is asserted (a census pin would violate P16). Plus the measured confirmation that `ipd set` and `prompts set` record the UTC date, which F-05 predicts and which must be verified by DRIVING them, not assumed.
  - Observed evidence:
    1. Pasted report of derived, exercised, and skipped spellings produced by:
    `python3 -m pytest tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_derived_history_writing_surface_coverage_and_floor -o addopts="" -s`:
    ```
    DERIVED SPELLINGS: ['backlog note', 'backlog set', 'config set', 'ipd dependencies set', 'ipd set', 'prompts set', 'set', 'specs note', 'specs set']
    EXERCISED SPELLINGS: ['backlog note', 'backlog set', 'ipd set', 'prompts set', 'set', 'specs note', 'specs set']
    SKIPPED SPELLINGS: {'config set': 'not an artifact verb; writes no history record', 'ipd dependencies set': 'edits dependency metadata field rather than artifact lifecycle status (verified by driving that it appends same-status history via run_set_command)'}
    ```
    2. Derivation code quoted from `tests/test_history_date_clock_parity.py`:
    ```python
    def derive_history_writing_surface() -> tuple[list[str], dict[str, str]]:
        """Derive history-writing candidate commands from COMMAND_INVENTORY."""
        exercised: list[str] = []
        skipped: dict[str, str] = {}

        for cmd in command_surface.COMMAND_INVENTORY:
            tokens = cmd.command.split()
            if not tokens or tokens[-1] not in ("set", "note"):
                continue
            if cmd.command_class != "mutation":
                continue

            name = cmd.command
            if name == "config set":
                skipped[name] = "not an artifact verb; writes no history record"
            elif name == "ipd dependencies set":
                skipped[name] = (
                    "edits dependency metadata field rather than artifact lifecycle status "
                    "(verified by driving that it appends same-status history via run_set_command)"
                )
            else:
                exercised.append(name)

        return sorted(exercised), skipped
    ```
    3. Floor assertion explicitly checks non-vacuity for core setters without pinning exact counts (respects GUIDING_PRINCIPLES P16 against census pins):
    ```python
    self.assertTrue(len(exercised) > 0, "Derived surface must be non-empty")
    self.assertIn("backlog set", exercised, "Floor must include 'backlog set'")
    self.assertIn("specs set", exercised, "Floor must include 'specs set'")
    self.assertIn("backlog note", exercised, "Floor must include 'backlog note'")
    self.assertIn("specs note", exercised, "Floor must include 'specs note'")
    self.assertIn("ipd set", exercised, "Floor must include 'ipd set'")
    self.assertIn("prompts set", exercised, "Floor must include 'prompts set'")
    self.assertIn("set", exercised, "Floor must include bare 'set'")
    self.assertIn("config set", skipped, "Floor must skip 'config set'")
    self.assertIn("ipd dependencies set", skipped, "Floor must skip 'ipd dependencies set'")
    ```
    4. Measured confirmation by driving `ipd set` and `prompts set` under both timezones:
    Both are driven in `test_derived_setters_record_utc_date_under_both_timezones` (cases 8 and 9):
    - `ipd set to-review pl{z_idx}01`: wrote `- 2026-10-07 to-review (aw set): ipd-set-trans` (UTC date).
    - `prompts set executed pr{z_idx}01`: wrote `- 2026-10-07 executed (aw set): prompt-set-trans` (UTC date).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the guard pasted RED AT BASE (in a detached scratch worktree at `3c55295a3^`, never by reverting or stashing in the shared checkout) showing a LOCAL date where UTC was required on BOTH the backlog and the specs family, then pasted GREEN after, each run with `-o addopts=""` and every case named. The swapped-order run pasted. One artifact pasted in full showing a LOCAL compact filename prefix beside a UTC `## Workflow history` record, with the local and UTC dates printed alongside to prove the run was inside a skew window. The F-01 reproduction re-run on both families, all four records pasted and agreeing. A statement that no assertion reads production source for a `timezone.utc` token.
  - Observed evidence:
    1. Guard RED AT BASE in detached scratch worktree at `3c55295a3^`:
    Ran in `/tmp/scratch_base_ayhveg`:
    ```
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_derived_setters_record_utc_date_under_both_timezones FAILED [ 16%]
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_cross_spelling_history_date_and_record_agreement FAILED [ 33%]
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_scoped_timezone_restores_environment PASSED [ 50%]
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_local_filename_and_utc_history_date_composition FAILED [ 66%]
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_derived_history_writing_surface_coverage_and_floor PASSED [ 83%]
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_precondition_at_least_one_zone_in_skew_window PASSED [100%]
    ...
    AssertionError: '2026-10-08' not found in {'2026-10-07'} : Under Pacific/Kiritimati, backlog set --status wrote 2026-10-08, expected UTC in {'2026-10-07'}
    ...
    AssertionError: '2026-10-08' not found in {'2026-10-07'} : Under Pacific/Kiritimati, created line wrote 2026-10-08, expected UTC in {'2026-10-07'}
    ========================= 3 failed, 3 passed in 9.63s ==========================
    ```
    Scratch worktree was cleanly removed with `git worktree remove --force /tmp/scratch_base_ayhveg`.
    2. Guard GREEN at current HEAD:
    `python3 -m pytest tests/test_history_date_clock_parity.py -o addopts=""`:
    ```
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_scoped_timezone_restores_environment PASSED [ 16%]
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_precondition_at_least_one_zone_in_skew_window PASSED [ 33%]
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_derived_setters_record_utc_date_under_both_timezones PASSED [ 50%]
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_cross_spelling_history_date_and_record_agreement PASSED [ 66%]
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_local_filename_and_utc_history_date_composition PASSED [ 83%]
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_derived_history_writing_surface_coverage_and_floor PASSED [100%]
    ========================== 6 passed in 60.77s (0:01:00) ===========================
    ```
    3. Swapped-order run:
    `AW_TEST_SWAP_TZ=1 python3 -m pytest tests/test_history_date_clock_parity.py -o addopts=""`:
    ```
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_scoped_timezone_restores_environment PASSED [ 16%]
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_precondition_at_least_one_zone_in_skew_window PASSED [ 33%]
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_cross_spelling_history_date_and_record_agreement PASSED [ 50%]
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_derived_setters_record_utc_date_under_both_timezones PASSED [ 66%]
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_local_filename_and_utc_history_date_composition PASSED [ 83%]
    tests/test_history_date_clock_parity.py::HistoryDateClockParityTests::test_derived_history_writing_surface_coverage_and_floor PASSED [100%]
    ========================= 6 passed in 64.58s (0:01:04) =========================
    ```
    4. One artifact pasted in full showing local compact filename prefix beside UTC `## Workflow history` record inside skew window:
    Spec artifact generated under `Pacific/Kiritimati`:
    ```markdown
    # Spec: Composition Spec Pacific/Kiritimati

    - Date: 2026-10-08
    - Status: draft
    - Id: o5vi72
    - Author: Tester
    - Scope: testing composition

    ## Workflow history
    - 2026-10-07 created (aw specs): testing composition
    ```
    Dates:
    - Local date (ISO): 2026-10-08 (compact: 20261008 in filename `20261008-o5vi72-01-o5vi72-comp-pacific-kiritimati.spec.md`)
    - UTC date (ISO): 2026-10-07 (history record: `- 2026-10-07 created (aw specs): testing composition`)
    5. F-01 reproduction re-run on both families:
    All 4 records written under `Pacific/Kiritimati`:
    - Record 1 (backlog flag): `- 2026-10-07 same-status (aw backlog): repro-bk-flag`
    - Record 2 (backlog pos):  `- 2026-10-07 same-status (aw set): repro-bk-pos`
    - Record 3 (specs flag):   `- 2026-10-07 to-review (aw specs): repro-sp-flag`
    - Record 4 (specs bare):   `- 2026-10-07 to-review (aw set): repro-sp-bare`
    All four records agree on UTC date `2026-10-07`.
    6. Code-pinning confirmation: No test or assertion inspects production source code for a `timezone.utc` token, uses `inspect`, `ast.parse`, or searches production source text. All checks assert observable written artifact behavior.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the diff of `tests/test_backlog_history_dedup_parity.py` showing the DATE normalization removed and the ACTOR normalization retained, plus its corrected module and helper docstrings quoted (the "Date by shape" and "normalizes the date token by shape" sentences must be gone); the diff of the one corrected comment in `tests/test_history_label_parity.py`; `rg -n "HIST_DATE|<DATE>|date skew|by shape" tests/` pasted returning no date-mask hit. Each file named in Required tests run individually with results pasted. `git diff --stat tests/test_backlog.py tests/test_history_date_clock.py` pasted empty. The bare suite green with its `N passed` line, plus the two whole-suite runs under `TZ=Pacific/Kiritimati` and `TZ=Pacific/Honolulu`. `tests/test_specs_date_containment.py` passing under both timezones with `git diff --stat` showing it unchanged. The before-and-after finding sets for `aw check`, `aw backlog check`, `aw specs check` and `aw attention --check`, shown UNCHANGED.
  - Observed evidence:
    1. Diff of `tests/test_backlog_history_dedup_parity.py`:
    ```diff
    diff --git a/tests/test_backlog_history_dedup_parity.py b/tests/test_backlog_history_dedup_parity.py
    index e3029145b..345a254ca 100644
    --- a/tests/test_backlog_history_dedup_parity.py
    +++ b/tests/test_backlog_history_dedup_parity.py
    @@ -10,10 +10,9 @@ Fences the contract established by IPD evbx9s (backlog r74211):
     - (e) the F-03 indented-prose fixture: the record IS written and the history block is non-empty.
     - (f) the sidecar: a suppressed call adds no .aw/records/history.jsonl line; a recorded call adds exactly one.

    -All cross-spelling comparisons normalize:
    -1. Date by shape (- YYYY-MM-DD -> - <DATE> ) via regex so local vs UTC clock differences
    -   (owned by 2wae2x/tl8qmc, per spec wy9aru S3) do not produce false parity failures.
    -2. Actor ('(aw backlog)' vs '(aw set)') as truthful attribution kept distinct by design (jbipfa).
    +All cross-spelling comparisons compare history dates literally (unified onto UTC
    +per spec 2vev8j 4.4) while normalizing:
    +1. Actor ('(aw backlog)' vs '(aw set)') as truthful attribution kept distinct by design (jbipfa).

     Conforms strictly to GUIDING_PRINCIPLES P16 and AGENTS.md:
     - No inspect, ast, regex, or substring search over production source code.
    @@ -34,20 +33,17 @@ from agent_workflows import attention as att
     from agent_workflows import attention_contract as ac
     from agent_workflows import cli

    -_DATE_RE = re.compile(r"-\s+\d{4}-\d{2}-\d{2}\s+")
     _ACTOR_PAREN = re.compile(r"\((?:aw backlog|aw set)\)")


     def _normalize_history_record(record: str) -> str:
    -    """Normalize date shape and actor in a history record line for cross-spelling parity comparisons.
    +    """Normalize actor in a history record line for cross-spelling parity comparisons.

    -    Hides two known out-of-scope axes per spec wy9aru S3 and IPD evbx9s:
    -    1. Date clock: normalizes the date token by shape (- YYYY-MM-DD -> - <DATE> )
    -       so local vs UTC clock differences across spellings (2wae2x/tl8qmc) do not cause false cross-spelling failures.
    -    2. Actor: '(aw backlog)' vs '(aw set)' truthfully identifies the writer and is deliberate (jbipfa).
    +    Hides one known out-of-scope axis per IPD evbx9s:
    +    1. Actor: '(aw backlog)' vs '(aw set)' truthfully identifies the writer and is deliberate (jbipfa).
    +    (Date clock differences are eliminated by unifying writers onto UTC per spec 2vev8j 4.4; dates are compared literally).
         """
    -    res = _DATE_RE.sub("- <DATE> ", record.strip())
    -    return _ACTOR_PAREN.sub("(HIST_ACTOR)", res)
    +    return _ACTOR_PAREN.sub("(HIST_ACTOR)", record.strip())


     def _normalize_for_parity(text: str) -> str:
    ```
    2. Diff of comment in `tests/test_history_label_parity.py`:
    ```diff
    diff --git a/tests/test_history_label_parity.py b/tests/test_history_label_parity.py
    index df7ef7754..4adc2e580 100644
    --- a/tests/test_history_label_parity.py
    +++ b/tests/test_history_label_parity.py
    @@ -280,7 +280,7 @@ class HistoryLabelParityTests(unittest.TestCase):
             self.assertIn(" graduated (aw backlog): handed off to plan", rec1)
             self.assertIn(" graduated (aw set): handed off to plan", rec2)

    -        # Normalized comparison (hiding actor and date skew)
    +        # Normalized comparison (hiding actor)
             norm1 = _normalize_history_record(rec1)
             norm2 = _normalize_history_record(rec2)
             self.assertEqual(norm1, norm2)
    ```
    3. Date-mask search in tests:
    `rg -n "HIST_DATE|<DATE>|date skew|by shape" tests/` returned exit 1 (0 matches).
    4. Individual test runs:
    - `tests/test_backlog_history_dedup_parity.py`: `6 passed in 5.82s`
    - `tests/test_history_label_parity.py`: `5 passed in 2.75s`
    - `tests/test_backlog.py`: `47 passed in 6.51s`
    - `tests/test_history_date_clock.py`: `5 passed in 31.64s`
    - `tests/test_history_provenance.py`: `7 passed in 6.19s`
    5. Untouched files check:
    `git diff --stat tests/test_backlog.py tests/test_history_date_clock.py` output is empty.
    6. Bare suite green:
    `python3 -m pytest`: `6319 passed, 2 skipped, 3 warnings in 691.32s (0:11:31)`
    7. Whole-suite runs under timezones:
    - `TZ=Pacific/Kiritimati python3 -m pytest`: `6319 passed, 2 skipped, 3 warnings in 162.16s (0:02:42)`
    - `TZ=Pacific/Honolulu python3 -m pytest`: `6319 passed, 2 skipped, 3 warnings in 242.28s (0:04:02)`
    8. `tests/test_specs_date_containment.py`:
    - Ran under `TZ=Pacific/Kiritimati`: `15 passed in 0.81s`
    - Ran under `TZ=Pacific/Honolulu`: `15 passed in 0.82s`
    - `git diff --stat tests/test_specs_date_containment.py` output is empty.
    9. Tooling checks:
    - `aw backlog check`: `aw backlog check: all backlog items conform.`
    - `aw specs check`: `aw specs check: all specs conform. 40 specs checked.`
    - `aw attention --check`: `aw attention --check: the view is valid.`
    - `aw check`: unchanged baseline finding set; 0 findings for scope paths or `ayhveg`.
    - `aw sanitize --agent`: clean (`{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. Its `- Readiness:` field is an OUTPUT of
`/plan-review` and must never be hand-written by an author or executor.

DO NOT EXECUTE THIS PLAN BEFORE `5ivkdh` IS EXECUTED. That is recorded as
`Item-Dependencies: executed:5ivkdh` and the runner re-checks it at dispatch, but it is restated here
because the consequence is specific: run early and the guard is RED ON ARRIVAL on two families, and an
executor may then "fix" it by weakening the assertion, which destroys the only thing this plan
delivers.

DO NOT WEAKEN THE GUARD TO MAKE IT PASS. If the new file fails after `5ivkdh` lands, the correct
conclusion is that a history writer remains on the local clock, and the fix belongs in production code
under a corrective plan, not in this test. A guard that passes because it detects nothing is worse than
no guard, because it reports safety that does not exist.

Execution contract: commit ONLY the files this plan changed, limited to its `Scope-Paths`, through
`aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push.
Verify the staged set with `git diff --cached --name-only` before each commit and unstage anything
not this plan's with `git restore --staged <path>`; this is a shared checkout and another agent's
uncommitted work must never enter a commit here.

Validation is not optional and not inferable: every `V-*` item demands pasted output from a command
actually run. In particular, a claim that this guard works is NOT acceptable on a green suite alone,
because the suite was measured green at `51 passed` while the defect was live on two families (F-02).
The guard MUST be demonstrated failing before the fix, and the skew-window self-check MUST be
demonstrated firing.

Post-gate lifecycle: on completion, run `aw ipd lint --phase pre-transition` to conforming, then move
this plan to `.aw/records/plans/executed/` through the tooled lifecycle transition. Do not hand-edit
the terminal state. Backlog item `a2zpzq` is handed off via `- From-Backlog:` and should reach
`graduated`, not `done`: this plan carries its `- Blocks-Release: next` gate, and the gate is released
only when this plan is `executed`.
