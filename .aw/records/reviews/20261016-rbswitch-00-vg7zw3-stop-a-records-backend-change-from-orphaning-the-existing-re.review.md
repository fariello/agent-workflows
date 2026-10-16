# Review findings: plan vg7zw3

- Subject-Id: vg7zw3
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane after the `s07f73` review commit `d2e525084`. The plan was committed and unchanged, so no pre-review snapshot was taken. The plan is an orchestrator (first `- Kind:` bullet). `aw ipd lint --phase author --agent`: `clean`, zero findings (no `IPD-S407`). `aw ipd coverage vg7zw3`: "Orchestrator vg7zw3 is ready for review." (no `IPD-S408` findings; no repair loop needed).

Verified:
- Child table matches the three children on disk: `s07f73` (Order 1), `fxbm7j` (Order 2), `vv9ki4` (Order 3), each `- Set: rbswitch`, `- From-Backlog: wbz75c`, `- Blocks-Release: next`, matching this plan's gate.
- Depends-on column matches each child's `- Item-Dependencies:` exactly (`executed:ppu39q`; `executed:s07f73, executed:6u755v`; `executed:fxbm7j, executed:ozr356`).
- Completion criteria and cross-IPD owners resolve: `fxbm7j` E-05 case (8) is the mode-blocking journal test; `fxbm7j` V-01 demands the `records_root_switch` call in `plan_records_root_switch`; `vv9ki4` V-05 demands `make test-all`.
- OQ-01 evidence: `c54a4z` Deferred lists "A `--records-backend` change on an installed repo that keeps the config placement ... distinct root cause" with `Carrier: wbz75c`.
- E-items are orchestration only (confirm each child executed); `aw find plans s07f73` currently prints the `pending/` path, so V-01 is correctly pending.
- Gate carries an execution contract with conditional runner/by-hand finalize ownership and no hand `git mv`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | Cross-plan consistency | `.aw/records/reviews/20261016-rbswitch-01-s07f73-refuse-a-records-root-switch-at-every-install-entry-point-an.review.md` PR-001; this plan "Companion records backends (a second git repository is involved); they keep refusing." | After the `s07f73` review count-gated the companion refusal (a companion change with nothing to orphan is a plain policy update), the orchestrator's unconditional "they keep refusing" overstated the Set's behavior. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Deferred bullet reworded: a companion records move refuses whenever the current root holds records and proceeds only when nothing would be orphaned; carrier `n9vd2h` unchanged. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`. `aw ipd coverage vg7zw3` after revisions: ready for review.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep the Set separate from `cfgreloc`? | Yes, as the plan's OQ-01 decided. | Add children to `cfgreloc` (rejected: reopens six approved plans and `c54a4z` already defers `wbz75c` as a distinct root cause). | `c54a4z` Deferred `Carrier: wbz75c`; cross-Set `Item-Dependencies` re-checked at dispatch. | yes |
