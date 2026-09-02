# Review: Lane input materialization with a sealed manifest and clean-base guard

- Plan-Id: nna8yz
- Reviewed-At: 2026-09-01
- Reviewer: codex/gpt-5
- Verdict: REVIEWED

## Round 1

Reviewed at HEAD `08ae65cb`; the plan was committed and unchanged before review. Author-phase IPD lint
returned clean and verified. The design correctly distinguishes copy independence from merely avoiding
symlinks, defines all three parts of the seal, reuses the lane-local runbook instead of recopying it,
and limits the pre-launch clean-base refusal to tracked changes.

The main execution risk is hidden size. Four OpenCode concerns plus the clean-base guard are represented
clearly, but the Antigravity implementation of all of them is combined with the guard in one final item.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G. Right-sizing / D. Anti-regression | `nna8yz:35-57`, especially E-05 at `:54-57` | E-05 combines the tracked-base refusal with mirroring materialization, inode independence, sealing and revision behavior, and attachment localization into the Antigravity driver. These have separate failure modes and test seams. One checkbox cannot reliably establish all of them in one focused pass. | C:Medium; U:Low; S:Medium; F:High; Overall:Medium | FIXED | FIXED 2026-09-01. E-05 no longer mirrors materialization: the materializer, the seal, and attachment resolution must be host-neutral, so E-05 adds only the clean-base guard plus thin wiring. The inode, owner-write-bit, revision, attachment, and dirty-base assertions are unchanged. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing and regression | Required tests `nna8yz:96-104`; baseline commit `59e68d5a`; later test changes in `8ced15ce` | The exact suite count is historical rather than an execution-time measurement. The plan's property tests are specific, but its regression comparison can become misleading as the suite grows. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | FIXED 2026-09-01. Baseline replaced with measure-at-execution-time plus failure-identity comparison; explicit assertions preserved. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does the manifest need to provide operating-system immutability? | No. Retain the approved accident-guard definition and do not widen this plan to OS confinement. | Add ownership, ACL, or sandbox hardening here. Rejected because spec R5.1a defines the seal as read-only files plus new revisions and explicitly requires honest labeling of the same-user limit. | `nna8yz:39-45`; spec `7ckptx` R5.1a | yes |

## Round 2

Disclosed self-review by the original author at HEAD `868106a4`. The finding below is fixed in the current plan and spec.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| SR-002 | HIGH | IN-SCOPE | C. Architecture / G. Plan executability | Plan `Scope-Paths` versus host-neutral instructions | Shared materialization behavior had no declared host-neutral module, making the remediation incompatible with the scope fence. | C:Medium; U:Low; S:Low; F:High; Overall:Medium | FIXED | Added spec R2.6/A5c and declared `agent_workflows/lane_containment.py`; E-05 now contains only the clean-base guard and thin wiring. |
