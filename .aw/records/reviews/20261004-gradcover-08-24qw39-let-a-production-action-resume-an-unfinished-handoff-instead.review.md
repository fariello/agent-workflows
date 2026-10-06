# Review findings: plan 24qw39

- Subject-Id: 24qw39
- Subject-Type: ipd
- Reviewed-At: 2026-10-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in lane `review-sweep-run-20261006T040814Z-944` at HEAD `087dcc1df`. The plan was committed and byte-identical
to the sealed lane input (rev-9); no snapshot needed. `- Kind: child`, so `IPD-S407` does not apply. `aw ipd lint --phase
author` clean before; `review-finalize` clean after.

Re-measured: `production_checks.backlog_graduate_count` / `spec_plan_count` (`duplicate_active` clause),
`_check_ipd_conformance` (exact `to-review`), `_TERMINAL_DISPOSITIONS`; `runner_shared.execute_item_core` production
branches (baseline from the main repo, verifiers on `new_produced_paths`, `produced_ids_str` and `produced_sets` from
`new_produced_plans`); both prompt builders and their two call sites (main tree, then lane tree);
`commit_backlog_production_output` / `commit_spec_production_output`; spec `25kzda` amendment text in `hm1h3l` A.8 and
the 4.8/4.9 pass-criterion replacement; `tests/test_backlog_production.py` and `tests/test_spec_production.py` count
tests. Scratch-repo probe of the commit helper; corpus scan of active linked plans by Set and status.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | A data integrity | scratch repo: `commit_backlog_production_output(d, "bkl001", {"old001"})` returned `(sha, (new001 path,), (old001 path,))`, edited `old001` left ` M` | The agent's fixes to existing plans, the plan's whole purpose, are classified out of scope and never committed; in a lane they are lost at integration. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-05/V-05: `continued_plan_ids` allowlist for modified existing pending plans, pre-dirty exclusion in the shared checkout, deletes/renames stay out of scope; integration case (iv) and second mutation. |
| PR-002 | HIGH | IN-SCOPE | A correctness | scan: `25kzda` 7 Sets, `2vev8j` 4, `uonrjg` 3, `7ckptx` 2; no backlog item >1 | Rule (c) "linked plans carry more than one Set" would refuse every future plan production on four approved specs that legitimately span phases. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rule (c) fails only a Set this action introduces next to existing plans; pre-existing multi-Set states pass; Set-less plans grouped by id6. |
| PR-003 | HIGH | IN-SCOPE | A correctness | `_check_ipd_conformance` "expected 'to-review'"; scan: 59 active linked plans `approved`, 70 `to-review` | E-03 feeds existing plans to the per-plan verifier, which fails any `reviewed`/`approved` plan, so a partly-approved handoff could never continue. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `continued_ids` keyword: existing plans pass at `to-review` or later, new plans still exactly `to-review`, existing `draft` fails. |
| PR-004 | MEDIUM | IN-SCOPE | F UX / A | `26m1nb` E-01/E-05 (children-first, backward `--message`) | The continue instruction did not say how to edit a `reviewed`/`approved` plan, children-first ordering, that Production Contract items 1-2 are for new plans, or forbid deleting/moving existing plans; the backward-move edge it relies on lands in `26m1nb`, not in this plan's chain. | Overall:Low | FIXED | Instruction extended; placement stated; `executed:26m1nb` added. |
| PR-005 | MEDIUM | IN-SCOPE | A correctness | `execute_item_core` `produced_ids_str`, `produced_sets` | A pure continuation would graduate with an empty id list and no `--graduated-to`. | Overall:Low | FIXED | E-03 computes both from existing plus new plans; V-03 checks the recorded value. |
| PR-006 | LOW | IN-SCOPE | G executability | the two builder call sites (`repo`, then `lane_root`) | Which tree the existing-plan list is read from, and that building a prompt must not ask the probe, were unstated. | Overall:Low | FIXED | Root = `lane_root` or `repo`; `ask=False`; zero probe calls asserted. |
| PR-007 | LOW | UNDER-SCOPE | E regression | `test_backlog_graduate_count` step 4; `test_spec_plan_count` step 3 | Two tests pin the old duplicate refusal; the plan left them to `--scope-reason`. | Overall:Low | FIXED | Both named in E-04 and declared in Scope-Paths. |
| PR-008 | LOW | IN-SCOPE | G execution contract | gate section | No scope fence, paste-actual-output rule, dependency stop or finalize form. | Overall:Low | FIXED | Gate completed. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What does "only a SECOND active Set fails" mean for a spec already spanning several Sets? | Fail only a Set this action introduces | fail any multi-Set state (blocks four approved specs forever); never check Sets for specs | `hm1h3l` A.8/4.8 text; corpus scan | yes |
| D-2 | How are existing plans' edits committed? | Allowlist modified existing pending plans by id6 in the existing commit helpers, excluding pre-dirty paths in a shared checkout | a second commit path; commit everything under pending/ | `commit_*_production_output`; AGENTS.md shared-checkout rule | yes |
| D-3 | What status must an existing plan have? | `to-review` or later | exactly `to-review` (blocks approved handoffs); any status (accepts `draft`) | scan; `hm1h3l` 2.5d condition 2 ("below `to-review`" is the failure) | yes |
