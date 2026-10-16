- Id: upryxf
- Status: done
- Graduated-To: selquiet
- Blocks-Release: next
- Set: selquiet
- Priority: medium
- Work-Kind: bug
- Summary: aw show exits 1 on a zero-match selector, not 2 as the zyj8io survey recorded

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD uhp38x executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-selquiet-03-uhp38x-make-aw-show-refuse-a-zero-match-selector-with-exit-2-and-dr.ipd.md); evidence .aw/records/plans/executed/20261014-selquiet-03-uhp38x-make-aw-show-refuse-a-zero-match-selector-with-exit-2-and-dr.ipd.md
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131029Z-4042525: uhp38x
- 2026-10-12 created (aw backlog): filed while graduating tbe8v0

Measured 2026-10-12 in the tbe8v0 lane: `aw show zzzzzz` exits 1 on human, --agent (outcome findings, rule show.not_found) and --json. IPD zyj8io E-08's survey table recorded `aw show <sel>` as exit 2 on every surface and Conforming; that row is wrong. Spec 25kzda Section 2.3 rules zero matches exit 2. `aw show` is the one surveyed read verb tbe8v0 did not list, so plan yxsfjc does not fix it. Its command_surface declaration is exit_contract (0, 1, 2), so the fix must also decide whether 1 stays reachable (conformance domain_failure scenario).
