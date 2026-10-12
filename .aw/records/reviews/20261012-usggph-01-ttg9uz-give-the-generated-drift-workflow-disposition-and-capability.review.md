# Review findings: plan ttg9uz

- Subject-Id: ttg9uz
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `c6bea069b` in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified by driving the code:
- `gate_generated_drift()`, `gate_workflow_disposition()`, `gate_capability_freshness()` with no argument -> `[True, True, True]`.
- `git grep -e drift_files -e undispositioned -e stale_claims -- '*.py' ':!tests/'` outside `release_readiness.py` hits only `migration_complex.ReleaseReviewLedger.undispositioned`.
- `host_matrix.json`: 19 `"supported": true`; `migrate_from_static_matrix` seeds 24 records; all 19 queries at `exact_version="1.0.0"` return `is_supported=False` with `Unproven claim: static migration seed requires an operator-run live probe.`
- `load_host_matrix(<nonexistent>)` returns a built-in matrix with 0 supported booleans (F-07). Invalid JSON raises `ValueError`.
- `build_inventory(Path(".aw/system/workflows"))` -> `ok=True`, 64 dispositions. A minimal tree (manifest markers, one `whatnext` row, `conformance/operator-protocol.md`) -> `ok=True`, 2 dispositions, no findings, and adding a canonical package dir does not change that. `zzz` row -> `InventoryError`; no markers -> `SystemExit` (not an `Exception`); no `index.md` -> `FileNotFoundError`.
- `tests/fixtures/workflow-src/plan-review` copied under a workflows tree: `load_package` ok, `_compute_drift` gives 7 `missing`. 0 live `*/workflow.yaml` packages. PyYAML 6.0.3 present.
- Under a `subprocess.run` recorder, `build_inventory` and the capability path spawn nothing.
- `build_report` has no production caller; sibling `wa64wz` carries `executed:ttg9uz`. Backlog `5gzno3`, `3jkm7y`, `uypgvi` exist.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E. Testing (falsifiability) | `agent_workflows/release_readiness.py` `gate_generated_drift(drift_files: Sequence[str] = ())` has no `repo_root` parameter | The required RED arms (a), (g), (h), (j), (l) call `gate_*(repo_root=...)`, which against the pre-change module fail only by `TypeError`. That proves the signature changed, not that the gate can fail. Only arm (n) was a real behavioral red. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 adds `build_report` arms (o), (p), (q), one per gate, which the pre-change `build_report` accepts and reports PASS, so they are red by `AssertionError`. V-07 now demands that failure reason. |
| PR-002 | LOW | IN-SCOPE | Evidence | `agent_workflows/migration_complex.py` `ReleaseReviewLedger.undispositioned` | The Concern said each of the three names matches only `release_readiness.py`. `undispositioned` also matches an unrelated method, as F-01 and E-01 already say. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern reworded to match F-01. |
| PR-003 | LOW | OVER-SCOPE | F. KISS | `HostCapabilityRegistry.query_capability(..., now=None)`; F-04 "no persisted evidence store" | E-04 added a `now` parameter that no caller and no test arm exercises. With only static-migration seeds, expiry is never reached. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `now` removed from the E-04 signature and call. |
| PR-004 | LOW | IN-SCOPE | Evidence / D. Anti-regression | `tests/test_release_readiness.py::test_allowlist_recorder_decision_path`; `tests/test_release_readiness_docs_gate.py::test_checker_exception_handled_cleanly` | F-08 said "five" GO tests break but listed four, one of which (`test_checker_exception_handled_cleanly`) asserts only membership and does not break. The allowlist-recorder test is also the guard that the new producers spawn no subprocess, and the plan did not say so. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-08 now names the three GO-asserting tests. E-06 requires `test_allowlist_recorder_decision_path` to pass unmodified as the no-subprocess guard. |
| PR-005 | LOW | UNDER-SCOPE | E. Testing (failure path) | `engine.parse_manifest` reads `source_root / "index.md"` | A workflows dir with no `index.md` raises `FileNotFoundError` through `build_inventory`. E-03's `except Exception` covers it, but no arm pinned it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added arm (i2). |
| PR-006 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate did not state the open-question status. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now says OQ-01 and OQ-02 are resolved and non-blocking. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep a `now` parameter on `gate_capability_freshness` for testable expiry? | No | Keep it untested (dead parameter); add an expiry arm (needs a persisted evidence store that does not exist) | `host_capability_registry.query_capability` defaults `now`; F-04 no `save_to_json` caller | yes |
| D-2 | Prove falsifiability through `build_report` rather than only the gate functions? | Add `build_report` arms beside the gate arms | Accept `TypeError` reds (proves nothing about passing); drop the gate arms (loses detail assertions) | pre-change `build_report` accepts `repo_root` (`release_readiness.build_report` signature) | yes |
