# Plan Review Compression and Modularity Assessment

## Recommendation

Use the modular version for installed workflows and keep the compact single
file as the portable fallback.

The compact file is about half the size of the prior 780-line revision while
retaining the core control flow, Fix Bar, rubric, interactive decisions,
commit safety, verdict/readiness distinction, and deterministic report.

The modular version improves execution reliability when the agent loads each
step only when active.

## Does splitting help context rot and directive drift?

Yes, under specific conditions.

It helps because:

- The active step is shorter and more salient.
- The agent does not carry the full rubric and final template during discovery.
- Each phase can re-read its instructions immediately before acting.
- Exit gates create a forcing function before moving forward.
- The orchestrator can repeat the small set of global non-negotiable rules.
- A fresh or compacted session can resume from the active step without loading
  the entire workflow history.

It does not help automatically.

Splitting can make reliability worse when:

- The agent reads every file up front anyway.
- Critical global rules exist only in one early file.
- Step files duplicate or contradict each other.
- There are too many tiny files and cross-references.
- The orchestrator does not specify loading order and exit gates.
- The agent is allowed to proceed from memory instead of re-reading the active
  step.

## Recommended structure

```text
plan-review/
  plan-review.md
  01-discover-and-snapshot.md
  02-review-and-revise.md
  03-resolve-and-finalize.md
  review-rubric.md
  report-template.md
```

`plan-review.md` is the controlling orchestrator. It contains only:

- the memory kernel;
- the boundary;
- ordered step execution;
- context-loading rules;
- global stop conditions;
- completion requirements.

The detailed rubric is loaded only during review. The final report template is
loaded only during finalization.

## Why three step files

Three is a useful balance:

1. Discover and snapshot.
2. Review and revise.
3. Resolve, finalize, and report.

More files would fragment the workflow without a clear attention benefit.
Fewer files would keep the largest and most failure-prone phases mixed.

## Salience pattern

At each step the agent should assemble context in this order:

1. Orchestrator memory kernel.
2. Current project evidence and state.
3. Supporting rubric or template, if required.
4. Active step file and exit gate last.

This places the active instructions at the freshest end of context while
keeping global invariants visible at the front.

## Trade-offs

### Advantages

- Lower active instruction load.
- Better recovery after context compaction or model handoff.
- Easier testing and revision of one phase.
- Less chance that the detailed rubric hides the interactive or reporting
  requirements.
- Easier use by Flash-class or smaller models.

### Costs

- More installed files.
- A missing or stale module can break the workflow.
- Cross-file consistency must be maintained.
- Some agents may ignore the instruction to load files just in time.

Mitigate these costs with a manifest, version field, installer integrity check,
and tests that verify every referenced file exists.

## Suggested deployment policy

- Install the modular workflow by default.
- Keep `plan-review.compact.md` as a standalone fallback for copying into a
  single prompt or environment that cannot load sibling files.
- Do not maintain the compact and modular versions manually as independent
  sources. Generate one from a canonical source or test them for semantic
  parity.
- Add a workflow self-check that verifies referenced files, headings, verdicts,
  decision values, and final-output constraints.
