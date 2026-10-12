# Review findings: plan o58r3r

- Subject-Id: o58r3r
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `b41952ca2`. The pending plan matched the sealed lane input byte for byte and was committed, so no snapshot commit was needed. `aw ipd lint --phase author --agent` and `--phase review-finalize --agent` both reported `clean`. `- Kind: child`.

Re-measured: the E-01 `rg` census returns exactly the seven F-01 lines (oc/agy `run_queue`, `refuse_undispatchable_typed_entry` x2, the two exhaustion constants, `BOUND_EXPIRY_DISPOSITION`), and the runtime probe prints `failed-safely failed-safely failed-safely False fail-gate ['failed-safely'] True`, matching F-02. All eight specs named in Scope-Paths exist, and they are exactly the set `rg -l "no longer written by the runner"` returns. All eight are `specs check` clean. `aw specs note` was exercised on scratch copies and appends exactly one line. Cells (a), (b), (c), (d), (f), (g) of E-05 were driven once against the real functions with no file changed (recorded as F-08 in the plan). Option (b) is well supported: `turn_failure_is_retryable({}, 'fail-gate')` is `False` and approved plan `ytas91` writes `failed-safely`.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | D (spec truthfulness) | `25kzda` 5.5 table row "fix-it budget exhausted \| `fail-gate`, `budget_exhausted`"; `runner_shared.TURN_RETRY_EXHAUSTED_STATUS` / `FINALIZE_RETRY_EXHAUSTED_STATUS` = `failed-safely`; no `budget_exhausted` producer in `agent_workflows` | The plan corrects the spec about `failed-safely` writers but left the 5.5 table row that names a different, unwritten token for the two exhaustion writers, so the contradiction would survive inside the new paragraph's own table. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 adds item (5), changes that one Disposition cell, and explains why an exhausted `failed-safely` is not retried by the turn predicate. V-02 and the expected outcome were updated. Added F-09. |
| PR-002 | MEDIUM | IN-SCOPE | A (correctness of the normative rule) | `runner_shared.outcome_precedence_disposition(None, {'disposition': 'failed-safely'})` -> `fail-gate` (review probe); `build_prompt` outcome schema offers `failed-safely` | E-02's "MUST key on the raw token, never canonicalize" rule would contradict shipped code that deliberately canonicalizes an AGENT-recorded `failed-safely` (a self-claim) to the non-retryable `fail-gate`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 (1) now states that the agent-recorded token is canonicalized by design and that the raw-token rule governs runner-written tokens. |
| PR-003 | LOW | IN-SCOPE | E (test robustness) | E-05 (e), (h) | Cells (e) and (h) could hard-code the literal and then pass vacuously after a migration. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | (e) reads the token observed in (a). (h) cross-checks (b), (c), (d) and the finalize constant against it. (a) records the measured `run_queue` return. Added F-08 with the demonstration. |
| PR-004 | LOW | IN-SCOPE | G (honest ownership, validation precision) | OQ-01 `Owner: maintainer (confirms at approval)` though the plan author resolved it; E-06 whole-tree `specs check` | A false `Owner: maintainer` on an author-resolved question is the anti-pattern plan-review 3.1(5) names. Also, the whole-tree `specs check` cannot show that the eight touched specs conform. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owner changed to `plan author (the maintainer confirms or overturns at approval)`. E-06 and V-06 now run `specs check <path> --agent` once per touched spec. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should the review also correct the 5.5 `fix-it budget exhausted` row? | Yes, one Disposition cell, inside this plan's already-declared spec path. | Leave it and file a backlog item (it would leave a contradiction in the very table the new paragraph cites). | `runner_shared.TURN_RETRY_EXHAUSTED_STATUS`, `FINALIZE_RETRY_EXHAUSTED_STATUS`; `rg budget_exhausted agent_workflows` returns no producer. | yes |
| D-2 | Does the raw-token rule apply to agent-recorded `failed-safely`? | No; scope it to runner-written tokens and document the canonicalization. | Apply it universally (contradicts `outcome_precedence_disposition`'s anti-self-claim design). | `runner_shared.outcome_precedence_disposition` docstring rung 3 and review probe. | yes |
