- Id: 67n5as
- Status: open
- Blocks-Release: next
- Set: revsteps
- Priority: high
- Work-Kind: feature
- Summary: author k3yx72 Stage 2 plans (Orders 03, 06, 07, 08, rest of 05)

## Workflow history
- 2026-10-26 created (aw backlog): author k3yx72 Stage 2 plans (Orders 03, 06, 07, 08, rest of 05)

### Problem Statement

Spec `k3yx72` (Plan Review Redesign) defines a two-stage rollout (MD-20): Stage 1 implemented the core infrastructure (Orders 01, 02, 04, minimal 05, and pilot 09 under IPD `kk62qt`). The review pilot executed under `kk62qt` with results recorded in findings report `.aw/records/research/20261017-revsteps-06-2m4i0o-review-pilot-results.findings.md`. Following the Section 13.5 gate evaluation (`MD-20 gate: OTHERWISE`) and maintainer consultation via `/askme` on 2026-10-26, the maintainer ruled **BUILD THE REST**.

Stage 2 implementation plans can now be authored to complete the remaining orders of spec `k3yx72`.

### Scope and Target Orders

Author child IPDs in Set `revsteps` covering the following Stage 2 work defined in spec `k3yx72` Section 14:
- **Order 03**: Citation resolver, its review and `aw ipd begin` integration, and the `20260802-1904` Section 10.2 amendment (depends on Order 09).
- **Order 05 (rest)**: The no-go clearing path of Section 9.4 (`AW-MATERIAL` marker, reviewed-contract hash test, `recheck-readiness` or targeted re-review; may be two plans; depends on Order 04 and Order 09).
- **Order 06**: Split step, including graph changes and `RETIRED` header on retirement through `aw ipd set superseded` (depends on Order 04 and Order 09).
- **Order 07**: Retire `/plan-review-long` (workflow, shims, index, installer entries, current docs, tests; depends on Orders 01, 04, 09).
- **Order 08**: Records README and `AGENTS.md` pointers: read a tree's README before editing an artifact in it (depends on Orders 01, 03).

### Reference Documents

- Spec: `.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md`
- Pilot Findings Report: `.aw/records/research/20261017-revsteps-06-2m4i0o-review-pilot-results.findings.md`
