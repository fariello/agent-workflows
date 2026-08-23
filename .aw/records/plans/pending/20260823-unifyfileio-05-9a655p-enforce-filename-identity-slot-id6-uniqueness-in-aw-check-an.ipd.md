# IPD: Enforce filename identity-slot id6 uniqueness in aw check and aw doctor

- Date: 2026-08-23
- Kind: child
- Concern: `aw check`/`aw doctor` cannot detect a foreign id6 sitting in a file's FILENAME identity slot. `check_engine.check_collisions` reads only the frontmatter `- Id:` line (`_ID_LINE_RE`, `check_engine.py:199,237`) and never inspects the `YYYYMMDD-<setid>-NN-<id6>` slot, so a walkthrough (or any artifact) that reuses another artifact's id6 in its own identity slot AND declares no `- Id:` is invisible to the check. That is exactly how `20260823-artifactenginefix-01-p7dqwz-execution.walkthrough.md` shipped with the plan `p7dqwz`'s id6 in its slot while `aw check` reported clean. DECISIONS.md D140 establishes that the identity-slot id6 is the unique identity of exactly one file; this plan makes the tooling enforce that invariant, and fixes the one existing violation.
- Scope: Extend the collision check so the id6 in a file's identity-slot MUST equal that file's own declared identity and MUST be globally unique across all record files, mirroring `tmp/find_id6_dupes.py`; surface it in `aw check` and `aw doctor` with a remediation; and rename the one offending `p7dqwz` walkthrough to its own id6 with a typed source-plan reference. Touch: `agent_workflows/check_engine.py` (`check_collisions`), `agent_workflows/doctor.py` (remediation mapping for the new rule), `tests/` (new coverage), and the one on-disk walkthrough. Depends on Order 01 (grammar authority: to parse the identity slot from a filename) - do not re-implement slot parsing here.
- Status: reviewed
- Set: unifyfileio
- Order: 5
- Highest E allocated: 03
- Author: Gabriele Fariello
- Id: 9a655p

## Workflow history

- 2026-08-23 draft (Gabriele Fariello): created (per DECISIONS.md D140; closes the enforcement gap that let a foreign id6 in a filename slot pass `aw check`).
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. Verified all material claims: check_engine.check_collisions reads id6 only from `_ID_LINE_RE` (check_engine.py:199,237, no slot inspection); the p7dqwz walkthrough exists sharing p7dqwz's slot id6 (aw find shows two files); DECISIONS.md D140 exists and mandates this; tmp/find_id6_dupes.py exists (gitignored); doctor.build_remediation is the extension point. PR-001 (E-03 double-touch with Order 01 E-06 walkthrough migration - added explicit sequencing: E-03 runs after E-06, re-resolves the path, STOPs if E-06 hasn't run); PR-002 (tightened E-01 to a precise (a)/(b) rule so it flags the reuse case but never mass-flags conformant files; V-01 asserts no-mass-flag); PR-003 (marked tmp/ script disposable; durable enforcement is the check+tests); PR-004 (canonical typed field `Target-Id:` chosen by human, OQ-02; spec-sync records it).

## Goal

Make `aw check` and `aw doctor` fail closed when a file's filename identity-slot id6 is not that file's own unique identity - the invariant `tmp/find_id6_dupes.py` verifies today by hand - so a future artifact can never again reuse another artifact's id6 in its own identity slot undetected. Then rename the single existing violator (`p7dqwz` execution walkthrough) to its own id6 with a typed `Target-Id:` reference to the plan it documents.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Enforce the identity-slot invariant in the check engine

- [ ] E-01 Extend `agent_workflows/check_engine.check_collisions` (or an adjacent check consumed by the same `aw check` path) so that, for every record file whose filename carries an identity slot, the slot id6 is parsed via the Order 01 naming authority and validated by this PRECISE rule (so it flags the p7dqwz reuse but does NOT mass-flag conformant files): (a) if the file DECLARES a frontmatter `- Id:`, its slot id6 MUST EQUAL that declared `- Id:`; (b) if the file declares NO frontmatter `- Id:`, its slot id6 MUST NOT equal any OTHER file's declared `- Id:` NOR any other file's slot id6 (i.e. it must be the sole holder of that id6) - this is exactly the reuse case (a slot id6 owned by another file's identity), which is the p7dqwz violation; (c) emit a distinct `check.id6-identity-slot` `Drift` naming the offending path AND the file that actually owns that id6. Preserve the existing frontmatter-`- Id:` global-uniqueness check unchanged. Keep the legacy `YYYYMMDD-HHMM-NN-<slug>` names (no id6 slot) exempt - only files whose slot parses as a real id6 are checked.
  - Depends on: none
  - Expected outcome: `aw check` fails closed on a file whose identity-slot id6 is not its own identity (reproducing the `tmp/find_id6_dupes.py` finding), and stays clean on a conformant tree.
  - Execution state: pending

### Task group 2: Surface it in doctor and rename the existing violator

- [ ] E-02 Map the new `check.id6-identity-slot` rule into `agent_workflows/doctor.py` so `aw doctor` reports it with a clear remediation ("this file's identity slot holds another artifact's id6; give it its own id6 and reference the source via a typed frontmatter field per DECISIONS.md D140"), consistent with how `doctor` renders other `check_engine` drift.
  - Depends on: E-01
  - Expected outcome: `aw doctor --agent` lists the identity-slot violation with an actionable remediation, not a bare failure.
  - Execution state: pending

- [ ] E-03 Rename the one existing violator (currently `.aw/records/walkthroughs/20260823-artifactenginefix-01-p7dqwz-execution.walkthrough.md`, or whatever name Order 01 E-06's walkthrough migration has already given it - re-resolve the file at execution time, do not assume the path) so it carries its OWN newly-minted id6 in the identity slot, add the typed `Target-Id: p7dqwz` frontmatter field (canonical per PR-004/OQ-02) pointing at the plan it documents, and rewrite any inbound citation to the old filename. Use `git mv` and the unified rename/reference tooling; do not hand-edit citations that the tool owns. SEQUENCING (verified): Order 01 E-06 (the broad `-walkthrough.md` -> `.walkthrough.md` migration) ALSO touches this same file (Order 01 records "the on-disk p7dqwz walkthrough fix rides the E-06 walkthrough migration"). To avoid double-touching: this E-03 runs AFTER Order 01 E-06; it takes the already-facet-form file and gives it its OWN id6 + typed reference. If Order 01 E-06 has NOT yet run at this plan's execution time, STOP and report (do not race the migration).
  - Depends on: E-01
  - Expected outcome: `aw check`/`aw doctor` report zero identity-slot violations; the walkthrough is self-identified (its own id6) and links to `p7dqwz` by a typed `Target-Id:` reference, not by identity reuse; no double-rename churn with Order 01 E-06.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `check_engine.check_collisions` (`check_engine.py:219-221`) documents "Cross-tree id6 AND setid uniqueness ... collisions are global, not per-type", but it detects id6 ONLY from the frontmatter `- Id:` line (`_ID_LINE_RE`, `check_engine.py:199`; searched at `:237`); it never inspects the filename identity slot. This is the enforcement gap.
- Frontmatter `- Id:` is genuinely globally unique today (verified: `tmp/find_id6_dupes.py` reports 0 frontmatter duplicates across 422 declaring files). The ONLY identity-slot reuse is the `p7dqwz` walkthrough.
- Walkthroughs are OPTIONAL (DECISIONS.md D140 + the corrected `walkthroughs/README.md`) and, per Order 01 OQ-05, get their OWN id6 with a typed source-plan reference; this plan aligns the checker + the one legacy file with that rule.
- The naming authority (Order 01) owns filename parsing; this plan consumes `parse_name`/the identity-slot accessor rather than re-implementing slot regex.

## Findings

Today's collision check gives a false sense of safety: it enforces frontmatter-`- Id:` uniqueness but is blind to a foreign id6 in a filename identity slot, so `aw find p7dqwz` truthfully shows two files sharing that id6 while `aw check` reports clean. The invariant "the identity-slot id6 is the unique identity of exactly one file" (D140) is only real once the checker enforces it. The fix is small and local (extend one check + one doctor mapping) and is guarded by tests that reproduce the `p7dqwz` case and then confirm the renamed file is clean.

## Proposed changes (ordered, validatable)

1. Extend `check_collisions` to validate the filename identity slot against the file's own identity + global uniqueness, emitting a distinct rule (E-01).
2. Map the rule into `aw doctor` remediation (E-02).
3. Rename the one existing violator to its own id6 + typed source reference (E-03).

## Deferred / out of scope (with reason)

- Setid identity/dangling semantics: out of scope (D140 covers id6 identity; setid-dangling is deferred separately per unifyfileio Order 03 OQ-01).
- The naming authority itself and the walkthrough grammar migration: owned by Order 01 (this plan consumes them; Order 01 OQ-05 + E-06 own the walkthrough builder + broad migration).
- Rewriting id6/setid citations: unchanged and out of scope (stable by design).

## Scope check

- Over-scope: none. Only the identity-slot check, its doctor remediation, and the one existing violator are touched.
- Under-scope: none. The check is added, surfaced in doctor, and the lone violation is fixed and regression-guarded.

## Required tests / validation

- A test that builds a fixture with a file whose identity-slot id6 differs from its own declared identity (or is absent) and asserts `check_collisions` flags `check.id6-identity-slot`; and a conformant fixture that stays clean.
- A test asserting `aw doctor` renders the new rule with a remediation.
- After E-03: `aw check all` and `aw doctor --agent` report zero identity-slot findings. (`tmp/find_id6_dupes.py` is a DISPOSABLE, gitignored oracle used only to characterize the current state; the DURABLE enforcement is the new `check.id6-identity-slot` rule + its tests, NOT that script. Do not depend on `tmp/` at runtime or in tests.)
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Update the `check_collisions` docstring to state it checks BOTH the frontmatter `- Id:` AND the filename identity slot. Cite DECISIONS.md D140. Update `aw check`/`aw doctor` help or the check rule list if it enumerates rules; else N/A with reason.
- Document the canonical `Target-Id: <id6>` typed source-plan reference field (OQ-02) wherever the walkthrough/artifact frontmatter convention is described (e.g. `.aw/records/walkthroughs/README.md` and/or the IPD/naming spec), so future tooling reads one canonical field name.

## Open questions

### OQ-01: For a type that legitimately declares no frontmatter `- Id:`, is a real id6 in its identity slot allowed at all?

- Blocking: no
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED per DECISIONS.md D140: the identity slot is an IDENTITY, so any file that carries a real id6 in its slot MUST own that id6 (declare it, or at minimum be the unique holder of it); a file may not put another artifact's id6 in its slot. Under Order 01 OQ-05 walkthroughs will declare their own id6, so the "slot present but no frontmatter Id" case becomes a violation to flag, exactly matching the `p7dqwz` fix. No further human input required; the check implements D140.

### OQ-02: What is the canonical typed field name for the source-plan reference?

- Blocking: no
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human (2026-08-23, /plan-review): `Target-Id: <id6>` is canonical (D140 lists it first; specific and directional - the walkthrough targets the plan it documents). E-03 uses `Target-Id:` and the Spec/documentation sync records the new field so future tooling reads one canonical name. `References:` is NOT introduced here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: unit tests drive `check_collisions` and assert: rule (a) a file whose declared `- Id:` differs from its slot id6 is flagged; rule (b) a file with NO `- Id:` whose slot id6 is ALSO another file's identity is flagged (the p7dqwz case), naming both paths; a conformant tree (including conformant files that declare `- Id:` matching their slot, and id6-less legacy HHMM no-slot names) yields NONE (no mass-flagging); the pre-existing frontmatter-`- Id:` uniqueness behavior is unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: a test asserts `aw doctor` (human and `--agent`) renders the new rule with the D140 remediation text.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: after the rename, the walkthrough filename carries its own id6, its frontmatter carries a typed `Target-Id: p7dqwz`, inbound citations resolve, `aw check all` + `aw doctor --agent` report zero identity-slot findings, and `pytest -n auto` is green (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - make the identity-slot invariant (D140) enforced and true on disk - staged as enforce (E-01) -> surface (E-02) -> fix the lone violation (E-03).

### Execution contract

1. Open questions RESOLVED: OQ-01 resolved (implements D140). PREREQUISITE: consumes the Order 01 naming authority to parse the identity slot; execute after Order 01 lands (or, if Order 01's slot accessor is not yet available, STOP and report rather than re-implementing slot parsing).
2. Scope fence: extend the collision check + its doctor remediation and fix the ONE existing violator only. Do NOT change id6/setid citation rewriting, the grammar (Order 01), or setid semantics. If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.
