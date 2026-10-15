# Review findings: plan uiej2a

- Subject-Id: uiej2a
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `70179b555`. The plan was committed and unchanged (`60bc401cc`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize` clean after revisions.

Re-verified at review HEAD:
- `production_checks.parse_spec_requirement_ids` on `89xjll` returns `R-1`..`R-9` and `AC-1`..`AC-10`; `parse_spec_id_markers` returns `{}` (no `[Deferred]` id, so E-02's gate will not block E-05).
- `production_checks.spec_plan_trace_deferred` has zero callers in `agent_workflows/`; `spec_plan_trace_vacuity` is called at `runner_shared.py:40852`, before the correction loop, and is not re-run inside the loop (`runner_shared.py:41046` re-runs `spec_plan_trace` only).
- `build_spec_production_prompt` `implementing` branch carries item 8; the `approved` branch does not.
- `status_set.validate_transition_allowed` specs arm: `if auth.get("evidence"):` at :798; `->implemented` authority `evidence: True`, `->implementing` executor-only (`attention_contract.TRANSITION_AUTHORITY`).
- `check_engine.evaluate_handoff_ready(., "spec", "89xjll").ready == True`.
- `production_checks.py:23` imports `specs` at module top.
- `_BacklogCarrierClassification` fields: `unexecuted_ipds`, `unimplemented_specs` (no `spec_all_implemented` / `spec_not_impl`).
- `vy20et` is in `backlog/graduated/`, no `Blocks-Release`.
- `aw specs check` exit 0; `aw attention --check` exit 1 with 8 lane-hygiene findings unrelated to this plan.
- Targeted baseline: `45 passed in 14.20s`.
- `production_checks.spec_plan_trace(., "89xjll", [plan])` returns `[]` after revisions.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G. Executability / evidence | `agent_workflows/runner_shared.py:45765` `_BacklogCarrierClassification` (fields `unexecuted_ipds`, `unimplemented_specs`) | E-05 and V-05 demanded `spec_all_implemented == True` and `spec_not_impl == []`, which are not fields of the classification. While E-05 runs, this plan is itself an unexecuted IPD carrier, so a "fully complete" demand is unsatisfiable in-turn. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05/V-05 now demand `unimplemented_specs == []` and `unexecuted_ipds` equal to exactly this plan's `pending/` path. |
| PR-002 | HIGH | IN-SCOPE | E. Verification feasibility | `aw attention --check` at review HEAD: exit 1, 8 `attention.lane-stranded`/`lane-superseded` findings | E-05/V-05 demanded `aw attention --check` exit 0, which depends on unrelated live lane state the plan cannot fix. Bare-suite "passes" also had no baseline. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bar is now: no finding naming `89xjll`/`vy20et`/`uiej2a` (exit code recorded, re-derived). E-01 records a bare-suite baseline by node id; V-05 compares against it. |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness | `runner_shared.py:40852` (vacuity record before `# Production correction turn loop`), `runner_shared.py:41094` `if findings:` / `# Success path!` | E-03 placed the deferred event beside the vacuity record, which runs on the FIRST evaluation before the correction loop. A production that fails TRACE would still emit `partial: True`, which contradicts `89xjll` Section 6.3 (a partial PASS). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and Proposed change 3 now emit on the success path only. A negative case was added: a non-deferred production emits none. |
| PR-004 | MEDIUM | UNDER-SCOPE | C. Parity / docs | `.aw/system/workflows/plan-review/plan-review.md:13-17` ("kept in deliberate parity"); `.aw/system/workflows/plan-review-long/review-rubric.md` `## A. Plan completeness`; executed `9aprci` Scope-Paths | The 6.2b guidance was added only to the single-file variant, which would leave `/plan-review-long` silent on qualified citations. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `review-rubric.md` added to Scope-Paths, the scope fence, E-06, and Proposed change 4, with identical bullet text. V-06 checks that the two strings are equal. |
| PR-005 | MEDIUM | IN-SCOPE | G. Right-sizing | plan E-03 as authored (runner event + prompt + workflow markdown) | E-03 bundled three deliverables with independent test surfaces under one V-item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split out E-06 (prompt plus both review surfaces) with V-06. E-04 now depends on E-06, and `Highest E allocated: 06`. |
| PR-006 | LOW | IN-SCOPE | C. Architecture | `agent_workflows/production_checks.py:23` `from agent_workflows import specs as _specs` | `_deferred_ids_refusal` importing `production_checks` at module level in `specs.py` would be circular. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and Proposed change 1 require a function-local import. |
| PR-007 | LOW | IN-SCOPE | E. Testing | `tests/test_spec_production.py` `_HOSTS` loop (e.g. `test_5_5_trace_success`) | The runner-event test did not require both hosts, and V-04 implicitly relied on test names and counts. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04/V-03 now require both hosts. V-04 treats test names as non-binding pointers. |
| PR-008 | LOW | IN-SCOPE | G. Evidence accuracy | plan F-01/F-05/Goal; `.aw/records/backlog/graduated/20260926-reqids-01-vy20et-*.backlog.md`; `xvv7n4`, `i2ty4u` Scope-Paths | The plan called `vy20et` "open" (it is `graduated`). F-05 said no pending plan declares `specs.py` or `test_spec_production.py`, but `xvv7n4` and `i2ty4u` (both `reviewed`) do. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Goal, F-01, and F-05 were corrected. Runner isolation handles the overlap, so no dependency edge is needed. Revision prose was also reworded so that no `89xjll <word>` token in an E/V item reads as an unknown TRACE citation (`spec_plan_trace` on this plan returns `[]`). |
| PR-009 | MEDIUM | IN-SCOPE | Project rule (`check.ipd-uncarried-obligation`) | `aw check all` at review HEAD: `check.ipd-uncarried-obligation` [ERROR] on this plan, "deferred row 1, deferred row 2, deferred row 3" | All three `## Deferred / out of scope` rows named no `Carrier`, `Carrier-Evidence`, or `Carrier-Declined`, which `aw check` reports as an error. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each row now carries a `- Carrier-Declined:` reason: two are spec-fixed non-goals, and the third is a close owned by `process_backlog_close`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where should the partial-pass event be emitted? | The success path after the correction loop | Beside the first-evaluation vacuity record (mislabels failed productions); inside the loop on every evaluation (noisy) | `89xjll` Section 6.3 ("a PASS ... MUST be distinguishable as PARTIAL"); `runner_shared.py:41094` | yes |
| D-2 | Should the long plan-review variant be updated too? | Yes, with identical text | Single-file only (breaks stated parity) | `plan-review.md:13-17`; precedent `9aprci` | yes |
| D-3 | What is the bar for `aw attention --check`? | No finding naming this plan's artifacts | Exit 0 (blocked by unrelated live lane state) | Measured exit 1 with 8 lane findings at `70179b555` | yes |
| D-4 | Does the spec text need amending? | No; status, Graduated-To, and history change only | Amend `89xjll` | The plan implements R-5/R-6/R-9 as written | yes |
