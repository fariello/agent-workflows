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
- Status: open
- Owner: none
- Resolution or deferral rationale: The observed pattern is source->plan-Set. Default `Graduated-To`
  targets plan Sets; generalize only if a real spec->spec/backlog->spec graduation is needed. Decide at
  review.

### OQ-02: Within-type setid reuse with the SAME descriptive across Orders is legitimate clustering - confirm I1 does not over-constrain it.

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: I1 targets CROSS-TYPE duplication; the existing within-type
  descriptive-consistency rule is retained unchanged. Confirm the predicate distinguishes "same setid,
  same type, same descriptive, different Order" (legitimate Set clustering) from a true collision.

### OQ-03: Is a fresh-setid mint on graduation compatible with the intuitive same-name mental model (agentadhere backlog -> agentadhere plan Set)?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: The typed bidirectional links (From-Backlog/From-Spec + Graduated-To)
  preserve the TRACEABLE connection without the colliding name; the human-readable slug can still echo the
  source (only the setid token must differ). Confirm the graduation tool derives a distinct-but-recognizable
  child setid.

## Workflow history
- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored as the follow-on rationale for a setid-uniqueness tooling IPD Set, correcting the soft/detect-only setid-collision posture (awcheck-02-xwxxo8 E-02) to a hard, prevented, cross-type-unique invariant, and replacing shared-setid graduation coupling with typed bidirectional links (From-Backlog/From-Spec by id6 + new multi-valued Graduated-To by setid). Origin: `aw ipd set approved agentadhere` failed on a cross-type setid collision. Parent (uniform-naming 20260817-2147-01) is implemented/frozen; this extends it. REVISABLE before implementation.
