# Review findings: plan 1i2kgq

- Subject-Id: 1i2kgq
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`c556e6f79`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize --agent` was clean after revisions (one intermediate `IPD-I305` from prose in a `Depends on:` field was fixed).

Re-verified at review HEAD:
- `agent_workflows/backlog.py:1281` `run_new`: `core.kebab(getattr(args, "slug", None) or item.summary or "item")[:50] or "item"`, hand-formatted f-string filename at 1283.
- `agent_workflows/set_records.py:349` `promote_question_to_backlog`: `(_core.kebab(summary or "question")[:50]) or "question"`, `.format` filename at 350.
- `agent_workflows/prompts.py:509` `core.kebab(slug_arg)[:60].strip("-")` idiom exists.
- `agent_workflows/specs.py:1084` and `agent_workflows/ipd_authoring.py:579` slices route through `artifact_naming.build_clustered_name` (`artifact_naming.py:219` re-applies `_core.kebab(slug)`); `plans_refs.clustered_name` delegates to it.
- Scratch-repo probe: `run_new` with summary `"a"*49 + " tail words"` wrote `...-aaaa...a-.backlog.md`; `backlog.run_check` returned 0 and `validate_item` reported no drift on that name; `promote_question_to_backlog` wrote the same shape without raising; `check_engine.check_names(repo, "backlog")` returned `['check.name-nonconformant']`, and `python3 -m agent_workflows check backlog --agent` exited 1 with that rule. After renaming the files to drop the trailing `-`, `check_names` returned `[]` and `check backlog` exited 0.
- `build_clustered_name(..., slug=kebab("a"*49+" b")[:50], artifact_type="spec")` returned `20261014-s-01-abc123-aaaa...a.spec.md`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Testing / D. Anti-regression | `agent_workflows/backlog.py:1752` `run_check`; `agent_workflows/backlog.py:418` `validate_item`; `agent_workflows/check_engine.py:1316` `check_names` | E-03's oracles (`backlog.run_check` returns 0; `validate_item` reports no drift) both PASS on the pre-fix defective filename, measured in a scratch repo. The regression tests as written could never go red, so V-03's "failing on pre-fix code" demand was unsatisfiable and the tests would guard nothing. The filename grammar is checked only by `check_engine.check_names`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now asserts on the filename and on `check_engine.check_names(repo, "backlog")` reporting no `check.name-nonconformant`, and explicitly forbids `run_check`/`validate_item` as the oracle. V-01 wording, Step 0 conventions, and Required tests swept to match. |
| PR-002 | MEDIUM | IN-SCOPE | Evidence | `agent_workflows/set_records.py:351` `drift = _backlog.validate_item(dest, rendered)` | E-02's expected outcome implied the pre-fix promotion might be "refused". It is not: `validate_item` does not check the name, so the nonconformant file is written. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 expected outcome corrected with the measured behavior. |
| PR-003 | MEDIUM | IN-SCOPE | G. Sequencing | plan E-03 `Depends on: E-01, E-02`; V-03 "failing on pre-fix code" | E-03 depended on E-01/E-02, yet V-03 demands a red run on pre-fix code, forcing a revert dance. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 is authored and run first (`Depends on: none`); Proposed changes reordered; V-03 demands both red and green runs. |
| PR-004 | LOW | UNDER-SCOPE | G. Execution contract | `## Approval and execution gate` | Gate lacked the OQ status line, scope-fence declaration, MUST-paste honesty rule, and conditional runner/executor finalize ownership with no hand `git mv`. OQ-01 owner was `none` and its HOW-style resolution lacked a demonstration. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Execution contract added; OQ-01 owner set to `plan author` with the `build_clustered_name` demonstration cited. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which oracle should the regression tests use for filename conformance? | `check_engine.check_names(repo, "backlog")` | `backlog.run_check` / `validate_item` (do not check names); subprocess `aw check backlog` (heavier, same rule) | `agent_workflows/check_engine.py:1316` `check_names`, `:1390` emits `check.name-nonconformant`; scratch-repo probe above | yes |
| D-2 | Leave specs/IPD slices unchanged (OQ-01)? | Yes, unchanged | Add defensive `.strip("-")` there too | `agent_workflows/artifact_naming.py:219` re-kebab; demonstrated `.spec.md` name has no trailing hyphen | yes |
| D-3 | Keep Work-Kind `chore` (not `bug`, which would need `Blocks-Release`)? | Keep `chore`, inherited from backlog `g73xcx` | Reclassify `bug` | backlog item `g73xcx` is `Work-Kind: chore`; reclassification is the item owner's call and the defect is only reachable with a 49-char-boundary summary | yes |
