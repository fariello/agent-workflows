- Id: v1re2z
- Status: done
- Graduated-To: uypgvi
- Blocks-Release: next
- Set: uypgvi
- Priority: medium
- Work-Kind: bug
- Summary: release_readiness: report a gate whose input files are absent as not-applicable instead of failing, so installed release-review is usable in managed repos

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD 4bw2u5 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261016-uypgvi-02-4bw2u5-release-readiness-report-a-gate-whose-input-files-are-absent.ipd.md); evidence .aw/records/plans/executed/20261016-uypgvi-02-4bw2u5-release-readiness-report-a-gate-whose-input-files-are-absent.ipd.md
- 2026-10-16 graduated (aw backlog): graduated by run run-20261016T145446Z-2140972: 4bw2u5
- 2026-10-15 created (aw backlog): release_readiness: report a gate whose input files are absent as not-applicable instead of failing, so installed release-review is usable in managed repos

Maintainer decision 2026-10-15 on kmmoca OQ-03: release-review in every repo runs aw releases readiness; a gate whose producer/input is absent (docs/, host_matrix.json, workflow catalog bookkeeping, workflow.yaml packages, CHANGELOG) reports not-applicable and does not force NO-GO. In this repository all inputs exist, so every gate runs in full. Known risk accepted: a repo that deleted an input by mistake sees not-applicable rather than failure; report the N/A gates prominently. Plan kmmoca depends on this.
