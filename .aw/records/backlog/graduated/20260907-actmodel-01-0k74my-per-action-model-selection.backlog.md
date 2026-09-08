- Id: 0k74my
- Status: graduated
- Set: actmodel
- Priority: medium
- Work-Kind: feature
- Summary: no per-action model selection: the runner resolves ONE model identity for a whole run, so a cheap action like the orchestrator probe cannot choose a cheap model, and kgpptv covers only the verifier role

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan btot17 (actmodel-01) as a DECISION plan, which is what this item asks for ('a decided-but-unscoped design question, not a task list'). Gap re-verified by symbol: runner_profiles still has ZERO role occurrences and resolve_launch_profile still resolves one identity per run, but it MOVED from the item's cited :2660 to oc_runipd.py:2702 (42-line drift). ONE PREMISE IS NOW FALSE and changes the design space: this item and kgpptv both treat the profile mechanism as opencode-only, but approved tm2cz8 registers the agy host and ybkmzp warns explicitly that kgpptv's F-12 'child 01 makes false, so its scope should be re-read rather than trusted', so a per-action design must be cross-host from the outset. The plan keeps question 1 (role versus arbitrary action) BLOCKING because its answer decides whether APPROVED plan kgpptv is executed, re-scoped or retired, and an agent choosing the unit would settle that by implication. Questions 2, 3 and 4 are RESOLVED from existing precedent: question 2 follows f2mrsw's per-profile precedence chain; question 3 answers warn-and-fall-back, with the plan recording why the nearby sandbox precedent (select_execution_profile RAISES) must not be applied by analogy, since degradation there removes a security boundary while a model fallback only costs money; question 4 answers keep-and-record, anchored to the maintainer's existing m7gvuz ruling, while requiring the executor to verify the answering-model record actually exists since 8tgg6g is unexecuted. 'Record the decision and build nothing yet' is an explicitly legitimate outcome, since the motivating consumer m7gvuz is itself unexecuted and the cost is bounded by content-digest caching. No Blocks-Release on the item, so none inherited.
- 2026-09-07 created (aw backlog): no per-action model selection: the runner resolves ONE model identity for a whole run, so a cheap action like the orchestrator probe cannot choose a cheap model, and kgpptv covers only the verifier role

GRADUATED 2026-09-08 to plan `btot17` (`actmodel-01`), authored as a DECISION plan because that is what
this item asks for. NOTHING IS OBSOLETE; the gap is real and was re-verified by symbol. But TWO things moved.

ONE CITATION IS STALE: `resolve_launch_profile` is at `oc_runipd.py:2702`, not the `:2660` recorded below,
a 42-line drift. The substance holds and was re-measured: `runner_profiles` still contains ZERO `role`
occurrences, and that function still resolves ONE launch identity for the whole run.

ONE PREMISE IS NOW FALSE, AND IT CHANGES THE DESIGN SPACE. This item and `kgpptv` both treat the profile
mechanism as opencode-only. Approved plan `tm2cz8` (`hostdefault-01`) registers the AGY host in
`runner_profiles.RUNNER_REGISTRY`, and `ybkmzp`'s Deferred section says so explicitly: "NOTE for whoever
executes `kgpptv`: it was authored believing the profile mechanism is oc-only (its F-12), which child 01
makes false, so its scope should be re-read rather than trusted." So a per-action mechanism designed now
must be CROSS-HOST from the outset, not oc-shaped.

WHAT THE PLAN DOES AND DELIBERATELY DOES NOT DO. It carries question 1 (role versus arbitrary action) as a
BLOCKING open question, because the answer decides whether APPROVED plan `kgpptv` should be executed,
re-scoped or retired, and an agent choosing the unit would settle that by implication. It RESOLVES questions
2 and 3 from existing precedent rather than leaving them open: question 2 follows `f2mrsw`'s established
per-profile precedence chain, and question 3 answers warn-and-fall-back, with the plan explicitly recording
WHY the nearby sandbox precedent (`select_execution_profile` RAISES rather than degrading) must NOT be
applied by analogy: degradation there removes a security boundary, while a model fallback removes no
boundary and merely costs money. It resolves question 4 as keep-and-record, anchored to the maintainer's
existing `m7gvuz` ruling, while requiring the executor to VERIFY that the answering-model record actually
exists yet, since `8tgg6g` is unexecuted.

"RECORD THE DECISION AND BUILD NOTHING YET" IS AN EXPLICITLY LEGITIMATE OUTCOME of that plan, and the cost
bound recorded below is why: verdicts are cached against a content digest, so waste scales with plan churn
rather than run count. Note also that the motivating consumer is PROSPECTIVE, since `m7gvuz` is unexecuted
and carries its own blocking questions; if it never executes, this item loses its motivating case.

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
