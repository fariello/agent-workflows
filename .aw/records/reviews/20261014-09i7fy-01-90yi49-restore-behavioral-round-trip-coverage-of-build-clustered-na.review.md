# Review findings: plan 90yi49

- Subject-Id: 90yi49
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `3016e07c7` in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified by calling the real functions:
- Build then parse holds for `None` plus all 10 `ARTIFACT_TYPE_FACETS`.
- The four corpus names rebuild byte for byte.
- `artifact_type="ipdd"` raises `ValueError`, and `parse_clustered("...ipdd.md")` returns `None`.
- `rg -n build_clustered_name tests/` is empty, which confirms F-01.
- `RoundTripTests` is present at both `80db6750c^` and `19313eed7^`, so `19313eed` is the correct deletion commit.
- An in-process probe (no source edit) showed:
  - A `{order:03d}` builder mutant fails a build test.
  - A greedy-`set` regex mutant fails a group-pinning test.
  - Under that greedy mutant, the lazy-quantifier name still round-trips byte for byte.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | D. Anti-regression | `artifact_naming._CLUSTERED_RE` lazy `set` group; `_CLUSTERED_PREFIX_RE` comment "THE LAZY QUANTIFIER IS LOAD-BEARING"; review probe | The E-02 lazy-quantifier corpus entry claimed to guard the quantifier, but `build(parse(n)) == n` still holds under a greedy regex (set `foo-12-abc123-bar`, order `01`). The identity check alone does not catch the regression that entry was added to catch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now asserts `set == "foo"`, `nn == "12"` and `slug == "bar-01-def456-slug"`. Added F-04. V-02 demands a greedy-mutant probe that fails. |
| PR-002 | MEDIUM | IN-SCOPE | E. Verification / safety | Required tests "temporarily changing the builder's `{order:02d}`"; V-01 | The falsifiability step told the executor to edit production source "in a scratch copy" and revert, which is ambiguous and risks committing a mutated `artifact_naming.py`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with an in-process mutant probe through module attributes (E-01 now requires module-attribute calls). V-01 demands `git diff --stat` showing no executable change. Demonstrated at review. |
| PR-003 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | Required tests "Full bare suite `python3 -m pytest` passes"; V-04 "`N passed` summary" | A fully green bare suite was the bar, so another party's failure would block a correct execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Changed to "no failure that does not also fail on the base commit", compared by test id. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the OQ status, the paste-output honesty rule, `aw ipd begin`, staged-set verification, a scope fence and runner-conditional finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all of those elements. |
| PR-005 | LOW | IN-SCOPE | Plan-review 3.1(5) | OQ-01 `- Owner: none` | A resolved question listed no owner. The linter accepts this because owner is only checked for deferred questions, but the workflow requires naming who decided. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owner set to the plan author, confirmed by review. Also added F-05 (the deletion commit is verified) and widened the no-source-reading grep to `open\(`. |
| PR-006 | MEDIUM | IN-SCOPE | G. Lifecycle gate | `check.ipd-uncarried-obligation` on this plan at base; `.aw/records/plans/README.md` "Durable carrier vocabulary" | The three Deferred rows carried no `Carrier`, `Carrier-Evidence` or `Carrier-Declined`, so `aw check` warned and the plan would fail its own pre-transition gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each row now has `- Carrier-Declined:` with its reason: all three are deliberate exclusions, not outstanding work. The warning is cleared. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should falsifiability be proven? | In-process mutant substitution through module attributes | Edit-and-revert production source (risk of committing a mutant); drop falsifiability (weaker V-01) | review probe output: real 0 failures, mutant-a and mutant-b each fail | yes |
| D-2 | Pin the lazy-quantifier groups beyond identity? | Yes | Identity only (shown blind to a greedy regex) | review probe F-04 | yes |
| D-3 | Carry or decline the three Deferred rows? | `Carrier-Declined` on each | File backlog items for exclusions nobody asked for (manufactures work) | backlog `09i7fy` names only the round trip; P16 | yes |
