# Review: Coordinate companion repo and AW_HOME bug fixes

- Subject-Id: 92ujfc
- Subject-Type: ipd
- Subject-Path: .aw/records/plans/pending/20261124-comphome-00-92ujfc-coordinate-companion-repo-and-aw-home-bug-fixes.ipd.md
- Reviewed-At: 2026-11-25
- Reviewer: antigravity/Gemini 4 Neon (High)
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Proofreading

Checked against `.aw/system/workflows/technical-writing/technical-writing.md` (all 12 requirements):

### Changes
| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `## Findings` | Informal short module names (e.g. `engine`, `install_wizard`, `cli`) omitting `project_context.py`, `project_schema.py`, `placement_switch.py` (`7gverp`), `ipd_authoring.py` (`7eivm2`), and `attention.py` (`7hfx7r`) | Canonical `agent_workflows/<mod>.py` citations matching all six reviewed child `Scope-Paths` | Technical Writing Reqs 1, 2, 7 and cross-plan consistency |
| `## Deferred / out of scope (with reason)` | Pointed `artifact_meta.check_freshness` `ReleaseResolution` mismatch to `- Carrier: ywl7uc` despite `ywl7uc` declining it | Filed open backlog item `f3qdqh` and updated `- Carrier: f3qdqh` with canonical `agent_workflows/artifact_meta.py::check_freshness` and `agent_workflows/releases.py::ReleaseResolution` citations | `steps/s5-questions.md` carrier integrity and Technical Writing Req 7 |
| `E-06`, `## Child IPDs`, `## Project conventions`, `## Spec / documentation sync`, `## Approval and execution gate` | `E-06` omitted `E-01`; `IPD-Z603` note claimed no size exceptions; `Spec / documentation sync` gave tentative `7gverp` note; abbreviated gate line | Aligned `E-06` (`E-01, E-03, E-05`), updated child table/size/doc-sync facts to match all six reviewed children, and added the complete execution contract | `steps/r7-cross-plan.md` and `steps/s7-finalize.md` |

### Issues
| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|

### Step T

- Checked: skipped per spec `k3yx72` Section 5.1 (Order-00 orchestrator; `- Kind: orchestrator`, `- Review-Depth: orchestrator`).

### Step R1

- Checked: `.aw/records/plans/pending/20261124-comphome-00-92ujfc-coordinate-companion-repo-and-aw-home-bug-fixes.ipd.md`, all six Set `comphome` child IPDs (`ywl7uc`, `7gverp`, `mmuv3v`, `7eivm2`, `7hfx7r`, `4vnd36`), existing carrier plan `rntx9a` (`.aw/records/plans/pending/20261119-vo0y6q-01-rntx9a-route-artifact-meta-state-and-lock-paths-to-aw-home-when-rec.ipd.md`), `agent_workflows/artifact_meta.py::check_freshness:4974-4995`, and `agent_workflows/releases.py::ReleaseResolution` / `resolve_release_outcome`.
- Confirmed the `ReleaseResolution` attribute mismatch (`rel_outcome.status`/`rel_outcome.candidates` vs `outcome`/`paths`) is real and uncarried after `ywl7uc:179-180` explicitly declined carrying it -> `PR-001`.

### Step R2

- Checked: `IPD-S407` (`E-01..E-06` `CONFIRM <id6> REACHED executed` rows match all six children 1:1), `IPD-S408` (`aw ipd coverage 92ujfc --no-commit` verified semantic coverage pass with refreshed fingerprint), `E-01..E-06` <-> `V-01..V-06` bijection, `- Item-Dependencies:` (all six children listed), `- Scope-Paths:` (orchestrator plan file only), carrier integrity, and execution-contract completeness.
- Fixed missing execution-contract clauses in `## Approval and execution gate` -> `PR-003`.

### Step R7

- Checked: cross-plan consistency between `92ujfc` and all six reviewed children (`ywl7uc`, `7gverp`, `mmuv3v`, `7eivm2`, `7hfx7r`, `4vnd36`: all `Status: reviewed`, `Readiness: go-pending-approval`, `Review-Depth: complex`), dependency DAG acyclicity (`ywl7uc` -> `7gverp`, `mmuv3v`, `7eivm2`, `7hfx7r`; `{ywl7uc, mmuv3v, 7hfx7r}` -> `4vnd36`), and carrier ownership for deferred items (`rntx9a` and newly filed `f3qdqh`).
- Reconciled `E-06` `Depends on: E-01, E-03, E-05`, child module lists (`7gverp`, `7eivm2`, `7hfx7r`), `IPD-Z603` size-exception accounting, and `## Spec / documentation sync` against the six reviewed children -> `PR-002`.

### Step S5

- Checked: both `OQ-01` and `OQ-02` are already `Status: resolved` by the maintainer (`2026-11-24`). All three findings (`PR-001..PR-003`) have Low Remediation Risk and were resolved directly from repository evidence and reviewed child plans. Zero open questions or unfixed `HIGH`/`BLOCKER` findings remain; both recorded decisions (`D-1..D-2`) are `Reversible: yes`.

### Pass 2

- Checked: re-read the entire revised `92ujfc` end-to-end (`Concern`, `Scope`, `E-01..E-06`, `## Child IPDs` table + Mermaid flowchart, `## Completion criteria`, `## Cross-IPD validation`, `## Project conventions`, `## Findings`, `## Proposed changes`, `## Deferred / out of scope`, `## Spec / documentation sync`, `## Open questions`, `V-01..V-06`, and `## Approval and execution gate`). Verified `IPD-S407` rows preserved verbatim, `aw ipd coverage 92ujfc --no-commit` passing with current fingerprint, `aw ipd lint --phase review-finalize` clean, zero em/en dashes, and valid `- Readiness: go-pending-approval` and `- Review-Depth: orchestrator`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | High | in-scope | Cross-Plan Carrier Integrity | `.aw/records/plans/pending/20261124-comphome-00-92ujfc-coordinate-companion-repo-and-aw-home-bug-fixes.ipd.md:138-139`; `.aw/records/plans/pending/20261124-comphome-01-ywl7uc-fix-companion-and-aw-home-core-storage-context-placement-swi.ipd.md:179-180`; `agent_workflows/artifact_meta.py:4976-4984`; `agent_workflows/releases.py` (`ReleaseResolution`) | `92ujfc` pointed the verified backend-agnostic `artifact_meta.py::check_freshness` `ReleaseResolution` attribute mismatch (`status`/`candidates` vs `outcome`/`paths`) to `- Carrier: ywl7uc`, but `ywl7uc` explicitly declined carrying it and does not touch `agent_workflows/artifact_meta.py`, leaving the bug with a broken carrier pointer. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Filed open backlog item `f3qdqh` via `aw backlog new --apply` and updated `92ujfc` to `- Carrier: f3qdqh` (recommendation strength: very strong). |
| PR-002 | Medium | in-scope | Cross-Plan Consistency | `.aw/records/plans/pending/20261124-comphome-00-92ujfc-coordinate-companion-repo-and-aw-home-bug-fixes.ipd.md:65,74-78,112,118-123,152`; all six reviewed Set `comphome` child IPDs | After the six child reviews completed, `92ujfc` drifted slightly from its children: `E-06` listed `Depends on: E-03, E-05` (omitting `E-01`, which appears in the child table, diagram, and `4vnd36`), `Step 0` implied no child carried an `IPD-Z603` exception (5 of 6 carry `exception`), `## Findings` and the child table omitted added scope modules (`project_context.py`/`project_schema.py`/`placement_switch.py` in `7gverp`, `ipd_authoring.py` in `7eivm2`, `attention.py` in `7hfx7r`), and `## Spec / documentation sync` gave a tentative `7gverp` doc note that `7gverp` had already verified unnecessary. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Reconciled `E-06`, child table summaries, `Step 0`, `## Findings` canonical module paths, and `## Spec / documentation sync` to match all six reviewed children exactly (recommendation strength: strong). |
| PR-003 | Medium | in-scope | Execution Contract & Prose | `.aw/records/plans/pending/20261124-comphome-00-92ujfc-coordinate-companion-repo-and-aw-home-bug-fixes.ipd.md:204-209` | `## Approval and execution gate` contained only a one-line retirement sentence and omitted the required execution-contract clauses (scope fence, hard-MUST paste-actual-output validation honesty rule, path-scoped commit and never-push rule, and conditional runner automatic retirement vs standalone `aw ipd finalize 92ujfc` with no hand-rolled `git mv`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Added the complete five-point execution contract in `## Approval and execution gate` and standardized code citations to canonical `agent_workflows/<mod>.py` form (recommendation strength: strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `92ujfc` re-home the deferred `agent_workflows/artifact_meta.py::check_freshness` `ReleaseResolution` attribute mismatch after `ywl7uc` declined carrying it? | File a dedicated open backlog item (`f3qdqh`) via `aw backlog new --apply` and cite `- Carrier: f3qdqh` in `92ujfc`. | Use `- Carrier-Declined:` (rejected: `artifact_meta.py:4976-4984` vs `releases.py::ReleaseResolution` is a confirmed live bug silently swallowing `AttributeError`, so dropping it loses a real defect) or assign to `mmuv3v` (rejected: out of companion/`~/.aw/` scope and would rewrite an already-reviewed sibling). | `agent_workflows/artifact_meta.py:4976-4994`; `agent_workflows/releases.py::ReleaseResolution`; `.aw/system/workflows/plan-review/steps/s5-questions.md:84-85` | yes |
| D-2 | Should `92ujfc` keep its existing six-child Set `comphome` layout and Mermaid diagram after reconciling child scope updates? | Keep the six-child layout (`ywl7uc`, `7gverp`, `mmuv3v`, `7eivm2`, `7hfx7r`, `4vnd36`) and existing Mermaid DAG unchanged while updating `E-06` `Depends on:` and module summaries to match the reviewed children. | Re-partition children into smaller plans (rejected: all six children already passed `complex`-tier `/plan-review` with justified `IPD-Z603` assessments and clean dependency ordering). | All six reviewed Set `comphome` child IPDs (`Status: reviewed`, `Readiness: go-pending-approval`) | yes |
