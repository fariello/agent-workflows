# Review findings: plan jykyqb

- Subject-Id: jykyqb
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `a61001308`. Plan committed and byte-identical to the lane input; no
pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; `--phase review-finalize`: `clean` after revision.
Not an orchestrator.

Verified from code: `check_engine.evaluate_blocking_close` HANDOFF arm filters `carrier_items` by `_same_release` into
`same_gate_carriers` and requires `all(_carrier_eval(_c) for _c in same_gate_carriers)` (F-01 holds);
`runner_shared.evaluate_backlog_close` takes every carrier from `find_from_backlog_artifacts` discarding the gate and
requires `plan_bucket == "executed"` / `_carrier_is_executed` (F-02 holds). `find_from_backlog_*` return `""` for an
ungated carrier, and `_same_release("", "next")` falls back to string equality (False), so the plan's drop analysis
holds. `release_gate_warnings` keys `gates_map` by gate (F-07 holds); `check_release_gate_consistency`'s grandfathered
arm has exactly the two cohort strings (F-08 holds; test at `tests/test_check_engine_release_gate.py`
`test_rule_blocking_close_grandfathered_cohort_details`). All five "EVERY same-gate"/"every same-gate carrier" prose
sites exist as cited; `AGENTS.md` fix (1) is at line 230, below `<!-- /aw:block -->` at line 125.
`tests/test_backlog_close_gate_prose.py` regexes are as quoted. `llbr2b` is `to-review`. `ncmugb` is pending.

Reproduced by driving the code in a scratch repo built with the test module's own `_make_scratch_repo`/`_write_*`
helpers: executed same-gate plan + pending ungated plan -> `check_engine: True HANDOFF`, runner `False IPD carrier(s)
not executed: ...plnpen...`. Corpus re-measure (one shared `_from_backlog_carrier_index`): 479 gated items, 0 flips.
`aw check release-gates --agent`: `conforms`, 0 findings.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Rubric A/D (semantics decision unrecorded) | `check_engine._carrier_is_executed` (true only for an `executed` path segment / spec `implemented`); `_iter_plan_ipds` walks every bucket including `superseded/`; review probe: same-gate executed + UNGATED superseded -> check_engine `True HANDOFF`, runner `False`; same-gate executed + same-gate superseded -> `False` today; corpus: 16 gated `done` items carry a superseded carrier | Widening to "every carrier" makes a RETIRED ungated sibling block the HANDOFF close permanently. The plan neither decided nor tested this, though it is the most consequential new refusal shape. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01(c) records the decision (retired counts as unfinished, consistent with the same-gate rule and the runner; remedies SATISFIED/DE-GATED unchanged; 0 corpus flips); E-02 case (6) pins refusal plus the DE-GATED escape; V-02 updated. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric G (unsatisfiable bar) | review run: `aw check --agent` -> `outcome: findings`, `exit 1`, 123 findings (72 `check.lifecycle-transition-unvalidated`, 28 `check.ipd-uncarried-obligation`, ...) | E-10/V-10 demanded `aw check` with 0 errors, which the repository does not meet for reasons unrelated to this plan; the executor would have to fail the item or misreport. | all Low | FIXED | E-10/V-10 now demand a before/after per-rule count with no release-gate-family rule rising; `aw check release-gates` keeps the 0-errors bar. |
| PR-003 | LOW | IN-SCOPE | Rubric G (live-artifact bar, reproducibility) | E-10(c) "Re-run the corpus measurement" with no method; gated count 473 at authoring vs 479 at review | The corpus re-measure had no stated method, and its population is live. | all Low | FIXED | E-10(c) specifies the single-index old/new comparison and states the count is live; the bar is 0 flips. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does a superseded/not-executed ungated sibling block the HANDOFF close? | Yes (not terminal). | Exempt retired carriers (rejected: diverges from the runner `plan_bucket != "executed"` and from today's same-gate behavior, re-creating the disagreement this plan closes; would need a new terminal predicate). | `runner_shared.evaluate_backlog_close`; `check_engine._carrier_is_executed` docstring ("We do NOT use is_retired ..."); review probes; 0 corpus flips. | yes |
| D-2 | Keep the author's OQ-01(a)/(b) (every carrier blocks; same-gate entry condition stays)? | Keep. | Drop entry condition (rejected per plan's Deferred reasoning). | F-02, F-06 re-measured. | yes |
| D-3 | What bar replaces "`aw check` 0 errors"? | No release-gate-family rule count rises; `aw check release-gates` conforms. | Require whole `aw check` exit 0 (rejected: unsatisfiable today). | review `aw check --agent` output. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
