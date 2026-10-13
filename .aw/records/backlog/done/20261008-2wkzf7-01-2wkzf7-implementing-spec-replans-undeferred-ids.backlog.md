- Id: 2wkzf7
- Status: done
- Graduated-To: 2wkzf7
- Set: 2wkzf7
- Priority: medium
- Work-Kind: feature
- Summary: Give an implementing spec with uncited non-deferred requirement ids a plan-writing turn before running its children

## Workflow history
- 2026-10-13 done (aw backlog): closed by aw agy run: IPD 2hgxi1 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261012-2wkzf7-01-2hgxi1-give-an-implementing-spec-with-uncited-non-deferred-trace-id.ipd.md); evidence .aw/records/plans/executed/20261012-2wkzf7-01-2hgxi1-give-an-implementing-spec-with-uncited-non-deferred-trace-id.ipd.md
- 2026-10-12 graduated (aw backlog): graduated by run run-20261012T005650Z-2322198: 2hgxi1
- 2026-10-09 created (aw backlog): Give an implementing spec with uncited non-deferred requirement ids a plan-writing turn before running its children

Maintainer decision 2026-10-08 (spec 89xjll OQ-08): a spec planned in stages stays implementing between stages. When the runner dispatches an implementing spec that declares a mandatory, non-[Deferred] TRACE id cited by no pooled From-Spec plan (89xjll 6.1), it should run a plan-writing turn checked by SPEC-PLAN-TRACE over the pooled set before dispatching child plans; otherwise dispatch children as today. Requires amending spec 25kzda's implementing dispatch rule (run_selection_policy._SPEC_ACTIONS comment: implementing dispatches its From-Spec children) and depends on rtvdak's requirement-id parser. Stopgap until shipped: human steps the spec implementing -> approved with --by-human. Grandfathered specs declare no TRACE ids, so their dispatch must be unchanged.
