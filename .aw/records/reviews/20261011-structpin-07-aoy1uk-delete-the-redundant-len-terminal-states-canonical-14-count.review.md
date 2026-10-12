# Review findings: plan aoy1uk

- Subject-Id: aoy1uk
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `ff5f9937d` in an isolated review lane. The plan was committed and unchanged, so no
pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review.

Re-verified:
- `test_canonical_terminal_states_set` is the equality against the hand-written 14-member
  `EXPECTED_CANONICAL_STATES` frozenset followed by `self.assertEqual(len(runner_shared.TERMINAL_STATES_CANONICAL), 14)`.
- `python3 -m pytest tests/test_terminal_status_vocabulary.py -o addopts="" -q` -> `16 passed in 0.49s`.
- In-process rebinding probe (scratch under gitignored `tmp/`, deleted, no source edit), literal still present:
  growth `'probe-15th-state'` -> `1 failed in 0.21s`; shrink `'retired'` -> `1 failed in 0.09s`; both raised by
  the name-level equality, so F-02 holds.
- F-04 site `assert len(rs.TERMINAL_STATES_CANONICAL) == 14` in `tests/test_runwire_verifier_authority.py`;
  carrier backlog `2n9y3f` exists in `open/`. Backlog `rdtme9` is `graduated` to `aoy1uk`, no `Blocks-Release`.
- `76ic0k`, `44c42h`, `9g97e5` executed. No other pending plan declares the file. `git status --short` clean.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | G. Execution contract | `## Approval and execution gate`, "If execution appears to need any other edit, STOP and report" and "Move the plan to `executed/` only through the tooled lifecycle" | The gate told the executor to STOP over a scope question (contrary to the 2026-09-01 scope-fence ruling), lacked the paste-actual-output honesty rule, `aw ipd begin`, and the conditional runner/executor finalize ownership, and did not state the backlog gate (none) handoff. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten to the sibling `9g97e5` house contract: scope as declaration with `--scope-reason`, safety stop kept only for the E-01 premise, honesty rule, `aw ipd begin`, staged-set check, never push, conditional finalize, no inherited Blocks-Release. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is the E-01 STOP-before-delete a forbidden scope-stop? | No; it is a genuine-safety stop on the redundancy premise and is kept | Remove it (would allow deleting a non-redundant pin) | plan-review Step 4 scope-fence wording, "A stop directive for a genuinely unsafe condition ... remains correct" | yes |
| D-2 | Is "16 at authoring" in E-01 / Required tests a forbidden collected-count bar? | No; V-01 (d) bars on before/after equality re-derived at execution, 16 is context | Strip the number | plan-review rubric G live-artifact convention | yes |
