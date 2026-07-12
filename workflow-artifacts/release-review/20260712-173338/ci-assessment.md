# CI assessment
- tests.yml: unittest on 3.9+3.13, wheel build+import on 3 OSes. FIXED this run (A5): install `build` in the unittest job so the packaging ship-vs-dev gate (test_packaging.py) actually runs instead of self-skipping.
- secret-scan.yml: gitleaks full-history, push+PR, read-only. Sound.
- No auto-publish workflow (correct/desired per RELEASING.md + the execution contract).
- Deferred (non-blocking, follow-up): no lint/type-check job in CI (CI-2).
