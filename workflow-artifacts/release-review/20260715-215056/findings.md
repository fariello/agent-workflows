# Release-review findings register (run 20260715-215056)

Mode: REPORT-ONLY (no in-place fixes; corrective work proposed as an IPD). Framework-is-subject.
Three parallel audit lanes (D84) covered Sections 2-6; coordinator synthesized + independently
re-verified every Medium/actionable finding against source.

| ID | Sev | Section | Area | Finding | Evidence | Disposition |
|----|-----|---------|------|---------|----------|-------------|
| REL-000 | Low | 1 | git state | 7 staged-but-uncommitted scaffold files (comms skeleton + 2 docs .gitkeep) left by earlier installs | (pre-audit) | FIXED pre-audit, commit 817cbb7 (maintainer-approved housekeeping) |
| REL-001 | MEDIUM | 2 | correctness / consistency | The D85 F8 SystemExit-isolation fix landed in the CLI `_install_all`/`setup` but NOT in the legacy `engine.run()` multi-repo `--repo A B C` loop; `install_into_repo` there is not wrapped, so one repo's SystemExit (dir-conflict/git-fail) aborts the whole batch | engine.py:2809 (call unwrapped); cli.py:498 (the fix, for comparison) | PROPOSE (corrective IPD) |
| REL-002 | MEDIUM | 4 | release metadata | Author email disagrees between published metadata: `pyproject.toml` (gabriele.fariello@gmail.com) vs `CITATION.cff` (gfariello@fariel.com) | pyproject.toml:15; CITATION.cff:10 | PROPOSE (needs human: which is canonical) |
| REL-003 | LOW | 2 | rollback robustness | `run_rollback` catches only `OSError` reading `.created-files.json`; a corrupt/truncated record raises `JSONDecodeError` (ValueError) -> crashes before restoring | engine.py:1846 | PROPOSE (corrective IPD) |
| REL-004 | LOW | 4 | prose / attribution | `NOTICE` contains 2 em dashes, violating the repo's own no-dash rule; NOTICE ships in the wheel/sdist and is the redistributed attribution text | NOTICE:6,10 | PROPOSE (corrective IPD) |
| REL-005 | LOW | 4 | metadata freshness | `CITATION.cff` `date-released: 2026-07-05` is stale vs the pending 1.2.x cut (mid-July) | CITATION.cff:14 | PROPOSE (fold into release-execution / release-notes at tag time) |
| REL-006 | LOW | 6 | doc consistency | Internal "3.8 floor / 3.8-safe" wording in `_compat.py` + `tests.yml` comments vs the declared `>=3.9` | _compat.py:8-12; tests.yml:27-29 | PROPOSE (corrective IPD) |
| REL-007 | LOW | 6 | release process | `make version-file` bakes VERSION but does not sync the `index.md` WORKFLOWS-VERSION stamp in lockstep (both agree now at 1.2.1, but a future cut could forget) | Makefile:27; index.md:3 | PROPOSE (corrective IPD or release-checklist gate) |
| REL-008 | Nit | 2 | robustness | `latest_pypi_version` interpolates package name into URL without encoding (not exploitable; names are restricted) | versioning.py:359 | OPTIONAL / defer |
| DEC-1 | Decision | 6/8 | release scope | CHANGELOG has TWO pending un-cut sections (1.2.1 patch + 1.3.0 features). The cut must pick scope and reconcile: cutting 1.3.0 should fold the 1.2.1 bug-fix bullets in (same dev cycle) so no dangling "1.2.1 pending" is left untagged | CHANGELOG.md:7-12,51-53 | HUMAN DECISION (Section 8) |

## Confirmed SOUND (audited, clean - not defects)

- Security: no shell=True/eval/exec; all subprocess list-form; `comms.is_filename_safe` bypass-free;
  `scan_secrets.redact` leaks no full secret (incl. the D85 short-secret fix); gitleaks history clean;
  no hardcoded secrets; NO in-repo insecure-by-default service (comms ships no daemon/server/port).
- The three D85 fixes (run() exit code, --undo rollback completeness, CLI batch isolation) are real and
  tested; versioning robust on weird tags; the 1 test skip is justified (conditional release-tag assert);
  no residual date/tmpdir flakiness; tests are meaningful, not vacuous.
- PACKAGING (most release-critical): Python 3.9 is genuinely supported - EVERY module has
  `from __future__ import annotations`, zero unguarded runtime PEP 604 unions, no match statements. Zero
  runtime deps (enforced in CI). Version source (resolver + hatch_build) agree; a clean `v1.2.1` tag
  yields exactly `1.2.1`; dev/dirty builds get a `+local` segment PyPI rejects (double-guarded against
  accidental publish). Package-data ships the whole `.agents/workflows/` tree + VERSION; CI has a real
  wheel build+install+CLI-smoke gate across Linux/macOS/Windows on 3.9 + 3.13; entry points, metadata,
  LICENSE/NOTICE present.
- DOCS: novice path (pipx -> aw install .) sound and correctly ordered; `aw --help` + subcommands match
  docs; counts accurate (17 workflow dirs, 18 shims/tool, 16-row table, 30 assess lenses, 7 personas);
  install-workflows.py correctly marked deprecated with `aw` primary; `.agents/comms/` documented
  adequately; `GO - PENDING HUMAN APPROVAL` + `CONDITIONAL GO` vocabulary consistent everywhere;
  D79 D22b/D23b/D24b disambiguation fully resolved (no ambiguous cross-refs); cold-start knowledge sound;
  guiding-principles conformance good (P2 honest-docs, P4 cold-start, P6 KISS, P8 single-source all met).
