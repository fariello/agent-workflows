# Review findings: plan z2xs98

- Subject-Id: z2xs98
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `1d1701d21`. The plan was committed and byte-identical to the lane
input (sha256 `7762d3be...`), so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean`.
The plan is not an orchestrator.

Verified:
- `aw backlog new ... --set trimgap --priority low --work-kind chore` in preview mode would write `.aw/records/backlog/open/20261016-trimgap-01-<id6>-<slug>.backlog.md` and prints a duplicate-candidate report. A preview with `--work-kind bug --blocks-release next` also runs cleanly. The verb has no commit option.
- The single `planned` release is `f33nrj` 2.0.0. `9qvfie` is `graduated` with no `- Blocks-Release:`.
- `aw check --agent` reports 75 findings at review (3 error, 1 warning, 71 info), so the before/after comparison in E-04 is the right bar.
- `.aw/records/backlog/blocked/` does not exist. The plan's grep exits 2 on it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Rubric D (dropped outcomes) | `8dyt88` E-04 "Order 06 (`z2xs98`) must carry a `replay-unverified` file as a gap exactly like `exclusive-now`"; `hpjj44` `## Reconciliation` (d) lists `property-unidentifiable` as carrier-needed; `24h56i` E-03 allows a final `unprovable` | The gap collection omitted `replay-unverified` files, `property-unidentifiable` keys and a non-`guarded` `PROP-02`. Those outcomes would get neither a carrier nor a carrier-free class, so the reconciliation would hide them. | all Low | FIXED | Scope, E-01 and E-03 now list these classes. E-01 lists every carrier-free class explicitly. V-01 checks that each source item is either grouped or named carrier-free. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric D (release gate) | E-02 "up to 15 ... ONE residual `chore`"; `AGENTS.md` "Every live bug gates the next release" | A `regression` group past the cap would be rolled into the `chore` residual and lose its `bug` classification and release gate. | all Low | FIXED | Regression groups are never rolled up and are filed individually past the cap. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric G (cross-plan contract) | `rf1xxr` `## Deferred` "Keys left `budget-exhausted`: Order 06 files them as one grouped item" | Grouping per (module, remedy) contradicted the single-item carrier that `rf1xxr` declares for `budget-exhausted` keys. | all Low | FIXED | E-01 now puts all `budget-exhausted` keys in one group with remedy `probe then restore`. |
| PR-004 | LOW | IN-SCOPE | Rubric G (executability) | `ls .aw/records/backlog` has no `blocked/`; `grep` exit 2 | The dedupe grep fails on an absent status directory. Self-hits on `9qvfie` and the `trimcarry` plans were not excluded. Nothing stated that `aw backlog new` leaves files uncommitted until E-04. | all Low | FIXED | Added `-s` and the self-hit exclusion. Added the commit note to E-02, a `git status` demand to V-02, and review measurements as F4/F5. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should regressions past the 15 cap be rolled up? | No. Each is filed as its own `bug` with `--blocks-release next`. | Raise the cap for everything (REJECTED: it inflates chores). Roll them up (REJECTED: a chore cannot carry the gate). | `AGENTS.md` "Every live bug gates the next release". | yes |
| D-2 | How should `budget-exhausted` keys be grouped? | One group, as `rf1xxr` declares. | Per module (REJECTED: contradicts the sibling's declared carrier). | `rf1xxr` `## Deferred`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
