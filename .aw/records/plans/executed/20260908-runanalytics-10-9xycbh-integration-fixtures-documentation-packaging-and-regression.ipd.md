# IPD: Integration fixtures, documentation, packaging, and regression closeout

- Date: 2026-09-08
- Kind: child
- Concern: Prove the entire analytics feature works from installed CLI to offline report and agent outputs, with complete documentation and no regressions.
- Scope: Build representative fixture corpora and mutation scenarios, run end-to-end/privacy/offline/package validation, finish user/developer documentation, and close every Set acceptance criterion.
- Scope-Paths: tests/fixtures/run_analytics/**, tests/test_run_analytics_e2e.py, tests/test_run_analytics_packaging.py, tests/test_run_analytics_privacy_boundary.py, tests/test_packaging.py, tests/test_docs.py, README.md, docs/**, pyproject.toml, .aw/records/plans/README.md
- Item-Dependencies: executed:5f2h8i, executed:6eq3oq, executed:8hald1, executed:aflsz3, executed:bzz5e6, executed:ixis0c, executed:lhccjf, executed:mm5p3v, executed:xbwq8n
- Status: executed
- Readiness: go-pending-approval
- Set: runanalytics
- Order: 10
- Highest E allocated: 10
- Author: Codex
- Id: 9xycbh

## Workflow history
- 2026-09-19 executed (aw oc run): aw oc run self-finalize: 9xycbh verified (set runanalytics, attempt 1). [Scope reconciliation - in-scope-unmodified .aw/records/plans/README.md: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified pyproject.toml: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified tests/test_packaging.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-08 approved (aw set): status set to approved

- 2026-09-08 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. PR-113..PR-124, ALL TWELVE FIXED, no open findings. The verdict token is stated explicitly because `plan_readiness.newest_verdict` reads the newest review record's first verdict token and falls back to a negative scan when none is present. THE BLOCKER IS THAT THIS PLAN'S PRIVACY PROOF WOULD HAVE PASSED WITH EVERY CANARY PRESENT, AND IT WAS PROBE-VERIFIED (PR-113, F-1). The orchestrator mandates that Order 10's sanitizer scan CONSUME `aw sanitize --agent`, and this plan's V-03 rests on it. But `leak_sanitizer.scan_working_tree` enumerates `git ls-files` (`_tracked_files`), and `.aw/records/runs/` is GITIGNORED at `.aw/.gitignore:14`, so the entire analytics output tree is invisible to that walk. Probe: a repo whose `.aw/records/runs/analytics/facts.json` contained a fail-severity home path AND prompt text scanned `{"outcome":"clean","findings":0}` at exit 0, while `scan_text` over the identical bytes returned `home-path` and `handle` at FAIL. Pointing the CLI at the analytics directory itself also reports clean, because `git ls-files` there is empty. So the Set's highest-risk requirement was to be validated by a command that cannot read the files in question, on the one child that owns acceptance. E-04 now scans artifact CONTENT through the same engine (`build_ruleset` + `scan_text`) and REQUIRES a control run proving the invocation flags a raw canary. SECOND, THE FIXTURE TREE IS THE OPPOSITE CASE AND IT BITES (PR-115, F-3): `tests/fixtures/run_analytics/**` is TRACKED (`git check-ignore` exit 1), so it IS in `_tracked_files` and the named `local-leaks` CI job WILL scan it; probe-verified, a fixture holding a seeded home path returns `home-path`/`handle` at fail. Committing a literal canary therefore breaks a fail-closed CI job, so canaries must be assembled at test time, as sibling `ixis0c`'s gate already requires. THIRD, "no live run corpus in this checkout" IS FALSE AND THE ORCHESTRATOR ALREADY SAID SO (PR-114, F-2): measured 135 runs, 1976 files, 272.3 MB, with 120 `oc_runipd.py`, 13 legacy `runipd.py`, 2 `ipdrunner.py` and ZERO Agy, so scenario 2 cannot be corpus-validated at all and scenario 3 "mixed-runner corpus" would be satisfied entirely by OpenCode lineage unless the two legacy generations become their own scenarios. FOURTH, THE ISOLATED-INSTALL PROOF CANNOT BE A TEST (PR-117, F-5): measured, `pip install` of the built wheel into a clean venv with `--no-index` FAILS on `filelock>=3`, so the install needs the network, which this plan's own rules forbid in tests; CI's existing `wheel` job already performs it. FIFTH, PERFORMANCE BUDGETS ARE MANDATED AGAINST DOCUMENTS THAT DO NOT EXIST (PR-118, F-6): no numeric time or memory threshold appears anywhere in the eleven plans, so E-06 now MEASURES AND PUBLISHES rather than inventing a retroactive gate. ALSO FIXED: "all 33 scenarios pass" contradicts Order 06's reviewed refusals and Order 07's refusal panel, so a REFUSAL is now an accepted passing outcome and a synthetic-fixture code-path exercise may never be reported as a corpus-level finding (PR-116, F-4); `docs/**` in `Scope-Paths` triggers `tests/test_docs.py`, a NON-slow deterministic gate asserting zero dash/link/command findings, which the plan never named, while the doc-index completeness it implies does not exist (three docs are unlinked today) (PR-119, F-7); `aw plans index --check` as written is a usage error and the real verb `aw index plans --check` FAILS TODAY on a pre-existing `stale-index` that pending plan `yvvf98` exists to remove (PR-121, F-9); the three E-items were mechanically sized and the Set orchestrator's OWN blocking OQ-01 names this plan's E-03 as one of the four densest items in the Set, this being the LAST unsplit child after nine siblings were split (PR-120, F-8, split to TEN); `pyproject.toml` is also declared by Order 07 and `.aw/records/plans/README.md` by `yvvf98`, so both may need a finalize `--scope-ack` rather than an edit (PR-122, F-10); the live-corpus proof the orchestrator demands conflicts with the never-commit rule unless only aggregate counts are pasted (PR-123, F-11); and the gate carried no execution contract, the tenth sibling in a row, plus 28 escaped backticks, one smart quote and no baseline, now measured `2 failed, 5655 passed, 3 skipped, 2 xfailed in 55.69s` with both failures attributed pre-existing (PR-124, F-12).

- 2026-09-08 to-review (aw set): set Item-Dependencies to executed:5f2h8i, executed:6eq3oq, executed:8hald1, executed:aflsz3, executed:bzz5e6, executed:ixis0c, executed:lhccjf, executed:mm5p3v, executed:xbwq8n

- 2026-09-08 to-review (Codex): enumerated the corpus, mutation, packaging, privacy, offline, performance, documentation, and full regression proof.
- 2026-09-08 draft (Codex): created.

## Goal

Close the Set with reproducible end-to-end evidence that an installed `aw` can analyze both runner formats incrementally, generate a correct offline SPA and agent data, and export only under the requested consent. Make locations, privacy limits, telemetry controls, statistics, and recovery discoverable to users.

THIS PLAN'S VALUE IS ENTIRELY IN WHETHER ITS PROOFS CAN FAIL, WHICH IS WHY THE ROOT FINDING MATTERS. Measured at review, the sanitizer invocation the orchestrator mandates for this child's privacy scan CANNOT SEE the analytics tree, because that walk enumerates tracked files and the tree is gitignored (F-1). A proof that cannot fail is worse than no proof, because it is reported as assurance. Every acceptance item below must therefore be falsifiable: state what result would count as a FAILURE, and for each detector-based check, run a CONTROL that proves the same invocation flags a planted positive.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

RIGHT-SIZING NOTE. Authored with THREE E-items, and the Set orchestrator `5lxvl3`'s own blocking open question names THIS plan's E-03 explicitly as one of the four densest items in the Set: "Order 10 E-03 is a single item covering the 33-scenario acceptance matrix, performance budgets, the sanitizer scan, the offline proof, the bare suite, lint and diff". Nine siblings were already split for the identical reason (`bzz5e6` 3->6, `lhccjf` 3->8, `5f2h8i` 3->7, `8hald1` 3->8, `aflsz3` 3->9, `6eq3oq` 3->8, `mm5p3v` 3->8, `ixis0c` 3->9), leaving this the LAST unsplit child while carrying the widest scope in the Set. The count-based lint clears nothing here: `aw ipd lint --phase author` reported conforming, and `ipd_schema.e_item_density_advisory` returned `None` for all three authored items. Split into TEN items across four groups (fixture corpus / the privacy proof / acceptance and packaging / documentation and closeout).

### Task group 1: The fixture corpus and canary discipline

- [x] E-01 Build the deterministic cross-runner fixture corpus, including the TWO LEGACY DRIVER GENERATIONS, and label the Agy side synthetic.
  MEASURED AT REVIEW, AND IT CORRECTS THIS PLAN'S OWN CONVENTION. This checkout holds 135 run directories, 1976 files, 272.3 MB. Their `state.json` driver paths are `oc_runipd.py` 120, the legacy `tools/ipdrunner/runipd.py` 13, and `tools/ipdrunner/ipdrunner.py` 2. `agy_runipd.py` is the driver of NONE. Two consequences the authored scenario list did not carry. FIRST, scenario 2 ("Agy completed run") and the Agy half of scenario 3 have NO observed on-disk shape, so their fixtures are written against the Agy runner's CODE and are SYNTHETIC; a passing Agy test proves conformance to the adapter's own assumptions and must never be reported as cross-host corpus validation. SECOND, the two legacy generations are the REAL historical schema drift in this repository, so each is its own scenario; without them scenario 3 is satisfied entirely by OpenCode lineage and the mixed-runner claim is vacuous.
  - Depends on: none
  - Expected outcome: fixtures use deterministic timestamps and hand-calculated expected values, cover both runners plus BOTH legacy generations as named scenarios, and every Agy-derived assertion is labeled synthetic in the fixture manifest itself; no byte of the live corpus is copied into `tests/fixtures/`.
  - Execution state: performed

- [x] E-02 Build the mutation harness for the cache lifecycle scenarios.
  This is the axis Order 02 (`bzz5e6`) owns and this plan proves: unchanged, active-then-changed, resumed-in-place, added, removed, corrupt-among-valid, and schema-upgraded. Order 02 recorded the freshness insight that matters here, so do not re-derive it: a RESUMED run reuses its directory, so mtime cannot establish staleness. Concurrency and interrupted-publication scenarios belong here too, and both must be driven deterministically rather than by real sleeps.
  - Depends on: E-01
  - Expected outcome: each lifecycle scenario is a named, independently runnable case with an asserted cache decision (reuse or rebuild) and a stated reason; a corrupt run among valid runs degrades that one run only; no test performs a real sleep, a real subprocess spawn, or a network call.
  - Execution state: performed

- [x] E-03 Assemble every sensitive canary AT TEST TIME, because a committed literal canary breaks a fail-closed CI job.
  MEASURED, AND THE TWO TREES BEHAVE OPPOSITELY. `tests/fixtures/run_analytics/**` is TRACKED (`git check-ignore` exits 1), so it IS enumerated by `leak_sanitizer._tracked_files` and the named `local-leaks` CI job (`.github/workflows/local-leaks.yml`, `python -m agent_workflows check-local-leaks .`) WILL scan it. Probe-verified: a fixture file containing a seeded home path returned `home-path` and `handle` at FAIL severity. So committing a canary as a literal fails a fail-closed gate. Sibling `ixis0c` already carries the correct rule in its gate ("generate it at test time or assemble it from fragments, as the detection engine does with its own patterns") and this plan, which owns the corpus, must carry it too. Note the canary set is the twelve classes `ixis0c` enumerates, of which the shipped detector catches ONE, so most canaries must be proven excluded STRUCTURALLY.
  - Depends on: E-01
  - Expected outcome: no committed fixture contains a literal home path, username, hostname, token, remote, or secret-shaped string; canaries are composed at runtime from fragments or from the real environment; a test asserts the committed fixture tree itself scans clean, which is the same gate CI applies.
  - Execution state: performed

### Task group 2: The privacy proof that can actually fail

- [x] E-04 Scan artifact CONTENT through the leak-sanitizer ENGINE, with a mandatory control run, because the CLI walk cannot see the analytics tree.
  THIS IS THE ROOT FINDING AND IT WAS PROBE-VERIFIED. The orchestrator requires this child's scan to CONSUME `aw sanitize --agent` rather than reimplement detection, and the intent (one engine, no second detector) is right. The MECHANISM is not: `leak_sanitizer.scan_working_tree` enumerates `git ls-files` via `_tracked_files`, and `.aw/records/runs/` is gitignored at `.aw/.gitignore:14`, so every cache, report, agent output, export and receipt this Set produces is INVISIBLE to that walk. Probe: a repo whose `.aw/records/runs/analytics/facts.json` held a fail-severity home path and prompt text scanned `{"outcome":"clean","findings":0}` at exit 0; `scan_text` over the identical bytes returned `home-path` and `handle` at FAIL. Pointing the CLI at the analytics directory as its root also reports clean, because `git ls-files` is empty there. `--staged` does not help either, since these artifacts are never staged.
  SO CONSUME THE ENGINE, NOT THE WALK: `leak_sanitizer.build_ruleset(repo_root)` plus `leak_sanitizer.scan_text(content, location, ruleset)` over each produced artifact's bytes. That satisfies the single-source rule exactly (no second detector, no reimplemented patterns) while reading files the walk skips by construction. And because the detector catches ONE of the twelve canary classes at fail severity (measured in `ixis0c`'s review and re-measured here: git remote, branch, commit message, `AWS_SECRET_ACCESS_KEY=`, `sk-proj-` token, `=cmd|` formula, `../../../etc/passwd`, prompt text and shell command all return ZERO findings; hostname only `warn`), the detector is CORROBORATION and the structural field allowlist is the guarantee.
  - Depends on: E-03
  - Expected outcome: every safe artifact class (cache, report, agent JSON/JSONL, metrics export, redacted export, diagnostics, submission receipt) is scanned by content through `build_ruleset`/`scan_text`; each scan is paired with a CONTROL asserting the same invocation FLAGS a planted positive, so "clean" and "not looking" are distinguishable; the eleven detector-blind canary classes are proven excluded STRUCTURALLY, not by detection; no second detector or regex set is written.
  - Execution state: performed

### Task group 3: Acceptance, performance, offline, and packaging

- [x] E-05 Execute the scenario matrix, treating a documented REFUSAL as a passing outcome.
  THE AUTHORED "all 33 scenarios pass" CONTRADICTS TWO REVIEWED SIBLINGS. Order 06 (`aflsz3`) now REFUSES four required analyses as under-powered (multi-attempt items n=6 of 733, recovery attempts n=6, merge-conflicts n=3) and refuses model comparison at 1.1 percent identity coverage; Order 07 (`6eq3oq`) renders a first-class REFUSAL PANEL rather than a chart. So scenarios 18 through 20 (failed merge then retry, permanent merge failure, test failure/retry loop) are exercisable as CODE PATHS against synthetic fixtures while the corpus-level ANALYSIS of them correctly refuses. Those are different claims and neither may be reported as the other. An acceptance run that turns a refusal into a number is the exact fabrication this Set exists to prevent.
  - Depends on: E-02
  - Expected outcome: every scenario maps to a named test with a stated expected outcome, where the expected outcome may legitimately be `cannot-determine` with an observed n; a synthetic-fixture code-path exercise is labeled as such and never cited as corpus validation; a test asserts a refused analysis cannot yield a rendered value.
  - Execution state: performed

- [x] E-06 MEASURE AND PUBLISH performance baselines; do not invent a threshold this Set never declared.
  MEASURED ABSENCE, WHICH DECIDES THE SHAPE OF THIS ITEM. No numeric time, memory or size threshold exists anywhere in the eleven plans: Order 07 requires a size budget to be DECLARED at execution, Order 03 requires "a measured overhead figure" with no pass bar, and no plan states a first-scan or rebuild time limit. So "against documented budgets" as authored points at documents that do not exist, and this plan explicitly originates no new behavior. The honest form is a recorded baseline: measure first scan, unchanged rescan, single-run rebuild, large-corpus peak memory, report size and telemetry overhead, publish each with its method and machine context, and let a future plan set a gate from real data. Inventing a threshold here would either be trivially passed or would fail a sibling's correct implementation on a number nobody agreed to.
  - Depends on: E-05
  - Expected outcome: each performance dimension has a measured figure with its method, input scale and machine context recorded; no measurement is asserted as a pass or fail against an undeclared budget; where a sibling DID declare a budget (Order 07's report size), that one is checked against its own declared value and cited.
  - Execution state: performed

- [x] E-07 Prove the report works offline with the network denied, and prove the proof can fail.
  Reuse the EXISTING harness rather than inventing a mock: `lifecycle_fixtures.run_no_network` subclasses `socket.socket` so any `connect`/`connect_ex` raises, which is the in-repo pattern for this exact assertion. The static half (zero `http:`/`https:`/external asset/dynamic import/fetch/XHR/WebSocket occurrences in the bundle) is Order 07's E-07; this item's job is the END-TO-END proof at Set scale, plus opening the bundle from a path containing spaces and non-ASCII characters.
  - Depends on: E-05
  - Expected outcome: the bundle loads from a `file://` path (including one with spaces and Unicode) with sockets denied and issues zero requests; a control proves the same harness FAILS when a deliberate network reference is introduced; the offline claim is stated as what was tested rather than as browser-universal.
  - Execution state: performed

- [x] E-08 Prove the packaged artifacts carry every asset, and keep the isolated INSTALL out of the test suite.
  MEASURED, AND IT RULES OUT THE OBVIOUS TEST. `pip install` of the built wheel into a clean venv with `--no-index --no-cache-dir` FAILED on `filelock>=3` (the single declared runtime dependency), so an isolated-environment install REQUIRES the network, which this plan's own rules forbid in any test. CI already performs exactly that proof in its `wheel` job (build, fresh venv, `pip install dist/*.whl`, import and `--version` smoke) across three operating systems, so the correct division is: the SUITE asserts artifact CONTENTS offline by reading the built wheel and sdist, and the INSTALL proof is the existing CI job, cited by name and not reimplemented.
  ALSO NOTE THE OWNERSHIP BOUNDARY. Order 07 owns the POSITIVE per-asset packaging assertion (its E-02, after its review measured that `tests/test_packaging.py` asserts only ABSENCE of forbidden content and reports `7 passed` while every browser asset could be missing). This item extends that to the whole feature surface and must not duplicate or replace it.
  - Depends on: E-06
  - Expected outcome: the wheel and sdist are proven to contain every analytics Python module and every SPA asset by a POSITIVE per-name assertion, extending `tests/test_packaging.py` rather than paralleling it; no test in the suite performs a network install; the isolated-install evidence is the named CI `wheel` job's output, or a manual out-of-suite run whose network use is recorded.
  - Execution state: performed

### Task group 4: Documentation and closeout

- [x] E-09 Write the documentation for every audience, and satisfy the DETERMINISTIC docs gate the plan never named.
  MEASURED, AND `docs/**` IN `Scope-Paths` MAKES THIS LOAD-BEARING. `tests/test_docs.py` is NOT `slow`-marked, so the bare suite runs it, and it asserts `docs_check.check_docs_dir(docs/)` returns ZERO findings across three checks: no em (U+2014) or en (U+2013) dash anywhere, every relative Markdown link resolves to an existing file, and every `aw <token>` names a known TOP-LEVEL subcommand. Currently 0 findings, so any new finding is attributable to this plan. Two specifics. FIRST, only the FIRST token after `aw` is checked, and `runs` is already known, so `aw runs analyze` passes; a top-level typo does not. SECOND, em and en dashes are forbidden in README and docs because they are USER-FACING prose (`AGENTS.md`, `CONTRIBUTING.md:142`), and that rule does NOT extend to this IPD. `test_required_docs_present` also pins a fixed doc list, so a new doc is additive and must not displace one.
  DO NOT CLAIM AN INDEX-COMPLETENESS GATE THAT DOES NOT EXIST: measured, three shipped docs (`branch-protection.md`, `runner-profiles.md`, `wtiso-state-taxonomy.md`) are not linked from `docs/README.md` and nothing fails, so linking a new analytics doc from the index is good practice enforced by review, not by a test.
  - Depends on: E-08
  - Expected outcome: documentation gives exact commands and paths, explains disposable storage and deletion, distinguishes measured from derived from missing values, states the no-anonymity and no-causation limits, and NAMES the detector's measured blind spots as `ixis0c` requires; `python3 -m pytest tests/test_docs.py` passes with zero findings; no em or en dash appears in any file under `docs/` or in `README.md`.
  - Execution state: performed

- [x] E-10 Produce the full regression evidence against a baseline the executor measured itself.
  THE SUITE IS NOT SUFFICIENT ALONE, AND THE INDEX VERB IN THE AUTHORED PLAN DOES NOT EXIST. Measured: `aw plans index --check` is a usage error (`invalid choice: 'plans'`); the real verb is `aw index plans --check`, and it EXITS 1 TODAY with `stale-index: INDEX.json is missing or out of date`, a PRE-EXISTING condition that pending plan `yvvf98` exists to remove by untracking the generated manifests. So treat that check as a recorded pre-existing state, not as a gate this plan must turn green. Separately the bare suite DESELECTS `-m 'not slow'`, which hides `tests/test_cli_conformance_matrix.py` (the leaf-declaration gate Orders 08 and 09 depend on) and `tests/test_leak_sanitizer.py`; run those explicitly.
  - Depends on: E-09
  - Expected outcome: a bare `python3 -m pytest` run with its `N passed` line, compared to the executor's own baseline by FAILING NODE IDS and never by totals; the explicit `slow`-marked gates run and pasted; `aw ipd lint --phase pre-transition` conforming; `git diff --check` clean; the `aw index plans --check` state recorded with its pre-existing attribution; every failure routed to the owning child rather than patched here.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The required test command is bare `python3 -m pytest`; flags such as `-q`, `-x`, or `--tb` are not acceptable final evidence. Measured baseline at review HEAD `5fe992aa`: `2 failed, 5655 passed, 3 skipped, 2 xfailed in 55.69s`. Both failures are PRE-EXISTING live-corpus couplings, confirmed by inspection: `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today` fails on an unrelated pending plan (`20260906-integearn-01-32ij2j`), and `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows` fails because plan `kgpptv` is now `approved` where the test expects `reviewed`. Re-measure in the executing worktree and compare NODE IDS.
- IPD IDs, E/V identifiers, dependencies, and indexes are tool-maintained; execution must run sync/lint/index commands rather than edit derived metadata by hand.
- THE LEAK-SANITIZER CLI CANNOT SEE THIS SET'S OUTPUT, WHICH INVALIDATES THE AUTHORED PRIVACY PROOF. `scan_working_tree` enumerates `git ls-files` (`_tracked_files`) and `.aw/records/runs/` is gitignored at `.aw/.gitignore:14`. Probe-verified: an analytics artifact containing a fail-severity home path and prompt text scanned `{"outcome":"clean","findings":0}` at exit 0, while `scan_text` over the same bytes returned `home-path` and `handle` at FAIL. Consume the ENGINE (`build_ruleset` + `scan_text`) over artifact content, which honors the one-engine rule while reading the files the walk skips.
- THE DETECTOR COVERS ONE OF THE TWELVE CANARY CLASSES AT FAIL SEVERITY, re-measured here: home path CAUGHT; hostname `warn` only; git remote, branch name, commit message, `AWS_SECRET_ACCESS_KEY=`, `sk-proj-` token, `=cmd|` formula, `../../../etc/passwd`, prompt text and shell command ALL uncaught. Three of its fail rules are compiled from this maintainer's own tokens, so they match nothing on an adopter's machine. The structural allowlist is the guarantee; the detector is corroboration whose blind spots the documentation must name.
- THE FIXTURE TREE IS TRACKED AND THEREFORE IS SCANNED. `tests/fixtures/run_analytics/**` is not gitignored (`git check-ignore` exit 1), so it IS in `_tracked_files` and the `local-leaks` CI job scans it; a fixture holding a seeded home path returns `home-path`/`handle` at fail (probe-verified). Compose canaries at test time.
- THERE IS A LIVE RUN CORPUS AND THE AUTHORED CLAIM WAS FALSE. Measured: 135 run directories, 1976 files, 272.3 MB; drivers are `oc_runipd.py` 120, legacy `tools/ipdrunner/runipd.py` 13, `tools/ipdrunner/ipdrunner.py` 2, and Agy ZERO. The corpus is gitignored and disposable, so it is a READ-ONLY smoke input and never committed evidence; the Agy side is necessarily synthetic; the two legacy generations are the real historical schema drift.
- AN ISOLATED WHEEL INSTALL NEEDS THE NETWORK. Measured: `pip install` of the built wheel with `--no-index` FAILED resolving `filelock>=3`. CI's `wheel` job already builds, installs into a fresh venv and smoke-tests the CLI on three operating systems, so cite it rather than writing a networked test.
- THE PACKAGING TEST IS ABSENCE-ONLY TODAY. `tests/test_packaging.py` asserts FORBIDDEN content is missing plus a few named modules and reports `7 passed`; it would pass with every new asset absent. Order 07 owns the positive per-asset assertion; extend that file rather than paralleling it.
- THE DOCS GATE IS DETERMINISTIC AND RUNS IN THE BARE SUITE. `tests/test_docs.py` is not `slow`-marked and requires `docs_check.check_docs_dir(docs/)` to return zero findings (no em/en dash, every relative link resolves, every top-level `aw` verb known); it is at zero today. Em and en dashes are forbidden in `README.md` and `docs/` as USER-FACING prose and are NOT forbidden in this IPD.
- `aw plans index --check` DOES NOT EXIST; the verb is `aw index plans --check`, and it exits 1 today on a pre-existing `stale-index` that pending plan `yvvf98` addresses by untracking the generated manifests.
- Existing `.aw/records/runs` content is ignored/disposable and must not be used as permanent test evidence. Where the orchestrator requires a REAL-artifact privacy check, paste only aggregate counts and rule names, never the offending content.

## Findings

The integration matrix must cover at least these 33 cases from the implementation prompt, each carrying its measured feasibility so an executor cannot mistake a refusal for a failure:

1. OpenCode completed run. Corpus-supported (120 runs).
2. Agy completed run. SYNTHETIC ONLY; zero Agy runs exist here.
3. Mixed-runner corpus. Must include the TWO LEGACY generations (`runipd.py` 13, `ipdrunner.py` 2), or it is satisfied entirely by OpenCode lineage and proves nothing.
4. Review and execute separated.
5. Review and execute aggregated.
6. Verifier present.
7. Verifier absent.
8. Retry/multi-attempt IPD. Code path exercisable synthetically; the corpus ANALYSIS refuses (n=6 of 733, Order 06 F-4).
9. Resumed same-directory run. Note Order 02's finding: a resumed run reuses its directory, so mtime cannot establish staleness.
10. In-progress run cached then changed.
11. New run added after first analysis.
12. Run removed after first analysis.
13. One corrupt run among valid runs; degradation must be scoped to that run.
14. Missing cost.
15. Missing token component.
16. Missing model price.
17. Price changes at an effective-date boundary. Order 06 measured the two real eras and their boundary instants; use them.
18. Failed merge then successful retry. Synthetic code path; corpus analysis refuses (n=3).
19. Permanent merge failure. Same.
20. Test failure/retry loop. Synthetic code path; corpus analysis refuses (n=6).
21. Gate/risk-heavy activity.
22. Overlapping activity intervals.
23. Telemetry disabled.
24. Basic start/end telemetry.
25. Periodic telemetry.
26. Different node pseudonyms across attempts.
27. Probe permission/timeout/malformed failure.
28. Concurrent analyzers/cache writers.
29. Interrupted cache/report publication.
30. Empty corpus.
31. Large synthetic corpus (Order 07 measured the real scale at 29766 fact rows; size the fixture to it).
32. Sensitive canaries in every forbidden source field, ASSEMBLED AT TEST TIME and proven excluded STRUCTURALLY for the eleven classes the detector misses.
33. Fixed CLI leaf collisions and `--` target escape. Note Order 08 measured that `aw runs -- status` returns ALL runs rather than resolving one, so a naive collision assertion passes vacuously.

Also cover package contents, report opening from a path containing spaces and Unicode, export archive traversal, submission network isolation, config reconfiguration, and snapshot retention.

## Proposed changes (ordered, validatable)

1. E-01 through E-03 build the corpus, the mutation harness, and the runtime-assembled canary set.
2. E-04 replaces the blind CLI walk with a content-level engine scan plus a control run.
3. E-05 through E-08 run the matrix with refusals accepted, measure and publish performance, prove offline behavior, and assert packaged contents without a networked install test.
4. E-09 writes the documentation against the deterministic docs gate; E-10 produces the regression evidence against a self-measured baseline.

## Deferred / out of scope (with reason)

- Real user run data is never committed as a fixture, and no canary is committed as a literal (it would fail the `local-leaks` CI job, measured).
- STRENGTHENING `leak_sanitizer` IS OUT OF SCOPE, as sibling `ixis0c` also records: it backs `aw sanitize`, a pre-commit hook and a CI job, so changing its false-positive profile is a separate plan with its own risk budget. This plan changes only WHICH ENTRY POINT is called, not what the engine detects.
- DECLARING NUMERIC PERFORMANCE GATES is out of scope, because no sibling declared any (measured) and this plan originates no behavior. E-06 measures and publishes; a future plan may set a bar from that data.
- A NETWORKED INSTALL TEST is out of scope; CI's `wheel` job already performs the isolated install, and an offline install fails on `filelock` (measured).
- A hosted analytics service and server-side aggregation are outside this repository.
- Automatic workflow/model changes based on findings are excluded; the tool advises and supports experiments.
- Fixing the pre-existing `stale-index` state or the two pre-existing suite failures is out of scope; they are the baseline that makes a new regression attributable.

## Scope check

- Over-scope: no new analytical behavior originates here; a failure returns to the child that owns the behavior. Specifically, and each for a measured reason: do NOT write a second detector or regex set (one engine, per the single-source rule); do NOT edit `leak_sanitizer` (see the deferred note); do NOT invent a performance threshold no sibling declared; do NOT write a test that installs over the network (an offline install fails on `filelock`, measured); do NOT duplicate Order 07's positive per-asset packaging assertion; do NOT commit any part of the live corpus or any literal canary; do NOT introduce an em or en dash into `README.md` or `docs/` (a non-slow test fails on it); and do NOT edit a spec, since none is declared in `Scope-Paths`.
- `tests/test_packaging.py`, `tests/test_docs.py` and `tests/test_run_analytics_privacy_boundary.py` are now in `Scope-Paths`, necessarily: the first two are the existing gates this plan extends rather than parallels, and the third is where the content-level privacy proof lives.
- `pyproject.toml` is ALSO declared by Order 07 and `.aw/records/plans/README.md` by pending plan `yvvf98`. If a sibling already made the edit, the correct action is a finalize `--scope-ack` on the declared-but-unmodified path, NOT a redundant edit; `aw ipd finalize` refuses to complete without one.
- An out-of-scope edit is not forbidden outright, it must be JUSTIFIED: `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path.
- Under-scope: covers fixture breadth including the legacy generations, canary discipline, the content-level privacy proof, end-to-end behavior, offline proof, packaged contents, every documentation audience, and repository-wide regression evidence. The engine-level scan (E-04), the runtime canary assembly (E-03), the legacy-generation scenarios (E-01), the refusal-tolerant matrix (E-05), the measure-and-publish performance posture (E-06) and the out-of-suite install boundary (E-08) were all under-scope or wrong before review.

## Required tests / validation

- Execute the scenario matrix with each case's expected outcome stated in advance, INCLUDING the cases whose correct outcome is a documented refusal.
- Content-level leak scan of cache, report, agent JSON/JSONL, metrics export, redacted export, diagnostics and submission receipts via `build_ruleset` + `scan_text`, each paired with a CONTROL proving the invocation flags a planted positive. A `scan_working_tree` or `aw sanitize --agent` result over the analytics tree is NOT acceptable evidence: it reports clean by construction (measured).
- A test asserting the committed fixture tree itself scans clean under the same gate CI applies, so no canary was committed as a literal.
- Offline proof: the bundle opens from `file://` (including a path with spaces and Unicode) with sockets denied via `lifecycle_fixtures.run_no_network`, issuing zero requests, plus a control proving the harness fails when a network reference is introduced.
- Cached versus forced-rebuild facts compared byte-for-byte after excluding documented volatile manifest fields.
- Measured and PUBLISHED figures for first scan, unchanged rescan, one-run rebuild, large-corpus peak memory, report size and telemetry overhead, each with method and machine context; only Order 07's declared size budget is checked as a pass or fail.
- Packaged-content assertions naming each analytics module and SPA asset in BOTH wheel and sdist, extending `tests/test_packaging.py`. The isolated INSTALL proof is CI's `wheel` job (or a recorded manual run), never a test.
- `python3 -m pytest tests/test_docs.py` with zero `docs_check` findings, and a grep proving no em or en dash in `README.md` or under `docs/`.
- The explicit `slow`-marked gates the bare suite deselects: `tests/test_cli_conformance_matrix.py`, `tests/test_cli_quality_gates.py`, `tests/test_leak_sanitizer.py`, `tests/test_packaging.py`.
- `aw ipd lint --phase pre-transition`, bare `python3 -m pytest`, `git diff --check`, and `aw index plans --check` with its pre-existing `stale-index` state recorded rather than fixed.
- No test may reach the network, spawn a browser, sleep for real time, or use the live corpus as its assertion source.

## Spec / documentation sync

THIS PLAN DECLARES NO `.spec.md` IN `Scope-Paths` AND MUST EDIT NONE. If execution concludes a spec contract must change, that is a STOP-and-raise.

Update README and focused docs for:

- Quick start and optional enablement (note `ixis0c`'s measured correction: all analytics code ships in-package, so the wizard gates ENABLEMENT, not code presence).
- Exact storage tree under `.aw/records/runs/analytics/`, and that the whole tree is gitignored and disposable.
- Analyze/query/open/path/list/snapshot commands.
- Agent JSON/JSONL schemas and examples, emitted through the existing `aw.agent/v1` envelope.
- Fact/data dictionary, metric conservation, overlap, missingness, and phase semantics.
- Taxonomy rules and explanations, including the measured multi-label overlap.
- Effective-dated prices, source maintenance, recorded versus estimated costs, and the two measured eras.
- SPA controls, accessibility, offline limitations, large-data fallback, and which analyses REFUSE with an observed n.
- Telemetry fields/defaults/periodic opt-in/platform support/overhead/privacy, described as PSEUDONYMOUS and never anonymous.
- Cache invalidation, corruption recovery, retention, and deletion.
- Export tiers, sanitizer limits, explicit submission, endpoint governance, and no automatic network activity.
- THE DETECTOR'S MEASURED BLIND SPOTS BY NAME, which `ixis0c` calls the most important documentation obligation in the Set. State what is structurally excluded, what is detected, and what is neither. Never write that an artifact "passes the sanitizer" as a privacy guarantee.
- Troubleshooting and compatibility matrix.

Update `.aw/records/plans/README.md` only if the new command/report lifecycle creates a durable plan convention; do not add analytics operational detail to always-loaded instructions. Note pending plan `yvvf98` also declares that file.

## Open questions

"No open questions" was not accurate: the plan required six decisions it specified nowhere. All six are answerable from repository evidence or measurement rather than by asking, so each is recorded resolved with its basis. Every reviewed sibling in this Set carried the same inaccurate claim.

### OQ-01: How is the privacy boundary actually proven, given the mandated scan cannot see the artifacts?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW BY PROBE as a CONTENT-LEVEL scan through the same engine (`leak_sanitizer.build_ruleset` + `scan_text`) over each produced artifact's bytes, with a mandatory control run. Measured: `scan_working_tree` enumerates `git ls-files` via `_tracked_files`, and `.aw/records/runs/` is gitignored at `.aw/.gitignore:14`, so a probe repo whose `analytics/facts.json` held a fail-severity home path and prompt text scanned `{"outcome":"clean","findings":0}` at exit 0, while `scan_text` over the identical bytes returned `home-path` and `handle` at FAIL; pointing the CLI at the analytics directory as its own root also reported clean, because `git ls-files` is empty there. REJECTED: `aw sanitize --agent` over the tree as the orchestrator's wording implies, because it cannot fail and would report assurance it never established. Temporarily `git add`-ing analytics output so the walk sees it, rejected because it stages gitignored disposable artifacts into a shared checkout's index and risks committing exactly the content under test. Writing a second detector in `run_analytics_*`, rejected outright as the drift the single-source rule forbids and which the orchestrator explicitly names. The chosen fix honors the orchestrator's INTENT (one engine, no reimplemented detection) while correcting its MECHANISM.

### OQ-02: Do the two legacy driver generations and the synthetic Agy side become explicit scenarios?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW BY CENSUS as YES for the legacy generations and YES for a synthetic label on Agy. Measured across all 135 `state.json` files: `oc_runipd.py` 120, `tools/ipdrunner/runipd.py` 13, `tools/ipdrunner/ipdrunner.py` 2, `agy_runipd.py` ZERO. So the authored convention "no live run corpus in this checkout" is false (135 runs, 1976 files, 272.3 MB), scenario 2 has no observed shape, and scenario 3 as authored would be satisfied entirely by OpenCode lineage. REJECTED: claiming cross-host corpus validation from a passing Agy fixture, because it proves conformance to the adapter's own assumptions only. Omitting the legacy generations as "historical", rejected because they ARE the schema drift the ingestion layer exists to survive and 15 real runs carry it. Committing live runs as fixtures to get real Agy shapes, rejected because no Agy run exists to copy and the corpus must never be committed regardless.

### OQ-03: What counts as a passing acceptance outcome for an analysis a sibling refuses?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW from two reviewed siblings as A DOCUMENTED REFUSAL IS A PASS, and a synthetic code-path exercise may never be reported as a corpus finding. Order 06 (`aflsz3`) refuses four required analyses at n=3 to 6 and refuses model comparison at 1.1 percent identity coverage; Order 07 (`6eq3oq`) renders a first-class refusal panel. REJECTED: requiring a computed value for all 33 scenarios as authored, because it would force an executor to fabricate five analyses from refusals, destroying the property this Set exists to protect. Dropping the refused scenarios from the matrix, rejected because their CODE PATHS are real and testable against synthetic fixtures, and dropping them would leave the ingestion and reporting paths unexercised.

### OQ-04: Who declares the performance budgets this plan measures against?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW BY MEASURED ABSENCE as MEASURE AND PUBLISH, with no invented gate. No numeric time, memory or size threshold appears anywhere across the eleven plans: Order 07 leaves its size budget to be declared at execution, Order 03 requires a measured overhead figure with no bar, and no plan states a scan or rebuild limit. REJECTED: this plan declaring the thresholds, because it explicitly originates no new behavior and a number invented at acceptance time is either trivially passed or fails a sibling's correct implementation on a bar nobody agreed to. Deleting the performance requirement, rejected because the measurements are genuinely useful and are the only data from which a future gate can be set honestly. Order 07's own DECLARED size budget is the one exception and is checked as a pass or fail against its declared value.

### OQ-05: Is the isolated wheel install a test or an out-of-suite step?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW BY EXECUTION as OUT OF SUITE. Measured: `pip install` of the built wheel into a clean venv with `--no-index --no-cache-dir` FAILED resolving `filelock>=3`, the single declared runtime dependency, so an isolated install requires network access, which this plan's own rules forbid in tests. CI's `wheel` job already builds the wheel, creates a fresh venv, installs it and smoke-tests the console script and packaged-data lookup on ubuntu, macos and windows. REJECTED: a networked install test in the suite, because it contradicts the no-network rule and would make the suite fail offline. Vendoring or removing `filelock` to enable an offline install, rejected outright: `pyproject.toml` documents at length why that dependency exists (a silent mutual-exclusion failure on Windows without it). Asserting only that the wheel BUILDS, rejected because it proves nothing about importability from site-packages, which is precisely what the CI job establishes.

### OQ-06: Does this plan split its three E-items?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW as YES, consistent with the precedent already applied to all nine siblings. The Set orchestrator `5lxvl3`'s blocking OQ-01 names this plan's E-03 explicitly as one of the four densest items in the Set, and its own recommendation was option (b), re-cut into finer E/V items within existing child boundaries. Nine siblings were split on that basis (`bzz5e6` 3->6, `lhccjf` 3->8, `5f2h8i` 3->7, `8hald1` 3->8, `aflsz3` 3->9, `6eq3oq` 3->8, `mm5p3v` 3->8, `ixis0c` 3->9), leaving this the last unsplit child while carrying the widest scope. Measured: `aw ipd lint --phase author` reported conforming and `ipd_schema.e_item_density_advisory` returned `None` for all three items, so nothing mechanical would catch it. REJECTED: leaving three items and relying on the V-items to catch a partial pass, because the work most likely to fall off the tail of E-03 was the privacy proof, the offline proof and the packaging proof, which are the three things this Set's value depends on. Splitting this child into further children, rejected because it renumbers the Set and changes ownership, where re-cutting the checklist changes neither.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the fixture manifest mapping every scenario to its assertions and hand-calculated expected values. Paste the driver census re-measured in the executing worktree (120 `oc_runipd.py`, 13 `runipd.py`, 2 `ipdrunner.py`, 0 Agy at review) and show BOTH legacy generations present as named scenarios. Paste the synthetic label on every Agy assertion. Paste proof no live-corpus byte was copied into `tests/fixtures/`.
  - Observed evidence: the generated fixture manifest, both legacy generations present as named scenarios, the synthetic Agy label in the data, and the hand-calculated totals:

    ```
    FIXTURE MANIFEST (`tests.fixtures.run_analytics.corpus_manifest()`, generated, not hand-typed):
        scenario_count: 33
        generation_drivers: {"oc_runipd": "agent_workflows/oc_runipd.py", "agy_runipd": "agent_workflows/agy_runipd.py", "runipd": "tools/ipdrunner/runipd.py", "ipdrunner": "tools/ipdrunner/ipdrunner.py"}
        legacy_generations: ['runipd', 'ipdrunner']
        synthetic_generations: {"agy_runipd": "zero Agy runs in the measured corpus (120 oc_runipd, 13 runipd, 2 ipdrunner, 0 agy); written against agy_runipd's code, never an observed Agy run"}
        expected_outcome_counts: {"cannot-determine": 5, "computed": 28}
        canary_classes: 13

    BOTH LEGACY GENERATIONS PRESENT AS NAMED SCENARIOS, asserted by
    `FixtureCorpusTests::test_the_corpus_carries_all_four_generations_including_both_legacy_ones`, which
    reads `sources.inventory_corpus(...).generation_counts` and requires
    {"oc_runipd": 1, "agy_runipd": 1, "runipd": 1, "ipdrunner": 1}. PASSED.

    THE DRIVER CENSUS COULD NOT BE RE-MEASURED IN THIS WORKTREE, AND THAT IS REPORTED RATHER THAN
    INVENTED. `.aw/records/runs/` DOES NOT EXIST in this isolated lane:
        $ ls .aw/records/runs/ ; find .aw/records/runs -type f | wc -l
        ls: cannot access '.aw/records/runs/': No such file or directory
        0
    The tree is gitignored, so an isolated worktree starts without it. The review-time census
    (120 oc_runipd / 13 runipd / 2 ipdrunner / 0 agy, 135 runs) is therefore CITED AS A REVIEW-TIME
    SNAPSHOT and is NOT claimed as current; no number in this plan's implementation depends on it, because
    the fixtures reproduce the PROPERTY (four generations, uniform schema_version) rather than the counts.
    `test_schema_version_is_uniform_so_it_cannot_discriminate_a_generation` PASSED, which is the property
    the census motivated.

    SYNTHETIC LABEL ON EVERY AGY ASSERTION, in the DATA and not a comment:
    `test_the_agy_scenarios_are_labeled_synthetic_in_the_manifest_itself` PASSED, and its converse
    `test_no_non_agy_scenario_is_falsely_marked_synthetic` PASSED (a blanket label would be meaningless).

    NO LIVE-CORPUS BYTE COPIED INTO `tests/fixtures/`:
    `test_no_live_corpus_byte_was_copied_into_the_fixture_tree` PASSED. It enumerates `git ls-files --
    tests/fixtures/run_analytics` and requires zero `state.json`/`events.jsonl`/`driver.lock` and zero
    non-`.py` tracked paths, so the tree holds only generator modules.

    HAND-CALCULATED EXPECTATION:
    `test_hand_calculated_totals_match_the_ingested_facts` PASSED: tokens input=100, output=20,
    token_total=120 (100+20==120 by hand) and wall_seconds=3600.0 from the 00:00:00Z..01:00:00Z interval.

        $ python3 -m pytest tests/test_run_analytics_e2e.py -o addopts=""
        34 passed in 0.84s
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste each lifecycle scenario (unchanged, active-then-changed, resumed-in-place, added, removed, corrupt-among-valid, schema-upgraded, concurrent, interrupted) with its asserted cache decision and stated reason. Paste proof a resumed run is not judged by mtime. Paste proof a corrupt run degrades only itself. Paste a grep proving no test sleeps, spawns a subprocess, or opens a socket.
  - Observed evidence: all nine lifecycle cases with the verdict AND reason each asserted, plus the mtime-invariance and containment proofs:

    ```
    EVERY LIFECYCLE CASE WITH ITS ASSERTED DECISION AND STATED REASON (from
    `tests.fixtures.run_analytics.mutations.run_all`, each case in its OWN repo):

        case                     verdict  reason                     conforms  concern
        unchanged                hit      fresh-complete-entry       True      a terminal run with an entry and identical inputs is REUSED
        active_then_changed      rebuild  fingerprint-changed        True      a run cached while live, then mutated, must rebuild
        resumed_in_place         rebuild  run-not-terminal           True      a resumed run reuses its directory, so mtime cannot prove staleness
        added                    rebuild  no-entry                   True      a run first seen after an analysis has no entry
        removed                  (none)   (none)                     True      a removed run yields NO decision
        corrupt_among_valid      rebuild  no-entry                   True      one unreadable run degrades ITSELF
        schema_upgraded          rebuild  schema-version-mismatch    True      an entry from another cache schema is not reused
        concurrent               skip     lock-busy                  True      a contended entry SKIPS and never waits
        interrupted_publication  rebuild  entry-unreadable           True      a partial entry is never read as valid

    `conforms` is computed from the verdict AND the reason together, so a case cannot pass for the wrong
    reason. `test_every_lifecycle_case_produces_its_declared_decision_and_reason` PASSED.

    A RESUMED RUN IS NOT JUDGED BY MTIME: `test_a_resumed_run_is_not_judged_by_mtime` PASSED. The case
    rewrites `state.json` to a RUNNING queue and then RESTORES the original mtime with `os.utime`, and the
    test asserts `mtime_unchanged` is True before requiring verdict=rebuild reason=`run-not-terminal`. So
    the only observable difference is the terminal flag; an mtime-keyed rule would report a hit.

    A CORRUPT RUN DEGRADES ONLY ITSELF: `test_a_corrupt_run_degrades_only_itself` PASSED with
    corrupt_fact_count=0, healthy_fact_count>0, corrupt warnings containing `state-unreadable`, and
    totals.total==2 (the sweep COMPLETED over both).

    NO SLEEP, NO SUBPROCESS, NO SOCKET: `test_no_mutation_case_sleeps_spawns_or_opens_a_socket` PASSED. It
    greps the harness source for `time.sleep`, `subprocess.`, `socket.`, `requests.` and `urlopen` and
    requires none. Contention is driven by taking the real `platform_lock` entry lock directly, and
    mutations are made observable by stamping mtimes.

    Also PASSED: `test_a_removed_run_yields_no_decision_at_all`,
    `test_a_contended_entry_skips_and_writes_nothing` (entry_written False),
    `test_a_truncated_entry_never_reads_back_as_valid` (entry_readable False).
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the runtime canary assembly showing no literal home path, username, hostname, token or secret-shaped string is committed. Paste the scan of the COMMITTED fixture tree reporting clean under the same gate CI applies, and paste the probe measurement that motivated this item (a fixture holding a seeded home path returns `home-path`/`handle` at FAIL).
  - Observed evidence: runtime canary assembly, the committed tree scanning clean under the gate CI applies, and the probe proving that gate can fail:

    ```
    RUNTIME CANARY ASSEMBLY, NO COMMITTED LITERAL. All 13 classes are built from fragments by
    `corpus.canary(kind)` (`_CANARY_FRAGMENTS`), e.g. the filesystem path is `"/ho" + "me/" + "gfa" +
    "riello" + "/VC/agent-workflows"`. `test_every_canary_class_is_assembled_and_non_empty` PASSED and
    asserts the fixture set EQUALS `run_analytics_export.CANARY_CLASSES`, so a class cannot be quietly
    dropped:
        canary_classes (13): archive-traversal, branch-name, commit-message, environment-secret,
        filesystem-path, git-remote, high-entropy-token, hostname, prompt-text, response-text,
        shell-command, spreadsheet-formula, username

    THE COMMITTED FIXTURE TREE SCANS CLEAN UNDER THE SAME GATE CI APPLIES:
    `test_the_committed_fixture_tree_scans_clean_under_the_same_gate_ci_applies` PASSED (it scans every
    `.py` under `tests/fixtures/run_analytics/` through `build_ruleset(REPO_ROOT)` + `scan_text`, the same
    engine and ruleset the `local-leaks` job compiles), and
    `test_this_test_module_also_scans_clean` PASSED for the test module itself.

    Corroborated by the repository's own gate over the tracked set:
        $ python3 -m agent_workflows sanitize --agent
        {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
        exit=0
    (That command IS valid evidence here, because `tests/fixtures/**` is TRACKED. It is NOT valid for the
    analytics tree, which is V-04's subject.)

    THE PROBE MEASUREMENT THAT MOTIVATED THE RULE, re-run at execution rather than cited:
    `test_the_gate_can_fail_which_is_why_clean_means_something` PASSED. A fixture-shaped line holding a
    seeded home path returns, through the same invocation:
        rules: ['handle', 'home-path'] , every finding at severity 'fail'
    So a literal canary WOULD break the fail-closed `local-leaks` job, and "clean" above is a real result
    rather than a scan that never looked.

    THE TREE REALLY IS TRACKED, re-measured not assumed:
    `test_the_fixture_tree_is_tracked_which_is_why_the_rule_exists` PASSED, requiring
    `git check-ignore -q tests/fixtures/run_analytics` to exit 1 (NOT ignored).
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste, per safe artifact class, the CONTENT-level scan through `build_ruleset` + `scan_text` reporting clean, EACH paired with a CONTROL run showing the same invocation FLAGS a planted positive. A scan lacking its control is a FAILED validation. Paste the measurement proving the CLI walk cannot substitute (an analytics artifact containing a fail-severity home path scanned `findings: 0` at exit 0). Paste, for each of the eleven detector-blind canary classes, the STRUCTURAL exclusion that removes it, and re-measure the detector's coverage.
  - Observed evidence: every artifact class scanned BY CONTENT with its control, the walk-cannot-see measurement reproduced, and the 2-of-13 detector coverage re-measured:

    ```
    PER-ARTIFACT-CLASS CONTENT SCAN, EACH PAIRED WITH ITS CONTROL. Every check below runs
    `leak_sanitizer.build_ruleset(REPO_ROOT)` + `leak_sanitizer.scan_text(content, location, ruleset)` over
    the artifact's actual bytes, then re-scans the SAME bytes with a canary appended and requires the
    `home-path` fail rule to fire. A scan whose control does not fire FAILS the test, so "clean" and "never
    looked" are distinguishable by construction. All PASSED:

        analytics/cache/entry.json                  clean, control fired
        analytics/report/index.html                 clean, control fired
        analytics/report/analysis.json              clean, control fired
        analytics/report/<manifest members>         clean, control fired
        analytics/agent/record.json  (aw.agent/v1)  clean, control fired
        analytics/agent/stream.jsonl (aw.agent/v1)  clean, control fired
        analytics/export/metrics.json               clean, control fired
        analytics/export/events-redacted.json       clean, control fired
        analytics/export/bundle/<every file>        clean, control fired
        analytics/diagnostics/message.txt           clean (via privacy.redact_text)
        analytics/submit/receipt.json               clean, control fired

    The diagnostics case additionally asserts its INPUT was detectable before redaction (`home-path`
    present), which is that artifact's control. The receipt case additionally asserts
    `auth_value_recorded` is False and that the destination's query string (`token=...`) is absent.

    THE MEASUREMENT PROVING THE CLI WALK CANNOT SUBSTITUTE, reproduced at execution as a test rather than
    cited: `WhyTheCliWalkCannotSubstituteTests::test_scan_working_tree_reports_clean_over_a_gitignored_analytics_artifact`
    PASSED. In a throwaway git repo whose `.aw/records/runs/analytics/facts.json` holds a fail-severity home
    path AND prompt text:
        tracked files: ['.aw/.gitignore']          # the artifact is NOT enumerated
        scan_working_tree findings: 0              # exit-0 clean
        scan_text over the identical bytes: [('handle','fail'), ('home-path','fail')]
    And `test_the_analytics_tree_as_its_own_root_also_reports_clean` PASSED: pointing the walk at the
    analytics directory as its own root also reports clean, because `git ls-files` is empty there. So
    `aw sanitize --agent` / `scan_working_tree` over the analytics tree is NOT acceptable evidence, exactly
    as this plan's stop condition requires.

    DETECTOR COVERAGE RE-MEASURED AT EXECUTION (not cited):
    `test_the_detector_covers_two_of_thirteen_classes_re_measured_here` PASSED. Scanning each assembled
    canary through the same engine:
        filesystem-path      2 findings  [('handle','fail'), ('home-path','fail')]
        username             1 finding   [('handle','fail')]
        hostname             0 findings
        prompt-text          0 findings
        response-text        0 findings
        shell-command        0 findings
        git-remote           0 findings
        branch-name          0 findings
        commit-message       0 findings
        environment-secret   0 findings
        high-entropy-token   0 findings
        spreadsheet-formula  0 findings
        archive-traversal    0 findings
    CAUGHT 2 of 13 at fail severity; 11 BLIND. The test asserts these sets EQUAL
    `export.DETECTOR_COVERED_CLASSES` / `DETECTOR_BLIND_SPOTS`, so a ruleset change fails here rather than
    silently invalidating the documentation.

    THE ELEVEN BLIND CLASSES ARE EXCLUDED STRUCTURALLY, NOT BY DETECTION:
    - `test_every_blind_class_is_refused_by_the_write_side_allowlist` PASSED: for each of the 11, the key is
      absent from `privacy.ALLOWED_METRIC_KEYS` and `project_metric_facts` RAISES `PrivacyRefusal` (refused,
      not dropped), so the envelope is never built.
    - `test_every_blind_class_is_dropped_by_the_export_field_construction` PASSED: `build_redacted_events`
      yields `redaction_method='structural-field-allowlist'` with all 11 names in `dropped_field_names` and
      none of the 11 canary VALUES present anywhere in the serialized payload.
    - `test_the_structural_exclusion_holds_for_a_class_the_detector_cannot_see` PASSED: prompt text returns
      ZERO detector findings AND is refused by the projector, asserted together, which is the whole
      argument.

    NO SECOND DETECTOR OR REGEX SET WAS WRITTEN: `test_no_second_detector_or_regex_set_was_written` PASSED.
    It PARSES each of this plan's four new modules with `ast` and requires no `import re`, no `from re`, and
    no `re.compile/match/search/findall` call. (A substring check was tried first and correctly flagged its
    own docstring, which is why the AST form is used.)

        $ python3 -m pytest tests/test_run_analytics_privacy_boundary.py -o addopts=""
        16 passed in 0.75s
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the scenario-to-test map with each case's expected outcome stated in advance, showing which cases legitimately expect `cannot-determine` with an observed n. Paste a test proving a refused analysis cannot yield a rendered value. Paste proof every synthetic-fixture exercise is labeled as such and none is cited as corpus validation.
  - Observed evidence: the scenario-to-test map with every outcome stated in advance, the five refusals with their observed n, and the no-rendered-value proof:

    ```
    SCENARIO-TO-TEST MAP WITH EVERY EXPECTED OUTCOME STATED IN ADVANCE. The 33 scenarios are
    declared in `tests.fixtures.run_analytics.SCENARIOS`, each carrying `expected_outcome` and (for a
    refusal) the `observed_n` that justifies it. Structure asserted by:
    - `test_the_matrix_declares_exactly_thirty_three_numbered_scenarios` PASSED (contiguous 1..33, unique
      names).
    - `test_every_scenario_states_its_expected_outcome_in_advance` PASSED (each is `computed` or
      `cannot-determine`, each states a concern, and every `computed` one asserts something).
        expected_outcome_counts: {"cannot-determine": 5, "computed": 28}

    THE CASES WHOSE CORRECT OUTCOME IS A DOCUMENTED REFUSAL, WITH THEIR OBSERVED n:
    `test_a_refusal_is_a_declared_passing_outcome_with_an_observed_n` PASSED and pins the refusing set to
    exactly [8, 18, 19, 20, 26]:
        8  retry-multi-attempt        cannot-determine  n=6   (Order 06 refuses multi-attempt analysis)
        18 failed-merge-then-retry    cannot-determine  n=3   (Order 06 refuses merge-conflict analysis)
        19 permanent-merge-failure    cannot-determine  n=3
        20 test-failure-retry-loop    cannot-determine  n=6
        26 different-node-pseudonyms  cannot-determine  n=6   (thin identity coverage)
    Each n is required to be a positive int below 30, so a refusal cannot be declared at a sample size that
    would not justify one.

    A REFUSED ANALYSIS CANNOT YIELD A RENDERED VALUE:
    `test_a_refused_analysis_cannot_yield_a_rendered_value` PASSED. A `cannot-determine` result routed
    through `spa.refusal_from_result` produces a `RefusalView`, and the test asserts that view exposes NO
    `value` attribute, so there is no path by which a refusal reaches a chart. (Order 07's
    `build_view_model` routes on `renderable` structurally; this asserts the type-level consequence.)

    EVERY SYNTHETIC EXERCISE IS LABELED AND NONE IS CITED AS CORPUS VALIDATION:
    `test_every_synthetic_exercise_is_labeled_and_none_claims_corpus_validation` PASSED, requiring every
    synthetic scenario's reason to name the zero-Agy measurement.

    LIVE EXERCISES (code paths, not declarations), all PASSED:
        test_scenario_1_and_2_ingest_their_generation_and_host          (oc->opencode, agy->agy)
        test_scenario_7_absent_verifier_is_not_applicable_rather_than_zero
        test_scenario_13_corrupt_run_is_contained                       (sweep completes, 0 warnings)
        test_scenario_30_empty_corpus_is_a_valid_sweep                  (totals.total==0, no decisions)
        test_scenario_31_corpus_scale_ingestion_without_a_time_dependency (24 runs, no sleep)
        test_scenario_32_every_canary_class_is_planted_and_structurally_excluded (all 13 refused)
    Scenarios 8/18/19/20/26 are exercised as CODE PATHS against synthetic fixtures while their corpus-level
    ANALYSIS correctly refuses; the two claims are kept separate and neither is reported as the other.
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste each measured figure (first scan, unchanged rescan, one-run rebuild, large-corpus peak memory, report size, telemetry overhead) with its method, input scale and machine context. Paste proof no measurement is asserted against an undeclared budget. Paste Order 07's DECLARED size budget checked against its own value, citing where it was declared.
  - Observed evidence: each measured figure with method, input scale and machine context, none asserted against an undeclared budget:

    ```
    MEASURED FIGURES WITH METHOD, INPUT SCALE AND MACHINE CONTEXT, printed by
    `PerformanceBaselineTests` at teardown (`python3 -m pytest tests/test_run_analytics_packaging.py
    -o addopts="" -s`). Machine context carries NO hostname and no path, deliberately:

        "machine_context": {
          "cpu_count": 12,
          "machine": "x86_64",
          "platform": "Linux-6.8.0-139-generic-x86_64-with-glibc2.39",
          "python": "3.14.6"
        }

        dimension                                  measurement                 input   method
        first-scan                                 886.7 ms                    40 runs update_cache over a cold cache
        unchanged-rescan                            85.6 ms                    40 runs update_cache over a warm cache
        single-run-rescan                            1.9 ms                    1 run   update_cache over one cached run
        corpus-ingest-peak-heap                    612951 B (0.58 MiB)         40 runs tracemalloc peak over ingest_corpus
        telemetry-sample-overhead-system-adapter   ~161 us/sample              50 iter SystemResourceProbeAdapter.resources()
        telemetry-sample-overhead-fake-adapter     ~4 us/sample                50 iter FakeResourceProbeAdapter.resources()
        report-document-size                       18886 B                     500 rows len(render_document(...).encode('utf-8'))

    NO MEASUREMENT IS ASSERTED AGAINST AN UNDECLARED BUDGET. Every record carries
    `asserted_against_a_budget` and `budget_source`; six of the seven read
    `false` / "none declared by any plan in this Set (re-checked at execution)". The guard
    `test_no_measurement_here_is_asserted_against_an_undeclared_budget` PASSED and requires any record
    claiming a pass/fail to CITE the sibling declaration it rests on.

    What IS asserted is CORRECTNESS, which is what makes each timing a measurement of the intended work
    rather than of a no-op: the first scan must report rebuild==40, the rescan hit==40, the single-run pass
    total==1. `test_measure_first_scan_unchanged_rescan_and_single_run_rebuild` PASSED.

    ORDER 07's DECLARED BUDGET, CHECKED AGAINST ITS OWN VALUE AND CITED:
    `test_report_size_IS_checked_against_order_07s_declared_budget` PASSED.
        declared at: `agent_workflows/run_analytics_spa.py`, symbol `SIZE_BUDGET_BYTES`
        budget_bytes: 8388608 (8 MiB), stated basis: a 0.71 MB base64-gzip payload at 29766 rows plus
                      sub-1 MB chrome
        measured:     18886 bytes at 500 rows  ->  PASS
    This is the ONLY pass/fail among the performance dimensions, because it is the only budget a sibling
    actually declared. Re-checked at execution across all eleven plans in the Set: no numeric time, memory
    or first-scan threshold is declared anywhere, so none is invented here.
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the bundle opening from `file://` with sockets denied via `lifecycle_fixtures.run_no_network`, including a path containing spaces and non-ASCII characters, with zero recorded connect attempts. Paste the CONTROL proving the harness FAILS when a deliberate network reference is introduced. State the offline claim as what was tested, not as browser-universal.
  - Observed evidence: the file:// read with sockets denied from a spaces+Unicode path, and BOTH controls:

    ```
    THE BUNDLE OPENS FROM `file://` WITH SOCKETS DENIED, FROM A HOSTILE-BUT-LEGAL PATH:
    `OfflineReportTests::test_the_bundle_opens_from_a_file_url_with_sockets_denied` PASSED. The document is
    rendered through the real `spa.build_view_model` + `spa.render_document` (two data rows and one REFUSED
    analysis, so both a payload and a refusal panel are present), written to

        <tmp>/a report dir with spaces/rapport-\u00e9t\u00e9-\u65e5\u672c/index.html

    and read back with `socket.socket` replaced by a denying subclass (the
    `lifecycle_fixtures.run_no_network` pattern: `connect`/`connect_ex` record the attempt and raise). The
    test asserts the URI starts with `file://`, that the DECODED path really contains a space and U+65E5,
    that the bytes round-trip exactly, that the recorded attempt list is EMPTY (zero connections), and that
    `spa.scan_for_network_references(document)` returns [].

    TWO CONTROLS, BOTH PASSED, because one alone would leave a gap:
    - `test_the_offline_harness_FAILS_when_a_network_reference_is_introduced`: planting
      `<script src="https://cdn.example.com/chart.js">` makes `scan_for_network_references` return a
      non-empty list, so a clean scan is a real result rather than a scanner that never ran.
    - `test_denying_sockets_really_does_deny_them`: inside the harness, `socket.socket().connect(...)`
      RAISES and the attempt is recorded, so a silently uninstalled harness cannot make the assertion above
      vacuous.

    THE OFFLINE CLAIM IS STATED AS WHAT WAS TESTED, NOT AS BROWSER-UNIVERSAL:
    `test_the_offline_claim_is_stated_as_what_was_tested` PASSED, pinning the claim text:
        "TESTED: the published bundle is read from a file:// path (including spaces and non-ASCII
        characters) with sockets denied, and a static scan finds zero network references. NOT TESTED:
        behavior in any particular browser engine."
    The same limit is written into `docs/run-analytics.md` ("what was NOT tested is behavior in any
    particular browser engine"), so it travels with the user-facing documentation and not only with the
    test. The STATIC half (zero network references in the bundle) remains Order 07's E-07; this is the
    end-to-end read-path proof at Set scale.
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the POSITIVE per-name assertions showing every analytics module and SPA asset present in BOTH the wheel and the sdist listing, added to `tests/test_packaging.py` (re-measure its count; `7 passed` at review). Paste the CI `wheel` job (or a recorded manual run) as the isolated-install evidence, and paste the measurement showing why it is not a test (an offline `pip install` FAILED on `filelock>=3`). Paste a grep proving no test in the suite installs over the network.
  - Observed evidence: positive per-name assertions in wheel AND sdist, and the isolated-install citation verified to exist:

    ```
    POSITIVE PER-NAME ASSERTIONS IN BOTH ARTIFACTS. `ANALYTICS_MODULES` is enumerated from the
    package directory at import time (so a new module is covered without a hand edit) and gives 19 modules;
    the test also requires at least 18 so the enumeration cannot collapse and pass vacuously.
    - `test_every_analytics_module_ships_in_the_wheel_BY_NAME` PASSED (missing == []).
    - `test_every_analytics_module_ships_in_the_sdist_BY_NAME` PASSED (the sdist `include` is a separate
      allowlist mechanism, so the wheel proves nothing about it).
    - `test_the_browser_assets_order_07_declares_ship_in_both_artifacts` PASSED. It IMPORTS
      `REQUIRED_BROWSER_ASSETS` from `tests/test_packaging.py` rather than restating it, so the two cannot
      disagree, and asserts each asset present in the wheel AND the sdist. This EXTENDS Order 07's E-02
      (which owns the positive per-asset assertion) to the whole feature surface; it does not duplicate or
      replace it.
    - `test_the_analytics_modules_are_importable_from_the_extracted_wheel` PASSED: the wheel is EXTRACTED
      and every analytics module imported in a child interpreter with the dev checkout purged from
      `sys.path`. No index, no venv, no network.

    Order 07's own file still passes and its count is re-measured (the plan cited `7 passed` at review; it
    is now 13):
        $ python3 -m pytest tests/test_packaging.py -o addopts=""
        13 passed in 7.32s

    WHY THE ISOLATED INSTALL IS NOT A TEST, re-measured: the wheel declares exactly ONE unconditional
    runtime dependency, so an isolated install needs an index.
    `test_the_single_runtime_dependency_is_why_the_install_needs_a_network` PASSED, asserting exactly one
    `Requires-Dist` without an `extra ==` marker and that it names `filelock`.

    NO TEST IN THE SUITE INSTALLS OVER THE NETWORK:
    `test_no_test_in_this_suite_installs_over_the_network` PASSED. It PARSES every `tests/test_*.py` with
    `ast` and flags an install argv only where the list/tuple is an ARGUMENT to a subprocess spawner
    (`run`/`check_call`/`check_output`/`call`/`Popen`); offenders == []. Two narrower forms were each
    measured wrong first and are recorded in the test's own docstring: a substring search flagged this
    test's docstring, and a bare list/tuple scan flagged `tests/test_run_analytics_wizard.py:292`, which is
    a tuple of FORBIDDEN tokens asserting the OPPOSITE of an install.

    THE ISOLATED-INSTALL EVIDENCE IS CI's NAMED JOB, AND THE CITATION IS CHECKED TO EXIST:
    `test_the_isolated_install_proof_is_cis_named_wheel_job` PASSED, reading
    `.github/workflows/tests.yml` and requiring the strings "build + import wheel", "python -m venv" and
    "pip install dist/*.whl" to be present (job declared at `.github/workflows/tests.yml:80`, matrix over
    three operating systems). So the citation is verified rather than asserted from a comment.

        $ python3 -m pytest tests/test_run_analytics_packaging.py -o addopts=""
        12 passed in 8.87s
    ```
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste `python3 -m pytest tests/test_docs.py` passing with zero `docs_check` findings. Paste a grep proving no em (U+2014) or en (U+2013) dash in `README.md` or under `docs/`. Paste the documentation section NAMING the detector's measured blind spots, and paste proof no document claims an artifact "passes the sanitizer" as a privacy guarantee. Paste the per-audience coverage map.
  - Observed evidence: the deterministic docs gate at zero findings, zero em/en dashes, and the blind-spot list coupled to the code:

    ```
    THE DETERMINISTIC DOCS GATE PASSES WITH ZERO FINDINGS:
        $ python3 -c "from agent_workflows import docs_check; from pathlib import Path; print('findings:', len(docs_check.check_docs_dir(Path('docs'))))"
        findings: 0

        $ python3 -m pytest tests/test_docs.py -o addopts=""
        29 passed in 0.36s
    (23 passed before this plan; the six new ones are `RunAnalyticsPrivacyDocTests`.)

    NO EM (U+2014) OR EN (U+2013) DASH IN `README.md` OR UNDER `docs/`:
        $ python3 - <<'EOF'   # scans README.md plus every docs/**/*.md
        ... for ch in (U+2014, U+2013): report any line containing it
        EOF
        em/en dash findings: 0

    THE DOCUMENTATION NAMES THE DETECTOR'S MEASURED BLIND SPOTS, AND THE CLAIM IS COUPLED TO THE CODE:
    `test_every_detector_blind_spot_is_NAMED_in_the_documentation` PASSED. It asserts every member of
    `run_analytics_export.DETECTOR_BLIND_SPOTS` appears in `docs/run-analytics.md` and every member of
    `DETECTOR_COVERED_CLASSES` is named as covered, so a future ruleset change FAILS here with a message
    naming the document to update rather than leaving a stale claim in place. The document lists the two
    covered classes (`filesystem-path`, `username`) and all eleven blind ones by name, plus the absence of
    any entropy or secret-shape rule and the fact that three fail rules are maintainer-specific and match
    nothing elsewhere.

    NO DOCUMENT CLAIMS AN ARTIFACT "PASSES THE SANITIZER":
    `test_no_document_claims_an_artifact_PASSES_the_sanitizer` PASSED over every `docs/**/*.md`, forbidding
    "passes the sanitizer", "passed the sanitizer", "sanitizer-clean" and "verified clean by the sanitizer".
    The document states the opposite explicitly: "never read 'the sanitizer found nothing' as a privacy
    guarantee", and records that `aw sanitize` reports clean over the analytics tree BECAUSE IT CANNOT SEE
    IT.

    PER-AUDIENCE COVERAGE MAP, asserted rather than promised:
    `test_the_documentation_covers_every_audience_this_plan_owes` PASSED, requiring the sections
    "## Quick start (operator)", "## The agent surface", "## The privacy boundary", "## Troubleshooting",
    "## Compatibility", "## The cache, and when it rebuilds" and "## Telemetry".
    Also PASSED: `test_the_documentation_distinguishes_measured_derived_and_missing` (recorded / measured /
    derived / missing / unavailable / not-applicable all present) and
    `test_the_documentation_states_the_no_anonymity_and_no_causation_limits` ("no tier is anonymous",
    "minimization is not anonymity", "pseudonymous, never anonymous", and the causation limit).
    `test_the_analytics_doc_exists_and_is_linked_from_the_index` PASSED (linked from `docs/README.md`).

    Content covered per the plan's spec-sync list: exact commands and paths, the gitignored/disposable
    storage tree and how to delete it, the query views and agent envelope, provenance and the three kinds of
    absence, refusals with observed n, effective-dated pricing, telemetry defaults/interval bounds/measured
    overhead, the full cache decision table with reason codes and corruption recovery, export tiers with no
    anonymity claim, explicit submission with no automatic network activity, troubleshooting, and
    compatibility (including that Agy support is NOT corpus-validated).
    ```
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: paste the bare `python3 -m pytest` output including its `N passed` summary line, and the FAILING NODE ID delta against the baseline you measured yourself (never a total comparison). Paste the explicit `slow`-marked runs (`tests/test_cli_conformance_matrix.py`, `tests/test_cli_quality_gates.py`, `tests/test_leak_sanitizer.py`, `tests/test_packaging.py`). Paste `aw ipd lint --phase pre-transition` conforming and `git diff --check` clean. Paste `aw index plans --check` with its result recorded and the pre-existing `stale-index` attributed. For any failure, paste which child owns it and the fact that it was NOT patched here.
  - Observed evidence: the bare suite with its N passed line, the failing-node-id delta, the slow gates, and the two pre-existing failures proven pre-existing:

    ```
    BARE SUITE, WITH ITS `N passed` LINE (no added flags; the configured addopts supply
    `-q -n auto --dist=worksteal -m 'not slow'`):

        $ python3 -m pytest
        ........................................................................ [ 99%]
        ................                                                         [100%]
        8228 passed, 3 skipped, 2 xfailed in 92.10s (0:01:32)

    FAILING-NODE-ID DELTA AGAINST A BASELINE MEASURED IN THIS WORKTREE (never a total comparison):
        baseline, this worktree at HEAD 906b0e83, before any change:
        $ python3 -m pytest
        8160 passed, 3 skipped, 2 xfailed in 98.59s (0:01:38)

        baseline failing node ids: (none)
        post-change failing node ids: (none)
        DELTA: {} -- no node id fails now that did not fail before.
    Counts moved 8160 -> 8228 (+68), which is this plan's new tests being collected; the plan's cited
    review-time baseline of `2 failed, 5655 passed` does NOT reproduce here and is not used, exactly as the
    re-measure rule requires. Both of those review-time failures are absent: this worktree's baseline had
    ZERO failures.

    THE `slow`-MARKED GATES THE BARE SUITE DESELECTS, RUN EXPLICITLY:
        $ python3 -m pytest tests/test_cli_quality_gates.py tests/test_leak_sanitizer.py tests/test_packaging.py -o addopts=""
        tests/test_cli_quality_gates.py ..............                           [ 22%]
        tests/test_leak_sanitizer.py ....................................        [ 79%]
        tests/test_packaging.py .............                                    [100%]
        63 passed in 13.80s

        $ python3 -m pytest tests/test_cli_conformance_matrix.py tests/test_cli_quality_gates.py tests/test_leak_sanitizer.py tests/test_packaging.py -o addopts=""
        FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_no_undeclared_parser_leaves
        FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_every_declared_leaf_gets_a_full_scenario_row_set
        2 failed, 72 passed in 227.15s (0:03:47)

    THOSE TWO FAILURES ARE PRE-EXISTING AND ARE PROVEN SO RATHER THAN ASSUMED, AND THEY ARE NOT PATCHED
    HERE. Both report the same five undeclared leaves:
        ['oc profile add', 'oc profile default', 'oc profile list', 'oc profile remove', 'oc profile show']
    Three independent lines of evidence:
    1. OWNERSHIP: this plan changes no CLI or declaration code. `git diff --name-only 906b0e83..HEAD`
       returns only README.md, docs/README.md, docs/run-analytics.md, tests/test_docs.py, and the four new
       test/fixture modules. Nothing under `agent_workflows/` is touched at all.
    2. REPRODUCED WITH THIS PLAN'S WORK REMOVED: with `tests/ docs/ README.md` set aside,
       `python3 -m pytest tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests -o addopts=""`
       still reported `2 failed, 2 passed in 0.39s` with the identical five leaves.
    3. ALREADY PINNED BY A SIBLING: `tests/test_run_analytics_cli.py` carries
       `KNOWN_UNDECLARED = {"oc profile add", "oc profile default", "oc profile list", "oc profile remove",
       "oc profile show"}` described in place as "the measured pre-existing baseline ... a live failure of
       `test_no_undeclared_parser_leaves` that predates this plan and is explicitly out of scope".
    OWNING CHILD: neither this plan nor any runanalytics sibling; the `oc profile` leaf declarations belong
    to the runner-profiles surface. Filed as a backlog item this turn rather than patched, because
    declaring five CLI leaves is outside this plan's Scope-Paths and would change a normative inventory.

        $ git diff --check
        (no output; CLEAN)

        $ python3 -m agent_workflows index plans --check
        INDEX.json: check.stale-index-missing: INDEX.json has not been generated; run 'aw index plans'
        INDEX.md: check.stale-index-missing: INDEX.md has not been generated; run 'aw index plans'
        REAL EXIT: 0
    RECORDED WITH ITS ATTRIBUTION AND NOT FIXED. The plan predicted `stale-index` at exit 1; the
    CURRENT state is `stale-index-MISSING` at exit 0, because the generated manifests are now UNTRACKED
    (`.aw/.gitignore` names `records/plans/INDEX.json`/`INDEX.md`), which is the outcome pending plan
    `yvvf98` existed to produce. So this is a pre-existing, non-failing condition, reported rather than
    turned green.

    `aw ipd lint --phase pre-transition` output is recorded in this plan's workflow history at finalize.
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: this is the Set's single integration and release-proof owner and it adds no independent feature behavior, which is why the ten items belong to ONE PLAN. NOTE THE SCOPE OF THAT ARGUMENT: it does not make a fixture corpus, a canary discipline, a content-level privacy proof, an acceptance matrix, a performance baseline, an offline proof, a packaging proof, a documentation pass and a regression sweep one deliverable, which is why the ten items exist (F-8, and the Set orchestrator's own OQ-01 naming this plan's E-03 among the four densest items in the Set).

EXECUTION CONTRACT. This plan requires explicit human approval (`aw ipd set approved 9xycbh --by-human --message ...`), and its `Item-Dependencies` refuse dispatch until all nine siblings are `executed`. Execute only after Orders 01 through 09. A green unit suite without the content-level privacy proof, the offline proof, the packaged-content proof, the cache-mutation matrix and the bare-suite evidence is NOT completion.

- SCOPE FENCE, AS A DECLARATION AND NOT A HALT. The declared paths are the fence; the prohibitions in the Scope check above are the measured ones. If the work genuinely requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, because `aw ipd finalize` refuses to complete until every out-of-scope changed path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`. Do NOT stop the run over a scope question. Note two declared paths may legitimately need an ACK rather than an edit: `pyproject.toml` (Order 07 may already have made the packaging edit) and `.aw/records/plans/README.md` (pending plan `yvvf98` also declares it).
- COMMIT DISCIPLINE: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never `-a`, and NEVER push. THIS IS A SHARED CHECKOUT: verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since a rejected hook can leave paths you never staged in the index. Prefer the tooled path (`aw commit <plan> -- <paths>`).
- NEVER COMMIT THE LIVE CORPUS OR A LITERAL CANARY. The corpus is gitignored, mutable and 272.3 MB, and its `state.json` files carry absolute maintainer home paths in the first fields an ingester reads. Where the orchestrator requires a REAL-artifact privacy check, run it and paste only AGGREGATE COUNTS AND RULE NAMES, never the offending content. A canary committed as a literal breaks the `local-leaks` CI job (measured), so assemble canaries at test time.
- THE HONESTY RULE, which outranks every convenience: when you report that tests passed, PASTE THE ACTUAL RUNNER OUTPUT including the `N passed` line from a BARE `python3 -m pytest` (the configured `addopts` already supply `-q -n auto -m 'not slow'`; do not add flags). Never fill an `Observed evidence:` field from memory, and never mark a `V-*` from the matching execution checkmark. THREE TRAPS SPECIFIC TO THIS PLAN: a clean `aw sanitize` over the analytics tree means NOTHING, because that walk cannot see gitignored files (probe-verified); the bare suite DESELECTS the leaf-conformance, leak-sanitizer and packaging gates; and `tests/test_packaging.py` asserts only ABSENCE, so it passes with every new asset missing.
- RE-MEASURE EVERY NUMBER IN THIS PLAN. Every figure (135 runs, 1976 files, 272.3 MB, the 120/13/2/0 driver census, one-of-twelve detector coverage, `7 passed` on the packaging test, the 29766-row scale, the baseline `2 failed, 5655 passed`) is a review-time snapshot of a tree that grows with every run. Re-derive them; do not cite them as current.
- RE-LOCATE EVERY CITED SYMBOL BY NAME, not by line number. Find `leak_sanitizer.build_ruleset`/`scan_text`/`_tracked_files`, `lifecycle_fixtures.run_no_network`, `docs_check.check_docs_dir`, and the packaging test's assertions by name; both this Set's siblings and the surrounding modules are actively changing.
- LIFECYCLE MOVE: transition via `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. Do not hand-move the file or hand-write the terminal `Status:`.

SIX STOP CONDITIONS. If you are about to cite `aw sanitize --agent` or `scan_working_tree` as the privacy proof over the analytics tree, STOP: it reports clean by construction, because the tree is gitignored and that walk enumerates tracked files. If a detector-based check has no CONTROL run, STOP: clean and not-looking are otherwise indistinguishable. If you are about to commit a literal canary or any part of the live corpus, STOP: the fixture tree is tracked and scanned by CI. If you are about to declare a numeric performance threshold, STOP: no sibling declared one and this plan originates no behavior. If you are about to write a test that installs a wheel from the network, STOP: an offline install fails on `filelock` and CI's `wheel` job already owns that proof. And if an acceptance case fails because a sibling correctly REFUSES an under-powered analysis, STOP before recording a failure: a documented refusal is a passing outcome, and turning it into a number is the fabrication this Set exists to prevent.
