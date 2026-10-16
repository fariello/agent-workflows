# Review findings: plan c54a4z

- Subject-Id: c54a4z
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane after `aa43a6177` (the `ppu39q` review). The plan was committed (`fa52d1582`) and byte-identical to the lane input, so no pre-review snapshot was taken. The plan's own first `- Kind:` bullet reads `orchestrator`. `aw ipd lint --phase author --agent` reported `clean` (0 findings), so there were no `IPD-S407` violations and no repair loop was needed. `aw ipd coverage c54a4z` printed "Orchestrator c54a4z is ready for review." both before and after the revisions, so no `IPD-S408` repair loop was needed either. The coverage re-check refreshed `- Coverage-Fingerprint:` and added a history line, both tool-written.

Verified:
- All five child files exist under `pending/`. Their `- Order:` values are 1 to 5, and each carries `- From-Backlog: ui1aln` and `- Blocks-Release: next`. Their `- Item-Dependencies:` match the Child IPDs table (`executed:ppu39q`, `executed:xvlemm`, `executed:xvlemm, executed:gjylny`, `executed:6u755v`).
- The parent carries orchestration items only (E-01..E-05 confirm the children). It has no deliverable of its own.
- Every completion criterion names an owning child E-range.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G (cross-plan contract) | `ppu39q` E-02 after review PR-001 (two-branch `config_placement_switch`, `label` branch only with `existing_policy`); `xvlemm` E-01 "Detection reuses `install_wizard.config_placement_switch`" and E-02 `companion-unsupported` | After the `ppu39q` revision, a planner that calls the detector without `existing_policy` gets `None` for a companion pair, because writer and reader resolve to the same in-tree dir. It would then report `not-a-placement-switch` instead of `companion-unsupported`. The cross-IPD validation bullet did not carry this obligation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The cross-IPD bullet now states the `PlacementSwitch` return shape and requires the planner to pass the stored policy as `existing_policy`. xvlemm V-01 owns the check. |
| PR-002 | LOW | IN-SCOPE | Honest docs (child table) | `ozr356` Scope "`--relocate` ... `--relocate-resume` and `--relocate-rollback`" | The Child IPDs row for Order 05 omitted `--relocate-resume`. | Overall:Low | FIXED | Row updated. |
| PR-003 | LOW | IN-SCOPE | Traceability | `gjylny` E-04 "Mutation proof: temporarily make `side=\"target\"` fall through" | Completion criterion 4 cited gjylny `E-01..E-03`, which omitted its E-04 mutation proof. | Overall:Low | FIXED | The criterion now cites `E-01..E-04`. |
| PR-004 | LOW | IN-SCOPE | Traceability | `ozr356` V-04 "pasted `git diff -- CHANGELOG.md README.md`"; V-05 "`tests/test_placement_switch_cli.py` with every case PASSED" | The cross-IPD bullet for end-to-end tests named ozr356 V-04, which is the docs check. The tests are E-05 and V-05. | Overall:Low | FIXED | The bullet now names `E-05, V-05`. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean` (0 findings). `aw ipd coverage c54a4z`: ready for review.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where should the planner's `existing_policy` obligation live? | In the orchestrator's cross-IPD validation, owned by xvlemm V-01. | Edit xvlemm directly (REJECTED: xvlemm is outside this review's ledger, and it will get its own review). | `.aw/system/workflows/plan-review/plan-review.md` 2.4 "fix it in the owning plan and cross-reference it from dependent plans"; ppu39q owns the shape, and c54a4z is the cross-reference surface. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
