# Review findings: plan w9l8ph

- Subject-Id: w9l8ph
- Subject-Type: ipd
- Reviewed-At: 2026-10-14
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `2fcae08d5`. The plan was committed and byte-identical to the
lane input (sha256 `d25361b0...`), so no pre-review snapshot. `aw ipd lint --phase author`: `conforming`.
Not an orchestrator.

Re-measured at HEAD: `gate_artifact_manifest(manifest_present: bool = True, consistent: bool = True)` and
`build_report`'s `manifest_present: bool = True` / `manifest_consistent: bool = True` pass-through (F-01
MATCH); `release_readiness` is consumed only by `cli.py`'s `releases readiness` route. Live
`engine.parse_manifest(.aw/system/workflows)`: 63 rows, 0 duplicate commands, 0 body/lens paths missing at
`repo_root / rel`, no absolute or `..` paths, both stamps `1.2.1` equal to `.aw/system/VERSION` (F-02
MATCH). `setup_minimal_workflows_tree` writes `| whatnext | workflows/whatnext.md | ... |` with no file
(F-03 MATCH). Existing injection tests `test_gate_artifact_manifest_passing` / `_failing` assert exact
`detail` and `evidence` dicts, which E-02's injection branch preserves. Probes: `UnicodeDecodeError` from
`parse_manifest` and its `SystemExit` messages carry no path, but an `OSError` message does; a symlink in
the workflows dir to a file outside the tree is `is_file()` True and not `is_relative_to(root)`. Live `aw
releases readiness --agent --suite-passed --residual-risk-signer qa`: exit 1, NO-GO on `ipd_lint` and
`capability_freshness` (unrelated).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A correctness / B containment | plan E-02 step 3 (`(root / rel).is_file() or (manifest_file.parent / rel).is_file()`); `engine` `Workflow.body` is repo-relative | A second resolution base accepted paths the installer would never ship (the very fixture defect F-03 describes would pass), and `is_file()` follows symlinks out of the repo. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 resolves only `root / rel`, requires `resolve()` within `root`; new E-05 arm `(r3b)`. |
| PR-002 | MEDIUM | IN-SCOPE | B leak hygiene | plan E-02 step 2 (`f"... {type(exc).__name__}: {exc}"`); review probe (OSError message contains the tmp path) | Interpolating `str(exc)` would put absolute paths into `evidence`, rendered verbatim by `aw releases readiness --agent`; manifest-supplied `rel` text likewise. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Exception text only for `SystemExit`; `rel` passed through `agent_schema.redact_home_paths`; E-05 `(r4)` adds an invalid-UTF-8 arm asserting no tmp path in evidence. |
| PR-003 | MEDIUM | IN-SCOPE | G live-artifact criteria | plan E-01 (c) "63 rows"; E-06 "+7 new tests"; V-06 "`81 passed`", "+7 passed tests"; V-02 (6) `workflows_checked=63` | Bars were live counts (manifest row count, collected test totals) that the re-derivation convention forbids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bars now re-derived at execution HEAD and stated by named tests / zero new failures by name. |
| PR-004 | MEDIUM | UNDER-SCOPE | D anti-regression | plan E-01 (c) | Nothing said what to do if the live manifest is dirty at execution; wiring the gate would then turn the live report NO-GO on a pre-existing defect. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now stops and reports when the live tree is not clean. |
| PR-005 | LOW | UNDER-SCOPE | G documentation | `CHANGELOG.md` Unreleased (sibling `releases readiness` entries) | A user-visible behavior change to `aw releases readiness` had no CHANGELOG line. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | CHANGELOG added to E-06, V-06 and Scope-Paths. |
| PR-006 | LOW | IN-SCOPE | G runtime reachability | plan V-02 | No demonstration through the real CLI path; also a computed failure gave no count in `detail`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 adds an `aw releases readiness --agent` run on the repo (code path `run_readiness` -> `build_report` -> `gate_artifact_manifest`), expected to omit `artifact_manifest` from diagnostics whatever the overall verdict; computed `detail` carries the problem count, injected `detail` unchanged. |
| PR-007 | LOW | IN-SCOPE | G execution contract | plan gate; OQ-01/OQ-02 `Owner: none` | The scope fence did not use the declare-then-justify wording (`--scope-reason`/`--scope-ack`); resolved questions named no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate wording added; owners set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Resolve manifest paths relative to the repo only, or also relative to `index.md`'s directory? | Repo root only, contained by `resolve()`. | Dual base as authored (REJECTED: accepts paths that do not ship; F-03's fixture would pass). | Live manifest: every body/lens is `.aw/system/workflows/...` from repo root; `engine` uses `Workflow.body` as repo-relative. | yes |
| D-2 | Accept the author's OQ-01 (validate `index.md`, not `managed-sections.json`) and OQ-02 (stamps validated when present)? | Accept both. | Require stamps always (REJECTED: forces VERSION into unrelated fixtures; the live tree carries both, so drift is still caught). | Plan F-02..F-04 re-measured; `Makefile` `version-file`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
