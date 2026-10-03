# Review findings: plan moegsl

- Subject-Id: moegsl
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `0f8de354f` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review; `--phase review-finalize` was clean after revision.

Re-verified (read-only):
- `docs/cli-agent-protocol.md` `## Token control`: "Two escape hatches tune the token cost:" then `--fields` and
  `--verbose` bullets; `--limit` appears in `## Stream truncation is honest` and the worked `find` summary example.
- `docs/cli-output-contract.md` `## 6. Token Control and Escape Hatches`: bullets `**Compact Defaults**` (no flag),
  `--fields`, `--limit`, `--verbose` / `--json`. A regex `- (?:\*\*)?`(--[a-z-]+)` per section yields
  `['--fields', '--verbose']` and `['--fields', '--limit', '--verbose']`.
- Backlog `4uw9gy` is now `graduated` (to plan `2zvxhx`, `reviewed`, `go-pending-approval`), whose E-06 amends
  contract Section 6's `--limit` bullet. Plan `okiso1` (`reviewed`) declares `docs/cli-agent-protocol.md` and defers the
  count to `9qya0k`. Plan `t9lcdu` touches neither declared path.
- `aw runs analyze --help`: `--limit LIMIT  Maximum records per agent stream page`; probe with zero runs emitted one
  `result` record with and without `--limit 1` (inconclusive). `aw research index --help`: hot-window size.
- Bare suite: `5 failed, 4636 passed, 2 skipped, 3 warnings in 376.84s`; a re-run named four FAILED nodes
  (`test_readiness_absence_invariant`, `test_spec_review_attestation`, `test_selector_type_containment`,
  `test_run_finding_reachability`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Unsatisfiable validation | plan Required tests "green before and green after"; V-03 "delta must equal ... (3)"; bare suite above | The suite is not green at base, and its failure count varies between runs, so both demands are unsatisfiable or flaky. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline is now a failing-node-id set; V-03 compares by node id and requires the three new tests not to fail. |
| PR-002 | MEDIUM | IN-SCOPE | G. Sequencing / shared checkout | E-03 `Depends on: E-02` vs "SHOW IT RED FIRST"; "stash or revert" | E-03 depended on E-02 yet must be red before it; `git stash` in a shared checkout sweeps a co-worker's work. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 depends on E-01 and is authored before E-02; `git stash` forbidden with a safe alternative; ORDER MATTERS paragraph reconciled. |
| PR-003 | MEDIUM | IN-SCOPE | A. Stale premise | `4uw9gy` at `graduated/`; plan `2zvxhx` E-06 amends contract Section 6 | Plan said `4uw9gy` is `open` and cited its `open/` path; it did not name `2zvxhx`, which changes both the reach E-01 measures and the contract text E-02 mirrors. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Status/path corrected in E-01, F-03, Deferred row; E-02 now mirrors the contract as it reads at execution and drops the pointer if `4uw9gy` is done. |
| PR-004 | MEDIUM | IN-SCOPE | E. Test design | contract Section 6 `**Compact Defaults**` bullet | E-03's cross-document set test as written would count the flagless Compact Defaults bullet as a hatch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 requires extracting only backticked-flag bullets and locating sections by heading text, with the measured extraction quoted. |
| PR-005 | LOW | IN-SCOPE | E. Measurement validity | `aw runs analyze --help` "Maximum records per agent stream page"; zero-run probe | An empty-tree probe of `runs analyze` cannot distinguish honored from ignored; the authoring classification of it as ignored is unproven. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 and V-01 require help text plus a probe, and record an empty probe as INCONCLUSIVE. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract | POST-GATE LIFECYCLE MOVE; SCOPE FENCE "COORDINATE WITH `okiso1`" | Lifecycle ownership was not conditional; the coordination wording implied a runtime hazard the runner's isolated worktrees already handle. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Conditional runner/executor ownership added; sibling survey rewritten as a facts-change note. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Write the `--limit` bullet now or wait for `2zvxhx`/`okiso1`? (OQ-01) | Now, re-derived at execution | Wait for siblings (keeps two shipped docs disagreeing) | Contract Section 6 already lists `--limit`; E-01 re-measures | yes |
| D-2 | Add `- Item-Dependencies:` on `2zvxhx`? | No | Depend on `2zvxhx` (would delay a low-priority doc fix behind a medium code plan) | E-01/E-02 require re-derivation, which absorbs either ordering | yes |
