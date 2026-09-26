# IPD: Make slow-marked tests visible: CI runs them, the default run reports what it deselected, release-review requires the full suite

- Date: 2026-09-26
- Kind: child
- Concern: `pyproject.toml` `addopts` deselects every `slow`-marked test (`-m 'not slow and not livecorpus'`), and every consumer of the default command inherits that: agents (told to run bare), `make test`, the runner's suite gate, AND CI (`.github/workflows/tests.yml` "Run self-tests (parallel)" runs `python -m pytest tests/ -n auto -q`, which inherits `addopts`). So CI has never run the 172 slow tests, and the default xdist summary prints only `N passed` with no deselected count, so nothing tells a reader the number is partial. Measured at HEAD `61ef21d8`: `-m slow` gives `3 failed, 169 passed in 66.99s`.
- Scope: IN: an advisory CI step that runs the slow set; a notice on every default run naming how many tests were deselected and how to run them; the release-review final-validation section requiring the full-suite target; correcting the two comments that claim CI runs the full suite; recording the fail-closed flip condition on the three owning bug items. OUT: fixing the 3 slow failures (owned by 57dwkc, 3ypquf, 4vfkl1); changing `addopts` itself.
- Scope-Paths: .github/workflows/tests.yml, conftest.py, tests/deselect_notice.py, tests/test_deselect_notice.py, .aw/system/workflows/release-review/08-final-ship-review.md, pyproject.toml, Makefile, .aw/records/backlog/open/20260918-57dwkc-01-57dwkc-deep-cleanup-orphans-layout-json.backlog.md, .aw/records/backlog/open/20260923-3ypquf-01-3ypquf-deep-cleanup-gitignored-readme-at-risk.backlog.md, .aw/records/backlog/open/20260918-4vfkl1-01-4vfkl1-installer-deep-cleanup-leaves-aw-dir.backlog.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: xuc9v0
- Blocks-Release: next
- Set: slowvis
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 4petcj

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog xuc9v0: CI runs the slow set advisorily, the default run prints its deselected count, and release-review requires the full suite; re-measured at HEAD 61ef21d8 (172 slow, 3 failed).

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A green default run, and a green CI, can no longer be mistaken for a green full suite: CI runs the slow set (advisory until its three known failures are fixed), every default run prints how many tests it skipped and how to run them, and release-review requires the full suite as release evidence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: CI runs the slow set

- [ ] E-01 In `.github/workflows/tests.yml` job `unittest`, directly after the step named "Run self-tests (parallel)", add a step named `Run slow-marked tests (ADVISORY until 57dwkc, 3ypquf, 4vfkl1 are fixed)` with `shell: bash`, `continue-on-error: true`, and `run: python -m pytest tests/ -n auto -m slow`. A command-line `-m` overrides the `addopts` `-m` (last wins; measured: `python3 -m pytest -m slow --collect-only` -> `172/2411 tests collected (2239 deselected)`). Add a comment above it stating: why it is advisory (three known failures, each owned by a gated bug item), and the flip condition (remove `continue-on-error` once `-m slow` reports 0 failed on the ubuntu leg, i.e. once 57dwkc, 3ypquf and 4vfkl1 are done). `continue-on-error` is used rather than `|| true` because it keeps the step visibly red in the Actions UI while not failing the job.
  - Depends on: none
  - Expected outcome: every matrix leg runs the 172 slow tests and reports their result without failing the job.
  - Execution state: pending

- [ ] E-02 Record the flip condition on each owning item with `aw backlog note <id6> --message "..."` for `57dwkc`, `3ypquf` and `4vfkl1`: "CI step 'Run slow-marked tests' (tests.yml, plan 4petcj) is advisory because of this item's slow-test failure; when the last of 57dwkc/3ypquf/4vfkl1 closes, remove its continue-on-error so the slow set fails closed."
  - Depends on: E-01
  - Expected outcome: each of the three items carries a history note naming the step and the flip.
  - Execution state: pending

### Task group 2: the default run says what it skipped

- [ ] E-03 Add `tests/deselect_notice.py`, a small pytest plugin, and register it from the root `conftest.py` with `pytest_plugins = ["tests.deselect_notice"]`. It counts deselected items via `pytest_deselected`; on an xdist worker it publishes the count through `config.workeroutput` in `pytest_sessionfinish`; on the controller it reads it in `pytest_testnodedown` (taking the MAX across workers, because every worker collects and deselects the full set, so summing would multiply the count); in `pytest_terminal_summary` it writes one line when the count is nonzero: `NOTE: <N> tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all`. The line MUST NOT begin with a digit, so `runner_shared._SUITE_SUMMARY_RE` (`^(?:=+\s*)?(\d+ (?:passed|failed)...`) and `parse_suite_summary` are unaffected. Serial runs (`-p no:xdist`, `-n0`) must print the same line (there `pytest_deselected` fires on the controller itself). Prototype measured under `-n 2` and `-n0` on a two-test fixture: both printed the line with the count 1.
  - Depends on: none
  - Expected outcome: a bare `python3 -m pytest` ends with the NOTE line naming 2239 (or the then-current) deselected tests; the `N passed` summary line is still present and still parsed.
  - Execution state: pending

- [ ] E-04 Add `tests/test_deselect_notice.py`: in a `tempfile.TemporaryDirectory`, write a `pytest.ini` (`markers = slow`, `addopts = -q -m "not slow"`) and a test file with one plain test and one `@pytest.mark.slow` test; run `sys.executable -m pytest -p tests.deselect_notice` there with `PYTHONPATH` pinned to the repo root, once with `-n 2` and once with `-p no:xdist`; assert exit 0, that stdout contains `NOTE: 1 tests were deselected`, and that `runner_shared.parse_suite_summary(stdout)` still returns a line starting `1 passed`. A third case runs with `-m ""` and asserts the NOTE line is ABSENT (nothing deselected). Outcomes only: no assertion on the plugin's source, and no pinning of the full sentence beyond the stable prefix `NOTE: <n> tests were deselected`. Mark nothing `slow` (the three subprocess runs take about 2s).
  - Depends on: E-03
  - Expected outcome: three cases pass; with the plugin not loaded the first two fail.
  - Execution state: pending

### Task group 3: release-review requires the full suite; stale comments

- [ ] E-05 Edit `.aw/system/workflows/release-review/08-final-ship-review.md` section `## Final validation`: add a MUST paragraph stating that the test evidence for the GO recommendation must come from the repository's FULL test target, including every marker its default invocation deselects (in this toolkit that is `make test-all`, i.e. `python3 -m pytest tests/ -m ''`); that a default run printing a deselected count is the fast subset and is NOT release evidence; and that every failure in the full run is either fixed or listed as an explicit release blocker with its backlog id. Phrase it generically (this file ships to other repositories via the wheel `force-include` of `.aw/system`), naming `make test-all` only as this toolkit's instance. Also correct the two comments that claim CI runs the full suite: `pyproject.toml` (the `addopts` comment "run the FULL suite for release-review / CI with `make test-all`") and `Makefile` (the `test-all` comment "Use for release-review, CI, or before shipping"), so they say CI runs the fast suite plus an advisory slow step.
  - Depends on: none
  - Expected outcome: the shipped release-review body requires the full target; no comment claims CI runs the full suite.
  - Execution state: pending

- [ ] E-06 Run the bare suite `python3 -m pytest`, then `make test-all`.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: bare run green and ending with the NOTE line; `make test-all` shows exactly the three known failures and no new one.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `.aw/system/` IS the shipped source of the workflow bodies: `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]` maps `.aw/system` into `agent_workflows/_data/.aw/system`. There is no separate generator for `08-final-ship-review.md`; edit it in place. `.aw/system/managed-sections.json` records a sha256 for it that is ALREADY stale at HEAD (recorded `54926ba1...`, actual `1c35948e...`; the last body edit `eb5db98a` did not refresh it), so this plan does not touch the manifest.
- `runner_shared.SUITE_CHECK_ARGV` is a bare `python -m pytest`, so the runner's merge gate also runs only the fast subset; this plan does not change that (lanes must stay fast), it only makes the omission visible.
- Tests are stdlib `unittest.TestCase` or plain pytest functions; subprocess CLI spawns pin `PYTHONPATH` to the repo root (`tests/support.run_cli`).
- Tests assert OUTCOMES only (maintainer rule): no test here pins source text, comment wording or workflow prose.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `61ef21d8`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `.github/workflows/tests.yml` step "Run self-tests (parallel)" | CI inherits `addopts` and so never runs a `slow` test; its own comment elsewhere ("the `unittest` job already runs the full suite") is false. | `run: python -m pytest tests/ -n auto -q`; `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"` |
| F-2 | HIGH | slow set | 172 of 2411 tests are `slow`; 3 fail today, all installer deep-cleanup, each owned by an open gated bug. | `-m slow -o addopts="-q -n auto --dist=worksteal"` -> `3 failed, 169 passed in 66.99s`; failures `test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed`, `test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw`, `test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory` |
| F-3 | MED | default summary | Under xdist the summary omits the deselected count entirely (`1 passed in 0.71s`); only a serial run prints `1 passed, 1 deselected`. | two-test fixture, `-n 2` vs `-n0` |
| F-4 | LOW | `pyproject.toml` addopts comment, `Makefile` `test-all` comment | Both say CI uses the full suite; it does not. | quoted strings in E-05 |
| F-5 | INFO | `livecorpus` marker | Currently carried by 0 tests (`-m livecorpus` collects none), so the slow step needs no livecorpus handling. | `no tests collected (2411 deselected)` |
| F-6 | INFO | brief correction | The brief said 2410 tests; HEAD collects 2411. Immaterial. | `2411 tests collected` |

## Proposed changes (ordered, validatable)

1. E-01, E-02: advisory CI slow step and its recorded flip condition.
2. E-03, E-04: deselected-count notice plugin and its outcome test.
3. E-05: release-review full-suite requirement; stale comments.
4. E-06: bare suite and full suite.

## Deferred / out of scope (with reason)

- Flipping the CI slow step to fail-closed (remove `continue-on-error`). It cannot be done now without reddening `main` on three known failures that are other plans' work; the condition is recorded on the owning items by E-02.
  - Carrier: 57dwkc
- Fixing the three slow failures themselves: owned by 57dwkc, 3ypquf and 4vfkl1.
  - Carrier: 3ypquf
- Making the runner's suite gate run the slow set: it would add minutes to every lane merge; this plan only makes the omission visible.
  - Carrier-Declined: deliberate design (fast lane gate); the release-review requirement in E-05 is where the full suite is enforced.

## Scope check

- Over-scope: none. The two comment fixes in E-05 correct claims this plan's own finding F-1 proves false.
- Under-scope: none for the declared concern.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_deselect_notice.py -v` (outcome test, three cases).
- Bare `python3 -m pytest` and `make test-all`.
- Test rule: outcomes only; no test pins source text, docstrings, or workflow wording.

## Spec / documentation sync

`.aw/system/workflows/release-review/08-final-ship-review.md` is a shipped workflow BODY, not a `.spec.md`; it is in Scope-Paths because E-05 amends it. No `.spec.md` is touched: no spec describes the CI matrix or the pytest summary.

## Open questions

### OQ-01: Advisory mechanism: `continue-on-error: true` or `|| true`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `continue-on-error: true`. It keeps the step's real exit status visible (red step, green job) whereas `|| true` makes the step green and hides the failures, which is the exact invisibility this plan fixes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `tests.yml` diff; paste `python3 -c 'import yaml; j=yaml.safe_load(open(".github/workflows/tests.yml"))["jobs"]["unittest"]["steps"]; s=[x for x in j if "slow" in x.get("name","")][0]; print(s["name"], s.get("continue-on-error"), s["run"])'` showing `True` and `-m slow`; paste the local run of the step's exact command's summary line (`python -m pytest tests/ -n auto -m slow`) showing the three known failures and no others.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `grep -n "4petcj" ` over the three backlog item files, showing one note line in each.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the last three lines of a BARE `python3 -m pytest`, showing the `N passed` line AND the `NOTE: <N> tests were deselected` line with N equal to the count from `python3 -m pytest --collect-only -q -o addopts="" -m "slow or livecorpus" | tail -1` (paste that too). Paste `python3 -c` calling `runner_shared.parse_suite_summary` on the captured bare-run output, showing it returns the `N passed` line, not the NOTE line.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_deselect_notice.py -v` showing 3 passed; then, IN THE WORKTREE, temporarily make `tests/deselect_notice.py`'s `pytest_terminal_summary` return without writing, paste the xdist and serial cases FAILING on the missing NOTE line (not on an import or fixture error), restore, and paste green again.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the diff of `08-final-ship-review.md`, `pyproject.toml` and `Makefile`; paste `grep -n "test-all" .aw/system/workflows/release-review/08-final-ship-review.md` showing the new requirement.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the final summary lines of a BARE `python3 -m pytest` (0 failed, NOTE line present) and of `make test-all`, naming every failure in the latter by node id and showing it is one of the three F-2 failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. CI gains one advisory step that runs the 172 slow tests on every matrix leg (about one extra minute per leg) and does not fail the job; the default pytest run gains one NOTE line; the release-review body requires the full suite; two comments are corrected; three backlog items get a history note. No production code changes.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

GENUINE STOP CONDITION: if the NOTE line changes what `runner_shared.parse_suite_summary` returns for a bare run, stop and report, because the runner's merge gate parses that line.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane). Then set backlog item `xuc9v0` `done` with `--evidence` citing the executed plan; this plan carries its `- Blocks-Release: next`.
