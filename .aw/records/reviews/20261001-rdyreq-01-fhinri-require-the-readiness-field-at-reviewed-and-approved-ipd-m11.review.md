# Review findings: plan fhinri

- Subject-Id: fhinri
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `fe2ee961c` in an isolated review lane. The plan was committed and byte-identical to the lane input,
so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review. After
revision, `--phase review-finalize` was conforming with no advisories (after the E-07/E-08 split).

Reproduced (gitignored probes under `.aw/state/`, with no production edit):
- Imported `C_*` census for `IPD-M*` runs M101..M112. `C_COVERAGE_RECORD = "IPD-M112"` (gradcover `qs00nc`).
- 1313 tracked `.ipd.md`, 1164 legacy/quarantined. Partition: `to-review` 47 absent, `reviewed` 12 present,
  `approved` 50 present, `draft` 40 absent. A Status-keyed rule would fire on 0 plans at all five checkpoints.
- `to-review` AND `history_has_review_record`: 2 (`qpw45x`, `q4uifc`). Each carries a `/plan-review APPROVE WITH
  REVISIONS APPLIED` record; commit `8c460a9a1` removed their `- Readiness:` lines (and their status reads `to-review`).
- R6 paragraphs in `plan-review.md` and in `plan-review-long/02-review-and-revise.md` / `03-resolve-and-finalize.md`
  all state that the plan "remains `- Status: to-review`".
- Scratch repository: `aw ipd set approved 62pkkg --by-human --allow-open-questions` on a `to-review` copy succeeded
  and wrote `- Approval:` with no `- Readiness:`; `aw ipd lint` then reported `clean`.
- `validate_transition('to-review','approved',actor='human')` returns `ok=True`.
- `l34oi2` graduated to `l56tyz` (`approved`), which declares the same four prose files.
- Spec `ipd-structure-and-linting`: zero `Readiness` mentions; Section 10 rule 20 is `IPD-M112`; no `IPD-M110`/`M111`.
- `pytest tests/test_spec_review_attestation.py tests/test_ipd_lint.py tests/test_ipd_schema.py -o addopts=""`:
  `1 failed, 129 passed`. The failure is `ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta`
  (`livecorpus`, pre-existing, unrelated).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness | `agent_workflows/ipd_lint.py` `C_COVERAGE_RECORD = "IPD-M112"`; `tests/test_orchestrator_readiness.py` | The plan named its new code `IPD-M112`, which another rule has since taken. Executed as written, it would collide with or shadow an existing rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Renumbered to `IPD-M113` throughout. E-01(d) still re-derives the number by import. |
| PR-002 | HIGH | IN-SCOPE | G. Executability | Probe: 2 `to-review` plans with a review record | The authored stop condition (c) ("to-review with a review record, expected 0, else STOP") fires today. It would halt execution, yet those plans are outside the gated set, so they confirm the design rather than refute it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | (c) is now context, with the two plans explained. A new (c') counts plans at a gated status whose newest review is non-concluding, which is the measurement that would actually void the decision. |
| PR-003 | MEDIUM | UNDER-SCOPE | D/F. Invariants, UX | Scratch-repo `aw ipd set approved --by-human` result; `validate_transition` | The plan did not consider a human approving an unreviewed plan directly. That path produces `approved` with no Readiness, so after this plan `aw ipd begin` refuses it. | C:Low; U:Medium; S:Low; F:Low; Overall:Medium | FIXED | Added E-01(e) to measure the path and E-03 message text that explains the review requirement. New OQ-03 resolves it as a deliberate, reversible tightening. Added an E-05 table row. |
| PR-004 | MEDIUM | IN-SCOPE | E. Testing | `pyproject.toml` `livecorpus` marker definition | The E-06 corpus sweep was unmarked, so any agent's plan could red the default suite and block every lane's merge. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06/V-06 now require `@pytest.mark.livecorpus` and a `-m livecorpus` run. The induced failure must leave a clean `git status`. |
| PR-005 | LOW | IN-SCOPE | G. Spec sync; right-sizing | Spec Section 10 rule 20; `IPD-Z602` advisory on E-07 | The spec claimed M109/M110/M111 recorded themselves in Section 4.4. M110/M111 do not appear at all, and lint rules are enumerated in Section 10. E-07 also bundled the prose fix with the spec amendment. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-08/V-08, which amend Sections 4.4 and 10. The pre-existing M110/M111 gap is noted, not closed. |
| PR-006 | LOW | IN-SCOPE | E. Verification | `test_corpus_verdict_neutrality_delta` failing | The suite bar was a bare pass against a non-green base. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline is re-derived and failure sets compared by name. The pre-existing `livecorpus` failure is named. |
| PR-007 | MEDIUM | IN-SCOPE | G. Execution contract | Approval and execution gate | No paste-output rule, scope fence, conditional finalize ownership or Readiness-ownership statement. The STOP wording mixed unsafe-condition stops with scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten. Unsafe-condition stops now mark the dependent E-items `blocked`. |
| PR-008 | MEDIUM | IN-SCOPE | C. Duplicate paths | `.aw/records/plans/pending/*l56tyz*` (`approved`) declaring the same four prose files | E-07 did not coordinate with `l56tyz`, which corrects the same four claims and narrows the absent arm. Two layered corrections would conflict. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07/V-07 now check whether `l56tyz` landed and state which case applied, so the end state is one sentence per file. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should a human's direct approval of an unreviewed plan be refused at `aw ipd begin`? | Yes, as a deliberate tightening (OQ-03) | Exempt `approved` plans carrying a human `- Approval:` (reopens the hole for every hand-approved plan) | Plan Goal; AGENTS.md lifecycle `to-review`->`reviewed`->`approved`; zero live plans affected (probe) | yes |
| D-2 | What should replace the authored R6 stop condition that fires today? | Keep (c) as context and add (c'): gated-status plans whose newest review is non-concluding | Keep (c) as a STOP (halts on plans that confirm the design); drop the check | Probe of `qpw45x`/`q4uifc`; R6 paragraphs in both workflow bodies | yes |
| D-3 | Which code number? | `IPD-M113`, re-derived by import at execution | Keep M112 (collision) | `ipd_lint` `C_COVERAGE_RECORD` | yes |
