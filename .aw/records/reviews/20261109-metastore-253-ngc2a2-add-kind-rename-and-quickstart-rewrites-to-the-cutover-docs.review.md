# Review findings: plan ngc2a2

- Subject-Id: ngc2a2
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `aaf2d94ec` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-253-ngc2a2-add-kind-rename-and-quickstart-rewrites-to-the-cutover-docs.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent --verbose` returned clean with two non-blocking `IPD-C802` em-dash advisories in line 108. During revision, explicit state directory initialization (`mkdir -p .aw/state/ngc2a2`) was added to E-01, code citations were standardized (e.g. `agent_workflows/cli.py`, `agent_workflows/engine.py`), a Mermaid `flowchart TD` diagram was added under `## Proposed changes`, structured resolved question `OQ-01` was added with attested owner `plan author`, and `Approval and execution gate` was updated with the standard hand-mv restriction, conditional runner/executor finalize clause, and narrow unsafe-condition stop rule. Pass 2 re-checked the complete revised plan against spec `4sd62s` section 5.4, parent split plan `90iqr1`, and prerequisite cutover doc plan `y1zihp`, and `aw ipd lint --phase review-finalize --agent --verbose` returned clean (`0` findings across all severities).

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Omitted narrow unsafe-condition stop rule, hand-mv restriction, and conditional runner/executor finalize clause | Added explicit stop-and-report rule for missing prerequisite patch or apply failure, hand-mv restriction, and explicit conditional runner/executor ownership clause | PR-001, Technical Writing Standard Requirement 1. |
| Open questions | Prose stating "None open." without structured question block | Added structured resolved `OQ-01` with `- Owner: plan author` documenting patch isolation per `4sd62s` C10a | PR-002, steps/s5-questions.md owner attestation standard. |
| Proposed changes (ordered, validatable) | Three-line description without process diagram | Added Mermaid `flowchart TD` diagram showing scratch worktree workflow across E-01..E-05 | PR-003, Technical Writing Standard Requirement 12(b). |
| Scope / V-03 / V-04 | Cited `cli.py` and `engine.py` without repo-relative path prefix | Standardized code citations to `agent_workflows/cli.py` and `agent_workflows/engine.py` | PR-004, Technical Writing Standard Requirement 7, IPD-C801. |
| Validation-state rule / E-01 / Front matter | Contained em dashes (U+2014) in V-rule prose, lacked mkdir in E-01, and omitted front matter readiness and depth | Replaced em dashes with parentheses resolving two `IPD-C802` advisories, added `mkdir -p .aw/state/ngc2a2`, and added `- Readiness: go-pending-approval` and `- Review-Depth: standard` | PR-005, Technical Writing Standard Requirement 1, Step S7 review output requirements. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Partly. The plan does not modify live documents in main, but finalizes the cumulative cutover documentation patch `.aw/system/cutover/metastore-docs.cutover.patch` including two new quickstart documents and installer templates that land at the cutover (`cxxmyv`).
2. No. It creates a temporary scratch worktree under `.aw/state/ngc2a2/scratch` to update a patch file; it touches no guard modules.
3. No. It has 5 E-items in 3 task groups across 2 declared Scope-Paths (`ngc2a2.ipd.md` and `.aw/system/cutover/metastore-docs.cutover.patch`).
4. Yes. `- Scope-Paths:` explicitly declares `ngc2a2.ipd.md` and `.aw/system/cutover/metastore-docs.cutover.patch`.
5. Low. Edits are confined to a scratch worktree and packaged as a `.patch` file. Live documents and code remain untouched until `cxxmyv`.

AW-TIER: standard

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (sections 4.1 and 5.4); parent split plan `90iqr1` (Order 12); prerequisite plan `y1zihp` (Order 252); cutover commit carrier `cxxmyv` (Order 13).
- Target documents and templates: `qhay6a` F-03 table documents for `Kind` renames, `agent_workflows/cli.py` help strings, two new quickstart documents (`.aw/AGENT_QUICKSTART.md`, `.aw/QUICKSTART.md`), and installer template text in `agent_workflows/engine.py`.
- Added structured resolved question `OQ-01` with `- Owner: plan author` documenting patch isolation (`PR-002`).

### Step R2

- Checked: E/V bijection (`5/5`: `E-01..E-05` <-> `V-01..V-05`), `- Highest E allocated: 05`, `- Item-Dependencies:` (`executed:9o83cr, executed:y1zihp`), and isolated-lane reachability of every `V-*` demand.
- Checked gate contract: added narrow unsafe-condition stop rule, hand-mv restriction, and explicit conditional runner/executor finalize ownership clause to `Approval and execution gate` (`PR-001`).
- Verified zero em/en dashes, explicit state directory initialization (`mkdir -p .aw/state/ngc2a2`), and valid `- Scope-Paths:`.

### Step R3

- Checked: scratch worktree operations are isolated under `.aw/state/ngc2a2/scratch` (gitignored), scratch worktree is removed with `git worktree remove --force` in E-05, and no sensitive data or leak-sanitizer patterns are added.

### Step R4

- A (Correctness and data integrity): Patch application is atomic; git apply failure in scratch halts without side effects.
- C (Architecture and operability): Cumulative patch mechanism cleanly preserves spec `4sd62s` C10a invariant by keeping documentation rewrites and quickstarts off `main` until the atomic cutover commit (`cxxmyv`).
- D and E (Anti-regression and testing): E-02 verifies that `rg -n -w 'Kind' --type md` in scratch worktree finds only quoted legacy examples and `Work-Kind`/`Gate-Kind` spellings; E-03 confirms only help strings change in `cli.py`; V-01..V-05 provide concrete diff and verification checks.
- Executability and right-sizing: 5 E-items in 3 task groups across 2 Scope-Paths; cohesive and focused.

### Step R5

- Checked: QA/QC (deterministic diff stats and patch verification), Architect (clean isolation of cutover documentation changes via cumulative patch), Software Engineer (ensuring CLI option names remain untouched while updating help strings), and Modest Executor (linear sequential dependencies).

### Step R6

- Checked: right-sizing at 5 E-items in 3 task groups across 2 Scope-Paths (`- Size assessment: standard`). Cleanly decoupled split from `90iqr1`. No further decomposition needed.

### Step R7

- Checked: `- Item-Dependencies: executed:9o83cr, executed:y1zihp` (both verified present under `.aw/records/plans/`), parent split plan `90iqr1`, and downstream cutover integration in `cxxmyv`. All contracts align cleanly.

### Step S5

- Checked: OQ-01 is resolved and non-blocking. Attested owner set and decisions D-1 through D-5 recorded in `### Decisions`. Zero questions belong to the human (`questions: []`).

### Step S6

- Re-review check: No new `E-*` or `V-*` items added or removed; `- Scope-Paths:` and `- Item-Dependencies:` unchanged; all edits are surgical hardening.
- Re-run `aw ipd lint --phase review-finalize --agent --verbose` confirmed clean (`0` errors, `0` warnings, `0` info advisories).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261109-metastore-253-ngc2a2-add-kind-rename-and-quickstart-rewrites-to-the-cutover-docs.ipd.md:160 | Approval and execution gate omitted explicit narrow unsafe-condition stop rule, explicit hand-mv restriction, and conditional runner/executor finalize clause. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added narrow stop rule for missing prerequisites or apply failure, hand-mv restriction, and explicit conditional runner/executor ownership clause to Gate (recommendation strength: strong). |
| PR-002 | MEDIUM | IN-SCOPE | R1 / S5 / Open questions | .aw/records/plans/pending/20261109-metastore-253-ngc2a2-add-kind-rename-and-quickstart-rewrites-to-the-cutover-docs.ipd.md:121 | Open questions section used informal prose ("None open.") without a structured resolved question block or owner attestation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added structured resolved `OQ-01` with `- Owner: plan author` documenting patch isolation per `4sd62s` C10a and recorded D-1 in `### Decisions` (recommendation strength: strong). |
| PR-003 | LOW | IN-SCOPE | Proofreading / Requirement 12(b) | .aw/records/plans/pending/20261109-metastore-253-ngc2a2-add-kind-rename-and-quickstart-rewrites-to-the-cutover-docs.ipd.md:79 | Proposed changes lacked a Mermaid diagram required by Technical Writing Standard Requirement 12(b) for multi-step processes with branches. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram under `## Proposed changes` showing scratch worktree workflow across E-01..E-05 (recommendation strength: strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Requirement 7 / Step 0 | .aw/records/plans/pending/20261109-metastore-253-ngc2a2-add-kind-rename-and-quickstart-rewrites-to-the-cutover-docs.ipd.md:6 | Scope, V-03, and V-04 cited `cli.py` and `engine.py` without repo-relative path prefix (`IPD-C801`, Technical Writing Standard Requirement 7). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Standardized code citations to `agent_workflows/cli.py` and `agent_workflows/engine.py` (recommendation strength: strong). |
| PR-005 | LOW | IN-SCOPE | Proofreading / Advisory IPD-C802 / Step S7 | .aw/records/plans/pending/20261109-metastore-253-ngc2a2-add-kind-rename-and-quickstart-rewrites-to-the-cutover-docs.ipd.md:132 | Line 132 contained em dashes (U+2014) in V-rule prose triggering `IPD-C802` advisories; E-01 lacked mkdir parent dir; front matter lacked `- Readiness: go-pending-approval` and `- Review-Depth: standard`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced em dashes with parentheses in line 132, added `mkdir -p .aw/state/ngc2a2` in E-01, and added `- Readiness: go-pending-approval` and `- Review-Depth: standard` to front matter (recommendation strength: very strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Are documentation rewrites applied to live documents in this plan? | No. Spec `4sd62s` C10a requires all cutover doc rewrites to remain off `main` until the atomic cutover commit (`cxxmyv`). All edits are captured in `.aw/system/cutover/metastore-docs.cutover.patch`. | Edit live documents directly (rejected: violates C10a invariant and breaks live tests). | `4sd62s` C10a, `90iqr1` OQ-01 | yes |
| D-2 | Where does the scratch worktree live? | In `.aw/state/ngc2a2/scratch` within the gitignored state directory of the executing checkout, initialized with `mkdir -p .aw/state/ngc2a2`. | Use `/tmp` (rejected: outside authorized workspace); use main checkout (rejected: pollutes git status). | `90iqr1` OQ-03, `qhay6a` OQ-01 | yes |
| D-3 | How are new or renamed files captured in the cumulative patch? | Use `git add -A` in the scratch worktree, followed by `git diff --cached --binary HEAD` written to `.aw/system/cutover/metastore-docs.cutover.patch`. | Use `git diff HEAD` (rejected: drops untracked new files). | `90iqr1` PR-005 | yes |
| D-4 | Are CLI option names renamed in this plan? | No. Only help strings in `agent_workflows/cli.py` describe the option values as plan role and research kind. Option renames are CLI contract changes owned by Order 13's code changes (`cxxmyv`). | Rename `--kind` CLI flags (rejected: breaks existing scripts and caller contracts before cutover). | `ngc2a2` E-03, `4sd62s` 5.4 | yes |
| D-5 | How is patch integrity verified before commit? | Validate `git apply --stat` over the regenerated patch showing both quickstarts as new and `.aw/system/managed-sections.json` included, and verify the scratch worktree is cleanly removed. | Skip patch apply check (rejected: unverified patch could fail during cutover). | `ngc2a2` V-05, `90iqr1` V-08 | yes |
