# Check T: Review Tier

Answer each of the five tier questions below in the review record's `### Step T` subsection, one line each, each line starting `1.` to `5.` with the question's number:

1. Does the plan change a spec, a public interface (CLI option, output format, file format, configuration key), or another contract that other code or other plans rely on?
2. Does the plan touch code that guards private data, commits, worktree isolation, merges to main, or the sandbox? Examples in this repository: `agent_workflows/leak_sanitizer.py`, `agent_workflows/local_leaks.py`, `agent_workflows/git_commit_helper.py`, `agent_workflows/commit_lock.py`, `agent_workflows/lane_containment.py`, `agent_workflows/egress_policy.py`, `agent_workflows/host_sandbox_profile.py`.
3. Is the plan large or cross-cutting: many execution items, several task groups, or changes in several unrelated modules?
4. Does the plan list the files it changes (`- Scope-Paths:`)? If not, what does the review know about its reach?
5. Could a mistake in this change lose data, break existing behavior that other code depends on, or be hard to undo?

When run by a runner, the runner supplies the pre-pass facts in the first prompt (whether `- Scope-Paths:` names a `.spec.md` file, the execution-item and task-group counts, and the `- Scope-Paths:` list). An interactive reviewer collects them itself from the plan file.

Guidance in the step file, not a rule: a "yes" to question 1, 2, or 5 usually means `standard` or `complex`; `simple` fits a change where every answer is "no" and the change is small.

End your reply with the required last non-empty line:
```text
AW-TIER: <simple|standard|complex>
```
