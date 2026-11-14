# Review findings: plan 9hk3rh

- Subject-Id: 9hk3rh
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `c8f3aee45` in a non-interactive runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-204-9hk3rh-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent --verbose` returned `clean` (`0` errors, `0` warnings, `0` info advisories). Live inspection against governing spec `4sd62s` section 6, parent plan `1upea0`, the 7 target test modules in `tests/`, and the batch rule uncovered findings `PR-001..PR-005`, all fixed in place. Pass 2 re-checked `E-01..E-04` and `V-01..V-04`, and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` with `0` findings across all severities.

### Proofreading

Checked `.aw/records/plans/pending/20261109-metastore-204-9hk3rh-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Omitted Scope fence hand-mv restriction, conditional runner/executor finalize clause, and stop-and-report safety clause | Added explicit `never a hand git mv`, conditional runner/executor ownership clause ("When `aw oc run` or `aw agy run` executes the plan..."), and standard stop-and-report safety clause | PR-001. |
| Open questions (OQ-01) | `- Owner: none` recorded on resolved question | Updated to `- Owner: plan author` and recorded decision in `### Decisions` (D-1) | PR-002. |
| Proposed changes | Lacked Requirement 12 Mermaid diagram | Added Mermaid `flowchart TD` diagram to `Proposed changes` showing batch progression and ordered step enumeration | PR-003. |
| Front matter, line 20 | Template prompt blockquote; missing `Review-Depth:` and `Readiness:`; status `to-review` | Replaced template line with standard compliance blockquote; added `- Review-Depth: complex` and `- Readiness: go-pending-approval`; updated status to `reviewed` and updated workflow history | PR-004. |
| Batch rule step 1 | Piped directly into `.aw/state/59aiyh/<batch>-files.txt` without ensuring directory exists | Added `mkdir -p .aw/state/59aiyh` to guarantee directory existence on fresh worktrees | PR-005. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `9hk3rh` converts 7 setter and runner test modules to use the shared record builder `tests/record_builder.py` via the Order-49 fixture codemod (`653ndz`).
2. No. It converts test data fixtures in test modules, not execution runners, commit locks, or isolation boundaries.
3. No. 4 E-items (3 batch items of at most 4 modules each and 1 finishing item) across 7 test files.
4. Yes. `- Scope-Paths:` explicitly lists all 7 test module paths plus the plan itself.
5. Yes. Test outcome preservation: per-test outcomes must remain identical before and after conversion.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section 6 and section 7 step 6); parent plan `1upea0` (Order 40); research `nj8zdp` guidance; and the 7 test modules in `tests/`.
- Checked: All dependencies in `- Item-Dependencies:` (`653ndz`, `9rgn2w`, `g5hpbb`, `tve77h`, `xexn45`) resolve in `.aw/records/plans/` and match orchestrator `63ib9r` row 204.
- Found owner violation in OQ-01 (`PR-002`): OQ-01 recorded `- Owner: none` on a resolved question. Fixed by setting `- Owner: plan author` and recording D-1 in `### Decisions`.

### Step R2

- Checked: `E-*`/`V-*` bijection (`4/4`: `E-01..E-04` <-> `V-01..V-04`, with `- Highest E allocated: 04` preserved), dependency chain (`E-01, E-02, E-03 -> E-04`), `- Scope-Paths:` completeness (all 7 target modules and the plan declared), and runtime reachability of all `V-*` checks.
- Found missing lifecycle finalize clause and safety rule in Approval and execution gate (`PR-001`): gate lacked the explicit `never a hand git mv` guard, omitted the conditional runner/executor finalize clause required by `steps/s7-finalize.md`, and lacked the stop-and-report safety clause. Fixed in Gate.

### Step R3

- Checked: safety, test outcome invariance, refusal count threshold (at most 25 hand conversions before stop), and rollback semantics. Verified that outcome list diffs must be empty and that `raw_fields=` is used only for deliberate invalid-input tests.
- Commits are path-scoped to `- Scope-Paths:`. `aw sanitize --agent` runs clean.

### Step R4

- Checked: conformance with spec `4sd62s` section 6, batch rule structure, pytest determinism (`-p no:randomly -n 0`), right-sizing (`4` `E-*` items, `7` work Scope-Paths), and outcome-based testing (`AGENTS.md`).
- Confirmed baseline test run across all 7 target modules (`220 passed in 61.85s`).

### Step R5

- Checked: QA/QC (deterministic outcome list diffs before and after), Architect (shared record builder decoupling test data from storage layout changes), Software Engineer (codemod automation with static refusal classification), and Modest Executor (bounded batch items of at most 4 modules each).

### Step R6

- Checked: `4` `E-*` items in `2` task groups across `7` work `- Scope-Paths:` entries (`- Size assessment: standard`; split from `1upea0` on 2026-11-09 per `nj8zdp`). No further split is required.

### Step R7

- Checked: `- Item-Dependencies: executed:653ndz, executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45` (all verified under `.aw/records/plans/`), split parent `1upea0`, and cutover plan `cxxmyv`. All contracts align cleanly.

### Step S5

- Checked: pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`), updated owner from `none` to `plan author`; recorded three engineering decisions (`D-1..D-3`) in `### Decisions`, all `Reversible: yes`. Zero human-owned questions remain (`questions: []`).

### Pass 2

- Re-reviewed `E-01..E-04` and `V-01..V-04` per `steps/s6-rereview.md` rule 1 after adding gate clauses, Mermaid diagram, and formatting decisions.
- Verified 4-to-4 `E-*`/`V-*` bijection, `- Highest E allocated: 04`, valid `- Scope-Paths:` and `- Item-Dependencies:`, zero em/en dashes, and `0` findings across all severities from `aw ipd lint --phase review-finalize --agent --verbose` (`clean`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261109-metastore-204-9hk3rh-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:164-177 | Approval and execution gate omitted the explicit hand-mv guard, conditional runner/executor finalize clause, and stop-and-report safety clause, required by steps/s7-finalize.md. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added standard hand-mv restriction, conditional runner/executor ownership clause, and stop-and-report safety clause to Gate. Recommendation strength: strong. |
| PR-002 | MEDIUM | IN-SCOPE | R1 / S5 / OQ-01 | .aw/records/plans/pending/20261109-metastore-204-9hk3rh-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:139 | OQ-01 recorded - Owner: none on a resolved question, violating the owner attestation standard in steps/s5-questions.md. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated - Owner: plan author in OQ-01 and recorded the decision in ### Decisions (D-1). Recommendation strength: strong. |
| PR-003 | LOW | IN-SCOPE | Proofreading / Technical writing standard Requirement 12 / R4 | .aw/records/plans/pending/20261109-metastore-204-9hk3rh-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:104 | Proposed changes lacked a Mermaid diagram required by requirement 12(b). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid flowchart TD diagram in Proposed changes showing batch flow. Recommendation strength: strong. |
| PR-004 | LOW | IN-SCOPE | Proofreading / Front Matter | .aw/records/plans/pending/20261109-metastore-204-9hk3rh-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:20 | Unremoved authoring template prompt blockquote and missing front-matter metadata (- Review-Depth: complex, - Readiness: go-pending-approval). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced template line with standard compliance blockquote, added - Review-Depth: complex and - Readiness: go-pending-approval, set Status: reviewed, and updated history. Recommendation strength: strong. |
| PR-005 | LOW | IN-SCOPE | R2 / R4 Batch Rule | .aw/records/plans/pending/20261109-metastore-204-9hk3rh-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:38 | Batch rule step 1 redirected output to .aw/state/59aiyh/<batch>-files.txt without ensuring directory exists, which fails on clean/fresh worktrees. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added mkdir -p .aw/state/59aiyh to batch rule step 1 command. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Can Chunk 2 execute in any order relative to other chunk plans? | Yes. Module sets are disjoint, each chunk depends on builder and codemod, and none edits `tests/support.py` (which runs in `59aiyh` E-09). | Impose strict serial ordering across all 7 chunks (rejected: unnecessary serialization of independent test files). | OQ-01, research `nj8zdp` | yes |
| D-2 | What is the threshold for halting hand conversions? | Stop after codemod step 3 if hand conversion count exceeds 25, commit proved codemod rewrites, and report subset for re-splitting. | Attempt unbounded manual conversions (rejected: high risk of agent mistakes and drift). | `9hk3rh` Batch rule step 4, research `nj8zdp` | yes |
| D-3 | How should directory creation be handled for `.aw/state/59aiyh/` in fresh lane worktrees? | Prepend `mkdir -p .aw/state/59aiyh && ` in step 1 of the batch rule. | Assume pre-existing directory (rejected: causes bash redirection failure in clean worktrees). | `9hk3rh` Batch rule step 1, clean worktree directory verification | yes |
