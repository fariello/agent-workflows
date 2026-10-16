- Id: 66ls4r
- Status: done
- Graduated-To: runledger
- Set: runledger
- Priority: low
- Work-Kind: chore
- Summary: Spec 25kzda 1.2 step 8 and 5.1 still require a tamper-evident run ledger for driver runs, contradicting the rdjka2 option (b) decision; no follow-on amendment exists

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD 9epp40 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-runledger-04-9epp40-amend-spec-25kzda-1-2-step-8-and-5-1-to-scope-the-hash-chain.ipd.md); evidence .aw/records/plans/executed/20261014-runledger-04-9epp40-amend-spec-25kzda-1-2-step-8-and-5-1-to-scope-the-hash-chain.ipd.md
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131029Z-4042525: 9epp40
- 2026-10-12 created (aw backlog): Filed while authoring plan v47z9u from backlog hegwri: rdjka2 Spec/documentation sync names this follow-on and none was found.

Executed plan rdjka2 resolved OQ-01 to option (b) on 2026-10-08 (decision record utb2qr): driver runs keep state.json/events.jsonl and do not write a ledger. Its Spec / documentation sync section states that this creates a DIVERGENCE from approved spec 25kzda, whose Scope is the aw oc run / aw agy run verb, whose Section 1.2 step 8 requires capturing evidence 'in a tamper-evident run ledger', and whose Section 5.1 lists 'the append-only, hash-chained run ledger' as admissible completion input, and that it must be closed by a FOLLOW-ON plan that either amends 25kzda to scope the ledger requirement to the aw run path or records an accepted dated divergence. Searched 2026-10-12 (backlog and pending plans for 25kzda plus ledger, 'divergence', 'step 8'): no such carrier exists. Plan v47z9u (from hegwri) amends only Section 6.2's storage-location bullet and deliberately does not touch 1.2 or 5.1, because choosing between amendment and accepted divergence is a public-contract decision for the maintainer.
