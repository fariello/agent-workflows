# Review findings: plan 9g97e5

- Subject-Id: 9g97e5
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `1968ee6cb` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review, and `--phase review-finalize` was clean after revision.

Re-verified:
- Target `self.assertEqual(len(swept), 24)` present in
  `TestArtifactAuditEngine.test_terminal_states_tolerance_and_counterexample_trichotomy`; `swept` built by
  `for st in sorted(runner_shared.TERMINAL_STATES): swept.add(st)` (the F-03 tautology holds).
- `test_terminal_states_union` plus `tests/test_artifact_audit.py`: `25 passed in 0.98s` (1 + 24).
- In-process rebinding probe (no source edit; scratch under gitignored `tmp/`, deleted): growth
  `3 failed, 14 passed` with `'probe-25th-state' not found`; shrink (`not-attempted`) `2 failed, 15 passed`,
  including `test_terminal_states_union`. With the literal still present the edited test fails on shrink,
  consistent with F-04's claim that after deletion it would not.
- `8fo926` is now `reviewed` and declares `tests/test_artifact_audit.py` (adds two tests). `76ic0k` approved.
  `rdtme9` and `2je7m3` open. `git status --short` clean at end.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Live-artifact criterion | E-01 Expected outcome, Required tests item 4, V-01 (f) "reports `24 passed`"; `8fo926` E-02/E-03 add tests to the same file and is now `reviewed` | A collected test count is a live artifact of test organization, not a bar. If `8fo926` lands first, a correct execution reports 26 and fails V-01 (f). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bar is now "all passed, collected count unchanged from the same command run before the edit", re-derived at execution. |
| PR-002 | LOW | IN-SCOPE | B/D Safety of probes | Required tests item 5, V-01 (d)/(e) edit `agent_workflows/runner_shared.py` and revert | Mutating an out-of-scope production file in a shared checkout is avoidable: an in-process rebinding of the module attributes reaches both tests without touching any tracked file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the demonstrated in-process mechanism as preferred, with measured output; the source-edit route remains as a fallback under the existing revert rules. |
| PR-003 | MEDIUM | IN-SCOPE | G. Execution contract | Gate: "`aw ipd finalize` for the terminal transition" | The finalize instruction was unconditional. Under `aw oc run` the runner owns that step. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Ownership is now conditional (runner vs. hand executor), plus scope-declaration wording; `8fo926` status refreshed in F-06. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does F-04's shrink-direction residue need to stay detectable inside this file? | No; the cross-file name pin carries it and is a stop condition | Keep the literal (fails on legitimate growth, the defect being removed); add a hand-written name table here (duplicates `test_terminal_status_vocabulary.py`) | Shrink probe: `test_terminal_states_union` red; P16 "No count or census pins" | yes |
| D-2 | Accept OQ-01's refusal to delete the tautology? | Yes | Delete it too (touches lines `8fo926` cites, wider than the backlog item) | `8fo926` prose citing those lines; backlog `2je7m3` scope | yes |
