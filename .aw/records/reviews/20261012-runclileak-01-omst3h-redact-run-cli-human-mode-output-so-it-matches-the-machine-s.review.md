# Review findings: plan omst3h

- Subject-Id: omst3h
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `d1dfd6295`. The pending plan matched the sealed lane input byte for byte and was already committed, so no snapshot was needed. `aw ipd lint --phase author` reported `clean`. `- Kind: child`.

Verified symbols:
- `run_cli._redact_output` (regex `ghp_[A-Za-z0-9]{20,}|Bearer\s+...` plus key-name masking) is called only from `_emit_machine`.
- `_emit_error`'s human branch is `print(f"error: {message}")`.
- `_run_evidence` prints `Command: {item.get('argv')}` raw.
- The module docstring bullet "Redacts sensitive values in both human and machine outputs." is present.
- Every listed `print(` site exists. The six cited test modules exist; `tests/test_run_cli_ledger_message.py`, named only inside a quoted docstring, does not.
- Backlog `94op6l` carries `Blocks-Release: next`. `h9kgjp` is in `backlog/done/`.

Security lens: the fix is output-only masking, idempotent on `[REDACTED]`, and changes no exit code. It does not alter what lands on disk, and the plan states that.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | B security / D invariant | `agent_workflows/run_cli.py:127` `_run_decisions` and `:141` `_run_questions` print unconditionally with no machine branch. Review loop: `runs decisions <ghp-path> --agent` token count 1, `questions --agent` count 1 | The plan's F-3 and V-01 asserted `--agent` 0 only for six leaves, and treated `decisions`/`questions` as human-only. These two leaves leak on the MACHINE surface too, and no test covered it. E-01's routing closes it, but nothing proved that. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now drives both leaves in human AND `--agent` mode. Added F-6. V-01 now measures human and `--agent` counts on all twelve leaves. |
| PR-002 | MEDIUM | UNDER-SCOPE | E coverage | Review loop: `run start|record|cancel|finalize <ghp-path>` each print the token at exit 2 with no extra arguments | The scope check left writer coverage conditional ("if the executor finds..."). The writers are reachable, so the condition is already met and the cases are required. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires the four writer cases, with an exit-code-unchanged assertion. The scope check has been updated. |
| PR-003 | MEDIUM | IN-SCOPE | E feasibility | Review rehearsal: a minimal `RunLedgerStore.append` is refused with `RL-E010`/`RL-E014`/`RL-E015`/`RL-E034`. `tests/test_run_cli_declarations.py` `_create_valid_one_record_ledger` shows the accepted shape | E-03 named only the kind-specific fields. An executor following it literally gets `SchemaInvalidRecordError`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now names the common fields and the bare-hex `stdout_sha256`. Added F-7, which records the rehearsal: the token is on disk, the human output leaks it, and `--agent` shows `[REDACTED]`. |
| PR-004 | MEDIUM | UNDER-SCOPE | G lifecycle gate | Pre-transition lint: `check.ipd-uncarried-obligation: 5 obligation(s) name no durable carrier` | Four deferred rows and OQ-01 had no carrier, so finalize would refuse. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `Carrier-Declined` with reasons to four of them. `h9kgjp` got `Carrier-Evidence` pointing at its done record. The uncarried count is now 0. |
| PR-005 | LOW | IN-SCOPE | G execution contract | Original gate | The gate instructed `aw ipd begin`/`finalize` unconditionally, with no runner ownership, no scope fence, and no guard on the pre-fix comparison state. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote it as EXECUTION CONTRACT, SCOPE FENCE, and POST-GATE LIFECYCLE. |
| PR-006 | LOW | IN-SCOPE | Plan contract | OQ-01 `- Owner: maintainer` on a deferral the author made | The owner claim was false: the maintainer did not answer this question. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set to `plan author`. Added the observation that the home-path rule in `docs/cli-output-contract.md` binds `aw.agent/v1` envelopes, and these payloads are not `aw.agent/v1`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should `decisions`/`questions` gain a structured machine payload instead of redacted text? | No. Route them through the same redacting helper and assert no token in both modes. | Add a JSON payload for both leaves. | The plan forbids changing machine payload shapes; redaction alone closes the measured leak. | yes |
| D-2 | Keep OQ-01 (home-path redaction) deferred? | Keep it deferred, as declined. | Apply home-path redaction to human output. | No credential is involved, and the machine side does not do it either (plan OQ-01). The contract doc binds `aw.agent/v1` only. | yes |
