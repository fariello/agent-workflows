---
id: 2m4i0o
created: 20261026
set: revsteps
order: 06
topic: [plan-review, pilot, analytics]
model: 
kind: findings
status: active
outcome: informational
summary: k3yx72 pilot: proposed vs current plan-review, per-tier cost and quality, MD-20 gate decision
consumed-by: [kk62qt]
---

# Research Findings: Plan Review Redesign Pilot Results (k3yx72)

- Date: 2026-10-26
- Set: revsteps
- Spec: k3yx72
- Plan: kk62qt
- Baseline commit: `bb094ca8ab37a04dec9f7aa431551d4c70764b86`
- Pilot commit: `51d68b44e4589adf8c45bc4245f07f65ea4cbfa4`

## Decision Summary

- MD-20 gate: OTHERWISE
- complex default: single-12

---

## 1. Executive Summary and Decision Rationale

Spec `k3yx72` MD-20 establishes a gate before building Stage 2 (Orders 03, 06, 07, 08, and the remainder of 05): evaluate whether a tiered, multi-prompt review costs less than the current single-turn `/plan-review` without sacrificing quality.

The review pilot testbed was fully constructed and validated:
1. **Fixtures and Planted Defects**: 9 fixture plans (3 simple, 3 standard, 3 complex) were prepared from recent executed plans, with 27 defects planted (3 per fixture: V-item evidence omissions, wrong file paths, and breaking CLI option modifications) weighted by harm (harm 1 to 3).
2. **Quality Rubric and Judge Protocol**: A 4-component scoring rubric (planted defects 40%, false findings 20%, edit correctness 20%, design quality 20%) and a blind judge evaluation prompt were committed before any review execution (`51d68b44e`).
3. **Pilot Driver & Worktree Isolation**: The test driver `tools/review_pilot.py` was authored, verified with unit tests `tests/test_review_pilot.py` across all isolation and budgeting properties (7/7 passed), and dry-run verified to configure 84 cells (24 simple, 24 standard, 36 complex).

At E-05, the maintainer attended the session and answered question OQ-01 regarding the budget cap:
- **Maintainer Ruling**: Set `--budget 0.0` (Dry-run / test only; halts before any live OpenCode reviews or judge calls are dispatched).

Under this $0 budget cap, the driver stopped before incurring live model spend. Consequently, zero live review cells and zero live judge evaluations completed.

Under spec Section 13.5:
- In the absence of live comparative cost and quality measurements, the gate outcome is **OTHERWISE**. The maintainer decides whether to proceed with Stage 2, stop, or execute a sized run once budget is allocated.
- For the `complex` grouping default, spec Section 13.5 specifies that when variants are not shown different, the default is **`single-12`** because it provides one runner-visible result per check.

---

## 2. Pilot Design as Built

| Dimension | Specification |
|---|---|
| Fixture Plans | 9 plans: 3 simple (`h4nu1j`, `3glhpc`, `ea7gsh`), 3 standard (`dn21zx`, `3jv5f4`, `g0oj9k`), 3 complex (`z2rygb`, `mp6g57`, `utcqct`) |
| Planted Defects | 27 total defects (3 per plan): harm 2 (V-item evidence), harm 2 (wrong file path), harm 3 (CLI option change) |
| Methods | `simple` & `standard`: `single` (current), `steps` (`proposed`). `complex`: `single` (current), `steps` (`grouped-6`), `steps` (`single-12`) |
| Review Models | OpenCode: Opus 5.5 High (`uri/its_direct/pt3-claude-opus-5.5-1m-us`), GPT-6.1 Sol High (`openai/gpt-6.1-sol`); Antigravity: Gemini 3.8 Flash High (`gemini-3.8-flash-high`) |
| Repeats | 1 plan per tier repeated across all models and methods to measure noise (`h4nu1j`, `dn21zx`, `z2rygb`) |
| Total Planned Reviews | 84 reviews: Simple 24, Standard 24, Complex 36 |
| Blind Judges | 3 models per review (Opus 5.5, GPT-6.1 Sol, Gemini 3.8 Flash) = 252 judge evaluations |
| Blinding & Redaction | Author, reviewer, agent, host, and run-id strings redacted with `<redacted>` |
| Blinding Limit | Residual formatting difference (steps-mode produces `### Step` sections) is noted in the rubric |

---

## 3. Results and Measures per Tier

Because execution was halted under the maintainer-confirmed $0 budget cap:

| Tier | Method | Planned Cells | Completed Cells | Missing Cells | Median Cost | Median Tokens | Avg Quality Score |
|---|---|---|---|---|---|---|---|
| `simple` | `single` (current) | 12 | 0 | 12 | N/A | N/A | N/A |
| `simple` | `steps` (proposed) | 12 | 0 | 12 | N/A | N/A | N/A |
| `standard` | `single` (current) | 12 | 0 | 12 | N/A | N/A | N/A |
| `standard` | `steps` (proposed) | 12 | 0 | 12 | N/A | N/A | N/A |
| `complex` | `single` (current) | 12 | 0 | 12 | N/A | N/A | N/A |
| `complex` | `steps` (`grouped-6`) | 12 | 0 | 12 | N/A | N/A | N/A |
| `complex` | `steps` (`single-12`) | 12 | 0 | 12 | N/A | N/A | N/A |
| **Total** | | **84** | **0** | **84** | | | |

### Missing Cells and Reasons
All 84 cells were halted unexecuted.
- **Reason for omission**: Maintainer attended session confirmed budget cap of $0.00 at E-05 (dry-run / test execution only; no live API charges authorized).

### Judge Runs and Scoring
- Total planned judge evaluations: 252 (84 reviews x 3 judges).
- Completed judge evaluations: 0.
- Missing judge evaluations: 252 (unexecuted due to review cell budget stop).
- Judge disagreement & self-scoring: Unmeasured empirically in this run.

---

## 4. Worktree and Baseline Verification Evidence

Worktrees built in `tmp/review-pilot/` during testbed validation confirmed exact baseline and pilot code isolation:
- `simple_h4nu1j_single_current_opus_r1`:
  - `ls tests/fixtures/review-pilot`: Failed (absent, verified removed).
  - SHA256 of `plan-review.md`: `0cecbb50fe0702708352f1f4f7d5e8fec2ed2506a5e100c835c92e8d725a54d4` (matches baseline commit `bb094ca8` exactly).
- `simple_h4nu1j_steps_proposed_opus_r1`:
  - `ls tests/fixtures/review-pilot`: Failed (absent, verified removed).
  - SHA256 of `plan-review.md`: `0ce83a23359a575445cc019e41577dfa8acc5c4a30b3d60e9340e4eaa4f9f5d8` (matches pilot commit `51d68b44` exactly).

---

## 5. Sample Size Calculation for Sized Run (OQ-10)

Per spec Section 13.3 stage 2 and OQ-10, the sized run uses a paired two one-sided test (TOST) on cost and quality.

Assuming the historical median review cost of $7.83 and an estimated cost coefficient of variation $CV = 0.50$:
$$n \approx 2 \times \frac{(z_{1-\alpha} + z_{1-\beta/2})^2 \times CV^2}{\Delta^2}$$

For $\alpha = 0.05$ (95% confidence) and $1-\beta = 0.80$ (80% power), $(z_{0.95} + z_{0.90})^2 \approx 7.84$:

| Cost Margin ($\Delta$) | Required Paired Reviews ($n$) | Total Reviews ($2n$) | Projected Spend (at $7.83/review) |
|---|---|---|---|
| $\pm 5\%$ | 1,568 | 3,136 | ~$24,550 |
| $\pm 10\%$ | 392 | 784 | ~$6,140 |
| $\pm 15\%$ | 174 | 348 | ~$2,725 |
| $\pm 20\%$ | 98 | 196 | ~$1,535 |

This table allows the maintainer to set the appropriate confidence, equivalence margin, and dollar cap in OQ-10 should a sized run be commissioned.

---

## 6. Appendix: Raw Data Records

### Appendix A: Cells Data (`tmp/review-pilot/cells.jsonl`)
- Line count in `tmp/review-pilot/cells.jsonl`: 0 lines.

| Cell Key | Fixture ID6 | Method | Variant | Model | Repeat | Run ID | Started At | Ended At | Exit Code | Outcome | Cost | Tokens | Assigned Tier |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

*(0 rows recorded; 84 cells unexecuted due to $0 budget cap).*

### Appendix B: Scores Data (`tmp/review-pilot/scores.jsonl`)
- Line count in `tmp/review-pilot/scores.jsonl`: 0 lines.

| Cell Key | Judge Model | Planted Defects | False Findings | Edit Correctness | Design Quality | Total Score | Cost |
|---|---|---|---|---|---|---|---|

*(0 rows recorded; 252 judge runs unexecuted due to $0 budget cap).*
