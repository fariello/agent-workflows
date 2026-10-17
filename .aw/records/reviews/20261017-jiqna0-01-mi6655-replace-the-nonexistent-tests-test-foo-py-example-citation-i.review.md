# Review findings: plan mi6655

- Subject-Id: mi6655
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `f0906ca7f`. Plan committed and byte-identical to the lane
input (`cmp`), so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`. Not an orchestrator.

Verified at review:
- `CONTRIBUTING.md:147` and `AGENTS.md:304` each contain exactly one `tests/test_foo.py`
  (`rg -n test_foo CONTRIBUTING.md AGENTS.md`); `ls tests/test_foo.py` fails (No such file or directory).
- `AGENTS.md:139` is the `<!-- /aw:block -->` line; the citation at line 304 sits in the repo-local
  "Repository development contract" section (marker comment at `AGENTS.md:301`), so no `engine.py` change.
- `tests/test_core_tier_selection.py` exists; its module docstring states "An explicit path invocation runs
  all non-slow tests (including non-core)". `python3 -m pytest tests/test_core_tier_selection.py` at review:
  `8 passed in 24.42s`.
- `rg "non-slow in that path"` in `agent_workflows` and `tests`: no match, so no test or template pins the text.
  Repo-wide, the only other carrier is executed plan `hguae9` (correctly declared immutable).
- Placeholder allowlists cited in Step 0 exist: `agent_workflows/check_engine.py:9035`,
  `tools/lost_guard_census.py:92`; `conftest.py:137` docstring illustration exists.
- `test_core_tier_selection` currently has zero matches in both docs, so V-01/V-02's "one match" bar is
  produced only by the edit.
- Backlog `jiqna0` is `graduated`, `Work-Kind: bug`, `Blocks-Release: next`; the plan inherits both and
  carries `From-Backlog: jiqna0`.
- `aw sanitize --agent`: `clean`, 0 findings.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | UNDER-SCOPE | Rubric G (execution contract) | plan `## Approval and execution gate` "transition the plan to `executed/` through the tooled lifecycle (`aw ipd` begin/finalize)"; `.aw/records/plans/README.md:195-227` | The gate lacked the declaration-style scope-fence wording (justify out-of-scope edits at finalize), an explicit open-question status, and conditional runner/executor ownership of `aw ipd finalize` (it read as unconditional). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten as a bulleted contract: scope fence with finalize justification, MUST-paste honesty rule, `aw commit mi6655 -- CONTRIBUTING.md AGENTS.md`, never push, finalize owned by the runner under `aw oc run`/`aw agy run` and by the executor when run by hand. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which existing file should replace the placeholder (plan OQ-01)? | `tests/test_core_tier_selection.py` | Another arbitrary test file (works but does not demonstrate the explicit-path claim); a directory example only | `tests/test_core_tier_selection.py:1-5` docstring; review run `8 passed` | yes |
