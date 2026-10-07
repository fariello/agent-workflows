# Review findings: plan z2l43n

- Subject-Id: z2l43n
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `e643abfd5`. The plan was committed and unchanged, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean and `aw ipd coverage z2l43n` was ready before revision.

Re-measured at review:
- Children `x7unul`, `vfqjc0` and `gzb2rq` are all `to-review` in `pending/`. Their `Item-Dependencies` are `none`, then `executed:x7unul`, then `executed:vfqjc0`, which matches the table. All three carry `From-Backlog: eeiytw` and `Blocks-Release: next`. No child's `Scope-Paths` names a `.spec.md`.
- Plan `87m438` is in `executed/` (`- Status: executed`), not pending.
- Backlog `4uw9gy` is `done`. Open backlog `4izduy` (`Blocks-Release: next`) carries "aw index --agent emits bare human text instead of an aw.agent/v1 record on its write path".
- Backlog `eeiytw` is `- Status: open`. Its 2026-10-06 history says "re-run graduation to complete the handoff".
- `aw index all --json` still exits 1, which is consistent with the Deferred row.
- `gzb2rq` V-04 covers strict parseability, the human-surface removal, the manifest `Change`, the commit path-set, the two index verbs and the headline `plans` commands. The no-double-emit count for `aw research mv` lives in `vfqjc0` V-05(a). Byte-equality composition is spread across `x7unul` V-02(d)/V-03(d), `vfqjc0` E-06(f) and `gzb2rq` V-01(b)/V-02(c). The doc-diff check is `vfqjc0` V-01(a).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Orchestrator ownership | Cross-IPD preamble "Each check below is performed by Order 03 `gzb2rq` ... as part of its V-04"; `gzb2rq` V-04 (a)-(g) | Several cross-IPD checks (research-mv single emit, byte-equality composition, doc diff, research commit path-set) are not in `gzb2rq` V-04, so the stated single owner is false and a reader could treat them as parent-owned work. | all Low | FIXED | Each bullet now names its real owning child V-item. |
| PR-002 | LOW | IN-SCOPE | C. Evidence currency | Cross-IPD bullet and gate say "pending plan `87m438` ... approved"; `87m438` is in `executed/` | The shared-file hazard was presented as concurrent, but the change is already on the base. | all Low | FIXED | Both mentions now record that `87m438` is executed and part of the base. |
| PR-003 | LOW | IN-SCOPE | G. Carrier accuracy | Deferred `index` row and OQ-02 cite "open item `4uw9gy`"; `4uw9gy` `Status: done`; `4izduy` open | The declined-carrier rationale relied on an item that is now closed. The real carrier for `index`'s payload defect is `4izduy`. | all Low | FIXED | `4izduy` is now cited as the carrier, and `4uw9gy` is marked done. |
| PR-004 | LOW | IN-SCOPE | G. Lifecycle / provenance | Goal: "closed by the runner's normal backlog close"; `eeiytw` `Status: open` | The plan did not record that the coverage demotion reopened `eeiytw`. | all Low | FIXED | Added a state note that re-graduation is a backlog-tier act outside this Set. |
| PR-005 | LOW | UNDER-SCOPE | G. Execution contract | Approval gate | The scope-fence declaration wording was missing. | all Low | FIXED | Added. |

### Coverage repair log (`IPD-S408`)
- Attempt 1: after the PR-001 edits, `aw ipd coverage --no-commit z2l43n` reported `coverage-fail`: "uncovered obligation: Confirm no `.spec.md` file is in any child's `- Scope-Paths:`". Change made: the spec bullet was restated as a re-measured authored fact enforced by the finalize scope gate, with the doc check owned by `vfqjc0` V-01(a).
- Attempt 2: `aw ipd coverage --no-commit z2l43n` reported "Orchestrator z2l43n is ready for review." `review-finalize` was clean.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep V-02(b)/V-03(b)'s live re-derivations on the parent? | Keep | Replace with quotations of child evidence | Both are duplicated by child checks (`vfqjc0` E-06(a)/(e), `gzb2rq` V-04(e)), so no work exists only on the parent; under a hand execution they are a cheap independent re-check, and under runner retirement nothing is lost | yes |
| D-2 | Is the `index`/`archive` exclusion still correctly carried? | Yes, via `4izduy` for `index`; `archive` declares no machine flag | File a new carrier | `4izduy` summary and `Blocks-Release: next`; plan OQ-02 | yes |
