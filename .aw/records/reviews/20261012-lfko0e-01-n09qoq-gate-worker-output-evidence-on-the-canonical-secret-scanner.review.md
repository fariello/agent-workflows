# Review findings: plan n09qoq

- Subject-Id: n09qoq
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `548700461` in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified by driving the code:
- `check_evidence_redaction` runs only `leak_sanitizer.scan_text` (F-01). With `{"stdout": s}` it returns `ok=True` for each of the following, so all are admitted today: `AWS_SECRET_ACCESS_KEY=<AKIA...>`, `export AWS_ACCESS_KEY_ID=<AKIA...>`, `Authorization: Bearer <30 chars>`, and a `<NAME>_TOKEN=<12 chars>` assignment.
- `scan_secrets.scan_text(..., use_entropy=False, use_pii=False)` flags those as `aws-access-key-id` (high) plus `generic-secret-env` (low), `aws-access-key-id`, `bearer-token` (low), and `generic-secret-env`. It reports nothing for a 64-hex digest plus a 40-hex sha, and nothing for `contact someone@example.com from 10.0.0.1`. RULES categories are exactly `{pii, secret}`. Severity `low` must count (F-03 holds).
- The bearer-under-`authorization` row flattens to `authorization\n[REDACTED]\nstdout\nok\nredacted\nTrue`, and stage 3 reports nothing for it.
- `_finding_repr` reads `where` before `location`, so it yields `generic-secret-env@evidence`, NOT `@evidence:<line>`. `location` is `evidence:2` after flattening.
- `_load_scan_secrets` registers `aw_scan_secrets` in `sys.modules` before `exec_module`. A stub left there makes the next `.scan_text` raise `AttributeError`.
- `_compat.packaged_source_root()` returns None in a source checkout; `SYSTEM_DATA_RELATIVE = ("_data", ".aw", "system")`. `scan_secrets.py` is git-tracked, and `pyproject.toml` force-includes `.aw/system` into the wheel. The `build` package is importable.
- `run_task` refuses on `boundary.ok is False`. The only callers of `check_evidence_redaction` are `host_runner.redact_worker_output` and the tests.
- Baseline: `11 passed in 0.35s`. `0ev8cz` is `reviewed` and pending (dependency edge correct); its F-08 already accounts for this plan's E-06 (iii). `gqyold` is executed. `pbl020` is pending and touches no file here.
- `docs/security.md` item 4 carries the "not evaluated by this boundary today (backlog lfko0e)" sentence. `host_runner.py` and `security_hardening.py` contain no "not evaluated" today.
- `Work-Kind: security` is not in the default release-gating set (`bug`), so no `Blocks-Release` is required.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Evidence feasibility | `security_hardening._finding_repr` (`getattr(f, "where", getattr(f, "location", "?"))`); probe -> `generic-secret-env@evidence` | E-03 and V-03 required `generic-secret-env@evidence:1`. `_finding_repr` emits `@evidence` with no line, so V-03 was unsatisfiable as written. F-06 also misdescribed the format as `rule@location`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03, V-03 and F-06 now state `<rule>@evidence`. The E-01 and E-02 `startswith(rule + "@")` checks were already correct. |
| PR-002 | MEDIUM | UNDER-SCOPE | B. Security (fail-closed) / C. Operability | `security_hardening._load_scan_secrets` registers `sys.modules[name]` before `exec_module`; stub probe -> `AttributeError` | Only the LOAD was wrapped fail-closed. An exception raised inside `scan_text` would escape `run_task`, and a failed exec would leave a half-initialized module cached for every later call. The plan also did not forbid copying exception text (which could echo input) into evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now wraps load plus scan in one `except Exception`, records only `type(exc).__name__`, and pops `sys.modules` on exec failure. Added a second test case where `scan_text` raises. V-04 extended. |
| PR-003 | MEDIUM | UNDER-SCOPE | E. Testing (wheel path) | `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]`; `_compat.packaged_source_root` | The wheel fallback, which F-05 says prevents a `FileNotFoundError` on installed `run_task`, had no evidence that the scanner actually ships in the wheel. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 now requires building the wheel and listing `agent_workflows/_data/.aw/system/workflows/assess/tools/scan_secrets.py`. E-04 states why the fallback branch is not unit-tested. |
| PR-004 | LOW | IN-SCOPE | G. Live-artifact criteria | V-05 "expect 11 baseline plus the tests this plan added" and "collected-count delta ... equals the number of tests added" | Test counts were used as bars, and the E-01 rows are table rows, not tests, so the expected delta was ambiguous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05 now requires zero failed plus a by-name failure-list comparison. Counts are context only. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` "transition ... (`aw ipd` begin/finalize)" | The gate told the executor to run finalize unconditionally. It also lacked the OQ status line, the must-paste honesty rule, the scope-fence justification, the staged-set check, and a rule against pasting secret material into evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Finalize ownership is now conditional on runner versus hand execution, with no hand `git mv`. The missing elements were added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Change `_finding_repr` to emit `location` so findings carry a line? | No: correct the plan to the existing `@evidence` format | Edit `_finding_repr` (changes stage 2 and boundary-8 outputs other callers and tests read) | `security_hardening._finding_repr`; E-01's `startswith(rule + "@")` | yes |
| D-2 | Fail closed on a scan-time exception too, not only on load? | Yes, one `try` around load and scan | Let scan exceptions propagate (a traceback out of `run_task` instead of a recorded refusal) | `docs/security.md` "fails closed"; OQ-03 | yes |
