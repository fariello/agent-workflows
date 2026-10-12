# Review findings: plan yxsfjc

- Subject-Id: yxsfjc
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `c4246a696` in an isolated review lane. The plan was committed and unchanged (`2723651e6`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize` was re-run after revisions.

Re-verified:
- `cli.find_selector_vocabulary`, `cli.FindSelectorMatchFacts.refusable`, `cli.find_selector_match_facts`, and `_run_find`'s `if facts.refusable:` block (hand-built `kind:error` record, `assert_valid_agent_record`, human refusal on stderr through `format_empty_result`) exist as cited.
- Predicate over all `ARTIFACT_TYPES`: `zzzzzz`, `none01`, `ZZZZZZ`, a home-path-shaped token refusable; `f36de0`, `25kzda`, `selquiet`, `approved`, `reviewed`, `tbe8v0`, a file path not refusable.
- `reviews.run_decisions` docstring "0 whether or not any decision was found"; `reviews._resolve_selector_paths` direct-path and no-reviews branches.
- `readiness_recheck._resolve` appends any token `resolve_selectors(..., "plans", [tok])` misses; `run_recheck_readiness` ends `return 1 if missing else 0`; `--stale-findings` amendments run inside the per-path loop.
- `command_surface`: `ipd recheck-readiness` `exit_contract=(0, 1, 2)`, command_class `mutation` (so the `domain_failure` scenario rule for read/check leaves does not apply to it); `record-history (0,1,2)`, `graduation (0,2)`, `reviews decisions (0,2)`.
- `tests/test_graduation_forward_links.py::test_case_6_no_source_at_all` asserts rc 0 and the `Proceed.` text for `none01`.
- `zyj8io` is in `plans/executed/`. Backlog `upryxf` exists in the Set's scope note.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | C. Operability / UX (user-perceptible latency) | Measured: `find_selector_match_facts(repo, list(ARTIFACT_TYPES), [tok])` 1.33s (`f36de0`), 1.44s (`tbe8v0`); per-type early exit hits `plans` after 0.20-0.31s; end to end `record-history h0tiaw --agent` 0.33s, `reviews decisions h0tiaw --agent` 0.45s | The plan said the predicate runs "only on the empty path", treating that path as the unknown-token path. A REAL-BUT-EMPTY token, the common answer for `record-history` (the sidecar is machine-local) and `reviews decisions`, also takes that path. An all-types call would make those answers about 4x slower, a perceptible regression the plan would itself ship. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now drops vocabulary and file-path tokens at no cost, then resolves type by type with early exit, still built only from `find_selector_match_facts`. Added F-11. V-02 demands equality with the all-types answer plus timing. V-09 demands before/after real-but-empty timings. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness (state ordering) | `reviews._resolve_selector_paths` returns "no review records exist yet" before any selector judgement | E-03 grouped "no review records exist at all" with legitimate empty answers. An executor could then skip the refusal whenever the repo has no reviews, letting an unknown token pass as clean. | all Low | FIXED | E-03 now states that the refusal depends only on the predicate, and an unknown token is refused even with zero reviews. E-08 adds that case. |
| PR-003 | MEDIUM | IN-SCOPE | Evidence | Driven: `aw ipd recheck-readiness 25kzda --agent` -> exit 0, 13 plans re-checked; `adgtqb` (backlog) -> exit 1 `readiness.selector-unresolved` | E-07, V-07 and E-08 used "a spec id6" as the non-plan example. A spec id6 is usually cited by its plans and resolves as a plan through the substring rung, so the case would not exercise the path it names. | all Low | FIXED | Added F-12. Every non-plan case now names an artifact id6 that matches no plan (`adgtqb`, or one re-derived the same way). |
| PR-004 | MEDIUM | IN-SCOPE | A. Correctness / E. Testing | `readiness_recheck.run_recheck_readiness` per-path loop runs `_run_stale_findings` before `PR.recheck_readiness` | Refuse-before-write was specified for the plan write only. `--stale-findings` also amends review records in the same loop, and the mixed-invocation test used a plan that may have had nothing to write, so it could pass without proving anything. The live-repo `--apply` instruction in V-07 would also have mutated tracked plans. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 covers `--stale-findings`. E-08 and V-07 use a fixture plan carrying a re-checkable `no-go` (so a write would otherwise happen) and require the plan and review record to stay byte-identical. The gate confines `--apply` to fixtures. |
| PR-005 | LOW | IN-SCOPE | Evidence (OQ-02) | `git log -S'"ipd recheck-readiness"' -- agent_workflows/command_surface.py` -> `af3b5b2e9`; `git tag --contains af3b5b2e9` empty | OQ-02 called the 1 -> 2 move a change to a "published exit contract" without checking whether any release carries it. | all Low | FIXED | Added F-13. OQ-02 records that no release ships the exit 1. |
| PR-006 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate`; Scope check "stop and re-declare rather than editing" | The gate lacked the approval/OQ statement, `aw ipd begin`, the staged-set check, the never-`--no-verify` rule, conditional finalize ownership and the prerequisite check. The scope check told the executor to stop over a scope question, contrary to the declaration rule. | all Low | FIXED | Gate rewritten. The scope-check line now says make the edit and justify it with `--scope-reason`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the shared predicate avoid the all-types cost on real tokens? | Vocabulary and file-path short-circuit, then per-type `find_selector_match_facts` with early exit | One all-types call (about 4x slower real-but-empty answers); a new resolver (duplicates `find` and violates the plan's reuse rule) | F-11 timings; `find_selector_match_facts` accepts `types` and `vocabulary` parameters | yes |
| D-2 | Which artifact exercises the "real non-plan" `recheck-readiness` case? | An id6 matching no plan (`adgtqb` at review) | A spec id6 (resolves as a plan through citing plans) | F-12 drive | yes |
| D-3 | Must refuse-before-write cover `--stale-findings` amendments? | Yes | Plan write only (leaves a partial review-record mutation) | `run_recheck_readiness` loop order; OQ-01's rationale | yes |
