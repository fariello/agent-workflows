- Id: 1vd74h
- Status: open
- Set: sbh1o1
- Priority: low
- Work-Kind: chore
- Summary: Decide whether check.spec-anchor-stale should gate, and wire it where a gate actually runs

## Workflow history
- 2026-10-02 created (aw backlog): Filed by /plan-review of atpvao, which descoped its promotion items E-05/E-06 because mt54wr OQ-01 (Owner: maintainer, open) reserves the gating decision to the maintainer and says promotion is a separate follow-on. Measured 2026-10-02 at e75cde645: (1) bare aw check specs ALREADY exits 1 on an unrelated finding (89xjll Scope), so 'bare check specs exits 0 on the swept tree' is unsatisfiable today; (2) CI never runs aw check specs (tests.yml runs specs check and check plans/releases/backlog/release-gates), so wiring the rule into bare check specs gates nothing in CI; (3) the detector costs about 3.5s user CPU versus about 0.6s for bare check specs, a user-perceptible slowdown if made default; (4) after the 25kzda sweep the detector still reports check_engine.py:353 (spec pqsx96 :135, a valid I-07 table-row citation it cannot recognize), so the census is not zero; (5) the detector misses anchors in comment/docstring blocks that do not name the id6 (runner_shared RUN_POLICY_FLAGS comment, evaluate_unverifiable_admission, run_evidence AggregatedItem). Each must be answered before a promotion is honest.
