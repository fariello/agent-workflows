# Review findings: plan 5jevb2

- Subject-Id: 5jevb2
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was byte-identical to the lane input and committed unchanged (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 5), test-only, one declared path (absent at HEAD).

Verified in the lane (no production file edited; scratch test copy removed):
- `19313eed^:tests/test_run_packet_gates.py` (756 lines) has classes `TestStepPacketRendering`, `TestOutcomeEnvelopeLegality`, `TestHumanDecisionGates`, `TestStepPacketEdgeCases` and the named tests; under pytest at the lane HEAD: `20 passed in 0.70s`.
- All 10 keys exist in `agent_workflows/run_packet.py`. `tests/test_core_module_coverage.py::test_run_packet_envelope` is the only surviving caller, as F-01 says.
- Direct calls reproduced E-02 to E-06: contract fields, `scope_fence`, `trace == {"S-01": ["R-01"]}`, wrapper unwrapping, tools default, digest round trip and sensitivity, all binding branches, compact JSON, key shape, budget error hierarchy, exact `to_dict` shapes, all 10 rejection codes with the stated `where`/`envelope is None`, controls, and `apply_outcome_envelope` appending exactly `['step_attempt', 'artifact_ref']` (path `output.txt`). Every fail-closed row raises the stated type with record count and `running` state unchanged.
- Backlog `ziuj5c` (run_gates) exists. Bare `python3 -m pytest` at the lane HEAD: `753 passed in 43.70s` with `CORE TIER BUDGET EXCEEDED` (backlog `o58dro`, a release-gated bug).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Testing (flaky, weak digest test) | `run_packet.build_step_packet` puts `ts` in `payload_for_digest`; `19313eed^:tests/test_run_packet_gates.py` `test_packet_digest_changes_when_bound_requirement_changes` builds without `timestamp` | The deleted test's builds carry wall-clock timestamps that feed the digest (measured: builds 1s apart differ). Restored verbatim, the stability assertion flakes across a second boundary, and the sensitivity assertion passes from clock drift even if a mutant ignores the requirement text. E-03(a) pinned the timestamp only for the extra determinism check. | all Low | FIXED | E-03(a) pins the same explicit timestamp on EVERY build in the test and forbids the timestamp-less verbatim restore. |
| PR-002 | MEDIUM | IN-SCOPE | Testing (assertion cannot detect the mutation it targets) | `build_step_packet` raw branch: `_normalize` match, then fallback `frozen_must_items[idx]` | In the whitespace case, the positional fallback can bind the same item, so a broken `_normalize` would go unnoticed. The fixture (frozen set, `satisfies` position) was not specified. | all Low | FIXED | E-03(c) fixes the fixture: frozen `["first thing", "second thing"]`, raw text in position 0. A broken normalize then binds `first thing`. Added a `_normalize` identity mutation (Required tests, V-03). Also added the uncovered positional-fallback branch, measured. |
| PR-003 | MEDIUM | IN-SCOPE | Validation (bar is unmeetable for reasons outside the plan) | Required tests "within the 30s budget"; V-01 "core-tier wall time under budget"; measured `753 passed in 43.70s`, `CORE TIER BUDGET EXCEEDED` | The core tier already exceeds its budget on this host before any change (`o58dro`), so V-01 could never reach `pass`. | all Low | FIXED | The bar is now: every test passes, plus the module's own runtime under 1s. The budget line is reported against `o58dro`. |
| PR-004 | LOW | IN-SCOPE | Testing (assertion would fail on correct code) | `render_prompt` always emits `## Step Exit Checklist`; `## Allowed Scope & Tools` whenever default tools are non-empty | E-02 said the minimal packet renders "WITHOUT those optional headings" without naming them. The plan's own heading list includes two headings that are always present for that packet (measured). | all Low | FIXED | E-02 names the four headings that are absent and the two that remain. V-02's mutation is now a guard drop that this test catches; the old "emit every step's action" mutation could not be implemented without reshaping the function. |
| PR-005 | LOW | IN-SCOPE | Evidence accuracy | F-04 "ids are `M-01`, `M-02`, `SC-01`, `V-01`, `O-01`" | Measured: `M-01`, `M-02`, `M-03`, `SC-01`, `V-01`, `O-01`. | all Low | FIXED | F-04 corrected. |
| PR-006 | LOW | IN-SCOPE | Execution contract; worktree hygiene | gate paragraph; Reach command | The gate lacked the honesty rule, the staged-set check, scope-fence wording and finalize ownership. The Reach command writes `.coverage` into the worktree and offered two alternative commands. | all Low | FIXED | Gate rewritten. It also notes not to freeze the unpinned bare `KeyError` for an unknown step. Reach is now a single command with `COVERAGE_FILE` outside the repo. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Pin timestamps in the restored digest test even though it departs from the deleted source? | Pin on every build | Restore verbatim (flaky, weak) | `build_step_packet` `payload_for_digest` includes `timestamp`; measured | yes |
| D-2 | What is the V-01 bar while the core tier overruns on this host? | Every test passes, plus the module itself under 1s; the budget is reported | Keep the 30s bar (unmeetable); drop the timing evidence | measured `43.70s`; backlog `o58dro` | yes |
| D-3 | Test `apply_outcome_envelope` with an unknown step id? | No; leave it unpinned | Pin the bare `KeyError` (freezes possibly accidental behavior outside the typed hierarchy) | rubric D "do not freeze accidental behavior"; measured `KeyError` | yes |
