# Review: Strike the dangling NoRunnerImportTests citations

- Subject-Id: 9vtas9
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The plan was committed and unchanged, so I skipped the pre-review snapshot. `aw ipd lint --phase author` was clean before my edits, and `--phase review-finalize` was clean after them. At pre-transition, the only findings are the expected not-executed S404 noise.

Re-measured at lane HEAD `916664e94`:

- The invariant holds. No import statement names `runipd`, and a fresh interpreter prints `[]`.
- No `class NoRunnerImport` exists in `tests/`.
- `grep -c NoRunnerImportTests agent_workflows/runner_shared.py` returns `6`.
- `oc_runipd` and `agy_runipd` each have `0` citations.
- `09622d3ed` (not an ancestor of authoring HEAD `b87641ff2`) removed the `closure_target_admission` block.
- The module docstring regex `asserts\s+the\s+absence\s+by\s+AST` matches, but a single-line grep returns nothing.
- `SUITE_FAILURE_LINE_LIMIT` is defined in `runner_shared` (re-homed by `12adf6883`).
- No test references either cap constant.
- `ery0ia` has executed and `x3zno3` is approved.
- Backlog `xvp5vx` is done. The live owners are `046nys` (the first-party-import family) and `3tov52` (the dangling test-symbol citations).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Validation feasibility (E) | agent_workflows/runner_shared.py module docstring: "asserts the" / "absence by AST" split across two lines | E-03 and V-03 use `grep -n 'asserts the absence by AST'` returning nothing as the success bar. That grep returns nothing before the edit too, so the check can never fail. It would also have made E-01(e) report the headwater claim as absent, which leaves E-03 with nothing to do. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced the grep with a newline-tolerant `re.search` over `__doc__`. Measured `True` now; the target is `False`. |
| PR-002 | MEDIUM | IN-SCOPE | Evidence currency | `git log b87641ff2..HEAD -S NoRunnerImportTests` shows `09622d3ed`; count is `6` | One of the seven sites, `closure_target_admission` (E-04(b), together with the F-07 second-guard clause), was already removed upstream. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-11. E-04(b) and V-04(b) now accept "no subject". The gate now says an absent block is not a stop condition. |
| PR-003 | MEDIUM | IN-SCOPE | Correctness of replacement prose | `runner_shared.SUITE_FAILURE_LINE_LIMIT: int = 40`; `grep -rn 'SUITE_FAILURE_(LIST_CAP\|LINE_LIMIT)' tests/ --include=*.py` returns nothing | E-05(a) left the pin-test question to the executor. I measured both points: no pin test exists, and the "driver" constant now lives in this same module, so the comment's import-rule rationale is obsolete. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05(a) now gives the measured target wording. It forbids collapsing the constants here, and says to file a backlog item if collapsing is wanted. |
| PR-004 | MEDIUM | IN-SCOPE | Carrier validity | `xvp5vx` in `backlog/done/`; `046nys` and `3tov52` open; `x3zno3` approved | Three Deferred rows name `xvp5vx`, which is done. The `should_color` row names `pn7rw3` instead of `x3zno3`, the plan that actually owns that subject. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Repointed those rows to `046nys`, `3tov52`, `3tov52` and `x3zno3`, with a note on each. |
| PR-005 | LOW | IN-SCOPE | Plan hygiene | OQ-01 `Owner: none`; gate Readiness sentence | The resolved OQ has no owner. The gate text claims that no Readiness field exists, which is no longer true after this review. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set the owner to `plan author` and corrected the sentence. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the `SUITE_FAILURE_LIST_CAP` comment be corrected? | Say it mirrors this module's `SUITE_FAILURE_LINE_LIMIT`, that equality is maintained by hand, and that the import rationale is obsolete | Keep the pin claim (false); collapse the constants (an executable change, refused by V-05) | measurements above | yes |
| D-2 | Which items carry the residues formerly assigned to `xvp5vx`? | `046nys`, `3tov52` | Leave `xvp5vx` (done, so the obligation reads as already discharged) | `oyh28b` E-07 filed these items; backlog headers | yes |
| D-3 | Should the plan be rewritten wholesale from "seven" to "six"? | No; F-11 records the correction and the specific bars were adjusted | Rewrite 27 mentions | Keeps the authoring history readable, and E-01 already treats counts as re-derived | yes |
