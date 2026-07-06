# Implementation plan (Section 7)

Consolidated from Sections 1-6. Fix Bar: fix by default; defer only at Medium-High+ Remediation
Risk. All findings here are Low severity except a couple Medium; none is a blocker. The subject
is the framework itself.

## Findings and disposition

| ID | Sev | RR | Axis | Disposition |
|----|-----|----|----|-------------|
| S2-B1 | Low | Low | - | FIX: scan_secrets.py skip `workflow-artifacts/` + `*-lock.json`; add regression test. |
| S2-M1 | Low | Low | - | FIX: add `--version` to setup_tools.py + test. |
| S2-M2 | Low | Low | - | FIX: compute shannon_entropy once in scan_secrets.py. |
| S3-T1 | Low | Low | - | FIX (small): add a capture_hpc parse test (monkeypatch which/env). |
| S3-T2 | Low | Low | - | RESOLVED-BY S6-CI1 + optional: adding tests.yml lets verify-in-CI run them; a Makefile `test` target would let /verify discover locally. FIX the Makefile target (low RR, dogfoods verify). |
| S4-D1 | Med | Low | - | FIX: ARCHITECTURE shims count 15 -> 16. |
| S4-D2 | Med | Low | - | FIX: ARCHITECTURE "three Python tools" -> four; add bench_env.py; correct test enumeration. |
| S4-D3 | Low | Low | - | FIX: add a benchmark route to getting-started. |
| S6-CI1 | Med | Low | - | FIX: add `.github/workflows/tests.yml` running the unittest suite on push+PR. |
| S5-F1 | Low | Med | functionality | DEFER to user action (validation): run /benchmark on a real repo. Not a code fix; forcing a redesign without a live run is the Medium-RR functionality risk. Surface in Section 8. |
| S6-P1 | Low | Med | functionality | PARTIAL: the CI matrix (in tests.yml) will attempt to verify the floor. If 3.7/3.8 cannot be provisioned on runners, SOFTEN the README claim to the lowest CI-verified minor rather than assert an unverified floor (honesty, P2). The stated-floor change itself is Medium-RR (compat contract), so do the safe part (test what we can + soften) and note the rest. |

## Ordered Section 7 batches

1. **Tools batch** (S2-B1, S2-M1, S2-M2): edit scan_secrets.py (skip set + single entropy calc),
   setup_tools.py (--version), add regression tests (scanner scope, setup_tools --version) and the
   S3-T1 capture_hpc test. Run the full suite (must stay green).
2. **Docs batch** (S4-D1, S4-D2, S4-D3): ARCHITECTURE counts + getting-started route. Em-dash-free.
3. **CI + dogfood batch** (S6-CI1, S3-T2, S6-P1): add tests.yml with a conservative Python matrix;
   add a Makefile `test` target so /verify discovers the suite locally; adjust the README 3.7+
   claim only if the matrix cannot cover it (leave the claim if the matrix floor supports it, note
   the decision).
4. **VERSION + DECISIONS**: bump 20260704-05 -> 20260704-06; add a DECISIONS entry (D43) recording
   this review's fixes. Update index.md stamp.

## Deferred / user-action

- S5-F1: run /benchmark on a real repo (user action; surfaced in the final report, not fixed here).

## Validation

- `python3 -m unittest discover -s tests -t .` must stay green (and grow with new tests).
- scan_secrets re-run: candidate count drops (no workflow-artifacts/lockfile hits).
- setup_tools.py --version prints VERSION.
- installer dry-run on self: still no drift after doc/CI edits.
- em-dash sweep = 0 on all changed files.
- tests.yml: validate YAML shape; it will actually run once pushed (cannot run Actions locally).
