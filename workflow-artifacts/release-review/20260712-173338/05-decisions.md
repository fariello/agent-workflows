# 05 Decisions

- Subject: the framework itself (explicit-subject exception, D43 precedent). workflow-artifacts/ excluded.
- Parallel audit mode USED: 4 read-only lanes (code/security/MEM, tests, docs, packaging/CI). Main agent synthesized, deduped, assigned official IDs, verified the 2 convergent high-value findings against source before acting.
- Fix Bar: all 10 findings were Low remediation risk. FIXED 7 (A1-A7); DEFERRED 3 (A8 P4-history, A9 non-adversarial/out-of-scope, A10 maintainer-deferred bucket) with stated axes.
- Duplicate: the rc-comparator issue was independently found by 3 lanes (code C-B1, tests T-1, packaging VER-2); merged into one finding S2-B1.
- The pre-flight gate fired verdict-free (D72 fix working) and the user chose PROCEED.
- No LIVE/High data-integrity finding. No secret exposure. No public API break (rc comparator + Term fixes are internal; pyproject classifier drop is metadata-only, twine-clean).
