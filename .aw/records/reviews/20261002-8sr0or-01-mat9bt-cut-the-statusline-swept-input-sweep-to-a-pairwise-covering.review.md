# Review findings: plan mat9bt

- Subject-Id: mat9bt
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `6ba6cda19` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review, and `--phase review-finalize` was clean after revision.

Re-verified (stdin probes, no file written, no production or test edit):
- `tests/test_statusline_behavior.py` `TestStatuslineBoxInvariants.test_box_renderer_invariants_across_swept_inputs`
  uses `itertools.product` over nine domains, asserts `len(combos) == 7776` and `render_count == 31104`; value lists match F-04 sizes.
- `conftest._test_timeout_seconds`: marker, then `AW_TEST_TIMEOUT`, then `_DEFAULT_TEST_TIMEOUT = 90.0`; no `slow` lookup.
- `@pytest.mark.timeout(500)` in `tests/test_exit_contract_conformance.py`, two `timeout(300)` in `tests/test_json_surface_leak_posture.py`.
- `.github/workflows/tests.yml` slow step: `python -m pytest tests/ -n auto -m slow` (parallel).
- Naive greedy covering array: `naive: covering array did not converge (naive greedy)`; seeded-from-uncovered-pair: `seeded rows 19 1.1ms det True`.
- Zero-width setid now rectangular: `'a\u200bb' [117, 117, 117, 117]`; `it6tpj` and `mzrr7x` are both `executed`; ASCII mode `ascii pure: True`.
- Backlog: `8sr0or` graduated to `mat9bt`; `mu4k1g` graduated to `6ye76g`; `cqgr7f` open.
- Sibling plan `6ye76g` (reviewed, go-pending-approval) scope `conftest.py, tests/test_hang_guard_budget.py`; marker floors wall at `n`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Evidence | plan E-02 / V-02 cite "F-06" for the non-convergence result; F-06 records the 3-way miss | Dangling cross-reference: the non-convergence finding the generator design rests on had no Findings row. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-15 with the review probe output; E-02/V-02 repointed; E-02 now requires an explicit non-convergence raise. |
| PR-002 | MEDIUM | IN-SCOPE | G. Live-artifact criterion | E-02 / OQ-02 / gate quote "18 rows"; review probe produced 19 with a different tie-break | Row count is tie-break dependent and was phrased as a fixed fact. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 states the count is an output, not a bar; "about 18" in OQ-02 and gate. |
| PR-003 | HIGH | IN-SCOPE | D. Anti-regression | `.github/workflows/tests.yml` `python -m pytest tests/ -n auto -m slow`; E-05 "citing the measured serial duration" | E-05 sized the slow arm's timeout from serial duration, but the slow arm runs in parallel beside subprocess-heavy tests, where the same work measured 68.16s. A serial-sized budget would reproduce this very defect in the slow arm. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 sizes against the contended in-suite figure with at least 3x headroom (about 200s; 300 matches convention); V-05 requires a parallel-context duration and ratio. |
| PR-004 | MEDIUM | IN-SCOPE | C. Architecture (no duplicate paths) | Current test body is ~200 lines of four invariants; E-04 and E-05 each require "the identical four invariants" | Nothing prevented two copy-pasted invariant blocks that could drift, making the slow arm test something different. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04/E-05 require one module-level domain definition and one per-row invariant helper shared by both arms; V-04 confirms. |
| PR-005 | MEDIUM | IN-SCOPE | E. Evidence (stale premise) | `.aw/records/plans/executed/...it6tpj...` `- Status: executed`; probe `'a\u200bb' [117, 117, 117, 117]`; `...mzrr7x...` executed | Plan called `it6tpj` "approved" and said zero-width breaks the box "today" and ASCII purity "fails today"; both are fixed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Step 0 convention, Deferred bullet and V-04 rewritten: value lists stay unchanged as a no-domain-change rule, not for a live defect; V-04 requires `git diff` showing domains byte-identical. |
| PR-006 | MEDIUM | IN-SCOPE | G. Live-artifact criterion | E-01/V-01 "fallen far below F-01's 68.16s"; Required tests and POST-GATE reconcile against F-12 counts | Load-dependent in-suite duration (sibling measured 59-66s, isolated 15-30s) and an authoring-time suite count were used as bars. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01/V-01 re-derive baseline failing nodeid set and isolated duration; stop condition is structural (product gone, or isolated < 5s); reconciliation uses the E-01 set with isolated-rerun attribution. |
| PR-007 | MEDIUM | IN-SCOPE | G. Execution contract | POST-GATE "Run `aw ipd begin` before implementing and `aw ipd finalize` after every `V-*`" | Unconditional finalize instruction; under `aw oc run` the runner owns the transition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten with conditional runner/executor ownership; no hand `git mv`. |
| PR-008 | LOW | IN-SCOPE | G. Scope-fence wording | Gate and Deferred bullet "STOP AND REPORT rather than widening scope" for a discovered renderer defect | Stop directive for the out-of-scope case contradicts the 2026-09-01 scope-fence ruling. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with file via `aw backlog new`; justify any out-of-scope edit with `--scope-reason`; scratch-harness cleanup added. E-01 premise-refuted stop retained (genuine unsafe condition). |
| PR-009 | LOW | UNDER-SCOPE | C. Architecture / coordination | F-11 says all three items `open`; sibling plan `6ye76g` unmentioned; E-06 3-way triple taken from authoring | Stale backlog states and an unreferenced complementary plan on the same symptom; also the F-06 trigger triple might be covered by a differently tie-broken array. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-11 corrected; F-16 added reconciling `6ye76g` (non-overlapping, marker floors wall); E-06/V-06 require the 3-way triple be chosen from actual rows, with the counting argument (27 triples > rows) and an absence line. OQ owners set to plan author. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What should the slow arm's timeout be sized against? | Contended in-suite duration, >= 3x headroom (~200s; 300 by convention) | Serial duration (reproduces the defect under `-n auto`); `timeout(0)` (disables hang protection) | `.github/workflows/tests.yml` slow step uses `-n auto`; F-01 68.16s in-suite | yes |
| D-2 | What is the E-01 stop condition once the in-suite figure is known to be load-dependent? | Structural: product no longer swept, or isolated serial < 5s | Keep "far below 68.16s" (unmeasurable, load-dependent) | F-10 isolated 14-15s; `6ye76g` F-02 29.53s isolated / 66.53s in-suite | yes |
| D-3 | Keep the zero-width/newline-free value lists now that `it6tpj` fixed the defect? | Keep unchanged; domain changes are out of scope for an enumeration change | Add zero-width values to the sweep (coverage change, already owned by `TestStatuslineHostileInputs`) | probe `'a\u200bb' [117, 117, 117, 117]`; `it6tpj` executed | yes |
| D-4 | Shared helper or duplicated assertions for the two arms? | Shared domain definition and invariant helper | Duplicate the ~150-line body in each arm | Rubric C (no duplicate paths); current test body | yes |
