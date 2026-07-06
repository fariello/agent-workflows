# Persona review (accumulates across sections)

## Section 1 (inventory) seed notes
- Stakeholder (8): the toolkit is coherent and internally consistent (no manifest/shim drift,
  version consistent, tests green). Fitness-for-purpose looks strong at inventory level.
- Software engineer (5): only 4 small stdlib tools carry executable risk; clean subprocess use.
- Novice (7): README + getting-started present; deeper first-run check in Section 4.
(Sections 2-6 append lead-persona observations here.)

## Section 2 (quality/security/edge) lead-persona notes
- QA/QC (1): the built-in scanner's 98% false-positive rate on this repo (S2-B1) is a QA
  concern for anyone reading its raw output; triage guidance in the workflow body mitigates it,
  but excluding workflow-artifacts/ and lockfiles would materially cut noise.
- Software engineer (5): the 4 tools are clean - arg-list subprocess (no shell=True), files via
  `with`, temp files removed in `finally` (bench_env disk_probe), size caps, no eval/exec. Only
  S2-M1 (missing --version) and S2-M2 (double entropy calc) are minor. MEM: tools are short-lived
  CLIs; no unbounded caches, no leaks; not applicable at production-service scale.
- Security architect (4): NO committed secrets/PII (gitleaks 0/65 commits). No injection surface.
  Scanner redaction never emits full values (verified redact() at :133). Strong posture.
- LIVE surfaces: NOT APPLICABLE - the tools are read-only scanners / environment capture / a
  check-runner with a hard denylist + consent; no resume/spend/coordination/overwrite surface.
  The installer writes files but stages-not-commits, backs up, and is idempotent (its own tests
  cover fresh/re-run/prune/dry-run).

## Section 3 (tests/regression) lead-persona notes
- Testing/regression expert (2): 46 tests cover all 4 tools and the SAFETY-critical paths well
  (run_checks denylist-never-runs-under-yes, scan_secrets redaction+history, installer
  prune/migration/exec-bit, bench_env each-diagnosis-fires). Gaps are minor (S3-T1, S3-T2).
  The S2-B1 fix must ship with a regression test (planned in Section 7).
- QA/QC (1): the framework does not dogfood its own `verify` (S3-T2) - run_checks finds 0 checks
  here because the test command is only in CONTRIBUTING prose. Worth fixing for dogfooding.
- Evidence: verify-results.json (VID 20260706-113000) records the real run: discovered 1, ran 1,
  passed 1, exit 0, ~8.9s. all_ran_passed=true. Not self-reported.

## Section 4 (docs/specs/examples) lead-persona notes
- Complete novice (7): README quick-start, command table, and the /benchmark row are clear and
  accurate. But the getting-started TOUR omits a performance goal (S4-D3) - a newcomer asking
  "how do I check performance?" is not routed to the new workflow.
- UI/UX (3): docs are internally consistent EXCEPT two stale counts in ARCHITECTURE introduced by
  the benchmark addition (S4-D1 shims 15->16; S4-D2 "three tools"->four). Both are exactly the
  P2 honest-docs axis this repo holds itself to. Recent D42 (accessibility terminal rubric) and
  README benchmark coverage are accurate and complete.
