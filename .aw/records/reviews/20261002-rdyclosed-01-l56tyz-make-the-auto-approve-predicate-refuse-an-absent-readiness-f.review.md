# Review findings: plan l56tyz

- Subject-Id: l56tyz
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `5aecd7fb1`. The plan was committed and byte-identical to the lane input, so no pre-review
snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and
`--phase review-finalize` was clean after revision.

Re-verified with gitignored scratch probes under `.aw/state/`, run against the lane's own package:
- `plan_readiness.is_plan_review_approved`: the field arm calls `history_has_review_record`; the absent-field arm
  calls only `history_verdict_approves(extract_newest_history_entry(text))` plus the blocking-question check.
  Confirmed as cited.
- In-memory truth table over field-less plans (base / any-record guard / newest-record guard):
  to-review mentioning APPROVE True/False/False; draft APPROVE True/False/False; narrated predecessor True/False/False;
  genuine `/plan-review APPROVE WITH REVISIONS APPLIED` True/True/True; `reviewed (aw set): /plan-review ...` True/True/True;
  genuine `/plan-review REJECT - NEEDS REPLAN` with newer `to-review (agent): now APPROVE` **True/True/False**.
- Corpus: 1266 tracked `.ipd.md`; exactly one fallback-decided plan, `920qnm` (executed), whose newest record is a
  review record, so both guards flip 0.
- Probe with the newest-record guard monkeypatched in-process (`-o addopts=""`, call counter 4) over
  `test_readiness_absence_invariant.py`, `test_oc_runipd.py::AllSelectorAndFullAutoTests`, `test_agy_runipd_cli.py`,
  `test_review_record_classifier.py`, `test_status_set_descriptive_safety.py`: `1 failed, 101 passed`.
- That one failure, `test_corpus_partition_pre_review_plans_lack_readiness_field`, also fails on an UNMODIFIED tree
  (`1 failed, 3 passed` for the file): four pending plans (`42ertq`, `5eygjt`, `5xq2ng`, `685iq8`) carry
  `- Readiness: go-pending-approval` at `- Status: to-review`.
- Spec `r07vma` R6 and step 7 state only the instruction (leave the field absent), not the fail-closed rationale, so
  the plan's "no spec amendment" claim holds.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | B. Security (gate forgery) | `agent_workflows/plan_readiness.py` `is_plan_review_approved` absent-field arm; `history_has_review_record` (any-record rule) | The prescribed fix guards the fallback with the ANY-record `history_has_review_record`, but the fallback reads its verdict from the NEWEST record. A field-less plan whose genuine review said `REJECT - NEEDS REPLAN` and whose newer non-review record contains `APPROVE` is True today and stays True under the prescribed fix; under `--full-auto` that promotes a rejected plan to an execute tier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires `is_review_history_entry` on the newest record (the one whose verdict is read); Scope, E-01(b), E-02 Probe B, E-04 (fourth forgery row), V-03, Proposed change 3, OQ-02, F-12 swept; new F-13 records the measurement. |
| PR-002 | MEDIUM | IN-SCOPE | E. Baseline attribution | `tests/test_readiness_absence_invariant.py::test_corpus_partition_pre_review_plans_lack_readiness_field` | A fourth pre-existing failure sits in this plan's own target file (live-corpus property 1, broken by other lanes' records), so V-04's "passing" run and E-06's three-failure baseline were unsatisfiable as written. | all Low | FIXED | New F-14; E-06 compares failure sets by node name; V-04 requires showing it fails identically on the baseline. |
| PR-003 | MEDIUM | IN-SCOPE | G. Execution contract | Approval and execution gate | No scope-fence declaration (with `--scope-reason`/`--scope-ack`, relevant because `fhinri` may already have edited the prose files) and no runner-vs-hand finalize ownership. | all Low | FIXED | Gate paragraph added; the two existing stop conditions are legitimate premise-voiding stops and were kept. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which provenance rule for the fallback arm? | Newest record must be a review record (`is_review_history_entry`). | Any-record `history_has_review_record` (authoring choice). | In-memory truth table above; corpus flip 0; predicate's docstring accepts false negatives. | yes |
