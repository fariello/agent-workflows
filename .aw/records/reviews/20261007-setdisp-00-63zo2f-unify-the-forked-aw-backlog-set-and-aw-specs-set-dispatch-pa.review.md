# Review findings: plan 63zo2f

- Subject-Id: 63zo2f
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `ad22ff70a`. The plan was committed and byte-identical to the sealed lane input
(`diff` empty), so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` and
`--phase review-finalize --agent` were clean before revision; `aw ipd coverage 63zo2f` reported ready.
After revision the coverage record was stale (`IPD-S408 coverage-record-stale`), `aw ipd coverage
--no-commit 63zo2f` re-recorded `Coverage: pass`, and `review-finalize` returned clean (attempt 1 of 2).

Re-measured at review: every child's `- Status:`/`- Item-Dependencies:` line; carrier state of every
id6 the plan names (`find`/`grep '^- Id:'` under `.aw/records`); the overlapping `setdispgate` plans'
front matter and gate prose.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | C. Duplicate paths / release gates | `.aw/records/plans/pending/20261002-setdispgate-01-wdyz5n-...ipd.md:15` `- From-Backlog: h4fiwa`, `:8` `Item-Dependencies: none`; `...setdispgate-02-ju3rhs-...ipd.md:15` `- From-Backlog: fv4b6s`, `:10` `Status: approved`; `...setdisp-03-m1jlwm-...ipd.md:14` `- From-Backlog: fcnz1r` | The orchestrator never mentions that the two release-gated bypasses child 03 fixes already have their own ungated carrier plans (`wdyz5n`, `ju3rhs`), which are the only plans carrying the `h4fiwa`/`fv4b6s` gates and will likely execute before `m1jlwm`. E-03/V-03 demanded `m1jlwm` close both items via the SATISFIED route, which may be impossible or produce a second copy of each refusal. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03, V-03, child-sequence prose, completion criteria and cross-IPD partial-close check now name the overlap, accept HANDOFF or SATISFIED, require exactly one implementation observed behaviorally, and allow `m1jlwm` retirement; OQ-02 added and resolved. |
| PR-002 | MEDIUM | IN-SCOPE | G. Sequencing / stale evidence | `.aw/records/plans/executed/20260930-histlabel-01-jbipfa-...ipd.md`; `.aw/records/plans/executed/20260929-ipdsetback-01-nvsz19-...ipd.md`; `...bjcz05-01-ulepef-...ipd.md:9` `Status: approved`; `...setdisp-04-m94eht-...ipd.md:8` (no `ulepef` edge), `:255` "Plan `ulepef` must also have landed" | "Three live artifacts must land before 04 and 05" was stale: `jbipfa` and `nvsz19` are executed and `ulepef` is `approved`, not `to-review`. The remaining real prerequisite (`ulepef` before `m94eht`) is enforced by no dependency edge and checked by no item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Paragraph rewritten with re-derived states and a re-derive-at-execution instruction; E-04 expected outcome and V-04 evidence now require `ulepef` executed before `m94eht`, with commit dates. |
| PR-003 | MEDIUM | IN-SCOPE | G. Executability | plan Completion criteria "All five children"; Approval gate "ALL FIVE children"; child table row 06 `7zb4ny` | After Order 06 was added, two completion statements still counted five children, so the Set could be declared done with the audit child unrun. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both changed to six; Scope line names the audit child. |
| PR-004 | LOW | IN-SCOPE | G. Live-artifact criteria | `.aw/records/backlog/done/*r74211*`, `*19lmbe*`, `*t1gbwg*`, `*mbjuv5*`, `*68sur3*` all `- Status: done` | Completion criterion "every Section 7 axis remains OPEN under its own carrier" is already false for five carriers closed by their own work, so it was unsatisfiable; the `aw prompts set` deferral described a still-dead verb whose carrier is done. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Criterion restated as a property (live, or closed by its own carrier, never by this Set without measured COMPLETE), with re-derivation; `68sur3` bullet updated. |
| PR-005 | LOW | UNDER-SCOPE | G. Execution contract | plan "Approval and execution gate" Post-gate lifecycle | Gate did not state runner-vs-hand ownership of the orchestrator's terminal transition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added: runner rollup retires it; a hand executor verifies V-01..V-06 then uses `aw ipd finalize`, never a hand `git mv`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which plan owns the `h4fiwa`/`fv4b6s` fixes? | Keep all three; whichever lands first owns each refusal, the other consumes it; `m1jlwm` may be retired by a maintainer | Retire `wdyz5n`/`ju3rhs` and move their gates to `m1jlwm`; retire `m1jlwm` now | `wdyz5n` gate "Whichever of the two executes SECOND must consume"; `ju3rhs` gate "whichever executes second must REBASE ONTO the first"; both carry the items' `From-Backlog` | yes |
| D-2 | Add an `executed:ulepef` edge to `m94eht`? | No; the orchestrator's E-04/V-04 check the ordering instead | Edit child `m94eht` front matter (outside this review's scope) | `m94eht` gate prose already requires it; plan-review edits only the reviewed plan | yes |
