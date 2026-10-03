# Review: Register the aw prompts set subparser and bound the prompts status vocabulary to its five buckets

- Subject-Id: 7z3ovv
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged (`2eac22968`), so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

Re-verified at lane HEAD `83888bf53`:

- `TYPE_STATUSES["prompts"]` holds 11 tokens, and `normalize_target_status("pending","prompts")` returns `to-review`.
- `LIFECYCLE_SUBDIRS["prompts"]` and `CLASS_MAPS["prompts"]` are the same 5 tokens.
- The `prompts set` declaration matches F-02.
- `aw prompts set` is rejected by argparse.
- `build_matrix` gives `[] ['prompts set', 'upgrade-test'] 1193`.
- The `cli.main` `prompt_cmd == "set"` arm is live.
- Both F-11 docstrings are present.

I applied the E-01 narrowing in-process and ran `tests/test_status_set.py` and `tests/test_status_set_descriptive_safety.py`. The result was `4 failed, 104 passed`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness of carrier handling (A/G) | `.aw/records/backlog/graduated/20261001-setdispgate-01-68sur3-...backlog.md` "graduated by run run-20261001T221821Z-1985969: gm9baj", `- Graduated-To: declabsent`; plan `gm9baj` `- From-Backlog: 68sur3` | E-07 told the executor to graduate `68sur3` from `open/` to point at `7z3ovv`. Since authoring, `68sur3` has been graduated to `gm9baj`. Executing E-07 as written would act on a path that no longer exists and could sever `gm9baj`'s HANDOFF carrier. Scope-Paths also declared the stale `open/` path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07, the Deferred section, the Scope check, V-07 and the gate now say `68sur3` is carried by `gm9baj` and must not be edited. The stale path is removed from Scope-Paths. Added coordination with `gm9baj`'s set-equality allow-set: if `gm9baj` has already executed, delete the stale `prompts set` entry and justify it with `--scope-reason`. |
| PR-002 | HIGH | UNDER-SCOPE | Anti-regression (D) / testing (E) | review measurement: in-process narrowing gave `4 failed, 104 passed`; `tests/test_status_set.py` `test_prompt_set` (`approved`), `test_set_multiple_mixed_types` (`reviewed`), `test_a_non_plan_artifact_transition_is_unaffected` (`draft`); `tests/test_status_set_descriptive_safety.py` `test_conforming_transitions_across_five_trees` (`to-review`) | E-01 breaks four existing tests that drive a prompt to a non-bucket status. The plan named none of them, and one file was not in Scope-Paths. A "zero failures" bar would push the executor either to weaken the narrowing or to edit tests without guidance. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now records the four measured failures. E-06 re-targets each prompt member to a real bucket and adds an explicit assertion that a mixed batch with the prompt at `reviewed` is refused. V-06 demands the diffs and passing results. `tests/test_status_set_descriptive_safety.py` is added to Scope-Paths. |
| PR-003 | MEDIUM | IN-SCOPE | Live-artifact criteria (G) | V-03 "row count GREATER than the 1193"; E-07/V-07/Required tests "zero failures"; open `wc5c5e` | Two bars rested on live artifacts. The 1193 matrix total is moved by other plans (`gm9baj`, `lbbo9s`), and "zero failures" ignores load-sensitive nodes that already fail. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 now asserts that `rows_for('prompts set')` is non-empty and its scenarios equal `required_scenarios(decl)`. The suite bar is now "no failed node absent from the pre-edit `<baseline>`", with the baseline recorded in E-01. |
| PR-004 | MEDIUM | IN-SCOPE | CLI correctness (A) | `cli._add_commit_flags` docstring "`--commit` ... the only way to commit non-interactively"; `p_ipd_set` calls `_add_commit_flags(p_ipd_set)`; `status_set._offer_self_commit` reads `args.commit`/`args.no_commit` | E-03's flag surface omitted the shared commit flags, so a non-interactive `aw prompts set` could never commit, unlike every sibling setter. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now registers `_add_commit_flags(p_prompts_set)` and adds `--commit`/`--no-commit` to the declaration. V-03 lists them. |
| PR-005 | MEDIUM | IN-SCOPE | Shared-checkout safety (B/G) | V-05 "`git stash push -- agent_workflows/`"; AGENTS.md shared-checkout rule | The negative-control stash covered the whole `agent_workflows/` directory, which can sweep a co-worker's uncommitted edits. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The stash is now limited to this plan's four production paths. |
| PR-006 | MEDIUM | UNDER-SCOPE | Execution contract (G) | gate "move this plan ... (`aw ipd finalize`...)" unconditional; no scope fence | The gate told the executor to run `aw ipd finalize` unconditionally and declared no scope fence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SCOPE FENCE declaration and conditional runner/executor finalize ownership. |
| PR-007 | LOW | IN-SCOPE | OQ owner | OQ-01/OQ-02 `Owner: author` | The owner label was not in the standard form. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both are now `Owner: plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Who carries `68sur3` now? | Leave it with `gm9baj`; this plan does not edit it | Re-graduate it to `7z3ovv` (breaks `gm9baj`'s carrier); add a second `From-Backlog` (a plan carries one) | `68sur3` history line; `gm9baj` front matter and Scope `OUT` | yes |
| D-2 | Fix the four broken vocabulary tests by re-targeting them or by keeping a wider vocabulary? | Re-target them to real buckets and add a refusal assertion | Keep `reviewed`/`draft`/`to-review` valid (re-introduces the F-04 defect) | F-03 corroborated by `LIFECYCLE_SUBDIRS`, `CLASS_MAPS` and the docs table; review measurement `4 failed` | yes |
| D-3 | Narrowing refuses `approved`/`reviewed`/`draft`/`to-review` on `aw set` for prompts. Is that a breaking public-contract change? | Treat it as a bug fix, not a contract break | Deprecation window | All tracked prompts carry `pending`/`executed`/`superseded` in their comment (F-03), and the refused tokens map to no bucket and produced `check.prompt-status-mismatch` (F-07). The plan carries `Work-Kind: bug` and `Blocks-Release: next`. | yes |
