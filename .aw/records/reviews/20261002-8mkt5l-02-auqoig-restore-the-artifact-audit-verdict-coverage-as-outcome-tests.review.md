# Review: Restore the artifact_audit verdict coverage as outcome tests after triage

- Subject-Id: auqoig
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before edits and `--phase review-finalize` was clean after.

Re-verified at lane HEAD `49844944f` by probe against today's `agent_workflows.artifact_audit`. All four F-06 shapes reproduce exactly: clean `F F F unchanged`, location-only `T F T regressed`, status-only `F T T unknown`, missing `True missing`. The deleted `superseded`-in-`executed/` case reads `True True` (F-02). The live and not-live `running`/`approved`-in-`pending/` cases are both `unchanged` with `is_live` mirrored. `expected_dir_for_status` maps the three retirement/standing dispositions to themselves and all six pre-terminal statuses to `pending`. `read_declared_status` gives `None` for the multi-word value and `executed` for the single token. `grep -rn read_declared_status tests/` still matches nothing. `git show 19313eed^:tests/test_artifact_audit.py` has the class at line 277 and is 1312 lines, against 529 at HEAD. `8sr0or` exists.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Testing / mutation validity (E) | plan E-06(d) "swap `CLASS_REGRESSED` and `CLASS_UNKNOWN`"; E-02 "Reference the class CONSTANTS" | The mutation was ambiguous. If an executor swaps the constant VALUES, tests that compare against the constants (which E-02 requires) stay green, so the proof shows nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06(d) now mutates the `classify_difference` plans-branch return (anchor "BACKWARDS: the run recorded a SUCCESS") from `CLASS_REGRESSED` to `CLASS_UNKNOWN`, and explicitly forbids the constant-value swap. |
| PR-002 | MEDIUM | IN-SCOPE | Live-artifact criteria (G) | plan E-07, V-07 "F-08's baseline of `1 failed, 4356 passed, 2 skipped`" | The bar was a suite count and failing set measured at authoring. Both are live and have since moved (the a8e2l8 plan measured `4530 passed` with 5 failures), so a correct execution would fail V-07. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 and V-07 now require a baseline re-derived before the change and reconciliation against that failing set. F-08 is kept as context only. |
| PR-003 | LOW | IN-SCOPE | Live-artifact criteria (G) | plan E-02 "four shape tests"; V-02 "passing by name" | The test count and names were the bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bar is now the behaviour plus a test-to-shape mapping, with names treated as pointers. |
| PR-004 | LOW | IN-SCOPE | Evidence durability | plan F-04 cites `.aw/state/scratch-1sn4h0/old_test_artifact_audit.py` (absent in this lane); E-01 "scratch path INSIDE this worktree" | F-04 cited an ephemeral scratch file that no longer exists. E-01 did not name a gitignored location, so it risked a tracked path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 now cites the git object. E-01 names the gitignored `tmp/`. |
| PR-005 | LOW | IN-SCOPE | Execution contract (G) | plan gate "`aw ipd set executed <plan>` / the runner's finalize"; OQ-01 `Owner: none` | The gate offered `aw ipd set executed`, which bypasses finalize's scope and receipt gates. OQ-01 was resolved by the author but named no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now requires `aw ipd finalize` with conditional runner/executor ownership. OQ-01 owner is `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which mutation proves the class assertions are load-bearing? | Change the return site in `classify_difference` | Swap the constant values (invisible to constant-referencing tests); swap the constant names (an import-level rename, not a behaviour change) | `agent_workflows/artifact_audit.py` `classify_difference` "BACKWARDS" branch; probe shows location-only reaches it with run status `executed` | yes |
