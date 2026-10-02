# IPD: Restore the packaging boundary coverage the wheel guard does not reach: sdist, console scripts, and the browser assets

- Date: 2026-10-02
- Kind: child
- Concern: THE BACKLOG ITEM'S PACKAGING MEASUREMENT IS NOW PARTLY STALE, AND THE REAL GAP IS NARROWER AND SHARPER THAN IT STATES. The item (measured at HEAD `4e6cae095`) says `tests/test_packaging.py` was deleted by `19313eed` and that no test builds a wheel and asserts its contents. THAT IS NO LONGER TRUE: commit `2edb9ff8e` ("Restore a behavioral wheel ship-vs-dev packaging guard...", plan `iocyf3`) restored a 183-line `tests/test_packaging.py` that DOES build the wheel and assert on its entries. SO I RE-MEASURED THE SURFACE RATHER THAN RESTORING WHAT ALREADY EXISTS, and what the restored guard does NOT reach is a closed, checkable list. The guard covers two properties, the ship-versus-dev boundary and the runtime-dependency allowlist, and it NEVER BUILDS AN SDIST AT ALL: `rg -ln 'build.*--sdist|tarfile' tests/` matches only `tests/test_installer.py`, and there for an installer backup archive, not a distribution. The sdist is a DIFFERENT mechanism from the wheel, an EXPLICIT ALLOWLIST in `[tool.hatch.build.targets.sdist].include`, so anything outside `/agent_workflows` is absent from the sdist even when the wheel carries it, and nothing checks that. Nothing asserts the three console scripts either (`rg -ln entry_points.txt tests/` returns nothing), so a wheel that installs with no `aw` command on PATH passes the suite. AND THE BROWSER ASSETS HAVE NO PRESENCE ASSERTION IN EITHER ARTIFACT (`rg -ln run_analytics_assets tests/` returns nothing), which is the one that matters most because the failure mode is SILENT: I reproduced it at authoring, hatchling honors `.gitignore` and omitted a matching asset from a probe wheel at exit 0 with no warning on stderr.
- Scope: Add the packaging properties the restored wheel guard does not reach, as one new test file that builds the SDIST and asserts the distribution-contents properties neither artifact currently has a caller for: the sdist allowlist carries the package, the data tree and the browser assets; the wheel registers its three console scripts; and the browser assets are present AND non-empty in both artifacts, with the declared asset list kept honest against `run_analytics_spa.REQUIRED_ASSETS` rather than hand-maintained. Out of scope: the two properties `tests/test_packaging.py` already covers (the ship-versus-dev boundary and the runtime-dependency allowlist), which are NOT re-asserted anywhere here; the deleted `tests/test_run_analytics_packaging.py` performance-baseline arms, which are benchmarks and not packaging (carrier below); the `.gitignore`-injected-into-sdist nit `pyproject.toml` already documents as accepted; and the security-hardening half of the item, which is Order 01 of this Set.
- Scope-Paths: tests/test_packaging_distribution.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: security
- Priority: high
- From-Backlog: mflqqf
- Set: mflqqf
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: d0lg63

## Workflow history

- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `mflqqf` in a non-interactive authoring turn. The item's packaging measurement was re-checked at HEAD `4fbbc8386` and found PARTLY STALE (F-01), so the plan's subject narrowed from "restore the deleted packaging suite" to "add only the properties the already-restored guard does not reach", and the authoring turn measured which those are rather than inferring them (F-03 through F-06).
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Close the packaging-boundary gaps that remain AFTER the `iocyf3` restoration, so a silently dropped browser asset, a missing console script, or an sdist that omits what the wheel carries is reported by the suite instead of shipping. Add no duplicate of a property already covered.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the asset presence assertions and their honesty guard

- [ ] E-01 Create `tests/test_packaging_distribution.py` with the wheel-building fixture and the POSITIVE, PER-ASSET presence assertions for the browser assets, recovered from `git show 19313eed^:tests/test_packaging.py` (the `REQUIRED_BROWSER_ASSETS` arms) and re-verified against the current build. ASSERT PRESENCE BY NAME AND NON-EMPTINESS SEPARATELY, because a zero-byte asset ships as happily as a real one and renders exactly as badly: at authoring the wheel carries `agent_workflows/run_analytics_assets/app.css` at 5235 bytes and `app.js` at 21944 bytes, so both arms pass today. REUSE THE EXISTING FIXTURE SHAPE FROM `tests/test_packaging.py` RATHER THAN INVENTING ONE, which is the detail that decides whether this file is maintainable: that file's `setUpClass` SKIPS when `import build` fails (a genuine environment limit) but raises `AssertionError` when `build` IS importable and the build FAILS, so a real packaging defect is never hidden behind a skip. Copy that discrimination exactly; it is the behavior that makes a packaging test trustworthy in CI.
  - Depends on: none
  - Expected outcome: The file exists and passes. `python3 -m pytest tests/test_packaging_distribution.py -o addopts="" -q` reports every collected test passing, and `rg -c run_analytics_assets tests/test_packaging_distribution.py` is non-zero where `rg -l run_analytics_assets tests/` returned nothing before.
  - Execution state: pending

- [ ] E-02 Add the HONESTY GUARD for the asset list: assert the file's `REQUIRED_BROWSER_ASSETS` equals the set derived from `run_analytics_spa.ASSETS_DIRNAME` and `run_analytics_spa.REQUIRED_ASSETS`, so adding an asset to the module without adding it here FAILS instead of silently reducing coverage. This is the item that stops a hand-maintained list rotting, which is the standing failure mode of every by-name presence assertion. Derive the expected names by importing the module and composing `f"agent_workflows/{ASSETS_DIRNAME}/{name}"`; do NOT hard-code a count. At authoring `ASSETS_DIRNAME` is `run_analytics_assets` and `REQUIRED_ASSETS` is `('app.css', 'app.js')`, so the guard holds with two entries, but the assertion must be over the derived SET and not the number two.
  - Depends on: E-01
  - Expected outcome: The guard passes against the current module. Adding a third name to `REQUIRED_ASSETS` without updating the test file would fail this arm, and the arm's failure message names the difference rather than only reporting inequality.
  - Execution state: pending

- [ ] E-03 Add the MEASURED-HAZARD arm, restored from the deleted `test_a_gitignored_asset_would_be_DETECTED_rather_than_silently_dropped`, which builds a throwaway probe package whose asset directory contains a gitignored file and demonstrates that the wheel omits it at exit 0. THIS ARM EXISTS TO KEEP E-01'S RATIONALE HONEST RATHER THAN TO TEST OUR OWN PACKAGE: everything else about an asset can be asserted by absence-checking, and the reason a POSITIVE per-asset assertion is needed at all is that the drop is silent, so the defense should rest on a reproduced measurement rather than on a review note. I REPRODUCED THE BEHAVIOR AT AUTHORING against hatchling 1.32.4 (`exit 0`, `kept.css` present, `ignored.css` absent, no warning on stderr), so the arm is known to hold here. Build the probe under `tempfile`, skip if the probe build itself is unavailable, and make the failure message say that hatchling no longer honors `.gitignore` and that E-01's assertion is still correct but its stated rationale needs updating, so a future hatchling change produces a comprehensible instruction rather than a bare red test.
  - Depends on: E-02
  - Expected outcome: The arm passes, printing the measured probe outcome. If hatchling ever stops honoring `.gitignore`, the arm fails with a message that tells the reader to update the rationale rather than to delete the assertion.
  - Execution state: pending

### Task group 2: the sdist, which nothing builds today

- [ ] E-04 Add a separate SDIST test class, restored from the deleted `SdistBrowserAssetTests` and widened, because `[tool.hatch.build.targets.sdist].include` is an EXPLICIT ALLOWLIST (`/agent_workflows`, `/.aw/system`, `/hatch_build.py`, `/pyproject.toml`, `/README.md`, `/LICENSE`, `/NOTICE`) and is a different mechanism from the wheel's `packages` plus `force-include`, so asserting only the wheel leaves this half unchecked and nothing in the tree builds an sdist at all (F-03). A SEPARATE CLASS IS REQUIRED, not a preference: it needs its own build, and the wheel fixture cannot supply it. Assert the sdist carries the browser assets BY NAME, the analytics modules that read them (`run_analytics_spa.py`, `run_analytics_report.py`), and the bundled data tree the build itself depends on (`/.aw/system`), normalizing member names by stripping the leading `<name>-<version>/` component so they compare in the same form as the wheel's. I verified all of these are present at authoring and that the sdist builds in about 4 seconds, so this class is cheap.
  - Depends on: none
  - Expected outcome: The sdist class passes. `rg -c 'sdist' tests/test_packaging_distribution.py` is non-zero where no test in the tree built an sdist before.
  - Execution state: pending

### Task group 3: the console scripts, and proving the tree still holds

- [ ] E-05 Add the CONSOLE SCRIPT arm, restored from the deleted `test_wheel_registers_three_console_scripts`: read `entry_points.txt` from the wheel's `dist-info` and assert all three scripts (`aw`, `agent-workflows`, `agentwf`) are registered and each points at `agent_workflows.cli:main`. ASSERT THE TARGET AND NOT ONLY THE NAME, which is a strengthening over the deleted version: that one checked each name appeared somewhere in the file and that the string `agent_workflows.cli:main` appeared, which would pass if two scripts pointed at the right target and the third pointed anywhere. Parse the file with `configparser` (it is INI) and assert the mapping, so a script registered against a missing entry point fails. Then run the full suite BARE as `python3 -m pytest` with no added flags, measuring the collected total against a baseline taken AT THE EXECUTION BASE. THE BASE IS NOT GREEN AND YOU MUST NOT ACCEPT THAT ON THIS PLAN'S WORD (F-08): at authoring the bare suite was `5 failed, 4622 passed, 2 skipped in 410.45s`, three of the five filed and two load-sensitive. Re-measure, and re-run every red node ALONE before classifying it.
  - Depends on: E-04
  - Expected outcome: All three scripts are asserted to map to `agent_workflows.cli:main` (verified present at authoring), and the bare suite shows no newly failing test against the executor's own base baseline, with the collected total rising by exactly the number of tests this plan adds.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE. `AGENTS.md` forbids reading production source with `inspect`, `ast`, regex or substring search and forbids symbol censuses as a proxy for correctness (GUIDING_PRINCIPLES P16). Every item above BUILDS A DISTRIBUTION and asserts on its real contents, which is behavioral in the strongest available sense: the artifact a user installs. E-02 imports `run_analytics_spa` and reads two module CONSTANTS, which is a data comparison against a declared contract rather than a structural assertion about code.
- THE `rg -c` COUNTS IN THE EXPECTED OUTCOMES ARE REACHABILITY CHECKS ON THE NEW FILE, NOT ASSERTIONS INSIDE IT. They belong in the V-item evidence; no committed test may assert a count over the tree.
- DELIBERATELY NOT MARKED `slow`, and the existing file records the reasoning this plan follows. `tests/test_packaging.py`'s module docstring states that because `addopts` deselects `slow` and CI's slow step carries `continue-on-error: true`, marking a packaging guard `slow` would leave the boundary with NO blocking gate in routine runs, lane integration, or CI. The same logic applies here, and the budget fits: I measured the wheel build at 6.5s and the sdist at 4.2s against `conftest.py`'s 90.0s `_DEFAULT_TEST_TIMEOUT`. Two builds in one file is the cost to weigh at review.
- A SEPARATE FILE, NOT AN EXTENSION OF `tests/test_packaging.py`. The existing file is a focused ship-versus-dev guard with a single wheel fixture and a docstring arguing its own non-`slow` status; adding an sdist build and a probe build to it would double its cost and blur that argument. The repository convention is narrowly named per-property files, and keeping them separate also keeps this plan's `- Scope-Paths:` to one path, so it cannot collide with a sibling that touches the existing guard.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, so E-05 uses `python3 -m pytest` with no added flags; `-o addopts=""` appears above ONLY for the narrowed per-file runs where per-test counts are needed.
- A COUNT OVER THE LIVE TREE IS RE-DERIVED, NOT MATCHED. Every count comparison here is SELF-RELATIVE: measure before, measure after, require the delta to equal the tests added.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE BACKLOG ITEM'S PACKAGING MEASUREMENT IS STALE AND THIS PLAN DOES NOT RESTORE WHAT EXISTS. The item says `tests/test_packaging.py` was deleted and that no test builds a wheel and asserts its contents. The file is BACK, 183 lines, restored by `2edb9ff8e` (plan `iocyf3`), and it does build the wheel. Its two properties are the ship-versus-dev boundary and the runtime-dependency allowlist. | `git log --oneline -3 -- tests/test_packaging.py` shows `2edb9ff8e` above `19313eed7`; the file's two test methods are `test_wheel_ship_vs_dev_boundary` and `test_wheel_declares_only_the_allowlisted_runtime_dependency`. |
| F-02 | The item's other packaging claim, that zero test files match `force-include` or `hatch.build`, still holds for test CODE. The only match in `tests/` is a JSON fixture, not a test. | `rg -l 'force-include\|force_include\|hatch\.build' tests/` matches only `tests/fixtures/awphysical/order04/e02-packaging.json`. |
| F-03 | NOTHING IN THE TREE BUILDS AN SDIST, so the sdist allowlist is entirely unchecked. The sdist is a DIFFERENT mechanism from the wheel: `[tool.hatch.build.targets.sdist].include` is an explicit allowlist, so a path outside `/agent_workflows` can be absent from the sdist while the wheel carries it. | `rg -ln 'build.*--sdist\|tarfile' tests/` matches only `tests/test_installer.py`, where `tarfile` is used for an installer BACKUP archive (around its `tarfile.open(backup_path, "r:gz")` call), not a distribution. `pyproject.toml`'s sdist `include` list read in full. |
| F-04 | NOTHING ASSERTS THE CONSOLE SCRIPTS, so a wheel that installs with no `aw` on PATH passes the suite. The wheel does register all three today, each mapped to `agent_workflows.cli:main`. | `rg -ln entry_points.txt tests/` returns nothing. Built wheel at authoring: `entry_points.txt` contains `[console_scripts]` with `agent-workflows`, `agentwf` and `aw`, all three `= agent_workflows.cli:main`. |
| F-05 | NOTHING ASSERTS THE BROWSER ASSETS' PRESENCE IN EITHER ARTIFACT, and absence-only testing cannot see a missing one. The existing guard asserts what must NOT ship plus a handful of named modules, so it would pass with every browser asset missing. | `rg -ln run_analytics_assets tests/` returns nothing. The two tests in `tests/test_packaging.py` assert forbidden-path absence plus `agent_workflows/cli.py` and two `_data` paths. |
| F-06 | THE DROP IS SILENT, WHICH IS WHY A POSITIVE ASSERTION IS NEEDED AND WHY E-03 REPRODUCES IT. Hatchling honors `.gitignore`: a probe package whose asset matched an ignore pattern built at exit 0 with the asset OMITTED and no warning. A missing asset is therefore not a build error a human would see; it is a report that renders unstyled and inert after install, with a green suite. | Probe built at authoring against hatchling 1.32.4: `exit 0`, `kept.css present: True`, `ignored.css present: False`, stderr carrying only ordinary build progress lines. |
| F-07 | THE ASSETS AND MODULES ARE ALL PRESENT TODAY IN BOTH ARTIFACTS, so every arm in this plan is expected GREEN on arrival and none of it is fixing a live defect. Wheel: `app.css` 5235 bytes, `app.js` 21944 bytes, 357 entries total, no legacy `_data/.agents/workflows/` double-ship. Sdist: both assets plus `run_analytics_spa.py` and `run_analytics_report.py` present. | Wheel and sdist built into gitignored `.aw/state/` scratch at authoring and their member lists inspected; scratch removed afterwards and `git status --short` clean. |
| F-08 | THE BASE IS NOT GREEN AND ONLY THREE OF THE FIVE RED NODES ARE FILED. Bare `python3 -m pytest` at authoring HEAD `4fbbc8386` gave `5 failed, 4622 passed, 2 skipped, 3 warnings in 410.45s`. Filed: `test_spec_review_attestation` (`6bolin`), `test_run_finding_reachability` (`8jeh4x`), `test_selector_type_containment` (`bxnhdj`). NOT filed: `test_verbose_flag_reach` and `test_typecheck_gate`, and both PASS IN ISOLATION, so they are load-sensitive under `-n auto` rather than standing failures. | Bare suite run. Narrowed re-run of the two unfiled nodes: `2 passed in 118.59s`. Filed-ness checked with `rg -l` over `.aw/records/backlog/open/`. |
| F-09 | THE BUILD COST FITS THE PER-TEST BUDGET, so this file need not be marked `slow`. Wheel build 6.5s, sdist build 4.2s, against `conftest.py`'s `_DEFAULT_TEST_TIMEOUT` of 90.0s. Each build happens once per class via `setUpClass`. | Timed builds into gitignored scratch at authoring; `_DEFAULT_TEST_TIMEOUT = 90.0` in `conftest.py`. |
| F-10 | THE DECLARED PATH IS UNCONTESTED, and the NEARBY existing file is contested, which is a further reason to use a new file. `tests/test_packaging_distribution.py` is named by no pending plan. `tests/test_packaging.py` is cited by two pending plans (`1xthrh` and `ua133b`), though neither DECLARES it in `- Scope-Paths:`. | `rg -l` over `.aw/records/plans/pending/` for each path, then `- Scope-Paths:` read from each matching plan: `1xthrh` declares `agent_workflows/home_path_patterns.py`, `agent_workflows/agent_schema.py`, `agent_workflows/leak_sanitizer.py`, `tests/test_home_path_pattern_source.py`. |

## Proposed changes (ordered, validatable)

1. `tests/test_packaging_distribution.py` (new), wheel class: per-asset presence and non-emptiness assertions, the honesty guard against `run_analytics_spa.REQUIRED_ASSETS`, the reproduced gitignore-drop hazard arm, and the console-script mapping assertion (E-01, E-02, E-03, E-05).
2. `tests/test_packaging_distribution.py`, sdist class: a second build asserting the allowlist carries the browser assets, the analytics modules and the bundled data tree (E-04).

## Deferred / out of scope (with reason)

- The two properties `tests/test_packaging.py` ALREADY covers, the ship-versus-dev boundary and the runtime-dependency allowlist, are deliberately NOT re-asserted here. Duplicating them would double the build cost for no added coverage and create two places to update when the allowlist legitimately changes. This is the single most important scope decision in this plan and it follows directly from F-01.
  - Carrier-Declined: NOTHING IS OUTSTANDING, which is the whole point of the row. These two properties are COVERED by a shipped test (`tests/test_packaging.py`, restored by `2edb9ff8e`), so this row records that the plan declines to duplicate existing coverage, not that it leaves work undone. Filing a carrier for a property a committed test already asserts would create a false obligation.
- The deleted `tests/test_run_analytics_packaging.py` is NOT restored. Its `PerformanceBaselineTests` arms measure scan latency, peak heap, report size and telemetry overhead, which are BENCHMARKS and not packaging boundaries, and the repository keeps benchmark machinery under its own surfaces. Its `PackagedContentTests` arms overlap this plan's asset and module assertions and are subsumed by E-01 and E-04; its `test_the_isolated_install_proof_is_cis_named_wheel_job` asserts a CI job name, which is a workflow-file coupling this plan does not want to re-introduce.
  - Carrier-Declined: The performance arms are not a coverage gap this item owns; backlog item `mflqqf` is about the security-hardening checkers and the packaging boundary, and a latency baseline is neither. Filing a carrier would assert an obligation the item never created. A reviewer who wants the benchmarks restored should file that separately, where it can be justified on its own evidence; that is a deliberate refusal to launder unscoped work through this plan, not an oversight.
- The extracted-wheel import arms from the deleted file (`test_installed_wheel_migrate_layout_without_tools`) are NOT restored. They extract the wheel and spawn an interpreter with a filtered `sys.path`, which is a post-install IMPORT property rather than a distribution-contents property, and the `sys.path` filtering is fragile (it drops any path containing the string `tools`).
  - Carrier-Declined: THE DURABLE HALF IS COVERED HERE, so nothing outstanding remains to carry. What those arms protected is that `layout_migration` and `layout_inventory` SHIP, and E-04's module list asserts exactly that (both measured present in the wheel at authoring). What is dropped is the fragile post-install import spawn, whose own `sys.path` filter would silently discard any legitimate path containing the substring `tools`. Filing a carrier would assert an obligation to restore a mechanism this plan judges unsound.
- The `.gitignore` that hatchling injects into the sdist is NOT asserted against. `pyproject.toml` already documents it as a known, accepted, non-functional artifact of hatchling's VCS handling that an sdist-target `exclude` does not override, and the wheel never carries it.
  - Carrier-Declined: THIS IS AN ACCEPTED CONDITION, NOT AN OBLIGATION. `pyproject.toml`'s own sdist note records that it was investigated, that an sdist-target `exclude` does not override the injection, and that it was left as-is deliberately rather than adding non-functional config. Asserting its absence would codify a failing expectation, and filing a carrier would reopen a decision already recorded with its reasoning.
- The security-hardening half of backlog item `mflqqf` is Order 01 of this Set and is not touched here.
  - Carrier: gqyold

## Scope check

- Over-scope: none. One new test file, every arm required by a numbered item, and no source or document change at all. The plan deliberately does NOT widen to the existing guard's file even though the subject is adjacent.
- Under-scope: Deliberate and named above. The benchmark arms, the extracted-wheel import arms and the two already-covered properties stay out. A reviewer who wants any of them in scope should say so before approval, since each would change the declared `- Scope-Paths:`.
- ACCOUNTING AGAINST THE ITEM'S OWN SECOND MEASUREMENT, since that is what a reviewer will check this plan against. The item makes three packaging claims: `tests/test_packaging.py` was deleted (STALE, F-01, so nothing to restore), zero test files match `force-include` or `hatch.build` (HOLDS for test code, F-02, and this plan does not change it because asserting on build CONFIGURATION would be the code-pinning P16 forbids, while asserting on built ARTIFACTS is the behavioral equivalent), and no test builds a wheel and asserts its contents (STALE for the wheel, F-01; TRUE for the sdist, F-03, which E-04 closes). The item's framing was right about the gap existing and wrong about where it is; this plan targets the measured remainder.

## Required tests / validation

Narrowed runs with `-o addopts=""` for per-test counts on the new file, then the FULL suite run BARE (`python3 -m pytest`) with its actual output pasted.

CAPTURE YOUR OWN BASELINE; DO NOT USE A NUMBER FROM THIS PLAN. The authoring figure of `4622 passed, 5 failed, 2 skipped` at HEAD `4fbbc8386` is a dated measurement, not a bar. Every count comparison here is SELF-RELATIVE.

THE BAR IS "NO NEWLY FAILING TEST", NOT "GREEN", which follows from F-08 and is not a license to wave anything through. For EVERY red node at your base, re-run it ALONE before accepting it: three of the five authoring failures are filed (`6bolin`, `8jeh4x`, `bxnhdj`) and two passed in isolation, so a node that fails under load but passes alone must be REPORTED as load-sensitive. Anything red that is neither filed nor reproducible in isolation is new and must be investigated.

EVERY ARM IN THIS PLAN IS EXPECTED GREEN ON ARRIVAL (F-07), which changes what counts as validation: a passing run proves almost nothing on its own, so each V-item below demands a FALSIFIABILITY demonstration showing the arm can fail. That is the load-bearing evidence here, not the green run. Specifically, the asset-presence arm must be shown failing when an asset name is perturbed, and the console-script arm must be shown failing when a script name is perturbed; perturb the TEST's expectation, never the shipped package or `pyproject.toml`, so no tracked production file is edited at all.

METHOD RULE. Build every distribution into a `tempfile` directory, never into the repository tree, and never into a tracked `dist/`. The authoring measurements used a gitignored directory under `.aw/state/` and removed it afterwards with `git status --short` confirmed clean; a test must use `tempfile` so it leaves nothing behind even on failure. This is a SHARED CHECKOUT, so hold any temporary edit for the narrowed run only.

## Spec / documentation sync

No `.spec.md` file is amended, so none appears in `- Scope-Paths:`. No user-facing document gains or loses a claim either: this plan adds test coverage for packaging properties that already hold (F-07) and changes no shipped behavior, so `CHANGELOG.md` is not touched and the executor should say so rather than inventing an entry. Note for the reviewer that `CONTRIBUTING.md` carries packaging claims which plan `iocyf3` already corrected when it restored the wheel guard; this plan asserts nothing that contradicts them and so does not reopen that document.

## Open questions

### OQ-01: Should both builds live in one file, or should the sdist class be its own file?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT to keep ONE file with two classes. The two builds cost 6.5s and 4.2s against a 90.0s per-test budget, each once per class, so the combined file is comfortably inside the hang guard (F-09), and the two classes share the asset list and the honesty guard that keeps it from rotting, which is the coupling that argues against splitting them. Not blocking: splitting into two files changes only the declared `- Scope-Paths:` and no assertion, so a reviewer who prefers the split costs nothing by asking.

### OQ-02: Should this file be marked `pytest.mark.slow`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM A SHIPPED PRECEDENT AND ITS RECORDED REASONING, to leave it UNMARKED. `tests/test_packaging.py`'s own docstring sets out the argument for exactly this case: `addopts` deselects `slow`, CI's slow step is `continue-on-error: true` and therefore advisory, so marking a packaging guard `slow` leaves the boundary with NO blocking gate in routine runs, lane integration, or CI. Following the precedent keeps the two packaging files consistent, and F-09 shows the cost fits. Not blocking, but note the honest trade a reviewer should weigh: this adds roughly 11 seconds of build to every default suite run, on top of what the existing guard already spends, and a maintainer who would rather pay that only in CI can say so.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: Paste `python3 -m pytest tests/test_packaging_distribution.py -o addopts="" -q` showing every collected test passing with a count, and `rg -c run_analytics_assets tests/test_packaging_distribution.py`. Paste the observed asset sizes so the non-emptiness arm is shown doing real work rather than asserting against nothing. Then paste the FALSIFIABILITY demonstration, which is the load-bearing evidence for this item since the arm is expected green on arrival (F-07): perturb the expected asset NAME in the test file to a name the wheel does not carry, paste the resulting failure, restore it, and paste `git status --short` empty. Perturb the TEST, never the package or `pyproject.toml`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the honesty guard passing, and paste the derived expected set alongside the file's declared list so the reviewer sees they were COMPARED rather than both hard-coded. Paste a FALSIFIABILITY demonstration: temporarily add a third name to the test file's declared list, show the guard failing with a message that names the difference, restore it, and paste `git status --short` empty. Confirm in the pasted output that no count literal (such as the number two) is asserted anywhere in the arm.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the probe arm's run including its printed measurement, showing the probe wheel built at exit 0 with the kept asset present and the gitignored asset ABSENT, and name the hatchling version the probe resolved. Paste the arm's failure message text (from the source or a forced failure) so the reviewer can confirm it instructs a future reader to update E-01's rationale rather than to delete the assertion. Confirm the probe built under `tempfile` and left nothing behind: `git status --short` empty.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the sdist class passing and `rg -c sdist tests/test_packaging_distribution.py`. Paste the normalized member names for the asserted paths so the reviewer can see the `<name>-<version>/` strip worked and the comparison is in the same form as the wheel's. Paste a FALSIFIABILITY demonstration for the allowlist property specifically, since that is the mechanism this item exists to check: assert temporarily on a path that is OUTSIDE the sdist `include` allowlist (for example a `tests/` path), show it ABSENT from the sdist, and paste that result; then restore the file and paste `git status --short` empty. That probe is what proves the sdist allowlist is real rather than assumed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the console-script arm passing, with the parsed mapping shown so the reviewer sees each of the three scripts resolved to `agent_workflows.cli:main` rather than only that the strings appeared in the file. Paste a FALSIFIABILITY demonstration: perturb one expected script name or target in the test, show the failure, restore, and paste `git status --short` empty. Then paste the FULL bare `python3 -m pytest` output including the final summary line, with no added flags, plus your own execution-base baseline total measured BEFORE the change and the new total, stating the delta explicitly; the delta must equal the number of tests added. For EVERY red node in either run, paste its isolated re-run and classify it as filed-and-pre-existing (name the backlog id), load-sensitive (passes alone), or NEW (must be investigated). Do NOT report the run green by excluding any node. Paste `git diff --cached --name-only` before the commit showing ONLY the one declared `- Scope-Paths:` entry, and paste `aw ipd lint --phase pre-transition` reporting conforming.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution; it writes no `- Readiness:` field, since that is `/plan-review`'s output and never an author's to assert.

EXECUTION CONTRACT. Commit only the one declared `- Scope-Paths:` entry and only through `aw commit <plan> -- <paths>`, never `git add -A` and never with `--no-verify`; do not push; do not create a tag or release. The full suite must be run BARE (`python3 -m pytest`) and its actual output pasted, never summarized or claimed. EVERY V-ITEM REQUIRES A FALSIFIABILITY DEMONSTRATION and that is not optional padding: every arm this plan adds is expected GREEN on arrival (F-07), so a passing run alone does not show the arm can fail, and an assertion that cannot fail proves nothing. PERTURB THE TEST FILE ONLY. No production file, no `pyproject.toml`, no shipped asset may be edited to force a failure, since a packaging config edit in a shared checkout can break a co-worker's build. Restore every perturbation in the same pass and prove it with `git status --short` empty, holding each edit for the narrowed run only.

SCOPE FENCE. The declared `- Scope-Paths:` is `tests/test_packaging_distribution.py`. That is a DECLARATION so finalize can reconcile what was edited against what was declared, not a stop condition: if the work genuinely requires a path outside it, make the edit and JUSTIFY it at finalize with `--scope-reason`. Do not stop and report over a scope question. DO stop and report for a genuinely unsafe condition: a build that fails for a reason this plan did not predict (which would be a real packaging defect and must be reported, not skipped past), or a concurrent edit to `pyproject.toml` that changes either target's configuration under you. Verified at authoring that no pending plan declares the new path, and note that `tests/test_packaging.py` is CITED by two pending plans (`1xthrh`, `ua133b`) without being declared (F-10), which is a further reason this plan adds a new file rather than extending that one.

POST-GATE LIFECYCLE MOVE. The finalize obligation is unconditional: this plan does not reach `.aw/records/plans/executed/` until every `V-*` carries pasted evidence with a non-pending `Result` and `aw ipd lint --phase pre-transition` reports conforming. OWNERSHIP IS CONDITIONAL: when executed under `aw oc run` or `aw agy run`, the RUNNER performs the finalize and the lifecycle move, so do not invoke it yourself; when executed by hand outside a runner, the executor performs it via `aw ipd finalize`. Never hand-edit the status line and never hand-move the file. This plan is one of two graduation carriers for backlog item `mflqqf` (Order 01 carries the security-hardening half), so it does NOT close that item on its own; the item stays `graduated` until both carriers execute.
