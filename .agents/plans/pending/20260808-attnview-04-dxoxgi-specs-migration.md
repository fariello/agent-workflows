# IPD: specs status and history migration (Set attnview, Order 4)

- Date: 2026-08-08
- Kind: child
- Concern: bring the existing specs corpus into conformance with the new specs contract (bare-enum `- Status:` + `## Workflow history`) via the `aw specs` verbs, WITHOUT moving any file, so `aw attention --check` passes clean on the repo's specs and the specs blind spot the whole Set targets is actually closed.
- Scope: a one-time normalization of the existing specs under `.agents/docs/specs/` using `aw specs set`/`note` (Order 02): map each free-form prose status to a bare enum token, add a `## Workflow history` section where missing, and add typed gates to any `deferred` spec. Preserve every repository-relative path (specs stay flat). Does NOT change spec DESIGN content, does NOT touch other trees. Requires Orders 01, 02, 03 executed.
- Status: approved
- Approval: 2026-08-08, human maintainer ("Approved all. Go.") after /plan-review (APPROVE WITH REVISIONS APPLIED)
- Set: attnview
- Order: 4
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: dxoxgi

## Workflow history

- 2026-08-08 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created. Child of Set `attnview`, authored from the approved spec F7/A9 and Section 7 normalization guidance; requires the Order 02 verbs and the Order 03 checker.
- 2026-08-08 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. FIXED L4-01 (corpus is 10 specs not "~8"; E-01 enumerates ALL), L4-02 (specs with both `- Status: approved` and `- Implemented: SHIPPED` map to `implemented`/done, evidence cited, the free-form bullet folded into history), L4-03 (added the self-contradictory `20260802-1904-01` APPROVED-vs-"remains a draft" case to the blocking OQ-01 for human arbitration at the E-02 gate), L4-04 (do not assume `--approved-by`/`--evidence` flag names; consume Order 02's mechanism; re-normalize THIS approved spec's trailing-prose bullet through the verb; STOP if the verb cannot set approved/implemented via a human token), L4-05 (idempotency: re-run adds no duplicate history / no re-wrap), L4-06 (handle the bare-prose and wrapped-bullet status cases), L4-07 (E-04 reworded to the non-overlapping residual). Status draft -> reviewed.
- 2026-08-08 approved (human maintainer): "Approved all. Go." Status reviewed -> approved; cleared for execution via ipd-lifecycle.

## Goal

Normalize ALL existing specs (10 at authoring; verify at execution) to the new contract using the owner verbs (not hand edits): each spec ends with exactly one bare-enum `- Status:` and a conformant `## Workflow history`; any `deferred` spec carries valid typed gates. No file is renamed or moved. After migration, `aw attention --check` (and `aw specs check`) pass clean on the specs tree.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: survey + dry run

- [ ] E-01 enumerate ALL specs under `.agents/docs/specs/` (excluding `README.md`; verify the count at execution - it is 10 as of authoring, not "~8") and record each one's current prose status and whether it has a `## Workflow history` section; produce the old->new bare-enum map. Handle these grounded cases: `canonical` -> `implemented` + `- Canonical: true` (the agent-comms and ipd-spec specs); `APPROVED ... Go` -> `approved`; `draft (evidence-gated)` -> `deferred` WITH a gate, or `draft`, per the spec's actual state; a spec carrying BOTH `- Status: approved` AND a separate `- Implemented: SHIPPED ...` line (the two artifact-org specs) -> `implemented` (class `done`), citing the executed IPD Set as evidence, with the free-form `- Implemented:` bullet removed and its content preserved in history; flag `20260715-1722-01-agent-comms-convention.md` (its `Status:` is bare body prose with NO leading `- `, so a new `- Status:` metadata bullet must be created, not an in-place body edit) and `20260706-0000-01-...` (a 2-line wrapped `- Status:` bullet to collapse to a single bare token, prose moved to history).
  - Depends on: none
  - Expected outcome: a reviewed old->new status map covering ALL specs (verified count), including the dual-line, bare-prose, and wrapped-bullet edge cases; no writes yet.
  - Execution state: pending
- [ ] E-02 STOP-for-review gate: present the old->new mapping (including any spec that becomes `deferred` and the gate to attach) for human confirmation before any write.
  - Depends on: E-01
  - Expected outcome: the human has confirmed the per-spec target status + gates.
  - Execution state: pending

### Task group 2: apply via the owner verbs

- [ ] E-03 for each spec, run `aw specs set <path> --status <target> [--gate-* ...] --message "attnview migration: normalize status to the closed enum"`, supplying the approval token / evidence citation via WHATEVER mechanism Order 02 actually implements (per Order 01 OQ10; do NOT assume `--approved-by`/`--evidence` flag names) where the confirmed target is `approved`/`implemented`, so each write goes through the validating verb and records history; NO file is renamed or moved. IDEMPOTENCY: for a spec already carrying a bare-enum `- Status:` + a conformant `## Workflow history`, the verb must be a no-op or append at most one migration record; re-running the migration must NOT duplicate history or re-wrap a conformant bullet. Note THIS spec (`20260808-1945-01`) already `approved` but with trailing prose on its `- Status:` bullet must be re-normalized to bare `approved` THROUGH the verb (token re-supplied), not hand-edited. If Order 02's `set` cannot set `approved`/`implemented` for the already-approved/shipped specs via a human-token path, STOP at E-02 and report.
  - Depends on: E-02
  - Expected outcome: every spec carries a bare-enum `- Status:` + an appended history record; paths unchanged; re-run is idempotent.
  - Execution state: pending
- [ ] E-04 for any spec where `aw specs set` did NOT create the `## Workflow history` (e.g. a no-op status set on an already-conformant status), run `aw specs note` to guarantee the section exists - making E-04's action non-overlapping with E-03.
  - Depends on: E-03
  - Expected outcome: every spec has a conformant `## Workflow history`, including specs whose status was already conformant (where `set` was a no-op).
  - Execution state: pending

### Task group 3: verify clean

- [ ] E-05 run `aw specs check` and `aw attention --check` on the repo; confirm the specs tree is clean (no missing/unknown status, no malformed gate, no missing history); run the full suite; confirm paths are unchanged with `git status` (only content edits, no renames). Paste actual output.
  - Depends on: E-03, E-04
  - Expected outcome: specs tree passes `--check`; no path changed; full suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The migration MUST use the Order 02 verbs (not hand edits) so every change is validated and self-records history; this dogfoods `aw specs`.
- G8/A9: preserve every repository-relative path; specs stay flat (no disposition subdirs).
- This spec (`20260808-1945-01`) is itself already `approved`; the migration normalizes the OTHER specs and leaves this one consistent.

## Findings

The existing specs carry free-form prose statuses (`DRAFT`, `canonical`, `approved (2026-08-08, human)`, `APPROVED ... Go`, `draft (evidence-gated)`, hand-written `Implemented`); several lack a `## Workflow history`. Three specs describe deferred work (external-delivery, clean-delta, pip/PyPI) and are candidates for `deferred` + a gate, which is exactly the blind spot the Set closes.

## Proposed changes (ordered, validatable)

1. In-place content edits to each spec under `.agents/docs/specs/` (status normalization + history), applied via `aw specs set`/`note`. No renames.
2. No new source files (this is a data migration using Order 02 tooling).

## Deferred / out of scope (with reason)

| Item | Axis | Reason | Later step |
|------|------|--------|-----------|
| Renaming/moving specs into disposition subdirs | functionality | Breaks citation paths (spec Non-goals); specs stay flat. | not planned |
| Editing spec DESIGN content | scope | Migration only normalizes status/history metadata. | n/a |
| Migrating other trees (plans/research already conform; prompts/comms excluded) | scope | Out of v1 (OQ3). | Phase 3 |

## Scope check

- Over-scope: none - metadata normalization only, via the owner verb, no renames, no design edits.
- Under-scope: MUST leave every spec conformant so `aw attention --check` passes on the specs tree; a partial migration leaves the checker red and the blind spot open.

## Required tests / validation

`aw specs check` and `aw attention --check` clean on `.agents/docs/specs/`; `git status` shows only content modifications (zero renames) to spec files; `python3 -m unittest discover -s tests -t .` green (paste `Ran N ... OK`); `aw sanitize --agent` clean; no em/en dashes.

## Spec / documentation sync

The migration itself is the spec-sync (it brings specs into contract conformance). Record the migration in each spec's `## Workflow history` (the verb does this). No separate doc change.

## Open questions

### OQ-01: which specs get `deferred` vs `draft`/`parked`, and reconciling the self-contradictory spec

- Blocking: yes
- Status: open
- Owner: human (resolved at the E-02 STOP-for-review gate)
- Resolution or deferral rationale: two human judgments about true state, both resolved interactively at E-02 before any write (blocking because the target status determines the gate/token): (1) whether external-delivery / clean-delta / pip-PyPI become `deferred` (with a gate citing the TODO/decision) or another status; (2) `20260802-1904-01-ipd-structure-and-linting.spec.md` has INTERNALLY CONTRADICTORY status prose (line 4 says `APPROVED ... "Approved. Go."`, later prose says it "remains a draft pending maintainer review and approval") - the human MUST arbitrate its true enum at E-02, and if the answer is `approved` the human token is required (an agent must not self-resolve a contradiction into `approved`). Any `->approved`/`->implemented` target names its token/evidence at the gate.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the old->new status map lists EVERY spec under `.agents/docs/specs/` (the verified count, 10 at authoring) with its current prose status and target enum token + any gate; the dual `- Status: approved` + `- Implemented: SHIPPED` specs are mapped to `implemented`; the bare-prose (`20260715-1722-01`) and wrapped-bullet (`20260706-0000-01`) and self-contradictory (`20260802-1904-01`) cases are each flagged.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the human confirmed the mapping at the STOP gate (recorded); no write occurred before confirmation.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: each spec now has a single bare-enum `- Status:` and an appended migration history record; `git status` shows content edits only (zero renames); `approved`/`implemented` targets carried the Order-02 token/evidence; the dual-line specs are `implemented` with the `- Implemented:` bullet folded into history; a re-run of the migration adds no duplicate history line and re-wraps nothing (idempotency).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: every spec has a conformant `## Workflow history` section, including specs whose status was already conformant (where `set` was a no-op and `note` created it).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `aw specs check` and `aw attention --check` output showing the specs tree clean; paste the `git status` proving zero renames; paste the `python3 -m unittest` summary.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This child MUST be reviewed and approved by a human before execution. It carries a BLOCKING open question (OQ-01) resolved at the in-run STOP-for-review gate (E-02) before any write. Do NOT mark it done or move it to `executed/` until every V-* item is verified with concrete evidence; if any item cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload. The terminal lifecycle transition is a POST-gate transaction, never an E-*/V-* item. Requires Orders 01, 02, 03 executed first; if their symbols/verbs are absent, STOP.
