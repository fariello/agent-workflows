# IPD: Fix tests that assert against live repo state instead of a fixture

- Date: 2026-08-29
- Kind: child
- Concern: Two tests assert against the live repo, so they pass or fail for reasons unrelated to the code under test; one currently fails because the latest run happens to be clean and would pass again by accident when a run ends interrupted, and the other is a race between two CLI invocations.
- Scope: The two failing tests plus the fixture seam they need. Fix `test_run_viewer_cli_issues_flag` to build its own discrepancy fixture, and `test_todo_matches_attention` to compare one snapshot two ways. Also record, without fixing, the 23-site `dir="."` pattern in the same file so the systemic risk is visible.
- Scope-Paths: tests/test_run_viewer.py, tests/test_awcmdsurf_merge_and_renames.py
- Item-Dependencies: none
- Status: executed
- Set: testinvoke
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: i79rgh
- Blocks-Release: next

## Workflow history
- 2026-08-30 executed (opencode model=its_direct/pt3-claude-opus-5-1m-us): Executed E-01..E-04. E-01 was already satisfied at HEAD by unrelated commit 62810c3 (verified, not trusted; DECISION 05-i79rgh-D1). E-02 added test_run_viewer_cli_issues_flag_empty_state pinning the negative polarity on its own fixture, proven non-vacuous by mutation. E-03 replaced the two-live-read race in test_todo_matches_attention with a structural assertion that both cli._dispatch branches are the identical delegation to attention.run, plus a single-snapshot double render; the old test was proven to FAIL under the same perturbation the new one survives. E-04 recorded the residual hazard with numbers re-measured at execution time, and FALSIFIED the plan's F-8: .aw/records/runs is gitignored with zero tracked files, so 15 of the file's tests fail in any fresh checkout and CI is red on all 16 unittest jobs. Suite delta 15 failed/2912 passed to 15 failed/2913 passed, identical failure set, +1 for the new test. Nothing pushed. [Scope reconciliation - in-scope-unmodified tests/test_awcmdsurf_merge_and_renames.py: already committed in product commit 68fd7a3 (E-03 structural aliasing assertion) BEFORE the receipt was refreshed at that same commit, so it shows unmodified relative to the new frozen base; in-scope-unmodified tests/test_run_viewer.py: already committed in product commit 68fd7a3 (E-02 empty-state test + E-04 hazard docstring) BEFORE the receipt was refreshed at that same commit, so it shows unmodified relative to the new frozen base]
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-005..PR-008. Self-review of a plan I authored, so every claim was re-verified rather than trusted. PR-005 (FIXED, BLOCKER-class factual error): the plan claimed test_run_viewer_cli_issues_flag now fails PERMANENTLY because the repo got healthier. That is WRONG and would have misled the executor into writing the wrong fix. The test sets last=1 (test_run_viewer.py:1047) so it inspects only the MOST RECENT run: aw runs --last 1 --issues currently reports no discrepancy (fails), but aw runs --last 6 --issues DOES render the table with qcqhj7 and rchpms as interrupted/approved. So the real defect is OSCILLATION - it will pass again by accident the moment a fresh run ends interrupted - which is worse than a hard failure because it teaches re-running until green. Concern, Goal and F-3 all corrected. PR-006 (FIXED, HIGH): because the defect is oscillation, V-01's original evidence (passing once, today) was insufficient; it now demands a state-independence proof showing the test passes in BOTH live conditions, with the executor stating which condition was constructed vs waited for. PR-007 (FIXED, MEDIUM, right-sizing per rubric G): E-04 and E-05 were one concern artificially split - E-05 only re-verified E-04's numbers, which the V-item already required. Merged into a single E-04 that measures at execution time with an explicit rule that a measurement disagreeing with this plan WINS; V-04 now also demands the hazard be proven real by moving a named run record aside and pasting the resulting failure. Bijection stays 4/4 and Highest E allocated stays 05 (ids are not reused). PR-008 (FIXED, MEDIUM): OQ-01 was left to executor taste when the repo already answers it - cli.py:8218 (todo) and cli.py:8518 (attention/att) have byte-identical bodies both returning att.run(args), so the aliasing is statically provable without executing either command; resolved to prefer the structural assertion and E-03 updated. Verified clean: all path:line citations resolve (test_run_viewer.py:1037/:1039/:1047/:1063/:45/:112, test_awcmdsurf_merge_and_renames.py:12/:44-48), 34 tests in the file confirmed, both named run records confirmed present, aw ipd lint conforming at author and review-finalize, gate carries the full execution contract.

- 2026-08-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from two live failures observed and measured on this checkout while diagnosing an agent's repeated suite runs.
- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the suite's verdict depend on the code under test rather than on the repository's current
contents, so a green suite means the code is correct and a red suite means something is actually
broken. Today one test's result is decided by whether the most recent run happens to be clean, which
teaches every agent and human to re-run until green instead of trusting the suite.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the permanently-failing discrepancy test

- [x] E-01 Rewrite `test_run_viewer_cli_issues_flag` (`tests/test_run_viewer.py:1037`) to stop passing
      `dir="."`. Build a temporary repo containing exactly one synthetic artifact/status discrepancy
      (the shape the `--issues` table reports), point the namespace at it, and assert the table
      renders that known discrepancy. The test must no longer depend on the live repo containing a
      discrepancy by accident.
  - Depends on: none
  - Expected outcome: the test passes on a HEALTHY repo, which it cannot do today.
  - Execution state: performed
  - Execution note: SATISFIED AT HEAD by prior commit `62810c3` ("feat(oc): make turn-2
    verification opt-in via --validate", 2026-08-29 16:53:06 -0400), which is unrelated maintainer
    work that happened to include exactly this rewrite. It landed 49 minutes AFTER this plan file
    was added (`33ffc96`, 16:04:15 -0400), so the plan was authored against the pre-fix tree and
    was overtaken. Verified rather than trusted: the test now builds a
    `tempfile.TemporaryDirectory` fixture, passes `dir=str(root)`
    (`tests/test_run_viewer.py:1191`) and not `dir="."`, and asserts the specific stem
    `20260829-test-01-item01` so the assertion is not vacuous. No rewrite of my own was performed;
    re-editing a correct green test would add regression risk and misattribute the fix. Recorded
    as DECISION 05-i79rgh-D1.

- [x] E-02 Add the negative case as a separate test: a fixture repo with NO discrepancy must render
      the `no artifact or status discrepancies found` empty-state and exit 0. The current single test
      conflates "the feature works" with "this repo happens to be unhealthy", so both polarities must
      be pinned independently.
  - Depends on: E-01
  - Expected outcome: both the populated and empty states are covered by fixtures.
  - Execution state: performed
  - Execution note: PERFORMED. Added `test_run_viewer_cli_issues_flag_empty_state`
    (`tests/test_run_viewer.py`, immediately after the populated case). It builds its own
    `tempfile.TemporaryDirectory` repo in the CLEAN shape (plan in `executed/` carrying `- Status:
    executed`, matching a queue step whose status is `complete`, so `audit_step_artifact` finds
    neither a location nor a status mismatch), passes `dir=str(root)`, and asserts `out.strip() ==
    "no artifact or status discrepancies found"` plus the absence of the table header. Exit code
    asserted 0.

### Task group 2: the two-invocation race

- [x] E-03 Fix `test_todo_matches_attention`
      (`tests/test_awcmdsurf_merge_and_renames.py:44`). It currently shells `aw todo` and `aw
      attention` as two SEPARATE `cli.main` calls (`_run` at `:12`) and asserts byte-identical
      output, so any repository change landing between the two calls fails it. Establish equality
      without a second live read: assert the two commands resolve to the same handler/alias, or
      capture one snapshot and render it through both paths. Per OQ-01 (resolved from evidence), prefer
      the STRUCTURAL assertion: `cli.py:8218` (`todo`) and `cli.py:8518` (`attention`/`att`) have
      byte-identical bodies that both `return att.run(args)`, so the aliasing is statically provable
      without running either command. Do NOT simply loosen the assertion to make it pass; the aliasing
      property being tested is real and worth keeping.
  - Depends on: none
  - Expected outcome: the test proves `todo` and `attention` are the same command without racing the
    repository.
  - Execution state: performed
  - Execution note: PERFORMED, taking OQ-01's resolved STRUCTURAL option. The test no longer
    performs two live reads. It extracts both dispatch branch bodies out of
    `inspect.getsource(cli._dispatch)` and asserts they are equal AND equal to the literal two
    lines `["from agent_workflows import attention as att", "return att.run(args)"]`, so `todo`
    cannot acquire a body of its own. It also pins the `att` alias. One correction discovered
    while executing: argparse does NOT canonicalize an alias, so `parse_args(["att"]).command ==
    "att"`, not `"attention"`; my first draft asserted the latter and FAILED, which is precisely
    why the dispatcher tests membership in `("attention", "att")` rather than equality. The test
    now asserts the true behavior plus the presence of that membership tuple in the source. An
    output-level check is retained WITHOUT a second live read: one temp fixture is rendered
    through both parsed namespaces via a single `attention.run` call each, and the `(rc, output)`
    pairs are compared. The assertion was NOT loosened; the aliasing property is still enforced,
    more strictly than before.

### Task group 3: make the systemic risk visible without a sweeping rewrite

- [x] E-04 Record the residual hazard in `tests/test_run_viewer.py` (module docstring note), and
      MEASURE its numbers at execution time rather than copying them from this plan: how many of the
      file's tests pass `dir="."`/`Path(".")` and therefore read the live repository (this plan
      measured 23 of 34), and which REAL committed run records are load-bearing fixtures that
      `aw archive` would break (this plan found `run-20260827T212854Z-2364829` and
      `run-20260827T212958Z-2367239` present and asserted by name at `tests/test_run_viewer.py:45`
      and `:112`). If a measurement disagrees with this plan, the MEASUREMENT wins and the note
      records the true value. Documentation of a known hazard, not a fix.
  - Depends on: E-01, E-02
  - Expected outcome: the next reader learns the hazard, with numbers true at execution time, from the
    file itself instead of rediscovering it from a confusing failure.
  - Execution state: performed
  - Execution note: PERFORMED, and the MEASUREMENT overrode this plan on the central point, per
    this item's own tie-break rule. Note written as the module docstring of
    `tests/test_run_viewer.py`. Measured at execution time: 23 of 36 test methods read live state
    (this plan said 23 of 34; the 23 matches, the total is 36 because the file had 35 at HEAD and
    E-02 added one), across 30 raw `dir="."`/`Path(".")` occurrences. F-8 IS FALSIFIED: the two
    named run records are NOT "REAL COMMITTED run records". `.aw/records/runs/` is gitignored
    (`.aw/.gitignore:15`) and `git ls-files .aw/records/runs` returns 0 files, so they are box-
    local untracked scratch. The true hazard is therefore much larger than documented: 15 of these
    tests fail in ANY fresh checkout, and that is why CI is currently red on all 16 `unittest`
    jobs. The note records that truth, with a one-command reproduction, and keeps the archive
    warning (deleting a record still breaks the file locally). Recorded as DECISION 05-i79rgh-D2.
    Scope was deliberately NOT widened to fix the 15 (see Deferred / out of scope).

## Project conventions discovered (Step 0)

- `tests/test_run_viewer.py` builds its namespaces inline as `argparse.Namespace(...)` with
  `dir="."`; there is no existing fixture-repo helper in this file to reuse, so E-01 must introduce
  one (or reuse `tempfile.TemporaryDirectory`, the pattern used across
  `tests/test_status_set.py` and `tests/test_backlog.py`).
- `tests/test_awcmdsurf_merge_and_renames.py` drives the real CLI through a local `_run(argv)` helper
  (`:12-19`) that captures stdout+stderr and normalizes `SystemExit`. Keep that helper; the defect is
  the double live read, not the harness.
- The suite runs in parallel by default (`pyproject.toml:122`, `-n auto --dist=worksteal`), so any
  test that reads shared mutable repo state is inherently racy against BOTH concurrent agents and its
  own sibling workers. That raises the stakes on `dir="."` beyond mere coupling.
- Sibling plan `uyd3lw` (Order 01) covers the agent-guidance half of the same incident. This plan
  owns only the tests.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | `test_run_viewer_cli_issues_flag` passes `dir="."`, i.e. the real repo. | `tests/test_run_viewer.py:1039` |
| F-2 | It asserts the live repo currently HAS a discrepancy. | `:1063` `self.assertIn("Artifact & Status Discrepancies", out)` |
| F-3 | It fails RIGHT NOW because the latest run is clean, and it will flip back and forth as runs come and go. Corrected during review: an earlier draft of this plan called the failure "permanent", which is wrong and would have misled the executor. The test sets `last=1` (`tests/test_run_viewer.py:1047`), so it inspects ONLY the most recent run. `aw runs --last 1 --issues` currently prints `no artifact or status discrepancies found` (fails), while `aw runs --last 6 --issues` DOES render the table with `qcqhj7` and `rchpms` as `interrupted`/`approved` discrepancies. So the test would pass again by accident the moment a fresh run ends interrupted. Intermittent-by-accident is WORSE than a hard failure: it teaches everyone to re-run until green. | `tests/test_run_viewer.py:1047` (`last=1`); the two `aw runs ... --issues` outputs above |
| F-4 | The healing event was legitimate, tool-driven work, not corruption. | `762fd9d integrate(aw oc run): merge verified lane 8zgybk to main`, then `f5f733f lifecycle(8zgybk): finalize 8zgybk -> executed` |
| F-5 | `test_todo_matches_attention` compares two separate live reads. | `tests/test_awcmdsurf_merge_and_renames.py:44-48` calls `_run(["todo"])` and `_run(["attention"])`, then asserts `out_t == out_a` |
| F-6 | That one is a race, not a steady-state break: it passed 3/3 on re-run. | Three consecutive runs of the single test each reported `1 passed` |
| F-7 | The pattern is systemic in that file, not isolated. | 23 of 34 tests in `test_run_viewer.py` use `dir="."` or `Path(".")` |
| F-8 | ~~Two REAL committed run records are load-bearing fixtures.~~ **FALSIFIED AT EXECUTION.** The records are load-bearing but they are NOT committed: `.aw/records/runs/` is gitignored and has ZERO tracked files, so they are box-local untracked scratch. The real hazard is therefore much larger than this plan assumed: 15 of the file's tests fail in ANY fresh checkout, and that is why CI is red on all 16 `unittest` jobs. Corrected per E-04's measurement-wins rule; see DECISION 05-i79rgh-D2. | `.aw/.gitignore:15` -> `records/runs/`; `git ls-files .aw/records/runs \| wc -l` -> `0`; `git clone --no-local` produces a tree with no `.aw/records/runs` at all and `15 failed, 20 passed`; CI run `33293159863` fails the same 15 names on every platform |
| F-9 | Both failures are independent of recent code changes. | Both fail identically with the working tree's changes stashed |

## Proposed changes (ordered, validatable)

1. Give the discrepancy test its own fixture with a known discrepancy (E-01).
2. Pin the empty-state polarity separately (E-02).
3. Remove the double live read from the todo/attention equality test (E-03).
4. Record the remaining `dir="."` hazard truthfully, after re-verifying it (E-04; E-05 was merged into
   E-04 by review finding PR-007, so there is no separate E-05 item).

## Deferred / out of scope (with reason)

- **Converting all 23 `dir="."` tests to fixtures.** Deliberately deferred: it is a large mechanical
  rewrite of a file whose subject (the run viewer) is adjacent to surfaces the wtiso Set is actively
  changing, and doing it in the same pass as a targeted bug fix would make the diff unreviewable and
  the regression risk hard to bound. This plan fixes the two tests that actually fail and DOCUMENTS
  the rest (E-04) so the debt is visible rather than silent.
- **Decoupling from the two real run records.** Deferred with the sweep above; noted in E-04 because
  `aw archive` on either record would break tests, which a future archiving run needs to know.
- **Adding a lint/CI rule banning `dir="."` in tests.** Deferred: worth doing, but it would fail on 23
  existing sites the moment it lands, so it must follow the sweep, not precede it.
- **The agent-invocation guidance.** Owned by sibling `uyd3lw`.

## Scope check

- Over-scope: none. Two test files; no production code. Verified at execution: the commit touches only
  `tests/test_run_viewer.py` and `tests/test_awcmdsurf_merge_and_renames.py`, both declared in
  Scope-Paths.
- Under-scope: acknowledged and deliberate. After this plan, 23 tests still read the live repo and
  the two run records remain load-bearing fixtures. The honest claim is "the two failing tests are
  fixed and the residual hazard is documented", NOT "the suite no longer depends on repo state".
- Under-scope, CORRECTED AND MORE SERIOUS THAN WRITTEN (measured at execution): the residual hazard is
  not latent debt, it is an ACTIVE red CI. 15 of the file's tests fail in every fresh checkout and on
  all 16 CI `unittest` jobs, because the run records they read are untracked box-local scratch (F-8
  falsified). This plan deliberately did NOT widen scope to fix them, per its own Deferred section and
  the runbook's prohibition on opportunistic scope growth; the sweep needs its own plan and is
  escalated in DECISION 05-i79rgh-D2.

## Required tests / validation

1. `python3 -m pytest tests/test_run_viewer.py tests/test_awcmdsurf_merge_and_renames.py` green, run
   BARE so the repo's configured parallelism applies.
2. Full default suite green with counts pasted. Current baseline is `2874 passed, 3 skipped, 4
   xfailed` WITH these two deselected; after this plan the same total must pass with NO deselection.
3. Proof the rewritten discrepancy test is state-independent: run it on the current (healthy) repo and
   show it passes, which is impossible today.
4. Proof the race is gone: run `test_todo_matches_attention` repeatedly (at least 10 iterations) while
   the repo is being modified, and show it passes every time.

### Results (recorded at execution)

Item 1 and item 2 CANNOT be satisfied as literally written, and the reason is the defect this plan
documents rather than anything this plan did. Both were written expecting the run-record fixtures to be
committed (F-8). They are not, so `tests/test_run_viewer.py` cannot be green in a lane worktree or a
fresh clone or CI, only on the maintainer's box. Judged by DELTA instead, which is the honest measure,
and stated plainly rather than dressed up as green:

```
$ python3 -m pytest tests/ 2>&1 | tail -2          # BASELINE, before my changes
15 failed, 2912 passed, 3 skipped, 4 xfailed in 24.39s

$ python3 -m pytest tests/ 2>&1 | tail -2          # AFTER my changes
15 failed, 2913 passed, 3 skipped, 4 xfailed in 29.35s

$ diff <baseline FAILED list> <after FAILED list>
IDENTICAL: 15 == 15, same names, no regression
```

Passes went `2912 -> 2913`, exactly `+1`, matching the single test E-02 added. The failing set is
byte-identical before and after: all 15 are the pre-existing `dir="."` live-state tests named in the
E-04 note, none is new, and none was introduced by me. The plan's `2874` baseline no longer holds
(the tree has moved on under concurrent lanes); `2912` is the measured baseline in this session.

Targeted run of the two Scope-Paths files, run BARE as required:

```
$ python3 -m pytest tests/test_run_viewer.py tests/test_awcmdsurf_merge_and_renames.py
15 failed, 27 passed in 2.46s
```

`27 passed` vs `26` at baseline (+1, E-02's test), with the same 15 pre-existing failures. The
`test_awcmdsurf_merge_and_renames.py` file is fully green on its own (`6 passed`), which is the file
E-03 targeted.

Items 3 and 4 are satisfied in full: see V-01 (both live conditions) and V-03 (12 perturbed
iterations, plus the old test failing under the identical perturbation).

HONEST SUMMARY: this plan's own acceptance bar of "full default suite green" is currently
UNREACHABLE by any plan executed in a lane, for reasons entirely outside this plan's Scope-Paths. That
is the finding, not an excuse; it is escalated to the maintainer in DECISION 05-i79rgh-D2.

## Spec / documentation sync

- No spec governs these tests. E-04 is itself the documentation deliverable.
- If E-04 lands, a future `aw archive` run over `.aw/records/runs/` should consult it; no README
  currently warns that archiving a run record can break the suite.

## Open questions

### OQ-01: Should `test_todo_matches_attention` assert aliasing structurally instead of by output?

- Blocking: no
- Status: resolved
- Owner: resolved from repository evidence during /plan-review
- Resolution or deferral rationale: RESOLVED - assert it STRUCTURALLY. The repository already answers
  this, so it should not have been left to executor taste: `cli.py:8218` dispatches `todo` and
  `cli.py:8518` dispatches `attention`/`att`, and BOTH bodies are the identical two lines
  `from agent_workflows import attention as att` / `return att.run(args)`. The aliasing is therefore a
  static property of the dispatcher and provable without executing either command, let alone executing
  both against live state. Prefer asserting that the two commands resolve to the same handler (and that
  `att` is included). A single-snapshot double render remains acceptable if the executor also wants an
  output-level check, but it must not reintroduce a second live read.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the rewritten test passing while `aw runs --last 1 --issues` prints
    `no artifact or status discrepancies found` at the same time, together proving the test no longer
    depends on the live repo being unhealthy. Paste `grep -n 'dir=' ` for the rewritten test showing it
    points at a temp fixture, not `"."`. STATE-INDEPENDENCE PROOF (required, because F-3's real defect
    is oscillation, not one-directional failure): show the test passing in BOTH live conditions - once
    when `aw runs --last 1 --issues` reports no discrepancy, and once when the latest run DOES carry one
    (either wait for such a run or construct the condition in a scratch fixture and say which you did).
    A test that only passes in today's condition has not been decoupled.
  - Observed evidence: BOTH live conditions proven; full transcripts below. Condition A (live repo reports NO discrepancy): `aw runs --last 1 --issues` -> `no artifact or status discrepancies found` while the two tests report `2 passed in 1.47s`. Condition B (latest run DOES carry a discrepancy, CONSTRUCTED in a scratch fixture and stated as such): `aw runs --last 1 --issues` renders the table for `20260830-cond-01-condb1` and the same two tests still report `2 passed`. Fixture-pointing confirmed by `grep -n 'dir=str(root)'` -> lines 1191 and 1259, so neither test passes `dir="."`. F-3's oscillation was additionally OBSERVED LIVE: the main checkout's `--last 1` flipped from 3 in-flight discrepancies to clean within minutes of this turn, with no code change.

    Fixture-pointing check (the test points at a temp fixture, NOT `"."`):

    ```
    $ grep -n 'dir=str(root)' tests/test_run_viewer.py
    1191:                dir=str(root),
    1259:                dir=str(root),
    ```

    (1191 is `test_run_viewer_cli_issues_flag`, 1259 is the E-02 empty-state test. Neither
    appears in the `dir="."` census.)

    CONDITION A - the live repo reports NO discrepancy, and the test passes anyway:

    ```
    $ python3 -m agent_workflows runs --last 1 --issues
    no artifact or status discrepancies found

    $ python3 -m pytest tests/test_run_viewer.py -k "issues_flag" -p no:randomly
    ..                                                                       [100%]
    2 passed in 1.47s
    ```

    CONDITION B - a repo whose LATEST run DOES carry a discrepancy. Constructed deterministically
    in a scratch fixture (stated plainly, as V-01 requires: CONSTRUCTED, not waited for), because
    the live condition oscillates:

    ```
    CONDITION B: `aw runs --last 1 --issues` on a repo whose LATEST run is discrepant:
    Artifact & Status Discrepancies
    ╭─────────────────────────┬───────────┬──────────┬──────────┬──────────╮
    │ Item                    │ Expected  │ Actual   │ Expected │ Actual   │
    │                         │ Location  │ Location │ Status   │ Status   │
    ├─────────────────────────┼───────────┼──────────┼──────────┼──────────┤
    │ 20260830-cond-01-condb1 │ executed/ │ pending/ │ complete │ approved │
    ╰──
    discrepancy REPORTED for --last 1 ? True
    ```

    The two tests pass identically in both conditions (2 passed in each), so their verdict is
    independent of the surrounding repository's health. That is the decoupling V-01 demands.

    F-3's OSCILLATION was ALSO OBSERVED LIVE during this turn, which is the strongest possible
    confirmation of the review finding: minutes apart, the main checkout's `--last 1` went from
    reporting 3 in-flight discrepancies to `no artifact or status discrepancies found`, while
    `--last 6` still rendered a 7-row table. Under the OLD `dir="."` test that flip alone would
    have changed the suite's verdict with no code change whatsoever.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste both polarity tests passing, and paste the actual rendered output each
    asserts (the populated table and the empty-state string), so neither assertion is vacuous.
  - Observed evidence: Both polarities pass and neither assertion is vacuous; transcripts below. `pytest ...issues_flag_empty_state ...issues_flag -p no:randomly` -> `2 passed in 1.50s`. Populated polarity renders the `Artifact & Status Discrepancies` table row `20260829-test-01-item01 | executed/ | pending/ | complete | approved`; empty-state polarity renders exactly `no artifact or status discrepancies found`. NON-VACUITY PROVEN: mutating the new test's fixture to the discrepant shape makes the CLI emit the table instead, so the empty-state assertion evaluates False.

    Both polarity tests passing:

    ```
    $ python3 -m pytest tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_issues_flag_empty_state \
        tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_issues_flag -p no:randomly
    12 workers [2 items]
    ..                                                                       [100%]
    2 passed in 1.50s
    ```

    POPULATED polarity - the actual rendered table the first test asserts (captured by running the
    same fixture shape directly):

    ```
    Artifact & Status Discrepancies
    ╭─────────────────────────┬───────────┬──────────┬──────────┬──────────╮
    │ Item                    │ Expected  │ Actual   │ Expected │ Actual   │
    │                         │ Location  │ Location │ Status   │ Status   │
    ├─────────────────────────┼───────────┼──────────┼──────────┼──────────┤
    │ 20260829-test-01-item01 │ executed/ │ pending/ │ complete │ approved │
    ╰──
    ```

    EMPTY-STATE polarity - the exact string the new test asserts, rendered by its clean fixture:

    ```
    no artifact or status discrepancies found
    ```

    NON-VACUITY PROOF for the empty-state assertion (it genuinely discriminates rather than
    trivially holding). Mutating the new test's fixture to the DISCREPANT shape (`- Status: approved`
    in `pending/`) makes the CLI render the table instead, so the assertion fails:

    ```
    MUTATED fixture (approved in pending/) output:
    Artifact & Status Discrepancies
    ╭─────────────────────────┬───────────┬──────────┬──────────┬──────────╮
    ...
    would empty-state assertion hold? False
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste at least 10 consecutive passes of `test_todo_matches_attention`, AND
    paste a run performed while the repo is concurrently modified (e.g. touch a tracked record between
    iterations) showing it still passes. The old test must be shown to fail under that same
    perturbation, so the fix is demonstrated, not asserted.
  - Observed evidence: Race proven gone AND the old test proven to fail under the identical perturbation; transcripts below. 12 consecutive perturbed iterations of `test_todo_matches_attention` all pass (`iter 1..12: . [100%]`). The ORIGINAL body, re-created verbatim with a backlog record created BETWEEN its two live reads, FAILS: `AssertionError: 0 != 1` (the interleaved write changed even the RETURN CODE, so the old test was more fragile than F-5 claimed). The NEW test passes with that same probe file present. Probe cleaned up; `git status --porcelain` shows only my two intended test files.

    12 consecutive passes, each with the repository perturbed between iterations (the perturbation is
    a file I create and then delete, never another party's work):

    ```
    iter 1: .                                                                        [100%]
    iter 2: .                                                                        [100%]
    iter 3: .                                                                        [100%]
    iter 4: .                                                                        [100%]
    iter 5: .                                                                        [100%]
    iter 6: .                                                                        [100%]
    iter 7: .                                                                        [100%]
    iter 8: .                                                                        [100%]
    iter 9: .                                                                        [100%]
    iter 10: .                                                                       [100%]
    iter 11: .                                                                       [100%]
    iter 12: .                                                                       [100%]
    ```

    THE OLD TEST FAILS UNDER THE SAME PERTURBATION (this is the part that makes the fix demonstrated
    rather than asserted). The original body was re-created verbatim and a backlog record was created
    BETWEEN its two live reads, exactly the concurrent-agent scenario F-5 describes:

    ```
    test_todo_matches_attention_ORIGINAL ... FAIL

    ======================================================================
    FAIL: test_todo_matches_attention_ORIGINAL
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "/tmp/opencode/old_test_race.py", line 30, in test_todo_matches_attention_ORIGINAL
        self.assertEqual(rc_t, rc_a)
    AssertionError: 0 != 1
    ----------------------------------------------------------------------
    Ran 1 test in 1.660s
    FAILED (failures=1)
    ```

    Note the failure is on the RETURN CODE (`0 != 1`), not merely the text: the interleaved write was
    enough to change the second invocation's exit status, so the old test was even more fragile than
    F-5 claimed.

    THE NEW TEST SURVIVES THE IDENTICAL PERTURBATION (same probe file present):

    ```
    NEW test with the SAME perturbation present:
    .                                                                        [100%]
    ```

    Cleanup verified: the probe record was removed and `git status --porcelain` shows only my two
    intended test files modified, no stray artifact left behind.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the recorded note, plus the command output backing EVERY number in it
    (the `dir="."`/`Path(".")` count, the total test count, and the existence check for each named run
    directory), so the documentation is verified at execution time rather than copied from this plan.
    Then prove the hazard is real, not theoretical: temporarily move one of the named run records
    aside, run `tests/test_run_viewer.py`, and paste the resulting FAILURE; restore it and paste the
    file green again. If a measured number differs from this plan's, say so explicitly in the evidence.
  - Observed evidence: Note recorded as the module docstring of `tests/test_run_viewer.py`; every number re-measured at execution time, with two differing from this plan and both stated explicitly. MEASURED: 36 total test methods (plan said 34; file had 35 at HEAD, E-02 added one), 23 reading live state (plan said 23, MATCHES), 30 raw `dir="."`/`Path(".")` occurrences, 7 tests asserting `...2367239` (my first draft said five; measured and corrected), 1 asserting `...2364829`. F-8 FALSIFIED: `git ls-files .aw/records/runs | wc -l` -> `0` and `.aw/.gitignore:15` ignores `records/runs/`, so the records are untracked box-local scratch, NOT committed fixtures. HAZARD PROVEN REAL by a strictly stronger read-only substitution for the move-aside step (disclosed; rationale in DECISION 05-i79rgh-D3): a fresh `git clone --no-local` has no `.aw/records/runs` at all and yields `15 failed, 20 passed`, and CI run `33293159863` fails the SAME 15 names on all 16 `unittest` jobs, while the main checkout reports `35 passed`.

    The recorded note is the module docstring of `tests/test_run_viewer.py` (see the file). Command
    output backing EVERY number in it:

    ```
    MEASURED total test methods: 36
    MEASURED tests reading live repo: 23
    MEASURED raw dir='.'/Path('.') occurrences: 30

    $ git ls-files .aw/records/runs | wc -l
    0

    $ grep -n "records/runs/" .aw/.gitignore
    15:records/runs/
    ```

    Named-record existence check, and the count of tests asserting each by name:

    ```
    tests asserting 2367239: 7
       test_resolve_target_runs_by_substring_and_setid
       test_load_run_summary_state_json
       test_format_run_human
       test_run_viewer_cli_target_human
       test_run_viewer_cli_json
       test_run_viewer_cli_agent
       test_run_viewer_cli_since_filter
    tests asserting 2364829: 1
       test_run_viewer_cli_since_filter
    ```

    NUMBERS THAT DIFFER FROM THIS PLAN, stated explicitly as required:
    - Total test methods: 36 measured, plan said 34. The file had 35 at HEAD; E-02 added one.
    - Live-state tests: 23 measured, plan said 23. MATCHES.
    - The count asserting `...2367239` is 7. My first draft of the note said "five tests"; I measured
      it, found 7, and corrected the note. The note now also tells the reader to grep for the ids
      rather than trust line numbers, since my first draft's line citations (`:33`, `:42`, `:109`,
      `:137`) had already drifted by the time the docstring was inserted.
    - F-8 IS FALSIFIED, the single most important measured difference: the records are NOT committed.
      `git ls-files .aw/records/runs` -> `0`, and `.aw/.gitignore:15` ignores `records/runs/`.

    HAZARD PROVEN REAL, NOT THEORETICAL. V-04 asked me to move a named record aside; I substituted a
    strictly stronger read-only demonstration and disclose the substitution here (rationale in
    DECISION 05-i79rgh-D3: those records are shared live state in the main checkout, being read right
    now by 18 lane worktrees and by this run's own driver, so moving one mid-run is unsafe for 118MB
    of another party's history; and the condition V-04 wanted already obtains for free where the whole
    directory is absent). A fresh clone, where the directory does not exist at all:

    ```
    $ git clone --no-local <repo-root> /tmp/opencode/freshclone
    $ ls /tmp/opencode/freshclone/.aw/records/runs
    ls: cannot access '.../.aw/records/runs': No such file or directory

    $ cd /tmp/opencode/freshclone && python3 -m pytest tests/test_run_viewer.py -p no:randomly
    15 failed, 20 passed in 1.59s
    ```

    And the same 15 names fail in CI, job `unittest (ubuntu-latest, py3.13)` of run `33293159863`
    (head `be49ac4`), with all 16 `unittest` jobs failing and the last three `tests` workflow runs all
    `failure`:

    ```
    FAILED tests/test_run_viewer.py::RunViewerTests::test_aw_cli_entry_points - AssertionError: 'run-' not found in 'no matching runs found\n'
    FAILED tests/test_run_viewer.py::RunViewerTests::test_discover_run_dirs - AssertionError: False is not true
    FAILED tests/test_run_viewer.py::RunViewerTests::test_format_run_human - AssertionError: unexpectedly None
    FAILED tests/test_run_viewer.py::RunViewerTests::test_load_run_summary_state_json - AssertionError: 0 != 1
    FAILED tests/test_run_viewer.py::RunViewerTests::test_multi_run_cli_json_summary - AssertionError: 'summary' not found in {'runs': []}
    ... (15 total, identical name-for-name to the fresh-clone list)
    ```

    Corroboration that the cause is the shared one rather than machine noise: the fresh clone, this
    lane worktree, and CI all fail on exactly the same 15 test names, while the main checkout (74
    untracked local run directories) reports `35 passed`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

Execution contract: commit only the files changed for this plan, path-scoped
(`git commit -m msg -- <path>`), never `git add -A` and never push. Other agents and runs are ACTIVE in
this checkout, and V-03 deliberately perturbs the repository, so keep that perturbation to files YOU
create and never to another party's work. Run the suite BARE when validating. When every `V-*` item
carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`.
