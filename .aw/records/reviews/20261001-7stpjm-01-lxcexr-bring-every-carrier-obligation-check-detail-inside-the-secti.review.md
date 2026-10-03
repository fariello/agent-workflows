# Review findings: plan lxcexr

- Subject-Id: lxcexr
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `8c14feb1f` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review; `--phase review-finalize` was clean after revision.

Re-verified (read-only; the fix was SIMULATED in memory by re-composing details from the real
`evaluate_carrier_obligation` verdicts over every pending plan; no repository code was modified):
- `check all --json`: 102 diagnostics, 29 fail `attention_contract.is_safe_descriptive` (`MAX_DESCRIPTIVE_LEN = 300`):
  `check.ipd-carrier-finished-unverified` 14 (all 14 newline-bearing, worst 2258), `check.ipd-uncarried-obligation`
  14 (worst 942), `check.ipd-lint-diagnostic` 1 (650, plan `d5ntkj`).
- `check_engine.evaluate_carrier_obligation`: both `all_finished` branches build `reason` as the four-part `\n`-joined
  string; the duplicated "an agent must confirm it did this work ..." clause is built in `check_engine._resolve_carrier`,
  not in the per-row reason body. `evaluate_durable_carrier` uses `shown = rule_failures[:5]`; its docstring and the
  `_IPD_LINT_SHOWN` comment both describe the fixed five.
- `tests/test_check_engine.py::CarrierDischargedRemedyTests` substring pins confirmed (`expected_line` In
  `verdict.reason`, `fixes[0]`; `Carrier-Declined` In reason; NotIn on superseded branch).
- `tests/test_carrier_finished_verification.py` `assertIn("re-point", ref.remedy)` reads a `runner_shared` string, not
  `_resolve_carrier`'s detail.
- Simulation results over 39 carrier findings: whole-group budget + plan-style medium remedy -> 10 unsafe, worst 357;
  + partial-group elision -> 7 unsafe, worst 326; compact remedy (`; shipped: add \`<evidence_line>\`, not
  Carrier-Declined`) + partial groups -> 0 unsafe, worst 298; compact remedy + whole groups only -> 4 unsafe, worst
  327. Locators named versus today's `min(5,total)`: 6 findings fewer, 4 more (whole-group) / 0 more (partial, capped).
- Eligible evidence paths: 1681, min 36, median 118, max 136. Worst single-row composition with the compact remedy:
  304 with today's header, 275 with a shortened header.
- Backlog `7stpjm` is at `graduated/` (history: graduated by run run-20261001T221834Z-1991716: lxcexr), not `open/`
  as `- Scope-Paths:` declared. `0livgf` is `open`; `evwmm2` is `done`; `aw check plans` prints `Fix:` carrying the
  `- Carrier-Evidence:` path.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G. Feasibility of the bound | `check_engine.evaluate_durable_carrier` `shown = rule_failures[:5]`; simulation above | E-04 as written (whole partitions only, floor of one whole group) cannot bring single-body findings of 7 to 9 uncarried locators in bound: they compose 304 to 327 characters with nothing left to elide. The plan's "all in bound" premise held only on its authoring population. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires partial-group elision (show as many locators of the next group as fit, floor of one locator), counting the tail in the budget; E-02 gains case (e), nine uncarried rows; OQ-01 amended. |
| PR-002 | HIGH | IN-SCOPE | G. Feasibility of the bound | `evaluate_carrier_obligation` `all_finished` branches; simulation above | E-03 left the single-line remedy wording unconstrained; a reasonable medium wording still leaves 7 of 39 findings over the bound (worst 326). Only a compact clause clears all of them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 states the measured budget (about 35 fixed characters around `evidence_line`), the shape that cleared 39 of 39, and requires re-measuring the chosen words with the E-05 census. |
| PR-003 | MEDIUM | IN-SCOPE | D. Honest claims | F-08, E-04 rationale, E-06 note | "Names MORE locators" / "information goes UP" is false for 6 of 39 live findings, which name fewer than today's five. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-08, E-04 and E-06 now state the mixed direction; V-04 demands per-finding named-before/after counts; failure criterion changed to "obligation neither named nor counted". |
| PR-004 | MEDIUM | IN-SCOPE | G. Executability | `check_engine._resolve_carrier` `all_finished` detail | E-04 locates the duplicated clause in "the finished-carrier per-row body" without saying it comes from `_resolve_carrier`; an executor could miss it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 names `_resolve_carrier` as the producer, its sole caller, the absence of any test pin on it, and keeps the `required=` text; V-04 asks which route was used. |
| PR-005 | MEDIUM | UNDER-SCOPE | G. Doc sync | `evaluate_durable_carrier` docstring "enumerating up to five offending locators"; `_IPD_LINT_SHOWN` comment "Mirrors ... (five, then \"(and N more)\")" | Both become false after E-04. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 rationale requires both comment updates (code of `_IPD_LINT_SHOWN` unchanged); V-04 demands the diffs. |
| PR-006 | MEDIUM | IN-SCOPE | G. Scope-path staleness | `- Scope-Paths:` `.aw/records/backlog/open/...7stpjm...`; actual `graduated/` | The declared backlog path was already stale at review, the exact class the plan warns about. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope-Paths corrected to `graduated/`; E-06 note and Scope check prose updated; the stale "runner sets it graduated" wording removed. |
| PR-007 | MEDIUM | IN-SCOPE | E. Acceptance criterion | V-05 "ZERO entries failing", E-05; live `check.ipd-lint-diagnostic` 650-char detail | A tree-wide zero-failures demand is unsatisfiable today because a third, out-of-scope rule fails the predicate; the Deferred row's "22 of 22" was stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05/V-05 scoped to the two carrier rules, others listed as context; Deferred row updated with the measurement and kept on `0livgf`. |
| PR-008 | LOW | IN-SCOPE | G. Execution contract | POST-GATE LIFECYCLE paragraph | Missing conditional runner/executor finalize ownership and a declaration-style scope fence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added both; V-05 worst-case wording relaxed to "recorded, not asserted" since the compact remedy may now land under 300. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to make every live single-body group fit? | Partial-group elision with a one-locator floor | Whole-group floor (plan as written, 3-4 still over); smaller fixed cap (loses locators unconditionally) | Simulation above over 39 findings | yes |
| D-2 | Prescribe exact remedy wording? | No; prescribe a measured budget and the shape that met it | Pin exact bytes (violates P16 for tests and over-constrains); leave unconstrained (7 still over) | Simulation above; plan E-02's own no-literal-pin rule | yes |
| D-3 | Accept naming fewer locators on some findings? | Yes, every hidden obligation counted | Keep fixed five (violates Section 8.8 at 400-2258 chars) | `attention_contract.is_safe_descriptive`; existing `(and N more)` contract | yes |
| D-4 | Include `check.ipd-lint-diagnostic` over-bound detail? | No; out of scope, recorded, carried by `0livgf` | Widen this plan to a third rule | Plan Scope OUT list; `0livgf` is the cross-rule mechanism carrier | yes |
