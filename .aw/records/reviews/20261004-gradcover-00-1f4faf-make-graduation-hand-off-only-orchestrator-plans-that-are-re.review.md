# Review findings: plan 1f4faf

- Subject-Id: 1f4faf
- Subject-Type: ipd
- Reviewed-At: 2026-10-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (LOW, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (HIGH, fixed), PR-005 (MEDIUM, fixed), PR-006 (HIGH, fixed), PR-007 (MEDIUM, fixed), PR-008 (LOW, fixed), PR-009 (LOW, fixed), PR-010 (LOW, fixed)

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

## Round 2

Re-review in isolated lane `review-sweep-run-20261006T040814Z-944` at HEAD `318b47f25`, after the
2026-10-04 maintainer ruling (coverage answer stored in the plan, `25kzda` 2.5e) and the revision of
every affected child. The target plan was committed and byte-identical to the sealed lane input, so
no pre-review snapshot was needed. `aw ipd lint --phase author --agent` and `--phase review-finalize
--agent` were both `clean` (exit 0) before and after revision; no `IPD-S407` finding, so the bounded
repair loop did not run. OQ-03 now reads `Blocking: no`, `Status: resolved`, `Owner: maintainer`,
which confirms round 1's PR-006 as fixed.

Re-measured: all 13 children exist in `pending/`; every child's `- Item-Dependencies:` matches the
child table (including the round-1 edges `52opph` -> `26m1nb` and `wytlly` -> `5etev3`); release
`f33nrj` reads `- Status: planned`; every child carries `- From-Spec: none`; `wytlly` E-05 owns the
five-surface ONE PREDICATE parity check; `52opph` E-01/E-02 exclude Set `gradcover` from demotion;
`ipd_lifecycle._LEGAL_BACKWARD_EDGES` still holds only three edges (so Order 05 is required before
Order 09, as declared); `runner_shared.enforce_freeze_time_refusal` lints approved IPDs at
`pre-execution` (`checkpoint = ("pre-execution" if status in ("approved", "auto-approved") else
"author")`). Every Completion criterion names an owning child, and every Cross-IPD bullet either names
an owner or is a constraint on children.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-007 | MEDIUM | UNDER-SCOPE | C (operability, self-gating) | `agent_workflows/runner_shared.py` `enforce_freeze_time_refusal` (the `checkpoint = ("pre-execution" ...` line); qs00nc E-04 "An ABSENT or OUT-OF-DATE coverage record is an ERROR at `review-finalize` and `pre-execution`"; qs00nc E-06 rule over `approved` orchestrators | Once Order 03 lands, this orchestrator is itself a pending orchestrator with no coverage record, so `aw check plans` flags it and any NEW run over the approved Set (a resume, or a second `aw oc run gradcover`) is refused whole at freeze time until a record exists. The plan was silent on this window, which an operator resuming mid-Set would hit. Not uncovered work: the remedy is an existing operator command, Order 09 records the answer, and Order 04's retirement re-check asks if none exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a Cross-IPD bullet "THIS SET BECOMES SUBJECT TO ITS OWN GATE MID-EXECUTION" naming the refusal, its remedy `aw ipd coverage 1f4faf`, and the owning children (`52opph`, `5etev3`). |
| PR-008 | LOW | IN-SCOPE | G (evidence accuracy) | 1f4faf Concern point (4); `axozpe` `## Scope check` names only "Order 04"; `axozpe` `## Required tests / validation` "which Order 04 carries as the last child"; `axozpe` child table row `04 \| rlhmt9` | Concern said `axozpe` names `rlhmt9` in its `Scope check`; the round-1 history line already corrected this but the Concern text was never swept. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern now says `axozpe`'s `Required tests / validation` assigns the final measurement to Order 04, which its own child table resolves to `rlhmt9`. |
| PR-009 | LOW | IN-SCOPE | G (consistency) | 1f4faf Scope "the four spec amendments (Order 01)" and Completion criterion 10; child table row 01 and hm1h3l Scope "Edit exactly five spec files" | Count mismatch: Order 01 edits five specs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both places now say five specs. |
| PR-010 | LOW | IN-SCOPE | E (evidence feasibility) | 1f4faf V-01..V-13 "paste `grep -n '^- Status:' <plan>`"; each child carries `- Status: resolved` lines under `## Open questions` (e.g. hm1h3l lines 279, 286, 293) | The demanded grep returns the open-question `Status:` lines as well as the plan status, so the pasted evidence would be ambiguous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All 13 V-items now demand `grep -m1 -n '^- Status:'`, which returns only the front-matter status. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-4 | Does the self-gating window need a new child, a parent step, or a stated note? | A Cross-IPD note naming the refusal, its remedy and the owning children | a new child that records `1f4faf`'s coverage right after Order 03; a parent E-item; reordering Order 09 earlier | the remedy is an existing operator command and the durable record is already owned by `52opph`; a parent step would be uncovered work (AGENTS.md "AN ORCHESTRATOR HOLDS ORCHESTRATION"); reordering breaks the declared Order 08/05 dependencies | yes |
