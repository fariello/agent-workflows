# Benchmark

The benchmark measures agent behavior against a seeded corpus with hidden ground truth and sets
the release bar with a threshold policy. The modules are `agent_workflows/benchmark_corpus.py`,
`benchmark_metrics.py`, `benchmark_scorer.py`, `benchmark_thresholds.py`, and
`benchmark_reports.py`.

## The seeded corpus

The corpus represents seven agent-behavior task classes: simple_commands,
interactive_planning, complex_review, multi_step_implementation, migration, failure_recovery,
and orchestration. Each seed carries a hidden `ground_truth.json` beside the executor-visible
`workspace`; the ground truth is NEVER exposed to the executor. `is_ground_truth_accessible`
fails a workspace that leaked the answer.

## Release thresholds (generated from the threshold policy)

The table below is generated from `benchmark_thresholds.ThresholdPolicy` (see
`agent_workflows/docs_render.render_benchmark_thresholds_table`). The two non-negotiable
invariants are visible: max critical escapes is 0 and min evidence validity is 1.0 for every
risk class. A threshold revision that would violate an invariant is rejected unless it is
human-signed, and even then the invariant itself cannot be relaxed.

| Risk class | Min requirement recall | Min task correctness | Min test integrity | Max critical escapes | Min evidence validity |
|---|---|---|---|---|---|
| destructive_gated | 1.0 | 1.0 | 1.0 | 0 | 1.0 |
| high | 1.0 | 0.95 | 1.0 | 0 | 1.0 |
| low | 0.9 | 0.85 | 1.0 | 0 | 1.0 |
| medium | 0.95 | 0.9 | 1.0 | 0 | 1.0 |

To render the current table (with the as-of date and provenance line):

```
python3 -c "from agent_workflows import docs_render as d; print(d.render_benchmark_thresholds_table())"
```

## The release gate

`evaluate_release_gate` checks a run's metrics against the thresholds for its risk class. The
first non-negotiable check is zero critical seeded escapes; the second is 100% evidence
validity. A gate that fails either is a release blocker.

## Responsibility boundary

The corpus and the scorer decide the numbers. The threshold policy decides the bar. A human
signature is required to revise a threshold, and no revision can relax the two invariants.

## Limitations

- A benchmark result is scoped to a specific corpus, host, and version. It is a default observed
  under those conditions, not a universal quality claim (see [model-profiles.md](model-profiles.md)).
- A combination that has not been measured is reported as pending, not asserted.
