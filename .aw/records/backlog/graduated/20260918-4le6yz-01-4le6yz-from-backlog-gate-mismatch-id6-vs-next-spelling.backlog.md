- Id: 4le6yz
- Status: graduated
- Graduated-To: gatesame
- Blocks-Release: next
- Set: 4le6yz
- Priority: medium
- Work-Kind: bug
- Summary: check.from-backlog-gate-mismatch fires on an id6-vs-next gate spelling difference that denotes the SAME release

## Workflow history
- 2026-09-25 graduated (aw set): graduated into gatesame (plan ooydp3); verified live at 8e74dcac
- 2026-09-18 created (aw backlog): check.from-backlog-gate-mismatch fires on an id6-vs-next gate spelling difference that denotes the SAME release

Found while executing plan `di08i9` (Set `nobugship`), establishing that plan's required CHECKER
baseline. It is adjacent to that plan's concern but outside its declared `- Scope-Paths:`, so it is
filed rather than fixed there.

WHAT IS WRONG. `check_engine.check_release_gate_consistency` rule 2 compares a `From-Backlog`
carrier's `- Blocks-Release:` against its backlog item's by RAW STRING EQUALITY
(`if carrier_br != item_br`), but the field has two spellings that resolve to the SAME release: the
literal `next` and the release's own id6. `releases.resolve_release` accepts both, and today
`next` resolves to `f33nrj`. So a carrier that says `f33nrj` and an item that says `next` are
reported as a broken handoff when the gate is in fact identical and correctly preserved.

MEASURED, on the live tree at HEAD `af5fa26e`:

```text
check_release_gate_consistency -> 2 findings, both check.from-backlog-gate-mismatch
  .aw/records/plans/pending/20260912-doctorprobe-01-h90ij1-...ipd.md
    "From-Backlog plan's Blocks-Release 'f33nrj' does not match backlog item hdhzr2's Blocks-Release 'next'"
  .aw/records/plans/pending/20260912-migleftover-01-z1yefm-...ipd.md
    "From-Backlog plan's Blocks-Release 'f33nrj' does not match backlog item x15f0q's Blocks-Release 'next'"
```

Both are false positives by the rule's own stated purpose: the rule exists to catch a DROPPED
handoff (a plan that is non-blocking though it graduated from a blocking item), and in both cases
the gate was preserved, just written in the other accepted spelling.

WHY IT MATTERS, i.e. why this is a `bug` and not a `chore`: the rule is registered at ERROR severity
in the EXIT-BLOCKING sweep, so these findings fail `aw check` for a user who has done nothing wrong,
and the only ways out are to rewrite a correct field or to ignore an error-severity finding. Both
teach the wrong lesson, and standing noise in an exit-blocking sweep erodes the signal that makes
the rule worth having.

SUGGESTED FIX. Compare RESOLVED releases rather than raw strings: resolve both sides through
`releases.resolve_release(repo_root, value)` and flag only when they differ (treating an unresolvable
value as already covered by `check.blocks-release-dangling`). That preserves the dropped-handoff
detection exactly while removing the spelling sensitivity.

RELATED, worth checking in the same pass: `evaluate_blocking_close`'s HANDOFF branch also compares
`carrier_br == blocks_release` by raw string, so the same spelling difference could make a
legitimate handoff close be refused.
