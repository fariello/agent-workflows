- Id: bkprhk
- Status: done
- Graduated-To: evidpend
- Set: evidpend
- Priority: low
- Work-Kind: followup
- Summary: Carrier-Evidence (evaluate_carrier_obligation SATISFIED) and spec citations still accept a non-terminal artifact as evidence; decide whether they should share the backlog close's executed-plan rule from 7lfe87

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD 3392n9 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-evidpend-02-3392n9-require-executed-plans-in-carrier-evidence-and-implemented-s.ipd.md); evidence .aw/records/plans/executed/20261014-evidpend-02-3392n9-require-executed-plans-in-carrier-evidence-and-implemented-s.ipd.md
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131029Z-4042525: 3392n9
- 2026-10-12 created (aw backlog): Filed while graduating 7lfe87 (plan ncmugb). ncmugb deliberately confines its executed-plan rule to check_engine.evaluate_blocking_close's SATISFIED arm and leaves the shared check_engine.resolve_evidence_artifact unchanged, because two other callers read it: specs._evidence_resolvable (already stricter, unaffected) and check_engine.evaluate_carrier_obligation (Carrier-Evidence). MEASURED at HEAD 319da03a9: executed plan 20261002-mt6j1p-01-wyk11f-... carries '- Carrier-Evidence: .aw/records/plans/pending/20261001-tf4jz5-01-j7dsci-...ipd.md', a pending plan that exists, so tightening the shared resolver would turn that row into a new check.ipd-uncarried-obligation error on an executed plan that may not be edited. Seven other Carrier-Evidence rows cite pending/ paths that no longer exist and already fail. The open question: should Carrier-Evidence citing a plan require executed/ (and a cited spec require implemented), and if so how are existing rows grandfathered. Classified followup, not bug, because a Carrier-Evidence row does not drop a release gate; the maintainer may reclassify.
