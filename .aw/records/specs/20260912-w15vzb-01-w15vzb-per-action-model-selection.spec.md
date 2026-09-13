# Spec: Per-action model selection: the unit a model attaches to

- Date: 2026-09-12
- Status: approved
- Id: w15vzb
- Author: aw specs new
- Scope: A model preference attaches to a ROLE (a kind of work), declared in a top-level roles map that extends verify_with rather than superseding it
- From-Backlog: 0k74my

## Workflow history
- 2026-09-13 approved (aw set, --by-human): status set to approved
- 2026-09-13 reviewed (aw set): spec-review round 1 (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; SR-201..SR-205, all five FIXED, none deferred. THE DECISION RECORD IS EXEMPLARY AND THE SPEC HAD NO ACCEPTANCE CRITERIA AT ALL: nine MUSTs, zero criteria, so Section 9's claim that seven requirements are implemented was unrefusable. Added twelve criteria with a coverage map, three marked OUTSTANDING (A-8 needs the consumer, A-9 a verdict store that does not exist, A-10 the version bump that must ship WITH the consumer). Two properties the spec argues for had nothing checking them: the byte-identical resolution of every pre-existing configuration (the 'extend, do not supersede' promise it calls 'asserted rather than assumed') and the distinct role-map provenance. R-9 was conditional on an open question living only in plan btot17, so the spec now carries it as OQ-01 with owner, ruling and closing conditions (non-blocking because R-9's typed refusal keeps the pair inexpressible). Section renumbered after MEASURING that attention's OQ regex rejects a '7a.' heading, so the question is actually counted. VERIFIED every implementation claim: ROLE_NAMES exactly six, SCHEMA_VERSION 2, ALLOWED_PROFILE_KEYS unwidened, 131 passed in 2.42s, and zero runner_profiles hits in agy_runipd.py confirming the OC-only reach. Recorded a naming hazard: host_adapters defines a disjoint closed set also called roles.
- 2026-09-13 to-review (aw set): Records the actmodel-01 (btot17) decision: a model preference attaches to a ROLE from a closed vocabulary, declared in a top-level roles map that EXTENDS verify_with as a new bottom tier of the one existing chain. Sections 4.1-4.6 carry the four questions the backlog item reserved, with the maintainer's fitness-for-task reframing replacing the item's cost framing. R-1..R-5, R-9 and R-6 case A are implemented and tested; R-6 case B, R-7 and R-8 are outstanding and need the consumer that does not exist yet, so this is NOT implemented and is offered for critique.

- 2026-09-12 created (aw specs): A model preference attaches to a ROLE (a kind of work), declared in a top-level roles map that extends verify_with rather than superseding it

## 1. Why this record exists

The next action that wants a particular model must find an ANSWER here instead of re-deriving the
analysis. That is the whole deliverable: backlog item `0k74my` was filed as a "decided-but-unscoped
design question", and a decision that lives only in a closed item is a decision the repository
loses.

It records what plan `btot17` (`actmodel` Order 01) decided and built, and it records the parts that
were deliberately NOT built, with the reasons, so a later reader can tell a boundary from an
omission.

## 2. The question, and the correction that reframed it

The item asked: the runner resolves ONE model identity for a whole run, so a cheap action such as
the orchestrator probe cannot choose a cheap model. What should a model preference attach to?

THE FRAMING WAS WRONG, and the correction decides everything downstream. The item, and the plan
graduated from it, framed this as COST CONTROL. The maintainer rejected that outright on 2026-09-08:

> It is NOT about just getting a cheap model. It's about getting the best model for the job. Writing
> prose? Sonnet 5. Writing code? Opus 5. Writing code fast? Gemini 3.8 Flash, with Opus 5
> validation. Doing research online? GPT 5.6 Sol High. Checking content? Haiku.

Two consequences follow, and both are load-bearing:

1. THE UNIT IS DECIDED BY FITNESS FOR TASK, not by an extensibility count or a rate of new actions.
   The maintainer's categories ARE roles: they are kinds of work, not step names.
2. "RECORD IT AND BUILD NOTHING YET" STOPPED BEING AVAILABLE. Deferral was affordable only under the
   cost framing, whose bound was that probe verdicts are cached against a content digest so waste
   scales with plan churn. A quality argument has every run as a beneficiary, and caching is
   irrelevant to it.

## 3. The starting point: a per-role preference had ALREADY shipped

The measurement that motivated the item (`grep role agent_workflows/runner_profiles.py` returns
zero) is TRUE and MISLEADING. The shipped mechanism spells the concept `verify_with`, so a term
search could not see it. A vocabulary grep is not a capability measurement.

What `kgpptv` (`runprofile` Order 06, `- Status: executed`) had already shipped, and what this
design therefore had to EXTEND rather than invent:

- A per-role model preference for ONE role, the verifier: `verify_with`, in both
  `ALLOWED_PROFILE_KEYS` and `ALLOWED_DEFAULTS_KEYS`.
- A settled precedence chain for a model preference:
  `explicit --verify-with > profile's own verify_with > defaults.verify_with > ABSENT`, where ABSENT
  means "the verifier uses the executor's own launch".
- A REFERENCE, not an inline model string. The recorded reason is that an inline model "would fork
  the one place a launch identity is defined"; a reference reuses a whole already-validated profile.
- A LOAD-TIME refusal of a dangling reference (`_validate_verify_reference`), because a silent
  fallback would let "the operator believe an independent model verified the work when the same
  model did".
- A schema version bump 1 -> 2 with `SUPPORTED_SCHEMA_VERSIONS` reading both, so ABSENT is the whole
  backward-compatibility story.

What was still genuinely absent: any way for an ARBITRARY kind of work to declare a preference.
`resolve_launch_profile` (`oc_runipd.py`, located by symbol) resolves one launch identity for the
whole run, for every action except the verifier.

## 4. The decisions

### 4.1 The unit is a ROLE, from a CLOSED vocabulary

`ROLE_NAMES` is exactly six: `write-prose`, `write-code`, `write-code-fast`, `research-online`,
`check-content`, `verify`.

The first five are the maintainer's own categories, taken verbatim rather than reinterpreted. The
sixth, `verify`, exists because the shipped `verify_with` field had to become an ENTRY in this map
rather than remain a parallel field; mapping the verifier onto `check-content` would have been wrong
twice, since `verify_with` is per-PROFILE ("verify THIS profile's work with X") while
`check-content` is a kind of work, and the existing `--verify-with` chain would then silently have
become a second way to set `check-content`.

CLOSED, NOT OPEN, is a validation decision rather than a taste one. An arbitrary action key cannot
be checked, so a preference for a MISSPELLED action would be a silent no-op: it would sit in the
store looking effective and route nothing, and the operator would discover it from the bill. A
closed enum makes that a load-time refusal, which is the trade the dangling-reference check and
`FORBIDDEN_PROFILE_KEYS` already make everywhere else in the module.

### 4.2 Where it is declared: a TOP-LEVEL `roles` map

```json
{
  "schema_version": 2,
  "roles": {"write-prose": "sonnet", "write-code": "opus", "verify": "opus"},
  "profiles": {"opus": {"runner": "oc", "model": "vendor/strong-1"}}
}
```

TOP LEVEL, not per profile, for two reasons. First, a role is a property of the WORK, not of one
launch identity: "which model writes prose" no more belongs inside the `gem` profile than
`defaults.profiles` does. Second, per-profile placement would let N profiles each declare a role map
with no rule saying which wins, which is the "two switches for one behavior" defect the module's
precedence chains exist to prevent.

There is also a scope reason, recorded because it is the kind of thing that later looks arbitrary:
per-profile placement would have widened `ALLOWED_PROFILE_KEYS`, which is pinned literally in
`tests/test_runner_profiles_e2e.py` and enumerated in user-facing prose in `docs/runner-profiles.md`,
neither of which `btot17` declared in `Scope-Paths`. The top-level shape needed neither.

EACH VALUE IS A PROFILE REFERENCE, for `verify_with`'s reason exactly, and a dangling role reference
is REFUSED AT LOAD by `_validate_referential_integrity`.

### 4.3 Precedence: the role map is a NEW BOTTOM TIER of the ONE existing chain

```text
explicit --verify-with > profile's own verify_with > defaults.verify_with > roles["verify"] > ABSENT
```

This is what "EXTEND, do not supersede or layer" means concretely. The role map is consulted ONLY
where the shipped chain had already fallen through to ABSENT, so it can ADD an answer where there
was none and can never CHANGE an answer an existing document already produced. Every configuration
written before this field resolves byte-identically, which is asserted rather than assumed.

Question 2 of the item ("where is the preference declared, with what precedence") is therefore not
answered by analogy. A model preference ALREADY resolved this way, `f2mrsw` having set the pattern
with the `validate` tri-state and `kgpptv` having applied the same chain to `verify_with`. A third
variant would have been the defect. The provenance value is `role-map`, DISTINCT from `defaults`,
because an operator debugging "why did it run on that model" needs to know which tier spoke.

### 4.4 An unprovidable model: TWO cases, opposite answers

The item recommended a single answer ("warn and fall back, never fail the run"). That contradicts
shipped behavior, and the two cases genuinely differ:

- (A) AN UNRESOLVABLE REFERENCE, naming something that matches no profile. REFUSE AT LOAD TIME. This
  is what `_validate_verify_reference` already does, and the role map does the same, for the reason
  the code states: a silent fallback means the failure is "invisible in the result rather than
  visible in the bill". It is a configuration error, knowable and fixable at load, and refusing it
  costs nothing.
- (B) A RESOLVED PROFILE WHOSE MODEL THE HOST CANNOT PROVIDE AT LAUNCH. WARN AND FALL BACK, do not
  fail the run, and record the fallback in run state so it is LOUD rather than merely printed. Here
  the item's reasoning holds: "Failing closed on a MODEL CHOICE is probably wrong, since the work
  can still be done, just more expensively." It is discovered mid-run, where refusing would waste a
  queue for no safety gain.

Case (A) is IMPLEMENTED by this Order. Case (B) is a RUNTIME behavior and belongs to the plan that
wires a consumer, since nothing resolves a role into a launch yet (Section 6).

The sandbox precedent (`select_execution_profile` RAISES rather than degrading) is worth stating but
is the WEAKER analogy: it fails closed because degradation removes a SECURITY boundary, whereas
`verify_with` shows this module already fails closed on a MODEL question for an INTEGRITY reason,
which is the nearer case.

### 4.5 Cache validity across a preference change: KEEP IT AND RECORD THE ANSWERING MODEL

Options, with their costs:

- Invalidate on model change. Safe, expensive, and it defeats the caching that made the probe free.
- KEEP AND RECORD which model answered. Cheap, and it lets a reader distrust a weak verdict.
- Keep only when the new model is "stronger". Needs a model RANKING the repository does not have;
  embedding a fast-moving external judgement in durable config would age badly. Recommended AGAINST.

KEEP AND RECORD is chosen, anchored to the maintainer's 2026-09-07 ruling on the analogous case
(`m7gvuz` OQ-01: use the run's resolved model and record which model answered "so a future reader
can distrust a verdict produced by a weak model").

ONE CORRECTION TO THE ITEM'S PREMISE: the item said "the probe verdict store already records the
answering model ... so the data to make that judgment exists". It does NOT exist. Measured:
`m7gvuz` and `8tgg6g` are both `approved` and unexecuted, no probe or verdict-store symbol exists in
`agent_workflows/`, and the answering-model field is a DESIGN INTENT in `m7gvuz` OQ-01. So this is a
forward commitment on a store yet to be built, and `8tgg6g` remains its owner. No cache behavior was
changed by this Order.

### 4.6 The version was deliberately NOT bumped

`SCHEMA_VERSION` stays 2 and `roles` is read at any supported version. This DECLINES to follow
06-kgpptv-D2's precedent, for a stated reason rather than by oversight.

That precedent turns entirely on WHICH REFUSAL an older aw shows a user holding a document that
carries the new key: bumped, "Upgrade aw rather than editing the file"; unbumped, "unknown field(s)
['roles']", which invites hand-deleting a field the new aw owns. That difference only MATTERS once
such a document exists, and none can: no writer emits `roles` (the wizard writes profiles only) and
no consumer reads it. A bump now would spend a version number, plus a user-facing documentation
edit, on a field nothing can yet carry.

The asymmetry is why this is safe: staying at 2 and bumping later is free, while bumping early
cannot be undone without breaking a store already written as 3. There is also shipped precedent for
decoupling field acceptance from the declared version, since a v1 document may already carry
`verify_with`.

THE BUMP IS A REQUIRED COMPANION OF THE WIRING PLAN (Section 6), not an optional follow-up.

## 5. Disposition of `verify_with`: EXTENDED

Recorded explicitly, because a shipped schema key's future must be findable from the decision that
affects it:

- `verify_with` is NOT removed, NOT renamed, and NOT deprecated. It remains valid at both levels,
  still mutable through `set_verify_with_default`, and still resolves exactly as it did.
- `verify` is an ENTRY in the role map, and the map is a TIER of the same chain, so there is one
  chain rather than two switches.
- Retiring the key, if ever wanted, is separate compatibility work with its own migration.
- `kgpptv`'s PLAN file is in `executed/` and was not touched. What this record disposes of is its
  FIELD, by extension; the plan itself shipped and its fate is not a live question.

## 6. What is deliberately NOT built (boundaries, not omissions)

- NO CONSUMER, AND THEREFORE NO ROUTING. This Order ships the SCHEMA only. Declaring a role routes
  no model until a follow-on plan resolves a role into a turn's argv. The field is
  inert-but-validated on purpose: the schema is the part that must be agreed before a consumer
  hard-codes a shape. A reader must not mistake a populated role map for working routing.
- THE PRODUCING-PLUS-VALIDATING PAIR (`btot17` OQ-05, OPEN, owner: maintainer). The maintainer's
  fifth example ("Writing code fast? Gemini 3.8 Flash, with Opus 5 validation") wants a role to name
  TWO models. The ruling was "role to model mapping now, pairing recorded as the next step". It is
  not a trivial extension: it crosses `validate` (WHETHER a verifier turn runs) and `verify_with`
  (WHICH profile runs it), which the module says must not be conflated; it must say whether it
  inherits the ONE-HOP rule (DECISION 06-kgpptv-D1, under which a verifier profile's own
  `verify_with` is INERT); and "with Opus 5 validation" may mean the existing verifier turn with a
  different model or a new intra-action pairing, which are different builds. An object role value is
  REFUSED BY NAME with a message citing OQ-05, so the pair cannot become quietly expressible without
  a decision.
- CROSS-HOST ROUTING. The mechanism is OC-ONLY IN PRACTICE. `tm2cz8` executed and `RUNNER_REGISTRY`
  carries an `agy` row, but `runner_profiles`, `resolve_launch_profile` and `launch_profile` all grep
  to ZERO in `agy_runipd.py`. A registry row is not an integration, so cross-host routing depends on
  an integration that does not exist. (This corrects `btot17`'s original claim that the registry row
  had already made the mechanism cross-host.)
- A MODEL RANKING OR STRENGTH ORDER (Section 4.5).
- THE PROBE'S CACHE BEHAVIOR, owned by `8tgg6g`.
- THE `validate` TRI-STATE, owned by `f2mrsw`. Note the distinction the module insists on:
  `validate` decides WHETHER a verifier turn runs, `verify_with` decides WHICH profile runs it.

## 7. Requirements

- R-1 A model preference attaches to a ROLE, a kind of work, from a CLOSED vocabulary. An unknown
  role name is refused at load with a message listing the vocabulary.
- R-2 The vocabulary is the maintainer's five kinds of work plus `verify`. Widening it is a decision,
  recorded here and pinned by a test.
- R-3 A role's value is a PROFILE REFERENCE, never an inline model, and never an object. A dangling
  reference is refused at load time.
- R-4 `roles["verify"]` is the BOTTOM TIER of the existing `verify_with` chain, below
  `defaults.verify_with` and above ABSENT. No existing configuration's resolution may change.
- R-5 `verify_with` remains valid, resolvable and mutable. This design EXTENDS it.
- R-6 An unresolvable reference is REFUSED at load (case A). An unprovidable-at-launch model WARNS,
  falls back, and records the fallback in run state (case B), and belongs to the wiring plan.
- R-7 A cached artifact produced under model A stays valid when the preference changes, with the
  ANSWERING MODEL recorded alongside it.
- R-8 The first plan that makes `roles` consumable MUST also bump `SCHEMA_VERSION` to 3 and extend
  `SUPPORTED_SCHEMA_VERSIONS`, updating `docs/runner-profiles.md` and the e2e version pins in the
  same change (Section 4.6).
- R-9 A role naming a producing plus a validating model stays INEXPRESSIBLE until OQ-05 is decided,
  enforced by a typed refusal that cites the open question.

## 8. Open questions

### OQ-01: Should a role be able to name a PRODUCING plus a VALIDATING model?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: RAISED HERE AT REVIEW because this spec's own R-9 makes a
  requirement conditional on an open question that lived only in plan `btot17` (as its OQ-05), so a reader
  of the spec alone could not see what R-9 waits on or who owns it. The question is the maintainer's fifth
  example, "Writing code fast? Gemini 3.8 Flash, with Opus 5 validation", which wants one role to name two
  models. The 2026-09-08 ruling was "role to model mapping now, pairing recorded as the next step", so the
  DEFERRAL is already decided; what is open is the DESIGN, and it is genuinely the maintainer's because it
  is a public configuration shape. NOT BLOCKING because R-9 ships a typed refusal, so the pair cannot
  become quietly expressible while the question waits; a decision is needed only when someone wants the
  capability. WHAT WOULD CLOSE IT: a ruling on three points Section 6 already names, namely whether pairing
  crosses `validate` (WHETHER a verifier turn runs) and `verify_with` (WHICH profile runs it) in a way the
  module permits, whether it inherits the ONE-HOP rule under which a verifier profile's own `verify_with`
  is inert, and whether "with Opus 5 validation" means the existing verifier turn with a different model or
  a new intra-action pairing, which are different builds.

## 9. Acceptance criteria

ADDED AT REVIEW, because the spec had none: it carried nine requirements and no criterion, so nothing
stated what evidence would satisfy or refuse a claim of completion. Each criterion names the requirements
it covers, and the coverage map at the end makes an uncovered MUST visible.

- **A-1** (R-1, R-2) A role name outside the closed vocabulary is REFUSED at load with a message listing
  the vocabulary, and a test pins the vocabulary's exact membership so widening it fails the suite rather
  than passing silently. Evidence: the refusal message, plus the vocabulary assertion.
- **A-2** (R-3) A role value that is an inline model string, a non-string, or an OBJECT is refused; the
  object case is refused BY NAME with a message citing the open question that owns pairing. Evidence: all
  three refusals, and the object refusal's message text.
- **A-3** (R-3, R-6 case A) A role naming no existing profile is refused AT LOAD, and no mutator can leave
  a dangling role behind (including removing a profile a role references). Evidence: the load refusal plus
  the mutator cases.
- **A-4** (R-4) `roles["verify"]` resolves ONLY where the shipped chain fell through to ABSENT, and never
  overrides `--verify-with`, a profile's own `verify_with`, or `defaults.verify_with`. Evidence: the
  resolution at each tier with the role map present, showing the role map speaks last.
- **A-5** (R-4) EVERY configuration written before this field resolves BYTE-IDENTICALLY. Evidence: a
  pre-existing document's resolution and its serialized bytes before and after, equal. This is the
  criterion that proves "extend, do not supersede", and it must be asserted rather than assumed.
- **A-6** (R-4) The provenance of a role-map answer is reported as `role-map`, distinct from `defaults`, so
  an operator debugging which tier spoke can tell them apart. Evidence: the provenance value on a
  role-resolved launch.
- **A-7** (R-5) `verify_with` remains valid at both levels, resolvable, and mutable through its existing
  setter. Evidence: a round trip through the setter with the role map also present.
- **A-8** (R-6 case B) An unprovidable-at-launch model WARNS, falls back, and RECORDS the fallback in run
  state, and does NOT fail the run. OUTSTANDING: this needs the consumer. Evidence when built: the warning,
  the durable run-state record, and a non-failing exit.
- **A-9** (R-7) A cached artifact produced under model A stays valid when the preference changes, with the
  ANSWERING MODEL recorded beside it. OUTSTANDING and dependent on a verdict store that does not exist
  (Section 4.5). Evidence when built: the retained artifact plus the recorded model.
- **A-10** (R-8) The first plan that makes `roles` CONSUMABLE also bumps `SCHEMA_VERSION` to 3, extends
  `SUPPORTED_SCHEMA_VERSIONS`, and updates `docs/runner-profiles.md` and the e2e version pins IN THE SAME
  CHANGE. OUTSTANDING. Evidence when built: all four edits in one commit. A consumer landing without the
  bump is a failed criterion, not a follow-up.
- **A-11** (R-9) A producing-plus-validating pair stays INEXPRESSIBLE until the open question is decided,
  enforced by a typed refusal citing it. Evidence: the refusal and the citation (this is A-2's object case,
  asserted here for the requirement it defends rather than the shape it rejects).
- **A-12** (Section 6 boundary) A populated role map routes NO model until a consumer exists. Evidence: a
  resolution with roles declared, showing the launch identity unchanged. This criterion exists so the
  inert-but-validated state cannot be mistaken for working routing.

COVERAGE: R-1 A-1; R-2 A-1; R-3 A-2/A-3; R-4 A-4/A-5/A-6; R-5 A-7; R-6 A-3 (case A) and A-8 (case B);
R-7 A-9; R-8 A-10; R-9 A-11. Every requirement is covered. A-1 through A-7, A-11 and A-12 are satisfiable
today; A-8, A-9 and A-10 are the outstanding set and each names what it waits on.

## 10. Implementation status

Implemented by plan `btot17` (`actmodel` Order 01) in `agent_workflows/runner_profiles.py` with
tests in `tests/test_runner_profiles.py`: R-1 through R-5, R-9, plus R-6 case A. Outstanding: R-6
case B, R-7 and R-8, all of which need the consumer that does not exist yet.

VERIFIED AT REVIEW, 2026-09-13 at HEAD `9697856e`: `ROLE_NAMES` is exactly the six named roles;
`SCHEMA_VERSION` is 2 with `SUPPORTED_SCHEMA_VERSIONS` reading both 1 and 2; `PROVENANCE_ROLE_MAP` is
`role-map`; `roles` is a top-level key and `ALLOWED_PROFILE_KEYS` was NOT widened; and
`tests/test_runner_profiles.py` passes (`131 passed in 2.42s`) with named cases covering the vocabulary,
the dangling reference, the mutator cases, the tier ordering, the unchanged-bytes property, and the
no-version-bump decision. The claim that no consumer reads `roles` also holds: `runner_profiles`,
`resolve_launch_profile` and `launch_profile` each grep to ZERO in `agy_runipd.py`, so the mechanism is
OC-only in practice exactly as Section 6 states.

ONE NAMING HAZARD RECORDED AT REVIEW, because it will confuse the next reader and is not a defect in
either place: `agent_workflows/host_adapters.py` ALSO defines a closed set of things it calls roles
(`ROLE_ROUTER`, `ROLE_ISOLATED_EXECUTOR`, `ROLE_NONINTERACTIVE_RUNTIME`, `ROLE_PERMISSION_GATE`) with a
`resolve_role_target` resolver. Those are HOST CAPABILITIES (what a host can do), unrelated to this spec's
KINDS OF WORK (what a model is good at). The two vocabularies are disjoint and must not be unified or
cross-validated; a plan that wires a consumer should say which it means at every call site.
