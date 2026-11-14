# Review findings: plan iqhzse

- Subject-Id: iqhzse
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `c75baed64` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-146-iqhzse-move-the-setter-staleness-lifecycle-and-runner-merge-path-gi.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `0` advisories), and baseline test suites (`tests/test_review_staleness_advisory.py`, `tests/test_ipd_lifecycle_cli.py`, `tests/test_records_only_lane_rederive.py`, `tests/test_runner_backlog_close_behavior.py`, `tests/test_merge_conflict_sendback.py`, and `tests/test_status_set.py -k untooled`) passed (`183 passed in 21.19s`). During revision, `Approval and execution gate` was updated with the standard conditional runner/executor finalize ownership clause, scope fence declaration, and narrow unsafe-condition stop rule (`PR-001`), `mkdir -p .aw/state/t4gl15 .aw/state/iqhzse` was added to the PIN-FIRST rule (`PR-002`), `## Findings` was expanded to document `D-1` through `D-5` under `### Behavior decisions` (`PR-003`), a Mermaid `flowchart TD` diagram was added under `## Proposed changes` (`PR-004`), `OQ-01` owner was updated to `plan author` (`PR-005`), code citations in `Step 0` were converted to repo-relative `path::Symbol` identifiers, the authoring prompt was replaced with a declarative conformance note, and front matter gained `- Readiness: go-pending-approval` and `- Review-Depth: complex` (`PR-006`). Pass 2 re-checked the complete revised plan against `4sd62s`, `t4gl15`, `h58z9n`, `snh19k`, and `63ib9r`, and `aw ipd lint --phase review-finalize --agent` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Omitted conditional runner/executor finalize clause, scope fence boundary clarification, and narrow stop rule | Added conditional runner/executor finalize ownership clause, scope fence clarification, and narrow unsafe-condition stop rule | PR-001, `steps/r2-executability.md` and `steps/s7-finalize.md`. |
| PIN-FIRST rule | Redirected into `.aw/state/t4gl15/` without ensuring directory existence | Added `mkdir -p .aw/state/t4gl15 .aw/state/iqhzse` in the PIN-FIRST rule | PR-002, ensure isolated lane worktrees succeed without redirection failure. |
| Findings (Behavior decisions) | Listed only D-1, omitting D-2 through D-5 | Added full D-1 through D-5 documentation under `### Behavior decisions` matching `t4gl15` and `h58z9n` | PR-003, ensure self-contained decision ledger. |
| Proposed changes | Three-step prose summary without diagram | Added Mermaid `flowchart TD` diagram showing the 3-step staged pipeline | PR-004, Technical Writing Standard Requirement 12(b). |
| Open questions (OQ-01) | `- Owner: none` recorded on resolved question | Set `- Owner: plan author` on resolved question | PR-005, `steps/s5-questions.md` owner attestation rule. |
| Front matter, Step 0, Authoring prompt | Imperative authoring prompt, bare symbols in Step 0, omitted review readiness and tier in front matter | Replaced authoring prompt with declarative conformance note, standardized citations to `path::Symbol`, added `- Readiness: go-pending-approval`, `- Review-Depth: complex`, and review history record | PR-006, Technical Writing Standard Requirement 7 and Step S7. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `iqhzse` moves git-content readers in `status_set.py`, `plan_readiness.py`, `ipd_lifecycle.py`, and `runner_shared.py` (merge stage and conflict resolution) onto `artifact_meta.read_at` / `read_text`.
2. Yes. Governs status transitions, review-staleness calculation, release-lane landing checks, and runner merge conflict detection.
3. No. Right-sized at 3 `E-*` items in 2 task groups across 6 work Scope-Paths (`agent_workflows/status_set.py`, `agent_workflows/plan_readiness.py`, `agent_workflows/ipd_lifecycle.py`, `agent_workflows/runner_shared.py`, `agent_workflows/artifact_meta.py`, `tests/test_readers_read_at_gates.py`).
4. Yes. `- Scope-Paths:` explicitly names the 6 work modules plus the plan file itself.
5. Yes. Preservation of review-staleness frozen digests and conflict rederivation behavior across 183 baseline tests.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section 4.4, C5, C5a); parent plan `h58z9n` (Order 33); predecessor plan `snh19k` (Order 145); split parent `t4gl15` (Order 09); orchestrator `63ib9r` (Order 00, row 146); and prerequisite plans `ffceq0` (Order 08), `g5hpbb` (Order 14), `tve77h` (Order 02), and `xexn45` (Order 07).
- Verified that all 11 referenced `id6` identifiers resolve cleanly via `aw find all --agent` and all declared modules exist on HEAD `c75baed64` (with `tests/test_readers_read_at_gates.py` created by executed prerequisite `snh19k`).
- Found owner violation in `OQ-01` (`- Owner: none` on resolved question, `PR-005`), bare `module.function` citations in `Step 0` (`PR-006`), and missing D-2 through D-5 documentation in `## Findings` (`PR-003`). Fixed all in place.

### Step R2

- Checked: 3-to-3 `E-*`/`V-*` 1:1 bijection (`E-01..E-03` <-> `V-01..V-03`), `- Highest E allocated: 03`, dependency chain (`E-01 -> E-02 -> E-03`), `- Scope-Paths:` completeness, and runtime reachability of all `V-*` checks.
- Found missing directory creation for `.aw/state/t4gl15/` (`PR-002`) and missing conditional runner vs. standalone executor finalize ownership clause, scope fence declaration, and narrow unsafe-condition stop rule in `Approval and execution gate` (`PR-001`). Fixed both in place.

### Step R3

- Checked: access control, query safety, revision traversal safety, and index locking. Verified that `artifact_meta.read_at` safely handles revision specs, and git-blob readers do not bypass leak-sanitizer constraints.

### Step R4

- Checked: behavioral decisions and invariant preservation:
  1. `D-1`: Multi-word plan status normalization (`executed` for `EXECUTED`/`DONE`, `legacy/unknown` otherwise); non-plan records retain exact single-token status.
  2. `D-2`: Merge-stage blob resolution (`:<stage>:<path>` via `read_at`, fallback to `read_text`).
  3. `D-3`: Review-staleness index moves plan status to `read_at` while preserving frozen-region body digest via raw blob.
  4. `D-4`: Landing check byte equality remains byte comparison; status/id validations use `read_at`.
  5. `D-5`: State directory initialization (`mkdir -p .aw/state/t4gl15 .aw/state/iqhzse`).
- Verified test determinism (`-p no:randomly -n 0`), right-sizing (`3` `E-*` items, `6` work Scope-Paths), and Requirement 12(b) diagram coverage (`PR-004`).

### Step R5

- Checked: Architect (clean migration of git-content readers in setter, staleness, lifecycle, and runner merge path onto `artifact_meta.read_at`/`read_text`), Security Reviewer (safe revision parsing without shell injection, leak-sanitizer compliance), QA/QC (baseline outcome list diffs, 183 verified baseline tests across 6 modules), Software Engineer (clean typing, preservation of public reader signatures), and Modest Executor (3 bounded `E-*` items in 2 task groups).

### Step R6

- Checked: `3` `E-*` items in `2` task groups across `6` work `- Scope-Paths:` entries (`- Size assessment: standard`; split from `h58z9n` on 2026-11-09 per research `nj8zdp` guidance). No further split is required.

### Step R7

- Checked: `- Item-Dependencies: executed:ffceq0, executed:g5hpbb, executed:tve77h, executed:xexn45, executed:snh19k` (all verified in `metastore`), parent `h58z9n` (which depends on `iqhzse`), split sibling `snh19k` (which creates `tests/test_readers_read_at_gates.py`), split parent `t4gl15`, and orchestrator `63ib9r` (row 146). Contracts align coherently across all related artifacts.

### Step S5

- Checked: pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`), updated owner from `none` to `plan author`; recorded five engineering decisions (`D-1..D-5`) under `### Behavior decisions` and `### Decisions` below, all `Reversible: yes`. Zero human-owned questions remain (`questions: []`).

### Pass 2

- Re-reviewed `E-01..E-03` and `V-01..V-03` per `steps/s6-rereview.md` rule 1 after adding gate clauses, state directory initialization, behavior decisions, and Mermaid process diagram.
- Verified 3-to-3 `E-*`/`V-*` bijection, `- Highest E allocated: 03`, valid `- Scope-Paths:` and `- Item-Dependencies:`, zero em/en dashes in user-facing text, and `0` findings across all severities from `aw ipd lint --phase review-finalize --agent` (`clean`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261109-metastore-146-iqhzse-move-the-setter-staleness-lifecycle-and-runner-merge-path-gi.ipd.md:167 | `Approval and execution gate` omitted conditional runner vs. standalone executor ownership of `aw ipd finalize`, explicit scope fence boundary clarification, and narrow unsafe-condition stop rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added conditional runner vs. executor ownership clause, scope fence clarification, and narrow stop rule to Gate (recommendation strength: very strong). |
| PR-002 | MEDIUM | IN-SCOPE | R2 / R4 / PIN-FIRST rule | .aw/records/plans/pending/20261109-metastore-146-iqhzse-move-the-setter-staleness-lifecycle-and-runner-merge-path-gi.ipd.md:38 | PIN-FIRST rule redirected baseline dumps into `.aw/state/t4gl15/` without directory initialization (`mkdir -p .aw/state/t4gl15 .aw/state/iqhzse`), which fails in fresh isolated lane worktrees where `.aw/state/` does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `mkdir -p .aw/state/t4gl15 .aw/state/iqhzse` in the PIN-FIRST rule (recommendation strength: strong). |
| PR-003 | MEDIUM | IN-SCOPE | R1 / R4 / Findings & Behavior decisions | .aw/records/plans/pending/20261109-metastore-146-iqhzse-move-the-setter-staleness-lifecycle-and-runner-merge-path-gi.ipd.md:91 | `## Findings` stated decisions were copied from `t4gl15`, but omitted D-2 through D-5 covering merge stages, frozen digests, landing byte equality, and directory initialization. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Expanded `## Findings` to document D-1 through D-5 under `### Behavior decisions` matching `t4gl15` and `h58z9n` (recommendation strength: strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Requirement 12(b) | .aw/records/plans/pending/20261109-metastore-146-iqhzse-move-the-setter-staleness-lifecycle-and-runner-merge-path-gi.ipd.md:101 | `Proposed changes` lacked a Mermaid `flowchart TD` diagram required by Technical Writing Standard Requirement 12(b) for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram under `Proposed changes` showing the 3-step staged pipeline (recommendation strength: strong). |
| PR-005 | LOW | IN-SCOPE | R1 / S5 / OQ-01 | .aw/records/plans/pending/20261109-metastore-146-iqhzse-move-the-setter-staleness-lifecycle-and-runner-merge-path-gi.ipd.md:145 | `OQ-01` recorded `- Owner: none` on a resolved question, violating the owner attestation standard in `steps/s5-questions.md`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set `- Owner: plan author` on OQ-01 and logged the decision in `### Decisions` (recommendation strength: strong). |
| PR-006 | LOW | IN-SCOPE | Proofreading / Requirement 7 / S7 | .aw/records/plans/pending/20261109-metastore-146-iqhzse-move-the-setter-staleness-lifecycle-and-runner-merge-path-gi.ipd.md:9, .aw/records/plans/pending/20261109-metastore-146-iqhzse-move-the-setter-staleness-lifecycle-and-runner-merge-path-gi.ipd.md:22, .aw/records/plans/pending/20261109-metastore-146-iqhzse-move-the-setter-staleness-lifecycle-and-runner-merge-path-gi.ipd.md:63 | Plan retained an imperative authoring-prompt note, used unqualified `module.function` citations in `Step 0`, and omitted review readiness and tier in front matter. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced authoring prompt with declarative conformance note, converted `Step 0` citations to repo-relative `path::Symbol` identifiers, added `- Readiness: go-pending-approval` and `- Review-Depth: complex` to front matter, and transitioned `- Status: reviewed` via `aw ipd set` (recommendation strength: very strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `artifact_meta.read_at` normalize status for plan records? | For PLAN records only, match `plans.normalize_status` of the FIRST token of the cached raw value (`executed` for `EXECUTED`/`DONE`, `legacy/unknown` otherwise); all other record types use exact single-token matching. | Use raw unnormalized status across all readers; normalize non-plan vocabularies (rejected: corrupts non-plan statuses). | `t4gl15` D-1, `4sd62s` Section 4.3 | yes |
| D-2 | How should merge-stage git blobs be resolved by `artifact_meta`? | Attempt `read_at(id6, ":<stage>:")` first; if rejected by `read_at`, pass blob text to `artifact_meta.read_text`, recording the chosen path in F-03. | Hand-parse raw markdown bullets in `runner_shared` (rejected: bypasses centralized `artifact_meta` loader). | `t4gl15` OQ-02, `4sd62s` Section 4.4 | yes |
| D-3 | How should review-staleness index handle frozen-region digests? | Plan status moves to `read_at(id6, <commit>)`, while the batched `git cat-file --batch` body read stays for the frozen-region digest (body prose, N3). | Attempt to extract frozen-region digests through metadata state (rejected: frozen regions are body markdown content). | `agent_workflows/plan_readiness.py`, `4sd62s` N3 | yes |
| D-4 | How should lifecycle landing verification check plan edits before landing? | Byte equality check of landed blob vs mirrored bytes remains a raw byte comparison; status or id validations use `read_at`. | Route byte comparison through replayed metadata state (rejected: does not detect body-text edits). | `agent_workflows/ipd_lifecycle.py::_release_own_plan_edit_before_landing` | yes |
| D-5 | Where should baseline test outcome lists be preserved across isolated lane worktrees? | Preserve `.aw/state/t4gl15/` as the baseline directory with explicit initialization (`mkdir -p .aw/state/t4gl15 .aw/state/iqhzse`). | Use plan-specific `.aw/state/iqhzse/` only (rejected: breaks finishing parent `h58z9n`'s residual audit comparison). | `h58z9n` E-05, `t4gl15` Task group 3 | yes |
