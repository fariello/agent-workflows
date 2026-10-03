# Review: Refuse an unsafe descriptive value at every research write path

- Subject-Id: deftzy
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The plan was committed and unchanged (`9a3d3d03a`), so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before edits and `--phase review-finalize` was clean after them.

Re-verified at lane HEAD `db3126a69`:

- `research_cmd` has no `_refuse_unsafe_descriptive` yet, and does not import `attention_contract` or `backlog` at module level. After `import agent_workflows.research_cmd`, `agent_workflows.backlog` is absent from `sys.modules`.
- Calling `build_frontmatter` with summary `legit\nstatus: reference\nblocks-release: next` and topic `a]\nstatus: reference\nblocks-release: next\njunk: [x` makes `parse_frontmatter` return `status=reference`, `blocks-release=next`, `topic=['a']`, `junk=['x']`, while `validate_frontmatter` returns `[]`.
- Calling `update_frontmatter_fields` with `consumed-by` rendered from `aaaaaa]\nstatus: active\njunk: [x` produces `consumed-by=['aaaaaa']`, `status=active`, `junk=['x']`, with no `validate_frontmatter` drift.
- The `backlog._refuse_unsafe_descriptive` outputs match the plan's quoted strings exactly, including the `bound_length=False` whole-value control-character case.
- `artifact_adopt._first_heading` passes the ESC byte through. `plan_adoption` returns `(None, err)` on a planner error, and `run_adopt` emits it as `cannot-run`, exit 2.
- `status_set._refuse_unsafe_descriptive` already forwards to `backlog` through a function-local import (`4gwgo3`). `uz05bl` has EXECUTED. Hoist plan `685iq8` is pending, and its Deferred section says this plan "should import it instead of porting".
- `pyproject.toml` `addopts` is `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`.
- Pending `wjvn8a` (`ol1m2q`) depends on `executed:deftzy` and already says to check for the `attention_contract` import before adding it. It stays compatible with the forwarder design.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Architecture, reuse (C/F) | plan E-01 "PORT `backlog._refuse_unsafe_descriptive` VERBATIM"; `agent_workflows/status_set.py` `_refuse_unsafe_descriptive` forwarder; pending `685iq8` Deferred "should import it instead of porting" | E-01 adds a fourth literal copy while the shipped precedent forwards, and a pending hoist exists to remove copies. The plan's deferral rationale ("`uz05bl` is still pending") is stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01, V-01, proposed change 1 and the hoist deferral were rewritten: the helper forwards to `attention_contract.refuse_unsafe_descriptive` if `685iq8` has executed, otherwise to `backlog` through a function-local import. Wording is byte-identical by construction. |
| PR-002 | MEDIUM | IN-SCOPE | Validation honesty (E) | plan V-02(b) "against HEAD code"; Required tests "`git worktree` at HEAD" | Once the fix is committed, `HEAD` contains it, so a pre-fix counterpart run against `HEAD` would silently test the fixed code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The executor now records a `<base>` sha before any edit, and every pre-fix run uses `<base>`. |
| PR-003 | MEDIUM | IN-SCOPE | Testing (E) | plan E-06(d), V-06(d); `research_cmd._existing_id6s` scans filenames on disk | The `_existing_id6s(root) unchanged` assertion is vacuous. The planner never writes, so it passes both before and after the fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with a before/after listing of the research tree. The mint ordering is verified by diff review, not by a test. |
| PR-004 | LOW | UNDER-SCOPE | UX, novice (F) | `artifact_adopt.plan_adoption` `summary=summary or _first_heading(text) or suggestion.slug` | In the heading-only adopt case the refusal names `--summary`, a flag the user never passed, which leaves them without a path to recovery. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and V-02(d) add a clause, in `plan_adoption` only, that names the first heading as the source and `--summary` as the override. `artifact_adopt.py` is added to Scope-Paths, the fence and the commit line. No pending plan declares that file. |
| PR-005 | LOW | IN-SCOPE | Evidence accuracy | plan conventions, Required tests and gate quote `-m 'not slow'`; `pyproject.toml` `addopts` | The quoted addopts were stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three occurrences were corrected to `-m 'not slow and not livecorpus'`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Port a fourth helper copy, or forward to the existing owner? | Forward, with the target picked at execution HEAD | Verbatim port, as authored; making this plan depend on `685iq8` | `status_set._refuse_unsafe_descriptive` precedent; `685iq8` Deferred; `uz05bl` in `executed/` | yes |
| D-2 | Fix the misleading `--summary` refusal in the adopt heading case? | Yes, with a clause in `plan_adoption` and the planner wording left unchanged | Leave as is (user confusion); change the planner message (breaks cross-tree wording) | `artifact_adopt.plan_adoption` summary fallback expression | yes |
