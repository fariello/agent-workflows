- Id: 4vh5nb
- Status: graduated
- Graduated-To: histresid
- Set: setterguard
- Priority: low
- Work-Kind: chore
- Summary: aw specs set and aw specs migrate write history without deduplicating an identical same-status re-assertion, so the x6tk1u dedup rule plan vhbvwz added to status_set does not cover the specs.py fork

## Workflow history
- 2026-09-23 graduated (aw set): Graduated to IPD 7jqev2 (histresid Order 01) E-04. Verified by source inspection that specs._append_history carries no dedup logic, so an identical same-status re-assertion appends a duplicate round. E-04 requires SHARING the x6tk1u backlog-side rule rather than forking a second predicate.
- 2026-09-22 created (aw backlog): FOUND while executing plan vhbvwz E-01. The dedup rule that keeps an idempotent re-assertion from appending a duplicate history record (status_set.same_status_message_is_duplicate) was installed in status_set.apply_status_change, which is the route the POSITIONAL spelling 'aw specs set <status> <selector>' takes. The '--status' spelling routes to specs.run_set instead (the dual dispatch is documented at the bottom of specs.py and in cli.py), and that fork calls specs._append_history unconditionally, so a repeated identical 'aw specs set <path> --status <same-status> --message <same message>' appends one record per call. NOT A REGRESSION, and that is why this is a chore rather than a bug: specs.run_set only reaches _append_history after its own transition checks, and the duplicate-growth path plan vhbvwz measured in production is the RUNNER one (oc_runipd/agy_runipd calling set_plan_approved with the constant FULL_AUTO_APPROVAL_MESSAGE), which is a PLAN transition and therefore goes through status_set where the rule now lives. No runner calls the specs --status spelling in a loop. Filed so the asymmetry is recorded rather than rediscovered: the same-gate-in-both-forks reasoning that specs.py itself documents twice ('a gate in only one of them is bypassed by choosing the other') argues for consuming the shared predicate here too.
