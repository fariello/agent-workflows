# Review findings: plan pyuw4v

- Subject-Id: pyuw4v
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `dcdc79632` in an isolated review lane. The plan was committed and unchanged (lane input sha256 `81dac8e7...` matches the tracked file), so no snapshot was needed. `aw ipd lint --phase author --agent` reported `clean` with 7 advisory `IPD-C801` notes. All 7 are in F-02/F-03 or E-06, where the bare offset is itself the subject being measured (the line-as-subject case Section 10.2 exempts), so they need no fix. `--phase review-finalize` was clean after revisions.

Re-verified:
- `spec_citations._resolve_offset(lines, headings, in_fence, offset) -> Tuple[str, str]` with verdicts `past_eof`/`in_fence`/`blank_line`/`valid`, matching E-01/E-02. Pending `fz3i3m` declares `spec_citations.py` in its Scope-Paths, so E-01's adaptation clause is warranted.
- `cli._run_check` `--source-anchors` branch: `exit_code = 0`, `status = "clean" if len(findings) == 0 else "findings"` (the `g3ropl` pairing). `agent_schema.POSITIVE_OUTCOMES == ('clean', 'ok', 'conforms')`. `cli._build_check_continuation` has `is_source_anchors`. `check.spec-anchor-stale` is in `RULE_REGISTRY`. `aw check` accepts `--dir` and `--limit`.
- `--source-citations` and `--source-anchors` together run only the first (the `--source-citations` record), so the opt-in scan flags have first-match precedence.
- E-02 rules re-implemented as a throwaway probe over `agent_workflows`, `tools`, `tests`: "resolved 37 unres 3 7", wall time 2.15s. The 7 sites: `agy_runipd.py` x3 past_eof (`oc_runipd.py:8766`, `:8645`, `:8834`), `runner_shared.py` x2 blank_line (`ipd_lifecycle.py:3989`, `cli.py:8487-8512`), `selectors.py` punct_only (`status_set.py:132-133`), and `tests/test_runner_shared.py` blank_line (`agy_runipd.py:2190`). The `tests/test_oc_runipd.py` `oc_runipd.py:4823` site is no longer defective at HEAD.
- `artifact_core.is_ignored_path` with `get_ignored_dirs` ignores `.aw/worktrees/` (probe: a copied `oc_runipd.py` under `.aw/worktrees/zzprobe/` returned `True`; the probe was removed afterwards). So runner lanes do not create duplicate basenames in the E-02 target index. Every basename the live sites cite is unique.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Testing / environment | AGENTS.md "aw: invoked in checkout ... re-running with"; repo test posture (`AW_NO_REEXEC=1`, isolated `HOME`) | E-06 (k) runs `aw check` as a subprocess without saying which package it imports. A bare `aw` on PATH may import the installed checkout rather than the one under test, so (k) could pass or fail against code this plan did not change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | (k) now specifies `sys.executable -m agent_workflows`, `PYTHONPATH` at the checkout, `AW_NO_REEXEC=1`, and `HOME`/`XDG_CONFIG_HOME` in `tmp_path`. |
| PR-002 | LOW | IN-SCOPE | F. UX / prevent silent failure | `aw check --source-anchors --source-citations --agent` -> only the `source-citations` record | Where the new branch sits decides what a combined invocation does, and E-04 did not say. A combined flag set silently runs only one scan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now places the branch after `--source-anchors` (existing precedence unchanged) and states the precedence in the help text. |
| PR-003 | LOW | IN-SCOPE | G. Live-artifact criteria | review probe "resolved 37 unres 3 7" vs F-02 "8" | The live census already drifted from 8 to 7 between authoring and review. F-02 needed to say that the count is context and not the bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the review re-measurement and the re-derivation note to F-02. V-02 already explains differences by commits since authoring. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract / decision recording | gate `EXECUTION CONTRACT`; OQ-01..OQ-04 `- Owner: none` | The gate lacked the resolved-OQ statement, the staged-set check and the explicit HONESTY RULE wording. The resolved questions also had no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate amended. Owners set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where should the new branch sit relative to the other opt-in scans? | After `--source-anchors`, with the precedence documented in help. | Make the flags mutually exclusive in argparse (changes an existing CLI contract); run every requested scan (a combined record has no current shape). | observed first-match behavior of `cli._run_check` | yes |
| D-2 | Should the plan's 7 advisory `IPD-C801` notes be fixed? | No; they cite the measured defect itself. | Rewrite them with symbols (the cited sites are the defect being measured, so a symbol would misdescribe the finding). | spec `ipd-structure-and-linting` Section 10.2 line-as-subject case, as cited by plan F-03 | yes |
