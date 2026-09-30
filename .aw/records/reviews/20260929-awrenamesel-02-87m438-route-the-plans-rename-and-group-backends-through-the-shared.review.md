# Review findings: plan 87m438

- Subject-Id: 87m438
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `90965f0f` in a lane worktree. Structural preflight `aw ipd lint --phase author --agent`
CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent` conforms after.
`IPD-S407` does not apply: the plan's own first `- Kind:` bullet reads `child`. No pre-review snapshot was
owed: `git status --porcelain` was empty at review start.

NO PRODUCTION FILE WAS MODIFIED BY THIS REVIEW. Every measurement was an in-process `cli.main` call under
`redirect_stdout`, a direct library call, or a read. No `--apply` was ever passed, so no file on disk was
renamed. The only writes were to this plan and this record.

THIS IS AN EXCEPTIONALLY WELL-MEASURED PLAN AND ITS DIAGNOSIS IS CORRECT THROUGHOUT. It corrects its own
backlog item in four places rather than transcribing it, it identifies the naive-fix corruption trap that is
the real hazard in the obvious implementation, and it sequences itself behind a sibling for a measured
security reason. I re-derived all fourteen findings. ALL CONFIRMED:

- **F-01/F-02/F-03.** `aw rename plans <filename> --to-id6` and `aw group plans <filename> --set zz` both
  exit 2 with `error: no plan has Id '<filename>'`; `aw rename plans 7qx7ys --to-id6` exits 0 and previews
  `20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd.md`; `aw find plans <the same filename>
  --paths` exits 0 and prints the path. `plans_refs.run_mv` and `plans_refs.plan_set_assign` both call
  `_find_plan_by_id`, an exact `- Id:` equality scan over `plans_dir.rglob("*.md")` with no shape guard.
- **F-04, the corruption trap.** `clustered_name(date='20260808', set_id='plans-adopter', order=6,
  id6='20260808-0004-06-migrate-existing-plans.ipd.md', slug='migrate-existing-plans',
  artifact_type='ipd')` returns
  `20260808-plans-adopter-06-20260808-0004-06-migrate-existing-plans.ipd.md-migrate-existing-plans.ipd.md`.
  `run_mv` really does pass `id6=id6` where `id6 = getattr(args,"id","")`.
- **F-05, the sequencing premise.** `resolve_for_mutation(repo,'plans',<a spec path>)` returns the SPEC with
  `err=None`. `status_set.match_selector`'s docstring independently confirms the mechanism and names the
  `Type mismatch` refusal as "the only guard on this case". `eby93o` is `reviewed`/`go-pending-approval`, so
  the declared `Item-Dependencies: executed:eby93o` is live and correctly ordered.
- **F-06.** `tests/test_group_verb_policy.py` has the four parametrized cases; three assert
  `"zzzzzz" in out` and `test_group_setid_refusal` asserts `"zzzzzz" not in out`.
- **F-07/F-08.** `check_engine._identity_rename_hint`'s docstring carries the quoted rationale verbatim.
  Zero plans lack a `- Id:`.
- **F-09.** Selector kinds resolve as claimed: `id6` n=1, `substring` (filename) n=1, `substring` (stem)
  n=1, `path` n=1, `setid` n=4.
- **F-10, the load-bearing equality.** Both enumerations yield the SAME set, symmetric difference empty in
  both directions.
- **F-11.** `set_id = getattr(args,"set",None) or existing_terse or id6` is present as quoted.
- **F-12.** `aw rename plans 7qx7ys` and `... --to-id6` produce byte-identical output; `to_id6` occurs zero
  times in `plans_refs.py`.
- **F-14.** No test passes a plan filename or path to `rename`/`group`.
- **Both argparse claims.** `--yes` exits 2 with `unrecognized arguments: --yes`;
  `--no-interactive rename plans 7qx7ys` exits 0.
- **The spec citations.** `z7nbn1` 1.1 contains "There is ONE universal artifact selector" and "A selector
  that resolves for one verb MUST resolve identically for every other verb" as quoted, and it is
  `Status: implementing`. `2lcqno` is `approved` and its N2/N3 read as cited.

THE ONE THING THE PLAN MISSED IS THE ONE THAT COULD HAVE LOST WORK. See PR-201. Everything else I changed is
housekeeping by comparison.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | UNDER-SCOPE | A (correctness/data integrity); D (anti-regression); F (prevent silent failure) | `selectors.resolve_for_mutation` (setid branch returns `list(res.paths), None`); `plans_refs.run_mv`; `artifact_rename.run_rename_generic`'s `if len(paths) > 1 and not force:` guard; measured `resolve_for_mutation(repo,'plans','awrenamesel')` -> 5 paths, `err=None`, `paths[0]` = the Order-00 orchestrator | **THE PLAN SETTLED SETID EXPANSION FOR `group` AND NOWHERE FOR `rename`, WHILE PROMISING `rename` WOULD ACCEPT A SETID, WHICH WOULD SHIP A SILENT ARBITRARY RENAME.** `resolve_for_mutation` returns a setid multi-match as a deliberate SUCCESS (`err=None`, N paths, documented "act on ALL members"), but `run_mv` renames exactly ONE file and would consume `paths[0]`. So `aw rename plans <a multi-plan setid> --apply` would rename one arbitrary Set member and exit 0. That is strictly WORSE than the defect being fixed, which at least refuses loudly. OQ-04 covered the `group` side; E-03's Expected outcome nonetheless read "accepts filename, stem, path, id6 and setid". The generic engine already solved this and RECORDS why in a code comment; `aw rename` already advertises `--force` while `plans_refs` reads it nowhere. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (the remedy is copying a shipped sibling's guard verbatim in shape) | FIXED | E-03 now mandates the refuse-unless-`--force` guard and threading `force`; its Expected outcome is corrected; OQ-05 records the decision with the rejected alternatives; E-06 gains guard (f); V-03 names it as a gate; V-06 requires the refusal plus proof no file was renamed; the Required-tests list and the gate both carry it as a THIRD mandatory evidence gate. Recorded as F-15. |
| PR-202 | LOW | IN-SCOPE | E (testing); G (executability) | `tests/test_doctor.py` `test_remediation_name_nonconformant` (asserts `"aw rename plans .aw/records/plans/pending"` NOT in the hint) and `test_remediation_setid_collision` (asserts `"aw group plans 6k7xot"` in the hint) | E-05's reconciliation list named four pre-existing tests; a FIFTH file also reads the plans rename/group hint surface. Both cases assert hint TEXT built by `check_engine`/`doctor`, which this plan leaves byte-unchanged, so they should pass; unnamed, an executor seeing one fail would not know whether it is in the fence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now also checks them and states they are out-of-fence-report-only; the Required-tests list and the negative fence proof both add `tests/test_doctor.py`. Recorded as F-17. |
| PR-203 | LOW | IN-SCOPE | G (live-artifact criteria) | re-measured: 1035 plans (not 919), `3291 passed, 2 skipped` (not `3246`), `findtier` setid n=4 (not n=3) | Three authored counts have already drifted in the days since authoring. The plan correctly marks F-13 as "not a bar" but states F-08's `919` and F-09's `n=3` as bare facts, and E-03 repeats "ZERO of 919". The load-bearing PROPERTIES (set equality; zero plans lacking an id6) are unchanged, but a criterion counting live artifacts must require re-derivation rather than pinning a measured number. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now states the bar is "the zero, not the denominator" and gives both measurements; new F-16 records every drifted count with the re-measured value and reaffirms the properties. |
| PR-204 | LOW | UNDER-SCOPE | D (domain invariants); documentation sync | approved spec `2lcqno` N3: scoped resolution is type-safe "EXCEPT a direct PATH ... That refusal must be PINNED, never retired as dead code" | E-06(e) (the foreign-type-path refusal) is not merely prudent, it discharges a named obligation in an APPROVED spec. The plan's spec-sync section cites `2lcqno` N2 and N3's type-scoping half but not the documented hole and its pinning requirement, which is precisely what E-06(e) tests. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06(e) now names the spec obligation, so an executor cannot read that guard as optional. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | What should `aw rename plans <a setid matching several plans>` do once the resolver is widened? | Refuse with the candidate list unless `--force`, copying `artifact_rename.run_rename_generic`'s shape | (a) Rename `paths[0]` silently, REJECTED as data loss dressed as success: measured, 5 paths with `err=None` and `paths[0]` is the Order-00 orchestrator, so `--apply` would rename an arbitrary Set member at exit 0. (b) Always refuse a multi-match with no escape, REJECTED because it would make `plans` behave DIFFERENTLY from the seven types routed through the generic engine, which is the very inconsistency this plan exists to remove, and it would strand an operator who legitimately wants the documented first-match behavior | `artifact_rename.run_rename_generic` already implements refuse-unless-`--force` and its comment states the reasoning ("a setid selecting several is unusual for rename and, absent `--force`, also refuses rather than silently renaming an arbitrary member"); `aw rename --help` advertises `--force` while `grep force agent_workflows/plans_refs.py` finds no read of it. Adopting the sibling's answer is what makes the plan's own consistency premise true for this case | yes |
| D-2 | Do the drifted population counts (919 -> 1035, 3246 -> 3291, n=3 -> n=4) invalidate any finding or change the plan's scope? | No. Record them as drift; reaffirm the properties; require re-derivation | (a) Treat the drift as a stale-evidence finding against the plan, REJECTED: the plan explicitly warns its own executor that F-13's count drifts and to re-measure, so it already holds the right position; only F-08/F-09's bare numbers needed the same treatment. (b) Re-state the new numbers as the bar, REJECTED because that repeats the original mistake one commit later | Re-measured every one at review: set equality still exact (symmetric difference empty both directions), plans lacking `- Id:` still ZERO, suite still green. The PROPERTIES are what the plan's reasoning rests on and none moved | yes |
| D-3 | `eby93o` is `reviewed`, not `executed`, while this plan declares `Item-Dependencies: executed:eby93o`. Does that block this review or the plan's readiness? | No. It is the correct declaration and the runner enforces it at dispatch | (a) Flag the unmet edge as a finding, REJECTED: the dependency is DELIBERATE and the AGENTS.md runner contract states dependencies are re-checked at dispatch, with an unmet edge marking that item `dependency-blocked` and continuing, so the ordering is already guaranteed without a review finding. (b) Recommend NO-GO until `eby93o` executes, REJECTED: readiness concerns whether the PLAN is sound, and both plans are independently reviewed and awaiting the same approval | Both Order 00 (`95jk4s`) and Order 01 (`eby93o`) are already `reviewed` with `go-pending-approval`; the queue sorts by dependency depth first, so `eby93o` precedes `87m438` mechanically | yes |
| D-4 | E-05 must predict whether the four pinned `zzzzzz` assertions survive the message change. Should that be left for the executor to discover? | No. Measure it at review and record the expected answer, while still requiring the executor to confirm | (a) Leave it open, REJECTED: the plan already says "VERIFY rather than assume", and a reviewer who can cheaply settle the premise should, so the executor is not left to discover a test-reconciliation task mid-execution. (b) Declare it settled and drop the verification, REJECTED because the executor's tree is not this tree and the assertion set could change | Measured `resolve_for_mutation(<fresh git repo>,'plans','zzzzzz')` -> exactly `no plans artifact matched 'zzzzzz'`, which contains `zzzzzz`, so the three positive assertions and the one negative assertion are all expected to pass unchanged | yes |

No `Reversible: no` decision was taken, so no escalation is owed. PR-201 is HIGH but was FIXED, not left
`OPEN` or `DEFERRED`, so no `- Blocking: yes` escalation is owed under the gate-threshold rule.
