# Review findings: plan v5m5y8

- Subject-Id: v5m5y8
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `1134a92b6` in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize` was clean after revisions.

Re-verified:
- `backlog.validate_item` has no history rule; consumers are `backlog.run_check`, `check_engine` record type `backlog`, `set_records.promote` (validates before write), and `runner_shared` run-structure preflight.
- Prerequisite: `kgv213` is `reviewed` in `plans/pending/`; `attention_contract.history_block` does not exist at this HEAD.
- Live corpus: all 977 tracked `.md` files under `.aw/records/backlog` probed; only `README.md` (excluded by `_iter_items` and `check_engine._SKIP_NAMES`) lacks a column-zero record.
- Regression probe: the bare suite run with `validate_item` monkeypatched to add the rule gave `2 failed, 7279 passed, 2 skipped`; both failures are `tests/test_check_engine.py` fixtures without a history block. Both pass unpatched (`tests/test_check_engine.py`: `50 passed`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Anti-regression | `tests/test_check_engine.py:801` `_BKLG_OPEN`/`_BKLG_DONE`; `tests/test_check_engine.py:1604` `bkl111` row; probe `2 failed, 7279 passed` | The plan assumed the rule breaks nothing because the live corpus is clean, but two existing check_engine tests use backlog fixtures with no `## Workflow history` and would fail. `tests/test_check_engine.py` was not in Scope-Paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-04, E-05/V-05 (repair fixtures without changing any expected set; re-derive any other breakage via the bare suite), and the path to Scope-Paths. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness / G | `backlog.validate_item` (no registry entry for sibling shape rules); `check_engine._DEFAULT_RULESPEC` = `error` | E-01 did not state the rule's severity or whether to register it. | all Low | FIXED | E-01 says do not register; default `error` is the intended fail-closed severity; the consumer consequence is stated. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing | E-02 cases (a)-(e) | No case proved a real writer's output passes the rule (the Step 0 claim) and `check_engine`'s path was untested; the two empty-shape details were not asserted distinct. | all Low | FIXED | E-02 adds (e) `backlog new` output is clean and (g) `aw check backlog` path; (b)/(d) assert distinct details. V-02 demands per-case pinning evidence. |
| PR-004 | MEDIUM | IN-SCOPE | G. Prerequisite / execution contract | `## Approval and execution gate` | The prerequisite check named only `history_block`, with no paste demand; the gate lacked OQ status, scope-as-declaration, `aw ipd begin`, staged-set check, never `--no-verify`, and the executor-must-not-finalize-under-a-runner rule. | all Low | FIXED | E-01 and V-01 check and paste both prerequisite facts; gate rewritten. |
| PR-005 | LOW | UNDER-SCOPE | F. UX / documentation | `agent_workflows/cli.py:517` backlog check description | `aw backlog check --help` enumerates the rules it enforces and would omit the new one. | all Low | FIXED | Added E-06/V-06 and `agent_workflows/cli.py` to Scope-Paths. |
| PR-006 | LOW | IN-SCOPE | Evidence | F-02 "967 tracked `*.backlog.md`"; `git ls-files .aw/records/backlog` | F-02's glob missed one tracked item not named `*.backlog.md` that `_iter_items` (`*.md`) validates; OQ-01 had `Owner: none`. | all Low | FIXED | Added F-05 with the 977-file re-measurement (still zero violators); OQ-01 owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the new rule be registered in `RULE_REGISTRY` with a non-default severity? | No; default `error` | Register as `warning` (same exit consequence) or `info` (would not refuse) | `check_engine._DEFAULT_RULESPEC`; Goal says the defect must be caught, not merely reported | yes |
| D-2 | Fix the breaking fixtures, or narrow the rule so they pass? | Fix the fixtures (add one history record) | Exempt items with no heading (defeats OQ-01's resolution) | probe output; OQ-01 | yes |
