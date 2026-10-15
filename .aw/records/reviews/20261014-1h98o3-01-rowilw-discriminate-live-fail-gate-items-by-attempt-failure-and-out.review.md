# Review findings: plan rowilw

- Subject-Id: rowilw
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`74b723563`), so no snapshot was needed. `aw ipd lint --phase author` was clean before review. `--phase review-finalize` is clean after the revisions, with one info advisory (`IPD-Z602` on E-03): E-03 is one test module covering one function's producer shapes, so it was judged one concern. `--phase pre-transition` no longer reports `check.ipd-uncarried-obligation`.

Prototype: the revised E-01 helper was wired at all five call sites in a scratch copy under the gitignored `.aw/state/` (deleted afterwards). Ten adjacent test modules gave `159 passed in 30.77s`. Rendered words:

| Shape | Outcome word |
|---|---|
| crash exit 1 / exit 137 | `FAILED` |
| refusal-free executed claim | `COMPLETED` |
| same, with `integration_signal="suite-failed"` | `STRANDED` |
| same, with legacy `finalize_refusal` | `BLOCKED` |
| bare / clean-base / agent-`blocked` | `BLOCKED` |
| `[executed, crash]` | `FAILED` |

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness | `agent_workflows/render_stream.py:3289-3290` `@dataclass(frozen=True) class Refusal`; `render_stream.py:3525` `if not isinstance(item, dict): return None` in `refusal_of_item` | Proposed changes called `refusal.get("code")`, which raises `AttributeError` on a `Refusal` dataclass and would crash the run summary for every refused `fail-gate` item. The helper also accepted any `Mapping`, but `refusal_of_item` silently returns `None` for a non-dict, so a refused item could be scored SUCCESS. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 and Proposed changes now read `refusal.code` and pass a `dict`. E-03 adds a `MappingProxyType` case, and V-01 demands both. |
| PR-002 | HIGH | IN-SCOPE | G. Executability | `render_stream.py:4224-4310` ladder has no `all_failed` and no success-plus-skipped arm; `render_stream.py:3150-3155` defines no `OUTCOME_CLASS_SKIPPED`; five `RUN_OUTCOME_CLASS_BY_STATUS.get(it.get("status"))` sites | E-02 and Proposed changes 2 told the executor to rewrite arms that do not exist and to use a constant that does not exist. They also omitted the `INTERRUPTED` site and the `NO WORK PERFORMED` success test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now replaces every one of the five sites and forbids other ladder changes. The real ladder is recorded in Conventions. V-02 adds a no-remaining-site check. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing | review measurement: `[executed, failed-safely]` renders `FAILED`; the `FAILED` arm is `any(...)` | E-03(a) and Proposed changes expected `[executed, crashed fail-gate]` to render `PARTIAL`. The ladder renders `FAILED`, so the planned test would fail against a correct implementation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The expectation is now `FAILED`, and Findings row 1 is corrected. |
| PR-004 | MEDIUM | IN-SCOPE | D. Anti-regression | `tests/test_outcome_word_ladder.py` `test_case_a_word_table` shapes `[{"number": 1}]` without `exit_code`; `test_zero_dispatch_outcome.py:298` and `:455` pin `fail-gate` -> `BLOCKED`; Findings row 2 "`exit_code == 0` (or absent)" | Treating an absent exit code as success risks relabelling exit-code-less fixtures and records. Success also had no `action` guard, although review-action `fail-gate` items also carry `last_outcome`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Success now requires a recorded `int` `exit_code == 0` and `action == "execute"`. The existing word-table tests are named as unchanged pins, and the docstring/divergence-reason/`RULE:` wording is updated. |
| PR-005 | MEDIUM | UNDER-SCOPE | G. Lifecycle gate | pre-transition lint: `check.ipd-uncarried-obligation 1 obligation(s) name no durable carrier: deferred row 1` | The deferred row lacked a carrier, so the plan could never finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `Carrier-Declined` with its reason. The rule is cleared. |
| PR-006 | MEDIUM | IN-SCOPE | G. Execution contract | old gate "finalize through the runner or `aw ipd set executed rowilw`" | The gate offered a non-lifecycle transition and lacked the ownership split, honesty rule, scope fence, and never-push rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with the standard execution contract. |
| PR-007 | LOW | UNDER-SCOPE | G. Docs sync | `CHANGELOG.md` `## 2.0.0 (pending)` | A user-visible change to the run summary word had no release-notes line. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-04/V-04 and put `CHANGELOG.md` in Scope-Paths. |
| PR-008 | LOW | IN-SCOPE | E. Evidence accuracy | E-03(c) cited `SPEC-PLAN-LINT`; `rg` finds no such code (real: `SPEC-PLAN-COUNT`, `-SET`, `-TRACE`, `-CONFORMANCE`, `-GATE-CARRY`) | The test named a refusal code that does not exist. The V-03 bare run and the evidence demands were also thin. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Uses `SPEC-PLAN-COUNT`. The focused run is widened to the adjacent modules, and V-03 demands verbose output, the P16 assertion quote, and the bare-suite line. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does an absent exit code qualify as success? | No; a recorded `exit_code == 0` is required | Accept absent (relabels exit-code-less records and fixtures) | `execute_item_core` `attempt.update({... "exit_code": exit_code ...})` always records it for a run turn; `test_outcome_word_ladder` shapes | yes |
| D-2 | Expected word for `[executed, crashed fail-gate]`? | `FAILED` | `PARTIAL` (authored; contradicts the `any(...)` FAILED arm) | Review measurement on `[executed, failed-safely]` | yes |
| D-3 | Accept OQ-01 (finalize refusal BLOCKED, suite-failed STRANDED)? | Yes, as authored | Treat suite-failed as BLOCKED | Prototype rendering; `refusal_of_item` legacy `finalize_refusal` arm; `work_did_not_land` | yes |
| D-4 | Restrict success to the execute action? | Yes | All actions | Review turns also set `last_outcome`; the review `fail-gate` producers are gate refusals or nonzero exits | yes |
