- Id: qzxt1m
- Status: open
- Blocks-Release: next
- Set: qzxt1m
- Priority: high
- Work-Kind: bug
- Summary: A stranded run still exits 0, which spec 25kzda:1057 defines as every actionable item verified

## Workflow history
- 2026-09-20 created (aw backlog): Carried forward from plan ys1dor OQ-01, which was deferred to the maintainer NON-BLOCKING and is now filed so the machine-readable half of the lie has a durable carrier. ys1dor made the run summary print a red STRANDED for a run whose own record says integration was refused, but deliberately did NOT touch the process exit code: that is a public contract with CI consumers, and changing it was outside a one-rendering-file fence. THE GAP: spec 25kzda:1057 defines exit 0 as 'Every actionable item is verified; remaining items were benign skips', and a stranded item is NOT verified (it kept a success-tuple status while its own record recorded an integration refusal). Read literally, a stranded run exiting 0 already violates that row, so the question is not 'should we add a behavior' but 'is the current exit code already wrong'. TWO COMPLICATIONS the plan measured: (1) the exit-code table is already internally unreconciled (25kzda:1061 records that the spec row 4 and the shipped aw runs table disagree from 4 upward, and the drivers return only 0/2/130/143 today), and (2) exit 1 is defined as 'at least one item failed, ended dependency_not_met, or ended ran/unavailable without --unverifiable-ok', which a stranded item matches none of, so honoring the intent needs either widening 1 or minting a new code. Both are public contract changes needing the spec path in Scope-Paths. Note aw attention --check already gives automation a fail-closed signal without touching the run exit contract, so nothing is blocked. NEEDS A MAINTAINER DECISION on scope and on whether to widen 1 or mint a new code.
