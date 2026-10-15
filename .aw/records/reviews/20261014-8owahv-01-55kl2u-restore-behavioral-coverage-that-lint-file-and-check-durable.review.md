# Review: Restore behavioral coverage that lint_file and check_durable_carrier share the evaluate_durable_carrier predicate

- Subject-Id: 55kl2u
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `68f4b465b`, clean tree, target plan committed unchanged (snapshot skipped).
`aw ipd lint --phase author` conforming before revisions; `--phase review-finalize` conforming after.

Verified TRUE: `check_engine.evaluate_durable_carrier` docstring still says "no live guard currently
asserts this"; `check_engine.check_durable_carrier` calls the module-global evaluator;
`ipd_lint._merge_durable_carrier` imports `check_engine as _ce` at call time and is gated by
`_CARRIER_CHECKPOINTS = frozenset(("pre-transition",))`; `ipd_schema.CHECKPOINTS` has five members;
`tests/support.py` `declare_execution_role` exists. A one-off probe (deleted afterwards) rebuilt the
deleted module's `_mkrepo`/`_plan` fixtures from `19313eed7^`: with a sentinel patched in, `lint_file`
and `check_durable_carrier` both yield `["SENTINEL"]`; unpatched, both yield one `error` finding; under a
`wraps=` spy, `lint_text`/`check_checkpoint` make 0 calls at every checkpoint, and `lint_file` makes 1 at
`pre-transition` and 0 elsewhere.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A. Correctness (false premise) | Probe at `68f4b465b`: `lint_file(plan, checkpoint="pre-transition")` on the historical `_plan` fixture also reports `IPD-M101` (Concern, Scope, Author), `IPD-M104`, `IPD-M110`, `IPD-M111`, `IPD-M113` | E-01 claimed the `performed`/`pass` fixture "isolates this rule" at pre-transition; it no longer does, since the metadata schema has grown. An executor asserting disposition or the full diagnostic list would write a failing or misleading test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now records the measured extra diagnostics and requires every assertion to filter by `code == "check.ipd-uncarried-obligation"`; also pins the cutover source (no `project.json`, so the `CARRIER_CUTOVER_DATE` constant applies). |
| PR-002 | MEDIUM | UNDER-SCOPE | D. Anti-regression (one-sided mutation) | Plan Required tests and V-01 mutate only `check_durable_carrier` | The non-vacuity check exercised only the sweep consumer; the lint consumer (`_merge_durable_carrier`) was never shown to be load-bearing for either test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Mutation check extended to `_merge_durable_carrier` returning `result` unchanged; V-01 and V-02 require pasted FAIL output and a revert diff over both files; gate states the scratch edits must be reverted and why `ipd_lint.py` stays out of Scope-Paths. |
| PR-003 | MEDIUM | UNDER-SCOPE | G. Executability (execution contract) | Plan's original Approval gate | No scope-fence declaration, no paste-actual-output rule, no `--no-verify`/staged-set guidance, and an executor-owned move to `executed/` with no runner/executor split; the plan file was not in Scope-Paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | EXECUTION CONTRACT and POST-GATE LIFECYCLE MOVE paragraphs added; plan file added to Scope-Paths. |
| PR-004 | LOW | IN-SCOPE | E. Testing (P16 proof is noisy) | V-01 `grep -nE "inspect\|..."` | An unbounded `inspect` alternative matches ordinary prose in docstrings (the deleted module's own docstrings used "inspect"-free prose only by luck), so "no match" may be unattainable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Pattern anchored to import statements and `getsource(`. |
| PR-005 | LOW | IN-SCOPE | G. Live-artifact criteria convention | V-01/V-02 barred on test function names; OQ-01 `Owner: none` | Test names are pointers, not bars; a resolved question had no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01/V-02 demand the pinned behavior; OQ-01 owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Add `ipd_lint.py` to Scope-Paths since V-01 now mutates it? | No; scratch-only edit reverted before commit, stated in the gate. | Add it: rejected, would declare an intended committed change that does not exist and weaken the finalize scope reconciliation. | `aw ipd finalize` `--scope-ack` semantics (declared-but-unmodified paths need acknowledgement) | yes |
| D-2 | Keep OQ-01 (new module rather than append)? | Keep. | Append to `tests/test_carrier_detail_descriptive_bound.py`: rejected, its scope is the Section 8.8 descriptive bound. | Plan OQ-01; sibling `yfo6z6` precedent | yes |
