# Review findings: ipd 3xwbvs

- Subject-Id: 3xwbvs
- Subject-Type: ipd
- Reviewed-At: 2026-11-27
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261127T062613Z-2263911`). The target Order-00 orchestrator plan `.aw/records/plans/pending/20261122-selectors-00-3xwbvs-orchestrate-normalized-artifact-selector-flags-across-all-aw.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings), and `aw ipd coverage 3xwbvs` returned `Orchestrator 3xwbvs is ready for review.` (exit 0). Because `3xwbvs` is an Order-00 orchestrator (`- Kind: orchestrator`), Check T was skipped per spec `k3yx72` Section 5.1 (`- Review-Depth: orchestrator`), and the review ran Checks P, R1, R2 (`IPD-S407`, `IPD-S408`), R7 (cross-plan consistency across the full Set `selectors`), S5, S6, and S7. It examined `3xwbvs`, all three approved Set `selectors` child plans (`bzsoai`, `mnlaoa`, `e36q6r`), backlog item `1iojci`, spec `ogd2nv`, and dependent Set `cliverbs` orchestrator `lmlji2`. It found three `MEDIUM` and one `LOW` findings (`PR-001..PR-004`), all `Overall:Low` remediation risk and all fixed in place. No production code or test code was modified.

### Step T

- Checked: skipped per spec `k3yx72` Section 5.1 (Order-00 orchestrator; `- Kind: orchestrator`, `- Review-Depth: orchestrator`).

### Step R1

- Checked: `.aw/records/plans/pending/20261122-selectors-00-3xwbvs-orchestrate-normalized-artifact-selector-flags-across-all-aw.ipd.md`, Order 01 `bzsoai` (`Status: approved`, `Readiness: go-pending-approval`), Order 02 `mnlaoa` (`Status: approved`, `Readiness: go-pending-approval`), Order 03 `e36q6r` (`Status: approved`, `Readiness: go-pending-approval`), backlog `1iojci` (`Status: graduated`), spec `ogd2nv` (`Status: to-review`), and dependent Set `cliverbs` orchestrator `lmlji2`.
- Found: `3xwbvs` cited `e36q6r` (`E-04` / `V-04`) for whole-Set cross-command parity and validation, which moved to `e36q6r` (`E-05` / `V-05`) during `e36q6r`'s review (`PR-001`); child summaries and completion criteria omitted post-review scope refinements across `bzsoai`, `mnlaoa`, and `e36q6r` (`PR-002`); `E-*`/`V-*` items lacked qualified `ogd2nv R-*`/`AC-*` citations and the gate lacked the execution contract (`PR-003`).

### Step R2

- Checked: `IPD-S407` (`E-01..E-03` `CONFIRM <id6> REACHED executed` rows match all three declared children 1:1), `IPD-S408` (`aw ipd coverage 3xwbvs` verified ready for review before and after edits with refreshed fingerprint), `3/3` E/V bijection (`- Highest E allocated: 03`), `- Item-Dependencies: executed:bzsoai, executed:mnlaoa, executed:e36q6r`, `- Scope-Paths:` (orchestrator file only), durable carrier `- Carrier: lmlji2` in `## Deferred / out of scope`, post-cutover qualified `ogd2nv` spec citations, and `## Approval and execution gate` execution contract.
- Found: missing qualified `ogd2nv` citations in `E-01..E-03`/`V-01..V-03` and an abbreviated one-line gate lacking scope-fence, honesty, commit, and conditional runner-retirement vs standalone `aw ipd finalize 3xwbvs` clauses (`PR-003`). Fixed in place.

### Step R7

- Checked: cross-plan consistency across `3xwbvs` and all three approved child plans (`bzsoai` -> `mnlaoa` -> `e36q6r`), verifying dependency DAG acyclicity (`bzsoai`: none; `mnlaoa`: `executed:bzsoai`; `e36q6r`: `executed:mnlaoa`; `3xwbvs`: all three), requirement partition (`ogd2nv` R-01..R-04 in `bzsoai`, R-02/R-05/R-06 query+mutation + spec amendment in `mnlaoa`, R-05/R-06 runner/completion/docs + spec amendment + whole-Set parity in `e36q6r`), deferred handoff (`lmlji2` depends on `executed:e36q6r`), and child `IPD-Z603` size rationales.
- Found: `3xwbvs` drifted from the post-review versions of `bzsoai`, `mnlaoa`, and `e36q6r` (`E-04`/`V-04` vs `E-05`/`V-05`, `--new-date` on `group`/`rename`, `--history-date` on `specs set`/`set`, `search -p`, hidden `--arcive-state`, `partition`/`ipd board`/`index` carve-outs, `runner_shared.py` queue seam, runner `include_types=False` preserving `--type`, `aw agy exec --prompt`, `command_surface.py` `legacy_flags`, `CHANGELOG.md`, and `mnlaoa` `OQ-01` resolution) (`PR-001`, `PR-002`). All reconciled in place.

### Step S5

- Checked: `## Open questions`. All five open questions in backlog `1iojci` were resolved by the maintainer on 2026-11-22, `mnlaoa` `OQ-01` (`--new-date`) was resolved by the maintainer on 2026-11-25, and all three children are already `Status: approved`. All four review findings (`PR-001..PR-004`) have `Overall:Low` remediation risk and are settled by the approved child plans. One reversible decision is recorded in `### Decisions` (`D-1`). No human question remains; lane outcome JSON records `{"questions": []}`.

### Pass 2

- Trigger: `Scope`, `E-01..E-03` expected outcomes, `## Child IPDs`, `## Completion criteria`, `## Cross-IPD validation`, `## Scope check`, `## Required tests / validation`, `## Open questions`, `V-01..V-03`, and `## Approval and execution gate` were updated during Round 1.
- Re-checked the complete revised `3xwbvs` end to end: verified `IPD-S407` `CONFIRM <id6> REACHED executed` rows preserved verbatim, `3/3` E/V bijection, qualified `ogd2nv` citations, zero em/en dashes, refreshed `aw ipd coverage 3xwbvs` passing, and clean `aw ipd lint --phase review-finalize --agent` (exit 0, 0 findings).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | MEDIUM | IN-SCOPE | R1 / R7 / Stale `e36q6r` item reference (`E-04`/`V-04` vs `E-05`/`V-05`) | .aw/records/plans/pending/20261122-selectors-00-3xwbvs-orchestrate-normalized-artifact-selector-flags-across-all-aw.ipd.md:80,94; .aw/records/plans/pending/20261122-selectors-03-e36q6r-wire-normalized-artifact-selectors-into-runner-clis-shell-co.ipd.md:105-113,209-212 | `3xwbvs` attributed whole-Set cross-command parity and validation to `e36q6r` (`E-04` / `V-04`), but during `e36q6r`'s review `E-04`/`V-04` became completions and `legacy_flags`, while `E-05`/`V-05` owns the spec amendment, docs, `CHANGELOG.md`, parity tests, and whole-Set validation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `## Cross-IPD validation` and `## Required tests / validation` to cite `e36q6r` (`E-05` / `V-05`) and aligned the parity command list and validation suite with `e36q6r` (`D-1`). Recommendation strength: very strong. |
| PR-002 | MEDIUM | IN-SCOPE | R7 / Child summaries, completion criteria, and open-question history drifted from approved children | .aw/records/plans/pending/20261122-selectors-00-3xwbvs-orchestrate-normalized-artifact-selector-flags-across-all-aw.ipd.md:6,51,56,61,68-76,90,98; approved child plans `bzsoai`, `mnlaoa`, `e36q6r` | `3xwbvs` predated the reviews of `bzsoai`, `mnlaoa`, and `e36q6r` and omitted key shipped scope refinements: `mnlaoa`'s `dest_prefix`/`selector_records`, `--new-date` (`OQ-01` resolved 2026-11-25), `specs set --history-date`, `search -p`, hidden `--arcive-state`, `partition`/`ipd board`/`index` carve-outs, and `ogd2nv` E-10 amendment; `e36q6r`'s `runner_shared.py` queue seam, runner `include_types=False` preserving `--type`, `aw agy exec --prompt`, `command_surface.py` `legacy_flags`, `CHANGELOG.md`, and `ogd2nv` E-05 amendment; `bzsoai`'s `attention_contract.py::ORDER_KEYS` comment sync; and the advisory `IPD-Z603` status of `mnlaoa` and `e36q6r`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reconciled `Scope`, `E-01..E-03` expected outcomes, `## Child IPDs`, `## Completion criteria`, `## Scope check`, `## Open questions`, and `V-01..V-03` with all three approved children (`D-1`). Recommendation strength: strong. |
| PR-003 | MEDIUM | IN-SCOPE | R2 / Unqualified post-cutover spec citations and missing execution contract in gate | .aw/records/plans/pending/20261122-selectors-00-3xwbvs-orchestrate-normalized-artifact-selector-flags-across-all-aw.ipd.md:17,49-62,104-124 | `E-01..E-03` and `V-01..V-03` omitted qualified `ogd2nv R-*`/`AC-*` citations (`SPEC-PLAN-TRACE`), and `## Approval and execution gate` contained only one sentence, omitting resolved-OQ, scope-fence (`--scope-reason`/`--scope-ack`), honesty, path-scoped commit/never-push, and conditional runner automatic retirement vs standalone `aw ipd finalize 3xwbvs` clauses. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added qualified `ogd2nv` citations across `E-01..E-03` and `V-01..V-03` and added the complete execution contract to `## Approval and execution gate`. Recommendation strength: very strong. |
| PR-004 | LOW | IN-SCOPE | P / Technical writing standard, code citation format, and Mermaid diagram sync | .aw/records/plans/pending/20261122-selectors-00-3xwbvs-orchestrate-normalized-artifact-selector-flags-across-all-aw.ipd.md:1-124; .aw/system/workflows/technical-writing/technical-writing.md | Informal bare symbol/file names (`selectors.SelectorSpec`, `attention.py`) lacked canonical `agent_workflows/<mod>.py::Symbol` anchors, and the Mermaid flowchart omitted `mnlaoa`'s `dest_prefix`/renames and `e36q6r`'s `runner_shared` queue seam and `agy exec --prompt`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Normalized `agent_workflows/<mod>.py::Symbol` citations, synchronized the Mermaid flowchart with the three approved children, and tightened prose with zero em or en dashes. Recommendation strength: strong. |

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Scope`, `## Goal`, Mermaid flowchart | Pre-review summary of three children | Reconciled summary and Mermaid labels matching approved `bzsoai`, `mnlaoa`, and `e36q6r` | PR-002, PR-004, technical writing standard requirement 12 |
| `E-01..E-03`, `## Child IPDs`, `## Completion criteria` | Informal symbol names, pre-review `mnlaoa`/`e36q6r` descriptions, no qualified `ogd2nv` citations | Canonical `agent_workflows/<mod>.py::Symbol` citations, post-review child scope details, qualified `ogd2nv` R-01..R-06 and AC-01..AC-03 citations | PR-002, PR-003, PR-004 |
| `## Cross-IPD validation`, `## Required tests / validation` | Cited `e36q6r` (`E-04` / `V-04`) and 4 bare commands | Cited `e36q6r` (`E-05` / `V-05`) with exact parity commands and full validation suite (`pytest`, bare core `python3 -m pytest`, `mypy`, `aw specs check`, `aw attention --check`, `aw sanitize --agent`) | PR-001 |
| `## Scope check`, `## Open questions`, `V-01..V-03`, `## Approval and execution gate` | Omitted `mnlaoa` `OQ-01` resolution, `ogd2nv` `to-review` note, child `IPD-Z603` status, child V-item ranges, and execution contract | Recorded `mnlaoa` `OQ-01` resolution, `ogd2nv` amendment ownership, child `IPD-Z603` rationales, exact child V-item ranges (`V-01..V-04`, `V-01..V-10`, `V-01..V-05`), and full execution contract | PR-002, PR-003 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `3xwbvs` reconcile its pre-review text with the already-reviewed and approved children `bzsoai`, `mnlaoa`, and `e36q6r`? | Update `3xwbvs` in place to match all three approved children (`E-05`/`V-05` in `e36q6r`, `--new-date`/`--history-date`/`search -p`/carve-outs in `mnlaoa`, `runner_shared` seam/`include_types=False`/`agy exec --prompt`/`legacy_flags` in `e36q6r`) while preserving the three-child DAG and `IPD-S407` rows verbatim. | Leave `3xwbvs` with pre-review summaries or reopen approved children (rejected: stale orchestrator text misleads future readers and `e36q6r` `E-04`/`V-04` no longer owns whole-Set validation; all three children already passed review and human approval). | Approved child plans `bzsoai`, `mnlaoa`, and `e36q6r`; `steps/r7-cross-plan.md`. | yes |
