# Review Pilot Quality Rubric

This rubric defines the scoring criteria and weights for blind evaluation of plan reviews in the `k3yx72` review pilot (spec Section 13.4).

## Weights and Formula

The overall review quality is evaluated on an integer scale from 0 to 100 based on four core components:

| Component | Weight | Raw Scale | Weighted Contribution |
|---|---|---|---|
| Planted Defects Found ($D$) | 40% | 0 to 10 | $4 \times D$ (0 to 40) |
| False Findings Raised ($F$) | 20% | 0 to 10 | $2 \times F$ (0 to 20) |
| Correctness of Edits ($C$) | 20% | 0 to 10 | $2 \times C$ (0 to 20) |
| Design Quality of Plan ($Q$) | 20% | 0 to 10 | $2 \times Q$ (0 to 20) |

$$\text{Total Score} = 4 \times D + 2 \times F + 2 \times C + 2 \times Q$$

---

## Component Anchors

### 1. Planted Defects Found ($D \in [0, 10]$)

Each fixture contains exactly three planted defects with assigned harm weights $h_i \in \{1, 2, 3\}$, summing to a total possible harm of 7:
- Defect 1: A `V-*` item whose `Required evidence` asks for no concrete evidence (harm: 2).
- Defect 2: A wrong file path in an `E-*` item (harm: 2).
- Defect 3: A changed CLI option that another command reads without caller updates (harm: 3).

The score reflects the total harm of the detected planted defects:

| Harm Found | Defects Detected | Score ($D$) |
|---|---|---|
| 7 / 7 | All 3 planted defects detected | 10 |
| 5 / 7 | Harm 3 defect + one Harm 2 defect detected | 7 |
| 4 / 7 | Both Harm 2 defects detected (Harm 3 missed) | 6 |
| 3 / 7 | Harm 3 defect only detected | 4 |
| 2 / 7 | One Harm 2 defect only detected | 3 |
| 0 / 7 | No planted defects detected | 0 |

### 2. False Findings Raised ($F \in [0, 10]$)

A false finding is an issue raised by the reviewer against correct, conforming, or intentional parts of the plan that are not actually defective:

| False Findings | Description | Score ($F$) |
|---|---|---|
| 0 | No false findings; high precision and relevance | 10 |
| 1 | 1 minor false finding (e.g. harmless stylistic dispute or overzealous nit) | 8 |
| 2 | 2 minor false findings or 1 material false finding (claiming working spec/code is broken) | 6 |
| 3 | 3 minor false findings or 2 material false findings | 4 |
| 4 | 4 false findings; significant distraction from real issues | 2 |
| 5+ | 5 or more false findings; severe hallucinatory noise | 0 |

### 3. Correctness of Edits Made ($C \in [0, 10]$)

Evaluates the edits applied to the plan file by the review to fix findings:

| Score ($C$) | Anchored Description |
|---|---|
| 10 | All applied edits cleanly fix identified defects without introducing syntax errors, lint failures, regressions, or breaking plan structure. |
| 8 | Edits are substantively correct with minor formatting/whitespace imperfections. |
| 5 | Edits are partially correct; or fixed one defect while slightly disrupting another section; or left valid findings unfixed without rationale. |
| 2 | Edits introduced a new defect, broke an existing valid contract, or corrupted a section. |
| 0 | Destructive edits; deleted required sections or introduced preflight-refused syntax errors. |

*(Note: If the reviewer correctly chose not to edit the plan directly because findings require author/human replanning, score based on the accuracy of the prescribed remediations).*

### 4. Design Quality of Reviewed Plan ($Q \in [0, 10]$)

Evaluates the overall quality, executability, and rigor of the plan document after the review:

| Score ($Q$) | Anchored Description |
|---|---|
| 10 | Pristine plan: clear scope, atomic actionable E-items, robust validation with concrete evidence demands, clear error handling. |
| 8 | High quality: solid executability and validation with minor phrasing improvements possible. |
| 5 | Acceptable: executable but with loose validation criteria or ambiguous edge cases. |
| 2 | Poor: vague execution steps, weak verification, or missing architectural detail. |
| 0 | Unexecutable or fundamentally flawed. |

---

## Blinding Protocol and Residual Limits

- **Redaction**: Review files presented to the judge have all agent identifiers, model names, host names, and run IDs redacted (`<redacted>`).
- **Residual Limit**: The review method (single-turn vs. tiered multi-prompt steps) remains inferable from the review record layout (`### Step` subsections vs flat headings). Judges are instructed to evaluate solely on review thoroughness, accuracy, and plan quality, without favoring or penalizing a particular record formatting style.
