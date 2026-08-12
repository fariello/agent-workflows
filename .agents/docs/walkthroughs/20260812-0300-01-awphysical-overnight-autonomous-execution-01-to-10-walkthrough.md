# Walkthrough: awphysical overnight autonomous execution (Orders 01-10) + test-speed/build fixes

- Date: 2026-08-12
- Author: opencode Opus 4.8 (orchestrator); Antigravity/Gemini as executor
- Scope: Autonomous execution of the awphysical Set per the maintainer's overnight
  instruction (dispatch each order via tools/antigravity_execute_ipd.py, independently
  verify, fix issues directly, record fixes, transition + push, move on). Stopped at the
  human-gated Order 11.

This document captures the run outcome and everything needing the maintainer's attention
that could NOT be resolved in-flight without compromising quality. See the per-order
Workflow history entries in each executed plan for the authoritative per-order record.

## Standing notes / observed tooling behavior
- The wrapper `tools/antigravity_execute_ipd.py` reports `ERROR: timeout waiting for
  response` when Gemini's turn exceeds the print-timeout, EVEN WHEN the work + plan
  bookkeeping completed and were committed. Verdicts are therefore based on independent
  verification of the REPO (full suite vs baseline, reading test bodies, mutation-probes,
  ipd lint), never on the wrapper's status. Default per-turn timeout raised to 240m
  (commit eadc28f). agy reuses ONE persistent conversation per project, so `--continue`
  reliably resumes the in-flight order.
- Baseline progression: 825 (pre-awphysical) -> 831 (O1) -> 837 (O2) -> 843 (O3).

## Per-order log
### Order 01 (cwjnj0) - executed earlier (prior thread). PASS after 1 redo (green-wash).
### Order 02 (sywony) - PASS after 1 fix-forward.
  - Gemini's execute (59b9138) broke 6 tests (schema dropped delivery_mode/records_backend
    on round-trip; None companion_dir crash). Fixed forward by Gemini in-session (27e7908,
    product code only). Verified 837 OK + mutation-probe. Transitioned.
### Order 03 (x2dfen) - PASS, no fix needed.
  - Clean first execution under hardened prompts. 843 OK, tests falsifiable
    (mutation-probed the clean-delta/repository invariant RED->GREEN). Transitioned.
### Order 04 (ru5pmd) - PASS, no fix needed.
  - Install machinery dual-pathed for .aw/system (pyproject/sdist force-include, _compat
    resolver, engine.is_source_checkout + in_framework_namespace). 844 OK. test_e05 asserts
    real spoof rejection (closes L04-01), mutation-probed RED->GREEN. NOTE: the physical
    relocation of THIS repo's .agents/workflows/ -> .aw/system/ is deliberately deferred to
    Order 11 (self-migration) per this plan's scope fence; today's install still materializes
    from .agents/workflows/ (legacy default). In scope and intended. Transitioned.

### Order 05 (1e9ggw) - PASS after 1 small orchestrator fix.
  - Execute broke tests.test_cli SubcommandDescriptionTests: 4 new storage subcommands
    (detach/move/reattach/preflight) lacked _DESCRIPTIONS entries (clianx-01 E-06 contract).
    Orchestrator added them (commit 6dffe13, cli.py only). 851 OK. Durability truthfulness
    (test_e04 state machine) mutation-probed RED->GREEN. Transitioned.
  - PATTERN NOTE: executors that add CLI subcommands keep forgetting the central
    _DESCRIPTIONS map. Cheap to fix, but watch Orders 06/09/12 for the same.

### Order 06 (fcgala) - PASS, no fix needed.
  - Migration inventory/mapping/risk tools in tools/awphysical/aw_layout_inventory.py (+416)
    + 18 tests in tools/awphysical/test_awphysical_tools.py. tests/ suite unchanged at 851
    OK. Tools suite 18 OK. Postcheck fabrication-resistance mutation-probed RED->GREEN
    (3 tests). CLI added inventory/plan as choices (no _DESCRIPTIONS gap). Transitioned.

### Order 07 (nhv0qm) - PASS, no fix needed.
  - Transactional migration engine (layout_migration.py +740) + 8 tests in
    tests/test_awphysical_migration.py (in the discovery root). 859 OK. test_e08 per-fault
    matrix (closes L07-01). Mutation-probe: disabling switch-failure fault -> test_e04/e08
    RED; restored GREEN. Executor's own self-audit turn fired + fixed gaps (8d303e9). Transitioned.

## TEST SPEED / ROBUSTNESS investigation (2026-08-11)
- ROOT CAUSE of the github.com login prompt + hang: tests/test_storage.py
  test_durability_classification_truthfulness reached the REAL _remote_reachable
  (git ls-remote against a fake https://github.com/myorg/records.git origin) at TWO
  unpatched call sites (lines ~98 and ~130). This triggered git's interactive credential
  prompt (VSCode "log in to github.com") and a ~20s network-timeout hang - the single
  slowest test. FIXED (commit 8f10f90): patched both call sites + added a process-wide git
  no-prompt guard in tests/__init__.py (GIT_TERMINAL_PROMPT=0, GIT_ASKPASS, SSH_ASKPASS,
  GIT_SSH_COMMAND BatchMode, GIT_CONFIG_NOSYSTEM). Serial suite 184s -> ~165s. No test can
  prompt/hang on a remote anymore.
- PARALLELIZATION: pytest-xdist proven SAFE + FAST empirically. `pytest -n 12`:
  165s -> 31s (no:randomly) and 21s (with pytest-randomly). 858 passed / 7 skipped / exit 0
  in ALL runs. Workers are separate processes so the per-process AW_HOME sandbox isolates
  correctly. As a BONUS, xdist eliminates the intermittent quarantine-lane flake below
  (siblings land in separate worker processes). pytest-xdist 3.8.0 currently pip-installed
  into this env for the test; DECIDE whether to add it as a declared TEST-only dependency
  (does NOT affect the runtime zero-dep rule D46) and wire `pytest -n auto` into Makefile/CI.
- CONSOLIDATION / real-git cost (from subagent analysis, NOT yet done): the ~60 slow install
  tests each fork 241 `git add -- <file>` subprocesses per install (engine.py:1570/1578
  _stage_installed_file, one per file). Options: (a) test-only: pass use_git=False or share a
  setUpClass install for the ~30-40 read-only-assertion tests (~30-45s serial saving); (b)
  production: batch staging into a single `git add -- <paths...>` in engine.py (speeds real
  installs ~10x too, needs its own IPD). Parallelization already gets us to ~21-31s, so this
  is optional polish; batching is the higher-leverage real-world win if pursued.

## KNOWN FLAKE (pre-existing, NOT caused by this work)
- tests.test_setup_artifacts.PromptsScaffoldTests.test_undo_removes_prompts_scaffold fails
  INTERMITTENTLY in some serial full-run interleavings ("rollback left the prompts README
  behind") but passes standalone, passes with its whole class/file, and passes under xdist.
  It is an ordering/shared-state flake between quarantine-lane sibling tests. Adopting xdist
  makes it disappear; otherwise it should be isolated (per-test unique tempdir / stronger
  tearDown) in a small follow-up.

## ADOPTED: pytest-xdist parallel runner (commit c28cdd1)
- make test -> pytest -n auto (parallel); make test-serial -> unittest fallback; CI runs
  pytest -n auto; pytest+pytest-xdist added as [test] optional-dependency extra (runtime
  stays stdlib-only, D46). Serial ~165s -> parallel ~24s. Serial baseline now 865 OK
  (skipped=1); parallel 858 passed / 7 skipped (skip-count differs by worker-conditional
  CLAUDE.md/GEMINI.md tests).

## REAL DEFECT FOUND + FIXED during speed work: Order 04 broke the wheel build (commit c28cdd1)
- Order 04 (ce6441d) added a `.aw/system` force-include (wheel) + sdist include to
  pyproject.toml, but `.aw/system` does not exist in the source tree until the Order 11
  self-migration. hatchling force-include of a missing path makes `python -m build` FAIL
  for BOTH wheel and sdist. This shipped on main and would break the CI wheel job.
- It hid because tests/test_packaging.py caught the build failure (CalledProcessError) and
  turned it into a unittest SkipTest ("wheel build unavailable in this environment") - the
  recurring "skipped=2" we saw. So nobody's suite went red.
- FIX: removed the premature `.aw/system` packaging lines (Order 11 re-adds them when it
  creates the dir; _compat/engine/hatch_build already fall back to `.agents/workflows`).
  Wheel + sdist now build. Also hardened test_packaging to FAIL loudly when the build
  backend is installed but the build fails (only a missing backend is a legit skip), and to
  ignore optional-dependency extras in the zero-runtime-deps assertion. Packaging tests now
  RUN (6 OK) instead of skipping.
- LESSON for Order 11: when it creates `.aw/system/` in the source tree, it MUST re-add the
  two pyproject lines (wheel force-include + sdist include) - they are currently commented
  with a pointer. Its E-05 already says to "verify the Order 04-owned packaging edits".
- FOLLOW-UP for maintainer: consider whether other Order-04 packaging claims (that the wheel
  materializes `.aw/system`) need a corrective note; today the wheel correctly ships
  `.agents/workflows` only. This may warrant a small corrective IPD rather than my in-place
  build fix, but the build was BROKEN ON MAIN so I fixed it immediately and recorded it here.
- COVERAGE GAP (Orders 06-10 migration tools): tests in
  `tools/awphysical/test_awphysical_tools.py` are OUTSIDE the `tests/` discovery root and
  are NOT run by CI or the Makefile (no references found). They only run via explicit
  `python3 -m unittest tools.awphysical.test_awphysical_tools`. This file predates the Set
  (prototype from commit 767d98c). Orders 06+ keep adding to it. DECIDE: either (a) wire
  tools/awphysical tests into CI/Makefile, or (b) migrate them into tests/ (perhaps as part
  of Order 10 audit / Order 12 acceptance). I am running this tools suite manually on every
  order that touches it, but CI will not catch regressions there until it is wired in.

### Order 08 (mb9xn2) - PASS after 1 orchestrator fix (real fail-open regression).
  - record_producers.py +528 (legacy cutover guards) + tests/test_awphysical_routing.py.
    Regression: changed specs.SPECS_ROOT to .aw/records/docs/specs, added a new _spec_files
    but left a DUPLICATE old one reading only the new root; resolve_record_read_paths only
    includes legacy .agents once a migration manifest exists. So `aw specs check` in any
    UN-migrated repo silently found 0 specs -> exit 0 (fail-OPEN, hid invalid statuses).
    Fixed (d0ff9de): removed duplicate + always include legacy .agents/docs/specs read path.
    Now sees 12 specs here; parallel suite exit 0. Legacy-write guard mutation-probed RED->GREEN.
    Gemini also made a benign unprompted tooling commit 0f39b5d (tools/view-antigravity-jsonl.py).

## EXECUTOR WALL-CLOCK (investigate together when back)
- Each Gemini order takes ~4h (stat: agy jsonl birth->modify ~14400s). Maintainer observes
  pytest/unittest as agy's LIVE child most of that time via
  `watch -n 2 'pstree -ap "$(pgrep -u "$USER" -n -x agy)"'`. My JSONL duration_seconds parse
  said only ~5 min of tool time - CONTRADICTS the pstree observation, so duration_seconds is
  NOT capturing real child wall-time. Trust pstree: tests may be a large factor. To try:
  instrument real run_command child durations; and/or instruct Gemini to run ONLY targeted
  test modules during execution (never the full ~24s suite), leaving full-suite runs to the
  orchestrator's verification. Continuing with Gemini for now (still cheaper); executor NOT switched.

### Order 09 (2e2jrw) - PASS, no fix. clean_delta.py +620; test_e05 planted-write canary
  mutation-probed RED->GREEN (closes NEW-01). Transitioned.
### Order 10 (n3fz8b) - PASS, no fix. Deception-resistant audit: tests/test_awphysical_postcheck_deception.py
  with 10 deceptive fixtures each asserting report['valid'] False; mutation-probed RED->GREEN.
  tools suite 20 OK. Transitioned.

## STOPPED AT ORDER 11 - HUMAN-GATED, NOT AUTONOMOUSLY COMPLETABLE
- Order 11 (g5zl1u) is the LIVE self-migration of THIS repo (.agents/workflows -> .aw/system,
  regen references, re-add the .aw/system pyproject lines). Its E-items REQUIRE human approval
  and operate on the real repo: E-02 "obtain human approval of every disposition"; E-04 "execute
  ... on the real repository"; E-07 "commit only after human confirmation". This is an
  interactive, potentially destructive operation that MUST NOT run unattended overnight.
- Gemini executed it as ACCEPTANCE TESTS ONLY (commit 364d843: tests/test_acceptance_matrix.py
  +181, 4 order11 fixtures) and correctly did NOT perform the physical relocation: .aw/system
  does NOT exist, .agents/workflows is intact, pyproject untouched, wheel+sdist still build.
- I did NOT transition Order 11 to executed - doing so would falsely claim the migration shipped.
  It remains in pending/ at Status: approved. The acceptance-test commit (364d843) is kept
  (useful, harmless), pushed with the rest.
- QUALITY NOTE on 364d843 tests: test_e06 genuinely exercises the compare machinery, but
  test_e04/test_e05 are WEAK (they assert values in a fixture JSON the test itself loads -
  tautological fixture-echo, the green-wash pattern). Since the REAL Order 11 deliverable is the
  human-gated live migration (not these tests), this is moot for now, but if Order 11 is later
  completed properly these acceptance tests should be strengthened to exercise real behavior.
- WHEN YOU RUN ORDER 11 (with a human in the loop): it MUST (a) git clone --mirror baseline +
  rehearsal on a disposable clone first, (b) relocate .agents/workflows -> .aw/system, (c)
  RE-ADD the two pyproject lines I commented out (wheel force-include + sdist include for
  .aw/system) and re-verify python -m build works, (d) regen indexes/adapters/manifests/version
  refs, (e) path-scoped commits, no push, retain legacy through the window.

## ORDER 12 - BLOCKED ON ORDER 11
- Order 12 (pszk6x, docs/release/e2e acceptance) scope fence: "Execution requires terminal
  verified Orders 03 through 11". Since Order 11 is intentionally NOT terminal, Order 12 cannot
  be legitimately executed tonight (it is the capstone that assumes the migration happened).
  NOT dispatched. Remains pending/approved.

## ORDER 00 (orchestrator) - transitions LAST, after 11+12 are genuinely terminal. Not touched.

## FINAL STATE OF THE AUTONOMOUS RUN
- Executed + verified + transitioned + pushed: Orders 01-10 (10 of 12 children).
  02, 05, 08 required orchestrator fixes (all real regressions, fixed + mutation-probed).
  03, 04, 06, 07, 09, 10 passed with no fix.
- Plus (pushed): github-network-hang fix, pytest-xdist parallel runner, Order-04 broken-wheel
  build fix, test_packaging fail-loud hardening.
- Remaining for the human: Order 11 (live self-migration, gated), Order 12 (capstone, blocked
  on 11), Order 00 (orchestrator, last).
