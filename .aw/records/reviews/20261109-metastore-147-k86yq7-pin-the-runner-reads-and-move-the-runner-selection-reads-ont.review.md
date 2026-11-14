# Review findings: plan k86yq7

- Subject-Id: k86yq7
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `bb1e8749e` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-147-k86yq7-pin-the-runner-reads-and-move-the-runner-selection-reads-ont.ipd.md` was committed and clean at turn start, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `0` advisories), and the reference baseline suites (`pytest` across the 10 runner baseline test modules and front matter whitespace fixture) passed (`398 passed in 33.42s` on E-03 modules, `109 passed in 15.10s` on E-04 modules, `4 passed in 1.69s` on loose whitespace). The 4.4 search command (`rg -n -e '"show"' -e 'cat-file' -e '"ls-files", "-s"' -e '"--cached"' -e '":0:"' -e 'rev-parse' agent_workflows/runner_shared.py agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py`) was re-run and confirmed exactly 53 hits in runner files, matching F-01/F-03. Live inspection against governing spec `4sd62s` C5a and section 7 step 5, predecessor plans `ffceq0`, `g5hpbb`, `h58z9n`, `tve77h`, `xexn45`, and the batch rule uncovered findings `PR-001..PR-007`, all fixed in place. Pass 2 re-checked `E-01` through `E-05` and `V-01` through `V-05`, and `aw ipd lint --phase review-finalize --agent --verbose` confirmed zero errors, warnings, or advisories.

### Proofreading

#### Changes

| Step | Plan location | Before | After | Rationale |
|---|---|---|---|---|
| PR-001 | Front matter | `- Status: to-review` | `- Status: reviewed`<br>`- Readiness: go-pending-approval`<br>`- Review-Depth: complex` | Advances lifecycle to reviewed with readiness assessment and tier tag. |
| PR-002 | Line 20 blockquote | `> Write and proofread this plan per the technical writing standard...` | `> Written to .aw/system/workflows/technical-writing/technical-writing.md. Every obligation, exact identifier, quotation, evidence record, and lifecycle status is preserved.` | Replaces authoring prompt instructions with standard compliance blockquote. |
| PR-003 | `## Workflow history` | Draft and to-review split entries only | Added 2026-11-14 review entry citing verdict and review record path | Records complete review provenance in plan history. |
| PR-004 | Detailed Implementation Checklist & E-02 | Redirection to `.aw/state/t4gl15/` without `mkdir -p` | Added `mkdir -p .aw/state/t4gl15 && ` to command and E-02 instructions | Prevents shell redirection failures when running in clean worktrees where `.aw/state/t4gl15/` has not yet been created. |
| PR-005 | `## Proposed changes (ordered, validatable)` | Plain 3-item numbered list without diagram | Mermaid `flowchart TD` task progression diagram inserted before numbered list | Complies with technical writing standard Requirement 12 (diagrams). |
| PR-006 | `## Open questions` (`OQ-01`) | `- Owner: none` | `- Owner: plan author` | Complies with owner attestation standard on resolved questions. |
| PR-007 | `## Approval and execution gate` | Missing safety rule, hand-mv prohibition, and conditional runner/executor finalize clause | Added explicit safety rule, `(never a hand git mv)`, and runner/executor distinction | Clarifies operational safeguards for hand vs automated runner execution. |

#### Issues

| Id | Severity | Location | Summary | Remediation | Status |
|---|---|---|---|---|---|
| PR-001 | required | Front matter | Status remained `to-review`; missing `Readiness:` and `Review-Depth:` | Updated to `reviewed`, added `Readiness: go-pending-approval` and `Review-Depth: complex` | fixed |
| PR-002 | required | Plan preamble | Unremoved authoring prompt instructions | Replaced with standard compliance blockquote | fixed |
| PR-003 | required | Workflow history | Missing review history entry | Appended review entry with date, verdict, and review record path | fixed |
| PR-004 | required | E-02 and checklist preamble | Shell redirection into non-existent `.aw/state/t4gl15/` directory | Prepended `mkdir -p .aw/state/t4gl15` | fixed |
| PR-005 | required | Proposed changes | Missing Requirement 12 flowchart diagram | Added Mermaid `flowchart TD` task diagram | fixed |
| PR-006 | required | OQ-01 | Resolved question carried `Owner: none` | Updated owner to `plan author` | fixed |
| PR-007 | required | Approval gate | Missing explicit hand-mv guard and safety rule | Added safety rule and conditional runner finalize clause | fixed |

### Step T

- Question 1 (Changes public interface or contract?): Yes. Moves `runner_shared.PlanRecord` construction, `runner_shared.discover_plans`, `discover_specs`, `expand_selectors`, and dependency resolution onto `artifact_meta`, and alters multi-word status resolution in `runner_shared.parse_plan_file` per decision D-1.
- Question 2 (Guard code?): No.
- Question 3 (Large/cross-cutting?): No. Confined to 5 E-items across runner discovery and selection reads, within a single module family (`runner_shared`, `oc_runipd`, `agy_runipd`).
- Question 4 (Scope-Paths declared?): Yes. Exactly 5 code/test paths plus the plan path itself.
- Question 5 (Data loss / break behavior?): Yes. Plan discovery and queue building regressions could misroute execution or drop queue entries across unattended runner runs.
- **Classification**: `AW-TIER: complex`

### Step R1

Governing spec `4sd62s` C5a demands that every runner read metadata through the cache. Plan `k86yq7` covers the queue-building part of section 7 step 5, cleanly isolating the selection reads from the later execution-path reads (`k3hb06`, Order 152). Predecessors `ffceq0`, `g5hpbb`, `h58z9n`, `tve77h`, and `xexn45` are declared in `- Item-Dependencies:` and must be executed prior to running `k86yq7`. Interface contracts (`artifact_meta.read`, `artifact_meta.query`, `artifact_meta.resolve`, `artifact_meta.read_text`) are faithfully preserved.

### Step R2

Scope boundaries are rigorous:
- Includes: 4.4 search classification for runner files (E-01), pinning runner reader behavior in `tests/test_readers_runner.py` (E-02), recording before-baselines for 10 runner test modules (E-03, E-04), and moving selection reads onto `artifact_meta` with after-diff verification (E-05).
- Excludes: execution-path reads and own-log finalize scope (deferred to `k3hb06`), runner residual audit (deferred to `y97k46`), five git-content readers (deferred to `iqhzse`), writer methods (Orders 06/07), and parser deletion (Order 11).
- No over-scope or uncontained side effects.

### Step R3

The task sequencing is strictly ordered and validatable:
- E-01 classifies all 53 git-reading hits across runner files.
- E-02 pins observable behavior on unmodified code into a new test file `tests/test_readers_runner.py` before any edits.
- E-03 and E-04 establish baseline test results across 10 modules into `.aw/state/t4gl15/E-06-before-1.txt` and `E-06-before-2.txt`.
- E-05 executes the migration onto `artifact_meta` and validates diffs against saved baselines.
- The 1:1 bijection between E-items and V-items is strictly maintained (`V-01`..`V-05`), with concrete pasted evidence required for every verification step.

### Step R4

Testing and validation rigor is exemplary:
- Adheres strictly to the pin-first rule: observable behavior is pinned before changes and asserted unchanged after changes.
- D-1 status normalization (`pending` directory fallback -> normalized `executed` status) is the single allowed behavioral diff, verified against `tests/test_front_matter_loose_whitespace.py`.
- D-4 loose whitespace tolerance is preserved and verified.
- Zero code-pinning tests: all assertions test behavioral outputs and returned structures without inspecting source code via regex or AST.

### Step R5

Risk analysis and edge cases are well handled:
- Non-standard leading whitespace in plan front matter is explicitly preserved via D-4 (`artifact_meta.read_text` loose fallback).
- Multi-word status tokens are canonicalized via D-1, with only a single record (`vfa1tl`) changing status from `EXECUTED` to `executed`.
- Readiness absence invariant (`plan_readiness.is_plan_review_approved`, 4.4a `l56tyz`) is tested and preserved.
- Operational hazard of missing `.aw/state/t4gl15/` directory in fresh lane worktrees was identified and remediated in PR-004.

### Step R6

Operational readiness and reversibility:
- Changes are fully reversible via standard git branch revert.
- The commit protocol mandates `aw commit k86yq7 -- <paths>` with no bulk staging or pushes.
- Plan lifecycle transition requires `aw ipd finalize k86yq7` with pre-transition lint clean and all V-items passed.

### Step R7

Review findings PR-001 through PR-007 have been completely synthesized and resolved in place. The plan conforms to all structural, formatting, and behavioral requirements.

### Step S5

Review of open questions:
- `OQ-01` addresses splitting the ten-module baseline across two items (E-03 and E-04) to maintain the ~8 named units per item right-sizing rule. It is resolved with strong rationale and owned by `plan author`.
- Zero unresolved or blocking questions remain (`questions: []`).

### Pass 2

`AW-REVIEW: DONE`

All five E-items, five V-items, front matter metadata, and compliance gates were re-evaluated. `aw ipd lint --phase review-finalize --agent --verbose` reports `clean` with 0 findings. The plan is hardened and ready for maintainer approval.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | Metadata / Front matter | .aw/records/plans/pending/20261109-metastore-147-k86yq7-pin-the-runner-reads-and-move-the-runner-selection-reads-ont.ipd.md:9-10 | Status was to-review; missing - Readiness: go-pending-approval and - Review-Depth: complex. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated Status: reviewed, added Readiness: go-pending-approval and Review-Depth: complex. Recommendation strength: strong. |
| PR-002 | LOW | IN-SCOPE | Formatting / Technical writing standard | .aw/records/plans/pending/20261109-metastore-147-k86yq7-pin-the-runner-reads-and-move-the-runner-selection-reads-ont.ipd.md:20 | Preamble had unremoved authoring prompt instructions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with standard compliance blockquote. Recommendation strength: strong. |
| PR-003 | LOW | IN-SCOPE | Provenance / Workflow history | .aw/records/plans/pending/20261109-metastore-147-k86yq7-pin-the-runner-reads-and-move-the-runner-selection-reads-ont.ipd.md:22-26 | Missing review entry in workflow history. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Appended review entry citing verdict and review record path. Recommendation strength: strong. |
| PR-004 | MEDIUM | IN-SCOPE | Operational / Checklist & E-02 | .aw/records/plans/pending/20261109-metastore-147-k86yq7-pin-the-runner-reads-and-move-the-runner-selection-reads-ont.ipd.md:35,46 | Shell commands redirected to .aw/state/t4gl15/ without ensuring directory exists, which fails on clean worktrees. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Prepended mkdir -p .aw/state/t4gl15 to commands and E-02 instructions. Recommendation strength: strong. |
| PR-005 | LOW | IN-SCOPE | Technical writing standard / Requirement 12 | .aw/records/plans/pending/20261109-metastore-147-k86yq7-pin-the-runner-reads-and-move-the-runner-selection-reads-ont.ipd.md:105 | Proposed changes lacked a Mermaid diagram required by requirement 12. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid flowchart TD diagram showing task progression across E-01..E-05. Recommendation strength: strong. |
| PR-006 | LOW | IN-SCOPE | Attestation / Open questions | .aw/records/plans/pending/20261109-metastore-147-k86yq7-pin-the-runner-reads-and-move-the-runner-selection-reads-ont.ipd.md:138 | Resolved question OQ-01 carried - Owner: none. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set - Owner: plan author on OQ-01. Recommendation strength: strong. |
| PR-007 | HIGH | IN-SCOPE | Governance / Approval gate | .aw/records/plans/pending/20261109-metastore-147-k86yq7-pin-the-runner-reads-and-move-the-runner-selection-reads-ont.ipd.md:175-183 | Approval gate lacked safety rule, hand-mv prohibition, and conditional runner/executor finalize clause. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added standard hand-mv prohibition, runner/executor finalize clause, and safety rule. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should multi-word status tokens be resolved in `runner_shared.parse_plan_file`? | Normalize to the canonical first-token status (`plans.normalize_status`), yielding `executed` instead of falling back to directory bucket `pending`. | Keep directory bucket fallback (rejected: violates metastore consistency across reader family). | Spec `4sd62s`, plan `ffceq0`, `tests/test_front_matter_loose_whitespace.py` | yes |
| D-2 | Why split the ten-module baseline across two items (E-03, E-04)? | Two halves of five modules each maintain the ~8 named units right-sizing guideline and keep diffs clear. | Keep as a single 10-module item (rejected: too large for a single step). | `OQ-01`, research `nj8zdp` | yes |
| D-3 | How should directory creation for `.aw/state/t4gl15/` be handled in fresh lane worktrees? | Prepend `mkdir -p .aw/state/t4gl15 && ` in checklist command and E-02. | Assume directory exists (rejected: causes bash redirection failure in clean worktrees). | PR-004, worktree clean state verification | yes |
| D-4 | How should loose whitespace in runner front matter reads be handled? | Keep tolerance by reading loose values from `artifact_meta.read_text` when strict cached value is absent. | Enforce strict whitespace only (rejected: breaks existing plan front matter compatibility). | Plan `k86yq7`, `tests/test_front_matter_loose_whitespace.py` | yes |
