# Review findings: plan rlhmt9

- Subject-Id: rlhmt9
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `fb4e23e99`. The plan was committed and byte-identical to the sealed lane input, so no
pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before revision and
`--phase review-finalize --agent` was clean after it.

Re-verified (code reads; AST walk; subprocess runs with `PYTHONPATH=<lane>`, `AW_NO_REEXEC=1`, isolated `HOME`):
- The three mixed helpers and their callers are exactly as F-01 states. Each helper body is a single `resolve_verb_repo_root(getattr(args, "dir", None))`.
- `attention.run` and `cli._run_plans` both hand-roll the `classify_project_dir` / `no_project_message` refusal (F-04 holds).
- Every read and write verb named accepts `--dir`. The five write verbs all have `--apply`, so preview mode exists for each.
- On an empty installed fixture, all four read verbs answer clean at both `--dir <root>` and `--dir <deep>` (F-09). `run_check_miscategorized` has no `--agent` branch.
- A scratch copy with a refusal added to the four read verbs, run over every test that drives them, produced `1 failed, 370 passed` (F-10).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | D. Anti-regression / scope paths | `tests/test_agent_field_projection.py:267` `cli.main(["releases","show","zzzzzz","--dir", tmp, "--agent"])` with `next == "aw releases list"` | E-03's refusal breaks a shipped projection test whose fixture is a bare non-project. The test was outside Scope-Paths and the plan did not anticipate it. | all Low | FIXED | Added F-10. E-03 now requires a fixture-only repair, the file is added to Scope-Paths and the focused run, and V-03 requires the fail-then-pass proof. |
| PR-002 | MEDIUM | IN-SCOPE | E. Non-vacuous controls | F-09 measurement: all four read verbs are clean at both roots on an empty fixture | Without seeded data the read-side matrix cannot tell the refusal from the greenwash. The fixture recipe named (`--records-backend repository` alone) installs nothing non-interactively. | all Low | FIXED | E-05 now gives the complete install recipe, isolates `HOME`, and seeds a nonzero observable per verb (a release, a dangling citation, an archived-but-cited doc). |
| PR-003 | MEDIUM | IN-SCOPE | G. Output-surface correctness | `research_archive.run_check_miscategorized` only `print`s and returns 0/1 | E-03 and E-05 demanded a `cannot-run` machine record for a verb that has no machine surface, which would force an unrequested output-contract addition. | all Low | FIXED | E-03 makes its refusal human-only. V-03 and V-05 were adjusted to match. |
| PR-004 | MEDIUM | UNDER-SCOPE | D. Consistency with Set decisions | sibling `jei45f` OQ-02 (refuse bare no-project too) | The plan did not say whether the guard keys on `--dir` or on the resolved root. An `if explicit_dir` guard would leave the bare greenwash in place and diverge from Order 02. | all Low | FIXED | E-03 now keys on the resolved root. The bare-outside-project row was added to E-05 and V-03. |
| PR-005 | MEDIUM | IN-SCOPE | G. Sequencing | `pua92o` changes `cli._nv_backend_args`, which dispatches `aw rename/group/archive research`; it depends only on `sjsb04` | Order 05 was missing from `- Item-Dependencies:`. This plan could capture its write-side BEFORE baselines and E-04 captures on the pre-Order-05 adapter, and the gate's "last carrier" claim would be false. | all Low | FIXED | Added `executed:pua92o` (no cycle) plus F-11, and updated the gate text. |
| PR-006 | LOW | IN-SCOPE | E. Evidence feasibility | E-04/V-04 "byte-identical" bar | A before/after diff needs captures taken before the edit; the plan did not say so. | all Low | FIXED | E-04 and V-04 now require same-fixture captures taken before editing. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should `check-miscategorized` gain an `--agent` refusal record? | No; human-only refusal | Add a machine surface | It has no machine surface today; adding one is an output-contract change no finding asks for | yes |
| D-2 | Make this plan depend on `pua92o`? | Yes | Leave the ordering to chance | F-11; the gate text claims this is the last carrier | yes |
| D-3 | How to handle the `releases show` projection test? | Repair the fixture only | Widen its assertions; exempt `run_show` | The test asserts projection, not non-project behavior (F-10) | yes |
