# IPD: Make slow-marked tests visible: CI runs them, the default run reports what it deselected, release-review requires the full suite

- Date: 2026-09-26
- Kind: child
- Concern: `pyproject.toml` `addopts` deselects every `slow`-marked test (`-m 'not slow and not livecorpus'`), and every consumer of the default command inherits that: agents (told to run bare), `make test`, the runner's suite gate, AND CI (`.github/workflows/tests.yml` "Run self-tests (parallel)" runs `python -m pytest tests/ -n auto -rs`, which inherits `addopts`). So CI has never run the slow tests, and the default xdist summary prints only `N passed` with no deselected count, so nothing tells a reader the number is partial. Measured at HEAD `61ef21d8`: `-m slow` gives `3 failed, 169 passed in 66.99s`. RE-MEASURED AT REVIEW on HEAD `05fa2a7b`: the set is now 174 slow of 2634 total (2460 deselected) and `-m slow` gives `4 failed, 170 passed in 49.12s`. The fourth failure is a same-day REGRESSION owned by no backlog item, which is this concern demonstrating itself (F-8).
- Scope: IN: an advisory CI step that runs the slow set; a notice on every default run naming how many tests were deselected and how to run them; the release-review final-validation section requiring the full-suite target; correcting the two comments that claim CI runs the full suite; recording the fail-closed flip condition on the three owning bug items. OUT: fixing the 3 slow failures (owned by 57dwkc, 3ypquf, 4vfkl1); changing `addopts` itself.
- Scope-Paths: .github/workflows/tests.yml, conftest.py, tests/deselect_notice.py, tests/test_deselect_notice.py, .aw/system/workflows/release-review/08-final-ship-review.md, pyproject.toml, Makefile, .aw/records/backlog/open/20260918-57dwkc-01-57dwkc-deep-cleanup-orphans-layout-json.backlog.md, .aw/records/backlog/graduated/20260923-3ypquf-01-3ypquf-deep-cleanup-gitignored-readme-at-risk.backlog.md, .aw/records/backlog/open/20260918-4vfkl1-01-4vfkl1-installer-deep-cleanup-leaves-aw-dir.backlog.md, .aw/records/backlog/open/20260926-g0bdgg-01-g0bdgg-subcommand-description-gaps.backlog.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
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
- 2026-09-27 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 4petcj verified (set slowvis, attempt 1). [Scope reconciliation - widened-scope .aw/records/backlog/open/20260926-g0bdgg-01-g0bdgg-subcommand-description-gaps.backlog.md: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run)]
- 2026-09-26 approved (aw set): status set to approved
- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed in place

- 2026-09-26 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 all FIXED in place. Ran the described plugin design on a scratch fixture and it ABORTS under `-p no:xdist` (`PluginValidationError: unknown hook 'pytest_testnodedown'`, exit 3) because that hook is xdist-owned; `-n 0` cannot catch it, which is why the authored prototype passed. E-03 now registers it behind a `hasplugin("xdist")` probe (verified correct on `-n 2`/`-n 0`/`-p no:xdist`/`-m ""`) and E-04 gains a distinct `-n 0` case plus an INTERNALERROR-absent assertion. Re-measured the slow set: FOUR failures, not three, and the fourth (`SubcommandDescriptionTests::test_every_subparser_has_fuller_description`, eight subparser description gaps) is owned by NO backlog item and landed the same day via executed plan `8ud1is`, so E-02 now re-derives the set and files a gated bug item for any unowned failure. Corrected a `- Scope-Paths:` entry pointing at a moved file (`3ypquf` is graduated), restated drifted counts as properties (174/2634 now, was 172/2411), and fixed the mis-quoted CI command (`-rs`, not `-q`). Verified the gate's stop condition is safe (`parse_suite_summary` still returns the count line with the NOTE present) and that nothing enforces the stale `managed-sections.json` digest. Findings F-7..F-12 added. Watermark unchanged at 06.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog xuc9v0: CI runs the slow set advisorily, the default run prints its deselected count, and release-review requires the full suite; re-measured at HEAD 61ef21d8 (172 slow, 3 failed).

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A green default run, and a green CI, can no longer be mistaken for a green full suite: CI runs the slow set (advisory until its three known failures are fixed), every default run prints how many tests it skipped and how to run them, and release-review requires the full suite as release evidence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: CI runs the slow set

- [x] E-01 In `.github/workflows/tests.yml` job `unittest`, directly after the step named "Run self-tests (parallel)", add a step named `Run slow-marked tests (ADVISORY until the known slow failures are fixed)` with `shell: bash`, `continue-on-error: true`, and `run: python -m pytest tests/ -n auto -m slow`. A command-line `-m` overrides the `addopts` `-m` (last wins; re-measured at review: `python3 -m pytest -m slow --collect-only -q -o addopts=""` -> `174/2634 tests collected (2460 deselected)`). Add a comment above it stating: why it is advisory (the known slow failures, each named with its owning item or, for an unowned one, its newly filed item), and the flip condition (remove `continue-on-error` once `-m slow` reports 0 failed on the ubuntu leg, i.e. once every owning item is done). `continue-on-error` is used rather than `|| true` because it keeps the step visibly red in the Actions UI while not failing the job.
  - DO NOT NAME THE OWNING ITEM IDS IN THE STEP NAME. The step name is a GitHub Actions UI label that appears in every run; embedding `57dwkc, 3ypquf, 4vfkl1` there makes it wrong the moment the failure set changes, and it already IS wrong (review measured FOUR failures, one of them owned by none of those three: PR-002). Put the ids in the COMMENT, which E-02 keeps in step with the items, and keep the name stable.
  - Depends on: none
  - Expected outcome: every matrix leg runs the slow set (174 at review-time HEAD; re-derive) and reports its result without failing the job.
  - Execution state: performed

- [x] E-02 RE-DERIVE THE FAILING SET FIRST, then record the flip condition on each owning item. Run `python3 -m pytest -m slow -o addopts="-q -n auto --dist=worksteal"` and take the ACTUAL `FAILED` node ids as the authority; do not assume the three the plan was authored against. For each failure, find its owning backlog item; for any failure with NO owning item, FILE ONE with `aw backlog new` (`--work-kind bug`, and `--blocks-release next` per the repository's "every live bug gates the next release" rule) before proceeding, and add its path to this plan's own record of the set. Then `aw backlog note <id6> --message "..."` on every owning item (use `aw backlog note`, NOT `aw backlog set`: a note changes no status, which is what this is): "CI step 'Run slow-marked tests' (tests.yml, plan 4petcj) is advisory because of this item's slow-test failure; when the last of the owning items closes, remove its continue-on-error so the slow set fails closed." Name the concrete id list in the message you write.
  - AT REVIEW THE SET WAS FOUR, NOT THREE, AND ONE WAS UNOWNED (PR-002, F-8). `tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description` fails on eight subparser description gaps (`upgrade-test list/new/sandboxes/probe/env/clean` have EMPTY descriptions; `config unset` and `conf unset` have a description shorter than their help). It is `slow`-marked via the module-level `pytestmark = pytest.mark.slow` in `tests/test_cli.py`, which is why the default run never saw it. It was introduced the same day by commit `64859728` ("feat(upgrade-test): restore safety tests and graduate harness to aw upgrade-test", plan `8ud1is`, already executed), so it is a REGRESSION this plan's own CI step would have caught and is exactly the class of defect the plan exists to surface. It must be filed rather than folded silently into the advisory comment.
  - ALSO NOTE `3ypquf` IS NO LONGER `open`: it is `graduated` (to plan Set `deepclean`, pending plan `baxbdh`), so it now lives at `.aw/records/backlog/graduated/20260923-3ypquf-01-...backlog.md`. This plan's `- Scope-Paths:` still names the `open/` path, which does not exist (PR-003); the path is corrected there. A note on a graduated item is still correct and still the right place for the flip condition, since the item is the durable carrier until its plan executes.
  - Depends on: E-01
  - Expected outcome: every failure in the re-derived slow set has an owning item, each owning item carries a history note naming the step and the flip, and any previously unowned failure has a newly filed gated bug item whose id6 is recorded here and in the E-01 comment.
  - Execution state: performed

### Task group 2: the default run says what it skipped

- [x] E-03 Add `tests/deselect_notice.py`, a small pytest plugin, and register it from the root `conftest.py` with `pytest_plugins = ["tests.deselect_notice"]`. It counts deselected items via `pytest_deselected`; on an xdist worker it publishes the count through `config.workeroutput` in `pytest_sessionfinish`; on the controller it reads it in `pytest_testnodedown` (taking the MAX across workers, because every worker collects and deselects the full set, so summing would multiply the count); in `pytest_terminal_summary` it writes one line when the count is nonzero: `NOTE: <N> tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all`. The line MUST NOT begin with a digit, so `runner_shared._SUITE_SUMMARY_RE` (`^(?:=+\s*)?(\d+ (?:passed|failed)...`) and `parse_suite_summary` are unaffected.
  - DECLARE `pytest_testnodedown` CONDITIONALLY OR `-p no:xdist` HARD-CRASHES (review PR-001, measured F-7). `pytest_testnodedown` is an XDIST-OWNED hook. A plugin that defines it at module level is validated against the loaded hookspecs at registration, so with xdist ABSENT pytest aborts before collection with `INTERNALERROR> pluggy._manager.PluginValidationError: unknown hook 'pytest_testnodedown'` and exit 3 (measured on the plan's own described design). That is not a corner case: E-04 REQUIRES a `-p no:xdist` case, and `make test-serial` exists. `-n0` does NOT reproduce it (xdist is still loaded, just with zero workers), which is exactly why the plan's `-n0` prototype looked fine. THE FIX, measured working on all four invocations (`-n 2`, `-n 0`, `-p no:xdist`, `-m ""`): keep the module-level hooks limited to `pytest_deselected` / `pytest_sessionfinish` / `pytest_terminal_summary` / `pytest_configure`, and in `pytest_configure` register the xdist hook only behind a capability probe, `if config.pluginmanager.hasplugin("xdist"): config.pluginmanager.register(<small object defining pytest_testnodedown>, "...")`. Do not instead `try: import xdist` at module scope, which tests importability rather than whether THIS run loaded the plugin.
  - THE PER-PROCESS COUNTER MUST NOT LIVE ON `config` ALONE: `pytest_deselected(items)` receives no `config`, so the count is accumulated in module state and read back in `pytest_terminal_summary` (which does receive `config`). Take `max(worker_max, local_count)` so the serial path (where `pytest_deselected` fires on the controller itself) and the xdist path share one code path.
  - Serial runs (`-p no:xdist`, `-n0`) must print the same line. MEASURED at review with the guarded design: `-n 2` -> NOTE present, `-n 0` -> NOTE present, `-p no:xdist` -> NOTE present (exit 0, no INTERNALERROR), `-m ""` -> NOTE correctly ABSENT. The MAX-not-SUM reasoning was also verified rather than assumed: with 10 deselected and `-n 4`, per-worker counts were `[10, 10, 10, 10]`, so MAX=10 (correct) and SUM=40 (wrong by 4x).
  - Depends on: none
  - Expected outcome: a bare `python3 -m pytest` ends with the NOTE line naming the then-current deselected count (2460 at review-time HEAD; re-derive, do not hardcode); the `N passed` summary line is still present and still parsed; `-p no:xdist` exits normally with the same line.
  - Execution state: performed

- [x] E-04 Add `tests/test_deselect_notice.py`: in a `tempfile.TemporaryDirectory`, write a `pytest.ini` (`markers = slow`, `addopts = -q -m "not slow"`) and a test file with one plain test and one `@pytest.mark.slow` test; run `sys.executable -m pytest -p tests.deselect_notice` there with `PYTHONPATH` pinned to the repo root, once with `-n 2` and once with `-p no:xdist`; assert exit 0, that stdout contains `NOTE: 1 tests were deselected`, and that `runner_shared.parse_suite_summary(stdout)` still returns a line starting `1 passed`. A third case runs with `-m ""` and asserts the NOTE line is ABSENT (nothing deselected). ADD A FOURTH case with `-n 0`, because `-n 0` and `-p no:xdist` are NOT equivalent (the first still loads xdist) and only the second catches the hook-validation crash of PR-001; a suite that tests one and not the other cannot detect that regression. Each case MUST assert the run did not abort: check exit 0 AND that `INTERNALERROR` is absent from stdout, since a pluggy validation failure exits 3 with no NOTE line and a bare "missing NOTE" assertion would report it as the wrong defect. Outcomes only: no assertion on the plugin's source, and no pinning of the full sentence beyond the stable prefix `NOTE: <n> tests were deselected`. Mark nothing `slow` (the four subprocess runs take about 2s).
  - Depends on: E-03
  - Expected outcome: four cases pass; with the plugin not loaded the `-n 2`, `-n 0` and `-p no:xdist` cases fail on the missing NOTE line; with the xdist hook declared UNCONDITIONALLY (the PR-001 bug) the `-p no:xdist` case fails on `INTERNALERROR`/exit 3 while the others still pass.
  - Execution state: performed

### Task group 3: release-review requires the full suite; stale comments

- [x] E-05 Edit `.aw/system/workflows/release-review/08-final-ship-review.md` section `## Final validation`: add a MUST paragraph stating that the test evidence for the GO recommendation must come from the repository's FULL test target, including every marker its default invocation deselects (in this toolkit that is `make test-all`, i.e. `python3 -m pytest tests/ -m ''`); that a default run printing a deselected count is the fast subset and is NOT release evidence; and that every failure in the full run is either fixed or listed as an explicit release blocker with its backlog id. Phrase it generically (this file ships to other repositories via the wheel `force-include` of `.aw/system`), naming `make test-all` only as this toolkit's instance. Also correct the two comments that claim CI runs the full suite: `pyproject.toml` (the `addopts` comment "run the FULL suite for release-review / CI with `make test-all`") and `Makefile` (the `test-all` comment "Use for release-review, CI, or before shipping"), so they say CI runs the fast suite plus an advisory slow step.
  - Depends on: none
  - Expected outcome: the shipped release-review body requires the full target; no comment claims CI runs the full suite.
  - Execution state: performed

- [x] E-06 Run the bare suite `python3 -m pytest`, then `make test-all`.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: bare run green and ending with the NOTE line; `make test-all` shows exactly the KNOWN failures re-derived in E-02 (four at review-time HEAD, each with an owning item after E-02) and no NEW one. State the bar as a PROPERTY, not a count: every `FAILED` node id in the full run must appear in E-02's re-derived, now-owned set. Baseline measured at review on HEAD `05fa2a7b` for comparison: bare `2458 passed, 2 skipped in 36.56s`; `make test-all` `4 failed, 2628 passed, 2 skipped in 77.02s`.
  - Execution state: performed


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

Added at review, measured on HEAD `05fa2a7b`. THE NUMBERS IN F-2/F-5/F-6 HAVE ALREADY DRIFTED, which is itself the argument for stating bars as properties: the suite is now 2634 tests with 174 `slow` (was 2411/172), and the deselected count is 2460 (was 2239). `livecorpus` is still carried by 0 tests, so F-5 holds.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-7 | HIGH | E-03's described plugin design | DECLARING `pytest_testnodedown` AT MODULE LEVEL ABORTS ANY RUN WITHOUT XDIST. It is an xdist-owned hookspec, so pluggy validates it at plugin registration and, with xdist unloaded, pytest dies before collection: `INTERNALERROR> pluggy._manager.PluginValidationError: unknown hook 'pytest_testnodedown'`, exit 3, no tests run. The plan's own E-04 requires a `-p no:xdist` case, and `make test-serial` exists, so this would have been hit immediately. `-n 0` does NOT reproduce it (xdist stays loaded), which is precisely why the plan's `-n0` prototype passed and the bug survived authoring. FIX VERIFIED at review: register the hook from `pytest_configure` behind `config.pluginmanager.hasplugin("xdist")`; all four of `-n 2`, `-n 0`, `-p no:xdist`, `-m ""` then behave correctly. | the plan's design run verbatim on a scratch fixture -> exit 3 + INTERNALERROR under `-p no:xdist`, exit 0 + NOTE under `-n 0`; the guarded design -> NOTE present for `-n 2`/`-n 0`/`-p no:xdist` and correctly ABSENT for `-m ""` |
| F-8 | HIGH | the slow set at HEAD `05fa2a7b` | THE SLOW SET HAS FOUR FAILURES, NOT THREE, AND THE FOURTH IS OWNED BY NOBODY. `tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description` fails on eight subparser description gaps (`upgrade-test list/new/sandboxes/probe/env/clean` EMPTY; `config unset` and `conf unset` description shorter than help). `grep` over `.aw/records/backlog/` finds no item for it. It is `slow` only because `tests/test_cli.py` carries a module-level `pytestmark = pytest.mark.slow`. It was introduced the SAME DAY by `64859728` (plan `8ud1is`, executed), making it a live regression that this plan's own CI step is designed to catch, so E-02 must file it rather than let the advisory comment paper over it. | `-m slow` -> `4 failed, 170 passed in 49.12s`; `make test-all` -> `4 failed, 2628 passed, 2 skipped`; the assertion lists the eight gaps; `git log -S "upgrade-test" -- agent_workflows/cli.py` -> `64859728 2026-09-26` |
| F-9 | MEDIUM | `- Scope-Paths:` entry for `3ypquf` | A DECLARED SCOPE PATH DOES NOT EXIST. The plan declares `.aw/records/backlog/open/20260923-3ypquf-...backlog.md`, but `3ypquf` is now `- Status: graduated` (`- Graduated-To: deepclean`, pending plan `baxbdh`) and the file lives under `graduated/`. `ls` of the declared path fails. Left uncorrected, E-02's note would target a missing file and the finalize scope reconciliation would see a declared-but-unmodified path. | `ls .aw/records/backlog/open/20260923-3ypquf-...` -> `No such file or directory`; the item at `graduated/` carries `- Status: graduated` |
| F-10 | INFO | `runner_shared.parse_suite_summary` | THE STOP CONDITION'S PREMISE IS SOUND AND THE NOTE IS SAFE. Verified directly against the shipped reader with the NOTE line both AFTER and BEFORE the count line: it returns the count line in both cases. So the NOTE cannot displace what the runner's merge gate parses, which is what the gate's stop condition guards. | `parse_suite_summary` on a two-line sample -> `'2364 passed in 45.12s'` in both orderings |
| F-11 | INFO | `.aw/system/managed-sections.json` | THE STALE-MANIFEST DECISION IS SAFE. The recorded sha256 for `08-final-ship-review.md` is `54926ba1...` and the actual is `1c35948e...`, confirming the plan's claim, and NOTHING enforces it: no test selects on `managed_sections`/`managed-sections` (`-k` over the whole suite collects 0), and no `check_engine` rule verifies the digest. So E-05 editing the body without refreshing the manifest introduces no new failure. | the two digests computed at review; `python3 -m pytest -o addopts="" -q -k "managed_section or managed-sections"` -> `2634 deselected` (zero selected) |
| F-12 | LOW | `.github/workflows/tests.yml` step "Run self-tests (parallel)" | THE PLAN MIS-QUOTES THE CI COMMAND. The plan's `- Concern:` says the step runs `python -m pytest tests/ -n auto -q`; it actually runs `python -m pytest tests/ -n auto -rs`. The CONCLUSION is unaffected (the step still inherits `addopts` and so still never runs a `slow` test), but E-01 inserts a step directly after this one by name, so an executor matching on the quoted command would not find it. | `grep -n "run: python -m pytest" .github/workflows/tests.yml` -> `77:        run: python -m pytest tests/ -n auto -rs` |

## Proposed changes (ordered, validatable)

1. E-01, E-02: advisory CI slow step and its recorded flip condition.
2. E-03, E-04: deselected-count notice plugin and its outcome test.
3. E-05: release-review full-suite requirement; stale comments.
4. E-06: bare suite and full suite.

## Deferred / out of scope (with reason)

- Flipping the CI slow step to fail-closed (remove `continue-on-error`). It cannot be done now without reddening `main` on the known failures, which are other plans' work; the condition is recorded on the owning items by E-02.
  - Carrier: 57dwkc
- Fixing the slow failures themselves: owned by `57dwkc`, `3ypquf`, `4vfkl1`, plus the item E-02 files for the previously-unowned fourth failure (F-8).
  - Carrier: 3ypquf
- Making the runner's suite gate run the slow set: it would add minutes to every lane merge; this plan only makes the omission visible.
  - Carrier-Declined: deliberate design (fast lane gate); the release-review requirement in E-05 is where the full suite is enforced.
- Fixing the eight subparser description gaps that make the fourth slow failure red.
  - Carrier-Declined: E-02 FILES the owning item for it (a gated bug), which is this plan's obligation and is where the fix belongs; fixing eight `add_parser` descriptions is unrelated to making the slow set visible and would put CLI help text inside a test-visibility plan. The filed item is the durable record, so nothing is lost when this plan executes.

## Scope check

- Over-scope: none. The two comment fixes in E-05 correct claims this plan's own finding F-1 proves false. E-02 filing a backlog item for the unowned fourth failure is NOT over-scope: the plan already undertakes to record the flip condition on "each owning item", and an item that does not exist cannot carry it, so filing it is the minimum that makes E-02's own deliverable true.
- Under-scope: none for the declared concern after review. Note review ADDED the requirement that the failing set be re-derived at execution rather than taken from the authored list (the list was already stale by one failure within hours), and that the `-p no:xdist` case be tested distinctly from `-n 0`.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_deselect_notice.py -v` (outcome test, FOUR cases: `-n 2`, `-n 0`, `-p no:xdist`, `-m ""`).
- Bare `python3 -m pytest` and `make test-all`, with the bar stated as a property (every `FAILED` node id appears in E-02's re-derived owned set), not as a count.
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

- [x] V-01 validates E-01
  - Required evidence: paste the `tests.yml` diff; paste `python3 -c 'import yaml; j=yaml.safe_load(open(".github/workflows/tests.yml"))["jobs"]["unittest"]["steps"]; s=[x for x in j if "slow" in x.get("name","")][0]; print(s["name"], s.get("continue-on-error"), s["run"])'` showing `True` and `-m slow`; paste the local run of the step's exact command's summary line (`python -m pytest tests/ -n auto -m slow`) showing exactly the re-derived known failures from E-02 and no others. ALSO paste the step's inserted position (for example `grep -n -A 4 "Run self-tests (parallel)" .github/workflows/tests.yml`) showing it sits directly after that step, and show the step NAME contains no backlog id6 (the ids belong in the comment; the name is a durable UI label).
  - Observed evidence: verified; tests.yml diff, python yaml query, local slow test run, and step position verified.
    1. tests.yml diff:
    ```diff
    diff --git a/.github/workflows/tests.yml b/.github/workflows/tests.yml
    index 944b1f61..63980b76 100644
    --- a/.github/workflows/tests.yml
    +++ b/.github/workflows/tests.yml
    @@ -76,6 +76,18 @@ jobs:
             # equivalent serial fallback (see `make test-serial`).
             run: python -m pytest tests/ -n auto -rfEs

    +      # Advisory step running slow-marked tests: currently advisory because of known pre-existing
    +      # slow failures tracked by backlog items:
    +      # - 57dwkc & 4vfkl1: installer deep-cleanup leaves .aw/ directory
    +      # - 3ypquf: installer deep-cleanup README classified at-risk
    +      # - g0bdgg: subcommand description gaps in CLI parser
    +      # Flip condition: remove continue-on-error once -m slow reports 0 failed on the ubuntu leg,
    +      # i.e. once every owning item is done.
    +      - name: Run slow-marked tests (ADVISORY until the known slow failures are fixed)
    +        shell: bash
    +        continue-on-error: true
    +        run: python -m pytest tests/ -n auto -m slow
    +
       wheel:
         name: build + import wheel (${{ matrix.os }})
         runs-on: ${{ matrix.os }}
    ```
    2. Python yaml query:
    ```
    $ python3 -c 'import yaml; j=yaml.safe_load(open(".github/workflows/tests.yml"))["jobs"]["unittest"]["steps"]; s=[x for x in j if "slow" in x.get("name","")][0]; print(s["name"], s.get("continue-on-error"), s["run"])'
    Run slow-marked tests (ADVISORY until the known slow failures are fixed) True python -m pytest tests/ -n auto -m slow
    ```
    3. Exact command local run summary line:
    ```
    $ python3 -m pytest tests/ -n auto -m slow
    FAILED tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description
    FAILED tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory
    FAILED tests/test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw
    FAILED tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed
    4 failed, 170 passed in 53.34s
    ```
    4. Step position:
    ```
    $ grep -n -A 4 "Run self-tests (parallel)" .github/workflows/tests.yml
    72:      - name: Run self-tests (parallel)
    73-        shell: bash
    74-        # Process-based parallelism; the suite is xdist-safe (per-process AW_HOME sandbox,
    75-        # per-test tempdirs). `python -m unittest discover -s tests -t .` remains an
    76-        # equivalent serial fallback (see `make test-serial`).
    ```
    Directly followed by step at line 85: `Run slow-marked tests (ADVISORY until the known slow failures are fixed)`. Step name contains no backlog id6.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: FIRST paste the re-derived failing set: the `FAILED` lines and summary of `python3 -m pytest -m slow -o addopts="-q -n auto --dist=worksteal"`. Then paste, for EVERY node id in that set, the owning backlog item id6 and a `grep -n "4petcj"` over its file showing one note line. If any failure had no owning item, paste the `aw backlog new` invocation and its resulting path, and show the new item carries `- Work-Kind: bug` and `- Blocks-Release: next`. The number of noted items must equal the number of distinct owning items for the ACTUAL failing set, not the three the plan was authored against (at review the set was four with one unowned; F-8).
  - Observed evidence: verified; 4 slow failures re-derived, g0bdgg filed, all 4 owning backlog items noted.
    1. Re-derived failing set from `python3 -m pytest -m slow -o addopts="-q -n auto --dist=worksteal"`:
    ```
    =========================== short test summary info ============================
    FAILED tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description
    FAILED tests/test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw
    FAILED tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed
    FAILED tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory
    4 failed, 170 passed in 95.11s (0:01:35)
    ```
    2. Owning backlog item id6 for each failing node id:
    - tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description -> g0bdgg (filed in E-02)
    - tests/test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw -> 57dwkc
    - tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed -> 3ypquf
    - tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory -> 57dwkc (and 4vfkl1)
    3. aw backlog new invocation for unowned failure:
    ```
    $ aw backlog new --summary "SubcommandDescriptionTests fails on eight subparser description gaps" --slug "subcommand-description-gaps" --priority medium --work-kind bug --blocks-release next --apply
    aw backlog new: wrote .aw/records/backlog/open/20260926-g0bdgg-01-g0bdgg-subcommand-description-gaps.backlog.md
    ```
    Metadata confirmation:
    `- Work-Kind: bug`
    `- Blocks-Release: next`
    4. grep -n "4petcj" over every owning backlog item:
    ```
    .aw/records/backlog/open/20260918-57dwkc-01-57dwkc-deep-cleanup-orphans-layout-json.backlog.md:10:- 2026-09-26 note (aw backlog): CI step 'Run slow-marked tests' (tests.yml, plan 4petcj) is advisory because of this item's slow-test failure; when the last of the owning items (57dwkc, 3ypquf, 4vfkl1, g0bdgg) closes, remove its continue-on-error so the slow set fails closed.
    .aw/records/backlog/graduated/20260923-3ypquf-01-3ypquf-deep-cleanup-gitignored-readme-at-risk.backlog.md:11:- 2026-09-26 note (aw backlog): CI step 'Run slow-marked tests' (tests.yml, plan 4petcj) is advisory because of this item's slow-test failure; when the last of the owning items (57dwkc, 3ypquf, 4vfkl1, g0bdgg) closes, remove its continue-on-error so the slow set fails closed.
    .aw/records/backlog/open/20260918-4vfkl1-01-4vfkl1-installer-deep-cleanup-leaves-aw-dir.backlog.md:10:- 2026-09-26 note (aw backlog): CI step 'Run slow-marked tests' (tests.yml, plan 4petcj) is advisory because of this item's slow-test failure; when the last of the owning items (57dwkc, 3ypquf, 4vfkl1, g0bdgg) closes, remove its continue-on-error so the slow set fails closed.
    .aw/records/backlog/open/20260926-g0bdgg-01-g0bdgg-subcommand-description-gaps.backlog.md:10:- 2026-09-26 note (aw backlog): CI step 'Run slow-marked tests' (tests.yml, plan 4petcj) is advisory because of this item's slow-test failure; when the last of the owning items (57dwkc, 3ypquf, 4vfkl1, g0bdgg) closes, remove its continue-on-error so the slow set fails closed.
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the last three lines of a BARE `python3 -m pytest`, showing the `N passed` line AND the `NOTE: <N> tests were deselected` line with N equal to the count from `python3 -m pytest --collect-only -q -o addopts="" -m "slow or livecorpus" | tail -1` (paste that too). Paste `python3 -c` calling `runner_shared.parse_suite_summary` on the captured bare-run output, showing it returns the `N passed` line, not the NOTE line.
  - Observed evidence: verified; bare pytest output has NOTE line with 174 deselected, and parse_suite_summary returns count line.
    1. Last lines of bare `python3 -m pytest`:
    ```
    -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
    NOTE: 174 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    2505 passed, 2 skipped, 3 warnings in 42.98s
    ```
    2. Deselected collection count from `python3 -m pytest --collect-only -q -o addopts="" -m "slow or livecorpus" | tail -1`:
    ```
    174/2681 tests collected (2507 deselected) in 1.28s
    ```
    (174 collected matches N=174 in the NOTE line).
    3. python3 -c calling runner_shared.parse_suite_summary:
    ```
    $ python3 -c 'from agent_workflows import runner_shared; sample = """NOTE: 174 tests were deselected by -m/-k and did not run (the default run skips '\''slow'\'' and '\''livecorpus'\''); run everything with: make test-all\n2505 passed, 2 skipped, 3 warnings in 42.98s"""; print("Parsed summary:", repr(runner_shared.parse_suite_summary(sample)))'
    Parsed summary: '2505 passed, 2 skipped, 3 warnings in 42.98s'
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_deselect_notice.py -v` showing 4 passed; then, IN THE WORKTREE, temporarily make `tests/deselect_notice.py`'s `pytest_terminal_summary` return without writing, paste the `-n 2`, `-n 0` and `-p no:xdist` cases FAILING on the missing NOTE line (not on an import or fixture error), restore, and paste green again. SECOND NEGATIVE CONTROL for PR-001, which is the one that proves the `-p no:xdist` case earns its place: temporarily move `pytest_testnodedown` to MODULE level (the unguarded design), paste the `-p no:xdist` case failing with `INTERNALERROR`/exit 3 while `-n 2` and `-n 0` still pass, then restore and paste green. Without this, nothing shows the new case detects anything the old two did not.
  - Observed evidence: verified; 4 tests pass, negative control 1 fails on missing NOTE, negative control 2 fails on INTERNALERROR, restored green.
    1. 4 passed on test_deselect_notice.py:
    ```
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_with_zero_workers PASSED [ 25%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_with_xdist_workers PASSED [ 50%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_with_no_xdist PASSED [ 75%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_absent_when_nothing_deselected PASSED [100%]
    ============================== 4 passed in 2.78s ===============================
    ```
    2. Negative control 1 (empty terminal summary):
    ```
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_with_no_xdist FAILED [ 25%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_absent_when_nothing_deselected PASSED [ 50%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_with_zero_workers FAILED [ 75%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_with_xdist_workers FAILED [100%]
    AssertionError: 'NOTE: 1 tests were deselected' not found
    ========================= 3 failed, 1 passed in 2.79s ==========================
    ```
    3. Negative control 2 (PR-001 unguarded module-level pytest_testnodedown):
    ```
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_with_zero_workers PASSED [ 25%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_absent_when_nothing_deselected PASSED [ 50%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_with_xdist_workers PASSED [ 75%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_with_no_xdist FAILED [100%]
    AssertionError: 'INTERNALERROR' unexpectedly found in 'INTERNALERROR> pluggy._manager.PluginValidationError: unknown hook \'pytest_testnodedown\' in plugin <module \'tests.deselect_notice\' from \'tests/deselect_notice.py\'>\n\nno tests ran in 0.01s\n'
    ========================= 1 failed, 3 passed in 2.87s ==========================
    ```
    4. Restored and green:
    ```
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_absent_when_nothing_deselected PASSED [ 25%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_with_zero_workers PASSED [ 50%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_with_no_xdist PASSED [ 75%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_with_xdist_workers PASSED [100%]
    ============================== 4 passed in 2.59s ===============================
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the diff of `08-final-ship-review.md`, `pyproject.toml` and `Makefile`; paste `grep -n "test-all" .aw/system/workflows/release-review/08-final-ship-review.md` showing the new requirement.
  - Observed evidence: verified; 08-final-ship-review.md diff and grep show full suite requirement; pyproject.toml and Makefile comments updated.
    1. Diff of 08-final-ship-review.md, pyproject.toml, and Makefile:
    ```diff
    diff --git a/.aw/system/workflows/release-review/08-final-ship-review.md b/.aw/system/workflows/release-review/08-final-ship-review.md
    index dd5632f4..caae986f 100644
    --- a/.aw/system/workflows/release-review/08-final-ship-review.md
    +++ b/.aw/system/workflows/release-review/08-final-ship-review.md
    @@ -86,6 +86,8 @@ If a new material issue is found, update the finding and action registers and de

     Run the most appropriate repository-native validation commands available and safe. Record all results in `10-validation-results.md`. If validation cannot be run, explain why and assess release risk.

    +**Full test suite required for release evidence.** The test evidence backing the GO recommendation MUST come from the repository's FULL test target, running every test including every marker or category that routine/default runs deselect (in this toolkit that is `make test-all`, i.e. `python3 -m pytest tests/ -m ''`). A default test run that deselects test subsets or prints a notice of deselected tests is a fast subset for routine development and is NOT valid release evidence. Every failure in the full test run must either be fixed before release or explicitly listed as a tracked release blocker with its backlog item ID.
    +
     Use the `verify` workflow (`verify/tools/run_checks.py`) to run the repo's own checks and produce machine-checkable evidence (`.aw/workflow-artifacts/verify/<RUN_ID>/verify-results.json`): actual commands, exit codes, metrics, and logs. `10-validation-results.md` should CITE that evidence rather than assert results from reading the code.

     **Evidence gate on the recommendation.** The GO / CONDITIONAL GO / NO-GO recommendation must be backed by this evidence. If a relevant test/lint/build/type-check could not be verified (no runnable setup, needs services/credentials, or blocked by the safety denylist), the recommendation may not be a clean GO: downgrade to CONDITIONAL GO with the unverified checks listed as explicit prerequisites, and state plainly which claims are unverified. Never issue a GO whose basis is the agent's self-report where deterministic evidence was available but not produced. "Could not verify" must appear as prominently as "verified".
    diff --git a/Makefile b/Makefile
    index fe63ca0a..4464f647 100644
    --- a/Makefile
    +++ b/Makefile
    @@ -24,8 +24,9 @@ install-dev:
     test:
     	python3 -m pytest tests/

    -# FULL suite including the `slow` subprocess/integration tests. Use for release-review,
    -# CI, or before shipping. `-m ""` clears the default `not slow` filter; still parallel.
    +# FULL suite including the `slow` subprocess/integration tests (CI runs the fast
    +# suite plus an advisory slow step). Use for release-review or before shipping.
    +# `-m ""` clears the default `not slow` filter; still parallel.
     test-all:
     	python3 -m pytest tests/ -m ''

    diff --git a/pyproject.toml b/pyproject.toml
    index 3dbc310e..17056c5a 100644
    --- a/pyproject.toml
    +++ b/pyproject.toml
    @@ -163,8 +163,9 @@ markers = [
     #     `--dist=worksteal` lets idle workers steal queued tests so one straggler cannot
     #     stall the whole run.
     #  2) `-m "not slow"` so the DEFAULT run is the FAST subset (pure-logic unit tests, ~24s).
    -#     The ~9 subprocess-heavy files are marked `slow` and excluded here; run the FULL
    -#     suite for release-review / CI with `make test-all` (which passes `-m ""`).
    +#     The ~9 subprocess-heavy files are marked `slow` and excluded here; CI runs the
    +#     fast suite plus an advisory slow step; run the FULL suite for release-review
    +#     with `make test-all` (which passes `-m ""`).
     # To force serial when debugging a test-isolation issue: `make test-serial`
     # (`python -m unittest discover -s tests -t .`).
     addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"
    ```
    2. grep -n "test-all" in 08-final-ship-review.md:
    ```
    89:**Full test suite required for release evidence.** The test evidence backing the GO recommendation MUST come from the repository's FULL test target, running every test including every marker or category that routine/default runs deselect (in this toolkit that is `make test-all`, i.e. `python3 -m pytest tests/ -m ''`). A default test run that deselects test subsets or prints a notice of deselected tests is a fast subset for routine development and is NOT valid release evidence. Every failure in the full test run must either be fixed before release or explicitly listed as a tracked release blocker with its backlog item ID.
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the final summary lines of a BARE `python3 -m pytest` (0 failed, NOTE line present) and of `make test-all`, naming every failure in the latter by node id and showing each one appears in E-02's re-derived, now-owned set. Compare against the review baseline on HEAD `05fa2a7b` (bare `2458 passed, 2 skipped`; `make test-all` `4 failed, 2628 passed, 2 skipped`) and account for any difference. A failure NOT in the owned set is a NEW regression: name it and stop rather than widening the set silently.
  - Observed evidence: verified; bare pytest green with NOTE line; make test-all matches exactly the 4 re-derived owned failures.
    1. Bare `python3 -m pytest` summary lines:
    ```
    NOTE: 174 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    2505 passed, 2 skipped, 3 warnings in 42.98s
    ```
    0 failed, NOTE line present.
    2. `make test-all` summary and failures:
    ```
    =========================== short test summary info ============================
    FAILED tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed
    FAILED tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory
    FAILED tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description
    FAILED tests/test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw
    4 failed, 2675 passed, 2 skipped, 3 warnings in 83.18s (0:01:23)
    ```
    Every failure node ID appears in E-02's re-derived, owned set:
    - tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed -> 3ypquf
    - tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory -> 57dwkc & 4vfkl1
    - tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description -> g0bdgg
    - tests/test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw -> 57dwkc
    No new failures. Compared to review baseline on HEAD 05fa2a7b (bare 2458 passed, 2 skipped; make test-all 4 failed, 2628 passed, 2 skipped), test counts increased due to test suite growth across the repository and the 4 new test cases added in this plan in tests/test_deselect_notice.py (bare: 2505 passed vs 2458; full: 2675 passed vs 2628).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. CI gains one advisory step that runs the slow set (174 tests at review-time HEAD) on every matrix leg, taking roughly one extra minute per leg and NOT failing the job; the default pytest run gains one NOTE line naming how many tests it skipped; the release-review body requires the full suite as release evidence; two comments that falsely claim CI runs the full suite are corrected; and every backlog item owning a slow failure gets a history note recording the flip condition. No production code changes.

ONE THING REVIEW ADDED THAT YOU ARE ALSO APPROVING: the slow set has FOUR failures, not the three the plan was authored against, and the fourth (`tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description`, eight missing or too-short subparser descriptions, six of them on `upgrade-test`) is owned by NO backlog item and was introduced the same day by an already-executed plan. So E-02 now FILES a gated bug item for it before recording the flip condition. That is a new tracked item, and it is the plan's own concern proving itself: a regression landed in `main` today and only the deselected slow set could see it.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above. NOTE the `3ypquf` entry was corrected from `open/` to `graduated/` (the item moved; the declared path did not exist). E-02 may also create ONE new backlog item file, which is an addition the fence cannot name in advance because its id6 is minted at execution; record it with `--scope-reason` at finalize. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. RE-DERIVE the failing slow set rather than copying the authored list: it was already stale by one failure within hours of authoring, and an executor who trusts the list will file no item for the unowned failure and will report "exactly the three known failures" about a run that showed four.

GENUINE STOP CONDITIONS:
1. If the NOTE line changes what `runner_shared.parse_suite_summary` returns for a bare run, stop and report, because the runner's merge gate parses that line. (Verified SAFE at review: with the NOTE line both before and after the count line, the shipped reader still returns the count line, F-10. So this is a re-check, not an expected blocker.)
2. If a `-p no:xdist` run of the suite aborts with `INTERNALERROR ... unknown hook 'pytest_testnodedown'`, the plugin registered its xdist hook unconditionally; fix it per E-03's capability probe rather than deleting the `-p no:xdist` test case to make the suite green.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane). Then set backlog item `xuc9v0` `done` with `--evidence` citing the executed plan; this plan carries its `- Blocks-Release: next`.
