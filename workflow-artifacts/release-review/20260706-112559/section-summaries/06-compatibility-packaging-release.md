# Section 6 per-phase report - Compatibility, packaging, CI, release

## What I did
- Assessed CI (.github/workflows), the cross-tool shim frontmatter, the installer's version
  stamping, install/first-run clarity, and the Python 3.7+ compatibility claim.

## Why
- For an installable, multi-tool framework, the release risks are: does it install and run across
  the claimed tools/Python versions, and is quality enforced in CI? Those are the operator/engineer
  concerns.

## Findings
- S6-CI1 (CI, Medium/Low): only secret-scan runs in CI; the 46 self-tests (the core quality gate)
  are not enforced. Add tests.yml (stdlib unittest; no secrets/publish) in Section 7.
- S6-P1 (P, Low / Medium functionality): "Python 3.7+" is asserted, not tested. Verify via a CI
  matrix or soften to the lowest CI-verified minor. RR Medium because the stated floor is a
  compatibility contract to change deliberately.

## Assessed OK
- secret-scan CI: well-formed (full history, read-only perms, no publish).
- Shims: correctly tailored per tool (opencode vs claude frontmatter); no drift (Section 1).
- Install/first-run: clear (stages-not-commits, --dry-run, --version, AGENTS pointer).
- Schema validation: NOT APPLICABLE (no data schemas; tool JSON shapes covered by self-tests).
- No breaking changes this cycle; DECISIONS is the changelog. No migration concerns.

## What I considered but did NOT do
- Did NOT recommend lint/format/typecheck CI: no configured tooling; would be new scope (P6).
- Did NOT edit CI/README (Section 7 owns changes).
