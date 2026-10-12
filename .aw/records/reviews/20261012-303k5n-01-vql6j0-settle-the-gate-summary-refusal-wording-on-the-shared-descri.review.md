# Review findings: plan vql6j0

- Subject-Id: vql6j0
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `ba0fb6975` in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified by driving the code:
- `specs.run_set` docstring: "Thin adapter delegating to status_set.run_set_command" (F-01).
- `status_set.run_set_command` pre-flight loop refuses `--gate-summary` with `_refuse_unsafe_descriptive("aw set", ...)` and rc 2 before `validate_transition_allowed` reaches `validate_gate_flags` (F-05 unreachable-from-CLI claim holds).
- `attention_contract.validate_gate_flags("aw set","date","2026-10-02",v)`: newline, BEL, 301 and 400 chars all return `aw set: --gate-summary must be a bounded single control-char-free line`; 300 chars, `ok` and `""` return None. `refuse_unsafe_descriptive("aw set","--gate-summary",v)` returns `must not contain embedded newlines`, `must not contain control characters`, `exceeds maximum length of 300 characters (N > 300)`, and None for the same inputs. The E-02 expected outcomes are exactly reachable.
- The kind/ref arms run before the summary arm (`bogus` kind with a bad summary returns the gate-kind message), so E-02 cannot change their precedence.
- `git grep 'bounded single control-char-free' -- agent_workflows tests` hits only `attention_contract.py` (`validate_gate_flags`) and the stale test comment. `validate_gate_flags` has one production caller (`status_set.validate_transition_allowed`) and no test caller (F-06).
- `-k non_regression_already` -> `1 passed, 18 deselected`. The five related test files -> `1051 passed`.
- `CHANGELOG.md` has no `Unreleased` heading; the topmost pending section is `## 2.0.0 (pending)`.
- Spec `20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` exists under `specs/implemented/`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | E-04 "full suite reports `N passed` with no failures"; sibling plan `ttg9uz` F-09 measured `39 failed` bare at `2600a93e3` | Zero failures in the bare suite was the pass bar. On a tree that already has unrelated red tests, that bar blocks a correct execution, or pushes the executor into claiming a pass that did not happen. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 and V-04 now compare base and post-change failures by name and add a targeted-files run. |
| PR-002 | LOW | IN-SCOPE | G. Executability | `CHANGELOG.md` headings: `## 2.0.0 (pending)` is topmost, and there is no `Unreleased` | E-04 told the executor to add an `Unreleased` entry, but no such section exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now names `## 2.0.0 (pending)`. |
| PR-003 | LOW | IN-SCOPE | E. Verification precision | `grep -rn 'bounded single' agent_workflows` matches `agent_workflows/__pycache__/attention_contract.cpython-314.pyc` | A plain recursive grep matches stale bytecode, so the "absent" check can fail even after a correct edit. The pytest command also omitted `-o addopts=""`, and V-01 used a test count as its bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Every absence check now uses `git grep -- agent_workflows`. E-01 uses `-o addopts="" -q`. V-01 now requires "selected test passed, none failed". |
| PR-004 | LOW | UNDER-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate did not state the OQ status, the must-paste honesty rule, the scope-fence justification path, the staged-set check, runner ownership of finalize, or the ban on a hand `git mv`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added an EXECUTION CONTRACT and a POST-GATE LIFECYCLE paragraph. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Accept OQ-01's resolution to option (a) without asking the maintainer? | Yes | Escalate as blocking (the backlog item called it a maintainer call) | Executed plan `m94eht` refusal table marks the `--gate-summary` row `changed`, and `CHANGELOG.md` names `--gate-summary` among the changed refusals, so the maintainer-visible message change already shipped. This plan only changes an unreachable-from-CLI library string. | yes |
