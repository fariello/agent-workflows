# Review findings: plan gqyold

- Subject-Id: gqyold
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `76faafbc2`. The plan was committed and byte-identical to the lane input, so no pre-review
snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review, and
`--phase review-finalize` was clean after revision.

Re-verified (scratch probes under `/tmp`, no production edit):
- `rg -l security_hardening tests/` exits 1; the only package importer is `agent_workflows/host_runner.py`.
- `check_local_server_binding(h, True, 'tok')`: `127.0.0.1.evil.com`, `127.evil.com`, `127.0.0.1@evil.com`,
  `127.0.0.1 evil.com` all `True` (fail-open confirmed). Also `True`: `127.0.0.1:8080`, `127.1`, `LOCALHOST`,
  `127.0.0.0/8`. `False`: `[::1]`, `::ffff:127.0.0.1`, `0.0.0.0`, `127x`.
- `ipaddress.ip_address('::ffff:127.0.0.1').is_loopback`: True on 3.9.25 and 3.11.15, False on 3.12.3 and 3.14.6.
- A candidate fix (exact-set, then `ip_address` with ValueError->refuse, then refuse `ipv4_mapped`, then
  `is_loopback`) gave `mismatches: []` over 20 spellings on all four interpreters.
- Destructive gate: `human` True; `executor`, `verifier`, `agent`, `bogus` False.
- `check_evidence_redaction({'stdout': '/home/<some-user>/secret/path'})` -> `ok=True` (placeholder excluded by
  the `home-path` regex); runtime-built `"/home/" + "hardeningprobe" + ...` -> `ok=False`, `home-path` finding.
- AWS-shaped `aws_secret_access_key = ...` under `stdout`: `check_evidence_redaction` `ok=True`;
  `scan_text_for_secrets` -> `['generic-secret-env']`; `run_task` -> `completed`/`performed`, stdout admitted.
- `redact_worker_output(stdout='Authorization: Bearer abc123')` -> `ok=True`, stdout unchanged.
- `run_task` with a home-path runner double -> `failed_final`, `failed`, `[REDACTED-LEAK]`; clean -> `completed`,
  `performed`. `run_task` has no caller in `agent_workflows/`.
- Carriers resolve: `fe6aro`, `go20fk`, `wc5c5e` (open backlog), `d0lg63` (pending plan). New `lfko0e` filed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A/D. Correctness, cross-interpreter invariant | `agent_workflows/security_hardening.py:115` `check_local_server_binding`; `pyproject.toml:12` `requires-python = ">=3.9"` | E-03's prescribed `ipaddress` fix would make `::ffff:127.0.0.1` HOLD on 3.9/3.11 and REFUSE on 3.12+, contradicting E-01's refusal row and turning one CI leg red. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires refusing `ipv4_mapped` before `is_loopback`, records a demonstrated shape, and V-03 demands the binding run on a pre-3.12 and a 3.12+ interpreter (or an explicit statement that only CI 3.9 proves it). |
| PR-002 | MEDIUM | IN-SCOPE | D. Unexplained behavior change | same function, probe at `76faafbc2` | `127.0.0.1:8080` and `127.1` hold today only via the prefix disjunct and silently flip under E-03; the plan's holding set and refusal rows did not mention them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 adds both as refusal rows (red before E-03) plus `LOCALHOST`/`127.0.0.0/8` holding rows; E-03 requires naming the flip in the diff comment; E-02/V-02 counts updated from four to six. |
| PR-003 | HIGH | UNDER-SCOPE | B. Security, honest documentation | `agent_workflows/security_hardening.py:242` `check_evidence_redaction`; `docs/security.md` boundary 4 "if a secret survives, it fails closed" | Stage 2 runs only the identifying-info sanitizer, never the secret scanner, so a credential under a non-sensitive key holds and `run_task` admits it. E-07 would leave the false boundary 4 claim in the document it is already editing. | C:Low; U:Low; S:Low; F:Low; Overall:Low (doc fix); code fix Medium-High on functionality | FIXED | E-07/V-07 now correct boundary 4 wording (in declared scope). The code change is deferred with carrier `lfko0e` (false-positive risk on admission is a design decision); F-15 and a Deferred row record it. |
| PR-004 | MEDIUM | IN-SCOPE | E. Testing, reachability | `agent_workflows/host_runner.py:224` `redact_worker_output` payload keys `stdout`/`stderr`/`diff`; `security_hardening.default_redaction_policy` | E-06 required asserting that "a secret in a sensitive position is masked in the returned result", which is unreachable: no payload key is sensitive and the policy has no value patterns. The executor would have had to fabricate a test or fail the item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06/V-06 now pin detection on `redact_worker_output` and the actual refusal on `run_task` (runner double), and forbid a masking assertion. F-16 records the measurement. |
| PR-005 | LOW | IN-SCOPE | G. Evidence citation | E-06 "WIRED INTO PRODUCTION (F-06)" | E-06 cited F-06 (the docs finding) for the wiring claim, which is F-09, and called an uncalled path "production". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Citation corrected to F-09, and E-06 states `run_task` has no package caller. |
| PR-006 | MEDIUM | IN-SCOPE | E. Testing, vacuous control | E-04 expected outcome `'/home/<some-user>/secret/path'`; `agent_workflows/leak_sanitizer.py:67` `home-path` regex excludes `<` | The literal planted path in E-04's expected outcome HOLDS under the sanitizer, so copying it would make the redaction refusal row pass for the wrong reason or fail; a real literal would trip the `local-leaks` hook. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 and E-06 require a runtime-built home path with an alphanumeric probe user, as the recovered file did. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should IPv4-mapped loopback be accepted after the fix? | Refuse on every interpreter (matches today's verdict on the dev interpreter and E-01's pinned row). | Accept via `ipv4_mapped.is_loopback`; leave interpreter-dependent. | Plan's own Deferred row declining `::ffff:` acceptance; probes on 3.9/3.11/3.12/3.14. | yes |
| D-2 | Should `127.0.0.1:8080` and `127.1` keep holding? | Refuse (fail-closed; neither is a bind host literal). | Special-case port stripping or inet_aton shorthand. | No caller exists (F-09/F-16); the module's contract is "refuses a routable address". | yes |
| D-3 | Fix the missing secret-scan stage here or defer? | Correct the doc in scope, defer the code to `lfko0e`. | Wire `scan_text_for_secrets` into stage 2 now. | Functionality risk (false-positive refusals); `host_runner.py` outside Scope-Paths. | yes |
| D-4 | Pin `redact_worker_output` masking or the `run_task` refusal? | Pin detection plus `run_task` refusal. | Keep the unreachable masking assertion; extend scope to `host_runner.py`. | `host_runner.redact_worker_output` payload construction; `run_task` probe. | yes |
