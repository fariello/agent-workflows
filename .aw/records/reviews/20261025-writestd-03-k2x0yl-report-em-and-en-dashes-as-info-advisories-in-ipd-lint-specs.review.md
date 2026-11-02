# Review findings: plan k2x0yl

- Subject-Id: k2x0yl
- Subject-Type: ipd
- Reviewed-At: 2026-11-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `f70329c47` in a runner review-sweep lane worktree (non-interactive). The lane-input
copy (revision 4) is byte-identical to the tracked plan (committed, unmodified), so no pre-review
snapshot. `aw ipd lint --phase author` clean before revisions; `--phase review-finalize` clean after
(an intermediate `IPD-Z602` density advisory on E-04 was resolved by splitting out E-07).

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Scope | Validators emit the rules | Separate advisory functions called only by the check commands | Meaning correction from PR-001. |
| E-01 | "front-matter block" | YAML front matter and the metadata block before the first `## ` heading | Names the boundary `specs._metadata_end` uses. |
| E-05 | Section 10 item 17 only | Item 17 and the Section 16 acceptance bullet | The acceptance bullet states the same retired rule. |
| Gate | Partial execution contract | Full contract | S7 rule. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes: adds rule ids to `check_engine.RULE_REGISTRY`, changes `aw specs check`/`aw backlog check` agent output severity, amends an implemented spec.
2. No.
3. Moderately: 7 E-items across five modules, but one concern.
4. Yes: nine Scope-Paths including one `.spec.md`.
5. Yes before revision: emitting drift from `validate_spec`/`validate_item` would break `aw specs set` and other callers.

Tier: standard.

### Step R1

- Checked: spec `ecmw83` R-07, AC-05, AC-06; `ipd_lint` comments at `C_CITATION_ANCHOR` and "IPD-D701 (em/en dash in authored prose) was RETIRED"; `ipd_lint._structural_lines`, `ipd_lint.lint_text` (terminal-directory `DISPOSITION_LEGACY` short-circuit), `ipd_lint.check_citation_anchors`, `ipd_lint.CITATION_ANCHOR_CUTOVER_DATE`; `specs.validate_spec`, `specs._metadata_end`, `specs.run_check`; `backlog.validate_item`, `backlog.run_check`; `check_engine.RuleSpec`, `RULE_REGISTRY`, `rule_spec`, `enrich_drift`, `check_content`, `_iter_type_files`, `_RETIRED_STATUSES`; `artifact_core.Drift`, `drift_exit_code`; `tests/test_ipd_lint.py` `StructuralRuleTests` and `test_every_structural_rule_fires_on_its_own_violation`; spec `ipd-structure-and-linting` Section 10 item 17 and Section 16 bullet; `docs/cli-output-contract.md` Section 3; Orders 07 to 09 (`sfez3e`, `uog8nc`, `381ml6`) E-02 usage of the advisories.
- Callers of the validators that refuse on any drift: `status_set` (two sites, `residual = _specs_mod.validate_spec(...)`), `specs` migrate (`residual = validate_spec(path, new_text)`), `set_records` promote (`drift = _backlog.validate_item(dest, rendered)`), `attention._spec_record` (feeds `drift_exit_code`), `runner_shared` (two sites).
- Probe: `aw ipd lint --agent` on a pending fixture with only an `IPD-C801` advisory printed `"outcome":"clean","exit":0` with `info:1`.
- Probe: `Drift('x','spec.prose-dash','y')` has severity `''` and `drift_exit_code` returns 1; with `severity='info'` returns 0; `rule_spec('spec.prose-dash')` defaults to `error`.
- Measured dash population: live specs 1 file (`4sd62s`), live backlog 0, pending/reusable plans 0; executed plans 375 (already silent via `DISPOSITION_LEGACY`).

### Step R2

- Checked: E/V bijection (7/7 after split), Scope-Paths (added `tests/fixtures/review-pilot/`), Item-Dependencies none (correct: no Set prerequisite), V reachability (V-02 and V-03 observations produced by `ipd_lint` lint command `OutDiag` loop and the two `run_check` functions), spec trace (`ecmw83` R-07, AC-05 now qualified).

### Step R3

- Checked: no trust-boundary input, no secrets; a read-only text scanner. Not applicable beyond that.

### Step R4

- Checked: C reuses the advisory channel (`LintResult.advisories`) and registry; D invariant "the advisory never changes a disposition or exit status" maps to E-04 rows (b) and (c) and V-06's `findings_by_severity` comparison; E adds the canonical no-error-added proof shape and the `make test-all` run; F smallest design. Right-sizing: E-04 split into E-04 and E-07. Spec sync section corrected.

### Step S5

- Checked: no pre-existing open questions. One reviewer decision recorded (D-1, reversible). No human-only question.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | blocker | IN-SCOPE | A correctness / D invariant | `status_set` "residual = _specs_mod.validate_spec(prep.dest_path, prep.updated_text)"; `set_records` "drift = _backlog.validate_item(dest, rendered)"; `specs` "residual = validate_spec(path, new_text)" | E-03 put the advisory inside `validate_spec`/`validate_item`, whose callers refuse on any returned drift. `aw specs set` on `4sd62s` (holds a dash) would refuse, violating R-07 "never change a disposition or an exit status". | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-03 adds separate `prose_dash_advisories` functions called only by the two `run_check` commands and `check_engine.check_content`; E-04 (a) and (c) test it. |
| PR-002 | high | IN-SCOPE | A correctness | `artifact_core.drift_exit_code`; `check_engine.rule_spec` default; `specs.run_check` "severity=\"error\"" | Un-enriched Drift has empty severity (fails the gate) and both check commands hard-code `error`, so "exit 0" in E-03 was unreachable as written. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Drift sets `severity="info"`; both `run_check` agent branches use `d.severity or "error"`. |
| PR-003 | high | IN-SCOPE | R7 cross-plan | `sfez3e` E-02 "the Order 03 advisory `spec.prose-dash` lists them"; `ecmw83` AC-06 | The authoring-date cutover would hide every pre-existing artifact, which is the population Orders 07 to 09 use the advisory to find. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Cutover removed (D-1); terminal plans stay silent through the existing `DISPOSITION_LEGACY` path. |
| PR-004 | medium | IN-SCOPE | C architecture | `ipd_lint` imports `ipd_schema` which imports `backlog` | Reusing `ipd_lint._structural_lines` from `specs`/`backlog` risks an import cycle and couples modules. | Low | fixed | `prose_dash` imports no first-party module; V-01 proves it. |
| PR-005 | medium | UNDER-SCOPE | E testing | spec `ipd-structure-and-linting` Section 16 bullet; `tests/test_review_pilot.py` | Missing: canonical no-error-added proof, executed-plan silence, set-command non-refusal, review-pilot fixtures, `make test-all`. | Low | fixed | E-04 rows (a) to (d), E-07, E-06 `make test-all` and `aw check all` comparison. |
| PR-006 | medium | IN-SCOPE | Spec sync | spec Section 16 "the retired no-em/en-dash rule is NOT enforced" | E-05 amended item 17 only, leaving the acceptance bullet contradicting it. | Low | fixed | E-05 amends both. |
| PR-007 | low | IN-SCOPE | R4 right-sizing | `IPD-Z602` on E-04 | E-04 bundled the new test file with the existing row and fixtures. | Low | fixed | Split into E-04 and E-07 with V-07. |
| PR-008 | low | UNDER-SCOPE | G execution contract / spec trace | plan gate; `production_checks._compute_spec_trace_coverage` | Gate lacked the full contract; no qualified `ecmw83` AC id in V-items. | Low | fixed | Gate rewritten; AC-05 qualified in V-01 to V-04. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Gate the advisory on an authoring-date cutover? | No cutover; terminal artifacts stay silent through existing paths | Cutover at execution date (original E-02); cutover plus an on-demand flag | `sfez3e`/`uog8nc` E-02 rely on the advisory; `ecmw83` AC-06; measured only 1 live dash-bearing file; `ipd_lint.lint_text` returns `DISPOSITION_LEGACY` for terminal directories; `check_engine._iter_type_files` skips retired | yes |
| D-2 | Where do spec and backlog advisories live? | Separate functions, not the validators | Inside validators with every caller filtered by severity | Seven refusing callers (Step R1); fewer edits and no caller changes | yes |
| D-3 | Review tier | standard | complex | Step T | yes |
