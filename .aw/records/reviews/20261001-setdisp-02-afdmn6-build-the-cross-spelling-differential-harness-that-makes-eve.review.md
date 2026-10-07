# Review: Build the cross-spelling differential harness that makes every later dispatch move attributable

- Subject-Id: afdmn6
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `8b7640a7b` in review lane `review-sweep-run-20261007T165410Z-456709`. Target plan
committed and byte-identical to the lane input; pre-review snapshot skipped. `aw ipd lint --phase author`
clean. Dependency `c6f6sj` is executed. `tests/test_set_dispatch_parity.py` does not exist (correct; E-01
creates it), and no other pending plan declares it except the downstream children that flip it.

The design (tests only, normalize by shape, positive assertions instead of xfail, mutation probes) is
sound. I DROVE every E-04 candidate axis through `cli.main` in scratch git repositories rather than
reading the inventory, and three of the eight no longer held as written. Measured:

- (a) flag `--status implemented` without evidence -> rc 1, unchanged; positional -> rc 0, relocated. HOLDS.
- (b) `deferred --gate-kind bogus-kind`: flag rc 1; positional rc 0, writes `- Gate-Kind: bogus-kind`. HOLDS.
- (c) relocation under `--no-commit`, tracked item: BOTH spellings end ` D open/<f>` + `?? parked/<f>`.
  Traced: `apply_status_change` calls `artifact_core.git_mv` (alone yields `R  a -> b`, verified), then
  `status_set._offer_self_commit` runs `git reset --quiet HEAD -- <paths>`, unstaging the rename. STALE.
- (d) sidecar: flag writes `.aw/records/history.jsonl`; positional writes none. HOLDS.
- (e) setid selector over two items: flag moves one (rc 0), positional moves both (rc 0); ambiguous
  substring: both rc 2. Divergence exists but is NOT refuse-versus-act. WRONG AS WRITTEN.
- (f) `specs set sp0001 --status approved` -> rc 2 "cannot read sp0001". HOLDS.
- (g) `backlog.run_set` direct call with `work_kind="bogus"` -> rc 2, file unchanged. Backlog half HOLDS;
  shared-engine half left to E-04 (direct call, as planned).
- (h) `--message`/`--gate-ref` with an embedded newline: both rc 2, nothing written. STALE: `4gwgo3`
  (`a165cb65b`, after authoring HEAD `ec857565a`) added the refusal to the shared engine.

Also re-verified: `backlog._reattach_history` and `status_set.apply_status_change` now both stamp
`artifact_core.utc_history_date` (`5ivkdh`, `3c55295a3`), so E-01's "two clocks" rationale is historical;
the normalizer remains required by spec `wy9aru` S3.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / E. Verification | E-04 (c); `status_set._offer_self_commit` "`_gch._git(repo_root, ["reset", "--quiet", "HEAD", "--", *paths])`"; scratch-repo porcelain identical on both spellings | E-04 required asserting a divergence that does not exist; the executor would either write a failing test at base or bend the assertion. Children 04/05 also inherit a wrong premise that the shared engine already yields a single rename | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | (c) reclassified as an AGREEMENT axis in E-02, comment must name the reset as cause and state `wy9aru` AC-5 is met by neither spelling; F-08 added |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness | E-04 (h); `status_set.run_set_command` loop calling `_refuse_unsafe_descriptive("aw set", _flag, ...)`; commit `a165cb65b`; both spellings rc 2 | Stale divergence; same failure mode as PR-001 | All Low | FIXED | (h) moved to E-02 agreement |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness | E-04 (e); `backlog.run_set` "`src = res.paths[0]`"; setid run moved 1 vs 2; substring run rc 2 on both | The described divergence (refuse vs act) is wrong; the real one is one-versus-all on a setid | All Low | FIXED | (e) restated with both cases |
| PR-004 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | E-04 / V-04 / Proposed change 4 bar "all eight expected-difference tests"; three of eight already drifted between authoring (`ec857565a`, 2026-10-01) and review | A fixed count of live divergences is a drifting bar; the plan's own downstream (`7zb4ny` E-02 "eight-row table") keys on it | All Low | FIXED | E-04 now requires re-measuring and classifying all eight at execution; V-04 demands the per-axis table with deciding output |
| PR-005 | LOW | IN-SCOPE | G. Evidence | E-01 date rationale; `artifact_core.utc_history_date` now used by both writers | Rationale described a clock split that `5ivkdh` closed | All Low | FIXED | Rationale updated; normalizer kept on `wy9aru` S3 |
| PR-006 | LOW | IN-SCOPE | G. Evidence | Conventions bullet quoted addopts as `-m 'not slow'`; `pyproject.toml` `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"` | Stale quote | All Low | FIXED | Quote corrected |
| PR-007 | MEDIUM | UNDER-SCOPE | G. Execution contract | Gate had commit/honesty rules but no scope-fence declaration and no conditional lifecycle ownership | Executor has no rule on runner versus hand finalize | All Low | FIXED | Added declaration-only fence and runner-self-finalize / hand-`aw ipd finalize` split, no hand `git mv` |

### Cross-plan note (not this plan's to fix)

PR-001's root cause is a probable production defect outside this plan's scope: under `--no-commit` (or a
declined offer) `_offer_self_commit`'s reset unstages the `git mv` rename that `status_set` documents as the
fix for the 2026-09-13 half-committed-relocation incident. That affects spec `wy9aru` AC-5 and children
`m94eht` / `vhiqo6`, which assume the shared engine already satisfies it. Reported to the maintainer
rather than filed by this review (a review edits plans only).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001: assert the stale (c) divergence anyway, drop it, or reclassify? | Reclassify as agreement, with a comment naming the cause and AC-5 gap | Keep as divergence (false at base); delete the axis (loses the AC-5 signal) | Scratch-repo porcelain on both spellings; plan's own E-03 rule "asserting agreement ... that fails at base would be a false regression signal" | yes |
| D-2 | Fix children 04/05/06 for the reclassified axes now? | No; cross-reference here and report | Edit them in this review | plan-review Step 0.1 ledger and Step 2.4 "fix it in the owning plan and cross-reference"; each is `to-review` and gets its own review | yes |
