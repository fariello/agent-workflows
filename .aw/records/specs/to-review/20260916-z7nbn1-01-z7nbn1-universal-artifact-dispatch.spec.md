# Spec: Universal artifact dispatch: one selector, one action table, one conformance gate for every runner and reader

- Date: 2026-09-16
- Status: to-review
- Blocks-Release: next
- Id: z7nbn1
- Author: opencode/its_direct-pt3-claude-opus-5 (dictated by the maintainer 2026-09-16)
- Work-Kind: feature
- Scope: Every tool that looks at or acts on artifacts resolves them through one selector, decides what to do through one action table, and refuses clearly on anything it cannot classify; executing a spec or backlog item PRODUCES plans or backlog items rather than doing work itself.

## Workflow history
- 2026-09-25 note (aw specs): AMENDED 2026-09-25 (statusvocab 9x7otz / cyamvi): canonical terminal status vocabulary updated (fail-depend, fail-merge, fail-gate, fail-verify, fail-begin, fail-lane, not-run, interrupted). Legacy terminal status tokens (including dependency-blocked, integration-blocked, merge-needs-human, merge-conflict, merge-refused, substantially-complete, failed-safely, not-attempted) remain readable forever for backward compatibility on historical run records (via TERMINAL_STATUS_ALIASES), but are no longer written by the runner.
- 2026-09-18 to-review (aw set): Carry forward Blocks-Release: next from superseded plan mng63x per maintainer ruling

- 2026-09-16 to-review (aw specs): MAINTAINER RULINGS RECORDED 2026-09-16, all three open questions resolved. OQ-01: NO FOLLOW for now; a production action REPORTS the artifacts it created and does not enqueue them, with --follow-generated becoming the opt-in same-run mechanism once implemented (the safe default, because the frozen queue is what resume reads). OQ-02: PARTIALLY IN SCOPE, the four SPEC-PLAN-* codes only, because they verify Section 3's production actions; also CORRECTED this spec's own 4.4, there are THIRTEEN such codes not eleven and they are declared in approved spec 25kzda 4.8, so they are agreed requirements never implemented rather than speculative work. OQ-03: SUPERSEDE mng63x, and its Blocks-Release: next carries forward to whatever plan graduates from this spec. Added acceptance criteria 5.5a (report-only proven by comparing the queue id set before and after) and 5.5b (gate carry tested in both directions).
## 0. Why this spec exists

`aw oc run reviews --type spec` can SELECT the specs awaiting review. Nothing can then RUN one. Plan
`mng63x` (`specdispatch-01`) captured that gap, recorded the constraints, and refused to choose a shape
because the maintainer reserved the decision ("HOW execution is implemented is something that needs
discussion; capture that fact loudly"). Its `OQ-01` is `Blocking: yes` with `Owner: maintainer`, and it
carries `- Readiness: no-go` so nothing can execute it as though the design were settled.

THIS SPEC IS THAT DECISION. The maintainer stated the target architecture on 2026-09-16. It is written
down here because it was not captured anywhere: `mng63x` records the constraints and three candidate
shapes, not a chosen one.

## 0.1 Concepts (kept distinct)

These are routinely conflated and every requirement below depends on keeping them apart.

- **ARTIFACT**: a tracked record file of a known TYPE (`plans`, `specs`, `backlog`, `prompts`,
  `releases`, `research`, `roadmaps`, `walkthroughs`, `comms`). An artifact has a stable `<id6>`, a
  `- Status:`, and a contract its type owns.
- **SELECTION**: turning what an operator typed into a concrete set of artifact FILES. A read-only act.
- **ACTION**: what a tool should DO with one selected artifact, derived from its type plus its status.
  A pure function of those two facts, never of what the caller happens to want.
- **DISPATCH**: performing that action. The only step that spends an agent turn or mutates the tree.
- **CONFORMANCE**: whether an artifact actually matches the contract its type declares, checked BEFORE
  any dispatch, so a malformed file is refused rather than handed to a handler that assumes it is well
  formed.
- **PRODUCTION**: an action whose OUTPUT is new artifacts rather than completed work. Executing a spec
  produces plans or backlog items; it does not itself do the work the spec describes.

## 1. The architecture (the maintainer's ruling)

1.1 There is ONE universal artifact selector. It resolves artifacts by type, and it is what every tool
that looks at or acts on artifacts uses: the runners, `aw attention`, the checkers, the listers, and any
future consumer. A selector that resolves for one verb MUST resolve identically for every other verb.

1.2 There is ONE action table answering "what is the next action for an artifact of this type in this
status". Every dispatcher consults it. No tool carries a second copy, and no tool infers an action from
anything other than (type, status).

1.3 A runner MUST check, before anything runs, that every selected artifact is CONFORMANT and is the
kind of thing the runner expects. A malformed or misfiled artifact is refused at selection time, not
discovered by a handler that assumed otherwise.

1.4 A runner MUST verify that declared dependencies are met OR COULD BE MET during the run, and MUST
refuse to run if any dependency is neither. The distinguishing case, stated because it is the whole
point: if `efg456` requires `abc123` to be executed and `abc123` is not yet executed BUT IS IN THE SAME
BATCH, the dependency CAN be met and the run proceeds with `abc123` ordered first. If `abc123` is absent
from the batch and not already executed, the run REFUSES.

1.5 A runner orders selected artifacts so that dependencies can be met, then iterates.

1.6 For each artifact, the runner performs the action the table gives:
  - an artifact in a review-ready status gets the review appropriate TO ITS TYPE;
  - an artifact in an executable status gets executed;
  - an artifact whose action is PRODUCTION emits new artifacts (see Section 3).

1.7 If the runner cannot determine what to do with a selected artifact, it MUST print an error that
explains the issue clearly and exit BEFORE running anything. Silently skipping it, or bucketing it into
some other action, is forbidden.

1.8 The dispatcher MAY be structured as a thin router delegating to per-type handlers, OR as one
monolithic handler. THIS IS EXPLICITLY LEFT TO THE IMPLEMENTER (maintainer: "I don't care either way").
An implementation choice here is not a spec violation.

## 2. What is already built (MEASURED at HEAD 2026-09-16, not assumed)

This section exists so no plan re-implements working machinery. Each claim carries the measurement.

2.1 THE UNIVERSAL SELECTOR EXISTS and satisfies 1.1. `agent_workflows/selectors.py` describes itself as
"the ONE selector-to-file resolver for the whole package", resolving direct path, `<id6>`, setid,
status, bare stem and filename fragment. Measured: it knows nine types (`backlog`, `comms`, `plans`,
`prompts`, `releases`, `research`, `roadmaps`, `specs`, `walkthroughs`), and thirteen modules route
through it, including `attention.py`, `cli.py`, `run_selection_policy.py`, `runner_shared.py`,
`status_set.py`, `ipd_lifecycle.py`, `reviews.py` and `artifact_audit.py`. Requirement 1.1 is therefore
largely SATISFIED TODAY; what remains is to keep it so.

2.2 THE ONE ACTION TABLE EXISTS and satisfies 1.2. `run_selection_policy._ACTION_TABLES` holds one
table per type. Measured contents:

```
ipd:      to-review->review  approved->execute  auto-approved->execute  reusable->execute
          executed->skip  superseded->skip  not-executed->skip
spec:     to-review->review  approved->plan  implemented->skip  deferred->skip
          parked->skip  superseded->skip
backlog:  open->plan  blocked->skip  parked->skip  graduated->skip  done->skip
```

2.3 THE REFUSE-CLEARLY PATH EXISTS IN PART and partially satisfies 1.7. `ACTION_UNDETERMINED` is a
first-class action, and the code comment states the intent directly: an unknown type or status maps to
`undetermined` rather than "silently bucketing an undetermined item into `skip`". What is NOT yet proven
is 1.7's second half, that the runner exits BEFORE running anything when any selected item is
`undetermined`; see 5.1.

2.4 DEPENDENCY ORDERING AND REFUSAL EXIST and largely satisfy 1.4 and 1.5. The queue is sorted with
dependency depth as the FIRST key (`queue_sort_key`, `dependency_depth`), edges are RE-CHECKED at
dispatch rather than only at queue build, and an unmet edge marks that one item `fail-depend` (legacy `dependency-blocked`) and
continues rather than failing the whole run. The in-batch case of 1.4 is handled: a dependency inside
the same queue contributes to the ordering.

2.5 PER-TYPE CONFORMANCE CHECKING EXISTS as a verb and partially satisfies 1.3. `aw check <type>`
validates artifacts of a type against their contract (exit 0 clean, 1 findings, 2 cannot-run). What is
not established is that a RUNNER invokes it, or an equivalent, over its whole selection before dispatch.

## 3. Production actions: executing a spec or backlog item YIELDS artifacts

THE MAINTAINER'S RULING, 2026-09-16: "executing a spec results in either backlog items or plans."

3.1 An action of `plan` is a PRODUCTION action. Its successful outcome is one or more NEW artifacts
(plans, or backlog items), each conformant and each linked to the artifact that produced it. It is NOT
"the work the spec describes was done".

3.2 The produced artifacts MUST carry machine-readable provenance back to their source. The repository
already has the fields: a plan or spec carries `- From-Spec: <spec-id6>`, and `- From-Backlog:
<backlog-id6>` for a backlog source. A production action that emits an artifact without provenance is
incomplete, because the link is what lets a release gate be provably handed off rather than dropped.

3.3 A production action MUST NOT mark its source artifact as done work. A spec that produced plans
advances toward `implementing` (its children now carry the work); a backlog item that produced a plan
becomes `graduated`, NOT `done`, per the existing rule that `graduated` means the design was handed off
while `done` means code was written and validated.

3.4 WHAT THIS SPEC DOES NOT DECIDE: whether the artifacts a production action emits are enqueued into
the SAME run, or reported as next actions for a later run. Both are defensible and the repository has an
unimplemented flag reserving the question (`--follow-generated`, measured `implemented=False`, owner
backlog `x8diyb`). See `OQ-01`.

## 4. The one real gap

4.1 THE QUEUE ADMITS ONLY PLANS. This is the single structural blocker, and it sits between two working
halves: the selector can FIND a spec (2.1) and the action table KNOWS a to-review spec means review
(2.2), but the manifest between them cannot carry it. Measured: `build_dynamic_manifest` compiles
`discover_plans` output into a `plans_dict`; a queue entry is plan-shaped
(`"configured_file": plan["file"]`); and `configured_file` is read at 37 sites across five modules
(`oc_runipd` 16, `agy_runipd` 11, `run_viewer` 5, `artifact_audit` 4, `attention` 1).

4.2 THE PATH RESOLVER FAILS OPEN ON A NON-PLAN, which is worse than a refusal and is the strongest
argument for a TYPED resolver rather than guarding 37 call sites. Measured in
`runner_shared.resolve_plan_path`: it first resolves by `<id6>` against the `plans` type, then falls
back to a `configured` branch that returns any path which merely EXISTS:

```python
if configured:
    direct = (repo / configured).resolve()
    if direct.is_file():
        return direct        # returns a .spec.md with no diagnostic
```

Its final fallback globs `*-<id6>-*.ipd.md` and raises `DriverError` when nothing matches. So a spec is
refused ONLY when no `configured` path is supplied; supply one and it passes silently into code that
assumes a plan.

4.3 PRODUCTION HAS NO CONSUMER. `ACTION_PLAN` is defined and mapped (spec `approved` -> `plan`, backlog
`open` -> `plan`) but nothing dispatches it: measured, `ACTION_PLAN` appears only in its own definition,
the action-order tuple, and the two table entries. So 1.6's third bullet and all of Section 3 are
unbuilt.

4.4 THIRTEEN `SPEC-*` CONFORMANCE CODES ARE DECLARED BUT UNBUILT, and they are declared in section 4.8
of spec `25kzda`, whose `- Status:` is `approved`. They are therefore AGREED REQUIREMENTS THAT WERE NEVER
IMPLEMENTED, not speculative future work. Measured: every one greps to ZERO enforcement under
`agent_workflows/`; the single textual `SPEC-` hit in the package is an unrelated prose comment. A plan
MUST NOT treat them as existing enforcement, which is the error an earlier draft of `mng63x` E-04 made.
`OQ-02` rules FOUR of them IN SCOPE here (the `SPEC-PLAN-*` family) because they verify Section 3's
production actions; the other NINE stay with `25kzda` 4.8.

## 5. Acceptance criteria

5.1 A run whose selection contains an artifact the action table maps to `undetermined` PRINTS a clear
error naming the artifact, its type and its status, and EXITS having dispatched nothing. Proven by a
selection containing one unclassifiable artifact plus one valid plan, showing the valid plan did NOT
run.

5.2 A run whose selection contains a malformed artifact of a known type REFUSES at selection time and
names the conformance finding, before any dispatch.

5.3 The in-batch dependency case of 1.4 is proven BOTH ways: `efg456` requiring `abc123` runs when
`abc123` is in the batch (ordered first), and REFUSES when `abc123` is absent from the batch and not
already executed.

5.4 A to-review spec dispatches the SPEC review, not the plan review, and the run record shows which
handler ran.

5.5 An approved spec dispatched as a production action emits at least one conformant artifact carrying
`- From-Spec:` pointing at that spec, and the spec is NOT marked as completed work (3.3).

5.5a REPORT-ONLY IS PROVEN, not assumed (OQ-01). The artifacts a production action emits do NOT enter the
running queue: after such a run, the frozen `state['queue']` contains exactly the items it was created
with, and the emitted artifacts appear as REPORTED next actions. Proven by comparing the queue id set
before the first turn against the queue id set at run end, and by showing a resume of that run dispatches
nothing new.

5.5b THE RELEASE GATE CARRIES FORWARD (OQ-03). A spec carrying `- Blocks-Release: <R>` that produces a
plan yields a plan carrying the SAME value, and a spec with no gate yields a plan with none invented.
This is `SPEC-PLAN-GATE-CARRY` (OQ-02, in scope) and both directions must be tested.

5.6 No second action table exists: an AST or grep check proves `_ACTION_TABLES` is the only
type-plus-status-to-action mapping in the package.

5.7 The typed resolver refuses a type mismatch with a diagnostic. Given a `.spec.md` supplied as a
plan's `configured_file`, the resolver REFUSES and names the mismatch rather than returning the path
(directly reversing the 4.2 measurement).

5.8 Every one of the 37 `configured_file` read sites either reads through the typed accessor or is
individually justified in the executing plan. A count alone is not evidence; the enumeration is.

## 6. Open questions (for the maintainer)

### OQ-01: Are artifacts produced by a production action enqueued into the SAME run, or reported for a later one?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution: RULED 2026-09-16 by the maintainer: NO FOLLOW FOR NOW. A production action REPORTS the
  artifacts it created as next actions; it does NOT enqueue them into the running queue. When
  `--follow-generated` is implemented (owner backlog `x8diyb`), that flag becomes the opt-in mechanism
  for the same-run behavior, and the default stays report-only.
  WHY THIS IS THE SAFE DEFAULT, recorded so it is not "simplified" later: enqueueing makes a run's scope
  unbounded at freeze time, and the frozen `state['queue']` is what `resume` reads after an interruption,
  so a run that grew its own queue could not be resumed deterministically. Report-only keeps the queue a
  fixed set decided before the first turn.
  CONSEQUENCE FOR REQUIREMENT 1.6 AND SECTION 3: a production action's success is measured by the
  artifacts it WROTE and their provenance links, never by those artifacts having also run. Acceptance
  criterion 5.5 already states it this way and needs no change.

### OQ-02: Are the unbuilt `SPEC-*` conformance codes in scope for this work?

- Blocking: no
- Status: resolved
- Owner: maintainer (decided 2026-09-16 after the codes were explained; see the correction below)
- Resolution: PARTIALLY IN SCOPE. The FOUR `SPEC-PLAN-*` codes ARE in scope (`SPEC-PLAN-COUNT`,
  `SPEC-PLAN-CONFORMANCE`, `SPEC-PLAN-TRACE`, `SPEC-PLAN-GATE-CARRY`),
  because they are the verification layer for the production actions Section 3 defines. The remaining
  codes (`SPEC-REVIEW-*`, `SPEC-APPROVAL-AUTHORITY`, `SPEC-IMPLEMENTING-*`, `SPEC-LINKED-PLANS`,
  `SPEC-CHILD-OUTCOMES`, `SPEC-IMPLEMENTED-*`) are NOT required by this spec and remain owned by
  `25kzda` 4.8 for separate work.
  A CORRECTION TO THIS SPEC'S OWN 4.4: the count is THIRTEEN codes, not eleven, and they are declared in
  section 4.8 of spec `25kzda`, whose `- Status:` is `approved`. So they are not speculative future work:
  they are AGREED REQUIREMENTS THAT WERE NEVER IMPLEMENTED. Measured at HEAD, every one greps to zero
  enforcement under `agent_workflows/`.
  WHAT THE IN-SCOPE ONES REQUIRE, in plain terms, since each maps directly onto a Section 3 obligation:
  `SPEC-PLAN-COUNT` (at least one new plan was really created and no duplicate active plan already
  existed), `SPEC-PLAN-CONFORMANCE` (each new plan is canonical, `to-review`, in `pending/`, carries
  `From-Spec`, and has concrete Scope-Paths), `SPEC-PLAN-TRACE` (every mandatory spec requirement maps to
  at least one E item and every acceptance criterion to at least one V item), and
  `SPEC-PLAN-GATE-CARRY` (a spec's `Blocks-Release` is copied to the plan EXACTLY and an absent gate is
  never invented). That last one is the mechanical enforcement of the maintainer's OQ-03 ruling that a
  release gate carries forward.
  NOT IN SCOPE BUT WORTH NAMING: `SPEC-APPROVAL-AUTHORITY` requires that a HUMAN approved the exact
  reviewed digest and states that `--full-auto` does not satisfy it. It is the anti-forgery gate for spec
  approval and deserves its own work rather than being folded in here.

### OQ-03: Does this spec supersede plan `mng63x`, or is that plan re-authored against it?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution: SUPERSEDE, ruled 2026-09-16, and THE RELEASE GATE CARRIES FORWARD. `mng63x` chose no shape
  and did not contemplate production actions, so editing E-02 to E-04 item by item would leave a plan
  whose findings argue toward a decision now already made; its own instruction prescribes superseding in
  exactly this case. Its `- Blocks-Release: next` MUST be carried by whatever plan graduates from this
  spec, per the close-legitimacy rule that a blocking item may only close through handoff, cited
  evidence, or explicit de-gating. Mechanically enforced by `SPEC-PLAN-GATE-CARRY` once built (OQ-02).
- Notes: `mng63x` is `reviewed` with `- Readiness: no-go` and its own instruction is explicit: "IF THE
  RULING CHANGES THIS PLAN'S SHAPE ... SUPERSEDE this plan rather than editing E-02 to E-04 item by
  item." This ruling does change its shape, since it chooses the generalize-the-queue direction and adds
  production actions the plan did not contemplate. Recommendation is therefore to supersede, but the
  call is the maintainer's. Note `mng63x` carries `- Blocks-Release: next`, so the gate must be handed
  to whatever replaces it rather than dropped.

## 7. Deliberately out of scope

- WHICH internal structure the dispatcher uses (1.8, the maintainer's explicit indifference).
- Prompt and comms dispatch. The action table has no entries for them, and inventing statuses for types
  whose lifecycle nobody has specified is how a table acquires rows no reader trusts.
- Rewriting the nine existing selector types or their contracts. This spec constrains how tools CONSUME
  artifacts, not what the artifacts are.
- Changing `aw attention`, the checkers, or the listers. They already route through the shared selector
  (2.1); this spec asks the RUNNERS to reach the same standard, not the readers to change.
