# IPD: Fix tests that assert against live repo state instead of a fixture

- Date: 2026-08-29
- Kind: child
- Concern: Two tests assert against the live repo, so they pass or fail for reasons unrelated to the code under test; one currently fails because the latest run happens to be clean and would pass again by accident when a run ends interrupted, and the other is a race between two CLI invocations.
- Scope: The two failing tests plus the fixture seam they need. Fix `test_run_viewer_cli_issues_flag` to build its own discrepancy fixture, and `test_todo_matches_attention` to compare one snapshot two ways. Also record, without fixing, the 23-site `dir="."` pattern in the same file so the systemic risk is visible.
- Scope-Paths: tests/test_run_viewer.py, tests/test_awcmdsurf_merge_and_renames.py
- Item-Dependencies: none
- Status: approved
- Set: testinvoke
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: i79rgh
- Approval: 2026-08-29, recorded via aw ipd set: status set to approved
- Blocks-Release: next

## Workflow history
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-005..PR-008. Self-review of a plan I authored, so every claim was re-verified rather than trusted. PR-005 (FIXED, BLOCKER-class factual error): the plan claimed test_run_viewer_cli_issues_flag now fails PERMANENTLY because the repo got healthier. That is WRONG and would have misled the executor into writing the wrong fix. The test sets last=1 (test_run_viewer.py:1047) so it inspects only the MOST RECENT run: aw runs --last 1 --issues currently reports no discrepancy (fails), but aw runs --last 6 --issues DOES render the table with qcqhj7 and rchpms as interrupted/approved. So the real defect is OSCILLATION - it will pass again by accident the moment a fresh run ends interrupted - which is worse than a hard failure because it teaches re-running until green. Concern, Goal and F-3 all corrected. PR-006 (FIXED, HIGH): because the defect is oscillation, V-01's original evidence (passing once, today) was insufficient; it now demands a state-independence proof showing the test passes in BOTH live conditions, with the executor stating which condition was constructed vs waited for. PR-007 (FIXED, MEDIUM, right-sizing per rubric G): E-04 and E-05 were one concern artificially split - E-05 only re-verified E-04's numbers, which the V-item already required. Merged into a single E-04 that measures at execution time with an explicit rule that a measurement disagreeing with this plan WINS; V-04 now also demands the hazard be proven real by moving a named run record aside and pasting the resulting failure. Bijection stays 4/4 and Highest E allocated stays 05 (ids are not reused). PR-008 (FIXED, MEDIUM): OQ-01 was left to executor taste when the repo already answers it - cli.py:8218 (todo) and cli.py:8518 (attention/att) have byte-identical bodies both returning att.run(args), so the aliasing is statically provable without executing either command; resolved to prefer the structural assertion and E-03 updated. Verified clean: all path:line citations resolve (test_run_viewer.py:1037/:1039/:1047/:1063/:45/:112, test_awcmdsurf_merge_and_renames.py:12/:44-48), 34 tests in the file confirmed, both named run records confirmed present, aw ipd lint conforming at author and review-finalize, gate carries the full execution contract.

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from two live failures observed and measured on this checkout while diagnosing an agent's repeated suite runs.

## Goal

Make the suite's verdict depend on the code under test rather than on the repository's current
contents, so a green suite means the code is correct and a red suite means something is actually
broken. Today one test's result is decided by whether the most recent run happens to be clean, which
teaches every agent and human to re-run until green instead of trusting the suite.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the permanently-failing discrepancy test

- [ ] E-01 Rewrite `test_run_viewer_cli_issues_flag` (`tests/test_run_viewer.py:1037`) to stop passing
      `dir="."`. Build a temporary repo containing exactly one synthetic artifact/status discrepancy
      (the shape the `--issues` table reports), point the namespace at it, and assert the table
      renders that known discrepancy. The test must no longer depend on the live repo containing a
      discrepancy by accident.
  - Depends on: none
  - Expected outcome: the test passes on a HEALTHY repo, which it cannot do today.
  - Execution state: pending

- [ ] E-02 Add the negative case as a separate test: a fixture repo with NO discrepancy must render
      the `no artifact or status discrepancies found` empty-state and exit 0. The current single test
      conflates "the feature works" with "this repo happens to be unhealthy", so both polarities must
      be pinned independently.
  - Depends on: E-01
  - Expected outcome: both the populated and empty states are covered by fixtures.
  - Execution state: pending

### Task group 2: the two-invocation race

- [ ] E-03 Fix `test_todo_matches_attention`
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
  - Execution state: pending

### Task group 3: make the systemic risk visible without a sweeping rewrite

- [ ] E-04 Record the residual hazard in `tests/test_run_viewer.py` (module docstring note), and
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
  - Execution state: pending

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
| F-8 | Two REAL committed run records are load-bearing fixtures. | `run-20260827T212854Z-2364829` and `run-20260827T212958Z-2367239` both exist under `.aw/records/runs/` and are asserted by name (`:45`, `:112`) |
| F-9 | Both failures are independent of recent code changes. | Both fail identically with the working tree's changes stashed |

## Proposed changes (ordered, validatable)

1. Give the discrepancy test its own fixture with a known discrepancy (E-01).
2. Pin the empty-state polarity separately (E-02).
3. Remove the double live read from the todo/attention equality test (E-03).
4. Record the remaining `dir="."` hazard truthfully, after re-verifying it (E-04, E-05).

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

- Over-scope: none. Two test files; no production code.
- Under-scope: acknowledged and deliberate. After this plan, 21 tests still read the live repo and
  two real run records remain load-bearing fixtures. The honest claim is "the two failing tests are
  fixed and the residual hazard is documented", NOT "the suite no longer depends on repo state".

## Required tests / validation

1. `python3 -m pytest tests/test_run_viewer.py tests/test_awcmdsurf_merge_and_renames.py` green, run
   BARE so the repo's configured parallelism applies.
2. Full default suite green with counts pasted. Current baseline is `2874 passed, 3 skipped, 4
   xfailed` WITH these two deselected; after this plan the same total must pass with NO deselection.
3. Proof the rewritten discrepancy test is state-independent: run it on the current (healthy) repo and
   show it passes, which is impossible today.
4. Proof the race is gone: run `test_todo_matches_attention` repeatedly (at least 10 iterations) while
   the repo is being modified, and show it passes every time.

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

- [ ] V-01 validates E-01
  - Required evidence: paste the rewritten test passing while `aw runs --last 1 --issues` prints
    `no artifact or status discrepancies found` at the same time, together proving the test no longer
    depends on the live repo being unhealthy. Paste `grep -n 'dir=' ` for the rewritten test showing it
    points at a temp fixture, not `"."`. STATE-INDEPENDENCE PROOF (required, because F-3's real defect
    is oscillation, not one-directional failure): show the test passing in BOTH live conditions - once
    when `aw runs --last 1 --issues` reports no discrepancy, and once when the latest run DOES carry one
    (either wait for such a run or construct the condition in a scratch fixture and say which you did).
    A test that only passes in today's condition has not been decoupled.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste both polarity tests passing, and paste the actual rendered output each
    asserts (the populated table and the empty-state string), so neither assertion is vacuous.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste at least 10 consecutive passes of `test_todo_matches_attention`, AND
    paste a run performed while the repo is concurrently modified (e.g. touch a tracked record between
    iterations) showing it still passes. The old test must be shown to fail under that same
    perturbation, so the fix is demonstrated, not asserted.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the recorded note, plus the command output backing EVERY number in it
    (the `dir="."`/`Path(".")` count, the total test count, and the existence check for each named run
    directory), so the documentation is verified at execution time rather than copied from this plan.
    Then prove the hazard is real, not theoretical: temporarily move one of the named run records
    aside, run `tests/test_run_viewer.py`, and paste the resulting FAILURE; restore it and paste the
    file green again. If a measured number differs from this plan's, say so explicitly in the evidence.
  - Observed evidence:
  - Result: pending

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
