# Model profiles

A model profile is an EVIDENCE-BACKED default, not a universal personality or quality claim. This
document explains the distinction the system enforces and how the profile table is rendered.

## Model ID is distinct from the profile

Two different things are often conflated:

- The MODEL ID identifies which model runs (chosen by the operator or the host).
- The PROFILE tunes only TRANSPORT knobs: packet size, output format, and an evidence-backed
  reasoning tier (`low`, `medium`, `high`, `max`). A profile never changes the model identity,
  the workflow semantics, the MUST requirements, or the scope fence.

The profile table renders them in separate columns on purpose (see
`agent_workflows/docs_render.render_model_profile_table`). The reasoning tier is
evidence-backed: the benchmark justifies raising it, and a profile that sets a disallowed key is
rejected (`workflow_profile.validate_profile`).

## What the table records

Every model-profile table carries its provenance so a reader can see it is a default observed
under specific conditions, not a general guarantee:

- Benchmark date.
- Task corpus (the seven classes; see [benchmark.md](benchmark.md)).
- Host and version the evidence came from.
- Measurement uncertainty.
- Pending combinations that have not been measured (listed, not asserted).

Render an example table:

```
python3 -c "from agent_workflows import docs_render as d; \
print(d.render_model_profile_table([{'model_id':'(operator-selected)','profile':{'name':'default','reasoning_level':'medium'},'notes':'baseline'}], benchmark_date='(date)', host='(host)', host_version='(version)', uncertainty='(range)', pending_combinations=['(combo not yet measured)']))"
```

## What the documentation will not do

No document turns vendor marketing, or a single observed rollout, into a general quality
guarantee. A model performs a certain way on a specific corpus and host; that is the claim, and
nothing wider.

## Responsibility boundary

The benchmark produces the numbers. The profile carries the transport tier. The operator picks
the model. The documentation renders the evidence and states its scope.

## Limitations

- A default observed on one corpus and host does not transfer to a different corpus, host, or
  version. Unmeasured combinations are pending.
