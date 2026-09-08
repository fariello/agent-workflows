- Id: 0k74my
- Status: open
- Set: actmodel
- Priority: medium
- Work-Kind: feature
- Summary: no per-action model selection: the runner resolves ONE model identity for a whole run, so a cheap action like the orchestrator probe cannot choose a cheap model, and kgpptv covers only the verifier role

## Workflow history
- 2026-09-07 created (aw backlog): no per-action model selection: the runner resolves ONE model identity for a whole run, so a cheap action like the orchestrator probe cannot choose a cheap model, and kgpptv covers only the verifier role

DECIDED 2026-09-07 (maintainer, while resolving `m7gvuz` OQ-01): filed as a BACKLOG ITEM rather than
an IPD, because it is a decided-but-unscoped design question, not a task list. It graduates into a
plan if and when it earns one.

THE GAP, measured 2026-09-07. The runner resolves ONE model identity for an entire run:

- `runner_profiles` contains no `role` concept at all.
- `resolve_launch_profile` (`oc_runipd.py:2660`) resolves a single launch identity for the whole run.
- Both the executor turn and the verifier turn read one shared `options["model"]`.

So there is no way to say "this action uses a cheap model, that action uses a strong one".

WHY IT SURFACED. Plan `m7gvuz` adds a pre-run probe that asks a model one yes/no question per queued
orchestrator. Paying a top-tier rate for a yes/no question is wasteful, but the probe cannot choose a
cheaper model without machinery that does not exist. The ruling was to use the run's already-resolved
model and RECORD which model answered with each cached verdict, so a future reader can distrust a
verdict produced by a weak model.

WHY `kgpptv` DOES NOT COVER THIS. `kgpptv` (approved, unexecuted) gives the VERIFIER TURN its own
resolved profile. That is one specific role, not a general mechanism, so an arbitrary new action such
as the orchestrator probe still has nowhere to declare a model preference. A general capability would
likely SUBSUME `kgpptv`, which is worth considering before executing it.

WHAT A SOLUTION WOULD NEED TO DECIDE:

1. What is the unit a model attaches to: a ROLE (executor, verifier, reviewer, probe), or an
   arbitrary named ACTION? A role vocabulary is smaller and easier to validate; an action vocabulary
   does not need extending every time a new action appears.
2. Where the preference is declared: the user-local runner profile config, a per-run flag, or both
   with a documented precedence. Note `f2mrsw` already established a per-profile `validate`
   tri-state, so a precedence chain convention exists to follow rather than invent.
3. What happens when a preference names a model the host cannot provide: refuse the run, or fall back
   to the run's model with a warning. Failing closed on a MODEL CHOICE is probably wrong, since the
   work can still be done, just more expensively.
4. Whether a cached artifact produced under model A stays valid when the preference changes to model
   B. The probe verdict store already records the answering model for exactly this reason, so the
   data to make that judgment exists.

COST BOUND THAT MAKES THIS NON-URGENT. Probe verdicts are cached against a content digest, so on a
stable corpus the probe costs nothing after its first pass. The waste is bounded by how often plans
change, not by how often runs happen. That is why this is filed rather than built.

RELATED: `kgpptv` (verifier-specific profile, approved and unexecuted), `f2mrsw` (per-profile
`validate` tri-state, executed), `m7gvuz` (the probe whose OQ-01 raised this).
