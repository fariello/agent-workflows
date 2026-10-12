# Review findings: plan pbl020

- Subject-Id: pbl020
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `46d887d1e` in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review. After revisions, `--phase review-finalize` was conforming with one info-level `IPD-Z602` advisory on E-05, accepted: its three "clauses" are the arrange/act/assert steps of a single test.

Re-verified:
- F-1/F-2/F-4: `RedactionPolicy.__init__` stores `frozenset(sensitive_keys)` and `_redact_value` tests `parent_key in self.sensitive_keys`. The default key list is all lowercase. The only constructors are `security_hardening.default_redaction_policy` and tests.
- The defect is live: `default_redaction_policy().redact({'TOKEN':'s','Authorization':'b'})` returned both unmasked with `was_redacted` False.
- A probe of exactly the E-02 edits (exec'd module copy, nothing written) masked `TOKEN`, `Authorization`, nested `PASSWORD`, list `Secret`, `X-Api-Key` configured vs `x-api-key` payload, and a list value under `token`; `stdout` and an int key `3` were untouched with no exception.
- The three named suites pass at base: 39 passed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E. Testing | `run_ledger_store.RunLedgerStore.append_held` (`active_policy.redact(rec_to_write)`); plan E-01 | The Concern is about the run ledger, but every planned test is a unit call on `redact`. Probe: a ledger with `default_redaction_policy()` wrote `Authorization: Bearer s3cr3t` raw to the file while masking a lowercase `token`. | Overall: Low | FIXED | Added E-05/V-05: an end-to-end ledger test using the schema-valid seed shape from `tests/test_capture_command_contract.py`, failing on base. Added F-6 and F-7. |
| PR-002 | LOW | IN-SCOPE | D. Anti-regression | plan E-02 expected outcome "non-string keys ... no longer risk an AttributeError path" | This was misleading: the old membership test never raised on an int payload key. The new `.casefold()` call is the risk, and the `isinstance` guard is what prevents it. Configured non-string keys now raise at construction, which went unstated. | Overall: Low | FIXED | Reworded E-02 and added an int-key and a list-under-key case to E-01. |
| PR-003 | LOW | IN-SCOPE | E. Testing | plan E-03/V-03 "zero failures" | The bare-suite bar had no baseline and omitted the `RunLedgerStore` test modules, which exercise the changed class. | Overall: Low | FIXED | E-03/V-03 now take a same-session baseline and include modules found with `grep -ln RunLedgerStore tests/`. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | plan gate | The gate lacked the open-question status, `aw ipd begin`, the scope-fence declaration, and the MUST-paste wording. It also offered `aw ipd set executed` as an alternative and did not split runner and manual finalize. | Overall: Low | FIXED | Gate rewritten. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should a non-string configured key be tolerated? | No: it raises at construction (the type is `Sequence[str]`; a misconfigured security policy should fail loudly) | Coerce with `str(k)` (silently masks a key nobody spells) | `RedactionPolicy.__init__` signature; all in-tree constructors pass strings | yes |
| D-2 | Is `Blocks-Release` required on this security item? | No: `release_gate_work_kinds` is unset, so the default gating set is `bug` only | Add `Blocks-Release: next` (a maintainer prioritization call, not a review fix) | `.aw/config/project.json` has no `release_gate_work_kinds`; AGENTS.md "Every live bug gates the next release" | yes |
