# Review findings: plan plb8jx

- Subject-Id: plb8jx
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `b0d02e763`. The plan was committed and byte-identical to the
lane input (`cmp`), so no pre-review snapshot was needed. `aw ipd lint --phase author` was clean with zero
findings before review and `--phase review-finalize` clean with zero findings after revision. `- Kind:
child`, so `IPD-S407` does not apply.

Verified by symbol: `research_refs.plan_set_assign` opens with the `a --set id is required` refusal and then
the `for i, id6 in enumerate(id6s):` loop; `_apply_renames` has the `if not apply:` preview printing
`p.new_path.name`, the `_rel` helper using `relative_to`, and the unguarded `dst_rel =
p.new_path.relative_to(repo_root).as_posix()`; `run_set_assign` computes the date default before calling the
planner; `research_refs` imports `research_cmd as _rcmd`, and `research_cmd` imports only `artifact_core` and
`research_contract`; `_refuse_unsafe_date` does NOT exist yet; `iumgvk` is `reviewed`/`go-pending-approval`;
`ki1uqk` is open; `deftzy`, `m5csyi`, `7w6zsl`, `tf4jz5` exist. No destructive probe was run at review.

NON-DESTRUCTIVE MEASUREMENT AT REVIEW (resolution only, nothing moved):

```
fresh <tmp>/n1/n2/n3/repo, git init, no research dir:
  no dir:   <home>/.aw/projects/repo-<hash>/records/research
after mkdir -p .aw/records/research:
  with dir: <tmp>/n1/n2/n3/repo/.aw/records/research
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Rubric B/E (test safety) | `research_contract.resolve_research_root` -> `record_producers.resolve_record_path`; measurement above; sibling `iumgvk` E-04 PR-001 | The plan bounds probes by fixture-path arithmetic, but an unregistered scratch repo without a research directory resolves its research root under the real home, so the bound can say "safe" while the move lands in the user's home. V-03's legacy-layout fixture deliberately lacks `.aw/records/research` and is exactly that case | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 requires pre-creating the research dir, isolating `HOME`/`XDG_CONFIG_HOME`, and computing the bound from the resolved root, for tests and manual probes; gate updated |
| PR-002 | HIGH | IN-SCOPE | Rubric G (reachability) | `_apply_renames` returns `Tuple[str, ...]`; `run_set_assign`/`run_mv` `return MutationResult(0, touched)` | E-03's "nonzero exit through the verb's existing result channel" does not exist: the funnel cannot signal a refusal, so an implementer would either exit 0 on refusal or raise | all Low | FIXED | E-03 specifies a pure containment helper, a refusal sentinel from `_apply_renames`, and `MutationResult(2)` in both callers (the only two); that helper is also the stated E-02 bypass for V-03 |
| PR-003 | MEDIUM | IN-SCOPE | Cross-plan contract consistency | `iumgvk` E-01 "validating `\A[0-9]{8}\Z` (ASCII digits; PR-002)" vs this plan's `\A\d{8}\Z` | OQ-03's convergence rests on identical contracts, but `iumgvk`'s review changed its regex to ASCII (Python `\d` accepts fullwidth digits); the two plans now diverge | all Low | FIXED | Aligned E-01/V-01/Proposed changes to `\A[0-9]{8}\Z`; added the fullwidth input to the verdict table; OQ-03 note |
| PR-004 | MEDIUM | IN-SCOPE | Scope fence | E-01 second branch edits `research_cmd`; `- Scope-Paths:` lists only `research_refs.py` and the test | A declared branch of E-01 writes an undeclared file | all Low | FIXED | Declared `agent_workflows/research_cmd.py`, with `--scope-ack` on the reuse branch; gate SCOPE FENCE paragraph added |
| PR-005 | LOW | IN-SCOPE | Internal consistency; execution contract | Scope check "with a carrier to be filed at execution" vs Deferred "`ki1uqk` was FILED"; gate lacked the paste-actual-output rule | Stale wording and a missing honesty clause | all Low | FIXED | Scope check corrected; honesty rule added |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How does `_apply_renames` signal a containment refusal? | Return a sentinel; callers return `MutationResult(2)`. | Raise an exception: rejected, it trades F-06's traceback for another. Print and return `()`: rejected, the verb would exit 0 on refusal | `_apply_renames` signature; `run_set_assign`/`run_mv` bodies | yes |
| D-2 | Which regex, given the sibling's reviewed change? | `\A[0-9]{8}\Z`, matching `iumgvk`. | Keep `\d`: rejected, the two plans would add divergent definitions of one helper, contrary to OQ-03 | `iumgvk` E-01 PR-002 note | yes |

No `Reversible: no` decision. OQ-01..OQ-03 remain `resolved`, `Blocking: no`. No finding is left `OPEN` or
`DEFERRED`.
