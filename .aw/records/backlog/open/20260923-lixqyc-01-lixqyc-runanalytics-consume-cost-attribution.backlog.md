- Id: lixqyc
- Status: open
- Set: lixqyc
- Priority: medium
- Work-Kind: followup
- Summary: run_analytics facts read only options.model and so cannot yet see the new per-run cost_attribution model and rate card

## Workflow history
- 2026-09-23 created (aw backlog): Found while executing w33lrl. That plan is the PRODUCER of options.cost_attribution (resolved model identity, model_source, and the launch-time rate card with its own config digest) and the runanalytics Set is the declared CONSUMER, but all three consumer plans (5f2h8i, 8hald1, aflsz3) had already EXECUTED, so nothing reads the new field: run_analytics._model_of reads only state['options']['model'], which is null on every run where no --model was passed. Consequence: a forward run now RECORDS an attributable model and card, and the fact schema still reports model='' for it, so run_analytics_query's own near-absent-model-coverage caveat stays triggered for runs that no longer deserve it. The field name and unit are pinned as a contract (runner_shared.COST_ATTRIBUTION_KEY = 'cost_attribution', oc_models.CARD_UNIT = '$/Mtok'); the follow-up is to bind Fact.model to it (falling back to options.model), and to bind the verifier phase's model to the conditional verify_cost_attribution rather than the executor's. Scope note: this is a CONSUMER change and deliberately out of w33lrl's fence, which forbids touching any aw runs view or adding a cost recomputation.
