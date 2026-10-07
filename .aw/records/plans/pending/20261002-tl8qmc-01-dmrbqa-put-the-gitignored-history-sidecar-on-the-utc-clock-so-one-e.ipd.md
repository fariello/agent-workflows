# IPD: Put the gitignored history sidecar on the UTC clock so one event's two copies cannot disagree by a day

- Date: 2026-10-02
- Kind: child
- Concern: `record_history` stamps the sidecar activity log from the LOCAL clock at two sites (`append` and `append_rename`, each `date = _date.today().strftime("%Y%m%d")`), and NO plan in the pending tree declares `agent_workflows/record_history.py` in its `- Scope-Paths:`. That matters because the sibling plan `5ivkdh` is about to move the INLINE history writers to UTC while leaving this one local, so the two copies of ONE event will disagree by up to a day. Measured in this lane at HEAD `743d2be3d` under `TZ=XXX-20` (local `2026-10-03`, UTC `2026-10-02`): a single real `aw backlog set --status open` wrote inline `- 2026-10-03 same-status (aw backlog): probe msg` AND sidecar `{"id6": "bk0001", "date": "20261003", ...}`. Today both read local, so they agree and nothing is visibly wrong; after `5ivkdh` the inline copy becomes `2026-10-02` and the sidecar stays `20261003`, which is a NEW disagreement introduced BY the fix. REVIEW UPDATE 2026-10-06: `5ivkdh` HAS EXECUTED, and the disagreement is now LIVE, measured by plan-review at HEAD `fe2ee961c` under `TZ=Pacific/Honolulu` (local `2026-10-06`, UTC `2026-10-07`): one real `aw backlog set --status open` wrote inline `- 2026-10-07 same-status (aw backlog): probe msg` and sidecar `"date": "20261006"`, and `aw record-history` rendered `- 20261006 [backlog] aw backlog set (aw backlog): probe msg`. `5ivkdh` did not overlook this site, it deferred it on an explicitly FALSIFIABLE condition - "OUT unless the audit shows a user reads it" - and that condition is now measured TRUE: `aw record-history bk0001` renders the stamped date straight to a human as `- 20261003 [backlog] aw backlog set (aw backlog): probe msg`, so the sidecar date is user-facing output and spec `2vev8j` 4.4 ("Every writer, tool and human-facing helper alike, records UTC") reaches it.
- Scope: IN: route the two `record_history` sidecar date defaults onto the same shared UTC helper `5ivkdh` adds, in the compact `YYYYMMDD` shape the sidecar schema already uses, preserving each function's explicit-`date` precedence; and add the outcome test that pins ONE event's inline and sidecar copies to the SAME date under a skew timezone, which is the property no existing test covers. OUT, each with a reason recorded under "Deferred": the inline history writers and the shared helper itself (owned by `5ivkdh`, taken as a hard dependency); the cross-spelling timezone guard (`ayhveg`); the scaffold and plan-family `created` records (`9wcei0`, `rfyrvp`); the lifecycle-gate coverage companion (`5xq2ng`); the duplicate-item convergence that closes this plan's own source item (`qjm4bg`); FILENAME dates, which `DECISIONS.md` D55 rules LOCAL; and migrating the sidecar to the per-artifact tracked journal of `2vev8j` 4.2, which that spec itself declares out of its own scope (N3).
- Scope-Paths: agent_workflows/record_history.py, tests/test_history_date_clock_sidecar.py
- Item-Dependencies: executed:5ivkdh
- Status: reviewed
- Readiness: go-pending-approval
- From-Spec: 2vev8j
- Work-Kind: bug
- Priority: medium
- From-Backlog: tl8qmc
- Blocks-Release: next
- Set: tl8qmc
- Order: 1
- Highest E allocated: 02
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: dmrbqa

## Workflow history
- 2026-10-07 reviewed (aw set): plan-review

- 2026-10-06 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007. Reviewed at HEAD `fe2ee961c` in an isolated review-sweep lane; plan committed and byte-identical to the lane input, so no pre-review snapshot. `5ivkdh` is EXECUTED (dependency satisfiable) and the predicted disagreement is now LIVE: under `TZ=Pacific/Honolulu` (local 2026-10-06, UTC 2026-10-07) a real `aw backlog set --status open` wrote inline `- 2026-10-07 same-status ...` and sidecar `"date": "20261006"`; `aw record-history` rendered `- 20261006 ...`. Both sites still read `_date.today().strftime("%Y%m%d")`; `artifact_core.utc_history_date()` ships with no compact variant by `5ivkdh` E-01's explicit decision. Revisions: E-01 derives compact via `_core.utc_history_date().replace("-", "")` instead of adding an `artifact_core` variant, which was an undeclared path and contradicted the shipped decision (PR-001); E-02 drops the stale 'zero tests set TZ' premise, copies the shipped subprocess-TZ pattern, prefers always-skewed `XXX-24`/`XXX+23:59` zones (XXX-20 measured NOT skewed at 03:42 UTC), and notes `tests/test_history_date_clock.py` never reads the sidecar (PR-002); explicit-`date` precedence pinned by direct calls since no CLI surface reaches it (PR-003); test-first ordering made machine-visible and `git stash`/revert replaced (PR-004); baseline re-derived by node id since `8c460a9a1` fixed the authoring three (PR-005); CHANGELOG note that 5ivkdh's entry is currently false for the sidecar (PR-006); gate gains conditional finalize ownership and plan-file commit (PR-007).

- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `tl8qmc`. The item's own stated work (unify the two setter clocks) is ALREADY owned by five review-ready plans, and `tl8qmc` itself is in `qjm4bg`'s `- Scope-Paths:` to be closed by its E-04, so authoring a sixth copy of that fix was declined. Instead the authoring turn audited for a history-date writer no plan declares and found exactly one: `record_history`'s two sidecar sites. `5ivkdh`'s stated exit condition for deferring them was measured TRUE at HEAD `743d2be3d` (`aw record-history` renders the date to a human), which is what gives this plan a scope distinct from all five siblings. Divergence reproduced under `TZ=XXX-20`; bare suite baseline `3 failed, 4624 passed, 2 skipped`, all three failures pre-existing and untouched here.
- 2026-10-02 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the sidecar's recorded date agree with the inline history record written by the SAME action, by
putting both on the one UTC clock spec `2vev8j` 4.4 mandates.

The point is NOT that the sidecar is important; it is gitignored and advisory, and this plan does not
argue otherwise. The point is that `5ivkdh` converts one of the two copies of each event and this
plan converts the other, so that a correct fix does not introduce a day-sized disagreement between
two renderings of a single action. Filename dates stay LOCAL, because `DECISIONS.md` D55 deliberately
put them there and that ruling is current.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: move the sidecar's two date defaults onto the UTC clock

- [ ] E-01 Route the `date is None` defaults in `record_history.append` and `record_history.append_rename` onto the shared UTC history-date helper `5ivkdh` adds to `artifact_core`, in the COMPACT `YYYYMMDD` shape, and change nothing else about either function.

    THE TWO SITES ARE THE ONLY ONES IN THIS MODULE, AND BOTH ARE REACHED ONLY BY DEFAULT. Each reads `if date is None: date = _date.today().strftime("%Y%m%d")`. Verify with the census E-02 demands rather than trusting this sentence; the module also parses a date out of an inline record in `_parse_history_record`, which READS text and must NOT be touched.

    PRESERVE EXPLICIT-`date` PRECEDENCE EXACTLY (and note how it is OBSERVABLE: no CLI surface passes a `date` to these functions - `aw specs note --date` sets only the inline date, and `specs._sidecar_append` and the three `backlog` sites call `append_advisory` without `date=` - so E-02 pins precedence by CALLING `record_history.append(..., date="20200101")` and `record_history.record_rename(..., date="20200101")` directly and asserting the written sidecar line, which is behavior, not code-pinning). Both functions accept `date: Optional[str]`, and `record_rename` and `append_advisory` thread it through. A caller that passes a date must still win, because that is the path a migration or a backfill uses to record a date that is deliberately not today. Measured in this lane: NO in-tree caller passes one today (all eight call sites in `artifact_rename`, `specs`, `plans_refs`, `research_refs` and `backlog` rely on the default), so the default is what every real invocation gets and the parameter is the untaken branch that must keep working.

    DERIVE THE COMPACT FORM FROM THE SHIPPED HELPER; DO NOT ADD A SECOND FUNCTION. The sidecar schema is compact `YYYYMMDD` while inline records are `YYYY-MM-DD`. `5ivkdh` has EXECUTED and its E-01 as reviewed and shipped DECIDED this exactly: "DO NOT ADD A COMPACT (`YYYYMMDD`) VARIANT. The one future compact caller is the sidecar owned by `dmrbqa`, which can derive it as `<helper>().replace("-", "")`, exactly as `specs.run_new` already derives `date_compact` from `date_iso`". The helper is `artifact_core.utc_history_date()` (returns UTC `YYYY-MM-DD`; `record_history` already imports `artifact_core` as `_core`), so each default becomes `_core.utc_history_date().replace("-", "")`. Re-deriving `datetime.now(timezone.utc)` inline here would recreate the scattered-expression problem this family exists to end, and adding an `artifact_core` function would both contradict that shipped decision and touch an undeclared path. If the now-unused `from datetime import date as _date` import has no other user in the module, remove it.

    DO NOT CHANGE THE SIDECAR'S SCHEMA, KEY ORDER, OR FAILURE ISOLATION. `append_rename`'s record is documented as a superset reusing the status record's key order, and `record_rename` wraps its call in a bare `except Exception: pass` so a ledger failure can never fail a rename. Both properties are load-bearing and outside this plan's concern.
  - Depends on: E-02
  - Expected outcome: both `record_history` sidecar date defaults derive from the shared UTC helper and emit compact `YYYYMMDD`; an explicitly passed `date` is still used verbatim by both functions; the record schema, key order and failure isolation are byte-for-byte unchanged in shape; `tests/test_history_provenance.py` and `tests/test_backlog.py` pass.
  - Execution state: pending

- [ ] E-02 Add `tests/test_history_date_clock_sidecar.py` pinning, as an OUTCOME test under a skew timezone, that ONE action's inline record and sidecar record carry the SAME date, and that the date is the UTC one.

    ASSERT THE AGREEMENT, NOT THE IMPLEMENTATION. Drive a real `aw backlog set` through the CLI (in a subprocess, as `tests/test_history_date_clock.py` does) against a fixture item in a temporary repo, then read the two artifacts the action produced (the item's `## Workflow history` line and the `.aw/records/history.jsonl` line) and assert their dates denote the same day and equal the UTC date. Do NOT assert that `record_history` calls any particular function, do NOT use `inspect` or regex over production source, and do NOT count call sites: `AGENTS.md` forbids code-pinning tests and GUIDING_PRINCIPLES P16 is the authority.

    THE TIMEZONE MUST ACTUALLY PRODUCE SKEW OR THE TEST PROVES NOTHING. A test that runs in a zone where local and UTC agree passes vacuously. REVIEW UPDATE 2026-10-06: `ayhveg`'s "zero tests set `TZ`" measurement is STALE; `5ivkdh` and `9wcei0` shipped two patterns to copy. `tests/test_history_date_clock.py` drives the real CLI in a SUBPROCESS with `env={**os.environ, "TZ": zone, "AW_NO_REEXEC": "1"}` (no parent mutation, so no leak), and `tests/test_scaffold_history_clock.py` uses `XXX-24` / `XXX+23:59`, which are ALWAYS a full day either side of UTC. PREFER THOSE TWO ZONES: with them exactly one of local-east and local-west differs from UTC at EVERY instant (both, except exactly at UTC midnight), so the test enters a skew window on every run instead of only part of the day. Named zones (`XXX-20`, `Pacific/Honolulu`) do not have that property: measured at review 03:42 UTC, `XXX-20` read `2026-10-07` locally, the same as UTC, so it was NOT in a window while Honolulu was. Still COMPUTE both the local and UTC dates per zone and fail explicitly if NEITHER zone produced skew, so a vacuous pass is impossible. Tolerate a run that crosses UTC midnight the way `tests/test_history_date_clock.py::_expected_utc_dates` does.

    THIS PROPERTY IS COVERED BY NO EXISTING TEST AND BY NO SIBLING PLAN. `tests/test_history_provenance.py` passes an explicit `--date` on the paths it exercises, so it never evaluates a default clock; `tests/test_history_date_clock.py` (from `5ivkdh`) asserts the INLINE record is UTC but never reads `.aw/records/history.jsonl` (verified at review), so it is green while the sidecar is local. `ayhveg` builds a cross-SPELLING guard derived from `command_surface.COMMAND_INVENTORY` setter/note verbs and declares only test files, so it compares one spelling's inline record against another's; it does not compare the two COPIES one spelling writes. Restore nothing and duplicate nothing: this is one new file.

    RESTORE THE AMBIENT TIMEZONE WHATEVER HAPPENS. A leaked `TZ` plus `tzset()` would silently re-date every later test in the same worker, and the suite runs under `-n auto` with randomized order, so the corruption would surface as an unrelated flake. Restore in a `finally` or via an `addCleanup`, and prefer setting `TZ` in a SUBPROCESS environment over mutating the parent process where the CLI can be driven that way.
  - Depends on: none
  - ORDERING: write and run this test FIRST and observe it red, THEN perform E-01 (which therefore depends on E-02); the numbering is presentation order, not execution order.
  - Expected outcome: a new `tests/test_history_date_clock_sidecar.py` that fails against the pre-E-01 code and passes after it, driving the real CLI under at least one east-of-UTC and one west-of-UTC zone, asserting the inline and sidecar dates agree and equal the UTC date, proving a genuine skew window was entered, pinning explicit-`date` precedence, and restoring the ambient timezone; the bare suite shows no new failure and no order-dependence.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec `2vev8j` Section 4.4 is the clock authority and is `approved` with a human attestation; its words are "Every writer, tool and human-facing helper alike, records UTC; local time is a RENDER-TIME concern only." It is the reason this plan carries `- From-Spec: 2vev8j` and needs no maintainer decision on which clock wins.
- `DECISIONS.md` D55 ("Human-facing timestamps use LOCAL time, not UTC") governs FILENAME dates and deliberately reverses an earlier UTC directive. The two rulings compose: history records are UTC, names are local. A plan that unifies both clocks silently reverses a current ruling, which is why this plan touches no filename site.
- `2vev8j` 4.2 rules that history should live in a TRACKED per-artifact journal, and 4.3 rules that an explicit `seq` should carry ordering while timestamps become display-only. Both are UNIMPLEMENTED, and the spec's own N3 puts the sidecar migration outside its scope. So the sidecar is the current reality and fixing its clock is not in tension with the spec's end state.
- Tests must assert observable behavior, never code structure: no `inspect`, no regex over production source, no call-site censuses (`AGENTS.md` test-outcomes rule; GUIDING_PRINCIPLES P16). This shapes E-02 into a CLI-driven outcome test.
- The bare suite is already parallel and scoped (`pyproject.toml` `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`); run `python3 -m pytest` with no added flags, which is also why a leaked `TZ` is dangerous under randomized order.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence | Consequence |
|---|---|---|---|
| F-01 | THE DECIDING FINDING: no pending plan declares `agent_workflows/record_history.py`, so these two sites are genuinely unowned. | A search of every `- Scope-Paths:` line across `.aw/records/plans/pending/*.ipd.md` for `record_history` returns nothing. | Without this plan the sidecar stays local after the whole family lands. This is the one scope in the cluster not already claimed. |
| F-02 | `5ivkdh` deferred the sidecar on a FALSIFIABLE condition, and the condition is now measured TRUE. | Its Deferred row reads "THE GITIGNORED HISTORY SIDECAR IS NOT CONVERTED UNLESS E-05 FINDS A READER", and its E-05 text says the sidecar is "OUT unless the audit shows a user reads it". Measured at HEAD `743d2be3d`: `aw record-history bk0001` prints `- 20261003 [backlog] aw backlog set (aw backlog): probe msg`. | A human-facing helper renders this date, so `2vev8j` 4.4 reaches it. This plan does not contradict `5ivkdh`; it satisfies the exit condition `5ivkdh` wrote. |
| F-03 | The defect is LIVE and both copies are local TODAY, so nothing looks broken yet. | Under `TZ=XXX-20` (local `2026-10-03`, UTC `2026-10-02`) one `aw backlog set --status open` wrote inline `- 2026-10-03 same-status (aw backlog): probe msg` and sidecar `"date": "20261003"`. | The two agree at base. The disagreement is CREATED by `5ivkdh` moving only the inline copy, which is exactly why this plan depends on `5ivkdh` rather than racing it. |
| F-04 | Every real invocation takes the defaulted clock; the explicit-`date` parameter is the untaken branch. | All eight in-tree call sites (`artifact_rename` twice, `specs`, `plans_refs`, `research_refs`, `backlog` three times) call `append_advisory`/`record_rename` without a `date=` argument. | The default IS the behavior, so converting it changes every real write; and the parameter must keep working untested-by-production, hence E-02 pins it explicitly. |
| F-05 | No existing test can observe this, because the tests that touch these paths supply the date themselves. | `tests/test_history_provenance.py` passes `--date 2026-01-03` / `--date 2026-01-04` on the paths it drives. `ayhveg` measured that zero tests in `tests/` call `time.tzset()` or set `TZ`, and `tests/test_history_provenance.py`, `tests/test_history_label_parity.py` and `tests/test_backlog.py` measured `59 passed` together while the divergence was live. | A green suite proves nothing here. E-02 must build the skew mechanism rather than extend an existing fixture, and must fail-loud if the window is absent. |
| F-06 | `ayhveg`'s guard would not catch this even after it lands. | It derives its surface from `command_surface.COMMAND_INVENTORY` setter/note verbs and declares only `tests/` paths; it compares the date one SPELLING writes against the date another SPELLING writes. | The inline-versus-sidecar axis is a different comparison (two copies from ONE spelling), so this plan's test is additive rather than duplicative. |
| F-07 | The sidecar is gitignored and advisory, which bounds this plan's severity honestly. | `.aw/.gitignore` ignores `records/history.jsonl`; `engine.py` carries `records/history.jsonl` in the installed template; `2vev8j` notes "176 of the 177 sidecar records exist only on the maintainer's machine"; `backlog.py` states the sidecar "can never gate this write". | No gate, no CI check and no clone depends on this date. The user-perceptible impact is the rendered `aw record-history` output and its disagreement with the inline record, not a broken gate; this plan claims no more than that. |
| F-08 | `tl8qmc`'s own stated work is already owned five times over, and `tl8qmc` is itself scheduled for closure. | `5ivkdh`, `ayhveg`, `9wcei0`, `rfyrvp` and `5xq2ng` each own a distinct slice of the clock defect; `qjm4bg` declares `tl8qmc`'s path in its `- Scope-Paths:` and closes it in E-04. `aw graduation tl8qmc` reports "nothing yet", because that view matches only `- From-Backlog:` links and `qjm4bg` carries `fnb8pl`. | Authoring a sixth copy of the setter fix would collide with review-ready work. The honest graduation of this item is the one unowned site, which is F-01. |
| F-09 | `tl8qmc`'s stated symptom no longer reproduces, so it must not be used as this plan's acceptance test. | Its text says `test_release_exempt_setter_roundtrip_and_parity` fails; that test now carries a date mask whose comment reads "This clock skew is live bug fnb8pl (out of scope for jbipfa), so dates are normalized by shape", and it measured `59 passed` with its file-mates in this lane. | The red test a reader would look for is green. E-02 pins a NEW property instead, and correcting the item's prose belongs to `qjm4bg` E-02, which already owns it. |
| F-10 | `tl8qmc` asserts the clock choice is an open decision; it is not. | The item says "Which clock is the decision to record". Spec `2vev8j` 4.4 is `approved` and human-attested, and `DECISIONS.md` D55 settles filenames. `5ivkdh`'s OQ-01 independently reached the same reading and flagged the item as stale. | No maintainer decision is required for this plan to proceed, and OQ-01 below is resolved from evidence rather than referred upward. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/record_history.py`: the `date is None` defaults in `append` and `append_rename` derive from the shared UTC helper in compact `YYYYMMDD`, with explicit-`date` precedence, record schema, key order and failure isolation all unchanged (E-01).
2. `tests/test_history_date_clock_sidecar.py`: a new outcome test driving the real `aw backlog set` under an east-of-UTC and a west-of-UTC zone, asserting the inline and sidecar dates agree and equal the UTC date, proving the skew window was entered, pinning explicit-`date` precedence, and restoring the ambient timezone (E-02).

## Deferred / out of scope (with reason)

- THE INLINE HISTORY WRITERS AND THE SHARED UTC HELPER ARE NOT BUILT HERE. `5ivkdh` adds the helper to `artifact_core` and converts `backlog`, `specs`, `status_set`, `releases` and `readiness_recheck`. This plan consumes that helper and takes a hard `executed:5ivkdh` dependency rather than duplicating or pre-empting it.
  - Carrier: 5ivkdh
  - Carrier-Evidence: .aw/records/plans/executed/20261001-7qvs1c-01-5ivkdh-unify-every-artifact-history-date-onto-the-utc-clock-ruled-b.ipd.md
- THE CROSS-SPELLING TIMEZONE GUARD IS NOT BUILT HERE. `ayhveg` owns the derived, timezone-parameterized differential guard over the setter surface, including the spec-family divergence no filed item mentions. F-06 records why its comparison and this plan's are different axes.
  - Carrier: ayhveg
- THE SCAFFOLD AND PLAN-FAMILY `created` RECORDS ARE NOT TOUCHED. `9wcei0` and `rfyrvp` each own an `ipd_authoring` site, and this plan declares no `ipd_authoring.py` path.
  - Carrier: 9wcei0
  - Carrier-Evidence: .aw/records/plans/executed/20261002-jvw1kg-01-9wcei0-stamp-the-scaffold-s-draft-history-record-from-the-utc-clock.ipd.md
- THE LIFECYCLE-GATE COVERAGE COMPANION IS NOT BUILT HERE. `5xq2ng` owns the rule that reports when `check.lifecycle-transition-invalid` validates nothing once date variation is removed. That is a consequence of the inline fix, not of the sidecar, which gates nothing (F-07).
  - Carrier: 5xq2ng
- THE DUPLICATE-ITEM CONVERGENCE IS NOT PERFORMED HERE, INCLUDING THIS PLAN'S OWN SOURCE ITEM. `qjm4bg` declares `tl8qmc`'s path and closes it in E-04, and also owns correcting the stale diagnosis F-09 describes. This plan writes no status onto `tl8qmc` and edits none of the cluster's records.
  - Carrier: qjm4bg
- FILENAME DATE PREFIXES STAY LOCAL. `DECISIONS.md` D55 is a current ruling that deliberately reversed an earlier UTC directive on a UX rationale. The sidecar carries no filename date, so this plan has no occasion to touch one.
  - Carrier-Declined: not a defect; D55 is a deliberate, current ruling and the two clocks compose as written.
- THE SIDECAR IS NOT MIGRATED TO THE TRACKED PER-ARTIFACT JOURNAL. `2vev8j` 4.2 rules that history should live in tracked per-id6 JSONL and 4.3 that an explicit `seq` should own ordering, but the spec's own N3 places that migration outside its scope and it is unimplemented. Fixing the clock of the store that exists today is independent of replacing that store later.
  - Carrier-Declined: deliberately out of scope per the spec's own N3; no carrier exists yet and this plan does not create the obligation.
- THE `--date` OVERRIDE IS NOT ADDED TO THE `aw set` FAMILY. `5ivkdh` records that gap. `record_history`'s functions already accept a `date` parameter, which is all E-01 must preserve.
  - Carrier: fcnz1r
- THE THREE PRE-EXISTING SUITE FAILURES ARE NOT FIXED. The bare suite measured `3 failed, 4624 passed, 2 skipped` at authoring, in `test_spec_review_attestation`, `test_run_finding_reachability` and `test_selector_type_containment`. None involves a history date or the sidecar. (Review 2026-10-06: commit `8c460a9a1` has since addressed them; re-derive the baseline at execution.)
  - Carrier-Declined: unrelated to this plan's subject; it touches neither the modules nor the behaviors those tests exercise.

## Scope check

- Over-scope: none. Two paths are declared: the one production module holding the unowned sidecar date defaults, and the one new test file pinning the property. No other module, no sibling plan's declared path, no record and no spec file is touched.
- Under-scope: the shared UTC helper itself is `5ivkdh`'s (hence the hard dependency); the stale prose and the closure of `tl8qmc` are `qjm4bg`'s; the cross-spelling guard is `ayhveg`'s; the two `ipd_authoring` sites are `9wcei0`'s and `rfyrvp`'s; the gate-coverage companion is `5xq2ng`'s; the sidecar's eventual replacement by the `2vev8j` 4.2 journal has no carrier and is declined with that spec's own N3 as the reason. Each is listed under "Deferred" with its carrier.

## Required tests / validation

1. THE NEW TEST MUST FAIL BEFORE E-01 AND PASS AFTER. Run `tests/test_history_date_clock_sidecar.py` against the pre-E-01 code and paste the failure. Produce that state by writing and running the test BEFORE making E-01's edit (the ordering E-02's own expected outcome requires), or, if missed, by running it against `git show HEAD:agent_workflows/record_history.py` placed in a gitignored scratch package; NEVER `git stash` or revert in what may be a shared checkout (AGENTS.md). Note that only the zone currently in a skew window fails pre-fix; paste which. then against the post-E-01 code and paste the pass. A test that was never observed failing is not known to test anything.
2. THE SKEW WINDOW MUST BE PROVEN ENTERED, by printing the local and UTC dates alongside the assertion in both the east-of-UTC and west-of-UTC runs. Equal dates mean the run proved nothing and must be reported as such rather than counted as a pass.
3. ONE EVENT, ONE DATE, DRIVEN END TO END: a real `aw backlog set` under a skew zone, with the resulting inline `## Workflow history` line and the resulting `.aw/records/history.jsonl` line both pasted, showing the same day and the UTC day.
4. EXPLICIT-`date` PRECEDENCE PRESERVED for both `append` and `append_rename`, demonstrated by observable output rather than by reading the source.
5. NO AMBIENT TIMEZONE LEAK: the bare suite run after the change shows no new failure, and a repeated bare run (the suite randomizes order under `-n auto`) shows the same result, so a leaked `TZ` would surface.
6. REGRESSION: `tests/test_history_provenance.py`, `tests/test_history_label_parity.py` and `tests/test_backlog.py` still pass (they measured `59 passed` together at authoring).
7. SUITE UNCHANGED OTHERWISE: a bare `python3 -m pytest` run at execution HEAD BEFORE any edit records the baseline failing node ids (the authoring-time three were fixed by `8c460a9a1`, so the baseline may now be empty); after the change, compare BY NODE ID and show no node id added, with the actual summary lines pasted.
8. NO COLLATERAL EDIT: `git diff --cached --name-only` at commit lists only the two declared `- Scope-Paths:` entries (plus this plan file, which is implicitly allowed).

## Spec / documentation sync

No spec amendment is required, and `- Scope-Paths:` declares no `.spec.md` file.

This plan IMPLEMENTS an approved ruling rather than changing a contract: spec `2vev8j` Section 4.4
already mandates UTC for every writer and human-facing helper, and `- From-Spec: 2vev8j` records that
link. `DECISIONS.md` D55 keeps filename dates local and is untouched, because the sidecar carries no
filename date.

No CHANGELOG entry is claimed here. `5ivkdh` E-06 already wrote the user-facing entry (`CHANGELOG.md`,
"unified artifact workflow history dates onto the UTC clock across all history writers"), and that
statement covers this change too; note it is currently FALSE for the sidecar, which this plan makes true;
adding a second entry for the gitignored advisory log would be noise. If the executor finds that
`5ivkdh`'s entry landed WITHOUT covering the sidecar, say so in the finalize report rather than
silently widening scope to edit `CHANGELOG.md`, which is not in `- Scope-Paths:`.

## Open questions

### OQ-01: Should the gitignored sidecar move to UTC at all, given that nothing gates on it?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, not referred to the maintainer. Yes, for two independent reasons. FIRST, spec `2vev8j` 4.4 is `approved` and human-attested and says "Every writer, tool and human-facing helper alike, records UTC"; `aw record-history` is a human-facing helper that renders this exact date (measured: `- 20261003 [backlog] aw backlog set (aw backlog): probe msg`), so the ruling reaches it on its own terms. SECOND, and decisively for the TIMING, `5ivkdh` deferred this site on the explicit condition "OUT unless the audit shows a user reads it", so converting it is the completion of a condition a review-ready sibling already wrote rather than a new judgement. The counter-argument (F-07: gitignored, advisory, gates nothing) is real and is why this plan is `medium` priority with a narrow two-path scope, not why it should be skipped: leaving it local would mean the family's own fix CREATES a day-sized disagreement between two renderings of one event.

### OQ-02: Should the sidecar instead be migrated to the tracked per-artifact journal of `2vev8j` 4.2, making this fix moot?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED, not here and not now. `2vev8j` 4.2 does rule for a tracked per-id6 journal and 4.3 for an explicit `seq` with timestamps display-only, which would supersede both this plan's sites. But the spec's own N3 declares that migration OUT of its scope ("NOT a migration of backlog and specs off the global sidecar in this spec's scope"), it is unimplemented today (`record_history` holds no `seq`), and no plan carries it. A two-line clock correction to the store that actually exists cannot sensibly wait on an unscheduled redesign, and it is not wasted if that redesign lands, since the migration would delete these sites outright. Recorded under "Deferred" as declined with the spec's own N3 as the reason.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: the post-change source of both `record_history.append` and `record_history.append_rename` date defaults quoted, showing each derives from the shared `artifact_core` UTC helper and emits compact `YYYYMMDD`; AND a pasted demonstration, DRIVEN through the CLI under a skew zone with the local and UTC dates printed alongside, that a real `aw backlog set` now writes the UTC date into `.aw/records/history.jsonl`; AND a pasted demonstration that an explicitly passed `date` is still recorded verbatim by BOTH functions; AND a pasted sidecar record showing its key order and fields unchanged in shape; AND the results of `tests/test_history_provenance.py` and `tests/test_backlog.py`. A statement that the helper is called, unsupported by driven output, is not acceptable evidence. Confirm no compact variant was added to `artifact_core` (the derivation is `_core.utc_history_date().replace("-", "")`, per `5ivkdh` E-01's shipped decision).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the new test's output pasted TWICE, once failing against the pre-E-01 production code (naming how that state was produced) and once passing after it, since a test never seen red is not known to be a guard; AND the pasted output of the passing run for BOTH an east-of-UTC and a west-of-UTC zone, each printing the local and UTC dates to prove a genuine skew window was entered rather than passing vacuously; AND the inline record and the sidecar record from one driven action quoted side by side showing the same date; AND the test source quoted at the points where it sets and RESTORES the timezone, plus the pasted summary lines of two separate bare `python3 -m pytest` runs showing no failing node id beyond the baseline re-derived at execution HEAD before the edit, which is what would expose an ambient `TZ` leak under randomized parallel order. Evidence that reads production source with `inspect`, regex or a call-site census is inadmissible here and would itself be a defect (GUIDING_PRINCIPLES P16).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT, binding on whoever executes this plan:

1. ALL OPEN QUESTIONS ARE RESOLVED. OQ-01 and OQ-02 are both `Status: resolved` from cited
   repository evidence and neither is `Blocking`. Nothing here awaits a maintainer decision.
2. THE `Item-Dependencies` EDGE IS HARD. `executed:5ivkdh` must hold, because this plan CONSUMES the
   shared UTC helper that plan adds and its whole purpose is to keep the sidecar copy in step with
   the inline copy `5ivkdh` converts. If `5ivkdh` is not executed, STOP and report: that is a missing
   prerequisite, not a scope question. Do not work around it by writing a private UTC expression in
   `record_history`, which would recreate the scattered-clock defect this family exists to end.
3. SCOPE FENCE. Touch only `agent_workflows/record_history.py` and
   `tests/test_history_date_clock_sidecar.py`. Do not edit another plan's declared path, do not edit
   any `.aw/records/` artifact, and do not write a status onto `tl8qmc` (that is `qjm4bg` E-04's).
   If the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the
   two-way scope reconciliation at finalize.
4. NO CODE-PINNING TESTS. E-02's test must drive the CLI and assert on recorded output. Never read
   production source with `inspect`, `ast`, regex or substring search, and never assert a call-site
   count (`AGENTS.md` test-outcomes rule; GUIDING_PRINCIPLES P16).
5. RESTORE THE AMBIENT TIMEZONE. A leaked `TZ` plus `tzset()` re-dates later tests in the same
   worker and the suite runs parallel with randomized order, so the damage would appear as an
   unrelated flake. Prefer a subprocess environment over mutating the parent process.
6. RUN THE SUITE BARE, as `python3 -m pytest`. Do not add `-n0`, a second `-q`, or
   `-p no:randomly`; the configured `addopts` already handles quiet, parallel and marker scoping,
   and `-p no:randomly` would disable exactly the order randomization that catches a `TZ` leak.
7. HARD MUST, HONESTY. When you report that validation passed, paste the ACTUAL command output.
   Never claim a run you did not perform. V-02 demands a BEFORE (red) and AFTER (green) observation
   that cannot be satisfied from memory.
8. COMMIT ONLY THIS PLAN'S OWN PATHS (the two declared `- Scope-Paths:` plus this plan file), through `aw commit <plan> -- <paths>`. Never `git add -A`,
   never bare `git add`, never `-a`, never `--no-verify`, and never push. Verify the staged set with
   `git diff --cached --name-only` before committing.
9. LIFECYCLE MOVE ON COMPLETION, WITH CONDITIONAL OWNERSHIP. Under `aw oc run` / `aw agy run` the
   DRIVER finalizes: write the outcome file the prompt names and do NOT run finalize yourself. In a
   hand execution with no runner, finalize with
   `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`, which runs the
   pre/post-transition gates, reconciles changed paths against the reviewed `Scope-Paths`, writes the
   attributed history newest-first, moves the plan to `.aw/records/plans/executed/`, and makes the
   path-scoped lifecycle commit as one transaction. Do not hand-move the file and do not claim
   `executed` until `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass`.
