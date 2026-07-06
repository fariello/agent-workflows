# Section 2 per-phase report - Quality, security, edge cases

## What I did
- Ran the mandatory committed-secrets scan (tree + history) via scan_secrets.py, saved
  secrets-scan.json, and cross-checked with gitleaks over full history.
- Triaged all 518 built-in candidates: 508 (98%) high-entropy false positives (prose/hashes),
  8 "PII" hits all intentional (author contact email in DECISIONS/CITATION, test@example.com in
  fixtures). gitleaks: 0 leaks across 65 commits. Result: NO committed secrets/PII (S2-S1).
- Read the four Python tools for correctness, security, edge cases, MEM, and LIVE surfaces.

## Why
- Secrets in history are the highest-consequence release risk and cannot be caught by reading
  files; the scan is a MUST. The tools are the only executable code, so they carry all the
  correctness/security risk in this repo.

## Findings
- S2-S1 (Low): secrets scan CLEAN. Recorded as evidence, no action.
- S2-B1 (B, Low sev / Low RR): scan_secrets.py does not skip workflow-artifacts/ or *-lock.json,
  so it re-scans run records (including its own prior scan.json) and lockfiles -> 140 of 518
  candidates were avoidable noise. Fix in Section 7 (add to skip set + a test).
- S2-M1 (M, Low / Low): setup_tools.py lacks --version while the other three tools have it. Fix.
- S2-M2 (M, Low / Low): scan_secrets.py computes shannon_entropy twice per token. Trivial; fix.

## MEM / LIVE
- MEM: not a concern. Tools are short-lived CLIs; files via `with`, temp files removed in
  `finally`, size caps, no unbounded caches. No leaks.
- LIVE: NOT APPLICABLE. Read-only scanners / env capture / check-runner (denylist + consent).
  No resume/spend/coordination/overwrite surface. Installer stages-not-commits, backs up,
  idempotent (own tests cover it).

## What I considered but did NOT do
- Did NOT file findings on the 508 entropy false positives themselves: that is inherent to a
  heuristic entropy detector and correctly marked "low" for triage; the fixable part is scope
  (S2-B1), not the heuristic.
- Did NOT treat the 8 email hits as PII leaks: they are the maintainer's deliberately-published
  contact and standard test fixtures.
- Did NOT change any tool code (Section 7 owns fixes).
