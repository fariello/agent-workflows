# Spec: setid uniqueness across types + bidirectional graduation links

- Date: 2026-08-27
- Status: draft
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 4w7d6s
- Summary: Make a Set id (setid) a hard, prevented, cross-type-unique identity, and replace shared-setid graduation coupling with typed bidirectional links (child From-Backlog/From-Spec by id6; source Graduated-To by setid).
- Parent: `.aw/records/specs/20260817-2147-01-uniform-artifact-naming-grammar.spec.md` (the uniform naming
  grammar that defines `<setid>`; it is `implemented` and transition-frozen, so this follow-on CORRECTS
  and EXTENDS it rather than editing it, per the reslife/5tapom precedent).
- Scope: the setid identity invariant (uniqueness across ALL record types), its enforcement posture
  (soft-detect today -> hard-prevent), and the graduation-link model that removes the shared-setid
  coupling which currently causes cross-type setid collisions. NOT in scope: the id6 identity invariant
  (already hard, D140 / check.id6-collision / check.id6-identity-slot - unchanged), the filename grammar
  itself (unchanged), or the runner.

This spec is the load-bearing rationale for a follow-on tooling IPD Set. It records the observed failure,
the existing partial enforcement, the chosen hard-invariant + graduation-link design, and acceptance
criteria, so the IPD Set can be authored and reviewed against a single source of truth.

---

## 1. Problem statement (observed, with evidence)

`aw ipd set approved agentadhere ...` FAILS with a confusing "Type mismatch: selector 'agentadhere'
resolved to artifact(s) of type ['backlog', 'research'] ... scoped to 'plans'." The root cause: the
setid `agentadhere` is used by a plan Set AND by the (now-closed) `agentadhere` backlog item AND by the
original `agentadhere` research reports. A type-scoped setter cannot act on the plan Set by its setid
because the setid is not unique across types.

`aw check all` already REPORTS this as `check.setid-collision` with a fix suggestion - so detection
exists. But two gaps make it a live, recurring failure:

1. **Enforcement is soft, not hard.** The `check.setid-collision` rule was DELIBERATELY built as
   surface-for-later-whitelisting drift (executed IPD `awcheck-02-xwxxo8` E-02: "If a setid legitimately
   spans a type by design, this is still worth surfacing as drift the maintainer can whitelist later").
   It is detect-only: NOT prevented at creation, NOT consulted by `aw ipd set`/`aw set`. Contrast the id6
   invariant, which IS hard (D140; `check.id6-collision` + `check.id6-identity-slot` fail closed in
   `aw check`/`aw doctor`; unifyfileio-05). setid and id6 are asymmetrically enforced.

2. **Graduation reuses a shared setid across trees - the actual source of the collision.** The
   backlog->IPD / spec->IPD graduation pattern (bklggrad, ipddeps design) currently couples source and
   child by giving them the SAME setid (the `agentadhere` backlog item and the `agentadhere` plan Set).
   That is precisely a cross-type setid collision by construction.

## 2. Existing partial enforcement (what NOT to rebuild)

- `check_engine.check_collisions` emits `check.id6-collision` (frontmatter `- Id:` dup across trees),
  `check.id6-identity-slot` (filename-slot id6 not the file's own / owned by another - D140, hard), and
  `check.setid-collision` (same setid under two different types OR conflicting descriptive within a type
  - currently SOFT). Wired into `aw check all`; `aw doctor` renders remediations.
- Typed cross-tree link fields already exist/are-designed: `From-Backlog` (built, bklggrad) and
  `From-Spec` (designed, ipddeps/25kzda) - the child->source back-reference by id6, with dangling
  checks (`check.from-backlog-dangling`).
- id6 minting already prevents id6 reuse at creation (the naming authority + identity-slot rule).

This spec REUSES all of the above; it changes the setid rule from soft to hard and adds the missing
source->child forward link + the creation/setter enforcement.

## 3. The invariant (normative)

> **REVERSED BY MAINTAINER DECISION 2026-09-10 (see OQ-03). DO NOT IMPLEMENT I1, I2, I3 or G1 AS WRITTEN
> BELOW.** The maintainer ruled that a setid is a SHARED CROSS-TYPE TOPIC LABEL, not a unique identity, so
> cross-type sharing is CORRECT and must not be prevented. The measurements behind the reversal are
> recorded in full under OQ-03: 117 of 433 setids already span types by design, review names deliberately
> inherit their subject's setid, and the motivating `agentadhere` failure was a LOOKUP defect (the setter
> held both the setid and the target type and still refused) rather than a naming one.
> WHAT SURVIVES: **I4** (type-scoped resolution) is the real fix and is now the spec's centre of gravity,
> and the within-type descriptive-consistency rule stays. **G2**, **G4** and **G5** survive as the typed
> link model, since id6 remains the identity. **I2 is inverted**: `check.setid-collision` must be
> DOWNGRADED, not hardened, because it currently reports 86 findings at severity `error` (invariant
> `I-09`) of which 78 are the backlog+plans topic sharing this decision endorses.
> This spec is `draft` and MUST be revised before implementation; the sections below are preserved
> unedited as the record of the superseded design, per the convention of correcting rather than rewriting.

- **I1 (cross-type uniqueness).** A setid MUST be unique across ALL record types. The same setid token
  MUST NOT appear under two different record types. (Within-type descriptive consistency, already
  checked, is retained.)
- **I2 (hard enforcement).** `check.setid-collision` becomes fail-closed (error, like
  `check.id6-collision`), NOT advisory/whitelistable. The "whitelist later" allowance from
  awcheck-02-xwxxo8 E-02 is explicitly RETIRED.
- **I3 (prevention at creation).** Creation/move verbs (`aw ipd scaffold`, `aw research new`/
  `new-comparison`, `aw backlog new`, `aw group`, `aw rename`) MUST refuse to mint or move an artifact
  into a setid already used by another type, at write time - consulting the collision predicate the way
  id6 minting already prevents id6 reuse.
- **I4 (setter resolution + error).** A type-scoped selector (`aw ipd set`, `aw set <type>`) MUST resolve
  a setid WITHIN the requested type's tree (so `aw ipd set agentadhere` acts on the plan Set even if the
  token also exists elsewhere); and where a genuine cross-type ambiguity would otherwise surface, the
  setter MUST emit the specific `setid-collision` message + the `aw group ... --set <new>` recovery, NOT
  the generic "type mismatch." (Once I1/I3 hold, cross-type setid duplicates cannot exist; I4's
  within-tree resolution is the correct behavior regardless, and the specific error is the transition
  safety net.)

## 4. Graduation-link model (normative)

Graduation (a backlog item or spec becoming one or more plan Sets) MUST NOT couple source and child by a
shared setid. Instead:

- **G1 (fresh child setid).** A graduated plan Set is minted with its OWN unique setid (never the
  source's).
- **G2 (child->source back-link, by id6).** Each generated IPD carries `From-Backlog: <id6>` or
  `From-Spec: <id6>` pointing at the single source item. (Existing/designed; unchanged.)
- **G3 (source->child forward-link, by setid).** On graduation, the source artifact (backlog item /
  spec) is UPDATED to carry `Graduated-To: <setid>[, <setid>...]` - a MULTI-VALUED list of the generated
  plan Set setid(s). A source may graduate more than once over its life (a spec may spawn several plan
  Sets; a re-graduation adds an entry), so the field is a list.
- **G4 (link asymmetry rationale).** Back-link is by id6 (each child points at exactly ONE source item);
  forward-link is by setid (a source points at the whole generated SET, orchestrator + children). This
  asymmetry is intentional and correct, not an inconsistency.
- **G5 (both directions validated).** `aw check` validates that every `From-Backlog`/`From-Spec` id6
  resolves (existing dangling check) AND that every `Graduated-To` setid resolves to a real plan Set
  (new `check.graduated-to-dangling`, mirroring the from-backlog dangling check).
- **G6 (graduation writes both links atomically).** The graduation operation (the tool that authors the
  child Set from a source) mints the fresh setid (G1), writes the child back-links (G2), and updates the
  source's `Graduated-To` (G3) as one path-scoped change.
- **G7 (close-legitimacy synergy).** A `done` backlog item / `implementing`->`implemented` spec whose
  release gate was handed off can now PROVE the handoff via a resolvable `Graduated-To` set, strengthening
  the bklggrad close-legitimacy guard (a resolvable forward link is satisfaction evidence).

## 5. Grandfathering / migration (the existing agentadhere collision)

- The current `agentadhere` collision (closed backlog item `3gr7fk` sharing the plan Set's setid) is a
  PRE-EXISTING violation. Making I1/I2 hard means it must be FIXED, not whitelisted: re-group the closed
  backlog item to its own unique setid (`aw group backlog <file> --set <new>`), and (per G3) record the
  plan Set it graduated into via `Graduated-To`. This both clears the `check.setid-collision` and unblocks
  `aw ipd set agentadhere`.
- A one-time sweep MUST identify and resolve any other existing cross-type setid collisions before I2 is
  turned on fail-closed, so enabling the hard rule does not mass-fail the tree. (Mirror the grandfathering
  discipline used for Scope-Paths / dependency cutover: find violators, fix, then enforce.)

## 6. Acceptance criteria

1. `check.setid-collision` is fail-closed (error) in `aw check`/`aw doctor`; no artifact tree carries a
   cross-type setid duplicate; the existing `agentadhere` collision is resolved.
2. Creation/move verbs refuse to create/move into a cross-type-duplicate setid, with an actionable message.
3. `aw ipd set <setid>` / `aw set <type> <setid>` resolve within the requested type; a true collision (if
   one somehow exists) yields the specific setid-collision message + `aw group` recovery, never a bare
   "type mismatch."
4. `Graduated-To` exists on backlog items and specs, is multi-valued, is written by the graduation
   operation alongside the child's `From-Backlog`/`From-Spec`, and `check.graduated-to-dangling` flags an
   unresolved entry.
5. Graduation mints a fresh child setid (never the source's); a graduated source shows what it became and
   each child shows its source, with no shared setid.
6. A one-time migration sweep resolves all pre-existing cross-type setid collisions; the full suite +
   `aw check all` are green after enforcement is enabled.

## 7. Open questions

### OQ-01: Does `Graduated-To` also apply to spec->spec or backlog->spec graduations, or only ->plan-Set?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED 2026-09-10 AS **YES, GENERALIZE**, by applying this
  question's OWN stated rule rather than by asking: it said "generalize only if a real
  spec->spec/backlog->spec graduation is needed", which is a measurement, and the measurement now says
  such graduations EXIST. Counted across all 29 specs at HEAD: 4 specs carry a non-empty
  `- From-Backlog:` (a backlog->spec graduation) and 1 carries a non-empty `- From-Spec:` (a spec->spec
  graduation), so 5 real non-plan-Set graduations are already in the tree. When this question was
  authored on 2026-08-27 the observed pattern was source->plan-Set only; that premise has since expired.
  CONSEQUENCE FOR THE DESIGN: `Graduated-To` must accept a spec target, not only a plan Set, or those 5
  existing sources cannot record what they became and the forward half of the bidirectional link is
  silently unavailable for them. Note the field is specified as multi-valued and keyed by setid, and a
  spec target is addressable the same way, so this widens the VALUE domain rather than the shape.
  ALSO NOTE the repository already treats a spec as a legitimate graduation target elsewhere: `AGENTS.md`
  states a spec "is an equally valid gate carrier, so a spec-first graduation can legitimately close its
  item", and `check.from-spec-dangling` ships as the mirror of `check.from-backlog-dangling`. So the
  plan-Set-only default would have contradicted a rule already in force.

### OQ-02: Within-type setid reuse with the SAME descriptive across Orders is legitimate clustering - confirm I1 does not over-constrain it.

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED 2026-09-10 AS **CONFIRMED, I1 DOES NOT OVER-CONSTRAIN
  LEGITIMATE CLUSTERING**, and resolved by measurement rather than by asking because the question asked
  only to CONFIRM a property of shipped code, which is a fact the repository holds. MEASURED THREE WAYS
  in a scratch tree against the shipped `check_engine.check_collisions`, not by reading it alone:
  (1) THE LEGITIMATE CASE PASSES. Three plans sharing setid `samesetid` AND the same descriptive across
  Orders 01/02/03 produce **0** findings. This is the exact shape the question worried about.
  (2) THE CROSS-TYPE CASE STILL FIRES. Adding a backlog item on the same setid produces **1** finding:
  `setid samesetid conflicts with ...(different type: plans vs backlog)`.
  (3) THE WITHIN-TYPE CONFLICTING-DESCRIPTIVE CASE STILL FIRES. Adding a fourth plan on the same setid
  with a DIFFERENT descriptive produces a second, distinct finding naming both descriptives.
  So the predicate already discriminates on exactly the two axes the invariant needs (type, then
  descriptive) and treats Order as irrelevant, which is what makes same-setid clustering legitimate. The
  mechanism, for the implementer: it keys `seen_sets` on the setid alone and compares the stored
  `(type, descriptive)` pair, emitting only on a type difference or on two non-None differing
  descriptives; a repeated setid with matching type and matching descriptive falls through silently.
  IMPLEMENTATION CONSTRAINT THIS IMPLIES, worth stating because the hard-enforcement change is where it
  could be lost: the creation-time and setter-time guards I1 adds MUST reuse this same predicate rather
  than re-deriving uniqueness, or the new hard path can easily forbid the clustering the detect-only path
  correctly allows. That is the one way this confirmation could stop being true.

### OQ-03: Is a fresh-setid mint on graduation compatible with the intuitive same-name mental model (agentadhere backlog -> agentadhere plan Set)?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`) AS **KEEP THE SETID
  SHARED AS A CROSS-TYPE TOPIC LABEL; FIX THE AMBIGUOUS LOOKUP INSTEAD, AND DOWNGRADE THE FALSE ERROR**.
  This REVERSES the premise of this spec's central invariant I1 (see the amendment note in Section 3) and
  therefore answers OQ-03 by removing the question: no fresh-setid mint is wanted, so there is no
  distinct-but-recognizable child setid to derive.
  THE MAINTAINER'S REASONING, recorded because it is the load-bearing part: research, specs, prompts and
  IPDs concerning one issue ARE naturally one set to a user, and a shared setid makes that relationship
  obvious while distinct setids OBFUSCATE it. They framed the alternative reading honestly (a setid as
  things that "run together", i.e. a plan-execution batch) and observed that under it the setid becomes
  effectively useless for most artifacts and always useless for specs, since no "spec set" exists.
  THE MEASUREMENTS THAT SETTLED IT, taken at HEAD before the decision and shown to the maintainer:
  (1) CROSS-TYPE SHARING IS THE DOMINANT PATTERN, NOT DRIFT. Of 433 distinct filename-slot setids, **117
  span more than one record type**. The widest are genuine topics: `agentadhere` covers 7 plans + 1
  backlog item + 5 research reports (13 files), `lanectn` covers 7 plans + 7 reviews + 1 walkthrough. I1
  would have forbidden all 117.
  (2) IT IS PARTLY AUTOMATIC AND DELIBERATE. `review_findings.build_review_name` constructs a review's
  name from the SUBJECT's setid and the SUBJECT's id6 ("the join key ... not a fresh identifier"), so
  plans+reviews sharing a setid is designed behavior. That combination alone accounts for 47 of the 117,
  plus 38 more as backlog+plans+reviews.
  (3) THE MOTIVATING FAILURE IS A LOOKUP DEFECT, NOT A NAMING ONE. The Section 1 error ("selector
  'agentadhere' resolved to artifact(s) of type ['backlog', 'research'] ... scoped to 'plans'") shows the
  setter HELD both the setid and the target type and still refused. Resolution by (type, setid) was
  available and unused.
  (4) THE CHECK IS CURRENTLY MISLABELLING CORRECT BEHAVIOR. `check.setid-collision` ships at severity
  `error` under invariant `I-09` and reports **86** live findings, 78 of them backlog+plans, i.e. mostly
  the graduation topic-sharing this decision endorses.
  WHAT REPLACES I1, stated so no implementer inherits the reversed rule by accident: setid is a GROUPING
  LABEL, not an identity. The identity invariant already exists and is already hard (id6, D140), and every
  cross-tree link is keyed by id6 (`From-Backlog`, `From-Spec`, and a review's inherited subject id6). So
  tools MUST resolve by `(type, setid)` or by id6 and MUST NOT assume a bare setid is globally unique.
  ACCEPTED COST: a bare setid remains ambiguous by design, so every name-taking verb needs a type scope or
  a disambiguating prompt. That is the price of filename-level topic discovery, which the maintainer
  judged worth more than global uniqueness.

## Workflow history

- 2026-09-10 note (aw specs): askme 2026-09-10: all three open questions resolved. OQ-01 and OQ-02 resolved from measurement by the agent (each stated its own decision rule; both rules were decidable once measured). OQ-03 resolved BY THE MAINTAINER and it REVERSES the spec's central invariant: a setid is a SHARED cross-type TOPIC label, not a unique identity, so I1/I2/I3/G1 must NOT be implemented as written. Basis measured before asking: 117 of 433 setids span types by design, review names deliberately inherit the subject's setid (47 of those 117), and the motivating agentadhere failure was a lookup defect. I4 (type-scoped resolution) becomes the fix; check.setid-collision must be downgraded from its current error severity, where it reports 86 findings, 78 of them correct behavior. A reversal banner now heads Section 3; the superseded design text is preserved unedited. Spec stays draft and needs revision before implementation.
