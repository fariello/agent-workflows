# IPD: Put the plan family created record on the UTC history clock the two in-flight clock plans classify as out of scope

- Date: 2026-10-02
- Kind: child
- Concern: `ipd_authoring.run_scaffold` computes ONE local-clock date and spends it on TWO roles: the plan FILENAME prefix (correctly local per `DECISIONS.md` D55) and the plan's `draft`/`created` `## Workflow history` record (which spec `2vev8j` Section 4.4 rules must be UTC). So a plan authored inside the skew window records a history date that is a day behind the UTC date, and its own later transition record, written by the already-UTC `status_set.apply_status_change`, disagrees with it. Measured in this lane at HEAD `ebc28ee39` under `TZ=Pacific/Honolulu` (local `2026-10-01`, UTC `2026-10-02`): `aw ipd scaffold --apply` wrote `- 2026-10-01 draft (probe/agent): created.`, then `aw ipd set to-review` on the SAME file seconds later wrote `- 2026-10-02 to-review (aw set): ...`, so one file's history reads `2026-10-02` above `2026-10-01` while being strictly newest-first and strictly correct in order. This site is NOT covered by the two in-flight clock plans: `5ivkdh` E-05 explicitly classifies `ipd_authoring` as "plan `- Date:` and its compact filename date (D55, leave)" and declares no `ipd_authoring.py` path, and `ayhveg` derives its guard from `command_surface.COMMAND_INVENTORY` setter/note verbs, which reaches `ipd set` but NOT the `ipd scaffold` creation verb that writes this record.
- Scope: IN: split the one overloaded date in `ipd_authoring.run_scaffold` so the FILENAME stays local per D55 while the `draft` history record it renders becomes UTC per `2vev8j` 4.4, and add the behavioral guard that no existing test provides for the plan family's created record. OUT, each with a reason recorded under "Deferred": the shared UTC helper and the backlog/specs/releases/readiness writers (owned by `5ivkdh`); the cross-spelling setter guard (owned by `ayhveg`); the records convergence closing the duplicate cluster (owned by `qjm4bg`); the plan `- Date:` front-matter field, which is not a history record; filename dates, which D55 rules LOCAL; and the four pre-existing suite failures.
- Scope-Paths: agent_workflows/ipd_authoring.py, tests/test_ipd_authoring.py
- Item-Dependencies: none
- Status: to-review
- From-Spec: 2vev8j
- Work-Kind: bug
- Priority: medium
- From-Backlog: lq2w86
- Blocks-Release: next
- Set: lq2w86
- Order: 1
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: rfyrvp

## Workflow history

- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `lq2w86`. The authoring turn found that the item's own described symptom (the `backlog set` versus `aw set` divergence) is ALREADY owned by three review-ready plans, two of which name this item's cluster for closure, so re-fixing it would have produced a fourth colliding plan. Scoped instead to a genuine RESIDUAL measured in this lane at HEAD `ebc28ee39`: the plan family's own `created` record, which `5ivkdh` E-05 classifies as "leave" and which `ayhveg`'s setter-derived guard does not reach. The clock question itself was RESOLVED from repository evidence (spec `2vev8j` 4.4, approved and human-attested, rules history dates UTC; `DECISIONS.md` D55 rules filename dates LOCAL), so no maintainer decision gates this plan. Bare suite baseline at authoring: `4 failed, 4618 passed, 2 skipped` (all four failures pre-existing, named in F-07, and untouched by this plan).
- 2026-10-02 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a plan's `created` history record say WHEN it was created on the one clock the repository has
already ruled for history (UTC), while leaving its filename on the local clock the repository has
already ruled for human-facing names, so the plan family stops being the one artifact family whose
own file can carry two records a day apart in the correct order.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: pin the defect before changing it

- [ ] E-01 Add a timezone-driven behavioral guard to `tests/test_ipd_authoring.py` that drives `ipd scaffold --apply` under a timezone WEST of UTC and a timezone EAST of UTC and asserts the rendered `draft` history record carries the UTC date while the FILENAME prefix carries the LOCAL date. THIS ITEM COMES FIRST AND MUST BE DEMONSTRATED RED, because the measured state of the suite is that nothing sees this defect: a search of `tests/test_ipd_authoring.py` for `date.today`, `strftime`, `%Y%m%d` and `%Y-%m-%d` returns NOTHING, so the scaffold's date behavior is unpinned in both directions and a fix landed without a guard would be indistinguishable from no fix.

    ASSERT BOTH ROLES IN ONE TEST, NOT JUST THE ONE BEING FIXED. A test that only asserts the history record is UTC would pass if the implementer moved BOTH dates to UTC, which silently reverses D55 for every plan filename. Asserting the filename is LOCAL in the same case is what makes the split itself the pinned property rather than a side effect.

    SET `TZ` FOR THE CODE UNDER TEST ONLY, via a context manager that restores the prior value and calls `time.tzset()` on both entry and exit; do NOT export `TZ` for the suite. Pick the pair so a skew window EXISTS whatever the wall-clock hour: `Pacific/Kiritimati` (UTC+14) and `Pacific/Honolulu` (UTC-10) are 24 hours apart, so at every instant at least one of them is on a different date from UTC. Derive which one is skewed at run time and assert against the computed UTC and local dates rather than against a hard-coded date, or the test rots within a day.

    ASSERT ON THE WRITTEN FILE, never by reading `ipd_authoring`'s source for a `timezone.utc` token (GUIDING_PRINCIPLES P16, and the `AGENTS.md` no-code-pinning rule): the outcome is the date in the artifact and the date in its name.
  - Depends on: none
  - Expected outcome: a new test in `tests/test_ipd_authoring.py` that drives the real scaffold verb under a UTC+14 and a UTC-10 timezone and asserts history-is-UTC and filename-is-local; demonstrated FAILING at base on the history assertion, with the failure output pasted and showing the local date where the UTC date was expected.
  - Execution state: pending

### Task group 2: split the one overloaded date

- [ ] E-02 Split the single date value in `ipd_authoring.run_scaffold` so the two roles read two clocks, and change nothing else in the module. One expression currently assigned to `when` is passed BOTH into the body renderer, where `_SECTION_BODY[S.H_WORKFLOW_HISTORY]` formats it into `- {date} draft ({author}): created.`, AND (in compact form, as a separate `date.today()` call in the derived-name branch) into `plans_refs.clustered_name`. Keep a LOCAL value for the filename and derive a UTC value for the history record.

    NAME BOTH AUTHORITIES IN A COMMENT AT THE SPLIT. This is the whole reason the defect survived: the two values look identical at the call site, so the next reader deletes one as redundant unless the code says why there are two. Cite `2vev8j` 4.4 for the UTC history date and `DECISIONS.md` D55 for the local filename date, in the same comment.

    DO NOT MOVE THE PLAN'S `- Date:` FRONT MATTER FIELD. `run_scaffold` also writes `when` into `- Date:` via the metadata renderer, and that field is front matter describing the artifact, not a `## Workflow history` record, so `2vev8j` 4.4 does not reach it; `5ivkdh` E-05 classifies the same field the same way. Moving it would be an undeclared behavior change and would additionally break the local-date agreement between `- Date:` and the filename that `check_engine._artifact_compact_date` relies on when it falls back from the filename date to `- Date:`.

    DO NOT ADD A SECOND INLINE `datetime.now(timezone.utc)` IF `5ivkdh` HAS ALREADY LANDED ITS SHARED HELPER. Check `artifact_core` for the helper first; if it exists, CALL it, because one clock decision having two implementations is the defect class this plan belongs to (GUIDING_PRINCIPLES P8). If it does not exist, compute UTC inline here and say in the transition message that it should be collapsed onto the shared helper when `5ivkdh` lands. `ipd_authoring` already imports `artifact_core` as `_core`, so calling it adds no import edge.
  - Depends on: E-01
  - Expected outcome: `ipd scaffold` writes a UTC `draft` history record and a LOCAL filename prefix from two separately derived values, with a comment naming both authorities; the plan's `- Date:` field is unchanged; E-01's guard now passes.
  - Execution state: pending

### Task group 3: confirm nothing else in this module writes history

- [ ] E-03 Audit the REMAINING date calls in `ipd_authoring` and record a per-site HISTORY-or-FILENAME-or-NEITHER verdict, converting only the history ones. This item exists separately from E-02 because E-02 was scoped from one measured call path, and a module can hold a second history writer that the reproduction did not reach; a verdict table is what makes the claim "this module's history dates are UTC" checkable rather than asserted.

    THE SITES ALREADY SEEN, so this is a confirmation plus a search for anything absent: the `- Date:` front-matter write (NEITHER, per E-02's reasoning) and the compact filename date in the derived-name branch (FILENAME, D55, leave). Any OTHER date-producing call in the module is the thing this audit exists to surface.

    CHECK THE SCAFFOLD'S SIBLING WRITE PATHS TOO, not just the one the reproduction drove. `run_scaffold` has an explicit `--path` branch and a derived-name branch, and the reproduction exercised only the derived one; confirm by DRIVING the `--path` branch under a skew timezone that it records the same UTC history date, rather than reading the code and concluding it must.

    IF THE AUDIT FINDS A HISTORY WRITER OUTSIDE THIS MODULE, DO NOT FIX IT HERE. `5ivkdh` declares six production paths and `qjm4bg` owns the records tree; report it in the transition message and let the owning plan have it. Widening this plan to a path another review-ready plan declares is how two plans collide in the same file.
  - Depends on: E-02
  - Expected outcome: a verdict table covering every date-producing call in `ipd_authoring`, each HISTORY/FILENAME/NEITHER with its reason; the `--path` branch driven under a skew timezone and shown to record the UTC date; a statement that no history writer remains on the local clock in this module, or the named site and its owning plan if one is found outside it.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- OUTCOME TESTS ONLY (`AGENTS.md`, GUIDING_PRINCIPLES P16). The clock fix is proven by the date written into the artifact and into its filename, never by asserting that a module calls `datetime.timezone.utc`.
- Run the suite BARE: `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and deselects `slow`/`livecorpus`; `-n0` is forbidden and a second `-q` suppresses the `N passed` line this plan requires pasted. Use `-o addopts=""` only when a narrowed run needs per-test counts.
- `aw` re-execs into the checkout's own package unless `AW_NO_REEXEC=1` is set; inside a lane worktree it prints a notice naming both paths, which pollutes pasted evidence. Set `AW_NO_REEXEC=1` on every `aw` invocation, or drive `python3 -m agent_workflows` directly.
- `aw ipd scaffold` REQUIRES `--author` (or `AW_IPD_AUTHOR`) and `--kind`; a guard that drives it must supply both or it exits 2 before reaching any date code. Measured while authoring: omitting each produced `error: the following arguments are required: --kind` and `error: --author is required (or set AW_IPD_AUTHOR)`.
- THE TWO CLOCKS ARE BOTH CORRECT AND THE RULINGS DO NOT CONFLICT. `2vev8j` 4.4 scopes itself to WRITERS of history and calls local time "a RENDER-TIME concern only"; D55 scopes itself to human-facing NAMES on an explicit UX rationale. A reviewer who assumes one clock must win will read E-02's split as inconsistent, which is why the split site names both authorities in a comment.
- DERIVE A VALUE, NEVER RE-LIST IT (GUIDING_PRINCIPLES P8). E-02's instruction to prefer `5ivkdh`'s shared helper over a fresh inline UTC call follows from this: a clock ruling with two implementations is the same defect shape in a new place.

## Findings

Established in this lane at HEAD `ebc28ee39`, by driving the real CLI under a skew timezone and by reading the three in-flight plans in full.

| # | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH (THE DEFECT, MEASURED) | Under `TZ=Pacific/Honolulu` (local `2026-10-01`, UTC `2026-10-02`), `aw ipd scaffold --kind child --set probe --order 1 --apply` wrote the file `20261001-probe-01-16wn17-...ipd.md` containing `- Date: 2026-10-01` and `- 2026-10-01 draft (probe/agent): created.`, exit 0. | **THE PLAN FAMILY'S `created` HISTORY RECORD IS ON THE LOCAL CLOCK**, violating `2vev8j` 4.4 for every plan authored inside the skew window. This is permanent, committed, user-visible history. |
| F-02 | HIGH (SELF-CONTRADICTION INSIDE ONE FILE) | On that same file, seconds later and in the same shell, `aw ipd set to-review <path> --message ...` wrote `- 2026-10-02 to-review (aw set): ...` directly ABOVE the `- 2026-10-01 draft ...` record. | **ONE PLAN'S HISTORY BLOCK NOW DISAGREES WITH ITSELF BY A DAY WHILE BEING CORRECTLY ORDERED.** This is the sharpest statement of the harm: the two records are both truthful about order and both written by this toolkit, so a reader cannot reconcile them without knowing which writer used which clock. It also shows the fix direction is forced: the transition writer is already UTC, so the creation writer is the one that must move. |
| F-03 | HIGH (NOT COVERED BY `5ivkdh`) | `5ivkdh`'s `Scope-Paths` lists `artifact_core.py`, `backlog.py`, `specs.py`, `status_set.py`, `releases.py`, `readiness_recheck.py` and three test files; `ipd_authoring.py` appears NOWHERE in it. Its E-05 audit names the module once, classifying it as "`ipd_authoring`'s plan `- Date:` and its compact filename date (D55, leave)". | **THE OWNING PLAN HAS ALREADY LOOKED AT THIS MODULE AND RULED IT OUT, AND THAT RULING IS INCOMPLETE RATHER THAN WRONG.** Its two named sites are both correctly classified; the one it does not name is the `{date}` substituted into the history-section template, which is a third role for the same value. So this is a genuine residual, not a duplicate, and E-05 would not catch it because the site it misses is not in its list. |
| F-04 | HIGH (NOT COVERED BY `ayhveg`) | `ayhveg` derives its guard's targets from `command_surface.COMMAND_INVENTORY` filtered to setter/note verbs, which its F-04 enumerates as `ipd set`, `backlog set`, `backlog note`, `specs set`, `specs note`, `prompts set` and the `spec` aliases. `ipd scaffold` is a CREATION verb and is in none of them. Its F-05 predicts and verifies that `ipd set` is already UTC, which is true and is a different site. | **THE GUARD PLAN COVERS THE TRANSITION WRITERS AND MISSES EVERY CREATION WRITER.** Its derived-surface design is the right one and still does not reach here, because the inventory class it filters on is the setter class. So E-01's guard is additive to `ayhveg`'s rather than a duplicate of it, and the two are independent in either order. |
| F-05 | HIGH (THE SUITE IS BLIND IN BOTH DIRECTIONS) | A search of `tests/test_ipd_authoring.py` for `date.today`, `strftime`, `%Y%m%d` and `%Y-%m-%d` returns no match. No test in `tests/` sets `TZ` or calls `time.tzset()`. The bare suite measured `4 failed, 4618 passed, 2 skipped` at HEAD `ebc28ee39` with the defect live. | **NO TEST PINS THE SCAFFOLD'S DATE BEHAVIOR AT ALL**, so "the suite is green" is worthless evidence here AND a fix would be unguarded against regression. This is why E-01 precedes E-02 and why its acceptance bar is a demonstrated RED, and why it must assert the FILENAME too: there is currently no guard stopping an implementer moving both dates to UTC. |
| F-06 | MEDIUM (THE TRAP, UNGUARDED HERE) | `DECISIONS.md` D55 rules human-facing filename timestamps LOCAL, explicitly reversing an earlier UTC directive on a UX rationale. `check_engine._artifact_compact_date` reads the filename date and FALLS BACK to `- Date:`, treating them interchangeably. | **THE OBVIOUS ONE-LINE FIX REVERSES D55 AND DESILENTLY DESYNCS `- Date:` FROM THE FILENAME.** Redefining the single `when` value is the smallest possible diff and is wrong twice over. This is what shapes E-02 into a split with both authorities named, and what makes E-01's filename assertion load-bearing rather than decorative. |
| F-07 | N/A (BASELINE) | Bare `python3 -m pytest` at HEAD `ebc28ee39`: `4 failed, 4618 passed, 2 skipped, 3 warnings in 145.38s`, failing in `test_selector_type_containment`, `test_run_finding_reachability`, `test_spec_review_attestation` and `test_typecheck_gate`. | **THE BASE IS NOT CLEAN AND THE FOUR FAILURES ARE UNRELATED TO THE CLOCK**, so validation must compare FAILURE SETS BY NAME rather than counts. Recorded so a reviewer does not read a `4 failed` line after this plan as damage it caused. |
| F-08 | LOW (THE ITEM'S OWN SYMPTOM IS ALREADY OWNED) | `lq2w86`'s summary names the `run_set`/`status_set` parity. That exact divergence is owned by `5ivkdh` (production fix), guarded by `ayhveg`, and `qjm4bg` E-03 names `lq2w86` among five duplicates it will close citing the executed `5ivkdh`. Reproduced here for confirmation: the two spellings wrote `- 2026-10-01 same-status (aw backlog): m` and `- 2026-10-02 same-status (aw set): m`. | **THIS PLAN MUST NOT RE-FIX THE ITEM'S LITERAL SYMPTOM**, which is why it declares no `backlog.py` path and takes no dependency on the three in-flight plans. The item's residual value is the family nobody checked, and that is what this plan graduates. `qjm4bg` closing `lq2w86` later is compatible: that plan converges RECORDS and changes no code. |

## Proposed changes (ordered, validatable)

1. `tests/test_ipd_authoring.py`: a timezone-driven guard asserting the scaffold's history record is UTC and its filename prefix is LOCAL, under a UTC+14 and a UTC-10 timezone, demonstrated red at base (E-01).
2. `agent_workflows/ipd_authoring.py`: `run_scaffold`'s one date split into a LOCAL filename value and a UTC history value, with a comment citing `2vev8j` 4.4 and D55, preferring `5ivkdh`'s shared helper if it has landed; `- Date:` untouched (E-02).
3. The module's remaining date calls audited to a HISTORY/FILENAME/NEITHER verdict, with the `--path` branch driven rather than reasoned about (E-03).

## Deferred / out of scope (with reason)

- THE SHARED UTC HELPER AND THE BACKLOG, SPECS, RELEASES AND READINESS WRITERS ARE NOT TOUCHED. `5ivkdh` declares all six production paths and owns the helper this plan would rather call than duplicate. Editing those files here would collide with a review-ready plan in the same functions.
  - Carrier: 5ivkdh
- THE CROSS-SPELLING SETTER GUARD IS NOT BUILT HERE. `ayhveg` owns the `COMMAND_INVENTORY`-derived differential guard over the setter surface, including the spec-family divergence no filed item mentions. This plan adds a guard for the CREATION verb its derivation does not reach, and declares a different test file so the two cannot conflict.
  - Carrier: ayhveg
- THE DUPLICATE CLUSTER IS NOT CLOSED AND `lq2w86` IS NOT SET `done`. `qjm4bg` owns the records convergence and names `lq2w86` explicitly among the items it closes. This plan graduates its own item through `- From-Backlog:` and writes no status onto it.
  - Carrier: qjm4bg
- THE PLAN'S `- Date:` FRONT-MATTER FIELD STAYS LOCAL. It describes the artifact rather than recording an event, so `2vev8j` 4.4 does not reach it, and `check_engine._artifact_compact_date` falls back from the filename date to this field, so desyncing them would change cutover decisions. Moving it would be an undeclared behavior change.
  - Carrier-Declined: not a defect; the field is not a history record and its local value agrees with the filename by design.
- FILENAME DATE PREFIXES STAY LOCAL. D55 is a current, deliberate ruling that reversed an earlier UTC directive on a UX rationale. Changing it would need its own maintainer decision, and E-01 adds the assertion that stops this plan doing it by accident.
  - Carrier-Declined: not a defect; D55 is a deliberate, current ruling and the two clocks compose as written.
- THE FOUR PRE-EXISTING SUITE FAILURES ARE NOT FIXED (F-07). None involves a date or a clock, and this plan touches neither their code nor their fixtures.
  - Carrier-Declined: unrelated to this plan's subject; pre-existing at the measured baseline.
- NO HISTORIC PLAN RECORD IS RESTAMPED. Plans already written carry whichever clock wrote them. Rewriting committed history to assert a date that was never recorded would be a false record (GUIDING_PRINCIPLES P4).
  - Carrier-Declined: not a defect; the existing records are the honest history.

## Scope check

- Over-scope: none. Both declared paths are edited by a numbered item: `agent_workflows/ipd_authoring.py` (E-02, audited by E-03) and `tests/test_ipd_authoring.py` (E-01).
- Under-scope: E-03's audit may surface a history writer OUTSIDE this module, in which case it is reported rather than fixed and the owning plan keeps it, so no path is widened. If `5ivkdh` lands before this plan executes, E-02 calls its `artifact_core` helper, which changes no declared path because `ipd_authoring` already imports that module. E-01 may need a shared timezone context manager; if it is placed in a conftest rather than the declared test file, declare that path at execution and record the widening in the transition message, which this note authorizes. The plan's own file needs no declaration (implicit lifecycle-artifact allowance, spec `ipd-structure-and-linting` Section 4.5).

## Required tests / validation

- The new guard in `tests/test_ipd_authoring.py` run alone with `-o addopts=""`, every case named, demonstrated RED AT BASE (revert or stash the `ipd_authoring.py` edit and paste the failure) and GREEN after. A guard never seen failing proves nothing, and F-05 establishes that nothing else in the suite can see this defect.
- The BARE suite: `python3 -m pytest`, with the `N passed` line pasted. Baseline is `4 failed, 4618 passed, 2 skipped` at HEAD `ebc28ee39` (F-07); compare FAILURE SETS BY NAME, not counts.
- `tests/test_ipd_authoring.py` and `tests/test_ipd_schema.py` each run individually with results pasted, since E-02 changes what the scaffold writes and the schema tests consume scaffolded output.
- The whole suite run a second time under an exported `TZ=Pacific/Honolulu` (UTC-10) and a third under `TZ=Pacific/Kiritimati` (UTC+14), both pasted. These bracket UTC in both directions so one is always inside a skew window. This is a VALIDATION-TIME use of `TZ` to expose the defect, not a fix-time use to hide it.
- A manual end-to-end re-run of F-01 and F-02's reproduction under a skew timezone: scaffold a plan, then transition it, and show the two history records now agreeing on the UTC date while the FILENAME still carries the local compact date. Paste the filename, both records, and the computed local and UTC dates proving the run was inside a skew window.
- The `--path` branch of `run_scaffold` driven under a skew timezone (E-03), with its written history record pasted.
- `AW_NO_REEXEC=1 aw ipd lint` on a freshly scaffolded plan, conforming, proving E-02 did not break the skeleton it renders.
- `AW_NO_REEXEC=1 aw check`, `AW_NO_REEXEC=1 aw attention --check` and `AW_NO_REEXEC=1 aw sanitize --agent`. `aw check` and `aw attention --check` exit 1 on PRE-EXISTING conditions unrelated to this plan, so the honest bar is an UNCHANGED FINDING SET: re-derive before and after and diff. Do not "fix" another plan's finding or another lane's state.
- `AW_NO_REEXEC=1 aw ipd lint --phase pre-transition` on this plan, conforming.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Verify the staged set against this plan's `Scope-Paths` before committing.

## Spec / documentation sync

No spec is amended, and `- Scope-Paths:` declares no `.spec.md` file.

This plan IMPLEMENTS spec `2vev8j` Section 4.4 ("One timezone for every writer"), which is already
`approved` with a human attestation, for the one artifact family the two in-flight clock plans leave
on the local clock. It therefore consumes a settled contract rather than changing one, which is why
`- From-Spec: 2vev8j` is recorded as the provenance link.

`DECISIONS.md` gets NO new entry, for two reasons: the UTC history ruling was already made in
`2vev8j` 4.4, and recording it again would create a second authority for one ruling; and D55 remains
correct and untouched, since this plan deliberately keeps filename dates local.

`CHANGELOG.md` is NOT declared. The user-visible statement that history dates are UTC everywhere
while filenames remain local is owned by `5ivkdh`'s changelog entry, which covers the whole sweep;
adding a second entry for one family would fragment one user-facing change across two lines. If
`5ivkdh` has NOT landed when this plan executes, add the entry and declare the path at execution,
recording the widening in the transition message.

## Open questions

### OQ-01: Which clock should a plan's `created` history record use, UTC or the machine's local time?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, not referred to the maintainer, because the repository has already ruled twice and the two rulings answer different questions. HISTORY DATES ARE UTC: spec `2vev8j` Section 4.4, "One timezone for every writer", states "Every writer, tool and human-facing helper alike, records UTC; local time is a RENDER-TIME concern only." That spec is `approved` and carries a human attestation. FILENAME DATES ARE LOCAL: `DECISIONS.md` D55 reverses the earlier UTC directive for human-facing names on an explicit UX rationale and is still current. Two in-flight plans (`5ivkdh`, `ayhveg`) already treat exactly this pair as settled and build on it. F-02 additionally makes the direction mechanically forced rather than merely ruled: the plan family's TRANSITION writer is already UTC, so moving the CREATION writer to UTC makes one file self-consistent while moving the transition writer to local would contradict 4.4 and desync the backlog and spec families that `5ivkdh` is moving the other way.

### OQ-02: Should this plan instead widen `5ivkdh` to cover `ipd_authoring`, rather than exist separately?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from the repository's own execution contract. NO, a separate plan is correct. `5ivkdh` is `to-review` and carries a reviewed `Scope-Paths` plus an `E-*`/`V-*` bijection; adding a path and an item to it would invalidate the review state it is waiting on and would change a plan another agent authored. The plans README contract also fences execution to declared paths, and `ipd_authoring.py` is not among `5ivkdh`'s, so its executor could not legitimately make this edit even after finding the site in its E-05 audit, which is precisely the case E-05 handles by reporting. The two plans are independent in either order: if `5ivkdh` lands first, E-02 calls its shared helper; if this lands first, `5ivkdh`'s E-05 audit finds this module already correct and says so. Worth flagging to the maintainer (and not resolvable from evidence): `5ivkdh` E-05's classification of `ipd_authoring` names only two of its three date roles, so a reader of that line would conclude the module is clean; it would be worth a correcting note on that plan, which this plan does not have authority to edit.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: the new test pasted FAILING at base (with no `ipd_authoring.py` edit applied), run with `-o addopts=""`, every case named, the failure message showing the LOCAL date where the UTC date was expected. Plus the test's own source quoted, showing that it derives the expected UTC and local dates at run time rather than hard-coding a date, that it restores `TZ` and calls `time.tzset()` on exit, and that it asserts BOTH the history record is UTC AND the filename prefix is LOCAL. Plus a statement, with the search command, that no pre-existing test in `tests/test_ipd_authoring.py` referenced a date at all (F-05).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: under a skew timezone, a scaffolded plan's FILENAME (local compact date) and its `draft` history record (UTC date) both pasted from the same artifact, differing by one day, with the computed local and UTC dates printed alongside to prove a skew window was entered. Plus that same plan's `- Date:` field shown STILL LOCAL and still agreeing with its filename, proving the front-matter field was not moved. Plus the F-02 reproduction re-run: the scaffolded plan transitioned with `aw ipd set`, and both history records shown agreeing on the UTC date. Plus the split site's source quoted showing the comment names both `2vev8j` 4.4 and D55, and a statement of whether `5ivkdh`'s shared helper existed and was therefore called or was absent and computed inline. Plus `tests/test_ipd_authoring.py` and `tests/test_ipd_schema.py` results, and E-01's guard now passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the full per-site verdict table for `ipd_authoring` (every date-producing call, each HISTORY/FILENAME/NEITHER with its reason), plus the command used to enumerate the sites so the census is reproducible. An explicit statement that no history writer remains on the local clock in this module, or the named site and the plan that owns it if one was found outside it. The `--path` branch DRIVEN under a skew timezone with its written history record pasted, not a reading of the code. Plus `aw ipd lint` conforming on a freshly scaffolded plan; the bare suite with its summary line and its failure set compared BY NAME against F-07's four; the two whole-suite runs under `TZ=Pacific/Honolulu` and `TZ=Pacific/Kiritimati`; and `aw check` plus `aw attention --check` finding sets compared before and after.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries no `- Readiness:` field: that field is an OUTPUT of `/plan-review`
and writing one here would forge a review that has not happened. It requires explicit human approval
before execution.

EXECUTION CONTRACT, binding on whoever executes this plan:

1. BOTH OPEN QUESTIONS ARE RESOLVED from cited repository evidence and neither is `Blocking`. Nothing
   here awaits a maintainer decision. Two things are worth RAISING without blocking: `5ivkdh` E-05's
   incomplete classification of this module (OQ-02), and the fact that `qjm4bg` will later close
   `lq2w86` citing `5ivkdh` rather than this plan (F-08).
2. ORDER IS LOAD-BEARING. E-01 precedes E-02 and must be seen RED first. Per F-05 the suite is blind
   to this defect in both directions, so a green suite is NOT evidence of a fix and a fix landed
   without the demonstrated-red guard is indistinguishable from no change at all.
3. SCOPE FENCE. Touch only `agent_workflows/ipd_authoring.py` and `tests/test_ipd_authoring.py`. Do
   NOT edit `backlog.py`, `specs.py`, `status_set.py`, `releases.py`, `readiness_recheck.py` or
   `artifact_core.py`: all six are declared by `5ivkdh`, and editing them here would collide with a
   review-ready plan in the same functions. Do NOT edit the other three plans' files.
4. DO NOT WRITE A STATUS ONTO `lq2w86`. The runner sets it `graduated` on verification. Writing it
   here would forge a transition this plan does not perform, and `done` would additionally drop a
   `Blocks-Release: next` gate this plan inherits and carries.
5. HARD MUST, HONESTY. When you report that validation passed, paste the ACTUAL command output. Every
   `V-*` above demands pasted output from a command actually run, and V-01 demands a failure that was
   actually observed.
6. COMMIT ONLY THIS PLAN'S OWN PATHS, through `aw commit <plan> -- <paths>`. Never `git add -A`, never
   bare `git add`, never `-a`, never `--no-verify`, and never push. Verify the staged set with
   `git diff --cached --name-only` before committing and unstage anything not this plan's with
   `git restore --staged <path>`; this is a shared checkout and another agent's uncommitted work must
   never enter a commit here.
7. LIFECYCLE MOVE ON COMPLETION. Run `aw ipd lint --phase pre-transition` to conforming, then move
   this plan to `.aw/records/plans/executed/` through the tooled lifecycle transition. Do not
   hand-edit the terminal state and do not claim `executed` until every `V-*` reads `pass`. Backlog
   item `lq2w86` is handed off via `- From-Backlog:` and should reach `graduated`, not `done`: this
   plan carries its `- Blocks-Release: next` gate, and the gate is released only when this plan is
   `executed`.
