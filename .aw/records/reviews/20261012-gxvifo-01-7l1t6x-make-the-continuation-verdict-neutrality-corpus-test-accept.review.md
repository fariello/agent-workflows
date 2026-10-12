# Review findings: plan 7l1t6x

- Subject-Id: 7l1t6x
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `fee276097`. The pending plan matched the sealed lane input byte for byte and was committed, so no snapshot commit was needed. `aw ipd lint --phase author --agent` and `--phase review-finalize` both reported `clean`. `- Kind: child`.

Re-measured with the lane package (`PYTHONPATH=.`, `AW_NO_REEXEC=1`). I confirmed the test body and its current exemption in `ContinuationSubfieldOutcomeTests.test_corpus_verdict_neutrality_delta` (`tests/test_ipd_lint.py:4109-4172`), the `@pytest.mark.livecorpus` decorator, and `_CONTINUATION_SUBFIELDS = frozenset(("Observed evidence", "Execution note"))`. A classification over 1441 plans with a multiset comparison found 555 delta pairs, all `removed-only-evidence`, with dispositions all `('error', 'error')`, zero duplicate messages, and zero advisory differences. The E-03 mutation (adding `Execution state`), applied in memory, ADDS diagnostics on `20260810-awphysical-12-pszk6x-...`, so the corrected predicate still goes red.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A (executability) | `agent_workflows/ipd_schema.py:1703-1714` `DISPOSITIONS` = conforming, quarantined, legacy/not evaluated, error | E-02(c) ordered dispositions as "conforming < warning < error using the `S.DISPOSITION_*` constants", but no warning disposition exists, so (c) could not be written as specified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | (c) is now "widened disposition equals one-line or is conforming", with an explicit note that no warning disposition exists. |
| PR-002 | MEDIUM | IN-SCOPE | E (predicate strength) | E-02 (a)/(b) phrased as "contains no message absent from" (set semantics) | Set semantics would accept a delta that doubles an existing diagnostic, or that removes one copy of a non-evidence message duplicated elsewhere. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now specifies a `collections.Counter` multiset comparison. I measured zero duplicate-message pairs on the corpus, so this does not change the expected pass. |
| PR-003 | LOW | IN-SCOPE | F (honest documentation) | Test docstring "(disposition, diagnostics) with continuation read equals the pair computed with one-line read"; plan Goal and OQ-01 cited "the docstring's property" | The docstring states strict equality, which the existing exemption already contradicts. The plan attributed the relaxed property to it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now rewrites the docstring too. Goal and OQ-01 now cite the inline comment. V-02 demands the rewritten docstring in the diff. |
| PR-004 | LOW | IN-SCOPE | A (shared checkout safety) / D (live-artifact bar) | E-03 `git checkout -- agent_workflows/ipd_lint.py`; F-3 "552" | The revert could discard a co-worker's edit. The 552 count is a live population (555 at review). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a clean-file precondition with an in-memory `mock.patch` fallback. F-3 now states the property as the bar and records both counts. Recorded the review's mutation measurement in E-03. |
| PR-005 | LOW | IN-SCOPE | G (execution contract) | Approval gate; OQ-01 `Owner: none` | The gate lacked the scope declaration, the paste-actual-output rule, the never-commit rule for the transient mutation, conditional finalize ownership and the backlog close. OQ-01 had no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate and set `Owner: plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should (c) compare dispositions given there is no warning disposition? | Equal to one-line, or conforming. | A severity order over all four dispositions (quarantined/legacy have no natural rank relative to error). | `ipd_schema.DISPOSITIONS`; review measurement shows every delta is `error -> error`. | yes |
