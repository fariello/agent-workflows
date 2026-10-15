# Review findings: plan 8ru81x

- Subject-Id: 8ru81x
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `6a412554d` in an isolated review lane. The plan was committed and unchanged (`088a00057`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified by driving the code:
- Live matrix: 8 hosts, 24 tier dicts, 19 true and 5 false. `migrate_from_static_matrix` returns `24` and every record is `('unverified', 'static_migration')`. `gate_capability_freshness()` returns `False`, `19 stale claim(s)`, with `stale_claims` as a list of STRINGS.
- `aw releases readiness --suite-passed --residual-risk-signer qa` exits 1, and `capability_freshness` is the only failing gate.
- A copy of the matrix with all 24 keys removed passes the gate (`claims_checked 0`). Scaffold and render succeed for T1/T2/T3. Re-seeding one `supported: true` fails the gate with `stale_claims[0] == 'antigravity:t2_layout: ...'`.
- `lifecycle_fixtures.run_all_fixtures()` returns a list of 11 `FixtureOutcome`s, all passed. It has no `all_passed` attribute, and no fixtures named `fresh-install`/`rerun-update`/`conformance-probe` exist.
- The 6 targeted test files report `102 passed`.
- `pyproject.toml` force-includes `.aw/system` into the wheel.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Verification (unsatisfiable test) | `release_readiness.gate_capability_freshness` `stale.append(f"{host}:{feat}: {reason}")`; probe | E-02 (t2) asserted `evidence["stale_claims"][0]["host"] == "antigravity"`. The entries are strings, so a correct implementation would raise `TypeError`, and the RED demonstration would conflate a broken test with a valid failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Changed to `.startswith("antigravity:t2_layout:")`. E-02 now requires the RED failure to be an `AssertionError` specifically. |
| PR-002 | HIGH | IN-SCOPE | E. Verification (wrong API) | `lifecycle_fixtures.run_all_fixtures` returns `List[FixtureOutcome]`; `lifecycle_fixtures.ALL_FIXTURES` (11 names) | E-04/V-04 demanded `all_passed == True` across 4 fixtures (`fresh-install`, `rerun-update`, `conformance-probe`), none of which exist, plus `hosts_discovered=8`, which is not a field. That demand cannot be satisfied. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten as `all(o.passed ...)` over `ALL_FIXTURES`, with `multi-host-discovery` `evidence["hosts"]` listing 8 hosts. |
| PR-003 | MEDIUM | IN-SCOPE | E. Verification (live counts as bars) | 6-file run `102 passed`; plan demanded `104 passed` and `+2 passed` | The success criteria hard-coded test counts, which are artifacts of test organization. V-04 also demanded `Verdict: GO` exit 0, which depends on every other live gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bars are now 0 failed and no new failures by name. The verdict and exit code are pasted as observed, and any other failing gate must be shown to fail identically at base. |
| PR-004 | MEDIUM | IN-SCOPE | G. Stale evidence | `HostCapabilityRegistry.query_capability`; `hcr.SOURCE_STATIC_MIGRATION == "static_migration"`; `migrate_from_static_matrix -> int` | The plan cited a nonexistent `query_claim` (the gate calls `query_capability`), the value `"static-migration"` (the real value is `static_migration`), "24 `CapabilityRecord` entries" (the method returns an int count), and an over-broad `git grep '"supported"'` claim. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected throughout. The review measurements are recorded in Step 0. |
| PR-005 | MEDIUM | IN-SCOPE | E. Testing (harness and vacuity) | `tests/test_host_capability_registry.py` is `unittest` (`import unittest`, `tempfile`); `load_host_matrix` fallback dict when the file is absent | E-02 used pytest `tmp_path` in a unittest module. The shape test could also pass vacuously through the fallback dict if the default path moved. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The tests now use `tempfile.TemporaryDirectory()` and assert `DEFAULT_MATRIX_PATH.is_file()` first. Scaffold and render cover every host and tier, and `repo_root` is explicit. |
| PR-006 | MEDIUM | UNDER-SCOPE | G. Documentation sync | `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]` `".aw/system"` | `host_matrix.json` ships in the wheel, so this is a user-visible data change, but the plan had no CHANGELOG entry. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-05/V-05 (one `- Fixed:` bullet, dash check) and added `CHANGELOG.md` to Scope-Paths. |
| PR-007 | LOW | IN-SCOPE | G. Execution contract / executability | `## Approval and execution gate`; matrix key order | The gate lacked `aw ipd begin`, an explicit scope fence, and a plan-id-specific `aw commit` and finalize. E-03 did not warn that `"supported"` is the last key in `t2_layout`/`t3_global`, so removing it requires a comma fix and JSON validation. OQ owners read `none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate. Added the comma note to E-03 and a `json.tool` check to V-03. OQ owners are now `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does the readiness CLI step require overall GO/exit 0? | No; require only the `capability_freshness` PASS row, with other failures shown to pre-exist | Keep GO/exit 0 (depends on unrelated live gates) | `aw releases readiness` gate table at `6a412554d` | yes |
| D-2 | Add a CHANGELOG entry for a data-only change? | Yes, one `- Fixed:` bullet | Omit (the wheel ships the file, so users would see unexplained behavior) | `pyproject.toml` force-include of `.aw/system` | yes |
| D-3 | Keep OQ-01/OQ-02 resolved without asking the maintainer? | Yes; the owner is recorded as `plan author` | Escalate as blocking (the backlog item already names retirement as acceptable, and the change is a reversible data edit) | backlog `5gzno3` text; `4fttzq` findings; review probe on a copied matrix | yes |
