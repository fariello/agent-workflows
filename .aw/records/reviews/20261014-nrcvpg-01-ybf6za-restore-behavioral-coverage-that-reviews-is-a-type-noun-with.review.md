# Review findings: plan ybf6za

- Subject-Id: ybf6za
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review lane. The plan was already committed and unchanged at `1781d0205`, so no pre-review snapshot was needed. `aw ipd lint --phase author` reported conforming before and after the revisions. Before the revisions, `--phase pre-transition` reported `check.ipd-uncarried-obligation` on all three Deferred rows.

Claims I verified at HEAD:
- Commit `19313eed` exists, and `ev7t1w` is in `executed/`.
- The `artifact_types.py` docstring carries "(`tests/test_awcmdsurf_vocab_and_parsers.py` was deleted in `19313eed`; no live guard currently asserts this)".
- `tests/test_reviews_type_noun_surface.py` does not exist yet.

I prototyped E-01..E-03 as a pytest module under the gitignored `.aw/state/` (removed afterwards). Results:
- `rename`/`group`/`index reviews` each returned 2 with `'<verb>' is not supported for reviews.`, and the file was unchanged.
- The routed-verb union was `{new, index, find, rename, group, archive, check}`, with `reviews` absent from all of them.
- `find reviews ab12cd` returned 0 and listed the path.
- `describe_unresolved_plan_selector` on the review stem returned the generic message. The spec control returned "is a spec (...), not an IPD plan."
- `selectors.resolve` matched under `reviews`, not under `other`.
- All 6 tests passed.

Non-vacuity, all in-process:
- With `mock.patch.dict(TYPE_BACKENDS, {"reviews": {"rename": ...}})`, the `rename` refusal text vanished. Output was `other verb cannot act on ...`.
- With `KNOWN_PRIMARY_TYPES | {"reviews"}`, the review message became "is a reviews record (...), not an IPD plan."

Unknown-noun contrast: `rename nosuchtype` returned 2 with `unknown artifact type 'nosuchtype'`.

`aw set approved <review> --no-commit` returned 0 and REWROTE the review, adding `- Status: approved` and a history line.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G. Lifecycle gate | `aw ipd lint --phase pre-transition`: `check.ipd-uncarried-obligation: 3 obligation(s) ... deferred row 1, deferred row 2, deferred row 3` | The plan could not pass its own pre-transition gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Row 1 now has `Carrier: 9pu7sf` with evidence. Rows 2 and 3 now have a reasoned `Carrier-Declined`. Lint is clean. |
| PR-002 | MEDIUM | IN-SCOPE | D. Honest documentation | `agent_workflows/artifact_types.py` docstring: reviews "stays out of ... `aw set`"; measured: `aw set approved <review>` exits 0 and writes `- Status: approved` into the review | E-04 would have put a live-guard pointer next to a claim that is false today. F-05 was also understated: it covered only `--dry-run`, but the real run mutates the record. The plan left the defect unfiled. | all Low | FIXED | Filed backlog `9pu7sf` (bug, `Blocks-Release: next`). E-04/V-04 now rewrite the clause to point at `9pu7sf`. F-05 is corrected. |
| PR-003 | MEDIUM | IN-SCOPE | E. Non-vacuity method | old Required tests: "scratch, uncommitted edit ... to `artifact_types.TYPE_BACKENDS` ... revert", while E-04 edits the same file | A source sabotage of a file E-04 also edits risks the revert wiping E-04's change, or the sabotage getting committed. Also, only the `TYPE_BACKENDS` half had a non-vacuity proof. | all Low | FIXED | Both halves now carry in-module `mock.patch` non-vacuity tests (prototyped, both pass). The source-edit step is removed. |
| PR-004 | LOW | IN-SCOPE | E. Distinguishability | old E-02 asserted the two refusal modes differ only in prose | The "no backend" vs "unknown type" distinction was asserted, not observed. | all Low | FIXED | Added a `nosuchtype` contrast case with measured text. |
| PR-005 | LOW | UNDER-SCOPE | G. Execution contract | old gate: three sentences, no begin, scope fence, honesty rule, never-tag, or runner-owned finalize; plan file absent from Scope-Paths | Incomplete contract. | all Low | FIXED | Rewrote the gate in the repo's standard form and added the plan path to Scope-Paths. V-03 now also runs `tests/test_no_code_structure_pins.py`. OQ-01 Owner set to `plan author` (it was `none`). |

`aw ipd lint --phase review-finalize` reported conforming after the revisions.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the `aw set` mutation of a review be handled? | File backlog `9pu7sf` (bug, gated next) and carry it from Deferred | Fold the fix into this plan (production change outside `nrcvpg`); leave it unfiled (an uncarried obligation, and the defect would vanish) | Measured `aw set approved <review> --no-commit` rewrite; AGENTS.md "Every live bug gates the next release" | yes |
| D-2 | How should non-vacuity be proved? | In-process `mock.patch` tests committed in the module | A temporary source edit plus revert (collides with E-04) | Prototype: both patches flip the observed outcome | yes |
