# IPD: Retire unproven supported booleans from the conformance host matrix

- Date: 2026-10-14
- Kind: child
- Concern: NINETEEN UNPROVEN `supported: true` BOOLEANS IN `.aw/system/workflows/conformance/tools/host_matrix.json` CAUSE `capability_freshness` TO BE THE SOLE REMAINING LIVE FAILURE OF `aw releases readiness` ON THIS REPOSITORY. Both sibling plans in Set `usggph` (`ttg9uz` and `wa64wz`) are now `executed`. Measured at authoring HEAD `e2b5c0555` (and re-measured at review HEAD `6a412554d`): `.aw/system/workflows/conformance/tools/host_matrix.json` defines 8 hosts (`antigravity`, `claude_code`, `codex`, `copilot`, `cursor`, `gemini_cli`, `kiro`, `opencode`), each with 3 tier dicts (`t1_policy`, `t2_layout`, `t3_global`) for 24 tier entries total, of which 19 carry `"supported": true` (`antigravity:t1_policy`, `antigravity:t2_layout`, `antigravity:t3_global`, `claude_code:t1_policy`, `claude_code:t2_layout`, `claude_code:t3_global`, `codex:t2_layout`, `codex:t3_global`, `copilot:t2_layout`, `copilot:t3_global`, `cursor:t2_layout`, `cursor:t3_global`, `gemini_cli:t1_policy`, `gemini_cli:t2_layout`, `gemini_cli:t3_global`, `kiro:t2_layout`, `kiro:t3_global`, `opencode:t2_layout`, `opencode:t3_global`) and 5 carry `"supported": false` (`codex:t1_policy`, `copilot:t1_policy`, `cursor:t1_policy`, `kiro:t1_policy`, `opencode:t1_policy`). Driving `release_readiness.gate_capability_freshness()` on the repository root returns `GateResult(name='capability_freshness', passed=False, detail='19 stale claim(s)', evidence={'stale_claims': [...], 'claims_checked': 19})`, where each of the 19 `supported: true` entries fails `HostCapabilityRegistry.query_capability` (`is_supported is False`) and is recorded as the string `"<host>:<tier>: Unproven claim: static migration seed requires an operator-run live probe."`. Driving `python3 -m agent_workflows releases readiness --suite-passed --residual-risk-signer qa` exits `1` (`Verdict: NO-GO`), with `capability_freshness` as the only failing gate of all 11 (F-01).
  WHY RETIRE THE `supported` BOOLEANS RATHER THAN RECORD PROBE EVIDENCE IN GIT (F-02, F-03, OQ-01). Backlog item `5gzno3` asks to *"Either record real probe evidence for the 19 `supported: true` host/tier claims in `.aw/system/workflows/conformance/tools/host_matrix.json` or retire the claims that are not yet backed by probes, so `gate_capability_freshness()` reflects verified support."* Repository architecture and prior decisions resolve this to retiring the `"supported"` booleans from `host_matrix.json`:
  1. `DECISIONS.md` D113 (`Phase 0 conformance harness for host delivery (deterministic scaffolder + operator-run protocol)`) defines `host_matrix.json` as a "seeded host matrix" for a deterministic scaffolder whose host invocations are an operator-run protocol, not recorded proof.
  2. Research `20260821-awoptimize-01-y1eb0q` and executed plan `4fttzq` (`Host capability evidence registry and isolated probes`) ruled: *"Replace boolean host support claims with versioned evidence that defaults to unverified"* and *"The static host matrix contains unproven support booleans + command templates. | Treat it as seed data, not evidence; migrate to versioned claims that default to `unverified`."* `host_capability_registry.load_host_matrix`'s built-in fallback dict (used only when the file is absent) already omits `"supported"` from every host entry. `.aw/system/workflows/conformance/tools/host_matrix.json` lay outside `4fttzq`'s scope fence and kept the legacy Phase 0 seed booleans (F-02).
  3. Mechanically, `release_readiness.gate_capability_freshness` instantiates a fresh `HostCapabilityRegistry()`, seeds it solely from `host_matrix.json` via `migrate_from_static_matrix(data)` (which tags every migrated entry `source_type=SOURCE_STATIC_MIGRATION` and `result=STATUS_UNVERIFIED`), and calls `reg.query_capability(host=host, exact_version="1.0.0", feature=feat)` only on `(host, feat)` pairs where `feat_val.get("supported") is True`. Nothing in the repository persists or loads a separate capability evidence store on disk (`ttg9uz` F-04), any committed probe timestamp would expire after `DEFAULT_EVIDENCE_TTL_DAYS = 90` days, and the 8 external proprietary host CLIs/IDEs cannot be live-probed in a repository checkout (F-03).
  WHY REMOVE `"supported"` FROM ALL 24 TIER DICTS RATHER THAN FLIPPING `true` TO `false` (F-04, OQ-02). Setting `"supported": false` on `t2_layout` and `t3_global` would replace an unproven positive claim with a false negative claim. `HostCapabilityRegistry.migrate_from_static_matrix` checks `if not feat_key.startswith("t") or not isinstance(feat_val, dict): continue` and never reads `"supported"`. Neither `conformance_harness.py`, nor `host_capability_registry.py` (`scaffold_probe_fixture`, `render_probe_commands`), nor `lifecycle_fixtures.run_multi_host_discovery` reads `"supported"`. Removing the key from all 24 dicts while keeping `t1_policy` (`mechanism`, `notes`), `t2_layout` (`preferred_path`), and `t3_global` (`global_path`) intact preserves all 24 migrated records, all 8 hosts, and all `T1`/`T2`/`T3` probe scaffolding and command rendering, while `gate_capability_freshness()` returns `passed=True, detail='no stale capability claims', evidence={'stale_claims': [], 'claims_checked': 0}` (F-04).
  WHY `followup` AND NO RELEASE GATE IS INVENTED. Backlog item `5gzno3` carries `- Work-Kind: followup`, `- Priority: medium`, and no `- Blocks-Release:`; all three are preserved without inventing a release gate.
- Scope: IN: (1) add behavioral and falsifiability tests in `tests/test_host_capability_registry.py` (shown RED against the pre-change matrix first) verifying that the shipped default host matrix (`host_capability_registry.DEFAULT_MATRIX_PATH`) exists, carries all 8 hosts and 24 tier dicts, contains zero `"supported"` keys, migrates all 24 `(host, tier)` entries to `STATUS_UNVERIFIED` / `SOURCE_STATIC_MIGRATION`, scaffolds and renders `T1`/`T2`/`T3` probes for every host, and passes `release_readiness.gate_capability_freshness()`, while a copy with one `"supported": true` seed fails `gate_capability_freshness(repo_root=...)`; (2) remove the `"supported"` key from all 24 tier entries in `.aw/system/workflows/conformance/tools/host_matrix.json`, preserving every other field; (3) one `CHANGELOG.md` `- Fixed:` bullet, because the matrix ships in the wheel. OUT: modifying `agent_workflows/host_capability_registry.py`, `agent_workflows/release_readiness.py`, or `.aw/system/workflows/conformance/tools/conformance_harness.py`; building an on-disk persistence format for live probe records; wiring `gate_artifact_manifest` (`3jkm7y` / `w9l8ph`); and running `aw releases readiness` from CI or `release-review` (`uypgvi`).
- Scope-Paths: .aw/system/workflows/conformance/tools/host_matrix.json, tests/test_host_capability_registry.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: 5gzno3
- Set: 5gzno3
- Order: 1
- Highest E allocated: 05
- Author: antigravity
- Id: 8ru81x
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): plan-review applied revisions
- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
- 2026-10-14 to-review (aw set): Authored from backlog 5gzno3 at HEAD e2b5c0555: retire unproven supported booleans from .aw/system/workflows/conformance/tools/host_matrix.json and guard with behavioral tests.

- 2026-10-14 draft (antigravity): created.

## Goal

Retire the unproven Phase 0 `"supported"` boolean claims from `.aw/system/workflows/conformance/tools/host_matrix.json` so the shipped matrix serves purely as structural host/tier seed data that migrates to `unverified` in `HostCapabilityRegistry`, clearing the 19 stale-claim failures in `release_readiness.gate_capability_freshness()` while preserving all 24 host/tier registrations and probe-harness consumers.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before changing anything

- [ ] E-01 Re-measure the live `.aw/system/workflows/conformance/tools/host_matrix.json` boolean claims, `HostCapabilityRegistry.migrate_from_static_matrix`, and `release_readiness.gate_capability_freshness` at the executing HEAD before changing any file.
  - Depends on: none
  - Expected outcome: one pasted transcript proving, by driving the code on the repository root: (a) `host_capability_registry.load_host_matrix(host_capability_registry.DEFAULT_MATRIX_PATH)` loads 8 hosts and 24 `t*` tier dicts, of which 19 carry `"supported": True` and 5 carry `"supported": False`; (b) `HostCapabilityRegistry().migrate_from_static_matrix(data)` returns `24` and every record has `result == "unverified"` and `source_type == "static_migration"` (the values of `hcr.STATUS_UNVERIFIED` and `hcr.SOURCE_STATIC_MIGRATION`); and (c) `release_readiness.gate_capability_freshness()` returns `passed=False`, `detail == "19 stale claim(s)"`, and `evidence["claims_checked"] == 19`, with all 19 `stale_claims` entries being STRINGS of the form `"<host>:<tier>: Unproven claim: static migration seed requires an operator-run live probe."`. If (a) already shows 0 `"supported"` keys and (c) already returns `passed=True`, stop and reconcile rather than repeating the change.
  - Execution state: pending

### Task group 2: add falsifiable behavioral tests and retire the unproven booleans

- [ ] E-02 Add behavioral and falsifiability tests in `tests/test_host_capability_registry.py` for the shipped default host matrix and `release_readiness.gate_capability_freshness`, and verify they fail (RED) before editing `.aw/system/workflows/conformance/tools/host_matrix.json`.
  - Depends on: E-01
  - Expected outcome: add a `unittest.TestCase` class `TestShippedHostMatrixAndFreshnessGate` in `tests/test_host_capability_registry.py`. The module is `unittest`-based, so use `tempfile.TemporaryDirectory()`, not pytest's `tmp_path`. Exercise real functions and data, and never inspect `.py` source via `inspect`, `ast`, or regex. Add two test methods (names are non-binding pointers):
    - `(t1)` shipped-matrix shape and migration:
      - First assert `hcr.DEFAULT_MATRIX_PATH.is_file()`, so the built-in fallback dict in `load_host_matrix` (which already lacks `"supported"`) cannot make the test pass vacuously. Then load `data = hcr.load_host_matrix(hcr.DEFAULT_MATRIX_PATH)`.
      - Assert the host set equals `{"antigravity", "claude_code", "codex", "copilot", "cursor", "gemini_cli", "kiro", "opencode"}`.
      - Assert every host defines `display_name`, `t1_policy` (non-empty `mechanism`), `t2_layout` (non-empty `preferred_path`), `t3_global` (non-empty `global_path`), `command_template`, and `diagnostic_commands`.
      - Assert `[(h, k) for h, cfg in data["hosts"].items() for k, v in cfg.items() if k.startswith("t") and isinstance(v, dict) and "supported" in v] == []`.
      - Assert `reg.migrate_from_static_matrix(data) == 24`. For every `(host, tier)`, assert `reg.query_capability(host=h, exact_version="1.0.0", feature=tier).is_supported is False` and that the stored record (`reg.get_record(...)` or equivalent public accessor) has `result == hcr.STATUS_UNVERIFIED` and `source_type == hcr.SOURCE_STATIC_MIGRATION`.
      - For every host and `tier in ("T1", "T2", "T3")` (`subTest`), in a fresh `tempfile.TemporaryDirectory()` each, assert `fixture = hcr.scaffold_probe_fixture(base, host, "1.0.0", tier=tier)` and `hcr.render_probe_commands(host, "1.0.0", tier, base, fixture.nonce)` return without raising.
    - `(t2)` freshness gate on the shipped matrix, with a falsifiability control:
      - Call `release_readiness.gate_capability_freshness(repo_root=REPO)`, where `REPO = Path(__file__).resolve().parent.parent`. Assert `passed is True`, `detail == "no stale capability claims"`, and `evidence == {"stale_claims": [], "claims_checked": 0}`.
      - Then, in a `tempfile.TemporaryDirectory()` `t`, write a copy of `data` to `t / ".aw/system/workflows/conformance/tools/host_matrix.json"` with `copy["hosts"]["antigravity"]["t2_layout"]["supported"] = True`. Assert `gate_capability_freshness(repo_root=t)` returns `passed is False`, `evidence["claims_checked"] == 1`, and `evidence["stale_claims"][0].startswith("antigravity:t2_layout:")`. The entries are strings, not dicts.
    Run `python3 -m pytest -o addopts="" -v tests/test_host_capability_registry.py -k TestShippedHostMatrixAndFreshnessGate` against the pre-E-03 matrix. Both methods must FAIL with `AssertionError`: t1 on the non-empty `"supported"` list, and t2 on `passed is True` with `19 stale claim(s)`. A failure of any other kind (`TypeError`, `KeyError`, `AttributeError`) means the test is broken, not validly RED, and must be fixed before E-03.
  - Execution state: pending

- [ ] E-03 Remove the `"supported"` boolean keys from all 24 `t1_policy`, `t2_layout`, and `t3_global` tier objects across the 8 hosts in `.aw/system/workflows/conformance/tools/host_matrix.json`.
  - Depends on: E-02
  - Expected outcome: in `.aw/system/workflows/conformance/tools/host_matrix.json`, the `"supported"` entry is deleted from each host's `t1_policy`, `t2_layout`, and `t3_global` object. All 8 host keys, `display_name`, `t1_policy.mechanism`, `t1_policy.notes`, `t2_layout.preferred_path`, `t3_global.global_path`, `diagnostic_commands`, and `command_template` keep their values. The file stays valid JSON with the existing 2-space indentation. Trailing commas are fixed where the removed key was the last member: `"supported"` is the FIRST key of each `t1_policy` and the LAST key of each `t2_layout`/`t3_global`, so the preceding line's comma must be dropped in the latter. Both new tests and all existing tests in `tests/test_host_capability_registry.py` pass.
  - Execution state: pending

### Task group 3: validate across capability, lifecycle, release-readiness, and full test suites

- [ ] E-04 Run the capability, release-readiness, and lifecycle fixture checks, verify `aw releases readiness --suite-passed --residual-risk-signer qa` on the live checkout, and run the bare full test suite.
  - Depends on: E-03
  - Expected outcome:
    1. `python3 -m pytest -o addopts="" -q tests/test_host_capability_registry.py tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py tests/test_release_readiness_producers.py tests/test_releases_readiness_cli.py tests/test_release_readiness_child_pin.py` reports 0 failed. The pass count is re-derived at execution and is not a bar.
    2. `lifecycle_fixtures.run_all_fixtures()` returns a `List[FixtureOutcome]`, one per name in `lifecycle_fixtures.ALL_FIXTURES`. It must satisfy `all(o.passed for o in outcomes)`, and the `multi-host-discovery` outcome's `evidence["hosts"]` must list all 8 hosts.
    3. `python3 -m agent_workflows releases readiness --suite-passed --residual-risk-signer qa` on the live worktree reports `capability_freshness | PASS | no stale capability claims`. Paste the overall verdict and exit code as observed. If any OTHER gate fails, name it and show it fails identically at the execution base, so it is not caused by this change.
    4. Bare `python3 -m pytest` shows zero new failures, compared by name against the execution-base baseline.
  - Execution state: pending

- [ ] E-05 Add one `- Fixed:` bullet under `## 2.0.0 (pending)` in `CHANGELOG.md` (no em or en dashes). It states that the shipped conformance host matrix no longer carries unproven `supported` booleans, so `aw releases readiness` no longer reports 19 stale capability claims, and that host support is established only by probe evidence in the capability registry.
  - Depends on: E-04
  - Expected outcome: `CHANGELOG.md` gains exactly one bullet under the pending release heading, with zero em or en dashes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Static host matrix entries are seed data for probe scaffolding and command rendering, not capability proof. `HostCapabilityRegistry.migrate_from_static_matrix` (`agent_workflows/host_capability_registry.py`) registers every `t*` dict on a host as `result=STATUS_UNVERIFIED` and `source_type=SOURCE_STATIC_MIGRATION`. `HostCapabilityRegistry.query_capability` refuses `SOURCE_STATIC_MIGRATION` records as unproven, with the reason `"Unproven claim: static migration seed requires an operator-run live probe."` (`DECISIONS.md` D113; executed plan `4fttzq`).
- `release_readiness.gate_capability_freshness` (`agent_workflows/release_readiness.py`) checks only `(host, feat)` entries in `.aw/system/workflows/conformance/tools/host_matrix.json` that explicitly assert `"supported": True`. It fails closed whenever a static matrix claims support without live probe evidence (executed plan `ttg9uz`).
- Tests must assert observable behavior and outcomes, never source code structure (`inspect`, `ast`, regex over `.py` files, or line counts), and must be shown RED against the pre-change state first (AGENTS.md and GUIDING_PRINCIPLES P16).
- Full test suite runs BARE as `python3 -m pytest` (no `-n0`, extra `-q`, or `-p no:randomly`).
- `host_matrix.json` is SHIPPED: `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]` maps `".aw/system" = "agent_workflows/_data/.aw/system"`. Editing it therefore changes installed package data and needs a `CHANGELOG.md` entry; recent fixes use `- Fixed:` bullets under `## 2.0.0 (pending)`.
- Measured at review (HEAD `6a412554d`):
  - `gate_capability_freshness` `evidence["stale_claims"]` is a `list[str]` (`f"{host}:{feat}: {reason}"`), not a list of dicts.
  - `hcr.SOURCE_STATIC_MIGRATION == "static_migration"` and `hcr.STATUS_UNVERIFIED == "unverified"`.
  - `migrate_from_static_matrix` returns the `int` count of records.
  - `lifecycle_fixtures.run_all_fixtures()` returns 11 `FixtureOutcome`s (`clean-install`, `legacy-update`, `partial-state`, `customized-file`, `interrupted-update`, `rollback`, `downgrade-warning`, `no-network`, `no-credential`, `multi-host-discovery`, `unsupported-host`), all `passed=True`.
  - On a copy of the matrix with all 24 `"supported"` keys removed:
    - `gate_capability_freshness(repo_root=<copy>)` returns `passed=True, evidence={'stale_claims': [], 'claims_checked': 0}`.
    - Migration yields 24 `('unverified', 'static_migration')` records.
    - `scaffold_probe_fixture` and `render_probe_commands` succeed for `opencode` at `T1`/`T2`/`T3`.
    - Re-seeding `antigravity.t2_layout.supported = True` gives `passed=False`, `claims_checked=1`, `stale_claims=['antigravity:t2_layout: Unproven claim: ...']`.
  - `aw releases readiness --suite-passed --residual-risk-signer qa` exits 1 with `capability_freshness` as the only failing gate.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Both plans in Set `usggph` (`ttg9uz` and `wa64wz`) are now `executed`, and the 19 `"supported": true` booleans in `.aw/system/workflows/conformance/tools/host_matrix.json` are the sole remaining cause of `capability_freshness` failing on the live repository. | `.aw/records/plans/executed/20261012-usggph-01-ttg9uz-give-the-generated-drift-workflow-disposition-and-capability.ipd.md` and `.aw/records/plans/executed/20261012-usggph-02-wa64wz-add-a-read-only-aw-releases-readiness-command-that-renders-t.ipd.md` have `- Status: executed`. Driven at `e2b5c0555` and again at `6a412554d`, `release_readiness.gate_capability_freshness()` returns `passed=False, detail='19 stale claim(s)'`. `python3 -m agent_workflows releases readiness --suite-passed --residual-risk-signer qa` exits `1` (`Verdict: NO-GO`), and `capability_freshness` is the only `FAIL` row of 11 gates. |
| F-02 | Prior decision D113 (`DECISIONS.md`), research `20260821-awoptimize-01-y1eb0q`, and executed plan `4fttzq` already decided that static host matrix boolean support flags give way to `unverified` seed records. `host_capability_registry.load_host_matrix`'s built-in fallback dict already omits `"supported"`. | `DECISIONS.md` D113 records `host_matrix.json` as the "seeded host matrix" of a deterministic scaffolder plus operator-run protocol. Executed plan `4fttzq` (`20260821-awoptimize-10-4fttzq-host-capability-evidence-registry-and-isolated-probes.ipd.md`), `- Concern:` and findings table: *"Replace boolean host support claims with versioned evidence that defaults to unverified"* and *"The static host matrix contains unproven support booleans + command templates. \| Treat it as seed data, not evidence; migrate to versioned claims that default to `unverified`."* In `agent_workflows/host_capability_registry.py`, `load_host_matrix`'s fallback dict (returned when the file is absent) has no `"supported"` keys. The `.aw/system/workflows/conformance/tools/host_matrix.json` file was outside `4fttzq`'s `- Scope-Paths:`. |
| F-03 | Recording static probe evidence in git is neither supported by the architecture nor durable across releases. | `release_readiness.gate_capability_freshness` instantiates `reg = hcr.HostCapabilityRegistry()` and calls `reg.migrate_from_static_matrix(data)` without loading any persisted probe store (`ttg9uz` F-04). `HostCapabilityRegistry.query_capability` enforces `DEFAULT_EVIDENCE_TTL_DAYS = 90`, so a static timestamp committed to git would decay into a release blocker. The 8 external host CLIs/IDEs cannot be executed in a repository checkout. |
| F-04 | Removing `"supported"` from all 24 tier dicts preserves every consumer while making `gate_capability_freshness()` pass with `claims_checked == 0`. | The only reader of a host-matrix `"supported"` key is `release_readiness.gate_capability_freshness` (`if isinstance(feat_val, dict) and feat_val.get("supported") is True:`). Other `"supported"` strings in `agent_workflows/` (`host_cmd.py` row dicts, `host_adapters.py` status values, `host_capability_registry.STATUS_SUPPORTED`) are unrelated and never read the matrix. `tests/` uses synthetic matrices. Driven at review against a copy with all 24 keys removed: migration yields 24 `('unverified', 'static_migration')` records, `scaffold_probe_fixture`/`render_probe_commands` succeed across `T1`/`T2`/`T3`, and `gate_capability_freshness(repo_root=<copy>)` returns `passed=True, detail='no stale capability claims', evidence={'stale_claims': [], 'claims_checked': 0}`. |
| F-05 | No other pending plan touches `.aw/system/workflows/conformance/tools/host_matrix.json` or `tests/test_host_capability_registry.py`. All existing tests across the 6 capability and release-readiness test files pass. | `git grep -n -e "host_matrix.json" -e "test_host_capability_registry.py" .aw/records/plans/pending/` matches only this plan. The 6-file run reported `102 passed` at authoring and again at review HEAD `6a412554d`; this count is context, not a bar. |

## Proposed changes (ordered, validatable)

1. E-01 re-measures `.aw/system/workflows/conformance/tools/host_matrix.json` (19 `supported: true`, 5 `supported: false`), `HostCapabilityRegistry.migrate_from_static_matrix` (24 `unverified` records), and `release_readiness.gate_capability_freshness()` (`passed=False`, 19 stale claims) at the executing HEAD.
2. E-02 adds `TestShippedHostMatrixAndFreshnessGate` (`unittest.TestCase`) in `tests/test_host_capability_registry.py` and runs it against the pre-E-03 `host_matrix.json` to demonstrate an `AssertionError` RED first.
3. E-03 removes the `"supported"` key from all 24 tier dicts in `.aw/system/workflows/conformance/tools/host_matrix.json` and keeps every other field.
4. E-04 runs the 6-file capability and release-readiness pytest suite, `lifecycle_fixtures.run_all_fixtures()`, `python3 -m agent_workflows releases readiness --suite-passed --residual-risk-signer qa`, and the bare `python3 -m pytest` suite.
5. E-05 adds one `- Fixed:` `CHANGELOG.md` bullet for the shipped data change.

## Deferred / out of scope (with reason)

- Wiring `release_readiness.gate_artifact_manifest` and `release_readiness.build_report` to validate `.aw/system/workflows/index.md` on disk.
  - Carrier: 3jkm7y, w9l8ph
- Cleaning up legacy IPD lint errors across the repository's historical plan corpus if any surface outside clean worktrees.
  - Carrier: r4a4ab
- Calling `aw releases readiness` automatically from `release-review`, CI, or a pre-push hook.
  - Carrier: uypgvi
- Modifying `agent_workflows/host_capability_registry.py`, `agent_workflows/release_readiness.py`, or `.aw/system/workflows/conformance/tools/conformance_harness.py`. Consumed unchanged.
  - Carrier-Declined: out-of-scope boundary; these modules already implement the unverified migration and freshness check and are consumed unchanged.

## Scope check

- Over-scope: none. Only `.aw/system/workflows/conformance/tools/host_matrix.json`, `tests/test_host_capability_registry.py`, and `CHANGELOG.md` are modified.
- Under-scope: none. Every consumer of `host_matrix.json` (`conformance_harness.py`, `host_capability_registry.py`, `release_readiness.py`, `lifecycle_fixtures.py`) is verified against the updated matrix.

## Required tests / validation

Run the following:
- The pre-E-03 RED demonstration: `python3 -m pytest -o addopts="" -v tests/test_host_capability_registry.py -k TestShippedHostMatrixAndFreshnessGate`.
- The post-E-03 GREEN run of `tests/test_host_capability_registry.py` and the five release-readiness test files (`tests/test_release_readiness.py`, `tests/test_release_readiness_docs_gate.py`, `tests/test_release_readiness_producers.py`, `tests/test_releases_readiness_cli.py`, `tests/test_release_readiness_child_pin.py`).
- `lifecycle_fixtures.run_all_fixtures()`.
- `python3 -m agent_workflows releases readiness --suite-passed --residual-risk-signer qa`.
- The full bare test suite (`python3 -m pytest`), comparing any failure by name against the execution-base baseline.

## Spec / documentation sync

- `CHANGELOG.md`: one `- Fixed:` bullet (E-05), because the matrix ships in the wheel.
- Everything else is N/A with reason: no `.spec.md` and no user-facing documentation under `docs/` or `.aw/system/workflows/conformance/` specifies `"supported"` booleans in `host_matrix.json`. `.aw/system/workflows/conformance/README.md` only names the file path. Removing the Phase 0 booleans aligns `host_matrix.json` with `DECISIONS.md` D113 and executed plan `4fttzq`.

## Open questions

### OQ-01: Should this plan record live probe evidence for the 19 `supported: true` entries or retire the unproven `"supported"` booleans from `host_matrix.json`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from repository evidence (F-02, F-03): retire the unproven `"supported"` booleans from `.aw/system/workflows/conformance/tools/host_matrix.json`. `DECISIONS.md` D113 defines `host_matrix.json` as a Phase 0 scaffold whose host invocations are an operator-run protocol. Executed plan `4fttzq` ruled that static host matrix boolean support claims give way to `HostCapabilityRegistry` records that default to `unverified`. Furthermore, `release_readiness.gate_capability_freshness` builds an in-memory `HostCapabilityRegistry` seeded only from `host_matrix.json`, any committed probe timestamp would expire after `DEFAULT_EVIDENCE_TTL_DAYS = 90` days, and the 8 external host CLIs/IDEs cannot be live-probed inside a repository checkout. Backlog `5gzno3` offers exactly these two options and names retirement as acceptable.

### OQ-02: Should the `"supported"` key be removed from all 24 tier dicts (`t1_policy`, `t2_layout`, `t3_global`) or should the 19 `"supported": true` entries be flipped to `"supported": false`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from repository evidence (F-02, F-04): remove the key from all 24 tier dicts. Flipping to `"supported": false` would falsely assert that those tiers are known to be unsupported, when their actual state in `HostCapabilityRegistry.migrate_from_static_matrix` is `STATUS_UNVERIFIED`. Removal matches the fallback dict in `host_capability_registry.load_host_matrix`, preserves all 24 migrated records, and leaves every consumer working. This was demonstrated at review on a copy of the matrix (see the review measurements in Step 0).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the execution HEAD sha and the full E-01 transcript (code paths: `host_capability_registry.load_host_matrix`, `HostCapabilityRegistry.migrate_from_static_matrix`, `release_readiness.gate_capability_freshness`) showing:
    - (a) 8 hosts and 24 `t*` tier dicts, with 19 `"supported": True` and 5 `"supported": False`;
    - (b) `migrate_from_static_matrix` returning `24`, with every record `result == "unverified"` and `source_type == "static_migration"`;
    - (c) `gate_capability_freshness()` returning `passed=False`, `detail='19 stale claim(s)'`, and `claims_checked=19`, with the stale entries printed as strings.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste:
    1. the `git diff` hunk adding `TestShippedHostMatrixAndFreshnessGate` in `tests/test_host_capability_registry.py`;
    2. the pre-E-03 RED pytest output of `python3 -m pytest -o addopts="" -v tests/test_host_capability_registry.py -k TestShippedHostMatrixAndFreshnessGate`, showing both new methods failing with `AssertionError` (not `TypeError`/`KeyError`/`AttributeError`) against the unmodified `host_matrix.json`;
    3. `git grep -n -E 'getsource|import ast|ast\.parse|import inspect' tests/test_host_capability_registry.py` returning exit 1 (no matches).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste:
    1. the `git diff` for `.aw/system/workflows/conformance/tools/host_matrix.json`, showing only the 24 `"supported"` lines removed (plus the trailing-comma adjustments on the preceding lines) and every other field preserved;
    2. `git grep -n '"supported"' .aw/system/workflows/conformance/tools/host_matrix.json` returning exit 1 (0 matches), and `python3 -m json.tool .aw/system/workflows/conformance/tools/host_matrix.json > /dev/null` exiting 0;
    3. the post-E-03 GREEN pytest output of `python3 -m pytest -o addopts="" -v tests/test_host_capability_registry.py`, showing every test in the file passing, including both methods of `TestShippedHostMatrixAndFreshnessGate`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste:
    1. the output of `python3 -m pytest -o addopts="" -q tests/test_host_capability_registry.py tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py tests/test_release_readiness_producers.py tests/test_releases_readiness_cli.py tests/test_release_readiness_child_pin.py` (0 failed);
    2. the driven output of `[(o.name, o.passed) for o in lifecycle_fixtures.run_all_fixtures()]` with every entry `True`, plus the `multi-host-discovery` outcome's `evidence["hosts"]` listing all 8 hosts (code path: `lifecycle_fixtures.run_multi_host_discovery` via `hcr.load_host_matrix`);
    3. the full CLI output and exit code of `python3 -m agent_workflows releases readiness --suite-passed --residual-risk-signer qa`, showing the `capability_freshness | PASS | no stale capability claims` row (code path: `release_readiness.build_report` -> `gate_capability_freshness`), with any other failing gate shown to fail identically at the execution base;
    4. the execution-base and post-change bare `python3 -m pytest` summary lines, with zero new failures by name (pass counts are context, not a bar).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `git diff CHANGELOG.md` showing the one new `- Fixed:` bullet under `## 2.0.0 (pending)`, plus pasted output of `git diff -U0 CHANGELOG.md | grep -P '^\+.*[\x{2013}\x{2014}]'` returning exit 1 (no em/en dash on any added line).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval (`- Status: approved`) before execution.

EXECUTION CONTRACT. All open questions (OQ-01, OQ-02) are resolved; none blocks. When executing by hand, start with `aw ipd begin 8ru81x`. Commit only the declared `- Scope-Paths:` plus this plan, through `aw commit 8ru81x -- <paths>`; never `git add -A`, `-a`, `--no-verify`, `git stash`, or a push. Verify the staged set with `git diff --cached --name-only` before committing (shared checkout). HONESTY RULE: every `V-*` MUST paste the ACTUAL runner output; never claim a test run that was not performed.

SCOPE FENCE. `agent_workflows/host_capability_registry.py`, `agent_workflows/release_readiness.py`, and `.aw/system/workflows/conformance/tools/conformance_harness.py` are consumed unchanged. If an out-of-scope edit proves necessary, make it, then justify it with `aw ipd finalize --scope-reason`.

POST-GATE LIFECYCLE. Do not mark this plan `executed` until `aw ipd lint --phase pre-transition` conforms, every `E-*` is `performed`, and all five `V-*` items carry pasted evidence with `Result: pass`. Under `aw oc run` or `aw agy run` the runner owns begin and finalize, so the executor must NOT run `aw ipd finalize`. When executing by hand, run `aw ipd finalize 8ru81x`; never move the plan with a hand `git mv`.
