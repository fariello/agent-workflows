# Review findings: plan 1f4faf

- Subject-Id: 1f4faf
- Subject-Type: ipd
- Reviewed-At: 2026-10-04
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Findings: PR-001 (LOW, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (HIGH, fixed), PR-005 (MEDIUM, fixed), PR-006 (HIGH, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261004T134544Z-4052083` at HEAD `c6b27962c`.
The target plan was committed and unchanged (byte-identical to the sealed lane input), so no
pre-review snapshot was needed. The plan's first `- Kind:` bullet reads `orchestrator`. `aw ipd lint
--phase author --agent` and `--phase review-finalize --agent` were both clean before revision, with
no `IPD-S407` finding, so the bounded repair loop did not run. After revision `review-finalize`
reports only `IPD-Q501`, which is the intended effect of the blocking OQ-03.

Re-measured: all 13 child files exist in `pending/` at `to-review`, and each child's
`- Item-Dependencies:` matches the table; release `f33nrj` is `planned`; `ipd_authoring` already
writes `"- Status: draft"` and the three `TODO` placeholders the Concern quotes;
`build_backlog_production_prompt` / `build_spec_production_prompt` contain no orchestrator or coverage
wording; `ipd_lifecycle.validate_transition('to-review','draft')` returns `ok=False`;
`probe_verdict_store_path` resolves under `.aw/state/runtime/`, matched by `.aw/.gitignore` `/state/`
(`git check-ignore -v`), and `DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS = 30`; `tests.yml` runs
`python -m agent_workflows check plans --agent` fail-closed; `axozpe` E-04 names `rlhmt9` as the
owner of the final measurement.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | G (accuracy) | 1f4faf child table row 05; `agent_workflows/ipd_authoring.py:286` `lines.append("- Status: draft")`; 26m1nb Scope "it already writes `draft` for both kinds" | The table said Order 05 makes the scaffold write `draft`; it already does, and 26m1nb only pins it. Row 05 also omitted the backward-move work (26m1nb E-05). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Row 05 and Scope now say "pin" the scaffold default and name the loud backward moves. |
| PR-002 | HIGH | UNDER-SCOPE | Orchestrator coverage (`25kzda` 2.5b) | 1f4faf `## Cross-IPD validation` "ONE PREDICATE ... Check by driving each surface ..." | The Set's own Scope check claims nothing is parked on the parent, yet the ONE PREDICATE five-surface parity check had no owner. qs00nc covers only lint/check/coverage parity; no child drives `aw ipd set`, production and retirement against one fixture. On retirement this would be marked complete unperformed, and the probe would (correctly) refuse the parent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `wytlly` E-05/V-05 (five-surface parity with a mutation); Cross-IPD bullet and Completion criterion 4 name `wytlly` as owner. |
| PR-003 | HIGH | IN-SCOPE | C (sequencing) | 52opph `- Item-Dependencies: executed:24qw39`, F-04 "depends on it transitively through Order 08"; chain 24qw39 -> nnsa2o -> r2wa38 -> qs00nc; wytlly deps `sbiv1j, dalmk4` while Runs B/C assert 5etev3 behavior | Two undeclared edges. 52opph's `aw ipd set draft --message` needs 26m1nb's backward edges, but 26m1nb is not in its chain, so a runner could dispatch 52opph first and every demotion would refuse. wytlly asserts Order 04 behavior with no path to 5etev3. The parent's E-09/E-12 mirrored the gaps. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `executed:26m1nb` to 52opph and `executed:5etev3` to wytlly (re-scope history lines on both), corrected 52opph F-04, and updated parent table, E-09 and E-12 deps and a Cross-IPD bullet. |
| PR-004 | HIGH | IN-SCOPE | A (integrity) | 52opph E-01 "every plan under pending/ whose Kind is orchestrator"; E-02 demotes every NOT-ready one | 52opph would measure and could demote `1f4faf` itself and its pending children (10 to 13) to `draft` mid-execution, stranding the Set it belongs to. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | 52opph Scope, E-01 and E-02 now exclude Set `gradcover` from demotion and stop-and-report if `1f4faf` is not ready; parent Cross-IPD and table say so. |
| PR-005 | MEDIUM | IN-SCOPE | G (execution contract) | 1f4faf `## Approval and execution gate` | The gate lacked the paste-actual-output rule and the path-scoped commit / never-push rule for a hand executor. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both added to the gate paragraph. |
| PR-006 | HIGH | IN-SCOPE | C/E (design feasibility) | `agent_workflows/runner_shared.py:18391` `probe_verdict_store_path` (`.aw/state/runtime/`, gitignored `/state/`); `DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS = 30`; hm1h3l D.1 rule 19 "An absent or stale verdict is a finding"; qs00nc E-04 `check.orchestrator-not-review-ready` severity `error`; `.github/workflows/tests.yml` "aw check plans (plan conformance; fail closed)" | Condition 4 is read from a machine-local, expiring, uncommitted store, yet the model-free consumers make its absence an error. CI, any other clone, and the same machine after 30 days have no verdict, so `aw check plans` fails permanently on every orchestrator at `to-review` or later, and `pre-execution` lint refuses them. qs00nc's Deferred describes only a temporary window, which understates it. | C:Medium-High; U:High; S:Low; F:High; Overall:High | FIXED | RESOLVED 2026-10-04 by maintainer ruling, recorded in the plan's OQ-03 (now `Blocking: no`, `Status: resolved`): the coverage answer is STORED IN THE PLAN (new `25kzda` 2.5e: `Coverage`, `Coverage-Fingerprint`, `Coverage-Checked`, `## Coverage findings`), written only by the tool with a matching history line and refused otherwise by new lint rule `IPD-M112`, excluded from the execution-receipt fingerprint, retiring the gitignored 30-day cache. Every clone and CI read the same record, so an absent or out-of-date record is an error in `aw ipd lint` and `aw check` without CI or freeze-gate breakage. Applied in hm1h3l (A.2, A.3, A.6, 2.5e, B.2, D.1, rule 20), 8mabmu (E-03, E-06, E-07) and qs00nc (E-01, E-04, E-06). Previously: Escalated as 1f4faf OQ-03 (`- Blocking: yes`, `- Finding: PR-006`). Needs a maintainer decision on what guarantee the model-free gates make; the answer amends hm1h3l (rule 19, 2.5d) and qs00nc (E-04, V-04). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Who owns the five-surface ONE PREDICATE parity check? | `wytlly` (new E-05) | a new Order 14 child; qs00nc (too early, the other surfaces do not exist yet); leave on parent | wytlly already owns the cross-child end-to-end measurement and depends on every surface; AGENTS.md "ADD A CHILD ... do NOT delete" | yes |
| D-2 | Should 52opph skip its own Set? | Measure but never demote Set `gradcover`; stop and report if `1f4faf` fails | demote it like the rest; skip measuring it | demoting a mid-execution Set strands 10 to 13 and the parent; reporting keeps the human in the loop | yes |
| D-3 | Fix the missing edges by adding dependencies or by reordering? | Add `executed:26m1nb` to 52opph and `executed:5etev3` to wytlly | renumber Orders | runner sorts by dependency depth (`runner_shared.queue_sort_key`); adding edges is the minimal correct change | yes |
