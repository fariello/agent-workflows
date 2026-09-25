- Id: 0cqf33
- Status: done
- Set: 0cqf33
- Priority: medium
- Work-Kind: bug
- Summary: check.from-backlog-gate-mismatch compares gate spellings literally, so next versus its resolved release id6 reads as a broken handoff

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: duplicate of 4le6yz
- 2026-09-18 created (aw backlog): check.from-backlog-gate-mismatch compares gate spellings literally, so next versus its resolved release id6 reads as a broken handoff

FOUND 2026-09-18 while executing nobugship rgaasb E-05, as the explanation for a baseline this plan could not clear. PRE-EXISTING.

WHAT IS WRONG. check_engine.check_release_gate_consistency compares a carrier's - Blocks-Release: to its item's with a plain string comparison (carrier_br != item_br). 'next' and the id6 it resolves to are TWO SPELLINGS OF ONE GATE, so a carrier spelling the gate one way under an item spelling it the other is reported as a DROPPED HANDOFF when the gate is in fact intact and identical.

MEASURED at HEAD 8087387e. Two of the repository's findings are exactly this, and they are the entire live check.from-backlog-gate-mismatch baseline:

    .aw/records/plans/pending/20260912-doctorprobe-01-h90ij1-....ipd.md   - Blocks-Release: f33nrj
      its item hdhzr2   - Blocks-Release: next
    .aw/records/plans/pending/20260912-migleftover-01-z1yefm-....ipd.md   - Blocks-Release: f33nrj
      its item x15f0q   - Blocks-Release: next

and releases.resolve_release(repo, 'next') returns the f33nrj record, so both pairs name the SAME
release. Neither is a broken handoff, and both sit in an exit-blocking sweep as ERRORs.

WHY IT MATTERS. It is a FALSE POSITIVE in a fail-closed rule, which is the expensive direction: it
teaches a reader that these two plans dropped a gate they did not drop, and an agent trying to clear
the sweep is pushed toward editing another party's artifact to change a spelling that was never
wrong. The parent Set qmgn12 already noted that every gated backlog item spells the gate as the
literal 'next', so the mixed-spelling case is rare today but is created by any tool or author that
writes the id6 form, which - Blocks-Release:'s own help text explicitly invites ('a release id6,
'next', or '-' to clear').

SUGGESTED FIX. Resolve BOTH sides through releases.resolve_release before comparing, and compare
release IDENTITY rather than spelling; fall back to the literal comparison when either side does not
resolve, so a genuinely dangling value stays visible to check.blocks-release-dangling.

NOT FIXED BY rgaasb DELIBERATELY: the only shipped-rule change that plan was authorized to make is
the terminal-carrier narrowing the maintainer ruled on, and both affected plans are another party's
artifacts outside its population. Recorded as this plan's stated baseline of 2 instead.
