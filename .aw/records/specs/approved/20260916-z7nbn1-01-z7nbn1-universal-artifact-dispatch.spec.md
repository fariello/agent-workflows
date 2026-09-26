# Spec: Universal artifact dispatch: one selector, one action table, one conformance gate for every runner and reader

- Date: 2026-09-16
- Status: approved
- Blocks-Release: next
- Id: z7nbn1
- Author: opencode/its_direct-pt3-claude-opus-5 (dictated by the maintainer 2026-09-16)
- Work-Kind: feature
- Scope: Every tool that looks at or acts on artifacts resolves them through one selector, decides what to do through one action table, and refuses clearly on anything it cannot classify; executing a spec or backlog item PRODUCES plans or backlog items rather than doing work itself.

## Workflow history
- 2026-09-26 approved (aw set, --by-human): Maintainer approved 2026-09-26 in chat ('Yes, approve and graduate') after /spec-review APPROVE WITH REVISIONS APPLIED

- 2026-09-26 note (aw specs): /spec-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; SR-001..SR-010 FIXED; review record .aw/records/reviews/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.review.md; ready for human approval
- 2026-09-26 reviewed (aw set): /spec-review round 1: APPROVE WITH REVISIONS APPLIED; SR-001..SR-010 all FIXED; maintainer rulings 2026-09-26 recorded as OQ-04 (split refusal by when known; amends 25kzda), OQ-02 revised (SPEC-PLAN-TRACE deferred to backlog vy20et), OQ-05 (backlog production + BACKLOG-* codes in scope)
- 2026-09-25 note (aw specs): AMENDED 2026-09-25 (statusvocab 9x7otz / cyamvi): canonical terminal status vocabulary updated (fail-depend, fail-merge, fail-gate, fail-verify, fail-begin, fail-lane, not-run, interrupted). Legacy terminal status tokens (including dependency-blocked, integration-blocked, merge-needs-human, merge-conflict, merge-refused, substantially-complete, failed-safely, not-attempted) remain readable forever for backward compatibility on historical run records (via TERMINAL_STATUS_ALIASES), but are no longer written by the runner.
- 2026-09-18 to-review (aw set): Carry forward Blocks-Release: next from superseded plan mng63x per maintainer ruling

- 2026-09-16 to-review (aw specs): MAINTAINER RULINGS RECORDED 2026-09-16, all three open questions resolved. OQ-01: NO FOLLOW for now; a production action REPORTS the artifacts it created and does not enqueue them, with --follow-generated becoming the opt-in same-run mechanism once implemented (the safe default, because the frozen queue is what resume reads). OQ-02: PARTIALLY IN SCOPE, the four SPEC-PLAN-* codes only, because they verify Section 3's production actions; also CORRECTED this spec's own 4.4, there are THIRTEEN such codes not eleven and they are declared in approved spec 25kzda 4.8, so they are agreed requirements never implemented rather than speculative work. OQ-03: SUPERSEDE mng63x, and its Blocks-Release: next carries forward to whatever plan graduates from this spec. Added acceptance criteria 5.5a (report-only proven by comparing the queue id set before and after) and 5.5b (gate carry tested in both directions).
## 0. Why this spec exists

`aw oc run reviews --type spec` can SELECT the specs awaiting review. Nothing can then RUN one. Plan
`mng63x` (`specdispatch-01`) captured that gap, recorded the constraints, and refused to choose a shape
because the maintainer reserved the decision ("HOW execution is implemented is something that needs
discussion; capture that fact loudly"). It was left `Blocking: yes` / `- Readiness: no-go` so nothing
could execute it as though the design were settled, and it was SUPERSEDED by this spec on 2026-09-18
(OQ-03; now at `.aw/records/plans/superseded/`).

THIS SPEC IS THAT DECISION. The maintainer stated the target architecture on 2026-09-16. It is written
down here because it was not captured anywhere: `mng63x` records the constraints and three candidate
shapes, not a chosen one.

## 0.2 Relations to other artifacts (direction stated)

- AMENDS approved spec `25kzda` (run-and-verify). This spec's refusal granularity (1.3, 1.4, 1.7, as
  ruled 2026-09-26 in OQ-04) is STRICTER than `25kzda` 3.1 gate 1 and the `RUN-STRUCTURE-PREFLIGHT`
  row of 4.2, which fail only the offending ITEM. The plan that implements this MUST carry the matching
  amendment to `25kzda` in the same change and list that `.spec.md` in its `- Scope-Paths:`. THIS IS AN
  IRREVERSIBLE-IN-PRACTICE CONTRACT CHANGE: `25kzda` is the approved contract every runner plan is
  reviewed against.
- IMPLEMENTS the unbuilt parts of `25kzda` 3.3 (`approved` spec -> author plans), 3.4 (`open` backlog
  -> author plans), and the verification codes in 4.8/4.9 that Section 4.4 below brings in scope.
- OWNS the execution half of approved spec `6m4kow` R-15 (how a runner dispatches a non-plan artifact),
  per `6m4kow`'s own ownership table.
- SUBSUMES open backlog `oc3mhb` (spec selector resolves but cannot be queued), whose four measured seams
  are the same gap as Section 4.1 and 4.3 and which itself asks to be reconciled with this spec before
  work starts. The first plan graduating from this spec SHOULD carry `- From-Backlog: oc3mhb` so that
  item closes by handoff rather than becoming parallel work.
- OVERLAPS a draft plan observed at review, `mxzogk` (make `resolve_plan_path` fail closed on a non-plan
  path, `- From-Backlog: m10mrs`), which targets exactly 4.2 / 5.7. If it executes first, 5.7 is
  satisfied by it and the implementing plan cites it rather than redoing it.
- DEPENDS ON (for one deferred check only) backlog `vy20et` (requirement-ID convention), which owns
  `SPEC-PLAN-TRACE`; see 4.4.

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
discovered by a handler that assumed otherwise. The refusal is of the WHOLE RUN, before any host
session, lease or worktree (OQ-04).

1.4 A runner MUST verify that declared dependencies are met OR COULD BE MET during the run, and MUST
refuse to run if any dependency is neither. The distinguishing case, stated because it is the whole
point: if `efg456` requires `abc123` to be executed and `abc123` is not yet executed BUT IS IN THE SAME
BATCH, the dependency CAN be met and the run proceeds with `abc123` ordered first. If `abc123` is absent
from the batch and not already executed, the run REFUSES as a whole, before any session (OQ-04).
"Could be met" is judged by the SAME consuming-action rule `25kzda` 2.9 already fixes (a review turn
is satisfied by a `reviewed`/`approved` target; an execute turn needs `executed`), so this requirement
adds a refusal point and changes no satisfaction semantics.

1.4a WHAT STAYS PER-ITEM (OQ-04, "split by when known"). Whole-run refusal applies only to conditions
KNOWABLE AT FREEZE TIME: an undetermined action (1.7), a non-conformant artifact (1.3), and a
dependency that is provably unsatisfiable in this run (1.4). An in-batch prerequisite that was
satisfiable at freeze but later FAILS during the run keeps today's behavior: its dependents are marked
`fail-depend` and independent items continue. Refusing the whole run at that point would discard
completed work for no safety gain.

1.5 A runner orders selected artifacts so that dependencies can be met, then iterates.

1.6 For each artifact, the runner performs the action the table gives:
  - an artifact in a review-ready status gets the review appropriate TO ITS TYPE;
  - an artifact in an executable status gets executed;
  - an artifact whose action is PRODUCTION emits new artifacts (see Section 3).

1.7 If the runner cannot determine what to do with a selected artifact, it MUST print an error that
explains the issue clearly and exit BEFORE running anything. Silently skipping it, or bucketing it into
some other action, is forbidden. "Cannot determine" means `undetermined` AFTER the runner has applied
the inputs `run_selection_policy` deliberately does not see (a draft's completeness check,
`--full-auto`, `--action`); a `reviewed` plan is not undetermined to a runner that knows its flags, so
this requirement does not refuse every run containing one.

1.8 The dispatcher MAY be structured as a thin router delegating to per-type handlers, OR as one
monolithic handler. THIS IS EXPLICITLY LEFT TO THE IMPLEMENTER (maintainer: "I don't care either way").
An implementation choice here is not a spec violation.

## 2. What is already built (MEASURED at HEAD 2026-09-16, not assumed)

This section exists so no plan re-implements working machinery. Each claim carries the measurement.

2.1 THE UNIVERSAL SELECTOR EXISTS and satisfies 1.1. `agent_workflows/selectors.py` describes itself as
"the ONE selector-to-file resolver for the whole package", resolving direct path, `<id6>`, setid,
status, bare stem and filename fragment. Measured: it knows nine types (`backlog`, `comms`, `plans`,
`prompts`, `releases`, `research`, `roadmaps`, `specs`, `walkthroughs`), and (re-measured 2026-09-26)
seventeen modules import it, including `attention.py`, `cli.py`, `run_selection_policy.py`,
`runner_shared.py`, `status_set.py`, `ipd_lifecycle.py`, `reviews.py` and `artifact_audit.py`.
Requirement 1.1 is therefore largely SATISFIED FOR READERS; the runners' `expand_selectors` still
carries its own plan-filename substring fallback (`runner_shared.match_spec_selector` docstring), so
the runners are where 1.1 remains to be proven.

2.2 THE ACTION TABLE EXISTS BUT IS NOT YET THE ONE TABLE, so 1.2 is only PARTLY satisfied.
`run_selection_policy._ACTION_TABLES` holds one table per type, read only through the PRIVATE
`_action_for`. Measured contents:

```
ipd:      to-review->review  approved->execute  auto-approved->execute  reusable->execute
          executed->skip  superseded->skip  not-executed->skip
spec:     to-review->review  approved->plan  implemented->skip  deferred->skip
          parked->skip  superseded->skip
backlog:  open->plan  blocked->skip  parked->skip  graduated->skip  done->skip
```

(Absent rows map to `undetermined`: IPD `draft`/`reviewed`, spec `draft`/`reviewed`/`implementing`.
`research`/`release`/`walkthrough` skip by type alone; `prompt` executes unless terminal.)

BUT THE RUNNERS DO NOT CONSULT IT. The runners derive their action from a SECOND mapping,
`runner_shared.action_for(kind, status)` over `determine_action(status)`, which returns only
`review`/`execute`/`orchestrate` and maps EVERY non-review status, including `executed`, to `execute`
(`runner_shared.determine_action`). Queue building, dependency preflight and the dependency-closure
code all call it (`runner_shared._consuming_actions_for`, `initialize_run_core`). So the package has
two status-to-action mappings that disagree (for example `executed`: `skip` in the table, `execute` in
`action_for`). The maintainer ruled on 2026-09-10 (IPD `iuxtjy` OQ-04, recorded in backlog `oc3mhb`)
that the fix is a PUBLIC reader over `_ACTION_TABLES` that the drivers consult per type, not a third
copy. The `orchestrate` action (a Kind-dependent refinement for `- Kind: orchestrator` plans) has no
row in the table; the implementing plan MUST either add it to the table or record why a Kind
refinement layered on the table's answer does not count as a second table.

2.3 THE REFUSE-CLEARLY PATH EXISTS IN PART and partially satisfies 1.7. `ACTION_UNDETERMINED` is a
first-class action, and the code comment states the intent directly: an unknown type or status maps to
`undetermined` rather than "silently bucketing an undetermined item into `skip`". What is NOT yet proven
is 1.7's second half, that the runner exits BEFORE running anything when any selected item is
`undetermined`; see 5.1.

2.4 DEPENDENCY ORDERING EXISTS and satisfies 1.5; REFUSAL IS PER-ITEM and does NOT yet satisfy 1.4.
The queue is sorted with dependency depth as the FIRST key (`queue_sort_key`, `dependency_depth`),
and the in-batch case orders correctly. Two kinds of refusal exist today:
  - STATIC graph errors (malformed, dangling, ambiguous, cyclic, unresolved) refuse the WHOLE run
    before any session (`runner_shared.enforce_dependency_preflight`).
  - An edge that is well-formed but UNSATISFIABLE in this run (the 1.4 "absent and not executed" case)
    does NOT refuse the run: it is discovered at dispatch by `runner_shared.edge_satisfied`, marks that
    one item `fail-depend` (legacy `dependency-blocked`), and independent items continue. This matches
    approved spec `25kzda` 3.1 gate 1 ("an unmet but valid dependency produces `dependency-not-met`
    without a host session"), which is why OQ-04 and 0.2 require amending `25kzda`.
Edges are RE-CHECKED at dispatch rather than only at queue build, and that stays (1.4a).

2.5 PER-TYPE CONFORMANCE CHECKING EXISTS as a verb and partially satisfies 1.3. `aw check <type>`
validates artifacts of a type against their contract (exit 0 clean, 1 findings, 2 cannot-run). What is
not established is that a RUNNER invokes it, or an equivalent, over its whole selection before dispatch.
The runner's only pre-dispatch structural gate today is the dependency preflight above, which is
IPD-only. `25kzda`'s `RUN-STRUCTURE-PREFLIGHT` row specifies this check but as `FAIL ITEM`; 1.3 makes
it whole-run.

## 3. Production actions: executing a spec or backlog item YIELDS artifacts

THE MAINTAINER'S RULING, 2026-09-16: "executing a spec results in either backlog items or plans."

3.1 An action of `plan` is a PRODUCTION action. Its successful outcome is one or more NEW artifacts
(plans, or backlog items), each conformant and each linked to the artifact that produced it. It is NOT
"the work the spec describes was done".

3.2 The produced artifacts MUST carry machine-readable provenance back to their source. The repository
already has the fields: a plan or spec carries `- From-Spec: <spec-id6>`, and `- From-Backlog:
<backlog-id6>` for a backlog source. A production action that emits an artifact without provenance is
incomplete, because the link is what lets a release gate be provably handed off rather than dropped.

3.3 A production action MUST NOT mark its source artifact as done work. After the produced artifacts
are committed, a spec that produced plans is tool-set `approved -> implementing` through `aw specs
set` (its children now carry the work), per `25kzda` 3.3; a backlog item that produced a plan is
tool-set `open -> graduated`, NOT `done`, through `aw backlog set`, per `25kzda` 3.4 and the existing
rule that `graduated` means the design was handed off while `done` means code was written and
validated. Both transitions go through the setters, never a text edit.

3.3a A production action MUST NOT modify the approved requirements of the spec it reads (`25kzda` 3.3
"Forbidden unattended"), and MUST NOT produce a duplicate of an active plan that already carries the
same `- From-Spec:`/`- From-Backlog:` for the same phase (`SPEC-PLAN-COUNT`, `BACKLOG-GRADUATE-COUNT`).

3.4 SAME-RUN FOLLOW IS DECIDED: REPORT-ONLY (OQ-01). The artifacts a production action emits are
REPORTED as next actions and are NOT enqueued into the running queue, matching `25kzda` 3.3/3.4
("Report generated IPDs as next actions; do not run them in the same run"). The previously reserved
`--follow-generated` flag was REMOVED by executed plan `hzdq8y` because no producer existed, and its
owner backlog `x8diyb` is `done`. Reintroducing an opt-in same-run mechanism is OUT OF SCOPE here and
would need its own spec amending both this one and `25kzda` 3.1, because it changes what `resume`
reads.

## 4. The one real gap

4.1 THE QUEUE ADMITS ONLY PLANS. This is the single structural blocker, and it sits between two working
halves: the selector can FIND a spec (2.1) and the action table KNOWS a to-review spec means review
(2.2), but the manifest between them cannot carry it. Measured: `build_dynamic_manifest` compiles
`discover_plans` output into a `plans_dict`; a queue entry is plan-shaped
(`"configured_file": plan["file"]`); and `configured_file` was measured at 37 sites across five modules
at authoring (`oc_runipd` 16, `agy_runipd` 11, `run_viewer` 5, `artifact_audit` 4, `attention` 1).
RE-MEASURED 2026-09-26 AFTER the `hostdedup`/`rununify` lifts moved host code into `runner_shared`:
`grep -o configured_file agent_workflows/*.py` gives 44 occurrences across six modules
(`runner_shared` 27, `run_viewer` 6, `artifact_audit` 5, `oc_runipd` 3, `agy_runipd` 2,
`attention` 1). The count WILL keep moving; 5.8 therefore requires an enumeration at execution time,
not this number.

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
The same holds for the FIVE `BACKLOG-*` codes of `25kzda` 4.9 (`BACKLOG-GRADUATE-COUNT`,
`BACKLOG-GRADUATE-IPD`, `BACKLOG-GATE-HANDOFF`, `BACKLOG-GRADUATE-LEGITIMACY`, `BACKLOG-CROSS-TREE`):
re-measured 2026-09-26, zero hits under `agent_workflows/`.

WHAT IS IN SCOPE (OQ-02 as revised 2026-09-26, and OQ-05):
  - IN: `SPEC-PLAN-COUNT`, `SPEC-PLAN-CONFORMANCE`, `SPEC-PLAN-GATE-CARRY` (they verify the spec
    production action of Section 3), and all five `BACKLOG-*` codes (they verify the backlog
    production action of Section 3). Each is implemented with the pass criterion, message text and
    Action column `25kzda` 4.8/4.9 already specify; this spec does not restate them.
  - DEFERRED: `SPEC-PLAN-TRACE`. It needs a machine-readable id on every spec requirement, and the
    corpus has no single convention (research `vkub9o`). Owned by backlog `vy20et`, which must define
    the convention and parser as its own spec. Until then, requirement coverage of a produced plan is
    checked by plan review, as today, and a produced plan MUST NOT be described as trace-verified.
  - NOT IN SCOPE, stay with `25kzda` 4.8: `SPEC-REVIEW-*`, `SPEC-APPROVAL-AUTHORITY`,
    `SPEC-IMPLEMENTING-TRANSITION`, `SPEC-LINKED-PLANS`, `SPEC-CHILD-OUTCOMES`, `SPEC-IMPLEMENTED-*`.
    NOTE: 3.3's `approved -> implementing` transition is still performed here through the setter; only
    the dedicated `SPEC-IMPLEMENTING-TRANSITION` verifier stays out.

## 5. Acceptance criteria

5.1 A run whose selection contains an artifact the action table maps to `undetermined` PRINTS a clear
error naming the artifact, its type and its status, and EXITS having dispatched nothing. Proven by a
selection containing one unclassifiable artifact plus one valid plan, showing the valid plan did NOT
run.

5.2 A run whose selection contains a malformed artifact of a known type REFUSES at selection time and
names the conformance finding, before any dispatch. Proven like 5.1: a malformed artifact plus one
valid plan in the selection, showing the valid plan did NOT run and no session or lane worktree was
created.

5.3 The in-batch dependency case of 1.4 is proven BOTH ways: `efg456` requiring `abc123` runs when
`abc123` is in the batch (ordered first), and the WHOLE RUN REFUSES before any session when `abc123`
is absent from the batch and not already executed, naming the edge; an unrelated valid plan in that
same selection did NOT run.

5.3a The per-item path of 1.4a is preserved: with `abc123` in the batch and satisfiable at freeze,
forcing `abc123` to fail during the run marks `efg456` `fail-depend` while an independent plan in the
same run still runs to completion.

5.3b `25kzda` is amended in the same change (0.2): its 3.1 gate 1 and the `RUN-STRUCTURE-PREFLIGHT`
row state the freeze-time whole-run refusal, and the plan's `- Scope-Paths:` names that `.spec.md`
so the runner's spec-edit announcement lists it.

5.4 A to-review spec dispatches the SPEC review, not the plan review, and the run record shows which
handler ran. The refusal path is also proven: after the turn, the spec is `reviewed` only via `aw specs
set` with a conforming review record, and a turn that leaves no such record does NOT advance the spec.

5.5 An approved spec dispatched as a production action emits at least one conformant artifact carrying
`- From-Spec:` pointing at that spec, and the spec is set `implementing` through the setter and is NOT
marked as completed work (3.3). Refusal paths proven: a production turn that writes no plan, a plan
lacking `From-Spec`, or a non-conformant plan FAILS the item with `SPEC-PLAN-COUNT` /
`SPEC-PLAN-CONFORMANCE` respectively and leaves the spec `approved`.

5.5c An open backlog item dispatched as a production action emits at least one conformant plan carrying
`- From-Backlog:` and inheriting any `- Blocks-Release:`, and the item ends `graduated`, never `done`.
Refusal paths proven with the five `BACKLOG-*` codes of `25kzda` 4.9: no plan written
(`BACKLOG-GRADUATE-COUNT`), non-conformant plan (`BACKLOG-GRADUATE-IPD`), dropped release gate
(`BACKLOG-GATE-HANDOFF`), item set `done` or set before the handoff commit
(`BACKLOG-GRADUATE-LEGITIMACY`), and a cross-tree finding after the handoff (`BACKLOG-CROSS-TREE`);
in each case the item is left `open`.

5.5a REPORT-ONLY IS PROVEN, not assumed (OQ-01). The artifacts a production action emits do NOT enter the
running queue: after such a run, the frozen `state['queue']` contains exactly the items it was created
with, and the emitted artifacts appear as REPORTED next actions. Proven by comparing the queue id set
before the first turn against the queue id set at run end, and by showing a resume of that run dispatches
nothing new.

5.5b THE RELEASE GATE CARRIES FORWARD (OQ-03). A spec carrying `- Blocks-Release: <R>` that produces a
plan yields a plan carrying the SAME value, and a spec with no gate yields a plan with none invented.
This is `SPEC-PLAN-GATE-CARRY` (OQ-02, in scope) and both directions must be tested.

5.6 No second action table exists: an AST or grep check proves `_ACTION_TABLES` is the only
type-plus-status-to-action mapping in the package. In particular `runner_shared.action_for` /
`determine_action` either read through the public table reader or are removed; a test pins that the
runner's derived action equals the table's for every (type, status) row, including `executed ->
skip`.

5.7 The typed resolver refuses a type mismatch with a diagnostic. Given a `.spec.md` supplied as a
plan's `configured_file`, the resolver REFUSES and names the mismatch rather than returning the path
(directly reversing the 4.2 measurement).

5.8 Every `configured_file` read site that exists AT EXECUTION TIME (44 at the 2026-09-26 review; see
4.1) either reads through the typed accessor or is individually justified in the executing plan. A
count alone is not evidence; the enumeration is.

5.9 A selector naming a spec or backlog id6 resolves to THAT artifact on both hosts through the shared
selector, never to a plan whose filename contains the id6 (1.1), proven for one spec and one backlog
item.

## 5a. Honest limits

- The conformance gate (1.3) proves STRUCTURE only, exactly as `aw specs check` / `aw check` do; it
  says nothing about whether a well-formed artifact is a good one.
- A production action's checks prove plans were WRITTEN, LINKED and GATED. With `SPEC-PLAN-TRACE`
  deferred (4.4), nothing mechanical proves a produced plan COVERS its spec; plan review remains the
  only coverage check.
- Freeze-time refusal (1.4) is judged against repository state AT FREEZE. A dependency satisfied at
  freeze can still fail later (1.4a); the run does not promise that every admitted item will run.
- Migration: artifacts already on disk are unaffected. Existing run records keep their queue shape;
  only new runs use typed queue entries. Existing plans produced by hand from a spec without
  `From-Spec` are not retro-flagged by this spec (backlog `1zknu7` owns that).

## 6. Open questions (for the maintainer)

### OQ-01: Are artifacts produced by a production action enqueued into the SAME run, or reported for a later one?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution: RULED 2026-09-16 by the maintainer: NO FOLLOW FOR NOW. A production action REPORTS the
  artifacts it created as next actions; it does NOT enqueue them into the running queue.
  UPDATED AT SPEC REVIEW 2026-09-26: the ruling's forward reference ("when `--follow-generated` is
  implemented (owner backlog `x8diyb`), that flag becomes the opt-in") is OBSOLETE. Executed plan
  `hzdq8y` removed the never-built flag and `x8diyb` is `done`. Report-only is therefore the ONLY
  behavior this spec specifies; any future opt-in is out of scope (3.4).
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
- REVISED 2026-09-26 by the maintainer at spec review: `SPEC-PLAN-TRACE` is DEFERRED to backlog
  `vy20et` (a separate spec defining a requirement-ID convention and parser), because the check cannot
  be built deterministically without one and research `vkub9o` (2026-09-20, after this ruling) found
  none. THREE `SPEC-PLAN-*` codes remain in scope. The original resolution follows for the record.
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

### OQ-04: Does a freeze-time problem refuse the whole run, or only the offending item?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution: RULED 2026-09-26 at spec review: SPLIT BY WHEN KNOWN. Anything knowable at freeze (an
  undetermined action, a non-conformant artifact, a dependency provably unsatisfiable in this run)
  refuses the WHOLE run before any session. An in-batch prerequisite that fails DURING the run keeps
  today's per-item `fail-depend` cascade. Written into 1.3, 1.4, 1.4a and 1.7.
- Notes: raised because 1.3/1.4/1.7 said whole-run while approved `25kzda` 3.1 gate 1 and
  `RUN-STRUCTURE-PREFLIGHT` say per-item and the shipped runner does per-item for unsatisfiable edges
  (`runner_shared.edge_satisfied`); this spec's old 2.4 claimed 1.4 was "largely satisfied", which was
  false. Consequence: `25kzda` must be amended by the implementing plan (0.2, 5.3b).

### OQ-05: Is backlog-to-plan production, with its verification codes, in scope?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution: RULED 2026-09-26 at spec review: ALL IN SCOPE. The backlog production action of
  Section 3 and the five `BACKLOG-*` verification codes of `25kzda` 4.9 are built here, covered by
  acceptance criterion 5.5c. Same reasoning as OQ-02: they verify a Section 3 production action.

## 7. Deliberately out of scope

- WHICH internal structure the dispatcher uses (1.8, the maintainer's explicit indifference).
- Prompt and comms dispatch. The action table has no entries for them, and inventing statuses for types
  whose lifecycle nobody has specified is how a table acquires rows no reader trusts.
- Rewriting the nine existing selector types or their contracts. This spec constrains how tools CONSUME
  artifacts, not what the artifacts are.
- Changing `aw attention`, the checkers, or the listers. They already route through the shared selector
  (2.1); this spec asks the RUNNERS to reach the same standard, not the readers to change. (1.1 and 1.2
  still bind them: a reader that later grows its own action mapping violates 5.6.)
- `SPEC-PLAN-TRACE` and the requirement-ID convention it needs (backlog `vy20et`).
- An opt-in same-run follow of produced artifacts (3.4).
- The `SPEC-*` codes listed as NOT IN SCOPE in 4.4, and the `implementing` spec dispatch row of `25kzda`
  3.3 (resolving and running a spec's `From-Spec` children), which stay with `25kzda`.
