# CI assessment

## Current CI
- `.github/workflows/secret-scan.yml`: gitleaks over full history (fetch-depth 0), read-only
  permissions, on push+PR. Well-formed, low-risk, no publish/deploy. GOOD.

## Gap
- S6-CI1 (Medium sev / Low RR): NO CI runs the 46 self-tests. The tests are the framework's core
  quality guarantee (they gate every tool change per CONTRIBUTING), yet a PR could break them
  undetected. Adding a `tests.yml` that runs `python3 -m unittest discover -s tests -t .` is:
  clear command, low risk, no secrets, no publish/deploy/upload, aligned with the stdlib-only
  toolchain, and materially improves release readiness. RECOMMEND adding it (Section 7).
  A Python version matrix (e.g. 3.9/3.11/3.13) would ALSO verify the "Python 3.7+" compat claim
  (S6-P1). Note: 3.7/3.8 are EOL and may be hard to provision on current runners; recommend a
  matrix of supported-and-available minors and softening the claim if 3.7 cannot be CI-verified.

## Not recommended
- No lint/format/typecheck CI: the repo has no configured linter/formatter/type-checker and is
  stdlib prose+tools; adding one would be new tooling beyond current scope (P6). Not recommended now.
