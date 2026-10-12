# IPD: Give the generated_drift, workflow_disposition and capability_freshness release gates real producers so they can fail

- Date: 2026-10-12
- Kind: child
- Concern: THREE OF THE ELEVEN RELEASE-READINESS GATES CANNOT FAIL, BECAUSE NOTHING EVER COMPUTES THEIR INPUT. `release_readiness.build_report` takes `drift_files`, `undispositioned` and `stale_claims`, each defaulting to `()`, and feeds them to `gate_generated_drift`, `gate_workflow_disposition` and `gate_capability_freshness`, whose passing condition is "the sequence is empty". Measured at authoring HEAD `2600a93e3` by `git grep` over `*.py`, `.github`, `Makefile` and `.pre-commit-config.yaml` excluding `tests/`: `drift_files` and `stale_claims` match ONLY `agent_workflows/release_readiness.py` itself (the gate parameter, its body, the `build_report` parameter and the pass-through), and `undispositioned` additionally matches only the unrelated `migration_complex.ReleaseReviewLedger.undispositioned` method, and driving the gates with no argument returns `passed=True` for all three (F-01). So the report renders `generated_drift PASS`, `workflow_disposition PASS` and `capability_freshness PASS` on every invocation, and those rows mean "nobody looked", indistinguishable from "checked, clean". Sibling plan `wix4xe` (executed) fixed the identical defect for `doc_findings` and explicitly deferred these three to this item (its F-06 and its `## Deferred` row `Carrier: usggph`).
  EACH GATE HAS A REAL PRODUCER IN THIS REPOSITORY ALREADY, SO THIS IS WIRING, NOT INVENTION (F-02, F-03, F-04). Drift: `aw workflow check-generated` already computes it per canonical package through `workflow_loader.load_package`, `workflow_compiler.render_generated_files(compile_workflow(ir))` and `workflow_cli._compute_drift`. Disposition: `migration_inventory.build_inventory(<workflows root>)` already returns an `InventoryResult` whose `findings` list is empty iff every manifest row, lens, persona and the conformance package carries exactly one valid disposition. Capability freshness: `host_capability_registry.HostCapabilityRegistry.query_capability` already refuses to call a claim `supported` when its evidence is missing, expired or a static-migration seed.
  WIRING THE CAPABILITY GATE HONESTLY TURNS IT RED ON THIS TREE, AND THAT IS A TRUE FINDING, NOT A FALSE POSITIVE (F-05). The conformance host matrix `.aw/system/workflows/conformance/tools/host_matrix.json` carries 19 `"supported": true` booleans across 8 hosts. Seeding a registry from it with `migrate_from_static_matrix` and querying each one returns `unverified` with the reason `Unproven claim: static migration seed requires an operator-run live probe.` for all 19. ADR D113 calls that matrix a "seeded" scaffold whose host launches are operator-run, and plan `4fttzq` (executed) says to "Treat it as seed data, not evidence". The gate's own docstring says "documented support must render only proven, unexpired evidence". So 19 unproven support booleans in a tracked file ARE the stale claims this gate exists to catch. The remedy for the data is a separate decision (retire the booleans or record real probe evidence) and is filed as backlog `5gzno3`; this plan wires the gate and must not edit the matrix to make it pass.
  THE OTHER TWO PRODUCERS HAVE FAIL-OPEN AND CRASH MODES THE WIRING MUST CLOSE (F-06, F-07). `migration_inventory.build_inventory` RAISES `InventoryError` for a manifest command with no reviewed family (driven: a manifest row `zzz` gives `InventoryError manifest command 'zzz' has no reviewed family assignment (silent omission)`), and `engine.parse_manifest` raises `SystemExit` (a `BaseException`, which `except Exception` does NOT catch) for a manifest missing its markers or with zero rows. Either would abort `build_report` instead of rendering one failing row, and an unassigned command is precisely an undispositioned workflow. `host_capability_registry.load_host_matrix` silently substitutes a built-in default matrix carrying ZERO `supported` booleans when the path does not exist (driven: 0 claims), so a computed gate pointed at a tree with no matrix would read clean. And `workflow_source.parse_entry` needs PyYAML at build time (D139) and raises `SourceError` without it.
  WHY `followup` AND NO RELEASE GATE IS INVENTED. The item is `- Work-Kind: followup` with no `- Blocks-Release:`; both are preserved. `build_report` has no production caller today (sibling plan `wa64wz` in this Set adds the first one), so no user receives a wrong answer yet; the false PASS rows are latent, which keeps this off `bug` under the AGENTS.md perceptibility test.
- Scope: IN: (1) give `gate_generated_drift`, `gate_workflow_disposition` and `gate_capability_freshness` a `None` sentinel default plus `repo_root`, computing their findings from the repository when nothing is injected and preserving explicit injection, exactly the pattern `gate_docs_checks` already follows; (2) make each computed path FAIL rather than pass or crash when its input tree is missing or its producer raises (including `SystemExit` and `InventoryError`); (3) carry the three sentinels and `repo_root` through `build_report`; (4) extend the two existing synthetic GO fixtures so every existing GO assertion still exercises every gate, weakening no assertion; (5) add a behavioral test file with falsifiability arms shown RED against the pre-change gates. OUT, each with a carrier: editing `host_matrix.json` or adding probe evidence to clear the 19 unproven claims (`5gzno3`); the inert `artifact_manifest` gate, the same defect class on two booleans (`3jkm7y`); a command that renders the report (`wa64wz`, Order 02 of this Set); running the report from CI, release-review or a hook (`uypgvi`); and any edit to `workflow_cli.py`, `migration_inventory.py`, `host_capability_registry.py` or `engine.py`, whose behavior is consumed unchanged.
- Scope-Paths: agent_workflows/release_readiness.py, tests/test_release_readiness.py, tests/test_release_readiness_docs_gate.py, tests/test_release_readiness_producers.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: usggph
- Set: usggph
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: ttg9uz

## Workflow history

- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed. Re-verified at c6bea069b: three gates pass with no argument; 19 unproven host-matrix claims; build_inventory ok with 64 dispositions; 0 live packages; minimal whatnext tree inventories clean; producers spawn no subprocess.
- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog `usggph` in an isolated lane at HEAD `2600a93e3`. The item's claim reproduced exactly (F-01). Each gate already has an in-repo producer (F-02..F-04). Driving them found one true red (19 unproven host-matrix support booleans, F-05, data remedy filed as `5gzno3`) and three fail-open or crash modes the wiring must close (F-06, F-07). The fixture-coupling hazard to existing GO tests is handled in E-06 (F-08). Bare suite baseline: `39 failed, 7180 passed, 2 skipped`, all failures in the nonsurveyable-root / explicit-dir / commit-trailer families and unrelated (F-09).
- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make the `generated_drift`, `workflow_disposition` and `capability_freshness` rows of the release-readiness report reflect the real state of the repository, so each can fail, and so a missing input or a crashing producer fails its row instead of reading as clean or aborting the report. Leave tests that go red if any of the three becomes inert again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before changing anything

- [ ] E-01 Re-measure the three inert gates and their producers at the executing HEAD, and record the transcript, so every later item acts on current fact.
  - Depends on: none
  - Expected outcome: one pasted transcript proving, by DRIVING the code: (a) `git grep -n -e drift_files -e undispositioned -e stale_claims -- '*.py' ':!tests/'` matches only `agent_workflows/release_readiness.py` (plus the unrelated `migration_complex.ReleaseReviewLedger.undispositioned` method, which is a different symbol); (b) `gate_generated_drift()`, `gate_workflow_disposition()` and `gate_capability_freshness()` with no argument each return `passed=True`; (c) the live producers' current answers: the count of `.aw/system/workflows/*/workflow.yaml` packages (0 at authoring), `migration_inventory.build_inventory(Path(".aw/system/workflows"))` `ok` and disposition count (`True`, 64 at authoring), and the number of host-matrix `supported: true` booleans the registry does not prove (19 at authoring). IF (b) already returns `passed=False` for any gate, another plan has wired it; stop and reconcile rather than writing it twice. Different counts in (c) are NOT a stop condition: record them and use them in V-05.
  - Execution state: pending

### Task group 2: give each gate a real input

- [ ] E-02 Make `release_readiness.gate_generated_drift` compute its drift set from the repository's canonical workflow packages when the caller injects nothing.
  - Depends on: E-01
  - Expected outcome: signature `gate_generated_drift(drift_files: Optional[Sequence[str]] = None, repo_root: Optional[Path] = None)`. Explicit injection (including `[]`) behaves exactly as today. When `None`: resolve `root = repo_root or _repo_root()`; if `root / ".aw/system/workflows"` is not a directory, FAIL with a detail naming the relative path and `evidence={"missing": True, "path": ".aw/system/workflows", "drift_files": []}`; otherwise, for each `<root>/.aw/system/workflows/*/workflow.yaml` (sorted), call `workflow_loader.load_package(pkg_dir)`. A failed load is a finding (`"<pkg>: load failed: <code>"`). A successful load is diffed with `workflow_cli._compute_drift(Path(ir["source_root"]), workflow_compiler.render_generated_files(workflow_compiler.compile_workflow(ir)))`, each `(kind, rel)` becoming `"<pkg>/<rel>: <kind>"`. Reuse those exact functions so the gate and `aw workflow check-generated` cannot disagree (GUIDING_PRINCIPLES P8). Import them inside the function, following `gate_changelog_versioning`'s local-import precedent. Importing the private `_compute_drift` is deliberate: it is the single drift definition, and `workflow_cli.py` is out of scope. Wrap the computed path in `try/except Exception` so a `SourceError` (no PyYAML) or other producer error FAILS with `docs`-gate-style detail `generated drift check could not run: <ExcType>` and `evidence["error"]`. ZERO packages PASSES, with the distinct detail `no canonical workflow packages to check` and `evidence={"packages_checked": 0, "drift_files": []}` (OQ-01). Every computed result records `packages_checked`. Gate `name` and the `drift_files` evidence key are unchanged. Every path in evidence is repo-relative.
  - Execution state: pending

- [ ] E-03 Make `release_readiness.gate_workflow_disposition` compute its undispositioned set from the disposition inventory when the caller injects nothing.
  - Depends on: E-01
  - Expected outcome: signature `gate_workflow_disposition(undispositioned: Optional[Sequence[str]] = None, repo_root: Optional[Path] = None)`. Explicit injection unchanged. When `None`: a missing `<root>/.aw/system/workflows` FAILS as in E-02. Otherwise call `migration_inventory.build_inventory(root / ".aw/system/workflows")` and use `[str(f) for f in result.findings]` as the undispositioned list, with `evidence["dispositions"] = len(result.dispositions)`. `InventoryError` is itself an undispositioned workflow (the fail-closed "no reviewed family assignment" refusal), so catch it and FAIL with its message as the single finding. Catch `SystemExit` EXPLICITLY (it is a `BaseException`; `engine.parse_manifest` raises it for missing manifest markers or zero rows) and any other `Exception`, and FAIL with `workflow disposition check could not run: <ExcType>`. Do NOT catch `KeyboardInterrupt`. Gate `name` and the `undispositioned` evidence key are unchanged.
  - Execution state: pending

- [ ] E-04 Make `release_readiness.gate_capability_freshness` compute its stale-claim set from the conformance host matrix when the caller injects nothing.
  - Depends on: E-01
  - Expected outcome: signature `gate_capability_freshness(stale_claims: Optional[Sequence[str]] = None, repo_root: Optional[Path] = None)` (no `now` parameter: nothing persists evidence, so no caller or arm could exercise expiry, and `query_capability` already defaults `now` to the current time). Explicit injection unchanged. When `None`: resolve `matrix = root / ".aw/system/workflows/conformance/tools/host_matrix.json"` (NOT the package-relative `DEFAULT_MATRIX_PATH`, so `repo_root` is honored). If it is not a file, FAIL with `capability matrix missing: <relpath>` and `evidence["missing"] = True`, because `load_host_matrix` would otherwise substitute a built-in matrix with zero claims and read clean (F-07). Otherwise load it with `host_capability_registry.load_host_matrix(matrix)`, build a `HostCapabilityRegistry`, seed it with `migrate_from_static_matrix(data)`, and for every `(host, feature)` whose matrix entry is a dict with `"supported": true` (sorted), call `query_capability(host=host, exact_version="1.0.0", feature=feature)`. `"1.0.0"` is `migrate_from_static_matrix`'s `default_version`, so the query finds the seeded record. Each claim whose evaluation `is_supported` is False becomes `"<host>:<feature>: <first reason>"`. Record `evidence["claims_checked"]`. A JSON or other producer error FAILS with `capability freshness check could not run: <ExcType>`. Do not special-case the live 19: they are the true finding (F-05) and are carried by `5gzno3`. Gate `name` and the `stale_claims` evidence key are unchanged.
  - Execution state: pending

- [ ] E-05 Carry the three sentinels and `repo_root` through `release_readiness.build_report`.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: `build_report`'s `drift_files`, `undispositioned` and `stale_claims` default to `None` (annotated `Optional[Sequence[str]]`) instead of `()`, and the three gates receive `repo_root=repo_root` exactly as `gate_docs_checks` already does. The parameters stay keyword-only and keep their positions; every other default is unchanged. Update the module docstring's gate list only if a description became false.
  - Execution state: pending

### Task group 3: keep the existing GO tests honest, then make inertness fail

- [ ] E-06 Extend the two existing synthetic GO fixtures so the existing GO assertions keep exercising every gate after E-05.
  - Depends on: E-05
  - Expected outcome: after E-05, `build_report` against `tests/test_release_readiness.py::_build_synthetic_root` and `tests/test_release_readiness_docs_gate.py::_setup_go_fixture` would FAIL the three newly computed gates, because neither synthetic tree has `.aw/system/workflows` (F-08). Extend BOTH helpers to also write a minimal valid workflows tree: `.aw/system/workflows/index.md` with the manifest markers and ONE manifest row whose command is in `migration_inventory._COMMAND_FAMILY` (for example `whatnext`, which needs no alias handling), `.aw/system/workflows/conformance/operator-protocol.md`, and `.aw/system/workflows/conformance/tools/host_matrix.json` containing hosts with NO `"supported": true` booleans. Put the shared tree-writing in ONE helper in `tests/test_release_readiness_producers.py`, imported by both files, rather than copying it. Change NO assertion: every existing test that asserted GO, `failing_gates() == []` or `failing_gates() == ["docs_checks"]` must still assert exactly that. `test_allowlist_recorder_decision_path` (which replaces `subprocess.run` and asserts only `git describe`/`git ls-files` are spawned) must pass UNMODIFIED: it is the guard that none of the three new producers shells out (review probe: `build_inventory` and the capability path spawn nothing under that recorder). Pending plan `514wv3` (Set `r4a4ab`) also edits `tests/test_release_readiness.py` and builds on `_build_synthetic_root`, so extending that helper (not adding a new one beside it) keeps its tests correct in either execution order.
  - Execution state: pending

- [ ] E-07 Add `tests/test_release_readiness_producers.py` driving each computed gate over real `tmp_path` trees, with a falsifiability arm per gate shown RED against the pre-change gates.
  - Depends on: E-06
  - Expected outcome: every assertion is BEHAVIORAL (calls the real gate or `build_report` over a `tmp_path` tree and asserts returned fields; no source reading, `inspect`, `ast` or symbol census, per AGENTS.md and P16; no arm reads this repository's live `.aw/`). Minimum arms. DRIFT: (a) a canonical package copied from `tests/fixtures/workflow-src/plan-review` with NO `_generated/` fails, listing `missing` entries; (b) the same package after writing the compiler's own output passes with `packages_checked == 1`; (c) after hand-editing one generated file it fails naming `changed`; (d) zero packages passes with `no canonical workflow packages to check`; (e) a missing workflows dir fails with `missing`. DISPOSITION: (f) the minimal valid tree passes; (g) a deleted `conformance/operator-protocol.md` fails with that finding; (h) a manifest row with an unassigned command fails (InventoryError path) and does not raise; (i) an `index.md` with no markers fails with `could not run: SystemExit` and does not raise; (i2) a workflows dir with no `index.md` fails with `could not run: FileNotFoundError` and does not raise. CAPABILITY: (j) a matrix with one `"supported": true` fails naming `<host>:<feature>`; (k) a matrix with none passes with `claims_checked == 0`; (l) a missing matrix fails with `missing` (the F-07 fail-open arm). INJECTION: (m) for each gate, explicit `[]` passes and a one-element list fails without touching the filesystem (use a `tmp_path` root with no tree). END TO END: (n) `build_report(..., run_subprocess_gates=False)` over the E-06 GO tree is GO, then adding one `"supported": true` makes it NO-GO with `failing_gates() == ["capability_freshness"]`. Every synthetic tree sets `GIT_CEILING_DIRECTORIES` (the PR-002 lesson recorded in plan `dyiasf`). Mark the PyYAML-dependent drift arms with `pytest.importorskip("yaml")`. Arms (a), (g), (h), (j), (l) and (n) must be shown RED against the pre-E-02 module, since a gate that cannot fail is the defect. A gate-level arm calling `gate_*(repo_root=...)` is red against the pre-change module only by `TypeError` (the parameter does not exist yet), which proves the signature changed, not that the gate can fail. So ALSO add one `build_report(..., repo_root=tree, run_subprocess_gates=False)` arm per gate (o: drift, a package with no `_generated/`; p: disposition, deleted `conformance/operator-protocol.md`; q: capability, one `"supported": true`), each asserting that gate's name is in `failing_gates()`; these must be red against the pre-change module by `AssertionError` (the pre-change `build_report` accepts `repo_root` and reports the gate PASS).
  - Execution state: pending

- [ ] E-08 Run the targeted files and the bare suite, comparing failures by name against a baseline taken at the execution base.
  - Depends on: E-07
  - Expected outcome: `python3 -m pytest -o addopts="" -q tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py tests/test_release_readiness_producers.py tests/test_release_readiness_child_pin.py` is all green; bare `python3 -m pytest` shows no failure absent from the base-commit baseline (any newly red node is re-run alone at the base before being called pre-existing).
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL or quoted string, never a bare line number (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- A gate needing repository state takes `repo_root: Optional[Path] = None`, resolves `root = repo_root or _repo_root()`, and imports its producer inside the function: `gate_changelog_versioning` and `gate_docs_checks` both do this. `gate_docs_checks` (plan `wix4xe`) is the exact template: `None` sentinel computes, explicit injection bypasses, a missing tree and a raising checker each FAIL with distinct details, evidence paths are relative.
- Tests assert outcomes, never code structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16), and must be mutation-sensitive (P16: "a test is only valid if breaking the underlying behavior makes the test fail").
- Synthetic trees must set `GIT_CEILING_DIRECTORIES`, or `versioning._git_describe` walks up into the enclosing checkout (plan `dyiasf` PR-002).
- PyYAML is a build-time-only dependency in the `test` extra (D139; `pyproject.toml` comment "PyYAML IS IN THE TEST EXTRA"); runtime import paths must not import `yaml` at module load.
- The suite is run BARE as `python3 -m pytest`; no `-n0`, extra `-q` or `-p no:randomly` (AGENTS.md repo-local contract).
- `- Item-Dependencies:` uses `executed:<id6>`; the runner re-checks edges at dispatch.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The item's claim reproduces: the three parameters are computed by nothing and the three gates pass vacuously. | At `2600a93e3`, `git grep -n <name> -- '*.py' '.github' 'Makefile' '.pre-commit-config.yaml'` minus `tests/`: `drift_files` and `stale_claims` hit only `agent_workflows/release_readiness.py`; `undispositioned` also hits `migration_complex.ReleaseReviewLedger.undispositioned`, a different symbol that is not wired to the gate. Driven: `gate_generated_drift().passed, gate_workflow_disposition().passed, gate_capability_freshness().passed` -> `True True True`. `build_report(suite_passed=True, run_subprocess_gates=False).render()` shows all three `PASS`. |
| F-02 | A drift producer exists and is the CLI's own. | `workflow_cli._run_check_generated` calls `workflow_loader.load_package`, `workflow_compiler.render_generated_files(workflow_compiler.compile_workflow(result.ir))` and `workflow_cli._compute_drift`. Driven over a copy of `tests/fixtures/workflow-src/plan-review`: 7 `missing` entries with no `_generated/`, `[]` after writing the compiler output, `[('changed', '_generated/prompt.md')]` after a hand edit. The live tree has ZERO `.aw/system/workflows/*/workflow.yaml` packages. |
| F-03 | A disposition producer exists and is clean on the live tree. | `migration_inventory.build_inventory(Path(".aw/system/workflows"))` -> `ok=True`, 64 dispositions, `findings=[]`, in 0.09s. Over a synthetic tree, deleting `conformance/operator-protocol.md` gives `['conformance entry file missing: conformance/operator-protocol.md']`. |
| F-04 | A freshness evaluator exists. | `HostCapabilityRegistry.query_capability` returns `unverified` for a missing, expired (`EvidenceRecord.is_expired`, `DEFAULT_EVIDENCE_TTL_DAYS = 90`) or `SOURCE_STATIC_MIGRATION` record. Nothing in `agent_workflows/` calls `save_to_json`/`load_from_json` (`git grep`), so there is no persisted evidence store; the only tracked claim source is the host matrix. |
| F-05 | Wired honestly, the capability gate is RED on the live tree, and that is correct. | `host_matrix.json` has 19 `"supported": true` across 8 hosts; `migrate_from_static_matrix` then `query_capability(..., exact_version="1.0.0")` gives `is_supported=False` for all 19, reason `Unproven claim: static migration seed requires an operator-run live probe.`. D113 ("seeded host matrix", "host launches are an operator-run protocol"); plan `4fttzq` ("Treat it as seed data, not evidence"); research `20260821-awoptimize-01-y1eb0q` ("Consumers may misread scaffold data as capability evidence"). The data remedy is filed as backlog `5gzno3`. |
| F-06 | The disposition producer raises instead of reporting, in two ways. | Driven: a manifest row `zzz` -> `InventoryError manifest command 'zzz' has no reviewed family assignment (silent omission)`. `index.md` with no markers -> `SystemExit index.md is missing the manifest markers ...`; an empty manifest -> `SystemExit No workflows found in the index.md manifest.` `SystemExit` derives from `BaseException`. |
| F-07 | The capability producer fails open on a missing matrix. | `load_host_matrix(<nonexistent path>)` returns a built-in dict; counting its `"supported": true` gives `0`. |
| F-08 | Wiring breaks three existing GO-asserting tests unless their fixtures grow. | `tests/test_release_readiness.py::_build_synthetic_root` writes only `CHANGELOG.md`, `.aw/system/VERSION` and `docs/`; `tests/test_release_readiness_docs_gate.py::_setup_go_fixture` the same. Three GO-asserting tests build reports over them: `test_build_report_clean_tree_is_go`, `test_allowlist_recorder_decision_path` and `test_end_to_end_contrast_pair` (asserts `failing_gates() == []` then `== ["docs_checks"]`). `test_checker_exception_handled_cleanly`, `test_json_dumps_with_doc_finding_evidence` and the two forced-NO-GO tests assert only membership or serialization and stay correct either way. Pending `514wv3` also builds on `_build_synthetic_root`. |
| F-09 | The baseline is not green, for unrelated reasons, so validation compares failure NAMES. | Bare `python3 -m pytest` at `2600a93e3`: `39 failed, 7180 passed, 2 skipped` in 222s, in `test_no_project_exit_is_cannot_run` (12), `test_explicit_dir_non_project` (6), `test_validator_nonsurveyable_dir` (5), `test_nonsurveyable_root_refusal` (4), `test_commit_run_trailers_env` (3), `test_read_class_callers_refuse` (3), `test_explicit_dir_subdir_resolution` (2), and one each in `test_agent_surface_conformance`, `test_attention`, `test_finalize_sendback`, `test_nv_backend_args_climb`. No `release_readiness` test fails: `42 passed` across the three existing files. |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the inert gates and the live producers' answers.
2. E-02, E-03 and E-04 each give one gate a `None` sentinel, `repo_root`, a computed path reusing the existing producer, and fail-closed handling of a missing tree or a raising producer.
3. E-05 threads the sentinels and `repo_root` through `build_report`.
4. E-06 grows the two existing GO fixtures (one shared helper) so no existing assertion changes.
5. E-07 adds `tests/test_release_readiness_producers.py`, with its falsifiability arms shown red first.
6. E-08 runs the targeted files and the bare suite against the baseline.

## Deferred / out of scope (with reason)

- Clearing the 19 unproven `supported: true` booleans in `host_matrix.json` (retire them or record live probe evidence). This is a data and policy decision about what the toolkit claims, separate from wiring the gate, and editing the matrix here would make the new gate pass by changing what it measures.
  - Carrier: 5gzno3
- `gate_artifact_manifest` is inert in the same way: `build_report` defaults `manifest_present`/`manifest_consistent` to `True` and nothing computes either. Outside the item's three named parameters, and it needs a definition of "the release artifact manifest" that the repo does not state.
  - Carrier: 3jkm7y
- A command that renders the report. Sequenced after this plan so it never displays the vacuous rows.
  - Carrier: wa64wz
- Running the report from release-review, CI or a hook. A process decision about what gates a release.
  - Carrier: uypgvi

## Scope check

- Over-scope: none. `release_readiness.py` carries the three gates and `build_report`; the two existing test files need only their fixture helpers grown (E-06); the new test file is the guard. No producer module is edited.
- Under-scope: the live report stays NO-GO after this plan (residual risk unsigned, `ipd_lint` red per `r4a4ab`, and now `capability_freshness` red per F-05). That is the honest verdict, with each cause carried.

## Required tests / validation

Bare `python3 -m pytest`, failures compared BY NAME against a base-commit baseline (F-09). Plus the four release-readiness test files passing under `-o addopts=""`, with the E-07 falsifiability arms shown RED against the pre-change module first.

## Spec / documentation sync

N/A, with reason. No `.spec.md` governs `release_readiness`. Gate names, passing conditions and evidence keys are unchanged; the gates now compute what their docstrings already say they evaluate. User-facing docs are updated by `wa64wz`, the plan that adds a way for a user to see the report.

## Open questions

### OQ-01: should zero canonical workflow packages pass or fail `generated_drift`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as PASS with a distinct detail and `packages_checked: 0`. Drift means generated output disagreeing with its source; with no canonical package there is no generated output, so "no drift" is true and not vacuous, unlike today's pass, which never looks. A missing workflows directory still FAILS, so "could not check" stays distinguishable from "nothing to check". Failing on zero packages would make every release NO-GO until the workflow-package migration ships, which is a scope decision this gate should not force. Reversible by a one-line change if the maintainer prefers fail-closed.

### OQ-02: is the host matrix the right source of capability claims, given it is seed data?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as YES on repository evidence (F-04, F-05). It is the only tracked file asserting host support (nothing persists registry evidence). The gate's purpose is that documented support must rest on proven, unexpired evidence, and D113 plus `4fttzq` say these booleans are not evidence. Treating them as claims makes the gate report what is true. Ignoring them would bring back the vacuous pass. What to do with the booleans is carried by `5gzno3`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the execution HEAD sha and the full E-01 transcript: the `git grep` output, the three no-argument gate results showing `passed=True`, the live package count, the `build_inventory` `ok`/count, and the unproven-claim count. Any gate already `passed=False` with no argument makes this FAIL (stop and reconcile).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `git diff` hunk for `gate_generated_drift` showing the sentinel, `repo_root`, the local imports of `workflow_loader`, `workflow_compiler` and `workflow_cli._compute_drift`, and the missing-tree and `except Exception` branches. Paste a driven probe (code path: `gate_generated_drift(repo_root=tmp)`, created by E-02) printing `passed`, `detail` and `evidence` for: a fixture package with no `_generated/` (fail, `missing` entries), after writing compiler output (pass, `packages_checked: 1`), zero packages (pass, `no canonical workflow packages to check`), and no workflows dir (fail, `missing: True`). Confirm no absolute path appears in any printed evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `git diff` hunk for `gate_workflow_disposition`, showing `except SystemExit` and the `InventoryError` branch. Paste a driven probe (code path: `gate_workflow_disposition(repo_root=tmp)`, created by E-03) printing results for: the minimal valid tree (pass, `dispositions` count), a deleted `conformance/operator-protocol.md` (fail, that finding), an unassigned manifest command (fail, the `no reviewed family assignment` message, no exception escapes), and `index.md` with no markers (fail, `could not run: SystemExit`, no exception escapes).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `git diff` hunk for `gate_capability_freshness`, showing the root-relative matrix path, the missing-file branch and the `query_capability` loop. Paste a driven probe (code path: `gate_capability_freshness(repo_root=tmp)`, created by E-04) printing results for: a matrix with one `"supported": true` (fail, `<host>:<feature>: Unproven claim...`), a matrix with none (pass, `claims_checked: 0`), and no matrix file (fail, `missing: True`). Also paste `gate_capability_freshness()` against the real repo, showing `passed=False` with the stale-claim count equal to E-01's.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `inspect.signature(release_readiness.build_report)` showing `drift_files`, `undispositioned` and `stale_claims` defaulting to `None`, with every other default as in plan `wix4xe` V-05's dump. Paste `build_report(suite_passed=True, residual_risk_signed=True, residual_risk_signer="x", run_subprocess_gates=False).to_dict()["gates"]` against the REAL repo, filtered to the three gates, showing each now carries computed evidence (`packages_checked`, `dispositions`, `claims_checked`), with `capability_freshness` failing on the E-01 count.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `git diff tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py` and show that ONLY fixture helpers or imports changed and no `assert` line was removed or altered. Paste `python3 -m pytest -o addopts="" -q tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py` green AFTER E-05 and E-06. Also paste the same run with E-05 applied but the E-06 fixture growth absent (run in a scratch `git worktree` holding the post-E-05 module and the base test files, then removed), showing the GO tests going red. That proves the fixtures now feed the new producers rather than being bypassed.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: THE RED RUN COMES FIRST: paste `python3 -m pytest -o addopts="" -q tests/test_release_readiness_producers.py` against the pre-E-02 `release_readiness.py`, showing arms (a), (g), (h), (j), (l), (n), (o), (p) and (q) failing, with (n), (o), (p) and (q) failing by `AssertionError` (not `TypeError`); paste the short failure reason per arm. Do NOT use `git stash` for this in the shared checkout: run the red pass in a scratch `git worktree add <tmp> <base>` with the new test file and the E-06 fixture helper copied in, then remove that worktree. Then paste the green run with test names (`-v`). Paste `git grep -n -E 'getsource|import ast|ast\.parse|import inspect|read_text\(.*release_readiness' tests/test_release_readiness_producers.py` returning nothing, and `git grep -n 'Path(".aw' tests/test_release_readiness_producers.py` showing no read of the live tree.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the targeted four-file run's summary line (`N passed`, zero failed), the base-commit bare-suite failure list, and the post-change bare-suite summary line plus failure list, with a by-name diff of the two lists showing no new failure (any difference re-run alone at the base, output pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval (`- Status: approved`) before execution.

EXECUTION CONTRACT. All open questions (OQ-01, OQ-02) are resolved; none blocks. Commit only the four declared paths plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, `-a`, `--no-verify`, `git stash` or a push. Verify the staged set before committing (shared checkout). Paste actual test output; never claim a run that was not performed.

POST-GATE LIFECYCLE. Do not mark this plan `executed` until `aw ipd lint --phase pre-transition` conforms and all eight `V-*` items carry pasted evidence with `Result: pass`. Under `aw oc run`/`aw agy run` the runner owns begin/finalize; by hand, use `aw ipd finalize`, never a hand `git mv`.

TWO THINGS AN EXECUTOR MUST NOT DO, each of which would look like finishing the work. FIRST, do not edit `host_matrix.json`, or special-case its claims, to make `capability_freshness` pass on the live tree: its red is the true finding (F-05) and `5gzno3` owns it. SECOND, do not weaken any existing GO assertion to absorb the newly computed gates; grow the fixture (E-06).
