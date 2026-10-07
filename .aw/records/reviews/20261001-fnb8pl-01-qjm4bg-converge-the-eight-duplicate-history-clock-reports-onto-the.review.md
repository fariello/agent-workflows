# Review findings: plan qjm4bg

- Subject-Id: qjm4bg
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `c97763c85`. The plan file was committed and unchanged
(sha256 matched the sealed lane-input manifest), so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` before any edit;
`--phase review-finalize` reports `conforming` after revision. The plan's first `- Kind:` bullet
reads `child`, so `IPD-S407`/`IPD-S408` do not apply.

The plan's DESIGN is sound: a records-only convergence through the SATISFIED route, citing an
executed path, keeping the gate line, never de-gating, and declining to exploit `7lfe87`. What failed
was its PREMISE. Between authoring (2026-10-01) and review the cluster moved substantially, and
`aw check all` already reported six `check.scope-path-target-stale` errors against this plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G. Executability (stale premise) | `aw check all --agent`: 6x `check.scope-path-target-stale` on this plan; backlog `jvw1kg`/`doe2fo` histories "2026-10-03 done (aw backlog): closed by aw agy run: IPD 9wcei0 / 840y6i executed"; `fnb8pl`, `tl8qmc`, `o8l2y2`, `lq2w86` now under `backlog/graduated/` | Six of seven Scope-Paths no longer existed. E-03 would have closed `jvw1kg` and `doe2fo`, which are already `done` by their own carriers, and treated `o8l2y2` and `lq2w86` as uncarried `open` items, though both are `graduated`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope-Paths now point at the current locations. The `done/` rename targets are left undeclared because they would trip the same rule, and finalize justifies them with `--scope-reason`. E-03 now closes only `2wae2x` (still `open`, no carrier) and `lq2w86` (whose only carrier `rfyrvp` is SUPERSEDED). Concern, Scope, F-02 and Proposed changes updated. |
| PR-002 | HIGH | IN-SCOPE | D. Invariants (release gate) | `.aw/records/plans/executed/...5ivkdh...ipd.md:155` "THE GITIGNORED HISTORY SIDECAR IS NOT CONVERTED HERE"; `.aw/records/plans/pending/...dmrbqa...` (`From-Backlog: tl8qmc`, `Blocks-Release: next`); `.aw/records/plans/pending/...5xq2ng...` (`From-Backlog: o8l2y2`) | E-04 would have closed `tl8qmc` "satisfied" by `5ivkdh`. But `tl8qmc` is graduated to `dmrbqa`, which owns LOCAL-clock sites (`record_history.append`/`append_rename`) that `5ivkdh` deferred. That close would drop a gate on unshipped work. F-08's claim that "no production clock site remains" was false for the same reason. `o8l2y2` is in the same position with `5xq2ng`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 is now a verify-only item for `tl8qmc` and `o8l2y2`. F-08 corrected. OQ-02 extended. The gate forbids writing a status onto either item. |
| PR-003 | MEDIUM | IN-SCOPE | G. Stale premise | backlog `fnb8pl` history "2026-10-01 graduated (aw backlog): graduated by run ...: qjm4bg" | E-05 and V-05 said the runner would set `fnb8pl` `graduated`, and V-05 required it to still be `open`. It is already `graduated`, so V-05 could never pass. | Overall:Low | FIXED | E-05 and V-05 now expect `graduated`, closed through HANDOFF when this plan executes. |
| PR-004 | MEDIUM | IN-SCOPE | E. Evidence trail | `git show 3c55295a3 -- tests/test_backlog.py` deletes "This clock skew is live bug fnb8pl"; under `TZ=Pacific/Honolulu` the test reports `1 passed` | E-02's correction note was based on the `da04c5cf0` mask, which `5ivkdh` has since removed. The test now passes because the clock is fixed, not because of a mask. A note naming only the mask commit would be wrong. | Overall:Low | FIXED | E-02 and V-02 now name both commits. `tl8qmc`'s note also names its live carrier. |
| PR-005 | MEDIUM | IN-SCOPE | E. Evidence feasibility | Review probe at 05:39 UTC: Honolulu local `2026-10-06` / UTC `2026-10-07` (skewed), Kiritimati local = UTC (not skewed) | The claim that one of Honolulu or Kiritimati is "always inside a skew window" is false. Between 10:00 and 14:00 UTC neither zone is skewed, so a reproduction in that window proves nothing. | Overall:Low | FIXED | E-01, Required tests 1 and V-01 now require printing local and UTC dates, and at least one zone that is actually skewed. |
| PR-006 | MEDIUM | IN-SCOPE | E. Unsatisfiable bar | `aw attention --json`: `valid: false`, 5x `attention.lane-stranded`; `aw attention --blocking next` lists `jvw1kg` with `attention_class: done` | E-05 required `valid: true`, which was already false for unrelated reasons. It also required closed items to be "absent" from a view that lists done items. | Overall:Low | FIXED | The bar is now: no new violation compared with the E-01 baseline, and the closed items show `attention_class: done`. |
| PR-007 | MEDIUM | IN-SCOPE | G. Live-artifact count / execution contract | Required tests 6; gate item 8 | "Same five pre-existing failures" used an authoring-time count as the bar. The gate also told the executor to finalize unconditionally, with no runner/executor split, and did not label the scope fence as a declaration. | Overall:Low | FIXED | The suite is now compared before and after, against a re-derived baseline. Finalize ownership is conditional on whether a runner is driving the plan. The fence is labelled a declaration. |
| PR-008 | LOW | IN-SCOPE | G. Consistency | Goal | The Goal of "ONE live owner" contradicted the corrected design, in which `dmrbqa` and `5xq2ng` legitimately keep their own gates. | Overall:Low | FIXED | Goal restated. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should `lq2w86` close here, given it is `graduated`? | Yes, SATISFIED by the executed `5ivkdh`, with the message naming the superseded `rfyrvp` and the absorbing `9wcei0`. | Leave it graduated to a dead carrier; re-point it to `9wcei0`. | `.aw/records/plans/superseded/...rfyrvp...ipd.md` "Superseded by pending plan 9wcei0"; `--dry-run` close returned clean with evidence and exit 1 without | yes |
| D-2 | Should `tl8qmc` and `o8l2y2` close here? | No; verify only. | Close as SATISFIED (authored). | 5ivkdh Deferred row on the sidecar; carriers `dmrbqa`/`5xq2ng` live and gated | yes |
| D-3 | Keep the `executed:ayhveg` edge although `ayhveg` is not yet executed? | Keep it; the runner holds the plan `dependency-blocked` until then. | Drop the edge to unblock now. | Plan's own OQ-02 (the guard must ship before the duplicates close honestly); AGENTS.md runner semantics | yes |
| D-4 | What bar replaces `valid: true`? | No new violation compared with the E-01 baseline, plus `attention_class: done` on the closed items. | Keep `valid: true`; drop the attention check. | Measured `valid: false` from 5 unrelated stranded lanes | yes |
