# Review findings: plan whz0oi

- Subject-Id: whz0oi
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `aa139e584` in an isolated review-sweep lane. Child plan (own first `- Kind:` bullet reads `child`).
Plan committed and byte-identical to the lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent`
clean (one advisory `IPD-Z602`) before semantic review; `aw ipd lint --phase review-finalize --agent` clean (0 findings)
after revisions.

Verified at HEAD:
- `.aw/system/VERSION` = `1.2.1`; `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]`
  `".aw/system" = "agent_workflows/_data/.aw/system"`; no `[tool.hatch.build.hooks.custom]` yet.
- `agent_workflows/__init__._resolve_own_version` installed branch returns
  `versioning.resolve_version(bundled, version_file=bundled / "VERSION")`, i.e. the bundled file (F-01/F-02 hold).
- `cli._build_parser` `--version` is `action="version"` with `version=f"agent-workflows {__version__}"` (F-08).
- `doctor.probe_environment` emits `core.Drift` for `doctor.version-*` / `doctor.pypi-update-available`, with a
  `build_remediation` branch for the latter (F-04).

Demonstrations (hatchling 1.32.4, throwaway venv and scratch projects under the temp dir):
- Hook `build_data["force_include"][<tmpfile>] = "pkg/_data/system/VERSION"` beside a directory force-include of
  the same tree: wheel namelist `['pkg/_data/system/VERSION']` (single entry), content `b'9.9.9\n'`; source file
  still `1.2.1`. (F-06)
- Project with `code` version source reading a `1.2.1` file plus a `PKG-INFO` of `1.3.0rc2.dev5+gabc1234`
  (sdist-shaped): hook printed `HOOK metadata.version= 1.3.0rc2.dev5+gabc1234  code VERSION= 1.2.1`; wheel
  `fi-1.3.0rc2.dev5+gabc1234-py2.py3-none-any.whl`, bundled VERSION `b'1.3.0rc2.dev5+gabc1234\n'`. (F-05)
- Local-dir `pip install` writes `direct_url.json` = `{"dir_info": {}, "url": "file:///..."}`. (F-07)

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness | `hatch_build.py` `VERSION = resolve_version(_ROOT, version_file=v_file)`; demo F-05 above | E-02 baked `hatch_build.VERSION`, which in a wheel built from an sdist (no git) is the stale committed file while the dist version comes from `PKG-INFO`, so D01 would recur for sdist-built wheels. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now bakes `self.metadata.version`; V-02 adds an sdist-to-wheel check; F-05 records the demonstration. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness | `agent_workflows/__init__._resolve_own_version`; `importlib.metadata.version` resolves by name over `sys.path` | E-03's `importlib.metadata.version("agent-workflows")` could report a different installed copy than the one executing; the "files include this module" check was underspecified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 resolves the sibling `agent_workflows-*.dist-info` via `Distribution.at`, falls back to the bundled file, imports lazily. |
| PR-003 | MEDIUM | UNDER-SCOPE | G. Executability / right-sizing | `cli._build_parser` `action="version"`; original `Scope-Paths` lacked `agent_workflows/cli.py` | The conditional `aw --version` note was bundled into the doctor E-item, needs a change to an argparse static version action in an undeclared file, and had no V-item demanding its evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split to E-06 with V-06; `cli.py` added to Scope-Paths; check runs only when `--version` is requested. |
| PR-004 | MEDIUM | UNDER-SCOPE | C. Operability / F. silent failure | `doctor.probe_environment`, `doctor.build_remediation` | E-04 did not name the emission surface (Drift plus remediation), git timeouts, the build sha missing from the source repo, the `.d<date>` dirty suffix, or the non-git/no-`+g` cases; tests covered only three of them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 specifies each case, a 5 s git timeout, and the Drift plus `build_remediation` surface; E-05(b) adds the extra negative cases and the `--version` path. |
| PR-005 | HIGH | UNDER-SCOPE | Project rule (Every live bug gates the next release) | `AGENTS.md` "a spec or plan has no exemption field today and so must carry the gate"; front matter `- Work-Kind: bug` with no `Blocks-Release`; orchestrator review PR-002 of `i99ykd` | Live bug plan did not gate release `next`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Blocks-Release: next`. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract / V evidence | `## Approval and execution gate`; V-02, V-04 | Gate lacked resolved-OQ statement, explicit honesty rule, scope fence as declaration, and conditional finalize ownership (it told the executor to run `aw ipd set executed` unconditionally); V-04 did not require running outside the checkout / `AW_NO_REEXEC=1`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten; V-04 states the re-exec precondition. |
| PR-007 | HIGH | IN-SCOPE | Project rule (durable carrier) | `check_engine.check_durable_carrier` on the unrevised plan: `malformed \`Carrier\` reference(s) 'none (deliberately not done)' (expected a bare 6-char id6)`; rule `check.ipd-uncarried-obligation` | Deferred row 1's `Carrier: none (...)` parses as a malformed id6 and fails `aw check` at error (same defect fixed on `i99ykd` as its PR-001). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with `Carrier-Declined:`; `check_durable_carrier` now returns nothing for this plan. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which value should the build hook bake? | `self.metadata.version` | `hatch_build.VERSION` as authored | Demonstration F-05 (hatchling `metadata/core.py` reads `PKG-INFO` for dynamic fields) | yes |
| D-2 | How should an installed package find its own version? | Sibling dist-info via `Distribution.at`, fallback bundled file | `importlib.metadata.version(name)` | F-07; first-match-on-`sys.path` semantics of name lookup | yes |
| D-3 | Should the `--version` note stay inside E-04? | Split to E-06 | Keep bundled | Right-sizing rubric (a)-(c): separate file, separate test surface | yes |
| D-4 | Add `Blocks-Release: next` within this review? | Yes | Leave for maintainer | AGENTS.md live-bug rule; this plan is in the review ledger; `i99ykd` review PR-002 asked for it at each child's review | yes |
