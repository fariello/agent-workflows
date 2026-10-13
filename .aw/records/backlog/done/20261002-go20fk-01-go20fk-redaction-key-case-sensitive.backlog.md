- Id: go20fk
- Status: done
- Graduated-To: go20fk
- Set: go20fk
- Priority: medium
- Work-Kind: security
- Summary: RedactionPolicy sensitive-key match is case-sensitive, so an uppercase secret key is never masked

## Workflow history
- 2026-10-13 done (aw backlog): closed by aw agy run: IPD pbl020 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261012-go20fk-01-pbl020-case-fold-redactionpolicy-sensitive-key-matching.ipd.md); evidence .aw/records/plans/executed/20261012-go20fk-01-pbl020-case-fold-redactionpolicy-sensitive-key-matching.ipd.md
- 2026-10-12 graduated (aw backlog): graduated by run run-20261012T005606Z-2321569: pbl020
- 2026-10-02 created (aw backlog): filed from mflqqf plan authoring; measured at HEAD 4fbbc8386

Measured at HEAD 4fbbc8386 while authoring plan gqyold (backlog item mflqqf).

agent_workflows/run_ledger_store.py RedactionPolicy._redact_value tests `parent_key in self.sensitive_keys` against a frozenset of LOWERCASE key names, with no case folding. security_hardening.default_redaction_policy supplies that lowercase list (authorization, auth_token, token, api_key, apikey, secret, password, bearer).

Reproducing probe:
- pol.redact({'token': 's3cr3t'})  -> {'token': '[REDACTED]', 'redacted': True}
- pol.redact({'TOKEN': 's3cr3t'})  -> {'TOKEN': 's3cr3t'}        # NOT masked
- pol.redact({'nested': {'token': ...}}) -> masked (nesting is handled)
- pol.redact({'items': [{'token': ...}]}) -> masked (lists are handled)

So nesting and lists are handled correctly and CASE is not. A payload that spells the key 'Authorization' or 'TOKEN' passes redaction unmasked.

Why this is security rather than chore: the policy is the pre-append scrub that runs BEFORE records land in the run ledger, and host_runner.redact_worker_output calls it on captured worker stdout/stderr/diff. An unmasked secret therefore reaches durable run state. The leak sanitizer stage catches home paths and similar identifiers but is not a general secret masker, so the key match is the control that matters for a secret-bearing key.

Scope note: plan gqyold deliberately does NOT fix this. It lives in run_ledger_store.py, outside that plan's declared Scope-Paths, and changing a shared redaction policy's matching is a behavior change for every ledger caller rather than test restoration.

Open question for whoever takes it: fold the key case (and decide whether to also fold the payload's keys) versus widening the declared key list. Folding is the smaller change and the one that cannot be forgotten when a new key spelling appears.
