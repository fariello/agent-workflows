# Review findings: plan 0bjke0

- Subject-Id: 0bjke0
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T030816Z-4078927` at HEAD `7246858d3`. The plan was
committed and byte-identical to the sealed lane input (rev-2); no snapshot needed. `- Kind: child`, so `IPD-S407`
and `IPD-S408` do not apply. `aw ipd lint --phase author` clean before review; `review-finalize` clean after.

Re-measured anchors in spec `25kzda`: `### 4.1 Message and recovery conventions`, `### 5.3 Durable state and
restartability`, `#### 5.3a Per-invocation telemetry`, the paragraph "The frozen driver record within durable run
state must name the module that created the run", "A snapshot is a cache; replaying the ledger is authoritative",
`### 6.1 Limits` (items 1-9, so A.4's `10.` is correct), and one `- Status: approved` line; `aw specs check` on the
spec is clean. History lines use the `AMENDED <date> (plan <id6>...)` form via `aw specs note`. Code: begin's
pre-execution refusal (`ipd_lifecycle.begin`) already returns its findings and the `ipd begin` CLI prints them, and
`runner_shared.driver_begin` records both streams as `item["begin_refusal"]`; `runner_shared.locked_run` holds
`driver.lock` under spec `c4gd2h` R2. gradcover children touching `agent_workflows/`: 10 of 13 (Scope-Paths and
commits since 2026-10-06 09:00), not 12.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | C architecture / cross-child contract | A.1 point 4-5 name only `driver-restarted` and "a named refusal"; re15ol uses `driver-restart-limit` and `AW_NO_DRIVER_RESTART`, 34zv7d emits `driver-restart-unavailable`, hohlc6 depends on the env var | The contract Orders 02-05 implement left their observable names and the disable switch unspecified, so the children define contract surface no spec carries. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A.1 now names all three events and `AW_NO_DRIVER_RESTART=1` (test-only purpose); E-03 and validation greps cover them. |
| PR-002 | MEDIUM | IN-SCOPE | A correctness / spec-to-code accuracy | A.3 lists "begin" among checkpoints; `ipd_lifecycle.begin` returns `findings=finding_lines` and the CLI prints `  IPD-BEGIN <finding>`; vvqr34 Scope covers finalize and retirement only | A.3 would oblige begin behavior no child implements (and that already exists), leaving the spec's begin clause unverified by Set `runfresh`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A.3 scoped to finalize (pre/post) and retirement, with a note that begin already carries its findings. |
| PR-003 | MEDIUM | IN-SCOPE | A correctness / honest limits | A.4 title "sees only committed, integrated code" vs its own body "code edited by hand ... is picked up"; Order 02 fingerprints file bytes on disk | Title contradicted the body and the mechanism; the half-finished-edit hazard was unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Retitled "sees the code on disk, not only integrated code" and states the import-failure consequence and recovery via `resume`. |
| PR-004 | LOW | UNDER-SCOPE | C operability | A.1 point 2 "releases the run lock"; `runner_shared.locked_run` / spec `c4gd2h` R2; re15ol E-03 | Did not tie lock release to the c4gd2h invariant `os.execv` would otherwise break, nor say "the CURRENT process" for the compared fingerprint (point 5 relies on it). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Point 2 cites `c4gd2h` R2 and compares against the current process's loaded code. |
| PR-005 | LOW | IN-SCOPE | G evidence | OQ-01 "the 14-item `gradcover` run had 12 such items"; re-measured 10 | Stale measured figure in a resolution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected to 10 with method; conclusion (20 suffices) unchanged. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the spec name the restart disable switch? | Yes, as a test-only env var | leave it to the child docstring (undocumented contract) | re15ol "A FLAG TO DISABLE THE RESTART"; hohlc6 Scope | yes |
| D-2 | Keep "begin" in A.3? | No; finalize and retirement only, note begin already complies | add begin work to vvqr34 (already done in code) | `ipd_lifecycle.begin` findings; `runner_shared.driver_begin` | yes |
