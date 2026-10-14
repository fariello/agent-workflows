# IPD: Retire unproven supported booleans from the conformance host matrix

- Date: 2026-10-14
- Kind: child
- Concern: NINETEEN UNPROVEN `supported: true` BOOLEANS IN `.aw/system/workflows/conformance/tools/host_matrix.json` CAUSE `capability_freshness` TO BE THE SOLE REMAINING LIVE FAILURE OF `aw releases readiness` ON THIS REPOSITORY. Both sibling plans in Set `usggph` (`ttg9uz` and `wa64wz`) are now `executed`. Measured at authoring HEAD `e2b5c0555`: `.aw/system/workflows/conformance/tools/host_matrix.json` defines 8 hosts (`antigravity`, `claude_code`, `codex`, `copilot`, `cursor`, `gemini_cli`, `kiro`, `opencode`), each with 3 tier dicts (`t1_policy`, `t2_layout`, `t3_global`) for 24 tier entries total, of which 19 carry `"supported": true` (`antigravity:t1_policy`, `antigravity:t2_layout`, `antigravity:t3_global`, `claude_code:t1_policy`, `claude_code:t2_layout`, `claude_code:t3_global`, `codex:t2_layout`, `codex:t3_global`, `copilot:t2_layout`, `copilot:t3_global`, `cursor:t2_layout`, `cursor:t3_global`, `gemini_cli:t1_policy`, `gemini_cli:t2_layout`, `gemini_cli:t3_global`, `kiro:t2_layout`, `kiro:t3_global`, `opencode:t2_layout`, `opencode:t3_global`) and 5 carry `"supported": false` (`codex:t1_policy`, `copilot:t1_policy`, `cursor:t1_policy`, `kiro:t1_policy`, `opencode:t1_policy`). Driving `release_readiness.gate_capability_freshness()` on the repository root returns `GateResult(name='capability_freshness', passed=False, detail='19 stale claim(s)', evidence={'claims_checked': 19, 'stale_claims': [...]})` where every one of the 19 `supported: true` entries fails `HostCapabilityRegistry.query_claim` with `Unproven claim: static migration seed requires an operator-run live probe.`, and driving `python3 -m agent_workflows releases readiness --suite-passed --residual-risk-signer qa` exits `1` (`Verdict: NO-GO`) with `capability_freshness` as the sole failing gate out of all 11 gates (F-01).
  WHY RETIRE THE `supported` BOOLEANS RATHER THAN RECORD PROBE EVIDENCE IN GIT (F-02, F-03, OQ-01). Backlog item `5gzno3` asks to *"Either record real probe evidence for the 19 `supported: true` host/tier claims in `.aw/system/workflows/conformance/tools/host_matrix.json` or retire the claims that are not yet backed by probes, so `gate_capability_freshness()` reflects verified support."* Repository architecture and prior decisions resolve this to retiring the `"supported"` booleans from `host_matrix.json`:
  1. `DECISIONS.md` D113 (`Phase 0 host delivery conformance harness and operator protocol`) defines `host_matrix.json` as a deterministic scaffold ("seeded host matrix") whose host invocations are an operator-run protocol, not recorded proof.
  2. Research `20260821-awoptimize-01-y1eb0q` and executed plan `4fttzq` (`Host capability evidence registry and isolated probes`) ruled: *"Replace boolean host support claims with versioned evidence that defaults to unverified"* and *"The static host matrix contains unproven support booleans + command templates. | Treat it as seed data, not evidence; migrate to versioned claims that default to unverified."* When `4fttzq` implemented `host_capability_registry.load_host_matrix`, its built-in fallback schema already omitted `"supported"` from every host entry, keeping only the structural probe-harness fields (`display_name`, `t2_layout.preferred_path`, `t3_global.global_path`, `command_template`, `diagnostic_commands`); `.aw/system/workflows/conformance/tools/host_matrix.json` lay outside `4fttzq`'s scope fence and kept the legacy Phase 0 seed booleans (F-02).
  3. Mechanically, `release_readiness.gate_capability_freshness` instantiates a fresh `HostCapabilityRegistry()`, seeds it solely from `host_matrix.json` via `migrate_from_static_matrix(data)` (which tags every migrated entry `source_type=SOURCE_STATIC_MIGRATION` and `result=STATUS_UNVERIFIED`), and calls `reg.query_claim(host, feat)` only on `(host, feat)` pairs where `feat_val.get("supported") is True`. Nothing in the repository persists or loads a separate capability evidence store on disk (`ttg9uz` F-04), any committed probe timestamp would expire after `DEFAULT_EVIDENCE_TTL_DAYS = 90` days, and the 8 external proprietary host CLIs/IDEs (`antigravity`, `claude_code`, `codex`, `copilot`, `cursor`, `gemini_cli`, `kiro`, `opencode`) cannot be live-probed in a repository checkout (F-03).
  WHY REMOVE `"supported"` FROM ALL 24 TIER DICTS RATHER THAN FLIPPING `true` TO `false` (F-04, OQ-02). Setting `"supported": false` on `t2_layout` and `t3_global` would replace an unproven positive claim with a false negative claim that those tiers are unsupported, whereas `HostCapabilityRegistry.migrate_from_static_matrix` checks `if not feat_key.startswith("t") or not isinstance(feat_val, dict): continue` (never reading `"supported"`), and neither `conformance_harness.py` nor `host_capability_registry.py` (`scaffold_probe_fixture`, `render_probe_commands`) nor `lifecycle_fixtures.py` (`multi-host-discovery`) reads `"supported"`. Removing the `"supported"` key from all 24 `t1_policy`, `t2_layout`, and `t3_global` dicts while keeping `t1_policy` (`mechanism`, `notes`), `t2_layout` (`preferred_path`), and `t3_global` (`global_path`) intact preserves all 24 migrated `(host, tier)` records (`result == STATUS_UNVERIFIED`, `source_type == SOURCE_STATIC_MIGRATION`), all 8 hosts in `multi-host-discovery`, and all `T1`/`T2`/`T3` probe scaffolding and command rendering, while `gate_capability_freshness()` returns `passed=True, detail='no stale capability claims', evidence={'stale_claims': [], 'claims_checked': 0}` (F-04).
  WHY `followup` AND NO RELEASE GATE IS INVENTED. Backlog item `5gzno3` carries `- Work-Kind: followup`, `- Priority: medium`, and no `- Blocks-Release:`; all three are preserved without inventing a release gate.
- Scope: IN: (1) add behavioral and falsifiability tests in `tests/test_host_capability_registry.py` (shown RED against the pre-change `.aw/system/workflows/conformance/tools/host_matrix.json` first) verifying that the shipped default host matrix (`host_capability_registry.DEFAULT_MATRIX_PATH`) carries all 8 hosts and 24 `t1_policy`/`t2_layout`/`t3_global` tier dicts, contains zero `"supported"` boolean claims, migrates all 24 `(host, tier)` entries to `STATUS_UNVERIFIED` / `SOURCE_STATIC_MIGRATION` via `HostCapabilityRegistry.migrate_from_static_matrix`, scaffolds and renders `T1`/`T2`/`T3` probes cleanly, and passes `release_readiness.gate_capability_freshness()` while a copy of the matrix with a `"supported": true` seed fails `gate_capability_freshness(repo_root=...)`; (2) retire the `"supported"` boolean keys from all 24 `t1_policy`, `t2_layout`, and `t3_global` tier entries across the 8 hosts in `.aw/system/workflows/conformance/tools/host_matrix.json`, preserving all structural and documentation fields (`display_name`, `mechanism`, `notes`, `preferred_path`, `global_path`, `diagnostic_commands`, `command_template`). OUT: modifying `agent_workflows/host_capability_registry.py`, `agent_workflows/release_readiness.py`, or `.aw/system/workflows/conformance/tools/conformance_harness.py`; building an on-disk persistence format for live probe records; wiring `gate_artifact_manifest` (`3jkm7y` / `w9l8ph`); and running `aw releases readiness` from CI or `release-review` (`uypgvi`).
- Scope-Paths: .aw/system/workflows/conformance/tools/host_matrix.json, tests/test_host_capability_registry.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: medium
- From-Backlog: 5gzno3
- Set: 5gzno3
- Order: 1
- Highest E allocated: 04
- Author: antigravity
- Id: 8ru81x

## Workflow history
- 2026-10-14 to-review (aw set): Authored from backlog 5gzno3 at HEAD e2b5c0555: retire unproven supported booleans from .aw/system/workflows/conformance/tools/host_matrix.json and guard with behavioral tests.

- 2026-10-14 draft (antigravity): created.

## Goal

Retire the unproven Phase 0 `"supported"` boolean claims from `.aw/system/workflows/conformance/tools/host_matrix.json` so the shipped matrix serves purely as structural host/tier seed data that migrates to `unverified` in `HostCapabilityRegistry`, clearing the 19 stale-claim failures in `release_readiness.gate_capability_freshness()` while preserving all 24 host/tier registrations and probe-harness consumers.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before changing anything

- [ ] E-01 Re-measure the live `.aw/system/workflows/conformance/tools/host_matrix.json` boolean claims, `HostCapabilityRegistry.migrate_from_static_matrix`, and `release_readiness.gate_capability_freshness` at the executing HEAD before changing any file.
  - Depends on: none
  - Expected outcome: one pasted transcript proving, by driving the code on the repository root: (a) `host_capability_registry.load_host_matrix(host_capability_registry.DEFAULT_MATRIX_PATH)` loads 8 hosts and 24 `t*` tier dicts (`t1_policy`, `t2_layout`, `t3_global`), of which 19 carry `"supported": True` and 5 carry `"supported": False`; (b) `HostCapabilityRegistry().migrate_from_static_matrix(data)` produces 24 `CapabilityRecord` entries, all with `result == "unverified"` and `source_type == "static-migration"`; and (c) `release_readiness.gate_capability_freshness()` returns `passed=False`, `detail == "19 stale claim(s)"`, and `evidence["claims_checked"] == 19` with all 19 `stale_claims` entries carrying `reason == "Unproven claim: static migration seed requires an operator-run live probe."`. If (a) already shows 0 `"supported"` keys and (c) already returns `passed=True`, stop and reconcile rather than repeating the change.
  - Execution state: pending

### Task group 2: add falsifiable behavioral tests and retire the unproven booleans

- [ ] E-02 Add behavioral and falsifiability tests in `tests/test_host_capability_registry.py` for the shipped default host matrix and `release_readiness.gate_capability_freshness`, and verify they fail (RED) before editing `.aw/system/workflows/conformance/tools/host_matrix.json`.
  - Depends on: E-01
  - Expected outcome: add a test class `TestShippedHostMatrixAndFreshnessGate` in `tests/test_host_capability_registry.py` (exercising real functions and data structures, never inspecting `.py` source code via `inspect`, `ast`, or regex) with two test methods:
    - `(t1)` `test_shipped_host_matrix_omits_boolean_support_claims_and_migrates_all_tiers_unverified`: loads `data = hcr.load_host_matrix(hcr.DEFAULT_MATRIX_PATH)`, asserts `len(data["hosts"]) == 8`, asserts every host defines `t1_policy`, `t2_layout` (with non-empty `preferred_path`), `t3_global` (with non-empty `global_path`), `command_template`, and `diagnostic_commands`, asserts no `t*` tier dict in `data["hosts"]` contains the `"supported"` key (`[(h, k) for h, cfg in data["hosts"].items() for k, v in cfg.items() if k.startswith("t") and isinstance(v, dict) and "supported" in v] == []`), asserts `HostCapabilityRegistry().migrate_from_static_matrix(data)` registers all 24 `(host, tier)` records with `result == hcr.STATUS_UNVERIFIED` and `source_type == hcr.SOURCE_STATIC_MIGRATION`, and asserts `hcr.scaffold_probe_fixture` and `hcr.render_probe_commands` succeed for `T1`, `T2`, and `T3` against the shipped matrix;
    - `(t2)` `test_shipped_host_matrix_passes_capability_freshness_gate_while_seeded_true_fails`: calls `release_readiness.gate_capability_freshness()` against the repository root and asserts `passed is True`, `detail == "no stale capability claims"`, and `evidence == {"stale_claims": [], "claims_checked": 0}`; then writes a copy of `data` into `tmp_path / ".aw/system/workflows/conformance/tools/host_matrix.json"` with `antigravity.t2_layout["supported"] = True` and asserts `release_readiness.gate_capability_freshness(repo_root=tmp_path)` returns `passed is False`, `evidence["claims_checked"] == 1`, and `evidence["stale_claims"][0]["host"] == "antigravity"`.
    Run `python3 -m pytest -o addopts="" -v tests/test_host_capability_registry.py -k TestShippedHostMatrixAndFreshnessGate` against the pre-E-03 `.aw/system/workflows/conformance/tools/host_matrix.json` and observe both `(t1)` and `(t2)` failing with `AssertionError` on the 19/24 `"supported"` booleans and `19 stale claim(s)`.
  - Execution state: pending

- [ ] E-03 Remove the `"supported"` boolean keys from all 24 `t1_policy`, `t2_layout`, and `t3_global` tier objects across the 8 hosts in `.aw/system/workflows/conformance/tools/host_matrix.json`.
  - Depends on: E-02
  - Expected outcome: in `.aw/system/workflows/conformance/tools/host_matrix.json`, delete the `"supported": true` / `"supported": false` entry from each host's `t1_policy`, `t2_layout`, and `t3_global` object while keeping `version`, all 8 host keys, `display_name`, `t1_policy.mechanism`, `t1_policy.notes`, `t2_layout.preferred_path`, `t3_global.global_path`, `diagnostic_commands`, and `command_template` byte-for-byte intact. Both new tests in `TestShippedHostMatrixAndFreshnessGate` and all existing tests in `tests/test_host_capability_registry.py` pass.
  - Execution state: pending

### Task group 3: validate across capability, lifecycle, release-readiness, and full test suites

- [ ] E-04 Run the capability, release-readiness, and lifecycle fixture checks, verify `aw releases readiness --suite-passed --residual-risk-signer qa` on the live checkout, and run the bare full test suite.
  - Depends on: E-03
  - Expected outcome: (1) `python3 -m pytest -o addopts="" -q tests/test_host_capability_registry.py tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py tests/test_release_readiness_producers.py tests/test_releases_readiness_cli.py tests/test_release_readiness_child_pin.py` passes with 0 failures (`104 passed`); (2) `lifecycle_fixtures.run_all_fixtures()` returns `all_passed == True` across all 4 fixtures (`fresh-install`, `rerun-update`, `multi-host-discovery`, `conformance-probe`) with `multi-host-discovery` discovering all 8 hosts; (3) `python3 -m agent_workflows releases readiness --suite-passed --residual-risk-signer qa` on the live worktree reports `capability_freshness: PASS — no stale capability claims` (and exits `0` with `Verdict: GO` when all other live gates are clean); and (4) bare `python3 -m pytest` passes with zero new failures compared by name against the execution-base baseline.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Static host matrix entries are seed data for probe scaffolding and command rendering, not capability proof: `HostCapabilityRegistry.migrate_from_static_matrix` (`agent_workflows/host_capability_registry.py`) registers every `t*` dict on a host as `result=STATUS_UNVERIFIED` and `source_type=SOURCE_STATIC_MIGRATION`, and `HostCapabilityRegistry.query_claim` refuses `SOURCE_STATIC_MIGRATION` records as unproven (`DECISIONS.md` D113; executed plan `4fttzq`).
- `release_readiness.gate_capability_freshness` (`agent_workflows/release_readiness.py`) checks only `(host, feat)` entries in `.aw/system/workflows/conformance/tools/host_matrix.json` that explicitly assert `"supported": True`, failing closed whenever a static matrix claims support without live probe evidence (`executed` plan `ttg9uz`).
- Tests must assert observable behavior and outcomes, never source code structure (`inspect`, `ast`, regex over `.py` files, or line counts), and must be shown RED against the pre-change state first (AGENTS.md and GUIDING_PRINCIPLES P16).
- Full test suite runs BARE as `python3 -m pytest` (no `-n0`, extra `-q`, or `-p no:randomly`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Both plans in Set `usggph` (`ttg9uz` and `wa64wz`) are now `executed`, and the 19 `"supported": true` booleans in `.aw/system/workflows/conformance/tools/host_matrix.json` are the sole remaining cause of `capability_freshness` failing on the live repository at `e2b5c0555`. | `.aw/records/plans/executed/20261012-usggph-01-ttg9uz-give-the-generated-drift-workflow-disposition-and-capability.ipd.md` and `.aw/records/plans/executed/20261012-usggph-02-wa64wz-add-a-read-only-aw-releases-readiness-command-that-renders-t.ipd.md` have `- Status: executed`. Driven at `e2b5c0555`: `release_readiness.gate_capability_freshness()` returns `GateResult(name='capability_freshness', passed=False, detail='19 stale claim(s)', evidence={'claims_checked': 19, 'stale_claims': [...]})`, and `python3 -m agent_workflows releases readiness --suite-passed --residual-risk-signer qa` exits `1` (`Verdict: NO-GO`) with `capability_freshness` as the only `FAIL` row among all 11 gates. |
| F-02 | Prior decision D113 (`DECISIONS.md`), research `20260821-awoptimize-01-y1eb0q`, and executed plan `4fttzq` already decided that static host matrix boolean support flags are retired in favor of `unverified` seed records, and `host_capability_registry.load_host_matrix`'s built-in fallback schema already omits `"supported"`. | `DECISIONS.md` D113 describes `host_matrix.json` as a Phase 0 deterministic scaffold whose host launches are an operator-run protocol. Executed plan `4fttzq` (`20260821-awoptimize-10-4fttzq-host-capability-evidence-registry-and-isolated-probes.ipd.md` under `## Findings` and `## Goal`) states: *"Replace boolean host support claims with versioned evidence that defaults to unverified"* and *"The static host matrix contains unproven support booleans + command templates. \| Treat it as seed data, not evidence; migrate to versioned claims that default to unverified."* In `agent_workflows/host_capability_registry.py`, `load_host_matrix`'s fallback dict defines `t2_layout: {"preferred_path": ...}` and `t3_global: {"global_path": ...}` with no `"supported"` keys; `.aw/system/workflows/conformance/tools/host_matrix.json` was outside `4fttzq`'s `- Scope-Paths:` and retained the Phase 0 booleans. |
| F-03 | Recording static probe evidence in git is neither supported by the architecture nor durable across releases. | `release_readiness.gate_capability_freshness` instantiates `reg = hcr.HostCapabilityRegistry()` and calls `reg.migrate_from_static_matrix(data)` without loading any persisted probe store (`ttg9uz` F-04 notes no committed capability evidence file exists in the repository). `HostCapabilityRegistry.query_claim` enforces `DEFAULT_EVIDENCE_TTL_DAYS = 90`, so any static timestamp committed to git would decay into a release blocker after 90 days, and the 8 external proprietary host CLIs/IDEs cannot be executed in a repository checkout. |
| F-04 | Removing `"supported"` from all 24 `t1_policy`, `t2_layout`, and `t3_global` dicts in `.aw/system/workflows/conformance/tools/host_matrix.json` preserves every consumer in the repository while making `gate_capability_freshness()` pass with `claims_checked == 0`. | `git grep -n '"supported"'` across the repository matches only `agent_workflows/release_readiness.py` (`gate_capability_freshness`: `if isinstance(feat_val, dict) and feat_val.get("supported") is True:`), `.aw/system/workflows/conformance/tools/host_matrix.json`, and synthetic test dicts in `tests/`. Driven at `e2b5c0555` against a copy of `host_matrix.json` with `"supported"` removed from all 24 tier dicts: `HostCapabilityRegistry().migrate_from_static_matrix(data)` still produces 24 `CapabilityRecord` entries (`result == "unverified"`, `source_type == "static-migration"`), `conformance_harness.scaffold` / `render_commands` and `host_capability_registry.scaffold_probe_fixture` / `render_probe_commands` succeed across `T1`/`T2`/`T3`, `lifecycle_fixtures.run_fixture("multi-host-discovery")` passes (`hosts_discovered == 8`), and `release_readiness.gate_capability_freshness(repo_root=...)` returns `passed=True, detail='no stale capability claims', evidence={'stale_claims': [], 'claims_checked': 0}`. |
| F-05 | No other pending plan in `.aw/records/plans/pending/` touches `.aw/system/workflows/conformance/tools/host_matrix.json` or `tests/test_host_capability_registry.py`, and all 102 existing tests across the 6 capability and release-readiness test files pass at `e2b5c0555`. | `git grep -n -e "host_matrix.json" -e "test_host_capability_registry.py" .aw/records/plans/pending/` matches only this plan. `python3 -m pytest -o addopts="" -q tests/test_host_capability_registry.py tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py tests/test_release_readiness_producers.py tests/test_releases_readiness_cli.py tests/test_release_readiness_child_pin.py` -> `102 passed in 21.87s`. |

## Proposed changes (ordered, validatable)

1. E-01 re-measures `.aw/system/workflows/conformance/tools/host_matrix.json` (19 `supported: true`, 5 `supported: false`), `HostCapabilityRegistry.migrate_from_static_matrix` (24 `unverified` records), and `release_readiness.gate_capability_freshness()` (`passed=False`, 19 stale claims) at the executing HEAD.
2. E-02 adds `TestShippedHostMatrixAndFreshnessGate` in `tests/test_host_capability_registry.py` (`test_shipped_host_matrix_omits_boolean_support_claims_and_migrates_all_tiers_unverified` and `test_shipped_host_matrix_passes_capability_freshness_gate_while_seeded_true_fails`) and runs it against the pre-E-03 `host_matrix.json` to demonstrate RED failure first.
3. E-03 removes the `"supported"` boolean keys from all 24 `t1_policy`, `t2_layout`, and `t3_global` tier dicts in `.aw/system/workflows/conformance/tools/host_matrix.json`, keeping all structural and documentation fields untouched.
4. E-04 runs the 6-file capability and release-readiness pytest suite, `lifecycle_fixtures.run_all_fixtures()`, `python3 -m agent_workflows releases readiness --suite-passed --residual-risk-signer qa`, and the bare `python3 -m pytest` suite.

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

- Over-scope: none. Only `.aw/system/workflows/conformance/tools/host_matrix.json` and `tests/test_host_capability_registry.py` are modified.
- Under-scope: none. Every consumer of `host_matrix.json` (`conformance_harness.py`, `host_capability_registry.py`, `release_readiness.py`, `lifecycle_fixtures.py`) is verified against the updated matrix.

## Required tests / validation

Run the pre-E-03 RED test demonstration (`python3 -m pytest -o addopts="" -v tests/test_host_capability_registry.py -k TestShippedHostMatrixAndFreshnessGate`), the post-E-03 GREEN run of `tests/test_host_capability_registry.py` and the five release-readiness test files (`tests/test_release_readiness.py`, `tests/test_release_readiness_docs_gate.py`, `tests/test_release_readiness_producers.py`, `tests/test_releases_readiness_cli.py`, `tests/test_release_readiness_child_pin.py`), `lifecycle_fixtures.run_all_fixtures()`, `python3 -m agent_workflows releases readiness --suite-passed --residual-risk-signer qa`, and the full bare test suite (`python3 -m pytest`), comparing any failure by name against the execution-base baseline.

## Spec / documentation sync

N/A with reason: no `.spec.md` or user-facing documentation under `docs/` or `.aw/system/workflows/conformance/README.md` specifies `"supported"` booleans in `.aw/system/workflows/conformance/tools/host_matrix.json` (`git grep -n -e "5gzno3" -e "host_matrix.json" -- docs/ .aw/system/workflows/` matches only `.aw/system/workflows/conformance/README.md`'s file path bullet and `conformance_harness.py::DEFAULT_MATRIX_PATH`). Removing the Phase 0 `"supported"` booleans brings `host_matrix.json` into alignment with `DECISIONS.md` D113 and executed plan `4fttzq`.

## Open questions

### OQ-01: Should this plan record live probe evidence for the 19 `supported: true` entries or retire the unproven `"supported"` booleans from `host_matrix.json`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from repository evidence (F-02, F-03): retire the unproven `"supported"` booleans from `.aw/system/workflows/conformance/tools/host_matrix.json`. `DECISIONS.md` D113 defines `host_matrix.json` as a Phase 0 scaffold whose host invocations are an operator-run protocol, and executed plan `4fttzq` ruled that boolean host support claims in the static host matrix are replaced by `HostCapabilityRegistry` records that default to `unverified` (`host_capability_registry.load_host_matrix`'s built-in fallback schema already omits `"supported"`). Furthermore, `release_readiness.gate_capability_freshness` instantiates an in-memory `HostCapabilityRegistry` seeded only from `host_matrix.json`, any committed probe timestamp would expire after `DEFAULT_EVIDENCE_TTL_DAYS = 90` days, and the 8 proprietary external host CLIs/IDEs cannot be live-probed inside a repository checkout.

### OQ-02: Should the `"supported"` key be removed from all 24 tier dicts (`t1_policy`, `t2_layout`, `t3_global`) or should the 19 `"supported": true` entries be flipped to `"supported": false`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from repository evidence (F-02, F-04): remove the `"supported"` key from all 24 tier dicts rather than flipping `"supported": true` to `"supported": false`. Flipping `t2_layout` and `t3_global` to `"supported": false` would falsely assert that those tiers are known to be unsupported, whereas the actual state in `HostCapabilityRegistry.migrate_from_static_matrix` is `STATUS_UNVERIFIED`. Removing `"supported"` matches the fallback schema in `host_capability_registry.load_host_matrix`, preserves all 24 migrated `(host, tier)` records (`if not feat_key.startswith("t") or not isinstance(feat_val, dict): continue`), and leaves every consumer (`conformance_harness.py`, `host_capability_registry.py`, `lifecycle_fixtures.py`, `release_readiness.py`) working cleanly.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the execution HEAD sha and the full E-01 transcript (code paths: `host_capability_registry.load_host_matrix`, `HostCapabilityRegistry.migrate_from_static_matrix`, `release_readiness.gate_capability_freshness`) showing: (a) 8 hosts and 24 `t*` tier dicts in `.aw/system/workflows/conformance/tools/host_matrix.json` with 19 `"supported": True` and 5 `"supported": False`; (b) 24 migrated `CapabilityRecord` entries with `result == "unverified"` and `source_type == "static-migration"`; and (c) `gate_capability_freshness()` returning `passed=False`, `detail='19 stale claim(s)'`, and `claims_checked=19`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste (1) the `git diff` hunk adding `TestShippedHostMatrixAndFreshnessGate` in `tests/test_host_capability_registry.py`; (2) the pre-E-03 RED pytest output of `python3 -m pytest -o addopts="" -v tests/test_host_capability_registry.py -k TestShippedHostMatrixAndFreshnessGate` showing both `test_shipped_host_matrix_omits_boolean_support_claims_and_migrates_all_tiers_unverified` and `test_shipped_host_matrix_passes_capability_freshness_gate_while_seeded_true_fails` failing with `AssertionError` against the unmodified `host_matrix.json`; and (3) `git grep -n -E 'getsource|import ast|ast\.parse|import inspect' tests/test_host_capability_registry.py` returning exit 1 (no matches).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste (1) the `git diff` for `.aw/system/workflows/conformance/tools/host_matrix.json` showing only the 24 `"supported"` lines removed and all structural/documentation fields preserved; (2) `git grep -n '"supported"' .aw/system/workflows/conformance/tools/host_matrix.json` returning exit 1 (0 matches); and (3) the post-E-03 GREEN pytest output of `python3 -m pytest -o addopts="" -v tests/test_host_capability_registry.py` showing all tests in the file (including both methods of `TestShippedHostMatrixAndFreshnessGate`) passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste (1) the output of `python3 -m pytest -o addopts="" -q tests/test_host_capability_registry.py tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py tests/test_release_readiness_producers.py tests/test_releases_readiness_cli.py tests/test_release_readiness_child_pin.py` (`104 passed`, 0 failed); (2) the driven output of `lifecycle_fixtures.run_all_fixtures()` showing `all_passed=True` across all 4 fixtures (`fresh-install`, `rerun-update`, `multi-host-discovery` with `hosts_discovered=8`, `conformance-probe`); (3) the CLI output and exit code of `python3 -m agent_workflows releases readiness --suite-passed --residual-risk-signer qa` showing `[PASS] capability_freshness: no stale capability claims` and `Verdict: GO` (exit 0); and (4) the execution-base bare `python3 -m pytest` summary line alongside the post-change bare `python3 -m pytest` summary line showing +2 passed tests and zero new failures by name.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval (`- Status: approved`) before execution.

EXECUTION CONTRACT. All open questions (OQ-01, OQ-02) are resolved; none blocks. Commit only the two declared `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, `-a`, `--no-verify`, `git stash`, or a push. Verify the staged set with `git diff --cached --name-only` before committing (shared checkout). Paste actual runner output; never claim a test run that was not performed.

POST-GATE LIFECYCLE. Do not mark this plan `executed` until `aw ipd lint --phase pre-transition` conforms and all four `V-*` items carry pasted evidence with `Result: pass`. Under `aw oc run` or `aw agy run` the runner owns begin/finalize; by hand, use `aw ipd finalize`, never a hand `git mv`.
